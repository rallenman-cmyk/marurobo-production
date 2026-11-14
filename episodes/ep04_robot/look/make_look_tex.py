# 図の場面を 3D にするための絵（3D の板に貼る）。字は貼らない（ゆがんだ単語は「絵」として貼る。読ませる字は 2D の札）
# python3 make_look_tex.py <フォント NotoSansJP_700Bold.ttf> <出力（board の tex と同じ所）>
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFont
import numpy as np
FB, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "storyboard", "board_overlay.py"), encoding="utf-8").read()
def font(n): return ImageFont.truetype(FB, n)
exec(src[src.index("def warp_word"):src.index("def chat_icon")])
NAVY = (20, 36, 72); NAVY2 = (47, 74, 115); WHITE = (255, 255, 255)
S = 2
def captcha(name, upon_col=(60, 60, 70)):
    W, H = 1000 * S, 270 * S
    im = Image.new("RGB", (W, H), WHITE); d = ImageDraw.Draw(im)
    for k, (w, seed) in enumerate((("morning", 3), ("upon", 7))):
        wi = warp_word(w, 110 * S, seed)
        im.paste(Image.new("RGB", wi.size, upon_col if k else (60, 60, 70)), ((50 if k == 0 else 560) * S, 40 * S), wi)
    d.rounded_rectangle([200 * S, 215 * S, 800 * S, 255 * S], 10 * S, fill=(240, 243, 246), outline=(170, 182, 198), width=3 * S)
    im.save(os.path.join(OUT, name + ".png"))
captcha("lk_captcha"); captcha("lk_captcha_r", (170, 110, 20))
wi = warp_word("upon", 110 * S, 7); im = Image.new("RGB", (wi.width + 80, wi.height + 40), WHITE)
im.paste(Image.new("RGB", wi.size, (170, 110, 20)), (40, 20), wi); im.save(os.path.join(OUT, "lk_upon.png"))
# 記録のアイコン（新聞・カート・再生）：白い角の丸い板に色の印
def icon(name, col, draw):
    im = Image.new("RGB", (400, 400), WHITE); d = ImageDraw.Draw(im)
    d.ellipse([60, 60, 340, 340], outline=col, width=22); draw(d, col); im.save(os.path.join(OUT, name + ".png"))
icon("lk_news", NAVY2, lambda d, c: [d.rounded_rectangle([140, 145, 260, 255], 10, outline=c, width=14)] + [d.line([(165, y), (235, y)], fill=c, width=10) for y in (180, 200, 220)])
def cart(d, c):
    d.line([(125, 150), (155, 150), (180, 240), (265, 240), (285, 175), (165, 175)], fill=c, width=16, joint="curve")
    for x in (190, 255): d.ellipse([x - 14, 260, x + 14, 288], fill=c)
icon("lk_cart", (226, 76, 66), cart)
icon("lk_play", (33, 193, 179), lambda d, c: d.polygon([(170, 135), (170, 265), (275, 200)], fill=c))
# ふつうのページ（ChatGPT が操作している画面）
im = Image.new("RGB", (1600, 1000), (214, 222, 232)); d = ImageDraw.Draw(im)
d.rectangle([0, 0, 1600, 90], fill=(198, 210, 224))
for k in range(3): d.ellipse([30 + k * 40, 22, 56 + k * 40, 48], fill=(160, 176, 196))
for y, w in ((150, 760), (230, 560), (310, 700), (390, 520), (470, 640)): d.rounded_rectangle([120, y, 120 + w, y + 34], 17, fill=(186, 198, 214))
im.save(os.path.join(OUT, "lk_page.png"))
# チェック欄の絵から、矢印を消した版（3D の矢印を動かすので）
im = Image.open(os.path.join(OUT, "scr_check.png")).convert("RGB"); ImageDraw.Draw(im).rectangle([1235, 805, 1325, 925], fill=(214, 222, 232))
im.save(os.path.join(OUT, "lk_check.png"))
print("TEX OK")
