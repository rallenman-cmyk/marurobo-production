# 1章：8マスがたたまれて箱になる（箱の壁＝8マスの板。白黒はマスのまま）・縦横の21マスの線
import math, bpy
from mathutils import Vector, Euler, Matrix
from kit import world as W
import qr_world as QW
PANEL = 0.7; WALL_H = 0.7; BOXW = 1.4          # 板1枚 0.7m。壁は 2枚×高さ 0.7m。箱は 1.4×1.4×0.7m＋ふた
def panel_targets(center):
    """箱の8枚の板の置き場所（読む順に：前2・右2・後2・左2）。(位置, 回転)"""
    c = Vector(center); out = []
    for side, (nx, ny) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        n = Vector((nx, ny, 0)); t = Vector((-ny, nx, 0))
        for k in (-1, 1):
            p = c + n * (BOXW / 2) + t * (PANEL / 2 * k) + Vector((0, 0, WALL_H / 2))
            rz = math.atan2(ny, nx) - math.pi / 2
            out.append((p, Euler((math.pi / 2, 0, rz), 'XYZ')))
    return out
def tile_color(v, state):
    """箱の板：白黒を残したまま、役割の色を強めに乗せる（大地のマスより見分けやすく）"""
    if state in (None, 'none'): return QW.color_for(v, None)
    base = W.srgb(QW.COL['black'] if v else QW.COL['white']); tint = W.srgb(QW.COL[state])
    return (*QW.mixc(base, tint, 0.45 if v else 0.62), 1.0)
def panels(Wd, b, center, state=None, u=1.0, lid=True, lid_open=False, name='Box'):
    """箱 b の8マス → 板。u=0：マスの位置（平ら）、u=1：箱の壁。途中は弧を描いて起き上がる"""
    A = Wd['assets']; cells = A['boxes'][str(b)]; tm = Wd['tiles'][tuple(cells[0])].data.materials[0]
    tg = panel_targets(center); objs = []
    for i, (r, c) in enumerate(cells):
        t = Wd['tiles'][(r, c)]; v = t['v']; t.color = (*QW.color_for(v, None)[:3], 0.22)   # 元のマスは、うっすら跡として残す
        p0 = Wd['xy'](r, c); p0.z = QW.TILE_H / 2; p1, e1 = tg[i]
        ui = max(0.0, min(1.0, u * 1.6 - i * 0.075))        # 読む順に少しずつ遅れて起き上がる
        s = ui * ui * (3 - 2 * ui)
        p = p0.lerp(p1, s) + Vector((0, 0, math.sin(math.pi * s) * 1.6))
        sz = (QW.MOD - QW.GAP) * (1 - s) + PANEL * s
        o = W.box('%s panel %d' % (name, i), (sz, sz, QW.TILE_H * (1 - s) + 0.05 * s), tm, bevel=0.02, seg=2)
        o.location = p; o.rotation_euler = Euler((e1.x * s, 0, e1.z * s), 'XYZ'); o.color = tile_color(v, state); objs.append(o)
    if lid and u >= 0.999:
        lm = W.mat('%s lid' % name, (0.86, 0.88, 0.90) if state is None else W.srgb(QW.COL[state]), rough=0.5)
        lo = W.box('%s lid' % name, (BOXW + 0.05, BOXW + 0.05, 0.08), lm, bevel=0.02); c = Vector(center)
        if lid_open: lo.location = c + Vector((0, BOXW * 0.55, WALL_H + 0.35)); lo.rotation_euler = (math.radians(-70), 0, 0)
        else: lo.location = c + Vector((0, 0, WALL_H + 0.03))
        bm = W.box('%s floor' % name, (BOXW, BOXW, 0.04), W.mat('%s floor m' % name, (0.30, 0.32, 0.35), rough=0.6), bevel=0.0); bm.location = c + Vector((0, 0, 0.02))
        objs.append(lo)
    return objs
def box_center(Wd, b):
    e = Wd['boxes'][b].location; return (e.x, e.y, QW.TILE_H * 0.0 + 0.0)
def measure_lines(Wd, which=('v', 'h')):
    """縦・横の 21 マスの線（QR の左の外と上の外。マスごとに目盛り）"""
    m = W.mat_emit('Measure', W.srgb('#14A3B4'), 1.6); n = 21; M = QW.MOD; h = n * M / 2; off = 1.6; z = 0.35
    for w in which:
        if w == 'v':
            bar = W.box('Measure v', (0.45, n * M, 0.08), m); bar.location = (-h - off, 0, z)
            for k in range(n + 1): t = W.box('tick v', (1.4, 0.22, 0.08), m); t.location = (-h - off, h - k * M, z)
        else:
            bar = W.box('Measure h', (n * M, 0.45, 0.08), m); bar.location = (0, h + off, z)
            for k in range(n + 1): t = W.box('tick h', (0.22, 1.4, 0.08), m); t.location = (-h + k * M, h + off, z)
