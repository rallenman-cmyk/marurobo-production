# 16本目 2章（S13〜S17）の 2D：札・見取り図・2 つの棚・写真のたとえ・読めない形・脅しの手紙・2 つの道・153 件の図
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは overlays.py と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上、数は 56 以上）
#   絵コンテ表：../絵コンテ_v1.md の「2章」
import os, sys, math, json
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import icons16 as IC
s, e, w = T.s, T.e, T.w
NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48); GREY = (190, 198, 210); TEALC = (33, 193, 179); ORANGE = (255, 138, 31)
_WT = json.load(open(os.path.join(HERE, "word_times_ch2.json"), encoding="utf-8"))


def wv(i, word, occ=0): return _WT.get("%s|%s|%d" % (i, word, occ)) or w(i, word)


S2 = 2


def _canvas(W_, H_, a=245):
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, a))
    return im, d


def _done(im, W_, H_): return im.resize((W_, H_), Image.LANCZOS)


def _tag(d, cx, cy, wdt, col=(150, 162, 178), alpha=255, icons=True):
    """名札の小さな絵（字なし）：ふちの色＋4 つの絵"""
    h = wdt * 0.63
    d.rounded_rectangle((cx - wdt / 2, cy - h / 2, cx + wdt / 2, cy + h / 2), radius=int(wdt * 0.08), fill=col + (alpha,))
    b = wdt * 0.06
    d.rounded_rectangle((cx - wdt / 2 + b, cy - h / 2 + b, cx + wdt / 2 - b, cy + h / 2 - b), radius=int(wdt * 0.05), fill=(255, 255, 255, alpha))
    if icons:
        for (fx, fy), k in zip(((-0.22, -0.16), (0.22, -0.16), (-0.22, 0.18), (0.22, 0.18)), ("face", "house", "phone", "mail")):
            IC.icon(d, k, cx + fx * wdt, cy + fy * wdt, wdt * 0.1, NAVY if alpha == 255 else (150, 160, 176))


def floorplan_sprite(t, p):
    """13-08：お城の中の見取り図（廊下 1 本と部屋 6 つ。字なし）。影が通った所に点線が 1 つずつのびる"""
    W_, H_ = 560, 360
    im, d = _canvas(W_, H_)
    X0, X1, Y = 50, 510, 250
    d.rounded_rectangle((X0 * S2, (Y - 30) * S2, X1 * S2, (Y + 30) * S2), radius=10 * S2, outline=NAVY + (255,), width=4 * S2)
    for k in range(6):
        x = X0 + 20 + k * 75
        d.rounded_rectangle((x * S2, 60 * S2, (x + 62) * S2, (Y - 40) * S2), radius=8 * S2, outline=NAVY + (255,), width=4 * S2, fill=(240, 244, 250, 255))
    n = 0 if t < p["t_go"] else min(6, int((t - p["t_go"]) / p["step"]) + 1)
    D.ctext(d, (W_ * S2 / 2, 32 * S2), "お城の中", D.font(36 * S2), NAVY)       # 確認役：何の図か分からない
    for k in range(n):        # のぞいた部屋をぬる
        x = X0 + 20 + k * 75
        d.rounded_rectangle(((x + 3) * S2, 63 * S2, (x + 59) * S2, (Y - 43) * S2), radius=6 * S2, fill=(214, 200, 246, 255))
    for k in range(n):        # 廊下から部屋へ点線（のぞいた部屋）
        x = X0 + 51 + k * 75
        for j in range(5):
            yy = Y - 6 - j * 30
            d.ellipse(((x - 5) * S2, (yy - 5) * S2, (x + 5) * S2, (yy + 5) * S2), fill=(123, 91, 214, 255))
    m = 0 if t < p["t_go"] else min(23, int((t - p["t_go"]) / (p["step"] * 6) * 23) + 1)
    for j in range(m):
        x = X0 + 12 + j * 20
        d.ellipse(((x - 5) * S2, (Y - 5) * S2, (x + 5) * S2, (Y + 5) * S2), fill=(123, 91, 214, 255))
    return _done(im, W_, H_)


def coin_sprite():
    """14-06：硬貨（字なし。金色の丸を 3 枚重ねる）"""
    W_, H_ = 220, 200
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, (dx, dy) in enumerate(((-40, 30), (40, 30), (0, -30))):
        cx, cy = (W_ / 2 + dx) * S2, (H_ / 2 + dy) * S2; r = 58 * S2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(240, 190, 60, 255), outline=(190, 140, 30, 255), width=6 * S2)
        d.ellipse((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=(255, 226, 140, 255), width=5 * S2)
    return _done(im, W_, H_)


def shelves_sprite(t, p):
    """14-08・14-12・14-13：2 つの棚（左＝名札の倉庫・右＝予備の倉庫）。
    copy：左から右へ写しが出る（14-08）／ x：左の棚に×（14-13）／ back：右から左へ戻る（14-13）"""
    W_, H_ = 980, 420
    im, d = _canvas(W_, H_)
    for side, (x0, lab) in enumerate(((60, "名札の倉庫"), (560, "予備の倉庫"))):
        d.rounded_rectangle((x0 * S2, 70 * S2, (x0 + 360) * S2, 330 * S2), radius=14 * S2, fill=(122, 90, 60, 255))
        for r in range(2):
            d.rectangle(((x0 + 14) * S2, (90 + r * 120) * S2, (x0 + 346) * S2, (190 + r * 120) * S2), fill=(80, 60, 42, 255))
        D.ctext(d, ((x0 + 180) * S2, 380 * S2), lab, D.font(44 * S2), NAVY)
    # 左の棚の名札
    gone = p.get("t_x") is not None and t >= p["t_x"]
    back = 0 if p.get("t_back") is None or t < p["t_back"] else min(1.0, (t - p["t_back"]) / 1.2)
    for r in range(2):
        for c in range(4):
            cx, cy = (60 + 60 + c * 80) * S2, (90 + 50 + r * 120) * S2
            if not gone or back > (r * 4 + c) / 8.0: _tag(d, cx, cy, 64 * S2)
    # 右の棚の写し（少し薄い）
    cp = 1.0 if p.get("t_copy") is None else (0.0 if t < p["t_copy"] else min(1.0, (t - p["t_copy"]) / 1.6))
    for r in range(2):
        for c in range(4):
            if cp > (r * 4 + c) / 8.0:
                _tag(d, (560 + 60 + c * 80) * S2, (90 + 50 + r * 120) * S2, 64 * S2, alpha=150)
    if p.get("t_copy") is not None and p["t_copy"] <= t < p["t_copy"] + 1.8:       # 写す向きの矢印
        _arrow(d, 440, 200, 540, 200, TEALC)
    if back > 0 and back < 1.0 or (p.get("t_back") is not None and p["t_back"] <= t < p["t_back"] + 1.8):
        _arrow(d, 540, 200, 440, 200, TEALC)
    if gone:
        d.line((80 * S2, 90 * S2, 400 * S2, 310 * S2), fill=RED + (255,), width=14 * S2); d.line((400 * S2, 90 * S2, 80 * S2, 310 * S2), fill=RED + (255,), width=14 * S2)
    return _done(im, W_, H_)


def _arrow(d, x0, y0, x1, y1, col):
    d.line((x0 * S2, y0 * S2, x1 * S2, y1 * S2), fill=col + (255,), width=12 * S2)
    sg = 1 if x1 > x0 else -1
    d.polygon([(x1 * S2, y1 * S2), ((x1 - sg * 26) * S2, (y1 - 20) * S2), ((x1 - sg * 26) * S2, (y1 + 20) * S2)], fill=col + (255,))


def _phone(d, cx, cy, h, photo=True, crack=False, dark=False):
    wd = h * 0.5
    d.rounded_rectangle((cx - wd / 2, cy - h / 2, cx + wd / 2, cy + h / 2), radius=int(h * 0.09), fill=(40, 44, 52, 255))
    m = h * 0.05
    scr = (cx - wd / 2 + m, cy - h / 2 + m * 1.6, cx + wd / 2 - m, cy + h / 2 - m * 1.6)
    d.rectangle(scr, fill=(18, 20, 26, 255) if dark else (236, 242, 248, 255))
    if photo and not dark: _photo(d, (scr[0] + scr[2]) / 2, (scr[1] + scr[3]) / 2, (scr[2] - scr[0]) * 0.86)
    if crack:
        pts = [(cx - wd * 0.1, cy - h * 0.3), (cx + wd * 0.08, cy - h * 0.08), (cx - wd * 0.12, cy + h * 0.06), (cx + wd * 0.1, cy + h * 0.28)]
        d.line(pts, fill=(255, 255, 255, 255), width=int(h * 0.02)); d.line([(cx + wd * 0.08, cy - h * 0.08), (cx + wd * 0.3, cy - h * 0.02)], fill=(255, 255, 255, 255), width=int(h * 0.015))


def _photo(d, cx, cy, wd):
    """写真の絵（字なし）：空・山・太陽"""
    h = wd * 0.75
    d.rectangle((cx - wd / 2, cy - h / 2, cx + wd / 2, cy + h / 2), fill=(150, 205, 240, 255))
    d.polygon([(cx - wd / 2, cy + h / 2), (cx - wd * 0.1, cy - h * 0.1), (cx + wd * 0.15, cy + h * 0.15), (cx + wd * 0.3, cy), (cx + wd / 2, cy + h / 2)], fill=(90, 160, 100, 255))
    r = wd * 0.1; d.ellipse((cx + wd * 0.22 - r, cy - h * 0.28 - r, cx + wd * 0.22 + r, cy - h * 0.28 + r), fill=(255, 200, 60, 255))


def _cloud(d, cx, cy, wd):
    for (dx, dy, r) in ((-0.28, 0.08, 0.2), (0.0, -0.08, 0.27), (0.28, 0.08, 0.2), (0.12, 0.12, 0.2), (-0.12, 0.12, 0.2)):
        d.ellipse((cx + (dx - r) * wd, cy + (dy - r) * wd, cx + (dx + r) * wd, cy + (dy + r) * wd), fill=(214, 230, 246, 255))


def photo_sprite(t, p):
    """14-10・14-11：スマホの写真を、雲の形の預け先にも預けておく → スマホが壊れる → 預けた写真から元どおり"""
    W_, H_ = 980, 470
    im, d = _canvas(W_, H_)
    _cloud(d, 690 * S2, 150 * S2, 360 * S2)
    up = 0.0 if t < p["t_up"] else min(1.0, (t - p["t_up"]) / 1.0)
    if up > 0: _photo(d, 690 * S2, 160 * S2, 120 * S2)
    if 0 < up < 1:            # スマホから雲へ、写真が飛ぶ
        x = 260 + (690 - 260) * up; y = 260 + (160 - 260) * up; _photo(d, x * S2, y * S2, 90 * S2)
    broken = t >= p["t_break"]
    newp = t >= p["t_new"]
    if not newp:
        _phone(d, 260 * S2, 265 * S2, 330 * S2, photo=True, crack=broken, dark=broken)
    else:
        _phone(d, 260 * S2, 265 * S2, 330 * S2, photo=False)
        k = min(1.0, (t - p["t_new"]) / 1.0)
        x = 690 + (260 - 690) * k; y = 160 + (260 - 160) * k
        _photo(d, x * S2, y * S2, (120 - 20 * k) * S2)
        if k < 1: _arrow(d, 600, 170, 380, 230, TEALC)
    if up > 0 and up < 1: _arrow(d, 360, 230, 560, 170, TEALC)
    D.ctext(d, (690 * S2, 330 * S2), "預け先", D.font(44 * S2), NAVY)
    return _done(im, W_, H_)


def scramble_sprite(t, p):
    """16-09：名札の 4 つの絵が、読めないぐちゃぐちゃの記号に変わる"""
    W_, H_ = 560, 360
    im, d = _canvas(W_, H_)
    k = 0.0 if t < p["t_s"] else min(1.0, (t - p["t_s"]) / 1.4)
    import random
    rnd = random.Random(int(t * 12))
    cx, cy, wd = 280 * S2, 170 * S2, 400 * S2
    h = wd * 0.63
    d.rounded_rectangle((cx - wd / 2, cy - h / 2, cx + wd / 2, cy + h / 2), radius=int(wd * 0.08), fill=(150, 162, 178, 255))
    b = wd * 0.06
    d.rounded_rectangle((cx - wd / 2 + b, cy - h / 2 + b, cx + wd / 2 - b, cy + h / 2 - b), radius=int(wd * 0.05), fill=(255, 255, 255, 255))
    for i, ((fx, fy), kd) in enumerate(zip(((-0.22, -0.16), (0.22, -0.16), (-0.22, 0.18), (0.22, 0.18)), ("face", "house", "phone", "mail"))):
        x, y = cx + fx * wd, cy + fy * wd
        if k < (i + 1) / 4.0:
            IC.icon(d, kd, x, y, wd * 0.1, NAVY)
        else:
            for j in range(7):       # 記号のかたまり（字ではない線と点）
                x1, y1 = x + rnd.uniform(-1, 1) * wd * 0.12, y + rnd.uniform(-1, 1) * wd * 0.1
                x2, y2 = x + rnd.uniform(-1, 1) * wd * 0.12, y + rnd.uniform(-1, 1) * wd * 0.1
                d.line((x1, y1, x2, y2), fill=(rnd.choice([RED, NAVY, (120, 120, 120)]) + (255,)), width=7 * S2)
    return _done(im, W_, H_)


def lockicon_sprite(sz=110):
    im = Image.new("RGBA", (240, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.arc((60, 20, 180, 140), 180, 360, fill=(255, 255, 255, 255), width=22)
    d.line((60, 80, 60, 110), fill=(255, 255, 255, 255), width=22); d.line((180, 80, 180, 110), fill=(255, 255, 255, 255), width=22)
    d.rounded_rectangle((36, 100, 204, 220), radius=20, fill=(255, 255, 255, 255))
    d.ellipse((106, 136, 134, 164), fill=(226, 58, 48, 255)); d.rectangle((114, 150, 126, 190), fill=(226, 58, 48, 255))
    return im.resize((sz, sz), Image.LANCZOS)


def letter_sprite(text, sub=None):
    """17-02・17-07：脅しの手紙（大きな札。赤い封の印つき）。字の幅を測って札の幅を決める（試しの絵：はみ出した）"""
    f0 = D.font(46 * S2)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = tmp.textlength(text, font=f0) / S2
    W_, H_ = int(min(1240, tw + 170)), 200
    im, d = _canvas(W_, H_, 250)
    d.rounded_rectangle((10 * S2, 10 * S2, (W_ - 10) * S2, (H_ - 10) * S2), radius=24 * S2, outline=(200, 190, 170, 255), width=4 * S2)
    d.polygon([(55 * S2, 65 * S2), (85 * S2, 95 * S2), (55 * S2, 125 * S2), (25 * S2, 95 * S2)], fill=RED + (255,))
    D.ctext(d, ((W_ / 2 + 40) * S2, (H_ / 2) * S2), text, f0, (150, 20, 20))
    return _done(im, W_, H_)


def pip_lockcoin_sprite():
    """17-03 の小窓：赤い錠のかかった扉 → 硬貨"""
    W_, H_ = 520, 300
    im, d = _canvas(W_, H_)
    d.rounded_rectangle((70 * S2, 40 * S2, 210 * S2, 260 * S2), radius=10 * S2, fill=(110, 80, 52, 255))
    d.rounded_rectangle((115 * S2, 140 * S2, 165 * S2, 185 * S2), radius=6 * S2, fill=RED + (255,)); d.arc((122 * S2, 112 * S2, 158 * S2, 150 * S2), 180, 360, fill=(160, 30, 30, 255), width=6 * S2)
    _arrow(d, 240, 150, 320, 150, NAVY)
    for i, (dx, dy) in enumerate(((-30, 25), (30, 25), (0, -25))):
        cx, cy = (410 + dx) * S2, (150 + dy) * S2; r = 46 * S2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(240, 190, 60, 255), outline=(190, 140, 30, 255), width=5 * S2)
    return _done(im, W_, H_)


def pip_backup_sprite(t, p):
    """17-04 の小窓：予備の倉庫の棚（写しの名札）"""
    W_, H_ = 520, 300
    im, d = _canvas(W_, H_)
    d.rounded_rectangle((60 * S2, 40 * S2, 460 * S2, 230 * S2), radius=12 * S2, fill=(122, 90, 60, 255))
    for r in range(2):
        d.rectangle((74 * S2, (56 + r * 86) * S2, 446 * S2, (128 + r * 86) * S2), fill=(80, 60, 42, 255))
        for c in range(4):
            _tag(d, (120 + c * 90) * S2, (92 + r * 86) * S2, 64 * S2, alpha=150)
    D.ctext(d, (260 * S2, 265 * S2), "予備の倉庫", D.font(40 * S2), NAVY)
    return _done(im, W_, H_)


def tworoads_sprite(t, p):
    """17-09：2 通の手紙を左右に並べ、それぞれの逃げ道（「払わずに戻す」「見せさせない」）に×"""
    W_, H_ = 1000, 440
    im, d = _canvas(W_, H_)
    for i, (x0, lab, road) in enumerate(((60, "錠をかけて脅す", "予備で元に戻す"), (540, "名札で脅す", "見せないでもらう"))):
        if t < p["t%d" % i]: continue
        d.rounded_rectangle((x0 * S2, 40 * S2, (x0 + 400) * S2, 170 * S2), radius=18 * S2, fill=(250, 246, 236, 255), outline=(200, 190, 170, 255), width=4 * S2)
        d.polygon([((x0 + 36) * S2, 84 * S2), ((x0 + 56) * S2, 104 * S2), ((x0 + 36) * S2, 124 * S2), ((x0 + 16) * S2, 104 * S2)], fill=RED + (255,))
        D.ctext(d, ((x0 + 218) * S2, 105 * S2), lab, D.font(44 * S2), (150, 20, 20))
        d.line(((x0 + 200) * S2, 175 * S2, (x0 + 200) * S2, 235 * S2), fill=NAVY + (255,), width=8 * S2)
        d.rounded_rectangle(((x0 + 20) * S2, 240 * S2, (x0 + 380) * S2, 330 * S2), radius=40 * S2, fill=(236, 240, 246, 255), outline=NAVY + (255,), width=4 * S2)
        D.ctext(d, ((x0 + 200) * S2, 285 * S2), road, D.font(44 * S2), NAVY)       # 札のはば 360・字 8 つまで
        if t >= p["tx%d" % i]:      # 道の字が読めるよう、×は字に重ねず、下に赤い丸の×を置く（試しの絵：字が×で隠れた）
            _xbadge(d, (x0 + 200) * S2, 380 * S2, 34 * S2, RED)
    return _done(im, W_, H_)


def grid153_sprite(t, p):
    """17-10・17-11：お金を求められた被害 153 件（マスを 153 個）。136 件＝2 回脅す形を赤く"""
    W_, H_ = 1000, 480
    im, d = _canvas(W_, H_)
    D.ctext(d, (W_ * S2 / 2, 42 * S2), "2025年 警察のまとめ", D.font(40 * S2), NAVY)      # 1章と同じ見出し（「確かめ」は使わない。SKILL §4）
    n = 0 if t < p["t_fill"] else min(153, int((t - p["t_fill"]) / max(0.9, p["t153"] - p["t_fill"]) * 153) + 1)
    red = 0 if t < p["t136"] else min(136, int((t - p["t136"]) / 1.0 * 136) + 1)
    for i in range(n):
        r_, c_ = divmod(i, 26)
        x = (70 + c_ * 24) * S2; y = (95 + r_ * 38) * S2
        col = RED if i < red else GREY
        d.rounded_rectangle((x, y, x + 18 * S2, y + 28 * S2), radius=5 * S2, fill=col + (255,))
    if t >= p["t153"]: D.ctext(d, (500 * S2, 355 * S2), "お金を求められた被害 153件", D.font(44 * S2), NAVY)
    if t >= p["t136"]: D.ctext(d, (500 * S2, 420 * S2), "2回脅す形 136件", D.font(56 * S2), RED)
    return _done(im, W_, H_)


def nopromise_sprite(t, p):
    """17-12：2 通の手紙に、それぞれ灰色の「約束なし」"""
    W_, H_ = 1000, 300
    im, d = _canvas(W_, H_)
    for i, (x0, lab) in enumerate(((60, "元に戻す"), (540, "見せないでくれる"))):
        d.rounded_rectangle((x0 * S2, 40 * S2, (x0 + 400) * S2, 170 * S2), radius=18 * S2, fill=(250, 246, 236, 255), outline=(200, 190, 170, 255), width=4 * S2)
        D.ctext(d, ((x0 + 200) * S2, 105 * S2), lab, D.font(46 * S2), NAVY)
        if t >= p["t%d" % i]:
            _xbadge(d, (x0 + 70) * S2, 235 * S2, 30 * S2, (130, 136, 146))
            D.ctext(d, ((x0 + 230) * S2, 235 * S2), "約束なし", D.font(52 * S2), (110, 116, 126))
    return _done(im, W_, H_)


def _xbadge(d, cx, cy, r, col):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (255,))
    k = r * 0.5
    d.line((cx - k, cy - k, cx + k, cy + k), fill=(255, 255, 255, 255), width=int(r * 0.28)); d.line((cx + k, cy - k, cx - k, cy + k), fill=(255, 255, 255, 255), width=int(r * 0.28))


def fan_img(q, q2, a):
    """15-06：門番さんの見ている向き（うすい黄色の扇）。q＝門番さん、q2＝見ている先"""
    im = Image.new("RGBA", (2560, 1440), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    dx, dy = q2[0] - q[0], q2[1] - q[1]; L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L; sp = L * 0.55
    pts = [(q[0] * 2, q[1] * 2), ((q2[0] + nx * sp) * 2, (q2[1] + ny * sp) * 2), ((q2[0] - nx * sp) * 2, (q2[1] - ny * sp) * 2)]
    d.polygon(pts, fill=(255, 226, 120, int(110 * a)))
    return im.resize((1280, 720), Image.LANCZOS)


# ---------------------------------------------------------------- 一覧（overlays.ev_list から足す）
def ev_list2():
    E = []
    add = lambda *a: E.append(a)
    add(wv("13-01", "でしょうか") - 0.3, wv("13-02", "いいえ") + 0.1, "qmark", dict(obj="shadow", dy=-150))       # 「いいえ」で消す
    add(wv("13-07", "なぜ") - 0.1, e("13-07") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(wv("13-08", "お城の中") - 0.2, e("13-08") + 0.3, "c2_floor", dict(t_go=wv("13-08", "すみずみ") - 0.3, step=0.35))
    add(wv("14-03", "管理する人") - 0.1, e("14-03") + 0.3, "tag", dict(text="管理する人のID", pos=(640, 100), size=52))
    add(wv("14-05", "名札の倉庫") - 0.1, e("14-05") + 0.3, "tag", dict(text="名札の倉庫", pos=(640, 100), size=52))
    add(wv("14-06", "お金") - 0.1, e("14-06") + 0.3, "c2_coin", dict(pos=(1040, 200)))
    add(wv("14-07", "予備の倉庫") - 0.1, e("14-07") + 0.3, "tag", dict(text="予備の倉庫", pos=(640, 100), size=52))
    add(s("14-08") - 0.05, e("14-08") + 0.3, "c2_shelves", dict(t_copy=wv("14-08", "写し") - 0.6, label=("データの写し", wv("14-08", "データ") - 0.1)))
    add(wv("14-09", "なぜ") - 0.2, e("14-09") + 0.3, "qmark", dict(obj="shadow", dy=-160))
    add(s("14-10") + 0.1, s("14-12") + 0.25, "c2_photo", dict(t_up=wv("14-10", "別の所") - 0.2, t_break=wv("14-11", "壊れても") - 0.1, t_new=wv("14-11", "元どおり") - 0.4))
    add(s("14-12") - 0.05, e("14-13") + 0.3, "c2_shelves", dict(t_copy=None, t_x=wv("14-13", "使えなく") - 0.1, t_back=wv("14-13", "元に戻せる") - 0.5))
    add(wv("15-03", "青緑") - 0.2, e("15-03") + 0.3, "ring", dict(obj="mytag", r=70, col=RED))
    add(wv("15-04", "まるロボ") - 0.05, e("15-04") + 0.6, "bubble", dict(obj="maru_top", icon="!"))
    add(wv("15-06", "正面") - 0.2, e("15-06") + 0.3, "c2_fan", dict(a="gk", b="gk_front"))
    add(wv("16-03", "何のため") - 0.3, e("16-03") + 0.3, "qmark", dict(obj="shadow", dy=-150))
    add(wv("16-05", "廊下の扉") - 0.1, e("16-05") + 0.3, "tag", dict(text="廊下の扉", obj="lk_admin", dy=-150, size=44))
    add(wv("16-05", "働く人の部屋") - 0.1, e("16-05") + 0.3, "tag", dict(text="働く人の部屋", obj="lk_work", dy=-150, size=44))
    add(s("16-09") + 0.1, e("16-09") + 0.3, "c2_scramble", dict(t_s=wv("16-09", "読めない") - 0.6))
    add(wv("16-09", "読めない") - 0.1, e("16-09") + 0.3, "tag", dict(text="読めない形に変える", pos=(640, 470), size=48))
    add(wv("16-13", "パソコン") + 0.3, e("16-13") + 0.3, "c2_lockicon", dict(obj="screen0"))
    add(wv("16-14", "注文") - 0.1, e("16-14") + 0.3, "tag", dict(text="注文", obj="orders", dy=-120, size=52))
    add(wv("16-14", "荷物") - 0.1, e("16-14") + 0.3, "tag", dict(text="荷物", obj="parcels", dy=-140, size=52))
    add(wv("17-02", "元に") - 0.1, e("17-02") + 0.4, "c2_letter", dict(text="「元に戻してほしければ、お金を払え」", pos=(640, 150)))
    add(s("17-03") + 0.1, e("17-03") + 0.3, "c2_pip", dict(which="lockcoin"))
    add(s("17-04") + 0.1, e("17-04") + 0.3, "c2_pip", dict(which="backup"))
    add(wv("17-04", "かも") - 0.1, e("17-04") + 0.3, "qmark", dict(pos=(560, 120), size=120))
    add(s("17-06") + 0.1, e("17-06") + 0.3, "pip_clip", dict(clip="P17", src_t=wv("14-04", "こっそり") - 0.9))
    add(wv("17-07", "払わなければ") - 0.1, e("17-07") + 0.4, "c2_letter", dict(text="「払わなければ、盗んだ名札をみんなに見せるぞ」", pos=(640, 150)))
    add(s("17-08"), e("17-08") + 0.2, "tint", {})
    add(s("17-09") - 0.05, s("17-10") + 0.2, "c2_roads", dict(t0=s("17-09"), t1=wv("17-09", "盗んだ名札") - 0.1, tx0=wv("17-09", "逃げ道") - 0.1, tx1=wv("17-09", "両方") - 0.1))
    add(s("17-10") - 0.05, s("17-12") + 0.2, "c2_grid", dict(t_fill=wv("17-10", "お金を") - 0.1, t153=wv("17-10", "153件") - 0.2, t136=wv("17-11", "136件") - 0.2))
    add(s("17-12") - 0.05, e("17-12") + 0.3, "c2_nopromise", dict(t0=wv("17-12", "元に戻る") - 0.1, t1=wv("17-12", "見せないで") - 0.1))
    return E


def sfx_list2():
    L = [(wv("14-06", "お金") - 0.05, "jingle", 0.3)]                     # 硬貨「ちゃりん」
    L.append((wv("14-11", "壊れても") - 0.1, "crackle", 0.3))              # スマホが割れる「ピシッ」
    L.append((wv("14-11", "元どおり") - 0.4 + 1.0, "pop", 0.35))           # 写真が戻る「ぽん」
    L.append((wv("14-13", "元に戻せる") - 0.5 + 1.2, "pop", 0.3))
    L.append((wv("16-09", "読めない") - 0.6, "zap", 0.25))                 # 読めない形に変わる「じじっ」
    for k in (0, 1): L.append((wv("17-09", ("逃げ道", "両方")[k]) - 0.1, "thud", 0.25))
    return L


def draw2(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    """overlays.draw から呼ぶ。描いたら True"""
    k, a = _pop_k, _pop_a
    if kind == "c2_floor": _paste(base, floorplan_sprite(t, p), 960, 260, k, a)
    elif kind == "c2_coin": _paste(base, coin_sprite(), p["pos"][0], p["pos"][1], k, a)
    elif kind == "c2_shelves":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        _paste(base, shelves_sprite(t, p), 640, 260, k, a)
        lab = p.get("label")
        if lab and t >= lab[1]:
            import overlays as OV
            spr, off = OV.tag_sprite(lab[0], 52); _paste(base, spr, 640, 50 + spr.height / 2 - 20, 1.0, a)
    elif kind == "c2_photo":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        _paste(base, photo_sprite(t, p), 640, 270, k, a)
    elif kind == "c2_fan":
        qa, qb = where(p["a"], t), where(p["b"], t)
        if qa is None or qb is None: return True
        base.alpha_composite(fan_img(qa, qb, a))
    elif kind == "c2_scramble": _paste(base, scramble_sprite(t, p), 640, 250, k, a)
    elif kind == "c2_lockicon":
        q = where(p["obj"], t)
        if q is not None: _paste(base, lockicon_sprite(), q[0], q[1], k, a)
    elif kind == "c2_letter": _paste(base, letter_sprite(p["text"]), p["pos"][0], p["pos"][1], k, a)
    elif kind == "c2_pip":
        spr = pip_lockcoin_sprite() if p["which"] == "lockcoin" else pip_backup_sprite(t, p)
        _paste(base, spr, 30 + 260, 25 + 150, k, a)
    elif kind == "c2_roads":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        _paste(base, tworoads_sprite(t, p), 640, 270, k, a)
    elif kind == "c2_grid":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        _paste(base, grid153_sprite(t, p), 640, 285, k, a)
    elif kind == "c2_nopromise":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        _paste(base, nopromise_sprite(t, p), 640, 230, k, a)
    else:
        return False
    return True
