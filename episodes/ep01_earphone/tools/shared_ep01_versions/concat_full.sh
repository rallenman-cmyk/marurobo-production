#!/bin/bash
# 通しの完成版（約18分・1080p）：各章の本番をつなぐ
#   絵：つなぐだけ（もう一度圧縮しない＝画質が落ちない）。音：章ごとに絵の長さちょうどに伸ばして切りそろえ（ずれがたまらない。
#   各章の音は絵より 0.01〜0.1 秒短く終わる（中身は頭からぴったり合っている）ので、終わりに無音を足す。サンプル数で数える。2026-11-09：時刻で数えると足りず、後ろの章ほど声が早くなっていた）、
#   ステレオ 48kHz にしてつなぎ、通しで大きさをそろえる（一度測って同じだけ足す＝強弱は変えない。山は alimiter で -1.5 dBFS に抑える。目安 -14 LUFS）
#   使い方: bash concat_full.sh   → stage/final/bluetooth_full_1080.mp4
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; F=$S/stage/final; W=$S/work_full; rm -rf $W; mkdir -p $W
LIST="$F/ch0102_final_1080.mp4 $F/ch03_final_1080.mp4 $F/ch04_final_1080.mp4 $S/stage/ch03/ch5_final/ch05_final_1080.mp4 $F/ch06_final_1080.mp4 $F/ch07_final_1080.mp4 $F/ch08_final_1080.mp4 $F/summary_final_1080.mp4"
i=0; : > $W/video.txt; : > $W/audio.txt; T=0
for f in $LIST; do
  [ -f "$f" ] || { echo "STOP: ない $f"; exit 1; }
  i=$((i + 1)); v=$(ffprobe -v error -select_streams v -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name -of csv=p=0 "$f")
  [ "$v" = "h264,1920,1080,yuv420p,24/1" ] || { echo "STOP: 形式がちがう $f ($v)"; exit 1; }
  n=$(ffprobe -v error -select_streams v -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$f")
  d=$(python3 -c "print('%.6f' % ($n / 24.0))")
  echo "$i $(basename $f) frames $n = ${d}s  始まり $(python3 -c "t=$T; print('%d:%05.2f' % (t // 60, t % 60))")"
  T=$(python3 -c "print($T + $n / 24.0)")
  ns=$((n * 2000))                                                     # 48kHz で n コマ分のサンプル数（24fps）
  ffmpeg -v error -y -i "$f" -vn -af "aresample=48000,asetpts=N/SR/TB,apad=whole_len=$ns,atrim=end_sample=$ns" -ac 2 -c:a pcm_s16le $W/a_$i.wav   # 時刻はサンプル数で数え直す（AAC の時刻は少しずれている）
  echo "file '$f'" >> $W/video.txt; echo "file '$W/a_$i.wav'" >> $W/audio.txt
done
echo "通し $(python3 -c "t=$T; print('%d:%05.2f' % (t // 60, t % 60))")"
ffmpeg -v error -y -f concat -safe 0 -i $W/audio.txt -c:a pcm_s16le $W/full_raw.wav
M=$(ffmpeg -hide_banner -i $W/full_raw.wav -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
echo "$M" > $W/loud_pass1.json
G=$(python3 -c "import json; m=json.load(open('$W/loud_pass1.json')); print('%.2f' % (-14.0 - float(m['input_i'])))")
echo "1 回目：$(python3 -c "import json; m=json.load(open('$W/loud_pass1.json')); print('I', m['input_i'], 'TP', m['input_tp'], 'LRA', m['input_lra'])")  → 足す ${G} dB"
ffmpeg -v error -y -i $W/full_raw.wav -af "volume=${G}dB,alimiter=limit=0.84:attack=5:release=60:level=disabled" -c:a pcm_s16le $W/full_norm.wav
ffmpeg -v error -y -f concat -safe 0 -i $W/video.txt -map 0:v -c:v copy $W/full_video.mp4
ffmpeg -v error -y -i $W/full_video.mp4 -i $W/full_norm.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -movflags +faststart -t $T $F/bluetooth_full_1080.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,channels -of compact $F/bluetooth_full_1080.mp4
ffmpeg -hide_banner -i $F/bluetooth_full_1080.mp4 -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=summary -f null - 2>&1 | grep -E "Input Integrated|Input True Peak|Input LRA"
rm -f $W/a_*.wav $W/full_raw.wav
echo "CONCAT DONE $(date -u +%T)"
