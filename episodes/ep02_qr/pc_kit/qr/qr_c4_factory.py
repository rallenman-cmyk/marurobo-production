# QRコード回・4章のはじめ「1994 年、工場で生まれた」（F1・F2）の本番描画（PC・Blender 4.3.2・EEVEE）。台本 v2.0 の時刻
#   blender -b --factory-startup --python qr_c4_factory.py -- --blend story.blend --out DIR --frames 279:1006 --video 1 --vprefix qrc4f_
#   確認用：--standin 1（仮のまるロボ）。--still 400,800 で指定のコマだけ PNG
#   作業台・部品箱・伝票（QR）・油の缶。21-02 で伝票に油が落ちて広がる。看板の字（1994）は書かない（2D の札）
import sys, os, math, json, argparse
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import c4_plan as CP
from c4_plan import FPS, s, e, fr_of
ap = argparse.ArgumentParser()
R0 = CP.FACTORY_RANGES[0]
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc4f'); ap.add_argument('--frames', default='%d:%d' % (fr_of(R0[0]), fr_of(R0[1])))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc4f_'); ap.add_argument('--standin', type=int, default=0)
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

# ================================================================ 工場（灰色の空間・コンクリートの床・作業台）
wd = bpy.data.worlds.new('Factory'); sc.world = wd; wd.use_nodes = True; bg = wd.node_tree.nodes['Background']; bg.inputs[0].default_value = (*W.srgb('#C9CDD2'), 1); bg.inputs[1].default_value = 0.55
la = bpy.data.lights.new('key', 'AREA'); la.shape = 'DISK'; la.size = 30; la.energy = 14000; k_ = W.link(O.new('key', la)); k_.location = (-4, -10, 22); k_.rotation_euler = (math.radians(25), 0, math.radians(-10))
ls = bpy.data.lights.new('sun', 'SUN'); ls.energy = 2.0; ls.angle = math.radians(4); s_ = W.link(O.new('sun', ls)); s_.rotation_euler = (math.radians(40), 0, math.radians(-30))
fl = W.box('shop floor', (60, 60, 0.2), W.mat('concrete', W.srgb('#9AA0A6'), rough=0.9)); fl.location = (0, 0, -0.05)
top = W.box('bench', (5.6, 2.6, 0.18), W.mat('wood', W.srgb('#B98A5A'), rough=0.6), bevel=0.03); top.location = (0, 0, 2.0)
for dx in (-2.6, 2.6):
    for dy in (-1.1, 1.1):
        lg = W.box('leg', (0.14, 0.14, 2.0), W.mat('steel', W.srgb('#59616A'), metal=0.6, rough=0.4)); lg.location = (dx, dy, 1.0)
img = bpy.data.images.load(os.path.join(HERE, 'qr_paper.png'))
def slip(x, y, rz, s=0.75):
    m = bpy.data.materials.new('slip'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']; tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Linear'      # v12 #56：Closest は遠くでちらつく
    nt.links.new(tx.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
    bpy.ops.mesh.primitive_plane_add(size=s, location=(x, y, 2.103)); o = bpy.context.object      # v12 #56：紙の上面（2.1）と同じ高さで重なってちらついていた → 3mm 浮かす; o.rotation_euler = (0, 0, rz); o.data.materials.append(m)
    pa = W.box('paper', (s * 1.25, s * 1.6, 0.01), W.mat('paper', W.srgb('#F4F2EC'), rough=0.8)); pa.location = (x, y + s * 0.18, 2.095); pa.rotation_euler = (0, 0, rz)
    return o
for k, (x, col) in enumerate(((-1.9, '#3F86DD'), (-0.6, '#3E9E62'), (0.7, '#F0953A'))):
    bx = W.box('bin', (1.0, 0.8, 0.5), W.mat('bin%d' % k, W.srgb(col), rough=0.5), bevel=0.04); bx.location = (x, 0.75, 2.34)
    for j in range(4):
        pt = W.cyl('part', 0.08, 0.25, W.mat('metal', W.srgb('#C0C6CC'), metal=0.8, rough=0.3)); pt.location = (x - 0.25 + j * 0.17, 0.75, 2.62)
slip(-1.6, -0.55, 0.12); slip(CP.SLIP2[0], CP.SLIP2[1], -0.08)
can = W.cyl('oil can', 0.2, 0.5, W.mat('can', W.srgb('#C23B32'), metal=0.4, rough=0.4)); can.location = (1.9, -0.3, 2.34)
oil_m = W.mat('oil', (0.01, 0.012, 0.014), rough=0.15, coat=0.6)
def blob(name, c, rx, ry, rz, seed):
    import random; rnd = random.Random(seed); root = W.link(O.new(name, None)); root.location = c
    for k in range(7):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); o = bpy.context.object; o.name = '%s %d' % (name, k); o.data.materials.append(oil_m); o.parent = root
        dx = rnd.uniform(-0.45, 0.45) * rx if k else 0; dy = rnd.uniform(-0.45, 0.45) * ry if k else 0; sc_ = rnd.uniform(0.45, 0.8) if k else 1.0
        o.location = (dx, dy, 0); o.scale = (rx * sc_, ry * sc_, rz)
    return root
blob('old oil', (1.5, -0.55, 2.1), 0.25, 0.18, 0.01, 11)
# 21-02：伝票に油が落ちて、広がる（しずく → しみ）
drop = W.link(O.new('oil drop', None))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0, 0, 0)); dm = bpy.context.object; dm.data.materials.append(oil_m); dm.parent = drop
x0, y0 = CP.SLIP2[0] + 0.12, CP.SLIP2[1] - 0.05
for t, z in ((CP.T_OIL - 0.5, 3.6), (CP.T_OIL, 2.12)): drop.location = (x0, y0, z); drop.keyframe_insert('location', frame=fr_of(t))
interp(drop, 'LINEAR')
for f, h in ((1, True), (fr_of(CP.T_OIL - 0.5), False), (fr_of(CP.T_OIL) + 1, True)): dm.hide_render = h; dm.keyframe_insert('hide_render', frame=f)
for nm, c, rx, ry, seed, dt in (('stain a', (x0, y0, 2.11), 0.22, 0.17, 7, 0.0), ('stain b', (CP.SLIP2[0] - 0.2, CP.SLIP2[1] + 0.15, 2.11), 0.1, 0.08, 9, 0.25)):
    st = blob(nm, c, rx, ry, 0.012, seed)
    for t, sc_ in ((CP.T_OIL + dt, 0.05), (CP.T_OIL + dt + 0.7, 1.0)): st.scale = (sc_, sc_, 1); st.keyframe_insert('scale', frame=fr_of(t))
    for ob in hier(st):
        if ob.type == 'MESH':
            for f, h in ((1, True), (fr_of(CP.T_OIL + dt), False)): ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)

# ================================================================ まるロボ（作業台の上）
plan, FR = CP.factory_frames()
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

# ================================================================ カメラ（F1：作業台の全体／F2：伝票に寄る）
C = lambda *v: Vector(v)
VIEWS = {'F1': (C(3.2, -6.8, 4.4), C(0.0, 0.2, 2.3), 30), 'F2': (C(0.2, -2.8, 3.6), C(-0.3, -0.5, 2.1), 34)}
SH = [(a, b, k) for a, b, k in CP.SHOTS if k in VIEWS]
for n_, (t0, t1, k) in enumerate(SH):
    L, T, lens = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 300; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler()
    for t, dd in ((t0, 0.0), (t1, 0.05)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    interp(cam, 'LINEAR')
    m = sc.timeline_markers.new('c4f %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples, exposure=-0.9)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'f4_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    cam_at(F0); sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'f4_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.FACTORY_RANGES, oil=CP.T_OIL, events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'beep_surprise')], shots=SH),
          open(os.path.join(A.out, 'qrc4f_log_%d.json' % F0), 'w'), default=float, indent=0)
print('QRC4F DONE', F0, F1)
