# 6面図（上段）と、作った3D（中段）、重ね（下段）を並べる
import sys, os
from PIL import Image
k, d, out = sys.argv[1:4]
SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sheets")
names = ["front", "left45", "left", "back", "right"]
cols = []
for nm in names:
    ref = Image.open(os.path.join(SH, f"{k}_{nm}.png")).convert("RGB"); ref = ref.crop((0, 60, ref.width, 560))
    ref = ref.crop((0, 0, ref.width, 500)); mine = Image.open(os.path.join(d, f"{k}_{nm}.png")).convert("RGB").resize(ref.size)
    col = Image.new("RGB", (ref.width, 1500), "white"); col.paste(ref, (0, 0)); col.paste(mine, (0, 500)); col.paste(Image.blend(ref, mine, 0.5), (0, 1000)); cols.append(col)
W = sum(c.width for c in cols); img = Image.new("RGB", (W, 1500), "white"); x = 0
for c in cols: img.paste(c, (x, 0)); x += c.width
img.resize((W * 2 // 3, 1000)).save(out, quality=88)
