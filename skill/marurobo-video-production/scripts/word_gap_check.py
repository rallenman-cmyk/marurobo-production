# 声の「言葉の途中の長い間」を探す（16本目 6章 v17「ほ、とんどのドア」っていってる：「ほ」のあとに 0.5 秒の間があった）
#   文ごとに、句読点（、。？！……）に当てはまらない無音で、min_gap 秒以上の物を出す（書き起こしでは「ほとんど」と正しく出て気づけない）
#   使い方：python3 word_gap_check.py <placement.json> <声のフォルダ> [始めの秒] [終わりの秒] [min_gap=0.2]
import sys, os, json
import subs_pause_align as PA
P = json.load(open(sys.argv[1], encoding="utf-8")); VD = sys.argv[2]
a = float(sys.argv[3]) if len(sys.argv) > 3 else -1; b = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
mg = float(sys.argv[5]) if len(sys.argv) > 5 else 0.2
bad = 0
for p in P:
    if not (a <= p["start"] < b): continue
    w = os.path.join(VD, "line_%03d.wav" % p["no"])
    if not os.path.exists(w): continue
    S, dur = PA.silences(w, p.get("speed", 1.0))
    used = {round(r[1] - p["start"], 2) for r in PA.align(p["text"], p["start"], w, p.get("speed", 1.0)) if r[1] is not None}
    for s0, s1 in S:
        if s1 - s0 >= mg and round(s1, 2) not in used:
            bad += 1; print("%d %.2f秒  文の頭から %.2f〜%.2f（%.2f 秒）  %s" % (p["no"], p["start"], s0, s1, s1 - s0, p["text"]))
print("言葉の途中の長い間：%d か所" % bad)
