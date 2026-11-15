# QR回（EP02「QRコードは欠けてもなぜ読める？」）のサムネイル案（2026-11-15）。EP01 の thumbs.py を元にした
#   使い方: THUMB_WORK=<作業フォルダ（src/ にコマの png、out/ に出す）> python3 thumbs_ep02.py
#   コマ：組み立てた章の字幕なしの動画（final/<章>_clean.mp4）から、札の出ていない所を ffmpeg で抜いた png（<章>_<秒>.png）
#   素材：PC で描いた本番の 3D（字幕・札なし）。2560×1440 で組んで 1280×720 に縮める（字のふちがきれい）
#   字：Noto Sans CJK JP を太らせて（同じ色のふち）、紺の太いふち＋影。黄色は大事な言葉
import os, math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
S = os.environ["THUMB_WORK"]; SRC = S + "/src"; OUT = S + "/out"
FONT = os.environ.get("THUMB_FONT", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
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
    bold = bold if bold is not None else max(2, int(px * 0.012)); out = out if out is not None else int(px * 0.13)
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
# A：欠けても なぜ読める？（まるロボの目のアップ）
im = bg("op_28.png", zoom=1.0, cx=0.62, cy=0.5); im = shade(im, "right", 0.62, 0.86)
im = ribbon(im, (W - 90 - 760, 80), SER)
im, _ = big(im, (W - 110, 360), [("欠けても", WHITE)], 300, anchor="r")
im, _ = big(im, (W - 100, 760), [("なぜ", WHITE), ("読める", YEL), ("？", WHITE)], 300, anchor="r")
made.append(save(im, "thumb_A"))
# B：体で隠しても 読めた!?（まるロボが QR の右下に乗る。字は上、まるロボは下）
im = bg("op_13.png", zoom=1.3, cx=0.45, cy=0.50); im = shade(im, "top", 0.50, 0.90)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (W / 2, 210), [("体で隠しても", WHITE)], 190, anchor="c")
im, _ = big(im, (W / 2, 430), [("読めた", YEL), ("!?", WHITE)], 280, anchor="c")
made.append(save(im, "thumb_B"))
# C：3分の2は 予備だった！（色分けした QR の中の世界）
im = bg("c5_94.png", zoom=1.15, cx=0.62, cy=0.66); im = shade(im, "top", 0.62, 0.90)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (W / 2, 230), [("中身の", WHITE), ("3分の2", YEL), ("は", WHITE)], 230, anchor="c")
im, _ = big(im, (W / 2, 520), [("予備", YEL), ("だった！", WHITE)], 290, anchor="c")
made.append(save(im, "thumb_C"))
# D：たった3%の汚れで 読めない!?（インクのびんを倒したまるロボ。字は左、まるロボは右）
im = bg("c5_34.png", zoom=1.12, cx=0.50, cy=0.55); im = shade(im, "left", 0.58, 0.88)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 330), [("たった", WHITE), ("3%", YEL), ("の", WHITE)], 210)
im, _ = big(im, (100, 590), [("汚れで", WHITE)], 210)
im, _ = big(im, (100, 860), [("読めない", YEL), ("!?", WHITE)], 250)
made.append(save(im, "thumb_D"))
# E：QRコードの中に 入ってみた！（箱の並ぶ世界のまるロボ。字は上、まるロボは下）
im = bg("c1_92.png", zoom=1.0, cx=0.5, cy=0.30); im = shade(im, "top", 0.50, 0.92)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (W / 2, 200), [("QRコードの", WHITE), ("中", YEL), ("に", WHITE)], 210, anchor="c")
im, _ = big(im, (W / 2, 450), [("入ってみた！", WHITE)], 240, anchor="c")
made.append(save(im, "thumb_E"))
# F：隠すと読める 汚れると読めない？（まるロボの正面）
im = bg("op_49.png", zoom=1.3, cx=0.30, cy=0.45); im = shade(im, "left", 0.62, 0.88)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 320), [("隠すと", WHITE)], 200)
im, _ = big(im, (100, 540), [("読める", YEL)], 260)
im, _ = big(im, (100, 860), [("汚れると", WHITE)], 200)
im, _ = big(im, (100, 1080), [("読めない？", YEL)], 220)
made.append(save(im, "thumb_F"))
# 一覧：同じ大きさで並べたもの・スマホの一覧の大きさ（210×118）
tiles = [Image.open(p) for p in made]
sheet = Image.new("RGB", (640 * 3 + 40, 360 * 2 + 30), (240, 240, 240))
for i, t in enumerate(tiles): sheet.paste(t.resize((640, 360), Image.LANCZOS), (10 + (i % 3) * 650, 10 + (i // 3) * 370))
sheet.save(os.path.join(OUT, "sheet.jpg"), quality=90)
small = Image.new("RGB", (210 * 3 + 40, 118 * 2 + 30), (255, 255, 255))
for i, t in enumerate(tiles): small.paste(t.resize((210, 118), Image.LANCZOS), (10 + (i % 3) * 220, 10 + (i // 3) * 128))
small.save(os.path.join(OUT, "sheet_small.png"))
print("\n".join(made))
