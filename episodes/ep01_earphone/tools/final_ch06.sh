#!/bin/bash
# 第6章の本番（1080p）：PC で描いた mp4 20本 → 1920×1080 の連番 → 札・字幕・声・曲を重ねて直接 mp4 へ（MARU_STREAM=1）
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; DL=$S/dl_pc/ch06; O=$C/ch06_final
mkdir -p $O/frames; cp $DL/ch06_log.json $O/
for f in $DL/ch06_stage_*.mp4; do b=$(basename $f .mp4); r=${b#ch06_stage_}; a=$((10#${r%-*})); nice -n 5 ffmpeg -v error -y -i $f -start_number $a $O/frames/f_%04d.png; done
python3 - "$O" <<'PY'
import os, sys
from PIL import Image
d = os.path.join(sys.argv[1], "frames"); miss = [i for i in range(1, 1934) if not os.path.exists(os.path.join(d, "f_%04d.png" % i))]
sz = Image.open(os.path.join(d, "f_0001.png")).size; print("frames", 1933 - len(miss), "/ 1933 missing", miss[:10], "size", sz)
if miss or sz != (1920, 1080): sys.exit("そろっていない")
PY
cd $C && MARU_STREAM=1 MARU_OUTW=1920 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch06_assemble.py $O > $O/assemble_final.log 2>&1
mkdir -p $S/stage/final && cp $O/ch06_animatic.mp4 $S/stage/final/ch06_final_1080.mp4
ffprobe -v error -show_entries stream=width,height:format=duration -of compact $S/stage/final/ch06_final_1080.mp4
rm -rf $O/frames
echo "FINAL CH06 DONE"
