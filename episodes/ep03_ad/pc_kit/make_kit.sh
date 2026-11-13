#!/bin/bash
# PC 用の一式 marurobo_ep03.zip を作る：bash make_kit.sh <出力フォルダ>
set -e
EP=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$EP/../.." && pwd); OUT=${1:-.}
T=$(mktemp -d); K=$T/marurobo_ep03
mkdir -p $K/pc_kit $K/episodes/ep03_ad/anim $K/episodes/ep03_ad/storyboard $K/episodes/ep03_ad/voice $K/episodes/ep01_earphone/stage/human
cp $EP/pc_kit/run_pc_render_ep03.ps1 $EP/pc_kit/README_PC.md $K/pc_kit/
cp $EP/pc_kit/README_PC.md $K/
cp $EP/anim/common.py $EP/anim/scenes_all.py $EP/anim/s07s08_gate.py $EP/anim/pc_out.py $K/episodes/ep03_ad/anim/
cp $EP/storyboard/*.py $EP/storyboard/*.png $K/episodes/ep03_ad/storyboard/
cp $EP/voice/placement.json $EP/voice/script_v1_0.json $K/episodes/ep03_ad/voice/
cp $REPO/episodes/ep01_earphone/stage/human/{iconfig,hgen,hbuild,sdf}.py $K/episodes/ep01_earphone/stage/human/
(cd $T && rm -f "$OUT/marurobo_ep03.zip" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$OUT/marurobo_ep03.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('marurobo_ep03'):
    for f in fs: z.write(os.path.join(r,f))
z.close()")
rm -rf $T; ls -la $OUT/marurobo_ep03.zip
