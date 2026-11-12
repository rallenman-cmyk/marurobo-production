#!/bin/bash
# PC で描いた第7章・第8章の塔（1080p の mp4）から、確認ページ用の動画（1280×720）を組む
#   使い方: bash pc_check78.sh ch07|ch08   （dl_pc/ch07.ok・dl_pc/ch08.ok がそろっていること）
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; DL=$S/dl_pc; M=$S/review_page/media; IMG=$S/review_page/img
page() {  # page OUTDIR NAME AUDIO SUBS POSTER_T
  for crf in 23 26 29; do
    nice -n 5 ffmpeg -v error -y -framerate 24 -i $1/full/f_%04d.png -i $3 -vf "subtitles=$4:fontsdir=$S/stage/av/fonts" \
      -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/$2.mp4
    sz=$(stat -c %s $M/$2.mp4); echo "$2 crf $crf size $sz"; [ $sz -le 15000000 ] && break
  done
  ffmpeg -v error -y -ss $5 -i $M/$2.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_$2.jpg
  ffprobe -v error -show_entries format=duration -of csv=p=0 $M/$2.mp4
}
extract() {  # extract SRC_DIR PREFIX DST_DIR  → f_NNNN.png（1280×720）
  mkdir -p $3/frames
  for f in $1/$2*.mp4; do b=$(basename $f .mp4); r=${b#$2}; a=$((10#${r%-*})); nice -n 5 ffmpeg -v error -y -i $f -vf scale=1280:720:flags=lanczos -start_number $a $3/frames/f_%04d.png; done
  echo "frames $(ls $3/frames | wc -l)"
}
if [ "$1" = "ch07" ]; then
  O=$C/ch07_pc; mkdir -p $O; cp $DL/ch07/ch07_log.json $O/; extract $DL/ch07 ch07_stage_ $O
  cd $C && MARU_OUTW=1280 nice -n 5 python3 ch07_assemble.py $O --no_video > $O/assemble.log 2>&1
  page $O ch07_check_v1 $O/ch07_audio.wav $O/ch07_subs.ass 62.5
  echo "PC CHECK CH07 DONE"
fi
if [ "$1" = "ch08" ]; then
  O=$C/ch08_pc; A8=$S/work8/asm; mkdir -p $O; cp $DL/ch08/ch08_tower_log.json $O/; extract $DL/ch08 ch08_tower_ $O
  cd $C && nice -n 5 python3 ch08_game.py $A8 --redo > $A8/game_1280.log 2>&1                     # 図（2D）は 1280×720 で描き直す
  cd $C && MARU_OUTW=1280 nice -n 5 python3 ch08_assemble.py $A8 --tower $O --no_video > $A8/assemble.log 2>&1
  page $A8 ch08_check_v1 $A8/ch08_audio.wav $A8/ch08_subs.ass 66.0
  echo "PC CHECK CH08 DONE"
fi
