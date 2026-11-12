# この動画（Bluetooth イヤホンのしくみ）のサムネイル案（2026-11-09）
#   素材：PC で描いた本番の 3D（字幕・札なし）。2560×1440 で組んで 1280×720 に縮める（字のふちがきれい）
#   字：Noto Sans CJK JP を太らせて（同じ色のふち）、紺の太いふち＋影。黄色は大事な言葉
import os, math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
S = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; SRC = S + "/work_thumb/src"; OUT = S + "/work_thumb/out"
FONT = S + "/stage/av/fonts/japanese.ttc"
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


SER = "Bluetoothイヤホンのしくみ"
made = []
# A：隣の曲、なぜ混ざらない？（電車の中の主人公とまわりの人）
im = bg("op_0589.png", zoom=1.10, cx=0.74, cy=0.50); im = shade(im, "left", 0.66, 0.84)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 330), [("隣の曲", YEL)], 300)
im, _ = big(im, (100, 690), [("なぜ", WHITE)], 230)
im, _ = big(im, (100, 960), [("混ざらない？", WHITE)], 270)
made.append(save(im, "thumb_A"))
# B：音がとぎれる本当の理由（耳に手を当てる主人公の寄り）
im = bg("o2_1176.png", zoom=1.05, cx=0.60, cy=0.45); im = shade(im, "left", 0.62, 0.85)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 330), [("音が", WHITE)], 250)
im, _ = big(im, (100, 610), [("とぎれる", YEL)], 330)
im, _ = big(im, (100, 990), [("本当の理由", WHITE)], 230)
im = qmark(im, (2050, 330), 120)
made.append(save(im, "thumb_B"))
# C：イヤホンの中に 倉庫があった（バッファの塔とまるロボ）
im = bg("c7_1850.png", zoom=1.15, cx=0.57, cy=0.45, bri=1.04); im = shade(im, "right", 0.60, 0.80, col=(40, 30, 20))
im = ribbon(im, (W - 90 - 1020, 80), SER)
im, _ = big(im, (W - 110, 330), [("イヤホンの中に", WHITE)], 170, anchor="r")
im, _ = big(im, (W - 100, 590), [("倉庫", YEL), ("が", WHITE)], 350, anchor="r")
im, _ = big(im, (W - 110, 1000), [("あった！", WHITE)], 250, anchor="r")
made.append(save(im, "thumb_C"))
# D：音楽は 荷物で届く（荷物を運ぶまるロボと巨大イヤホン）
im = bg("c3_0836.png", zoom=1.0, cx=0.5, cy=0.5); im = shade(im, "top", 0.50, 0.72, col=(12, 30, 50))
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (W - 120, 120), [("音楽は", WHITE)], 210, anchor="r")
im, _ = big(im, (W - 110, 370), [("荷物", YEL), ("で届く", WHITE)], 275, anchor="r")
made.append(save(im, "thumb_D"))
# E：2つのナゾ（まるロボの寄り＋①②）
im = bg("c3_0620.png", zoom=1.25, cx=0.38, cy=0.52, bri=1.03); im = shade(im, "left", 0.60, 0.85, col=(10, 30, 45))
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 300), [("イヤホンの", WHITE)], 200)
im, _ = big(im, (100, 545), [("2つのナゾ", YEL)], 268)
im, _ = big(im, (110, 930), [("① 混ざらない？", WHITE)], 140)
im, _ = big(im, (110, 1140), [("② とぎれる？", WHITE)], 140)
made.append(save(im, "thumb_E"))
# F：時間を止めて、のぞいてみた（一時停止ボタンに乗ったまるロボ）
im = bg("o2_1300.png", zoom=1.30, cx=0.33, cy=0.56, bri=1.05); im = shade(im, "left", 0.58, 0.82)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 320), [("電車の中で", WHITE)], 190)
im, _ = big(im, (100, 570), [("時間を", WHITE)], 250)
im, _ = big(im, (100, 860), [("止めてみた", YEL)], 280)
made.append(save(im, "thumb_F"))
# 一覧（大きい・小さい）
sheet = Image.new("RGB", (1280 * 2 + 30, 720 * 3 + 40), (240, 242, 244))
for i, p in enumerate(made):
    sheet.paste(Image.open(p), ((i % 2) * 1290, (i // 2) * 730))
sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2), Image.LANCZOS).save(OUT + "/sheet_big.jpg", quality=88)
small = Image.new("RGB", (6 * 214 + 10, 140), (255, 255, 255))     # スマホの一覧で見える大きさ（約 210×118）
for i, p in enumerate(made):
    small.paste(Image.open(p).resize((210, 118), Image.LANCZOS), (i * 214 + 4, 10))
small.save(OUT + "/sheet_small.png"); print("\n".join(made))
