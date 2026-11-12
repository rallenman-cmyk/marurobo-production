# 形を「距離の式（SDF）」で決めて、なめらかな網目（メッシュ）にする道具
# 粘土を盛るように、楕円体・円すい・角を丸めた箱を「なめらかに足す／引く」
import numpy as np


def rot(rx=0.0, ry=0.0, rz=0.0):
    """XYZオイラー角（度）→ 3x3 回転行列（列＝局所軸）"""
    rx, ry, rz = np.radians([rx, ry, rz])
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def ellipsoid(c, r, R=None):
    c = np.asarray(c, float); r = np.asarray(r, float)
    def f(p):
        q = p - c
        if R is not None: q = q @ R
        k0 = np.sqrt(((q / r) ** 2).sum(1)); k1 = np.sqrt(((q / (r * r)) ** 2).sum(1))
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-12)
    return f


def sphere(c, r):
    c = np.asarray(c, float)
    return lambda p: np.sqrt(((p - c) ** 2).sum(1)) - r


def cone(a, b, r1, r2):
    """両端が球の円すい（太さが変わる円柱）"""
    a = np.asarray(a, float); b = np.asarray(b, float); ba = b - a; l2 = float(ba @ ba)
    rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
    def f(p):
        pa = p - a; y = pa @ ba; z = y - l2
        x = pa * l2 - np.outer(y, ba); x2 = (x * x).sum(1); y2 = y * y * l2; z2 = z * z * l2
        k = np.sign(rr) * rr * rr * x2
        return np.where(np.sign(z) * a2 * z2 > k, np.sqrt(x2 + z2) * il2 - r2,
               np.where(np.sign(y) * a2 * y2 < k, np.sqrt(x2 + y2) * il2 - r1,
                        (np.sqrt(np.maximum(x2 * a2 * il2, 0.0)) + y * rr) * il2 - r1))
    return f


def bounded(f, lo, hi, pad=0.0):
    """範囲（箱）の外では計算を省く。外の点には「箱までの距離＋余白」を返す（本当の距離以下の下限）"""
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    def g(p):
        d_out = np.sqrt((np.maximum(np.maximum(lo - p, p - hi), 0.0) ** 2).sum(1))
        inside = d_out <= 0.0
        out = d_out + pad
        if inside.any(): out[inside] = f(p[inside])
        return out
    return g


def cone_b(a, b, r1, r2, margin=0.02):
    a = np.asarray(a, float); b = np.asarray(b, float); r = max(r1, r2) + margin
    return bounded(cone(a, b, r1, r2), np.minimum(a, b) - r, np.maximum(a, b) + r, pad=margin)


def rbox(c, half, rad, R=None):
    c = np.asarray(c, float); half = np.asarray(half, float)
    def f(p):
        q = p - c
        if R is not None: q = q @ R
        q = np.abs(q) - half + rad
        return np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rad
    return f


def torus(c, R, major, minor):
    """R の第3列（局所Z）が輪の軸"""
    c = np.asarray(c, float)
    def f(p):
        q = (p - c) @ R
        rxy = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - major
        return np.sqrt(rxy ** 2 + q[:, 2] ** 2) - minor
    return f


def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k): return -smin(-a, -b, k)


class Model:
    """部品（名前・骨の割り当て・グループ付き）をなめらかに足し合わせた形"""
    def __init__(self):
        self.prims = []; self.subs = []; self.post = []

    def add(self, f, label, k=0.0, bones=None, group="main"):
        self.prims.append(dict(f=f, label=label, k=k, bones=bones or {}, group=group)); return self

    def sub(self, f, k=0.0):
        self.subs.append((f, k)); return self

    def __call__(self, p):
        d = None
        for pr in self.prims:
            di = pr["f"](p); d = di if d is None else smin(d, di, pr["k"])
        for f, k in self.subs: d = smax(d, -f(p), k)
        for g in self.post: d = g(p, d)
        return d

    def dists(self, p):
        return np.stack([pr["f"](p) for pr in self.prims], 1)


def _eval(F, P, chunk=300000):
    out = np.empty(len(P))
    for s in range(0, len(P), chunk): out[s:s + chunk] = F(P[s:s + chunk])
    return out


def surface_nets(F, lo, hi, h):
    """格子で符号を調べ、境目の面を四角形でつなぐ（Surface Nets）"""
    lo = np.asarray(lo, float) - 2 * h; hi = np.asarray(hi, float) + 2 * h
    n = (np.floor((hi - lo) / h).astype(int) + 2)
    axes = [lo[i] + h * np.arange(n[i]) for i in range(3)]
    S = np.empty(tuple(n), bool)
    X, Y = np.meshgrid(axes[0], axes[1], indexing="ij")
    XY = np.stack([X.ravel(), Y.ravel()], 1)
    for k, z in enumerate(axes[2]):  # 1層ずつ（メモリ節約）
        P = np.concatenate([XY, np.full((len(XY), 1), z)], 1)
        S[:, :, k] = (_eval(F, P) < 0).reshape(n[0], n[1])
    nc = n - 1
    cnt = np.zeros(tuple(nc), np.int16)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                cnt += S[dx:dx + nc[0], dy:dy + nc[1], dz:dz + nc[2]]
    act = (cnt > 0) & (cnt < 8)
    idx = np.full(tuple(nc), -1, np.int64); ii = np.nonzero(act); idx[ii] = np.arange(len(ii[0]))
    V = np.stack([lo[a] + h * (ii[a] + 0.5) for a in range(3)], 1)
    quads = []
    for a in range(3):
        b, c = (a + 1) % 3, (a + 2) % 3
        s0 = [slice(None)] * 3; s1 = [slice(None)] * 3
        s0[a] = slice(0, n[a] - 1); s1[a] = slice(1, n[a])
        A0 = S[tuple(s0)]; A1 = S[tuple(s1)]
        e = list(np.nonzero(A0 != A1))
        m = (e[b] >= 1) & (e[b] <= n[b] - 2) & (e[c] >= 1) & (e[c] <= n[c] - 2)
        e = [x[m] for x in e]
        low_in = A0[tuple(e)]
        def cell(db, dc):
            ci = [e[0].copy(), e[1].copy(), e[2].copy()]
            ci[b] = ci[b] - 1 + db; ci[c] = ci[c] - 1 + dc
            return idx[tuple(ci)]
        q = np.stack([cell(0, 0), cell(1, 0), cell(1, 1), cell(0, 1)], 1)
        q[~low_in] = q[~low_in][:, ::-1]
        quads.append(q)
    return V, np.concatenate(quads)


def grad(F, V, e):
    ex, ey, ez = np.array([e, 0, 0]), np.array([0, e, 0]), np.array([0, 0, e])
    return np.stack([F(V + ex) - F(V - ex), F(V + ey) - F(V - ey), F(V + ez) - F(V - ez)], 1) / (2 * e)


def project(F, V, h, iters=5):
    """点を面の上へ寄せる（ニュートン法）"""
    for _ in range(iters):
        d = F(V); g = grad(F, V, h * 0.2)
        st = (d / ((g * g).sum(1) + 1e-12))[:, None] * g
        L = np.sqrt((st * st).sum(1)); sc = np.minimum(1.0, h / np.maximum(L, 1e-12))
        V = V - st * sc[:, None]
    return V


def edges_of(Q):
    E = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    return np.unique(np.sort(E, 1), axis=0)


def neighbor_avg(X, E, n):
    cnt = np.bincount(E[:, 0], minlength=n) + np.bincount(E[:, 1], minlength=n)
    out = np.zeros((n, X.shape[1]))
    for j in range(X.shape[1]):
        out[:, j] = np.bincount(E[:, 0], weights=X[E[:, 1], j], minlength=n) + np.bincount(E[:, 1], weights=X[E[:, 0], j], minlength=n)
    return out / np.maximum(cnt, 1)[:, None]


def relax(F, V, Q, h, iters=4, lam=0.5):
    """網目を均して（ならして）から、もう一度面の上へ戻す"""
    E = edges_of(Q)
    for _ in range(iters):
        V = V + lam * (neighbor_avg(V, E, len(V)) - V)
        V = project(F, V, h, 2)
    return V


def mesh(F, lo, hi, h, relax_iters=4):
    V, Q = surface_nets(F, lo, hi, h)
    V = project(F, V, h, 6)
    V = relax(F, V, Q, h, relax_iters)
    return V, Q


def smooth_weights(W, Q, iters=6, lam=0.5):
    E = edges_of(Q)
    for _ in range(iters): W = W + lam * (neighbor_avg(W, E, len(W)) - W)
    return W / np.maximum(W.sum(1, keepdims=True), 1e-9)


def prim_weights(model, V, Q, bone_names, sigma=0.012, neighbors=None, iters=6):
    """各点の重み：近い部品ほど強く（同じ／隣のグループだけ）→ 骨ごとに合計 → なめらかに"""
    D = model.dists(V)
    groups = [pr["group"] for pr in model.prims]
    dom = D.argmin(1)
    allowed = np.ones_like(D, bool)
    if neighbors is not None:
        gi = {g: i for i, g in enumerate(sorted(set(groups)))}
        ok = np.zeros((len(gi), len(gi)), bool)
        for g in gi: ok[gi[g], gi[g]] = True
        for g1, g2 in neighbors:
            if g1 in gi and g2 in gi: ok[gi[g1], gi[g2]] = ok[gi[g2], gi[g1]] = True
        pg = np.array([gi[g] for g in groups])
        allowed = ok[pg[dom]][:, pg]
    dmin = D.min(1, keepdims=True)
    Wp = np.where(allowed, np.exp(-(D - dmin) / sigma), 0.0)
    Wp /= Wp.sum(1, keepdims=True)
    bi = {b: i for i, b in enumerate(bone_names)}
    W = np.zeros((len(V), len(bone_names)))
    for j, pr in enumerate(model.prims):
        for b, w in pr["bones"].items(): W[:, bi[b]] += Wp[:, j] * w
    return smooth_weights(W, Q, iters)
