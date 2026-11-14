# 音の泡の中の絵（字なし）：時計・車・寝息（月と星）・テント。gate.py と同じフォルダに書き出す
import math, sys, os
from PIL import Image, ImageDraw
out = sys.argv[1] if len(sys.argv) > 1 else "."
def base():
    im = Image.new('RGBA', (512, 512), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
im, d = base(); d.ellipse([86, 86, 426, 426], fill='#FFFFFF', outline='#3D5A80', width=28)
for k in range(12):
    a = k * math.pi / 6; r1, r2 = 150, 125
    d.line([(256 + r1 * math.sin(a), 256 - r1 * math.cos(a)), (256 + r2 * math.sin(a), 256 - r2 * math.cos(a))], fill='#3D5A80', width=10)
d.line([(256, 256), (256, 150)], fill='#E5484D', width=18); d.line([(256, 256), (330, 290)], fill='#1B2733', width=18)
d.ellipse([240, 240, 272, 272], fill='#1B2733'); im.save(os.path.join(out, 'icon_clock.png'))
im, d = base(); d.rounded_rectangle([60, 230, 452, 350], 40, fill='#4C9BE8'); d.polygon([(140, 230), (190, 150), (330, 150), (390, 230)], fill='#4C9BE8')
d.polygon([(165, 228), (205, 170), (250, 170), (250, 228)], fill='#DDF4FF'); d.polygon([(268, 228), (268, 170), (320, 170), (362, 228)], fill='#DDF4FF')
for x in (150, 360):
    d.ellipse([x - 48, 300, x + 48, 396], fill='#1B2733'); d.ellipse([x - 20, 328, x + 20, 368], fill='#C9D1D5')
im.save(os.path.join(out, 'icon_car.png'))
m = Image.new('L', (512, 512), 0); md = ImageDraw.Draw(m); md.ellipse([110, 90, 410, 390], fill=255); md.ellipse([200, 50, 480, 330], fill=0)
im = Image.new('RGBA', (512, 512), (0, 0, 0, 0)); im.paste(Image.new('RGBA', (512, 512), '#FFD166'), (0, 0), m)
d = ImageDraw.Draw(im)
for (x, y, r) in ((380, 330, 22), (430, 250, 14), (330, 420, 12)):
    d.ellipse([x - r, y - r, x + r, y + r], fill='#FFFFFF')
im.save(os.path.join(out, 'icon_sleep.png'))
im, d = base(); d.polygon([(70, 420), (256, 110), (442, 420)], fill='#E9692C'); d.polygon([(210, 420), (256, 290), (302, 420)], fill='#7A2E12'); d.line([(256, 110), (256, 70)], fill='#5a3a20', width=12)
im.save(os.path.join(out, 'icon_tent.png'))
# 手がかりの箱の前の札（v4「箱のイラストもう少し分かるように」7:21）：白い札に、場所のピン／見たページ／二人
OR, DK = '#E07B22', '#5B3B22'
def card():
    im = Image.new('RGBA', (512, 512), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([16, 16, 496, 496], 70, fill='#FFFFFF', outline=DK, width=18); return im, d
im, d = card()                                  # 場所：地図のピン
d.ellipse([146, 70, 366, 290], fill=OR); d.polygon([(158, 225), (256, 440), (354, 225)], fill=OR); d.ellipse([214, 138, 298, 222], fill='#FFFFFF')
d.ellipse([186, 420, 326, 462], outline=DK, width=12)
im.save(os.path.join(out, 'box_pin.png'))
im, d = card()                                  # 見たページ：ブラウザの窓
d.rounded_rectangle([86, 96, 426, 416], 26, fill='#FFFFFF', outline=OR, width=20); d.rectangle([96, 106, 416, 166], fill=OR)
for k, x in enumerate((122, 152, 182)): d.ellipse([x - 10, 126, x + 10, 146], fill='#FFFFFF')
d.rounded_rectangle([122, 196, 250, 300], 10, fill='#F6C18E')
for y in (206, 246, 286): d.line([(274, y), (392, y)], fill=DK, width=14)
for y in (336, 372): d.line([(122, y), (392, y)], fill=DK, width=14)
im.save(os.path.join(out, 'box_page.png'))
im, d = card()                                  # 一緒にいた人：二人
for cx, col in ((186, OR), (326, '#3E7CB1')):
    d.ellipse([cx - 58, 110, cx + 58, 226], fill=col); d.pieslice([cx - 100, 250, cx + 100, 450], 180, 360, fill=col); d.rectangle([cx - 100, 349, cx + 100, 400], fill=col)
im.save(os.path.join(out, 'box_two.png'))
