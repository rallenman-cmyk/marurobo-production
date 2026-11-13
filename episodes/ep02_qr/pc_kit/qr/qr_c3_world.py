# QRコード回・3章「読む」の中の世界の本番描画（PC・Blender 4.3.2・EEVEE）。台本 v2.0 の時刻（c3_v20_times.json）
#   blender -b --factory-startup --python qr_c3_world.py -- --blend story.blend --out DIR --frames 1:1514 --video 1 --vprefix qrc3w_
#   確認用：--standin 1（仮のまるロボ）。--still 300,1000 で指定のコマだけ PNG
#   描くのは 3D の場面だけ（c3_plan.WORLD_RANGES。目次・英数字の表は 2D）。3D の中に字は書かない（0 と 1 は板の白黒だけ。数字は 2D の札）
#   中身：右下の角 → ジグザグの道が伸びる（真上）→ 通った 8 マスが箱に → 早回し：運んで右の白いフチに 9 個並べる →
#         最初の箱のふたが開き、0 と 1 の板が 8 枚浮かぶ → 読む（空に 2D の図）→ 並んだ箱を見渡す → 予備の 17 個が光る
import sys, os, math, json, argparse
import bpy
from mathutils import Vector, Euler, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import marumotion as mm
import qr_world as QW
import c3_plan as CP
from c3_plan import FPS, s, e, fr_of, rc, H, MOD
ap = argparse.ArgumentParser()
ap.add_argument('--blend', default=''); ap.add_argument('--out', default='/tmp/qrc3w'); ap.add_argument('--frames', default='1:%d' % fr_of(CP.WORLD_RANGES[0][1]))
ap.add_argument('--res', nargs=2, type=int, default=[1920, 1080]); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--video', type=int, default=0); ap.add_argument('--vprefix', default='qrc3w_'); ap.add_argument('--standin', type=int, default=0)
ap.add_argument('--font', default=''); ap.add_argument('--still', default=''); ap.add_argument('--save', default='')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
F0, F1 = map(int, A.frames.split(':'))
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = F0, F1
O = bpy.data.objects
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
def interp(ob, kind, only=None):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if only and not fc.data_path.startswith(only): continue
            for kp in fc.keyframe_points: kp.interpolation = kind
def show(ob, spans):
    keys = [(1, True)]
    for a, b in spans: keys += [(max(2, fr_of(a)), False), (fr_of(b), True)]
    for f, h in keys: ob.hide_render = h; ob.keyframe_insert('hide_render', frame=f)
    interp(ob, 'CONSTANT', only='hide')

# ================================================================ 大地（目印＝赤・中身＝青・予備＝橙）
Wd = QW.build(); coll = Wd['coll']; QW.lights_c(sc, coll)
AS = Wd['assets']; SYM = Wd['symbol']; TILES = Wd['tiles']; TM = TILES[(0, 0)].data.materials[0]
QW.paint(Wd, QW.cells_of(Wd, 'finder'), 'finder'); QW.paint(Wd, QW.cells_of(Wd, 'data'), 'data'); QW.paint(Wd, QW.cells_of(Wd, 'spare'), 'spare')
CEV = []
def color_at(t, ob, rgba, ramp=0.15): CEV.append((t, ob, tuple(rgba), ramp))
def bake_colors():
    last = {}
    for t, ob, c, ramp in sorted(CEV, key=lambda x: x[0]):
        f = fr_of(t); prev = last.get(ob.name, tuple(ob.color))
        ob.color = prev; ob.keyframe_insert('color', frame=f)
        ob.color = c; ob.keyframe_insert('color', frame=f + max(1, int(round(ramp * FPS))))
        last[ob.name] = c
    for ob in {x[1] for x in CEV}: interp(ob, 'LINEAR', only='color')
def ghost(b, t):                                         # 箱になったあとのマスは、うっすら跡
    for rc_ in CP.BOX_CELLS[b]: tl = TILES[rc_]; color_at(t, tl, (*QW.color_for(tl['v'], 'data')[:3], 0.22), 0.2)

# ================================================================ 光る物
def beam(name, p0, p1, col='#FFD640', r=0.30, strength=4.0, t0=0.0, grow=0.3, t1=1.0):
    p0, p1 = Vector(p0), Vector(p1); dv = p1 - p0
    b = W.cyl(name, r, 1.0, W.mat_emit(name, W.srgb(col), strength), seg=12); b.visible_shadow = False
    b.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler()
    b.location = p0; b.scale = (1, 1, 0.001); b.keyframe_insert('location', frame=fr_of(t0)); b.keyframe_insert('scale', frame=fr_of(t0))
    b.location = p0 + dv / 2; b.scale = (1, 1, max(0.001, dv.length)); b.keyframe_insert('location', frame=fr_of(t0 + grow)); b.keyframe_insert('scale', frame=fr_of(t0 + grow))
    interp(b, 'LINEAR'); show(b, [(t0, t1)]); return b
# ---------------------------------------------------------------- 18-02b：ジグザグの道（2列ずつ、上へ・下へ）。右下から伸びていく
z = QW.TILE_H + 0.35; pts = []
for r in range(20, 8, -1): pts += [rc(r, 20), rc(r, 19)]
top, bot = rc(8.6, 0)[1], rc(20.4, 0)[1]; prev = (rc(9, 19.5)[0], top)
for c1, c2, d in ((18, 17, -1), (16, 15, +1), (14, 13, -1)):
    x = (rc(0, c1)[0] + rc(0, c2)[0]) / 2; y0, y1 = (top, bot) if d < 0 else (bot, top)
    pts += [(x, y0), (x, y1)]
segs = list(zip(pts[:-1], pts[1:])); L = [math.dist(a, b) for a, b in segs]; Lt = sum(L); tcur = CP.T_PATH[0]
for k, ((a, b), l) in enumerate(zip(segs, L)):
    g = (CP.T_PATH[1] - CP.T_PATH[0]) * l / Lt
    beam('path %02d' % k, (a[0], a[1], z), (b[0], b[1], z), t0=tcur, grow=g, t1=CP.shot_start('G3a')); tcur += g

# ================================================================ 箱（中身の 9 個だけ）：8 枚の板（マスの白黒）＋床＋ふた。箱ごとに根元の空の物
PANEL, WALL_H, BOXW = 0.7, 0.7, 1.4; Z0 = QW.TILE_H
def panel_targets():
    out = []
    for side, (nx, ny) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        n = Vector((nx, ny, 0)); tv = Vector((-ny, nx, 0))
        for k in (-1, 1): out.append((n * (BOXW / 2) + tv * (PANEL / 2 * k) + Vector((0, 0, WALL_H / 2)), math.atan2(ny, nx) - math.pi / 2))
    return out
PT_ = panel_targets()
def panel_color(v):
    base = W.srgb(QW.COL['black'] if v else QW.COL['white']); tint = W.srgb(QW.COL['data'])
    return (*QW.mixc(base, tint, 0.45 if v else 0.62), 1.0)
floor_m = W.mat('Box floor', (0.30, 0.32, 0.35), rough=0.6); lid_m = W.mat('Box lid', QW.mixc((0.86, 0.88, 0.90), W.srgb(QW.COL['data']), 0.7), rough=0.5)
BX = {}; CEN = {b: Vector((*CP.box_c(b), 0.0)) for b in range(1, 10)}
for b in range(1, 10):
    root = W.link(O.new('BoxRoot %d' % b, None)); root.location = (CEN[b].x, CEN[b].y, Z0)
    pans = []
    for i, (r, c) in enumerate(CP.BOX_CELLS[b]):
        p = W.box('Box %d panel %d' % (b, i), (1, 1, 1), TM, bevel=0.0, seg=1); p.parent = root; p['v'] = TILES[(r, c)]['v']; p.color = panel_color(p['v']); pans.append(p)
    fl = W.box('Box %d floor' % b, (BOXW, BOXW, 0.04), floor_m); fl.parent = root; fl.location = (0, 0, 0.02)
    hinge = W.link(O.new('Box %d hinge' % b, None)); hinge.parent = root; hinge.location = (BOXW / 2, 0, WALL_H); hinge.rotation_euler = (0, 0, math.radians(-90))   # 蝶番は右（奥）。ふたは左（まるロボの側）が持ち上がる
    lid = W.box('Box %d lid' % b, (BOXW + 0.05, BOXW + 0.05, 0.08), lid_m, bevel=0.02); lid.parent = hinge; lid.location = (0, -(BOXW + 0.05) / 2, 0.04)
    BX[b] = dict(root=root, pans=pans, floor=fl, hinge=hinge, lid=lid)
def pose_panels(b, u, f):
    B = BX[b]; c = CEN[b]
    for i, (r, cc) in enumerate(CP.BOX_CELLS[b]):
        p = B['pans'][i]; p0 = Vector((*rc(r, cc), 0.0)) - c; p0.z = QW.TILE_H / 2 - Z0 + (0.04 if p['v'] else 0.0)
        p1, rz = PT_[i]; ui = max(0.0, min(1.0, u * 1.6 - i * 0.075)); s_ = ui * ui * (3 - 2 * ui)
        p.location = p0.lerp(p1, s_) + Vector((0, 0, math.sin(math.pi * s_) * 1.6))
        sz = (MOD - QW.GAP) * (1 - s_) + PANEL * s_; p.scale = (sz, sz, QW.TILE_H * (1 - s_) + 0.05 * s_)
        p.rotation_euler = Euler((math.pi / 2 * s_, 0, rz * s_), 'XYZ'); p.hide_render = u <= 0.0
        for dp in ('location', 'scale', 'rotation_euler', 'hide_render'): p.keyframe_insert(dp, frame=f)
    s2 = min(1.0, max(0.0, (u - 0.86) / 0.14))
    B['hinge'].location.z = WALL_H + (1 - ease(s2)) * 0.9; B['hinge'].keyframe_insert('location', index=2, frame=f)
    for ob, vis in ((B['lid'], s2 > 0.0), (B['floor'], u >= 0.999)): ob.hide_render = not vis; ob.keyframe_insert('hide_render', frame=f)
def key_root(b, f, loc, yaw=0.0, pitch=0.0):
    R_ = BX[b]['root']; R_.location = loc; R_.rotation_euler = (pitch, 0, yaw); R_.keyframe_insert('location', frame=f); R_.keyframe_insert('rotation_euler', frame=f)
plan, FR = CP.frames()
def frame_at(t): return FR[min(len(FR) - 1, max(0, int(round(t * FPS))))]
def head_top(f):
    psi = f['psi']; Rr = Matrix.Rotation(psi, 3, 'Z') @ Matrix.Rotation(math.radians(-f['pitch']), 3, 'X')
    c = Vector(f['root']) + Vector((0, 0, mm.TORSO_Z)); return c + Rr @ Vector((0, -0.02, 0.50)), psi, math.radians(-f['pitch'])
ROWZ = CP.QZ_TOP - 0.01
for b in range(1, 10):
    pose_panels(b, 0.0, 1); key_root(b, 1, (CEN[b].x, CEN[b].y, Z0))
# 1：通った 8 マスが起き上がって箱に（18-03）→ 早回しで右の白いフチの 1 番目へ
for f in range(fr_of(CP.T_FOLD1[0]) - 1, fr_of(CP.T_FOLD1[1]) + 2): pose_panels(1, min(1.0, max(0.0, ((f - 1) / FPS - CP.T_FOLD1[0]) / (CP.T_FOLD1[1] - CP.T_FOLD1[0]))), f)
ghost(1, CP.T_FOLD1[0])
def place(b, k, t):
    f = fr_of(t); pose_panels(b, 1.0, f); key_root(b, f - 1, BX[b]['root'].location.copy()); rp = CP.row_pos(k); key_root(b, f, (rp[0], rp[1], ROWZ))
    interp(BX[b]['root'], 'CONSTANT', only='location')
key_root(1, fr_of(CP.T_G4) - 1, (CEN[1].x, CEN[1].y, Z0)); rp0 = CP.row_pos(0); key_root(1, fr_of(CP.T_G4), (rp0[0], rp0[1], ROWZ))
place(2, 1, CP.T_G4); ghost(2, CP.T_G4 - 0.1)
# 3：早回しの途中。まるロボの頭の上に載せて運ぶ → 3 番目へ
pose_panels(3, 1.0, fr_of(CP.T_G4)); ghost(3, CP.T_G4 - 0.1)
for f in range(fr_of(CP.T_G4), fr_of(CP.T_G5)):
    hp, yaw, pit = head_top(frame_at((f - 1) / FPS)); key_root(3, f, hp, yaw, pit)
rp = CP.row_pos(2); key_root(3, fr_of(CP.T_G5), (rp[0], rp[1], ROWZ), 0.0, 0.0)
for b in range(4, 10): place(b, b - 1, CP.T_G5); ghost(b, CP.T_G5 - 0.1)
for b in range(1, 10): interp(BX[b]['root'], 'CONSTANT')
# 19-01：最初の箱のふたが開く（まるロボが頭で押し上げる）
T_OPEN = CP.s('19-01', 2.25)
h1 = BX[1]['hinge']
for t, ang in ((0.0, 0.0), (T_OPEN, 0.0), (T_OPEN + 0.35, 112.0)): h1.rotation_euler.x = math.radians(-ang); h1.keyframe_insert('rotation_euler', index=0, frame=fr_of(t))
# 19-01b：0 と 1 の板が 8 枚浮かぶ（板の白黒だけ。数字は 2D の札）。中が青く光る
bits = format(SYM['box_bytes'][0], '08b'); c0 = Vector((*CP.C0R, ROWZ))
gl = W.box('Glow', (1.2, 1.2, 0.05), W.mat_emit('Glow m', W.srgb('#9CC8FF'), 5.0)); gl.location = c0 + Vector((0, 0, 0.4)); show(gl, [(T_OPEN + 0.2, 9e3)])
bm = {'1': W.mat('bit black', W.srgb(QW.COL['black']), rough=0.5), '0': W.mat_emit('bit white', W.srgb('#E9EEF2'), 1.2)}
G6_SPANS = [(CP.T_BITS, CP.shot_start('G7', 50.0)), (CP.shot_start('G6', 75.0), CP.shot_start('c3_alnum'))]
for k, bch in enumerate(bits):
    pl = W.box('bit %d' % k, (0.54, 0.06, 0.66), bm[bch]); x = c0.x - 3.5 * 0.62 + k * 0.62; ta = CP.T_BITS + 0.12 * k
    for t, loc in ((ta, (c0.x, c0.y, 0.5)), (ta + 0.7, (x, c0.y + 0.2, 2.35))): pl.location = loc; pl.keyframe_insert('location', frame=fr_of(t))
    show(pl, [(ta, G6_SPANS[0][1]), G6_SPANS[1]])
# 20-02：予備の 17 個（橙のマス）がゆっくり光る
gm = W.mat_emit('spare glow', W.srgb('#FFE2B0'), 6.0)
for (r, c) in QW.cells_of(Wd, 'spare'):
    g = W.box('sg %d-%d' % (r, c), (MOD * 0.7, MOD * 0.7, 0.06), gm); x, y = rc(r, c); g.location = (x, y, QW.TILE_H + 0.12); g.visible_shadow = False
    for k in range(6):
        t = CP.T_SPARE + 1.0 * k; g.scale = (0.6, 0.6, 1); g.keyframe_insert('scale', frame=fr_of(t)); g.scale = (1.0, 1.0, 1); g.keyframe_insert('scale', frame=fr_of(t + 0.5))
    show(g, [(CP.T_SPARE, 9e3)])
bake_colors()

# ================================================================ まるロボ
if A.standin:
    import op_stage_standin as SI
    rroot, rtorso, rlegs = SI.build_robot()
    for f in range(F0, F1 + 1): SI.pose(rroot, rtorso, rlegs, FR[min(len(FR) - 1, f - 1)], key=f)
else:
    import marurig as mr
    assert os.path.exists(A.blend), 'story.blend が見つからない。--blend で指定する'
    with bpy.data.libraries.load(A.blend, link=False) as (src, dst): dst.objects = [n for n in src.objects]
    loaded = [o for o in dst.objects if o is not None]; maru0 = next(o for o in loaded if o.name == 'Maru')
    keep = {o.name for o in hier(maru0)}
    for o in loaded:
        if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
    for n in keep: sc.collection.objects.link(O[n])
    for n in keep:
        if O[n].animation_data: O[n].animation_data_clear()
    for o in hier(O['Maru']):
        if o.name.startswith(('Cradle', 'Maru cargo')) or 'cradle' in o.name.lower(): o.hide_render = True
    rig = mr.MaruRig(O['Maru']); bk = mr.Baker()
    for i, fr in enumerate(FR):
        if F0 - 2 <= i + 1 <= F1 + 2: rig.apply(fr, i + 1, bk)
    bk.write()

# ================================================================ カメラ
C = lambda *v: Vector(v)
X, rp = CP.ROW_X, CP.row_pos; c0v = Vector((*CP.C0, 0)); r0 = Vector((*CP.C0R, 0)); pg1 = Vector((*CP.P_G1, 0))
VIEWS = {
    'G1': (pg1 + C(3.4, -5.6, 2.2), C(*rc(12, 16), 0.8), 22),
    'G2': (C(0, -0.01, 70), C(0, 0, 0), 32),
    'G3a': (c0v + C(5.2, -6.8, 3.4), c0v + C(0.6, 0.6, 0.6), 30), 'G3': (c0v + C(5.2, -6.8, 3.4), c0v + C(0.6, 0.6, 0.6), 30),
    'G4': (C(X + 5.0, rp(0)[1] - 6.0, 3.0), C(X - 0.6, rp(2)[1], 0.8), 26),
    'G5': (C(X + 6.5, rp(0)[1] - 7.5, 5.0), C(X - 1.0, rp(5)[1], 0.4), 22),
    'G6a': (r0 + C(1.2, -5.4, 2.4), r0 + C(-0.2, 0.2, 1.3), 30), 'G6': (r0 + C(1.2, -5.4, 2.4), r0 + C(-0.2, 0.2, 1.3), 30),
    'G7': (C(X - 6.0, rp(0)[1] - 6.0, 1.6), C(X + 1.0, rp(5)[1], 3.6), 22),
    'G8': (C(X + 6.5, rp(4)[1] - 5.0, 4.6), C(*rc(9, 9), 0.0), 20), 'G9': (C(X + 6.5, rp(4)[1] - 5.0, 4.6), C(*rc(9, 9), 0.0), 20),
}
PUSH = {'G2': 0.02, 'G4': 0.0, 'G5': 0.0}
SH = [(a, b, k) for a, b, k in CP.SHOTS if k in VIEWS]
for n_, (t0, t1, k) in enumerate(SH):
    L, T, lens = VIEWS[k]; cd = bpy.data.cameras.new('Cam %02d %s' % (n_, k)); cd.lens = lens; cd.clip_end = 900; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cam = W.link(O.new('Cam %02d %s' % (n_, k), cd)); cam.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler(); d1 = PUSH.get(k, 0.04)
    for t, dd in ((t0, 0.0), (t1, d1)): cam.location = L + (T - L) * dd; cam.keyframe_insert('location', frame=fr_of(t))
    interp(cam, 'LINEAR')
    m = sc.timeline_markers.new('c3 %02d %s' % (n_, k), frame=fr_of(t0)); m.camera = cam
    if n_ == 0: sc.camera = cam

# ================================================================ 描く
W.render_setup(sc, engine='eevee', res=tuple(A.res), samples=A.samples)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=A.save)
def cam_at(f):
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f: sc.camera = m.camera
if A.still:
    for f in [int(x) for x in A.still.split(',')]:
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w3_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif A.video:
    cam_at(F0); sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'; sc.render.filepath = os.path.join(A.out, A.vprefix)
    bpy.ops.render.render(animation=True)
else:
    for f in range(F0, F1 + 1):
        sc.frame_set(f); cam_at(f); sc.render.filepath = os.path.join(A.out, 'w3_%04d.png' % f); bpy.ops.render.render(write_still=True)
json.dump(dict(fps=FPS, frames=[F0, F1], ranges=CP.WORLD_RANGES, late=CP.LATE, fold1=CP.T_FOLD1, g4=CP.T_G4, g5=CP.T_G5, open=T_OPEN, bits=CP.T_BITS, spare=CP.T_SPARE,
               events=[ev for ev in plan.events if ev['kind'] in ('step', 'step_turn', 'takeoff', 'land', 'beep_happy', 'beep_yes', 'beep_surprise')], shots=SH),
          open(os.path.join(A.out, 'qrc3w_log_%d.json' % F0), 'w'), default=float, indent=0)
print('QRC3W DONE', F0, F1)
