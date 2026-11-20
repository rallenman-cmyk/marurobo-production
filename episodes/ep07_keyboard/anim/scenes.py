# 7本目（キーボード）：3D の場面を声の時刻に合わせて動かして描く
# blender -b --factory-startup --python scenes.py -- <クリップ> <出力フォルダ> [--samples 8] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   PC の本番：... -- <クリップ> <出力> --samples 24 --res 1920 1080 --frames 0 99 --gpu --video --fast
#   クリップの一覧は下の CUTS（名前・場面の組み立て・切り替わる時刻＝その文の字幕が出る時刻）
#   場面の組み立て（b_*）は、その舞台の動きを全部作り、カメラだけをクリップごとに選ぶ（6本目と同じ作り方）
#   部品は kit.py（6本目の kit を読み込んで足した）、時刻と動きの共通は 6本目の core.py（声は ../voice）
#   決まり：3D の中に字を書かない（キーの字は 2D。キーの場所を track で書き出す）／まるロボは喋らない／動きは言い終えてから／
#     瞬間移動に見せない（跳ねて・歩いて移る）／カメラはいつもゆっくり動かす／道のり：クワーティ＝青・ABC 順＝橙・いろは歌専用＝緑
import os, sys, math, json
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
_K7 = KIT_HERE
exec(open(os.path.join(KIT_HERE, "..", "..", "ep06_haizen", "anim", "core.py"), encoding="utf-8").read().replace(
    'VO = os.path.join(KIT_HERE, "..", "voice")', 'VO = os.path.join(_K7, "..", "voice")'))
CLIPNAME, OUTDIR = _argv[0], _argv[1]
# 字を言う瞬間（voice/letter_times.json）。文の頭からの秒を足す
_LT = json.load(open(os.path.join(_K7, "..", "voice", "letter_times.json"), encoding="utf-8"))
def lt(i, ch): return s(i) + _LT[i][ch]
# 効果音に「鳴らした物」（track の名前）を持たせる。組み立てで、その物が画面に映っているときだけ鳴らす（7本目 v5「まるロボが写ってないのにSE聞こえるのやめて」）
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
sys.path.insert(0, os.path.join(KIT_HERE, "..", "tools"))
IROHA = "irohanihoheto chirinuruwo wakayotareso tsunenaramu uwinookuyama kefukoete asakiyumemishi wehimosesu".replace(" ", "")
KANA = "いろはにほへとちりぬるをわかよたれそつねならむうゐのおくやまけふこえてあさきゆめみしゑひもせす"


_M_ = [None]


# まるロボ：本物の体を、動きの予定で動かす（2026-11-17 ユーザー「まるロボの動きは手で作らず、一覧の部品から選ぶ」）。MaruR は maru7.py
exec(open(os.path.join(_K7, "maru7.py"), encoding="utf-8").read())


def cam(loc, target, lens=35, t0=None, t1=None, loc1=None, target1=None, lens1=None):
    c, tg = cam_rig(loc, target, lens)
    if t0 is not None:
        cam_move(c, tg, t0, t1, loc, loc1 or loc, target, target1 or target, lens, lens1 or lens)
    return c, tg


def topcam(loc0, loc1=None, t0=None, t1=None, lens=30):
    c = cam_top(loc0, lens)
    if loc1 is not None: cam_top_move(c, t0, t1, loc0, loc1)
    return c


def hop_across(M, p0, p1, t_land):
    """キーボードからキーボードへ：机に跳び降りて歩き、となりのキーボードに跳び乗る（キーの上を宙に浮いて歩かない）"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    # キーボードの手前（y が小さい方）の机へ降りる
    a = (p0[0] + ux * 0.1, p0[1] - 0.62, 0.0); b = (p1[0] - ux * 0.1, p1[1] - 0.62, 0.0)
    tw = math.hypot(b[0] - a[0], b[1] - a[1]) / (1.3 * M.s)
    M.jump(t_land - tw - 3.2, a); M.walk(t_land - tw - 2.0, t_land - 1.6, b); M.jump(t_land, p1)


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
    key(A.root, "location", s("04-03") + 1.6, (0, 0, KEY_TOP)); ev(s("04-03") + 0.1, "whoosh", 0.4); ev(s("04-03") + 1.6, "land", 0.4, "")
    D = Board(ROWS_DV, DO_, name="kd", key_col="#E6F0EA"); D.track_all("d_")
    key(D.root, "location", -100.0, (6.0, 0, KEY_TOP)); key(D.root, "location", s("23-02"), (6.0, 0, KEY_TOP))
    key(D.root, "location", s("23-02") + 1.4, (0, 0, KEY_TOP))
    if s("23-02") > s("04-03"):
        key(A.root, "location", s("08-01"), (0, 0, KEY_TOP)); key(A.root, "location", s("08-01") + 0.1, (6.0, 0, KEY_TOP))
    M = MaruR(Q.pos("A", 0.075), face=0.0); track("maru", M.body, 0.1); track("maru_top", M.body, 0.25)
    P = lambda B, ch: B.pos(ch, 0.075)
    # 01：机の上を歩いてキーボードの前へ → 跳ねて A に乗る → A を打つ（2026-11-16 ユーザー「まるロボがキーボードのところまで歩いてくる感じにして」）
    fl = (QO[0] - 0.32, QO[1] - 0.2, 0.0)        # キーボードの左はし（A の左）
    M.at(-100.0, loc=(QO[0] - 0.7, QO[1] - 0.85, 0.0), face=-40)
    M.walk(s("01-01") + 0.4, e("01-01") + 0.2, fl)
    M.wobble(w("01-02", "腕") - 0.2, e("01-02") + 0.1, 10, 0.5)      # 01-02：腕がない（体を左右にふる）
    # 01-04「ぴょん」で A に跳び乗り、「カタッ」で A が鳴る（v7「ぴょんって言葉の時に乗るようにして」）。乗っている間のキーは足の位置から自動で沈む
    M.at(w("01-03", "跳ねて"), look=16); M.at(e("01-03"), look=0)      # 01-03：キーボードを見上げる
    t = w("01-04", "ぴょん"); M.jump(t + 0.3, P(Q, "A")); Q.press("A", w("01-04", "カタッ"), gain=0.7, motion=False)
    # 02：B をさがす（右に S・左は何もない・上に Q）
    # 向き：となりの S（右）を見る → 反対側（左）を見る（2026-11-16 ユーザー「まるロボ見てる方向が逆」で左右を入れかえた）
    M.at(w("02-01", "すぐとなり"), face=35)
    M.at(s("02-02"), face=60); M.at(s("02-03") - 0.1, face=60); M.at(s("02-03") + 0.4, face=-70)
    Q.light("S", w("02-02", "S"), s("02-04"), col="#FFD24A")      # 02-02：となりの S
    t = s("02-04"); M.at(t, face=-70)
    SR = ("Q", "W", "S", "D", "K")      # 最後は K（上の段の QWERTY の前に立たない。03 でその 6 個が浮き上がるため）
    hop_path(Q, "A" + "".join(SR), t + 0.4, 0.55, M, line=False)      # A から Q W S D K へ続けて跳ぶ（Q を押すのは t + 0.95。v6 と同じ）
    M.wobble(e("02-04") - 0.6, e("02-04"), 8, 0.3)
    # 03：上から。まるロボは K で止まったまま（B へは行かない。2026-11-16 ユーザー「この話してるときにＢのとこ行ってるのおかしい」）
    # 03-01：声が字を言う瞬間に光る（v5「音声に合わせて対象のキーを光らせて」。時刻は voice/letter_times.json）
    for ch in "QWERTY": Q.light(ch, lt("03-01", ch), s("03-03") + 0.2); ev(lt("03-01", ch), "pi", 0.2, "k_" + ch)
    # 03-02：Q W E R T Y のキーが浮き上がって、字をこちらに向ける
    for i, ch in enumerate("QWERTY"): Q.rise(ch, w("03-02", "左上") + 0.15 * i, e("03-02") + 0.6 + 0.08 * i)
    M.at(w("03-02", "左上") + 0.2, look=-18); M.at(e("03-02") + 0.8, look=0)
    M.at(e("03-05") + 0.4, face=0.0)
    # 04-01〜02：遠くのキーほど、たくさん跳ぶ（K → J は小さく、J → Q は大きく）
    Q.light("Q", w("04-01", "跳ねる距離"), e("04-02") + 0.2, col="#FFD24A")
    ta = w("04-02", "遠く"); M.at(e("04-01"), face=-90)
    hop_path(Q, "KJ", ta, 0.5, M, line=False, h=0.12)
    tb = w("04-02", "たくさん"); hop_path(Q, "JQ", tb, 1.0, M, line=False, h=0.45)
    # 04-03〜04：ABC 順のキーボードが右にすべりこむ → まるロボはそちら（右）を向いて、跳ねてよろこぶ（v5「まるロボはabcのキーボードの方を向かせて」）
    M.at(s("04-03") - 0.3, face=-60); M.at(s("04-03") + 2.4, face=80)
    M.hops(s("04-04") + 0.3, n=2)
    # 05：「マルロボ」を打つ（青 → 橙）。最初の M へ歩く
    M.walk(s("05-01") + 0.4, s("05-01") + 1.6, P(Q, "M"))
    t = w("05-04", "道のり"); dt = min(0.55, (e("05-04") + 0.4 - t) / 7)
    hop_path(Q, "MARUROBO", t, dt, M, col=BLUE_L, name="path_q")
    t2 = s("05-05") - 0.2; M.jump(t2 + 3.0, P(A, "M"), apex=0.3)      # となりのキーボードへ、大きく跳んで移る
    dt2 = min(0.55, (e("05-05") + 0.5 - (t2 + 4.3)) / 7)
    hop_path(A, "MARUROBO", t2 + 4.3, dt2, M, col=ORANGE_L, name="path_a")
    # 06：上から結果。まるロボは O の上できょとん（首をかしげる）
    M.at(s("06-04"), face=0.0); M.tilt(w("06-04", "ほとんど"), 14); M.tilt(e("06-04") + 0.3, 0)
    # 07：いろは歌（2 台で同時に。道のりの線が伸びる。まるロボは跳ねつかれて、ぜえぜえ）
    t0 = s("07-03") + 0.3; t1 = e("07-03") + 0.2; dt = (t1 - t0) / (len(IROHA) - 1)
    lq = hop_path(Q, IROHA, t0, dt, None, col=BLUE_L, name="iro_q", z=0.105)
    la = hop_path(A, IROHA, t0, dt, None, col=ORANGE_L, name="iro_a", z=0.105)
    M.hops(t0, n=max(2, int((t1 - t0) / 0.5)), height=0.04, sound=False)
    M.wobble(t1 + 0.1, s("07-05") + 1.0, 6, 0.6)
    for ob in (lq, la):        # 07 の終わりで消す（08 章から先の机の場面に残さない）。最初に「見える」を打っておく（打たないと、最初から隠れる）
        hide_key(ob, -100.0, False); hide_key(ob, s("08-01") - 0.5, True)
    for nm in ("path_q", "path_a"):
        hide_key(bpy.data.objects[nm], -100.0, False); hide_key(bpy.data.objects[nm], s("07-01"), True)
    # 19b：Z → S → E（となりへ 1 歩ずつ）
    M.at(s("08-01"), loc=P(Q, "Z"), face=0.0, interp="CONSTANT")   # 机が映っていない間に置き直す
    for ch, wd in (("Z", "この3つ"), ("S", "光らせて"), ("E", "みると")):
        Q.light(ch, w("19-03", wd), e("19-05") + 0.5, col="#FFD24A")
    hop_path(Q, "ZSE", w("19-04", "S"), 0.9, M, line=False)
    # 21：首をかしげる
    M.at(s("20-01"), loc=P(Q, "G"), face=0.0, interp="CONSTANT"); M.tilt(w("21-02", "もっと"), 12); M.tilt(e("21-02"), 0)
    # 23：速い並び（23-02 ですべりこむ。まるロボは跳ねて「おお」→ 23-06 で首をかしげる）
    M.jump(s("23-03") - 0.8, P(D, "A"), apex=0.32)      # 速い並びのキーボードへ、大きく跳んで移る
    hop_path(D, "AOEUIDHTNS", s("23-03") + 0.6, min(0.45, (e("23-04") - s("23-03")) / 11), M, line=False)
    for i, ch in enumerate("AOEUIDHTNS"): D.light(ch, w("23-03", "真ん中の列") + 0.12 * i, e("23-04") + 0.4, col="#7FD8A0")   # 2D の字の代わりに、真ん中の列を光らせる
    M.glow(s("23-04"), 1.6, 0.3); M.glow(e("23-04") + 0.2, 0.9, 0.3)
    # 24：スマホ（机に寝かせた大きなスマホ。棒のない、薄い機械）
    ph, scr = smartphone((-0.1, -1.6, 0.0), s=0.62); track("phone", scr, 0.05)
    key(ph, "location", -100.0, (-0.1, -6.0, 0.0)); key(ph, "location", s("24-06") - 1.0, (-0.1, -6.0, 0.0)); key(ph, "location", s("24-06"), (-0.1, -1.6, 0.0))
    M.at(s("24-01"), loc=(0.4, -0.75, 0.0), face=0.0, interp="CONSTANT")   # 机が映っていない間に、キーボードの手前の机へ
    M.walk(s("24-06") + 0.2, s("24-06") + 3.5, (0.1, -0.95, 0.0)); M.jump(w("24-07", "スマホ") - 0.1, (0.1, -1.25, 0.06))
    M.at(e("24-07"), face=0.0)
    key(ph, "location", s("27-01") + 1.4, (-0.1, -1.6, 0.0)); key(ph, "location", s("27-01") + 2.4, (-0.1, -6.0, 0.0))   # まるロボが降りてから片づける
    # 27-01：スマホから歩いてキーボードの前へ → 跳ねて G に乗る（v5「まるロボがワープしてる」）
    gx, gy, gz = P(Q, "G")
    M.jump(s("27-01") + 0.4, (0.25, -0.95, 0.0))
    M.walk(s("27-01") + 0.5, e("27-02") - 0.2, (gx, gy - 0.42, 0.0))
    M.jump(s("27-03") + 1.6, (gx, gy, gz))
    M.at(s("27-03") + 5.0, face=-25); M.at(s("27-04") + 0.4, face=25)
    # 27-05：キーを横へ押してずらそうとする → 動かない（v5「まるロボがただいるだけになってる」）
    M.at(s("27-05"), face=80)
    hk = Q.keys["H"]; hx = hk.location.x
    for k_ in range(3):
        tp = s("27-05") + 0.6 + k_ * 0.9
        M.push(tp - 0.05, 0.35)
        key(hk, ("location", 0), tp, hx); key(hk, ("location", 0), tp + 0.12, hx + 0.006); key(hk, ("location", 0), tp + 0.3, hx)
        ev(tp + 0.1, "tick", 0.3, "k_H")
    M.wobble(e("27-05") - 0.5, e("27-05") + 0.2, 6, 0.3)
    M.at(s("27-06"), face=0.0)
    return dict(Q=Q, A=A, D=D, M=M)


def b_desk_cam(cl, S_):
    Q, M = S_["Q"], S_["M"]
    if cl == "S01a":
        cam((-0.2, -2.3, 0.8), (-0.95, 0.15, 0.15), 34, s("01-01") - 0.2, e("01-02"), (-0.35, -2.0, 0.65), (-0.95, 0.2, 0.12), 38)
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
    elif cl == "S24c":     # 今のキーボードを横から（中に棒がない）
        cam((1.7, -0.1, 1.05), (0.0, 0.3, 0.02), 30, s("24-06"), e("24-09") + 0.8, (1.65, -0.15, 1.02), (0.0, 0.3, 0.02), 31)   # 高めの横から（まるロボがカメラの前を横切らない）
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
    # 横に長いキーボードは、28-03「できあがったのは」まで机の下に隠す（v5「最初の考えたところで横並びのキーボードうつさないで」）
    tu = w("28-03", "できあがった")
    key(L.root, "location", -100.0, (0, 0, KEY_TOP - 0.3)); key(L.root, "location", tu, (0, 0, KEY_TOP - 0.3)); key(L.root, "location", tu + 0.6, (0, 0, KEY_TOP))
    ev(tu + 0.1, "whoosh", 0.3)
    ix, iy, iz = L.pos("い", 0.075)
    M = MaruR((ix - 0.3, iy - 0.25, 0.0), face=0.0); track("maru", M.body, 0.1)
    M.at(-100.0, loc=(ix - 0.3, iy - 0.25, 0.0), face=30)
    M.jump(tu + 1.2, (ix, iy, iz))
    # キーがくるくる入れかわる（28-01〜28-02）：クワーティのキーが浮いて回る
    for i, (ch, o) in enumerate(list(Q.keys.items())[:18]):
        t_ = s("28-02") + 0.05 * i
        z_ = o.location.z; key(o, ("location", 2), t_, z_); key(o, ("location", 2), t_ + 0.4, z_ + 0.25); key(o, ("location", 2), t_ + 0.9, z_)
        key(o, ("rotation_euler", 2), t_, 0.0); key(o, ("rotation_euler", 2), t_ + 0.9, R(360))
    ev(s("28-02") + 0.1, "whoosh", 0.4)
    # いろは歌を打つ：となりへ、となりへ 1 歩ずつ（緑の線）
    t0 = w("28-04", "打って"); n = 10; dt = 0.3
    hop_path(L, KANA[:n], t0, dt, M, col=GREEN_L, name="path_l", h=0.12)
    ln2 = line_path("path_l2", [L.pos(c)[:2] for c in KANA[n - 1:]], col=GREEN_L, width=0.018, z=KEY_TOP + 0.1, emit=3.0)
    ln2.data.bevel_factor_end = 0.0; ln2.data.keyframe_insert("bevel_factor_end", frame=f(t0 + n * dt))
    ln2.data.bevel_factor_end = 1.0; ln2.data.keyframe_insert("bevel_factor_end", frame=f(s("28-05") + 0.6))
    M.hop(s("28-05") + 0.2, h=0.18, d=0.4); M.at(s("28-05") + 1.0, look=10)
    # 28-06：はっと固まる → 28-07〜08：人の手が来て、となりのいつものキーボードへ（まるロボはしょんぼり）
    M.at(s("28-06") + 0.6, look=0); M.glow(s("28-06") + 0.6, 2.0, 0.15); M.glow(s("28-06") + 1.0, 0.9, 0.3)
    # 人の手（ほかの人と同じ、丸い形。手のひら・丸い指 4 本・親指・そで口）（v5「何で急に雑な手が出てくるの」）
    hand = empty((3.5, -0.2, 1.4)); km = mat("skin", "#F1C7A5", rough=0.55)
    sphere(km, (0, 0, 0), 0.34, scale=(1.0, 1.25, 0.42), parent=hand)
    for i in range(4):
        fx = -0.24 + 0.16 * i; ln = (0.30, 0.36, 0.34, 0.27)[i]
        f_ = empty((fx, 0.36, 0.0)); f_.parent = hand; f_.rotation_euler = (R(-14), 0, 0)
        cyl(km, (0, ln / 2, 0), 0.068, ln, rot=(R(90), 0, 0), parent=f_, verts=20); sphere(km, (0, ln, 0), 0.068, parent=f_, seg=20)
    th = empty((0.32, 0.05, -0.02)); th.parent = hand; th.rotation_euler = (0, 0, R(-48))
    cyl(km, (0, 0.13, 0), 0.075, 0.26, rot=(R(90), 0, 0), parent=th, verts=20); sphere(km, (0, 0.26, 0), 0.075, parent=th, seg=20)
    cyl(mat("cuff", "#F4F2EC", rough=0.6), (0, -0.42, 0.0), 0.3, 0.12, rot=(R(90), 0, 0), parent=hand)
    cyl(mat("sleeve", "#3E7CB1", rough=0.7), (0, -1.25, 0.0), 0.31, 1.55, rot=(R(90), 0, 0), parent=hand)
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
TW_KEYS = [None]


def b_shop(cl, night=False):
    workshop(night=night)
    ptw, pk = piano_typewriter((-0.95, 0.4, 0.94))
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ": track("p_" + ch, pk[ch], 0.05)
    mtw, mk = modern_typewriter((0.0, 0.4, 0.94), layout=["QWE.TY", "ASDFG", "ZXCV"])
    TW_KEYS[0] = mk
    for ch, o in mk.items(): track("m_" + ("dot" if ch == "." else ch), o, 0.04)
    M = MaruR((-1.9, -0.6, 0.94), face=0.0, s=0.2); track("maru", M.body, 0.1)
    # 作業台の手前の床から机の上へ（08：歩いて入る → 机の上に跳び乗る）
    sh = walker((1.2, 1.5, 0), face=(20 if cl.startswith("S08") else 180), shirt="#5A4632", pants="#3A2E24", hair="#5A4A3A")   # ショールズさんたち（顔は描かない）
    sh2 = walker((2.2, 1.6, 0), face=(-20 if cl.startswith("S08") else 200), shirt="#3E4A5A", pants="#2D3640", hair="#2B2220")
    track("sholes", sh.head, 0.25); track("nakama", sh2.head, 0.25)
    if not night:
        M.at(-100.0, loc=(-2.6, -1.6, 0.0), face=-60)
        M.walk(s("08-01") + 0.3, s("08-02") - 2.4, (-1.8, -0.4, 0.0))
        M.at(s("08-02") + 0.1, face=0.0); M.at(s("08-02") + 0.5, look=18); M.at(e("08-03"), look=0)
        M.jump(s("09-01") + 0.2, (-1.0, 0.2, 0.94))
        # 09：A → B → C（となりへ）。キーに字（3D）。乗ったキーは沈み、降りたら戻る
        p = lambda ch: (pk[ch].matrix_world.translation.x, pk[ch].matrix_world.translation.y, 0.94 + 0.18)
        bpy.context.view_layer.update()
        M.jump(s("09-03") - 0.4, p("A"))
        Z0 = {ch: o.location.z for ch, o in pk.items()}       # 高さは先に覚えておく（打ったあとに読み直すと、戻らなくなる）
        hold = lambda o, z, t0, t1: [key(o, ("location", 2), t0 - 0.01, z), key(o, ("location", 2), t0 + 0.06, z - 0.02),
                                     key(o, ("location", 2), t1, z - 0.02), key(o, ("location", 2), t1 + 0.08, z)]
        tab = [s("09-03") - 0.4]
        for i, ch in enumerate("BC"):
            ta = w("09-03", "ABC") + 0.3 + 0.6 * i
            ev(ta, "key", 0.4, "p_" + ch); tab.append(ta)
        M.path([p("B"), p("C")], [tab[1] - 0.03, tab[2] - 0.03])
        t_off = s("10-01") + 0.4
        # 09-04〜05：手前の列が左から、奥の列が右から、順に光る
        for i, ch in enumerate("ABCDEFGHIJKLMN"): glow_plate(pk[ch], w("09-04", "手前") + 0.12 * i, e("09-05") + 0.5, "#FFB45C", (0.13 * 0.8, 0.26), 0.031)
        for i, ch in enumerate("OPQRSTUVWXYZ"): glow_plate(pk[ch], w("09-05", "奥") + 0.12 * i, e("09-05") + 0.5, "#7FA8FF", (0.13 * 0.6, 0.16), 0.031)
        # 10-01：鍵盤から机へ跳び降りて歩く（浮かない。v5「まるロボ浮いてるように見える」）
        M.jump(t_off + 0.5, (-0.75, -0.35, 0.94))
        # 10-02：ピアノの機械が消え、今の形の機械が出る。まるロボは歩いて近づく（足音）
        ta = s("10-02")
        hide_key(ptw, -100.0, False); hide_key(ptw, ta + 0.6, True)
        hide_key(mtw, -100.0, True); hide_key(mtw, ta + 0.6, False); scale_pop(mtw, ta + 0.6, 1.0, 0.5)
        ev(ta + 0.6, "pop", 0.5)
        M.walk(ta + 1.0, ta + 2.4, (-0.85, -0.4, 0.94))
        # 10-03：キーが 2 つずつ、弧をえがいて場所を入れかえる（最後に今の並び QWE.TY になる）
        bpy.context.view_layer.update()
        for k_, (a_, b_) in enumerate((("E", "T"), ("A", "S"), ("C", "V"))):
            oa, ob_ = mk[a_], mk[b_]; pa, pb = tuple(oa.location), tuple(ob_.location)
            tt = w("10-03", "入れかわって") - 0.6 + 0.7 * k_
            key(oa, "location", -100.0, pb); key(ob_, "location", -100.0, pa)
            key(oa, "location", tt, pb); key(ob_, "location", tt, pa)
            key(oa, "location", tt + 0.3, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, pa[2] + 0.16)); key(ob_, "location", tt + 0.3, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2 - 0.05, pb[2] + 0.1))
            key(oa, "location", tt + 0.6, pa); key(ob_, "location", tt + 0.6, pb)
            ev(tt + 0.1, "whoosh", 0.25); ev(tt + 0.6, "tick", 0.3)
        # 10-04：机の上（足は机の面）で上の列を見る
        M.at(s("10-04"), loc=(-0.85, -0.4, 0.94), face=25); M.at(s("10-04") + 0.4, look=14)
        # 10-05：声が字を言う瞬間に、そのキーが跳ねて光る（ピリオドは赤。10-06 のあいだ光り続ける）
        for ch in "QWE.TY":
            tt = lt("10-05", ch); o = mk[ch]; z_ = o.location.z
            key(o, ("location", 2), tt, z_); key(o, ("location", 2), tt + 0.15, z_ + 0.05); key(o, ("location", 2), tt + 0.35, z_)
            glow_plate(o, tt, (e("10-06") + 0.4) if ch == "." else (e("10-05") + 0.3), "#FF6A5A" if ch == "." else "#FFD24A", (0.13 * 0.62, 0.13 * 0.62), 0.016, round_=True)
            ev(tt, "pi", 0.2, "m_" + ("dot" if ch == "." else ch))
    else:
        hide_key(ptw, -100.0, True)
        # 20：夜。もう 1 台の、並びの違う機械（2 段目が X P M C H）
        xtw, xk = modern_typewriter((1.6, 0.35, 0.94), layout=["23456", "XPMCH", "JBWFL"], col="#4A2A2A", name="tx")
        for ch in "XPMCH": track("x_" + ch, xk[ch], 0.04)
        hide_key(xtw, -100.0, True); hide_key(xtw, w("20-04", "別の並び"), False); scale_pop(xtw, w("20-04", "別の並び"), 1.0, 0.5)
        ev(w("20-04", "別の並び"), "pop", 0.6)
        area((1.6, -0.8, 2.0), (1.6, 0.3, 0.95), energy=70, size=1.5, col="#FFE7C4")   # 夜でも並びの違う機械が見えるように
        for i, ch in enumerate("XPMCH"): glow_plate(xk[ch], w("20-05", "X P M C H") + 0.25 * i, e("20-06") + 0.3, "#FF6A5A", (0.13 * 0.62, 0.13 * 0.62), 0.016, round_=True); ev(w("20-05", "X P M C H") + 0.25 * i, "pi", 0.2, "x_" + ch)
        M.at(-100.0, loc=(0.8, -0.3, 0.94), face=0.0)
        M.at(w("20-04", "別の並び") + 0.4, face=-50); M.at(s("20-05") + 0.6, face=40); M.at(s("20-06"), face=-50); M.at(s("20-07"), face=0.0)
        M.at(s("20-07") + 0.5, look=16); M.glow(w("20-04", "なんと"), 1.8, 0.2); M.glow(w("20-04", "なんと") + 0.8, 0.9, 0.4)
    if cl == "S08a":
        cam((-0.6, -3.6, 1.4), (-0.6, 0.3, 0.9), 30, s("08-01"), e("08-03") + 0.8, (-0.2, -3.2, 1.5), (-0.4, 0.4, 0.95), 32)
    elif cl == "S09a":
        cam((-0.2, -1.2, 1.5), (-0.75, 0.3, 1.05), 30, s("09-01"), e("09-05") + 0.8, (-0.1, -1.1, 1.55), (-0.7, 0.3, 1.05), 31)
    elif cl == "S10a":
        cam((-0.4, -1.7, 1.6), (-0.3, 0.4, 1.05), 32, s("10-01"), e("10-03") + 0.6, (-0.1, -1.5, 1.7), (-0.1, 0.4, 1.05), 34)
    elif cl == "S10b":
        cam((-1.45, -1.05, 1.45), (-0.3, 0.3, 1.15), 32, s("10-04"), e("10-06") + 0.8, (-1.4, -0.95, 1.45), (-0.3, 0.3, 1.15), 33)
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
    sheets = [cube(pm, (-1.3, 1.1, 0.97 + k_ * 0.01), (0.42, 0.56, 0.008), rot=(0, 0, R(3 * k_ - 8))) for k_ in range(6)]
    top = sheets[-1]
    L0 = tuple(top.location)
    def flip(t):     # いちばん上の紙をめくって、下の紙を見る（何も書いていない）
        up = (L0[0], L0[1] + 0.12, L0[2] + 0.18)
        key(top, "location", t, L0); key(top, ("rotation_euler", 0), t, 0.0)
        key(top, "location", t + 0.4, up); key(top, ("rotation_euler", 0), t + 0.4, R(-70))
        key(top, "location", t + 1.4, up); key(top, ("rotation_euler", 0), t + 1.4, R(-70))
        key(top, "location", t + 1.8, L0); key(top, ("rotation_euler", 0), t + 1.8, 0.0)
        ev(t, "whoosh", 0.15)
    # 11：歩いて紙の束へ（滑らない）→ めくって、何も書いていないのを見る
    M.walk(e("10-09") + 0.3, s("11-01") - 1.4, (-1.55, 0.6, 0.94))
    M.at(s("11-01") + 0.6, face=-20); M.at(s("11-01") + 0.9, look=25)
    flip(w("11-02", "書き残して") - 0.6)
    M.tilt(w("11-02", "書き残して"), 15); M.tilt(e("11-02"), 0)
    # 12-01：機械へ歩き、キーに跳び乗る → キーが外れる → 開いた穴から中へ飛びこむ（v5「まるロボがタイプライターのキーを外して中に入り込むみたいな演出にして」）
    gx, gy, gz = -0.0675, 0.233, 1.192
    M.walk(s("11-03"), s("12-01") - 0.8, (gx, -0.32, 0.94))      # 11-03 のうちに歩き出す（遠いので）
    t1 = s("12-01") + 2.6; M.jump(t1, (gx, gy, gz))
    G = TW_KEYS[0]["G"]; gl = TW_KEYS[0]["G"].location[:]
    t2 = t1 + 1.6
    key(G, "location", t2, gl); key(G, ("rotation_euler", 1), t2, 0.0)
    key(G, "location", t2 + 0.25, (gl[0] + 0.12, gl[1] - 0.05, gl[2] + 0.22)); key(G, ("rotation_euler", 1), t2 + 0.6, R(160))
    key(G, "location", t2 + 0.7, (gl[0] + 0.42, gl[1] - 0.35, -0.2)); ev(t2 + 0.05, "pop", 0.4)
    M.hopto(t2 + 0.3, (gx - 0.1, gy - 0.12, gz))      # キーから横へよける（キーが外れる）
    M.hopto(t2 + 2.0, (gx, gy, 0.8))      # 開いた穴へ飛びこむ
    ev(t2 + 1.7, "whoosh", 0.4)
    # 14-02：紙の束へ戻って、もう一度めくる（記録はどこにもない）
    M.at(s("14-02") - 0.3, loc=(-1.55, 0.6, 0.94), face=-20, interp="CONSTANT"); M.at(s("14-02") - 0.2, look=25)
    flip(w("14-02", "記録") - 0.3)
    M.at(s("16-02"), look=0); M.at(s("16-03") + 0.3, look=-15); M.at(s("16-03") + 0.8, look=8)


# ======================================================================== C：タイプライターの中（S12〜S15）
def b_inside(cl):
    world("#3A3430", 1.0)
    fm = noise_mat("insidefloor", "#5A5048", "#4A423A", scale=8, rough=0.6, bump=0.1)
    cube(fm, (0, 0, -0.05), (8, 8, 0.1))
    root, pv = typebar_basket((0, 0.6, 0.02), r=1.2, n=36)
    for ch in "ERTY": track("bar_" + ch, pv[ch].children[1] if len(pv[ch].children) > 1 else pv[ch], 0.05)
    # 打つ所：棒の先が集まる所の向こうに、すけた紙と、紙を押さえる黒い筒（v7「上にはすかした紙みたいなの写してほしい」「棒の上にある丸いのはなに？」）
    hit = (0.0, 0.6, 0.92)
    cyl(mat("platen_in", "#15171A", rough=0.4), (hit[0], hit[1] + 0.3, hit[2] + 0.02), 0.16, 1.8, rot=(0, R(90), 0))
    pm_ = bpy.data.materials.new("paper_see"); pm_.use_nodes = True; bs_ = pm_.node_tree.nodes["Principled BSDF"]
    bs_.inputs["Base Color"].default_value = (0.5, 0.49, 0.46, 1); bs_.inputs["Alpha"].default_value = 0.3; bs_.inputs["Roughness"].default_value = 0.9
    pm_.blend_method = "BLEND" if hasattr(pm_, "blend_method") else None
    paper = cube(pm_, (hit[0], hit[1] + 0.16, hit[2] + 0.28), (1.1, 0.008, 0.6)); paper.rotation_euler = (R(-15), 0, 0)
    track("paper", paper, 0.3)
    spot((0.0, -1.5, 2.6), (0, 0.6, 0.3), energy=3200, angle=60, col="#FFE3BC")
    area((-2.0, 1.5, 2.0), (0, 0.6, 0.3), energy=600, size=3, col="#9FB3E0")
    area((1.8, -1.8, 2.2), (0, 0.2, 0.3), energy=700, size=3, col="#FFF1D6")
    M = MaruR((0.0, -0.9, 0.0), face=0.0, s=0.26); track("maru", M.body, 0.1)
    # 12：上から飛びこんできて着く → 棒が 1 本ずつ真ん中へ跳ね上がる
    M.drop(s("12-02") - 0.4, s("12-02") + 0.1, 1.6)
    M.at(s("12-02") + 0.5, look=15)
    for i, ch in enumerate("QAW"):
        bar_up(pv[ch], w("12-03", "跳ね上がって") + 0.5 * i, d=0.45); ev(w("12-03", "跳ね上がって") + 0.5 * i + 0.2, "clack", 0.35)
    M.hop(w("12-03", "跳ね上がって") + 0.05, h=0.18, d=0.4)
    # 13：T と Y（となり同士）が光る → T が真ん中へ上がる途中に Y も上がり、真ん中の手前でぶつかって交差したまま止まる（赤い光・ふるえる）
    a_, b_ = pv["T"], pv["Y"]
    for o, col in ((a_, "#FF9A3C"), (b_, "#4FB3FF")): glow_plate(o.children[0], s("13-01") + 0.3, e("13-02") + 0.4, col, (0.05, 1.2 * 0.9), 0.0135)   # T＝橙・Y＝青（どの 2 本か分かるように）
    t = w("13-01", "続けて") + 0.6
    key(a_, ("rotation_euler", 0), t, 0.0); key(a_, ("rotation_euler", 0), t + 0.5, R(-128))
    key(b_, ("rotation_euler", 0), t + 0.2, 0.0); key(b_, ("rotation_euler", 0), t + 0.6, R(-122))
    tj = s("13-02") + 0.1
    for k_ in range(8):      # からまって、小さくふるえる
        key(a_, ("rotation_euler", 0), tj + 0.12 * k_, R(-128 + (2 if k_ % 2 else -2))); key(b_, ("rotation_euler", 0), tj + 0.12 * k_, R(-122 + (-2 if k_ % 2 else 2)))
    key(a_, ("rotation_euler", 0), tj + 1.0, R(-128)); key(b_, ("rotation_euler", 0), tj + 1.0, R(-122))
    # ぶつかった所：赤い光の玉はやめ、2D の札「ぶつかって からまった！」で指す（v7「丸い光が何かわかんない」）
    jam = empty((-0.12, 0.38, 0.58)); track("jam", jam, 0.0)
    ev(t + 0.6, "clank", 0.6)
    M.walk(s("13-03") - 0.2, s("13-03") + 0.8, (-0.05, 0.05, 0.0)); M.at(s("13-03") + 1.0, look=20)
    M.wobble(s("13-03") + 1.0, s("13-04"), 8, 0.3)
    key(a_, ("rotation_euler", 0), s("13-04") + 0.2, R(-128)); key(a_, ("rotation_euler", 0), s("13-04") + 0.6, 0.0)
    key(b_, ("rotation_euler", 0), s("13-04") + 0.3, R(-122)); key(b_, ("rotation_euler", 0), s("13-04") + 0.7, 0.0)
    ev(s("13-04") + 0.5, "snap", 0.4); M.at(s("13-04") + 0.8, look=0)
    M.at(w("13-05", "ところが"), look=0); M.tilt(w("13-05", "ところが"), 12); M.tilt(e("14-01") + 0.3, 0)
    # 14-04：棒の半円にそって歩き、棒を 1 本ずつ見ていく → E と R の所で止まる → 2 本が光る（v5「探してみるとって言ってるのに全然探している演出じゃない」）
    for ch in "ER":
        g = glow_mat("barglow" + ch, "#FFD24A", 4.0)
        gl = cube(g, (0, -1.2 * 0.45, 0.05), (0.05, 1.2 * 0.9, 0.01), parent=pv[ch]); gl.visible_shadow = False
        hide_key(gl, -100.0, True); hide_key(gl, w("14-04", "となり同士"), False); hide_key(gl, e("14-05") + 0.6, True)
    # v8：棒は輪（根もと）から外へのびている。まるロボは輪の内がわ（棒のない床）だけを歩く（v7「足が棒に貫通」）
    bpy.context.view_layer.update()
    def inn(ch, d):        # 棒の根もとから、輪の内がわへ d の点
        x, y = pv[ch].matrix_world.translation.x, pv[ch].matrix_world.translation.y - 0.6
        rr = math.hypot(x, y); return (x - x / rr * d, y - y / rr * d + 0.6, 0.0)
    def face_out(ch):      # その棒の根もとの方を向く face（前の体は前が −Y）
        x, y = pv[ch].matrix_world.translation.x, pv[ch].matrix_world.translation.y - 0.6
        rr = math.hypot(x, y); return math.degrees(math.atan2(x / rr, -y / rr))
    M.at(s("14-03") + 0.4, look=14)      # E と R の棒はどこ？（棒を見上げる。そのまま歩き出す）
    t = w("14-04", "探して")      # 棒の方へ歩きながら、棒を見上げていく → 着いて見上げる → 跳ねる
    M.walk(s("14-04"), w("14-04", "となり同士") + 0.3, inn("E", 0.45)); M.at(t + 0.4, look=18); M.at(w("14-04", "となり同士") + 0.4, look=24)
    M.hop(e("14-04") - 0.3, h=0.15, d=0.4)
    # 15-03：輪の内がわに置いた「踏み板」（字のあるキー）に跳び乗る → 板が沈み、同じ字の棒がゆっくり上がって戻る（v7「まるロボが乗ったところが動いてない」）
    #   板は根もとから 0.35 内がわ。棒は 100 度まで（ほぼまっすぐ上へ）上げるので、まるロボの頭より上を通る（v7 は根もとの近くに立って、寝た角度の棒が体を突き抜けた）
    #   2 本は G と L（となり同士にすると、板が重なる）
    M.walk(s("15-01"), s("15-03") - 1.2, inn("G", 0.7)); M.at(s("15-03") - 0.2, face=face_out("G"))
    pedal_m = mat("pedal", "#E9ECEF", rough=0.4)
    for ch, tl in (("G", w("15-03", "ぴょん") - 0.05), ("L", e("15-03") - 0.2)):     # 「ぴょん」で着く
        px, py, _ = inn(ch, 0.35)
        pd = pressable(cube(pedal_m, (px, py, 0.03), (0.16, 0.16, 0.06)), 0.03)
        x, y = pv[ch].matrix_world.translation.x, pv[ch].matrix_world.translation.y - 0.6
        pd.rotation_euler = (0, 0, math.atan2(y, x) - math.pi / 2)
        key_label(pd, ch, 0.16, "#2B3340", size=0.5, h=0.06)
        hide_key(pd, -100.0, True); hide_key(pd, s("15-01"), False)      # 15 章から（12〜14 章に白い箱が見えないように）
        for c_ in pd.children: hide_key(c_, -100.0, True); hide_key(c_, s("15-01"), False)
        M.hopto(tl, (px, py, 0.06))
        bar_up(pv[ch], tl + 0.05, d=1.0, ang=100); ev(tl + 0.4, "clack", 0.3)
    M.at(w("15-04", "ちょっと待って"), look=0); M.tilt(w("15-04", "ちょっと待って") + 0.1, 14); M.tilt(e("15-06"), 0)
    M.at(w("15-09", "少しは"), look=24); M.at(e("15-09"), look=0)
    M.shake(s("15-10") + 0.4)      # 首をふる（胴ぜんぶでひねる）
    if cl == "S12a":
        cam((-1.3, -2.0, 0.85), (0.0, 0.0, 0.35), 26, s("12-02"), e("12-03") + 0.8, (-0.6, -1.8, 0.8), (0.0, 0.1, 0.4), 24)
    elif cl == "S13a":
        cam((0.5, -0.6, 1.0), (-0.45, 0.85, 0.55), 26, s("13-01"), e("13-05") + 0.8, (0.4, -0.55, 0.95), (-0.45, 0.85, 0.55), 27)
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
    # 19-02：タイプライターの Z・S・E（字は 3D）が光る
    for i, ch in enumerate("ZSE"): glow_plate(tk[ch], w("19-02", "この3つ") + 0.25 * i, e("19-02") + 0.6, "#FFD24A", (0.13 * 0.62, 0.13 * 0.62), 0.016, round_=True)
    # 19a：打つ人が迷う（手が止まる）
    a0, a1 = op.arms
    for t_ in (s("19-01") + 0.4, s("19-01") + 1.2, s("19-01") + 2.0):
        key(a0, ("rotation_euler", 2), t_, R(-8)); key(a0, ("rotation_euler", 2), t_ + 0.4, R(10))
    if cl == "S17a":
        cam((-2.2, -2.2, 1.6), (0.0, 0.6, 1.0), 28, s("17-01"), e("17-04") + 0.8, (-1.8, -2.0, 1.5), (0.0, 0.6, 1.0), 30)
    elif cl == "S18a":
        cam((-0.9, -0.6, 1.3), (-0.6, 0.6, 0.98), 40, s("18-01"), e("18-05") + 0.8, (-0.8, -0.4, 1.25), (-0.6, 0.6, 0.98), 44)
    elif cl == "S19a":
        cam((2.4, 0.15, 1.65), (0.55, 0.1, 1.1), 32, s("19-01"), e("19-02") + 0.6, (2.3, 0.25, 1.62), (0.55, 0.1, 1.1), 33)     # 横から、迷う顔とキー（頭が画面をふさがない）


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
        M.at(-100.0, loc=(-3.0, -1.4, 0.0), face=-30); M.hop(s("22-02") + 0.4, h=0.15, d=0.4)
        cam((-4.5, -4.0, 2.4), (-0.4, 0.2, 0.8), 28, s("22-01"), e("22-02") + 0.8, (-4.0, -3.6, 2.2), (0.0, 0.2, 0.8), 30)
    else:
        cam((4.4, -3.8, 2.5), (0.0, 0.2, 0.8), 28, s("17-05"), e("17-05") + 0.8, (4.0, -3.4, 2.3), (-0.2, 0.2, 0.8), 30)


def b_demo(cl):
    """17-06〜17-09：電信の会社のえらい人の前で試し打ち（えらい人がモールス信号を送り、先生がタイプライターで打つ）"""
    hall(col_wall="#CBB89A", floor=("#7A5233", "#6B4A30"))
    cube(mat("demotable", "#6B4A30", rough=0.5), (0, 0.8, 0.76), (3.0, 0.9, 0.05))
    mk_, lever = morse_key((-0.9, 0.75, 0.79))
    boss = person((-0.9, 0.2, 0), 180, shirt="#1F2630", pants="#1A1E26", hair="#6A6A6A")      # 机（音を出す機械）の方を向く
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
    cam((3.6, 1.0, 1.9), (-0.2, 0.5, 1.0), 30, s("17-06"), e("17-09") + 0.8, (3.5, 0.9, 1.88), (-0.2, 0.5, 1.0), 31)     # 横から：えらい人と先生の顔が見える


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
    # 打つ人は机（+y）を向くので、舞台の奥から顔と手を映す（手前の見ている人の頭がふさがないように）
    cam((0.4, 3.4, 2.7), (0.0, 0.5, 1.2), 30, s("22-03"), e("22-04") + 0.8, (-0.3, 3.3, 2.6), (0.0, 0.5, 1.2), 32)


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
        # 台車から作業台へ：一度持ち上げてから、台の上へ下ろす（v5「ミシンが貫通してる机を」：まっすぐ動かして台を突き抜けていた）
        key(tw, "location", s("10-07") + 2.3, (-0.6, -0.4, 1.15)); key(tw, "location", s("10-07") + 2.8, (0.4, -0.25, 1.15)); key(tw, "location", s("10-07") + 3.1, (0.4, -0.25, 0.89))
        ev(s("10-07") + 0.2, "motor_on", 1.0); ev(s("10-07") + 2.0, "motor_off", 1.0); ev(s("10-07") + 3.1, "clank", 0.4)
        dot = tk["."]; dz0 = dot.location.z      # 先に高さを覚えておく（キーを打つと location が変わる。v5 は R が 0.6 上に浮いたままで「Rが入ってない」）
        rk = cyl(mat("fx_keytop", "#F1EEE6", rough=0.3, coat=0.5), (dot.location.x, dot.location.y, dz0 + 0.6), 0.13 * 0.34, 0.025, parent=tw)
        key_label(rk, "R", 0.13, "#1E2530", size=0.72, h=0.045)
        track("f_R", rk, 0.03)
        hide_key(rk, -100.0, True)
        t = w("10-08", "外され"); key(dot, ("location", 2), t, dz0); key(dot, ("location", 2), t + 0.4, dz0 + 0.6); hide_key(dot, t + 0.45, True)
        ev(t + 0.05, "pop", 0.5, "f_dot")
        t = w("10-08", "R が"); hide_key(rk, t, False); key(rk, ("location", 2), t, dz0 + 0.6); key(rk, ("location", 2), t + 0.35, dz0)
        ev(t + 0.35, "snap", 0.5, "f_R")
        glow_plate(rk, t + 0.35, e("10-09") + 0.6, "#FFD24A", (0.13 * 0.62, 0.13 * 0.62), 0.016, round_=True)
        # 10-09：上の列 Q W E R T Y が順に光る
        for i, ch in enumerate("QWE"): glow_plate(tk[ch], w("10-09", "クワーティ") + 0.15 * i, e("10-09") + 0.6, "#7FB0FF", (0.13 * 0.62, 0.13 * 0.62), 0.016, round_=True)
        for i, ch in enumerate("TY"): glow_plate(tk[ch], w("10-09", "クワーティ") + 0.15 * (i + 4), e("10-09") + 0.6, "#7FB0FF", (0.13 * 0.62, 0.13 * 0.62), 0.016, round_=True)
        M.at(-100.0, loc=(1.4, -0.9, 0.0), face=40)
        M.jump(s("10-08"), (1.0, -0.45, 0.89))
        M.at(s("10-08") + 2.2, face=60); M.at(s("10-08") + 1.0, look=12); M.hop(s("10-09") + 0.4, h=0.12, d=0.4)
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
    # 24-05：キーを探して、1 字ずつゆっくり打つ人（手が止まり、首をかしげる）（v5「ゆっくり打ってる感じにして」）
    sl = T_[5]; track("slowhand", sl.arms[0], 0.0)
    for k_, tt in enumerate((s("24-05") + 0.3, s("24-05") + 1.6, s("24-05") + 3.0)):
        a = sl.arms[k_ % 2]
        key(a, ("rotation_euler", 0), tt - 0.4, R(-45)); key(a, ("rotation_euler", 0), tt, R(-60)); key(a, ("rotation_euler", 0), tt + 0.15, R(-55)); key(a, ("rotation_euler", 0), tt + 0.6, R(-45))
        key(a, ("rotation_euler", 2), tt - 0.4, R(0)); key(a, ("rotation_euler", 2), tt - 0.2, R(8 if k_ % 2 else -8)); key(a, ("rotation_euler", 2), tt, R(0))
        ev(tt, "key", 0.12, "slowhand")
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
    ("S08a", b_shop_day, s("08-01"), None, "S08a"), ("S08a2", b_shop_day, s("08-02"), C((1.6, -0.7, 1.5), (1.7, 1.5, 1.25), 32, (1.4, -0.6, 1.45)), "S08a"), ("S08b", b_shop_day, s("08-03"), C((-0.9, -2.7, 1.1), (-2.0, -0.7, 0.3), 30, (-1.0, -2.6, 1.05)), "S08a"),
    ("S09a", b_shop_day, s("09-01"), None, "S09a"), ("S09b", b_shop_day, s("09-04"), C((-0.05, 0.1, 2.7), (-0.05, 0.42, 0.98), 26, (0.0, 0.12, 2.6)), "S09a"),
    ("S10a", b_shop_day, s("10-01"), None, "S10a"), ("S10a2", b_shop_day, s("10-03"), C((0.3, -0.75, 1.35), (0.0, 0.35, 1.12), 34, (0.1, -0.7, 1.4)), "S10a"),
    ("S10b", b_shop_day, s("10-04"), None, "S10b"), ("S10b1", b_shop_day, s("10-05"), C((-0.25, 0.15, 1.95), (-0.25, 0.36, 1.15), 35, (-0.2, 0.15, 1.9)), "S10b"), ("S10b2", b_shop_day, s("10-06"), C((-0.15, -0.35, 1.62), (-0.25, 0.36, 1.2), 34, (-0.12, -0.32, 1.6)), "S10b"),
    ("S10c", b_factory, s("10-07"), None, "S10c"), ("S10c2", b_factory, s("10-08"), C((0.4, -0.75, 1.35), (0.28, -0.27, 1.03), 36, (0.38, -0.72, 1.33)), "S10c"),
    ("S11a", b_shop_day, s("11-01"), None, "S11a"), ("S11b", b_shop_day, s("11-03"), C((-0.6, -3.6, 1.6), (-0.6, 0.3, 0.9), 28, (-0.3, -3.3, 1.5)), "S11a"),
    ("S12o", b_shop_day, s("12-01"), C((0.55, -1.45, 1.75), (-0.05, 0.15, 1.12), 32, (0.45, -1.3, 1.65)), "S11a"),
    ("S12a", b_inside, s("12-02"), None, "S12a"), ("S12b", b_inside, s("12-03"), C((0.3, -0.2, 1.1), (0.0, 0.95, 0.4), 28, (0.25, -0.15, 1.08)), "S12a"),
    ("S13a", b_inside, s("13-01"), C((0.85, -0.55, 1.05), (-0.28, 0.72, 0.45), 30, (0.8, -0.5, 1.0)), "S13a"), ("S13b", b_inside, s("13-03"), C((0.0, -0.5, 2.4), (0.0, 0.6, 0.0), 26, (0.2, -0.3, 2.2)), "S13a"),
    ("S13c", b_inside, s("13-05"), lambda t0: F((0.3, 0.7, 0.25), 36), "S13a"),
    ("S14a", b_inside, s("14-01"), None, "S14a"), ("S14p", b_shop_day, s("14-02"), C((-1.95, 0.0, 1.45), (-1.35, 1.05, 0.97), 34, (-1.9, 0.05, 1.4)), "S11a"),
    ("S14b", b_inside, s("14-03"), C((0.95, -1.0, 1.9), (0.0, 0.8, 0.2), 30, (0.85, -0.9, 1.85)), "S14a"),
    ("S14b2", b_inside, s("14-05"), C((0.65, 0.05, 0.85), (-0.3, 1.1, 0.3), 30, (0.6, 0.1, 0.8)), "S14a"), ("S15a", b_inside, s("15-01"), None, "S15a"), ("S15b", b_inside, s("15-03"), lambda t0: F((0.85, 0.55, 0.34), 32), "S15a"),
    ("S15c", b_inside, s("15-05"), C((0.0, -0.4, 2.5), (0.0, 0.6, 0.0), 26, (-0.2, -0.3, 2.3)), "S15a"),
    ("S15d", b_inside, s("15-07"), C((-1.6, -2.0, 0.45), (0.2, 0.6, 0.35), 24, (-1.2, -2.2, 0.5)), "S15a"),
    ("S15e", b_inside, s("15-09"), lambda t0: F((-0.7, 0.4, 0.3), 32), "S15a"),
    ("S16a", b_shop_day, s("16-01"), None, "S16a"), ("S16b", b_shop_day, s("16-03"), C((-1.0, -0.6, 1.35), (-1.5, 0.6, 1.05), 32, (-0.95, -0.55, 1.33)), "S16a"),
    ("S17a", b_tel, s("17-01"), None, "S17a"), ("S17a2", b_tel, s("17-03"), C((-0.95, -0.5, 1.25), (-0.6, 0.6, 0.98), 40, (-0.85, -0.45, 1.2)), "S17a"),
    ("S17a3", b_tel, s("17-04"), C((2.3, -1.0, 2.6), (0.4, 0.6, 0.9), 30, (2.1, -0.9, 2.5)), "S17a"),
    ("S17b", b_school, s("17-05"), None, "S17b"),
    ("S17c", b_demo, s("17-06"), None, "S17c"), ("S17c2", b_demo, s("17-07"), C((-3.4, 1.2, 1.9), (0.0, 0.5, 1.0), 30, (-3.3, 1.1, 1.88)), "S17c"),
    ("S17c3", b_demo, s("17-08"), C((2.3, -0.5, 1.95), (0.8, 0.85, 0.95), 34, (2.2, -0.4, 1.9)), "S17c"),
    ("S17c4", b_demo, s("17-09"), lambda t0: F((0.4, -0.8, 0.3), 36), "S17c"),
    ("S18a", b_tel, s("18-01"), None, "S18a"), ("S18a2", b_tel, s("18-02"), C((-0.6, -1.3, 1.6), (-0.6, 0.6, 0.95), 30, (-0.5, -1.2, 1.55)), "S18a"), ("S18b", b_tel, s("18-04"), lambda t0: F((0.3, -0.5, 0.15), 38), "S18a"),
    ("S18c", b_tel, s("18-05"), C((-2.2, -2.2, 1.6), (0.0, 0.6, 1.0), 28, (-1.9, -2.0, 1.5)), "S18a"),
    ("S19a", b_tel, s("19-01"), None, "S19a"),
    ("S19a2", b_tel, s("19-02"), C((0.2, -0.2, 1.5), (0.17, 0.45, 1.1), 32, (0.22, -0.18, 1.48)), "S19a"), ("S19b", _desk, s("19-03"), None, "S19b"), ("S19b2", _desk, s("19-05"), TOP((-0.3, 0.3, 1.6), (-0.1, 0.3, 2.2)), "S19b"),
    ("S20a", b_shop_night, s("20-01"), None, "S20a"), ("S20b", b_shop_night, s("20-03"), lambda t0: F((0.3, -0.7, 0.2), 38), "S20a"),
    ("S20c", b_shop_night, s("20-04"), C((0.5, -1.7, 1.6), (1.25, 0.15, 1.0), 32, (0.7, -1.6, 1.55)), "S20a"),
    ("S20c2", b_shop_night, s("20-05"), C((1.3, -0.45, 1.65), (1.27, 0.2, 1.18), 32, (1.32, -0.42, 1.63)), "S20a"), ("S20d", b_shop_night, s("20-06"), C((-0.8, -2.0, 1.4), (1.0, 0.4, 1.0), 30, (-0.6, -1.8, 1.35)), "S20a"),
    ("S20e", b_shop_night, s("20-07"), C((0.45, -1.35, 1.3), (0.85, -0.25, 1.05), 36, (0.55, -1.25, 1.25)), "S20a"),
    ("S21a", _desk, s("21-01"), None, "S21a"), ("S21b", _desk, s("21-03"), TOP((0.0, 0.2, 1.8), (0.4, 0.2, 3.4)), "S21a"),
    ("S22a", b_school, s("22-01"), None, "S22a"),
    ("S22a2", b_school, s("22-02"), C((-1.2, 2.2, 1.6), (-1.6, -0.3, 0.9), 30, (-1.1, 2.1, 1.58)), "S22a"), ("S22b", b_contest, s("22-03"), None, "S22b"), ("S22b2", b_contest, s("22-04"), C((-3.6, 1.0, 2.0), (-0.9, 0.9, 1.3), 30, (-3.5, 1.1, 1.95)), "S22b"),
    ("S22c", b_factory, s("22-05"), None, "S22c"),
    ("S22d", b_merge, s("22-06"), None, "S22d"), ("S22d2", b_merge, s("22-07"), lambda t0: F((0.8, -1.4, 0.3), 30, 0.4), "S22d"),
    ("S22e", b_evolve, s("22-08"), None, "S22e"),
    ("S23a", _desk, s("23-01"), lambda t0: F((0.4, -0.7, 0.3), 38), "S23a"), ("S23a2", _desk, s("23-03"), lambda t0: F((0.2, -0.9, 0.6), 32), "S23a"),
    ("S23a3", _desk, s("23-04"), TOP((1.05, 0.2, 3.4), (1.05, 0.2, 3.9)), "S23a"),
    ("S23a1", _desk, s("23-02"), None, "S23a"), ("S23b", b_lab, s("23-05"), None, "S23b"), ("S23c", b_lab, s("23-06"), None, "S23c"),
    ("S23c2", b_lab, s("23-07"), lambda t0: F((0.4, -0.8, 0.3), 36), "S23c"), ("S24a", b_office, s("24-01"), None, "S24a"), ("S24a2", b_office, s("24-03"), C((-1.9, -3.4, 2.6), (-0.6, 0.0, 0.8), 30, (-1.7, -3.3, 2.55)), "S24a"),
    ("S24b", b_office, s("24-04"), None, "S24b"), ("S24b2", b_office, s("24-05"), C((-0.3, -1.3, 1.3), (-1.3, -0.55, 0.85), 34, (-0.32, -1.27, 1.28)), "S24b"),
    ("S24c", _desk, s("24-06"), None, "S24c"), ("S24c1", _desk, s("24-07"), TOP((-0.1, -1.6, 1.7), (-0.1, -1.5, 1.9)), "S24c"), ("S24c2", _desk, s("24-08"), lambda t0: F((0.4, -0.7, 0.3), 36), "S24c"),
    ("S24c3", _desk, s("24-09"), C((0.6, -3.4, 1.4), (0.2, 0.2, 0.3), 26, (0.8, -4.2, 1.8)), "S24c"),
    ("S27a", _desk, s("27-01"), None, "S27a"), ("S27b", _desk, s("27-03"), TOP((0.0, 0.2, 1.7), (0.2, 0.2, 2.1)), "S27a"),
    ("S27b2", _desk, s("27-04"), C((-1.2, -1.0, 0.5), (0.3, 0.3, 0.1), 28, (-1.0, -1.2, 0.55)), "S27a"), ("S27c", _desk, s("27-05"), lambda t0: F((0.35, -0.75, 0.25), 38), "S27a"),
    ("S27d", _desk, s("27-06"), C((0.3, -2.0, 0.7), (0.0, 0.5, 0.4), 30, (0.3, -3.4, 1.4), (0.0, 1.0, 0.9), d=9.0), "S27a"),
    ("S28a", b_end, s("28-01"), None, "S28a"), ("S28a1", b_end, s("28-02"), C((0.0, -0.6, 0.6), (-0.2, 0.35, 0.1), 30, (0.1, -0.55, 0.55)), "S28a"),
    ("S28a15", b_end, s("28-03"), C((-0.72, -1.62, 0.32), (-1.08, -1.0, 0.04), 40, (-0.75, -1.58, 0.3)), "S28a"),
    ("S28a2", b_end, s("28-04"), lambda t0: F((0.28, -0.5, 0.14), 42, 0.08), "S28a"),
    ("S09a2", b_shop_day, s("09-03"), C((-0.35, -0.75, 1.5), (-0.8, 0.35, 1.1), 34, (-0.3, -0.7, 1.45)), "S09a"),
    ("S15b2", b_inside, s("15-04"), lambda t0: F((0.45, -0.6, 0.25), 36), "S15a"),
    ("S20a1", b_shop_night, s("20-02"), C((-0.6, -1.8, 1.5), (0.6, 0.3, 1.0), 30, (-0.4, -1.7, 1.45)), "S20a"),
    ("S28b", b_end, s("28-06"), None, "S28b"), ("S28b1", b_end, s("28-07"), C((2.4, 2.0, 2.0), (0.3, -0.6, 0.2), 28, (2.2, 1.8, 1.9)), "S28b"), ("S28b2", b_end, s("28-08"), C((1.5, -3.2, 2.2), (0.1, -0.35, 0.15), 28, (1.3, -3.0, 2.1)), "S28b"),
]
END_T = e("28-08") + 2.5
CUTS.sort(key=lambda c: c[2])   # 足したカットを時刻の順に（次のカットの頭で終わる）
CLIPS = {}
for i, (nm, fn, tc, cm, par) in enumerate(CUTS):
    t0 = max(0.0, tc - 0.1)
    t1 = (CUTS[i + 1][2] + 0.75) if i + 1 < len(CUTS) else END_T
    CLIPS[nm] = (fn, t0, t1, cm, par)
# v6：07 の小窓（S06p）はやめた（比べのグラフにした）

if __name__ == "__main__" or True:
    if CLIPNAME == "--list":
        print(json.dumps({k: [round(v[1], 3), round(v[2], 3), round(([c[2] for c in CUTS if c[0] == k] or [v[1]])[0], 3), v[4]] for k, v in CLIPS.items()}))
    else:
        fn, t0, t1, cm, par = CLIPS[CLIPNAME]
        CLOCK["T0"] = t0; CLOCK["T1"] = t1
        fn(par)
        if os.environ.get("MARU_PLANONLY"):          # まるロボの予定だけ作って、間に合わない動きを出す（描かない）
            for m_ in MARU_ALL:
                m_.plan(END_T)
                for i_, r_ in enumerate(m_.log):        # 命令の時刻・種類・その時の予定の時刻・次の命令の前の予定の時刻
                    nx = m_.log[i_ + 1][2] if i_ + 1 < len(m_.log) else -1
                    print("MARU_LOG", r_[0], r_[1], r_[2], "->", nx)
            print("MARU_LATE", json.dumps(MARU_LATE, ensure_ascii=False)); sys.exit(0)
        bake_maru(t0, t1)
        if os.environ.get("MARU_PRESSCHECK"):     # 乗った物の点検だけ（描かない）
            print("PRESSCHECK", CLIPNAME, len(PRESS_BAD), PRESS_BAD[:10])
            for _t, _n, _ in PRESS_BAD[:3]:
                _o = bpy.data.objects[_n]; _fc = [c for c in _o.animation_data.action.fcurves if c.data_path == "location" and c.array_index == 2][0]
                print("  KEYS", _n, [(round(k.co.x / FPS + CLOCK["T0"], 2), round(k.co.y, 3), k.interpolation) for k in _fc.keyframe_points if abs(k.co.x / FPS + CLOCK["T0"] - _t) < 1.0])
            sys.exit(0)
        if os.environ.get("DBG_PY"): exec(open(os.environ["DBG_PY"]).read()); sys.exit(0)
        if os.environ.get("MARU_PROBE"):          # 物の高さを調べる（点検用）
            _sc = bpy.context.scene
            for _t in [float(x) for x in os.environ["MARU_PROBE"].split(",")]:
                _sc.frame_set(f(_t)); bpy.context.view_layer.update()
                _hi = sorted(((round(o.matrix_world.translation.z, 3), o.name) for o, _d, _z in PRESS ), reverse=True)[:8]
                print("PROBE", _t, _hi)
            sys.exit(0)
        if cm is not None: cm(t0)
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
