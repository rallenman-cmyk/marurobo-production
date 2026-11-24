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
    """13-08：お城の中の見取り図（廊下 1 本と部屋 6 つ）。部屋の中に置いてある物の小さな絵（机・鍵・名札・写しの名札）を描き、
    影の形が廊下を左から右へ進んで、のぞいた部屋に ✓ が付く（確認役 2 回目：紫の点で埋まっていくだけで、何の図か分からなかった）"""
    W_, H_ = 560, 380
    im, d = _canvas(W_, H_)
    X0, X1, Y = 50, 510, 290
    d.rounded_rectangle((X0 * S2, (Y - 30) * S2, X1 * S2, (Y + 30) * S2), radius=10 * S2, outline=NAVY + (255,), width=4 * S2, fill=(236, 228, 214, 255))
    D.ctext(d, (W_ * S2 / 2, 32 * S2), "お城の中", D.font(36 * S2), NAVY)
    n = 0 if t < p["t_go"] else min(6, int((t - p["t_go"]) / p["step"]) + 1)
    for k, what in enumerate(("desk", "key", "", "tag", "copy", "")):       # IDOORS の順（働く人・管理する人・廊下・名札・予備・廊下）
        x = X0 + 20 + k * 75; cx = (x + 31) * S2; cy = 150 * S2
        d.rounded_rectangle((x * S2, 70 * S2, (x + 62) * S2, (Y - 40) * S2), radius=8 * S2, outline=NAVY + (255,), width=4 * S2, fill=(246, 248, 252, 255))
        d.rectangle(((x + 20) * S2, (Y - 44) * S2, (x + 42) * S2, (Y - 36) * S2), fill=(150, 110, 70, 255))      # 扉
        if what == "desk":
            d.rectangle((cx - 20 * S2, cy - 18 * S2, cx + 20 * S2, cy + 6 * S2), fill=(60, 70, 90, 255)); d.rectangle((cx - 26 * S2, cy + 10 * S2, cx + 26 * S2, cy + 18 * S2), fill=(150, 110, 70, 255))
        elif what == "key":
            d.ellipse((cx - 22 * S2, cy - 14 * S2, cx - 2 * S2, cy + 6 * S2), outline=(200, 40, 40, 255), width=5 * S2); d.line((cx - 2 * S2, cy - 4 * S2, cx + 24 * S2, cy - 4 * S2), fill=(200, 40, 40, 255), width=5 * S2)
            d.line((cx + 16 * S2, cy - 4 * S2, cx + 16 * S2, cy + 6 * S2), fill=(200, 40, 40, 255), width=5 * S2)
        elif what == "tag": _tag(d, cx, cy, 46 * S2)
        elif what == "copy": _tag(d, cx, cy, 46 * S2, alpha=150)
        if k < n:          # のぞいた部屋に ✓
            d.line(((x + 14) * S2, 215 * S2, (x + 26) * S2, 228 * S2, (x + 48) * S2, 200 * S2), fill=(40, 170, 90, 255), width=7 * S2, joint="curve")
    # 影の形（黒い丸 2 つ）が廊下を進む。通った所は点線
    if t >= p["t_go"]:
        u = min(1.0, (t - p["t_go"]) / (p["step"] * 6))
        xs = X0 + 30 + u * (X1 - X0 - 60)
        for j in range(int((xs - X0 - 20) / 18)):
            xx = X0 + 20 + j * 18; d.ellipse(((xx - 4) * S2, (Y - 4) * S2, (xx + 4) * S2, (Y + 4) * S2), fill=(123, 91, 214, 255))
        d.ellipse(((xs - 13) * S2, (Y - 34) * S2, (xs + 13) * S2, (Y - 8) * S2), fill=(30, 24, 60, 255))
        d.ellipse(((xs - 18) * S2, (Y - 12) * S2, (xs + 18) * S2, (Y + 26) * S2), fill=(30, 24, 60, 255))
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
    if gone and back < 1.0:      # 名札が戻り切ったら×を消す（確認役 2 回目：戻ったのに×のまま）
        d.line((80 * S2, 90 * S2, 400 * S2, 310 * S2), fill=RED + (255,), width=14 * S2); d.line((400 * S2, 90 * S2, 80 * S2, 310 * S2), fill=RED + (255,), width=14 * S2)
    return _done(im, W_, H_)


def _arrow(d, x0, y0, x1, y1, col):
    """矢印。矢じりは線の向きに合わせ、大きく（v7 のコメント「矢印の先が潰れてて分かりにくい」2 件：矢じりが横向きの小さな三角のままで、ななめの線では先がつぶれて見えた）"""
    L = math.hypot(x1 - x0, y1 - y0) or 1; ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux
    hl, hw = 40, 30                                   # 矢じりの長さ・半分のはば
    bx, by = x1 - ux * hl, y1 - uy * hl
    d.line((x0 * S2, y0 * S2, bx * S2, by * S2), fill=col + (255,), width=12 * S2)
    d.polygon([(x1 * S2, y1 * S2), ((bx + nx * hw) * S2, (by + ny * hw) * S2), ((bx - nx * hw) * S2, (by - ny * hw) * S2)], fill=col + (255,))


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
        if t < p["t_new"] + 2.2: _arrow(d, 600, 120, 390, 180, TEALC)      # 写真の通り道より上に描き、写真が着いてからも 1.2 秒残す（v7 のコメント「矢印の先が潰れてて分かりにくい」：写真が矢じりに重なり、1 秒で消えていた）
    if up > 0 and t < p["t_up"] + 2.2: _arrow(d, 360, 180, 570, 120, TEALC)
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
        if k < 0.06 + i / 4.0:      # 「じじっ」と同時に 1 つ目から崩れる（確認役 2 回目：音より 1 秒遅れて崩れはじめた）
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
    """17-03 の小窓：お金を払う → 錠が外れて扉が開く（硬貨 → 開いた錠の扉）。
    確認役 2 回目：「扉 → 硬貨」で、扉がお金になると読めた → 向きを逆に（お金を払うと、錠が開く）"""
    W_, H_ = 520, 300
    im, d = _canvas(W_, H_)
    for i, (dx, dy) in enumerate(((-30, 25), (30, 25), (0, -25))):
        cx, cy = (120 + dx) * S2, (150 + dy) * S2; r = 46 * S2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(240, 190, 60, 255), outline=(190, 140, 30, 255), width=5 * S2)
    _arrow(d, 200, 150, 318, 150, NAVY)
    d.rounded_rectangle((330 * S2, 40 * S2, 470 * S2, 260 * S2), radius=10 * S2, fill=(110, 80, 52, 255))
    d.rounded_rectangle((375 * S2, 150 * S2, 425 * S2, 195 * S2), radius=6 * S2, fill=RED + (255,))
    d.arc((382 * S2, 100 * S2, 418 * S2, 138 * S2), 180, 360, fill=(160, 30, 30, 255), width=6 * S2)      # 上に外れた輪（開いた錠）
    d.line((418 * S2, 119 * S2, 418 * S2, 150 * S2), fill=(160, 30, 30, 255), width=6 * S2)
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
    """17-09〜17-14：2 つの脅しと、それぞれの逃げ道、影のふさぎ方を左右 2 列に並べる。
    v5「ここ分かりにくい」→ ユーザーの選択「逃げ道とふさぎ方を並べる」。v6「ここ展開早い、状況全然理解されない」→ ユーザーの選択「1 段ずつ言う 6 文」：
    1 文で 1 段ずつ出す。a0（17-09 1 通目の逃げ道）→ b0（17-10 予備にも錠の×）→ a1（17-11 元に戻せたら？）→ b1（17-12 名札は盗まれたまま の×）→ fin（17-13 両方ふさぐ）"""
    W_ = 1120
    shown = lambda k: t >= p[k]
    rows = max((2 if shown("b%d" % i) else (1 if shown("a%d" % i) else 0)) for i in (0, 1))
    H_ = 160 + 120 * (rows >= 1) + 110 * (rows >= 2) + 110 * shown("fin")      # 出ている段だけの高さ（空いた白い所を見せない）
    im, d = _canvas(W_, H_)
    cols = ((40, "脅し① 錠", "「払えば開けてやる」", "予備で戻す", "予備の倉庫にも錠"),
            (580, "脅し② 名札", "「払わないと見せる」", "戻せば解決？", "名札は盗まれたまま"))
    f44 = D.font(44 * S2)
    for i, (x0, head, quote, road, block) in enumerate(cols):
        if not shown("a%d" % i): continue
        cx = x0 + 250
        d.rounded_rectangle((x0 * S2, 20 * S2, (x0 + 500) * S2, 140 * S2), radius=18 * S2, fill=(253, 238, 236, 255), outline=RED + (255,), width=4 * S2)
        D.ctext(d, (cx * S2, 52 * S2), head, f44, (170, 25, 25))
        D.ctext(d, (cx * S2, 108 * S2), quote, f44, (150, 20, 20))
        _arrow_v(d, cx, 146, 182, NAVY)
        d.rounded_rectangle(((x0 + 2) * S2, 188 * S2, (x0 + 498) * S2, 262 * S2), radius=37 * S2, fill=(236, 244, 250, 255), outline=NAVY + (255,), width=4 * S2)
        D.ctext(d, (cx * S2, 225 * S2), "逃げ道：" + road, f44, NAVY)
        if shown("b%d" % i):
            _arrow_v(d, cx, 268, 304, RED)
            tw_ = d.textlength(block, font=f44) / S2
            _xbadge(d, (cx - tw_ / 2 - 14) * S2, 340 * S2, 26 * S2, RED)
            D.ctext(d, ((cx + 22) * S2, 340 * S2), block, f44, RED)
    if shown("fin"):
        D.ctext(d, (W_ / 2 * S2, (H_ - 60) * S2), "払わずにすむ道が、ない", D.font(56 * S2), (170, 25, 25))
    return _done(im, W_, H_)


def _arrow_v(d, x, y0, y1, col):
    d.line((x * S2, y0 * S2, x * S2, (y1 - 10) * S2), fill=col + (255,), width=8 * S2)
    d.polygon([((x - 14) * S2, (y1 - 14) * S2), ((x + 14) * S2, (y1 - 14) * S2), (x * S2, y1 * S2)], fill=col + (255,))


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
    # 確認役 2 回目：平らな三角で「何の印か分からない」→ 門番さんの頭から前へ広がる扇（先が丸い）にし、ふちを付ける。札は ev_list2 で出す
    ang0 = math.atan2(dy, dx); half = math.radians(26)
    pts = [(q[0] * 2, q[1] * 2)] + [((q[0] + L * math.cos(ang0 + half * (2 * j / 16 - 1))) * 2, (q[1] + L * math.sin(ang0 + half * (2 * j / 16 - 1))) * 2) for j in range(17)]
    d.polygon(pts, fill=(255, 226, 120, int(105 * a)))
    d.line(pts + [pts[0]], fill=(255, 214, 90, int(230 * a)), width=6)
    return im.resize((1280, 720), Image.LANCZOS)


# ---------------------------------------------------------------- 一覧（overlays.ev_list から足す）
def ev_list2():
    E = []
    add = lambda *a: E.append(a)
    add(wv("13-01", "でしょうか") - 0.3, wv("13-02", "いいえ") + 0.1, "qmark", dict(pos=(1090, 150), size=150))       # 「いいえ」で消す。語り手の問いなので影の頭には付けない（確認役 2 回目：影が首をかしげて見えた）
    add(wv("13-07", "なぜ") - 0.1, e("13-07") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(wv("13-08", "お城の中") - 0.2, e("13-08") + 0.3, "c2_floor", dict(t_go=wv("13-08", "すみずみ") - 0.3, step=0.35))
    add(wv("14-03", "管理する人") - 0.1, e("14-03") + 0.3, "tag", dict(text="管理する人のID", pos=(640, 100), size=52))
    add(wv("14-05", "名札の倉庫") - 0.1, e("14-05") + 0.3, "tag", dict(text="名札の倉庫", pos=(640, 100), size=52))
    add(wv("14-06", "お金") - 0.1, e("14-06") + 0.3, "c2_coin", dict(pos=(1040, 200)))
    add(wv("14-07", "予備の倉庫") - 0.1, e("14-07") + 0.3, "tag", dict(text="予備の倉庫", pos=(640, 100), size=52))
    add(s("14-08") - 0.05, e("14-08") + 0.3, "c2_shelves", dict(t_copy=wv("14-08", "写し") - 0.6, label=("データの写し", wv("14-08", "データ") - 0.1)))
    add(wv("14-09", "なぜ") - 0.2, e("14-09") + 0.3, "qmark", dict(pos=(1090, 150), size=150))      # 語り手の問い。影と扉の印に重ねない（確認役 2 回目）
    add(s("14-10") + 0.1, s("14-12") + 0.25, "c2_photo", dict(t_up=wv("14-10", "別の所") - 0.2, t_break=wv("14-11", "壊れても") - 0.1, t_new=wv("14-11", "元どおり") - 0.4))
    add(s("14-12") - 0.05, e("14-13") + 0.3, "c2_shelves", dict(t_copy=None, t_x=wv("14-13", "使えなく") - 0.1, t_back=wv("14-13", "元に戻せる") - 0.5))
    add(wv("15-03", "青緑") - 0.2, e("15-03") + 0.3, "ring", dict(obj="mytag", r=70, col=RED))
    add(wv("15-04", "まるロボ") - 0.05, e("15-04") + 0.6, "bubble", dict(obj="maru_top", icon="!"))
    add(max(wv("15-06", "正面") - 0.2, s("15-06") + 0.4), e("15-06") + 0.3, "c2_fan", dict(a="gk", b="gk_front"))       # 場面が替わり終わってから（確認役 2 回目：前の廊下の場面のうちに出た）
    add(max(wv("15-06", "正面") - 0.2, s("15-06") + 0.4), e("15-06") + 0.3, "tag", dict(text="門番さんが見ている所", pos=(250, 215), size=44))
    add(wv("15-06", "横の裏口") - 0.1, e("15-06") + 0.3, "tag", dict(text="裏口", obj="door", dy=-130, size=52))
    add(wv("16-03", "何のため") - 0.3, e("16-03") + 0.3, "qmark", dict(obj="shadow", dy=-150))
    add(wv("16-05", "廊下の扉") - 0.1, e("16-05") + 0.3, "tag", dict(text="廊下の扉", obj="lk_admin", dy=-150, size=44))
    add(wv("16-05", "働く人の部屋") - 0.1, e("16-05") + 0.3, "tag", dict(text="働く人の部屋", obj="lk_work", dy=-150, size=44))
    add(s("16-09") + 0.1, e("16-09") + 0.3, "c2_scramble", dict(t_s=wv("16-09", "読めない") - 0.6))
    add(wv("16-09", "読めない") - 0.1, e("16-09") + 0.3, "tag", dict(text="読めない形に変える", pos=(640, 470), size=48))
    for k_ in (0, 1): add(wv("16-13", "パソコン") + 0.3 + 0.3 * k_, e("16-14") + 0.3, "c2_lockicon", dict(obj="screen%d" % k_))      # 2 つの画面とも、16-14 の終わりまで（確認役 2 回目：錠の印が 1 秒で消えた）
    add(wv("16-14", "注文") - 0.1, e("16-14") + 0.3, "tag", dict(text="注文", obj="orders", dy=-120, size=52))
    add(wv("16-14", "荷物") - 0.1, e("16-14") + 0.3, "tag", dict(text="荷物", obj="parcels", dy=-140, size=52))
    add(wv("17-02", "元に") - 0.1, e("17-02") + 0.4, "c2_letter", dict(text="「元に戻してほしければ、お金を払え」", pos=(640, 150)))
    add(s("17-03") + 0.1, e("17-03") + 0.3, "c2_pip", dict(which="lockcoin"))
    add(s("17-04") + 0.1, e("17-04") + 0.3, "c2_pip", dict(which="backup"))
    add(wv("17-04", "かも") - 0.1, e("17-04") + 0.3, "qmark", dict(pos=(560, 120), size=120))
    add(s("17-06") + 0.1, e("17-06") + 0.3, "pip_clip", dict(clip="P17", src_t=wv("14-04", "こっそり") - 0.9))
    add(wv("17-07", "払わなければ") - 0.1, e("17-07") + 0.4, "c2_letter", dict(text="「払わなければ、盗んだ名札をみんなに見せるぞ」", pos=(640, 150)))
    add(s("17-08"), e("17-08") + 0.2, "tint", {})
    add(s("17-09") - 0.05, s("17-15") + 0.2, "c2_roads", dict(a0=s("17-09") + 0.1, b0=wv("17-10", "錠") - 0.3, a1=s("17-11") + 0.1, b1=wv("17-12", "盗まれた") - 0.3, fin=wv("17-13", "両方") - 0.1))      # 1 文で 1 段ずつ（v6 のコメント「展開早い」）
    add(s("17-15") - 0.05, s("17-17") + 0.2, "c2_grid", dict(t_fill=s("17-15") + 0.35, t153=wv("17-15", "153件") - 0.2, t136=wv("17-16", "136件") - 0.2))
    add(wv("17-18", "国") - 0.1, e("17-18") + 0.3, "tag", dict(text="国の呼びかけ「払わないで」", pos=(640, 110), size=48))      # 確認役 2 回目：「国も呼びかけています」に絵がなかった
    add(s("17-17") - 0.05, e("17-17") + 0.3, "c2_nopromise", dict(t0=wv("17-17", "元に戻る") - 0.1, t1=wv("17-17", "見せないで") - 0.1))
    return E


def sfx_list2():
    L = [(wv("14-06", "お金") - 0.05, "jingle", 0.3)]                     # 硬貨「ちゃりん」
    L.append((wv("14-11", "壊れても") - 0.1, "crackle", 0.3))              # スマホが割れる「ピシッ」
    L.append((wv("14-11", "元どおり") - 0.4 + 1.0, "pop", 0.35))           # 写真が戻る「ぽん」
    L.append((wv("14-13", "元に戻せる") - 0.5 + 1.2, "pop", 0.3))
    L.append((wv("16-09", "読めない") - 0.6 + 0.08, "zap", 0.25))                 # 読めない形に変わる「じじっ」
    L.append((wv("17-10", "錠") - 0.3, "thud", 0.25)); L.append((wv("17-12", "盗まれた") - 0.3, "thud", 0.25))      # ×が付く「どすっ」
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
        spr = tworoads_sprite(t, p); _paste(base, spr, 640, 40 + spr.height / 2, k, a)       # 上の端をそろえ、段が増えると下へのびる
    elif kind == "c2_grid":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        _paste(base, grid153_sprite(t, p), 640, 285, k, a)
    elif kind == "c2_nopromise":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        _paste(base, nopromise_sprite(t, p), 640, 230, k, a)
    else:
        return False
    return True
