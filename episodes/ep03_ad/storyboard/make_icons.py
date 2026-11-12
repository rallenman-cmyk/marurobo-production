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
