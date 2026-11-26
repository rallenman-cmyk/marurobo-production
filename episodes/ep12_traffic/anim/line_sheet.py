# 文ごとの絵の一覧（7本目 v6：絵コンテ表と、文ごとに見比べるため）
# python3 line_sheet.py 動画.mp4 出力フォルダ [終わりの秒]   → 文ごとに 3 枚（頭・まん中・終わりの少し前）を並べた絵を、章ごとに作る
import os, sys, json, subprocess
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
V, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
S = {x["no"]: x for x in json.load(open(os.path.join(HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
W_, H_ = 320, 180
from PIL import ImageFont
FNT = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 16)
TO = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9   # 12本目：章ごとの下書きは、動画の終わりまでの文だけ
rows = []
for p in P:
    if p["end"] > TO: continue
    a, c = p["start"], p["end"]; ims = []
    for k, t in enumerate((a + 0.3, (a + c) / 2, c - 0.2)):
        f = os.path.join(OUT, "_f%03d_%d.png" % (p["no"], k))
        subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.2f" % t, "-i", V, "-frames:v", "1", "-vf", "scale=%d:-1" % W_, "-y", f])
        ims.append(Image.open(f).convert("RGB"))
    rows.append((S[p["no"]]["id"], ims))
for k in range(0, len(rows), 8):
    g = rows[k:k + 8]; im = Image.new("RGB", (W_ * 3 + 70, H_ * len(g)), (0, 0, 0)); d = ImageDraw.Draw(im)
    for i, (id_, ims) in enumerate(g):
        d.text((4, i * H_ + 4), id_, fill=(255, 255, 0), font=FNT)
        for j, x in enumerate(ims): im.paste(x, (70 + j * W_, i * H_))
    im.save(os.path.join(OUT, "lines_%02d.png" % (k // 8)))
for f in os.listdir(OUT):
    if f.startswith("_f"): os.remove(os.path.join(OUT, f))
print("ok", (len(rows) + 7) // 8, "枚")
