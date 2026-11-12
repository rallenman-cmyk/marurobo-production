#!/bin/bash
# 冒頭の動き（ピクトグラム版）：連番（640x360）→ 軽いノイズ取り → 1280x720 → 字幕 → 音
set -e
H=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/human; AV=$H/av
FONTS=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/av/fonts
ffmpeg -v error -y -framerate 24 -start_number 1 -i $H/op_pict/frames/f_%04d.png -i $H/audio/opening.wav -frames:v 528 \
  -vf "hqdn3d=2.5:2:4:4,scale=1280:720:flags=lanczos,subtitles=$AV/opening_subs.ass:fontsdir=$FONTS" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -shortest $AV/opening_pict.mp4
ls -la $AV/opening_pict.mp4
