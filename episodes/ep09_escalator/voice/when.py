# 時刻（秒）から、その時に読んでいる文を出す：python3 when.py 111.3 706.1 …
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(H, "placement.json"), encoding="utf-8"))
ids = [l["id"] for l in json.load(open(os.path.join(H, "lines.json"), encoding="utf-8"))] if False else None
for a in sys.argv[1:]:
    t = float(a); best = None
    for i, x in enumerate(P):
        if x["start"] - 0.8 <= t <= x["end"] + 0.8: best = (i, x); break
        if x["start"] > t: best = (i - 1, P[i - 1]); break
    i, x = best
    print("%7.1f  #%d [%.1f-%.1f] %s ／次 [%.1f] %s" % (t, x["no"], x["start"], x["end"], x["text"][:30], P[i + 1]["start"] if i + 1 < len(P) else -1, P[i + 1]["text"][:20] if i + 1 < len(P) else ""))
