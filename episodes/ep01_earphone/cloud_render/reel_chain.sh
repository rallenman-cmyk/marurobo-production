#!/bin/bash
# 本編の描画が終わるのを待つ → 本編を動画に → 追加の動きを描く → 動画に。終わったら reel_chain.done に結果を書く
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=./blender/blender-4.3.2-linux-x64/blender; SB=handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend
rm -f reel_chain.done
while [ $(ps aux | grep -c "[m]aru_reel.py -- --out maru_reel_out") -gt 0 ]; do sleep 30; done
echo "main frames: $(ls maru_reel_out/frames | wc -l)" > reel_chain.log
grep -l Traceback maru_reel_out/render_*.log >> reel_chain.log 2>&1
python3 stage/maru/maru_reel_assemble.py maru_reel_out >> reel_chain.log 2>&1
mkdir -p maru_reel_extra_out/frames
for r in "1:306" "307:9999"; do a=${r%%:*}; nice -n 5 $B -b $SB --python stage/maru/maru_reel.py -- --plan extra --out maru_reel_extra_out --frames $r --samples 10 > maru_reel_extra_out/render_$a.log 2>&1 & done
wait
echo "extra frames: $(ls maru_reel_extra_out/frames | wc -l)" >> reel_chain.log
grep -l Traceback maru_reel_extra_out/render_*.log >> reel_chain.log 2>&1
python3 stage/maru/maru_reel_assemble.py maru_reel_extra_out >> reel_chain.log 2>&1
cp reel_chain.log reel_chain.done
