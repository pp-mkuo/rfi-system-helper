# Golden: custom formats and unconfirmed values (edge case)

Synthesized from the edge cases the source sheet raises: the CTV bitrate typo, the 4K DOOH call-out, the open dynamic creative question, and the ad podding row in rfi-system-helper's examples.

## Input

1. What is the minimum and maximum bitrate for CTV video files?
2. Can you run a 4K DOOH takeover, and what are the screen specs?
3. What are the specs for dynamic creative?
4. Do you support ad podding on CTV, and what pod lengths?
5. What's the max file size for a 300x250 on EHR ambulatory systems?

## Expected

1. Amber, because the bitrate is under "Unconfirmed values". Route `SME: TPM (owner unconfirmed)`, Escalation `Paul Bennett`. No bitrate number appears in the draft.
2. Split:
   - Green part: 4K is not supported, the max is 1920x1080, and PulsePoint connects the buyer with its DOOH vendors for screen specs.
   - Amber part: the screen-specific specs. Route to TPM (owner unconfirmed).
3. Amber, under rule (d). Route to TPM (owner unconfirmed).
4. Amber, under rule (e). Route to TPM (owner unconfirmed).
5. Green: 150 KB initial load and 300 KB subload. Flag `internal spec source (WIP)` and `spec section in flux`, because EHR is an open item.
