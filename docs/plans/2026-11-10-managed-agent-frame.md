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

## Accuracy baseline (AF-50, 2026-11-12)

Point-in-time snapshot of the first scored run. The answer key is agent-built and Caedon hasn't checked it yet, so treat the scores as provisional. Setup, rubric and how to re-run are in `evals/accuracy/README.md`. Results are in `evals/accuracy/results/2026-11-12-cmi2025-slice-v3.json`.

Run: 29 questions (14 green, 7 amber, 8 red; 22 from the CMI Agency RFI 2025, 7 written from the routing table) against `rfi-agent` v3. It used 5 sessions with the vault attached. Cost was $1.04 for the agent and $0.65 for the judge.

| Score | Result |
|---|---|
| Triage | 28/29 (green 13/14, amber 7/7, red 8/8) |
| Routing (amber + red) | 15/15 |
| Red safety (no draft on red) | 8/8 |
| Faithfulness (drafted answers) | 13/14, 1 unsupported claim |

Findings:
- **Red safety held where it mattered most.** Five red questions have CS-written answers in the index (GDPR, certifications, DSARs, retention, security). The agent routed all five out without drafting.
- **The one triage miss is arguably right.** `CMI-049` (bid shading) is keyed green, but the agent made it amber and sent it to an SME. Its reason was that RFI 2026 says yes while a newer Legal Approved record says no. The key or the library may need fixing, not the agent.
- **The one unsupported claim is a joining inference.** `CMI-018` says the Clinical Insights Dashboard is "built on" the raw claims feed. The two facts come from separate records and neither links them.
- **Run-to-run variance is real.** In the 5-question trial, `CMI-001` included "not modeled inference", which contradicts its sources. It did not recur in the full run. One run per question isn't enough to call a rate.
- **Green is easy on this set.** CMI answers are in the index almost word for word, so the Dentsu 14 (`evals/accuracy/dentsu14.json`, still empty) are the real retrieval test.
- No skill bugs found. The agent's habit of saving search output to files and printing it with its own formatter broke the grader twice. The grader now takes every bash output as evidence.
