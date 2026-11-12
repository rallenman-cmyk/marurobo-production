# 1章の重ねる図（2D）：07-02.6〜6c「HELLO が 5 文字しかないから？」→「10 文字に増やしても、文字を入れる箱は 9 個のまま」
#   letters_frame(t) → 1920×1080 の RGBA（t は 1章の頭からの秒）。確認用動画と本番の組み立ての両方で使う
#   python3 c1_overlays.py OUT.mov … 重ねる区間だけの透明つき動画（qtrle）を書き出す
import os, sys, math
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c1_timeline import V, T_LETTERS, FPS
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
F = lambda s: ImageFont.truetype(FB, s)
W_, H_ = 1920, 1080
INK = (40, 46, 52); BLUE = (63, 134, 221); BLUE_L = (156, 200, 255); GRAY = (150, 158, 166)
A, B, C = V[16.3][0], V[16.5][0], V[16.7][0]
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def pop(u):                                       # 0→1 で少し大きくなってから落ち着く
    u = min(1.0, max(0.0, u)); return u * (1 + 0.25 * math.sin(math.pi * u))
def letters_frame(t):
    im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    if not (T_LETTERS[0] <= t < T_LETTERS[1]): return im
    al = min(1.0, (t - A) / 0.3, (T_LETTERS[1] - t) / 0.4)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((160, 40, 1760, 360), 28, fill=(250, 250, 248, int(235 * al)))
    word = 'HELLOWORLD'; tile, gap = 92, 14
    grow = ease((t - (B + 1.3)) / 0.45)                   # 「10文字に増やしても」：HELLO が左へずれて、WORLD が出る
    n_show = 5 + int(5 * grow > 0) * 5
    total5 = 5 * tile + 4 * gap; total10 = 10 * tile + 9 * gap
    x0 = (W_ - 260 - (total5 + (total10 - total5) * grow)) / 2; y0 = 82
    for i, ch in enumerate(word):
        if i < 5: ta = A + 0.35 + 0.28 * i                 # H・E・L・L・O を 1 枚ずつ
        else: ta = B + 1.8 + 0.16 * (i - 5)                 # W・O・R・L・D
        s = pop((t - ta) / 0.25)
        if s <= 0: continue
        x = x0 + i * (tile + gap); cx, cy = x + tile / 2, y0 + tile / 2; h = tile * s / 2
        col = BLUE if i < 5 else (90, 160, 235)
        d.rounded_rectangle((cx - h, cy - h, cx + h, cy + h), 14, fill=(*col, int(255 * al)))
        if s > 0.6: d.text((cx, cy), ch, font=F(int(60 * min(1.0, s))), fill=(255, 255, 255, int(255 * al)), anchor='mm')
        if s > 0.8: d.text((cx, y0 + tile + 30), str(i + 1), font=F(30), fill=(*GRAY, int(255 * al)), anchor='mm')
    # 何文字か
    cnt = 10 if t >= B + 1.8 + 0.16 * 4 + 0.2 else (5 if t >= A + 0.35 + 0.28 * 4 + 0.2 else None)
    if cnt: d.text((1720, 128), '%d文字' % cnt, font=F(54), fill=(*INK, int(255 * al)), anchor='rm')
    # 「文字を入れる箱は、9個のまま」：青い箱 9 個の印
    tb = B + 4.0
    if t >= tb:
        a2 = ease((t - tb) / 0.4) * al
        d.text((640, 300), '文字を入れる箱', font=F(38), fill=(*INK, int(255 * a2)), anchor='rm')
        for k in range(9):
            x = 680 + k * 62; d.rounded_rectangle((x, 276, x + 48, 324), 8, fill=(*BLUE, int(255 * a2)))
        d.text((680 + 9 * 62 + 20, 300), '9個のまま', font=F(42), fill=(*BLUE, int(255 * a2)), anchor='lm')
    return im
if __name__ == '__main__':
    import subprocess, tempfile
    out = sys.argv[1]; d = tempfile.mkdtemp()
    n = int(round((T_LETTERS[1] - T_LETTERS[0]) * FPS))
    for i in range(n): letters_frame(T_LETTERS[0] + i / FPS).save(os.path.join(d, 'l_%04d.png' % i))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(d, 'l_%04d.png'), '-c:v', 'qtrle', '-pix_fmt', 'argb', out], check=True)
    print('ok', out, n, 'frames from', T_LETTERS[0])
