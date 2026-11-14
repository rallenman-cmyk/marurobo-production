# 声の調子がまわりと違うまとめ（batch）を、何回か作り直して、まわりに一番近いものを選ぶ
# MARU_WORK=<作業フォルダ> python3 retake_batches.py 2,4,12 [回数=3]
#   比べる物：声の高さ（中央値）・明るさ（周波数の重心）・話す速さ（1 字あたりの秒）。全体の中央値との差を、ばらつきで割って足す
#   前の版は batch_XX_before_retake.wav に残す。選んだら split_narration.py で切り直す（手で作り直した文は、あとで戻す）
import os, sys, json, wave, subprocess, shutil
import numpy as np
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
B = [int(x) for x in sys.argv[1].split(",")]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 3
FIX = json.load(open(D + "/tts_text.json", encoding="utf-8"))
STYLE = W + "/stage/voice_test/style_gentle.txt"
TOOLS = W + "/tools"


def rd(p):
    with wave.open(p) as w: sr = w.getframerate(); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, sr


def feat(p, chars):
    x, sr = rd(p); fr = int(0.04 * sr); hop = int(0.02 * sr); f = []
    for i in range(0, len(x) - fr, hop):
        s = x[i:i + fr]
        if np.sqrt((s ** 2).mean()) < 0.02: continue
        s = s - s.mean(); ac = np.correlate(s, s, 'full')[fr - 1:]
        lo, hi = int(sr / 400), int(sr / 120); k = lo + np.argmax(ac[lo:hi])
        if ac[k] > 0.4 * ac[0]: f.append(sr / k)
    X = np.abs(np.fft.rfft(x)); q = np.fft.rfftfreq(len(x), 1 / sr)
    return np.array([np.median(f), (X * q).sum() / X.sum(), len(x) / sr / chars * 100])


allf = []
for b in range(100):
    p = D + "/batch_%02d.wav" % b
    if not os.path.exists(p): break
    j = json.load(open(D + "/batch_%02d.json" % b, encoding="utf-8"))
    allf.append(feat(p, sum(len(t) for t in j["tts"])))
allf = np.array(allf); med = np.median(allf, 0); sd = allf.std(0)
score = lambda v: float((np.abs(v - med) / sd).sum())
for b in B:
    j = json.load(open(D + "/batch_%02d.json" % b, encoding="utf-8"))
    texts = j["tts"]; chars = sum(len(t) for t in texts)
    cand = [(score(allf[b]), D + "/batch_%02d.wav" % b)]
    tf = W + "/retake_%02d.txt" % b; open(tf, "w", encoding="utf-8").write("\n".join(texts))
    for k in range(N):
        out = W + "/retake_%02d_%d.wav" % (b, k)
        subprocess.run(["python3", TOOLS + "/gemini_tts2.py", out, "Achernar", tf, STYLE], capture_output=True)
        if os.path.exists(out): cand.append((score(feat(out, chars)), out))
    cand.sort()
    print("batch %02d" % b, " ".join("%.2f%s" % (s, "*" if p.endswith("%02d.wav" % b) else "") for s, p in cand), "→", os.path.basename(cand[0][1]))
    if not cand[0][1].endswith("batch_%02d.wav" % b):
        shutil.copy(D + "/batch_%02d.wav" % b, D + "/batch_%02d_before_retake.wav" % b)
        shutil.copy(cand[0][1], D + "/batch_%02d.wav" % b)
