#!/bin/bash
# 第3章の舞台（C3〜C11）を本番と同じ光（EEVEE）で、低画質（480×270・8サンプル）で描く：3つに分けて同時に → 欠けたコマを描き直す → 図 → 章ぜんぶをつなぐ
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=./blender/blender-4.3.2-linux-x64/blender; STORY=handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
OUT=stage/ch03/anim_eevee; mkdir -p $OUT/frames
for r in 1:397 398:794 795:1191; do
  $B -b --factory-startup $STORY --python stage/ch03/ch03_stage.py -- --out $OUT --frames $r --res 480 270 --samples 8 > $OUT/render_${r%%:*}.log 2>&1 &
  sleep 20
done
wait
for pass in 1 2; do
  BAD=$(python3 -c "
import os
from PIL import Image
bad=[]
for f in range(1,1192):
    p='$OUT/frames/f_%04d.png'%f
    try:
        if os.path.getsize(p)==0: raise Exception()
        Image.open(p).verify()
    except Exception: bad.append(f)
print(' '.join(map(str,bad)))")
  [ -z "$BAD" ] && break
  echo "re-render: $BAD" >> $OUT/render_fix.log
  for f in $BAD; do $B -b --factory-startup $STORY --python stage/ch03/ch03_stage.py -- --out $OUT --frames $f:$f --res 480 270 --samples 8 >> $OUT/render_fix.log 2>&1; done
done
cp -r stage/ch03/anim_wb/diagram $OUT/ 2>/dev/null || python3 stage/ch03/ch03_diagram.py $OUT
python3 stage/ch03/ch03_assemble.py $OUT > $OUT/assemble.log 2>&1 && echo "done $(date +%H:%M)" > ch03_eevee.done
