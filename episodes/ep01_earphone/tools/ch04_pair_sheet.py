# 第4章のペアリング区間のラベル確認用の一覧（組み上がった full/ のコマから）
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
OUT, PAIR, DST = sys.argv[1], sys.argv[2], sys.argv[3]
CH0, FPS = 161.1, 24
PL = json.load(open(os.path.join(PAIR, "pairing_log.json")))
T = PL["times"]
pts = [("ペアリング", 245.3), ("知っている色", 246.0), ("ひみつの色1", 247.0), ("見えても", 251.2),
       ("ひみつの色E", T["pour"]["secretE"] + 0.4), ("次からは", T["key"]["E"] + 1.3),
       ("ひみつの色P", T["pour"]["secretP"] + 0.4), ("同じ色の鍵", T["key"]["P"] + 1.3), ("まとめ", 262.5)]
F = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stage", "av", "fonts", "japanese.ttc"), 26)
tw, th = 640, 360; cols = 3; rows = (len(pts) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 34)), (30, 30, 30)); d = ImageDraw.Draw(sheet)
for j, (nm, t) in enumerate(pts):
    i = int(round((t - CH0) * FPS)); p = os.path.join(OUT, "full", "f_%04d.png" % (i + 1))
    if not os.path.exists(p): continue
    im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
    x, y = (j % cols) * tw, (j // cols) * (th + 34)
    sheet.paste(im, (x, y + 34)); d.text((x + 8, y + 3), "%s  t=%.2f  f_%04d" % (nm, t, i + 1), font=F, fill=(255, 255, 255))
sheet.save(DST, quality=88); print(DST)
