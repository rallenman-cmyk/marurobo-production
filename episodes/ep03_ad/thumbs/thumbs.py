# 会話と広告の回のサムネイル案（2026-11-12）。EP01 の thumbs.py と同じ作り
#   python3 thumbs.py <絵のフォルダ> <出力フォルダ> <フォント.ttf>
#   絵：3D の字幕・札なしのコマ（いまはクラウドで描いた 1920×1080。本番は PC の 3D のコマに差し替え）
#   素材：PC で描いた本番の 3D（字幕・札なし）。2560×1440 で組んで 1280×720 に縮める（字のふちがきれい）
#   字：Noto Sans CJK JP を太らせて（同じ色のふち）、紺の太いふち＋影。黄色は大事な言葉
import os, math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
import sys
SRC, OUT, FONT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True)
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


SER = "スマホと広告のしくみ"
made = []
# A：スマホの中に 見張り番がいた！（門と番犬とまるロボ）
if os.path.exists(os.path.join(SRC, "gate_0703.png")):
    im = bg("gate_0703.png", zoom=1.25, cx=0.66, cy=0.52, bri=1.15); im = shade(im, "left", 0.60, 0.85)
    im = ribbon(im, (90, 80), SER)
    im, _ = big(im, (100, 330), [("スマホの中に", WHITE)], 180)
    im, _ = big(im, (100, 590), [("見張り番", YEL)], 300)
    im, _ = big(im, (100, 960), [("がいた！", WHITE)], 240)
    made.append(save(im, "thumb_A"))
# B：話しただけなのに 広告が！？（テントの広告が出たスマホ）
im = bg("s02_0169.png", zoom=1.45, cx=0.33, cy=0.55); im = shade(im, "left", 0.62, 0.88)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (100, 330), [("話した", WHITE)], 240)
im, _ = big(im, (100, 600), [("だけなのに", WHITE)], 240)
im, _ = big(im, (100, 900), [("広告", YEL), ("が！？", WHITE)], 300)
made.append(save(im, "thumb_B"))
# C：容疑者は3人（3つの台と探偵のまるロボ）
im = bg("s05_0056.png", zoom=1.0, cx=0.5, cy=0.5, bri=1.7, con=1.1); im = shade(im, "bottom", 0.45, 0.75)
im = ribbon(im, (90, 80), SER)
im, _ = big(im, (W / 2, 960), [("容疑者は ", WHITE), ("3人", YEL)], 300, anchor="c")
im = qmark(im, (2330, 330), 120)
made.append(save(im, "thumb_C"))
# D：テント広告事件 犯人は…？（テントの広告とまるロボ）
im = bg("s22_0098.png", zoom=1.12, cx=0.42, cy=0.66, bri=1.02); im = shade(im, "top", 0.42, 0.85, col=(40, 30, 20))
im = ribbon(im, (90, 60), SER)
im, _ = big(im, (W / 2, 230), [("テント広告", WHITE), ("事件", YEL)], 250, anchor="c")
im, _ = big(im, (W - 70, 1180), [("犯人は…？", WHITE)], 180, anchor="r")
made.append(save(im, "thumb_D"))
# 一覧（大きい・小さい）
sheet = Image.new("RGB", (1280 * 2 + 30, 720 * 2 + 30), (240, 242, 244))
for i, p in enumerate(made): sheet.paste(Image.open(p), ((i % 2) * 1290, (i // 2) * 730))
sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2), Image.LANCZOS).save(OUT + "/sheet_big.jpg", quality=88)
small = Image.new("RGB", (len(made) * 214 + 10, 140), (255, 255, 255))     # スマホの一覧で見える大きさ（約 210×118）
for i, p in enumerate(made): small.paste(Image.open(p).resize((210, 118), Image.LANCZOS), (i * 214 + 4, 10))
small.save(OUT + "/sheet_small.png"); print("\n".join(made))
