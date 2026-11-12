#!/bin/bash
# 連番 → 1280x720 → 字幕を焼き付け → 音を重ねる
set -e
H=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/human; AV=$H/av
FONTS=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/av/fonts
ffmpeg -v error -y -framerate 24 -start_number 1 -i $H/op_icon_anim/frames/f_%04d.png -i $H/audio/hero_test.wav -frames:v 192 \
  -vf "scale=1280:720:flags=lanczos,subtitles=$AV/hero_subs.ass:fontsdir=$FONTS" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -shortest $AV/hero_motion_test.mp4
ls -la $AV/hero_motion_test.mp4
