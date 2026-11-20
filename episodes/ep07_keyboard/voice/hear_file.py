# 声のファイルをそのまま書き起こす（番号でなくファイルで。7本目 v8）：MARU_WORK=<作業> python3 hear_file.py a.wav b.wav …
import os, sys, wave
import numpy as np
_F = sys.argv[1:]; sys.argv = [sys.argv[0], "1"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "retake_line.py"), encoding="utf-8").read().split("norm = lambda")[0]
exec(src)
for f in _F:
    x = np.frombuffer(wave.open(f).readframes(10 ** 8), np.int16).astype(np.float32) / 32768
    print(os.path.basename(f), "|", heard_kana(x), flush=True)
