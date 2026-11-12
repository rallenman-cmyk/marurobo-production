# 第3章 v2（長い道）のカメラ：C6 の終わり・C9a・道のり（M1〜M3）・C10a・C10b・C11
#   Blender の外でも、画面の中の位置を数値で確かめられる（python3 ch03_cams.py）
#   画面の位置：x −1..1（左→右）、y −1..1（下→上）。センサー幅 36mm・16:9
import math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import ch03_plan as cp, marumotion as mm

F = np.array(cp.F); R = np.array(cp.R); L = np.array(cp.L); A = cp.A


def P3(s, r=0.0, z=0.0):
    xy = cp.RP(s, r); return np.array([xy[0], xy[1], z], float)


def eb_matrix():
    """Codex版の巨大イヤホン → この版の置き場所（2倍・耳の先をスマホへ・軸の先を地面へ）"""
    def T(x, y, z): M = np.eye(4); M[:3, 3] = (x, y, z); return M
    c, s = math.cos(cp.EB_ROT), math.sin(cp.EB_ROT); Rz = np.eye(4); Rz[:2, :2] = [[c, -s], [s, c]]
    S = np.diag([cp.EB_SCALE, cp.EB_SCALE, cp.EB_SCALE, 1.0])
    return T(cp.E[0], cp.E[1], -0.02) @ Rz @ S @ T(-cp.EB_SRC[0], -cp.EB_SRC[1], -cp.EB_SRC_Z)


EBM = eb_matrix()
def eb(p): return (EBM @ np.array([*p, 1.0]))[:3]


EB_PTS = {"eb_head": eb((-2.3, 11.1, 14.5)), "eb_tip": eb((-5.6, 10.2, 15.1)), "eb_top": eb((-2.3, 11.1, 18.1)), "eb_stem": eb((0.0, 11.12, 6.0)),
          "eb_base": eb((0.0, 11.12, 0.5))}
PHONE_TOP = np.array([*(L - F * 1.8), 9.6])
BOOTH_C = np.array([*(cp.E + cp.NG * (cp.R_STEM + 0.5)), 1.2])


def proj(cam, tgt, lens, P):
    cam = np.array(cam, float); f = np.array(tgt, float) - cam; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r); u = np.cross(r, f)
    d = np.array(P, float) - cam; z = d @ f
    if z <= 0: return None
    hx = 18.0 / lens; hy = 10.125 / lens
    return round(float((d @ r) / z / hx), 2), round(float((d @ u) / z / hy), 2), round(float(z), 1)


def aim(cam, Pa, xa, Pb, xb, Pc, yc):
    """Pa を画面の x＝xa、Pb を x＝xb に置く向きとレンズ、Pc を y＝yc に置く上下の向きを解く → (見る点, レンズ mm)"""
    cam = np.array(cam, float)
    def az(P): d = np.array(P, float) - cam; return math.atan2(d[1], d[0])
    ta, tb = az(Pa), az(Pb); best = None
    for i in range(3601):
        yaw = ta + math.radians(-90 + i * 0.05)
        ua, ub = math.tan(mm.wrap(yaw - ta)), math.tan(mm.wrap(yaw - tb))       # 右が＋になるよう、向きからの角度
        if abs(xa) < 1e-6 or abs(xb) < 1e-6: continue
        ka, kb = ua / xa, ub / xb
        if ka > 0 and kb > 0:
            e = abs(ka - kb) / (ka + kb)
            if best is None or e < best[0]: best = (e, yaw, 0.5 * (ka + kb))
    _, yaw, k = best
    lens = 18.0 / k
    dc = np.array(Pc, float) - cam; hz = math.hypot(dc[0], dc[1]); el = math.atan2(dc[2], hz)
    pitch = el - math.atan(yc * 10.125 / lens)
    tgt = cam + np.array([math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)]) * 10.0
    return tgt, lens


def lerp(a, b, u): return a + (b - a) * u


def shot(t, robot_xy):
    """予定の時刻 t → (位置, 見る点, レンズ, ピントの点, 名前)。C9a 以降（と C6 の終わり）"""
    r = np.array(robot_xy(t)); rz = lambda z: np.array([r[0], r[1], z])
    if t < A(cp.T_M1):                                                  # C9a 出発：右横から追う（左にスマホ、右へ進む）
        p = np.array([*(r + R * 4.6 - F * 0.6), 1.5]); tg = np.array([*(r + F * 1.0), 0.95])
        return p, tg, 28.0, rz(1.0), "C9a"
    if t < A(cp.T_M2):                                                  # M1 段差の台に跳び乗る：右うしろの低い所から。遠くに巨大イヤホン
        cam = P3(15.1, 3.3, 0.55)
        tg, lens = aim(cam, P3(17.9, 0.0, 0.9), -0.45, EB_PTS["eb_stem"], 0.52, EB_PTS["eb_top"], 0.80)
        return cam, tg, lens, P3(18.0, 0.0, 0.9), "M1"
    if t < A(cp.T_M3):                                                  # M2 溝を跳び越える：台の上の右横から（溝が台の面の黒い切れ目に見える高さ）。少しだけ横へ流す
        u = mm.smooth((t - A(cp.T_M2)) / (A(cp.T_M3) - A(cp.T_M2))); h = cp.TERRACE["h"]
        cam = P3(lerp(28.95, 29.55, u), 3.3, h + 0.62)
        return cam, P3(lerp(29.05, 29.45, u), -0.3, h + 1.00), 21.0, P3(29.25, 0.0, h + 0.8), "M2"
    if t < A(cp.T_C10):                                                 # M3 運河の細い橋：運河の中の低い所から見上げる（橋の薄さと、両側の深さが分かる）
        u = mm.smooth((t - A(cp.T_M3)) / (A(cp.T_C10) - A(cp.T_M3)))
        cam = P3(lerp(56.4, 57.2, u), 3.4, -0.80)
        return cam, P3(lerp(56.6, 57.4, u), -0.2, 0.80), 19.0, P3(57.0, 0.0, 0.8), "M3"
    if t < C10B:                                                        # C10a 到着・向きを変える：受付ボックスの右前から
        cam = P3(cp.S_U - 3.4, 3.6, 1.45)
        tg, lens = aim(cam, P3(cp.S_U - 1.2, 0.0, 1.0), -0.30, BOOTH_C, 0.35, P3(cp.S_U, 0.0, 0.9), -0.20)
        return cam, tg, lens, P3(cp.S_U - 0.4, 0.0, 1.0), "C10"
    if t < C11:                                                         # C10b 後ずさり・腕が引き取る：右横から（台・腕・ボックスの口）
        u = mm.smooth((t - C10B) / (C11 - C10B))
        cam = P3(cp.S_U + lerp(0.10, 0.30, u), lerp(3.5, 3.3, u), 1.55)
        tg, lens = aim(cam, P3(cp.S_U, 0.0, 0.8), -0.20, BOOTH_C, 0.35, P3(cp.S_U, 0.0, 0.0), -0.78)
        return cam, tg, lens, P3(cp.S_U + 0.3, 0.0, 1.25), "C10b"
    if t < C11B:                                                        # C11a 曲が鳴る：見上げて、曲に合わせて揺れるまるロボ（受付の灯は緑）。少しずつ寄る
        u = mm.smooth((t - C11) / (C11B - C11))
        cam = P3(cp.S_U - lerp(3.4, 3.0, u), lerp(2.6, 2.4, u), 1.0)
        return cam, P3(cp.S_U + 0.3, -0.3, 1.25), 26.0, P3(cp.S_U, 0.0, 1.0), "C11"
    u = mm.smooth((t - C11B) / 2.0)                                      # C11b 引きの絵：左に遠くのスマホ、右に巨大イヤホン、その足もとにまるロボ（図と同じ左右）
    cam = P3(lerp(29.0, 30.5, u), lerp(64.0, 66.0, u), lerp(9.0, 10.0, u))
    tg, lens = aim(cam, PHONE_TOP, -0.80, EB_PTS["eb_stem"], 0.62, EB_PTS["eb_top"], 0.86)
    return cam, tg, lens, P3(38.0, 0.0, 6.0), "C11b"


def c6a(t, robot_xy):
    """C6a（本編 116.9〜120.6。台本 v2）：まるロボの右前から右横へ、ゆっくり回りこむ（台座より前だけを通る）"""
    r = np.array(robot_xy(t)); u = mm.smooth((t - A(116.9)) / 3.7)
    a = math.radians(lerp(22.0, 78.0, u)); rad = lerp(3.8, 5.0, u)
    cam = np.array([*(r + (F * math.cos(a) + R * math.sin(a)) * rad), lerp(1.05, 1.40, u)])
    return cam, np.array([r[0], r[1], lerp(0.95, 1.0, u)]), lerp(30.0, 32.0, u), np.array([r[0], r[1], 1.0]), "C6"


def c6b(t):
    """C6b（本編 120.6〜123.4。台本 v2）：「目指すのは、あのイヤホン」。まるロボの少し前の高さ 1.9m から、遠くの巨大イヤホンへ、ゆっくり寄る"""
    u = mm.smooth((t - A(120.6)) / 2.8)
    cam = P3(lerp(2.0, 2.6, u), 1.6, 1.9)
    return cam, P3(74.0, -13.4, 15.5), lerp(30.0, 32.5, u), EB_PTS["eb_stem"], "C6b"


def c6_end():
    """C6 の終わり：左にスマホとまるロボ、右に遠くの巨大イヤホン"""
    cam = P3(-8.0, 8.5, 2.6)                                           # スマホの台座（右の端 r＝2）の陰にならない所
    tg, lens = aim(cam, P3(0.0, 0.0, 0.8), -0.30, EB_PTS["eb_stem"], 0.45, EB_PTS["eb_top"], 0.80)
    return cam, tg, lens


C10B = A(140.90 + cp.DV2)              # 向きを変え終えたら、横からの絵へ（台本 v2 は v1 より +3.8 秒）
C11 = A(146.95 + cp.DV2)               # 曲の始まる少し前
C11B = A(148.35 + cp.DV2)              # 引きの絵へ


if __name__ == "__main__":
    p, ta = cp.ch03_plan(); fr = mm.simulate(p)
    M = {nm: (a, b, mm.simulate(q)) for a, b, q, nm in cp.montage_plans()}
    def rxy(t):
        for a, b, fq in M.values():
            if A(a) <= t < A(b): return np.array(fq[min(int(round(t * 24)), len(fq) - 1)]["root"][:2])
        return np.array(fr[min(int(round(t * 24)), len(fr) - 1)]["root"][:2])
    def rz(t, z):
        for a, b, fq in M.values():
            if A(a) <= t < A(b): f_ = fq[min(int(round(t * 24)), len(fq) - 1)]; return np.array([*f_["root"][:2], f_["root"][2] + z])
        f_ = fr[min(int(round(t * 24)), len(fr) - 1)]; return np.array([*f_["root"][:2], f_["root"][2] + z])
    print("EB points", {k: v.round(1) for k, v in EB_PTS.items()})
    cam, tg, lens = c6_end(); print("C6 end lens %.1f" % lens)
    for k, P in (("robot", P3(0, 0, 0.8)), ("robot_top", P3(0, 0, 1.95)), ("phone_top", PHONE_TOP), *EB_PTS.items()): print("   %-10s %s" % (k, proj(cam, tg, lens, P)))
    for t_abs in (128.5, 130.5, 131.5, 132.0, 132.6, 132.8, 133.6, 134.2, 134.9, 135.1, 136.0, 136.9, 137.1, 138.4, 140.0, 141.0, 143.0, 145.0, 146.9, 147.0, 148.0, 148.4, 149.7):
        t = A(t_abs + cp.DV2); cam, tg, lens, fp, nm = shot(t, rxy)
        pts = {"feet": rz(t, 0.02), "body": rz(t, 0.75), "parcel_top": rz(t, 1.95)}
        if nm in ("M1", "M3", "C11"): pts.update({"eb_top": EB_PTS["eb_top"], "eb_stem": EB_PTS["eb_stem"]})
        if nm in ("C10", "C10b", "C11"): pts["booth"] = BOOTH_C
        if nm in ("C11", "C11b"): pts["phone_top"] = PHONE_TOP
        if nm == "C11b": pts.update({"eb_top": EB_PTS["eb_top"], "eb_stem": EB_PTS["eb_stem"]})
        print("%6.1f %-4s lens %5.1f " % (t_abs, nm, lens) + "  ".join("%s %s" % (k, proj(cam, tg, lens, P)) for k, P in pts.items()))
