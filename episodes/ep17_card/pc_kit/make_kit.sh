#!/bin/bash
# PC 用の一式 marurobo_ep17.zip を作る：bash make_kit.sh <出力フォルダ> <作業場所（MARU_WORK。tex17 の絵を取る）>
#   16本目の make_kit.sh を写した。17本目は 6本目（kit・core・plan・pc_out）と 5本目（kit・plan）と 3本目の絵コンテの部品、
#   まるロボの部品（marumotion・maru_real・marurig）、3D の中の絵（stage/tex17 の PNG → anim/tex17）、声の時刻（placement・script・phrase_t）を入れる
#   点検：ps_lint と py_compile を通してから zip にする。控え（*_before_*）と __pycache__ は入れない
#   決まり（SKILL 2026-11-27）：手順（gen_ps1.py）を作ってから、この zip を作る（zip には手順が入る）
set -e
EP=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$EP/../.." && pwd); OUT=$(cd "${1:-.}" && pwd); MW=${2:-$MARU_WORK}
python3 $REPO/skill/marurobo-video-production/scripts/ps_lint.py $EP/pc_kit/run_pc_render_ep17.ps1
for f in scenes kit17 maru17 timing pc_out; do python3 -m py_compile $EP/anim/$f.py; done
for f in scenes kit17 maru17 overlays; do python3 $REPO/skill/marurobo-video-production/scripts/comment_code_check.py $EP/anim/$f.py | tail -1 | grep -q '：0 行' || { echo "説明書きの中に命令が入っています：$f.py"; exit 1; }; done
test -f $MW/stage/tex17/ph_set_on.png || { echo "tex17 の絵がありません：$MW/stage/tex17"; exit 1; }
E6=$REPO/episodes/ep06_haizen/anim; E5=$REPO/episodes/ep05_vacuum/anim
T=$(mktemp -d); K=$T/marurobo_ep17
mkdir -p $K/pc_kit $K/episodes/ep17_card/anim/tex17 $K/episodes/ep17_card/voice $K/episodes/ep06_haizen/anim $K/episodes/ep05_vacuum/anim $K/episodes/ep03_ad/storyboard $K/skill/marurobo-video-production/scripts $K/episodes/ep01_earphone/stage/maru
cp $EP/pc_kit/run_pc_render_ep17.ps1 $EP/pc_kit/README_PC.md $EP/pc_kit/はじめに.txt $K/pc_kit/
cp $EP/pc_kit/はじめに.txt $EP/pc_kit/README_PC.md $K/
for f in scenes kit17 maru17 timing pc_out; do cp $EP/anim/$f.py $K/episodes/ep17_card/anim/; done
cp $EP/anim/clips.json $K/episodes/ep17_card/anim/
cp $MW/stage/tex17/*.png $K/episodes/ep17_card/anim/tex17/
cp $EP/voice/placement.json $EP/voice/script_v1_0.json $EP/voice/phrase_t.json $K/episodes/ep17_card/voice/
cp $E6/kit.py $E6/core.py $E6/plan.py $E6/pc_out.py $K/episodes/ep06_haizen/anim/
cp $E5/kit.py $E5/plan.py $K/episodes/ep05_vacuum/anim/
cp $REPO/episodes/ep03_ad/storyboard/scenes.py $K/episodes/ep03_ad/storyboard/
S=$REPO/skill/marurobo-video-production/scripts
cp $S/maru_real.py $S/marumotion.py $S/maru_sfx.py $K/skill/marurobo-video-production/scripts/
cp $REPO/episodes/ep01_earphone/stage/maru/marurig.py $K/episodes/ep01_earphone/stage/maru/
(cd $T && rm -f "$OUT/marurobo_ep17.zip" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$OUT/marurobo_ep17.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('marurobo_ep17'):
    for f in fs:
        if '__pycache__' in r or '_before_' in f: continue
        z.write(os.path.join(r,f))
z.close()")
rm -rf $T; ls -la $OUT/marurobo_ep17.zip
