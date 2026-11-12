# QRコード回・2章「見つける」の中の世界の本番描画（PC・Blender 4.3.2・EEVEE）。台本 v2.0 の時刻（c2_v20_times.json）
#   blender -b --factory-startup --python qr_c2_world.py -- --blend story.blend --out DIR --frames 1:1923 --video 1 --vprefix qrc2w_
#   確認用：--standin 1（仮のまるロボ）。--still 300,1000 で指定のコマだけ PNG
#   描くのは 3D の場面だけ（c2_plan.WORLD_RANGES。2D の図の場面は組み立てで重ねる）。3D の中に字は書かない（数字・名前は 2D の札）
#   中身：目の光でなぞる → マスが浮いて黒白の帯 → 斜め → 4方向 → 3つの目印が光る／大地ごと回る → 元の向き＋L字・目印のない角／
#         黒白交互の列を跳ぶ・1マスずつ光る／柄を外す（白黒が入れ替わる）／読み方の帯（紫）2本・片方が汚れる／白いフチ・境目・4マスの目盛り
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Euler
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
beam('beam row', (P0.x + 0.5, P0.y, ZB), (rc(3, 7.6)[0], P0.y, ZB), grow=CP.T_BEAM_ROW[1] - CP.T_BEAM_ROW[0], t0=CP.T_BEAM_ROW[0], t1=CP.T_LIFT + 0.6)
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
beam('beam again', (P0.x + 0.5, P0.y, 4.2), (rc(3, 7.6)[0], P0.y, 4.2), r=0.05, grow=CP.T_BEAM_AGAIN[1] - CP.T_BEAM_AGAIN[0], t0=CP.T_BEAM_AGAIN[0], t1=CP.T_BEAM_AGAIN[1] + 0.5)
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
blink = [(CP.T_CORNER + 0.8 * k, CP.T_CORNER + 0.8 * k + 0.5) for k in range(int((148.4 - CP.T_CORNER) / 0.8))]
sq = 3.5; pts = [(BR[0] - sq, BR[1] - sq), (BR[0] + sq, BR[1] - sq), (BR[0] + sq, BR[1] + sq), (BR[0] - sq, BR[1] + sq)]
dm = W.mat_emit('corner dash', W.srgb('#FFD640'), 3.0)
for k in range(4):
    a, b = pts[k], pts[(k + 1) % 4]
    for j in range(6):
        u0, u1 = j / 6.0, j / 6.0 + 0.09
        p0 = Vector((a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0, QW.TILE_H + 0.3)); p1 = Vector((a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1, QW.TILE_H + 0.3))
        dv = p1 - p0; ds = W.cyl('dash %d %d' % (k, j), 0.24, dv.length, dm, seg=10); ds.location = p0 + dv / 2; ds.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); show(ds, blink)
# ---------------------------------------------------------------- 12-02〜12-03：黒白交互の列（緑）→ 物差し：1マスずつ光る
tile_state(TIM, 'timing', CP.T_TIMING, ramp=0.4)
ticks = [(6, c) for c in range(8, 13)] + [(r, 6) for r in range(8, 13)]
for k, rc_ in enumerate(ticks): tile_state([rc_], 'restored', CP.T_TICK[k], 0.08); tile_state([rc_], 'timing', CP.T_TICK[k] + 0.35, 0.2)
# ---------------------------------------------------------------- 14：真上から。いまの QR（柄を重ねた後）→ 柄を外した並び。14-04b は光の線が通った所から入れ替わる
BP = SYM['before_pattern']; REG = [rc_ for rc_ in TILES if FL[rc_[0]][rc_[1]] == 'data']
cur = lambda rc_: TILES[rc_]['v']; raw = lambda rc_: BP[rc_[0]][rc_[1]]
tile_value(REG + TIM, cur, 217.6 - 0.05, 0.02)                     # 役割の色を外して、ふつうの白黒に
tile_value(REG, raw, 223.5 - 0.05, 0.02)                           # 14-02：中身をそのまま書いた並び
tile_value(REG, cur, 264.9 - 0.05, 0.02)                           # 14-04：柄を重ねたまま
for c in range(N):
    tc = CP.T_UNMASK[0] + (CP.T_UNMASK[1] - CP.T_UNMASK[0]) * c / (N - 1)
    tile_value([rc_ for rc_ in REG if rc_[1] == c], raw, tc, 0.12)
sweep = W.box('unmask sweep', (0.35, N * MOD + 1.0, 0.12), W.mat_emit('sweep', W.srgb('#7FE3F0'), 4.0)); sweep.visible_shadow = False
for t, x in ((CP.T_UNMASK[0], -H), (CP.T_UNMASK[1], H)): sweep.location = (x, 0, QW.TILE_H + 0.25); sweep.keyframe_insert('location', frame=fr_of(t))
interp(sweep, 'LINEAR'); show(sweep, [(CP.T_UNMASK[0], CP.T_UNMASK[1] + 0.1)])
tile_state(DATA_C, 'data', 276.2 - 0.05, 0.02); tile_state(SPARE_C, 'spare', 276.2 - 0.05, 0.02); tile_state(TIM, 'timing', 276.2 - 0.05, 0.02)
# ---------------------------------------------------------------- 13：読み方の帯（紫）2本。札（字なし）→ 同じ中身（弧）→ 片方が汚れても、もう片方が光る
tile_state(FMT, 'format', CP.T_FORMAT, 0.5)
def tag(name, rr, t0, t1):
    pl = W.box(name, (6.6, 2.2, 0.08), W.mat_emit(name, W.srgb('#8C55B8'), 1.4)); pl.location = (rc(rr, 3.5)[0], rc(rr, 3.5)[1], QW.TILE_H + 0.22); pl.rotation_euler = (math.radians(25), 0, 0)
    show(pl, [(t0, t1)])
    beam(name + ' link', (rc(rr, 3.5)[0] + 3.3, rc(rr, 3.5)[1], QW.TILE_H + 0.3), (rc(8, 7)[0], rc(8, 7)[1], QW.TILE_H + 0.3), col='#B88BE0', r=0.06, strength=2.0, grow=0.4, t0=t0 + 0.2, t1=t1)
tag('tag1', 10.6, CP.T_TAG1, 307.8); tag('tag2', 12.8, CP.T_TAG2, 307.8)
lk = W.torus('format link', H * 0.55, 0.12, W.mat_emit('format link', W.srgb('#B88BE0'), 2.5), arc=math.radians(180)); lk.location = (rc(8, 10)[0], rc(8, 10)[1], 0.6); lk.rotation_euler = (math.radians(90), 0, 0)
show(lk, [(CP.T_LINK, 321.3)])
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

# ================================================================ まるロボ
plan, FR = CP.frames()
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
    'K29': (C(r6[0] + 1.0, r6[1] - 9.0, 3.4), C(r6[0], r6[1] + 1.0, 0.6), 26, 0.0),
    'K30': (C(r9[0], r9[1] - 0.01, 26), C(r9[0], r9[1], 0), 30, 0.0),
    'K40': (C(0, -0.01, 66), C(0, 0, 0), 32, 0.0), 'K38': (C(0, -0.01, 66), C(0, 0, 0), 32, 0.0),
    'K31a': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0), 'K32': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0),
    'K33': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0), 'K31': (C(r10[0] + 2.0, r10[1] - 14.0, 13.0), C(r8[0], r8[1], 0), 28, 0.0),
    'K34': (C(H + 3.0 * MOD + 3.0, -H - 9.0, 3.6), C(H + 1.0, -H + 3.0, 0.4), 24, 0.0),
}
PUSH = {'K19': 0.0, 'K27': 0.0, 'K28': 0.02, 'K40': 0.02, 'K38': 0.02, 'K30': 0.03}
def look_q(loc, look, roll):
    q = (look - loc).to_track_quat('-Z', 'Y')
    if roll: q = q @ Euler((0, 0, math.radians(roll))).to_quaternion()
    return q.to_euler()
SH = [(a, b, k) for a, b, k in CP.SHOTS if k in VIEWS]
for n_, (t0, t1, k) in enumerate(SH):
    L, T, lens, roll = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 900; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = look_q(L, T, roll); d1 = PUSH.get(k, 0.04)
    for t, dd in ((t0, 0.0), (t1, d1)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    interp(cam, 'LINEAR')
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
