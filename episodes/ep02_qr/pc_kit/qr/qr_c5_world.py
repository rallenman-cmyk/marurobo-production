# QRコード回・5章「どこまで隠したら読めなくなる？」の中の世界（W29・W30・W28・W31・W31b）の本番描画（PC・Blender 4.3.2・EEVEE）
#   blender -b --factory-startup --python qr_c5_world.py -- --blend story.blend --out DIR --frames 327:816 --video 1 --vprefix qrc5w_
#   確認用：--standin 1（仮のまるロボ）。--still 500,1500 で指定のコマだけ PNG
#   26 個すべてが箱。場面ごとに「壊れた箱」（灰色）が変わる：一歩踏み込んだ 10 個／しずく 12 か所で 12 個／乗ったとき 6 個／ロゴで 8 個／ロゴ＋しずくで 9 個
#   数は 2D の札で出す（3D の中に字なし）
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import qr_world as QW
import c5_plan as CP
from c5_plan import FPS, s, e, fr_of, rc, H, MOD
ap = argparse.ArgumentParser()
R0 = CP.WORLD_RANGES[0]
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc5w'); ap.add_argument('--frames', default='%d:%d' % (fr_of(R0[0]), fr_of(R0[1])))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc5w_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--still', default=''); ap.add_argument('--save', default='')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
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

# ================================================================ 大地と 26 個の箱
Wd = QW.build(); coll = Wd['coll']; QW.lights_c(sc, coll)
AS = Wd['assets']; SYM = Wd['symbol']; TILES = Wd['tiles']; TM = TILES[(0, 0)].data.materials[0]; EX = AS['experiments']
DATA = list(SYM['data_boxes'])
QW.paint(Wd, QW.cells_of(Wd, 'finder'), 'finder')
BOX_CELLS = {int(b): [tuple(x) for x in cs] for b, cs in AS['boxes'].items()}
def role(b): return 'data' if b in DATA else 'spare'
for b, cells in BOX_CELLS.items():
    for rc_ in cells: tl = TILES[rc_]; c = list(QW.color_for(tl['v'], role(b))); c[3] = 0.22; tl.color = c
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
PANEL, WALL_H, BOXW = 0.7, 0.7, 1.4; Z0 = QW.TILE_H
PT_ = []
for side, (nx, ny) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
    n = Vector((nx, ny, 0)); tv = Vector((-ny, nx, 0))
    for k in (-1, 1): PT_.append((n * (BOXW / 2) + tv * (PANEL / 2 * k) + Vector((0, 0, WALL_H / 2)), math.atan2(ny, nx) - math.pi / 2))
def panel_color(v, state):
    base = W.srgb(QW.COL['black'] if v else QW.COL['white']); tint = W.srgb(QW.COL[state])
    if state == 'broken': return (*QW.mixc(base, tint, 0.7), 0.52)
    return (*QW.mixc(base, tint, 0.45 if v else 0.62), 1.0)
def lid_color(state):
    if state == 'broken': return (*W.srgb(QW.COL['broken']), 0.52)
    return (*QW.mixc((0.86, 0.88, 0.90), W.srgb(QW.COL[state]), 0.7), 1.0)
floor_m = W.mat('Box floor', (0.30, 0.32, 0.35), rough=0.6)
BX = {}
for b, cells in BOX_CELLS.items():
    cen = (sum(rc(*x)[0] for x in cells) / 8, sum(rc(*x)[1] for x in cells) / 8)
    root = W.link(O.new('BoxRoot %d' % b, None)); root.location = (cen[0], cen[1], Z0); pans = []
    for i, (r, c) in enumerate(cells):
        p = W.box('Box %d panel %d' % (b, i), (1, 1, 1), TM, bevel=0.0, seg=1); p.parent = root; p['v'] = TILES[(r, c)]['v']
        p1, rz = PT_[i]; p.location = p1; p.scale = (PANEL, PANEL, 0.05); p.rotation_euler = Euler((math.pi / 2, 0, rz), 'XYZ'); p.color = panel_color(p['v'], role(b)); pans.append(p)
    fl = W.box('Box %d floor' % b, (BOXW, BOXW, 0.04), floor_m); fl.parent = root; fl.location = (0, 0, 0.02)
    lid = W.box('Box %d lid' % b, (BOXW + 0.05, BOXW + 0.05, 0.08), TM, bevel=0.02); lid.parent = root; lid.location = (0, 0, WALL_H + 0.04); lid.color = lid_color(role(b))
    BX[b] = dict(root=root, pans=pans, lid=lid)
def box_state(b, state, t, ramp=0.25):
    for p in BX[b]['pans']: color_at(t, p, panel_color(p['v'], state), ramp)
    color_at(t, BX[b]['lid'], lid_color(state), ramp)
# ---------------------------------------------------------------- 場面ごとの「壊れた箱」
SPANS = {}
for a, b, k in CP.SHOTS:
    if k in CP.STATE: SPANS.setdefault(k, []).append((a, b))
def scene(k, t0, t1, t_count=None, step=0.35):
    bad = EX[CP.STATE[k]]['bad_boxes']
    for b in BX: box_state(b, role(b), t0 - 0.05, 0.02)
    for j, b in enumerate(bad): box_state(b, 'broken', (t_count + step * j) if t_count is not None else t0 - 0.04, 0.25 if t_count is not None else 0.02)
for k, sp in SPANS.items():
    for n_, (a, b) in enumerate(sp):
        tc = {'W29': CP.T_COUNT29, 'W30': CP.T_DROPS + 0.4, 'W31': CP.T_COUNT31}.get(k) if n_ == 0 else None
        scene(k, a, b, tc, step=(0.25 if k == 'W30' else 0.35))
# W31b：9 個目はしずくが落ちてから
d31 = [b for b in EX['logo7_ink1']['bad_boxes'] if b not in EX['logo7']['bad_boxes']]
for b in d31: box_state(b, role(b), CP.shot_start('W31b') - 0.03, 0.02); box_state(b, 'broken', CP.T_DROP31 + 0.4, 0.3)
# ---------------------------------------------------------------- しずく（W30 の 12 か所・W31b の 1 か所）
ink = W.mat('ink', (0.01, 0.012, 0.02), rough=0.3)
def drop_obj(name, xy, t_fall, spans):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); o = bpy.context.object; o.name = name; o.data.materials.append(ink)
    keys(o, 'location', [(t_fall, (xy[0], xy[1], 7.0)), (t_fall + 0.4, (xy[0], xy[1], 1.05))], kind='LINEAR')
    keys(o, 'scale', [(t_fall, (0.2, 0.2, 0.35)), (t_fall + 0.4, (0.2, 0.2, 0.35)), (t_fall + 0.55, (0.55, 0.5, 0.05))])
    show(o, spans)
w30 = SPANS['W30']
for j, (r, c) in enumerate(EX['ink12']['drops']):
    tf = CP.T_DROPS + 0.25 * j; drop_obj('ink %d' % j, rc(r, c), tf, [(tf, w30[0][1])] + [x for x in w30[1:]])
drop_obj('ink31', rc(*EX['logo7_ink1']['drop']), CP.T_DROP31, [(CP.T_DROP31, SPANS['W31b'][0][1])])
# ---------------------------------------------------------------- ロゴ（W31・W31b）：真ん中の 7×7 マス。透けると下の箱が見える
c = rc(10, 10); lm = W.mat('logo', W.srgb('#F2F4F5'), rough=0.4, alpha=1.0)
lg = W.box('logo', (7 * MOD, 7 * MOD, 0.4), lm, bevel=0.2); lg.location = (c[0], c[1], 1.3)
ey = W.cyl('logo eye', 2.6, 0.1, W.mat_emit('logo lens', W.srgb('#3FC6C9'), 1.6)); ey.location = (c[0], c[1], 1.55)
rg = W.torus('logo ring', 2.8, 0.25, W.mat('logo ring', W.srgb('#203236'), rough=0.3)); rg.location = (c[0], c[1], 1.55)
bsdf = lm.node_tree.nodes['Principled BSDF']
try: lm.surface_render_method = 'BLENDED'
except Exception: pass
for t, a in ((0.0, 1.0), (CP.T_LOGO, 1.0), (CP.T_LOGO + 0.8, 0.35)): bsdf.inputs['Alpha'].default_value = a; bsdf.inputs['Alpha'].keyframe_insert('default_value', frame=fr_of(t))
LOGO_SPANS = SPANS['W31'] + SPANS['W31b']
for ob in (lg, ey, rg): show(ob, LOGO_SPANS)
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

# ================================================================ カメラ
C = lambda *v: Vector(v)
def onrobot(p): return (C(p[0] + 9.0, p[1] - 15.0, 14.0), C(p[0] - 3.0, p[1] + 3.0, 0.5), 24)
WIDE = (C(0.0, -H * 1.55, H * 1.25), C(0.0, -1.0, 0.0), 24)
VIEWS = {'W29': onrobot(CP.P_STEP), 'W28': onrobot(CP.P_STAND), 'W30': WIDE, 'W31': WIDE, 'W31b': WIDE}
SH = [(a, b, k) for a, b, k in CP.SHOTS if k in VIEWS]
for n_, (t0, t1, k) in enumerate(SH):
    L, T, lens = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 900; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler()
    for t, dd in ((t0, 0.0), (t1, 0.04)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    interp(cam, 'LINEAR')
    m = sc.timeline_markers.new('c5w %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w5_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    cam_at(F0); sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w5_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.WORLD_RANGES, count29=CP.T_COUNT29, drops=CP.T_DROPS, logo=CP.T_LOGO, count31=CP.T_COUNT31, drop31=CP.T_DROP31,
               events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'beep_surprise', 'beep_yes')], shots=SH),
          open(os.path.join(A.out, 'qrc5w_log_%d.json' % F0), 'w'), default=float, indent=0)
print('QRC5W DONE', F0, F1)
