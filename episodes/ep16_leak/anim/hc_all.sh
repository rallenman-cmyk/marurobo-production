#!/bin/bash
cd /home/user/marurobo-production/episodes/ep16_leak/anim
W=/tmp/claude-0/-home-user-marurobo-production/0dd8ecb0-ce04-5cc7-9a3f-3082c1692b6c/scratchpad/maru; B=$W/blender-4.3.2-linux-x64/blender; export MARU_WORK=$W
L="shadow,shadow1,shadow2,shadow3,shadow4,maru,worker,gk,mach,g9mach,g9shadow,c9wk0,c9wk1,c9wk2,cart,door,door2,door_work,door_admin,door_hall2,door_tags,door_backup,door_hall5,hdoor0,hdoor1,g9home0"
for k in 0 1 2 3 4 5 6 7 8 9; do L="$L,sdoor$k"; done
for k in 0 1 2 3; do L="$L,g9door$k"; done
c=$1
$B -b --factory-startup --python hitcheck.py -- $c $L 2>&1 | grep -E "^HIT" > $W/out/hc9/$c.txt
echo "$c $(tail -1 $W/out/hc9/$c.txt)"
