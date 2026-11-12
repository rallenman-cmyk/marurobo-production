#!/bin/bash
# 冒頭（まるロボが通路にいる版）の確認用動画：まるロボが映るカット（K1・K3・K4・K7b）だけ簡易描画（workbench・1280×720）で描き、
#   ほかのコマは前の PC の絵（dl_pc/ch0102、字幕なしの元の絵）を 1280×720 にして使う → 声・曲・字幕を付けて組む
#   → review_page/media/ch0102_check_v5.mp4（15MB 以下）と表紙
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; H=$S/stage/human; B=$S/blender/blender-4.3.2-linux-x64/blender
O=$S/work_sum/opwb; M=$S/review_page/media; IMG=$S/review_page/img
mkdir -p $O/frames
for f in $S/dl_pc/ch0102/ch0102_*.mp4; do                              # まず全部のコマを、前の PC の絵で
  b=$(basename "$f" .mp4); r=${b#ch0102_}; a=$((10#${r%-*}))
  nice -n 5 ffmpeg -v error -y -i "$f" -vf scale=1280:720:flags=lanczos -start_number $a $O/frames/f_%04d.png
done
# まるロボが映るカット：K1 0〜3.7 秒、K3・K4 5.9〜12.7 秒、K7b 24.876〜29.878 秒（コマ番号＝秒×24＋1）
FR=$(python3 -c "
r = list(range(1, 90)) + list(range(143, 306)) + list(range(598, 718))
print(','.join(map(str, r)))")
cd $H && MARU_OP_SPOT=aisle nice -n 5 $B -b --factory-startup --python-exit-code 1 --python opening_phys.py -- --seq ch0102_seq.py --crowd 1 --world_len 1450 --acts 1 \
   --engine workbench --res 1280 720 --out $O --frames 1:1944 --dry 1 --dry_frames $FR > $O/run.log 2>&1 || { echo "STOP: render"; tail -20 $O/run.log; exit 1; }
for p in $O/check_*.png; do b=$(basename $p .png); mv $p $O/frames/f_${b#check_}.png; done
n=$(ls $O/frames | wc -l); echo "frames $n / 1944"; [ "$n" -ge 1944 ] || { echo "STOP: frames"; exit 1; }
cd $H && nice -n 5 python3 ch0102_assemble.py $O > $O/assemble.log 2>&1 || { echo "STOP: assemble"; tail -20 $O/assemble.log; exit 1; }
for crf in 23 26 29; do
  nice -n 5 ffmpeg -v error -y -i $O/ch0102_animatic.mp4 -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -c:a aac -b:a 128k $M/ch0102_check_v5.mp4
  sz=$(stat -c %s $M/ch0102_check_v5.mp4); echo "crf $crf size $sz"; [ $sz -le 15000000 ] && break
done
ffmpeg -v error -y -ss 1.9 -i $M/ch0102_check_v5.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_ch0102_check_v5.jpg
ffprobe -v error -show_entries format=duration -of csv=p=0 $M/ch0102_check_v5.mp4
rm -rf $O/frames $O/full
echo "OP PREVIEW DONE $(date -u +%T)"
