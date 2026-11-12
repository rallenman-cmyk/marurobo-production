#!/bin/bash
# 第3章の舞台のコマを、決めた範囲だけ CHUNK コマずつ描く（毎回 Blender を起動し直す：描くほどメモリが増えるので）。描けたコマは飛ばす
# 使い方: ch03_worker.sh OUT A Z TAG ENGINE W H SAMPLES CHUNK
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=./blender/blender-4.3.2-linux-x64/blender; STORY=handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
OUT=$1; A=$2; Z=$3; TAG=$4; ENG=${5:-eevee}; W=${6:-480}; H=${7:-270}; SMP=${8:-8}; CH=${9:-15}
mkdir -p $OUT/frames
f=$A
while [ $f -le $Z ]; do
  while [ $f -le $Z ] && python3 -c "
import sys
from PIL import Image
try: Image.open('$OUT/frames/f_%04d.png' % $f).verify()
except Exception: sys.exit(1)" 2>/dev/null; do f=$((f+1)); done
  [ $f -gt $Z ] && break
  e=$((f+CH-1)); [ $e -gt $Z ] && e=$Z
  nice -n 5 $B -b --factory-startup $STORY --python stage/ch03/ch03_stage.py -- --out $OUT --frames $f:$e --res $W $H --samples $SMP --engine $ENG >> $OUT/worker_$TAG.log 2>&1
  f=$((e+1))
done
echo "worker $TAG done $(date +%H:%M)" >> $OUT/worker_$TAG.log
