---
name: ad-specs
description: Answer RFI questions about PulsePoint creative specs — ad formats and units, sizes, file types, file weights (KB/MB), durations and lengths, bitrates, character limits — for display, rich media, Medscape, mobile, native, EHR, e-newsletter, search extension, video, CTV (including pause ads), audio and DOOH. Use when the rfi-system-helper skill triages a question that asks for spec values.
---

# Ad specs

Spec data lives in `specs.md` in this skill's directory. It is the only source for spec values; never quote a number that is not in it.

## Step 1: Read the specs

Read `specs.md`. Identify the channel (display, rich media, Medscape, mobile, native, EHR, eNL, search extension, video, CTV, CTV pause ads, audio, DOOH) and the unit or publisher the question names. When the question names no channel, answer for each channel the client's RFI scope covers; when that scope is unknown, cover display, video, native and audio.

## Step 2: Triage each requested value

A value is **green** when it appears in a `specs.md` table or note and is not under "Unconfirmed values".

A value is **amber** when any of these holds:
- (a) it is listed under "Unconfirmed values";
- (b) the format, unit or size is not in `specs.md` (custom, bespoke, unreleased or roadmap formats);
- (c) it asks for publisher-specific specs `specs.md` doesn't list (screen-level DOOH file limits, a named audio publisher's specs, a named site's rich media);
- (d) it asks for dynamic creative specs;
- (e) it asks for CTV or VAST mechanics beyond the listed formats and VAST versions (ad podding, pod sizes, SSAI, VPAID behavior on CTV).

Items under "Not covered by the source" in `specs.md` are always amber.

Route amber values per rfi-system-helper's routing table, row "Ad formats, CTV, ad podding, VAST", using that row's Route and Escalation and its unconfirmed-owner rule (as of 2026-11-17: Route `SME: TPM (owner unconfirmed)`, Escalation `Paul Bennett`). Split a question whose values are partly green and partly amber, as rfi-system-helper splits a straddle. Questions that are not about spec values (for example, whether PulsePoint supports a channel at all) go back to rfi-system-helper's library search.

## Step 3: Write the answer

- Pull only the units and values the question asks about; never paste whole sections or attach the guide.
- Give each value with its unit (px, KB, MB, kbps, seconds as `:15`, characters).
- One format or value: 1–3 sentences. Several formats: one short table, one row per unit, columns limited to what was asked.
- Audio or DOOH answers include that specs vary by publisher and PulsePoint confirms with the publisher before launch.
- When an answer leaves out units the client didn't ask about, close with the source disclaimer from `specs.md`.

## Step 4: Fill the export cells

For each green row:
- Route: `CS — answered`
- Source question(s): `Ad specs: <section>` (e.g. `Ad specs: Connected TV (CTV)`)
- Source date(s): the doc's last-modified date from `specs.md`
- Legal Approved: `No`
- Flags: leave empty. The source is the CS team's master ad specs doc, the reference behind the client-facing Knowledge Base guide.
