# SEO Explained: motion video

A ~78-second, 1920x1080 explainer with voice-over on what search engine optimization is and how it works, branded for Amiri Digital Agency.

**Output:** `seo-explained.mp4`

## Storyboard

Times are on the design timeline; the voice-over warp stretches them to ~78 s in the final video.

| Time | Scene | Technique |
|---|---|---|
| 0–7s | "Every day, billions of searches. Only a few get found." | Galaxy of particles morphs into a globe; camera rushes through it with a flash cut |
| 7–14s | Search bar types a query, results cascade, "Page one gets the clicks." | 3D-tilted UI, typewriter, light-leak + gold line sweep transition |
| 14–22s | "Search Engine Optimization" collapses into **SEO**, definition beside a morphing liquid-gold blob | Per-letter 3D kinetic type, displaced metallic mesh, zoom-through cut |
| 22–30s | 01 Crawl: bots follow links across a 3D network | Light pulses travel edges, orbiting camera, letterbox |
| 30–37s | 02 Index: network nodes fly into a curved library wall, scanning beam files them | Match-cut morph, tracking shot, whip pan with motion blur |
| 37–46s | 03 Rank: Relevance, Quality, Authority, Experience lift "Your website" to #1 | 3D result cards reorder, glow pulse |
| 46–54s | Three fronts: On-page, Technical, Off-page | Starfield converges into spheres that morph into a document, gear and chain links |
| 54–72s | "Don't chase the algorithm." → "They find you." → "Want to be the answer?" Amiri end card + "Book your free SEO strategy call" | Particles form a rotating ring, light leak, gold CTA button |

Narrated with the open-source Kokoro-82M voice `af_heart` (fp16 ONNX, espeak-ng phonemes). The script lives in
`vo_script.json`; each line has an *anchor* on the design timeline in `index.html`. `build_timeline.py` writes
`timeline.json`, a time-warp that stretches each scene just enough to fit its line, so visuals and voice stay in sync.

Story structure: **hook** (someone is searching for what you offer, will they find you?), explanation
(what SEO is, crawl, index, rank, three fronts), **payoff** (…they find you) and **CTA** (book a free SEO strategy call).

## Rebuild

```bash
npm install
pip install kokoro-onnx soundfile
python3 tts.py <kokoro-fp16.onnx> <voices.npz> af_heart en-us out/vo 1.0   # voice lines + vo_durations.json
python3 build_timeline.py out/vo/vo_durations.json                          # timeline.json
node render.js out/ 4 30                                                    # seg_*.mp4 + segments.txt
python3 soundtrack.py timeline.json out/vo out/mix_raw.wav                  # music, SFX and ducked voice
ffmpeg -i out/mix_raw.wav -af "highpass=f=30,loudnorm=I=-14:TP=-1.0:LRA=11" -ar 48000 out/mix.wav
ffmpeg -f concat -safe 0 -i out/segments.txt -i out/mix.wav -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart seo-explained.mp4
```

The Kokoro weights are not in this repo. `voices.npz` is built from the `voices/*.bin` style vectors in the `kokoro-js` npm package.
Open `index.html` through any local web server to preview it live. Stills for review: `node render.js --stills out/ 5 20 40`.
