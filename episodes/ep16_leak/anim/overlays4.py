# 16本目 4章（S22〜S24）の 2D：値札の小さな絵・透ける箱の小窓・紙とデジタルの写しの図・外へ広がる図・「？」
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜3章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   図は 1 文で 1 段ずつ・語り手の「？」は画面のすみ・場面のつなぎの中で大事な動きを始めない）
#   絵コンテ表：../絵コンテ_v1.md の「4章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
from overlays2 import wv, _canvas, _done, _tag, _arrow, S2, NAVY, RED, WHITE
s, e = T.s, T.e
TEAL = (47, 217, 200); PAPER = (205, 186, 150)
GOLD = (240, 190, 60); GOLD_D = (190, 140, 30)


def _coin(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (255,), outline=GOLD_D + (255,), width=max(2, int(r * 0.14)))
    d.ellipse((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=(255, 226, 140, 255), width=max(2, int(r * 0.1)))


def _glow_tag(d, cx, cy, w, a=1.0):
    """光るデジタルの名札（青緑のふち＋まわりの光）"""
    for k in range(4, 0, -1):
        r = w * (0.5 + 0.06 * k)
        d.rounded_rectangle((cx - r, cy - r * 0.63 - w * 0.02 * k, cx + r, cy + r * 0.63 + w * 0.02 * k), radius=int(w * 0.12),
                            fill=(120, 240, 225, int(28 * a)))
    _tag(d, cx, cy, w, col=TEAL)


def ptag_sprite(t, p):
    """22-07「安いから」：3章の値札（白い札に硬貨 1 つ）の小さな絵"""
    W_, H_ = 170, 230
    im, d = _canvas(W_, H_)
    d.rounded_rectangle((25 * S2, 22 * S2, 145 * S2, 208 * S2), radius=10 * S2, fill=(255, 246, 214, 255), outline=(150, 120, 70, 255), width=4 * S2)
    d.ellipse((77 * S2, 34 * S2, 93 * S2, 50 * S2), fill=(120, 110, 96, 255))
    _coin(d, 85 * S2, 135 * S2, 38 * S2)
    return _done(im, W_, H_)


def xray_sprite(t, p):
    """23-05：3章で影が持っていった箱が透けて、中に同じ青緑の名札（小窓）。左に、箱を持つ影の形"""
    W_, H_ = 470, 330
    im, d = _canvas(W_, H_)
    # 影（黒い形。輪郭は紫）
    d.ellipse((40 * S2, 60 * S2, 120 * S2, 140 * S2), fill=(24, 22, 40, 255), outline=(110, 90, 220, 255), width=3 * S2)
    d.rounded_rectangle((30 * S2, 130 * S2, 130 * S2, 300 * S2), radius=40 * S2, fill=(24, 22, 40, 255), outline=(110, 90, 220, 255), width=3 * S2)
    # 透けた箱（段ボールの色をうすく、ふちは濃く）
    bx0, by0, bx1, by1 = 150, 95, 440, 290
    d.rectangle((bx0 * S2, by0 * S2, bx1 * S2, by1 * S2), fill=(180, 138, 90, 90), outline=(140, 100, 60, 255), width=5 * S2)
    d.line((bx0 * S2, by0 * S2, (bx0 + 40) * S2, (by0 - 40) * S2, (bx1 + 0) * S2, (by0 - 40) * S2, bx1 * S2, by0 * S2), fill=(140, 100, 60, 255), width=5 * S2)
    for k in range(3):        # 中の名札（青緑）
        _tag(d, (205 + 85 * k) * S2, (195 + (k % 2) * 18) * S2, 80 * S2, col=TEAL)
    return _done(im, W_, H_)


def copy_sprite(t, p):
    """24-01〜24-06：左＝紙の名札、右＝デジタルの名札。1 文で 1 段ずつ（取られて 0 枚 → 写しが出る → 2 枚・4 枚 → 入れかわって「？」 → 1 枚取られて 3 枚）"""
    W_, H_ = 1120, 420
    im, d = _canvas(W_, H_)
    d.line((560 * S2, 30 * S2, 560 * S2, 390 * S2), fill=(200, 205, 214, 255), width=4 * S2)
    D.ctext(d, (280 * S2, 48 * S2), "紙", D.font(48 * S2), NAVY)
    D.ctext(d, (840 * S2, 48 * S2), "デジタル", D.font(48 * S2), NAVY)
    # 左：紙の名札 1 枚 → 取られると、点線のわくと「0枚」
    u = 0.0 if t < p["t_lt"] else min(1.0, (t - p["t_lt"]) / 0.7)
    cx, cy = 280, 205
    if u > 0:
        for k in range(12):        # 点線のわく（いまいた所）
            a0 = k / 12.0; x0 = cx - 95 + 190 * a0
            d.line((x0 * S2, (cy - 60) * S2, (x0 + 9) * S2, (cy - 60) * S2), fill=(150, 160, 176, 255), width=3 * S2)
            d.line((x0 * S2, (cy + 60) * S2, (x0 + 9) * S2, (cy + 60) * S2), fill=(150, 160, 176, 255), width=3 * S2)
        for k in range(7):
            y0 = cy - 60 + 120 * k / 7.0
            d.line(((cx - 95) * S2, y0 * S2, (cx - 95) * S2, (y0 + 9) * S2), fill=(150, 160, 176, 255), width=3 * S2)
            d.line(((cx + 95) * S2, y0 * S2, (cx + 95) * S2, (y0 + 9) * S2), fill=(150, 160, 176, 255), width=3 * S2)
    if u < 1.0:
        _tag(d, (cx - 260 * u) * S2, (cy - 40 * u) * S2, 190 * S2, col=PAPER, alpha=int(255 * (1 - u)) if u > 0 else 255)
    D.ctext(d, (cx * S2, 340 * S2), "0枚" if u >= 0.5 else "1枚", D.font(52 * S2), RED if u >= 0.5 else NAVY)
    # 右：デジタルの名札
    P2 = [(-95, 0), (95, 0)]; P4 = [(-95, -58), (95, -58), (-95, 62), (95, 62)]
    rx, ry = 840, 200
    if t < p["t_c1"]:
        pos = [(0, 0)]; wd = 190
    elif t < p["t_4"]:
        v = min(1.0, (t - p["t_c1"]) / 0.6)            # 元の 1 枚は残ったまま、写しが右へ出る
        pos = [(-95 * v, 0), (95 * v, 0)]; wd = 190 - 40 * v
    else:
        v = min(1.0, (t - p["t_4"]) / 0.6)
        pos = [(P2[i % 2][0] + (P4[i][0] - P2[i % 2][0]) * v, P4[i][1] * v) for i in range(4)]; wd = 150
        if t >= p["t_sh"]:                               # 入れかわって並び直す（どれが元か分からない）
            w_ = min(1.0, (t - p["t_sh"]) / 1.2); order = [3, 0, 1, 2]
            pos = [(P4[i][0] + (P4[order[i]][0] - P4[i][0]) * math.sin(math.pi * w_ / 2), P4[i][1] + (P4[order[i]][1] - P4[i][1]) * math.sin(math.pi * w_ / 2)) for i in range(4)]
    gone = 0.0 if t < p["t_take"] else min(1.0, (t - p["t_take"]) / 0.7)
    for i, (dx, dy) in enumerate(pos):
        if i == 0 and gone > 0:
            if gone >= 1.0: continue
            dx += 240 * gone; dy -= 40 * gone
        pulse = 1.0 + (0.08 * math.sin(min(1.0, (t - p["t_2"]) / 0.5) * math.pi) if p["t_2"] <= t < p["t_2"] + 0.5 else 0.0)
        _glow_tag(d, (rx + dx) * S2, (ry + dy) * S2, wd * pulse * S2)
    if p["t_q"] <= t < p["t_take"]:
        D.ctext(d, ((rx + 210) * S2, 70 * S2), "？", D.font(60 * S2), RED)
    n = 1 if t < p["t_c1"] else (2 if t < p["t_4"] else (4 if gone < 0.5 else 3))
    D.ctext(d, (rx * S2, 340 * S2), "%d枚" % n, D.font(52 * S2), NAVY)
    return _done(im, W_, H_)


def out_sprite(t, p):
    """24-09：1 枚の名札から、矢印で外へたくさんの写し。下に「一度出ると、取り戻せない」"""
    W_, H_ = 1120, 430
    im, d = _canvas(W_, H_)
    cx, cy = 560, 185
    u = 0.0 if t < p["t_go"] else min(1.0, (t - p["t_go"]) / 1.0)
    for k in range(6):
        ang = math.radians(-160 + 64 * k) if k < 3 else math.radians(20 + 64 * (k - 3))
        ang = [-150, -90, -30, 30, 90, 150][k]; ang = math.radians(ang)
        r1 = 115; r2 = 115 + 230 * u
        x1, y1 = cx + r1 * math.cos(ang) * 1.6, cy + r1 * math.sin(ang) * 0.75
        x2, y2 = cx + r2 * math.cos(ang) * 1.6, cy + r2 * math.sin(ang) * 0.75
        if u > 0.05:
            _arrow(d, x1, y1, x2 - 40 * math.cos(ang), y2 - 20 * math.sin(ang), RED)
            _glow_tag(d, x2 * S2, y2 * S2, 110 * S2)
    _glow_tag(d, cx * S2, cy * S2, 170 * S2)
    if t >= p["t_lbl"]:
        D.ctext(d, (560 * S2, 385 * S2), "一度出ると、取り戻せない", D.font(50 * S2), RED)
    return _done(im, W_, H_)


def ev_list4():
    E = []
    add = lambda *a: E.append(a)
    add(wv("22-07", "安いから") - 0.6, e("22-07") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(wv("22-07", "安いから") - 0.1, e("22-07") + 0.3, "c4_ptag", {})
    add(s("23-01") + 0.3, e("23-01") + 0.3, "qmark", dict(pos=(1120, 140), size=150))      # 語り手の問い（画面のすみ）
    add(wv("23-04", "まだ何枚") - 0.1, e("23-04") + 0.3, "ring", dict(obj="copies", r=170, col=RED))
    add(s("23-05") + 0.2, e("23-05") + 0.4, "c4_xray", {})
    add(wv("23-06", "どういう") - 0.3, e("23-06") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("24-01") - 0.05, e("24-06") + 0.3, "c4_copy", dict(t_lt=wv("24-02", "取り返せば") - 0.1, t_c1=wv("24-03", "写しても") - 0.1,
                                                            t_2=wv("24-04", "2枚に") - 0.1, t_4=wv("24-04", "4枚に") - 0.1, t_sh=s("24-05") + 0.3,
                                                            t_q=wv("24-05", "見分け") - 0.1, t_take=wv("24-06", "1枚取り返し") - 0.1))
    add(s("24-09") - 0.05, e("24-09") + 0.3, "c4_out", dict(t_go=wv("24-09", "外に出た") - 0.2, t_lbl=wv("24-09", "取り戻せない") - 0.2))
    add(wv("24-10", "どうなる") - 0.2, e("24-10") + 0.3, "qmark", dict(pos=(1120, 140), size=150))
    return E


def sfx_list4():
    L = [(wv("24-02", "取り返せば"), "swish", 0.2)]
    L.append((wv("24-03", "写しても") + 0.1, "swish", 0.25))
    L.append((wv("24-04", "2枚に"), "pop", 0.3)); L.append((wv("24-04", "4枚に"), "pop", 0.3))
    L.append((wv("24-06", "1枚取り返し"), "swish", 0.2))
    return L


def draw4(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    if kind in ("c4_copy", "c4_out"):
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(110 * a))))
        spr = copy_sprite(t, p) if kind == "c4_copy" else out_sprite(t, p)
        _paste(base, spr, 640, 30 + spr.height / 2, k, a)
    elif kind == "c4_ptag": _paste(base, ptag_sprite(t, p), 1050, 230, k, a)
    elif kind == "c4_xray": _paste(base, xray_sprite(t, p), 1000, 200, k, a)
