# rfi-system-helper

A Claude skill that helps PulsePoint Client Strategy answer client **RFI** questionnaires. It triages every question by scope, searches PulsePoint's answer library in Pinecone, drafts answers grounded in the sources it finds, and exports a triaged .xlsx workbook that routes out-of-scope questions to named owners.

Owner: Maggie Kuo (Client Strategy). Repo assembled 2026-11-06 for review.

## How it works

```
RFI questionnaire (pasted or attached in Claude)
        │
        ▼
skill/SKILL.md ── 1. Triage every question: 🟢 CS answers · 🟡 needs SME · 🔴 route out, never drafted
        │
        ▼
pipeline/query.py ── 2. Embed the question (OpenAI text-embedding-3-small, us.api.openai.com)
        │               and query Pinecone loopio-library-2 (namespace "")
        ▼               Prefer-newest: one row per question, newest last_updated_date wins
        │
        ▼
skill/SKILL.md ── 3. Draft from retrieved records only, with sources, dates, flags
                  4. Export .xlsx — opens with a scope summary; red/amber rows carry Route + Escalation contacts
```

The skill runs inside Claude with the user's computer linked. It calls `query.py` from `~/Desktop/pinecone-loopio/`, which reads `keys.env` from the same folder (Pinecone + OpenAI keys; not in this repo — see `pipeline/keys.env.example`).

## Shared path (Nov 2026, branch `productionise-artifact`)

A second way to run the same workflow, for anyone in the PulsePoint Claude org, with no desktop link and no personal keys. Built 2026-11-06/09; see `docs/rfi-system-helper-status-2026-11-09.md` for state and go-live steps.

```
Claude artifact (app/rfi-system-helper.html)
  triage → retrieve → draft (sample) → review → export (.xlsx) · logs every run to db
        │ mcp capability, connector "RFI Library"
        ▼
Retrieval service (app/endpoint/server.js, Cloud Run)   POST /search · POST /mcp/<token>
        │ holds the only secret: the Pinecone key
        ▼
Pinecone document index `rfi-answer-library` — embeds on write and on query with
text-embedding-3-small (same model as the library), so no OpenAI key anywhere
```

Build the index from this repo's backups with `pipeline/backfill_documents.py` (dry run by default, `--create-index`, `--commit` writes a rollback file). Query it from a shell with `pipeline/query_documents.py`. The legacy `loopio-library-2` index is untouched by all of this.

## Repo layout

| Path | What it is |
|---|---|
| `skill/SKILL.md` | The skill itself, as currently saved: role, triage rules, routing table, retrieval, voice and grounding rules, export spec. |
| `pipeline/query.py` | The search the skill calls. `python3 query.py "question" [topK] [--raw] [--stack NAME] [--cleaned-only]` |
| `pipeline/query.py.bak` | Earlier version (stack-preference ranking), kept for comparison. |
| `pipeline/ingest_rfi_2026.py` + `records.json` | Sept 16 ingest: 202 answers from three 2026 RFIs, IDs `rfi2026-*`. Dry run by default; `--commit`, `--rollback`. |
| `pipeline/ingest_qabank.py` + `qabank_records.json` | Oct 23 ingest: the supply team's RFI Q&A Bank (Supply / Demand / Agency-Client), IDs `qabank-*`, tagged `Unverified` / `Needs SME Review`. |
| `pipeline/apply_rewrites.py` + `qabank_rewrites_approved.json` | Oct 28: applies 16 human-approved fixes to Q&A Bank records (14 rewrites, 2 deletions/merges). `qabank_records.json` reflects the post-rewrite state (586 records). |
| `pipeline/backfill_documents.py` | Nov 2026: creates the `rfi-answer-library` document index (hosted `text-embedding-3-small`, 1536, cosine) and backfills 2,297 records from the CSV + JSONs below. Dry run by default; `--create-index`, `--commit`, `--rollback`, `--delete-index`. |
| `pipeline/query_documents.py` | Nov 2026: text-in search against the document index, same output shape and dedupe as `query.py`; `--eval file.json` for the Dentsu top-1 check. |
| `app/endpoint/` | Nov 2026: zero-dependency Node service (REST + MCP) for Cloud Run; `deploy.sh`, `test.js`. |
| `app/rfi-system-helper.html` | Nov 2026: the Claude artifact. Triage rules, routing table and drafting rules from `skill/SKILL.md` ported as data. |
| `pipeline/SETUP-2026-09-02.md` | Original setup notes from when the pipeline first worked. Record counts and the duplicate note are out of date. |
| `data/loopio_library_export_updated.csv` | Plain-file export of the Loopio library. **Loopio is retired**, so this is the only full plain-file copy of the original library outside Pinecone. 1,591 rows: `Client Strategy- Cleaned` 808, `Client Strategy` 783. The index's cleaned stack has 726 — the extra 82 look like RFI rows added by `legacy/.../append_rfi_to_csv.py`; worth confirming. |
| `docs/` | Design notes: scope triage rules, index access and data issues, Sept status and rollout plan. |
| `legacy/fabric-weaviate-autoresponder/` | Earlier, separate build (July – Sept 2): a FastAPI / Weaviate RFI auto-responder intended for the BI Fabric platform, early Pinecone experiments, an n8n workflow, and July Dentsu RFI outputs. **Not used by the skill.** Kept for context. |

## Current state of the index (`loopio-library-2`)

| Batch | Records | ID prefix | Stack / label |
|---|---|---|---|
| Loopio export | 1,509 | numeric Loopio item IDs | `Client Strategy`, `Client Strategy- Cleaned` |
| RFI 2026 (Sept 16) | 202 | `rfi2026-` | `RFI 2026` |
| RFI Q&A Bank (Oct 23, then rewrites Oct 28) | 588 → 586 | `qabank-` | `RFI Q&A Bank v2 (unverified)` |

1536-dim, cosine, dense. Embedding recipe: `question + "\n\n" + answer_plain`. Anything added must use the same recipe to be comparable.

## What's proven, what isn't

**Proven**
- Retrieval end to end; prefer-newest ranking removes duplicate returns.
- Score bands calibrated on the Dentsu 26/27 RFI.
- Integrated-embedding alternative (`loopio-library-3`) tested and rejected: 8/14 top-1 vs 13/14.
- First full questionnaire run (Oct 2026): 288-question IAB SafeGuard diligence filing from CMI. Triage, red routing and the .xlsx export all exercised; 15 preliminary answers with sources.

**Not yet**
- No one other than Maggie has run it.
- No frozen eval set checked in (the 14 Dentsu questions + correct records). Requested from Maggie 2026-11-07; slot in `docs/rfi-system-helper-status-2026-11-09.md`.
- The shared path (artifact + service + new index) is built and locally tested but was not live as of 2026-11-09.
- Auto-triggering on a natural request is untested.

## Review questions for Caedon

1. **Sharing / deployment.** ~~n8n webhook or plugin first?~~ Decided 2026-11-06/07: Claude artifact + one hosted retrieval service (see "Shared path" above). Plugin stays as the fallback.
2. **System of record.** With Loopio retired, Pinecone is the only live copy of the answer library: no editing UI, no version history. Full backups exist only as `data/loopio_library_export_updated.csv` + the two ingest JSONs. What should own the library going forward?
3. **Ingest scripts.** `ingest_*.py` and `apply_rewrites.py` write to the live index. Are the dry-run / `--rollback` patterns sound?
4. **Retrieval.** Dense-only. A sparse/hybrid test for acronym-heavy queries (NPI, Rx/Dx/Px) is the one configuration not tried.
5. **Data quality.** 79 questions only in the old Loopio stack; Q&A Bank records are unverified; nothing from 2026 is `Legal Approved`.

## Not in this repo

- `keys.env` (real keys). Hardcoded keys found in two legacy files (`batch_rfi.py`, `n8n_RFI_Workflow.json`) were replaced with placeholders here.
- Source documents that were attached in chats rather than saved to disk: the three 2026 RFIs, the RFI Q&A Bank workbook, the "How-To: Completing an RFI" contact list, the IAB SafeGuard questionnaire and its triaged output, the rewrite-review Google Sheet.
- Claude chat transcripts from the legacy folder (`.specstory/`).
