#!/bin/bash
# PC で描いた第1・2章（mp4）を受け取り、1080p で組む（字幕・声・音はこちらで付ける）
# 使い方: bash pc_ingest_ch0102.sh DL_DIR
#   DL_DIR：Google ドライブの marurobo_render/ch0102 から落としたもの（新しい空のフォルダに入れる）
#     ch0102_0001-0100.mp4 … ch0102_1901-1944.mp4（100コマずつ20本）と ch0102_log.json（まるロボの足音・跳ぶ音の時刻）
#   出力：stage/human/anim_ch0102_1080/ch0102_animatic.mp4（1920×1080）
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; H=$S/stage/human
DL=$(cd "$1" && pwd); O=$H/anim_ch0102_1080
mkdir -p $O/frames
cp $DL/ch0102_log.json $O/
for f in $DL/ch0102_*.mp4; do                                        # 範囲ごとの mp4 → f_NNNN.png（範囲の始まりの番号から）
  b=$(basename "$f" .mp4); r=${b#ch0102_}; a=$((10#${r%-*}))
  ffmpeg -v error -y -i "$f" -start_number $a $O/frames/f_%04d.png
done
python3 - "$O" <<'PY'
import os, sys, json
from PIL import Image
o = sys.argv[1]; st = set(os.listdir(os.path.join(o, "frames"))); n = json.load(open(os.path.join(o, "ch0102_log.json")))["frames"]
miss = [i for i in range(1, n + 1) if "f_%04d.png" % i not in st]
sz = Image.open(os.path.join(o, "frames", "f_0001.png")).size
print("frames", len(st), "/", n, "missing", miss[:10], "size", sz)
if miss or sz != (1920, 1080): sys.exit("そろっていない（上の番号を PC で描き直してもらう）")
PY
cd $H && MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 python3 ch0102_assemble.py $O
ffprobe -v error -show_entries stream=width,height:format=duration -of compact $O/ch0102_animatic.mp4
