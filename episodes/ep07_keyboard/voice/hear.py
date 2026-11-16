# 声のファイルを、漢字とひらがなで書き起こして読みを確かめる（7本目 v6）
# MARU_WORK=<作業> python3 hear.py 番号,番号…
import os, sys, json, wave
import numpy as np
sys.argv = [sys.argv[0], "1"] + sys.argv[1:]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "retake_line.py"), encoding="utf-8").read().split("norm = lambda")[0]
exec(src)
for no in sys.argv[2].split(","):
    x = np.frombuffer(wave.open(D + "/line_%03d.wav" % int(no)).readframes(10 ** 8), np.int16).astype(np.float32) / 32768
    print(no, "|", heard(x), "|", heard_kana(x), flush=True)
