#!/bin/bash
# 第6章の描き手（run_ch678.sh 2 24 ch6）が終わるのを待ち、欠けた絵があれば描き足してから、第7章・第8章の塔を続けて描く
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; LOG=$C/ch678_workers.log
PID=$1
while kill -0 $PID 2>/dev/null; do sleep 30; done
ok() { find $1/frames -name 'f_*.png' -size +1k | wc -l; }
for pass in 1 2; do
  n=$(ok $C/ch06_out); echo "CH6 CHECK pass$pass ok=$n/1933 $(date -u +%H:%M)" >> $LOG
  [ $n -ge 1933 ] && break
  find $C/ch06_out/frames -name 'f_*.png' -size -1k -delete
  SAMPLES=8 bash $S/tools/run_ch678.sh 2 24 ch6
done
echo "CH6 FRAMES OK $(ok $C/ch06_out) $(date -u +%H:%M)" >> $LOG
SAMPLES=8 bash $S/tools/run_ch678.sh 2 24 ch7 ch8
for d in ch07_out:3458 ch08_tower_out:510; do
  o=${d%:*}; N=${d#*:}; n=$(ok $C/$o)
  if [ $n -lt $N ]; then find $C/$o/frames -name 'f_*.png' -size -1k -delete; fi
done
n7=$(ok $C/ch07_out); n8=$(ok $C/ch08_tower_out)
if [ $n7 -lt 3458 ] || [ $n8 -lt 510 ]; then
  echo "CH78 REDO ch7=$n7 ch8=$n8 $(date -u +%H:%M)" >> $LOG
  SAMPLES=8 bash $S/tools/run_ch678.sh 2 24 ch7 ch8
fi
echo "CH78 FRAMES ch7=$(ok $C/ch07_out)/3458 ch8=$(ok $C/ch08_tower_out)/510 $(date -u +%H:%M)" >> $LOG
