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
- ~~The helper page still calls the "RFI Library" connector.~~ Routed to rfi-agent on 2026-11-12 (AF-35). See below.
- The library choice waits on the 14 Dentsu test questions.
- `rfp-builder` (referenced by Maggie's skill) isn't in this repo.

## Helper page routed to rfi-agent (2026-11-12, AF-35)

This is a point-in-time note. The Artifact runtime was at contract 0.2.96.

**Route.** The page is `app/rfi-system-helper.html`, published at https://claude.ai/artifact/9XvbBfgCXD7gxCWumZWCzm with the same link as before. It reaches the agent like this:

1. The page declares `mcp` with the host server `host:pp-joke` and three tools: `list_agents`, `send_message` and `get_reply`.
2. It finds `rfi-agent` with `list_agents`.
3. It sends questions 10 at a time in one agent session per run, along with the AE, AM and PSM/CM names.
4. It polls `get_reply` every 10 seconds, for up to 30 minutes per batch.
5. It reads back a JSON array with one row per question or question part.

The run log (`db`), the 👍/👎 feedback and the Excel export work as before.

**What moved to the agent.** The triage rules, routing table, drafting rules and the 0.45 score floor were deleted from the page. They now live only in the agent's `rfi-system-helper` skill, so the page can't drift from it. The `sample` capability and the demo snapshot fallback are gone too.

**Who can use it.** On PulsePoint's enterprise account pp-joke is force-loaded on every device, so any org member can link it to the page. That means one shared page works for everyone, even though the runtime docs say host servers are "owner-only for now". It works only in the Claude desktop app. In a browser tab the page says so, and it can still reopen past runs and export them.

**Tested.**
- Caedon's probe page called the agent from inside an Artifact.
- A 3-question batch (green HIPAA targeting, red SOC 2, amber CPM) sent through pp-joke with the page's exact prompt came back as the JSON the page expects.
- `app/check-agent-reply.js` checks the reply parsing.

**Gaps.**
- `library-search` output has no record IDs, so `sources[].id` comes back blank. The run log's `retrievedIds` are therefore empty, though scores and source questions still show. Adding IDs to `query.py` output would fix it.
- The agent's flags are full sentences, not the page's short labels, so the chips run long and the "flagged" count is right but not grouped. A short flag vocabulary in the skill would help.
- The reply doesn't include source answer text, so the matches drawer shows only source questions.
- "Stop" stops polling but not the agent's current batch.
- pp-joke 0.2.4 marks `list_agents` and `get_reply` read-only, so polling shouldn't ask for approval. Only `send_message` may ask, once per batch.
- Testers need Contributor access or higher for their runs to be logged, because of the `logs/{self}` write rule.
- A long questionnaire takes a few minutes per 10 questions. The batch size isn't tuned.
- **Server name.** In an Artifact the server is `host:pp-joke`, which is the desktop app's name for the org plugin. Claude Code's internal name `plugin_pp-joke_pp-joke` returns `server_not_connected`, which Caedon's first probe click showed.
- **Personal accounts.** The org plugin only reaches pages opened under the PulsePoint enterprise account. To test from a personal claude.ai account, install `pp-joke-0.2.4.mcpb` as a desktop extension. It was built on 2026-11-12 from the 0.2.4 plugin zip's server and the 0.2.2 `.mcpb` manifest, and it is also named `pp-joke`.
