# 会話と広告の回：言っている内容の「差し込みの絵」（2D・1280×720）。v4 のコメント「まるロボをただ映すのではなく、その内容の場面を差し込んで」
#   python3 inserts_2d.py <出力フォルダ> <フォント.ttf>   → ins_<名前>.png
#   字は札だけ（字幕と同じ文は書かない）。字は 46 以上。下の字幕の帯（下から 196px）には大事な物を置かない
import os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT, FONT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
W, H = 1280, 720
NAVY = (20, 36, 72); BG = (236, 242, 246); WHITE = (255, 255, 255)
HARU = (62, 124, 177); SORA = (229, 140, 90); SKIN = (244, 210, 181); SKIN2 = (233, 190, 154)
ORANGE = (242, 153, 58); RED = (229, 72, 77); TEAL = (42, 157, 143); YEL = (255, 214, 48); GRAY = (150, 160, 172)
F = lambda px: ImageFont.truetype(FONT, px)
BAND = H - 196


def canvas(bg=BG):
    im = Image.new("RGB", (W, H), bg); return im, ImageDraw.Draw(im)


def label(d, text, cx, cy, px=48, fg=NAVY, bg=WHITE, edge=NAVY):
    f = F(px); b = d.textbbox((0, 0), text, font=f); w, h = b[2] - b[0], b[3] - b[1]
    d.rounded_rectangle([cx - w / 2 - 22, cy - h / 2 - 16, cx + w / 2 + 22, cy + h / 2 + 16], 16, fill=bg, outline=edge, width=4)
    d.text((cx - w / 2 - b[0], cy - h / 2 - b[1]), text, font=f, fill=fg)


def person(d, x, y, s=1.0, shirt=HARU, skin=SKIN, cap=False, scarf=False, face=0):
    """座った人の上半身（点の目・口なし）。face：-1 左向き・1 右向き"""
    d.rounded_rectangle([x - 70 * s, y, x + 70 * s, y + 170 * s], int(50 * s), fill=shirt)
    d.ellipse([x - 52 * s, y - 112 * s, x + 52 * s, y - 8 * s], fill=skin)
    ex = 16 * s * face
    for k in (-1, 1): d.ellipse([x + ex + k * 18 * s - 6 * s, y - 66 * s, x + ex + k * 18 * s + 6 * s, y - 54 * s], fill=NAVY)
    if cap: d.chord([x - 56 * s, y - 128 * s, x + 56 * s, y - 40 * s], 180, 360, fill=(227, 174, 58))
    if scarf: d.rounded_rectangle([x - 54 * s, y - 6 * s, x + 54 * s, y + 22 * s], int(12 * s), fill=TEAL)


def bubble(d, x0, y0, x1, y1, tail, fill=WHITE):
    d.rounded_rectangle([x0, y0, x1, y1], 30, fill=fill, outline=NAVY, width=5)
    cx = (x0 + x1) / 2
    d.polygon([(cx - 22, y1 - 3), (cx + 22, y1 - 3), tail], fill=fill, outline=NAVY)
    d.line([(cx - 20, y1 - 3), (cx + 20, y1 - 3)], fill=fill, width=6)


def tent(d, cx, cy, s=1.0):
    d.polygon([(cx - 60 * s, cy + 45 * s), (cx, cy - 55 * s), (cx + 60 * s, cy + 45 * s)], fill=(233, 105, 44))
    d.polygon([(cx - 15 * s, cy + 45 * s), (cx, cy + 5 * s), (cx + 15 * s, cy + 45 * s)], fill=(122, 46, 18))


def phone(d, x, y, w, h, screen=WHITE):
    d.rounded_rectangle([x, y, x + w, y + h], int(w * 0.12), fill=(34, 38, 43), outline=NAVY, width=4)
    d.rounded_rectangle([x + w * 0.07, y + h * 0.06, x + w * 0.93, y + h * 0.94], int(w * 0.06), fill=screen)
    return (x + w * 0.07, y + h * 0.06, x + w * 0.93, y + h * 0.94)


def mic(d, cx, cy, s=1.0, col=RED):
    d.rounded_rectangle([cx - 14 * s, cy - 30 * s, cx + 14 * s, cy + 10 * s], int(14 * s), fill=col)
    d.arc([cx - 24 * s, cy - 18 * s, cx + 24 * s, cy + 22 * s], 0, 180, fill=col, width=int(6 * s))
    d.line([(cx, cy + 22 * s), (cx, cy + 34 * s)], fill=col, width=int(6 * s))


def waves(d, cx, cy, r0=30, n=3, col=NAVY, a0=-40, a1=40):
    for k in range(n):
        r = r0 + k * 22; d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=col, width=7)


def arrow(d, a, b, col=ORANGE, w=22):
    (x0, y0), (x1, y1) = a, b; ang = math.atan2(y1 - y0, x1 - x0); hl = w * 2.2
    xe, ye = x1 - hl * 0.8 * math.cos(ang), y1 - hl * 0.8 * math.sin(ang)
    d.line([(x0, y0), (xe, ye)], fill=col, width=w)
    d.polygon([(x1, y1), (x1 - hl * math.cos(ang) + hl * 0.7 * math.sin(ang), y1 - hl * math.sin(ang) - hl * 0.7 * math.cos(ang)),
               (x1 - hl * math.cos(ang) - hl * 0.7 * math.sin(ang), y1 - hl * math.sin(ang) + hl * 0.7 * math.cos(ang))], fill=col)


def wifi(d, cx, cy, s=1.0, col=NAVY):
    for r in (95, 65, 35): d.arc([cx - r * s, cy - r * s, cx + r * s, cy + r * s], 225, 315, fill=col, width=int(12 * s))
    d.ellipse([cx - 10 * s, cy - 10 * s, cx + 10 * s, cy + 10 * s], fill=col)


def house(d, x, y, s=1.0, col=(240, 200, 160)):
    d.polygon([(x - 120 * s, y), (x, y - 100 * s), (x + 120 * s, y)], fill=(196, 84, 60))
    d.rectangle([x - 95 * s, y, x + 95 * s, y + 140 * s], fill=col, outline=NAVY, width=4)
    d.rectangle([x - 25 * s, y + 60 * s, x + 25 * s, y + 140 * s], fill=(120, 80, 50))


def shop(d, x, y, s=1.0):
    d.rectangle([x - 110 * s, y, x + 110 * s, y + 140 * s], fill=(250, 246, 236), outline=NAVY, width=4)
    for k in range(6): d.rectangle([x - 110 * s + k * 220 * s / 6, y - 40 * s, x - 110 * s + (k + 1) * 220 * s / 6, y], fill=(TEAL if k % 2 else WHITE), outline=NAVY)
    d.rectangle([x - 80 * s, y + 40 * s, x + 80 * s, y + 100 * s], fill=(200, 230, 245), outline=NAVY, width=3)


def building(d, x, y, w, h, col=(210, 216, 226), win=(120, 170, 220)):
    d.rectangle([x, y, x + w, y + h], fill=col, outline=NAVY, width=4)
    for r in range(int(h // 60)):
        for c in range(int(w // 60)):
            d.rectangle([x + 18 + c * 60, y + 18 + r * 60, x + 48 + c * 60, y + 48 + r * 60], fill=win)


def save(im, name): im.save(os.path.join(OUT, "ins_%s.png" % name))


# ---------------- 家での会話（09-01b）：家の中で話す二人。テーブルのスマホのマイクが赤く光り、会話の波を吸いこむ（もし、こっそり聞くアプリがあったら）
im, d = canvas((250, 240, 225))
d.rectangle([0, 470, W, H], fill=(214, 186, 150)); d.rectangle([80, 60, 420, 300], fill=(190, 225, 245), outline=NAVY, width=6)
d.line([(250, 60), (250, 300)], fill=NAVY, width=5); d.line([(80, 180), (420, 180)], fill=NAVY, width=5)
person(d, 430, 330, 1.2, HARU, SKIN, face=1); person(d, 900, 330, 1.2, SORA, SKIN2, scarf=True, face=-1)
d.rounded_rectangle([470, 470, 860, 520], 12, fill=(160, 110, 70))
phone(d, 615, 400, 100, 70, (60, 70, 90)); mic(d, 665, 435, 0.9)
for cx, cy, a0, a1 in ((560, 250, -30, 30), (770, 250, 150, 210)): waves(d, cx, cy, 30, 3, NAVY, a0, a1)
for k in range(3): d.ellipse([665 - 28 - k * 26, 435 - 28 - k * 26, 665 + 28 + k * 26, 435 + 28 + k * 26], outline=RED, width=5)
label(d, "家での会話", 640, 90, 54)
save(im, "home_talk")

# ---------------- 電話の声（09-01b）：スマホを耳に当てて話す人。スマホのマイクが赤く光る
im, d = canvas((232, 238, 250))
person(d, 560, 330, 1.4, HARU, SKIN, face=1)
d.rounded_rectangle([650, 150, 720, 300], 16, fill=(34, 38, 43), outline=NAVY, width=4); mic(d, 685, 285, 0.7)
waves(d, 760, 230, 40, 3, NAVY, -45, 45)
for k in range(3): d.ellipse([685 - 30 - k * 24, 285 - 30 - k * 24, 685 + 30 + k * 24, 285 + 30 + k * 24], outline=RED, width=5)
label(d, "電話の声", 640, 90, 54)
save(im, "phone_call")

# ---------------- 同じ Wi-Fi（10-08）：家とお店。それぞれの Wi-Fi に、二人のスマホがつながっている
im, d = canvas()
house(d, 330, 260, 1.3); shop(d, 950, 260, 1.3)
for cx in (330, 950):
    wifi(d, cx, 200, 0.8, TEAL)
    for dx, col in ((-70, HARU), (70, SORA)):
        x0 = cx + dx - 38; phone(d, x0, 470, 76, 120, WHITE); d.rectangle([x0 + 14, 492, x0 + 62, 500], fill=col)
        d.line([(cx, 210), (cx + dx, 466)], fill=TEAL, width=5)
label(d, "家", 150, 140, 50); label(d, "お店", 1170, 140, 50)
save(im, "wifi_place")

# ---------------- 手がかりが広告の会社へ（10-09）：スマホ → アプリ・サイト → 広告の会社
im, d = canvas()
phone(d, 90, 170, 190, 330, WHITE)
for k, col in enumerate(((95, 170, 210), ORANGE, (140, 100, 200))): d.rounded_rectangle([120, 210 + k * 90, 250, 280 + k * 90], 14, fill=col)
for k, (x, y, col) in enumerate(((470, 190, (110, 140, 180)), (470, 330, (90, 160, 150)), (600, 260, (160, 130, 190)))):
    d.rounded_rectangle([x, y, x + 110, y + 110], 24, fill=col, outline=NAVY, width=4)
d.rounded_rectangle([450, 470, 720, 560], 14, fill=WHITE, outline=NAVY, width=4); d.rectangle([450, 470, 720, 495], fill=(200, 210, 222))
for k in range(3): d.ellipse([462 + k * 22, 476, 476 + k * 22, 490], fill=(RED, YEL, TEAL)[k])
building(d, 930, 170, 240, 360)
arrow(d, (300, 340), (440, 340)); arrow(d, (740, 340), (900, 340))
label(d, "アプリ・サイト", 585, 110, 48); label(d, "広告の会社", 1050, 110, 48)
save(im, "to_company")

# ---------------- 「許可」（10-10）：アプリを入れたときの「許可しますか？」の画面
im, d = canvas((30, 42, 60))
x0, y0, x1, y1 = phone(d, 430, 30, 420, 500, (244, 246, 248))
d.rounded_rectangle([x0 + 30, y0 + 90, x1 - 30, y1 - 70], 26, fill=WHITE, outline=(200, 205, 212), width=3)
d.ellipse([x0 + 150, y0 + 115, x0 + 240, y0 + 205], fill=(95, 170, 210))
d.polygon([(x0 + 195, y0 + 190), (x0 + 172, y0 + 150), (x0 + 218, y0 + 150)], fill=WHITE); d.ellipse([x0 + 180, y0 + 132, x0 + 210, y0 + 162], fill=WHITE)
for k in range(3): d.rounded_rectangle([x0 + 60, y0 + 230 + k * 34, x1 - 60 - (60 if k == 2 else 0), y0 + 248 + k * 34], 8, fill=(205, 212, 220))
d.rounded_rectangle([x0 + 50, y1 - 150, x0 + 175, y1 - 95], 14, fill=(225, 230, 236)); d.rounded_rectangle([x1 - 175, y1 - 150, x1 - 50, y1 - 95], 14, fill=TEAL)
# v5「まるの位置ずれてる」(7:42)：字はボタンのまん中に、丸はボタンをかこむ形に（中心をボタンにそろえる）
_bx0, _by0, _bx1, _by1 = x1 - 175, y1 - 150, x1 - 50, y1 - 95; _cx, _cy = (_bx0 + _bx1) / 2, (_by0 + _by1) / 2
f = F(40); _bb = d.textbbox((0, 0), "許可", font=f); d.text((_cx - (_bb[0] + _bb[2]) / 2, _cy - (_bb[1] + _bb[3]) / 2), "許可", font=f, fill=WHITE)
d.ellipse([_cx - 95, _cy - 52, _cx + 95, _cy + 52], outline=YEL, width=8)
save(im, "permission")

# ---------------- 役所が調べる（18-00・18-01）：役所の建物から、虫めがねが会社を調べる
im, d = canvas((232, 238, 246))
d.polygon([(130, 230), (330, 120), (530, 230)], fill=(210, 214, 220), outline=NAVY)
d.rectangle([150, 230, 510, 260], fill=(225, 228, 233), outline=NAVY, width=4)
for k in range(5): d.rectangle([170 + k * 70, 270, 200 + k * 70, 470], fill=(245, 246, 248), outline=NAVY, width=3)
d.rectangle([140, 470, 520, 500], fill=(210, 214, 220), outline=NAVY, width=4)
building(d, 860, 200, 240, 300, (220, 210, 230), (170, 150, 200))
d.ellipse([760, 230, 1000, 470], outline=(242, 193, 78), width=18); d.line([(960, 430), (1060, 530)], fill=(242, 193, 78), width=26)
arrow(d, (540, 360), (740, 360), NAVY, 16)
label(d, "役所", 330, 70, 54); label(d, "会社", 980, 120, 50)
save(im, "government")

# ---------------- 鏡に映る私たち（05-04b）：紫のふちの鏡に、見ている私たち（人の形）が映る
im, d = canvas((24, 22, 40))
d.ellipse([400, 40, 880, 520], fill=(140, 100, 200)); d.ellipse([430, 70, 850, 490], fill=(205, 220, 236))
for k, (x, col) in enumerate(((560, HARU), (720, SORA), (640, (90, 90, 110)))):
    s = 0.9 if k < 2 else 1.05; y = 330 if k < 2 else 360
    d.ellipse([x - 48 * s, y - 120 * s, x + 48 * s, y - 24 * s], fill=(180, 190, 205) if k == 2 else SKIN)
    d.rounded_rectangle([x - 70 * s, y - 20 * s, x + 70 * s, y + 140 * s], int(50 * s), fill=col)
label(d, "私たち", 640, 600 - 80, 54, WHITE, (140, 100, 200), WHITE)
save(im, "mirror_us")

# ---------------- ハルさんの手がかりの札（12-05）：3 枚の札（いた場所・見たページ・一緒にいた人）を、印と絵で
im, d = canvas((30, 42, 60))
label(d, "ハルさんの手がかり", 640, 80, 54, NAVY, WHITE, ORANGE)
cards = [("いた場所", "drop"), ("見たページ", "page"), ("一緒にいた人", "two")]
for k, (t, kind) in enumerate(cards):
    x = 70 + k * 390; d.rounded_rectangle([x, 150, x + 360, 500], 24, fill=(255, 239, 214), outline=ORANGE, width=8)
    cx, cy = x + 180, 300
    if kind == "drop":   # 電車と、場所の印
        d.rounded_rectangle([cx - 120, cy - 30, cx + 120, cy + 50], 20, fill=(160, 200, 225), outline=NAVY, width=4)
        for q in range(4): d.rectangle([cx - 100 + q * 52, cy - 15, cx - 62 + q * 52, cy + 15], fill=WHITE)
        d.polygon([(cx, cy - 40), (cx - 30, cy - 100), (cx + 30, cy - 100)], fill=RED); d.ellipse([cx - 32, cy - 135, cx + 32, cy - 72], fill=RED); d.ellipse([cx - 12, cy - 115, cx + 12, cy - 92], fill=WHITE)
    elif kind == "page":  # ニュースのページ
        phone(d, cx - 70, cy - 110, 140, 230, WHITE)
        for q in range(5): d.rectangle([cx - 48, cy - 80 + q * 34, cx + 48 - (30 if q % 2 else 0), cy - 66 + q * 34], fill=(150, 160, 172))
    else:                 # ソラさん
        person(d, cx, cy - 10, 0.7, SORA, SKIN2, scarf=True)
    label(d, t, cx, 450, 46, NAVY, WHITE, ORANGE)
save(im, "clues")

# ---------------- 窓の外の紅葉（14-01b）：電車の窓の外に、赤と黄の木
im, d = canvas((210, 200, 190))
d.rounded_rectangle([140, 60, 1140, 500], 30, fill=(150, 200, 235), outline=(90, 90, 100), width=18)
d.rectangle([158, 380, 1122, 482], fill=(170, 150, 110))
import random
random.seed(3)
for k in range(9):
    x = 210 + k * 112 + random.randint(-20, 20); y = 330 + random.randint(-20, 20); r = 70 + random.randint(-10, 15)
    d.rectangle([x - 8, y, x + 8, y + 80], fill=(110, 70, 40))
    d.ellipse([x - r, y - r, x + r, y + r * 0.6], fill=((217, 71, 43), (242, 153, 58), (230, 190, 60))[k % 3])
for k in range(10):
    x, y = random.randint(200, 1100), random.randint(100, 360); d.ellipse([x - 9, y - 6, x + 9, y + 6], fill=(217, 71, 43))
d.line([(640, 60), (640, 500)], fill=(90, 90, 100), width=14)
save(im, "autumn")


# ---------------- 記憶の場面（S16、16-01〜16-06）。広告のカードをたくさん並べて、どれが記憶に残るかを見せる
def ad_card(d, x, y, kind, dim=False, s=1.0):
    col = [(255, 255, 255), (238, 238, 238)][dim]; d.rounded_rectangle([x, y, x + 120 * s, y + 84 * s], 12, fill=col, outline=(GRAY if dim else NAVY), width=3)
    c = [(233, 105, 44), (95, 170, 210), (120, 180, 110), (200, 120, 180), (240, 190, 70)][kind % 5]
    if dim: c = tuple(int(v * 0.35 + 200 * 0.65) for v in c)
    if kind == 0: tent(d, x + 60 * s, y + 46 * s, 0.45 * s) if not dim else d.polygon([(x + 33 * s, y + 66 * s), (x + 60 * s, y + 22 * s), (x + 87 * s, y + 66 * s)], fill=c)
    else: d.rounded_rectangle([x + 22 * s, y + 18 * s, x + 98 * s, y + 66 * s], 10, fill=c)


GRID = [(x, y) for y in (40, 145, 250, 355) for x in range(60, 1220, 150)]
for name, mode in (("ads_many", 0), ("ads_forget", 1), ("ad_notice", 2)):
    im, d = canvas()
    for k, (x, y) in enumerate(GRID):
        if mode == 2 and k in (11, 12, 19, 20): continue
        ad_card(d, x, y, (k * 3) % 5 if k != 12 else 0, dim=(mode >= 1))
    if mode == 2:   # 話したばかりのテントの広告だけ、大きく光る
        d.ellipse([440, 130, 840, 430], fill=(255, 244, 200)); ad_card(d, 520, 196, 0, False, 2.0)
        for a in range(0, 360, 30):
            r0, r1 = 210, 260; x0 = 640 + r0 * math.cos(math.radians(a)); y0 = 274 + r0 * 0.75 * math.sin(math.radians(a))
            d.line([(x0, y0), (640 + r1 * math.cos(math.radians(a)), 274 + r1 * 0.75 * math.sin(math.radians(a)))], fill=YEL, width=10)
        label(d, "あっ！", 960, 120, 64, NAVY, YEL, NAVY)
    save(im, name)

im, d = canvas()   # 16-04：テントの広告が、頭の中の記憶の箱に強く入る
d.ellipse([700, 70, 1100, 470], fill=(225, 214, 245)); d.ellipse([760, 470, 1040, 560], fill=(225, 214, 245))
d.rounded_rectangle([800, 230, 1000, 380], 20, fill=(140, 100, 200), outline=NAVY, width=5)
ad_card(d, 830, 250, 0, False, 1.15)
arrow(d, (360, 300), (760, 300), ORANGE, 26); ad_card(d, 140, 230, 0, False, 1.6)
label(d, "聞かれてた！", 900, 120, 52, NAVY, YEL, NAVY)
save(im, "memory_strong")

im, d = canvas()   # 16-05：話したのに広告が出なかった物（くつ・本・ラーメン）は、記憶に残らず薄れていく
for k, (x, txt) in enumerate(((240, "shoe"), (640, "book"), (1040, "ramen"))):
    bubble(d, x - 150, 90, x + 150, 270, (x - 40, 330), (245, 245, 245))
    c = (175, 180, 190)
    if txt == "shoe": d.rounded_rectangle([x - 80, 160, x + 70, 215], 22, fill=c); d.rectangle([x - 80, 135, x - 30, 200], fill=c)
    elif txt == "book": d.rectangle([x - 70, 135, x + 70, 230], fill=c); d.line([(x, 135), (x, 230)], fill=(245, 245, 245), width=6)
    else: d.pieslice([x - 75, 120, x + 75, 260], 0, 180, fill=c)
    phone(d, x - 55, 360, 110, 150, (238, 238, 238)); d.text((x - 16, 395), "？", font=F(64), fill=(170, 175, 185))
fog = Image.new("RGB", (W, H), (236, 242, 246)); im = Image.blend(im, fog, 0.25)
save(im, "miss_forgot")

im, d = canvas()   # 16-06：当たり（1 つ）を大きく数え、外れ（たくさん）は数えない
d.rounded_rectangle([90, 120, 520, 520], 30, fill=(255, 248, 225), outline=ORANGE, width=8)
ad_card(d, 200, 230, 0, False, 1.8); d.text((420, 150), "✓", font=F(110), fill=(93, 187, 99))
d.rounded_rectangle([620, 120, 1190, 520], 30, fill=(240, 240, 240), outline=GRAY, width=6)
for k in range(12):
    x = 650 + (k % 4) * 132; y = 150 + (k // 4) * 120
    d.rounded_rectangle([x, y, x + 110, y + 80], 10, fill=(230, 230, 230), outline=(200, 200, 200), width=2)
    d.line([(x + 30, y + 20), (x + 80, y + 60)], fill=(200, 200, 200), width=6); d.line([(x + 80, y + 20), (x + 30, y + 60)], fill=(200, 200, 200), width=6)
save(im, "tally")
print("ok", sorted(f for f in os.listdir(OUT) if f.startswith("ins_")))

# ---------------- 電車の無料 Wi-Fi（13-05）と「一緒にいた人」（13-05b）
for name in ("wifi_train", "together"):
    im, d = canvas((225, 232, 240))
    d.rounded_rectangle([60, 140, 1220, 470], 40, fill=(245, 245, 240), outline=NAVY, width=6)
    for k in range(5): d.rounded_rectangle([110 + k * 220, 180, 260 + k * 220, 280], 14, fill=(170, 210, 235), outline=NAVY, width=3)
    d.rectangle([60, 400, 1220, 470], fill=(62, 124, 177))
    d.rounded_rectangle([590, 150, 690, 190], 10, fill=WHITE, outline=NAVY, width=4); wifi(d, 640, 150, 0.7, TEAL)
    for x, col in ((470, HARU), (810, SORA)):
        phone(d, x - 45, 300, 90, 140, WHITE); d.rectangle([x - 28, 318, x + 28, 328], fill=col)
        d.line([(640, 190), (x, 296)], fill=TEAL, width=6)
    label(d, "ハルさん", 470, 520 - 30, 46, NAVY, WHITE, HARU); label(d, "ソラさん", 810, 520 - 30, 46, NAVY, WHITE, SORA)
    if name == "wifi_train":
        label(d, "電車の無料Wi-Fi", 640, 70, 52, NAVY, WHITE, TEAL)
    else:
        d.rounded_rectangle([380, 280, 900, 460], 30, outline=ORANGE, width=10)
        label(d, "一緒にいた人", 640, 70, 52, NAVY, (255, 239, 214), ORANGE)
    save(im, name)
print("ok2")
