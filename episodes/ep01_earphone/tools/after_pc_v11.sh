#!/bin/bash
# PC の v11 一式（まとめ・冒頭・第7章・第8章）が届いたら：本番を新しい字幕で組む → 字幕の点検の一覧 → 通しの完成版 → 点検
#   見張り（drive_watch.py）が時間切れで終わっていて、まだそろっていなければ、残りの章で見張りをやり直す（最大 8 時間）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; DL=$S/dl_pc; C=$S/stage/ch03; H=$S/stage/human; WS=$S/work_subs
need="sum ch07r ch08r op"
cnt() { n=0; for c in $need; do [ -f $DL/$c.ok ] && n=$((n + 1)); done; echo $n; }
num() { case $1 in sum) echo 4;; ch07r) echo 35;; ch08r) echo 6;; op) echo 8;; esac; }
while [ "$(cnt)" -lt 4 ]; do
  if ! pgrep -f "python3 -I .*drive_watch.py" > /dev/null; then
    left=""; for c in $need; do [ -f $DL/$c.ok ] || left="$left $c:$(num $c)"; done
    echo "$(date -u +%T) 見張りをやり直す:$left"
    MARU_WATCH_SEC=28800 nohup python3 -I $S/tools/drive_watch.py $left >> $DL/watch_v11b.log 2>&1 &
    sleep 5
  fi
  sleep 60
done
echo "$(date -u +%T) PC の絵がそろった"
bash $S/tools/finals_78s.sh ch07 ch08 sum || { echo "STOP: finals_78s"; exit 1; }
bash $S/tools/pc_ingest_op.sh || { echo "STOP: pc_ingest_op"; exit 1; }
cd $S/tools
python3 subs_check.py $S/stage/final/ch07_final_1080.mp4 $C/ch07r_final/ch07_subs.ass $WS/chk_ch07
python3 subs_check.py $S/stage/final/ch08_final_1080.mp4 $S/work8/final/ch08_subs.ass $WS/chk_ch08
python3 subs_check.py $S/stage/final/summary_final_1080.mp4 $S/work_sum/sum_final/summary_subs.ass $WS/chk_sum
python3 subs_check.py $S/stage/final/ch0102_final_1080.mp4 $H/anim_ch0102_1080/ch0102_subs.ass $WS/chk_ch0102
bash $S/tools/concat_full.sh || { echo "STOP: concat_full"; exit 1; }
bash $S/tools/final_qa.sh
echo "CHAIN DONE $(date -u +%T)"
