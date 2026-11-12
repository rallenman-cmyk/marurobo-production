#!/bin/bash
# 3D の描き直し（第4章 pair6）を見張る：T 秒（既定 720）たつか、全部描けるか、描き手がいなくなったら、進み具合を一行出して終わる
#   待っている間もこまめに終わって声をかけるのは、手が空いたままだとコンテナが片付けられて（再起動して）描き手が止まるため
D=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/ch03/pair6
T=${1:-720}; NEED=${2:-2660}; end=$(( $(date +%s) + T ))
while :; do
  n=$(find $D/frames -name "p_*.png" -size +0 | wc -l)
  h=$(pgrep -fc "pair6/helper.sh ")
  if [ "$n" -ge "$NEED" ] || [ "$h" -eq 0 ] || [ "$(date +%s)" -ge "$end" ]; then break; fi
  sleep 30
done
echo "frames=$n/$NEED helpers=$h blender=$(pgrep -fc 'blender -b') empty=$(find $D/frames -size 0 | wc -l) mem_avail=$(free -g | awk '/Mem/{print $7}')G at $(date +%H:%M)UTC"
