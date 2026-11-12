# 資料の絵を3Dに貼るための「どの向きの絵を使うか」の重み（頂点ごと）。見えていて、面がその向きを向いているほど大きい
# 使い方: python3 proj_weights.py M1   → sheets/projw_M1.npz（Wh＝頭、Whair＝髪。列は VIEWS の順）
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SH = os.path.join(HERE, "..", "..", "sheets")
VIEWS = ["front", "left45", "left", "back", "right"]
ANG = {"front": 0.0, "left45": 45.0, "left": 90.0, "back": 180.0, "right": 270.0}


def normals(V, Q):
    n = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
    N = np.zeros_like(V)
    for j in range(4): np.add.at(N, Q[:, j], n)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    if ((V - V.mean(0)) * N).sum(1).mean() < 0: N = -N        # 外向きにそろえる
    return N


def cam_dir(view):
    a = math.radians(ANG[view]); return np.array([math.sin(a), -math.cos(a), 0.0])


def proj(V, view, S, v0, u0):
    a = math.radians(ANG[view])
    return np.stack([u0 + S * (V[:, 0] * math.cos(a) + V[:, 1] * math.sin(a)), v0 - S * V[:, 2]], 1)


def weights(Vs, Ns, k, power=10.0, tol=0.004, splat=2):
    sp = json.load(open(os.path.join(SH, f"spec_{k}.json"))); S, v0 = sp["reg"]["S"], sp["reg"]["v0"]
    reg = json.load(open(os.path.join(SH, f"reg_{k}.json")))
    from PIL import Image
    allV = np.concatenate(Vs)
    out = [np.zeros((len(V), len(VIEWS))) for V in Vs]
    for j, view in enumerate(VIEWS):
        W_, H_ = Image.open(os.path.join(SH, f"{k}_{view}.png")).size
        c = cam_dir(view)
        uv = proj(allV, view, S, v0, reg[view]); dep = allV @ c
        zb = np.full((H_, W_), -1e9)
        ui = np.round(uv[:, 0]).astype(int); vi = np.round(uv[:, 1]).astype(int)
        for du in range(-splat, splat + 1):
            for dv in range(-splat, splat + 1):
                uu = np.clip(ui + du, 0, W_ - 1); vv = np.clip(vi + dv, 0, H_ - 1)
                np.maximum.at(zb, (vv, uu), dep)
        for i, (V, N) in enumerate(zip(Vs, Ns)):
            uvi = proj(V, view, S, v0, reg[view]); d = V @ c
            a = np.clip(np.round(uvi[:, 0]).astype(int), 0, W_ - 1); b = np.clip(np.round(uvi[:, 1]).astype(int), 0, H_ - 1)
            inside = (uvi[:, 0] >= 0) & (uvi[:, 0] < W_) & (uvi[:, 1] >= 0) & (uvi[:, 1] < H_)
            vis = (d >= zb[b, a] - tol) & inside
            facing = np.clip(N @ c, 0, 1)
            out[i][:, j] = vis * facing ** power
    res = []
    for V, N, Wt in zip(Vs, Ns, out):
        s = Wt.sum(1)
        bad = s < 1e-4                      # どの絵からも見えない所（あごの下など）：向きだけで決める
        if bad.any():
            alt = np.stack([np.clip(N[bad] @ cam_dir(v), 0, 1) ** power for v in VIEWS], 1) + 1e-6
            Wt[bad] = alt; s = Wt.sum(1)
        res.append(Wt / s[:, None])
    return res


def weights_cam(Vs, Ns, k, dcam, sigma_deg=28.0, tol=0.004, splat=2, hard=False):
    """カメラの向き dcam（頭の座標）に近い向きの絵ほど重く（見えていて、面がそちらを向いている所だけ）"""
    sp = json.load(open(os.path.join(SH, f"spec_{k}.json"))); S, v0 = sp["reg"]["S"], sp["reg"]["v0"]
    reg = json.load(open(os.path.join(SH, f"reg_{k}.json")))
    from PIL import Image
    dcam = np.asarray(dcam, float); dcam /= np.linalg.norm(dcam)
    allV = np.concatenate(Vs); out = [np.zeros((len(V), len(VIEWS))) for V in Vs]
    for j, view in enumerate(VIEWS):
        W_, H_ = Image.open(os.path.join(SH, f"{k}_{view}.png")).size
        c = cam_dir(view); uv = proj(allV, view, S, v0, reg[view]); dep = allV @ c
        zb = np.full((H_, W_), -1e9); ui = np.round(uv[:, 0]).astype(int); vi = np.round(uv[:, 1]).astype(int)
        for du in range(-splat, splat + 1):
            for dv in range(-splat, splat + 1):
                np.maximum.at(zb, (np.clip(vi + dv, 0, H_ - 1), np.clip(ui + du, 0, W_ - 1)), dep)
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(c @ dcam)))))
        pref = math.exp(-(ang / sigma_deg) ** 2)
        for i, (V, N) in enumerate(zip(Vs, Ns)):
            uvi = proj(V, view, S, v0, reg[view]); d = V @ c
            a = np.clip(np.round(uvi[:, 0]).astype(int), 0, W_ - 1); b = np.clip(np.round(uvi[:, 1]).astype(int), 0, H_ - 1)
            inside = (uvi[:, 0] >= 0) & (uvi[:, 0] < W_) & (uvi[:, 1] >= 0) & (uvi[:, 1] < H_)
            vis = (d >= zb[b, a] - tol) & inside
            f = np.clip(N @ c, 0, 1); facing = np.clip((f - 0.05) / 0.30, 0, 1) ** 2
            if hard: facing = (f > 0.06).astype(float)        # 見えていれば、カメラに一番近い絵を優先（向きでは選ばない）
            out[i][:, j] = vis * facing * (pref + 1e-3 * f ** 8)
    res = []
    for V, N, Wt in zip(Vs, Ns, out):
        s = Wt.sum(1); bad = s < 1e-5
        if bad.any():
            alt = np.stack([np.clip(N[bad] @ cam_dir(v), 0, 1) ** 10 for v in VIEWS], 1) + 1e-6
            Wt[bad] = alt; s = Wt.sum(1)
        res.append(Wt / s[:, None])
    return res


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[2] == "--fit":       # 場面のカメラに合わせた重み
        k = sys.argv[1]; fit = json.load(open(sys.argv[3]))
        h = fit["heads"][k]; C = np.array(fit["camera"]["C"]); H = np.array(h["H"]); R = np.array(h["R"])
        dcam = R.T @ ((C - H) / np.linalg.norm(C - H))
        D = np.load(os.path.join(SH, f"mesh_{k}.npz")); V, Q, Vh, Qh = D["V"], D["Q"], D["Vh"], D["Qh"]
        Wh, Whair = weights_cam([V, Vh], [normals(V, Q), normals(Vh, Qh)], k, dcam)
        np.savez(os.path.join(SH, f"projw_{k}_scene.npz"), Wh=Wh.astype(np.float32), Whair=Whair.astype(np.float32))
        print(k, "camera dir (head coords)", np.round(dcam, 3), "mean weights head", np.round(Wh.mean(0), 2)); sys.exit(0)
    k = sys.argv[1]
    D = np.load(os.path.join(SH, f"mesh_{k}.npz"))
    V, Q, Vh, Qh = D["V"], D["Q"], D["Vh"], D["Qh"]
    Nh_, Nhair = normals(V, Q), normals(Vh, Qh)
    Wh, Whair = weights([V, Vh], [Nh_, Nhair], k)
    np.savez(os.path.join(SH, f"projw_{k}.npz"), Wh=Wh.astype(np.float32), Whair=Whair.astype(np.float32))
    print(k, "head", Wh.shape, "hair", Whair.shape, "mean weights head", np.round(Wh.mean(0), 2), "hair", np.round(Whair.mean(0), 2))
