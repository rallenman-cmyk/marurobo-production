#!/bin/bash
# 第4章の組み立て（WROTE が出るか、止まるまで）と、電車の場面の連番の進みを見張る。$1 秒まで待つ
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
L=$S/stage/ch03/ch04_out/assemble_v7.log; T=$S/stage/ch03/train_test/frames_train
end=$(( $(date +%s) + ${1:-540} ))
until [ $(date +%s) -ge $end ]; do
  if grep -q "WROTE" $L 2>/dev/null; then break; fi
  if ! pgrep -f ch04_assemble6.py > /dev/null; then break; fi
  sleep 15
done
n=$(find $T -name 't_*.png' -size +0 | wc -l); e=$(find $T -name 't_*.png' -size 0 | wc -l)
echo "ch04: $(tail -c 300 $L | tr '\r' '\n' | grep -v '^$' | tail -2 | tr '\n' ' ')"
echo "ch04_running=$(pgrep -f ch04_assemble6.py | wc -l) train_done=$n/562 train_inflight=$e blender=$(pgrep -f ch03_train.py | wc -l) mem_avail=$(free -g | awk '/Mem/{print $7}')G at $(date -u +%H:%MUTC)"
