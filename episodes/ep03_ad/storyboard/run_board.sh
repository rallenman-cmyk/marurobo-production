#!/bin/bash
# 絵コンテの 3D を全部描く：bash run_board.sh <blender> <samples> [場面...]
B=$1; N=$2; shift 2
L=${@:-b00 b01 b02 b04 b05 b06 b07 b08 b10 b11 b12 b13 b14 b15 b16 b17 b18 b19 b21 b22}
cd "$(dirname "$0")"
for k in $L; do $B -b --factory-startup --python board.py -- $k raw/board/$k.png $N 2>&1 | grep -E "RENDERED|Error|Traceback|line [0-9]" | tail -3; done
