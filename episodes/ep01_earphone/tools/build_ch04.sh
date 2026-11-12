#!/bin/bash
# 第4章の本番（1080p）を組み直す（2026-11-09 夜の直し：2:59 の絵・3:28 を切る・6:16 の前の間・5:00〜5:09 の電車・緑の位置・白い絵の具の音）
#   3D のコマ（pair_1080/frames）と図（ch04_out_1080/diagram6）はできているものを使う
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; O=$C/ch04_out_1080; PR=$C/pair_1080; F=$S/stage/final
n=$(ls $PR/frames | wc -l); [ "$n" -ge 2826 ] || { echo "STOP: 3D のコマ $n"; exit 1; }
[ -f $F/ch04_final_1080_before_fix1109b.mp4 ] || cp $F/ch04_final_1080.mp4 $F/ch04_final_1080_before_fix1109b.mp4
cd $C && MARU_RES=1080 nice -n 5 python3 ch04_diagram.py $O --v6=$PR > $O/diagram_1080.log 2>&1 || { echo "STOP: 図"; exit 1; }
echo "diagram6 $(ls $O/diagram6 | wc -l)  $(date -u +%T)"
cd $C && MARU_STREAM=1 MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch04_assemble6.py $O --pair=$PR --ver=v8 --alt624 > $O/assemble_1080.log 2>&1 || { echo "STOP: 組み立て"; tail -5 $O/assemble_1080.log; exit 1; }
cp $O/ch04_v8.mp4 $F/ch04_final_1080.mp4
ffprobe -v error -show_entries stream=width,height:format=duration -of compact $F/ch04_final_1080.mp4
echo "CH04 DONE $(date -u +%T)"
