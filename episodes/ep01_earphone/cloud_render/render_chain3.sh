#!/bin/bash
# ① 冒頭（物理版）の足りないコマ（50〜176）を2つで描く→動画　② 見本リール本編の続き→動画　③ 追加の見本→動画
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=./blender/blender-4.3.2-linux-x64/blender; SB=handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
rm -f opening_phys.done reel_main.done reel_extra.done
for r in "50:113" "114:176"; do a=${r%%:*}; nice -n 3 $B -b --factory-startup --python stage/human/opening_phys.py -- --out stage/human/op_phys --res 640 360 --samples 8 --frames $r > stage/human/op_phys_fix_$a.log 2>&1 & done
wait
echo "opening frames: $(ls stage/human/op_phys/frames | wc -l)" > opening_phys.log; grep -l Traceback stage/human/op_phys_fix_*.log >> opening_phys.log 2>&1
bash stage/human/assemble_opening_phys.sh >> opening_phys.log 2>&1
ffprobe -v error -show_entries format=duration -of csv=p=0 stage/human/av/opening_phys.mp4 >> opening_phys.log 2>&1
cp opening_phys.log opening_phys.done
# 本編の続き：前半（〜904）と後半（905〜）の、まだないコマから
R=$(python3 - <<'PY'
import os
fr = set(int(f[2:6]) for f in os.listdir("maru_reel_out/frames") if f.startswith("f_"))
a = next((f for f in range(1, 905) if f not in fr), 905); b = next((f for f in range(905, 1808) if f not in fr), 1808)
print(("%d:904" % a if a <= 904 else "") + " " + ("%d:1807" % b if b <= 1807 else ""))
PY
)
for r in $R; do a=${r%%:*}; nice -n 5 $B -b $SB --python stage/maru/maru_reel.py -- --out maru_reel_out --frames $r --samples 10 > maru_reel_out/render_resume2_$a.log 2>&1 & done
wait
echo "main frames: $(ls maru_reel_out/frames | wc -l)" > reel_main.log; grep -l Traceback maru_reel_out/render_resume2_*.log >> reel_main.log 2>&1
python3 stage/maru/maru_reel_assemble.py maru_reel_out >> reel_main.log 2>&1
cp reel_main.log reel_main.done
mkdir -p maru_reel_extra_out/frames
for r in "1:306" "307:9999"; do a=${r%%:*}; nice -n 5 $B -b $SB --python stage/maru/maru_reel.py -- --plan extra --out maru_reel_extra_out --frames $r --samples 10 > maru_reel_extra_out/render_$a.log 2>&1 & done
wait
echo "extra frames: $(ls maru_reel_extra_out/frames | wc -l)" > reel_extra.log; grep -l Traceback maru_reel_extra_out/render_*.log >> reel_extra.log 2>&1
python3 stage/maru/maru_reel_assemble.py maru_reel_extra_out >> reel_extra.log 2>&1
cp reel_extra.log reel_extra.done
