# 16本目：3D に貼る絵（字は書かない。3D の中に字を書かない決まり）。スマホの画面・名札の面・入力の板・ニュースの見出しの絵の地
# python3 make_tex16.py <出力フォルダ>
import os, sys, math
from PIL import Image, ImageDraw
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
TEAL = (47, 217, 200); TEAL_D = (20, 150, 140); NAVY = (24, 38, 74); WHITE = (255, 255, 255); GREY = (200, 206, 214); RED = (226, 58, 48)
ORANGE = (255, 154, 60); GREEN = (90, 180, 100); CASTLE = (120, 96, 170)
SS = 2
from icons16 import castle_logo, icon


def card(name, items, border, w=600, h=380):
    """札の面（はがきの形）。items：絵の種類のならび（2×2 か 3 つ）"""
    im = Image.new("RGB", (w * SS, h * SS), WHITE); d = ImageDraw.Draw(im)
    b = 22 * SS
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=40 * SS, fill=border)
    d.rounded_rectangle((b, b, w * SS - b, h * SS - b), radius=28 * SS, fill=WHITE)
    n = len(items)
    pos = [(0.27, 0.33), (0.73, 0.33), (0.27, 0.72), (0.73, 0.72)] if n == 4 else [(0.2, 0.5), (0.5, 0.5), (0.8, 0.5)]
    for k, (fx, fy) in zip(items, pos):
        icon(d, k, fx * w * SS, fy * h * SS, 62 * SS, NAVY if k != "face" else NAVY)
    im.resize((w, h), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


def screen(name, kind):
    """スマホの画面（縦 1:2.14）。字は書かない（字は 2D の札で重ねる）"""
    W_, H_ = 420, 900
    im = Image.new("RGB", (W_ * SS, H_ * SS), (236, 242, 248)); d = ImageDraw.Draw(im)
    S = lambda *v: tuple(x * SS for x in v)
    if kind == "home":       # ホームの画面に、上から通知の帯（お店の印と、字の代わりの灰色の線）
        im.paste((150, 196, 230), S(0, 0, W_, H_))
        for i in range(4):
            for j in range(4):
                x = 40 + j * 92; y = 330 + i * 120
                d.rounded_rectangle(S(x, y, x + 64, y + 64), radius=16 * SS, fill=[(255, 255, 255), (255, 214, 120), (130, 210, 170), (240, 140, 120)][(i + j) % 4])
        d.rounded_rectangle(S(20, 60, W_ - 20, 210), radius=26 * SS, fill=(250, 251, 253))
        castle_logo(d, 80 * SS, 135 * SS, 38 * SS)
        for k, ww in enumerate((210, 260, 180)):
            d.rounded_rectangle(S(140, 95 + k * 30, 140 + ww, 110 + k * 30), radius=6 * SS, fill=GREY)
    elif kind in ("mail", "mail_end", "mail2"):   # メールを開いた画面：上にお店の印、赤い線（大事なお知らせ）、灰色の行
        d.rectangle(S(0, 0, W_, 120), fill=(250, 251, 253))
        castle_logo(d, 70 * SS, 62 * SS, 36 * SS)
        d.rounded_rectangle(S(125, 45, 330, 70), radius=6 * SS, fill=GREY)
        top = 150
        if kind != "mail2":
            d.rounded_rectangle(S(30, top, W_ - 30, top + 70), radius=12 * SS, fill=(253, 232, 230))
            d.rounded_rectangle(S(50, top + 25, W_ - 70, top + 45), radius=6 * SS, fill=RED)
            top += 110
        n = 5 if kind != "mail_end" else 3
        for k in range(n):
            ww = [330, 300, 340, 250, 180][k]
            d.rounded_rectangle(S(30, top + k * 46, 30 + ww, top + k * 46 + 18), radius=6 * SS, fill=GREY)
        if kind == "mail2":   # 7章：手続きのボタン（青い帯）
            d.rounded_rectangle(S(60, top + 300, W_ - 60, top + 370), radius=30 * SS, fill=(70, 130, 220))
    im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


def form(name):
    """会員になるときの入力の画面（4 つの欄。左に絵、右に灰色の線）"""
    W_, H_ = 600, 700
    im = Image.new("RGB", (W_ * SS, H_ * SS), (250, 251, 253)); d = ImageDraw.Draw(im)
    S = lambda *v: tuple(x * SS for x in v)
    castle_logo(d, 300 * SS, 80 * SS, 48 * SS)
    for k, kind in enumerate(("face", "house", "phone", "mail")):
        y = 170 + k * 125
        d.rounded_rectangle(S(40, y, W_ - 40, y + 100), radius=18 * SS, fill=(236, 240, 246), outline=(190, 200, 214), width=3 * SS)
        icon(d, kind, 110 * SS, (y + 50) * SS, 34 * SS, NAVY)
        d.rounded_rectangle(S(180, y + 40, 480, y + 60), radius=6 * SS, fill=GREY)
    im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


screen("ph_home", "home"); screen("ph_mail", "mail"); screen("ph_mail_end", "mail_end"); screen("ph_mail2", "mail2")
card("tag_maru", ["face", "house", "phone", "mail"], TEAL)
card("tag_orange", ["mail", "cake", "bag"], ORANGE)
card("tag_green", ["phone", "bldg", "mail"], GREEN)
form("form4")
print("ok", sorted(os.listdir(OUT)))
