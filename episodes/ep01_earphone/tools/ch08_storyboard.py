# 第8章（15:06〜17:05：ためる余裕と、すぐ鳴ること）の絵コンテ
#   前半：第7章の貯蔵タワー（30秒の見本の舞台）の静止画に、札・目盛り・時間の帯を重ねる（もっとためれば？ → 余裕は増えるが、鳴るのが遅い）
#   後半：ゲームの例（OK 済みの案）。第1〜2章のピクトグラムの人（主人公：紺白しま・黄色いキャップ・点の目）がゲームの中でパンチを出し、
#         下の「操作 → 音」の時間の帯で、音が遅れて届く様子を見せる。最後に「途切れにくい」と「すぐ返る」の両方を考える
import json, math
from PIL import Image, ImageDraw, ImageFont
ST = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage"
SB = ST + "/ch7_sb"; FONT = ST + "/av/fonts/japanese.ttc"
TL = {e["no"]: e for e in json.load(open(ST + "/script/script_v2_timed.json", encoding="utf-8"))}
TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY = (31, 94, 102), (52, 168, 96), (214, 64, 60), (214, 128, 44), (40, 46, 52), (250, 250, 248), (150, 158, 166)
NAVY, YELLOW, BG, PUR = (36, 52, 92), (240, 198, 56), (238, 242, 245), (118, 92, 170)
S = 2
def F(px): return ImageFont.truetype(FONT, int(px * S))
def P(*xy): return [v * S for v in xy]
def base(t): return Image.open("%s/buffer_still_%05.1f.png" % (SB, t)).convert("RGB").resize((640 * S, 360 * S), Image.LANCZOS)
def blank(): return Image.new("RGB", (640 * S, 360 * S), BG)
def tag(d, xy, txt, col, px=17, fill=WHITE):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * S, xy[1] * S
    d.rounded_rectangle([x - w / 2 - 12 * S, y - px * 0.8 * S, x + w / 2 + 12 * S, y + px * 0.8 * S], radius=9 * S, fill=fill, outline=col, width=2 * S)
    d.text((x, y), txt, font=f, fill=col, anchor="mm")
def text(d, xy, txt, col=INK, px=16, anchor="mm"): d.text((xy[0] * S, xy[1] * S), txt, font=F(px), fill=col, anchor=anchor)
def ring(d, c, r, col, w=3): d.ellipse(P(c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col, width=w * S)
def gauge(d, xy, n, tot, title="タワーの中", col=TEAL):
    x, y = xy; text(d, (x, y - 20), title, INK, 13)
    for k in range(tot):
        yy = y + (tot - 1 - k) * 15; on = k < n
        d.rounded_rectangle(P(x - 24, yy, x + 24, yy + 12), radius=3 * S, fill=col if on else WHITE, outline=col, width=2 * S)


def strip(d, y, marks, title="", x0=70, x1=590, gap=None, unit=None):
    """時間の帯：左から右へ。marks＝[(x, ラベル, 色, 形)]（形：tap＝押す・hit＝当たる・snd＝音・play＝再生）。gap＝(xa, xb, ラベル) で赤い括弧"""
    d.line(P(x0, y, x1, y), fill=GRAY, width=3 * S); d.polygon(P(x1 + 10, y, x1 - 2, y - 6, x1 - 2, y + 6), fill=GRAY)
    text(d, (x1 + 4, y + 16), "時間", GRAY, 12, "rm")
    if title: text(d, (x0, y - 26), title, INK, 14, "lm")
    for x, lab, col, kind in marks:
        if kind == "tap":
            d.ellipse(P(x - 9, y - 9, x + 9, y + 9), fill=col); d.ellipse(P(x - 4, y - 4, x + 4, y + 4), fill=WHITE)
        elif kind == "hit":
            pts = []
            for k in range(10):
                r = 12 if k % 2 == 0 else 5; a = math.pi / 2 + k * math.pi / 5; pts += [x + r * math.cos(a), y - r * math.sin(a)]
            d.polygon(P(*pts), fill=col)
        elif kind == "snd":
            d.ellipse(P(x - 5, y - 5, x + 5, y + 5), fill=col)
            for r in (10, 16): d.arc(P(x - r, y - r, x + r, y + r), -50, 50, fill=col, width=2 * S)
        else:
            d.polygon(P(x - 6, y - 8, x - 6, y + 8, x + 8, y), fill=col)
        text(d, (x, y + 22), lab, col, 13)
    if gap:
        xa, xb, lab = gap; yb = y - 18
        d.line(P(xa, yb, xb, yb), fill=RED, width=2 * S); d.line(P(xa, yb - 5, xa, yb + 5), fill=RED, width=2 * S); d.line(P(xb, yb - 5, xb, yb + 5), fill=RED, width=2 * S)
        text(d, ((xa + xb) / 2, yb - 12), lab, RED, 13)


def fighter(d, x, y, punch=0.0, sc=1.0, face=0):
    """ゲームの中のピクトグラムの人（主人公と同じ：白い体・紺白しまの上着・黄色いキャップ・点の目）。punch＝0〜1（右の腕が前へ伸びる）"""
    s = sc
    d.ellipse(P(x - 16 * s, y - 72 * s, x + 16 * s, y - 40 * s), fill=WHITE, outline=(200, 205, 210), width=S)        # 頭
    d.chord(P(x - 17 * s, y - 76 * s, x + 17 * s, y - 50 * s), 180, 360, fill=YELLOW); d.rectangle(P(x, y - 64 * s, x + 24 * s, y - 60 * s), fill=YELLOW)  # キャップ（つばは前＝右）
    ex = 4 if face == 0 else 6
    d.ellipse(P(x + ex * s, y - 58 * s, x + (ex + 4) * s, y - 53 * s), fill=INK); d.ellipse(P(x + (ex + 7) * s, y - 58 * s, x + (ex + 11) * s, y - 53 * s), fill=INK)
    d.rounded_rectangle(P(x - 15 * s, y - 40 * s, x + 15 * s, y + 2 * s), radius=8 * S, fill=WHITE)                    # 上着（しま）
    for k in range(5): d.rectangle(P(x - 15 * s, y - 36 * s + k * 8 * s, x + 15 * s, y - 32 * s + k * 8 * s), fill=NAVY)
    d.line(P(x - 8 * s, y + 2 * s, x - 14 * s, y + 34 * s), fill=WHITE, width=int(9 * s * S)); d.line(P(x + 8 * s, y + 2 * s, x + 14 * s, y + 34 * s), fill=WHITE, width=int(9 * s * S))   # 脚
    d.line(P(x - 10 * s, y - 30 * s, x - 22 * s, y - 14 * s), fill=NAVY, width=int(8 * s * S))                          # 左の腕（構え）
    ax = x + 10 * s + (12 + 40 * punch) * s; ay = y - 30 * s - 2 * s * punch
    d.line(P(x + 10 * s, y - 30 * s, ax, ay), fill=NAVY, width=int(8 * s * S)); d.ellipse(P(ax - 7 * s, ay - 7 * s, ax + 7 * s, ay + 7 * s), fill=RED)   # 右の腕とグローブ


def game(im, punch=0.0, hit=False, sound=False, late=False, caption="", swing=0.0):
    """横向きのスマホのゲーム画面（上）。hit＝当たった光、sound＝「ドン」、late＝音がまだ（…）"""
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(P(120, 26, 520, 236), radius=26 * S, fill=(29, 34, 40))                                      # スマホ（横向き）
    d.rounded_rectangle(P(136, 38, 504, 224), radius=14 * S, fill=(196, 226, 236))                                    # 画面：空
    d.rectangle(P(136, 186, 504, 224), fill=(122, 170, 110)); d.rounded_rectangle(P(136, 186, 504, 224), radius=0, outline=None)
    fighter(d, 250, 186, punch, 1.0)
    bx = 352 + 10 * swing                                                                                             # サンドバッグ（吊り下げ。当たると揺れる）
    d.line(P(352, 38, bx, 96), fill=(90, 96, 104), width=2 * S)
    d.rounded_rectangle(P(bx - 22, 96, bx + 22, 176), radius=14 * S, fill=(200, 72, 60))
    if hit:
        pts = []
        for k in range(16):
            r = 26 if k % 2 == 0 else 11; a = k * math.pi / 8; pts += [bx - 22 + r * math.cos(a), 128 + r * math.sin(a)]
        d.polygon(P(*pts), fill=(255, 230, 90))
    if sound:
        for r in (30, 44, 58): d.arc(P(bx - r, 128 - r, bx + r, 128 + r), -40, 40, fill=AMBER, width=3 * S)
        text(d, (bx + 74, 104), "ドン！", AMBER, 22)
    if late: text(d, (bx + 70, 104), "……", GRAY, 22)
    d.rounded_rectangle(P(456, 196, 492, 218), radius=8 * S, fill=WHITE, outline=GRAY, width=S); text(d, (474, 207), "パンチ", INK, 10)
    if caption: tag(d, (320, 16), caption, TEAL, 15)
    return d


def flow(d, y, items, cols):
    """左から右への流れ：四角と矢印"""
    n = len(items); w = 560 / n; x = 40
    for k, (lab, sub) in enumerate(items):
        cx = x + w * (k + 0.5)
        d.rounded_rectangle(P(cx - w / 2 + 8, y - 28, cx + w / 2 - 8, y + 28), radius=10 * S, fill=WHITE, outline=cols[k], width=2 * S)
        text(d, (cx, y - 8), lab, cols[k], 15); text(d, (cx, y + 13), sub, INK, 11)
        if k < n - 1: d.polygon(P(cx + w / 2 - 6, y, cx + w / 2 - 14, y - 6, cx + w / 2 - 14, y + 6), fill=GRAY)


def balance(d, tilt, left, right):
    """てんびん：左＝ためる（途切れにくい）、右＝すぐ鳴る。tilt＞0 で左が下がる"""
    cx, cy = 320, 190; L = 170; a = math.radians(10 * tilt)
    d.polygon(P(cx, cy, cx - 22, cy + 70, cx + 22, cy + 70), fill=(120, 128, 136))
    xl, yl = cx - L * math.cos(a), cy + L * math.sin(a); xr, yr = cx + L * math.cos(a), cy - L * math.sin(a)
    d.line(P(xl, yl, xr, yr), fill=INK, width=4 * S); d.ellipse(P(cx - 6, cy - 6, cx + 6, cy + 6), fill=INK)
    for (x_, y_), (lab, col) in (((xl, yl), left), ((xr, yr), right)):
        d.line(P(x_, y_, x_, y_ + 34), fill=GRAY, width=2 * S)
        d.rounded_rectangle(P(x_ - 92, y_ + 34, x_ + 92, y_ + 74), radius=10 * S, fill=WHITE, outline=col, width=3 * S); text(d, (x_, y_ + 54), lab, col, 15)


def panel(n):
    if n == 1:                                    # 158 それなら、もっと先の分まで、ためておけばいいのでしょうか
        im = base(22.0); d = ImageDraw.Draw(im); tag(d, (220, 52), "もっと先の分まで、ためておけば？", TEAL); gauge(d, (585, 110), 1, 3)
    elif n == 2:                                  # 159 たくさん届くまで待ってから、鳴らし始める
        im = base(2.0); d = ImageDraw.Draw(im); tag(d, (230, 52), "たくさん届くまで、鳴らさずに待つ", TEAL); gauge(d, (585, 70), 6, 6)
        ring(d, (452, 300), 30, GRAY, 3); text(d, (452, 344), "まだ鳴らさない", GRAY, 13)
    elif n == 3:                                  # 160 遅れたときに備える余裕は増やせる
        im = base(26.0); d = ImageDraw.Draw(im); tag(d, (230, 52), "配達が遅れても、まだこんなに残っている", GREEN, 15); gauge(d, (585, 70), 5, 6, col=GREEN)
        text(d, (585, 172), "余裕 ✓", GREEN, 16)
    elif n == 4:                                  # 161 長く待てば、音が聞こえるのも遅くなる
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 50), "長く待つほど、音が出るのも遅い", AMBER)
        strip(d, 150, [(110, "▶ 押す", TEAL, "tap"), (200, "音が出る", GREEN, "snd")], "少しためる")
        strip(d, 270, [(110, "▶ 押す", TEAL, "tap"), (480, "音が出る", GREEN, "snd")], "たくさんためる", gap=(110, 480, "待つ時間"))
    elif n == 5:                                  # 162 待つ余裕と、すぐ音が出ることは、両立するとは限らない
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 46), "両方いっぺんには、よくならない", INK)
        balance(d, 1.0, ("ためる＝途切れにくい", TEAL), ("すぐ音が出る", AMBER))
    elif n == 6:                                  # 163 音楽の再生開始を少し待つだけなら、あまり気にならない
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 46), "音楽なら、始まりを少し待っても気にならない", GREEN, 15)
        d.rounded_rectangle(P(250, 80, 390, 250), radius=18 * S, fill=(29, 34, 40)); d.rounded_rectangle(P(260, 92, 380, 238), radius=10 * S, fill=(52, 60, 70))
        d.ellipse(P(290, 112, 350, 172), fill=(170, 200, 230)); d.polygon(P(312, 186, 312, 214, 336, 200), fill=WHITE)
        strip(d, 300, [(110, "▶ 押す", TEAL, "tap"), (230, "曲が始まる", GREEN, "snd")], gap=(110, 230, "少し待つ"))
    elif n == 7:                                  # 164 では、ゲームのように、操作に合わせて音が鳴る場合は
        im = blank(); game(im, 0.0, caption="ゲーム：ボタンを押すとパンチ")
        d = ImageDraw.Draw(im); text(d, (320, 270), "押した瞬間に、パンチの音が鳴ってほしい", INK, 16)
    elif n == 8:                                  # 165 まずは、パンチと音が、ぴったり合う場合
        im = blank(); d = game(im, 1.0, hit=True, sound=True, swing=1.0, caption="ぴったり合う")
        strip(d, 300, [(110, "押す", TEAL, "tap"), (230, "当たる・音（同時）", (220, 170, 30), "hit")]); d.arc(P(220, 280, 260, 320), -50, 50, fill=GREEN, width=2 * S)
    elif n == 9:                                  # 166 次は、音が遅れてくる場合
        im = blank(); game(im, 0.0, caption="音が遅れてくる場合")
    elif n == 10:                                 # 167 パンチは、もう当たっているのに
        im = blank(); d = game(im, 1.0, hit=True, late=True, swing=1.0, caption="もう当たっているのに")
        strip(d, 300, [(110, "押す", TEAL, "tap"), (230, "当たる", (220, 170, 30), "hit")])
    elif n == 11:                                 # 168 音だけ、今ごろ届きました
        im = blank(); d = game(im, 0.0, sound=True, swing=-0.6, caption="音だけ、今ごろ")
        strip(d, 300, [(110, "押す", TEAL, "tap"), (230, "当たる", (220, 170, 30), "hit"), (430, "音", GREEN, "snd")], gap=(230, 430, "ずれ"))
    elif n == 12:                                 # 169 調子が狂う
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 50), "見た目と音がずれると、調子が狂う", RED)
        fighter(d, 260, 250, 0.3, 1.4, face=1); text(d, (330, 140), "？", RED, 40)
        strip(d, 312, [(150, "当たる", (220, 170, 30), "hit"), (330, "音", GREEN, "snd")], gap=(150, 330, "ずれ"))
    elif n == 13:                                 # 170 ゲームでは、操作してから、必要な音が決まる
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 50), "操作してから、鳴らす音が決まる", TEAL)
        flow(d, 170, [("押す", "操作"), ("パンチ！", "音が決まる"), ("送る", "電波"), ("鳴る", "イヤホン")], [TEAL, AMBER, TEAL, GREEN])
    elif n == 14:                                 # 171 効果音そのものは用意できても、いつ鳴らすかは決まらない
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 50), "音そのものは用意できる。いつ鳴らすかは、押すまで分からない", INK, 14)
        d.rounded_rectangle(P(110, 110, 290, 230), radius=12 * S, fill=WHITE, outline=GREEN, width=3 * S); text(d, (200, 150), "パンチの音", GREEN, 17); text(d, (200, 190), "用意できる ✓", GREEN, 14)
        d.rounded_rectangle(P(350, 110, 530, 230), radius=12 * S, fill=WHITE, outline=RED, width=3 * S); text(d, (440, 150), "いつ鳴らす？", RED, 17); text(d, (440, 190), "押すまで分からない", RED, 13)
    elif n == 15:                                 # 172 長く待たせれば、操作した瞬間と聞こえる瞬間が離れる
        im = base(2.0); d = ImageDraw.Draw(im); tag(d, (240, 46), "パンチの音も、タワーで順番を待つと…", AMBER, 15)
        d.rectangle(P(0, 268, 640, 360), fill=BG); strip(d, 300, [(110, "押す", TEAL, "tap"), (470, "聞こえる", GREEN, "snd")], gap=(110, 470, "待たせた分だけ離れる"))
    elif n == 16:                                 # 173 まだしていない操作の音を、先に全部ためておくわけにはいかない
        im = base(22.0); d = ImageDraw.Draw(im); tag(d, (230, 46), "まだ押していない分は、先にためられない", RED, 15)
        for k, yy in enumerate((90, 130, 170)): text(d, (585, yy), "？", RED, 28)
        text(d, (585, 212), "これからの操作", RED, 12)
    elif n == 17:                                 # 174〜176 途切れにくいこと・すぐ返ってくること・両方を考える
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 46), "使い方に合わせて、両方を考える", INK)
        balance(d, 0.0, ("途切れにくい", TEAL), ("すぐ返ってくる", AMBER)); text(d, (150, 300), "音楽を聴く", TEAL, 14); text(d, (490, 300), "ゲーム", AMBER, 14)
    elif n == 18:                                 # 177 実際の遅れは、機器や通信の方式によっても変わる
        im = blank(); d = ImageDraw.Draw(im); tag(d, (320, 60), "遅れの大きさは、機器や通信の方式で変わる", INK, 15)
        for k, (lab, w_) in enumerate((("機器 A", 380), ("機器 B", 250), ("機器 C", 160))):
            y_ = 130 + 54 * k; text(d, (110, y_), lab, INK, 14); d.rounded_rectangle(P(150, y_ - 12, 150 + w_, y_ + 12), radius=6 * S, fill=(200, 210, 216))
        text(d, (320, 312), "（棒の長さは、たとえ）", GRAY, 12)
    elif n == 19:                                 # 178 今回は、音を待たせる時間に注目して見てきた
        im = base(26.0); d = ImageDraw.Draw(im); tag(d, (240, 52), "今回は、音を待たせる時間に注目した", TEAL)
    return im


PANELS = [(1, 158), (2, 159), (3, 160), (4, 161), (5, 162), (6, 163), (7, 164), (8, 165), (9, 166), (10, 167), (11, 168), (12, 169),
          (13, 170), (14, 171), (15, 172), (16, 173), (17, 174), (18, 177), (19, 178)]
NOTE = {1: "第7章の貯蔵タワー：もっとためれば？", 2: "たくさん届くまで鳴らさずに待つ（タワーの目盛りがいっぱい）", 3: "配達が遅れても余裕がある ✓",
        4: "時間の帯：たくさんためると、押してから音が出るまで長い", 5: "てんびん：ためる（途切れにくい）と、すぐ音が出る", 6: "音楽なら、始まりを少し待っても気にならない",
        7: "ゲーム：主人公と同じピクトグラムの人がパンチ", 8: "ぴったり合う：当たる瞬間に「ドン！」", 9: "次は、音が遅れてくる場合", 10: "当たったのに、音がまだ（……）",
        11: "音だけ、今ごろ届く：時間の帯に「ずれ」", 12: "見た目と音がずれて、調子が狂う", 13: "ゲームは、押してから鳴らす音が決まる（流れ）",
        14: "音そのものは用意できる／いつ鳴らすかは押すまで分からない", 15: "パンチの音もタワーで待たせると、押した瞬間と聞こえる瞬間が離れる",
        16: "まだ押していない操作の音は、先にためられない", 17: "途切れにくい（音楽）と、すぐ返ってくる（ゲーム）を、使い方に合わせて", 18: "遅れの大きさは機器・方式で変わる（棒はたとえ）",
        19: "今回は、音を待たせる時間に注目した → まとめへ"}

f1 = ImageFont.truetype(FONT, 17); f2 = ImageFont.truetype(FONT, 15)
if __name__ == "__main__":
    W, H, CAP, cols = 480, 270, 66, 4
    rows = (len(PANELS) + cols - 1) // cols
    sh = Image.new("RGB", (W * cols, (H + CAP) * rows + 50), "white"); dd = ImageDraw.Draw(sh)
    dd.text((12, 12), "第8章（15:06〜17:05）絵コンテ　ためる余裕と、すぐ鳴ること（ゲームの例）", font=ImageFont.truetype(FONT, 22), fill=TEAL)
    for j, (n, ln) in enumerate(PANELS):
        im = panel(n).resize((W, H), Image.LANCZOS); x, y = (j % cols) * W, (j // cols) * (H + CAP) + 50; sh.paste(im, (x, y))
        t = TL[ln]["start"]; m, s_ = divmod(t, 60); dd.rectangle((x, y, x + 64, y + 18), fill=TEAL); dd.text((x + 4, y + 1), "%d:%04.1f" % (m, s_), font=f2, fill="white")
        dd.text((x + 6, y + H + 4), "▶ " + NOTE[n][:27], font=f1, fill=TEAL); txt = TL[ln]["text"]
        dd.text((x + 6, y + H + 26), txt[:30], font=f2, fill=(60, 60, 60)); dd.text((x + 6, y + H + 45), txt[30:60], font=f2, fill=(60, 60, 60))
    sh.save(ST + "/ch03/review/ch08_storyboard.jpg", quality=88); print("ok")
