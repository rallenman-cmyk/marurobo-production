# 17本目 まとめ・オチ：家の中のカメラを、条件で探す（cam28.py を広げた）。proj.py の簡単なピンホールで、画面の位置（左上 0,0）を出す
#   need：画面に入れたい点（名前 → (x, y, z)）。lens_pt：まるロボの目（小窓 pip の所に入れない）。maru：まるロボの足もとの点（0.95 m 以上離す）
#   家具の中（小さな金庫・机・ベッド・ソファ・帽子かけ）とかべの外には置かない
import math, itertools, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "proj.py")).read().split("cases=")[0])
BAD = [((0.55, 1.62, 0.0), (1.05, 2.08, 0.55)), ((1.15, 1.75, 0.0), (2.85, 2.4, 0.8)), ((1.25, -2.4, 0.0), (2.9, -0.35, 0.65)),
       ((-2.85, 1.55, 0.0), (-0.95, 2.4, 0.9)), ((-0.05, 1.15, 0.0), (0.3, 1.5, 1.6))]


def inside(c, extra=()):
    if not (-2.85 < c[0] < 2.9 and -2.4 < c[1] < 2.4 and 0.1 < c[2] < 2.2): return True
    return any(all(a[i] - 0.08 < c[i] < b[i] + 0.08 for i in range(3)) for a, b in list(BAD) + list(extra))


def search(need, maru, lens_pt=None, pip=False, list_yb=None, mtop=None, mbot=None, extra=(), lenses=(20, 22, 24, 26, 28, 30), grid=None):
    res = []
    xs, ys, zs = grid or ([-0.6 + 0.3 * i for i in range(12)], [-0.9 + 0.3 * i for i in range(11)], [0.45, 0.6, 0.8, 1.0, 1.25])
    tgts = [need[k] for k in need]
    cx_, cy_, cz_ = [sum(p[i] for p in tgts) / len(tgts) for i in range(3)]
    for cx, cy, cz in itertools.product(xs, ys, zs):
        c = (cx, cy, cz)
        if inside(c, extra) or math.hypot(cx - maru[0], cy - maru[1]) < 0.95: continue
        for dx, dy, dz in itertools.product((-0.3, 0, 0.3), (-0.3, 0, 0.3), (-0.15, 0, 0.15)):
            t = (cx_ + dx, cy_ + dy, cz_ + dz)
            for L in lenses:
                q = {k: proj(c, t, L, p) for k, p in need.items()}
                if any(not (0.04 < x < 0.96 and 0.04 < y < 0.9) for x, y in q.values()): continue
                if lens_pt is not None:
                    lx, ly = proj(c, t, L, lens_pt)
                    if pip and lx < 0.5 and ly < 0.5: continue
                    if list_yb and lx > 0.52 and ly < list_yb: continue
                xs_ = [x for x, y in q.values()]; ys_ = [y for x, y in q.values()]
                spread = (max(xs_) - min(xs_)) * (max(ys_) - min(ys_))
                if mtop and mbot:
                    h = proj(c, t, L, mbot)[1] - proj(c, t, L, mtop)[1]
                    if proj(c, t, L, mtop)[1] < 0.05 or proj(c, t, L, mbot)[1] > 0.95: continue
                    if pip and proj(c, t, L, mtop)[0] < 0.5 and proj(c, t, L, mtop)[1] < 0.5: continue
                else: h = 0
                res.append((round(spread + h, 3), c, tuple(round(v, 2) for v in t), L))
    res.sort(reverse=True)
    return res
