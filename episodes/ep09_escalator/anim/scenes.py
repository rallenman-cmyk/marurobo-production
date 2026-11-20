# 9本目（エスカレーター）：3D の場面を声の時刻に合わせて動かして描く（7本目の scenes.py と同じ作り方）
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 8] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   PC の本番：... -- <クリップ> <出力> --samples 24 --res 1920 1080 --frames 0 99 --gpu --video --fast
#   舞台：A＝昼の駅（b_day）／B＝夜の駅と床の下（b_night）／C＝作業場（b_bench）／D＝断面（b_cut）／I＝想像の場面（b_imag。組み立てで青っぽくする）
#   舞台の組み立て（b_*）は、その舞台の動きを全部作り、カメラだけをクリップごとに選ぶ。絵コンテ表：../絵コンテ_v1.md
#   決まり：3D の中に字を書かない／まるロボは喋らない・本物の体を marumotion の予定で動かす（maru9.py）／動きは言い終えてから／
#     段・鎖・歯車・手すりは esc_geom の計算どおりに動く（kit9.Esc）。カメラが切りかわる所でだけ、輪を先へ進めてよい（SpeedS の skips）
import os, sys, math, json
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(KIT_HERE, "kit9.py"), encoding="utf-8").read())
MAT = M                            # 材質の一覧（場面の中では M はまるロボ）
_K7 = KIT_HERE
exec(open(os.path.join(KIT_HERE, "..", "..", "ep06_haizen", "anim", "core.py"), encoding="utf-8").read().replace(
    'VO = os.path.join(KIT_HERE, "..", "voice")', 'VO = os.path.join(_K7, "..", "voice")'))
CLIPNAME, OUTDIR = _argv[0], _argv[1]
_SRC_DEFAULT = {"step": "maru_c", "jump": "maru_c", "land": "maru_c", "takeoff": "maru_c", "step_turn": "maru_c"}


def ev(t, kind, gain=1.0, src=None):
    EVENTS.append((round(t, 3), kind, gain, src if src is not None else _SRC_DEFAULT.get(kind, "")))


def _opt(name, n=1, default=None):
    if name in _argv:
        i = _argv.index(name); v = _argv[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default


SAMPLES = int(_opt("--samples", 1, 8)); RES = tuple(int(x) for x in _opt("--res", 2, ("480", "270"))); STEP = int(_opt("--step", 1, 3))
STILLS = [float(x) for x in _opt("--stills", 1, "").split(",") if x]
TRACK_ONLY = "--track" in _argv
_M_ = [None]
exec(open(os.path.join(_K7, "maru9.py"), encoding="utf-8").read())


def cam(loc, target, lens=35, t0=None, t1=None, loc1=None, target1=None, lens1=None):
    c, tg = cam_rig(loc, target, lens)
    c.data.dof.use_dof = False; c.data.dof.aperture_fstop = 64.0     # 9本目：ぼかさない（render_settings が入れるぼかしを止める）
    if t0 is not None:
        cam_move(c, tg, t0, t1, loc, loc1 or loc, target, target1 or target, lens, lens1 or lens)
    return c, tg


def F(off, lens=40, dz=0.35, t0=None, t1=None, off1=None):
    """まるロボを追うカメラ（足もとの root を追う）。off＝まるロボからのずれ（世界の向き）"""
    c = cam_follow(_M_[0].root, off, dz, lens); c.data.dof.aperture_fstop = 64.0
    if t0 is not None: key(c, "location", t0, off); key(c, "location", t1, off1)
    return c


def C(loc, tgt, lens=35, loc1=None, tgt1=None, lens1=None, d=8.0):
    def mk(t0):
        return cam(loc, tgt, lens, t0, t0 + d, loc1 or loc, tgt1 or tgt, lens1 or lens)
    return mk


XLC = G.COMB_LO_X - 0.18          # 下のくしの線
XHC = G.COMB_HI_X - 0.18          # 上のくしの線
CP = 0.038                        # くしの板の上の面の高さ（床から。くしの線から 0.55 まで）
HY = CLAD_Y + 0.01
UP = G.H                           # 上の床の高さ
ESC = [None]


def glow_obj(ob, t0, t1, col="#FFFFFF", strength=4.0):
    """物を光らせる（材質を光る材質に差しかえて、強さにキーを打つ）"""
    m = mat("glow_" + ob.name, col, rough=0.4, emit=0.001)
    for c in [ob] + list(ob.children_recursive):
        if c.type == 'MESH':
            c.data.materials.clear(); c.data.materials.append(m)
    emit_key(m, t0 - 0.3, 0.0); emit_key(m, t0, strength); emit_key(m, t1, strength); emit_key(m, t1 + 0.3, 0.0)
    return m


def ring_at(loc, r, t0, t1, col="#FFFFFF", rot=(0, 0, 0)):
    """白い輪（見る所を示す）。3D の中の印（字ではない）"""
    bpy.ops.mesh.primitive_torus_add(location=loc, rotation=rot, major_radius=r, minor_radius=r * 0.06)
    o = bpy.context.object; o.data.materials.append(mat("ring" + col, col, rough=0.3, emit=3.0))
    hide_key(o, -100.0, True); hide_key(o, t0, False); hide_key(o, t1, True)
    return o


def button(loc):
    """非常停止ボタン（字は書かない）：灰色の台に、赤い丸いボタン"""
    b = cube(mat("btn_base", "#D8DADC", rough=0.5), loc, (0.12, 0.05, 0.16), bevel=0.01)
    p = cyl(mat("btn_red", "#D8322A", rough=0.35), (loc[0], loc[1] - 0.035, loc[2]), 0.035, 0.03, rot=(R(90), 0, 0), verts=32)
    return b, p


# ======================================================================== A：昼の駅（冒頭・1章・4章・5章・38・39-06・オチ）
def _day_speed():
    """昼のエスカレーター：分速 18m（0.3 m/秒）。1章でカメラが切りかわる所で、シールの段を先へ進める（下で計算）"""
    return SpeedS([(-100.0, 0.3), (2000.0, 0.3)])


def b_day(cl):
    station(night=False)
    sp = _day_speed()
    E = Esc(sp, hr_speed=SpeedS([(-100.0, 0.3), (s("22-01"), 0.3), (s("22-01") + 1.0, 0.34), (e("22-04") + 1.0, 0.34), (e("22-04") + 2.0, 0.3), (2000.0, 0.3)]))
    ESC[0] = E
    track("comb_hi", E.combs["hi"], 0.05); track("comb_lo", E.combs["lo"], 0.05)
    # お客さん（後ろ姿。段に乗って上り、上で歩いて去る）。お客さんは喋らない
    for k, (sh, y) in zip((3, 14, 27, 41, 52), (("#3E7CB1", 0.2), ("#B5502F", -0.18), ("#4F7A55", 0.15), ("#7B5EA7", -0.2), ("#C9A227", 0.2))):
        wk = walker((0, 0, 0), 90.0, shirt=sh); E.add_rider(wk, k, y)
    E.rider_hide = [(s("25-01") - 0.5, e("27-05") + 1.0)]
    for nm, (x_, z_) in (("loop_lo", E.gear_c["lo"]), ("loop_hi", E.gear_c["hi"])):
        track(nm, empty((x_, 0.0, z_)), 0.0)
    track("loop_mid", empty(((E.gear_c["lo"][0] + E.gear_c["hi"][0]) / 2, 0.0, (E.gear_c["lo"][1] + E.gear_c["hi"][1]) / 2 - 0.9)), 0.0)
    bt = button((XLC - 0.75, -(Y_HR + 0.06), 0.62))
    M = MaruR((-1.9, -0.15, 0.0), face=60.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    # ---------------------------------------------------------------- 冒頭：乗る → 運ばれる → 上で降りる → 消える段を見る → 乗り直して、くしにはじかれる
    M.walk(s("01-01") + 0.4, e("01-01"), (XLC - 0.75, -0.15, 0.0))
    M.wobble(w("01-02", "腕") - 0.3, e("01-02"), 10, 0.5)
    M.at(w("01-03", "乗って"), look=22); M.at(e("01-03") + 0.2, look=0)
    M.at(s("01-04"), face=90.0)
    t_on = w("01-04", "乗り口") + 0.35
    k1 = E.find_step(t_on, 0.75)
    M.jump(t_on, E.tread(k1, t_on))
    # 運ばれる（上の降り口で降りる少し前まで）
    t_off_land = s("03-02") + 0.4
    x_off = (XHC + 0.75, -0.15, UP)
    M.carry(t_on + 0.05, t_off_land - 0.85, E.carry_fn(k1, t_on + 0.05))
    M.at(w("02-04", "きょろきょろ") - 0.3, look=-18); M.act(w("02-04", "きょろきょろ"), "look_around"); M.at(e("02-04") + 0.3, look=0)
    M.jump(t_off_land, x_off)
    M.at(t_off_land + 2.4, face=-90.0)                  # ふり返って、すき間を見る
    M.at(s("03-03"), look=-20); M.at(e("03-04"), look=0)
    # 04-01：段に乗ったまま入ってみる → 段へ跳び戻る（流れに逆らって）→ くしへ向く
    t_ret = s("04-01") + 5.2
    k2 = E.find_step(t_ret, XHC - 0.15 - 0.3 * (w("04-03", "ころん") - 0.15 - t_ret) + 0.18)
    M.walk(s("04-01") + 0.6, s("04-01") + 2.8, (XHC + 0.45, -0.15, UP + CP))
    M.jump(t_ret, E.tread(k2, t_ret))
    t_sc = w("04-03", "ころん") - 0.15                  # くしに乗り上げる
    M.carry(t_ret + 0.05, t_sc, E.carry_fn(k2, t_ret + 0.05))
    M.at(t_ret + 1.6, face=90.0)
    M.surprise(e("04-02") - 1.3)
    p_sc = E.tread(k2, t_sc)
    M.carry(t_sc, t_sc + 0.6, lambda t, t0=t_sc: (0.55 * min(1, (t - t0) / 0.6), 0.0, 0.05 * math.sin(math.pi * min(1, (t - t0) / 0.6))))
    M.act(t_sc + 0.05, "roll_over", side=-1)
    ev(t_sc, "clank", 0.25, "comb_hi")
    M.act(s("04-05") + 0.3, "get_up")
    M.at(s("04-06") - 0.2, face=-80.0)
    M.confused(w("04-06", "首") - 0.6)
    M.nod(w("05-04", "確かめて"))
    # ---------------------------------------------------------------- 1章：下へ移ってしるしを貼る → シールの段と一緒に上る → 上で降りる
    M.at(s("07-01") - 0.05, loc=(XLC - 0.55, -0.32, CP), face=60.0, interp="CONSTANT")    # 06-06 の引きのあと、下の乗り口の場面で置き直す
    t_p = w("07-03", "ぺたっ")
    k3 = E.find_step(t_p, 0.42)
    stk = E.sticker(k3, t_p); track("sticker", stk, 0.02)
    M.at(t_p - 1.2, face=90.0)
    M.push(t_p - 0.25, 0.35)
    ev(t_p, "pop_ui", 0.35, "sticker")
    t_on2 = w("07-04", "上へ") + 0.2
    M.jump(t_on2, E.tread(k3 - 1, t_on2))
    # 07-05 の切りかわりで、シールの段を上のくしの下まで進める（見えない所で時間を縮める）。まるロボはその次の段に乗ったまま
    t_cut1 = s("07-05") - 0.05; t_gone = w("07-05", "消えました") - 0.1
    s_now = (sp.pos(t_gone) + k3 * G.PITCH) % G.LOOP
    target = G.LTOP - 0.35 - 0.12                   # 前の車輪が、上のくしの下に入った所
    sp.skips.append((t_cut1, (target - s_now) % G.LOOP))
    t_off2 = t_gone + 1.0
    M.carry(t_on2 + 0.05, t_off2 - 0.85, E.carry_fn(k3 - 1, t_on2 + 0.05))
    M.jump(t_off2, (8.35, 1.25, UP), apex=0.3)          # 横の階段の側（上の床）へ跳び降りる
    # 08-01：横の階段へ歩き、何段か跳ねて下りる → 切りかわりで下の乗り口へ（置き直す）
    M.walk(t_off2 + 1.2, t_off2 + 2.8, (7.9, 1.85, UP))
    stair = [(7.6 - 0.3 * (i + 0.5), 2.6, UP - G.H / 18 * (i + 1)) for i in range(4)]
    M.path(stair, [t_off2 + 3.8 + 0.42 * i for i in range(4)], silent=False)
    t_cut2 = s("08-02") - 0.05
    M.at(t_cut2, loc=(XLC - 0.6, -0.2, 0.03), face=80.0, interp="CONSTANT")
    M.wobble(s("08-02") + 0.3, e("08-02") + 0.4, 7, 0.55)
    t_out = w("08-03", "出てきました")
    s_now2 = (sp.pos(t_out) + k3 * G.PITCH) % G.LOOP
    sp.skips.append((t_cut2, (0.62 - s_now2) % G.LOOP))     # シールが、下のくしから出たところ
    M.surprise(t_out + 0.1); M.hops(t_out + 2.0, n=2)
    M.confused(w("08-07", "なぜ") - 0.5)
    # ---------------------------------------------------------------- 4章：手すりに頭をのせて上る（頭が前へずれる）
    t4 = s("21-01") - 0.05
    M.at(t4, loc=(XLC - 0.7, -0.2, 0.0), face=90.0, interp="CONSTANT")
    t_on4 = s("22-01") + 0.9
    k4 = E.find_step(t_on4, 0.6)
    M.jump(t_on4, E.tread(k4, t_on4, ly=-0.22))
    M.carry(t_on4 + 0.05, e("24-08") + 2.0, E.carry_fn(k4, t_on4 + 0.05))
    M.tilt(w("22-01", "頭で"), 16)                       # 手前（−y）の手すりへ頭を寄せる
    for t0, t1 in ((s("22-02") + 0.2, e("22-02") + 0.3), (s("22-03") + 0.6, e("22-03") + 0.3), (s("22-04") + 0.6, e("22-04"))):
        M.lean(t0, t1, 14)
    M.confused(e("22-04") - 0.4)
    # 5章（25-02）：上の降り口の床で首をかしげる
    M.at(s("25-02") - 0.05, loc=(XHC + 0.8, -0.15, UP), face=-90.0, interp="CONSTANT")
    M.confused(s("25-02") + 0.6)
    M.at(s("26-05") - 0.3, face=-90.0); M.confused(s("26-05") + 0.4)
    # 38：昼の駅。ボタンから離れて立ち、こちらを向く
    M.at(s("38-01") - 0.05, loc=(XLC - 1.4, -0.9, 0.0), face=0.0, interp="CONSTANT")
    M.at(s("38-01") + 1.0, look=5); M.nod(w("38-02", "困った"))
    # ---------------------------------------------------------------- オチ：坂の上の方で乗っている → くしの手前で跳ぶ → よろけて、おじさんの手の中へ
    oj = ojisan((XHC + 1.35, -0.2, UP), face=-90.0); track("ojisan", oj.root, 1.2)
    for ob in [oj.root] + list(oj.root.children_recursive): hide_key(ob, -100.0, True); hide_key(ob, s("40-01") - 0.1, False)
    t_o = s("40-01") - 0.05
    k5 = E.find_step(t_o, 6.9)
    M.at(t_o, loc=E.tread(k5, t_o, ly=-0.1), face=90.0, interp="CONSTANT")
    t_j = w("40-02", "ぴょん") + 0.35
    M.carry(t_o + 0.02, t_j - 0.8, E.carry_fn(k5, t_o + 0.02, lx=-0.18))
    M.jump(t_j, (XHC + 0.55, -0.15, UP + CP), apex=0.35)
    M.hops(t_j + 0.9, n=1, height=0.08)
    # 40-04：着地でよろけて、おじさんの手の中へ（おじさんが腕を下ろして受け止める）
    t_c = w("40-04", "手の中")
    M.wobble(s("40-04") + 0.2, t_c - 0.2, 12, 0.4)
    M.hopto(t_c, (XHC + 0.95, -0.18, UP))
    for a_ in oj.arms:
        key(a_, ("rotation_euler", 0), -100.0, 0.0); key(a_, ("rotation_euler", 0), t_c - 0.9, 0.0); key(a_, ("rotation_euler", 0), t_c - 0.1, R(-38))
    ev(t_c + 0.05, "land", 0.2, "maru_c")
    M.blink(s("40-05") + 0.4); M.blink(s("40-05") + 0.9)
    # 26-10〜12：くしの歯に小石がはさまる → 歯の先が折れて、小石が外れる
    ch = E.combs["hi"]
    tip = cube(MAT["yellow"], (ch.location.x - 0.06, 0.1, UP - 0.012), (0.04, 0.008, 0.012)); track("tooth", tip, 0.0)
    peb = sphere(mat("pebble", "#7D7A74", rough=0.8), (ch.location.x - 0.08, 0.1, UP + 0.012), 0.022, scale=(1.2, 1, 0.8)); track("pebble", peb, 0.0)
    hide_key(peb, -100.0, True); hide_key(peb, s("26-10"), False); hide_key(peb, s("27-01"), True)
    t_br = w("26-12", "折れて")
    for ob, d in ((tip, (-0.05, 0.0, -0.06)), (peb, (-0.12, 0.0, -0.01))):
        x0, y0, z0 = ob.location
        key(ob, "location", -100.0, (x0, y0, z0)); key(ob, "location", t_br, (x0, y0, z0)); key(ob, "location", t_br + 0.5, (x0 + d[0], y0 + d[1], z0 + d[2]))
    key(tip, ("rotation_euler", 1), t_br, 0.0); key(tip, ("rotation_euler", 1), t_br + 0.5, R(70))
    hide_key(tip, -100.0, True); hide_key(tip, s("26-10"), False); hide_key(tip, s("27-01"), True)
    ev(t_br, "snap", 0.35, "tooth")
    # 27：段に乗った人の靴（すき間の手前で止まる）
    t27 = s("27-01") - 0.1
    ks = E.find_step(t27, 2.6)
    shoe = cube(mat("shoe", "#2A2522", rough=0.5), (-0.16, -(YW - 0.07), G.TREAD_DZ + 0.035), (0.26, 0.1, 0.07), bevel=0.02, parent=E.steps[ks])
    track("shoe", shoe, 0.0)
    hide_key(shoe, -100.0, True); hide_key(shoe, t27, False); hide_key(shoe, e("27-05") + 1.0, True)
    key(shoe, ("location", 1), -100.0, -(YW - 0.12)); key(shoe, ("location", 1), w("27-02", "つま先"), -(YW - 0.12)); key(shoe, ("location", 1), w("27-02", "つま先") + 1.0, -(YW - 0.07))
    # 絵コンテの音の欄（2026-11-20 の点検で足した）。エスカレーター全体・場面全体の音なので、映る物の条件は付けない
    ev(s("01-02") + 0.6, "whoosh", 0.12, "")                                       # 01-02：体を左右にふる「くるっ」
    ev(s("03-02") + 1.5, "katan", 0.15, "")                                        # 03-02：段がくしの下へ（小）
    ev(w("03-03", "1枚") + 0.1, "katan", 0.2, ""); ev(w("03-03", "また") + 0.45, "katan", 0.2, "")   # 03-03：1枚、また1枚
    ev(s("06-01") + 1.0, "katan", 0.15, "")                                        # 06-01：降り口（小）
    ev(w("07-05", "消えました") - 0.25, "katan", 0.2, "")                         # 07-05：シールの段が消える
    ev(s("25-01") + 1.05, "clank", 0.2, ""); ev(s("25-01") + 1.4, "land", 0.3, "")   # 25-01：04-03 の絵をもう一度（くしに乗り上げて、ころん）
    return dict(E=E, M=M, k3=k3, k2=k2, oj=oj, bt=bt)


def _day(cl):
    b_day(cl)


# ======================================================================== B：夜の駅・床の下（2章・6章）
def _night_speed():
    """夜の点検：止まっている → 09-05 でゆっくり動き出す（0.25 m/秒）。6章：見張りで止まる → おじさんが動かし直す。ボタンの試しは分速 30m"""
    k = [(-100.0, 0.0), (w("09-05", "動かして") + 0.2, 0.0), (w("09-05", "動かして") + 1.4, 0.25)]
    stops = [(w("29-03", "止まりました") - 0.9, s("30-01") + 0.4), (w("30-03", "止まりました") - 0.9, s("31-01") + 0.4),
             (w("31-03", "止まりました") - 0.9, s("32-01") + 0.4)]
    t_hr = w("32-02", "押さえると") + 0.5                    # 手すりが止まる
    t_all = w("32-03", "全体が") - 0.6                       # 段も止まる
    stops.append((t_all, s("34-01") + 0.6))
    for a, b in stops:
        k += [(a, 0.25), (a + 0.7, 0.0), (b, 0.0), (b + 1.0, 0.25)]
    k[-1] = (k[-1][0], 0.5)                                   # 34-01 から：分速 30m（ボタンの試し）
    t_btn = w("34-03", "えいっ") + 0.25
    k += [(t_btn, 0.5), (t_btn + 1.2, 0.0)]                  # すうっと（約 0.3m）止まる
    k += [(e("36-06") + 1.0, 0.0)]
    return SpeedS(sorted(k)), t_hr, t_all, t_btn


def b_night(cl):
    station(night=True); pit()
    sp, t_hr, t_all, t_btn = _night_speed()
    hk = [(t, v) for t, v in sp.keys]
    hk = [(t, v) for t, v in hk if not (t_hr - 0.01 <= t <= t_all + 1.5)] + [(t_hr - 0.3, 0.25), (t_hr + 0.2, 0.0)]
    E = Esc(sp, hr_speed=SpeedS(sorted(hk)))
    ESC[0] = E
    track("comb_hi", E.combs["hi"], 0.05); track("comb_lo", E.combs["lo"], 0.05); track("gear", E.gears["hi"], 0.0)
    track("inlet", E.inlets["lo"], 0.05)
    lid = bpy.data.objects[[o.name for o in bpy.data.objects if o.type == 'MESH' and abs(o.location.x - (LID_HI[0] + LID_HI[1]) / 2) < 0.01 and abs(o.location.z - (UP - 0.012)) < 0.01][0]]
    oj = ojisan((LID_HI[1] + 0.35, -1.1, UP), face=-70.0); track("ojisan", oj.root, 1.2)
    bt = button((XLC - 0.75, -(Y_HR + 0.06), 0.62)); track("button", bt[1], 0.0)
    M = MaruR((LID_HI[0] - 0.2, -0.25, UP), face=-20.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    def glow_mat(m_, t0, t1, st=2.5):
        b_ = m_.node_tree.nodes["Principled BSDF"]; b_.inputs["Emission Color"].default_value = b_.inputs["Base Color"].default_value
        emit_key(m_, -100.0, 0.0); emit_key(m_, t0 - 0.3, 0.0); emit_key(m_, t0, st); emit_key(m_, t1, st); emit_key(m_, t1 + 0.3, 0.0)
    glow_mat(MAT["chain"], w("11-02", "鎖"), e("11-03"))
    glow_mat(MAT["gear"], w("11-06", "歯車"), w("11-06", "鎖") + 0.2)
    glow_mat(MAT["chain"], w("11-06", "鎖"), e("11-06") + 0.3)
    glow_mat(MAT["tread"], w("11-07", "段"), e("11-07") + 0.3, 1.5)
    glow_mat(MAT["motor"], w("11-08", "モーター"), e("11-08") + 0.4)
    for nm_, wd in (("motor", "モーター"), ("gear", "歯車"), ("chain", "鎖")):
        glow_mat(MAT[nm_], w("11-09", wd), w("11-09", wd) + 1.0)
    glow_mat(MAT["chain"], s("11-10"), w("11-10", "段") + 0.6); glow_mat(MAT["tread"], w("11-10", "段"), e("11-10"), 1.5)
    track("motor", E.motor, 0.0)
    ch_pt = empty((G.X_HI_END - 0.6, -Y_CHAIN, G.H - 0.25)); track("chain_pt", ch_pt, 0.0)
    # ---------------------------------------------------------------- 2章：ふたを外す → 機械の部屋へ跳び降りる → 見上げる → 鎖をたどる → 戻る段に乗る
    M.at(w("09-02", "おじさん"), look=25, face=60.0); M.at(e("09-02"), look=0)
    t_lid = w("09-03", "外す") 
    key(lid, "location", -100.0, tuple(lid.location)); key(lid, "location", t_lid, tuple(lid.location))
    key(lid, "location", t_lid + 0.4, (lid.location.x, lid.location.y, UP + 0.18))   # 持ち上げて
    key(lid, "location", t_lid + 1.2, (lid.location.x, -HY - 0.75, UP + 0.02))   # 横へ置く
    for a_ in oj.arms:                                       # おじさんが腕を下ろして、ふたを持つ
        key(a_, ("rotation_euler", 0), -100.0, 0.0); key(a_, ("rotation_euler", 0), t_lid - 0.5, 0.0); key(a_, ("rotation_euler", 0), t_lid, R(-38))
        key(a_, ("rotation_euler", 0), t_lid + 1.2, R(-38)); key(a_, ("rotation_euler", 0), t_lid + 1.8, 0.0)
    ev(t_lid + 0.1, "clank", 0.3, "ojisan")
    M.peer(s("09-04") + 0.2, 1.6)
    t_go = w("09-05", "動かして")                          # 09-05：おじさんがうなずいて、段を動かす合図
    # 動き出す音（エスカレーター全体の音なので、映っている物に関係なく鳴らす）：09-05 と、見張りで止まったあとおじさんが動かし直す所
    ev(t_go + 0.05, "click", 0.3, ""); ev(t_go + 0.25, "start", 0.35, "")
    for t_rs in (s("30-01") + 0.4, s("31-01") + 0.4, s("32-01") + 0.4, s("34-01") + 0.6):
        ev(t_rs, "start", 0.35, "")
    key(oj.head, ("rotation_euler", 0), -100.0, 0.0); key(oj.head, ("rotation_euler", 0), t_go - 0.5, 0.0)
    key(oj.head, ("rotation_euler", 0), t_go - 0.2, R(14)); key(oj.head, ("rotation_euler", 0), t_go + 0.2, 0.0)
    x_room = (LID_HI[0] + LID_HI[1]) / 2 - 0.05
    t_dn = s("10-01") + 0.15                               # 10-01 の絵（機械の部屋の中）で、跳び降りてくる所を見せる
    M.jump(t_dn, (x_room, -0.2, Z_PIT_HI))
    M.at(s("10-01") + 2.6, face=-90.0)                     # 左（くしの方）を向く
    M.at(s("10-01") + 1.3, look=38); M.at(e("10-04"), look=10)
    M.at(s("11-04"), look=0)
    M.walk(w("11-04", "たどって"), e("11-04") + 0.8, (G.X_HI_END + G.RG + 0.55, -0.2, Z_PIT_HI))
    M.act(w("11-05", "歯車") + 0.2, "awe", dur=2.4, pitch=24)
    M.at(s("12-04"), look=-5)
    M.glow(s("12-05"), 1.8, 0.4)
    # 12-06：さかさまの段の裏に跳び乗る（戻る側の平らな所）
    t_b = w("12-06", "ちょこん")
    kb = None
    for k in range(G.N_STEPS):
        x, z, r = E.step_at(k, t_b)
        if abs(r - 180) < 0.5 and G.X_HI_END - 0.75 < x < G.X_HI_END - 0.35: kb = k
    kb = kb if kb is not None else 0
    M.jump(t_b, E.back(kb, t_b), apex=0.25)
    M.carry(t_b + 0.05, s("13-01") + 0.2, E.carry_fn(kb, t_b + 0.05, back=True))
    # 13-01 の切りかわりで、段を下の端まで進める（見えない所）。まるロボは下の機械の部屋に置き直す（13-01〜03 はまるロボを映さない）
    t_c13 = s("13-01") - 0.05
    s_kb = (sp.pos(t_c13) + kb * G.PITCH) % G.LOOP
    want = G.LTOP + math.pi * G.RG + G.LTOP - 2.2               # 戻る側の下の端の少し手前
    sp.skips.append((t_c13, (want - s_kb) % G.LOOP))
    M.at(s("13-01") + 0.3, loc=(XL_PIT + 0.55, -0.2, Z_PIT_LO), face=90.0, interp="CONSTANT")
    ev(w("13-03", "すき間") + 0.1, "clank", 0.12, "comb_lo")     # 13-03：段がすき間から出る小さな「カタン」
    lid_lo = bpy.data.objects[[o.name for o in bpy.data.objects if o.type == 'MESH' and abs(o.location.x - (LID_LO[0] + LID_LO[1]) / 2) < 0.01 and abs(o.location.z - (-0.012)) < 0.01][0]]
    key(lid_lo, "location", -100.0, tuple(lid_lo.location)); key(lid_lo, "location", s("13-01"), (lid_lo.location.x, -HY - 0.75, 0.02))
    # 13-01 の切りかわり（地下を映している間）に、おじさんを下のふたの横へ移す（13-04：開けて待っている）
    key(oj.root, "location", -100.0, tuple(oj.root.location), "CONSTANT"); key(oj.root, ("rotation_euler", 2), -100.0, oj.root.rotation_euler.z, "CONSTANT")
    key(oj.root, "location", s("13-01"), (LID_LO[0] - 0.3, 0.5, 0.0), "CONSTANT"); key(oj.root, ("rotation_euler", 2), s("13-01"), R(-20), "CONSTANT")
    M.jump(w("13-04", "外へ") + 0.3, (LID_LO[0] - 0.55, -0.25, 0.0), apex=0.45)
    M.confused(s("13-05") + 0.2)
    # ---------------------------------------------------------------- 6章：見張りに挑戦（夜。ゆっくり動いている）
    t6 = s("28-01") - 0.05
    M.at(t6, loc=(XLC - 1.2, -0.75, 0.0), face=60.0, interp="CONSTANT")
    key(oj.root, "location", t6 - 0.06, (LID_LO[0] - 0.3, 0.5, 0.0), "CONSTANT")
    key(oj.root, "location", t6, (XLC - 2.6, -0.2, 0.0), "CONSTANT"); key(oj.root, ("rotation_euler", 2), t6, R(60), "CONSTANT")
    M.glow(s("28-02") + 0.2, 1.5, 0.3); M.hops(s("28-02") + 0.6, n=2, height=0.06)
    # ① 手すりの入口：ボールを転がす
    # 入口は手すりが台へ入る所（高さ 0.51）。まるロボが頭の上のボールを、体を前へ傾けて押し出し、入口へ転がし入れる
    xin = E.inlets["lo"].location.x; zin = E.inlets["lo"].location.z
    mx = xin - 0.8
    ball = sphere(mat("ball", "#F2A33A", rough=0.4), (mx, -(Y_HR), 0.96), 0.08)   # 頭の上（高さ約 0.88）に乗せる。0.87 では頭に埋まって見えなかった
    track("ball", ball, 0.0)
    hide_key(ball, -100.0, True); hide_key(ball, s("29-02") - 0.03, False); hide_key(ball, s("30-01") - 0.05, True)
    t_p = w("29-02", "転がして") - 0.2
    key(ball, "location", -100.0, (mx, -(Y_HR), 0.96)); key(ball, "location", t_p + 0.05, (mx, -(Y_HR), 0.96))
    key(ball, "location", t_p + 0.3, (mx + 0.30, -(Y_HR), 0.88))
    key(ball, "location", t_p + 0.75, (xin - 0.13, -(Y_HR), zin + 0.03))
    key(ball, "location", w("29-02", "入りこみ") + 0.4, (xin - 0.13, -(Y_HR), zin + 0.03))
    key(ball, "location", w("29-02", "入りこみ") + 1.2, (xin - 0.09, -(Y_HR), zin + 0.03))
    ev(t_p + 0.3, "roll", 0.3, "ball")
    M.walk(s("28-04") + 0.4, s("29-01") + 1.0, (mx, -(Y_HR), 0.0)); M.at(s("29-01") + 3.5, face=90.0)
    M.push(t_p, 0.35)
    ev(w("29-03", "止まりました") - 0.2, "stop", 0.4, "")
    M.sigh(s("29-05") + 0.2)
    # ② 段の横：リボン
    t_rb = w("30-02", "はさんで") + 0.1
    kr = E.find_step(t_rb, XLC + 0.35)
    rib = cube(mat("ribbon", "#E0457B", rough=0.5), (-0.12, -(YW - 0.015), G.TREAD_DZ + 0.035), (0.30, 0.03, 0.05), parent=E.steps[kr])   # 段の横のすき間から立って見える大きさ（0.012 では見えなかった）
    track("ribbon", rib, 0.0)
    hide_key(rib, -100.0, True); hide_key(rib, t_rb, False); hide_key(rib, s("31-01") - 0.1, True)
    M.at(s("30-01") - 0.05, loc=(XLC - 0.42, -0.3, CP), face=90.0, interp="CONSTANT")
    M.push(w("30-02", "はさんで"), 0.3)
    ev(w("30-03", "止まりました") - 0.2, "stop", 0.4, "")
    # ③ くし：小石
    peb = sphere(mat("pebble", "#7D7A74", rough=0.8), (XLC + 0.05, 0.0, 0.02), 0.03, scale=(1.2, 1, 0.8)); track("pebble", peb, 0.0)
    hide_key(peb, -100.0, True); hide_key(peb, w("31-02", "小石"), False); hide_key(peb, s("32-01"), True)
    M.at(s("31-01") - 0.05, loc=(XLC - 0.45, 0.2, CP), face=90.0, interp="CONSTANT")
    M.push(w("31-02", "はさんで"), 0.3)
    ck = E.combs["lo"]
    key(ck, ("location", 0), -100.0, ck.location.x); key(ck, ("location", 0), w("31-03", "押されると"), ck.location.x)
    key(ck, ("location", 0), w("31-03", "押されると") + 0.3, ck.location.x - 0.012); key(ck, ("location", 0), s("32-01"), ck.location.x)
    ev(w("31-03", "止まりました") - 0.2, "stop", 0.4, "")
    # ④ 手すりを頭で押さえる（下の乗り口の近く）
    M.at(s("32-01") - 0.05, loc=(XLC - 0.65, -(Y_HR - 0.42), 0.0), face=90.0, interp="CONSTANT")
    M.tilt(w("32-02", "押さえる") - 0.3, 18); M.push(w("32-02", "押さえる"), 0.6); M.tilt(e("32-03") + 0.2, 0)
    ev(t_all + 0.2, "stop", 0.4, "")
    M.sigh(s("33-02") + 0.1)
    for a_ in oj.arms: key(a_, ("rotation_euler", 0), -100.0, 0.0)
    key(oj.head, ("rotation_euler", 0), -100.0, 0.0); key(oj.head, ("rotation_euler", 0), s("33-03") + 0.3, 0.0)
    key(oj.head, ("rotation_euler", 0), s("33-03") + 0.6, R(14)); key(oj.head, ("rotation_euler", 0), s("33-03") + 1.0, 0.0)
    key(oj.head, ("rotation_euler", 0), s("34-01") + 0.3, 0.0); key(oj.head, ("rotation_euler", 0), s("34-01") + 0.6, R(14)); key(oj.head, ("rotation_euler", 0), s("34-01") + 1.0, 0.0)
    # 非常停止ボタン：まるロボが体で押す
    bx = bt[1].location
    # 34-02 の間はボタンの横で待つ（前に立つとボタンが体に隠れた）。「えいっ」の前に横へ 1 歩寄る
    M.walk(s("33-03") + 1.0, s("34-02") + 1.0, (bx.x - 0.55, bx.y - 0.42, 0.0))
    M.at(s("34-02") + 1.8, face=180.0)
    M.walk(w("34-03", "えいっ") - 0.75, w("34-03", "えいっ") - 0.15, (bx.x - 0.05, bx.y - 0.42, 0.0))
    M.at(w("34-03", "えいっ") - 0.1, face=180.0)
    M.push(w("34-03", "えいっ") - 0.05, 0.3)
    key(bt[1], ("location", 1), -100.0, bx.y); key(bt[1], ("location", 1), t_btn - 0.05, bx.y)
    key(bt[1], ("location", 1), t_btn + 0.05, bx.y + 0.015); key(bt[1], ("location", 1), t_btn + 0.5, bx.y)
    ev(t_btn, "click", 0.4, "button"); ev(t_btn + 0.3, "stop", 0.35, "")
    k_m = E.find_step(t_btn, 0.75)
    x_m = E.step_at(k_m, t_btn)[0]
    for nm_, dx in (("stop0", 0.0), ("stop10", 0.10), ("stop60", 0.60)):
        track(nm_, empty((x_m + dx, -(YW - 0.05), 0.005)), 0.0)
    track("stop_now", E.steps[k_m], G.TREAD_DZ)
    M.at(s("35-01") + 0.3, face=10.0)                 # 35-01 の寄り：こちらを向いて首をかしげる
    M.confused(s("35-01") + 0.5)
    # 36-05：段の止まった所まで、転がって測る
    M.at(s("36-01") - 0.05, loc=(1.2, -0.15, 0.0), face=90.0, interp="CONSTANT")
    M.path([(1.35, -0.15, 0.0), (1.5, -0.15, 0.0), (1.62, -0.15, 0.0)], [w("36-05", "測って") + 0.4 * i for i in range(1, 4)], silent=False)
    M.nod(s("36-06") + 0.4)
    ev(w("10-03", "1枚") + 0.1, "katan", 0.15, "")                               # 10-03：すき間から段が入ってくる
    ev(s("11-02") + 0.3, "chain", 0.6, "")                                        # 11-02：鎖の音（小）
    ev(w("11-06", "回ると") + 0.1, "gotton", 0.25, "")                            # 11-06：ゴトン（ゆっくり）
    ev(w("12-01", "くるっと") + 0.1, "gotton", 0.3, "")                            # 12-01：段が歯車で回る
    ev(w("13-01", "くるっと") + 0.1, "gotton", 0.3, "")                            # 13-01：下の歯車で回る
    return dict(E=E, M=M, oj=oj, bt=bt, lid=lid, kb=kb, t_btn=t_btn, t_all=t_all, t_hr=t_hr)


def _night(cl):
    b_night(cl)


# ======================================================================== C：作業場（3章：外した段・模型）
def b_bench(cl):
    bench_room()
    # 外した段（15）：横向きに台の上
    tb = cube(mat("bench", "#7A5B3E", rough=0.7), (-2.2, 0.6, 0.38), (1.6, 1.2, 0.06), bevel=0.01)
    for sx in (-0.7, 0.7):
        for sy in (-0.5, 0.5): cube(MAT["frame"], (-2.2 + sx, 0.6 + sy, 0.18), (0.05, 0.05, 0.36))
    st = make_step(200); st.location = (-2.0, 0.6, 0.41 + 0.05); st.rotation_euler = (0, 0, 0)
    track("step_removed", st, 0.2)
    fw = [c for c in st.children if c.data and c.data.materials and c.data.materials[0].name.startswith("fw")]
    rw = [c for c in st.children if c.data and c.data.materials and c.data.materials[0].name.startswith("rw")]
    fw.sort(key=lambda c: c.matrix_world.translation.y); rw.sort(key=lambda c: c.matrix_world.translation.y)
    if fw: track("fw0", fw[0], 0.0)
    if rw: track("rw0", rw[0], 0.0)
    md = Model3((1.2, 0.6, 0.0))
    for i, s_ in enumerate(md.steps): track("model%d" % i, s_, 0.2)
    rr_ = md.rear_line; mx_ = (rr_[0][0] + rr_[1][0]) / 2 - 0.15; mz_ = (rr_[0][1] + rr_[1][1]) / 2 - 0.15
    track("rear_rail_pt", empty((mx_, 0.6 - Y_RW, mz_)), 0.0); track("rear_rail_lo", empty((mx_, 0.6 - Y_RW, mz_ - 0.45)), 0.0)
    oj = ojisan((-2.2, 1.45, 0.0), face=-90.0); track("ojisan", oj.root, 1.2)   # 台の向こう：段を台に置く（15-01）
    M = MaruR((-3.3, -0.8, 0.0), face=30.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    # 15：段のまわりを歩いて車輪をのぞきこむ
    M.walk(s("15-04") + 0.1, s("15-04") + 2.6, (-2.4, -0.45, 0.0)); M.at(s("15-04") + 3.4, face=170.0); M.peer(e("15-04") - 0.9, 1.3)
    t_put = s("15-01") + 0.3
    for a_ in oj.arms:                                       # おじさんが段を台に置く（腕を前へ → 戻す）
        key(a_, ("rotation_euler", 0), -100.0, 0.0); key(a_, ("rotation_euler", 0), t_put, R(-55)); key(a_, ("rotation_euler", 0), t_put + 1.0, R(-55))
        key(a_, ("rotation_euler", 0), t_put + 1.6, 0.0)
    ev(t_put + 0.9, "clank", 0.3, "step_removed")
    # 17：模型（両方とも前のレール → 傾く → つるっ → 乗せかえ → 水平 → 跳んで上る）
    t_a = w("17-02", "両方とも") + 0.8
    # 17-02：おじさんが模型の向こうへ来て、手で後ろの車輪を前のレールに乗せる
    key(oj.root, "location", -100.0, tuple(oj.root.location), "CONSTANT"); key(oj.root, "location", s("16-01"), (1.25, 1.35, 0.0), "CONSTANT")
    for a_ in oj.arms:
        key(a_, ("rotation_euler", 0), t_a - 0.7, 0.0); key(a_, ("rotation_euler", 0), t_a - 0.1, R(-60)); key(a_, ("rotation_euler", 0), t_a + 1.2, R(-60))
        key(a_, ("rotation_euler", 0), t_a + 1.8, 0.0)
    if CLIPNAME == "C17e":                                   # 17-10 のまるロボの寄り：おじさんの頭が映りこむので、この絵だけ奥へ（前の絵とは溶けてつながる）
        key(oj.root, "location", s("16-01") + 0.01, (4.5, -0.5, 0.0), "CONSTANT")
    md.set_rot(-100.0, 0.0); md.set_rot(t_a, 0.0); md.set_rot(t_a + 1.2, -37.0)
    for i in range(3): ev(t_a + 0.3 * i, "click", 0.3, "model%d" % i)
    M.at(s("17-01") - 0.05, loc=(0.2, -0.55, 0.0), face=60.0, interp="CONSTANT")
    t_j = w("17-04", "乗って") + 0.4
    p1 = md.tread(0, -37.0, -0.2)
    M.jump(t_j, p1, apex=0.3)
    # つるっ：傾いた段をすべり落ちて、模型の下の床へ
    M.carry(t_j + 0.15, t_j + 0.9, lambda t, t0=t_j + 0.15: (-0.55 * min(1, (t - t0) / 0.75) ** 2, 0.0, -(p1[2]) * min(1, (t - t0) / 0.75) ** 2))
    M.act(t_j + 0.5, "tumble_back"); ev(t_j + 0.95, "land", 0.4, "maru_c")
    M.act(s("17-05") + 0.6, "get_up")
    t_b = w("17-06", "乗せかえ") + 0.6
    md.set_rot(t_b, -37.0); md.set_rot(t_b + 1.2, 0.0)
    for i in range(3): ev(t_b + 0.35 * i, "click", 0.3, "model%d" % i)
    o_ = M.off(t_j + 1.0)
    pts = [md.tread(i, 0.0, -0.18) for i in range(3)]
    M.path(pts, [w("17-09", "今度は") + 0.45 * i for i in range(1, 4)], silent=False)
    M.hops(e("17-09") + 0.3, n=1, height=0.05)
    M.confused(w("17-10", "なぜ") - 0.4)
    ev(w("15-03", "前に") + 0.05, "pi", 0.25, ""); ev(w("15-03", "後ろに") + 0.05, "pi", 0.25, "")   # 15-03：車輪が光る（ピッ×2）
    return dict(M=M, md=md, st=st, oj=oj)


def _bench(cl):
    b_bench(cl)


# ======================================================================== D：断面（手前の板を外した絵）
def b_cut(cl):
    station_back()
    sp = SpeedS([(-100.0, 0.3), (s("14-01") + 0.2, 0.3), (s("14-01") + 1.2, 2.2), (e("14-02") - 0.8, 2.2), (e("14-02") + 0.5, 0.3), (2000.0, 0.3)])
    E = Esc(sp, cutaway=True); E.set_cutaway(True); ESC[0] = E
    # シールの段（14-01 で白く光らせて追う）
    k = 0
    stk = E.sticker(k, -50.0); track("sticker", stk, 0.02)
    tr = glow_obj(E.steps[k].children[0], s("14-01") + 0.2, e("14-02") - 0.2, "#FFFFFF", 3.0)
    # 16：レールを順に光らせる（前＝オレンジ・後ろ＝紫）
    for nm, t0, t1 in (("front", w("16-02", "前のレール"), e("16-04") + 0.4), ("rear", w("16-03", "後ろのレール"), e("16-04") + 0.4),
                       ("front", w("18-05", "2本"), e("18-06") + 0.4), ("rear", w("18-05", "2本"), e("18-06") + 0.4),
                       ("front", w("39-02", "2本"), e("39-02") + 0.4), ("rear", w("39-02", "2本"), e("39-02") + 0.4)):
        m_ = MAT["rail_f"] if nm == "front" else MAT["rail_r"]
        if not m_.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value:
            m_.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = m_.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
        emit_key(m_, t0 - 0.3, 0.0); emit_key(m_, t0, 3.0); emit_key(m_, t1, 3.0); emit_key(m_, t1 + 0.3, 0.0)
    def rail_pt(which, s_):
        x_, z_, r_ = G.loop_pose(s_)
        if which == "rear": x_, z_ = G.local_to_world(x_, z_, r_, *G.REAR)
        return (x_, Y_FW if which == "front" else Y_RW, z_)
    s_slope = 5.0; s_end = G.LTOP - 1.2
    for nm_, wh, s_ in (("railf_pt", "front", s_slope), ("railr_pt", "rear", s_slope + 0.0), ("railf_end", "front", s_end), ("railr_end", "rear", s_end)):
        track(nm_, empty(rail_pt(wh, s_)), 0.0)
    track("top_mid", empty((5.0, 0.0, 2.0)), 0.0); track("ret_mid", empty((5.6, 0.0, 0.2)), 0.0)
    k18 = E.find_step(s("18-03") + 1.0, 8.6)
    ch18 = [c for c in E.steps[k18].children if c.type == 'MESH' and c.data.materials and c.data.materials[0].name in ("fw", "rw")]
    for c in ch18:
        if c.location.y > 0: track(c.data.materials[0].name + "_end", c, 0.0)
    # 26-06〜08：くしの真横の切り口（ゆっくり）。まるロボの形の小さな人形を段に乗せる
    doll = MaruR((-20.0, 0.0, 0.0), face=90.0, s=0.4); track("doll", doll.body, 0.3)
    t_d0 = s("26-06") - 0.2
    kd = E.find_step(t_d0, XHC - 0.75)
    doll.at(t_d0 - 0.06, loc=E.tread(kd, t_d0), face=90.0, interp="CONSTANT")
    t_sc = w("26-08", "乗り上げて") + 0.2
    doll.carry(t_d0, t_sc, E.carry_fn(kd, t_d0))
    doll.carry(t_sc, t_sc + 0.8, lambda t, t0=t_sc: (0.45 * min(1, (t - t0) / 0.8), 0.0, 0.04 * math.sin(math.pi * min(1, (t - t0) / 0.8))))
    MARU_ALL.remove(doll); MARU_ALL.append(doll)
    cube(mat("dfloor", "#D9D4CB", rough=0.7), (5.0, -1.6, -0.02), (4.0, 1.6, 0.04))      # まるロボが立つ床（手前）
    M = MaruR((4.5, -1.6, 0.0), face=10.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    _M_[0] = M
    M.confused(s("14-03") + 0.5)
    M.nod(w("20-01", "答え"))
    M.at(s("39-01"), face=10.0)
    ev(s("23-03") + 0.5, "rub", 0.5, "")                                           # 23-03：車ではさんでこする（ゴロゴロ・小）
    return dict(E=E, M=M, doll=doll)


def _cut(cl):
    b_cut(cl)


# ======================================================================== I：想像の場面（4章 24-01〜03・6章 35-02〜03。組み立てで青っぽくする）
def b_imag(cl):
    station(night=False)
    t24 = s("24-01")
    sp = SpeedS([(-100.0, 0.3), (2000.0, 0.3)])
    hr = SpeedS([(-100.0, 0.3), (w("24-02", "引っぱられて") - 1.2, 0.3), (w("24-02", "引っぱられて") - 0.8, 0.18), (s("24-04"), 0.18), (s("24-04") + 0.5, 0.3), (2000.0, 0.3)])
    # 35：ガクンと急に止まる
    t_stop = w("35-02", "ガクン")
    sp = SpeedS([(-100.0, 0.3), (t_stop - 0.04, 0.3), (t_stop + 0.04, 0.0), (s("35-04") + 1.0, 0.0), (2000.0, 0.0)])
    E = Esc(sp, hr_speed=hr); ESC[0] = E
    M = MaruR((-1.9, -0.15, 0.0), face=90.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    # 24：段に乗って手すりに頭をのせる → 手すりが遅れて、頭が後ろへ → ころん
    t0 = t24 - 0.05
    k = E.find_step(t0, 3.2)
    M.at(t0, loc=E.tread(k, t0, ly=-0.22), face=90.0, interp="CONSTANT")
    t_fall = w("24-02", "ころん")
    M.carry(t0 + 0.02, s("24-04"), E.carry_fn(k, t0 + 0.02))
    M.tilt(t0 + 0.3, 16)
    M.lean(w("24-02", "引っぱられて") - 0.8, t_fall - 0.3, -16)
    M.act(t_fall - 0.25, "tumble_back"); ev(t_fall, "land", 0.4, "maru_c")
    # 35：段に乗っている → ガクン → 前へつんのめって転がる
    t35 = s("35-02") - 0.05
    k2 = E.find_step(t35, 3.0)
    M.at(t35, loc=E.tread(k2, t35, ly=0.0), face=90.0, interp="CONSTANT")
    M.carry(t35 + 0.02, t_stop, E.carry_fn(k2, t35 + 0.02))
    M.carry(t_stop, t_stop + 0.5, lambda t, t0=t_stop: (0.35 * min(1, (t - t0) / 0.5), 0.0, 0.17 * min(1, (t - t0) / 0.5)))
    M.act(t_stop + 0.05, "roll_over", side=1); ev(t_stop, "thunk", 0.4, "maru_c")
    return dict(E=E, M=M)


def _imag(cl):
    b_imag(cl)


# ======================================================================== カット割り：(名前, 舞台, 切り替わる時刻, カメラ, 親)
#   同じ絵を 12 秒以上続けない。文の切れ目で、寄り・引き・横・まるロボを追う絵に替える（7本目と同じ）
def INL(dx, dy, dz, lens=28):
    def mk(t0):
        x = ESC[0].inlets["lo"].location.x
        return cam((x + dx, -(Y_HR) + dy, 0.6 + dz), (x, -(Y_HR), 0.55), lens)
    return mk


HX, HZ = G.X_HI_END, G.H
WIDE_D = C((5.0, -13.0, 1.0), (5.0, 0.0, 0.8), 34, (5.0, -12.6, 1.0))
MARU_D = C((4.0, -4.4, 1.0), (4.7, 0.0, 0.9), 30, (4.1, -4.3, 1.0))
CUTS = [
    # 冒頭（昼）
    ("A01", _day, 0.0, C((-4.6, -3.8, 1.7), (0.5, 0.0, 0.7), 30, (-4.1, -3.4, 1.5)), "A"),
    ("A01b", _day, s("01-02"), lambda t0: F((0.9, -1.4, 2.2), 32), "A"),
    ("A01c", _day, s("01-03"), C((-3.2, -1.0, 1.0), (4.0, 0.0, 2.2), 28), "A"),
    ("A01d", _day, s("01-04"), C((0.3, -2.6, 3.0), (0.4, 0.0, 0.5), 30), "A"),
    ("A02", _day, s("02-01"), lambda t0: F((-0.5, -1.5, 2.4), 30), "A"),
    ("A02b", _day, s("02-03"), lambda t0: F((0.5, -0.9, 1.6), 32, 0.1), "A"),
    ("A02c", _day, s("02-04"), lambda t0: F((-1.2, -1.3, 2.2), 34), "A"),
    ("A02d", _day, s("02-05"), C((4.5, -12.0, 2.0), (4.8, 0.0, 1.5), 30), "A"),
    ("A03", _day, s("03-01"), lambda t0: F((0.3, -1.5, 2.4), 30), "A"),
    ("A03b", _day, s("03-02"), C((XHC - 1.1, -0.85, HZ + 1.5), (XHC + 0.25, 0.0, HZ), 28), "A"),
    ("A03c", _day, s("03-04"), C((XHC - 0.8, -0.3, HZ + 0.45), (XHC + 0.1, 0.0, HZ + 0.05), 24), "A"),
    ("A04", _day, s("04-01"), lambda t0: F((-1.6, -1.4, 2.4), 32), "A"),
    ("A04b", _day, s("04-02"), C((XHC + 0.75, -0.22, HZ + 0.42), (XHC - 0.6, 0.0, HZ + 0.42), 24), "A"),
    ("A04c", _day, s("04-03"), C((XHC + 0.2, -1.6, HZ + 2.4), (XHC + 0.2, 0.0, HZ + 0.2), 28), "A"),
    ("A04d", _day, s("04-04"), C((XHC + 3.0, -2.3, HZ + 1.9), (XHC - 0.1, -0.05, HZ + 0.3), 30), "A"),   # 床の上のまるロボと、すき間へ入る段を前の上から（横からは手すりの壁に隠れた）
    ("A04e", _day, s("04-06"), lambda t0: F((-1.3, -0.3, 0.9), 34), "A"),
    ("A05", _day, s("05-01"), C((-6.0, -12.0, 4.0), (5.0, 0.0, 1.5), 26, (-5.0, -11.0, 3.6)), "A"),
    ("A05b", _day, s("05-02"), C((XHC - 1.1, -0.85, HZ + 1.5), (XHC + 0.25, 0.0, HZ), 28), "A"),
    ("A05c", _day, s("05-04"), lambda t0: F((-1.3, -0.3, 0.9), 34), "A"),
    # 1章（昼）
    ("A06", _day, s("06-01"), C((XHC + 0.9, -0.5, HZ + 2.2), (XHC - 0.35, 0.0, HZ), 28), "A"),   # 上から見下ろして、まるロボの頭ごしにすき間（正面からはまるロボの背中で隠れた）
    ("A06b", _day, s("06-04"), C((XHC - 2.0, -3.2, HZ + 1.6), (XHC, 0.0, HZ), 30, (-2.2, -3.2, 1.6), (XLC, 0.0, 0.0), d=2.5), "A"),
    ("A06c", _day, s("06-05"), C((XLC - 2.2, -0.3, 1.3), (XLC + 0.5, 0.0, 0.0), 30), "A"),
    ("A06d", _day, s("06-06"), C((4.8, -12.5, 1.8), (4.8, 0.0, 1.4), 32), "A"),
    ("A07", _day, s("07-01"), C((XLC - 2.3, -1.4, 2.2), (XLC - 0.3, -0.2, 0.4), 30), "A"),   # 手すりの壁ごしに見下ろす（低いとまるロボが壁に隠れた）
    ("A07b", _day, s("07-03"), C((XLC + 1.2, -1.0, 1.5), (XLC - 0.1, -0.1, 0.2), 30), "A"),
    ("A07c", _day, s("07-04"), lambda t0: F((-0.4, -1.5, 2.4), 30), "A"),
    ("A07d", _day, s("07-05"), C((XHC - 1.1, -0.85, HZ + 1.5), (XHC + 0.25, 0.0, HZ), 28), "A"),
    ("A08", _day, s("08-01"), C((6.2, -1.6, 4.3), (7.2, 2.4, 2.6), 28), "A"),
    ("A08b", _day, s("08-02"), C((XLC - 2.3, -1.4, 2.2), (XLC - 0.1, -0.15, 0.4), 30), "A"),   # 同じ（まるロボと乗り口を一緒に）
    ("A08c", _day, s("08-04"), C((XLC - 0.3, -0.3, 1.0), (XLC + 0.7, -0.25, 0.0), 30), "A"),
    ("A08d", _day, s("08-05"), C((4.8, -12.5, 1.8), (4.8, 0.0, 1.0), 32), "A"),
    ("A08e", _day, s("08-07"), lambda t0: F((0.9, -1.3, 2.0), 34), "A"),
    # 2章（夜・床の下）
    ("B09", _night, s("09-01"), C((-5.0, -12.0, 4.5), (5.5, 0.0, 1.5), 26, (-4.6, -11.6, 4.3)), "B"),
    ("B09b", _night, s("09-02"), C((LID_HI[0] + 0.9, -4.6, HZ + 1.4), (LID_HI[0] + 0.9, -0.5, HZ + 0.8), 30), "B"),
    ("B09c", _night, s("09-03"), C((LID_HI[0] + 1.0, -4.6, HZ + 2.0), (LID_HI[0] + 1.0, -0.7, HZ + 0.4), 28), "B"),
    ("B09d", _night, s("09-04"), C((LID_HI[0] + 0.7, -1.0, HZ + 1.9), (LID_HI[0] + 0.7, 0.0, Z_PIT_HI), 30), "B"),
    ("B09e", _night, s("09-05"), C((XHC + 2.0, -4.6, HZ + 2.0), (XHC + 1.7, -0.5, HZ + 0.3), 24), "B"),
    ("B09f", _night, w("09-05", "動かして") + 0.3, C((XHC + 1.2, -1.2, HZ + 1.6), (XHC - 1.5, 0.0, HZ - 0.3), 28), "B"),   # 段が動き出す（坂を見下ろす）
    ("B10", _night, s("10-01"), C((XR_PIT - 0.25, -0.55, Z_PIT_HI + 0.5), (HX + 0.2, 0.0, HZ - 0.4), 20), "B"),
    ("B10b", _night, s("10-02"), C((XHC + 1.0, -0.45, Z_PIT_HI + 0.7), (XHC - 0.2, 0.0, HZ - 0.1), 20), "B"),
    ("B11", _night, s("11-01"), C((HX + 0.7, -0.6, HZ - 0.55), (HX - 0.7, -0.5, HZ - 0.3), 22), "B"),
    ("B11b", _night, s("11-04"), lambda t0: F((1.5, -0.4, 0.55), 28), "B"),   # 引いて、背中で鎖が隠れないように
    ("B11c", _night, s("11-05"), C((XR_PIT - 0.3, -0.6, Z_PIT_HI + 0.4), (HX, 0.0, HZ - 0.6), 20), "B"),
    ("B12b", _night, s("12-01"), C((HX + 1.0, -0.62, HZ - 0.5), (HX - 0.15, 0.0, HZ - 0.85), 20), "B"),   # 引いて、歯車のまわりを回る段を見せる（寄りすぎで車輪の色の固まりしか見えなかった）
    ("B12c", _night, s("12-02"), C((HX - 0.2, -0.68, 1.9), (HX - 2.2, 0.0, 1.3), 20), "B"),
    ("D12", _cut, s("12-03"), WIDE_D, "D"),
    ("B12d", _night, s("12-04"), C((HX + 0.4, -0.62, 2.0), (HX - 1.6, 0.0, 1.5), 18), "B"),
    ("B12e", _night, s("12-05"), lambda t0: F((1.5, -0.4, 0.55), 28), "B"),
    ("B12f", _night, s("12-07"), lambda t0: F((1.2, -0.6, 0.5), 26), "B"),
    ("B13", _night, s("13-01"), C((1.3, -0.62, -0.55), (0.1, 0.0, -0.85), 20), "B"),
    ("B13b", _night, s("13-03"), C((XLC + 1.0, -0.3, 0.45), (XLC - 0.1, 0.0, 0.02), 24), "B"),   # 乗り口のすき間から段が出てくる（床の上の低い所から）
    ("B13c", _night, s("13-04"), C((LID_LO[0] - 1.9, -2.6, 1.4), (LID_LO[0] - 0.3, -0.1, 0.55), 30), "B"),
    ("B13d", _night, s("13-05"), lambda t0: F((-0.9, -1.4, 0.4), 34), "B"),
    ("D14", _cut, s("14-00"), WIDE_D, "D"),
    ("D14b", _cut, s("14-03"), MARU_D, "D"),
    ("D14c", _cut, s("14-04"), C((4.6, -3.4, 1.2), (4.6, 0.0, 1.0), 32), "D"),
    # 3章（作業場・断面）
    ("C15", _bench, s("15-01"), C((-0.5, -3.5, 1.6), (-2.0, 0.6, 0.5), 30, (-0.7, -3.3, 1.5)), "C"),
    ("C15b", _bench, s("15-02"), C((-2.0, -1.4, 0.7), (-2.0, 0.6, 0.55), 30), "C"),
    ("C15c", _bench, s("15-03"), C((-1.0, -1.3, 1.0), (-2.1, 0.6, 0.5), 30), "C"),
    ("C15d", _bench, s("15-04"), lambda t0: F((0.9, -1.4, 0.35), 32), "C"),
    ("D15", _cut, s("15-05"), C((4.6, -3.6, 1.3), (4.6, 0.0, 1.0), 30), "D"),
    ("D16", _cut, s("16-01"), C((4.6, -2.8, 1.0), (4.6, 0.0, 0.9), 30, (4.9, -2.8, 1.1)), "D"),
    ("C17", _bench, s("17-01"), C((2.1, -3.7, 1.4), (2.1, 0.6, 0.8), 30), "C"),
    ("C17b", _bench, s("17-02"), C((2.0, -2.7, 1.0), (2.0, 0.6, 0.9), 30), "C"),
    ("C17c", _bench, s("17-04"), C((1.6, -3.3, 1.0), (1.6, 0.6, 0.6), 30), "C"),
    ("C17d", _bench, s("17-06"), C((2.0, -2.7, 1.0), (2.0, 0.6, 0.9), 30), "C"),
    ("C17e", _bench, s("17-10"), lambda t0: F((0.5, 1.5, 0.35), 34), "C"),
    ("C17f", _bench, s("17-11"), C((1.9, -1.6, 0.95), (1.9, 0.6, 0.85), 26), "C"),
    ("D17", _cut, s("17-12"), C((4.6, -3.0, 1.1), (4.6, 0.0, 0.9), 30), "D"),
    ("D18", _cut, s("18-01"), C((8.8, -3.0, 2.6), (8.8, 0.0, 2.5), 30, (9.0, -2.9, 2.6)), "D"),
    ("D18b", _cut, s("18-03"), C((8.6, -1.9, 2.7), (8.6, 0.0, 2.6), 30), "D"),
    ("D18c", _cut, s("18-05"), WIDE_D, "D"),
    ("D20", _cut, s("20-01"), MARU_D, "D"),
    ("D20b", _cut, s("20-02"), WIDE_D, "D"),
    # 4章（昼・断面・想像）
    ("A21", _day, s("21-01"), C((-3.5, -6.5, 2.4), (2.5, 0.0, 1.0), 28), "A"),
    ("A21b", _day, s("21-02"), C((-1.8, -1.3, 1.8), (3.0, 0.0, 1.5), 30), "A"),
    ("A21c", _day, s("21-03"), C((1.6, -1.6, 2.0), (2.6, -0.67, 1.3), 30), "A"),
    ("A22", _day, s("22-01"), lambda t0: F((0.6, -1.4, 2.2), 32, 0.6), "A"),
    ("A22b", _day, s("22-02"), lambda t0: F((0.2, -1.2, 2.0), 32, 0.6), "A"),
    ("D23", _cut, s("23-01"), C((5.5, -3.0, 1.4), (5.5, 0.6, 1.0), 30), "D"),
    ("D23b", _cut, s("23-03"), C((5.0, -1.8, 1.1), (5.0, 0.6, 0.9), 26), "D"),
    ("I24", _imag, s("24-01"), lambda t0: F((0.6, -1.4, 2.2), 32, 0.6), "I"),
    ("A24", _day, s("24-04"), C((3.0, -1.3, 3.2), (3.8, 0.0, 1.2), 28), "A"),
    ("A24c", _day, s("24-07"), C((2.2, -1.7, 2.0), (3.6, -0.6, 1.5), 30), "A"),
    # 5章（昼・断面）
    ("A25", _day, s("25-01"), C((XHC + 0.2, -1.6, HZ + 2.4), (XHC + 0.2, 0.0, HZ + 0.2), 28), "A"),
    ("A25b", _day, s("25-02"), lambda t0: F((-1.3, -0.3, 0.9), 34), "A"),
    ("A26", _day, s("26-01"), C((XHC - 0.9, -0.35, HZ + 0.75), (XHC, -0.05, HZ), 28), "A"),
    ("A26b", _day, s("26-02"), C((XHC - 0.45, -0.3, HZ + 0.35), (XHC, 0.0, HZ), 28), "A"),
    ("A26c", _day, s("26-03"), C((XHC - 1.5, -0.35, HZ + 0.7), (XHC - 1.0, 0.0, HZ), 30), "A"),
    ("A26d", _day, s("26-04"), C((XHC - 0.5, -0.35, HZ + 0.22), (XHC, 0.0, HZ - 0.02), 24), "A"),
    ("A26e", _day, s("26-05"), lambda t0: F((-1.3, -0.3, 0.9), 34), "A"),
    ("D26", _cut, s("26-06"), C((XHC - 0.25, -1.6, HZ + 0.3), (XHC, 0.0, HZ), 26), "D"),
    ("A26f", _day, s("26-10"), C((XHC - 0.3, -0.2, HZ + 0.18), (XHC, 0.08, HZ), 24), "A"),
    ("A27", _day, s("27-01"), C((2.5, -0.25, 1.15), (3.1, -0.5, 0.55), 26, (2.9, -0.25, 1.35), (3.5, -0.5, 0.75)), "A"),
    ("A27c", _day, s("27-05"), C((3.2, -0.15, 1.25), (3.6, -0.5, 0.75), 26), "A"),
    # 6章（夜）
    ("B28", _night, s("28-01"), C((-5.0, -6.0, 2.5), (1.0, 0.0, 0.8), 28), "B"),
    ("B28b", _night, s("28-02"), lambda t0: F((1.2, -1.6, 0.35), 34), "B"),
    ("B28c", _night, s("28-03"), C((-3.6, -5.0, 2.2), (1.5, 0.0, 0.6), 28), "B"),
    ("B28d", _night, s("28-04"), C((XLC - 0.6, -3.5, 1.2), (XLC - 1.8, -1.0, 0.8), 30), "B"),
    ("B29", _night, s("29-01"), INL(-0.9, -1.2, 0.0), "B"),
    ("B29b", _night, s("29-02"), C((XLC - 1.95, -3.1, 0.9), (XLC - 1.85, -0.67, 0.6), 30), "B"),
    ("B29c", _night, s("29-05"), lambda t0: F((0.9, -1.5, 0.4), 34), "B"),
    ("B30", _night, s("30-01"), C((XLC - 1.3, -0.6, 1.6), (XLC + 0.6, -0.45, 0.35), 26), "B"),   # リボンが止まる所まで入れる（上から見下ろすと段といっしょに画面の外へ出た）
    ("B31", _night, s("31-01"), C((XLC + 1.2, -0.5, 1.2), (XLC - 0.05, 0.1, 0.25), 22), "B"),
    ("B32", _night, s("32-01"), C((XLC - 0.9, -2.0, 2.2), (XLC - 0.5, -0.45, 0.8), 30), "B"),
    ("B32b", _night, s("32-05"), INL(-0.9, -1.2, 0.0), "B"),
    ("B33", _night, s("33-01"), C((-3.6, -5.0, 2.2), (1.5, 0.0, 0.6), 28), "B"),
    ("B33b", _night, s("33-02"), lambda t0: F((0.9, -1.3, 2.0), 34), "B"),
    ("B33c", _night, s("33-03"), C((XLC - 0.6, -3.5, 1.2), (XLC - 1.8, -1.0, 0.8), 30), "B"),
    ("B34", _night, s("34-01"), C((XLC - 1.3, -3.4, 1.3), (XLC - 1.4, -0.8, 0.6), 28), "B"),
    ("B34b", _night, s("34-03"), C((XLC + 0.9, -1.75, 1.1), (XLC - 0.77, -0.9, 0.6), 30), "B"),
    ("B34c", _night, s("34-04"), C((1.2, -1.5, 2.6), (1.2, 0.0, 0.1), 30), "B"),
    ("B35a", _night, s("35-01"), C((-0.2, -2.7, 0.75), (-0.45, -1.18, 0.45), 32), "B"),
    ("I35", _imag, s("35-02"), lambda t0: F((0.4, -1.4, 2.2), 30, 0.5), "I"),
    ("B35", _night, s("35-04"), C((1.2, -1.5, 2.6), (1.2, 0.0, 0.1), 30), "B"),
    ("B36", _night, s("36-01"), C((1.4, -1.5, 2.6), (1.4, 0.0, 0.0), 30), "B"),
    ("B36b", _night, s("36-05"), lambda t0: F((0.3, -1.3, 1.9), 32), "B"),
    ("B36c", _night, s("36-06"), C((3.0, -0.2, 1.45), (1.62, -0.15, 0.45), 30), "B"),
    ("A38", _day, s("38-01"), lambda t0: F((0.0, -1.7, 0.4), 36), "A"),
    ("A38b", _day, s("38-02"), C((XLC - 1.5, -2.0, 0.95), (XLC - 0.75, -0.73, 0.62), 28), "A"),
    # まとめ・オチ
    ("D39", _cut, s("39-01"), WIDE_D, "D"),
    ("A39", _day, s("39-06"), C((-6.0, -12.0, 4.0), (5.0, 0.0, 1.5), 26, (-5.5, -11.5, 3.8)), "A"),
    ("A40", _day, s("40-01"), lambda t0: F((-0.3, -1.5, 2.4), 30), "A"),
    ("A40b", _day, s("40-02"), C((XHC + 3.0, -2.3, HZ + 2.2), (XHC + 0.4, -0.15, HZ + 0.5), 30), "A"),   # 降り口の先の上から（横からは手すりの壁にまるロボが隠れた）
    ("A40c", _day, s("40-05"), C((XHC + 0.3, -1.7, HZ + 0.9), (XHC + 1.0, -0.2, HZ + 0.7), 32), "A"),
]
END_T = e("40-05") + 2.5
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
                if os.environ.get("MARU_PLANONLY") == "log":
                    for i_, r_ in enumerate(m_.log):
                        print("MARU_LOG", r_[0], r_[1], r_[2])
            print("MARU_LATE", json.dumps(MARU_LATE, ensure_ascii=False)); sys.exit(0)
        bake_maru(t0, t1)
        if cm is not None: cm(t0)
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
