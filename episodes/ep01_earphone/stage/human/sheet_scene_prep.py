# 電車の場面の準備（Blenderの外で）：3人をベンチに座らせる置き方、参考画像に合うカメラ、カメラに合わせた絵の重み
# 使い方: python3 sheet_scene_prep.py fit10.json out.json
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import seat_sheet as ss, seat_assemble as sa
from proj_weights import normals, weights_cam
SH = os.path.join(HERE, "..", "..", "sheets")
import trace_fit as tf            # 参考画像の目印（OBS）、頭の目印（KP, HC）、投影

ORDER = ["M1", "W1", "G1"]
SEAT_Z = 0.465 - 0.45             # 電車の座面は絵のベンチより 1.5cm 高い
PELVIS = np.array([0.0, 0.24, 0.45])     # 座った体の「お尻の中心」（絵の座標）


def Rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def person_T(psi, Y):
    """絵の座標 → 世界：向き psi、お尻の中心を (−0.02, Y, 0.465) に置く"""
    R = Rz(psi); T = np.array([-0.02, Y, 0.45 + SEAT_Z]) - R @ PELVIS
    return R, T


def head_world(k, psi, Y, A, dp=0.0, dy=0.0):
    """dp, dy：場面に合わせた頭の追加のうつむき・向き（頭の中心まわり）"""
    p = A[k]["head"]; Rh = sa.rotm(*p[1:4]) @ sa.rotm(dy, dp, 0.0); R, T = person_T(psi, Y)
    return R @ Rh * p[0], R @ p[4:7] + T              # 頭の座標 → 世界：x ↦ M x + t


def keypoints_world(k, psi, Y, A, dp=0.0, dy=0.0):
    M, t = head_world(k, psi, Y, A, dp, dy)
    return np.array([M @ (tf.KP[k][n] - tf.HC[k]) + t for n in tf.NAMES])


NP = 4
def residual(x, A, init):
    cam = (x[0:3], x[3], x[4], x[5], x[6]); res = []
    for i, k in enumerate(ORDER):
        psi, Y, dp, dy = x[7 + NP * i: 7 + NP * (i + 1)]
        uv, zc = tf.project(keypoints_world(k, psi, Y, A, dp, dy), cam)
        res.append(((uv - np.array([tf.OBS[k][n] for n in tf.NAMES], float)) / 6.0).ravel())
        res.append(np.minimum(zc - 0.3, 0) * 50)
        res.append(np.array([(psi - init[k][0]) / math.radians(1.0), (Y - init[k][1]) / 0.25, dp / math.radians(10), dy / math.radians(3)]) * 1.5)
    C = cam[0]
    res.append(np.array([(C[2] - 1.05) / 0.20, (cam[4] - 27) / 4, cam[3] / math.radians(1.5), (cam[2] - math.radians(10)) / math.radians(6)]) * 2.0)
    return np.concatenate(res)


def lm(f, x, iters=150):
    lam = 1e-2; r = f(x); e = r @ r
    for _ in range(iters):
        J = np.zeros((len(r), len(x))); h = 1e-5
        for j in range(len(x)):
            dx = np.zeros_like(x); dx[j] = h; J[:, j] = (f(x + dx) - r) / h
        A_ = J.T @ J; g = J.T @ r
        while True:
            st = np.linalg.solve(A_ + lam * np.diag(np.diag(A_) + 1e-9), -g); xn = x + st; rn = f(xn); en = rn @ rn
            if en < e: x, r, e = xn, rn, en; lam = max(lam / 3, 1e-8); break
            lam *= 4
            if lam > 1e9: return x, e
    return x, e


if __name__ == "__main__":
    fit = json.load(open(sys.argv[1])); out = sys.argv[2]
    A = {k: dict(np.load(os.path.join(SH, f"seatasm_{k}.npz"))) for k in ORDER}
    # 体の向き：参考に合わせた頭の向きから、座った絵での頭の向き（体に対する）を引いたもの（ほぼ固定）
    init = {k: (fit["heads"][k]["psi"] - float(A[k]["head"][1]), fit["heads"][k]["H"][1]) for k in ORDER}
    cf = fit["camera"]
    x0 = np.array(list(cf["C"]) + [cf["yaw"], cf["pitch"], cf["roll"], cf["lens"]] + sum([[init[k][0], init[k][1], 0.0, 0.0] for k in ORDER], []))
    x, e = lm(lambda x: residual(x, A, init), x0)
    cam = (x[0:3], x[3], x[4], x[5], x[6])
    print("camera", np.round(x[0:3], 3), "yaw/pitch/roll", np.round(np.degrees(x[3:6]), 1), "lens", round(x[6], 1), "err", round(e, 2))
    res = dict(camera=dict(C=list(map(float, x[0:3])), yaw=float(x[3]), pitch=float(x[4]), roll=float(x[5]), lens=float(x[6])), people={})
    for i, k in enumerate(ORDER):
        psi, Y, dp, dy = x[7 + NP * i: 7 + NP * (i + 1)]
        uv, _ = tf.project(keypoints_world(k, psi, Y, A, dp, dy), cam)
        err = np.linalg.norm(uv - np.array([tf.OBS[k][n] for n in tf.NAMES], float), axis=1)
        R, T = person_T(psi, Y); Mh, th = head_world(k, psi, Y, A, dp, dy)
        print(k, "yaw", round(math.degrees(psi), 1), "Y", round(Y, 3), "head extra pitch/yaw", round(math.degrees(dp), 1), round(math.degrees(dy), 1), "keypoint err px", np.round(err, 1))
        # カメラに合わせた絵の重み：体（座った絵4枚）と頭・髪（6面図5枚）
        Cw = x[0:3]
        reg = json.load(open(os.path.join(SH, f"seatreg_{k}.json"))); Mk, _ = ss.masks(k)
        Bm = np.load(os.path.join(SH, f"seatmesh_{k}.npz")); Vb, Qb = Bm["V"], Bm["Q"]
        cb = R.T @ (Cw - (R @ Vb.mean(0) + T)); cb /= np.linalg.norm(cb)
        Hm = np.load(os.path.join(SH, f"mesh_{k}.npz")); p = A[k]["head"]
        Vhs = (np.concatenate([Hm["V"][Hm["V"][:, 2] > -0.105], Hm["Vh"]]) * p[0]) @ sa.rotm(*p[1:4]).T + p[4:7]
        Wb = sa.body_weights(Vb, normals(Vb, Qb), reg, Mk, dcam=cb, extra=Vhs, sigma=8.0, hard=True)
        ch = np.linalg.solve(Mh, Cw - th); ch /= np.linalg.norm(ch)      # 頭の座標でのカメラの向き
        Wh, Whair = weights_cam([Hm["V"], Hm["Vh"]], [normals(Hm["V"], Hm["Q"]), normals(Hm["Vh"], Hm["Qh"])], k, ch, sigma_deg=8.0, hard=True)
        np.savez(os.path.join(SH, f"scenew_{k}.npz"), Wb=Wb.astype(np.float32), Wh=Wh.astype(np.float32), Whair=Whair.astype(np.float32))
        res["people"][k] = dict(psi=float(psi), Y=float(Y), dp=float(dp), dy=float(dy), R=R.tolist(), T=T.tolist(), Mh=Mh.tolist(), th=th.tolist(),
                                cam_body=cb.tolist(), cam_head=ch.tolist())
        print(k, "camera dir: body", np.round(cb, 2), "head", np.round(ch, 2), flush=True)
    json.dump(res, open(out, "w"), indent=1)
