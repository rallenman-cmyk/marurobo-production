# 2章 S16（卓上）：まるロボが小さな箱（3×3マス分）を頭に載せて運び、左上の目印の真ん中に置く → 読めない
#   blender -b --factory-startup -P ch2_table_sb.py -- KEY OUT.png [--screen SCREEN.png]
#   KEY：phonecam（スマホのカメラの絵）／K41（運ぶ）／K42（置いて離れる）／K43（肩越し：結果が出ない）
import sys, os, math
import bpy
from mathutils import Vector
OP = '/home/user/qr_plan/parts/opening'; sys.path.insert(0, OP)
import op_tilt as OT
import op_stage as OS
from kit import world as W
sys.path.insert(0, '/home/user/qr_plan/parts/pc_qr'); import op_stage_standin as SI
from op_timeline import *
a = sys.argv[sys.argv.index('--') + 1:]; KEY, OUT = a[0], a[1]; SCREEN = a[a.index('--screen') + 1] if '--screen' in a else None
def rc(r, c): return (-(N * MOD) / 2 + (c + 0.5) * MOD, (N * MOD) / 2 - (r + 0.5) * MOD)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
OS.build_set()
for nm in ('Arm base', 'Arm pole', 'Arm', 'Phone', 'Phone screen glass', 'Phone camera'):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
root, torso, legs = SI.build_robot()
def pose(p, heading, pitch=0.0):
    psi = math.radians(heading); rx, ry = math.cos(psi), math.sin(psi)
    feet = [dict(ankle=[p[0] + s * 0.255 * rx, p[1] + s * 0.255 * ry, 0.17], psi=psi) for s in (-1, 1)]
    SI.pose(root, torso, legs, dict(root=[p[0], p[1], -0.01], psi=psi, pitch=pitch, twist=0.0, feet=feet))
bm = W.mat('Small box', W.srgb('#C9CED4'), rough=0.6); S_ = 3 * MOD
box = W.box('Small box', (S_, S_, S_ * 0.8), bm, bevel=0.02); c3 = rc(3, 3)
if KEY == 'K41':
    p = (c3[0] + 0.15, c3[1] - 1.55); pose(p, 0.0); box.location = (p[0], p[1] - 0.02, 1.24 + S_ * 0.4)
else:
    box.location = (c3[0], c3[1], 0.004 + S_ * 0.4); pose((-2.25, 0.25), -70.0, pitch=8.0 if KEY == 'K42' else 0.0)
sc = bpy.context.scene
if KEY == 'phonecam':
    back, x, y = OT.phone_basis(); OT.cam(OT.LENS + back * 0.05, OT.AIM, 34, 'HORIZONTAL')
    W.render_setup(sc, engine='eevee', res=(560, 1160), samples=12)
else:
    OT.build_phone(SCREEN, False)
    v = {'K41': ((-4.6, -4.4, 2.6), (-0.9, 0.4, 0.7), 26), 'K42': ((-4.6, -4.4, 2.6), (-1.2, 0.5, 0.5), 26), 'K43': ((-0.95, -6.7, 4.45), (0.10, 0.05, 1.25), 30)}[KEY]
    OT.cam(*v); W.render_setup(sc, engine='eevee', res=(960, 540), samples=16)
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
