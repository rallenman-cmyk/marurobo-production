#!/bin/bash
# 2026-11-09 夜（25か所の直し）の残り：第8章が終わったら まとめ → 第4章が終わったら 第3章 → 全部そろったら 字幕の点検の一覧 → 通し → 点検
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; F=$S/stage/final; WF=$S/work_fix1109b; WS=$S/work_subs
waitfor() { while ! grep -q "$2" "$1" 2>/dev/null; do grep -q "STOP" "$1" 2>/dev/null && { echo "STOP in $1"; tail -3 "$1"; exit 1; }; sleep 30; done; }
waitfor $WF/finals78.log "FINALS DONE"; echo "$(date -u +%T) 第8章できた → まとめ"
bash $S/tools/finals_78s.sh sum > $WF/finals_sum.log 2>&1; grep -q "FINALS DONE" $WF/finals_sum.log || { echo "STOP: まとめ"; tail -3 $WF/finals_sum.log; exit 1; }
waitfor $WF/build_ch04.log "CH04 DONE"; echo "$(date -u +%T) 第4章できた → 3D のコマを消して 第3章"
rm -rf "$C/pair_1080/frames"
[ -f $F/ch03_final_1080_before_fix1109b.mp4 ] || cp $F/ch03_final_1080.mp4 $F/ch03_final_1080_before_fix1109b.mp4
(bash $S/tools/pc_ingest_ch03.sh $S/dl_pc/ch03 > $C/anim_1080/fix1109b.log 2>&1) || { echo "STOP: 第3章"; tail -5 $C/anim_1080/fix1109b.log; exit 1; }
cp $C/anim_1080/ch03_animatic.mp4 $F/ch03_final_1080.mp4; rm -rf "$C/anim_1080/frames" "$C/anim_1080/full" "$C/train_1080/frames_train"
echo "$(date -u +%T) 第3章できた"
waitfor $WF/build_ch06.log "FINAL CH06 DONE"; echo "$(date -u +%T) 第6章できた"
cd $S/tools
python3 subs_check.py $F/ch03_final_1080.mp4 $C/anim_1080/ch03_subs.ass $WS/chk3_ch03
python3 subs_check.py $F/ch04_final_1080.mp4 $C/ch04_out_1080/ch04_subs8.ass $WS/chk3_ch04
python3 subs_check.py $C/ch5_final/ch05_final_1080.mp4 $C/ch5_final3/ch05_subs.ass $WS/chk3_ch05
python3 subs_check.py $F/ch06_final_1080.mp4 $C/ch06_final/ch06_subs.ass $WS/chk3_ch06
python3 subs_check.py $F/ch07_final_1080.mp4 $C/ch07r_final/ch07_subs.ass $WS/chk3_ch07
python3 subs_check.py $F/ch08_final_1080.mp4 $S/work8/final/ch08_subs.ass $WS/chk3_ch08
python3 subs_check.py $F/summary_final_1080.mp4 $S/work_sum/sum_final/summary_subs.ass $WS/chk3_sum
echo "SUBS CHECK SHEETS DONE $(date -u +%T)"
[ -f $F/bluetooth_full_1080_v1.mp4 ] || cp $F/bluetooth_full_1080.mp4 $F/bluetooth_full_1080_v1.mp4
bash $S/tools/concat_full.sh || { echo "STOP: 通し"; exit 1; }
bash $S/tools/final_qa.sh
echo "CHAIN DONE $(date -u +%T)"
