import sys
from PIL import Image
out_p = sys.argv[1]; paths = sys.argv[2:]
ims = [Image.open(p).convert("RGB") for p in paths]
W = sum(i.width for i in ims); H = max(i.height for i in ims)
out = Image.new("RGB", (W, H), "white"); x = 0
for i in ims: out.paste(i, (x, 0)); x += i.width
out.save(out_p, quality=90)
