# まるロボが映っている時間を、場面ごとの記録（PLAN_DUMP の *_plan.json の vis）から、区間の一覧にまとめる（3本目 v12）
#   PLAN_DUMP=<dir> blender ... scenes_all.py -- <場面> ... / s07s08_gate.py -- <gate|phone> ...  のあとで
#   python3 make_maru_vis.py <dir>  →  anim/maru_vis.json（[[場面, 始まり, 終わり], ...]）。assemble.py が読み、映っていない時のまるロボの音を外す
import json, glob, os, sys
out = []
for p in sorted(glob.glob(os.path.join(sys.argv[1], "*_plan.json"))):
    d = json.load(open(p)); k = os.path.basename(p)[:-10]; cur = None
    for t, v in d.get("vis", []):
        if v and cur is None: cur = t
        if not v and cur is not None: out.append([k, round(cur, 3), round(t, 3)]); cur = None
    if cur is not None: out.append([k, round(cur, 3), round(d["t1"], 3)])
# 3D の点で数えられない「映っている」所（手で足す。理由を書く）
EXTRA = [["s05", 100.0, 113.1]]   # 鏡の場面：まるロボは画面の下の端に背中だけ、鏡の中に映った姿が大きく出ている（v11 105〜112 のコマで確かめた）
out += EXTRA
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "maru_vis.json"), "w"), ensure_ascii=False)
print("まるロボが映っている区間：%d" % len(out))
