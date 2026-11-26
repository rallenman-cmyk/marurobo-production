# 16本目：3D に貼る絵（字は書かない。3D の中に字を書かない決まり）。スマホの画面・名札の面・入力の板・ニュースの見出しの絵の地
# python3 make_tex16.py <出力フォルダ>
import os, sys, math
from PIL import Image, ImageDraw
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
TEAL = (47, 217, 200); TEAL_D = (20, 150, 140); NAVY = (24, 38, 74); WHITE = (255, 255, 255); GREY = (200, 206, 214); RED = (226, 58, 48)
ORANGE = (255, 154, 60); GREEN = (90, 180, 100); CASTLE = (120, 96, 170)
SS = 2
from icons16 import castle_logo, icon


def card(name, items, border, w=600, h=380, pale=0.0):
    """札の面（はがきの形）。items：絵の種類のならび（2×2 か 3 つ）"""
    im = Image.new("RGB", (w * SS, h * SS), WHITE); d = ImageDraw.Draw(im)
    b = 22 * SS
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=40 * SS, fill=border)
    d.rounded_rectangle((b, b, w * SS - b, h * SS - b), radius=28 * SS, fill=WHITE)
    n = len(items)
    pos = [(0.27, 0.33), (0.73, 0.33), (0.27, 0.72), (0.73, 0.72)] if n == 4 else [(0.2, 0.5), (0.5, 0.5), (0.8, 0.5)]
    for k, (fx, fy) in zip(items, pos):
        icon(d, k, fx * w * SS, fy * h * SS, 62 * SS, NAVY if k != "face" else NAVY)
    if pale: im = Image.blend(im, Image.new("RGB", im.size, WHITE), pale)      # 2章：予備の倉庫の写し（少し薄い色）
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
# 2章：お城の倉庫のお客さんの名札（白っぽい灰色のふち）と、予備の倉庫の写し（薄い）
card("tag_cust", ["face", "house", "phone", "mail"], (150, 162, 178))
card("tag_copy", ["face", "house", "phone", "mail"], (150, 162, 178), pale=0.45)
card("tag_maru_copy", ["face", "house", "phone", "mail"], TEAL, pale=0.45)
# 3章：市場の箱の印（お城の形。字なし）と値札（硬貨の絵 1 つ）
def emblem(name, col, kind):
    """箱の前に貼る印（四角い白地に、色の丸とお城の形）。kind 0＝冒頭のメールのお店の印（まるロボのお城）。1〜5＝ほかのお城（形がちがう）"""
    W_ = 400
    im = Image.new("RGB", (W_ * SS, W_ * SS), (246, 242, 232)); d = ImageDraw.Draw(im)
    c = W_ / 2 * SS; r = 150 * SS
    if kind == 0:
        castle_logo(d, c, c, r, col); im.resize((W_, W_), Image.LANCZOS).save(os.path.join(OUT, name + ".png")); return
    d.ellipse((c - r, c - r, c + r, c + r), fill=col)
    w = r * 1.15; base = c + r * 0.45
    if kind == 1:       # 塔 3 つ（とがった屋根）
        for k, (dx, h) in enumerate(((-0.38, 0.55), (0, 0.8), (0.38, 0.55))):
            x = c + dx * r; tw = r * 0.26
            d.rectangle((x - tw / 2, base - h * r, x + tw / 2, base), fill=WHITE)
            d.polygon([(x - tw * 0.7, base - h * r), (x, base - h * r - r * 0.3), (x + tw * 0.7, base - h * r)], fill=WHITE)
    elif kind == 2:     # 丸い屋根 1 つ
        d.rectangle((c - w * 0.35, base - r * 0.55, c + w * 0.35, base), fill=WHITE)
        d.pieslice((c - w * 0.35, base - r * 1.05, c + w * 0.35, base - r * 0.1), 180, 360, fill=WHITE)
    elif kind == 3:     # 横に長いかべと、ぎざぎざ 2 段
        d.rectangle((c - w * 0.5, base - r * 0.45, c + w * 0.5, base), fill=WHITE)
        for k in range(7):
            if k % 2 == 0: d.rectangle((c - w * 0.5 + k * w / 7, base - r * 0.65, c - w * 0.5 + (k + 1) * w / 7, base - r * 0.45), fill=WHITE)
        d.rectangle((c - r * 0.15, base - r * 0.95, c + r * 0.15, base - r * 0.45), fill=WHITE)
    elif kind == 4:     # 塔 2 つと旗
        for dx in (-0.3, 0.3):
            x = c + dx * r; d.rectangle((x - r * 0.15, base - r * 0.75, x + r * 0.15, base), fill=WHITE)
        d.rectangle((c - r * 0.3, base - r * 0.45, c + r * 0.3, base), fill=WHITE)
        d.line((c, base - r * 0.45, c, base - r * 1.0), fill=WHITE, width=int(r * 0.06)); d.polygon([(c, base - r * 1.0), (c + r * 0.3, base - r * 0.9), (c, base - r * 0.8)], fill=WHITE)
    elif kind == 5:     # ぎざぎざのかべと、まん中のとがった高い塔（家に見えないように、ぎざぎざを付ける）
        d.rectangle((c - w * 0.45, base - r * 0.4, c + w * 0.45, base), fill=WHITE)
        for k in range(9):
            if k % 2 == 0: d.rectangle((c - w * 0.45 + k * w * 0.9 / 9, base - r * 0.55, c - w * 0.45 + (k + 1) * w * 0.9 / 9, base - r * 0.4), fill=WHITE)
        d.rectangle((c - r * 0.17, base - r * 0.9, c + r * 0.17, base - r * 0.4), fill=WHITE)
        d.polygon([(c - r * 0.25, base - r * 0.9), (c, base - r * 1.25), (c + r * 0.25, base - r * 0.9)], fill=WHITE)
    d.rectangle((c - r * 0.1, base - r * 0.25, c + r * 0.1, base), fill=col)        # 門
    im.resize((W_, W_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


emblem("emb0", CASTLE, 0)
for k, col in enumerate([(214, 72, 64), (70, 160, 90), (240, 150, 50), (60, 90, 170), (150, 110, 70)]):
    emblem("emb%d" % (k + 1), col, k + 1)
# 値札：白い札に硬貨の絵が 1 つ（数字なし）。上にひもの穴
W_, H_ = 300, 420
im = Image.new("RGB", (W_ * SS, H_ * SS), (250, 248, 240)); d = ImageDraw.Draw(im)
d.ellipse(((W_ / 2 - 18) * SS, 30 * SS, (W_ / 2 + 18) * SS, 66 * SS), fill=(120, 110, 96))
cx, cy, r = W_ / 2 * SS, 250 * SS, 70 * SS
d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(240, 190, 60), outline=(190, 140, 30), width=8 * SS)
d.ellipse((cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62), outline=(255, 226, 140), width=6 * SS)
im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, "pricetag.png"))
# 6章：ドアの上の看板（字なし。白い板に絵 1 つ。会社の名前・見た目は出さない）。play＝再生の三角（動画）・note＝音符（音楽）
def sign(name, kind, col):
    W_, H_ = 480, 220
    im = Image.new("RGB", (W_ * SS, H_ * SS), col); d = ImageDraw.Draw(im)
    d.rounded_rectangle((14 * SS, 14 * SS, (W_ - 14) * SS, (H_ - 14) * SS), radius=24 * SS, fill=(252, 251, 247))
    cx, cy, r = W_ / 2 * SS, H_ / 2 * SS, 70 * SS
    if kind == "play":
        # 画面の枠（紺の線）と、中の三角（実在の会社の印に似せない：赤い角丸に白い三角はやめた）
        d.rounded_rectangle((cx - r * 1.2, cy - r * 0.8, cx + r * 1.2, cy + r * 0.65), radius=int(r * 0.12), outline=NAVY, width=int(r * 0.13))
        d.rectangle((cx - r * 0.5, cy + r * 0.75, cx + r * 0.5, cy + r * 0.85), fill=NAVY)
        d.polygon([(cx - r * 0.3, cy - r * 0.45), (cx + r * 0.45, cy - r * 0.07), (cx - r * 0.3, cy + r * 0.3)], fill=NAVY)
    elif kind == "note":
        d.ellipse((cx - r * 0.75, cy + r * 0.2, cx - r * 0.15, cy + r * 0.7), fill=NAVY); d.ellipse((cx + r * 0.25, cy + r * 0.05, cx + r * 0.85, cy + r * 0.55), fill=NAVY)
        d.rectangle((cx - r * 0.25, cy - r * 0.8, cx - r * 0.15, cy + r * 0.45), fill=NAVY); d.rectangle((cx + r * 0.75, cy - r * 0.95, cx + r * 0.85, cy + r * 0.3), fill=NAVY)
        d.polygon([(cx - r * 0.25, cy - r * 0.8), (cx + r * 0.85, cy - r * 0.95), (cx + r * 0.85, cy - r * 0.7), (cx - r * 0.25, cy - r * 0.55)], fill=NAVY)
    else:
        icon(d, kind, cx, cy, r, NAVY)
    im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


for kind, col in (("bag", (236, 150, 60)), ("play", (90, 160, 200)), ("mail", (70, 130, 210)), ("phone", (90, 170, 110)), ("cake", (220, 120, 170)),
                  ("bldg", (120, 130, 150)), ("note", (150, 110, 200)), ("house", (180, 140, 90))):
    sign("sign_" + kind, kind, col)
# 6章：灰色の×の札（試して開かなかったドア）
im = Image.new("RGBA", (300 * SS, 300 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.ellipse((10 * SS, 10 * SS, 290 * SS, 290 * SS), fill=(236, 238, 242, 255), outline=(150, 156, 166, 255), width=10 * SS)
for a_, b_ in (((80, 80), (220, 220)), ((220, 80), (80, 220))):
    d.line((a_[0] * SS, a_[1] * SS, b_[0] * SS, b_[1] * SS), fill=(120, 126, 136, 255), width=34 * SS)
im.resize((300, 300), Image.LANCZOS).save(os.path.join(OUT, "xmark.png"))
print("ok", sorted(os.listdir(OUT)))
