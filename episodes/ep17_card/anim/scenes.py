# 17本目（カード）：3D の場面を声の時刻に合わせて動かして描く（9本目の scenes.py と同じ作り方）
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 4] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   PC の本番：... -- <クリップ> <出力> --samples 24 --res 1920 1080 --frames 0 99 --gpu --video --fast
#   舞台：A＝まるロボの家（b_house。S01 だけ夜 b_night）／C＝ネットのお店（b_shop）／I＝想像の場面（b_imag14・b_pip*。組み立てで青っぽくする）
#   舞台の組み立て（b_*）は、その舞台の動きを全部作り、カメラだけをクリップごとに選ぶ。絵コンテ表：../絵コンテ_v1.md
#   決まり：3D の中に字を書かない／まるロボは喋らない・本物の体を marumotion の予定で動かす（maru17.py）／動きは言い終えてから
#   この版は冒頭・1章・2章（S01〜S14）。§2.6：章ごとに動く下書きで OK をもらう
import os, sys, math, json
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.read_factory_settings(use_empty=True)
TEX = os.environ.get("TEX17") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "tex17")
exec(open(os.path.join(KIT_HERE, "kit17.py"), encoding="utf-8").read())
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
exec(open(os.path.join(_K7, "maru17.py"), encoding="utf-8").read())


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


# ======================================================================== A：まるロボの家（冒頭〜2章の前半 S01〜S12）
#   家の中のまるロボは 0.40 倍（小さなロボ）。歩く速さは約 0.4 m/秒なので、置き場所を近くにまとめる（SKILL §5）
PH = (1.42, 0.98, 0.0)          # 床に置いたスマホ（画面が上）。金庫の近く（走って 1 秒ほど）
HOUSE_S = 0.40
SAFE = (0.8, 1.85, 0.0)          # 金庫（前＝−y。とびらの面は y=1.64）
SAFE_FRONT = (0.8, 1.12, 0.0)    # 金庫の前に立つ所（とびらが開いても当たらない）
HOME = (1.16, 0.55, 0.0)
PH_SPOT = (1.16, 0.98, 0.0)      # スマホをのぞく所
RACK = (0.12, 1.32, 0.0)         # 帽子かけ
UNDER_RACK = (0.34, 1.20, 0.0)
TRASH = (1.95, 1.45, 0.0)
TRASH_FRONT = (1.95, 1.08, 0.0)
WIN_SPOT = (2.50, 0.30, 0.0)     # 窓の下（窓は右のかべ x=3、y −1.05〜0.65。ベッドは y −0.35 より手前なので、窓の北の端に寄せる）
ENV = (0.50, 0.80, 0.0)          # S01 の封筒（まるロボの左手前）
CARD_FLOOR = (0.8, 1.40, 0.0)    # 09-01 で金庫から出て、床に落ちるカード（まるロボと金庫の間）
TILE_C = (0.8, 1.48, 0.70)       # タイルの列のまん中（前＝−y。金庫の前の宙）
TILE_C2 = (0.8, 1.48, 0.90)      # 紫のカードの列（11-06）
TWR_B = (6.2, -0.45, 0.0)        # 窓の外の遠くの塔（青い旗）。空の板（x=9）より手前に置く（試しの絵：板のうしろで見えなかった）
TWR_P = (6.6, 0.45, 0.0)         # 紫の旗の塔（11-06）
TOWN_X = 3.0


def town_view17(x1=TOWN_X, night=False):
    """窓の外：遠くの町の建物と、カードの会社の塔（青い旗。2章で指す）"""
    random.seed(7)
    for k in range(7):
        y = -3.2 + k * 1.05; h = random.uniform(2.6, 3.8)
        if abs(y - (-0.35)) < 0.9: continue
        o = cube(mat("townb%d" % k, random.choice(["#B9C3CF", "#C7CED8", "#AEB9C6"]), rough=0.8), (x1 + 6.4, y, h / 2 - 0.3), (0.4, 0.9, h)); o.visible_shadow = False
    tb = tower(TWR_B, flag=BLUE_C, s=0.75, night=night)      # 木より大きく（試しの絵：木にかくれて屋根の先しか見えなかった）
    for o in [tb["root"]] + list(tb["root"].children_recursive):
        if hasattr(o, "visible_shadow"): o.visible_shadow = False
    return tb


def _house_common(night=False):
    room(window=True)
    tb = town_view17(night=night)
    sf = safe(SAFE, 0.0); track("safe", sf["root"], 0.3); track("safe_in", sf["shelf"], 0.03)
    hat_rack(RACK); tr = trash_can(TRASH); track("trash", tr["root"], 0.25)
    if night:
        # 夜（試しの絵の点検：昼の明るさのままだった）：日の光を消し、部屋の照明をほぼ消して、机の電気スタンドだけ明るく。
        #   窓の外の空も暗くし、月の青い光を少し。まるロボと金庫のあたりは、スタンドの光で見える
        for l_, e_ in LIGHTS:
            l_.data.energy = e_ * (1.6 if (l_.type == 'POINT' and e_ < 40) else 0.04)
        for o_ in bpy.data.objects:
            if o_.type == 'LIGHT' and o_.data.type == 'SUN': o_.data.energy = 0.0
        for n_, s_ in GLOWS_W: n_.inputs["Strength"].default_value = s_ * 0.05
        bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.02
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 5)); mo = bpy.context.object; mo.rotation_euler = (R(60), 0, R(70)); mo.data.energy = 0.35; mo.data.color = (0.62, 0.72, 1.0)
        bpy.ops.object.light_add(type='POINT', location=(0.9, 0.9, 0.9)); fl = bpy.context.object; fl.data.energy = 6.0; fl.data.color = (1.0, 0.85, 0.65); fl.data.shadow_soft_size = 0.4
    return sf, tr, tb


def b_night(cl):
    """S01：夜。封筒からカードが出て、まるロボが頭に載せて金庫へ運び、しまってダイヤルを回す"""
    sf, tr, tb = _house_common(night=True)
    envelope(ENV, 20.0)
    M = MaruR((0.80, 0.66, 0.0), face=180.0, s=HOUSE_S); track("maru", M.body, 0.25); track("maru_top", M.body, 0.32)     # 金庫に向いて立つ（歩くのはまっすぐ前へ 0.46 m。向きを変えない）
    t_card = w("01-01", "1枚") - 0.1
    # カード：封筒の上に出る → まるロボの頭に載る（胴の子。胴の中の寸法は大きさ 1 のときの寸法）→ 01-03 で金庫の棚へ
    cfree = card_obj((ENV[0], ENV[1], 0.02), (0, 0, R(20))); track("card", cfree, 0.0)
    key(cfree, "location", -100.0, (ENV[0], ENV[1], 0.0), "CONSTANT"); key(cfree, "location", t_card, (ENV[0], ENV[1], 0.0))
    key(cfree, "location", t_card + 0.6, (ENV[0] - 0.05, ENV[1], 0.18)); ev(t_card, "swish", 0.25, "card")
    hide_key(cfree, -100.0, True); hide_key(cfree, t_card, False); hide_key(cfree, t_card + 1.2, True)
    for o in cfree.children: hide_key(o, -100.0, True); hide_key(o, t_card, False); hide_key(o, t_card + 1.2, True)
    hc = empty((0, 0, 0)); hc.parent = M.torso; hc.location = (0, 0.0, 0.47)
    chead = card_obj((0, 0, 0), (0, 0, R(90)), w=0.17 / HOUSE_S, parent=hc)
    t_in = e("01-03") - 0.5                 # 棚へ入れる時刻（金庫の前に着いて、向き終わってから）
    for o in [chead] + list(chead.children): hide_key(o, -100.0, True); hide_key(o, t_card + 1.2, False); hide_key(o, t_in, True)
    cshelf = card_obj((0, 0, 0), (0, 0, 0), parent=sf["shelf"]); track("card_safe", cshelf, 0.0)
    for o in [cshelf] + list(cshelf.children): hide_key(o, -100.0, True); hide_key(o, t_in, False)
    key(cshelf, "location", t_in, (0, -0.30, 0.02)); key(cshelf, "location", t_in + 0.5, (0, 0, 0)); ev(t_in, "slide", 0.3, "safe")
    # まるロボ：封筒の前 → カードが頭に（01-01）→ うれしくて跳ねる（01-02）→ 金庫へ歩く（01-03）→ とびらを閉めてダイヤル（01-04）→ 得意顔
    M.at(t_card + 0.2, face=210.0, look=-15)                             # 左の封筒を見る
    M.at(t_card + 1.6, face=180.0, look=10)
    M.hops(w("01-02", "はじめて") + 0.1, n=2); ev(w("01-02", "はじめて") + 0.1, "beep_happy", 0.35, "maru_c")
    M.walk(e("01-02") + 0.3, s("01-03") + 2.4, SAFE_FRONT)
    M.push(t_in - 0.2, 0.15)
    safe_open(sf, -100.0, 0.01); key(sf["door"], "rotation_euler", -50.0, (0, 0, R(-105)), "CONSTANT")
    t_cl = w("01-04", "閉めて") - 0.1
    safe_close(sf, t_cl, 0.5); ev(t_cl + 0.5, "click", 0.4, "safe")
    safe_dial(sf, w("01-04", "ダイヤル") - 0.1, 1.5, 1.3); ev(w("01-04", "ダイヤル"), "dial", 0.35, "safe")
    M.at(w("01-04", "ひと安心") - 0.6, face=20.0)                          # ふり向いて、見る人のほうへ得意顔（試しの絵：背中しか見えなかった）
    M.blink(w("01-04", "ひと安心"))
    M.nod(w("01-04", "ひと安心") + 0.1, n=1)


def b_house(cl):
    """S02〜S12：朝の家。知らせ → 金庫 → 探偵の帽子 → 3 か所を調べる → ころん → カードを出す → 数字のタイル"""
    sf, tr, tb = _house_common()
    ph, scr = phone_seq(PH, 90.0, [(0.0, os.path.join(TEX, "ph_home.png")), (w("02-01", "ブルッ") - 0.2, os.path.join(TEX, "ph_notice.png"))], glow=1.6)
    track("phone", ph, 0.0)
    t_n = w("02-01", "ブルッ") - 0.25
    ev(t_n, "buzz", 0.45, "phone")
    for k in range(7): key(ph, "rotation_euler", t_n + k * 0.06, (0, 0, R(90 + (3 if k % 2 else -3))))
    key(ph, "rotation_euler", t_n + 0.45, (0, 0, R(90)))
    cshelf = card_obj((0, 0, 0), (0, 0, 0), parent=sf["shelf"]); track("card_safe", cshelf, 0.0)
    M = MaruR(HOME, face=180.0, s=HOUSE_S); track("maru", M.body, 0.25); track("maru_top", M.body, 0.32)
    t_hat = w("04-01", "帽子") + 0.2
    hat_on_maru(M, t_hat, RACK, 0.86)
    # 02：知らせ → スマホへ → え？ → 金庫へ走る → 開ける → 中にある → 首をかしげる
    M.act(t_n + 0.25, "wake")
    M.walk(t_n + 1.4, s("02-02") + 1.9, PH_SPOT)
    M.at(s("02-02") + 2.0, face=90.0, look=-25)
    M.surprise(s("02-04") + 0.15)
    M.at(e("02-04") - 0.3, look=0)
    M.walk(e("02-04") - 0.5, e("02-05") - 0.3, SAFE_FRONT)
    M.at(e("02-05") - 0.2, face=180.0)
    t_op = s("02-06") - 0.1                                                # 金庫のほうを向き終わってから開ける
    safe_open(sf, t_op, 0.7); ev(t_op, "click", 0.4, "safe"); ev(t_op + 0.2, "creak_s", 0.3, "safe")
    M.peer(s("02-06") + 0.8, 1.4)
    M.at(s("02-07") + 0.1, face=90.0)                                       # 右へ 90 度向いて、首をかしげる（斜め前のカメラに顔を見せる。半回転は 3 秒以上かかり声に遅れる）
    M.confused(s("02-07") + 2.0)
    safe_close(sf, e("02-08") + 0.2, 0.5); ev(e("02-08") + 0.7, "click", 0.3, "safe")
    M.at(s("03-03") + 0.2, look=-10)
    M.at(s("03-05") + 0.2, face=-90.0)                                     # 帽子かけを見る
    # 04：帽子かけの下へ → 跳ぶ → 帽子が頭に → 得意顔 → 見回す
    M.walk(s("04-01") - 0.8, w("04-01", "帽子") - 0.5, UNDER_RACK)
    M.hop(w("04-01", "帽子") - 0.35, h=0.15, d=0.45); ev(t_hat, "puff", 0.4, "maru_c")
    M.at(s("04-02") + 0.1, face=-30.0)
    M.blink(w("04-02", "探偵") + 0.2)
    M.look_around(s("04-03") + 0.2)
    # 04-04：3 か所に丸い光（窓・ゴミ箱・スマホ）
    for k_, (pp, nm) in enumerate((((2.92, -0.2, 1.45), "spot1"), ((TRASH[0], TRASH[1], 0.32), "spot2"), ((PH[0], PH[1], 0.06), "spot3"))):
        sp = sphere(glow_mat("spotglow", "#FFD24A", 3.0), pp, 0.02, seg=24); track(nm, sp, 0.0)      # 小さく（試しの絵：大きな白い光の玉に見えた。番号の札は 2D で出す）
        t_ = w("04-04", "1つずつ") + 0.1 + 0.55 * k_
        pop_in(sp, t_, 1.0, 0.3); ev(t_, "pi", 0.3, nm); pop_out(sp, w("08-04", "どこからも"), 1.0, 0.4)
    # 05：窓へ歩いて、のぞく（窓のまわり・すき間）→ 首を振る
    M.walk(s("04-04") + 0.3, s("05-02") + 1.6, WIN_SPOT)
    M.at(s("05-02") + 1.7, face=90.0)
    M.peer(s("05-02") + 2.6, 1.2)
    M.at(e("05-02") - 0.4, look=20)
    M.at(e("05-02") - 0.6, face=0.0)                                       # 窓から右へ 90 度ふり向いて、首を横に振る（斜め前のカメラ。部屋の手前の何もない所は映さない）
    M.shake(w("05-03", "ありません") + 0.5); ev(w("05-03", "ありません") + 0.6, "beep_no", 0.35, "maru_c")
    # 06：ゴミ箱の前へ → 押して倒す → 紙くずが広がる → 封筒をのぞく → 首を振る
    M.walk(e("05-03") + 0.1, s("06-01") + 2.4, TRASH_FRONT)
    M.at(s("06-01") + 2.5, face=180.0)
    t_push = w("06-02", "ひっくり返して") + 0.3
    M.push(t_push - 0.25, 0.25)
    key(tr["root"], "rotation_euler", t_push, (0, 0, 0)); key(tr["root"], "rotation_euler", t_push + 0.35, (R(-88), 0, 0)); ev(t_push + 0.3, "rustle", 0.5, "trash")
    random.seed(17)
    for k_, p_ in enumerate(tr["papers"]):
        dx, dy = random.uniform(-0.3, 0.3), random.uniform(0.25, 0.55)
        key(p_, "location", t_push + 0.1, (0.0, 0.0, 0.18)); key(p_, "location", t_push + 0.6 + 0.05 * k_, (dx, dy, 0.03))
    env2 = envelope((TRASH[0] + 0.12, TRASH[1] + 0.42, 0.0), -30.0)
    for o in [env2] + list(env2.children): hide_key(o, -100.0, True); hide_key(o, t_push + 0.5, False)
    M.peer(w("06-02", "封筒") + 0.2, 1.3)
    M.at(s("06-03") + 0.1, face=90.0)                                       # 右へ 90 度向いて、首を横に振る（斜め前のカメラ）
    M.shake(w("06-03", "どこにも") + 1.6); ev(w("06-03", "どこにも") + 1.7, "beep_no", 0.35, "maru_c")
    # 07：スマホのほうを向いて、首を横に振る（使っていない）
    M.at(s("07-01") + 1.2, face=-75.0)                                    # スマホ（左の手前）のほうを向く
    M.shake(w("07-02", "首を") - 0.2); ev(w("07-02", "首を"), "beep_no", 0.35, "maru_c")
    # 08：ころん → 目の光が下がる → 「？」
    t_t = w("08-02", "ころん") - 0.1
    M.act(t_t, "tumble_back", lift=0.0); ev(t_t + 0.35, "boing", 0.35, "maru_c")
    M.glow(s("08-03") + 0.3, 0.35, 0.6)
    M.glow(s("09-01") - 0.3, 0.9, 0.4)
    # 09：起き上がって金庫の前へ → 押すと開く → カードがすべり出て床へ（まるロボと金庫の間）→ とびらが閉まる
    M.act(w("08-05", "いったい") - 0.2, "get_up")
    M.walk(e("08-05") + 0.1, w("09-01", "取り出しました") - 0.9, SAFE_FRONT)
    M.at(w("09-01", "取り出しました") - 0.8, face=180.0)
    t_o2 = e("09-01")                                                      # 金庫のほうを向き終わってから押して開ける
    M.push(t_o2 - 0.25, 0.15)
    safe_open(sf, t_o2, 0.6); ev(t_o2, "click", 0.4, "safe")
    key(cshelf, "location", t_o2 + 0.5, (0, 0, 0)); key(cshelf, "location", t_o2 + 1.2, (0, -0.30, 0.02))
    hide_key(cshelf, t_o2 + 1.3, True)
    for o in cshelf.children: hide_key(o, -100.0, False); hide_key(o, t_o2 + 1.3, True)
    cf = card_obj((CARD_FLOOR[0], CARD_FLOOR[1] + 0.1, 0.24), (0, 0, R(90))); track("card_floor", cf, 0.0)      # 横の寄り（東から）で番号がさかさにならない向き
    for o in [cf] + list(cf.children): hide_key(o, -100.0, True); hide_key(o, t_o2 + 1.3, False)
    key(cf, "location", t_o2 + 1.3, (CARD_FLOOR[0], CARD_FLOOR[1] + 0.1, 0.24)); key(cf, "location", t_o2 + 1.8, (CARD_FLOOR[0], CARD_FLOOR[1], 0.003)); ev(t_o2 + 1.8, "tap", 0.3, "card_floor")
    safe_close(sf, t_o2 + 2.2, 0.5); ev(t_o2 + 2.7, "click", 0.3, "safe")
    M.peer(t_o2 + 2.0, 1.2)
    # 10：虫めがねでのぞく → タイルが浮かぶ
    M.peer(s("10-01") + 0.2, 1.4)
    base, tl = tile_row(TILE_C, face=0.0)
    for k_, d_ in enumerate(tl):
        r_ = d_["root"]; p1 = tuple(r_.location)
        track("tile%d" % k_, r_, 0.0)
        t_ = w("10-02", "数字が") + 0.15 * k_
        key(r_, "location", -100.0, (CARD_FLOOR[0] - TILE_C[0] + (k_ - 3.5) * 0.02, -(CARD_FLOOR[1] - TILE_C[1]), -TILE_C[2]), "CONSTANT")
        key(r_, "location", t_, (CARD_FLOOR[0] - TILE_C[0] + (k_ - 3.5) * 0.02, -(CARD_FLOOR[1] - TILE_C[1]), -TILE_C[2]))
        key(r_, "location", t_ + 0.8, p1)
        key(r_, "scale", -100.0, (0.15, 0.15, 0.15), "CONSTANT"); key(r_, "scale", t_, (0.15, 0.15, 0.15)); key(r_, "scale", t_ + 0.8, (1, 1, 1))
    ev(w("10-02", "数字が"), "float", 0.4, "tile3")
    M.at(e("10-02") + 0.2, look=20)
    M.at(s("10-06") + 0.2, look=22)
    # 11：はじめの 2 枚が青く → 窓の外の塔 → 青い光の点が塔へ → 紫のカードの列
    for k_ in (0, 1): tile_color(tl[k_], w("11-01", "はじめ") - 0.1, BLUE_C)
    ev(w("11-01", "はじめ"), "pi", 0.35, "tile0")
    dot = sphere(glow_mat("dotblue", BLUE_C, 12.0), (0, 0, 0), 0.035, seg=16); track("dot", dot, 0.0)
    t_d = w("11-05", "同じ塔") - 0.3
    p0 = (TILE_C[0] - 0.5, TILE_C[1] - 0.02, TILE_C[2]); p1 = (TWR_B[0] - 0.7, TWR_B[1], 2.2)
    key(dot, "location", -100.0, p0, "CONSTANT"); key(dot, "location", t_d, p0); key(dot, "location", t_d + 1.4, p1)
    hide_key(dot, -100.0, True); hide_key(dot, t_d, False); hide_key(dot, t_d + 1.5, True)
    ev(t_d, "whoosh", 0.3, "dot")
    base2, tl2 = tile_row(TILE_C2, face=0.0)
    t_p = w("11-06", "別の") - 0.2
    pop_in(base2, t_p, 1.0, 0.35); ev(t_p, "pop", 0.35, "tile3")
    for k_ in (0, 1): tile_color(tl2[k_], t_p + 0.5, PURP_C)
    pop_out(base2, s("12-01") - 0.1, 1.0, 0.3)
    tp = tower(TWR_P, flag=PURP_C, s=0.75)
    pop_in(tp["root"], t_p + 0.4, 0.75, 0.4)
    # 12：青の 2 枚は消え、最後の 1 枚が橙 → 前の 7 枚から光が集まる
    for k_ in (0, 1): tile_off(tl[k_], s("12-01") - 0.1)
    tile_color(tl[7], w("12-01", "最後") - 0.1, ORANGE_C); ev(w("12-01", "最後"), "pi", 0.35, "tile7")
    M.at(s("12-02") + 0.3, look=10); M.confused(w("12-02", "役目") - 0.2)
    t_g = w("12-03", "前に") + 0.1
    for k_ in range(7):
        g = sphere(glow_mat("gath", "#FFF2C8", 10.0), (0, 0, 0), 0.022, seg=12)
        a_ = tl[k_]["root"].location; q0 = (TILE_C[0] + a_[0], TILE_C[1] - 0.03, TILE_C[2] + 0.07); q1 = (TILE_C[0] + tl[7]["root"].location[0], TILE_C[1] - 0.03, TILE_C[2])
        key(g, "location", -100.0, q0, "CONSTANT"); key(g, "location", t_g + 0.12 * k_, q0); key(g, "location", t_g + 0.12 * k_ + 1.1, q1)
        hide_key(g, -100.0, True); hide_key(g, t_g + 0.12 * k_, False); hide_key(g, t_g + 0.12 * k_ + 1.15, True)
    ev(t_g, "shimmer", 0.3, "tile7")
    M.nod(s("12-06") + 0.4, n=1)


# ======================================================================== C：ネットのお店（S13〜S14）
SHOP_S = 0.72
TWR_SHOP = (10.0, 9.0, 0.0)
SHOP_TILE_C = (0.0, 2.15, 1.95)     # レジの奥の宙（門の外からも、門の中に見える）


def b_shop(cl):
    S_ = shop(); track("register", S_["screen"], 0.0); track("gate", S_["lamp"], 0.0)
    tw = tower(TWR_SHOP, flag=BLUE_C, s=1.2); track("tower", tw["top"], 0.0)
    keys = S_["keys"]
    # 画面：打つたびに 1 つずつ入る → 7 つ目をまちがえる → 赤 → 打ち直す → 緑
    seq = []
    t3 = w("13-03", "1けたずつ") - 0.1
    press = []
    for k_ in range(6): press.append((t3 + 0.55 * k_, NUM[k_], "reg_%d" % (k_ + 1)))
    t4 = w("13-04", "となり") - 0.2
    press.append((t4, "5", "reg_w7"))
    press.append((s("13-05") + 0.2, NUM[7], "reg_w8"))
    states = [(0.0, "reg_0")] + [(t + 0.08, img) for t, _, img in press]
    t_bad = s("13-06") - 0.05
    states.append((t_bad, "reg_wrong"))
    t10 = w("13-10", "打ち直す") - 0.3
    re_ = [(t10, "reg_6"), (t10 + 0.5, "reg_7"), (t10 + 1.0, "reg_8")]
    for t, nm in re_: press.append((t, NUM[int(nm.split("_")[1]) - 1], nm))
    states += [(t + 0.08, nm) for t, nm in re_]
    t_ok = s("13-11") + 0.1
    states.append((t_ok, "reg_ok"))
    states.append((s("14-01") + 0.3, "reg_nocheck"))
    states.append((s("14-04") - 0.1, "reg_wrong"))
    states.append((e("14-04") + 0.5, "reg_0"))
    reg_screen(S_["screen"], sorted(states))
    for t, ch, _ in press:
        press_key(keys[ch], t); ev(t + 0.05, "key", 0.3, "register")
    ev(t_bad + 0.05, "buzz_ng", 0.45, "register"); ev(t_ok + 0.05, "chime_ok", 0.45, "register")
    ev(s("14-04") + 0.05, "buzz_ng", 0.3, "register")
    # まるロボ（0.72 倍）：門の前 → 中へ歩く → キーの前で押す → むっ → 打ち直す → うなずく
    M = MaruR((0.0, -1.3, 0.0), face=180.0, s=SHOP_S); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    M.at(s("13-01") + 0.3, look=12)
    M.walk(s("13-02") + 0.1, s("13-02") + 3.0, (0.0, 0.62, 0.0))
    M.at(s("13-02") + 3.1, face=180.0)
    for t, _, _ in press: M.push(t - 0.12, 0.12)
    M.surprise(t_bad + 0.1)
    M.at(s("13-08") + 0.2, face=150.0)
    M.blink(w("13-08", "むっと") - 0.1, d=0.5); ev(w("13-08", "むっと"), "beep_hmph", 0.35, "maru_c")
    M.at(t10 - 0.4, face=180.0)
    M.hops(t_ok + 0.3, n=2)
    M.at(e("14-04") + 0.3, face=180.0, look=0)
    M.at(s("14-05") + 0.2, face=180.0, look=22)                         # レジの奥の宙のタイルを見上げる（歩かない）
    M.nod(w("14-08", "決まり") + 0.2, n=2)
    # 14-05〜：門の上の宙にタイルの列
    base, tl = tile_row(SHOP_TILE_C, face=0.0, size=0.2, gap=0.04)
    for k_, d_ in enumerate(tl): track("stile%d" % k_, d_["root"], 0.0)
    pop_in(base, s("14-05") - 0.4, 1.0, 0.5); ev(s("14-05") - 0.3, "float", 0.35, "stile3")
    for k_ in range(2, 7): tile_color(tl[k_], w("14-06", "1人1人") - 0.1, "#FFFFFF", 4.0)
    ev(w("14-06", "1人1人"), "pi", 0.3, "stile4")
    for k_ in range(2, 7): tile_off(tl[k_], s("14-07") - 0.05, s0=4.0)
    for k_ in (0, 1): tile_color(tl[k_], w("14-07", "会社") - 0.1, BLUE_C)
    for k_ in range(2, 7): tile_color(tl[k_], w("14-07", "1人1人") - 0.1, "#FFFFFF", 4.0)
    tile_color(tl[7], w("14-07", "検算") - 0.1, ORANGE_C)
    for wd in ("会社", "1人1人", "検算"): ev(w("14-07", wd), "pi", 0.3, "stile4")
    # 14-09：空が少し暗く → 14-10：門の内側の奥に、黒い影がうっすら
    bg = bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"]
    for t, v in ((s("14-09") - 0.1, 0.9), (s("14-09") + 1.2, 0.35)):
        bg.default_value = v; bg.keyframe_insert("default_value", frame=f(t))
    sh = shadow((0.0, 3.7, 0.0), face=0.0, s=1.0); track("shadow", sh.root, 1.5)
    pop_in(sh.root, w("14-10", "悪いこと") - 0.2, 1.0, 1.2); ev(w("14-10", "悪いこと"), "low_wind", 0.3, "shadow")
    ev(cl_t0(), "street", 0.15, "")


def cl_t0():
    return CLOCK["T0"]


# ======================================================================== I：想像の場面（14-02・14-03。組み立てで青っぽくする）
def b_imag14(cl):
    world("#D7E6F2", 0.8)
    plane(noise_mat("imgground", "#C9D3C0", "#BFC9B6", 5.0, 0.9), (0, 0, 0), (60, 60))
    sun(rot=(50, 0, -25), energy=3.0, col="#FFF1DC", angle=6)
    tw = tower((0.0, 6.0, 0.0), flag=BLUE_C, s=1.0); track("tower", tw["top"], 0.0)
    lh = little_house((4.2, 2.6, 0.0), face=-20.0); track("post", lh["post"], 1.0)
    p = walker((3.9, 1.2, 0.0), 160.0, shirt="#C77D4A")
    track("stranger", p.head, 0.0)
    # 打ちまちがえた番号の札（小さなタイルの列）が、塔へ飛び、塔の窓の前で別の札と重なる
    base, tl = tile_row((-3.0, 0.0, 1.2), face=0.0, size=0.12, gap=0.02)
    base2, tl2 = tile_row((0.0, 5.0, 3.0), face=0.0, size=0.12, gap=0.02)
    for d_ in tl2: tile_color(d_, -100.0, "#FFFFFF", 2.0, 0.01)
    t_f = w("14-02", "ほかの人") - 0.3
    key(base, "location", -100.0, (-3.0, 0.0, 1.2), "CONSTANT"); key(base, "location", t_f, (-3.0, 0.0, 1.2)); key(base, "location", t_f + 1.6, (0.0, 4.98, 3.0))
    ev(t_f, "whoosh", 0.3, "tower")
    for d_ in tl: tile_color(d_, t_f + 1.6, "#FFD24A", 4.0)
    # 14-03：封筒（買い物ぶくろの絵）が塔からポストへ → 知らない人が首をかしげる
    env = envelope((0, 0, 0), 0.0); track("bill", env, 0.0)
    t_b = w("14-03", "代金") - 0.2
    pa = (0.0, 5.2, 3.0); pb = (lh["post"].matrix_world.translation[0] if False else 4.2 - 0.9 * math.cos(R(-20)) + 1.4 * math.sin(R(-20)), 2.6 - 0.9 * math.sin(R(-20)) - 1.4 * math.cos(R(-20)), 1.05)
    key(env, "location", -100.0, pa, "CONSTANT"); key(env, "location", t_b, pa); key(env, "location", t_b + 1.4, pb)
    key(env, "rotation_euler", t_b, (0, 0, 0)); key(env, "rotation_euler", t_b + 1.4, (R(80), 0, R(-20)))
    hide_key(env, -100.0, True); hide_key(env, t_b, False)
    for o in env.children: hide_key(o, -100.0, True); hide_key(o, t_b, False)
    ev(t_b + 1.4, "thud", 0.3, "post")
    key(p.head, "rotation_euler", w("14-03", "知らない人") + 0.3, (0, 0, 0)); key(p.head, "rotation_euler", w("14-03", "知らない人") + 0.8, (0, R(14), 0))


# ======================================================================== 小窓（想像。青っぽくする）：05 のぞき見・06 捨てた紙・07 お店で使う
def b_pip05(cl):
    """窓の外から、人がのぞきこむ（家の中から窓を見る）"""
    room(window=True); town_view17()
    p = walker((3.6, -0.2, 0.0), -90.0, shirt="#3A4A5E"); track("peeker", p.head, 0.0)
    key(p.root, "location", s("05-01") - 0.2, (3.9, 0.6, 0.0)); key(p.root, "location", s("05-01") + 1.2, (3.6, -0.2, 0.0))


def b_pip06(cl):
    """番号を書いた紙が、ゴミ箱へひらひら落ちる"""
    room(window=True); tr = trash_can(TRASH)
    pp = card_obj((0, 0, 0), (0, 0, 0), tex="card_blue", w=0.2); track("paper", pp, 0.0)      # 番号を書いた紙（カードの番号の写し。大きく）
    t0 = s("06-01") + 0.3
    for k in range(6):
        key(pp, "location", t0 + k * 0.35, (TRASH[0] + 0.06 * (1 if k % 2 else -1), TRASH[1], 0.9 - k * 0.12))
        key(pp, "rotation_euler", t0 + k * 0.35, (R(25 * (1 if k % 2 else -1)), 0, R(20 * k)))


def b_pip07(cl):
    """お店のレジで、カードを出す（人は出さず、レジに差し出したカードを前から。番号を打つ画面も見える）"""
    S_ = shop()
    reg_screen(S_["screen"], [(0.0, "reg_0"), (s("07-01") + 1.6, "reg_4"), (s("07-01") + 2.4, "reg_8")])
    c_ = card_obj((0.0, 1.0, 1.05), (R(80), 0, 0), w=0.24); track("card", c_, 0.0)
    key(c_, "location", -100.0, (0.0, 0.7, 1.05), "CONSTANT"); key(c_, "location", s("07-01") + 0.3, (0.0, 0.7, 1.05)); key(c_, "location", s("07-01") + 1.3, (0.0, 1.0, 1.05))


# ======================================================================== カット割り：(名前, 舞台, 切り替わる時刻, カメラ, 親)
#   同じ絵を 8 秒以上続けない。文の切れ目で、寄り・引き・横・まるロボを追う絵に替える。家の中は、まるロボから 0.9 m 以上離す
SX, SY = SAFE[0], SAFE[1]
CUTS = [
    # 冒頭（夜）
    ("A01", b_night, 0.0, C((-0.4, -1.3, 1.25), (1.2, 1.2, 0.25), 26, (-0.2, -1.1, 1.15)), "A"),
    ("A01b", b_night, w("01-01", "1枚") - 0.3, C((-0.25, 0.75, 0.5), (0.75, 0.72, 0.22), 30), "A"),
    ("A01c", b_night, s("01-03"), C((1.6, 0.35, 0.7), (0.8, 1.35, 0.25), 26), "A"),
    ("A01d", b_night, s("01-04"), C((1.35, 0.3, 0.55), (0.8, 1.45, 0.3), 30), "A"),
    # 冒頭（朝）
    ("A02", b_house, s("02-01"), C((1.65, 0.72, 0.45), (1.42, 0.98, 0.0), 34), "A"),
    ("A02b", b_house, s("02-02"), C((2.2, 0.4, 0.55), (1.3, 0.85, 0.2), 28), "A"),
    ("A02c", b_house, s("02-03"), C((1.55, 0.82, 0.38), (1.42, 0.98, 0.0), 36), "A"),
    ("A02d", b_house, s("02-04"), C((2.25, 0.85, 0.42), (1.16, 0.98, 0.22), 30), "A"),
    ("A02e", b_house, s("02-05"), C((1.9, 0.3, 0.8), (1.0, 1.2, 0.25), 26), "A"),
    ("A02f", b_house, s("02-06"), C((1.25, 1.15, 0.62), (0.8, 1.85, 0.22), 30), "A"),
    ("A02g", b_house, s("02-07"), C((1.6, 0.4, 0.5), (0.8, 1.12, 0.25), 28), "A"),
    ("A02h", b_house, s("02-08"), C((1.55, 0.82, 0.38), (1.42, 0.98, 0.0), 36), "A"),
    ("A03", b_house, s("03-01"), C((-0.6, -1.4, 1.3), (1.2, 1.0, 0.4), 30, (-0.4, -1.2, 1.25)), "A"),
    ("A03b", b_house, s("03-03"), C((1.9, 0.0, 0.8), (0.8, 1.4, 0.3), 26, (1.7, 0.2, 0.75)), "A"),
    ("A03c", b_house, s("03-05"), C((-0.35, 0.55, 0.55), (0.75, 1.12, 0.3), 28), "A"),
    # 1章
    ("A04", b_house, s("04-01"), C((1.2, 0.35, 0.8), (0.3, 1.25, 0.5), 26), "A"),
    ("A04b", b_house, s("04-02"), C((-0.1, 0.3, 0.5), (0.34, 1.2, 0.4), 30), "A"),
    ("A04c", b_house, s("04-03"), C((1.25, 0.4, 0.6), (0.34, 1.2, 0.25), 28), "A"),
    ("A04d", b_house, s("04-04"), C((-1.2, -1.8, 2.0), (1.4, 0.7, 0.3), 24), "A"),
    ("A05", b_house, s("05-01"), C((0.5, -0.4, 1.0), (2.6, 0.1, 0.75), 26, (0.6, -0.35, 0.98)), "A"),
    ("A05b", b_house, s("05-02") + 1.2, C((1.4, 0.0, 0.55), (2.7, 0.3, 0.6), 28), "A"),
    ("A05c", b_house, s("05-03"), C((1.6, -0.3, 0.6), (2.5, 0.3, 0.3), 30), "A"),
    ("A05d", b_house, s("05-04"), C((1.6, 0.2, 0.8), (0.8, 1.75, 0.3), 26), "A"),
    ("A06", b_house, s("06-01"), C((2.95, 1.6, 0.65), (2.0, 1.0, 0.2), 28), "A"),
    ("A06b", b_house, s("06-02"), C((0.95, 1.2, 0.45), (1.95, 1.35, 0.15), 28), "A"),
    ("A06c", b_house, s("06-03"), C((2.85, 0.4, 0.5), (1.95, 1.08, 0.22), 30), "A"),
    ("A07", b_house, s("07-01"), C((1.0, 0.25, 0.55), (1.9, 1.05, 0.25), 28), "A"),
    ("A07b", b_house, s("07-02"), C((0.95, 0.75, 0.35), (1.95, 1.08, 0.22), 30), "A"),
    ("A08", b_house, s("08-01"), C((-0.6, -1.4, 1.5), (1.3, 0.8, 0.3), 28), "A"),
    ("A08b", b_house, s("08-02"), C((1.0, 0.55, 0.55), (1.95, 1.05, 0.15), 28), "A"),
    ("A08c", b_house, s("08-03"), C((0.95, 0.8, 0.18), (1.95, 1.08, 0.12), 30), "A"),
    ("A08d", b_house, s("08-04"), C((-1.2, -1.8, 2.0), (1.6, 0.6, 0.3), 24), "A"),
    ("A08e", b_house, s("08-05"), C((1.5, 0.1, 0.55), (1.95, 1.08, 0.2), 30), "A"),
    ("A09", b_house, s("09-01"), C((1.75, 0.15, 0.75), (1.2, 1.2, 0.25), 26), "A"),
    ("A09b", b_house, s("09-02"), C((1.75, 1.3, 0.5), (0.8, 1.3, 0.12), 30), "A"),
    ("A09c", b_house, s("09-03"), C((1.45, 1.45, 0.3), (0.8, 1.4, 0.0), 50), "A"),
    # 2章（家）
    ("A10", b_house, s("10-01"), C((1.75, 1.3, 0.45), (0.8, 1.3, 0.15), 30), "A"),
    ("A10b", b_house, s("10-02"), C((0.8, 0.15, 0.6), (0.8, 1.48, 0.62), 30), "A"),
    ("A10c", b_house, s("10-05"), C((0.0, 0.2, 0.62), (0.8, 1.48, 0.7), 32, (1.6, 0.2, 0.62)), "A"),
    ("A10d", b_house, s("10-06"), C((1.75, 1.0, 0.4), (0.8, 1.3, 0.5), 28), "A"),
    ("A11", b_house, s("11-01"), C((0.35, 0.85, 0.72), (0.37, 1.48, 0.70), 34), "A"),
    ("A11b", b_house, s("11-04"), C((1.2, 0.5, 0.75), (TWR_B[0], TWR_B[1], 2.4), 24), "A"),
    ("A11c", b_house, s("11-05"), C((0.6, 0.6, 0.85), (3.0, 0.0, 1.3), 24), "A"),
    ("A11d", b_house, s("11-06"), C((0.8, 0.2, 0.8), (0.8, 1.48, 0.8), 30), "A"),
    ("A12", b_house, s("12-01"), C((1.25, 0.85, 0.72), (1.31, 1.48, 0.70), 34), "A"),
    ("A12b", b_house, s("12-02"), C((1.75, 1.35, 0.5), (0.95, 1.2, 0.45), 30), "A"),
    ("A12c", b_house, s("12-03"), C((0.8, 0.2, 0.75), (0.8, 1.48, 0.70), 30), "A"),
    ("A12d", b_house, s("12-05"), C((1.25, 0.85, 0.72), (1.31, 1.48, 0.70), 34), "A"),
    ("A12e", b_house, s("12-06"), C((1.75, 1.0, 0.45), (0.8, 1.12, 0.25), 30), "A"),
    # 2章（お店）
    ("C13", b_shop, s("13-01"), C((-3.2, -6.5, 1.9), (0.0, 0.2, 1.4), 28, (-2.8, -6.0, 1.8)), "C"),
    ("C13b", b_shop, s("13-02"), C((1.6, 0.7, 1.5), (0.0, 1.35, 1.0), 30), "C"),
    ("C13c", b_shop, s("13-03"), C((-1.5, 0.5, 1.2), (0.0, 1.05, 0.8), 30), "C"),
    ("C13d", b_shop, s("13-04"), C((0.6, 0.55, 1.0), (0.0, 1.15, 0.8), 32), "C"),
    ("C13e", b_shop, s("13-05"), C((0.0, 0.3, 1.5), (0.0, 1.45, 1.12), 36), "C"),
    ("C13f", b_shop, s("13-07"), C((-5.0, -7.5, 2.6), (3.0, 3.0, 2.0), 24), "C"),
    ("C13g", b_shop, s("13-08"), C((0.9, 1.35, 0.95), (0.0, 0.62, 0.6), 30), "C"),
    ("C13h", b_shop, s("13-09"), C((0.0, 0.3, 1.5), (0.0, 1.45, 1.12), 36), "C"),
    ("C13i", b_shop, s("13-10"), C((-1.5, 0.5, 1.2), (0.0, 1.05, 0.8), 30), "C"),
    ("C13j", b_shop, s("13-11"), C((0.0, 0.3, 1.5), (0.0, 1.45, 1.12), 36), "C"),
    ("I14", b_imag14, s("14-02"), C((-1.0, -7.5, 3.0), (0.8, 3.5, 2.0), 26), "I"),
    ("I14b", b_imag14, s("14-03"), C((1.6, -3.0, 1.8), (4.0, 2.0, 1.0), 28), "I"),
    ("C14", b_shop, s("14-04"), C((0.0, 0.3, 1.5), (0.0, 1.45, 1.12), 36), "C"),
    ("C14b", b_shop, s("14-05"), C((0.0, -1.2, 1.3), (0.0, 2.15, 1.95), 30), "C"),
    ("C14c", b_shop, s("14-07"), C((0.0, -0.8, 1.35), (0.0, 2.15, 1.9), 28), "C"),
    ("C14d", b_shop, s("14-08"), C((1.1, 1.4, 1.0), (0.0, 0.62, 0.9), 28), "C"),
    ("C14e", b_shop, s("14-09"), C((0.0, -6.0, 2.0), (0.0, 1.0, 2.0), 26, (0.0, -5.4, 2.0)), "C"),
    # 8 秒をこえるカットを、文の切れ目で替える（下書きの最初の点検）
    ("A03a", b_house, s("03-02"), C((2.4, 1.0, 1.1), (0.8, 1.6, 0.3), 26), "A"),
    ("A03b2", b_house, s("03-04"), C((1.5, 0.35, 0.5), (0.8, 1.35, 0.3), 30, (1.45, 0.42, 0.48)), "A"),
    ("A07c", b_house, s("07-03"), C((1.3, 0.2, 0.6), (1.9, 1.08, 0.2), 28), "A"),
    ("A10b2", b_house, s("10-03"), C((0.8, 0.1, 0.8), (0.8, 1.48, 0.68), 28), "A"),
    ("A10b3", b_house, s("10-04"), C((-0.1, 0.5, 0.5), (0.8, 1.48, 0.7), 28), "A"),
    ("A10e", b_house, s("10-07"), C((0.1, 0.45, 0.5), (0.85, 1.45, 0.6), 30), "A"),
    ("A11a", b_house, s("11-02"), C((0.8, 0.2, 0.75), (0.55, 1.48, 0.7), 30), "A"),
    ("A11a2", b_house, s("11-03"), C((0.15, 0.95, 0.62), (0.37, 1.48, 0.7), 36), "A"),
    ("A12c2", b_house, s("12-04"), C((1.6, 0.6, 0.6), (0.8, 1.48, 0.66), 30), "A"),
    ("C14b2", b_shop, s("14-06"), C((0.9, 0.4, 1.4), (0.0, 2.15, 1.95), 30), "C"),
    ("C13p", b_shop, s("13-01") - 0.1, None, "C"),
    # 小窓（想像）
    ("P05", b_pip05, s("05-01") - 0.2, C((1.4, -0.3, 1.1), (3.0, -0.2, 1.4), 30), "I"),
    ("P06", b_pip06, s("06-01") - 0.2, C((1.55, 0.85, 0.75), (1.95, 1.45, 0.35), 30), "I"),
    ("P07", b_pip07, s("07-01") - 0.2, C((0.75, 0.25, 1.45), (0.0, 1.15, 1.0), 30), "I"),
]
CUTS = [c for c in CUTS if c[3] is not None]
for i_, c_ in enumerate(CUTS):
    if len(c_) == 4: CUTS[i_] = c_ + ("B",)
PIP_ONLY = {"P05", "P06", "P07"}
END_T = e("14-10") + 2.0
CUTS.sort(key=lambda c: c[2])
_main = [c for c in CUTS if c[0] not in PIP_ONLY]
CLIPS = {}
for i, (nm, fn, tc, cm, par) in enumerate(_main):
    t0 = max(0.0, tc - 0.1)
    t1 = (_main[i + 1][2] + 0.75) if i + 1 < len(_main) else END_T
    CLIPS[nm] = (fn, t0, t1, cm, par)
for _p, _fn, _a, _b in (("P05", b_pip05, "05-01", "05-03"), ("P06", b_pip06, "06-01", "06-03"), ("P07", b_pip07, "07-01", "07-03")):
    CLIPS[_p] = (_fn, s(_a) - 0.2, e(_b) + 0.4, [c for c in CUTS if c[0] == _p][0][3], "I")


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
