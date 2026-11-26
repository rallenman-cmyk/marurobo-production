# 文ごとの声の高さ（中央値 Hz）を測り、全体の中央値より 20Hz 以上高い・低い文を出す（SKILL §5「声の高さを文ごとに測る」3本目 v9）
# MARU_WORK=<作業フォルダ> python3 pitch_lines.py
import os, json, wave
import numpy as np
D = os.environ["MARU_WORK"] + "/stage/voice/achernar"
L = {e["no"]: e for e in json.load(open(os.environ["MARU_WORK"] + "/stage/script/script_v2_timed.json", encoding="utf-8"))}
def f0(x, sr):
    fr = int(0.04 * sr); hop = int(0.02 * sr); out = []
    for i in range(0, len(x) - fr, hop):
        y = x[i:i + fr]
        if np.sqrt((y ** 2).mean()) < 0.03: continue
        y = y - y.mean(); c = np.correlate(y, y, "full")[fr - 1:]
        lo, hi = int(sr / 400), int(sr / 120)
        k = lo + np.argmax(c[lo:hi])
        if c[k] > 0.5 * c[0]: out.append(sr / k)
    return np.median(out) if out else None
R = {}
for no in sorted(L):
    with wave.open(D + "/line_%03d.wav" % no) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    R[no] = f0(x, sr)
med = np.median([v for v in R.values() if v])
print("全体の中央値 %.0f Hz" % med)
for no, v in R.items():
    if v and abs(v - med) >= 20: print(no, L[no]["id"], "%.0f Hz（%+.0f）" % (v, v - med), L[no]["text"])
