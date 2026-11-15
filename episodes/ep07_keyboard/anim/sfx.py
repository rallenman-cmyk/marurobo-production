# 7本目（キーボード）の効果音。6本目の sfx.py（3〜6本目の step・jump・land・pi・pop・whoosh・click・snap・motor など）に、この回の音を足す
#   key：キーを押す（カタッ）／tick：電信の受信機（カチッ）／clack：タイプライターの棒が紙を打つ（パチッ）／clank：棒がぶつかる（ガチッ）
#   決まり（SKILL §6）：絵の動き 1 つに音 1 つ。同じ動きに 3D の音と札の音を重ねない。足音は小さく（0.05）
import os, importlib.util
import numpy as np
_sp = importlib.util.spec_from_file_location("sfx_ep06", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ep06_haizen", "anim", "sfx.py"))
S6 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S6)
S3 = S6.S3
_t, _n, _mx = S3._tone, S3._noise, S3._mx


def make(kind, sr=48000):
    if kind == "key":       # カタッ（低めのこもった音と、短い高い音）
        return 0.32 * _mx(_n(0.05, sr, 300, 2500, a=0.0005, d=0.02), 0.5 * _n(0.02, sr, 3000, 9000, a=0.0003, d=0.008))
    if kind == "tick":      # 受信機のカチッ（金属の短い音）
        return 0.28 * _mx(_n(0.03, sr, 1800, 7000, a=0.0003, d=0.01), 0.4 * _t(2600, 2500, 0.03, sr, a=0.0003, d=0.015))
    if kind == "clack":     # 棒が紙を打つ（パチッ）
        return 0.3 * _mx(_n(0.04, sr, 900, 6000, a=0.0003, d=0.012), 0.4 * _t(1400, 1200, 0.05, sr, a=0.0005, d=0.02))
    if kind == "clank":     # 棒どうしがぶつかる（ガチッ）
        return 0.34 * _mx(_n(0.08, sr, 500, 5000, a=0.0005, d=0.04), 0.6 * _t(900, 820, 0.18, sr, a=0.0005, d=0.1))
    return S6.make(kind, sr)
