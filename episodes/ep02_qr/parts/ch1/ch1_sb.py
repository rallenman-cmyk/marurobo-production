# 1章（中に入る）の絵コンテ：巨大なQRの大地＋箱（8マスがたたまれた箱）＋仮のまるロボ
#   blender -b --factory-startup -P ch1_sb.py -- KEY OUT.png
import sys, os, math
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import qr_world as QW
from kit import world as W
import op_stage_standin as SI
import ch1_box as BX
MOD = QW.MOD
def robot_at(xy, heading_deg, pitch=0.0, lift=0.0):
    root, torso, legs = SI.build_robot(); psi = math.radians(heading_deg)
    fx, fy = -math.sin(psi), math.cos(psi); rx, ry = math.cos(psi), math.sin(psi)
    z0 = QW.TILE_H + 0.04 + lift
    feet = [dict(ankle=[xy[0] + s * 0.255 * rx, xy[1] + s * 0.255 * ry, z0 + 0.17], psi=psi) for s in (-1, 1)]
    SI.pose(root, torso, legs, dict(root=[xy[0], xy[1], z0 - 0.01], psi=psi, pitch=pitch, twist=0.0, feet=feet))
    return root
def crate(name, loc, col, lid_open=False, glow=False):
    m = W.mat_emit(name + ' glow', col, 1.4) if glow else W.mat(name + ' mat', col, rough=0.5)
    b = W.box(name, (1.0, 1.0, 0.75), m, bevel=0.05); b.location = (loc[0], loc[1], loc[2] + 0.375)
    lid = W.box(name + ' lid', (1.04, 1.04, 0.08), m, bevel=0.03)
    if lid_open: lid.location = (loc[0], loc[1] + 0.52, loc[2] + 1.0); lid.rotation_euler = (math.radians(-70), 0, 0)
    else: lid.location = (loc[0], loc[1], loc[2] + 0.79)
    return b
def crates(Wd, state='neutral', only=None, lift=0.0, open_box=None, broken=()):
    S = Wd['symbol']
    for b in Wd['boxes']:
        if only and b not in only: continue
        role = 'data' if b in S['data_boxes'] else 'spare'
        st = None if state == 'neutral' else (role if state == 'role' else ('data' if role == 'data' else None))
        if b in broken: st = 'broken'
        BX.panels(Wd, b, BX.box_center(Wd, b), state=st, u=1.0, lid_open=(b == open_box), name='Box %d' % b)
def label(text, loc, size=1.6, col='#FFFFFF'):
    cu = bpy.data.curves.new('lab', 'FONT'); cu.body = text; cu.size = size; cu.align_x = 'CENTER'
    cu.font = bpy.data.fonts.load('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
    t = W.link(bpy.data.objects.new('lab', cu)); t.location = loc; t.rotation_euler = (math.radians(70), 0, 0)
    t.data.materials.append(W.mat_emit('lab', W.srgb(col), 2.0)); return t
def cam(loc, look, lens):
    cd = bpy.data.cameras.new('C'); cd.lens = lens; cd.clip_end = 600; c = W.link(bpy.data.objects.new('C', cd)); c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); bpy.context.scene.camera = c
def rc(r, c): return (-(21 * MOD) / 2 + (c + 0.5) * MOD, (21 * MOD) / 2 - (r + 0.5) * MOD)
KEY = sys.argv[sys.argv.index('--') + 1]; OUT = sys.argv[sys.argv.index('--') + 2]
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; Wd = QW.build(); QW.lights_c(sc, Wd['coll']); h = 21 * MOD / 2
fin = QW.cells_of(Wd, 'finder')
FOLD_B = 14
_cells = Wd['assets']['boxes'][str(FOLD_B)]; _c0 = Wd['xy'](*_cells[0]); _cen = Wd['boxes'][FOLD_B].location
FOLD_P = (_cen.x - 1.3, _cen.y + 1.5); FOLD_H = math.degrees(math.atan2(-(_cen.x - FOLD_P[0]), _cen.y - FOLD_P[1]))
def fold_cam(): cam((_cen.x + 4.6, _cen.y - 6.2, 3.2), (_cen.x - 0.4, _cen.y + 0.5, 0.6), 30)
if KEY.startswith('F'):   # たたむ：F1 端のマスを踏む / F2 起き上がる / F3 組み上がる / F4 箱
    QW.paint(Wd, fin, 'finder'); u = {'F1': 0.0, 'F2': 0.35, 'F3': 0.7, 'F4': 1.0}[KEY]
    if KEY == 'F1':
        QW.paint(Wd, _cells, 'restored'); robot_at((_c0.x, _c0.y), FOLD_H + 180, lift=0.15)
    else:
        robot_at(FOLD_P, FOLD_H, pitch=-6); BX.panels(Wd, FOLD_B, (_cen.x, _cen.y, 0.0), u=u, name='Fold')
    fold_cam()
elif KEY in ('K03v', 'K03h'):   # 縦に21マス／横に21マス
    BX.measure_lines(Wd, ('v',) if KEY == 'K03v' else ('v', 'h')); robot_at(rc(10, 14), 200); cam((0, -0.01, 66), (0, 0, 0), 32)
elif KEY == 'K05b':  # 「8マスずつのまとまり」：まとまりの1つがうすく光り、ふちに線
    QW.paint(Wd, fin, 'finder'); QW.paint(Wd, _cells, 'restored'); robot_at(FOLD_P, FOLD_H, pitch=6); fold_cam()
elif KEY == 'K02a':  # 画面の中へ：空から落ちてくる
    p = rc(17, 16); robot_at(p, 210, pitch=-20, lift=3.0); cam((p[0] + 5.0, p[1] - 7.0, 1.2), (p[0], p[1], 2.6), 22)
elif KEY == 'K04b':  # 目の光で角を照らすと、その目印が赤くなる（まず左上）
    tl = [rc_ for rc_ in fin if rc_[0] < 8 and rc_[1] < 8]; QW.paint(Wd, tl, 'finder')
    p = rc(9.5, 10.5); tgt = rc(3, 3); hd = math.degrees(math.atan2(-(tgt[0] - p[0]), tgt[1] - p[1])); robot_at(p, hd, pitch=-4)
    e0 = Vector((p[0], p[1], QW.TILE_H + 0.78)) + Vector((-math.sin(math.radians(hd)), math.cos(math.radians(hd)), 0)) * 0.5
    e1 = Vector((tgt[0], tgt[1], QW.TILE_H + 0.05)); dv = e1 - e0
    bm = W.mat_emit('Eye beam', W.srgb('#7FE3F0'), 4.0); bb = W.cyl('Eye beam', 0.06, dv.length, bm, seg=12); bb.location = e0 + dv / 2; bb.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler(); bb.visible_shadow = False
    mid = Vector(((p[0] + tgt[0]) / 2, (p[1] + tgt[1]) / 2, 0.4)); d2 = Vector((tgt[0] - p[0], tgt[1] - p[1], 0)).normalized(); perp = Vector((d2.y, -d2.x, 0))
    cam(tuple(mid + perp * 11.0 + Vector((0, 0, 4.0))), tuple(mid), 24)
elif KEY == 'K09a':  # 箱を開けると、中が光る（青）
    QW.paint(Wd, fin, 'finder'); b0 = 6; crates(Wd, 'neutral', only=[b for b in range(1, 27) if b != b0])
    c0 = BX.box_center(Wd, b0); BX.panels(Wd, b0, c0, state='data', u=1.0, lid_open=True, name='Open')
    gl = W.box('Glow', (1.2, 1.2, 0.05), W.mat_emit('Glow m', W.srgb('#9CC8FF'), 6.0)); gl.location = (c0[0], c0[1], 0.4)
    p = (c0[0] - 1.2, c0[1] + 1.1); hd = math.degrees(math.atan2(-(c0[0] - p[0]), c0[1] - p[1])); robot_at(p, hd, pitch=16); cam((c0[0] + 3.6, c0[1] - 4.4, 3.0), (c0[0] - 0.3, c0[1] + 0.4, 0.6), 30)
elif KEY == 'K15':  # 1章の終わり：箱が元のマスに戻っていく
    QW.paint(Wd, fin, 'finder'); S_ = Wd['symbol']
    for b in Wd['boxes']: BX.panels(Wd, b, BX.box_center(Wd, b), state=('data' if b in S_['data_boxes'] else 'spare'), u=0.45, name='Back %d' % b)
    robot_at(rc(10, 14), 200); cam((h * 0.95, -h * 1.25, 9.0), (-h * 0.1, h * 0.2, 0.0), 22)
elif KEY == 'K16':  # 元のマスに戻った（中身＝青・予備＝橙のまま）
    QW.paint(Wd, fin, 'finder'); QW.paint(Wd, QW.cells_of(Wd, 'data'), 'data'); QW.paint(Wd, QW.cells_of(Wd, 'spare'), 'spare')
    robot_at(rc(10, 14), 200); cam((h * 0.95, -h * 1.25, 9.0), (-h * 0.1, h * 0.2, 0.0), 22)
elif KEY == 'K02':   # 降り立つ（壮大）
    p = rc(17, 16); robot_at(p, 210, lift=0.35); cam((p[0] + 3.2, p[1] - 4.6, 1.5), (-h * 0.3, h * 0.5, 2.5), 18)
elif KEY == 'K03':  # 真上から全体
    robot_at(rc(10, 14), 200); cam((0, -0.01, 66), (0, 0, 0), 32)
elif KEY == 'K04':  # 目印が赤
    QW.paint(Wd, fin, 'finder'); robot_at(rc(10, 14), 200); cam((0, -0.01, 66), (0, 0, 0), 32)
elif KEY == 'K05':  # どこに書いてある？（見回す）
    QW.paint(Wd, fin, 'finder'); robot_at(rc(12, 12), 160, pitch=-8); cam((rc(12, 12)[0] + 4.5, rc(12, 12)[1] - 6.5, 2.0), (rc(12, 12)[0] - 2, rc(12, 12)[1] + 6, 1.2), 22)
elif KEY == 'K06':  # 26個とも箱に
    QW.paint(Wd, fin, 'finder'); crates(Wd, 'neutral'); robot_at(rc(12, 12), 160); cam((h * 0.9, -h * 1.2, 9.0), (-h * 0.1, h * 0.2, 0.0), 22)
elif KEY == 'K07':  # 箱を頭に載せる（たたんだばかりの箱。まわりはまだマス）
    QW.paint(Wd, fin, 'finder'); p = FOLD_P; robot_at(p, FOLD_H); BX.panels(Wd, FOLD_B, (p[0], p[1], 1.25), u=1.0, name='Held')
    for (r_, c_) in _cells: Wd['tiles'][(r_, c_)].color = (*QW.color_for(Wd['tiles'][(r_, c_)]['v'], None)[:3], 0.22)
    cam((p[0] + 3.0, p[1] - 4.2, 1.6), (p[0], p[1], 1.3), 32)
elif KEY == 'K08':  # 違うみたい（橙の箱をのぞく）
    QW.paint(Wd, fin, 'finder'); crates(Wd, 'neutral'); e = Wd['boxes'][20].location; p = (e.x + 1.2, e.y - 0.6)
    robot_at(p, 120, pitch=12); cam((p[0] + 2.8, p[1] - 3.6, 1.7), (e.x, e.y, 0.8), 30)
elif KEY == 'K09':  # 見つかりました：青い箱
    QW.paint(Wd, fin, 'finder'); crates(Wd, 'data_only'); robot_at(rc(12, 15), 150); label('HELLO', (rc(16, 18)[0], rc(16, 18)[1], 5.0), 2.4, '#7FB3FF')
    cam((h * 1.05, -h * 1.35, 6.5), (h * 0.3, -h * 0.25, 1.0), 22)
elif KEY == 'K10':  # 引いて：ほんの一角
    QW.paint(Wd, fin, 'finder'); crates(Wd, 'data_only'); cam((0, -0.01, 70), (0, 0, 0), 32)
elif KEY == 'K11':  # 冒頭でまるロボが乗っていた所（影）：その下の箱が灰色
    QW.paint(Wd, fin, 'finder'); A = Wd['assets']; crates(Wd, 'data_only', broken=A['experiments']['robot_stand']['bad_boxes'])
    robot_at(rc(16, 16), 200); cam((h * 0.6, -h * 1.3, 16), (h * 0.45, -h * 0.45, 0), 26)
elif KEY == 'K12':  # 開けてもらう：予備の箱は空
    QW.paint(Wd, fin, 'finder'); crates(Wd, 'data_only', open_box=20); e = Wd['boxes'][20].location; p = (e.x + 1.2, e.y - 0.6)
    robot_at(p, 120, pitch=14); cam((p[0] - 1.6, p[1] - 3.8, 2.2), (e.x, e.y, 0.7), 30)
elif KEY == 'K13':  # 青と橙で表す
    QW.paint(Wd, fin, 'finder'); crates(Wd, 'role'); robot_at(rc(10, 14), 200); cam((h * 0.95, -h * 1.25, 9.0), (-h * 0.1, h * 0.2, 0.0), 22)
elif KEY == 'K14':  # 予備の箱の群れ（低く）→ 目印へ
    QW.paint(Wd, fin, 'finder'); crates(Wd, 'role'); robot_at(rc(10, 10), 200); cam((rc(13, 8)[0], rc(13, 8)[1], 0.9), (rc(3, 3)[0], rc(3, 3)[1], 2.0), 20)
W.render_setup(sc, engine='eevee', res=(960, 540), samples=16); sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
