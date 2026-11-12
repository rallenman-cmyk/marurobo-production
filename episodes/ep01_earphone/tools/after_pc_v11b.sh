#!/bin/bash
# 2026-11-09 夜（字幕は 1行25字・文字 56、まとめの 182 を 1.35 秒遅らせた版）：
#   ① 第3〜6章を新しい字幕で組み直す（並行）  ② まとめ → 第7章 → 第8章の本番（PC の絵）  ③ まとめの確認用動画（確認ページ用）
#   ④ 冒頭（PC の絵 op）が届いたら組む  ⑤ 字幕の点検の一覧  ⑥ 通しの完成版  ⑦ 点検
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; DL=$S/dl_pc; C=$S/stage/ch03; H=$S/stage/human; WS=$S/work_subs; F=$S/stage/final
M=$S/review_page/media; IMG=$S/review_page/img
( bash $S/tools/resub_3456.sh > $WS/resub2.log 2>&1; echo "RESUB EXIT $?" >> $WS/resub2.log ) &
PB=$!
echo "$(date -u +%T) 第3〜6章の組み直しを始めた（pid $PB）"
bash $S/tools/finals_78s.sh sum || { echo "STOP: まとめ"; exit 1; }
for crf in 23 26 29; do                                                       # 確認ページ用（1280×720・15MB 以下）
  nice -n 5 ffmpeg -v error -y -i $F/summary_final_1080.mp4 -vf scale=1280:720:flags=lanczos -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -c:a aac -b:a 128k $M/summary_check_v2.mp4
  sz=$(stat -c %s $M/summary_check_v2.mp4); echo "summary_check_v2 crf $crf size $sz"; [ $sz -le 15000000 ] && break
done
ffmpeg -v error -y -ss 20.9 -i $M/summary_check_v2.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_summary_check_v2.jpg
echo "SUMMARY CHECK READY $(date -u +%T)"
bash $S/tools/finals_78s.sh ch07 || { echo "STOP: 第7章"; exit 1; }
bash $S/tools/finals_78s.sh ch08 || { echo "STOP: 第8章"; exit 1; }
while [ ! -f $DL/op.ok ]; do                                                 # 冒頭の絵を待つ（見張りが終わっていたら、やり直す）
  if ! pgrep -f "python3 -I .*drive_watch.py" > /dev/null; then
    echo "$(date -u +%T) 見張りをやり直す: op"; MARU_WATCH_SEC=28800 nohup python3 -I $S/tools/drive_watch.py op:8 >> $DL/watch_v11b.log 2>&1 &
    sleep 5
  fi
  sleep 60
done
echo "$(date -u +%T) 冒頭の絵がそろった"
bash $S/tools/pc_ingest_op.sh || { echo "STOP: 冒頭"; exit 1; }
wait $PB; tail -2 $WS/resub2.log
grep -q "RESUB DONE" $WS/resub2.log || { echo "STOP: 第3〜6章の組み直し"; exit 1; }
cd $S/tools
python3 subs_check.py $F/ch0102_final_1080.mp4 $H/anim_ch0102_1080/ch0102_subs.ass $WS/chk2_ch0102
python3 subs_check.py $F/ch03_final_1080.mp4 $C/anim_1080/ch03_subs.ass $WS/chk2_ch03
python3 subs_check.py $F/ch04_final_1080.mp4 $C/ch04_out_1080/ch04_subs8.ass $WS/chk2_ch04
python3 subs_check.py $C/ch5_final/ch05_final_1080.mp4 $C/ch5_final2/ch05_subs.ass $WS/chk2_ch05
python3 subs_check.py $F/ch06_final_1080.mp4 $C/ch06_final/ch06_subs.ass $WS/chk2_ch06
python3 subs_check.py $F/ch07_final_1080.mp4 $C/ch07r_final/ch07_subs.ass $WS/chk2_ch07
python3 subs_check.py $F/ch08_final_1080.mp4 $S/work8/final/ch08_subs.ass $WS/chk2_ch08
python3 subs_check.py $F/summary_final_1080.mp4 $S/work_sum/sum_final/summary_subs.ass $WS/chk2_sum
echo "SUBS CHECK SHEETS DONE $(date -u +%T)"
bash $S/tools/concat_full.sh || { echo "STOP: 通し"; exit 1; }
bash $S/tools/final_qa.sh
echo "CHAIN DONE $(date -u +%T)"
