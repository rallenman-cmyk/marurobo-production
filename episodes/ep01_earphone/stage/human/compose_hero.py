# 主人公の服装3案＋乗客の例
import sys, os
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
META = {"beanie": ("① ニット帽", "からし色のニット帽。頭の形が変わるので遠くからでも主人公と分かる。耳とイヤホンは見える"),
        "cap": ("② キャップ", "からし色のキャップ。横顔でも、つばの形で分かる。上から撮ると目が少し隠れる"),
        "scarf": ("③ マフラー", "からし色のマフラー。頭は他の人と同じで、首まわりの色で見分ける。顔がいちばん見やすい"),
        "plain": ("（参考）乗客", "落ち着いた色の上着とズボン。帽子などの目印はなし。主人公の青緑とからし色が目立つ")}
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
f_t = ImageFont.truetype(FONT, 34); f_h = ImageFont.truetype(FONT, 28); f_s = ImageFont.truetype(FONT, 19)
CW = 470; pad = 18; top = 86; head_h = 118
cols = [k for k in ("beanie", "cap", "scarf", "plain") if os.path.exists(os.path.join(src, f"{k}_upper.png"))]
sheet = Image.new("RGB", (pad + len(cols) * (CW + pad), top + head_h + CW * 2 + pad * 3), (17, 21, 27)); d = ImageDraw.Draw(sheet)
d.text((pad, 22), "主人公の服装：青緑のフード付きパーカー＋目印1つ（3案）", font=f_t, fill=(240, 240, 236))
def wrap(text, font, width):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > width: lines.append(cur); cur = ch
        else: cur += ch
    return lines + ([cur] if cur else [])
for i, k in enumerate(cols):
    x = pad + i * (CW + pad); title, note = META[k]
    d.text((x, top), title, font=f_h, fill=(247, 205, 120) if k != "plain" else (170, 176, 184))
    for j, line in enumerate(wrap(note, f_s, CW)[:3]): d.text((x, top + 38 + j * 25), line, font=f_s, fill=(214, 218, 222))
    for r, v in enumerate(("upper", "full")):
        im = Image.open(os.path.join(src, f"{k}_{v}.png")).convert("RGB").resize((CW, CW), Image.LANCZOS)
        sheet.paste(im, (x, top + head_h + r * (CW + pad)))
sheet.save(out, quality=90); print("sheet", out, sheet.size)
