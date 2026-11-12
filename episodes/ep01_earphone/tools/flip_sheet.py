# 簡易描画（3コマおき）の連番から、時刻の範囲の一覧表を作る：python3 flip_sheet.py DIR t0 t1 step out.png [cols]
import sys, os, json
from PIL import Image, ImageDraw
D, t0, t1, step, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 6
L = json.load(open(os.path.join(D, "pairing_log.json"))); T0 = L["t0"]
f0 = int(round((t0 - T0) * 24)) + 1; f1 = int(round((t1 - T0) * 24)) + 1
fs = [f for f in range(f0, f1 + 1) if (f - 1) % 3 == 0][::step]
fs = [f for f in fs if os.path.exists(os.path.join(D, "frames", "p_%04d.png" % f))]
W, H = 320, 180; rows = (len(fs) + cols - 1) // cols
sh = Image.new("RGB", (W * cols, H * rows), "white"); d = ImageDraw.Draw(sh)
for i, f in enumerate(fs):
    im = Image.open(os.path.join(D, "frames", "p_%04d.png" % f)).convert("RGB").resize((W, H))
    x, y = (i % cols) * W, (i // cols) * H; sh.paste(im, (x, y))
    d.rectangle((x, y, x + 92, y + 14), fill="black"); d.text((x + 3, y + 1), "%.2f f%d" % (T0 + (f - 1) / 24, f), fill="yellow")
sh.save(out); print(out, len(fs))
