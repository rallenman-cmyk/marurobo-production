# 2章の図（1920×1080）：S11 印刷物を白黒にして比率を調べる／S17 大きな QR の小さな目印
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import segno
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'sb'); os.makedirs(OUT, exist_ok=True)
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
BG = (238, 242, 245); INK = (40, 46, 52); GRAY = (150, 158, 166); BLACK = (24, 27, 32); WHITE = (250, 250, 248); TEAL = (44, 198, 208); RED = (217, 71, 90); ORG = (240, 149, 58)
F = lambda s: ImageFont.truetype(FB, s)
W_, H_ = 1920, 1080
A = json.load(open(os.path.join(HERE, 'qr_assets.json'), encoding='utf-8')); M = A['symbols']['HELLO_H']['matrix']
rng = np.random.default_rng(5)

def card(kind, w, h, bw=False):
    """チラシ・雑誌・段ボール（簡単な絵）。bw=True で白黒に直した版（ブロック状）"""
    im = Image.new('RGB', (w, h), (255, 255, 255)); d = ImageDraw.Draw(im)
    if kind == 'flyer':
        d.rectangle((0, 0, w, h), fill=(255, 236, 200)); d.rectangle((0, 0, w, h * 0.28), fill=(232, 90, 70)); d.text((w / 2, h * 0.14), 'SALE', font=F(int(h * 0.15)), fill=(255, 255, 255), anchor='mm')
        d.ellipse((w * 0.15, h * 0.36, w * 0.55, h * 0.76), fill=(250, 190, 60)); d.text((w * 0.75, h * 0.56), '50%', font=F(int(h * 0.12)), fill=(200, 40, 40), anchor='mm')
        for k in range(3): d.rectangle((w * 0.1, h * (0.8 + 0.055 * k), w * 0.9, h * (0.82 + 0.055 * k)), fill=(120, 90, 70))
    elif kind == 'mag':
        d.rectangle((0, 0, w, h), fill=(225, 238, 250)); d.rectangle((w * 0.08, h * 0.06, w * 0.92, h * 0.5), fill=(90, 140, 200))
        d.ellipse((w * 0.35, h * 0.12, w * 0.65, h * 0.42), fill=(240, 210, 180)); d.text((w / 2, h * 0.58), 'MAGAZINE', font=F(int(h * 0.07)), fill=(30, 40, 60), anchor='mm')
        for k in range(6): d.rectangle((w * 0.1, h * (0.66 + 0.05 * k), w * (0.9 - 0.08 * (k % 3)), h * (0.68 + 0.05 * k)), fill=(80, 90, 110))
    else:
        d.rectangle((0, 0, w, h), fill=(196, 150, 100))
        for k in range(8): d.line((0, h * k / 8, w, h * k / 8 + 6), fill=(180, 135, 88), width=3)
        d.rectangle((w * 0.2, h * 0.3, w * 0.8, h * 0.6), outline=(60, 40, 25), width=8); d.text((w / 2, h * 0.45), 'FRAGILE', font=F(int(h * 0.08)), fill=(60, 40, 25), anchor='mm')
        d.text((w / 2, h * 0.78), '↑↑', font=F(int(h * 0.14)), fill=(60, 40, 25), anchor='mm')
    if bw:
        g = np.asarray(im.convert('L').resize((w // 12, h // 12), Image.BILINEAR)); b = (g > 185).astype(np.uint8) * 255
        im = Image.fromarray(b).resize((w, h), Image.NEAREST).convert('RGB')
    return im

def frame_bw(stage):
    """K25：印刷物 → 白黒に直す → 横になぞって比率を数える"""
    img = Image.new('RGB', (W_, H_), BG); d = ImageDraw.Draw(img)
    kinds = (('flyer', 'チラシ'), ('mag', '雑誌'), ('box', '段ボール')); w, h = 300, 400
    for k, (kd, nm) in enumerate(kinds):
        x = 180 + k * 560; img.paste(card(kd, w, h), (x, 170)); d.text((x + w / 2, 130), nm, font=F(44), fill=INK, anchor='mm')
        if stage >= 1:
            bw = card(kd, w, h, bw=True); img.paste(bw, (x + 330 - 80 if False else x, 620 - 20)) if False else None
    if stage >= 1:
        for k, (kd, nm) in enumerate(kinds):
            x = 180 + k * 560; bw = card(kd, w // 2 * 2, h, bw=True).resize((w, h // 2 + 40)); y = 640
            img.paste(bw, (x, y)); d.line((x + w / 2, 590, x + w / 2, 630), fill=GRAY, width=6); d.polygon([(x + w / 2 - 14, 618), (x + w / 2 + 14, 618), (x + w / 2, 636)], fill=GRAY)
            if stage >= 2:
                yy = y + 60 + 30 * k; d.line((x - 10, yy, x + w + 10, yy), fill=TEAL, width=6)
        d.text((W_ / 2, 1010), '白黒に直す', font=F(40), fill=GRAY, anchor='mm') if stage == 1 else None
    img.save(os.path.join(OUT, 'K25%s.png' % ('' if stage == 2 else 'a')))

def frame_chart(hl):
    """K26：比率ごとに数える（イメージ）。1:1:3:1:1 はほとんど出てこない"""
    img = Image.new('RGB', (W_, H_), BG); d = ImageDraw.Draw(img)
    labels = ['1:1:1:1:1', '2:1:1:1:2', '1:2:1:2:1', '3:1:1:1:3', '1:1:2:1:1', '2:2:1:2:2', '1:3:1:3:1', '2:1:2:1:2', '1:1:3:1:1']
    vals = [0.95, 0.82, 0.71, 0.60, 0.50, 0.41, 0.33, 0.25, 0.015]
    x0, y0, bw, gap, Hh = 200, 760, 118, 62, 540
    d.line((x0 - 30, y0, x0 + len(vals) * (bw + gap) + 10, y0), fill=GRAY, width=4)
    for k, (lb, v) in enumerate(zip(labels, vals)):
        x = x0 + k * (bw + gap); hh = max(6, Hh * v); col = TEAL if (hl and k == 8) else (176, 184, 192)
        d.rectangle((x, y0 - hh, x + bw, y0), fill=col)
        d.text((x + bw / 2, y0 + 40), lb, font=F(26 if not (hl and k == 8) else 30), fill=TEAL if (hl and k == 8) else INK, anchor='mm')
    d.text((x0 - 30, 150), '印刷物に出てきた回数', font=F(42), fill=INK, anchor='lm'); d.text((W_ - 160, 150), '（イメージ）', font=F(30), fill=GRAY, anchor='rm')
    if hl:
        x = x0 + 8 * (bw + gap) + bw / 2; d.ellipse((x - 95, y0 - 80, x + 95, y0 + 80), outline=TEAL, width=8); d.text((x + 40, y0 - 230), '一番少ない', font=F(40), fill=TEAL, anchor='mm')
    img.save(os.path.join(OUT, 'K26%s.png' % ('b' if hl else 'a')))

def qr_draw(d, mat, x, y, px, quiet=2):
    n = len(mat); d.rectangle((x, y, x + (n + 2 * quiet) * px, y + (n + 2 * quiet) * px), fill=WHITE)
    for r in range(n):
        for c in range(n):
            if mat[r][c]: d.rectangle((x + (c + quiet) * px, y + (r + quiet) * px, x + (c + quiet + 1) * px - 1, y + (r + quiet + 1) * px - 1), fill=BLACK)

def frame_big():
    """K37：大きな QR（41×41・バージョン6）の小さな目印（位置合わせ）に丸。今回の 21×21 にはない"""
    img = Image.new('RGB', (W_, H_), BG); d = ImageDraw.Draw(img)
    q = segno.make('https://example.com/qr/maru-robo/hello-world-and-more-text', error='h', version=6, boost_error=False)
    big = [[1 if v else 0 for v in row] for row in q.matrix]; n = len(big)
    px = 14; X, Y = 1000, 110
    qr_draw(d, M, 260, 260, 18); d.text((260 + 25 * 18 / 2, 200), '今回（21×21）', font=F(40), fill=INK, anchor='mm')
    qr_draw(d, big, X, Y, px); d.text((X + (n + 4) * px / 2, 70), '大きなQR（41×41）', font=F(40), fill=INK, anchor='mm')
    # 位置合わせの目印（バージョン6：6, 22, 34 の組み合わせ。目印と重なる3か所を除く）
    pos = [6, 22, 34]
    for r in pos:
        for c in pos:
            if (r, c) in ((6, 6), (6, 34), (34, 6)): continue
            cx = X + (c + 2 + 0.5) * px; cy = Y + (r + 2 + 0.5) * px; d.ellipse((cx - 52, cy - 52, cx + 52, cy + 52), outline=ORG, width=8)
    d.text((X + (n + 4) * px / 2, Y + (n + 4) * px + 60), 'ゆがみを直す、小さな目印', font=F(40), fill=ORG, anchor='mm')
    img.save(os.path.join(OUT, 'K37.png')); print('version', q.version, 'size', n)

frame_bw(1); frame_bw(2); frame_chart(False); frame_chart(True); frame_big()
