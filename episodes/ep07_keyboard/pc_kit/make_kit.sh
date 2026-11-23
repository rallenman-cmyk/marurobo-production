#!/bin/bash
# PC 用の一式 marurobo_ep07.zip を作る：KEY_FONT=<NotoSansJP_700Bold.ttf> bash make_kit.sh <出力フォルダ>
#   6本目の make_kit.sh と同じ作り。7本目は 6本目の部品（ep06_haizen/anim の kit・core・plan）を読みこむので、それも入れる
#   キーの字のフォント（KEY_FONT。いろは歌の「い ろ は」もある日本語の字）を anim/fonts に入れる（大きいのでリポジトリには入れない）
#   点検：ps_lint と py_compile を通してから zip にする。控え（*_before_*）と __pycache__ は入れない
set -e
EP=$(cd "$(dirname "$0")/.." && pwd); REPO=$(cd "$EP/../.." && pwd); OUT=${1:-.}
[ -f "$KEY_FONT" ] || { echo "KEY_FONT（NotoSansJP_700Bold.ttf）がない"; exit 1; }
python3 $REPO/skill/marurobo-video-production/scripts/ps_lint.py $EP/pc_kit/run_pc_render_ep07.ps1
for f in scenes kit maru7 timing pc_out; do python3 -m py_compile $EP/anim/$f.py; done
E6=$REPO/episodes/ep06_haizen/anim
T=$(mktemp -d); K=$T/marurobo_ep07
mkdir -p $K/pc_kit $K/episodes/ep07_keyboard/anim/fonts $K/episodes/ep07_keyboard/voice $K/episodes/ep06_haizen/anim $K/episodes/ep03_ad/storyboard $K/skill/marurobo-video-production/scripts $K/episodes/ep01_earphone/stage/maru
cp $EP/pc_kit/run_pc_render_ep07.ps1 $EP/pc_kit/README_PC.md $EP/pc_kit/はじめに.txt $K/pc_kit/
cp $EP/pc_kit/はじめに.txt $EP/pc_kit/README_PC.md $K/
cp $EP/anim/scenes.py $EP/anim/kit.py $EP/anim/maru7.py $EP/anim/timing.py $EP/anim/pc_out.py $EP/anim/clips.json $K/episodes/ep07_keyboard/anim/
cp "$KEY_FONT" $K/episodes/ep07_keyboard/anim/fonts/NotoSansJP_700Bold.ttf
cp $EP/voice/placement.json $EP/voice/script_v1_0.json $EP/voice/letter_times.json $EP/voice/pauses.json $K/episodes/ep07_keyboard/voice/
cp $E6/kit.py $E6/core.py $E6/plan.py $K/episodes/ep06_haizen/anim/
cp $REPO/episodes/ep03_ad/storyboard/scenes.py $K/episodes/ep03_ad/storyboard/
S=$REPO/skill/marurobo-video-production/scripts
cp $S/maru_real.py $S/marumotion.py $S/maru_sfx.py $K/skill/marurobo-video-production/scripts/
cp $REPO/episodes/ep01_earphone/stage/maru/marurig.py $K/episodes/ep01_earphone/stage/maru/
(cd $T && rm -f "$OUT/marurobo_ep07.zip" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$OUT/marurobo_ep07.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('marurobo_ep07'):
    for f in fs:
        if '__pycache__' in r or '_before_' in f: continue
        z.write(os.path.join(r,f))
z.close()")
rm -rf $T; ls -la $OUT/marurobo_ep07.zip
