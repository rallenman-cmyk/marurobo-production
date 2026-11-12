#!/bin/bash
# 時間までに描き終わらなかったときの予備：描けていないコマを簡易描画のコマで埋めてつなぐ
cd /tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad
SRC=stage/ch03/anim_eevee; FB=stage/ch03/anim_wb; OUT=stage/ch03/anim_mix
rm -rf $OUT; mkdir -p $OUT/frames; cp $SRC/ch03_log.json $OUT/; cp -r $FB/diagram $OUT/
python3 - <<PY
import os
from PIL import Image
n_e = n_w = 0
for f in range(1, 1192):
    p = "$SRC/frames/f_%04d.png" % f; q = "$OUT/frames/f_%04d.png" % f
    try:
        Image.open(p).verify(); os.symlink(os.path.abspath(p), q); n_e += 1
    except Exception:
        Image.open("$FB/frames/f_%04d.png" % f).convert("RGB").resize((480, 270), Image.LANCZOS).save(q); n_w += 1
print("eevee", n_e, "workbench", n_w)
PY
python3 stage/ch03/ch03_assemble.py $OUT > $OUT/assemble.log 2>&1; tail -1 $OUT/assemble.log
