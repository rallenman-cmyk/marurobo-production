#!/bin/bash
# 第6章・第7章・第8章の塔を、確認用（640×360・EEVEE 16）で描く。描き手 NW 本（既定 3）。範囲は CH コマずつ（既定 40）
#   それぞれの描き手は、範囲の並びを少しずつずらして回る（同じ範囲を取り合わない。描けている絵は飛ばす）
#   使い方: run_ch678.sh [NW] [CH] [jobs...]   jobs は ch6 ch7 ch8 のどれか（既定ぜんぶ、この順）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad; C=$S/stage/ch03
NW=${1:-3}; CH=${2:-40}; shift 2; JOBS=${@:-ch6 ch7 ch8}
declare -A SCRIPT=( [ch6]=ch06_stage.py [ch7]=ch07_stage.py [ch8]=ch07_stage.py )
declare -A EXTRA=( [ch6]="" [ch7]="--part ch7" [ch8]="--part ch8" )
declare -A NF=( [ch6]=1933 [ch7]=3458 [ch8]=510 )
declare -A OUTD=( [ch6]=$C/ch06_out [ch7]=$C/ch07_out [ch8]=$C/ch08_tower_out )
for w in $(seq 1 $NW); do
  (
    for j in $JOBS; do
      n=${NF[$j]}; rs=(); for ((a=1; a<=n; a+=CH)); do b=$((a+CH-1)); [ $b -gt $n ] && b=$n; rs+=("$a:$b"); done
      k=${#rs[@]}; off=$(( (w-1) * k / NW )); ord=()
      for ((i=0; i<k; i++)); do ord+=("${rs[$(( (i+off) % k ))]}"); done
      bash $C/stage_helper.sh ${SCRIPT[$j]} ${OUTD[$j]} "w$w" "${EXTRA[$j]}" "${ord[@]}"
    done
    echo "WORKER $w DONE $(date -u +%H:%M)" >> $C/ch678_workers.log
  ) &
  sleep 20
done
wait
echo "ALL CH678 DONE $(date -u +%H:%M)" >> $C/ch678_workers.log
