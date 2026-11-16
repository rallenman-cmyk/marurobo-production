# 7本目（キーボード）：3D の上に重ねる 2D（キーの字・札・吹き出し・題名・小窓・棒グラフ・モールス信号の点）
#   一覧 EVENTS：(始め, 終わり, 種類, 中身)。時刻は声の時刻（timing.py）。札の答えは、その言葉を言う瞬間に出す（SKILL §3）
#   見た目は 4本目の design.py（2 倍で描いて縮める・やわらかい影・ぽんと弾んで出る 0.3 秒）。6本目の overlays.py を写して、この回の札にした
#   字の大きさ：数字・年は 56〜64、ほかは 48（キーの字は 46。1280×720 の座標。スマホで読める大きさ）。字幕の帯（y 560 より下）に置かない
#   3D の中に字を書かないので、キーの字は全部ここで、キーの場所（scenes.py の track：k_A など）に重ねる。話に出る字だけ出す
#   色：クワーティ＝青・ABC 順＝橙・いろは歌専用＝緑（3D の道のりの線と同じ）
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep04_robot", "look"))
import design as D
import timing as T
s, e, w = T.s, T.e, T.w
YEL = (255, 210, 74); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48)
BLUE = (61, 139, 255); ORANGE = (255, 154, 60); GREEN = (60, 203, 106)
SUB_TOP = 560
_cache = {}


def ev_list():
    E = []
    add = lambda *a: E.append(a)
    # 机のキーボード（k_・a_・d_・l_）は、キーの上に字を書いたので 2D の字は出さない（2026-11-16 ユーザー「最初っからＡってテロップあってもわかんない」「ボタンにそれぞれの文字表示して」）
    kl = lambda t0, t1, keys, **kw: None if all(o.split("_")[0] in ("k", "a", "d", "l") for o, _ in keys) else add(t0, t1, "keys", dict(keys=keys, **kw))
    # 01〜02：A を打つ → 画面に A。B をさがす
    kl(s("01-01"), e("02-04") + 0.3, [("k_A", "A")])
    add(w("01-04", "カタッ") + 0.1, e("01-04") + 0.5, "tag", dict(text="A", obj="screen", dy=0, size=64))
    kl(w("02-02", "S"), e("02-04") + 0.3, [("k_S", "S")]); kl(w("02-03", "反対側"), e("02-04") + 0.3, [("k_Q", "Q"), ("k_W", "W")])
    add(w("02-04", "どこ") - 0.2, e("02-04") + 0.3, "bubble", dict(obj="maru", icon="B"))
    # 03：上から。Q W E R T Y を 1 つずつ → 名前「クワーティ」。B（まるロボが着く所）
    for i, ch in enumerate("QWERTY"):
        kl(w("03-01", "Q W E R T Y") + 0.3 * i, e("03-05") + 0.3, [("k_" + ch, ch)], col=BLUE)
    kl(s("03-01") + 0.5, e("03-05") + 0.3, [("k_B", "B")])
    add(w("03-02", "クワーティ"), e("03-05") + 0.3, "tag", dict(text="Q W E R T Y ＝ クワーティ", pos=(640, 80), size=52, bg=WHITE))
    add(w("03-04", "なぜ") - 0.2, e("03-04") + 0.4, "bubble", dict(obj="maru", icon="?"))
    add(e("03-05") + 0.3, s("04-01") - 0.3, "title", {})
    # 04〜05：ABC 順のキーボード。名前の札（色は道のりと同じ）
    add(s("04-03") + 1.6, e("05-05") + 0.5, "tag", dict(text="クワーティ", obj="k_T", dy=-150, bg=BLUE, fg=WHITE))
    add(s("04-03") + 1.6, e("05-05") + 0.5, "tag", dict(text="ABC 順", obj="a_E", dy=-150, bg=ORANGE, fg=WHITE))
    kl(w("04-04", "ABC 順"), s("05-01"), [("a_A", "A"), ("a_B", "B"), ("a_C", "C")], col=ORANGE)
    add(w("05-03", "人は") - 0.1, w("05-03", "まるロボ") + 0.2, "tag", dict(text="人：10本の指", pos=(1020, 110), size=48))
    add(w("05-03", "まるロボ"), e("05-03") + 0.3, "tag", dict(text="まるロボ：1字ずつ", pos=(1000, 110), size=48))
    # MARUROBO：打った字を、打つ瞬間に（青 → 橙）
    t = w("05-04", "道のり"); dt = min(0.55, (e("05-04") + 0.4 - t) / 7)
    for i, ch in enumerate("MARUROBO"):
        kl(t + i * dt, e("05-05") + 0.6, [("k_" + ch, ch)], col=BLUE)
    t2 = s("05-05") - 0.2; dt2 = min(0.55, (e("05-05") + 0.5 - t2) / 7)
    for i, ch in enumerate("MARUROBO"):
        kl(t2 + 0.4 + i * dt2, e("05-05") + 0.6, [("a_" + ch, ch)], col=ORANGE)
    # 06：上から結果（名前の札・数字。言うときに 1 つずつ）
    add(s("06-01"), w("07-02", "いろはにほへと"), "tag", dict(text="クワーティ", obj="k_T", dy=-110, bg=BLUE, fg=WHITE, size=44))
    add(s("06-01"), w("07-02", "いろはにほへと"), "tag", dict(text="ABC 順", obj="a_E", dy=-110, bg=ORANGE, fg=WHITE, size=44))
    add(w("06-02", "キー28個分"), e("06-04") + 0.4, "tag", dict(text="キー28個分", pos=(330, 500), size=60, bg=YEL))
    add(w("06-03", "キー31個分"), e("06-04") + 0.4, "tag", dict(text="キー31個分", pos=(950, 500), size=60, bg=YEL))
    add(w("06-04", "ほとんど") - 0.1, e("06-04") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 07：いろは歌（ひらがな → ローマ字）→ 結果の棒グラフ → 名前の結果を小窓で
    add(w("07-02", "いろはにほへと"), w("07-04", "結果"), "iroha", {})
    add(w("07-04", "クワーティ"), e("07-08") + 0.3, "bars", dict(items=[(BLUE, "クワーティ", 316, w("07-04", "クワーティ")), (ORANGE, "ABC 順", 302, w("07-04", "ABC 順"))], unit="キー", vmax=330))
    add(w("07-06", "もし"), e("07-07") + 0.3, "pip_clip", dict(clip="S06p", src_t=e("06-04"), hold=True))
    add(w("07-09", "何のために") - 0.2, e("07-09") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 08〜09：1868年。ピアノのような鍵盤の字（手前 A→N 左から右、奥 O→Z 右から左）
    add(w("08-01", "1868年"), e("08-03") + 0.3, "tag", dict(text="1868年　アメリカ", pos=(640, 80), size=56))
    kl(w("09-03", "ABC"), w("09-04", "手前"), [("p_A", "A"), ("p_B", "B"), ("p_C", "C")], col=ORANGE, size=44)
    kl(w("09-04", "手前"), e("09-05") + 0.5, [("p_" + c, c) for c in "ABCDEFGHIJKLMN"], col=ORANGE, size=34, flow=0.12)
    kl(w("09-05", "奥"), e("09-05") + 0.5, [("p_" + c, c) for c in "OPQRSTUVWXYZ"], col=NAVY, size=34, flow=0.12)
    add(w("09-04", "左から右"), e("09-05") + 0.5, "arrow2", dict(a="p_A", b="p_N", dy=48, col=ORANGE))
    add(w("09-05", "右から左"), e("09-05") + 0.5, "arrow2", dict(a="p_O", b="p_Z", dy=-46, col=NAVY))
    # 10：1872年の上の列（Q W E ． T Y）→ 1873年の会社 → R が入る
    add(w("10-04", "1872年"), e("10-06") + 0.3, "tag", dict(text="1872年ごろ", pos=(1080, 80), size=56))
    for i, (o, ch) in enumerate((("m_Q", "Q"), ("m_W", "W"), ("m_E", "E"), ("m_dot", "．"), ("m_T", "T"), ("m_Y", "Y"))):
        tt = w("10-05", "Q W E") + 0.35 * min(i, 2) if i < 3 else (w("10-05", "ピリオド") if i == 3 else w("10-05", "T Y") + 0.35 * (i - 4))
        kl(tt, e("10-06") + 0.3, [(o, ch)], col=RED if ch == "．" else BLUE, size=44)
    add(w("10-07", "1873年"), e("10-09") + 0.3, "tag", dict(text="1873年", pos=(1100, 80), size=56))
    kl(s("10-08"), e("10-09") + 0.3, [("f_" + c, c) for c in "QWE"] + [("f_T", "T"), ("f_Y", "Y")], col=BLUE, size=40)
    kl(s("10-08"), w("10-08", "外され") + 0.4, [("f_dot", "．")], col=RED, size=40)
    kl(w("10-08", "R が") + 0.35, e("10-09") + 0.3, [("f_R", "R")], col=BLUE, size=40)
    add(w("10-09", "クワーティ"), e("10-09") + 0.3, "tag", dict(text="クワーティ", pos=(640, 80), size=52, bg=BLUE, fg=WHITE))
    add(w("11-01", "どうして") - 0.2, e("11-02") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 13〜14：からまる → E と R の棒
    add(s("13-02") + 0.2, e("13-02") + 0.4, "bubble", dict(obj="maru", icon="!"))
    kl(w("14-03", "E"), e("14-05") + 0.4, [("bar_E", "E"), ("bar_R", "R")], col=YEL, size=48)
    # 15：わざとゆっくり？ → 最初のお客さん（電信の部屋を小窓で先に少し）
    add(w("15-02", "わざと"), e("15-02") + 0.3, "tag", dict(text="わざと ゆっくり？", pos=(640, 80), size=52))
    add(w("15-04", "ちょっと待って") - 0.1, e("15-04") + 0.3, "bubble", dict(obj="maru", icon="?"))
    add(w("15-07", "最初のお客さん"), e("15-07") + 0.3, "pip_clip", dict(clip="S17a", src_t=s("17-04")))
    # 16〜17：日本の研究・電信・最初のお客さん・試し打ち
    add(w("16-02", "京都大学"), e("16-03") + 0.3, "tag", dict(text="京都大学　安岡孝一さんたち（2011年）", pos=(640, 80), size=48))
    add(w("17-02", "電信"), e("17-02") + 0.3, "tag", dict(text="電信", pos=(1060, 80), size=56))
    add(w("17-03", "モールス信号"), e("17-04") + 0.3, "tag", dict(text="モールス信号", pos=(1020, 80), size=52))
    add(w("17-05", "シカゴ"), e("17-05") + 0.3, "tag", dict(text="シカゴの電信の学校", pos=(640, 80), size=52))
    add(w("17-06", "1872年"), e("17-09") + 0.3, "tag", dict(text="1872年", pos=(1100, 80), size=56))
    add(w("17-08", "もっと速く"), e("17-08") + 0.5, "tag", dict(text="もっと速く！", obj="teacher", dy=-70, size=52, bg=YEL))
    # 18：Z と SE（点の並び。言うときに 1 段ずつ）
    add(w("18-02", "Z"), e("18-05") + 0.4, "morse", dict(t_z=w("18-02", "Z"), t_s=w("18-03", "S"), t_e=w("18-04", "E が"), t_same=w("18-04", "あれ")))
    # 19：迷う → Z S E が、ななめにつながる
    add(w("19-01", "迷って") - 0.1, e("19-01") + 0.3, "bubble", dict(obj="op", icon="?"))
    for ch, wd in (("Z", "この3つ"), ("S", "光らせて"), ("E", "みると")):
        kl(w("19-03", wd), e("19-05") + 0.4, [("k_" + ch, ch)], col=YEL, size=48)
    # 20：ショールズさんの別の並び（2 段目 X P M C H）
    add(w("20-04", "別の並び"), e("20-06") + 0.3, "tag", dict(text="1889年", pos=(1100, 80), size=56))
    kl(w("20-05", "X P M C H"), e("20-06") + 0.3, [("x_" + c, c) for c in "XPMCH"], col=RED, size=40, flow=0.25)
    kl(w("20-05", "クワーティ"), e("20-06") + 0.3, [("m_" + c, c) for c in "QWE"] + [("m_T", "T"), ("m_Y", "Y")], col=BLUE, size=40)
    add(w("21-02", "もっと良い") - 0.2, e("21-02") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 22：広まっていく
    add(w("22-03", "1888年"), e("22-04") + 0.3, "tag", dict(text="1888年", pos=(1100, 80), size=56))
    add(w("22-04", "キーを見ないで"), e("22-04") + 0.3, "tag", dict(text="キーを見ないで、10本の指で", pos=(640, 80), size=48))
    add(w("22-05", "1891年"), e("22-05") + 0.3, "tag", dict(text="1891年", pos=(1100, 80), size=56))
    add(w("22-05", "10万台"), e("22-05") + 0.5, "tag", dict(text="10万台", pos=(640, 200), size=64, bg=YEL))
    add(w("22-06", "1893年"), e("22-07") + 0.3, "tag", dict(text="1893年", pos=(1100, 80), size=56))
    add(w("22-07", "クワーティ"), e("22-08") + 0.3, "tag", dict(text="クワーティ", pos=(640, 80), size=52, bg=BLUE, fg=WHITE))
    # 23：速い並び（真ん中の列）→ 比べ直すと、ほぼ同じ
    add(w("23-02", "1936年"), e("23-04") + 0.3, "tag", dict(text="1936年", pos=(1100, 80), size=56))
    kl(w("23-03", "真ん中の列"), e("23-04") + 0.3, [("d_" + c, c) for c in "AOEUIDHTNS"], col=GREEN, size=40, flow=0.15)
    add(w("23-05", "考えた本人"), e("23-05") + 0.3, "tag", dict(text="考えた本人", obj="prof", dy=-60, size=48))
    add(w("23-06", "比べ直す"), e("23-07") + 0.3, "bars", dict(items=[(BLUE, "クワーティ", None, w("23-06", "比べ直す") + 0.3), ((120, 134, 156), "新しい並び", None, w("23-06", "比べ直す") + 0.8)], vmax=1.0, vals=[0.9, 0.92]))
    # 24：もしも → スマホもクワーティ
    add(w("24-04", "もし"), e("24-05") + 0.3, "tint", {})
    add(w("24-04", "もし"), e("24-05") + 0.3, "tag", dict(text="もしも…", pos=(1080, 80), size=52))
    add(w("24-07", "スマホ"), e("24-08") + 0.3, "phonekeys", dict(obj="phone"))
    # 28：いろは歌専用（距離 → 引くと、いろは順）
    add(w("28-05", "7分の1"), e("28-05") + 0.6, "tag", dict(text="クワーティの 7分の1", pos=(640, 90), size=60, bg=YEL))
    kl(w("28-06", "い ろ は"), e("28-07") + 0.4, [("l_%d" % i, c) for i, c in enumerate("いろはにほへとちりぬるを")], col=GREEN, size=40, flow=0.08)
    return sorted(E, key=lambda x: x[0])


EVENTS = None


def _pop(t, t0, t1):
    k = D.ease_out_back((t - t0) / 0.3) if t - t0 < 0.3 else 1.0
    a = 1.0 if t1 - t > 0.2 else max(0.0, (t1 - t) / 0.2)
    return max(0.05, k), a


def _paste(base, spr, cx, cy, k=1.0, a=1.0):
    if k != 1.0:
        spr = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.LANCZOS)
    if a < 1.0:
        al = spr.getchannel("A").point(lambda v: int(v * a)); spr = spr.copy(); spr.putalpha(al)
    base.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))


def tag_sprite(text, size=48, bg=WHITE, fg=None, tail=None):
    key = ("tag", text, size, bg, fg, tail)
    if key not in _cache:
        _cache[key] = D.pill(text, size, fg=fg or NAVY, bg=bg, tail=tail)
    return _cache[key]


def key_sprite(ch, size=46, col=BLUE):
    """キーの字（白い角の丸い四角に、色の字。キーの上の面に重ねる）"""
    key = ("key", ch, size, col)
    if key not in _cache:
        S2 = 2; wd = int(size * 1.35) * S2
        spr, off = D.card(wd // S2, wd // S2, r=12, draw=lambda d, W_, H_, ss, img: D.ctext(d, (W_ / 2, H_ / 2 - 2 * ss), ch, D.font(size * ss), col))
        _cache[key] = spr
    return _cache[key]


def icon_draw(kind):
    def dr(d, cx, cy, ss, img):
        f = D.font(80 * ss)
        if kind in ("?", "!", "B"):
            D.ctext(d, (cx, cy), kind, f, NAVY if kind != "!" else D.ORANGE)
    return dr


def bubble_sprite(kind):
    key = ("bub", kind)
    if key not in _cache:
        _cache[key] = D.bubble(120, 110, (0, 0), draw=icon_draw(kind))
    return _cache[key]


def title_sprite():
    key = ("title",)
    if key not in _cache:
        spr, off = D.card(1000, 330, draw=lambda d, W_, H_, ss, img: [D.ctext(d, (W_ / 2, H_ / 2 - 92 * ss), "パソコンのキーボードは、", D.font(54 * ss), NAVY),
                                                                      D.ctext(d, (W_ / 2, H_ / 2 + 0 * ss), "なぜ ABC 順に", D.font(66 * ss), D.TEAL_D),
                                                                      D.ctext(d, (W_ / 2, H_ / 2 + 92 * ss), "並んでいない？", D.font(66 * ss), D.TEAL_D)])
        _cache[key] = spr
    return _cache[key]


def iroha_sprite(k):
    """いろは歌（ひらがな 2 行 → ローマ字が下に出る）"""
    st = 1 if k >= 0.5 else 0
    key = ("iroha", st)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            D.ctext(d, (W_ / 2, 62 * ss), "いろはにほへと ちりぬるを わかよたれそ", D.font(44 * ss), NAVY)
            D.ctext(d, (W_ / 2, 122 * ss), "つねならむ うゐのおくやま けふこえて …", D.font(44 * ss), NAVY)
            if st: D.ctext(d, (W_ / 2, 186 * ss), "irohanihoheto chirinuruwo …", D.font(44 * ss), D.TEAL_D)
        _cache[key] = D.card(1000, 230 if st else 170, draw=dr)[0]
    return _cache[key]


def bars_sprite(p, t, t0):
    """棒グラフ（横の棒。名前・長さ・数字。1 本ずつ、言うときに伸びる）。card の draw の中で 2 倍の座標で描く"""
    n = len(p["items"]); Wd, Hd = 940, 60 + 100 * n
    def dr(d, W_, H_, ss, img):
        for i, (col, name, val, ti) in enumerate(p["items"]):
            if t < ti: continue
            kk = min(1.0, (t - ti) / 0.6); kk = 1 - (1 - kk) ** 3
            y = (30 + 100 * i + 50) * ss
            D.ctext(d, (130 * ss, y), name, D.font(42 * ss), NAVY)
            v = val if val is not None else p["vals"][i]
            L = 470 * v / p["vmax"] * kk
            d.rounded_rectangle([250 * ss, y - 26 * ss, (250 + max(L, 8)) * ss, y + 26 * ss], 12 * ss, fill=col + (255,))
            if val is not None and kk > 0.9:
                D.ctext(d, ((250 + L + 105) * ss, y), "%s%d" % (p.get("unit", ""), val), D.font(42 * ss), NAVY)
    return D.card(Wd, Hd, draw=dr)[0]


def morse_sprite(t, p):
    """Z ＝ ・・・　・ と、S ＋ E ＝ ・・・　・（2 段。ほとんど同じ）"""
    def dr(d, W_, H_, ss, img):
        def dots(x, y, pat, col):
            for c in pat:
                if c == " ": x += 46 * ss; continue
                d.ellipse([x, y - 15 * ss, x + 30 * ss, y + 15 * ss], fill=col); x += 48 * ss
        if t >= p["t_z"]:
            D.ctext(d, (110 * ss, 90 * ss), "Z", D.font(64 * ss), NAVY); dots(230 * ss, 90 * ss, "... .", NAVY)
        if t >= p["t_s"]:
            D.ctext(d, (110 * ss, 210 * ss), "S E", D.font(56 * ss), D.TEAL_D)
            dots(230 * ss, 210 * ss, "..." if t < p["t_e"] else "... .", D.TEAL_D)
        if t >= p["t_same"]:
            d.rounded_rectangle([210 * ss, 40 * ss, 470 * ss, 260 * ss], 20 * ss, outline=RED + (255,), width=6 * ss)
    return D.card(560, 300, draw=dr)[0]


def arrow_img(p0, p1, col):
    S2 = 2; im = Image.new("RGBA", (1280 * S2, 720 * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); ca, sa = math.cos(ang), math.sin(ang)
    L_, Hw, lw = 40, 24, 12
    tip = (p1[0] * S2, p1[1] * S2); bs = ((p1[0] - L_ * ca) * S2, (p1[1] - L_ * sa) * S2)
    d.line([(p0[0] * S2, p0[1] * S2), (bs[0] + 4 * ca, bs[1] + 4 * sa)], fill=col + (255,), width=lw * S2)
    d.polygon([tip, (bs[0] - Hw * sa * S2, bs[1] + Hw * ca * S2), (bs[0] + Hw * sa * S2, bs[1] - Hw * ca * S2)], fill=col + (255,))
    return im.resize((1280, 720), Image.LANCZOS)


def phone_keys():
    key = ("phonekeys",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            for r, row in enumerate(("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")):
                x0 = 30 * ss + r * 28 * ss
                for c, ch in enumerate(row):
                    x = x0 + c * 58 * ss; y = 28 * ss + r * 70 * ss
                    d.rounded_rectangle([x, y, x + 52 * ss, y + 62 * ss], 8 * ss, fill=(233, 238, 245), outline=(180, 190, 205), width=2 * ss)
                    D.ctext(d, (x + 26 * ss, y + 31 * ss), ch, D.font(40 * ss), BLUE if (r == 0 and c < 6) else NAVY)
        _cache[key] = D.card(650, 250, draw=dr)[0]
    return _cache[key]


_TAGS = []
GAP = [1e9]


def draw(t, base, where, frame_of=None, fontdir=None):
    global EVENTS
    if fontdir and not D.FDIR[0]: D.FDIR[0] = fontdir
    if EVENTS is None: EVENTS = ev_list()
    _TAGS.clear()
    # その時に出ているキーの字を全部集めて、となりとの間がいちばん狭い所を測る（字は 1 字ずつ別の出し方のことが多いため）
    pts = []
    for t0_, t1_, k_, p_ in EVENTS:
        if k_ == "keys" and t0_ <= t < t1_:
            for i_, (o_, _) in enumerate(p_["keys"]):
                if t < t0_ + p_.get("flow", 0.0) * i_: continue
                q_ = where(o_, t)
                if q_ is not None and 0 <= q_[0] <= 1280 and 0 <= q_[1] <= SUB_TOP - 10: pts.append(q_)
    GAP[0] = min((((a_[0] - b_[0]) ** 2 + (a_[1] - b_[1]) ** 2) ** 0.5 for i_, a_ in enumerate(pts) for b_ in pts[i_ + 1:]), default=1e9)
    for t0, t1, kind, p in EVENTS:
        if not (t0 <= t < t1): continue
        k, a = _pop(t, t0, t1)
        if kind == "tag":
            # いろは歌の札が出ている間は、上の方の板の名前を出さない（札の下に隠れて半分だけ見えたため。7本目 v1 の 2:26）
            if any(k_ == "iroha" and a_ <= t < b_ for a_, b_, k_, _ in EVENTS) and not p.get("keep"): continue
            if p.get("obj", "")[:2] in ("k_", "a_") and p.get("obj") in ("k_T", "a_E", "k_V", "a_V"):
                # 2 台の名前・距離の札は、2 台とも画面に入った引きの絵だけに出す（寄った絵では、別のキーボードの上に出てしまった。7本目 v5 の 1:34〜2:16）
                qa, qb = where("k_T", t), where("a_E", t)
                if qa is None or qb is None or not all(20 <= q[0] <= 1260 and 20 <= q[1] <= SUB_TOP for q in (qa, qb)) or abs(qa[0] - qb[0]) < 380: continue
            if "pos" in p: cx, cy = p["pos"]
            else:
                q = where(p["obj"], t)
                if q is None: continue
                cx, cy = q[0] + p.get("dx", 0), min(max(70, q[1] + p.get("dy", -120)), SUB_TOP - 60)
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), p.get("fg"))
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            # 札どうしが重なるときは、あとの札を下へずらす（7本目 v1 の 1:49 で「クワーティ」が「ABC 順」の下に隠れた）
            x0 = cx + off[0] + spr.width / 2 - spr.width / 2
            for _ in range(4):
                y0 = cy + off[1]
                hit = [r for r in _TAGS if x0 < r[2] and r[0] < x0 + spr.width and y0 < r[3] and r[1] < y0 + spr.height]
                if not hit: break
                cy = max(r[3] for r in hit) + 8 - off[1]
            _TAGS.append((x0, cy + off[1], x0 + spr.width, cy + off[1] + spr.height))
            _paste(base, spr, cx + (off[0] + spr.width / 2), cy + (off[1] + spr.height / 2), k, a)
        elif kind == "keys":
            fl = p.get("flow", 0.0)
            # 引いた絵でキーの字どうしが重なるときは、となりとの間に合わせて小さくする（7本目 v1 の 0:56・10:08 で字が重なった）
            sz = p.get("size", 46)
            if GAP[0] * 0.85 < 30: continue     # 遠くて字が重なるだけなら出さない（7本目 v1 の 0:52〜0:58・1:55）
            sz = min(sz, int(GAP[0] * 0.85))
            for i, (obj, ch) in enumerate(p["keys"]):
                ti = t0 + fl * i
                if t < ti: continue
                q = where(obj, t)
                if q is None or not (0 <= q[0] <= 1280 and 0 <= q[1] <= SUB_TOP - 10): continue
                k2, a2 = _pop(t, ti, t1)
                _paste(base, key_sprite(ch, sz, p.get("col", BLUE)), q[0], q[1], k2, a2)
        elif kind == "bubble":
            q = where(p["obj"], t)
            if q is None or not (-20 <= q[0] <= 1300 and -20 <= q[1] <= 700): continue
            spr, off = bubble_sprite(p["icon"])
            cx = min(max(q[0], spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(q[1] - 40 - spr.height / 2, spr.height / 2 + 10), SUB_TOP - spr.height / 2)
            _paste(base, spr, cx, cy, k, a)
        elif kind == "title":
            base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(120 * a))))
            _paste(base, title_sprite(), 640, 290, k, a)
        elif kind == "iroha":
            _paste(base, iroha_sprite(0.0 if t < w("07-03", "ローマ字") else 1.0), 640, 150, k, a)
        elif kind == "bars":
            _paste(base, bars_sprite(p, t, t0), 640, 175, k, a)
        elif kind == "morse":
            _paste(base, morse_sprite(t, p), 640, 230, k, a)
        elif kind == "arrow2":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            im = arrow_img((qa[0], qa[1] + p["dy"]), (qb[0], qb[1] + p["dy"]), p.get("col", NAVY))
            if a < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            base.alpha_composite(im)
        elif kind == "tint":      # もしも：少し青く暗く（ふだんの場面と分かるように）
            base.alpha_composite(Image.new("RGBA", base.size, (40, 60, 120, int(70 * a))))
        elif kind == "phonekeys":
            q = where(p["obj"], t)
            if q is None: continue
            _paste(base, phone_keys(), min(max(q[0], 280), 1000), max(150, q[1] - 170), k, a)
        elif kind == "pip_clip" and frame_of:
            im = frame_of(p["clip"], p["src_t"] + (0 if p.get("hold") else (t - t0)))
            if im is None: continue
            im = im.convert("RGB").resize((400, 225), Image.LANCZOS)
            fr = Image.new("RGBA", (412, 237), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            _paste(base, fr, 30 + 206, 25 + 118, k, a)
    return base
