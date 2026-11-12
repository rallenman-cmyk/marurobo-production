# 簡単な形の人4案の比較シート
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
LABELS = {"stick": "① 棒人間", "picto": "② ピクト", "bean": "③ マメ", "doll": "④ デッサン人形"}
NOTES = {"stick": "球の頭と細い棒の手足、点の目だけ。いちばん記号的で、まるロボがいちばん目立つ",
         "picto": "案内表示の人の形。顔なし・1人1色、頭と体のすき間が目印。誰が何をしているか一目で分かる",
         "bean": "頭と体がひと続きの豆の形に大きな点の目。かわいく、表情は目と体の傾きで出す",
         "doll": "木のデッサン人形。顔なしで関節の球が見える。「体の仕組み・動きの物理」を見せるのに向く"}
order = ["stick", "picto", "bean", "doll"]
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
f_t = ImageFont.truetype(FONT, 34); f_h = ImageFont.truetype(FONT, 28); f_s = ImageFont.truetype(FONT, 19)
CW = 470; pad = 18; top = 86; head_h = 118
cols = [k for k in order if os.path.exists(os.path.join(src, f"{k}_upper.png"))]
sheet = Image.new("RGB", (pad + len(cols) * (CW + pad), top + head_h + CW * 2 + pad * 3), (17, 21, 27)); d = ImageDraw.Draw(sheet)
d.text((pad, 22), "もっと簡単な形の人：4案（骨格と動きは共通）", font=f_t, fill=(240, 240, 236))
def wrap(text, font, width):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > width: lines.append(cur); cur = ch
        else: cur += ch
    return lines + ([cur] if cur else [])
for i, k in enumerate(cols):
    x = pad + i * (CW + pad)
    d.text((x, top), LABELS[k], font=f_h, fill=(247, 205, 120))
    for j, line in enumerate(wrap(NOTES[k], f_s, CW)[:3]): d.text((x, top + 38 + j * 25), line, font=f_s, fill=(214, 218, 222))
    for r, v in enumerate(("upper", "full")):
        im = Image.open(os.path.join(src, f"{k}_{v}.png")).convert("RGB").resize((CW, CW), Image.LANCZOS)
        sheet.paste(im, (x, top + head_h + r * (CW + pad)))
sheet.save(out, quality=88); print("sheet", out, sheet.size)
