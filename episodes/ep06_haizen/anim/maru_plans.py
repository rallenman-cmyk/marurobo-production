# 6本目：まるロボの動きの予定（marumotion）。2026-11-17 ユーザー「止めて本物に替える」
#   決まり：skill/marurobo-video-production/references/maru_walk.md（手で動かさない。予定 → simulate → marurig で当てる）
#   bpy を使わない（Blender の外でも、時刻が間に合うかを確かめられる：python3 maru_plans.py）
#
#   座標の約束：まるロボは「小さく置く親」（場所 ORIGIN・大きさ S）の中で動く。予定の座標は親の中（本物の寸法・m）。
#     世界の (x, y) → 予定の (x / S, y / S)（親は世界の原点・回転なし・大きさ S。台の上は親の高さで上げる）
#   向きの約束：marumotion の heading 0 は +Y を向く（左回りが＋）。6本目の face（Maru(face=…)）0 は −Y を向く → heading = face + 180
#   時刻：予定の 0 秒＝クリップの時刻 0 秒（声の時刻と同じ）。T0 から始め、upto() で声の時刻まで待つ
import os, sys, math, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_MM = os.path.join(HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts", "marumotion.py")
_sp = importlib.util.spec_from_file_location("marumotion", _MM); mm = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(mm)
import timing as T
s, e, w = T.s, T.e, T.w

S = 0.26            # まるロボの大きさ（本物の 0.26 倍：体の高さ約 0.32m）
LATE = []           # 声の時刻に間に合わない所（確かめ用）


def L(p):
    """世界の (x, y) → 予定の座標"""
    return (p[0] / S, p[1] / S)


def H(face):
    """6本目の face（度）→ marumotion の heading（度）"""
    return face + 180.0


def new(pos, face, t0):
    p = mm.Plan(pos=L(pos), heading=H(face))
    p.wait(t0)
    return p


def upto(p, t, what=""):
    """声の時刻 t まで待つ。もう過ぎていたら記録する（動きが声に間に合っていない）"""
    if p.t > t + 0.05: LATE.append((what, round(t, 2), round(p.t, 2)))
    if p.t < t: p.idle(t - p.t, glance=False) if t - p.t > 0.6 else p.wait(t - p.t)
    return p


# ---------------------------------------------------------------- S01〜S04：通路で先輩に会う
def plan_open(t0=0.0):
    # はじめから、歩く先（通路の奥）を向いて立つ（歩き出す前に回ると、声に間に合わない）
    p = new((-0.15, 0.3), 166, t0)
    upto(p, s("01-02"), "01-02 歩き出し")
    p.walk_to(L((0.0, 0.9)), label="見て回る")
    p.look(yaw=45, hold=0.3)                         # きょろきょろ（体ごと左を見る → 戻る）
    upto(p, w("02-01", "奥から"), "02-01 奥を向く")
    p.turn_to(heading=H(180))
    upto(p, w("03-01", "ぴたっ") + 0.05, "03-01 ぴたっ")
    p.surprise()
    upto(p, s("03-03") + 1.3, "03-03 先輩をよける")
    p.turn_to(heading=H(180) + 40)
    upto(p, s("03-04") + 1.0, "03-04 見送る")
    p.turn_to(heading=H(320))
    upto(p, s("04-04") + 0.4, "04-04 歩いて移る")
    p.walk_to(L((-0.25, 0.9)))
    return p


# ---------------------------------------------------------------- S05〜S07：台所の出口で先輩をよく見る
def plan_meet(t0=0.0):
    # 場面の前から歩き出して、カットをまたぐ（maru_walk.md「カットの前から歩き出す」）
    p = new((-0.25, 0.9), 180, t0)
    upto(p, s("05-01") - 1.0, "05-01 歩く")
    p.walk_to(L((0.0, 1.95)), speed=mm.V_BRISK)
    upto(p, w("05-02", "ピポ") - 0.3, "05-02 ピポ")
    p.greet()
    upto(p, s("06-01") + 0.2, "06-01 回りこむ")
    p.walk_to(L((0.6, 2.2)))
    upto(p, s("06-02") + 0.1, "06-02 おなかのカメラ")
    p.walk_to(L((0.35, 1.95))); p.look(pitch=12, hold=0.4)
    upto(p, s("06-03") + 0.5, "06-03 足もと")
    p.walk_to(L((-0.1, 2.0)))
    upto(p, s("07-03") + 0.6, "07-03 にこっ")
    p.hops(n=2)
    return p


# ---------------------------------------------------------------- 予定にない動き（ころぶ・寝ころぶ・運ばれる）
#   予定（marurig で当てた体）の外側に、2 つの重ねる動きを置く：
#   PARENT：小さく置く親の場所・向き（世界）。運ばれる所だけ使う。[(時刻, (x, y, z), face 度)]。無ければ親は世界の原点に止まる
#   TILT：足もとを中心に、体ごと倒す。まるロボの向きで見て、pitch＋＝後ろへ倒れる、roll＋＝右へ倒れる、dz＝持ち上げ（親の中の m＝本物の寸法。体の半径は約 0.5）。[(時刻, pitch, roll, dz)]
EXTRA = {}


def extra(name, parent=None, tilt=None):
    EXTRA[name] = dict(parent=parent or [], tilt=tilt or [])


# ---------------------------------------------------------------- S08：番号を押すのを見上げる
def plan_order(t0=0.0):
    p = new((0.45, 2.0), 160, t0)
    upto(p, w("08-03", "画面") - 0.1, "08-03 画面を見上げる")
    p.look(pitch=14, hold=max(0.5, e("08-03") - p.t - 0.4))
    upto(p, s("08-04") + 1.2, "08-04 先輩を見送る")
    p.turn_to(heading=H(200))
    return p


# ---------------------------------------------------------------- S11：天井を見上げて……ころん
def plan_ceil(t0=0.0):
    p = new((-0.35, 0.9), 32, t0)
    upto(p, w("11-05", "見上げて") - 0.2, "11-05 見上げる")
    p.awe(dur=max(1.2, w("11-05", "ころん") - 0.4 - p.t), pitch=30)
    tc = w("11-05", "ころん") - 0.1
    # 見上げすぎて、後ろへころん（足もとを中心に 92 度。転がった体は床の上に横たわる）
    extra("ceil", tilt=[(tc - 0.35, 0, 0, 0), (tc + 0.3, 92, 0, 0.47)])
    p.event(tc + 0.3, "land", 0.6)
    return p


# ---------------------------------------------------------------- S13：光の物差しの窓をのぞきこむ
def plan_lidar(t0=0.0):
    p = new((0.55, 0.15), 130, t0)
    upto(p, s("13-02") + 0.4, "13-02 のぞく")
    p.look(pitch=-14, hold=1.2); p.peer(dur=1.6)
    return p


# ---------------------------------------------------------------- S14〜S16：暗い店で立っている（先輩の目の点の世界）
def plan_dark(t0=0.0):
    p = new((0.5, 2.15), 200, t0)
    p.idle(max(1.0, e("16-04") + 1.5 - p.t), glance=False)
    return p


# ---------------------------------------------------------------- S17〜S21：床に転がる係 → 起きて横へ
def plan_test(t0=0.0):
    # はじめから歩く先を向き、通路のまん中の近くから歩き出す（遠くから回って歩くと、寝ころぶ言葉に間に合わない）
    p = new((0.35, 0.35), -66.8, t0)
    upto(p, s("18-01"), "18-01 歩く")
    p.walk_to(L((0.0, 0.2)), speed=mm.V_BRISK)
    tl = w("18-01", "転がって") + 0.9
    upto(p, tl, "18-01 寝ころぶ")
    tu = s("19-01") - 0.9
    # 横に寝ころぶ（足もとを中心に右へ 88 度）→ 19-01 の前に起きる
    extra("test", tilt=[(tl, 0, 0, 0), (tl + 0.45, 0, 88, 0.5), (tu, 0, 88, 0.5), (tu + 0.45, 0, 0, 0)])
    p.event(tl + 0.45, "land", 0.6); p.event(tu, "jump", 0.4)
    upto(p, tu + 0.5, "19-01 起きる")
    p.walk_to(L((0.5, 0.55)), speed=mm.V_BRISK); p.turn_to(heading=H(200))
    return p


# ---------------------------------------------------------------- S23〜S25：狭い通路を見守る
def plan_narrow(t0=0.0):
    p = new((-0.35, 1.3), 200, t0)
    upto(p, s("23-03") + 0.3, "23-03 困る")
    p.turn_to(heading=H(180)); p.confused()
    upto(p, e("25-02") - 0.8, "25-02 よろこぶ")
    p.hops(n=2)
    return p


# ---------------------------------------------------------------- S26〜S28：テーブルの上で、頭をすりすり → 怒られる
TABLE_Z = 0.742


def plan_face(t0=0.0):
    p = new((1.15, 1.35), -90, t0)
    extra("face", parent=[(t0, (0.0, 0.0, TABLE_Z), 0.0)])     # テーブルの上（親を天板の高さへ）
    t_r = s("28-01") + 2.2
    upto(p, t_r - 0.6, "28-01 近づく")
    p.walk_to(L((1.02, 1.35)))
    t_ang = w("28-03", "怒った") - 0.15
    # すりすり：前へ頭を傾けて、うなずくように何度もこすりつける（怒った顔になる直前まで）
    k = 0
    while p.t < t_ang - 0.9:
        p.nod(n=2, amp=14.0); k += 1
        if k % 2 == 0: p.event(p.t - 0.2, "rub", 0.4)
    upto(p, t_ang + 0.2, "28-03 怒られる")
    p.surprise(); p.back_to(L((1.32, 1.35)))
    return p


# ---------------------------------------------------------------- S29：まとめ（立っている）
def plan_sum(t0=0.0):
    p = new((-0.25, 0.9), 200, t0)
    p.idle(max(1.0, e("29-07") + 1.5 - p.t), glance=True)
    return p


# ---------------------------------------------------------------- S30：オチ（台でひと休み → 店員さんに運ばれ、トレーに乗って席へ）
#   運ばれる所・トレーの上は、親（PARENT）を scenes.py の b_end と同じ場所に動かす。予定は親の中で (0, 0) に立ったまま
def plan_end(t0, parent_keys):
    p = mm.Plan(pos=(0.0, 0.0), heading=0.0); p.wait(t0)
    extra("end", parent=parent_keys)
    upto(p, s("30-01") + 0.3, "30-01 ひと休み")
    p.rest(dur=1.0)
    t_l = w("30-02", "ひょいと")
    upto(p, t_l - 0.7, "30-02 起きる")
    p.wake()
    upto(p, w("30-04", "デザート") - 0.2, "30-04 デザート")
    p.surprise()
    return p


def check():
    for nm, fn, t0 in (("S01〜S04", plan_open, 0.0), ("S05〜S07", plan_meet, s("05-01") - 1.2), ("S08", plan_order, s("08-01") - 0.2),
                       ("S11", plan_ceil, s("11-01") - 0.2), ("S13", plan_lidar, s("13-01") - 0.2), ("S14〜S16", plan_dark, s("14-01") - 0.2),
                       ("S17〜S21", plan_test, s("17-01") - 0.2), ("S23〜S25", plan_narrow, s("23-01") - 0.2), ("S26〜S28", plan_face, s("26-01") - 0.2),
                       ("S29", plan_sum, s("29-01") - 0.2), ("S30", lambda t0: plan_end(t0, []), s("30-01") - 0.2)):
        LATE.clear(); p = fn(t0)
        print(nm, "予定の終わり %.1f 秒" % p.t, "間に合わない所：", LATE or "なし")


if __name__ == "__main__":
    check()
