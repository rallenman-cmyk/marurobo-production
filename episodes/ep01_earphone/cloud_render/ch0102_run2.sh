#!/bin/bash
# 第1・2章の確認用動画：3つの作業でコマを描く → 欠けたコマを描き直す → 字幕・音をつけてつなぐ
# 使い方: ch0102_run.sh OUT ENGINE W H SAMPLES CHUNK
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
OUT=$1; ENG=$2; W=$3; H=$4; SMP=$5; CH=$6; N=1944
./ch0102_worker2.sh $OUT 1 648 A $ENG $W $H $SMP $CH &
./ch0102_worker2.sh $OUT 649 1296 B $ENG $W $H $SMP $CH &
./ch0102_worker2.sh $OUT 1297 $N C $ENG $W $H $SMP $CH &
wait
for pass in 1 2; do ./ch0102_worker2.sh $OUT 1 $N FIX$pass $ENG $W $H $SMP $CH; done
cd stage/human && python3 ch0102_assemble.py $OUT > $OUT/assemble.log 2>&1 && echo "done $(date +%H:%M)" > $OUT/run.done || echo "assemble failed $(date +%H:%M)" > $OUT/run.done
