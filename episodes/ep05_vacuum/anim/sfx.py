# 5本目（ロボット掃除機）の効果音。3本目の sfx.py（step・jump・land・pi・pipo・pop・whoosh・rise など）と 4本目の click に、この回の音を足す
#   chime：台に戻った「ピロリン」／notify：スマホの画面がつく／pipi：先輩の返事（ピッ、ピッ）／pi_low：低い「ピ…」（しょんぼり・返ってこない）
#   bonk：まるロボがゴツン／bonk_soft：昔の先輩のバンパーがコツン／power_down：目の光を消す／snap：ぴたっと重なる
#   switch：電気のスイッチ（パチン）／light_on：目の光がぱっ／stop：先輩がぴたっと止まる／squish：着地（うんちのすぐ横）
#   motor：先輩が走っている間の、小さなモーターの音（組み立てで motor_on〜motor_off の間に敷く）
#   決まり（SKILL §6）：絵の動き 1 つに音 1 つ。同じ動きに 3D の音と札の音を重ねない。足音は小さく（0.05）
import os, importlib.util
import numpy as np
_sp = importlib.util.spec_from_file_location("sfx_ep03", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ep03_ad", "anim", "sfx.py"))
S3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S3)
_t, _n, _mx = S3._tone, S3._noise, S3._mx


def make(kind, sr=48000):
    if kind == "click":
        a = _mx(_n(0.025, sr, 2000, 9000, a=0.0005, d=0.004), 0.5 * _t(2600, 2400, 0.02, sr, a=0.0005, d=0.004))
        return 0.5 * np.concatenate([a, np.zeros(int(0.07 * sr)), 0.6 * a])
    if kind == "chime":
        return 0.28 * np.concatenate([_t(1047, 1047, 0.14, sr, d=0.12), _t(1319, 1319, 0.14, sr, d=0.12), _t(1568, 1568, 0.35, sr, d=0.25)])
    if kind == "notify":
        return 0.25 * _mx(_t(1400, 1400, 0.18, sr, d=0.12), 0.5 * _t(2100, 2100, 0.18, sr, d=0.1))
    if kind == "pipi":
        a = _t(1700, 1700, 0.07, sr, d=0.04)
        return 0.26 * np.concatenate([a, np.zeros(int(0.11 * sr)), a])
    if kind == "pi_low":
        return 0.24 * _t(620, 420, 0.5, sr, a=0.01, d=0.35)
    if kind == "bonk":
        return 0.5 * _mx(_n(0.12, sr, 80, 1200, d=0.03), _t(180, 90, 0.16, sr, d=0.05), 0.3 * _t(700, 500, 0.08, sr, d=0.02))
    if kind == "bonk_soft":
        return 0.35 * _mx(_n(0.06, sr, 300, 2500, d=0.015), 0.5 * _t(380, 300, 0.06, sr, d=0.02))
    if kind == "power_down":
        return 0.25 * _t(900, 180, 0.45, sr, a=0.01, d=0.3)
    if kind == "snap":
        return 0.32 * _mx(_t(880, 880, 0.2, sr, d=0.15), 0.7 * _t(1320, 1320, 0.25, sr, d=0.2), 0.3 * _n(0.03, sr, 2000, 8000, d=0.008))
    if kind == "switch":
        return 0.5 * _mx(_n(0.03, sr, 1500, 9000, a=0.0005, d=0.006), 0.6 * _t(2200, 1800, 0.02, sr, a=0.0005, d=0.005))
    if kind == "light_on":
        return 0.3 * _mx(_t(600, 1400, 0.25, sr, a=0.01, d=0.2), 0.3 * _n(0.25, sr, 3000, 9000, a=0.02, d=0.12))
    if kind == "stop":
        return 0.25 * _mx(_t(500, 500, 0.06, sr, d=0.03), 0.4 * _n(0.05, sr, 200, 1500, d=0.02))
    if kind == "squish":
        return 0.4 * _mx(_n(0.14, sr, 60, 700, d=0.05), _t(140, 80, 0.12, sr, d=0.05))
    if kind == "motor":     # 1 秒ぶん（組み立てでくり返して敷く）
        n = sr; tt = np.arange(n) / sr
        x = 0.6 * _n(1.0, sr, 90, 700, a=0.0, d=100.0) + 0.25 * np.sin(2 * np.pi * 118 * tt) + 0.12 * np.sin(2 * np.pi * 236 * tt)
        return 0.05 * x / (np.abs(x).max() + 1e-9)
    return S3.make(kind, sr)
