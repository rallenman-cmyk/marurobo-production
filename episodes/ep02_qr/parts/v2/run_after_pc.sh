#!/bin/bash
# PC の描画が届いたら 1 回で：① ドライブから受け取る（そろった章だけ）→ ② 章ごとに組む（PC の絵を差し込む・足音）→ ③ 通し（-14 LUFS）→ ④ 機械の点検
#   使い方: bash run_after_pc.sh v9        （WATCH=秒 で受け取りを待つ長さ。既定 60 秒＝今ある分だけ）
#   そろっていない章は絵コンテの静止画のまま組む（final/<章>_pc.json の missing に出る）
VER=${1:-v9}; V2=$(cd "$(dirname "$0")" && pwd); export PC_RENDER=${PC_RENDER:-/home/user/qr_plan/pc_render}
SK=${SK:-$(ls -d /root/.claude/skills/synced/*/marurobo-video-production/scripts 2>/dev/null | head -1)}
[ -f "$SK/drive_watch.py" ] || SK=/home/user/marurobo-production/skill/marurobo-video-production/scripts
mkdir -p "$PC_RENDER"
MARU_DL="$PC_RENDER" MARU_WATCH_SEC=${WATCH:-60} python3 -I "$SK/drive_watch.py" qrop4:21 qrc1:70 qrc2:71 qrc3:28 qrc4:95 qrc5:22
cd "$V2"
for g in "op c3 c5" "c1 end" "c2" "c4"; do
  for t in $g; do python3 final_build.py $t > final/$t.log 2>&1 & done
done
wait
for t in op c1 c2 c3 c4 c5 end; do tail -1 final/$t.log; done
F=$V2/final
cd "$V2/../review" && VER=$VER FINAL=1 PC3D=1 python3 through_review.py $F/qr_ep02_final_test.mp4 $F:op $F:c1 $F:c2 $F:c3 $F:c4 $F:c5 $F:end
cp $F/qr_ep02_final_test.mp4 $F/qr_ep02_final_$VER.mp4
cd autocheck && python3 auto_check.py | tail -20      # 点検は本番（final）と、最後の確認用動画（VER 既定 v8）の両方
