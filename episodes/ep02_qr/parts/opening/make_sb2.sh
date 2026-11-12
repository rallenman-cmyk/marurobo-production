#!/bin/bash
# 絵コンテ v2（スマホを手前に斜めに立てる案）
set -e
cd "$(dirname "$0")"; B=/opt/blender/blender-4.3.2-linux-x64/blender; mkdir -p sb2 sb2/screens
r(){ timeout 900 $B -b --factory-startup -P op_tilt.py -- "$@" 2>&1 | grep -E "Saved|Error:" || true; }
# 1) スマホのカメラから見た絵
(r 3.0 phonecam sb2/screens/pc_plain.png; r 13.5 phonecam sb2/screens/pc_stand.png) &
(r 19.3 phonecam sb2/screens/pc_stand2.png; r 32.0 phonecam sb2/screens/pc_step.png) &
wait
python3 make_screens.py
# 2) 場面
(r 3.0 wide sb2/S01_wide_lines.png --screen sb2/screens/scr_plain_scan.png --lines; r 9.6 wide2 sb2/S03_walk.png --screen sb2/screens/scr_plain_hello.png; r 24.0 close sb2/S06_close.png --screen sb2/screens/scr_stand_hello.png) &
(r 6.4 shoulder sb2/S02_sh_hello.png --screen sb2/screens/scr_plain_hello.png; r 13.5 shoulder sb2/S04_sh_scan.png --screen sb2/screens/scr_stand_scan.png; r 19.3 shoulder sb2/S05_sh_hello.png --screen sb2/screens/scr_stand2_hello.png; r 41.5 wide sb2/S09_off.png --screen sb2/screens/scr_plain_hello.png) &
(r 32.0 shoulder sb2/S07_sh_step.png --screen sb2/screens/scr_step_scan.png; r 36.0 med sb2/S08_med.png --screen sb2/screens/scr_step_scan.png; r 52.0 low sb2/S10_low.png --screen sb2/screens/scr_plain_hello.png; r 64.5 face sb2/S11_face.png --screen sb2/screens/scr_plain_hello.png) &
wait; ls sb2
