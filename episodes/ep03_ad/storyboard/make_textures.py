# 絵コンテ用の絵（字なし）：つり広告のテントの絵と、スマホの広告の画面。scenes.py と同じフォルダに書き出す
# python3 make_textures.py <出力フォルダ>
import sys, os
from PIL import Image, ImageDraw

out = sys.argv[1] if len(sys.argv) > 1 else "."
W, H = 600, 800
im = Image.new('RGB', (W, H), '#FFF6E6'); d = ImageDraw.Draw(im)
d.rectangle([0, 0, W, H * 0.62], fill='#BFE3F2')
d.ellipse([400, 90, 520, 210], fill='#FFC94A')
d.rectangle([0, H * 0.62, W, H], fill='#9ED07A')
d.polygon([(90, 560), (300, 250), (510, 560)], fill='#E9692C')
d.polygon([(250, 560), (300, 420), (350, 560)], fill='#7A2E12')
d.line([(300, 250), (300, 215)], fill='#5a3a20', width=10)
im.save(os.path.join(out, 'tent.png'))

im2 = Image.new('RGB', (540, 1080), '#F4F6F8'); d = ImageDraw.Draw(im2)
d.rectangle([0, 0, 540, 120], fill='#DDE3EA')
for y in (180, 240):
    d.rounded_rectangle([40, y, 500, y + 30], 10, fill='#CBD3DC')
d.rounded_rectangle([30, 330, 510, 830], 24, fill='#BFE3F2')
d.rectangle([30, 640, 510, 830], fill='#9ED07A')
d.ellipse([380, 370, 470, 460], fill='#FFC94A')
d.polygon([(110, 760), (270, 470), (430, 760)], fill='#E9692C')
d.polygon([(235, 760), (270, 650), (305, 760)], fill='#7A2E12')
d.rounded_rectangle([150, 880, 390, 950], 30, fill='#2BB3A6')
im2.save(os.path.join(out, 'phone_ad.png'))
