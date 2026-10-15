# SEO Explained: motion video

A 62-second, 1920x1080 explainer on what search engine optimization is and how it works, branded for Amiri Digital Agency.

**Output:** `seo-explained.mp4`

## Storyboard

| Time | Scene | Technique |
|---|---|---|
| 0–7s | "Every day, billions of searches. Only a few get found." | Galaxy of particles morphs into a globe; camera rushes through it with a flash cut |
| 7–14s | Search bar types a query, results cascade, "Page one gets the clicks." | 3D-tilted UI, typewriter, light-leak + gold line sweep transition |
| 14–22s | "Search Engine Optimization" collapses into **SEO**, definition beside a morphing liquid-gold blob | Per-letter 3D kinetic type, displaced metallic mesh, zoom-through cut |
| 22–30s | 01 Crawl: bots follow links across a 3D network | Light pulses travel edges, orbiting camera, letterbox |
| 30–37s | 02 Index: network nodes fly into a curved library wall, scanning beam files them | Match-cut morph, tracking shot, whip pan with motion blur |
| 37–46s | 03 Rank: Relevance, Quality, Authority, Experience lift "Your website" to #1 | 3D result cards reorder, glow pulse |
| 46–54s | Three fronts: On-page, Technical, Off-page | Starfield converges into spheres that morph into a document, gear and chain links |
| 54–62s | "Don't chase the algorithm. Be the answer." → Amiri end card | Particles form a rotating ring, light leak, fade |

## Rebuild

```bash
npm install
node render.js out/ 4 30          # renders seg_*.mp4 + segments.txt into out/
python3 soundtrack.py out/soundtrack_raw.wav
ffmpeg -i out/soundtrack_raw.wav -af "highpass=f=30,loudnorm=I=-14:TP=-1.0:LRA=9" -ar 48000 out/soundtrack.wav
ffmpeg -f concat -safe 0 -i out/segments.txt -i out/soundtrack.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart seo-explained.mp4
```

Open `index.html` through any local web server to preview it live in a browser.
Stills for review: `node render.js --stills out/ 5 20 40`.
