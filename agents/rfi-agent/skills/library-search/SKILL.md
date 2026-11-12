---
name: library-search
description: Search PulsePoint's approved RFI answer library (Pinecone loopio-library-2) for prior answers to a client question. Use whenever the rfi-system-helper skill needs to retrieve answers for a green or amber question.
---

# Library search

Run the script in this skill's directory:

```
PINECONE_INDEX_HOST=https://loopio-library-2-yxxbxim.svc.gcp-us-central1-4a9f.pinecone.io python3 <this skill's directory>/query.py "the client's question" 5
```

Always include the `PINECONE_INDEX_HOST=...` prefix: without it the script targets an index this workspace can't reach.

It prints JSON: `query`, `mode`, and `results`, each with `score`, `stack`, `updated`, `source`, `tags`, `question` and `answer`.

| Flag | Behavior |
|---|---|
| *(default)* | prefer-newest: one row per question; where a question appears more than once, the newest answer wins, curated stacks break ties |
| `--stack NAME` | hard filter to one stack, e.g. `--stack "RFI 2026"` |
| `--cleaned-only` | shorthand for `--stack "Client Strategy- Cleaned"`; drops the RFI 2026 batch and ~79 older-only answers |
| `--raw` | no dedupe, every match as stored |

The default is almost always right.

## Keys

`PINECONE_API_KEY` and `OPENAI_API_KEY` come from the agent's vault. Inside the workspace they hold placeholder values; the real keys are added as the request leaves, and only for `loopio-library-2-yxxbxim.svc.gcp-us-central1-4a9f.pinecone.io` and `us.api.openai.com`. Never print, echo or inspect them.

## Errors

| Symptom | Cause |
|---|---|
| `Missing in keys.env or environment` | The session was started without the vault attached (`vault_ids`). |
| `401` from the index host | The Pinecone credential is missing from the vault, or scoped to the wrong host. |
| `401` from `us.api.openai.com` | The OpenAI credential is missing from the vault, or scoped to the wrong host. |
| `429 insufficient_quota` | OpenAI account out of credits: billing, not a rate limit. |
| Connection refused or blocked | `PINECONE_INDEX_HOST` prefix left off, or host missing from the environment's allowed list. |

Report any error to the user as it appears. Never answer from memory in place of a failed search.

`query.py` is a copy of `pipeline/query.py` in this repo. Keep the two in sync.
