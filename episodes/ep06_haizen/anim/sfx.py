# 6本目（配膳ロボット）の効果音。5本目の sfx.py（3本目の step・jump・land・pi・pipo・pop・whoosh と、click・stop・motor・snap など）に、この回の音を足す
#   piron：先輩の「ピロン」（画面がぱっと明るくなる）／clink：料理をテーブルに置く（コトッ）／chair：いすを引く（ズズッ）
#   rub：まるロボが頭ですりすり／purr：耳をなでられて、うれしい電子音／grr：怒った顔の「ブブッ」／rise：道が伸びる
#   決まり（SKILL §6）：絵の動き 1 つに音 1 つ。同じ動きに 3D の音と札の音を重ねない。足音は小さく（0.05）
import os, importlib.util
import numpy as np
_sp = importlib.util.spec_from_file_location("sfx_ep05", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ep05_vacuum", "anim", "sfx.py"))
S5 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S5)
S3 = S5.S3
_t, _n, _mx = S3._tone, S3._noise, S3._mx


def make(kind, sr=48000):
    if kind == "piron":
        return 0.26 * np.concatenate([_t(1319, 1319, 0.09, sr, d=0.06), _t(1976, 1976, 0.22, sr, d=0.18)])
    if kind == "clink":
        return 0.3 * _mx(_n(0.04, sr, 1500, 7000, a=0.0005, d=0.01), 0.6 * _t(2400, 2300, 0.12, sr, a=0.0005, d=0.06))
    if kind == "chair":
        n = int(0.45 * sr); tt = np.arange(n) / sr
        x = _n(0.45, sr, 120, 900, a=0.02, d=0.3) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * tt))
        return 0.45 * x
    if kind == "rub":
        return 0.18 * _n(0.18, sr, 600, 3000, a=0.03, d=0.1)
    if kind == "purr":
        return 0.2 * np.concatenate([_t(880, 1175, 0.12, sr, d=0.08), _t(1175, 1568, 0.18, sr, d=0.14)])
    if kind == "grr":
        a = _t(300, 260, 0.12, sr, d=0.05)
        return 0.3 * np.concatenate([a, np.zeros(int(0.05 * sr)), a])
    if kind == "splash":    # スープがはねる（ピチャッ）。v2
        return 0.3 * _mx(_n(0.12, sr, 700, 5000, a=0.002, d=0.08), 0.5 * _n(0.05, sr, 2500, 9000, a=0.001, d=0.03))
    if kind == "rise":
        return 0.22 * _t(500, 1100, 0.6, sr, a=0.05, d=0.3)
    return S5.make(kind, sr)
