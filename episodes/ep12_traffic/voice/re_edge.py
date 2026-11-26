# 16本目 v1 のコメント（02-06「の情報が」と聞こえる・12-07 の終わりが変な切られ方）：声の頭と終わりを、元の録音から切り直す
#   調べると、289 文のうち 287 文で、頭か終わりの 0.04 秒以内まで声が入っていた（切り出しが -42 dB・0.04 秒のゆとりで、きつすぎた）。
#   いまの line_NNN.wav が元のまとめ（batch_XX.wav）のどこかを、波形の重ね合わせで探し、
#   頭は声が切れずに続く所まで（-50 dB を 0.03 秒下回る所。のばすのは 0.10 秒まで。息を吸う音は、その前の無音で止まるので入らない）、
#   終わりは -55 dB を 0.05 秒下回る所まで（0.35 秒まで）のばす。となりの文の声には入らない。大きさは、いまの声に合わせる。
#   前の声は line_NNN_before_reedge.wav に残す。作り直した声（retake）は元のまとめにないので、頭と終わりが切れていれば知らせるだけ
# MARU_WORK=<作業> python3 re_edge.py [--dry]
import os, sys, json, wave, shutil
import numpy as np
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"; DRY = "--dry" in sys.argv
V = json.load(open(D + "/lines.json", encoding="utf-8"))
def load(p):
    with wave.open(p) as w: sr = w.getframerate(); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, sr
def save(p, x, sr):
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
def db(x, sr, hop=0.01):
    n = int(hop * sr); m = len(x) // n
    return 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9)
B = {}; byb = {}
for k, v in V.items(): byb.setdefault(v["batch"], []).append(int(k))
out = []; warn = []
for k in sorted(V, key=int):
    v = V[k]; n = int(k); p = D + "/line_%03d.wav" % n
    src = p.replace(".wav", "_before_reedge.wav") if os.path.exists(p.replace(".wav", "_before_reedge.wav")) else p
    x, sr = load(src)
    e = db(x, sr, 0.02)
    if max(e[:2]) < -40 and max(e[-2:]) < -40: continue
    if v.get("retake"): warn.append(n); continue
    if v["batch"] not in B: B[v["batch"]] = load(D + "/" + v["batch"] + ".wav")[0]
    b = B[v["batch"]]
    # いまの声が元のまとめのどこか（t0 の前後 1.5 秒で、波形の重なりがいちばん大きい所）
    c0 = int(max(0, v["t0"] - 1.5) * sr); c1 = min(len(b), int((v["t0"] + 1.5) * sr) + len(x))
    seg = b[c0:c1]; L = min(len(x), int(2.0 * sr)); tpl = x[:L]
    best, bi = -1, 0
    for i in range(0, len(seg) - L, int(0.002 * sr)):
        s = seg[i:i + L]; c = float(np.dot(s, tpl)) / (np.linalg.norm(s) * np.linalg.norm(tpl) + 1e-9)
        if c > best: best, bi = c, i
    i0 = c0 + bi
    # ほそかく合わせる（1 サンプル単位で ±2ms）
    bb = -1
    for j in range(i0 - int(0.002 * sr), i0 + int(0.002 * sr)):
        s = b[j:j + L]; c = float(np.dot(s, tpl)) / (np.linalg.norm(s) * np.linalg.norm(tpl) + 1e-9)
        if c > bb: bb, jj = c, j
    i0 = jj; i1 = i0 + len(x)
    if bb < 0.9: warn.append(n); continue
    g = np.sqrt((x ** 2).mean()) / (np.sqrt((b[i0:i1] ** 2).mean()) + 1e-12)
    # となりの文（同じまとめの中）の範囲
    lo, hi = 0, len(b)
    for m in byb[v["batch"]]:
        if m == n: continue
        w_ = V[str(m)]
        if w_["t1"] * sr <= i0 + 10: lo = max(lo, int(((w_["t1"] * sr) + i0) / 2))
        if w_["t0"] * sr >= i1 - 10: hi = min(hi, int(((w_["t0"] * sr) + i1) / 2))
    h = int(0.01 * sr)
    a = i0; lim = max(lo, i0 - int(0.10 * sr)); q = 0
    while a - h > lim:
        if 20 * np.log10(np.sqrt((b[a - h:a] ** 2).mean()) + 1e-9) < -50: q += 1
        else: q = 0
        if q >= 3: a += 2 * h; break
        a -= h
    z = i1; lim2 = min(hi, i1 + int(0.35 * sr)); q = 0
    while z + h < lim2:
        if 20 * np.log10(np.sqrt((b[z:z + h] ** 2).mean()) + 1e-9) < -55: q += 1
        else: q = 0
        if q >= 5: break
        z += h
    y = b[a:z] * g
    pre = np.zeros(int(0.03 * sr), np.float32); post = np.zeros(int(0.03 * sr), np.float32)
    fi = min(int(0.008 * sr), len(y) // 4); fo = min(int(0.03 * sr), len(y) // 4)
    y = y.copy(); y[:fi] *= np.linspace(0, 1, fi) ** 2; y[-fo:] *= np.linspace(1, 0, fo) ** 2
    y = np.concatenate([pre, y, post])
    out.append((n, round((i0 - a) / sr, 3), round((z - i1) / sr, 3), round(bb, 3)))
    if not DRY:
        if not os.path.exists(p.replace(".wav", "_before_reedge.wav")): shutil.copy(p, p.replace(".wav", "_before_reedge.wav"))
        save(p, y, sr); V[k]["dur"] = round(len(y) / sr, 3)
if not DRY: json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("切り直した文", len(out), "／ 頭をのばした平均 %.3f 秒・終わりをのばした平均 %.3f 秒" % (np.mean([o[1] for o in out]), np.mean([o[2] for o in out])) if out else "")
print("合わせ方が弱いか作り直しの声（知らせるだけ）：", warn)
for o in out[:12]: print(o)
