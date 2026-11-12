---
name: routing-directory
description: Look up who owns an amber or red RFI question — owner, escalation contact and lane — so the rfi-system-helper skill can route it. Use whenever a question is triaged amber or red, or when the user asks "who do I send this to". Contains contact data only; the writing and routing rules live in rfi-system-helper.
---

# Routing directory

Contact data for amber and red RFI questions. The rfi-system-helper skill decides the lane and applies the routing rules; this skill supplies the names. To change a contact, edit a row here and leave rfi-system-helper alone.

**Last reconciled: 2026-11-12** (draft, AF-40). Every row carries its source and date. Open conflicts between sources are listed in `docs/routing-directory-sources.md` in the repo; that file is not loaded at runtime.

## Source key

| Code | Source | Date |
|---|---|---|
| Doc | Google Doc "How-To: Completing an RFI" (owner Leah Drotch), the WIP "Point of Contact" table | read 2026-11-12; doc last modified 2026-10-23 |
| Bank-C | RFI Q&A Bank, Owners tab, status *Confirmed* (Michael Pessis) | confirmed 2026-10-21 |
| Bank-P | RFI Q&A Bank, Owners tab, status *Proposed* (no owner confirmation) | built 2026-10-21 |
| Skill | Default carried in rfi-system-helper, commit 685d8cc | 2026-11-12 |

**Status** is the strongest source on the row: `listed` = named in Doc; `confirmed` = named in Bank-C; `unconfirmed` = Bank-P or Skill only. Append "(owner unconfirmed)" to the Route cell of every `unconfirmed` row.

## Contacts

Lane 🟡 = amber (CS keeps the question and contacts the SME). Lane 🔴 = red (route only, no draft). Contacts on one row are all valid; Doc contacts come first.

| ID | Topic | Route to | Escalation | Lane | Status | Source |
|---|---|---|---|---|---|---|
| R01 | Tech integrations | Mike Leviste; TPM | Paul Bennett | 🟡 | confirmed | Doc (Mike Leviste); Bank-C (TPM, Paul Bennett) |
| R02 | OpenRTB / bid request specs, endpoints, latency, tmax, data centers, QPS | TPM | Paul Bennett | 🟡 | confirmed | Bank-C |
| R03 | Ad formats, CTV, ad podding, VAST | TPM | Paul Bennett | 🟡 | unconfirmed | Bank-P |
| R04 | Identifiers and identity (EIDs, UID2, RampID, cookie sync) | TPM | Paul Bennett | 🟡 | unconfirmed | Bank-P |
| R05 | Platform / product capabilities the library doesn't cover | Becky Hallam | — | 🟡 | listed | Doc |
| R06 | Future roadmap | Amanda Alterman | — | 🟡 | listed | Doc |
| R07 | Inventory (supply) overview and logistics | Jay Irwin / Walker Linares | — | 🟡 | listed | Doc |
| R08 | Exchange, supply scale, partner-specific questions | Jay Irwin / Walker Linares | — | 🟡 | listed | Doc |
| R09 | Curated markets | Jay Irwin / Walker Linares; Doug Richards | — | 🟡 | listed | Doc; Bank-C (Jay Irwin, Doug Richards) |
| R10 | Deals, PMP, programmatic guaranteed (PG) | Jay Irwin (deal strategy); Doug Richards (deal operations) | TPM (PG and deal-sync mechanics) | 🟡 | confirmed | Bank-C |
| R11 | Set-up, activation, general capabilities for this account | PSM/CM on the account | Zach Rice | 🟡 | listed | Doc |
| R12 | Brand safety, ad fraud, IVT, supply quality | Divyang / Matt Katz | TPM (how blocks work technically) | 🟡 | listed | Doc; Bank-C for IVT, fraud and traffic quality; Bank-P for brand-safety policy |
| R13 | Company overview facts the library doesn't cover (HQ, countries, terms) | Matt Katz | Jessica Hoffman | 🟡 | unconfirmed | Bank-P |
| R14 | Ad policies, advertiser vetting, LegitScript | Matt Katz | Jessica Hoffman | 🟡 | unconfirmed | Bank-P |
| R15 | Pricing (rates, discounts, commercial terms), differentiators, sales process | AE on the account | AE's VP | 🟡 | listed | Doc |
| R16 | Reporting specifics, billing, discrepancies, commercial commitments, client relations | AM on the account; Erica Yard | AM's superior; Julie Maggio | 🟡 | listed | Doc (AM, AM's superior); Bank-P (Erica Yard, Julie Maggio) |
| R17 | Reddit / social audiences | Mimi Liu | — | 🟡 | listed | Doc |
| R18 | Legal, privacy, data rights (GDPR, CCPA, COPPA, state laws), data privacy | Jessica Hoffman — jhhoffman@webmd.net (WebMD; email or gchat only); IB RFI team — rfi@internetbrands.com | TPM (technical facts only, e.g. how opt-out signals are handled) | 🔴 | listed | Doc; Bank-P (IB RFI team, TPM) |
| R19 | Sustainability | michael.cordova@internetbrands.com | — | 🔴 | listed | Doc |
| R20 | Data and platform infrastructure security | Security/privacy team — rfi@internetbrands.com | — | 🔴 | listed | Doc |
| R21 | HR, DE&I, other company policy sourced from IB | Internet Brands RFI team — rfi@internetbrands.com | — | 🔴 | unconfirmed | Skill; Doc process text sends "In-Depth Policies & Procedures" to this alias but names no topic row |

## Account roles

PSM/CM (R11), AE (R15) and AM (R16) are roles. Use the names the user gave for the account team. When none were given, write the role ("AE on the account") and list the unfilled role once in the scope summary.

## Gaps — no owner on file

| ID | Topic | What the sources say | Source |
|---|---|---|---|
| G01 | Data process, data foundation, targeting methodology | Doc lists "??"; Bank lists "targeting & data" as unassigned and notes data-sharing questions lean to the IB RFI team | Doc; Bank-P, 2026-10-21 |
| G02 | Supply path, schain, sellers.json, ads.txt | Bank lists it as unassigned and notes it sits near brand safety: Matt Katz for policy, TPM for technical | Bank-P, 2026-10-21 |

Route a gap question as "SME needed — no owner on file ([topic])" and list it as an open routing gap. For G02, add "try Matt Katz (policy) or TPM (technical)". Do not name anyone else.
