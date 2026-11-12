# 座った体に絵を貼る重みと、細かく作った頭（6面図から）を座った絵の頭に合わせる位置・向き・大きさ
# 使い方: python3 seat_assemble.py M1   → sheets/seatasm_M1.npz（体の重み Wb、頭の置き方 head_T）
import sys, os, json, math, time
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seat_sheet as ss
from proj_weights import normals
SH = os.path.join(HERE, "..", "..", "sheets")


def view_dir(view, reg):
    a = math.radians(reg.get("ang", {}).get(view, ss.ANG[view])); return np.array([math.sin(a), -math.cos(a), 0.0])


def body_weights(V, N, reg, M, dcam=None, power=10.0, sigma=28.0, tol=0.006, splat=2, extra=None, hard=False):
    """extra：ほかの物（頭など）の点。手前にあれば体を隠す"""
    allV = V if extra is None else np.concatenate([V, extra])
    W = np.zeros((len(V), len(ss.VIEWS)))
    for j, view in enumerate(ss.VIEWS):
        Hh, Ww = M[view]["person"].shape; c = view_dir(view, reg)
        uv = ss.proj(allV, view, reg); dep = allV @ c
        zb = np.full((Hh, Ww), -1e9); ui = np.round(uv[:, 0]).astype(int); vi = np.round(uv[:, 1]).astype(int)
        for du in range(-splat, splat + 1):
            for dv in range(-splat, splat + 1):
                np.maximum.at(zb, (np.clip(vi + dv, 0, Hh - 1), np.clip(ui + du, 0, Ww - 1)), dep)
        uvb = uv[:len(V)]; d = V @ c
        a = np.clip(np.round(uvb[:, 0]).astype(int), 0, Ww - 1); b = np.clip(np.round(uvb[:, 1]).astype(int), 0, Hh - 1)
        vis = d >= zb[b, a] - tol
        inside = M[view]["person"][b, a] | (M[view]["bench"][b, a] & (view == "back"))
        f = np.clip(N @ c, 0, 1)
        if dcam is None: w = f ** power
        else:
            ang = math.degrees(math.acos(max(-1.0, min(1.0, float(c @ dcam)))))
            fac = (f > 0.06).astype(float) if hard else np.clip((f - 0.05) / 0.30, 0, 1) ** 2
            w = fac * (math.exp(-(ang / sigma) ** 2) + 1e-3 * f ** 8)
        if view == "back":
            w = w * (~M[view]["bench"][b, a])            # 後ろの絵のベンチの部分は使わない（体が隠れている）
        W[:, j] = vis * w * M[view]["person"][b, a]
    s = W.sum(1); bad = s < 1e-6
    if bad.any():
        alt = np.stack([np.clip(N[bad] @ view_dir(v, reg), 0, 1) ** power for v in ss.VIEWS], 1) + 1e-6
        W[bad] = alt; s = W.sum(1)
    return W / s[:, None]


def rotm(yaw, pitch, roll):
    """頭の向き：まず前後の傾き（X軸、うつむき＝正）、左右の傾き（Y軸）、最後に向き（Z軸）"""
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]]); Rx = np.array([[1.0, 0, 0], [0, cp, -sp], [0, sp, cp]]); Ry = np.array([[cr, 0, sr], [0, 1.0, 0], [-sr, 0, cr]])
    return Rz @ Ry @ Rx


def fit_head(k, M, reg, Vhead, Vface=None, Nface=None):
    """頭（髪と顔、頭の座標）を座った絵の頭の輪郭に合わせる：大きさ・向き・位置"""
    # 頭の部分：あごより上の行だけで比べる。あごの高さは横の絵の肌のいちばん下（顔の範囲）で決める
    rng = np.random.default_rng(1); P0 = Vhead[rng.choice(len(Vhead), min(len(Vhead), 25000), replace=False)]
    Ms = {v: M[v]["person"][::2, ::2] for v in ss.VIEWS}
    SK = {}
    for v in ss.VIEWS:
        rgb = M[v]["rgb"]; r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]; lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        SK[v] = ((g - b > 0.08) & (r - b > 0.20) & (lum > 0.33))[::2, ::2]
    def score(p):
        s_, yaw, pitch, roll, tx, ty, tz = p
        Rm = rotm(yaw, pitch, roll)
        P = (P0 * s_) @ Rm.T + np.array([tx, ty, tz])
        # うつむき＝pitch が正（この回し方では前が下がる）。−5°〜45°、左右の傾き ±12°、向き ±30° の範囲
        pen = max(0.0, abs(math.degrees(roll)) - 12) * 0.02 + max(0.0, abs(math.degrees(yaw)) - 30) * 0.02 + max(0.0, -5 - math.degrees(pitch)) * 0.02 + max(0.0, math.degrees(pitch) - 45) * 0.02
        face = 0.0
        if Vface is not None:      # 顔の肌の点は、その向きから見える所なら絵の肌の上に来るはず
            Pf = (Vface * s_) @ Rm.T + np.array([tx, ty, tz]); Nf = Nface @ Rm.T
            for view in ("front", "left", "left45"):
                c = view_dir(view, reg); sel = (Nf @ c) > 0.35
                if sel.sum() < 30: continue
                uv = ss.proj(Pf[sel], view, reg) / 2; u = np.clip(np.round(uv[:, 0]).astype(int), 0, SK[view].shape[1] - 1); v = np.clip(np.round(uv[:, 1]).astype(int), 0, SK[view].shape[0] - 1)
                face += SK[view][v, u].mean() / 3.0
        tot = 0.0
        for view in ss.VIEWS:
            m = Ms[view]; uv = ss.proj(P, view, reg) / 2; u = np.round(uv[:, 0]).astype(int); v = np.round(uv[:, 1]).astype(int)
            ok = (u >= 0) & (u < m.shape[1]) & (v >= 0) & (v < m.shape[0]); sil = np.zeros_like(m); sil[v[ok], u[ok]] = True
            sil = sil | np.roll(sil, 1, 0) | np.roll(sil, 1, 1) | np.roll(sil, -1, 0) | np.roll(sil, -1, 1)
            vlo = int(v[ok].min()) - 3; vhi = int(np.percentile(v[ok], 97))       # 頭の高さの範囲だけ
            mm = m[max(vlo, 0):vhi]; ss_ = sil[max(vlo, 0):vhi]
            tot += (mm & ss_).sum() / max((mm | ss_).sum(), 1)
        return tot / len(ss.VIEWS) + 0.8 * face - pen
    # 初期値：正面と横の絵の、上のほうの人の画素の中心
    mF = M["front"]["person"]; mL = M["left"]["person"]
    top = np.nonzero(mF.any(1))[0].min(); S = reg["S"]
    rowsF = mF[top:top + int(0.25 * S)]; cF = np.nonzero(rowsF.any(0))[0]; xc = ((cF.min() + cF.max()) / 2 - reg["u"]["front"]) / S
    rowsL = mL[top:top + int(0.25 * S)]; cL = np.nonzero(rowsL.any(0))[0]; yc = ((cL.min() + cL.max()) / 2 - reg["u"]["left"]) / S
    zc = (reg["floor"] - (top + 0.20 * S)) / S
    p = np.array([0.96, 0.0, math.radians(22), 0.0, xc, yc, zc]); best = score(p)
    steps = np.array([0.03, math.radians(6), math.radians(6), math.radians(4), 0.012, 0.012, 0.012])
    for it in range(6):
        improved = True
        while improved:
            improved = False
            for i in range(len(p)):
                for sgn in (1, -1):
                    q = p.copy(); q[i] += sgn * steps[i]; v_ = score(q)
                    if v_ > best: best, p, improved = v_, q, True
        steps *= 0.5
    return p, best


if __name__ == "__main__":
    k = sys.argv[1]; t0 = time.time()
    M, floor = ss.masks(k); reg = json.load(open(os.path.join(SH, f"seatreg_{k}.json")))
    B = np.load(os.path.join(SH, f"seatmesh_{k}.npz")); V, Q = B["V"], B["Q"]; N = normals(V, Q)
    H = np.load(os.path.join(SH, f"mesh_{k}.npz")); Vhead = np.concatenate([H["V"][H["V"][:, 2] > -0.105], H["Vh"]])     # 首は除く（体の首を使う）
    Nh = normals(H["V"], H["Q"]); Vh0 = H["V"]
    fs = (Vh0[:, 2] > -0.10) & (Vh0[:, 2] < 0.035) & (Vh0[:, 1] < -0.04) & (np.abs(Vh0[:, 0]) < 0.075)     # 顔（髪より下、あごより上）
    p, sc = fit_head(k, M, reg, Vhead, Vh0[fs], Nh[fs])
    print(k, "head fit: scale", round(p[0], 3), "yaw/pitch/roll deg", np.round(np.degrees(p[1:4]), 1), "pos", np.round(p[4:7], 3), "mean IoU", round(sc, 3), flush=True)
    R = rotm(*p[1:4]); Ph = (Vhead * p[0]) @ R.T + p[4:7]
    Wb = body_weights(V, N, reg, M, extra=Ph)
    np.savez(os.path.join(SH, f"seatasm_{k}.npz"), Wb=Wb.astype(np.float32), head=p)
    print(k, "body weights", np.round(Wb.mean(0), 2), round(time.time() - t0, 1), "s")
