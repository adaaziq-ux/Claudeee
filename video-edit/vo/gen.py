import json, os, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
K = os.environ.get('KOKORO_DIR', 'kokoro/')  # kokoro-v1.0.onnx + voices-v1.0.bin
OUT = sys.argv[1]
kok = Kokoro(K + 'kokoro-v1.0.onnx', K + 'voices-v1.0.bin')
# id, start, end (window the line must fit), text
LINES = json.load(open(OUT + '/lines.json'))
VOICES = {'male': 'am_michael', 'female': 'af_heart'}
report = {}
for vk, voice in VOICES.items():
    for ln in LINES:
        win = ln['end'] - ln['start']
        speed = 1.05
        for _ in range(6):
            samples, sr = kok.create(ln['text'], voice=voice, speed=speed, lang='en-us')
            # trim leading/trailing silence
            nz = np.where(np.abs(samples) > 0.01)[0]
            samples = samples[max(0, nz[0] - 240): nz[-1] + 2400]
            dur = len(samples) / sr
            if dur <= win or speed >= 1.15: break
            speed = min(1.15, speed * dur / win + 0.02)
        sf.write(f"{OUT}/{vk}_{ln['id']}.wav", samples, sr)
        report[f"{vk}_{ln['id']}"] = (round(dur, 2), round(win, 2), round(speed, 2))
for k, v in report.items(): print(k, 'dur', v[0], 'win', v[1], 'speed', v[2], 'OVER' if v[0] > v[1] else '')
