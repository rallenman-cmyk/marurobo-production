#!/bin/bash
# PC で描いた第7章・第8章の塔の「まるロボ入り」版（v10 一式：ch07r_stage_*・ch08r_tower_*、1080p の mp4）から、確認ページ用の動画（1280×720）を組む
#   使い方: bash pc_check78r.sh ch07r|ch08r   （dl_pc/ch07r.ok・dl_pc/ch08r.ok がそろっていること）
#   第8章の天びんのまるロボは、本番の大きさの絵（ch03/seesaw）があればそれを、なければ確認用（work_sum/seesaw_p）を使う
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
extract() {  # extract SRC_DIR PREFIX DST_DIR N  → f_NNNN.png（1280×720）
  mkdir -p $3/frames
  for f in $1/$2*.mp4; do b=$(basename $f .mp4); r=${b#$2}; a=$((10#${r%-*})); nice -n 5 ffmpeg -v error -y -i $f -vf scale=1280:720:flags=lanczos -start_number $a $3/frames/f_%04d.png; done
  n=$(ls $3/frames | wc -l); echo "frames $n / $4"; [ "$n" -ge "$4" ] || { echo "STOP: frames missing"; exit 1; }
}
if [ "$1" = "ch07r" ]; then
  O=$C/ch07r_pc; rm -rf $O; mkdir -p $O; cp $DL/ch07r/ch07_log.json $O/; extract $DL/ch07r ch07r_stage_ $O 3458
  cd $C && MARU_OUTW=1280 MARU_NOTE="確認用・本番の光（PC で描いた絵を小さくしたもの）・まるロボ入り" nice -n 5 python3 ch07_assemble.py $O --no_video > $O/assemble.log 2>&1
  page $O ch07_check_v3 $O/ch07_audio.wav $O/ch07_subs.ass 63.1
  rm -rf $O/full $O/frames; echo "PC CHECK CH07R DONE"
fi
if [ "$1" = "ch08r" ]; then
  O=$C/ch08r_pc; A8=$S/work8/asm; AW=$S/work8/asm_wb; rm -rf $O; mkdir -p $O; cp $DL/ch08r/ch08_tower_log.json $O/; extract $DL/ch08r ch08r_tower_ $O 510
  SSD=$C/seesaw; [ -f $SSD/seesaw_B.json ] || SSD=$S/work_sum/seesaw_p
  cd $C && MARU_SEESAW=$SSD nice -n 5 python3 ch08_game.py $A8 --redo > $A8/game_1280.log 2>&1      # 図（2D）は天びんのまるロボ入りで描き直す
  cp $A8/ch08_game.json $AW/
  cd $C && MARU_OUTW=1280 MARU_NOTE="確認用・本番の光（PC で描いた塔を小さくしたもの）・まるロボ入り（塔・天びん）" nice -n 5 python3 ch08_assemble.py $AW --tower $O --no_video > $AW/assemble.log 2>&1
  page $AW ch08_check_v5 $AW/ch08_audio.wav $AW/ch08_subs.ass 101.6
  rm -rf $AW/full $O/frames; echo "PC CHECK CH08R DONE"
fi
