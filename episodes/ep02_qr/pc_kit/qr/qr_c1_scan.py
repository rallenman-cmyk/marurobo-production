# QRコード回・1章「最初にすること。それは見つけること」（09-03）の差し込み：卓上のスマホが QR を探し、3 つの目印が光る（PC・Blender 4.3.2・EEVEE）
#   blender -b --factory-startup --python qr_c1_scan.py -- --out DIR --frames 1:N --video 1   （N は T_SCAN の長さ。組み立てで中の世界の上に重ねる）
#   まるロボはいない（スマホの中に入っているので）。1 回の実行で 2 段：① スマホのカメラの絵 → ② 本番
import sys, os, math, json, argparse
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
from c1_timeline import *
import op_timeline as OPT
NS = int(round((T_SCAN[1] - T_SCAN[0]) * FPS))
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc1s'); ap.add_argument('--frames', default='1:%d' % NS)
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc1s_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--phone_res', nargs=2, type=int, default=[540, 1120]); ap.add_argument('--phone_samples', type=int, default=16)
ap.add_argument('--still', default='')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
def fr_of(t): return int(round(t * FPS)) + 1          # t はこの差し込みの頭からの秒
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def link(ob, coll=None): (coll or sc.collection).objects.link(ob); return ob
N, QZ, MODT = OPT.N, OPT.QZ, OPT.MOD
def rcT(r, c): return Vector((-(N * MODT) / 2 + (c + 0.5) * MODT, (N * MODT) / 2 - (r + 0.5) * MODT, 0.0))

# ================================================================ 舞台：冒頭と同じ（机・QRの紙・光 A案）
W.sky_and_sun(sc, az_deg=135.0, el_deg=50.0, sky_strength=0.35, sun_energy=4.0)
desk = W.box('Desk', (16, 17, 0.3), W.mat('Desk wood', W.srgb('#B98A5E'), rough=0.55), bevel=0.03); desk.location = (0, -2.5, -0.15)   # 冒頭より手前に広い（画面の前に立つ所）
pm = bpy.data.materials.new('QR paper'); pm.use_nodes = True; nt = pm.node_tree; bs = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.join(HERE, 'qr_paper.png')); tex.interpolation = 'Closest'
nt.links.new(tex.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
side = (N + 2 * QZ) * MODT
bpy.ops.mesh.primitive_plane_add(size=side, location=(0, 0, 0.004)); paper = bpy.context.object; paper.name = 'QR paper'; paper.data.materials.append(pm)

# ================================================================ スマホ（冒頭と同じ所に斜めに立てる。画面は手前・上を向く）
LENS_V, AIM_V = Vector(OPT.LENS), Vector(OPT.AIM); PW, PH, PT = OPT.PHONE_SIZE
back = (AIM_V - LENS_V).normalized(); px = back.cross(Vector((0, 0, 1))).normalized(); py = (-back).cross(px).normalized()
R = Matrix((px, py, -back)).transposed()
def place(ob, c, scale=None):
    m = R.to_4x4(); m.translation = c
    if scale: m = m @ Matrix.Diagonal((*scale, 1))
    ob.matrix_world = m
cphone = LENS_V - back * (PT / 2) - py * (PH / 2 - 0.35)
phone = W.box('Phone', (PW, PH, PT), W.mat('Phone body', W.srgb('#1E2228'), rough=0.3, metal=0.2), bevel=0.08, seg=4); place(phone, cphone)
smat = bpy.data.materials.new('Phone screen'); smat.use_nodes = True; snt = smat.node_tree; snt.nodes.clear()
sem = snt.nodes.new('ShaderNodeEmission'); sout = snt.nodes.new('ShaderNodeOutputMaterial'); snt.links.new(sem.outputs[0], sout.inputs[0])
stex = snt.nodes.new('ShaderNodeTexImage'); snt.links.new(stex.outputs[0], sem.inputs['Color'])
bpy.ops.mesh.primitive_plane_add(size=1); scr = bpy.context.object; scr.name = 'Phone screen'; scr.data.materials.append(smat)
SCR_C = cphone - back * (PT / 2 + 0.005); NRM = -back
place(scr, SCR_C, (PW - 0.12, PH - 0.12, 1))
metal = W.mat('Stand metal', W.srgb('#3A3F46'), rough=0.35, metal=0.8)
foot = Vector((cphone.x, cphone.y - 0.9, 0)); base = W.cyl('Stand base', 0.45, 0.08, metal); base.location = (foot.x, foot.y, 0.04)
d = (cphone + back * 0.2) - foot; pole = W.cyl('Stand pole', 0.06, d.length, metal); pole.location = foot + d / 2; pole.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

# ================================================================ カメラ：スマホの後ろ・少し左上から（冒頭の肩越し）。ゆっくり画面へ寄る
def look_rot(loc, look): return (look - loc).to_track_quat('-Z', 'Y').to_euler()
cd = bpy.data.cameras.new('Cam scan'); cd.lens = 30; cd.clip_end = 400; cam = link(O.new('Cam scan', cd))
L0, T0 = Vector((-0.95, -6.7, 4.45)), Vector((0.10, 0.05, 1.25)); cam.rotation_euler = look_rot(L0, T0)
for t, dd in ((0.0, 0.02), (NS / FPS, 0.16)): cam.location = L0 + (T0 - L0) * dd; cam.keyframe_insert('location', frame=fr_of(t))
sc.camera = cam; _m = sc.timeline_markers.new('s0', frame=1); _m.camera = cam

# ================================================================ スマホの画面の中の表示（読み取りの枠と「HELLO」）＝スマホのカメラにだけ映る。飛び込む少し前に消える
ui = bpy.data.collections.new('Phone UI'); sc.collection.children.link(ui)
pcd = bpy.data.cameras.new('PhoneCam'); pcd.lens = 34; pcd.sensor_fit = 'HORIZONTAL'
pcam = link(O.new('PhoneCam', pcd)); pcam.location = LENS_V + back * 0.05; pcam.rotation_euler = (AIM_V - LENS_V).to_track_quat('-Z', 'Y').to_euler()
pw, ph = A.phone_res; asp = ph / pw; zd = 0.5; hw = zd * 18 / 34; hh = hw * asp
def ui_obj(name, ob):
    for c in ob.users_collection: c.objects.unlink(ob)
    ui.objects.link(ob); ob.parent = pcam; return ob
cm = bpy.data.materials.new('Scan corner'); cm.use_nodes = True; cnt = cm.node_tree; cnt.nodes.clear()
ce = cnt.nodes.new('ShaderNodeEmission'); co = cnt.nodes.new('ShaderNodeOutputMaterial'); cnt.links.new(ce.outputs[0], co.inputs[0]); ce.inputs['Color'].default_value = (*W.srgb('#FFD640'), 1)
k_ = hw * 0.72; cy0 = -hh * 0.16; arm = hw * 0.22; th = hw * 0.035; ui_objs = []
for sx in (-1, 1):
    for sy in (-1, 1):
        for horiz in (True, False):
            bpy.ops.mesh.primitive_plane_add(size=1); p = ui_obj('corner', bpy.context.object); p.data.materials.append(cm)
            cx_, cy_ = sx * k_, cy0 + sy * k_
            p.location = (cx_ - sx * arm / 2, cy_, -zd) if horiz else (cx_, cy_ - sy * arm / 2, -zd)
            p.scale = (arm, th, 1) if horiz else (th, arm, 1); ui_objs.append(p)
# 枠：はじめは大きく、QR を見つけるにつれて縮む（読み取りの枠が QR を探す）
for f in range(F0, F1 + 1):
    u = ease(((f - 1) / FPS - 0.3) / 1.6); s_ = 1.45 - 0.45 * u
    for p_ in ui_objs:
        p_['base'] = p_.get('base') or list(p_.location)
        bx, by, bz = p_['base']; p_.location = (bx * s_, cy0 + (by - cy0) * s_, bz); p_.keyframe_insert('location', frame=f)
# 3 つの目印に赤い枠（スマホの画面にだけ映る：紙の上に置くが、本番のカメラからは隠す）
rm = W.mat_emit('Finder hit', W.srgb('#FF3B4E'), 6.0)
for k, (r0, c0) in enumerate(((3, 3), (3, 17), (17, 3))):
    c = rcT(r0, c0) + Vector((0, 0, 0.012)); half = 3.9 * MODT
    for (dx, dy, sx, sy) in ((0, half, 2 * half + 0.08, 0.08), (0, -half, 2 * half + 0.08, 0.08), (half, 0, 0.08, 2 * half), (-half, 0, 0.08, 2 * half)):
        bpy.ops.mesh.primitive_plane_add(size=1); q = bpy.context.object; q.data.materials.append(rm); q.location = c + Vector((dx, dy, 0)); q.scale = (sx, sy, 1)
        for cl in q.users_collection: cl.objects.unlink(q)
        ui.objects.link(q); t0 = 2.2 + 0.55 * k
        for f, h in ((1, True), (fr_of(t0), False)): q.hide_render = h; q.keyframe_insert('hide_render', frame=f)

# ================================================================ 描く
def setup(res, samples): W.render_setup(sc, engine='eevee', res=tuple(res), samples=samples)
def view_layer_only(phone_pass):
    for lc in sc.view_layers[0].layer_collection.children:
        if lc.collection == ui: lc.exclude = not phone_pass
    scr.hide_render = phone_pass
frames = [int(x) for x in A.still.split(',')] if A.still else list(range(F0, F1 + 1))
# ① スマホのカメラの絵（まるロボはスマホの後ろなので映らない）
pdir = os.path.join(A.out, 'phone_scan'); os.makedirs(pdir, exist_ok=True)   # 卓上（qrc1t_）の phone と分ける
view_layer_only(True); setup(A.phone_res, A.phone_samples)
saved = [(m, m.camera) for m in sc.timeline_markers]
for m in sc.timeline_markers: m.camera = None
sc.camera = pcam
need = sorted(set(range(min(frames), max(frames) + 1)) if not A.still else set(frames))
for f in need:
    p = os.path.join(pdir, 'p_%04d.png' % f)
    if os.path.exists(p) and os.path.getsize(p) > 0: continue
    sc.frame_set(f); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
# ② 本番
for m, c in saved: m.camera = c
view_layer_only(False); setup(A.res, A.samples)
if A.still:
    for f in frames:
        img = bpy.data.images.load(os.path.join(pdir, 'p_%04d.png' % f)); stex.image = img
        sc.frame_set(f)
        for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
            if m.frame <= f: sc.camera = m.camera
        sc.render.filepath = os.path.join(A.out, 't_%04d.png' % f); bpy.ops.render.render(write_still=True)
else:
    img = bpy.data.images.load(os.path.join(pdir, 'p_%04d.png' % F0)); img.source = 'SEQUENCE'; stex.image = img
    stex.image_user.frame_start = F0; stex.image_user.frame_offset = F0 - 1; stex.image_user.frame_duration = F1 - F0 + 1; stex.image_user.use_auto_refresh = True
    if A.video:
        sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
        sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
        bpy.ops.render.render(animation=True)
    else:
        for f in range(F0, F1 + 1):
            sc.frame_set(f); sc.render.filepath = os.path.join(A.out, 't_%04d.png' % f); bpy.ops.render.render(write_still=True)
print('QRC1S DONE', F0, F1)
