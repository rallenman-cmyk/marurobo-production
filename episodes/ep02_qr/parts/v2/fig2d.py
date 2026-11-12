# 台本 v2.0 の確認用動画で使う 2D の図（1280×720 の PNG）。python3 fig2d.py → fig/*.png
import os, json, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'fig'); os.makedirs(OUT, exist_ok=True)
P = os.path.dirname(HERE)
A = json.load(open(os.path.join(P, 'ch1', 'qr_assets.json')))
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
F = lambda n: ImageFont.truetype(FB, n)
BG = (238, 241, 244); INK = (40, 46, 52); GRAY = (150, 158, 166); BLUE = (63, 134, 221); BLUE_L = (222, 236, 252); ORANGE = (240, 149, 58); OR_L = (251, 227, 200)
RED = (217, 71, 90); TEAL = (20, 163, 180); WHITE = (255, 255, 255); BLACK = (21, 25, 31)
ROBOT = Image.open(os.path.join(P, 'ch4', 'cut', 'robot_look_right.png')); ROBOT = ROBOT.crop(ROBOT.split()[3].getbbox())
ROBOT_F = Image.open(os.path.join(P, 'ch4', 'cut', 'robot_front.png')); ROBOT_F = ROBOT_F.crop(ROBOT_F.split()[3].getbbox())
def canvas(): im = Image.new('RGBA', (1280, 720), (*BG, 255)); return im, ImageDraw.Draw(im)
def robot(im, x=40, y=470, h=220, front=False):
    r = ROBOT_F if front else ROBOT; r = r.resize((int(r.width * h / r.height), h), Image.LANCZOS); im.alpha_composite(r, (int(x), int(y)))
def save(im, name): im.convert('RGB').save(os.path.join(OUT, name + '.png')); print('fig', name)
def qr(d, mtx, x0, y0, m, quiet=2, white=WHITE, black=BLACK):
    n = len(mtx); d.rectangle((x0, y0, x0 + (n + 2 * quiet) * m, y0 + (n + 2 * quiet) * m), fill=white)
    for r in range(n):
        for c in range(n):
            if mtx[r][c]: d.rectangle((x0 + (c + quiet) * m, y0 + (r + quiet) * m, x0 + (c + quiet + 1) * m - 1, y0 + (r + quiet + 1) * m - 1), fill=black)
    return lambda r, c: (x0 + (c + quiet + 0.5) * m, y0 + (r + quiet + 0.5) * m)
H_ = A['symbols']['HELLO_H']['matrix']; L_ = A['symbols']['HELLO_L']['matrix']
# ---- 1章 07-02.7b〜e：住所の文字が1文字ずつ → 文字が多いと大きなQR
def url():
    im, d = canvas(); s = 'https://example.com/qr'
    d.text((640, 120), 'ウェブサイトのQRコード', font=F(44), fill=INK, anchor='mm')
    w = 50; x0 = 640 - len(s) * w / 2
    for k, ch in enumerate(s):
        x = x0 + k * w; d.rounded_rectangle((x + 3, 220, x + w - 3, 300), 10, fill=BLUE_L, outline=BLUE, width=2); d.text((x + w / 2, 260), ch, font=F(38), fill=INK, anchor='mm')
    d.text((640, 360), '1文字ずつ、箱に入れる', font=F(40), fill=GRAY, anchor='mm'); robot(im); save(im, 'c1_url')
def bigger():
    im, d = canvas(); import segno
    d.text((330, 90), '文字が少ない', font=F(40), fill=INK, anchor='mm'); d.text((930, 90), '文字が多い', font=F(40), fill=INK, anchor='mm')
    qr(d, H_, 230, 160, 8)
    big = segno.make('https://example.com/qr/'+'a'*40, error='h', boost_error=False).matrix
    qr(d, [list(r) for r in big], 760, 140, max(3, int(300 / (len(big) + 4))))
    d.text((330, 470), '21×21マス・箱26個', font=F(34), fill=GRAY, anchor='mm'); d.text((930, 470), '%d×%dマス・箱が多い' % (len(big), len(big)), font=F(34), fill=GRAY, anchor='mm')
    save(im, 'c1_bigger')
# ---- 2章
def nearfar():
    im, d = canvas()
    for k, (cx, m, lab) in enumerate(((360, 12, '近い：大きく写る'), (920, 5, '遠い：小さく写る'))):
        d.rounded_rectangle((cx - 160, 60, cx + 160, 420), 32, fill=(28, 32, 38)); d.rectangle((cx - 144, 76, cx + 144, 404), fill=(232, 228, 220))
        m = int(m * 0.8); n = 25 * m; qr(d, H_, cx - n / 2, 240 - n / 2, m)
        d.text((cx, 470), lab, font=F(42), fill=INK, anchor='mm')
    save(im, 'c2_nearfar')
def ruler():
    im, d = canvas(); m = 46; x0 = 640 - 10.5 * m
    for c in range(21):
        d.rectangle((x0 + c * m, 300, x0 + (c + 1) * m - 2, 300 + m), fill=BLACK if c % 2 == 0 else WHITE, outline=(200, 205, 210))
        d.line((x0 + c * m, 260, x0 + c * m, 300), fill=INK, width=3 if c % 5 == 0 else 2)
    d.line((x0 + 21 * m, 260, x0 + 21 * m, 300), fill=INK, width=3); d.line((x0, 260, x0 + 21 * m, 260), fill=INK, width=3)
    d.text((640, 200), '定規の目盛りのように、1マスずつ', font=F(44), fill=INK, anchor='mm')
    d.rectangle((x0 + 4 * m, 296, x0 + 5 * m, 300 + m + 4), outline=RED, width=5); d.text((x0 + 4.5 * m, 420), '1マス', font=F(40), fill=RED, anchor='mm')
    robot(im); save(im, 'c2_ruler')
def times21():
    im, d = canvas(); m = 14; ox = 640 - 12.5 * m; qr(d, H_, ox, 120, m)
    d.rectangle((ox + 2 * m, 120 + 2 * m, ox + 3 * m, 120 + 3 * m), outline=RED, width=4)
    d.text((640, 520), '1マス × 21 ＝ QRコード全体の大きさ', font=F(48), fill=INK, anchor='mm'); robot(im); save(im, 'c2_times21')
def three_done():
    im, d = canvas(); items = ['QRコードを見つけた', '向きが分かった', 'マスの大きさが分かった']
    for k, t in enumerate(items):
        y = 170 + k * 120; d.rounded_rectangle((330, y - 45, 950, y + 45), 20, fill=WHITE, outline=(200, 205, 210), width=2)
        d.text((390, y), '✓', font=F(52), fill=TEAL, anchor='mm'); d.text((440, y), t, font=F(44), fill=INK, anchor='lm')
    robot(im); save(im, 'c2_three')
def manual():
    im, d = canvas(); d.rounded_rectangle((440, 70, 840, 420), 18, fill=WHITE, outline=(190, 195, 200), width=3)
    d.text((640, 130), '説明書', font=F(60), fill=INK, anchor='mm')
    for k, t in enumerate(('1．予備の箱の数', '2．重ねた柄の番号')): d.text((480, 230 + k * 90), t, font=F(40), fill=INK, anchor='lm')
    d.text((640, 480), 'QRコードの「読み方」', font=F(44), fill=GRAY, anchor='mm'); robot(im); save(im, 'c2_manual')
def shop():
    im, d = canvas()
    for k, (cx, sign) in enumerate(((340, True), (940, False))):
        d.rectangle((cx - 200, 190, cx + 200, 440), fill=(214, 196, 170)); d.rectangle((cx - 60, 320, cx + 60, 440), fill=(120, 90, 60))
        d.polygon([(cx - 230, 190), (cx + 230, 190), (cx + 200, 140), (cx - 200, 140)], fill=(200, 80, 70))
        if sign: d.rounded_rectangle((cx - 150, 50, cx + 150, 125), 12, fill=WHITE, outline=INK, width=3); d.text((cx, 88), 'お店', font=F(46), fill=INK, anchor='mm')
        else: d.text((cx, 88), '？', font=F(80), fill=RED, anchor='mm')
        d.text((cx, 490), '看板がある' if sign else '看板がない', font=F(42), fill=INK, anchor='mm')
    save(im, 'c2_shop')
# ---- 3章
def toc():
    im, d = canvas(); d.rounded_rectangle((380, 120, 900, 520), 18, fill=WHITE, outline=(190, 195, 200), width=3)
    d.text((640, 180), '目次', font=F(56), fill=INK, anchor='mm'); d.text((440, 290), '英字と数字', font=F(48), fill=INK, anchor='lm'); d.text((840, 290), '5文字', font=F(48), fill=BLUE, anchor='rm')
    d.line((440, 340, 840, 340), fill=(210, 214, 218), width=2); d.text((640, 420), 'ここまで読めばいい', font=F(40), fill=GRAY, anchor='mm')
    robot(im); save(im, 'c3_toc')
def alnum(hl=False):
    im, d = canvas(); chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'; w = 92; h = 84
    d.text((640, 70), '英字と数字の表', font=F(46), fill=INK, anchor='mm')
    for k, ch in enumerate(chars):
        r, c = divmod(k, 12); x = 88 + c * w; y = 130 + r * (h + 34); on = hl and ch in 'HELO'
        d.rounded_rectangle((x, y, x + w - 8, y + h), 10, fill=BLUE if on else WHITE, outline=(190, 195, 200), width=2)
        d.text((x + (w - 8) / 2, y + h / 2), ch, font=F(40), fill=WHITE if on else INK, anchor='mm'); d.text((x + (w - 8) / 2, y + h + 16), str(k), font=F(26), fill=BLUE if on else GRAY, anchor='mm')
    if hl: d.text((640, 510), 'H＝17　E＝14　L＝21　O＝24', font=F(52), fill=INK, anchor='mm')
    save(im, 'c3_alnum_hl' if hl else 'c3_alnum')
# ---- 4章
def bignum():
    im, d = canvas(); d.text((380, 150), '本当の数字', font=F(44), fill=INK, anchor='mm'); d.text((900, 150), '今回', font=F(44), fill=INK, anchor='mm')
    for x, t, sz in ((380, '0〜255', 64), (900, '0〜9', 64)):
        d.rounded_rectangle((x - 200, 220, x + 200, 420), 24, fill=BLUE_L, outline=BLUE, width=4); d.text((x, 320), t, font=F(sz), fill=INK, anchor='mm')
    d.text((380, 480), '最大3ケタ', font=F(44), fill=GRAY, anchor='mm'); d.text((900, 480), '1ケタ', font=F(44), fill=GRAY, anchor='mm'); d.text((640, 320), '→', font=F(80), fill=GRAY, anchor='mm')
    robot(im); save(im, 'c4_bignum')
def bitflip(stage):
    im, d = canvas(); bits = '00101110' if stage == 0 else '10101110'; w = 110; x0 = 640 - 4 * w
    d.text((640, 90), 'この箱の0と1', font=F(44), fill=INK, anchor='mm')
    for k, b in enumerate(bits):
        x = x0 + k * w; on = b == '1'; ch = stage == 1 and k == 0
        d.rounded_rectangle((x + 6, 170, x + w - 6, 300), 12, fill=BLACK if on else WHITE, outline=RED if ch else (190, 195, 200), width=8 if ch else 2)
        d.text((x + w / 2, 235), b, font=F(60), fill=WHITE if on else INK, anchor='mm')
    if stage == 1: d.text((x0 + w / 2, 330), '汚れで 0→1', font=F(36), fill=RED, anchor='mm')
    d.text((640, 390), '箱の数字', font=F(44), fill=GRAY, anchor='mm'); d.text((640, 470), '46' if stage == 0 else '46 → 174', font=F(84), fill=INK if stage == 0 else RED, anchor='mm')
    save(im, 'c4_bits%d' % stage)
def d5(key):
    im, d = canvas()
    def row(y, left, right):
        d.rounded_rectangle((110, y - 42, 610, y + 42), 12, fill=WHITE, outline=(200, 205, 210), width=2); d.text((360, y), left, font=F(30), fill=INK, anchor='mm')
        d.text((660, y), '→', font=F(40), fill=GRAY, anchor='mm'); d.rounded_rectangle((710, y - 42, 930, y + 42), 12, fill=OR_L, outline=ORANGE, width=3)
        d.text((820, y), right, font=F(34), fill=INK, anchor='mm'); d.text((960, y), 'で', font=F(28), fill=GRAY, anchor='lm'); d.text((1010, y), '1つ', font=F(40), fill=INK, anchor='lm')
    row(170, '消えた場所が分かる', 'メモ 1つ')
    if key != 'D5a': row(285, 'すり替わった（場所が分からない）', 'メモ 2つ')
    if key in ('D5c', 'D5d'):
        n = 26; w = 30; g = 8; x0 = (1280 - (n * w + (n - 1) * g)) / 2; y = 410
        for k in range(n):
            col = BLUE if k < 9 else ORANGE
            if key == 'D5d' and k == 25: col = TEAL
            d.rounded_rectangle((x0 + k * (w + g), y, x0 + k * (w + g) + w, y + w), 5, fill=col)
        if key == 'D5c': d.text((640, 505), '予備の箱 17個 → 直せる箱 8個', font=F(40), fill=INK, anchor='mm')
        else:
            for j in range(8):
                a = x0 + (9 + 2 * j) * (w + g); b = a + 2 * w + g; d.line((a, y + w + 10, a, y + w + 18, b, y + w + 18, b, y + w + 10), fill=ORANGE, width=3)
            d.text((x0 + 9 * (w + g) + (16 * (w + g) - g) / 2, y + w + 46), '予備2つで1つ直す × 8', font=F(30), fill=INK, anchor='mm')
            d.text((x0 + 25 * (w + g) + w / 2, y + w + 46), '確かめ', font=F(30), fill=TEAL, anchor='mm')
    robot(im); save(im, key)
# ---- 5章
def table_drops(drops=True, logo=False, logo_drop=False):
    im, d = canvas(); d.rectangle((0, 0, 1280, 720), fill=(214, 196, 170)); m = 20; ox = 640 - 12.5 * m; oy = 360 - 12.5 * m
    cc = qr(d, H_, ox, oy, m)
    if drops:
        for (r, c) in A['experiments']['ink12']['drops']: x, y = cc(r, c); d.ellipse((x - 9, y - 8, x + 9, y + 8), fill=(10, 14, 40))
        d.rounded_rectangle((990, 380, 1080, 520), 16, fill=(30, 40, 90)); d.rectangle((1015, 350, 1055, 385), fill=(60, 60, 70))
        d.text((640, 40), '12か所・全体のたった3%', font=F(44), fill=INK, anchor='mm')
    if logo:
        x, y = cc(10, 10); d.rounded_rectangle((x - 3.6 * m, y - 3.6 * m, x + 3.6 * m, y + 3.6 * m), 16, fill=WHITE)
        r = ROBOT_F.resize((int(ROBOT_F.width * 5.6 * m / ROBOT_F.height), int(5.6 * m)), Image.LANCZOS); im.alpha_composite(r, (int(x - r.width / 2), int(y - r.height / 2)))
        if logo_drop: x2, y2 = cc(*A['experiments']['logo7_ink1']['drop']); d.ellipse((x2 - 9, y2 - 8, x2 + 9, y2 + 8), fill=(10, 14, 40))
    robot(im, x=60, y=450, h=200); save(im, 'c5_logo%s' % ('_drop' if logo_drop else '') if logo else 'c5_drops')
def two_qr(box=False):
    im, d = canvas(); m = 12
    for k, (mtx, lab, nb, ns) in enumerate(((L_, '予備 7個', 19, 7), (H_, '予備 17個', 9, 17))):
        cx = 330 + k * 620; ox = cx - 12.5 * m; cc = qr(d, mtx, ox, 150, m)
        if box: x, y = cc(18, 18); d.rectangle((x - 2.5 * m, y - 2.5 * m, x + 2.5 * m, y + 2.5 * m), fill=(240, 240, 240), outline=GRAY, width=2)
        w = 300; d.rectangle((cx - w / 2, 80, cx - w / 2 + w * nb / 26, 112), fill=BLUE); d.rectangle((cx - w / 2 + w * nb / 26, 80, cx + w / 2, 112), fill=ORANGE)
        d.text((cx, 520), lab, font=F(44), fill=INK, anchor='mm')
        if box: d.text((cx, 600), '読めない' if k == 0 else '読める', font=F(52), fill=RED if k == 0 else TEAL, anchor='mm')
    save(im, 'c5_two_box' if box else 'c5_two')
def balance(tilt):
    im, d = canvas(); cx, cy = 640, 250; a = math.radians(tilt); L = 360
    d.polygon([(cx - 40, 560), (cx + 40, 560), (cx, cy)], fill=(120, 126, 134))
    xl, yl = cx - L * math.cos(a), cy + L * math.sin(a); xr, yr = cx + L * math.cos(a), cy - L * math.sin(a)
    d.line((xl, yl, xr, yr), fill=INK, width=10)
    for x, y, t, col in ((xl, yl, '汚れへの強さ', ORANGE), (xr, yr, '入れられる文字の数', BLUE)):
        d.line((x, y, x, y + 120), fill=INK, width=4); d.rounded_rectangle((x - 170, y + 120, x + 170, y + 200), 14, fill=col); d.text((x, y + 160), t, font=F(36), fill=WHITE, anchor='mm')
    d.text((640, 640), '予備を増やすと…' if tilt else '', font=F(44), fill=GRAY, anchor='mm'); save(im, 'c5_balance%d' % (1 if tilt else 0))
def thirty():
    im, d = canvas(); n = 26; w = 38; g = 8; x0 = (1280 - (n * w + (n - 1) * g)) / 2
    for k in range(n): d.rounded_rectangle((x0 + k * (w + g), 110, x0 + k * (w + g) + w, 110 + w), 6, fill=(138, 144, 151) if k < 8 else (205, 210, 216))
    d.text((640, 220), '26個のうち 8個 → 約31%', font=F(60), fill=INK, anchor='mm')
    for k, t in enumerate(('L 約7%', 'M 約15%', 'Q 約25%', 'H 約30%')): d.text((260 + k * 250, 330), t, font=F(44), fill=RED if k == 3 else GRAY, anchor='mm')
    d.text((640, 440), '「30%」は、広さではなく 箱の数', font=F(44), fill=INK, anchor='mm'); robot(im, x=40, y=470, h=200); save(im, 'c5_thirty')
def meter_demo(): pass
# ---- 結び
def world_icons():
    im, d = canvas(); items = ['工場の伝票', '街のポスター', 'お店のレシート', '駅の案内', 'スマホの画面']
    for k, t in enumerate(items):
        cx = 150 + k * 245; d.rounded_rectangle((cx - 105, 200, cx + 105, 410), 18, fill=WHITE, outline=(200, 205, 210), width=2)
        m = 6; qr(d, H_, cx - 12.5 * m, 230, m, quiet=2); d.text((cx, 460), t, font=F(32), fill=INK, anchor='mm')
    d.text((640, 120), '工場から、世界中へ', font=F(54), fill=INK, anchor='mm'); save(im, 'end_world')
def endcard():
    im, d = canvas(); d.text((640, 260), 'QRコードは', font=F(60), fill=INK, anchor='mm'); d.text((640, 360), '欠けてもなぜ読める？', font=F(76), fill=BLUE, anchor='mm')
    robot(im, x=560, y=430, h=220, front=True); save(im, 'end_card')
if __name__ == '__main__':
    url(); bigger(); nearfar(); ruler(); times21(); three_done(); manual(); shop(); toc(); alnum(False); alnum(True); bignum(); bitflip(0); bitflip(1)
    for k in ('D5a', 'D5b', 'D5c', 'D5d'): d5(k)
    table_drops(); table_drops(drops=False, logo=True); table_drops(drops=False, logo=True, logo_drop=True); two_qr(False); two_qr(True); balance(0); balance(-12); thirty(); world_icons(); endcard()
