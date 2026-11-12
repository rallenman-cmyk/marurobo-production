# 参考画像の顔：顔の表面に「描いた」アニメ風の目（白目・黒目は面の上、太い上まつげの線と目尻のはね）
# 黒目の位置は、目の骨と一緒に回る座標から材質の中で計算する（視線が動く）。まばたきはシェイプキー
import math
import numpy as np
from hgen import onto_face, head_frame


def almond_uv(P, s, i, nu=30, nv=14, close=0.0, wide=0.0):
    """目の形（頭の中心からの x, z）。u＝目頭0→目尻1、v＝下−1→上+1"""
    hf = head_frame(P); ec = hf["eye"][i]; sx = 1 if i == 0 else -1
    E = P.get("aeye", 1.0)
    w = 0.031 * s * E; hu = 0.0090 * s * E * P.get("eye_open", 1.0); hl = 0.0046 * s * E
    x_in = ec[0] - sx * P.get("eye_in", 0.44) * w; x_out = ec[0] + sx * (1 - P.get("eye_in", 0.44)) * w
    z_in = ec[2] - 0.0012 * s; z_out = ec[2] + 0.0016 * s * P.get("eye_tilt", 1.0)
    if P.get("loft"):         # 6面図の目の形（目頭・目尻・上下の高さ）
        B = P["loft"]["feat"]["eye_box"]
        x_in, x_out = sx * B["x_in"], sx * B["x_out"]; z_in, z_out = B["z_in"], B["z_out"]; hu, hl = B["hu"] * (1 + 0 * E), B["hl"]; w = abs(x_out - x_in)
    u = np.linspace(0, 1, nu); v = np.linspace(-1, 1, nv)
    U, Vv = np.meshgrid(u, v, indexing="ij")
    base = z_in + (z_out - z_in) * U
    top = hu * np.sin(np.pi * U ** 0.80) ** 0.62 * (1 + 0.22 * wide)
    bot = hl * np.sin(np.pi * U ** 1.16) ** 0.85
    upper = base + top * (1 - close) - bot * close * 0.92        # 閉じると上のふちが下のふちへ
    lower = base - bot
    Z = lower + (upper - lower) * (Vv + 1) / 2
    X = x_in + (x_out - x_in) * U
    return X, Z, U, Vv, dict(base=base, top=top, bot=bot, x_in=x_in, x_out=x_out, sx=sx, w=w, ec=ec)


def _grid_faces(nu, nv):
    F = []
    for a in range(nu - 1):
        for b in range(nv - 1):
            F.append((a * nv + b, (a + 1) * nv + b, (a + 1) * nv + b + 1, a * nv + b + 1))
    return F


def eye_white(Fm, hc, P, s, i):
    """白目の面（顔から0.3mm浮かせる）と、シェイプキー（close, wide）"""
    out = {}
    for nm, cl, wd in (("rest", 0.0, 0.0), ("close", 1.0, 0.0), ("wide", 0.0, 1.0)):
        X, Z, U, Vv, info = almond_uv(P, s, i, close=cl, wide=wd)
        nu, nv = X.shape
        pts, nrm = onto_face(Fm, np.asarray(hc), np.stack([X.ravel(), Z.ravel()], 1), -0.16 * s, 0.00030 * s)
        out[nm] = pts
    F = _grid_faces(nu, nv)
    if i == 1:                                    # 右目は u が −X 向きなので面の向きを裏返す
        F = [f[::-1] for f in F]
    return out, F, dict(u=U.ravel(), v=Vv.ravel())


def _ribbon(Fm, hc, s, cx, cz, half, nx, nz, offset):
    """（x,z）の線に沿った帯：中心線と、面の上の上下の向き（nx,nz）に half だけ広げる → 顔に貼る"""
    n = len(cx); pts = []
    for k in (-1.0, 0.0, 1.0):
        pts.append(np.stack([cx + nx * half * k, cz + nz * half * k], 1))
    UV = np.concatenate(pts)
    V, _ = onto_face(Fm, np.asarray(hc), UV, -0.16 * s, offset)
    F = []
    for r in range(2):
        for j in range(n - 1):
            F.append((r * n + j, r * n + j + 1, (r + 1) * n + j + 1, (r + 1) * n + j))
    return V, F


def lash_line(Fm, hc, P, s, i, close=0.0, wide=0.0):
    """太い上まつげの線＋目尻のはね（外へ、少し上へ伸びて細くなる）"""
    X, Z, U, Vv, info = almond_uv(P, s, i, nu=40, nv=2, close=close, wide=wide)
    sx = info["sx"]
    cx = X[:, -1]; cz = Z[:, -1]; u = U[:, 0]
    # 目尻の先へ伸ばす（はね）
    E = P.get("aeye", 1.0); L = P.get("wing", 1.0) * 0.0068 * s * E
    t = np.linspace(0, 1, 9)[1:]
    dx = cx[-1] - cx[-3]; dz = cz[-1] - cz[-3]; d = np.array([dx, dz]); d /= np.linalg.norm(d)
    d2 = np.array([sx * 0.80, 0.60]); d2 /= np.linalg.norm(d2)
    wing = np.array([cx[-1], cz[-1]])[None, :] + (np.outer(t, d * 0.5 + d2 * 0.5)) * L + np.outer(t ** 2, d2) * L * 0.25
    cx = np.concatenate([cx, wing[:, 0]]); cz = np.concatenate([cz, wing[:, 1]])
    uu = np.concatenate([u, 1 + t * 0.35])
    th = P.get("lash_w", 1.0) * s * np.where(uu <= 1, 0.00055 + 0.00125 * np.sin(np.pi * np.clip(uu, 0, 1) ** 0.7) ** 0.5 + 0.0004 * uu,
                                              0.00175 * np.clip(1 - (uu - 1) / 0.35, 0, 1) ** 0.9 + 0.00008)
    # 線の上下の向き（中心線に垂直）
    tx = np.gradient(cx); tz = np.gradient(cz); ln = np.hypot(tx, tz) + 1e-12; tx /= ln; tz /= ln
    nx, nz = -tz * sx, tx * sx
    if (nz < 0).mean() > 0.5: nx, nz = -nx, -nz
    ccx = cx + nx * th * 0.55; ccz = cz + nz * th * 0.55          # 線は目のふちより少し上にかぶせる
    V, F = _ribbon(Fm, hc, s, ccx, ccz, th, nx, nz, 0.00055 * s)
    if i == 1: F = [f[::-1] for f in F]
    return V, F


def lower_line(Fm, hc, P, s, i):
    X, Z, U, Vv, info = almond_uv(P, s, i, nu=24, nv=2)
    m = U[:, 0] > 0.38
    cx = X[m, 0]; cz = Z[m, 0]; uu = U[m, 0]
    th = 0.00030 * s * np.sin(np.pi * (uu - 0.38) / 0.62) ** 0.6 + 0.00004 * s
    tx = np.gradient(cx); tz = np.gradient(cz); ln = np.hypot(tx, tz) + 1e-12; tx /= ln; tz /= ln
    nx, nz = -tz, tx
    if (nz < 0).mean() > 0.5: nx, nz = -nx, -nz
    V, F = _ribbon(Fm, hc, s, cx - nx * th * 0.4, cz - nz * th * 0.4, th, nx, nz, 0.00045 * s)
    if i == 1: F = [f[::-1] for f in F]
    return V, F


def eye_set(Fm, hc, P, s):
    """両目の部品：白目（rest/close/wide）、上の線（同）、下の線、目の中心からの奥行き"""
    out = {}
    for i, sd in enumerate(("L", "R")):
        wv, wf, uv = eye_white(Fm, hc, P, s, i)
        lv = {nm: lash_line(Fm, hc, P, s, i, close=c, wide=w)[0] for nm, c, w in (("rest", 0, 0), ("close", 1, 0), ("wide", 0, 1))}
        lf = lash_line(Fm, hc, P, s, i)[1]
        dv, df = lower_line(Fm, hc, P, s, i)
        ec = np.asarray(hc) + head_frame(P)["eye"][i]
        cpt = wv["rest"][len(wv["rest"]) // 2]
        out[sd] = dict(white=wv, white_F=wf, u=uv["u"], v=uv["v"], lash=lv, lash_F=lf, low=dv, low_F=df, ec=ec, depth=float(np.linalg.norm(cpt - ec)))
    return out
