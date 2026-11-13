# QR回の中の世界で使う、まるロボの予定の小さな部品（2章・3章…で共通）
#   大地のマスの上（TILE_TOP）と、まわりの白いフチ（QZ_TOP。マスより約 0.24m 低い）で、立つ高さが違う
import math
import numpy as np
import marumotion as mm
TILE_TOP, QZ_TOP = 0.24, 0.0
LATE = []
def teleport_z(p, pos, heading, z):
    """場面の切り替え（カット）で置き直す。立つ高さ z も変える（marumotion の teleport に高さを足したもの）"""
    t = p.t; P = np.array(pos, float); psi = math.radians(heading)
    p._seg_add(mm.Seg(t, t, P, psi))
    for j in (0, 1):
        p._lift_foot(j, t); p._place(j, t, (*(P + mm.rgt(psi) * (-1 if j == 0 else 1) * mm.HIP_X), z), psi)
    for ch, tr in p.tracks.items(): tr.set(t, 0.0, 0.0)
    p.cuts.append(t); p._p, p._psi = P, psi
    return p
def at(p, t, fn, name=''):
    if t < p.t - 1e-6: LATE.append((name, round(p.t - t, 2)))
    gap = t - p.t
    if gap > 3.2: p.idle(gap - 0.4, shifts=True, glance=True)
    p.wait(max(0.0, t - p.t)); fn(p)
def cut(p, t, pos, heading, z=TILE_TOP):
    at(p, t, lambda q: teleport_z(q, pos, heading, z), 'cut %.1f' % t)
def start(pos, heading, z):
    p = mm.Plan(pos=pos, heading=heading, ground=z)
    return p
def stagger(p, n=3, side=0.16, roll=22.0, label=None):
    """よろける（v12 #24）：反応の遅れ→目を見開く→横へ小さく跳ぶ（左右交互に n 回、だんだん小さく）。体は左右に大きく傾いて揺れ、踏んばって止まる"""
    lid = p._lb(label)
    t0 = p.t + 0.12
    p.blinks.append((t0, "fast")); p.no_blink.append((t0 - 0.3, t0 + 2.8))
    p.tracks["iris"].set(t0 + 0.05, 0.06, 0.30); p.tracks["iris"].set(t0 + 2.6, 0.8, 0.0)
    p.event(t0, "beep_surprise", 1.0)
    t = t0; sgn = 1.0
    for k in range(n):
        a = 0.72 ** k
        dv = mm.rgt(p._psi) * sgn * side * a - mm.fwd(p._psi) * 0.04 * a
        seg = p._jumps(t, [0.07 * a], dxy=tuple(dv), crouch=0.025, T_c=0.08, ext=0.03, depth=0.04, zeta=0.5, settle=0.22, T_l=0.12)
        t = seg.t1; sgn = -sgn
    T = t - t0 + 0.9
    p.layer(t0, t0 + T, lambda tt, t0=t0, T=T: {
        "roll": roll * math.exp(-(tt - t0) / (0.7 * T)) * math.sin(2 * math.pi * 1.55 * (tt - t0)) * min(1.0, (t0 + T - tt) / 0.3),
        "pitch": -6.0 * math.exp(-(tt - t0) / 0.5) * math.sin(math.pi * min(1.0, (tt - t0) / 0.5)),
        "light": 2.5 * math.exp(-(tt - t0) / 0.3)})
    p.t = t0 + T; p._lb_end(lid); return p
def tilt(p, deg=16.0, hold=1.8, label=None):
    """首をかしげる（v12 #41）：目を少し細めて上を見る→横へ deg 度かしげて止める→ゆっくり戻す。問いかけの電子音"""
    lid = p._lb(label); t0 = p.t
    p.tracks["roll"].set(t0, 0.45, -deg); p.tracks["twist"].set(t0, 0.45, 7.0)
    p.tracks["iris"].set(t0, 0.3, -0.08); p.tracks["gaze_pitch"].set(t0, 0.12, 9.0)
    p.event(t0 + 0.25, "beep_question", 1.0)
    for ch in ("roll", "twist", "iris", "gaze_pitch"): p.tracks[ch].set(t0 + 0.45 + hold, 0.55, 0.0)
    p.blinks.append(t0 + 0.9)
    p.t = t0 + 0.45 + hold + 0.6; p._lb_end(lid); return p
