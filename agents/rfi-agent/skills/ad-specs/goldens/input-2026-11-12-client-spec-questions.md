# Golden: client spec questions (representative)

Questions are verbatim from past client RFIs in the RFI Q&A Bank (rows AGC-077, AGC-081 and AGC-083, sources CL-BMS-KINESSO-2024 and CL-KINESSO-STOREFRONT-2023). The CTV question is from row SUP-220.

## Input

1. Which ad sizes / units are accepted for each channel?
2. What video durations / lengths are supported (max duration)?
3. Which creative file / media types and max file sizes do you support?
4. For CTV, what file format, resolution and length do you need?

## Expected

All four are green.

1. A short table by channel: display (970x250, 728x90, 970x90, 300x250, 300x600, 160x600, 300x1050, 320x50, 300x50), native (1000x600 main image, 1:1 logo), video (1920x1080 or 1440x1080), CTV (1920x1080) and eNL (300x250 most common). No KB limits, since the question didn't ask for them. Closes with the source disclaimer.
2. Online video: :90 or less is best practice, and :120 is the recommended max. CTV: :30 recommended, with :60 and :90 on request. Display animation is capped at :15, or :30 on the leaderboard.
3. Video: MOV, MP4, AVI, FLV, VAST/VPAID, max 200 MB. Display: initial load by unit (e.g. 150 KB for 300x250 and 728x90, 200 KB for 300x600), and in-banner video is 3rd-party served only. Native image max 1 MB. Audio: MP3, MPEG, AAC, OGG or VAST.
4. MP4 or VAST 2.0, 1920x1080, :30 recommended (:60 and :90 on request), max 200 MB. **No bitrate.**

Export cells: Route `CS — answered`. Source `Ad specs: <section>`. Date 2026-11-04. Legal Approved `No`. Flag `internal spec source (WIP)`.
