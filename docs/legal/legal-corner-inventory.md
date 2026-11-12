---
provenance: agent-generated
last-verified: never
---

# Legal Corner inventory for the RFI agent

> **Point-in-time snapshot, dated 2026-11-12.** An agent read the Confluence pages and Slack threads below on that date. Jessica said she will keep adding to Legal Corner, so pages, wording and the "last updated" dates can have changed since. This is a historical reference for deciding what goes into `loopio-library-2` and what becomes a red "route to legal" rule. It is not a gold standard, and nothing here is legal advice or has been reviewed by Legal.

Everything in the "approved position" column is a paraphrase of the Confluence page it links to. Re-read the source page before quoting any of it to a client.

## Which Jessica

**Jessica Hoffman** (`jhhoffman@pulsepoint.com`, Slack `U07U93D986Q`). She is in Legal: she created the Legal Corner folder, announced it in #general, and authored 8 of its 9 pages. Not **Jessica Wang** (Hatch product/scrum), who shows up in many of the same Slack searches.

## Scope and counts

| Item | Count |
|---|---|
| Confluence pages read in full | 9 (the folder holds 9 pages plus 1 whiteboard) |
| Whiteboard, not opened | 1 (see "Could not open") |
| Attachments on those pages | 0 found by CQL |
| Question rows below | **33** |
| 🟢 green (answer from library) | **13** |
| 🟡 amber (needs a check) | **17** |
| 🔴 red (route to legal, never draft) | **3** |
| Drafting guardrails (not questions) | 6 phrase rules, listed separately |
| Call readout also read | `docs/legal/2026-11-09-jessica-discovery-call.md` and its Meet transcript |

Colour rule used (my suggestion, except where marked as hers): **green** = factual or standard Q&A she wrote for self-serve reuse. **Amber** = approved wording exists, but it is a legal or regulatory characterization, uses a banned phrase, depends on the client, or has an internal-only element, so a human checks the draft. **Red** = the answer is a contract or negotiation matter that Legal owns.

Row P9 comes from the 2026-11-09 discovery call (see "Jessica's guidance"), not from a Confluence page; the other 32 rows come from the pages.

Source pages are all in the Product & Technology space (`pt`). Every Q&A page carries a standing disclaimer ("educational only, not legal advice, not a representation or warranty"). Any answer lifted from them should keep it.

## Question inventory

Owner for every row defaults to **Jessica Hoffman / PulsePoint Legal** unless noted. Legal requests go through the Jira CM board (see guidance below).

### Pixels: [Pixel FAQs](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4142039052/Pixel+FAQs), updated 2026-08-27

| # | Question | Approved position (paraphrase) | Owner / route | Colour |
|---|---|---|---|---|
| P1 | What do PulsePoint's pixels collect? | IP address, user agent, PulsePoint ID, and sometimes page URL and referrer. The page has a per-pixel matrix (retargeting, smart/HCP, conversion). Conversion pixel does not take page URL or referrer. | Legal | 🟢 |
| P2 | How is the HCP365 / Smart Pixel compliant with HIPAA? | No PHI is involved. The pixel only detects whether HCPs visited specific pages. Reporting returns HCP name and practice location from the public NPI registry. No patient data. **Avoid the word "compliant"** (see W1); say "no PHI is collected". | Legal | 🟡 |
| P3 | How can you tell me which HCPs visited my site? | Pixel visits are matched to HCPs using the NPI registry and PulsePoint's first-party data foundation: the HCP identity graph uses Medscape's member database to authenticate about 3.2M NPIs and maps them to online IDs. Check the 3.2M figure is current. | Legal | 🟢 |
| P4 | How does the HCP365 / Smart Pixel work? | High-level: a database reports back which kinds of HCPs visited (e.g., cardiologists in a state), with NPI-registry name and practice location. | Legal | 🟢 |
| P5 | Where is the data collected by your pixels held? | On PulsePoint servers in the US. May also use cloud storage licensed through Google. | Legal | 🟢 |
| P6 | What do you do with the data collected through your pixels? | Used to perform services for the client: visitor reporting, insights, HCP smart lists for retargeting. Data is used only for that client. High-level aggregates may be used to improve services. No sensitive information is collected. | Legal | 🟢 |
| P7 | Do your pixels collect personally identifiable or sensitive information? | Page answer is "No", and the pixel collects nothing beyond the P1 list. Amber because IP address and an ID can count as personal data under some laws, so a client-specific or definitional follow-up needs a person. | Legal | 🟡 |
| P8 | What cookies do the pixels drop? | A 17-row table: name, set/delete behaviour, expiry, client-facing description and OneTrust class (V, VP, cwbh1, pb_rtb_ev, CWOptOut, cw, wf, vf, gdpr, ccpa, gpp, bhsp, rs, INGRESSCOOKIE, JSESSIONID, mc, sc). Load the table as structured data, not prose. | Legal | 🟢 |
| P9 | Can you place a pixel on a specific client site, especially one run by a HIPAA covered entity? (from the 2026-11-09 call, not a Confluence page) | No library answer. Jessica says this is case by case: if the client is not a HIPAA covered entity, HIPAA does not apply; if it is, someone has to look at the page and make a human determination. C2 says Legal reviews these placements. Jessica wants these routed to her every time. | Jessica Hoffman | 🔴 |

### Company and contract: [Company and Contract FAQs](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4152459283/Company+and+Contract+FAQs), updated 2026-06-08

| # | Question | Approved position (paraphrase) | Owner / route | Colour |
|---|---|---|---|---|
| C1 | Corporate information: legal entity name, state of incorporation, tax ID, company address | Page lists a Delaware corporation, PulsePoint, Inc., with a tax ID and a Newark, NJ address. I did not copy the tax ID or address here; take them from the page. The page has typos ("Untied States", "Newark,,"), so do not paste them verbatim. | Legal | 🟢 |
| C2 | Will PulsePoint sign a Business Associate Agreement (BAA)? How do you handle PHI? | No. PulsePoint does not let clients send it PHI and does not collect PHI through its services, so there is nothing for a BAA to cover. Legal reviews intended pixel placements when a client that considers itself a HIPAA covered entity wants to engage, and sets parameters so no PHI is collected. Also covered on the [Privacy & Compliance FAQs](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4377804822/Privacy+Compliance+FAQs) page (updated 2026-08-14). Jessica repeated "BAAs (no)" in Slack. If the client is a covered entity or asks for an exception, route to Legal. | Legal | 🟢 |
| C3 | Is PulsePoint a signatory to the IAB's Multi-State Privacy Agreement (MSPA)? | Yes. | Legal | 🟢 |

### Privacy and compliance: [Privacy & Compliance FAQs](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4377804822/Privacy+Compliance+FAQs), updated 2026-08-14

| # | Question | Approved position (paraphrase) | Owner / route | Colour |
|---|---|---|---|---|
| V1 | What industry guidelines does PulsePoint follow? | NAI Framework Principles, the DAA, the European DAA, and the IAB EU Transparency & Consent Framework. MSPA signatory. | Legal | 🟢 |
| V2 | How does PulsePoint ensure compliance with US state laws? | Legal tracks federal, state and local legislation and works with data, marketing, ops, sales and tech. The NAI offers compliance support and runs an annual audit of services and privacy practices. | Legal | 🟢 |
| V3 | Is PulsePoint HIPAA compliant? | Not subject to HIPAA: not a covered entity and generally does not handle HIPAA-covered data. Some licensed third-party data (e.g., filled-prescription data) is de-identified to HIPAA standards and used in line with HIPAA. Do not answer with the phrase "HIPAA compliant" (see W1). | Legal | 🟡 |
| V4 | What steps have you taken to comply with Washington's My Health My Data Act? | No targeted advertising in Washington State. Only contextual advertising (targeting the page content, not a device or person). Matches the DTC Washington block on the state-restrictions page (S4). | Legal | 🟡 |
| V5 | Is PulsePoint a "Service Provider" under CCPA/CPRA? | No. For DSP clients using PulsePoint data for targeting, PulsePoint is the "Business". For retargeting-pixel clients it is a "Third Party Business", because the data is used for targeted advertising. A contract-specific characterization, so check against the client's paper. | Legal | 🟡 |
| V6 | How do you get consent? Do HCPs and consumers consent to tracking? | Publishers or site owners obtain consent where the law requires it, and PulsePoint honours the consent signal passed to it. For the HCP database, PulsePoint is a named affiliate in Medscape's privacy policy, and HCPs agree to it when they register with Medscape. | Legal | 🟡 |
| V7 | How does PulsePoint manage opt-outs? | Recognizes GPP, GPC and GDPR/CCPA consent strings from a CMP. Honours verified opt-outs and deletion requests. Opt-out routes: web form, NAI, DAA, an NPI-specific HCP opt-out, and the AdChoices icon (processed immediately). | Legal | 🟢 |
| V8 | What changes have you made for US state geofencing laws? | A nationwide minimum geofence radius of 0.38 miles (2,006 ft). No DSP client can target tighter, including by entering lat/longs. Clients may widen the radius. | Legal | 🟢 |
| V9 | Do you have explicit consent from users to track their location for geofencing? | PulsePoint does not track precise location. It only uses, serves and reports at a radius of 2,006 ft or wider. Consent is required for precise location in the US. The "not precise location" claim is a legal characterization. | Legal | 🟡 |

### California DROP: [California Privacy Compliance](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4522115084/California+Privacy+Compliance), updated 2026-09-22

This page was **not written by Jessica**. The author shown is Zachary Riddle. It sits in her folder, but confirm with Jessica that she treats it as approved. These two rows are my inference: the page is written as client-facing context, not as Q&A.

| # | Question | Approved position (paraphrase) | Owner / route | Colour |
|---|---|---|---|---|
| D1 | How does PulsePoint handle California DROP deletion/opt-out requests? | PulsePoint is a registered data broker and pulls the DROP deletion list every 45 days, then implements deletions within the following 45 days. | Legal (page author: Zachary Riddle) | 🟡 |
| D2 | Why do HCP reporting or reach numbers change after DROP? | Matched HCPs get NPI placeholder `0000000000` and their attributes stop being collected or reported, retroactively for impressions already served. Deleted HCPs are no longer targetable. DTC campaigns are reported in aggregate, so the visible effect is lower reach in California. | Legal (Zachary Riddle) / campaign ops | 🟡 |

### Wording rules: [Words and Phrases to AVOID](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4192075784/Words+and+Phrases+to+AVOID+and+what+to+use+instead), updated 2026-06-16

The page is a style guide, not Q&A. It says to use it "when answering questionnaires". These three rows are my derived questions: RFI questions that invite a banned phrase. The page links to a Google Doc with more options for "anonymized" and "privacy-safe". I did not open it.

| # | Question (derived) | Approved position (paraphrase) | Owner / route | Colour |
|---|---|---|---|---|
| W1 | Are you HIPAA-compliant / NAI-compliant / DAA-compliant / privacy compliant? | Never claim these. Use "in alignment with legal and regulatory compliance". For the HIPAA status answer use V3. | Legal | 🟡 |
| W2 | Is your data anonymized or de-identified? | Do not say "anonymized" unless it is known to be anonymous. Use "pseudonymous", "privacy-enhanced", or "aggregated" where true. "De-identified" is only for claims data (e.g., Forian), never for behavioral or web signals. | Legal | 🟡 |
| W3 | Is your audience fully opted-in / is the platform privacy-safe? | Do not say "100% opted-in" (use "permissioned") or "privacy-safe" (use "privacy-preserving" or "privacy-forward"). Avoid "patient" in a DTC targeting context; use "patient populations" or "health-interested audiences". | Legal | 🟡 |

### State restrictions: [Ad Targeting State Level Restrictions - PulsePoint POV](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4171431941/Ad+Targeting+State+Level+Restrictions+-+PulsePoint+POV), updated 2026-06-09

The page is a table, with a "Trader Best Practice" column that reads as internal ops guidance. Do not put that column in a client-facing library answer. These rows are derived from the table.

| # | Question (derived) | Approved position (paraphrase) | Owner / route | Colour |
|---|---|---|---|---|
| S1 | How do you handle HCP targeting in states with drug-pricing disclosure laws (CO, CT, VT)? | Not blocked by default. The laws require price disclosure (WAC/AWP) in marketer communications. PulsePoint does not control ad creative, so the client chooses whether to block the state. Internally, traders block CO and VT unless creative clearly includes the disclosure. | Legal | 🟡 |
| S2 | How do you handle HCP targeting in Washington? | Not blocked by default. PulsePoint's position is that it does not collect "Consumer Health Data" for HCP campaigns. Clients may choose to block. | Legal | 🟡 |
| S3 | How do you comply with state geofencing-near-healthcare-facility laws for DTC (CA, CT, MD, NV, NY)? | Not blocked. The laws bar geofences of 1,750 or 1,850 ft or less around healthcare facilities. PulsePoint's 2,006 ft minimum radius means its geo-targeting is outside the laws' definition of geofencing. Clients can widen the radius or block a state. | Legal | 🟡 |
| S4 | How do you handle DTC targeting in Washington? | Blocked by default, because the My Health My Data Act needs opt-in consent for any health-related data, and the required consents can't be collected. Contextual (page-content) targeting is allowed. Clients may also block the state. | Legal | 🟡 |

### Governance and contracts

| # | Question | Approved position (paraphrase) | Owner / route | Colour |
|---|---|---|---|---|
| A1 | How does PulsePoint review and approve new AI tools? (derived) | Any new AI tool must be reviewed by the IB AI Review Board via an internal evaluation form. After the board approves, IB legal reviews the tool's legal terms. Source: [AI Tool Review Process](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4281106434/AI+Tool+Review+Process), updated 2026-07-15. The page is an internal process note with an internal link, so do not publish its link externally. Security questionnaires on AI governance likely also belong to the security team. | IB AI Review Board, then IB legal | 🟡 |
| T1 | Will PulsePoint sign our NDA, or can we use your standard NDA? (derived) | PulsePoint keeps up-to-date internal templates: Mutual NDA, Life Agreements, Audience Manager Addendum (omnichannel/social), and an Audience Manager Naming Amendment (authorized clients only; ask Rachel/Donovan). Source: [Up to Date Templates](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4152885263/Up+to+Date+Templates), updated 2026-06-03. The agent should not send or describe these templates. | Legal, via the Jira CM board | 🔴 |
| T2 | Will you sign a DUA, TPA, DPA, or MSA? (derived) | Page only says: submit a Jira ticket to the Contracts/Legal Matters board with the client (usually an agency), the end client (advertiser), and for TPAs the vendor receiving data. No standard positions are published. Same source as T1. | Legal, via the Jira CM board | 🔴 |

## Jessica's guidance

What I found she actually said or wrote, and where:

- **Legal Corner is the self-serve place for her most-asked questions.** Announced in #general on 2026-06-09: "pixels, whether we sign BAAs (no), corporate information, etc." She added "I'll be adding to it over time but this will get you started." ([announcement](https://pulsepoint.slack.com/archives/C024LDV57/p1781021107692189), [follow-up](https://pulsepoint.slack.com/archives/C024LDV57/p1781021134550289))
- **Legal is looking for help answering legal RFI questions faster.** Caedon wrote on 2026-11-06, relaying Andrew Stark, that Jessica was looking for a tool for this. Jessica replied "yes please!" ([thread](https://pulsepoint.slack.com/archives/C0CFR0BEFFE/p1793988455483019), [her reply](https://pulsepoint.slack.com/archives/C0CFR0BEFFE/p1793988547557109)). That is the only trace I found of the RFI conversation.
- **Wording rules for externally facing answers**, from the Words and Phrases page: never "privacy-safe", "HIPAA/NAI/DAA/privacy compliant", "100% opted-in", unqualified "anonymized", "de-identified" for non-claims data, or "patient" in DTC.
- **Do not share templates via Google Doc sharing with clients**; download a copy each time (reminder in #general, 2026-09-09 14:42 EDT; I did not capture a permalink).
- **Requests to Legal go through the Jira Contracts/Legal Matters board** (key `CM`), with a request type, due date and unassigned owner. Follow-ups go back into the "With Legal" lane, with the Legal contact tagged. Source: [Jira Ticket Process](https://ppinc.atlassian.net/wiki/spaces/pt/pages/4196237314/Jira+Ticket+Process), updated 2026-06-17. This is the route the agent should name in red answers.
- **Not stated by her anywhere I could find:** a list of contract topics (DPA, redlines, liability) to route to legal. The two contract rows (T1, T2) and the red cutoff for anything not in the table are my suggestion, to confirm with her.

**From the 2026-11-09 discovery call** (Jessica, Caedon, Maggie; readout in `docs/legal/2026-11-09-jessica-discovery-call.md`). Her words, checked against the transcript:

- **Pain.** The same questions come in several times a day but never worded identically, so copy-paste fails and her FAQs go unused. Her goal is that business teams self-serve and only nuanced or off-the-beaten-path questions reach her.
- **Forced route to her: pixel placement on a HIPAA covered entity's site.** Case by case, needs a human look at the page. If the client is not a covered entity it does not apply. This is row P9 (red).
- **No definitive legal positions.** The tool must not state how PulsePoint complies with HIPAA or other laws as settled fact, because it may be untrue or something PulsePoint does not want to say. This backs the amber on P2, V3, V9 and the banned-phrase rows.
- **Newest answer wins for legal questions.** Layering old and new is fine for product questions (CPMs, how the product works); for legal she would use the newer answer.
- **Trusted source.** The Privacy & Compliance FAQs are the 2025 FAQ she wrote and had blessed by outside counsel ("those I feel good about"). She did not name the other pages as trusted or untrusted.
- **Contradictory legal answers go to her.** If two library answers conflict on something in the legal realm, flag it to her to resolve.
- **Not hers: encryption and retention.** She said "retention policies or encryption or any of that stuff" need engineering or data owners. The PHM RFI answered "do you encrypt data in transit and at rest" two different ways and she does not know the true answer. Treat these as route-to-engineering, not green and not legal answers.
- **Keep it out of her email.** She works on restricted matters and it is unclear whether privilege survives sharing with AI.
- **She will dig up more Q&A pairs**, and said recent RFIs probably hold a lot of the same content.

## Gaps and things I could not open

**Could not open**
- Whiteboard "Untitled whiteboard 2026-07-15" (id 4280254466, in the folder, authored by Jessica). The page-read tool returned 404, and whiteboards aren't readable through it. Content unknown, and the title suggests a scratch board.
- Google Docs linked from the Words and Phrases and Up to Date Templates pages (alternatives to "anonymized" and "privacy-safe", the NDA, Life Agreements folder, Audience Manager addendum and naming amendment). I did not open them: the link targets are outside Confluence, and the templates are contract text, not RFI answers.
- The folder id itself (4141842441) returns 404 on the page-descendants call because it is a folder, not a page. I listed the contents with CQL (`ancestor = 4141842441`) instead, which returned 10 items (9 pages and the whiteboard). No attachments and no nested sub-pages turned up.

**Context I could not find**
- My first pass found no Granola meeting with Jessica (the free plan only exposes the last 30 days). The 2026-11-09 call is recorded in a Meet transcript and the call readout instead, and is now used above. I only read the transcript sections on her requirements, not the whole call.
- On that call she did not walk through Legal Corner page by page or give a "route X to legal" list beyond the HIPAA pixel case. Her only Legal Corner post in Slack is the 2026-06-09 announcement. A DM thread from 2026-09-16 and 2026-09-21 between her and Caedon exists but I did not read it, so I can't say whether it covers Legal Corner.

**Questions the brief expected that are not in Confluence.** Jessica's own examples (pixels, BAAs, corporate information) are all covered. These common legal-RFI topics have **no approved answer in Legal Corner**, so treat the legal ones as red until she says otherwise (encryption and retention route to engineering, per her):
- DPA terms and redline or fallback guidance, including liability caps, indemnification, insurance coverage, warranties, governing law, and audit rights.
- Data retention and deletion timelines for client data, and subprocessor lists.
- GDPR and EU/UK transfer mechanisms (the pages mention the consent strings only).
- Security questionnaire topics: SOC 2, penetration tests, encryption, incident response. Jessica says encryption and retention belong to engineering or data owners, not Legal, and nobody owns them yet (gap flagged in the call readout).
- Pricing or contract-term questions, and any client-specific paper.
- Whether PulsePoint signs agencies' DUA/TPA terms as written (page defers to Jira).

**Data-quality flags for whoever loads these**
- Duplicate content: the BAA answer is on two pages, and three Pixel FAQ answers repeat the same "high-level" paragraph. Dedupe before loading.
- Typos on the Company page ("Untied States", "Newark,,").
- The Pixel FAQ was updated 2026-08-27, newer than the Privacy FAQ (2026-08-14), so for any overlap on pixel data collection, treat the Pixel FAQ as the newer statement. That matches her "newest wins" rule for legal, but she also said the counsel-reviewed Privacy & Compliance FAQ is the one she trusts most, so a conflict between the two should go to her rather than be settled by date alone.
