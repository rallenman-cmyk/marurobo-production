# 絵コンテ（台本 v1.0）に字幕と 2D の札を重ね、2D の場面（b03・b09・b20）を描く
# python3 board_overlay.py <フォントのフォルダ>   → board/bXX.png（字幕つき）・board/bXX_390.png（幅 390 の点検用）
# 字幕の決まり：1280×720 で 56・太字・紺のふち 5・影・1 行 25 字まで・2 行まで（SKILL §3）
# 札：単語・ラベル・数字だけ（字幕と同じことは書かない）。字は 44 以上
import sys, os, math
from PIL import Image, ImageDraw, ImageFont
F = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
os.makedirs('board', exist_ok=True)
B = ImageFont.truetype(F + '/NotoSansJP_700Bold.ttf', 56)
TAGF = ImageFont.truetype(F + '/NotoSansJP_700Bold.ttf', 46)
BIG = ImageFont.truetype(F + '/NotoSansJP_700Bold.ttf', 64)
NAVY = (20, 36, 72)
ORANGE = (255, 138, 42)


def sub(im, text):
    d = ImageDraw.Draw(im)
    rows = text.split('\n')
    for r in rows:  # 1 行の幅が画面（左右 30 の余白）に入るか
        assert d.textlength(r, font=B) <= im.width - 60, ('幅をこえる', r)
    lh = 72
    y0 = im.height - 40 - lh * len(rows)
    for k, row in enumerate(rows):
        w = d.textlength(row, font=B)
        x = (im.width - w) / 2
        y = y0 + k * lh
        d.text((x + 3, y + 4), row, font=B, fill=(0, 0, 0), stroke_width=5, stroke_fill=(0, 0, 0))
        d.text((x, y), row, font=B, fill='white', stroke_width=5, stroke_fill=NAVY)
    return y0  # 字幕の帯の上の端


def tag(im, text, cx, cy, tail=None, bg=(255, 255, 255), fg=NAVY, font=TAGF):
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), text, font=font)
    w, th = bb[2] - bb[0], bb[3] - bb[1]
    h = th + 30
    cx = min(max(cx, w / 2 + 30), im.width - w / 2 - 30)
    x0, y0, x1, y1 = cx - w / 2 - 22, cy - h / 2, cx + w / 2 + 22, cy + h / 2
    if tail:
        base_y = y1 - 2 if tail[1] > cy else y0 + 2
        d.polygon([(cx - 16, base_y), (cx + 16, base_y), tail], fill=bg, outline=NAVY)
    d.rounded_rectangle([x0, y0, x1, y1], 18, fill=bg, outline=NAVY, width=4)
    d.text((x0 + 22 - bb[0], cy - th / 2 - bb[1]), text, font=font, fill=fg)
    return (x0, y0, x1, y1)


def ring(im, cx, cy, rx, ry, col=ORANGE, w=8):
    d = ImageDraw.Draw(im)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=col, width=w)


def wifi(d, cx, cy, s=1.0, col='white'):
    for r in (90, 62, 34):
        r *= s
        d.arc([cx - r, cy - r, cx + r, cy + r], 225, 315, fill=col, width=int(12 * s))
    d.ellipse([cx - 9 * s, cy - 9 * s, cx + 9 * s, cy + 9 * s], fill=col)


def picbubble(im, cx, cy, r, draw_fn):
    d = ImageDraw.Draw(im)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='white', outline=NAVY, width=4)
    d.ellipse([cx - r * 0.9 - 30, cy + r * 0.7, cx - r * 0.9, cy + r * 0.7 + 30], fill='white', outline=NAVY, width=3)
    draw_fn(d, cx, cy, r)


def leaf(d, cx, cy, r):
    pts = []
    for i in range(10):
        a = math.radians(90 + i * 36)
        rr = r * (0.75 if i % 2 == 0 else 0.35)
        pts.append((cx + rr * math.cos(a), cy - rr * math.sin(a)))
    d.polygon(pts, fill=(217, 71, 43))
    d.line([(cx, cy), (cx, cy + r * 0.7)], fill=(120, 40, 20), width=6)


def phone_mock(im, x, y, w, h, inner):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], 28, fill=(34, 38, 43), outline=NAVY, width=4)
    m = 14
    sc = inner.resize((w - 2 * m, h - 2 * m))
    im.paste(sc, (x + m, y + m))


# ---------------- 2D の場面
def scene_b03():
    im = Image.new('RGB', (1280, 720), (238, 244, 247))
    d = ImageDraw.Draw(im)
    # 話している人の吹き出し（左）から、物の絵がスマホ（右）へ
    d.ellipse([60, 120, 420, 400], fill='white', outline=NAVY, width=6)
    d.polygon([(150, 380), (210, 380), (120, 470)], fill='white', outline=NAVY)
    d.ellipse([110, 470, 210, 570], fill=(241, 199, 165))  # 人の頭（顔は描かない）
    d.pieslice([90, 540, 230, 700], 180, 360, fill=(78, 143, 199))
    icons = [(150, 260), (240, 210), (330, 260)]
    # ラーメン
    d.pieslice([110, 230, 190, 310], 0, 180, fill=(242, 169, 59)); d.line([(120, 235), (185, 205)], fill=(120, 80, 40), width=6)
    # かばん
    d.rounded_rectangle([210, 185, 275, 245], 8, fill=(62, 124, 177)); d.arc([225, 165, 260, 200], 180, 360, fill=(40, 60, 90), width=6)
    # 犬のえさ（骨）
    d.rounded_rectangle([300, 252, 365, 268], 6, fill=(200, 160, 110))
    for x in (298, 362):
        for yy in (248, 268):
            d.ellipse([x - 9, yy - 9, x + 9, yy + 9], fill=(200, 160, 110))
    for k, (x, y) in enumerate(icons):
        d.line([(x + 60, y), (800 - 20 * k, 230 + 60 * k)], fill=(150, 165, 180), width=5)
        d.polygon([(800 - 20 * k, 220 + 60 * k), (800 - 20 * k, 240 + 60 * k), (825 - 20 * k, 230 + 60 * k)], fill=(150, 165, 180))
    ad = Image.open('phone_ad.png').convert('RGB')
    phone_mock(im, 860, 60, 300, 560, ad)
    return im


def scene_b09():
    im = Image.new('RGB', (1280, 720), (30, 42, 60))
    d = ImageDraw.Draw(im)
    cols = [(110, 140, 180), (90, 160, 150), (160, 130, 190), (190, 150, 110), (120, 170, 120)]
    cells = []
    for r in range(5):
        for c in range(14):
            x, y = 80 + c * 80, 120 + r * 80
            red = (r, c) in ((1, 3), (3, 9), (2, 12))
            d.rounded_rectangle([x, y, x + 60, y + 60], 12, fill=(229, 72, 77) if red else cols[(r + c) % 5])
            if red:  # 画面を撮る印（四角の中に四角）
                d.rectangle([x + 16, y + 12, x + 44, y + 48], outline='white', width=4)
                d.ellipse([x + 26, y + 24, x + 34, y + 32], fill='white')
    # 虫めがね
    d.ellipse([820, 170, 980, 330], outline=(242, 193, 78), width=14)
    d.line([(960, 310), (1040, 390)], fill=(242, 193, 78), width=22)
    return im


def scene_b20():
    im = Image.new('RGB', (1280, 720), (12, 20, 38))
    d = ImageDraw.Draw(im)
    scr = Image.new('RGB', (300, 600), (244, 246, 248))
    sd = ImageDraw.Draw(scr)
    for k in range(5):
        y = 60 + k * 100
        sd.rounded_rectangle([20, y, 280, y + 70], 14, fill='white')
        sd.rounded_rectangle([30, y + 22, 170, y + 46], 8, fill=(203, 211, 220))
        on = k != 2
        sd.rounded_rectangle([200, y + 18, 266, y + 52], 17, fill=(43, 179, 166) if on else (190, 196, 204))
        sd.ellipse([234 if on else 202, y + 20, 264 if on else 232, y + 50], fill='white')
    phone_mock(im, 490, 40, 300, 600, scr)
    ring(im, 723, 40 + 14 + 260 * 600 / 600 * 1 + 35, 70, 50)
    return im


# ---------------- 場面ごと：(字幕, 札, 追加の絵)
def ov_b01(im):
    tag(im, '今度、キャンプ行きたいね', 390, 110, tail=(390, 300))
    tag(im, 'いいね！', 940, 190, tail=(935, 300))


def ov_b06(im):
    ring(im, 830, 392, 200, 62)


def ov_b07(im):
    tag(im, '見張り番', 1110, 130, tail=(860, 290))


def ov_b08(im):
    tag(im, 'Hey Siri', 600, 110, tail=(590, 280), bg=(255, 244, 214))


def ov_b09(im):
    tag(im, '1万7千本以上のアプリ', 640, 60)
    tag(im, '2018年', 1120, 60)


def ov_b10(im):
    tag(im, 'いた場所', 930, 320, tail=(830, 450))


def ov_b13(im):
    d = ImageDraw.Draw(im)
    wifi(d, 640, 150, 1.0)
    for x, y in ((250, 330), (830, 330)):
        for t in range(0, 100, 10):
            a = (640 + (x - 640) * t / 100, 150 + (y - 150) * t / 100)
            b = (640 + (x - 640) * (t + 5) / 100, 150 + (y - 150) * (t + 5) / 100)
            d.line([a, b], fill='white', width=6)
    phone_mock(im, 1000, 150, 170, 330, Image.open('phone_ad.png').convert('RGB'))
    tag(im, 'ソラさんのスマホ', 1085, 80)


def ov_b14(im):
    picbubble(im, 800, 300, 80, leaf)


def ov_b15(im):
    for k, x in enumerate((70, 640, 1210)):
        ring(im, x, 300, 80, 90)
        tag(im, str(k + 1), x, 170, font=BIG)


def ov_b16(im):
    tag(im, '当たり', 470, 150, tail=(560, 300))
    tag(im, '外れ', 1050, 330, tail=(950, 470))


def ov_b18(im):
    tag(im, 'メールアドレスの名簿', 900, 110, tail=(820, 330))


def ov_b20(im):
    tag(im, '広告の設定', 1010, 330, tail=(800, 330))


def ov_b21(im):
    tag(im, 'ピポ、ピポ', 980, 170)


S = [
    ('b00', 'キャンプの話をしたのは、たった一度。\n今日の昼の、電車の中だけ。', None),
    ('b01', 'どうやら、今度の休みに、二人で\nキャンプへ行く話がまとまったみたいです。', ov_b01),
    ('b02', '……まるロボが、タオルで\nマイクをふさいでいます。', None),
    ('b03', '話しただけの物が、\nあとでスマホの広告に出てくる。', None),
    ('b04', 'うふふ。どうやら、探偵になって\n調べてくれるみたいです。', None),
    ('b05', '映っているのは、私たち自身。\n3人目は「わたしたちの記憶」です。', 'suspects'),
    ('b06', 'スマホの下の、この小さな穴。\nこれが、マイクの入り口です。', ov_b06),
    ('b07', '入ってきた音を聞いて、門を開けるか\nどうかを決める係です。', ov_b07),
    ('b08', '柱の上のランプが、\nオレンジ色にともっています。', ov_b08),
    ('b09', '結果は……そんなアプリは、\n一つも見つからなかった！', ov_b09),
    ('b10', 'しずくの印の箱は、「いた場所」。', ov_b10),
    ('b11', '箱はスマホを飛び出し、電波に乗って、\n町をこえ、山をこえて……。', None),
    ('b12', 'そして、一番高い値段をつけたテントの会社の\n広告が、ニュースのページに出るのです。', None),
    ('b13', 'そして二人のスマホは、同じ電車の\n無料Wi-Fiにつないでいました。', ov_b13),
    ('b14', 'ロボットなのに、季節の移り変わりに\n気づくとは。なかなかの名探偵です。', ov_b14),
    ('b15', '1枚、2枚、3枚。全部で3枚です！', ov_b15),
    ('b16', '外れはたくさんあるのに、\n当たりだけを数えている。', ov_b16),
    ('b17', '探偵まるロボの前に、\n新たな容疑者が現れました。', None),
    ('b18', 'すると……この会社は、\n会話を何も聞いていなかった。', ov_b18),
    ('b19', 'そう。この「テント広告事件」の犯人は、\n一人ではなかったのです。', None),
    ('b20', '「やっぱり、ちょっと怖い」と感じた方は、\n設定を見直してみるのも一つの手です。', ov_b20),
    ('b21', 'ピポ、ピポ……。テントの絵を浮かべて、\n「テント」と言っているつもりみたいです。', ov_b21),
    ('b22', '今回の犯人は……探偵でした。', None),
]
for key, text, extra in S:
    if key == 'b03':
        im = scene_b03()
    elif key == 'b09':
        im = scene_b09()
    elif key == 'b20':
        im = scene_b20()
    else:
        im = Image.open('raw/board/%s.png' % key).convert('RGB')
    if extra == 'suspects':
        d = ImageDraw.Draw(im)
        boxes = []
        for t, x, y in (('①マイク', 227, 70), ('②出ていく手がかり', 627, 165), ('③わたしたちの記憶', 1040, 70)):
            boxes.append(tag(im, t, x, y))
        for i, a in enumerate(boxes):  # 札どうしが重ならないか
            for b in boxes[i + 1:]:
                assert a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1], ('札が重なる', a, b)
    elif extra:
        extra(im)
    sub(im, text)
    im.save('board/%s.png' % key)
    im.resize((390, 219), Image.LANCZOS).save('board/%s_390.png' % key)
print('ok', len(S))
