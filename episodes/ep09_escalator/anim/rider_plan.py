# 9本目 v1 のコメント（「まるロボに人が貫通してる」3 件）から：乗る人（お客さん）を、まるロボと重ならない段に乗せる
#   blender -b --factory-startup --python rider_plan.py -- A01 <出力フォルダ> --track
#   昼の場面が映る時間（A・I の場面）を 1/8 秒ごとに、まるロボの位置（動きの予定から計算。描かない）と、
#   人を段 k・横 y に乗せたときの位置を比べ、重なる時間を数える。
#   いまの人（RIDERS）の重なりと、重ならない段 k の候補を出す（RIDER_NOW / RIDER_FREE）
import os, sys, json, math
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenes.py")
src = open(P, encoding="utf-8").read().replace("        render_clip(CLIPNAME,", "        PLAN()\n        0 and render_clip(CLIPNAME,")


def PLAN():
    G_ = _G; G = G_["G"]; E = G_["ESC"][0]
    mm = G_["mm"]; M = G_["MARU_ALL"][0]
    CL = json.load(open(os.path.join(os.path.dirname(P), "clips.json")))
    st = sorted(v[2] for v in CL.values())
    shown = []
    for k_, v in CL.items():
        if v[3] not in ("A", "I"): continue
        nx = [x for x in st if x > v[2] + 0.01]
        shown.append((v[2], nx[0] if nx else v[1]))
    T1 = max(b for a, b in shown)
    p = M.plan(T1 + 1.0)
    frames = mm.simulate(p, fps=8, t_end=T1 + 1.0, t_start=0.0)
    s_board, s_alight = G.DIP_LEN + 0.45, G.LTOP - G.DIP_LEN - 0.3
    xb, _ = G.top_point(s_board)[0]; xa, _ = G.top_point(s_alight)[0]
    Lr = s_alight - s_board
    hide = getattr(E, "rider_hide", [])

    def rider(pos, k, y):
        sk = (pos + k * G.PITCH) % G.LOOP
        u = sk - s_board
        if u > G.LOOP / 2: u -= G.LOOP
        if u < 0: return xb + u, y, 0.0
        if u <= Lr:
            (fx, fz), _ = G.top_point(sk); return fx - 0.18, y, fz + G.TREAD_DZ
        return xa + (u - Lr), y, G.H

    pts = []
    for fr in frames:
        t = fr["t"]
        if not any(a <= t < b for a, b in shown) or any(a <= t <= b for a, b in hide): continue
        x, y, z = fr["root"]; o = M.off(t)
        pts.append((t, x * M.s + o[0], y * M.s + o[1], z * M.s + o[2], E.pos(t)))

    def hits(k, y):
        h = []
        for t, mx, my, mz, pos in pts:
            rx, ry, rz = rider(pos, k, y)
            if not (-11.0 < rx < 22.0): continue
            if math.hypot(rx - mx, ry - my) < 0.6 and rz - 0.4 < mz < rz + 1.8: h.append(round(t, 2))
        return h
    now = []
    for wk, k, y in E.riders:
        h = hits(k, y); now.append((k, y, len(h), h[:1] + h[-1:]))
    print("RIDER_NOW", json.dumps(now))
    free = {}
    for y in (0.2, -0.2, 0.15, -0.15):
        free[str(y)] = [k for k in range(G.N_STEPS) if not hits(k, y)]
    print("RIDER_FREE", json.dumps(free))


_G = {"__file__": P, "__name__": "__main__", "PLAN": PLAN}
exec(compile(src, P, "exec"), _G)
