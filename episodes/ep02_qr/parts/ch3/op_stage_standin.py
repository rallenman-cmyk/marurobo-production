# 確認用の仮のまるロボ（本物のモデルがないときだけ）。寸法は marumotion と同じ
import math, bpy
from mathutils import Vector, Euler
from kit import world as W
def build_robot():
    white = W.mat('Maru white', W.srgb('#F2F4F5'), rough=0.35, coat=0.3); teal = W.mat_emit('Maru lens', W.srgb('#3FC6C9'), 2.2)
    dark = W.mat('Maru lens ring', W.srgb('#203236'), rough=0.25); orange = W.mat_emit('Maru antenna', W.srgb('#FF9A3C'), 1.5); gray = W.mat('Maru leg', W.srgb('#C9CED3'), rough=0.4)
    root = W.empty('Maru root'); torso = W.empty('Maru torso'); torso.parent = root
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24); b = bpy.context.object; b.name = 'Maru body'
    b.scale = (0.51, 0.46, 0.49); b.data.materials.append(white); b.parent = torso
    for f in b.data.polygons: f.use_smooth = True
    ring = W.cyl('Maru ring', 0.27, 0.06, dark); ring.rotation_euler = (math.radians(90), 0, 0); ring.location = (0, 0.445, 0.025); ring.parent = torso
    lens = W.cyl('Maru eye', 0.223, 0.07, teal); lens.rotation_euler = (math.radians(90), 0, 0); lens.location = (0, 0.47, 0.025); lens.parent = torso
    rod = W.cyl('Maru antenna rod', 0.018, 0.55, gray); rod.location = (-0.33, -0.04, 0.62); rod.rotation_euler = (0, math.radians(-13), 0); rod.parent = torso
    ball = W.cyl('Maru antenna ball', 0.07, 0.14, orange, seg=24); ball.location = (-0.40, -0.04, 0.92); ball.parent = torso
    legs = [(W.cyl('Maru leg %d' % s, 0.06, 1.0, gray), W.box('Maru foot %d' % s, (0.22, 0.32, 0.07), white, bevel=0.03)) for s in (-1, 1)]
    return root, torso, legs
def pose(root, torso, legs, f, key=None):
    r = Vector(f['root']); root.location = r; root.rotation_euler = Euler((0, 0, f['psi']), 'XYZ')
    torso.location = (0, 0, 0.73); torso.rotation_euler = Euler((math.radians(-f['pitch']), 0, math.radians(f['twist'])), 'XYZ')
    bpy.context.view_layer.update()
    for sgn, (leg, foot), ft in zip((-1, 1), legs, f['feet']):
        hip = root.matrix_world @ Vector((sgn * 0.255, 0, 0.43)); ank = Vector(ft['ankle']); d = hip - ank
        leg.location = (hip + ank) / 2; leg.scale = (1, 1, d.length); leg.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        foot.location = ank + Vector((0, 0, -0.10)); foot.rotation_euler = (0, 0, ft['psi'])
    if key is not None:
        for ob in (root, torso): ob.keyframe_insert('location', frame=key); ob.keyframe_insert('rotation_euler', frame=key)
        for leg, foot in legs:
            for ob in (leg, foot):
                ob.keyframe_insert('location', frame=key); ob.keyframe_insert('rotation_euler', frame=key)
            leg.keyframe_insert('scale', frame=key)
