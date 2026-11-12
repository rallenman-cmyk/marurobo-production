# 作風の比較シート：列＝作風、上＝顔のアップ、下＝全身（座ってスマホ）
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
order = sys.argv[3].split(",") if len(sys.argv) > 3 else ["soft", "film", "toy", "real"]
META = {
    "soft": ("A ふんわり", "丸くやわらかい形。大きな頭と目、ボタンのような鼻、つやを抑えた質感。絵本のような親しみやすさ"),
    "film": ("B くっきり", "映画のCGアニメ風。広い肩・はっきりした眉とあご・大きな毛束で、形にメリハリ。表情が伝わりやすい"),
    "toy": ("C おもちゃ", "ソフビ人形のようなつや。大きな黒目、ひとかたまりの髪、ふっくらした手。小さなロボと同じ世界になじむ"),
    "real": ("今の版（参考）", "現実に近い比率。目が小さく、頬やあごの形が現実的なため、少し不気味に見えやすい"),
}
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
f_t = ImageFont.truetype(FONT, 34); f_h = ImageFont.truetype(FONT, 28); f_s = ImageFont.truetype(FONT, 19)
CW = 470; pad = 18; top = 86; head_h = 118
cols = [k for k in order if os.path.exists(os.path.join(src, f"{k}_face.png"))]
H = top + head_h + CW * 2 + pad * 3
sheet = Image.new("RGB", (pad + len(cols) * (CW + pad), H), (17, 21, 27)); d = ImageDraw.Draw(sheet)
d.text((pad, 22), "人の見た目：3つの作風（どれもオリジナル）と今の版", font=f_t, fill=(240, 240, 236))


def wrap(text, font, width):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > width: lines.append(cur); cur = ch
        else: cur += ch
    if cur: lines.append(cur)
    return lines


for i, k in enumerate(cols):
    x = pad + i * (CW + pad); y = top
    title, note = META[k]
    d.text((x, y), title, font=f_h, fill=(247, 205, 120) if k != "real" else (170, 176, 184))
    for j, line in enumerate(wrap(note, f_s, CW)[:3]): d.text((x, y + 38 + j * 25), line, font=f_s, fill=(214, 218, 222))
    for r, v in enumerate(("face", "full")):
        im = Image.open(os.path.join(src, f"{k}_{v}.png")).convert("RGB").resize((CW, CW), Image.LANCZOS)
        sheet.paste(im, (x, top + head_h + r * (CW + pad)))
sheet.save(out, quality=88); print("sheet", out, sheet.size)
