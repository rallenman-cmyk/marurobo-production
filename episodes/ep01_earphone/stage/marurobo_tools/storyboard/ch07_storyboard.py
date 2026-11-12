# 第7章（バッファ）の絵コンテ：OK 済みの 30 秒の見本の舞台（貯蔵タワー）の静止画に、札・輪・仮の絵を重ねる
import json, math
from PIL import Image, ImageDraw, ImageFont
ST = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage"
SB = ST + "/ch7_sb"; FONT = ST + "/av/fonts/japanese.ttc"
TL = {e["no"]: e for e in json.load(open(ST + "/script/script_v2_timed.json", encoding="utf-8"))}
TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY = (31, 94, 102), (52, 168, 96), (214, 64, 60), (214, 128, 44), (40, 46, 52), (250, 250, 248), (150, 158, 166)
S = 2
def F(px): return ImageFont.truetype(FONT, px * S)
def base(t): return Image.open("%s/buffer_still_%05.1f.png" % (SB, t)).convert("RGB").resize((640 * S, 360 * S), Image.LANCZOS)
def tag(d, xy, txt, col, px=17):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * S, xy[1] * S
    d.rounded_rectangle([x - w / 2 - 12 * S, y - px * 0.8 * S, x + w / 2 + 12 * S, y + px * 0.8 * S], radius=9 * S, fill=WHITE, outline=col, width=2 * S)
    d.text((x, y), txt, font=f, fill=col, anchor="mm")
def ring(d, c, r, col, w=3): d.ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], outline=col, width=w * S)
def note(d, c, col, sc=1.0):
    x, y = c[0] * S, c[1] * S; s = sc * S
    d.ellipse([x - 7 * s, y + 5 * s, x + 4 * s, y + 14 * s], fill=col); d.line([(x + 3 * s, y + 9 * s), (x + 3 * s, y - 13 * s)], fill=col, width=int(2.5 * s)); d.line([(x + 3 * s, y - 13 * s), (x + 12 * s, y - 8 * s)], fill=col, width=int(2.5 * s))
def cover(d, box, col=(70, 82, 90)): d.rectangle([v * S for v in box], fill=col)
def gauge(d, xy, n, tot=3, title="タワーの中"):
    x, y = xy; f = F(14); d.text((x * S, (y - 22) * S), title, font=f, fill=INK, anchor="mm")
    for k in range(tot):
        yy = y + (tot - 1 - k) * 22; on = k < n
        d.rounded_rectangle([(x - 26) * S, yy * S, (x + 26) * S, (yy + 18) * S], radius=4 * S, fill=TEAL if on else WHITE, outline=TEAL, width=2 * S)
def wave(d, x0, x1, y, gap=None, col=TEAL):
    for s0, s1 in ([(x0, gap[0]), (gap[1], x1)] if gap else [(x0, x1)]):
        d.line([(x * S, (y + 9 * math.sin((x - x0) / 8.0)) * S) for x in range(int(s0), int(s1), 2)], fill=col, width=3 * S)
    if gap: d.line([((gap[0] + 3) * S, y * S), ((gap[1] - 3) * S, y * S)], fill=GRAY, width=2 * S)
DECK = (405, 250); TOWER = (395, 178)
def panel(n):
    if n == 1: im = base(6.8); d = ImageDraw.Draw(im); tag(d, (320, 330), "イヤホンの中（30秒の見本と同じ舞台）", TEAL)
    elif n == 2: im = base(2.0); d = ImageDraw.Draw(im); ring(d, (DECK[0] - 5, DECK[1] + 5), 34, GREEN, 4); tag(d, (250, 290), "04：いま鳴っている", GREEN)
    elif n == 3: im = base(2.0); d = ImageDraw.Draw(im); ring(d, TOWER, 34, TEAL, 4); tag(d, (230, 175), "05：届いて待っている", TEAL)
    elif n == 4: im = base(8.4); d = ImageDraw.Draw(im); ring(d, (415, 250), 34, GREEN, 4); tag(d, (250, 290), "04 が終わったら、05", GREEN); [note(d, (500 + 26 * k, 210 - 14 * k), TEAL, 1.2) for k in range(3)]
    elif n == 5: im = base(13.2); d = ImageDraw.Draw(im); ring(d, (315, 72), 36, AMBER, 4); tag(d, (470, 60), "その間に 06 が到着（再送した分）", AMBER)
    elif n == 6: im = base(15.6); d = ImageDraw.Draw(im); ring(d, (425, 185), 32, TEAL, 4); tag(d, (250, 175), "05 が終わる前に間に合った", GREEN)
    elif n == 7: im = base(26.0); d = ImageDraw.Draw(im); tag(d, (230, 120), "先に受け取ったデータを待たせておく場所", TEAL, 15)
    elif n == 8: im = base(22.0); d = ImageDraw.Draw(im); gauge(d, (560, 70), 1); tag(d, (250, 60), "少し遅れても、先に届いた分を鳴らせる（余裕）", TEAL, 15)
    elif n == 9:
        im = base(22.0); d = ImageDraw.Draw(im); cover(d, (395, 245, 455, 300), (55, 66, 74)); cover(d, (395, 168, 455, 205), (205, 210, 212))
        d.text((425 * S, 186 * S), "07", font=F(16), fill=INK, anchor="mm"); d.text((425 * S, 272 * S), "08", font=F(16), fill=WHITE, anchor="mm")
        tag(d, (200, 60), "今度は 09 がなかなか届かない", RED); d.text((150 * S, 130 * S), "09 …？", font=F(24), fill=RED, anchor="mm")
    elif n == 10:
        im = base(8.4); d = ImageDraw.Draw(im); cover(d, (0, 60, 70, 120), (200, 204, 206)); gauge(d, (560, 70), 1); tag(d, (230, 60), "先に届いていた分が、少しずつ減る", AMBER)
    elif n == 11: im = base(11.0); d = ImageDraw.Draw(im); cover(d, (290, 30, 360, 110), (40, 42, 46)); gauge(d, (560, 70), 0); tag(d, (230, 60), "残りは、鳴っている一つだけ", AMBER)
    elif n == 12:
        im = base(11.0); d = ImageDraw.Draw(im); cover(d, (290, 30, 360, 110), (40, 42, 46)); cover(d, (395, 238, 455, 268), (30, 32, 36))
        wave(d, 120, 330, 300, (210, 250)); tag(d, (300, 60), "次の音が間に合わない → 音が途切れる", RED)
    elif n == 13:
        a = base(15.6).resize((320 * S, 180 * S)); b = base(11.0).resize((320 * S, 180 * S)); im = Image.new("RGB", (640 * S, 360 * S), (238, 242, 245)); im.paste(a, (0, 90 * S)); im.paste(b, (320 * S, 90 * S)); d = ImageDraw.Draw(im)
        tag(d, (160, 50), "遅れたけれど、つなげた ✓", GREEN, 16); tag(d, (480, 50), "つなげる分がなくなった ×", RED, 16); tag(d, (320, 315), "間に合うかどうかで、続けられるかが変わる", TEAL, 15)
    elif n == 14:
        im = Image.open(ST + "/ch03/ch04_out/D8.png").convert("RGB").resize((640 * S, 360 * S), Image.LANCZOS); d = ImageDraw.Draw(im)
        tag(d, (320, 50), "人の体や物にさえぎられて、電波が弱くなることもある", AMBER, 15)
    return im.resize((640, 360), Image.LANCZOS)
PANELS = [(1, 128), (2, 131), (3, 132), (4, 135), (5, 137), (6, 138), (7, 139), (8, 140), (9, 146), (10, 148), (11, 149), (12, 152), (13, 153), (14, 157)]
NOTE = {1: "イヤホンの中：貯蔵タワーと再生装置（30秒の見本の舞台）", 2: "下の再生装置で 04 が鳴っている", 3: "05 はタワーの中で順番を待つ", 4: "04 が終わると 05 が落ちて鳴る。曲は続く",
        5: "その間に、まるロボが 06 を運んでくる", 6: "05 が終わる前に 06 が間に合った", 7: "札「バッファ」（見本と同じ）", 8: "タワーの中の数（目盛り）＝余裕",
        9: "後半：07・08 が入っていて、09 が届かない（番号は描き直す）", 10: "待っている間も鳴り続けて、タワーの中が減っていく", 11: "タワーは空。鳴っているのは最後の一つ",
        12: "再生装置が空になり、灯が消えて音が止まる（第3章の「二つの疑問」②の波）", 13: "二つを並べる：間に合った ✓／間に合わなかった ×", 14: "届きにくい理由はほかにも：人の体や物（電車の画に戻る）"}
f1 = ImageFont.truetype(FONT, 17); f2 = ImageFont.truetype(FONT, 15)
W, H, CAP, cols = 480, 270, 66, 4
rows = (len(PANELS) + cols - 1) // cols
sh = Image.new("RGB", (W * cols, (H + CAP) * rows + 50), "white"); dd = ImageDraw.Draw(sh)
dd.text((12, 12), "第7章（12:11〜15:07）絵コンテ　イヤホンの中の貯蔵タワー＝バッファ（30秒の見本の舞台を使う）", font=ImageFont.truetype(FONT, 22), fill=TEAL)
for j, (n, ln) in enumerate(PANELS):
    im = panel(n).resize((W, H), Image.LANCZOS); x, y = (j % cols) * W, (j // cols) * (H + CAP) + 50; sh.paste(im, (x, y))
    t = TL[ln]["start"]; m, s_ = divmod(t, 60); dd.rectangle((x, y, x + 64, y + 18), fill=TEAL); dd.text((x + 4, y + 1), "%d:%04.1f" % (m, s_), font=f2, fill="white")
    dd.text((x + 6, y + H + 4), "▶ " + NOTE[n][:27], font=f1, fill=TEAL); txt = TL[ln]["text"]
    dd.text((x + 6, y + H + 26), txt[:30], font=f2, fill=(60, 60, 60)); dd.text((x + 6, y + H + 45), txt[30:60], font=f2, fill=(60, 60, 60))
sh.save(ST + "/ch03/review/ch07_storyboard.jpg", quality=88); print("ok")
