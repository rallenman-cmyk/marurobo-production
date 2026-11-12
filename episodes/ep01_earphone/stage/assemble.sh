#!/bin/bash
# 連番 → 1280x720に拡大 → 字幕を焼き付け → 音を重ねる → 比較動画
set -e
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage; AV=$S/av; N=${1:-720}
cd $AV
ffmpeg -v error -y -framerate 24 -start_number 1 -i $S/buffer_anim/frames/f_%04d.png -i $AV/sample_audio.wav -frames:v $N \
  -vf "scale=1280:720:flags=lanczos,subtitles=$AV/subs.ass:fontsdir=$AV/fonts" \
  -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -shortest $AV/buffer_sample_30s.mp4
if [ "$N" -ge 720 ]; then
  ffmpeg -v error -y -i $AV/card_before.mp4 -i $AV/codex_ch8.mp4 -i $AV/card_after.mp4 -i $AV/buffer_sample_30s.mp4 \
    -filter_complex "[0:v]setsar=1,fps=24[v0];[1:v]scale=1280:720,setsar=1,fps=24[v1];[2:v]setsar=1,fps=24[v2];[3:v]setsar=1,fps=24[v3];[0:a]aresample=48000[a0];[1:a]aresample=48000[a1];[2:a]aresample=48000[a2];[3:a]aresample=48000[a3];[v0][a0][v1][a1][v2][a2][v3][a3]concat=n=4:v=1:a=1[v][a]" \
    -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k $AV/compare_before_after.mp4
fi
ls -la $AV/*.mp4
