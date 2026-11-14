# ロボットではありません回：絵コンテの 3D に 2D の字・札を重ね、2D の場面（S06・S07・S09・S10・S19・S20 など）を描く
# python3 board_overlay.py <3D の絵のフォルダ> <フォントのフォルダ> <出力フォルダ>
#   出力：<出力>/<ショット>.png（1280×720・字幕なし）と shots.json（どの台詞からどの絵か）・<ショット>_390.png（幅 390 の点検用）
# 決まり：字幕と同じことは書かない（単語・ラベル・数字・式だけ）。札の字は 46 以上、数字は 60 以上。字幕の帯（y>520）に札を置かない
# 本物の画面のまねはしない（チャンネルの色と形で描く。会社の印〈ロゴ〉は使わない）
import sys, os, json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, F, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
FB = F + '/NotoSansJP_700Bold.ttf'
def font(n): return ImageFont.truetype(FB, n)
NAVY = (20, 36, 72); NAVY2 = (47, 74, 115); TEAL = (33, 193, 179); ORANGE = (255, 138, 42); GREEN = (64, 176, 96); WHITE = (255, 255, 255)
BG = (226, 236, 244)
SUB_TOP = 520          # これより下は字幕の帯
LOG = []               # 札の字の大きさ・場所（点検用）


def load(name):
    return Image.open(os.path.join(SRC, name + '.png')).convert('RGB').resize((1280, 720))


def anch(name):
    p = os.path.join(SRC, name + '.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def check_band(shot, box, size):
    LOG.append(dict(shot=shot, box=[round(v) for v in box], size=size))
    assert box[3] <= SUB_TOP, ('字幕の帯にかかる', shot, box)


def tag(im, shot, text, cx, cy, size=48, bg=WHITE, fg=NAVY, tail=None):
    d = ImageDraw.Draw(im); f = font(size)
    bb = d.textbbox((0, 0), text, font=f); w, th = bb[2] - bb[0], bb[3] - bb[1]
    cx = min(max(cx, w / 2 + 40), 1280 - w / 2 - 40)
    x0, y0, x1, y1 = cx - w / 2 - 24, cy - th / 2 - 16, cx + w / 2 + 24, cy + th / 2 + 16
    if tail:
        by = y1 - 2 if tail[1] > cy else y0 + 2
        bx = min(max(tail[0], x0 + 40), x1 - 40) if abs(tail[0] - cx) > w / 2 else cx
        d.polygon([(bx - 34, by), (bx + 34, by), tail], fill=bg, outline=NAVY)
    d.rounded_rectangle([x0, y0, x1, y1], 18, fill=bg, outline=NAVY, width=4)
    d.text((x0 + 24 - bb[0], cy - th / 2 - bb[1]), text, font=f, fill=fg)
    check_band(shot, (x0, y0, x1, y1), size)
    return x0, y0, x1, y1


def check_card(im, shot, cx=640, cy=110, state='empty', size=52, show_text=True):
    """チャンネルの絵で描いたチェック欄（四角＋「私はロボットではありません」）"""
    d = ImageDraw.Draw(im); f = font(size); text = '私はロボットではありません'
    tw = d.textlength(text, font=f); w = tw + 150; h = size + 56
    x0, y0 = cx - w / 2, cy - h / 2
    d.rounded_rectangle([x0 + 6, y0 + 8, x0 + w + 6, y0 + h + 8], 20, fill=(0, 0, 0, 60))
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 20, fill=WHITE, outline=NAVY2, width=5)
    bx = x0 + 30; by = cy - 32
    if state == 'checked':
        d.rounded_rectangle([bx, by, bx + 64, by + 64], 10, fill=GREEN)
        d.line([(bx + 13, by + 34), (bx + 28, by + 50), (bx + 52, by + 14)], fill=WHITE, width=10)
    else:
        d.rounded_rectangle([bx, by, bx + 64, by + 64], 10, fill=WHITE, outline=NAVY2, width=6)
    if show_text: d.text((bx + 96, cy - size * 0.62), text, font=f, fill=NAVY)
    check_band(shot, (x0, y0, x0 + w, y0 + h), size)
    return bx + 32, by + 32   # 四角い欄のまん中


def ctext(d, xy, text, font, fill):
    """字の外形（textbbox）で、(x, y) にぴったりまん中を合わせて書く（v5 コメント「左右高さ中央揃えじゃない」）"""
    b = d.textbbox((0, 0), text, font=font)
    d.text((xy[0] - (b[0] + b[2]) / 2, xy[1] - (b[1] + b[3]) / 2), text, font=font, fill=fill)


def pic_bubble(im, cx, cy, r, draw, to=None):
    """字のない絵の吹き出し。to：しっぽを向ける先（まるロボなど）。省くと左下"""
    d = ImageDraw.Draw(im)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=NAVY, width=5)
    if to is None: to = (cx - r * 1.0, cy + r * 1.5)
    ang = math.atan2(to[1] - cy, to[0] - cx); ux, uy = math.cos(ang), math.sin(ang); px, py = -uy, ux
    bx, by = cx + ux * r * 0.85, cy + uy * r * 0.85
    L = min(r * 0.75, max(r * 0.35, math.hypot(to[0] - bx, to[1] - by) - 12))
    tip = (bx + ux * (L + r * 0.15), by + uy * (L + r * 0.15))
    d.polygon([(bx + px * r * 0.3, by + py * r * 0.3), (bx - px * r * 0.3, by - py * r * 0.3), tip], fill=WHITE, outline=NAVY)
    d.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], fill=WHITE)
    draw(d, cx, cy, r)


def q_mark(d, cx, cy, r, col=ORANGE):
    ctext(d, (cx, cy), '?', font(int(r * 1.3)), col)


def ex_mark(d, cx, cy, r):
    ctext(d, (cx, cy), '!', font(int(r * 1.3)), ORANGE)


def light_icon(d, cx, cy, s):
    d.rounded_rectangle([cx - 18 * s, cy - 45 * s, cx + 18 * s, cy + 45 * s], 8 * s, fill=(45, 47, 52))
    for k, col in enumerate(((230, 60, 50), (240, 190, 40), (70, 190, 90))):
        y = cy - 28 * s + k * 28 * s
        d.ellipse([cx - 11 * s, y - 11 * s, cx + 11 * s, y + 11 * s], fill=col)


def wavy(d, x0, y0, x1, y1, col, amp=40, n=40, dot=7):
    for k in range(n):
        t = k / (n - 1)
        x = x0 + (x1 - x0) * t + amp * math.sin(t * 7.5) * (1 - t)
        y = y0 + (y1 - y0) * t + amp * 0.6 * math.sin(t * 11 + 1) * (1 - t)
        if k % 2 == 0: d.ellipse([x - dot, y - dot, x + dot, y + dot], fill=col)


def straight(d, x0, y0, x1, y1, col, n=18, dot=7):
    for k in range(n):
        t = k / (n - 1); x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
        d.ellipse([x - dot, y - dot, x + dot, y + dot], fill=col)


def mini_screen(im, x, y, w, h):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], 20, fill=(214, 222, 232), outline=NAVY2, width=6)
    d.rectangle([x + 6, y + 6, x + w - 6, y + 40], fill=(206, 216, 228))
    return d


def warp_word(word, size=150, seed=1):
    """ゆがんだ文字（テストの昔の形）：字を描いて波でゆがめ、線を引く"""
    random.seed(seed)
    f = font(size); tmp = Image.new('L', (int(size * len(word) * 0.75) + 80, int(size * 1.6)), 0); d = ImageDraw.Draw(tmp)
    x = 30
    for ch in word:
        layer = Image.new('L', tmp.size, 0); dl = ImageDraw.Draw(layer)
        dl.text((x, size * 0.2 + random.randint(-12, 12)), ch, font=f, fill=255)
        layer = layer.rotate(random.uniform(-18, 18), center=(x + size * 0.3, size * 0.8))
        tmp = Image.fromarray(__import__('numpy').maximum(__import__('numpy').array(tmp), __import__('numpy').array(layer)))
        x += int(d.textlength(ch, font=f) * 0.82)
    import numpy as np
    a = np.array(tmp); out = np.zeros_like(a)
    for yy in range(a.shape[0]):
        sh = int(10 * math.sin(yy / 14.0))
        out[yy] = np.roll(a[yy], sh)
    a2 = out.copy()
    for xx in range(a.shape[1]):
        a2[:, xx] = np.roll(out[:, xx], int(9 * math.sin(xx / 22.0)))
    img = Image.fromarray(a2)
    d2 = ImageDraw.Draw(img)
    d2.line([(10, img.height * 0.55), (img.width - 10, img.height * 0.42)], fill=255, width=7)
    return img


def chat_icon(d, cx, cy, s=1.0, col=TEAL):
    """AI の印（自作。チャットの吹き出しの形に 3 つの点。本物のロゴに似せない）"""
    d.rounded_rectangle([cx - 90 * s, cy - 75 * s, cx + 90 * s, cy + 55 * s], int(36 * s), fill=col)
    d.polygon([(cx - 50 * s, cy + 50 * s), (cx - 10 * s, cy + 50 * s), (cx - 60 * s, cy + 95 * s)], fill=col)
    for k in (-1, 0, 1): d.ellipse([cx + k * 45 * s - 13 * s, cy - 23 * s, cx + k * 45 * s + 13 * s, cy + 3 * s], fill=WHITE)


SHOTS = []
def save(im, name, start_id, dt=0.0):
    """dt：その台詞の頭から何秒あとに替えるか（ふらふらのように、1 つの台詞の中で絵を替えるとき）"""
    im.save(os.path.join(OUT, name + '.png'))
    im.resize((390, 219), Image.LANCZOS).save(os.path.join(OUT, name + '_390.png'))
    SHOTS.append(dict(id=start_id, img=name + '.png', **({'dt': dt} if dt else {})))


# v2（動画レビュー v1 のコメント）：札・数字・答えは、声で言う瞬間に出す（先に絵でネタバレさせない）。同じ絵が長く続く所は途中で絵を変える
# ---------------- 冒頭
save(load('b01'), 's01', '01-01')
im = load('b02'); check_card(im, 's02a', cy=96, show_text=False)
pic_bubble(im, 1110, 300, 70, lambda d, x, y, r: q_mark(d, x, y, r))
save(im, 's02a', '02-01')
im = load('b02'); check_card(im, 's02b', cy=96)
pic_bubble(im, 1110, 300, 70, lambda d, x, y, r: q_mark(d, x, y, r))
save(im, 's02b', '02-02')
im = load('b03'); check_card(im, 's03', cy=96); save(im, 's03', '03-01')

# オープニング（v5 コメント「03-05 のあとにオープニングを 2 秒」）：画面の中の世界に題名
im = load('b12'); im = Image.eval(im, lambda v: int(v * 0.55)); d = ImageDraw.Draw(im)
d.rounded_rectangle([170, 150, 1110, 470], 30, fill=(10, 20, 40), outline=TEAL, width=6)   # 画面の端から 170 ピクセル内側（スマホで端が隠れても切れない。v5 コメント）
ctext(d, (640, 222), 'ロボットが', font(60), WHITE)
ctext(d, (640, 310), '「私はロボットではありません」を', font(48), (255, 214, 120))
ctext(d, (640, 398), '押したら？', font(60), WHITE); LOG.append(dict(shot='op', size=48))
f52 = font(48); bb = d.textbbox((0, 0), '「私はロボットではありません」を', font=f52); assert bb[2] - bb[0] <= 1110 - 170 - 160, 'オープニングの字が枠からはみ出す'
save(im, 's_op', '04-01', dt=-2.0)

# ---------------- ① 実験
im = load('b04a'); check_card(im, 's04a', cy=96); tag(im, 's04a', 'まるロボ', 1080, 250, tail=(1020, 330)); save(im, 's04a', '04-01')
im = load('b04a'); check_card(im, 's04x', cy=96); save(im, 's04x', '04-03')     # まだくるくる回っている（テストは 04-04 で出す）
im = load('b04b'); tag(im, 's04b', '信号機を全部選んでください', 640, 70, size=48); save(im, 's04b', '04-04')
im = load('b04b'); tag(im, 's04c', '信号機を全部選んでください', 640, 70, size=48); tag(im, 's04c', '疑われたときに出る', 1020, 220, size=48, bg=(255, 236, 214)); save(im, 's04c', '04-05')
im = load('b05a'); check_card(im, 's05x', cy=96); save(im, 's05x', '05-01')
im = load('b05a'); check_card(im, 's05a', cy=96); tag(im, 's05a', '私', 300, 250, size=56); save(im, 's05a', '05-02')
im = load('b05b'); check_card(im, 's05b', cy=96, state='checked'); save(im, 's05b', '05-03')

# S06 何が違った？（2D：左右に並べる）
im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
for k, (x, who, col) in enumerate(((70, 'まるロボ', TEAL), (690, '私', ORANGE))):
    mini_screen(im, x, 130, 520, 340)
    if k == 0:  # 絵のテスト
        d.rounded_rectangle([x + 150, 170, x + 370, 450], 10, fill=WHITE)
        d.rectangle([x + 150, 170, x + 370, 210], fill=(70, 130, 220))
        for r in range(3):
            for c in range(3):
                d.rectangle([x + 160 + c * 70, 220 + r * 75, x + 220 + c * 70, 285 + r * 75], fill=(160, 195, 220))
        light_icon(d, x + 260, 327, 0.7)
    else:
        d.rounded_rectangle([x + 110, 260, x + 410, 340], 14, fill=WHITE, outline=NAVY2, width=4)
        d.rounded_rectangle([x + 130, 275, x + 180, 325], 8, fill=GREEN)
        d.line([(x + 140, 300), (x + 152, 313), (x + 172, 285)], fill=WHITE, width=8)
    tag(im, 's06', who, x + 260, 70, size=52, bg=WHITE, fg=col if k == 0 else (200, 90, 20))
save(im, 's06', '06-01')

# ---------------- ② 昔のテスト（S07・S08）
WORDS = (('morning', 3), ('upon', 7))
def old_test(shot, glow_right=False, frames=(), y0=230):
    """昔のテスト：ゆがんだ単語 2 つと、打ち込む欄。frames＝枠で囲む単語（'L'・'R'）"""
    im = Image.new('RGB', (1280, 720), (238, 232, 220)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([140, y0, 1140, y0 + 270], 24, fill=WHITE, outline=NAVY2, width=5)
    for k, (w, seed) in enumerate(WORDS):
        wimg = warp_word(w, 110, seed)
        tint = Image.new('RGB', wimg.size, (60, 60, 70) if not (glow_right and k == 1) else (170, 110, 20))
        x = 190 if k == 0 else 700
        im.paste(tint, (x, y0 + 20), wimg)
        if ('L' if k == 0 else 'R') in frames:
            d.rounded_rectangle([x - 15, y0 + 30, x + 420, y0 + 190], 14, outline=ORANGE if k else TEAL, width=7)
    d.rounded_rectangle([340, y0 + 205, 940, y0 + 250], 10, fill=(240, 243, 246), outline=(170, 182, 198), width=3)
    return im


def asker(im, shot):
    """出題する側（四角い出題係の印）"""
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([590, 40, 690, 140], 22, fill=NAVY2); d.ellipse([615, 65, 665, 115], fill=WHITE)
    tag(im, shot, '出題する側', 820, 90, size=44)


def known_bubble(im):      # 左：出題する側は答えを知っている（きれいな字で読めている）
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([250, 50, 530, 180], 30, fill=WHITE, outline=NAVY, width=5)
    d.polygon([(380, 178), (420, 178), (400, 238)], fill=WHITE, outline=NAVY)
    ctext(d, (390, 115), 'morning', font(60), NAVY); LOG.append(dict(shot='bubble', size=60))


def unknown_bubble(im):    # 右：出題する側も答えを知らない
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([790, 160, 960, 230], 30, fill=WHITE, outline=NAVY, width=5)
    ctext(d, (875, 195), '？？？', font(54), ORANGE)


save(old_test('s07'), 's07', '07-01')
im = old_test('s07b')   # 07-04（v5 コメント「人と機械がわかりにくい」）：人は読めて吹き出しに単語、機械（パソコンの目）は吹き出しに？
d = ImageDraw.Draw(im)
d.ellipse([70, 50, 160, 140], fill=(244, 210, 181)); d.rounded_rectangle([50, 140, 180, 205], 30, fill=(62, 124, 177))   # 人
d.rounded_rectangle([210, 40, 450, 130], 26, fill=WHITE, outline=NAVY, width=5); d.polygon([(220, 110), (250, 125), (175, 150)], fill=WHITE, outline=NAVY)
ctext(d, (330, 85), 'morning', font(52), NAVY)
d.ellipse([465, 55, 535, 125], outline=GREEN, width=12)
d.rounded_rectangle([1060, 40, 1220, 150], 14, fill=NAVY2); d.rectangle([1075, 52, 1205, 138], fill=(214, 222, 232))   # 機械（パソコンの画面に目）
d.ellipse([1110, 70, 1170, 120], fill=TEAL); d.ellipse([1128, 86, 1152, 108], fill=NAVY); d.rectangle([1125, 150, 1155, 175], fill=NAVY2); d.rounded_rectangle([1090, 172, 1190, 190], 6, fill=NAVY2)
d.rounded_rectangle([830, 40, 1030, 130], 26, fill=WHITE, outline=NAVY, width=5); d.polygon([(1010, 110), (990, 125), (1065, 120)], fill=WHITE, outline=NAVY)
ctext(d, (930, 85), '？？？', font(52), ORANGE)
d.line([(700, 60), (780, 140)], fill=(220, 70, 60), width=12); d.line([(780, 60), (700, 140)], fill=(220, 70, 60), width=12)
tag(im, 's07b', '人', 330, 178, size=44); tag(im, 's07b', '機械', 930, 178, size=44)
LOG.append(dict(shot='s07b', size=52))
save(im, 's07b', '07-04')
save(old_test('s08a', frames=('L', 'R')), 's08a', '08-01')                       # 2 つの種類：枠で 2 つに分ける
im = old_test('s08b', frames=('L',)); asker(im, 's08b'); known_bubble(im)
save(im, 's08b', '08-02')
im = old_test('s08c', frames=('L', 'R'), glow_right=True); asker(im, 's08c'); known_bubble(im); save(im, 's08c', '08-03')
im = old_test('s08d', frames=('L', 'R'), glow_right=True); asker(im, 's08d'); known_bubble(im)
d = ImageDraw.Draw(im); d.polygon([(860, 228), (890, 228), (875, 250)], fill=WHITE, outline=NAVY); unknown_bubble(im)
save(im, 's08d', '08-04')
im = load('b08'); tag(im, 's08e', '古い新聞', 640, 70, size=52); save(im, 's08e', '08-04c')
im = load('b08'); tag(im, 's08f', '1851年からの新聞', 640, 70, size=60); save(im, 's08f', '08-07')

# ---------------- ③ ロボットの方が得意（S09・S10）
def eyes(im):
    d = ImageDraw.Draw(im)
    for x in (175, 685):
        d.rounded_rectangle([x, 250, x + 430, 420], 12, outline=TEAL, width=8)
im = old_test('s09a'); eyes(im); save(im, 's09a', '09-01')
im = old_test('s09b'); eyes(im); tag(im, 's09b', '2014年', 260, 90, size=60); tag(im, 's09b', 'Google', 560, 90, size=52); save(im, 's09b', '09-02')
im = old_test('s09c'); eyes(im); tag(im, 's09c', '2014年', 260, 90, size=60); tag(im, 's09c', 'Google', 560, 90, size=52); tag(im, 's09c', '99.8%', 1010, 90, size=72, bg=(214, 247, 243)); save(im, 's09c', '09-03')


def compare(shot, labels=False, prog=False, human=False):
    im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
    for k, (x, who, acc, sec, col) in enumerate(((80, '人', '5〜8割', '9〜15秒', ORANGE), (680, 'プログラム', 'ほぼ全部', '1秒未満', TEAL))):
        d.rounded_rectangle([x, 140, x + 520, 500], 26, fill=WHITE, outline=col, width=8)
        if labels: tag(im, shot, who, x + 260, 140, size=52)
        if (k == 1 and prog) or (k == 0 and human):
            f = font(58); fs = font(46)
            for yy, lab, val in ((270, '正解', acc), (410, '時間', sec)):
                d.rounded_rectangle([x + 30, yy - 34, x + 150, yy + 34], 14, fill=(232, 238, 246))
                ctext(d, (x + 90, yy), lab, fs, NAVY2)
                ctext(d, (x + 335, yy), val, f, NAVY)
            LOG.append(dict(shot=shot, size=46))
    tag(im, shot, '2023年', 640, 55, size=56)
    return im
save(compare('s10a'), 's10a', '10-01')
save(compare('s10b', labels=True), 's10b', '10-02')
save(compare('s10c', labels=True, prog=True), 's10c', '10-03')
save(compare('s10d', labels=True, prog=True, human=True), 's10d', '10-04')
im = load('b11'); check_card(im, 's11', cy=96); tag(im, 's11', '2014年', 1120, 230, size=60); save(im, 's11', '11-02')

# ---------------- ④ 中で見ているもの
a = anch('b12'); im = load('b12')
save(im, 's12a', '12-01')
im = load('b12'); g = a.get('gate', [640, 100]); tag(im, 's12b', 'チェック欄', g[0], max(60, g[1] - 10), size=50, tail=(g[0], g[1] + 50)); save(im, 's12b', '12-02')
im = load('b12'); g = a.get('dog', [900, 200]); tag(im, 's12c', '門番', min(g[0] + 140, 1150), max(80, g[1] - 60), size=56, tail=(g[0] + 30, g[1])); save(im, 's12c', '12-03')
a = anch('b13'); h = a.get('human_path', [400, 300]); r = a.get('robot_path', [850, 300])
save(load('b13e'), 's13a', '13-01')                                                     # まだ足あとなし
im = load('b13h'); tag(im, 's13b', '私', h[0] - 120, min(h[1], 470), size=56, bg=(255, 236, 214)); save(im, 's13b', '13-03')
im = load('b13h'); tag(im, 's13c', '私', h[0] - 120, min(h[1], 470), size=56, bg=(255, 236, 214)); save(im, 's13c', '13-04')
im = load('b13'); tag(im, 's13d', '私', h[0] - 120, min(h[1], 470), size=56, bg=(255, 236, 214))
tag(im, 's13d', 'まるロボ', r[0] + 170, min(r[1], 470), size=52, bg=(214, 247, 243)); save(im, 's13d', '13-05')
save(load('b14'), 's14', '14-01')
save(load('b15'), 's15a', '15-01')
a = anch('b15'); im = load('b15'); b = a.get('book', [800, 250]); tag(im, 's15b', 'これまでの記録', b[0], max(70, b[1] - 120), size=52, tail=(b[0], b[1] - 40)); save(im, 's15b', '15-02')
a = anch('b16'); im = load('b16'); m = a.get('meter_top', [300, 150]); tag(im, 's16', '人らしさ', m[0], max(60, m[1] - 50), size=54, tail=(m[0], m[1] + 10)); save(im, 's16', '16-01')
im = load('b16'); m = a.get('meter_top', [300, 150]); tag(im, 's16b', '人らしさ', m[0], max(60, m[1] - 50), size=54, tail=(m[0], m[1] + 10))
tag(im, 's16b', '迷ったら → 絵のテスト', 920, 170, size=46, bg=(255, 236, 214)); save(im, 's16b', '16-03')

# ---------------- ⑤ 絵のテスト
im = load('b17n'); tag(im, 's17a', '信号機のマスを全部選んでください', 640, 60, size=46); save(im, 's17a', '17-01')
im = load('b17'); tag(im, 's17b', '信号機のマスを全部選んでください', 640, 60, size=46); save(im, 's17b', '17-03b')
a = anch('b18'); e = a.get('edge', [900, 250]); mr = a.get('maru', [660, 220]); CELL = [tuple(a['cell%d' % k]) for k in range(4)] if 'cell0' in a else None
def cell_line(im):   # まるロボが乗っている端っこのマスを、マスの形でふちどる
    d = ImageDraw.Draw(im)
    if CELL: d.line(CELL + [CELL[0]], fill=ORANGE, width=9, joint='curve')
    else: d.ellipse([e[0] - 110, e[1] - 80, e[0] + 110, e[1] + 80], outline=ORANGE, width=9)
BUB = (mr[0] - 330, max(110, mr[1] - 60))
im = load('b18'); pic_bubble(im, BUB[0], BUB[1], 80, lambda d, x, y, r: (light_icon(d, x - 15, y, 0.9), q_mark(d, x + 38, y, r * 0.55)), to=(mr[0] - 40, mr[1])); save(im, 's18a', '18-01')
im = load('b18'); cell_line(im)
pic_bubble(im, BUB[0], BUB[1], 80, lambda d, x, y, r: (light_icon(d, x - 15, y, 0.9), q_mark(d, x + 38, y, r * 0.55)), to=(mr[0] - 40, mr[1])); save(im, 's18b', '18-02')

# ---------------- ⑥ AI（2D）
def chat(shot, n, head=True, person=True):
    im = Image.new('RGB', (1280, 720), (232, 238, 246)); d = ImageDraw.Draw(im)
    chat_icon(d, 140, 255, 1.0)
    tag(im, shot, 'GPT-4', 140, 420, size=48)
    if person:
        d.ellipse([1070, 160, 1190, 280], fill=(244, 210, 181)); d.rounded_rectangle([1040, 280, 1220, 400], 46, fill=(62, 124, 177))
        tag(im, shot, '頼まれた人', 1110, 450, size=46)
    if n >= 1: pic_bubble(im, 1180, 120, 56, lambda d, x, y, r: q_mark(d, x, y, r))
    if n >= 2: tag(im, shot, '「私はロボットではありません」', 640, 330, size=48, bg=(214, 247, 243), tail=(240, 280))
    if head: tag(im, shot, '2023年  OpenAI「GPT-4」', 640, 60, size=48)
    return im
save(chat('s19a', 0, head=False, person=False), 's19a', '19-01')
save(chat('s19b', 0, person=False), 's19b', '19-02')
save(chat('s19c', 0), 's19c', '19-03b')
save(chat('s19d', 1), 's19d', '19-04')
save(chat('s19e', 2), 's19e', '19-06')
im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
for r in range(4):
    for c in range(4):
        x0, y0 = 360 + c * 140, 110 + r * 100
        d.rectangle([x0, y0, x0 + 130, y0 + 92], fill=(160, 195, 220) if (c, r) not in ((2, 0), (2, 1)) else (59, 130, 246))
light_icon(d, 710, 200, 1.4)
d.rounded_rectangle([340, 95, 940, 515], 12, outline=TEAL, width=8)
tag(im, 's20a', '2024年', 170, 120, size=60)
save(im, 's20a', '20-01')
def ai_screen(shot, card=False, checked=False):
    im = Image.new('RGB', (1280, 720), BG); d = mini_screen(im, 240, 100, 800, 400)
    if card:
        d.rounded_rectangle([300, 250, 980, 340], 14, fill=WHITE, outline=NAVY2, width=4)
        if checked:
            d.rounded_rectangle([320, 265, 380, 325], 8, fill=GREEN); d.line([(330, 296), (344, 312), (370, 278)], fill=WHITE, width=9)
        else:
            d.rounded_rectangle([320, 265, 380, 325], 8, fill=WHITE, outline=NAVY2, width=5)
        d.text((405, 295), '人間かどうかを確かめます', font=font(46), fill=NAVY, anchor='lm'); LOG.append(dict(shot=shot, size=46))
    else:   # 作業中の画面（字のない行）
        for k in range(4): d.rounded_rectangle([300, 180 + k * 60, 300 + (560 if k % 2 == 0 else 420), 210 + k * 60], 10, fill=(196, 206, 218))
    chat_icon(ImageDraw.Draw(im), 150, 300, 0.8); tag(im, shot, 'ChatGPT', 150, 430, size=46)
    tag(im, shot, '2025年', 640, 50, size=50)
    return im
save(ai_screen('s20b'), 's20b', '20-02')
save(ai_screen('s20c', card=True), 's20c', '20-02c')
save(ai_screen('s20d', card=True, checked=True), 's20d', '20-04')
im = load('b01'); d = ImageDraw.Draw(im)   # 21-03：ふつうに買い物をしている画面（チェック欄なし）。その裏で、人らしさの点がついている
tag(im, 's21', 'チェック欄なし', 330, 80, size=50, bg=(255, 236, 214))
d.rounded_rectangle([960, 60, 1240, 470], 24, fill=(20, 33, 58), outline=TEAL, width=5)
d.rounded_rectangle([1070, 150, 1130, 430], 14, fill=NAVY2); d.rounded_rectangle([1080, 240, 1120, 420], 10, fill=TEAL)
tag(im, 's21', '人らしさ', 1100, 110, size=46); tag(im, 's21', '見えない所', 1100, 470 - 10, size=44, bg=(214, 247, 243))
save(im, 's21', '21-03')

# ---------------- ⑦ まとめ・オチ
im = load('b22'); check_card(im, 's22', cy=96); d = ImageDraw.Draw(im)
wavy(d, 1000, 470, 1180, 230, ORANGE, amp=30, n=30, dot=6); straight(d, 100, 470, 260, 230, TEAL, n=14, dot=6)
save(im, 's22', '22-01')
im = load('b23'); check_card(im, 's23', cy=96); save(im, 's23a', '23-01')
for k, side in enumerate(('l', 'r', 'l', 'r')):
    im = load('b23' + side); check_card(im, 's23', cy=96); save(im, 's23w%d' % k, '23-02', dt=0.7 * k)
im = load('b23'); check_card(im, 's23', cy=96, state='checked'); d = ImageDraw.Draw(im); wavy(d, 1180, 480, 900, 200, ORANGE, amp=30, n=30, dot=6); save(im, 's23b', '23-03')


# ---------------- v2：同じ絵が長く続く所（12 秒以上）に、声に合わせた絵を足す
def ring_on(im, cx, cy, rx, ry, col=ORANGE):
    ImageDraw.Draw(im).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=col, width=9)
def lock(d, cx, cy, s=1.0):
    d.rounded_rectangle([cx - 45 * s, cy - 10 * s, cx + 45 * s, cy + 60 * s], 10, fill=NAVY2)
    d.arc([cx - 30 * s, cy - 60 * s, cx + 30 * s, cy + 10 * s], 180, 360, fill=NAVY2, width=int(12 * s))
    d.ellipse([cx - 9 * s, cy + 15 * s, cx + 9 * s, cy + 33 * s], fill=WHITE)
def screens_crowd(im, n=12):
    d = ImageDraw.Draw(im); random.seed(4)
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n; x = 640 + 470 * math.cos(a); y = 270 + 190 * math.sin(a)
        d.rounded_rectangle([x - 50, y - 34, x + 50, y + 34], 10, fill=(214, 222, 232), outline=NAVY2, width=4); pts.append((x, y))
    return pts
# 03-03：四角の欄に丸
im = load('b03'); bc = check_card(im, 's03b', cy=96); ring_on(im, bc[0], bc[1], 62, 56); save(im, 's03b', '03-03')
im = load('b03'); check_card(im, 's03c', cy=96); save(im, 's03c', '03-05')
# 06-04：昔は違う形 → 欄に「？」
im = load('b11'); check_card(im, 's06b', cy=96); pic_bubble(im, 1080, 280, 80, lambda d, x, y, r: q_mark(d, x, y, r)); save(im, 's06b', '06-04')
# 08-05・08-06：たくさんの人に読んでもらう → 同じ答えが集まって決まる
im = Image.new('RGB', (1280, 720), (238, 232, 220)); pts = screens_crowd(im)
w = warp_word('upon', 110, 7); im.paste(Image.new('RGB', w.size, (170, 110, 20)), (640 - w.width // 2, 270 - w.height // 2), w); save(im, 's08g', '08-05')
im = Image.new('RGB', (1280, 720), (238, 232, 220)); pts = screens_crowd(im); d = ImageDraw.Draw(im)
for x, y in pts: d.line([(x, y), (640, 270)], fill=(200, 180, 140), width=4)
d.rounded_rectangle([470, 210, 810, 330], 20, fill=WHITE, outline=GREEN, width=6); ctext(d, (640, 270), 'upon', font(80), NAVY); LOG.append(dict(shot='s08h', size=80))
save(im, 's08h', '08-06')
# 10-05：プログラムの方に丸
im = compare('s10e', labels=True, prog=True, human=True); ring_on(im, 940, 320, 290, 200, TEAL); save(im, 's10e', '10-05')
# 11-03〜11-05：ロボットにも押せる → 冒頭のテスト → どこを見ている？
im = load('b04a'); check_card(im, 's11b', cy=96); save(im, 's11b', '11-03')
im = load('b04b'); tag(im, 's11c', '信号機を全部選んでください', 640, 70, size=48); tag(im, 's11c', '疑われたときに出る', 1020, 220, size=48, bg=(255, 236, 214)); save(im, 's11c', '11-04')
im = load('b11'); check_card(im, 's11d', cy=96); pic_bubble(im, 1080, 280, 80, lambda d, x, y, r: q_mark(d, x, y, r)); save(im, 's11d', '11-05')
# 13-06・13-07：ふらつく私の跡に丸 → まっすぐのまるロボの跡に丸
a13 = anch('b13'); h = a13.get('human_path', [400, 300]); r = a13.get('robot_path', [850, 300])
im = load('b13'); tag(im, 's13e', '私', h[0] - 120, min(h[1], 470), size=56, bg=(255, 236, 214)); ring_on(im, h[0], h[1] - 40, 150, 120); save(im, 's13e', '13-06')
im = load('b13'); tag(im, 's13f', 'まるロボ', r[0] + 170, min(r[1], 470), size=52, bg=(214, 247, 243)); ring_on(im, r[0], r[1] - 40, 130, 150, TEAL); save(im, 's13f', '13-07')
# 15-02c〜15-02e：ふだんの記録（いろいろなスタンプ）→ 同じスタンプが何百も
def icon(d, kind, x, y, col, r=46):
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE, outline=col, width=7)
    if kind == 'news':
        d.rectangle([x - 24, y - 18, x + 24, y + 18], outline=col, width=5); d.line([(x - 14, y - 4), (x + 14, y - 4)], fill=col, width=4); d.line([(x - 14, y + 6), (x + 8, y + 6)], fill=col, width=4)
    elif kind == 'cart':
        d.line([(x - 26, y - 16), (x - 16, y + 12), (x + 20, y + 12), (x + 26, y - 10), (x - 20, y - 10)], fill=col, width=5)
        d.ellipse([x - 14, y + 16, x - 6, y + 24], fill=col); d.ellipse([x + 10, y + 16, x + 18, y + 24], fill=col)
    elif kind == 'video':
        d.polygon([(x - 12, y - 20), (x - 12, y + 20), (x + 20, y)], fill=col)


def page(shot, same=False):
    """これまでの記録：ふだん（いろいろなことをしてきた）／怪しい（同じことを何百回）"""
    im = Image.new('RGB', (1280, 720), (238, 232, 220)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([140, 110, 1140, 500], 24, fill=(250, 246, 236), outline=NAVY2, width=6)
    if same:
        for k in range(36):
            x = 220 + (k % 12) * 76; y = 170 + (k // 12) * 110
            icon(d, 'cart', x, y, (220, 80, 70), r=32)
        tag(im, shot, '同じことを何百回も', 640, 460, size=48, bg=(255, 236, 214))
    else:
        for k, (kind, lab, col) in enumerate((('news', 'ニュース', NAVY2), ('cart', '買い物', (220, 80, 70)), ('video', '動画', (33, 160, 150)))):
            x = 340 + k * 300; icon(d, kind, x, 250, col, r=70)
            tag(im, shot, lab, x, 390, size=48)
    tag(im, shot, 'これまでの記録', 640, 55, size=50)
    return im
save(page('s15c'), 's15c', '15-02c')
save(page('s15d', same=True), 's15d', '15-02e')
im = load('b15'); a15 = anch('b15'); b = a15.get('book', [800, 250]); tag(im, 's15e', 'これまでの記録', b[0], max(70, b[1] - 120), size=52, tail=(b[0], b[1] - 40)); save(im, 's15e', '15-03')
# 16-05：細かいことは公開されていない → かぎ
im = load('b16'); a16 = anch('b16'); m = a16.get('meter_top', [300, 150]); tag(im, 's16c', '人らしさ', m[0], max(60, m[1] - 50), size=54, tail=(m[0], m[1] + 10))
lock(ImageDraw.Draw(im), 1000, 200, 1.4); tag(im, 's16c', '公開されていない', 1000, 330, size=46); save(im, 's16c', '16-05')
# 18-05・18-06：選び方も手がかり → まるロボの行ったり来たり
im = load('b18'); cell_line(im); d = ImageDraw.Draw(im)
d.rounded_rectangle([60, 140, 130, 470], 16, fill=NAVY2); d.rounded_rectangle([75, 300, 115, 455], 10, fill=TEAL)
tag(im, 's18c', '人らしさ', 200, 110, size=48); tag(im, 's18c', '選び方も見ている', 560, 110, size=48, bg=(255, 236, 214)); save(im, 's18c', '18-05')
# 19-03：AI は自分では解けない（テストの絵に ✕）
im = chat('s19f', 0, person=False); d = ImageDraw.Draw(im)
for r in range(3):
    for c in range(3): d.rectangle([470 + c * 70, 170 + r * 70, 530 + c * 70, 230 + r * 70], fill=(160, 195, 220))
d.line([(450, 150), (690, 390)], fill=(220, 70, 60), width=16); d.line([(690, 150), (450, 390)], fill=(220, 70, 60), width=16)
save(im, 's19f', '19-03')
# 19-07：頼まれた人がテストを解く → 19-08：研究者が手伝った試験
im = chat('s19g', 2); d = ImageDraw.Draw(im); d.ellipse([930, 160, 1010, 240], fill=GREEN); d.line([(948, 200), (965, 218), (995, 180)], fill=WHITE, width=10); save(im, 's19g', '19-07')
im = chat('s19h', 2); d = ImageDraw.Draw(im)
d.ellipse([340, 380, 420, 460], fill=(244, 210, 181)); d.rounded_rectangle([320, 455, 440, 510], 30, fill=(240, 240, 240), outline=NAVY2, width=4)
tag(im, 's19h', '研究者が手伝った試験', 700, 440, size=46, bg=(255, 236, 214)); save(im, 's19h', '19-08')
# 21：このように → ふるまい全体を見る → チェック欄さえ出さない
save(load('b20d'), 's20e', '20-05')
im = load('b14'); tag(im, 's21b', 'ふるまい全体を見る', 640, 70, size=52); save(im, 's21b', '21-02')   # 門番が足あと全体を照らして見ている（v5 コメント「分かりにくい」）
# 22（v3 コメント「表現が分かりにくい」）：問い → 動き方 → 記録 → 昔と今 → AI が賢く → 見分け方が残り少ない
im = load('b22'); check_card(im, 's22a', cy=96); pic_bubble(im, 1080, 280, 80, lambda d, x, y, r: q_mark(d, x, y, r)); save(im, 's22a', '22-01')
a13 = anch('b13'); h = a13.get('human_path', [400, 300]); r = a13.get('robot_path', [850, 300])
im = load('b13'); tag(im, 's22b', '私', h[0] - 120, min(h[1], 470), size=56, bg=(255, 236, 214)); tag(im, 's22b', 'まるロボ', r[0] + 170, min(r[1], 470), size=52, bg=(214, 247, 243)); tag(im, 's22b', '動き方', 640, 70, size=56); save(im, 's22b', '22-02')
im = load('b15'); a15 = anch('b15'); b = a15.get('book', [800, 250]); tag(im, 's22c', 'これまでの記録', b[0], max(70, b[1] - 120), size=52, tail=(b[0], b[1] - 40)); save(im, 's22c', '22-03')
im = Image.new('RGB', (1280, 720), BG)
im.paste(old_test('x').resize((560, 315)), (50, 170)); im.paste(load('b13').resize((560, 315)), (670, 170))
tag(im, 's22d', '昔：文字を読めるか', 330, 100, size=46); tag(im, 's22d', '今：ふるまい', 950, 100, size=46); save(im, 's22d', '22-04')
im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im); chat_icon(d, 640, 290, 1.5)
for x in (400, 880): d.polygon([(x - 40, 330), (x + 40, 330), (x, 230)], fill=ORANGE); d.rectangle([x - 15, 330, x + 15, 400], fill=ORANGE)
tag(im, 's22e', 'AI は ますます賢く', 640, 80, size=50); save(im, 's22e', '22-05')
im = Image.new('RGB', (1280, 720), (40, 48, 64)); d = ImageDraw.Draw(im)
for k, lab in enumerate(('ゆがんだ文字', '絵のテスト', 'ふるまい')):
    x = 230 + k * 410
    d.rounded_rectangle([x - 170, 160, x + 170, 420], 24, fill=(214, 222, 232) if k < 2 else WHITE, outline=NAVY2, width=5)
    tag(im, 's22f', lab, x, 220, size=46)
    if k < 2:
        d.line([(x - 110, 270), (x + 110, 400)], fill=(220, 70, 60), width=18); d.line([(x + 110, 270), (x - 110, 400)], fill=(220, 70, 60), width=18)
    else:
        ctext(d, (x, 340), '？', font(110), ORANGE)
tag(im, 's22f', '見分ける方法', 640, 80, size=50); save(im, 's22f', '22-06')
json.dump(SHOTS, open(os.path.join(OUT, 'shots.json'), 'w'), ensure_ascii=False, indent=0)
json.dump(LOG, open(os.path.join(OUT, 'tags_log.json'), 'w'), ensure_ascii=False, indent=0)
small = [l for l in LOG if l.get('size', 99) < 44]
print('ショット', len(SHOTS), '札', len(LOG), '44 未満の字', small)
