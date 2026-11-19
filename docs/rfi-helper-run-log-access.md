---
provenance: agent-generated
last-verified: never
---

# RFI helper: who gets their runs logged (AF-127)

Point-in-time note, written 2026-11-19 against the Artifact runtime contract 0.2.96. The rules and the share menu may have changed since, so check them again before relying on this.

## What the run log needs

The page saves each run to its `db` store at `logs/<viewer id>/runs/<run id>`. It declares `db` with no access rules, so the defaults apply:

| Share-menu level | Runtime level | Can save a run? |
|---|---|---|
| Owner, Editor | `admin` | Yes |
| Contributor | `interact` | Yes |
| Commenter, Viewer | `view` | **No**, not even into their own `data/users/<id>/` space |
| Anyone outside the organization | `view` | **No** |
| Signed out | none | No data at all |

`view` can never write. A page's rules can raise who may write, or widen who may read, but they can't let a Viewer write. So **no page change can log a Viewer's or Commenter's runs in the db.** Each tester needs Contributor or higher.

## What to grant, and where

Do this on the **PulsePoint Enterprise** copy of the page. On a personal account there are no other members, so the Contributor level doesn't apply. Only the owner can write there, plus someone invited by email as an Editor while the page has no public link. The contract also limits `host:` servers such as pp-joke to the artifact's owner, and the PulsePoint org exemption (Caedon, 2026-11-12) only covers the Enterprise account.

Pick one of these, in the page's **Share** menu on claude.ai:

1. **Per person (narrowest).** Add each tester by name (Jessica Hoffman, Maggie Kuo) and set them to **Contributor**.
2. **Whole org.** Set **General access** to PulsePoint, **Contributor**. Every PulsePoint member who opens the page can then save runs. An org member who arrives by a public link also gets Contributor-level writes.

Testers also need the Claude desktop app with pp-joke installed, or rfi-agent can't be reached at all.

## Who can read the runs

Under today's defaults, **anyone who can open the page can read every run**, Viewers included: `logs/` uses the default `read: "view"` rule. Runs hold client RFI questions and draft answers. If they should be visible only to the people who ran them and to Editors, that takes a rules change, which is a separate decision for Maggie and Caedon. For example: `{path: "logs", read: "admin", write: "admin"}` plus `{path: "logs/{self}", read: "interact", write: "interact"}`.

## What changed on the page (AF-127, same PR as AF-126)

- The Run log chip now checks `user.can("data.write")` when the page opens. A tester without write access sees **"Run log off: needs Contributor access"**, and the Your runs panel tells them to ask the owner or export the workbook. Before, the chip said "Run log on" and the writes failed silently.
- If a run can't be logged, two records still exist without any extra access. The exported workbook is one. The other is the rfi-agent session in the Claude Console (Managed Agents, then Sessions, titled with the run name). The session keeps the questions and the agent's output, but not draft edits, 👍/👎 or "accepted".
