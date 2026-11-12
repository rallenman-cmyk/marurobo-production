#!/bin/bash
# 冒頭（網棚のまるロボ）の描き直し（PC：ch0102r_0001-0100.mp4 … 0701-0800.mp4 の 8 本）を受け取り、
#   残り（801〜1944 コマ）は前の PC の絵（dl_pc/ch0102）のまま、1080p で組み直す（字幕・声・音はこちらで付ける）
#   使い方: bash pc_ingest_op.sh   （dl_pc/op.ok がそろっていること）→ stage/final/ch0102_final_1080.mp4（前のものは *_before_rack.mp4 に残す）
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; H=$S/stage/human; F=$S/stage/final
NEW=$S/dl_pc/op; OLD=$S/dl_pc/ch0102; O=$H/anim_ch0102_1080
rm -rf $O/frames; mkdir -p $O/frames
cp $NEW/ch0102_log.json $O/                                            # 新しい版の記録（まるロボの動きの時刻）
for f in $OLD/ch0102_*.mp4; do                                        # 前の版：801 コマ目から
  b=$(basename "$f" .mp4); r=${b#ch0102_}; a=$((10#${r%-*}))
  [ $a -ge 801 ] && nice -n 5 ffmpeg -v error -y -i "$f" -start_number $a $O/frames/f_%04d.png
done
for f in $NEW/ch0102r_*.mp4; do                                       # 新しい版：1〜800 コマ
  b=$(basename "$f" .mp4); r=${b#ch0102r_}; a=$((10#${r%-*}))
  nice -n 5 ffmpeg -v error -y -i "$f" -start_number $a $O/frames/f_%04d.png
done
python3 - "$O" <<'PY'
import os, sys, json
from PIL import Image
o = sys.argv[1]; st = set(os.listdir(os.path.join(o, "frames"))); n = json.load(open(os.path.join(o, "ch0102_log.json")))["frames"]
miss = [i for i in range(1, n + 1) if "f_%04d.png" % i not in st]
sz = Image.open(os.path.join(o, "frames", "f_0001.png")).size
print("frames", len(st), "/", n, "missing", miss[:10], "size", sz)
if miss or sz != (1920, 1080): sys.exit("そろっていない")
PY
cd $H && MARU_STREAM=1 MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch0102_assemble.py $O > $O/assemble_op.log 2>&1
[ -f $F/ch0102_final_1080_before_rack.mp4 ] || cp $F/ch0102_final_1080.mp4 $F/ch0102_final_1080_before_rack.mp4
cp $O/ch0102_animatic.mp4 $F/ch0102_final_1080.mp4
ffprobe -v error -show_entries stream=width,height:format=duration -of compact $F/ch0102_final_1080.mp4
rm -rf $O/frames
echo "PC INGEST OP DONE"
