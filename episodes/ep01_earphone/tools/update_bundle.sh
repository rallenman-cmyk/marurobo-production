#!/bin/bash
# PC 用の道具一式（stage/marurobo_tools）を最新にして、zip を作り直す
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; T=$S/stage/marurobo_tools; C=$S/stage/ch03
for f in ch04_pairing6.py ch04_assemble6.py ch04_diagram.py ch03_screen.py earbud_v2.py ch03_plan.py ch03_cams.py ch07_robot.py \
         ch06_plan.py ch06_stage.py ch06_assemble.py ch07_plan.py ch07_stage.py ch07_assemble.py ch08_assemble.py ch08_game.py overlay2d.py; do
  [ -f $C/$f ] && cp $C/$f $T/ch03/
done
mkdir -p $T/ch03/screens && cp $C/screens/*.png $T/ch03/screens/ 2>/dev/null
for f in marumotion.py marurig.py; do [ -f $S/stage/maru/$f ] && cp $S/stage/maru/$f $T/maru/; done
for f in ch0102_seq.py ch0102_assemble.py summary_seq.py people.py hero_anim.py dance.py opening_phys.py; do [ -f $S/stage/human/$f ] && cp $S/stage/human/$f $T/human/; done
mkdir -p $T/voice/achernar && cp $S/stage/voice/achernar/placement.json $T/voice/achernar/   # 声の置き場所（第4〜8章の動きの時刻はこれから計算する）
mkdir -p $T/human/screens $T/human/refscene && cp $S/stage/human/screens/*.png $T/human/screens/ && cp $S/stage/human/refscene/*.png $T/human/refscene/   # 乗客のスマホの画面（music_b.png など）・窓の外の町
# 曲の最初の 86 秒だけ（舞台の荷物の札の棒＝81.0〜84.5 秒、第7章のスピーカー＝40.04〜43.12 秒に使う分）。PC でも同じ場所にあれば、舞台は何もしなくても使う
mkdir -p $T/human/audio && python3 - "$S/stage/human/audio/song_mono.wav" "$T/human/audio/song_mono.wav" <<'PY'
import sys, wave
r = wave.open(sys.argv[1]); w = wave.open(sys.argv[2], "wb"); w.setparams(r.getparams()); w.writeframes(r.readframes(int(86 * r.getframerate()))); w.close()
PY
cd $S/stage && rm -f marurobo_tools.zip && zip -qr marurobo_tools.zip marurobo_tools -x "*/__pycache__/*" "*.bak" && unzip -l marurobo_tools.zip | tail -1
