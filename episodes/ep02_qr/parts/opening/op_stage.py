# 冒頭の舞台A（卓上）。確認用は仮のまるロボ。PC の本番では maru_opening.blend のまるロボに marurig で同じ予定を当てる
#   blender -b -P op_stage.py -- --still t秒 カメラ名 出力.png [--res 960x540]
import sys, os, json, math
import bpy
from mathutils import Vector, Euler, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
from op_timeline import *

FR = json.load(open(os.path.join(HERE, 'op_frames.json')))
def frame_at(t): return FR[min(len(FR) - 1, max(0, int(round(t * 24))))]

def build_set():
    sc = bpy.context.scene; coll = sc.collection
    W.sky_and_sun(sc, az_deg=135.0, el_deg=50.0, sky_strength=0.35, sun_energy=4.0)     # A案：左前から・高さ50°・5600K
    wood = W.mat('Desk wood', W.srgb('#B98A5E'), rough=0.55)
    desk = W.box('Desk', (16, 12, 0.3), wood, bevel=0.03); desk.location = (0, 0, -0.15)
    pm = bpy.data.materials.new('QR paper'); pm.use_nodes = True; nt = pm.node_tree; bs = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.join(HERE, 'qr_paper.png')); tex.interpolation = 'Closest'
    nt.links.new(tex.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
    side = (N + 2 * QZ) * MOD
    bpy.ops.mesh.primitive_plane_add(size=side, location=(0, 0, 0.004)); paper = bpy.context.object; paper.name = 'QR paper'; paper.data.materials.append(pm)
    # スマホを上に構えるアーム（机に立つ台→柱→腕→スマホの台）。スマホの画面は上向き、カメラは下向き
    metal = W.mat('Arm metal', W.srgb('#3A3F46'), rough=0.35, metal=0.8)
    base = W.cyl('Arm base', 0.6, 0.12, metal); base.location = (-3.2, 2.6, 0.06)
    pole = W.cyl('Arm pole', 0.08, PHONE_H + 0.4, metal); pole.location = (-3.2, 2.6, (PHONE_H + 0.4) / 2)
    arm = W.box('Arm', (4.3, 0.16, 0.16), metal); arm.location = (-1.1, 1.3, PHONE_H + 0.35); arm.rotation_euler = (0, 0, math.atan2(-1.3, 2.1) * 0 + math.radians(-31.8))
    body = W.mat('Phone body', W.srgb('#1E2228'), rough=0.3, metal=0.2)
    phone = W.box('Phone', (1.95, 4.0, 0.22), body, bevel=0.12, seg=4); phone.location = (0, 0, PHONE_H)
    scr = W.mat_emit('Phone screen', W.srgb('#0F1A24'), 1.2)
    s = W.box('Phone screen glass', (1.80, 3.82, 0.01), scr); s.location = (0, 0, PHONE_H + 0.115)
    lens = W.cyl('Phone camera', 0.13, 0.05, W.mat('Lens', W.srgb('#0A0C10'), rough=0.1)); lens.location = (0.55, 1.55, PHONE_H - 0.13)
    return dict(phone=phone)

def build_robot():
    white = W.mat('Maru white', W.srgb('#F2F4F5'), rough=0.35, coat=0.3)
    teal = W.mat_emit('Maru lens', W.srgb('#3FC6C9'), 2.2)
    dark = W.mat('Maru lens ring', W.srgb('#203236'), rough=0.25)
    orange = W.mat_emit('Maru antenna', W.srgb('#FF9A3C'), 1.5)
    gray = W.mat('Maru leg', W.srgb('#C9CED3'), rough=0.4)
    root = W.empty('Maru root'); torso = W.empty('Maru torso'); torso.parent = root
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24); b = bpy.context.object; b.name = 'Maru body'
    b.scale = (0.51, 0.46, 0.49); b.data.materials.append(white); b.parent = torso
    for f in b.data.polygons: f.use_smooth = True
    ring = W.cyl('Maru ring', 0.27, 0.06, dark); ring.rotation_euler = (math.radians(90), 0, 0); ring.location = (0, 0.445, 0.025); ring.parent = torso
    lensm = W.cyl('Maru eye', 0.223, 0.07, teal); lensm.rotation_euler = (math.radians(90), 0, 0); lensm.location = (0, 0.47, 0.025); lensm.parent = torso
    rod = W.cyl('Maru antenna rod', 0.018, 0.55, gray); rod.location = (-0.33, -0.04, 0.62); rod.rotation_euler = (0, math.radians(-13), 0); rod.parent = torso
    ball = W.cyl('Maru antenna ball', 0.07, 0.14, orange, seg=24); ball.location = (-0.40, -0.04, 0.92); ball.parent = torso
    legs = []
    for sgn in (-1, 1):
        leg = W.cyl('Maru leg %d' % sgn, 0.06, 1.0, gray); foot = W.box('Maru foot %d' % sgn, (0.22, 0.32, 0.07), white, bevel=0.03)
        legs.append((leg, foot))
    return root, torso, legs

def pose_robot(root, torso, legs, t):
    f = frame_at(t); r = Vector(f['root'])
    root.location = r; root.rotation_euler = Euler((0, 0, f['psi']), 'XYZ')
    torso.location = (0, 0, 0.73); torso.rotation_euler = Euler((math.radians(-f['pitch']), math.radians(f['roll']) * 0.0, math.radians(f['twist'])), 'XYZ')
    bpy.context.view_layer.update()
    for sgn, (leg, foot), ft in zip((-1, 1), legs, f['feet']):
        hip = root.matrix_world @ Vector((sgn * 0.255, 0, 0.43)); ank = Vector(ft['ankle'])
        mid = (hip + ank) / 2; d = hip - ank
        leg.location = mid; leg.scale = (1, 1, d.length); leg.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        foot.location = ank + Vector((0, 0, -0.10)); foot.rotation_euler = (0, 0, ft['psi'])

CAMS = {
    'wide':  ((5.4, -6.0, 3.3), (-0.2, 0.2, 1.6), 22),
    'med':   ((-1.94, 1.26, 1.5), (0.78, -0.78, 1.05), 30),
    'med2':  ((-2.25, 1.55, 1.5), (0.50, -0.50, 1.05), 30),
    'top':   ((0.0, 0.0, PHONE_H - 0.25), (0.0, 0.0, 0.0), 22),
    'close': ((-0.66, 0.30, 0.75), (0.78, -0.78, 0.55), 32),
    'low':   ((2.6, -2.9, 0.45), (-0.4, 0.4, 0.2), 22),
    'face':  ((3.2, -4.6, 1.0), (1.6, -1.7, 0.75), 38),
}

def camera(name):
    loc, look, lens = CAMS[name]; cd = bpy.data.cameras.new('Cam'); cd.lens = lens
    cam = W.link(bpy.data.objects.new('Cam', cd)); cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); bpy.context.scene.camera = cam

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    t = float(argv[argv.index('--still') + 1]); cam = argv[argv.index('--still') + 2]; out = argv[argv.index('--still') + 3]
    res = tuple(map(int, (argv[argv.index('--res') + 1] if '--res' in argv else '960x540').split('x')))
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    build_set(); root, torso, legs = build_robot(); pose_robot(root, torso, legs, t); camera(cam)
    sc = bpy.context.scene; W.render_setup(sc, engine='eevee', res=res, samples=16)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)
