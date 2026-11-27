# 12本目（17本目から写した）：動画レビューの版データを作る（vr_version.py build の結果に、字幕（subs）とメモを足す）
# 使い方：python3 make_version.py BUILT.json OUT.json "メモ" [最後の文の ID]
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
built, out, notes = sys.argv[1], sys.argv[2], sys.argv[3]
last = sys.argv[4] if len(sys.argv) > 4 else None
d = json.load(open(built, encoding="utf-8"))
S = {x["no"]: x for x in json.load(open(os.path.join(HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
END = d.get("duration", 1e9)
subs = []
for p in P:
    if p["start"] >= END: break
    subs.append(dict(id=S[p["no"]]["id"], t0=round(p["start"], 2), t1=round(p["end"], 2), text=S[p["no"]]["text"], who="ナレーション"))
    if last and S[p["no"]]["id"] == last: break      # 12本目 v1：通しは 10-08 で終わる（次の文の頭が動画の長さの中に入っていた）
d["subs"] = subs
d["notes"] = notes
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(out, len(d["subs"]), "字幕", d.get("segment_count"), "区切り", d["subs"][-1]["id"])
