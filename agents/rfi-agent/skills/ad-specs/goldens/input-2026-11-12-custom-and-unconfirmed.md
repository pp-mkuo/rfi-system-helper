# Golden: custom formats and unconfirmed values (edge case)

Synthesized from the edge cases the source doc raises: the DOOH max-size and CTV pause ad typos, the 4K DOOH call-out, formats the doc doesn't cover, and the ad podding row in rfi-system-helper's examples.

## Input

1. What is the minimum and maximum bitrate for CTV video files?
2. Can you run a 4K DOOH takeover, and what are the screen specs?
3. What are the specs for dynamic creative?
4. Do you support ad podding on CTV, and what pod lengths?
5. What's the max file size for a 300x250 on EHR ambulatory systems?
6. Do VAST tags for CTV pause ads need to be https?

## Expected

1. Green: 15–30 Mbps.
2. Split:
   - Green part: 4K is not supported. Common sizes are 1920x1080 (landscape), 1080x1920 (portrait), and 1400x400 / 840x400 for billboards, taxi tops and transit. Specs vary by publisher.
   - Amber part: screen-level file size limits. Route `SME: TPM (owner unconfirmed)`, Escalation `Paul Bennett`. The draft never quotes "920x1080".
3. Amber, under rule (d). Route to TPM (owner unconfirmed).
4. Amber, under rule (e). Route to TPM (owner unconfirmed).
5. Green: 150 KB initial load and 300 KB subload. No flag.
6. Amber: the pause ad tag rule is under "Unconfirmed values" (it says "secured" but "http://"). Route to TPM (owner unconfirmed). Green part allowed: 3rd-party tracking pixels are permitted.
