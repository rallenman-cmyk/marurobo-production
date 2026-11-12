#!/bin/bash
# まとめの確認用：電車の場面（こちらで描く 960×540）が描き終わったら → 抜けたコマを描き足す → 組み立て（1280×720）→ 確認ページ用の mp4 と表紙
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; R=$S/work_sum/r540; FR=$R/frames; O=$S/work_sum/sum_check; M=$S/review_page/media
B=$S/blender/blender-4.3.2-linux-x64/blender
while [ "$(pgrep -fc 'blender.*summary_seq.py')" -gt 0 ]; do sleep 30; done
for pass in 1 2; do
  find $FR -name 'f_*.png' -size -1k -delete                                   # 止めた描き手の置き札（0 バイト）を消して、描き足す
  miss=$(python3 -c "
import os
print(sum(1 for f in range(1945, 2341) if not (os.path.exists('$FR/f_%04d.png' % f) and os.path.getsize('$FR/f_%04d.png' % f) > 1000)))")
  echo "pass $pass missing $miss"; [ "$miss" -eq 0 ] && break
  (cd $S/stage/human && $B -b --factory-startup --python-exit-code 1 --python opening_phys.py -- --seq summary_seq.py --crowd 1 --world_len 1450 --acts 1 \
     --engine eevee --samples 16 --res 960 540 --out $R --frames 1945:2340 > $R/fill$pass.log 2>&1)
done
mkdir -p $O && cd $C && MARU_OUTW=1280 MARU_CRF=21 nice -n 5 python3 summary_assemble.py $O --frames3d $FR --log $R/summary_log.json > $O/assemble.log 2>&1 || { echo "STOP: assemble failed"; tail -20 $O/assemble.log; exit 1; }
cp $O/summary.mp4 $M/summary_check_v1.mp4
ffmpeg -v error -y -ss 46.0 -i $M/summary_check_v1.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $S/review_page/img/poster_summary_check_v1.jpg
ls -la $M/summary_check_v1.mp4; ffprobe -v error -show_entries format=duration -of csv=p=0 $M/summary_check_v1.mp4
echo "FINISH SUMMARY DONE"
