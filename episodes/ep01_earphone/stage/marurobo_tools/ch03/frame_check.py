# カメラの候補を数値で確かめる（画面の中の位置：x −1..1 左→右、y −1..1 下→上。範囲外は写らない）
import numpy as np, math, sys
sys.path.insert(0, "."); import ch03_plan as cp, marumotion as mm
L = np.array(cp.L); psi1 = cp.psi1; F = np.array(mm.fwd(psi1)); R = np.array(mm.rgt(psi1))
PTS = {"robot": (*L, 0.75), "robot_top": (*L, 1.3), "robot_feet": (*L, 0.05), "stem_base": (0, 11.12, 0.5), "stem_mid": (0, 11.12, 6), "head_c": (-2.3, 11.1, 14.5),
       "tip": (-5.6, 10.2, 15.1), "head_top": (-2.3, 11.1, 18.0), "booth": (*(cp.E + cp.NG * 2.38), 1.5), "dock_corner": (*(L - F * 0.8 + R * 2.0), 2.75),
       "phone_top": (*(L - F * 2.0), 10.0), "U": (*cp.U, 0.75)}
def proj(cam, tgt, lens, P):
    cam = np.array(cam, float); f = np.array(tgt, float) - cam; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r); u = np.cross(r, f)
    d = np.array(P, float) - cam; z = d @ f
    if z <= 0: return None
    hx = 18.0 / lens; hy = 10.125 / lens
    return round((d @ r) / z / hx, 2), round((d @ u) / z / hy, 2), round(z, 1)
def show(name, cam, tgt, lens):
    print("==", name, "cam", np.round(cam, 2), "lens", lens)
    for k, P in PTS.items(): print("   %-11s %s" % (k, proj(cam, tgt, lens, P)))
if __name__ == "__main__":
    for spec in sys.argv[1:]:
        cx, cy, cz, tx, ty, tz, lens = [float(v) for v in spec.split(",")]
        show(spec, (cx, cy, cz), (tx, ty, tz), lens)
