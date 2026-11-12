#!/bin/bash
# ① 冒頭（物理版）の 206〜528 コマを、直した手で描き直す→動画　② 追加の見本の続き→動画
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=./blender/blender-4.3.2-linux-x64/blender; SB=handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
rm -f opening_phys.done reel_extra.done
render_op() { for r in "$@"; do a=${r%%:*}; nice -n 3 $B -b --factory-startup --python stage/human/opening_phys.py -- --out stage/human/op_phys --res 640 360 --samples 8 --frames $r > stage/human/op_phys_hand_$a.log 2>&1 & done; wait; }
render_op "206:367" "368:528"
# 壊れたコマ（途中で止まった印のファイル）があれば消して描き直す
for k in 1 2; do
  BAD=$(python3 - <<'PY'
import glob, os
from PIL import Image
bad = []
for f in range(1, 529):
    p = "stage/human/op_phys/frames/f_%04d.png" % f
    try: Image.open(p).verify()
    except Exception: bad.append(f)
print(" ".join("%d:%d" % (f, f) for f in bad))
PY
)
  [ -z "$BAD" ] && break
  for r in $BAD; do rm -f stage/human/op_phys/frames/f_$(printf %04d ${r%%:*}).png; done
  render_op $BAD
done
echo "opening frames: $(ls stage/human/op_phys/frames | wc -l)" > opening_phys.log; grep -l Traceback stage/human/op_phys_hand_*.log >> opening_phys.log 2>&1
bash stage/human/assemble_opening_phys.sh >> opening_phys.log 2>&1
ffprobe -v error -show_entries format=duration -of csv=p=0 stage/human/av/opening_phys.mp4 >> opening_phys.log 2>&1
cp opening_phys.log opening_phys.done
R=$(python3 - <<'PY'
import os
fr = set(int(f[2:6]) for f in os.listdir("maru_reel_extra_out/frames") if f.startswith("f_"))
a = next((f for f in range(1, 307) if f not in fr), 307); b = next((f for f in range(307, 613) if f not in fr), 613)
print(("%d:306" % a if a <= 306 else "") + " " + ("%d:9999" % b if b <= 612 else ""))
PY
)
for r in $R; do a=${r%%:*}; nice -n 5 $B -b $SB --python stage/maru/maru_reel.py -- --plan extra --out maru_reel_extra_out --frames $r --samples 10 > maru_reel_extra_out/render_resume_$a.log 2>&1 & done
wait
echo "extra frames: $(ls maru_reel_extra_out/frames | wc -l)" > reel_extra.log; grep -l Traceback maru_reel_extra_out/render_resume_*.log >> reel_extra.log 2>&1
python3 stage/maru/maru_reel_assemble.py maru_reel_extra_out >> reel_extra.log 2>&1
cp reel_extra.log reel_extra.done
