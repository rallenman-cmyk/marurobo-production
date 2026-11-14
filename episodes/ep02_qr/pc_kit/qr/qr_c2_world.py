# QRコード回・2章「見つける」の中の世界の本番描画（PC・Blender 4.3.2・EEVEE）。台本 v2.0 の時刻（c2_v20_times.json）
#   blender -b --factory-startup --python qr_c2_world.py -- --blend story.blend --out DIR --frames 1:1923 --video 1 --vprefix qrc2w_
#   確認用：--standin 1（仮のまるロボ）。--still 300,1000 で指定のコマだけ PNG
#   描くのは 3D の場面だけ（c2_plan.WORLD_RANGES。2D の図の場面は組み立てで重ねる）。3D の中に字は書かない（数字・名前は 2D の札）
#   中身：目の光でなぞる → マスが浮いて黒白の帯 → 斜め → 4方向 → 3つの目印が光る／大地ごと回る → 元の向き＋L字・目印のない角／
#         黒白交互の列を跳ぶ・1マスずつ光る／柄を外す（白黒が入れ替わる）／読み方の帯（紫）2本・片方が汚れる／白いフチ・境目・4マスの目盛り
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Euler, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import qr_world as QW
import c2_plan as CP
from c2_plan import FPS, s, e, fr_of, rc, H, MOD, TL, TR, BL, BR
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc2w'); ap.add_argument('--frames', default='1:%d' % fr_of(CP.WORLD_RANGES[0][1]))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc2w_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--still', default=''); ap.add_argument('--save', default='')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
def interp(ob, kind, only=None):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if only and not fc.data_path.startswith(only): continue
            for kp in fc.keyframe_points: kp.interpolation = kind
def show(ob, spans):
    """ob を spans（[(始め, 終わり)]）の間だけ見せる"""
    keys = [(1, True)]
    for a, b in spans: keys += [(max(2, fr_of(a)), False), (fr_of(b), True)]
    for f, h in keys: ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)
    interp(ob, 'CONSTANT', only='hide')
def hide(ob, spans):
    """ob を spans の間だけ消す（ほかは見せる）"""
    keys = [(1, False)]
    for a, b in spans: keys += [(max(2, fr_of(a)), True), (fr_of(b), False)]
    for f, h in keys: ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)
    interp(ob, 'CONSTANT', only='hide')
ZB = 0.80                                                # 目の光の高さ（白いフチに立ったまるロボの目）

# ================================================================ 大地（1章の終わりの色：目印＝赤・中身＝青・予備＝橙）
Wd = QW.build(); coll = Wd['coll']; QW.lights_c(sc, coll)
AS = Wd['assets']; SYM = Wd['symbol']; N = AS['size']; TILES = Wd['tiles']; FL = AS['function_labels']
FIN = QW.cells_of(Wd, 'finder'); TIM = QW.cells_of(Wd, 'timing'); FMT = QW.cells_of(Wd, 'format')
DATA_C = QW.cells_of(Wd, 'data'); SPARE_C = QW.cells_of(Wd, 'spare')
FMT_A = [rc_ for rc_ in FMT if rc_[0] <= 8 and rc_[1] <= 8]; FMT_B = [rc_ for rc_ in FMT if rc_ not in FMT_A]
QW.paint(Wd, FIN, 'finder'); QW.paint(Wd, DATA_C, 'data'); QW.paint(Wd, SPARE_C, 'spare')
# 大地ごと回す（「おっとっと」）：原点の空の物にまとめる
pivot = W.empty('Pivot', coll, size=1.0)
bpy.context.view_layer.update()
for ob in list(coll.objects):
    if ob is pivot or ob.parent is not None or ob.type == 'LIGHT' or ob.name.startswith('Void'): continue
    mw = ob.matrix_world.copy(); ob.parent = pivot; ob.matrix_world = mw
for f in range(fr_of(CP.T_SPIN[0]) - 1, fr_of(CP.T_UNSPIN[1]) + 2):
    pivot.rotation_euler = (0, 0, math.radians(CP.spin_angle((f - 1) / FPS))); pivot.keyframe_insert('rotation_euler', index=2, frame=f)

# ---------------------------------------------------------------- 色のキー（物ごとに時刻の順に：前の色 → 新しい色を ramp 秒で）
CEV = []
def color_at(t, ob, rgba, ramp=0.15): CEV.append((t, ob, tuple(rgba), ramp))
def tile_state(cells, state, t, ramp=0.15):
    for rc_ in cells: tl = TILES[tuple(rc_)]; color_at(t, tl, QW.color_for(tl['v'], state), ramp)
def tile_value(cells, val_of, t, ramp=0.15):
    for rc_ in cells: color_at(t, TILES[tuple(rc_)], QW.color_for(val_of(rc_), None), ramp)
def bake_colors():
    last = {}
    for t, ob, c, ramp in sorted(CEV, key=lambda x: x[0]):
        f = fr_of(t); prev = last.get(ob.name, tuple(ob.color))
        ob.color = prev; ob.keyframe_insert('color', frame=f)
        ob.color = c; ob.keyframe_insert('color', frame=f + max(1, int(round(ramp * FPS))))
        last[ob.name] = c
    for ob in {x[1] for x in CEV}: interp(ob, 'LINEAR', only='color')

# ================================================================ まるロボの予定（目の位置を光に使うので先に）
plan, FR = CP.frames()
def eye_at(t):
    f = FR[min(len(FR) - 1, max(0, int(round(t * FPS))))]
    R = Matrix.Rotation(f['psi'], 3, 'Z') @ Matrix.Rotation(math.radians(-f['pitch']), 3, 'X')
    return Vector(f['root']) + Vector((0, 0, mm.TORSO_Z)) + R @ Vector((0, mm.LENS['y'], mm.LENS['z']))
def eye_ray(name, t0, t1, target_of, col='#7FE3F0', r=0.06, strength=5.0):
    """目から target_of(t) へ伸びる光（毎コマ）。t0〜t1 の間だけ（v12 #16：光が目から出ていると分かるように）"""
    b = W.cyl(name, r, 1.0, W.mat_emit(name, W.srgb(col), strength), seg=12); b.visible_shadow = False
    for f in range(max(2, fr_of(t0) - 1), fr_of(t1) + 2):
        t = (f - 1) / FPS; e0 = eye_at(t); dv = Vector(target_of(t)) - e0
        b.location = e0 + dv / 2; b.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); b.scale = (1, 1, max(0.001, dv.length))
        for k in ('location', 'rotation_euler', 'scale'): b.keyframe_insert(k, frame=f)
    show(b, [(t0, t1)]); return b
def spot(name, t0, t1, pos_of, col='#BFF6FF', R=0.28):
    """光が当たっている所の明るい点"""
    o = W.box(name, (2 * R, 2 * R, 2 * R), W.mat_emit(name, W.srgb(col), 8.0), bevel=R, seg=4); o.visible_shadow = False
    for f in range(max(2, fr_of(t0) - 1), fr_of(t1) + 2): o.location = Vector(pos_of((f - 1) / FPS)); o.keyframe_insert('location', frame=f)
    show(o, [(t0, t1)]); return o

# ================================================================ 光る物（目の光・線）
def beam(name, p0, p1, col='#7FE3F0', r=0.07, strength=5.0, grow=0.4, t0=0.0, t1=1.0):
    """t0 から grow 秒で p0 → p1 へ伸びる光の棒。t1 で消える"""
    p0, p1 = Vector(p0), Vector(p1); dv = p1 - p0
    b = W.cyl(name, r, 1.0, W.mat_emit(name, W.srgb(col), strength), seg=12); b.visible_shadow = False
    b.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler()
    b.location = p0; b.scale = (1, 1, 0.001); b.keyframe_insert('location', frame=fr_of(t0)); b.keyframe_insert('scale', frame=fr_of(t0))
    b.location = p0 + dv / 2; b.scale = (1, 1, dv.length); b.keyframe_insert('location', frame=fr_of(t0 + grow)); b.keyframe_insert('scale', frame=fr_of(t0 + grow))
    interp(b, 'LINEAR'); show(b, [(t0, t1)]); return b
def ring(name, xy0, t0, t1, R=6.2, col='#7FE3F0'):
    rg = W.torus(name, R, 0.16, W.mat_emit(name, W.srgb(col), 3.0)); rg.location = (xy0[0], xy0[1], QW.TILE_H + 0.2); rg.visible_shadow = False
    for t, sc_ in ((t0, 0.6), (t0 + 0.25, 1.12), (t0 + 0.5, 1.0)): rg.scale = (sc_, sc_, 1); rg.keyframe_insert('scale', frame=fr_of(t))
    show(rg, [(t0, t1)]); return rg

# ---------------------------------------------------------------- 10-01：左上の目印に光る輪（全体を真上から）
ring('ring19', TL, s('10-01', 0.6), 4.6)
# ---------------------------------------------------------------- 10-02〜10-04：目の光でなぞる → 通ったマスが浮き上がって黒白の帯に
P0, P1 = Vector((*CP.P0, 0)), Vector((*CP.P1, 0))
XL, XR = rc(3, -0.5)[0], rc(3, 6.5)[0]                         # 左上の目印の左の端・右の端
def _u(t, a, b): return min(1.0, max(0.0, (t - a) / (b - a)))
_ra, _rb = CP.T_BEAM_ROW
_row_pt = lambda t: (XL + (XR - XL) * _u(t, _ra, _rb), P0.y - 0.2, QW.TILE_H + 0.18)
eye_ray('beam row ray', _ra, _rb + 0.35, _row_pt)
spot('beam row spot', _ra, _rb + 0.35, _row_pt)
beam('beam row', (XL, P0.y - 0.2, QW.TILE_H + 0.18), (XR, P0.y - 0.2, QW.TILE_H + 0.18), r=0.07, grow=_rb - _ra, t0=_ra, t1=CP.T_LIFT + 0.6)
LM = {1: W.mat('lift black', (0.02, 0.025, 0.03), rough=0.6), 0: W.mat_emit('lift white', (0.95, 0.95, 0.93), 1.3)}
LIFTED = []
def lift(cells, t_start, z, xs=None, yc=None, step=0.16, t_back=None, mid=()):
    for k, (r, c) in enumerate(cells):
        tl = TILES[(r, c)]; v = tl['v']; x0, y0 = rc(r, c)
        o = W.box('lift %d-%d' % (r, c), (MOD - 0.02, MOD - 0.02, QW.TILE_H), LM[v], bevel=0.03)
        x1 = xs[k] if xs else x0; y1 = yc if yc is not None else y0; ta = t_start + step * k
        keys = [(ta, (x0, y0, QW.TILE_H / 2), 0.0), (ta + 0.6, (x1, y1, z), 90.0)]
        zz = z
        for tm, zm in mid: keys += [(tm, (x1, y1, zz), 90.0), (tm + 0.5, (x1, y1, zm), 90.0)]; zz = zm
        if t_back: keys += [(t_back, (x1, y1, zz), 90.0), (t_back + 0.6, (x0, y0, QW.TILE_H / 2), 0.0)]
        for t, loc, rx in keys:
            o.location = loc; o.rotation_euler = (math.radians(rx), 0, 0)
            o.keyframe_insert('location', frame=fr_of(t)); o.keyframe_insert('rotation_euler', frame=fr_of(t))
        show(o, [(ta, (t_back + 0.6) if t_back else 9e3)])
        hide(tl, [(ta, (t_back + 0.6) if t_back else 9e3)])     # 元のマスは浮いている間だけ消す（地面に抜けた跡）
        LIFTED.append(o)
    return LIFTED[-len(cells):]
row = [(3, c) for c in range(7)]
band1 = lift(row, CP.T_LIFT, 4.2, t_back=CP.T_DROP, mid=[(CP.T_LIFT_DIAG, 5.6)])     # 斜めの帯が来るとき、1本目は少し上へ
_aa, _ab = CP.T_BEAM_AGAIN; YF = P0.y - QW.TILE_H / 2 - 0.16      # 帯の手前の面（カメラ側）
_band_pt = lambda t: (XL + (XR - XL) * _u(t, _aa + 0.25, _ab), YF, 4.2)
eye_ray('beam again ray', _aa, _ab + 0.4, _band_pt)
spot('beam again spot', _aa, _ab + 0.4, _band_pt)
beam('beam again', (XL, YF, 4.2), (XR, YF, 4.2), r=0.06, grow=_ab - _aa - 0.25, t0=_aa + 0.25, t1=_ab + 0.9)
for k, o in enumerate(band1):                                      # 光が通るとき、その板が少しふくらむ（1・1・3・1・1 を数える）
    tp = _aa + 0.25 + (_ab - _aa - 0.25) * (k + 0.5) / 7.0
    for t, sc_ in ((tp - 0.12, 1.0), (tp, 1.13), (tp + 0.25, 1.0)): o.scale = (sc_, sc_, sc_); o.keyframe_insert('scale', frame=fr_of(t))
d0 = Vector((rc(-0.6, -0.6)[0], rc(-0.6, -0.6)[1], ZB)); d1 = Vector((rc(7.6, 7.6)[0], rc(7.6, 7.6)[1], ZB))
beam('beam diag', d0, d1, grow=CP.T_BEAM_DIAG[1] - CP.T_BEAM_DIAG[0], t0=CP.T_BEAM_DIAG[0], t1=CP.T_LIFT_DIAG + 1.6)
sp = MOD * 1.414
lift([(k, k) for k in range(7)], CP.T_LIFT_DIAG, 3.4, xs=[TL[0] + (k - 3) * sp for k in range(7)], yc=rc(3, 3)[1], t_back=CP.T_DROP)
# 10-04.5：縦・横・斜め 2 本を、速く
for k, (a, b) in enumerate(((rc(3, -1), rc(3, 7.6)), (rc(-1, 3), rc(7.6, 3)), (rc(-1, -1), rc(7.6, 7.6)), (rc(-1, 7), rc(7.6, -0.6)))):
    beam('beam fast %d' % k, (a[0], a[1], ZB), (b[0], b[1], ZB), r=0.05, strength=3.5, grow=0.3, t0=CP.T_BEAMS4[k], t1=53.3)
# 10-05：3 つの目印が順に光る
for k, key in enumerate((TL, TR, BL)): ring('ring24 %d' % k, key, CP.T_RINGS[k], 79.6, R=6.4)
# ---------------------------------------------------------------- 12-01：大地ごと回る（回る向きの矢印）→ 元に戻りながら L 字・目印のない角
arc = W.torus('spin arc', H * 1.35, 0.18, W.mat_emit('spin arc', W.srgb('#FFD640'), 2.5), arc=math.radians(110)); arc.location = (0, 0, 0.6); arc.rotation_euler = (0, 0, math.radians(20))
show(arc, [(CP.T_SPIN[0] + 0.1, CP.T_UNSPIN[0])])
beam('L top', (TR[0], TR[1], QW.TILE_H + 0.3), (TL[0], TL[1], QW.TILE_H + 0.3), col='#FFD640', r=0.22, strength=3.0, grow=0.6, t0=CP.T_LSHAPE, t1=148.4)
beam('L left', (TL[0], TL[1], QW.TILE_H + 0.3), (BL[0], BL[1], QW.TILE_H + 0.3), col='#FFD640', r=0.22, strength=3.0, grow=0.6, t0=CP.T_LSHAPE + 0.6, t1=148.4)
blink = [(CP.T_CORNER + 0.8 * k, CP.T_CORNER + 0.8 * k + 0.5) for k in range(4)] + [(CP.T_CORNER + 3.2, 148.4)]   # v12 #25：点滅は 5 回、あとは出したまま
sq = 3.5; pts = [(BR[0] - sq, BR[1] - sq), (BR[0] + sq, BR[1] - sq), (BR[0] + sq, BR[1] + sq), (BR[0] - sq, BR[1] + sq)]
dm = W.mat_emit('corner dash', W.srgb('#FFB000'), 4.5); dk = W.mat('corner dash edge', W.srgb('#3A2600'), rough=0.6)   # v12 #25：太く・濃い縁取りで見やすく
for k in range(4):
    a, b = pts[k], pts[(k + 1) % 4]
    for j in range(6):
        u0, u1 = j / 6.0, j / 6.0 + 0.09
        p0 = Vector((a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0, QW.TILE_H + 0.3)); p1 = Vector((a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1, QW.TILE_H + 0.3))
        dv = p1 - p0; ds = W.cyl('dash %d %d' % (k, j), 0.40, dv.length, dm, seg=12); ds.location = p0 + dv / 2 + Vector((0, 0, 0.12)); ds.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); show(ds, blink)
        de = W.cyl('dash edge %d %d' % (k, j), 0.56, dv.length + 0.3, dk, seg=12); de.location = p0 + dv / 2 - Vector((0, 0, 0.05)); de.rotation_euler = ds.rotation_euler; show(de, blink)
# ---------------------------------------------------------------- 12-02〜12-03：黒白交互の列（緑）→ 物差し：1マスずつ光る
# v12 #26：黒を緑に変えない。話している列（目印と目印の間の白黒交互）を、光る枠で囲む
def frame_box(name, r0, c0, r1, c1, t0, t1, col='#FFC400', z=QW.TILE_H + 0.16, rr=0.17):
    x0, y0 = rc(r0 - 0.5, c0 - 0.5); x1, y1 = rc(r1 + 0.5, c1 + 0.5); pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for k in range(4):
        a, b = pts[k], pts[(k + 1) % 4]; beam('%s %d' % (name, k), (a[0], a[1], z), (b[0], b[1], z), col=col, r=rr, strength=4.5, grow=0.45, t0=t0 + 0.1 * k, t1=t1)
frame_box('timing row', 6, 8, 6, 12, CP.T_TIMING, 180.2); frame_box('timing col', 8, 6, 12, 6, CP.T_TIMING + 0.3, 180.2)
ticks = [(6, c) for c in range(8, 13)] + [(r, 6) for r in range(8, 13)]
for k, rc_ in enumerate(ticks): tile_state([rc_], 'restored', CP.T_TICK[k], 0.08); tile_value([rc_], lambda q: TILES[q]['v'], CP.T_TICK[k] + 0.35, 0.2)
# ---------------------------------------------------------------- 14：真上から。いまの QR（柄を重ねた後）→ 柄を外した並び。14-04b は光の線が通った所から入れ替わる
BP = SYM['before_pattern']; REG = [rc_ for rc_ in TILES if FL[rc_[0]][rc_[1]] == 'data']
cur = lambda rc_: TILES[rc_]['v']; raw = lambda rc_: BP[rc_[0]][rc_[1]]
tile_value(REG + TIM, cur, 217.6 - 0.05, 0.02)                     # 役割の色を外して、ふつうの白黒に
tile_value(REG, raw, 223.5 - 0.05, 0.02)                           # 14-02：中身をそのまま書いた並び
tile_value(REG, raw, 264.9 - 0.05, 0.02)                           # 14-04：下のマスは元の並び。その上に柄のシートが落ちてきて重なる（v12 #31）
# v12 #31：スキャンの光ではなく「柄のシート」をめくる。シートには柄を重ねた後の白黒が刷ってある。下のマスは元の並び
import bmesh
def peel_sheet(t0, t1, rho=1.7, sub=4, z0=QW.TILE_H + 0.09):
    """REG のマスを覆うシート（1 枚のメッシュ・1 マスを横に sub 分割）。右の端から左へ、丸まりながらめくれて（めくれた所は裏返って上に重なる）、最後に浮いて消える"""
    me = bpy.data.meshes.new('mask sheet'); ob = bpy.data.objects.new('mask sheet', me); coll.objects.link(ob)
    md = W.mat('sheet dark', W.srgb('#1C2430'), rough=0.25, coat=0.6); ml = W.mat('sheet light', W.srgb('#E4EDF5'), rough=0.25, coat=0.6)
    me.materials.append(md); me.materials.append(ml)
    V_, F_, M_ = [], [], []; idx = {}
    def vid(x, y):
        k = (round(x, 4), round(y, 4))
        if k not in idx: idx[k] = len(V_); V_.append((x, y, 0.0))
        return idx[k]
    g = 0.02
    for (r, c) in REG:
        x0 = c * MOD + g; x1 = (c + 1) * MOD - g; y0 = H - r * MOD - g; y1 = H - (r + 1) * MOD + g
        xs = [x0 + (x1 - x0) * i / sub for i in range(sub + 1)]
        for i in range(sub):
            F_.append((vid(xs[i], y1), vid(xs[i + 1], y1), vid(xs[i + 1], y0), vid(xs[i], y0))); M_.append(0 if cur((r, c)) else 1)
    me.from_pydata(V_, [], F_); me.update()
    for p_, m_ in zip(me.polygons, M_): p_.material_index = m_
    ob.location = (-H, 0, z0)
    sol = ob.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.05
    base = [Vector(v) for v in V_]; L = N * MOD
    sk0 = ob.shape_key_add(name='flat'); keys = []
    f0, f1 = fr_of(t0), fr_of(t1)
    for f in range(f0, f1 + 1):
        u = (f - f0) / max(1, f1 - f0); u = u * u * (3 - 2 * u)
        xp = L + 2.0 - (L + 2.0 + math.pi * rho) * u                 # めくれの折り目（右の外 → 左の外へ）
        sk = ob.shape_key_add(name='peel %d' % f)
        for i, v in enumerate(base):
            sarc = v.x - xp
            if sarc <= 0: co = Vector((v.x, v.y, 0.0))
            elif sarc < math.pi * rho: ph = sarc / rho; co = Vector((xp + rho * math.sin(ph), v.y, rho * (1 - math.cos(ph))))
            else: co = Vector((xp - (sarc - math.pi * rho), v.y, 2 * rho))
            sk.data[i].co = co
        keys.append((f, sk))
    for n_, (f, sk) in enumerate(keys):
        for ff, val in ((f - 1, 0.0), (f, 1.0), (f + 1, 0.0)):
            if n_ == len(keys) - 1 and ff == f + 1: continue          # 最後の形はそのまま残す（浮いて消えるまで）
            sk.value = val; sk.keyframe_insert('value', frame=ff)
    # 14-04 の頭：上から落ちてきて重なる
    for t, z in ((264.95, z0 + 5.0), (265.55, z0)): ob.location = (-H, 0, z); ob.keyframe_insert('location', frame=fr_of(t))
    # めくり終わり：上へ浮いて小さくなって消える
    for t, z, s_ in ((t1, z0, 1.0), (t1 + 0.7, z0 + 9.0, 0.6)):
        ob.location = (-H, 0, z); ob.scale = (s_, s_, s_); ob.keyframe_insert('location', frame=fr_of(t)); ob.keyframe_insert('scale', frame=fr_of(t))
    show(ob, [(264.95, t1 + 0.7)])
    return ob
SHEET = peel_sheet(*CP.T_UNMASK)
tile_state(DATA_C, 'data', 276.2 - 0.05, 0.02); tile_state(SPARE_C, 'spare', 276.2 - 0.05, 0.02)     # v12 #26：タイミングの列は緑にしない
# ---------------------------------------------------------------- 13：読み方の帯（紫）2本。札（字なし）→ 同じ中身（弧）→ 片方が汚れても、もう片方が光る
tile_state(FMT, 'format', CP.T_FORMAT, 0.5)
# v13 #36：浮いた板はやめた。紫の帯の本物のマスを光らせる（1つ目＝予備の量 2 マス・2つ目＝柄の番号 3 マス。横の帯の左から）
def tag(name, cells, t0, t1, col):
    for k, (r_, c_) in enumerate(cells):
        pl = W.box('%s %d' % (name, k), (MOD - 0.10, MOD - 0.10, 0.05), W.mat_emit('%s %d' % (name, k), W.srgb(col), 3.0), bevel=0.04)
        pl.location = (rc(r_, c_)[0], rc(r_, c_)[1], QW.TILE_H + 0.035); pl.visible_shadow = False
        for f, z in ((fr_of(t0), 0.2), (fr_of(t0) + 4, 1.25), (fr_of(t0) + 8, 1.0)):
            pl.scale = (z, z, 1.0); pl.keyframe_insert('scale', frame=f)
        show(pl, [(t0, t1)])
tag('tag1', [(8, 0), (8, 1)], CP.T_TAG1, 307.8, '#C77DFF'); tag('tag2', [(8, 2), (8, 3), (8, 4)], CP.T_TAG2, 307.8, '#C77DFF')
for k in range(2):                                                  # v12 #36：上へ出る線はやめた。2本が同時に光る（同じ中身）
    tile_state(FMT, 'restored', CP.T_LINK + 0.9 * k, 0.12); tile_state(FMT, 'format', CP.T_LINK + 0.9 * k + 0.45, 0.25)
tile_state(FMT_A, 'broken', CP.T_DIRTY, 0.3)
tile_state(FMT_B, 'restored', CP.T_DIRTY + 1.2, 0.2); tile_state(FMT_B, 'format', CP.T_DIRTY + 2.4, 0.4)
tile_state(FMT_A, 'format', 321.3 - 0.05, 0.02)
# ---------------------------------------------------------------- 15：白いフチ。QR の境目の線と、4 マスの目盛り（字なし）
for k, (a, b) in enumerate((((-H, -H), (H, -H)), ((H, -H), (H, H)), ((H, H), (-H, H)), ((-H, H), (-H, -H)))):
    beam('border %d' % k, (a[0], a[1], QW.TILE_H + 0.05), (b[0], b[1], QW.TILE_H + 0.05), col='#FFFFFF', r=0.06, strength=2.5, grow=0.5, t0=CP.T_BORDER + 0.5 * k, t1=344.0)
for k in range(5):
    beam('qtick %d' % k, (H + k * MOD, -H - 1.2, QW.TILE_H + 0.05), (H + k * MOD, -H - 2.6, QW.TILE_H + 0.05), col='#14A3B4', r=0.08, strength=2.0, grow=0.2, t0=CP.T_QTICK + 0.15 * k, t1=344.0)
beam('qtick base', (H, -H - 1.9, QW.TILE_H + 0.05), (H + 4 * MOD, -H - 1.9, QW.TILE_H + 0.05), col='#14A3B4', r=0.08, strength=2.0, grow=0.6, t0=CP.T_QTICK, t1=344.0)
bake_colors()

# ================================================================ まるロボ（予定は上で作った FR）
if A.standin:
    import op_stage_standin as SI
    rroot, rtorso, rlegs = SI.build_robot()
    for f in range(F0, F1 + 1): SI.pose(rroot, rtorso, rlegs, FR[min(len(FR) - 1, f - 1)], key=f)
else:
    import marurig as mr
    assert os.path.exists(A.blend), 'story.blend が見つからない。--blend で指定する'
    with bpy.data.libraries.load(A.blend, link=False) as (src, dst): dst.objects = [n for n in src.objects]
    loaded = [o for o in dst.objects if o is not None]; maru0 = next(o for o in loaded if o.name == 'Maru')
    keep = {o.name for o in hier(maru0)}
    for o in loaded:
        if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
    for n in keep: sc.collection.objects.link(O[n])
    for n in keep:
        if O[n].animation_data: O[n].animation_data_clear()
    for o in hier(O['Maru']):
        if o.name.startswith(('Cradle', 'Maru cargo')) or 'cradle' in o.name.lower(): o.hide_render = True
    rig = mr.MaruRig(O['Maru']); bk = mr.Baker()
    for i, fr in enumerate(FR):
        if F0 - 2 <= i + 1 <= F1 + 2: rig.apply(fr, i + 1, bk)
    bk.write()

# ================================================================ カメラ（場面ごと。2D の図の場面はない）
C = lambda *v: Vector(v)
r6 = rc(6, 10); r9 = rc(9, 9); r10 = rc(10, 6); r8 = rc(8, 6)
VIEWS = {
    'K19': (C(0, -0.01, 70), C(0, 0, 0), 32, 0.0), 'K27': (C(0, -0.01, 70), C(0, 0, 0), 32, 0.0), 'K28': (C(0, -0.01, 70), C(0, 0, 0), 32, 0.0),
    'K20': (C(TL[0] + 3.5, TL[1] - 14.0, 7.0), C(TL[0] - 0.6, TL[1], 0.6), 30, 0.0),
    'K21a': (C(TL[0] + 1.0, TL[1] - 15.5, 6.2), C(TL[0] - 0.4, TL[1], 2.6), 30, 0.0), 'K21': (C(TL[0] + 1.0, TL[1] - 15.5, 6.2), C(TL[0] - 0.4, TL[1], 2.6), 30, 0.0),
    'K22': (C(TL[0] + 1.0, TL[1] - 16.5, 6.8), C(TL[0] - 0.4, TL[1], 3.2), 30, 0.0),
    'K23': (C(TL[0] + 6.0, TL[1] - 12.0, 9.0), C(TL[0], TL[1], 0.6), 30, 0.0),
    'K24': (C(H * 1.2, -H * 1.6, 22), C(0, 0, 0), 26, -22.0),
    'K29': (C(r6[0] + 1.5, r6[1] - 12.5, 8.0), C(r6[0], r6[1] + 0.5, 0.0), 26, 0.0),      # v12 #26：少し上から。白黒交互の列と枠が見えるように
    'K30': (C(r9[0], r9[1] - 0.01, 26), C(r9[0], r9[1], 0), 30, 0.0),
    'K40': (C(0, -0.01, 66), C(0, 0, 0), 32, 0.0), 'K38': (C(0, -0.01, 66), C(0, 0, 0), 32, 0.0),
    'K31a': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0), 'K32': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0),
    'K33': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0), 'K31': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0),
    'K34': (C(H + 3.0 * MOD + 3.0, -H - 9.0, 3.6), C(H + 1.0, -H + 3.0, 0.4), 24, 0.0),
}
# v12：1つの絵（SHOTS）の中で、カメラを切り替える所（始め, 終わり, 見え方）
VIEWS.update({
    'K38peel': (C(0, -46.0, 40.0), C(0, 2.0, 0), 30, 0.0),                       # #31：シートがめくれるのが見えるよう斜めから
    'K34phone': (C(1.2, -5.0, 78.0), C(0, 0, 0), 32, 3.0),                       # #39：スマホから見た角度（真上から少し傾けた手持ち）
})
SPLIT = {
    'K27': [(124.9, 130.8, 'K27u'), (130.8, 134.4, 'K27')],      # #24：よろけるのをアップで（v13：場面の頭からアップ。大地が回るのはアップの中だけ）
    'K38': [(269.6, 276.2, 'K38peel')],
    'K34': [(321.3, CP.T_PHONE, 'K34'), (CP.T_PHONE, 344.0, 'K34phone')],
}
FOLLOW = {'K27u': (Vector((2.6, -3.6, 1.15)), 0.62, 30)}                          # まるロボを追うカメラ：ずれ・見る高さ・レンズ
PUSH = {'K19': 0.0, 'K27': 0.0, 'K28': 0.02, 'K40': 0.02, 'K38': 0.02, 'K30': 0.03}
def look_q(loc, look, roll):
    q = (look - loc).to_track_quat('-Z', 'Y')
    if roll: q = q @ Euler((0, 0, math.radians(roll))).to_quaternion()
    return q.to_euler()
SH = []
for a, b, k in CP.SHOTS:
    if k not in VIEWS: continue
    parts = [(max(a, x), min(b, y), v) for x, y, v in SPLIT.get(k, [])] if k in SPLIT else []
    parts = [p_ for p_ in parts if p_[1] - p_[0] > 1e-3]
    if not parts: SH.append((a, b, k)); continue
    cur_ = a
    for x, y, v in parts:
        if x - cur_ > 1e-3: SH.append((cur_, x, k))
        SH.append((x, y, v)); cur_ = y
    if b - cur_ > 1e-3: SH.append((cur_, b, k))
def root_at(t): return Vector(FR[min(len(FR) - 1, max(0, int(round(t * FPS))))]['root'])
for n_, (t0, t1, k) in enumerate(SH):
    if k in FOLLOW:
        off, hz, lens = FOLLOW[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 900; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
        cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); sm = root_at(t0 + 2.0 / FPS)          # v13：場面の頭のまるロボから追い始める（前の場面の位置から寄らない）
        for f in range(fr_of(t0) - 1, fr_of(t1) + 2):
            rt = root_at((f - 1) / FPS); sm = rt if sm is None else sm.lerp(rt, 0.35)        # 少し遅れて追う（揺れをやわらげる）
            T = sm + Vector((0, 0, hz)); L = T + off; cam.location = L; cam.rotation_euler = look_q(L, T, 0.0)
            cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    else:
        L, T, lens, roll = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 900; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
        cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = look_q(L, T, roll); d1 = PUSH.get(k, 0.04)
        for t, dd in ((t0, 0.0), (t1, d1)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
        if k == 'K34phone':                                                       # 手持ちの小さな揺れ
            for f in range(fr_of(t0), fr_of(t1) + 1, 6):
                tt = (f - 1) / FPS; u = (tt - t0) / max(1e-3, t1 - t0)
                cam.location = L + (T - L) * d1 * u + Vector((0.25 * math.sin(1.3 * tt), 0.2 * math.sin(0.9 * tt + 1.0), 0)); cam.keyframe_insert('location', frame=f)
        interp(cam, 'LINEAR' if k != 'K34phone' else 'BEZIER')
    m = sc.timeline_markers.new('c2 %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=A.save)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w2_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    cam_at(F0); sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w2_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.WORLD_RANGES, late=CP.LATE,
               events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_happy', 'beep_yes', 'beep_no', 'beep_surprise', 'ding')],
               shots=SH, spin=[CP.T_SPIN, CP.T_UNSPIN], lift=CP.T_LIFT, lift_diag=CP.T_LIFT_DIAG, drop=CP.T_DROP, unmask=CP.T_UNMASK),
          open(os.path.join(A.out, 'qrc2w_log_%d.json' % F0), 'w'), default=float, indent=0)
print('QRC2W DONE', F0, F1)
