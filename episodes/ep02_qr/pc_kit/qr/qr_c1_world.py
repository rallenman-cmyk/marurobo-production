# QRコード回・1章「中の世界」の本番描画（PC・Blender 4.3.2・EEVEE）。卓上の後（F_TABLE_END+1 〜 F_END）
#   blender -b --factory-startup --python qr_c1_world.py -- --blend story.blend --out DIR --frames 248:4370 --video 1
#   確認用（本物のまるロボがないとき）：--standin 1 で仮のまるロボ。--still 1000,2000 で指定のコマだけ PNG
#   中身：21×21 の大地（1マス1.5m）・目の光・縦横の21マスの線・8マスのまとまり・箱をたたむ／運ぶ／のぞく／開ける・HELLO・影・青と橙・元に戻す
import sys, os, math, json, argparse
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import qr_world as QW
from c1_timeline import *
import c1_plan as CP
import op_timeline as OPT
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc1w'); ap.add_argument('--frames', default='%d:%d' % (F_TABLE_END + 1, F_END))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc1w_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--still', default=''); ap.add_argument('--save', default='')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
FW0 = F_TABLE_END + 1                                  # 中の世界の最初のコマ
def fr_of(t): return int(round(t * FPS)) + 1
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
def const_interp(ob):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def lin_interp(ob):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
FONT = None
for fp in (A.font, os.path.join(HERE, 'japanese.ttc'), 'C:/Windows/Fonts/meiryob.ttc', 'C:/Windows/Fonts/meiryo.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'):
    if fp and os.path.exists(fp): FONT = bpy.data.fonts.load(fp); break
FONT = None   # v18 の決まり：3D の中に字を書かない（「21」「HELLO」「予備の数字」は、組み立てで 2D の大きな札にして重ねる）

# ================================================================ 大地（QW.build：441マス・余白の岸・暗い床）と光（C案）
Wd = QW.build(); coll = Wd['coll']; QW.lights_c(sc, coll)
AS = Wd['assets']; SYM = Wd['symbol']; N = AS['size']; MOD = QW.MOD; H = N * MOD / 2
TILES = Wd['tiles']; TM = TILES[(0, 0)].data.materials[0]
def xy(r, c): return Vector((*CP.xy(r, c), 0.0))
BOXES = {int(b): [tuple(rc) for rc in cs] for b, cs in AS['boxes'].items()}
DATA = list(SYM['data_boxes']); SPARE = list(SYM['spare_boxes'])
CEN = {b: Vector((*CP.box_c(b), 0.0)) for b in BOXES}
FIN = QW.cells_of(Wd, 'finder')
FIN_OF = {'TL': [rc for rc in FIN if rc[0] < 10 and rc[1] < 10], 'TR': [rc for rc in FIN if rc[0] < 10 and rc[1] > 10], 'BL': [rc for rc in FIN if rc[0] > 10 and rc[1] < 10]}

# ---------------------------------------------------------------- 色のキー（物ごとに時刻の順に：前の色→新しい色を ramp 秒で）
CEV = []                                               # (t, obj, rgba, ramp)
def color_at(t, ob, rgba, ramp=0.15): CEV.append((t, ob, tuple(rgba), ramp))
def tile_state(cells, state, t, ramp=0.15, alpha=None):
    for rc in cells:
        tl = TILES[tuple(rc)]; c = list(QW.color_for(tl['v'], state))
        if alpha is not None: c[3] = alpha
        color_at(t, tl, c, ramp)
def bake_colors():
    last = {}
    for t, ob, c, ramp in sorted(CEV, key=lambda e: e[0]):
        f = fr_of(t); prev = last.get(ob.name, tuple(ob.color))
        ob.color = prev; ob.keyframe_insert('color', frame=f)
        ob.color = c; ob.keyframe_insert('color', frame=f + max(1, int(round(ramp * FPS))))
        last[ob.name] = c
    for ob in {e[1] for e in CEV}: lin_interp(ob)

# ================================================================ まるロボの予定（中の世界）
plan, FR = CP.world_frames(); MK = CP.MARK
def frame_at(t): return FR[min(len(FR) - 1, max(0, int(round(t * FPS))))]
T_STEP_LAND = next(e['t'] for e in plan.events if e['kind'] == 'land' and e['t'] > MK['step'])
T_TOSS = MK['toss'] + 0.05; T_TOSS_LAND = T_TOSS + 0.6
T_WAVE0 = max(T_WAVE[0], T_TOSS_LAND + 0.1)
def torso_frame(f):
    """胴の中心と向き（ワールド）"""
    psi = f['psi']; R = Matrix.Rotation(psi, 3, 'Z') @ Matrix.Rotation(math.radians(-f['pitch']), 3, 'X')
    return Vector(f['root']) + Vector((0, 0, mm.TORSO_Z)), R
def eye_pos(f):
    c, R = torso_frame(f); return c + R @ Vector((0, mm.LENS['y'], mm.LENS['z']))
def head_top(f):
    c, R = torso_frame(f); return c + R @ Vector((0, -0.02, 0.50)), f['psi'], math.radians(-f['pitch'])

# ================================================================ 縦・横の 21 マスの線（「縦に21マス」「横に21マス」）：線が伸びて、目盛りが1つずつ出る
mmat = W.mat_emit('Measure', W.srgb('#14A3B4'), 1.8)
def measure(which, t0, t_hide):
    off = 1.6; z = 0.4; L = N * MOD; grow = 1.6
    bar = W.box('Measure %s' % which, (1, 1, 1), mmat)
    ticks = []
    for k in range(N + 1):
        tk = W.box('tick %s %d' % (which, k), (1.4, 0.22, 0.08) if which == 'v' else (0.22, 1.4, 0.08), mmat)
        tk.location = (-H - off, H - k * MOD, z) if which == 'v' else (-H + k * MOD, H + off, z); ticks.append(tk)
    lab = None
    if FONT:
        cu = bpy.data.curves.new('lab21' + which, 'FONT'); cu.body = '21'; cu.size = 4.2; cu.font = FONT; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
        lab = W.link(O.new('Label 21 ' + which, cu)); lab.data.materials.append(mmat)
        lab.location = (-H - off - 3.4, 0, z) if which == 'v' else (0, H + off + 2.9, z)
    for f in range(fr_of(t0) - 1, fr_of(t0 + grow) + 2):
        u = ease((f - 1) / FPS - t0) if False else min(1.0, max(0.0, ((f - 1) / FPS - t0) / grow)); l = max(0.001, L * u)
        if which == 'v': bar.scale = (0.45, l, 0.08); bar.location = (-H - off, H - l / 2, z)
        else: bar.scale = (l, 0.45, 0.08); bar.location = (-H + l / 2, H + off, z)
        bar.keyframe_insert('scale', frame=f); bar.keyframe_insert('location', frame=f)
    for k, tk in enumerate(ticks):
        ta = t0 + grow * k / N
        for ob, (f, h) in [(tk, x) for x in ((1, True), (fr_of(ta), False), (fr_of(t_hide), True))]: ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)
    for ob, ta in ((bar, t0), (lab, t0 + grow)):
        if ob is None: continue
        for f, h in ((1, True), (fr_of(ta), False), (fr_of(t_hide), True)): ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)
    for ob in [bar] + ticks + ([lab] if lab else []): const_interp(ob) if ob is not bar else None
measure('v', T_VLINE, V[4][0]); measure('h', T_HLINE, V[4][0])

# ================================================================ 目の光で目印を照らす（向き終わった瞬間に光が伸び、目印が赤くなる）
bmat = W.mat_emit('Eye beam', W.srgb('#7FE3F0'), 5.0)
for k, key in enumerate(CP.BEAM_ORDER):
    tb = T_BEAM[k]; f = frame_at(tb); e0 = eye_pos(f); tgt = np.mean([xy(*rc) for rc in FIN_OF[key]], axis=0)
    e1 = Vector((tgt[0], tgt[1], QW.TILE_H + 0.05)); dv = e1 - e0
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.07, depth=1.0, location=(0, 0, 0.5)); bb = bpy.context.object; bb.name = 'Eye beam %s' % key
    bpy.ops.object.transform_apply(location=True); bb.data.materials.append(bmat); bb.visible_shadow = False
    bb.location = e0; bb.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler()
    for ff in range(fr_of(tb) - 1, fr_of(tb + 0.3) + 1):
        u = min(1.0, max(0.0, ((ff - 1) / FPS - tb) / 0.25)); bb.scale = (1, 1, max(0.001, dv.length * u)); bb.keyframe_insert('scale', frame=ff)
    for ff, h in ((1, True), (fr_of(tb), False), (fr_of(tb + 1.1), True)): bb.hide_render = h; bb.keyframe_insert('hide_render', frame=ff)
    tile_state(FIN_OF[key], 'finder', tb + 0.25, ramp=0.2)
    # 光が当たった所に、ぱっと輪
    rm = W.mat_emit('Hit ring', W.srgb('#7FE3F0'), 3.0); ring = W.torus('Hit %s' % key, 1.0, 0.08, rm); ring.location = (tgt[0], tgt[1], QW.TILE_H + 0.12)
    for ff in range(fr_of(tb + 0.25), fr_of(tb + 0.95) + 1):
        u = ((ff - 1) / FPS - tb - 0.25) / 0.7; s = 0.5 + 5.0 * ease(u); ring.scale = (s, s, 1); ring.keyframe_insert('scale', frame=ff)
    for ff, h in ((1, True), (fr_of(tb + 0.25), False), (fr_of(tb + 0.95), True)): ring.hide_render = h; ring.keyframe_insert('hide_render', frame=ff)

# ================================================================ 8マスずつのまとまり：読む順に、1つずつ光って消える → 箱 14 だけ光ったまま
order = [b for b in AS['read_order']] if 'read_order' in AS and isinstance(AS['read_order'][0], int) else list(range(1, 27))
GRP_COL = (W.srgb('#7FE3F0'), W.srgb('#FFD27A'))                # v12 #4：まとまりが見えるよう 2 色を交互に。言い終わるまで光ったまま
for k, b in enumerate(order):
    ta = V[7][0] + 0.4 + k * 0.17
    for rc in BOXES[b]:
        tl = TILES[tuple(rc)]; base = QW.color_for(tl['v'], None)
        color_at(ta, tl, (*QW.mixc(base[:3], GRP_COL[k % 2], 0.55 if not tl['v'] else 0.42), 1.0), 0.12)
        color_at(V[8][0] - 0.1, tl, base, 0.4)
tile_state(BOXES[CP.FOLD_B], 'restored', V[8][0] + 0.3, ramp=0.3)

# ================================================================ 箱：8枚の板（マスの白黒のまま）＋床＋ふた。箱ごとに根元の空の物（BoxRoot）
PANEL, WALL_H, BOXW = 0.7, 0.7, 1.4; Z0 = QW.TILE_H
def panel_targets():
    out = []
    for side, (nx, ny) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        n = Vector((nx, ny, 0)); tv = Vector((-ny, nx, 0))
        for k in (-1, 1):
            out.append((n * (BOXW / 2) + tv * (PANEL / 2 * k) + Vector((0, 0, WALL_H / 2)), math.atan2(ny, nx) - math.pi / 2))
    return out
PT_ = panel_targets()
def panel_color(v, state):
    if state in (None, 'none'): return QW.color_for(v, None)
    base = W.srgb(QW.COL['black'] if v else QW.COL['white']); tint = W.srgb(QW.COL[state])
    if state == 'broken': return (*QW.mixc(base, tint, 0.7), 0.52)          # 壊れた箱：灰色で半分すける（中が読めない）
    return (*QW.mixc(base, tint, 0.45 if v else 0.62), 1.0)
def lid_color(state):
    if state in (None, 'none'): return (0.86, 0.88, 0.90, 1.0)
    if state == 'broken': return (*W.srgb(QW.COL["broken"]), 0.52)
    return (*QW.mixc((0.86, 0.88, 0.90), W.srgb(QW.COL[state]), 0.7), 1.0)
gm = bpy.data.materials.new('Glow'); gm.use_nodes = True; gnt = gm.node_tree; gnt.nodes.clear()
_oi = gnt.nodes.new('ShaderNodeObjectInfo'); _em = gnt.nodes.new('ShaderNodeEmission'); _tr = gnt.nodes.new('ShaderNodeBsdfTransparent'); _mx = gnt.nodes.new('ShaderNodeMixShader'); _out = gnt.nodes.new('ShaderNodeOutputMaterial')
gnt.links.new(_oi.outputs['Color'], _em.inputs['Color']); _em.inputs['Strength'].default_value = 6.0
gnt.links.new(_oi.outputs['Alpha'], _mx.inputs[0]); gnt.links.new(_tr.outputs[0], _mx.inputs[1]); gnt.links.new(_em.outputs[0], _mx.inputs[2]); gnt.links.new(_mx.outputs[0], _out.inputs[0])
try: gm.surface_render_method = 'BLENDED'
except Exception: pass
floor_m = W.mat('Box floor', (0.30, 0.32, 0.35), rough=0.6)
BX = {}
for b, cells in BOXES.items():
    root = W.link(O.new('BoxRoot %d' % b, None)); root.empty_display_size = 0.5; root.location = (CEN[b].x, CEN[b].y, Z0)
    pans = []
    for i, (r, c) in enumerate(cells):
        tl = TILES[(r, c)]; p = W.box('Box %d panel %d' % (b, i), (1, 1, 1), TM, bevel=0.0, seg=1); p.parent = root
        p['v'] = tl['v']; p.color = panel_color(tl['v'], None); pans.append(p)
    fl = W.box('Box %d floor' % b, (BOXW, BOXW, 0.04), floor_m); fl.parent = root; fl.location = (0, 0, 0.02)
    hinge = W.link(O.new('Box %d hinge' % b, None)); hinge.parent = root; hinge.location = (0, 0, WALL_H)
    lid = W.box('Box %d lid' % b, (BOXW + 0.05, BOXW + 0.05, 0.08), TM, bevel=0.02); lid.parent = hinge; lid.location = (0, -(BOXW + 0.05) / 2, 0.04); lid.color = lid_color(None)
    glow = W.box('Box %d glow' % b, (BOXW - 0.1, BOXW - 0.1, 0.02), gm); glow.parent = root; glow.location = (0, 0, WALL_H * 0.72); glow.color = (0, 0, 0, 0); glow.visible_shadow = False
    BX[b] = dict(root=root, pans=pans, floor=fl, hinge=hinge, lid=lid, glow=glow, cells=cells)
def set_hinge_back(b, toward):
    """ふたの蝶番を「toward（のぞく人）から見て奥」に置く。ふたは手前が持ち上がって、中が手前に見える"""
    d = Vector((CEN[b].x - toward[0], CEN[b].y - toward[1], 0.0)); d.normalize(); yaw = math.atan2(-d.x, d.y)   # +Y を d に向ける
    yaw = round(yaw / (math.pi / 2)) * (math.pi / 2); d = Vector((-math.sin(yaw), math.cos(yaw), 0.0))       # ふたは箱の辺にそろえる（90°刻み）
    h = BX[b]['hinge']; h.location = (d.x * BOXW / 2, d.y * BOXW / 2, WALL_H); h.rotation_euler = (0, 0, yaw)
    BX[b]['lid'].location = (0, -(BOXW + 0.05) / 2, 0.04)
set_hinge_back(CP.FOLD_B, CP.P_HOLD); set_hinge_back(11, CP.S1); set_hinge_back(CP.OPEN_DATA, CP.S1); set_hinge_back(CP.OPEN_SPARE, CP.S3)
for b in BOXES:
    if b not in (CP.FOLD_B, 11, CP.OPEN_DATA, CP.OPEN_SPARE): set_hinge_back(b, (CEN[b].x, CEN[b].y - 1.0))

def pose_panels(b, u, f):
    """u=0：マスの位置（平ら）、u=1：箱の壁。読む順に少しずつ遅れて、弧を描いて起き上がる"""
    B = BX[b]; c = CEN[b]
    for i, (r, cc) in enumerate(B['cells']):
        p = B['pans'][i]; p0 = xy(r, cc) - c; p0 = Vector((p0.x, p0.y, 0.0)); p0.z = QW.TILE_H / 2 - Z0 + (0.04 if p['v'] else 0.0)
        p1, rz = PT_[i]; ui = max(0.0, min(1.0, u * 1.6 - i * 0.075)); s = ui * ui * (3 - 2 * ui)
        p.location = p0.lerp(p1, s) + Vector((0, 0, math.sin(math.pi * s) * 1.6))
        sz = (MOD - QW.GAP) * (1 - s) + PANEL * s; p.scale = (sz, sz, QW.TILE_H * (1 - s) + 0.05 * s)
        p.rotation_euler = Euler((math.pi / 2 * s, 0, rz * s), 'XYZ')
        p.hide_render = u <= 0.0
        for dp in ('location', 'scale', 'rotation_euler', 'hide_render'): p.keyframe_insert(dp, frame=f)
    s2 = min(1.0, max(0.0, (u - 0.86) / 0.14))                       # ふたは最後に上から落ちてくる
    B['hinge'].location.z = WALL_H + (1 - ease(s2)) * 0.9; B['hinge'].keyframe_insert('location', index=2, frame=f)
    for ob, vis in ((B['lid'], s2 > 0.0), (B['floor'], u >= 0.999)):
        ob.hide_render = not vis; ob.keyframe_insert('hide_render', frame=f)
def fold_track(b, segs):
    """segs：[(t0, t1, u0, u1)] の区間だけ毎コマのキー。その外は前後の値のまま"""
    pose_panels(b, segs[0][2], 1)
    for t0, t1, u0, u1 in segs:
        for f in range(fr_of(t0) - 1, fr_of(t1) + 2):
            u = u0 + (u1 - u0) * min(1.0, max(0.0, ((f - 1) / FPS - t0) / (t1 - t0))); pose_panels(b, u, f)
for B in BX.values():
    for p in B['pans']: p.hide_render = True
# いつたたむか：14 は T_FOLD、ほかは T_WAVE（14 から近い順に波のように）。最後に全部ひらく（読む順に）
dist14 = sorted([b for b in BOXES if b != CP.FOLD_B and b not in ROBOT_FOLD], key=lambda b: -(CEN[b] - CEN[CP.FOLD_B]).length)   # 遠い箱から波のように、まるロボの近くへ
FOLD_T = {CP.FOLD_B: T_FOLD}
for b in ROBOT_FOLD: FOLD_T[b] = (MK['fold%d' % b] + 0.25, MK['fold%d' % b] + 1.35)     # まるロボが跳び乗った箱：着いてすぐ起き上がる
for k, b in enumerate(dist14):
    a = T_WAVE0 + (T_WAVE[1] - T_WAVE[0] - 1.0) * k / (len(dist14) - 1); FOLD_T[b] = (a, a + 1.0)
UNF_T = {}
for k, b in enumerate(sorted(BOXES)):
    a = T_UNFOLD[0] + (T_UNFOLD[1] - T_UNFOLD[0] - 0.9) * k / 25; UNF_T[b] = (a, a + 0.9)
for b in BOXES:
    fold_track(b, [(FOLD_T[b][0], FOLD_T[b][1], 0.0, 1.0), (UNF_T[b][0], UNF_T[b][1], 1.0, 0.0)])
    tile_state(BOXES[b], None, FOLD_T[b][0], ramp=0.2, alpha=0.22)          # 元のマスは、うっすら跡として残す

# ---------------------------------------------------------------- 箱 14：頭に跳び乗る → 運ばれる → 前へ跳んで元の場所へ
R14 = BX[CP.FOLD_B]['root']
def key_root(f, loc, yaw=0.0, pitch=0.0, sq=1.0):
    R14.location = loc; R14.rotation_euler = Euler((pitch, 0, yaw), 'ZXY' if False else 'XYZ'); R14.scale = (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq)
    R14.keyframe_insert('location', frame=f); R14.keyframe_insert('rotation_euler', frame=f); R14.keyframe_insert('scale', frame=f)
c14 = Vector((CEN[CP.FOLD_B].x, CEN[CP.FOLD_B].y, Z0))
key_root(1, c14)
ta, tl_ = T_CARRY[0], CP.CARRY_LAND
for f in range(fr_of(ta), fr_of(T_TOSS_LAND) + 3):
    t = (f - 1) / FPS
    if t <= tl_:                                                  # 跳び乗る：放物線（高さ 1.4m）・着く前に少し回って向きをそろえる
        u = (t - ta) / (tl_ - ta); hp, yaw, pit = head_top(frame_at(tl_)); loc = c14.lerp(hp, ease(u)) + Vector((0, 0, 1.4 * math.sin(math.pi * u)))
        key_root(f, loc, yaw * ease(u), 0.0)
    elif t <= T_TOSS:                                             # 頭の上（ロボの傾き・向きのまま）
        hp, yaw, pit = head_top(frame_at(t)); sq = 1.0 - 0.10 * math.exp(-(t - tl_) / 0.08) * (1 if t - tl_ < 0.25 else 0)
        key_root(f, hp, yaw, pit, sq)
    else:                                                         # 前へ跳んで元の場所へ（高さ 1.0m）・着いて少しつぶれる
        hp, yaw, pit = head_top(frame_at(T_TOSS)); u = min(1.0, (t - T_TOSS) / (T_TOSS_LAND - T_TOSS))
        loc = hp.lerp(c14, u) + Vector((0, 0, 1.0 * math.sin(math.pi * u))); sq = 1.0
        if t > T_TOSS_LAND: sq = 1.0 - 0.12 * math.exp(-(t - T_TOSS_LAND) / 0.06)
        key_root(f, loc, yaw * (1 - ease(u)), pit * (1 - u), sq)
key_root(fr_of(T_TOSS_LAND) + 6, c14)

# ---------------------------------------------------------------- ふた：のぞく（少し持ち上がる）・開ける（大きく開く）
def lid_key(b, t, ang, f_ease=0.25):
    h = BX[b]['hinge']; f = fr_of(t); h.rotation_euler.x = math.radians(-ang); h.keyframe_insert('rotation_euler', index=0, frame=f)
def lid_move(b, t0, a0, a1, dur):
    lid_key(b, t0, a0); lid_key(b, t0 + dur, a1)
for b in BOXES: lid_key(b, 0.0, 0.0)
lid_move(CP.FOLD_B, MK['peek0'] + 0.5, 0, 28, 0.35); lid_move(CP.FOLD_B, MK['peek0'] + 2.0, 28, 0, 0.3)
lid_move(CP.FOLD_B, MK['peek1'] + 0.45, 0, 28, 0.3); lid_move(CP.FOLD_B, MK['peek1'] + 1.0, 28, 0, 0.25)
lid_move(11, MK['peek2'] + 0.45, 0, 28, 0.3); lid_move(11, MK['peek2'] + 1.0, 28, 0, 0.25)
t_open8 = T_OPEN_DATA; lid_move(CP.OPEN_DATA, t_open8, 0, 112, 0.35)
# 目の光：まるロボが青い箱 8 を向いた瞬間、目から箱へ光が伸びる → ふたが開く
_tb = MK['beam8']; _f = frame_at(_tb + 0.15); _e0 = eye_pos(_f); _e1 = Vector((CEN[CP.OPEN_DATA].x, CEN[CP.OPEN_DATA].y, Z0 + WALL_H + 0.1)); _dv = _e1 - _e0
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.07, depth=1.0, location=(0, 0, 0.5)); b8 = bpy.context.object; b8.name = 'Eye beam box8'
bpy.ops.object.transform_apply(location=True); b8.data.materials.append(bmat); b8.visible_shadow = False; b8.location = _e0; b8.rotation_euler = _dv.to_track_quat('Z', 'Y').to_euler()
_ts = _tb - 1.1                                                     # v12 #7：向きを変えながら光でなでて探す → 箱 8 で止まる
for ff in range(fr_of(_ts) - 1, fr_of(_tb + 0.35) + 1):
    t_ = (ff - 1) / FPS; fr_ = frame_at(t_); e0 = eye_pos(fr_); c_, R_ = torso_frame(fr_)
    if t_ < _tb:
        fwd = (e0 - c_); fwd.z = 0; fwd = fwd.normalized() if fwd.length > 1e-6 else Vector((0, 1, 0)); L_ = min(_dv.length, 3.0 + 6.0 * min(1, (t_ - _ts) / 0.5))
        d_ = fwd * L_ + Vector((0, 0, -0.6))
    else: d_ = _e1 - e0
    b8.location = e0; b8.rotation_euler = d_.to_track_quat('Z', 'Y').to_euler(); b8.scale = (1, 1, max(0.001, d_.length))
    b8.keyframe_insert('location', frame=ff); b8.keyframe_insert('rotation_euler', frame=ff); b8.keyframe_insert('scale', frame=ff)
for ff, h in ((1, True), (fr_of(_ts), False), (fr_of(t_open8 + 0.7), True)): b8.hide_render = h; b8.keyframe_insert('hide_render', frame=ff)
t_open20 = MK['open20'] + 0.22; lid_move(CP.OPEN_SPARE, t_open20, 0, 112, 0.35); lid_move(CP.OPEN_SPARE, T_BLUE - 0.6, 112, 0, 0.4)
lid_move(CP.OPEN_DATA, V[16][0] + 0.5, 112, 0, 0.4)
for b in BOXES:
    ad = BX[b]['hinge'].animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BACK' if False else 'BEZIER'

# ---------------------------------------------------------------- 中身の箱：開けると中が青く光る → 光が残り 8 個へ（近い順）→ 箱が青に
BLUE = (*W.srgb('#7FB3FF'), 1.0); OFF = (0, 0, 0, 0)
def glow_at(b, t, rgba, ramp=0.2): color_at(t, BX[b]['glow'], rgba, ramp)
def box_state(b, state, t, ramp=0.25):
    for p in BX[b]['pans']: color_at(t, p, panel_color(p['v'], state), ramp)
    color_at(t, BX[b]['lid'], lid_color(state), ramp)
glow_at(CP.OPEN_DATA, t_open8 + 0.1, (*BLUE[:3], 0.95), 0.3); box_state(CP.OPEN_DATA, 'data', t_open8 + 0.2)
pl = bpy.data.lights.new('Box8 light', 'POINT'); pl.color = BLUE[:3]; pl.shadow_soft_size = 0.4
plo = W.link(O.new('Box8 light', pl)); plo.location = (CEN[CP.OPEN_DATA].x, CEN[CP.OPEN_DATA].y, Z0 + 1.2)
for t, e in ((0, 0), (t_open8, 0), (t_open8 + 0.4, 900), (V[16][0] + 0.5, 900), (V[16][0] + 0.9, 0)): pl.energy = e; pl.keyframe_insert('energy', frame=fr_of(t))
others = sorted([b for b in DATA if b != CP.OPEN_DATA], key=lambda b: (CEN[b] - CEN[CP.OPEN_DATA]).length)
for k, b in enumerate(others):
    ta = T_SPREAD[0] + (T_SPREAD[1] - T_SPREAD[0]) * k / (len(others) - 1)
    glow_at(b, ta, (*BLUE[:3], 0.9), 0.12); glow_at(b, ta + 0.5, OFF, 0.5); box_state(b, 'data', ta)
    # v12 #7：ほかの箱のふたは開けない（光が届いて青くなるだけ）
    BX[b]['glow'].location.z = WALL_H + 0.12
glow_at(CP.OPEN_DATA, V[16][0] + 0.6, OFF, 0.4)
for b in DATA: glow_at(b, T_BOX9, (*BLUE[:3], 0.85), 0.12); glow_at(b, T_BOX9 + 0.7, OFF, 0.5)     # 「箱の数は…」：9 個の箱がぱっと光る
# 光が箱から箱へ飛ぶ（小さな光の玉）
om = W.mat_emit('Orb', BLUE[:3], 8.0)
for k, b in enumerate(others):
    ta = T_SPREAD[0] + (T_SPREAD[1] - T_SPREAD[0]) * k / (len(others) - 1); src = CEN[CP.OPEN_DATA]; dst = CEN[b]; t0 = ta - 0.45
    orb = W.box('Orb %d' % b, (0.35, 0.35, 0.35), om, bevel=0.17, seg=4); orb.visible_shadow = False
    for f in range(fr_of(t0), fr_of(ta) + 1):
        u = ((f - 1) / FPS - t0) / 0.45; u = min(1, max(0, u))
        orb.location = Vector((src.x, src.y, Z0 + 1.0)).lerp(Vector((dst.x, dst.y, Z0 + 0.9)), ease(u)) + Vector((0, 0, 2.2 * math.sin(math.pi * u))); orb.keyframe_insert('location', frame=f)
    for f, h in ((1, True), (fr_of(t0), False), (fr_of(ta) + 1, True)): orb.hide_render = h; orb.keyframe_insert('hide_render', frame=f)

# ---------------------------------------------------------------- HELLO の文字（中身の箱の上に浮かぶ）
hello = None
if FONT:
    cu = bpy.data.curves.new('HELLO', 'FONT'); cu.body = 'HELLO'; cu.size = 4.2; cu.font = FONT; cu.align_x = 'CENTER'; cu.extrude = 0.12
    hello = W.link(O.new('HELLO', cu)); hello.data.materials.append(W.mat_emit('HELLO m', W.srgb('#9CC8FF'), 2.4))
    dc = np.mean([CEN[b] for b in DATA], axis=0); hello.location = (dc[0] - 1.0, dc[1] + 1.0, 4.2)
    camdir = Vector((16.5, -21.3, 6.5)) - Vector((dc[0] - 1.0, dc[1] + 1.0, 4.2)); hello.rotation_euler = (math.radians(80), 0, math.atan2(camdir.x, -camdir.y) * 1.0)
    for f in range(fr_of(T_HELLO) - 1, fr_of(T_HELLO + 0.5) + 1):
        u = min(1.0, max(0.0, ((f - 1) / FPS - T_HELLO) / 0.45)); s = max(0.001, ease(u) * (1 + 0.15 * math.sin(math.pi * u))); hello.scale = (s, s, s); hello.keyframe_insert('scale', frame=f)
    for f, h in ((1, True), (fr_of(T_HELLO), False), (fr_of(V[18][0]), True)): hello.hide_render = h; hello.keyframe_insert('hide_render', frame=f)

# ---------------------------------------------------------------- 冒頭でまるロボが乗っていた所：影が落ち、その下の箱が灰色に → 「残りの17個」で戻る
st = AS['experiments']['robot_stand']; sc_ = MOD / OPT.MOD; rr, cc_ = st['center_rc']
sh_c = Vector(CP.xy(rr - 0.5, cc_ - 0.5)); ex, ey = [m * MOD for m in st['ellipse_modules']]
shm = bpy.data.materials.new('Robot shadow'); shm.use_nodes = True; snt = shm.node_tree; snt.nodes.clear()
s_tc = snt.nodes.new('ShaderNodeTexCoord'); s_gr = snt.nodes.new('ShaderNodeTexGradient'); s_gr.gradient_type = 'SPHERICAL'
s_mp = snt.nodes.new('ShaderNodeMapRange'); s_mp.inputs['From Min'].default_value = 0.0; s_mp.inputs['From Max'].default_value = 0.25
s_oi = snt.nodes.new('ShaderNodeObjectInfo'); s_mul = snt.nodes.new('ShaderNodeMath'); s_mul.operation = 'MULTIPLY'
s_em = snt.nodes.new('ShaderNodeEmission'); s_em.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1); s_tr = snt.nodes.new('ShaderNodeBsdfTransparent'); s_mx = snt.nodes.new('ShaderNodeMixShader')
s_o = snt.nodes.new('ShaderNodeOutputMaterial')
snt.links.new(s_tc.outputs['Object'], s_gr.inputs['Vector']); snt.links.new(s_gr.outputs['Fac'], s_mp.inputs['Value'])
snt.links.new(s_mp.outputs['Result'], s_mul.inputs[0]); snt.links.new(s_oi.outputs['Alpha'], s_mul.inputs[1]); snt.links.new(s_mul.outputs[0], s_mx.inputs[0])
snt.links.new(s_tr.outputs[0], s_mx.inputs[1]); snt.links.new(s_em.outputs[0], s_mx.inputs[2]); snt.links.new(s_mx.outputs[0], s_o.inputs[0])
try: shm.surface_render_method = 'BLENDED'
except Exception: pass
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type='NGON', location=(0, 0, 0)); shadow = bpy.context.object; shadow.name = 'Robot shadow'
shadow.data.materials.append(shm); shadow.scale = (ex / 2, ey / 2, 1); shadow.location = (sh_c.x, sh_c.y, Z0 + WALL_H + 0.25); shadow.visible_shadow = False
shadow.color = (1, 1, 1, 0)
rim = W.torus('Shadow rim', 1.0, 0.012, W.mat_emit('Shadow rim m', W.srgb('#C9D3DC'), 1.2), seg=96); rim.location = shadow.location + Vector((0, 0, 0.02)); rim.scale = (ex / 2 * 0.92, ey / 2 * 0.92, 1); rim.visible_shadow = False
for f, h in ((1, True), (fr_of(T_SHADOW + 0.3), False), (fr_of(V[21][0]), True)): rim.hide_render = h; rim.keyframe_insert('hide_render', frame=f)
color_at(T_SHADOW - 0.1, shadow, (1, 1, 1, 0.0), 0.05); color_at(T_SHADOW, shadow, (1, 1, 1, 0.78), 0.6); color_at(V[21][0], shadow, (1, 1, 1, 0.0), 0.6)
for k, b in enumerate(st['bad_boxes']):
    box_state(b, 'broken', T_SHADOW + 0.7 + 0.12 * k, 0.25)
    box_state(b, 'data' if b in DATA else None, V[21][0] + 0.2, 0.4)

# ---------------------------------------------------------------- 予備の箱 20：文字はない。代わりに、中身の 9 個の箱から計算した数字（この箱の本当の値）の札が浮かぶ
if FONT:
    val = SYM['box_bytes'][CP.OPEN_SPARE - 1]
    cu = bpy.data.curves.new('Spare num', 'FONT'); cu.body = str(val); cu.size = 2.6; cu.font = FONT; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = 0.08
    num = W.link(O.new('Spare number', cu)); num.data.materials.append(W.mat_emit('Spare num m', W.srgb('#F0953A'), 3.0))
    card = W.box('Spare num card', (4.2, 2.7, 0.08), W.mat('Spare card m', (0.98, 0.95, 0.90), rough=0.5), bevel=0.05); card.parent = num; card.location = (0, 0, -0.1)
    num.rotation_euler = (math.radians(90), 0, math.radians(-22.6)); c20_ = CEN[CP.OPEN_SPARE]
    for f in range(fr_of(T_NUMBER) - 1, fr_of(T_NUMBER + 1.2) + 1):
        u = ease(((f - 1) / FPS - T_NUMBER) / 1.2); num.location = (c20_.x, c20_.y, Z0 + 0.6 + 3.2 * u); s_ = max(0.001, 0.3 + 0.7 * u); num.scale = (s_, s_, s_)
        num.keyframe_insert('location', frame=f); num.keyframe_insert('scale', frame=f)
    for f, h in ((1, True), (fr_of(T_NUMBER), False), (fr_of(V[24][0] + 0.5), True)):
        for ob in (num, card): ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)
# 中身の 9 個の箱から予備の箱へ、細い光の線（計算して作った数字だと分かるように）
lm9 = W.mat_emit('Calc line', W.srgb('#9CC8FF'), 2.5)
for k, b in []:                                                      # v12 #11：線はやめた（下の光の玉に）
    a_ = Vector((CEN[b].x, CEN[b].y, Z0 + WALL_H + 0.2)); b_ = Vector((CEN[CP.OPEN_SPARE].x, CEN[CP.OPEN_SPARE].y, Z0 + WALL_H + 0.6)); dv = b_ - a_
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.05, depth=1.0, location=(0, 0, 0.5)); ln = bpy.context.object; ln.name = 'Calc line %d' % b
    bpy.ops.object.transform_apply(location=True); ln.data.materials.append(lm9); ln.visible_shadow = False; ln.location = a_; ln.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler()
    t0 = T_NUMBER - 0.9 + 0.08 * k
    for f in range(fr_of(t0) - 1, fr_of(t0 + 0.7) + 1):
        u = min(1.0, max(0.0, ((f - 1) / FPS - t0) / 0.6)); ln.scale = (1, 1, max(0.001, dv.length * ease(u))); ln.keyframe_insert('scale', frame=f)
    for f, h in ((1, True), (fr_of(t0), False), (fr_of(T_NUMBER + 2.4), True)): ln.hide_render = h; ln.keyframe_insert('hide_render', frame=f)

# v12 #11：中身の 9 個の箱から、光の玉が予備の箱 20 へ順に流れ込む（「文字の箱をもとに計算した数字」）。着くたびに箱 20 が橙に光る
om20 = W.mat_emit('Orb20', W.srgb('#9CC8FF'), 8.0); c20 = CEN[CP.OPEN_SPARE]
TRAVEL = 0.95                                                      # 試し描きで玉が小さく見えにくかった → 大きく・ゆっくり・尾（遅れて追う小さな玉 3 つ）
for k, b in enumerate(DATA):
    t0 = T_NUMBER - 2.0 + 0.16 * k; src = CEN[b]
    glow_at(b, t0 - 0.05, (*W.srgb('#9CC8FF'), 0.85), 0.08); glow_at(b, t0 + 0.5, OFF, 0.4)     # 玉が出る箱がぱっと光る
    for j, (sz, lag) in enumerate(((0.62, 0.0), (0.42, 0.05), (0.30, 0.10), (0.20, 0.15))):
        orb = W.box('Orb to 20 %d %d' % (b, j), (sz, sz, sz), om20, bevel=sz / 2, seg=4); orb.visible_shadow = False
        for f in range(fr_of(t0 + lag), fr_of(t0 + lag + TRAVEL) + 1):
            u = min(1, max(0, ((f - 1) / FPS - t0 - lag) / TRAVEL))
            orb.location = Vector((src.x, src.y, Z0 + 1.0)).lerp(Vector((c20.x, c20.y, Z0 + 0.8)), ease(u)) + Vector((0, 0, 2.8 * math.sin(math.pi * u))); orb.keyframe_insert('location', frame=f)
        for f, h in ((1, True), (fr_of(t0 + lag), False), (fr_of(t0 + lag + TRAVEL) + 1, True)): orb.hide_render = h; orb.keyframe_insert('hide_render', frame=f)
glow_at(CP.OPEN_SPARE, T_NUMBER - 0.9, (*W.srgb('#F0953A'), 0.9), 0.4); glow_at(CP.OPEN_SPARE, T_NUMBER + 2.6, OFF, 0.6)
# ---------------------------------------------------------------- 予備の箱 20：開けると空っぽ（「予備」で中がうすく橙に）
ORG = (*W.srgb('#F0953A'), 1.0)
glow_at(CP.OPEN_SPARE, V[23][0] + 3.6, (*ORG[:3], 0.55), 0.5); glow_at(CP.OPEN_SPARE, T_BLUE - 0.6, OFF, 0.4)
# ---------------------------------------------------------------- 青と橙で表す：「青」で中身の箱がぱっと光る、「橙」で予備の箱が近い順に橙へ
for b in DATA: glow_at(b, T_BLUE, (*BLUE[:3], 0.8), 0.12); glow_at(b, T_BLUE + 0.6, OFF, 0.5)
spare_ord = sorted(SPARE, key=lambda b: (CEN[b] - CEN[CP.OPEN_SPARE]).length)
for k, b in enumerate(spare_ord):
    ta = T_ORANGE + 1.2 * k / (len(spare_ord) - 1); box_state(b, 'spare', ta, 0.2); glow_at(b, ta, (*ORG[:3], 0.7), 0.1); glow_at(b, ta + 0.4, OFF, 0.4)
for b in BOXES: BX[b]['glow'].location.z = WALL_H + 0.12 if b not in (CP.OPEN_DATA, CP.OPEN_SPARE) else WALL_H * 0.72
# ---------------------------------------------------------------- 元のマスに戻る：役割の色（目印＝赤・中身＝青・予備＝橙）
for b in BOXES: tile_state(BOXES[b], 'data' if b in DATA else 'spare', UNF_T[b][1] - 0.1, ramp=0.25)
bake_colors()

# ================================================================ まるロボ（本物：story.blend の「Maru」に marurig で予定を当てる）
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

# ================================================================ カメラ（カットごと。タイムラインの印で切り替える）
S_ = 1.0 / OPT.MOD * MOD                                 # 卓上 → 中の世界の大きさの比（11.5 倍）
PH_LOC = Vector(OPT.LENS) * S_; PH_AIM = Vector(OPT.AIM) * S_
C = lambda *v: Vector(v)
pland = Vector((CP.P_LAND[0], CP.P_LAND[1], 0)); c14v = C(CEN[14].x, CEN[14].y, 0); c8 = C(CEN[8].x, CEN[8].y, 0); c20 = C(CEN[20].x, CEN[20].y, 0)
pb = Vector((CP.P_BEAM[0], CP.P_BEAM[1], 0))
VIEWS = {
    'land': (pland + C(3.2, -4.6, 1.5), C(-H * 0.3, H * 0.5, 2.5), 18),
    'tile': (pland + C(2.8, -3.3, 1.35), pland + C(-0.5, 0.7, 0.3), 24),       # 足もとすれすれ：マスがまるロボより大きい
    'top': (C(-1.2, 1.19, 70), C(-1.2, 1.2, 0), 32),
    'beam': (C(14.0, -20.0, 9.0), C(1.8, -4.2, 0.0), 22),        # 目印 3 つとまるロボが全部入る
    'top2': (C(0, -0.01, 64), C(0, 0, 0), 32),
    'look': (pb + C(-4.4, -1.6, 1.5), pb + C(0, 0, 0.95), 28),
    'groups': (C(10, -30, 27), C(0, -1.5, 0), 26),
    'fold': (c14v + C(6.2, -8.2, 4.4), c14v + C(-0.2, -1.2, 0.7), 28),
    'carry': (C(8.2, -10.4, 2.4), C(2.6, -8.6, 1.4), 30),
    'wave': (C(H * 0.9, -H * 1.2, 9.0), C(-H * 0.1, H * 0.2, 0.0), 22),
    'peek0': (C(6.4, -12.2, 2.1), C(2.5, -7.8, 0.8), 30),
    'row': (C(5.2, -17.5, 4.8), C(5.0, -7.2, 0.6), 30),
    'open': (c8 + C(3.6, -4.4, 3.0), c8 + C(-0.3, 0.4, 0.6), 30),
    'hello': (C(H * 1.05, -H * 1.35, 6.5), C(8.0, -5.0, 3.2), 22),
    'high': (C(0, -0.01, 70), C(0, 0, 0), 32),
    'shadow': (C(H * 0.6, -H * 1.3, 16), C(H * 0.45, -H * 0.45, 0), 26),
    'follow': (C(9.5, -12.5, 4.5), None, 26),
    'spare': (c20 + C(-0.3, -5.0, 2.4), c20 + C(0.4, 0.0, 0.7), 30),
    'number': (C(-7.5, -17.0, 13.0), C(4.5, -5.0, 1.6), 26),     # 中身の 9 個の箱から予備の箱へ線、数字の札が浮かぶ
    'wave2': (C(10.5, -17.5, 7.0), C(3.2, -8.8, 0.4), 26),       # まるロボが最後の 2 個に跳び乗る（奥で波のようにたたまれていく）
    'roles': (C(H * 0.95, -H * 1.25, 9.0), C(-H * 0.1, H * 0.2, 0.0), 22),
    'low': (C(5.8, -9.8, 2.3), C(-10.5, 10.5, 1.2), 24),
    'unfold': (C(14, -22, 14), C(-1.0, 1.0, 0.0), 22),
}
TE = T_TABLE_END
SHOTS_W = [(TE, T_LAND + 0.7, 'dive', 0, 0), (T_LAND + 0.7, V[2.5][0] + 0.2, 'land', 0.0, 0.04), (V[2.5][0] + 0.2, V[3][0], 'tile', 0.0, 0.06), (V[3][0], T_BEAM[0] - 1.2, 'top', 0.0, 0.04),
           (T_BEAM[0] - 1.2, T_BEAM[2] + 1.2, 'beam', 0.0, 0.05), (T_BEAM[2] + 1.2, V[6][0], 'top2', 0.0, 0.03), (V[6][0], V[7][0], 'look', 0.0, 0.08),
           (V[7][0], V[8][0] + 0.3, 'groups', 0.0, 0.04), (V[8][0] + 0.3, MK['catch'] + 0.6, 'fold', 0.0, 0.10), (MK['catch'] + 0.6, T_WAVE0, 'carry', 0.0, 0.06),     # v12 #5：跳び乗るのを引きで見せてから
           (T_WAVE0, T_WAVE0 + 1.0, 'wave', 0.0, 0.03), (T_WAVE0 + 1.0, V[12][0] + 0.6, 'wave2', 0.0, 0.06), (V[12][0] + 0.6, T_PEEK[0] - 0.8, 'peek0', 0.0, 0.06), (T_PEEK[0] - 0.8, t_open8 + 0.45, 'row', 0.0, 0.07),
           (t_open8 + 0.45, T_SPREAD[0] + 0.1, 'open', 0.0, 0.05), (T_SPREAD[0] + 0.1, V[16][0], 'hello', 0.0, 0.05), (V[16][0], V[19][0], 'high', 0.0, 0.05),
           (V[19][0], V[21][0], 'shadow', 0.0, 0.08), (V[21][0], t_open20 - 1.0, 'follow', 0, 0), (t_open20 - 1.0, T_NUMBER - 1.0, 'spare', 0.0, 0.06), (T_NUMBER - 1.0, T_BLUE - 0.8, 'number', 0.0, 0.05),
           (T_BLUE - 0.8, V[25][0], 'roles', 0.0, 0.05), (V[25][0], T_UNFOLD[0] - 0.3, 'low', 0.0, 0.12), (T_UNFOLD[0] - 0.3, T_END, 'unfold', 0.0, 0.04)]
def look_rot(loc, look, up_world=True): return (look - loc).to_track_quat('-Z', 'Y').to_euler()
def new_cam(name, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 900; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    return W.link(O.new(name, cd))
for k, (t0, t1, v, d0, d1) in enumerate(SHOTS_W):
    cam = new_cam('Cam %02d %s' % (k, v), 30)
    if v == 'dive':                                       # スマホのカメラと同じ所・向き（卓上の画面の絵とつながる）→ 降りてくるまるロボの方へ
        L1, T1, lens1 = VIEWS['land']; f_a, f_b = fr_of(t0), fr_of(t1)
        for f in range(f_a, f_b + 1):
            u = ease(((f - 1) / FPS - t0) / (t1 - t0)) ** 0.9
            loc = PH_LOC.lerp(L1, u); look = PH_AIM.lerp(T1, u); cam.location = loc; cam.rotation_euler = look_rot(loc, look)
            cam.data.lens = 34 + (lens1 - 34) * u
            cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f); cam.data.keyframe_insert('lens', frame=f)
    elif v == 'follow':                                   # 走るまるロボを、ゆっくり首を振って追う
        L, _, lens = VIEWS[v]; cam.location = L; cam.data.lens = lens; prev = None
        for f in range(fr_of(t0), fr_of(t1) + 1, 2):
            rp = Vector(frame_at((f - 1) / FPS)['root']) + Vector((0, 0, 0.9)); prev = rp if prev is None else prev.lerp(rp, 0.35)
            cam.rotation_euler = look_rot(L, prev); cam.keyframe_insert('rotation_euler', frame=f)
    else:
        L, T, lens = VIEWS[v]; cam.data.lens = lens; cam.rotation_euler = look_rot(L, T)
        for t, dd in ((t0, d0), (t1, d1)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    m = sc.timeline_markers.new('w%02d %s' % (k, v), frame=fr_of(t0)); m.camera = cam
    if k == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=A.save)
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f)
        for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
            if m.frame <= f: sc.camera = m.camera
        sc.render.filepath = os.path.join(A.out, 'w_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); sc.render.filepath = os.path.join(A.out, 'w_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], events=[e for e in plan.events if e['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_happy', 'beep_yes', 'beep_no', 'beep_surprise', 'ding')],
               marks=MK, shots=[(a, b, v) for a, b, v, _, _ in SHOTS_W], fold=FOLD_T, unfold=UNF_T, t_open8=t_open8, t_open20=t_open20, toss=T_TOSS, toss_land=T_TOSS_LAND,
               beams=T_BEAM, step_land=T_STEP_LAND), open(os.path.join(A.out, 'qrc1w_log.json'), 'w'), default=float, indent=0)
print('QRC1W DONE', F0, F1)
