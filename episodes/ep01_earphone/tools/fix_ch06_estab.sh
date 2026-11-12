#!/bin/bash
# 第6章：S3a（巨大イヤホンの引き）・S3 と S6（巨大スマホの引き → 返事ランプ）を描き直して、組み立てと確認ページ用の mp4 を作り直す
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; O=$C/ch06_out; M=$S/review_page/media
R="$(seq 166 281) $(seq 484 643)"; NR=$(echo $R | wc -w)
for f in $R; do rm -f $(printf "$O/frames/f_%04d.png" $f); done
echo "start $(date -u +%H:%M) frames $NR"
SAMPLES=8 bash $C/stage_helper.sh ch06_stage.py $O estab "" 166:189 190:213 214:237 238:261 262:281 484:507 508:531 532:555 556:579 580:603 604:627 628:643
n=0; for f in $R; do p=$(printf "$O/frames/f_%04d.png" $f); [ -s $p ] && n=$((n+1)); done
echo "rendered $n/$NR $(date -u +%H:%M)"; [ $n -lt $NR ] && { echo "STOP: missing frames"; exit 1; }
cd $C && MARU_OUTW=1280 nice -n 5 python3 ch06_assemble.py $O --no_video > $O/assemble_estab.log 2>&1 || { echo "STOP: assemble"; tail -5 $O/assemble_estab.log; exit 1; }
nice -n 5 ffmpeg -v error -y -framerate 24 -i $O/full/f_%04d.png -i $O/ch06_audio.wav -vf "subtitles=$O/ch06_subs.ass:fontsdir=$S/stage/av/fonts" \
  -c:v libx264 -crf 22 -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/ch06_check_v1.mp4
ls -la $M/ch06_check_v1.mp4; echo "FIX ESTAB DONE $(date -u +%H:%M)"
