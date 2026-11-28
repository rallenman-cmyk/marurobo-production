# 19本目（メッセージの旅）：3D に貼る絵。スマホの画面（字なし）・ネジのスタンプ・まるロボの写真・基板の模様
#   決まり：3D の中に字を書かない。アプリの本物の画面の見た目をまねしない（色・形は架空）。既読の印は目の形の絵
# python3 make_tex19.py <出力フォルダ>
import os, sys, math, random
from PIL import Image, ImageDraw
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons17 import icon, icon5
NAVY = (24, 38, 74); WHITE = (255, 255, 255); TEAL = (47, 217, 200); SKY = (214, 236, 250); GREY = (196, 204, 214)
SS = 2
# 画面の上の決まった場所（0〜1。左上が 0,0）。scenes19.py の SEND・STAMP の位置と同じ
SEND = (0.86, 0.935); STAMP_BTN = (0.14, 0.935); STAMP_PICK = (0.22, 0.70); PHOTO_PICK = (0.50, 0.62)


def screw(d, cx, cy, r):
    """ネジ（横から）：丸い頭と、ななめの線のあるじく"""
    d.rounded_rectangle((cx - r * 0.9, cy - r * 1.05, cx + r * 0.9, cy - r * 0.55), radius=int(r * 0.22), fill=(150, 160, 172), outline=(90, 98, 110), width=max(2, int(r * 0.06)))
    d.rectangle((cx - r * 0.08, cy - r * 1.05, cx + r * 0.08, cy - r * 0.75), fill=(90, 98, 110))
    d.polygon([(cx - r * 0.38, cy - r * 0.55), (cx + r * 0.38, cy - r * 0.55), (cx + r * 0.30, cy + r * 0.95), (cx, cy + r * 1.2), (cx - r * 0.30, cy + r * 0.95)], fill=(176, 184, 196), outline=(90, 98, 110))
    for k in range(6):
        y = cy - r * 0.45 + k * r * 0.24
        d.line((cx - r * 0.36, y + r * 0.12, cx + r * 0.36, y - r * 0.02), fill=(100, 108, 120), width=max(2, int(r * 0.07)))


def maru_face(d, cx, cy, r):
    """まるロボの顔（白い球・青緑の目・アンテナ）"""
    d.line((cx + r * 0.2, cy - r * 0.95, cx + r * 0.45, cy - r * 1.45), fill=(120, 128, 140), width=max(2, int(r * 0.08)))
    d.ellipse((cx + r * 0.33, cy - r * 1.6, cx + r * 0.6, cy - r * 1.33), fill=TEAL)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 250, 252), outline=(190, 198, 208), width=max(2, int(r * 0.05)))
    d.ellipse((cx - r * 0.42, cy - r * 0.42, cx + r * 0.42, cy + r * 0.42), fill=(30, 40, 52))
    d.ellipse((cx - r * 0.28, cy - r * 0.28, cx + r * 0.28, cy + r * 0.28), fill=TEAL)
    d.ellipse((cx - r * 0.12, cy - r * 0.2, cx + r * 0.02, cy - r * 0.06), fill=WHITE)


def stamp_img():
    im = Image.new("RGBA", (512 * SS, 512 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20 * SS, 20 * SS, 492 * SS, 492 * SS), radius=80 * SS, fill=(255, 246, 214), outline=(240, 190, 80), width=10 * SS)
    screw(d, 256 * SS, 250 * SS, 170 * SS)
    im.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "stamp_screw.png"))


def photo_img():
    im = Image.new("RGB", (512 * SS, 512 * SS), (178, 218, 244)); d = ImageDraw.Draw(im)
    d.rectangle((0, 380 * SS, 512 * SS, 512 * SS), fill=(150, 200, 140))
    d.ellipse((380 * SS, 40 * SS, 470 * SS, 130 * SS), fill=(255, 220, 110))
    maru_face(d, 250 * SS, 270 * SS, 150 * SS)
    im.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "photo_maru.png"))


def screen(name, kind):
    """スマホの画面（縦 512×1024）。字は書かない。上の帯（相手の顔の丸）・話の所・下の帯（スタンプのボタン・送信の矢印）"""
    W_, H_ = 512, 1024
    S = lambda *v: tuple(int(x * SS) for x in v)
    im = Image.new("RGB", (W_ * SS, H_ * SS), (236, 244, 250)); d = ImageDraw.Draw(im)
    d.rectangle(S(0, 0, W_, 120), fill=(70, 120, 200))                          # 上の帯（架空の色）
    d.ellipse(S(28, 26, 96, 94), fill=(255, 214, 170)); d.ellipse(S(44, 40, 80, 76), fill=(120, 80, 60))   # 相手（友だち）の顔の丸
    d.rounded_rectangle(S(112, 48, 300, 72), radius=12 * SS, fill=(150, 185, 230))   # 名前の所（字なし。線だけ）
    d.rectangle(S(0, 900, W_, H_), fill=(250, 252, 255)); d.line(S(0, 900, W_, 900), fill=GREY, width=2 * SS)
    # 下の帯：スタンプのボタン（にこにこの丸）・入力の所（線）・送信の矢印
    cx, cy = STAMP_BTN[0] * W_, STAMP_BTN[1] * H_
    d.ellipse(S(cx - 34, cy - 34, cx + 34, cy + 34), fill=(255, 205, 80)); d.arc(S(cx - 18, cy - 10, cx + 18, cy + 20), 20, 160, fill=NAVY, width=5 * SS)
    d.ellipse(S(cx - 14, cy - 14, cx - 6, cy - 6), fill=NAVY); d.ellipse(S(cx + 6, cy - 14, cx + 14, cy - 6), fill=NAVY)
    d.rounded_rectangle(S(110, cy - 30, 380, cy + 30), radius=30 * SS, fill=(232, 238, 246))
    sx, sy = SEND[0] * W_, SEND[1] * H_
    d.ellipse(S(sx - 44, sy - 44, sx + 44, sy + 44), fill=TEAL if kind != "home" else (150, 210, 205))
    d.polygon(S(sx - 20, sy - 24, sx + 26, sy, sx - 20, sy + 24, sx - 10, sy), fill=WHITE)
    # 話の所：相手のこれまでの吹き出し（左・字なしの線）
    d.rounded_rectangle(S(24, 170, 330, 250), radius=30 * SS, fill=WHITE)
    for k in range(2): d.rounded_rectangle(S(50, 192 + k * 30, 290 - k * 80, 206 + k * 30), radius=7 * SS, fill=(205, 212, 222))
    if kind == "stamp":          # スタンプを選ぶ板（下の半分）。ネジに丸い光
        d.rectangle(S(0, 560, W_, 900), fill=(248, 240, 222))
        stamps = ["screw", "star", "flower", "cup", "sun", "apple"]
        for k, st in enumerate(stamps):
            x = 90 + (k % 3) * 166; y = 650 + (k // 3) * 150
            if st == "screw":
                d.ellipse(S(x - 66, y - 66, x + 66, y + 66), outline=TEAL, width=10 * SS)
                screw(d, x * SS, y * SS, 52 * SS)
            else:
                icon5(d, st, x * SS, y * SS, 44 * SS)
    if kind == "photo":          # 写真を選ぶ板（ます目の写真）。まるロボの写真に丸い光
        d.rectangle(S(0, 480, W_, 900), fill=(232, 236, 242))
        for k in range(6):
            x = 14 + (k % 3) * 166; y = 494 + (k // 3) * 200
            col = [(170, 200, 230), (200, 180, 150), (160, 200, 160), (220, 200, 170), (190, 190, 220), (210, 170, 170)][k]
            d.rectangle(S(x, y, x + 152, y + 186), fill=col)
            if k == 1:
                pi = Image.open(os.path.join(OUT, "photo_maru.png")).resize((152 * SS, 186 * SS)); im.paste(pi, S(x, y))
                d.rectangle(S(x - 5, y - 5, x + 157, y + 191), outline=TEAL, width=10 * SS)
    if kind in ("sent", "read"):  # 右に、送ったスタンプと写真
        screw(d, 380 * SS, 380 * SS, 70 * SS)
        pi = Image.open(os.path.join(OUT, "photo_maru.png")).resize((210 * SS, 210 * SS)); im.paste(pi, S(270, 500))
        d.rounded_rectangle(S(266, 496, 484, 714), radius=14 * SS, outline=WHITE, width=6 * SS)
        if kind == "read":        # 既読の印：小さな目の形（字なし）
            for (ex, ey) in ((228, 440), (228, 690)):
                d.ellipse(S(ex - 26, ey - 14, ex + 26, ey + 14), fill=WHITE, outline=(70, 120, 200), width=4 * SS)
                d.ellipse(S(ex - 9, ey - 9, ex + 9, ey + 9), fill=(70, 120, 200))
    im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


def pcb():
    """基板の模様（緑の地に、金色の細い線と丸い点）。上から見て、町の道のように"""
    N = 2048; random.seed(19)
    im = Image.new("RGB", (N, N), (22, 92, 60)); d = ImageDraw.Draw(im)
    for k in range(60):
        x, y = random.randint(0, N), random.randint(0, N)
        for _ in range(random.randint(2, 4)):
            if random.random() < 0.5: x2, y2 = x + random.choice((-1, 1)) * random.randint(80, 500), y
            else: x2, y2 = x, y + random.choice((-1, 1)) * random.randint(80, 500)
            d.line((x, y, x2, y2), fill=(196, 160, 70), width=random.choice((4, 6, 8)))
            x, y = x2, y2
        d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(214, 182, 96))
    for k in range(300):
        x, y = random.randint(0, N), random.randint(0, N)
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(200, 170, 90))
    im.save(os.path.join(OUT, "pcb.png"))


stamp_img(); photo_img()
for nm, kd in (("ph_home", "home"), ("ph_stamp", "stamp"), ("ph_photo", "photo"), ("ph_sent", "sent"), ("ph_read", "read")):
    screen(nm, kd)
pcb()
print("ok", sorted(os.listdir(OUT)))
