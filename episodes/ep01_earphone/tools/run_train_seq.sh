#!/bin/bash
# 第3章の電車の場面（C1・C2・C12）を、カメラが動く連番で描く（確認用：640×360・16サンプル）
#   Blender はコマを描くほどメモリが増える（1コマ約55MB。70コマで約5GB になり、止められた）。
#   そこで 16 コマずつ Blender を起動し直す。描き手は 2 本（1本が描く瞬間に最大約 5GB。3本だと重なったときに止められる）。
#   描き手は、まだ描けていない 16 コマの組を早い者勝ちで取る（mkdir の印）。止まった組は最後にもう一度描く。
#   出力：stage/ch03/train_test/frames_train/t_NNNN.png と train_frames_log_NNNN_*.json（ch03_assemble.py が自動で使う）
S=/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
B=$S/blender/blender-4.3.2-linux-x64/blender
OUT=$S/stage/ch03/train_test; FD=$OUT/frames_train; mkdir -p $FD
OPB=$S/handoff/bluetooth_handoff_restored/restore/v3/bt_opening/output/maru_opening.blend
NW=${1:-2}; CH=16
CHUNKS=$(python3 -c "
r=[]
for a,b in ((0,461),(1651,1752)):
    for i in range(a,b,$CH): r.append('%d:%d'%(i,min(i+$CH,b)))
print(' '.join(r))")
missing() { local i; for i in $(seq $1 $(($2-1))); do [ -s $(printf "$FD/t_%04d.png" $i) ] || return 0; done; return 1; }
worker() {  # $1 名前 $2 印のフォルダ
  for c in $CHUNKS; do
    i0=${c%:*}; i1=${c#*:}
    missing $i0 $i1 || continue
    mkdir $2/$c 2>/dev/null || continue
    a=$(python3 -c "print('%.6f:%.6f'%($i0/24.0,$i1/24.0))")
    echo "=== $c ($a) start $(date +%H:%M:%S)" >> $OUT/run_train_$1.log
    $B -b --factory-startup --python $S/stage/ch03/ch03_train.py -- --blend $OPB --out $OUT --res 640 360 --samples 16 --anim $a --share 1 --tag $1 >> $OUT/run_train_$1.log 2>&1
    echo "=== $c done rc=$? $(date +%H:%M:%S)" >> $OUT/run_train_$1.log
  done
}
for pass in 1 2 3; do
  LK=$OUT/locks_$pass; rm -rf $LK; mkdir -p $LK
  for w in $(seq 1 $NW); do worker w$w $LK & sleep 40; done
  wait
  find $FD -name 't_*.png' -size 0 -delete                          # 止められた描き手の「描いている印」を消す
  left=0; for c in $CHUNKS; do missing ${c%:*} ${c#*:} && left=$((left+1)); done
  echo "pass $pass end $(date +%H:%M:%S) chunks_left=$left" >> $OUT/run_train_all.log
  [ $left -eq 0 ] && break
done
echo "ALL TRAIN DONE $(date +%H:%M:%S)" >> $OUT/run_train_all.log
