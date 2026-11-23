# 16本目 v1 のコメント「間のばらつきが大きい・たまに食い気味」：1 つの声の中で文が変わる所（。？！のあと）の無音を、0.5 秒にそろえる
#   区切りの場所は pauses.cut_all（読みの長さの割合 → いちばん近い無音）。0.5 秒より短ければ、無音のまん中に足す（長いのはそのまま）。
#   前の声は line_NNN_before_pause.wav に残す（2 回目からは元に戻してからやり直す）。lines.json の dur も直す
# MARU_WORK=<作業> python3 inner_pause.py [--dry]
import os, sys, json, wave, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pauses as PZ
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"; DRY = "--dry" in sys.argv; GOAL = 0.5
V = json.load(open(D + "/lines.json", encoding="utf-8"))
S = {l["no"]: l for l in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "script_v1_0.json"), encoding="utf-8"))}
done = []; nofind = []
for n in sorted(S):
    p = D + "/line_%03d.wav" % n; bk = p.replace(".wav", "_before_pause.wav")
    src = bk if os.path.exists(bk) else p
    cuts = [c for c in PZ.cut_all(src, S[n]["tts"]) if c[1] in "。？！"]
    if not cuts: continue
    with wave.open(src) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).copy()
    add = []
    for pos, ch, r in cuts:
        if r is None: nofind.append((n, S[n]["text"][:pos][-8:])); continue
        s, e = r
        if e - s < GOAL: add.append(((s + e) / 2, GOAL - (e - s), round(e - s, 2)))
    if not add: continue
    out = []; last = 0
    for t, d, _ in sorted(add):
        i = int(t * sr); out += [x[last:i], np.zeros(int(d * sr), np.int16)]; last = i
    out.append(x[last:]); y = np.concatenate(out)
    done.append((n, [a[2] for a in add]))
    if not DRY:
        if not os.path.exists(bk): shutil.copy(p, bk)
        with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())
        V[str(n)]["dur"] = round(len(y) / sr, 3)
if not DRY: json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("文の切れ目をのばした声", len(done), "文")
for d in done: print("  ", d[0], S[d[0]]["id"], "前の無音", d[1])
print("切れ目が見つからない文の終わり", nofind)
