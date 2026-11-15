#!/bin/bash
# PC 用の一式 marurobo_ep05.zip を作る：bash make_kit.sh <出力フォルダ>
#   中身：手順（ps1・README・はじめに）、3D の道具（anim の scenes.py・kit.py・core.py・plan.py・pc_out.py）、
#         3本目の部品（ep03_ad/storyboard/scenes.py：まるロボ・材質・光）、声の時刻（voice）、スマホの地図の絵（tex：map_tex.py で作る）
#   点検（SKILL §8）：ps_lint と py_compile を通してから zip にする。控え（*_before_*）と __pycache__ は入れない
set -e
EP=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$EP/../.." && pwd); OUT=${1:-.}
python3 $REPO/skill/marurobo-video-production/scripts/ps_lint.py $EP/pc_kit/run_pc_render_ep05.ps1
for f in scenes kit core plan pc_out map_tex; do python3 -m py_compile $EP/anim/$f.py; done
T=$(mktemp -d); K=$T/marurobo_ep05
mkdir -p $K/pc_kit $K/episodes/ep05_vacuum/anim $K/episodes/ep05_vacuum/voice $K/episodes/ep03_ad/storyboard $K/tex
cp $EP/pc_kit/run_pc_render_ep05.ps1 $EP/pc_kit/README_PC.md $EP/pc_kit/はじめに.txt $K/pc_kit/
cp $EP/pc_kit/はじめに.txt $EP/pc_kit/README_PC.md $K/
cp $EP/anim/scenes.py $EP/anim/kit.py $EP/anim/core.py $EP/anim/plan.py $EP/anim/pc_out.py $EP/anim/clips.json $K/episodes/ep05_vacuum/anim/
cp $EP/voice/placement.json $EP/voice/script_v1_0.json $K/episodes/ep05_vacuum/voice/
cp $REPO/episodes/ep03_ad/storyboard/scenes.py $K/episodes/ep03_ad/storyboard/
python3 $EP/anim/map_tex.py $K/tex > /dev/null
(cd $T && rm -f "$OUT/marurobo_ep05.zip" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$OUT/marurobo_ep05.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('marurobo_ep05'):
    for f in fs:
        if '__pycache__' in r or '_before_' in f: continue
        z.write(os.path.join(r,f))
z.close()")
rm -rf $T; ls -la $OUT/marurobo_ep05.zip
