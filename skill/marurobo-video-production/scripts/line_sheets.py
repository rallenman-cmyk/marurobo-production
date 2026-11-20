# 文ごとに 3 枚（頭・まん中・終わり）を並べた絵を作る（点検表「全部の文を 3 枚ずつ並べて、表と見比べた」用。2026-11-20）
#   python3 line_sheets.py <通し.mp4> <placement.json> <出力フォルダ> [1 枚に並べる文の数=10]
#   出力：sheet_00.png …（1 行が 1 文。左に文の番号と時刻）
import os, sys, json, subprocess
from PIL import Image, ImageDraw, ImageFont

mp4, pj, out = sys.argv[1], sys.argv[2], sys.argv[3]
per = int(sys.argv[4]) if len(sys.argv) > 4 else 10
os.makedirs(out, exist_ok=True)
P = json.load(open(pj, encoding="utf-8"))
W, H = 320, 180
font = None
for f in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"):
    if os.path.exists(f): font = ImageFont.truetype(f, 15); break
font = font or ImageFont.load_default()


def grab(t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", mp4, "-frames:v", "1", "-vf", "scale=%d:%d" % (W, H),
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return Image.frombytes("RGB", (W, H), r.stdout) if len(r.stdout) == W * H * 3 else Image.new("RGB", (W, H))


for si in range(0, len(P), per):
    rows = P[si:si + per]
    sheet = Image.new("RGB", (150 + 3 * W, len(rows) * H), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for ri, p in enumerate(rows):
        a, c = p["start"], p["end"]
        for ci, t in enumerate((a + 0.3, (a + c) / 2, max(a + 0.3, c - 0.2))):
            sheet.paste(grab(t), (150 + ci * W, ri * H))
        d.text((6, ri * H + 6), "%d  %d:%05.2f" % (p["no"], int(a // 60), a % 60), fill=(255, 230, 80), font=font)
        txt = p.get("text", ""); y = ri * H + 30
        for k in range(0, len(txt), 9):
            d.text((6, y), txt[k:k + 9], fill=(230, 230, 230), font=font); y += 18
    sheet.save(os.path.join(out, "sheet_%02d.png" % (si // per)))
    print("sheet_%02d.png" % (si // per), flush=True)
