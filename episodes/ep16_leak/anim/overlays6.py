# 16本目 6章（S27〜S29）の 2D：短い札・鍵束の横の「ID」「パスワード」・28-09 の「お城と同じパスワード」の図
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜5章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   語り手の「？」は 1 文に 1 つ・物は急に出さない）。絵コンテ表：../絵コンテ_v1.md の「6章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import icons16 as IC
from overlays2 import wv, _canvas, _done, S2, NAVY, RED
s, e = T.s, T.e
TEAL = (47, 217, 200); GOLD = (201, 162, 74); GOLD_D = (150, 116, 40)


def _key(d, cx, cy, r, col=GOLD, dk=GOLD_D):
    """鍵の絵（輪・軸・歯 2 つ）。右を向く"""
    d.ellipse((cx - r * 1.4, cy - r * 0.5, cx - r * 0.4, cy + r * 0.5), outline=col + (255,), width=int(r * 0.28))
    d.rectangle((cx - r * 0.45, cy - r * 0.13, cx + r * 1.4, cy + r * 0.13), fill=col + (255,))
    for dx in (0.85, 1.25): d.rectangle((cx + r * dx - r * 0.1, cy + r * 0.1, cx + r * dx + r * 0.1, cy + r * 0.5), fill=dk + (255,))


def same_sprite(t, p):
    """28-09：左にお城の印と鍵、右に青緑の縁のドアと鍵。2 つの鍵が同じ形（＝）。下に「同じパスワード」"""
    W_, H_ = 860, 330
    im, d = _canvas(W_, H_)
    IC.castle_logo(d, 190 * S2, 120 * S2, 70 * S2)
    d.rounded_rectangle((615 * S2, 55 * S2, 725 * S2, 190 * S2), radius=6 * S2, outline=TEAL + (255,), width=10 * S2, fill=(122, 85, 54, 255))     # 青緑の縁のドア
    d.ellipse((695 * S2, 118 * S2, 707 * S2, 130 * S2), fill=(201, 176, 116, 255))
    u = min(1.0, max(0.0, (t - p["t_k"]) / 0.4))
    if u > 0:
        _key(d, 190 * S2, 235 * S2, 40 * S2 * u); _key(d, 670 * S2, 235 * S2, 40 * S2 * u)
    if t >= p["t_eq"]:
        D.ctext(d, (430 * S2, 160 * S2), "＝", D.font(110 * S2), NAVY)
        D.ctext(d, (430 * S2, 290 * S2), "同じパスワード", D.font(48 * S2), RED)
    return _done(im, W_, H_)


def ev_list6():
    E = []
    add = lambda *a: E.append(a)
    add(wv("27-01", "ほかのドア") - 0.2, e("27-01") + 0.3, "tag", dict(text="使い道1：ほかのドアを試す", pos=(640, 110), size=52))
    add(wv("27-05", "自動で") - 0.1, e("27-05") + 0.3, "tag", dict(text="自動で次々に試すプログラム", pos=(640, 110), size=50))
    add(wv("27-06", "IDとパスワード") - 0.1, e("27-06") + 0.3, "tag", dict(text="鍵 ＝ IDとパスワード", pos=(640, 110), size=52))
    add(s("28-09") + 0.1, e("28-09") + 0.3, "c6_same", dict(t_k=s("28-09") + 0.2, t_eq=wv("28-09", "同じパスワード") - 0.1))
    add(wv("28-11", "別のパスワード") - 0.1, e("28-11") + 0.3, "tag", dict(text="別のパスワード", pos=(640, 110), size=52))
    add(wv("29-02", "使い回し") - 0.2, e("29-02") + 0.3, "tag", dict(text="同じパスワードの使い回し → 開いてしまう", pos=(640, 110), size=46))
    return E


def sfx_list6():
    return [(wv("28-09", "同じパスワード") - 0.1, "tick", 0.3)]


def draw6(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    if kind == "c6_same":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
        spr = same_sprite(t, p); _paste(base, spr, 640, 40 + spr.height / 2, k, a)
