# 2章（見つける）の絵コンテ：中の世界（1章の終わりの色＝目印は赤・中身は青・予備は橙）＋仮のまるロボ
#   blender -b --factory-startup -P ch2_sb.py -- KEY OUT.png
import sys, os, math, json
import bpy
from mathutils import Vector, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import qr_world as QW
from kit import world as W
import op_stage_standin as SI
MOD = QW.MOD; N = 21; H = N * MOD / 2
KEY = sys.argv[sys.argv.index('--') + 1]; OUT = sys.argv[sys.argv.index('--') + 2]
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
def robot_at(xy, heading_deg, pitch=0.0, lift=0.0, roll=0.0):
    root, torso, legs = SI.build_robot(); psi = math.radians(heading_deg)
    rx, ry = math.cos(psi), math.sin(psi); z0 = QW.TILE_H + 0.04 + lift
    feet = [dict(ankle=[xy[0] + s * 0.255 * rx, xy[1] + s * 0.255 * ry, z0 + 0.17 + (0.0 if lift < 0.2 else 0.0)], psi=psi) for s in (-1, 1)]
    SI.pose(root, torso, legs, dict(root=[xy[0], xy[1], z0 - 0.01], psi=psi, pitch=pitch, twist=0.0, feet=feet))
    if roll: root.rotation_euler = Euler((0, math.radians(roll), psi), 'XYZ')
    return root
def heading_to(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))
def cam(loc, look, lens, roll=0.0):
    cd = bpy.data.cameras.new('C'); cd.lens = lens; cd.clip_end = 600; c = W.link(bpy.data.objects.new('C', cd)); c.location = loc
    q = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y')
    if roll: q = q @ Euler((0, 0, math.radians(roll))).to_quaternion()
    c.rotation_euler = q.to_euler(); bpy.context.scene.camera = c
def text3d(body, loc, size, col, rot=(0, 0, 0), emit=2.0, align='CENTER'):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = 'CENTER'; cu.font = bpy.data.fonts.load(FB)
    t = W.link(bpy.data.objects.new('t', cu)); t.location = loc; t.rotation_euler = rot; t.data.materials.append(W.mat_emit('t' + body, W.srgb(col), emit)); return t
def beam(p0, p1, col='#7FE3F0', r=0.07, strength=5.0):
    p0, p1 = Vector(p0), Vector(p1); dv = p1 - p0
    b = W.cyl('beam', r, dv.length, W.mat_emit('beam', W.srgb(col), strength), seg=12); b.location = p0 + dv / 2; b.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); b.visible_shadow = False; return b
def band(center, seg_len, z, facing_deg=0.0, labels=True, h=0.9):
    """白黒の帯（黒1・白1・黒3・白1・黒1 の長さ）。下に 1 1 3 1 1"""
    widths = [1, 1, 3, 1, 1]; total = sum(widths) * seg_len; x = -total / 2; objs = []
    psi = math.radians(facing_deg); ux = Vector((math.cos(psi), math.sin(psi), 0))
    for k, w in enumerate(widths):
        L = w * seg_len; col = (0.06, 0.07, 0.08) if k % 2 == 0 else (0.95, 0.95, 0.93)
        b = W.box('band', (L - 0.04, 0.08, h), W.mat('bm%d' % k, col, rough=0.6) if k % 2 == 0 else W.mat_emit('bw%d' % k, col, 1.4))
        c = Vector(center) + ux * (x + L / 2); c.z = z; b.location = c; b.rotation_euler = (0, 0, psi)
        if labels: text3d(str(w), Vector(center) + ux * (x + L / 2) + Vector((0, 0, -h / 2 - 0.75)) - Vector((0, 0, center[2] if len(center) > 2 else 0)) + Vector((0, 0, z)), 1.5, '#2CC6D0', rot=(math.radians(90), 0, psi), emit=4.0)
        x += L
    return objs
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; Wd = QW.build(); QW.lights_c(sc, Wd['coll']); A = Wd['assets']; S = Wd['symbol']
fin = QW.cells_of(Wd, 'finder'); tim = QW.cells_of(Wd, 'timing'); fmt = QW.cells_of(Wd, 'format')
QW.paint(Wd, fin, 'finder'); QW.paint(Wd, QW.cells_of(Wd, 'data'), 'data'); QW.paint(Wd, QW.cells_of(Wd, 'spare'), 'spare')
TL = rc(3, 3); TR = rc(3, 17); BL = rc(17, 3); BR = rc(17, 17)
if KEY == 'K19':     # 10-01「角にあるこの印」：まず全体を真上から（左上の目印に光る輪）→ ここから寄る
    rm = W.mat_emit('ring19', W.srgb('#7FE3F0'), 3.0); ring = W.torus('ring19', 6.2, 0.16, rm); ring.location = (TL[0], TL[1], QW.TILE_H + 0.2)
    robot_at(rc(3, -2.2), -90); cam((0, -0.01, 70), (0, 0, 0), 32)
elif KEY == 'K20':     # 10-01「角にあるこの印」：左上の目印に寄る。まるロボは目印の左の白いフチに立つ
    p = rc(3, -2.2); robot_at(p, -90); cam((TL[0] + 3.5, TL[1] - 14.0, 7.0), (TL[0] - 0.6, TL[1], 0.6), 30)
elif KEY in ('K21a', 'K21', 'K22'):   # 10-02〜10-04：目の光が通ったマスが、本来の黒白のまま地面から浮き上がり、そのまま帯になる（地面には抜けた跡）
    def lift(cells, z, xs=None, yc=None, labels=True):
        """cells のマスを本来の黒白で浮かせる。xs：並べる x（省くと元の位置の真上）"""
        objs = []
        for k, (r, c) in enumerate(cells):
            t_ = Wd['tiles'][(r, c)]; v = t_['v']; t_.hide_render = True
            x = xs[k] if xs else rc(r, c)[0]; y = yc if yc is not None else rc(r, c)[1]
            o = W.box('lift', (MOD - 0.02, MOD - 0.02, QW.TILE_H), LM[v], bevel=0.03)
            o.location = (x, y, z); o.rotation_euler = (math.radians(90), 0, 0); objs.append(o)     # 浮いたマスは起き上がって、こちらに面を向ける
        if labels:
            runs = []; k = 0
            while k < len(cells):
                j = k
                while j + 1 < len(cells) and Wd['tiles'][cells[j + 1]]['v'] == Wd['tiles'][cells[k]]['v']: j += 1
                runs.append((k, j)); k = j + 1
            for (k, j) in runs:
                x = ((xs[k] + xs[j]) / 2) if xs else (rc(*cells[k])[0] + rc(*cells[j])[0]) / 2
                text3d(str(j - k + 1), (x, (yc if yc is not None else rc(*cells[0])[1]) - 0.2, z - 1.45), 1.4, '#2CC6D0', rot=(math.radians(90), 0, 0), emit=4.0)
        return objs
    row = [(3, c) for c in range(7)]
    LM = {1: W.mat('lift black', (0.02, 0.025, 0.03), rough=0.6), 0: W.mat_emit('lift white', (0.95, 0.95, 0.93), 1.3)}
    if KEY == 'K21a':            # 浮き上がる途中（左から順に）
        p = rc(3, -2.2); robot_at(p, -90, pitch=-4); beam((p[0] + 0.5, p[1], QW.TILE_H + 0.78), (rc(3, 7.6)[0], p[1], QW.TILE_H + 0.78))
        for k, rcx in enumerate(row):
            t_ = Wd['tiles'][rcx]; v = t_['v']; t_.hide_render = True
            o = W.box('lift', (MOD - 0.02, MOD - 0.02, QW.TILE_H), LM[v], bevel=0.03); u = max(0.0, min(1.0, 1.0 - 0.16 * k))
            o.location = (rc(*rcx)[0], rc(*rcx)[1], QW.TILE_H / 2 + 4.2 * u); o.rotation_euler = (math.radians(90) * u, 0, 0)
        cam((TL[0] + 1.0, TL[1] - 15.5, 6.2), (TL[0] - 0.4, TL[1], 2.4), 30)
    elif KEY == 'K21':           # 帯になった（黒1・白1・黒3・白1・黒1）
        p = rc(3, -2.2); robot_at(p, -90, pitch=-6); lift(row, 4.2)
        cam((TL[0] + 1.0, TL[1] - 15.5, 6.2), (TL[0] - 0.4, TL[1], 2.6), 30)
    else:                        # 斜め：通ったマスが浮いて、1本目の帯の下に並ぶ（斜めは 1 マスが長い）
        p = rc(-2.2, -2.2); robot_at(p, -135, pitch=-4); lift(row, 5.6, labels=False)
        diag = [(k, k) for k in range(7)]; sp = MOD * 1.414
        lift(diag, 3.4, xs=[TL[0] + (k - 3) * sp for k in range(7)], yc=rc(3, 3)[1])
        cam((TL[0] + 1.0, TL[1] - 16.5, 6.8), (TL[0] - 0.4, TL[1], 3.2), 30)
elif KEY == 'K23':   # 10-04.5：縦・別の斜めでも、速く
    p = rc(-2.2, -2.2); robot_at(p, -135, pitch=-4)
    z = QW.TILE_H + 0.78
    for a, b in (((rc(3, -1)), rc(3, 7.6)), (rc(-1, 3), rc(7.6, 3)), (rc(-1, -1), rc(7.6, 7.6)), (rc(-1, 7), rc(7.6, -0.6))):
        beam((a[0], a[1], z), (b[0], b[1], z), strength=3.5, r=0.05)
    cam((TL[0] + 6.0, TL[1] - 12.0, 9.0), (TL[0], TL[1], 0.6), 30)
elif KEY == 'K24':   # 10-05：傾いていても、回っていても → 3つの目印がリズムで光る
    for (r0, c0) in ((3, 3), (3, 17), (17, 3)):
        rm = W.mat_emit('ring', W.srgb('#7FE3F0'), 3.0); ring = W.torus('ring', 6.4, 0.12, rm); ring.location = (rc(r0, c0)[0], rc(r0, c0)[1], QW.TILE_H + 0.15)
    robot_at(rc(10, 14), 200); cam((H * 1.2, -H * 1.6, 22), (0, 0, 0), 26, roll=-22)
elif KEY == 'K27':   # 12-01「おっとっと」：大地ごと回る（真上から。回る向きの矢印）
    robot_at(rc(10, 12), 30, roll=18, pitch=-10)
    am = W.mat_emit('arrow', W.srgb('#FFD640'), 2.5); arc = W.torus('arc', H * 1.35, 0.18, am, arc=math.radians(110)); arc.location = (0, 0, 0.6); arc.rotation_euler = (0, 0, math.radians(20))
    cam((0, -0.01, 70), (0, 0, 0), 32, roll=62)
elif KEY == 'K28':   # 12-01.5：3つの目印を線で結ぶと L 字。目印のない角（右下）
    lm = W.mat_emit('L', W.srgb('#FFD640'), 3.0)
    for a, b in ((TR, TL), (TL, BL)):
        beam((a[0], a[1], QW.TILE_H + 0.3), (b[0], b[1], QW.TILE_H + 0.3), col='#FFD640', r=0.22, strength=3.0)
    for k in range(4):     # 右下の角：点線の四角
        for j in range(6):
            t = j / 6.0; s = 3.5
            pts = [(BR[0] - s, BR[1] - s), (BR[0] + s, BR[1] - s), (BR[0] + s, BR[1] + s), (BR[0] - s, BR[1] + s)]
            a, b = pts[k], pts[(k + 1) % 4]; x0 = a[0] + (b[0] - a[0]) * t; y0 = a[1] + (b[1] - a[1]) * t; x1 = a[0] + (b[0] - a[0]) * (t + 0.09); y1 = a[1] + (b[1] - a[1]) * (t + 0.09)
            beam((x0, y0, QW.TILE_H + 0.3), (x1, y1, QW.TILE_H + 0.3), col='#FFD640', r=0.24, strength=3.0)
    text3d('？', (BR[0], BR[1], QW.TILE_H + 0.4), 5.0, '#FFD640', emit=4.0)
    robot_at(rc(12, 12), heading_to(rc(12, 12), TL)); cam((0, -0.01, 70), (0, 0, 0), 32)
elif KEY == 'K29':   # 12-02：目印の間の、黒白交互の列（緑）。まるロボが黒いマスを跳んで渡る
    QW.paint(Wd, tim, 'timing'); robot_at(rc(6, 10), -90, lift=0.9, pitch=6)
    cam((rc(6, 10)[0] + 1.0, rc(6, 10)[1] - 9.0, 3.4), (rc(6, 10)[0], rc(6, 10)[1] + 1.0, 0.6), 26)
elif KEY == 'K30':   # 12-03：マスの物差し。目盛りの数字
    QW.paint(Wd, tim, 'timing')
    for c_ in range(8, 13): text3d(str(c_ - 7), (rc(6, c_)[0], rc(6, c_)[1] + 1.6, QW.TILE_H + 0.3), 1.3, '#FFFFFF', emit=3.0)
    for r_ in range(8, 13): text3d(str(r_ - 7), (rc(r_, 6)[0] - 1.6, rc(r_, 6)[1], QW.TILE_H + 0.3), 1.3, '#FFFFFF', emit=3.0)
    robot_at(rc(6, 13.2), -90); cam((rc(9, 9)[0], rc(9, 9)[1] - 0.01, 26), (rc(9, 9)[0], rc(9, 9)[1], 0), 30)
elif KEY in ('K31', 'K31a', 'K32', 'K33'):   # 13：読み方の札（紫の細い帯 2 本）。同じ中身が2か所
    QW.paint(Wd, tim, 'timing'); QW.paint(Wd, fmt, 'format')
    def tag(body, rr):
        text3d(body, (rc(rr, 3.5)[0], rc(rr, 3.5)[1], QW.TILE_H + 0.35), 1.7, '#FFFFFF', rot=(math.radians(25), 0, 0), emit=3.5)
        pl = W.box('tagbg', (6.6, 2.2, 0.08), W.mat_emit('tagbg', W.srgb('#8C55B8'), 1.4)); pl.location = (rc(rr, 3.5)[0], rc(rr, 3.5)[1], QW.TILE_H + 0.22); pl.rotation_euler = (math.radians(25), 0, 0)
        beam((rc(rr, 3.5)[0] + 3.3, rc(rr, 3.5)[1], QW.TILE_H + 0.3), (rc(8, 7)[0], rc(8, 7)[1], QW.TILE_H + 0.3), col='#B88BE0', r=0.06, strength=2.0)
    if KEY in ('K32', 'K33'): tag('予備の量', 10.6)
    if KEY == 'K33': tag('柄の番号', 12.8)
    if KEY == 'K31':
        lm = W.mat_emit('link', W.srgb('#B88BE0'), 2.5); arc = W.torus('link', H * 0.55, 0.12, lm, arc=math.radians(180)); arc.location = (rc(8, 10)[0], rc(8, 10)[1], 0.6); arc.rotation_euler = (math.radians(90), 0, 0)
    robot_at(rc(10, 9), heading_to(rc(10, 9), rc(8, 4)))
    cam((rc(10, 6)[0] + 2.0, rc(10, 6)[1] - 14.0, 13.0), (rc(8, 6)[0], rc(8, 6)[1], 0), 28)
elif KEY in ('K38', 'K39', 'K40'):   # 14：柄を外す → 重ねる前 → 柄（縦じま）が降りてきて、白黒が入れ替わる → いまの QR
    bp = S['before_pattern']; fl = A['function_labels']
    for (r, c), t in Wd['tiles'].items():
        if fl[r][c] != 'data': continue
        if KEY == 'K38' or (KEY == 'K39' and r >= 11): t.color = QW.color_for(bp[r][c], None)
        else: t.color = QW.color_for(t['v'], None)
    QW.paint(Wd, fin, 'finder')
    if KEY == 'K39':
        sm = W.mat_emit('stripe', W.srgb('#7FE3F0'), 1.2)
        for c in range(0, N, 3):
            s_ = W.box('stripe', (MOD * 0.92, N * MOD * 0.5, 0.06), sm); s_.location = (rc(0, c)[0], rc(5, 0)[1], 2.4)
    robot_at(rc(10, -2.5), -90); cam((0, -0.01, 66), (0, 0, 0), 32)
elif KEY == 'K34':   # 15：白いフチを歩く。ここから先は QR ではない、の境目（光る線）と 4 マスの目盛り
    lm = '#14A3B4'
    for a, b in (((-H, -H)), ((H, -H))), (((H, -H)), ((H, H))), (((H, H)), ((-H, H))), (((-H, H)), ((-H, -H))):
        beam((a[0], a[1], QW.TILE_H + 0.05), (b[0], b[1], QW.TILE_H + 0.05), col='#FFFFFF', r=0.06, strength=2.5)
    for k in range(5):
        beam((H + k * MOD, -H - 1.2, QW.TILE_H + 0.05), (H + k * MOD, -H - 2.6, QW.TILE_H + 0.05), col=lm, r=0.08, strength=2.0)
    beam((H, -H - 1.9, QW.TILE_H + 0.05), (H + 4 * MOD, -H - 1.9, QW.TILE_H + 0.05), col=lm, r=0.08, strength=2.0)
    text3d('4マス', (H + 2 * MOD, -H - 3.8, QW.TILE_H + 0.1), 1.6, lm, emit=3.0)
    robot_at((H + 2.0 * MOD, -H + 6.0), 180)
    cam((H + 3.0 * MOD + 3.0, -H - 9.0, 3.6), (H + 1.0, -H + 3.0, 0.4), 24)
W.render_setup(sc, engine='eevee', res=(960, 540), samples=16); sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
