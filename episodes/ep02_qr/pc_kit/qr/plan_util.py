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
