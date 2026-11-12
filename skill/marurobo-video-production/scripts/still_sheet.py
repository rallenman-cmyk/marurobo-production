# 試し描きの静止画を一覧にする: python3 still_sheet.py DIR OUT.jpg 秒,秒,...
import os, sys
from PIL import Image, ImageDraw
d, out, ts = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(",")]
W, H = 640, 360; cols = 3; rows = (len(ts) + cols - 1) // cols
sh = Image.new("RGB", (W * cols, H * rows), (20, 20, 20))
for j, t in enumerate(ts):
    p = os.path.join(d, "still_%06.2f.png" % t)
    if not os.path.exists(p): continue
    im = Image.open(p).convert("RGB").resize((W, H)); dr = ImageDraw.Draw(im); dr.text((6, 6), "t=%.2f" % t, fill=(255, 0, 0))
    sh.paste(im, ((j % cols) * W, (j // cols) * H))
sh.save(out, quality=90); print(out)
