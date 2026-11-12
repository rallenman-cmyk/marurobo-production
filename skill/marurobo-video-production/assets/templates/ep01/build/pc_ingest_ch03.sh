#!/bin/bash
# PC で描いた第3章の 3D（mp4）を受け取り、1080p で組む（図・字幕・声・音はこちらで付ける）
# 使い方: bash pc_ingest_ch03.sh DL_DIR
#   DL_DIR：Google ドライブの marurobo_render/ch03 から落としたもの（新しい空のフォルダに入れる）
#     ch03_stage_0001-0100.mp4 … ch03_stage_1201-1283.mp4（舞台。100コマずつ13本）
#     train_c1c2.mp4（電車 C1・C2、461コマ）・train_c12.mp4（電車 C12、101コマ）
#     train_frames_log_*.json（電車のカメラの記録。48コマずつ）
#   出力：stage/ch03/anim_1080/ch03_animatic.mp4（1920×1080）
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03
DL=$(cd "$1" && pwd); O=$C/anim_1080; TR=$C/train_1080
mkdir -p $O/frames $TR/frames_train
cp $C/anim_v2/ch03_log.json $O/                                      # 舞台の動きの記録（同じ予定なので、確認用と同じ）
for f in $DL/ch03_stage_*.mp4; do                                    # 舞台：範囲ごとの mp4 → f_NNNN.png（範囲の始まりの番号から）
  b=$(basename "$f" .mp4); r=${b#ch03_stage_}; a=$((10#${r%-*}))
  ffmpeg -v error -y -i "$f" -start_number $a $O/frames/f_%04d.png
done
ffmpeg -v error -y -i $DL/train_c1c2.mp4 -start_number 0 $TR/frames_train/t_%04d.png
ffmpeg -v error -y -i $DL/train_c12.mp4 -start_number 1651 $TR/frames_train/t_%04d.png
cp $DL/train_frames_log_*.json $TR/                                 # 48コマずつの記録（ぜんぶ）
python3 - "$O" "$TR" <<'PY'
import os, sys, json
from PIL import Image
o, tr = sys.argv[1], sys.argv[2]
st = sorted(os.listdir(os.path.join(o, "frames"))); n = json.load(open(os.path.join(o, "ch03_log.json")))["frames"]
miss = [i for i in range(1, n + 1) if "f_%04d.png" % i not in st]
tf = set(os.listdir(os.path.join(tr, "frames_train")))
miss_t = [i for i in list(range(0, 461)) + list(range(1651, 1752)) if "t_%04d.png" % i not in tf]
sz = Image.open(os.path.join(o, "frames", st[0])).size
print("stage", len(st), "/", n, "missing", miss[:10], "train missing", miss_t[:10], "size", sz)
if miss or miss_t or sz != (1920, 1080): sys.exit("そろっていない（上の番号を PC で描き直してもらう）")
PY
cd $C
[ -d $O/diagram ] && [ $(ls $O/diagram | wc -l) -ge 200 ] || MARU_RES=1080 python3 ch03_diagram.py $O       # 図（C13）を 1080p で
[ -d $O/questions ] && [ $(ls $O/questions | wc -l) -ge 230 ] || MARU_RES=1080 python3 ch03_questions.py $O # 二つの疑問（C14）を 1080p で
MARU_RES=1080 MARU_FINAL=1 MARU_CRF=16 python3 ch03_assemble.py $O $S/stage/script/bluetooth_voice_rev3.srt $S/stage/human/audio/song_mono.wav $S/stage/human/op_phys/frames $TR
ffprobe -v error -show_entries stream=width,height:format=duration -of compact $O/ch03_animatic.mp4
