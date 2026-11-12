# まとめて読ませた声（batch_XX.wav、5文ずつ）を、1文ずつ（line_NNN.wav）に分ける
#   文と文の間の「無音」を候補にし、①長い無音ほど ②分けた長さが文の字数に比例するほど よい分け方を、全部の組み合わせから選ぶ
#   前後の無音は 40ms だけ残して切る。結果は lines.json（番号・長さ・どのまとめのどこか）
# 使い方: python3 split_narration.py
import os, json, wave, math, itertools
import numpy as np
SC = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; D = SC + "/stage/voice/achernar"
FR = 0.010; THR_DB = -42.0; MIN_SIL = 0.12; PAD = 0.04


def load(p):
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    return x, sr


def silences(x, sr):
    n = int(FR * sr); m = len(x) // n
    db = 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9)
    quiet = db < THR_DB; runs = []; i = 0
    while i < m:
        if quiet[i]:
            j = i
            while j < m and quiet[j]: j += 1
            runs.append((i * FR, j * FR)); i = j
        else: i += 1
    return runs, db


def split(x, sr, texts):
    runs, db = silences(x, sr)
    total = len(x) / sr
    s0 = runs[0][1] if runs and runs[0][0] <= 0.0 + 1e-6 else 0.0                  # 頭の無音の終わり
    s1 = runs[-1][0] if runs and runs[-1][1] >= total - FR * 1.5 else total        # 終わりの無音の始め
    inner = [r for r in runs if r[0] > s0 + 0.05 and r[1] < s1 - 0.05 and r[1] - r[0] >= MIN_SIL]
    N = len(texts)
    if N == 1: return [(s0, s1)]
    chars = np.array([max(len(t.replace("、", "").replace("。", "").replace("？", "")), 1) for t in texts], float)
    best = None
    for combo in itertools.combinations(range(len(inner)), N - 1):
        cuts = [inner[k] for k in combo]
        segs = []; a = s0
        for (c0, c1) in cuts: segs.append((a, c0)); a = c1
        segs.append((a, s1))
        durs = np.array([b - a for a, b in segs])
        if (durs <= 0.2).any(): continue
        exp = chars / chars.sum() * durs.sum()
        fit = float(((np.log(durs / exp)) ** 2).sum())
        pause = float(sum(math.log(c1 - c0) for c0, c1 in cuts))
        score = pause - 6.0 * fit
        if best is None or score > best[0]: best = (score, segs, fit)
    if best is None: return None
    return best[1]


if __name__ == "__main__":
    out = {}
    for fn in sorted(f for f in os.listdir(D) if f.startswith("batch_") and f.endswith(".json")):
        meta = json.load(open(os.path.join(D, fn), encoding="utf-8")); wp = os.path.join(D, fn.replace(".json", ".wav"))
        if not os.path.exists(wp): continue
        x, sr = load(wp); segs = split(x, sr, meta["tts"])
        if segs is None: print("SPLIT FAILED", fn); continue
        for no, txt, (a, b) in zip(meta["nos"], meta["texts"], segs):
            a2, b2 = max(0, a - PAD), min(len(x) / sr, b + PAD)
            y = (x[int(a2 * sr):int(b2 * sr)] * 32767).astype(np.int16)
            with wave.open(os.path.join(D, "line_%03d.wav" % no), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())
            out[no] = dict(no=no, text=txt, dur=round(b2 - a2, 3), batch=fn[:-5], t0=round(a2, 3), t1=round(b2, 3))
    json.dump(out, open(os.path.join(D, "lines.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("lines", len(out))
