# 本番用の動く図（2D）：1920×1080。画面いっぱいの図（明るい地）と、上に重ねる札・メーター（透明つき）
#   FIG[名前](t, dur, cue) → PIL RGBA。t は図が出てからの秒、dur は出ている長さ、cue は {要素: 出る秒} の上書き（声に合わせる）
#   座標は 1280×720 で考えて 1.5 倍で描く（確認用の fig2d と同じ配置）。字は字幕（1280基準 56px）より小さくしない所は大きく
import json, math, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.dirname(HERE)
A = json.load(open(os.path.join(P, 'ch1', 'qr_assets.json')))
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; K = 1.5; W, H = 1920, 1080
_F = {}
def F(n):
    n = int(n * K)
    if n not in _F: _F[n] = ImageFont.truetype(FB, n)
    return _F[n]
BG = (238, 241, 244); INK = (40, 46, 52); GRAY = (150, 158, 166); BLUE = (63, 134, 221); BLUE_L = (222, 236, 252); ORANGE = (240, 149, 58); OR_L = (251, 227, 200)
RED = (217, 71, 90); TEAL = (20, 163, 180); WHITE = (255, 255, 255); BLACK = (21, 25, 31); PANEL = (250, 250, 248)
H_ = A['symbols']['HELLO_H']['matrix']; L_ = A['symbols']['HELLO_L']['matrix']
ROBOT = Image.open(os.path.join(P, 'ch4', 'cut', 'robot_look_right.png')); ROBOT = ROBOT.crop(ROBOT.split()[3].getbbox())
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def pop(u): u = min(1.0, max(0.0, u)); return u * (1 + 0.22 * math.sin(math.pi * u))
class D:
    """1280×720 の座標で描くと 1.5 倍で描かれる。a（0〜1）で透明度"""
    def __init__(s, im, blend=False):
        s.im = im; s.d = ImageDraw.Draw(im)
        s.blend = blend
        if blend: s.d.draw = Image.core.draw(im.im, 1)   # 地のある図：薄い色は地と混ぜる（フェードが効くように）
    def rect(s, b, fill=None, outline=None, width=1, r=0, a=1.0):
        b = [v * K for v in b]; f = fill and (*fill, int(255 * a)); o = outline and (*outline, int(255 * a))
        if r: s.d.rounded_rectangle(b, r * K, fill=f, outline=o, width=max(1, int(width * K)))
        else: s.d.rectangle(b, fill=f, outline=o, width=max(1, int(width * K)))
    def text(s, xy, t, size, col, a=1.0, anchor='mm'):
        if a <= 0.004: return
        if a >= 0.996 or not getattr(s, 'blend', False): s.d.text((xy[0] * K, xy[1] * K), t, font=F(size), fill=(*col, int(255 * a)), anchor=anchor); return
        # 地のある図で薄く出す字：別の層に描いて重ねる（そのまま描くと薄くならない）
        x0, y0, x1, y1 = s.d.textbbox((xy[0] * K, xy[1] * K), t, font=F(size), anchor=anchor); x0, y0 = int(x0) - 2, int(y0) - 2
        L = Image.new('RGBA', (int(x1) - x0 + 4, int(y1) - y0 + 4), (0, 0, 0, 0)); ImageDraw.Draw(L).text((xy[0] * K - x0, xy[1] * K - y0), t, font=F(size), fill=(*col, int(255 * a)), anchor=anchor)
        s.im.alpha_composite(L, (max(0, x0), max(0, y0)), (max(0, -x0), max(0, -y0)))
    def line(s, pts, col, width, a=1.0): s.d.line([v * K for v in pts], fill=(*col, int(255 * a)), width=max(1, int(width * K)))
    def ell(s, b, fill, a=1.0): s.d.ellipse([v * K for v in b], fill=(*fill, int(255 * a)))
    def poly(s, pts, fill, a=1.0): s.d.polygon([(x * K, y * K) for x, y in pts], fill=(*fill, int(255 * a)))
def canvas(): im = Image.new('RGBA', (W, H), (*BG, 255)); return im, D(im, blend=True)
def clear(): im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); return im, D(im)
def robot(im, x=40, y=470, h=220, look=0.0):
    r = ROBOT.resize((int(ROBOT.width * h * K / ROBOT.height), int(h * K)), Image.LANCZOS)
    im.alpha_composite(r, (int(x * K), int((y + 4 * math.sin(look)) * K)))
def qr(d, mtx, x0, y0, m, quiet=2, a=1.0):
    n = len(mtx); d.rect((x0, y0, x0 + (n + 2 * quiet) * m, y0 + (n + 2 * quiet) * m), fill=WHITE, a=a)
    for r in range(n):
        for c in range(n):
            if mtx[r][c]: d.rect((x0 + (c + quiet) * m, y0 + (r + quiet) * m, x0 + (c + quiet + 1) * m - 0.4, y0 + (r + quiet + 1) * m - 0.4), fill=BLACK, a=a)
    return lambda r, c: (x0 + (c + quiet + 0.5) * m, y0 + (r + quiet + 0.5) * m)
def C(cue, k, v): return cue.get(k, v) if cue else v
def tint_box(d, cc, mtx, b, m, a=1.0):
    """箱 b のマスを橙で塗る（黒いマス→濃い橙、白いマス→薄い橙。柄は見えたまま）"""
    for (r, c) in A['boxes'][str(b)]:
        x, y = cc(r, c); d.rect((x - m / 2, y - m / 2, x + m / 2 - 0.4, y + m / 2 - 0.4), fill=(196, 104, 24) if mtx[r][c] else (252, 214, 170), a=a)
# ---------------- 画面いっぱいの図
def url(t, dur, cue=None):
    im, d = canvas(); s = 'https://example.com/qr'; w = 54; x0 = 640 - len(s) * w / 2
    d.text((640, 110), 'ウェブサイトのQRコード', 56, INK, a=ease(t / 0.4))
    for k, ch in enumerate(s):
        u = pop((t - C(cue, 'letters', 0.5) - 0.09 * k) / 0.25)
        if u <= 0: continue
        x = x0 + k * w; h = 46 * u; d.rect((x + 3, 260 - h, x + w - 3, 260 + h), fill=BLUE_L, outline=BLUE, width=2, r=10)
        if u > 0.6: d.text((x + w / 2, 260), ch, 48, INK)
    d.text((640, 390), '1文字ずつ、箱に入れる', 54, GRAY, a=ease((t - C(cue, 'note', 2.8)) / 0.4)); robot(im, look=t); return im
def bigger(t, dur, cue=None):
    import segno
    im, d = canvas(); big_ = [list(r) for r in segno.make('https://example.com/qr/' + 'a' * 40, error='h', boost_error=False).matrix]
    a1 = ease(t / 0.4); a2 = ease((t - C(cue, 'big', 1.2)) / 0.5)
    d.text((330, 70), '文字が少ない', 56, INK, a=a1); qr(d, H_, 330 - 12.5 * 11, 120, 11, a=a1); d.text((330, 460), '21×21マス・箱26個', 50, GRAY, a=a1)
    if a2 > 0:
        mb = max(3, int(300 / (len(big_) + 4))); n = (len(big_) + 4) * mb
        d.text((940, 70), '文字が多い', 56, INK, a=a2); qr(d, big_, 940 - n / 2, 120, mb, a=a2); d.text((940, 460), '%d×%dマス・箱が多い' % (len(big_), len(big_)), 50, GRAY, a=a2)
    return im
def nearfar(t, dur, cue=None):
    im, d = canvas()
    for k, (cx, m, lab) in enumerate(((360, 12, '近い：大きく写る'), (920, 5, '遠い：小さく写る'))):
        a = ease((t - k * C(cue, 'far', 1.2)) / 0.5)
        if a <= 0: continue
        d.rect((cx - 160, 50, cx + 160, 410), fill=(28, 32, 38), r=32, a=a); d.rect((cx - 144, 66, cx + 144, 394), fill=(232, 228, 220), a=a)
        mm = int(m * 0.8 * (0.6 + 0.4 * a)); n = 25 * mm; cc = qr(d, H_, cx - n / 2, 230 - n / 2, mm, a=a); d.text((cx, 470), lab, 54, INK, a=a)
        uc = ease((t - C(cue, 'cell', 9e9) - 0.3 * k) / 0.4)          # v11 #27：「1マス」がどこで、どのくらいの大きさか
        if uc > 0:
            x, y = cc(0, 0); d.rect((x - mm / 2 - 3, y - mm / 2 - 3, x + mm / 2 + 3, y + mm / 2 + 3), outline=RED, width=4, a=uc)
            lx, ly = (cx - 210, 120) if k == 0 else (cx + 210, 120); d.line((x, y, lx, ly + 30), RED, 3, a=uc)
            d.rect((lx - 80, ly - 10, lx + 80, ly + 60), fill=RED, r=14, a=uc); d.text((lx, ly + 25), '1マス', 44, WHITE, a=uc)
    return im
def ruler(t, dur, cue=None):
    im, d = canvas(); m = 46; x0 = 640 - 10.5 * m; d.text((640, 180), '定規の目盛りのように、1マスずつ', 54, INK, a=ease(t / 0.4))
    for c in range(21):
        u = ease((t - 0.4 - 0.05 * c) / 0.2)
        if u <= 0: continue
        d.rect((x0 + c * m, 300, x0 + (c + 1) * m - 2, 300 + m), fill=BLACK if c % 2 == 0 else WHITE, outline=(200, 205, 210), a=u)
        d.line((x0 + c * m, 260, x0 + c * m, 300), INK, 3 if c % 5 == 0 else 2, a=u)
    if t > 1.5: d.line((x0, 260, x0 + 21 * m, 260), INK, 3); d.line((x0 + 21 * m, 260, x0 + 21 * m, 300), INK, 3)
    a = ease((t - C(cue, 'one', 2.2)) / 0.3)
    if a > 0: d.rect((x0 + 4 * m, 296, x0 + 5 * m, 300 + m + 4), outline=RED, width=5, a=a); d.text((x0 + 4.5 * m, 420), '1マス', 58, RED, a=a)
    robot(im, look=t); return im
def times21(t, dur, cue=None):
    im, d = canvas(); m = 13; ox = 640 - 12.5 * m; qr(d, H_, ox, 110, m)
    a = ease((t - 0.3) / 0.3); d.rect((ox + 2 * m, 110 + 2 * m, ox + 3 * m, 110 + 3 * m), outline=RED, width=4, a=a)
    u = ease((t - C(cue, 'grow', 1.0)) / 1.2)
    if u > 0: d.rect((ox + 2 * m, 110 + 2 * m, ox + 2 * m + 21 * m * u, 110 + 2 * m + 21 * m * u), outline=RED, width=4)
    d.text((640, 490), '1マス × 21 ＝ QRコード全体の大きさ', 56, INK, a=ease((t - C(cue, 'text', 1.6)) / 0.4)); return im
def three(t, dur, cue=None):
    im, d = canvas(); items = ['QRコードを見つけた', '向きが分かった', 'マスの大きさが分かった']
    for k, s in enumerate(items):
        a = ease((t - C(cue, 'step', 0.9) * k) / 0.35)
        if a <= 0: continue
        y = 150 + k * 130; d.rect((250, y - 52, 1030, y + 52), fill=WHITE, outline=(200, 205, 210), width=2, r=20, a=a)
        d.text((315, y), '✓', 60 * pop(min(1, (t - C(cue, 'step', 0.9) * k - 0.2) / 0.3)) + 1, TEAL, a=a); d.text((375, y), s, 54, INK, a=a, anchor='lm')
    robot(im, look=t); return im
def manual(t, dur, cue=None):
    im, d = canvas(); a = ease(t / 0.4); d.rect((350, 50, 930, 420), fill=WHITE, outline=(190, 195, 200), width=3, r=18, a=a); d.text((640, 115), '説明書', 64, INK, a=a)
    for k in range(2):                                            # v11：中身（予備の数・柄の番号）は、言う場面で上の札に出す。ここでは「2つ」だけ
        a2 = ease((t - C(cue, 'line', 0.8) - 0.5 * k) / 0.4); d.text((400, 225 + k * 100), '%d．' % (k + 1), 56, INK, a=a2, anchor='lm'); d.rect((470, 205 + k * 100, 860, 245 + k * 100), fill=(226, 230, 234), r=10, a=a2)
    d.text((640, 480), 'QRコードの「読み方」', 54, GRAY, a=a); robot(im, look=t); return im
def shop(t, dur, cue=None):
    im, d = canvas()
    for k, (cx, sign) in enumerate(((340, True), (940, False))):
        a = ease((t - k * C(cue, 'second', 1.0)) / 0.4)
        if a <= 0: continue
        d.rect((cx - 200, 180, cx + 200, 420), fill=(214, 196, 170), a=a); d.rect((cx - 60, 310, cx + 60, 420), fill=(120, 90, 60), a=a)
        d.poly([(cx - 230, 180), (cx + 230, 180), (cx + 200, 130), (cx - 200, 130)], (200, 80, 70), a=a)
        if sign: d.rect((cx - 150, 40, cx + 150, 115), fill=WHITE, outline=INK, width=3, r=12, a=a); d.text((cx, 78), 'お店', 54, INK, a=a)
        else: d.text((cx, 78), '？', 80 * pop((t - 1.6) / 0.3) + 1, RED, a=a)
        d.text((cx, 475), '看板がある' if sign else '看板がない', 56, INK, a=a)
    return im
def toc(t, dur, cue=None):
    im, d = canvas(); a = ease(t / 0.4); d.rect((290, 110, 990, 420), fill=WHITE, outline=(190, 195, 200), width=3, r=18, a=a); d.text((640, 175), '目次', 64, INK, a=a)
    b = ease((t - C(cue, 'row', 0.6)) / 0.4); d.text((330, 300), '英字と数字', 58, INK, a=b, anchor='lm'); d.text((950, 300), '5文字', 66, BLUE, a=b, anchor='rm')
    for k in range(9): d.ell((630 + k * 13 - 3, 310 - 3, 630 + k * 13 + 3, 310 + 3), (160, 166, 172), a=b)      # 本の目次の点線。右端にページ数のかわりに文字数
    robot(im, look=t); return im
def alnum(t, dur, cue=None):
    im, d = canvas(); chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'; w = 100; h = 70; d.text((640, 42), '英字と数字の表', 52, INK)
    hl = {'H': C(cue, 'H', 9e9), 'E': C(cue, 'E', 9e9), 'L': C(cue, 'L', 9e9), 'O': C(cue, 'O', 9e9)}
    for k, ch in enumerate(chars):
        a = ease((t - 0.02 * k) / 0.25)
        if a <= 0: continue
        r, c = divmod(k, 12); x = 40 + c * w; y = 84 + r * (h + 62); on = ch in hl and t >= hl[ch]
        d.rect((x, y, x + w - 8, y + h), fill=BLUE if on else WHITE, outline=(190, 195, 200), width=2, r=10, a=a)
        d.text((x + (w - 8) / 2, y + h / 2), ch, 48, WHITE if on else INK, a=a); d.text((x + (w - 8) / 2, y + h + 30), str(k), 46, BLUE if on else GRAY, a=a)
    vals = [(hl[c], '%s＝%d' % (c, chars.index(c))) for c in 'HELO']; shown = [s for tt, s in vals if t >= tt]
    if shown: d.text((640, 505), '　'.join(shown), 58, INK)
    return im
def bignum(t, dur, cue=None):
    im, d = canvas()
    for k, (x, lab, s, sub) in enumerate(((380, '本当の数字', '0〜255', '最大3ケタ'), (900, '今回', '0〜9', '1ケタ'))):
        a = ease((t - k * C(cue, 'small', 1.6)) / 0.4)
        if a <= 0: continue
        d.text((x, 130), lab, 56, INK, a=a); d.rect((x - 200, 200, x + 200, 400), fill=BLUE_L, outline=BLUE, width=4, r=24, a=a); d.text((x, 300), s, 72, INK, a=a)
        d.text((x, 470), sub, 58, GRAY, a=min(a, ease((t - C(cue, 'sub%d' % (k + 1), 0.0)) / 0.4)))      # v11 #58：「最大3ケタ」「1ケタ」は言ってから
    if t > C(cue, 'small', 1.6): d.text((640, 300), '→', 80, GRAY, a=ease((t - C(cue, 'small', 1.6)) / 0.3))
    robot(im, look=t); return im
def bits(t, dur, cue=None):
    im, d = canvas(); tf = C(cue, 'flip', 9e9); u = ease((t - tf) / 1.0); w = 120; x0 = 640 - 4 * w     # v11 #61：ゆっくり
    d.text((640, 70), 'この箱の0と1', 56, INK)
    for k, b in enumerate('00101110'):
        if k == 0 and u > 0: b = '1' if u > 0.5 else '0'
        on = b == '1'; ch = k == 0 and u > 0
        if k == 0 and u > 0:                                        # 白いマスに、インクが下から広がって黒くなる
            d.rect((x0 + 6, 140, x0 + w - 6, 280), fill=WHITE, outline=RED, width=8, r=12)
            if 136 * u > 6: d.rect((x0 + 10, 280 - 136 * u, x0 + w - 10, 276), fill=BLACK, r=10)     # 出始め（高さ 6px 未満）は描かない
            d.text((x0 + w / 2, 210), b, 66, WHITE if u > 0.5 else INK); continue
        d.rect((x0 + k * w + 6, 140, x0 + (k + 1) * w - 6, 280), fill=BLACK if on else WHITE, outline=RED if ch else (190, 195, 200), width=8 if ch else 2, r=12)
        d.text((x0 + k * w + w / 2, 210), b, 66, WHITE if on else INK)
    fall = (t - (tf - 0.9)) / 0.9                                   # インクのしずくが上から落ちてくる
    if 0 <= fall < 1:
        yy = 20 + 180 * ease(fall); cx = x0 + w / 2
        d.ell((cx - 16, yy - 22, cx + 16, yy + 16), (10, 14, 40)); d.poly([(cx - 11, yy - 12), (cx + 11, yy - 12), (cx, yy - 42)], (10, 14, 40))
    if u > 0: d.text((x0 + w / 2 + 40, 320), '汚れで 0→1', 52, RED, a=u, anchor='mm')
    d.text((640, 390), '箱の数字', 54, GRAY); d.text((640, 470), '46' if u < 0.5 else '46 → 174', 84, INK if u < 0.5 else RED); return im
def summary(t, dur, cue=None):
    """26 のまとめ：メモ1つ／メモ2つ → 予備17個 → 2つで1つ×8＋確かめ1"""
    im, d = canvas()
    def row(y, left, right, a):
        d.rect((30, y - 50, 670, y + 50), fill=WHITE, outline=(200, 205, 210), width=2, r=12, a=a); d.text((350, y), left, 48, INK, a=a)
        d.text((710, y), '→', 52, GRAY, a=a); d.rect((750, y - 50, 1000, y + 50), fill=OR_L, outline=ORANGE, width=3, r=12, a=a); d.text((875, y), right, 52, INK, a=a)
        d.text((1020, y), 'で1つ直る', 48, INK, a=a, anchor='lm')
    row(110, '消えた（場所が分かる）', 'メモ1つ', ease(t / 0.4)); row(235, 'すり替わった（場所不明）', 'メモ2つ', ease((t - C(cue, 'row2', 1.5)) / 0.4))
    tb = C(cue, 'bar', 9e9); n = 26; w = 38; g = 8; x0 = (1280 - (n * w + (n - 1) * g)) / 2; y = 350
    for k in range(n):
        a = ease((t - tb - 0.03 * k) / 0.2)
        if a <= 0: continue
        col = BLUE if k < 9 else ORANGE
        if t >= C(cue, 'pairs', 9e9) and k == 25: col = TEAL
        d.rect((x0 + k * (w + g), y, x0 + k * (w + g) + w, y + w), fill=col, r=6, a=a)
    tp = C(cue, 'pairs', 9e9)
    if t >= tp:
        for j in range(8):
            a = ease((t - tp - 0.12 * j) / 0.2); x1 = x0 + (9 + 2 * j) * (w + g); x2 = x1 + 2 * w + g; d.line((x1, y + w + 10, x1, y + w + 20, x2, y + w + 20, x2, y + w + 10), ORANGE, 4, a=a)
        d.text((x0 + 9 * (w + g) + (16 * (w + g) - g) / 2 - 40, y + w + 70), '予備2つで1つ直す × 8', 52, INK, a=ease((t - tp - 1.0) / 0.3))
        d.text((1250, y + w + 70), '確かめ', 48, TEAL, a=ease((t - tp - 1.4) / 0.3), anchor='rm')
    elif t >= tb + 1.0: d.text((640, 470), '予備の箱 17個 → 直せる箱 8個', 56, INK, a=ease((t - tb - 1.0) / 0.4))
    robot(im, look=t); return im
def drops_table(t, dur, cue=None):
    im, d = canvas(); d.rect((0, 0, 1280, 720), fill=(214, 196, 170)); m = 20; ox = 640 - 12.5 * m; oy = 360 - 12.5 * m; cc = qr(d, H_, ox, oy, m)
    tb = C(cue, 'tip', 0.3); ang = min(1, max(0, (t - tb) / 0.4)) * 80
    cx, cy = 1035, 450; L = 70; ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(-45, -70), (45, -70), (45, 70), (-45, 70)]; d.poly([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], (30, 40, 90))
    for k, (r, c) in enumerate(A['experiments']['ink12']['drops']):
        u = ease((t - tb - 0.5 - 0.08 * k) / 0.15)
        if u <= 0: continue
        x, y = cc(r, c); d.ell((x - 9 * u, y - 8 * u, x + 9 * u, y + 8 * u), (10, 14, 40))
    d.rect((330, 24, 950, 94), fill=PANEL, r=16, a=ease((t - C(cue, 'note', 2.5)) / 0.4) * 0.92); d.text((640, 59), '12か所・全体のたった3%', 56, INK, a=ease((t - C(cue, 'note', 2.5)) / 0.4)); robot(im, x=60, y=450, h=200, look=t); return im
def logo_qr(t, dur, cue=None):
    im, d = canvas(); d.rect((0, 0, 1280, 720), fill=(214, 196, 170)); m = 20; ox = 640 - 12.5 * m; oy = 360 - 12.5 * m; cc = qr(d, H_, ox, oy, m)
    tl = C(cue, 'logo', 0.4); u = ease((t - tl) / 0.5); x, y = cc(10, 10)
    walk = (t - (tl - 1.6)) / 1.6                                   # v11 #75：まるロボが顔のロゴを持って来て、真ん中に置く
    if 0 <= walk < 1:
        rx = 60 + (220 - 60) * ease(walk); hop = 12 * abs(math.sin(walk * math.pi * 4))
        rb = ROBOT.resize((int(ROBOT.width * 200 * K / ROBOT.height), int(200 * K)), Image.LANCZOS); im.alpha_composite(rb, (int(rx * K), int((450 - hop) * K)))
        lg = ROBOT.resize((int(ROBOT.width * 90 * K / ROBOT.height), int(90 * K)), Image.LANCZOS); im.alpha_composite(lg, (int((rx + 40) * K), int((380 - hop) * K)))
    if u > 0:
        d.rect((x - 3.6 * m, y - 3.6 * m, x + 3.6 * m, y + 3.6 * m), fill=WHITE, r=16, a=u)
        r = ROBOT.resize((int(ROBOT.width * 5.6 * m * K / ROBOT.height), int(5.6 * m * K)), Image.LANCZOS)
        if u < 1: al = r.split()[3].point(lambda v: int(v * u)); r.putalpha(al)
        im.alpha_composite(r, (int(x * K - r.width / 2), int(y * K - r.height / 2)))
    td = C(cue, 'drop', 9e9); x2, y2 = cc(*A['experiments']['logo7_ink1']['drop'])
    fall = (t - (td - 0.8)) / 0.8                                   # v11 #78：しずくが上から垂れてくる
    if 0 <= fall < 1:
        yy = -30 + (y2 + 30) * ease(fall) ** 1.6; d.ell((x2 - 9, yy - 12, x2 + 9, yy + 8), (10, 14, 40)); d.poly([(x2 - 6, yy - 6), (x2 + 6, yy - 6), (x2, yy - 26)], (10, 14, 40))
    if t >= td:
        s = pop((t - td) / 0.25); d.ell((x2 - 9 * s, y2 - 8 * s, x2 + 9 * s, y2 + 8 * s), (10, 14, 40))
        ur = ease((t - td - 0.2) / 0.3) * (1 if t - td < 3.0 else max(0, 1 - (t - td - 3.0) / 0.5))
        if ur > 0: d.d.ellipse([(x2 - 40) * K, (y2 - 40) * K, (x2 + 40) * K, (y2 + 40) * K], outline=(*RED, int(255 * ur)), width=int(6 * K))
    tp = C(cue, 'proud', 9e9); hop = 18 * abs(math.sin((t - tp) * 9)) if 0 <= t - tp < 1.4 else 0   # 「ちょっと得意げ」：ぴょんぴょん
    if not (0 <= walk < 1): robot(im, x=60 if walk < 0 else 220, y=450 - hop, h=200, look=t)   # 運んだあとは、QR のすぐ左に立つ
    return im
def two_qr(t, dur, cue=None):
    im, d = canvas(); m = 12; tb = C(cue, 'box', 9e9); tr = C(cue, 'result', 9e9)
    for k, (mtx, lab, nb) in enumerate(((L_, '予備 7個', 19), (H_, '予備 17個', 9))):
        a = ease((t - 0.5 * k) / 0.4); cx = 330 + k * 620; ox = cx - 12.5 * m; cc = qr(d, mtx, ox, 130, m, a=a)
        w = 300; d.rect((cx - w / 2, 70, cx - w / 2 + w * nb / 26, 102), fill=BLUE, a=a); d.rect((cx - w / 2 + w * nb / 26, 70, cx + w / 2, 102), fill=ORANGE, a=a)
        sp = [b for b in range(nb + 1, 27)]                    # 予備の箱（置く順で、文字の箱のあと）
        for b in sp: tint_box(d, cc, mtx, b, m, a)
        d.text((cx - 20, 480), '予備', 58, ORANGE, a=a, anchor='rm'); d.text((cx - 10, 480), lab.replace('予備 ', ''), 58, INK, a=a, anchor='lm')
        u = ease((t - tb - 0.4 * k) / 0.3)
        tw = tb - 0.9 + 0.4 * k                                   # v11 #80：まるロボが紙を持って来て、右下に置く
        if tw - 0.6 < t < tb + 0.4 * k + 0.9:
            w_ = ease((t - tw) / 0.6); x, y = cc(18, 18); rx = x + 140 - 60 * w_ - 80 * ease((t - tb - 0.4 * k - 0.3) / 0.5)
            r = ROBOT.resize((int(ROBOT.width * 130 * K / ROBOT.height), int(130 * K)), Image.LANCZOS); im.alpha_composite(r, (int(rx * K), int((y - 40 - 10 * math.sin(min(1, max(0, (t - tw) / 0.6)) * math.pi)) * K)))
            if u <= 0 and t > tw: d.rect((rx - 2.5 * m - 10, y - 2.5 * m - 60, rx + 2.5 * m - 10, y + 2.5 * m - 60), fill=(240, 240, 240), outline=GRAY, width=2)
        if u > 0: x, y = cc(18, 18); d.rect((x - 2.5 * m, y - 2.5 * m - (1 - u) * 60, x + 2.5 * m, y + 2.5 * m - (1 - u) * 60), fill=(240, 240, 240), outline=GRAY, width=2)
        v = ease((t - tr - 0.6 * k) / 0.3)
        if v > 0:
            d.rect((cx - 150, 240, cx + 150, 330), fill=WHITE, outline=RED if k == 0 else TEAL, width=5, r=16, a=v * 0.95)
            d.text((cx, 285), '読めない' if k == 0 else '読める', 60, RED if k == 0 else TEAL, a=v)
    return im
def balance(t, dur, cue=None):
    im, d = canvas(); tilt = -12 * ease((t - C(cue, 'tilt', 1.0)) / 1.0); cx, cy = 640, 220; a = math.radians(tilt); L = 360
    d.poly([(cx - 40, 520), (cx + 40, 520), (cx, cy)], (120, 126, 134))
    xl, yl = cx - L * math.cos(a), cy + L * math.sin(a); xr, yr = cx + L * math.cos(a), cy - L * math.sin(a); d.line((xl, yl, xr, yr), INK, 10)
    for x, y, s, col in ((xl, yl, '汚れへの強さ', ORANGE), (xr, yr, '入れられる文字の数', BLUE)):
        d.line((x, y, x, y + 110), INK, 4); d.rect((x - 245, y + 110, x + 245, y + 200), fill=col, r=14); d.text((x, y + 155), s, 50, WHITE)
    if tilt: d.text((640, 60), '予備を増やすと…', 56, INK, a=ease((t - C(cue, 'tilt', 1.0)) / 0.4))
    return im
def thirty(t, dur, cue=None):
    """v11（#86 わかりにくい）：一度に全部出さず、声に合わせて 1 つずつ。①「30%＝広さではなく箱の数」→ ②予備がいちばん多いとき → ③26個のうち8個が灰色 → ④だいたい3割"""
    im, d = canvas(); n = 26; w = 38; g = 8; x0 = (1280 - (n * w + (n - 1) * g)) / 2
    a0 = ease(t / 0.4); d.rect((210, 30, 1070, 110), fill=WHITE, outline=(200, 205, 210), width=2, r=16, a=a0)
    d.text((640, 70), '「30%」＝ 広さ ではなく 箱の数', 52, INK, a=a0)
    tb = C(cue, 'boxes', 2.5); ab = ease((t - tb) / 0.4)
    if ab > 0:
        d.text((640, 170), '予備を一番多くしたとき', 48, ORANGE, a=ab)
        for k in range(n):
            gray = k < 8 and t >= C(cue, 'gray', tb + 1.0) + 0.15 * k
            d.rect((x0 + k * (w + g), 230, x0 + k * (w + g) + w, 230 + w), fill=(110, 116, 123) if gray else (205, 210, 216), r=6, a=ab)
        d.text((640, 330), '26個のうち 8個まで 直せる', 60, INK, a=ease((t - C(cue, 'gray', tb + 1.0) - 1.2) / 0.4))
        d.text((640, 430), '8 ÷ 26 ＝ だいたい 3割（30%）', 60, RED, a=ease((t - C(cue, 'pct', tb + 3.0)) / 0.4))
    robot(im, x=40, y=470, h=200, look=t); return im
def levels(t, dur, cue=None):
    """v11（#83）：予備の量は 4 段階（L・M・Q・H）。棒の橙が予備の多さ。32-06b で「工場は多め・ふだんは中くらい」"""
    im, d = canvas(); d.text((640, 60), '予備の量は　4段階から選べる', 58, INK, a=ease(t / 0.4))
    for k, (lv, p, nm) in enumerate((('L', 7, '少なめ'), ('M', 15, '中くらい'), ('Q', 25, '多め'), ('H', 30, '一番多い'))):
        a = ease((t - 0.4 - 0.3 * k) / 0.35)
        if a <= 0: continue
        cx = 205 + k * 290; d.rect((cx - 120, 130, cx + 120, 470), fill=WHITE, outline=(200, 205, 210), width=2, r=18, a=a)
        d.text((cx, 180), lv, 66, INK, a=a); hh = 220; d.rect((cx - 40, 230, cx + 40, 230 + hh), fill=(222, 236, 252), r=8, a=a)
        d.rect((cx - 40, 230 + hh * (1 - p / 30 * 0.9), cx + 40, 230 + hh), fill=ORANGE, r=8, a=a); d.text((cx, 505), nm, 46, GRAY, a=a)
    tf = C(cue, 'use', 9e9); u = ease((t - tf) / 0.4)
    if u > 0:
        for k, lab in ((3, '工場'), (1, 'ふだん')):
            cx = 205 + k * 290; d.rect((cx - 125, 125, cx + 125, 475), outline=RED if k == 3 else TEAL, width=6, r=20, a=u)
            d.rect((cx - 78, 100, cx + 78, 148), fill=RED if k == 3 else TEAL, r=14, a=u); d.text((cx, 124), lab, 44, WHITE, a=u)     # 札は箱の上の縁に（字幕の帯にかけない）
    return im
def boxbar(t, dur, cue=None):
    """v11（#82 まだ天秤の話ではない）：箱は全部で 26 個（大きさで決まる）→ 予備を増やすと、文字の箱が減る"""
    im, d = canvas(); n = 26; w = 38; g = 8; x0 = (1280 - (n * w + (n - 1) * g)) / 2
    d.text((640, 90), '箱は 全部で 26個（QRコードの大きさで決まる）', 52, INK, a=ease(t / 0.4))
    tm = C(cue, 'more', 9e9); u = ease((t - tm) / 1.2); nb = round(9 - 4 * u)       # 文字の箱 9 → 5
    for k in range(n): d.rect((x0 + k * (w + g), 230, x0 + k * (w + g) + w, 230 + 60), fill=BLUE if k < nb else ORANGE, r=8, a=ease((t - 0.3 - 0.02 * k) / 0.3))
    d.text((x0, 340), '文字の箱 %d個' % nb, 54, BLUE, a=ease((t - 0.8) / 0.4), anchor='lm'); d.text((1280 - x0, 340), '予備 %d個' % (n - nb), 54, ORANGE, a=ease((t - 0.8) / 0.4), anchor='rm')
    if u > 0: d.text((640, 450), '予備を増やす　→　文字の箱が減る', 56, RED, a=min(1, u * 2))
    robot(im, x=40, y=470, h=200, look=t); return im
def end_parts(t, dur, cue=None):
    """v11（#91 話と絵が合っていない）：QR の中に、目印（赤）と予備（橙）も入っている"""
    im, d = canvas(); m = 17; ox = 640 - 12.5 * m; oy = 70; cc = qr(d, H_, ox, oy, m)
    a1 = ease((t - C(cue, 'finder', 0.3)) / 0.4)
    for (r0, c0) in ((0, 0), (0, 14), (14, 0)):
        x, y = cc(r0, c0); d.rect((x - m / 2 - 6, y - m / 2 - 6, x + 6.5 * m + 6, y + 6.5 * m + 6), outline=RED, width=8, r=10, a=a1)
    d.rect((ox - 330, 120, ox - 40, 200), fill=RED, r=16, a=a1); d.text((ox - 185, 160), '見つける目印', 46, WHITE, a=a1)
    a2 = ease((t - C(cue, 'spare', 2.0)) / 0.4)
    for b in range(10, 27): tint_box(d, cc, H_, b, m, a2)
    d.rect((ox + 25 * m + 30, 330, ox + 25 * m + 370, 410), fill=ORANGE, r=16, a=a2); d.text((ox + 25 * m + 200, 370), '直すための予備', 46, WHITE, a=a2)
    return im
def world_icons(t, dur, cue=None):
    im, d = canvas(); items = ['工場', 'ポスター', 'レシート', '駅', 'スマホ']; d.text((640, 90), '工場から、世界中へ', 60, INK, a=ease(t / 0.4))
    for k, s in enumerate(items):
        a = ease((t - 0.4 - 0.35 * k) / 0.3)
        if a <= 0: continue
        cx = 150 + k * 245; d.rect((cx - 110, 170, cx + 110, 400), fill=WHITE, outline=(200, 205, 210), width=2, r=18, a=a); qr(d, H_, cx - 12.5 * 7, 197, 7, a=a); d.text((cx, 460), s, 52, INK, a=a)
    return im
_MK = json.load(open(os.path.join(HERE, 'mask_ff.json')))
def _grid(d, mtx, x0, y0, m, a=1.0, hl=None, wipe=None, alt=None):
    """21×21 を描く（余白1マス）。wipe（0〜1）までの列は alt の並びで描く"""
    n = len(mtx); d.rect((x0, y0, x0 + (n + 2) * m, y0 + (n + 2) * m), fill=WHITE, a=a)
    for r in range(n):
        for c in range(n):
            v = alt[r][c] if (wipe is not None and c < wipe * n) else mtx[r][c]
            if v: d.rect((x0 + (c + 1) * m, y0 + (r + 1) * m, x0 + (c + 2) * m - 0.4, y0 + (r + 2) * m - 0.4), fill=BLACK, a=a)
    return lambda r, c: (x0 + (c + 1) * m, y0 + (r + 1) * m)
def mask_fig(t, dur, cue=None):
    """14-02b〜14-03b：中身をそのまま書くと黒い塊ができる → 8種類の柄から1つを重ねる → 塊がなくなる"""
    im, d = canvas(); raw, msk, k, pats, fn = _MK['raw'], _MK['masked'], _MK['mask'], _MK['pats'], _MK['func']
    tb, tf, tp, to = C(cue, 'blob', 4.0), C(cue, 'fake', 9.5), C(cue, 'pats', 23.0), C(cue, 'over', 29.0)
    m = 15; X0, Y0 = 75, 110; P = lambda r, c: (X0 + (r * 0 + c + 1) * m, Y0 + (r + 1) * m)
    a0 = ease(t / 0.4); d.text((X0 + 172, 66), '中身をそのまま書くと', 46, INK, a=a0)
    _grid(d, raw, X0, Y0, m, a=a0)
    ub = ease((t - tb) / 0.5); up = ease((t - tp) / 0.5)
    if ub > 0:   # 黒い塊を赤で囲む
        x0, y0 = X0 + 9 * m + m, Y0 + 9 * m + m; a = ub * (1 - 0.6 * up)
        d.rect((x0 - 4, y0 - 4, x0 + 12 * m + 4, y0 + 12 * m + 4), outline=RED, width=6, r=10, a=a)
        d.text((X0 + 172, 492), '黒い塊', 60, RED, a=a)
    uf = ease((t - tf) / 0.5) * (1 - up)
    if uf > 0:   # 目印の真ん中（黒い3×3）と、塊の中の黒い3×3
        for r0, c0 in ((2, 2), (12, 13)):
            x, y = X0 + (c0 + 1) * m, Y0 + (r0 + 1) * m; d.rect((x - 5, y - 5, x + 3 * m + 5, y + 3 * m + 5), outline=ORANGE, width=6, r=6, a=uf)
        d.text((880, 170), '目印の真ん中', 56, INK, a=uf); d.text((880, 330), '塊の中の黒い四角', 56, INK, a=uf)
        for dx in (-9, 9): d.line((880 + dx, 222, 880 + dx, 278), ORANGE, 7, a=uf)            # v11（#30）：上下に並べて比べるので、等号も縦に
        d.line((X0 + 6.5 * m, Y0 + 3.5 * m, 690, 170), ORANGE, 4, a=uf * 0.9); d.line((X0 + 17 * m, Y0 + 14.5 * m, 636, 330), ORANGE, 4, a=uf * 0.9)   # どこのことか線でつなぐ
        d.text((880, 440), 'そっくり！ 迷う', 64, RED, a=ease((t - tf - 3.0) / 0.4) * (1 - up))
    if up > 0:   # 8種類の柄（青が「白黒を入れ替える所」）
        uo = ease((t - to) / 0.5); a = up * (1 - uo)
        if a > 0:
            u1 = ease((t - tp - 1.6) / 0.3)
            d.text((850, 66), '決まった8種類の柄' if u1 < 0.5 else 'この中から1つを選ぶ', 46, INK if u1 < 0.5 else BLUE, a=a * abs(1 - 2 * u1))
            for j in range(8):
                gx, gy = 470 + (j % 4) * 196, 120 + (j // 4) * 196; mm = 8; sel = j == k and t > tp + 1.6
                d.rect((gx - 6, gy - 6, gx + 21 * mm + 6, gy + 21 * mm + 6), fill=WHITE, outline=BLUE if sel else (200, 205, 210), width=7 if sel else 2, r=10, a=a)
                for r in range(21):
                    for c in range(21):
                        if fn[r][c]: d.rect((gx + c * mm, gy + r * mm, gx + (c + 1) * mm - 0.5, gy + (r + 1) * mm - 0.5), fill=(226, 230, 234), a=a)
                        elif pats[j][r][c]: d.rect((gx + c * mm, gy + r * mm, gx + (c + 1) * mm - 0.5, gy + (r + 1) * mm - 0.5), fill=BLUE, a=a)
        if uo > 0:   # 選んだ柄を重ねる：左から順に白黒が入れ替わる → 塊が消える
            w = ease((t - to - 0.6) / 1.6); XR = 700
            d.text((XR + 172, 66), '柄を重ねると', 46, INK, a=uo); d.text((640, 290), '→', 80, GRAY, a=uo)
            _grid(d, raw, XR, Y0, m, a=uo, wipe=w, alt=msk)
            if w > 0 and w < 1:
                xw = XR + (w * 21 + 1) * m; d.rect((xw - 3, Y0 + m, xw + 3, Y0 + 22 * m), fill=BLUE, a=uo)
            u2 = ease((t - to - 2.4) / 0.4)
            if u2 > 0: d.text((XR + 172, 492), '塊がなくなった！', 60, (29, 122, 62), a=u2)
    return im
# ---------------- 2章の平面の図（もとは 1920 の静止画で字が小さかった。D1・K25a/K25・K26a/K26b の代わり）
def _ch2_card():
    import re as _re
    src = open(os.path.join(P, 'ch2', 'ch2_2d.py'), encoding='utf-8').read()
    g = {'Image': Image, 'ImageDraw': ImageDraw, 'ImageFont': ImageFont, 'F': lambda n: ImageFont.truetype(FB, n), 'np': __import__('numpy'),
         'rng': __import__('numpy').random.default_rng(5), 'BLACK': (24, 27, 32), 'WHITE': (250, 250, 248), 'INK': INK, 'GRAY': GRAY}
    exec(_re.search(r'(?ms)^def card\(.*?(?=^def )', src).group(0), g); return g['card']
_CARD = None
def finder(t, dur, cue=None):
    """目印を横になぞると 1:1:3:1:1"""
    im, d = canvas(); m = 34; X0, Y0 = 90, 120; a = ease(t / 0.4)
    d.rect((X0 - 10, Y0 - 10, X0 + 7 * m + 10, Y0 + 7 * m + 10), fill=WHITE, a=a)
    for r in range(7):
        for c in range(7):
            on = r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4)
            if on: d.rect((X0 + c * m, Y0 + r * m, X0 + (c + 1) * m - 1, Y0 + (r + 1) * m - 1), fill=BLACK, a=a)
    u = ease((t - C(cue, 'scan', 0.6)) / 0.8); yy = Y0 + 3.5 * m
    if u > 0: d.rect((X0 - 30, yy - 4, X0 - 30 + (7 * m + 60) * u, yy + 4), fill=TEAL)
    d.text((820, 80), '横になぞると', 56, INK, a=ease((t - 0.8) / 0.4))
    wu = 74; bx = 820 - 3.5 * wu; v = ease((t - C(cue, 'bars', 1.4)) / 0.5)
    for k, (wd, col) in enumerate(((1, BLACK), (1, WHITE), (3, BLACK), (1, WHITE), (1, BLACK))):
        x = bx + sum((1, 1, 3, 1, 1)[:k]) * wu
        d.rect((x, 170, x + wd * wu, 300), fill=col, outline=(200, 205, 210) if col == WHITE else None, width=2, a=v)
        d.text((x + wd * wu / 2, 360), str(wd), 64, TEAL, a=v)
    d.text((820, 460), '1 : 1 : 3 : 1 : 1', 64, INK, a=ease((t - C(cue, 'bars', 1.4) - 0.8) / 0.4))
    return im
def printed(t, dur, cue=None):
    """チラシ・雑誌・段ボールを白黒に直す → 横になぞって比率を調べる"""
    global _CARD
    if _CARD is None: _CARD = _ch2_card()
    im, d = canvas(); ts = C(cue, 'scan', 9e9)
    for k, (kd, nm) in enumerate((('flyer', 'チラシ'), ('mag', '雑誌'), ('box', '段ボール'))):
        cx = 250 + k * 390; a = ease((t - 0.25 * k) / 0.4)
        if a <= 0: continue
        d.text((cx, 50), nm, 54, INK, a=a)
        c = _CARD(kd, int(170 * K), int(210 * K)).convert('RGBA'); c.putalpha(int(255 * a)); im.alpha_composite(c, (int((cx - 85) * K), int(88 * K)))
        b = ease((t - 0.8 - 0.25 * k) / 0.4)
        if b > 0:
            d.poly([(cx - 14, 312), (cx + 14, 312), (cx, 334)], GRAY, a=b)
            bw = _CARD(kd, int(170 * K), int(210 * K), bw=True).resize((int(170 * K), int(130 * K))).convert('RGBA'); bw.putalpha(int(255 * b)); im.alpha_composite(bw, (int((cx - 85) * K), int(345 * K)))
            if t >= ts:
                u = ease((t - ts - 0.2 * k) / 0.6); yy = 380 + 25 * k; d.rect((cx - 95, yy - 3, cx - 95 + 190 * u, yy + 3), fill=TEAL)
    if t > 0.9: d.text((640, 510), '↑ 白黒に直す', 52, GRAY, a=ease((t - 0.9) / 0.4))
    return im
def chart(t, dur, cue=None):
    """印刷物に出てきた比率の回数（イメージ）。1:1:3:1:1 はほとんど出てこない"""
    im, d = canvas(); vals = [0.95, 0.82, 0.71, 0.60, 0.50, 0.41, 0.33, 0.25, 0.015]; th = C(cue, 'mark', 9e9)
    d.text((80, 55), '白と黒の並び方ごとの、見つかった回数', 52, INK, anchor='lm'); d.text((1240, 55), '（イメージ）', 40, GRAY, anchor='rm')
    x0, y0, bw, gap, Hh = 110, 440, 92, 34, 320; d.line((x0 - 20, y0, x0 + 9 * (bw + gap), y0), GRAY, 3); d.text((x0, y0 + 40), '並び方（比率）いろいろ →', 42, GRAY, anchor='lm')
    for k, v in enumerate(vals):
        u = ease((t - 0.3 - 0.08 * k) / 0.4)
        if u <= 0: continue
        x = x0 + k * (bw + gap); hh = max(4, Hh * v * u); on = t >= th and k == 8
        d.rect((x, y0 - hh, x + bw, y0), fill=TEAL if on else (176, 184, 192))
    v = ease((t - th) / 0.4)
    if v > 0:
        x = x0 + 8 * (bw + gap) + bw / 2; d.d.ellipse([(x - 70) * K, (y0 - 60) * K, (x + 70) * K, (y0 + 60) * K], outline=(*TEAL, int(255 * v)), width=int(6 * K))
        d.text((1250, y0 - 150), '一番少ない', 60, TEAL, a=v, anchor='rm'); d.text((1250, 520), '1 : 1 : 3 : 1 : 1', 58, TEAL, a=v, anchor='rm')
    return im

# ---------------- v11 の重ね絵（声に合わせて出す）
def ratio_bars(t, dur, cue=None):
    """1:1:3:1:1 を、幅の違う 5 本の棒で（下の字幕と同じ字を出さず、目で比べられる形に。v10 #15 #18）。
    cue：mid＝真ん中だけ光る（3倍）、run1・run2＝声に合わせて 1 本ずつ光る"""
    im, d = clear(); al = min(1.0, t / 0.3, (dur - t) / 0.3)
    if al <= 0: return im
    u = 66; ws = (1, 1, 3, 1, 1); tot = sum(ws) * u; x0 = 640 - tot / 2; y0, y1 = 36, 112
    d.rect((x0 - 30, y0 - 18, x0 + tot + 30, y1 + 78), fill=PANEL, r=18, a=al * 0.94)
    lit = set(); tm = C(cue, 'mid', 9e9)
    for key in ('run1', 'run2'):
        tr = C(cue, key, 9e9)
        for k in range(5):
            if tr + 0.42 * k <= t < tr + 0.42 * 5 + 1.2: lit.add(k)
    x = x0
    for k, wv in enumerate(ws):
        on = k in lit or (k == 2 and tm <= t < C(cue, 'mid_end', 9e9))
        d.rect((x, y0, x + wv * u, y1), fill=BLACK if k % 2 == 0 else WHITE, outline=TEAL if on else (150, 158, 166), width=6 if on else 2, a=al)
        d.text((x + wv * u / 2, y1 + 38), str(wv), 50, TEAL if on else INK, a=al); x += wv * u
    if tm <= t < C(cue, 'mid_end', 9e9): d.text((x0 + tot + 70, (y0 + y1) / 2), '3倍', 54, RED, a=al * ease((t - tm) / 0.3), anchor='lm')
    return im
def arrows(pts):
    """3D の上に矢印と短いラベル。pts：[(x, y, ラベル, cue のキー, 向き 'down'|'up'|'left'|'right')]（座標は 1280×720）"""
    def f(t, dur, cue=None):
        im, d = clear()
        for x, y, lab, key, dr in pts:
            t0 = C(cue, key, 0.0); a = min(ease((t - t0) / 0.25), (dur - t) / 0.3)
            if a <= 0: continue
            bob = 6 * math.sin((t - t0) * 6) * (1 - min(1, (t - t0) / 1.5))
            vx, vy = {'down': (0, 1), 'up': (0, -1), 'left': (-1, 0), 'right': (1, 0)}[dr]; L = 70
            tx, ty = x - vx * (12 + bob), y - vy * (12 + bob); sx, sy = tx - vx * L, ty - vy * L
            d.line((sx, sy, tx - vx * 20, ty - vy * 20), RED, 12, a=a)
            px, py = -vy, vx; d.poly([(tx, ty), (tx - vx * 30 + px * 22, ty - vy * 30 + py * 22), (tx - vx * 30 - px * 22, ty - vy * 30 - py * 22)], RED, a=a)
            if lab:
                lx, ly = sx - vx * 34, sy - vy * 34; w = 22 + 30 * len(lab)
                d.rect((lx - w / 2, ly - 30, lx + w / 2, ly + 30), fill=RED, r=14, a=a); d.text((lx, ly), lab, 44, WHITE, a=a)
        return im
    return f
def patterns8(t, dur, cue=None):
    """右上に、さっきの 8 種類の柄（小さく）。2 本の帯に書いてあるのは「どの柄を重ねたか」（v10 #35）"""
    im, d = clear(); al = min(1.0, t / 0.3, (dur - t) / 0.3)
    if al <= 0: return im
    pats, fn, k = _MK['pats'], _MK['func'], _MK['mask']; mm = 3.2; gw = 21 * mm
    d.rect((770, 22, 1260, 22 + 2 * (gw + 16) + 70), fill=PANEL, r=16, a=al * 0.95); d.text((1015, 52), '8種類の柄', 40, INK, a=al)
    for j in range(8):
        gx, gy = 790 + (j % 4) * (gw + 52), 84 + (j // 4) * (gw + 16); sel = j == k and t > C(cue, 'sel', 1.0)
        d.rect((gx - 3, gy - 3, gx + gw + 3, gy + gw + 3), fill=WHITE, outline=BLUE if sel else (200, 205, 210), width=5 if sel else 1, a=al)
        for r in range(21):
            for c in range(21):
                if not fn[r][c] and pats[j][r][c]: d.rect((gx + c * mm, gy + r * mm, gx + (c + 1) * mm, gy + (r + 1) * mm), fill=BLUE, a=al)
        d.text((gx + gw / 2, gy + gw + 2), '', 10, INK, a=0)
    return im
def insets(items):
    """左右に 2 枚の小さな画面（前の場面の切り抜き）と見出し。items：[(PIL 画像, 見出し, cue のキー)]"""
    def f(t, dur, cue=None):
        im, d = clear()
        for k, (pic, lab, key) in enumerate(items):
            a = min(ease((t - C(cue, key, 0.0)) / 0.35), (dur - t) / 0.3)
            if a <= 0: continue
            cx = 330 + k * 620; w, h = 520, 292; x0, y0 = cx - w / 2, 150
            d.rect((x0 - 10, y0 - 10, x0 + w + 10, y0 + h + 10), fill=WHITE, r=16, a=a)
            p = pic.resize((int(w * K), int(h * K)), Image.LANCZOS).convert('RGBA'); p.putalpha(int(255 * a)); im.alpha_composite(p, (int(x0 * K), int(y0 * K)))
            d.rect((cx - 250, y0 + h + 24, cx + 250, y0 + h + 90), fill=PANEL, r=14, a=a * 0.95); d.text((cx, y0 + h + 57), lab, 40 if len(lab) > 9 else 46, INK, a=a)
        return im
    return f
def pip(pic, label):
    """左上に、前の場面の切り抜き（小さな画面）。「さきほど」「体で隠れた」などと言うときに（v10 #8 #14 #40 #69 #74）"""
    def f(t, dur, cue=None):
        im, d = clear(); a = min(ease(t / 0.3), (dur - t) / 0.3)
        if a <= 0: return im
        w, h = 400, 225; x0, y0 = 28, 26
        d.rect((x0 - 8, y0 - 8, x0 + w + 8, y0 + h + 64), fill=WHITE, r=14, a=a)
        p = pic.resize((int(w * K), int(h * K)), Image.LANCZOS).convert('RGBA'); p.putalpha(int(255 * a)); im.alpha_composite(p, (int(x0 * K), int(y0 * K)))
        d.text((x0 + w / 2, y0 + h + 30), label, 36, INK, a=a); return im
    return f
def seq_card(parts, size=64, xy=(640, 150)):
    """札の言葉を、声に合わせて少しずつ足す（v10 #50 #52）。parts：[(言葉, cue のキー)]"""
    def f(t, dur, cue=None):
        im, d = clear(); al = min(1.0, (dur - t) / 0.3)
        shown = [(s_, ease((t - C(cue, k, 0.0)) / 0.25)) for s_, k in parts if t >= C(cue, k, 0.0)]
        if not shown or al <= 0: return im
        txt = ''.join(s_ for s_, _ in shown); x0, y0, x1, y1 = d.d.textbbox((xy[0] * K, xy[1] * K), txt, font=F(size), anchor='mm'); p = 28 * K
        d.d.rounded_rectangle((x0 - p, y0 - p * 0.7, x1 + p, y1 + p * 0.7), 20 * K, fill=(*PANEL, int(240 * al)))
        x = x0
        for s_, a in shown:
            d.d.text((x, (y0 + y1) / 2), s_, font=F(size), fill=(*INK, int(255 * al * a)), anchor='lm'); x += d.d.textlength(s_, font=F(size))
        return im
    return f
def title_card(t, dur, cue=None):
    """冒頭の題（v10 #2）：3D の上に、真ん中ぞろえで大きく。地を少し暗くして字を立たせる"""
    im, d = clear(); a = min(ease(t / 0.5), 1.0)
    d.rect((0, 0, 1280, 720), fill=(10, 16, 24), a=0.45 * a)
    d.text((640, 300), 'QRコードは', 72, WHITE, a=a); d.text((640, 410), '欠けても なぜ読める？', 96, (120, 220, 230), a=ease((t - 0.25) / 0.5))
    return im
# ---------------- 重ねる札・メーター（透明つき）
def card(text, size=60, xy=(640, 150)):
    def f(t, dur, cue=None):
        im, d = clear(); al = min(1.0, t / 0.25, (dur - t) / 0.3)
        if al <= 0: return im
        s = 0.9 + 0.1 * ease(t / 0.25); x0, y0, x1, y1 = d.d.textbbox((xy[0] * K, xy[1] * K), text, font=F(size * s), anchor='mm')
        p = 28 * K; d.d.rounded_rectangle((x0 - p, y0 - p * 0.7, x1 + p, y1 + p * 0.7), 20 * K, fill=(*PANEL, int(240 * al)))
        d.d.text((xy[0] * K, xy[1] * K), text, font=F(size * s), fill=(*INK, int(255 * al)), anchor='mm'); return im
    return f
def meter(n, start=0.4, step_=0.18):
    def f(t, dur, cue=None):
        im, d = clear(); al = min(1.0, t / 0.3, (dur - t) / 0.3)
        if al <= 0: return im
        k = min(n, int((t - start) / step_) + 1) if t > start else 0; over = k > 8
        d.rect((780, 24, 1256, 178), fill=PANEL, r=18, a=al * 0.94); d.text((1018, 56), '直せる箱：8個まで', 34, INK, a=al)
        for j in range(8): d.rect((806 + j * 54, 92, 850 + j * 54, 136), fill=RED if over else ((138, 144, 151) if j < k else (225, 229, 233)), r=8, a=al)
        if k: d.text((1018, 156), '壊れた箱 %d個%s' % (k, '　あふれた' if over else ''), 28, RED if over else (90, 96, 104), a=al)
        return im
    return f
def blank(t, dur, cue=None):
    """何もない地（上に重ねる切り抜きのための台）"""
    im, d = canvas(); d.text((640, 60), '隠した広さ ではなく、壊れた箱の数', 54, INK, a=ease(t / 0.4)); return im
FIG = dict(c5_blank=blank, c5_levels=levels, c5_boxbar=boxbar, end_parts=end_parts, c1_url=url, c1_bigger=bigger, c2_nearfar=nearfar, c2_ruler=ruler, c2_times21=times21, c2_three=three, c2_manual=manual, c2_shop=shop, c3_toc=toc,
           c3_alnum=alnum, c4_bignum=bignum, c4_bits=bits, c4_summary=summary, c5_drops=drops_table, c5_logo=logo_qr, c5_two=two_qr, c5_balance=balance,
           c5_thirty=thirty, end_world=world_icons, c2_mask=mask_fig, c2_finder=finder, c2_print=printed, c2_chart=chart)
if __name__ == '__main__':
    import sys, subprocess
    out = os.path.join(HERE, 'fig_anim'); os.makedirs(out, exist_ok=True)
    demo = dict(c3_alnum={'H': 2.0, 'E': 2.6, 'L': 3.2, 'O': 3.8}, c4_bits={'flip': 1.5}, c4_summary={'bar': 2.5, 'pairs': 5.0}, c5_logo={'drop': 2.5}, c5_two={'box': 1.5, 'result': 2.6})
    names = sys.argv[1:] or list(FIG)
    from PIL import Image as I
    sheet = I.new('RGB', (480 * 4, 270 * ((len(names) + 3) // 4)), 'white')
    for j, nm in enumerate(names):
        f = FIG[nm]; dur = 6.0; cue = demo.get(nm)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', '24', '-i', '-', '-c:v', 'libx264', '-crf', '22', '-pix_fmt', 'yuv420p', os.path.join(out, nm + '.mp4')], stdin=subprocess.PIPE)
        for i in range(int(dur * 24)): ff.stdin.write(f(i / 24, dur, cue).convert('RGB').tobytes())
        ff.stdin.close(); ff.wait()
        sheet.paste(f(5.5, dur, cue).convert('RGB').resize((480, 270)), ((j % 4) * 480, (j // 4) * 270))
    sheet.save(os.path.join(out, 'sheet.png')); print('ok', len(names))
# ---------------- 4章の数字の空間：右半分のメモ（3D の看板の小さな字の代わり。スマホでも読める大きさ）
P1, P2, P3 = (52, 120, 210), (222, 118, 24), (34, 146, 84)     # 1番目・2番目・3番目の箱の色（メモの数字と箱の下の札をそろえる。v10 #63）
def _segs(d, xy, segs, size, a):
    """[(字, 色)] を真ん中ぞろえで並べて描く"""
    tw = sum(d.d.textlength(t_, font=F(size)) for t_, _ in segs); x = xy[0] * K - tw / 2
    for t_, col in segs: d.d.text((x, xy[1] * K), t_, font=F(size), fill=(*col, int(255 * a)), anchor='lm'); x += d.d.textlength(t_, font=F(size))
def memo(m1, m2=None, extra=None, xlab=False, fade=True, glow2=False, diff=False):
    """m1・m2：(見出し, 1行目, 2行目 or None, 2行目の色)。extra：下に出す大きな一行。xlab：箱の下に ×1 ×2 ×3"""
    def f(t, dur, cue=None):
        im, d = clear(); al = min(1.0, (t / 0.3) if fade else 1.0, (dur - t) / 0.25 if dur - t < 0.25 else 1.0)
        if al <= 0: return im
        for k, m in enumerate((m1, m2)):
            if not m: continue
            y0 = 24 + k * 225; title, l1, l2, c2 = (list(m) + [None, None])[:4]            # v11：下の札が字幕の帯にかからないよう少し詰める
            d.rect((700, y0, 1255, y0 + 210), fill=(253, 240, 224), outline=ORANGE, width=4, r=20, a=al * 0.97)
            d.text((728, y0 + 36), title, 34, (150, 90, 30), a=al, anchor='lm')
            if isinstance(l1, list): _segs(d, (978, y0 + 110), l1, 58 if sum(len(x) for x, _ in l1) < 12 else 48, al)
            else: d.text((978, y0 + 110), l1, 58 if len(l1) < 12 else 48, INK, a=al)
            if l2: d.text((978, y0 + 182), l2, 44, c2 or RED, a=al)
        if extra: d.rect((700, 472, 1255, 528), fill=PANEL, r=16, a=al * 0.95); d.text((978, 500), extra, 44, RED, a=al)
        if xlab:
            for k, x in enumerate((115, 330, 535)):
                col = (P1, P2, P3)[k]; d.rect((x - 46, 482, x + 46, 528), fill=RED if (glow2 and k == 1) else col, r=14, a=al)   # 箱の下に色の札（字幕の帯にかけない）
                d.text((x, 505), '×%d' % (k + 1), 42, WHITE, a=al)
        if diff:                                                       # v10 #64：ずれ（2大きい → 4大きい）がちょうど2倍、を線で結ぶ
            d.line((688, 206, 676, 206, 676, 431, 688, 431), RED, 5, a=al); d.rect((572, 222, 668, 282), fill=WHITE, outline=RED, width=3, r=10, a=al); d.text((620, 252), '2倍', 44, RED, a=al)      # 白い札にのせて、箱の角と重ならないように
        return im
    return f
