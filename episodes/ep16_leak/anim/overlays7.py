# 16本目 7章（S30〜S32）の 2D：夕方のメールの札（2 段）・朝のメールとの見比べ・「まるロボ様」と名簿のつながり・
#   名札がメールに変わる動き・名札の旅の小窓・会社のふり・名前だけ光るメール・電話と郵便
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜6章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   語り手の「？」は 1 文に 1 つ・物は急に出さない・図は場面のつなぎのあとに出す）。絵コンテ表：../絵コンテ_v1.md の「7章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import icons16 as IC
from overlays2 import wv, _canvas, _done, _tag, S2, NAVY, RED
s, e = T.s, T.e
TEAL = (47, 217, 200); TEAL_L = (210, 248, 243); GREYB = (200, 206, 216); BLUE = (68, 132, 222); YEL = (255, 200, 30)


def _ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def _mail(d, x0, y0, W_, t, p, ss=S2, dim=False, name_glow=0.0, part2=1.0, morning=False, short=False):
    """メールの札（白い角丸の中）：左上にお店の印、その横に灰色の帯（お店の名前）、下に文。
    morning：朝のメール（赤い字「流出したおそれがあります」）。dim：名前のほかを灰色に（32-04）"""
    g = (176, 182, 194)
    IC.castle_logo(d, (x0 + 60) * ss, (y0 + 58) * ss, 34 * ss)
    d.rounded_rectangle(((x0 + 110) * ss, (y0 + 44) * ss, (x0 + 330) * ss, (y0 + 72) * ss), radius=14 * ss, fill=GREYB + (255,))
    if morning:
        D.ctext(d, ((x0 + W_ / 2) * ss, (y0 + 140) * ss), "お客さまの情報が、", D.font(44 * ss), NAVY)
        D.ctext(d, ((x0 + W_ / 2) * ss, (y0 + 200) * ss), "流出したおそれがあります", D.font(44 * ss), RED)
        return
    if name_glow > 0:
        a_ = int(255 * name_glow)
        d.rounded_rectangle(((x0 + W_ / 2 - 150) * ss, (y0 + 108) * ss, (x0 + W_ / 2 + 150) * ss, (y0 + 172) * ss), radius=18 * ss, fill=TEAL_L + (a_,), outline=TEAL + (a_,), width=5 * ss)
    D.ctext(d, ((x0 + W_ / 2) * ss, (y0 + 140) * ss), "まるロボ様", D.font(52 * ss), NAVY)
    D.ctext(d, ((x0 + W_ / 2) * ss, (y0 + 210) * ss), "ご迷惑をおかけしました" if short else "このたびは、ご迷惑をおかけしました", D.font(44 * ss), g if dim else NAVY)      # short：はばのせまい札（試しの絵：字がはみ出した）
    if part2 > 0:
        a_ = int(255 * part2)
        D.ctext(d, ((x0 + W_ / 2) * ss, (y0 + 275) * ss), "おわびのお金を返します", D.font(44 * ss), (g if dim else NAVY) + (a_,))
        d.rounded_rectangle(((x0 + W_ / 2 - 190) * ss, (y0 + 315) * ss, (x0 + W_ / 2 + 190) * ss, (y0 + 380) * ss), radius=32 * ss, fill=(g if dim else BLUE) + (a_,))
        D.ctext(d, ((x0 + W_ / 2) * ss, (y0 + 348) * ss), "お手続きはこちら", D.font(44 * ss), (255, 255, 255, a_))


def mail_sprite(t, p):
    """30-03〜30-04（と 32-04）：夕方のメールの札。30-04 の頭で 2 段目（おわびのお金・青いボタン）がうすく出てくる"""
    W_, H_ = 860, 410
    im, d = _canvas(W_, H_)
    u2 = _ease((t - p["t2"]) / 0.35) if p.get("t2") is not None else 1.0
    ng = _ease((t - p["t_glow"]) / 0.3) if p.get("t_glow") is not None else 0.0
    _mail(d, 0, 0, W_, t, p, dim=p.get("dim", False), name_glow=ng, part2=u2)
    return _done(im, W_, H_)


def compare_sprite(t, p):
    """30-05：左に朝のメール、右に夕方のメール。「名前」で 2 つの灰色の帯、「印」で 2 つの印に黄色い輪（同じ時刻に）"""
    W_, H_ = 1240, 470
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, (x0, lab, mor) in enumerate(((10, "朝のメール", True), (630, "夕方のメール", False))):
        d.rounded_rectangle((x0 * S2, 60 * S2, (x0 + 600) * S2, (H_ - 10) * S2), radius=26 * S2, fill=(255, 255, 255, 245))
        D.ctext(d, ((x0 + 300) * S2, 30 * S2), lab, D.font(44 * S2), (255, 255, 255))
        _mail(d, x0, 60, 600, t, p, part2=0.0, morning=mor, short=True)
        if t >= p["t_name"]:
            d.rounded_rectangle(((x0 + 100) * S2, (60 + 32) * S2, (x0 + 340) * S2, (60 + 84) * S2), radius=24 * S2, outline=YEL + (255,), width=7 * S2)
        if t >= p["t_mark"]:
            d.ellipse(((x0 + 60 - 52) * S2, (60 + 58 - 52) * S2, (x0 + 60 + 52) * S2, (60 + 58 + 52) * S2), outline=YEL + (255,), width=7 * S2)
    return _done(im, W_, H_)


def trace_sprite(t, p):
    """31-02〜31-04：大きなメールの札。31-02 で「まるロボ様」に寄る（大きくなる）→ 31-03 で名前が青緑に光り、左上に名簿の小窓（名前が光る）
    → 31-04 で名簿から青緑の名札が飛び出し、弧をえがいてメールの「まるロボ様」の所へ。重なってから札がメールの青緑の光に替わる"""
    W_, H_ = 1240, 480
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # 右：メール（31-02 で少し大きく）
    zm = 1.0 + 0.18 * _ease((t - p["t_zoom"]) / 0.6)
    mw, mh = 600, 300
    sub = Image.new("RGBA", (mw * S2, mh * S2), (0, 0, 0, 0)); sd = ImageDraw.Draw(sub)
    sd.rounded_rectangle((0, 0, mw * S2 - 1, mh * S2 - 1), radius=26 * S2, fill=(255, 255, 255, 245))
    ng = _ease((t - p["t_glow"]) / 0.3) if t >= p["t_glow"] else 0.0
    if t >= p["t_land"]: ng = 1.0
    _mail(sd, 0, 0, mw, t, p, name_glow=ng, part2=0.0, short=True)
    sub = sub.resize((int(mw * S2 * zm), int(mh * S2 * zm)), Image.LANCZOS)
    mx, my = 890, 250
    im.alpha_composite(sub, (int(mx * S2 - sub.width / 2), int(my * S2 - sub.height / 2)))
    # 左上：名簿の小窓（31-03 から。表紙が開いた形のまま、名前の所が光る）
    if t >= p["t_book"]:
        a_ = _ease((t - p["t_book"]) / 0.35)
        bx, by, bw, bh = 40, 60, 420, 300
        d.rounded_rectangle((bx * S2, by * S2, (bx + bw) * S2, (by + bh) * S2), radius=20 * S2, fill=(31, 168, 154, int(255 * a_)))
        d.rounded_rectangle(((bx + 12) * S2, (by + 12) * S2, (bx + bw - 12) * S2, (by + bh - 12) * S2), radius=12 * S2, fill=(250, 248, 240, int(255 * a_)))
        D.ctext(d, ((bx + bw / 2) * S2, (by - 28) * S2), "影の名簿", D.font(44 * S2), (255, 255, 255, int(255 * a_)))
        for i, (kd, nm) in enumerate((("face", "名前"), ("house", "住所"), ("phone", "電話"))):
            cx = bx + 75 + i * 135; cy = by + 120
            if i == 0:
                d.ellipse(((cx - 52) * S2, (cy - 52) * S2, (cx + 52) * S2, (cy + 52) * S2), fill=TEAL_L + (int(255 * a_),))
            IC.icon(d, kd, cx * S2, cy * S2, 34 * S2, NAVY if i == 0 else (176, 182, 194))
            D.ctext(d, (cx * S2, (cy + 92) * S2), nm, D.font(44 * S2), (NAVY if i == 0 else (176, 182, 194)) + (int(255 * a_),))
    # 31-04：名札が名簿の「名前」から、弧をえがいてメールの「まるロボ様」へ（0.9 秒）。着いたら小さくなって消え、名前が光ったまま
    if p["t_fly"] <= t < p["t_land"] + 0.35:
        u = _ease((t - p["t_fly"]) / (p["t_land"] - p["t_fly"]))
        x0_, y0_ = 115, 180; x1_, y1_ = mx, my - 110 * zm + 30
        x = x0_ + (x1_ - x0_) * u; y = y0_ + (y1_ - y0_) * u - 160 * math.sin(math.pi * u)
        sc = 1.0 if t < p["t_land"] else max(0.0, 1.0 - (t - p["t_land"]) / 0.35)
        if sc > 0: _tag(d, x * S2, y * S2, 130 * S2 * sc, col=TEAL)
    return _done(im, W_, H_)


JOURNEY = [("castle", "お城"), ("bag", "市場"), ("face", "影の机"), ("house", "まるロボの家")]


def journey_sprite(t, p):
    """31-05：名札の旅の小窓。左のお城から右のまるロボの家まで、弧の上の 4 つの所が順に光り、名札が進む（線ではなく、点が順に光る）"""
    W_, H_ = 1120, 400
    im, d = _canvas(W_, H_)
    xs = [140, 410, 680, 950]; ys = [260, 150, 150, 260]      # 「まるロボの家」が札の右のはしに当たらない所（v19 の点検）
    for i, ((kd, nm), x, y) in enumerate(zip(JOURNEY, xs, ys)):
        lit = t >= p["lit"][i]
        if lit:
            v = min(1.0, (t - p["lit"][i]) / 0.25); r = 64 + 8 * math.sin(v * math.pi)
            d.ellipse(((x - r) * S2, (y - r) * S2, (x + r) * S2, (y + r) * S2), fill=TEAL_L + (255,))
        col = NAVY if lit else (176, 182, 194)
        if kd == "castle": IC.castle_logo(d, x * S2, y * S2, 44 * S2, col=(122, 90, 170) if lit else (176, 182, 194))
        else: IC.icon(d, kd, x * S2, y * S2, 40 * S2, col)
        D.ctext(d, (x * S2, (y + 95) * S2), nm, D.font(44 * S2), col)
        if i + 1 < len(xs):            # 次の所への小さな点（3 つ）
            for k in range(1, 4):
                u = k / 4; px = x + (xs[i + 1] - x) * u; py = y + (ys[i + 1] - y) * u - 30 * math.sin(math.pi * u)
                on = t >= p["lit"][i] + (p["lit"][i + 1] - p["lit"][i]) * u
                rr = 9 if on else 6
                d.ellipse(((px - rr) * S2, (py - rr) * S2, (px + rr) * S2, (py + rr) * S2), fill=(TEAL if on else (200, 206, 216)) + (255,))
    # 名札：いまいる所の上
    k = max([i for i in range(4) if t >= p["lit"][i]] or [0])
    _tag(d, xs[k] * S2, (ys[k] - 95) * S2, 90 * S2, col=TEAL)
    return _done(im, W_, H_)


def fake_sprite(t, p):
    """32-03：メールの差出人の所に、本物の会社の印をまねた印。左「流出した会社」（お城の印）、右「有名な会社」（ビルの絵）。
    それぞれの下に「ふり」（点線のわく＝まねた物）"""
    W_, H_ = 900, 330
    im, d = _canvas(W_, H_)
    for k, (x, lab) in enumerate(((240, "流出した会社"), (660, "有名な会社"))):
        a_ = _ease((t - p["t"][k]) / 0.3)
        if a_ <= 0: continue
        if k == 0: IC.castle_logo(d, x * S2, 130 * S2, 62 * S2)
        else: IC.icon(d, "bldg", x * S2, 130 * S2, 58 * S2, NAVY)
        for j in range(16):            # 点線のわく（まねた印）
            a0 = j * 2 * math.pi / 16
            d.arc(((x - 95) * S2, (130 - 95) * S2, (x + 95) * S2, (130 + 95) * S2), math.degrees(a0), math.degrees(a0) + 12, fill=RED + (255,), width=6 * S2)
        D.ctext(d, (x * S2, 270 * S2), lab + "のふり", D.font(44 * S2), NAVY)
    return _done(im, W_, H_)


def other_sprite(t, p):
    """32-06：メールのほかに、あやしい電話（ふるえる電話）と郵便（手紙）"""
    W_, H_ = 700, 300
    im, d = _canvas(W_, H_)
    for k, (x, kd, lab) in enumerate(((190, "phone", "電話"), (510, "mail", "郵便"))):
        a_ = _ease((t - p["t"][k]) / 0.3)
        if a_ <= 0: continue
        dx = 5 * math.sin((t - p["t"][k]) * 40) if kd == "phone" and t - p["t"][k] < 1.2 else 0
        IC.icon(d, kd, (x + dx) * S2, 120 * S2, 58 * S2, NAVY)
        D.ctext(d, (x * S2, 245 * S2), "あやしい" + lab, D.font(44 * S2), NAVY)
    return _done(im, W_, H_)


def ev_list7():
    E = []
    add = lambda *a: E.append(a)
    add(max(wv("30-01", "使い道") - 0.2, s("30-01") + 0.8), e("30-01") + 0.3, "tag",      # 章の頭のつなぎが終わってから
        dict(text="使い道2：家に直接届く", pos=(640, 110), size=52))
    # 30-03〜30-04：夕方のメールの札（30-04 の頭で 2 段目）
    add(s("30-03") + 0.05, e("30-04") + 0.3, "c7_mail", dict(t2=s("30-04") - 0.05))
    add(s("30-05") + 0.05, s("30-06") + 0.8, "c7_compare",      # 次の場面へのつなぎが終わるまで（v19 の点検：0.3 秒、下の絵が見えた）
        dict(t_name=wv("30-05", "名前") - 0.1, t_mark=wv("30-05", "印") - 0.1))
    add(wv("30-05", "そっくり") - 0.1, e("30-05") + 0.3, "tag", dict(text="そっくり", pos=(640, 560), size=52))
    add(s("30-06") + 0.85, e("30-06") + 0.3, "bubble", dict(obj="maru_top", icon="coin"))      # 見比べの札が消えてから（「お金が」のあたり）
    add(wv("31-01", "どこから") - 0.2, e("31-01") + 0.3, "qmark", dict(pos=(1120, 140), size=150))
    add(s("31-02") + 0.05, s("31-05") + 0.05, "c7_trace",      # 次の旅の小窓まで続ける（v19 の点検：あいだの 0.3 秒、下の絵が一瞬見えた）
        dict(t_zoom=s("31-02") + 0.1, t_glow=wv("31-03", "まるロボ") - 0.1, t_book=s("31-03") + 0.1,
                                                            t_fly=wv("31-04", "メール") - 0.6, t_land=wv("31-04", "メール") + 0.3))
    add(s("31-05") + 0.05, s("32-01") + 0.8, "c7_journey",      # 次の場面へのつなぎが終わるまで（下の絵が 0.6 秒だけ見えた）
        dict(lit=[s("31-05") + 0.2, wv("31-05", "ぐるっと") - 0.1, wv("31-05", "回って") - 0.1, wv("31-05", "自分の家") - 0.1]))
    add(wv("32-03", "ふり") - 1.6, s("32-04") + 0.05, "c7_fake",      # 次のメールの札まで続ける
        dict(t=[wv("32-03", "流出した会社") - 0.1, wv("32-03", "有名な会社") - 0.1]))
    add(s("32-04") + 0.05, s("32-06") + 0.8, "c7_mail", dict(t2=None, dim=True,      # 32-05 まで残し、次の場面へのつなぎが終わるまで
        t_glow=wv("32-04", "名前") - 0.1))      # 32-05 まで残す（札をその下に）
    add(wv("32-05", "名前で") - 0.1, e("32-05") + 0.3, "tag", dict(text="名前で呼ばれても → 本物とは限らない", pos=(640, 520), size=48))
    add(wv("32-06", "電話") - 0.3, e("32-06") + 0.3, "c7_other", dict(t=[wv("32-06", "電話") - 0.3, wv("32-06", "郵便") - 0.1]))      # 電話の絵は札と同時に（白いだけの札が出ないように）
    return E


def sfx_list7():
    return [(wv("30-05", "名前") - 0.1, "tick", 0.3), (wv("30-05", "印") - 0.1, "tick", 0.3),
            (wv("31-03", "まるロボ") - 0.1, "tick", 0.3), (wv("31-04", "メール") - 0.6, "swish", 0.4),
            (wv("31-05", "ぐるっと") - 0.1, "tick", 0.25), (wv("31-05", "回って") - 0.1, "tick", 0.25), (wv("31-05", "自分の家") - 0.1, "tick", 0.25)]


def draw7(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    fn = {"c7_mail": mail_sprite, "c7_compare": compare_sprite, "c7_trace": trace_sprite, "c7_journey": journey_sprite,
          "c7_fake": fake_sprite, "c7_other": other_sprite}[kind]
    if kind != "c7_other":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(100 * a))))
    spr = fn(t, p); _paste(base, spr, 640, 30 + spr.height / 2, k, a)
