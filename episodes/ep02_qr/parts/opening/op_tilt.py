# 案：スマホを斜めに構える（裏のカメラがQRを向き、画面はこちら＝見ている人のほうを向く）
#   1回目：スマホのカメラから見た絵を描く → 2回目：それを画面に貼って舞台を描く
#   blender -b -P op_tilt.py -- t秒 カメラ名 出力.png [--lines]
import sys, os, math, subprocess
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import op_stage as OS
from kit import world as W
from op_timeline import *
LENS = Vector(LENS); AIM = Vector(AIM)                                    # スマホのカメラの位置と向く先（op_timeline）
PW, PH, PT = PHONE_SIZE

def phone_basis():
    back = (AIM - LENS).normalized()                     # 裏（カメラ）の向き
    up = Vector((0, 0, 1)); x = up.cross(-back).normalized() if False else back.cross(up).normalized()
    y = (-back).cross(x).normalized()                    # 画面の上の向き
    return back, x, y

def build_phone(screen_img=None, lines=False):
    back, x, y = phone_basis()
    rot = Matrix_from(x, y, -back)
    body = W.box('Phone T', (PW, PH, PT), W.mat('Phone body T', W.srgb('#1E2228'), rough=0.3, metal=0.2), bevel=0.08, seg=4)
    c = LENS - back * (PT / 2) - y * (PH / 2 - 0.35); body.matrix_world = rot_to_matrix(rot, c)
    sm = bpy.data.materials.new('Screen T'); sm.use_nodes = True; nt = sm.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0]); e.inputs['Strength'].default_value = 1.0
    if screen_img:
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(screen_img); nt.links.new(tx.outputs[0], e.inputs['Color'])
    bpy.ops.mesh.primitive_plane_add(size=1); s = bpy.context.object; s.scale = (PW - 0.12, PH - 0.12, 1); s.data.materials.append(sm)
    s.matrix_world = rot_to_matrix(rot, c - back * (PT / 2 + 0.005)) @ __import__('mathutils').Matrix.Diagonal((PW - 0.12, PH - 0.12, 1, 1))
    # スマホの台（机に立つ細い柱と挟む部分）
    metal = W.mat('Stand metal', W.srgb('#3A3F46'), rough=0.35, metal=0.8)
    foot = Vector((c.x, c.y - 0.9, 0)); base = W.cyl('Stand base', 0.45, 0.08, metal); base.location = (foot.x, foot.y, 0.04)
    d = (c + back * 0.2) - foot; pole = W.cyl('Stand pole', 0.06, d.length, metal); pole.location = foot + d / 2; pole.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    if lines:      # カメラが見ている範囲：レンズからQRの四隅へ、うすい線（最初の1回だけ見せる想定）
        lm = W.mat_emit('View line', W.srgb('#7FE3F0'), 3.0); hs = N * MOD / 2
        for cx, cy in ((-hs, hs), (hs, hs), (hs, -hs), (-hs, -hs)):
            dv = Vector((cx, cy, 0.01)) - LENS; ln = W.cyl('View line', 0.012, dv.length, lm, seg=8); ln.location = LENS + dv / 2; ln.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); ln.visible_shadow = False
    return body

def Matrix_from(x, y, z):
    from mathutils import Matrix
    return Matrix((x, y, z)).transposed()
def rot_to_matrix(rot, c):
    m = rot.to_4x4(); m.translation = c; return m

def scene(t, extra_cam=None):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    OS.build_set()
    for nm in ('Arm base', 'Arm pole', 'Arm', 'Phone', 'Phone screen glass', 'Phone camera'):
        if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    root, torso, legs = OS.build_robot(); OS.pose_robot(root, torso, legs, t)

def cam(loc, look, lens, fit='AUTO'):
    cd = bpy.data.cameras.new('Cam'); cd.lens = lens; cd.sensor_fit = fit; cm = W.link(bpy.data.objects.new('Cam', cd)); cm.location = loc
    cm.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); bpy.context.scene.camera = cm

if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]; t = float(a[0]); view = a[1]; out = a[2]; lines = '--lines' in a
    sc = bpy.context.scene
    if view == 'phonecam':
        scene(t); back, x, y = phone_basis(); cam(LENS + back * 0.05, AIM, 34, 'HORIZONTAL')
        W.render_setup(sc, engine='eevee', res=(560, 1160), samples=12); sc.render.filepath = out; bpy.ops.render.render(write_still=True); sys.exit(0)
    scene(t); build_phone(a[a.index('--screen') + 1] if '--screen' in a else None, lines)
    views = {'shoulder': ((-0.95, -6.7, 4.45), (0.10, 0.05, 1.25), 30),      # スマホの後ろ・少し左上から（画面とQRが一緒に見える）
             'wide': ((6.4, -4.6, 3.4), (0.2, -0.6, 1.0), 22),               # 右手前から：スマホ・QR・まるロボ
             'wide2': ((5.6, 2.6, 2.6), (0.6, -0.9, 0.8), 24),               # 右奥から：まるロボがスマホへ歩く
             'close': ((0.05, -2.15, 0.62), (0.78, -0.78, 0.55), 30),        # まるロボの前（スマホ側）から低く
             'med': ((-0.35, -2.55, 1.15), (0.55, -0.55, 0.9), 30),          # 踏み込んだまるロボを前から
             'low': ((-2.6, 2.9, 0.42), (0.6, -0.6, 0.25), 22),              # QRの面すれすれ（奥から手前のスマホへ）
             'face': ((3.4, -4.4, 1.0), (2.2, -0.4, 0.75), 36)}
    cam(*views[view]); W.render_setup(sc, engine='eevee', res=(960, 540), samples=16); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
