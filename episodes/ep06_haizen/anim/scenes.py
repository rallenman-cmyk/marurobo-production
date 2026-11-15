# 6本目（配膳ロボット）：3D の場面を声の時刻に合わせて動かして描く
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 8] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   PC の本番：... -- <クリップ> <出力> --samples 48 --res 1920 1080 --frames 0 99 --gpu --video
#   クリップの一覧は下の CUTS（名前・場面の組み立て・切り替わる時刻＝その文の字幕が出る時刻）
#   場面の組み立て（b_*）は、まるロボ・先輩・人の動きをクリップに関係なく全部作り、カメラだけをクリップごとに選ぶ
#   部品は kit.py、時刻と動きの共通は core.py、間取りは plan.py（5本目の作り方を写した）
#   決まり（SKILL・制作バイブル）：3D の中に字を書かない／まるロボと先輩は喋らない（電子音・画面の顔・身ぶり）／
#     動きは言い終えてから／瞬間移動に見せない／カメラはいつもゆっくり動かす／
#     止まった物の点＝青緑・動く人の点＝橙・席の点＝白い丸（最後まで同じ表し方）
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
TRACK_ONLY = "--track" in _argv
WAIT = plan.WAIT
SEAT11, SEAT12, SEAT10 = plan.seat_point(11), plan.seat_point(12), plan.seat_point(10)
SVS = SV_S


def cut(cl, *names): return cl in names


def cam(loc, target, lens=35, t0=None, t1=None, loc1=None, target1=None, lens1=None):
    """カメラ（いつもゆっくり動かす：loc1・target1 があれば t0〜t1 で動く）"""
    c, tg = cam_rig(loc, target, lens)
    if t0 is not None:
        cam_move(c, tg, t0, t1, loc, loc1 or loc, target, target1 or target, lens, lens1 or lens)
    return c, tg


def cam_track(c, tg, t0, t1, fn, dt=0.25):
    """見る点を、動く物に合わせて動かす（fn(t) → (x, y, z)）"""
    t = t0
    while t <= t1 + 1e-6:
        key(tg, "location", t, fn(t), "LINEAR"); t += dt


def drive_end(pts, t_end, v=0.5, turn=90.0, face0=None):
    """t_end に着くように、道 pts を走る Drive を作る"""
    d0 = plan.Drive(pts, 0.0, v, turn, face0)
    return plan.Drive(pts, t_end - d0.t1, v, turn, face0)


def crowd(skip=()):
    """座っているお客さん（店の空気。顔は描かない）"""
    S = [(10, 'in', "#E8A04D", False), (10, 'out', "#5B8DB8", False), (11, 'out', "#9BBB59", False), (11, 'in', "#C0504D", False),
         (12, 'out', "#7E57C2", False), (20, 'in', "#4F81BD", False), (20, 'out', "#E57373", True), (21, 'out', "#F2C14E", False),
         (22, 'in', "#6D8C9E", False), (22, 'out', "#D98C5F", False)]
    P = {}
    for n, side, col, kid in S:
        if (n, side) in skip: continue
        P[(n, side)] = seated(n, side, col, kid=kid)
    return P


def maru_lie(M, t, d=0.45, back=False):
    """まるロボが床に転がる（横に倒れる）／起き上がる"""
    z0, z1 = M.z0, 0.5 * M.s * 0.0 + 0.13 / M.s if False else M.z0
    if not back:
        key(M.body, ("rotation_euler", 1), t, 0.0); key(M.body, ("rotation_euler", 1), t + d, R(88))
        key(M.body, ("location", 2), t, M.z0); key(M.body, ("location", 2), t + d, 0.52)
        ev(t + d, "land", 0.6)
    else:
        key(M.body, ("rotation_euler", 1), t, R(88)); key(M.body, ("rotation_euler", 1), t + d, 0.0)
        key(M.body, ("location", 2), t, 0.52); key(M.body, ("location", 2), t + d, M.z0)
        ev(t, "jump", 0.4)


def tray_item(sv, item, tray=1, t_show=None, t_hide=None):
    """先輩のトレーに料理を乗せる（item：'ramen'・'hamburg'）"""
    if item == "ramen": o = ramen(sv.d["trays"][tray], (0, 0, 0.012))["root"]
    else: o = hamburg(sv.d["trays"][tray], (0, 0, 0.012))
    if t_show is not None or t_hide is not None:
        hide_key(o, CLOCK["T0"] - 5, t_show is not None)
        if t_show is not None: hide_key(o, t_show, False)
        if t_hide is not None: hide_key(o, t_hide, True)
    return o


def table_item(n, item, t_show, toward=0.22):
    x, y = plan.TABLE[n]; sg = 1 if x > 0 else -1
    loc = (x - sg * toward, y, 0.742)
    o = ramen(None, loc)["root"] if item == "ramen" else hamburg(None, loc)
    show_between(o, t_show)
    ev(t_show, "clink", 0.5)
    return o


def aim_arm(arm, root_loc, root_rot_z, target):
    """腕（肩の empty。-Z が腕の向き）を、その時の体の向きのまま、目当て（世界の座標）へ向ける回転"""
    from mathutils import Vector, Matrix, Euler
    rz = Matrix.Rotation(root_rot_z, 3, 'Z')
    sh = Vector(root_loc) + rz @ Vector(arm.location)
    d = rz.inverted() @ (Vector(target) - sh)
    return tuple(d.to_track_quat('-Z', 'Y').to_euler())


def take_ramen(person_root, dr, t0, n=11):
    """座ったお客さん（通路がわ）が、体をひねって先輩のトレーのラーメンを受け取り、テーブルに置く。
       t0：体をひねり始める。+1.25 秒でつかむ（トレーの器は消え、手の器に替わる）、+2.8 秒でテーブルに置く"""
    x, y = plan.TABLE[n]; sg = 1 if x > 0 else -1
    sx, sy, sa = dr.pose(dr.t1)
    pr = person_root; base = pr.rotation_euler[2]; ploc = tuple(pr.location)
    # 腕 2 本（肩から。3本目の人には腕がないので足す）
    sm = mat("shirt_arm%d" % n, "#C0504D", rough=0.7); km = mat("skin", "#F1C7A5", rough=0.55)
    arms = []
    for ax in (-0.24, 0.24):
        ap = empty((ax, -0.02, 1.08)); ap.parent = pr
        cyl(sm, (0, 0, -0.22), 0.05, 0.44, parent=ap, verts=12); sphere(km, (0, 0, -0.47), 0.055, parent=ap, seg=12)
        key(ap, "rotation_euler", t0 - 5, (R(-35), 0, 0)); arms.append(ap)   # ふだんは手をテーブルの方へ少し出している
    from mathutils import Vector
    dx, dy = sx - ploc[0], sy - ploc[1]
    want = math.atan2(-dx, dy)               # 前（-y）を先輩の方へ向ける回転
    turn = max(-R(80), min(R(80), (want - base + math.pi) % (2 * math.pi) - math.pi))   # 体は 80 度までひねる
    def dist_to(a): return (Vector(ploc) + __import__("mathutils").Matrix.Rotation(base + turn, 3, 'Z') @ Vector(a.location) - Vector((sx, sy, 0.7))).length
    near = min(arms, key=dist_to)            # 先輩に近い方の腕
    bowl_tray = (sx, sy, 0.70); bowl_table = (x - sg * 0.22, y, 0.76)
    key(pr, ("rotation_euler", 2), t0, base); key(pr, ("rotation_euler", 2), t0 + 0.8, base + turn, "BEZIER")
    key(near, "rotation_euler", t0 + 0.3, (R(-35), 0, 0)); key(near, "rotation_euler", t0 + 1.2, aim_arm(near, ploc, base + turn, bowl_tray))
    key(near, "rotation_euler", t0 + 1.45, aim_arm(near, ploc, base + turn, bowl_tray))
    key(pr, ("rotation_euler", 2), t0 + 1.45, base + turn); key(pr, ("rotation_euler", 2), t0 + 2.45, base, "BEZIER")
    key(near, "rotation_euler", t0 + 2.05, aim_arm(near, ploc, base + turn * 0.4, (ploc[0] + sg * 0.15, ploc[1] + (0.42 if sy > ploc[1] else -0.42), 0.95)))
    key(near, "rotation_euler", t0 + 2.45, aim_arm(near, ploc, base, (x - sg * 0.3, y, 0.9)))
    key(near, "rotation_euler", t0 + 2.8, aim_arm(near, ploc, base, bowl_table))
    key(near, "rotation_euler", t0 + 3.5, (R(-35), 0, 0))
    # 器：トレーの上 → 手（腕の先）→ テーブル。手の先を毎 0.1 秒で追う
    o = ramen(None, bowl_tray)["root"]
    key(o, "location", t0 - 5, bowl_tray); key(o, "location", t0 + 1.25, bowl_tray)
    # 体の中を通らないように、肩の横 → テーブルの角の上を回って置く
    side = 1 if sy > ploc[1] else -1
    pts = [(t0 + 1.25, bowl_tray), (t0 + 1.6, (sx + sg * 0.14, sy, 0.86)), (t0 + 2.05, (ploc[0] + sg * 0.15, ploc[1] + side * 0.42, 0.95)),
           (t0 + 2.45, (x - sg * 0.3, y + side * 0.2, 0.9)), (t0 + 2.8, bowl_table)]
    for t, p in pts: key(o, "location", t, p, "BEZIER")
    show_between(o, t0 + 1.25)
    ev(t0 + 1.25, "rub", 0.35); ev(t0 + 2.8, "clink", 0.5)
    return o


# ======================================================================== S01〜S04：人だらけの通路を、ラーメンが走ってくる
def b_open(cl):
    restaurant(); P = crowd()
    M = Maru((-0.15, 0.3, 0), face=0); track("maru", M.root, 0.4)
    # 01-02：きょろきょろしながら見て回る（歩いて移る）
    M.at(s("01-02") - 0.3, face=0)
    M.walk(s("01-02") + 0.2, s("01-02") + 2.2, (0.0, 0.9))
    M.at(s("01-02") + 2.6, face=-50); M.at(e("01-02") - 0.2, face=50); M.at(e("01-02") + 0.6, face=0)
    M.at(w("02-01", "奥から"), face=180)        # 奥を向く
    # 人：店員さんと、お客さん（ロボの道に入らない所を歩く）
    st = Wk(walker((-0.32, -1.9), 0, shirt="#2B2F36", apron=True))
    t_ = st.walk(0.3, [(-0.32, -1.9), (-0.32, -1.3), (-0.62, -1.85)], v=0.6); st.at(t_ + 0.4, -0.62, -1.85, -90)
    cu = Wk(walker((0.25, -0.2), 0, shirt="#7FB3A8"))
    t_ = cu.walk(0.6, [(0.25, -0.2), (0.25, -0.75), (0.62, -1.05)], v=0.5); cu.at(t_ + 0.5, 0.62, -1.05, 90)
    cu2 = Wk(walker((-2.9, -2.65), -90, shirt="#E9B48A", pants="#4A4038"))
    cu2.walk(6.0, [(-2.9, -2.65), (2.9, -2.65)], v=0.9)
    # 先輩：台所の奥から出てきて、まるロボの前でぴたっ
    sv = Sv(senpai_serve((0, 4.2), 0)); track("senpai", sv.root, 1.2); track("tray", sv.d["trays"][1], 0.05)
    tray_item(sv, "ramen", 1, t_hide=s("03-05") - 0.9 + 1.25)
    ts = w("03-01", "ぴたっ")
    d1 = plan.Drive([(0, 4.2), (0, 2.2)], s("02-01") + 0.3, v=2.0 / (ts - 4.0 - s("02-01") - 0.3), face0=0)
    sv.drive(d1); d2 = plan.Drive([(0, 2.2), (0, 1.6)], d1.t1, v=0.6 / (ts - d1.t1), face0=0); sv.drive(d2, motor=False)
    sv.spin(CLOCK["T0"] - 1, 70)
    ev(ts, "stop", 0.6)
    sv.set_face(s("03-02") - 0.1, "dots"); sv.set_face(s("03-03"), "normal")
    M.hop(ts + 0.1, h=0.12, d=0.35, sound=False); ev(ts + 0.1, "pi", 0.4)
    # 03-03：少し下がって、横によける → 奥の席（11 番）でぴたり
    tb = s("03-03") + 0.3
    sv.place(tb, 0, 1.6, 0); sv.place(tb + 1.0, 0, 1.85, 0, "BEZIER")
    # v2：通路のまん中寄り（x 0.34）を通る。0.45 だと、いすの背にめりこんだ（v1 0:34）
    STOP11 = (0.32, 0.2)   # v2：テーブルの角の横で止まる（真後ろだと、受け取るお客さんが先輩に隠れる）
    R11 = [(0, 1.85), (0.34, 1.35), STOP11]
    d3 = drive_end(R11, w("03-04", "ぴたり"), v=0.42, turn=120, face0=0)
    d3 = plan.Drive(R11, max(tb + 1.2, d3.t0), 0.42, 120, 0)
    sv.drive(d3); ev(d3.t1, "stop", 0.5)
    M.at(d3.t0 + 1.0, face=180); M.at(d3.t0 + 3.0, face=320)
    # v2：お客さんが、トレーのラーメンを手で受け取って、テーブルに置く（v1 0:44「ラーメンは人が受け取る感じにして」）
    take_ramen(P[(11, 'in')], d3, s("03-05") - 0.9)
    sv.piron(e("03-05") + 0.2, "happy"); sv.set_face(e("04-01"), "normal")
    # 04-05 のあと：台所の出口へ戻る
    d4 = plan.Drive([STOP11, (0.25, 0.5), (0.25, 1.6), (0.0, 2.75)], s("04-05") + 0.2, 0.55, 120)
    sv.drive(d4)
    M.walk(s("04-04") + 0.4, s("04-04") + 2.0, (-0.25, 0.9))
    if cut(cl, "S01a"): cam((0.3, -3.1, 1.55), (0.0, 0.9, 0.55), 24, 0.0, s("01-02") + 0.5, (0.25, -2.7, 1.45), (0.0, 1.0, 0.5))
    if cut(cl, "S01b"): cam((0.38, -0.35, 0.5), (0.0, 0.8, 0.25), 32, s("01-02") - 0.2, s("02-01"), (0.35, -0.2, 0.48), (0.0, 0.9, 0.25))
    if cut(cl, "S02a"):
        c, tg = cam((0.35, -0.6, 0.45), (0.0, 2.6, 0.75), 30)
        cam_track(c, tg, s("02-01") - 0.5, s("02-02") + 0.8, lambda t: (d1.pose(t)[0] * 0.5, max(1.9, d1.pose(t)[1]), 0.7))
    if cut(cl, "S02b"):
        c, tg = cam((0.45, 1.2, 1.05), (0.0, 3.0, 0.8), 34)
        cam_track(c, tg, s("02-02") - 0.5, s("02-03") + 0.8, lambda t: (sv_pose(d1, d2, t)[0], sv_pose(d1, d2, t)[1], 0.8))
        key(c, "location", s("02-02") - 0.5, (0.45, 1.2, 1.05)); key(c, "location", s("02-03") + 0.8, (0.45, 0.9, 1.0))
    if cut(cl, "S02c"): cam((-0.4, 0.45, 0.85), (0.0, 2.2, 0.7), 30, s("02-03") - 0.2, s("03-01"), (-0.38, 0.55, 0.8), (0.0, 1.9, 0.65))
    if cut(cl, "S03a"): cam((1.0, 0.55, 0.62), (0.0, 1.25, 0.45), 28, s("03-01") - 0.2, s("03-02"), (0.95, 0.6, 0.6), (0.0, 1.25, 0.5))
    if cut(cl, "S03b"): cam((0.32, 0.05, 0.62), (0.0, 1.45, 0.72), 26, s("03-02") - 0.2, s("03-03"), (0.3, 0.12, 0.6), (0.0, 1.45, 0.75))
    if cut(cl, "S03c"): cam((-0.45, 3.1, 1.85), (0.2, 0.4, 0.4), 26, s("03-03") - 0.2, e("03-04"), (-0.3, 2.9, 1.8), (0.25, 0.0, 0.4))
    # v2：先輩のトレーと、受け取るお客さんが両方見える、通路の向こうがわから
    if cut(cl, "S03d"): cam((0.3, 1.45, 1.75), (0.8, -0.3, 0.8), 24, s("03-05") - 0.2, s("04-01"), (0.32, 1.4, 1.72), (0.82, -0.3, 0.8))   # v2 点検：奥がわの横から（後ろからだと、テーブルに置く所がお客さんの体に隠れる）
    if cut(cl, "S04a"): cam((0.35, -3.1, 1.6), (0.0, 0.3, 0.5), 22, s("04-01") - 0.2, e("04-05") + 2.0, (0.25, -2.8, 1.5), (0.0, 0.5, 0.5))


def sv_pose(d1, d2, t):
    return d1.pose(t) if t <= d1.t1 else d2.pose(t)


# ======================================================================== S05〜S07：先輩に会う
def b_meet(cl):
    restaurant(); crowd()
    sv = Sv(senpai_serve(WAIT, 0)); track("senpai", sv.root, 1.2); track("head", sv.d["head"], 0.0); track("tray", sv.d["trays"][1], 0.0)
    track("lens", sv.d["lenses"][0], 0.0); track("window", sv.d["lidwin"], 0.0)
    d0 = plan.Drive([(0.25, 1.6), (0.0, 2.75)], s("05-01") - 2.2, 0.55, 120)
    sv.drive(d0); sv.spin(CLOCK["T0"] - 1, 120)
    ev(d0.t1, "stop", 0.5)
    sv.place(d0.t1 + 0.05, 0.0, 2.75, d0.pose(d0.t1)[2]); sv.place(d0.t1 + 1.3, 0.0, 2.75, 0.0, "BEZIER")   # くるっと前を向く
    M = Maru((-0.25, 0.9, 0), face=180); track("maru", M.root, 0.4)
    M.walk(s("05-01") + 0.3, s("05-01") + 2.4, (0.0, 1.95))
    M.at(s("05-01") + 2.8, face=180)
    M.hop(w("05-02", "ピポ") - 0.1, h=0.18, d=0.4, sound=False); ev(w("05-02", "ピポ"), "pipo", 0.6)
    sv.piron(w("05-03", "ピロン"), "happy")
    sv.set_face(s("05-05"), "normal")
    # 06：まるロボが先輩のまわりを回ってのぞく（歩いて移る）
    M.walk(s("06-01") + 0.2, s("06-01") + 2.6, (0.6, 2.2))
    M.walk(s("06-02") + 0.3, s("06-02") + 2.5, (0.35, 1.95)); M.at(s("06-02") + 2.8, face=150, look=12)
    M.at(e("06-02") + 0.3, look=0)
    M.walk(s("06-03") + 0.5, s("06-03") + 2.5, (-0.1, 2.0)); M.at(s("06-03") + 2.8, face=180)
    # 07：店の引きの絵（ほかの先輩も働いている）
    for (x, y, a) in ((-0.32, -0.25, 0), (0.32, -1.85, 180)):
        o = senpai_serve((x, y), a)
        for k, g in o["face"].items(): g.hide_render = (k != "normal")
        ramen(o["trays"][1], (0, 0, 0.012), steam=False)
    sv.piron(s("07-03") + 0.4, "happy", sound=False); M.hop(s("07-03") + 0.6, h=0.15, d=0.4)
    if cut(cl, "S05a"): cam((-0.38, 0.75, 0.8), (0.0, 2.4, 0.7), 28, s("05-01") - 0.2, s("05-03"), (-0.33, 0.85, 0.78), (0.0, 2.45, 0.7))
    # v2：まるロボの体も入るように、通路の横から少し引いて（v1 1:11「まるロボもう少し体うつるように」）
    if cut(cl, "S05b"): cam((0.32, 0.3, 0.78), (0.0, 2.4, 0.56), 24, s("05-03") - 0.2, s("06-01"), (0.3, 0.4, 0.78), (0.0, 2.4, 0.58))
    if cut(cl, "S06a"):   # 先輩のまわりを、ゆっくり（上 → トレー → おなかの前 → 足もと）。左の通路から
        c, tg = cam((-0.45, 1.65, 1.45), (0.0, 2.75, 1.1), 30)
        cam_move(c, tg, s("06-01") - 0.2, e("06-01"), (-0.45, 1.65, 1.45), (-0.42, 1.85, 1.0), (0.0, 2.75, 1.1), (0.0, 2.75, 0.75))
        cam_move(c, tg, e("06-01"), w("06-02", "足もと") - 0.3, (-0.42, 1.85, 1.0), (-0.38, 1.9, 0.62), (0.0, 2.75, 0.75), (0.0, 2.68, 0.42))
        cam_move(c, tg, w("06-02", "足もと") - 0.3, e("06-02") + 0.3, (-0.38, 1.9, 0.62), (-0.35, 1.95, 0.32), (0.0, 2.68, 0.42), (0.0, 2.6, 0.22))
        cam_move(c, tg, e("06-02") + 0.3, s("07-01"), (-0.35, 1.95, 0.32), (-0.4, 1.4, 0.8), (0.0, 2.6, 0.22), (0.0, 2.5, 0.6))
    if cut(cl, "S07a"): cam((-0.3, -3.1, 1.7), (0.1, 0.4, 0.4), 22, s("07-01") - 0.2, s("07-03"), (-0.2, -2.85, 1.6), (0.1, 0.6, 0.4))
    if cut(cl, "S07b"): cam((0.4, 0.85, 0.75), (0.0, 2.45, 0.65), 30, s("07-03") - 0.2, s("08-01"), (0.38, 0.95, 0.75), (0.0, 2.45, 0.68))


# ======================================================================== S08：番号を押す
D_ORDER = None


def order_drive():
    """08-04 で走り出し、09-04「止まれば」で 12 番の席の点に着く（上から見た絵と同じ動き）"""
    t0 = s("08-04") + 0.4
    d0 = plan.Drive(plan.ROUTE12, 0.0, 0.5, 90, 0)
    v = 0.5 * d0.t1 / max(1.0, (w("09-04", "止まれば") - t0))
    return plan.Drive(plan.ROUTE12, t0, max(0.25, v * 1.15), 70, 0)


def b_order(cl):
    restaurant(); crowd()
    sv = Sv(senpai_serve(WAIT, 0)); track("senpai", sv.root, 1.2); track("head", sv.d["head"], 0.0); track("tray", sv.d["trays"][1], 0.0)
    sv.spin(CLOCK["T0"] - 1, 200)
    st = Wk(walker((-0.55, 3.0), 120, shirt="#2B2F36", apron=True)); track("staff", st.root, 1.7)
    st.at(CLOCK["T0"], -0.55, 3.0, 120)
    tray_item(sv, "hamburg", 1, t_show=w("08-02", "置きました") - 0.2)
    st.arm_up(s("08-02") + 0.1, 1, 70, 0.6); key(st.w.arms[1], ("rotation_euler", 0), w("08-02", "置きました") + 0.3, 0.0)
    st.arm_up(w("08-03", "押します") - 0.6, 1, 95, 0.5); key(st.w.arms[1], ("rotation_euler", 0), w("08-03", "12番") + 0.6, 0.0)
    ev(w("08-03", "押します"), "click", 0.6); ev(w("08-03", "12番"), "click", 0.6)
    M = Maru((0.45, 2.0, 0), face=160); track("maru", M.root, 0.4)
    M.at(w("08-03", "画面") , look=12); M.at(e("08-03"), look=0)
    dr = order_drive(); sv.drive(dr)
    sv.piron(s("08-04") + 0.05, "happy"); sv.set_face(s("08-04") + 1.5, "normal")
    M.at(dr.t0 + 0.8, face=200)
    if cut(cl, "S08a"): cam((0.42, 1.0, 1.1), (-0.15, 2.8, 1.0), 30, s("08-01") - 0.2, s("08-03"), (0.4, 1.1, 1.1), (-0.15, 2.8, 1.0))
    if cut(cl, "S08b"): cam((0.55, 1.95, 1.35), (0.0, 2.8, 1.18), 30, s("08-03") - 0.2, s("08-04"), (0.5, 2.0, 1.33), (0.0, 2.8, 1.18))
    if cut(cl, "S08c"):
        c, tg = cam((0.42, 0.3, 0.9), (0.0, 2.6, 0.7), 28)
        cam_track(c, tg, s("08-04") - 0.3, s("09-01") + 1.2, lambda t: (dr.pose(t)[0], dr.pose(t)[1], 0.7))


# ======================================================================== S09〜S10：上から見た店の地図・席の点・道
def b_map(cl):
    restaurant(ceiling=False, top_view=True); crowd()
    sv = Sv(senpai_serve(WAIT, 0)); track("senpai", sv.root, 0.0)
    dr = order_drive(); sv.drive(dr); sv.spin(CLOCK["T0"] - 1, 200)
    tray_item(sv, "hamburg", 1, t_hide=dr.t1 + 2.5)
    table_item(12, "hamburg", dr.t1 + 2.5)
    # 席の点（白い丸）：「白い丸の点」で全部ぽんと出る。12 番は黄色い輪で
    pts = {}
    for k, n in enumerate(sorted(plan.TABLE)):
        x, y = plan.seat_point(n)
        # v2：白い通路の上でも見えるように、紺のふちどりを下に敷いて、少し大きく（v1 2:31「白い点もう少し視認性良く」）
        o = ring_marker((x, y), r=0.2, col=WHITE_PT, w=0.05, z=0.03)
        bd = cyl(mat("seatbase", "#1F3550", rough=0.6), (0, 0, 0), 0.29, 0.012, verts=48); bd.parent = o; bd.location = (0, 0, -0.012); bd.visible_shadow = False
        d_ = cyl(flat_mat("seatdot", WHITE_PT, 3.0), (0, 0, 0), 0.1, 0.008, verts=24); d_.parent = o; d_.location = (0, 0, 0.0)
        t_ = w("09-03", "白い丸") + 0.08 * k
        show_between(o, t_); scale_pop(o, t_)
        track("seat%d" % n, o, 0.0); pts[n] = o
    ev(w("09-03", "白い丸"), "pop", 0.6)
    r12 = ring_marker(SEAT12, r=0.27, col="#FFD24A", w=0.04, z=0.022); show_between(r12, w("09-04", "ここで")); scale_pop(r12, w("09-04", "ここで"))
    # 10：いまいる所から点までの道（黄色い線が伸びる）
    # v2：道は濃い青で太く（黄色は白い通路の上で見えなかった。v1 2:39「道の色も見えにくい」）
    ln = line_path("route", plan.ROUTE12, col="#1565D8", width=0.075, z=0.035, emit=0.6)
    key(ln.data, "bevel_factor_end", CLOCK["T0"] - 1, 0.0); key(ln.data, "bevel_factor_end", w("10-01", "いまいる所") , 0.0); key(ln.data, "bevel_factor_end", e("10-01") + 0.3, 1.0)
    ev(w("10-01", "いまいる所"), "rise", 0.5)
    show_between(ln, w("10-01", "いまいる所") - 0.1)
    st = ring_marker(WAIT, r=0.2, col="#FFD24A", w=0.018, z=0.022); show_between(st, w("10-01", "いまいる所")); scale_pop(st, w("10-01", "いまいる所"))
    # 10-03〜：道をなぞる光の粒（この道に沿って走る）
    dot = sphere(flat_mat("routedot", "#7FB2FF", 4.0), (WAIT[0], WAIT[1], 0.1), 0.09)
    d2 = plan.Drive(plan.ROUTE12, s("10-03") + 0.2, 1.6, 400, 0)
    show_between(dot, s("10-03") + 0.2, d2.t1 + 0.6)
    t = d2.t0
    while t <= d2.t1 + 1e-6:
        x, y, _ = d2.pose(t); key(dot, "location", t, (x, y, 0.08), "LINEAR"); t += 0.1
    # 10-04〜05：「自分はどこ？」で先輩に黄色い輪がふわっと
    q = ring_marker(SEAT12, r=0.36, col="#FFD24A", w=0.018, z=0.03); show_between(q, w("10-05", "自分が")); scale_pop(q, w("10-05", "自分が"))
    if cut(cl, "S09a"): cam_top_move(cam_top((0.0, 0.1, 9.6), 24), s("09-01") - 0.3, e("10-05") + 1.0, (0.0, 0.1, 9.6), (0.0, 0.0, 9.0))


# ======================================================================== S10b：道に沿って走る → 止まって「いまどこ？」（v2：上からの絵が続きすぎた。v1 2:53）
def b_where(cl):
    restaurant(); crowd()
    sv = Sv(senpai_serve(WAIT, 0)); track("senpai", sv.root, 1.2); track("head", sv.d["head"], 0.0)
    sv.spin(CLOCK["T0"] - 1, 260)
    tray_item(sv, "hamburg", 1)
    dr = plan.Drive([WAIT, (0.0, 1.6), (0.0, -0.2)], s("10-03") + 0.1, 0.45, 90, 0)
    sv.hold(CLOCK["T0"] - 1, pose=(WAIT[0], WAIT[1], 0.0)); sv.drive(dr); ev(dr.t1, "stop", 0.5)
    # 10-05：止まって、首をかしげるように左右を向く（自分はどこ？）
    t_ = w("10-05", "自分が")
    sv.place(t_ - 0.1, 0.0, -0.2, 0.0); sv.place(t_ + 0.7, 0.0, -0.2, 28.0, "BEZIER"); sv.place(t_ + 1.6, 0.0, -0.2, -28.0, "BEZIER"); sv.place(t_ + 2.4, 0.0, -0.2, 0.0, "BEZIER")
    sv.set_face(t_, "dots"); sv.set_face(e("10-05") + 0.6, "normal")
    if cut(cl, "S10b"):
        c, tg = cam((0.42, -1.75, 0.95), (0.0, 1.6, 0.8), 30)
        cam_track(c, tg, s("10-03") - 0.3, e("10-05") + 1.0, lambda t: (0.0, max(-0.2, dr.pose(t)[1]), 0.78))
        key(c, "location", s("10-03") - 0.3, (0.42, -1.75, 0.95)); key(c, "location", e("10-04"), (0.4, -1.6, 0.9)); key(c, "location", e("10-05") + 1.0, (0.36, -1.35, 1.05))


# ======================================================================== S11：天井の目印
def b_ceil(cl):
    R_ = restaurant(); crowd()
    sv = Sv(senpai_serve(SEAT12, 180)); track("senpai", sv.root, 1.2)
    sv.spin(CLOCK["T0"] - 1, 220)
    dr = plan.Drive([SEAT12, (0.0, -1.2), (0.0, 2.0)], s("11-01") + 0.3, 0.3, 90, 180)
    sv.drive(dr)
    # 上を向いたカメラから天井へ伸びる光（11-03 から）
    bm = empty((0, 0, 0)); bm.parent = sv.d["upcam"]
    b_ = cyl(glow_mat("upbeam", "#BFF7EF", 3.0), (0, 0, 0.7), 0.006, 1.4, parent=bm, verts=8); b_.visible_shadow = False
    show_between(bm, w("11-03", "上を向いた"), e("11-04") + 0.3)
    # 目印が光る：先輩がその下を通るとき（11-02「目印のシール」で全部ぽっと光ってから）
    for (mx, my), o in zip(plan.CEIL_MARKS, R_["marks"]):
        m = o.data.materials[0]
        emit_key(m, CLOCK["T0"] - 1, 0.0); emit_key(m, w("11-02", "目印"), 0.0); emit_key(m, w("11-02", "目印") + 0.3, 2.5); emit_key(m, e("11-02") + 0.5, 0.4)
        if abs(mx) < 0.7:
            t = dr.t0
            while t < dr.t1:
                x, y, _ = dr.pose(t)
                if abs(y - my) < 0.25 and t > w("11-03", "上を向いた"):
                    emit_key(m, t - 0.4, 0.4); emit_key(m, t, 6.0); emit_key(m, t + 0.6, 0.4); break
                t += 0.1
    ev(w("11-02", "目印"), "pop", 0.5)
    # 11-05：まるロボも見上げて……ころん
    M = Maru((-0.35, 0.9, 0), face=32); track("maru", M.root, 0.4)
    M.at(s("11-05") + 0.2, look=0); M.at(w("11-05", "見上げて") + 0.4, look=35)
    t_ = w("11-05", "ころん") - 0.1
    key(M.body, ("rotation_euler", 0), t_ - 0.3, R(-35)); key(M.body, ("rotation_euler", 0), t_ + 0.35, R(-95))
    key(M.body, ("location", 2), t_ - 0.3, M.z0); key(M.body, ("location", 2), t_ + 0.35, 0.52)
    ev(t_ + 0.35, "land", 0.6)
    if cut(cl, "S11a"):
        c, tg = cam((0.45, -0.6, 0.35), (0.0, 0.2, 2.6), 18, s("11-01") - 0.2, e("11-04"), (0.42, -0.2, 0.35), (0.0, 1.0, 2.6))
    if cut(cl, "S11b"): cam((0.2, 0.05, 0.4), (-0.35, 0.9, 0.3), 32, s("11-05") - 0.2, s("12-01"), (0.18, 0.12, 0.38), (-0.35, 0.9, 0.25))


# ======================================================================== S12：まわりの形と地図を見比べる（上から）
def b_shape(cl):
    restaurant(ceiling=False, top_view=True); crowd()
    pos = (0.0, 0.35)
    sv = Sv(senpai_serve(pos, 0)); track("senpai", sv.root, 0.0); sv.spin(CLOCK["T0"] - 1, 230)
    # 地図（うすい青緑の点）：通路の何か所かから見える点を全部
    S = plan.segments(); mp = set()
    for yy in (-2.4, -1.2, 0.0, 1.2, 2.4):
        for k in range(720):
            h = plan.ray(0.0, yy, math.radians(k * 0.5), S, 7.0)
            if h: mp.add((round(h[1][0] / 0.04) * 0.04, round(h[1][1] / 0.04) * 0.04))
    t_map = s("12-01a") + 0.3
    pc, pm = point_cloud("map", [(x, y, t_map + 0.002 * i) for i, (x, y) in enumerate(sorted(mp))], col=TEAL, radius=0.045, z=0.05, base=1.6, pop=3.0, decay=4.0, t_offset=CLOCK["T0"])
    # v3：いま見えている形を地図に重ねる所は 2D の図にした（overlays.py の shapematch。v2 3:31「分かりにくい・動きも早い」）。3D は地図の点と先輩だけ
    t_o = s("12-02"); t_k = e("12-02c")
    ev(w("12-02b", "合わない"), "click", 0.35); ev(w("12-02b", "も……合") + 0.15, "click", 0.35); ev(w("12-02c", "ぴったり") + 0.35, "snap", 0.6)   # 図の × × ✓ の音
    r_ = ring_marker(pos, r=0.36, col="#FFD24A", w=0.03, z=0.03); show_between(r_, t_k); scale_pop(r_, t_k)
    # 12-03：先輩に寄っていく（このあと、先輩の目をのぞく）
    if cut(cl, "S12a"):
        cc = cam_top((0.0, 0.2, 7.8), 24)
        cam_top_move(cc, s("12-01") - 0.3, t_o, (0.0, 0.2, 7.8), (0.0, 0.25, 6.4))
        cam_top_move(cc, t_o, t_k + 0.4, (0.0, 0.25, 6.4), (0.0, 0.3, 5.2))
        cam_top_move(cc, s("12-03"), e("12-03") + 1.0, (0.0, 0.3, 5.2), (0.0, 0.35, 2.6))


# ======================================================================== S13：回る光の物差し
def b_lidar(cl):
    restaurant(); crowd()
    pos = (0.0, 0.6)
    sv = Sv(senpai_serve(pos, 0)); track("senpai", sv.root, 1.2); track("window", sv.d["lidwin"], 0.0)
    sv.spin(CLOCK["T0"] - 1, 240, rps=0.5)
    # 光の線（回る頭から、まわりへ。13-03「光を当てて」から）
    for k in range(3):
        bm = beam(sv.d["spin"], length=2.6, col=TEAL, r=0.004, strength=8.0); bm.rotation_euler = (0, 0, R(120 * k))
        show_between(bm, w("13-03", "光を当てて"))
    # 当たった所に点（壁・脚）
    S = plan.segments(); P_ = []
    t0 = w("13-03", "返ってきた")
    for i in range(400):
        t = t0 + i * 0.012; a = -math.pi / 2 + 2 * math.pi * 0.5 * t + R(120 * (i % 3))
        h = plan.ray(pos[0], pos[1], a, S, 2.6)
        if h: P_.append((h[1][0], h[1][1], t))
    point_cloud("hits", P_, col=TEAL, radius=0.02, base=1.8, pop=6.0, decay=6.0, t_offset=CLOCK["T0"])
    M = Maru((0.55, 0.15, 0), face=130); track("maru", M.root, 0.4)
    M.at(s("13-02") + 0.5, look=-12); key(M.body, ("location", 2), s("13-02") + 0.5, M.z0); key(M.body, ("location", 2), s("13-02") + 1.0, M.z0 - 0.08)
    if cut(cl, "S13a"): cam((-0.35, -0.75, 0.95), (0.0, 0.6, 0.5), 28, s("13-01") - 0.2, s("13-02"), (-0.32, -0.6, 0.88), (0.0, 0.6, 0.45))
    if cut(cl, "S13b"): cam((0.45, -0.15, 0.36), (0.0, 0.6, 0.3), 34, s("13-02") - 0.2, s("14-01"), (0.45, -0.3, 0.5), (0.0, 0.6, 0.28), 26)


# ======================================================================== S14〜S16：先輩の目で見たファミレス（暗い中の点）
def dark_world(robot_dim=True):
    world("#000000", 0.0)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5)); s_ = bpy.context.object; s_.data.energy = 0.15
    plane(mat("darkfloor", "#05080C", rough=0.9), (0, 0.1, 0), (7.2, 6.6))


def walk_pos(pts, t0, v, t):
    """歩く人の場所と向き（Wk.walk と同じ計算。足の点を出すため）"""
    tt = t0
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1]); t1 = tt + d / v
        if t <= t1 or i == len(pts) - 2:
            k = max(0.0, min(1.0, (t - tt) / max(1e-6, t1 - tt)))
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k; y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k
            return x, y, math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
        tt = t1
    return pts[-1][0], pts[-1][1], 0.0


def feet(x, y, hd, t, moving=True):
    """足 2 本の円（光の物差しの高さ）。歩いているときは前後に開く"""
    sw = 0.12 * math.sin(t * 6.0) if moving else 0.0
    px, py = -math.sin(hd), math.cos(hd); fx, fy = math.cos(hd), math.sin(hd)
    return [(x + px * 0.1 + fx * sw, y + py * 0.1 + fy * sw, 0.065), (x - px * 0.1 - fx * sw, y - py * 0.1 - fy * sw, 0.065)]


DARK_PEOPLE = []   # (道, 歩き出す時刻, 速さ)


def dark_people():
    """人ごとの歩く区間 [(道, 歩き出す時刻, 速さ), …]"""
    return [[([(-2.9, 0.55), (2.9, 0.55)], s("14-04") - 1.5, 0.55)],                                    # 通路を横切る人（14-04「この橙の点」）
            [([(0.25, -2.8), (0.25, -0.8), (0.9, -0.95)], s("14-01") + 0.5, 0.5)],                      # 手前から歩いてきて、席へ
            [([(-0.95, -0.25), (-0.15, -0.2)], s("16-01") - 3.5, 0.45), ([(-0.15, -0.2), (-0.95, -1.4)], e("16-04"), 0.45)]]   # 通路に立ち止まる人（16 章）


def legs_pos(legs, t):
    cur = None
    for L in legs:
        if t >= L[1]: cur = L
    if cur is None:
        p0, p1 = legs[0][0][0], legs[0][0][1]
        return p0[0], p0[1], math.atan2(p1[1] - p0[1], p1[0] - p0[0]), False
    x, y, hd = walk_pos(cur[0], cur[1], cur[2], t)
    d_ = sum(math.dist(cur[0][i], cur[0][i + 1]) for i in range(len(cur[0]) - 1))
    return x, y, hd, t < cur[1] + d_ / cur[2]


def b_dark(cl, maru_lying=False):
    dark_world()
    pos0 = (0.0, 1.7)
    sv = Sv(senpai_serve(pos0, 0)); track("senpai", sv.root, 0.6)
    for o in [sv.root] + list(sv.root.children_recursive):
        for ms in getattr(o, "material_slots", []):
            pass
    sv.spin(CLOCK["T0"] - 1, 300, rps=1.0)
    # 先輩の動き：14〜15 は止まって見ている。16：近づくと遅く → ぴたっ → よける
    t_stop = w("16-02", "ぴたっ")
    da = plan.Drive([pos0, (0.0, 1.0)], s("16-01") - 0.4, 0.5, 90, 0)
    db = plan.Drive([(0.0, 1.0), (0.0, 0.55)], da.t1, 0.45 / max(0.5, t_stop - da.t1), 90, 0)
    # v2：よける道を通路のまん中寄りに（x 0.42 だと、いすの脚の点に重なって見えた。v1 4:48）
    dc = plan.Drive([(0.0, 0.55), (0.3, 0.2), (0.3, -0.9), (0.12, -1.6)], s("16-03") + 0.1, 0.4, 120, 0)
    sv.hold(CLOCK["T0"], pose=(pos0[0], pos0[1], 0.0)); sv.drive(da); sv.drive(db, motor=False); sv.drive(dc)
    ev(t_stop, "stop", 0.6)

    def pose_at(t):
        if t < da.t0: return pos0
        if t <= da.t1: return da.pose(t)[:2]
        if t <= db.t1: return db.pose(t)[:2]
        if t < dc.t0: return db.pose(db.t1)[:2]
        return dc.pose(t)[:2]
    PP = dark_people()

    def people(t):
        C = []
        for legs in PP:
            x, y, hd, mv = legs_pos(legs, t)
            C += feet(x, y, hd, t, mv)
        return C
    # まるロボ（止まっている＝青緑の点）。18 章の小窓では、床に転がっていて見えない
    MP = (0.5, 2.15) if not maru_lying else (0.0, 0.2)
    S = plan.segments() + ([] if maru_lying else plan._box(MP[0], MP[1], 0.12))
    t0 = s("14-02") - 0.2 if not maru_lying else CLOCK["T0"]
    t1 = (e("16-04") + 1.0) if not maru_lying else CLOCK["T0"] + 8.0
    still, moving = plan.scan(pose_at if not maru_lying else (lambda t: (0.0, 0.62)), t0, t1, rot_per_s=2.0, rays=150, S=S, people=people if not maru_lying else None, maxd=4.5)
    point_cloud("still", still, col=TEAL, radius=0.035, base=2.0, pop=6.0, decay=8.0, life=4.0, t_offset=CLOCK["T0"])
    if moving: point_cloud("moving", moving, col=ORANGE_PT, radius=0.045, base=3.0, pop=6.0, decay=6.0, life=0.6, t_offset=CLOCK["T0"])
    # 人の体（うすく、影のように。点が足だと分かるように 15 章から）
    for k, legs in enumerate(PP):
        pts = legs[0][0]
        wk = Wk(walker(pts[0], 0, shirt="#1B2430", pants="#141A22", skin="#1B2430", hair="#141A22"))
        track("person%d" % k, wk.root, 1.0); track("feet%d" % k, wk.root, 0.3)
        wk.at(CLOCK["T0"] - 1, pts[0][0], pts[0][1], plan.face_deg(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]))
        for (pts_, t0_, v) in legs: wk.walk(t0_, pts_, v=v)
        if k == 2 or k == 0:   # 近づきすぎない広さ（橙の輪）。15-04 から
            rg = ring_marker((0, 0), r=0.55, col=ORANGE_PT, w=0.015, z=0.02); rg.parent = wk.root
            show_between(rg, w("15-04", "近づきすぎない"))
    if maru_lying:   # v2：まるロボがいるはずの所に、点がないことを黄色い輪で示す（v1 5:20「わかりにくい」）
        rq = ring_marker(MP, r=0.24, col="#FFD24A", w=0.022, z=0.03); show_between(rq, w("18-03", "映って") - 0.3); scale_pop(rq, w("18-03", "映って") - 0.3)
    if not maru_lying:
        M = Maru((MP[0], MP[1], 0), face=200); track("maru", M.root, 0.4)
        for o in [M.root] + list(M.root.children_recursive): o.visible_shadow = False
    track("orange", sv.root, 0.0)
    if cut(cl, "S14a"): cam((0.7, 3.3, 3.3), (0.0, 0.0, 0.0), 24, s("14-01") - 0.2, s("14-04"), (0.6, 3.2, 3.2), (0.0, -0.2, 0.0))
    if cut(cl, "S14b"): cam((1.8, 2.3, 2.4), (-0.3, 0.4, 0.2), 26, s("14-04") - 0.2, s("15-03"), (1.6, 2.2, 2.3), (-0.2, 0.3, 0.2))
    if cut(cl, "S15a"): cam((1.4, 2.6, 2.6), (0.0, 0.0, 0.1), 24, s("15-03") - 0.2, s("16-01"), (1.3, 2.5, 2.5), (0.0, -0.1, 0.1))
    if cut(cl, "S16a"):
        c, tg = cam((1.3, 2.4, 1.5), (0.0, 0.8, 0.3), 28)
        cam_track(c, tg, s("16-01") - 0.3, e("16-04") + 1.0, lambda t: (pose_at(t)[0] * 0.5, pose_at(t)[1] - 0.6, 0.3))
        key(c, "location", s("16-01") - 0.3, (1.4, 2.5, 2.4)); key(c, "location", e("16-04") + 1.0, (1.5, 0.5, 2.2))
    if cut(cl, "S18p"): cam((0.0, 1.9, 1.6), (0.0, 0.0, 0.0), 30)


def b_dark18(cl): b_dark(cl, maru_lying=True)


# ======================================================================== S17〜S21：光の板・低い物・高い物・前のカメラ・子どもの飛び出し
def b_test(cl):
    restaurant(); crowd(skip=((20, 'out'),))
    # 19：通路に出っぱったテーブル（脚は通路の外。天板だけが光の板より上で出っぱる）
    ex = empty((-0.62, -0.95, 0))
    cube(mat("tabletop", "#8A5E3B", rough=0.3, coat=0.4), (0, 0, 0.72), (0.62, 0.62, 0.04), bevel=0.01, parent=ex)
    cyl(mat("tableleg", "#3E2E24", rough=0.4, metal=0.2), (-0.22, 0, 0.36), 0.035, 0.72, parent=ex)
    cyl(mat("tableleg", "#3E2E24", rough=0.4, metal=0.2), (-0.22, 0, 0.01), 0.18, 0.02, parent=ex)
    hamburg(ex, (0.05, 0.0, 0.742)); track("edge", ex, 0.72)
    edge_pt = empty((-0.31, -0.95, 0.72)); track("edgept", edge_pt, 0.0)
    sv = Sv(senpai_serve((0.0, 1.2), 0)); track("senpai", sv.root, 1.2); track("tray", sv.d["trays"][1], 0.0); track("lens", sv.d["lenses"][0], 0.0)
    track("lens1", sv.d["lenses"][1], 0.0); track("lens2", sv.d["lenses"][2], 0.0)   # v2：「このカメラ」で丸をつける（v1 5:51）
    sv.spin(CLOCK["T0"] - 1, 400)
    rm = tray_item(sv, "ramen", 1)
    # 17：光の板（水平に広がる）
    lp, lm = light_plane(sv.root, r=1.0 / SVS); lp.location = (0, 0, plan.LIDAR_Z / SVS)
    show_between(lp, w("17-02", "この高さ"), s("20-01")); scale_pop(lp, w("17-02", "この高さ"))
    ev(w("17-02", "この高さ"), "whoosh", 0.4)
    lp2, _ = light_plane(sv.root, r=1.0 / SVS); lp2.location = (0, 0, plan.LIDAR_Z / SVS)
    show_between(lp2, w("20-04", "回る光"), s("20-05") + 0.2); scale_pop(lp2, w("20-04", "回る光"))
    # 18：まるロボが転がる → 先輩が近づいて、手前で止まる
    M = Maru((0.55, 0.45, 0), face=120); track("maru", M.root, 0.3)
    M.walk(s("18-01") + 0.6, s("18-01") + 2.6, (0.0, 0.2)); M.at(s("18-01") + 3.0, face=180)
    maru_lie(M, w("18-01", "転がって") + 0.9)
    d18 = drive_end([(0.0, 1.2), (0.0, 0.66)], w("18-04", "止まりました"), v=0.22, face0=0)
    sv.hold(d18.t0 - 0.1, pose=(0.0, 1.2, 0)); sv.drive(d18); ev(d18.t1, "stop", 0.6)
    # 19：起き上がって、横へ。先輩は出っぱった天板をよけて進む
    maru_lie(M, s("19-01") - 0.9, back=True)
    M.walk(s("19-01") - 0.2, s("19-01") + 1.6, (0.5, 0.55)); M.at(s("19-01") + 2.0, face=200)
    d19 = drive_end([(0.0, 0.66), (0.0, -0.2), (0.2, -0.65), (0.22, -1.25), (0.05, -1.75)], w("19-03", "よけて") + 1.2, v=0.38, turn=90, face0=0)
    d19 = plan.Drive([(0.0, 0.66), (0.0, -0.2), (0.2, -0.65), (0.22, -1.25), (0.05, -1.75)], max(s("19-03") - 0.6, d19.t0), 0.38, 90, 0)
    sv.hold(d19.t0 - 0.05, pose=(0.0, 0.66, 0)); sv.drive(d19)
    # 20：前のカメラが見ている範囲（上下に広がる扇）
    for k, ln in enumerate(sv.d["lenses"]):
        fo, fm = cam_fan(ln, far=1.3 / SVS, a_lo=-45 if k < 2 else -60, a_hi=20 if k < 2 else 10, half_w=30)
        show_between(fo, w("20-02", "3つ") + 0.15 * k, s("21-01")); scale_pop(fo, w("20-02", "3つ") + 0.15 * k)
    ev(w("20-02", "3つ"), "pop", 0.5)
    # 21：先輩が戻る途中で、テーブルのかげから子どもが飛び出す → すぐにストップ → 行ってから、ゆっくり
    kid = Wk(walker((-0.95, 0.75), -90, shirt="#E57373", pants="#3E5C76", s=0.62)); track("kid", kid.root, 0.9)
    kid.at(CLOCK["T0"] - 1, -0.95, 0.75, -90)
    t_kid = s("21-01") + 0.3
    kid.walk(t_kid, [(-0.95, 0.75), (0.75, 0.6)], v=1.6)
    d21a = plan.Drive([(0.05, -1.75), (0.0, -1.2), (0.0, -0.05)], t_kid - 2.6, 0.55, 140)
    d21a = plan.Drive([(0.05, -1.75), (0.0, -1.2), (0.0, 0.05)], t_kid - (plan.Drive([(0.05, -1.75), (0.0, -1.2), (0.0, 0.05)], 0, 0.55, 140).t1) + 0.45, 0.55, 140)
    sv.drive(d21a); ev(d21a.t1, "stop", 0.6); sv.set_face(d21a.t1, "dots"); sv.set_face(s("21-03"), "normal")
    d21b = plan.Drive([(0.0, 0.05), (0.0, 1.6)], s("21-03") + 0.7, 0.25, 140)
    sv.drive(d21b)
    if cut(cl, "S17a"): cam((-0.35, -0.75, 0.9), (0.0, 1.1, 0.35), 26, s("17-01") - 0.2, s("18-01"), (-0.32, -0.6, 0.85), (0.0, 1.1, 0.32))
    if cut(cl, "S18a"): cam((1.0, 0.45, 0.5), (0.0, 0.55, 0.25), 28, s("18-01") - 0.2, s("18-03"), (0.95, 0.5, 0.48), (0.0, 0.55, 0.25))
    if cut(cl, "S18b"): cam((0.85, 0.55, 0.42), (0.0, 0.5, 0.3), 30, s("18-04") - 0.2, s("19-01"), (0.8, 0.6, 0.42), (0.0, 0.55, 0.32))
    if cut(cl, "S19a"):
        c, tg = cam((0.35, -2.75, 1.05), (-0.25, -0.9, 0.6), 26)
        cam_track(c, tg, s("19-01") - 0.3, s("20-01") + 0.6, lambda t: ((d19.pose(t)[0] - 0.3) * 0.6, min(-0.6, d19.pose(t)[1]) if t > d19.t0 else -0.9, 0.62))
    if cut(cl, "S20a"): cam((-0.42, -2.9, 0.75), (0.05, -1.75, 0.55), 26, s("20-01") - 0.2, s("21-01"), (-0.35, -2.85, 0.85), (0.05, -1.75, 0.55))
    if cut(cl, "S21a"): cam((0.45, -1.6, 1.0), (-0.1, 0.5, 0.55), 26, s("21-01") - 0.2, s("22-01"), (0.42, -1.5, 0.95), (0.0, 0.6, 0.55))


# ======================================================================== S22：ラーメンのスープがこぼれない（ゆっくりもう一度）
def b_ramen(cl):
    restaurant(); crowd()
    sv = Sv(senpai_serve((0.0, -1.0), 0)); track("senpai", sv.root, 1.2); track("tray", sv.d["trays"][1], 0.05)
    sv.spin(CLOCK["T0"] - 1, 430)
    R1 = ramen(sv.d["trays"][1], (0, 0, 0.012)); track("ramen", R1["root"], 0.08)
    br = R1["broth"]
    # 22-01a：急に止まる（ゆっくりに見せる：0.4 倍の速さ）→ スープの面が少しかたむいて、戻る
    t1 = w("22-01a", "止まった") + 0.2
    d1 = plan.Drive([(0.0, -1.0), (0.0, 0.25)], t1 - 1.25 / 0.18, 0.18, 90, 180)
    sv.place(CLOCK["T0"] - 1, 0.0, -1.0, 180); sv.drive(d1, motor=False)
    for (dt, a) in ((0.0, 0.0), (0.5, 4.0), (1.1, -2.0), (1.6, 1.0), (2.1, 0.0)):
        key(br, ("rotation_euler", 0), t1 + dt, R(a))
    # 22-02：なめらかに速さを変える（走り出し → ゆっくり止まる）。車輪のあたりに速さの線
    d2 = plan.Drive([(0.0, 0.25), (0.0, 1.75)], s("22-02") + 0.2, 0.3, 90, 180)
    sv.drive(d2)
    for (dt, a) in ((0.0, 0.0), (0.5, 1.5), (1.0, 0.0)):
        key(br, ("rotation_euler", 0), d2.t1 + dt, R(a))
    for st_ in R1["steam"]:
        z0 = st_.location.z
        for k in range(30):
            tt = CLOCK["T0"] + k * 1.5; key(st_, ("location", 2), tt, z0, "LINEAR"); key(st_, ("location", 2), tt + 1.49, z0 + 0.08, "LINEAR")
    if cut(cl, "S22a"):
        c, tg = cam((0.48, -0.3, 0.98), (0.0, -0.5, 0.72), 40)
        cam_track(c, tg, s("22-01") - 0.3, s("22-02") + 0.4, lambda t: (0.0, d1.pose(t)[1] if t < d2.t0 else d2.pose(t)[1], 0.72))
        def cpos(t):
            y = d1.pose(t)[1] if t < d2.t0 else d2.pose(t)[1]
            return (0.48, y + 0.25, 0.98)
        t = s("22-01") - 0.3
        while t <= s("22-02") + 0.4: key(c, "location", t, cpos(t), "LINEAR"); t += 0.25
    if cut(cl, "S22b"):
        c, tg = cam((0.5, -0.5, 0.95), (0.0, 0.5, 0.6), 30)
        cam_track(c, tg, s("22-02") - 0.3, e("22-03") + 0.8, lambda t: (0.0, d2.pose(t)[1], 0.55))
        key(c, "location", s("22-02") - 0.3, (0.5, -0.5, 0.95)); key(c, "location", e("22-03") + 0.8, (0.5, 0.2, 0.95))


# ======================================================================== S22c：一日に何度も、止まったり曲がったり（v2：ラーメンの寄りが続きすぎた。v1 6:42）
def b_daily(cl):
    restaurant(); crowd()
    sv = Sv(senpai_serve((0.0, -2.6), 180)); track("senpai", sv.root, 1.2); track("tray", sv.d["trays"][1], 0.05)
    sv.spin(CLOCK["T0"] - 1, 420)
    R1 = ramen(sv.d["trays"][1], (0, 0, 0.012)); track("ramen", R1["root"], 0.08)
    pts = [(0.0, -2.6), (0.0, -1.5), (0.0, -0.75), (-0.32, -0.25)]
    dr = plan.Drive(pts, s("22-01c") - 0.6, 0.42, 110, 180, wait=0.45)
    sv.hold(CLOCK["T0"] - 1, pose=(0.0, -2.6, 180)); sv.drive(dr)
    t = dr.t0
    for k in range(1, len(dr.keys)):
        if dr.keys[k][1:3] == dr.keys[k - 1][1:3] and dr.keys[k][3] == dr.keys[k - 1][3]: ev(dr.keys[k - 1][0], "stop", 0.35)
    # 22-01d：向きを変えて、また走る（帰り道）
    d2 = plan.Drive([(-0.32, -0.25), (0.0, 0.3), (0.0, 1.4)], max(dr.t1 + 0.5, s("22-01d") - 0.3), 0.42, 110)
    sv.drive(d2)
    pose = lambda t: dr.pose(t) if t <= dr.t1 + 0.4 else d2.pose(t)
    if cut(cl, "S22c"):
        c, tg = cam((0.45, 1.2, 1.55), (0.0, -1.6, 0.6), 26)
        cam_track(c, tg, s("22-01c") - 0.3, e("22-01d") + 1.0, lambda t: (pose(t)[0] * 0.8, pose(t)[1], 0.62))
        key(c, "location", s("22-01c") - 0.3, (0.45, 1.2, 1.55)); key(c, "location", s("22-01d"), (0.42, 1.0, 1.35))
        key(c, "location", e("22-01d") + 1.0, (0.4, 2.0, 1.15))


# ======================================================================== S22p：人がおぼんで運んでいて、急に止まると……スープがはねる（小窓。v2：2D の絵から 3D へ。v1 6:35「もう少しリアルに」）
def b_spill(cl):
    restaurant(); crowd()
    t_s = w("22-01b", "人が") - 0.3; t_stop = w("22-01b", "急に") + 0.25; v = 1.0
    y_stop = -0.2; y0 = y_stop + v * (t_stop - t_s)
    st = Wk(walker((0.0, y0), 0, shirt="#2B2F36", apron=True))
    st.at(CLOCK["T0"] - 1, 0.0, y0, 0); st.walk(t_s, [(0.0, y0), (0.0, y_stop)], v=v)
    for i in (0, 1):   # 両手でおぼんを前に持つ（歩くときの腕ふりは消す）
        st.w.arms[i].animation_data_clear()
        key(st.w.arms[i], "rotation_euler", CLOCK["T0"] - 1, aim_arm(st.w.arms[i], (0.0, 0.0, 0.0), 0.0, ((-0.2 if i == 0 else 0.2), -0.42, 1.0)))
    tr = empty((0, -0.4, 1.06)); tr.parent = st.root
    cube(mat("obon", "#7A5634", rough=0.4, coat=0.4), (0, 0, 0), (0.42, 0.3, 0.02), bevel=0.008, parent=tr)
    R1 = ramen(tr, (0, 0, 0.012), steam=False); br = R1["broth"]
    # 急に止まる：体が前へかたむき、スープが前へはねる
    key(st.root, ("rotation_euler", 0), t_stop - 0.05, 0.0); key(st.root, ("rotation_euler", 0), t_stop + 0.15, R(-7)); key(st.root, ("rotation_euler", 0), t_stop + 0.6, 0.0, "BEZIER")
    key(br, ("rotation_euler", 0), t_stop, 0.0); key(br, ("rotation_euler", 0), t_stop + 0.12, R(-24)); key(br, ("rotation_euler", 0), t_stop + 0.35, R(12)); key(br, ("rotation_euler", 0), t_stop + 0.7, 0.0)
    bowl_w = (0.0, y_stop - 0.4, 1.06 + 0.08)
    sm = mat("splash", "#C9782C", rough=0.15, coat=1.0)   # v2 点検：うすい色だと床で見えない
    import random as _r; _r.seed(6)
    for k in range(24):   # v2 点検：しずくが小さくて見えなかった → 大きく・多く
        dx, dy, dz = _r.uniform(-0.3, 0.3), -_r.uniform(0.5, 1.2), _r.uniform(0.5, 1.2)
        o = sphere(sm, bowl_w, _r.uniform(0.018, 0.032)); show_between(o, t_stop + 0.06)
        t = 0.0
        while t <= 0.62:
            z = bowl_w[2] + dz * t - 4.9 * t * t
            if z < 0.01: z = 0.01
            key(o, "location", t_stop + 0.06 + t, (bowl_w[0] + dx * t, bowl_w[1] + dy * t, z), "LINEAR"); t += 0.04
    ev(t_stop, "stop", 0.5); ev(t_stop + 0.1, "splash", 0.5)
    if cut(cl, "S22p"): cam((0.75, -1.75, 1.45), (0.0, -0.55, 1.12), 32)   # 前の横から（おぼんとラーメンが見えるように。v2 点検：近づけて、はねるのが見えるように）


# ======================================================================== S23〜S25：通路を狭くすると
def b_narrow(cl):
    PULL = 0.62
    t_p = w("23-01", "いすを") + 0.2; t_b = s("25-01") + 0.3
    Rr = restaurant(); crowd(skip=((11, 'in'),))
    ch = Rr["chairs"][11]
    p11 = seated(11, 'in', "#C0504D")
    for ob in (ch, p11):
        x0 = ob.location.x
        key(ob, ("location", 0), CLOCK["T0"] - 1, x0); key(ob, ("location", 0), t_p, x0); key(ob, ("location", 0), t_p + 1.2, x0 - PULL)
        key(ob, ("location", 0), t_b, x0 - PULL); key(ob, ("location", 0), t_b + 1.2, x0)
    ev(t_p, "chair", 0.6); ev(t_b, "chair", 0.5)
    sv = Sv(senpai_serve((0.0, 2.3), 0)); track("senpai", sv.root, 1.2); sv.spin(CLOCK["T0"] - 1, 460)
    tray_item(sv, "ramen", 1)
    t_st = w("23-02", "ぴたり")
    da = drive_end([(0.0, 2.3), (0.0, 0.55)], t_st, v=0.4, face0=0)
    sv.hold(CLOCK["T0"], pose=(0.0, 2.3, 0)); sv.drive(da); ev(t_st, "stop", 0.6)
    sv.set_face(s("23-03") + 0.1, "trouble")
    sv.piron(w("25-02", "ピロン"), "happy")
    db = plan.Drive([(0.0, 0.55), (0.0, -1.2), SEAT12], w("25-02", "ピロン") + 0.6, 0.5, 90, 0)
    sv.drive(db)
    track("gapL", empty((-0.645, -0.25, 0.05)), 0.0)
    gr = empty((0.855 - PULL - 0.21, -0.25, 0.05)); track("gapR", gr, 0.0)
    M = Maru((-0.35, 1.3, 0), face=200); track("maru", M.root, 0.4)
    M.at(s("23-03") + 0.3, face=180); M.hop(s("23-03") + 0.5, h=0.1, d=0.3, sound=False)
    M.at(s("25-01"), face=210); M.hop(e("25-02") - 0.6, h=0.18, d=0.4)
    if cut(cl, "S23a"): cam((0.0, -2.95, 1.35), (0.0, 0.3, 0.45), 26, s("23-01") - 0.2, s("23-03"), (0.0, -2.8, 1.3), (0.0, 0.3, 0.45))
    if cut(cl, "S23b"): cam((0.15, -0.6, 1.15), (0.0, 0.55, 1.12), 34, s("23-03") - 0.2, s("24-01"), (0.12, -0.5, 1.13), (0.0, 0.55, 1.12))
    if cut(cl, "S24a"): cam((0.0, 1.55, 2.7), (0.0, -0.25, 0.0), 30, s("24-01") - 0.2, s("25-01"), (0.0, 1.45, 2.6), (0.0, -0.3, 0.0))
    if cut(cl, "S25a"): cam((0.0, -2.95, 1.35), (0.0, 0.3, 0.45), 26, s("25-01") - 0.2, s("26-01"), (0.0, -2.8, 1.3), (0.0, 0.0, 0.45))


# ======================================================================== S26〜S28：顔のひみつ・耳をなでると
def b_face(cl):
    Rf = restaurant(); crowd(skip=((10, 'in'),))
    for o_ in [Rf["chairs"][10]] + list(Rf["chairs"][10].children_recursive): o_.hide_render = True
    SP = (0.68, 1.35)
    sv = Sv(senpai_serve(SP, 0)); track("senpai", sv.root, 1.2); track("head", sv.d["head"], 0.0); sv.spin(CLOCK["T0"] - 1, 520)
    track("ear", sv.d["ears"][1], 0.05)
    # 26-02：通路で、人がすっと道をあける（遠くで、別のお客さんと先輩）
    cu = Wk(walker((-0.1, -0.6), 180, shirt="#7FB3A8")); cu.at(CLOCK["T0"] - 1, -0.1, -0.6, 180)
    o2 = senpai_serve((0.0, -2.5), 180)
    for k, g in o2["face"].items(): g.hide_render = (k != "normal")
    sv2 = Sv(o2, "normal"); d2 = plan.Drive([(0.0, -2.5), (0.0, 0.4)], s("26-03") - 0.5, 0.45, 90, 180); sv2.drive(d2)
    cu.walk(s("26-03") + 0.6, [(-0.1, -0.6), (-0.42, -0.4)], v=0.6); cu.at(s("26-03") + 2.0, -0.42, -0.4, 90)
    sv.set_face(s("26-01") + 0.3, "happy"); sv.set_face(e("26-02") + 0.5, "normal")
    # 27：子どもが耳をなでる → うれしそう（耳が小さくゆれる）
    kid = Wk(walker((0.2, 0.75), -30, shirt="#F2C14E", pants="#3E5C76", s=0.78)); track("kid", kid.root, 0.8)
    kid.at(CLOCK["T0"] - 1, -1.0, 0.55, -90)
    kid.walk(s("27-01") - 2.4, [(-1.0, 0.55), (0.3, 1.0)], v=0.7); kid.at(s("27-01") + 0.1, 0.3, 1.0, 133)
    for k in range(4):
        tt = s("27-01") + 0.4 + k * 0.6
        kid.arm_up(tt, 0, 165, 0.3); key(kid.w.arms[0], ("rotation_euler", 0), tt + 0.3, R(-140))
    key(kid.w.arms[0], ("rotation_euler", 0), e("27-02") + 0.2, R(-140)); key(kid.w.arms[0], ("rotation_euler", 0), e("27-02") + 0.8, 0.0)
    sv.set_face(s("27-02") - 0.2, "happy"); sv.ears(s("27-01") + 0.4, e("27-02"), 10, 0.45); ev(s("27-02") - 0.1, "purr", 0.5)
    kid.walk(e("27-03") - 2.0, [(0.3, 1.0), (-0.6, 0.55), (-1.0, 0.55)], v=0.7)
    sv.set_face(e("27-03") - 0.5, "normal")
    # 28：まるロボがまねして、テーブルの上から頭ですりすり → しつこく → 怒った顔
    M = Maru((1.15, 1.35, 0.742), face=-90); track("maru", M.root, 0.4)
    t_r = s("28-01") + 2.2
    M.at(t_r - 0.3, loc=(1.15, 1.35, 0.742)); M.at(t_r + 0.3, loc=(1.02, 1.35, 0.742))
    for k in range(12):
        tt = t_r + 0.4 + k * 0.42
        key(M.body, ("rotation_euler", 0), tt, R(30 if k % 2 else 18)); key(M.body, ("rotation_euler", 1), tt, R(-8 if k % 2 else 8)); key(M.body, ("location", 2), tt, M.z0 + (0.14 if k % 2 else 0.08))
        if k % 2 == 0: ev(tt, "rub", 0.4)
    t_end = t_r + 0.4 + 12 * 0.42
    sv.ears(t_r + 0.4, t_end, 8, 0.42)
    sv.set_face(t_r + 0.6, "happy")
    t_ang = w("28-03", "怒った") - 0.15
    sv.set_face(t_ang, "angry"); ev(t_ang, "grr", 0.6)
    key(M.body, ("rotation_euler", 0), max(t_end, t_ang + 0.1), R(18)); key(M.body, ("rotation_euler", 0), t_ang + 0.45, R(-10)); key(M.body, ("rotation_euler", 1), t_ang + 0.45, 0.0); key(M.body, ("location", 2), t_ang + 0.45, M.z0)
    M.at(t_ang + 0.2, loc=(1.02, 1.35, 0.742)); M.at(t_ang + 0.6, loc=(1.32, 1.35, 0.742))
    M.glow(t_ang + 0.3, 0.3, 0.3); M.glow(e("28-04"), 0.9, 0.5)
    sv.set_face(e("28-05") - 0.3, "normal")
    if cut(cl, "S26a"): cam((-0.5, -0.3, 1.25), (0.62, 1.35, 1.1), 30, s("26-01") - 0.2, s("26-02") + 0.6, (-0.4, -0.15, 1.22), (0.62, 1.35, 1.12))
    if cut(cl, "S26b"): cam((-0.35, 2.1, 1.6), (-0.1, -0.8, 0.6), 26, s("26-03") - 0.2, s("27-01"), (-0.3, 2.0, 1.55), (-0.1, -0.6, 0.6))
    if cut(cl, "S27a"): cam((0.58, 0.32, 1.15), (0.55, 1.3, 1.1), 28, s("27-01") - 0.2, s("28-01"), (0.6, 0.4, 1.15), (0.6, 1.35, 1.12))
    if cut(cl, "S28a"): cam((0.72, 0.42, 1.2), (0.85, 1.35, 1.05), 30, s("28-01") - 0.2, s("29-01"), (0.7, 0.48, 1.18), (0.85, 1.35, 1.08))


# ======================================================================== S29：まとめ（冒頭と同じ絵）
def b_sum(cl):
    restaurant(); crowd()
    M = Maru((-0.25, 0.9, 0), face=200); track("maru", M.root, 0.4)
    sv = Sv(senpai_serve(WAIT, 0)); track("senpai", sv.root, 1.2); sv.spin(CLOCK["T0"] - 1, 600)
    tray_item(sv, "ramen", 1, t_hide=s("29-04") + 1.0)
    d1 = plan.Drive([WAIT, (0.25, 1.6), (0.3, 0.4), SEAT11], s("29-01") + 0.5, 0.45, 100)
    sv.drive(d1); table_item(11, "ramen", s("29-04") + 1.0, toward=0.05)
    cu = Wk(walker((-0.3, -1.4), 0, shirt="#6C8EBF")); cu.at(CLOCK["T0"] - 1, -0.3, -1.4, 180)
    cu.walk(s("29-05"), [(-0.3, -1.4), (-0.3, -0.75), (-0.45, -0.6)], v=0.5)
    d2 = plan.Drive([SEAT11, (0.3, -0.9), (0.3, -1.5)], s("29-05") + 0.4, 0.4, 100)
    sv.drive(d2)
    sv.set_face(s("29-07"), "happy")
    if cut(cl, "S29a"): cam((0.35, -3.1, 1.6), (0.0, 0.3, 0.5), 22, s("29-01") - 0.2, e("29-07") + 1.0, (0.25, -2.8, 1.5), (0.0, 0.5, 0.5))


# ======================================================================== S30：オチ（デザートだと思われた）
def aim_arm_full(arm, root_loc, rot_xyz, target):
    """歩く人の腕（-Z が腕の向き）を、体のかたむき（x）と向き（z）を入れて、目当てへ向ける回転"""
    from mathutils import Vector, Euler
    m = Euler(rot_xyz, 'XYZ').to_matrix()
    sh = Vector(root_loc) + m @ Vector(arm.location)
    d = m.inverted() @ (Vector(target) - sh)
    return tuple(d.to_track_quat('-Z', 'Y').to_euler())


def b_end(cl):
    # v2：まるロボは台所の出口の横の台でひと休み → 店員さんが両手で持ち上げ、先輩のいちばん下のトレーへ（v1 9:23「動きおかしい」）。
    #     まるロボ（高さ約 0.40 m）はトレーの間（0.21 m）に入らないので、この場面だけ、まん中と上のトレーを外しておく（v1 9:28「貫通してる」）
    restaurant(); crowd(skip=((10, 'in'),))
    sv = Sv(senpai_serve(WAIT, 0)); track("senpai", sv.root, 1.2); sv.spin(CLOCK["T0"] - 1, 640)
    for tr_ in sv.d["trays"][1:]:          # まん中と上のトレーを外す（上から下ろすときも当たらないように）
        tr_.scale = (0.0001, 0.0001, 0.0001)
        for ch in tr_.children_recursive: ch.hide_render = True
    # 台所の出口の横の台
    cnt = (1.35, 3.12); CZ = 0.86
    cube(mat("counter", "#E9E2D6", rough=0.5), (cnt[0], cnt[1] + 0.02, CZ / 2), (0.7, 0.42, CZ), bevel=0.02)
    cube(mat("countertop", "#8A5E3B", rough=0.3, coat=0.4), (cnt[0], cnt[1] + 0.02, CZ - 0.01), (0.74, 0.46, 0.03), bevel=0.008)
    M = Maru((cnt[0], cnt[1] - 0.05, CZ + 0.005), face=200); track("maru", M.root, 0.4)
    M.at(s("30-01") + 0.3, look=-8); M.glow(s("30-01") + 0.6, 0.45, 0.6)
    st = Wk(walker((-0.6, 3.1), 120, shirt="#2B2F36", apron=True)); track("staff", st.root, 1.6)
    st.at(CLOCK["T0"] - 1, -0.6, 3.1, 120)
    t_l = w("30-02", "ひょいと"); t_p = w("30-02", "トレー") + 0.2
    SP = (0.85, 2.92)                                   # 店員さんが立つ所
    f_cnt = plan.face_deg(cnt[0] - SP[0], cnt[1] - SP[1]); f_sv = plan.face_deg(WAIT[0] - SP[0], WAIT[1] - SP[1])
    f_sv = f_cnt + ((f_sv - f_cnt + 180) % 360 - 180)
    t_w = st.walk(t_l - 1.0 - 2.2, [(-0.6, 3.1), (0.1, 3.28), SP], v=0.85); st.at(t_l - 1.0, SP[0], SP[1], f_cnt)
    tray0 = (0.0, WAIT[1] - 0.02 * SVS, 0.52 * SVS + 0.016)   # いちばん下のトレーの上（まるロボの足もと）
    # まるロボの場所（足もと）と、店員さんの体（場所・かたむき・向き）
    MB = 0.18                                           # 足もとから体のまん中まで
    g = t_l - 0.45                                      # つかむ（「ひょいと」の少し前）
    keys = [(g, (cnt[0], cnt[1] - 0.05, CZ + 0.005), 0.0, f_cnt),
            (g + 0.35, (cnt[0] - 0.12, cnt[1] - 0.1, CZ + 0.16), 0.0, f_cnt),
            (g + 0.9, None, 0.0, f_sv),
            (t_p - 0.25, (tray0[0] + 0.1, tray0[1] - 0.05, tray0[2] + 0.36), 0.0, f_sv),
            (t_p + 0.15, (tray0[0] + 0.03, tray0[1], tray0[2] + 0.3), 0.0, f_sv)]   # ここで手をはなし、まるロボがぽんと乗る
    for i, (t, loc, lean, f) in enumerate(keys):
        if loc is None:   # 体の前に抱える
            th = R(f); fx, fy = math.sin(th), -math.cos(th); loc = (SP[0] + fx * 0.42, SP[1] + fy * 0.42, 0.78)
        M.at(t, loc=loc, interp="BEZIER")
        key(st.root, ("rotation_euler", 0), t, lean, "BEZIER"); key(st.root, ("rotation_euler", 2), t, R(f), "BEZIER")
        tgt = (loc[0], loc[1], loc[2] + MB)
        for arm in st.w.arms:
            key(arm, "rotation_euler", t, aim_arm_full(arm, (SP[0], SP[1], 0.0), (lean, 0.0, R(f)), tgt), "BEZIER")
    M.at(t_p + 0.4, loc=tray0, interp="BEZIER")
    for hp in st.w.hips:   # 持ち上げる間は、足をそろえて立つ
        key(hp, ("rotation_euler", 0), g - 0.3, 0.0); key(hp, ("rotation_euler", 0), s("30-03") + 0.5, 0.0)
    for arm in st.w.arms:   # 手をのばし始める・はなす
        key(arm, "rotation_euler", t_l - 1.0, (0, 0, 0)); key(arm, "rotation_euler", t_p + 0.8, (R(-20), 0, 0))
    key(st.root, ("rotation_euler", 0), t_p + 0.8, 0.0, "BEZIER")
    M.at(g, face=200); M.at(g + 0.9, face=180); M.at(t_p + 0.15, face=0)
    M.glow(g + 0.2, 0.9, 0.2); ev(g + 0.05, "jump", 0.35); ev(t_p + 0.4, "land", 0.5)
    st.at(t_p + 1.0, SP[0], SP[1], f_sv); st.walk(s("30-03") + 0.6, [SP, (1.0, 2.4)], v=0.6)
    sv.piron(w("30-03", "ピロン"), "happy")
    dr = plan.Drive([WAIT, (0.0, 2.2), SEAT10], w("30-03", "走り出し"), 0.4, 90, 0)
    sv.drive(dr)
    t = dr.t0
    while t <= dr.t1 + 0.6:
        x, y, a = dr.pose(min(t, dr.t1)); th = R(a)
        dd = 0.02 * SVS; M.at(t, loc=(x + dd * math.sin(th), y - dd * math.cos(th), tray0[2]), face=a, interp="LINEAR", hold=False); t += 0.125
    # 席で、スプーンを持って待つお客さん
    p = seated(10, 'in', "#E8A04D")
    spn = empty((0.75, 1.15, 0.85)); spn.rotation_euler = (R(60), 0, R(20))
    cube(mat("spoon", "#D9DDE1", rough=0.2, metal=0.9), (0, 0, 0), (0.02, 0.012, 0.16), parent=spn); sphere(mat("spoon", "#D9DDE1", rough=0.2, metal=0.9), (0, 0, 0.09), 0.03, scale=(1, 0.4, 1.3), parent=spn)
    track("spoon", spn, 0.0)
    M.glow(w("30-04", "デザート") - 0.4, 1.6, 0.2); M.wobble(w("30-04", "デザート") - 0.2, e("30-04") + 1.2, 6, 0.3)
    if cut(cl, "S30a"): cam((0.4, 1.55, 1.15), (1.3, 3.1, 0.95), 30, s("30-01") - 0.2, s("30-02"), (0.42, 1.65, 1.12), (1.3, 3.1, 0.97))
    if cut(cl, "S30b"): cam((-0.35, 1.05, 1.45), (0.5, 2.95, 0.95), 26, s("30-02") - 0.2, s("30-03"), (-0.32, 1.15, 1.42), (0.45, 2.9, 0.9))
    if cut(cl, "S30c"):
        c, tg = cam((-0.4, 0.55, 1.3), (0.0, 2.4, 0.7), 26)
        cam_track(c, tg, s("30-03") - 0.3, e("30-04") + 2.6, lambda t: (dr.pose(t)[0] * 0.7 + 0.2, dr.pose(t)[1] - 0.2, 0.7))
        key(c, "location", s("30-03") - 0.3, (-0.4, 0.55, 1.3)); key(c, "location", e("30-04") + 2.6, (-0.35, 0.3, 1.25))


# ======================================================================== クリップの一覧
#   CUTS：カットの名前・組み立て・切り替わる時刻。切り替わる時刻＝その文の字幕が出る時刻（声の頭）
#   （4本目 v10：絵は字幕と同じコマで替える。声より先に替えない）。組み立てでは 0.35 秒（章の変わり目は 0.6 秒）で溶かしてつなぐ
CUTS = [
    ("S01a", b_open, 0.0), ("S01b", b_open, s("01-02")), ("S02a", b_open, s("02-01")), ("S02b", b_open, s("02-02")), ("S02c", b_open, s("02-03")),
    ("S03a", b_open, s("03-01")), ("S03b", b_open, s("03-02")), ("S03c", b_open, s("03-03")), ("S03d", b_open, s("03-05")), ("S04a", b_open, s("04-01")),
    ("S05a", b_meet, s("05-01")), ("S05b", b_meet, s("05-03")), ("S06a", b_meet, s("06-01")), ("S07a", b_meet, s("07-01")), ("S07b", b_meet, s("07-03")),
    ("S08a", b_order, s("08-01")), ("S08b", b_order, s("08-03")), ("S08c", b_order, s("08-04")),
    ("S09a", b_map, s("09-01")), ("S10b", b_where, s("10-03")),
    ("S11a", b_ceil, s("11-01")), ("S11b", b_ceil, s("11-05")),
    ("S12a", b_shape, s("12-01")),
    ("S13a", b_lidar, s("13-01")), ("S13b", b_lidar, s("13-02")),
    ("S14a", b_dark, s("14-01")), ("S14b", b_dark, s("14-04")), ("S15a", b_dark, s("15-03")), ("S16a", b_dark, s("16-01")),
    ("S17a", b_test, s("17-01")), ("S18a", b_test, s("18-01")), ("S18b", b_test, s("18-04")), ("S19a", b_test, s("19-01")),
    ("S20a", b_test, s("20-01")), ("S21a", b_test, s("21-01")),
    ("S22a", b_ramen, s("22-01")), ("S22c", b_daily, s("22-01c")), ("S22b", b_ramen, s("22-02")),
    ("S23a", b_narrow, s("23-01")), ("S23b", b_narrow, s("23-03")), ("S24a", b_narrow, s("24-01")), ("S25a", b_narrow, s("25-01")),
    ("S26a", b_face, s("26-01")), ("S26b", b_face, s("26-03")), ("S27a", b_face, s("27-01")), ("S28a", b_face, s("28-01")),
    ("S29a", b_sum, s("29-01")),
    ("S30a", b_end, s("30-01")), ("S30b", b_end, s("30-02")), ("S30c", b_end, s("30-03")),
]
END_T = e("30-04") + 2.5
CLIPS = {}
for i, (nm, fn, tc) in enumerate(CUTS):
    t0 = max(0.0, tc - 0.1)
    t1 = (CUTS[i + 1][2] + 0.75) if i + 1 < len(CUTS) else END_T
    CLIPS[nm] = (fn, t0, t1)
# 小窓用（本編の切り替わりには入らない）：18-03「先輩の目の絵」＝まるロボが転がっていて点がない
CLIPS["S18p"] = (b_dark18, s("18-03") - 0.5, e("18-03") + 1.0)
CLIPS["S22p"] = (b_spill, s("22-01b") - 0.5, e("22-01b") + 1.0)   # v2：人が運ぶと、こぼれる（小窓）

if __name__ == "__main__" or True:
    if CLIPNAME == "--list":
        print(json.dumps({k: [round(v[1], 3), round(v[2], 3), round(([c[2] for c in CUTS if c[0] == k] or [v[1]])[0], 3)] for k, v in CLIPS.items()}))
    else:
        fn, t0, t1 = CLIPS[CLIPNAME]
        CLOCK["T0"] = t0
        fn(CLIPNAME)
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
