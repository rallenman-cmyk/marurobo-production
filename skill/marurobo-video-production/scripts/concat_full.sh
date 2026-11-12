#!/bin/bash
# 通しの完成版：各章の本番（1920×1080・24fps・h264）をつなぐ
#   絵：つなぐだけ（もう一度圧縮しない＝画質が落ちない）
#   音：章ごとに「絵のコマ数 × 2000 サンプル（48kHz）」ちょうどに伸ばして切りそろえる（時刻ではなくサンプル数で数える。
#       AAC の時刻は少しずれていて、時刻で数えると後ろの章ほど声が早くなった：EP01 の失敗）→ ステレオ 48kHz でつなぐ
#   大きさ：通しで一度測り、同じだけ足す（-14 LUFS。強弱は変えない）。山は alimiter で -1.5 dBFS に抑える
#   使い方: bash concat_full.sh 出力.mp4 章1.mp4 章2.mp4 …   （作業用は 出力と同じ所の work_full/）
set -e
OUT=${1:?出力.mp4}; shift; [ $# -ge 1 ] || { echo "章の mp4 を順に並べて渡す"; exit 1; }
W=$(dirname "$OUT")/work_full; rm -rf "${W:?}"; mkdir -p "$W"
i=0; : > "$W/video.txt"; : > "$W/audio.txt"; T=0
for f in "$@"; do
  [ -f "$f" ] || { echo "STOP: ない $f"; exit 1; }
  i=$((i + 1)); v=$(ffprobe -v error -select_streams v -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name -of csv=p=0 "$f")
  [ "$v" = "h264,1920,1080,yuv420p,24/1" ] || { echo "STOP: 形式がちがう $f ($v)"; exit 1; }
  n=$(ffprobe -v error -select_streams v -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$f")
  echo "$i $(basename "$f") frames $n  始まり $(python3 -c "t=$T; print('%d:%05.2f' % (t // 60, t % 60))")"
  T=$(python3 -c "print($T + $n / 24.0)"); ns=$((n * 2000))
  ffmpeg -v error -y -i "$f" -vn -af "aresample=48000,asetpts=N/SR/TB,apad=whole_len=$ns,atrim=end_sample=$ns" -ac 2 -c:a pcm_s16le "$W/a_$i.wav"
  echo "file '$f'" >> "$W/video.txt"; echo "file '$W/a_$i.wav'" >> "$W/audio.txt"
done
echo "通し $(python3 -c "t=$T; print('%d:%05.2f' % (t // 60, t % 60))")"
ffmpeg -v error -y -f concat -safe 0 -i "$W/audio.txt" -c:a pcm_s16le "$W/full_raw.wav"
ffmpeg -hide_banner -i "$W/full_raw.wav" -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p' > "$W/loud_pass1.json"
G=$(python3 -c "import json; m=json.load(open('$W/loud_pass1.json')); print('%.2f' % (-14.0 - float(m['input_i'])))")
echo "1 回目：$(python3 -c "import json; m=json.load(open('$W/loud_pass1.json')); print('I', m['input_i'], 'TP', m['input_tp'])")  → 足す ${G} dB"
ffmpeg -v error -y -i "$W/full_raw.wav" -af "volume=${G}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled" -c:a pcm_s16le "$W/full_norm.wav"
ffmpeg -v error -y -f concat -safe 0 -i "$W/video.txt" -map 0:v -c:v copy "$W/full_video.mp4"
ffmpeg -v error -y -i "$W/full_video.mp4" -i "$W/full_norm.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -movflags +faststart -t $T "$OUT"
ffmpeg -hide_banner -i "$OUT" -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=summary -f null - 2>&1 | grep -E "Input Integrated|Input True Peak"
rm -f "$W"/a_*.wav "$W/full_raw.wav"
echo "CONCAT DONE"
