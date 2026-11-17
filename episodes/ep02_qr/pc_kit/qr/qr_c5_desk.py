# QRコード回・5章の机の場面（v14：前は 2D の平らな絵だった。「急にめちゃくちゃチープになってる、3D にしてよ」）。PC・Blender 4.3.2・EEVEE
#   blender -b --factory-startup --python qr_c5_desk.py -- --blend story.blend --out DIR --frames 777:1298 --video 1 --vprefix qrc5d_
#   確認用：--standin 1（仮のまるロボ）。--still 800,900 で指定のコマだけ PNG
#   冒頭と同じ机と QR の紙。① インク：まるロボがびんにぶつかって倒す → 12 か所にしずく（上から見る）
#   ② ロゴ：まるロボが顔のロゴのカードを持って来て、真ん中に置く → 得意げ → しずくが 1 つ、ロゴの横に落ちる（赤い輪）
import sys, os, math, json, argparse, random
import bpy
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import op_timeline as OPT
import c5_plan as CP
from c5_plan import FPS, s, e, fr_of, mxy
ap = argparse.ArgumentParser()
R0 = CP.DESK_RANGES
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc5d'); ap.add_argument('--frames', default='%d:%d' % (fr_of(R0[0][0]), fr_of(R0[-1][1])))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc5d_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--still', default='')
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
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)

# ================================================================ 舞台：冒頭と同じ（机・QR の紙・光 A 案）
W.sky_and_sun(sc, az_deg=135.0, el_deg=50.0, sky_strength=0.35, sun_energy=4.0)
desk = W.box('Desk', (16, 12, 0.3), W.mat('Desk wood', W.srgb('#B98A5E'), rough=0.55), bevel=0.03); desk.location = (0, 0, -0.15)
pm = bpy.data.materials.new('QR paper'); pm.use_nodes = True; nt = pm.node_tree; bs = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.join(HERE, 'qr_paper.png')); tex.interpolation = 'Closest'
nt.links.new(tex.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
side = (OPT.N + 2 * OPT.QZ) * OPT.MOD
bpy.ops.mesh.primitive_plane_add(size=side, location=(0, 0, 0.004)); paper = bpy.context.object; paper.name = 'QR paper'; paper.data.materials.append(pm)
ink_m = W.mat('ink', W.srgb('#0E1430'), rough=0.12, coat=0.7)
ZP = 0.006                                                    # 紙の上（しずく・カードは紙より少し上に置く。同じ高さで重ならない）

# ================================================================ ① インクのびん：倒れて、しずくが 12 か所に飛ぶ
glass = W.mat('bottle glass', W.srgb('#22325E'), rough=0.08, coat=0.8)
piv = W.link(O.new('bottle pivot', None)); piv.location = (CP.BOTTLE[0] - 0.17, CP.BOTTLE[1], 0.0)      # 倒れる側（紙の側＝左）の底の縁
body = W.cyl('bottle', 0.17, 0.40, glass, seg=32); body.parent = piv; body.location = (0.17, 0, 0.20)
neck = W.cyl('bottle neck', 0.08, 0.10, glass, seg=24); neck.parent = piv; neck.location = (0.17, 0, 0.45)
cap = W.cyl('bottle cap', 0.09, 0.07, W.mat('cap', W.srgb('#2B2B2E'), rough=0.4), seg=24); cap.parent = piv; cap.location = (0.17, 0, 0.535)
lab = W.cyl('bottle label', 0.172, 0.16, W.mat('label', W.srgb('#E8E2D2'), rough=0.6), seg=32); lab.parent = piv; lab.location = (0.17, 0, 0.18)
for ob in (body, neck, lab): show(ob, [(0.0, s('31-01', -1.0))])                  # びんもロゴの場面では出さない
for t, ang in ((0.0, 0.0), (CP.T_TIP, 0.0), (CP.T_TIP + 0.32, 84.0), (CP.T_TIP + 0.42, 80.0), (CP.T_TIP + 0.5, 82.0)):
    piv.rotation_euler = (0, math.radians(-ang), 0); piv.keyframe_insert('rotation_euler', index=1, frame=fr_of(t))
cap.parent = None; cap.location = (CP.BOTTLE[0], CP.BOTTLE[1], 0.535)
mouth0 = Vector((CP.BOTTLE[0] - 0.17 - 0.50, CP.BOTTLE[1], 0.16))   # 倒れたあとの口の位置
for t, loc in ((CP.T_TIP + 0.28, (CP.BOTTLE[0], CP.BOTTLE[1], 0.535)), (CP.T_TIP + 0.32, (mouth0.x - 0.05, mouth0.y, 0.12)), (CP.T_TIP + 0.9, (mouth0.x - 0.35, mouth0.y - 0.45, 0.045))):
    cap.location = loc; cap.keyframe_insert('location', frame=fr_of(t))
for t, r in ((CP.T_TIP + 0.32, 0.0), (CP.T_TIP + 0.9, 260.0)): cap.rotation_euler = (math.radians(r), math.radians(90), 0); cap.keyframe_insert('rotation_euler', frame=fr_of(t))
show(cap, [(0.0, s('31-01', -1.0))])
def splat(name, x, y, r, seed, t_land, grow=0.12):
    """紙の上のしみ（少し形のくずれた円）。t_land で広がる"""
    rnd = random.Random(seed); root = W.link(O.new(name, None)); root.location = (x, y, ZP)
    for k in range(4):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.0, depth=1.0); o = bpy.context.object; o.name = '%s %d' % (name, k); o.data.materials.append(ink_m); o.parent = root
        dx = rnd.uniform(-0.35, 0.35) * r if k else 0; dy = rnd.uniform(-0.35, 0.35) * r if k else 0; s_ = rnd.uniform(0.45, 0.7) if k else 1.0
        o.location = (dx, dy, 0.002); o.scale = (r * s_, r * s_ * rnd.uniform(0.85, 1.0), 0.004)
    for t, s_ in ((t_land, 0.05), (t_land + grow, 1.0)): root.scale = (s_, s_, 1); root.keyframe_insert('scale', frame=fr_of(t))
    t_end = 9e3 if t_land > s('31-01', -1.0) else s('31-01', -1.0)           # インクの場面のしみは、ロゴの場面では消す（別の紙）
    for ob in hier(root):
        if ob.type == 'MESH': show(ob, [(t_land, t_end)])
    return root
def fly(name, p0, p1, t0, T, h):
    """しずく：p0 から p1 へ放物線（高さ h）。着いたら消える"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, segments=16, ring_count=8); d = bpy.context.object; d.name = name; d.data.materials.append(ink_m)
    for f in range(fr_of(t0), fr_of(t0 + T) + 1):
        u = min(1.0, ((f - 1) / FPS - t0) / T); p = p0.lerp(p1, u); p.z += 4 * h * u * (1 - u)
        d.location = p; d.keyframe_insert('location', frame=f)
    show(d, [(t0, t0 + T)])
for k, (r, c) in enumerate(CP.INK_DROPS):
    x, y = mxy(r, c); t0 = CP.T_TIP + 0.30 + 0.035 * k; T = 0.32 + 0.06 * ((x - mouth0.x) ** 2 + (y - mouth0.y) ** 2) ** 0.5
    fly('ink drop %d' % k, mouth0.copy(), Vector((x, y, ZP)), t0, T, 0.35 + 0.05 * (k % 3))
    splat('ink splat %d' % k, x, y, 0.045, 100 + k, t0 + T)
splat('ink puddle', mouth0.x - 0.08, mouth0.y, 0.22, 7, CP.T_TIP + 0.35, grow=0.8)       # びんの口のそばの水たまり（紙の外）

# ================================================================ ② ロゴのカード（7×7 マス・顔のロゴ）：まるロボの頭の上 → 真ん中へ置く
LG = 7 * OPT.MOD
lm = bpy.data.materials.new('logo'); lm.use_nodes = True; lnt = lm.node_tree; lbs = lnt.nodes['Principled BSDF']
ltx = lnt.nodes.new('ShaderNodeTexImage'); ltx.image = bpy.data.images.load(os.path.join(HERE, 'logo_robot.png')); ltx.interpolation = 'Linear'
lnt.links.new(ltx.outputs['Color'], lbs.inputs['Base Color']); lbs.inputs['Roughness'].default_value = 0.5
bpy.ops.mesh.primitive_plane_add(size=LG); card = bpy.context.object; card.name = 'logo card'; card.data.materials.append(lm)
cth = W.box('logo card back', (LG, LG, 0.012), W.mat('card edge', W.srgb('#F2F2F0'), rough=0.6)); cth.parent = card; cth.location = (0, 0, -0.007)
plan, FR = CP.desk_frames()
def frame_at(t): return FR[min(len(FR) - 1, max(0, int(round(t * FPS))))]
def head_top(t):
    f = frame_at(t); psi = f['psi']; c = Vector(f['root']) + Vector((0, 0, mm.TORSO_Z))
    return c + Vector((0, 0, 0.62)), psi
cx, cy = mxy(10, 10); T_P = CP.T_LOGO_PLACE
for f in range(fr_of(s('31-01', -0.6)), fr_of(T_P + 0.7) + 1):
    t = (f - 1) / FPS
    if t < T_P:                                              # 頭の上に平らにのせて運ぶ（上からのカメラで顔が見える）
        p, psi = head_top(t); card.location = p; card.rotation_euler = (0, 0, psi)
    else:                                                    # 真ん中へ、弧を描いて置く
        u = ease((t - T_P) / 0.7); p0, psi = head_top(T_P); p1 = Vector((cx, cy, ZP + 0.013))
        p = p0.lerp(p1, u); p.z += 0.6 * 4 * u * (1 - u); card.location = p; card.rotation_euler = (0, 0, psi * (1 - u))
    card.keyframe_insert('location', frame=f); card.keyframe_insert('rotation_euler', frame=f)
show(card, [(s('31-01', -1.0), 9e3)]); show(cth, [(s('31-01', -1.0), 9e3)])      # 裏の板も（子は親の hide_render を引き継がない）
# しずくが 1 つ、ロゴの横に落ちる（上から垂れて）→ 赤い輪（壊れた 9 個目）
x2, y2 = mxy(*CP.LOGO_DROP); td = CP.T_LOGO_DROP
fly('logo drop', Vector((x2, y2, 2.6)), Vector((x2, y2, ZP)), td - 0.55, 0.55, 0.0)
splat('logo splat', x2, y2, 0.05, 55, td)
ring = W.torus('logo ring', 0.20, 0.018, W.mat_emit('ring red', W.srgb('#E23B3B'), 4.0), seg=48); ring.location = (x2, y2, ZP + 0.02); ring.visible_shadow = False
for t, s_ in ((td + 0.15, 0.3), (td + 0.45, 1.0)): ring.scale = (s_, s_, 1); ring.keyframe_insert('scale', frame=fr_of(t))
show(ring, [(td + 0.15, td + 3.5)])

# ================================================================ まるロボ（机の上。2 つの場面の間は置き直し＝カットの外）
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

# ================================================================ カメラ（D5a：まるロボ・びん・紙／D5b・L5b〜d：真上から紙／L5a：まるロボ・紙を左前から）
C = lambda *v: Vector(v)
VIEWS = {'D5a': (C(4.3, -3.9, 2.5), C(1.0, 0.2, 0.35), 28), 'D5b': (C(0.0, -0.45, 5.6), C(0.0, 0.0, 0.0), 30),
         'L5a': (C(-4.4, -3.6, 2.6), C(-0.9, 0.1, 0.40), 28), 'L5b': (C(0.0, -0.45, 5.6), C(0.0, 0.0, 0.0), 30),
         'L5c': (C(0.0, -0.45, 5.6), C(0.0, 0.0, 0.0), 30), 'L5d': (C(0.0, -0.45, 5.6), C(0.0, 0.0, 0.0), 30)}
PUSH = {'D5a': 0.04, 'D5b': 0.05, 'L5a': 0.04, 'L5b': 0.03, 'L5c': 0.04, 'L5d': 0.03}
for n_, (t0, t1, k) in enumerate(CP.DESK_SHOTS):
    L, T, lens = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 300; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler()
    for t, dd in ((t0, 0.0), (t1, PUSH[k])): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    interp(cam, 'LINEAR')
    m = sc.timeline_markers.new('c5d %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'd5_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    cam_at(F0); sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'd5_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.DESK_RANGES, tip=CP.T_TIP, place=CP.T_LOGO_PLACE, drop=CP.T_LOGO_DROP,
               events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_surprise')], shots=CP.DESK_SHOTS),
          open(os.path.join(A.out, 'qrc5d_log_%d.json' % F0), 'w'), default=float, indent=0)
print('QRC5D DONE', F0, F1)
