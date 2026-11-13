#!/bin/bash
# 絵コンテの 3D を全部描く：bash run_board.sh <blender> <絵のフォルダ> <出力フォルダ> <samples> [場面...]
B=$1; TX=$2; O=$3; N=$4; shift 4
L=${@:-b01 b02 b03 b04a b04b b05a b05b b08 b11 b12 b13 b14 b15 b16 b17 b18 b21 b22 b23}
cd "$(dirname "$0")"; mkdir -p "$O"
for k in $L; do $B -b --factory-startup --python board.py -- $k "$O/$k.png" $N --tex "$TX" 2>&1 | grep -E "RENDERED|Error|Traceback|line [0-9]+" | tail -3; done
