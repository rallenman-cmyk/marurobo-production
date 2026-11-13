# 会話と広告の回のサムネ案 第2弾（2026-11-13）：「話している内容が、なぜ広告に出る？」の切り口
#   リサーチ（サムネのリサーチ.md）から：字を画面の半分くらい・話した物 → 広告を赤い矢印で結ぶ・強い表情・広告に赤丸
#   python3 thumbs2.py <絵のフォルダ> <出力フォルダ> <フォント.ttf>
#   絵：s01_0210（電車で話す二人）・s02_0169（テントの広告のスマホ）・s22_0098（まるロボとスマホ）。本番は PC の 3D に差し替え
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "thumbs.py"), encoding="utf-8").read().split('SER = ')[0]
exec(_src)
RED2 = (232, 40, 40)


def lay(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def bubble(im, box, lines, px, tail, col=WHITE, ink=NAVY):
    """吹き出し：box=(x0,y0,x1,y1)、tail=しっぽの先。字は lines（[(文字,色)…] の行のリスト）"""
    L = lay(); d = ImageDraw.Draw(L); x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bw = max(10, int(px * 0.09))
    tl = [(cx - (x1 - x0) * 0.12, y1 - 10), (cx + (x1 - x0) * 0.06, y1 - 10), tail]
    for k, c in ((bw, ink), (0, col)):
        d.rounded_rectangle((x0 - k, y0 - k, x1 + k, y1 + k), radius=int((y1 - y0) * 0.45) + k, fill=c + (255,))
        if k: d.polygon([(tl[0][0] - k * 1.2, tl[0][1]), (tl[1][0] + k * 1.2, tl[1][1]), (tail[0] + (k * 0.6 if tail[0] > cx else -k * 0.6), tail[1] + k)], fill=c + (255,))
        else: d.polygon(tl, fill=c + (255,))
    sh = L.filter(ImageFilter.GaussianBlur(14)); sh2 = lay(); sh2.paste((0, 0, 0, 110), (0, 0), sh.split()[3])
    im = Image.alpha_composite(im, ImageChops_offset(sh2, 10, 16)); im = Image.alpha_composite(im, L)
    f = F(px); total = len(lines) * px * 1.15; y = cy - total / 2
    for runs in lines:
        tw = sum(f.getbbox(t)[2] - f.getbbox(t)[0] for t, _ in runs); x = cx - tw / 2; dd = ImageDraw.Draw(im)
        for t, c in runs:
            b = f.getbbox(t); dd.text((x - b[0], y - f.getbbox("あ")[1]), t, font=f, fill=c, stroke_width=2, stroke_fill=c); x += b[2] - b[0]
        y += px * 1.15
    return im


def ImageChops_offset(im, dx, dy):
    out = lay(); out.paste(im, (dx, dy)); return out


def arrow(im, pts, width=60, col=RED2):
    """曲がった矢印（2 次ベジェ）：pts=(始, 曲げ, 先)。紺のふち＋赤"""
    (ax, ay), (bx, by), (cx, cy) = pts
    P = [((1 - t) ** 2 * ax + 2 * (1 - t) * t * bx + t * t * cx, (1 - t) ** 2 * ay + 2 * (1 - t) * t * by + t * t * cy) for t in [i / 60 for i in range(61)]]
    end = P[-8]; ang = math.atan2(cy - end[1], cx - end[0]); hl, hw = width * 2.2, width * 1.9
    head = [(cx, cy), (cx - hl * math.cos(ang) + hw * math.sin(ang), cy - hl * math.sin(ang) - hw * math.cos(ang)),
            (cx - hl * math.cos(ang) - hw * math.sin(ang), cy - hl * math.sin(ang) + hw * math.cos(ang))]
    body = P[:-6]
    for w_, c in ((width + 26, NAVY), (width, col)):
        L = lay(); d = ImageDraw.Draw(L)
        d.line(body, fill=c + (255,), width=w_, joint="curve")
        for p in (body[0],): d.ellipse((p[0] - w_ / 2, p[1] - w_ / 2, p[0] + w_ / 2, p[1] + w_ / 2), fill=c + (255,))
        if c == NAVY:
            k = 13; hh = [(cx + k * 1.6 * math.cos(ang), cy + k * 1.6 * math.sin(ang)), (head[1][0] - k * math.cos(ang) + k * math.sin(ang), head[1][1] - k * math.sin(ang) - k * math.cos(ang)),
                          (head[2][0] - k * math.cos(ang) - k * math.sin(ang), head[2][1] - k * math.sin(ang) + k * math.cos(ang))]
            d.polygon(hh, fill=c + (255,))
        else: d.polygon(head, fill=c + (255,))
        im = Image.alpha_composite(im, L)
    return im


def ring(im, c, rx, ry, col=RED2, w=26):
    L = lay(); d = ImageDraw.Draw(L); x, y = c
    d.ellipse((x - rx - 13, y - ry - 13, x + rx + 13, y + ry + 13), outline=NAVY + (255,), width=w + 26)
    d.ellipse((x - rx, y - ry, x + rx, y + ry), outline=col + (255,), width=w)
    return Image.alpha_composite(im, L)


def inset(im, name, crop, box, rot=0, border=16):
    """別の絵の一部を、ふちつきの四角で貼る（スマホの広告の寄りなど）"""
    s = Image.open(os.path.join(SRC, name)).convert("RGB").crop(crop)
    s = ImageEnhance.Color(s).enhance(1.15).resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
    m = Image.new("L", s.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, s.size[0] - 1, s.size[1] - 1), 40, fill=255)
    L = lay(); d = ImageDraw.Draw(L)
    d.rounded_rectangle((box[0] - border, box[1] - border, box[2] + border, box[3] + border), 52, fill=WHITE + (255,), outline=NAVY + (255,), width=10)
    L.paste(s, (box[0], box[1]), m)
    if rot: L = L.rotate(rot, center=((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), resample=Image.BICUBIC)
    sh = lay(); sh.paste((0, 0, 0, 120), (0, 0), L.split()[3].filter(ImageFilter.GaussianBlur(18)))
    return Image.alpha_composite(Image.alpha_composite(im, ImageChops_offset(sh, 14, 22)), L)


def sweat(im, c, s=1.0):
    L = lay(); d = ImageDraw.Draw(L); x, y = c
    for dx, dy, k in ((0, 0, 1.0), (70 * s, 90 * s, 0.7)):
        r = 34 * s * k; X, Y = x + dx, y + dy
        for w_, col in ((12, NAVY), (0, (120, 200, 255))):
            d.polygon([(X, Y - r * 2.1 - w_), (X - r - w_, Y), (X + r + w_, Y)], fill=col + (255,)); d.ellipse((X - r - w_, Y - r - w_, X + r + w_, Y + r + w_), fill=col + (255,))
    return Image.alpha_composite(im, L)


def shock(im, c, s=1.0):
    """びっくりの線（3 本）"""
    L = lay(); d = ImageDraw.Draw(L); x, y = c
    for a in (-60, -90, -120):
        r0, r1 = 40 * s, 140 * s; aa = math.radians(a)
        p0, p1 = (x + r0 * math.cos(aa), y + r0 * math.sin(aa)), (x + r1 * math.cos(aa), y + r1 * math.sin(aa))
        d.line([p0, p1], fill=NAVY + (255,), width=int(44 * s)); d.line([p0, p1], fill=YEL + (255,), width=int(22 * s))
    return Image.alpha_composite(im, L)


TALK = [[("キャンプ", NAVY)], [("行きたいね！", NAVY)]]
made = []
AD = (560, 330, 1360, 1000)          # s02_0169 の中の、テントの広告のあたり
# 1：電車で話す二人 → 矢印 → テントの広告（赤丸）。字は下に大きく
im = bg("s01_0210.png", zoom=1.0, cx=0.5, cy=0.5, bri=1.05); im = shade(im, "bottom", 0.36, 0.95)
im = bubble(im, (60, 60, 820, 400), TALK, 118, (720, 570))
im = inset(im, "s02_0169.png", AD, (1780, 50, 2450, 610), rot=-5)
im = ring(im, (2110, 340), 230, 200)
im = arrow(im, ((840, 210), (1300, 20), (1730, 250)))
im, _ = big(im, (W / 2, 990), [("話した内容が", WHITE)], 180, anchor="c")
im, _ = big(im, (W / 2, 1190), [("なぜ ", WHITE), ("広告", YEL), ("に？", WHITE)], 210, anchor="c")
made.append(save(im, "t2_1"))
# 2：まるロボのびっくり＋スマホの広告に赤丸。字は左に大きく
im = bg("s22_0098.png", zoom=1.35, cx=0.45, cy=0.70, bri=1.03); im = shade(im, "left", 0.45, 0.92)
im = ring(im, (2047, 864), 330, 360)
im = sweat(im, (1440, 300), 1.3); im = shock(im, (1500, 230), 1.5)
im = bubble(im, (60, 60, 900, 380), [[("さっき", NAVY), ("テント", RED2)], [("の話をしたら…", NAVY)]], 96, (1000, 470))
im, _ = big(im, (80, 520), [("なぜ", WHITE)], 210)
im, _ = big(im, (80, 790), [("広告", YEL), ("に", WHITE)], 300)
im, _ = big(im, (80, 1150), [("出る？", WHITE)], 210)
made.append(save(im, "t2_2"))
# 3：字が主役。「話した内容が 広告に!?」＋右に吹き出し → 広告の寄り
im = bg("s02_0169.png", zoom=1.0, cx=0.5, cy=0.5, bri=0.70); im = shade(im, "left", 0.70, 0.95)
im = inset(im, "s02_0169.png", AD, (1600, 560, 2440, 1260), rot=-4)
im = ring(im, (2020, 900), 300, 260)
im = bubble(im, (1540, 50, 2450, 320), [[("テント", RED2), ("ほしいな", NAVY)]], 110, (2000, 560))
im, _ = big(im, (80, 140), [("話した", WHITE)], 250)
im, _ = big(im, (80, 450), [("内容が", WHITE)], 250)
im, _ = big(im, (80, 790), [("広告", YEL), ("に!?", RED2)], 360)
made.append(save(im, "t2_3"))
sheet = Image.new("RGB", (1280 * 2 + 30, 720 * 2 + 30), (240, 242, 244))
for i, p in enumerate(made): sheet.paste(Image.open(p), ((i % 2) * 1290, (i // 2) * 730))
sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2), Image.LANCZOS).save(OUT + "/sheet2_big.jpg", quality=88)
small = Image.new("RGB", (len(made) * 214 + 10, 140), (255, 255, 255))
for i, p in enumerate(made): small.paste(Image.open(p).resize((210, 118), Image.LANCZOS), (i * 214 + 4, 10))
small.save(OUT + "/sheet2_small.png"); print("\n".join(made))
