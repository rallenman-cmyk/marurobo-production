#!/bin/bash
# 冒頭の確認用ができたら、第8章の天びんのまるロボ（本番の大きさ）の描画を再開する（描けているコマは飛ばす）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; B=$S/blender/blender-4.3.2-linux-x64/blender; O=$C/seesaw
while pgrep -f "tools/op_preview.sh" > /dev/null; do sleep 30; done
find $O -name "f_*.png" -size 0 -delete
for sc in A B; do (cd $C && nice -n 8 $B -b $S/handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend --python-exit-code 1 --python ch08_seesaw_render.py -- --out $O --scene $sc --engine eevee --samples 24 --scale 1.0 > $O/run2_$sc.log 2>&1 &); done
sleep 5; echo "seesaw resumed $(date -u +%T)"
