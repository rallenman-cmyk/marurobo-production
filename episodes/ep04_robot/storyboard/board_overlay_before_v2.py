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
        d.polygon([(cx - 18, by), (cx + 18, by), tail], fill=bg, outline=NAVY)
    d.rounded_rectangle([x0, y0, x1, y1], 18, fill=bg, outline=NAVY, width=4)
    d.text((x0 + 24 - bb[0], cy - th / 2 - bb[1]), text, font=f, fill=fg)
    check_band(shot, (x0, y0, x1, y1), size)
    return x0, y0, x1, y1


def check_card(im, shot, cx=640, cy=110, state='empty', size=52):
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
    d.text((bx + 96, cy - size * 0.62), text, font=f, fill=NAVY)
    check_band(shot, (x0, y0, x0 + w, y0 + h), size)


def pic_bubble(im, cx, cy, r, draw):
    d = ImageDraw.Draw(im)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=NAVY, width=5)
    d.ellipse([cx - r * 0.75, cy + r * 0.85, cx - r * 0.75 + 26, cy + r * 0.85 + 26], fill=WHITE, outline=NAVY, width=3)
    draw(d, cx, cy, r)


def q_mark(d, cx, cy, r, col=ORANGE):
    f = font(int(r * 1.3)); d.text((cx, cy), '?', font=f, fill=col, anchor='mm')


def ex_mark(d, cx, cy, r):
    f = font(int(r * 1.3)); d.text((cx, cy), '!', font=f, fill=ORANGE, anchor='mm')


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


SHOTS = []
def save(im, name, start_id):
    im.save(os.path.join(OUT, name + '.png'))
    im.resize((390, 219), Image.LANCZOS).save(os.path.join(OUT, name + '_390.png'))
    SHOTS.append(dict(id=start_id, img=name + '.png'))


# ---------------- 冒頭
save(load('b01'), 's01', '01-01')
im = load('b02'); check_card(im, 's02', cy=96)
a = anch('b02')
pic_bubble(im, 1110, 300, 70, lambda d, x, y, r: q_mark(d, x, y, r))
save(im, 's02', '02-01')
im = load('b03'); check_card(im, 's03', cy=96); save(im, 's03', '03-01')

# ---------------- ① 実験
im = load('b04a'); check_card(im, 's04a', cy=96); tag(im, 's04a', 'まるロボ', 1080, 250, tail=(1020, 330)); save(im, 's04a', '04-01')
im = load('b04b'); tag(im, 's04b', '信号機を全部選んでください', 640, 70, size=48); save(im, 's04b', '04-03')
im = load('b04b'); tag(im, 's04c', '信号機を全部選んでください', 640, 70, size=48); tag(im, 's04c', '疑われたときに出る', 1020, 220, size=48, bg=(255, 236, 214)); save(im, 's04c', '04-05')
im = load('b05a'); check_card(im, 's05a', cy=96); tag(im, 's05a', '私', 300, 250, size=56); save(im, 's05a', '05-01')
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
def old_test(shot, labels=False, glow_right=False):
    im = Image.new('RGB', (1280, 720), (238, 232, 220)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([140, 120, 1140, 470], 24, fill=WHITE, outline=NAVY2, width=5)
    for k, (w, seed) in enumerate((('morning', 3), ('upon', 7))):
        wimg = warp_word(w, 120, seed)
        tint = Image.new('RGB', wimg.size, (60, 60, 70) if not (glow_right and k == 1) else (170, 110, 20))
        x = 190 if k == 0 else 700
        im.paste(tint, (x, 170), wimg)
    d.rounded_rectangle([340, 400, 940, 450], 10, fill=(240, 243, 246), outline=(170, 182, 198), width=3)
    if labels:
        tag(im, shot, '答えが分かっている', 400, 70, size=46)
        tag(im, shot, '答えが分からない', 900, 70, size=46, bg=(255, 236, 214))
    return im
save(old_test('s07'), 's07', '07-01')
save(old_test('s08a', labels=True), 's08a', '08-01')
save(old_test('s08b', labels=True, glow_right=True), 's08b', '08-03')
im = load('b08'); tag(im, 's08c', '古い新聞', 640, 70, size=52); save(im, 's08c', '08-04c')
im = load('b08'); tag(im, 's08d', '1851年からの新聞', 640, 70, size=60); save(im, 's08d', '08-07')

# ---------------- ③ ロボットの方が得意（S09・S10）
im = old_test('s09')
d = ImageDraw.Draw(im)
for x in (180, 690):
    d.rounded_rectangle([x, 160, x + 420, 330], 12, outline=TEAL, width=8)
tag(im, 's09', '2014年', 260, 60, size=60)
tag(im, 's09', '99.8%', 1010, 60, size=72, bg=(214, 247, 243))
save(im, 's09', '09-01')
im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
for k, (x, who, acc, sec, col) in enumerate(((80, '人', '5〜8割', '9〜15秒', ORANGE), (680, 'プログラム', 'ほぼ全部', '1秒未満', TEAL))):
    d.rounded_rectangle([x, 120, x + 520, 500], 26, fill=WHITE, outline=col, width=8)
    tag(im, 's10', who, x + 260, 120, size=52)
    f = font(64)
    d.text((x + 260, 260), acc, font=f, fill=NAVY, anchor='mm'); LOG.append(dict(shot='s10', size=64))
    d.text((x + 260, 400), sec, font=f, fill=NAVY, anchor='mm')
    # 砂時計
    hx = x + 60
    d.polygon([(hx - 25, 340), (hx + 25, 340), (hx, 380)], fill=(240, 190, 80) if k == 0 else (200, 200, 200))
    d.polygon([(hx - 25, 420), (hx + 25, 420), (hx, 380)], fill=(240, 190, 80))
tag(im, 's10', '2023年', 640, 50, size=56)
save(im, 's10', '10-01')
im = load('b11'); check_card(im, 's11', cy=96); tag(im, 's11', '2014年', 1120, 230, size=60); save(im, 's11', '11-02')

# ---------------- ④ 中で見ているもの
a = anch('b12'); im = load('b12')
save(im, 's12a', '12-01')
im = load('b12'); g = a.get('gate', [640, 100]); tag(im, 's12b', 'チェック欄', g[0], max(60, g[1] - 10), size=50, tail=(g[0], g[1] + 50)); save(im, 's12b', '12-02')
im = load('b12'); g = a.get('dog', [900, 200]); tag(im, 's12c', '門番', min(g[0] + 140, 1150), max(80, g[1] - 60), size=56, tail=(g[0] + 30, g[1])); save(im, 's12c', '12-03')
a = anch('b13'); im = load('b13')
h = a.get('human_path', [400, 300]); r = a.get('robot_path', [850, 300])
tag(im, 's13', '私', h[0] - 120, min(h[1], 470), size=56, bg=(255, 236, 214))
tag(im, 's13', 'まるロボ', r[0] + 170, min(r[1], 470), size=52, bg=(214, 247, 243))
save(im, 's13', '13-01')
save(load('b14'), 's14', '14-01')
a = anch('b15'); im = load('b15'); b = a.get('book', [800, 250]); tag(im, 's15', 'これまでの記録', b[0], max(70, b[1] - 120), size=52, tail=(b[0], b[1] - 40)); save(im, 's15', '15-01')
a = anch('b16'); im = load('b16'); m = a.get('meter_top', [300, 150]); tag(im, 's16', '人らしさ', m[0], max(60, m[1] - 50), size=54, tail=(m[0], m[1] + 10)); save(im, 's16', '16-01')
im = load('b16'); m = a.get('meter_top', [300, 150]); tag(im, 's16b', '人らしさ', m[0], max(60, m[1] - 50), size=54, tail=(m[0], m[1] + 10))
d = ImageDraw.Draw(im); tag(im, 's16b', '迷ったら → 絵のテスト', 920, 170, size=46, bg=(255, 236, 214)); save(im, 's16b', '16-03')

# ---------------- ⑤ 絵のテスト
im = load('b17'); tag(im, 's17', '信号機のマスを全部選んでください', 640, 60, size=46); save(im, 's17', '17-01')
a = anch('b18'); im = load('b18'); e = a.get('edge', [900, 250]); d = ImageDraw.Draw(im)
d.ellipse([e[0] - 110, e[1] - 80, e[0] + 110, e[1] + 80], outline=ORANGE, width=9)
pic_bubble(im, 300, 170, 80, lambda d, x, y, r: (light_icon(d, x - 15, y, 0.9), q_mark(d, x + 38, y, r * 0.55)))
save(im, 's18', '18-01')

# ---------------- ⑥ AI（2D）
def chat(shot, n):
    im = Image.new('RGB', (1280, 720), (232, 238, 246)); d = ImageDraw.Draw(im)
    # 左：AI の印（四角い光）・右：人の形
    d.rounded_rectangle([50, 170, 230, 350], 34, fill=TEAL); d.ellipse([100, 220, 180, 300], fill=WHITE)
    d.ellipse([1070, 160, 1190, 280], fill=(244, 210, 181)); d.rounded_rectangle([1040, 280, 1220, 400], 46, fill=(62, 124, 177))
    tag(im, shot, 'AI', 140, 420, size=48); tag(im, shot, '頼まれた人', 1110, 450, size=46)
    if n >= 1:   # 人が「？」（言葉は字幕と声で。上に同じ文を出さない）
        pic_bubble(im, 1180, 120, 56, lambda d, x, y, r: q_mark(d, x, y, r))
    if n >= 2:   # AI の答えの決めぜりふだけ札に
        tag(im, shot, '「私はロボットではありません」', 640, 330, size=48, bg=(214, 247, 243), tail=(240, 280))
    tag(im, shot, '2023年  OpenAI「GPT-4」', 640, 60, size=48)
    return im
save(chat('s19a', 0), 's19a', '19-01')
save(chat('s19b', 1), 's19b', '19-04')
save(chat('s19c', 2), 's19c', '19-05')
im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
for r in range(4):
    for c in range(4):
        x0, y0 = 360 + c * 140, 110 + r * 100
        d.rectangle([x0, y0, x0 + 130, y0 + 92], fill=(160, 195, 220) if (c, r) not in ((2, 0), (2, 1)) else (59, 130, 246))
light_icon(d, 710, 200, 1.4)
d.rounded_rectangle([340, 95, 940, 515], 12, outline=TEAL, width=8)
tag(im, 's20a', '2024年', 170, 120, size=60)
save(im, 's20a', '20-01')
im = Image.new('RGB', (1280, 720), BG); d = mini_screen(im, 240, 100, 800, 400)
d.rounded_rectangle([300, 250, 980, 340], 14, fill=WHITE, outline=NAVY2, width=4)
d.rounded_rectangle([320, 265, 380, 325], 8, fill=WHITE, outline=NAVY2, width=5)
d.text((405, 295), '人間かどうかを確かめます', font=font(46), fill=NAVY, anchor='lm'); LOG.append(dict(shot='s20b', size=46))
tag(im, 's20b', '2025年  ChatGPT', 640, 50, size=50)
save(im, 's20b', '20-02')
im2 = im.copy(); d2 = ImageDraw.Draw(im2)
d2.rounded_rectangle([320, 265, 380, 325], 8, fill=GREEN); d2.line([(330, 296), (344, 312), (370, 278)], fill=WHITE, width=9)
save(im2, 's20c', '20-04')
save(load('b21'), 's21', '21-01')

# ---------------- ⑦ まとめ・オチ
im = load('b22'); check_card(im, 's22', cy=96); d = ImageDraw.Draw(im)
wavy(d, 1000, 470, 1180, 230, ORANGE, amp=30, n=30, dot=6); straight(d, 100, 470, 260, 230, TEAL, n=14, dot=6)
save(im, 's22', '22-01')
im = load('b23'); check_card(im, 's23', cy=96); save(im, 's23a', '23-01')
im = load('b23'); check_card(im, 's23', cy=96, state='checked'); d = ImageDraw.Draw(im); wavy(d, 1180, 480, 900, 200, ORANGE, amp=30, n=30, dot=6); save(im, 's23b', '23-03')

json.dump(SHOTS, open(os.path.join(OUT, 'shots.json'), 'w'), ensure_ascii=False, indent=0)
json.dump(LOG, open(os.path.join(OUT, 'tags_log.json'), 'w'), ensure_ascii=False, indent=0)
small = [l for l in LOG if l.get('size', 99) < 44]
print('ショット', len(SHOTS), '札', len(LOG), '44 未満の字', small)
