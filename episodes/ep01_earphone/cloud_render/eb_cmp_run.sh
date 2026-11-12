#!/bin/bash
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
for V in new old; do
  E=1; [ $V = old ] && E=0
  nice -n 5 ./blender/blender-4.3.2-linux-x64/blender -b --factory-startup handoff/bluetooth_handoff_restored/bt_production_v1/output/story.blend --python stage/ch03/ch03_stage.py -- --out stage/ch03/eb_cmp/$V --still 18.0,38.0,44.0,47.5,49.0 --res 960 540 --samples 24 --eb2 $E --eb_views 1 > stage/ch03/eb_cmp/$V/run.log 2>&1
done
touch stage/ch03/eb_cmp/done
