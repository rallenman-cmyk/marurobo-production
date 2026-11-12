# 会話と広告の回：効果音を合成する（make(種類, 48000) → numpy の音。大きさは 0.3〜0.5 ほど）
#   step：まるロボの足音／jump・land：跳ぶ・着く／pi・pipo：まるロボの電子音（喋らない代わり）／pop：音の泡がはじける
#   bubble_in：泡が流れてくる／gate_up・gate_down：格子が上がる・下りる／lamp：ランプがつく／pop_ui：画面が切り替わる
#   towel：タオルがぱさり／hat：帽子がぽすん／dive：画面に飛び込む／spot・spot_off：照明／win：競りが決まる
#   whoosh：一瞬で終わる競り／rise：台がせり上がる／clatter：ヘッドホンが落ちる
import numpy as np
_rng = np.random.default_rng(3)


def _env(n, a, d, sr):
    e = np.ones(n); ka = max(1, int(a * sr)); e[:ka] = np.linspace(0, 1, ka)
    e *= np.exp(-np.arange(n) / (d * sr)); return e


def _tone(f0, f1, dur, sr, a=0.005, d=0.08, shape="sin"):
    n = int(dur * sr); fr = np.linspace(f0, f1, n); ph = 2 * np.pi * np.cumsum(fr) / sr
    x = np.sin(ph) if shape == "sin" else np.sign(np.sin(ph)) * 0.6
    return x * _env(n, a, d, sr)


def _noise(dur, sr, lo=200, hi=4000, a=0.003, d=0.05):
    n = int(dur * sr); x = _rng.standard_normal(n)
    X = np.fft.rfft(x); fq = np.fft.rfftfreq(n, 1 / sr); X[(fq < lo) | (fq > hi)] = 0
    x = np.fft.irfft(X, n); x /= np.abs(x).max() + 1e-9
    return x * _env(n, a, d, sr)


def _mx(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o


def make(kind, sr=48000):
    if kind == "step":
        return 0.25 * _mx(_noise(0.07, sr, 150, 1500, d=0.018), 0.5 * _tone(180, 120, 0.06, sr, d=0.02))
    if kind == "jump":
        return 0.3 * _tone(300, 900, 0.18, sr, d=0.12)
    if kind == "land":
        return 0.35 * _mx(_noise(0.12, sr, 80, 900, d=0.035), _tone(120, 70, 0.12, sr, d=0.04))
    if kind == "pi":
        return 0.3 * _tone(1800, 1800, 0.09, sr, d=0.05)
    if kind == "pipo":
        a = _tone(1500, 1500, 0.1, sr, d=0.06); b = _tone(1000, 1000, 0.14, sr, d=0.08)
        return 0.28 * np.concatenate([a, np.zeros(int(0.03 * sr)), b])
    if kind == "pop":
        return 0.35 * _mx(_noise(0.06, sr, 1500, 9000, d=0.012), 0.6 * _tone(900, 1500, 0.05, sr, d=0.015))
    if kind == "bubble_in":
        return 0.12 * _tone(500, 700, 0.25, sr, a=0.05, d=0.15)
    if kind in ("gate_up", "gate_down", "rise"):
        n = int(1.0 * sr); m = _noise(1.0, sr, 60, 500, a=0.1, d=0.8) * (0.7 + 0.3 * np.sin(2 * np.pi * 30 * np.arange(n) / sr))
        return 0.3 * m
    if kind == "lamp":
        return 0.3 * _mx(_tone(660, 660, 0.25, sr, d=0.2), _tone(990, 990, 0.25, sr, d=0.2) * 0.6)
    if kind == "pop_ui":
        return 0.22 * _tone(1200, 1600, 0.06, sr, d=0.03)
    if kind == "towel":
        return 0.3 * _noise(0.25, sr, 300, 3000, a=0.01, d=0.08)
    if kind == "hat":
        return 0.35 * _noise(0.1, sr, 100, 1200, d=0.03)
    if kind == "dive":
        return 0.3 * _mx(_tone(400, 1400, 0.35, sr, a=0.02, d=0.25), 0.4 * _noise(0.35, sr, 2000, 8000, a=0.05, d=0.2))
    if kind in ("spot", "spot_off"):
        return 0.35 * _mx(_noise(0.05, sr, 1000, 6000, d=0.01), _tone(90, 60, 0.15, sr, d=0.06))
    if kind == "win":
        return 0.3 * np.concatenate([_tone(880, 880, 0.12, sr, d=0.1), _tone(1320, 1320, 0.25, sr, d=0.2)])
    if kind == "whoosh":
        return 0.35 * _noise(0.35, sr, 300, 6000, a=0.08, d=0.15)
    if kind == "clatter":
        return 0.4 * _mx(_noise(0.3, sr, 800, 7000, d=0.06), 0.5 * _tone(400, 300, 0.2, sr, d=0.05))
    return None
