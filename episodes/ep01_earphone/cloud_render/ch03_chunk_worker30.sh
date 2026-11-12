#!/bin/bash
# 決めた範囲を30コマずつ、毎回Blenderを起動し直して描く（描くほどメモリが増えるので）。すでに描けたコマは飛ばす
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=./blender/blender-4.3.2-linux-x64/blender; STORY=handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
OUT=stage/ch03/anim_eevee; A=$1; Z=$2; TAG=$3
f=$A
while [ $f -le $Z ]; do
  while [ $f -le $Z ] && python3 -c "
import sys
from PIL import Image
try: Image.open('$OUT/frames/f_%04d.png' % $f).verify()
except Exception: sys.exit(1)" 2>/dev/null; do f=$((f+1)); done
  [ $f -gt $Z ] && break
  e=$((f+29)); [ $e -gt $Z ] && e=$Z
  $B -b --factory-startup $STORY --python stage/ch03/ch03_stage.py -- --out $OUT --frames $f:$e --res 480 270 --samples 8 >> $OUT/worker_$TAG.log 2>&1
  f=$((e+1))
done
echo "worker $TAG done $(date +%H:%M)" >> $OUT/worker_$TAG.log
