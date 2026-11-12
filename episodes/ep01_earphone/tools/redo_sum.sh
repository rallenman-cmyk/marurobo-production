#!/bin/bash
# まとめだけ組み直す（本番 1080p）＋確認ページ用（1280×720・15MB 以下）＋表紙
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; F=$S/stage/final; M=$S/review_page/media; IMG=$S/review_page/img
bash $S/tools/finals_78s.sh sum || { echo "STOP: まとめ"; exit 1; }
for crf in 23 26 29; do
  nice -n 5 ffmpeg -v error -y -i $F/summary_final_1080.mp4 -vf scale=1280:720:flags=lanczos -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -c:a aac -b:a 128k $M/summary_check_v2.mp4
  sz=$(stat -c %s $M/summary_check_v2.mp4); echo "summary_check_v2 crf $crf size $sz"; [ $sz -le 15000000 ] && break
done
ffmpeg -v error -y -ss 20.9 -i $M/summary_check_v2.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_summary_check_v2.jpg
echo "REDO SUM DONE $(date -u +%T)"
