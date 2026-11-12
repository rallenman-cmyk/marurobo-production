# 4章（直す）の絵コンテ：工場のジオラマ（F）／数字の箱の空間（C・R）／QRの大地（W・B）＋仮のまるロボ
#   blender -b --factory-startup -P ch4_sb.py -- KEY OUT.png
import sys, os, math
import bpy
from mathutils import Vector, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import op_stage_standin as SI
KEY = sys.argv[sys.argv.index('--') + 1]; OUT = sys.argv[sys.argv.index('--') + 2]
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
QR_PNG = '/home/user/qr_plan/parts/opening/qr_paper.png'
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
def robot_at(xy, heading_deg, pitch=0.0, z=0.0, glow=False):
    root, torso, legs = SI.build_robot(); psi = math.radians(heading_deg)
    rx, ry = math.cos(psi), math.sin(psi); z0 = z + 0.04
    feet = [dict(ankle=[xy[0] + s * 0.255 * rx, xy[1] + s * 0.255 * ry, z0 + 0.17], psi=psi) for s in (-1, 1)]
    SI.pose(root, torso, legs, dict(root=[xy[0], xy[1], z0 - 0.01], psi=psi, pitch=pitch, twist=0.0, feet=feet))
    if glow:                                   # 分かった瞬間：アンテナの先が光る
        bpy.context.view_layer.update(); ball = bpy.data.objects['Maru antenna ball'] if 'Maru antenna ball' in bpy.data.objects else None
        if ball:
            g = W.link(bpy.data.objects.new('glow', None)); p = ball.matrix_world.translation
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=p); s_ = bpy.context.object; s_.data.materials.append(W.mat_emit('ant glow', W.srgb('#FFD640'), 12.0))
    return root
def heading_to(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))
def cam(loc, look, lens):
    cd = bpy.data.cameras.new('C'); cd.lens = lens; cd.clip_end = 600; c = W.link(bpy.data.objects.new('C', cd)); c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); sc.camera = c
def text3d(body, loc, size, col, rot=(math.radians(90), 0, 0), emit=2.5, align='CENTER'):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = 'CENTER'; cu.font = bpy.data.fonts.load(FB)
    t = W.link(bpy.data.objects.new('t', cu)); t.location = loc; t.rotation_euler = rot
    t.data.materials.append(W.mat_emit('t' + body + col, W.srgb(col), emit) if emit else W.mat('t' + body + col, W.srgb(col), rough=0.5)); return t
def beam(p0, p1, col='#7FE3F0', r=0.07, strength=5.0):
    p0, p1 = Vector(p0), Vector(p1); dv = p1 - p0
    b = W.cyl('beam', r, dv.length, W.mat_emit('beam' + col, W.srgb(col), strength), seg=12); b.location = p0 + dv / 2; b.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); b.visible_shadow = False; return b
def blob(center, rx, ry, rz=0.05, m=None, seed=0):
    """汚れ：つぶれた球をいくつか重ねる"""
    import random; rnd = random.Random(seed); m = m or W.mat('stain', (0.01, 0.012, 0.014), rough=0.15, coat=0.6); out = []
    for k in range(7):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); o = bpy.context.object
        dx = rnd.uniform(-0.45, 0.45) * rx if k else 0; dy = rnd.uniform(-0.45, 0.45) * ry if k else 0; s = rnd.uniform(0.45, 0.8) if k else 1.0
        o.location = (center[0] + dx, center[1] + dy, center[2]); o.scale = (rx * s, ry * s, rz); o.data.materials.append(m); out.append(o)
    return out
def studio(col='#E4EAF0'):
    wd = bpy.data.worlds.new('C space'); sc.world = wd; wd.use_nodes = True; bg = wd.node_tree.nodes['Background']; bg.inputs[0].default_value = (*W.srgb(col), 1); bg.inputs[1].default_value = 0.55
    fl = W.box('floor', (400, 400, 0.2), W.mat('floor', W.srgb('#F3F5F7'), rough=0.7)); fl.location = (0, 0, -0.1)
    la = bpy.data.lights.new('key', 'AREA'); la.shape = 'DISK'; la.size = 30; la.energy = 14000; k = W.link(bpy.data.objects.new('key', la)); k.location = (-4, -10, 22); k.rotation_euler = (math.radians(25), 0, math.radians(-10))
    ls = bpy.data.lights.new('sun', 'SUN'); ls.energy = 2.0; ls.angle = math.radians(4); s_ = W.link(bpy.data.objects.new('sun', ls)); s_.rotation_euler = (math.radians(40), 0, math.radians(-30))
# ---------------- 数字の箱の空間（C）：青い箱・橙のメモ・台
BLUE = '#3F86DD'; ORANGE = '#F0953A'; RED = '#D9475A'; TEAL = '#14A3B4'; INK = '#283038'
XS = [-5.4, -2.6, 0.2]
def crate(k, num, num_col='#FFFFFF', stain=False, cloth=False, q=False):
    x = XS[k]; b = W.box('crate%d' % k, (2.4, 2.0, 2.4), W.mat('crate', W.srgb(BLUE), rough=0.45), bevel=0.08); b.location = (x, 0, 1.2 + 0.35)
    if not cloth: text3d(num, (x, -1.02, 1.55), 1.9, num_col, emit=4.0)
    if stain: blob((x + 0.3, -1.02, 2.0), 0.55, 0.05, rz=0.4, seed=3)[0]; [setattr(o, 'scale', (o.scale[0], 0.04, o.scale[2] * 8)) for o in []]
    if cloth:
        c = W.box('cloth', (2.75, 2.35, 2.7), W.mat('cloth', W.srgb('#8A9097'), rough=0.9), bevel=0.35, seg=4); c.location = (x, 0, 1.35 + 0.35)
        text3d('？', (x, -1.2, 1.7), 1.8, '#FFFFFF', emit=2.0)
    if q: text3d('？', (x, -0.2, 3.5 + 0.35), 1.5, RED, emit=0)
def stand(k, label, glow=False):
    x = XS[k]; s = W.box('stand', (2.8, 2.3, 0.35), W.mat_emit('stand g', W.srgb('#FFD640'), 2.5) if glow else W.mat('stand', W.srgb('#C9D3DD'), rough=0.5), bevel=0.05); s.location = (x, 0, 0.175)
    pass   # ×1×2×3 の字は 2D で重ねる
def memo(row, title, val, val2=None, diff=None, x=4.9):
    z = 4.4 if row == 0 else 1.5
    p = W.box('memo', (4.6, 0.15, 2.3), W.mat('memo', W.srgb('#FBE3C8'), rough=0.6), bevel=0.06); p.location = (x, 0.6, z)
    fr = W.box('memo edge', (4.8, 0.12, 2.5), W.mat('memo edge', W.srgb(ORANGE), rough=0.6), bevel=0.06); fr.location = (x, 0.7, z)
    text3d(title, (x, 0.5, z + 0.68), 0.5, INK, emit=0)
    if val2 is None: text3d(val, (x, 0.5, z - 0.25), 1.1, INK, emit=0)
    else:
        text3d(val, (x - 1.25, 0.5, z - 0.25), 1.0, INK, emit=0); text3d('→', (x, 0.5, z - 0.25), 0.8, '#8A9097', emit=0); text3d(val2, (x + 1.35, 0.5, z - 0.25), 1.0, RED, emit=0)
    if diff: text3d(diff, (x + 3.4, 0.5, z - 0.2), 1.2, RED, emit=0)
    if row == 0:
        for dx in (-1.8, 1.8):
            leg = W.cyl('memo leg', 0.06, 3.2, W.mat('leg', W.srgb('#B0B8C0'))); leg.location = (x + dx, 0.75, 1.6)
def ccam(): cam((1.6, -15.0, 4.2), (1.6, 0, 1.9), 30)
def C(key):
    studio()
    if key == 'C1':        # 22-02：数字1つ＝箱1つ
        crate(0, '2'); robot_at((XS[0] + 2.2, -2.2), heading_to((XS[0] + 2.2, -2.2), (XS[0], 0)))
        cam((-2.6, -10.5, 3.6), (-4.4, 0, 1.6), 30); return
    nums = {'C2a': '253', 'C12a': '273', 'C2': '253', 'C3': '253', 'C4': '253', 'C6a': '253', 'C6': '273', 'C7': '273', 'C8': '273', 'C9': '273', 'C10': '273', 'C11': '273', 'C12': '253'}[key]
    for k in range(3):
        crate(k, nums[k], num_col=('#7FE3F0' if key == 'C12' and k == 1 else '#FFFFFF'), stain=(key == 'C6' and k == 1), cloth=(key in ('C3', 'C4') and k == 1), q=(key in ('C8',)))
    if False: memo(0, '合計', '10', val2=('12' if key in ('C8', 'C9', 'C10', 'C11', 'C12', 'C12a') else None), diff=('+2' if key in ('C8', 'C9', 'C10', 'C11', 'C12', 'C12a') else None))
    if key in ('C9', 'C10', 'C11', 'C12', 'C12a'):
        if False: memo(1, '1倍＋2倍＋3倍の合計', '21', val2=('25' if key in ('C10', 'C11', 'C12', 'C12a') else None), diff=('+4' if key in ('C10', 'C11', 'C12', 'C12a') else None))
        for k in range(3): stand(k, '×%d' % (k + 1), glow=(key in ('C12', 'C12a') and k == 1))
    if key == 'C4':
        pass
    if key == 'C6a':       # 黒い汚れが落ちてくる
        for o in blob((XS[1] + 0.3, -0.6, 4.2), 0.35, 0.35, rz=0.3, seed=5): pass
    pos = {'C2a': (XS[2] + 1.35, -2.3), 'C12a': (XS[1] + 0.5, -2.4), 'C2': (XS[2] + 1.35, -2.3), 'C3': (XS[2] + 1.35, -2.3), 'C4': (XS[2] + 1.35, -2.3), 'C6a': (XS[2] + 1.35, -2.3), 'C6': (XS[2] + 1.35, -2.3), 'C7': (XS[1] + 1.4, -2.9),
           'C8': (XS[2] + 1.35, -2.3), 'C9': (XS[2] + 1.35, -2.3), 'C10': (XS[2] + 1.35, -2.3), 'C11': (XS[2] + 1.35, -2.3), 'C12': (XS[1], -2.3)}[key]
    look = {'C2a': (XS[1], 0), 'C12a': (XS[1], 0), 'C2': (XS[1], 0), 'C3': (XS[1], 0), 'C4': (XS[1], 0), 'C6a': (XS[1], 0), 'C6': (XS[1], 0), 'C7': (XS[0], 0), 'C8': (4.9, 0), 'C9': (4.9, 0), 'C10': (4.9, 0), 'C11': (4.9, 0), 'C12': (XS[1], 0)}[key]
    robot_at(pos, heading_to(pos, look), glow=(key in ('C4', 'C12', 'C12a')))
    if key == 'C7': text3d('？', (pos[0], pos[1], 2.3), 0.7, RED, emit=3.0)
    ccam()   # v2.1：メモ・式・×1×2×3 は 2D で右半分に大きく重ねる。箱は左半分に大きく
# ---------------- 本物の仕組み（R）：0〜255 の輪・たくさんの予備・名前
def R(key):
    studio('#DCE3EC')
    if key == 'R1':
        b = W.box('crate', (2.4, 2.0, 2.4), W.mat('crate', W.srgb(BLUE), rough=0.45), bevel=0.08); b.location = (0, 0, 1.55); text3d('46', (0, -1.02, 1.55), 1.4, '#FFFFFF', emit=1.6)
        rm = W.mat_emit('ring', W.srgb(TEAL), 2.0); ring = W.torus('ring', 3.4, 0.09, rm, seg=96); ring.location = (0, 0.1, 1.9); ring.rotation_euler = (math.radians(90), 0, 0)
        for k in range(32):
            a = math.pi / 2 - 2 * math.pi * k / 32; L = 0.45 if k % 8 == 0 else 0.22
            p0 = Vector((math.cos(a) * 3.4, 0.0, 1.9 + math.sin(a) * 3.4)); p1 = Vector((math.cos(a) * (3.4 + L), 0.0, 1.9 + math.sin(a) * (3.4 + L)))
            beam(p0, p1, col=TEAL, r=0.035, strength=2.5)
        for lab, k in (('0', 0), ('64', 8), ('128', 16), ('192', 24)):
            a = math.pi / 2 - 2 * math.pi * k / 32; text3d(lab, (math.cos(a) * 4.5, -0.1, 1.9 + math.sin(a) * 4.5), 0.75, INK, emit=0)
        text3d('255', (-1.1, -0.1, 1.9 + 4.3), 0.55, INK, emit=0)
        robot_at((3.4, -2.6), heading_to((3.4, -2.6), (0, 0))); cam((1.0, -15.0, 3.8), (0.6, 0, 2.4), 30); return
    xs = [-6.4, -3.2, 0.0, 3.2, 6.4]
    for k, x in enumerate(xs):
        b = W.box('c', (1.9, 1.6, 1.9), W.mat('crate', W.srgb(BLUE if k != 2 else '#8A9097'), rough=0.45), bevel=0.07); b.location = (x, 0, 0.95)
    for j in range(6):
        x = -7.5 + j * 3.0; p = W.box('m', (2.2, 0.12, 1.3), W.mat('memo', W.srgb('#FBE3C8'), rough=0.6), bevel=0.05); p.location = (x, 4.5, 4.8)
        fr = W.box('me', (2.35, 0.1, 1.45), W.mat('memo edge', W.srgb(ORANGE), rough=0.6), bevel=0.05); fr.location = (x, 4.6, 4.8)
        for k, xc in enumerate(xs):
            if (j + k) % 2 == 0: beam((x, 4.4, 4.2), (xc, -0.1, 1.95), col='#FFB060', r=0.03, strength=2.5)
    if key == 'R3':
        pl = W.box('name', (8.4, 0.15, 1.5), W.mat('name', W.srgb('#FFFFFF'), rough=0.4), bevel=0.08); pl.location = (0.0, 4.2, 7.0)
        text3d('リード・ソロモン符号', (0.0, 4.08, 7.0), 0.95, INK, emit=0)
    robot_at((0.0, -2.6), 180 - 180, pitch=-12); cam((0.6, -17.5, 4.6), (0.3, 1.5, 3.6), 28)
# ---------------- 工場（F）：作業台・部品箱・伝票（QR）・油の汚れ
def F(key):
    studio('#C9CDD2')
    fl = W.box('shop floor', (60, 60, 0.2), W.mat('concrete', W.srgb('#9AA0A6'), rough=0.9)); fl.location = (0, 0, -0.05)
    top = W.box('bench', (5.6, 2.6, 0.18), W.mat('wood', W.srgb('#B98A5A'), rough=0.6), bevel=0.03); top.location = (0, 0, 2.0)
    for dx in (-2.6, 2.6):
        for dy in (-1.1, 1.1):
            lg = W.box('leg', (0.14, 0.14, 2.0), W.mat('steel', W.srgb('#59616A'), metal=0.6, rough=0.4)); lg.location = (dx, dy, 1.0)
    img = bpy.data.images.load(QR_PNG)
    def slip(x, y, rz, stain=False, s=0.75):
        m = bpy.data.materials.new('slip'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']; tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img
        nt.links.new(tx.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
        bpy.ops.mesh.primitive_plane_add(size=s, location=(x, y, 2.1)); o = bpy.context.object; o.rotation_euler = (0, 0, rz); o.data.materials.append(m)
        pa = W.box('paper', (s * 1.25, s * 1.6, 0.01), W.mat('paper', W.srgb('#F4F2EC'), rough=0.8)); pa.location = (x, y + s * 0.18, 2.095); pa.rotation_euler = (0, 0, rz)
        if stain: blob((x + 0.12, y - 0.05, 2.11), 0.22, 0.17, rz=0.012, seed=7); blob((x - 0.2, y + 0.15, 2.11), 0.1, 0.08, rz=0.012, seed=9)
        return o
    for k, (x, col) in enumerate(((-1.9, '#3F86DD'), (-0.6, '#3E9E62'), (0.7, '#F0953A'))):
        bx = W.box('bin', (1.0, 0.8, 0.5), W.mat('bin%d' % k, W.srgb(col), rough=0.5), bevel=0.04); bx.location = (x, 0.75, 2.34)
        for j in range(4):
            pt = W.cyl('part', 0.08, 0.25, W.mat('metal', W.srgb('#C0C6CC'), metal=0.8, rough=0.3)); pt.location = (x - 0.25 + j * 0.17, 0.75, 2.62)
    slip(-1.6, -0.55, 0.12); slip(-0.3, -0.6, -0.08, stain=(key in ('F1', 'F2')))
    can = W.cyl('oil can', 0.2, 0.5, W.mat('can', W.srgb('#C23B32'), metal=0.4, rough=0.4)); can.location = (1.9, -0.3, 2.34)
    blob((1.5, -0.55, 2.1), 0.25, 0.18, rz=0.01, seed=11)
    robot_at((1.7, 0.6), heading_to((1.7, 0.6), (-0.3, -0.6)), pitch=10, z=2.09)
    sign = W.box('sign', (1.6, 0.08, 0.7), W.mat('sign', W.srgb('#FFFFFF'), rough=0.5)); sign.location = (-2.0, 1.6, 3.4)
    text3d('1994', (-2.0, 1.55, 3.4), 0.42, INK, emit=0)
    if key == 'F2': cam((0.2, -2.8, 3.6), (-0.3, -0.5, 2.1), 34)
    else: cam((3.2, -6.8, 4.4), (0.0, 0.2, 2.3), 30)
# ---------------- QRの大地（W・B）
def B(key):
    import qr_world as QW, ch1_box as BX
    MOD = QW.MOD; H = 21 * MOD / 2
    def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
    Wd = QW.build(); QW.lights_c(sc, Wd['coll']); A = Wd['assets']; S = Wd['symbol']
    QW.paint(Wd, QW.cells_of(Wd, 'finder'), 'finder')
    def wrobot(xy, hd, pitch=0.0): return robot_at(xy, hd, pitch=pitch, z=QW.TILE_H)
    if key == 'W23':     # 23-02：白いマスに黒い汚れ → 黒に見える
        r0, c0 = 14, 6
        cands = [(r, c) for r in range(9, 13) for c in range(9, 13) if Wd['tiles'][(r, c)]['v'] == 0]
        r0, c0 = cands[0]; x, y = rc(r0, c0)
        blob((x, y, QW.TILE_H + 0.02), MOD * 0.52, MOD * 0.5, rz=0.03, seed=2)
        p = (x + 3.2, y - 1.2); wrobot(p, heading_to(p, (x, y)), pitch=14); cam((x + 2.6, y - 6.4, 3.6), (x + 0.6, y + 0.3, 0.3), 30); return
    bad = A['experiments']['robot_stand']['bad_boxes']
    if key == 'W26':     # 26-02：体で隠れたマスも、汚れたマスも、どちらも「すり替わったマス」
        QW.paint(Wd, QW.cells_of(Wd, 'data'), 'data'); QW.paint(Wd, QW.cells_of(Wd, 'spare'), 'spare')
        cov = A['experiments']['robot_stand']['covered']; ctr = rc(*A['experiments']['robot_stand']['center_rc'])
        for (r, c) in cov: t = Wd['tiles'][(r, c)]; t.color = QW.color_for(0, 'broken')
        wrobot(ctr, 200)
        sx, sy = rc(10, 10); blob((sx, sy, QW.TILE_H + 0.02), MOD * 1.2, MOD * 1.0, rz=0.03, seed=4, m=W.mat('stain matte', (0.01, 0.012, 0.014), rough=0.9))
        for (x, y) in ((ctr[0] + 2.4, ctr[1] + 4.6), (sx, sy + 2.6)): text3d('？', (x, y, 3.0), 5.5, '#D9475A', rot=(math.radians(55), 0, 0), emit=4.0)
        cam((H * 0.25, -H * 1.25, 27), (H * 0.2, -H * 0.12, 0), 26); return
    # B28：まるロボが乗った QR に戻る。箱にして、壊れた6個は灰色の抜け殻 → 光の線 → 半透明で組み上がる → HELLO
    ctr = rc(*A['experiments']['robot_stand']['center_rc'])
    for b in Wd['boxes']:
        role = 'data' if b in S['data_boxes'] else 'spare'; st = role
        if b in bad: st = {'B28a': 'broken', 'B28b': 'broken', 'B28c': 'restored', 'B28d': 'restored'}[key]
        BX.panels(Wd, b, BX.box_center(Wd, b), state=st, u=1.0, lid=True, name='Box %d' % b)
    if key in ('B28b',):
        for b in S['spare_boxes']:
            c0 = BX.box_center(Wd, b); tgt = BX.box_center(Wd, bad[b % len(bad)])
            beam((c0[0], c0[1], 1.2), (tgt[0], tgt[1], 1.2), col='#FFB060', r=0.05, strength=3.0)
    if key == 'B28d':
        text3d('HELLO', (ctr[0] - 6.0, ctr[1] + 6.0, 9.0), 4.0, '#7FB3FF', rot=(math.radians(70), 0, 0), emit=3.5)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.02, location=(ctr[0], ctr[1], 0.9)); sh = bpy.context.object; sh.scale = (7.8 * 0.75, 7.1 * 0.75, 1)
    shm = W.mat('shadow', (0.0, 0.0, 0.0), rough=1.0); shm.blend_method = 'BLEND' if hasattr(shm, 'blend_method') else None
    bs = shm.node_tree.nodes['Principled BSDF']; bs.inputs['Alpha'].default_value = 0.25; sh.data.materials.append(shm)
    try: shm.surface_render_method = 'DITHERED'
    except Exception: pass
    if key in ('B28a', 'B28b', 'B28c'): wrobot((ctr[0] - 7.5, ctr[1] + 5.0), heading_to((ctr[0] - 7.5, ctr[1] + 5.0), ctr), pitch=(-10 if key != 'B28a' else 0))
    else: wrobot((ctr[0] - 7.5, ctr[1] + 5.0), 160, pitch=-20)
    cam((ctr[0] + 9.0, ctr[1] - 15.0, 10.0), (ctr[0] - 4.0, ctr[1] + 3.0, 0.5), 24)
if KEY[0] == 'C': C(KEY)
elif KEY[0] == 'R': R(KEY)
elif KEY[0] == 'F': F(KEY)
else: B(KEY)
W.render_setup(sc, engine='eevee', res=(960, 540), samples=16, exposure=(-0.9 if KEY[0] in 'CRF' else 0.0)); sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
