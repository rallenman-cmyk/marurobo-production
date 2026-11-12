# QRコード回・2章の終わり「小さな箱で目印を隠すと、読めない」の本番描画（PC・Blender 4.3.2・EEVEE）。冒頭と同じ机・QRの紙・スマホ
#   1回の実行で2段に描く：① スマホのカメラの絵（画面に貼る）→ ② 本番の絵（1章の卓上と同じ仕組み）
#   blender -b --factory-startup --python qr_c2_table.py -- --blend story.blend --out DIR --frames 8428:9567 --video 1 --vprefix qrc2t_
#   確認用：--standin 1（仮のまるロボ）。--still 8500,8700 で指定のコマだけ
#   動き：頭に載せた小さな箱を、左上の目印の真ん中に落として置く → 離れてスマホを見上げる → 読めない（枠は出るが結果が出ない）→ 首を振る・考える → 箱の近くへ
#   スマホの画面に字は出さない（結果が出ないことは、枠が探し続けることで見せる）
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import c2_plan as CP
from c2_plan import FPS, s, e, fr_of
import op_timeline as OPT
ap = argparse.ArgumentParser()
R0 = CP.DESK_RANGES[0]
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc2t'); ap.add_argument('--frames', default='%d:%d' % (fr_of(R0[0]), fr_of(R0[1])))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc2t_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--phone_res', nargs=2, type=int, default=[540, 1120]); ap.add_argument('--phone_samples', type=int, default=12)
ap.add_argument('--still', default='')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def link(ob, coll=None): (coll or sc.collection).objects.link(ob); return ob
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
N, QZ, MODT = OPT.N, OPT.QZ, OPT.MOD

# ================================================================ 舞台：冒頭と同じ（机・QRの紙・光 A案）
W.sky_and_sun(sc, az_deg=135.0, el_deg=50.0, sky_strength=0.35, sun_energy=4.0)
desk = W.box('Desk', (16, 17, 0.3), W.mat('Desk wood', W.srgb('#B98A5E'), rough=0.55), bevel=0.03); desk.location = (0, -2.5, -0.15)
pm = bpy.data.materials.new('QR paper'); pm.use_nodes = True; nt = pm.node_tree; bs = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.join(HERE, 'qr_paper.png')); tex.interpolation = 'Closest'
nt.links.new(tex.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
side = (N + 2 * QZ) * MODT
bpy.ops.mesh.primitive_plane_add(size=side, location=(0, 0, 0.004)); paper = bpy.context.object; paper.name = 'QR paper'; paper.data.materials.append(pm)
# スマホ（冒頭と同じ所に斜めに立てる）
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
SCR_C = cphone - back * (PT / 2 + 0.005); place(scr, SCR_C, (PW - 0.12, PH - 0.12, 1))
metal = W.mat('Stand metal', W.srgb('#3A3F46'), rough=0.35, metal=0.8)
foot = Vector((cphone.x, cphone.y - 0.9, 0)); base = W.cyl('Stand base', 0.45, 0.08, metal); base.location = (foot.x, foot.y, 0.04)
d = (cphone + back * 0.2) - foot; pole = W.cyl('Stand pole', 0.06, d.length, metal); pole.location = foot + d / 2; pole.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

# ================================================================ まるロボ
plan, FR = CP.desk_frames()
def frame_at(t): return FR[min(len(FR) - 1, max(0, int(round(t * FPS))))]
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
    for n in keep: link(O[n])
    for n in keep:
        if O[n].animation_data: O[n].animation_data_clear()
    for o in hier(O['Maru']):
        if o.name.startswith(('Cradle', 'Maru cargo')) or 'cradle' in o.name.lower(): o.hide_render = True
    rig = mr.MaruRig(O['Maru']); bk = mr.Baker()
    for i, fr in enumerate(FR):
        if F0 - 2 <= i + 1 <= F1 + 2: rig.apply(fr, i + 1, bk)
    bk.write()

# ================================================================ 小さな箱（3×3マス分）：頭に載せて運ぶ → 前へ落ちて、目印の真ん中に置かれる
S_ = CP.BOX_S
box = W.box('Small box', (S_, S_, S_ * 0.8), W.mat('Small box', W.srgb('#C9CED4'), rough=0.6), bevel=0.02)
def head_top(f):
    psi = f['psi']; Rr = Matrix.Rotation(psi, 3, 'Z') @ Matrix.Rotation(math.radians(-f['pitch']), 3, 'X')
    c = Vector(f['root']) + Vector((0, 0, mm.TORSO_Z)); return c + Rr @ Vector((0, -0.02, 0.50)), psi
T_DROP = CP.T_DROP_BOX; LAND = Vector((CP.C3[0], CP.C3[1], 0.004 + S_ * 0.4))
for f in range(F0, F1 + 1):
    t = (f - 1) / FPS
    if t < T_DROP:
        hp, psi = head_top(frame_at(t)); box.location = hp + Vector((0, 0, S_ * 0.4)); box.rotation_euler = (0, 0, psi)
    elif t < T_DROP + 0.6:
        hp, psi = head_top(frame_at(T_DROP)); a = hp + Vector((0, 0, S_ * 0.4)); u = (t - T_DROP) / 0.6
        box.location = a.lerp(LAND, u) + Vector((0, 0, 0.35 * math.sin(math.pi * u))); box.rotation_euler = (math.radians(-25 * math.sin(math.pi * u)), 0, psi * (1 - u))
    else:
        box.location = LAND; box.rotation_euler = (0, 0, 0)
    box.keyframe_insert('location', frame=f); box.keyframe_insert('rotation_euler', frame=f)

# ================================================================ カメラ（K41：箱と目印／K42：置いて離れたまるロボとスマホ／K43：肩越しにスマホの画面）
def look_rot(loc, look): return (look - loc).to_track_quat('-Z', 'Y').to_euler()
VIEWS = {'K41': ((-4.6, -4.4, 2.6), (-0.9, 0.4, 0.7), 26), 'K42': ((-4.6, -4.4, 2.6), (-1.2, 0.5, 0.5), 26), 'K43': ((-0.95, -6.7, 4.45), (0.10, 0.05, 1.25), 30)}
SH = [(a, b, k) for a, b, k in CP.SHOTS if k in VIEWS]
for n_, (t0, t1, k) in enumerate(SH):
    L, T, lens = map(lambda v: Vector(v) if isinstance(v, tuple) else v, VIEWS[k])
    cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 400; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = look_rot(L, T); d1 = 0.0 if k == 'K43' else 0.04
    for t, dd in ((t0, 0.0), (t1, d1)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    m = sc.timeline_markers.new('d %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ スマホの画面の中の表示：読み取りの枠だけ（結果は出ない）。枠は探し続けて点滅する
ui = bpy.data.collections.new('Phone UI'); sc.collection.children.link(ui)
pcd = bpy.data.cameras.new('PhoneCam'); pcd.lens = 34; pcd.sensor_fit = 'HORIZONTAL'
pcam = link(O.new('PhoneCam', pcd)); pcam.location = LENS_V + back * 0.05; pcam.rotation_euler = (AIM_V - LENS_V).to_track_quat('-Z', 'Y').to_euler()
pw, ph = A.phone_res; asp = ph / pw; zd = 0.5; hw = zd * 18 / 34; hh = hw * asp
cm = bpy.data.materials.new('Scan corner'); cm.use_nodes = True; cnt = cm.node_tree; cnt.nodes.clear()
ce = cnt.nodes.new('ShaderNodeEmission'); co = cnt.nodes.new('ShaderNodeOutputMaterial'); cnt.links.new(ce.outputs[0], co.inputs[0]); ce.inputs['Color'].default_value = (*W.srgb('#78DC8C'), 1)
for f in range(fr_of(CP.T_D0), fr_of(CP.T_END) + 1, 6):                # 探している間はゆっくり点滅
    t = (f - 1) / FPS; ce.inputs['Strength'].default_value = 0.35 + 0.65 * (0.5 + 0.5 * math.cos(2 * math.pi * t / 1.2)); ce.inputs['Strength'].keyframe_insert('default_value', frame=f)
k_ = hw * 0.72; cy0 = -hh * 0.16; arm = hw * 0.22; th = hw * 0.035
for sx in (-1, 1):
    for sy in (-1, 1):
        for horiz in (True, False):
            bpy.ops.mesh.primitive_plane_add(size=1); p = bpy.context.object
            for c in p.users_collection: c.objects.unlink(p)
            ui.objects.link(p); p.parent = pcam; p.data.materials.append(cm)
            cx_, cy_ = sx * k_, cy0 + sy * k_
            p.location = (cx_ - sx * arm / 2, cy_, -zd) if horiz else (cx_, cy_ - sy * arm / 2, -zd); p.scale = (arm, th, 1) if horiz else (th, arm, 1)

# ================================================================ 描く（① スマホのカメラの絵 → ② 本番）
def setup(res, samples): W.render_setup(sc, engine='eevee', res=tuple(res), samples=samples)
def view_layer_only(phone_pass):
    for lc in sc.view_layers[0].layer_collection.children:
        if lc.collection == ui: lc.exclude = not phone_pass
    scr.hide_render = phone_pass
frames = [int(x) for x in A.still.split(',')] if A.still else list(range(F0, F1 + 1))
pdir = os.path.join(A.out, 'phone2'); os.makedirs(pdir, exist_ok=True)
view_layer_only(True); setup(A.phone_res, A.phone_samples)
saved = [(m, m.camera) for m in sc.timeline_markers]
for m in sc.timeline_markers: m.camera = None
sc.camera = pcam
for f in sorted(set(frames)):
    p = os.path.join(pdir, 'p_%04d.png' % f)
    if os.path.exists(p) and os.path.getsize(p) > 0: continue
    sc.frame_set(f); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
for m, c in saved: m.camera = c
view_layer_only(False); setup(A.res, A.samples)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in frames:
        stex.image = bpy.data.images.load(os.path.join(pdir, 'p_%04d.png' % f)); sc.frame_set(f); cam_at(f)
        sc.render.filepath = os.path.join(A.out, 'd_%04d.png' % f); bpy.ops.render.render(write_still=True)
else:
    img = bpy.data.images.load(os.path.join(pdir, 'p_%04d.png' % F0)); img.source = 'SEQUENCE'; stex.image = img
    stex.image_user.frame_start = F0; stex.image_user.frame_offset = F0 - 1; stex.image_user.frame_duration = F1 - F0 + 1; stex.image_user.use_auto_refresh = True
    cam_at(F0)
    if A.video:
        sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
        sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
        bpy.ops.render.render(animation=True)
    else:
        for f in range(F0, F1 + 1):
            sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'd_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.DESK_RANGES, late=CP.LATE, t_drop=T_DROP, scan_ng=CP.T_SCAN_NG,
               events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_no', 'beep_yes')], shots=SH),
          open(os.path.join(A.out, 'qrc2t_log_%d.json' % F0), 'w'), default=float)
print('QRC2T DONE', F0, F1)
