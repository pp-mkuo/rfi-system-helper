---
provenance: agent-generated
last-verified: never
---
# RFI legal discovery call with Jessica Hoffman: readout (2026-11-09)

> Point-in-time snapshot. The call was 2026-11-09, 10:31–11:00 ET; this readout was written 2026-11-09 and filed 2026-11-12 by Caedon's agent. It records what was said and committed on that date, not the current state of the RFI build. Check live state before acting on any of it.

**Attendees:** Caedon Gibson, Jessica Hoffman (legal), Maggie Kuo.
**Source:** Meet transcript `2026-11-09-group-rfi-legal-questions-user-discovery-chat.md` (kept in Caedon's local meeting archive, not in this repo).
**Related:** the RFI build is this repo; tasks are on the RFI command board (Jira AF-33 and sub-tasks).

## Superseded since the call

On the call the tool was a Claude artifact backed by a Cloud Run retrieval service, blocked on Ezra attaching billing. Per session memory (agent-generated, not re-verified here), that path was dropped on 2026-11-12 in favour of a managed agent (`rfi-agent`) reached through the pp-joke plugin, so the billing blocker no longer applies. Jessica's requirements below are independent of that change and still stand.

## Where things stood on 2026-11-09

- The tool was not live. The demo errored on the database call.
- Jessica had seen it, not used it. She wants "the one that works", not a sandbox copy.
- No legal content was loaded. Caedon committed to loading her Q&As that day and then sending her the link.
- Maggie was out until Wednesday 2026-11-11; Caedon owned front end, data load and deploy until then.

## What we learned (Jessica's requirements)

- **The pain:** the same questions arrive several times a day but never worded identically, so copy-paste fails and her Confluence FAQs go unused.
- **Her end goal:** business teams self-serve and only nuanced questions reach her.
- **Hard escalation case:** pixel placement on a HIPAA covered entity's site needs her case-by-case judgment. If the client is not a covered entity, it does not apply.
- **No definitive legal positions:** the tool must not state how PulsePoint complies with a law as settled fact.
- **Newest answer wins for legal:** layering old and new answers is fine for product questions (CPMs, how the product works). For legal answers use the newer one, because laws change and states get added.
- **Best source:** the Privacy & Compliance FAQs page (2025) was reviewed by outside counsel, and she trusts it.
- **Known bad data:** "do you encrypt data in transit and at rest" was answered two different ways in the PHM RFI, and she does not know the true answer. Retention policy has the same problem. These need an engineering or data owner.
- **Routing:** legal questions end with her. Engineering and security questions get passed on. Contradictory legal answers should be flagged to her.
- **Privacy boundary:** keep the tool out of her email. She works on restricted matters, and whether privilege survives sharing with AI is unsettled.
- **Undecided:** how much she wants to review personally. She needs to see real output first.

## Action items from the call

| Owner | Action | When (as stated) |
|---|---|---|
| Caedon | Get the tool running (then: Ezra billing; see Superseded) | Blocking |
| Caedon | Load Jessica's legal Q&As into the library | 2026-11-09 |
| Caedon | Clean up the UI, fix buttons, add file drop | Before the link goes out |
| Caedon | Send Jessica the link | After the above |
| Caedon | Build the feedback bar so her corrections stop bad matches recurring | After first use |
| Caedon | Move the build from the personal Max plan into the PulsePoint repo | Once running |
| Maggie | Apply the "newest wins for legal" rule in the generator | 2026-11-11 |
| Maggie | Find past approved RFIs with legal answers for the library | 2026-11-11 |
| Jessica | Dig up more Q&A pairs; use the tool and report wrong greens | Once she has the link |

Status of each item after 2026-11-09 is not recorded here.

## Gaps the agent flagged (not raised on the call)

- **An owner for encryption and retention.** Nobody took this. Without one defensible answer the tool keeps serving the contradiction.
- **A source ranking.** The counsel-reviewed FAQ should outrank old RFI answers, not just compete on date.
- **A forced red lane.** HIPAA covered entity pixel questions should always route to Jessica regardless of confidence score.
- **Her "Words and Phrases to AVOID" page as a draft check.** It bans terms like "HIPAA-Compliant" and "Privacy-Safe" in external answers.
- **A contradiction flag.** When the library holds two conflicting answers, surface that instead of picking one.
- **A check against her AI Tool Review Process page.** Not read; unknown whether this tool needs IB AI Review Board sign-off before legal relies on it.

## Legal Corner inventory

Folder: https://ppinc.atlassian.net/wiki/spaces/pt/folder/4141842441/Legal+Corner. Titles and summaries only were read on 2026-11-09; page bodies were not.

| Page | ID | Last modified | Suggested use |
|---|---|---|---|
| Privacy & Compliance FAQs | 4377804822 | 2026-08-14 | Load as answers; counsel-reviewed, highest trust |
| Pixel FAQs | 4142039052 | 2026-08-27 | Load as answers |
| Company and Contract FAQs | 4152459283 | 2026-06-08 | Load as answers |
| Ad Targeting State Level Restrictions - PulsePoint POV | 4171431941 | 2026-06-09 | Load as answers |
| California Privacy Compliance | 4522115084 | 2026-09-22 | Load as answers; author is Zachary Riddle, not Jessica |
| Words and Phrases to AVOID, and what to use instead | 4192075784 | 2026-06-16 | Load as a drafting rule, not an answer |
| AI Tool Review Process | 4281106434 | 2026-07-15 | Skip as content; read for the sign-off question |
| Jira Ticket Process | 4196237314 | 2026-06-17 | Skip |
| Up to Date Templates | 4152885263 | 2026-06-03 | Skip |
| Untitled whiteboard 2026-07-15 | 4280254466 | 2026-07-15 | Skip |
