#!/bin/bash
# 冒頭（網棚のまるロボ）の静止画：まとめの電車の描画（描き足しまで）が終わってから、本番と同じ光（小さめ）で要所を描く
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; H=$S/stage/human; B=$S/blender/blender-4.3.2-linux-x64/blender; O=$S/work_sum/op1
until ! pgrep -f "blender.*summary_seq.py" > /dev/null && grep -q "missing 0\|STOP\|FINISH SUMMARY DONE" $S/work_sum/finish_summary.log 2>/dev/null; do sleep 20; done
while pgrep -f "blender.*summary_seq.py" > /dev/null; do sleep 20; done
mkdir -p $O
# t（秒）→ コマ：K1 0.6/1.9/3.2、K2・K3 4.6/6.6、K4 8.2/9.6/11.2、K5 14.5、K6 19.5、K7 22.6/24.2、K7b 26.5/29.2、K8 30.6/31.9、K9 36、K10 46
FR=$(python3 -c "print(','.join(str(int(round(t*24))+1) for t in (0.6,1.9,3.2,4.6,6.6,8.2,9.6,11.2,14.5,19.5,22.6,24.2,26.5,29.2,30.6,31.9,36.0,46.0)))")
cd $H && nice -n 5 $B -b --factory-startup --python-exit-code 1 --python opening_phys.py -- --seq ch0102_seq.py --crowd 1 --world_len 1450 --acts 1 \
   --engine eevee --samples 8 --res 640 360 --out $O --frames 1:1944 --dry 1 --dry_frames $FR > $O/run.log 2>&1
echo "OP STILLS DONE $(date -u +%T) exit $?"
