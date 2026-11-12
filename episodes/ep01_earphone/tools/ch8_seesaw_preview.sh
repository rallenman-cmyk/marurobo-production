#!/bin/bash
# 第8章 v4（確認用）：天びんの 2 か所にまるロボ（ch08_seesaw_render.py の絵）→ その時間の図だけ描き直す → 組み立て（1280×720）→ mp4・表紙
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03; O=$S/work_sum/seesaw_p
A8=$S/work8/asm; AW=$S/work8/asm_wb; W8=$S/work_sum/c8wb; M=$S/review_page/media; IMG=$S/review_page/img
NOTE="確認用・塔の場面は簡易描画（光と色は本番と違います）・まるロボ入り（塔・天びん）"
while pgrep -f ch08_seesaw_render.py > /dev/null; do sleep 20; done
python3 - "$O" <<'PY' || { echo "STOP: seesaw frames"; exit 1; }
import json, os, sys
O = sys.argv[1]; bad = []
for sc in ("A", "B"):
    J = json.load(open(os.path.join(O, "seesaw_%s.json" % sc)))
    miss = [i for i in range(1, J["n"] + 1) if not (os.path.exists(os.path.join(O, sc, "f_%04d.png" % i)) and os.path.getsize(os.path.join(O, sc, "f_%04d.png" % i)) > 0)]
    print(sc, "frames", J["n"] - len(miss), "/", J["n"], "missing", miss[:10]); bad += miss
sys.exit(1 if bad else 0)
PY
# 天びんの二つの時間の図だけ消して、描き直させる（ほかの図はそのまま）
python3 - "$C" "$A8" <<'PY'
import json, os, sys
C, A8 = sys.argv[1], sys.argv[2]; sys.path.insert(0, C)
import ch08_seesaw as ss
G = json.load(open(os.path.join(A8, "ch08_game.json"))); t0, fps = G["t0"], G["fps"]; n = 0
for sc in ("A", "B"):
    a, b = ss.SCN[sc]["t_in"], ss.SCN[sc]["t_out"]
    for i in range(int((a - t0) * fps) - 3, int((b - t0) * fps) + 4):
        fp = os.path.join(A8, "game", "g_%04d.png" % (i + 1))
        if os.path.exists(fp): os.remove(fp); n += 1
print("removed game frames", n)
PY
cd $C && MARU_SEESAW=$O nice -n 5 python3 ch08_game.py $A8 > $A8/game_seesaw.log 2>&1 || { echo "STOP: game"; tail -5 $A8/game_seesaw.log; exit 1; }
cp $A8/ch08_game.json $AW/
cd $C && MARU_OUTW=1280 MARU_NOTE="$NOTE" nice -n 5 python3 ch08_assemble.py $AW --tower $W8 --no_video > $AW/assemble.log 2>&1 || { echo "STOP: assemble"; tail -20 $AW/assemble.log; exit 1; }
for crf in 23 26; do
  nice -n 5 ffmpeg -v error -y -framerate 24 -i $AW/full/f_%04d.png -i $AW/ch08_audio.wav -vf "subtitles=$AW/ch08_subs.ass:fontsdir=$S/stage/av/fonts" \
    -c:v libx264 -crf $crf -preset slow -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 128k -shortest $M/ch08_check_v4.mp4
  sz=$(stat -c %s $M/ch08_check_v4.mp4); echo "crf $crf size $sz"; [ $sz -le 15000000 ] && break
done
ffmpeg -v error -y -ss 101.6 -i $M/ch08_check_v4.mp4 -frames:v 1 -vf scale=960:-2 -q:v 3 $IMG/poster_ch08_check_v4.jpg
rm -rf $AW/full; ffprobe -v error -show_entries format=duration -of csv=p=0 $M/ch08_check_v4.mp4
echo "CH8 SEESAW PREVIEW DONE $(date -u +%T)"
