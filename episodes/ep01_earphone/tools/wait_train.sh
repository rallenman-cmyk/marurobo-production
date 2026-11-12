#!/bin/bash
# 電車の場面の連番を見張る。$1 秒まで待つか、全部描けたか、止められた（OOM）か、描く仕組みが止まったら抜ける
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; T=$S/stage/ch03/train_test
end=$(( $(date +%s) + ${1:-1500} )); k0=$(dmesg 2>/dev/null | grep -ci "killed process")
until [ $(date +%s) -ge $end ]; do
  grep -q "ALL TRAIN DONE" $T/run_train_all.log 2>/dev/null && break
  [ $(dmesg 2>/dev/null | grep -ci "killed process") -gt $k0 ] && { echo "OOM!"; break; }
  pgrep -f "run_train_seq.sh" > /dev/null || { echo "runner gone"; break; }
  sleep 20
done
d=$(find $T/frames_train -name 't_*.png' -size +0 | wc -l); e=$(find $T/frames_train -name 't_*.png' -size 0 | wc -l)
echo "train_done=$d/562 inflight=$e blender=$(pgrep -f ch03_train.py | wc -l) mem_avail=$(free -g | awk '/Mem/{print $7}')G at $(date -u +%H:%MUTC)"
ps -eo rss,args | grep -v grep | grep ch03_train.py | awk '{printf "%dMB ", $1/1024}'; echo
tail -2 $T/run_train_all.log 2>/dev/null; dmesg 2>/dev/null | grep -i "killed process" | tail -1 | cut -c1-120
