# 9本目（エスカレーター）の効果音。7本目の sfx.py を写して、この回の音を足した。6本目の sfx.py（3〜6本目の step・jump・land・pi・pop・whoosh・click・snap・motor など）に、この回の音を足す
#   clank：くしに乗り上げる・ふたを外す（ガチッ）／snap：くしの歯の先が折れる（ポキッ）／roll：ボールが転がる（ころころ）／
#   stop：エスカレーターが止まる（うなりが下がって静かになる）／click：ボタン（カチッ）／thunk：ガクンと止まる（想像の場面）
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
    if kind == "snap":      # ポキッ（短く高い）
        return 0.3 * _mx(_n(0.03, sr, 2500, 9000, a=0.0002, d=0.008), 0.5 * _t(2200, 1800, 0.04, sr, a=0.0002, d=0.015))
    if kind == "roll":      # ころころ（小さな音が続く）
        n = int(1.0 * sr); x = np.zeros(n)
        for i in range(9):
            c = _n(0.03, sr, 400, 2200, a=0.001, d=0.012) * (0.6 + 0.4 * (i % 2)); j = int(i * 0.11 * sr); x[j:j + len(c)] += c[:n - j]
        return 0.22 * x * np.linspace(1, 0.6, n)
    if kind == "stop":      # 低いうなりが下がって消える
        n = int(0.9 * sr); tt = np.arange(n) / sr; f = 95 - 40 * tt / 0.9
        x = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.linspace(1, 0, n) ** 1.5
        return 0.25 * (x + 0.3 * _n(0.9, sr, 60, 400, a=0.01, d=0.8)[:n])
    if kind == "start":     # 動き出す（静かな所から低いうなりが上がる。stop の逆）
        n = int(0.9 * sr); tt = np.arange(n) / sr; f = 55 + 40 * tt / 0.9
        x = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.linspace(0, 1, n) ** 1.5
        return 0.25 * (x + 0.3 * _n(0.9, sr, 60, 400, a=0.8, d=1e9)[:n] * np.linspace(0, 1, n))
    if kind == "hum":       # エスカレーターの低いうなり（2 秒でつながる輪。ずっと流す床の音）
        n = 2 * sr; tt = np.arange(n) / sr
        x = np.sin(2 * np.pi * 95 * tt) + 0.5 * np.sin(2 * np.pi * 190 * tt) + 0.25 * np.sin(2 * np.pi * 285 * tt)
        return (x / 1.75 + 0.35 * _n(2.0, sr, 80, 600, a=0.0001, d=1e9)).astype(np.float32)
    if kind == "murmur":    # 駅のざわめき（人の声のような帯の雑音。ゆっくり大きさが揺れる。4 秒でつながる輪）
        n = 4 * sr; tt = np.arange(n) / sr
        x = _n(4.0, sr, 250, 1800, a=0.0001, d=1e9) * (0.75 + 0.25 * np.sin(2 * np.pi * tt / 4.0)) * (0.85 + 0.15 * np.sin(2 * np.pi * 3 * tt / 4.0))
        return x.astype(np.float32)
    if kind == "katan":     # 段がくしの下へ入る小さな「カタン」（軽い金属の当たる音）
        return 0.26 * _mx(_n(0.05, sr, 400, 3500, a=0.0004, d=0.018), 0.5 * _t(520, 470, 0.08, sr, a=0.0004, d=0.03))
    if kind == "gotton":    # 段が歯車で回る「ゴトン」（低く、ゆっくり）
        return 0.34 * _mx(_n(0.18, sr, 60, 700, a=0.003, d=0.07), 0.8 * _t(85, 60, 0.3, sr, a=0.003, d=0.12))
    if kind == "chain":     # 鎖の音（小さなカチャカチャが続く。1.2 秒）
        n = int(1.2 * sr); x = np.zeros(n)
        for i in range(12):
            c = _n(0.025, sr, 1500, 6000, a=0.0003, d=0.008) * (0.5 + 0.5 * ((i * 7) % 3) / 2); j = int(i * 0.095 * sr); x[j:j + len(c)] += c[:n - j]
        return 0.2 * x * np.sin(np.linspace(0, np.pi, n)) ** 0.5
    if kind == "click":     # ボタン（カチッ）
        return 0.3 * _mx(_n(0.02, sr, 1500, 6000, a=0.0002, d=0.006), 0.4 * _t(1800, 1700, 0.03, sr, a=0.0002, d=0.01))
    if kind == "thunk":     # ガクン（低くて重い）
        return 0.4 * _mx(_n(0.12, sr, 60, 900, a=0.001, d=0.08), 0.7 * _t(70, 45, 0.25, sr, a=0.001, d=0.15))
    return S6.make(kind, sr)
