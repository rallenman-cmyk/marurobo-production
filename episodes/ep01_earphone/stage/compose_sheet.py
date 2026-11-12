import sys, os
from PIL import Image, ImageDraw, ImageFont

d = sys.argv[1]
F = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
f_title, f_head, f_body = ImageFont.truetype(F, 34), ImageFont.truetype(F, 28), ImageFont.truetype(F, 21)
items = [
    ("A", "くっきり昼光：分かりやすさ優先", "光：左前45°・高さ50°・5600K・影やや柔らか／明暗比2:1"),
    ("B", "夕方の逆光：迫力とスケール感", "光：後方・高さ13°・3000K・影くっきり（太陽と同じ0.5°）／明暗比約6:1・薄いかすみ"),
    ("C", "夜、受付口だけが光る：注目を集める", "光：受付口の青緑の光＋まるロボへの上からのスポット3500K＋月明かり8000K"),
]
W, Hh = 960, 540
pad, cap = 24, 86
sheet = Image.new("RGB", (W + 2 * pad, 70 + len(items) * (Hh + cap + pad)), (18, 22, 30))
dr = ImageDraw.Draw(sheet)
dr.text((pad, 18), "舞台「巨大イヤホンの受付口」光の3案（スケッチの配置を3Dにしたもの）", font=f_title, fill=(240, 244, 248))
y = 70
for key, head, body in items:
    im = Image.open(os.path.join(d, f"stage_{key}.png")).convert("RGB")
    sheet.paste(im, (pad, y))
    dr.text((pad, y + Hh + 10), f"{key}：{head}", font=f_head, fill=(255, 214, 120))
    dr.text((pad, y + Hh + 48), body, font=f_body, fill=(205, 214, 224))
    y += Hh + cap + pad
out = os.path.join(d, "stage_variants_sheet.jpg")
sheet.save(out, quality=88)
print(out, sheet.size)
