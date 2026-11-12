# 字幕の点検：組んだ動画から、字幕 1 枚ごとのまん中のコマを取り出し、画面の下半分を並べた一覧にする（札や図と重ならないか・読めるか）
#   使い方: python3 subs_check.py 動画.mp4 字幕.ass 出力の名前   → 出力の名前_1.jpg, _2.jpg …（1 枚に 24 こま）
import os, sys, re, subprocess
from PIL import Image, ImageDraw, ImageFont
mp4, ass, out = sys.argv[1], sys.argv[2], sys.argv[3]
FONT = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/av/fonts/japanese.ttc"


def sec(x):
    h, m, s = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)


ev = []
for ln in open(ass, encoding="utf-8"):
    if not ln.startswith("Dialogue:"): continue
    f = ln.rstrip("\n").split(",", 9)
    if f[3] not in ("Main", "Sub"): continue
    ev.append((sec(f[1]), sec(f[2]), re.sub(r"\{[^}]*\}", "", f[9]).replace("\\N", "／")))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout)
TW, TH, COLS, ROWS = 640, 200, 3, 8
font = ImageFont.truetype(FONT, 18)
tiles = []
for a, b, t in ev:
    if a >= dur: continue
    tm = min((a + b) / 2, dur - 0.05)
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % tm, "-i", mp4, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    if not r.stdout: continue
    im = Image.open(__import__("io").BytesIO(r.stdout)).convert("RGB"); W, H = im.size
    tile = im.crop((0, int(H * 0.52), W, H)).resize((TW, TH - 24), Image.LANCZOS)
    c = Image.new("RGB", (TW, TH), (20, 22, 26)); c.paste(tile, (0, 24))
    ImageDraw.Draw(c).text((6, 2), "%d:%05.2f  %s" % (int(tm // 60), tm % 60, t[:34]), font=font, fill=(255, 220, 120))
    tiles.append(c)
per = COLS * ROWS
for s in range(0, len(tiles), per):
    sh = Image.new("RGB", (COLS * TW + (COLS + 1) * 6, ROWS * TH + (ROWS + 1) * 6), (60, 60, 60))
    for i, c in enumerate(tiles[s:s + per]):
        sh.paste(c, (6 + (i % COLS) * (TW + 6), 6 + (i // COLS) * (TH + 6)))
    p = "%s_%d.jpg" % (out, s // per + 1); sh.save(p, quality=85); print(p, len(tiles[s:s + per]))
