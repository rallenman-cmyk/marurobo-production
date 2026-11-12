# 第4章の図（A案）の見本：C13 と同じ描き方で、上に自分の組、下に隣の組。電波は両方のイヤホンに届き、受付口は印を確かめる
# 使い方: python3 ch04_concept.py OUT.jpg
import sys, os, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.join(HERE, "..", "av", "fonts", "japanese.ttc")
W, H, S = 1280, 720, 2
BG = (238, 242, 245); INK = (40, 46, 52); TEAL = (31, 94, 102); CYAN = (63, 198, 201); AMBER = (214, 128, 44); GRAY = (150, 158, 166)


def font(px): return ImageFont.truetype(FONT, int(px * S))


def rr(d, box, r, **kw):
    if "width" in kw: kw["width"] = int(kw["width"] * S)
    d.rounded_rectangle([v * S for v in box], radius=r * S, **kw)


def phone(d, x, y, col):
    rr(d, (x - 40, y - 76, x + 40, y + 76), 12, fill=INK); rr(d, (x - 33, y - 68, x + 33, y + 68), 7, fill=(23, 27, 32))
    for k in range(20):
        c = tuple(int(a + (b - a) * k / 19) for a, b in zip(col[0], col[1])); d.rectangle([(x - 25) * S, (y - 58 + k * 2.4) * S, (x + 25) * S, (y - 58 + (k + 1) * 2.4) * S], fill=c)


def bud(d, x, y, mark, col):
    d.ellipse([(x - 46) * S, (y - 54) * S, (x + 34) * S, (y + 14) * S], fill=(250, 250, 248), outline=(205, 210, 215), width=3 * S)
    rr(d, (x - 5, y - 2, x + 19, y + 86), 12, fill=(250, 250, 248), outline=(205, 210, 215), width=3)
    d.ellipse([(x - 58) * S, (y - 36) * S, (x - 36) * S, (y - 10) * S], fill=(205, 212, 218))
    rr(d, (x - 1, y + 34, x + 15, y + 54), 4, fill=col)                                      # 受付口
    sym(d, x + 7, y + 104, mark, col, 13)


def sym(d, x, y, mark, col, r, width=4):
    if mark == "o": d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], outline=col, width=width * S)
    else:
        pts = [(x, y - r * 1.15), (x - r * 1.05, y + r * 0.75), (x + r * 1.05, y + r * 0.75)]
        d.polygon([(px * S, py * S) for px, py in pts], outline=col, width=width * S)


def parcel(d, x, y, mark, col, sc=1.0, faded=False):
    c0 = col if not faded else tuple(int(v * 0.35 + 238 * 0.65) for v in col)
    rr(d, (x - 34 * sc, y - 23 * sc, x + 34 * sc, y + 23 * sc), 7 * sc, fill=c0)
    rr(d, (x - 28 * sc, y - 18 * sc, x + 28 * sc, y + 18 * sc), 4 * sc, fill=(42, 45, 49) if not faded else (200, 204, 208))
    sym(d, x - 10 * sc, y - 4 * sc, mark, (233, 236, 238), 8 * sc, 3)


def rings(d, cx, cy, r_max, col, n=5):
    for k in range(n):
        r = r_max * (k + 1) / n; a = int(255 * (1 - k / n) * 0.55)
        c = tuple(int(BG[i] + (col[i] - BG[i]) * a / 255) for i in range(3))
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], outline=c, width=3 * S)


def panel(title, draw_fn):
    im = Image.new("RGB", (W * S, H * S), BG); d = ImageDraw.Draw(im)
    draw_fn(d)
    d.text((40 * S, 30 * S), title, font=font(30), fill=INK)
    return im.resize((W, H), Image.LANCZOS)


TOP, BOT = 230, 520; PX, EX = 260, 1010
A_COL = ((45, 172, 205), (232, 110, 160)); B_COL = ((242, 168, 64), (112, 72, 168))


def base(d, top_lab=True):
    phone(d, PX, TOP, A_COL); bud(d, EX, TOP - 30, "o", TEAL); phone(d, PX, BOT, B_COL); bud(d, EX, BOT - 30, "t", AMBER)
    if top_lab:
        d.text((90 * S, TOP * S), "自分の組", font=font(24), fill=TEAL, anchor="lm"); d.text((90 * S, BOT * S), "隣の組", font=font(24), fill=AMBER, anchor="lm")


def p1(d):
    base(d)
    for y, col in ((TOP, TEAL), (BOT, AMBER)):
        d.line([(PX + 70) * S, y * S, (EX - 110) * S, y * S], fill=col, width=5 * S)


def p2(d):
    base(d); rings(d, PX, TOP, 820, TEAL, 6)
    d.text((640 * S, 650 * S), "電波は、隣のイヤホンのところにも届く", font=font(26), fill=INK, anchor="mm")


def p3(d):
    base(d)
    parcel(d, EX - 150, TOP - 80, "o", TEAL); parcel(d, EX - 150, TOP + 20, "t", AMBER, faded=True)
    d.line([(EX - 110) * S, (TOP - 80) * S, (EX - 10) * S, (TOP + 14) * S], fill=TEAL, width=4 * S)
    d.text(((EX - 150) * S, (TOP + 70) * S), "×", font=font(34), fill=GRAY, anchor="mm")
    parcel(d, EX - 150, BOT - 80, "t", AMBER); parcel(d, EX - 150, BOT + 20, "o", TEAL, faded=True)
    d.line([(EX - 110) * S, (BOT - 80) * S, (EX - 10) * S, (BOT + 14) * S], fill=AMBER, width=4 * S)
    d.text(((EX - 150) * S, (BOT + 70) * S), "×", font=font(34), fill=GRAY, anchor="mm")
    d.text((640 * S, 670 * S), "受付口は印を確かめ、つないだ相手のものだけを鳴らす", font=font(26), fill=INK, anchor="mm")


def p4(d):
    base(d, top_lab=False)
    for x in (PX + 90, EX - 120):                                     # ペアリング：同じ鍵を二台が持つ
        d.ellipse([(x - 16) * S, (TOP - 120) * S, (x + 16) * S, (TOP - 88) * S], outline=TEAL, width=5 * S)
        d.line([(x + 16) * S, (TOP - 104) * S, (x + 60) * S, (TOP - 104) * S], fill=TEAL, width=5 * S)
        d.line([(x + 50) * S, (TOP - 104) * S, (x + 50) * S, (TOP - 92) * S], fill=TEAL, width=5 * S)
    parcel(d, 640, TOP, "o", TEAL, 1.3); rr(d, (622, TOP + 26, 658, TOP + 52), 5, fill=TEAL)
    d.text((640 * S, (TOP - 150) * S), "ペアリングで、同じ鍵を持つ", font=font(26), fill=TEAL, anchor="mm")
    d.text((640 * S, (BOT + 120) * S), "隣のイヤホンには開けられない", font=font(26), fill=AMBER, anchor="mm")


panels = [panel("D2 上が自分の組、下が隣の組", p1), panel("D3 電波はまわり一面に広がる", p2), panel("D5 印を確かめる（○は鳴らす、△は鳴らさない）", p3),
          panel("D7 ペアリングと鍵", p4)]
sheet = Image.new("RGB", (W * 2 // 2 * 2 // 2 * 2, H * 2), (20, 22, 26)); sheet = Image.new("RGB", (W, H), (20, 22, 26))
out = Image.new("RGB", (W * 2, H * 2), (20, 22, 26))
for i, p in enumerate(panels): out.paste(p, ((i % 2) * W, (i // 2) * H))
out = out.resize((W * 2 * 3 // 4, H * 2 * 3 // 4), Image.LANCZOS)
out.save(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "review", "ch04_concept_A.jpg"), quality=88); print("ok")
