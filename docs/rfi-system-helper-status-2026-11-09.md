---
provenance: agent-generated
last-verified: never
---
# rfi-system-helper — status and rollout plan (successor to the 2026-09-14 note)

> Point-in-time snapshot written 2026-11-09 by Caedon's agent on branch `productionise-artifact`. It describes what was built and what was still unverified on that date. Patterns, hosts and counts may have moved on; check live state before relying on any of them. The 2026-09-14 note remains the record of the skill-only phase.

## Where things stand in one paragraph

The skill still works exactly as Maggie runs it (account skill + `pipeline/query.py` + `loopio-library-2`). Nothing about that path was changed. Alongside it, a second path was built so that anyone in the PulsePoint Claude org can run the same workflow without Maggie's laptop or keys: a **Claude artifact** that does triage, retrieval, drafting and export in the viewer's browser, backed by **one small retrieval service** that holds the only secret (the Pinecone key) and a **new Pinecone document index** that embeds on write with the same model the library was embedded with. As of this note the code is written and locally tested, and the artifact is published privately; the index, the service and the connector were **not yet live** because the key and the Cloud Run login were still with Caedon.

## What changed since 2026-09-14

| Then | Now |
|---|---|
| Deployment choice open (plugin vs n8n webhook vs Fabric) | Decided 2026-11-06/07: Claude artifact + tiny hosted retrieval service on Cloud Run. Plugin remains the fallback. n8n not used (labs→prod migration blocked). |
| Integrated embeddings rejected (llama-text-embed-v2 scored 8/14) | Reopened for `text-embedding-3-small` only, which Pinecone now hosts on document indexes. Same model ⇒ same vectors ⇒ quality expected to match 13/14. **Not yet measured**, see Eval below. |
| OpenAI key needed per user for query-time embedding | Gone on the new path. Pinecone embeds the query server-side. No OpenAI call, no OpenAI key, no `429 insufficient_quota` failure mode. |
| Retrieval runs on the user's desktop via shell | Retrieval runs behind one URL. The artifact reaches it through the viewer's claude.ai connector (see "Why MCP, not REST"). |
| No logging of what is asked | Every question, triage colour, retrieved record ids, draft and viewer feedback is written to the artifact's `db`, per viewer. Admins read all. |

## The pieces (all on `productionise-artifact`)

| Piece | File | State on 2026-11-09 |
|---|---|---|
| Index build + backfill | `pipeline/backfill_documents.py` | Dry run verified: 2,297 documents (783 Client Strategy, 726 Cleaned, 202 RFI 2026, 586 Q&A Bank), 24 batches of ≤96. `--create-index` tries `processing_location: us` then falls back to `global` and reports which took. `--commit` writes `pipeline/backfill-rollback-<index>.json` before upserting. Never touches `loopio-library-2`. **Not run live.** |
| Text-in search + eval | `pipeline/query_documents.py` | Same JSON shape and prefer-newest dedupe as `query.py`. `--eval file.json` prints top-1 hits. **Not run live.** |
| Retrieval service | `app/endpoint/server.js` (+ `test.js`, `deploy.sh`) | Node 20, zero dependencies. `POST /search` (header `X-RFI-Token`) and `POST /mcp/<token>` (MCP Streamable HTTP, tool `search_library`). 60 req/min per IP in memory. Local smoke test passed up to Pinecone's auth check. **Not deployed.** |
| Artifact | `app/rfi-system-helper.html` | Published privately: https://claude.ai/artifact/9XvbBfgCXD7gxCWumZWCzm. Capabilities `sample`, `db` (per-viewer rules, verified with a probe document), `user`, `downloads`, `mcp` (connector "RFI Library", tool `search_library`). Triage rules, routing table and drafting rules are ported from `skill/SKILL.md` as data in the page. **Connector call unverified** until the service exists. |

### Why MCP, not REST

Artifact pages run under a Content Security Policy that blocks `fetch`, XHR and WebSocket to every external host. Only script loads from a few CDNs are allowed. So the page cannot call a REST endpoint. The service therefore also speaks MCP, is added to claude.ai as a **custom connector named exactly `RFI Library`**, and the page calls it with the `mcp` capability using the viewer's own connector. Connectors cannot send custom headers, so the token lives in the connector URL path (`/mcp/<token>`), which is org-visible. Caedon accepted that on 2026-11-06; rate limiting is the only other guard. The REST route stays for scripts and for the plugin fallback.

### Why ExcelJS, not SheetJS

The export spec requires red/amber/green cell fills. SheetJS Community Edition cannot write cell styles; ExcelJS 4.4.0 (cdnjs) can, and also reads the uploaded xlsx.

## Going live: the steps and who does them

1. **Caedon:** place a write-capable Pinecone key for the same project as `loopio-library-2` at `~/.config/rfi-system-helper/keys.env` (`chmod 600`, line `PINECONE_API_KEY=...`). Run `gcloud auth login` for project `agent-system-cmgibson`.
2. **Agent:** `python3 pipeline/backfill_documents.py --create-index` and report the processing location that took (`us` needs Standard/Enterprise; Starter/Builder get `global`). PP's OpenAI org enforced US residency, so if `global` is what the plan allows, that is a decision for Caedon, not a default to accept silently.
3. **Agent:** `--commit`, then `query_documents.py` spot checks (the HIPAA control question scored 0.899 on the old index; expect similar).
4. **Agent:** `RFI_TOKEN=<long random> app/endpoint/deploy.sh`. Record the Cloud Run URL.
5. **Caedon (org owner):** add the custom connector `RFI Library` at `<url>/mcp/<token>` **org-wide**. Fallback if org-wide add is unavailable: each user adds it once under Settings → Connectors with the same name.
6. **Agent:** open the artifact, run a sample questionnaire end to end, confirm rows in `db` under `logs/<viewer>/runs/...`, fix, republish to the same URL.
7. **Caedon:** share the artifact to the PulsePoint org.

## Eval: the slot for the 13/14 comparison

The 14 Dentsu questions with known-correct records were never checked in. Caedon asked Maggie for them on 2026-11-07 (Slack). When they arrive:

```bash
python3 pipeline/query_documents.py --eval docs/eval/dentsu-14.json
```

Format: a JSON list of `{"question": "...", "expected": "<document _id or exact library question>"}`. Record the result here:

| Index | Model | Top-1 | Date | Who |
|---|---|---|---|---|
| `loopio-library-2` (legacy, client-side embed) | text-embedding-3-small via OpenAI | 13/14 | Sept 2026 | Maggie |
| `loopio-library-3` (document, hosted) | llama-text-embed-v2 | 8/14 | Sept 2026 | Maggie |
| `rfi-answer-library` (document, hosted) | text-embedding-3-small via Pinecone | **pending** | | |

Until that row is filled, the new index is not approved for the skill path; it is only the artifact's backend.

## Unverified on 2026-11-09 (say so when citing this note)

- Pinecone plan tier and therefore processing location. Known only at `--create-index` time.
- Eval numbers (above).
- A real `search_library` call from inside the published artifact.
- CORS from the artifact origin is moot (fetch is blocked anyway); CORS on `/search` is `*` for scripts and was only tested locally.
- Cloud Run cold-start latency under the artifact's two-worker loop.
- Whether `sample` rate limits allow a 288-question run in one sitting; the page backs off 30 s doubling, three tries, then stops the run cleanly.

## Open decisions carried forward (unchanged from CLAUDE.md)

System of record and edit workflow for the library; key ownership and billing once shared; red-lane destination after the 2026-11-09 legal discovery chat; Q&A Bank verification and the 79 Loopio-only questions.

## Recommended next after go-live

1. Fill the eval row. If < 13/14, do not retire `query.py`; investigate before changing anything else.
2. Pilot with two Client Strategy teammates on the artifact only. Watch the `db` logs for amber rates and thumbs-down.
3. Decide whether the skill path (account skill + desktop) is retired or kept as the power-user route.
