# 静止画を並べて、名前（時刻）を付けた一覧にする：still_grid.py OUT.jpg COLS W H 画像...
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, cols, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]); fs = sys.argv[5:]
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stage", "av", "fonts", "japanese.ttc")
f = ImageFont.truetype(F, 16)
rows = (len(fs) + cols - 1) // cols; sh = Image.new("RGB", (W * cols, H * rows), "white"); d = ImageDraw.Draw(sh)
for j, p in enumerate(fs):
    im = Image.open(p).convert("RGB").resize((W, H)); x, y = (j % cols) * W, (j // cols) * H; sh.paste(im, (x, y))
    t = os.path.basename(p).replace("still_", "").replace(".png", ""); d.rectangle((x, y, x + 8 + d.textlength(t, font=f), y + 20), fill=(31, 94, 102)); d.text((x + 4, y + 1), t, font=f, fill="white")
sh.save(out, quality=88); print(out, sh.size)
