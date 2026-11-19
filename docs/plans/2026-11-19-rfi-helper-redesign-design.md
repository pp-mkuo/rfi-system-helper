---
provenance: agent-generated
last-verified: never
---

# RFI System Helper: redesign

Point-in-time design, written 2026-11-19 by Caedon's agent. Mockups: Paper file "RFI System Helper — redesign" (https://app.paper.design/file/01M7TKH5B27D5XFDBQVY9Z3P9J), artboards "Send — new run" and "A · Review — list + side panel". The page may have changed since; read `app/rfi-system-helper.html` for what it does now.

## Why

Caedon, 2026-11-19: the page is hard to read. Reviewing the questions is chunky, and it's hard to see quickly what you need to get out of it. Slim it down, so getting from sending questions in to reading the answers back is easy. Show flags as icons you can hover. Smooth and minimal, not extreme.

## Goals

- Scan a whole run in a few seconds: one slim row per question.
- Flags as icons, explained on hover.
- Review answers one at a time without losing your place in the list.
- Three steps that read as one flow: Send → Working → Review.

## Non-goals

- No change to what the page sends rfi-agent, how it parses replies, the run log (db) or the .xlsx export. AF-126/AF-127 (PR #10) behaviour is kept as-is.
- No new capabilities and no new libraries beyond ExcelJS, which the page already loads.

## Anti-goals

- A prettier page that hides a flag, a failed row or a routing gap the old page showed.
- Animations. The `pulsepoint` Platform mode has no motion, so "smooth" means fewer boxes.

## Approaches considered

- **A. Slim list + side panel** (picked by Caedon, 2026-11-19). Rows on the left. The selected question's draft, feedback, Accept and library matches sit in a right panel, with next/previous arrows. Best for working through drafts in order.
- **B. Rows open in place.** The draft opens under its row. Simpler on narrow screens, but the page grows as long as today's once many rows are open.
- **C. Lane columns (Green/Amber/Red board).** Dropped. Long RFI questions get cramped in columns, and most of the work is on green drafts anyway.

## Design (decided)

- **Look:** the `pulsepoint` design system, Platform mode (labs-open-design `design-systems/pulsepoint/DESIGN.md`, `tokens.css`).
  - White page, Open Sans, the 18/16/13/12 type scale, `--pp-*` tokens only.
  - The brand gradient goes on the one primary button.
  - Lanes use `--pp-positive` (green), `--pp-warning` (amber) and `--pp-negative` (red). Labels stay GREEN/AMBER/RED.
  - Line SVG icons, no emoji.
- **Send:** a centered composer.
  - A paste box that shows the live question count.
  - Upload .xlsx/.csv, with the column pickers shown only after a file loads.
  - Run name, AE, AM and PSM/CM on one line.
  - Agent status and one "Send N questions" button.
  - Recent runs below as slim rows, each with a lane bar.
- **Working:** the run header replaces the composer and shows the progress bar and the status text. Rows fill in as batches return. Stop sits in the header.
- **Review:**
  - **Header:** run name, counts and account team, plus the agent chip, New run and Export .xlsx.
  - **Filter strip:** a segmented control (All · Green · Amber · Red · Flagged, plus Failed when there are any) and "N of M green answers accepted".
  - **Each row:** #, lane dot, the question (2 lines max), and the route or failure on a second line. Then the flag icons (hover or focus for a tooltip) and a state: Accepted, Draft to review, Routed, Working, Retry.
  - **Side panel, question selected:** lane pill and route, the question and why, the draft editor (autosave as today), 👍/👎 and Accept. Then the library matches, top 2 shown with "Show N more", and next/previous arrows (also the ↑/↓ keys).
  - **Side panel, nothing selected:** the scope summary (routing groups, open routing gaps, failed count).
- **Flag icons:** owner unconfirmed (person ?), no owner on file (person ×), stitched claim (link), uncovered sub-question (dashed circle), any other agent flag (flag), Legal Approved source used (shield). Failed shows as text in the row.
- **Narrow screens (< 900px):** the panel becomes a full-width sheet over the list.

## Left to the builder

The exact markup, keyboard handling, and keeping `check-agent-reply.js` passing.
