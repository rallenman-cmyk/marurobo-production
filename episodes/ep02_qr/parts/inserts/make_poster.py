# 冒頭 02-03.5「そういえば、少し汚れたポスターのQRコードでも、ちゃんと読めることがありますよね。」の図（1920×1080）
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, '..', 'qrdata', 'qr_assets.json'), encoding='utf-8')); M = A['symbols']['HELLO_H']['matrix']; N = A['size']
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
BG = (238, 242, 245); INK = (40, 46, 52); GRAY = (150, 158, 166); BLACK = (24, 27, 32)
W_, H_ = 1920, 1080
def qr_img(px, quiet=2):
    n = N + 2 * quiet; im = Image.new('RGB', (n, n), (250, 250, 246)); d = im.load()
    for r in range(N):
        for c in range(N):
            if M[r][c]: d[c + quiet, r + quiet] = BLACK
    return im.resize((px, px), Image.NEAREST)
def stain(base, cx, cy, r, seed):
    rng = np.random.default_rng(seed); lay = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pts = [(cx + r * (1 + 0.18 * rng.standard_normal()) * math.cos(a), cy + r * (1 + 0.18 * rng.standard_normal()) * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
    d.polygon(pts, fill=(120, 78, 40, 120)); d.line(pts + [pts[0]], fill=(95, 60, 30, 170), width=6)
    for k in range(6):
        a = rng.uniform(0, 2 * math.pi); rr = r * rng.uniform(1.15, 1.6); s = rng.uniform(5, 14)
        d.ellipse((cx + rr * math.cos(a) - s, cy + rr * math.sin(a) - s, cx + rr * math.cos(a) + s, cy + rr * math.sin(a) + s), fill=(110, 70, 35, 150))
    return Image.alpha_composite(base, lay.filter(ImageFilter.GaussianBlur(1.2)))
img = Image.new('RGB', (W_, H_), BG); dr = ImageDraw.Draw(img)
f1 = ImageFont.truetype(FB, 52); fp = ImageFont.truetype(FB, 86); fs = ImageFont.truetype(FB, 30)
# ---- 左：壁に貼ったポスター（右下の角が少し破れ、QRにしみと汚れ）
PW, PH = 560, 760; post = Image.new('RGBA', (PW, PH), (246, 240, 226, 255)); pd = ImageDraw.Draw(post)
pd.rectangle((0, 0, PW, 170), fill=(63, 134, 221, 255)); pd.text((PW / 2, 88), '夏まつり', font=fp, fill=(255, 255, 255, 255), anchor='mm')
for k, w in enumerate((420, 360, 400, 300)): pd.rounded_rectangle((60, 220 + 46 * k, 60 + w, 244 + 46 * k), 10, fill=(205, 198, 182, 255))
q = qr_img(300); post.paste(q, (PW - 360, PH - 360))
post = stain(post, PW - 175, PH - 150, 62, 3)                                    # 中身のあたりにコーヒーのしみ
pd = ImageDraw.Draw(post)
for (x, y, s) in ((PW - 300, PH - 290, 9), (PW - 120, PH - 250, 7), (PW - 230, PH - 95, 11)): pd.ellipse((x - s, y - s, x + s, y + s), fill=(60, 50, 40, 230))
tear = [(PW, PH - 110), (PW - 70, PH), (PW, PH)]; pd.polygon(tear, fill=(0, 0, 0, 0))   # 右下の角が破れている（目印のない角）
pd.line([(PW, PH - 110), (PW - 34, PH - 62), (PW - 70, PH)], fill=(200, 192, 176, 255), width=4)
for x in (40, PW - 40): pd.rectangle((x - 46, -6, x + 46, 30), fill=(230, 226, 205, 210))   # テープ
post = post.rotate(-3, resample=Image.BICUBIC, expand=True)
sh = Image.new('RGBA', post.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 70), mask=post.split()[3]); sh = sh.filter(ImageFilter.GaussianBlur(10))
px0, py0 = 330, 200
img.paste(sh, (px0 + 12, py0 + 16), sh); img.paste(post, (px0, py0), post)
dr.text((px0 + PW / 2, 120), '汚れたポスター', font=f1, fill=INK, anchor='mm')
# ---- 矢印
dr.line((975, 580, 1060, 580), fill=GRAY, width=8); dr.polygon([(1060, 556), (1094, 580), (1060, 604)], fill=GRAY)
# ---- 右：スマホ（読み取りの結果）
x0, y0, w, h = 1150, 160, 440, 840
dr.rounded_rectangle((x0, y0, x0 + w, y0 + h), 60, fill=BLACK); dr.rounded_rectangle((x0 + 18, y0 + 18, x0 + w - 18, y0 + h - 18), 46, fill=(214, 206, 190))
cam = post.resize((int(post.size[0] * 0.62), int(post.size[1] * 0.62))); img.paste(cam, (x0 + 40, y0 + 250), cam)
dr = ImageDraw.Draw(img)
dr.rounded_rectangle((x0 + 36, y0 + 60, x0 + w - 36, y0 + 200), 28, fill=(248, 248, 246))
dr.text((x0 + 70, y0 + 96), 'URL', font=fs, fill=(110, 116, 124), anchor='lm'); dr.text((x0 + 70, y0 + 152), 'example.com', font=ImageFont.truetype(FB, 38), fill=INK, anchor='lm')
cx, cy = x0 + w - 78, y0 + 100; dr.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=(120, 220, 140)); dr.line([(cx - 16, cy + 2), (cx - 4, cy + 14), (cx + 18, cy - 12)], fill=(255, 255, 255), width=8)
dr.text((x0 + w / 2, 120), '読み取れる', font=f1, fill=INK, anchor='mm')
img.save(os.path.join(HERE, 'poster_dirty.png')); print('ok')
