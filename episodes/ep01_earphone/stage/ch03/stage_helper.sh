#!/bin/bash
# 舞台の描き手（第6章・第7章・第8章の塔）：与えた範囲を順に回り、まだ無い絵だけを描く（use_overwrite=False / placeholder で他の描き手と取り合わない）
#   一本の Blender は描くほどメモリが増えるので、範囲ごとに起動し直す
# 使い方: stage_helper.sh スクリプト 出力 名前 "追加の引数" 範囲1 範囲2 ...   （範囲は A:B、番号は 1 から）
#   例: stage_helper.sh ch07_stage.py /path/out w1 "--part ch7" 1:150 151:300
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
SCRIPT=$1; OUT=$2; name=$3; EXTRA=$4; shift 4; mkdir -p $OUT/frames
for r in "$@"; do
  a=${r%:*}; b=${r#*:}; miss=0
  for ((f=a; f<=b; f++)); do [ -e $(printf "$OUT/frames/f_%04d.png" $f) ] || { miss=1; break; }; done
  [ $miss = 0 ] && { echo "skip $r (all present)" >> $OUT/run_$name.log; continue; }
  echo "=== range $r start $(date +%H:%M)" >> $OUT/run_$name.log
  (cd $S/stage/ch03 && $S/blender/blender-4.3.2-linux-x64/blender -b $S/handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend \
    --python $SCRIPT -- --out $OUT --engine eevee --res 640 360 --samples ${SAMPLES:-16} $EXTRA --frames $r) >> $OUT/run_$name.log 2>&1
done
echo "=== helper $name done $(date +%H:%M)" >> $OUT/run_$name.log
