#!/bin/bash
# 第6章の舞台（ch06_stage.py）の描き手：与えた範囲を順に回り、まだ無い絵だけを描く（use_overwrite=False / placeholder で他の描き手と取り合わない）
#   一本の Blender は描くほどメモリが増えるので、範囲ごとに起動し直す。EEVEE は一本あたり最大 約3.4GB（同時に3本まで）
# 使い方: ch06_helper.sh 出力 名前 範囲1 範囲2 ...   （範囲は A:B、番号は 1 から）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
OUT=$1; name=$2; shift 2; mkdir -p $OUT/frames
for r in "$@"; do
  a=${r%:*}; b=${r#*:}; miss=0
  for ((f=a; f<=b; f++)); do [ -e $(printf "$OUT/frames/f_%04d.png" $f) ] || { miss=1; break; }; done
  [ $miss = 0 ] && { echo "skip $r (all present)" >> $OUT/run_$name.log; continue; }
  echo "=== range $r start $(date +%H:%M)" >> $OUT/run_$name.log
  (cd $S/stage/ch03 && $S/blender/blender-4.3.2-linux-x64/blender -b $S/handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend \
    --python ch06_stage.py -- --out $OUT --engine eevee --res 640 360 --samples 16 --frames $r) >> $OUT/run_$name.log 2>&1
done
echo "=== helper $name done $(date +%H:%M)" >> $OUT/run_$name.log
