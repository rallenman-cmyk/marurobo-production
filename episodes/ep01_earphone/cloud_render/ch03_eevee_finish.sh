#!/bin/bash
# 3つの作業が終わるのを待つ → 欠けたコマを描き直す（30コマずつ）→ 図 → 章ぜんぶをつなぐ
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
OUT=stage/ch03/anim_eevee
while pgrep -f ch03_chunk_worker >/dev/null; do sleep 10; done; sleep 5; while pgrep -f ch03_chunk_worker >/dev/null; do sleep 10; done
for pass in 1 2; do
  ./ch03_chunk_worker15.sh 1 1191 FIX$pass
done
cp -r stage/ch03/anim_wb/diagram $OUT/ 2>/dev/null
python3 stage/ch03/ch03_assemble.py $OUT > $OUT/assemble.log 2>&1 && echo "done $(date +%H:%M)" > ch03_eevee.done || echo "assemble failed" > ch03_eevee.done
