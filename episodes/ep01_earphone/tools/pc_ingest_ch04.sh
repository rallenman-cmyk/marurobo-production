#!/bin/bash
# PC で描いた第4章 v8 の 3D（1080p の mp4 29 本）を受け取り、1080p の完成版に組む（図は 1080p で描き直す。字幕・声・効果音・札はこちらで）
#   使い方: bash pc_ingest_ch04.sh   （dl_pc/ch04 に mp4 と pairing_log.json）  → stage/final/ch04_final_1080.mp4
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; DL=$S/dl_pc/ch04; O=$C/ch04_out_1080; PR=$C/pair_1080
mkdir -p $O $PR/frames
cp $C/ch04_out/ch04_heads.json $C/ch04_out/D1.png $C/ch04_out/D8.png $O/
cp $DL/pairing_log.json $PR/
for f in $DL/ch04_pair_*.mp4; do b=$(basename $f .mp4); r=${b#ch04_pair_}; a=$((10#${r%-*})); nice -n 5 ffmpeg -v error -y -i $f -start_number $a $PR/frames/p_%04d.png; done
python3 - "$PR" <<'PY'
import os, sys
from PIL import Image
d = os.path.join(sys.argv[1], "frames"); miss = [i for i in range(1, 2827) if not os.path.exists(os.path.join(d, "p_%04d.png" % i))]
sz = Image.open(os.path.join(d, "p_0001.png")).size; print("3D frames", 2826 - len(miss), "/ 2826 missing", miss[:10], "size", sz)
if miss or sz != (1920, 1080): sys.exit("そろっていない")
PY
cd $C && MARU_RES=1080 nice -n 5 python3 ch04_diagram.py $O --v6=$PR > $O/diagram_1080.log 2>&1
echo "diagram6 $(ls $O/diagram6 | wc -l)"
cd $C && MARU_STREAM=1 MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch04_assemble6.py $O --pair=$PR --ver=v8 --alt624 > $O/assemble_1080.log 2>&1
mkdir -p $S/stage/final && cp $O/ch04_v8.mp4 $S/stage/final/ch04_final_1080.mp4
ffprobe -v error -show_entries stream=width,height:format=duration -of compact $S/stage/final/ch04_final_1080.mp4
echo "PC INGEST CH04 DONE"
