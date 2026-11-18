# 文ごとの声の高さ（基本の高さ Hz の中央値）を測る（3本目 v10「8分あたりから声がずっと高い」）
#   使い方：python3 line_pitch.py voice.wav word_times.json  → 文の ID・高さ・全体の中央値との差
import json, sys, wave
import numpy as np

def f0_track(x, sr, lo=120, hi=400, win=0.04, hop=0.01):
    n = int(win * sr); h = int(hop * sr); out = []
    for i in range(0, len(x) - n, h):
        f = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt((f ** 2).mean()) < 0.02: continue
        ac = np.correlate(f, f, "full")[n - 1:]; ac /= ac[0] + 1e-9
        a, b = int(sr / hi), int(sr / lo)
        k = a + int(np.argmax(ac[a:b]))
        if ac[k] > 0.5: out.append(sr / k)
    return np.array(out)

def measure(wav, wt):
    with wave.open(wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; sr = w.getframerate()
    d = json.load(open(wt)); res = {}
    for k, v in d.items():
        seg = x[int(v["start"] * sr):int(v["end"] * sr)]
        f = f0_track(seg, sr)
        if len(f) > 10: res[k] = float(np.median(f))
    return res

if __name__ == "__main__":
    r = measure(sys.argv[1], sys.argv[2]); med = float(np.median(list(r.values())))
    print("全体の中央値 %.0f Hz" % med)
    for k, f in r.items(): print("%-7s %4.0f Hz %+4.0f%s" % (k, f, f - med, "  ← 高い" if f - med >= 20 else ""))
