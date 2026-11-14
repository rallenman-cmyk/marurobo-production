# QRコード回・4章「直す」の QR の大地（G9・G6・W23・W26・B28a〜d）の本番描画（PC・Blender 4.3.2・EEVEE）。台本 v2.0 の時刻
#   blender -b --factory-startup --python qr_c4_world.py -- --blend story.blend --out DIR --frames 1:303 --video 1 --vprefix qrc4w_
#   確認用：--standin 1（仮のまるロボ）。--still 100,3200 で指定のコマだけ PNG
#   3D の中に字は書かない（「？」「HELLO」は 2D の札・赤い輪で）
#   状態は場面の切り替えで変える：前半（G9・G6）＝右の白いフチに 9 個の箱が並ぶ／W23・W26＝平らな大地／B28＝26 個すべてが箱（壊れた 6 個は灰色）
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Euler, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import qr_world as QW
import c4_plan as CP
from c4_plan import FPS, s, e, fr_of, rc, H, MOD
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc4w'); ap.add_argument('--frames', default='1:%d' % fr_of(CP.WORLD_RANGES[0][1]))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc4w_'); ap.add_argument('--standin', type=int, default=0)
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
    keys = [(1, True)]
    for a, b in spans: keys += [(max(2, fr_of(a)), False), (fr_of(b), True)]
    for f, h in keys: ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)
    interp(ob, 'CONSTANT', only='hide')
def keys(ob, path, pts, kind='BEZIER'):
    for t, v in pts: setattr(ob, path, v); ob.keyframe_insert(path, frame=fr_of(t))
    interp(ob, kind, only=path)

# ================================================================ 場面の切り替えの時刻
T_LAND = CP.shot_start('W23')                           # ここから平らな大地
T_B28 = CP.shot_start('B28a')                           # ここから 26 個すべてが箱
G9_SPANS = [(0.0, CP.shot_start('F1')), (CP.shot_start('G9', 40.0), CP.shot_start('C1'))]
G6_SPAN = (CP.shot_start('G6'), CP.shot_start('c4_bignum'))
W23_SPAN = (T_LAND, CP.shot_start('c4_bits0')); W26_SPAN = (CP.shot_start('W26'), CP.shot_start('D5c'))

# ================================================================ 大地
Wd = QW.build(); coll = Wd['coll']; QW.lights_c(sc, coll)
AS = Wd['assets']; SYM = Wd['symbol']; TILES = Wd['tiles']; TM = TILES[(0, 0)].data.materials[0]
DATA = list(SYM['data_boxes']); SPARE = list(SYM['spare_boxes'])
QW.paint(Wd, QW.cells_of(Wd, 'finder'), 'finder'); QW.paint(Wd, QW.cells_of(Wd, 'data'), 'data'); QW.paint(Wd, QW.cells_of(Wd, 'spare'), 'spare')
BOX_CELLS = {int(b): [tuple(x) for x in cs] for b, cs in AS['boxes'].items()}
CEV = []
def color_at(t, ob, rgba, ramp=0.15): CEV.append((t, ob, tuple(rgba), ramp))
def bake_colors():
    last = {}
    for t, ob, c, ramp in sorted(CEV, key=lambda x: x[0]):
        f = fr_of(t); prev = last.get(ob.name, tuple(ob.color))
        ob.color = prev; ob.keyframe_insert('color', frame=f)
        ob.color = c; ob.keyframe_insert('color', frame=f + max(1, int(round(ramp * FPS))))
        last[ob.name] = c
    for ob in {x[1] for x in CEV}: interp(ob, 'LINEAR', only='color')
def role(b): return 'data' if b in DATA else 'spare'
def tiles_alpha(boxes, t, alpha):
    for b in boxes:
        for rc_ in BOX_CELLS[b]: tl = TILES[rc_]; c = list(QW.color_for(tl['v'], role(b))); c[3] = alpha; color_at(t, tl, c, 0.02)
tiles_alpha(DATA + SPARE, 0.0, 0.22)                     # 前半：中身の 9 個は箱になって右のフチへ・予備の 17 個はその場で箱（v12 #54。マスは跡）
tiles_alpha(DATA + SPARE, T_LAND - 0.05, 1.0)             # 平らな大地
tiles_alpha(DATA + SPARE, T_B28 - 0.05, 0.22)            # 26 個すべてが箱（マスは跡）

# ================================================================ 箱 26 個（8 枚の板＋床＋ふた）
PANEL, WALL_H, BOXW = 0.7, 0.7, 1.4; Z0 = QW.TILE_H
PT_ = []
for side, (nx, ny) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
    n = Vector((nx, ny, 0)); tv = Vector((-ny, nx, 0))
    for k in (-1, 1): PT_.append((n * (BOXW / 2) + tv * (PANEL / 2 * k) + Vector((0, 0, WALL_H / 2)), math.atan2(ny, nx) - math.pi / 2))
def panel_color(v, state):
    base = W.srgb(QW.COL['black'] if v else QW.COL['white']); tint = W.srgb(QW.COL[state])
    if state == 'broken': return (*QW.mixc(base, tint, 0.7), 0.52)
    if state == 'restored': return (*QW.mixc(base, tint, 0.55), 0.75)
    return (*QW.mixc(base, tint, 0.45 if v else 0.62), 1.0)
def lid_color(state):
    if state == 'broken': return (*W.srgb(QW.COL['broken']), 0.52)
    if state == 'restored': return (*QW.mixc((0.86, 0.88, 0.90), W.srgb(QW.COL['restored']), 0.7), 0.75)
    return (*QW.mixc((0.86, 0.88, 0.90), W.srgb(QW.COL[state]), 0.7), 1.0)
floor_m = W.mat('Box floor', (0.30, 0.32, 0.35), rough=0.6)
BX = {}; CEN = {}
for b, cells in BOX_CELLS.items():
    CEN[b] = Vector((sum(rc(*x)[0] for x in cells) / 8, sum(rc(*x)[1] for x in cells) / 8, 0))
    root = W.link(O.new('BoxRoot %d' % b, None)); pans = []
    for i, (r, c) in enumerate(cells):
        p = W.box('Box %d panel %d' % (b, i), (1, 1, 1), TM, bevel=0.0, seg=1); p.parent = root; p['v'] = TILES[(r, c)]['v']; p.color = panel_color(p['v'], role(b)); pans.append(p)
    fl = W.box('Box %d floor' % b, (BOXW, BOXW, 0.04), floor_m); fl.parent = root; fl.location = (0, 0, 0.02)
    hinge = W.link(O.new('Box %d hinge' % b, None)); hinge.parent = root; hinge.location = (BOXW / 2, 0, WALL_H); hinge.rotation_euler = (0, 0, math.radians(-90))
    lid = W.box('Box %d lid' % b, (BOXW + 0.05, BOXW + 0.05, 0.08), TM, bevel=0.02); lid.parent = hinge; lid.location = (0, -(BOXW + 0.05) / 2, 0.04); lid.color = lid_color(role(b))
    BX[b] = dict(root=root, pans=pans, floor=fl, hinge=hinge, lid=lid)
def pose(b, u, t, loc):
    """場面の切り替えで、箱 b を u（0＝平らなマス・1＝箱）にして loc に置く"""
    f = max(1, fr_of(t)); B = BX[b]; c = CEN[b]
    B['root'].location = loc; B['root'].keyframe_insert('location', frame=f)
    for i, (r, cc) in enumerate(BOX_CELLS[b]):
        p = B['pans'][i]; p1, rz = PT_[i]
        if u >= 1.0: p.location = p1; p.scale = (PANEL, PANEL, 0.05); p.rotation_euler = Euler((math.pi / 2, 0, rz), 'XYZ')
        p.hide_render = u < 1.0
        for dp in ('location', 'scale', 'rotation_euler', 'hide_render'): p.keyframe_insert(dp, frame=f)
    for ob in (B['lid'], B['floor']): ob.hide_render = u < 1.0; ob.keyframe_insert('hide_render', frame=f)
ROWZ = CP.QZ_TOP - 0.01
for b in BOX_CELLS:
    inplace = Vector((CEN[b].x, CEN[b].y, Z0))
    if b in DATA:
        k = DATA.index(b); rp = CP.row_pos(k); pose(b, 1.0, 0.0, Vector((rp[0], rp[1], ROWZ)))
    else: pose(b, 1.0, 0.0, inplace)                     # v12 #54：予備は「箱」の形で光らせる（マスではなく）
    pose(b, 0.0, T_LAND - 0.05, inplace)
    pose(b, 1.0, T_B28 - 0.05, inplace)
for B in BX.values():
    for ob in [B['root']] + B['pans']: interp(ob, 'CONSTANT')
# 前半：最初の箱のふたは開いたまま。B28 では閉じる
h1 = BX[DATA[0]]['hinge']; keys(h1, 'rotation_euler', [(0.0, (math.radians(-112), 0, math.radians(-90))), (T_B28 - 0.05, (0, 0, math.radians(-90)))], kind='CONSTANT')
# 前半：予備の 17 個の箱が、ふたの上でゆっくり光る（G9。v12 #54：17 個と数が合うよう、1 箱に 1 つの光）
gm = W.mat_emit('spare glow', W.srgb('#FFD29A'), 5.0)
for b in SPARE:
    g = W.box('sg box %d' % b, (BOXW * 0.86, BOXW * 0.86, 0.05), gm, bevel=0.1); g.location = (CEN[b].x, CEN[b].y, Z0 + WALL_H + 0.16); g.visible_shadow = False
    for k in range(int(G9_SPANS[-1][1])):
        g.scale = (0.75, 0.75, 1); g.keyframe_insert('scale', frame=fr_of(k * 1.0)); g.scale = (1.0, 1.0, 1); g.keyframe_insert('scale', frame=fr_of(k * 1.0 + 0.5))
    show(g, G9_SPANS)
# 前半：0 と 1 の板（G6。字なし）
bits = format(SYM['box_bytes'][0], '08b'); c0 = Vector((*CP.row_pos(0), ROWZ))
bm = {'1': W.mat('bit black', W.srgb(QW.COL['black']), rough=0.5), '0': W.mat_emit('bit white', W.srgb('#E9EEF2'), 1.2)}
for k, bch in enumerate(bits):
    pl = W.box('bit %d' % k, (0.54, 0.06, 0.66), bm[bch]); pl.location = (c0.x - 3.5 * 0.62 + k * 0.62, c0.y + 0.2, 2.35); show(pl, [G6_SPAN])
gl = W.box('Glow', (1.2, 1.2, 0.05), W.mat_emit('Glow m', W.srgb('#9CC8FF'), 5.0)); gl.location = c0 + Vector((0, 0, 0.4)); show(gl, [G6_SPAN])

# ================================================================ W23：白いマスに黒い汚れが落ちる（黒いマスに見える）
stain_m = W.mat('stain', (0.01, 0.012, 0.014), rough=0.15, coat=0.6)
def blob(name, xy, rx, ry, rz, m, seed, t_fall=None, z_top=QW.TILE_H + 0.03):
    import random; rnd = random.Random(seed); root = W.link(O.new(name, None)); root.location = (xy[0], xy[1], z_top)
    for k in range(7):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); o = bpy.context.object; o.name = '%s %d' % (name, k); o.data.materials.append(m); o.parent = root
        dx = rnd.uniform(-0.45, 0.45) * rx if k else 0; dy = rnd.uniform(-0.45, 0.45) * ry if k else 0; sc_ = rnd.uniform(0.45, 0.8) if k else 1.0
        o.location = (dx, dy, 0); o.scale = (rx * sc_, ry * sc_, rz)
    if t_fall is not None:
        keys(root, 'location', [(t_fall, (xy[0], xy[1], z_top + 4.0)), (t_fall + 0.45, (xy[0], xy[1], z_top))], kind='LINEAR')
        keys(root, 'scale', [(t_fall, (0.5, 0.5, 6.0)), (t_fall + 0.45, (0.5, 0.5, 6.0)), (t_fall + 0.6, (1, 1, 1))])
    return root
st23 = blob('stain23', CP.W23_XY, MOD * 0.52, MOD * 0.5, 0.03, stain_m, 2, t_fall=CP.T_STAIN_W)
for ob in hier(st23): show(ob, [(CP.T_STAIN_W, W23_SPAN[1])]) if ob.type == 'MESH' else None
# ================================================================ W26：体で隠れたマス（灰色）と、汚れたマス。どちらにも赤い輪
for rc_ in AS['experiments']['robot_stand']['covered']:
    tl = TILES[tuple(rc_)]; color_at(W26_SPAN[0] - 0.05, tl, QW.color_for(0, 'broken'), 0.02); color_at(W26_SPAN[1], tl, QW.color_for(tl['v'], role(tl['box']) if tl['box'] else None), 0.02)
sx, sy = rc(10, 10)
st26 = blob('stain26', (sx, sy), MOD * 1.2, MOD * 1.0, 0.03, W.mat('stain matte', (0.01, 0.012, 0.014), rough=0.9), 4)
for ob in hier(st26): show(ob, [W26_SPAN]) if ob.type == 'MESH' else None
rm = W.mat_emit('mark ring', W.srgb('#D9475A'), 4.0)
for k, (xy, R) in enumerate(((CP.CTR, 6.2), ((sx, sy), 2.8))):
    rg = W.torus('mark ring %d' % k, R, 0.22, rm); rg.location = (xy[0], xy[1], QW.TILE_H + 0.25); rg.visible_shadow = False
    t0 = CP.T_MARK26[k]; keys(rg, 'scale', [(t0, (0.6, 0.6, 1)), (t0 + 0.3, (1.1, 1.1, 1)), (t0 + 0.5, (1, 1, 1))]); show(rg, [(t0, W26_SPAN[1])])
# ================================================================ B28：壊れた 6 個（灰色）→ 予備の 17 個から光の線 → 組み上がる（水色）
for b in CP.BAD:
    for p in BX[b]['pans']: color_at(T_B28 - 0.05, p, panel_color(p['v'], 'broken'), 0.02); color_at(CP.T_RESTORE, p, panel_color(p['v'], 'restored'), 0.6)
    color_at(T_B28 - 0.05, BX[b]['lid'], lid_color('broken'), 0.02); color_at(CP.T_RESTORE, BX[b]['lid'], lid_color('restored'), 0.6)
# v12 #89：線の星形をやめた。予備の箱が順に光って、そこから光の玉（尾つき）が壊れた箱へ飛ぶ。玉が着くたびに壊れた箱が光る
om = W.mat_emit('gather orb', W.srgb('#FFC27A'), 9.0); SRC = [b for b in SPARE if b not in CP.BAD]; TRAVEL = 0.85
fl_m = W.mat_emit('bad flash', W.srgb('#BFF6FF'), 6.0); arrive = {b: [] for b in CP.BAD}
for k, b in enumerate(SRC):
    tgt_b = CP.BAD[k % len(CP.BAD)]; tgt = CEN[tgt_b]
    t0 = CP.T_BEAMS28[0] + (CP.T_BEAMS28[1] - CP.T_BEAMS28[0] - TRAVEL + 0.3) * k / (len(SRC) - 1)
    p0 = Vector((CEN[b].x, CEN[b].y, Z0 + WALL_H + 0.4)); p1 = Vector((tgt.x, tgt.y, Z0 + WALL_H + 0.3))
    sg = W.box('src glow %d' % b, (BOXW * 0.86, BOXW * 0.86, 0.05), gm, bevel=0.1); sg.location = (CEN[b].x, CEN[b].y, Z0 + WALL_H + 0.16); sg.visible_shadow = False
    keys(sg, 'scale', [(t0 - 0.25, (0.3, 0.3, 1)), (t0, (1.1, 1.1, 1)), (t0 + 0.5, (0.9, 0.9, 1))]); show(sg, [(t0 - 0.25, CP.T_RESTORE + 0.6)])
    for j, (sz, lag) in enumerate(((0.78, 0.0), (0.54, 0.05), (0.38, 0.10), (0.25, 0.15))):     # 試し描きで小さかった → 大きく
        o = W.box('gather orb %d %d' % (b, j), (sz, sz, sz), om, bevel=sz / 2, seg=4); o.visible_shadow = False
        for f in range(fr_of(t0 + lag), fr_of(t0 + lag + TRAVEL) + 1):
            u = min(1.0, max(0.0, ((f - 1) / FPS - t0 - lag) / TRAVEL)); o.location = p0.lerp(p1, ease(u)) + Vector((0, 0, 2.6 * math.sin(math.pi * u))); o.keyframe_insert('location', frame=f)
        show(o, [(t0 + lag, t0 + lag + TRAVEL)])
    arrive[tgt_b].append(t0 + TRAVEL)
for b, ts_ in arrive.items():                                   # 玉が着いた瞬間、壊れた箱のふたがぱっと光る
    fo = W.box('bad flash %d' % b, (BOXW * 0.9, BOXW * 0.9, 0.05), fl_m, bevel=0.1); fo.location = (CEN[b].x, CEN[b].y, Z0 + WALL_H + 0.18); fo.visible_shadow = False
    pts = []
    for ta in sorted(ts_): pts += [(ta - 0.02, (0.2, 0.2, 1)), (ta + 0.12, (1.15, 1.15, 1)), (ta + 0.45, (0.2, 0.2, 1))]
    keys(fo, 'scale', pts); show(fo, [(min(ts_) - 0.05, max(ts_) + 0.5)])
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.02, location=(CP.CTR[0], CP.CTR[1], 0.9)); sh = bpy.context.object; sh.name = 'robot shadow'; sh.scale = (5.9, 5.3, 1)
shm = W.mat('shadow', (0.0, 0.0, 0.0), rough=1.0); shm.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.25; sh.data.materials.append(shm)
try: shm.surface_render_method = 'DITHERED'
except Exception: pass
show(sh, [(T_B28, CP.T_RESTORE)])
bake_colors()

# ================================================================ まるロボ
plan, FR = CP.world_frames()
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

# ================================================================ カメラ
C = lambda *v: Vector(v)
X, rp = CP.ROW_X, CP.row_pos; r0 = Vector((*rp(0), 0)); wx, wy = CP.W23_XY; ct = Vector((*CP.CTR, 0))
VIEWS = {'G9': (C(X + 6.5, rp(4)[1] - 5.0, 4.6), C(*rc(9, 9), 0.0), 20), 'G6': (r0 + C(0.45, -5.9, 2.5), r0 + C(-0.3, 0.2, 1.45), 30),   # v12 #46：3章と同じ、板がほぼ正面に並ぶ角度
         'W23': (C(wx + 2.6, wy - 6.4, 3.6), C(wx + 0.6, wy + 0.3, 0.3), 30), 'W26': (C(H * 0.25, -H * 1.25, 27), C(H * 0.2, -H * 0.12, 0), 26)}
for k in ('B28a', 'B28b', 'B28c', 'B28d'): VIEWS[k] = (ct + C(9.0, -15.0, 10.0), ct + C(-4.0, 3.0, 0.5), 24)
SH = [(a, b, k) for a, b, k in CP.SHOTS if k in VIEWS]
for n_, (t0, t1, k) in enumerate(SH):
    L, T, lens = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 900; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler()
    for t, dd in ((t0, 0.0), (t1, 0.04)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    interp(cam, 'LINEAR')
    m = sc.timeline_markers.new('c4w %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=A.save)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w4_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    cam_at(F0); sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w4_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.WORLD_RANGES, late=CP.U.LATE, stain=CP.T_STAIN_W, mark26=CP.T_MARK26, beams28=CP.T_BEAMS28, restore=CP.T_RESTORE,
               events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_happy', 'beep_yes', 'beep_surprise')], shots=SH),
          open(os.path.join(A.out, 'qrc4w_log_%d.json' % F0), 'w'), default=float, indent=0)
print('QRC4W DONE', F0, F1)
