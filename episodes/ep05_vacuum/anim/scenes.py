# 5本目（ロボット掃除機）：3D の場面を声の時刻に合わせて動かして描く
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 8] [--res 480 270] [--step 3] [--stills 秒,秒] [--track] [--tex <絵のフォルダ>]
#   PC の本番：... -- <クリップ> <出力> --samples 48 --res 1920 1080 --frames 0 99 --gpu --video --tex <絵のフォルダ>（run_pc_render_ep05.ps1 が呼ぶ）
#   クリップの一覧は下の CLIPS（名前 → 場面の組み立て・始め・終わり）。始め・終わりは声の時刻（voice/placement.json）から出す
#   場面の組み立て（b_*）は、まるロボと先輩の動きをクリップに関係なく全部作り、カメラだけをクリップごとに選ぶ
#   （カットの前後で、まるロボや先輩の場所が飛ばないように。SKILL §5「カットで置き直さない」）
#   部品は kit.py、時刻と動きの共通は core.py、間取りは plan.py
#   決まり（SKILL・制作バイブル）：3D の中に字を書かない／まるロボと先輩は喋らない（電子音と身ぶり）／
#     動きは言い終えてから／瞬間移動に見せない（歩いて移る）／カメラはいつもゆっくり動かす／
#     光の点は青緑で最後まで同じ表し方／通った道の線は黄色／いま見えている形は白っぽい点
import os, sys
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
exec(open(os.path.join(KIT_HERE, "core.py"), encoding="utf-8").read())
CLIPNAME, OUTDIR = _argv[0], _argv[1]


def _opt(name, n=1, default=None):
    if name in _argv:
        i = _argv.index(name); v = _argv[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default


SAMPLES = int(_opt("--samples", 1, 8)); RES = tuple(int(x) for x in _opt("--res", 2, ("480", "270"))); STEP = int(_opt("--step", 1, 3))
STILLS = [float(x) for x in _opt("--stills", 1, "").split(",") if x]
TEX = _opt("--tex", 1, os.environ.get("MARU_TEX", os.path.join(KIT_HERE, "tex")))
TRACK_ONLY = "--track" in _argv
YELLOW = "#FFD24A"
DOCKP = (0.3, 2.12)                 # 充電の台にいるときの光の物差しの先輩（前＝-y を部屋に向ける）
DOCK2 = (2.75, 1.2)                 # カメラの先輩の台（右の壁、机とベッドの間）
DESK_Z = 0.755
MARU_DESK = (1.95, 2.0, DESK_Z)
PHONE_DESK = (1.55, 1.93, DESK_Z)


def tex(n): return os.path.join(TEX, n)


def cut(cl, name): return cl == name


def dashed_ring(parent, r=0.17, n=16, col=None, strength=5.0, name="ghostring"):
    """どこにいるか分からない（思っているだけの）先輩の場所：床の上の白い点線の輪（v3。S13 と S15 で同じ表し方）"""
    g = empty((0, 0, 0.0)); g.parent = parent
    gm_ = glow_mat(name, col or WHITE_PT, strength)
    for k in range(n):
        a0 = 2 * math.pi * k / n
        o_ = cube(gm_, (r * math.cos(a0), r * math.sin(a0), 0.02), (0.045, 0.012, 0.012), parent=g); o_.rotation_euler = (0, 0, a0 + math.pi / 2); o_.visible_shadow = False
    return g


# ======================================================================== S01〜S05：誰も教えていないのに、地図が出た／先輩に会う
def b_open(cl):
    room(); door_leaf(False)
    sp = Sp(senpai_lidar(DOCKP, 0)); sp.spin(0, 100, 0.6)
    t0 = s("01-01") + 0.3
    dr = plan.Drive([(0.3, 0.6), (0.3, 1.7)], t0, v=0.36, face0=180)
    sp.drive(dr)
    t1 = dr.t1
    sp.place(t1 + 0.05, 0.3, 1.7, 180); sp.place(t1 + 1.3, 0.3, 1.7, 360); sp.place(t1 + 2.2, 0.3, DOCKP[1], 360)
    ev(t1 + 2.2, "motor_off", 0.5)
    sp.pi(s("01-02"), n=1, sound=False); ev(s("01-02"), "chime", 0.7)            # 「ピロリン」は声と同時に
    m = Maru(MARU_DESK, face=face_to(MARU_DESK, (0.3, 1.5)))
    m.at(s("01-01"), look=-8); m.at(s("01-03") + 0.3, look=-14)
    # スマホ（横向き）：「何かが……」で画面がつく → 言うたびに家具が光る → いまいる場所に輪（2D の大きなスマホの絵はやめた）
    ph, scr = phone_seq(PHONE_DESK, -95, [(0, tex("phone3d_off.png")), (e("02-01") - 0.3, tex("phone3d_base.png")),
        (w("02-03", "ソファ"), tex("phone3d_sofa.png")), (w("02-03", "机"), tex("phone3d_desk.png")), (w("02-03", "ベッド"), tex("phone3d_bed.png")),
        (e("02-03") + 0.2, tex("phone3d_base.png")), (w("02-04", "この点"), tex("phone3d_ring.png"))])
    for wd in ("ソファ", "机", "ベッド"): ev(w("02-03", wd), "pi", 0.18)
    ev(w("02-04", "この点"), "pop", 0.4)
    ev(e("02-01") - 0.3, "notify", 0.6)
    # 02：スマホに地図 → まるロボがのぞきこむ
    fp = face_to(MARU_DESK, PHONE_DESK); f0 = face_to(MARU_DESK, (0.3, 1.5))
    m.at(s("02-01") + 0.2, face=fp, look=-25); m.peer(s("02-02") + 0.1, dur=1.8)      # 「これは……地図でしょうか？」でのぞき込む（一覧の peer）
    r = ring_marker(DOCKP, 0.24, YELLOW); show_between(r, s("02-05") + 0.2, s("03-01")); scale_pop(r, s("02-05") + 0.2); ev(s("02-05") + 0.2, "pop", 0.5)
    m.at(s("02-05") + 0.2, face=f0, look=-14)
    # 03：感心 → 待って → 見回す → 首をかしげる
    m.at(s("03-01") - 0.3, face=fp, look=-25); m.at(s("03-01") + 0.85, face=f0, look=-12)
    m.nod(w("03-01", "偉い"), n=2)          # 本物の体：うなずきは予定の nod（体を手で回さない）
    m.at(s("03-02") + 0.1, look=0); m.blink(s("03-02") + 0.15)
    m.at(s("03-03") + 0.2, face=f0 - 60); m.at(s("03-03") + 2.0, face=f0 + 50); m.at(s("03-03") + 3.3, face=fp)
    m.at(s("03-04") + 0.2, face=fp, look=-25); m.at(s("03-04") + 2.0, face=f0, look=-10); m.confused(s("03-04") + 2.2)      # 「いったいどうやって？」（一覧の confused）
    # 04：机から降りて、先輩の前へ。あいさつ
    #   v6（本物の歩きは大きさ 0.26 で約 0.26 m/秒。短い歩きも向きを変えると 3 秒ほど）：「確かめに行ってみます」で机の前のふちへ歩き、
    #   床へ跳び、「まるロボが、掃除機の前へ」で斜め前（GREET）へ歩く。あいさつの「ピポ」の前に着く
    ta = s("04-01")
    GREET = (1.05, 1.5)
    m.jump(s("03-05") - 0.1, (MARU_DESK[0], MARU_DESK[1]), (1.45, 1.55), z_to=0.0, apex=0.2)     # 机の上から床へ跳び降りる（一覧の jump_to。音は takeoff・land）。v6：少し高く跳んで机のふちを越え、机の前に着く（カメラは引いて床まで入れる）
    m.at(s("04-02") - 0.6, loc=(GREET[0], GREET[1], 0.0), look=5)       # 歩いて来た向き（ほぼ先輩の方）のまま止まる
    m.greet(s("04-02") - 0.6)           # あいさつ（一覧の greet：おじぎと beep_hello。声の前のすき間に）
    sp.pi(s("04-02") + 0.98, n=2)          # 先輩の返事は、声の「……」の間（声の頭から 0.95〜1.53 秒の無音）に
    m.hops(s("04-04") + 0.6, n=2, height=0.06)       # うれしい（一覧の hops）
    # 05：先輩の体をぐるりと（v6：まるロボは GREET にいたまま。カメラが左側から回る）
    m.at(e("04-04") + 1.0, face=face_to(GREET, DOCKP), look=10)
    d = sp.d
    lr = ring_marker((0.3, 2.155), 0.075, YELLOW, w=0.004, z=d["top_z"] + 0.03); show_between(lr, s("05-02") + 0.1, e("05-02") + 0.6); scale_pop(lr, s("05-02") + 0.1); ev(s("05-02") + 0.1, "pop", 0.4)
    bm = bpy.data.materials["sp_bumper"]; bm.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = srgb(YELLOW)
    emit_key(bm, s("05-03") + 0.2, 0.0); emit_key(bm, s("05-03") + 0.5, 1.6); emit_key(bm, e("05-03") + 0.4, 1.6); emit_key(bm, e("05-03") + 0.8, 0.0)
    th = w("05-03", "へこむ")
    key(d["bumper"], ("location", 1), th, 0.0); key(d["bumper"], ("location", 1), th + 0.2, 0.012); key(d["bumper"], ("location", 1), th + 0.5, 0.0); ev(th + 0.2, "click", 0.4)
    bl = d["belly"].data.materials[0]; bl.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = srgb(YELLOW)
    emit_key(bl, s("05-04") + 0.2, 0.0); emit_key(bl, s("05-04") + 0.6, 14.0); emit_key(bl, e("05-04") + 0.5, 14.0); emit_key(bl, e("05-04") + 0.9, 0.0)
    m.peer(s("05-04") + 0.2, dur=1.8)           # おなかの下の窓をのぞき込む
    t3 = w("05-05", "3つ")
    le = bpy.data.materials["lid_eye"]
    emit_key(le, t3, 4.0); emit_key(le, t3 + 0.2, 14.0); emit_key(le, t3 + 0.8, 4.0)
    emit_key(bm, t3 + 0.5, 0.0); emit_key(bm, t3 + 0.7, 1.6); emit_key(bm, t3 + 1.3, 0.0)
    emit_key(bl, t3 + 1.0, 0.0); emit_key(bl, t3 + 1.2, 14.0); emit_key(bl, t3 + 1.8, 0.0)
    ev(t3, "pi", 0.3)                     # 3 か所が順に光る（音は頭の 1 つだけ。声と重ねない）
    m.nod(e("05-05") - 0.3)                     # 「覚えておいてくださいね」→ はい
    # カメラ
    if cut(cl, "S01a"):
        c, tg = cam_rig((-1.4, -1.6, 1.15), (0.5, 1.7, 0.25), 30)
        cam_move(c, tg, s("01-01"), e("01-02") + 0.5, (-1.4, -1.6, 1.15), (-0.9, -1.0, 1.0), (0.5, 1.7, 0.25), (0.45, 1.9, 0.25))
    elif cut(cl, "S01b"):
        c, tg = cam_rig((2.6, 0.9, 1.25), (1.95, 2.0, 0.9), 40)
        cam_move(c, tg, s("01-03") - 0.6, e("01-03") + 0.5, (2.75, 0.85, 1.3), (2.55, 1.05, 1.18), (1.9, 2.0, 0.92), (1.9, 2.0, 0.9)); dof(c, m.root, 3.0)
    elif cut(cl, "S02a"):     # 机の上 → スマホに寄って、画面の地図を大きく（3D のまま）
        c, tg = cam_rig((1.95, 1.2, 1.1), (1.72, 1.97, 0.82), 36)
        cam_move(c, tg, s("02-01") - 0.8, s("02-02"), (2.0, 1.15, 1.12), (1.85, 1.35, 1.02), (1.72, 1.97, 0.84), (1.65, 1.95, 0.8))   # 「！」の間はまるロボを映したまま
        cam_move(c, tg, s("02-02"), s("02-03"), (1.85, 1.35, 1.02), (1.57, 1.70, 1.0), (1.65, 1.95, 0.8), (1.55, 1.97, 0.70), 36, 44)
        cam_move(c, tg, s("02-03"), e("02-04") + 1.2, (1.57, 1.70, 1.0), (1.562, 1.712, 0.992), (1.55, 1.97, 0.70), (1.55, 1.97, 0.696), 44, 45)   # スマホは字幕の帯より上に
        dof(c, ph, 5.6)
    elif cut(cl, "S02b"):
        c, tg = cam_rig((-0.4, 0.6, 0.7), (0.3, 2.1, 0.12), 34)
        cam_move(c, tg, s("02-05") - 0.6, e("02-05") + 0.6, (-0.45, 0.55, 0.72), (-0.2, 0.9, 0.55), (0.3, 2.1, 0.12), (0.3, 2.12, 0.1))
    elif cut(cl, "S03a"):
        c, tg = cam_rig((2.0, 0.6, 1.0), (1.4, 2.0, 0.6), 30)
        cam_move(c, tg, s("03-01") - 0.8, s("03-05") - 2.0, (2.2, 0.55, 1.05), (1.85, 0.45, 1.0), (1.5, 2.0, 0.62), (1.4, 2.0, 0.6)); dof(c, m.root, 5.6)
        cam_move(c, tg, s("03-05") - 2.0, s("03-05") + 1.6, (1.85, 0.45, 1.0), (1.75, -0.3, 1.1), (1.4, 2.0, 0.6), (1.3, 1.9, 0.52))      # v6：跳び降りるまるロボが、跳ぶ高さから床に着くまで入るように引く
    elif cut(cl, "S04a"):
        c, tg = cam_rig((1.6, -0.3, 0.9), (1.4, 1.8, 0.55), 28)
        cam_move(c, tg, s("04-01") - 0.6, s("04-01") + 1.2, (1.7, -0.4, 0.95), (1.55, -0.1, 0.85), (1.6, 1.8, 0.6), (1.3, 1.7, 0.3))
        cam_move(c, tg, s("04-01") + 1.2, e("04-02") + 0.4, (1.55, -0.1, 0.85), (1.2, 0.3, 0.55), (1.3, 1.7, 0.3), (0.5, 1.9, 0.15))
        cam_move(c, tg, e("04-02") + 0.4, e("04-04") + 0.5, (1.2, 0.3, 0.55), (1.0, 0.75, 0.32), (0.5, 1.9, 0.15), (0.4, 1.85, 0.12)); dof(c, m.root, 4.0)
    elif cut(cl, "S05a"):
        # v6：まるロボが右前（GREET）にいるので、左側から回る（前の動きを x＝0.3 で左右に映した形）
        c, tg = cam_rig((-0.6, 1.0, 0.6), (0.3, 2.1, 0.08), 38)
        cam_move(c, tg, s("05-01") - 0.8, e("05-02") + 0.3, (-0.65, 1.05, 0.6), (-0.05, 1.25, 0.55), (0.3, 2.12, 0.1), (0.3, 2.15, 0.12), 38, 46)
        cam_move(c, tg, e("05-02") + 0.3, e("05-03") + 0.3, (-0.05, 1.25, 0.55), (-0.15, 1.45, 0.2), (0.3, 2.15, 0.12), (0.3, 1.98, 0.06), 46, 46)
        cam_move(c, tg, e("05-03") + 0.3, e("05-04") + 0.3, (-0.15, 1.45, 0.2), (0.05, 1.6, 0.03), (0.3, 1.98, 0.06), (0.3, 2.0, 0.01), 46, 50)
        cam_move(c, tg, e("05-04") + 0.3, e("05-05") + 0.6, (0.05, 1.6, 0.03), (-0.25, 1.05, 0.5), (0.3, 2.0, 0.01), (0.5, 2.0, 0.1), 50, 32)
    track("maru", m.root, 0.42); track("senpai", sp.root, 0.15)
    # v6（ユーザー「バンパーの吹き出しは画面の右側からで、バンパーの位置をちゃんとわかるように」）：札が指す点を、物の上に置く
    for nm_, lp_ in (("bumper_pt", (0.105, -0.12, 0.05)), ("belly_pt", (0.0, -0.13, 0.0))):
        e_ = empty(lp_); e_.parent = sp.root; track(nm_, e_, 0.0)


# ======================================================================== S06：昔の先輩（2002 年ごろ。セピアは組み立てで付ける）
def b_old(cl):
    room(front_wall=cut(cl, "S06b")); door_leaf(False)
    op = Sp(senpai_old((0.0, -0.4), 0))
    # まっすぐ → ぶつかったら向きを変える。06-07「押されます」で、ちょうどぶつかるように時刻をずらす
    pts, hits = plan.bounce_path((0.0, 0.3), 120, 9, 297, r=0.21)   # 並びは、部屋の奥まで広く走るものを選んだ（手前の壁ぎわばかりだと映らない）
    t_hit = w("06-07", "押されます") + 0.1
    dr = plan.Drive(pts, 0.0, v=0.3, turn=110)
    arr = [k[0] for k in dr.keys if any(abs(k[1] - p[0]) < 1e-6 and abs(k[2] - p[1]) < 1e-6 for p in pts[1:])]
    def open_wall(p):
        for k in ("sofa", "desk", "bed", "shelf"):
            x0_, y0_, x1_, y1_ = plan.FURN[k][:4]
            if x0_ - 0.3 < p[0] < x1_ + 0.3 and y0_ - 0.3 < p[1] < y1_ + 0.3: return False
        x0_, y0_, x1_, y1_ = plan.ROOM
        return min(p[0] - x0_, x1_ - p[0], p[1] - y0_, y1_ - p[1]) < 0.3      # 部屋の壁にぶつかる所
    hit_pts = {round(k[0], 4): (k[1], k[2]) for k in dr.keys if any(abs(k[1] - p[0]) < 1e-6 and abs(k[2] - p[1]) < 1e-6 for p in pts[1:])}
    cand = [a for a in arr if t_hit - a <= s("06-01") - 0.5 and open_wall(hit_pts[round(a, 4)])]
    shift = t_hit - min(cand) if cand else s("06-01")
    dr = plan.Drive(pts, shift, v=0.3, turn=110)
    t_end_rand = min(dr.t1, s("06-09") - 0.4)
    op.drive(dr, max(dr.t0, s("06-01") - 2), t_end_rand, motor=False)
    hit_ts = [k[0] for k in dr.keys if any(abs(k[1] - p[0]) < 1e-6 and abs(k[2] - p[1]) < 1e-6 for p in pts[1:])]
    for th in hit_ts:
        if s("06-01") - 1 < th < t_end_rand:
            key(op.d["bumper"], ("location", 1), th - 0.06, 0.0); key(op.d["bumper"], ("location", 1), th, 0.014); key(op.d["bumper"], ("location", 1), th + 0.35, 0.0)
            ev(th, "bonk_soft", 0.35 if abs(th - t_hit) > 0.2 else 0.6)
    ev(t_hit, "click", 0.7)
    # バンパーの中のスイッチ（押された瞬間に光る小さな印）
    sw = sphere(glow_mat("switch", YELLOW, 0.0), (0, -0.155, 0.075), 0.012, parent=op.root)
    swm = sw.data.materials[0]
    emit_key(swm, t_hit - 0.05, 0.0); emit_key(swm, t_hit + 0.05, 18.0); emit_key(swm, t_hit + 0.9, 18.0); emit_key(swm, t_hit + 1.3, 0.0)
    # 06-09〜06-10：上からの絵。ぐるぐる（らせん）→ 壁ぞい → また進む（ここだけ早回し）。通った道を黄色い線で
    x0, y0, a0 = dr.pose(t_end_rand)
    ts = s("06-09") - 0.3
    spiral = [(x0, y0)]
    cx, cy = -0.4, 0.0
    spiral.append((cx, cy))
    for k in range(1, 50):
        a = k * 0.36; rr = 0.08 + 0.022 * k
        spiral.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    wall = [spiral[-1], (-2.35, 1.2), (-0.95, 1.25), (0.0, 1.95), (1.0, 1.95), (1.0, 1.4), (2.6, 1.4), (2.6, 0.2)]
    dr2 = plan.Drive(spiral + wall[1:], ts, v=1.1, turn=600)
    op.drive(dr2, ts, min(dr2.t1, e("06-10") + 1.5), motor=False)
    poly = [(k[1], k[2]) for k in dr2.keys]
    ln = line_path("oldpath", poly, YELLOW, 0.014, emit=3.0)
    L = [0.0]
    for i in range(1, len(poly)): L.append(L[-1] + math.dist(poly[i - 1], poly[i]))
    for k in dr2.keys:
        i = dr2.keys.index(k)
        ln.data.bevel_factor_end = L[i] / max(1e-6, L[-1]); ln.data.keyframe_insert("bevel_factor_end", frame=f(k[0]))
    show_between(ln, ts)
    if cut(cl, "S06a"):
        c, tg = cam_rig((-1.6, -3.6, 2.6), (0.0, 0.0, 0.0), 22)
        cam_move(c, tg, s("06-01") - 0.8, s("06-07"), (-1.7, -3.7, 2.7), (-1.2, -3.4, 2.4), (0.0, 0.0, 0.0), (0.0, -0.2, 0.0))
        con = tg.constraints.new('COPY_LOCATION'); con.target = op.root; con.influence = 0.45   # 先輩を半分だけ追う
    elif cut(cl, "S06b"):
        # ぶつかる所のアップ：先輩の横について行くカメラ（ぶつかる壁とバンパーが両方入る向き。部屋の中に収まる側を選ぶ）
        xh, yh, ah = dr.pose(t_hit)
        fwd = (math.sin(R(ah)), -math.cos(R(ah))); side = (math.cos(R(ah)), math.sin(R(ah)))
        off = None
        for sg in (-1, 1):      # 2:03 のちらつき：+側だと出入り口の外（黒）が映ったので、-側を先に
            o_ = (sg * side[0] * 0.55 - fwd[0] * 0.35, sg * side[1] * 0.55 - fwd[1] * 0.35, 0.3)
            if plan.ROOM[0] + 0.15 < xh + o_[0] < plan.ROOM[2] - 0.15 and plan.ROOM[1] + 0.15 < yh + o_[1] < plan.ROOM[3] - 0.15: off = o_; break
        off = off or (-fwd[0] * 0.6, -fwd[1] * 0.6, 0.35)
        c = cam_follow(op.root, off, 0.05, 30)
    else:
        c = cam_top((-0.2, 0.15, 7.6), 32)
        cam_top_move(c, s("06-09") - 0.8, e("06-10") + 0.8, (-0.2, 0.15, 7.6), (-0.2, 0.15, 7.1))
    track("senpai", op.root, 0.15)


# ======================================================================== S07〜S08：まるロボ、目の光を消して「ぶつかったら曲がる」
def blind_route():
    A = (-2.55, 1.12); B = (-2.87, 1.12); Cp = (-2.85, 1.42)     # v6：1 回目は 07-03 で歩き出して「ゴツン」に着く近さ（本物の歩きは約 0.26 m/秒）     # v6：2 回目のゴツンまでが短くなるよう、ソファの近くを歩く（本物の体は歩きがおそい）
    # 08：B→C のあと、早回しで部屋を回る（左手前のすみには行かない）。行かない並びを探す
    best = None
    for sd in range(1, 300):
        pts, hits = plan.bounce_path(Cp, 140, 22, sd, r=0.15)
        samp = []
        for i in range(len(pts) - 1):
            (xa, ya), (xb, yb) = pts[i], pts[i + 1]; n = max(1, int(math.dist((xa, ya), (xb, yb)) / 0.05))
            samp += [(xa + (xb - xa) * k / n, ya + (yb - ya) * k / n) for k in range(n)]
        if any(x < -2.0 and y < -1.5 for x, y in samp): continue
        center = sum(1 for x, y in samp if -1 < x < 1 and -1 < y < 1)
        if best is None or center > best[0]: best = (center, pts)
    return [A, B, Cp] + best[1][1:]


def b_blind(cl):
    room(); door_leaf(False)
    route = blind_route()
    A, B, Cp = route[0], route[1], route[2]
    m = Maru((A[0], A[1], 0), face=-90)
    m.at(s("07-01") - 1.0, loc=(A[0], A[1], 0), face=-90, look=0)
    m.hop(e("07-01") - 0.6, 0.1, 0.3)
    tg_off = w("07-02", "消しました")
    m.glow(tg_off - 0.1, 0.0, d=0.4, g0=0.9); m.rest(tg_off, dur=1.6)        # 一覧の rest（目の輪を細め、アンテナの光を落とす。音は power_down）
    m.eyes_closed(tg_off + 0.9, e("08-06") + 3.0)          # v3「目を閉じさせて」→ v6：本物の体は目の内側の輪を閉じた形に保つ（まばたきのチャンネル）
    th1 = w("07-03", "ゴツン") + 0.05
    m.walk(s("07-03") + 0.1, th1, (B[0] + 0.03, B[1], 0), turn=False)
    m.act(th1 + 0.01, "bonk", hold=0.55)        # ゴツン（着いてすぐ。ゆれを残したまま向きを変えはじめる）：一覧の bonk（はね返る。5本目で足した）
    ev(th1, "bonk", 0.8)
    th2 = w("07-04", "ゴツン") + 0.05
    m.walk(th1 + 0.85, th2, (Cp[0], Cp[1] - 0.02, 0), speeds="run")     # 向きを変えて「またまっすぐ……ゴツン」：2 回目は走ってぶつかる（歩きでは間に合わない）
    th2 = th2 + 0.26          # 走って着くのが声の「ゴツン」より 0.26 秒あと：ぶつかる絵と音は、着いた時に
    m.act(th2 + 0.01, "bonk")
    ev(th2, "bonk", 0.8)
    m.confused(s("07-05") + 0.2); m.mute(s("07-05"), e("07-05") + 0.5)     # ふらふら：一覧の confused（音は場面の「いたそうな音」だけにする）
    ev(e("07-05") - 2.6, "ouch", 0.8)      # v3：いたそうな音（ぐるぐるの吹き出しと一緒に。5本目 v2「いたそうなまるロボの SE」）
    # 08：上から。早回しで部屋じゅうを回り、通った道を黄色い線で
    ts = s("08-01") + 0.4; te = e("08-02") + 0.2
    rest = route[2:]
    Ls = [0.0]
    for i in range(1, len(rest)): Ls.append(Ls[-1] + math.dist(rest[i - 1], rest[i]))
    tot = Ls[-1]
    # 早回し：予定は本当の速さ（大きさ 0.26 なので約 0.26 m/秒）で歩かせ、ts〜te に入るように速く流す（route_fast）
    hits = m.route_fast(ts, te, [(Cp[0], Cp[1] - 0.1)] + list(rest[1:]))
    for th_ in hits: ev(th_, "bonk_soft", 0.18)
    full = [A, B] + rest
    ln = line_path("marupath", full, YELLOW, 0.016, emit=3.0)
    Lf = [0.0]
    for i in range(1, len(full)): Lf.append(Lf[-1] + math.dist(full[i - 1], full[i]))
    key(ln.data, "bevel_factor_end", s("07-03"), 0.0, "LINEAR") if False else None
    ln.data.bevel_factor_end = 0.0; ln.data.keyframe_insert("bevel_factor_end", frame=f(s("07-03") + 0.1))
    ln.data.bevel_factor_end = Lf[1] / Lf[-1]; ln.data.keyframe_insert("bevel_factor_end", frame=f(th1))
    ln.data.bevel_factor_end = Lf[2] / Lf[-1]; ln.data.keyframe_insert("bevel_factor_end", frame=f(th2))
    for i in range(3, len(full)):
        ln.data.bevel_factor_end = Lf[i] / Lf[-1]; ln.data.keyframe_insert("bevel_factor_end", frame=f(hits[i - 3]))     # まるロボが着く時刻に合わせて線がのびる
    for fc in ln.data.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    show_between(ln, s("08-01") - 0.5)
    corner = ring_marker((-2.45, -1.95), 0.42, YELLOW, w=0.02); show_between(corner, s("08-03") + 0.1); scale_pop(corner, s("08-03") + 0.1); ev(s("08-03") + 0.1, "pop", 0.5)
    m.at(te + 0.6, face=face_to(rest[-2], rest[-1]) + 30); m.confused(s("08-03") + 0.2)       # 「おや？」
    if cut(cl, "S07b"):     # v3：07-02 は正面のアップ（目の光が消えて、まぶたが閉じる。5本目 v2）
        # v6：壁までが近い（まるロボは 07-03 で歩き出す）ので、カメラは前の近くから広めのレンズで。壁の外に出ない
        c, tg = cam_rig((A[0] - 0.38, A[1] - 0.12, 0.2), (A[0], A[1], 0.17), 28)
        cam_move(c, tg, s("07-02") - 0.6, s("07-03") + 0.2, (A[0] - 0.40, A[1] - 0.13, 0.21), (A[0] - 0.34, A[1] - 0.10, 0.19), (A[0], A[1], 0.17), (A[0], A[1], 0.17)); dof(c, m.root, 2.8)
    elif cut(cl, "S07a") or cut(cl, "S07c"):
        c, tg = cam_rig((-0.6, -1.4, 1.0), (-2.2, 0.9, 0.2), 30)
        cam_move(c, tg, s("07-01") - 0.8, e("07-05") + 0.6, (-0.5, -1.5, 1.05), (-0.9, -1.0, 0.85), (-2.0, 0.9, 0.2), (-2.5, 1.1, 0.2)); dof(c, m.root, 5.0)
    else:
        c = cam_top((0.0, 0.0, 8.3), 30)
        cam_top_move(c, s("08-01") - 0.8, e("08-06") + 0.8, (0.0, 0.0, 8.3), (-0.4, -0.2, 7.4))
    track("maru", m.root, 0.42); track("corner", corner, 0.0)


# ======================================================================== S09〜S12：今の先輩。光の物差しで点を描く
MAP_PATH = [(-1.3, 0.95), (-0.4, 0.4), (0.3, 0.75), (1.9, 0.75), (2.45, 1.35), (2.5, 0.05), (0.8, -0.15), (0.8, -1.95), (-1.0, -2.1), (-2.2, -1.9), (-2.25, -0.9), (-2.25, 0.95), (-1.3, 0.95)]


def lidar_drives():
    """09〜12 の先輩の走り（一つの流れ）。09：真ん中から走り出し、壁の手前で曲がる → 10：止まる → 11〜12：部屋をひと回り"""
    t9 = e("09-01") + 0.1
    d9 = plan.Drive([(-1.6, 0.2), (-2.38, 0.2), (-2.38, 0.95), (-1.3, 0.95)], t9, v=0.55, turn=200)
    t11 = s("11-03") - 0.6
    cut_i = 6
    d11 = plan.Drive(MAP_PATH[:cut_i + 1], t11, v=0.32, turn=160)
    t12 = s("12-01") - 0.2
    d12 = plan.Drive(MAP_PATH[cut_i:], max(d11.t1, t12 - 6.0), v=1.6, turn=500, face0=d11.pose(d11.t1)[2])
    return d9, d11, d12


def full_map_points():
    """出来上がった地図の点（09〜12 と同じ走りで光を回したもの）。生まれた秒つき"""
    d9, d11, d12 = lidar_drives()
    # 光の届く距離を 2.6 m に（遠くの壁まで一度に出ず、近い所から順に点がふえる。ひと回りで地図の 99% がうまる）
    a = plan.scan_drive(d11, d11.t0, d11.t1, rot_per_s=1.0, rays=200, seed=2, maxd=2.6)
    b = plan.scan_drive(d12, d12.t0, d12.t1, rot_per_s=4.0, rays=200, seed=3, maxd=2.6)
    return a + b, d9, d11, d12


def b_lidar(cl):
    room(); door_leaf(False)
    sp = Sp(senpai_lidar((-1.6, 0.2), plan.face_deg(-1, 0)))
    pts, d9, d11, d12 = full_map_points()
    sp.place(s("09-01") - 1.0, -1.6, 0.2, plan.face_deg(-1, 0))
    sp.drive(d9); sp.spin(s("09-01") - 1, e("12-05") + 2, 0.6)
    sp.drive(d11); sp.drive(d12)          # v6：先輩の動きは先に全部決める（まるロボが乗る所を、実際の先輩の場所と向きから求めるため）
    xe, ye, ae = d12.pose(d12.t1); sp.place(e("12-05") + 2, xe, ye, ae)
    m = Maru((-1.15, -0.15, 0), face=face_to((-1.15, -0.15), (-1.6, 0.2)))
    m.at(s("09-01") - 1.0, loc=(-1.15, -0.15, 0)); m.at(s("09-02") + 0.1, face=face_to((-1.15, -0.15), (-2.38, 0.3)))
    m.surprise(s("09-02") + 0.1)       # 「あれ？　ぶつかる前に向きを変えた？」
    m.walk(e("09-02") + 0.1, e("09-03") + 1.2, (-1.5, 0.55, 0))      # v6：出発を近くに（本物の体の歩きは 0.26 m/秒）
    # 09-04 ふたが光る
    le = bpy.data.materials["lid_eye"]
    emit_key(le, w("09-04", "頭の上") - 0.1, 4.0); emit_key(le, w("09-04", "頭の上") + 0.3, 16.0); emit_key(le, e("09-04") + 0.6, 6.0)
    lr = ring_marker((0, 0), 0.075, YELLOW, w=0.004, z=0.0); lr.parent = sp.root; lr.location = (0, 0.035, sp.d["top_z"] + 0.03)
    show_between(lr, w("09-04", "丸いふた"), e("09-04") + 0.8); scale_pop(lr, w("09-04", "丸いふた")); ev(w("09-04", "丸いふた"), "pop", 0.4)
    # 10：まるロボが先輩の上にぴょん（先輩の子にして、上に乗せる）
    tj = w("10-01", "ぴょん")
    # v6（ユーザー「まるロボが上の位置にワープしている。ジャンプして乗る、そして向きを変える」）：
    #   床のまるロボが「ぴょん」で跳んで先輩の上に着き、脚で受け止め終わってから、着いた所・同じ向きのまま先輩に乗ったまるロボに入れかわる。
    #   入れかわったあとに、ふたの方へ向きを変えて、のぞき込む
    # v6：乗る所は「跳んで来た向きのまま、ふたの手前」。着いたら向きを変えずに、そのままふたをのぞき込める（本物の体は回るのがゆっくり）
    bpy.context.scene.frame_set(f(tj + 1.5)); spm = sp.root.matrix_world.copy()          # 入れかわるころの先輩（実際に置かれた場所と向き）
    Lw = spm @ Vector((0, 0.035, 0)); F0 = Vector((-1.5, 0.55, 0))                        # ふたの真ん中（世界）・跳ぶ前に立つ所
    u_ = (Lw - F0); u_.z = 0; u_.normalize()
    Pw = Lw - u_ * 0.11                                                                   # ふた（半径 0.052）から足が離れる近さ
    PL = spm.inverted() @ Pw; MRX, MRY = PL.x, PL.y                                       # 先輩の上の置き場所（先輩から見た所。半径 0.158 の内側）
    TOP = (Pw.x, Pw.y)
    sa_ = math.degrees(spm.to_euler()[2])
    fj = face_to((F0.x, F0.y), TOP)                                     # 跳ぶ向き＝着いたときの向き＝ふたの方
    m.at(tj - 1.0, face=fj)      # 立っていた所（09-04 のあいだは動かず、次のカットに入ってから向く）（ふたを隠さない左）から、跳ぶ先を向く
    m.jump(tj - 0.95, (-1.5, 0.55), TOP, z_to=sp.d["top_z"] + 0.004, apex=0.17)    # 見る→しゃがむ→「ぴょん」で蹴る（一覧の jump_to）
    mr = Maru((0, 0, 0), face=fj - sa_)      # 先輩の上（置き場所の親を先輩の子に）。床から跳んで来た向きのまま
    hp = mr.handle.parent; hp.parent = sp.root; hp.matrix_parent_inverse = Matrix.Identity(4); hp.location = (MRX, MRY, sp.d["top_z"] + 0.004)
    hide_key(m.root, s("09-01") - 1.5, False)
    TSW = [tj + 1.6]           # 入れかえの時刻（焼いたあとに、着いた本当の時刻 ＋ 受け止め終わりへ直す）

    def _swap(m=m, mr=mr, tj=tj):
        lands = [ts for ts, k in m.evs if k == "land" and ts is not None and ts > tj - 1.0]
        if lands: TSW[0] = lands[0] + 0.9
        hide_key(m.root, TSW[0], True); show_between(mr.root, TSW[0])
        if os.environ.get("DBG_SWAP"):
            for tt in (TSW[0] - 0.05, TSW[0] + 0.05):
                bpy.context.scene.frame_set(f(tt))
                print("DBGSWAP sp", round(math.degrees(sp.root.matrix_world.to_euler()[2]), 1), "fj", round(fj, 1), "sa", round(sa_, 1), "MR", round(MRX, 3), round(MRY, 3))
                for nm, h in (("床", m.handle), ("上", mr.handle)):
                    mw = h.torso.matrix_world; print("DBGSWAP", round(tt, 2), nm, tuple(round(v, 3) for v in mw.translation), round(math.degrees(mw.to_euler()[2]), 1))
    AFTER_BAKE.append(_swap)
    mr.peer(tj + 1.75, dur=2.2)        # 入れかわったら、そのまま「ふたをのぞきこみました」（一覧の peer）        # 「ふたをのぞきこみました」（一覧の peer）
    # ふたを透かす
    for nm in ("lid_glass", "lid_base", "lid_cap"):
        mm = [x for x in bpy.data.materials if x.name.startswith(nm)][0]
        b = mm.node_tree.nodes["Principled BSDF"]
        try: mm.blend_method = 'BLEND'
        except Exception: pass
        alpha_key(mm, w("10-02", "透かして"), 1.0); alpha_key(mm, w("10-02", "透かして") + 0.9, 0.12)
        alpha_key(mm, s("11-01"), 0.12); alpha_key(mm, s("11-01") + 1.0, 1.0)
    ev(w("10-02", "透かして"), "rise", 0.35)
    # 光の物差しの光（回る頭の前へ伸びる線）。長さは、その向きで壁までの距離（plan.ray）
    bm_ = beam(sp.d["spin"], 1.0, TEAL, 0.004, 8.0)
    tip = sphere(glow_mat("tip", TEAL, 12.0), (0, -1.0, 0), 0.02, parent=bm_)
    rps_slow = 0.35
    sp_obj = sp.d["spin"]
    ta, tb = s("10-03") - 0.4, s("11-01")
    key(sp_obj, ("rotation_euler", 2), s("09-01") - 1, (s("09-01") - 1) * 0.6 * 2 * math.pi, "LINEAR")
    key(sp_obj, ("rotation_euler", 2), ta, ta * 0.6 * 2 * math.pi, "LINEAR")
    key(sp_obj, ("rotation_euler", 2), tb, ta * 0.6 * 2 * math.pi + (tb - ta) * rps_slow * 2 * math.pi, "LINEAR")
    key(sp_obj, ("rotation_euler", 2), e("12-05") + 2, ta * 0.6 * 2 * math.pi + (tb - ta) * rps_slow * 2 * math.pi + (e("12-05") + 2 - tb) * 1.2 * 2 * math.pi, "LINEAR")
    S_ = plan.segments(); xs, ys, angs = -1.3, 0.95, d9.pose(d9.t1)[2]
    t = ta
    while t < tb:
        spin_a = ta * 0.6 * 2 * math.pi + (t - ta) * rps_slow * 2 * math.pi
        wa = R(angs) + spin_a                    # 頭の前（-y）の、世界での向き（前＝-y を 0 とする角度）
        dirx, diry = math.sin(wa), -math.cos(wa)
        h = plan.ray(xs + dirx * 0.0, ys + diry * 0.0, math.atan2(diry, dirx), S_)
        L = (h[0] if h else 3.0)
        # v4「レーザーみたいなのもまるロボやソファに当たってるときは貫通させないで」：
        #   乗っているまるロボの足（先輩の上の円）と、ソファの形（本当は座面の下を通るが、絵では突きぬけて見える）で止める
        if t > tj + 0.5: L = min(L, _ray_circle(xs, ys, dirx, diry, *_loc2world(xs, ys, R(angs), MRX, MRY), 0.075))
        L = min(L, _ray_rect(xs, ys, dirx, diry, plan.FURN["sofa"][:4]))
        key(bm_, ("scale", 1), t, L, "LINEAR"); t += 1 / FPS * 2
    show_between(bm_, s("10-03") - 0.3, s("11-01") + 0.2)
    # 10-04：光が出て、返ってくる（光の玉が行って戻る）
    pulse = sphere(glow_mat("pulse", "#FFFFFF", 20.0), (0, 0, 0), 0.03, parent=bm_)
    for k in range(2):
        tp = w("10-04", "返ってきた") - 1.0 + k * 1.4
        key(pulse, ("location", 1), tp, 0.0, "LINEAR"); key(pulse, ("location", 1), tp + 0.5, -1.0, "LINEAR"); key(pulse, ("location", 1), tp + 1.0, 0.0, "LINEAR")
    show_between(pulse, w("10-04", "返ってきた") - 1.0, w("10-04", "返ってきた") + 1.9)
    # 10-05：速く回ると、まわり全部（光の円盤）
    fan = cyl(flat_mat("fan", TEAL, 0.0), (0, 0, 0), 1.0, 0.002, parent=sp.d["spin"], verts=64)
    fm = fan.data.materials[0]
    fn = fm.node_tree.nodes["Emission"]
    mix = fm.node_tree.nodes.new("ShaderNodeMixShader"); tr = fm.node_tree.nodes.new("ShaderNodeBsdfTransparent")
    out = fm.node_tree.nodes["Material Output"]
    fm.node_tree.links.new(tr.outputs[0], mix.inputs[1]); fm.node_tree.links.new(fn.outputs[0], mix.inputs[2]); fm.node_tree.links.new(mix.outputs[0], out.inputs[0])
    mix.inputs[0].default_value = 0.0; mix.inputs[0].keyframe_insert("default_value", frame=f(w("10-05", "何回も") - 0.2))
    mix.inputs[0].default_value = 0.12; mix.inputs[0].keyframe_insert("default_value", frame=f(w("10-05", "何回も") + 0.5))
    mix.inputs[0].default_value = 0.12; mix.inputs[0].keyframe_insert("default_value", frame=f(e("10-05") + 0.2))
    mix.inputs[0].default_value = 0.0; mix.inputs[0].keyframe_insert("default_value", frame=f(e("10-05") + 0.8))
    fn.inputs["Strength"].default_value = 2.0
    fan.scale = (2.4, 2.4, 1); fan.visible_shadow = False
    show_between(fan, w("10-05", "何回も") - 0.3, e("10-05") + 1.0); ev(w("10-05", "何回も"), "whoosh", 0.4)
    ring1 = [(round(h_[1][0], 3), round(h_[1][1], 3), w("10-05", "何回も") + 0.3) for h_ in [plan.ray(xs, ys, R(a_), S_) for a_ in range(0, 360, 2)] if h_]
    rp, rm = point_cloud("ring1", ring1, life=e("10-05") + 0.6 - w("10-05", "何回も") - 0.3, t_offset=CLOCK["T0"])
    # 11：明かりを落とす → 走りながら点を置く（まるロボは上に乗ったまま）
    lights_off(s("11-02") + 0.3, s("11-02") + 2.4, sky=DARK_SKY, world_s=DARK_W)
    pc, pm = point_cloud("map", pts, t_offset=CLOCK["T0"])
    mr.at(s("11-07") - 0.2, look=-25); mr.awe(s("11-07"), dur=3.2, pitch=-10)     # 「すっかり見入っている」（一覧の awe。床の点を見下ろして）
    # 11-05「ここは壁。ここは、ソファの足」（点の上に輪）
    WPT = (0.82, plan.ROOM[3] - 0.02)          # v6（ユーザー「ここは壁の時に本棚に丸つけてる」）：前は左の壁の前（本棚に当たった点）→ 奥の壁（ソファと机のあいだ）の点に
    rw = ring_marker(WPT, 0.22, YELLOW, w=0.012, z=plan.LIDAR_Z); rw.rotation_euler = (R(90), 0, 0)
    show_between(rw, w("11-05", "壁"), e("11-05") + 0.8); scale_pop(rw, w("11-05", "壁")); ev(w("11-05", "壁"), "pop", 0.4)
    lx, ly = plan.legs("sofa")[0]
    track("wallpt", empty((WPT[0], WPT[1], plan.LIDAR_Z))); track("sofaleg", empty((lx, ly, plan.LIDAR_Z)))   # 2D の輪をつける所
    rs = ring_marker((lx, ly), 0.12, YELLOW, w=0.01, z=plan.LIDAR_Z)
    show_between(rs, w("11-05", "ソファ"), e("11-05") + 0.8); scale_pop(rs, w("11-05", "ソファ")); ev(w("11-05", "ソファ"), "pop", 0.4)
    # 12-03〜12-04：スマホの地図を上から重ねる（同じ間取りから描いた絵なので、ぴったり重なる）
    bx0, by0, bx1, by1 = plan.ROOM[0] - 0.15, plan.ROOM[1] - 0.15, plan.ROOM[2] + 0.15, plan.ROOM[3] + 0.15   # map_tex.world_box と同じ
    mpl = plane(img_mat("mapplane", tex("map_plane.png"), emit=2.0), ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.9), (bx1 - bx0, by1 - by0))
    mpm = mpl.data.materials[0]; mpm.blend_method = 'BLEND'
    nt = mpm.node_tree; b = nt.nodes["Principled BSDF"]; tx_ = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; nt.links.new(tx_.outputs["Alpha"], mul.inputs[0]); nt.links.new(mul.outputs[0], b.inputs["Alpha"])
    mul.inputs[1].default_value = 0.0; mul.inputs[1].keyframe_insert("default_value", frame=f(w("12-03", "比べて") - 0.4))
    mul.inputs[1].default_value = 0.85; mul.inputs[1].keyframe_insert("default_value", frame=f(w("12-03", "比べて") + 0.3))
    key(mpl, ("location", 2), w("12-03", "比べて"), 0.9); key(mpl, ("location", 2), s("12-04") - 0.1, plan.LIDAR_Z + 0.004)
    emit_key(mpm, s("12-04") - 0.05, 2.0); emit_key(mpm, s("12-04") + 0.25, 7.0); emit_key(mpm, s("12-04") + 1.0, 2.0)
    show_between(mpl, w("12-03", "比べて") - 0.5); ev(s("12-04"), "snap", 0.6)
    # カメラ
    if cut(cl, "S09a"):
        c, tg = cam_rig((-0.4, -1.6, 0.8), (-2.0, 0.4, 0.1), 30)
        cam_move(c, tg, s("09-01") - 0.8, e("09-03"), (-0.3, -1.7, 0.85), (-0.8, -1.2, 0.7), (-1.9, 0.3, 0.1), (-2.2, 0.7, 0.1))
        cam_move(c, tg, e("09-03"), e("09-04") + 0.6, (-0.8, -1.2, 0.7), (-1.05, 0.35, 0.42), (-2.2, 0.7, 0.1), (-1.3, 0.95, 0.12), 30, 44)
    elif cut(cl, "S10a"):
        c, tg = cam_rig((-0.7, 0.2, 0.55), (-1.3, 0.95, 0.15), 34)
        # v6：跳び乗るまでは今の側から。乗ったら、ふたの向こう側（ソファの側）へ回って、ふたをのぞき込むまるロボの顔を見せる（背中でふたを隠さない）
        tj_ = w("10-01", "ぴょん")
        cam_move(c, tg, s("10-01") - 0.8, tj_ + 1.0, (-0.65, 0.15, 0.55), (-0.72, 0.32, 0.52), (-1.3, 0.9, 0.18), (-1.33, 0.86, 0.18), 34, 34)
        cam_move(c, tg, tj_ + 1.0, e("10-02") + 0.8, (-0.72, 0.32, 0.52), (-0.74, 1.45, 0.5), (-1.33, 0.86, 0.18), (-1.3, 0.92, 0.12), 34, 42)
        cam_move(c, tg, e("10-02") + 0.8, e("10-04"), (-0.74, 1.45, 0.5), (0.2, -0.6, 1.4), (-1.3, 0.92, 0.12), (-1.5, 1.0, 0.0), 42, 24)
        cam_move(c, tg, e("10-04"), e("10-05") + 0.6, (0.2, -0.6, 1.4), (0.4, -1.4, 2.2), (-1.5, 1.0, 0.0), (-1.2, 0.6, 0.0), 24, 22)
    elif cut(cl, "S11a"):
        c, tg = cam_rig((1.6, -3.4, 3.4), (-0.6, 0.6, 0.0), 24)
        cam_move(c, tg, s("11-01") - 0.8, e("11-07") + 0.6, (1.7, -3.5, 3.5), (0.6, -3.6, 3.9), (-0.6, 0.6, 0.0), (-0.3, 0.2, 0.0))
    else:
        c = cam_top((0.1, 0.0, 8.0), 30)
        cam_top_move(c, s("12-01") - 0.8, e("12-05") + 0.8, (0.1, -0.1, 8.0), (0.0, 0.0, 8.6))
    track("senpai", sp.root, 0.15); track("maru", mr.root, 0.5)


# ======================================================================== S13〜S15：暗い地図。自分はどこ？ → 「だいたい」から「ぴったり」へ
SP13 = (-1.62, -0.2)


START_SE_FROM[0] = s("18-01")    # 先輩ごとの動き出しの音は、カメラの先輩が出てから
DARK_SKY, DARK_W = 0.06, 0.035   # 明かりを落とした部屋（v4「部屋の暗さ若干明るく」「明るくしすぎなくていい」：0.03・0.02 から少しだけ。点の線は目立つまま）


def dark_map(split_x=0.3):
    """暗くした部屋と、出来上がった地図（右側＝x > split_x は、13-08 で「まだ描いていない所」として消せるよう別にする）"""
    room(); door_leaf(False)
    lights_off(CLOCK["T0"] - 2.0, CLOCK["T0"] - 1.0, sky=DARK_SKY, world_s=DARK_W)
    pts = [(x, y, -10.0) for x, y in plan.map_points()]
    left = [p for p in pts if p[0] <= split_x]; right = [p for p in pts if p[0] > split_x]
    a, am = point_cloud("mapL", left, pop=0.0, t_offset=CLOCK["T0"])
    b, bm = point_cloud("mapR", right, pop=0.0, t_offset=CLOCK["T0"])
    return am, bm, right


def _loc2world(x, y, a, lx, ly):
    return (x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a))


def _ray_circle(ox, oy, dx, dy, cx, cy, r):
    """(ox, oy) から (dx, dy) 向きの線が円に当たるまでの長さ（当たらなければ大きな数）"""
    fx, fy = ox - cx, oy - cy; b = fx * dx + fy * dy; c = fx * fx + fy * fy - r * r; d = b * b - c
    if d < 0: return 99.0
    t1 = -b - math.sqrt(d)
    return t1 if t1 > 0 else 99.0


def _ray_rect(ox, oy, dx, dy, rc):
    x0, y0, x1, y1 = rc; tn, tf = -1e9, 1e9
    for o, d, lo, hi in ((ox, dx, x0, x1), (oy, dy, y0, y1)):
        if abs(d) < 1e-9:
            if not (lo <= o <= hi): return 99.0
            continue
        a_, b_ = (lo - o) / d, (hi - o) / d
        tn, tf = max(tn, min(a_, b_)), min(tf, max(a_, b_))
    return tn if (tn <= tf and tn > 0) else 99.0


def pts_color(m, t, col):
    """点の色を t で変える（v3：1 周目＝青緑・2 周目＝オレンジ）"""
    em = [x for x in m.node_tree.nodes if x.type == 'EMISSION'][0]
    em.inputs["Color"].default_value = srgb(col); em.inputs["Color"].keyframe_insert("default_value", frame=f(t))


def pts_glow(m, t, v):
    n = [x for x in m.node_tree.nodes if x.type == 'MATH' and x.operation == 'MULTIPLY_ADD'][0]
    n.inputs[2].default_value = v; n.inputs[2].keyframe_insert("default_value", frame=f(t))


def b_dark(cl):
    am, bm, right = dark_map()
    sp = Sp(senpai_lidar(SP13, plan.face_deg(-1, 0))); sp.spin(CLOCK["T0"] - 2, e("15-10") + 3, 0.6)
    m = Maru((-1.25, -0.62, 0), face=face_to((-1.25, -0.62), SP13), glow=1.2)
    # 13-02〜13-03：光の線を 1 本、本棚まで
    #   v3（5本目 v2「ロボット掃除機が消えて『ここ』が分からなくなるのをうまく表現して」）：先輩・光の線・先の点を 1 つの組（unit）にする。
    #   「ここ」で先輩が消え、点線の輪（どこにいるか分からない先輩）と線と点が、組のまま当てずっぽうに動き回る（点の場所が決まらない）。
    #   13-05 で先輩が戻ると、組も本当の場所に戻って、点がぴたっと置かれる
    unit = empty((SP13[0], SP13[1], 0.0))
    bp = empty((-0.035, 0.0, 0.127)); bp.parent = unit
    b1 = beam(bp, 1.0, TEAL, 0.004, 9.0); b1.rotation_euler = (0, 0, R(plan.face_deg(-1, 0)))
    h = plan.ray(SP13[0], SP13[1], math.pi, plan.segments()); L1 = h[0]
    key(b1, ("scale", 1), w("13-02", "どの向き") - 0.05, 0.01); key(b1, ("scale", 1), w("13-02", "どの向き") + 0.6, L1)
    tq = w("13-04", "「ここ」"); tback = s("13-05") + 0.3
    show_between(b1, w("13-02", "どの向き") - 0.1, tback + 1.2); ev(w("13-02", "どの向き"), "whoosh", 0.3)
    hit = sphere(glow_mat("hit13", TEAL, 14.0), (h[1][0] - SP13[0], h[1][1] - SP13[1], plan.LIDAR_Z), 0.03, parent=unit); show_between(hit, w("13-02", "どの向き") + 0.6, e("13-05") + 0.5)
    anchor13 = empty(((SP13[0] + h[1][0]) / 2, SP13[1], plan.LIDAR_Z + 0.12)); track("onemeter", anchor13)
    hide_key(sp.root, s("13-01") - 1.5, False); hide_key(sp.root, tq, True); hide_key(sp.root, tback, False)
    # どこにいるか分からない先輩：白い点線の輪（床の上）
    ghost = dashed_ring(unit, name="ghost13")
    show_between(ghost, tq, tback); scale_pop(ghost, tq, d=0.25); ev(tq, "whoosh", 0.3)
    rnd = [(0.32, 0.18, 18), (-0.22, 0.34, -22), (0.12, -0.28, 12), (-0.3, -0.08, -15), (0.26, 0.3, 25)]
    key(unit, "location", tq, (SP13[0], SP13[1], 0)); key(unit, ("rotation_euler", 2), tq, 0.0)
    for k, (dx, dy, da) in enumerate(rnd):
        tk = tq + 0.35 + k * (tback - 0.5 - tq - 0.35) / (len(rnd) - 1)
        key(unit, "location", tk, (SP13[0] + dx, SP13[1] + dy, 0)); key(unit, ("rotation_euler", 2), tk, R(da))
    key(unit, "location", tback, (SP13[0], SP13[1], 0)); key(unit, ("rotation_euler", 2), tback, 0.0); ev(tback + 0.1, "snap", 0.4)
    gh_t = empty((0, 0, 0.1)); gh_t.parent = unit
    track("ghost", gh_t, 0.0); track("senpai", sp.root, 0.18, box=True)
    # 13-07 地図が光る、13-08 右の半分は「まだ描いていない」→ 消える
    pts_glow(am, w("13-07", "地図") - 0.05, 2.2); pts_glow(am, w("13-07", "地図") + 0.3, 6.0); pts_glow(am, e("13-07") + 0.2, 2.2)
    pts_glow(bm, w("13-07", "地図") - 0.05, 2.2); pts_glow(bm, w("13-07", "地図") + 0.3, 6.0); pts_glow(bm, e("13-07") + 0.2, 2.2)
    pts_glow(bm, w("13-08", "途中") - 0.2, 2.2); pts_glow(bm, w("13-08", "途中") + 0.8, 0.0)
    # 14：まるロボ、こんがらがる
    fc = face_to((-1.25, -0.62), (-0.75, -1.4))            # 14：カメラの方（見ている人の方）を向いて、こんがらがる
    m.at(s("14-01") - 0.5, look=10, face=fc)
    for k in range(4):
        m.at(s("14-01") + 0.6 + k * 1.7, face=fc + (25 if k % 2 else -25))
    m.at(e("14-05") + 0.3, face=face_to((-1.25, -0.62), SP13))
    m.glow(s("14-04"), 2.4, 0.3, g0=1.2); m.confused(s("14-04") + 0.2); m.glow(e("14-04") + 0.4, 1.2)
    # 15：車輪を数える（アップ）→ 「だいたい」の丸 → いま見えている形（白い点）を地図と重ねる → 「ぴったり」
    t_go = w("15-02", "車輪") - 0.2
    sp.place(t_go - 0.5, SP13[0], SP13[1], plan.face_deg(-1, 0))
    d15 = plan.Drive([SP13, (-0.75, -0.2)], t_go, v=0.11, face0=plan.face_deg(-1, 0), turn=120)
    sp.drive(d15, wheel_scale=1.0)
    PX = (-0.75, -0.2)
    # 「だいたい」の丸（本当の場所から少しずれた所に、大きくぼんやり）
    off = (0.16, 0.12)
    disc = cyl(flat_mat("guess", YELLOW, 0.0), (PX[0] + off[0], PX[1] + off[1], 0.02), 0.45, 0.004, verts=64)
    gm = disc.data.materials[0]; gn = gm.node_tree.nodes["Emission"]
    mix = gm.node_tree.nodes.new("ShaderNodeMixShader"); tr = gm.node_tree.nodes.new("ShaderNodeBsdfTransparent"); out = gm.node_tree.nodes["Material Output"]
    gm.node_tree.links.new(tr.outputs[0], mix.inputs[1]); gm.node_tree.links.new(gn.outputs[0], mix.inputs[2]); gm.node_tree.links.new(mix.outputs[0], out.inputs[0])
    gn.inputs["Strength"].default_value = 1.2; disc.visible_shadow = False
    def dalpha(t, a): mix.inputs[0].default_value = a; mix.inputs[0].keyframe_insert("default_value", frame=f(t))
    td = w("15-04", "だいたいここ"); dalpha(td - 0.2, 0.0); dalpha(td + 0.3, 0.3)
    scale_pop(disc, td); ev(td, "pop", 0.5)
    for k in range(4):   # 15-05：ふらふらとずれる
        key(disc, "location", s("15-05") + 0.3 + k * 0.9, (PX[0] + off[0] + 0.06 * math.sin(k * 2.1), PX[1] + off[1] + 0.06 * math.cos(k * 1.7), 0.02))
    track("disc", disc, 0.0)
    # いま見えている形（白い点）：思っている場所（ずれ）で置いた点 → 15-07 で動いて、地図の点に重なる
    S_ = plan.segments(); cur = []
    for a_ in range(0, 360, 2):
        hh = plan.ray(PX[0], PX[1], R(a_), S_)
        if hh and math.dist(hh[1], PX) < 2.2: cur.append((hh[1][0], hh[1][1], 0.0))
    wpt = empty((PX[0], PX[1], 0.0))
    cpt, cm = point_cloud("cur", [(x - PX[0], y - PX[1], t) for x, y, t in cur], col=WHITE_PT, radius=0.02, z=plan.LIDAR_Z + 0.01, pop=0.0, base=3.0, t_offset=1e5)
    cpt.parent = wpt
    tw = w("15-06", "いま見えている")
    show_between(cpt, tw); ev(tw + 0.2, "pop", 0.4)
    # v3（5本目 v2「壁の線と、ロボット掃除機が動かして位置を合わせてるのが分かるように」）：
    #   白い形と一緒に、「思っている自分の場所」の点線の輪が動く → 地図の壁にぴったり重なると、輪が本当の先輩に重なって消える
    ring15 = dashed_ring(wpt, name="guess15")
    show_between(ring15, tw, w("15-08", "ぴったり") + 0.35); scale_pop(ring15, tw, d=0.25)
    top = max(cur, key=lambda q: q[1]); an_c = empty((top[0] - PX[0], top[1] - PX[1], 0.05)); an_c.parent = wpt
    track("curshape", an_c, 0.0); track("guess15", wpt, 0.05)
    th_err = 9.0
    key(wpt, "location", tw, (PX[0] + off[0], PX[1] + off[1], 0)); key(wpt, ("rotation_euler", 2), tw, R(th_err))
    t7 = s("15-07") + 0.3
    seq = [(off[0] * 0.3, -0.12, 4.0), (-0.1, 0.05, -5.0), (0.05, 0.03, 2.0), (0.0, 0.0, 0.0)]
    for k, (ox, oy, oa) in enumerate(seq):
        tt = t7 + (k + 1) * (w("15-08", "ぴったり") - t7) / len(seq)
        key(wpt, "location", tt, (PX[0] + ox, PX[1] + oy, 0)); key(wpt, ("rotation_euler", 2), tt, R(oa))
    tp = w("15-08", "ぴったり")
    ev(tp, "snap", 0.6); pts_glow(am, tp - 0.05, 2.2); pts_glow(am, tp + 0.2, 7.0); pts_glow(am, tp + 0.9, 2.2)
    key(disc, "location", tp - 0.3, (PX[0] + off[0] * 0.2, PX[1] + off[1] * 0.2, 0.02)); key(disc, "location", tp + 0.2, (PX[0], PX[1], 0.02))
    key(disc, "scale", tp - 0.3, (1, 1, 1)); key(disc, "scale", tp + 0.2, (0.12, 0.12, 1))
    # 15-09：白い点を消して、まだ描いていなかった右側の点が生まれる（地図を広げる）
    hide_key(cpt, w("15-09", "新しい点"), True)
    tg9 = w("15-09", "新しい点")
    newp = [(x, y, tg9 + 0.2 + 3.5 * (x - 0.3) / 2.7) for x, y, _ in right]
    np_, nm = point_cloud("grow", newp, t_offset=CLOCK["T0"]); ev(tg9 + 0.2, "rise", 0.35)
    # 15-10：また少し進んで、だいたい → ぴったり（丸が大きく → 小さく、を 2 回）
    d15b = plan.Drive([PX, (0.2, -0.45)], s("15-10") + 0.2, v=0.2)
    sp.drive(d15b)
    for k in range(2):
        tk = s("15-10") + 1.0 + k * 3.0
        xk, yk, _ = d15b.pose(tk)
        key(disc, "location", tk, (xk + 0.1, yk + 0.08, 0.02)); key(disc, "scale", tk, (0.9, 0.9, 1)); ev(tk, "pop", 0.25)
        key(disc, "location", tk + 1.3, (xk, yk, 0.02)); key(disc, "scale", tk + 1.3, (0.12, 0.12, 1)); ev(tk + 1.3, "snap", 0.3)
    dalpha(e("15-10") + 0.3, 0.35); dalpha(e("15-10") + 0.9, 0.0)
    m.walk(s("15-02") - 0.5, s("15-02") + 1.4, (-1.15, 0.3, 0)); m.at(s("15-04"), face=face_to((-1.15, 0.3), PX)); m.at(s("15-08") + 0.5, look=15)
    m.at(tp + 0.2, look=20); m.at(tp + 0.6, look=0); m.at(tp + 1.0, look=20); m.at(tp + 1.4, look=-15)     # 本物の体：見上げは目と胴（予定の look）
    if cut(cl, "S13a"):
        c, tg = cam_rig((-0.6, -2.4, 1.5), (-2.0, -0.2, 0.1), 28)
        cam_move(c, tg, s("13-01") - 0.8, e("13-05"), (-0.5, -2.5, 1.55), (-1.2, -2.1, 1.25), (-2.0, -0.2, 0.1), (-2.1, -0.2, 0.15))
        cam_move(c, tg, e("13-05"), e("13-08") + 0.8, (-1.2, -2.1, 1.25), (1.2, -3.9, 4.0), (-2.1, -0.2, 0.15), (-0.2, 0.2, 0.0), 28, 24)
    elif cut(cl, "S14a"):
        c, tg = cam_rig((-0.7, -1.35, 0.42), (-1.3, -0.55, 0.3), 40)
        cam_move(c, tg, s("14-01") - 0.8, e("14-05") + 0.6, (-0.62, -1.55, 0.46), (-0.72, -1.38, 0.42), (-1.27, -0.6, 0.25), (-1.25, -0.62, 0.25)); dof(c, m.root, 2.8)      # v6：本物の体は目が低いので、少し引いて字幕に目がかからないように
    elif cut(cl, "S15b"):
        c, tg = cam_rig((-1.5, -0.85, 0.1), (-1.3, -0.2, 0.03), 40)
        con = tg.constraints.new('COPY_LOCATION'); con.target = sp.root
        cam_move(c, tg, s("15-02") - 0.5, e("15-03") + 0.6, (-1.55, -0.85, 0.1), (-0.95, -0.85, 0.1))
    else:
        c, tg = cam_rig((0.6, -3.4, 3.3), (-0.6, -0.2, 0.0), 26)
        if cut(cl, "S15a"):
            cam_move(c, tg, s("15-01") - 0.8, e("15-01") + 0.6, (0.7, -3.5, 3.4), (0.5, -3.3, 3.2), (-0.8, -0.2, 0.0), (-0.9, -0.2, 0.0))
        else:
            cam_move(c, tg, s("15-04") - 0.8, e("15-08"), (0.3, -2.6, 2.4), (0.0, -2.2, 2.1), (-0.7, -0.15, 0.0), (-0.75, -0.2, 0.0))
            cam_move(c, tg, e("15-08"), e("15-10") + 0.8, (0.0, -2.2, 2.1), (1.0, -3.4, 3.4), (-0.75, -0.2, 0.0), (0.0, 0.1, 0.0))
    track("maru", m.root, 0.42)


# ======================================================================== S16〜S17：じゅうたんで、すべる → 一周して戻ると、ぴたっ
DRIFT = dict(c=(-0.2, 0.0), th=7.0, d=(0.22, -0.12))


def rug_drive():
    t0 = e("16-02") + 0.2
    P = plan.RUG_PATH
    # じゅうたんの上はゆっくり（すべる）。前後はふつう
    i_on = 2; i_off = 3   # (−0.2, 0.2) → (−1.9, −0.5) の区間がじゅうたん
    d1 = plan.Drive(P[:i_on + 1], t0, v=0.3)
    d2 = plan.Drive(P[i_on:i_off + 1], d1.t1, v=0.09, face0=d1.pose(d1.t1)[2])
    d3 = plan.Drive(P[i_off:], d2.t1, v=0.3, face0=d2.pose(d2.t1)[2])
    return d1, d2, d3


def drift_at(t, d2):
    k = 0.0 if t <= d2.t0 else (1.0 if t >= d2.t1 else (t - d2.t0) / (d2.t1 - d2.t0))
    return k


def drift_points(dr, t0, t1, d2, rot=1.0, rays=200, seed=5):
    """思っている場所で置いた点（じゅうたんでずれたぶん、地図全体が回って動いている）"""
    S_ = plan.segments(); out = []
    c = DRIFT["c"]; th = DRIFT["th"]; dx, dy = DRIFT["d"]
    raw = plan.scan_drive(dr, t0, t1, rot_per_s=rot, rays=rays, seed=seed)
    for x, y, t in raw:
        k = drift_at(t, d2)
        if k <= 0: continue
        a = math.radians(th * k); ca, sa = math.cos(a), math.sin(a)
        rx, ry = x - c[0], y - c[1]
        out.append((round(c[0] + rx * ca - ry * sa + dx * k, 3), round(c[1] + rx * sa + ry * ca + dy * k, 3), t))
    return out


def b_rug(cl):
    room(rug=True); door_leaf(False)
    rug = RUGOBJ[-1]
    tr_ = w("16-02", "じゅうたん")
    # v4「じゅうたんはまるロボが転がして広げる感じに」→ v6（本物の歩きは約 0.26 m/秒）：巻いたじゅうたんを右はしに置き、
    #   右にいるまるロボが数歩（0.4 m）押すと、巻きはそのまま左へ転がって広がる（広がった所だけ見せる・巻きは残りの長さで細くなる）
    rx0, ry0, rx1, ry1 = plan.RUG; yc_ = (ry0 + ry1) / 2; LW = rx1 - rx0; TH = 0.024; PUSH = 0.4; MG = 0.17
    Ta = tr_ + 0.6                       # 押し終わり（まるロボが着く時刻）
    tp0, tp1 = Ta - 1.9, Ta + 3.0        # 巻きが動き出す・左はしに着く
    rmat = bpy.data.materials["rug"]
    roll = empty((0, 0, 0)); rcyl = cyl(rmat, (0, 0, 0), 1.0, ry1 - ry0 + 0.02, rot=(R(90), 0, 0), parent=roll, verts=48)
    for sy in (-1, 1):     # 両はしだけ、ふちの色（巻いた渦の面）
        cyl(mat("rugedge_r", "#E9D8C4", rough=0.95), (0, sy * ((ry1 - ry0) / 2 + 0.018), 0), 1.0, 0.03, rot=(R(90), 0, 0), parent=roll, verts=48)
    rad = lambda xr: math.sqrt(0.0035 ** 2 + TH * max(0.0, xr - rx0) / math.pi)
    def xr_at(t):            # 巻きの右はし（広がった所の左はし）の x
        if t <= tp0: return rx1
        if t <= Ta: u = (t - tp0) / (Ta - tp0); return rx1 - PUSH * u * u * (3 - 2 * u) if u < 1 else rx1 - PUSH
        u = min(1.0, (t - Ta) / (tp1 - Ta))      # 最後のひと押しで勢いがつき、だんだん止まる
        return rx1 - PUSH - (LW - PUSH) * (1 - (1 - u) ** 2)
    ang = 0.0; nst = 48; prev = rx1
    for i in range(nst + 1):
        tt = tp0 + (tp1 - tp0) * i / nst; xr = xr_at(tt); r_ = rad(xr)
        ang += (prev - xr) / max(r_, 0.02); prev = xr
        key(roll, "location", tt, (xr - r_, yc_, r_), "LINEAR"); key(roll, "scale", tt, (r_, 1, r_), "LINEAR"); key(roll, ("rotation_euler", 1), tt, -ang, "LINEAR")
        key(rug, "location", tt, (rx1 - (rx1 - xr) / 2 - 0.0001, yc_, 0), "LINEAR"); key(rug, "scale", tt, (max(0.001, (rx1 - xr) / LW), 1, 1), "LINEAR")
    show_between(roll, CLOCK["T0"] - 1.0, tp1 + 0.05)
    ev(Ta + 0.1, "whoosh", 0.3)
    sp = Sp(senpai_lidar((0.3, 1.95), 0)); sp.spin(CLOCK["T0"] - 2, e("17-11") + 3, 0.6)
    d1, d2, d3 = rug_drive()
    sp.place(s("16-01") - 1.5, 0.3, 1.95, plan.face_deg(0, -1))
    sp.drive(d1); sp.drive(d2, wheel_scale=4.0); sp.drive(d3)
    xe, ye, ae = d3.pose(d3.t1); sp.place(e("17-11") + 3, xe, ye, ae)
    MP16 = (rx1 + MG - PUSH, yc_)       # 押したあと、そのまま立って見る所
    m = Maru((rx1 + MG, yc_, 0), face=plan.face_deg(-1, 0))
    m.walk(tp0, Ta, (MP16[0], MP16[1], 0))                       # 巻きを押して数歩
    if cut(cl, "S16b"): hide_key(m.root, CLOCK["T0"] - 1.0, True)     # v6：車輪の寄りでは、本物の大きい体がカメラの前を横切るので隠す
    m.at(s("16-03") + 1.4, face=face_to(MP16, (-0.6, 0.0)))
    m.at(s("16-03") + 2.6, face=face_to(MP16, (-1.0, -0.2)))
    m.confused(s("16-06") + 0.1)       # 「首をかしげています」
    m.walk(s("17-01") + 0.2, e("17-02"), (0.9, 0.9, 0))      # MP16 から 1.4 m（本物の体の歩きで約 6 秒。先輩が一周するあいだに歩き、17-02 の終わりに着く）
    # 16-05 から暗い地図：もとの地図（青緑）＋ ずれて置かれた新しい点（青緑）→ 壁が二重
    tdark = s("16-05") - 0.25
    # v6（ユーザー「ここのシーンの切り替わりのときに別のシーンみたいなのが一瞬うつる」）：車輪の寄り（S16b）は、次の真上の絵へ
    #   重ねて切りかえる間も明るいまま・地図の点なし（前は寄りの絵が先に暗くなり、地図の点の線が横切っていた）
    if not cut(cl, "S16b"): lights_off(tdark, tdark + 0.25, sky=DARK_SKY, world_s=DARK_W)
    base = [(x, y, -10.0) for x, y in plan.map_points()]
    first = [p for p in base if p[1] > 2.3 and -1.0 < p[0] < 1.4]
    restb = [p for p in base if not (p[1] > 2.3 and -1.0 < p[0] < 1.4)]
    bo, bom = point_cloud("base", restb, pop=0.0, t_offset=CLOCK["T0"])
    fo, fom = point_cloud("first", first, pop=0.0, t_offset=CLOCK["T0"])
    for o, mm in ((bo, bom), (fo, fom)):
        show_between(o, tdark); pts_glow(mm, tdark - 0.1, 0.0); pts_glow(mm, tdark + 0.4, 2.2)
    dp = drift_points(d2, d2.t0, d2.t1, d2) + drift_points(d3, d3.t0, d3.t1, d2, seed=6)
    dp = [(x, y, max(t, tdark + 0.3)) for x, y, t in dp]
    hold = empty((0, 0, 0))
    do, dom = point_cloud("drift", dp, t_offset=CLOCK["T0"]); do.parent = hold
    if cut(cl, "S16b"):          # v6：車輪の寄りには地図の点を出さない（切りかえの間に線が横切って見えた）
        for o in (bo, fo, do): hide_key(o, CLOCK["T0"] - 1.0, True); hide_key(o, tdark + 0.001, True); hide_key(o, tdark + 0.4, True)
    # 17-03：いま見えている（最初の壁の前で）形を白い点で
    xs, ys, _ = d3.pose(d3.t1)
    S_ = plan.segments(); cur = []
    a = math.radians(DRIFT["th"]); ca, sa = math.cos(a), math.sin(a); c = DRIFT["c"]
    for a_ in range(0, 360, 2):
        hh = plan.ray(xs, ys, R(a_), S_)
        if hh and hh[1][1] > 2.3:
            rx, ry = hh[1][0] - c[0], hh[1][1] - c[1]
            cur.append((c[0] + rx * ca - ry * sa + DRIFT["d"][0], c[1] + rx * sa + ry * ca + DRIFT["d"][1], 0.0))
    tw = w("17-03", "いま見えている")
    co, com = point_cloud("cur17", cur, col=WHITE_PT, radius=0.022, z=plan.LIDAR_Z + 0.01, pop=0.0, base=3.5, t_offset=1e5); co.parent = hold
    show_between(co, tw); ev(tw, "pop", 0.4)
    # v4「いま見えている壁のときには、いま見えている壁のとこだけ見せた方がいいかも」：17-03 の間は地図の点を隠し、白い形だけ。
    #   17-04（どこかで見たような）で地図が戻って、見比べる
    for o in (bo, fo, do): hide_key(o, tw - 0.05, True); hide_key(o, s("17-04") - 0.1, False)
    # 17-05：いちばん最初に描いた壁が光る／17-06 先輩「ピッ」
    t5 = w("17-05", "あの壁")
    pts_glow(fom, t5 - 0.1, 2.2); pts_glow(fom, t5 + 0.3, 9.0); pts_glow(fom, e("17-05") + 0.4, 9.0); pts_glow(fom, e("17-05") + 1.0, 3.5)
    sp.pi(w("17-06", "気づいた"), n=1)
    # 17-08：ずれていた地図全体を引き戻す（回転の中心 c、ずれ d を打ち消す動き）
    tA = w("17-08", "ぐっと"); tB = s("17-09") + 0.15
    th = -math.radians(DRIFT["th"]); ct, st_ = math.cos(th), math.sin(th)
    cx, cy = DRIFT["c"]; dx, dy = DRIFT["d"]
    Lx = cx - (ct * (cx + dx) - st_ * (cy + dy)); Ly = cy - (st_ * (cx + dx) + ct * (cy + dy))
    key(hold, "location", tA, (0, 0, 0)); key(hold, ("rotation_euler", 2), tA, 0.0)
    key(hold, "location", tB, (Lx, Ly, 0)); key(hold, ("rotation_euler", 2), tB, th)
    ev(tA, "whoosh", 0.4); ev(tB, "snap", 0.8)
    for mm in (dom, fom, com, bom):
        pts_glow(mm, tB - 0.05, 2.2 if mm is not com else 3.5); pts_glow(mm, tB + 0.2, 8.0); pts_glow(mm, tB + 1.2, 2.2 if mm is not com else 3.5)
    hide_key(co, e("17-10"), True)
    m.hops(tB + 0.2, n=2, height=0.06)       # ぴたっと重なった！
    # v3（5本目 v2「ここの表現全然わかんない」→ 上から見て色分け）：17-07 で真上から。1 周目に描いた壁＝青緑、
    #   2 周目（じゅうたんのあと）に描いた点・いま見えている形＝オレンジ。本当の壁はうすい白の帯で重ねる（本当は 1 本）。
    #   2D で「同じ壁」の両向きの矢印と札（overlays）。17-08 で引き戻すと、オレンジが青緑にぴたっと重なり、17-10 で青緑に戻る
    t7 = w("17-07", "一つの壁") - 0.2
    ORANGE = "#FF9A3C"
    pts_color(com, t7 - 0.01, WHITE_PT); pts_color(com, t7 + 0.4, ORANGE)
    pts_color(com, s("17-10") + 0.2, ORANGE); pts_color(com, s("17-10") + 1.0, TEAL)
    pts_color(dom, tB + 0.25, TEAL)             # ずれた点は S17c では隠していて、ぴたっと重なったあとに青緑で戻る
    Y1 = 2.49                                   # 地図の点の壁の線（plan.map_points の y）
    real = empty((0.2, Y1, 0.005))      # 大きさは子の板で（scale_pop は親の empty に。板の scale を 1 に戻すと 1 m の箱になった）
    rb_ = cube(flat_mat("realwall", "#FFFFFF", 0.9), (0, 0, 0), (2.5, 0.07, 0.004), parent=real); rb_.visible_shadow = False
    show_between(real, t7 + 0.3, tA); scale_pop(real, t7 + 0.3, d=0.3)
    ax_ = -0.75
    a1 = empty((ax_, Y1, plan.LIDAR_Z))
    th0 = math.radians(DRIFT["th"]); rx, ry = ax_ - DRIFT["c"][0], Y1 - DRIFT["c"][1]
    a2 = empty((DRIFT["c"][0] + rx * math.cos(th0) - ry * math.sin(th0) + DRIFT["d"][0], DRIFT["c"][1] + rx * math.sin(th0) + ry * math.cos(th0) + DRIFT["d"][1], plan.LIDAR_Z)); a2.parent = hold
    track("wall1", a1, 0.0); track("wall2", a2, 0.0)
    if cut(cl, "S16a"):
        c_, tg = cam_rig((1.6, -2.6, 1.6), (-0.4, 0.4, 0.0), 28)
        cam_move(c_, tg, s("16-01") - 0.8, e("16-02") + 0.8, (1.7, -2.7, 1.65), (1.3, -2.3, 1.45), (-0.4, 0.4, 0.0), (-0.5, 0.2, 0.0))
    elif cut(cl, "S16b"):
        # v3（5本目 v2「車輪も写ってないし空回りもわかんない」）：体を透かして車輪を見せ、すぐ横の低い所から。
        #   車輪は速く回る（スポークが回る）のに、体と床の模様はほとんど進まない。2D で車輪のまわりに回る矢印（overlays の spin）
        for nm in ("sp_top_#F3F5F7", "sp_side_#DDE2E6", "sp_bumper"):
            mm = bpy.data.materials[nm]; mm.blend_method = 'BLEND'
            alpha_key(mm, s("16-03") - 0.2, 0.14)
        c_ = cam_follow(sp.root, (0.06, -0.62, 0.07), 0.03, 50)     # 先輩の右の車輪の真横、床すれすれ（近すぎるとぼける）
        c_.data.dof.use_dof = True; c_.data.dof.focus_object = sp.root; c_.data.dof.aperture_fstop = 11.0
    elif cut(cl, "S16c"):
        c_ = cam_top((-0.4, 0.1, 8.0), 30)
        cam_top_move(c_, s("16-05") - 0.8, e("16-06") + 0.8, (-0.4, 0.1, 8.0), (-0.6, 0.1, 7.6))
    elif cut(cl, "S17a"):
        c_, tg = cam_rig((1.2, -2.8, 3.0), (-0.6, 0.8, 0.0), 26)
        cam_move(c_, tg, s("17-01") - 0.8, e("17-02") + 0.4, (1.2, -2.8, 3.0), (1.4, -1.6, 2.6), (-0.6, 0.8, 0.0), (0.2, 1.7, 0.0))
    elif cut(cl, "S17c"):    # v3：真上から（1 周目と 2 周目の壁を色で分けて見せる）→ 17-10 で地図全体へ引く
        # v3 点検：点の光が床を照らして画面じゅうがオレンジになり、青緑の線も矢印も埋もれた → この絵では点はまわりを照らさない。
        #   寄りすぎると点が大きな粒になって帯に見え、左はソファに隠れる → 高さ 1.9 m（2 本の間は画面で 140px ほど）
        # 何周分ものずれた点が重なって太い帯に見えた → この絵では、ずれた点（do）を隠して、いま見えている形（オレンジの 1 本）だけにする。
        #   引き戻してぴたっと重なったあとに戻す（青緑の地図の一部として）
        hide_key(do, s("17-07") - 1.0, True)     # v4「青い点がすごいブレて線みたいじゃなくなってる」：ぴたっと重なったあとも戻さない（もとの地図だけで、きれいな線）
        for o in (do, co, fo, bo):
            o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False; o.visible_volume_scatter = False
        c_ = cam_top((-0.5, 2.2, 1.95), 29)
        cam_top_move(c_, s("17-07") - 0.4, e("17-09"), (-0.5, 2.2, 1.95), (-0.45, 2.2, 1.85))
        cam_top_move(c_, e("17-09"), e("17-11") + 0.8, (-0.45, 2.2, 1.85), (0.0, 0.2, 7.6))
    else:
        c_, tg = cam_rig((0.4, 0.4, 2.2), (0.3, 2.3, 0.0), 30)
        cam_move(c_, tg, s("17-03") - 0.8, s("17-07") + 1.0, (0.45, 0.45, 2.2), (0.35, 0.75, 2.0), (0.3, 2.3, 0.0), (0.3, 2.35, 0.0))
    track("senpai", sp.root, 0.15); track("maru", m.root, 0.42); track("wheel_r", sp.d["wheels"][1], 0.0); track("roll", roll, 0.0)


# ======================================================================== S18〜S21：カメラの先輩
CAMP = (-1.2, 0.95)
LIDP = (-0.55, 0.95)


def b_cam(cl):
    pov = cut(cl, "S19a"); dark_ceiling = cut(cl, "S21a")
    room(ceiling=(pov or dark_ceiling), front_wall=(pov or dark_ceiling)); door_leaf(False)   # 見上げる絵は手前の壁も（灰色のすき間を見せない）
    cs = Sp(senpai_camera((-1.9, 2.0), plan.face_deg(0.5, -1)))
    ls = Sp(senpai_lidar(DOCKP, 0)); ls.spin(CLOCK["T0"] - 2, e("21-03") + 3, 0.6)
    m = Maru((-0.3, 0.3, 0), face=180)
    # 18-01：ソファの下から、カメラの先輩が出てくる。光の先輩も台から出て、横に並ぶ
    t1 = w("18-01", "もう1台") - 0.2
    dc = plan.Drive([(-1.9, 2.0), (-1.6, 1.3), CAMP], t1, v=0.35, face0=plan.face_deg(0.5, -1))
    cs.place(s("18-01") - 1.5, -1.9, 2.0, plan.face_deg(0.5, -1)); cs.drive(dc)
    cs.place(dc.t1 + 0.6, CAMP[0], CAMP[1], 0)
    dl = plan.Drive([DOCKP, (0.3, 1.5), (-0.55, 1.35), LIDP], s("18-02"), v=0.4)
    ls.place(s("18-01") - 1.5, DOCKP[0], DOCKP[1], 0); ls.drive(dl); ls.place(dl.t1 + 0.5, LIDP[0], LIDP[1], 0)
    m.at(s("18-01") - 1.5, loc=(-0.3, 0.3, 0), face=180)
    m.at(t1 + 0.2, face=face_to((-0.3, 0.3), (-1.6, 1.3))); m.surprise(t1 + 0.6)       # 「もう1台の先輩が登場」
    m.at(s("18-03"), face=face_to((-0.3, 0.3), CAMP)); m.at(s("18-03") + 1.6, face=face_to((-0.3, 0.3), LIDP)); m.at(s("18-03") + 3.0, face=face_to((-0.3, 0.3), CAMP))
    m.walk(e("18-04") + 0.1, s("19-01") + 4.5, (0.75, 0.75, 0)); m.at(s("19-03"), face=face_to((0.75, 0.75), (0.0, -0.3)))     # 1.1 m に約 5 秒。19 章のカメラの目の絵の間に歩く   # 先輩の通り道をあける
    cr = bpy.data.materials["cam_ring"]
    emit_key(cr, w("18-04", "カメラ") - 0.1, 1.2); emit_key(cr, w("18-04", "カメラ") + 0.3, 8.0); emit_key(cr, e("18-04") + 0.6, 1.2); ev(w("18-04", "カメラ"), "pi", 0.35)
    # 19：天井の照明を見ながら進む（カメラの先輩から見た絵）。目印＝光る点（線で結ばない）
    t19 = e("19-02") - 0.6
    d19 = plan.Drive([CAMP, (-0.4, 0.55), (0.0, -0.9)], s("19-01") - 0.2, v=0.25)
    cs.drive(d19, s("19-01") - 0.2, t19)
    d19b = plan.Drive([d19.pose(t19)[:2], (0.0, 1.4)], t19, v=0.32, face0=d19.pose(t19)[2])
    cs.drive(d19b)
    x9, y9, a9 = d19b.pose(d19b.t1)
    cs.place(s("19-05"), x9, y9, a9); cs.place(s("19-06") + 0.4, x9, y9, a9); cs.place(e("19-06") - 0.3, x9, y9, a9 - 70)
    marks = []
    def mark(p, t, r=0.05):
        o = sphere(glow_mat("mark%d" % len(marks), YELLOW, 10.0), p, r); o.visible_shadow = False; show_between(o, t); scale_pop(o, t); marks.append(o); ev(t, "pi", 0.3); return o
    H = plan.CEIL
    lamp_mark = mark((0.0, 0.2, H - 0.075), w("19-01", "照明"), 0.07)
    x0, y0, x1, y1 = plan.ROOM
    t6 = w("19-06", "天井の角")
    mark((x0 + 0.05, y1 - 0.05, H - 0.06), t6); mark((x1 - 0.05, y1 - 0.05, H - 0.06), t6 + 0.15)
    sx0, sy0, sx1, sy1 = plan.FURN["shelf"][:4]
    mark((sx1, sy1, 0.9), w("19-06", "本棚の角")); mark((sx1, sy0, 0.9), w("19-06", "本棚の角") + 0.15)
    # 20：電気を消す → 光の先輩は進む、カメラの先輩はくるくる
    toff = e("20-01") + 0.15
    if not pov:
        lights_off(toff, toff + 0.12, sky=0.07, world_s=0.05); ev(toff, "switch", 0.8)   # 暗くても、先輩の動きが分かるくらいは残す
    xl, yl, al = LIDP[0], LIDP[1], 0.0
    d20 = plan.Drive([LIDP, (0.4, 0.3), (1.6, 0.3), (1.6, -1.2)], s("20-02") + 0.3, v=0.3)
    ls.drive(d20)
    xc, yc, ac = d19b.pose(d19b.t1); ac = ac - 70
    cs.place(s("20-04") + 0.3, xc, yc, ac)
    for k in range(1, 9):
        cs.place(s("20-04") + 0.3 + k * 0.9, xc, yc, ac + k * 80)
    ev(s("20-04") + 0.3, "motor_on", 0.3)
    m.at(e("19-07"), loc=(0.75, 0.75, 0))
    m.walk(s("20-05"), s("20-05") + 2.0, (xc + 0.45, yc - 0.35, 0)); m.at(s("20-06"), face=face_to((xc + 0.45, yc - 0.35), (xc, yc)))
    m.at(s("21-01") + 0.3, look=60)        # v3：真上に近く（光が天井に当たるのが見えるように。5本目 v2「まるロボが照らしてるのが分かりにくい」）
    # 21：まるロボが目の光で天井を照らす → 目印がまた見える → カメラの先輩が動き出す
    tp = w("21-01", "ぱっ")
    m.glow(tp - 0.1, 9.0, 0.15, g0=1.0); ev(tp, "light_on", 0.6)
    # v6：本物の体は見上げても胴が少ししか傾かないので、光の筋は体の場所だけについていき、向きは天井の光の丸へ固定する
    mx0, my0 = xc + 0.45, yc - 0.35; ux, uy = xc - mx0, yc - my0; ul = math.hypot(ux, uy); ux, uy = ux / ul, uy / ul
    reach = (plan.CEIL - 0.2) / math.tan(R(60)); SPOTP = Vector((mx0 + ux * reach, my0 + uy * reach, plan.CEIL - 0.006))
    eye0 = Vector((mx0, my0, MM.TORSO_Z * Maru.S))
    anc = empty(tuple(eye0)); anc.scale = (Maru.S,) * 3
    anc.rotation_euler = (SPOTP - eye0).to_track_quat('Y', 'Z').to_euler()     # 体の +Y を天井の丸へ
    cl_ = anc.constraints.new('COPY_LOCATION'); cl_.target = m.torso
    bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0)); spl = bpy.context.object
    spl.parent = anc; spl.location = (0, 0.55, MM.LENS["z"]); spl.rotation_euler = (R(90), 0, 0)
    spl.data.spot_size = R(40); spl.data.spot_blend = 0.5; spl.data.color = srgb("#BFFFF6")[:3]
    spl.data.energy = 0.0; spl.data.keyframe_insert("energy", frame=f(tp - 0.1)); spl.data.energy = 1400.0; spl.data.keyframe_insert("energy", frame=f(tp + 0.15))
    CD = 9.6   # 円すいの長さ（体の中の大きさ。まるロボは 0.26 倍なので、本当は約 2.5 m＝天井まで）
    # v4「まるロボ側が細くて、天井側の光が広いように」：円すいの +z（radius2）が目の側に来るので、目の側を細く
    bpy.ops.mesh.primitive_cone_add(radius1=1.6, radius2=0.1, depth=CD, vertices=48, location=(0, 0, 0)); cone = bpy.context.object
    CD = ((SPOTP - eye0).length - 0.55 * Maru.S) / Maru.S          # 目から天井の丸まで（体の中の大きさで）
    cone.data.transform(Matrix.Scale(CD / 9.6, 4, Vector((0, 0, 1))))
    cone.parent = anc; cone.location = (0, 0.55 + CD / 2, MM.LENS["z"]); cone.rotation_euler = (R(90), 0, 0)   # 目の光の筋（光の円すい。天井まで）
    cm_ = bpy.data.materials.new("eyecone"); cm_.use_nodes = True; nt_ = cm_.node_tree
    for n_ in list(nt_.nodes): nt_.nodes.remove(n_)
    o_ = nt_.nodes.new("ShaderNodeOutputMaterial"); em_ = nt_.nodes.new("ShaderNodeEmission"); tr_ = nt_.nodes.new("ShaderNodeBsdfTransparent"); mx_ = nt_.nodes.new("ShaderNodeMixShader")
    em_.inputs["Color"].default_value = srgb("#BFFFF6"); em_.inputs["Strength"].default_value = 2.2
    nt_.links.new(tr_.outputs[0], mx_.inputs[1]); nt_.links.new(em_.outputs[0], mx_.inputs[2]); nt_.links.new(mx_.outputs[0], o_.inputs[0])
    mx_.inputs[0].default_value = 0.13; cone.data.materials.append(cm_); cone.visible_shadow = False
    for a_ in ("visible_diffuse", "visible_glossy", "visible_transmission"): setattr(cone, a_, False)
    show_between(cone, tp)
    # 天井に当たった光の丸（はっきり見えるように）
    spot = cyl(glow_mat("ceilspot", "#DFFFFA", 3.0), tuple(SPOTP), 0.42, 0.004, verts=64); spot.visible_shadow = False
    for a_ in ("visible_diffuse", "visible_glossy"): setattr(spot, a_, False)
    show_between(spot, tp); scale_pop(spot, tp, d=0.2)
    for o in marks:
        hide_key(o, toff, True); hide_key(o, tp + 0.4, False)
    cs.place(s("21-02") + 0.6, xc, yc, ac + 8 * 80)
    d21 = plan.Drive([(xc, yc), (xc - 0.6, yc - 0.8)], s("21-02") + 1.0, v=0.25, face0=ac + 8 * 80)
    cs.drive(d21)
    hl = cs.d["headlight"].data.materials[0]
    emit_key(hl, w("21-03", "ライト") - 0.1, 0.0); emit_key(hl, w("21-03", "ライト") + 0.2, 30.0)
    bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0)); hs = bpy.context.object
    hs.parent = cs.root; hs.location = (0.04, -0.16, 0.06); hs.rotation_euler = (R(-80), 0, 0); hs.data.spot_size = R(70); hs.data.energy = 0.0
    hs.data.keyframe_insert("energy", frame=f(w("21-03", "ライト") - 0.1)); hs.data.energy = 60.0; hs.data.keyframe_insert("energy", frame=f(w("21-03", "ライト") + 0.2))
    if cut(cl, "S18a"):
        c, tg = cam_rig((-0.9, -1.0, 0.7), (-1.2, 1.1, 0.1), 30)
        cam_move(c, tg, s("18-01") - 0.8, e("18-02") + 0.4, (-0.85, -1.05, 0.72), (-0.9, -0.5, 0.5), (-1.5, 1.4, 0.1), (-0.9, 1.0, 0.1))
        cam_move(c, tg, e("18-02") + 0.4, s("18-04"), (-0.9, -0.5, 0.5), (-1.15, 0.35, 0.3), (-0.9, 1.0, 0.1), (-1.2, 0.95, 0.07), 30, 48)
        cam_move(c, tg, s("18-04"), e("18-04") + 0.6, (-1.15, 0.35, 0.3), (-1.2, 0.2, 0.15), (-1.2, 0.95, 0.07), (-1.2, 0.8, 0.06), 48, 45)   # v3：前のカメラに寄る（5本目 v2「前のカメラがどれかわかんない」）
    elif pov:
        cam = bpy.data.objects.new("povcam", bpy.data.cameras.new("povcam")); bpy.context.collection.objects.link(cam)
        cam.parent = cs.root; cam.location = (0, -0.1, 0.12); cam.rotation_euler = (R(150), 0, R(180)); cam.data.lens = 14
        bpy.context.scene.camera = cam
    elif cut(cl, "S20a"):
        c, tg = cam_rig((0.6, -3.2, 2.2), (-0.3, 0.4, 0.0), 26)
        cam_move(c, tg, s("20-01") - 0.8, e("20-06") + 0.6, (0.7, -3.3, 2.25), (0.1, -2.6, 1.6), (-0.3, 0.4, 0.0), (-0.2, 0.1, 0.0))
    else:
        c, tg = cam_rig((1.6, -0.9, 0.7), (0.4, 1.1, 1.0), 22)
        cam_move(c, tg, s("21-01") - 0.8, e("21-02"), (1.6, -0.9, 0.7), (1.4, -0.7, 0.6), (0.2, 1.2, 1.3), (0.1, 1.2, 1.0))
        cam_move(c, tg, e("21-02"), e("21-03") + 0.6, (1.4, -0.7, 0.6), (0.9, 0.0, 0.35), (0.1, 1.2, 1.0), (-0.1, 0.9, 0.08), 22, 32)
    track("cam", cs.root, 0.12); track("lidar", ls.root, 0.15); track("maru", m.root, 0.42); track("camlens", cs.d["cam"], 0.0, box=True)


# ======================================================================== S22〜S23：段差（光の物差しの先輩）
def b_step(cl):
    room(hall_walls=(True, not cut(cl, "S23a")), front_wall=cut(cl, "S22a")); door_leaf(True)
    ls = Sp(senpai_lidar((-2.3, -1.75), plan.face_deg(-1, 0))); ls.spin(CLOCK["T0"] - 2, e("23-02") + 3, 0.6)
    cs = Sp(senpai_camera((-2.2, -1.15), plan.face_deg(-1, 0)))
    m = Maru((-1.7, -2.05, 0), face=plan.face_deg(-1, 0))
    ls.place(s("22-01") - 1.5, -2.3, -1.75, plan.face_deg(-1, 0)); cs.place(s("22-01") - 1.5, -2.2, -1.15, plan.face_deg(-1, 0))
    m.at(s("22-01") - 1.5, loc=(-1.7, -2.05, 0))
    edge = plan.STEP_X + 0.19
    d22 = plan.Drive([(-2.3, -1.75), (edge, -1.75)], w("22-04", "ぴたっ") - (abs(edge + 2.3) / 0.3), v=0.3)
    ls.drive(d22)
    tst = w("22-04", "ぴたっ")
    ls.place(tst + 0.05, edge, -1.75, plan.face_deg(-1, 0)); ls.place(tst + 1.2, edge, -1.75, plan.face_deg(1, 0) - 360)
    ev(tst, "stop", 0.5)
    # まるロボは横の列を歩いて、そのまま段差の先へ → ころん
    tf = w("22-05", "ころん")
    m.walk(s("22-05") - 0.6, tf - 0.45, (plan.STEP_X + 0.05, -2.05, 0))
    m.move_parent(tf - 0.45, tf, (-0.30, 0.0), dz=-plan.STEP_H)     # 段差の先へ出て、置き場所ごと下へ落ちる
    # v6（ユーザー「まるロボが落ちた時にコロンって転がる感じにして」）：床に着いたら、一覧の roll_over（5本目で足した）で横へ転がる。
    #   転がった分（体の半径 約 0.085 m × 80°）だけ置き場所を横へ動かす
    # v7（ユーザー「コロンってときはひっくり返る感じに」）：床に着いたら、前へでんぐり返ってあお向け（脚が上）に。23-01 で戻って起き上がる
    FWD = (0.0, 1.0)          # 倒れる向き：画面の左（段差の側）へ横に。前（-x）だと画面の外へ出る
    m.flip(tf + 0.02, 0.75, FWD, at=(plan.STEP_X + 0.05 - 0.30, -2.05)); ev(tf + 0.02 + 0.75 * 1.0 / 1.7, "maru:land", 0.9); ev(tf + 0.02 + 0.75 * 1.5 / 1.7, "maru:land", 0.35)
    m.blink(s("22-06") + 0.2); m.blink(s("22-06") + 0.6)
    m.flip(s("23-01") + 0.3, 0.6, FWD, back=True); ev(s("23-01") + 0.9, "maru:land", 0.6)      # 逆にたどって起き上がる
    m.act(s("23-01") + 1.0, "get_up"); m.at(s("23-01") + 5.1, face=plan.face_deg(1, 0), look=25)      # 一覧の get_up
    # 23：おなかの下の光（体を少し透かして見せる）。床では行って返る、段差の上では返ってこない
    for nm in ("sp_top_#F3F5F7", "sp_side_#DDE2E6", "sp_bumper"):
        mm = bpy.data.materials[nm]; mm.blend_method = 'BLEND'
        alpha_key(mm, s("23-01") - 0.5, 1.0); alpha_key(mm, s("23-01") + 0.3, 0.25)
    # 窓と床のすき間（実物は 1 cm たらず）を、この場面だけ少し広げて見せる（体を上げ、車輪は床のまま）
    key(ls.root, ("location", 2), s("23-01") - 0.6, 0.0); key(ls.root, ("location", 2), s("23-01") + 0.2, 0.035)
    for wl in ls.d["wheels"]: key(wl.parent, ("location", 2), s("23-01") - 0.6, 0.03); key(wl.parent, ("location", 2), s("23-01") + 0.2, -0.005)
    bb = beam(ls.root, 1.0, YELLOW, 0.006, 9.0); bb.location = (0, -0.13, 0.006); bb.rotation_euler = (R(90), 0, 0)
    for ch in bb.children:      # v3：光の線がまわり（段差の板）を照らして、板を突きぬけて見えた（5本目 v2「一瞬光が下に貫通してる」）→ まわりを照らさない
        ch.visible_diffuse = False; ch.visible_glossy = False; ch.visible_transmission = False
    pulse = sphere(glow_mat("bpulse", "#FFFFFF", 20.0), (0, 0, 0), 0.012, parent=bb)
    bb.scale = (1, 0.045, 1)
    t1_ = w("23-01", "光が出ている") - 0.3
    show_between(bb, t1_ - 0.2)
    for k in range(3):
        tk = t1_ + k * 0.9
        key(pulse, ("location", 1), tk, 0.0, "LINEAR"); key(pulse, ("location", 1), tk + 0.3, -1.0, "LINEAR"); key(pulse, ("location", 1), tk + 0.6, 0.0, "LINEAR")
    # 23-02：少し前へ → 窓が段差の上に出る → 光は下へ落ちて、返ってこない → 止まって下がる
    t2 = s("23-02") - 0.2
    ls.place(t2, edge, -1.75, plan.face_deg(1, 0) - 360)
    ls.place(t2 + 0.8, edge, -1.75, plan.face_deg(-1, 0) - 360 - 360 + 360)
    ls.place(t2 + 1.6, edge - 0.09, -1.75, plan.face_deg(-1, 0) - 360 - 360 + 360)
    key(bb, ("scale", 1), t2 + 1.5, 0.045); key(bb, ("scale", 1), t2 + 1.7, 0.15)     # 下の床に届かない長さで止める（v3）
    for k in range(2):
        tk = t2 + 1.8 + k * 1.1
        key(pulse, ("location", 1), tk, 0.0, "LINEAR"); key(pulse, ("location", 1), tk + 0.7, -1.0, "LINEAR"); key(pulse, ("location", 1), tk + 0.71, 0.0, "CONSTANT")
    ev(w("23-02", "返ってこなければ"), "pi_low", 0.5)
    tb = w("23-02", "止まれる")
    ls.place(tb, edge - 0.09, -1.75, -450); ls.place(tb + 0.8, edge + 0.05, -1.75, -450)
    key(bb, ("scale", 1), tb + 0.6, 0.15); key(bb, ("scale", 1), tb + 0.8, 0.045)
    if cut(cl, "S22a"):     # 部屋の中から、出入り口の方を
        c, tg = cam_rig((-1.0, -0.4, 0.9), (-3.3, -1.9, 0.0), 26)
        cam_move(c, tg, s("22-01") - 0.8, e("22-03") + 0.4, (-0.9, -0.3, 0.95), (-1.5, -0.9, 0.55), (-3.0, -1.7, 0.0), (-3.0, -1.8, 0.05))
    elif cut(cl, "S22b"):   # 廊下のつきあたりから、段差と部屋の方をふり返る
        c, tg = cam_rig((-4.5, -1.5, 0.42), (-3.4, -1.9, 0.0), 24)
        cam_move(c, tg, s("22-04") - 0.8, s("22-05"), (-4.5, -1.5, 0.42), (-4.49, -1.53, 0.4), (-3.4, -1.85, 0.0), (-3.5, -1.92, -0.02), 24, 24)
        cam_move(c, tg, s("22-05"), e("22-06") + 0.6, (-4.49, -1.53, 0.4), (-4.5, -1.6, 0.42), (-3.5, -1.92, -0.02), (-3.75, -2.05, 0.02), 24, 19)      # v7：ひっくり返る弧が入るよう、少し広く
    else:                   # 23：横から（廊下の片側の壁を外して）
        c, tg = cam_rig((-3.55, -0.85, 0.06), (-3.6, -1.75, 0.02), 42)
        cam_move(c, tg, s("23-01") - 0.8, e("23-02") + 0.6, (-3.5, -0.85, 0.06), (-3.62, -0.95, 0.05), (-3.58, -1.75, 0.03), (-3.62, -1.75, 0.0))
    track("lidar", ls.root, 0.15); track("maru", m.root, 0.42)


# ======================================================================== S24〜S25：よける（カメラの先輩）
SOCK = (-0.55, -1.15); CORD = [(0.15, -1.55), (0.25, -1.25), (0.1, -0.95), (0.3, -0.7)]; POOP = (0.9, -0.55)


def b_avoid(cl):
    room(); door_leaf(False)
    cs = Sp(senpai_camera((-1.8, -1.15), plan.face_deg(1, 0)))
    m = Maru((-0.4, -0.25, 0), face=face_to((-0.4, -0.25), SOCK))
    sock((SOCK[0], SOCK[1], 0.0), 30); cord(CORD)
    # 24：靴下・コードの手前でよける
    t3 = s("24-02") + 0.5
    route = [(-1.8, -1.15), (-1.05, -1.15), (-0.75, -1.55), (-0.25, -1.6), (-0.15, -1.95), (0.55, -2.0), (0.6, -1.3), (0.75, -1.1)]
    d24 = plan.Drive(route, t3, v=0.3)
    cs.place(s("24-01") - 1.5, -1.8, -1.15, plan.face_deg(1, 0)); cs.drive(d24)
    def frame_box(cx, cy, wx, wy, t0, t1):
        bx = empty((cx, cy, 0.03))
        for (px, py, sx, sy) in ((0, wy / 2, wx, 0.012), (0, -wy / 2, wx, 0.012), (wx / 2, 0, 0.012, wy), (-wx / 2, 0, 0.012, wy)):
            o = cube(flat_mat("frm", TEAL, 4.0), (px, py, 0), (sx, sy, 0.012), parent=bx); o.visible_shadow = False
        show_between(bx, t0, t1); scale_pop(bx, t0); ev(t0, "pi", 0.35); return bx
    frame_box(SOCK[0] + 0.02, SOCK[1] - 0.03, 0.34, 0.34, w("24-02", "靴下"), e("24-04") + 0.5)
    frame_box(0.2, -1.12, 0.36, 0.95, w("24-02", "コード"), e("24-04") + 0.5)
    m.at(s("24-01") - 1.5, loc=(-0.4, -0.25, 0)); m.at(s("24-03"), face=face_to((-0.4, -0.25), (0.0, -1.8))); m.at(s("24-04"), face=face_to((-0.4, -0.25), (0.6, -1.3)))
    # 25：うんちがぽん → カメラの先輩が見分けて、手前でよける
    pe = poop((POOP[0], POOP[1], 0.0)); tpo = w("25-02", "うんち")
    show_between(pe, tpo - 0.05); scale_pop(pe, tpo); ev(tpo, "pop", 0.6)
    m.peer(tpo + 0.3, dur=1.4)
    frame_box(POOP[0], POOP[1], 0.26, 0.26, s("25-03") + 0.6, s("25-04") + 0.5)
    # 25-06：約束は、テレビの広告（S25c・b_ad）で見せる（v3。5本目 v2「広告なりインタビューで宣言してるような映像を差し込んで」）
    x24, y24, a24 = d24.pose(d24.t1)
    d25 = plan.Drive([(x24, y24), (0.75, -0.85), (0.4, -0.78), (0.2, -0.25), (0.55, 0.2)], max(d24.t1, s("25-03") - 0.2), v=0.28, face0=a24)   # v3：まるロボ（mp1）から 0.37 m 離れて通る
    cs.drive(d25)
    # 25-07：まるロボ、のけぞって後ろへ跳ぶ → 足がうんちのすぐ横に（アップでは踏んだように見える）
    mp2 = (POOP[0] - 0.072, POOP[1] + 0.025)       # v6（ユーザー「まるロボのかかとが若干うんちを踏んでる感じに」）：前は 0.139 m 離れていた → かかとがうんちのふちにかかる近さ
    _u = (0.0 - mp2[0], 0.6 - mp2[1]); _l = math.hypot(*_u); mp1 = (mp2[0] + 0.035 * _u[0] / _l, mp2[1] + 0.035 * _u[1] / _l)   # v6：surprise の後ろ跳び（約 3 cm）で足がうんちの横に着く所
    # v3（5本目 v2「驚く前にうんちに近づくのが違和感」）：うんちが出る前（24-04 のあと）に歩いておく。うんちが出たら見て、25-05 で向こうを向く
    m.walk(e("24-04") + 0.3, w("25-02", "うんち") - 1.05, mp1); m.at(tpo + 0.1, face=face_to(mp1, POOP))
    m.at(s("25-05") + 0.3, face=face_to(mp1, (0.0, 0.6)))
    tj = s("25-07") + 0.2
    m.surprise(tj - 0.2)       # 「思わずのけぞって」：一覧の surprise（後ろへ小さく跳ぶ。足がうんちのすぐ横に）
    ev(tj + 0.4, "squish", 0.8)          # 足がうんちのすぐ横に着く音
    m.at(tj + 0.9, look=-5)
    m.glow(s("25-08") + 0.2, 0.3, 0.3, g0=0.9)
    m.at(e("25-08") + 0.2, look=-40); m.glow(e("25-08") + 0.5, 1.6, 0.2, g0=0.3); m.shake(e("25-08") + 0.6)      # 「踏んでない」と首を振る（一覧の shake）
    if cut(cl, "S24a"):
        c, tg = cam_rig((-1.8, -2.6, 1.3), (-0.3, -1.2, 0.0), 30)
        cam_move(c, tg, s("24-01") - 0.8, e("24-04") + 0.5, (-1.9, -2.7, 1.35), (-0.6, -2.9, 1.1), (-0.6, -1.2, 0.0), (0.1, -1.3, 0.0))
    elif cut(cl, "S25a") or cut(cl, "S25d"):
        c, tg = cam_rig((-0.4, -1.9, 1.0), (0.7, -0.45, 0.05), 30)
        cam_move(c, tg, s("25-01") - 0.8, e("25-06") + 0.4, (-0.45, -2.0, 1.05), (-0.1, -1.7, 0.75), (0.7, -0.45, 0.05), (0.8, -0.5, 0.05))
        cam_move(c, tg, e("25-06") + 0.4, e("25-08") - 0.2, (-0.1, -1.7, 0.75), (0.5, -0.95, 0.1), (0.8, -0.5, 0.05), (0.82, -0.48, 0.04), 30, 48)
    else:   # 25-08 の終わり：上から見ると、ちゃんと横
        c = cam_top((0.8, -0.5, 1.0), 40)
        cam_top_move(c, e("25-08") - 0.6, e("25-09") + 0.6, (0.8, -0.5, 1.0), (0.8, -0.45, 1.25))
    track("cam", cs.root, 0.12); track("maru", m.root, 0.42); track("poop", pe, 0.1)


# ======================================================================== S25c：テレビの広告（v3）。架空の会社。本物の会社名・ロゴは使わない。字は書かない
def b_ad(cl):
    """スタジオの台の上でカメラの先輩が回る → 「うんち」で前にうんち → 「よけられなかったら」で赤い × → 「新品」で箱がぽん（きらきら）。
    2D で、まわりにテレビのふち（overlays の tv）"""
    sc = bpy.context.scene; sc.world = bpy.data.worlds.new("adw"); sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = srgb("#DDEFF0"); bg.inputs["Strength"].default_value = 0.08
    # 床と、奥のまるい壁（つなぎ目の見えない背景）
    fl = cyl(mat("adfloor", "#E3ECEC", rough=0.7), (0, 0, -0.01), 6.0, 0.02, verts=96)
    bpy.ops.mesh.primitive_cylinder_add(radius=3.2, depth=4.0, vertices=128, location=(0, 0.6, 2.0), end_fill_type='NOTHING'); wall = bpy.context.object
    wm = bpy.data.materials.new("adwall"); wm.use_nodes = True; nt = wm.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp_ = nt.nodes.new("ShaderNodeSeparateXYZ"); cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sp_.inputs[0]); nt.links.new(sp_.outputs["Z"], cr.inputs[0])
    cr.color_ramp.elements[0].color = srgb("#CFEDEA"); cr.color_ramp.elements[1].color = srgb("#2A8C88"); cr.color_ramp.elements[1].position = 0.75
    nt.links.new(cr.outputs[0], bs.inputs["Base Color"]); nt.links.new(cr.outputs[0], bs.inputs["Emission Color"]); bs.inputs["Emission Strength"].default_value = 0.08
    bs.inputs["Roughness"].default_value = 0.8; wall.data.materials.append(wm)
    # 台（白い丸い台・青緑の光の輪・前に会社の印（丸い形だけ））
    cyl(mat("podium", "#FFFFFF", rough=0.2, coat=0.6), (0, 0, 0.05), 0.42, 0.1, verts=96)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.008, location=(0, 0, 0.1)); ring = bpy.context.object
    ring.data.materials.append(glow_mat("podring", TEAL, 6.0)); ring.visible_shadow = False
    logo = cyl(glow_mat("adlogo", TEAL, 2.0), (0, -0.421, 0.05), 0.035, 0.004, rot=(R(90), 0, 0), verts=48); logo.visible_shadow = False
    cyl(mat("adlogo_in", "#FFFFFF", rough=0.3), (0, -0.424, 0.05), 0.018, 0.004, rot=(R(90), 0, 0), verts=32)
    # 主役：カメラの先輩（台の上でゆっくり回る）
    cs = Sp(senpai_camera((0, 0, 0.1), 0))
    t0 = s("25-06") - 0.6; tpo = w("25-06", "うんち"); tx_ = w("25-06", "よけられなかったら") + 0.25; tn = w("25-06", "新品"); tend = s("25-07") + 1.0
    key(cs.root, ("rotation_euler", 2), t0, R(-40), "LINEAR"); key(cs.root, ("rotation_euler", 2), tpo, R(25), "LINEAR")
    key(cs.root, ("rotation_euler", 2), tpo + 0.5, R(25)); key(cs.root, ("rotation_euler", 2), tend, R(40), "LINEAR")
    # うんち（台の前の床）→ 赤い ×
    # v3 点検：うんちが字幕の下・× が先輩の前に浮いて重なる・箱が画面の外 → 左にうんちと ×、真ん中に先輩、右に箱。少し引いて全部入れる
    PP = (-0.52, -0.45)
    pe = poop((PP[0], PP[1], 0.0), 1.2); show_between(pe, tpo - 0.05); scale_pop(pe, tpo); ev(tpo, "pop", 0.5)
    xe = empty((PP[0], PP[1], 0.3)); xe.rotation_euler = (0, 0, R(90))      # うんちの上に浮かべる（うんちを隠さない）
    xr = mat("xred", "#C8231A", rough=0.45)
    for sg, th_ in ((1, 0.026), (-1, 0.022)): cube(xr, (0, 0, 0), (th_, 0.26, 0.045), rot=(R(45 * sg), 0, 0), bevel=0.008, parent=xe)   # 厚みを変えて、重なる面のちらつき（黒い四角）を防ぐ
    show_between(xe, tx_); scale_pop(xe, tx_); ev(tx_, "bonk_soft", 0.5)
    # 新品の箱（右に。リボン・きらきら）
    bx = empty((0.56, -0.32, 0.0)); bx.rotation_euler = (0, 0, R(-18)); bsz = 0.26
    cube(noise_mat("cardboard", "#C99A62", "#BE8E57", 30, 0.8), (0, 0, bsz / 2), (bsz, bsz, bsz), bevel=0.006, parent=bx)
    cube(mat("boxlid", "#D3A66C", rough=0.75), (0, 0, bsz + 0.012), (bsz + 0.02, bsz + 0.02, 0.03), bevel=0.006, parent=bx)
    rb = mat("ribbon", "#E24C42", rough=0.35, coat=0.4)
    cube(rb, (0, 0, bsz / 2 + 0.01), (0.04, bsz + 0.024, bsz + 0.04), parent=bx); cube(rb, (0, 0, bsz / 2 + 0.01), (bsz + 0.024, 0.04, bsz + 0.04), parent=bx)
    for sx in (-1, 1): sphere(rb, (sx * 0.04, 0, bsz + 0.05), 0.034, scale=(1.3, 0.6, 0.8), parent=bx)
    for k, (dx, dy, dz) in enumerate(((-0.2, 0.0, 0.36), (0.19, 0.05, 0.32), (-0.06, -0.12, 0.46), (0.12, -0.14, 0.2))):
        sm_ = mat("spark%d" % k, "#FFD24A", rough=0.3, emit=0.0)
        sphere(sm_, (dx, dy, dz), 0.018, parent=bx, seg=12)
        for j in range(4):
            tt = tn + 0.15 + k * 0.12 + j * 0.55
            emit_key(sm_, tt, 0.0); emit_key(sm_, tt + 0.12, 9.0); emit_key(sm_, tt + 0.35, 0.0)
    show_between(bx, tn); scale_pop(bx, tn, d=0.35); ev(tn, "chime", 0.5)
    # まわりのきらきら（広告らしく）
    for k in range(10):
        a_ = 2 * math.pi * k / 10; sm_ = mat("adsp%d" % k, "#FFFFFF", rough=0.3, emit=0.0)
        sphere(sm_, (0.75 * math.cos(a_), 0.4 + 0.5 * math.sin(a_), 0.5 + 0.35 * (k % 3)), 0.012, seg=10)
        for j in range(6):
            tt = t0 + 0.2 + k * 0.17 + j * 1.1
            emit_key(sm_, tt, 0.0); emit_key(sm_, tt + 0.15, 12.0); emit_key(sm_, tt + 0.45, 0.0)
    # 光（上からのやわらかい光・後ろからの縁の光）
    for loc, en, sz in (((0.9, -1.6, 2.2), 70, 1.6), ((-1.4, -0.8, 1.6), 30, 1.2), ((0.0, 1.2, 1.8), 70, 1.0)):
        bpy.ops.object.light_add(type='AREA', location=loc); L_ = bpy.context.object; L_.data.energy = en; L_.data.size = sz
        dd = Vector((0, 0, 0.2)) - Vector(loc); L_.rotation_euler = dd.to_track_quat('-Z', 'Y').to_euler()
    c, tg = cam_rig((0.0, -2.5, 0.7), (0.0, -0.25, 0.08), 44)
    cam_move(c, tg, t0, tend, (0.05, -2.6, 0.72), (0.0, -2.4, 0.66), (0.0, -0.25, 0.08), (0.0, -0.27, 0.08)); dof(c, cs.root, 8.0)


# ======================================================================== S26〜S27：まとめ・オチ
def b_end(cl):
    room(); door_leaf(False)
    ls = Sp(senpai_lidar((0.9, 0.2), 0)); ls.spin(CLOCK["T0"] - 2, e("27-05") + 3, 0.6)
    cs = Sp(senpai_camera((1.6, -0.5), 90))
    cube(mat("dock2", "#E9ECEF", rough=0.3, coat=0.4), (2.93, 1.2, 0.07), (0.08, 0.5, 0.14), bevel=0.02)
    # スマホ：26 章はきのうの地図 → 次の日の頭で消える → 「スマホにまた地図が」でつく（まるロボの丸い形つき）→「丸い形」で輪
    ph, scr = phone_seq(PHONE_DESK, -95, [(0, tex("phone3d_base.png")), (s("27-01"), tex("phone3d_off.png")),
        (w("27-02", "スマホ"), tex("phone3d_maru.png")), (w("27-03", "丸い形"), tex("phone3d_maru_ring.png"))])
    ev(w("27-02", "スマホ"), "notify", 0.6); ev(w("27-03", "丸い形"), "pop", 0.45)
    # 26：2 台が台へ戻る
    dl = plan.Drive([(0.9, 0.2), (0.3, 1.0), (0.3, 1.7)], s("26-01") - 0.2, v=0.3)
    ls.place(s("26-01") - 1.5, 0.9, 0.2, 0); ls.drive(dl)
    ls.place(dl.t1 + 0.1, 0.3, 1.7, 180); ls.place(dl.t1 + 1.2, 0.3, 1.7, 360); ls.place(dl.t1 + 2.0, 0.3, DOCKP[1], 360)
    dc = plan.Drive([(1.6, -0.5), (2.3, 1.2), (2.55, 1.2)], s("26-02"), v=0.3, face0=90)
    cs.place(s("26-01") - 1.5, 1.6, -0.5, 90); cs.drive(dc); cs.place(dc.t1 + 1.0, 2.55, 1.2, 90)
    m = Maru((0.2, -0.3, 0), face=face_to((0.2, -0.3), (0.3, 1.5)))
    m.at(s("26-01") - 1.5, loc=(0.2, -0.3, 0)); m.at(s("26-03"), face=face_to((0.2, -0.3), (2.5, 1.2))); m.at(s("26-05"), face=face_to((0.2, -0.3), (0.3, 2.0)))
    # 27：次の日。まるロボは部屋の真ん中で見守る。光の先輩がまわりを掃除してよけて通る → 台へ
    MC = (0.0, 0.2)
    T27 = s("27-01")
    m.teleport(T27 - 0.40, (MC[0], MC[1]), 0)      # 「次の日」：カットで置き直す（一覧の teleport。26 章の終わりは昔の場面に差しかわっていて見えない）
    m.at(e("26-05") - 1.2, face=0, look=0)      # 26 章の終わり（昔の場面に差しかわって見えない間）に向きを変えておく
    ring = [(MC[0] + 0.45 * math.cos(a), MC[1] + 0.45 * math.sin(a)) for a in [math.radians(-90 + k * 30) for k in range(13)]]
    d27 = plan.Drive([DOCKP, (0.3, -0.25)] + ring[1:] + [(0.3, -0.25), (0.3, 1.7)], T27 + 0.8, v=0.45, turn=260, face0=360)
    ls.drive(d27, T27 + 0.8, d27.t1)
    a27 = d27.pose(d27.t1)[2]; ls.place(d27.t1 + 0.1, 0.3, 1.7, a27); ls.place(d27.t1 + 1.2, 0.3, 1.7, a27 + 180); ls.place(d27.t1 + 2.0, 0.3, DOCKP[1], a27 + 180)
    for k in range(3): m.at(T27 + 2.0 + k * 2.0, face=(k * 120) % 360)
    m.at(s("27-03") + 0.2, face=face_to(MC, (1.55, 1.93)), look=-10)
    m.at(s("27-04") + 0.2, look=-40)
    m.glow(w("27-05", "家具") - 0.2, 0.25, 0.6, g0=0.9); m.sigh(w("27-05", "家具") + 0.2)      # がっかり（一覧の sigh）
    ev(w("27-05", "家具") + 0.2, "pi_low", 0.5)
    if cut(cl, "S26a"):
        c, tg = cam_rig((1.8, -3.0, 2.4), (0.4, 0.8, 0.0), 26)
        cam_move(c, tg, s("26-01") - 0.8, e("26-05") + 0.6, (1.9, -3.1, 2.45), (1.2, -3.3, 2.1), (0.4, 0.8, 0.0), (0.6, 0.6, 0.0))
    elif cut(cl, "S27b"):     # スマホに寄る（3D のまま。2D の大きなスマホの絵はやめた）
        c, tg = cam_rig((1.57, 1.70, 1.0), (1.55, 1.97, 0.70), 44)
        cam_move(c, tg, s("27-02") - 0.2, e("27-04") + 1.0, (1.58, 1.68, 1.02), (1.565, 1.70, 1.0), (1.55, 1.97, 0.69), (1.55, 1.97, 0.69), 44, 45.5)
        dof(c, ph, 5.6)
    else:
        c, tg = cam_rig((1.4, -2.2, 1.6), (0.0, 0.4, 0.1), 28)
        cam_move(c, tg, s("27-01") - 0.8, e("27-02"), (1.5, -2.3, 1.7), (1.1, -1.9, 1.3), (0.0, 0.4, 0.1), (0.0, 0.3, 0.15))
        cam_move(c, tg, e("27-02"), e("27-05") + 1.5, (1.1, -1.9, 1.3), (0.55, -0.75, 0.55), (0.0, 0.3, 0.15), (0.0, 0.2, 0.25), 28, 40)
        dof(c, m.root, 4.0)
    track("maru", m.root, 0.42); track("lidar", ls.root, 0.15)


# ======================================================================== クリップの一覧
#   CUTS：カットの名前・組み立て・切り替わる時刻。切り替わる時刻＝その文の字幕が出る時刻（声の頭）
#   （4本目 v10「メインのテロップとそれ以外の切り替わりがズレてる」：絵は字幕と同じコマで替える。声より先に替えない）
#   組み立てでは、切り替わる時刻から 0.35 秒（章の変わり目は 0.6 秒）で溶かしてつなぐ。そのぶん前のカットを長めに描いておく
CUTS = [
    ("S01a", b_open, 0.0), ("S01b", b_open, s("01-03")), ("S02a", b_open, s("02-01")), ("S02b", b_open, s("02-05")),
    ("S03a", b_open, s("03-01")), ("S04a", b_open, s("04-01")), ("S05a", b_open, s("05-01")),
    ("S06a", b_old, s("06-01")), ("S06b", b_old, s("06-07")), ("S06c", b_old, s("06-09")),
    ("S07a", b_blind, s("07-01")), ("S07b", b_blind, s("07-02")), ("S07c", b_blind, s("07-03")), ("S08a", b_blind, s("08-01")),
    ("S09a", b_lidar, s("09-01")), ("S10a", b_lidar, s("10-01")), ("S11a", b_lidar, s("11-01")), ("S12a", b_lidar, s("12-01")),
    ("S13a", b_dark, s("13-01")), ("S14a", b_dark, s("14-01")), ("S15a", b_dark, s("15-01")), ("S15b", b_dark, s("15-02")), ("S15c", b_dark, s("15-04")),
    ("S16a", b_rug, s("16-01")), ("S16b", b_rug, s("16-03")), ("S16c", b_rug, s("16-05")), ("S17a", b_rug, s("17-01")), ("S17b", b_rug, s("17-03")), ("S17c", b_rug, s("17-07")),
    ("S18a", b_cam, s("18-01")), ("S19a", b_cam, s("19-01")), ("S20a", b_cam, s("20-01")), ("S21a", b_cam, s("21-01")),
    ("S22a", b_step, s("22-01")), ("S22b", b_step, s("22-04")), ("S23a", b_step, s("23-01")),
    ("S24a", b_avoid, s("24-01")), ("S25a", b_avoid, s("25-01")), ("S25c", b_ad, s("25-06")), ("S25d", b_avoid, s("25-07")), ("S25b", b_avoid, s("25-09")),
    ("S26a", b_end, s("26-01")), ("S27a", b_end, s("27-01")), ("S27b", b_end, s("27-02")), ("S27c", b_end, s("27-05")),
]
END_T = e("27-05") + 2.5
CLIPS = {}
for i, (nm, fn, tc) in enumerate(CUTS):
    t0 = max(0.0, tc - 0.1)
    t1 = (CUTS[i + 1][2] + 0.75) if i + 1 < len(CUTS) else END_T
    CLIPS[nm] = (fn, t0, t1)

if __name__ == "__main__" or True:
    if CLIPNAME == "--list":
        print(json.dumps({k: [round(v[1], 3), round(v[2], 3), round(c[2], 3)] for (k, v), c in zip(CLIPS.items(), CUTS)}))
    else:
        fn, t0, t1 = CLIPS[CLIPNAME]
        CLOCK["T0"] = t0
        fn(CLIPNAME)
        maru_bake_all(t1)          # まるロボの毎コマ（本物の体・決まりどおりの動き）
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None     # PC：--frames 0 99（この範囲だけ、1 コマずつ）
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
