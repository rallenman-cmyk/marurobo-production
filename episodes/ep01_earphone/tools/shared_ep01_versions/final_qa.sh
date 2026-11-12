#!/bin/bash
# 通しの完成版の点検：①章のつなぎ目の前後（各 ±0.5 秒）のコマを並べる ②真っ黒なコマ ③声が途切れて長く無音の所 ④音の大きさ
#   使い方: bash final_qa.sh [動画]   （省くと stage/final/bluetooth_full_1080.mp4）→ work_full/qa_*.jpg と qa.txt
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; V=${1:-$S/stage/final/bluetooth_full_1080.mp4}; W=$S/work_full; mkdir -p $W/qa; rm -f $W/qa/*
F=$S/stage/final
LIST="$F/ch0102_final_1080.mp4 $F/ch03_final_1080.mp4 $F/ch04_final_1080.mp4 $S/stage/ch03/ch5_final/ch05_final_1080.mp4 $F/ch06_final_1080.mp4 $F/ch07_final_1080.mp4 $F/ch08_final_1080.mp4"
T=0; J=""
for f in $LIST; do n=$(ffprobe -v error -select_streams v -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$f"); T=$(python3 -c "print($T + $n / 24.0)"); J="$J $T"; done
k=0
for t in $J; do
  k=$((k + 1))
  for d in -0.50 -0.08 0.04 0.50; do
    tt=$(python3 -c "print(max(0, $t + $d))")
    ffmpeg -v error -y -ss $tt -i $V -frames:v 1 -vf scale=480:-1 $W/qa/j${k}_$(printf "%+.2f" $d).png
  done
done
python3 - $W <<'PY'
import sys, glob, os
from PIL import Image, ImageDraw
W = sys.argv[1]; fs = sorted(glob.glob(W + "/qa/j*.png"), key=lambda p: (int(os.path.basename(p)[1:].split("_")[0]), float(os.path.basename(p).split("_")[1][:-4])))
rows = {}
for f in fs: rows.setdefault(int(os.path.basename(f)[1:].split("_")[0]), []).append(f)
w, h = Image.open(fs[0]).size; im = Image.new("RGB", (4 * w, len(rows) * (h + 22)), (20, 20, 20)); d = ImageDraw.Draw(im)
for r, k in enumerate(sorted(rows)):
    for c, f in enumerate(rows[k]):
        im.paste(Image.open(f), (c * w, r * (h + 22) + 22)); d.text((c * w + 6, r * (h + 22) + 4), "join %d  %s s" % (k, os.path.basename(f).split("_")[1][:-4]), fill=(255, 220, 120))
im.save(W + "/qa_joins.jpg", quality=85); print("joins sheet", im.size)
PY
{
  echo "== 真っ黒なコマ（0.2 秒以上）"; ffmpeg -hide_banner -i $V -vf "blackdetect=d=0.2:pix_th=0.06" -an -f null - 2>&1 | grep -o "black_start:[0-9.]* black_end:[0-9.]* black_duration:[0-9.]*" || echo "なし"
  echo "== 無音（-45dB 以下が 2.5 秒以上）"; ffmpeg -hide_banner -i $V -af "silencedetect=n=-45dB:d=2.5" -vn -f null - 2>&1 | grep -o "silence_start: [0-9.]*\|silence_end: [0-9.]* | silence_duration: [0-9.]*" || echo "なし"
  echo "== 大きさ"; ffmpeg -hide_banner -i $V -af ebur128=peak=true -vn -f null - 2>&1 | grep -A12 "Summary" | grep -E "I:|LRA:|Peak:"
} | tee $W/qa.txt
echo "QA DONE"
