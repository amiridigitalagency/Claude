"""Voice-over synthesis with Kokoro-82M (ONNX) and espeak-ng phonemes.
Usage: python3 tts.py <model.onnx> <voices.npz> <voice> <lang> <out_dir> [speed]
Reads vo_script.json and writes one WAV per segment plus vo_durations.json."""
import json, os, re, sys
import numpy as np, onnxruntime as ort, soundfile as sf
from kokoro_onnx.tokenizer import Tokenizer

SR = 24000
model, voices_path, voice, lang, out_dir = sys.argv[1:6]
speed = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(out_dir, exist_ok=True)

sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
style_bank = np.load(voices_path)[voice]
tok = Tokenizer()

def speak(text):
    # sentence by sentence keeps each call well under the 510-token limit
    parts = [p for p in re.split(r'(?<=[.?!])\s+', text.strip()) if p]
    out = []
    for i, p in enumerate(parts):
        ids = tok.tokenize(tok.phonemize(p, lang))[:500]
        style = style_bank[len(ids)].astype(np.float32)
        # the fp16 export occasionally overflows to NaN on a given input; an inaudible speed nudge avoids it
        for sp in (speed, speed + 0.01, speed - 0.01, speed + 0.02, speed - 0.02):
            wav = sess.run(None, {'input_ids': np.array([[0, *ids, 0]], dtype=np.int64), 'style': style,
                                  'speed': np.array([sp], dtype=np.float32)})[0][0]
            if np.isfinite(wav).all() and np.abs(wav).max() < 1.5: break
        else:
            raise RuntimeError(f'could not synthesise cleanly: {p!r}')
        # trim leading/trailing near-silence
        idx = np.where(np.abs(wav) > 0.01)[0]
        if len(idx): wav = wav[max(0, idx[0] - 240): idx[-1] + 2400]
        out.append(wav)
        if i < len(parts) - 1: out.append(np.zeros(int(0.32 * SR), dtype=np.float32))
    return np.concatenate(out)

script = json.load(open(os.path.join(here, 'vo_script.json')))
durs = {}
for seg in script['segments']:
    wav = speak(seg['say'])
    sf.write(os.path.join(out_dir, seg['id'] + '.wav'), wav, SR)
    durs[seg['id']] = round(len(wav) / SR, 3)
    print(seg['id'], durs[seg['id']], 's')
json.dump(durs, open(os.path.join(out_dir, 'vo_durations.json'), 'w'), indent=1)
