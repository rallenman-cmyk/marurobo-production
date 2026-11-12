#!/bin/bash
# 第5章の本番（1080p）を組み直す（2026-11-09 夜：長い間を切る・9:26 の前を少し速く・8:26/8:45 の声の前に間）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; O5=$C/ch5_final3
[ -f $C/ch5_final/ch05_final_1080_before_fix1109b.mp4 ] || cp $C/ch5_final/ch05_final_1080.mp4 $C/ch5_final/ch05_final_1080_before_fix1109b.mp4
mkdir -p $O5
echo "frames $(date -u +%T)"
(cd $C && MARU_RES=1080 nice -n 5 python3 ch05_frames_par.py $O5 ${1:-3} > $O5/frames.log 2>&1) || { echo "STOP: 第5章の図"; tail -5 $O5/frames.log; exit 1; }
echo "assemble $(date -u +%T)"
(cd $C && MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch05_assemble.py $O5 > $O5/assemble.log 2>&1) || { echo "STOP: 第5章の組み立て"; tail -5 $O5/assemble.log; exit 1; }
cp $O5/ch05_v2_voice.mp4 $C/ch5_final/ch05_final_1080.mp4
ffprobe -v error -show_entries stream=width,height:format=duration -of compact $C/ch5_final/ch05_final_1080.mp4
echo "CH05 DONE $(date -u +%T)"
