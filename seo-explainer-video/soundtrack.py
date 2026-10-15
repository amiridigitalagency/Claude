"""Synthesises the soundtrack (pad, pulse, whooshes, impacts, accents) timed to index.html and
mixes in the voice-over with ducking. Event times are written in design-timeline seconds and
mapped to video seconds through timeline.json.
Usage: python3 soundtrack.py <timeline.json> <vo_dir|-> <out.wav>"""
import json, os, sys, wave
import numpy as np

SR = 48000
timeline = json.load(open(sys.argv[1]))
vo_dir, out_path = sys.argv[2], sys.argv[3]
DUR = timeline['duration']
_V = np.array([k[0] for k in timeline['warp']]); _D = np.array([k[1] for k in timeline['warp']])
def W(d):  # design seconds -> video seconds
    return float(np.interp(d, _D, _V))

n = int(SR * DUR)
t = np.arange(n) / SR
rng = np.random.default_rng(7)
L = np.zeros(n); R = np.zeros(n)

def note(m): return 440.0 * 2 ** ((m - 69) / 12)
def env_adsr(length, a, r):
    e = np.ones(length); ai = int(a * SR); ri = int(r * SR)
    e[:ai] = np.linspace(0, 1, ai) ** 2
    e[-ri:] *= np.linspace(1, 0, ri) ** 2
    return e
def add(sig, start, pan=0.0, gain=1.0, buf=None):
    bl, br = (L, R) if buf is None else buf
    i = int(start * SR); j = min(n, i + len(sig)); s = sig[: j - i] * gain
    bl[i:j] += s * np.sqrt((1 - pan) / 2); br[i:j] += s * np.sqrt((1 + pan) / 2)
def fft_filter(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

# --- pad: warm additive chords, slow crossfades
chords = [[57, 60, 64, 71], [53, 57, 60, 64], [48, 55, 60, 64], [55, 59, 62, 67],
          [57, 60, 64, 71], [53, 57, 60, 67], [48, 55, 64, 72], [57, 64, 69, 71]]
seg = DUR / len(chords)
for ci, ch in enumerate(chords):
    start = max(0, ci * seg - 1.5); length = seg + 3.0
    m = int(length * SR); tt = np.arange(m) / SR
    sig = np.zeros(m)
    for k, mn in enumerate(ch):
        f0 = note(mn)
        for det in (-0.12, 0.12):
            ph = rng.uniform(0, 6.28)
            for h in range(1, 7):
                sig += np.sin(2 * np.pi * f0 * h * (1 + det / 100) * tt + ph * h) / (h ** 1.6) * 0.5
    sig *= (0.75 + 0.25 * np.sin(2 * np.pi * 0.15 * tt + ci))
    sig *= env_adsr(m, 2.0, 2.5)
    add(sig, start, pan=(-0.3 if ci % 2 else 0.3), gain=0.016)

# --- plucked arpeggio: mid-range melody that carries on phone speakers
def pluck(at, f0, gain, pan):
    m = int(1.2 * SR); tt = np.arange(m) / SR
    s = sum(np.sin(2 * np.pi * f0 * h * tt) * np.exp(-tt * (3 + h * 2.5)) / h for h in range(1, 6))
    s[: int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    add(s * gain, at, pan)
step = 60 / 96 / 2  # eighth notes at 96 bpm
pattern = [0, 1, 2, 3, 2, 1, 2, 3]
a0, a1 = W(7.0), W(70.0)
k = 0; at = a0
while at < a1:
    ch = chords[min(int(at / seg), len(chords) - 1)]
    mn = ch[pattern[k % 8]] + 12
    ramp = min(1, (at - a0) / 2.5) * (1 - max(0, (at - (a1 - 3)) / 3))
    accent = 1.25 if k % 8 == 0 else 1.0
    pluck(at, note(mn), 0.075 * ramp * accent, 0.35 * np.sin(k * 0.9))
    k += 1; at += step
# sub drone
add(np.sin(2 * np.pi * note(33) * t) * env_adsr(n, 3, 3) * 0.022, 0)

# --- pulse (heartbeat kick) through the "how it works" chapters
beat = 60 / 96
k_len = int(0.45 * SR); kt = np.arange(k_len) / SR
kick = np.sin(2 * np.pi * (45 + 70 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 9)
b0, b1 = W(22.0), W(53.8)
b = b0
while b < b1:
    ramp = min(1, (b - b0) / 3) * (1 - max(0, (b - (b1 - 3)) / 3))
    add(kick, b, gain=0.2 * ramp)
    b += beat

# --- whooshes (rising band-passed noise) into each transition
def whoosh(t_end, length=0.9, gain=0.5):
    m = int(length * SR); x = fft_filter(rng.standard_normal(m), 250, 5000)
    e = np.linspace(0, 1, m) ** 3; e[-int(0.06 * SR):] *= np.linspace(1, 0, int(0.06 * SR))
    x *= e
    i = int((t_end - length) * SR); pan = np.linspace(-0.7, 0.7, m); j = min(n, i + m)
    L[i:j] += (x * np.sqrt((1 - pan) / 2) * gain)[: j - i]
    R[i:j] += (x * np.sqrt((1 + pan) / 2) * gain)[: j - i]
for te, ln, g in [(7.0, 0.9, 0.35), (14.0, 0.8, 0.25), (22.0, 0.9, 0.35), (37.0, 0.6, 0.4), (46.0, 0.8, 0.3), (54.2, 1.2, 0.18), (31.0, 1.4, 0.12)]:
    whoosh(W(te), ln, g)

# --- impacts (low boom + air)
def impact(at, gain=1.0):
    m = int(2.5 * SR); tt = np.arange(m) / SR
    boom = np.sin(2 * np.pi * (38 + 60 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.2)
    air = fft_filter(rng.standard_normal(m), 2000, 12000) * np.exp(-tt * 9) * 0.25
    add((boom * 0.8 + air) * gain, at)
for at, g in [(7.0, 0.55), (22.0, 0.55), (46.0, 0.45), (61.2, 0.5), (14.05, 0.25)]:
    impact(W(at), g)

# --- shimmer accents (bell partials)
def bell(at, base=1318.5, gain=0.12, pan=0.0):
    m = int(3.0 * SR); tt = np.arange(m) / SR
    s = sum(np.sin(2 * np.pi * base * r * tt) * a * np.exp(-tt * d) for r, a, d in [(1, 1, 2.0), (2.01, .4, 3.5), (3.0, .25, 5), (4.2, .12, 7)])
    s[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    add(s * gain, at, pan)
for at, base, pan in [(4.6, 1318.5, 0.2), (17.25, 1760.0, -0.2), (19.7, 1318.5, 0.3), (45.0, 1760.0, 0.25), (61.2, 1318.5, 0), (64.2, 1760.0, -0.1), (65.6, 2637.0, 0.2)]:
    bell(W(at), base, 0.09, pan)
# rank climb plucks (rising)
for at, mn in zip([39.3, 40.9, 42.5, 44.1], [69, 72, 76, 81]):
    bell(W(at), note(mn), 0.08, 0.3)
# crawl blips as nodes are discovered (sparse)
for k in range(22):
    bell(W(23.0 + k * 0.28 + rng.uniform(0, 0.1)), note(81 + int(rng.integers(0, 3)) * 2), 0.018, rng.uniform(-0.6, 0.6))

# --- typing clicks + enter
q = 'how do search engines work'
for c in range(len(q)):
    at = W(8.0 + 1.55 * (c + 1) / len(q)) + rng.uniform(-0.015, 0.015)
    m = int(0.03 * SR); x = fft_filter(rng.standard_normal(m), 1500, 9000) * np.exp(-np.arange(m) / SR * 220)
    add(x * 0.22, at, pan=rng.uniform(-0.2, 0.2))
m = int(0.08 * SR); add(fft_filter(rng.standard_normal(m), 600, 6000) * np.exp(-np.arange(m) / SR * 80) * 0.35, W(9.8))

# --- simple stereo reverb (decaying noise IR, FFT convolution)
def reverb(x, secs=2.2, seed=1):
    r = np.random.default_rng(seed); m = int(secs * SR)
    ir = r.standard_normal(m) * np.exp(-np.arange(m) / SR * 3.2); ir = fft_filter(ir, 200, 7000); ir /= np.abs(ir).sum() / 8
    N2 = 1 << int(np.ceil(np.log2(len(x) + m)))
    return np.fft.irfft(np.fft.rfft(x, N2) * np.fft.rfft(ir, N2), N2)[: len(x)]
L = L + 0.22 * reverb(L, seed=1); R = R + 0.22 * reverb(R, seed=2)
fade = np.clip((DUR - t) / 1.2, 0, 1); fin = np.clip(t / 0.4, 0, 1)
L *= fade * fin; R *= fade * fin
rms = lambda *ch: np.sqrt(np.mean(np.concatenate(ch) ** 2))

# --- voice-over: placed per timeline.json, music ducked underneath
if vo_dir != '-':
    import soundfile as sf
    VL = np.zeros(n); VR = np.zeros(n); presence = np.zeros(n)
    for seg_ in timeline['vo']:
        x, sr = sf.read(os.path.join(vo_dir, seg_['id'] + '.wav'), dtype='float64')
        if x.ndim > 1: x = x.mean(1)
        if sr != SR:  # band-limited resample via FFT
            m2 = int(round(len(x) * SR / sr)); X = np.fft.rfft(x); Y = np.zeros(m2 // 2 + 1, complex)
            c = min(len(X), len(Y)); Y[:c] = X[:c]; x = np.fft.irfft(Y, m2) * (m2 / len(x))
        x = fft_filter(x, 70, 16000)
        add(x, seg_['start'], 0.0, 1.0, (VL, VR))
        i = int(seg_['start'] * SR); presence[i: i + len(x)] = 1
    # smooth ducking envelope: 120 ms attack, 600 ms release
    kern_a = int(0.12 * SR); kern_r = int(0.6 * SR)
    duck = np.convolve(presence, np.ones(kern_r) / kern_r, 'full')[:n]
    duck = np.maximum(duck, np.concatenate([np.convolve(presence, np.ones(kern_a) / kern_a, 'full')[kern_a - 1:], np.zeros(0)])[:n])
    duck = np.clip(duck * 1.5, 0, 1)
    voice_rms = rms(VL[presence > 0], VR[presence > 0])
    music_rms = rms(L, R)
    g_music = (voice_rms / music_rms) * 10 ** (-9 / 20)   # music bed ~9 dB under the voice
    gain = g_music * (1 - 0.5 * duck)                      # a further ~6 dB dip while she speaks
    L = L * gain + VL; R = R * gain + VR

# master: soft clip and normalise (final loudness set with ffmpeg loudnorm)
peak = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(L / peak * 1.2) / np.tanh(1.2) * 0.89; R = np.tanh(R / peak * 1.2) / np.tanh(1.2) * 0.89
pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(out_path, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', out_path, round(DUR, 2), 's')
