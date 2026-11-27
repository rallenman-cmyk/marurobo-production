# 12本目（渋滞）：3D に貼る画面の絵（スマホの道案内・車のナビ）。自前の地図（どこの地図アプリの見た目もまねしない）。字は書かない
#   色：すいている＝緑・少しこむ＝黄・こんでいる＝赤・分からない＝灰色。自分の車の印＝青緑の三角
#   画面は横向き（1024×512）。phone_seq の板は縦長なので、最後に 90 度回して保存する
# python3 make_tex12.py <出力フォルダ>
import os, sys, math, random
from PIL import Image, ImageDraw
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
W, H = 1024, 512; SS = 2
BG = (206, 211, 218); ROAD = (255, 255, 255); EDGE = (198, 203, 210); PARK = (205, 228, 196); WATER = (178, 210, 236); BLOCK = (226, 223, 216)
# 冒頭〜2章 v1 の点検：3D の画面に貼ると、色の線が細くて白っぽく見えた（引いた地図の細い道の色が見えない）。
#   線の太さに下限を付け（大通り MW・細い道 SW）、地の色を少し濃くした
MW, SW = 14 * 2, 6 * 2
GREEN = (52, 178, 102); YELLOW = (242, 194, 48); RED = (226, 58, 48); GREY = (154, 164, 178); TEAL = (47, 217, 200); NAVY = (24, 38, 74)


def base(zoom=1.0, seed=4):
    """町の地図（zoom＝何倍に引いて見るか）。道は太い大通り（横）と、曲がった先の道（縦）と、細い道の網"""
    im = Image.new("RGB", (W * SS, H * SS), BG); d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    k = SS / zoom
    cx, cy = W * SS * 0.42, H * SS * 0.62       # 交差点（画面の左寄りの下）
    # ブロック・公園・川（ブロックの上に公園と川を描く）
    G = int(12 * zoom) + 2
    for gx in range(-G, G + 1):
        for gy in range(-G, G + 1):
            x0 = cx + gx * 120 * k + 8 * k; y0 = cy + gy * 120 * k + 8 * k
            d.rectangle([x0, y0, x0 + 104 * k, y0 + 104 * k], fill=BLOCK)
    for (px, py) in ((300, -420), (-1500, -900), (1700, 700), (-2600, 500)):
        d.rectangle([cx + px * k, cy + py * k, cx + (px + 240) * k, cy + (py + 230) * k], fill=PARK)
    d.rectangle([cx - 4000 * k, cy + 128 * k, cx + 4000 * k, cy + 232 * k], fill=WATER)
    # 細い道の網
    for gx in range(-G, G + 1):
        x = cx + gx * 120 * k; d.line([x, 0, x, H * SS], fill=ROAD, width=max(2, int(9 * k)))
    for gy in range(-G, G + 1):
        y = cy + gy * 120 * k; d.line([0, y, W * SS, y], fill=ROAD, width=max(2, int(9 * k)))
    # 大通り（横）と、曲がった先の道（縦）
    d.line([0, cy, W * SS, cy], fill=EDGE, width=int(34 * k)); d.line([0, cy, W * SS, cy], fill=ROAD, width=int(28 * k))
    d.line([cx, 0, cx, cy], fill=EDGE, width=int(30 * k)); d.line([cx, 0, cx, cy], fill=ROAD, width=int(24 * k))
    return im, d, (cx, cy), k


def color_line(d, pts, col, w):
    d.line(pts, fill=col, width=w, joint="curve")


def me(d, x, y, s=1.0, heading=0.0):
    """自分の車の印（青緑の三角。白いふち）"""
    r = 64 * SS * s                 # 12本目 v1 の確認役（2 回目）：26 では画面の上で小さく、「この先」がどちらか分からなかった
    pts = []
    for a in (0, 140, 220):
        th = math.radians(a + heading)
        pts.append((x + r * math.cos(th), y - r * math.sin(th)))
    d.polygon(pts, fill=(255, 255, 255)); r2 = r * 0.72
    pts2 = []
    for a in (0, 140, 220):
        th = math.radians(a + heading); pts2.append((x + r2 * math.cos(th), y - r2 * math.sin(th)))
    d.polygon(pts2, fill=TEAL)


def save(im, name):
    im = im.resize((W, H), Image.LANCZOS).rotate(90, expand=True)
    im.save(os.path.join(OUT, name + ".png"))


def jam_icon(d, x, y, s=1.0):
    """字のない「この先 渋滞」の印：白い丸に、赤い三角と、車の列（四角 3 つ）"""
    r = 44 * SS * s
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=RED, width=int(6 * SS * s))
    for k_ in range(3):
        bx = x - r * 0.55 + k_ * r * 0.4; d.rounded_rectangle([bx, y - r * 0.12, bx + r * 0.32, y + r * 0.22], radius=int(4 * SS * s), fill=RED)


def town_colors(d, c, k, near=True):
    """町の道に色（緑・黄・赤）。near＝寄り（大通りの先が赤）"""
    cx, cy = c
    rnd = random.Random(11)
    color_line(d, [(0, cy), (cx - 200 * k, cy)], GREEN, max(int(16 * k), MW))
    color_line(d, [(cx - 200 * k, cy), (cx - 40 * k, cy)], YELLOW, max(int(16 * k), MW))
    color_line(d, [(cx, cy - 20 * k), (cx, 0)], RED, max(int(15 * k), MW))           # 曲がった先の道が赤
    color_line(d, [(cx, cy), (W * SS, cy)], GREEN, max(int(16 * k), MW))
    G = 40
    # v1 の確認役：引いた地図で、細い道の色が「ちらばった点」にしか見えなかった → 細い道の色は 3 ます続けて、少し太く
    sw = SW if near else int(SW * 1.7)
    for gx in range(-G, G + 1):     # 細い道にも少し色
        for gy in range(-G, G + 1):
            if rnd.random() < (0.18 if near else 0.07):
                x = cx + gx * 120 * k; y = cy + gy * 120 * k; col = rnd.choice([GREEN, GREEN, YELLOW, RED])
                n_ = 1 if near else 3
                if rnd.random() < 0.5: color_line(d, [(x, y), (x + 120 * k * n_, y)], col, max(sw, int(7 * k)))
                else: color_line(d, [(x, y), (x, y + 120 * k * n_)], col, max(sw, int(7 * k)))


FAR = (0.80, 0.22)   # 引いた地図で「遠くの町の細い道」を必ず描く所（横の割合・縦の割合）。3D の輪はここに付ける（scenes.py の ph_far）


def far_town(d, k):
    """遠くの町の細い道（緑・黄の L 字と、短い赤）。04-06 の輪で囲む所"""
    x0, y0 = FAR[0] * W * SS, FAR[1] * H * SS; L = 120 * k * 2; w = int(SW * 1.7)
    color_line(d, [(x0 - L, y0), (x0, y0)], GREEN, w); color_line(d, [(x0, y0), (x0, y0 + L)], YELLOW, w)
    color_line(d, [(x0, y0), (x0 + L * 0.7, y0)], GREEN, w); color_line(d, [(x0 - L * 0.5, y0 + L * 0.6), (x0 - L * 0.5, y0 + L * 1.2)], RED, w)


def main():
    # 1）道案内（寄り）：自分の印が大通りを進む。曲がった先の道が赤い
    im, d, c, k = base(1.0); town_colors(d, c, k); me(d, c[0] - 300 * k, c[1], 1.0, 0); save(im, "ph_map_a")
    # 2）同じ＋字のない渋滞の印
    im, d, c, k = base(1.0); town_colors(d, c, k); me(d, c[0] - 300 * k, c[1], 1.0, 0); jam_icon(d, c[0] + 70 * SS, c[1] - 170 * SS, 1.0); save(im, "ph_map_alert")
    # 3）曲がったあと（列の中）：自分の印は縦の道の上、上向き
    im, d, c, k = base(1.0); town_colors(d, c, k); me(d, c[0], c[1] - 90 * k, 1.0, 90); save(im, "ph_map_q")
    # 4）引いた地図（2 倍・4 倍）：遠くの町の細い道まで色
    for z, nm in ((2.2, "ph_map_z1"), (4.5, "ph_map_z2")):
        im, d, c, k = base(z); town_colors(d, c, k, near=False); far_town(d, k); me(d, c[0], c[1] - 90 * k, 0.8, 90); save(im, nm)
    # 5）着く時刻の場所を明るく（字は 2D で重ねる。ここは白い札の地だけ）
    im, d, c, k = base(1.0); town_colors(d, c, k); me(d, c[0], c[1] - 90 * k, 1.0, 90)
    d.rounded_rectangle([W * SS * 0.66, H * SS * 0.06, W * SS * 0.96, H * SS * 0.30], radius=24 * SS, fill=(255, 255, 255), outline=TEAL, width=6 * SS)
    save(im, "ph_map_eta")
    # 6）車のナビ（2章）：大通りが赤い／町はずれの道だけ灰色
    im, d, c, k = base(1.4, seed=8); town_colors(d, c, k); me(d, c[0] - 200 * k, c[1], 1.0, 0); save(im, "nav_red")
    # v1 の確認役：09-04 の「ぽん」で画面に何も出なかった → 赤い線のない地図から、言葉の時刻に替える
    im, d, c, k = base(1.4, seed=8); town_colors(d, c, k)
    color_line(d, [(c[0], c[1] - 20 * k), (c[0], 0)], GREEN, max(int(15 * k), MW)); me(d, c[0] - 200 * k, c[1], 1.0, 0); save(im, "nav_green")
    im = Image.new("RGB", (W * SS, H * SS), (178, 204, 160)); d = ImageDraw.Draw(im)
    d.line([0, H * SS * 0.55, W * SS, H * SS * 0.45], fill=(255, 255, 255), width=44 * SS)
    d.line([0, H * SS * 0.55, W * SS, H * SS * 0.45], fill=(120, 130, 146), width=30 * SS)
    me(d, W * SS * 0.45, H * SS * 0.50, 1.0, 5); save(im, "nav_grey")
    print("ok", sorted(os.listdir(OUT)))


main()
