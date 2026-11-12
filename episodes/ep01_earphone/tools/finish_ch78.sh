#!/bin/bash
# 第7章・第8章の仕上げ：塔の絵（第7章 3458・第8章 510）が描き終わったら（chain_after_ch6.sh の CH78 FRAMES）
#   → 絵の検査 → 第7章の組み立て（1280×720）→ 確認ページ用 mp4・表紙 → 第8章の図を 1280×720 で描き直し → 第8章の組み立て → mp4・表紙
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; M=$S/review_page/media; IMG=$S/review_page/img
until grep -q "CH78 FRAMES" $C/ch678_workers.log 2>/dev/null; do sleep 60; done
verify() {  # verify DIR N
python3 -c "
from PIL import Image
D='$1/frames'; bad=[]
for f in range(1,$2+1):
    p='%s/f_%04d.png'%(D,f)
    try: Image.open(p).verify()
    except Exception: bad.append(f)
print('frames ok' if not bad else 'BAD %s'%bad[:20])"; }
page() {  # page OUTDIR NAME AUDIO SUBS POSTER_T
  for crf in 23 26 29; do
    nice -n 5 ffmpeg -v error -y -framerate 24 -i $1/full/f_%04d.png -i $3 -vf "subtitles=$4:fontsdir=$S/stage/av/fonts" \
      -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/$2.mp4
    sz=$(stat -c %s $M/$2.mp4); echo "$2 crf $crf size $sz"; [ $sz -le 15000000 ] && break
  done
  ffmpeg -v error -y -ss $5 -i $M/$2.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_$2.jpg
  ls -la $M/$2.mp4 $IMG/poster_$2.jpg; ffprobe -v error -show_entries format=duration -of csv=p=0 $M/$2.mp4
}
# 第7章
O7=$C/ch07_out; verify $O7 3458 | tee $O7/verify.txt; grep -q "frames ok" $O7/verify.txt || { echo "STOP: ch7 bad frames"; exit 1; }
cd $C && MARU_OUTW=1280 nice -n 5 python3 ch07_assemble.py $O7 --no_video > $O7/assemble.log 2>&1 || { echo "STOP: ch7 assemble failed"; tail -20 $O7/assemble.log; exit 1; }
page $O7 ch07_check_v1 $O7/ch07_audio.wav $O7/ch07_subs.ass 62.5
echo "FINISH CH07 DONE"
# 第8章（図は 1280×720 で描き直してから）
O8=$C/ch08_tower_out; A8=$S/work8/asm; verify $O8 510 | tee $O8/verify.txt; grep -q "frames ok" $O8/verify.txt || { echo "STOP: ch8 bad frames"; exit 1; }
cd $C && nice -n 5 python3 ch08_game.py $A8 --redo > $A8/game_1280.log 2>&1 || { echo "STOP: ch8 game failed"; tail -20 $A8/game_1280.log; exit 1; }
cd $C && MARU_OUTW=1280 nice -n 5 python3 ch08_assemble.py $A8 --tower $O8 --no_video > $A8/assemble.log 2>&1 || { echo "STOP: ch8 assemble failed"; tail -20 $A8/assemble.log; exit 1; }
page $A8 ch08_check_v1 $A8/ch08_audio.wav $A8/ch08_subs.ass 66.0
echo "FINISH CH78 DONE"
