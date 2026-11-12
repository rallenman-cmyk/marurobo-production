#!/bin/bash
# 第4〜6章：字幕と同じ文の札を消した版で組み直す（11月9日「どっちもおけ」）。PC の 3D の絵と声はそのまま、札だけ変わる
#   前の完成版は *_before_notext.mp4 として残す。順番：第6章 → 第5章 → 第4章（軽い順）
#   使い方: bash renotext_456.sh [6] [5] [4]   （何も書かなければ全部）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; F=$S/stage/final
WANT="${*:-6 5 4}"
has() { case " $WANT " in *" $1 "*) return 0;; esac; return 1; }
if has 6; then
  echo "== 第6章 $(date -u +%T)"
  [ -f $F/ch06_final_1080_before_notext.mp4 ] || cp $F/ch06_final_1080.mp4 $F/ch06_final_1080_before_notext.mp4
  bash $S/tools/final_ch06.sh || { echo "STOP: 第6章"; exit 1; }
fi
if has 5; then
  echo "== 第5章 $(date -u +%T)"
  [ -f $C/ch5_final/ch05_final_1080_before_notext.mp4 ] || cp $C/ch5_final/ch05_final_1080.mp4 $C/ch5_final/ch05_final_1080_before_notext.mp4
  O5=$C/ch5_final2; rm -rf $O5/ch05; mkdir -p $O5
  (cd $C && MARU_RES=1080 nice -n 5 python3 ch05_frames_par.py $O5 3 > $O5/frames.log 2>&1) || { echo "STOP: 第5章の図"; tail -5 $O5/frames.log; exit 1; }
  (cd $C && MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch05_assemble.py $O5 > $O5/assemble.log 2>&1) || { echo "STOP: 第5章の組み立て"; tail -5 $O5/assemble.log; exit 1; }
  cp $O5/ch05_v2_voice.mp4 $C/ch5_final/ch05_final_1080.mp4
  ffprobe -v error -show_entries stream=width,height:format=duration -of compact $C/ch5_final/ch05_final_1080.mp4
  rm -rf $O5/ch05
fi
if has 4; then
  echo "== 第4章 $(date -u +%T)"
  [ -f $F/ch04_final_1080_before_notext.mp4 ] || cp $F/ch04_final_1080.mp4 $F/ch04_final_1080_before_notext.mp4
  O=$C/ch04_out_1080; rm -rf $O/diagram6_before_notext; [ -d $O/diagram6 ] && mv $O/diagram6 $O/diagram6_before_notext   # 図を描き直させる（できているコマは飛ばすため）
  bash $S/tools/pc_ingest_ch04.sh || { echo "STOP: 第4章"; exit 1; }
  rm -rf $C/pair_1080/frames $O/diagram6_before_notext
fi
echo "RENOTEXT DONE $(date -u +%T)"
