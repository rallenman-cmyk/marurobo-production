# 人物の形（頭・顔の部品・髪・体・手・靴）を数式で作る。Blenderに依存しない部分
# 座標：人物のローカル座標（実寸のメートル）。正面＝−Y、上＝＋Z、人物の左＝＋X
import math
import numpy as np
from sdf import (Model, ellipsoid, sphere, cone, cone_b, rbox, torus, rot, smin, smax,
                 mesh, project, grad, relax)

# ---------------------------------------------------------------- 頭
HEAD = dict(hs=1.12, width=1.0, eye=1.0, nose=0.85, cheek=1.0, jaw=1.0, chin=1.0, ear=1.0, brow=1.0, neck=1.12,
            cran=1.0, face_len=1.0, eye_x=1.0, eye_z=0.0, mouth_w=1.0, cheek_z=0.0, muzzle=1.0,
            iris=30.0, pupil=12.0, lid_up=30.0, lid_lo=33.0)


def head_frame(P):
    """頭の中の目印（頭の中心からの位置、実寸）"""
    if P.get("loft"):          # 6面図から起こした頭：部品の位置は設計値
        F = P["loft"]["feat"]
        return dict(s=P["hs"], W=1.0, re=0.015, eye=[np.array(e, float) for e in F["eye"]], mouth=np.array(F["mouth"], float),
                    ear=[np.array(e, float) for e in F["ear"]], brow=[np.array(e, float) for e in F["brow"]])
    s = P["hs"]; W = P["width"]; fl = P["face_len"]
    re = 0.0150 * s * P["eye"]
    ey = -0.0705 * s + (re - 0.0150 * s) * 0.55        # 大きな目は少し奥へ（飛び出さないように）
    return dict(
        s=s, W=W, re=re,
        eye=[np.array([sx * 0.0345 * W * s * P["eye_x"], ey, (0.010 + P["eye_z"]) * s]) for sx in (1, -1)],   # 左, 右
        mouth=np.array([0.0, -0.080 * s * (0.6 + 0.4 * P["muzzle"]), (-0.052 * fl - 0.2 * P.get("jaw_fwd", 0.0)) * s]),
        ear=[np.array([sx * 0.081 * W * s * (0.75 + 0.25 * P["cran"]), 0.010 * s, (-0.004 + P.get("ear_z", 0.0)) * s]) for sx in (1, -1)],
        brow=[np.array([sx * 0.034 * W * s * P["eye_x"], -0.080 * s, (0.040 + P["eye_z"] + (P["eye"] - 1) * 0.012) * s]) for sx in (1, -1)],
    )


def head_model(P, hc):
    """頭（首を含む）。hc＝頭の中心（人物座標）。cran＝頭蓋の大きさ、face_len＝顔の下半分の縦の長さ"""
    if P.get("loft"):
        import loft_head
        return loft_head.loft_model(P, hc)
    s = P["hs"]; W = P["width"]; F = head_frame(P); fl = P["face_len"]; cr = P["cran"]
    hc = np.asarray(hc, float)
    def v(x, y, z): return hc + np.array([x * W, y, z]) * s
    def r3(x, y, z): return np.array([x * W, y, z]) * s
    H = {"head": 1.0}
    m = Model()
    m.add(ellipsoid(v(0, 0.010, 0.032 + (cr - 1) * 0.035), r3(0.083 * cr, 0.098 * cr, 0.102 * cr)), "cranium", bones=H)
    m.add(ellipsoid(v(0, -0.026, -0.014 * fl), r3(0.065, 0.057, 0.060 * fl)), "face", k=0.030 * s, bones=H)
    jf = P.get("jaw_fwd", 0.0)          # 下顔（あご・口元）をまとめて前へ（参考の絵は長く前に出たあご）
    m.add(ellipsoid(v(0, -0.034 - jf, -0.056 * fl - 0.3 * jf), r3(0.044 * P["jaw"], 0.047, 0.038 * fl)), "jaw", k=0.026 * s, bones=H)
    cy_ = P.get("chin_y", 0.0)          # あごを前へ（−）
    m.add(ellipsoid(v(0, -0.0735 + cy_ - jf, -0.0785 * fl - 0.3 * jf), r3(0.0200, 0.0130, 0.0150) * P["chin"]), "chin", k=0.016 * s, bones=H)
    ck = P["cheek"]
    for sx in (1, -1):
        m.add(ellipsoid(v(sx * 0.038, -0.060, -0.017 * fl + P["cheek_z"]), r3(0.022, 0.018, 0.018) * ck), "cheek", k=0.022 * s, bones=H)
    m.add(ellipsoid(v(0, -0.071, 0.037 + P["eye_z"]), r3(0.058, 0.016, 0.014) * np.array([1, P["brow"] ** 0.3, 1])), "brow", k=0.012 * s, bones=H)
    nz = P["nose"]
    def nv(x, y, z):  # 鼻は付け根（y=-0.084, z=0.01）を中心に大きさを変える
        b = np.array([0, -0.084, 0.010]); return hc + (b + (np.array([x, y, z]) - b) * nz) * np.array([W, 1, 1]) * s
    if P.get("nose_style") == "anime":   # 小さくとがった鼻（小鼻はほんの少し）
        nd = P.get("nose_drop", 0.0)      # 鼻先を下へ（参考の絵は鼻が下に長い）
        tip = P.get("nose_tip", 1.0)      # 鼻先の丸さ（小さいほどとがる）
        m.add(cone(nv(0, -0.084, 0.016), nv(0, -0.1035, -0.0175 - nd), 0.0050 * s * nz * tip, 0.0062 * s * nz * tip), "nose", k=0.010 * s, bones=H)
        m.add(sphere(nv(0, -0.1015, -0.0200 - nd), 0.0078 * s * nz * tip), "nose", k=0.006 * s, bones=H)
    else:
        m.add(cone(nv(0, -0.086, 0.014), nv(0, -0.101, -0.017), 0.0068 * s * nz, 0.0095 * s * nz), "nose", k=0.010 * s, bones=H)
        m.add(sphere(nv(0, -0.1005, -0.0215), 0.0112 * s * nz), "nose", k=0.006 * s, bones=H)
        for sx in (1, -1):
            m.add(sphere(nv(sx * 0.0108, -0.0925, -0.0255), 0.0078 * s * nz), "nose", k=0.006 * s, bones=H)
    mz = P["muzzle"]
    m.add(ellipsoid(v(0, -0.0755 + (1 - mz) * 0.010 - 0.6 * jf, -0.050 * fl - 0.2 * jf), r3(0.023, 0.011 * mz, 0.015)), "muzzle", k=0.014 * s, bones=H)
    # 耳：薄い楕円体を少し後ろへ傾け、外側にくぼみ（耳の穴の周り）
    for i, sx in enumerate((1, -1)):
        R = rot(-14, 0, -sx * 16)
        c = F["ear"][i] + hc
        er = np.array([0.010, 0.020, 0.030]) * s * P["ear"]
        m.add(ellipsoid(c, er, R), "ear", k=0.005 * s, bones=H)
        m.sub(ellipsoid(c + R @ (np.array([sx * 0.0085, -0.002, -0.004]) * s), np.array([0.006, 0.0115, 0.017]) * s * P["ear"], R), k=0.002 * s)
    # 首（頭の下から胴の中へ）
    nk = P["neck"]
    m.add(cone(hc + np.array([0, 0.026, -0.048]), hc + np.array([0, 0.036, -0.205]), 0.048 * nk, 0.055 * nk), "neck", k=0.012 * s,
          bones={"neck": 1.0})
    # 目のくぼみ（眼球がはまる）
    if P.get("socket", True):
        for e in F["eye"]:
            m.sub(sphere(hc + e, F["re"] + 0.0006), k=0.004 * s)
    return m


def head_mesh(P, hc, h=0.0022):
    m = head_model(P, hc); s = P["hs"]
    lo = np.asarray(hc) + np.array([-0.12, -0.15, -0.24]) * s; hi = np.asarray(hc) + np.array([0.12, 0.13, 0.16]) * s
    V, Q = mesh(m, lo, hi, h)
    return m, V, Q


# ---------------------------------------------------------------- 髪
# style: short（横は短く上は長め、前髪は横へ流す）/ crop（全体に短い）/ bob（耳を覆う）
HAIR = dict(style="short", thick=1.0, front=0.52, back=-0.50, side=0.15, clumps=13, groove=0.30, tip=0.10,
            crown=(0.20, 0.45, 0.87), swirl=0.55, sweep=-0.45, sweep_drop=0.20, part=0.0, top=0.020, sides=0.0030, seed=1)


def _dirs(p, hc):
    u = p - hc; r = np.sqrt((u * u).sum(1)) + 1e-12; u = u / r[:, None]
    el = np.arcsin(np.clip(u[:, 2], -1, 1)); az = np.arctan2(u[:, 0], -u[:, 1])
    return u, el, az


def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def hair_frame(HP):
    cr = np.asarray(HP["crown"], float); cr = cr / np.linalg.norm(cr)
    e1 = np.cross(cr, [1.0, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(cr, e1)
    return cr, e1, e2


def hair_fields(HP, s):
    """髪の厚み T(方向) と「流れ」の角度（つむじから渦を巻いて放射状）"""
    cr, e1, e2 = hair_frame(HP)
    f, sd, b = HP["front"], HP["side"], HP["back"]
    a1 = (f - b) / 2; a0 = ((f + b) / 2 + sd) / 2; a2 = (f + b) / 2 - a0
    rng = np.random.default_rng(HP["seed"]); ph = rng.uniform(0, 2 * math.pi, 3)
    n = HP["clumps"]

    def flow(u):
        ang = np.arccos(np.clip(u @ cr, -1, 1))
        return np.arctan2(u @ e2, u @ e1) + HP["swirl"] * ang, ang

    def wave_of(phi):  # 毛束：間隔と深さを少し不ぞろいに
        q = n * phi + 1.1 * np.sin(3 * phi + ph[0]) + 0.6 * np.sin(5 * phi + ph[1]) + HP["part"]
        depth = 0.75 + 0.25 * np.sin(2 * phi + ph[2])
        return 0.5 + 0.5 * np.cos(q), depth

    def hairline(az, phi):
        hl = a0 + a1 * np.cos(az) + a2 * np.cos(2 * az)
        if HP["style"] in ("short", "crop"):
            hl = hl + 0.30 * np.exp(-((np.abs(az) - math.radians(96)) / math.radians(24)) ** 2)  # 耳の周りを刈り上げ
        if HP["style"] == "bob":
            hl = hl - 0.62 * np.exp(-((np.abs(az) - math.radians(105)) / math.radians(60)) ** 2)  # 横は耳を覆う
        hl = hl - HP["sweep_drop"] * np.exp(-((az - HP["sweep"]) / 0.55) ** 2)            # 前髪が片側へ下りる
        wv, _ = wave_of(phi)
        front = np.exp(-(az / math.radians(80)) ** 2)
        return hl + HP["tip"] * (1 - wv) ** 1.5 * front * (1 if HP["style"] != "crop" else 0.3)

    def T(u, el, az):
        phi, ang = flow(u)
        hl = hairline(az, phi)
        top, sides = HP["top"] * s, HP["sides"] * s
        base = (sides + (top - sides) * _ss(0.0, 1.0, el) * (0.75 + 0.25 * np.cos(az))) * HP["thick"]
        if HP["style"] == "bob":
            base = base + 0.011 * s * np.exp(-((np.abs(az) - math.radians(105)) / math.radians(55)) ** 2) * _ss(-1.0, 0.1, el)
        if HP["style"] == "crop": base = base * 0.45
        wv, depth = wave_of(phi)
        g = HP["groove"] * depth * _ss(0.15, 0.70, ang)
        th = base * (1.0 - g * (1 - wv) ** 1.5)
        w = _ss(0.0, 0.16, el - hl)
        return -0.0012 + (th + 0.0012) * w, el - hl, phi
    return T


def hair_mesh(head_m, HP, hc, s, h=0.0022):
    T = hair_fields(HP, s)
    hc = np.asarray(hc, float)

    def F(p):
        u, el, az = _dirs(p, hc)
        t, rel, _ = T(u, el, az)
        return np.maximum(head_m(p) - t, (-rel - 0.07) * 0.05)
    lo = hc + np.array([-0.13, -0.15, -0.21]) * s; hi = hc + np.array([0.13, 0.14, 0.17]) * s
    V, Q = mesh(F, lo, hi, h)
    u, el, az = _dirs(V, hc); _, rel, phi = T(u, el, az)
    keep_f = (rel[Q].max(1) > -0.069)
    return F, V, Q[keep_f], phi


# ---------------------------------------------------------------- 目・まぶた・眉・口
def uv_sphere(r, nu=32, nv=20):
    V = [(0, 0, r), (0, 0, -r)]
    for i in range(1, nv):
        th = math.pi * i / nv
        for j in range(nu):
            ph = 2 * math.pi * j / nu
            V.append((r * math.sin(th) * math.cos(ph), r * math.sin(th) * math.sin(ph), r * math.cos(th)))
    F = []
    def idx(i, j): return 2 + (i - 1) * nu + (j % nu)
    for j in range(nu):
        F.append((0, idx(1, j), idx(1, j + 1)))
        F.append((1, idx(nv - 1, j + 1), idx(nv - 1, j)))
    for i in range(1, nv - 1):
        for j in range(nu):
            F.append((idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)))
    return np.array(V), F


def eyeball(center, r):
    """眼球。前＝−Y。'dir' は眼球の中心から見た向き（色分けに使う）"""
    V, F = uv_sphere(r, 40, 28)
    d = V / r
    return V + center, F, d


def lid_shell(center, re, upper=True, a_rest=24.0, span=78.0, tilt=0.0, thick=0.0017, gap=0.0005, extra=0):
    """まぶた：眼球を包む殻の一部。縁（まつげの線）は丸く。X軸まわりに回すと開閉する"""
    sgn = 1.0 if upper else -1.0
    na, nb = 22, 34
    alphas = np.linspace(0.0, math.radians(135 if upper else 120), na)
    betas = np.linspace(-math.radians(span), math.radians(span), nb)
    r_in, r_out = re + gap, re + gap + thick
    rows = []
    # 縁の丸み：内側→外側を半円でつなぐ
    rim = []
    for k in range(7):
        t = math.pi * k / 6.0
        rr = 0.5 * (r_in + r_out) - 0.5 * (r_out - r_in) * math.cos(t)
        da = -math.sin(t) * (thick * 0.55) / re
        rim.append((rr, da))
    prof = [(r_in, a) for a in alphas[::-1]] + [(rr, da) for (rr, da) in rim] + [(r_out, a) for a in alphas]
    V = []
    for (rr, a) in prof:
        for b in betas:
            d = np.array([math.sin(b), -math.cos(b) * math.cos(a), sgn * math.cos(b) * math.sin(a)])
            V.append(d * rr)
    V = np.array(V)
    R = rot(-sgn * a_rest, tilt, 0.0)  # 開いた状態（休みの姿勢）。上まぶたは上へ、下まぶたは下へ
    V = V @ R.T
    nr = len(prof); F = []
    for i in range(nr - 1):
        for j in range(nb - 1):
            a, b_, c, d = i * nb + j, i * nb + j + 1, (i + 1) * nb + j + 1, (i + 1) * nb + j
            F.append((a, b_, c, d) if upper else (a, d, c, b_))
    # 縁（まつげの線）の面
    i0 = len(alphas) - 3; i1 = len(alphas) + len(rim) + 1 + extra
    margin = [((i >= i0) and (i < i1)) for i in range(nr - 1) for _ in range(nb - 1)]
    return V + center, F, margin


def tube_along(points, normals, half_w, half_t, nseg=10):
    """曲線に沿った平たい管（眉など）。normals＝肌の向き"""
    P = np.asarray(points); N = np.asarray(normals)
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    B = np.cross(N, T); B /= np.linalg.norm(B, axis=1, keepdims=True)
    V = []
    for i in range(len(P)):
        for j in range(nseg):
            a = 2 * math.pi * j / nseg
            V.append(P[i] + B[i] * half_w[i] * math.cos(a) + N[i] * half_t[i] * math.sin(a))
    V.append(P[0] - T[0] * 0.0005); V.append(P[-1] + T[-1] * 0.0005)
    F = []
    n = len(P)
    for i in range(n - 1):
        for j in range(nseg):
            F.append((i * nseg + j, i * nseg + (j + 1) % nseg, (i + 1) * nseg + (j + 1) % nseg, (i + 1) * nseg + j))
    c0, c1 = n * nseg, n * nseg + 1
    for j in range(nseg):
        F.append((c0, (j + 1) % nseg, j)); F.append((c1, (n - 1) * nseg + j, (n - 1) * nseg + (j + 1) % nseg))
    return np.array(V), F


def surface_hit(Fm, origins, dirs, tmax=0.12, iters=40):
    """origins から dirs 方向へ進み、最初に面に当たる点（外側から）"""
    lo = np.zeros(len(origins)); hi = np.full(len(origins), tmax)
    # 粗く進んで最初の内側を探す
    ts = np.linspace(0, tmax, 160)
    first = np.full(len(origins), tmax)
    for t in ts[::-1]:
        inside = Fm(origins + dirs * t) < 0
        first = np.where(inside, t, first)
    hi = first; lo = np.maximum(first - tmax / 159, 0)
    for _ in range(iters):
        mid = 0.5 * (lo + hi); ins = Fm(origins + dirs * mid[:, None]) < 0
        hi = np.where(ins, mid, hi); lo = np.where(ins, lo, mid)
    return origins + dirs * hi[:, None]


def onto_face(Fm, hc, uv, y_front, offset):
    """顔の前（y_front）から後ろ（+Y）へ光線を飛ばし、顔の面に貼る"""
    uv = np.asarray(uv, float)
    O = np.stack([hc[0] + uv[:, 0], np.full(len(uv), hc[1] + y_front), hc[2] + uv[:, 1]], 1)
    D = np.tile([0.0, 1.0, 0.0], (len(uv), 1))
    P = surface_hit(Fm, O, D, tmax=abs(y_front) + 0.05)
    g = grad(Fm, P, 0.0004); g /= np.linalg.norm(g, axis=1, keepdims=True)
    return P + g * offset, g


def brows(Fm, hc, P, s, raise_=0.0):
    out = []
    BL = P["loft"]["feat"]["brow_line"] if P.get("loft") else None
    if BL:
        for sx in (1, -1):
            t = np.linspace(0, 1, 18)
            u = sx * (BL["inner"][0] + (BL["outer"][0] - BL["inner"][0]) * t)
            v = BL["inner"][1] + (BL["outer"][1] - BL["inner"][1]) * t + BL.get("arch", 0.0) * np.sin(np.pi * t) + raise_
            pts, nrm = onto_face(Fm, np.asarray(hc), np.stack([u, v], 1), -0.30, 0.00045)
            hw = (BL["t_in"] + (BL["t_out"] - BL["t_in"]) * t) / 2 * (1 - 0.35 * t ** 6)
            V, F = tube_along(pts, nrm, hw, np.full_like(t, 0.00040), 10)
            out.append((V, F))
        return out
    for sx in (1, -1):
        t = np.linspace(0, 1, 18)
        u = sx * (0.011 + 0.043 * t) * P["width"] * s
        v = (0.031 + 0.012 * P.get("brow_arch", 1.0) * np.sin(math.pi * (t * 0.85 + 0.05)) - 0.004 * t + raise_) * s
        flat = P.get("brow_flat", False)      # 描いたような平たい眉（横から見ても浮かない）
        pts, nrm = onto_face(Fm, np.asarray(hc), np.stack([u, v], 1), -0.16 * s, (0.00045 if flat else 0.0009) * s)
        hw = (0.0040 - 0.0022 * t ** 1.4) * s * P["brow"]
        ht = (np.full_like(t, 0.00040) if flat else (0.0013 - 0.0004 * t)) * s
        V, F = tube_along(pts, nrm, hw, ht, 10)
        out.append((V, F))
    return out


MOUTH_SHAPES = {
    #        幅   高さ  反り（口角の上がり）  中心の上下
    "rest": (0.0150, 0.00075, 0.0026, 0.0),
    "o":    (0.0072, 0.0072, 0.0004, -0.0012),
    "open": (0.0125, 0.0068, 0.0010, -0.0015),
    "flat": (0.0135, 0.00070, 0.0000, 0.0),
    "smile": (0.0185, 0.0016, 0.0042, 0.0005),
}


def mouth_disc(nr=5, ns=36):
    """口：楕円の円盤（形ごとに縦横・反りを変えてシェイプキーにする）"""
    pts = [(0.0, 0.0)]
    for i in range(1, nr + 1):
        rr = i / nr
        for j in range(ns):
            a = 2 * math.pi * j / ns
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    F = []
    for j in range(ns): F.append((0, 1 + j, 1 + (j + 1) % ns))
    for i in range(1, nr):
        for j in range(ns):
            a = 1 + (i - 1) * ns + j; b = 1 + (i - 1) * ns + (j + 1) % ns
            F.append((a, a + ns, b + ns, b))
    return np.array(pts), F


def mouth_shapes(Fm, hc, P, s, names=("rest", "o", "open", "flat", "smile")):
    D, F = mouth_disc()
    fr = head_frame(P); mc = fr["mouth"]
    out = {}
    ML = P["loft"]["feat"]["mouth_line"] if P.get("loft") else None
    for nm in names:
        w, hgt, curve, dz = MOUTH_SHAPES[nm]
        if ML:
            u = D[:, 0] * ML["hw"] * (w / 0.0150)
            vv = D[:, 1] * hgt * 1.3 + ML["sag"] * (curve / 0.0026) * (D[:, 0] ** 2) + dz
            V, _ = onto_face(Fm, np.asarray(hc), np.stack([u, vv + ML["z_mid"]], 1), -0.30, 0.00035)
            out[nm] = V; continue
        u = D[:, 0] * w * s * P.get("mouth_w", 1.0)
        vv = D[:, 1] * hgt * s * P.get("mouth_h", 1.0) + curve * s * (D[:, 0] ** 2) + dz * s
        V, _ = onto_face(Fm, np.asarray(hc), np.stack([u, vv + mc[2]], 1), -0.16 * s, 0.00035 * s)
        out[nm] = V
    return out, F


# ---------------------------------------------------------------- 骨格（座った姿勢が基本の形）
BODY = dict(shoulder=0.180, hip=1.0, waist=1.0, chest=1.0, belly=1.0, arm=1.0, thigh=1.0, finger=1.0, finger_r=1.0, palm=1.0)


def norm(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)


def skeleton(B):
    """座った休みの姿勢の関節位置（実寸）。座面の高さ0.46m、背もたれは y=+0.197"""
    J = {}
    J["pelvis"] = np.array([0, 0.065, 0.575]); J["spine"] = np.array([0, 0.075, 0.690])
    J["chest"] = np.array([0, 0.085, 0.820]); J["neck"] = np.array([0, 0.070, 1.065])
    J["head"] = np.array([0, 0.045, 1.190]); J["head_top"] = np.array([0, 0.045, 1.420])
    J["head_center"] = np.array([0, 0.040, 1.228])
    for sd, sx in (("L", 1), ("R", -1)):
        J["clav." + sd] = np.array([sx * 0.025, 0.040, 1.035])
        sh = np.array([sx * B["shoulder"], 0.070, 1.045]); J["shoulder." + sd] = sh
        el = sh + 0.280 * norm((sx * 0.55, -0.20, -0.81)); J["elbow." + sd] = el
        J["wrist." + sd] = el + 0.250 * norm((sx * 0.20, -0.80, -0.40))
        J["hip." + sd] = np.array([sx * 0.088, 0.045, 0.530])
        J["knee." + sd] = np.array([sx * 0.130, -0.355, 0.500])
        an = np.array([sx * 0.140, -0.385, 0.085]); J["ankle." + sd] = an
        J["ball." + sd] = an + np.array([sx * 0.012, -0.135, -0.058])
        J["toe." + sd] = an + np.array([sx * 0.016, -0.205, -0.062])
    return J


HEM_P0 = np.array([0, 0.06, 0.605]); HEM_N = norm((0, -0.2, 1.0))


def body_model(B, J, part="all"):
    """服を着た胴・腕・脚。part: all（全部）/ top（ニット＝胴と袖）/ bottom（ズボン＝腰と脚）"""
    m = Model(); T = "torso"
    pelvis = ellipsoid((0, 0.075, 0.575), (0.160 * B["hip"], 0.128, 0.105))
    belly = ellipsoid((0, 0.058, 0.700), (0.143 * B["waist"], 0.108 * B["belly"], 0.120))
    def plane(p): return (p - HEM_P0) @ HEM_N
    if part == "bottom":
        # ズボンの腰：裾の線より上は切り、ニットの裾の下では1.5mm内側へ（ニットの下に隠れる）
        def pel(p):
            pl = plane(p); t = np.clip((pl + 0.020) / 0.0075, 0, 1)
            return smax(pelvis(p) + 0.0015 * t * t * (3 - 2 * t), pl - 0.010, 0.002)
        m.add(pel, "pelvis", bones={"hips": 1}, group=T)
    else:
        m.add(pelvis, "pelvis", bones={"hips": 1}, group=T)
    if part in ("all", "top"):
        m.add(belly, "belly", k=0.045, bones={"spine": 1}, group=T)
        m.add(ellipsoid((0, 0.080, 0.875), (0.172 * B["chest"], 0.120, 0.165)), "chest", k=0.050, bones={"chest": 1}, group=T)
        m.add(ellipsoid((0, 0.086, 1.000), (0.152 * B["chest"], 0.088, 0.078)), "upper_chest", k=0.040, bones={"chest": 1}, group=T)
        for sd, sx in (("L", 1), ("R", -1)):
            m.add(cone((sx * 0.04, 0.088, 1.062), (sx * (B["shoulder"] - 0.03), 0.076, 1.056), 0.044, 0.046), "traps", k=0.030,
                  bones={"chest": 0.5, "clav." + sd: 0.5}, group=T)
        # 裾のリブ（胴の面から3.5mm外へ、幅2.2cmの帯）
        def hem(p):
            core = smin(pelvis(p), belly(p), 0.045)
            return np.maximum(core - 0.0035, np.abs(plane(p)) - 0.011)
        m.add(hem, "hem", k=0.002, bones={"hips": 0.5, "spine": 0.5}, group=T)
        # 襟（首の付け根の輪）。6面図の人は襟を別に作る（タートルネック・シャツの襟）ので付けない
        if B.get("collar", 1):
            nax = norm(J["head"] - J["neck"]); ctr = J["neck"] + nax * 0.022
            m.add(torus(ctr, np.stack([norm(np.cross([0, 1, 0], nax)), norm(np.cross(nax, np.cross([0, 1, 0], nax))), nax], 1), 0.066, 0.0135),
                  "collar", k=0.006, bones={"chest": 0.7, "neck": 0.3}, group=T)
        for sd, sx in (("L", 1), ("R", -1)):
            A = "arm." + sd; ar = B["arm"]
            sh, el, wr = J["shoulder." + sd], J["elbow." + sd], J["wrist." + sd]
            fd = norm(wr - el)
            m.add(sphere(sh, 0.052 * ar), "shoulder", k=0.030, bones={"upper_arm." + sd: 0.6, "clav." + sd: 0.4}, group=A)
            m.add(cone(sh, el, 0.050 * ar, 0.041 * ar), "upper_arm", k=0.020, bones={"upper_arm." + sd: 1}, group=A)
            m.add(cone(el, wr + fd * 0.004, 0.041 * ar, 0.035 * ar), "forearm", k=0.015, bones={"forearm." + sd: 1}, group=A)
            m.add(cone(wr - fd * 0.030, wr + fd * 0.008, 0.0385 * ar, 0.0375 * ar), "cuff", k=0.004, bones={"forearm." + sd: 1}, group=A)
            m.sub(cone(wr + fd * 0.000, wr + fd * 0.05, 0.0215 * ar, 0.0215 * ar), k=0.002)   # 袖口の穴（手首が入る。浅く小さく）
    if part in ("all", "bottom"):
        for sd, sx in (("L", 1), ("R", -1)):
            Lg = "leg." + sd; th = B["thigh"]
            hp, kn, an = J["hip." + sd], J["knee." + sd], J["ankle." + sd]
            m.add(cone(hp, kn, 0.082 * th, 0.060 * th), "thigh", k=0.030, bones={"thigh." + sd: 1}, group=Lg)
            m.add(sphere(kn, 0.060 * th), "knee", k=0.020, bones={"thigh." + sd: 0.5, "shin." + sd: 0.5}, group=Lg)
            m.add(cone(kn, an + np.array([0, 0, 0.012]), 0.057, 0.050), "shin", k=0.015, bones={"shin." + sd: 1}, group=Lg)
    return m


BODY_NEIGHBORS = [("torso", "arm.L"), ("torso", "arm.R"), ("torso", "leg.L"), ("torso", "leg.R")]
RIB = {"hem", "cuff", "collar"}
PANTS = {"thigh", "knee", "shin"}


def body_mesh(B, J, h=0.0055):
    """ニット（胴・袖）とズボン（腰・脚）を別々の網目にする：裾の縁がまっすぐな線になる"""
    mt = body_model(B, J, "top"); mb = body_model(B, J, "bottom")
    def Fs(p): return smax(mt(p), -((p - HEM_P0) @ HEM_N + 0.0125), 0.002)
    Vs, Qs = mesh(Fs, np.array([-0.46, -0.48, 0.45]), np.array([0.46, 0.27, 1.13]), h)
    C = Vs[Qs].mean(1); D = mt.dists(C)
    mat = np.array([1 if mt.prims[i]["label"] in RIB else 0 for i in D.argmin(1)])
    Vp, Qp = mesh(mb, np.array([-0.46, -0.48, 0.03]), np.array([0.46, 0.27, 0.70]), h)
    return mt, mb, (Vs, Qs, mat), (Vp, Qp)


# ---------------------------------------------------------------- 手（右手の形を作り、左は鏡写し）
FINGERS = {  # 付け根(x, y)、開き角（度）、3節の長さ、付け根の太さ（半径）
    "index": (-0.0255, 0.094, 12.0, (0.040, 0.025, 0.019), 0.0094),
    "middle": (-0.0080, 0.098, 2.0, (0.044, 0.028, 0.020), 0.0098),
    "ring": (0.0095, 0.095, -8.0, (0.041, 0.027, 0.019), 0.0093),
    "pinky": (0.0260, 0.087, -17.0, (0.032, 0.021, 0.017), 0.0082),
}
REST_CURL = (12.0, 20.0, 12.0)


def _chain(base, d, z, lengths, curls):
    pts = [np.asarray(base, float)]; zs = []; ds = []
    d = norm(d); z = norm(z - (z @ d) * d)
    for L, c in zip(lengths, curls):
        th = math.radians(c)
        d, z = d * math.cos(th) - z * math.sin(th), z * math.cos(th) + d * math.sin(th)
        ds.append(d.copy()); zs.append(z.copy()); pts.append(pts[-1] + d * L)
    return pts, ds, zs


def hand_local(B):
    """右手（手首が原点、+Y 指先方向、+Z 手の甲、親指は −X）"""
    k = B["finger"]
    chains = {}
    for nm, (x, y, sp, L, r) in FINGERS.items():
        a = math.radians(sp)
        pts, ds, zs = _chain((x, y, 0.001), (-math.sin(a), math.cos(a), 0), np.array([0, 0, 1.0]), [l * k for l in L], REST_CURL)
        chains[nm] = dict(pts=pts, z=zs, r=r * k * B.get("finger_r", 1.0))
    pts, ds, zs = _chain((-0.019, 0.016, -0.006), (-0.62, 0.72, -0.30), np.array([-0.35, -0.15, 0.92]),
                         [0.040 * k, 0.031 * k, 0.025 * k], (8.0, 14.0, 12.0))
    chains["thumb"] = dict(pts=pts, z=zs, r=0.0122 * k * B.get("finger_r", 1.0))
    m = Model()
    for nm, ch in chains.items():
        p, r = ch["pts"], ch["r"]; radii = [r, r * 0.94, r * 0.88, r * 0.80]
        for i in range(3):
            tip = p[i + 1] - (p[i + 1] - p[i]) / np.linalg.norm(p[i + 1] - p[i]) * (radii[i + 1] * 0.8 if i == 2 else 0)
            m.add(cone_b(p[i], tip, radii[i], radii[i + 1], 0.012), nm, k=(0.0 if i == 0 else 0.0025),
                  bones={f"{nm}_{i + 1:02d}": 1.0}, group=nm)
    pk = B.get("palm", 1.0)
    m.add(rbox((0.000, 0.050, 0.000), (0.037 * pk, 0.046, 0.0125 * pk), 0.011 * pk), "palm", k=0.008, bones={"hand": 1}, group="palm")
    m.add(cone((0, -0.035, 0.0), (0, 0.006, 0.0), 0.0225, 0.0245), "wrist", k=0.012, bones={"forearm": 0.65, "hand": 0.35}, group="palm")
    m.add(ellipsoid((-0.022, 0.032, -0.009), (0.016, 0.026, 0.012)), "thenar", k=0.010, bones={"hand": 0.5, "thumb_01": 0.5}, group="palm")
    m.add(ellipsoid((0.025, 0.040, -0.006), (0.012, 0.030, 0.010)), "hypothenar", k=0.008, bones={"hand": 1}, group="palm")
    return m, chains


HAND_NEIGHBORS = [("palm", f) for f in ("thumb", "index", "middle", "ring", "pinky")]


class Placed:
    """局所座標で作った形を、人物座標に置く（左手は鏡写し）"""
    def __init__(self, model, origin, R, mirror=False):
        self.m = model; self.o = np.asarray(origin, float); self.R = np.asarray(R, float)
        self.s = np.array([-1.0 if mirror else 1.0, 1.0, 1.0]); self.prims = model.prims
    def loc(self, p): return ((p - self.o) @ self.R) * self.s
    def to_char(self, q): return self.o + (np.asarray(q) * self.s) @ self.R.T
    def __call__(self, p): return self.m(self.loc(p))
    def dists(self, p): return self.m.dists(self.loc(p))


def hand_frame(J, sd, sx):
    el, wr = J["elbow." + sd], J["wrist." + sd]
    Y = norm(wr - el); lat = np.array([sx, 0.0, 0.0])
    Z = norm(lat - (lat @ Y) * Y); X = np.cross(Y, Z)
    return wr, np.stack([X, Y, Z], 1)


def hand_mesh(B, J, sd, sx, h=0.0011):
    m, chains = hand_local(B)
    o, R = hand_frame(J, sd, sx)
    P = Placed(m, o, R, mirror=(sd == "L"))
    c = o + R[:, 1] * 0.08
    V, Q = mesh(P, c - 0.135, c + 0.135, h)
    # 関節位置を人物座標へ
    out = {}
    for nm, ch in chains.items():
        out[nm] = dict(pts=[P.to_char(p) for p in ch["pts"]], z=[norm(P.to_char(z) - P.to_char(np.zeros(3))) for z in ch["z"]])
    mcp_mid = P.to_char(np.array([-0.008, 0.098, 0.0])); dorsal = R[:, 2]
    return P, V, Q, dict(chains=out, mcp_mid=mcp_mid, dorsal=dorsal)


# ---------------------------------------------------------------- 靴
def shoe_model(J, sd):
    an, ball = J["ankle." + sd], J["ball." + sd]
    fwd = norm((ball - an) * np.array([1, 1, 0])); up = np.array([0, 0, 1.0]); lat = np.cross(fwd, up)
    R = np.stack([lat, fwd, up], 1)
    def at(f, l, u): return an + fwd * f + lat * l + up * u
    F = {"foot." + sd: 1.0}
    m = Model()
    m.add(rbox(at(0.062, 0, -0.0725), (0.047, 0.137, 0.0125), 0.010, R), "sole", bones=F)
    m.add(ellipsoid(at(0.138, 0, -0.050), (0.041, 0.068, 0.030), R), "upper", k=0.020, bones=F)
    m.add(ellipsoid(at(0.058, 0, -0.036), (0.045, 0.090, 0.044), R), "upper", k=0.020, bones=F)
    m.add(ellipsoid(at(-0.030, 0, -0.030), (0.041, 0.048, 0.050), R), "upper", k=0.020, bones=F)
    m.add(cone(at(-0.008, 0, -0.030), at(-0.008, 0, 0.026), 0.043, 0.041), "upper", k=0.015, bones=F)
    m.sub(cone(at(-0.008, 0, 0.004), at(-0.008, 0, 0.07), 0.033, 0.033), k=0.004)
    return m


def shoe_mesh(J, sd, h=0.0028):
    m = shoe_model(J, sd); an = J["ankle." + sd]
    V, Q = mesh(m, an + np.array([-0.08, -0.25, -0.09]), an + np.array([0.08, 0.10, 0.05]), h)
    C = V[Q].mean(1); D = m.dists(C)
    mat = np.array([0 if m.prims[i]["label"] == "upper" else 1 for i in D.argmin(1)])
    return m, V, Q, mat


# ---------------------------------------------------------------- イヤホン
def earbud_model(hf, hc, i, sx, s):
    c = np.asarray(hc) + hf["ear"][i]
    R = rot(-14, 0, -sx * 16)
    bud = c + R @ (np.array([sx * 0.0125, -0.003, -0.005]) * s)
    stem_dir = norm((0, -0.28, -0.96))
    m = Model()
    m.add(ellipsoid(bud, np.array([0.0072, 0.0085, 0.0082]) * s, R), "bud")
    m.add(cone(bud + stem_dir * 0.004 * s + np.array([sx * 0.002, 0, 0]), bud + stem_dir * 0.030 * s + np.array([sx * 0.003, 0, 0]), 0.0034 * s, 0.0031 * s), "stem", k=0.004 * s)
    return m, bud


def earbud_mesh(hf, hc, i, sx, s, h=0.0006):
    m, bud = earbud_model(hf, hc, i, sx, s)
    V, Q = mesh(m, bud - 0.045 * s, bud + 0.025 * s, h)
    return V, Q


# ---------------------------------------------------------------- 骨の一覧
def bone_list(J, eyes, brows, hands, hair=None):
    Bl = []
    def add(name, h, t, parent, z):
        Bl.append(dict(name=name, head=tuple(np.asarray(h, float)), tail=tuple(np.asarray(t, float)), parent=parent, z=tuple(np.asarray(z, float))))
    Fw = (0, -1.0, 0); U = (0, 0, 1.0)
    add("hips", J["pelvis"], J["spine"], None, Fw)
    add("spine", J["spine"], J["chest"], "hips", Fw)
    add("chest", J["chest"], J["neck"], "spine", Fw)
    add("neck", J["neck"], J["head"], "chest", Fw)
    add("head", J["head"], J["head_top"], "neck", Fw)
    if hair is not None: add("hair", hair[0], hair[1], "head", (0, 0, 1.0))      # 髪の揺れ（遅れて追いかける）
    for i, sd in enumerate(("L", "R")):
        e = eyes[i]
        for nm in ("eye", "lid_up", "lid_lo"): add(f"{nm}.{sd}", e, e + np.array([0, -0.02, 0]), "head", U)
        b = brows[i]; add("brow." + sd, b, b + np.array([0, 0, 0.015]), "head", Fw)
        add("clav." + sd, J["clav." + sd], J["shoulder." + sd], "chest", U)
        add("upper_arm." + sd, J["shoulder." + sd], J["elbow." + sd], "clav." + sd, Fw)
        add("forearm." + sd, J["elbow." + sd], J["wrist." + sd], "upper_arm." + sd, U)
        hd = hands[sd]
        add("hand." + sd, J["wrist." + sd], hd["mcp_mid"], "forearm." + sd, hd["dorsal"])
        for fname, ch in hd["chains"].items():
            parent = "hand." + sd
            for k in range(3):
                nm = f"{fname}_{k + 1:02d}.{sd}"
                add(nm, ch["pts"][k], ch["pts"][k + 1], parent, ch["z"][k]); parent = nm
        add("thigh." + sd, J["hip." + sd], J["knee." + sd], "hips", U)
        add("shin." + sd, J["knee." + sd], J["ankle." + sd], "thigh." + sd, Fw)
        add("foot." + sd, J["ankle." + sd], J["ball." + sd], "shin." + sd, U)
    return Bl


# ---------------------------------------------------------------- 髪（毛束を並べる型：アニメらしいかたまり）
def slerp_dir(a, b, t):
    a = norm(a); b = norm(b); w = math.acos(max(-1.0, min(1.0, float(a @ b))))
    if w < 1e-6: return a
    return (math.sin((1 - t) * w) * a + math.sin(t * w) * b) / math.sin(w)


def surf_radius(head_m, hc, u, rmax=0.25):
    """頭の中心から方向 u に進んだとき、頭の面までの距離"""
    lo = np.zeros(len(u)); hi = np.full(len(u), rmax)
    for _ in range(36):
        mid = 0.5 * (lo + hi); ins = head_m(hc + u * mid[:, None]) < 0
        lo = np.where(ins, mid, lo); hi = np.where(ins, hi, mid)
    return 0.5 * (lo + hi)


def dir_from(az, el):
    return np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])


LOCKS_DEFAULT = dict(
    # (向き az°, 高さ el°, 太さ倍率, 曲げ°)  az：0＝正面、＋＝人物の左
    front=[(-52, 20, 1.0, -18), (-30, 22, 1.1, -16), (-8, 24, 1.15, -14), (14, 25, 1.05, -12), (34, 22, 0.9, -10)],
    side=[(60, 14, 0.95, 0), (88, 12, 0.85, 0), (-64, 10, 0.95, 0), (-92, 10, 0.85, 0), (118, 0, 0.95, 0), (-120, 0, 0.95, 0)],
    back=[(150, -22, 1.0, 0), (180, -28, 1.05, 0), (-150, -22, 1.0, 0)],
)


def locks_model(head_m, HP, hc, s, P):
    hc = np.asarray(hc, float); cr = norm(HP["crown"]); R0 = HP.get("lock_r", 0.0145) * s
    m = Model()
    # 地肌を覆う薄い層（毛束の根元のすき間を埋める）
    T = hair_fields(dict(HP, groove=0.0, tip=0.0, top=HP.get("cap", 0.007), sides=HP.get("cap_side", 0.004), style="short"), s)
    def cap(p):
        u, el, az = _dirs(p, hc); t, rel, _ = T(u, el, az)
        return np.maximum(head_m(p) - t, (-rel - 0.07) * 0.05)
    m.add(cap, "cap", bones={"head": 1.0})
    rng = np.random.default_rng(HP.get("seed", 1))
    L = HP.get("locks", LOCKS_DEFAULT)
    kk = HP.get("lock_k", 0.010) * s
    for grp in ("front", "side", "back"):
        for (az, el, rk, bend) in L[grp]:
            end = dir_from(math.radians(az), math.radians(el))
            start = norm(cr + rng.normal(0, 0.035, 3))
            n = 12; ts = np.linspace(0, 1, n)
            dirs = []
            for t in ts:
                d = slerp_dir(start, end, t)
                ang = math.radians(bend) * t * t                     # 毛先ほど横へ流す（放射方向まわりの回転）
                axis = d
                d = norm(d * math.cos(ang) + np.cross(axis, d) * math.sin(ang) + axis * (axis @ d) * (1 - math.cos(ang)))
                dirs.append(d)
            dirs = np.array(dirs); rs = surf_radius(head_m, hc, dirs)
            rr = R0 * rk * (0.85 + 0.25 * np.sin(np.pi * ts)) * (1 - ts ** 3) ** 0.8 + 0.0015 * s   # なめらかに細る
            pts = hc + dirs * (rs + rr * 0.50)[:, None]
            for j in range(n - 1):
                m.add(cone_b(pts[j], pts[j + 1], rr[j], rr[j + 1], 0.02 * s), "lock_" + grp, k=(kk if j == 0 else 0.6 * kk), bones={"head": 1.0})
    return m


def hair_locks_mesh(head_m, HP, hc, s, P, h=0.0022):
    m = locks_model(head_m, HP, hc, s, P)
    hc = np.asarray(hc, float)
    lo = hc + np.array([-0.15, -0.17, -0.20]) * s; hi = hc + np.array([0.15, 0.16, 0.19]) * s
    V, Q = mesh(m, lo, hi, max(h, 0.0028), relax_iters=2)
    return m, V, Q
