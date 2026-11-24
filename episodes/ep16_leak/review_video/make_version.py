# 16本目（9本目から写した）：動画レビューの版データを作る（vr_version.py build の結果に、字幕（subs）とメモを足す）
# 使い方：python3 make_version.py BUILT.json OUT.json "メモ" [章の頭の秒（本編の秒。2章は 389.9）]
#   章の頭の秒を渡すと、文の時刻からその秒を引き、その章の中の文だけを入れる（16本目 2章の動画は本編の 6:29.9 から始まる）
#   BUILT.json：skill/.../scripts/vr_version.py build が作ったもの
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
built, out, notes = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(built, encoding="utf-8"))
S = {x["no"]: x for x in json.load(open(os.path.join(HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
END = d.get("duration", 1e9)   # 16本目：章ごとに見せるので、動画の長さの中の文だけ
F = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
d["subs"] = [dict(id=S[p["no"]]["id"], t0=round(p["start"] - F, 2), t1=round(p["end"] - F, 2), text=S[p["no"]]["text"], who="ナレーション") for p in P if F <= p["start"] < F + END]
d["notes"] = notes
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(out, len(d["subs"]), "字幕", d.get("segment_count"), "区切り")
