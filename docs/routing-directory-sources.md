---
provenance: agent-generated
last-verified: never
---

# Routing directory — sources and conflicts (AF-40)

Point-in-time snapshot, 2026-11-12. Written by an agent session while drafting `agents/rfi-agent/skills/routing-directory/SKILL.md`. Contacts and org charts change; re-check against the live sources before relying on any name here.

## Where the list is

**"How-To: Completing an RFI"** is a Google Doc, not a message.

- Link: https://docs.google.com/document/d/1Wl_VGkUV1ut4tu9ctO0VDvPMlyX0pamKtkPDx-tpi2c/edit
- Doc ID `1Wl_VGkUV1ut4tu9ctO0VDvPMlyX0pamKtkPDx-tpi2c`. Created 2023-02-22; last modified 2026-10-23 by Maggie Kuo; owner Leah Drotch (Growth Marketing). Shared with Caedon 2026-01-13. Visibility: unlisted to the domain.
- Shared in Slack by **Andrew Portener**, 2025-12-03 12:37 EST, in the group DM with Latidra Washington and Caedon Gibson ("we follow this process: …"). The message says it is the RFI process; the doc title is the match.
- Also linked from Confluence "RFI Session Summary" (PM1, Ezra Suveyke, 2025-03-19), which holds an older copy of the contact table.

The contact list is the last section, "POINTS OF CONTACT", and has two tables: an older one and one headed "Point of Contact - WIP". The doc is large and mostly process (Salesforce case, Slack channel naming, IB RFI email fields); only the contact tables went into the skill.

## Where I looked

All read-only. Nothing posted, shared or changed.

| Source | Search | Result |
|---|---|---|
| Slack, public and private | "Completing an RFI"; "How-To RFI contacts"; files "completing an RFI" | Found Andrew Portener's 2025-12-03 message with the doc link |
| Google Drive | fullText/title "Completing an RFI", "RFI contacts"; "RFI Q&A Bank" | Read the doc by ID from the Slack link; found the Q&A Bank (shortcut by Andrew Portener, 2026-10-22; Owners tab read) |
| Confluence | CQL: text/title "Completing an RFI", title "RFI" | "RFI Session Summary" (2025-03-19, older contact table); "RFI Process" (SAM1, Lisa Choo, 2026-10-20, Signal flow, names Legal and Security/Data contacts) |
| Granola | search_meetings "Completing an RFI", "RFI contacts", "RFI owners", "RFI routing" | No matches. Free plan: last 30 days only. Transcript search is paid-only and was not available |
| Slack people lookup | each named contact | See departures below. Search shows active profiles; it cannot show deactivated or guest status |

Doc revision history returned empty, so I could not tell when the WIP table was added or which version rfi-system-helper copied.

## Conflicts

Skill = the routing table in `rfi-system-helper/SKILL.md` (commit 685d8cc, 2026-11-12). Directory = the new `routing-directory` skill. The directory matches the Skill table row for row; these are conflicts between the sources they both draw from.

| # | Topic | Conflict | Directory treatment |
|---|---|---|---|
| C1 | Which Doc table is current | The doc holds two tables. Older table: Amanda Alterman for platform/product and roadmap; Walker Linares alone for inventory; Marjorie Kazin for exchange and supply scale; Johnson Lin for data process, data capabilities, network and security. WIP table: Becky Hallam for platform/product, Amanda Alterman for roadmap only, Jay Irwin / Walker Linares for inventory, curated markets and exchange, "??" for data process. WIP also adds Mike Leviste (tech integrations) and Mimi Liu (Reddit/social). | Follows WIP. Nothing in the doc says WIP supersedes the older table. **Needs Caedon or the doc owner to confirm.** |
| C2 | Likely departures | Not found in Slack people search on 2026-11-12: **Johnson Lin** (older Doc table; Bank answerer on 2024 rows), **Jordan Brickman** and **Chris Schaal** (2025-03 Confluence table), **Julie Maggio** (Bank escalation for reporting and billing). "Not found" is not proof they left. | Johnson Lin, Jordan Brickman and Chris Schaal are not routed to. Julie Maggio stays in R16 as Bank-P only; confirm or drop. |
| C3 | Marjorie Kazin | Listed for exchange and supply scale in the older Doc table, dropped in WIP. Slack shows her active (Account Director, Supply) and she relayed answers on the Pinterest ticket APPS-5097 in 2026-09. Dropped, not departed. | Not routed to. **Confirm whether she should be on R08.** |
| C4 | Brand safety owner | Doc: "Divyang / Matt Katz" (one flattened cell; 2025-03 Confluence shows Divyang alone). Bank: Matthew Katz primary, TPM escalation. Divyang Shah is Sr. Director, TPM, so the Doc name overlaps the Bank's TPM escalation. | Kept "Divyang / Matt Katz" with TPM escalation. Confirm they are two people and who is first. |
| C5 | Bank "confirmed" scope | Every Bank-C row (R01, R02, R10, IVT part of R12) is confirmed for the supply and demand scopes. On the Agency-Client scope, which is what this agent answers, the same rows read "Proposed (client)" and the Bank notes agency/client owners are not confirmed yet. | Status `confirmed` kept, matching the current Skill. For agency RFIs that overstates it. **Decide whether R01, R02, R10 and R12 should show `unconfirmed`.** |
| C6 | Legal and privacy primary | Doc: Jessica Hoffman. Bank-P: IB RFI team primary, TPM escalation, "always needs human review". Confluence "RFI Process" (2026-10-20) sends Legal to Jessica and Security/Data to the RFI alias. | R18 lists both, Doc first. No change. |
| C7 | What the RFI alias accepts | Confluence "RFI Process": the alias answers security and compliance only and states it cannot answer legal, product or business questions. R21 (HR, DE&I, other policy) routes to the alias on the Skill's default and the Doc's "In-Depth Policies & Procedures" process, but no source names a topic row or owner for HR or DE&I. | R21 kept as `unconfirmed`. **Find an HR/DE&I owner or confirm the alias takes them.** |
| C8 | "Mirian" | Confluence "RFI Process" names Mirian for Security/Tech/Data. Not in the Doc or Bank; not found in Slack. The page itself says to confirm contacts or switch to the alias and role names. | Not added. |
| C9 | Jessica Hoffman channel | Doc and Skill: reachable only by email or gchat at jhhoffman@webmd.net. Slack has a Jessica Hoffman profile with a pulsepoint.com address. | Kept the Doc instruction. Confirm Slack is still the wrong channel. |
| C10 | Reporting and billing | Doc: AM on the account, AM's superior. Bank-P: Erica Yard, Julie Maggio. Erica Yard is Account Director on the Supply Team, so she may not fit agency/client accounts. | Merged as in the Skill. Confirm Erica Yard belongs on agency RFIs. |
| C11 | Unowned topics | Data process, data foundation and targeting methodology (Doc "??", Bank unassigned); supply path, schain, sellers.json, ads.txt (Bank unassigned). The 2025 table gave data topics to Johnson Lin. | Listed as gaps G01 and G02. No name filled in. |

Agreement, no conflict: Becky Hallam (platform), Amanda Alterman (roadmap), Zach Rice (PSM/CM escalation), Jessica Hoffman, michael.cordova@internetbrands.com (sustainability), rfi@internetbrands.com (security), Mimi Liu, AE and AE's VP, AM and AM's superior. Slack shows these people active, except the AE/AM roles and the IB addresses, which have no Slack profile.

## Not included in the skill

- The doc's process steps (Salesforce case, Slack channel naming, two business-day review by Andrew Portener, IB RFI email fields). Routing data only.
- Doc and Bank `answered_by` names (Eric, Brett, Anis Momin, Azar Hafizi and others). The helper skill already says these show who answered a past questionnaire, not who owns a topic.

## Hand-off

- AF-33 "contact list" gap: the list was found (above). The parent chat owns closing that gap.
- Registering the skill in `agent.md` and running `ant apply` were not done, per the AF-40 brief.
- The existing rfi-system-helper routing table was not edited. It still holds the same rows, so contacts exist in two places until the helper is pointed at this skill.
