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
YEL = (255, 210, 74); NAVY = D.NAVY; NAVY2 = D.NAVY2; WHITE = (255, 255, 255); RED = (226, 58, 48)
BLUE = (61, 139, 255); ORANGE = (255, 154, 60); GREEN = (60, 203, 106)
SUB_TOP = 560
_cache = {}


def ev_list():
    """v6（絵コンテ_v6.md と見比べて作る）。キーの字は全部 3D に書いたので、2D でキーの字は出さない"""
    E = []
    add = lambda *a: E.append(a)
    # 01〜02：A を打つ → A のキーから「A」が浮き上がって左上へ（v5「最初っからＡってテロップあってもわかんない」）
    tA = w("01-04", "ぴょん") + 0.18
    add(tA, e("02-04") + 0.3, "typed", dict(items=[("k_A", "A", tA, 0, 0, NAVY)]))
    add(w("02-04", "どこ") - 0.2, e("02-04") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 03：名前「クワーティ」（キーが浮き上がるのは 3D）
    add(w("03-02", "クワーティ"), e("03-03") + 0.3, "tag", dict(text="Q W E R T Y ＝ クワーティ", pos=(640, 80), size=52, bg=WHITE))
    add(w("03-04", "なぜ") - 0.2, e("03-04") + 0.4, "bubble", dict(obj="maru", icon="?"))
    add(e("03-05") + 0.3, s("04-01") - 0.3, "title", {})
    # 04〜05：名前の札（引きの絵だけ）・打つ言葉・人とまるロボの札（2 つ同時に）
    add(s("04-03") + 1.6, e("05-05") + 0.5, "tag", dict(text="クワーティ", obj="k_T", dy=-150, bg=BLUE, fg=WHITE))
    add(s("04-03") + 1.6, e("05-05") + 0.5, "tag", dict(text="ABC 順", obj="a_E", dy=-150, bg=ORANGE, fg=WHITE))
    add(w("05-02", "マルロボ"), s("05-04"), "tag", dict(text="マルロボ ＝ M A R U R O B O", pos=(640, 80), size=52))
    add(w("05-03", "人は") - 0.1, e("05-03") + 0.3, "tag", dict(text="人：10本の指", pos=(330, 110), size=46, keep=True))
    add(w("05-03", "まるロボ"), e("05-03") + 0.3, "tag", dict(text="まるロボ：1字ずつ", pos=(950, 110), size=46, keep=True))
    # MARUROBO：押したキーから字が浮き上がって、左上に並ぶ（v5「該当のキーを押したらその文字が浮かび上がって まるろぼ になるように」）
    t = w("05-04", "道のり"); dt = min(0.55, (e("05-04") + 0.4 - t) / 7)
    t2 = s("05-05") - 0.2 + 0.4; dt2 = min(0.55, (e("05-05") + 0.5 - (t2 - 0.4)) / 7)
    it = [("k_" + ch, ch, t + i * dt, i, 0, BLUE) for i, ch in enumerate("MARUROBO")]
    it += [("a_" + ch, ch, t2 + i * dt2, i, 1, ORANGE) for i, ch in enumerate("MARUROBO")]
    add(t, e("05-05") + 0.6, "typed", dict(items=it))
    # 06：結果（名前の札は引きの絵だけ。距離の札は決まった場所）
    add(s("06-01"), w("07-02", "いろはにほへと"), "tag", dict(text="クワーティ", obj="k_T", dy=-110, bg=BLUE, fg=WHITE, size=44))
    add(s("06-01"), w("07-02", "いろはにほへと"), "tag", dict(text="ABC 順", obj="a_E", dy=-110, bg=ORANGE, fg=WHITE, size=44))
    add(w("06-02", "キー28個分"), e("06-04") + 0.4, "tag", dict(text="キー28個分", pos=(330, 500), size=60, bg=YEL))
    add(w("06-03", "キー31個分"), e("06-04") + 0.4, "tag", dict(text="キー31個分", pos=(950, 500), size=60, bg=YEL))
    add(w("06-04", "ほとんど") - 0.1, e("06-04") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 07：いろは歌 → 比べのグラフ（題つき。予想の点線 → 2 組 → ✕）（v5「話の内容に見せ方があってない」）
    add(w("07-02", "いろはにほへと"), w("07-04", "結果"), "iroha", {})
    add(w("07-04", "クワーティ"), e("07-08") + 0.3, "cmp", dict(t_irq=w("07-04", "クワーティ"), t_ira=w("07-04", "ABC 順"), t_long=w("07-05", "長く"),
                                                             t_pred=w("07-06", "ずっと短く"), t_name=w("07-07", "名前"), t_x=w("07-08", "打つ距離")))
    add(w("07-09", "何のために") - 0.2, e("07-09") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 08〜09：1868年。人の名前の札。ピアノの形の鍵盤（字は 3D）・向きの矢印
    add(w("08-01", "1868年"), e("08-03") + 0.3, "tag", dict(text="1868年　アメリカ", pos=(640, 80), size=56))
    add(w("08-02", "ショールズさん"), e("08-02") + 0.3, "tag", dict(text="ショールズさん", obj="sholes", dy=-80, size=46, keep=True))
    add(w("08-02", "仲間"), e("08-02") + 0.3, "tag", dict(text="仲間", obj="nakama", dy=-80, size=46, keep=True))
    add(w("09-04", "左から右"), e("09-05") + 0.5, "arrow2", dict(a="p_A", b="p_N", dy=48, col=ORANGE))
    add(w("09-05", "右から左"), e("09-05") + 0.5, "arrow2", dict(a="p_O", b="p_Z", dy=-46, col=NAVY))
    # 10：1872年・1873年・クワーティ
    add(w("10-04", "1872年"), e("10-06") + 0.3, "tag", dict(text="1872年ごろ", pos=(1080, 80), size=56))
    add(w("10-07", "1873年"), e("10-09") + 0.3, "tag", dict(text="1873年", pos=(1100, 80), size=56))
    add(w("10-09", "クワーティ"), e("10-09") + 0.3, "tag", dict(text="クワーティ", pos=(640, 80), size=52, bg=BLUE, fg=WHITE))
    add(w("11-01", "どうして") - 0.2, e("11-01") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 13〜15：説（引用の札）・からまる・わざとゆっくり
    add(s("13-04"), e("13-04") + 0.3, "tag", dict(text="よく続けて打つ字を、わざと離した？", pos=(640, 80), size=46))
    add(s("13-02") + 0.6, e("13-02") + 0.4, "bubble", dict(obj="maru", icon="!"))
    add(w("14-05", "おかしい") - 0.2, e("14-05") + 0.3, "bubble", dict(obj="maru", icon="?"))
    add(w("15-02", "わざと"), e("15-02") + 0.3, "tag", dict(text="わざと ゆっくり打たせた？", pos=(640, 80), size=50))
    add(w("15-04", "ちょっと待って") - 0.1, e("15-04") + 0.3, "bubble", dict(obj="maru", icon="?"))
    add(w("15-05", "手で書く"), e("15-05") + 0.3, "note", dict(style="speed"))
    add(w("15-06", "わざと"), e("15-06") + 0.3, "note", dict(style="nobuy", t_x=w("15-06", "いなく")))
    add(w("15-07", "最初のお客さん"), e("15-07") + 0.3, "pip_clip", dict(clip="S17a", src_t=s("17-04")))
    add(s("15-08"), e("15-08") + 0.3, "note", dict(style="deny", t_x=w("15-08", "否定")))
    # 16〜17：研究・電信・学校・試し打ち（人の札）
    add(w("16-02", "京都大学"), e("16-03") + 0.3, "tag", dict(text="京都大学　安岡孝一さんたち（2011年）", pos=(640, 80), size=48))
    add(w("17-02", "電信"), e("17-02") + 0.3, "tag", dict(text="電信", pos=(1060, 80), size=56))
    add(w("17-03", "モールス信号"), e("17-04") + 0.3, "tag", dict(text="モールス信号", pos=(1020, 80), size=52))
    add(w("17-05", "シカゴ"), e("17-05") + 0.3, "tag", dict(text="シカゴの電信の学校", pos=(640, 80), size=52))
    add(w("17-06", "1872年"), e("17-09") + 0.3, "tag", dict(text="1872年", pos=(1100, 80), size=56))
    add(w("17-06", "えらい人"), e("17-07") + 0.3, "tag", dict(text="電信の会社のえらい人", obj="boss", dy=-90, size=44, keep=True))
    add(w("17-07", "学校の先生"), e("17-08") + 0.3, "tag", dict(text="学校の先生", obj="teacher", dy=-90, size=44, keep=True))
    add(w("17-08", "もっと速く"), e("17-08") + 0.5, "tag", dict(text="「もっと速く！」", pos=(640, 170), size=56, bg=YEL))
    # 18：Z と SE
    add(w("18-02", "Z"), e("18-05") + 0.4, "morse", dict(t_z=w("18-02", "Z"), t_s=w("18-03", "S"), t_e=w("18-04", "E が"), t_same=w("18-04", "あれ")))
    # 19：迷う
    add(w("19-01", "迷って") - 0.1, e("19-01") + 0.3, "bubble", dict(obj="op", icon="?"))
    # 20：予想・からみの小窓・特許の書類・1889年
    add(w("20-01", "予想"), e("20-01") + 0.3, "tag", dict(text="研究者の予想", pos=(640, 80), size=50))
    add(w("20-02", "棒のからみ"), e("20-02") + 0.3, "pip_clip", dict(clip="S13a", src_t=s("13-02") - 0.2))
    add(w("20-04", "特許"), e("20-04") + 0.4, "note", dict(style="patent"))
    add(w("20-05", "その並び"), e("20-06") + 0.3, "tag", dict(text="1889年", pos=(1100, 80), size=56))
    add(w("21-02", "もっと良い") - 0.2, e("21-02") + 0.3, "bubble", dict(obj="maru", icon="?"))
    # 22：広まっていく
    add(w("22-03", "1888年"), e("22-04") + 0.3, "tag", dict(text="1888年", pos=(1100, 80), size=56))
    add(w("22-04", "キーを見ないで"), e("22-04") + 0.3, "tag", dict(text="キーを見ないで、10本の指で", pos=(640, 80), size=48))
    add(w("22-05", "1891年"), e("22-05") + 0.3, "tag", dict(text="1891年", pos=(1100, 80), size=56))
    add(w("22-05", "10万台"), e("22-05") + 0.5, "tag", dict(text="10万台", pos=(640, 200), size=64, bg=YEL))
    add(w("22-06", "1893年"), e("22-07") + 0.3, "tag", dict(text="1893年", pos=(1100, 80), size=56))
    add(w("22-07", "クワーティ"), e("22-08") + 0.3, "tag", dict(text="クワーティ", pos=(640, 80), size=52, bg=BLUE, fg=WHITE))
    # 23：速い並び（真ん中の列は 3D で光る）→ 比べ直すと、ほぼ同じ（グラフに題）
    add(w("23-02", "1936年"), e("23-04") + 0.3, "tag", dict(text="1936年", pos=(1100, 80), size=56))
    add(w("23-05", "考えた本人"), e("23-05") + 0.3, "tag", dict(text="考えた本人", obj="prof", dy=-60, size=48))
    add(w("23-06", "比べ直す"), e("23-07") + 0.3, "bars", dict(title="打つ速さ（国の役所の比べ直し）", items=[(BLUE, "クワーティ", None, w("23-06", "比べ直す") + 0.3), ((120, 134, 156), "新しい並び", None, w("23-06", "比べ直す") + 0.8)], vmax=1.0, vals=[0.9, 0.92]))
    # 24：もしも → 指が止まる → スマホもクワーティ
    add(w("24-04", "もし"), e("24-05") + 0.3, "tint", {})
    add(w("24-04", "もし"), e("24-05") + 0.3, "tag", dict(text="もしも…", pos=(1080, 80), size=52))
    add(w("24-05", "指が止まって") - 0.2, e("24-05") + 0.3, "bubble", dict(obj="slowhand", icon="?"))
    add(w("24-07", "スマホ"), e("24-08") + 0.3, "phonekeys", dict(obj="phone"))
    # 28：いろは歌専用（7分の1）
    add(w("28-05", "7分の1"), e("28-05") + 0.6, "tag", dict(text="クワーティの 7分の1", pos=(640, 90), size=60, bg=YEL))
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
    n = len(p["items"]); top = 70 if p.get("title") else 0; Wd, Hd = 940, 60 + 100 * n + top
    def dr(d, W_, H_, ss, img):
        if top: D.ctext(d, (W_ / 2, 48 * ss), p["title"], D.font(40 * ss), NAVY)     # 何の比べか（v5「何の違いを示したグラフかかいてよ」）
        for i, (col, name, val, ti) in enumerate(p["items"]):
            if t < ti: continue
            kk = min(1.0, (t - ti) / 0.6); kk = 1 - (1 - kk) ** 3
            y = (top + 30 + 100 * i + 50) * ss
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


def cmp_sprite(t, p):
    """07 の比べ（題つき）。いろは歌 → 予想の点線の棒 → マルロボ → 「距離を短くするため？」に ✕（v5「話の内容に見せ方があってない」）"""
    xs = t >= p["t_x"]
    def dr(d, W_, H_, ss, img):
        D.ctext(d, (W_ / 2, 44 * ss), "打つ距離（キー何個分）", D.font(40 * ss), NAVY)
        y = 100
        def bar(name, val, mx, col, tt, yy, dash=False):
            if name: D.ctext(d, (120 * ss, yy * ss), name, D.font(38 * ss), NAVY)
            kk = min(1.0, (t - tt) / 0.6); kk = 1 - (1 - kk) ** 3; L = 420 * val / mx * kk
            if dash:
                x = 230
                while x < 230 + L:
                    d.rounded_rectangle([x * ss, (yy - 16) * ss, min(x + 22, 230 + L) * ss, (yy + 16) * ss], 6 * ss, outline=BLUE + (255,), width=4 * ss); x += 34
                if kk > 0.9: D.ctext(d, ((230 + L + 80) * ss, yy * ss), "予想", D.font(36 * ss), BLUE)
            else:
                d.rounded_rectangle([230 * ss, (yy - 18) * ss, (230 + max(L, 8)) * ss, (yy + 18) * ss], 9 * ss, fill=col + (255,))
                if kk > 0.9: D.ctext(d, ((230 + L + 60) * ss, yy * ss), "%d" % val, D.font(38 * ss), NAVY)
        if t >= p["t_irq"]:
            D.ctext(d, (120 * ss, (y + 30) * ss), "いろは歌", D.font(38 * ss), NAVY)
            bar("", 316, 316, BLUE, p["t_irq"], y + 6)
            if t >= p["t_ira"]: bar("", 302, 316, ORANGE, p["t_ira"], y + 54)
            if t >= p["t_pred"]: bar("", 302 * 0.55, 316, BLUE, p["t_pred"], y + 102, dash=True)
        y = 290
        if t >= p["t_name"]:
            D.ctext(d, (120 * ss, (y + 24) * ss), "マルロボ", D.font(38 * ss), NAVY)
            bar("", 28, 31, BLUE, p["t_name"], y)
            bar("", 31, 31, ORANGE, p["t_name"] + 0.3, y + 48)
        if xs:
            D.ctext(d, (W_ / 2 - 40 * ss, 420 * ss), "距離を短くするため？", D.font(40 * ss), NAVY)
            kk = min(1.0, (t - p["t_x"]) / 0.3); cx, cy, r = (W_ / ss / 2 + 230), 420, 26 * kk
            d.line([((cx - r) * ss, (cy - r) * ss), ((cx + r) * ss, (cy + r) * ss)], fill=RED + (255,), width=10 * ss)
            d.line([((cx + r) * ss, (cy - r) * ss), ((cx - r) * ss, (cy + r) * ss)], fill=RED + (255,), width=10 * ss)
    return D.card(900, 470 if xs else 380, draw=dr)[0]


def note_sprite(t, p):
    """15・20 の説明の札（速さの比べ・買わない・否定のはんこ・特許の書類）"""
    st = p["style"]
    def dr(d, W_, H_, ss, img):
        if st == "speed":
            D.ctext(d, (W_ / 2, 44 * ss), "字を書く速さ", D.font(40 * ss), NAVY)
            for k_, (name, L, col) in enumerate((("手で書く", 150, (150, 160, 175)), ("タイプライター", 430, BLUE))):
                y = (110 + 70 * k_) * ss
                D.ctext(d, (150 * ss, y), name, D.font(34 * ss), NAVY)
                d.rounded_rectangle([290 * ss, y - 20 * ss, (290 + L) * ss, y + 20 * ss], 10 * ss, fill=col + (255,))
            D.ctext(d, ((290 + 430 + 56) * ss, 180 * ss), "速い", D.font(36 * ss), BLUE)
        elif st == "nobuy":
            D.ctext(d, (W_ / 2, 60 * ss), "わざと遅いタイプライター", D.font(42 * ss), NAVY)
            D.ctext(d, (W_ / 2, 140 * ss), "高いのに、遅い", D.font(40 * ss), (120, 130, 145))
            if t >= p["t_x"]:
                D.ctext(d, (W_ / 2, 215 * ss), "→ 買う人がいない", D.font(42 * ss), RED)
        elif st == "deny":
            D.ctext(d, (330 * ss, 110 * ss), "「わざと遅く打たせた」", D.font(46 * ss), NAVY)
            if t >= p["t_x"]:      # はんこ「否定」（字に重ねない）
                kk = min(1.0, (t - p["t_x"]) / 0.25); r = 70 * (1.4 - 0.4 * kk)
                d.ellipse([(720 - r) * ss, (110 - r) * ss, (720 + r) * ss, (110 + r) * ss], outline=RED + (255,), width=8 * ss)
                D.ctext(d, (720 * ss, 110 * ss), "否定", D.font(int(46 * r / 70) * ss), RED)
        elif st == "patent":
            D.ctext(d, (W_ / 2, 50 * ss), "特許の申し込み（1889年）", D.font(42 * ss), NAVY)
            D.ctext(d, (W_ / 2, 108 * ss), "ショールズ", D.font(36 * ss), NAVY2)
            # 資料で確かめたのは「2 段目が X P M C H で始まる」ことだけ。ほかのキーは字を書かない
            rows = (["", ""] * 4, ["X", "P", "M", "C", "H", "", "", ""], [""] * 7)
            for r, row in enumerate(rows):
                for c, ch in enumerate(row):
                    x = ((760 - len(row) * 74) / 2 + r * 18 - 9 + c * 74) * ss; y = (160 + r * 70) * ss
                    d.rounded_rectangle([x, y, x + 62 * ss, y + 58 * ss], 10 * ss, fill=(255, 255, 255, 255), outline=(150, 140, 120, 255), width=3 * ss)
                    D.ctext(d, (x + 31 * ss, y + 29 * ss), ch, D.font(34 * ss), RED if (r == 1 and c < 5) else NAVY)
    hh = {"speed": 230, "nobuy": 270, "deny": 220, "patent": 400}[st]
    bg = (250, 244, 228) if st == "patent" else WHITE
    return D.card(860 if st != "patent" else 760, hh, bg=bg, draw=dr)[0]


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
        elif kind == "typed":      # 押したキーから字が浮き上がって、左上の列に並ぶ
            for obj, ch, ti, slot, row, col in p["items"]:
                if t < ti: continue
                gx, gy = 70 + 64 * slot, 60 + 74 * row
                q = where(obj, ti)
                kk = min(1.0, (t - ti) / 0.5); kk = 1 - (1 - kk) ** 3
                if q is None or not (0 <= q[0] <= 1280 and 0 <= q[1] <= 720): kk = 1.0; q = (gx, gy)
                x = q[0] + (gx - q[0]) * kk; y = q[1] - 40 * math.sin(math.pi * kk) + (gy - q[1]) * kk
                _paste(base, key_sprite(ch, 44, col), x, y, 1.0, a)
        elif kind == "cmp":
            _paste(base, cmp_sprite(t, p), 640, 270, k, a)
        elif kind == "note":
            _paste(base, note_sprite(t, p), 640, 240, k, a)
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
