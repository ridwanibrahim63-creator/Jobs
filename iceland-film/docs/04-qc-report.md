# Quality-control report

File: `output/iceland_winter_road_trip_9x16.mp4` (v2, re-cut after the reference TikToks and second footage batch arrived)

## Technical (measured on the exported file)

| Check | Result |
|---|---|
| Container / codecs | MP4 (faststart), H.264 High, AAC-LC |
| Resolution / aspect | 1080×1920, 9:16 |
| Frame rate | 30 fps constant, 1044 frames |
| Duration | 34.8 s |
| Video bitrate | 14.0 Mbps (62 MB) |
| Audio | 48 kHz stereo, 256 kbps, −13.1 LUFS integrated, −0.9 dBFS peak |
| Colour tags | Rec.709, yuv420p |
| Black frames | None except the intended fade-out (last 0.2 s) |
| Watermarks | None |
| Source footage | Untouched (read-only) |

## How it was reviewed

I reviewed the export as stills: one frame per beat for the whole film (`docs/contact-sheet.jpg`), full-resolution crops, and frame-by-frame strips across each transition. **I cannot play video or hear audio**, so motion feel and the soundtrack are verified by construction and measurement (cut positions, loudness, waveform), not by watching and listening. Please treat a real playback on your phone as the final check.

## Creative checks

| Question | Finding |
|---|---|
| Does the first second grab? | Map punch-in from frame 1, then nine 0.2 s flashes; the title shot lands at 2.4 s on the first impact. |
| Does pacing match the references? | Flash hook as refs 2 and 4, ~1.2 s body cuts as ref 3, people in roughly half the shots. Shot count went from 17 to 29 in a shorter film. |
| Cinematic, not automated? | Every shot is hand-reframed with keyframes; speed ramps are eased; one shared film grade; cuts on a musical grid. |
| Transitions intentional? | Four in total, each motivated by the footage; the rest are hard cuts on beats. |
| Grade consistent across cameras? | Drone, phone and Fuji clips sit together. The Fuji clips arrive with a heavy green cast; they are auto-neutralised. The geothermal shot reads moody teal and the ice detail slightly turquoise (2.4 s total). |
| Repeated shots? | The nine opening flashes preview moments that return later, by design (as in ref 4). Otherwise nothing repeats; the friend in the snowmobile suit appears twice, from different moments. |
| Story coherent? | Map → road → friends and places (crater, Seljalandsfoss, glacier, geothermal) → Gullfoss build → payoff → sunset. |
| Ending deliberate? | Silhouette eclipses the sun, in-camera bloom to white, sun over the lake slowed and held, 1.2 s fade with a 2.6 s audio tail (unchanged from v1). |
| TikTok safe areas? | Title sits at 25–34% of the height, centred, clear of the top bar, right-hand buttons and caption area. Subjects are kept in the central column. |

## Problems found during review and fixed

1. **Ghosted double images** on the payoff shot (frame blending at 1.3×) → shot now plays at true speed, one crisp source frame per output frame.
2. **Magenta shadows** on the Fuji clips from a fixed chroma offset → replaced with an automatic black/white-point neutral balance per shot.
3. **Stepped "echo" blur** on the hyperlapsed shots → sub-frames are now motion-interpolated before integration, giving smooth motion blur.
4. **Ghosting on the take-off shot** → ramp removed, plays at a constant 2.2× with crisp frames.
5. **File size** 296 MB at first export → capped at 14 Mbps (66 MB).

## Known limitations

- **Resolution.** The supplied files are 720p landscape proxies. A 9:16 crop uses about 405×720 pixels of each frame, upscaled 2.7× to 1080×1920. It holds up at phone size with a light sharpen and fine grain, but it is visibly softer than native footage would be. Dropping the camera originals into the source folder and re-running `edit.py` fixes this with no other changes.
- **References are 16:9; the film is 9:16** as the brief specifies. Say if you want a landscape version.
- **One shot is partly obscured:** in the group huddle a glove swings across the top-right of frame. It reads as playful, but it is the first thing I would swap if you disagree.
- **Soundtrack is synthesised** (pad, felt-piano motif, drums, impacts, wind and water). It is original and safe to publish, but it is not a recorded or mastered piece of music, and I could not listen to it. If you prefer a licensed track or a TikTok sound, cut points are on a 100 BPM grid: a 100 BPM track will line up directly.
- **Camera audio is not used**, for the reason given in the inventory.
- **Slow motion** is limited to the final shot because all footage is 30 fps.
