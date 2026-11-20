# 字幕の切り替わりと声のずれを、声の波形で数える（3本目 v12。v11 の「テロップの切り替わりが早い／遅い」約 30 件の振り返り）
#   ①文の頭の 1 枚：その文の声の頭との差 ②文の中の切り替わり：いちばん近い声の間（0.15 秒以上の無音）の終わり（＝次の言葉の頭）との差
#   ③v10（直してきた版）の同じ字の 1 枚との差。どれも 0.35 秒をこえる所を全部出す（短い「……」の 1 枚を 2 秒にした所は、理由つきで残す）
#   MARU_VOICE=<1 文ずつの声のフォルダ> python3 sub_sync_check.py [比べる版の字幕.json]
import json, os, re, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, "..", "voice")
L = json.load(open(os.path.join(HERE, "subs_events.json"), encoding="utf-8"))
P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
REF = {t: a for a, b, t in json.load(open(sys.argv[1], encoding="utf-8"))} if len(sys.argv) > 1 else {}
VD = os.environ["MARU_VOICE"]
def gaps(p):
    with wave.open(os.path.join(VD, "line_%03d.wav" % p["no"])) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
    h = sr // 100; n = len(x) // h; db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9); on = db > db.max() - 38
    out, i = [], 0
    while i < n:
        if not on[i]:
            j = i
            while j < n and not on[j]: j += 1
            if j - i >= 15 and i > 0 and j < n: out.append(p["start"] + j / 100)
            i = j
        else: i += 1
    return out
G = {p["no"]: gaps(p) for p in P}
bad = []
for k, (a, b, t) in enumerate(L):
    p = min(P, key=lambda q: 0 if q["start"] - 0.8 <= a <= q["end"] else min(abs(a - q["start"]), abs(a - q["end"])))
    if abs(a - p["start"]) < 0.8: d, why = a - p["start"], "文の頭"
    else:
        c = G[p["no"]]
        if not c: continue
        g = min(c, key=lambda v: abs(v - a)); d, why = a - g, "声の間の終わり"
    dr = (a - REF[t]) if t in REF else 0.0
    if abs(d) > 0.35 or abs(dr) > 0.35: bad.append((round(a, 2), round(d, 2), why, round(dr, 2), t.replace("\\N", " ")[:26]))
print("字幕 %d 枚。0.35 秒をこえてずれる 1 枚：%d" % (len(L), len(bad)))
for x in bad: print("  %7.2f  %+.2f（%s）  前の版から %+.2f  %s" % x)
