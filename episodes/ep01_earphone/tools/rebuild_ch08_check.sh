#!/bin/bash
# 第8章の確認用 第2版（字幕と同じ文の札をなくし、残す字を大きく）：2D の図を描き直し → 塔の絵（PC）と組む → 1280×720 の mp4 と表紙
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; A8=$S/work8/asm; O=$C/ch08_pc; DL=$S/dl_pc/ch08; M=$S/review_page/media; IMG=$S/review_page/img
mkdir -p $O/frames
for f in $DL/ch08_tower_*.mp4; do b=$(basename $f .mp4); r=${b#ch08_tower_}; a=$((10#${r%-*})); nice -n 8 ffmpeg -v error -y -i $f -vf scale=1280:720:flags=lanczos -start_number $a $O/frames/f_%04d.png; done
cp $DL/ch08_tower_log.json $O/
cd $C && nice -n 8 python3 ch08_game.py $A8 --redo > $A8/game_1280.log 2>&1
cd $C && MARU_OUTW=1280 nice -n 8 python3 ch08_assemble.py $A8 --tower $O --no_video > $A8/assemble.log 2>&1
for crf in 23 26; do
  nice -n 8 ffmpeg -v error -y -framerate 24 -i $A8/full/f_%04d.png -i $A8/ch08_audio.wav -vf "subtitles=$A8/ch08_subs.ass:fontsdir=$S/stage/av/fonts" \
    -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/ch08_check_v2.mp4
  sz=$(stat -c %s $M/ch08_check_v2.mp4); echo "crf $crf size $sz"; [ $sz -le 15000000 ] && break
done
ffmpeg -v error -y -ss 66.0 -i $M/ch08_check_v2.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_ch08_check_v2.jpg
rm -rf $O/frames
ffprobe -v error -show_entries format=duration -of csv=p=0 $M/ch08_check_v2.mp4
echo "REBUILD CH08 DONE"
