#!/bin/bash
# PC 用の一式 marurobo_ep16.zip を作る：bash make_kit.sh <出力フォルダ> <作業場所（MARU_WORK。tex16 の絵を取る）>
#   9本目の make_kit.sh と同じ作り。16本目は 6本目（kit・core・plan・pc_out）と 5本目（kit・plan）と 3本目の絵コンテの部品、
#   まるロボの部品（marumotion・maru_real・marurig）、3D の中の絵（stage/tex16 の PNG → anim/tex16）を入れる
#   点検：ps_lint と py_compile を通してから zip にする。控え（*_before_*）と __pycache__ は入れない
set -e
EP=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$EP/../.." && pwd); OUT=$(cd "${1:-.}" && pwd); MW=${2:-$MARU_WORK}
python3 $REPO/skill/marurobo-video-production/scripts/ps_lint.py $EP/pc_kit/run_pc_render_ep16.ps1
python3 $EP/anim/collide_check.py | tail -1 | grep -q '：0$' || { python3 $EP/anim/collide_check.py; echo "章のファイルが前の部品の名前を上書きしています（直してから作る）"; exit 1; }      # 16本目 8章の前：6章の DOOR_Y が 1章の裏口を上書きしていた
SCN=$(cd $EP/anim && ls scenes_ch*.py | sed 's/\.py$//' | tr '\n' ' ')      # 章を足したら自動で入る（5章を作ったとき scenes_ch5.py が入っていなかった）
for f in scenes $SCN kit16 kit16b kit16c maru16 timing; do python3 -m py_compile $EP/anim/$f.py; done
test -f $MW/stage/tex16/pricetag.png || { echo "tex16 の絵がありません：$MW/stage/tex16"; exit 1; }
E6=$REPO/episodes/ep06_haizen/anim; E5=$REPO/episodes/ep05_vacuum/anim
T=$(mktemp -d); K=$T/marurobo_ep16
mkdir -p $K/pc_kit $K/episodes/ep16_leak/anim/tex16 $K/episodes/ep16_leak/voice $K/episodes/ep06_haizen/anim $K/episodes/ep05_vacuum/anim $K/episodes/ep03_ad/storyboard $K/skill/marurobo-video-production/scripts $K/episodes/ep01_earphone/stage/maru
cp $EP/pc_kit/run_pc_render_ep16.ps1 $EP/pc_kit/README_PC.md $EP/pc_kit/はじめに.txt $K/pc_kit/
cp $EP/pc_kit/はじめに.txt $EP/pc_kit/README_PC.md $K/
for f in scenes $SCN kit16 kit16b kit16c maru16 timing pc_out; do cp $EP/anim/$f.py $K/episodes/ep16_leak/anim/; done
cp $EP/anim/clips.json $EP/anim/word_times_ch2.json $K/episodes/ep16_leak/anim/
cp $MW/stage/tex16/*.png $K/episodes/ep16_leak/anim/tex16/
cp $EP/voice/placement.json $EP/voice/script_v1_0.json $K/episodes/ep16_leak/voice/
cp $E6/kit.py $E6/core.py $E6/plan.py $E6/pc_out.py $K/episodes/ep06_haizen/anim/
cp $E5/kit.py $E5/plan.py $K/episodes/ep05_vacuum/anim/
cp $REPO/episodes/ep03_ad/storyboard/scenes.py $K/episodes/ep03_ad/storyboard/
S=$REPO/skill/marurobo-video-production/scripts
cp $S/maru_real.py $S/marumotion.py $S/maru_sfx.py $K/skill/marurobo-video-production/scripts/
cp $REPO/episodes/ep01_earphone/stage/maru/marurig.py $K/episodes/ep01_earphone/stage/maru/
(cd $T && rm -f "$OUT/marurobo_ep16.zip" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$OUT/marurobo_ep16.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('marurobo_ep16'):
    for f in fs:
        if '__pycache__' in r or '_before_' in f: continue
        z.write(os.path.join(r,f))
z.close()")
rm -rf $T; ls -la $OUT/marurobo_ep16.zip
