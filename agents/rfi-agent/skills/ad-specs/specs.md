# PulsePoint ad specs (structured)

Source: "PulsePoint_Ad Specs_Master_(Ref for KnowledgeBase)", Google Doc — https://docs.google.com/document/d/10QWSP4p95gYEgvkFLXEtonDVd_aBEUTCVCCkh7eiyvk/edit
Last modified 2026-11-02 (Andrew Portener). File owner Sanwari Gupta.
This is the master ad specs doc the CS team uses and the reference behind the Knowledge Base guide. It replaces the internal "[MASTER] 2025 Ad Specs Update - WIP.xlsx" sheet, which earlier drafts of this skill used.

Source disclaimer, client-safe: PulsePoint accepts almost any ad format; these specs give the widest acceptance across inventory sources, and the PulsePoint team confirms anything else.

## General display requirements (all display and mobile ads)

- Submission lead time: ad files at least 6 days before campaign start.
- Max CPU: 30% during host-initiated execution.
- Max host-initiated file requests: 15 during initial load and host-initiated subload; unlimited after user interaction.
- File weight counts every file (.html, .js, .css, images), including shared libraries unless the publisher exempts them, measured after gzip.
- Host-initiated subload may start one second after the browser's `domContentLoadedEventEnd`. User-initiated file load is unlimited where subload is allowed.
- Audio must be user-initiated. Hotspots: no larger than 1/4 of the ad, triggered after the cursor rests at least 1 second, never start audio.
- Ads need clearly defined borders so they are distinguishable from page content.
- Behaviorally targeted ads include IBA self-regulation controls (5 KB max).
- Video in display: minimum 24 fps. Controls may be omitted until user interaction; then Play, Pause and Mute (or volume to 0) are required. Autoplay in-banner video needs Mute only. Provide MP4/H.264 (Baseline profile) with AAC audio; WebM/VP8 alternates are optional. Encode web-optimized (moov atom at start).
- HTML5 is the standard; any Flash references in IAB style guides should be read as HTML5.

## Display: IAB Rising Stars

Rising Stars units should be the only rich media unit on a page. Style guides: www.iab.com/risingstars.

| Unit | Initial size (px) | Max expanded (px) | Max initial load | Host-initiated subload | Animation / video | Z-index |
|---|---|---|---|---|---|---|
| Billboard | 970 x 250 | initiates expanded | 200 KB | 1 MB | :30 video max (unlimited user-initiated); +2.2 MB for host-initiated video | 0–4,999 |
| Filmstrip | 300 x 600 window, 300 x 3000 scrolling ad (5 segments) | expansion not allowed | 200 KB | 300 KB | :15 video max; +1.1 MB host-initiated video | 0–4,999 |
| Pushdown | 970 x 90 (some publishers 970 x 66) | 970 x 415 | 200 KB | 300 KB | :15 video max; +1.1 MB host-initiated video | 0–4,999 |
| Sidekick | 300 x 250, 300 x 600, 970 x 250 | 850 x 550 (optional 970 x 550) | 200 KB | 300 KB | :15 video max; +1.1 MB host-initiated video | 5,000–1,999,999 |
| Slider | page width x 90, active content centered in 970 x 90 | 970 x 550 behind slider bar | 200 KB | 300 KB | :15 video max; +1.1 MB host-initiated video | 5,000–1,999,999 |

User-initiated video or animation has no file size limit on these units. Billboard collapses to "Show Ad" text with icon. Slider must include "Close X" on the bar and the content.

## Display: Universal Ad Package (UAP) and other standard units

No expansion, no host-initiated subload, no video (use In-Banner Video below). Animation max :15 unless noted.

| Unit | Size (px) | Max initial load |
|---|---|---|
| Medium Rectangle | 300 x 250 | 200 KB |
| Rectangle | 180 x 150 | 80 KB |
| Wide Skyscraper | 160 x 600 | 200 KB |
| Leaderboard | 728 x 90 | 200 KB |
| Super Leaderboard (provisional) | 970 x 90 (some publishers 970 x 66) | 200 KB |
| Half Page | 300 x 600 | 200 KB |

## Rich media (display)

Examples, not all-inclusive; 3rd-party ad tags can run a range of creative across supply.

| Unit | Sizes (px) | Initial / subload | Video | Notes |
|---|---|---|---|---|
| In-Banner Video | 300 x 250, 180 x 150, 160 x 600, 728 x 90, 300 x 600 | 200 KB / 100 KB | :15 max; +1.1 MB host-initiated | 3rd-party ad served only; no expansion |
| Expandable / Retractable | 300x250→600x250, 180x150→600x150, 160x600→600x600, 300x600→600x600, 728x90→728x315 | 200 KB / 300 KB | :15 max; +1.1 MB host-initiated | expansion user-initiated; click to close/expand or mouse-off retraction; 3rd-party ad served only; z-index 5,000–1,999,999 |
| Between-the-Page (interstitial) | variable | 200 KB / 300 KB | :15 max; +1.1 MB host-initiated | "Advertisement" label, 8–16 pt; Close X if overlaid on the page; 3rd-party ad served only |

## Medscape (site)

Sizes 300 x 250, 728 x 90, 300 x 600, 300 x 50, 320 x 50. Creative can be HTML but must be 3rd-party served; 1x1s execute as URL requests.

## Mobile: IAB units

| Unit | Initial | Expanded | Initial / subload | Animation / video | Z-index |
|---|---|---|---|---|---|
| 320 x 50 Adhesion Banner | 320 x 50 | n/a | 50 KB / 200 KB | :15 animation, no video | 0–4,999 |
| 320 x 50 Pull | 320 x 50 | full screen (varies by device) | 50 KB / 200 KB | :15 animation, :30 video; +2.2 MB host-initiated video | 0–4,999 |
| 320 x 50 Slider | 320 x 50 | full screen | 50 KB / 200 KB | :15 animation, :30 video | 5,000–1,999,999 |
| 300 x 600 Filmstrip (tablet) | 300 x 600 | 300 x 600 | 200 KB / 300 KB | :15 animation, :30 video | 0–4,999 |
| 320 x 50 Filmstrip Full Screen | 320 x 50 | full screen | 50 KB / 200 KB | :15 animation, :30 video | 5,000–1,999,999 |
| 320 x 50 Full Page Flex | 320 x 50 | full screen | phone 200 KB, tablet 300 KB / 300 KB | :15 animation, :30 video | 5,000–1,999,999 |

Adhesion banner: close button upper right; MRAID 1.0 and 2.0 compatible. Pull: close button about 40 x 40 upper right.

## Mobile: image ads

| Unit | Size (px) | Initial / subload | Animation / video |
|---|---|---|---|
| Smartphone Static Banner | 300 x 50 | 50 KB / none | :15 animation, no video |
| Smartphone Static Wide Banner | 320 x 50 | 50 KB / none | :15 animation, no video |
| Smartphone Interstitial | 300 x 250 | 200 KB / none | :15 animation, no video |
| Feature phone Small / Medium / Large Banner | 120 x 20 / 168 x 28 / 216 x 36 | 5 KB / none | :15 animation, no video |
| Smartphone Rich Interstitial | 300 x 250 | 200 KB / 300 KB | :15 animation, :30 video |
| Smartphone Rich Banner Expandable | 300 x 50, expands full screen | 50 KB / 200 KB | :15 animation, :30 video |
| Smartphone Rich Wide Banner Expandable | 320 x 50, expands full screen | 100 KB / 300 KB | :15 animation, :30 video |

Mobile landing pages must be mobile-optimized; include dimensions in the file name; use MRAID where appropriate. On 3G or slower connections, reduce file weights by 30%. High-density screens may take up to 2x the listed weights (confirm with the publisher).

## Native

| Field | Spec |
|---|---|
| Headline | max 50 characters |
| Description | 90 characters or less recommended; max 150 |
| Sponsored text (required) | max 25 characters; wording ("Sponsored by", "Ad by", "Promoted by") is set by each publisher |
| Main image | 1000 x 600 recommended; max 1 MB; text in image not recommended |
| Logo image | 1 x 1 |
| Tracking | 1x1 impression and click trackers (e.g. DCM) |
| Timing | demo links 3–6 business days; revisions 1–2 business days; assets due up to 12 business days before launch |

## Online video (OLV)

| Spec | Value |
|---|---|
| Dimensions | min height 144 px; max 2048 x 1080; recommended 1920 x 1080 (16:9) or 1440 x 1080 (4:3) |
| Aspect ratio | 16:9 recommended; 4:3 compatible |
| Length | :90 or less recommended; :120 max |
| Max upload | 200 MB |
| File types | MOV, MP4, AVI, FLV; VPAID/VAST ad-server tags (e.g. DoubleClick, Innovid) |
| Encoding | progressive, not interlaced |

PulsePoint does not compress video; hosted files are converted to MP4. Out-stream OLV placements autoplay muted.

## Connected TV (CTV)

| Spec | Value |
|---|---|
| Dimensions | 1920 x 1080 |
| Format / tag | MP4; VAST 2.0 or 3.0 (3rd-party served, to meet major CTV publishers' requirements) |
| Bitrate | 15–30 Mbps |
| Max upload | 250 MB |
| Length | :30 or less recommended; :60 and :90 accepted (contact the account team) |
| Frame rate | 23.98, 24, 25, 29.97 or 30 fps, constant frame rate |
| Video codec | H.264 |
| Audio | 48 kHz sample rate, 16- or 24-bit; AAC |
| Other | no blended frames; no letterboxing or pillarboxing |

Certifications: Innovid VAST audio on desktop, mobile in-app and CTV.

## CTV pause ads

Shown when a viewer pauses streaming video on a connected TV.

| Spec | Value |
|---|---|
| Dimensions | 1920 x 1080 |
| Bitrate | 5 Mbps or higher |
| Format | MP4, uncompressed; VAST only |
| Max upload | 200 MB |
| Duration | :30 |
| Frame rate | 29.97 fps |
| Audio | none; include a muted audio channel |

3rd-party tracking pixels are allowed; 3rd-party viewability measurement is not supported. Keep copy and logos out of the lower third; images must be opaque; no CTAs or button graphics (viewers may think they are clickable).

## Search extension

Headline max 50 characters; description max 120 characters; ad-server 1x1 click tracker supported; the display domain shows with the ad (e.g. www.pulsepoint.com).

## Audio

| Spec | Value |
|---|---|
| Format | MP3 or WAV |
| Max file size | 50 MB (Katz Media: 1 MB max) |
| Bitrate | 192–320 kbps, constant bitrate |
| Length | :15, :30; :60 and :90 on request |
| Tracking | 1x1 pixels for audio impressions and quartiles |

Companion banners: only when wrapped in the VAST tag by a 3rd-party ad server; not supported when the creative is hosted in the DSP, so no platform reporting and PulsePoint cannot monitor or troubleshoot them. Sizes: 300 x 250 (most common), 320 x 50 (mobile), 728 x 90 (desktop/tablet), 300 x 600 (less common). Always check publisher specs.

VAST tags should track start, first quartile, midpoint, third quartile and complete. With a companion wrapped in VAST, use UTM parameters on the landing page. 1x1s on site-served uploads must be IMG tags with the HTML stripped.

## DOOH

DOOH is bespoke: specs differ by publisher, screen size and content rules, so work with the publishers being activated. 4K assets are not supported. Min and max file sizes vary by publisher (the PX rep confirms).

| | Common sizes (px) | File types and settings |
|---|---|---|
| Display | 1920 x 1080 (landscape), 1080 x 1920 (portrait), 1400 x 400 and 840 x 400 (billboards, taxi tops, transit) | JPG or PNG, 72 ppi |
| Video | 1920 x 1080, 1080 x 1920, 1400 x 400 | MP4 with even-numbered pixel resolution; under 5,000 kbps; 30 fps; VAST tags not wrapped with DV/IAS/MOAT; VPAID not supported |

Landscape and portrait venues include entertainment, health and beauty, movie theaters, office buildings, point of care, residential, retail, transit and urban panels.

## Electronic Health Records (EHR)

| | EHR (ambulatory) | EHR (health systems) |
|---|---|---|
| Sizes | required 160 x 600, 728 x 90, 300 x 250 | 728 x 90 only |
| Ad serving | static images with 1x1 trackers, or DCM-wrapped tags only | 1P and 3P hosted |
| Initial load | 150 KB | static 200 KB; animated 500 KB |
| Subload | 300 KB | — |
| Animation | up to :30, up to 3 loops, up to 60 fps | under :30; HTML5 or GIF; no flashing, blinking or shaking |
| Static formats | JPG, PNG or GIF with click-through URL | HTML5 if it includes a scrollable ISI, otherwise JPG or PNG |

Ambulatory rules: DV, IAS and Moat wrapped tags are not supported; DV blocking is not recommended. 3rd-party measurement pixels are not supported (privacy). Accepted 1x1s: DoubleVerify and IAS viewability, Google Active View, Crossix DIFA. No autoplay: audio/video must be user-initiated, with a mute button once sound plays. Ads need a border of at least one pixel. US targeting only. Banners sit above the fold. Creative goes to PulsePoint for QA and approval at least 48 hours before launch.

Health systems rules: targeting excludes ABS, SV IT, DV BS and IAS. DV, IAS and Moat wrapped tags are not supported; DV blocking is not recommended. No audio or video. Images 72 dpi with no people, body parts or animals. No questions in the copy. Avoid bright or neon colors unless they are the brand logo. A static backup image is recommended.

## E-Newsletter (eNL)

| | Non-endemic (LiveIntent) | Endemic |
|---|---|---|
| Sizes | recommended 970 x 550, 970 x 250, 300 x 250; optional 728 x 90; most used 300 x 250 | 300 x 250 image only (most used); 728 x 90 for the Cleveland Clinic Medical Journal deal only |
| Formats | JPEG and GIF only | image tags only; no HTML5, JavaScript or GIF |
| Tracking | up to two 1x1 image impression trackers and one click tracker | 3rd-party 1x1 tracking tags not accepted; 1x1 image tags only execute as URL requests |

Non-endemic: audience targeting only (no contextual). Do not apply DoubleVerify brand safety, viewability or IVT filters (they rely on JavaScript). Not supported: HTML5, rich media, video, iFrame and JavaScript tags.

Endemic publishers include Medscape, MD Edge, Haymarket Tier 1 and Tier 2, Bulletin Health, Healio, Cleveland Clinic Medical Journal and the Endemic Curated Market eNL.

## Z-index ranges (display)

| Range | Layer |
|---|---|
| below 0 | background elements |
| 0–4,999 | main content and standard ads (including the CLEAR ad notice) |
| 5,000–1,999,999 | expanding ads (whole unit) |
| 2,000,000–2,999,999 | floating ads (over-the-page) |
| 3,000,000–3,999,999 | pop-up elements (chat, notifications) |
| 4,000,000–4,999,999 | non-anchored floating elements (survey panels) |
| 5,000,000–5,999,999 | expanding site navigation |
| 6,000,000+ | full-page overlays (full-window OTP and between-the-page ads that cover content) |

Publishers' own z-index guidelines take precedence.

## Pop-ups

Max one pop-up per user per site visit. Label the browser window with network or advertiser name, publisher name and browser type. Pop-Up 300 x 250: 40 KB initial, 100 KB polite subload, 2.2 MB user-initiated; audio/video user-initiated; close box controlled by the browser.

## Unconfirmed values — do not quote

These cells in the source look like typos or contradict another part of the doc. Route the question instead of quoting them.

- DOOH "Max Size: 920x1080": conflicts with the doc's own 1920 x 1080 common sizes; likely 1920 x 1080.
- CTV pause ads: "All VAST tags and tracking pixels must be secured and start with http://": "secured" implies https://.
- EHR health systems animation "Frame: < 10 RFP": unit unclear (likely fps).
- CTV audio bitrate: the CTV table says AAC 192 kbps or higher, but its notes say ~128 kbps (AAC-LC, 44.1 or 48 kHz, stereo).
- Pop-Up Large size "550x48": likely truncated.
- Filmstrip in the glossary is 350 x 3000 / 350 x 600; the spec table (300 x 3000 / 300 x 600) is the value to quote.

## Not covered by the source

Dynamic creative specs; ad podding, pod sizes and SSAI on CTV; publisher-specific audio specs (Spotify, Pandora, Triton, etc.); screen-level DOOH file limits.
