---
provenance: agent-generated
last-verified: never
---

# rfi-system-helper — productionisation brief

Point-in-time snapshot written 2026-11-06 by Caedon's agent after reading this repo and the 2026-11-06 Caedon / Maggie catch-up. Patterns may have moved on; verify paths and counts against live state before relying on them.

## What this is, in one paragraph

Maggie Kuo (Client Strategy) built a Claude skill that answers client RFI questionnaires. It triages each question green / amber / red, retrieves prior approved answers from a Pinecone vector index, drafts grounded answers, and exports a triaged .xlsx that routes out-of-scope questions to named owners. It works. It has run one real 288-question questionnaire end to end (IAB SafeGuard, Oct 2026). Only Maggie can run it. The job now is to make it run for everyone in Client Strategy without depending on her laptop or her keys.

## The moving parts

| Layer | What it is today | Portable? |
|---|---|---|
| Brain | `skill/SKILL.md` (~500 lines: triage rules, routing table, grounding rules, export spec). Saved as an **account skill on Maggie's Claude account only**. | Yes, it is a text file. Needs packaging. |
| Retrieval | `pipeline/query.py`, run by the skill via shell. Embeds the question with OpenAI `text-embedding-3-small` at `us.api.openai.com`, queries Pinecone, dedupes "prefer-newest". | Script is portable. Its **location and keys are not** (below). |
| Knowledge | Pinecone index `loopio-library-2`: ~2,297 records (1,509 Loopio + 202 RFI-2026 + 586 Q&A Bank). 1536-dim, cosine, namespace `""`. **Loopio is retired, so this index is the only live copy of the answer library.** | Cloud-hosted, already shared. Single point of failure with no edit UI or history. |
| Generation | The Claude session itself writes the answers. No second model call. | Yes. |
| Export | The `xlsx` skill produces the workbook. | Yes. |
| Backups | `data/loopio_library_export_updated.csv` (1,591 rows) + `pipeline/records.json` + `pipeline/qabank_records.json`. Re-embeddable with the recipe `question + "\n\n" + answer_plain`. | In this repo. |

`legacy/` is an earlier FastAPI + Weaviate / Fabric ADK build and an n8n workflow (July–Sept). Not used by the skill. Context only.

## What ties it to Maggie's machine (the actual problem)

1. **Hardcoded path.** Skill and every script expect `~/Desktop/pinecone-loopio/` and `cd` there before running.
2. **Personal keys in `keys.env`** in that folder: her Pinecone key and her OpenAI key. OpenAI is billable per person and dies as a silent `429 insufficient_quota` when credits run out.
3. **Desktop link required.** The skill only works in a Claude session with her computer connected and that folder reachable. Cloud-only sessions cannot run it.
4. **Account skill.** `/rfi-system-helper` exists only on her account (confirmed live on the call: Caedon could not see it).
5. **Org egress allowlist** for `us.api.openai.com`, `api.openai.com`, `*.svc.aped-4627-b74a.pinecone.io` under Organization → Capabilities → Code execution. Org-level and already done, but every new host (e.g. an n8n webhook) needs adding.

Items 1 to 4 are per-user friction that scales badly. Item 5 is one-time.

## Where this sits in the bigger picture

- **Decided on the 11-06 call:** Maggie compiles everything into a repo (done: this repo), Caedon reviews the setup, then together they pick the hosting shape. Work continues async; Maggie keeps a checklist and sends updates. She is in New York apartment-hunting through end of November and in Asia in December.
- **Caedon's framing on the call:** "Figure out a way to host it, figure out a way to get it to everyone else." Plugin on the PulsePoint marketplace is the default container if everything is files plus scripts.
- **Integrated embeddings, re-checked 2026-11-06:** the Sept A/B rejected Pinecone integrated embeddings because the only hosted model then (`llama-text-embed-v2`, `loopio-library-3`) scored 8/14 vs 13/14 top-1. That objection is now moot: Pinecone's hosted model list includes OpenAI `text-embedding-3-small` (1536-dim, the exact model the library was embedded with), available on **document indexes via the Documents API** (API version `2026-07`, announced 2026-10-22). Same model means same vectors, so quality should match the 13/14 result; confirm with the Dentsu eval set after backfill. Caveats: the existing `loopio-library-2` legacy index cannot be converted, a new document index must be created and the ~2,300 records re-upserted as text (Pinecone embeds on write, cost is cents); `us` processing location needs the Standard plan, Starter/Builder are `global` only, and PP's OpenAI org enforced US residency, so check the plan. Reranking with `bge-reranker-v2-m3` still tested worse; don't redo that.
- **Older history:** Jan 2026 RFI tool demo (confidence tiers gold = legal-approved, silver = seller-sourced); Aug 21 "RFI - Fabric + N8N Overview"; Aug 31 / Sep 1 working sessions that produced the current pipeline. The legacy Fabric ADK spec and n8n workflow come from that period.
- **Upcoming:** 2026-11-09 10:30 ET "RFI Legal Questions: User Discovery Chat" with Jessica Hoffman (WebMD legal) and Maggie. The 11-06 run showed most red questions were legal ones neither CS nor supply could answer, so this meeting is about the red-lane destination.

## Production options (from `docs/rfi-system-helper-status-2026-09-14.md`, still accurate)

| Option | Shareable | Keys | Effort | Notes |
|---|---|---|---|---|
| Account skill (today) | No | Maggie's | Done | |
| **Plugin on PP marketplace** (skill + `query.py` bundled) | Yes | Still per person | Low | Removes items 1 and 4. Users still need their own keys and a desktop link. |
| **Retrieval behind a webhook** (n8n or small service) doing embed + query server-side | Yes | Centralised | Medium | Removes items 2 and 3 too. One domain to allowlist. Central query log feeds library gap analysis. PP already runs n8n (`n8n-labs.pulsepoint.com`), and `legacy/.../n8n_RFI_Workflow.json` is a starting point. Caveat from Caedon's memory: the n8n labs → prod migration is blocked on KUBE-1136. |
| Fabric ADK tool (legacy `SPEC.md`) | Yes | Centralised | High (eng) | Needs `pulsepointinc/bi-services` PR access. |

**Build status 2026-11-09:** the shape below is built on branch `productionise-artifact` (`pipeline/backfill_documents.py`, `pipeline/query_documents.py`, `app/endpoint/`, `app/rfi-system-helper.html`) and the artifact is published privately; index, service and connector were not yet live. One correction to the plan: **artifact pages cannot `fetch()` any external host** (CSP), so the page does not call a REST URL. The service is also an MCP server and the page reaches it through the `mcp` capability via a claude.ai custom connector named exactly `RFI Library`. Details in `docs/rfi-system-helper-status-2026-11-09.md`.

**Likely shape (revised 2026-11-06, Caedon):** a **Claude artifact** shared to the PulsePoint org, plus one tiny hosted retrieval endpoint. The artifact's `sample` capability makes Claude the generation layer on the viewer's seat (no account skill, no desktop link, no Anthropic key); `db` logs every question, retrieved record IDs, draft and feedback per viewer; `downloads` + SheetJS produce the xlsx. The page cannot hold a secret, so retrieval goes through one URL that holds the Pinecone key. With a `text-embedding-3-small` document index, that endpoint is a pure pass-through to Pinecone's Documents search (no OpenAI call, no OpenAI key). Caedon's call 2026-11-06: endpoint auth is a later concern; Claude org sign-in is the gate for now, an org-visible token in the page is acceptable. Pinecone's own MCP is a local `npx` stdio server with an API key (not OAuth, not a hosted connector) and targets legacy Records-API indexes, so it is not a path for the artifact. The earlier plugin option remains the fallback.

## Open decisions that block "production"

1. **System of record.** Pinecone is the only live library. Who owns it, who can edit, how are changes reviewed? The ingest scripts have dry-run and `--rollback`, but there is no UI and no history.
2. **Key ownership and billing.** Whose Pinecone project and OpenAI org pay, once it is shared.
3. **Hosting of retrieval.** Webhook now, or plugin-only first.
4. **Eval set.** The 14 Dentsu questions with correct records are not checked in. Needed before any retrieval change.
5. **Red-lane destination.** `rfi@internetbrands.com` + Jessica Hoffman today; the 11-09 meeting may change it.
6. **Data quality.** Q&A Bank records are tagged Unverified; nothing from 2026 is Legal Approved; 79 questions exist only in the old Loopio stack.

## Where to look

| Need | File |
|---|---|
| The skill as Maggie runs it | `skill/SKILL.md` |
| Retrieval script | `pipeline/query.py` |
| Index facts, blockers, embedding recipe | `docs/loopio-library-2-access.md`, `pipeline/SETUP-2026-09-02.md` |
| Triage rules | `docs/rfi-scope-triage.md` |
| Status, rollout plan, deployment options | `docs/rfi-system-helper-status-2026-11-09.md` (current), `docs/rfi-system-helper-status-2026-09-14.md` (skill-only phase) |
| Shared path: index build, service, artifact | `pipeline/backfill_documents.py`, `app/endpoint/server.js`, `app/rfi-system-helper.html` |
| Repo-level summary and review questions | `README.md` |
| Previous build (Fabric / n8n / Weaviate) | `legacy/fabric-weaviate-autoresponder/SPEC.md` |
| Meeting source | `~/IDE Files/shade-os/agents/meet-source/data/transcripts/2026-11-06-maggie-caedon-maggie-catch-up.md` |

## Rules for working here

- This is **Maggie's repo** (`pp-mkuo/rfi-system-helper`). Propose changes on a branch and PR; do not push to `main`.
- No keys anywhere in the repo. `keys.env` is gitignored. Scan before committing.
- Do not write to the live Pinecone index without a dry run and a rollback file. Test writes go to a separate namespace.
- Do not re-run the reranker experiment; result is recorded above. The integrated-embedding question is reopened only for `text-embedding-3-small` on a document index (see above), nothing else.
