# 線画アイコン風の人 4案の比較シート
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
META = {"A": ("A 白×黒線（顔なし）", "参考画像にいちばん近い。白い体と太い輪郭線だけ。気持ちは姿勢と動きで伝える"),
        "B": ("B 白×黒線＋点の目", "点の目を2つだけ足す。まばたき・目線・目の大きさで「あれ？」などの反応が伝わる"),
        "C": ("C 服の色分け", "上着とズボンの色だけ塗る（頭と手足は白）。主人公や乗客を色で見分けられる。顔なし"),
        "D": ("D ずんぐり＋点の目", "頭を大きく、手足を太く。かわいらしさが増し、小さなまるロボと並べても釣り合う")}
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
f_t = ImageFont.truetype(FONT, 34); f_h = ImageFont.truetype(FONT, 28); f_s = ImageFont.truetype(FONT, 19)
CW = 470; pad = 18; top = 86; head_h = 118
cols = [k for k in "ABCD" if os.path.exists(os.path.join(src, f"{k}_upper.png"))]
sheet = Image.new("RGB", (pad + len(cols) * (CW + pad), top + head_h + CW * 2 + pad * 3), (17, 21, 27)); d = ImageDraw.Draw(sheet)
d.text((pad, 22), "線画アイコン風の人：4案（どれもオリジナル。骨格と動きは共通）", font=f_t, fill=(240, 240, 236))
def wrap(text, font, width):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > width: lines.append(cur); cur = ch
        else: cur += ch
    return lines + ([cur] if cur else [])
for i, k in enumerate(cols):
    x = pad + i * (CW + pad); title, note = META[k]
    d.text((x, top), title, font=f_h, fill=(247, 205, 120))
    for j, line in enumerate(wrap(note, f_s, CW)[:3]): d.text((x, top + 38 + j * 25), line, font=f_s, fill=(214, 218, 222))
    for r, v in enumerate(("upper", "full")):
        im = Image.open(os.path.join(src, f"{k}_{v}.png")).convert("RGB").resize((CW, CW), Image.LANCZOS)
        sheet.paste(im, (x, top + head_h + r * (CW + pad)))
sheet.save(out, quality=90); print("sheet", out, sheet.size)
