# Querying the answer library (Pinecone `loopio-library-2`)

> Written 2026-09-16. Record counts and the "Loopio as system of record" section predate the Q&A Bank ingest (Oct 23) and Loopio's retirement — see the top-level README for current state.

## What the index is

| | |
|---|---|
| Index | `loopio-library-2` |
| Host | `loopio-library-2-rme8ns3.svc.aped-4627-b74a.pinecone.io` |
| Records (2026-09-16) | **1,711** (1,509 Loopio + 202 from the 2026 RFI ingest) |
| Namespace | `""` (empty string — *not* `__default__`) |
| Vectors | 1536-dim, cosine, dense |
| Embeddings | OpenAI `text-embedding-3-small`, generated externally and upserted as pre-computed vectors |

Record metadata: `question`, `answer_plain`, `stack_name`, `tags`, `last_updated_date`.
The 2026 batch adds `source_doc`, `source_file`, `source_section`, `ingest_batch`.

**Embedding recipe (confirmed):** embedding `question + "\n\n" + answer_plain` with `text-embedding-3-small` reproduces a stored vector at **cosine 1.0000**. Anything upserted later must use the same recipe.

Sibling indexes `rfihistoricalanswers` and `pulsepoint-knowledge` have the same shape and the same limitation.

## Why the Pinecone MCP alone can't search it

None of the indexes has an integrated embedding model, so Pinecone cannot turn a plain-text question into a vector. Text search fails with `INVALID_ARGUMENT`. Queries must supply a pre-computed vector from the same model. The MCP's `upsert-records` tool is likewise unusable, so writes go through `POST /vectors/upsert` with a self-embedded vector.

## Three blockers that had to be cleared

1. **Egress allowlist** — `api.openai.com` and the Pinecone index host returned 403 at the proxy. Added under Organization settings → Capabilities → Code execution. MCP traffic is exempt from egress rules, which is why Pinecone *metadata* calls worked while a direct request to the same host did not.
2. **OpenAI credits** — `429 insufficient_quota`. Resolved with a new billable key.
3. **Regional hostname** — `401 incorrect_hostname`. Our OpenAI org enforces US data residency, so requests go to `us.api.openai.com`, which also had to be allowlisted.

## How to query

```
python3 query.py "your question" [topK] [--raw] [--stack NAME] [--cleaned-only]
```

Default mode is **prefer-newest**: one row per question; where a question appears more than once, the answer with the most recent `last_updated_date` wins. Ties break toward the curated stacks (`Client Strategy- Cleaned`, `RFI 2026`), then similarity score. Results include a `source` field (`source_doc`).

Only the question text leaves the network; library contents stay in Pinecone.

## Why ranking is date-driven and not year-stacked

A per-year stack (`RFI 2026`, `RFI 2027`, …) was rejected: it would relabel 726 cleaned-stack records whose real dates are 2024–2025, make `stack_name` useless as a filter, and make current-year-scoped queries silently miss older-but-still-current answers. Date-driven ranking gets "newer wins" with no relabeling.

## Known data issue: two stacks, incomplete cleanup

| | Distinct questions |
|---|---|
| `Client Strategy- Cleaned` | 726 |
| `Client Strategy` | 783 |
| In both (identical answer text) | 700 |
| **Only in the old stack** | **79** |

The 79 old-stack-only questions include real RFP asks — frequency capping, bulk creative upload, DTC endemic publisher integrations, value prop. `--cleaned-only` drops them, which is why the default mode never filters by stack.

## The 2026 RFI ingest (2026-09-16)

202 records, `stack_name = "RFI 2026"`, IDs `rfi2026-<doc>-NNN`. No existing record touched.

| Source file | Records | `last_updated_date` | Basis |
|---|---|---|---|
| `PulsePoint_Submission_2027_kso_dsp_pharma_rfi.docx` | 78 | 2026-08-20 | filename "8.20.26" |
| `CMI Media Group_Data RFI - August 2026- PulsePoint.xlsx` | 55 | 2026-08-18 | docProps created date |
| `CMI RFI - 2025.xlsx` | 69 | 2025-01-01 | **assumed** — no date metadata |

Scripts: `ingest_rfi_2026.py` (dry-run default, `--commit`, `--rollback`) and `records.json` (exact records upserted; rollback source).

`RFI - NEW - 8.20.26.docx` is an earlier copy of the Submission_2027 file (8 lines differ; Submission_2027 fixes typos, raises HCP list addressability 90% → 94%, adds the Orion partner line). Only Submission_2027 was ingested.

Known imperfections: two question texts appear twice with different answers; `tags` are keyword-derived; nothing is tagged `Legal Approved`.

## Alternative considered: integrated embeddings

Rebuilding via `create-index-for-model` (`llama-text-embed-v2`, 1024-dim) would remove the OpenAI dependency and all three blockers. Tested as `loopio-library-3`: 8/14 top-1 vs 13/14 for the current index. Not adopted.
