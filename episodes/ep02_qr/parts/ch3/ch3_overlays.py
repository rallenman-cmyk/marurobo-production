# 3章の重ねる図（2D）：19-02〜19-04.5「0と1から文字へ」。読んだ順の 0/1 が、区切り → 数字 → 文字 → HELLO になる
#   reading_frame(t, M, W=1280) → RGBA（上の暗い空に重ねる）。M は時刻の印（声の置き場所から決める）
#     M['a'] 19-02 頭：最初の2つの区切り（0010・000000101）が出る
#     M['b'] 19-02b：上に「英数字」「5文字」
#     M['c'] 19-03：続きの3つ（11・11・6 ビット）が出て、下に数字 779・966・24
#     M['d'] 19-04：声の「H・E・L・L・O」に合わせて上に文字 → M['hello'] で大きく HELLO
#     M['e'] 19-04.5：「ここまで」の 0000 と、すき間を埋める数（11101100 00010001）
#     M['end'] 消える
import math
from PIL import Image, ImageDraw, ImageFont
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
_F = {}
def F(s):
    if s not in _F: _F[s] = ImageFont.truetype(FB, s)
    return _F[s]
INK = (40, 46, 52); BLUE = (63, 134, 221); BLUE_L = (222, 236, 252); GRAY = (150, 158, 166); GRAY_L = (236, 238, 241); TEAL = (20, 163, 180)
SEG = [('0010', 'mode'), ('000000101', 'count'), ('01100001011', 'HE'), ('01111000110', 'LL'), ('011000', 'O'), ('0000', 'end'), ('11101100 00010001', 'pad')]
NUM = {'HE': '779', 'LL': '966', 'O': '24'}
TOP = {'mode': '英数字', 'count': '5文字', 'end': 'ここまで', 'pad': 'すき間を埋める数'}
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def pop(u): u = min(1.0, max(0.0, u)); return u * (1 + 0.25 * math.sin(math.pi * u))
def reading_frame(t, M, W=1280):
    s = W / 1280.0; H = int(720 * s)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if not (M['a'] <= t < M['end']): return im
    al = min(1.0, (t - M['a']) / 0.3, (M['end'] - t) / 0.4)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((40 * s, 22 * s, 1240 * s, 318 * s), 22 * s, fill=(250, 250, 248, int(238 * al)))
    # 区切りの幅（ビット数に比例）
    cw = 15.0; pad = 18; gap = 12
    ws = [len(b.replace(' ', '')) * cw + pad + (6 if ' ' in b else 0) for b, _ in SEG]
    x0 = (1280 - (sum(ws) + gap * (len(ws) - 1))) / 2; xs = []
    for w in ws: xs.append(x0); x0 += w + gap
    y_bits = 150
    appear = {'mode': M['a'] + 0.2, 'count': M['a'] + 0.45, 'HE': M['c'] + 0.3, 'LL': M['c'] + 0.9, 'O': M['c'] + 1.3, 'end': M['e'] + 0.3, 'pad': M['e'] + 1.2}
    for k, (bits, key) in enumerate(SEG):
        u = ease((t - appear[key]) / 0.3)
        if u <= 0: continue
        a = int(255 * al * u); x = xs[k] * s; w = ws[k] * s
        dull = key in ('mode', 'count') and t >= M['c'] + 0.3      # 文字の所が出たら、お知らせの所は少し引く
        fill = (*(GRAY_L if key in ('end', 'pad') or dull else BLUE_L), a)
        edge = (*(GRAY if key in ('end', 'pad') or dull else BLUE), a)
        d.rounded_rectangle((x, (y_bits - 25) * s - (1 - u) * 10 * s, x + w, (y_bits + 25) * s - (1 - u) * 10 * s), 9 * s, fill=fill, outline=edge, width=max(1, int(2 * s)))
        d.text((x + w / 2, y_bits * s - (1 - u) * 10 * s), bits, font=F(int(23 * s)), fill=(*INK, a), anchor='mm')
        # 上のラベル
        if key in TOP:
            tl = {'mode': M['b'], 'count': M['b'] + 0.5, 'end': M['e'] + 0.3, 'pad': M['e'] + 1.2}[key]
            v = ease((t - tl) / 0.3)
            if v > 0: d.text((x + w / 2, (y_bits + (-56 if key in ('mode', 'count') else 52)) * s), TOP[key], font=F(int((32 if key in ('mode', 'count') else 26) * s)), fill=(*(INK if key in ('mode', 'count') else GRAY), int(255 * al * v)), anchor='mm')
        # 下の数字（文字を2つずつ組にして数字に置き換えたもの）
        if key in NUM:
            v = ease((t - (appear[key] + 0.35)) / 0.3)
            if v > 0: d.text((x + w / 2, (y_bits + 50) * s), NUM[key], font=F(int(38 * s)), fill=(*TEAL, int(255 * al * v)), anchor='mm')
    # 文字：声の H・E・L・L・O に合わせて、数字の組の上に 1 文字ずつ
    letters = [('H', 'HE', -1), ('E', 'HE', 1), ('L', 'LL', -1), ('L', 'LL', 1), ('O', 'O', 0)]
    idx = {key: k for k, (_, key) in enumerate(SEG)}
    for j, (ch, key, side) in enumerate(letters):
        ta = M['d_letters'][j]; v = pop((t - ta) / 0.25)
        if v <= 0: continue
        k = idx[key]; cx = (xs[k] + ws[k] / 2 + side * 29) * s; cy = (y_bits - 58) * s; h = 25 * s * v
        d.rounded_rectangle((cx - h, cy - h, cx + h, cy + h), 8 * s, fill=(*BLUE, int(255 * al)))
        if v > 0.6: d.text((cx, cy), ch, font=F(int(34 * min(1.0, v) * s)), fill=(255, 255, 255, int(255 * al)), anchor='mm')
    v = ease((t - M['hello']) / 0.45)
    if v > 0:
        d.text((640 * s, (258 + (1 - v) * 12) * s), 'HELLO', font=F(int(72 * s)), fill=(*BLUE, int(255 * al * v)), anchor='mm')
    return im
