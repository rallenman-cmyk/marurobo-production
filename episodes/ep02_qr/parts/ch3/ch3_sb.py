# 3章（読む）の絵コンテ：1章の終わりの大地（目印＝赤・中身＝青・予備＝橙のマス）＋仮のまるロボ
#   blender -b --factory-startup -P ch3_sb.py -- KEY OUT.png
#   G1 右下の角に立つ / G2 ジグザグの道（真上）/ G3a・G3 8マスがたたまれる / G4 頭に載せて運ぶ（2箱置いた）/ G5 9箱が一列
#   G6a 箱を開ける / G6 0と1が出る / G7 読む（上に図を重ねる背景）/ G8 見渡す / G9 予備の17個が光る
import sys, os, math
import bpy
from mathutils import Vector, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import qr_world as QW
from kit import world as W
import op_stage_standin as SI
import ch1_box as BX
MOD = QW.MOD; N = 21; H = N * MOD / 2
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
KEY = sys.argv[sys.argv.index('--') + 1]; OUT = sys.argv[sys.argv.index('--') + 2]
def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
def robot_at(xy, heading_deg, pitch=0.0, lift=0.0):
    root, torso, legs = SI.build_robot(); psi = math.radians(heading_deg)
    rx, ry = math.cos(psi), math.sin(psi); z0 = QW.TILE_H + 0.04 + lift
    feet = [dict(ankle=[xy[0] + s * 0.255 * rx, xy[1] + s * 0.255 * ry, z0 + 0.17], psi=psi) for s in (-1, 1)]
    SI.pose(root, torso, legs, dict(root=[xy[0], xy[1], z0 - 0.01], psi=psi, pitch=pitch, twist=0.0, feet=feet)); return root
def heading_to(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))
def cam(loc, look, lens):
    cd = bpy.data.cameras.new('C'); cd.lens = lens; cd.clip_end = 600; c = W.link(bpy.data.objects.new('C', cd)); c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); bpy.context.scene.camera = c
def text3d(body, loc, size, col, rot=(math.radians(90), 0, 0), emit=2.5):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.font = bpy.data.fonts.load(FB)
    t = W.link(bpy.data.objects.new('t', cu)); t.location = loc; t.rotation_euler = rot; t.data.materials.append(W.mat_emit('t' + body, W.srgb(col), emit)); return t
def beam(p0, p1, col='#7FE3F0', r=0.07, strength=5.0):
    p0, p1 = Vector(p0), Vector(p1); dv = p1 - p0
    b = W.cyl('beam', r, dv.length, W.mat_emit('beam' + col, W.srgb(col), strength), seg=12); b.location = p0 + dv / 2; b.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); b.visible_shadow = False; return b
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; Wd = QW.build(); QW.lights_c(sc, Wd['coll']); A = Wd['assets']; S = Wd['symbol']
QW.paint(Wd, QW.cells_of(Wd, 'finder'), 'finder'); QW.paint(Wd, QW.cells_of(Wd, 'data'), 'data'); QW.paint(Wd, QW.cells_of(Wd, 'spare'), 'spare')
ROW_X = H + 3.0                                           # 右の白いフチ（余白）に、読んだ順に箱を並べる
def row_pos(k): return (ROW_X, -H + 1.6 + k * 2.3)
def ghost(boxes):                                          # たたんで運んだあとのマスは、うっすら跡
    for b in boxes:
        for (r, c) in A['boxes'][str(b)]:
            t = Wd['tiles'][(r, c)]; t.color = (*QW.color_for(t['v'], 'data')[:3], 0.22)
def placed(boxes, open_box=None):
    for k, b in enumerate(boxes):
        p = row_pos(k); BX.panels(Wd, b, (p[0], p[1], 0.0), state='data', u=1.0, lid_open=(b == open_box), name='Row %d' % b)
        for (r, c) in A['boxes'][str(b)]:       # panels() が元のマスを跡にするので、その色を中身の青の跡に
            t = Wd['tiles'][(r, c)]; t.color = (*QW.color_for(t['v'], 'data')[:3], 0.22)
BR = rc(20, 20)
if KEY == 'G1':      # 18-01：右下の角（余白）に立って、大地を見上げる
    p = (rc(20, 21.8)[0], rc(20.6, 0)[1]); robot_at(p, 25)
    cam((p[0] + 3.4, p[1] - 5.6, 2.2), (rc(12, 16)[0], rc(12, 16)[1], 0.8), 22)
elif KEY == 'G2':    # 18-02：真上から。右下から2列ずつ、上へ・下へ（最初の2列は細かいジグザグ）
    z = QW.TILE_H + 0.35; pts = []
    for r in range(20, 8, -1): pts += [rc(r, 20), rc(r, 19)]
    for a, b in zip(pts[:-1], pts[1:]): beam((a[0], a[1], z), (b[0], b[1], z), col='#FFD640', r=0.13, strength=3.5)
    lanes = [(18, 17, -1), (16, 15, +1), (14, 13, -1)]; top = rc(8.6, 0)[1]; bot = rc(20.4, 0)[1]
    prev = (rc(9, 19.5)[0], top)
    for c1, c2, d in lanes:
        x = (rc(0, c1)[0] + rc(0, c2)[0]) / 2; y0, y1 = (top, bot) if d < 0 else (bot, top)
        beam((prev[0], prev[1], z), (x, y0, z), col='#FFD640', r=0.13, strength=3.5); beam((x, y0, z), (x, y1, z), col='#FFD640', r=0.13, strength=3.5); prev = (x, y1)
    text3d('▲', (rc(8.4, 19.5)[0], rc(8.4, 19.5)[1], z), 1.4, '#FFD640', rot=(0, 0, 0), emit=3.5)
    robot_at((rc(20, 21.8)[0], rc(20.6, 0)[1]), 25); cam((0, -0.01, 70), (0, 0, 0), 32)
elif KEY in ('G3a', 'G3'):   # 18-03：通った8マスが起き上がって箱になる
    c0 = BX.box_center(Wd, 1); p = (c0[0] + 2.2, c0[1] + 0.4); robot_at(p, heading_to(p, c0), pitch=-6)
    BX.panels(Wd, 1, c0, state='data', u=(0.5 if KEY == 'G3a' else 1.0), name='Fold')
    cam((c0[0] + 5.2, c0[1] - 6.8, 3.4), (c0[0] + 0.6, c0[1] + 0.6, 0.6), 30)
elif KEY == 'G4':    # 箱を頭に載せて運び、道の脇に一列に置いていく（2箱置いた・3箱目を運ぶ）
    placed([1, 2]); ghost([3]); p = (ROW_X - 0.2, row_pos(2)[1] + 1.6); robot_at(p, 180)
    BX.panels(Wd, 3, (p[0], p[1], 1.25), state='data', u=1.0, name='Held')
    cam((ROW_X + 5.0, row_pos(0)[1] - 6.0, 3.0), (ROW_X - 0.6, row_pos(2)[1], 0.8), 26)
elif KEY == 'G5':    # 9箱が一列に並んだ（早回しの終わり）
    placed(list(range(1, 10))); p = (ROW_X - 1.6, row_pos(9)[1] - 0.2); robot_at(p, 200)
    cam((ROW_X + 6.5, row_pos(0)[1] - 7.5, 5.0), (ROW_X - 1.0, row_pos(5)[1], 0.4), 22)
elif KEY in ('G6a', 'G6'):   # 19-01：最初の箱を開ける → 黒は1・白は0
    placed(list(range(1, 10)), open_box=1); c0 = row_pos(0); p = (c0[0] - 1.5, c0[1] + 0.9); robot_at(p, heading_to(p, c0), pitch=14)
    if KEY == 'G6':
        bits = format(S['box_bytes'][0], '08b'); gl = W.box('Glow', (1.2, 1.2, 0.05), W.mat_emit('Glow m', W.srgb('#9CC8FF'), 5.0)); gl.location = (c0[0], c0[1], 0.4)
        for k, bch in enumerate(bits):
            x = c0[0] - 3.5 * 0.62 + k * 0.62; zt = 2.35; blk = bch == '1'
            pl = W.box('bit', (0.54, 0.06, 0.66), W.mat('bitp%s' % bch, W.srgb(QW.COL['black'] if blk else QW.COL['white']), rough=0.5) if blk else W.mat_emit('bitw', W.srgb('#E9EEF2'), 1.2))
            pl.location = (x, c0[1] + 0.2, zt)
            text3d(bch, (x, c0[1] + 0.12, zt), 0.46, '#7FE3F0' if blk else '#15191F', emit=4.0 if blk else 0.3)
    cam((c0[0] + 1.2, c0[1] - 5.4, 2.4), (c0[0] - 0.2, c0[1] + 0.2, 1.3), 30)
elif KEY == 'G7':    # 19-02〜04.5：読む（上半分は暗い空。ここに図を重ねる）
    placed(list(range(1, 10))); p = (ROW_X - 1.4, row_pos(0)[1] - 1.2); robot_at(p, 20, pitch=-14)
    cam((ROW_X - 6.0, row_pos(0)[1] - 6.0, 1.6), (ROW_X + 1.0, row_pos(5)[1], 3.6), 22)
elif KEY in ('G8', 'G9'):    # 20：並んだ青い箱を見渡す → 予備の17個（橙のマス）がゆっくり光る
    placed(list(range(1, 10))); p = (ROW_X - 1.3, row_pos(4)[1]); robot_at(p, (75 if KEY == 'G9' else 160))
    if KEY == 'G9':
        gm = W.mat_emit('spare glow', W.srgb('#FFB060'), 1.4)
        for (r, c) in QW.cells_of(Wd, 'spare'):
            g = W.box('sg', (MOD * 0.62, MOD * 0.62, 0.05), gm); x, y = rc(r, c); g.location = (x, y, QW.TILE_H + 0.1)
    cam((ROW_X + 6.5, row_pos(4)[1] - 5.0, 4.6), (rc(9, 9)[0], rc(9, 9)[1], 0.0), 20)
W.render_setup(sc, engine='eevee', res=(960, 540), samples=16); sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
