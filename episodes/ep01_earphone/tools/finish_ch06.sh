#!/bin/bash
# 第6章の仕上げ：絵（1933枚）が描き終わったら（chain_after_ch6.sh の CH6 FRAMES OK）→ 絵の検査 → 組み立て（1280×720）→ 確認ページ用の mp4（15MB 以下）と表紙
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; O=$C/ch06_out; NEED=1933; M=$S/review_page/media
until grep -q "CH6 FRAMES OK" $C/ch678_workers.log 2>/dev/null; do sleep 30; done
# 1) 全部の絵が開けるか
python3 -c "
from PIL import Image
D='$O/frames'; bad=[]
for f in range(1,$NEED+1):
    p='%s/f_%04d.png'%(D,f)
    try: Image.open(p).verify()
    except Exception: bad.append(f)
print('frames ok' if not bad else 'BAD %s'%bad[:20])" | tee $O/verify.txt
grep -q "frames ok" $O/verify.txt || { echo "STOP: bad frames"; exit 1; }
# 2) 組み立て（札・印は 1280×720 で描く。確認用の場面名・注記は出す）
cd $C && MARU_OUTW=1280 nice -n 5 python3 ch06_assemble.py $O --no_video > $O/assemble.log 2>&1 || { echo "STOP: assemble failed"; tail -20 $O/assemble.log; exit 1; }
# 3) 確認ページ用（15MB 以下）と表紙（返事の光がスマホへ飛んでいるところ）
for crf in 22 25 28; do
  nice -n 5 ffmpeg -v error -y -framerate 24 -i $O/full/f_%04d.png -i $O/ch06_audio.wav -vf "subtitles=$O/ch06_subs.ass:fontsdir=$S/stage/av/fonts" \
    -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/ch06_check_v1.mp4
  sz=$(stat -c %s $M/ch06_check_v1.mp4); echo "crf $crf size $sz"; [ $sz -le 15000000 ] && break
done
TP=$(cd $C && python3 -c "import ch06_plan as p; print('%.2f' % (p.T_REPLY0 + 1.3 - p.T0))")
ffmpeg -v error -y -ss $TP -i $M/ch06_check_v1.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $S/review_page/img/poster_ch06_check_v1.jpg
ls -la $M/ch06_check_v1.mp4 $S/review_page/img/poster_ch06_check_v1.jpg; ffprobe -v error -show_entries format=duration -of csv=p=0 $M/ch06_check_v1.mp4
echo "FINISH CH06 DONE"
