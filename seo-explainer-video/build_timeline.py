"""Builds timeline.json: a video->design time-warp so every voice-over line fits its scene,
plus the video start time of each line.
Usage: python3 build_timeline.py <vo_durations.json>"""
import json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
DESIGN_END = 72.5   # must match DURATION in index.html
GAP = 0.45          # minimum breath after each line
TAIL = 2.0          # hold after the last line

segs = json.load(open(os.path.join(here, 'vo_script.json')))['segments']
durs = json.load(open(sys.argv[1]))
warp = [[0.0, 0.0]]
placed = []
v_prev, d_prev, dur_prev = 0.0, 0.0, None
for s in segs:
    d = s['anchor']
    need = d - d_prev if dur_prev is None else max(d - d_prev, dur_prev + GAP)
    v = v_prev + need if dur_prev is not None else d  # first line: no stretch before it
    warp.append([round(v, 4), d]); placed.append({'id': s['id'], 'start': round(v, 4), 'dur': durs[s['id']]})
    v_prev, d_prev, dur_prev = v, d, durs[s['id']]
v_end = v_prev + max(DESIGN_END - d_prev, dur_prev + TAIL)
warp.append([round(v_end, 4), DESIGN_END])
json.dump({'duration': round(v_end, 4), 'warp': warp, 'vo': placed}, open(os.path.join(here, 'timeline.json'), 'w'), indent=1)
for (v0, d0), (v1, d1) in zip(warp, warp[1:]):
    if v1 - v0 > 1e-6: print(f'design {d0:6.2f}-{d1:6.2f} -> video {v0:6.2f}-{v1:6.2f}  stretch x{(v1 - v0) / (d1 - d0):.2f}')
print('video duration', round(v_end, 2))
