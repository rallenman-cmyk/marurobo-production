# ロボットではありません回：3D に貼る絵（字なし）。パソコンの画面・町の写真（信号機）・古い新聞・記録帳
# python3 make_textures.py <出力フォルダ>
# 決まり：3D の中に字を書かない（「私はロボットではありません」などの字は 2D で重ねる）。本物の画面のまねはしない
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFilter
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
NAVY = (47, 74, 115); TEAL = (33, 193, 179); ORANGE = (255, 138, 42); GREEN = (64, 176, 96)
W, H = 1600, 1000


def base():
    im = Image.new('RGB', (W, H), (238, 243, 247)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 90], fill=(206, 216, 228))
    for x in (40, 90, 140): d.ellipse([x, 30, x + 30, 60], fill=(170, 182, 198))
    return im, d


def tent(d, x, y, s):
    d.rectangle([x, y, x + 300 * s, y + 220 * s], fill=(191, 227, 242))
    d.rectangle([x, y + 150 * s, x + 300 * s, y + 220 * s], fill=(158, 208, 122))
    d.polygon([(x + 50 * s, y + 190 * s), (x + 150 * s, y + 50 * s), (x + 250 * s, y + 190 * s)], fill=(233, 105, 44))
    d.polygon([(x + 128 * s, y + 190 * s), (x + 150 * s, y + 130 * s), (x + 172 * s, y + 190 * s)], fill=(122, 46, 18))


def arrow(d, x, y, s=1.0):
    pts = [(0, 0), (0, 46), (12, 35), (21, 56), (29, 52), (20, 32), (36, 32)]
    d.polygon([(x + px * s, y + py * s) for px, py in pts], fill='white', outline=(20, 20, 20))


def card(d, checked=False, spin=False):
    # 真ん中の白い札：左に四角い欄、右は字を重ねる場所（空けておく）
    d.rounded_rectangle([380, 420, 1220, 600], 18, fill='white', outline=(170, 182, 198), width=4)
    if checked:
        d.rounded_rectangle([430, 465, 520, 555], 10, fill=GREEN)
        d.line([(448, 512), (470, 536), (505, 478)], fill='white', width=14)
    elif spin:
        d.arc([430, 465, 520, 555], 20, 300, fill=TEAL, width=10)
    else:
        d.rounded_rectangle([430, 465, 520, 555], 10, fill='white', outline=NAVY, width=6)
    d.rounded_rectangle([1080, 470, 1180, 550], 12, fill=(222, 240, 238))  # 右の小さな印（守りのマークの代わり）
    d.ellipse([1110, 485, 1150, 535], outline=TEAL, width=6)


# 1. 買い物の画面（テントが並ぶ）
im, d = base()
for i in range(3):
    tent(d, 120 + i * 470, 160, 1.2)
    d.rounded_rectangle([120 + i * 470, 450, 480 + i * 470, 490], 10, fill=(203, 211, 220))
    d.rounded_rectangle([120 + i * 470, 510, 330 + i * 470, 545], 10, fill=(225, 230, 236))
d.rounded_rectangle([1150, 820, 1500, 920], 24, fill=ORANGE)  # 「買う」のボタン（字は 2D）
arrow(d, 1330, 860, 1.6)
im.save(out + '/scr_shop.png')

# 2. チェック欄の画面（まだ押していない）
im, d = base(); d.rectangle([0, 90, W, H], fill=(214, 222, 232)); card(d)
arrow(d, 1250, 820, 1.6); im.save(out + '/scr_check.png')

# 3. まるロボが押す：矢印の跡がまっすぐ（青緑の点線）
im, d = base(); d.rectangle([0, 90, W, H], fill=(214, 222, 232)); card(d, spin=True)
for k in range(14):
    t = k / 13; x = 1250 + (475 - 1250) * t; y = 860 + (510 - 860) * t
    d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=TEAL)
arrow(d, 470, 505, 1.6); im.save(out + '/scr_robot_path.png')

# 4. 絵のテスト（3×3 の絵。信号機が写るマスもある。字は 2D）
im, d = base(); d.rectangle([0, 90, W, H], fill=(120, 130, 145))
d.rounded_rectangle([450, 130, 1150, 960], 16, fill='white')
d.rectangle([450, 130, 1150, 260], fill=(70, 130, 220))
random.seed(3)
for r in range(3):
    for c in range(3):
        x0, y0 = 480 + c * 220, 285 + r * 220
        d.rectangle([x0, y0, x0 + 200, y0 + 200], fill=(150 + random.randint(0, 60), 190, 220))
        d.rectangle([x0, y0 + 130, x0 + 200, y0 + 200], fill=(110, 110, 115))
        if (r, c) in ((0, 1), (1, 2), (2, 0)):
            d.rectangle([x0 + 90, y0 + 40, x0 + 110, y0 + 190], fill=(60, 60, 60))
            d.rounded_rectangle([x0 + 70, y0 + 20, x0 + 130, y0 + 120], 10, fill=(40, 40, 40))
            for k, col in enumerate(((230, 60, 50), (240, 190, 40), (70, 190, 90))):
                d.ellipse([x0 + 85, y0 + 27 + k * 31, x0 + 115, y0 + 57 + k * 31], fill=col)
        else:
            d.rectangle([x0 + 20, y0 + 90, x0 + 90, y0 + 150], fill=(200, 120, 80))
im.save(out + '/scr_test.png')

# 5. 私が押す：矢印の跡がくねくね（オレンジの点線）→ 緑のチェック
im, d = base(); d.rectangle([0, 90, W, H], fill=(214, 222, 232)); card(d, checked=True)
pts = []
for k in range(40):
    t = k / 39
    x = 1250 + (475 - 1250) * t + 90 * math.sin(t * 7.5) * (1 - t)
    y = 860 + (510 - 860) * t + 50 * math.sin(t * 11 + 1) * (1 - t)
    pts.append((x, y))
for i, (x, y) in enumerate(pts):
    if i % 2 == 0: d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=ORANGE)
arrow(d, 470, 505, 1.6); im.save(out + '/scr_human_pass.png')

# 6. 通った（緑のチェック・矢印なし）
im, d = base(); d.rectangle([0, 90, W, H], fill=(214, 222, 232)); card(d, checked=True); im.save(out + '/scr_pass.png')

# 7. 床の町の写真（4×4 で区切る。信号機は右上の 2 マスと、端がほんの少しだけ 3 マス目に入る）
S = 1600; im = Image.new('RGB', (S, S), (150, 200, 235)); d = ImageDraw.Draw(im)
d.rectangle([0, S * 0.55, S, S], fill=(105, 108, 115))
for x in range(0, S, 160): d.rectangle([x, S * 0.76, x + 90, S * 0.79], fill=(235, 235, 235))
for x, h, col in ((60, 380, (214, 190, 160)), (330, 520, (190, 175, 160)), (620, 300, (230, 205, 170))):
    d.rectangle([x, S * 0.55 - h, x + 230, S * 0.55], fill=col)
    for yy in range(int(S * 0.55 - h + 30), int(S * 0.55 - 30), 70):
        for xx in range(x + 25, x + 205, 60): d.rectangle([xx, yy, xx + 35, yy + 40], fill=(120, 160, 200))
d.ellipse([1380, 380, 1520, 470], fill=(80, 150, 70)); d.rectangle([1440, 450, 1460, 880], fill=(110, 80, 50))
# 信号機：本体は x=1010〜1240, y=130〜560。右端が 4 列目（x≥1200）に少しだけ入る（端っこのマス）
d.rectangle([1100, 300, 1130, 880], fill=(70, 72, 78))
d.rounded_rectangle([1010, 130, 1240, 560], 26, fill=(45, 47, 52))
for k, col in enumerate(((230, 60, 50), (240, 190, 40), (70, 190, 90))):
    d.ellipse([1050, 160 + k * 130, 1160, 270 + k * 130], fill=col)
d.rectangle([180, 980, 300, 1060], fill=(220, 80, 70)); d.rectangle([170, 1040, 330, 1090], fill=(40, 40, 40))  # 車
im.save(out + '/street.png')

# 8. 古い新聞（字の代わりの、かすれた線。光らせる単語は別の絵）
im = Image.new('RGB', (1000, 1300), (226, 214, 186)); d = ImageDraw.Draw(im); random.seed(5)
d.rectangle([40, 40, 960, 150], fill=(90, 80, 66))
for col in range(4):
    x0 = 50 + col * 230
    for y in range(190, 1260, 26):
        x = x0
        while x < x0 + 200:
            w = random.randint(14, 50)
            g = random.randint(70, 120)
            d.rectangle([x, y, min(x + w, x0 + 200), y + 10], fill=(g, g - 8, g - 20))
            x += w + 8
im = im.filter(ImageFilter.GaussianBlur(1.2)); im.save(out + '/newspaper.png')

# 9. 記録帳（スタンプ）
im = Image.new('RGB', (900, 640), (250, 246, 236)); d = ImageDraw.Draw(im)
d.line([(450, 0), (450, 640)], fill=(200, 190, 170), width=6)
random.seed(8)
for k in range(9):
    x, y = random.randint(60, 380) + (450 if k % 2 else 0), random.randint(60, 560)
    col = random.choice([(220, 80, 70), (47, 74, 115), (33, 160, 150)])
    d.ellipse([x - 45, y - 45, x + 45, y + 45], outline=col, width=9)
    d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=col)
im.save(out + '/stamps.png')
print('textures ->', out)
