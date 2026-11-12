# 第6章（送り直し）の絵コンテ：第3章の舞台の静止画（番号 06・07・08）に、返事・待ち時間・×✓・札を重ねる
import json, math, os
from PIL import Image, ImageDraw, ImageFont
ST = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage"
SB = ST + "/ch03/ch6_sb"; FONT = ST + "/av/fonts/japanese.ttc"
TL = {e["no"]: e for e in json.load(open(ST + "/script/script_v2_timed.json", encoding="utf-8"))}
TEAL, GREEN, RED, AMBER, INK, WHITE = (31, 94, 102), (52, 168, 96), (214, 64, 60), (214, 128, 44), (40, 46, 52), (250, 250, 248)
S = 2
def F(px): return ImageFont.truetype(FONT, px * S)
def base(name, lamp="green"): return Image.open("%s/%s/still_%s.png" % (SB, lamp, name)).convert("RGB").resize((640 * S, 360 * S), Image.LANCZOS)
def tag(d, xy, txt, col, px=17):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * S, xy[1] * S
    d.rounded_rectangle([x - w / 2 - 12 * S, y - px * 0.8 * S, x + w / 2 + 12 * S, y + px * 0.8 * S], radius=9 * S, fill=WHITE, outline=col, width=2 * S)
    d.text((x, y), txt, font=f, fill=col, anchor="mm")
def ring(d, c, r, col, w=3): d.ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], outline=col, width=w * S)
def mark(d, c, r, ok):
    col = GREEN if ok else RED; d.ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], fill=col)
    if ok: d.line([((c[0] - r * .45) * S, (c[1]) * S), ((c[0] - r * .1) * S, (c[1] + r * .35) * S), ((c[0] + r * .48) * S, (c[1] - r * .35) * S)], fill=WHITE, width=int(r * .2 * S))
    else:
        for sg in (1, -1): d.line([((c[0] - r * .42) * S, (c[1] - sg * r * .42) * S), ((c[0] + r * .42) * S, (c[1] + sg * r * .42) * S)], fill=WHITE, width=int(r * .2 * S))
def arc(d, a, b, col, dashed, h=70, w=3):
    pts = []
    for i in range(41):
        u = i / 40; x = a[0] + (b[0] - a[0]) * u; y = a[1] + (b[1] - a[1]) * u - h * 4 * u * (1 - u); pts.append((x * S, y * S))
    if dashed:
        for i in range(0, 40, 2): d.line([pts[i], pts[i + 1]], fill=col, width=w * S)
    else: d.line(pts, fill=col, width=w * S, joint="curve")
    x1, y1 = pts[-1]; x0, y0 = pts[-3]; ang = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1, y1), (x1 - 14 * S * math.cos(ang - .45), y1 - 14 * S * math.sin(ang - .45)), (x1 - 14 * S * math.cos(ang + .45), y1 - 14 * S * math.sin(ang + .45))], fill=col)
    return pts[20][0] / S, pts[20][1] / S
def bubble(d, c, txt, col, dashed):
    f = F(16); w = d.textlength(txt, font=f); x, y = c[0] * S, c[1] * S
    box = [x - w / 2 - 12 * S, y - 16 * S, x + w / 2 + 12 * S, y + 16 * S]
    d.rounded_rectangle(box, radius=10 * S, fill=WHITE if not dashed else (250, 250, 248), outline=col, width=2 * S)
    d.text((x, y), txt, font=f, fill=col, anchor="mm")
def note(d, c, col, sc=1.0):
    x, y = c[0] * S, c[1] * S; s = sc * S
    d.ellipse([x - 7 * s, y + 5 * s, x + 4 * s, y + 14 * s], fill=col); d.line([(x + 3 * s, y + 9 * s), (x + 3 * s, y - 13 * s)], fill=col, width=int(2.5 * s)); d.line([(x + 3 * s, y - 13 * s), (x + 12 * s, y - 8 * s)], fill=col, width=int(2.5 * s))
PH, EB = (63, 185), (497, 196)                # 引きの画（still 53.00）でのスマホと受付ボックス
LAMP = (380, 73)                               # 受付の灯（still 51.50）
P06 = (405, 246)                               # 窓の中の 06 の札（still 08.00）
def panel(n):
    if n == 1: im = base("53.00"); d = ImageDraw.Draw(im); tag(d, (320, 40), "まるロボの配達に戻る", TEAL)
    elif n == 2: im = base("08.00"); d = ImageDraw.Draw(im); ring(d, P06, 42, TEAL, 4); tag(d, (P06[0], P06[1] - 70), "六番の荷物", TEAL)
    elif n == 3: im = base("28.00"); d = ImageDraw.Draw(im); tag(d, (470, 60), "06 を載せて出発", TEAL)
    elif n == 4:
        im = base("47.50"); d = ImageDraw.Draw(im)
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); od.rectangle([215 * S, 128 * S, 300 * S, 142 * S], fill=(140, 255, 170, 150))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(im); tag(d, (255, 55), "誤りがないか確かめる", TEAL)
    elif n == 5:
        im = base("53.00"); d = ImageDraw.Draw(im); m = arc(d, EB, PH, GREEN, True, 90); bubble(d, (m[0], m[1] - 26), "届いたよ", GREEN, True); tag(d, (320, 330), "受け取れたら、スマホに返事", GREEN)
    elif n == 6: im = base("51.50", "red"); d = ImageDraw.Draw(im); ring(d, LAMP, 14, RED, 3); mark(d, (LAMP[0] + 40, LAMP[1] + 30), 16, False); tag(d, (300, 50), "誤りがあった（受け取れない）", RED)
    elif n == 7:
        im = base("08.00"); d = ImageDraw.Draw(im); c = (585, 60)
        d.ellipse([(c[0] - 15) * S, (c[1] - 15) * S, (c[0] + 15) * S, (c[1] + 15) * S], fill=(70, 76, 84), outline=WHITE, width=2 * S)
        d.arc([(c[0] - 26) * S, (c[1] - 26) * S, (c[0] + 26) * S, (c[1] + 26) * S], -90, 250, fill=AMBER, width=5 * S)
        d.text(((c[0] - 52) * S, c[1] * S), "？", font=F(30), fill=AMBER, anchor="mm"); tag(d, (470, 115), "返事が来ない（待ち時間が過ぎる）", AMBER)
    elif n == 8: im = base("08.00"); d = ImageDraw.Draw(im); ring(d, P06, 42, AMBER, 4); tag(d, (P06[0] - 10, P06[1] - 70), "スマホに残しておいた 06", AMBER)
    elif n == 9: im = base("32.50"); d = ImageDraw.Draw(im); tag(d, (440, 60), "同じ 06 を、もう一度", AMBER)
    elif n == 10: im = base("51.50"); d = ImageDraw.Draw(im); ring(d, LAMP, 14, GREEN, 3); mark(d, (LAMP[0] + 40, LAMP[1] + 30), 16, True); tag(d, (300, 50), "今度は受け取れた", GREEN)
    elif n == 11:
        im = base("53.00"); d = ImageDraw.Draw(im); m = arc(d, EB, PH, GREEN, False, 90); bubble(d, (m[0], m[1] - 26), "届いたよ", GREEN, False)
        d.ellipse([(PH[0] - 9) * S, (PH[1] - 52) * S, (PH[0] + 9) * S, (PH[1] - 34) * S], fill=GREEN)
    elif n == 12: im = base("53.00"); d = ImageDraw.Draw(im); tag(d, (320, 80), "再送（さいそう）", TEAL, 26)
    elif n == 13:
        im = base("08.00"); d = ImageDraw.Draw(im); f = F(18); x0 = 150
        for j, (txt, col) in enumerate((("06 ×", RED), ("06 ✓", GREEN), ("07", INK), ("08", INK))):
            x = x0 + j * 100; d.rounded_rectangle([(x - 36) * S, 18 * S, (x + 36) * S, 50 * S], radius=8 * S, fill=WHITE, outline=col, width=2 * S); d.text((x * S, 34 * S), txt, font=f, fill=col, anchor="mm")
            if j < 3: d.text(((x + 50) * S, 34 * S), "→", font=f, fill=INK, anchor="mm")
        tag(d, (300, 80), "新しい曲ではなく、受け取れなかった分をもう一度", TEAL, 15)
    elif n == 14:
        im = base("51.50"); d = ImageDraw.Draw(im)
        for k, (dx, dy) in enumerate(((560, 60), (600, 110), (520, 30), (610, 30))): note(d, (dx, dy), TEAL, 1.4 - 0.15 * k)
        tag(d, (300, 50), "曲は、ずっと続いていた", TEAL)
    elif n == 15: im = base("21.50"); d = ImageDraw.Draw(im); d.text((420 * S, 60 * S), "？", font=F(40), fill=TEAL, anchor="mm"); tag(d, (330, 330), "次はイヤホンの中へ（第7章）", TEAL)
    return im.resize((640, 360), Image.LANCZOS)
PANELS = [(1, 114), (2, 115), (3, 115), (4, 116), (5, 117), (6, 118), (7, 119), (8, 120), (9, 121), (10, 122), (11, 122), (12, 123), (13, 124), (14, 125), (15, 127)]
NOTE = {1: "第3章の舞台に戻る（引き）", 2: "窓の中の 06・07・08。06 を追いかける", 3: "06 を載せて出発（道のりは第3章のように短いカットで）", 4: "受付ボックスの中で、光が荷物をなぞって調べる",
        5: "受け取れたら、返事の合図（光）がスマホへ飛ぶ…（説明）", 6: "今回は誤り：受付の灯が赤", 7: "スマホの返事ランプは消えたまま。待ち時間の輪が一周して「？」",
        8: "06 はスマホに残してある（返事が来るまで消さない）", 9: "同じ 06 を、もう一度運ぶ", 10: "今度は受付の灯が緑", 11: "返事の合図がスマホへ。スマホの返事ランプが緑",
        12: "札「再送」", 13: "06 × → 06 ✓ → 07 → 08（新しい曲ではない）", 14: "まるロボは曲に合わせて揺れている（曲はずっと鳴っていた）", 15: "巨大イヤホンへ寄って「？」→ 第7章「イヤホンの中」"}
f1 = ImageFont.truetype(FONT, 17); f2 = ImageFont.truetype(FONT, 15)
W, H, CAP, cols = 480, 270, 66, 4
rows = (len(PANELS) + cols - 1) // cols
sh = Image.new("RGB", (W * cols, (H + CAP) * rows + 50), "white"); d = ImageDraw.Draw(sh)
d.text((12, 12), "第6章（10:55〜12:11）絵コンテ　第3章の舞台で、六番の荷物を追いかける（送り直し＝再送）", font=ImageFont.truetype(FONT, 22), fill=TEAL)
for j, (n, ln) in enumerate(PANELS):
    im = panel(n).resize((W, H), Image.LANCZOS); x, y = (j % cols) * W, (j // cols) * (H + CAP) + 50; sh.paste(im, (x, y))
    t = TL[ln]["start"]; m, s_ = divmod(t, 60); d.rectangle((x, y, x + 64, y + 18), fill=TEAL); d.text((x + 4, y + 1), "%d:%04.1f" % (m, s_), font=f2, fill="white")
    d.text((x + 6, y + H + 4), "▶ " + NOTE[n][:27], font=f1, fill=TEAL); txt = TL[ln]["text"]
    d.text((x + 6, y + H + 26), txt[:30], font=f2, fill=(60, 60, 60)); d.text((x + 6, y + H + 45), txt[30:60], font=f2, fill=(60, 60, 60))
sh.save(ST + "/ch03/review/ch06_storyboard.jpg", quality=88); print("ok")
