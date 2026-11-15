# 7本目（キーボード）：3D の場面を声の時刻に合わせて動かして描く
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 8] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   PC の本番：... -- <クリップ> <出力> --samples 24 --res 1920 1080 --frames 0 99 --gpu --video --fast
#   クリップの一覧は下の CUTS（名前・場面の組み立て・切り替わる時刻＝その文の字幕が出る時刻）
#   場面の組み立て（b_*）は、その舞台の動きを全部作り、カメラだけをクリップごとに選ぶ（6本目と同じ作り方）
#   部品は kit.py（6本目の kit を読み込んで足した）、時刻と動きの共通は 6本目の core.py（声は ../voice）
#   決まり：3D の中に字を書かない（キーの字は 2D。キーの場所を track で書き出す）／まるロボは喋らない／動きは言い終えてから／
#     瞬間移動に見せない（跳ねて・歩いて移る）／カメラはいつもゆっくり動かす／道のり：クワーティ＝青・ABC 順＝橙・いろは歌専用＝緑
import os, sys, math
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
_K7 = KIT_HERE
exec(open(os.path.join(KIT_HERE, "..", "..", "ep06_haizen", "anim", "core.py"), encoding="utf-8").read().replace(
    'VO = os.path.join(KIT_HERE, "..", "voice")', 'VO = os.path.join(_K7, "..", "voice")'))
CLIPNAME, OUTDIR = _argv[0], _argv[1]


def _opt(name, n=1, default=None):
    if name in _argv:
        i = _argv.index(name); v = _argv[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default


SAMPLES = int(_opt("--samples", 1, 8)); RES = tuple(int(x) for x in _opt("--res", 2, ("480", "270"))); STEP = int(_opt("--step", 1, 3))
STILLS = [float(x) for x in _opt("--stills", 1, "").split(",") if x]
TRACK_ONLY = "--track" in _argv
sys.path.insert(0, os.path.join(KIT_HERE, "..", "tools"))
IROHA = "irohanihoheto chirinuruwo wakayotareso tsunenaramu uwinookuyama kefukoete asakiyumemishi wehimosesu".replace(" ", "")
KANA = "いろはにほへとちりぬるをわかよたれそつねならむうゐのおくやまけふこえてあさきゆめみしゑひもせす"


_M_ = [None]


class MaruR(Maru):
    """まるロボ（最後に作ったものを覚えておく。カット割りのカメラで追うため）"""
    def __init__(self, *a, **k):
        Maru.__init__(self, *a, **k); _M_[0] = self


def cam(loc, target, lens=35, t0=None, t1=None, loc1=None, target1=None, lens1=None):
    c, tg = cam_rig(loc, target, lens)
    if t0 is not None:
        cam_move(c, tg, t0, t1, loc, loc1 or loc, target, target1 or target, lens, lens1 or lens)
    return c, tg


def topcam(loc0, loc1=None, t0=None, t1=None, lens=30):
    c = cam_top(loc0, lens)
    if loc1 is not None: cam_top_move(c, t0, t1, loc0, loc1)
    return c


# ======================================================================== A：夜の机（S01〜S07・S19b・S21・S23a・S24c・S27・S28）
QO = (-0.8, 0.5)        # クワーティの左上（上の段の左端）
AO = (1.45, 0.5)        # ABC 順（04-03 で右からすべりこむ）
DO_ = (1.45, 0.5)       # 速い並び（23 章。同じ場所に）


def b_desk(cl):
    desk_room()
    Q = Board(ROWS_Q, QO, name="kq"); Q.track_all("k_")
    A = Board(ROWS_ABC, AO, name="ka", key_col="#F3EDE2"); A.track_all("a_")
    # ABC 順：04-03 で右からすべりこむ（それまで画面の外）。08 章からは使わない
    key(A.root, "location", -100.0, (6.0, 0, KEY_TOP)); key(A.root, "location", s("04-03"), (6.0, 0, KEY_TOP))
    key(A.root, "location", s("04-03") + 1.6, (0, 0, KEY_TOP)); ev(s("04-03") + 0.1, "whoosh", 0.4); ev(s("04-03") + 1.6, "land", 0.4)
    D = Board(ROWS_DV, DO_, name="kd", key_col="#E6F0EA"); D.track_all("d_")
    key(D.root, "location", -100.0, (6.0, 0, KEY_TOP)); key(D.root, "location", s("23-02"), (6.0, 0, KEY_TOP))
    key(D.root, "location", s("23-02") + 1.4, (0, 0, KEY_TOP))
    if s("23-02") > s("04-03"):
        key(A.root, "location", s("08-01"), (0, 0, KEY_TOP)); key(A.root, "location", s("08-01") + 0.1, (6.0, 0, KEY_TOP))
    M = MaruR(Q.pos("A", 0.075), face=0.0); track("maru", M.body, 0.1); track("maru_top", M.body, 0.25)
    P = lambda B, ch: B.pos(ch, 0.075)
    # 01：A を打つ
    M.at(-100.0, loc=P(Q, "A"), face=0.0)
    t = w("01-04", "ぴょん"); M.hop(t - 0.2, h=0.22, d=0.4); Q.press("A", t + 0.18, gain=0.7)
    # 02：B をさがす（右に S・左は何もない・上に Q）
    M.at(w("02-01", "すぐとなり") - 0.4, face=0.0); M.at(w("02-01", "すぐとなり"), face=-35)
    M.at(s("02-02"), face=-60); M.at(s("02-03") - 0.1, face=-60); M.at(s("02-03") + 0.4, face=70)
    t = s("02-04"); M.at(t, face=70)
    for i, ch in enumerate(("Q", "W", "S", "D", "E")):
        hop_path(Q, ("A" + ch) if i == 0 else (("Q", "W", "S", "D", "E")[i - 1] + ch), t + 0.4 + i * 0.55, 0.55, M, line=False)
    M.wobble(e("02-04") - 0.6, e("02-04"), 8, 0.3)
    # 03：上から。迷いながら B へ（E → R → F → V → B）
    t = s("03-01") + 0.2
    for i, (a_, b_) in enumerate((("E", "R"), ("R", "F"), ("F", "V"), ("V", "B"))):
        hop_path(Q, a_ + b_, t + i * 0.9, 0.9, M, line=False)
    for i, ch in enumerate("QWERTY"): Q.light(ch, w("03-01", "Q W E R T Y") + 0.3 * i, s("03-03") + 0.2)
    M.at(e("03-05") + 0.4, face=0.0)
    # 04：ABC 順のキーボードがとなりに。まるロボは B から右を見て、跳ねてよろこぶ
    M.at(s("04-03") - 0.3, face=0.0); M.at(s("04-03") + 0.6, face=-90)
    M.hop(s("04-04") + 0.3, h=0.2, d=0.4); M.hop(s("04-04") + 0.8, h=0.2, d=0.4)
    # 05：「マルロボ」を打つ（青 → 橙）。最初の M へ歩く
    M.walk(s("05-01") + 0.4, s("05-01") + 1.6, P(Q, "M"))
    t = w("05-04", "道のり"); dt = min(0.55, (e("05-04") + 0.4 - t) / 7)
    hop_path(Q, "MARUROBO", t, dt, M, col=BLUE_L, name="path_q")
    t2 = s("05-05") - 0.2; M.at(t2 - 0.6, loc=P(Q, "O")); M.walk(t2 - 0.5, t2 + 0.2, P(A, "M"))
    dt2 = min(0.55, (e("05-05") + 0.5 - t2) / 7)
    hop_path(A, "MARUROBO", t2 + 0.4, dt2, M, col=ORANGE_L, name="path_a")
    # 06：上から結果。まるロボは O の上できょとん（首をかしげる）
    M.at(s("06-04"), face=0.0); M.tilt(w("06-04", "ほとんど"), 14); M.tilt(e("06-04") + 0.3, 0)
    # 07：いろは歌（2 台で同時に。道のりの線が伸びる。まるロボは跳ねつかれて、ぜえぜえ）
    t0 = s("07-03") + 0.3; t1 = e("07-03") + 0.2; dt = (t1 - t0) / (len(IROHA) - 1)
    lq = hop_path(Q, IROHA, t0, dt, None, col=BLUE_L, name="iro_q", z=0.105)
    la = hop_path(A, IROHA, t0, dt, None, col=ORANGE_L, name="iro_a", z=0.105)
    for k_ in range(int((t1 - t0) / 0.5)): M.hop(t0 + k_ * 0.5, h=0.1, d=0.45, sound=False)
    M.wobble(t1 + 0.1, s("07-05") + 1.0, 6, 0.6)
    for ob in (lq, la):        # 07 の終わりで消す（08 章から先の机の場面に残さない）。最初に「見える」を打っておく（打たないと、最初から隠れる）
        hide_key(ob, -100.0, False); hide_key(ob, s("08-01") - 0.5, True)
    for nm in ("path_q", "path_a"):
        hide_key(bpy.data.objects[nm], -100.0, False); hide_key(bpy.data.objects[nm], s("07-01"), True)
    # 19b：Z → S → E（となりへ 1 歩ずつ）
    M.at(s("19-03") - 1.0, loc=P(Q, "Z"), face=0.0)
    for ch, wd in (("Z", "この3つ"), ("S", "光らせて"), ("E", "みると")):
        Q.light(ch, w("19-03", wd), e("19-05") + 0.5, col="#FFD24A")
    hop_path(Q, "ZSE", w("19-04", "S"), 0.9, M, line=False)
    # 21：首をかしげる
    M.at(s("21-01") - 0.5, loc=P(Q, "G"), face=0.0); M.tilt(w("21-02", "もっと"), 12); M.tilt(e("21-02"), 0)
    # 23：速い並び（23-02 ですべりこむ。まるロボは跳ねて「おお」→ 23-06 で首をかしげる）
    M.walk(s("23-02") + 1.6, s("23-03") + 0.4, P(D, "A"))
    hop_path(D, "AOEUIDHTNS", s("23-03") + 0.6, min(0.45, (e("23-04") - s("23-03")) / 11), M, line=False)
    M.glow(s("23-04"), 1.6, 0.3); M.glow(e("23-04") + 0.2, 0.9, 0.3)
    # 24：スマホ（机に寝かせた大きなスマホ。棒のない、薄い機械）
    ph, scr = smartphone((-0.1, -1.6, 0.0), s=0.62); track("phone", scr, 0.05)
    key(ph, "location", -100.0, (-0.1, -6.0, 0.0)); key(ph, "location", s("24-06") - 1.0, (-0.1, -6.0, 0.0)); key(ph, "location", s("24-06"), (-0.1, -1.6, 0.0))
    M.walk(s("24-06") + 0.2, s("24-07") - 0.2, (0.1, -1.25, 0.06))
    M.hop(w("24-07", "スマホ"), h=0.2, d=0.4); M.at(e("24-07"), face=0.0)
    key(ph, "location", s("27-01") - 0.6, (-0.1, -1.6, 0.0)); key(ph, "location", s("27-01") - 0.5, (-0.1, -6.0, 0.0))
    M.at(s("27-01") - 0.6, loc=(0.1, -1.25, 0.06))
    # 27：まとめ（キーボードの真ん中でキーを見渡す）
    M.at(s("27-01") - 0.5, loc=P(Q, "G"), face=0.0)
    M.at(s("27-03"), face=-25); M.at(s("27-04"), face=25); M.at(s("27-06"), face=0.0)
    return dict(Q=Q, A=A, D=D, M=M)


def b_desk_cam(cl, S_):
    Q, M = S_["Q"], S_["M"]
    if cl == "S01a":
        cam((0.2, -2.2, 0.75), (-0.55, 0.3, 0.2), 38, s("01-01") - 0.2, e("01-04") + 1.0, (-0.1, -1.7, 0.55), (-0.62, 0.28, 0.15), 44)
    elif cl == "S02a":
        cam((-0.85, -0.55, 0.35), (-0.4, 0.4, 0.12), 26, s("02-01"), e("02-04") + 0.8, (-0.9, -0.75, 0.42), (-0.3, 0.45, 0.1), 24)
    elif cl == "S03a":
        topcam((0.2, 0.15, 2.0), (0.2, 0.15, 3.0), s("03-01"), e("03-05") + 0.8, lens=34)
    elif cl == "S04a":
        cam((0.9, -2.7, 1.5), (0.9, 0.15, 0.0), 30, s("04-01"), e("04-04") + 0.8, (1.25, -2.9, 1.7), (1.25, 0.15, 0.0), 30)
    elif cl == "S05a":
        cam((1.25, -2.9, 1.7), (1.25, 0.15, 0.0), 30, s("05-01"), e("05-05") + 0.8, (1.25, -2.8, 1.75), (1.3, 0.15, 0.0), 30)
    elif cl in ("S06a", "S07a"):
        topcam((1.05, 0.2, 3.9), (1.05, 0.2, 4.1), s("06-01") if cl == "S06a" else s("07-01"), (e("06-04") if cl == "S06a" else e("07-10")) + 0.8, lens=34)
    elif cl == "S19b":
        cam((-0.6, -1.3, 0.6), (-0.45, 0.35, 0.08), 34, s("19-03"), e("19-05") + 0.8, (-0.5, -1.2, 0.55), (-0.4, 0.38, 0.08), 36)
    elif cl == "S21a":
        cam((0.0, -1.9, 0.9), (0.0, 0.3, 0.2), 32, s("21-01"), e("21-03") + 0.8, (0.2, -2.1, 1.0), (0.1, 0.3, 0.2), 30)
    elif cl == "S23a":
        cam((1.0, -2.8, 1.6), (1.1, 0.15, 0.0), 30, s("23-01"), e("23-04") + 0.8, (1.25, -2.9, 1.7), (1.25, 0.15, 0.0), 30)
    elif cl == "S24c":
        cam((0.9, -2.9, 1.2), (0.0, -1.4, 0.1), 32, s("24-06"), e("24-09") + 0.8, (0.7, -2.7, 1.0), (0.0, -1.3, 0.1), 34)
    elif cl == "S27a":
        cam((0.2, -2.2, 0.75), (-0.2, 0.3, 0.2), 30, s("27-01"), e("27-06") + 0.8, (0.3, -2.8, 1.1), (0.0, 0.3, 0.2), 28)


# ======================================================================== A：オチ（いろは歌専用の横に長いキーボード）
def b_end(cl):
    desk_room()
    Q = Board(ROWS_Q, QO, name="kq")
    # 横に長い 1 列（47 キー）。手前（y=-1.2）。左端から い・ろ・は…
    k = KEY; x0 = -1.2; y0 = -1.0
    L = Board([KANA], (x0, y0), name="kl", key_col="#F6F1E4", offs=(0.0,), extra_rows=False)
    for i, ch in enumerate(KANA[:12]): track("l_%d" % i, L.keys[ch], 0.06)
    M = MaruR(L.pos("い", 0.075), face=0.0); track("maru", M.body, 0.1)
    # キーがくるくる入れかわる（28-01〜28-02）：クワーティのキーが浮いて回る
    for i, (ch, o) in enumerate(list(Q.keys.items())[:18]):
        t_ = s("28-02") + 0.05 * i
        key(o, ("location", 2), t_, o.location.z); key(o, ("location", 2), t_ + 0.4, o.location.z + 0.25); key(o, ("location", 2), t_ + 0.9, o.location.z)
        key(o, ("rotation_euler", 2), t_, 0.0); key(o, ("rotation_euler", 2), t_ + 0.9, R(360))
    ev(s("28-02") + 0.1, "whoosh", 0.4)
    # いろは歌を打つ：となりへ、となりへ 1 歩ずつ（緑の線）
    t0 = w("28-04", "打って"); n = 10; dt = 0.3
    hop_path(L, KANA[:n], t0, dt, M, col=GREEN_L, name="path_l", h=0.12)
    M.at(s("28-05"), face=0.0)
    ln2 = line_path("path_l2", [L.pos(c)[:2] for c in KANA[n - 1:]], col=GREEN_L, width=0.018, z=KEY_TOP + 0.1, emit=3.0)
    ln2.data.bevel_factor_end = 0.0; ln2.data.keyframe_insert("bevel_factor_end", frame=f(t0 + n * dt))
    ln2.data.bevel_factor_end = 1.0; ln2.data.keyframe_insert("bevel_factor_end", frame=f(s("28-05") + 0.6))
    M.hop(s("28-05") + 0.2, h=0.18, d=0.4); M.at(s("28-05") + 1.0, look=10)
    # 28-06：はっと固まる → 28-07〜08：人の手が来て、となりのいつものキーボードへ（まるロボはしょんぼり）
    M.at(s("28-06") + 0.6, look=0); M.glow(s("28-06") + 0.6, 2.0, 0.15); M.glow(s("28-06") + 1.0, 0.9, 0.3)
    hand = empty((3.5, -0.2, 1.4)); km = mat("skin", "#F1C7A5", rough=0.55)
    cube(km, (0, 0, 0), (0.7, 0.9, 0.18), bevel=0.08, parent=hand)
    for i in range(4): cyl(km, (-0.27 + 0.18 * i, 0.62, 0.0), 0.07, 0.42, rot=(R(90), 0, 0), parent=hand)
    cyl(km, (0.45, 0.1, 0.0), 0.08, 0.35, rot=(R(90), 0, R(-50)), parent=hand)
    cyl(mat("sleeve", "#3E7CB1", rough=0.7), (0, -1.2, 0.0), 0.36, 1.6, rot=(R(90), 0, 0), parent=hand)
    key(hand, "location", -100.0, (3.5, -4.5, 1.6)); key(hand, "location", s("28-07"), (3.5, -4.5, 1.6))
    key(hand, "location", s("28-07") + 1.6, (-0.1, -0.6, 0.4)); key(hand, "location", s("28-08"), (-0.1, -0.2, 0.25))
    key(hand, "location", s("28-08") + 0.6, (-0.1, -0.1, 0.22))
    Q.press("F", s("28-08") + 0.5); Q.press("J", s("28-08") + 0.75)
    M.at(s("28-08") + 0.2, face=-40); M.at(s("28-08") + 0.9, look=-14); M.glow(s("28-08") + 0.9, 0.35, 0.6)
    if cl == "S28a":
        cam((-0.5, -2.6, 0.75), (-0.75, -1.0, 0.1), 35, s("28-01"), e("28-05") + 0.8, (-0.1, -2.6, 0.72), (-0.3, -1.0, 0.1), 36)
    else:
        c_, tg_ = cam((-0.6, -1.6, 0.35), (-0.6, -1.0, 0.1), 40, s("28-06"), s("28-06") + 2.6, (1.6, -4.3, 1.7), (1.4, -0.9, 0.0), 26)
        cam_move(c_, tg_, s("28-06") + 2.6, e("28-08") + 2.0, (1.6, -4.3, 1.7), (1.4, -4.0, 1.6), (1.4, -0.9, 0.0), (1.2, -0.8, 0.0))


# ======================================================================== C：1868年の作業場（S08〜S11・S16・S20）
def b_shop(cl, night=False):
    workshop(night=night)
    ptw, pk = piano_typewriter((-0.95, 0.4, 0.94))
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ": track("p_" + ch, pk[ch], 0.05)
    mtw, mk = modern_typewriter((0.0, 0.4, 0.94), layout=["QWE.TY", "ASDFG", "ZXCV"])
    for ch, o in mk.items(): track("m_" + ("dot" if ch == "." else ch), o, 0.04)
    M = MaruR((-1.9, -0.6, 0.94), face=0.0, s=0.2); track("maru", M.body, 0.1)
    # 作業台の手前の床から机の上へ（08：歩いて入る → 机の上に跳び乗る）
    sh = walker((1.2, 1.5, 0), face=180, shirt="#5A4632", pants="#3A2E24", hair="#5A4A3A")   # ショールズさんたち（顔は描かない）
    sh2 = walker((2.2, 1.6, 0), face=200, shirt="#3E4A5A", pants="#2D3640", hair="#2B2220")
    if not night:
        M.at(-100.0, loc=(-2.6, -1.6, 0.0), face=-60)
        M.walk(s("08-01") + 0.3, s("08-02"), (-1.8, -0.4, 0.0))
        M.at(s("08-02") + 0.1, face=0.0); M.at(s("08-02") + 0.5, look=18); M.at(e("08-03"), look=0)
        M.hop(s("09-01") - 0.4, h=1.1, d=0.6); M.at(s("09-01") - 0.4, loc=(-1.8, -0.4, 0.0)); M.at(s("09-01") + 0.2, loc=(-1.0, 0.2, 0.94))
        # 09：A → B → C（となりへ）
        p = lambda ch: (pk[ch].matrix_world.translation.x, pk[ch].matrix_world.translation.y, 0.94 + 0.18)
        bpy.context.view_layer.update()
        M.at(s("09-03") - 0.4, loc=p("A"))
        for i, ch in enumerate("BC"):
            ta = w("09-03", "ABC") + 0.3 + 0.6 * i
            prv = p("AB"[i]); M.at(ta - 0.5, loc=prv, interp="LINEAR"); M.at(ta, loc=p(ch), interp="LINEAR"); M.hop(ta - 0.5, h=0.15, d=0.5)
            key(pk[ch], ("location", 2), ta, pk[ch].location.z); key(pk[ch], ("location", 2), ta + 0.05, pk[ch].location.z - 0.02); key(pk[ch], ("location", 2), ta + 0.15, pk[ch].location.z)
            ev(ta, "key", 0.5)
        M.at(e("09-05"), face=20); M.hop(e("09-05") + 0.2, h=0.12, d=0.4)
        # 10：作り直すたびに、入れかわる（ピアノの機械が消え、今の形の機械がキーをはね上げながら出てくる）
        ta = s("10-02")
        hide_key(ptw, -100.0, False); hide_key(ptw, ta + 0.6, True)
        hide_key(mtw, -100.0, True); hide_key(mtw, ta + 0.6, False); scale_pop(mtw, ta + 0.6, 1.0, 0.5)
        ev(ta + 0.6, "pop", 0.6)
        M.at(ta, loc=(-1.9, 0.0, 0.94)); M.at(ta + 0.4, loc=(-1.6, -0.1, 0.94))
        for i, (ch, o) in enumerate(mk.items()):
            tt = s("10-03") + 0.08 * i
            key(o, ("location", 2), tt, o.location.z); key(o, ("location", 2), tt + 0.25, o.location.z + 0.18); key(o, ("location", 2), tt + 0.6, o.location.z)
        ev(s("10-03") + 0.2, "whoosh", 0.4)
        for i, ch in enumerate("QWE.TY"):
            tt = w("10-05", "Q W E") + 0.35 * i if ch != "." else w("10-05", "ピリオド")
            if ch in "TY": tt = w("10-05", "T Y") + 0.35 * (ch == "Y")
            key(mk[ch], ("location", 2), tt, mk[ch].location.z); key(mk[ch], ("location", 2), tt + 0.15, mk[ch].location.z + 0.05); key(mk[ch], ("location", 2), tt + 0.35, mk[ch].location.z)
        M.at(s("10-04"), loc=(-0.9, -0.3, 0.94), face=20)
    else:
        hide_key(ptw, -100.0, True)
        # 20：夜。もう 1 台の、並びの違う機械（2 段目が X P M C H）
        xtw, xk = modern_typewriter((1.6, 0.35, 0.94), layout=["23456", "XPMCH", "JBWFL"], col="#4A2A2A", name="tx")
        for ch in "XPMCH": track("x_" + ch, xk[ch], 0.04)
        hide_key(xtw, -100.0, True); hide_key(xtw, w("20-04", "別の並び"), False); scale_pop(xtw, w("20-04", "別の並び"), 1.0, 0.5)
        ev(w("20-04", "別の並び"), "pop", 0.6)
        M.at(-100.0, loc=(0.8, -0.3, 0.94), face=0.0)
        M.at(w("20-04", "別の並び") + 0.4, face=-50); M.at(s("20-05") + 0.6, face=40); M.at(s("20-06"), face=-50); M.at(s("20-07"), face=0.0)
        M.at(s("20-07") + 0.5, look=16); M.glow(w("20-04", "なんと"), 1.8, 0.2); M.glow(w("20-04", "なんと") + 0.8, 0.9, 0.4)
    if cl == "S08a":
        cam((-0.6, -3.6, 1.4), (-0.6, 0.3, 0.9), 30, s("08-01"), e("08-03") + 0.8, (-0.2, -3.2, 1.5), (-0.4, 0.4, 0.95), 32)
    elif cl == "S09a":
        cam((-0.3, -1.3, 1.55), (-0.15, 0.35, 1.0), 34, s("09-01"), e("09-05") + 0.8, (-0.1, -1.2, 1.7), (-0.05, 0.4, 1.0), 33)
    elif cl == "S10a":
        cam((-0.4, -1.7, 1.6), (-0.3, 0.4, 1.05), 32, s("10-01"), e("10-03") + 0.6, (-0.1, -1.5, 1.7), (-0.1, 0.4, 1.05), 34)
    elif cl == "S10b":
        cam((-0.2, -0.95, 1.65), (-0.25, 0.35, 1.18), 38, s("10-04"), e("10-06") + 0.8, (-0.1, -0.9, 1.6), (-0.2, 0.35, 1.18), 40)
    elif cl == "S11a":
        cam((-1.6, -0.7, 1.4), (-1.3, 1.1, 0.96), 36, s("11-01"), e("11-03") + 0.8, (-1.5, -0.5, 1.35), (-1.3, 1.1, 0.96), 40)
    elif cl == "S16a":
        cam((-0.6, -3.0, 1.6), (-0.2, 0.4, 1.0), 30, s("16-01"), e("16-03") + 0.8, (-0.4, -2.6, 1.5), (-0.2, 0.4, 1.0), 32)
    elif cl == "S20a":
        cam((0.6, -2.6, 1.55), (0.8, 0.4, 1.0), 32, s("20-01"), e("20-07") + 0.8, (1.0, -2.4, 1.5), (0.9, 0.4, 1.0), 33)
    return M


def b_shop_night(cl): return b_shop(cl, night=True)


def b_shop_day(cl):
    M = b_shop(cl)
    # 11：何も書かれていない紙の束をのぞきこむ（字は書かない）
    pm = mat("blank", "#F6F1E4", rough=0.85)
    for k_ in range(6): cube(pm, (-1.3, 1.1, 0.97 + k_ * 0.01), (0.42, 0.56, 0.008), rot=(0, 0, R(3 * k_ - 8)))
    M.at(s("11-01") - 0.6, loc=(-1.55, 0.6, 0.94), face=-20); M.at(s("11-01") + 0.3, look=25)
    M.tilt(w("11-02", "書き残して"), 15); M.tilt(e("11-03"), 0)


# ======================================================================== C：タイプライターの中（S12〜S15）
def b_inside(cl):
    world("#3A3430", 1.0)
    fm = noise_mat("insidefloor", "#5A5048", "#4A423A", scale=8, rough=0.6, bump=0.1)
    cube(fm, (0, 0, -0.05), (8, 8, 0.1))
    root, pv = typebar_basket((0, 0.6, 0.02), r=1.2, n=36)
    for ch in "ER": track("bar_" + ch, pv[ch].children[1] if len(pv[ch].children) > 1 else pv[ch], 0.05)
    # 上の方のキーの裏（暗い）・紙の筒（真ん中の打つ所）
    cyl(mat("platen_in", "#15171A", rough=0.4), (0, 1.0, 1.25), 0.25, 3.2, rot=(0, R(90), 0))
    cube(mat("paper_in", "#F4EFE3", rough=0.8), (0, 1.1, 1.7), (2.2, 0.02, 0.9))
    spot((0.0, -1.5, 2.6), (0, 0.6, 0.3), energy=3200, angle=60, col="#FFE3BC")
    area((-2.0, 1.5, 2.0), (0, 0.6, 0.3), energy=600, size=3, col="#9FB3E0")
    area((1.8, -1.8, 2.2), (0, 0.2, 0.3), energy=700, size=3, col="#FFF1D6")
    M = MaruR((0.0, -0.9, 0.0), face=0.0, s=0.26); track("maru", M.body, 0.1)
    # 12：中へ入る → 棒が跳ね上がる
    M.at(-100.0, loc=(-1.5, -2.2, 0.0), face=-30)
    M.walk(s("12-01") + 0.6, s("12-02"), (0.0, -0.9, 0.0))
    M.at(s("12-02") + 0.2, look=15)
    for i, ch in enumerate("QAZ"):
        bar_up(pv[ch], w("12-03", "跳ね上がって") + 0.4 * i); ev(w("12-03", "跳ね上がって") + 0.4 * i + 0.18, "clack", 0.6)
    M.hop(w("12-03", "跳ね上がって") + 0.05, h=0.18, d=0.4)
    # 13：となり合う 2 本が続けて上がる → ぶつかって止まる → まるロボがほどく
    a_, b_ = pv["T"], pv["Y"]; t = w("13-01", "続けて")
    key(a_, ("rotation_euler", 0), t, 0.0); key(a_, ("rotation_euler", 0), t + 0.3, R(55))
    key(b_, ("rotation_euler", 0), t + 0.1, 0.0); key(b_, ("rotation_euler", 0), t + 0.35, R(52))
    ev(t + 0.35, "clank", 0.7)
    M.walk(s("13-03") - 0.2, s("13-03") + 0.8, (0.35, 0.0, 0.0)); M.at(s("13-03") + 1.0, look=20)
    M.wobble(s("13-03") + 1.0, s("13-04"), 8, 0.3)
    key(a_, ("rotation_euler", 0), s("13-04") + 0.2, R(55)); key(a_, ("rotation_euler", 0), s("13-04") + 0.6, 0.0)
    key(b_, ("rotation_euler", 0), s("13-04") + 0.3, R(52)); key(b_, ("rotation_euler", 0), s("13-04") + 0.7, 0.0)
    ev(s("13-04") + 0.5, "snap", 0.5); M.at(s("13-04") + 0.8, look=0)
    # 14：E と R の棒を同時に光らせる（となり同士）
    for ch in "ER":
        g = glow_mat("barglow" + ch, "#FFD24A", 4.0)
        bar = pv[ch].children[0]
        gl = cube(g, (0, -1.2 * 0.45, 0.05), (0.05, 1.2 * 0.9, 0.01), parent=pv[ch]); gl.visible_shadow = False
        hide_key(gl, -100.0, True); hide_key(gl, w("14-04", "となり同士"), False); hide_key(gl, e("14-05") + 0.6, True)
    M.walk(s("14-03"), s("14-04"), (0.15, -0.1, 0.0)); M.at(w("14-04", "となり同士") + 0.2, look=22)
    M.hop(w("14-04", "となり同士") + 0.1, h=0.15, d=0.4)
    # 15：わざとゆっくり跳ねる（棒は 1 本ずつ上がって、からまない）→ ちょっと待って、で止まる
    t = s("15-03") + 0.4
    for i, ch in enumerate("GH"):
        M.hop(t + i * 1.6, h=0.12, d=0.6); bar_up(pv[ch], t + i * 1.6 + 0.4, d=0.8); ev(t + i * 1.6 + 0.8, "clack", 0.4)
    M.at(w("15-04", "ちょっと待って"), look=0); M.tilt(w("15-04", "ちょっと待って") + 0.1, 14); M.tilt(e("15-06"), 0)
    if cl == "S12a":
        cam((-1.3, -2.0, 0.55), (0.0, 0.4, 0.35), 26, s("12-01"), e("12-03") + 0.8, (-0.6, -1.8, 0.5), (0.0, 0.5, 0.4), 24)
    elif cl == "S13a":
        cam((1.3, -1.4, 0.5), (0.2, 0.6, 0.5), 30, s("13-01"), e("13-05") + 0.8, (1.1, -1.5, 0.6), (0.1, 0.6, 0.55), 30)
    elif cl == "S14a":
        cam((0.2, -1.9, 0.9), (0.0, 0.8, 0.25), 30, s("14-01"), e("14-05") + 0.8, (0.0, -1.7, 1.0), (0.0, 0.85, 0.2), 31)
    elif cl == "S15a":
        cam((-1.2, -2.3, 0.7), (0.1, 0.4, 0.35), 28, s("15-01"), e("15-10") + 0.8, (-0.6, -2.5, 0.8), (0.1, 0.4, 0.35), 27)


# ======================================================================== D：電信の部屋（S17・S18・S19a）
def b_tel(cl):
    telegraph_room()
    sd, arm = sounder((-0.6, 0.6, 0.92)); track("sounder", sd, 0.12)
    tw, tk = modern_typewriter((0.6, 0.65, 0.92), layout=["QWERTY", "ASDFG", "ZXCV"], name="tt")
    for ch in "ZSE": track("t_" + ch, tk[ch], 0.04)
    op = typist((0.6, -0.15, 0), 0, shirt="#6D5A44", hair="#3A2E24"); track("op", op.root, 1.4)
    cube(mat("chairw", "#5A3D26", rough=0.6), (0.6, -0.35, 0.45), (0.5, 0.5, 0.06))
    M = MaruR((-0.95, 0.75, 0.92), face=-20, s=0.2); track("maru", M.body, 0.1)
    # 17：受信機がカチカチ → 人が打つ
    t = s("17-01") + 0.3
    click_seq(arm, t, ".-.. -- .- .--", 0.08, 0.35)
    click_seq(arm, s("17-03") + 0.2, ". .. ... - ..-", 0.09, 0.5)
    type_motion(op, s("17-04"), e("17-04") + 0.6, 6.0, 0.25)
    for t_ in (s("17-03") + 0.2, s("17-03") + 0.9): M.blink(t_, 1.3)
    M.at(s("17-04") + 0.3, face=30)
    # 18：Z と SE（点だけの音。絵は 2D の点。後ろの部屋はゆっくり寄る）
    click_seq(arm, w("18-02", "トントントン"), "... .", 0.1, 0.6)
    click_seq(arm, w("18-04", "トントントン"), "...", 0.1, 0.6); click_seq(arm, w("18-04", "E が") + 0.25, ".", 0.1, 0.6)
    M.at(s("18-05"), face=-30); M.at(s("18-05") + 0.6, face=30); M.tilt(e("18-05") - 0.2, 14); M.tilt(e("18-05") + 0.6, 0)
    # 19a：打つ人が迷う（手が止まる）
    a0, a1 = op.arms
    for t_ in (s("19-01") + 0.4, s("19-01") + 1.2, s("19-01") + 2.0):
        key(a0, ("rotation_euler", 2), t_, R(-8)); key(a0, ("rotation_euler", 2), t_ + 0.4, R(10))
    if cl == "S17a":
        cam((-2.2, -2.2, 1.6), (0.0, 0.6, 1.0), 28, s("17-01"), e("17-04") + 0.8, (-1.8, -2.0, 1.5), (0.0, 0.6, 1.0), 30)
    elif cl == "S18a":
        cam((-0.9, -0.6, 1.3), (-0.6, 0.6, 0.98), 40, s("18-01"), e("18-05") + 0.8, (-0.8, -0.4, 1.25), (-0.6, 0.6, 0.98), 44)
    elif cl == "S19a":
        cam((2.2, -1.6, 2.0), (0.6, 0.55, 1.0), 34, s("19-01"), e("19-02") + 0.6, (2.0, -1.4, 1.9), (0.6, 0.55, 1.0), 36)


def b_school(cl):
    """17-05：電信の打ち方を教える学校（同じ形の机が並ぶ）／22-01〜22-02：打ち方の教室"""
    hall(col_wall="#D9CDB8")
    T_ = []
    cols = ["#5B6E86", "#6D5A44", "#7E57C2", "#4F81BD", "#9BBB59", "#C0504D", "#8A6446", "#3E7CB1"]
    for r in range(2):
        for c in range(4):
            x, y = -2.4 + c * 1.6, 0.8 - r * 1.7
            cube(mat("sdesk", "#7B5638", rough=0.5), (x, y, 0.74), (1.1, 0.6, 0.05))
            modern_typewriter((x, y + 0.05, 0.77), name="s%d%d" % (r, c), col="#262626")[0].scale = (0.35, 0.35, 0.35)
            tp = typist((x, y - 0.55, 0), 0, shirt=cols[r * 4 + c]); T_.append(tp)
            cube(mat("schair", "#5A3D26", rough=0.6), (x, y - 0.75, 0.45), (0.45, 0.45, 0.05))
    for i, tp in enumerate(T_): type_motion(tp, CLOCK["T0"] + 0.2 * i, CLOCK["T0"] + 30, 5.0 + 0.3 * (i % 3), 0.06 if i < 2 else 0.0)
    cube(mat("board", "#2E3B33", rough=0.8), (0, 3.85, 2.0), (3.0, 0.05, 1.3))       # 黒板（字は書かない）
    M = MaruR((-3.4, 1.0, 0.0), face=-60); track("maru", M.body, 0.1)
    M.at(-100.0, loc=(-3.4, 1.4, 0.0), face=0.0)
    if cl == "S22a":
        M.at(s("22-01"), loc=(-3.0, -1.4, 0.0), face=-30); M.hop(s("22-02") + 0.4, h=0.15, d=0.4)
        cam((-4.5, -4.0, 2.4), (-0.4, 0.2, 0.8), 28, s("22-01"), e("22-02") + 0.8, (-4.0, -3.6, 2.2), (0.0, 0.2, 0.8), 30)
    else:
        cam((4.4, -3.8, 2.5), (0.0, 0.2, 0.8), 28, s("17-05"), e("17-05") + 0.8, (4.0, -3.4, 2.3), (-0.2, 0.2, 0.8), 30)


def b_demo(cl):
    """17-06〜17-09：電信の会社のえらい人の前で試し打ち（えらい人がモールス信号を送り、先生がタイプライターで打つ）"""
    hall(col_wall="#CBB89A", floor=("#7A5233", "#6B4A30"))
    cube(mat("demotable", "#6B4A30", rough=0.5), (0, 0.8, 0.76), (3.0, 0.9, 0.05))
    mk_, lever = morse_key((-0.9, 0.75, 0.79))
    boss = person((-0.9, 0.2, 0), 0, shirt="#1F2630", pants="#1A1E26", hair="#6A6A6A")
    cube(mat("bosschair", "#4A3220", rough=0.6), (-0.9, 0.0, 0.45), (0.55, 0.5, 0.06))
    tw, tk = modern_typewriter((0.8, 0.85, 0.79), name="tdm"); tw.scale = (0.45, 0.45, 0.45)
    tch = typist((0.8, 0.25, 0), 0, shirt="#6D5A44", hair="#3A2E24"); track("teacher", tch.root, 1.75)
    track("boss", boss, 1.75)
    cube(mat("tchair", "#4A3220", rough=0.6), (0.8, 0.05, 0.45), (0.5, 0.5, 0.06))
    for k in range(5):     # 見ている人たち（立っている）
        wk = walker((-2.6 + k * 1.3, 2.4, 0), face=180, shirt=["#3E4A5A", "#5A4632", "#4A3A5A", "#2D3640", "#6D5A44"][k], s=0.96)
    M = MaruR((0.0, -0.4, 0.0), face=0.0); track("maru", M.body, 0.1)
    t = s("17-07"); tend = e("17-08") + 0.8
    k_ = 0; tt = t
    while tt < tend:
        d = 0.08 if k_ % 3 else 0.22
        key(lever, ("rotation_euler", 1), tt, 0.0); key(lever, ("rotation_euler", 1), tt + 0.02, R(-6)); key(lever, ("rotation_euler", 1), tt + d, R(-6)); key(lever, ("rotation_euler", 1), tt + d + 0.02, 0.0)
        ev(tt, "tick", 0.3); tt += d + 0.09; k_ += 1
    type_motion(tch, t + 0.3, tend, 6.5, 0.15)
    M.at(s("17-07"), face=-30); M.at(s("17-07") + 1.2, face=30); M.at(s("17-08"), face=-30); M.at(s("17-08") + 0.8, face=30)
    M.glow(w("17-08", "なんと"), 1.8, 0.2); M.glow(e("17-08"), 0.9, 0.4)
    cam((0.2, -3.0, 1.8), (0.0, 0.7, 1.0), 30, s("17-06"), e("17-09") + 0.8, (0.0, -2.6, 1.6), (0.0, 0.7, 1.0), 32)


# ======================================================================== E：広まっていく（S22b〜S22e）・速い並びの実験（S23b・S23c）・事務所（S24a・S24b）
def b_contest(cl):
    hall(col_wall="#D6C3A0", lamps=5)
    for k in range(10):    # 見ている人（座っている）
        person((-3.0 + (k % 5) * 1.5, -2.0 - (k // 5) * 1.0, 0), 180 + 0, shirt=["#3E4A5A", "#5A4632", "#4A3A5A", "#2D3640", "#6D5A44"][k % 5])
    cube(mat("stage", "#6B4A30", rough=0.5), (0, 1.0, 0.2), (5.0, 2.4, 0.4))
    for x, col in ((-1.0, "#2B2B2B"), (1.0, "#3A3A3A")):
        cube(mat("ctable", "#7B5638", rough=0.5), (x, 1.2, 1.14), (1.1, 0.6, 0.05))
        modern_typewriter((x, 1.25, 1.17), name="c%d" % int(x), col=col)[0].scale = (0.35, 0.35, 0.35)
    a = typist((-1.0, 0.6, 0.4), 0, shirt="#5B6E86", hair="#2B2220"); b = typist((1.0, 0.6, 0.4), 0, shirt="#8A6446", hair="#5A4A3A")
    track("winner", a.root, 1.7)
    type_motion(a, s("22-03"), e("22-04") + 0.8, 8.0, 0.2); type_motion(b, s("22-03"), e("22-04") + 0.8, 3.5, 0.05)
    flag = empty((-1.0, 0.6, 2.4)); cyl(mat("pole", "#C9A24E", rough=0.3, metal=0.8), (0, 0, 0), 0.015, 0.5, parent=flag)
    cube(mat("flag", "#E23A30", rough=0.6), (0.14, 0, 0.15), (0.26, 0.01, 0.18), parent=flag)
    hide_key(flag, -100.0, True); hide_key(flag, w("22-03", "勝ちました"), False); scale_pop(flag, w("22-03", "勝ちました"), 1.0, 0.4)
    ev(w("22-03", "勝ちました"), "pop", 0.6)
    M = MaruR((-2.6, 0.2, 0.4), face=-20); track("maru", M.body, 0.1)
    M.at(s("22-03") + 0.5, face=20); M.at(s("22-03") + 1.6, face=-20); M.at(w("22-03", "勝ちました") + 0.3, face=10)
    M.hop(w("22-03", "勝ちました") + 0.3, h=0.15, d=0.4)
    cam((0.0, -4.4, 2.2), (0.0, 0.9, 1.4), 30, s("22-03"), e("22-04") + 0.8, (0.6, -4.0, 2.0), (-0.3, 0.9, 1.4), 34)


def b_factory(cl):
    """10-07〜10-09：大きな会社の工場（機械が並ぶ）／22-05：機械がどんどん増えていく（列になって運ばれる）"""
    hall(col_wall="#A88E74", floor=("#6E6458", "#625A50"), lamps=5, w=14, d=12)
    for k in range(4):   # 大きな歯車（奥の壁。回る）
        g = cyl(mat("gear", "#A39686", rough=0.4, metal=0.6), (-4.5 + k * 3.0, 4.75, 2.9), 0.42, 0.12, rot=(R(90), 0, 0), verts=24)
        key(g, ("rotation_euler", 1), CLOCK["T0"] - 1, 0.0, "LINEAR"); key(g, ("rotation_euler", 1), CLOCK["T0"] + 60, R(360 * (1 if k % 2 else -1) * 3), "LINEAR")
    belt = mat("belt", "#2A2622", rough=0.7)
    cube(belt, (0, 1.6, 0.8), (12.0, 0.8, 0.08))
    tws = []
    for k in range(9):
        tw, _ = modern_typewriter((-6 + k * 1.5, 1.6, 0.84), name="f%d" % k, col="#2B2B2B"); tw.scale = (0.4, 0.4, 0.4)
        key(tw, ("location", 0), CLOCK["T0"] - 1, -6 + k * 1.5, "LINEAR"); key(tw, ("location", 0), CLOCK["T0"] + 40, -6 + k * 1.5 + 12.0, "LINEAR")
        tws.append(tw)
    for k in range(3):
        wk = walker((-3 + k * 3, 2.6, 0), face=180, shirt=["#4A5A6A", "#6A5A44", "#3E4A5A"][k], apron=True)
    M = MaruR((0.6, -0.8, 0.0), face=0.0); track("maru", M.body, 0.1)
    if cl == "S10c":
        # 10-07：台車で運ばれてくる機械（運ぶ所を見せてから、作業台へ）→ 10-08：ピリオドが外れて R が入る
        cube(mat("fbench", "#7B5638", rough=0.5), (0.4, -0.3, 0.86), (1.4, 0.8, 0.05))
        tw, tk = modern_typewriter((0.4, -0.25, 0.89), layout=["QWE.TY", "ASDFG", "ZXCV"], name="fx")
        tw.scale = (0.5, 0.5, 0.5)
        for ch in "QWE.TY": track("f_" + ("dot" if ch == "." else ch), tk[ch], 0.03)
        cart = empty((0, 0, 0)); cube(mat("cart", "#6B4A30", rough=0.6), (0, 0, 0.5), (0.9, 0.6, 0.06), parent=cart)
        for sx in (-0.35, 0.35): cyl(mat("wheel", "#2A2622", rough=0.5), (sx, 0, 0.12), 0.12, 0.05, rot=(0, R(90), 0), parent=cart)
        pusher = walker((-4.2, -0.4, 0), face=-90, shirt="#4A5A6A", apron=True)
        key(cart, "location", s("10-07") - 0.5, (-3.5, -0.4, 0)); key(cart, "location", s("10-07") + 2.0, (-0.6, -0.4, 0))
        key(pusher.root, "location", s("10-07") - 0.5, (-4.2, -0.4, 0)); key(pusher.root, "location", s("10-07") + 2.0, (-1.3, -0.4, 0))
        key(tw, "location", s("10-07") - 0.5, (-3.5, -0.4, 0.56)); key(tw, "location", s("10-07") + 2.0, (-0.6, -0.4, 0.56))
        key(tw, "location", s("10-07") + 2.6, (0.4, -0.25, 0.89))
        ev(s("10-07") + 0.2, "motor_on", 1.0); ev(s("10-07") + 2.0, "motor_off", 1.0); ev(s("10-07") + 2.6, "clank", 0.4)
        dot = tk["."]; rk = cyl(mat("fx_keytop", "#F1EEE6", rough=0.3, coat=0.5), (dot.location.x, dot.location.y, dot.location.z + 0.5), 0.13 * 0.34, 0.025, parent=tw)
        track("f_R", rk, 0.03)
        hide_key(rk, -100.0, True)
        t = w("10-08", "外され"); key(dot, ("location", 2), t, dot.location.z); key(dot, ("location", 2), t + 0.4, dot.location.z + 0.6); hide_key(dot, t + 0.45, True)
        ev(t + 0.05, "pop", 0.5)
        t = w("10-08", "R が"); hide_key(rk, t, False); key(rk, ("location", 2), t, dot.location.z + 0.6); key(rk, ("location", 2), t + 0.35, dot.location.z)
        ev(t + 0.35, "snap", 0.6)
        M.at(-100.0, loc=(1.4, -0.9, 0.0), face=40)
        M.hop(s("10-08") - 0.6, h=1.0, d=0.6); M.at(s("10-08") - 0.6, loc=(1.3, -0.9, 0.0)); M.at(s("10-08"), loc=(1.0, -0.45, 0.89))
        M.at(s("10-08") + 0.2, face=60, look=12); M.hop(s("10-09") + 0.4, h=0.12, d=0.4)
        cam((1.8, -3.2, 2.0), (0.0, -0.2, 0.9), 30, s("10-07"), e("10-09") + 0.8, (1.6, -2.2, 1.6), (0.4, -0.2, 0.95), 38)
    else:
        M.at(-100.0, loc=(0.6, 0.4, 0.0), face=0.0)
        M.walk(s("22-05") + 0.2, e("22-05") + 0.6, (2.6, 0.6, 0.0))
        cam((-1.0, -4.2, 2.6), (0.6, 1.4, 0.8), 26, s("22-05"), e("22-05") + 0.8, (0.6, -4.0, 2.4), (1.6, 1.4, 0.8), 26)


def b_merge(cl):
    """22-06〜22-07：5 つの会社（建物）が 1 つにまとまる（字は 2D で年だけ）"""
    world("#BFD6EA", 0.9); sun((50, 0, 30), energy=3.2)
    ground("#9CC47F", 60, 0.0, 0.9)
    cube(mat("road", "#8A8F96", rough=0.8), (0, -2.0, 0.005), (30, 1.6, 0.01))
    cols = ["#B5502F", "#5B6E86", "#8A6446", "#7E57C2", "#4F81BD"]
    for k, col in enumerate(cols):
        x0 = -6 + k * 3.0
        b = empty((x0, 1.0, 0)); h = 2.0 + 0.3 * k
        cube(mat("bld" + col, col, rough=0.8), (0, 0, h / 2), (2.0, 1.6, h), parent=b)
        cube(mat("roof" + col, "#4A3A30", rough=0.7), (0, 0, h + 0.1), (2.2, 1.8, 0.2), parent=b)
        for j in range(3):
            for i in range(3): cube(mat("bwin", "#F3E6C4", rough=0.4, emit=0.6), (-0.6 + 0.6 * i, -0.81, 0.5 + j * 0.6), (0.35, 0.02, 0.35), parent=b)
        t = w("22-06", "1つに")
        key(b, "location", t - 0.2, (x0, 1.0, 0)); key(b, "location", t + 1.4, (0.0, 1.0, 0))
        key(b, "scale", t + 1.0, (1, 1, 1)); key(b, "scale", t + 1.4, (0.001, 0.001, 0.001) if k else (1.0, 1.0, 1.0))
    big = empty((0, 1.0, 0))
    cube(mat("bigbld", "#C9B79A", rough=0.8), (0, 0, 2.0), (5.0, 2.4, 4.0), parent=big)
    cube(mat("bigroof", "#4A3A30", rough=0.7), (0, 0, 4.15), (5.3, 2.7, 0.3), parent=big)
    for j in range(5):
        for i in range(7): cube(mat("bwin", "#F3E6C4", rough=0.4, emit=0.6), (-2.1 + 0.7 * i, -1.21, 0.6 + j * 0.7), (0.4, 0.02, 0.4), parent=big)
    hide_key(big, -100.0, True); hide_key(big, w("22-06", "1つに") + 1.3, False); scale_pop(big, w("22-06", "1つに") + 1.3, 1.0, 0.5)
    ev(w("22-06", "1つに") + 1.3, "pop", 0.7)
    M = MaruR((0.0, -2.6, 0.0), face=180 - 180); track("maru", M.body, 0.1)
    M.at(-100.0, loc=(-1.0, -2.4, 0.0), face=10)
    M.at(w("22-06", "1つに") + 1.5, look=20); M.hop(w("22-06", "1つに") + 1.6, h=0.15, d=0.4)
    cam((0.0, -10.0, 3.6), (0.0, 1.0, 1.6), 26, s("22-06"), e("22-07") + 0.8, (0.0, -9.0, 3.2), (0.0, 1.0, 1.8), 28)


def b_evolve(cl):
    """22-08：タイプライター → 電報の機械 → 今のキーボード（並びは全部同じ。カメラが横へ動く）"""
    world("#5A6270", 1.0)
    fm = noise_mat("evofloor", "#6A707A", "#5E646E", scale=6, rough=0.4)
    cube(fm, (0, 0, -0.05), (20, 6, 0.1))
    for k, x in enumerate((-3.0, 0.0, 3.0)):
        cyl(mat("ped", "#8A909A", rough=0.4, metal=0.2), (x, 0, 0.4), 0.9, 0.8)
        spot((x, -1.5, 3.5), (x, 0, 0.9), energy=1600, angle=40, col="#FFE3BC")
    area((0, -4, 4), (0, 0, 0.8), energy=600, size=8, col="#FFFFFF")
    tw, _ = modern_typewriter((-3.0, 0.0, 0.8), name="ev1"); tw.scale = (0.6, 0.6, 0.6)
    tele = empty((0.0, 0.0, 0.8))
    cube(mat("teleb", "#5B6155", rough=0.5), (0, 0, 0.35), (1.2, 0.9, 0.7), bevel=0.05, parent=tele)
    cube(mat("telek", "#2A2E33", rough=0.4), (0, -0.25, 0.75), (1.0, 0.4, 0.12), bevel=0.03, parent=tele)
    cyl(mat("telepaper", "#F4EFE3", rough=0.8), (0, 0.2, 0.85), 0.12, 0.8, rot=(0, R(90), 0), parent=tele)
    kb = Board(ROWS_Q, (2.25, 0.25), k=0.06, name="ev3", extra_rows=True); kb.root.location = (0, 0, 0.82)
    M = MaruR((-3.6, -1.4, 0.0), face=0.0); track("maru", M.body, 0.1)
    M.walk(s("22-08") + 0.2, e("22-08") + 1.2, (3.0, -1.4, 0.0))
    cam((-3.0, -4.2, 2.0), (-3.0, 0.0, 0.9), 32, s("22-08"), e("22-08") + 1.2, (3.0, -4.2, 2.0), (3.0, 0.0, 0.9), 32)


def b_lab(cl):
    """23-05：「速い」実験の部屋（考えた本人が、打つ人の横で見ている）／23-06〜23-07：別の人たちで比べ直す（2D の棒グラフはほぼ同じ）"""
    hall(col_wall="#D8DCD2", floor=("#8A8A80", "#7E7E74"), lamps=3)
    if cl == "S23b":
        cube(mat("labdesk", "#7B5638", rough=0.5), (0, 0.6, 0.74), (1.4, 0.7, 0.05))
        modern_typewriter((0, 0.65, 0.77), name="lb", col="#2E3A2E")[0].scale = (0.4, 0.4, 0.4)
        tp = typist((0, 0.0, 0), 0, shirt="#4F81BD", hair="#3A2E24"); type_motion(tp, s("23-05"), e("23-05") + 1, 7.0, 0.15)
        prof = walker((1.0, 0.1, 0), face=120, shirt="#5A5A5A", pants="#2D3640", hair="#BBBBBB"); track("prof", prof.head, 0.3)
        cube(mat("clipb", "#C9A96B", rough=0.6), (0.85, -0.15, 1.15), (0.25, 0.02, 0.32), rot=(R(-20), 0, R(30)))
        M = MaruR((-1.3, -0.6, 0.0), face=-30); track("maru", M.body, 0.1)
        M.at(s("23-05") + 0.6, face=40); M.tilt(w("23-05", "考えた本人"), 12); M.tilt(e("23-05") + 0.4, 0)
        cam((-1.6, -2.8, 1.8), (0.3, 0.4, 1.0), 30, s("23-05"), e("23-05") + 0.8, (-1.3, -2.6, 1.7), (0.3, 0.4, 1.0), 32)
    else:
        T_ = []
        for k in range(6):
            x = -2.5 + k * 1.0
            cube(mat("labdesk", "#7B5638", rough=0.5), (x, 0.6, 0.74), (0.8, 0.6, 0.05))
            modern_typewriter((x, 0.65, 0.77), name="lc%d" % k, col="#2E3A2E" if k % 2 else "#2B2B2B")[0].scale = (0.28, 0.28, 0.28)
            tp = typist((x, 0.05, 0), 0, shirt=["#4F81BD", "#C0504D", "#9BBB59", "#7E57C2", "#E8A04D", "#5B6E86"][k]); T_.append(tp)
            type_motion(tp, s("23-06") + 0.1 * k, e("23-07") + 1, 6.0, 0.04 if k < 2 else 0.0)
        M = MaruR((-3.3, -0.8, 0.0), face=-20); track("maru", M.body, 0.1)
        M.at(w("23-06", "はっきり") + 0.5, look=10); M.tilt(w("23-06", "はっきり") + 0.6, 14); M.tilt(e("23-07") + 0.3, 0)
        cam((-4.2, -3.4, 2.2), (-0.6, 0.4, 0.9), 26, s("23-06"), e("23-07") + 0.8, (-3.8, -3.2, 2.0), (-0.2, 0.4, 0.9), 27)


def b_office(cl):
    """24-01〜24-05：今の事務所（どの机のキーボードも同じ並び）。24-04〜24-05 は「もしも」：キーが入れかわり、指が止まる"""
    office_room()
    T_ = []
    cols = ["#3E7CB1", "#C0504D", "#9BBB59", "#7E57C2", "#E8A04D", "#5B6E86", "#4F81BD", "#8A6446"]
    kbs = []
    for r in range(2):
        for c in range(4):
            root, tp, kb = office_desk(-3.6 + c * 2.3, 1.6 - r * 2.0, 0, shirt=cols[r * 4 + c]); T_.append(tp); kbs.append(kb)
    t_if = s("24-04") + 0.3
    for i, tp in enumerate(T_):
        type_motion(tp, CLOCK["T0"], t_if, 6.0 + 0.4 * (i % 3), 0.05 if i < 2 else 0.0)
        a0, a1 = tp.arms
        for a in (a0, a1): key(a, ("rotation_euler", 0), t_if + 0.6, R(-62)); key(a, ("rotation_euler", 0), t_if + 1.0, R(-45))
    for kb in kbs:
        key(kb, ("rotation_euler", 2), t_if, 0.0); key(kb, ("rotation_euler", 2), t_if + 0.8, R(360))
    ev(t_if + 0.1, "whoosh", 0.4)
    M = MaruR((0.2, -2.6, 0.0), face=0.0); track("maru", M.body, 0.1)
    M.walk(s("24-02") + 0.2, s("24-03") + 1.0, (-0.6, -1.0, 0.0))
    M.at(t_if + 0.8, face=-30); M.at(t_if + 1.6, face=30); M.wobble(s("24-05"), e("24-05"), 8, 0.4)
    if cl == "S24a":
        cam((-5.5, -4.6, 3.2), (-0.5, 0.8, 0.8), 26, s("24-01"), e("24-03") + 0.8, (-4.8, -4.2, 3.0), (0.0, 0.8, 0.8), 27)
    else:
        cam((2.8, -4.4, 2.6), (-0.6, 0.6, 0.9), 28, s("24-04"), e("24-05") + 0.8, (2.4, -4.0, 2.4), (-0.6, 0.6, 0.9), 29)


# ======================================================================== クリップの一覧
#   CUTS：カットの名前・組み立て・切り替わる時刻（＝その文の字幕が出る時刻）。組み立てでは 0.35 秒（章の変わり目は 0.6 秒）で溶かしてつなぐ
def _desk(cl):
    S_ = b_desk(cl); b_desk_cam(cl, S_)


# ---- カット割り（2026-11-15 ユーザー「場面が変わり映えしないのが多いので気をつけてね」）：同じ絵を 12 秒以上続けない。
#   文の切れ目で、寄り・引き・真上・横・まるロボを追う絵に替える。親（舞台と動きを作るクリップ）はそのまま、カメラだけ替える
def F(off, lens=40, dz=0.05, t0=None, t1=None, off1=None):
    """まるロボを追うカメラ（体は跳ねても揺れないよう、足もとの root を追う）。off＝まるロボからのずれ（世界の向き）"""
    c = cam_follow(_M_[0].root, off, dz, lens)
    if t0 is not None: key(c, "location", t0, off); key(c, "location", t1, off1)
    return c


def C(loc, tgt, lens=35, loc1=None, tgt1=None, lens1=None, d=8.0):
    """決まったカメラ（カットの頭から d 秒かけて、ゆっくり動く）"""
    def mk(t0):
        return cam(loc, tgt, lens, t0, t0 + d, loc1 or loc, tgt1 or tgt, lens1 or lens)
    return mk


def TOP(loc, loc1=None, lens=32, d=8.0):
    def mk(t0):
        return topcam(loc, loc1 or loc, t0, t0 + d, lens)
    return mk


CUTS = [   # (名前, 舞台, 切り替わる時刻, カメラ（None＝舞台のカメラ）, 親)
    ("S01a", _desk, 0.0, None, "S01a"), ("S01b", _desk, s("01-03"), lambda t0: F((0.35, -0.75, 0.22), 40), "S01a"),
    ("S02a", _desk, s("02-01"), None, "S02a"), ("S02b", _desk, s("02-03"), lambda t0: F((-0.55, -0.55, 0.3), 34), "S02a"),
    ("S03a", _desk, s("03-01"), None, "S03a"), ("S03a2", _desk, s("03-02"), C((-0.2, -0.95, 0.35), (-0.1, 0.5, 0.1), 30, (0.1, -0.9, 0.35)), "S03a"), ("S03b", _desk, s("03-03"), C((1.6, -1.3, 0.45), (-0.2, 0.3, 0.1), 24, (1.3, -1.1, 0.4), (-0.3, 0.3, 0.1)), "S03a"),
    ("S03c", _desk, s("03-05"), lambda t0: F((0.2, -0.8, 0.3), 38, 0.05, t0, t0 + 6, (0.4, -0.95, 0.35)), "S03a"),
    ("S04a", _desk, s("04-01"), lambda t0: F((0.45, -0.7, 0.28), 38), "S04a"), ("S04b", _desk, s("04-03"), None, "S04a"),
    ("S05a", _desk, s("05-01"), None, "S05a"), ("S05a2", _desk, s("05-02"), lambda t0: F((0.3, -0.7, 0.25), 38), "S05a"), ("S05b", _desk, s("05-04"), lambda t0: F((0.0, -0.95, 0.85), 30), "S05a"),
    ("S05c", _desk, s("05-05"), C((3.7, -1.3, 0.9), (2.2, 0.3, 0.0), 30, (3.5, -1.5, 1.0)), "S05a"),
    ("S06a", _desk, s("06-01"), None, "S06a"), ("S06b", _desk, s("06-04"), lambda t0: F((0.3, -0.7, 0.25), 40), "S06a"),
    ("S07a", _desk, s("07-01"), None, "S07a"), ("S07a2", _desk, s("07-03"), C((-1.4, -1.2, 0.5), (1.0, 0.3, 0.0), 26, (-1.2, -1.4, 0.6)), "S07a"), ("S07b", _desk, s("07-04"), C((1.2, -2.3, 0.75), (1.2, 0.3, 0.0), 26, (1.0, -2.1, 0.7)), "S07a"),
    ("S07b2", _desk, s("07-05"), TOP((1.05, 0.2, 3.6), (1.05, 0.2, 3.8)), "S07a"), ("S07c", _desk, s("07-06"), lambda t0: F((-0.4, -0.7, 0.3), 38), "S07a"), ("S07c2", _desk, s("07-07"), C((3.4, -1.6, 0.9), (1.0, 0.3, 0.0), 28, (3.2, -1.8, 1.0)), "S07a"), ("S07d", _desk, s("07-08"), TOP((1.05, 0.2, 3.2), (1.05, 0.2, 4.4)), "S07a"),
    ("S07e", _desk, s("07-10"), C((0.9, -3.6, 1.6), (0.9, 1.5, 1.2), 28, (0.9, -2.2, 1.5), (0.9, 2.0, 1.8)), "S07a"),
    ("S08a", b_shop_day, s("08-01"), None, "S08a"), ("S08a2", b_shop_day, s("08-02"), C((1.6, -0.7, 1.5), (1.7, 1.5, 1.25), 32, (1.4, -0.6, 1.45)), "S08a"), ("S08b", b_shop_day, s("08-03"), C((-0.7, -0.7, 1.35), (-0.35, 0.45, 1.0), 34, (-0.5, -0.65, 1.3)), "S08a"),
    ("S09a", b_shop_day, s("09-01"), None, "S09a"), ("S09b", b_shop_day, s("09-04"), C((-0.05, 0.1, 2.7), (-0.05, 0.42, 0.98), 26, (0.0, 0.12, 2.6)), "S09a"),
    ("S10a", b_shop_day, s("10-01"), None, "S10a"), ("S10a2", b_shop_day, s("10-03"), C((0.3, -0.75, 1.35), (0.0, 0.35, 1.12), 34, (0.1, -0.7, 1.4)), "S10a"),
    ("S10b", b_shop_day, s("10-04"), None, "S10b"), ("S10b1", b_shop_day, s("10-05"), C((-0.25, 0.15, 1.95), (-0.25, 0.36, 1.15), 35, (-0.2, 0.15, 1.9)), "S10b"), ("S10b2", b_shop_day, s("10-06"), lambda t0: F((0.4, -0.6, 0.25), 38), "S10b"),
    ("S10c", b_factory, s("10-07"), None, "S10c"), ("S10c2", b_factory, s("10-08"), C((0.95, -1.1, 1.4), (0.4, -0.2, 0.95), 40, (0.8, -1.0, 1.35)), "S10c"),
    ("S11a", b_shop_day, s("11-01"), None, "S11a"), ("S11b", b_shop_day, s("11-03"), C((-0.6, -3.6, 1.6), (-0.6, 0.3, 0.9), 28, (-0.3, -3.3, 1.5)), "S11a"),
    ("S12a", b_inside, s("12-01"), None, "S12a"), ("S12b", b_inside, s("12-03"), C((0.45, -0.55, 0.5), (0.0, 0.7, 0.25), 28, (0.3, -0.5, 0.55)), "S12a"),
    ("S13a", b_inside, s("13-01"), None, "S13a"), ("S13b", b_inside, s("13-03"), C((0.0, -0.5, 2.4), (0.0, 0.6, 0.0), 26, (0.2, -0.3, 2.2)), "S13a"),
    ("S13c", b_inside, s("13-05"), lambda t0: F((0.35, -0.75, 0.25), 36), "S13a"),
    ("S14a", b_inside, s("14-01"), None, "S14a"), ("S14b", b_inside, s("14-03"), C((0.35, 0.0, 1.6), (0.0, 0.9, 0.0), 32, (0.2, 0.1, 1.5)), "S14a"),
    ("S14b2", b_inside, s("14-05"), lambda t0: F((0.3, -0.7, 0.2), 36), "S14a"), ("S15a", b_inside, s("15-01"), None, "S15a"), ("S15b", b_inside, s("15-03"), lambda t0: F((0.4, -0.8, 0.22), 36), "S15a"),
    ("S15c", b_inside, s("15-05"), C((0.0, -0.4, 2.5), (0.0, 0.6, 0.0), 26, (-0.2, -0.3, 2.3)), "S15a"),
    ("S15d", b_inside, s("15-07"), C((-1.6, -2.0, 0.45), (0.2, 0.6, 0.35), 24, (-1.2, -2.2, 0.5)), "S15a"),
    ("S15e", b_inside, s("15-09"), lambda t0: F((0.0, -0.8, 0.2), 38), "S15a"),
    ("S16a", b_shop_day, s("16-01"), None, "S16a"), ("S16b", b_shop_day, s("16-03"), C((0.3, -0.9, 1.4), (0.0, 0.4, 1.1), 34, (0.1, -0.85, 1.35)), "S16a"),
    ("S17a", b_tel, s("17-01"), None, "S17a"), ("S17a2", b_tel, s("17-03"), C((-0.95, -0.5, 1.25), (-0.6, 0.6, 0.98), 40, (-0.85, -0.45, 1.2)), "S17a"),
    ("S17a3", b_tel, s("17-04"), C((2.0, -1.4, 1.9), (0.6, 0.6, 0.95), 32, (1.8, -1.2, 1.8)), "S17a"),
    ("S17b", b_school, s("17-05"), None, "S17b"),
    ("S17c", b_demo, s("17-06"), None, "S17c"), ("S17c2", b_demo, s("17-07"), C((1.6, -2.4, 2.3), (-0.5, 0.5, 0.9), 26, (1.4, -2.2, 2.2)), "S17c"),
    ("S17c3", b_demo, s("17-08"), C((2.3, -0.5, 1.95), (0.8, 0.85, 0.95), 34, (2.2, -0.4, 1.9)), "S17c"),
    ("S17c4", b_demo, s("17-09"), lambda t0: F((0.4, -0.8, 0.3), 36), "S17c"),
    ("S18a", b_tel, s("18-01"), None, "S18a"), ("S18a2", b_tel, s("18-02"), C((-0.6, -1.3, 1.6), (-0.6, 0.6, 0.95), 30, (-0.5, -1.2, 1.55)), "S18a"), ("S18b", b_tel, s("18-04"), lambda t0: F((0.3, -0.5, 0.15), 38), "S18a"),
    ("S18c", b_tel, s("18-05"), C((-2.2, -2.2, 1.6), (0.0, 0.6, 1.0), 28, (-1.9, -2.0, 1.5)), "S18a"),
    ("S19a", b_tel, s("19-01"), None, "S19a"),
    ("S19a2", b_tel, s("19-02"), C((0.6, 0.0, 1.6), (0.6, 0.62, 0.95), 36, (0.65, 0.05, 1.55)), "S19a"), ("S19b", _desk, s("19-03"), None, "S19b"), ("S19b2", _desk, s("19-05"), TOP((-0.3, 0.3, 1.6), (-0.1, 0.3, 2.2)), "S19b"),
    ("S20a", b_shop_night, s("20-01"), None, "S20a"), ("S20b", b_shop_night, s("20-03"), lambda t0: F((0.3, -0.7, 0.2), 38), "S20a"),
    ("S20c", b_shop_night, s("20-04"), C((0.5, -1.7, 1.6), (1.25, 0.15, 1.0), 32, (0.7, -1.6, 1.55)), "S20a"),
    ("S20c2", b_shop_night, s("20-05"), C((1.6, -0.1, 1.7), (1.6, 0.3, 1.1), 36, (1.65, -0.05, 1.65)), "S20a"), ("S20d", b_shop_night, s("20-06"), C((-0.8, -2.0, 1.4), (1.0, 0.4, 1.0), 30, (-0.6, -1.8, 1.35)), "S20a"),
    ("S20e", b_shop_night, s("20-07"), C((0.45, -1.35, 1.3), (0.85, -0.25, 1.05), 36, (0.55, -1.25, 1.25)), "S20a"),
    ("S21a", _desk, s("21-01"), None, "S21a"), ("S21b", _desk, s("21-03"), TOP((0.0, 0.2, 1.8), (0.4, 0.2, 3.4)), "S21a"),
    ("S22a", b_school, s("22-01"), None, "S22a"),
    ("S22a2", b_school, s("22-02"), lambda t0: F((0.4, -0.8, 0.3), 36), "S22a"), ("S22b", b_contest, s("22-03"), None, "S22b"), ("S22b2", b_contest, s("22-04"), C((-1.6, -0.2, 1.7), (-1.0, 1.2, 1.3), 34, (-1.5, -0.1, 1.65)), "S22b"),
    ("S22c", b_factory, s("22-05"), None, "S22c"),
    ("S22d", b_merge, s("22-06"), None, "S22d"), ("S22d2", b_merge, s("22-07"), lambda t0: F((0.8, -1.4, 0.3), 30, 0.4), "S22d"),
    ("S22e", b_evolve, s("22-08"), None, "S22e"),
    ("S23a", _desk, s("23-01"), lambda t0: F((0.4, -0.7, 0.3), 38), "S23a"), ("S23a2", _desk, s("23-03"), lambda t0: F((0.2, -0.9, 0.6), 32), "S23a"),
    ("S23a3", _desk, s("23-04"), TOP((1.05, 0.2, 3.4), (1.05, 0.2, 3.9)), "S23a"),
    ("S23a1", _desk, s("23-02"), None, "S23a"), ("S23b", b_lab, s("23-05"), None, "S23b"), ("S23c", b_lab, s("23-06"), None, "S23c"),
    ("S23c2", b_lab, s("23-07"), lambda t0: F((0.4, -0.8, 0.3), 36), "S23c"), ("S24a", b_office, s("24-01"), None, "S24a"), ("S24a2", b_office, s("24-03"), C((-1.9, -3.0, 1.5), (-0.6, -0.6, 0.6), 30, (-1.6, -2.8, 1.45)), "S24a"),
    ("S24b", b_office, s("24-04"), None, "S24b"),
    ("S24c", _desk, s("24-06"), None, "S24c"), ("S24c1", _desk, s("24-07"), TOP((-0.1, -1.6, 1.7), (-0.1, -1.5, 1.9)), "S24c"), ("S24c2", _desk, s("24-08"), lambda t0: F((0.4, -0.7, 0.3), 36), "S24c"),
    ("S24c3", _desk, s("24-09"), C((0.6, -3.4, 1.4), (0.2, 0.2, 0.3), 26, (0.8, -4.2, 1.8)), "S24c"),
    ("S27a", _desk, s("27-01"), None, "S27a"), ("S27b", _desk, s("27-03"), TOP((0.0, 0.2, 1.7), (0.2, 0.2, 2.1)), "S27a"),
    ("S27b2", _desk, s("27-04"), C((-1.2, -1.0, 0.5), (0.3, 0.3, 0.1), 28, (-1.0, -1.2, 0.55)), "S27a"), ("S27c", _desk, s("27-05"), lambda t0: F((0.35, -0.75, 0.25), 38), "S27a"),
    ("S27d", _desk, s("27-06"), C((0.3, -2.0, 0.7), (0.0, 0.5, 0.4), 30, (0.3, -3.4, 1.4), (0.0, 1.0, 0.9), d=9.0), "S27a"),
    ("S28a", b_end, s("28-01"), None, "S28a"), ("S28a1", b_end, s("28-02"), C((0.0, -0.6, 0.6), (-0.2, 0.35, 0.1), 30, (0.1, -0.55, 0.55)), "S28a"), ("S28a2", b_end, s("28-04"), lambda t0: F((0.7, -1.7, 0.65), 30, 0.1), "S28a"),
    ("S28b", b_end, s("28-06"), None, "S28b"), ("S28b1", b_end, s("28-07"), C((3.2, -2.2, 0.9), (0.6, -0.6, 0.3), 30, (3.0, -2.0, 0.85)), "S28b"), ("S28b2", b_end, s("28-08"), C((1.5, -3.2, 2.2), (0.1, -0.35, 0.15), 28, (1.3, -3.0, 2.1)), "S28b"),
]
END_T = e("28-08") + 2.5
CUTS.sort(key=lambda c: c[2])   # 足したカットを時刻の順に（次のカットの頭で終わる）
CLIPS = {}
for i, (nm, fn, tc, cm, par) in enumerate(CUTS):
    t0 = max(0.0, tc - 0.1)
    t1 = (CUTS[i + 1][2] + 0.75) if i + 1 < len(CUTS) else END_T
    CLIPS[nm] = (fn, t0, t1, cm, par)
CLIPS["S06p"] = (_desk, s("06-01"), e("06-04") + 0.5, None, "S06a")   # 小窓用：名前で比べた結果（07-06〜07-07）

if __name__ == "__main__" or True:
    if CLIPNAME == "--list":
        print(json.dumps({k: [round(v[1], 3), round(v[2], 3), round(([c[2] for c in CUTS if c[0] == k] or [v[1]])[0], 3), v[4]] for k, v in CLIPS.items()}))
    else:
        fn, t0, t1, cm, par = CLIPS[CLIPNAME]
        CLOCK["T0"] = t0
        fn(par)
        if cm is not None: cm(t0)
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
