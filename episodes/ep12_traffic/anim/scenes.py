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
_hide_key0 = hide_key


def hide_key(ob, t, hidden):
    """12本目 v1 の点検：消す時刻のキーだけを打つと、その前もずっと消えたまま（人の印・光の粒が一度も映らなかった。SKILL §5 の決まりを、守らなくても大丈夫な形に）。
    まだキーのない物の最初のキーが「消す」なら、先に「-100 秒で見える」を打つ"""
    ad = ob.animation_data
    has = ad and ad.action and any(fc.data_path == "hide_render" for fc in ad.action.fcurves)
    if hidden and not has and t > -100.0: _hide_key0(ob, -100.0, False)
    _hide_key0(ob, t, hidden)


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
RT = 3.2                      # 曲がる半径（v1 の確認役：6 m では角の歩道を横切った。道の角から 1.1 m 離れるのは 3.3 m 以下）
XS = -LANE_Y - RT             # 曲がり始める x
Y_STOP = 15.0                 # 列のうしろで止まる y
D_TURN = 1.1; D_STOP = 1.8


def car_state(t):
    """おじさんの車の (x, y, 向き度)。向き 0＝+x、90＝+y"""
    T0 = STAGE["t_turn"]
    if t <= T0:     # 曲がる前の 1.5 秒で、曲がる速さ（弧の長さ ÷ D_TURN）までなめらかに落とす
        v1 = (math.pi / 2 * RT) / D_TURN; tau = T0 - t; tb = 1.5
        d_ = v1 * tau + (V_CAR - v1) / (2 * tb) * tau * tau if tau <= tb else v1 * tb + (V_CAR - v1) * tb / 2 + V_CAR * (tau - tb)
        return (XS - d_, LANE_Y, 0.0)
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
    road_strip((-340.0, 80.0), 420.0, "x", gaps=[(+1, -ROAD_W / 2, ROAD_W / 2)])   # 曲がる先の道の入り口は、歩道を切る
    road_strip((ROAD_W / 2, 200.0), 200.0, "y")
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
    cr = car((0, 0, 0), 0.0, "#7CC6E8", interior=True, name="ojicar"); STAGE["car"] = cr; track("owncar", cr, 2.2)
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
    # v1 の確認役：01-04 の「夢中」で、スマホの背中が黒い棒にしか見えなかった → 画面の明かりが、のぞきこむまるロボの顔に当たる（画面から後ろ＝−x へ）
    bpy.ops.object.light_add(type='AREA', location=(PHONE_L[0] - 0.03, 0.0, PHONE_L[2] + 0.02), rotation=(0, R(90), 0)); sl = bpy.context.object
    sl.data.energy = 6.0; sl.data.size = 0.16; sl.data.color = (0.80, 0.95, 1.0); sl.parent = cr
    p_, head = ojisan(cr)
    t = T_BEG; k_ = 0
    while t < T_END:      # 鼻歌：頭を小さくゆらす（前を向いたまま）
        key(head, "rotation_euler", t, (R(-3 if k_ % 2 else 3), 0, R(2 if k_ % 2 else -2))); t += 0.6; k_ += 1
    t_turn_end = STAGE["t_turn"] + D_TURN
    ph, scr = phone_on_holder(cr, [(0.0, os.path.join(TEX, "ph_map_a.png")), (wp("02-02", "渋滞") - 0.1, os.path.join(TEX, "ph_map_alert.png")),
                                   (t_turn_end, os.path.join(TEX, "ph_map_q.png")), (wp("04-05", "広げて"), os.path.join(TEX, "ph_map_z1.png")),
                                   (wp("04-06", "遠くの"), os.path.join(TEX, "ph_map_z2.png")), (s("04-08") - 0.3, os.path.join(TEX, "ph_map_eta.png"))])
    track("phone", ph, 0.0)
    # v1 の確認役：輪がスマホの真ん中に付き、赤い線・遠くの細い道に当たっていなかった → 画面の絵の上の点に付ける（割合は make_tex12.py の絵と同じ）
    track("ph_red", screen_pt(scr, 0.42, 0.34, "ph_red"), 0.0); track("ph_far", screen_pt(scr, 0.80, 0.24, "ph_far"), 0.0)
    track("ph_eta", screen_pt(scr, 0.81, 0.18, "ph_eta"), 0.0)
    ev(wp("02-02", "渋滞") - 0.1, "pop_ui", 0.35, "phone")
    # 走る音・曲がる・止まる
    ev(STAGE["t_turn"] + 0.1, "turn", 0.3, "car"); ev(t_turn_end + D_STOP - 0.6, "brake", 0.35, "car")
    # まるロボ：助手席のクッションの上（前を向く）。車に運ばれる（場所だけ。曲がり終わってから、その場で向きを直す）
    lp = (PASS[0] + 0.02, PASS[1], BOOST)
    p0 = car_point(T_BEG, lp)
    M = MaruR(p0, face=MFACE(0.0), s=MS); track("maru", M.body, 0.28); track("maru_top", M.body, 0.34)
    M.carry(T_BEG, T_END, lambda t, p0=p0: tuple(a - b for a, b in zip(car_point(t, lp), p0)))
    # 01-04：画面に顔を近づける → 窓と見比べる
    # v1 の確認役：「夢中」が絵に出ていない → スマホへ向いて顔を近づけ、窓とスマホを見比べてまたスマホへ
    M.at(s("01-04") + 0.1, face=MFACE(-27.0)); M.peer(s("01-04") + 1.2, 2.6)   # （v1 の確認役 2 回目）終わりの 1.5 秒だけ目を向けていた → 向き終わったらすぐ顔を近づけ、文の終わりまで
    ev(wp("01-04", "夢中"), "beep_happy", 0.3, "maru_c")
    # 窓との見比べは入れない（向くのに約 1.7 秒かかり、3.8 秒遅れた。MARU_LATE）
    M.at(s("02-03") + 0.2, face=MFACE(40.0))               # 左の窓の外を見る
    M.at(e("02-03") + 0.1, face=MFACE(0.0))
    M.tiltq(wp("02-04", "首を") - 0.2, deg=24.0, hold=1.3)   # （v1 の確認役 2 回目）10° では頭が傾いて見えなかった → 24° で止める（「？」と同じ時刻）
    # 曲がり終わって、その場で前（+y）へ向き直る。屋根の上から見ている間
    M.at(t_turn_end + 0.3, face=MFACE(90.0))
    M.at(s("03-03") - 0.6, face=MFACE(134.0))             # 前の斜めの窓（カメラ）へ顔を向けてから（v1 の確認役：しょんぼりが分からなかった）
    M.sigh(s("03-03") + 0.6)                                # しょんぼり：ため息・目線を下げ・前へ少し傾く
    M.droop(s("03-03") + 0.9, e("03-03") + 0.8)              # （v1 の確認役 2 回目）目が小さくなるだけで「ぼうぜん」に見えた → 前へ 16°・目線を下へ・アンテナが垂れる
    M.at(s("04-03") + 0.1, face=MFACE(90.0 + 45.0))         # 窓の外をきょろきょろ
    M.at(s("04-03") + 1.4, face=MFACE(90.0 - 10.0))
    M.tiltq(wp("04-03", "測って") - 0.2, deg=24.0, hold=1.6)   # （v1 の確認役 3 回目）「？」が 0.8 秒で消えた → 「測って」から 2 秒
    M.at(s("04-11") + 0.2, face=MFACE(90.0 + 85.0)); M.at(s("04-11") + 1.5, face=MFACE(90.0 + 35.0)); M.at(s("04-11") + 2.8, face=MFACE(90.0 + 85.0)); M.at(e("04-11") + 0.9, face=MFACE(90.0 + 85.0))   # 見回しても顔が窓（カメラ）から見える向きだけで（後ろ向きで頭しか見えなかった。v1 点検）
    ev(s("04-05") + 0.3, "zoom", 0.25, "")   # （v1 の確認役 3 回目）表の「シュー」（地図を広げる）が鳴っていなかった
    ev(s("04-11") + 0.3, "beep_think", 0.3, "maru_c")   # 表の「きょろきょろ」の電子音
    # 04-09：列の先が霧の中へ（このときだけ白い板を重ねる）
    fogm = mat("fog", "#F4EEE8", rough=1.0, alpha=0.45)    # v1 の点検：0.22・60 m からでは、霧に消えていくのが見えなかった（確認役 2 回目：0.30 でも夕方のもやと変わらない → 0.45）
    for k in range(14):
        pl = plane(fogm, (-2.0, 34.0 + k * 6.0, 4.0), (40, 14), rot=(R(90), 0, 0))
        hide_key(pl, -100.0, True); hide_key(pl, s("04-09") - 0.2, False); hide_key(pl, s("04-10") + 0.02, True)   # （v1 の確認役 3 回目）次の場面へ替わる前に霧が晴れた → 前の場面は替わる間止めた絵なので、次のカットの頭で消す（4 回目：+0.9 では次のカット 04-10 に霧が映って晴れた）


def MFACE(head_deg):
    """まるロボの face（前の体の決まり）を、世界の向き（0＝+x・90＝+y）から出す"""
    return head_deg + 90.0 + MFACE_OFF


MFACE_OFF = float(os.environ.get("MFACE_OFF", "0"))


# ======================================================================== A2：3章の夕方の渋滞（列がのろのろ進む）と、D：空の地図・光る点（S11〜S16）
SKY_H = 18.0                  # 空の地図の高さ（道の真上）
Y_OWN3 = 40.0                 # 3章のおじさんの車の、列の中の場所（前に 12 台・後ろに 4 台）
V_Q = 0.4                     # 列の平均の速さ（m/秒）。止まっては少し進む
PT_LAT = 0.6                  # 点を道のまん中へ寄せる割合（地図の線は道のまん中に 1 本）
SKY_NEUTRAL = "#9FB4CC"


def q_off(t):
    """列の進んだ距離（3章のはじめから）。速さは V_Q*(1-0.8cos) で、止まりかけては進む"""
    u = max(0.0, t - (s("11-01") - 3.0)); P_ = 9.0
    return V_Q * (u - 0.8 * P_ / (2 * math.pi) * math.sin(2 * math.pi * u / P_))


def own3(t):
    return (-LANE_Y, Y_OWN3 + q_off(t), SKY_H)


def own_pt3(t):
    """おじさんの車の点（空の地図の上）の世界の場所"""
    return (-LANE_Y * (1 - PT_LAT), Y_OWN3 + q_off(t), SKY_H)


def sky_point(car_obj, t_rise, lat, col="#FFFFFF", r=0.9, d=2.5, t_hide=None, name="pt", z=None):
    """車の点：車の中のスマホの所から、真上の空の地図の高さへ上がり、そのあとは車について動く（車の子）。lat＝車の左（+y）へのずれ"""
    p_ = sphere(glow_mat(name, col, 5.0), (0.4, 0.0, 1.2), r, seg=12, parent=car_obj)
    hide_key(p_, -100.0, True); hide_key(p_, t_rise, False)
    if t_hide is not None: hide_key(p_, t_hide, True)
    key(p_, "location", t_rise, (0.4, 0.0, 1.2)); key(p_, "location", t_rise + d, (0.0, lat, SKY_H if z is None else z))
    # v3 の点検：カメラのすぐ横の車から上がる点が、雲のような大きな玉に映った → 小さく出て、上がりながら大きくなる
    key(p_, "scale", t_rise, (0.01, 0.01, 0.01)); key(p_, "scale", t_rise + 0.25, (0.3, 0.3, 0.3)); key(p_, "scale", t_rise + d, (1.0, 1.0, 1.0))
    return p_


def sky_line(p0, p1, w, states, name="sl", z=SKY_H, th=0.35):
    """空の地図の 1 本の線。states＝[(時刻, 色)]（最初の時刻から見える）。色の替わる所で、見える物を替える"""
    cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    sx = abs(p1[0] - p0[0]) + (w if p0[0] == p1[0] else 0.0); sy = abs(p1[1] - p0[1]) + (w if p0[1] == p1[1] else 0.0)
    obs = []
    for i_, (t_, col) in enumerate(states):
        o_ = cube(glow_mat("%s_%s" % (name, col), col, 0.7 if col == SKY_NEUTRAL else 2.2), (cx, cy, z), (sx, sy, th))   # 試しの絵：白い太い帯に見えた → 色をおさえる
        t_end = states[i_ + 1][0] if i_ + 1 < len(states) else 1e9
        hide_key(o_, -100.0, True); hide_key(o_, t_, False)
        if t_end < 1e8: hide_key(o_, t_end, True)
        obs.append(o_)
    return obs


def drive_set():
    """冒頭と同じ、夕方の大通りと曲がった先の道（動かない物だけ）"""
    sky_evening()
    road_strip((-340.0, 80.0), 420.0, "x", gaps=[(+1, -ROAD_W / 2, ROAD_W / 2)])
    road_strip((ROAD_W / 2, 200.0), 200.0, "y")
    cube(_m("ground_a", "#ADA69A", rough=0.9), (-130.0, 60.0, -0.06), (500.0, 400.0, 0.1))
    for sg in (-1, 1):
        cube(_m("corner_a", "#B4ADA1", rough=0.85), (sg * (ROAD_W / 2 + SIDEWALK / 2 + 0.15), ROAD_W / 2 + SIDEWALK / 2 + 0.15, 0.0735), (SIDEWALK + 0.3, SIDEWALK + 0.3, 0.147))
    city_side(-340.0, -ROAD_W / 2 - SIDEWALK - 4.0, ROAD_W / 2 + SIDEWALK + 0.3, +1, seed=1)
    city_side(-340.0, 80.0, ROAD_W / 2 + SIDEWALK + 0.3, -1, seed=2)
    city_side(ROAD_W / 2 + SIDEWALK + 4.0, 80.0, ROAD_W / 2 + SIDEWALK + 0.3, +1, seed=3)
    city_side(ROAD_W / 2 + SIDEWALK + 4.0, 200.0, ROAD_W / 2 + SIDEWALK + 0.3, -1, seed=4, axis="y")
    city_side(ROAD_W / 2 + SIDEWALK + 4.0, 200.0, ROAD_W / 2 + SIDEWALK + 0.3, +1, seed=5, axis="y")


def b_jam(par):
    """3章：冒頭と同じ所の渋滞（列はのろのろ進む）。車のスマホから点が上がり、空の地図に集まる。道の色が変わる"""
    drive_set()
    T_BEG = s("11-01") - 3.0; T_END = e("16-02") + 3.0
    t_up = s("12-02") + 0.2                    # まわりの車の点が上がりはじめる
    t_map = wp("12-03", "空へ") - 0.3             # 空の地図が出る
    rnd = random.Random(77)
    PTS = []
    # ---------------------------------------------------------------- 大通り：右の車線は 10 m/秒。左の車線は角の手前 50 m で 4 m/秒（冒頭の地図の黄色）
    def pt_rise(ta):
        return max(ta + 0.3, t_up + rnd.uniform(0.0, 5.0))
    for (c_, ta, tb, ly, dr) in traffic([(LANE * 0.5, +1)], T_BEG, T_END, -360.0, 100.0, 10.0, 3.6, seed=31):
        PTS.append(sky_point(c_, pt_rise(ta), -PT_LAT * ly, t_hide=tb))
    for (c_, ta, tb, ly, dr) in traffic([(-LANE * 0.5, -1), (-LANE * 1.5, -1)], T_BEG, T_END, -360.0, 100.0, 10.0, 3.4, seed=32):
        PTS.append(sky_point(c_, pt_rise(ta), PT_LAT * ly, t_hide=tb))
    t = T_BEG - 46.0
    while t < T_END:
        c_ = car_fast((0, 0, 0), 0.0, rnd.choice(CAR_COLS), name="slow")
        t1_ = t + 310.0 / 10.0; t2_ = t1_ + 43.0 / 4.0; t3_ = t2_ + 107.0 / 10.0
        key(c_, "location", t, (-360.0, LANE_Y, 0), "LINEAR"); key(c_, "location", t1_, (-50.0, LANE_Y, 0), "LINEAR")
        key(c_, "location", t2_, (-7.0, LANE_Y, 0), "LINEAR"); key(c_, "location", t3_, (100.0, LANE_Y, 0), "LINEAR")
        hide_key(c_, -100.0, True); hide_key(c_, t, False); hide_key(c_, t3_, True)
        PTS.append(sky_point(c_, pt_rise(t), -PT_LAT * LANE_Y, t_hide=t3_))
        t += 3.2 * rnd.uniform(0.8, 1.3)
    # ---------------------------------------------------------------- 曲がった先の道：両方向とも列（のろのろ）
    Q = []
    for k in range(-4, 13):
        if k != 0: Q.append((-LANE_Y, Y_OWN3 + 5.6 * k, +1, CAR_COLS[(k + 9) % len(CAR_COLS)]))
        Q.append((-LANE * 0.5, Y_OWN3 + 2.5 + 5.9 * k, +1, CAR_COLS[(k + 13) % len(CAR_COLS)]))
    for k in range(18):
        Q.append((LANE * 0.5, 78.0 + 5.8 * k, -1, CAR_COLS[(k + 2) % len(CAR_COLS)]))
        Q.append((LANE_Y, 80.5 + 6.1 * k, -1, CAR_COLS[(k + 6) % len(CAR_COLS)]))
    for (lx, y0, dr, col) in Q:
        c_ = car_fast((lx, y0, 0.0), 90.0 if dr > 0 else -90.0, col, brake=(dr > 0), name="q3")
        t = T_BEG
        while t <= T_END:
            key(c_, "location", t, (lx, y0 + dr * q_off(t) * (1.0 if dr > 0 else 0.8), 0.0), "LINEAR"); t += 0.5
        # 「前の車からも、後ろの車からも」：おじさんの車に近い順に、0.4 秒ごと
        near = abs(y0 - Y_OWN3) + (0 if dr > 0 else 30.0)
        PTS.append(sky_point(c_, t_up + 0.15 + min(near * 0.04, 7.0) + rnd.uniform(0, 0.25), PT_LAT * lx * (1 if dr > 0 else -1)))
    ev(t_up + 0.2, "pop_s", 0.15, "owncar"); ev(t_up + 0.7, "pop_s", 0.15, "owncar"); ev(t_up + 1.3, "pop_s", 0.15, "owncar"); ev(t_up + 2.0, "pop_s", 0.15, "owncar")
    # ---------------------------------------------------------------- おじさんの車（列の中ほど）
    cr = car((0, 0, 0), 0.0, "#7CC6E8", interior=True, name="ojicar"); STAGE["car"] = cr; track("owncar", cr, 1.0); track("car", cr, 1.0)
    t = T_BEG
    while t <= T_END:
        key(cr, "location", t, (-LANE_Y, Y_OWN3 + q_off(t), 0.0), "LINEAR"); key(cr, "rotation_euler", t, (0, 0, R(90.0)), "LINEAR"); t += 1.0 / 6
    bpy.ops.object.light_add(type='AREA', location=(0.1, 0.1, 1.45)); il = bpy.context.object; il.data.energy = 18.0; il.data.size = 0.9
    bpy.ops.object.light_add(type='AREA', location=(-0.95, 0.0, 1.35), rotation=(0, R(-80), 0)); il2 = bpy.context.object; il2.data.energy = 45.0; il2.data.size = 1.0
    il2.data.color = (1.0, 0.92, 0.82); il2.parent = cr; il.data.color = (1.0, 0.93, 0.85); il.parent = cr
    bpy.ops.object.light_add(type='AREA', location=(PHONE_L[0] - 0.03, 0.0, PHONE_L[2] + 0.02), rotation=(0, R(90), 0)); sl = bpy.context.object
    sl.data.energy = 6.0; sl.data.size = 0.16; sl.data.color = (0.80, 0.95, 1.0); sl.parent = cr
    p_, head = ojisan(cr)
    t = T_BEG; k_ = 0
    while t < T_END:
        key(head, "rotation_euler", t, (R(-3 if k_ % 2 else 3), 0, R(2 if k_ % 2 else -2))); t += 0.6; k_ += 1
    ph, scr = phone_on_holder(cr, [(0.0, os.path.join(TEX, "ph_map_q.png"))]); track("phone", ph, 0.0)
    track("ph_tri", screen_pt(scr, 0.42, 0.444, "ph_tri"), 0.0)
    # おじさんの車の点（青緑）：「ぽうっと」で画面から出て、屋根の下まで → 外のカメラに替わる所で屋根の上へ → 空の地図へ
    ta_ = wp("11-04", "スマホ") - 0.1; tb_ = wp("11-04", "上がって") + 0.3     # 「スマホから」で画面から出て、ゆっくり屋根の下まで（「ぽうっと」と「上がって」は 0.5 秒しか離れていない）
    op = sphere(glow_mat("pt_own", TEAL_C, 6.0), (PHONE_L[0] - 0.05, 0.0, 1.05), 0.05, seg=16, parent=cr)   # 空では 22 倍（半径 1.1 m）
    hide_key(op, -100.0, True); hide_key(op, ta_, False)
    key(op, "location", ta_, (PHONE_L[0] - 0.05, 0.0, 1.05)); key(op, "location", tb_ - 0.15, (PHONE_L[0] - 0.12, 0.0, 1.33))
    key(op, "location", tb_ + 0.25, (0.6, 0.0, 2.3)); key(op, "location", tb_ + 3.8, (0.0, -PT_LAT * LANE_Y, SKY_H))   # 車の左（+y）は世界の −x。道のまん中（+x）へ寄せる
    key(op, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(op, "scale", ta_, (0.001, 0.001, 0.001)); key(op, "scale", ta_ + 0.5, (0.45, 0.45, 0.45))   # v3 の点検：「小さな光の点」なのに、車の中で大きな玉（半径 5 cm を 0.8 m 先から）に見えた → 車の中は 0.45 倍
    key(op, "scale", tb_ + 0.3, (0.45, 0.45, 0.45)); key(op, "scale", tb_ + 0.9, (4.0, 4.0, 4.0)); key(op, "scale", tb_ + 2.6, (8.0, 8.0, 8.0)); key(op, "scale", tb_ + 3.8, (22.0, 22.0, 22.0))   # v3 の点検：見上げるカメラ（A31e）で、空に月のような大きな玉 → 見上げる間は小さく、引きのカメラ（A31f）に替わる所で大きく   # 外のカメラでは、屋根の上に出たらすぐ見える大きさに   # 試しの絵：車の中で大きくなり、画面いっぱいの玉になった → 外に出てから大きく      # 空では、ほかの点より少し大きく（半径 1.1 m）
    track("ownpt", op, 0.0)
    ev(ta_ + 0.1, "float", 0.3, "phone"); ev(tb_ + 0.3, "float", 0.25, "owncar")
    # ---------------------------------------------------------------- まるロボ：助手席。12-01 で左の窓へ寄り、見上げる
    lp = (PASS[0] + 0.02, PASS[1], BOOST)
    def cpt(t, extra=0.0):
        x, y, _ = own3(t); return (x - lp[1] - extra, y + lp[0] + extra * 0.75, lp[2])      # 車は +y 向き：車の前＝+y・左＝−x
    t_win = s("12-01") + 0.2
    # v3 の点検：窓の内側（0.13 m）では屋根で空が見えず、外のカメラからは正面を向いて立つだけだった（「窓から顔を出して見上げる」が伝わらない）
    #   → 窓のふち（高さ 0.86＝クッションと同じ）へ 0.34 m 出て、体の半分を車の外へ。まん中の柱（x=0.02）に当たらず、驚いて後ろへ跳んでも柱に隠れないよう、前へ（0.26 m）
    def win_ext(t):
        u = min(1.0, max(0.0, (t - t_win) / 1.0)); return 0.34 * (u * u * (3 - 2 * u))
    p0 = cpt(T_BEG)
    M = MaruR(p0, face=MFACE(90.0), s=MS); track("maru", M.body, 0.28); track("maru_top", M.body, 0.34)
    M.carry(T_BEG, T_END, lambda t, p0=p0: tuple(a - b for a, b in zip(cpt(t, win_ext(t)), p0)))
    M.at(s("11-02") + 0.3, face=MFACE(90.0 - 20.0))                  # スマホの方を見る
    M.at(t_win, face=MFACE(180.0)); M.at(t_win + 0.9, look=28)       # 左の窓の外へ向き、見上げる
    M.surprise(wp("12-01", "みると") + 0.1)
    M.lookup(t_win + 1.0, e("12-03") + 0.3, deg=-6.0, gaze=32.0)   # v3 の点検：見上げたのが分からなかった → 目を大きく上へ（体を大きくそらすと車の中へ下がり、柱と座席に隠れた）
    M.at(e("12-05") + 0.5, look=20)
    M.surprise(e("15-02") - 0.2)                                     # 驚く動きは 1.9 秒かかる。「ぴょんぴょん」に間に合うように、15-02 の言い終わりから
    M.hops(wp("15-03", "ぴょんぴょん") - 0.1, n=3, height=0.07)   # v3 の点検：0.05 では跳んだのが分かりにくかった（屋根の下なので 0.07 まで）
    M.at(e("15-04") - 0.5, look=28)
    # ---------------------------------------------------------------- 空の地図（板・線・町の網）
    plate = plane(mat("skyplate", "#22355A", rough=1.0, alpha=0.7), (-45.0, 70.0, SKY_H - 0.05), (310.0, 290.0))   # 試しの絵：0.42 では夕方の空の色がすけて茶色に見えた
    hide_key(plate, -100.0, True); hide_key(plate, t_map, False)
    t_g = wp("14-02", "緑") - 0.1; t_y = wp("14-02", "黄色") - 0.1; t_r = wp("14-03", "赤") - 0.1
    N0 = (t_map, SKY_NEUTRAL); FL = (wp("14-01", "変わって") - 0.2, "#FFFFFF")    # 14-01「変わっていきます」：線が白く光り、色が変わる前ぶれ
    lines = []
    lines += sky_line((-200.0, 0.0), (-50.0, 0.0), 6.0, [N0, FL, (t_g, GREEN_C)], "av_l")
    lines += sky_line((-50.0, 0.0), (-7.0, 0.0), 6.0, [N0, FL, (t_y, YELLOW_C)], "av_y")
    lines += sky_line((-7.0, 0.0), (110.0, 0.0), 6.0, [N0, FL, (t_g, GREEN_C)], "av_r")
    lines += sky_line((0.0, 3.0), (0.0, 200.0), 6.0, [N0, FL, (t_r, RED_C)], "jam")
    rr = random.Random(5)
    t16 = s("16-01") + 0.5
    for gx in (-180.0, -120.0, -60.0, 60.0):
        c1 = rr.choice([GREEN_C, GREEN_C, YELLOW_C, RED_C]); c2 = rr.choice([GREEN_C, YELLOW_C, GREEN_C])
        sky_line((gx, -60.0), (gx, 200.0), 3.0, [N0, (t16 + rr.uniform(0, 1.5), c1), (s("16-02") + rr.uniform(0, 2.0), c2)], "gx%d" % gx, th=0.25)
    for gy in (-60.0, 60.0, 120.0, 180.0):
        c1 = rr.choice([GREEN_C, GREEN_C, YELLOW_C, RED_C]); c2 = rr.choice([GREEN_C, YELLOW_C, GREEN_C])
        sky_line((-200.0, gy), (110.0, gy), 3.0, [N0, (t16 + rr.uniform(0, 1.5), c1), (s("16-02") + rr.uniform(0, 2.0), c2)], "gy%d" % gy, th=0.25)
    # 町の網の点（下の車は小さく遠いので、点だけ道に沿って動かす）
    pm = glow_mat("pt", "#FFFFFF", 5.0)
    for k, gx in enumerate((-180.0, -120.0, -60.0, 60.0)):
        for j in range(4):
            v_ = rr.choice([8.0, 8.0, 3.0, 0.8]); y_a = -60.0 + rr.uniform(0, 260.0); dr = rr.choice([-1, 1])
            o_ = sphere(pm, (gx, y_a, SKY_H), 0.9, seg=10); hide_key(o_, -100.0, True); hide_key(o_, t_map + rr.uniform(0, 3), False)
            key(o_, "location", t_map, (gx, y_a, SKY_H), "LINEAR"); key(o_, "location", T_END, (gx, max(-60.0, min(200.0, y_a + dr * v_ * (T_END - t_map))), SKY_H), "LINEAR")
    for k, gy in enumerate((-60.0, 60.0, 120.0, 180.0)):
        for j in range(4):
            v_ = rr.choice([8.0, 8.0, 3.0, 0.8]); x_a = -200.0 + rr.uniform(0, 310.0); dr = rr.choice([-1, 1])
            o_ = sphere(pm, (x_a, gy, SKY_H), 0.9, seg=10); hide_key(o_, -100.0, True); hide_key(o_, t_map + rr.uniform(0, 3), False)
            key(o_, "location", t_map, (x_a, gy, SKY_H), "LINEAR"); key(o_, "location", T_END, (max(-200.0, min(110.0, x_a + dr * v_ * (T_END - t_map))), gy, SKY_H), "LINEAR")
    ev(t_map + 0.1, "shimmer", 0.25, "")
    ev(t_g, "pop", 0.25, ""); ev(t_y, "pop", 0.25, ""); ev(t_r, "pop", 0.3, "")
    # ---------------------------------------------------------------- 13 章：100 m の区切り・のろのろの点を囲む枠
    wm = glow_mat("bar", "#FFFFFF", 4.0)
    t4 = wp("13-04", "100") - 0.2; t5 = wp("13-05", "1分") - 0.6
    for (bx, by, rot_, t0_, t1_, nm) in ((-150.0, 0.0, 0, t4, e("13-04") + 0.4, "br_a1"), (-50.0, 0.0, 0, t4, e("13-04") + 0.4, "br_a2"),
                                         (0.0, 70.0, 1, t5, e("13-05") + 0.4, "br_b1"), (0.0, 170.0, 1, t5, e("13-05") + 0.4, "br_b2")):
        b_ = cube(wm, (bx, by, SKY_H + 0.4), (1.4, 14.0, 1.4) if rot_ == 0 else (14.0, 1.4, 1.4))
        hide_key(b_, -100.0, True); hide_key(b_, t0_, False); hide_key(b_, t1_, True)
        # v3 の点検：寝かせた棒だけでは町の網の線と同じに見え、区切りが分からなかった → 板の上に立つ光る柱を足し、カメラも引いて両はしを入れる
        pp_ = cube(wm, (bx, by, SKY_H + 4.0), (1.4, 1.4, 8.0)); hide_key(pp_, -100.0, True); hide_key(pp_, t0_, False); hide_key(pp_, t1_, True)
    track("br_a", empty((-100.0, 0.0, SKY_H)), 0.0); track("br_b", empty((0.0, 120.0, SKY_H)), 0.0)
    track("av_mid", empty((-100.0, 0.0, SKY_H)), 0.0); track("jam_mid", empty((0.0, 95.0, SKY_H)), 0.0)
    ev(t4, "pop", 0.25, ""); ev(t5, "pop", 0.25, "")
    fm = glow_mat("frame", "#FFE08A", 4.0); fm2 = glow_mat("frame2", "#FFE08A", 9.0)
    t6 = wp("13-06", "同じ") - 0.1; t7 = s("13-07") + 0.2
    for m_, t0_, t1_ in ((fm, t6, t7), (fm2, t7, s("14-01") + 0.15)):   # v3 の点検：カットが替わる前（e+0.5）に消え、一瞬だけ枠のない絵が映った。溶け終わるまで残すと、次のカットの途中で急に消えた → 溶けている間（まん中）に消す
        for (cx_, cy_, sx_, sy_) in ((0.0, 12.0, 16.0, 0.6), (0.0, 178.0, 16.0, 0.6), (-8.0, 95.0, 0.6, 166.6), (8.0, 95.0, 0.6, 166.6)):
            f_ = cube(m_, (cx_, cy_, SKY_H + 0.5), (sx_, sy_, 0.6)); hide_key(f_, -100.0, True); hide_key(f_, t0_, False); hide_key(f_, t1_, True)
    # v3 の点検：枠の光を強めただけでは「枠の中が光る」が見えなかった → 枠の中を、うすい黄色で光らせる
    fill_ = plane(glow_mat("frame_fill", "#FFE08A", 1.2), (0.0, 95.0, SKY_H + 0.3), (16.0, 166.0)); hide_key(fill_, -100.0, True); hide_key(fill_, t7, False); hide_key(fill_, s("14-01") + 0.15, True)
    ev(t6, "swish", 0.25, ""); ev(t7, "ping", 0.25, "")
    STAGE["own_pt"] = own_pt3


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
    tw0, tw1 = s("08-01") - 0.5, e("08-04") + 0.6     # 横から見る図の間は、見える所の車をなくす（見せる車だけ通す）
    cars_ = traffic([(LANE * 0.5, +1)], T_BEG, T_END, -260.0, 260.0, 11.0, 2.4, seed=31)
    cars_ += traffic([(LANE_Y, +1)], T_BEG, T_END, -260.0, 260.0, 11.0, 2.6, seed=32)
    cars_ += traffic([(-LANE * 0.5, -1), (-LANE_Y, -1)], T_BEG, T_END, -260.0, 260.0, 11.0, 2.3, seed=34)
    # v1 の確認役：流れる車は、止める時刻のあとも最後まで走るので、車線をあける間にも通っていた（図の前を横切った）。
    #   あける間に、見える所（x0〜x1）を通る車は、まるごと出さない
    def clear(w0, w1, xa, xb, lanes=None):
        for (c_, ta, tb, ly, dr) in cars_:
            if lanes is not None and ly not in lanes: continue
            a_, b_ = (-260.0, 260.0) if dr > 0 else (260.0, -260.0)
            u0 = ta + (xa - a_) / (b_ - a_) * (tb - ta); u1 = ta + (xb - a_) / (b_ - a_) * (tb - ta)
            if min(u0, u1) < w1 and max(u0, u1) > w0: hide_key(c_, ta, True)
    clear(tw0, tw1, SENSOR_X - 45.0, SENSOR_X + 45.0)
    clear(s("05-03") - 0.5, e("05-03") + 0.3, -10.0, 45.0, lanes=[LANE_Y])     # 05-03：目の光を当てる車線は、見せる車だけ
    clear(s("05-05") - 0.5, e("05-05") + 0.6, -10.0, 45.0, lanes=[LANE_Y, -LANE_Y])
    # まるロボ：階段の上から、手すりの前へ歩く（05-01）
    # まるロボ：歩道橋の上を歩いてきて、手すりの前で止まる（05-01）。この大きさは約 0.4 m/秒なので、近くから（B05 の試し：8 m では 1.7 秒遅れた）
    M = MaruR((0.8, LANE_Y + 1.15, BR_H), face=MFACE(-80.0), s=MS); track("maru", M.body, 0.28); track("maru_top", M.body, 0.34)
    M.walk(s("05-01") - 0.3, e("05-01") + 0.2, SPOT)
    M.at(s("05-02") + 1.2, face=MFACE(0.0))                # 着いてから向き直る（向くのに約 2 秒。言い終わる前に向き終わる）
    M.peer(s("05-02") + 1.6, 1.6)
    # 05-03：目の光で 1 台ずつ（ピッ、ピッ）。v1 の確認役：光と音が「1台ずつ」の所で、声の「ピッ」より 1.5 秒早かった・車に当たらず印もなかった
    #   → 声の「ピッ」の頭ごとに、下を通る車へ光を当て、その車の屋根に印が付いて一緒に走っていく
    M.at(wp("05-03", "目の光") - 0.2, look=-22)
    for k in range(2):
        tb = wp("05-03", "ピッ", occ=k)
        xt = SPOT[0] + 5.0 + 1.5 * k
        dc = car_fast((0, 0, 0), 0.0, ["#E8E8E8", "#3F6FB5"][k], name="cnt")
        key(dc, "location", tb - 4.0, (xt - 11.0 * 4.0, LANE_Y, 0), "LINEAR"); key(dc, "location", tb + 4.0, (xt + 11.0 * 4.0, LANE_Y, 0), "LINEAR")
        hide_key(dc, -100.0, True); hide_key(dc, tb - 4.0, False); hide_key(dc, tb + 4.0, True)
        beam_flash(EYE, (xt, LANE_Y, 1.5), tb, 0.35)
        mk = sphere(glow_mat("mark", TEAL_C, 5.0), (0, 0, 1.62), 0.2, seg=12, parent=dc); pop_in(mk, tb, 1.0, 0.15)
        ev(tb, "pi", 0.35, "maru_c")
    M.at(e("05-03") + 0.3, look=0)
    for k_ in range(3): ev(s("05-04") + 0.4 + 1.1 * k_, "swish", 0.2, "")   # （v1 の確認役 3 回目）表の「車の音」が鳴っていなかった → 車が下を通りすぎる「すっ」を 3 回
    # 05-05：右の車線も、左の車線も……ピピピピッ（首を振って 4 本）
    # （v1 の確認役 2 回目）首を右・左へ振らず、光は 0.5 秒・カメラの手前へのびて、どの車線のどの車に当たったか見えなかった
    #   → 「右の」で右（−y の車線）、「左の」で左（+y の車線）を見る。「ピピピピッ」の 4 つの音ごとに、右・左・右・左の車線の車へ光を当て、文の終わりまで残す
    M.lookyaw(wp("05-05", "右の") - 0.1, -50.0, d=0.7, pitch=-15.0)   # （v1 の確認役 3 回目）後ろからでは右を見たのが分からなかった → 50°
    M.lookyaw(wp("05-05", "左の") - 0.1, 50.0, d=0.7, pitch=-15.0)
    t_p = wp("05-05", "ピピ"); t_p1 = e("05-05")
    for k in range(4):
        tb = t_p + (t_p1 - 0.25 - t_p) / 4.0 * k
        ly = -LANE_Y if k % 2 == 0 else LANE_Y; dr_ = -1 if ly < 0 else 1
        xt = SPOT[0] + 5.0 + 1.6 * k
        dc = car_fast((0, 0, 0), 0.0 if dr_ > 0 else 180.0, ["#E8E8E8", "#C8312B", "#3F6FB5", "#F2C14E"][k], name="cnt2")
        key(dc, "location", tb - 4.0, (xt - dr_ * 11.0 * 4.0, ly, 0), "LINEAR"); key(dc, "location", tb + 4.0, (xt + dr_ * 11.0 * 4.0, ly, 0), "LINEAR")
        hide_key(dc, -100.0, True); hide_key(dc, tb - 4.0, False); hide_key(dc, tb + 4.0, True)
        beam_flash(EYE, (xt, ly, 1.5), tb, 0.35)   # （v1 の確認役 3 回目）文の終わりまで残すと、車が走り去ったあと光が何もない道に当たっていた → 0.35 秒（印は車の屋根に残る）
        mk = sphere(glow_mat("mark", TEAL_C, 5.0), (0, 0, 1.62), 0.2, seg=12, parent=dc); pop_in(mk, tb, 1.0, 0.15)
        ev(tb, "pi", 0.3, "maru_c")
    # 05-06：くるくる → ぽてん
    M.dizzy(s("05-06") + 0.05, s("05-06") + 1.35, period=0.5); ev(s("05-06") + 0.2, "dizzy", 0.35, "maru_c")   # （v1 の確認役 2 回目）横へゆれるだけで、目が回って見えなかった → 目の黒い所と頭が円を描いて回る
    M.act(s("05-06") + 1.4, "slump", lift=-0.17, pitch=-30.0)   # （v1 の確認役 3 回目）4.8 cm 沈むだけで、座りこんで見えなかった（06-01 も立って見えた）
    M.act(s("06-04") + 0.2, "get_up")
    M.wobble(s("06-04") + 1.4, e("06-04") + 0.2, deg=12, period=0.6)   # （v1 の確認役 2 回目）表の「ふらふら立ち上がる」がなかった
    # v1 の点検：後ろからで、見上げたのが分からなかった → 「ふらふら」で小さくゆれ、「上を」で大きく見上げる（肩ごしに、見る先の感知器と 1 枚に）
    M.wobble(s("07-01") + 0.05, wp("07-01", "上を") - 0.4, deg=8, period=0.5)
    M.at(wp("07-01", "上を") - 0.1, look=22); M.lean(wp("07-01", "上を") - 0.1, e("07-01") + 0.6, deg=-24.0)   # （v1 の確認役 3 回目）後ろからは見上げたのが見えなかった → 体ごと後ろへそらす（アンテナが倒れる）
    M.tiltq(wp("07-04", "何を") - 0.2, deg=24.0, hold=1.3)                     # v1 の確認役：首をかしげる音が「？」より 1.4 秒早かった → 「？」と同じ時刻
    M.at(e("07-04") + 0.2, look=0)
    # 08-05：感知器のまねで目の光を下へ
    M.at(s("08-05") + 0.2, look=-14)
    beam_flash(EYE, (SPOT[0] + 7.0, LANE_Y, 0.05), wp("08-05", "休まず") - 0.3, 1.2)   # （v1 の確認役 2 回目）4 m 先では歩道橋の床を突き抜けた → 手すりの上を通って道へ
    ev(wp("08-05", "休まず") - 0.3, "pi", 0.3, "maru_c")   # v1 の点検：真下へ向けると歩道橋の床に隠れて見えなかった
    M.at(e("08-05") + 0.1, look=0)
    M.at(s("10-01") + 0.2, look=12)
    # 感知器の音の波（08-01〜08-04）：水色の輪が真下へ → はね返って上へ
    wm = glow_mat("wave", WAVE_C, 6.0)
    def pulse(t, z_hit):
        bpy.ops.mesh.primitive_torus_add(location=(SENSOR_X, LANE_Y, 6.15), major_radius=0.8, minor_radius=0.12)   # v1 の点検・確認役：横から見ると細く小さくて見えなかった
        r_ = bpy.context.object; r_.data.materials.append(wm)
        dd = (6.15 - z_hit) / 9.0
        hide_key(r_, -100.0, True); hide_key(r_, t, False); hide_key(r_, t + 2 * dd + 0.05, True)
        key(r_, "location", t, (SENSOR_X, LANE_Y, 6.15), "LINEAR"); key(r_, "location", t + dd, (SENSOR_X, LANE_Y, z_hit + 0.02), "LINEAR")
        key(r_, "location", t + 2 * dd, (SENSOR_X, LANE_Y, 6.15), "LINEAR")
        key(r_, "scale", t, (0.6, 0.6, 0.6), "LINEAR"); key(r_, "scale", t + dd, (1.6, 1.6, 1.0), "LINEAR"); key(r_, "scale", t + 2 * dd, (0.8, 0.8, 0.8), "LINEAR")
    tc = wp("08-03", "車が") + 0.3           # 見せる車が感知器の真下に来る時刻
    STAGE["tc"] = tc
    # v1 の確認役：波が、車が真下にいる時も地面ではね返り、ピコンが 1.1 秒ごとに 21 回鳴った
    #   → 車の時刻は、波がちょうど屋根に着くように出す。ほかの波は、車がいない時に地面へ着くものだけ。音は文の頭と、車ではね返った時だけ
    T_CARS = [tc, wp("08-04", "通った") + 0.2, wp("08-04", "こみ具合") + 0.2]
    V_W = 9.0; d_road = 6.15 / V_W; d_roof = (6.15 - 1.45) / V_W
    for tt in T_CARS:
        pulse(tt - d_roof, 1.45); ev(tt, "ping2", 0.3, "sensor")
    t = s("08-01") + 0.4
    while t < e("08-04") + 0.5:
        # （v1 の確認役 4 回目）08-03 の車が止まりに来る間、道に落ちた輪が車の前を突き抜けた → 止まる車の来る 2.5 秒前から走り去るまで、道へは落とさない
        if all(abs(t + d_road - tt) > 0.8 and abs(t - (tt - d_roof)) > 0.7 for tt in T_CARS) and not (tc - 2.8 < t + d_road < e("08-03") + 1.6): pulse(t, 0.0)
        t += 1.3
    ev(s("08-01") + 0.4, "ping", 0.18, "sensor"); ev(s("08-02") + 0.1, "ping", 0.18, "sensor")
    # 08-03「短くなりました」：道までの線（水色・長い）と、車までの線（黄色・短い）を左右に並べて光らせる（絵コンテ表）
    tl_ = wp("08-03", "短く") - 0.3
    # （v1 の確認役 3 回目）細い白と薄い黄色で、車もいない時に出て、長さの差が分からなかった → 止まった車の屋根までの線（黄色）と、となりの道までの線（水色）を太く、車がいるうちに
    beam_flash((SENSOR_X, LANE_Y - 1.5, 6.15), (SENSOR_X, LANE_Y - 1.5, 0.02), tl_, e("08-03") + 0.6 - tl_, "#18B4E8", 0.11, "cmp_road")   # 4 回目：水色が白に見えた → こい水色
    beam_flash((SENSOR_X + 0.3, LANE_Y, 6.15), (SENSOR_X + 0.3, LANE_Y, 1.45), tl_ + 0.25, e("08-03") + 0.35 - tl_, "#FFC21A", 0.11, "cmp_car")
    ev(tl_, "pop_s", 0.2, "sensor")
    # 見せる車（08-03 で感知器の下を通る。08-04 でさらに 2 台）
    for k, tt in enumerate((tc, wp("08-04", "通った") + 0.2, wp("08-04", "こみ具合") + 0.2)):
        dc = car_fast((0, 0, 0), 0.0, ["#C8312B", "#3F6FB5", "#E8E8E8"][k], name="demo")
        if k == 0:                          # （v1 の確認役 3 回目）車が波の下を通りすぎて、はね返りが車か分からなかった → 感知器の真下で止まり、比べる線が消えてから走り出す
            t_go = e("08-03") + 0.4
            key(dc, "location", tt - 3.6, (SENSOR_X - 22.0, LANE_Y, 0), "LINEAR"); key(dc, "location", tt - 1.2, (SENSOR_X - 4.2, LANE_Y, 0))
            key(dc, "location", tt, (SENSOR_X, LANE_Y, 0)); key(dc, "location", t_go, (SENSOR_X, LANE_Y, 0)); key(dc, "location", t_go + 3.0, (SENSOR_X + 18.0, LANE_Y, 0), "LINEAR")
            hide_key(dc, -100.0, True); hide_key(dc, tt - 3.6, False); hide_key(dc, t_go + 3.0, True)
            continue
        key(dc, "location", tt - 4.0, (SENSOR_X - 4.0 * 7.0, LANE_Y, 0), "LINEAR"); key(dc, "location", tt + 4.0, (SENSOR_X + 4.0 * 7.0, LANE_Y, 0), "LINEAR")
        hide_key(dc, -100.0, True); hide_key(dc, tt - 4.0, False); hide_key(dc, tt + 4.0, True)                 # （v1 の確認役 2 回目）08-03 で、説明のない白い丸が「台数」の札より 5 秒早く出た → 数えるのは 08-04 の 2 台から
        g_ = sphere(glow_mat("count", "#18B4E8", 2.2), (SENSOR_X, LANE_Y - 1.0 - 0.75 * k, 5.55), 0.32, seg=12)   # 4 回目：白く小さく街灯の電球に見え、「台数」の札がかかった → こい水色で大きく、感知器の下に   # たまっていく光の粒（v1 の点検：小さくて見えなかった。感知器の横に 1 列）
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
    _pol = cube(_m("police", "#3D6FB6", rough=0.5), (POL[0], POL[1], 9.0), (24, 18, 18)); track("police", _pol, 9.0)
    _co = cube(_m("roadco", "#E58A3A", rough=0.5), (CO[0], CO[1], 8.0), (24, 18, 16)); track("roadco", _co, 8.0)
    # （v1 の確認役 3 回目）06-02 から青と橙の建物があり、何か分からなかった → 「警察」「道路」の言葉で出す
    # pop_in は大きさ（scale）を 1 にするので、大きさを scale で持つ箱が 1 m になって消えた（確認役 4 回目）→ 見える・見えないだけで出す
    hide_key(_pol, -100.0, True); hide_key(_pol, wp("09-02", "警察") - 0.3, False)
    hide_key(_co, -100.0, True); hide_key(_co, wp("09-02", "道路") - 0.3, False)
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
    # v1 の確認役：「電波で車のナビに届きます」で、車が映っていなかった → 塔の近くの道を走る車（模型に合わせて大きく）。輪が届く時刻に、車が光る
    ry = -half + round((TOWER[1] - 30.0 + half) / blk) * blk
    vc = car_fast((0, 0, 0), 0.0, "#7CC6E8", name="vcar"); vc.scale = (8.0, 8.0, 8.0)
    t0_ = s("09-03"); t1_ = e("09-03") + 1.0
    key(vc, "location", t0_, (TOWER[0] - 70.0, ry - 8.0, 0.0), "LINEAR"); key(vc, "location", t1_, (TOWER[0] + 10.0, ry - 8.0, 0.0), "LINEAR")
    hide_key(vc, -100.0, True); hide_key(vc, s("09-02"), False); hide_key(vc, s("10-04") - 0.5, True)
    track("vcar", vc, 6.0)
    ta_ = wp("09-03", "電波") + 1.2
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 9.0), major_radius=3.0, minor_radius=0.35); hl_ = bpy.context.object
    hl_.data.materials.append(glow_mat("radio_got", "#FFE08A", 5.0)); hl_.parent = vc; hl_.scale = (0.3, 0.3, 0.3)
    hide_key(hl_, -100.0, True); hide_key(hl_, ta_, False); hide_key(hl_, ta_ + 1.6, True)
    key(hl_, "scale", ta_, (0.15, 0.15, 0.15), "LINEAR"); key(hl_, "scale", ta_ + 0.8, (0.6, 0.6, 0.6), "LINEAR")
    ev(ta_, "pi", 0.2, "vcar")
    STAGE["half"] = half


# ======================================================================== N：車のナビの寄り（09-04・10-06）
def b_nav(par):
    # （v1 の確認役 3 回目）外が灰色の壁に見え、車の中と分からなかった → 前の窓の外に昼の道と前の車
    sky_day()
    road_strip((-200.0, 200.0), 400.0, "x", center=(0.0, -LANE * 0.5))   # 自分の車（y=0）が左の車線に来るように
    for sg, sd in ((+1, 41), (-1, 42)): city_side(-200.0, 200.0, ROAD_W / 2 + SIDEWALK + 0.3, sg, seed=sd)
    for x_, y_, c_ in ((14.0, 0.0, "#C8312B"), (26.0, LANE, "#3F6FB5"), (40.0, 0.0, "#E8E8E8")): car_fast((x_, y_, 0.0), 0.0, c_, name="ahead")
    area((0.4, 0.6, 1.6), (0.95, 0, 1.0), 120, 2.0)
    cr = car((0, 0, 0), 0.0, "#B9C3CF", interior=True, name="navcar"); STAGE["car"] = cr
    ph, _ = phone_on_holder(cr, [(0.0, os.path.join(TEX, "nav_green.png")), (wp("09-04", "渋滞") - 0.2, os.path.join(TEX, "nav_red.png")),
                                 (s("10-01"), os.path.join(TEX, "nav_grey.png"))], glow=0.9); track("phone", ph, 0.0)   # v1 の確認役：「ぽん」で何も出なかった → 赤い線が言葉の時刻に出る
    ev(wp("09-04", "渋滞") - 0.2, "pop_ui", 0.3, "")


# ======================================================================== C：町はずれの道（10-02〜10-08）
def b_field(par):
    field_road()
    M = MaruR((-5.0, 4.6, 0.0), face=MFACE(0.0), s=MS); track("maru", M.body, 0.28); track("maru_top", M.body, 0.34)
    M.walk(s("10-02") + 0.3, e("10-02") + 0.6, (-1.0, 4.6, 0.0))
    M.at(s("10-03") + 0.2, look=25); M.lean(s("10-03") + 0.2, e("10-03"), deg=-14.0)   # （v1 の確認役 3 回目）後ろからで見上げたのが見えなかった → 横から・体ごとそらす
    M.at(e("10-03") + 0.3, look=0)
    M.at(s("10-07") + 0.3, face=MFACE(-60.0))
    # （v1 の確認役 2 回目）10-07 で小窓と道を見比べる動きがなかった → 「冒頭の」で小窓（画面の左上＝まるロボの右上）を見上げ、「細い道」で道を見下ろす
    M.lookyaw(wp("10-07", "冒頭") - 0.1, -25.0, d=1.2, pitch=32.0)   # （v1 の確認役 3 回目）上でなく横を向いた・道と逆の右下を見た → 小窓（左上）へ上向きに、道（左下）へ下向きに
    M.lookyaw(wp("10-07", "細い道") - 0.1, -30.0, d=1.0, pitch=-30.0)
    M.tiltq(wp("10-08", "なぜ") - 0.2, deg=24.0, hold=1.2)
    # 16-03・16-04（3章）：町はずれの道を 1 台の車が走り、点が上がる。空の細い線（灰色）が、点が乗ると緑に
    # v3 の点検：遠くに残ったまるロボが、何か分からない白い点に見えた → 16-03 の前に、カメラの後ろへ移す
    t3 = s("16-03") - 0.6; FZ = 10.0
    M.at(t3 - 0.5, loc=(-1.0, 4.6, 0.0), interp="CONSTANT"); M.at(t3 - 0.45, loc=(-1.0, -80.0, 0.0), interp="CONSTANT")
    fc = car_fast((0, 0, 0), 0.0, "#D9A441", name="fcar"); track("fcar", fc, 1.0)
    # v3 の点検：車が画面に入る前に点が上がっていた（x=-34・6 m/s） → 画面の左の中から、カメラの動きに合わせて 3 m/s
    key(fc, "location", t3, (-8.0, -1.75, 0.0), "LINEAR"); key(fc, "location", e("16-04") + 2.0, (-8.0 + 3.0 * (e("16-04") + 2.0 - t3), -1.75, 0.0), "LINEAR")
    hide_key(fc, -100.0, True); hide_key(fc, t3, False)
    tr_ = wp("16-03", "細い道") - 0.2
    fp = sky_point(fc, tr_, 1.0, d=2.2, z=FZ); track("fpt", fp, 0.0)
    # v3 の点検：空の板（幅 16 m・高さ 12 m）がカメラに近すぎて、画面の上に大きな灰色の帯 → 幅 6 m・高さ 10 m・線も細く
    fpl = plane(mat("skyplate", "#22355A", rough=1.0, alpha=0.7), (0.0, 0.0, FZ - 0.05), (220.0, 6.0))
    hide_key(fpl, -100.0, True); hide_key(fpl, t3, False)
    sky_line((-110.0, 0.0), (110.0, 0.0), 2.0, [(t3, GREY_C), (tr_ + 2.3, GREEN_C)], "fline", z=FZ, th=0.3)
    ev(tr_ + 0.1, "float", 0.25, "fcar"); ev(tr_ + 2.3, "pop", 0.25, "")


# ======================================================================== カット
CUTS = [
    # 冒頭（A）
    ("A01", b_drive, s("01-01") - 0.5, C((-160.0, 2.0, 16.0), (-110.0, 4.0, 1.0), 30, (-145.0, 2.5, 12.0), (-95.0, 4.0, 1.0), d=5.0), "A"),
    ("A01b", b_drive, wp("01-01", "まるロボは"), CC((0.2, 3.2, 1.2), (0.1, 0.3, 1.0), 32), "A"),
    ("A01c", b_drive, s("01-02"), CC((2.7, 0.05, 1.28), (0.0, 0.0, 1.08), 26, (2.5, 0.0, 1.26), (0.0, 0.0, 1.08)), "A"),
    ("A01d", b_drive, s("01-03"), CC((0.35, 0.05, 1.18), (0.95, 0.0, 1.02), 30, (0.55, 0.03, 1.10), (0.95, 0.0, 1.02), d=3.0), "A"),
    ("A01e", b_drive, s("01-04"), CC((1.6, -0.25, 1.3), (0.5, 0.28, 1.0), 30), "A"),   # （v1 の確認役 2 回目）スマホが映らなかった → 少し上から、手前にスマホの背中   # v1 の確認役：まるロボがカメラを向いて立つだけで、スマホが映らず「夢中」が分からない → 前の窓の外の低い所から、手前にスマホの背中（カメラの穴つき）、奥にスマホへ顔を寄せるまるロボ
    ("A02", b_drive, s("02-01"), CC((0.55, 0.0, 1.12), (0.95, 0.0, 1.02), 52), "A"),   # v1 の確認役：画面が横幅の 4 割で小さかった
    ("A02b", b_drive, s("02-03"), CC((7.0, 3.2, 2.8), (-1.5, -2.5, 0.7), 26), "A"),
    ("A02c", b_drive, s("02-04"), CC((1.75, 0.55, 1.2), (0.15, 0.40, 0.95), 28), "A"),
    ("A03", b_drive, s("03-01") - 0.2, C((-30.0, -16.0, 30.0), (-6.0, 8.0, 0.0), 26), "A"),
    ("A03b", b_drive, s("03-02"), C((-6.0, -4.0, 9.0), (-4.0, 40.0, 1.0), 28), "A"),
    ("A03c", b_drive, s("03-03"), CC((1.5, 1.7, 1.25), (0.17, 0.4, 1.05), 30), "A"),   # v1 の確認役：しょんぼりが分からなかった → 前の斜めの窓の外から顔（後ろからは座席の背で隠れた）
    ("A03d", b_drive, s("03-04"), C((-3.0, 2.0, 14.0), (-4.0, 45.0, 1.0), 28), "A"),
    ("A04", b_drive, s("04-01"), C((8.0, 6.0, 26.0), (-4.0, 40.0, 0.0), 26, (8.0, 10.0, 26.0), (-4.0, 44.0, 0.0)), "A"),
    ("A04b", b_drive, s("04-02"), C((10.0, 26.0, 4.4), (-8.0, 22.0, 1.0), 24, (10.0, 44.0, 4.4), (-8.0, 40.0, 1.0)), "A"),   # v1 の確認役：手前の車がカメラのすぐ前を横切った → 歩道の奥・少し上から
    ("A04c", b_drive, s("04-03"), CC((1.35, 1.55, 1.15), (0.17, 0.4, 1.02), 30), "A"),
    ("A04d", b_drive, s("04-04"), CC((0.55, 0.0, 1.12), (0.95, 0.0, 1.02), 48), "A"),
    ("G04", b_globe, s("04-07") - 0.2, C((0.0, -15.0, 1.0), (0.0, 0.0, -0.85), 30, (2.2, -14.0, 0.8), (0.0, 0.0, -0.85), d=9.0), "G"),   # v1 の確認役：地球の上と下が切れ、巻きつく線が字幕の帯にかかった → 引いて、地球を上へ
    ("A04e", b_drive, s("04-08"), CC((0.55, 0.0, 1.12), (0.95, 0.0, 1.02), 48), "A"),
    ("A04f", b_drive, s("04-09"), C((-9.0, 5.0, 3.4), (-4.6, 60.0, 0.8), 30), "A"),   # v1 の確認役：真後ろの低い所からで、自分の車線の列が自分の車に隠れ「前がすいている」に見えた
    ("A04g", b_drive, s("04-10"), C((10.0, -6.0, 18.0), (-4.0, 40.0, 0.0), 24), "A"),
    ("A04h", b_drive, s("04-11"), CC((0.7, 2.3, 1.2), (0.17, 0.4, 1.0), 30, (0.95, 2.2, 1.18), (0.17, 0.4, 1.0), d=5.0), "A"),   # （v1 の確認役 3 回目）スマホの台の腕が目に刺さった棒に見えた → 少し上から（腕が目より下に）
    ("A04i", b_drive, s("04-12"), C((-14.0, -10.0, 6.0), (-4.0, 40.0, 3.0), 24, (-14.0, -10.0, 22.0), (-4.0, 50.0, 2.0)), "A"),
    # 1章（B 歩道橋 → T 町の引き）
    ("B05", b_bridge, s("05-01") - 0.5, C((0.55, 2.4, 5.75), (0.8, 5.9, 5.25), 30, (0.6, 2.7, 5.7), (0.8, 5.6, 5.25)), "B"),   # v1 の確認役：奥へ歩く背中だった → 前から、歩いてくる顔
    ("B05b", b_bridge, s("05-02"), C((-1.0, 7.6, 6.4), (5.5, 3.6, 2.3), 30), "B"),   # v1 の点検：まるロボが右の端で切れていた → 向きを左へ（画面の横 0.86 → 0.6）
    ("B05c0", b_bridge, s("05-03"), C((2.6, 5.1, 5.2), (SPOT[0], SPOT[1], BR_H + 0.25), 34), "B"),   # 「目の光で」：まるロボの顔の寄り（v1 の確認役：引きだけでは目が小さかった）
    ("B05c", b_bridge, wp("05-03", "1台") - 0.2, C((SPOT[0] - 1.1, LANE_Y + 0.25, BR_H + 1.45), (7.0, LANE_Y - 0.5, 0.6), 28), "B"),   # （v1 の確認役 2 回目）光の出どころのまるロボが見えなかった → 肩ごしに、まるロボの頭から下の車へ光がのびるのを
    ("B05d", b_bridge, s("05-04"), C((-6.0, 10.0, 4.0), (10.0, 1.0, 1.0), 24), "B"),
    ("B05e", b_bridge, s("05-05"), C((SPOT[0] - 1.9, LANE_Y + 0.4, BR_H + 1.7), (7.5, 0.2, 0.4), 26), "B"),   # （v1 の確認役 2 回目）肩ごしの上から、右・左を見るまるロボと、両方の車線の車に当たる光を 1 枚に
    ("B05f", b_bridge, s("05-06"), C((2.1, 4.95, 5.4), (SPOT[0], SPOT[1], BR_H + 0.2), 32), "B"),   # （v1 の確認役 3 回目）小さくガラスでかすみ、くるくるもぽてんも見えなかった → 寄る（ガラスもうすく）   # （v1 の確認役 2 回目）横からでは目が回るのが見えなかった → 前から、ぽてんまで体が全部入る引き
    ("B06", b_bridge, s("06-01"), C((2.9, 3.2, 6.5), (0.8, LANE_Y, 4.9), 26), "B"),   # （v1 の確認役 4 回目）まるロボが画面の幅の 5% で、座っているか分からなかった → 寄る
    ("T06", b_town, s("06-02"), C((0.0, -10.0, 520.0), (0.0, 0.0, 0.0), 30, (0.0, -10.0, 620.0), (0.0, 0.0, 0.0), d=9.0), "T"),
    ("B06b", b_bridge, s("06-04"), C((2.3, 6.6, 5.7), (SPOT[0], SPOT[1], BR_H + 0.2), 32), "B"),
    # 2章（B → T → N → C）
    ("B07", b_bridge, s("07-01"), C((1.75, LANE_Y - 1.2, BR_H + 0.3), (0.82, LANE_Y, BR_H + 0.34), 30), "B"),   # （v1 の確認役 3 回目）後ろ・肩ごしからは、感知器が遠く頭と同じ高さで、見上げたのが分からなかった（試しの絵 5 回）→ 横から、体ごと後ろへそらして目が上を向くのを。感知器は次の 07-02 で見せる   # v1 の確認役：上の機械が映らない（v1 の点検：斜め後ろの広い絵では、機械が小さく見上げたのも分からない → 肩ごしに、まるロボの頭と先の感知器を 1 枚に）
    ("B07b", b_bridge, s("07-02"), C((SENSOR_X - 16.0, LANE_Y - 1.0, 1.8), (SENSOR_X, LANE_Y + 1.5, 4.6), 26, (SENSOR_X - 10.0, LANE_Y - 1.0, 2.4), (SENSOR_X, LANE_Y + 1.0, 5.6), d=4.5), "B"),   # （v1 の確認役 2 回目）横からでは腕が奥へのびて、歩道の街灯に見えた → 道の先から、腕が道を横切って車の真上にあるのを   # v1 の確認役：道の上に張り出しているのが分からない → 下の道と車から寄る
    ("B07c", b_bridge, s("07-04"), C((2.1, 5.9, 5.45), (SPOT[0], SPOT[1], BR_H + 0.25), 32), "B"),   # （v1 の確認役 3 回目）画面の 1/12 で、首をかしげたのが見えなかった → 寄る
    ("B08", b_bridge, s("08-01") - 0.2, C((SENSOR_X + 10.0, LANE_Y - 3.6, 4.2), (SENSOR_X, LANE_Y + 0.4, 3.4), 24), "B"),   # （v1 の確認役 3 回目）腕がカメラの方を向き、波が柱をすべり下りる輪に見えた → 道の先から、腕が道を横切り、真下の車線へ波が落ちるのを   # v1 の確認役：4 つのカットがほぼ同じ絵で 22 秒 → カットごとに寄り方を替える
    ("B08b0", b_bridge, s("08-05"), C((2.6, 5.1, 5.2), (SPOT[0], SPOT[1], BR_H + 0.15), 30), "B"),   # （v1 の確認役 4 回目のあとの点検）横の引きでは「まるロボが目で」の所でまるロボが小さく何か分からない → 前半は顔の寄り
    ("B08b", b_bridge, wp("08-05", "この機械") - 0.3, C((2.6, LANE_Y - 5.4, BR_H + 1.0), (2.4, LANE_Y, BR_H - 1.5), 18), "B"),   # （v1 の確認役 3 回目）前からでは光が床ごしに下へ当たって見えた → 横から、光が手すりをこえて道へ届くのを
    ("B09", b_bridge, s("09-01"), C((SENSOR_X + 7.0, LANE_Y - 8.0, 4.0), (SENSOR_X, LANE_Y, 9.0), 26), "B"),   # （v1 の確認役 3 回目）左下の建物の角が大きな灰色の三角に見えた → 08 と同じ道の先の側から
    ("T09", b_town, s("09-02"), C((-100.0, -260.0, 230.0), (0.0, 40.0, 0.0), 26, (40.0, -260.0, 230.0), (40.0, 60.0, 0.0), d=10.0), "T"),
    ("N09", b_nav, s("09-04"), CC((-0.6, 0.0, 1.35), (1.2, 0.0, 1.05), 30, (0.62, 0.0, 1.1), (0.95, 0.0, 1.02), d=2.2), "N"),   # v1 の確認役：車の中か分からなかった → 前の座席の間の引き（ハンドル・前の窓）から画面へ寄る
    ("B10", b_bridge, s("10-01"), C((3.3, 6.6, 5.4), (SPOT[0], SPOT[1], BR_H + 0.3), 30), "B"),
    ("C10", b_field, s("10-02"), C((0.6, 1.4, 0.8), (-2.0, 4.6, 0.3), 32), "C"),
    ("C10b", b_field, s("10-03"), C((-0.6, 2.5, 0.15), (-0.9, 6.5, 1.5), 18), "C"),   # v1 の確認役：空と電柱だけで、まるロボがいない → 下の手前に見上げるまるロボ
    ("T10", b_town, s("10-04"), C((0.0, -420.0, 420.0), (0.0, 0.0, 0.0), 26, (120.0, -420.0, 420.0), (140.0, 60.0, 0.0), d=10.0), "T"),
    ("N10", b_nav, s("10-06"), CC((0.66, 0.0, 1.08), (0.95, 0.0, 1.02), 42), "N"),
    ("C10c", b_field, s("10-07"), C((0.5, 2.9, 0.6), (-1.6, 4.5, 0.32), 30), "C"),   # （v1 の確認役 2 回目）まるロボが小さく、小窓と道を見比べるのが見えなかった → 寄る
    # 3章（A2 渋滞 → D 空の地図 → C 町はずれ）
    ("A31", b_jam, s("11-01"), C((-8.0, 10.0, 10.0), (-4.0, 62.0, 1.0), 28), "J"),
    ("A31b", b_jam, s("11-02"), CC((1.5, 1.7, 1.25), (0.17, 0.4, 1.05), 30), "J"),
    ("A31c", b_jam, s("11-03"), CC((0.0, 0.0, 1.25), (0.95, 0.0, 1.02), 30, (0.5, 0.0, 1.15), (0.95, 0.0, 1.02), d=4.0), "J"),
    ("A31d", b_jam, s("11-04"), CC((0.05, 0.1, 1.22), (0.92, 0.0, 1.22), 34), "J"),
    ("A31e", b_jam, wp("11-04", "上がって") + 0.3, C((-5.25, Y_OWN3 + q_off(wp("11-04", "上がって")) - 22.0, 3.2), (-5.25, Y_OWN3 + q_off(wp("11-04", "上がって")) + 4.0, 3.0), 22, None, (-5.25, Y_OWN3 + q_off(wp("11-04", "上がって")) + 4.0, 11.0), 22, d=3.0), "J"),   # 点を追って見上げる。v3 の点検：9 m うしろから真上近くまで見上げると、すぐ上の街灯の玉だけが、何か分からない白い物に映った → 22 m うしろから、ゆるく見上げる
    ("A31f", b_jam, wp("11-05", "いまどこ") - 0.4, C((-3.5, Y_OWN3 + q_off(s("11-05")) - 34.0, 6.0), (-4.0, Y_OWN3 + q_off(s("11-05")), 9.0), 20), "J"),   # 試しの絵：歩道から（x=−8.6）では木に隠れた → 列の上から
    ("A32", b_jam, s("12-01"), CC((1.75, 2.2, 0.9), (0.45, 0.75, 1.45), 28), "J"),   # v3 の点検：真横からは正面を向いて立つだけで、見上げたのが分からなかった → 前の斜め下から（目が上を向くのが見える）
    ("A32b", b_jam, s("12-02"), C((-8.6, Y_OWN3 + q_off(s("12-02")) - 20.0, 1.4), (-3.0, Y_OWN3 + q_off(s("12-02")) + 6.0, 5.0), 20), "J"),
    ("A32c", b_jam, s("12-03"), CC((-1.6, 2.3, 0.95), (2.5, 0.1, 3.0), 18), "J"),   # v3 の点検：空の地図が見えず、まるロボの頭が切れた → 車の後ろの低い所から、見上げるまるロボ・点の列・空の地図
    ("A32d", b_jam, s("12-04"), CC((0.5, 0.0, 1.15), (0.95, 0.0, 1.02), 44), "J"),
    ("D12", b_jam, s("12-05"), C((-70.0, -50.0, 48.0), (-15.0, 50.0, 18.0), 26), "J"),
    ("D13", b_jam, s("13-01"), C((-50.0, -80.0, 80.0), (-15.0, 40.0, 18.0), 26, (-40.0, -60.0, 50.0), (-15.0, 40.0, 18.0), 26, d=3.6), "J"),
    ("D13b", b_jam, s("13-02"), C((-110.0, -38.0, 38.0), (-100.0, 0.0, 18.0), 28), "J"),
    ("D13c", b_jam, s("13-03"), C((-36.0, 60.0, 38.0), (0.0, 70.0, 18.0), 28), "J"),
    ("D13d", b_jam, s("13-04"), C((-100.0, -95.0, 62.0), (-100.0, 0.0, 18.0), 26), "J"),
    ("D13e", b_jam, s("13-05"), C((-85.0, 120.0, 64.0), (0.0, 120.0, 18.0), 26), "J"),
    ("D13f", b_jam, s("13-06"), C((-70.0, 95.0, 95.0), (0.0, 95.0, 18.0), 22), "J"),
    ("D14", b_jam, s("14-01"), C((-20.0, -140.0, 170.0), (-20.0, 50.0, 18.0), 26), "J"),
    ("D15", b_jam, s("15-01"), C((own_pt3(s("15-01"))[0] - 14.0, own_pt3(s("15-01"))[1] - 22.0, SKY_H + 14.0), own_pt3(s("15-01")), 30), "J"),
    ("D15b", b_jam, s("15-02"), C((-LANE_Y, own_pt3(s("15-02"))[1] - 1.0, 40.0), (-LANE_Y, own_pt3(s("15-02"))[1], 0.0), 55), "J"),   # v3 の点検：斜めからでは点と車が離れて見えた → 真上から。車の真上に置く（点と車が重なる所からでは、赤い線の下に車が隠れた）。点は車のすぐとなりに見える
    ("A35", b_jam, e("15-02") - 0.3, CC((1.75, 2.2, 0.9), (0.45, 0.75, 1.4), 42), "J"),   # v3 の点検：引きでは小さく跳ぶのが見えなかった → 寄る（42 mm）
    ("D15c", b_jam, s("15-04"), C((-LANE_Y, own_pt3(s("15-04"))[1] - 1.0, 40.0), (-LANE_Y, own_pt3(s("15-04"))[1], 0.0), 55), "J"),
    ("D15d", b_jam, s("15-05"), C((-40.0, -90.0, 110.0), (-20.0, 60.0, 18.0), 24), "J"),
    ("D16", b_jam, s("16-01"), C((-60.0, -200.0, 260.0), (-40.0, 70.0, 18.0), 24, (-60.0, -380.0, 480.0), (-40.0, 70.0, 0.0), 24, d=10.0), "J"),
    ("C16", b_field, s("16-03"), C((-12.0, -24.0, 3.0), (2.0, 0.0, 6.0), 26, (-4.0, -24.0, 3.0), (14.0, 0.0, 6.0), 26, d=9.0), "C"),
    ("C10d", b_field, s("10-08"), C((-0.2, 3.7, 0.4), (-1.0, 4.6, 0.24), 32), "C"),   # （v1 の確認役 3 回目）画面の 1/6 で小さかった → 寄る
    # 8 秒をこえる同じ絵を、文の切れ目で替える（下書きの最初の点検。決まり：同じ絵を 8 秒以上続けない）
    ("A02a", b_drive, s("02-02"), CC((0.62, -0.22, 1.16), (0.95, 0.02, 1.02), 38), "A"),
    ("A04d2", b_drive, s("04-05"), CC((0.6, 0.25, 1.15), (0.95, 0.0, 1.02), 36, (0.66, 0.18, 1.13), (0.95, 0.0, 1.02), d=4.0), "A"),
    ("A04d3", b_drive, s("04-06"), CC((0.55, -0.2, 1.12), (0.95, 0.03, 1.0), 40), "A"),
    ("T06b", b_town, s("06-03"), C((-200.0, -330.0, 160.0), (0.0, 0.0, 0.0), 26), "T"),
    ("B07b2", b_bridge, s("07-03"), C((SENSOR_X - 2.0, LANE_Y - 2.2, 5.0), (SENSOR_X, LANE_Y, 6.4), 34), "B"),
    ("B08a", b_bridge, s("08-02"), C((SENSOR_X + 8.0, LANE_Y - 3.2, 4.6), (SENSOR_X, LANE_Y + 0.3, 3.7), 24), "B"),
    ("B08c", b_bridge, s("08-03"), C((SENSOR_X + 10.5, LANE_Y - 3.8, 4.6), (SENSOR_X, LANE_Y + 0.2, 3.3), 24), "B"),   # 感知器が画面の上の外にあり、はね返る「ピコン」と線の「ぽん」が鳴らなかった → 感知器から車の屋根・道まで 1 枚に
    ("B08d", b_bridge, s("08-04"), C((SENSOR_X + 11.0, LANE_Y - 4.0, 4.4), (SENSOR_X - 1.0, LANE_Y, 3.4), 24), "B"),   # （v1 の確認役 2 回目）車が映らず粒がひとりでに増えた → 下の車と粒を 1 枚に
    ("T09b", b_town, s("09-03"), C((180.0, -120.0, 200.0), (20.0, 120.0, 10.0), 26), "T"),
    ("T10b", b_town, s("10-05"), C((560.0, -300.0, 330.0), (258.0, 18.0, 0.0), 22), "T"),   # v1 点検：橋の輪が字幕の帯に重なった → 少し引いて下へ向ける（橋 y=466・トンネル y=173）
]
END_T = e("16-04") + 2.0
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
                p_ = m_.plan(END_T)
                for tq in [float(x) for x in os.environ.get("MARU_PROBE", "").split(",") if x]:
                    k_ = p_.kin(tq); print("PROBE %.2f roll=%.1f pitch=%.1f twist=%.1f iris=%s" % (tq, k_["roll"], k_["pitch"], k_["twist"], k_["iris"]))
            print("MARU_LATE", json.dumps(MARU_LATE, ensure_ascii=False)); sys.exit(0)
        bake_maru(t0, t1)
        for tq in [float(x) for x in os.environ.get("MARU_PROBE_BAKE", "").split(",") if x]:   # 点検用：焼いたあとの胴の向き（世界）
            bpy.context.scene.frame_set(f(tq))
            for o_ in bpy.data.objects:
                if o_.name.endswith("• torso") or o_.name.startswith(("Antenna light", "Maru body", "Lens maru")): print("BAKE %.2f %s %s %s" % (tq, o_.name, tuple(round(math.degrees(v), 1) for v in o_.matrix_world.to_euler()), tuple(round(v, 3) for v in o_.matrix_world.translation)))
        if cm is not None: cm(t0)
        for tq in [float(x) for x in os.environ.get("CAM_PROBE", "").split(",") if x]:   # 点検用：その時刻のカメラと、おじさんの車・点の場所
            bpy.context.scene.frame_set(f(tq)); cmo = bpy.context.scene.camera
            print("CAMPROBE %.2f cam=%s" % (tq, tuple(round(v, 2) for v in cmo.matrix_world.translation)), " ".join("%s=%s" % (k_, tuple(round(v, 2) for v in TRACK[k_][0].matrix_world.translation)) for k_ in ("owncar", "ownpt") if k_ in TRACK))
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
