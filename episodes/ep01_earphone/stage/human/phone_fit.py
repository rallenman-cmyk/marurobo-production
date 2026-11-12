# スマホの位置と向きを参考画像から逆算する（上の2つの角と、長い辺の向き）。画面は持ち主の目の方を向く
# 使い方: python3 phone_fit.py fit.json out.json
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import hgen, ref_people
from trace_tool import project, IMG_W, IMG_H

OBS = {"M1": dict(tl=(850, 555), tr=(955, 532), edge=(1085, 730)),
       "W1": dict(tl=(350, 680), tr=(425, 665), edge=(480, 770)),
       "G1": dict(tl=(70, 675), tr=(115, 665), edge=(145, 730))}
SC = 1.3; PW, PL = 0.072 * SC, 0.150 * SC


def rot(a, b, c):
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    Rz = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1.0]]); Rx = np.array([[1.0, 0, 0], [0, cb, -sb], [0, sb, cb]]); Ry = np.array([[cc, 0, sc], [0, 1.0, 0], [-sc, 0, cc]])
    return Rz @ Rx @ Ry


def eyes_world(k, head):
    cfg = ref_people.PEOPLE[k]; P = dict(hgen.HEAD); P.update(cfg["head"]); B = dict(hgen.BODY); B.update(cfg.get("body", {}))
    J = hgen.skeleton(B); hc = np.asarray(J["head_center"]); hf = hgen.head_frame(P)
    R = np.array(head["R"]); H = np.array(head["H"])
    return np.mean([H + R @ (e) for e in hf["eye"]], 0)


def residual(x, k, cam, eye):
    C = x[:3]; R = rot(*x[3:6])
    xa, ya, n = R[:, 0], R[:, 1], R[:, 2]
    top_a = C + ya * PL / 2 - xa * PW / 2; top_b = C + ya * PL / 2 + xa * PW / 2; bot_b = C - ya * PL / 2 + xa * PW / 2; bot_a = C - ya * PL / 2 - xa * PW / 2
    uv, zc = project(np.array([top_a, top_b, bot_a, bot_b]), cam)
    o = OBS[k]; tl, tr, ed = np.array(o["tl"], float), np.array(o["tr"], float), np.array(o["edge"], float)
    # 上の2つの角（左右の割り当ては画像で左にある方を tl）
    a, b = (uv[0], uv[1]) if uv[0][0] < uv[1][0] else (uv[1], uv[0])
    bb = uv[3] if uv[0][0] < uv[1][0] else uv[2]          # 右上の角から下へのびる長い辺の終わり
    res = list((a - tl) / 5.0) + list((b - tr) / 5.0)
    dvec = bb - b; dvec = dvec / (np.linalg.norm(dvec) + 1e-9); w = ed - b
    res.append((dvec[0] * w[1] - dvec[1] * w[0]) / 5.0)       # 辺の点までの距離
    v = eye - C; dist = np.linalg.norm(v); v = v / dist
    res += list((n - v) / 0.25); res.append((dist - 0.33) / 0.06)
    return np.array(res)


def lm(f, x, iters=200):
    lam = 1e-2; r = f(x); e = r @ r
    for _ in range(iters):
        J = np.zeros((len(r), len(x))); h = 1e-6
        for j in range(len(x)):
            dx = np.zeros_like(x); dx[j] = h; J[:, j] = (f(x + dx) - r) / h
        A = J.T @ J; g = J.T @ r
        while True:
            st = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g); xn = x + st; rn = f(xn); en = rn @ rn
            if en < e: x, r, e = xn, rn, en; lam = max(lam / 3, 1e-8); break
            lam *= 4
            if lam > 1e9: return x, e
    return x, e


if __name__ == "__main__":
    fit = json.load(open(sys.argv[1])); cf = fit["camera"]; cam = (np.array(cf["C"]), cf["yaw"], cf["pitch"], cf["roll"], cf["lens"])
    out = {}
    rng = np.random.default_rng(0)
    for k in OBS:
        head = fit["heads"][k]; eye = eyes_world(k, head)
        best = None
        for t in range(40):
            # 初期値：目の前下 0.3m、画面は目の方
            C0 = eye + np.array([-0.15, rng.normal(0, 0.1), -0.22]) + rng.normal(0, 0.04, 3)
            x0 = np.concatenate([C0, rng.uniform(-math.pi, math.pi, 1), rng.uniform(-1.5, 1.5, 1), rng.uniform(-1, 1, 1)])
            x, e = lm(lambda x: residual(x, k, cam, eye), x0)
            if best is None or e < best[1]: best = (x, e)
        x, e = best; C = x[:3]; R = rot(*x[3:6]); r = residual(x, k, cam, eye)
        print(k, "err", round(e, 3), "C", np.round(C, 3), "corner px err", np.round(np.abs(r[:5]) * 5, 1), "dist", round(float(np.linalg.norm(eye - C)), 3))
        out[k] = dict(C=C.tolist(), R=R.tolist())
    json.dump(out, open(sys.argv[2], "w"), indent=1)
