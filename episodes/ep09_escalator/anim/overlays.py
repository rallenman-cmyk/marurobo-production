# 9本目（エスカレーター）：3D の上に重ねる 2D（札・吹き出し・題名・小窓・輪・矢印・長さの線・1円玉・想像の色）
#   一覧 EVENTS：(始め, 終わり, 種類, 中身)。時刻は声の時刻（timing.py）。札の答えは、その言葉を言う瞬間に出す（SKILL §3）
#   見た目は 4本目の design.py（2 倍で描いて縮める・やわらかい影・ぽんと弾んで出る 0.3 秒）。7本目の overlays.py を写して、この回の札にした
#   字の大きさ：数字は 56〜60、ほかは 48（1280×720 の座標。スマホで読める大きさ）。字幕の帯（y 560 より下）に置かない
#   3D の中に字を書かないので、字は全部ここ。絵コンテ表：../絵コンテ_v1.md
#   色：前の車輪・前のレール＝オレンジ、後ろの車輪・後ろのレール＝紫（3D と同じ）。くし＝黄色
import os, sys, math, json
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep04_robot", "look"))
import design as D
import timing as T
s, e, w = T.s, T.e, T.w
YEL = (255, 201, 40); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48)
ORANGE = (255, 138, 31); PURPLE = (138, 77, 255); TEAL = D.TEAL
SUB_TOP = 560
_cache = {}
EVENTS = None


def ev_list():
    """絵コンテ_v1.md と見比べて作る"""
    E = []
    add = lambda *a: E.append(a)
    # 冒頭
    add(w("02-03", "見てください"), e("02-03") + 0.2, "ring", dict(obj="step_edge", r=40))   # まるロボの段と、となりの段の段差（v4 のコメント 0:27）
    add(w("04-06", "首") - 0.3, e("04-06") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    # 題の札：「エスカレーター。」のすぐ後に急に出さず、少し間をおいてから出し、問いの文（05-02）を読む間ずっと見せる（v1 のコメント 1:30）
    add(s("05-02") - 0.05, e("05-02") + 0.4, "title", {})   # v2 のコメント 1:31「段は〜のセリフの時にオープニングも映して。表示で音声ないの気になる」：声が出ている間だけ出す（前の文との間も 2.8 → 1.0 秒に詰めた）
    add(s("05-03"), e("05-03") + 0.2, "pip_clip", dict(clip="A04c", src_t=w("04-03", "ころん") - 1.0))
    # 1章
    add(w("06-03", "消えた段") - 0.1, e("06-03") + 0.4, "pile", dict(pos=(640, 300)))   # 文の頭から（たまっていく絵を声と一緒に見せる）
    add(s("06-06"), e("06-06") + 0.2, "ring", dict(obj="comb_hi", r=60))
    add(s("06-06"), e("06-06") + 0.2, "ring", dict(obj="comb_lo", r=60))
    add(w("07-02", "このしるし"), e("07-02") + 0.3, "sticker", dict(pos=(290, 170)))   # 左上へ（まん中だと、まるロボの頭に重なった。9本目 v2 の点検）
    add(s("07-04"), e("07-04") + 0.2, "ring", dict(obj="sticker", r=40))
    add(s("08-03") + 0.9, e("08-03"), "bubble", dict(obj="maru_top", icon="!"))   # v3 の点検：この文は頭に 0.9 秒の息があり、字数の見積もり（w）では「！」が声より 0.8 秒早かった → 本当の声の頭（162.87 秒）に
    add(w("08-05", "輪"), e("08-06") + 0.3, "dotloop", dict(a="loop_lo", b="loop_hi"))
    add(w("08-06", "床の下"), e("08-06") + 0.3, "bubble", dict(obj="loop_mid", icon="?"))
    add(w("08-07", "なぜ") - 0.3, e("08-07") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    # 2章
    add(w("11-09", "モーター"), e("11-10") + 0.4, "flow", dict(items=[("モーター", w("11-09", "モーター")), ("歯車", w("11-09", "歯車")),
                                                                    ("鎖", w("11-09", "鎖")), ("段", w("11-10", "段"))]))
    add(w("12-00", "どうする") - 0.2, e("12-00") + 0.3, "bubble", dict(obj="gear", icon="?"))
    add(w("12-03", "上っていく"), e("12-03") + 0.3, "tag", dict(text="上っていく段", obj="top_mid", dy=-60, size=44))
    add(w("12-03", "真下"), e("12-03") + 0.3, "tag", dict(text="戻る段（さかさま）", obj="ret_mid", dy=60, size=44))
    add(e("13-05") - 1.2, e("13-05") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("14-01"), e("14-02"), "ring", dict(obj="sticker", r=38))
    add(w("14-03", "まだ") - 0.2, e("14-03") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    # 3章
    add(w("15-03", "前に"), e("15-03") + 0.3, "ring", dict(obj="fw0", r=34, col=ORANGE))
    add(w("15-03", "後ろに"), e("15-03") + 0.3, "ring", dict(obj="rw0", r=34, col=PURPLE))
    add(w("15-04", "どうして") - 0.2, e("15-04") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(w("16-02", "前のレール"), e("16-04") + 0.3, "tag", dict(text="前のレール", obj="railf_pt", dy=-70, bg=ORANGE, fg=WHITE))
    add(w("16-03", "後ろのレール"), e("16-04") + 0.3, "tag", dict(text="後ろのレール", obj="railr_pt", dy=-140, bg=PURPLE, fg=WHITE))
    add(w("17-10", "なぜ") - 0.3, e("17-10") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(w("17-11", "支えて") - 0.2, e("17-11") + 0.3, "arrow2", dict(a="rear_rail_lo", b="rear_rail_pt", dy=0, col=PURPLE))
    add(w("17-12", "離れて") - 0.3, e("17-12") + 0.3, "dbl", dict(a="railf_pt", b="railr_pt"))
    add(w("18-02", "近づいて") - 0.2, e("18-02") + 0.3, "dbl", dict(a="railf_end", b="railr_end"))
    add(w("18-03", "一直線") - 0.4, e("18-04") + 0.3, "seg", dict(a="fw_end", b="rw_end"))
    # 4章
    add(w("22-04", "ずれて") - 0.3, e("22-04") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("24-01"), e("24-03") + 0.1, "tint", {})
    add(w("24-04", "少しだけ"), e("24-05") + 0.3, "hrarrows", {})
    add(s("24-06"), e("24-06"), "pip_none", {})
    # 5章
    add(s("25-02") + 0.5, e("25-02") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    # 26-03（段の溝の絵）ではくしが画面の外なので出さない（外の札が画面の端に残った）
    add(w("26-02", "くし"), e("26-02") + 0.3, "tag", dict(text="くし", obj="comb_hi", dy=-110, bg=YEL))
    add(s("26-04"), e("26-04") + 0.3, "tag", dict(text="くし", obj="comb_hi", dy=-110, bg=YEL))
    add(s("26-05") + 0.3, e("26-05") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("26-09"), e("26-09") + 0.2, "pip_clip", dict(clip="A04c", src_t=w("04-03", "ころん") - 1.0))
    add(s("26-10") + 0.3, e("26-10") + 0.3, "ring", dict(obj="pebble", r=36))
    add(w("27-03", "5ミリ"), e("27-05") + 0.3, "tag", dict(text="5ミリ以下", pos=(640, 110), size=60, bg=YEL))
    add(w("27-04", "1円玉"), e("27-04") + 0.5, "coins", dict(pos=(1010, 330)))
    # 6章
    add(w("28-03", "見張り"), e("28-03") + 0.3, "tag", dict(text="見張り＝はさまったら止める", pos=(640, 100), size=46))
    add(s("29-01") + 0.3, e("29-01") + 0.3, "ring", dict(obj="inlet", r=48))
    add(w("29-02", "なると") - 0.3, e("29-02") + 0.3, "ring", dict(obj="ball", r=40))   # ボールが入口の手前ではさまる所（v2 のコメント 12:51）
    add(s("31-01") + 0.3, e("31-01") + 0.3, "ring", dict(obj="comb_hi", r=52))   # 上の降り口のくし（v2 のコメント 13:30）
    # 見張りの試しの小さな物（リボン・小石）を白い輪で示す（9本目 v2 の点検：小さくて見落とす）
    add(w("30-02", "リボン"), e("30-03") + 0.3, "ring", dict(obj="ribbon", r=34))
    add(w("31-02", "小石"), e("31-03") + 0.3, "ring", dict(obj="pebble", r=30))
    add(s("32-04"), e("32-04") + 0.2, "pip_clip", dict(clip="I24", src_t=w("24-02", "ころん") - 1.4))
    add(w("32-05", "2024年"), e("32-05") + 0.3, "tag", dict(text="2024年から", pos=(640, 110), size=58, bg=YEL))
    add(s("34-02") + 0.2, e("34-02") + 0.3, "ring", dict(obj="button", r=40, col=RED))
    add(w("35-01", "安全") - 0.3, e("35-01") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("35-02"), e("35-03") + 0.1, "tint", {})
    add(w("36-03", "1分間"), e("36-03") + 0.3, "tag", dict(text="1分間に30メートル", pos=(640, 105), size=56, bg=YEL))
    # 押した時の段（白い線）が、すうっと進んで止まった所を、段について動く青緑の線で見せる。36-05「この間に入っていました」が絵で分かるように（9本目 v2 の点検：止まった段の位置が絵になかった）
    add(w("34-04", "すうっと"), e("34-04") + 0.3, "vline", dict(obj="stop_now", text="", col=TEAL))   # 34-04 の間だけ：段といっしょに動いて止まる線（すうっと進むのが見えるように）
    # 床の下の場面（10-01〜13-02）：いま、どこを見ているかの小さな地図（v2 のコメント 3:55・4:03）
    #   v4 のコメント 5:10「今ここの赤い丸は映像で映してる場所にして」：赤い点は手で決めた割合でなく、映している場所（カメラのまん中の先・まるロボを追う場面はまるロボ）から
    #   locator_keys.py が決めた locator_keys.json で動かす。13-03（乗り口のすき間から外へ）まで出し、まるロボが床の上に出る 13-04 の前で消す
    _lk = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locator_keys.json")
    add(s("10-01"), s("13-04") - 0.1, "locator", dict(keys=[tuple(x) for x in json.load(open(_lk))]))
    # 10-02「ここは、冒頭でまるロボが見ていたすき間の、ちょうど裏側です」：冒頭の上から見たすき間を、左上の小窓で（v2 のコメント 3:42「冒頭のシーンを切り抜きみたいな感じで映して」）
    add(s("10-02"), e("10-02") + 0.3, "pip_clip", dict(clip="A03b", src_t=s("03-03") + 0.3))
    add(w("23-01", "手すり") - 0.2, e("23-04") + 0.4, "hrloop", dict(tA=w("23-02", "ゴム"), tB=w("23-03", "車"), tC=w("23-04", "すべって")))   # 手すりのしくみの図（v2 の点検：3D に手すりの輪と車が映っていなかった）
    add(w("36-04", "10センチ") - 0.2, e("36-05") + 0.5, "ruler", dict(pos=(640, 165), t_meas=w("36-05", "測って")))   # ものさしの図（3D の線は角度で読めなかった）
    return E


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


def icon_draw(kind):
    def dr(d, cx, cy, ss, img):
        f = D.font(80 * ss)
        if kind in ("?", "!"):
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
        # 2 行（v1 のコメント「2行で表現して」）
        spr, off = D.card(1000, 260, draw=lambda d, W_, H_, ss, img: [D.ctext(d, (W_ / 2, H_ / 2 - 52 * ss), "エスカレーターの段は、", D.font(60 * ss), NAVY),
                                                                      D.ctext(d, (W_ / 2, H_ / 2 + 52 * ss), "どこへ消える？", D.font(78 * ss), D.TEAL_D)])
        _cache[key] = spr
    return _cache[key]


def _layer():
    return Image.new("RGBA", (1280 * 2, 720 * 2), (0, 0, 0, 0))


def _down(im):
    return im.resize((1280, 720), Image.LANCZOS)


def ring_img(q, r, col, a):
    im = _layer(); d = ImageDraw.Draw(im); S2 = 2
    d.ellipse([(q[0] - r) * S2, (q[1] - r) * S2, (q[0] + r) * S2, (q[1] + r) * S2], outline=col + (int(255 * a),), width=7 * S2)
    return _down(im)


def arrow_img(p0, p1, col, both=False, a=1.0):
    S2 = 2; im = _layer(); d = ImageDraw.Draw(im)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); ca, sa = math.cos(ang), math.sin(ang)
    L_, Hw, lw = 30, 18, 9
    fill = col + (int(255 * a),)

    def head(tip, ca_, sa_):
        bs = ((tip[0] - L_ * ca_) * S2, (tip[1] - L_ * sa_) * S2)
        d.polygon([(tip[0] * S2, tip[1] * S2), (bs[0] - Hw * sa_ * S2, bs[1] + Hw * ca_ * S2), (bs[0] + Hw * sa_ * S2, bs[1] - Hw * ca_ * S2)], fill=fill)
    a0 = (p0[0] + (L_ * ca if both else 0), p0[1] + (L_ * sa if both else 0)); a1 = (p1[0] - L_ * ca, p1[1] - L_ * sa)
    d.line([(a0[0] * S2, a0[1] * S2), (a1[0] * S2, a1[1] * S2)], fill=fill, width=lw * S2)
    head(p1, ca, sa)
    if both: head(p0, -ca, -sa)
    return _down(im)


def sticker_sprite():
    key = ("sticker",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            cx, cy, r = W_ / 2, H_ / 2, 70 * ss
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 250, 246), outline=(200, 205, 210), width=3 * ss)
            d.ellipse([cx - 30 * ss, cy - 30 * ss, cx + 30 * ss, cy + 30 * ss], fill=(31, 184, 172))
            d.ellipse([cx - 12 * ss, cy - 12 * ss, cx + 12 * ss, cy + 12 * ss], fill=(16, 60, 70))
        _cache[key] = D.card(200, 200, draw=dr)[0]
    return _cache[key]


def coins_sprite():
    key = ("coins",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            for i in range(3):
                y = H_ / 2 + (30 - 22 * i) * ss
                d.ellipse([W_ / 2 - 80 * ss, y - 22 * ss, W_ / 2 + 80 * ss, y + 22 * ss], fill=(214, 218, 222), outline=(150, 156, 162), width=3 * ss)
            D.ctext(d, (W_ / 2, H_ / 2 + 84 * ss), "1円玉 3枚", D.font(40 * ss), NAVY)
        _cache[key] = D.card(260, 230, draw=dr)[0]
    return _cache[key]


def pile_sprite(t=None, t0=None):
    """06-03 の想像：横から見たエスカレーター。上の降り口で消えた段が、床の下に 1 枚ずつ落ちてたまっていく（v1 のコメント「この絵がわかりにくい」で描き替え）"""
    k = 1.0 if t is None else max(0.0, min(1.0, (t - t0) / 3.2))

    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: (x * ss, y * ss)
        GR, ST, NV = (150, 156, 166), (96, 104, 118), NAVY
        # 床（下の階・上の階）と坂
        d.line([S_(30, 330), S_(250, 330)], fill=GR, width=8 * ss)
        d.line([S_(250, 330), S_(560, 140)], fill=GR, width=8 * ss)
        d.line([S_(560, 140), S_(870, 140)], fill=GR, width=8 * ss)
        # 坂の段（のこぎりの形）
        for q in range(9):
            x0, y0 = 262 + q * 33, 323 - q * 20.2
            d.line([S_(x0, y0), S_(x0, y0 - 20), S_(x0 + 33, y0 - 20)], fill=ST, width=5 * ss)
        # 床の下（上の階の下）：点線の箱
        bx0, by0, bx1, by1 = 590, 160, 850, 400
        for xx in range(bx0, bx1, 22):
            d.line([S_(xx, by1), S_(xx + 12, by1)], fill=GR, width=4 * ss)
        for yy in range(by0, by1, 22):
            d.line([S_(bx0, yy), S_(bx0, yy + 12)], fill=GR, width=4 * ss)
            d.line([S_(bx1, yy), S_(bx1, yy + 12)], fill=GR, width=4 * ss)
        D.ctext(d, S_(520, 380), "床の下", D.font(32 * ss), GR)
        # たまっていく段（1 枚ずつ落ちる）
        u = k * 7.0; n = min(7, 1 + int(u))
        for i_ in range(n):
            fall = 1.0 if (i_ < n - 1 or k >= 1.0) else min(1.0, (u - (n - 1)) * 1.6 + 0.2)
            yb = by1 - 8 - i_ * 26; ytop = 150 + (yb - 150) * fall
            x0 = 640 + (i_ % 2) * 18
            d.rounded_rectangle([S_(x0, ytop - 22), S_(x0 + 150, ytop)], radius=5 * ss, fill=ST)
            for g in range(6):
                d.line([S_(x0 + 14 + g * 23, ytop - 18), S_(x0 + 14 + g * 23, ytop - 4)], fill=(150, 158, 172), width=3 * ss)
        # 消える所から下へ落ちる矢印
        d.line([S_(575, 128), S_(612, 128), S_(612, 210)], fill=(214, 72, 64), width=7 * ss)
        d.polygon([S_(598, 206), S_(626, 206), S_(612, 232)], fill=(214, 72, 64))
        D.ctext(d, S_(450, 40), "消えた段が、床の下にたまる？", D.font(46 * ss), NV)
    return D.card(900, 430, draw=dr)[0]


def hrloop_sprite(t, tA, tB, tC):
    """23-01〜23-04：手すりのしくみの図（9本目 v2 の点検：3D は段の断面のままで、「手すりはゴムの輪」「車ではさんで」の物が画面になかった）。
    手すりの輪（上を進み、端で回って床の下を戻る）。tA「ゴム」で輪が青緑に光る。tB「車」で、戻る所をはさむ 2 つの車がオレンジに光る。
    tC「すべって」で、車の所に「少しすべる」の印。手すりの白い印が輪にそって動き、車が回る"""
    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: (x * ss, y * ss)
        GR, NV = (70, 76, 86), NAVY
        D.ctext(d, S_(500, 40), "手すりのしくみ", D.font(40 * ss), NV)
        top = [(110, 270), (330, 270), (690, 115), (890, 115)]
        ret = [(x, y + 96) for x, y in reversed(top)]
        rr = 48
        arcR = [(890 + rr * math.sin(a), 115 + rr - rr * math.cos(a)) for a in [i * math.pi / 18 for i in range(19)]]
        arcL = [(110 - rr * math.sin(a), 366 - rr + rr * math.cos(a)) for a in [i * math.pi / 18 for i in range(19)]]
        loop = top + arcR + ret + arcL
        # 段（うすい灰色の坂。手すりがその上を進むのが分かるように）
        d.line([S_(x, y + 36) for x, y in top], fill=(205, 209, 215), width=26 * ss)
        D.ctext(d, S_(800, 175), "段", D.font(32 * ss), (150, 156, 166))
        on = t >= tA
        col = D.TEAL if on else GR
        if on: d.line([S_(x, y) for x, y in loop], fill=(170, 225, 215), width=30 * ss, joint="curve")
        d.line([S_(x, y) for x, y in loop], fill=col, width=16 * ss, joint="curve")
        # 白い印：輪にそって進む（上は右へ、床の下は左へ）
        acc = [0.0]
        for (a, b), (c, e_) in zip(loop, loop[1:]): acc.append(acc[-1] + math.hypot(c - a, e_ - b))
        L = acc[-1]
        for j in range(int(L // 70)):
            u = (j * 70 + 60.0 * t) % L
            i = max(0, min(len(acc) - 2, next(k for k in range(len(acc) - 1) if acc[k + 1] >= u)))
            (a, b), (c, e_) = loop[i], loop[i + 1]
            f = (u - acc[i]) / max(1e-6, acc[i + 1] - acc[i]); x, y = a + (c - a) * f, b + (e_ - b) * f
            d.ellipse([S_(x - 4, y - 4), S_(x + 4, y + 4)], fill=(235, 240, 244))
        # はさむ車（戻る坂のまん中）
        (xa, ya), (xb, yb) = ret[1], ret[2]
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        ln = math.hypot(xb - xa, yb - ya); nx, ny = -(yb - ya) / ln, (xb - xa) / ln
        onB = t >= tB
        for sg in (1, -1):
            cx, cy = mx + sg * nx * 36, my + sg * ny * 36
            fc = ORANGE if onB else (150, 156, 166)
            if onB: d.ellipse([S_(cx - 34, cy - 34), S_(cx + 34, cy + 34)], fill=(255, 214, 170))
            d.ellipse([S_(cx - 27, cy - 27), S_(cx + 27, cy + 27)], fill=fc, outline=NV, width=3 * ss)
            ang = sg * t * 3.0
            for q in range(3):
                a_ = ang + q * 2 * math.pi / 3
                d.line([S_(cx, cy), S_(cx + 22 * math.cos(a_), cy + 22 * math.sin(a_))], fill=NV, width=4 * ss)
        if on: D.ctext(d, S_(255, 215), "手すり（ゴムの輪）", D.font(34 * ss), D.TEAL_D)
        cl = (mx - nx * 36, my - ny * 36)          # 下の車
        if onB:
            d.line([S_(cl[0] + 30, cl[1] + 8), S_(700, 318)], fill=(214, 104, 0), width=3 * ss)
            D.ctext(d, S_(800, 318), "車ではさむ", D.font(34 * ss), (214, 104, 0))
        if t >= tC:
            ux, uy = (xb - xa) / ln, (yb - ya) / ln    # 戻る坂の向き
            bx, by = cl[0] + nx * -40, cl[1] + ny * -40
            d.line([S_(bx - ux * 40, by - uy * 40), S_(bx + ux * 30, by + uy * 30)], fill=RED, width=6 * ss)
            d.polygon([S_(bx + ux * 46, by + uy * 46), S_(bx + ux * 24 + nx * 12, by + uy * 24 + ny * 12), S_(bx + ux * 24 - nx * 12, by + uy * 24 - ny * 12)], fill=RED)
            d.line([S_(bx + 10, by + 10), S_(700, 372)], fill=RED, width=3 * ss)
            D.ctext(d, S_(800, 372), "少しすべる", D.font(34 * ss), RED)
    return D.card(1000, 420, draw=dr)[0]


LOC_PATH = [(292, 12), (318, 14), (330, 28), (316, 42), (282, 42), (104, 140), (72, 140), (60, 126), (70, 112), (96, 112)]   # 床の下の道（上の床の下 → 歯車 → 坂の下を戻る → 下の端 → 下の床の下）


def _loc_pt(u):
    acc = [0.0]
    for (a, b), (c, d) in zip(LOC_PATH, LOC_PATH[1:]): acc.append(acc[-1] + math.hypot(c - a, d - b))
    L = acc[-1] * max(0.0, min(1.0, u))
    for i in range(len(LOC_PATH) - 1):
        if acc[i + 1] >= L:
            f = (L - acc[i]) / max(1e-6, acc[i + 1] - acc[i]); (a, b), (c, d) = LOC_PATH[i], LOC_PATH[i + 1]
            return a + (c - a) * f, b + (d - b) * f
    return LOC_PATH[-1]


def locator_sprite(u, blink=1.0):
    """10〜13 章（床の下）：いま、エスカレーターのどこを見ているかの小さな地図（v2 のコメント 3:55「どの部分を見ているか分かりにくい」）。
    横から見たエスカレーター（下の床・坂・上の床）と、床の下の道（点線）に、赤い点と「いまここ」"""
    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: ((x + 10) * ss, (y + 50) * ss)
        GR, ST = (150, 156, 166), (96, 104, 118)
        d.line([S_(0, 100), S_(90, 100)], fill=GR, width=6 * ss)            # 下の床
        d.line([S_(90, 100), S_(270, 0)], fill=ST, width=10 * ss)           # 坂（段）
        d.line([S_(270, 0), S_(340, 0)], fill=GR, width=6 * ss)             # 上の床
        for (a, b), (c, e_) in zip(LOC_PATH, LOC_PATH[1:]):                  # 床の下の道（点線）
            L = math.hypot(c - a, e_ - b); n = max(1, int(L // 12))
            for q in range(n):
                f0, f1 = q / n, (q + 0.55) / n
                d.line([S_(a + (c - a) * f0, b + (e_ - b) * f0), S_(a + (c - a) * f1, b + (e_ - b) * f1)], fill=GR, width=4 * ss)
        x, y = _loc_pt(u)
        d.ellipse([S_(x - 15, y - 15), S_(x + 15, y + 15)], fill=(255, 205, 200))
        d.ellipse([S_(x - 9, y - 9), S_(x + 9, y + 9)], fill=RED)
        D.ctext(d, S_(110, -22), "いまここ", D.font(44 * ss), RED)
    return D.card(380, 230, draw=dr)[0]


def ruler_sprite(t=None, t_meas=None):
    """36-04〜36-06：止まるまでの長さを、まっすぐなものさしの図で（9本目 v2 ユーザー「テロップ重なるし、どこが何センチかわかんない」。
    3D の段の横に線を引くと、見る角度でずれて読めなかった）。10〜60 センチの間をぬり、36-05「測って」で矢印が 0 から約 50 センチまでのびる"""
    k = 0.0 if (t is None or t_meas is None) else max(0.0, min(1.0, (t - t_meas) / 1.6))

    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: (x * ss, y * ss)
        x0, cm = 175, 10.0                      # 0 センチの位置と、1 センチの長さ（65 センチまで）
        X = lambda c: x0 + c * cm
        GR, NV, YL, TL = (150, 156, 166), NAVY, YEL, D.TEAL_D
        D.ctext(d, S_(450, 36), "ボタンを押してから、止まるまで", D.font(40 * ss), NV)
        ya, yb = 132, 205                       # 矢印の高さ・ものさしの線の高さ
        d.rectangle([S_(X(10), yb - 36), S_(X(60), yb)], fill=YL)   # 決まりの間（10〜60 センチ）
        D.ctext(d, S_((X(10) + X(60)) / 2, yb - 18), "この間で止まる", D.font(28 * ss), NV)
        d.line([S_(X(0), yb), S_(X(65), yb)], fill=GR, width=6 * ss)
        for c in range(0, 66, 10):
            d.line([S_(X(c), yb), S_(X(c), yb + (18 if c in (0, 10, 60) else 10))], fill=GR, width=4 * ss)
        D.ctext(d, S_(X(0), yb + 42), "0", D.font(30 * ss), NV)
        D.ctext(d, S_(X(10), yb + 42), "10センチ", D.font(30 * ss), NV)
        D.ctext(d, S_(X(60), yb + 42), "60センチ", D.font(30 * ss), NV)
        D.ctext(d, S_(X(0) - 88, ya), "押した所", D.font(28 * ss), NV)
        d.line([S_(X(0), ya - 22), S_(X(0), yb)], fill=NV, width=4 * ss)
        if k > 0:
            xe = X(49 * k)
            d.line([S_(X(0), ya), S_(xe - 14, ya)], fill=TL, width=10 * ss)
            d.polygon([S_(xe, ya), S_(xe - 24, ya - 15), S_(xe - 24, ya + 15)], fill=TL)
            if k >= 1.0:
                d.line([S_(xe, ya), S_(xe, yb)], fill=TL, width=5 * ss)
                D.ctext(d, S_(xe, ya - 34), "止まった所（約50センチ）", D.font(28 * ss), TL)
    return D.card(900, 290, draw=dr)[0]


def hrarrows_sprite(t, t0):
    def dr(d, W_, H_, ss, img):
        k = min(1.0, (t - t0) / 0.8)
        for i, (lab, L, col) in enumerate((("手すり", 1.08, (40, 46, 54)), ("段", 1.0, D.TEAL_D))):
            y = (70 + 90 * i) * ss; x0 = 190 * ss; x1 = x0 + int(560 * ss * L * k)
            d.line([x0, y, x1 - 20 * ss, y], fill=col, width=12 * ss)
            d.polygon([(x1, y), (x1 - 34 * ss, y - 20 * ss), (x1 - 34 * ss, y + 20 * ss)], fill=col)
            D.ctext(d, (100 * ss, y), lab, D.font(42 * ss), col)
    return D.card(900, 230, draw=dr)[0]


def flow_sprite(t, items):
    shown = [nm for nm, ti in items if t >= ti]
    key = ("flow", tuple(shown))
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            # 字の幅を測って並べ、矢印はどれも同じ長さで字と字の間に（v2 のコメント 4:38「矢印が文字に重なってる」）。全部の字の場所を先に決めるので、出てきても字は動かない
            f_ = D.font(46 * ss); ws = [d.textlength(nm, font=f_) for nm, _ in items]
            gap, arr = 18 * ss, 70 * ss          # v4 のコメント 4:42：右上の「いまここ」の地図と重ならないよう、矢印を短く・札を細くして左へ寄せた
            tot = sum(ws) + (len(items) - 1) * (arr + 2 * gap); x = (W_ - tot) / 2
            for i, (nm, _) in enumerate(items):
                cx = x + ws[i] / 2
                if nm in shown: D.ctext(d, (cx, H_ / 2), nm, f_, NAVY)
                if i + 1 < len(items) and items[i + 1][0] in shown:
                    xa = x + ws[i] + gap; xb = xa + arr
                    d.line([xa, H_ / 2, xb - 16 * ss, H_ / 2], fill=D.TEAL_D, width=8 * ss)
                    d.polygon([(xb, H_ / 2), (xb - 22 * ss, H_ / 2 - 14 * ss), (xb - 22 * ss, H_ / 2 + 14 * ss)], fill=D.TEAL_D)
                x += ws[i] + arr + 2 * gap
        _cache[key] = D.card(760, 120, draw=dr)[0]
    return _cache[key]


def dotloop_img(qa, qb, a):
    """2 つの歯車の中心を結ぶ、輪（かまぼこ形）の点線"""
    im = _layer(); d = ImageDraw.Draw(im); S2 = 2
    dx, dy = qb[0] - qa[0], qb[1] - qa[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy, ux
    r = max(40, 0.12 * L)
    pts = []
    for i in range(41): pts.append((qa[0] + dx * i / 40 + nx * r, qa[1] + dy * i / 40 + ny * r))
    for i in range(21):
        th = math.pi / 2 - math.pi * i / 20; pts.append((qb[0] + (ux * math.cos(th) + nx * math.sin(th)) * r * 1, qb[1] + (uy * math.cos(th) + ny * math.sin(th)) * r))
    for i in range(41): pts.append((qb[0] - dx * i / 40 - nx * r, qb[1] - dy * i / 40 - ny * r))
    for i in range(21):
        th = -math.pi / 2 - math.pi * i / 20; pts.append((qa[0] + (ux * math.cos(th) + nx * math.sin(th)) * r, qa[1] + (uy * math.cos(th) + ny * math.sin(th)) * r))
    for i in range(0, len(pts) - 1, 2):
        d.line([(pts[i][0] * S2, pts[i][1] * S2), (pts[i + 1][0] * S2, pts[i + 1][1] * S2)], fill=(255, 255, 255, int(235 * a)), width=8 * S2)
    return _down(im)


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
                if q is None or not (-20 <= q[0] <= 1300 and -20 <= q[1] <= 740): continue   # 物が画面の外なら出さない（9本目 26-03：端に寄せた札が何もない所を指した）
                cx, cy = q[0] + p.get("dx", 0), min(max(70, q[1] + p.get("dy", -120)), SUB_TOP - 60)
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), p.get("fg"))
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            _paste(base, spr, cx + (off[0] + spr.width / 2), cy + (off[1] + spr.height / 2), k, a)
        elif kind == "bubble":
            q = where(p["obj"], t)
            if q is None or not (-20 <= q[0] <= 1300 and -20 <= q[1] <= 700): continue
            spr, off = bubble_sprite(p["icon"])
            cx = min(max(q[0], spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(q[1] - 40 - spr.height / 2, spr.height / 2 + 10), SUB_TOP - spr.height / 2)
            _paste(base, spr, cx, cy, k, a)
        elif kind == "title":
            base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(120 * a))))
            _paste(base, title_sprite(), 640, 290, k, a)
        elif kind == "ring":
            q = where(p["obj"], t)
            if q is None or not (0 <= q[0] <= 1280 and 0 <= q[1] <= 720): continue
            base.alpha_composite(ring_img((q[0] + p.get("dx", 0), q[1] + p.get("dy", 0)), p.get("r", 40) * k, p.get("col", WHITE), a))
        elif kind == "arrow2":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            base.alpha_composite(arrow_img((qa[0], qa[1] + p["dy"]), (qb[0], qb[1] + p["dy"]), p.get("col", NAVY), a=a))
        elif kind == "dbl":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            if math.hypot(qb[0] - qa[0], qb[1] - qa[1]) < 30: continue
            base.alpha_composite(arrow_img(qa, qb, YEL, both=True, a=a))
        elif kind == "seg":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            im = _layer(); d = ImageDraw.Draw(im)
            d.line([(qa[0] * 2, qa[1] * 2), (qb[0] * 2, qb[1] * 2)], fill=YEL + (int(255 * a),), width=12)
            for q in (qa, qb): d.ellipse([(q[0] - 9) * 2, (q[1] - 9) * 2, (q[0] + 9) * 2, (q[1] + 9) * 2], fill=YEL + (int(255 * a),))
            base.alpha_composite(_down(im))
        elif kind == "vline":
            q = where(p["obj"], t)
            if q is None or not (0 <= q[0] <= 1280): continue
            im = _layer(); d = ImageDraw.Draw(im)
            d.line([(q[0] * 2, (q[1] - 90) * 2), (q[0] * 2, (q[1] + 10) * 2)], fill=p.get("col", WHITE) + (int(255 * a),), width=10)
            base.alpha_composite(_down(im))
            if p.get("text"):
                spr, off = tag_sprite(p["text"], 40, p.get("bg", YEL), fg=p.get("fg"))
                if p.get("right"):   # right：線の右に札（上は 10・60 センチの札、下は字幕と重なる。9本目 v2）
                    _paste(base, spr, q[0] + spr.size[0] // 2 + 24, q[1] - 45, k, a)
                else:
                    _paste(base, spr, q[0], max(60, q[1] - 130), k, a)
        elif kind == "tint":      # 想像の場面：少し青く暗く（本当の試しではないと分かるように）
            base.alpha_composite(Image.new("RGBA", base.size, (40, 60, 120, int(80 * a))))
            spr, off = tag_sprite("もしも…", 44, WHITE)
            _paste(base, spr, 150, 70, 1.0, a)
        elif kind == "locator":
            ks = p["keys"]; u = ks[0][1]
            for (ta, ua), (tb, ub) in zip(ks, ks[1:]):
                if ta <= t <= tb: u = ua + (ub - ua) * (t - ta) / max(1e-6, tb - ta); break
                if t > tb: u = ub
            _paste(base, locator_sprite(round(u, 3)), 1080, 122, k, a)
        elif kind == "hrloop":
            _paste(base, hrloop_sprite(t, p["tA"], p["tB"], p["tC"]), 640, 300, k, a)
        elif kind == "ruler":
            _paste(base, ruler_sprite(t, p["t_meas"]), p["pos"][0], p["pos"][1], k, a)
        elif kind == "pile":
            _paste(base, pile_sprite(t, t0), p["pos"][0], p["pos"][1], k, a)
        elif kind == "sticker":
            _paste(base, sticker_sprite(), p["pos"][0], p["pos"][1], k, a)
        elif kind == "coins":
            _paste(base, coins_sprite(), p["pos"][0], p["pos"][1], k, a)
        elif kind == "hrarrows":
            _paste(base, hrarrows_sprite(t, t0), 640, 150, k, a)
        elif kind == "flow":
            _paste(base, flow_sprite(t, p["items"]), 410, 95, k, a)       # 右上の「いまここ」の地図（x 890〜）と重ならない所
        elif kind == "dotloop":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            base.alpha_composite(dotloop_img(qa, qb, a))
        elif kind == "pip_clip" and frame_of:
            im = frame_of(p["clip"], p["src_t"] + (0 if p.get("hold") else (t - t0)))
            if im is None: continue
            im = im.convert("RGB").resize((400, 225), Image.LANCZOS)
            fr = Image.new("RGBA", (412, 237), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            _paste(base, fr, 30 + 206, 25 + 118, k, a)
    return base
