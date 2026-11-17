# まるロボの動きの音（全部の回で共通）。marumotion の予定の events の種類ごとに、音を作る
#   中身は 1本目の見本リールの音（episodes/ep01_earphone/stage/maru/maru_reel_assemble.py）そのまま。2026-11-17 共通にした
#   使い方：import maru_sfx; x = maru_sfx.make("beep_yes", strength=1.0, sr=48000)（無い種類は None）
#   予定の events の時刻に置く（自分で別の時刻を決めない。references/maru_motions.md「音」）
import math
import numpy as np

KINDS = ("step", "step_turn", "takeoff", "land", "beep_yes", "beep_no", "beep_surprise", "beep_happy", "beep_think", "beep_question",
         "beep_hello", "power_down", "boot", "beep_present", "ding", "sigh", "zoom", "cradle_out", "cradle_in", "unload", "rub")
_rng = np.random.default_rng(5)


def make(kind, strength=1.0, sr=48000):
    SR = sr

    def env_ad(n, a=0.004, d=0.08):
        t = np.arange(n) / SR; return np.minimum(t / a, 1.0) * np.exp(-np.maximum(t - a, 0) / d)

    def tone(f0, f1, dur, amp, d=None, shape="sine"):
        n = int(dur * SR); t = np.arange(n) / SR; f = f0 + (f1 - f0) * t / dur
        ph = 2 * math.pi * np.cumsum(f) / SR
        x = np.sin(ph) if shape == "sine" else (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph))
        return amp * x * env_ad(n, 0.004, d or dur * 0.6)

    def lowpass(x, fc):
        a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s = 0.0
        for i, v in enumerate(x): s = a * s + (1 - a) * v; y[i] = s
        return y

    def thump(amp, dur=0.09, f=85.0, click=0.3):
        n = int(dur * SR); t = np.arange(n) / SR
        body = np.sin(2 * math.pi * f * t * (1 - 0.3 * t / dur)) * np.exp(-t / (dur * 0.35))
        nz = lowpass(_rng.normal(0, 1, n), 1800) * np.exp(-t / 0.012) * click
        return amp * (body + nz)

    def clank(amp, dur=0.25):
        n = int(dur * SR); t = np.arange(n) / SR
        return amp * sum(w * np.sin(2 * math.pi * f * t) * np.exp(-t / dd) for f, w, dd in ((820, 1.0, 0.09), (1310, 0.6, 0.06), (2170, 0.35, 0.04)))

    out = []

    def add(t, x): out.append((t, x))
    s = strength; k = kind
    if k == "step": add(0, thump(0.22 * (0.4 + 0.6 * min(s, 1.0)), f=95.0))
    elif k == "step_turn": add(0, thump(0.10, f=110.0, click=0.2))
    elif k == "takeoff": add(0, tone(320, 700, 0.12, 0.06, shape="buzz"))
    elif k == "land":
        v = min(s / 3.0, 1.0); add(0, thump(0.25 + 0.45 * v, dur=0.14, f=70.0, click=0.5)); add(0, clank(0.05 + 0.10 * v))
    elif k == "beep_yes": add(0, tone(880, 880, 0.08, 0.16)); add(0.11, tone(1175, 1175, 0.10, 0.16))
    elif k == "beep_no": add(0, tone(700, 660, 0.09, 0.16)); add(0.13, tone(480, 440, 0.12, 0.16))
    elif k == "beep_surprise": add(0, tone(600, 1900, 0.14, 0.20)); add(0.17, tone(1900, 1900, 0.05, 0.12))
    elif k == "beep_happy":
        for i, f in enumerate((1047, 1319, 1568, 2093)): add(0.075 * i, tone(f, f, 0.07, 0.13))
    elif k == "beep_think": add(0, tone(520, 520, 0.05, 0.08))
    elif k == "beep_question": add(0, tone(520, 560, 0.10, 0.13)); add(0.14, tone(600, 980, 0.22, 0.14))
    elif k == "beep_hello": add(0, tone(784, 784, 0.10, 0.13)); add(0.13, tone(1047, 1047, 0.18, 0.13))
    elif k == "power_down": add(0, tone(900, 180, 1.1, 0.10, d=0.8))
    elif k == "boot": add(0, tone(220, 1100, 0.35, 0.10, d=0.3)); add(0.38, tone(1319, 1319, 0.12, 0.12))
    elif k == "beep_present": add(0, tone(988, 988, 0.11, 0.14)); add(0.15, tone(1319, 1319, 0.16, 0.14))
    elif k == "ding":
        n = int(0.9 * SR); tt = np.arange(n) / SR
        add(0, 0.16 * sum(w * np.sin(2 * math.pi * f * tt) * np.exp(-tt / d) for f, w, d in ((1568, 1.0, 0.35), (3136, 0.4, 0.15), (4700, 0.2, 0.08))))
    elif k == "sigh":
        n = int(0.95 * SR); tt = np.arange(n) / SR
        nz = lowpass(_rng.normal(0, 1, n), 2500) * np.sin(math.pi * tt / 0.95) ** 2 * 0.10
        add(0, nz + tone(420, 230, 0.95, 0.07, d=0.6))
    elif k == "zoom": add(0, tone(900, 1400, 0.25, 0.05, shape="buzz"))
    elif k == "cradle_out": add(0, tone(180, 260, 0.5, 0.05, d=0.4, shape="buzz"))
    elif k == "cradle_in": add(0, tone(260, 170, 0.6, 0.05, d=0.5, shape="buzz"))
    elif k == "unload": add(0, tone(110, 150, 1.0, 0.06, d=0.8, shape="buzz"))
    elif k == "rub":   # すりすり（6本目で足した。こすれる柔らかい音）
        n = int(0.18 * SR); tt = np.arange(n) / SR
        add(0, lowpass(_rng.normal(0, 1, n), 2200) * np.sin(math.pi * tt / 0.18) ** 2 * 0.07 * min(s, 1.0))
    else: return None
    L = max(int(t * SR) + len(x) for t, x in out); y = np.zeros(L, np.float32)
    for t, x in out: i = int(t * SR); y[i:i + len(x)] += x.astype(np.float32)
    return y
