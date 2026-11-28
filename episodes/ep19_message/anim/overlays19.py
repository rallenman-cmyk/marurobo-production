# 19本目（メッセージの旅）：3D の上に重ねる 2D（札・吹き出し・題名・時計・小窓の絵）。17本目の overlays.py の作りを写した
#   一覧 EVENTS：(始め, 終わり, 種類, 中身)。時刻は声の時刻（timing.py。言葉に合わせる所は wp）。絵コンテ表：../絵コンテ_v1.md
#   決まり：札の答えは、その言葉を言う瞬間に出す。字幕の帯（y 560 より下）に置かない。下の字幕と同じことを上に書かない（単語・数字・ラベルだけ）
#   字の大きさ：数字は 56 以上、ほかは 44〜48（1280×720）。3D の中に字を書かないので、字は全部ここ
#   色：まるロボの包み＝青緑。注目・だめ＝赤
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep04_robot", "look"))
import design as D
import timing as T
s, e, w, wp = T.s, T.e, T.w, T.wp
YEL = (255, 201, 40); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48)
ORANGE = (255, 138, 31); TEAL = D.TEAL; BLUE = (52, 120, 230); GREY = (190, 198, 210)
SUB_TOP = 560
TEX19 = os.environ.get("TEX19") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "tex19")
_cache = {}
EVENTS = None


# ---------------------------------------------------------------- 時計（03-04 から出したまま。動く所だけ進め、説明のあいだは止める）
def clock_keys():
    K = [(0.0, 0.0), (s("03-07") + 0.3, 0.0), (e("03-07") + 0.6, 0.001),
         (wp("04-02", "ネジ") + 0.4, 0.001), (wp("04-02", "ネジ") + 2.6, 0.004),
         (s("05-02") + 0.1, 0.004), (s("05-02") + 2.4, 0.008),
         (s("08-01") + 0.2, 0.008), (s("08-02") + 0.3, 0.010), (wp("08-06", "着いて") - 0.1, 0.030)]
    return K


def clock_val(t):
    K = clock_keys(); v = K[0][1]
    for (ta, va), (tb, vb) in zip(K, K[1:]):
        if t <= ta: return va
        if t <= tb: return va + (vb - va) * (t - ta) / max(1e-6, tb - ta)
        v = vb
    return v


def clock_sprite(v, big=False):
    key = ("clock", round(v, 3), big)
    if key not in _cache:
        sz = 64 if big else 50
        def dr(d, W_, H_, ss, img):
            f = D.font(sz * ss); fs = D.font(int(sz * 0.62) * ss)
            tx = "%.3f" % v; wt = d.textlength(tx, font=f); ws = d.textlength(" 秒", font=fs)
            x0 = W_ / 2 - (wt + ws) / 2
            d.ellipse((x0 - 52 * ss, H_ / 2 - 20 * ss, x0 - 12 * ss, H_ / 2 + 20 * ss), outline=NAVY, width=5 * ss)   # 時計の丸（針 2 本）
            d.line((x0 - 32 * ss, H_ / 2, x0 - 32 * ss, H_ / 2 - 13 * ss), fill=NAVY, width=4 * ss); d.line((x0 - 32 * ss, H_ / 2, x0 - 22 * ss, H_ / 2 + 4 * ss), fill=NAVY, width=4 * ss)
            d.text((x0, H_ / 2), tx, font=f, fill=NAVY, anchor="lm"); d.text((x0 + wt, H_ / 2 + 4 * ss), " 秒", font=fs, fill=NAVY, anchor="lm")
        spr, off = D.card(330 if not big else 420, 86 if not big else 108, draw=dr)
        _cache[key] = spr
    return _cache[key]


# ---------------------------------------------------------------- 一覧
def ev_list():
    E = []
    add = lambda *a: E.append(a)
    # 冒頭
    add(wp("01-02", "お気に入り") - 0.1, e("01-02") + 0.3, "bubble", dict(obj="maru_top", icon="heart"))
    add(wp("01-06", "印") + 0.3, e("01-06") + 0.4, "bubble", dict(obj="maru_top", icon="?"))
    add(s("02-01") - 0.05, e("02-01") + 0.3, "tag", dict(text="送信 → 届く：0.2 秒ほど", pos=(640, 92), size=52))
    add(s("02-04") + 0.5, s("02-04") + 2.1, "bubble", dict(obj="maru_top", icon="?"))
    add(s("02-05") - 0.05, e("02-07") + 0.4, "shatter", dict(t_split=wp("02-05", "かけら") - 0.1, t_more=s("02-06") + 0.1, t_join=wp("02-07", "元どおり") - 0.4))
    add(wp("02-06", "2,000個") - 0.1, e("02-06") + 0.3, "tag", dict(text="約 2,000 個", pos=(308, 395), size=56, bg=YEL))
    add(s("03-01") - 0.05, e("03-01") + 0.5, "title", {})
    add(s("03-03") + 0.1, s("03-03") + 2.0, "slow", {})
    add(s("03-04") - 0.05, 1e9, "clock", {})
    add(s("03-05") - 0.05, e("03-05") + 0.3, "tag", dict(text="0.2 秒で届く場合の目安", pos=(1060, 142), size=44))
    # 1章
    add(s("04-03") + 0.3, s("04-03") + 1.9, "bubble", dict(obj="maru_top", icon="?"))
    add(wp("04-06", "あ") - 0.1, e("04-07") + 0.4, "charnum", dict(t2=wp("04-07", "い") - 0.1, t_num=wp("04-06", "12354") - 0.1))
    add(s("04-08") - 0.05, e("04-09") + 0.4, "pixel", dict(t_zoom=s("04-09") + 0.1))
    add(s("04-11") + 0.1, e("04-11") + 0.3, "conv", dict(t_w=wp("04-11", "電波") - 0.1, t_l=wp("04-11", "光") - 0.1))
    add(wp("05-04", "パケット") - 0.1, e("05-04") + 0.4, "tag", dict(text="パケット", obj="packet", dy=-170, size=56, bg=YEL))
    for k_, (lid, wd, tx) in enumerate((("06-02", "あて先", "あて先"), ("06-06", "送り主", "送り主"), ("06-09", "番号", "番号"))):
        add(wp(lid, wd) - 0.1, e("06-12") + 0.3, "tag", dict(text=tx, pos=(1140, 160 + 76 * k_), size=48, bg=TEAL, fg=WHITE))   # 時計（右上）の下へ（下の 2D の点検：時計に重なった）
    add(wp("06-05", "大きな建物") - 0.3, e("06-12") + 0.3, "bldg", dict(pos=(985, 160)))
    add(s("06-03") - 0.05, e("06-04") + 0.4, "envelope", dict(side="front", t_x=wp("06-04", "ありません") - 0.2))
    add(s("06-07") - 0.05, e("06-08") + 0.4, "envelope", dict(side="back", t_ret=wp("06-08", "送り主") - 0.4))
    add(s("06-10") + 0.3, s("06-10") + 1.9, "bubble", dict(obj="maru_top", icon="?"))
    add(wp("07-02", "480文字") - 0.2, e("07-04") + 0.3, "tag", dict(text="1 つの包み：日本語で約 480 文字まで", pos=(640, 470), size=48))   # 小窓と時計に重なった → 小窓の下（字幕の帯の上）
    add(s("07-03") - 0.05, e("07-03") + 0.4, "genkou", {})
    add(s("08-07") - 0.05, e("08-07") + 0.4, "map", {})
    add(s("08-08") - 0.05, e("08-08") + 0.3, "clockbig", {})
    add(s("08-10") + 0.9, s("08-10") + 2.5, "bubble", dict(obj="maru_top", icon="?"))
    return E


def sfx_list():
    """札・図に合わせて鳴らす音：(時刻, 種類, 大きさ)"""
    L = []
    L.append((s("02-01"), "pop", 0.3))
    L.append((wp("02-05", "かけら") - 0.1, "paper", 0.3)); L.append((wp("02-07", "元どおり") - 0.4, "shimmer", 0.3))
    L.append((s("03-01"), "pop", 0.35)); L.append((s("03-03") + 0.1, "rewind", 0.3)); L.append((s("03-04"), "pi", 0.3))
    L.append((wp("04-06", "12354") - 0.1, "pi", 0.3)); L.append((wp("04-07", "い") - 0.1, "pi", 0.3)); L.append((s("04-09") + 0.1, "pi", 0.3))
    L.append((wp("05-04", "パケット") - 0.1, "pop", 0.3))
    L.append((s("06-03"), "paper", 0.3)); L.append((wp("06-04", "ありません") - 0.2, "x_mark", 0.3)); L.append((s("06-07"), "paper", 0.3))
    L.append((wp("06-05", "大きな建物") - 0.3, "pop", 0.25))
    L.append((wp("07-02", "480文字") - 0.2, "pop", 0.3)); L.append((s("07-03"), "paper", 0.3))
    L.append((s("08-07"), "swish", 0.25)); L.append((s("08-08"), "pi", 0.3))
    return L


# ---------------------------------------------------------------- 絵
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


def tag_sprite(text, size=48, bg=WHITE, fg=None):
    key = ("tag", text, size, bg, fg)
    if key not in _cache: _cache[key] = D.pill(text, size, fg=fg or NAVY, bg=bg)
    return _cache[key]


def bubble_sprite(kind):
    key = ("bub", kind)
    if key not in _cache:
        def dr(d, cx, cy, ss, img):
            f = D.font(80 * ss)
            if kind in ("?", "!"): D.ctext(d, (cx, cy), kind, f, NAVY if kind != "!" else D.ORANGE)
            elif kind == "heart":
                r_ = 26 * ss
                d.ellipse((cx - r_, cy - r_ * 0.8, cx, cy + r_ * 0.2), fill=RED); d.ellipse((cx, cy - r_ * 0.8, cx + r_, cy + r_ * 0.2), fill=RED)
                d.polygon([(cx - r_ * 0.97, cy - r_ * 0.15), (cx + r_ * 0.97, cy - r_ * 0.15), (cx, cy + r_)], fill=RED)
        _cache[key] = D.bubble(120, 110, (0, 0), draw=dr)
    return _cache[key]


def title_sprite():
    key = ("title",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            f = D.font(64 * ss); y_, n_ = "メッセージ", "に乗ったら？"
            wy, wn = d.textlength(y_, font=f), d.textlength(n_, font=f); x0 = W_ / 2 - (wy + wn) / 2
            D.ctext(d, (x0 + wy / 2, H_ / 2), y_, f, (214, 150, 0)); D.ctext(d, (x0 + wy + wn / 2, H_ / 2), n_, f, NAVY)
        _cache[key] = D.card(1000, 230, draw=dr)[0]
    return _cache[key]


def _frame(im):
    """小窓の白いわく（556×318。字のない絵を入れる）"""
    fr = Image.new("RGBA", (556, 318), (255, 255, 255, 255)); fr.paste(im.convert("RGB").resize((544, 306), Image.LANCZOS), (6, 6))
    return fr


def _img(name):
    if name not in _cache: _cache[name] = Image.open(os.path.join(TEX19, name)).convert("RGBA")
    return _cache[name]


def shatter_sprite(t, p):
    """02-05〜02-07：写真が四角いかけらに割れる → さらに細かく → 集まって元どおり"""
    W_, H_ = 544, 306
    im = Image.new("RGB", (W_, H_), (236, 244, 250)); ph = _img("photo_maru.png").convert("RGB").resize((240, 240))
    n = 1
    if t >= p["t_split"]: n = 4
    if t >= p["t_more"]: n = 10
    if t >= p["t_join"]: n = 1
    spread = 0.0
    if p["t_split"] <= t < p["t_join"]: spread = min(1.0, (t - p["t_split"]) / 0.5)
    if t >= p["t_join"] - 0.0 and t < p["t_join"] + 0.6: spread = max(0.0, 1.0 - (t - p["t_join"]) / 0.6); n = 10
    if t >= p["t_join"] + 0.6: n = 1; spread = 0.0
    cs = 240 // n
    import random
    rnd = random.Random(5)
    for i in range(n):
        for j in range(n):
            piece = ph.crop((i * cs, j * cs, (i + 1) * cs, (j + 1) * cs))
            dx = (i - n / 2 + 0.5) * 18 * spread + rnd.uniform(-40, 40) * spread; dy = (j - n / 2 + 0.5) * 12 * spread + rnd.uniform(-25, 25) * spread
            im.paste(piece, (int(W_ / 2 - 120 + i * cs + dx), int(H_ / 2 - 120 + j * cs + dy)))
            if n > 1 and spread > 0.05:
                ImageDraw.Draw(im).rectangle((int(W_ / 2 - 120 + i * cs + dx), int(H_ / 2 - 120 + j * cs + dy), int(W_ / 2 - 120 + (i + 1) * cs + dx) - 1, int(H_ / 2 - 120 + (j + 1) * cs + dy) - 1), outline=(255, 255, 255), width=1)
    return _frame(im)


def charnum_sprite(t, p):
    """04-06・04-07：「あ」→ 12354、「い」→ 12356（カード）"""
    def dr(d, W_, H_, ss, img):
        fb = D.font(96 * ss); fn = D.font(64 * ss)
        rows = [("あ", "12354", t >= p["t_num"])]
        if t >= p["t2"]: rows.append(("い", "12356", True))
        for r, (ch, num, show) in enumerate(rows):
            y = (H_ / 2) if len(rows) == 1 else (H_ * (0.3 + 0.42 * r))
            D.ctext(d, (W_ * 0.24, y), ch, fb, NAVY)
            if show:
                d.line((W_ * 0.38 * 1, y, W_ * 0.52, y), fill=TEAL, width=8 * ss)
                d.polygon([(W_ * 0.52, y - 16 * ss), (W_ * 0.56, y), (W_ * 0.52, y + 16 * ss)], fill=TEAL)
                D.ctext(d, (W_ * 0.76, y), num, fn, (214, 120, 0))
    return D.card(620, 300 if t >= p["t2"] else 200, draw=dr)[0]


def pixel_sprite(t, p):
    """04-08・04-09：スタンプの絵に細かいます目 → 1 つのますに寄って「色 → 数字」"""
    W_, H_ = 544, 306
    im = Image.new("RGB", (W_, H_), (236, 244, 250)); st = _img("stamp_screw.png").convert("RGB").resize((240, 240))
    im.paste(st, (40, 33)); d = ImageDraw.Draw(im)
    for k in range(0, 241, 20):
        d.line((40 + k, 33, 40 + k, 273), fill=(120, 130, 150), width=1); d.line((40, 33 + k, 280, 33 + k), fill=(120, 130, 150), width=1)
    if t >= p["t_zoom"]:
        cx, cy = 40 + 120, 33 + 100
        col = st.getpixel((125, 105))
        d.rectangle((cx - 10, cy - 10, cx + 10, cy + 10), outline=RED, width=3)
        d.line((cx + 10, cy, 330, 150), fill=RED, width=3)
        d.rectangle((330, 100, 430, 200), fill=col, outline=NAVY, width=3)
    fr = _frame(im)
    if t >= p["t_zoom"]:
        spr, off = tag_sprite("色 → 数字", 44, YEL); fr.alpha_composite(spr, (fr.width - spr.width - 16, 24))
    return fr


def conv_sprite(t, p):
    """04-11：数字の粒の列 → 電波の輪／光の筋（小さな図）"""
    def dr(d, W_, H_, ss, img):
        y = H_ / 2
        for k in range(8): d.ellipse((30 * ss + k * 26 * ss, y - 9 * ss, 48 * ss + k * 26 * ss, y + 9 * ss), fill=TEAL if k % 2 else (40, 110, 120))
        d.polygon([(255 * ss, y - 14 * ss), (285 * ss, y), (255 * ss, y + 14 * ss)], fill=NAVY)
        if t >= p["t_w"]:
            for r in (20, 36, 52): d.arc((340 * ss - r * ss, y - r * ss, 340 * ss + r * ss, y + r * ss), -50, 50, fill=(90, 180, 230), width=6 * ss)
        if t >= p["t_l"]:
            d.line((430 * ss, y - 26 * ss, 560 * ss, y - 26 * ss), fill=(250, 200, 60), width=8 * ss)
            d.line((430 * ss, y - 26 * ss, 456 * ss, y - 34 * ss), fill=(250, 200, 60), width=8 * ss)
    return D.card(620, 140, draw=dr)[0]


def envelope_sprite(t, p):
    """06-03〜06-08：封筒の表（住所の所は線だけ）・うら・もどる矢印。字なし"""
    W_, H_ = 544, 306
    im = Image.new("RGB", (W_, H_), (236, 244, 250)); d = ImageDraw.Draw(im)
    d.rectangle((92, 50, 452, 256), fill=(255, 250, 236), outline=(200, 180, 140), width=4)
    if p["side"] == "front":
        for k in range(3): d.rectangle((150, 110 + k * 34, 390 - k * 50, 124 + k * 34), fill=(120, 130, 150))
        d.rectangle((396, 64, 436, 112), fill=(230, 120, 120))      # 切手
        if t >= p["t_x"]:
            d.rounded_rectangle((230, 92, 300, 210), radius=10, fill=(40, 44, 52)); d.rectangle((238, 104, 292, 196), fill=(150, 196, 230))
            d.line((210, 80, 320, 222), fill=RED, width=12); d.line((320, 80, 210, 222), fill=RED, width=12)
    else:
        d.polygon([(92, 50), (272, 150), (452, 50)], outline=(200, 180, 140), fill=(250, 242, 222))
        for k in range(2): d.rectangle((300, 190 + k * 26, 430 - k * 40, 202 + k * 26), fill=(120, 130, 150))
        if t >= p["t_ret"]:
            u = min(1.0, (t - p["t_ret"]) / 0.8)
            d.line((470, 150, 470 - 60 * u, 150), fill=TEAL, width=10)
            d.polygon([(470 - 60 * u - 22, 150), (470 - 60 * u, 136), (470 - 60 * u, 164)], fill=TEAL)
    return _frame(im)


def bldg_sprite():
    key = ("bldg",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            x0, y0 = W_ / 2 - 30 * ss, H_ / 2 - 34 * ss
            d.rectangle((x0, y0, x0 + 60 * ss, y0 + 68 * ss), fill=(140, 150, 170))
            for i in range(3):
                for j in range(4): d.rectangle((x0 + 8 * ss + i * 17 * ss, y0 + 8 * ss + j * 15 * ss, x0 + 18 * ss + i * 17 * ss, y0 + 16 * ss + j * 15 * ss), fill=(250, 240, 200))
        _cache[key] = D.card(110, 96, draw=dr)[0]
    return _cache[key]


def genkou_sprite():
    """07-03：原稿用紙 1 枚と、その 2 割ほど（ます目だけ）"""
    W_, H_ = 544, 306
    im = Image.new("RGB", (W_, H_), (236, 244, 250)); d = ImageDraw.Draw(im)
    def sheet(x0, cols):
        d.rectangle((x0, 30, x0 + cols * 12 + 8, 276), fill=WHITE, outline=(200, 120, 110), width=3)
        for c in range(cols):
            for r in range(20): d.rectangle((x0 + 4 + c * 12, 36 + r * 12, x0 + 14 + c * 12, 46 + r * 12), outline=(220, 150, 140), width=1)
    sheet(70, 20); sheet(340, 4)
    return _frame(im)


def map_sprite():
    """08-07：上から見た町の小さな地図。まるロボの家とアンテナを、短い線で"""
    W_, H_ = 544, 306
    im = Image.new("RGB", (W_, H_), (222, 232, 214)); d = ImageDraw.Draw(im)
    for k in range(0, W_, 68): d.line((k, 0, k, H_), fill=(250, 250, 250), width=6)
    for k in range(0, H_, 68): d.line((0, k, W_, k), fill=(250, 250, 250), width=6)
    hx, hy, ax, ay = 150, 200, 380, 110
    d.line((hx, hy, ax, ay), fill=TEAL, width=8)
    d.polygon([(hx - 22, hy), (hx, hy - 22), (hx + 22, hy)], fill=(184, 87, 74)); d.rectangle((hx - 16, hy, hx + 16, hy + 22), fill=(242, 217, 181))
    d.line((ax, ay + 26, ax, ay - 26), fill=(120, 128, 140), width=6); d.rectangle((ax - 14, ay - 30, ax + 14, ay - 10), fill=(220, 224, 230))
    fr = _frame(im)
    spr, off = tag_sprite("数百 m〜数 km", 44, YEL); fr.alpha_composite(spr, (int(fr.width / 2 - spr.width / 2), 196))
    return fr


def draw(t, base, where, frame_of=None, fontdir=None):
    global EVENTS
    if fontdir and not D.FDIR[0]: D.FDIR[0] = fontdir
    if EVENTS is None: EVENTS = ev_list()
    for t0, t1, kind, p in EVENTS:
        if not (t0 <= t < t1): continue
        k, a = _pop(t, t0, t1)
        if kind == "tag":
            if "pos" in p: cx, cy = p["pos"]
            else:
                q = where(p["obj"], t)
                if q is None or not (-20 <= q[0] <= 1300 and -20 <= q[1] <= 740): continue
                cx, cy = q[0] + p.get("dx", 0), min(max(70, q[1] + p.get("dy", -120)), SUB_TOP - 60)
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), p.get("fg"))
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            _paste(base, spr, cx + (off[0] + spr.width / 2), cy + (off[1] + spr.height / 2), k, a)
        elif kind == "bubble":
            q = p["pos"] if "pos" in p else where(p["obj"], t)
            if q is None or not (-60 <= q[0] <= 1340): continue
            spr, off = bubble_sprite(p["icon"])
            cx = min(max(q[0], spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(q[1] - 40 - spr.height / 2, spr.height / 2 + 10), SUB_TOP - spr.height / 2)
            _paste(base, spr, cx, cy, k, a)
        elif kind == "title":
            base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(110 * a))))
            _paste(base, title_sprite(), 640, 290, k, a)
        elif kind == "slow":       # ゆっくりの世界に入る：画面が少し青くなって、もどる
            u = (t - t0) / max(1e-6, t1 - t0); al = int(70 * math.sin(math.pi * min(1.0, u)))
            base.alpha_composite(Image.new("RGBA", base.size, (60, 110, 200, al)))
        elif kind == "clock":
            if any(a_ <= t < b_ for a_, b_, k_, _ in EVENTS if k_ == "clockbig"): continue
            _paste(base, clock_sprite(clock_val(t)), 1100, 58, 1.0, 1.0)
        elif kind == "clockbig":
            _paste(base, clock_sprite(clock_val(t), big=True), 1040, 70, 1.0, 1.0)
        elif kind == "shatter":
            _paste(base, shatter_sprite(t, p), 30 + 278, 25 + 159, k, a)
        elif kind == "charnum":
            _paste(base, charnum_sprite(t, p), 640, 210, k, a)
        elif kind == "pixel":
            _paste(base, pixel_sprite(t, p), 30 + 278, 25 + 159, k, a)
        elif kind == "conv":
            _paste(base, conv_sprite(t, p), 640, 120, k, a)
        elif kind == "envelope":
            _paste(base, envelope_sprite(t, p), 30 + 278, 25 + 159, k, a)
        elif kind == "bldg":
            _paste(base, bldg_sprite(), p["pos"][0], p["pos"][1], k, a)
        elif kind == "genkou":
            _paste(base, genkou_sprite(), 30 + 278, 25 + 159, k, a)
        elif kind == "map":
            _paste(base, map_sprite(), 30 + 278, 25 + 159, k, a)
    return base
