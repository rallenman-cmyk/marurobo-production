# 5章（どこまで隠したら読めなくなる？）の絵コンテ：大地を箱にして、壊れた箱を灰色に
#   blender -b --factory-startup -P c5_sb.py -- KEY OUT.png
#   W29 一歩踏み込んだ（10個）／W30 インクのしずく12か所（12個）／W31 真ん中のロゴ（8個）／W31b ロゴ＋しずく1つ（9個）／W28 乗ったとき（6個・比べる用）
import sys, os, math
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import op_stage_standin as SI, qr_world as QW, ch1_box as BX
KEY = sys.argv[sys.argv.index('--') + 1]; OUT = sys.argv[sys.argv.index('--') + 2]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; MOD = QW.MOD; H = 21 * MOD / 2
def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
def robot_at(xy, hd, pitch=0.0, z=0.0):
    root, torso, legs = SI.build_robot(); psi = math.radians(hd); rx, ry = math.cos(psi), math.sin(psi); z0 = z + 0.04
    feet = [dict(ankle=[xy[0] + s * 0.255 * rx, xy[1] + s * 0.255 * ry, z0 + 0.17], psi=psi) for s in (-1, 1)]
    SI.pose(root, torso, legs, dict(root=[xy[0], xy[1], z0 - 0.01], psi=psi, pitch=pitch, twist=0.0, feet=feet))
def blob(x, y, z, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); o = bpy.context.object
    o.location = (x, y, z); o.scale = (r, r * 0.9, 0.05); o.data.materials.append(W.mat('ink', (0.01, 0.012, 0.02), rough=0.3))
Wd = QW.build(); QW.lights_c(sc, Wd['coll']); A = Wd['assets']; S = Wd['symbol']; E = A['experiments']
QW.paint(Wd, QW.cells_of(Wd, 'finder'), 'finder')
exp = {'W29': 'robot_step', 'W30': 'ink12', 'W31': 'logo7', 'W31b': 'logo7_ink1', 'W28': 'robot_stand'}[KEY]
bad = E[exp]['bad_boxes']
for b in Wd['boxes']:
    role = 'data' if b in S['data_boxes'] else 'spare'
    BX.panels(Wd, b, BX.box_center(Wd, b), state=('broken' if b in bad else role), u=1.0, lid=True, name='Box %d' % b)
if KEY in ('W29', 'W28'):
    c = rc(*E[exp]['center_rc']); robot_at(c, 200, z=1.0)              # 箱の上に乗っている
    cam((c[0] + 8.0, c[1] - 14.0, 13.0), (c[0] - 3.0, c[1] + 2.0, 0.5), 24) if False else None
if KEY == 'W30':
    for (r, cc) in E['ink12']['drops']: x, y = rc(r, cc); blob(x, y, 1.05, 0.55)
    robot_at((H + 2.5, -H + 2.0), 120)
if KEY in ('W31', 'W31b'):
    c = rc(10, 10); lg = W.box('logo', (7 * MOD, 7 * MOD, 0.4), W.mat('logo', W.srgb('#F2F4F5'), rough=0.4, alpha=0.6), bevel=0.2); lg.location = (c[0], c[1], 1.3)
    ey = W.cyl('logo eye', 2.6, 0.1, W.mat_emit('logo lens', W.srgb('#3FC6C9'), 1.6)); ey.location = (c[0], c[1], 1.55)
    rg = W.torus('logo ring', 2.8, 0.25, W.mat('logo ring', W.srgb('#203236'), rough=0.3)); rg.location = (c[0], c[1], 1.55)
    robot_at((c[0] + 6.5, c[1] - 6.0), 40)
    if KEY == 'W31b': x, y = rc(*E['logo7_ink1']['drop']); blob(x, y, 1.05, 0.55)
cd = bpy.data.cameras.new('C'); cd.lens = 24; cm = W.link(bpy.data.objects.new('C', cd))
if KEY in ('W29', 'W28'):
    c = rc(*E[exp]['center_rc']); cm.location = (c[0] + 9.0, c[1] - 15.0, 14.0); look = (c[0] - 3.0, c[1] + 3.0, 0.5)
else:
    cm.location = (0.0, -H * 1.55, H * 1.25); look = (0.0, -1.0, 0.0)
cm.rotation_euler = (Vector(look) - cm.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = cm
W.render_setup(sc, engine='eevee', res=(960, 540), samples=16); sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
