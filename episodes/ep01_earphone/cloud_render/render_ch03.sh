#!/bin/bash
# 第3章の確認用動画：舞台（C3〜C11）を低画質で描く → 欠けたコマを描き直す → 図（C13）→ 章ぜんぶをつなぐ
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=./blender/blender-4.3.2-linux-x64/blender
STORY=handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
OUT=${1:-stage/ch03/anim_v1}; RES=${RES:-"480 270"}; SMP=${SMP:-6}
mkdir -p $OUT/frames
nice -n 8 $B -b --factory-startup $STORY --python stage/ch03/ch03_stage.py -- --out $OUT --frames 1:9999 --res $RES --samples $SMP --engine ${ENG:-eevee} > $OUT/render.log 2>&1
for pass in 1 2; do
  BAD=$(python3 -c "
import os,json
d='$OUT/frames'; n=json.load(open('$OUT/ch03_log.json'))['frames']
from PIL import Image
bad=[]
for f in range(1,n+1):
    p=os.path.join(d,'f_%04d.png'%f)
    try:
        if os.path.getsize(p)==0: raise Exception()
        Image.open(p).verify()
    except Exception: bad.append(f)
print(' '.join(map(str,bad)))")
  [ -z "$BAD" ] && break
  echo "re-render: $BAD" >> $OUT/render.log
  for f in $BAD; do rm -f $OUT/frames/f_$(printf %04d $f).png; nice -n 8 $B -b --factory-startup $STORY --python stage/ch03/ch03_stage.py -- --out $OUT --frames $f:$f --res $RES --samples $SMP --engine ${ENG:-eevee} >> $OUT/render.log 2>&1; done
done
python3 stage/ch03/ch03_diagram.py $OUT >> $OUT/render.log 2>&1
python3 stage/ch03/ch03_assemble.py $OUT >> $OUT/render.log 2>&1 && echo "done $(date +%H:%M)" > ch03_anim.done
