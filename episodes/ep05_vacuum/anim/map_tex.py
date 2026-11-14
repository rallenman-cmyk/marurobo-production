# 5本目：スマホの地図の絵（字なし）。間取り plan.py の点から描くので、3D の点の地図と同じ形になる
# python3 map_tex.py <出力フォルダ>
#   phone_map.png        ：スマホの画面（縦長）。部屋の地図＋掃除機のいる場所の点
#   phone_map_maru.png   ：オチ。部屋の真ん中に、まるい「動かない物」
#   phone_off.png        ：画面が消えている
#   map_plane.png        ：上から見た地図だけ（透明の地。3D の板に貼ると、点の地図とぴったり重なる。1 ピクセル＝1 cm）
# ほかの道具から：import map_tex; map_tex.draw_map(im, box, ...)
import os, sys, math
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan

TEAL = (47, 217, 200)
BG = (14, 27, 45)
DOCK = (0.3, 2.12)


def world_box():
    x0, y0, x1, y1 = plan.ROOM
    return (x0 - 0.15, y0 - 0.15, x1 + 0.15, y1 + 0.15)


def draw_map(im, box, dot=True, maru=False, furn=True, scale_pt=1.0, glow=True, fill=True, hl=None):
    """im の box（ピクセルの x0, y0, x1, y1）に部屋の地図を描く（上が奥＝y の大きい方）。hl＝光らせる家具の名前"""
    wx0, wy0, wx1, wy1 = world_box()
    bx0, by0, bx1, by1 = box
    sc = min((bx1 - bx0) / (wx1 - wx0), (by1 - by0) / (wy1 - wy0))
    ox = bx0 + ((bx1 - bx0) - sc * (wx1 - wx0)) / 2; oy = by0 + ((by1 - by0) - sc * (wy1 - wy0)) / 2
    P = lambda x, y: (ox + (x - wx0) * sc, oy + (wy1 - y) * sc)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if fill:   # 掃除した床（うすい色。部屋の中だけ）
        x0, y0, x1, y1 = plan.ROOM
        d.rounded_rectangle([P(x0, y1), P(x1, y0)], radius=int(0.08 * sc), fill=(40, 70, 95, 255))
    if furn:   # 家具の形（うすい面。アプリが家具を見分けて描いた、という形）
        for k in ("sofa", "desk", "bed", "shelf"):
            a, b, c, e_ = plan.FURN[k][:4]
            col = (255, 214, 90, 255) if (hl == k) else (70, 105, 130, 255)
            d.rounded_rectangle([P(a, e_), P(c, b)], radius=int(0.06 * sc), fill=col)
        a, b, c, e_ = plan.FURN["dock"][:4]
        d.rounded_rectangle([P(a, e_), P(c, b)], radius=int(0.03 * sc), fill=(120, 200, 160, 255))
    if maru:   # オチ：まるロボのいた所（まるい「動かない物」）
        cx, cy = P(0.0, 0.2); r = 0.17 * sc
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 105, 130, 255), outline=TEAL + (255,), width=max(2, int(0.025 * sc)))
    pr = max(1.5, 0.022 * sc * scale_pt)
    pts = plan.map_points()
    if maru:
        for k in range(48):
            a = 2 * math.pi * k / 48; pts.append((0.0 + 0.17 * math.cos(a), 0.2 + 0.17 * math.sin(a)))
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for x, y in pts:
            cx, cy = P(x, y); gd.ellipse([cx - pr * 2.6, cy - pr * 2.6, cx + pr * 2.6, cy + pr * 2.6], fill=TEAL + (90,))
        g = g.filter(ImageFilter.GaussianBlur(pr * 1.6)); lay = Image.alpha_composite(lay, g); d = ImageDraw.Draw(lay)
    for x, y in pts:
        cx, cy = P(x, y); d.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=TEAL + (255,))
    if dot:    # 掃除機のいる場所
        cx, cy = P(*DOCK); r = 0.11 * sc
        d.ellipse([cx - r * 1.9, cy - r * 1.9, cx + r * 1.9, cy + r * 1.9], fill=(255, 255, 255, 60))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255), outline=(255, 210, 74, 255), width=max(2, int(0.03 * sc)))
    im.alpha_composite(lay)
    return P


def phone_screen(W=720, H=1480, **kw):
    im = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(im)
    # 上の帯（字なし。小さな印だけ）
    d.rounded_rectangle([40, 60, W - 40, 150], radius=40, fill=(28, 46, 70, 255))
    d.ellipse([70, 80, 120, 130], fill=(120, 200, 160, 255))
    for k in range(3): d.rounded_rectangle([150 + k * 70, 98, 200 + k * 70, 112], radius=7, fill=(90, 120, 150, 255))
    # 地図（横長の部屋を、縦長の画面に回さずに入れる）
    draw_map(im, (30, 330, W - 30, 1060), **kw)
    # 下の大きな丸いボタン（字なし）
    d = ImageDraw.Draw(im)
    d.ellipse([W / 2 - 90, 1200, W / 2 + 90, 1380], fill=(47, 217, 200, 255))
    d.polygon([(W / 2 - 25, 1250), (W / 2 - 25, 1330), (W / 2 + 40, 1290)], fill=(255, 255, 255, 255))
    for k in range(2): d.ellipse([W / 2 - 240 + k * 420, 1265, W / 2 - 180 + k * 420, 1325], fill=(60, 90, 120, 255))
    return im


LAND_BOX = (150, 40, 1330, 680)


def phone_screen_land(W=1480, H=720, **kw):
    """横向きのスマホの画面（2D で大きく見せるとき。地図が大きく入る）"""
    im = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 40, 120, H - 40], radius=40, fill=(28, 46, 70, 255))
    d.ellipse([50, 70, 100, 120], fill=(120, 200, 160, 255))
    for k in range(3): d.rounded_rectangle([60, 160 + k * 60, 90, 200 + k * 60], radius=8, fill=(90, 120, 150, 255))
    draw_map(im, LAND_BOX, **kw)
    d = ImageDraw.Draw(im)
    d.ellipse([W - 130, H / 2 - 55, W - 20, H / 2 + 55], fill=(47, 217, 200, 255))
    d.polygon([(W - 95, H / 2 - 28), (W - 95, H / 2 + 28), (W - 50, H / 2)], fill=(255, 255, 255, 255))
    return im


def map_plane(cm=1.0):
    wx0, wy0, wx1, wy1 = world_box()
    W, H = int((wx1 - wx0) * 100 / cm), int((wy1 - wy0) * 100 / cm)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_map(im, (0, 0, W, H), dot=False, furn=False, fill=False, scale_pt=0.9)
    return im


if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    phone_screen().save(os.path.join(out, "phone_map.png"))
    phone_screen(maru=True, dot=True).save(os.path.join(out, "phone_map_maru.png"))
    Image.new("RGBA", (720, 1480), (11, 14, 18, 255)).save(os.path.join(out, "phone_off.png"))
    map_plane().save(os.path.join(out, "map_plane.png"))
    print("ok", out)
