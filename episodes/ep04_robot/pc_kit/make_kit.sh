#!/bin/bash
# PC 用の一式 marurobo_ep04.zip を作る：bash make_kit.sh <出力フォルダ> <絵のフォルダ（ep04_tex）> <画面のコマのフォルダ（anim/screens.py の出力）>
#   中身：手順（ps1・README・はじめに）、3D の道具（anim の common・clip_anim・scenes・clips.json、look の _head・kit3d・図の場面 9 つ）、
#         絵コンテの舞台（storyboard の board・rich）、3本目の部品（ep03_ad/storyboard の scenes・guards）、声の時刻（voice）、字幕の時刻（animatic/subs_events.json）、
#         絵（tex）とパソコンの画面のコマ（scr）
#   点検（SKILL §8）：ps_lint と py_compile を通してから zip にする。控え（*_before_*）と __pycache__ は入れない
set -e
EP=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$EP/../.." && pwd); OUT=$(cd "${1:-.}" && pwd); TEXD=$2; SCRD=$3
[ -d "$TEXD" ] && [ -d "$SCRD" ] || { echo "使い方：bash make_kit.sh <出力> <ep04_tex> <scr>"; exit 1; }
python3 $EP/pc_kit/make_ps1.py
python3 $REPO/skill/marurobo-video-production/scripts/ps_lint.py $EP/pc_kit/run_pc_render_ep04.ps1
LOOKS="s06 s07 s08x s09 s10 s15 s19 s20 s22"
for f in anim/common anim/clip_anim anim/scenes look/_head look/kit3d storyboard/board storyboard/rich; do python3 -m py_compile $EP/$f.py; done
for n in $LOOKS; do python3 -m py_compile $EP/look/${n}_3d.py; done
T=$(mktemp -d); K=$T/marurobo_ep04; E=$K/episodes/ep04_robot
mkdir -p $K/pc_kit $E/anim $E/look $E/storyboard $E/voice $E/animatic $K/episodes/ep03_ad/storyboard $K/tex $K/scr
cp $EP/pc_kit/run_pc_render_ep04.ps1 $EP/pc_kit/README_PC.md $EP/pc_kit/はじめに.txt $K/pc_kit/
cp $EP/pc_kit/はじめに.txt $EP/pc_kit/README_PC.md $K/
cp $EP/anim/common.py $EP/anim/clip_anim.py $EP/anim/scenes.py $EP/anim/clips.json $E/anim/
cp $EP/look/_head.py $EP/look/kit3d.py $E/look/
for n in $LOOKS; do cp $EP/look/${n}_3d.py $E/look/; done
cp $EP/storyboard/board.py $EP/storyboard/rich.py $E/storyboard/
cp $EP/voice/placement.json $EP/voice/script_v1_0.json $E/voice/
cp $EP/animatic/subs_events.json $E/animatic/
cp $REPO/episodes/ep03_ad/storyboard/scenes.py $REPO/episodes/ep03_ad/storyboard/guards.py $K/episodes/ep03_ad/storyboard/
cp $TEXD/*.png $K/tex/
cp $SCRD/*.png $K/scr/
(cd $T && rm -f "$OUT/marurobo_ep04.zip" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$OUT/marurobo_ep04.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('marurobo_ep04'):
    for f in fs:
        if '__pycache__' in r or '_before_' in f: continue
        z.write(os.path.join(r,f))
z.close()")
rm -rf $T; ls -la $OUT/marurobo_ep04.zip
