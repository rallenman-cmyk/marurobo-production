# QRコード回・1章のはじめ「画面に飛び込む」の本番描画（PC・Blender 4.3.2・EEVEE）。冒頭と同じ机・QRの紙・スマホ（1 〜 F_TABLE_END）
#   1回の実行で2段に描く：① スマホのカメラの絵（画面に貼る）→ ② 本番の絵
#   blender -b --factory-startup --python qr_c1_table.py -- --blend story.blend --out DIR --frames 1:247 --video 1
#   確認用：--standin 1（仮のまるロボ）。--still 100,200 で指定のコマだけ
#   動き：画面の前で見上げる → 画面の下へ歩く → 高く跳んで、上を向いた画面へ頭から飛び込む（画面に波紋）→ カメラが画面の中へ
import sys, os, math, json, argparse
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
from c1_timeline import *
import c1_plan as CP
import op_timeline as OPT
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc1t'); ap.add_argument('--frames', default='1:%d' % F_TABLE_END)
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc1t_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--phone_res', nargs=2, type=int, default=[1080, 2240]); ap.add_argument('--phone_samples', type=int, default=16)
ap.add_argument('--still', default='')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
def fr_of(t): return int(round(t * FPS)) + 1
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def link(ob, coll=None): (coll or sc.collection).objects.link(ob); return ob
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
N, QZ, MODT = OPT.N, OPT.QZ, OPT.MOD

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
# 飛び込んだあと、画面が少し明るくなる（中へ入っていく合図）
for t, s in ((0.0, 1.0), (T_ENTER, 1.0), (T_TABLE_END, 1.7)): sem.inputs['Strength'].default_value = s; sem.inputs['Strength'].keyframe_insert('default_value', frame=fr_of(t))
metal = W.mat('Stand metal', W.srgb('#3A3F46'), rough=0.35, metal=0.8)
foot = Vector((cphone.x, cphone.y - 0.9, 0)); base = W.cyl('Stand base', 0.45, 0.08, metal); base.location = (foot.x, foot.y, 0.04)
d = (cphone + back * 0.2) - foot; pole = W.cyl('Stand pole', 0.06, d.length, metal); pole.location = foot + d / 2; pole.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

# ================================================================ まるロボ（卓上の予定）。画面の面を越えた所は画面とスマホの体が隠す → 通り抜けたら消す
plan, FR, EV = CP.table_frames()
T_CROSS, T_GONE = EV['t_cross'], EV['t_gone']; P_CROSS = Vector(EV['p_cross'])
if A.standin:
    import op_stage_standin as SI
    rroot, rtorso, rlegs = SI.build_robot()
    for f in range(F0, F1 + 1): SI.pose(rroot, rtorso, rlegs, FR[min(len(FR) - 1, f - 1)], key=f)
    robot_objs = hier(rroot)
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
    bk.write(); robot_objs = hier(O['Maru'])
for ob in robot_objs:
    if ob.hide_render: continue
    for f, h in ((1, False), (fr_of(T_GONE) + 1, True)): ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)

# ---------------------------------------------------------------- 画面の波紋（入った所から 3 重の輪が広がる）＋ しぶきのような光の粒
rm = W.mat_emit('Ripple', W.srgb('#7FE3F0'), 3.0)
hit = P_CROSS - NRM * NRM.dot(P_CROSS - SCR_C) + NRM * 0.012          # 画面の面の上の点
rot = NRM.to_track_quat('Z', 'Y').to_euler()
for k in range(3):
    t0 = T_CROSS + 0.10 * k; ring = W.torus('Ripple %d' % k, 1.0, 0.035, rm, seg=64); ring.location = hit; ring.rotation_euler = rot; ring.visible_shadow = False
    for f in range(fr_of(t0) - 1, fr_of(T_TABLE_END) + 1):
        u = max(0.0, ((f - 1) / FPS - t0) / 0.9); s = max(0.001, 0.08 + 0.95 * (1 - (1 - min(u, 1.0)) ** 2)); ring.scale = (s, s, 1 + 0.0 * s); ring.keyframe_insert('scale', frame=f)
    for f, h in ((1, True), (fr_of(t0), False), (fr_of(T_TABLE_END) + 1, True)): ring.hide_render = h; ring.keyframe_insert('hide_render', frame=f)
pm_ = W.mat_emit('Splash', W.srgb('#BFF4FA'), 4.0); rng = np.random.default_rng(3)
for k in range(10):
    a = rng.uniform(0, 2 * math.pi); sp = rng.uniform(0.6, 1.3); up = rng.uniform(0.8, 1.6)
    dirv = (px * math.cos(a) + py * math.sin(a)) * sp + NRM * up
    dot = W.box('Splash %d' % k, (0.06, 0.06, 0.06), pm_, bevel=0.03, seg=2); dot.visible_shadow = False
    for f in range(fr_of(T_CROSS), fr_of(T_CROSS + 0.7) + 1):
        t = (f - 1) / FPS - T_CROSS; dot.location = hit + dirv * t + Vector((0, 0, -4.9 * t * t)); dot.keyframe_insert('location', frame=f)
    for f, h in ((1, True), (fr_of(T_CROSS), False), (fr_of(T_CROSS + 0.7), True)): dot.hide_render = h; dot.keyframe_insert('hide_render', frame=f)

# ================================================================ カメラ
def look_rot(loc, look): return (look - loc).to_track_quat('-Z', 'Y').to_euler()
def new_cam(name, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 400; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    return link(O.new(name, cd))
STAND = Vector((CP.T_STANDPT[0], CP.T_STANDPT[1], 0))
T_C1 = EV['t_takeoff'] - 1.0; T_C2 = T_CROSS + 0.12
# C0：画面とまるロボを右前から（見上げる→歩く）
c0 = new_cam('Cam t0 front', 30); L0, T0_ = Vector((4.6, -12.6, 3.0)), Vector((0.3, -5.0, 1.45))
c0.rotation_euler = look_rot(L0, T0_)
for t, dd in ((0.0, 0.0), (T_C1, 0.08)): c0.location = L0 + (T0_ - L0) * dd; c0.keyframe_insert('location', frame=fr_of(t))
# C1：高く跳ぶ → 上を向いた画面へ頭から（画面の正面より少し右・高めから）
c1 = new_cam('Cam t1 jump', 26); L1, T1_ = Vector((3.6, -9.0, 4.4)), Vector((0.1, -4.0, 2.1))
c1.rotation_euler = look_rot(L1, T1_)
for t, dd in ((T_C1, 0.0), (T_C2, 0.05)): c1.location = L1 + (T1_ - L1) * dd; c1.keyframe_insert('location', frame=fr_of(t))
# C2：画面の正面から、画面の中へ寄っていく。最後は画面の横幅いっぱい（＝中の世界の最初のカメラと同じ絵）
c2 = new_cam('Cam t2 into', 30)
Rc = Matrix((px, py, NRM)).transposed().to_euler()
d_end = (PW - 0.12) * 30 / 36 * 0.98
for f in range(fr_of(T_C2), F1 + 2):
    u = ease(((f - 1) / FPS - T_C2) / max(0.1, T_TABLE_END - T_C2)) ** 1.3
    dist = 3.4 + (d_end - 3.4) * u
    c2.location = SCR_C + NRM * dist; c2.rotation_euler = Rc; c2.keyframe_insert('location', frame=f); c2.keyframe_insert('rotation_euler', frame=f)
for k, (t0, cam) in enumerate(((0.0, c0), (T_C1, c1), (T_C2, c2))):
    m = sc.timeline_markers.new('t%d' % k, frame=fr_of(t0)); m.camera = cam
sc.camera = c0

# ================================================================ スマホの画面の中の表示（読み取りの枠と「HELLO」）＝スマホのカメラにだけ映る。飛び込む少し前に消える
ui = bpy.data.collections.new('Phone UI'); sc.collection.children.link(ui)
pcd = bpy.data.cameras.new('PhoneCam'); pcd.lens = 34; pcd.sensor_fit = 'HORIZONTAL'
pcam = link(O.new('PhoneCam', pcd)); pcam.location = LENS_V + back * 0.05; pcam.rotation_euler = (AIM_V - LENS_V).to_track_quat('-Z', 'Y').to_euler()
pw, ph = A.phone_res; asp = ph / pw; zd = 0.5; hw = zd * 18 / 34; hh = hw * asp
def ui_obj(name, ob):
    for c in ob.users_collection: c.objects.unlink(ob)
    ui.objects.link(ob); ob.parent = pcam; return ob
cm = bpy.data.materials.new('Scan corner'); cm.use_nodes = True; cnt = cm.node_tree; cnt.nodes.clear()
ce = cnt.nodes.new('ShaderNodeEmission'); co = cnt.nodes.new('ShaderNodeOutputMaterial'); cnt.links.new(ce.outputs[0], co.inputs[0]); ce.inputs['Color'].default_value = (*W.srgb('#78DC8C'), 1)
k_ = hw * 0.72; cy0 = -hh * 0.16; arm = hw * 0.22; th = hw * 0.035; ui_objs = []
for sx in (-1, 1):
    for sy in (-1, 1):
        for horiz in (True, False):
            bpy.ops.mesh.primitive_plane_add(size=1); p = ui_obj('corner', bpy.context.object); p.data.materials.append(cm)
            cx_, cy_ = sx * k_, cy0 + sy * k_
            p.location = (cx_ - sx * arm / 2, cy_, -zd) if horiz else (cx_, cy_ - sy * arm / 2, -zd)
            p.scale = (arm, th, 1) if horiz else (th, arm, 1); ui_objs.append(p)
bm_ = bpy.data.materials.new('Banner'); bm_.use_nodes = True; bnt = bm_.node_tree; bnt.nodes.clear()
be = bnt.nodes.new('ShaderNodeEmission'); bo = bnt.nodes.new('ShaderNodeOutputMaterial'); bnt.links.new(be.outputs[0], bo.inputs[0]); be.inputs['Color'].default_value = (*W.srgb('#F8F8F6'), 1); be.inputs['Strength'].default_value = 1.6
bpy.ops.mesh.primitive_plane_add(size=1); banner = ui_obj('Banner', bpy.context.object); banner.data.materials.append(bm_)
banner.location = (0, hh * 0.78, -zd + 0.001); banner.scale = (hw * 1.8, hh * 0.36, 1); ui_objs.append(banner)
font = None
for fp in (A.font, os.path.join(HERE, 'japanese.ttc'), 'C:/Windows/Fonts/meiryo.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'):
    if fp and os.path.exists(fp): font = bpy.data.fonts.load(fp); break
tm = W.mat_emit('Banner text', W.srgb('#1E2228'), 1.0); tm2 = W.mat_emit('Banner label', W.srgb('#6E747C'), 1.0)
for body, size, y, mat_ in (('テキスト', hh * 0.10, hh * 0.86, tm2), ('HELLO', hh * 0.22, hh * 0.67, tm)):
    cu = bpy.data.curves.new(body, 'FONT'); cu.body = body; cu.size = size
    if font: cu.font = font
    t = ui_obj('Text ' + body, link(O.new('Text ' + body, cu))); t.location = (-hw * 0.80, y, -zd + 0.002); t.data.materials.append(mat_); ui_objs.append(t)
for ob in ui_objs:
    for f, h in ((1, False), (fr_of(EV['t_takeoff']), True)): ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)

# ================================================================ 描く
def setup(res, samples): W.render_setup(sc, engine='eevee', res=tuple(res), samples=samples)
def view_layer_only(phone_pass):
    for lc in sc.view_layers[0].layer_collection.children:
        if lc.collection == ui: lc.exclude = not phone_pass
    scr.hide_render = phone_pass
frames = [int(x) for x in A.still.split(',')] if A.still else list(range(F0, F1 + 1))
# ① スマホのカメラの絵（まるロボはスマホの後ろなので映らない）
pdir = os.path.join(A.out, 'phone'); os.makedirs(pdir, exist_ok=True)
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
json.dump(dict(fps=FPS, frames=[F0, F1], events=[e for e in plan.events if e['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_happy')],
               t_cross=T_CROSS, t_gone=T_GONE, t_takeoff=EV['t_takeoff']), open(os.path.join(A.out, 'qrc1t_log.json'), 'w'), default=float)
print('QRC1T DONE', F0, F1)
