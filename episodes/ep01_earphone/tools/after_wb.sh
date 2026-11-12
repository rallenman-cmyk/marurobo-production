#!/bin/bash
# 第7章・第8章（まるロボ入り）の確認用：簡易描画（workbench・TEXTURE）が描き終わったら
#   → まとめの描き手2を立て直す（メモリが空いたので）→ 第7章・第8章を組む（1280×720）→ 確認ページ用 mp4（15MB 以下）・表紙
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; M=$S/review_page/media; IMG=$S/review_page/img
B=$S/blender/blender-4.3.2-linux-x64/blender; W7=$S/work_sum/c7wb; W8=$S/work_sum/c8wb; R=$S/work_sum/r540
NOTE="確認用・簡易描画（光と色は本番と違います）・まるロボ入り"
while pgrep -f "ch07_stage.py" > /dev/null; do sleep 30; done
verify() {  # verify DIR N
python3 -c "
from PIL import Image
D='$1/frames'; bad=[]
for f in range(1,$2+1):
    p='%s/f_%04d.png'%(D,f)
    try: Image.open(p).verify()
    except Exception: bad.append(f)
print('frames ok' if not bad else 'BAD %d %s'%(len(bad),bad[:20]))"; }
page() {  # page OUTDIR NAME AUDIO SUBS POSTER_T
  for crf in 23 26 29; do
    nice -n 5 ffmpeg -v error -y -framerate 24 -i $1/full/f_%04d.png -i $3 -vf "subtitles=$4:fontsdir=$S/stage/av/fonts" \
      -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/$2.mp4
    sz=$(stat -c %s $M/$2.mp4); echo "$2 crf $crf size $sz"; [ $sz -le 15000000 ] && break
  done
  ffmpeg -v error -y -ss $5 -i $M/$2.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_$2.jpg
  ls -la $M/$2.mp4 $IMG/poster_$2.jpg; ffprobe -v error -show_entries format=duration -of csv=p=0 $M/$2.mp4
}
# 第7章：後半（2430〜）を新しい動きで描き直したので、途中で止めた描き手の置き札（0 バイト）を消し、抜けたコマを描き足す
find $W7/frames -name 'f_*.png' -size 0 -print -delete
miss=$(python3 -c "
import os
print(sum(1 for f in range(1, 3459) if not os.path.exists('$W7/frames/f_%04d.png' % f)))")
echo "ch7 missing $miss"
if [ "$miss" -gt 0 ]; then
  (cd $C && nice -n 5 $B -b $S/handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend --python-exit-code 1 --python ch07_stage.py -- \
     --out $W7 --engine workbench --wb_color TEXTURE --res 640 360 --frames 1:3458 > $W7/fill.log 2>&1)
fi
v7=$(verify $W7 3458); v8=$(verify $W8 510); echo "ch7: $v7 / ch8: $v8"
# まとめの描き手2：死んだ描き手の置き札（10 分より古い 0 バイト）を消してから
if [ "$(pgrep -fc 'blender.*summary_seq.py')" -lt 2 ]; then
  find $R/frames -name 'f_*.png' -size 0 -mmin +10 -print -delete
  (cd $S/stage/human && nohup $B -b --factory-startup --python-exit-code 1 --python opening_phys.py -- --seq summary_seq.py --crowd 1 --world_len 1450 --acts 1 \
     --engine eevee --samples 16 --res 960 540 --out $R --frames 1945:2340 > $R/worker2b.log 2>&1 &)
  echo "summary worker2 restarted $(date -u +%T)"
fi
# 第7章
if [ "$v7" = "frames ok" ]; then
  A7=$S/work_sum/c7wb_asm; mkdir -p $A7; cp $W7/ch07_log.json $A7/
  cd $C && MARU_OUTW=1280 MARU_NOTE="$NOTE" nice -n 5 python3 ch07_assemble.py $A7 --frames $W7/frames --no_video > $A7/assemble.log 2>&1 \
    && page $A7 ch07_check_v2 $A7/ch07_audio.wav $A7/ch07_subs.ass 63.1 && rm -rf $A7/full && echo "CH07 PREVIEW DONE" || { echo "STOP: ch7 assemble failed"; tail -20 $A7/assemble.log; }
fi
# 第8章（2D の図は第2版のものを使う）
if [ "$v8" = "frames ok" ]; then
  A8=$S/work8/asm_wb; mkdir -p $A8; ln -sfn $S/work8/asm/game $A8/game; cp $S/work8/asm/ch08_game.json $A8/
  cd $C && MARU_OUTW=1280 MARU_NOTE="$NOTE" nice -n 5 python3 ch08_assemble.py $A8 --tower $W8 --no_video > $A8/assemble.log 2>&1 \
    && page $A8 ch08_check_v3 $A8/ch08_audio.wav $A8/ch08_subs.ass 12.0 && rm -rf $A8/full && echo "CH08 PREVIEW DONE" || { echo "STOP: ch8 assemble failed"; tail -20 $A8/assemble.log; }
fi
echo "AFTER WB DONE $(date -u +%T)"
