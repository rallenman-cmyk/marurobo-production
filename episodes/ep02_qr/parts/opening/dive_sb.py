# 1章の入口：まるロボがスマホの画面に飛び込む（卓上）。D1 画面の前で構える / D2 飛び込む（画面に波紋）
import sys, os, math
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import op_tilt as OT
import op_stage as OS
from kit import world as W
sys.path.insert(0, '/home/user/qr_plan/parts/pc_qr'); import op_stage_standin as SI
KEY, OUT = sys.argv[sys.argv.index('--') + 1], sys.argv[sys.argv.index('--') + 2]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
OS.build_set()
for nm in ('Arm base', 'Arm pole', 'Arm', 'Phone', 'Phone screen glass', 'Phone camera'):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
OT.build_phone('/home/user/qr_plan/parts/opening/sb2/screens/scr_plain_hello.png', False)
back, px, py = OT.phone_basis(); scr_c = OT.LENS - back * (OT.PT / 2) - py * (OT.PH / 2 - 0.35) - back * OT.PT / 2
front = Vector((-back.x, -back.y, 0)).normalized()                    # 画面が向いている側（地面の上の向き）
heading = math.degrees(math.atan2(-(-front.x), -front.y))              # 画面の方を向く
root, torso, legs = SI.build_robot()
def pose(p, pitch=0.0, z=0.0):
    psi = math.radians(heading); rx, ry = math.cos(psi), math.sin(psi)
    feet = [dict(ankle=[p.x + s * 0.255 * rx, p.y + s * 0.255 * ry, z + 0.17], psi=psi) for s in (-1, 1)]
    SI.pose(root, torso, legs, dict(root=[p.x, p.y, z - 0.01], psi=psi, pitch=pitch, twist=0.0, feet=feet))
g = Vector((scr_c.x, scr_c.y, 0)) + front * 1.6
if KEY == 'D1':
    pose(g, pitch=8.0)
else:
    p = scr_c + front * 0.85 - Vector((0, 0, 0.95)); pose(p, pitch=-35.0, z=p.z)
    rm = W.mat_emit('Ripple', W.srgb('#7FE3F0'), 2.5)
    for k, r in enumerate((0.45, 0.8, 1.15)):
        t = W.torus('Ripple %d' % k, r, 0.025, rm); t.location = scr_c - back * 0.02
        t.rotation_euler = (-back).to_track_quat('Z', 'Y').to_euler()
c = g + front * 3.2 + Vector((2.6, 0, 1.6)) if False else None
cd = bpy.data.cameras.new('C'); cd.lens = 26; cam = W.link(bpy.data.objects.new('C', cd))
side = Vector((-front.y, front.x, 0))
cam.location = Vector((scr_c.x, scr_c.y, 0)) + front * 6.2 + side * 3.4 + Vector((0, 0, 2.4))
look = Vector((scr_c.x, scr_c.y, 1.5)) + front * 1.0
cam.rotation_euler = (look - cam.location).to_track_quat('-Z', 'Y').to_euler(); bpy.context.scene.camera = cam
W.render_setup(bpy.context.scene, engine='eevee', res=(960, 540), samples=16); bpy.context.scene.render.filepath = OUT; bpy.ops.render.render(write_still=True)
