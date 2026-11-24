# 17本目（カード）：3D に貼る絵。数字のタイル・カードの表（数字はカードの物なので書く）・スマホの画面・レジの画面
#   決まり：番号は本物にならない短い 8 けた（3 5 2 8 0 4 7 6）。打ちまちがえは 7 つ目（4 → 5）。計算のやり方は描かない
# python3 make_tex17.py <出力フォルダ> <フォントの親フォルダ>
import os, sys
from PIL import Image, ImageDraw, ImageFont
OUT, FD = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons17 import icon
NAVY = (24, 38, 74); WHITE = (255, 255, 255); GREY = (200, 206, 214); RED = (226, 58, 48); ORANGE = (255, 138, 31)
GREEN = (52, 178, 102); BLUE = (52, 120, 230); TEAL = (47, 217, 200)
NUM = "35280471"; WRONG = "35280481"      # v1 のコメント「計算で決まる数字」：かんたんな決まり（前の 7 けたを足して、ちょうど 10 のまとまりになるように最後を決める）に合わせた。3+5+2+8+0+4+7=29 → 1。まちがえた番号は 3+5+2+8+0+4+8=30 → 0 のはずが 1。別の会社 4+9+2+8+0+4+7=34 → 6      # 7 つ目を打ちまちがえる（となりのキー。v1 の点検：前の 5 は 7 のとなりでなかった。キーは上 1〜5・下 6〜0 なので 8）
OTHER = "49280476"                         # 11-06 の別の会社のカード（はじめの 2 けただけちがう）
SS = 2
F = lambda n, w="900Black": ImageFont.truetype("%s/%s/NotoSansJP_%s.ttf" % (FD, w, w), n)


def tile(ch):
    """数字のタイルの面（白い地に黒い大きな数字）"""
    im = Image.new("RGB", (256, 256), WHITE); d = ImageDraw.Draw(im)
    d.text((128, 136), ch, font=F(200), fill=NAVY, anchor="mm")
    im.save(os.path.join(OUT, "tile_%s.png" % ch))


def card(name, base):
    """カードの表（架空の柄：地の色に、まるロボの顔の印と、番号の小さな数字。会社の名前・ロゴは描かない）"""
    W_, H_ = 856, 540
    im = Image.new("RGB", (W_ * SS, H_ * SS), base); d = ImageDraw.Draw(im)
    S = lambda *v: tuple(int(x * SS) for x in v)
    for k in range(12):       # 斜めのうすい帯
        d.polygon([S(-200 + k * 110, H_), S(-60 + k * 110, H_), S(200 + k * 110, 0), S(60 + k * 110, 0)], fill=tuple(min(255, c + 14) for c in base) if k % 2 else base)
    d.rounded_rectangle(S(70, 150, 190, 240), radius=14 * SS, fill=(222, 190, 96))          # 金色の四角（IC の形だけ）
    icon(d, "face", 720 * SS, 140 * SS, 52 * SS, NAVY)
    d.text(S(W_ / 2, 360), "  ".join(NUM[i:i + 2] for i in range(0, 8, 2)), font=F(76 * SS, "700Bold"), fill=WHITE, anchor="mm")
    im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


def phone(name, kind):
    """スマホの画面（縦 420×900）。字は書かない（字は 2D の札で重ねる）"""
    W_, H_ = 420, 900
    im = Image.new("RGB", (W_ * SS, H_ * SS), (150, 196, 230)); d = ImageDraw.Draw(im)
    S = lambda *v: tuple(int(x * SS) for x in v)
    for i in range(4):
        for j in range(4):
            x = 40 + j * 92; y = 330 + i * 120
            d.rounded_rectangle(S(x, y, x + 64, y + 64), radius=16 * SS, fill=[(255, 255, 255), (255, 214, 120), (130, 210, 170), (240, 140, 120)][(i + j) % 4])
    if kind == "notice":      # 上から知らせの帯：カードの絵と買い物ぶくろの絵、灰色の線
        d.rounded_rectangle(S(20, 60, W_ - 20, 230), radius=26 * SS, fill=(250, 251, 253))
        d.rounded_rectangle(S(45, 105, 135, 160), radius=8 * SS, fill=BLUE)
        icon(d, "bag", 95 * SS, 195 * SS, 22 * SS, ORANGE)
        for k, ww in enumerate((200, 230, 150)):
            d.rounded_rectangle(S(160, 100 + k * 32, 160 + ww, 116 + k * 32), radius=6 * SS, fill=GREY)
    im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


def register(name, digits, state="typing", bad=None):
    """レジの画面（横 800×300）：8 つのます。digits＝入った数字。state：typing／wrong（赤）／ok（緑）／nocheck（最後のますが灰色）。bad＝赤いますの番号"""
    W_, H_ = 800, 300
    bg = {"typing": (236, 242, 248), "wrong": (253, 226, 224), "ok": (220, 244, 228), "nocheck": (236, 242, 248)}[state]
    im = Image.new("RGB", (W_ * SS, H_ * SS), bg); d = ImageDraw.Draw(im)
    S = lambda *v: tuple(int(x * SS) for x in v)
    for k in range(8):
        x = 74 + k * 84; y = 86      # v1 のコメント「お店のモニターから数字はみ出てる」：ますが画面の左右ぎりぎりだった → 小さくして余白を取る
        col = WHITE
        if bad is not None and k == bad: col = (255, 150, 140)      # v1 の点検：うすい桃色で、赤に見えなかった
        line = ORANGE if k == 7 and state != "nocheck" else (NAVY if state != "nocheck" or k < 7 else GREY)
        if state == "nocheck" and k == 7: col = (210, 214, 220)
        if state == "wrong" and k == 7: line = RED
        if state == "ok": line = GREEN
        if bad is not None and k == bad and state != "ok": line = RED
        d.rounded_rectangle(S(x, y, x + 72, y + 108), radius=12 * SS, fill=col, outline=line, width=6 * SS)
        if k < len(digits): d.text(S(x + 36, y + 58), digits[k], font=F(76 * SS, "700Bold"), fill=NAVY, anchor="mm")
    if state == "ok": d.ellipse(S(W_ / 2 - 26, 222, W_ / 2 + 26, 274), fill=GREEN)
    if state == "wrong": d.ellipse(S(W_ / 2 - 26, 222, W_ / 2 + 26, 274), fill=RED)
    im.resize((W_, H_), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))


def key_face(ch):
    im = Image.new("RGB", (160, 160), (248, 248, 250)); d = ImageDraw.Draw(im)
    d.text((80, 86), ch, font=F(118, "700Bold"), fill=NAVY, anchor="mm"); im.save(os.path.join(OUT, "key_%s.png" % ch))


for c in "0123456789": tile(c); key_face(c)
card("card_blue", (52, 102, 196)); card("card_purple", (126, 84, 196))
phone("ph_home", "home"); phone("ph_notice", "notice")
for n in range(0, 9): register("reg_%d" % n, NUM[:n])
# v1 の点検：まちがえたますを画面で赤くすると、レジがどのけたをまちがえたか分かっているように見える（本当は検算が合わないことしか分からない）
#   → 画面は赤くしない。押しまちがえたキーは 2D の赤い輪で示す（overlays.py）。最後の検算のますだけ赤
for n in range(7, 9): register("reg_w%d" % n, WRONG[:n])
register("reg_wrong", WRONG, "wrong")
register("reg_ok", NUM, "ok"); register("reg_nocheck", WRONG[:7], "nocheck")
print("tex done", len(os.listdir(OUT)))
