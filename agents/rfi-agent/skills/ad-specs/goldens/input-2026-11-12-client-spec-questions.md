# Golden: client spec questions (representative)

Questions are verbatim from past client RFIs in the RFI Q&A Bank (rows AGC-077, AGC-081 and AGC-083, sources CL-BMS-KINESSO-2024 and CL-KINESSO-STOREFRONT-2023). The CTV question is from row SUP-220.

## Input

1. Which ad sizes / units are accepted for each channel?
2. What video durations / lengths are supported (max duration)?
3. Which creative file / media types and max file sizes do you support?
4. For CTV, what file format, resolution and length do you need?

## Expected

All four are green.

1. A short table by channel: display (970x250, 728x90, 970x90, 300x250, 300x600, 160x600, 180x150), mobile (320x50, 300x50), native (1000x600 main image, 1x1 logo), video (1920x1080 or 1440x1080 recommended), CTV (1920x1080), eNL (300x250 most used) and EHR (160x600, 728x90, 300x250). No KB limits, since the question didn't ask for them. Closes with the source disclaimer.
2. Online video: :90 or less recommended, :120 max. CTV: :30 or less recommended, with :60 and :90 accepted through the account team. Audio: :15 and :30, with :60 and :90 on request. Display animation: :15 max on standard units; the Billboard allows :30 video.
3. Video: MOV, MP4, AVI, FLV or VPAID/VAST, max 200 MB. CTV: MP4 or VAST, max 250 MB. Display: 200 KB initial load for standard IAB units (80 KB for 180x150); in-banner video is 3rd-party served only. Native image max 1 MB. Audio: MP3 or WAV, max 50 MB (1 MB on Katz Media).
4. MP4 or VAST 2.0/3.0 (3rd-party served), 1920x1080, :30 or less recommended (:60 and :90 accepted), max 250 MB. No bitrate, since the question didn't ask for one.

Export cells: Route `CS — answered`. Source `Ad specs: <section>`. Date 2026-11-02. Legal Approved `No`. No flag.
