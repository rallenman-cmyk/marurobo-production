#!/bin/bash
# 第8章の確認用（まるロボ入り・簡易描画）を組み直す（「鳴らし始める」の札をなくした版）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; M=$S/review_page/media; IMG=$S/review_page/img
A8=$S/work8/asm_wb; W8=$S/work_sum/c8wb; NOTE="確認用・簡易描画（光と色は本番と違います）・まるロボ入り"
cd $C && MARU_OUTW=1280 MARU_NOTE="$NOTE" nice -n 5 python3 ch08_assemble.py $A8 --tower $W8 --no_video > $A8/assemble.log 2>&1 || { echo "STOP"; tail -20 $A8/assemble.log; exit 1; }
for crf in 23 26; do
  nice -n 5 ffmpeg -v error -y -framerate 24 -i $A8/full/f_%04d.png -i $A8/ch08_audio.wav -vf "subtitles=$A8/ch08_subs.ass:fontsdir=$S/stage/av/fonts" \
    -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/ch08_check_v3.mp4
  sz=$(stat -c %s $M/ch08_check_v3.mp4); echo "crf $crf size $sz"; [ $sz -le 15000000 ] && break
done
ffmpeg -v error -y -ss 12.0 -i $M/ch08_check_v3.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_ch08_check_v3.jpg
rm -rf $A8/full; ffprobe -v error -show_entries format=duration -of csv=p=0 $M/ch08_check_v3.mp4; echo "REDO CH8 DONE"
