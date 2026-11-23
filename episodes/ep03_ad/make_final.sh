#!/bin/bash
# 3本目の公開用の完成動画（1080p）を作る（2026-11-23 ユーザー「mp4ファイル作ってこちらが依頼したらすぐ出せるようにして」）
#   組み立て（anim/assemble.py）は 1280×720 で作るので、きれいな設定（CRF 16）で組んでから 1920×1080 に広げる。
#   チャットで送れるのは 400MB まで（SKILL §9）なので、映像 3000k の 2 パス・音はそのまま（約 350MB）。
#   bash make_final.sh <scratch>   （<scratch> に font・v12f・v10f・anim/2d_v10・maru・voice11 がある前提。v12 と同じ組み立て）
set -e
S=$1; OUT=$S/final; mkdir -p $OUT
cd "$(dirname "$0")/anim"
MARU_WORK=$S/maru CRF=16 python3 assemble.py $S/font $OUT/ep03_v12_720_hq.mp4 $S/v12f $S/v10f $S/anim/2d_v10 > $OUT/assemble.log 2>&1
cd $OUT
ffmpeg -v error -y -i ep03_v12_720_hq.mp4 -vf "scale=1920:1080:flags=lanczos" -c:v libx264 -preset slow -b:v 3000k -pass 1 -passlogfile p2 -an -f mp4 /dev/null
ffmpeg -v error -y -i ep03_v12_720_hq.mp4 -vf "scale=1920:1080:flags=lanczos" -c:v libx264 -preset slow -b:v 3000k -pass 2 -passlogfile p2 -c:a copy -movflags +faststart ep03_完成_v12_1080p.mp4
ls -la ep03_完成_v12_1080p.mp4
