#!/bin/bash
# 字幕を新しい決まり（大きく・自然な改行・長い文は声の間で何枚かに。tools/subs_jp.py）にして、第3〜6章の本番（1080p）を組み直す
#   絵（PC の 3D・図）と声はそのまま。前の完成版は *_before_subs.mp4 に残す。順番：第6章 → 第5章 → 第4章 → 第3章
#   使い方: bash resub_3456.sh [6] [5] [4] [3]   （何も書かなければ全部）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; F=$S/stage/final
WANT="${*:-6 5 4 3}"
has() { case " $WANT " in *" $1 "*) return 0;; esac; return 1; }
bk() { [ -f "${1%.mp4}_before_subs.mp4" ] || cp "$1" "${1%.mp4}_before_subs.mp4"; }
if has 6; then
  echo "== 第6章 $(date -u +%T)"; bk $F/ch06_final_1080.mp4
  bash $S/tools/final_ch06.sh || { echo "STOP: 第6章"; exit 1; }
fi
if has 5; then
  echo "== 第5章 $(date -u +%T)"; bk $C/ch5_final/ch05_final_1080.mp4
  O5=$C/ch5_final2; rm -rf $O5/ch05; mkdir -p $O5
  (cd $C && MARU_RES=1080 nice -n 5 python3 ch05_frames_par.py $O5 3 > $O5/frames.log 2>&1) || { echo "STOP: 第5章の図"; tail -5 $O5/frames.log; exit 1; }
  (cd $C && MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 nice -n 5 python3 ch05_assemble.py $O5 > $O5/assemble.log 2>&1) || { echo "STOP: 第5章の組み立て"; tail -5 $O5/assemble.log; exit 1; }
  cp $O5/ch05_v2_voice.mp4 $C/ch5_final/ch05_final_1080.mp4
  ffprobe -v error -show_entries stream=width,height:format=duration -of compact $C/ch5_final/ch05_final_1080.mp4
  rm -rf $O5/ch05
fi
if has 4; then
  echo "== 第4章 $(date -u +%T)"; bk $F/ch04_final_1080.mp4
  bash $S/tools/pc_ingest_ch04.sh || { echo "STOP: 第4章"; exit 1; }
  rm -rf $C/pair_1080/frames
fi
if has 3; then
  echo "== 第3章 $(date -u +%T)"; bk $F/ch03_final_1080.mp4
  (bash $S/tools/pc_ingest_ch03.sh $S/dl_pc/ch03 > $C/anim_1080/resub.log 2>&1) || { echo "STOP: 第3章"; tail -5 $C/anim_1080/resub.log; exit 1; }
  cp $C/anim_1080/ch03_animatic.mp4 $F/ch03_final_1080.mp4
  ffprobe -v error -show_entries stream=width,height:format=duration -of compact $F/ch03_final_1080.mp4
  rm -rf $C/anim_1080/frames $C/anim_1080/full $C/train_1080/frames_train
fi
echo "RESUB DONE $(date -u +%T)"
