# 参考画像の目印（目・鼻先・口・あご・耳）から、カメラと3人の頭の位置・向きを逆算する（重ね合わせの土台）
# 使い方: python3 trace_fit.py out.json [check.png]
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import hgen, animeface, ref_people

IMG_W, IMG_H = 1672, 941
# 参考画像で測った目印（ピクセル）。手前に見えているのは人物の左側（左目・左耳）
OBS = {
    "M1": dict(eye=(1255, 398), nose=(1182, 505), mouth=(1255, 525), chin=(1290, 605), ear=(1475, 355)),
    "W1": dict(eye=(545, 545), nose=(510, 595), mouth=(545, 622), chin=(575, 655), ear=(655, 515)),
    "G1": dict(eye=(230, 580), nose=(195, 610), mouth=(225, 635), chin=(250, 655), ear=(315, 570)),
}
ORDER = ["M1", "W1", "G1"]
VIEW = {"M1": 66.0, "W1": 70.0, "G1": 62.0}
W_VIEW = float(os.environ.get("W_VIEW", "1.0"))


def keypoints(cfg):
    """頭の目印（人物の休み姿勢の座標、メートル）と頭の中心"""
    P = dict(hgen.HEAD); P.update(cfg["head"]); B = dict(hgen.BODY); B.update(cfg.get("body", {}))
    if cfg.get("sheet"):
        P["loft"] = json.load(open(os.path.join(HERE, "..", "..", "sheets", f"loftP_{cfg['sheet']}.json")))
    J = hgen.skeleton(B); hc = np.asarray(J["head_center"], float); s = P["hs"]
    m = hgen.head_model(P, hc); hf = hgen.head_frame(P)
    wv, wf, uv = animeface.eye_white(m, hc, P, s, 0)
    eye = wv["rest"].mean(0)
    # 鼻先：正面から光線を飛ばして一番前に出ている点
    zs = np.linspace(-0.036, 0.004, 41) * s
    O = np.stack([np.full_like(zs, hc[0]), np.full_like(zs, hc[1] - 0.25), hc[2] + zs], 1)
    hits = hgen.surface_hit(m, O, np.tile([0, 1.0, 0], (len(zs), 1)), tmax=0.30)
    nose = hits[np.argmin(hits[:, 1])]
    mc = hf["mouth"]; mouth = hgen.surface_hit(m, np.array([[hc[0], hc[1] - 0.25, hc[2] + mc[2]]]), np.array([[0, 1.0, 0]]), tmax=0.30)[0]
    zc = -(0.0785 * P["face_len"] + 0.016) * s
    if P.get("loft"): zc = min(z for z, y in P["loft"]["base"]) + 0.006         # 6面図のあごの少し上
    chin = hgen.surface_hit(m, np.array([[hc[0], hc[1] - 0.25, hc[2] + zc]]), np.array([[0, 1.0, 0]]), tmax=0.30)[0]
    ear = hc + hf["ear"][0] + np.array([0.008 * s, 0.0, 0.0])
    if P.get("loft"):
        ec = P["loft"]["ear"]["center"]; ear = hc + np.array([P["loft"]["ear"]["out_x"] - 0.012, ec[1], ec[2]])
    return dict(eye=eye, nose=nose, mouth=mouth, chin=chin, ear=ear), hc, J


def rotz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
def rotx(a): c, s = math.cos(a), math.sin(a); return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])
def roty(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1.0, 0], [-s, 0, c]])
def head_R(psi, th, ph): return rotz(psi) @ rotx(th) @ roty(ph)


def cam_basis(yaw, pit, roll):
    d = np.array([math.cos(pit) * math.cos(yaw), math.cos(pit) * math.sin(yaw), math.sin(pit)])
    r0 = np.array([math.sin(yaw), -math.cos(yaw), 0.0]); u0 = np.cross(r0, d)
    r = r0 * math.cos(roll) + u0 * math.sin(roll); u = -r0 * math.sin(roll) + u0 * math.cos(roll)
    return d, r, u


def project(Pw, cam):
    C, yaw, pit, roll, f = cam
    d, r, u = cam_basis(yaw, pit, roll)
    v = Pw - C; zc = v @ d; fx = f / 36.0 * IMG_W
    return np.stack([IMG_W / 2 + fx * (v @ r) / zc, IMG_H / 2 - fx * (v @ u) / zc], -1), zc


KP, HC, JJ = {}, {}, {}
for k in ORDER:
    KP[k], HC[k], JJ[k] = keypoints(ref_people.PEOPLE[k])
NAMES = ["eye", "nose", "mouth", "chin", "ear"]


OFFN = ["nose", "mouth", "chin", "ear"]
FIT_OFF = os.environ.get("FIT_OFF", "0") == "1"


def unpack(x):
    cam = (x[0:3], x[3], x[4], x[5], x[6]); heads = {}; offs = {}
    for i, k in enumerate(ORDER):
        o = 7 + 6 * i; heads[k] = (x[o:o + 3], x[o + 3], x[o + 4], x[o + 5])
    if FIT_OFF:
        base = 7 + 6 * len(ORDER)
        for i, k in enumerate(ORDER):
            offs[k] = {n: x[base + 12 * i + 3 * j: base + 12 * i + 3 * j + 3] for j, n in enumerate(OFFN)}
    return cam, heads, offs


def model_pts(k, heads, offs):
    H, psi, th, ph = heads[k]; R = head_R(psi, th, ph)
    return np.array([H + R @ (KP[k][n] - HC[k] + (offs[k][n] if (FIT_OFF and n in offs.get(k, {})) else 0.0)) for n in NAMES])


def residual(x, w_prior=1.0):
    cam, heads, offs = unpack(x); res = []
    for k in ORDER:
        pts = model_pts(k, heads, offs)
        uv, zc = project(pts, cam)
        obs = np.array([OBS[k][n] for n in NAMES], float)
        res.append(((uv - obs) / 6.0).ravel())             # 6px ≒ 1
        res.append(np.minimum(zc - 0.25, 0) * 50)
    # 座っている人としての決まり（弱い拘束）：頭の高さ、窓からの距離、並ぶ間隔、うつむき・かしげの範囲
    Hs = [heads[k][0] for k in ORDER]
    pr = []
    for i, k in enumerate(ORDER):
        H, psi, th, ph = heads[k]
        pr += [(H[2] - 1.20) / 0.05, (H[0] - (-0.02)) / 0.08, (th - math.radians(20)) / math.radians(8), ph / math.radians(10)]
    for a, b in zip(Hs[:-1], Hs[1:]):
        pr += [((b[1] - a[1]) - 0.60) / 0.15]
    C = cam[0]; pr += [(C[2] - 1.0) / 0.10, (cam[4] - 26) / 4, cam[3] / math.radians(2.0), (cam[2] - math.radians(14)) / math.radians(6)]
    # 参考では3人とも斜め横顔：正面の向きとカメラの方向の角度（人物の左側から）
    for k in ORDER:
        H, psi, th, ph = heads[k]
        fwd = np.array([math.sin(psi), -math.cos(psi)]); dc = C[:2] - H[:2]; dc = dc / (np.linalg.norm(dc) + 1e-9)
        ang = math.degrees(math.atan2(fwd[0] * dc[1] - fwd[1] * dc[0], fwd @ dc))      # 反時計回り（人物の左）が正
        pr += [(ang - VIEW[k]) / 10.0 * W_VIEW]
    if FIT_OFF:
        for k in ORDER:
            for n in OFFN: pr += list(offs[k][n] / 0.008)
    res.append(np.array(pr) * w_prior)
    return np.concatenate(res)


def lm(x, iters=300):
    lam = 1e-2; r = residual(x); e = r @ r
    for it in range(iters):
        J = np.zeros((len(r), len(x))); h = 1e-5
        for j in range(len(x)):
            dx = np.zeros_like(x); dx[j] = h; J[:, j] = (residual(x + dx) - r) / h
        A = J.T @ J; g = J.T @ r
        while True:
            step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
            xn = x + step; rn = residual(xn); en = rn @ rn
            if en < e: x, r, e = xn, rn, en; lam = max(lam / 3, 1e-7); break
            lam *= 4
            if lam > 1e8: return x, e
        if np.linalg.norm(step) < 1e-9: break
    return x, e


if __name__ == "__main__":
    out = sys.argv[1]
    best = None
    rng = np.random.default_rng(0)
    for trial in range(24):        # いくつかの初期値から始めて一番よいもの
        x0 = np.array([-0.75 + rng.normal(0, 0.15), -0.25 + rng.normal(0, 0.2), 1.0 + rng.normal(0, 0.06), 0.65 + rng.normal(0, 0.15),
                       0.15 + rng.normal(0, 0.06), 0.0, 30 + rng.normal(0, 5)]
                      + sum([[-0.02, 0.6 * i, 1.20, math.radians(a) + rng.normal(0, 0.2), math.radians(25), 0.0]
                             for i, a in enumerate((-136, -107, -84))], []) + ([0.0] * (12 * len(ORDER)) if FIT_OFF else []))
        x, e = lm(x0)
        if best is None or e < best[1]: best = (x, e)
        print("trial", trial, round(e, 3), flush=True)
    x, e = best; cam, heads, offs = unpack(x)
    print("BEST", round(e, 3))
    C, yaw, pit, roll, f = cam
    print("camera", np.round(C, 3), "yaw", round(math.degrees(yaw), 1), "pitch", round(math.degrees(pit), 1), "roll", round(math.degrees(roll), 1), "lens", round(f, 1))
    res = {"camera": dict(C=list(map(float, C)), yaw=float(yaw), pitch=float(pit), roll=float(roll), lens=float(f)), "heads": {}}
    for k in ORDER:
        H, psi, th, ph = heads[k]; R = head_R(psi, th, ph)
        pts = model_pts(k, heads, offs); uv, _ = project(pts, cam)
        if FIT_OFF: print("  offsets (x=左, y=後ろ, z=上, mm)", {n: np.round(offs[k][n] * 1000, 1).tolist() for n in OFFN})
        errs = np.linalg.norm(uv - np.array([OBS[k][n] for n in NAMES], float), axis=1)
        print(k, "H", np.round(H, 3), "yaw", round(math.degrees(psi), 1), "pitch", round(math.degrees(th), 1), "roll", round(math.degrees(ph), 1),
              "err px", np.round(errs, 1))
        res["heads"][k] = dict(H=list(map(float, H)), R=R.tolist(), psi=float(psi), pitch=float(th), roll=float(ph), hc=list(map(float, HC[k])),
                               uv={n: list(map(float, p)) for n, p in zip(NAMES, uv)})
    json.dump(res, open(out, "w"), indent=1)
    if len(sys.argv) > 2:
        from PIL import Image, ImageDraw
        im = Image.open(os.path.join(HERE, "..", "..", "refimg", "ref_2827_2.jpeg")).convert("RGB"); d = ImageDraw.Draw(im)
        for k in ORDER:
            for n in NAMES:
                ox, oy = OBS[k][n]; px, py = res["heads"][k]["uv"][n]
                d.ellipse([ox - 6, oy - 6, ox + 6, oy + 6], outline=(0, 255, 0), width=3); d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 0, 0))
        im.save(sys.argv[2])
