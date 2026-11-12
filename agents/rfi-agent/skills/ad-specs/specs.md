# PulsePoint ad specs (structured)

Source: "[MASTER] 2025 Ad Specs Update - WIP.xlsx", Google Drive folder "PulsePoint Ad Specifications" — https://drive.google.com/file/d/1rJFmz4FLh8F_28n7cgl3veWguaM92Lfs/view
Last modified 2026-11-04 (Zachary Rice). File owner Bisi Alade (ad specs SME per the sheet's Roles tab).
This is an internal work-in-progress sheet. The client-facing guide (Confluence KBP page 4213670081, "PulsePoint Ad Specifications", 2026-06-24) embeds a PDF that downloads blank, so this sheet is the best available source as of 2026-11-12.

Source disclaimer, client-safe: these specs cover the large majority of placements on the platform; the PulsePoint team confirms anything else.

## Display (IAB)

Animation and video in display units: minimum 24 fps; host-initiated video may add 1.1 MB (units capped at :15) or 2.2 MB (units capped at :30); user-initiated video has no file size limit. Subload files may load one second after the browser's `domContentLoadedEventEnd`. An auto-scrolling ISI counts toward the :15 animation cap.

| Unit | Size (px) | Max initial load | Max subload | Max animation / video |
|---|---|---|---|---|
| Billboard | 970 x 250 | 250 KB | 500 KB | :15 |
| Leaderboard | 728 x 90 | 150 KB | 300 KB | :30 |
| Super Leaderboard / Pushdown | 970 x 90 | 200 KB | 400 KB | no video |
| Medium Rectangle | 300 x 250 | 150 KB | 300 KB | :15 |
| Half Page (standard) | 300 x 600 | 200 KB | not allowed | no video, no expansion |
| Filmstrip | 300 x 600 | 200 KB | 400 KB | :15 |
| Portrait | 300 x 1050 | 250 KB | 500 KB | :15 |
| Skyscraper | 160 x 600 | 150 KB | 300 KB | :15 |
| Smartphone Banner | 300 x 50, 320 x 50 | 50 KB | 100 KB | :15 |
| Financial | 120 x 60 | 150 KB | 300 KB | :15 |
| Pushdown (expanding) | 970 x 90, expands to 850 x 550 or 970 x 550 | 200 KB | 300 KB | :15 |
| Sidekick | 300 x 250, expands to 850 x 700 | 100 KB | 100 KB on click | :15 |
| Slider | page width x 90, active content 950 x 90 | 100 KB | 300 KB | :15 |

## Rich media (display)

| Unit | Sizes (px) | Initial / subload | Notes |
|---|---|---|---|
| In-Banner Video | 300 x 250, 180 x 150, 160 x 600, 728 x 90, 300 x 600 | 200 KB / 100 KB | 3rd-party ad served only; expansion user-initiated |
| Expandable / Retractable | 300x250→600x250, 180x150→600x150, 160x600→600x600, 300x600→600x600, 728x90→728x315 | 200 KB / 300 KB | click to close/expand or mouse-off retraction |
| Interstitial (between-the-page) | variable | 200 KB / 300 KB | "Advertisement" label; Close X if overlaid |
| Floating | variable | 200 KB / 300 KB | "Advertisement" label; Close X on expanded content |

Multi-click-out creatives are not supported site-served; they must run through a 3rd-party ad server.

## Mobile

| Unit | Size (px) | Initial / subload | Animation / video |
|---|---|---|---|
| Adhesion Banner | 320 x 50 | 50 KB / 200 KB | :15 animation, no video; close button upper right; MRAID 1.0 and 2.0 |
| Pull, Slider, Filmstrip Full Screen | 320 x 50, expands full-screen | 50 KB / 200 KB | :15 animation, :30 video |
| Filmstrip (tablet) | 300 x 600 | 200 KB / 300 KB | :15 animation, :30 video |
| Static Banner | 300 x 50 or 320 x 50 | 50 KB / none | :15 animation, no video |
| Static Interstitial | 300 x 250 | 200 KB / none | :15 animation, no video |
| Rich Interstitial | 300 x 250 | 200 KB / 300 KB | :15 animation, :30 video |
| Rich Banner Expandable | 300 x 50 | 50 KB / 200 KB | :15 animation, :30 video |
| Rich Wide Banner Expandable | 320 x 50 | 100 KB / 300 KB | :15 animation, :30 video |

Mobile landing pages must be mobile-optimized; include dimensions in the file name.

## Native

| Field | Spec |
|---|---|
| Headline | max 50 characters |
| Description | 90 characters or less recommended; max 150 |
| Sponsored text (required) | max 25 characters; wording ("Sponsored by", "Ad by", "Promoted by") is set by the publisher |
| Main image | 1000 x 600 recommended; max 1 MB; text in image not recommended |
| Logo image | 1 x 1 aspect ratio supported |
| Tracking | 1x1 impression and click trackers (e.g. DCM) |
| Timing | build 3–6 business days; revisions 1–2 business days; assets due up to 12 business days before launch |

## Electronic Health Records (EHR)

| | Ambulatory systems | Health systems |
|---|---|---|
| Sizes | required 160 x 600 and 728 x 90; most common 300 x 250; also 300 x 600, 120 x 600, 970 x 90 | 728 x 90 only |
| Initial load | 150 KB (160x600, 728x90, 300x250); 200 KB (300x600, 320x600) | 200 KB |
| Subload | 300 KB (160x600, 728x90, 300x250); 400 KB (300x600, 320x600) | — |
| Animation | max :30, 3 loops | animation not supported |
| Formats | static JPG, PNG, GIF with click-through URL; 1x1 trackers or DCM-hosted tags | HTML5 if a scrollable ISI is included, otherwise JPG or PNG; 1P or 3P hosted |

Ambulatory rules: DV, IAS and Moat wrapped tags are not supported, and DV blocking is not recommended. 3rd-party measurement pixels are not supported (privacy). Accepted 1x1s: DoubleVerify and IAS viewability, Google Active View, Crossix DIFA. Audio/video must be user-initiated, with a mute button once sound plays. Ads need a border of at least one pixel. Targeting is US only. Units sit above the fold. Creative goes to PulsePoint for QA at least 48 hours before launch.

Health systems: targeting excludes ABS, SV IT, DV BS and IAS.

## E-Newsletter (eNL)

| | Standard eNL | Endemic eNL | Medscape site |
|---|---|---|---|
| Sizes | 970 x 550, 970 x 250, 300 x 250 (most common), 728 x 90 | 300 x 250 only | 300 x 250 (most delivery), 728 x 90, 300 x 600, 300 x 50, 320 x 50 |
| Formats | JPEG, GIF | JPEG, GIF | HTML, 3rd-party ad served |
| Tracking | up to two 1x1 image impression trackers and one click tracker | image tags or 1x1s fired as URL requests | 1x1s fired as URL requests |

eNL does not support HTML5, rich media, video, iFrame or JavaScript tags; JS-based DoubleVerify brand safety, viewability or IVT filters do not work. eNL targeting is audience only (no contextual). Endemic eNL: keep targeting minimal, no frequency caps, geo no finer than state (national recommended).

## Search Extension

Headline max 50 characters; description max 120 characters; ad-server 1x1 click tracker supported; the display domain shows with the ad.

## Online video (OLV)

| Spec | Value |
|---|---|
| Dimensions | min height 144 px; max 2048 x 1080; recommended 1920 x 1080 (16:9) or 1440 x 1080 (4:3) |
| Aspect ratio | 16:9 or 4:3 |
| Length | :90 or less best practice (:60 or less is eligible on all publishers); :120 recommended max |
| Max upload | 200 MB |
| File types | MOV, MP4, AVI, FLV; VAST and VPAID ad-server tags (e.g. DoubleClick, Innovid) |
| Encoding | progressive, not interlaced |
| Audio | AAC-LC, 44.1 or 48 kHz, stereo, ~128 kbps |

Hosted video is converted to MP4, not compressed. OLV runs in-stream and out-stream unless the buy targets one. Out-stream placements autoplay muted.

## Connected TV (CTV)

| Spec | Value |
|---|---|
| Dimensions | 1920 x 1080 |
| Format | MP4 (MPEG-4) or VAST 2.0 |
| Max upload | 200 MB |
| Length | :30 recommended; :60 and :90 on request to the account team |
| Frame rate | 23.98, 24, 25 or 29.97 fps |
| Audio | stereo PCM, 48 kHz, 16- or 24-bit; AAC at 192 kbps or higher |
| Other | no blended frames; no letterboxing or pillarboxing |

PulsePoint is Innovid-certified for VAST audio on desktop, mobile in-app and CTV.

## Audio

General: VAST URL, VAST XML, or upload of MP3, MPEG, AAC or OGG; at least 128 kbps; :15, :20, :30 or :60, in-stream, non-skippable. WAV is not yet available for upload. 1x1 impression, click and quartile events are supported; viewability does not apply to audio. Audio specs vary by publisher, so confirm with the publisher before trafficking.

| Publisher | Formats | Bitrate | Length | Other |
|---|---|---|---|---|
| Spotify | OGG upload | see Unconfirmed | up to :30 | max 500 MB; VAST 2.0 only; no blocking tags; health/pharma deals need manual Spotify approval |
| Triton Digital | MP3, WAV, WMA, OGG | at least 128 kbps | :15–:60 (:15 and :30 most used), trimmed of slate/silence | 1x1 pixel only |
| AdsWizz (commonly Pandora) | MPEG, WMA, AAC, OGG, MP4, WAV | at least 128 kbps | :15, :30, :60 | max 20 MB; 44,100 Hz |
| Pandora | MP3 | at least 320 kbps | up to :60 on podcast deals, :30 on others | 44.1 kHz; max 2.2 MB; up to VAST 4.0 |

Companion banners: only when wrapped in the VAST tag by a 3rd-party ad server (not uploadable, not hosted in the DSP, no platform reporting). Common sizes 300 x 250 and 320 x 50; also 728 x 90 and 300 x 600.

VAST tags should track start, first quartile, midpoint, third quartile and complete. 1x1s on site-served uploads must be IMG tags.

## DOOH

Max 1920 x 1080; 4K assets are not supported. DOOH specs are set per publisher and screen; PulsePoint connects the buyer with its integrated DOOH vendors for exact specs.

## Unconfirmed values — do not quote

These cells in the source look like typos. Route the question instead of quoting them.

- CTV bitrate: listed as "10,000–40,000 Mbps" (likely kbps).
- Spotify bitrate: listed as "at least 198 bps".

## Open items in the source

The sheet's to-do tab lists these as still being updated: EHR, audio, HTML animation restrictions, eNL, native sizes accepted. Dynamic creative specs have an open, unanswered question.
