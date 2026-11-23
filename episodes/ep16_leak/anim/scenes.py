# 16本目（情報流出）：3D の場面を声の時刻に合わせて動かして描く（9本目の scenes.py と同じ作り方）
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 4] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   PC の本番：... -- <クリップ> <出力> --samples 24 --res 1920 1080 --frames 0 99 --gpu --video --fast
#   舞台：A＝まるロボの家（b_house）／T＝机の上のたとえ（b_table）／B＝昼のお城（b_castle）／N＝夜のお城（b_night）／I＝想像の場面（b_imag。組み立てで青っぽくする）
#   舞台の組み立て（b_*）は、その舞台の動きを全部作り、カメラだけをクリップごとに選ぶ。絵コンテ表：../絵コンテ_v1.md
#   決まり：3D の中に字を書かない／まるロボは喋らない・本物の体を marumotion の予定で動かす（maru16.py）／動きは言い終えてから
#   この版は冒頭と 1章（S01〜S12）。§2.6：章ごとに動く下書きで OK をもらう
import os, sys, math, json
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.read_factory_settings(use_empty=True)
TEX = os.environ.get("TEX16") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "tex16")
exec(open(os.path.join(KIT_HERE, "kit16.py"), encoding="utf-8").read())
MAT = M if "M" in dir() else None
_K7 = KIT_HERE
exec(open(os.path.join(KIT_HERE, "..", "..", "ep06_haizen", "anim", "core.py"), encoding="utf-8").read().replace(
    'VO = os.path.join(KIT_HERE, "..", "voice")', 'VO = os.path.join(_K7, "..", "voice")'))
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
exec(open(os.path.join(_K7, "maru16.py"), encoding="utf-8").read())


def cam(loc, target, lens=35, t0=None, t1=None, loc1=None, target1=None, lens1=None):
    c, tg = cam_rig(loc, target, lens)
    c.data.dof.use_dof = False; c.data.dof.aperture_fstop = 64.0
    if t0 is not None:
        cam_move(c, tg, t0, t1, loc, loc1 or loc, target, target1 or target, lens, lens1 or lens)
    return c, tg


def F(off, lens=40, dz=0.35, t0=None, t1=None, off1=None):
    """まるロボを追うカメラ（足もとの root を追う）。off＝まるロボからのずれ（世界の向き）"""
    c = cam_follow(_M_[0].root, off, dz, lens); c.data.dof.aperture_fstop = 64.0
    if t0 is not None: key(c, "location", t0, off); key(c, "location", t1, off1)
    return c


def C(loc, tgt, lens=35, loc1=None, tgt1=None, lens1=None, d=8.0):
    """決まったカメラ（d 秒かけて loc → loc1 へゆっくり動く）"""
    def mk(t0):
        return cam(loc, tgt, lens, t0, t0 + d, loc1 or loc, tgt1 or tgt, lens1 or lens)
    return mk


def hold_key(ob, path, t, v):
    key(ob, path, t, v, "CONSTANT")


def pop_in(ob, t, s1=1.0, d=0.3):
    """t にぽんと出る（それまでは小さくして見えない）"""
    key(ob, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(ob, "scale", t, (0.001, 0.001, 0.001)); key(ob, "scale", t + d, (s1, s1, s1))


def pop_out(ob, t, s0=1.0, d=0.25):
    key(ob, "scale", t, (s0, s0, s0)); key(ob, "scale", t + d, (0.001, 0.001, 0.001), "CONSTANT")


# ======================================================================== A：まるロボの家（冒頭 S01〜S04）
PH = (1.95, 0.65, 0.0)          # 床に置いたスマホ（画面が上）
HOUSE_S = 0.40                  # 家の中のまるロボの大きさ（小さなロボ。床のスマホをのぞける）


def b_house(cl):
    room(window=True)
    ph, scr = phone_seq(PH, 90.0, [(0.0, os.path.join(TEX, "ph_home.png")),
                                    (w("01-03", "開きます") + 0.1, os.path.join(TEX, "ph_mail.png")),
                                    (s("04-02"), os.path.join(TEX, "ph_mail_end.png"))], glow=1.6)
    track("phone", ph, 0.0)
    # 通知が来たとき、スマホが光って震える（01-01 の「メール」）
    t_n = w("01-01", "メール") - 0.3
    ev(t_n, "chime", 0.5, "phone")
    for k in range(6):
        key(ph, "rotation_euler", t_n + k * 0.06, (0, 0, R(90 + (3 if k % 2 else -3))))
    key(ph, "rotation_euler", t_n + 0.4, (0, 0, R(90)))
    M = MaruR((1.3, 0.6, 0.0), face=90.0, s=HOUSE_S); track("maru", M.body, 0.25); track("maru_top", M.body, 0.32)
    # 01：通知で起きる → スマホに近づく → わくわく → 頭でちょんと押す
    M.act(t_n + 0.25, "wake")
    M.walk(s("01-02") + 0.2, s("01-02") + 2.0, (1.72, 0.62, 0.0))
    M.at(s("01-02") + 2.2, look=-25)
    M.wobble(w("01-03", "わくわく") - 0.2, w("01-03", "開きます") - 0.4, 9, 0.45)
    M.push(w("01-03", "開きます") - 0.25, 0.12); ev(w("01-03", "開きます"), "tap", 0.35, "phone")
    # 02：読む → え？（驚く）→ ほっとして首をかしげる（02-08）
    M.surprise(w("02-02", "え") - 0.05)
    M.at(e("02-02") + 0.3, look=0)
    M.confused(w("02-08", "安心") + 0.2)
    # 03：家の中のまるロボは小さく（遅い）ので、歩き回らず、その場で見回す → 窓を見る（動作を詰めない）
    M.act(s("03-01") + 0.2, "look_around")                                 # あわててきょろきょろ
    M.at(s("03-03") + 0.3, face=90.0); M.at(w("03-03", "お店") + 0.2, look=18)    # 窓の外（奥。盗まれたのはお店の方）を見る
    M.sigh(e("04-02") - 1.0)


# ======================================================================== T：机の上のたとえ（05）と、小窓（02-03 お店から紙が出ていく）
TZ = 0.75


def b_table(cl):
    table_set((0, 0, TZ))
    shop = shop_model((-0.36, -0.02, TZ), 1.0); track("shop", shop, 0.12)
    cas = castle_model((-0.36, -0.02, TZ), 1.0); track("castle_m", cas, 0.15)
    pop_out(shop, w("05-02", "お城") - 0.35); pop_in(cas, w("05-02", "お城") - 0.1); ev(w("05-02", "お城") - 0.1, "pop", 0.4, "castle_m")
    bd = board((0.0, 0.02, TZ), "form4", w=0.2, h=0.24); track("form", bd, 0.14)
    tag = nameplate((0.0, -0.03, TZ + 0.11), rot=(R(80), 0, 0), w=0.26); track("tag", tag, 0.0)
    pop_out(bd, w("05-03", "1枚") - 0.35); pop_in(tag, w("05-03", "1枚") - 0.1); ev(w("05-03", "1枚") - 0.1, "pop", 0.4, "tag")
    pw = pw_board((0.36, -0.02, TZ)); track("pw", pw, 0.05)
    ky = key_obj((0.31, -0.04, TZ + 0.06), rot=(0, 0, 0), s=1.3); track("key", ky, 0.0)
    pop_out(pw, w("05-04", "鍵") - 0.35); pop_in(ky, w("05-04", "鍵") - 0.1, s1=1.3); ev(w("05-04", "鍵") - 0.1, "pop", 0.4, "key")
    key(ky, "rotation_euler", w("05-04", "鍵"), (0, 0, 0)); key(ky, "rotation_euler", e("05-05"), (0, 0, R(40)))
    # 02-03 の小窓：お店の模型から、紙が外へ出ていく（お店は shop。流出＝外へ盗み出される）
    t2 = s("02-03")
    for k in range(5):
        pp = cube(mat("paper", "#FFFFFF", rough=0.6), (-0.36, -0.1, TZ + 0.05), (0.05, 0.035, 0.002))
        t_ = t2 + 0.5 + k * 0.45
        key(pp, "location", -100.0, (-0.36, -0.06, TZ + 0.05), "CONSTANT"); key(pp, "location", t_, (-0.36, -0.1, TZ + 0.05))
        key(pp, "location", t_ + 1.4, (-0.36 + 0.35 + 0.04 * k, -0.45 - 0.05 * k, TZ + 0.18 + 0.03 * (k % 2)))
        key(pp, "rotation_euler", t_, (0, 0, 0)); key(pp, "rotation_euler", t_ + 1.4, (R(30), R(20 * k), R(50)))
    M = MaruR((0.02, 0.28, TZ), face=0.0, s=0.22); track("maru", M.body, 0.18); track("maru_top", M.body, 0.24)
    M.at(w("05-02", "お城"), look=-10)
    M.surprise(w("05-03", "名札") + 0.2)
    M.hops(w("05-05", "名札") + 0.2, n=2)


# ======================================================================== B：昼のお城（06〜11）
GK = (1.75, -1.1, 0.0)          # 門番さんの立つ所（門の右。正面の外を向く）
DOOR2_Y = DOOR_Y + 3.2          # 10-07（v1：1.7 では、08-02「小さな扉がありました」の絵に 2 つの扉が並んで見えた）：同じかべの、もう 1 つの裏口（かんたんな鍵で開く）


def _castle_common(night):
    C_ = castle(night=night)
    gk = gatekeeper(GK, 0.0, night); track("gk", gk.head, 0.0)
    dc = empty((0, 0, 0)); dc.parent = C_["door"]; dc.location = (0.06, DOOR_W / 2, DOOR_H / 2)     # 扉のまん中（赤い丸・？を置く。v1：蝶つがいの端に出ていた）
    track("gate", C_["gate"][0], 2.0); track("door", dc, 0.0); track("lock", C_["lock"]["root"], 0.0)
    return C_, gk


def b_castle(cl):
    C_, gk = _castle_common(False)
    # 10-05：直す部品の箱（扉の横に置きっぱなし）。10-03 の「届けて」で上から降りてくる
    bx = parts_box((X_SIDE + 0.55, DOOR_Y + 0.95, 0.0)); track("box", bx, 0.25)
    t_box = w("10-03", "届けて") - 0.4
    key(bx, "location", -100.0, (X_SIDE + 0.55, DOOR_Y + 0.95, 3.0), "CONSTANT"); key(bx, "location", t_box, (X_SIDE + 0.55, DOOR_Y + 0.95, 3.0))
    key(bx, "location", t_box + 0.7, (X_SIDE + 0.55, DOOR_Y + 0.95, 0.0)); ev(t_box + 0.7, "thud", 0.35, "box")
    # 10-05：錠のひびが赤く光る（弱い所。中身や場所は描かない）
    cm = C_["lock"]["crack"]
    for _c in C_["lock"]["crack_objs"]: hide_key(_c, -100.0, True); hide_key(_c, w("10-05", "弱い所") - 0.3, False); hide_key(_c, e("10-06") + 0.6, True)
    emit_key(cm, w("10-05", "弱い所") - 0.3, 2.0); emit_key(cm, w("10-05", "弱い所"), 6.0); emit_key(cm, e("10-06") + 0.3, 6.0); emit_key(cm, e("10-06") + 0.6, 2.0)
    # 10-07：もう 1 つの裏口（同じかべの先）。かんたんな形の鍵が差さって開く
    hinge2 = empty((X_SIDE + 0.02, DOOR2_Y - DOOR_W / 2, 0.0))
    cube(noise_mat("doorwood", "#7C6448", "#6A5440", 1.2, 0.85, wave=True), (0.04, DOOR_W / 2, DOOR_H / 2), (0.08, DOOR_W, DOOR_H), parent=hinge2)
    lk2 = old_lock((0, 0, 0), face=90.0, crack=False); lk2["root"].parent = hinge2; lk2["root"].location = (0.12, DOOR_W - 0.14, 0.82)
    track("door2", hinge2, 0.75)
    sk = key_obj((X_SIDE + 0.6, DOOR2_Y + DOOR_W / 2 - 0.14, 0.81), rot=(0, 0, R(180)), simple=True, s=1.4); track("skey", sk, 0.0)
    t_k = w("10-07", "かんたんな") - 0.2
    sk.scale = (0, 0, 0); key(sk, "scale", -100.0, (0, 0, 0), "CONSTANT"); pop_in(sk, t_k - 0.35, 1.4, 0.25)     # 鍵は 10-07 で出す（v1：初めから扉の横に浮いていた）
    key(sk, "location", -100.0, (X_SIDE + 0.6, DOOR2_Y + DOOR_W / 2 - 0.14, 0.81), "CONSTANT")
    key(sk, "location", t_k, (X_SIDE + 0.6, DOOR2_Y + DOOR_W / 2 - 0.14, 0.81)); key(sk, "location", t_k + 0.8, (X_SIDE + 0.34, DOOR2_Y + DOOR_W / 2 - 0.14, 0.81))
    ev(t_k + 0.8, "click", 0.4, "skey")
    t_o = w("10-07", "開いて") - 0.1
    key(hinge2, "rotation_euler", t_o, (0, 0, 0)); key(hinge2, "rotation_euler", t_o + 1.0, (0, 0, R(-70))); ev(t_o, "creak", 0.35, "door2")
    pop_out(sk, t_o + 0.05, 1.4, 0.05)
    # まるロボ（歩く速さは 0.72 m/s。距離 ÷ 速さで間に合うよう、立ち位置を近くし、移動を減らす。SKILL §5）
    M = MaruR((0.0, -1.6, 0.0), face=180.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    # 06：門の前（既に来ている。06-01 は引きの絵で見せる）→ 見上げる → 少し踏み込んで押す → 体当たり → 後ろへ転ぶ → 起きる → 門番の横へ
    M.at(s("06-01") + 0.3, look=10); M.at(s("06-02") + 0.2, look=22); M.at(e("06-03"), look=0)
    M.confused(w("06-04", "どうやって") - 0.3)
    M.walk(s("06-05") - 1.6, w("06-05", "押して") + 0.1, (0.0, -0.6, 0.0))    # 門の前まで歩く（v1 の点検：門まで 1 m 届かずに押していた。体の前が門の鉄の帯から 0.06 m、押すと当たる）
    M.push(w("06-05", "押して") + 1.25, 0.25); ev(w("06-05", "押して") + 1.4, "push", 0.4, "maru_c")    # 門に着いてから押す（歩きは 1.04 秒遅れて 146.2 秒に着く）
    M.at(s("06-07") + 0.2, face=180.0)
    t_hit = w("06-07", "体当たり") + 0.1
    M.act(t_hit, "bonk"); ev(t_hit, "thump", 0.5, "gate")              # その場で体当たり → ゴツン
    M.act(t_hit + 0.3, "tumble_back", lift=0.0); ev(t_hit + 0.35, "boing", 0.35, "maru_c")
    M.act(s("06-09") - 1.3, "get_up")
    M.shake(e("06-09") - 0.6)                                          # 門番の横まで歩かず、その場で「だめ」と首を振る
    M.at(s("07-03") - 0.1, face=180.0)
    M.confused(w("07-03", "どこから") - 0.2)
    # 08：正面を見たまま → 「うしろです」でふり向いて驚く（移動はしない）→ 09 でカメラが裏口へ移る間に、裏口の前へ置き直す
    M.at(s("08-01"), face=180.0)
    M.at(s("08-03") + 0.2, face=170.0)
    M.surprise(w("08-04", "うしろ") + 0.2)
    # 09：カメラが裏口に切り替わる所で、裏口の前に置き直す（カメラが変わるのでワープに見えない）
    M.at(s("09-01") - 0.05, loc=(X_SIDE + 0.72, DOOR_Y - 0.05, 0.0), face=-90.0, interp="CONSTANT")   # 08-04 の驚きが終わる 192.1 秒に効く。裏口のカットは 09-01 の 0.55 秒あとから（v1：カットの頭で、まるロボが急に現れた）
    M.at(e("09-01") + 0.1, look=15)
    M.at(s("09-02") + 0.1, face=125.0)                                  # 見る人のほうを向いて「なぜ？」
    M.confused(w("09-02", "なぜ") - 0.3)
    M.at(e("09-02"), look=0, face=-90.0)
    M.walk(s("09-04") + 0.3, s("09-04") + 3.3, (X_SIDE + 2.6, DOOR_Y - 0.6, 0.0))   # 扉の前をあける（09-05 で扉を見せる）
    M.at(s("09-04") + 3.5, face=-90.0)
    M.walk(s("10-01") + 0.2, s("10-01") + 3.0, (X_SIDE + 0.72, DOOR_Y - 0.05, 0.0))   # 錠の前へもどる
    M.at(s("10-01") + 3.2, face=-90.0)
    M.peer(s("10-02") + 0.2, 1.4)                                      # 錠の前のまま、近くでのぞく（歩かない）
    M.at(s("10-07") - 0.3, face=-90.0)                                 # もう 1 つの裏口は、カメラだけが寄る（まるロボは錠の前のまま。移動させない）
    M.surprise(t_o + 0.3)
    M.confused(w("11-01", "多い") - 0.3)


# ======================================================================== N：夜のお城（12）
LEDGE = (X_SIDE + 1.55, DOOR_Y + 1.7)


def b_night(cl):
    C_, gk = _castle_common(True)
    sh = shadow((X_SIDE + 2.6, DOOR_Y - 3.0, 0.0), face=0.0); track("shadow", sh.root, 1.5)
    t_a = w("12-02", "夜の裏口") - 0.2
    # 影がすっと現れて、裏口の前へ（音は小さく「すっ」）
    pop_in(sh.root, t_a - 0.4, 1.0, 0.6); ev(t_a - 0.3, "swish", 0.3, "shadow")
    key(sh.root, "location", t_a, (X_SIDE + 2.6, DOOR_Y - 3.0, 0.0)); key(sh.root, "location", t_a + 2.2, (X_SIDE + 0.95, DOOR_Y + 0.25, 0.0))
    key(sh.root, "rotation_euler", t_a + 1.6, (0, 0, R(0))); key(sh.root, "rotation_euler", t_a + 2.4, (0, 0, R(-90)))
    # 12-03：何かを取り出しかける → 12-04：本物の鍵（手の中）
    ky = key_obj((0, 0, 0), rot=(0, 0, 0), s=2.2, parent=sh.hand); ky.location = (0.0, -0.12, 0.0); ky.rotation_euler = (0, 0, R(-90))
    bpy.ops.object.light_add(type='POINT', location=(X_SIDE + 0.6, DOOR_Y - 0.6, 1.7)); kl = bpy.context.object; kl.data.shadow_soft_size = 0.2; kl.data.color = (1.0, 0.85, 0.6)
    for t_, e_ in ((-100.0, 0.0), (s("12-03") - 0.1, 0.0), (s("12-03") + 0.3, 18.0), (e("12-05"), 18.0), (e("12-05") + 0.5, 0.0)):
        kl.data.energy = e_; kl.data.keyframe_insert("energy", frame=f(t_))     # 鍵を照らす小さな明かり（夜で鍵が暗かった）
    track("key", ky, 0.0)
    pop_in(ky, w("12-04", "本物") - 0.4, 1.6, 0.3); ev(w("12-04", "本物") - 0.3, "jingle", 0.4, "key")
    t_up = s("12-03") + 0.3
    key(sh.arm, "rotation_euler", t_up, (R(-60), 0, 0)); key(sh.arm, "rotation_euler", t_up + 0.8, (R(-5), 0, 0))
    # 12-05：鍵を錠に差す → カチャ → 扉が開く → 影が中へ入っていく（12-07）
    t_in = w("12-05", "IDとパスワード") - 0.2
    key(sh.root, "location", t_in - 0.6, (X_SIDE + 0.95, DOOR_Y + 0.25, 0.0)); key(sh.root, "location", t_in + 0.4, (X_SIDE + 0.72, DOOR_Y + 0.4, 0.0))
    ev(t_in + 0.5, "click", 0.45, "lock")
    hg = C_["door"]
    t_op = t_in + 1.1
    key(hg, "rotation_euler", t_op, (0, 0, 0)); key(hg, "rotation_euler", t_op + 1.2, (0, 0, R(-95))); ev(t_op, "creak", 0.4, "door")
    t_go = s("12-07") + 0.6
    key(sh.root, "location", t_go, (X_SIDE + 0.72, DOOR_Y + 0.4, 0.0)); key(sh.root, "location", t_go + 1.0, (X_SIDE + 0.9, DOOR_Y, 0.0))
    key(sh.root, "location", t_go + 2.2, (X_SIDE - 1.2, DOOR_Y, 0.0)); ev(t_go, "swish", 0.25, "shadow")
    pop_out(sh.root, t_go + 2.1, 1.0, 0.2)
    # 12-08：3 つを並べる台（古いままの錠・かんたんな鍵・漏れた鍵）。12-09 で裏口がゆっくり閉まる
    cube(_stone(), (LEDGE[0], LEDGE[1], 0.4), (0.5, 1.3, 0.8))
    l3 = old_lock((LEDGE[0], LEDGE[1] - 0.42, 0.88), face=90.0, crack=False); track("i_lock", l3["root"], 0.05)
    k3 = key_obj((LEDGE[0] - 0.05, LEDGE[1] - 0.06, 0.82), rot=(0, 0, R(180)), simple=True, s=1.4); track("i_skey", k3, 0.02)
    k4 = key_obj((LEDGE[0] - 0.05, LEDGE[1] + 0.34, 0.82), rot=(0, 0, R(180)), s=1.4); track("i_key", k4, 0.02)
    for o_, t_ in ((l3["root"], w("12-08", "古い")), (k3, w("12-08", "かんたん")), (k4, w("12-08", "漏れた"))):
        pop_in(o_, t_ - 0.15, o_.scale[0] if o_.scale[0] > 0.01 else 1.0); ev(t_ - 0.15, "pop", 0.3)
    for o_, s_ in ((k3, 1.4), (k4, 1.4)):
        pass
    key(hg, "rotation_euler", w("12-09", "そこから"), (0, 0, R(-95))); key(hg, "rotation_euler", e("12-09") + 0.6, (0, 0, 0)); ev(e("12-09") + 0.5, "door_shut", 0.4, "door")
    # 門番さんは正面を見たまま（12-06）。夜の虫の声
    ev(cl_t0(), "crickets", 0.25, "")


def cl_t0():
    return CLOCK["T0"]


# ======================================================================== I：想像の場面（07-01。映画のような、正面の守りを破る泥棒。組み立てで青っぽくする）
def b_imag(cl):
    C_, gk = _castle_common(False)
    sh = shadow((0.3, -1.6, 0.0), face=0.0); track("shadow", sh.root, 1.4)
    # 浮かぶキーボードと画面（光る）
    kb = cube(mat("kb", "#1E2228", rough=0.5), (0.3, -2.05, 1.0), (0.5, 0.18, 0.03), bevel=0.004)
    scr = cube(glow_mat("monscr", "#3FD1FF", 3.0), (0.3, -2.4, 1.35), (0.7, 0.02, 0.42))
    key(sh.root, "rotation_euler", -100.0, (0, 0, R(180)), "CONSTANT")
    t0 = s("07-01")
    for k in range(int((e("07-01") - t0) / 0.16)):
        key(sh.arm, "rotation_euler", t0 + k * 0.16, (R(-20 + (8 if k % 2 else -8)), 0, 0))
    ev(t0 + 0.2, "typing", 0.35, "shadow")
    for i, hg in enumerate(C_["gate"]):
        sx = -1 if i == 0 else 1
        key(hg, "rotation_euler", w("07-01", "破ります") - 0.2, (0, 0, 0)); key(hg, "rotation_euler", w("07-01", "破ります") + 0.6, (0, 0, R(-75 * sx)))
    ev(w("07-01", "破ります") - 0.1, "thump", 0.4, "gate")


# ======================================================================== P09：小窓（家の机で、働く人がパソコンを開く。後ろ姿）
def b_pip_home(cl):
    room(window=True)
    p = person((2.0, 1.25, 0.0), 180.0, shirt="#5A7BA8", sit=True)
    lp = empty((2.0, 1.95, DESK_TOP));
    cube(mat("lap", "#2B2F36", rough=0.4, metal=0.5), (0, 0, 0.01), (0.34, 0.24, 0.02), parent=lp)
    hg = empty((0, 0.12, 0.02)); hg.parent = lp
    cube(mat("lap", "#2B2F36", rough=0.4, metal=0.5), (0, 0, 0.12), (0.34, 0.015, 0.24), parent=hg)
    cube(glow_mat("lapscr", "#CFE6FF", 2.0), (0, -0.009, 0.12), (0.31, 0.002, 0.2), parent=hg)
    key(hg, "rotation_euler", s("09-03") + 0.6, (R(80), 0, 0)); key(hg, "rotation_euler", s("09-03") + 1.6, (R(-12), 0, 0))


# ======================================================================== カット割り：(名前, 舞台, 切り替わる時刻, カメラ, 親)
#   同じ絵を 8 秒以上続けない。文の切れ目で、寄り・引き・横・まるロボを追う絵に替える
DX = X_SIDE
CUTS = [
    # 冒頭（家）
    ("A01", b_house, 0.0, C((-0.3, -1.5, 1.25), (1.9, 0.8, 0.25), 26, (0.0, -1.3, 1.1)), "A"),
    ("A01b", b_house, s("01-02"), C((2.35, -0.1, 0.55), (1.78, 0.62, 0.14), 26), "A"),
    ("A01c", b_house, s("01-03"), C((2.55, 0.2, 0.45), (1.8, 0.64, 0.15), 30), "A"),
    ("A02", b_house, s("02-01"), C((1.97, 0.4, 0.36), (1.95, 0.65, 0.0), 32), "A"),
    ("A02b", b_house, s("02-02"), C((2.7, 0.3, 0.5), (1.8, 0.62, 0.2), 30), "A"),
    ("A02c", b_house, s("02-05"), C((2.8, 0.25, 0.55), (1.8, 0.62, 0.18), 30, (2.65, 0.3, 0.5)), "A"),
    ("A03", b_house, s("03-01"), C((2.6, -0.05, 0.55), (1.72, 0.62, 0.2), 28), "A"),      # きょろきょろが見える寄り（v1：遠くて首を振るのが見えなかった）
    ("A03b", b_house, s("03-02"), C((-0.5, -1.4, 1.2), (1.5, 0.6, 0.3), 30), "A"),
    ("A03c", b_house, s("03-03"), C((0.7, 0.62, 0.55), (3.0, 0.4, 0.55), 22), "A"),
    ("A04", b_house, s("04-01"), C((1.9, 0.4, 0.9), (3.4, 0.4, 1.5), 24, (2.0, 0.4, 0.95)), "A"),
    ("A04b", b_house, s("04-02"), C((1.97, 0.4, 0.36), (1.95, 0.65, 0.0), 32), "A"),
    ("A04c", b_house, s("04-03"), C((1.9, 0.4, 0.9), (3.4, 0.4, 1.5), 24), "A"),
    ("A04d", b_house, s("04-04"), C((0.7, 0.62, 0.55), (3.0, 0.4, 0.55), 22, (0.9, 0.62, 0.55)), "A"),
    ("T05", b_table, s("05-01"), C((0.0, -1.25, TZ + 0.45), (0.0, 0.0, TZ + 0.12), 34), "T"),
    ("T05b", b_table, s("05-02"), C((-0.36, -0.8, TZ + 0.3), (-0.36, -0.02, TZ + 0.12), 36), "T"),
    ("T05c", b_table, s("05-03"), C((0.0, -0.62, TZ + 0.22), (0.0, -0.02, TZ + 0.12), 40), "T"),
    ("T05d", b_table, s("05-04"), C((0.33, -0.55, TZ + 0.2), (0.33, -0.03, TZ + 0.08), 42), "T"),
    ("T05e", b_table, s("05-05"), C((0.0, -1.1, TZ + 0.45), (0.0, 0.05, TZ + 0.14), 34, (-0.3, -0.45, TZ + 0.2), (-0.36, -0.02, TZ + 0.12), d=4.5), "T"),
    ("P02", b_table, s("02-03") - 0.2, C((-0.1, -0.85, TZ + 0.35), (-0.25, -0.2, TZ + 0.1), 36), "T"),
    # 1章（昼のお城）
    ("B06", b_castle, s("06-01"), C((-4.5, -15.0, 3.2), (0.4, 0.0, 2.8), 30, (-4.0, -14.0, 3.0)), "B"),
    ("B06b", b_castle, s("06-02"), lambda t0: cam((0.4, -4.4, 0.45), (0.0, 0.0, 1.0), 22, t0, t0 + 3.5, (0.3, -4.2, 0.5), (0.0, 0.5, 4.2))),
    ("B06c", b_castle, s("06-03"), C((0.6, -3.4, 1.7), (1.75, -1.1, 1.5), 34), "B"),
    ("B06d", b_castle, s("06-04"), C((-3.2, -3.6, 1.6), (0.0, -1.0, 1.6), 30), "B"),
    ("B06e", b_castle, s("06-05"), C((-3.0, -1.2, 1.0), (0.0, -0.9, 0.8), 30), "B"),
    ("B06f", b_castle, s("06-07"), C((-4.2, -1.6, 1.2), (0.0, -1.0, 0.7), 28), "B"),
    ("B06g", b_castle, s("06-09"), C((0.5, -7.5, 1.6), (0.6, -1.0, 1.2), 28), "B"),
    ("I07", b_imag, s("07-01"), C((2.6, -5.2, 2.0), (0.3, -1.4, 1.6), 28), "I"),
    ("B07", b_castle, s("07-02"), C((0.5, -7.5, 1.6), (0.6, -1.0, 1.2), 28), "B"),
    ("B07b", b_castle, s("07-03"), lambda t0: F((2.0, -0.6, 0.7), 30), "B"),
    ("B08", b_castle, s("08-01"), C((3.0, -10.0, 3.5), (3.0, 0.0, 2.0), 26, (13.5, 1.0, 3.0), (DX, DOOR_Y, 1.0), d=4.5), "B"),
    ("B08b", b_castle, s("08-02"), C((DX + 2.6, DOOR_Y - 1.2, 1.0), (DX, DOOR_Y, 0.8), 30), "B"),
    ("B08c", b_castle, s("08-03"), C((8.0, -6.0, 1.5), (0.0, -0.9, 0.6), 40), "B"),       # 角の塔の外から、門の前のまるロボ（v1：錠のアップになっていた）
    ("B09", b_castle, s("09-01") + 0.55, C((DX + 3.2, DOOR_Y - 2.4, 1.2), (DX + 0.6, DOOR_Y, 0.8), 30), "B"),
    ("B09b", b_castle, s("09-02"), lambda t0: F((2.3, -1.5, 0.75), 30), "B"),
    ("B09c", b_castle, s("09-04"), C((DX + 12.0, DOOR_Y - 6.0, 9.0), (DX, DOOR_Y, 0.5), 30), "B"),
    ("B09d", b_castle, s("09-05"), C((DX + 2.0, DOOR_Y - 1.8, 1.1), (DX + 0.6, DOOR_Y + 0.2, 0.8), 30, (DX + 1.9, DOOR_Y - 1.6, 1.05)), "B"),
    ("B10", b_castle, s("10-01"), C((DX + 2.8, DOOR_Y + 0.6, 1.3), (DX, DOOR_Y, 0.7), 30), "B"),
    ("B10b", b_castle, s("10-02"), C((DX + 0.75, DOOR_Y + 0.6, 0.95), (DX + 0.1, DOOR_Y + DOOR_W / 2 - 0.14, 0.82), 36), "B"),
    ("B10c", b_castle, s("10-03"), C((DX + 2.4, DOOR_Y + 2.6, 1.4), (DX + 0.3, DOOR_Y + 0.5, 0.6), 30), "B"),
    ("B10d", b_castle, s("10-06"), C((DX + 0.75, DOOR_Y + 0.6, 0.95), (DX + 0.1, DOOR_Y + DOOR_W / 2 - 0.14, 0.82), 36), "B"),
    ("B10e", b_castle, s("10-07"), C((DX + 2.2, DOOR2_Y - 1.6, 1.2), (DX + 0.2, DOOR2_Y, 0.8), 30), "B"),
    ("B11", b_castle, s("11-01"), C((DX + 6.0, DOOR_Y - 4.0, 2.4), (DX, DOOR_Y, 1.0), 30, (DX + 5.6, DOOR_Y - 3.6, 2.3)), "B"),
    ("B11b", b_castle, s("11-10"), C((-4.5, -15.0, 3.2), (0.4, 0.0, 2.8), 30, (-4.2, -14.4, 3.1)), "B"),
    # 12（夜のお城）
    ("N12", b_night, s("12-01") + 0.6, C((DX + 5.0, DOOR_Y - 5.0, 2.2), (DX + 0.6, DOOR_Y, 0.9), 28), "N"),
    ("N12b", b_night, s("12-03"), C((DX + 0.6, DOOR_Y - 1.3, 1.3), (DX + 0.35, DOOR_Y + 0.15, 1.1), 32), "N"),      # 横から：手と鍵が体に隠れない（v1：鍵が見えなかった）
    ("N12c", b_night, s("12-05"), C((DX + 1.7, DOOR_Y - 0.6, 1.1), (DX + 0.2, DOOR_Y + 0.3, 0.85), 32), "N"),
    ("N12d", b_night, s("12-06"), C((0.6, -4.4, 1.6), (1.75, -1.1, 1.5), 34), "N"),
    ("N12e", b_night, s("12-07"), C((DX + 3.6, DOOR_Y - 1.8, 1.3), (DX + 0.4, DOOR_Y, 0.9), 30), "N"),
    ("N12f", b_night, s("12-08"), C((LEDGE[0] + 1.4, LEDGE[1] - 0.2, 1.25), (LEDGE[0], LEDGE[1] - 0.05, 0.85), 34), "N"),
    ("N12g", b_night, s("12-09"), C((LEDGE[0] + 1.6, LEDGE[1] - 0.6, 1.3), (DX, DOOR_Y + 0.5, 0.8), 30, (DX + 4.0, DOOR_Y - 1.6, 1.8)), "N"),
    ("P09", b_pip_home, s("09-03") - 0.2, C((2.0, 0.1, 1.35), (2.0, 1.9, 0.95), 30), "A"),
]
for i_, c_ in enumerate(CUTS):
    if len(c_) == 4: CUTS[i_] = c_ + ("B",)
PIP_ONLY = {"P02", "P09"}
END_T = e("12-09") + 1.5
CUTS.sort(key=lambda c: c[2])
_main = [c for c in CUTS if c[0] not in PIP_ONLY]
CLIPS = {}
for i, (nm, fn, tc, cm, par) in enumerate(_main):
    t0 = max(0.0, tc - 0.1)
    t1 = (_main[i + 1][2] + 0.75) if i + 1 < len(_main) else END_T
    CLIPS[nm] = (fn, t0, t1, cm, par)
CLIPS["P02"] = (b_table, s("02-03") - 0.2, e("02-03") + 0.4, [c for c in CUTS if c[0] == "P02"][0][3], "T")
CLIPS["P09"] = (b_pip_home, s("09-03") - 0.2, e("09-03") + 0.4, [c for c in CUTS if c[0] == "P09"][0][3], "A")


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
