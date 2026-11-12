# まとめ（17:05〜18:15）の絵コンテ：これまでの章の絵を使い回して、二つの疑問の答えと三つの工夫をふり返り、
#   最後は止まった電車に戻って、まるロボが時間を元に戻す（主人公はまだ同じ曲で踊っている）
import json, math, sys
from PIL import Image, ImageDraw, ImageFont
SC = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; ST = SC + "/stage"; FONT = ST + "/av/fonts/japanese.ttc"
TL = {e["no"]: e for e in json.load(open(ST + "/script/script_v2_timed.json", encoding="utf-8"))}
TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY, PUR, BG = (31, 94, 102), (52, 168, 96), (214, 64, 60), (214, 128, 44), (40, 46, 52), (250, 250, 248), (150, 158, 166), (118, 92, 170), (238, 242, 245)
S = 2
def F(px): return ImageFont.truetype(FONT, int(px * S))
def P(*xy): return [v * S for v in xy]
def load(path, size=(640 * S, 360 * S)): return Image.open(path).convert("RGB").resize(size, Image.LANCZOS)
def ch0102(t): return load(ST + "/human/anim_ch0102_v2/full/f_%04d.png" % (int(round(t * 24)) + 1))
def ch03(t): return load(ST + "/ch03/anim_v2/full/f_%04d.png" % (int(round((t - 81.0) * 24)) + 1))
def ch04(t): return load(ST + "/ch03/ch04_out/full7/f_%04d.png" % (int(round((t - 175.786) * 24)) + 1))
def ch05(t): return load(ST + "/ch03/ch5_out/ch05/c_%04d.png" % (int(round((t - 426.981) * 24)) + 1))
def questions(i): return load(ST + "/ch03/anim_v2/questions/q_%04d.png" % i)
def sb(path, n):
    src = open(path, encoding="utf-8").read(); src = src[:src.index("f1 = ImageFont.truetype")]
    g = {"__name__": "panels"}; exec(compile(src, path, "exec"), g); return g["panel"](n).resize((640 * S, 360 * S), Image.LANCZOS)
def tag(d, xy, txt, col, px=17):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * S, xy[1] * S
    d.rounded_rectangle([x - w / 2 - 12 * S, y - px * 0.8 * S, x + w / 2 + 12 * S, y + px * 0.8 * S], radius=9 * S, fill=WHITE, outline=col, width=2 * S)
    d.text((x, y), txt, font=f, fill=col, anchor="mm")
def check(d, xy, col=GREEN, r=16):
    x, y = xy; d.ellipse(P(x - r, y - r, x + r, y + r), fill=col); d.line(P(x - 7, y, x - 2, y + 6, x + 8, y - 6), fill=WHITE, width=4 * S)
def card(im, src, box, title, col):
    """src を縮めて box（x0,y0,x1,y1）に置き、上に見出し"""
    x0, y0, x1, y1 = box; w, h = int((x1 - x0) * S), int((y1 - y0) * S)
    im.paste(src.resize((w, h), Image.LANCZOS), (int(x0 * S), int(y0 * S))); d = ImageDraw.Draw(im)
    d.rectangle(P(x0, y0, x1, y1), outline=col, width=3 * S); tag(d, ((x0 + x1) / 2, y0 - 14), title, col, 13)


def panel(n):
    if n == 1:                                    # 179 最初の二つの疑問に戻りましょう
        im = questions(200)
    elif n == 2:                                  # 180 一つ目の疑問は、どうして隣の人の曲が混ざらないのか
        im = questions(200); d = ImageDraw.Draw(im); d.rectangle(P(325, 40, 640, 330), fill=BG); tag(d, (480, 180), "まずは ①", TEAL)
    elif n == 3:                                  # 181 つないだ相手との通信だけを選び、二台だけの鍵で音楽に鍵をかけている
        im = Image.new("RGB", (640 * S, 360 * S), BG)
        card(im, ch04(404.6), (24, 70, 312, 232), "つないだ相手だけを選ぶ（第4章）", TEAL)
        card(im, ch04(421.0), (328, 70, 616, 232), "二台だけの鍵（第4章）", PUR)
        d = ImageDraw.Draw(im); tag(d, (320, 290), "① の答え：つないだ相手を選び、二台だけの鍵をかける", TEAL, 15); check(d, (40, 290))
    elif n == 4:                                  # 182 二つ目の疑問は、どうしてときどき音が途切れるのか
        im = questions(200); d = ImageDraw.Draw(im); d.rectangle(P(0, 40, 318, 330), fill=BG); tag(d, (160, 180), "次は ②", AMBER)
    elif n == 5:                                  # 183 ほかの電波に邪魔されたりして、次に鳴らすデータが間に合わなくなる
        im = Image.new("RGB", (640 * S, 360 * S), BG)
        card(im, ch05(648.0), (24, 70, 312, 232), "ぶつかって届かない（第5章）", RED)
        card(im, sb(SC + "/tools/ch07_storyboard.py", 12), (328, 70, 616, 232), "間に合わず空になる（第7章）", RED)
        d = ImageDraw.Draw(im); tag(d, (320, 290), "② の答え：次に鳴らすデータが間に合わない", AMBER, 15); check(d, (60, 290), AMBER)
    elif n == 6:                                  # 184 周波数をそろえて切り替え、送り直し、先に届いた分をためて、次に備える
        im = Image.new("RGB", (640 * S, 360 * S), BG)
        card(im, ch05(582.0), (16, 92, 214, 204), "そろえて切り替える", TEAL)
        card(im, sb(SC + "/tools/ch06_storyboard.py", 12), (221, 92, 419, 204), "送り直す", AMBER)
        card(im, sb(SC + "/tools/ch07_storyboard.py", 8), (426, 92, 624, 204), "ためて備える", GREEN)
        d = ImageDraw.Draw(im); tag(d, (320, 40), "途切れないための三つの工夫", INK, 16)
        d.text((320 * S, 262 * S), "（第5章）　　　　　（第6章）　　　　　（第7章）", font=F(13), fill=GRAY, anchor="mm")
    elif n == 7:                                  # 185 その工夫が積み重なって、いつもの一曲が続いている
        im = ch03(152.0); d = ImageDraw.Draw(im); tag(d, (320, 44), "工夫が積み重なって、いつもの一曲が続く", TEAL, 16)
    elif n == 8:                                  # 186 お待たせしました
        im = ch0102(66.0); d = ImageDraw.Draw(im); tag(d, (320, 44), "止まった電車に戻る", INK, 16)
    elif n == 9:                                  # 187 時間を、元に戻しましょう
        im = ch0102(60.6); d = ImageDraw.Draw(im); tag(d, (320, 44), "まるロボが一時停止ボタンをもう一度押す → 時間が動き出す", TEAL, 15)
    elif n == 10:                                 # 188 ……この人は、まだこの曲でした
        im = ch0102(31.0); d = ImageDraw.Draw(im); tag(d, (320, 44), "色と音が戻る。主人公は、まだ同じ曲でノリノリ", GREEN, 15)
    elif n == 11:                                 # 189 電車の中では、こんなに踊ってはいけませんよ
        im = ch0102(34.0); d = ImageDraw.Draw(im); tag(d, (320, 44), "まわりの人がちらっと見る → おしまい", INK, 16)
    return im


PANELS = [(1, 179), (2, 180), (3, 181), (4, 182), (5, 183), (6, 184), (7, 185), (8, 186), (9, 187), (10, 188), (11, 189)]
NOTE = {1: "第3章の終わりと同じ「二つの疑問」の画", 2: "① を強く", 3: "① の答え：第4章の「つないだ相手」と「二台だけの鍵」を並べる ✓",
        4: "② を強く", 5: "② の答え：第5章の落ちた荷物と、第7章の空になったタワー", 6: "三つの工夫：第5章（そろえて切り替え）・第6章（送り直し）・第7章（ためる）",
        7: "第3章の舞台で曲が鳴っている（いつもの一曲）", 8: "止まった電車に戻る", 9: "まるロボがボタンをもう一度押す → 時間が動き出す（第2章の逆）",
        10: "色と音が戻り、主人公はまだ同じ曲で踊っている", 11: "まわりがちらっと見る → おしまい"}

f1 = ImageFont.truetype(FONT, 17); f2 = ImageFont.truetype(FONT, 15)
if __name__ == "__main__":
    W, H, CAP, cols = 480, 270, 66, 4
    rows = (len(PANELS) + cols - 1) // cols
    sh = Image.new("RGB", (W * cols, (H + CAP) * rows + 50), "white"); dd = ImageDraw.Draw(sh)
    dd.text((12, 12), "まとめ（17:05〜18:15）絵コンテ　二つの疑問の答え → 三つの工夫 → 時間を元に戻す", font=ImageFont.truetype(FONT, 22), fill=TEAL)
    for j, (n, ln) in enumerate(PANELS):
        im = panel(n).resize((W, H), Image.LANCZOS); x, y = (j % cols) * W, (j // cols) * (H + CAP) + 50; sh.paste(im, (x, y))
        t = TL[ln]["start"]; m, s_ = divmod(t, 60); dd.rectangle((x, y, x + 64, y + 18), fill=TEAL); dd.text((x + 4, y + 1), "%d:%04.1f" % (m, s_), font=f2, fill="white")
        dd.text((x + 6, y + H + 4), "▶ " + NOTE[n][:27], font=f1, fill=TEAL); txt = TL[ln]["text"]
        dd.text((x + 6, y + H + 26), txt[:30], font=f2, fill=(60, 60, 60)); dd.text((x + 6, y + H + 45), txt[30:60], font=f2, fill=(60, 60, 60))
    sh.save(ST + "/ch03/review/summary_storyboard.jpg", quality=88); print("ok")
