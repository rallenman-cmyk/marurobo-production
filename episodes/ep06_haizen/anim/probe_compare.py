# 同じ組み立ての、となり合う 2 場面で、同じ時刻の物の場所・向きが同じかを比べる（6本目 v8 9:52 の原因：
#   「最初のキーを場面の頭の 1 秒前に打つ」書き方で、後ろの場面だけ物が戻されていた）。
#   使い方：blender ... scenes.py -- <場面> <出力> --probe a b を 2 場面ぶん → python3 probe_compare.py <出力の親>
#   ずれ 2cm・3° をこえる物を、場面の組ごとに出す。まるロボの体の細かい部品は名前でまとめる
import os, sys, json, glob, math
root = sys.argv[1]; bad = 0
for d in sorted(glob.glob(os.path.join(root, "S*_S*"))):
    a, c = os.path.basename(d).split("_")
    pa, pc = os.path.join(d, a + "_probe.json"), os.path.join(d, c + "_probe.json")
    if not (os.path.exists(pa) and os.path.exists(pc)): print(os.path.basename(d), "書き出しなし"); bad += 1; continue
    A, C = json.load(open(pa)), json.load(open(pc)); hits = {}
    for t in A:
        if t not in C: continue
        for nm, va in A[t].items():
            vc = C[t].get(nm)
            if vc is None: continue
            dp = math.dist(va[:3], vc[:3]); dr = max(abs((x - y + math.pi) % (2 * math.pi) - math.pi) for x, y in zip(va[3:], vc[3:]))
            if dp > 0.02 or dr > math.radians(3):
                key = nm.split(".")[0]
                h = hits.setdefault(key, [t, t, 0.0]); h[1] = t; h[2] = max(h[2], dp)
    if hits:
        bad += 1
        print(os.path.basename(d), "：", "、".join("%s %s〜%s秒 最大 %.2fm" % (k, v[0], v[1], v[2]) for k, v in sorted(hits.items(), key=lambda x: -x[1][2])[:8]))
print("ずれのある組：", bad)
