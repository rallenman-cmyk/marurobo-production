# まとめて読ませた声の、文と文の分け目を手で直す（英字を 1 つずつ読む間を、文の切れ目と取り違えた所）
# MARU_WORK=<作業フォルダ> python3 resplit.py list <batch> <秒0> <秒1>      … その範囲の無音（0.12 秒以上）を並べる
# MARU_WORK=<作業フォルダ> python3 resplit.py cut <batch> <番号a> <番号b> <分け目の秒>   … a の終わりと b の頭を、その秒の無音の真ん中で分け直す
import os, sys, json, wave
import numpy as np
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
FR = 0.01; THR = 10 ** (-42 / 20); PAD = 0.04


def load(p):
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x, sr


def sil(x, sr, t0, t1):
    h = int(FR * sr); n = len(x) // h; e = np.abs(x[:n * h]).reshape(n, h).max(1) < THR
    out, k = [], int(t0 / FR)
    while k < min(n, int(t1 / FR)):
        if e[k]:
            j = k
            while j < n and e[j]: j += 1
            if (j - k) * FR >= 0.12: out.append((round(k * FR, 2), round(j * FR, 2)))
            k = j
        else: k += 1
    return out


def save(x, sr, a, b, p):
    seg = x[int(a * sr):int(b * sr)]
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((seg * 32767).astype(np.int16).tobytes())


if sys.argv[1] == "list":
    x, sr = load(D + "/%s.wav" % sys.argv[2]); print(sil(x, sr, float(sys.argv[3]), float(sys.argv[4])))
else:
    bt, na, nb, tb = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
    x, sr = load(D + "/%s.wav" % bt)
    S = sil(x, sr, tb - 0.8, tb + 0.8); s0, s1 = min(S, key=lambda q: abs((q[0] + q[1]) / 2 - tb))
    V = json.load(open(D + "/lines.json", encoding="utf-8"))
    A, B = V[str(na)], V[str(nb)]
    A["t1"] = round(s0 + PAD, 3); B["t0"] = round(s1 - PAD, 3)
    for E, n in ((A, na), (B, nb)):
        E["dur"] = round(E["t1"] - E["t0"], 3); save(x, sr, E["t0"], E["t1"], D + "/line_%03d.wav" % n)
    json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(na, A["t0"], A["t1"], "|", nb, B["t0"], B["t1"], "無音", s0, s1)
