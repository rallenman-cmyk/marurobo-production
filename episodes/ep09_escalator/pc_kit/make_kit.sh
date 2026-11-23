#!/bin/bash
# PC 用の一式 marurobo_ep09.zip を作る：bash make_kit.sh <出力フォルダ>
#   7本目の make_kit.sh と同じ作り。9本目は 6本目の部品（ep06_haizen/anim の kit・core・plan・pc_out）と、3本目のまるロボ・材質の部品を読みこむので、それも入れる
#   9本目は 3D の中に字がないので、フォントは要らない
#   点検：ps_lint と py_compile を通してから zip にする。控え（*_before_*）と __pycache__ は入れない
set -e
EP=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$EP/../.." && pwd); OUT=$(cd "${1:-.}" && pwd)
python3 $REPO/skill/marurobo-video-production/scripts/ps_lint.py $EP/pc_kit/run_pc_render_ep09.ps1
for f in scenes kit9 maru9 esc_geom timing; do python3 -m py_compile $EP/anim/$f.py; done
E6=$REPO/episodes/ep06_haizen/anim
T=$(mktemp -d); K=$T/marurobo_ep09
mkdir -p $K/pc_kit $K/episodes/ep09_escalator/anim $K/episodes/ep09_escalator/voice $K/episodes/ep06_haizen/anim $K/episodes/ep03_ad/storyboard $K/skill/marurobo-video-production/scripts $K/episodes/ep01_earphone/stage/maru
cp $EP/pc_kit/run_pc_render_ep09.ps1 $EP/pc_kit/README_PC.md $EP/pc_kit/はじめに.txt $K/pc_kit/
cp $EP/pc_kit/はじめに.txt $EP/pc_kit/README_PC.md $K/
cp $EP/anim/scenes.py $EP/anim/kit9.py $EP/anim/maru9.py $EP/anim/esc_geom.py $EP/anim/timing.py $EP/anim/pc_out.py $EP/anim/clips.json $K/episodes/ep09_escalator/anim/
cp $EP/voice/placement.json $EP/voice/script_v1_0.json $K/episodes/ep09_escalator/voice/
cp $E6/kit.py $E6/core.py $E6/plan.py $E6/pc_out.py $K/episodes/ep06_haizen/anim/
cp $REPO/episodes/ep03_ad/storyboard/scenes.py $K/episodes/ep03_ad/storyboard/
S=$REPO/skill/marurobo-video-production/scripts
cp $S/maru_real.py $S/marumotion.py $S/maru_sfx.py $K/skill/marurobo-video-production/scripts/
cp $REPO/episodes/ep01_earphone/stage/maru/marurig.py $K/episodes/ep01_earphone/stage/maru/
(cd $T && rm -f "$OUT/marurobo_ep09.zip" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$OUT/marurobo_ep09.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('marurobo_ep09'):
    for f in fs:
        if '__pycache__' in r or '_before_' in f: continue
        z.write(os.path.join(r,f))
z.close()")
rm -rf $T; ls -la $OUT/marurobo_ep09.zip
