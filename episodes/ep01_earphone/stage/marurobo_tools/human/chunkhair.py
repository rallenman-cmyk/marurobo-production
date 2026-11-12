# 参考画像の髪：大きなかたまりを「平面で削って」作る（面の大きいローポリ風）。Blenderに依存しない
# 座標：頭の中心 hc からの位置を頭の大きさ s で割った値（x＝人物の左、y＝後ろ、z＝上）
import math
import numpy as np
from sdf import Model, ellipsoid, cone, rot, grad, mesh, smin


def fib_dirs(n, rng, jitter=0.35):
    i = np.arange(n) + 0.5
    ph = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
    d = np.stack([np.cos(th) * np.sin(ph), np.sin(th) * np.sin(ph), np.cos(ph)], 1)
    d = d + rng.normal(0, jitter * 2.0 / math.sqrt(n), d.shape)
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def chisel(f, center, size, n, depth, rng):
    """凸な形 f を n 枚の平面で少しずつ削る → 大きさのそろわない平らな面の集まり"""
    if n <= 0: return f
    D = fib_dirs(n, rng); center = np.asarray(center, float)
    lo = np.zeros(n); hi = np.full(n, size * 4.0)
    for _ in range(44):
        mid = 0.5 * (lo + hi); ins = f(center + D * mid[:, None]) < 0
        lo = np.where(ins, mid, lo); hi = np.where(ins, hi, mid)
    S = center + D * lo[:, None]
    N = grad(f, S, size * 0.002); N /= np.linalg.norm(N, axis=1, keepdims=True)
    dep = depth * (0.45 + 1.1 * rng.random(n))
    off = ((S - N * dep[:, None]) * N).sum(1)
    def g(p):
        return np.maximum(f(p), (p @ N.T - off[None, :]).max(1))
    return g


def hairline(c, keysL, keysR):
    """生え際：頭蓋の中心 c から見た向き（φ：0＝正面、90＝真横）ごとの高さの角度θ。下は髪なし（正の値）"""
    xL, yL = (np.array(v, float) for v in zip(*keysL)); xR, yR = (np.array(v, float) for v in zip(*keysR))
    def f(q):
        d = q - c; r = np.linalg.norm(d, axis=1) + 1e-9
        ph = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))
        th = np.degrees(np.arcsin(np.clip(d[:, 2] / r, -1, 1)))
        thh = np.where(ph >= 0, np.interp(np.abs(ph), xL, yL), np.interp(np.abs(ph), xR, yR))
        return np.radians(thh - th) * np.maximum(r, 0.06)
    return f


def _opts(spec): return spec[-1] if isinstance(spec[-1], dict) else {}


def _nd(spec): return spec[-3:-1] if isinstance(spec[-1], dict) else spec[-2:]


def _prim(spec):
    kind = spec[0]
    if kind == "ell":
        _, cen, rad, ang = spec[:4]; R = rot(*ang)
        return ellipsoid(cen, rad, R), np.asarray(cen, float), float(max(rad))
    if kind == "cone":
        _, a, b, r1, r2 = spec[:5]; a = np.asarray(a, float); b = np.asarray(b, float)
        return cone(a, b, r1, r2), (a + b) / 2, float(np.linalg.norm(b - a) / 2 + max(r1, r2))
    raise ValueError(kind)


# 髪型：shell＝地肌を覆う厚さ、blobs＝生え際で切るかたまり、locks＝生え際に関係なく垂れる房（前髪など）
# 各かたまり：(種類, 形..., 削る枚数, 削る深さ)
def _hl(front, temple, burn, burn_tip, above_ear, behind, nape):
    return [(0, front), (28, front - 2), (46, temple), (58, temple - 8), (66, burn), (71, burn_tip), (76, burn), (80, above_ear - 2),
            (90, above_ear), (100, above_ear - 2), (106, -8), (114, behind), (130, (behind + nape) / 2 - 4), (155, nape), (180, nape - 2)]


STYLES = {
    # 主人公：上にボリューム、前は額にかぶさり、反対側（右）へ流れて先が下がる前髪。横は短く、耳の前はとがる
    "swept": dict(
        shell=0.0140,
        hl_L=_hl(13, 6, -14, -24, 3, -26, -50), hl_R=_hl(13, 6, -14, -22, 3, -26, -50),
        blobs=[("ell", (0.0, 0.006, 0.092), (0.086, 0.110, 0.080), (-6, 0, 0), 18, 0.0140),
               ("ell", (0.0, -0.040, 0.118), (0.078, 0.080, 0.058), (-18, 0, 0), 12, 0.0110),
               ("ell", (0.0, 0.052, 0.010), (0.088, 0.074, 0.088), (0, 0, 0), 12, 0.0120)],
        locks=[("ell", (-0.024, -0.094, 0.080), (0.074, 0.028, 0.040), (8, -20, 0), 10, 0.0080)]),
    # 眼鏡の人：きちんとした短い横分け。ボリュームは控えめ
    "neat": dict(
        shell=0.0060,
        hl_L=_hl(20, 15, 0, -10, 4, -24, -48), hl_R=_hl(20, 15, 0, -10, 4, -24, -48),
        blobs=[("ell", (0.0, 0.004, 0.080), (0.084, 0.106, 0.074), (-4, 0, 0), 18, 0.0120),
               ("ell", (0.010, -0.035, 0.105), (0.072, 0.075, 0.045), (-14, 0, 0), 10, 0.0080),
               ("ell", (0.0, 0.050, 0.008), (0.087, 0.072, 0.084), (0, 0, 0), 12, 0.0110)],
        locks=[("ell", (-0.006, -0.090, 0.090), (0.072, 0.024, 0.030), (6, -14, 0), 8, 0.0080)]),
    # 女性：ボブ。上は丸く大きく、あごの高さで外へ広がる。手前（左）は耳にかける、前髪は右へ流す
    "bob": dict(
        shell=0.0070,
        hl_L=[(0, 16), (30, 13), (50, 8), (62, -2), (70, -12), (76, -2), (82, 2), (92, 4), (102, 2), (110, -60), (180, -70)],
        hl_R=[(0, 16), (30, 13), (50, 6), (64, -70), (180, -70)],
        bottom=-0.080, bottom_tilt=0.10,
        blobs=[("ell", (0.0, 0.006, 0.062), (0.099, 0.120, 0.094), (0, 0, 0), 22, 0.0140),
               ("cone", (0.0, 0.040, 0.030), (0.0, 0.050, -0.060), 0.100, 0.114, 18, 0.0130, dict(hollow=0.016))],
        locks=[("ell", (-0.020, -0.092, 0.078), (0.086, 0.030, 0.044), (10, -24, 0), 10, 0.0090),
               ("cone", (-0.062, -0.068, 0.060), (-0.088, -0.034, -0.052), 0.026, 0.021, 14, 0.0040)]),
}


def chunk_hair_model(head_m, P, HP, hc, s):
    st = dict(STYLES[HP["style"]]); st.update(HP.get("over", {}))
    rng = np.random.default_rng(HP.get("seed", 1))
    cr = P.get("cran", 1.0); W = P.get("width", 1.0); hcA = np.asarray(hc, float)
    c = np.array([0.0, 0.010, 0.032 + (cr - 1) * 0.035])
    sc = np.array([W, 1.0, 1.0])
    def loc(p): return (p - hcA) / (s * sc)
    def shell(q): return head_m(hcA + q * sc * s) / s - st["shell"]
    def head_local(q): return head_m(hcA + q * sc * s) / s
    def build(b):
        f, cen, size = _prim(b); n, dep = _nd(b); g = chisel(f, cen, size, n, dep, rng); hol = _opts(b).get("hollow")
        if hol:      # 内側をくりぬく（ボブの下の部分：首とのすき間が暗い穴にならないよう、頭の少し外まで）
            return lambda q, g=g, hol=hol: np.maximum(g(q), -(head_local(q) - hol))
        return g
    blobs = [build(b) for b in st["blobs"]]
    locks = [build(b) for b in st.get("locks", [])]
    hl = hairline(c, st["hl_L"], st["hl_R"])
    bottom = st.get("bottom"); tilt = st.get("bottom_tilt", 0.0)

    def H(p):
        q = loc(p)
        d = shell(q)
        for f in blobs: d = np.minimum(d, f(q))
        d = np.maximum(d, hl(q))
        for f in locks: d = smin(d, f(q), st.get("lock_k", 0.010))     # 前髪は本体となめらかにつなぐ（段差でくるっと巻いて見えないように）
        if bottom is not None:
            d = np.maximum(d, (bottom + tilt * (-q[:, 1])) - q[:, 2])
        return d * s
    m = Model(); m.add(H, "hair", bones={"head": 1.0})
    return m


def chunk_hair_mesh(head_m, P, HP, hc, s, h=0.0022):
    m = chunk_hair_model(head_m, P, HP, hc, s); hc = np.asarray(hc, float)
    lo = hc + np.array([-0.16, -0.18, -0.13]) * s; hi = hc + np.array([0.16, 0.16, 0.20]) * s
    V, Q = mesh(m, lo, hi, h, relax_iters=1)
    return m, V, Q
VERSION = "c1"
