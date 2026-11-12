---
provenance: agent-generated
last-verified: never
---

# RFI managed agent: the frame

Point-in-time plan, written 2026-11-10 by Caedon's agent. The design is the Paper file "RFI managed agent — puzzle pieces" (two boards: the pieces, and where they go). Managed Agents is in beta, so check field names against current docs before reusing this.

## Goal

A working agent built only from pieces that exist today, so the missing ones can be added afterwards.

## Decisions (Caedon, 2026-11-10)

- Library: today's `loopio-library-2`, the scored one. Needs the OpenAI key as well as the Pinecone key. The agent uses the copy in Caedon's Pinecone project (`loopio-library-2-yxxbxim.svc.gcp-us-central1-4a9f.pinecone.io`), not Maggie's (`...-rme8ns3.svc.aped-4627-b74a...`): keys only work inside their own project. `query.py` takes the host from `PINECONE_INDEX_HOST`, defaulting to Maggie's.
- Files live in this repo under `agents/rfi-agent/`, synced with `ant apply`.
- Workspace: the Anthropic workspace pp-joke's key reaches ("Default").
- Keys: Caedon adds them to the vault in the Console. They never go in this repo or a chat.

## What's in the frame

| File | What it creates |
|---|---|
| `agents/rfi-agent/environment.yaml` | Workspace with limited networking: the index host and `us.api.openai.com` only |
| `agents/rfi-agent/vault.yaml` | Empty vault. Credentials are added in the Console |
| `agents/rfi-agent/agent.md` | The agent: Claude Opus 5.5, web tools off, three skills |
| `agents/rfi-agent/skills/rfi-system-helper/` | Maggie's skill, with the desktop-only parts removed (setup, keys, path) |
| `agents/rfi-agent/skills/library-search/` | `pipeline/query.py` plus instructions |

`pipeline/query.py` now reads keys from the environment when `keys.env` is missing, so it runs unchanged on a laptop and in the agent.

## Steps

1. Upgrade `ant` to 1.34 or later (1.8.0 is installed; `apply` needs 1.30, vaults 1.34).
2. Point `ant` at pp-joke's workspace. The current CLI key reaches a different workspace (the presales agents).
3. `ant apply --dry-run -v agents/rfi-agent/agent.md agents/rfi-agent/environment.yaml agents/rfi-agent/vault.yaml`, review, then apply. Commit `claude-lock.json`.
4. In the Console, add two environment-variable credentials to the `rfi-agent` vault, header only:
   - `PINECONE_API_KEY`, allowed host `loopio-library-2-yxxbxim.svc.gcp-us-central1-4a9f.pinecone.io`
   - `OPENAI_API_KEY`, allowed host `us.api.openai.com`
5. Test with a CLI session that attaches the vault (`--vault-ids`), starting with the HIPAA check question (expect ~0.89), then a green, an amber and a red question.

## Result (2026-11-10)

Applied to pp-joke's workspace; IDs are in `claude-lock.json`. Tested from the CLI with the vault attached:

- The vault adds both keys at egress (OpenAI in `Authorization`, Pinecone in `Api-Key`).
- HIPAA check: top match 0.8993, as expected.
- Green (HCP targeting by specialty): answered from the library. Amber (last quarter's IVT rate): no library match, routed to Divyang / Matt Katz. Red (SOC 2 report): routed to the security team, no draft.

## Index filled (2026-11-11)

Caedon's copy started with 1,509 vectors (the Loopio export only). Loaded the RFI 2026 batch (202) and the Q&A Bank (586, approved rewrites already in `qabank_records.json`) with the existing ingest scripts, which now take `PINECONE_INDEX_HOST` and environment keys like `query.py`. Count went 1,509 → 1,711 → 2,297, the same as Maggie's index. `--rollback` on either script removes its batch.

The vault's Pinecone key is read-only, which is all the agent needs. Loading needed a separate ReadWrite key, typed into a terminal and not stored. A read-only key passes `describe_index_stats` but shows up on upsert as `BrokenPipeError`, not a 403.

Re-tested with the vault attached. Both questions matched `RFI 2026` records at the top: audience quality and claims optimization at 0.7519, and SSPs at 0.5924. On the SSP question, the agent skipped a higher-scoring `RFI Q&A Bank v2 (unverified)` answer (0.792) and flagged it for the supply team to check.

## Known gaps after the frame

- **pp-joke vault support: rolled out (2026-11-12).** pp-joke 0.2.4 reads `environment_id` and `vault_ids` from the agent's `metadata`, which `agent.md` now sets. Tested by driving the connector directly: the session opened with the vault, and the HIPAA search returned a top match of 0.8596. 0.2.4 is in the org plugin library (install required, everyone), and a new Claude chat on Caedon's Mac reported `vaults_attached: 1` when it messaged `rfi-agent`. Hand-installed older copies of pp-joke take priority over the org plugin and need removing.
- Routing directory, ad specs and library upkeep skills.
- The helper page still calls the "RFI Library" connector.
- The library choice waits on the 14 Dentsu test questions.
- `rfp-builder` (referenced by Maggie's skill) isn't in this repo.

## Retrieval test (AF-49, 2026-11-12)

A point-in-time snapshot of Caedon's index copy (2,297 records) on 2026-11-12. Re-run `python3 evals/retrieval/run_retrieval_eval.py` before relying on these numbers; ids and scores change on re-ingest.

91 labelled questions in `evals/retrieval/testset.json`. 74 are paraphrases Claude wrote with the stored wording held out, 16 are RFI 2026 questions used verbatim (a ceiling, since they match stored text), and 1 is the HIPAA check. Searches use `pipeline/query.py`'s prefer-newest path. Results are in `evals/retrieval/results/2026-11-12.json`.

| | n | top-1 | top-3 | MRR | unverified above verified |
|---|---|---|---|---|---|
| Overall | 91 | 84 (92%) | 97% | 0.95 | 7 |
| Loopio export | 32 | 29 | 100% | 0.94 | 4 |
| RFI 2026 | 35 | 32 | 94% | 0.94 | 2 |
| Q&A Bank | 24 | 23 | 96% | 0.97 | 1 |
| Paraphrases only | 74 | 67 (91%) | 96% | 0.93 | 7 |

- **Strict vs reviewed.** On the first run, 67/91 were top-1 against the single labelled record. Most misses were a different record answering the same question. After reading those answers, 29 were accepted as correct (`added_on_review` in the test set) and 7 were rejected. The 84/91 depends on that review.
- **Margin and floor.** HIPAA check top match 0.8994. The median gap between the right record and the best wrong one is 0.11. Only one correct answer falls under the 0.45 floor: "dynamic creative optimization" never reaches the top 20, because the record says only "DCO". 12 correct answers land in the 0.45–0.60 band, which the skill says to read before trusting.
- **Where data quality hurts:**
  - **Unverified Q&A Bank answers outrank verified ones in 7 of 91 queries.** In 4 of them the unverified record is wrong and takes top-1: contextual, report breakouts, green deal IDs, value-based bidding. Its short, generic ad-tech questions ("Do you support PMP / Deal ID?", "multibid") pull on any question with a shared keyword. In the other 3 it is a correct answer but unverified (channels list, IAB taxonomy, OpenRTB version).
  - **Near-duplicates crowd the top 5.** 61 of 91 questions have more than one correct record. Prefer-newest collapses only exact question text, so variants of the same question (four answers to the FDCA compliance question, three SSP lists) fill the slots.
  - **Thin or wrong answers:** `13131289` "Yes" (bid shading), `13130732` "Yes" (pod bidding), `qabank-AGC-109` "Consent", `qabank-SUP-341` "It depends…". `13131184` answers a different question than the one it is stored under (price ranges → Havas segment customization).
- **Verdict:** the index returns the right record for client-style phrasing about 9 times in 10 at top-1, and nearly always in the top 3. The main fixable loss is unverified Q&A Bank intrusion, followed by near-duplicate clutter.
- **Dentsu 14:** still pending. Load the questions into `evals/retrieval/dentsu14.json`; the runner checks top-1 against today's 13 of 14.
