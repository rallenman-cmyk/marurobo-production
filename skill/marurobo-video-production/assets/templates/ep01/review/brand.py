# チャンネルの案（名前＋バナー＋アイコン）を 3 組（2026-11-09）
#   バナー：2560×1440。スマホ・パソコンで見えるのは真ん中の 1546×423（x 507〜2053・y 508〜931）だけなので、名前と言葉はその中へ。
#   パソコンでは横いっぱい（2560×423）、テレビでは全体が見える。アイコン：800×800（丸く切って表示される）
import os, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageChops
S = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; SRC = S + "/work_thumb/src"; OUT = S + "/work_brand"
FONT = S + "/stage/av/fonts/japanese.ttc"
NAVY, YEL, WHITE, TEAL, TEAL2, TEAL3, INK = (16, 30, 52), (255, 214, 48), (255, 255, 255), (20, 98, 106), (38, 160, 160), (12, 64, 72), (34, 44, 56)
BW, BH = 2560, 1440; SAFE = (507, 508, 2053, 931)
def F(px): return ImageFont.truetype(FONT, px, index=0)


def src(name, w, h, zoom=1.0, cx=0.5, cy=0.5, sat=1.1, con=1.05, bri=1.0):
    im = Image.open(os.path.join(SRC, name)).convert("RGB"); W0, H0 = im.size
    ar = w / h; cw = W0 / zoom; ch = cw / ar
    if ch > H0 / zoom: ch = H0 / zoom; cw = ch * ar
    x0 = min(max(cx * W0 - cw / 2, 0), W0 - cw); y0 = min(max(cy * H0 - ch / 2, 0), H0 - ch)
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat); im = ImageEnhance.Contrast(im).enhance(con); im = ImageEnhance.Brightness(im).enhance(bri)
    return im.convert("RGBA")


def text(im, xy, runs, px, anchor="l", bold=None, out=None, outcol=NAVY, shadow=True):
    W, H = im.size; bold = bold if bold is not None else max(2, int(px * 0.032)); out = out if out is not None else int(px * 0.11)
    f = F(px); ws = []
    for t, _ in runs:
        b = f.getbbox(t, stroke_width=bold); ws.append(b[2] - b[0])
    tw = sum(ws); x, y = xy
    if anchor == "c": x -= tw / 2
    elif anchor == "r": x -= tw
    sh, ol, fg = (Image.new("RGBA", (W, H), (0, 0, 0, 0)) for _ in range(3))
    ds, do, df = ImageDraw.Draw(sh), ImageDraw.Draw(ol), ImageDraw.Draw(fg); cx = x
    for (t, col), w_ in zip(runs, ws):
        top = -f.getbbox(t, stroke_width=bold)[1]
        if shadow: ds.text((cx + px * 0.03, y + top + px * 0.05), t, font=f, fill=(0, 0, 0, 130), stroke_width=bold + out, stroke_fill=(0, 0, 0, 130))
        if out > 0: do.text((cx, y + top), t, font=f, fill=outcol + (255,), stroke_width=bold + out, stroke_fill=outcol + (255,))
        df.text((cx, y + top), t, font=f, fill=col + (255,), stroke_width=bold, stroke_fill=col + (255,)); cx += w_
    if shadow: im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(px * 0.03)))
    if out > 0: im = Image.alpha_composite(im, ol)
    return Image.alpha_composite(im, fg), tw


def circle_photo(im, name, c, r, ring=TEAL2, zoom=1.0, cx=0.5, cy=0.5, ringw=14):
    ph = src(name, 2 * r, 2 * r, zoom=zoom, cx=cx, cy=cy)
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse((c[0] - r - ringw, c[1] - r - ringw, c[0] + r + ringw, c[1] + r + ringw), fill=ring + (255,))
    lay.paste(ph, (c[0] - r, c[1] - r), m)
    return Image.alpha_composite(im, lay)


def lens_icon(size, bg=TEAL, ring=(14, 70, 78)):
    """まるロボの目（白い体・青緑のレンズ・黒いひとみ・光）を図にしたアイコン"""
    k = 4; s = size * k; im = Image.new("RGBA", (s, s), bg + (255,)); d = ImageDraw.Draw(im); c = s / 2
    def circ(r, col, dx=0, dy=0): d.ellipse((c - r + dx, c - r + dy, c + r + dx, c + r + dy), fill=col)
    circ(s * 0.40, (245, 247, 248), dx=-s * 0.02, dy=s * 0.02)                       # 白い体
    circ(s * 0.27, ring); circ(s * 0.235, (28, 132, 140)); circ(s * 0.205, (12, 28, 36))   # レンズの縁・青緑・黒
    d.ellipse((c - s * 0.14, c - s * 0.14, c + s * 0.14, c + s * 0.14), outline=(170, 225, 230), width=int(s * 0.022))   # 光の輪
    circ(s * 0.045, (255, 255, 255), dx=s * 0.07, dy=-s * 0.075)                     # 光
    circ(s * 0.04, (28, 132, 140), dx=s * 0.30, dy=-s * 0.05)                        # 横の小さなレンズ（耳）
    return im.resize((size, size), Image.LANCZOS)


def guides(im):
    """確認用：スマホ・パソコンで見える範囲の線"""
    g = im.copy(); d = ImageDraw.Draw(g)
    d.rectangle((0, SAFE[1], BW - 1, SAFE[3]), outline=(255, 80, 80, 255), width=6)
    d.rectangle(SAFE, outline=(255, 214, 48, 255), width=6)
    return g


def save(im, name, q=92):
    p = os.path.join(OUT, name); im.convert("RGB").save(p, quality=q, optimize=True); return p


made = {}
# ---------------------------------------------------------------- 案1「まるロボのしくみ探検」：荷物を運ぶまるロボと巨大イヤホン（場面）
b = src("c3_0836.png", BW, BH, zoom=1.2, cx=0.433, cy=0.559, sat=1.12)
sky = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(sky)
for y in range(BH): d.line([(0, y), (BW, y)], fill=(8, 30, 48, int(120 * max(0, 1 - abs(y - 720) / 420))))
b = Image.alpha_composite(b, sky)
b, tw = text(b, (1530, 535), [("まるロボの", WHITE)], 110, anchor="c")
b, tw = text(b, (1530, 652), [("しくみ", YEL), ("探検", WHITE)], 178, anchor="c")
b, tw = text(b, (1530, 858), [("毎日つかう機械の “なか” へ", WHITE)], 56, anchor="c", out=8)
made["banner_1"] = save(b, "banner_1_tanken.jpg"); save(guides(b), "banner_1_tanken_guide.jpg", 80)
ic = src("c3_0620.png", 800, 800, zoom=1.40, cx=0.555, cy=0.55, bri=1.04)
m = Image.new("L", (800, 800), 0); ImageDraw.Draw(m).ellipse((0, 0, 799, 799), fill=255)
made["icon_1"] = save(ic, "icon_1_photo.jpg")
# ---------------------------------------------------------------- 案2「まるわかり！まるロボ」：青緑の図（電波の輪）＋まるロボの顔
b = Image.new("RGBA", (BW, BH), TEAL3 + (255,)); d = ImageDraw.Draw(b)
for y in range(BH):
    u = y / BH; col = tuple(int(TEAL3[i] + (TEAL[i] - TEAL3[i]) * (1 - abs(u - 0.5) * 2)) for i in range(3)); d.line([(0, y), (BW, y)], fill=col + (255,))
rings = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); dr = ImageDraw.Draw(rings); C0 = (760, 720)
for k in range(1, 14):
    r = 230 + k * 120; dr.ellipse((C0[0] - r, C0[1] - r, C0[0] + r, C0[1] + r), outline=(255, 255, 255, max(0, 70 - k * 5)), width=6)
b = Image.alpha_composite(b, rings)
b = circle_photo(b, "c3_0620.png", C0, 190, ring=WHITE, zoom=1.40, cx=0.53, cy=0.56, ringw=12)
b, tw = text(b, (1010, 540), [("まるわかり！", YEL)], 110, out=12)
b, tw = text(b, (1010, 652), [("まるロボ", WHITE)], 185, out=16)
b, tw = text(b, (1016, 866), [("スマホ・イヤホンのしくみを 3D で", WHITE)], 50, out=0, shadow=False)
made["banner_2"] = save(b, "banner_2_maruwakari.jpg"); save(guides(b), "banner_2_maruwakari_guide.jpg", 80)
made["icon_2"] = save(lens_icon(800), "icon_2_lens.jpg")
# ---------------------------------------------------------------- 案3「まるロボラボ」：白い方眼（実験ノート）＋のぞくまるロボ
b = Image.new("RGBA", (BW, BH), (244, 247, 248, 255)); d = ImageDraw.Draw(b)
for x in range(0, BW, 64): d.line([(x, 0), (x, BH)], fill=(214, 228, 232, 255), width=2 if x % 320 else 4)
for y in range(0, BH, 64): d.line([(0, y), (BW, y)], fill=(214, 228, 232, 255), width=2 if y % 320 else 4)
d.rectangle((0, 900, BW, BH), fill=TEAL + (255,))
b = circle_photo(b, "c6_0480.png", (1850, 716), 178, ring=TEAL, zoom=1.93, cx=0.47, cy=0.72, ringw=12)
b, tw = text(b, (590, 585), [("まるロボ", TEAL)], 158, out=0, shadow=False)
b, tw = text(b, (590 + tw + 24, 585), [("ラボ", INK)], 158, out=0, shadow=False)
b, tw = text(b, (596, 800), [("デジタル機器のしくみを、3D で実験・解説", INK)], 46, out=0, shadow=False)
made["banner_3"] = save(b, "banner_3_labo.jpg"); save(guides(b), "banner_3_labo_guide.jpg", 80)
ic = Image.new("RGBA", (800, 800), TEAL + (255,))
ph = src("o2_1300.png", 640, 640, zoom=2.08, cx=0.47, cy=0.45, bri=1.05)
mm = Image.new("L", (640, 640), 0); ImageDraw.Draw(mm).ellipse((0, 0, 639, 639), fill=255)
ic.paste(ph, (80, 80), mm)
made["icon_3"] = save(ic, "icon_3_robot.jpg")
print("\n".join("%s %s" % kv for kv in made.items()))
