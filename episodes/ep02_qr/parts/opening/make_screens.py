# スマホの画面（カメラの絵＋読み取りの枠＋結果）
from PIL import Image, ImageDraw, ImageFont
import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sb2', 'screens')
f = lambda s: ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', s)
for src in ('plain', 'stand', 'stand2', 'step'):
    for st in ('scan', 'hello'):
        im = Image.open(f'{D}/pc_{src}.png').convert('RGB'); d = ImageDraw.Draw(im); w, h = im.size
        cx, cy, k = w // 2, int(h * 0.58), 200; col = (255, 214, 64) if st == 'scan' else (120, 220, 140)
        for sx in (-1, 1):
            for sy in (-1, 1):
                X, Y = cx + sx * k, cy + sy * k; d.line([(X, Y), (X - sx * 60, Y)], fill=col, width=12); d.line([(X, Y), (X, Y - sy * 60)], fill=col, width=12)
        if st == 'hello':
            d.rounded_rectangle([30, 50, w - 30, 190], 30, fill=(248, 248, 246)); d.text((60, 70), 'テキスト', font=f(34), fill=(110, 116, 124)); d.text((60, 110), 'HELLO', font=f(56), fill=(30, 34, 40))
        im.save(f'{D}/scr_{src}_{st}.png')
print('screens ok')
