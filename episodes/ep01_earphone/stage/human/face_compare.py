# 顔の比較：参考｜描画｜重ね（半分ずつ）を人ごとに並べる
# 使い方: python3 face_compare.py render.png out.png
import sys, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
BOX = {"M1": (1080, 20, 1672, 640), "W1": (390, 320, 820, 700), "G1": (90, 420, 400, 700)}
ref = Image.open(os.path.join(HERE, "..", "..", "refimg", "ref_2827_2.jpeg")).convert("RGB")
mine = Image.open(sys.argv[1]).convert("RGB").resize(ref.size, Image.LANCZOS)
F = ImageFont.truetype("/usr/share/fonts/truetype/fonts-japanese-gothic.ttf", 22)
rows = []
for k, b in BOX.items():
    a = ref.crop(b); m = mine.crop(b); h = 360; w = int(a.width * h / a.height)
    a = a.resize((w, h)); m = m.resize((w, h)); bl = Image.blend(a, m, 0.5)
    row = Image.new("RGB", (3 * w + 20, h), "white"); row.paste(a, (0, 0)); row.paste(m, (w + 10, 0)); row.paste(bl, (2 * w + 20, 0)); rows.append(row)
W = max(r.width for r in rows); H = sum(r.height for r in rows) + 10 * len(rows) + 34
out = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(out); d.text((10, 4), "参考 ｜ 今回 ｜ 重ね", font=F, fill="#222")
y = 34
for r in rows: out.paste(r, (0, y)); y += r.height + 10
out.save(sys.argv[2], quality=90)
