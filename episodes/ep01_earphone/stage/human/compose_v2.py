# 前（Codex版の人物）と後（新しい人物）を並べた一覧
import sys, os
from PIL import Image, ImageDraw, ImageFont
old_dir, new_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
f_t = ImageFont.truetype(FONT, 34); f_h = ImageFont.truetype(FONT, 26); f_s = ImageFont.truetype(FONT, 21)
W = 760; H = int(W * 9 / 16); pad = 22; top = 92
rows = [("1", "車両の全景（A案）"), ("2", "音が途切れる瞬間（C案）"), ("3", "時間が止まる瞬間（C案）")]
sheet = Image.new("RGB", (pad * 3 + W * 2, top + len(rows) * (H + 64) + pad), (17, 21, 27))
d = ImageDraw.Draw(sheet)
d.text((pad, 24), "人物の作り直し：前（Codex版）と後（骨格入りの新しい人物）", font=f_t, fill=(240, 240, 236))
for i, (k, title) in enumerate(rows):
    y = top + i * (H + 64)
    d.text((pad, y), f"{k}. {title}", font=f_h, fill=(247, 205, 120))
    for j, (folder, name, label) in enumerate(((old_dir, f"opening_shot{k}.png", "前"), (new_dir, f"opening_v2_shot{k}.png", "後"))):
        p = os.path.join(folder, name)
        if not os.path.exists(p): continue
        im = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
        x = pad + j * (W + pad); sheet.paste(im, (x, y + 36))
        d.rounded_rectangle((x + 10, y + 46, x + 58, y + 80), 8, fill=(0, 0, 0))
        d.text((x + 21, y + 49), label, font=f_s, fill=(255, 255, 255))
sheet.save(out, quality=88); print("sheet", out, sheet.size)
