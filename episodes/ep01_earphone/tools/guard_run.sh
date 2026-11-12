#!/bin/bash
# 第4章の描画を守りながら、確かめ用の Blender を一本動かす：空きメモリが MIN_MB を下回ったら、その Blender を止める。最大のメモリ使用量も記録
#   使い方: guard_run.sh LOG MIN_MB -- コマンド...
LOG=$1; MIN=$2; shift 3
"$@" > "$LOG" 2>&1 &
P=$!; peak=0
while kill -0 $P 2>/dev/null; do
  a=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
  r=$(awk '/VmRSS/{print int($2/1024)}' /proc/$P/status 2>/dev/null); r=${r:-0}; [ "$r" -gt "$peak" ] && peak=$r
  if [ "$a" -lt "$MIN" ]; then echo "GUARD: MemAvailable ${a}MB < ${MIN}MB → stop" >> "$LOG"; kill $P 2>/dev/null; sleep 1; kill -9 $P 2>/dev/null; break; fi
  sleep 0.5
done
wait $P 2>/dev/null; echo "GUARD END rc=$? peak_rss=${peak}MB" >> "$LOG"
