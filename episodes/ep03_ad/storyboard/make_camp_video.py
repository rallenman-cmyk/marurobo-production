# 22-03「夜、まるロボがスマホでキャンプの動画をずっと見ていた」のスマホ画面（動画の画面＋次のおすすめ動画。字は入れない）
#   python3 make_camp_video.py → phone_camp_video.png（縦 660・横 320 の割合）
from PIL import Image, ImageDraw
import os
W, H = 640, 1320
im = Image.new("RGB", (W, H), (18, 18, 22)); d = ImageDraw.Draw(im)

def scene(x0, y0, w, h, fire=True):
    for i in range(h):                                   # 夕方の空
        t = i / h; c = (int(250 - 90 * t), int(170 - 60 * t), int(120 + 40 * t)); d.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=c)
    d.rectangle([x0, y0 + int(h * 0.68), x0 + w, y0 + h], fill=(86, 150, 92))   # 草
    d.polygon([(x0 + w * 0.05, y0 + h * 0.70), (x0 + w * 0.25, y0 + h * 0.42), (x0 + w * 0.45, y0 + h * 0.70)], fill=(70, 120, 90))   # 山
    tx, ty, tw, th = x0 + w * 0.38, y0 + h * 0.30, w * 0.40, h * 0.44
    d.polygon([(tx, ty + th), (tx + tw / 2, ty), (tx + tw, ty + th)], fill=(240, 120, 90))   # テント
    d.polygon([(tx + tw * 0.38, ty + th), (tx + tw / 2, ty + th * 0.45), (tx + tw * 0.62, ty + th)], fill=(150, 60, 50))
    if fire:
        fx, fy = x0 + w * 0.20, y0 + h * 0.80
        d.polygon([(fx - 18, fy), (fx, fy - 44), (fx + 18, fy)], fill=(255, 170, 40)); d.polygon([(fx - 8, fy), (fx, fy - 22), (fx + 8, fy)], fill=(255, 235, 120))
    d.ellipse([x0 + w * 0.78, y0 + h * 0.08, x0 + w * 0.90, y0 + h * 0.08 + w * 0.12], fill=(255, 230, 160))   # 夕日

scene(0, 90, W, 380)                                                   # いま見ている動画
d.rectangle([0, 470, W, 478], fill=(70, 70, 76)); d.rectangle([0, 470, int(W * 0.72), 478], fill=(235, 60, 60)); d.ellipse([int(W * 0.72) - 12, 462, int(W * 0.72) + 12, 486], fill=(235, 60, 60))   # 進み具合（だいぶ見た）
for k in range(3):                                                     # 次のおすすめ（キャンプの動画ばかり）
    y = 540 + k * 250
    scene(30, y, 300, 190, fire=(k != 1))
    d.rounded_rectangle([350, y + 20, 610, y + 46], 10, fill=(90, 90, 98)); d.rounded_rectangle([350, y + 66, 540, y + 88], 10, fill=(64, 64, 70))
im.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone_camp_video.png"))
print("ok")
