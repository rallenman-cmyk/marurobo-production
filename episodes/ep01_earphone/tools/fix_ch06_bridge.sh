#!/bin/bash
# 第6章：橋を渡る2カット（S6b・S8）だけ描き直して、組み立てと確認ページ用の mp4 を作り直す
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; O=$C/ch06_out; M=$S/review_page/media
for f in $(seq 640 716) $(seq 816 912); do rm -f $(printf "$O/frames/f_%04d.png" $f); done
echo "start $(date -u +%H:%M)"
SAMPLES=8 bash $C/stage_helper.sh ch06_stage.py $O fix "" 640:663 664:687 688:716 816:839 840:863 864:887 888:912
n=0; for f in $(seq 640 716) $(seq 816 912); do p=$(printf "$O/frames/f_%04d.png" $f); [ -s $p ] && n=$((n+1)); done
echo "rendered $n/174 $(date -u +%H:%M)"; [ $n -lt 174 ] && { echo "STOP: missing frames"; exit 1; }
cd $C && MARU_OUTW=1280 nice -n 5 python3 ch06_assemble.py $O --no_video > $O/assemble_fix.log 2>&1 || { echo "STOP: assemble"; tail -5 $O/assemble_fix.log; exit 1; }
nice -n 5 ffmpeg -v error -y -framerate 24 -i $O/full/f_%04d.png -i $O/ch06_audio.wav -vf "subtitles=$O/ch06_subs.ass:fontsdir=$S/stage/av/fonts" \
  -c:v libx264 -crf 22 -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/ch06_check_v1.mp4
ls -la $M/ch06_check_v1.mp4; echo "FIX CH06 DONE $(date -u +%H:%M)"
