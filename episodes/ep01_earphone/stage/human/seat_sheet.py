# 座った姿勢の4面図（正面・左・後ろ・左45°）から、座った体の形を起こす（輪郭の重なり＝視体積）。ベンチの中には入らない
# 座標：x＝人物の左、y＝後ろ（座面の前の縁が0）、z＝上（床が0）。単位メートル
# 使い方: python3 seat_sheet.py M1   → sheets/seatmesh_M1.npz と確認画像
import sys, os, json, math, time
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sdf
from hair_sheet import _erode, _dilate, _box3
SH = os.path.join(HERE, "..", "..", "sheets")
VIEWS = ["front", "left", "back", "left45"]
ANG = {"front": 0.0, "left45": 45.0, "left": 90.0, "back": 180.0}
BENCH = dict(hw=0.37, depth=0.586, seat=0.45, back_y=0.48, back_top=0.85)


def load(k):
    im = np.asarray(Image.open(os.path.join(SH, f"seat_{k}.png")).convert("RGB")).astype(float) / 255
    H, W, _ = im.shape; bg = np.median(im[5:20, 1000:1200].reshape(-1, 3), 0)
    diff = np.abs(im - bg).max(2); occ = (diff[30:660] > 0.06).mean(0); cols = occ > 0.03
    segs = []; x = 0
    while x < W:
        if cols[x]:
            x0 = x
            while x < W and cols[x]: x += 1
            if x - x0 > 40: segs.append((x0, x))
        x += 1
    return im, bg, segs


def masks(k):
    im, bg, segs = load(k)
    H, W, _ = im.shape
    sat = im.max(2) - im.min(2); lum = im.mean(2); diff = np.abs(im - bg).max(2)
    bench = (sat < 0.05) & (lum > 0.45) & (lum < 0.905) & (diff > 0.025)
    # 細い横線（目安線）を除く：縦方向に縮めてから戻す
    b2 = bench.copy()
    for _ in range(3): b2 = b2 & np.roll(b2, 1, 0) & np.roll(b2, -1, 0)
    for _ in range(3): b2 = b2 | np.roll(b2, 1, 0) | np.roll(b2, -1, 0)
    bench = b2 & bench
    frac = bench[:, 150:2100].mean(1)
    floor = max(i for i in range(H) if frac[i] > 0.25)               # ベンチの下の縁＝床
    person = (diff > 0.07) & ~bench
    person[floor + 1:] = False
    out = {}
    for view, (x0, x1) in zip(VIEWS, segs):
        x0 = max(0, x0 - 20); x1 = min(W, x1 + 20)
        p = person[:, x0:x1].copy(); b = bench[:, x0:x1].copy()
        pm = Image.fromarray((p * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))
        p = np.asarray(pm) > 128
        out[view] = dict(x0=x0, x1=x1, person=p, bench=b, rgb=im[:, x0:x1])
    return out, floor


def register(k, M, floor):
    """縮尺 S（px/m）と、各ビューの横の基準位置 u0。ベンチの位置から決める"""
    # 縦：座面の高さ（ベンチの上の縁）と背もたれの上の縁から
    fb = M["front"]["bench"]; rows = np.nonzero(fb[:, fb.shape[1] // 2 - 120:fb.shape[1] // 2 + 120].mean(1) > 0.25)[0]
    lb = M["left"]["bench"]
    # 左のビュー：ベンチの列（床の少し上の行）で前の縁、背もたれの後ろの縁
    rowL = floor - 12; colsL = np.nonzero(lb[rowL])[0]; u_front_edge = colsL.min(); u_back_edge = colsL.max()
    # 背もたれの上の縁：左のビューで、後ろの縁の少し内側の列の、いちばん上のベンチ画素
    cb = int(u_back_edge - 10); top_back = np.nonzero(lb[:, cb])[0].min()
    # 座面の上の縁：前の縁の少し内側（座面）の列で、いちばん上のベンチ画素（脚の陰になる所は避ける）
    seat_cols = np.arange(int(u_front_edge + 25), int(u_front_edge + 60))
    tops = [np.nonzero(lb[:, c])[0].min() for c in seat_cols if lb[:, c].any()]
    seat_top = float(np.median(tops))
    S1 = (floor - seat_top) / BENCH["seat"]; S2 = (floor - top_back) / BENCH["back_top"]
    S = (S1 + S2) / 2 if abs(S1 / S2 - 1) < 0.08 else S2
    depth = (u_back_edge - u_front_edge) / S
    # 正面・後ろ：ベンチの左右の端の中点が x=0
    def center(view):
        b = M[view]["bench"]; r = floor - 12; c = np.nonzero(b[r])[0]; return (c.min() + c.max()) / 2.0, (c.max() - c.min()) / S
    uF, wF = center("front"); uB, wB = center("back")
    hw = (wF + wB) / 4.0
    # 左45°：ベンチのいちばん左の点は (x=−hw, y=0) → u = u0 + S·(−hw·cos45)
    b45 = M["left45"]["bench"]; c45 = np.nonzero(b45[floor - 12])[0]
    u45 = c45.min() + S * hw * math.cos(math.radians(45))
    reg = dict(S=S, S_seat=S1, S_back=S2, floor=float(floor), u=dict(front=uF, back=uB, left=float(u_front_edge), left45=float(u45)),
               bench=dict(hw=hw, depth=depth, seat_top_px=seat_top, back_top_px=float(top_back)))
    return reg


def proj(P, view, reg):
    a = math.radians(reg.get("ang", {}).get(view, ANG[view])); S = reg["S"] * reg.get("sc", {}).get(view, 1.0)
    fl = reg["floor"] + reg.get("dv", {}).get(view, 0.0)
    return np.stack([reg["u"][view] + S * (P[:, 0] * math.cos(a) + P[:, 1] * math.sin(a)), fl - S * P[:, 2]], 1)


def hull(k, M, reg, h=0.006, open_r=1, views=None, occ_only=False):
    views = views or VIEWS
    lo = np.array([-0.45, -0.70, 0.0]); hi = np.array([0.45, 0.70, 1.55])
    n = np.floor((hi - lo) / h).astype(int) + 1
    xs, ys, zs = (lo[i] + h * np.arange(n[i]) for i in range(3))
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.stack([X.ravel(), Y.ravel()], 1)
    occ = np.ones(tuple(n), bool)
    pm = {}
    for view in views:
        p = M[view]["person"].copy()
        if view == "back": p |= M[view]["bench"]          # 後ろからは、ベンチの陰の体が見えない（削らない）
        pm[view] = np.asarray(Image.fromarray((p * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 128
    B = reg["bench"]
    for kz, z in enumerate(zs):
        P = np.concatenate([XY, np.full((len(XY), 1), z)], 1); ok = np.ones(len(P), bool)
        for view in views:
            uv = proj(P, view, reg); m = pm[view]; Hh, Ww = m.shape
            u = np.round(uv[:, 0]).astype(int); v = np.round(uv[:, 1]).astype(int)
            inside = (u >= 0) & (u < Ww) & (v >= 0) & (v < Hh)
            ok &= inside & m[np.clip(v, 0, Hh - 1), np.clip(u, 0, Ww - 1)]
        # ベンチの中には入らない（座面と背もたれ）
        inb = (np.abs(P[:, 0]) < B["hw"]) & (P[:, 1] > 0.0) & (P[:, 1] < B["depth"]) & (P[:, 2] < BENCH["seat"])
        inb |= (np.abs(P[:, 0]) < B["hw"]) & (P[:, 1] > B["depth"] - 0.10) & (P[:, 1] < B["depth"]) & (P[:, 2] < BENCH["back_top"])
        occ[:, :, kz] = (ok & ~inb).reshape(n[0], n[1])
    occ[0] = occ[-1] = False; occ[:, 0] = occ[:, -1] = False; occ[:, :, 0] = occ[:, :, -1] = False
    for _ in range(open_r): occ = _erode(occ)
    for _ in range(open_r): occ = _dilate(occ)
    idx = np.argwhere(occ)
    seed = np.zeros_like(occ); top = idx[np.argmax(idx[:, 2])]; seed[tuple(top)] = True; cnt = 1
    while True:
        nx = _dilate(seed) & occ; c2 = int(nx.sum())
        if c2 == cnt: break
        seed, cnt = nx, c2
    occ = seed
    if occ_only: return occ, lo, h
    s_ = _box3(_box3(occ.astype(np.float32))); G = (0.5 - s_) * 3.0 * h
    def F(p):
        q = (p - lo) / h; i0 = np.clip(np.floor(q).astype(int), 0, n - 2); t = np.clip(q - i0, 0, 1); out = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                    out = out + w * G[i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz]
        return out
    V, Q = sdf.mesh(F, lo + 2 * h, hi - 2 * h, h, relax_iters=2)
    return V, Q


def fit_view(view, M, reg, occ, lo, h, a_range, sc_range=(0.88, 1.12)):
    """3方向から作った形を、このビューの輪郭に一番よく重なる角度・縮尺・位置で合わせる"""
    idx = np.argwhere(occ); P = lo + idx * h
    rng = np.random.default_rng(0); P = P[rng.choice(len(P), min(len(P), 60000), replace=False)]
    m = M[view]["person"]; Hh, Ww = m.shape; d = 2; md = m[::d, ::d]
    best = (0, None)
    def iou(a, sc, u0, dv):
        r = dict(reg, ang={view: a}, sc={view: sc}, dv={view: dv}, u=dict(reg["u"], **{view: u0}))
        uv = proj(P, view, r) / d; u = np.round(uv[:, 0]).astype(int); v = np.round(uv[:, 1]).astype(int)
        ok = (u >= 0) & (u < md.shape[1]) & (v >= 0) & (v < md.shape[0]); sil = np.zeros_like(md)
        sil[v[ok], u[ok]] = True; sil = sil | np.roll(sil, 1, 0) | np.roll(sil, 1, 1)
        return (sil & md).sum() / max((sil | md).sum(), 1)
    cols = np.nonzero(m.any(0))[0]; mcx = (cols.min() + cols.max()) / 2
    for a in np.arange(a_range[0], a_range[1] + 0.1, 2.5):
        for sc in np.arange(sc_range[0], sc_range[1] + 1e-6, 0.02):
            r = dict(reg, ang={view: a}, sc={view: sc}, u=dict(reg["u"], **{view: 0.0}))
            uv = proj(P, view, r); u0 = mcx - (uv[:, 0].min() + uv[:, 0].max()) / 2
            for du in range(-16, 17, 4):
                for dv in (-6, -3, 0, 3, 6):
                    v_ = iou(a, sc, u0 + du, dv)
                    if v_ > best[0]: best = (v_, (a, sc, u0 + du, dv))
    a, sc, u0, dv = best[1]
    for _ in range(2):
        for a2 in np.arange(a - 2, a + 2.01, 0.5):
            for sc2 in np.arange(sc - 0.02, sc + 0.021, 0.005):
                for du in range(-4, 5, 1):
                    for dv2 in range(-3, 4, 1):
                        v_ = iou(a2, sc2, u0 + du, dv + dv2)
                        if v_ > best[0]: best = (v_, (a2, sc2, u0 + du, dv + dv2))
        a, sc, u0, dv = best[1]
    return best


if __name__ == "__main__":
    k = sys.argv[1]; t0 = time.time()
    M, floor = masks(k)
    reg = register(k, M, floor)
    print(k, "S", round(reg["S"], 1), "(seat", round(reg["S_seat"], 1), "back", round(reg["S_back"], 1), ") floor", floor, "u", {a: round(b, 1) for a, b in reg["u"].items()},
          "bench hw", round(reg["bench"]["hw"], 3), "depth", round(reg["bench"]["depth"], 3), flush=True)
    for view in VIEWS:
        m = M[view]
        Image.fromarray((m["rgb"] * 255).astype(np.uint8)).save(os.path.join(SH, f"seat{k}_{view}.png"))
        Image.fromarray((m["person"] * 255).astype(np.uint8)).save(os.path.join(SH, f"seat{k}_{view}_person.png"))
    occ3, lo3, h3 = hull(k, M, reg, h=0.008, views=["front", "left", "back"], occ_only=True)
    iou, (a, sc, u0, dv) = fit_view("left45", M, reg, occ3, lo3, h3, (25.0, 70.0))
    reg.setdefault("ang", {})["left45"] = a; reg.setdefault("sc", {})["left45"] = sc; reg.setdefault("dv", {})["left45"] = dv; reg["u"]["left45"] = u0
    print(k, "left45 fit: angle", round(a, 1), "scale", round(sc, 3), "u0", round(u0, 1), "dv", dv, "IoU", round(iou, 3), flush=True)
    json.dump(reg, open(os.path.join(SH, f"seatreg_{k}.json"), "w"), indent=1)
    V, Q = hull(k, M, reg)
    np.savez(os.path.join(SH, f"seatmesh_{k}.npz"), V=V, Q=Q)
    print(k, "body mesh", len(V), len(Q), "bbox", np.round(V.min(0), 3), np.round(V.max(0), 3), round(time.time() - t0, 1), "s")
