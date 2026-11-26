# 9本目 v4 のコメント 5:10「今ここの赤い丸は映像で映してる場所にして」：「いまここ」の地図の赤い点を、手で決めた割合ではなく、
#   その時に映している場所（カメラのまん中の先に当たる所。まるロボを追うカメラ・断面の図はまるロボの位置）から決める
#   python3 locator_keys.py <測った記録（pen_dbg5 の DBG 行）> → locator_keys.json（[時刻, 道の上の割合 u]）
#   世界の (x, z) を地図に写し（坂の始め・終わりと床の高さで合わせる）、床の下の道（overlays.LOC_PATH）のいちばん近い所を u にする
import sys, re, json, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import esc_geom as G
LOC_PATH = [(292, 12), (318, 14), (330, 28), (316, 42), (282, 42), (104, 140), (72, 140), (60, 126), (70, 112), (96, 112)]
X0 = G.COMB_LO_X + G.FLAT_LO; X1 = G.COMB_HI_X - G.FLAT_HI           # 坂の始め・終わり（世界）→ 地図の 90・270
def to_map(x, z): return (90 + (x - X0) * 180 / (X1 - X0), 100 - z * 100 / G.H)
acc = [0.0]
for (a, b), (c, d) in zip(LOC_PATH, LOC_PATH[1:]): acc.append(acc[-1] + math.hypot(c - a, d - b))
def proj(p):
    best = None
    for i in range(len(LOC_PATH) - 1):
        (a, b), (c, d) = LOC_PATH[i], LOC_PATH[i + 1]; L = math.hypot(c - a, d - b)
        f = max(0.0, min(1.0, ((p[0] - a) * (c - a) + (p[1] - b) * (d - b)) / (L * L)))
        q = (a + (c - a) * f, b + (d - b) * f); dd = math.hypot(p[0] - q[0], p[1] - q[1])
        if best is None or dd < best[0]: best = (dd, (acc[i] + L * f) / acc[-1])
    return best[1]
FOLLOW = {"B11b", "B12e", "B12e2", "B12f", "D12"}                        # まるロボを追う・まるロボを見せる場面は、まるロボの位置
rows = []
for l in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"(\S+) DBG ([\d.]+) maru \[([^\]]+)\] cam \[[^\]]+\] look (\[[^\]]+\]|None) ?(.*)", l.strip())
    if not m: continue
    clip, t = m.group(1), float(m.group(2)); mx, my, mz = [float(v) for v in m.group(3).split(",")]
    look = None if m.group(4) == "None" else [float(v) for v in m.group(4)[1:-1].split(",")]
    hitname = m.group(5)
    if clip in FOLLOW or look is None or hitname.startswith("Maru"): x, z = mx, mz
    else: x, z = look[0], look[2]
    rows.append((t, clip, round(proj(to_map(x, z)), 3)))
rows.sort()
# 同じクリップの中は、まん中の値（ゆれ止め）で、クリップが変わる所でだけ点を動かす（映像が切りかわる所で地図も切りかわる）
CL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips.json")))
out = []; i = 0
while i < len(rows):
    j = i
    while j < len(rows) and rows[j][1] == rows[i][1]: j += 1
    us = [r[2] for r in rows[i:j]]
    cut = CL[rows[i][1]][2]; nxt = CL[rows[j][1]][2] if j < len(rows) else rows[j - 1][0] + 0.5
    if rows[i][1] in FOLLOW:                                         # まるロボについて動く場面は、点もいっしょに動く
        out.append([cut, rows[i][2]])
        for r in rows[i:j]: out.append([r[0], r[2]])
        out.append([nxt - 0.01, rows[j - 1][2]])
    else:                                                            # 場面の切りかわりの時刻で、点も切りかわる（すべらせない）
        u = sorted(us)[len(us) // 2]; out.append([cut, u]); out.append([nxt - 0.01, u])
    i = j
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "locator_keys.json"), "w"), indent=0)
for t, u in out: print("%7.2f %.3f" % (t, u))
