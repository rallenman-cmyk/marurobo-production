# QRコード回の図（舞台C）の部品。1920×1080。動かすときは各関数に u（0〜1の進み）を渡す
#   python3 qr_diagrams.py OUT_DIR  → 見本の静止画を書き出す
import sys, os, json
from PIL import Image, ImageDraw, ImageFont
A = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'qrdata', 'qr_assets.json'), encoding='utf-8'))
W, H = 1920, 1080
FB = os.environ.get('MARU_FONT_B', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
FR = os.environ.get('MARU_FONT', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
_f = {}
def font(px, bold=True):
    k = (px, bold)
    if k not in _f: _f[k] = ImageFont.truetype(FB if bold else FR, px, index=0)
    return _f[k]
# EP01 の図と同じ地の色・字の色＋QR回の色の決まり
BG = (238, 242, 245); INK = (40, 46, 52); GRAY = (150, 158, 166); WHITE = (250, 250, 248); BLACK = (24, 27, 32)
ROLE = dict(finder=(217, 71, 90), timing=(62, 158, 98), format=(140, 85, 184), data=(63, 134, 221), spare=(240, 149, 58),
            broken=(138, 144, 151), restored=(127, 227, 240), cyan=(63, 198, 201))
def mix(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))
def canvas(bg=BG): im = Image.new('RGB', (W, H), bg); return im, ImageDraw.Draw(im)
def ctext(d, xy, s, px, fill=INK, bold=True, anchor='mm'): d.text(xy, s, font=font(px, bold), fill=fill, anchor=anchor)
def rbox(d, xyxy, fill, outline=None, w=0, r=18): d.rounded_rectangle(xyxy, r, fill=fill, outline=outline, width=w)
S = A['symbols']['HELLO_H']; M = S['matrix']; N = A['size']

def draw_qr(d, x0, y0, cell, mat=M, tint=None, quiet=1, cells_state=None):
    """tint：役割で色を乗せる（'roles'）。cells_state：{(r,c): state} で上書き"""
    d.rectangle([x0 - quiet * cell, y0 - quiet * cell, x0 + (N + quiet) * cell, y0 + (N + quiet) * cell], fill=WHITE)
    for r in range(N):
        for c in range(N):
            v = mat[r][c]; col = BLACK if v else WHITE
            st = None
            if tint == 'roles':
                lab = A['function_labels'][r][c]; b = A['box_of'][r][c]
                st = {'finder': 'finder', 'timing': 'timing', 'format': 'format', 'dark': 'format'}.get(lab) or ('data' if b and b in S['data_boxes'] else 'spare' if b else None)
            if cells_state and (r, c) in cells_state: st = cells_state[(r, c)]
            if st: col = mix(col, ROLE[st], 0.45 if v else 0.35)
            d.rectangle([x0 + c * cell, y0 + r * cell, x0 + (c + 1) * cell - 2, y0 + (r + 1) * cell - 2], fill=col)

# ---------- D1 目印の比率 1:1:3:1:1（S10）
def d1_ratio(u=1.0):
    im, d = canvas(); cell = 70; x0, y0 = 360, 150
    for r in range(7):
        for c in range(7):
            d.rectangle([x0 + c * cell, y0 + r * cell, x0 + (c + 1) * cell - 3, y0 + (r + 1) * cell - 3], fill=BLACK if M[r][c] else WHITE)
    yl = y0 + 3.5 * cell; d.line([x0 - 40, yl, x0 - 40 + (7 * cell + 80) * u, yl], fill=ROLE['cyan'], width=10)
    bx = 1060; seg = [(1, 1), (0, 1), (1, 3), (0, 1), (1, 1)]; x = bx; k = 90
    for v, w in seg:
        d.rectangle([x, yl - 60, x + w * k - 4, yl + 60], fill=BLACK if v else WHITE, outline=GRAY, width=2)
        ctext(d, (x + w * k / 2, yl + 110), str(w), 64, ROLE['cyan']); x += w * k
    ctext(d, ((bx + x) / 2, yl - 120), '左から', 46, INK)
    return im

# ---------- D2 柄を重ねる（S14）
def d2_mask():
    im, d = canvas(); cell = 22; ys = 300
    before = S['before_pattern']; mask = [[1 if (A['function_labels'][r][c] == 'data' and c % 3 == 0) else 0 for c in range(N)] for r in range(N)]
    for i, (mat, lab) in enumerate([(before, '重ねる前'), (mask, '決まった柄'), (M, 'いまのQR')]):
        x0 = 150 + i * 600; draw_qr(d, x0, ys, cell, mat)
        ctext(d, (x0 + N * cell / 2, ys - 80), lab, 54)
    for xx in (690, 1290): ctext(d, (xx, ys + N * cell / 2), '＋' if xx == 690 else '＝', 90, GRAY)
    return im

# ---------- D3 0と1から文字へ（S19）
def d3_reading():
    im, d = canvas(); segs = S['reading']['segments']; x = 120; y = 470
    cols = [GRAY, GRAY, ROLE['data'], ROLE['data'], ROLE['data'], mix(GRAY, WHITE, 0.3)]
    tops = ['英数字', '5文字', 'HE', 'LL', 'O', 'ここまで']
    kpx = 34
    for sg, col, top in zip(segs, cols, tops):
        w = len(sg['bits']) * kpx + 20
        rbox(d, [x, y, x + w, y + 110], fill=mix(col, WHITE, 0.75), outline=col, w=5, r=14)
        ctext(d, (x + w / 2, y + 55), sg['bits'], 40, INK, bold=False)
        ctext(d, (x + w / 2, y - 60), top, 58, col if col != GRAY else INK)
        x += w + 18
    ctext(d, (W / 2, 220), 'H  E  L  L  O', 110, ROLE['data'])
    return im

# ---------- D4 数字の実験（S22〜S25）：stage = 'sum','hidden','swap','sum_bad','weights'
def d4_numbers(stage='weights'):
    im, d = canvas(); vals = [2, 5, 3]
    if stage in ('swap', 'sum_bad', 'weights'): vals = [2, 7, 3]
    bw = 210; gap = 70; x0 = 170; y0 = 330
    for i, v in enumerate(vals):
        x = x0 + i * (bw + gap); hid = stage == 'hidden' and i == 1
        hi = stage == 'weights' and i == 1
        rbox(d, [x, y0, x + bw, y0 + bw], fill=mix(ROLE['data'], WHITE, 0.82) if not hid else mix(GRAY, WHITE, 0.4),
             outline=ROLE['finder'] if hi else ROLE['data'], w=10 if hi else 6, r=26)
        ctext(d, (x + bw / 2, y0 + bw / 2), '？' if hid else str(v), 140)
        if stage == 'weights': ctext(d, (x + bw / 2, y0 + bw + 70), f'×{i+1}', 64, ROLE['finder'] if hi else GRAY)
    mx = 1120
    def memo(y, title, val, now=None, diff=None):
        rbox(d, [mx, y, mx + 520, y + 190], fill=mix(ROLE['spare'], WHITE, 0.82), outline=ROLE['spare'], w=6, r=22)
        ctext(d, (mx + 260, y + 50), title, 44); ctext(d, (mx + 150, y + 125), str(val), 80)
        if now is not None:
            ctext(d, (mx + 330, y + 125), '→', 60, GRAY); ctext(d, (mx + 430, y + 125), str(now), 80, ROLE['finder'])
            ctext(d, (mx + 560, y + 125), diff, 72, ROLE['finder'], anchor='lm')
    memo(220, '合計', 10, 12 if stage in ('sum_bad', 'weights') else None, '＋2')
    if stage == 'weights':
        memo(470, '1倍＋2倍＋3倍', 21, 25, '＋4')
        ctext(d, (mx + 260, 800), '4 ÷ 2 ＝ 2', 72, ROLE['finder'])
    return im

# ---------- D5 まとめ（S26）
def d5_summary():
    im, d = canvas()
    rows = [('消えた（場所が分かる）', '予備 1つ', '1つ'), ('すり替わった（場所が分からない）', '予備 2つ', '1つ')]
    for i, (a, b, c) in enumerate(rows):
        y = 220 + i * 230
        rbox(d, [140, y, 980, y + 170], fill=WHITE, outline=GRAY, w=4); ctext(d, (560, y + 85), a, 50)
        ctext(d, (1060, y + 85), '→', 70, GRAY)
        rbox(d, [1140, y, 1500, y + 170], fill=mix(ROLE['spare'], WHITE, 0.8), outline=ROLE['spare'], w=6); ctext(d, (1320, y + 85), b, 56)
        ctext(d, (1610, y + 85), 'で', 44, GRAY); ctext(d, (1730, y + 85), c, 60)
    for k in range(26):
        x = 160 + k * 62; col = ROLE['data'] if k < 9 else ROLE['spare']
        rbox(d, [x, 760, x + 52, 812], fill=col, r=8)
    ctext(d, (W / 2, 900), '予備 17個 → 直せる箱 8個', 64)
    return im

# ---------- D6 予備の量（S34）
def d6_levels():
    im, d = canvas()
    for i, (lab, nd) in enumerate([('レベルL', 19), ('レベルH', 9)]):
        y = 300 + i * 300; ctext(d, (230, y + 40), lab, 60)
        for k in range(26):
            x = 400 + k * 52; rbox(d, [x, y, x + 44, y + 80], fill=ROLE['data'] if k < nd else ROLE['spare'], r=8)
        ctext(d, (400 + nd * 52 / 2, y + 140), f'中身 {nd}', 46, ROLE['data'])
        ctext(d, (400 + nd * 52 + (26 - nd) * 52 / 2, y + 140), f'予備 {26 - nd}', 46, ROLE['spare'])
    return im

# ---------- D7 「30%」の正体（S35）
def d7_thirty():
    im, d = canvas()
    for k in range(26):
        x = 150 + k * 62; col = ROLE['broken'] if k in (2, 5, 9, 12, 15, 18, 21, 24) else (ROLE['data'] if k < 9 else ROLE['spare'])
        rbox(d, [x, 380, x + 52, 470], fill=col, r=8)
    ctext(d, (W / 2, 640), '8 ÷ 26 ＝ 約31%', 120, INK)
    ctext(d, (W / 2, 230), '面積ではなく、箱の数', 64, INK)
    return im

# ---------- D8 壊れた箱のカウンター（5章の右上。透明PNG）
def d8_counter(nbad=6, limit=8):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    over = nbad > limit; col = ROLE['finder'] if over else (52, 168, 96)
    rbox(d, [1420, 50, 1870, 190], fill=(250, 250, 248, 235), outline=col, w=8, r=26)
    ctext(d, (1530, 120), '壊れた箱', 46, INK); ctext(d, (1740, 120), f'{nbad}／{limit}', 72, col)
    return im

# ---------- D9 見つける・読む・直す（S38。透明PNG。step=1〜3）
def d9_stages(step=3):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    labs = [('見つける', ROLE['finder']), ('読む', ROLE['data']), ('直す', ROLE['spare'])]
    for i, (s, col) in enumerate(labs[:step]):
        x = 360 + i * 420; rbox(d, [x, 60, x + 360, 190], fill=(*col, 235), r=30); ctext(d, (x + 180, 125), s, 72, WHITE)
        if i < step - 1: ctext(d, (x + 390, 125), '→', 64, WHITE)
    return im

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'; os.makedirs(out, exist_ok=True)
    jobs = dict(D1_ratio=d1_ratio, D2_mask=d2_mask, D3_reading=d3_reading,
                D4a_sum=lambda: d4_numbers('sum'), D4b_hidden=lambda: d4_numbers('hidden'), D4c_sumbad=lambda: d4_numbers('sum_bad'), D4d_weights=lambda: d4_numbers('weights'),
                D5_summary=d5_summary, D6_levels=d6_levels, D7_thirty=d7_thirty)
    for k, fn in jobs.items(): fn().save(os.path.join(out, k + '.png'))
    for k, im in dict(D8_counter_ok=d8_counter(6), D8_counter_over=d8_counter(10), D9_stages=d9_stages(3)).items():
        bg = Image.new('RGBA', (W, H), (60, 70, 80, 255)); bg.alpha_composite(im); bg.convert('RGB').save(os.path.join(out, k + '_onbg.png')); im.save(os.path.join(out, k + '.png'))
    print('ok')
