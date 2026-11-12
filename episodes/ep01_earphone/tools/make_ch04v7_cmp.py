# 第4章 v7 の確認ページ用：直した4点の「前（v6）｜後（v7）」の比べ画像を、一枚ずつ作る（スマホの幅で読めるように横並び2枚）
#   前：v6 の動画のコマ（stage/ch03/v7_compare/before_*.png）、後：v7 のコマ（ch04_out/full7/f_XXXX.png）
import os
from PIL import Image, ImageDraw, ImageFont
SC = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"
CMP = SC + "/stage/ch03/v7_compare"; FULL = SC + "/stage/ch03/ch04_out/full7"; OUT = SC + "/review_page/img"
F = ImageFont.truetype(SC + "/stage/av/fonts/japanese.ttc", 26)
CH0 = 175.786
ROWS = [("ch04v7_cmp1", "before_d5.png", 227.5), ("ch04v7_cmp2", "before_p15.png", 392.6),
        ("ch04v7_cmp3", "before_d8.png", 421.0), ("ch04v7_cmp4", "before_case.png", 288.0)]
W1, H1, pad, lab = 640, 360, 12, 36
for name, before, t in ROWS:
    after = os.path.join(FULL, "f_%04d.png" % (int(round((t - CH0) * 24)) + 1))
    sheet = Image.new("RGB", (pad * 3 + W1 * 2, pad + lab + H1 + pad), (238, 242, 245)); d = ImageDraw.Draw(sheet)
    for j, (txt, path, col) in enumerate((("前（v6）", os.path.join(CMP, before), (91, 104, 116)), ("後（v7）", after, (181, 101, 29)))):
        x = pad + j * (W1 + pad)
        d.text((x, pad), txt, font=F, fill=col)
        sheet.paste(Image.open(path).convert("RGB").resize((W1, H1), Image.LANCZOS), (x, pad + lab))
    sheet.save(os.path.join(OUT, name + ".jpg"), quality=86)
    print(name, after)
