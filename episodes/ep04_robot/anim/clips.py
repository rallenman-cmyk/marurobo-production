# ロボットではありません回：通しの中の 3D の区間（クリップ）の一覧を作る
#   ショット（overlay_layers.py の shots.json）を時刻順に並べ、同じ 3D の場面（base）が続く所を 1 つのクリップにまとめる
#   python3 clips.py <層のフォルダ> [END]  → <層>/clips.json：[{name, base, t0, t1, shots:[{img, t}]}]
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
LY = sys.argv[1]; END = float(sys.argv[2]) if len(sys.argv) > 2 else 642.27
VO = os.path.join(HERE, "..", "voice")
P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
L = {e["no"]: e for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
ID, first, prev = {}, set(), None
for p in P:
    ID.setdefault(L[p["no"]]["id"], p)
    if L[p["no"]]["scene"] != prev: first.add(L[p["no"]]["id"])
    prev = L[p["no"]]["scene"]
FULL = {"s_op"}
sh = json.load(open(os.path.join(LY, "shots.json"), encoding="utf-8"))
for s in sh: s["t"] = round(ID[s["id"]]["start"] - (0.4 if s["id"] in first else 0.15) + s.get("dt", 0.0), 3)
sh.sort(key=lambda s: s["t"]); sh[0]["t"] = 0.0
clips = []
for i, s in enumerate(sh):
    t1 = sh[i + 1]["t"] if i + 1 < len(sh) else END
    base = s["base"] if s["img"][:-4] not in FULL else None
    if base and clips and clips[-1]["base"] == base and abs(clips[-1]["t1"] - s["t"]) < 1e-6:
        clips[-1]["t1"] = t1; clips[-1]["shots"].append(dict(img=s["img"], t=s["t"]))
    elif base:
        clips.append(dict(name="c_" + s["img"][:-4], base=base, scene=None, t0=s["t"], t1=t1, shots=[dict(img=s["img"], t=s["t"])]))
for c in clips:
    for p in P:
        if p["start"] >= c["t0"] - 0.5: c["scene"] = L[p["no"]]["scene"]; break
json.dump(clips, open(os.path.join(LY, "clips.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
tot = sum(c["t1"] - c["t0"] for c in clips)
for c in clips: print(c["name"], c["base"], c["scene"], round(c["t0"], 2), round(c["t1"] - c["t0"], 1), [s["img"][:-4] for s in c["shots"]])
print(len(clips), "クリップ・3D の合計 %.0f 秒" % tot)
