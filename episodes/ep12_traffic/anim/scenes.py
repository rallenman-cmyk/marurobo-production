# 12本目（渋滞）：3D の場面を声の時刻に合わせて動かして描く（17本目の scenes.py と同じ作り方）
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 4] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   PC の本番：... -- <クリップ> <出力> --samples 24 --res 1920 1080 --frames 0 99 --gpu --video --fast
#   舞台：A＝夕方の大通りとおじさんの車（b_drive）／G＝地球（b_globe）／B＝昼の大通りと歩道橋・感知器（b_bridge）／
#         T＝町の引き（b_town）／N＝車のナビの寄り（b_nav）／C＝町はずれの道（b_field）
#   舞台の組み立て（b_*）は、その舞台の動きを全部作り、カメラだけをクリップごとに選ぶ。絵コンテ表：../絵コンテ_v1.md
#   決まり：3D の中に字を書かない／まるロボは喋らない・本物の体を marumotion の予定で動かす（maru12.py）／動きは言い終えてから
#   運転しながらスマホを見る絵にしない（スマホが映るカットで、おじさんの顔は前を向く）
#   この版は冒頭〜2章（S01〜S10）。§2.6：章ごとに動く下書きで OK をもらう
import os, sys, math, json
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.read_factory_settings(use_empty=True)
TEX = os.environ.get("TEX12") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "tex12")
exec(open(os.path.join(KIT_HERE, "kit12.py"), encoding="utf-8").read())
_K7 = KIT_HERE
exec(open(os.path.join(KIT_HERE, "..", "..", "ep06_haizen", "anim", "core.py"), encoding="utf-8").read().replace(
    'VO = os.path.join(KIT_HERE, "..", "voice")', 'VO = os.path.join(_K7, "..", "voice")'))
sys.path.insert(0, _K7)
from timing import wp       # 言葉の時刻は、声の本当の間から（SKILL §3。2D の札と同じ。表がなければ字数の見積もり）
CLIPNAME = _argv[0]; OUTDIR = _argv[1] if len(_argv) > 1 else "/tmp/x"
_SRC_DEFAULT = {"step": "maru_c", "jump": "maru_c", "land": "maru_c", "takeoff": "maru_c", "step_turn": "maru_c"}


def ev(t, kind, gain=1.0, src=None):
    EVENTS.append((round(t, 3), kind, gain, src if src is not None else _SRC_DEFAULT.get(kind, "")))


def _opt(name, n=1, default=None):
    if name in _argv:
        i = _argv.index(name); v = _argv[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default


SAMPLES = int(_opt("--samples", 1, 4)); RES = tuple(int(x) for x in _opt("--res", 2, ("480", "270"))); STEP = int(_opt("--step", 1, 3))
STILLS = [float(x) for x in _opt("--stills", 1, "").split(",") if x]
TRACK_ONLY = "--track" in _argv
_M_ = [None]
exec(open(os.path.join(_K7, "maru12.py"), encoding="utf-8").read())
MS = 0.40                     # まるロボの大きさ（全部の舞台で同じ）


def cam(loc, target, lens=35, t0=None, t1=None, loc1=None, target1=None, lens1=None, parent=None):
    c, tg = cam_rig(loc, target, lens)
    c.data.dof.use_dof = False; c.data.dof.aperture_fstop = 64.0
    if parent is not None:
        c.parent = parent; tg.parent = parent
    if t0 is not None:
        cam_move(c, tg, t0, t1, loc, loc1 or loc, target, target1 or target, lens, lens1 or lens)
    c.data.clip_start = 0.05; c.data.clip_end = 3000.0
    return c, tg


def C(loc, tgt, lens=35, loc1=None, tgt1=None, lens1=None, d=8.0):
    """決まったカメラ（d 秒かけて loc → loc1 へゆっくり動く）"""
    def mk(t0):
        return cam(loc, tgt, lens, t0, t0 + d, loc1 or loc, tgt1 or tgt, lens1 or lens)
    return mk


def CC(loc, tgt, lens=35, loc1=None, tgt1=None, lens1=None, d=8.0):
    """車の中・車についていくカメラ（座標は車の中の座標。前＝+x・左＝+y）"""
    def mk(t0):
        return cam(loc, tgt, lens, t0, t0 + d, loc1 or loc, tgt1 or tgt, lens1 or lens, parent=STAGE["car"])
    return mk


def pop_in(ob, t, s1=1.0, d=0.3):
    key(ob, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(ob, "scale", t, (0.001, 0.001, 0.001)); key(ob, "scale", t + d, (s1, s1, s1))


def pop_out(ob, t, s0=1.0, d=0.25):
    key(ob, "scale", t, (s0, s0, s0)); key(ob, "scale", t + d, (0.001, 0.001, 0.001), "CONSTANT")


def beam_flash(p0, p1, t, d=0.35, col=TEAL_C, r=0.02, name="beam"):
    """目の光（p0 → p1 の細い光の棒）を t から d 秒だけ出す"""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]; L_ = math.sqrt(dx * dx + dy * dy + dz * dz)
    b_ = cyl(glow_mat(name, col, 6.0), ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2), r, L_, verts=8)
    b_.rotation_euler = (0, math.atan2(math.sqrt(dx * dx + dy * dy), dz), math.atan2(dy, dx))
    hide_key(b_, -100.0, True); hide_key(b_, t, False); hide_key(b_, t + d, True)
    return b_


STAGE = {}


# ======================================================================== A：夕方の大通りとおじさんの車（冒頭 S01〜S04の2）
V_CAR = 8.0                   # 走る速さ（m/秒。約 30 km/時）
LANE_Y = LANE * 1.5           # +x へ走る車の左の車線（日本は左側）
RT = 6.0                      # 曲がる半径
XS = -LANE_Y - RT             # 曲がり始める x
Y_STOP = 15.0                 # 列のうしろで止まる y
D_TURN = 2.4; D_STOP = 1.8


def car_state(t):
    """おじさんの車の (x, y, 向き度)。向き 0＝+x、90＝+y"""
    T0 = STAGE["t_turn"]
    if t <= T0:
        return (XS - V_CAR * (T0 - t), LANE_Y, 0.0)
    if t <= T0 + D_TURN:
        u = (t - T0) / D_TURN; a = -90.0 + 90.0 * u
        cx, cy = XS, LANE_Y + RT
        return (cx + RT * math.cos(R(a)), cy + RT * math.sin(R(a)), a + 90.0)
    u = min(1.0, (t - T0 - D_TURN) / D_STOP); u = 1 - (1 - u) ** 2
    return (-LANE_Y, LANE_Y + RT + (Y_STOP - LANE_Y - RT) * u, 90.0)


def car_point(t, lp):
    """車の中の点 lp（前＝+x・左＝+y）の、時刻 t の世界の座標"""
    x, y, h = car_state(t); c_, s_ = math.cos(R(h)), math.sin(R(h))
    return (x + lp[0] * c_ - lp[1] * s_, y + lp[0] * s_ + lp[1] * c_, lp[2] if len(lp) > 2 else 0.0)


def b_drive(par):
    """冒頭：夕方の大通りを走る → 角を左へ曲がる → 列のうしろで止まる"""
    sky_evening()
    STAGE["t_turn"] = wp("03-01", "角を") - 0.2
    road_strip((-340.0, 80.0), 420.0, "x")
    road_strip((ROAD_W / 2 + 0.2, 200.0), 200.0, "y")
    # v1 の点検：交差点の角に、歩道のない所が黒い穴に見えた。道の下に、歩道の色の地面を敷く
    cube(_m("ground_a", "#ADA69A", rough=0.9), (-130.0, 60.0, -0.06), (500.0, 400.0, 0.1))
    for sg in (-1, 1):   # 角で 2 つの歩道が重なる所が黒くなった（地面を敷いても残った）。少し高い板でふたをする
        cube(_m("corner_a", "#B4ADA1", rough=0.85), (sg * (ROAD_W / 2 + SIDEWALK / 2 + 0.15), ROAD_W / 2 + SIDEWALK / 2 + 0.15, 0.0735), (SIDEWALK + 0.3, SIDEWALK + 0.3, 0.147))
    city_side(-340.0, -ROAD_W / 2 - SIDEWALK - 4.0, ROAD_W / 2 + SIDEWALK + 0.3, +1, seed=1)
    city_side(-340.0, 80.0, ROAD_W / 2 + SIDEWALK + 0.3, -1, seed=2)
    city_side(ROAD_W / 2 + SIDEWALK + 4.0, 80.0, ROAD_W / 2 + SIDEWALK + 0.3, +1, seed=3)
    city_side(ROAD_W / 2 + SIDEWALK + 4.0, 200.0, ROAD_W / 2 + SIDEWALK + 0.3, -1, seed=4, axis="y")
    city_side(ROAD_W / 2 + SIDEWALK + 4.0, 200.0, ROAD_W / 2 + SIDEWALK + 0.3, +1, seed=5, axis="y")
    T_END = e("04-12") + 3.0; T_BEG = max(0.0, s("01-01") - 3.0)
    # ほかの車：同じ向きの右の車線・向かいの 2 車線（流れる）
    traffic([(LANE * 0.5, +1)], T_BEG, STAGE["t_turn"] + 4, -360.0, 80.0, V_CAR * 1.05, 4.0, seed=11)
    traffic([(-LANE * 0.5, -1), (-LANE * 1.5, -1)], T_BEG, T_END, -360.0, 80.0, 9.5, 3.2, seed=12)
    # 曲がった先の列（赤いブレーキの光）と、向かいの流れ
    for k in range(14):
        car_fast((-LANE_Y, Y_STOP + 5.6 + k * 5.6, 0.0), 90.0, CAR_COLS[k % len(CAR_COLS)], brake=True, name="q")
        car_fast((-LANE * 0.5, Y_STOP + 2.5 + k * 5.9, 0.0), 90.0, CAR_COLS[(k + 4) % len(CAR_COLS)], brake=True, name="q")
    traffic([(LANE * 0.5, -1), (LANE * 1.5, -1)], T_BEG, T_END, 10.0, 200.0, 7.0, 4.5, seed=13, axis="y")
    # おじさんの車
    cr = car((0, 0, 0), 0.0, "#7CC6E8", interior=True, name="ojicar"); STAGE["car"] = cr
    t = T_BEG
    while t <= T_END:
        x, y, h = car_state(t)
        key(cr, "location", t, (x, y, 0.0), "LINEAR"); key(cr, "rotation_euler", t, (0, 0, R(h)), "LINEAR"); t += 1.0 / 6
    track("car", cr, 1.0)
    # 冒頭〜2章 v1 の点検：後ろの座席から見ると、車の中が暗く、2 人が黒い影だった。屋根の内側に弱い明かり（車について動く）
    bpy.ops.object.light_add(type='AREA', location=(0.1, 0.1, 1.45)); il = bpy.context.object; il.data.energy = 18.0; il.data.size = 0.9
    bpy.ops.object.light_add(type='AREA', location=(-0.95, 0.0, 1.35), rotation=(0, R(-80), 0)); il2 = bpy.context.object; il2.data.energy = 45.0; il2.data.size = 1.0
    il2.data.color = (1.0, 0.92, 0.82); il2.parent = cr      # 後ろの座席から前へ当てる（2 人の背中が黒い影にならないように）
    il.data.color = (1.0, 0.93, 0.85); il.parent = cr
    p_, head = ojisan(cr)
    t = T_BEG; k_ = 0
    while t < T_END:      # 鼻歌：頭を小さくゆらす（前を向いたまま）
        key(head, "rotation_euler", t, (R(-3 if k_ % 2 else 3), 0, R(2 if k_ % 2 else -2))); t += 0.6; k_ += 1
    t_turn_end = STAGE["t_turn"] + D_TURN
    ph, scr = phone_on_holder(cr, [(0.0, os.path.join(TEX, "ph_map_a.png")), (wp("02-02", "渋滞") - 0.1, os.path.join(TEX, "ph_map_alert.png")),
                                   (t_turn_end, os.path.join(TEX, "ph_map_q.png")), (wp("04-05", "広げて"), os.path.join(TEX, "ph_map_z1.png")),
                                   (wp("04-06", "遠くの"), os.path.join(TEX, "ph_map_z2.png")), (s("04-08") - 0.3, os.path.join(TEX, "ph_map_eta.png"))])
    track("phone", ph, 0.0)
    ev(wp("02-02", "渋滞") - 0.1, "pop_ui", 0.35, "phone")
    # 走る音・曲がる・止まる
    ev(STAGE["t_turn"], "turn", 0.3, "car"); ev(t_turn_end + D_STOP - 0.6, "brake", 0.35, "car")
    # まるロボ：助手席のクッションの上（前を向く）。車に運ばれる（場所だけ。曲がり終わってから、その場で向きを直す）
    lp = (PASS[0] + 0.02, PASS[1], BOOST)
    p0 = car_point(T_BEG, lp)
    M = MaruR(p0, face=MFACE(0.0), s=MS); track("maru", M.body, 0.28); track("maru_top", M.body, 0.34)
    M.carry(T_BEG, T_END, lambda t, p0=p0: tuple(a - b for a, b in zip(car_point(t, lp), p0)))
    # 01-04：画面に顔を近づける → 窓と見比べる
    M.peer(wp("01-04", "夢中") - 0.3, 1.4); ev(wp("01-04", "夢中"), "beep_happy", 0.3, "maru_c")
    M.at(s("02-03") + 0.2, face=MFACE(40.0))               # 左の窓の外を見る
    M.at(e("02-03") + 0.1, face=MFACE(0.0))
    M.confused(s("02-04") + 0.3)
    # 曲がり終わって、その場で前（+y）へ向き直る。屋根の上から見ている間
    M.at(t_turn_end + 0.3, face=MFACE(90.0))
    M.at(s("03-03") - 0.6, face=MFACE(90.0 + 80.0))       # 左の窓（外のカメラ）へ顔を向けてから（v1 の点検：顔が見えず、しょんぼりが分からなかった）
    M.sigh(s("03-03") + 0.6)                                # しょんぼり
    M.at(s("04-03") + 0.1, face=MFACE(90.0 + 45.0))         # 窓の外をきょろきょろ
    M.at(s("04-03") + 1.4, face=MFACE(90.0 - 10.0))
    M.confused(e("04-03") - 0.6)
    M.at(s("04-11") + 0.2, face=MFACE(90.0 + 85.0)); M.at(s("04-11") + 2.4, face=MFACE(90.0 - 30.0)); M.at(e("04-11") + 0.9, face=MFACE(90.0))
    # 04-09：列の先が霧の中へ（このときだけ白い板を重ねる）
    fogm = mat("fog", "#F4EEE8", rough=1.0, alpha=0.30)    # v1 の点検：0.22・60 m からでは、霧に消えていくのが見えなかった
    for k in range(14):
        pl = plane(fogm, (-2.0, 34.0 + k * 6.0, 4.0), (40, 14), rot=(R(90), 0, 0))
        hide_key(pl, -100.0, True); hide_key(pl, s("04-09") - 0.2, False); hide_key(pl, e("04-09") + 0.6, True)


def MFACE(head_deg):
    """まるロボの face（前の体の決まり）を、世界の向き（0＝+x・90＝+y）から出す"""
    return head_deg + 90.0 + MFACE_OFF


MFACE_OFF = float(os.environ.get("MFACE_OFF", "0"))


# ======================================================================== G：地球（04-07）
def b_globe(par):
    world("#0E1430", 0.4)
    bpy.ops.object.light_add(type='SUN', rotation=(R(50), 0, R(30))); bpy.context.object.data.energy = 3.0
    g = globe((0, 0, 0), 3.0)
    t0 = s("04-07") - 0.2; t1 = e("04-07") + 0.5
    key(g, "rotation_euler", t0 - 1.0, (0, 0, 0), "LINEAR"); key(g, "rotation_euler", t1 + 2.0, (0, 0, R(40)), "LINEAR")
    # 光る道の線：地球にぐるぐる巻きつく（うず巻きの線。だんだんのびる）
    cu = bpy.data.curves.new("wrap", "CURVE"); cu.dimensions = '3D'; sp = cu.splines.new('POLY')
    N = 900; sp.points.add(N - 1)
    for i in range(N):
        u = i / (N - 1); th = u * 2 * math.pi * 9; ph = -1.25 + 2.5 * u
        rr = 3.06
        sp.points[i].co = (rr * math.cos(ph) * math.cos(th), rr * math.cos(ph) * math.sin(th), rr * math.sin(ph), 1)
    cu.bevel_depth = 0.022; cu.bevel_resolution = 2
    ob = bpy.data.objects.new("wrap", cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(glow_mat("wrapg", "#FFE08A", 5.0)); ob.parent = g
    cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=f(wp("04-07", "地球") - 0.3))
    cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=f(e("04-07") - 0.2))
    ev(wp("04-07", "地球") - 0.3, "wrap", 0.35, "")


# ======================================================================== B：昼の大通りと歩道橋・感知器（1章・2章）
BR_H = 5.0
SPOT = (0.82, LANE_Y, BR_H)          # まるロボが立つ所（歩道橋の上、+x 側の手すりの前。真下は感知器のある車線）。0.95 ではのぞきこむと手すりの棒に入った（hitcheck）
EYE = (SPOT[0] + 0.14, SPOT[1], BR_H + 0.30)


def b_bridge(par):
    sky_day()
    road_strip((-260.0, 260.0), 520.0, "x")
    for sg, sd in ((+1, 21), (-1, 22)):
        city_side(-260.0, 260.0, ROAD_W / 2 + SIDEWALK + 0.3, sg, seed=sd)
    overpass(0.0, BR_H)
    box, eye = gantry(SENSOR_X, LANE_Y); track("sensor", box, 0.0)
    T_BEG = max(0.0, s("05-01") - 3.0); T_END = e("10-01") + 3.0
    tw0, tw1 = s("08-01") - 4.0, e("08-04") + 1.0     # 横から見る図の間は、感知器の車線をあける（見せる車だけ通す）
    traffic([(LANE * 0.5, +1)], T_BEG, T_END, -260.0, 260.0, 11.0, 2.4, seed=31)
    traffic([(LANE_Y, +1)], T_BEG, tw0, -260.0, 260.0, 11.0, 2.6, seed=32)
    traffic([(LANE_Y, +1)], tw1, T_END, -260.0, 260.0, 11.0, 2.6, seed=33)
    traffic([(-LANE * 0.5, -1), (-LANE_Y, -1)], T_BEG, T_END, -260.0, 260.0, 11.0, 2.3, seed=34)
    # まるロボ：階段の上から、手すりの前へ歩く（05-01）
    # まるロボ：歩道橋の上を歩いてきて、手すりの前で止まる（05-01）。この大きさは約 0.4 m/秒なので、近くから（B05 の試し：8 m では 1.7 秒遅れた）
    M = MaruR((0.8, LANE_Y + 1.15, BR_H), face=MFACE(-80.0), s=MS); track("maru", M.body, 0.28); track("maru_top", M.body, 0.34)
    M.walk(s("05-01") - 0.3, e("05-01") + 0.2, SPOT)
    M.at(s("05-02") + 1.2, face=MFACE(0.0))                # 着いてから向き直る（向くのに約 2 秒。言い終わる前に向き終わる）
    M.peer(s("05-02") + 1.6, 1.6)
    # 05-03：目の光で 1 台ずつ（ピッ、ピッ）
    for k, wd in enumerate(("ピッ、ピ", "ピッ。")):
        tb = wp("05-03", "1台") + 0.4 + 0.55 * k
        tgt = (SPOT[0] + 5.0 + 2.5 * k, LANE_Y, 1.45)
        beam_flash(EYE, tgt, tb, 0.4); mk = sphere(glow_mat("mark", TEAL_C, 5.0), tgt, 0.18, seg=12); pop_in(mk, tb, 1.0, 0.15); pop_out(mk, tb + 1.0)
        ev(tb, "pi", 0.35, "maru_c")
    # 05-05：右の車線も、左の車線も……ピピピピッ（首を振って 4 本）
    M.shake(s("05-05") + 0.2)
    for k in range(4):
        tb = wp("05-05", "ピピ") + 0.12 * k
        tgt = (SPOT[0] + 4.0 + 1.5 * k, LANE_Y - LANE * (k % 2) * 1.0, 1.45)
        beam_flash(EYE, tgt, tb, 0.6 - 0.12 * k); ev(tb, "pi", 0.3, "maru_c")   # v1 の点検：0.25 秒ずつでは 2 本しか見えなかった。4 本目が出るまで全部残す
    # 05-06：くるくる → ぽてん
    M.wobble(s("05-06") + 0.1, s("05-06") + 1.3, deg=16, period=0.35); ev(s("05-06") + 0.2, "dizzy", 0.35, "maru_c")
    M.act(s("05-06") + 1.4, "slump")
    M.act(s("06-04") + 0.2, "get_up")
    M.at(s("07-01") + 0.3, look=14)
    M.confused(s("07-04") + 0.3)
    M.at(e("07-04") + 0.2, look=0)
    # 08-05：感知器のまねで目の光を下へ
    M.at(s("08-05") + 0.2, look=-14)
    beam_flash(EYE, (SPOT[0] + 4.0, LANE_Y, 0.05), wp("08-05", "休まず") - 0.3, 1.2)   # v1 の点検：真下へ向けると歩道橋の床に隠れて見えなかった; ev(wp("08-05", "休まず") - 0.3, "pi", 0.3, "maru_c")
    M.at(e("08-05") + 0.1, look=0)
    M.at(s("10-01") + 0.2, look=12)
    # 感知器の音の波（08-01〜08-04）：水色の輪が真下へ → はね返って上へ
    wm = glow_mat("wave", WAVE_C, 6.0)
    def pulse(t, z_hit):
        bpy.ops.mesh.primitive_torus_add(location=(SENSOR_X, LANE_Y, 6.15), major_radius=0.45, minor_radius=0.06)   # v1 の点検：横から見ると細くて見えなかった
        r_ = bpy.context.object; r_.data.materials.append(wm)
        dd = (6.15 - z_hit) / 9.0
        hide_key(r_, -100.0, True); hide_key(r_, t, False); hide_key(r_, t + 2 * dd + 0.05, True)
        key(r_, "location", t, (SENSOR_X, LANE_Y, 6.15), "LINEAR"); key(r_, "location", t + dd, (SENSOR_X, LANE_Y, z_hit + 0.02), "LINEAR")
        key(r_, "location", t + 2 * dd, (SENSOR_X, LANE_Y, 6.15), "LINEAR")
        key(r_, "scale", t, (0.6, 0.6, 0.6), "LINEAR"); key(r_, "scale", t + dd, (1.6, 1.6, 1.0), "LINEAR"); key(r_, "scale", t + 2 * dd, (0.8, 0.8, 0.8), "LINEAR")
    tc = wp("08-03", "車が") + 0.3           # 見せる車が感知器の真下に来る時刻
    STAGE["tc"] = tc
    t = s("08-01") + 0.4
    while t < e("08-04") + 0.5:
        under = abs(t - tc) < 0.9
        pulse(t, 1.45 if under else 0.0)
        if not under: ev(t, "ping", 0.18, "sensor")
        t += 1.1
    ev(tc, "ping2", 0.3, "sensor")
    # 見せる車（08-03 で感知器の下を通る。08-04 でさらに 2 台）
    for k, tt in enumerate((tc, wp("08-04", "通った") + 0.2, wp("08-04", "こみ具合") + 0.2)):
        dc = car_fast((0, 0, 0), 0.0, ["#C8312B", "#3F6FB5", "#E8E8E8"][k], name="demo")
        key(dc, "location", tt - 4.0, (SENSOR_X - 4.0 * 7.0, LANE_Y, 0), "LINEAR"); key(dc, "location", tt + 4.0, (SENSOR_X + 4.0 * 7.0, LANE_Y, 0), "LINEAR")
        hide_key(dc, -100.0, True); hide_key(dc, tt - 4.0, False); hide_key(dc, tt + 4.0, True)
        g_ = sphere(glow_mat("count", WAVE_C, 6.0), (SENSOR_X + 0.75 + 0.42 * k, LANE_Y - 0.4, 6.45), 0.15, seg=12)   # たまっていく光の粒（v1 の点検：小さくて見えなかった。感知器の横に 1 列）
        pop_in(g_, tt + 0.1, 1.0, 0.2); hide_key(g_, -100.0, False); hide_key(g_, e("08-05") + 1.0, True)   # v1 の点検：隠す印が 1 つだけだと、ずっと隠れていた
    # 09-01：感知器から光の線が空へ
    lb = beam_flash((SENSOR_X, LANE_Y, 6.7), (SENSOR_X, LANE_Y, 60.0), wp("09-01", "どこへ") - 0.2, 2.5, WAVE_C, 0.05, "up")
    ev(wp("09-01", "どこへ") - 0.2, "swish", 0.3, "sensor")


# ======================================================================== T：町の引き（06-02・06-03・09-02・09-03・10-04・10-05）
def b_town(par):
    sky_day()
    roads, half = town_grid(9, 60.0)
    blk = 60.0
    # 06-03：道の角に人の印（小さな柱と丸い頭）がぽんぽん並ぶ
    pm = _m("pin", "#FF8A3D", rough=0.5)
    t = s("06-03") + 0.2; k = 0
    for i in range(10):
        for j in range(10):
            if (i + j) % 2: continue
            x, y = -half + i * blk, -half + j * blk
            ob = cyl(pm, (x, y, 8.0), 3.6, 16.0, verts=10); hd = sphere(pm, (0, 0, 11.5), 4.6, seg=12, parent=ob)   # v1 の点検：小さくて見えなかった
            tt = t + 0.12 * k * (1.0 - min(0.8, k / 60.0)); pop_in(ob, tt, 1.0, 0.2); hide_key(ob, -100.0, False); hide_key(ob, e("06-04") + 0.5, True)   # v1 の点検：人の印がずっと隠れていた（隠す印が 1 つだけ）
            if k % 4 == 0: ev(tt, "pop_s", 0.15, "")
            k += 1
    # 09-02・09-03：感知器（大きな道の角）→ 警察・道路の会社 → まとめる所 → 電波の塔 → 走る車
    POL = (-1.5 * blk, 1.0 * blk); CO = (1.5 * blk, 1.2 * blk); HUB = (0.0, 2.6 * blk); TOWER = (2.4 * blk, 2.8 * blk)
    track("police", cube(_m("police", "#3D6FB6", rough=0.5), (POL[0], POL[1], 9.0), (24, 18, 18)), 9.0)
    track("roadco", cube(_m("roadco", "#E58A3A", rough=0.5), (CO[0], CO[1], 8.0), (24, 18, 16)), 8.0)
    track("hub", cube(_m("hub", "#F4F4F0", rough=0.4), (HUB[0], HUB[1], 12.0), (34, 24, 24)), 12.0)
    track("tower", cyl(_m("tower", "#D9534F", rough=0.5), (TOWER[0], TOWER[1], 30.0), 1.5, 60.0, verts=12), 30.0)
    track("bridge", bpy.data.objects["bridge"], 1.0); track("tunnel", bpy.data.objects["tunnel"], 3.0)
    for k_ in range(4): cyl(_m("tower_w", "#F2F2F2"), (TOWER[0], TOWER[1], 8.0 + k_ * 14.0), 1.55, 5.0, verts=12)
    SENS = [(-half + 3 * blk, -half + 3 * blk), (-half + 6 * blk, -half + 3 * blk), (-half + 3 * blk, -half + 6 * blk), (-half + 6 * blk, -half + 6 * blk), (0.0, -half + 3 * blk)]
    sm = glow_mat("sens_t", WAVE_C, 6.0)
    for k_, (x, y) in enumerate(SENS):
        sp = sphere(sm, (x, y, 6.0), 9.0, seg=16); pop_in(sp, s("09-02") - 0.3 if k_ == 0 else s("10-04") + 0.3 + 0.25 * k_, 1.0, 0.2)   # v1 の点検：3.5 では引きの絵で見えなかった
        dk = cyl(glow_mat("sens_d", WAVE_C, 2.5), (x, y, 0.4), 22.0, 0.3, verts=32); pop_in(dk, s("10-04") + 0.3 + 0.25 * k_, 1.0, 0.25)
        if k_ > 0: ev(s("10-04") + 0.3 + 0.25 * k_, "ping", 0.25, "")
    def flow(pts, t0, t1, col=WAVE_C, nm="flow"):
        cu = bpy.data.curves.new(nm, "CURVE"); cu.dimensions = '3D'; sp_ = cu.splines.new('POLY'); sp_.points.add(len(pts) - 1)
        for i_, p_ in enumerate(pts): sp_.points[i_].co = (p_[0], p_[1], p_[2], 1)
        cu.bevel_depth = 1.0; ob_ = bpy.data.objects.new(nm, cu); bpy.context.collection.objects.link(ob_); ob_.data.materials.append(glow_mat(nm + "m", col, 5.0))
        cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=f(t0)); cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=f(t1))
        ev(t0, "swish", 0.25, "")
        hide_key(ob_, -100.0, False); hide_key(ob_, s("10-04") - 0.5, True)    # v1 の点検：10-04 で、09 の線が残って感知器の光と混ざっていた
        return ob_
    s0 = SENS[0]
    flow([(s0[0], s0[1], 6), ((s0[0] + POL[0]) / 2, (s0[1] + POL[1]) / 2, 40), (POL[0], POL[1], 20)], wp("09-02", "警察") - 0.2, wp("09-02", "警察") + 0.8, nm="f1")
    flow([(s0[0], s0[1], 6), ((s0[0] + CO[0]) / 2, (s0[1] + CO[1]) / 2, 40), (CO[0], CO[1], 18)], wp("09-02", "道路") - 0.2, wp("09-02", "道路") + 0.8, nm="f2")
    flow([(POL[0], POL[1], 20), ((POL[0] + HUB[0]) / 2, (POL[1] + HUB[1]) / 2, 45), (HUB[0], HUB[1], 26)], wp("09-03", "まとめる") - 0.2, wp("09-03", "まとめる") + 0.8, nm="f3")
    flow([(CO[0], CO[1], 18), ((CO[0] + HUB[0]) / 2, (CO[1] + HUB[1]) / 2, 45), (HUB[0], HUB[1], 26)], wp("09-03", "まとめる") - 0.1, wp("09-03", "まとめる") + 0.9, nm="f4")
    flow([(HUB[0], HUB[1], 26), ((HUB[0] + TOWER[0]) / 2, (HUB[1] + TOWER[1]) / 2, 55), (TOWER[0], TOWER[1], 60)], wp("09-03", "電波") - 0.4, wp("09-03", "電波") + 0.4, nm="f5")
    # 電波：塔から広がる輪
    for k_ in range(3):
        bpy.ops.mesh.primitive_torus_add(location=(TOWER[0], TOWER[1], 58.0), major_radius=4.0, minor_radius=0.5)
        rg = bpy.context.object; rg.data.materials.append(glow_mat("radio", "#FFE08A", 4.0)); t_ = wp("09-03", "電波") + 0.4 + 0.5 * k_
        hide_key(rg, -100.0, True); hide_key(rg, t_, False); hide_key(rg, t_ + 1.5, True)
        key(rg, "scale", t_, (1, 1, 1), "LINEAR"); key(rg, "scale", t_ + 1.5, (12, 12, 1), "LINEAR")
    ev(wp("09-03", "電波") + 0.4, "radio", 0.25, "")
    STAGE["half"] = half


# ======================================================================== N：車のナビの寄り（09-04・10-06）
def b_nav(par):
    world("#2A2F38", 0.6)
    area((0.4, 0.6, 1.6), (0.95, 0, 1.0), 120, 2.0)
    cr = car((0, 0, 0), 0.0, "#B9C3CF", interior=True, name="navcar"); STAGE["car"] = cr
    ph, _ = phone_on_holder(cr, [(0.0, os.path.join(TEX, "nav_red.png")), (s("10-01"), os.path.join(TEX, "nav_grey.png"))], glow=0.9); track("phone", ph, 0.0)
    ev(wp("09-04", "渋滞") - 0.2, "pop_ui", 0.3, "")


# ======================================================================== C：町はずれの道（10-02〜10-08）
def b_field(par):
    field_road()
    M = MaruR((-5.0, 4.6, 0.0), face=MFACE(0.0), s=MS); track("maru", M.body, 0.28); track("maru_top", M.body, 0.34)
    M.walk(s("10-02") + 0.3, e("10-02") + 0.6, (-1.0, 4.6, 0.0))
    M.at(s("10-03") + 0.2, look=15)
    M.at(e("10-03") + 0.3, look=0)
    M.at(s("10-07") + 0.3, face=MFACE(-60.0))
    M.confused(s("10-08") + 0.2)


# ======================================================================== カット
CUTS = [
    # 冒頭（A）
    ("A01", b_drive, s("01-01") - 0.5, C((-160.0, 2.0, 16.0), (-110.0, 4.0, 1.0), 30, (-145.0, 2.5, 12.0), (-95.0, 4.0, 1.0), d=5.0), "A"),
    ("A01b", b_drive, wp("01-01", "まるロボは"), CC((0.2, 3.2, 1.2), (0.1, 0.3, 1.0), 32), "A"),
    ("A01c", b_drive, s("01-02"), CC((2.7, 0.05, 1.28), (0.0, 0.0, 1.08), 26, (2.5, 0.0, 1.26), (0.0, 0.0, 1.08)), "A"),
    ("A01d", b_drive, s("01-03"), CC((0.35, 0.05, 1.18), (0.95, 0.0, 1.02), 30, (0.55, 0.03, 1.10), (0.95, 0.0, 1.02), d=3.0), "A"),
    ("A01e", b_drive, s("01-04"), CC((1.75, 0.55, 1.2), (0.15, 0.40, 0.95), 28), "A"),
    ("A02", b_drive, s("02-01"), CC((0.55, 0.0, 1.12), (0.95, 0.0, 1.02), 34), "A"),
    ("A02b", b_drive, s("02-03"), CC((7.0, 3.2, 2.8), (-1.5, -2.5, 0.7), 26), "A"),
    ("A02c", b_drive, s("02-04"), CC((1.75, 0.55, 1.2), (0.15, 0.40, 0.95), 28), "A"),
    ("A03", b_drive, s("03-01") - 0.2, C((-30.0, -16.0, 30.0), (-6.0, 8.0, 0.0), 26), "A"),
    ("A03b", b_drive, s("03-02"), C((-6.0, -4.0, 9.0), (-4.0, 40.0, 1.0), 28), "A"),
    ("A03c", b_drive, s("03-03"), CC((0.35, 2.3, 1.12), (0.15, 0.4, 1.0), 30), "A"),
    ("A03d", b_drive, s("03-04"), C((-3.0, 2.0, 14.0), (-4.0, 45.0, 1.0), 28), "A"),
    ("A04", b_drive, s("04-01"), C((8.0, 6.0, 26.0), (-4.0, 40.0, 0.0), 26, (8.0, 10.0, 26.0), (-4.0, 44.0, 0.0)), "A"),
    ("A04b", b_drive, s("04-02"), C((8.6, 26.0, 3.2), (-8.0, 22.0, 1.0), 24, (8.6, 44.0, 3.2), (-8.0, 40.0, 1.0)), "A"),
    ("A04c", b_drive, s("04-03"), CC((1.35, 1.55, 1.15), (0.17, 0.4, 1.02), 30), "A"),
    ("A04d", b_drive, s("04-04"), CC((0.55, 0.0, 1.12), (0.95, 0.0, 1.02), 34), "A"),
    ("G04", b_globe, s("04-07") - 0.2, C((0.0, -12.0, 2.5), (0.0, 0.0, 0.0), 40, (2.5, -9.5, 1.5), (0.0, 0.0, 0.0), d=9.0), "G"),
    ("A04e", b_drive, s("04-08"), CC((0.55, 0.0, 1.12), (0.95, 0.0, 1.02), 34), "A"),
    ("A04f", b_drive, s("04-09"), C((-6.0, 6.0, 1.4), (-5.0, 60.0, 1.6), 30), "A"),
    ("A04g", b_drive, s("04-10"), C((10.0, -6.0, 18.0), (-4.0, 40.0, 0.0), 24), "A"),
    ("A04h", b_drive, s("04-11"), CC((0.0, 2.35, 1.2), (0.17, 0.4, 1.0), 30, (0.45, 2.2, 1.16), (0.17, 0.4, 1.0), d=5.0), "A"),
    ("A04i", b_drive, s("04-12"), C((-14.0, -10.0, 6.0), (-4.0, 40.0, 3.0), 24, (-14.0, -10.0, 22.0), (-4.0, 50.0, 2.0)), "A"),
    # 1章（B 歩道橋 → T 町の引き）
    ("B05", b_bridge, s("05-01") - 0.5, C((-0.6, 9.2, 5.75), (0.8, 5.6, 5.2), 28, (-0.5, 8.6, 5.7), (0.9, 5.3, 5.2)), "B"),
    ("B05b", b_bridge, s("05-02"), C((-1.0, 7.6, 6.4), (6.0, 4.6, 2.0), 30), "B"),
    ("B05c", b_bridge, s("05-03"), C((-0.6, 6.4, 6.1), (7.0, 5.0, 1.2), 28), "B"),
    ("B05d", b_bridge, s("05-04"), C((-6.0, 10.0, 4.0), (10.0, 1.0, 1.0), 24), "B"),
    ("B05e", b_bridge, s("05-05"), C((2.6, 5.1, 5.2), (SPOT[0], SPOT[1], BR_H + 0.25), 34), "B"),
    ("B05f", b_bridge, s("05-06"), C((2.3, 6.3, 5.6), (SPOT[0], SPOT[1], BR_H + 0.2), 34), "B"),
    ("B06", b_bridge, s("06-01"), C((4.2, 2.6, 7.4), (0.7, LANE_Y + 0.3, 4.6), 26), "B"),
    ("T06", b_town, s("06-02"), C((0.0, -10.0, 520.0), (0.0, 0.0, 0.0), 30, (0.0, -10.0, 620.0), (0.0, 0.0, 0.0), d=9.0), "T"),
    ("B06b", b_bridge, s("06-04"), C((2.3, 6.6, 5.7), (SPOT[0], SPOT[1], BR_H + 0.2), 32), "B"),
    # 2章（B → T → N → C）
    ("B07", b_bridge, s("07-01"), C((-0.6, LANE_Y + 1.0, 5.3), (SENSOR_X, LANE_Y, 6.6), 26), "B"),
    ("B07b", b_bridge, s("07-02"), C((SENSOR_X - 5.0, LANE_Y - 4.0, 3.5), (SENSOR_X, LANE_Y, 6.4), 30, (SENSOR_X - 3.0, LANE_Y - 2.5, 4.5), (SENSOR_X, LANE_Y, 6.4), d=4.0), "B"),
    ("B07c", b_bridge, s("07-04"), C((3.3, 6.6, 5.5), (SPOT[0], SPOT[1], BR_H + 0.25), 30), "B"),
    ("B08", b_bridge, s("08-01") - 0.2, C((SENSOR_X, -3.4, 3.4), (SENSOR_X, LANE_Y, 3.4), 18), "B"),
    ("B08b", b_bridge, s("08-05"), C((2.6, 5.1, 5.2), (SPOT[0], SPOT[1], BR_H + 0.15), 30), "B"),
    ("B09", b_bridge, s("09-01"), C((SENSOR_X - 6.0, LANE_Y - 3.0, 1.5), (SENSOR_X, LANE_Y, 9.0), 22), "B"),
    ("T09", b_town, s("09-02"), C((-100.0, -260.0, 230.0), (0.0, 40.0, 0.0), 26, (40.0, -260.0, 230.0), (40.0, 60.0, 0.0), d=10.0), "T"),
    ("N09", b_nav, s("09-04"), CC((0.66, 0.0, 1.08), (0.95, 0.0, 1.02), 42), "N"),
    ("B10", b_bridge, s("10-01"), C((3.3, 6.6, 5.4), (SPOT[0], SPOT[1], BR_H + 0.3), 30), "B"),
    ("C10", b_field, s("10-02"), C((0.6, 1.4, 0.8), (-2.0, 4.6, 0.3), 32), "C"),
    ("C10b", b_field, s("10-03"), C((-2.3, 3.2, 0.35), (-0.4, 6.2, 5.0), 22), "C"),
    ("T10", b_town, s("10-04"), C((0.0, -420.0, 420.0), (0.0, 0.0, 0.0), 26, (120.0, -420.0, 420.0), (140.0, 60.0, 0.0), d=10.0), "T"),
    ("N10", b_nav, s("10-06"), CC((0.66, 0.0, 1.08), (0.95, 0.0, 1.02), 42), "N"),
    ("C10c", b_field, s("10-07"), C((1.5, 1.6, 0.8), (-1.0, 4.6, 0.25), 30), "C"),
    ("C10d", b_field, s("10-08"), C((0.4, 3.0, 0.45), (-1.0, 4.6, 0.25), 32), "C"),
    # 8 秒をこえる同じ絵を、文の切れ目で替える（下書きの最初の点検。決まり：同じ絵を 8 秒以上続けない）
    ("A02a", b_drive, s("02-02"), CC((0.62, -0.22, 1.16), (0.95, 0.02, 1.02), 38), "A"),
    ("A04d2", b_drive, s("04-05"), CC((0.6, 0.25, 1.15), (0.95, 0.0, 1.02), 36, (0.66, 0.18, 1.13), (0.95, 0.0, 1.02), d=4.0), "A"),
    ("A04d3", b_drive, s("04-06"), CC((0.55, -0.2, 1.12), (0.95, 0.03, 1.0), 40), "A"),
    ("T06b", b_town, s("06-03"), C((-200.0, -330.0, 160.0), (0.0, 0.0, 0.0), 26), "T"),
    ("B07b2", b_bridge, s("07-03"), C((SENSOR_X - 2.0, LANE_Y - 2.2, 5.0), (SENSOR_X, LANE_Y, 6.4), 34), "B"),
    ("B08a", b_bridge, s("08-02"), C((SENSOR_X + 3.0, -3.4, 3.3), (SENSOR_X, LANE_Y, 3.4), 18), "B"),
    ("B08c", b_bridge, s("08-03"), C((SENSOR_X - 1.0, -3.4, 3.4), (SENSOR_X, LANE_Y, 3.4), 18), "B"),
    ("B08d", b_bridge, s("08-04"), C((SENSOR_X - 2.5, -3.4, 3.5), (SENSOR_X + 0.6, LANE_Y, 3.6), 18), "B"),
    ("T09b", b_town, s("09-03"), C((180.0, -120.0, 200.0), (20.0, 120.0, 10.0), 26), "T"),
    ("T10b", b_town, s("10-05"), C((560.0, -300.0, 330.0), (190.0, 90.0, 0.0), 30), "T"),
]
END_T = e("10-08") + 2.0
CUTS.sort(key=lambda c: c[2])
CLIPS = {}
for i, (nm, fn, tc, cm, par) in enumerate(CUTS):
    t0 = max(0.0, tc - 0.1)
    t1 = (CUTS[i + 1][2] + 0.75) if i + 1 < len(CUTS) else END_T
    CLIPS[nm] = (fn, t0, t1, cm, par)


if __name__ == "__main__" or True:
    if CLIPNAME == "--list":
        print(json.dumps({k: [round(v[1], 3), round(v[2], 3), round(([c[2] for c in CUTS if c[0] == k] or [v[1]])[0], 3), v[4]] for k, v in CLIPS.items()}))
    else:
        fn, t0, t1, cm, par = CLIPS[CLIPNAME]
        CLOCK["T0"] = t0; CLOCK["T1"] = t1
        fn(par)
        if os.environ.get("MARU_PLANONLY"):
            for m_ in MARU_ALL:
                m_.plan(END_T)
            print("MARU_LATE", json.dumps(MARU_LATE, ensure_ascii=False)); sys.exit(0)
        bake_maru(t0, t1)
        if cm is not None: cm(t0)
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
