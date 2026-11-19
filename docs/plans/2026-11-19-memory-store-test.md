---
provenance: agent-generated
last-verified: never
---

# AF-129: memory store vs Pinecone for the answer library (2026-11-19)

This is a point-in-time result from one run of each eval on 2026-11-19. The answer keys are agent-built and Caedon hasn't checked them, so every score is provisional. Accuracy and routing judgments are Maggie's.

## What was tested

Ezra suggested keeping the library in a Claude Managed Agents **memory store** instead of Pinecone. A memory store is a set of text files mounted read-only at `/mnt/memory/`, and the agent searches it with grep. It has no meaning-based search and no scores. The feature is in beta, behind `agent-memory-2026-07-22`. It isn't the same as the agent's vault, which holds credentials only.

- **Store:** `memstore_01MqRVN7npVy4FFPnuWZmVru` (`rfi-answer-library`). It holds 2,297 files, one per record, in one folder per stack. It was loaded by `pipeline/build_memory_store.py` from the same 2,297 IDs that are in the Pinecone index. The Loopio records have no usable category, so the files couldn't be grouped by topic.
- **Agent:** `rfi-agent-memory` (`agent_01Eu17bC4gDYXD1h4eHT7Nu8`, v1) in `agents/rfi-agent-memory/`. It's a copy of live rfi-agent v3. The only changes are the retrieval sections of rfi-system-helper and a grep-based library-search skill. It has no vault, no Pinecone and no OpenAI.
- **rfi-agent itself was not changed.**

## Results

**Accuracy (AF-50 set, 29 questions)**, compared with the AF-50 baseline on rfi-agent v3 (2026-11-12):

| | Pinecone (v3) | Memory store (v1) |
|---|---|---|
| Triage | 28/29 | 29/29 |
| Routing (amber + red) | 15/15 | 15/15 |
| Red safety | 8/8 | 8/8 |
| Faithfulness | 13/14 | 15/16 |
| Agent cost | $1.04 | $1.79 |
| Judge cost | $0.65 | $1.81 |

**Retrieval (the first 30 paraphrase items of the AF-49 set)**, compared with the AF-49 baseline on loopio-library-2 (2026-11-12):

| | Pinecone | Memory store |
|---|---|---|
| Right record ranked first | 25/30 | 25/30 |
| Right record in the top 3 | 28/30 | 27/30 |
| Right record in the top 5 | n/a | 29/30 |
| Cost | about $0 (script) | $1.63 (agent sessions) |

**Where the two differ:**
- **Memory store missed, Pinecone hit:**
  - `af49-037`: report breakouts
  - `af49-038`: source of physician targeting data
  - `af49-039`: how fast an audience goes live
- **Memory store hit, Pinecone missed** (not in the top 3):
  - `af49-030`: dynamic creative optimization
  - `af49-031`: daily trigger files
- **Accuracy set:**
  - `CMI-049` (bid shading) came back green on the memory store and amber on Pinecone. The library has conflicting records on this, so routing it amber may be the better answer.
  - `CMI-055` has one unsupported claim, "patented MeSH-mapped contextual engine".
  - `CMI-018` passed this time.

## Caveats

- One run per question. AF-50 already showed that overclaims vary from run to run.
- The AF-49 answer key was widened by reviewing Pinecone's misses, so it leans toward Pinecone. Some of the memory store's "misses" may still be valid answers.
- The CMI set is easy: its answers sit in the library almost word for word. The Dentsu 14 (AF-120) are still the real test for both setups.
- Cost per question is about 1.7× on the agent side, because the agent runs several greps and file reads instead of one search call.

## Cost and scale

Prices are from pinecone.io/pricing, the Pinecone cost docs and OpenAI's API pricing page, checked 2026-11-19. They may have changed since.

**Per question:**

| | Pinecone (live) | Memory store |
|---|---|---|
| Search | 0.25 RU minimum at $16–18 per million RU, about $0.000004 | n/a (grep) |
| Embedding | OpenAI `text-embedding-3-small` at $0.02/M tokens, about $0.000001. Pinecone `llama-text-embed-v2` would be $0.16/M | none |
| Storage | about 15 MB at $0.33/GB-month, about $0.005 a month | no charge listed (the docs are silent) |
| Claude tokens | about $0.036 | about $0.062 |

**Fixed costs:**
- Pinecone's Standard plan has a $50/month minimum; Builder is $20 flat. The free Starter plan is AWS us-east-1 only, and the agent's index is on GCP us-central1, so the project is on a paid plan. Which plan is not checked.
- If that plan also covers the other indexes (`rfihistoricalanswers`, `pulsepoint-knowledge`), the library adds about $0 at the margin.
- If the plan exists only for this library, the memory store is cheaper overall below about 1,900 questions a month: $50 ÷ $0.026 extra per question.

**Upkeep costs (not on any invoice):**
- Two vendors' keys in the vault, plus the allowed hosts.
- A separate ReadWrite key for every load.
- An OpenAI account that can run out of credit (`429 insufficient_quota`).
- Two outside services to clear in a legal or security review.

**Scale:**
- **Memory store:**
  - The store holds at most 10,000 files; it has 2,297 now. Past that, records have to be packed several to a file or spread across stores (a session can attach up to 8).
  - Each keyword search returns more candidates as the library grows, so the tokens and time per question grow with it.
  - Matching reworded questions gets harder as near-duplicates pile up.
  - Loading takes one API call per file.
- **Pinecone:** the query cost stays at the 0.25 RU minimum up to about 0.25 GB per namespace (roughly 40,000 records at this size). Search quality doesn't depend on library size the way keyword search does.
- **Both:** duplicates and conflicts grow with the library, so library cleanup (AF-117) matters more than the choice of store.

## Reading

On this sample, keyword search over a memory store matched Pinecone on both accuracy and retrieval. It also removed the vault keys, the allowed hosts and the laptop load scripts. The open questions are the Dentsu 14, run-to-run variance, and whether the higher cost per question is acceptable. Those are calls for Maggie and Caedon.

## Rerun

```
unset ANTHROPIC_API_KEY
python3 evals/accuracy/run_accuracy_eval.py --agent-id agent_01Eu17bC4gDYXD1h4eHT7Nu8 --memory-store memstore_01MqRVN7npVy4FFPnuWZmVru
python3 evals/retrieval/run_memory_retrieval.py --origin paraphrase --limit 30
```
