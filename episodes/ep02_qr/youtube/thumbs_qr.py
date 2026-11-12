# QRコード回のサムネイル案（仮：絵コンテの絵。本番は PC の 3D のコマに差し替える）（2026-11-12）
#   素材：PC で描いた本番の 3D（字幕・札なし）。2560×1440 で組んで 1280×720 に縮める（字のふちがきれい）
#   字：Noto Sans CJK JP を太らせて（同じ色のふち）、紺の太いふち＋影。黄色は大事な言葉
import os, math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
SRC = "/home/user/qr_plan/parts"; OUT = "/home/user/qr_plan/youtube"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
W, H = 2560, 1440
NAVY, YEL, WHITE, TEAL, TEAL2, RED = (16, 30, 52), (255, 214, 48), (255, 255, 255), (20, 104, 112), (42, 170, 168), (226, 64, 56)
def F(px): return ImageFont.truetype(FONT, px, index=0)


def bg(name, zoom=1.0, cx=0.5, cy=0.5, sat=1.12, con=1.06, bri=1.0):
    im = Image.open(os.path.join(SRC, name)).convert("RGB"); w, h = im.size
    cw, ch = w / zoom, h / zoom; x0 = min(max(cx * w - cw / 2, 0), w - cw); y0 = min(max(cy * h - ch / 2, 0), h - ch)
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat); im = ImageEnhance.Contrast(im).enhance(con); im = ImageEnhance.Brightness(im).enhance(bri)
    return im.convert("RGBA")


def shade(im, side="left", frac=0.62, a0=0.78, col=(10, 22, 38)):
    """字の後ろを暗く（なめらかに）"""
    g = Image.new("L", (W, H), 0); d = ImageDraw.Draw(g)
    n = int(W * frac) if side in ("left", "right") else int(H * frac)
    for i in range(n):
        a = int(255 * a0 * (1 - i / n) ** 1.6)
        if side == "left": d.line([(i, 0), (i, H)], fill=a)
        elif side == "right": d.line([(W - 1 - i, 0), (W - 1 - i, H)], fill=a)
        elif side == "top": d.line([(0, i), (W, i)], fill=a)
        else: d.line([(0, H - 1 - i), (W, H - 1 - i)], fill=a)
    lay = Image.new("RGBA", (W, H), col + (0,)); lay.putalpha(g)
    return Image.alpha_composite(im, lay)


def text_w(txt, px, bold):
    f = F(px); b = f.getbbox(txt, stroke_width=bold); return b[2] - b[0], b[3] - b[1], b


def big(im, xy, runs, px, anchor="l", bold=None, out=None, shadow=True, spacing=0):
    """runs：[(文字, 色), …] を 1 行に。xy：行の左上（anchor l）・中央上（c）・右上（r）"""
    bold = bold if bold is not None else max(2, int(px * 0.032)); out = out if out is not None else int(px * 0.13)
    f = F(px); widths = [text_w(t, px, bold)[0] for t, _ in runs]; tw = sum(widths) + spacing * (len(runs) - 1)
    x, y = xy
    if anchor == "c": x -= tw / 2
    elif anchor == "r": x -= tw
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ol = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds, do, df = ImageDraw.Draw(sh), ImageDraw.Draw(ol), ImageDraw.Draw(fg)
    cx = x
    for (t, col), w_ in zip(runs, widths):
        top = -f.getbbox(t, stroke_width=bold)[1]
        if shadow: ds.text((cx + px * 0.035, y + top + px * 0.06), t, font=f, fill=(0, 0, 0, 150), stroke_width=bold + out, stroke_fill=(0, 0, 0, 150))
        do.text((cx, y + top), t, font=f, fill=NAVY + (255,), stroke_width=bold + out, stroke_fill=NAVY + (255,))
        df.text((cx, y + top), t, font=f, fill=col + (255,), stroke_width=bold, stroke_fill=col + (255,))
        cx += w_ + spacing
    if shadow: im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(px * 0.03)))
    im = Image.alpha_composite(im, ol); return Image.alpha_composite(im, fg), (x, y, tw)


def ribbon(im, xy, txt, px=64, bgc=TEAL, fg=WHITE):
    f = F(px); b = f.getbbox(txt, stroke_width=2); tw, th = b[2] - b[0], b[3] - b[1]
    x, y = xy; pad = int(px * 0.45)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x, y, x + tw + pad * 2, y + th + pad * 1.5), radius=int(px * 0.35), fill=bgc + (240,), outline=WHITE + (255,), width=6)
    d.text((x + pad, y + pad * 0.75 - b[1]), txt, font=f, fill=fg, stroke_width=2, stroke_fill=fg)
    return Image.alpha_composite(im, lay)


def qmark(im, c, r, col=YEL, txt="？", px=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); x, y = c
    d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), fill=NAVY + (255,)); d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
    f = F(px or int(r * 1.5)); b = f.getbbox(txt, stroke_width=6)
    d.text((x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2), txt, font=f, fill=NAVY, stroke_width=6, stroke_fill=NAVY)
    return Image.alpha_composite(im, lay)


def save(im, name):
    im = im.convert("RGB").resize((1280, 720), Image.LANCZOS)
    p = os.path.join(OUT, name + ".jpg"); im.save(p, quality=92, optimize=True); return p



SER = "QRコードのしくみ"
made = []
# A：隠しても読める！？（QRに乗ったまるロボと、HELLO が出たスマホ）
im = bg("opening/sb2/S05_sh_hello.png", zoom=1.0, cx=0.62, cy=0.5); im = shade(im, "left", 0.62, 0.85)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 330), [("隠しても", WHITE)], 250)
im, _ = big(im, (100, 640), [("読める", YEL), ("！？", WHITE)], 320)
made.append(save(im, "thumb_A"))
# B：たった3%で読めない（インクのしずく）
im = bg("v2/fig/c5_drops.png", zoom=1.05, cx=0.55, cy=0.45); im = shade(im, "left", 0.60, 0.85)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 300), [("たった", WHITE)], 200)
im, _ = big(im, (100, 540), [("3%", YEL), ("で", WHITE)], 340)
im, _ = big(im, (100, 1000), [("読めない！？", WHITE)], 220)
made.append(save(im, "thumb_B"))
# C：中に予備が17個（橙の箱の群れ）
im = bg("ch1/sb/K14.png", zoom=1.1, cx=0.5, cy=0.6); im = shade(im, "top", 0.55, 0.80, col=(12, 22, 38))
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (W - 110, 120), [("QRの中に", WHITE)], 200, anchor="r")
im, _ = big(im, (W - 100, 380), [("予備", YEL), ("が17個", WHITE)], 280, anchor="r")
made.append(save(im, "thumb_C"))
# D：ロゴ入りQRの弱点
im = bg("v2/fig/c5_logo.png", zoom=1.1, cx=0.5, cy=0.5); im = shade(im, "right", 0.62, 0.85)
im = ribbon(im, (W - 90 - 760, 80), SER)
im, _ = big(im, (W - 110, 330), [("ロゴ入りQRの", WHITE)], 180, anchor="r")
im, _ = big(im, (W - 100, 600), [("弱点", YEL)], 380, anchor="r")
made.append(save(im, "thumb_D"))
# E：欠けてもなぜ読める？（タイトルそのまま。まるロボの寄り）
im = bg("opening/sb2/S11_face.png", zoom=1.15, cx=0.62, cy=0.5); im = shade(im, "left", 0.62, 0.86)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 330), [("欠けても", WHITE)], 250)
im, _ = big(im, (100, 640), [("なぜ", YEL)], 300)
im, _ = big(im, (100, 1000), [("読める？", WHITE)], 260)
made.append(save(im, "thumb_E"))
# F：境目は8個（あふれたメーターの大地）
im = bg("c5/sb/W29.png", zoom=1.1, cx=0.5, cy=0.55); im = shade(im, "left", 0.58, 0.82)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 330), [("ここまで", WHITE)], 220)
im, _ = big(im, (100, 610), [("なら", WHITE)], 200)
im, _ = big(im, (100, 900), [("読める", YEL)], 300)
made.append(save(im, "thumb_F"))
sheet = Image.new("RGB", (1280 * 3 // 2, 720 * 2 // 2), "white")
for i, p in enumerate(made): sheet.paste(Image.open(p).resize((640, 360)), ((i % 3) * 640, (i // 3) * 360))
sheet.save(os.path.join(OUT, "thumbs_sheet.png"))
small = Image.new("RGB", (6 * 230, 140), "white")
for i, p in enumerate(made): small.paste(Image.open(p).resize((210, 118)), (10 + i * 230, 11))
small.save(os.path.join(OUT, "thumbs_small.png")); print("ok", len(made))
