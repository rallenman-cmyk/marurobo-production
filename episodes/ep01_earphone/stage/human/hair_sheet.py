# 6面図から髪の立体を起こす：各ビューの「髪か肌」の輪郭すべてに収まり（視体積）、頭の外側にあり、
# どのビューでも「その向きから見えるはずの肌」を隠さない所＝髪
import os, sys, math, json
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sdf, loft_specs
SH = os.path.join(HERE, "..", "..", "sheets")
ANG = {"front": 0.0, "left45": 45.0, "left": 90.0, "back": 180.0, "right": 270.0}


def edt1d(f):
    """1次元の2乗距離変換（Felzenszwalb）"""
    n = len(f); d = np.zeros(n); v = np.zeros(n, int); zz = np.zeros(n + 1); k = 0; v[0] = 0; zz[0] = -1e20; zz[1] = 1e20
    for q in range(1, n):
        s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
        while s <= zz[k]:
            k -= 1; s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
        k += 1; v[k] = q; zz[k] = s; zz[k + 1] = 1e20
    k = 0
    for q in range(n):
        while zz[k + 1] < q: k += 1
        d[q] = (q - v[k]) ** 2 + f[v[k]]
    return d


def edt(mask):
    """mask の外の点から mask までの距離（ピクセル）"""
    INF = 1e10; f = np.where(mask, 0.0, INF)
    g = np.array([edt1d(col) for col in f.T]).T
    return np.sqrt(np.array([edt1d(row) for row in g]))


def sdf2d(mask):
    return edt(mask) - edt(~mask)                       # 外が＋、内が−（ピクセル）


def view_masks(k, view):
    im = np.asarray(Image.open(os.path.join(SH, f"{k}_{view}.png")).convert("RGB")).astype(float) / 255
    fg = np.asarray(Image.open(os.path.join(SH, f"{k}_{view}_fg.png")).convert("L")) > 128
    skin = np.asarray(Image.open(os.path.join(SH, f"{k}_{view}_skin.png")).convert("L")) > 128
    r, g, b = im[..., 0], im[..., 1], im[..., 2]; lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    # 目安線（灰色の破線）を人物から除く：線の行の、灰色で明るめの画素
    sat = im.max(2) - im.min(2)
    lay = json.load(open(os.path.join(SH, "layout.json")))[k]
    fg = fg.copy()
    for gv in lay["guides"]:
        for v in range(max(0, gv - 3), min(fg.shape[0], gv + 4)):
            fg[v] &= ~((sat[v] < 0.08) & (lum[v] > 0.40))
    fg = np.asarray(Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(3))) > 128
    skin = skin | ((g - b > 0.09) & (r - b > 0.22) & (lum > 0.30))      # 影になった肌（首の後ろなど）も。茶色の髪は g−b が小さいので入らない
    white = (lum > 0.75) & fg & ~skin                    # イヤホン
    # 目・眉・口の穴を埋める：縦の列ごとに、肌と肌のあいだの短いすき間（30px以下）を肌にする（後ろ・真上はしない）
    skin = skin | white
    gap = {"back": 0, "top": 0}.get(view, 30)
    if gap:      # 目・眉・口のすき間だけ埋める：顔の範囲（耳より前、眉の上〜口の下）に限る（耳の後ろの髪を肌にしない）
        sp_ = json.load(open(os.path.join(SH, f"spec_{k}.json"))); S_, v0_ = sp_["reg"]["S"], sp_["reg"]["v0"]
        u0_ = json.load(open(os.path.join(SH, f"reg_{k}.json"))).get(view) if os.path.exists(os.path.join(SH, f"reg_{k}.json")) else None
        ey = sp_["ear"]["center"][1]; ex = sp_["ear"]["out_x"]
        H_, W_ = skin.shape; uu = np.arange(W_)
        if u0_ is None: allow = np.ones(W_, bool)
        elif view == "front": allow = np.abs(uu - u0_) < 0.072 * S_
        elif view == "left": allow = uu < u0_ + S_ * (ey - 0.030)
        elif view == "right": allow = uu > u0_ - S_ * (ey - 0.030)
        else: allow = uu < u0_ + S_ * ((ex * 0.7071 + ey * 0.7071) - 0.030)
        vlo, vhi = int(v0_ - 0.075 * S_), int(v0_ + 0.085 * S_)
        sk = skin.copy()
        for x in np.nonzero(allow)[0]:
            col = skin[vlo:vhi, x]; ys = np.nonzero(col)[0]
            if len(ys) < 2: continue
            d = np.diff(ys); idx = np.nonzero((d > 1) & (d <= gap))[0]
            for i in idx: sk[vlo + ys[i]:vlo + ys[i + 1], x] = True
        skin = sk
    return fg, skin


def build(k, cut_z=None):
    P, reg = loft_specs.get(k)
    S, v0 = reg["S"], reg["v0"]
    VV = {}
    cut_z = cut_z if cut_z is not None else loft_specs.MANUAL[k].get("hair_cut_z", -0.115)
    for view in ("front", "left45", "left", "back", "right"):      # 真上の図は位置合わせが不確かなので使わない
        fg, skin = view_masks(k, view)
        if view != "top":
            vcut = int(round(v0 - cut_z * S)); fg = fg.copy(); fg[vcut:, :] = False      # 肩・服は髪の候補から外す
        VV[view] = dict(hull=sdf2d(fg) / S, skin=sdf2d(skin) / S, shape=fg.shape)
    return P, reg, VV


def sample(F, uv):
    H, W = F.shape; u = np.clip(uv[:, 0], 0, W - 1.001); v = np.clip(uv[:, 1], 0, H - 1.001)
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int); du = u - u0; dv = v - v0
    return (F[v0, u0] * (1 - du) * (1 - dv) + F[v0, u0 + 1] * du * (1 - dv) + F[v0 + 1, u0] * (1 - du) * dv + F[v0 + 1, u0 + 1] * du * dv)


def proj(V, view, reg):
    S, v0 = reg["S"], reg["v0"]; u0 = reg["u"][view]
    if view == "top": return np.stack([u0 + S * V[:, 0], reg["vT"] - S * V[:, 1]], 1)
    a = math.radians(ANG[view]); return np.stack([u0 + S * (V[:, 0] * math.cos(a) + V[:, 1] * math.sin(a)), v0 - S * V[:, 2]], 1)


def near_side(V, view):
    """そのビューのカメラ側にある（＝見えていれば手前にある）度合い：正なら手前"""
    if view == "top": return V[:, 2] - 0.05
    a = math.radians(ANG[view]); cam = np.array([math.sin(a), -math.cos(a), 0.0])
    return V @ cam


def extents(VV, reg):
    """高さごとの髪の範囲：正面から x、横から y（メートル）"""
    S, v0 = reg["S"], reg["v0"]
    out = {}
    for view in ("front", "left"):
        inside = VV[view]["hull"] < 0
        rows = {}
        for v in range(inside.shape[0]):
            xs = np.nonzero(inside[v])[0]
            if len(xs): rows[v] = (xs.min(), xs.max())
        out[view] = rows
    zs, ex = [], []
    for v, (a, b) in out["front"].items():
        if v not in out["left"]: continue
        c, d = out["left"][v]
        z = (v0 - v) / S
        x0 = (a - reg["u"]["front"]) / S; x1 = (b - reg["u"]["front"]) / S
        y0 = (c - reg["u"]["left"]) / S; y1 = (d - reg["u"]["left"]) / S
        zs.append(z); ex.append((x0, x1, y0, y1))
    o = np.argsort(zs); Z = np.array(zs)[o]; E = np.array(ex)[o]
    k_ = np.ones(9) / 9.0                                      # 段（横じま）が出ないよう、高さ方向にならす
    E = np.stack([np.convolve(np.pad(E[:, j], 4, mode="edge"), k_, mode="valid") for j in range(4)], 1)
    return Z, E


def cam_dir(view):
    a = math.radians(ANG[view]); return np.array([math.sin(a), -math.cos(a), 0.0])     # 頭からカメラへの向き


def depth_map(head_m, view, reg, shape, stride=2):
    """各ピクセルで、頭のいちばん手前の面の深さ t（カメラ向きの座標）。当たらなければ −1"""
    S, v0 = reg["S"], reg["v0"]; u0 = reg["u"][view]; a = math.radians(ANG[view])
    H, W = shape; vs = np.arange(0, H, stride); us = np.arange(0, W, stride)
    UU, VVv = np.meshgrid(us, vs); r = (UU.ravel() - u0) / S; z = (v0 - VVv.ravel()) / S
    c = cam_dir(view); right = np.array([math.cos(a), math.sin(a), 0.0])
    t = np.full(len(r), 0.40); hit = np.zeros(len(r), bool); alive = np.ones(len(r), bool)
    for _ in range(90):
        idx = np.nonzero(alive)[0]
        if not len(idx): break
        p = right[None, :] * r[idx, None] + c[None, :] * t[idx, None]; p[:, 2] = z[idx]
        d = head_m(p)
        h = d < 0.0006; hit[idx[h]] = True; alive[idx[h]] = False
        t[idx[~h]] -= np.maximum(d[~h], 0.0008)
        gone = t < -0.40; alive &= ~gone
    T = np.where(hit, t, -1.0).reshape(len(vs), len(us))
    full = np.repeat(np.repeat(T, stride, 0), stride, 1)[:H, :W]
    return full


def hair_model(k, head_m, p_round=2.6):
    P, reg, VV = build(k)
    NECK = P["loft"]["neck"]
    ZS, EX = extents(VV, reg)
    import loft_head as _lh
    hm = _lh.loft_model(dict(P, loft=dict(P["loft"], no_neck=True)), np.zeros(3))
    HEADNN = hm
    EAR_Y = P["loft"]["ear"]["center"][1]
    def rounding(p):
        z = p[:, 2]
        x0 = np.interp(z, ZS, EX[:, 0]); x1 = np.interp(z, ZS, EX[:, 1]); y0 = np.interp(z, ZS, EX[:, 2]); y1 = np.interp(z, ZS, EX[:, 3])
        hx = np.maximum((x1 - x0) / 2, 1e-3); hy = np.maximum((y1 - y0) / 2, 1e-3)
        X = np.abs(p[:, 0] - (x0 + x1) / 2) / hx; Y = np.abs(p[:, 1] - (y0 + y1) / 2) / hy
        return ((X ** p_round + Y ** p_round) ** (1 / p_round) - 1) * np.minimum(hx, hy)
    DM = {view: depth_map(head_m, view, reg, D["shape"]) for view, D in VV.items()}
    def F(p):
        d = np.full(len(p), -1.0)
        for view, D in VV.items():
            uv = proj(p, view, reg)
            d = np.maximum(d, sample(D["hull"], uv))                 # 視体積：どのビューの輪郭にも入る
            # 見えるはずの肌を隠さない：肌に投影され、頭の面より手前（カメラ側）にある点は髪ではない
            sk = sample(D["skin"], uv)                               # 肌の中なら−
            tp = p @ cam_dir(view)
            H_, W_ = DM[view].shape; ui = np.clip(np.round(uv[:, 0]).astype(int), 0, W_ - 1); vi = np.clip(np.round(uv[:, 1]).astype(int), 0, H_ - 1)
            th = DM[view][vi, ui]
            front = (th < -0.5) | (tp > th + 0.002)                   # 頭に当たらない所、または頭より手前
            d = np.maximum(d, np.where(front, -sk - 0.002, -1.0))
        d = np.maximum(d, rounding(p))                               # 断面は角の丸い四角（角を落とす）
        # 後頭部は、後ろから見て髪の所なら、頭に沿った薄い髪（4mm）で必ず覆う（すき間から肌が見えないように）
        hd = HEADNN(p); shell = np.maximum(hd - 0.012, -hd - 0.001)          # 12mm（格子で細いかけらを除いても残る厚さ）
        Db = VV["back"]; uvb = proj(p, "back", reg)
        in_hair_b = np.maximum(sample(Db["hull"], uvb), -sample(Db["skin"], uvb))
        shell = np.maximum(shell, np.maximum(in_hair_b, (EAR_Y + 0.004) - p[:, 1]))
        d = np.minimum(d, shell)
        d = np.maximum(d, -(HEADNN(p) - 0.002))                      # 頭の外側（首は除く：うなじの髪は首に重なってよい）
        # 首の前と横（タートルネックの高さ）には髪を置かない。うなじ（後ろ）は残す
        q = p - np.array([0.0, NECK["c"][1], 0.0])
        rr = np.sqrt((q[:, 0] / (NECK["r"][0] + 0.03)) ** 2 + (q[:, 1] / (NECK["r"][1] + 0.03)) ** 2)
        low = np.clip((-0.07 - p[:, 2]) / 0.02, 0, 1) * np.clip((0.035 - p[:, 1]) / 0.02, 0, 1)
        d = np.maximum(d, np.where(low > 0, (1 - rr) * 0.03 * low, -1.0))
        return d
    m = sdf.Model(); m.add(F, "hair", bones={"head": 1.0})
    return m


def _erode(a):
    b = a.copy()
    b[1:] &= a[:-1]; b[:-1] &= a[1:]; b[:, 1:] &= a[:, :-1]; b[:, :-1] &= a[:, 1:]; b[:, :, 1:] &= a[:, :, :-1]; b[:, :, :-1] &= a[:, :, 1:]
    return b


def _dilate(a):
    b = a.copy()
    b[1:] |= a[:-1]; b[:-1] |= a[1:]; b[:, 1:] |= a[:, :-1]; b[:, :-1] |= a[:, 1:]; b[:, :, 1:] |= a[:, :, :-1]; b[:, :, :-1] |= a[:, :, 1:]
    return b


def _box3(f):
    g = f.copy()
    for ax in range(3):
        a = np.moveaxis(g, ax, 0); s_ = a.copy(); s_[1:] += a[:-1]; s_[:-1] += a[1:]; g = np.moveaxis(s_ / 3.0, 0, ax)
    return g


def hair_mesh(k, head_m, h=0.004, open_r=1):
    """髪の場を格子で調べ → 細いかけらを除く（オープニング）→ 一番大きなかたまりだけ残す → なめらかにして網目に"""
    m = hair_model(k, head_m)
    lo = np.array([-0.21, -0.23, -0.15]); hi = np.array([0.21, 0.25, 0.28])
    n = np.floor((hi - lo) / h).astype(int) + 1
    xs, ys, zs = (lo[i] + h * np.arange(n[i]) for i in range(3))
    X, Y = np.meshgrid(xs, ys, indexing="ij"); XY = np.stack([X.ravel(), Y.ravel()], 1)
    occ = np.zeros(tuple(n), bool)
    for kz, z in enumerate(zs):
        P = np.concatenate([XY, np.full((len(XY), 1), z)], 1)
        occ[:, :, kz] = (m(P) < 0).reshape(n[0], n[1])
    occ[0] = occ[-1] = False; occ[:, 0] = occ[:, -1] = False; occ[:, :, 0] = occ[:, :, -1] = False
    for _ in range(open_r): occ = _erode(occ)
    for _ in range(open_r): occ = _dilate(occ)
    idx = np.argwhere(occ)
    if len(idx):
        seed = np.zeros_like(occ); top = idx[np.argmax(idx[:, 2])]; seed[tuple(top)] = True; cnt = 1
        while True:
            nx = _dilate(seed) & occ; c2 = int(nx.sum())
            if c2 == cnt: break
            seed, cnt = nx, c2
        occ = seed
    s_ = _box3(_box3(occ.astype(np.float32)))
    G = (0.5 - s_) * 3.0 * h
    def F(p):
        q = (p - lo) / h; i0 = np.clip(np.floor(q).astype(int), 0, n - 2); t = np.clip(q - i0, 0, 1)
        out = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                    out = out + w * G[i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz]
        return out
    V, Q = sdf.mesh(F, lo + 2 * h, hi - 2 * h, h, relax_iters=2)
    return V, Q
