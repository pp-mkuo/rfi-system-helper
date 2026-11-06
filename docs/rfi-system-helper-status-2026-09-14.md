# rfi-system-helper — status and rollout plan

> Snapshot as of 2026-09-14. Superseded in places — see "Since this was written" at the bottom.

Skill is saved and live on Maggie's account. Not yet usable by anyone else.

## What is proven

| Component | Evidence |
|---|---|
| Retrieval pipeline (embed → query → results) | Verified live repeatedly; HIPAA control question returns 0.899 |
| `query.py` with prefer-cleaned dedupe | Fixes the 100% duplicate-return problem; three modes tested |
| Score bands | Recalibrated against the Dentsu 26/27 RFI; five correct answers measured at 0.527–0.608 |
| Integrated-inference A/B | `loopio-library-3` built and tested: 8/14 top-1 vs current 13/14 on real paraphrased questions. Decision: do not cut over. Reranking also worse. |

## What is specified but had never run (as of 2026-09-14)

- **The .xlsx export.** Columns, colour fills, scope summary — all unvalidated.
- **Scope triage (green/amber/red)** on a real questionnaire.
- **Red routing** — "never draft, route to IB" path.
- **Amber reclassification** on sub-0.45 scores.
- **The voice and grounding rules** — exercised twice manually, never by another user.

## What is unknown

- Whether the skill auto-triggers on a natural request (no first-time-user test yet)
- Whether anyone other than Maggie can run it end to end
- ~~Whether the Pinecone key has write access~~ — confirmed 2026-09-16

## Known constraints

- Single-file skill: `query.py` is embedded as a code block, path hardcoded to `~/Desktop/pinecone-loopio/`
- Each user needs their own Pinecone + OpenAI keys; OpenAI is billable and a shared exhausted balance fails as a silent 429
- Requires a desktop link with the folder connected
- Library hygiene: 79 questions exist only in the old stack; duplicates across stacks; typos (`Campain Hierarchy`); most targeting records are not `Legal Approved`; all content dated Oct 2025

## What to add, ranked

1. **Run one full RFI end to end.** Exercises export, triage and red routing in a single pass.
2. **A frozen eval set** — the 14 Dentsu questions with known-correct records, stored alongside the skill.
3. **IB RFI team intake destination** (email, form, or Jira queue).
4. **SME map for amber** — which internal team owns which topic.
5. **Library hygiene** — finish the cleanup pass, fix typos.
6. **Answer freshness process** — no refresh cadence.
7. *Optional:* sparse/hybrid retrieval test for acronym-heavy queries (NPI, Rx/Dx/Px).

## Deployment options

| Option | Shareable | Keys | Effort |
|---|---|---|---|
| Account skill (today) | No — Maggie only | Hers | Done |
| **Plugin via marketplace repo** | Yes, installable | Still per-person | Low |
| **n8n webhook** doing embed+query server-side | Yes | **Centralised** | Medium |
| Internal service | Yes | Centralised | High (eng) |

A Team/Enterprise owner can *restrict* which MCPs/extensions are permitted but **cannot force-install** anything.

The n8n option is the strongest fit: PulsePoint already runs n8n, a webhook holds the credentials server-side, and only one domain needs allowlisting org-wide. It also gives central logging of what is being asked, which feeds library gap analysis.

## Recommended sequence

1. Run the full Dentsu RFI; fix what the export surfaces.
2. Package as a plugin; pilot with two teammates on their own keys.
3. Move retrieval behind an n8n webhook to remove key distribution, then roll out broadly.

## Since this was written

- **Items 1, 3, 4 partly done (Oct 2026).** First end-to-end run on the 288-question IAB SafeGuard questionnaire (CMI); export, triage and red routing all exercised. Routing table with named contacts now in the skill (How-To doc + Q&A Bank Owners tab). IB RFI team intake: rfi@internetbrands.com.
- **Loopio is retired.** Pinecone `loopio-library-2` is now the only system of record for the answer library.
- **Index size:** 1,509 → 1,711 (RFI 2026 batch, Sept 16) → 2,299 (Q&A Bank, Oct 23) → rewrite pass applied (14 rewrites, 2 deletions/merges).
