# スマホの曲の画面（主人公のスマホ・巨大スマホで同じ）を、細かく描き直す。曲の進み具合の帯を「データのまとまり」01〜05 に区切る
#   k=0：ふつうの画面（冒頭と同じ）  k=1：帯がまとまりに区切られ、番号が出る  k=2：01・02（もう届いて鳴った分）が光る
#   k=3：いま送っている 03 が明るく光る（窓の中の荷物 03 とつながる）
# 使い方: python3 ch03_screen.py OUT_DIR  → music_k0.png 〜 music_k3.png（1440×3100。元の music.png の4倍）
import sys, os
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens"); os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "av", "fonts", "japanese.ttc")
S = 4; W, H = 360 * S, 775 * S
BG = (18, 22, 30); TEAL = (60, 220, 200); GRAYBAR = (70, 78, 92); LIGHT = (232, 236, 240); MID = (120, 128, 138); CYAN = (150, 255, 245)
X0, X1, YB = 40, 320, 563                       # 帯の左右と高さ（元の画面の画素）
KNOB = 175; N = 5; GAP = 4


def font(px):
    try: return ImageFont.truetype(FONT, px * S)
    except Exception: return ImageFont.load_default()


def base():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rounded_rectangle([130 * S, 30 * S, 230 * S, 44 * S], radius=7 * S, fill=(40, 44, 52))           # 上の切り欠き
    art = Image.new("RGB", (280 * S, 280 * S)); ad = ImageDraw.Draw(art)
    for y in range(280 * S):                                                                          # 曲の画像：青緑 → 桃色
        u = y / (280 * S - 1); c = tuple(int(a + (b - a) * u) for a, b in zip((45, 172, 205), (232, 110, 160)))
        ad.line([(0, y), (280 * S, y)], fill=c)
    mask = Image.new("L", art.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, 280 * S - 1, 280 * S - 1], radius=22 * S, fill=255)
    im.paste(art, (40 * S, 120 * S), mask)
    d.ellipse([(180 - 70) * S, (260 - 70) * S, (180 + 70) * S, (260 + 70) * S], fill=(250, 240, 222))
    d.ellipse([(180 - 22) * S, (260 - 22) * S, (180 + 22) * S, (260 + 22) * S], fill=(30, 40, 60))
    d.rounded_rectangle([40 * S, 440 * S, 261 * S, 462 * S], radius=11 * S, fill=LIGHT)               # 曲名
    d.rounded_rectangle([40 * S, 478 * S, 191 * S, 494 * S], radius=8 * S, fill=MID)                  # 歌手
    d.polygon([(165 * S, 620 * S), (165 * S, 680 * S), (216 * S, 650 * S)], fill=LIGHT)               # 再生
    d.polygon([(96 * S, 635 * S), (96 * S, 665 * S), (70 * S, 650 * S)], fill=(150, 158, 170))        # 前
    d.polygon([(285 * S, 635 * S), (285 * S, 665 * S), (311 * S, 650 * S)], fill=(150, 158, 170))     # 次
    return im, d


def chunks(k, first=1, now_i=2):
    """k≥1：曲の画像のすぐ下に、データのまとまりの帯（番号入り）を出す。持つ手の親指で隠れない高さ
    first：帯のいちばん左の番号、now_i：いま送っているまとまりの位置（0 から。それより左は届いて鳴った分）"""
    im, d = base()
    d.rounded_rectangle([X0 * S, (YB - 3) * S, X1 * S, (YB + 3) * S], radius=3 * S, fill=GRAYBAR)        # ふつうの帯とつまみ（そのまま）
    d.rounded_rectangle([X0 * S, (YB - 3) * S, KNOB * S, (YB + 3) * S], radius=3 * S, fill=TEAL)
    d.ellipse([(KNOB - 11) * S, (YB - 11) * S, (KNOB + 11) * S, (YB + 11) * S], fill=LIGHT)
    if k == 0: return im
    Y = 88; h = 13                                                                                    # まとまりの帯：画面のいちばん上（持つ手の親指で隠れない）
    d.rectangle([X0 * S, (Y - h - 8) * S, X1 * S, (Y + h + 8) * S], fill=BG)
    w = (X1 - X0 - GAP * (N - 1)) / N
    for i in range(N):
        a = X0 + i * (w + GAP); b = a + w; num = "%02d" % (i + first)
        played = k >= 2 and i < now_i; now = k >= 3 and i == now_i
        fill = CYAN if now else (TEAL if played else GRAYBAR)
        if now:                                                                                       # 光っているまとまりのにじみ（画面そのものが光る）
            for g in range(7, 0, -1):
                c = tuple(int(BG[j] + (CYAN[j] - BG[j]) * 0.09 * (8 - g)) for j in range(3))
                d.rounded_rectangle([(a - g) * S, (Y - h - g) * S, (b + g) * S, (Y + h + g) * S], radius=(6 + g) * S, fill=c)
        d.rounded_rectangle([a * S, (Y - h) * S, b * S, (Y + h) * S], radius=6 * S, fill=fill)
        col = (10, 30, 34) if (now or played) else (200, 206, 214)
        d.text(((a + b) / 2 * S, Y * S), num, font=font(15), fill=col, anchor="mm")
    return im


for k in range(4):
    chunks(k).save(os.path.join(OUT, "music_k%d.png" % k))
chunks(3, first=4, now_i=2).save(os.path.join(OUT, "music_c6.png"))          # 第6章：04〜08 の帯で、いま送っている 06 が光る
print("SCREENS ->", OUT)
