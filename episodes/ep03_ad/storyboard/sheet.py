# 絵の一覧（4 列）を作る：python3 sheet.py <出力.png> <絵...>
import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
W, H, C = 480, 270, 4
rows = (len(files) + C - 1) // C
s = Image.new('RGB', (W * C, H * rows), 'white')
d = ImageDraw.Draw(s)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((W, H))
    s.paste(im, ((i % C) * W, (i // C) * H))
    d.rectangle([(i % C) * W, (i // C) * H, (i % C) * W + 60, (i // C) * H + 24], fill='black')
    d.text(((i % C) * W + 6, (i // C) * H + 6), f.split('/')[-1][:3], fill='white')
s.save(out)
