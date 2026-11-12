#!/bin/bash
# 第3章の確認用動画：3つの作業で舞台のコマを描く → 欠けたコマを描き直す → 図 → 章ぜんぶをつなぐ
# 使い方: ch03_run.sh OUT ENGINE W H SAMPLES CHUNK
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
OUT=$1; ENG=$2; W=$3; H=$4; SMP=$5; CH=$6; N=1191
mkdir -p $OUT/frames
./ch03_worker.sh $OUT 1 400 A $ENG $W $H $SMP $CH &
./ch03_worker.sh $OUT 401 800 B $ENG $W $H $SMP $CH &
./ch03_worker.sh $OUT 801 $N C $ENG $W $H $SMP $CH &
wait
for pass in 1 2; do ./ch03_worker.sh $OUT 1 $N FIX$pass $ENG $W $H $SMP $CH; done
[ -d $OUT/diagram ] || cp -r stage/ch03/anim_wb/diagram $OUT/ 2>/dev/null || python3 stage/ch03/ch03_diagram.py $OUT
python3 stage/ch03/ch03_assemble.py $OUT > $OUT/assemble.log 2>&1 && echo "done $(date +%H:%M)" > $OUT/run.done || echo "assemble failed $(date +%H:%M)" > $OUT/run.done
