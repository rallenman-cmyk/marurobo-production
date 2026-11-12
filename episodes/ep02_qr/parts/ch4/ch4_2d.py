# 4章の図（2D・1280×720）：26 まとめ（D5a〜D5d）。まるロボの切り抜き（cut/）を左下に置く
#   python3 ch4_2d.py → sb/D5a.png … D5d.png
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
F = lambda s: ImageFont.truetype(FB, s)
BG = (238, 241, 244); INK = (40, 46, 52); GRAY = (150, 158, 166); BLUE = (63, 134, 221); ORANGE = (240, 149, 58); OR_L = (251, 227, 200); RED = (217, 71, 90); TEAL = (20, 163, 180)
def robot(im, name='robot_look_right.png', x=40, y=470, h=230):
    r = Image.open(os.path.join(HERE, 'cut', name)); r = r.crop(r.split()[3].getbbox()); r = r.resize((int(r.width * h / r.height), h), Image.LANCZOS); im.alpha_composite(r, (x, y))
def row(d, y, left, right, tail='1つ'):
    d.rounded_rectangle((110, y - 42, 610, y + 42), 12, fill=(255, 255, 255), outline=(200, 205, 210), width=2)
    d.text((360, y), left, font=F(30), fill=INK, anchor='mm')
    d.text((660, y), '→', font=F(40), fill=GRAY, anchor='mm')
    d.rounded_rectangle((710, y - 42, 930, y + 42), 12, fill=OR_L, outline=ORANGE, width=3)
    d.text((820, y), right, font=F(34), fill=INK, anchor='mm')
    d.text((960, y), 'で', font=F(28), fill=GRAY, anchor='lm'); d.text((1010, y), tail, font=F(40), fill=INK, anchor='lm')
def bar(d, y, pairs=False):
    n = 26; w = 30; g = 8; x0 = (1280 - (n * w + (n - 1) * g)) / 2
    for k in range(n):
        x = x0 + k * (w + g); col = BLUE if k < 9 else ORANGE
        if pairs and k == 25: col = TEAL
        d.rounded_rectangle((x, y, x + w, y + w), 5, fill=col)
    if pairs:
        for j in range(8):
            a = x0 + (9 + 2 * j) * (w + g); b = a + 2 * w + g
            d.line((a, y + w + 10, a, y + w + 18, b, y + w + 18, b, y + w + 10), fill=ORANGE, width=3)
        d.text((x0 + 9 * (w + g) + (16 * (w + g) - g) / 2, y + w + 46), '2つで1つ直す × 8', font=F(30), fill=INK, anchor='mm')
        xe = x0 + 25 * (w + g) + w / 2; d.text((xe, y + w + 46), '確かめ', font=F(30), fill=TEAL, anchor='mm')
    return x0
def make(key):
    im = Image.new('RGBA', (1280, 720), (*BG, 255)); d = ImageDraw.Draw(im)
    row(d, 170, '消えた（場所が分かる）', '予備 1つ')
    if key in ('D5b', 'D5c', 'D5d'): row(d, 285, 'すり替わった（場所が分からない）', '予備 2つ')
    if key in ('D5c', 'D5d'):
        bar(d, 410, pairs=(key == 'D5d'))
        if key == 'D5c': d.text((640, 505), '予備 17個 → 直せる箱 8個', font=F(40), fill=INK, anchor='mm')
    robot(im)
    im.convert('RGB').save(os.path.join(HERE, 'sb', key + '.png'))
for k in ('D5a', 'D5b', 'D5c', 'D5d'): make(k)
print('ok')
