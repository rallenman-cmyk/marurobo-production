# C13（本編 2:34.0〜2:41.0）の図：左にスマホ → 荷物 → 右にイヤホン。「送る」「受け取る」「音にする」を、ナレーションに合わせて出す
# 使い方: python3 ch03_diagram.py OUT_DIR  → OUT_DIR/diagram/d_0001.png …（1280×720・24fps・168コマ）
import sys, os, math
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(sys.argv[1], "diagram"); os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "av", "fonts", "japanese.ttc")
W, H, FPS, T = 1280, 720, 24, 8.4
T0 = 157.8                                    # 本編の時刻（台本 v2：31「データを送る」157.9・32「受け取って、音にする」159.3・33「この流れを土台に…」161.4〜166.1）
K_SEND, K_RECV, K_SOUND, K_ALL = 157.9 - T0, 159.3 - T0, 160.3 - T0, 161.4 - T0
BG = (238, 242, 245); INK = (40, 46, 52); TEAL = (31, 94, 102); CYAN = (63, 198, 201); GRAY = (150, 158, 166)
S = 2                                          # 2倍で描いて縮める（線をなめらかに）
if os.environ.get("MARU_RES") == "1080": S = 3   # 本番：3 倍で描いて 1920×1080 に縮める
OUT_WH = (1920, 1080) if S == 3 else (W, H)


def font(px, idx=0):
    try: return ImageFont.truetype(FONT, px * S, index=idx)
    except Exception: return ImageFont.load_default()


def smooth(u):
    u = max(0.0, min(1.0, u)); return u * u * u * (10 - 15 * u + 6 * u * u)


def fade(t, t0, T_=0.35): return smooth((t - t0) / T_)


def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle([v * S for v in box], radius=r * S, fill=fill, outline=outline, width=width * S)


def blend(c, a, bg=BG): return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))


PH = (250, 360)                                # スマホの中心
EB = (1030, 330)                               # イヤホンの中心
for i in range(int(T * FPS)):
    t = i / FPS
    im = Image.new("RGB", (W * S, H * S), BG); d = ImageDraw.Draw(im)
    # スマホ（左）：曲の画面
    x, y = PH; rr(d, (x - 72, y - 140, x + 72, y + 140), 18, fill=INK)
    rr(d, (x - 60, y - 126, x + 60, y + 126), 10, fill=(23, 27, 32))
    for k in range(40):                                        # 曲の画像（青緑→桃色）
        c = (int(45 + (232 - 45) * k / 39), int(170 + (110 - 170) * k / 39), int(205 + (160 - 205) * k / 39))
        d.rectangle([(x - 46) * S, (y - 108 + k * 2.2) * S, (x + 46) * S, (y - 108 + (k + 1) * 2.2) * S], fill=c)
    d.ellipse([(x - 18) * S, (y - 82) * S, (x + 18) * S, (y - 46) * S], fill=(250, 240, 222)); d.ellipse([(x - 6) * S, (y - 70) * S, (x + 6) * S, (y - 58) * S], fill=(30, 40, 60))
    rr(d, (x - 46, y + 8, x + 30, y + 16), 4, fill=(225, 230, 235)); rr(d, (x - 46, y + 24, x + 6, y + 30), 3, fill=(120, 128, 138))
    d.line([(x - 46) * S, (y + 56) * S, (x + 46) * S, (y + 56) * S], fill=(70, 80, 90), width=3 * S); d.line([(x - 46) * S, (y + 56) * S, (x + 2) * S, (y + 56) * S], fill=CYAN, width=3 * S)
    d.text((x * S, (y + 175) * S), "スマホ", font=font(28), fill=INK, anchor="mm")
    # イヤホン（右）
    x2, y2 = EB
    d.ellipse([(x2 - 78) * S, (y2 - 95) * S, (x2 + 62) * S, (y2 + 25) * S], fill=(250, 250, 248), outline=(205, 210, 215), width=3 * S)
    rr(d, (x2 - 8, y2 - 5, x2 + 34, y2 + 150), 21, fill=(250, 250, 248), outline=(205, 210, 215), width=3)
    d.ellipse([(x2 - 98) * S, (y2 - 62) * S, (x2 - 60) * S, (y2 - 18) * S], fill=(205, 212, 218))
    rr(d, (x2 - 2, y2 + 60, x2 + 28, y2 + 94), 6, fill=TEAL)            # 受付口
    d.text(((x2 + 13) * S, (y2 + 200) * S), "イヤホン", font=font(28), fill=INK, anchor="mm")
    # 矢印（スマホ → イヤホン）
    a0, a1 = (x + 110, y + 10), (x2 - 120, y2 + 60)
    al = fade(t, K_SEND - 0.1, 0.5)
    ax = a0[0] + (a1[0] - a0[0]) * al; ay = a0[1] + (a1[1] - a0[1]) * al
    hi = 1.0 + 0.6 * math.sin(math.pi * max(0.0, min(1.0, (t - K_ALL) / 1.2)))
    d.line([a0[0] * S, a0[1] * S, ax * S, ay * S], fill=blend(TEAL, min(1.0, 0.85 * hi)), width=int(7 * S))
    if al > 0.98:
        ang = math.atan2(a1[1] - a0[1], a1[0] - a0[0]); L_ = 26
        pts = [(a1[0] + 6 * math.cos(ang), a1[1] + 6 * math.sin(ang)), (a1[0] - L_ * math.cos(ang - 0.45), a1[1] - L_ * math.sin(ang - 0.45)),
               (a1[0] - L_ * math.cos(ang + 0.45), a1[1] - L_ * math.sin(ang + 0.45))]
        d.polygon([(px * S, py * S) for px, py in pts], fill=TEAL)
    # 荷物：送る間は矢印の上を進み、受け取ると受付口へ入る
    u = smooth((t - K_SEND) / 1.0)
    if t >= K_SEND - 0.05 and t < K_RECV + 0.6:
        px_ = a0[0] + (a1[0] - a0[0]) * u; py_ = a0[1] + (a1[1] - a0[1]) * u - 44
        if t > K_RECV: k_ = smooth((t - K_RECV) / 0.5); px_ += (x2 + 13 - a1[0]) * k_; py_ += (y2 + 77 - 30 - (a1[1] - 44)) * k_
        sc = 1.0 if t <= K_RECV else 1.0 - 0.6 * smooth((t - K_RECV) / 0.5)
        if sc > 0.42:
            w_, h_ = 62 * sc, 42 * sc
            rr(d, (px_ - w_, py_ - h_, px_ + w_, py_ + h_), 12 * sc, fill=TEAL)
            rr(d, (px_ - w_ + 9 * sc, py_ - h_ + 8 * sc, px_ + w_ - 9 * sc, py_ + h_ - 8 * sc), 6 * sc, fill=(42, 45, 49))
            d.text(((px_ + 18 * sc) * S, (py_ - 12 * sc) * S), "03", font=font(max(8, int(20 * sc))), fill=(233, 236, 238), anchor="mm")
            d.ellipse([(px_ - 40 * sc) * S, (py_ - 24 * sc) * S, (px_ - 20 * sc) * S, (py_ - 4 * sc) * S], outline=CYAN, width=max(1, int(3 * sc * S)))
            for b in range(7):
                hh = (6, 12, 9, 16, 11, 14, 8)[b] * sc
                d.rectangle([(px_ - 38 * sc + b * 11 * sc) * S, (py_ + 22 * sc - hh) * S, (px_ - 34 * sc + b * 11 * sc) * S, (py_ + 22 * sc) * S], fill=(233, 236, 238))
    # 言葉（物のすぐ横）
    for txt, (tx, ty), k0 in (("送る", ((a0[0] + a1[0]) / 2 - 40, (a0[1] + a1[1]) / 2 + 56), K_SEND), ("受け取る", (x2 - 150, y2 + 150), K_RECV),
                               ("音にする", (x2 - 20, y2 - 160), K_SOUND)):
        a = fade(t, k0, 0.35)
        if a > 0: d.text((tx * S, ty * S), txt, font=font(40, 0), fill=blend(INK, a), anchor="mm")
    # 音（イヤホンの先から広がる輪）
    if t >= K_SOUND:
        for k in range(3):
            ph = ((t - K_SOUND) * 1.2 - k * 0.33) % 1.0
            if t - K_SOUND < k * 0.28: continue
            r = 40 + 70 * ph; a = (1 - ph) * fade(t, K_SOUND, 0.3)
            d.arc([(x2 - 80 - r) * S, (y2 - 40 - r) * S, (x2 - 80 + r) * S, (y2 - 40 + r) * S], 140, 230, fill=blend(CYAN, a), width=int(5 * S))
    im = im.resize(OUT_WH, Image.LANCZOS); im.save(os.path.join(OUT, "d_%04d.png" % (i + 1)))
print("DIAGRAM", int(T * FPS), "frames ->", OUT)
