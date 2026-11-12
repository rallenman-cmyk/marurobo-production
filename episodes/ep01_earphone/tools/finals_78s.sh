#!/bin/bash
# PC の本番の絵（v10/v11：sum・ch07r・ch08r）が届いたら、1080p の本番を組む：第7章 → 第8章 → まとめ
#   使い方: bash finals_78s.sh [ch07] [ch08] [sum]   （何も書かなければ全部。dl_pc/<名前>.ok がそろっていること）
#   どれも画像を書き出さずに ffmpeg へ直接流す（MARU_STREAM=1）。3D の絵だけ一度 PNG にして、組んだら消す
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; DL=$S/dl_pc; F=$S/stage/final; mkdir -p $F
WANT="${*:-ch07 ch08 sum}"
has() { case " $WANT " in *" $1 "*) return 0;; esac; return 1; }
extract() {  # extract SRC_DIR PREFIX DST_FRAMES N
  mkdir -p $3
  for f in $1/$2*.mp4; do b=$(basename $f .mp4); r=${b#$2}; a=$((10#${r%-*})); nice -n 5 ffmpeg -v error -y -i $f -start_number $a $3/f_%04d.png; done
  n=$(ls $3 | wc -l); echo "  frames $n / $4"; [ "$n" -ge "$4" ]
}
if has ch07; then
  echo "== 第7章 $(date -u +%T)"; [ -f $DL/ch07r.ok ] || { echo "STOP: dl_pc/ch07r.ok がない"; exit 1; }
  O=$C/ch07r_final; rm -rf $O; mkdir -p $O; cp $DL/ch07r/ch07_log.json $O/
  extract $DL/ch07r ch07r_stage_ $O/frames 3458 || { echo "STOP: 第7章のコマ"; exit 1; }
  (cd $C && MARU_STREAM=1 MARU_OUTW=1920 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch07_assemble.py $O > $O/assemble.log 2>&1) || { echo "STOP: 第7章の組み立て"; tail -5 $O/assemble.log; exit 1; }
  [ -f $F/ch07_final_1080.mp4 ] && [ ! -f $F/ch07_final_1080_before_fix1109b.mp4 ] && cp $F/ch07_final_1080.mp4 $F/ch07_final_1080_before_fix1109b.mp4   # 前の本番を残す（一度だけ）
  cp $O/ch07_animatic.mp4 $F/ch07_final_1080.mp4; rm -rf $O/frames
  ffprobe -v error -show_entries stream=width,height:format=duration -of compact $F/ch07_final_1080.mp4
fi
if has ch08; then
  echo "== 第8章 $(date -u +%T)"; [ -f $DL/ch08r.ok ] || { echo "STOP: dl_pc/ch08r.ok がない"; exit 1; }
  [ -f $C/seesaw/seesaw_B.json ] && [ "$(ls $C/seesaw/A | wc -l)" -ge 191 ] && [ "$(ls $C/seesaw/B | wc -l)" -ge 274 ] || { echo "STOP: 天びんのまるロボ（本番の大きさ）がそろっていない"; exit 1; }
  O=$C/ch08r_final; A8=$S/work8/final; rm -rf $O; mkdir -p $O $A8; cp $DL/ch08r/ch08_tower_log.json $O/
  extract $DL/ch08r ch08r_tower_ $O/frames 510 || { echo "STOP: 第8章の塔のコマ"; exit 1; }
  (cd $C && MARU_RES=1080 MARU_SEESAW=$C/seesaw nice -n 5 python3 ch08_game.py $A8 --redo > $A8/game_1080.log 2>&1) || { echo "STOP: 第8章の図"; tail -5 $A8/game_1080.log; exit 1; }
  (cd $C && MARU_STREAM=1 MARU_OUTW=1920 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch08_assemble.py $A8 --tower $O > $A8/assemble.log 2>&1) || { echo "STOP: 第8章の組み立て"; tail -5 $A8/assemble.log; exit 1; }
  [ -f $F/ch08_final_1080.mp4 ] && [ ! -f $F/ch08_final_1080_before_fix1109b.mp4 ] && cp $F/ch08_final_1080.mp4 $F/ch08_final_1080_before_fix1109b.mp4   # 前の本番を残す（一度だけ）
  cp $A8/ch08_animatic.mp4 $F/ch08_final_1080.mp4; rm -rf $O/frames $A8/game
  ffprobe -v error -show_entries stream=width,height:format=duration -of compact $F/ch08_final_1080.mp4
fi
if has sum; then
  echo "== まとめ $(date -u +%T)"; [ -f $DL/sum.ok ] || { echo "STOP: dl_pc/sum.ok がない"; exit 1; }
  O=$S/work_sum/sum_final; rm -rf $O; mkdir -p $O/frames3d
  extract $DL/sum summary_ $O/frames3d 396 || { echo "STOP: まとめのコマ"; exit 1; }
  (cd $C && MARU_OUTW=1920 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 summary_assemble.py $O --frames3d $O/frames3d --log $DL/sum/summary_log.json > $O/assemble.log 2>&1) || { echo "STOP: まとめの組み立て"; tail -5 $O/assemble.log; exit 1; }
  cp $O/summary.mp4 $F/summary_final_1080.mp4; rm -rf $O/frames3d
  ffprobe -v error -show_entries stream=width,height:format=duration -of compact $F/summary_final_1080.mp4
fi
echo "FINALS DONE $(date -u +%T)"
