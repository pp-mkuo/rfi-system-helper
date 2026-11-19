---
provenance: agent-generated
last-verified: never
---

# RFI System Helper redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the look and flow of `app/rfi-system-helper.html` as Send → Working → Review, with a slim list, hover flag icons and a side panel. What the page sends, parses, logs and exports stays the same.

**Architecture:** One self-contained HTML page, as today. The agent call, reply parsing, db and export code (the `--- run`, `--- db` and `--- export` sections, plus `counts`/`summaryLines`) is kept byte-for-byte except for the DOM ids it touches. The CSS, the markup and the `--- render` section are replaced. Two new pure helpers, `rowState` and `flagList`, decide what a row shows, so they can be checked in Node.

**Tech Stack:** Plain HTML/CSS/JS, ExcelJS 4.4.0 (already loaded), Claude artifact runtime (`claude.use`: db, user, downloads, mcp `host:pp-joke`).

**Spec:** `docs/plans/2026-11-19-rfi-helper-redesign-design.md`. Mockups: Paper "RFI System Helper — redesign".

## Global Constraints

- `pulsepoint` Platform mode. Tokens are copied from labs-open-design `design-systems/pulsepoint/tokens.css`; never invent a hex.
  - `--pp-brand #5536B3`, `--pp-brand-light #EDE8FF`
  - text `rgb(34,34,34)` and `rgba(34,34,34,.55)`
  - outlines `.12` / `.18`, form surface `rgba(34,34,34,.03)`
  - positive `#008888`/`#E3F8F8`, warning `#F58406`/`#FFF1D9`, negative `#EA2656`/`#FDECF0`
- Open Sans 400/500/600/700, sizes 18/16/13/12 only, body never below 13px except captions (12).
- The brand gradient `linear-gradient(135deg,#655BC6 0%,#422B94 100%)` appears on exactly one primary button per screen.
- No motion: no transitions or animations. Line SVG icons, no emoji anywhere (👍/👎 become SVG thumbs).
- Dark mode: keep a `prefers-color-scheme: dark` token override (artifact-design contract). The values are dark neutrals over the same semantic hues.
- Lane labels stay GREEN / AMBER / RED.
- `node app/check-agent-reply.js` must print `ok`.

## Review Focus

1. **The panel's draft editor while a run is still filling rows.** `renderAll()` fires after every batch. Expected: text being typed in the draft box is never lost and the caret stays. Pinned in Task 3: rebuilding the list must never rebuild the panel when the same row is still selected.
2. **The selected row is hidden by a filter.** Expected: the panel keeps showing it, and ↑/↓ moves through the visible rows only. Pinned in Task 3.
3. **An unknown agent flag** (any string not in the known five). Expected: a generic flag icon whose tooltip is the flag text. Pinned in Task 1.
4. **A run reopened from the log, written before `sources`/`flags` existed.** Expected: the rows render with no crash and no icons. Pinned in Task 1 (`flagList` on a row with no flags or sources).
5. **A very long question or route.** Expected: it is clamped to 2 lines in the row and shown in full in the panel. Pinned in Task 2 (CSS line-clamp) and checked in the browser in Task 4.

---

### Task 1: Pure row helpers

**Files:**
- Modify: `app/rfi-system-helper.html` (the `--- render` section)
- Test: `app/check-agent-reply.js`

**Interfaces:**
- Produces:
  - `rowState(r) -> { key: "pending"|"working"|"failed"|"accepted"|"review"|"routed", label: string }`
  - `flagList(r) -> Array<{ key: "unconfirmed"|"noowner"|"stitched"|"uncovered"|"legal"|"other", label: string, tip: string }>`

- [ ] **Step 1: Add the failing asserts** to `check-agent-reply.js`. Add `grab("rowState") + grab("flagList")` to the eval, then:
```js
assert(rowState({ status: "failed", error: "timeout" }).key === "failed", "failed row");
assert(rowState({ status: "drafted", lane: "GREEN", accepted: true }).label === "Accepted", "accepted");
assert(rowState({ status: "drafted", lane: "GREEN", accepted: false }).label === "Draft to review", "draft");
assert(rowState({ status: "routed", lane: "RED" }).label === "Routed", "routed");
assert(rowState({ status: "working" }).key === "working" && rowState({ status: "pending" }).key === "pending", "in flight");
const fl = flagList({ flags: ["owner unconfirmed", "uncovered sub-question", "made up flag"], uncovered: "line-item reporting", sources: [{ legal: true, used: true }] });
assert(fl.map(f => f.key).join() === "unconfirmed,uncovered,other,legal", "flag order + unknown + legal source");
assert(fl[2].label === "made up flag" && /line-item reporting/.test(fl[1].tip), "unknown flag keeps its text; uncovered tip names the part");
assert(flagList({}).length === 0, "old run row with no flags or sources");
```
- [ ] **Step 2:** Run `node app/check-agent-reply.js`. Expected: a crash (`rowState is not defined` / grab fails).
- [ ] **Step 3: Implement both** in the `--- render` section.
  - `flagList` maps the five known flag strings (`owner unconfirmed`, `no owner on file`, `stitched claim`, `uncovered sub-question`) to keys in that order. Every other string becomes `other`. `legal` is added last when any source has `legal && used`.
  - Tips: unconfirmed "Q&A Bank proposed this owner. Confirm before routing.", noowner "No owner on file for this topic.", stitched "Draft joins claims from more than one source. Check it reads true.", uncovered `No library source for: ${r.uncovered}`, legal "The draft uses a Legal Approved answer."
  - Default missing fields with `r.flags || []` and `r.sources || []`.
- [ ] **Step 4:** Run `node app/check-agent-reply.js`. Expected: `ok`.
- [ ] **Step 5: Commit** "RFI helper: row state and flag helpers"

### Task 2: Shell, Send screen and run header

**Files:**
- Modify: `app/rfi-system-helper.html` (the `<style>` block, the markup before `<script>`, `startRun`, `setRunning`, `progress`, `loadRuns`, `openRun`)

**Interfaces:**
- Produces:
  - DOM ids kept, so the existing logic works unchanged: `paste file colpick qcol ncol filenote runname ae am psm start stop retry bar status notice runs runs-empty export exportnote chip-agent chip-db`
  - New ids: `send` (composer screen), `review` (run screen), `qcount`, `runhead`, `runmeta`, `newrun`, `strip`, `list`, `panel`
  - `showScreen(name: "send"|"review")`

- [ ] **Step 1: Replace `<style>`** with the token set from Global Constraints and the layout.
  - Header 64px with a bottom outline. The composer is centered and 720px wide. Inputs have 4px radius and a `.18` border.
  - Buttons are 9999px pills: `.primary` uses the gradient, `.ghost` an outline.
  - Row question text: `-webkit-line-clamp:2`.
  - Below 900px the panel is `position:fixed; inset:0`, shown only when a row is selected.
- [ ] **Step 2: Markup.**
  - **`#send`:** title "New RFI run", a one-line explainer, then a paste box. The box's footer shows the `#qcount` text ("N questions found · or drop an .xlsx / .csv") and an "Upload file" label wrapping the hidden `#file`.
  - Then `#colpick` (hidden until a file loads), and one row with run name, AE, AM and PSM/CM.
  - Then the agent chip, the db chip and `#start` ("Send N questions").
  - Then "Recent runs" (`#runs`, `#runs-empty`).
  - Keep the existing NO_HOST notice text.
  - **`#review`:** a header with `#runhead` (run name) and `#runmeta` (counts, time, account team), the chips, `#stop`, `#newrun` and `#export` (primary).
  - Under the header: `#bar` and `#status` (shown while running), `#notice`, `#strip`, and a body holding `#list` and `#panel`.
- [ ] **Step 3: Wire it up.**
  - `paste` input updates `#qcount` and the `#start` label from `parsePaste(...).length`. With an upload loaded, use `questionsFromUpload().length`.
  - `startRun` and `openRun` call `showScreen("review")` in place of unhiding `#summary`/`#rowspanel`. `#newrun` calls `showScreen("send")` and is disabled while `state.running`.
  - `loadRuns` renders slim rows: name, a 3-segment lane bar from `x.counts` (no bar when the run has no counts), the question count and the date. The whole row is a button that calls `openRun`.
- [ ] **Step 4:** Run `node app/check-agent-reply.js`. Expected: `ok`, which also proves the script still parses.
- [ ] **Step 5: Commit** "RFI helper: pulsepoint shell, Send screen, run header"

### Task 3: Review list, filter strip, side panel

**Files:**
- Modify: `app/rfi-system-helper.html` (the `--- render` section: `renderSummary`, `renderAll`, `renderRow`, `rowEl`, `applyFilter`, the filter listener)

**Interfaces:**
- Consumes: `rowState`, `flagList` (Task 1), `counts()`, `summaryLines()`, `dbRow`, `dbRowLater`
- Produces:
  - `state.sel: string|null` (selected row id)
  - `renderPanel()`
  - `select(id: string|null)`

- [ ] **Step 1: Filter strip `#strip`.**
  - Segmented buttons: All N, Green N, Amber N, Red N, Flagged N, and Failed N only when it's above 0. They set `state.filter` and keep `data-f` values `all GREEN AMBER RED flagged failed`.
  - On the right: "A of G green answers accepted" with a thin bar.
  - `#retry` sits next to Failed when there are failures and no run is going.
- [ ] **Step 2: `rowEl(r)` becomes one button row.**
  - Shows `#n`, the lane dot (an outline dot when there's no lane), the question, and a second line: route + escalation, or "failed: error" in negative.
  - Then the flag icons from `flagList`. Each is an `<span class="ico" tabindex="0" aria-label="label">` holding a `<span role="tooltip">` with `label` and `tip`, shown on `:hover` and `:focus`.
  - Then the `rowState` label. Clicking the row calls `select(r.id)`.
  - Keep the `data-lane`, `data-flagged` and `data-failed` attributes so `applyFilter` works unchanged.
- [ ] **Step 3: `renderPanel()`.**
  - **With no `state.sel`:** "Scope summary" with `summaryLines()`, indented lines as before.
  - **With a selection:** the lane pill, route and escalation, prev/next buttons, the full question and `why`, and the error if failed. For GREEN with a draft, a draft `<textarea>` (input calls `dbRowLater`), SVG thumbs up/down (toggle `r.feedback`, `dbRow`) and an Accept toggle (`r.accepted`, `dbRow`). Then the library matches: score, stack, updated, Legal Approved, used. The top 2 are shown, then "Show N more".
  - Also give amber and red rows a short line: "No draft: rfi-agent drafts green questions only."
- [ ] **Step 4: Keep typing safe** (Review Focus 1).
  - `renderAll()` rebuilds `#list` and `#strip` only.
  - It calls `renderPanel()` only when the selected row's displayed fields changed: compare a key built from `status|lane|draft|sources.length|flags`, held in `state.panelKey`.
  - Editing the textarea never triggers `renderAll`.
- [ ] **Step 5: Keyboard.**
  - ↑/↓, when focus isn't in a field, moves `state.sel` through the rows not hidden by the filter (Review Focus 2) and scrolls the row into view. Esc clears the selection.
  - Selecting a row that the filter hides doesn't clear the panel.
- [ ] **Step 6:** Run `node app/check-agent-reply.js`. Expected: `ok`.
- [ ] **Step 7: Commit** "RFI helper: slim list, hover flags, side panel"

### Task 4: Verify in the browser, then the PR

**Files:**
- Create: `app/preview-fake-host.html`. This is a local preview only: it loads the page with a stub `window.claude` whose `mcp.callTool` returns `list_agents` → rfi-agent, then fixed replies for a 6-question run that covers green+legal, a stitched claim, owner unconfirmed + uncovered, no owner, red, and a timeout failure. Not published.
- Modify: `docs/rfi-system-helper-status-2026-09-14.md` only if it describes the page layout; otherwise leave it.

- [ ] **Step 1:** Open the preview in the browser pane. Send the 6 questions and check:
  - The rows fill in as batches return, and the counts are right.
  - Hovering each flag shows its tooltip.
  - Selecting a row and typing in its draft while the run is still going keeps the text.
  - The filters work, and ↑/↓ and Esc behave.
  - A long question clamps in the row.
  - The layout holds at 390px and 1440px, in light and dark.
- [ ] **Step 2:** Run `node app/check-agent-reply.js`. Expected: `ok`.
- [ ] **Step 3:** Commit, push `claude/rfi-helper-redesign`, and open a PR **based on `claude/af-126-127-helper-page-c11839`** (stacked on #10). Note: retarget it to main after #10 merges, and don't merge it before Caedon reviews.
- [ ] **Step 4:** Republishing the artifact (https://claude.ai/artifact/9XvbBfgCXD7gxCWumZWCzm) waits for Caedon's explicit OK, because it would also ship #10.
