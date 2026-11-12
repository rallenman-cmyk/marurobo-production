#!/bin/bash
# 第4章 v8 の仕上げ：3D（2826枚）が描き終わったら → 足りない絵を描き足す → 組み立て → 確認ページ用の mp4（CRF 24）と表紙の絵
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; D=$S/stage/ch03/pair6; C=$S/stage/ch03; NEED=2826
B=$S/blender/blender-4.3.2-linux-x64/blender; SB=$S/handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
# 1) 描き手がいなくなってから：0バイトの置き場所（止まった描き手の残り）を消し、足りない絵をまとめて描く（2回まで）
while [ "$(pgrep -fc 'pair6/helper.sh ')" -gt 0 ]; do sleep 30; done
for pass in 1 2; do
  find $D/frames -name "p_*.png" -size 0 -delete
  runs=$(python3 -c "
import os
D='$D/frames'; miss=[f for f in range(1,$NEED+1) if not os.path.exists('%s/p_%04d.png'%(D,f))]
r=[];a=None
for f in miss:
    if a is None: a=b=f
    elif f==b+1: b=f
    else: r.append((a,b)); a=b=f
if a is not None: r.append((a,b))
print(' '.join('%d:%d'%x for x in r))")
  echo "pass $pass missing runs: ${runs:-none}"
  [ -z "$runs" ] && break
  for r in $runs; do $B -b $SB --python $C/ch04_pairing6.py -- --out $D --engine eevee --res 640 360 --samples 12 --frames $r > $D/fill_$pass.log 2>&1; done
done
# 2) 全部の絵が開けるか
python3 -c "
from PIL import Image; import os
D='$D/frames'; bad=[]
for f in range(1,$NEED+1):
    p='%s/p_%04d.png'%(D,f)
    try: Image.open(p).verify()
    except Exception: bad.append(f)
print('frames ok' if not bad else 'BAD %s'%bad[:20])" | tee $D/verify.txt
grep -q "frames ok" $D/verify.txt || { echo "STOP: bad frames"; exit 1; }
# 3) 組み立て（v8：大きいスマホ・6:24 は ②）
cd $C && python3 ch04_assemble6.py ch04_out --pair=$D --ver=v8 --alt624 > ch04_out/assemble_v8.log 2>&1 || { echo "STOP: assemble failed"; tail -20 ch04_out/assemble_v8.log; exit 1; }
# 4) 確認ページ用（15MB 以下にするため CRF 24）と表紙
O=$C/ch04_out; M=$S/review_page/media
ffmpeg -v error -y -framerate 24 -i $O/full8/f_%04d.png -i $O/ch04_audio8.wav -vf "subtitles=$O/ch04_subs8.ass:fontsdir=$S/stage/av/fonts" \
  -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/ch04_check_v8.mp4
ffmpeg -v error -y -ss 104 -i $M/ch04_check_v8.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $S/review_page/img/poster_ch04_check_v8.jpg
ls -la $M/ch04_check_v8.mp4; ffprobe -v error -show_entries format=duration -of csv=p=0 $M/ch04_check_v8.mp4
echo "FINISH CH04 V8 DONE"
