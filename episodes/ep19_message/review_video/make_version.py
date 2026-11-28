# 19本目（17本目から写した）：動画レビューの版データを作る（vr_version.py build の結果に、字幕（subs）とメモを足す）
# 使い方：python3 make_version.py BUILT.json OUT.json "メモ"
#   BUILT.json：skill/.../scripts/vr_version.py build が作ったもの
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
built, out, notes = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(built, encoding="utf-8"))
S = {x["no"]: x for x in json.load(open(os.path.join(HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
END = d.get("duration", 1e9)   # 16本目：章ごとに見せるので、動画の長さの中の文だけ
d["subs"] = [dict(id=S[p["no"]]["id"], t0=round(p["start"], 2), t1=round(p["end"], 2), text=S[p["no"]]["text"], who="ナレーション") for p in P if p["start"] < END]
d["notes"] = notes
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(out, len(d["subs"]), "字幕", d.get("segment_count"), "区切り")
