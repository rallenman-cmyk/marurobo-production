# QRコード回・4章「直す」の数字の空間（C1〜C12・R1〜R3）の本番描画（PC・Blender 4.3.2・EEVEE）。台本 v2.0 の時刻（c4_v20_times.json）
#   blender -b --factory-startup --python qr_c4_crates.py -- --blend story.blend --out DIR --frames 1134:1318 --video 1 --vprefix qrc4c_
#   確認用：--standin 1（仮のまるロボ）。--still 2000,4000 で指定のコマだけ PNG
#   字の決まり：メモ・式・×1×2×3・目盛りの数字・名前は 2D で重ねる。青い箱の数字（2・5・3・7・46）だけは箱の顔として 3D に大きく書く
#   中身：箱が順に降りてくる → 布で隠す → 取れて 5 → 黒い汚れが落ちて 7 に見える → 台がせり上がる → 2 番目が光る → 7 が 5 に戻る／
#         0〜255 の輪を光の点が 1 周 → たくさんの予備の札から箱へ線
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import c4_plan as CP
from c4_plan import FPS, s, e, fr_of, XS
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc4c'); ap.add_argument('--frames', default='%d:%d' % (fr_of(CP.CRATE_RANGES[0][0]), fr_of(CP.CRATE_RANGES[0][1])))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc4c_'); ap.add_argument('--standin', type=int, default=0)
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
FONT = None
for fp in (A.font, os.path.join(HERE, 'japanese.ttc'), 'C:/Windows/Fonts/meiryob.ttc', 'C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'):
    if fp and os.path.exists(fp): FONT = bpy.data.fonts.load(fp); break
def number(body, col, size, parent, loc):
    cu = bpy.data.curves.new('num ' + body, 'FONT'); cu.body = body; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = 0.02
    if FONT: cu.font = FONT
    t = W.link(O.new('num ' + body, cu)); t.data.materials.append(W.mat_emit('num ' + body + col, W.srgb(col), 4.0)); t.parent = parent; t.location = loc; t.rotation_euler = (math.radians(90), 0, 0); return t

# ================================================================ スタジオ（明るい灰色の空間）
wd = bpy.data.worlds.new('C space'); sc.world = wd; wd.use_nodes = True; bg = wd.node_tree.nodes['Background']; bg.inputs[0].default_value = (*W.srgb('#E4EAF0'), 1); bg.inputs[1].default_value = 0.55
fl = W.box('floor', (400, 400, 0.2), W.mat('floor', W.srgb('#F3F5F7'), rough=0.7)); fl.location = (0, 0, -0.1)
la = bpy.data.lights.new('key', 'AREA'); la.shape = 'DISK'; la.size = 30; la.energy = 14000; k_ = W.link(O.new('key', la)); k_.location = (-4, -10, 22); k_.rotation_euler = (math.radians(25), 0, math.radians(-10))
ls = bpy.data.lights.new('sun', 'SUN'); ls.energy = 2.0; ls.angle = math.radians(4); s_ = W.link(O.new('sun', ls)); s_.rotation_euler = (math.radians(40), 0, math.radians(-30))
BLUE, TEAL, ORANGE = '#3F86DD', '#14A3B4', '#F0953A'
T_R1 = CP.shot_start('R1'); T_R2 = CP.shot_start('R2')
C_SPAN = [(0.0, T_R1)]                                   # 数字の箱（C）が見える間

# ================================================================ C：青い箱 3 つ（数字は顔に大きく）
crate_m = W.mat('crate', W.srgb(BLUE), rough=0.45)
CRATE_COL = ('#3478D2', '#DE7618', '#229254')            # v12 #63：1番目・2番目・3番目の箱を、メモの数字・×1×2×3 の札と同じ色に（青・橙・緑）
CR = []
for k in range(3):
    root = W.link(O.new('Crate %d' % k, None)); b = W.box('crate%d body' % k, (2.4, 2.0, 2.4), W.mat('crate %d' % k, W.srgb(CRATE_COL[k]), rough=0.45), bevel=0.08); b.parent = root
    CR.append(dict(root=root, body=b))
NUM = {}
for k, n in enumerate('253'): NUM[(k, n)] = number(n, '#FFFFFF', 2.3, CR[k]['root'], (0, -1.03, 0.0))
NUM[(1, '7')] = number('7', '#FFFFFF', 2.3, CR[1]['root'], (0, -1.03, 0.0)); NUM[(1, '5c')] = number('5', '#7FE3F0', 2.3, CR[1]['root'], (0, -1.035, 0.0))
z_floor, z_stand = 1.2, 1.55
for k in range(3):
    r = CR[k]['root']; t_in = CP.T_CRATES[k] if k else 0.0
    pts = [(0.0, (XS[k], 0, z_floor if k == 0 else 9.0))]
    if k: pts += [(t_in, (XS[k], 0, 9.0)), (t_in + 0.45, (XS[k], 0, z_floor - 0.08)), (t_in + 0.6, (XS[k], 0, z_floor))]
    pts += [(CP.T_STANDS, (XS[k], 0, z_floor)), (CP.T_STANDS + 0.5, (XS[k], 0, z_stand))]
    keys(r, 'location', pts)
    show(CR[k]['body'], [(0.0 if k == 0 else t_in, T_R1)])            # 数字は下で別に出し入れする
show(NUM[(1, '5')], [(CP.T_CRATES[1], CP.T_STAIN[1]), ]); show(NUM[(1, '7')], [(CP.T_STAIN[1], CP.T_FIX)]); show(NUM[(1, '5c')], [(CP.T_FIX, T_R1)])
show(NUM[(0, '2')], C_SPAN); show(NUM[(2, '3')], [(CP.T_CRATES[2], T_R1)])
# 布：真ん中の箱を隠す → 取れる
cloth = W.box('cloth', (2.75, 2.35, 2.7), W.mat('cloth', W.srgb('#8A9097'), rough=0.9), bevel=0.35, seg=4)
keys(cloth, 'location', [(CP.T_CLOTH, (XS[1], 0, 7.0)), (CP.T_CLOTH + 0.45, (XS[1], 0, z_floor + 0.15)), (CP.T_REVEAL, (XS[1], 0, z_floor + 0.15)), (CP.T_REVEAL + 0.6, (XS[1], 0, 8.0))])
show(cloth, [(CP.T_CLOTH, CP.T_REVEAL + 0.6)])
# 黒い汚れ：落ちてきて、5 の上に貼りつく（7 に見える）→ 直ったら消える
stain_m = W.mat('stain', (0.01, 0.012, 0.014), rough=0.15, coat=0.6)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); st = bpy.context.object; st.name = 'stain'; st.data.materials.append(stain_m)
st.parent = CR[1]['root']
keys(st, 'location', [(CP.T_STAIN[0], (0.3, -0.6, 3.0)), (CP.T_STAIN[1] - 0.05, (0.35, -1.05, 0.45))], kind='LINEAR')
keys(st, 'scale', [(CP.T_STAIN[0], (0.35, 0.35, 0.3)), (CP.T_STAIN[1] - 0.05, (0.35, 0.35, 0.3)), (CP.T_STAIN[1] + 0.1, (0.55, 0.05, 0.42)), (CP.T_FIX, (0.55, 0.05, 0.42)), (CP.T_FIX + 0.6, (0.01, 0.01, 0.01))])
show(st, [(CP.T_STAIN[0], CP.T_FIX + 0.6)])
# 台（×1 ×2 ×3 の字は 2D）：せり上がる → 2 番目が光る
for k in range(3):
    sd = W.box('stand %d' % k, (2.8, 2.3, 0.35), W.mat('stand', W.srgb('#C9D3DD'), rough=0.5), bevel=0.05)
    keys(sd, 'location', [(CP.T_STANDS, (XS[k], 0, -0.2)), (CP.T_STANDS + 0.5, (XS[k], 0, 0.175))]); show(sd, [(CP.T_STANDS, T_R1)])
    if k == 1:
        g = W.box('stand glow', (2.84, 2.34, 0.36), W.mat_emit('stand g', W.srgb('#FFD640'), 2.5), bevel=0.05); g.location = (XS[k], 0, 0.175); show(g, [(CP.T_GLOW2, T_R1)])

# ================================================================ R1：箱「46」と 0〜255 の輪（目盛りの数字は 2D）。光の点が 1 周
R_SPAN1 = [(T_R1, T_R2)]
b46 = W.box('crate 46', (2.4, 2.0, 2.4), crate_m, bevel=0.08); b46.location = (0, 0, 1.55); show(b46, R_SPAN1)
t46 = number('46', '#FFFFFF', 1.7, None, (0, -1.03, 1.55)); show(t46, R_SPAN1)
rm = W.mat_emit('ring', W.srgb(TEAL), 2.0); ring = W.torus('ring', 3.4, 0.09, rm, seg=96); ring.location = (0, 0.1, 1.9); ring.rotation_euler = (math.radians(90), 0, 0); show(ring, R_SPAN1)
for k in range(32):
    a = math.pi / 2 - 2 * math.pi * k / 32; L = 0.45 if k % 8 == 0 else 0.22
    p0 = Vector((math.cos(a) * 3.4, 0.0, 1.9 + math.sin(a) * 3.4)); p1 = Vector((math.cos(a) * (3.4 + L), 0.0, 1.9 + math.sin(a) * (3.4 + L))); dv = p1 - p0
    tk = W.cyl('tick %d' % k, 0.035, dv.length, rm, seg=8); tk.location = p0 + dv / 2; tk.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); show(tk, R_SPAN1)
dot = W.link(O.new('dial dot', None))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(0, 0, 0)); dm = bpy.context.object; dm.name = 'dial dot m'; dm.data.materials.append(W.mat_emit('dot', W.srgb('#FFD640'), 8.0))
for f in range(fr_of(CP.T_DIAL[0]), fr_of(CP.T_DIAL[1]) + 1):
    u = ease(((f - 1) / FPS - CP.T_DIAL[0]) / (CP.T_DIAL[1] - CP.T_DIAL[0])); a = math.pi / 2 - 2 * math.pi * u * 0.996
    dm.location = (math.cos(a) * 3.4, -0.15, 1.9 + math.sin(a) * 3.4); dm.keyframe_insert('location', frame=f)
show(dm, [(CP.T_DIAL[0], T_R2)])
# R2・R3：たくさんの予備の札（字なし）から、5 つの箱へ光の線（真ん中の箱は壊れた灰色）
R_SPAN2 = [(T_R2, CP.CRATE_RANGES[-1][1] + 1)]
xs = [-6.4, -3.2, 0.0, 3.2, 6.4]
for k, x in enumerate(xs):
    b = W.box('c5 %d' % k, (1.9, 1.6, 1.9), W.mat('crate g' if k == 2 else 'crate', W.srgb('#8A9097' if k == 2 else BLUE), rough=0.45), bevel=0.07); b.location = (x, 0, 0.95); show(b, R_SPAN2)
for j in range(6):
    x = -7.5 + j * 3.0; p = W.box('memo %d' % j, (2.2, 0.12, 1.3), W.mat('memo', W.srgb('#FBE3C8'), rough=0.6), bevel=0.05); p.location = (x, 4.5, 4.8); show(p, R_SPAN2)
    fr_ = W.box('memo edge %d' % j, (2.35, 0.1, 1.45), W.mat('memo edge', W.srgb(ORANGE), rough=0.6), bevel=0.05); fr_.location = (x, 4.6, 4.8); show(fr_, R_SPAN2)
    for k, xc in enumerate(xs):
        if (j + k) % 2: continue
        p0, p1 = Vector((x, 4.4, 4.2)), Vector((xc, -0.1, 1.95)); dv = p1 - p0; t0 = CP.T_LINKS + 0.15 * (j * 5 + k) / 2
        bm = W.cyl('link %d %d' % (j, k), 0.03, 1.0, W.mat_emit('link', W.srgb('#FFB060'), 2.5), seg=8); bm.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); bm.visible_shadow = False
        keys(bm, 'location', [(t0, p0), (t0 + 0.4, p0 + dv / 2)], kind='LINEAR'); keys(bm, 'scale', [(t0, (1, 1, 0.001)), (t0 + 0.4, (1, 1, dv.length))], kind='LINEAR')
        show(bm, [(t0, R_SPAN2[0][1])])

# ================================================================ まるロボ
plan, FR = CP.crate_frames()
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

# ================================================================ カメラ（箱は左半分に大きく。右半分に 2D のメモ）
C = lambda *v: Vector(v)
CC = (C(1.6, -15.0, 4.2), C(1.6, 0, 1.9), 30)
VIEWS = {'C1': (C(-2.6, -10.5, 3.6), C(-4.4, 0, 1.6), 30), 'C6a': (C(XS[1] + 1.4, -7.4, 3.4), C(XS[1], 0, 2.0), 30), 'C6': (C(XS[1] + 1.4, -7.4, 3.4), C(XS[1], 0, 2.0), 30),
         'R1': (C(1.0, -15.0, 3.8), C(0.6, 0, 2.4), 30), 'R2': (C(0.6, -17.5, 4.6), C(0.3, 1.5, 3.6), 28), 'R3': (C(0.6, -17.5, 4.6), C(0.3, 1.5, 3.6), 28)}
for k in ('C2a', 'C2', 'C3', 'C4', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12a', 'C12'): VIEWS[k] = CC
PUSH = {'C6a': 0.0, 'C6': 0.06}
SH = [(a, b, k) for a, b, k in CP.SHOTS if k in VIEWS]
for n_, (t0, t1, k) in enumerate(SH):
    L, T, lens = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 600; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler(); d1 = PUSH.get(k, 0.03)
    for t, dd in ((t0, 0.0), (t1, d1)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    interp(cam, 'LINEAR')
    m = sc.timeline_markers.new('c4c %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples, exposure=-0.9)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=A.save)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'c4_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    cam_at(F0); sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'c4_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.CRATE_RANGES, late=CP.U.LATE, crates=CP.T_CRATES, cloth=CP.T_CLOTH, reveal=CP.T_REVEAL, stain=CP.T_STAIN, stands=CP.T_STANDS,
               glow2=CP.T_GLOW2, fix=CP.T_FIX, dial=CP.T_DIAL, links=CP.T_LINKS,
               events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_happy', 'beep_yes', 'beep_surprise')], shots=SH),
          open(os.path.join(A.out, 'qrc4c_log_%d.json' % F0), 'w'), default=float, indent=0)
print('QRC4C DONE', F0, F1)
