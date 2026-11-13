# QRコード回・冒頭（S01〜S04、0:00〜1:08.6）の本番描画（PC・Blender 4.3.2・EEVEE）
#   1回の実行で2段に描く：① スマホのカメラの絵（画面に貼る）→ ② 本番の絵（その絵をスマホの画面に貼る）
#   blender -b --factory-startup --python qr_op_stage.py -- --blend story.blend --out DIR --frames 1:100 --video 1 [--res 1920 1080] [--samples 32]
#   確認用（本物のまるロボがないとき）：--standin 1 で仮のまるロボ
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
from op_timeline import *
import op_plan
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrop'); ap.add_argument('--frames', default='1:1795')
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrop2_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--phone_res', nargs=2, type=int, default=[540, 1120]); ap.add_argument('--phone_samples', type=int, default=16)
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':')); FPS = 24
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
def link(ob, coll=None): (coll or sc.collection).objects.link(ob); return ob
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out

# ================================================================ 舞台：机・QRの紙・光（A案：左前から・高さ50°・5600K）
W.sky_and_sun(sc, az_deg=135.0, el_deg=50.0, sky_strength=0.35, sun_energy=4.0)
desk = W.box('Desk', (16, 12, 0.3), W.mat('Desk wood', W.srgb('#B98A5E'), rough=0.55), bevel=0.03); desk.location = (0, 0, -0.15)
pm = bpy.data.materials.new('QR paper'); pm.use_nodes = True; nt = pm.node_tree; bs = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.join(HERE, 'qr_paper.png')); tex.interpolation = 'Closest'
nt.links.new(tex.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
side = (N + 2 * QZ) * MOD
bpy.ops.mesh.primitive_plane_add(size=side, location=(0, 0, 0.004)); paper = bpy.context.object; paper.name = 'QR paper'; paper.data.materials.append(pm)

# ================================================================ スマホ（手前に斜めに立てる。裏のカメラがQRを向く）
LENS_V, AIM_V = Vector(LENS), Vector(AIM); PW, PH, PT = PHONE_SIZE
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
stex = snt.nodes.new('ShaderNodeTexImage'); snt.links.new(stex.outputs[0], sem.inputs['Color']); sem.inputs['Strength'].default_value = 1.0
bpy.ops.mesh.primitive_plane_add(size=1); scr = bpy.context.object; scr.name = 'Phone screen'; scr.data.materials.append(smat)
place(scr, cphone - back * (PT / 2 + 0.005), (PW - 0.12, PH - 0.12, 1))
metal = W.mat('Stand metal', W.srgb('#3A3F46'), rough=0.35, metal=0.8)
foot = Vector((cphone.x, cphone.y - 0.9, 0)); base = W.cyl('Stand base', 0.45, 0.08, metal); base.location = (foot.x, foot.y, 0.04)
d = (cphone + back * 0.2) - foot; pole = W.cyl('Stand pole', 0.06, d.length, metal); pole.location = foot + d / 2; pole.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
# 見ている範囲の線（最初の読み取りだけ。T_LINES のあいだだけ見える）
lines_coll = bpy.data.collections.new('View lines'); sc.collection.children.link(lines_coll)
lm = W.mat_emit('View line', W.srgb('#7FE3F0'), 3.0); hs = N * MOD / 2
for cx, cy in ((-hs, hs), (hs, hs), (hs, -hs), (-hs, -hs)):
    dv = Vector((cx, cy, 0.01)) - LENS_V; ln = W.cyl('View line', 0.012, dv.length, lm, seg=8, coll=lines_coll)
    ln.location = LENS_V + dv / 2; ln.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); ln.visible_shadow = False
    for f, h in ((1, True), (int(T_LINES[0] * FPS), True), (int(T_LINES[0] * FPS) + 1, False), (int(T_LINES[1] * FPS), False), (int(T_LINES[1] * FPS) + 1, True)):
        ln.hide_render = h; ln.keyframe_insert('hide_render', frame=f)

# ================================================================ まるロボ（本物：story.blend の「Maru」に marurig で予定を当てる）
plan = op_plan.plan(); FR = mm.simulate(plan, fps=FPS, t_end=T_END + 0.5)
if A.standin:
    import op_stage_standin as SI
    root, torso, legs = SI.build_robot()
    for f in range(F0, F1 + 1): SI.pose(root, torso, legs, FR[min(len(FR) - 1, f - 1)], key=f)
    def pose(f): pass
else:
    import marurig as mr
    blend = A.blend; assert os.path.exists(blend), 'story.blend が見つからない。--blend で指定する'
    with bpy.data.libraries.load(blend, link=False) as (src, dst): dst.objects = [n for n in src.objects]
    loaded = [o for o in dst.objects if o is not None]; maru0 = next(o for o in loaded if o.name == 'Maru')
    keep = {o.name for o in hier(maru0)}
    for o in loaded:
        if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
    for n in keep: link(O[n])
    for n in keep:
        ob = O[n]
        if ob.animation_data: ob.animation_data_clear()
    for o in hier(O['Maru']):
        if o.name.startswith(('Cradle', 'Maru cargo')) or 'cradle' in o.name.lower(): o.hide_render = True
    rig = mr.MaruRig(O['Maru']); bk = mr.Baker()
    for i, fr in enumerate(FR):
        if F0 - 2 <= i + 1 <= F1 + 2: rig.apply(fr, i + 1, bk)
    bk.write()
    def pose(f): pass

# ================================================================ カメラ（カットごと。タイムラインの印でカメラを切り替える）
# SHOTS は op_timeline から（確認用動画と同じ）
VIEWS = {'shoulder': ((-0.95, -6.7, 4.45), (0.10, 0.05, 1.25), 30), 'wide': ((6.4, -4.6, 3.4), (0.2, -0.6, 1.0), 22),
         'wide2': ((5.6, 2.6, 2.6), (0.6, -0.9, 0.8), 24), 'close': ((0.05, -2.15, 0.62), (0.78, -0.78, 0.55), 30),
         'med': ((-0.35, -2.55, 1.15), (0.55, -0.55, 0.9), 30), 'low': ((-2.6, 2.9, 0.42), (0.6, -0.6, 0.25), 22),
         'face': ((3.4, -4.4, 1.0), (2.2, -0.4, 0.75), 36)}
def ease(u): return u * u * (3 - 2 * u)
for k, (t0, t1, v, d0, d1) in enumerate(SHOTS):
    loc, look, lens = VIEWS[v]; cd = bpy.data.cameras.new('Cam %d %s' % (k, v)); cd.lens = lens; cd.clip_end = 400
    cam = link(O.new('Cam %d %s' % (k, v), cd)); L, T = Vector(loc), Vector(look)
    cam.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler()
    for t, dd in ((t0, d0), (t1, d1)):                           # ゆっくり寄る（見る点へ向かって距離の dd だけ進む）
        cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=round(t * FPS) + 1)
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'AUTO'
    m = sc.timeline_markers.new('shot %d' % k, frame=round(t0 * FPS) + 1); m.camera = cam
    if k == 0: sc.camera = cam

# ================================================================ スマホの画面の中の表示（読み取りの枠・結果）＝スマホのカメラにだけ映る
ui = bpy.data.collections.new('Phone UI'); sc.collection.children.link(ui)
pcd = bpy.data.cameras.new('PhoneCam'); pcd.lens = 34; pcd.sensor_fit = 'HORIZONTAL'
pcam = link(O.new('PhoneCam', pcd)); pcam.location = LENS_V + back * 0.05; pcam.rotation_euler = (AIM_V - LENS_V).to_track_quat('-Z', 'Y').to_euler()
pw, ph = A.phone_res; asp = ph / pw; zd = 0.5; hw = zd * 18 / 34; hh = hw * asp     # 近い面の上の半分の幅・高さ
def ui_obj(name, ob):
    for c in ob.users_collection: c.objects.unlink(ob)
    ui.objects.link(ob); ob.parent = pcam; return ob
col_scan, col_ok = W.srgb('#FFD640'), W.srgb('#78DC8C')
cm = bpy.data.materials.new('Scan corner'); cm.use_nodes = True; cnt = cm.node_tree; cnt.nodes.clear()
ce = cnt.nodes.new('ShaderNodeEmission'); co = cnt.nodes.new('ShaderNodeOutputMaterial'); cnt.links.new(ce.outputs[0], co.inputs[0]); ce.inputs['Strength'].default_value = 1.0
k_ = hw * 0.72; cy0 = -hh * 0.16; arm = hw * 0.22; th = hw * 0.035
for sx in (-1, 1):
    for sy in (-1, 1):
        for horiz in (True, False):
            bpy.ops.mesh.primitive_plane_add(size=1); p = ui_obj('corner', bpy.context.object); p.data.materials.append(cm)
            cx_, cy_ = sx * k_, cy0 + sy * k_
            p.location = (cx_ - sx * arm / 2, cy_, -zd) if horiz else (cx_, cy_ - sy * arm / 2, -zd)
            p.scale = (arm, th, 1) if horiz else (th, arm, 1)
bm_ = bpy.data.materials.new('Banner'); bm_.use_nodes = True; bnt = bm_.node_tree; bnt.nodes.clear()
be = bnt.nodes.new('ShaderNodeEmission'); bo = bnt.nodes.new('ShaderNodeOutputMaterial'); bnt.links.new(be.outputs[0], bo.inputs[0]); be.inputs['Color'].default_value = (*W.srgb('#F8F8F6'), 1); be.inputs['Strength'].default_value = 1.6
bpy.ops.mesh.primitive_plane_add(size=1); banner = ui_obj('Banner', bpy.context.object); banner.data.materials.append(bm_)
banner.location = (0, hh * 0.78, -zd + 0.001); banner.scale = (hw * 1.8, hh * 0.36, 1)
font = None
for fp in (A.font, os.path.join(HERE, 'japanese.ttc'), 'C:/Windows/Fonts/meiryo.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'):
    if fp and os.path.exists(fp): font = bpy.data.fonts.load(fp); break
tm = W.mat_emit('Banner text', W.srgb('#1E2228'), 1.0); tm2 = W.mat_emit('Banner label', W.srgb('#6E747C'), 1.0)
txts = []
for body, size, y, mat_ in (('テキスト', hh * 0.10, hh * 0.86, tm2), ('HELLO', hh * 0.22, hh * 0.67, tm)):
    cu = bpy.data.curves.new(body, 'FONT'); cu.body = body; cu.size = size
    if font: cu.font = font
    t = ui_obj('Text ' + body, link(O.new('Text ' + body, cu))); t.location = (-hw * 0.80, y, -zd + 0.002); t.data.materials.append(mat_); txts.append(t)
# 状態（scan／hello）をコマにキー
for a, s in SCREEN:
    f = round(a * FPS) + 1; ok = (s == 'hello')
    ce.inputs['Color'].default_value = (*(col_ok if ok else col_scan), 1); ce.inputs['Color'].keyframe_insert('default_value', frame=f)
    for ob in [banner] + txts:
        ob.hide_render = not ok; ob.keyframe_insert('hide_render', frame=f)
for c in (ce.inputs['Color'],):
    for fc in cm.node_tree.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ================================================================ 描く
def setup(res, samples):
    W.render_setup(sc, engine='eevee', res=tuple(res), samples=samples)
def view_layer_only(phone_pass):
    vl = sc.view_layers[0]
    for lc in vl.layer_collection.children:
        if lc.collection == ui: lc.exclude = not phone_pass
        if lc.collection == lines_coll: lc.exclude = phone_pass
    scr.hide_render = phone_pass                                    # スマホのカメラは自分の画面を映さない
# ① スマホのカメラの絵
pdir = os.path.join(A.out, 'phone'); os.makedirs(pdir, exist_ok=True)
view_layer_only(True); setup(A.phone_res, A.phone_samples)
markers = list(sc.timeline_markers); saved = [(m, m.camera) for m in markers]
for m in markers: m.camera = None
sc.camera = pcam
for f in range(F0, F1 + 1):
    p = os.path.join(pdir, 'p_%04d.png' % f)
    if os.path.exists(p) and os.path.getsize(p) > 0: continue
    sc.frame_set(f); pose(f); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
# ② 本番：①の絵をスマホの画面に
img = bpy.data.images.load(os.path.join(pdir, 'p_%04d.png' % F0)); img.source = 'SEQUENCE'; stex.image = img
stex.image_user.frame_start = F0; stex.image_user.frame_offset = F0 - 1; stex.image_user.frame_duration = F1 - F0 + 1; stex.image_user.use_auto_refresh = True
for m, c in saved: m.camera = c
view_layer_only(False); setup(A.res, A.samples)
if A.video:
    sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); pose(f); sc.render.filepath = os.path.join(A.out, 'f_%04d.png' % f); bpy.ops.render.render(write_still=True)
# 記録（足音の時刻など。組み立てで使う）
json.dump(dict(fps=FPS, frames=[F0, F1], events=[e for e in plan.events if e['kind'] in ('step', 'step_turn', 'takeoff', 'land')],
               shots=SHOTS, screen=SCREEN, lines=T_LINES), open(os.path.join(A.out, 'qrop_log.json'), 'w'), default=float)
print('QROP DONE', F0, F1)
