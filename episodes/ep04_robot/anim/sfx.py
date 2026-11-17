# ロボットではありません回の効果音（3本目の sfx.py に、この回の音を足す）
#   click：マウスのカチッ／down：しょんぼり（下がる電子音）／そのほか（step・jump・land・pi・pop_ui など）は 3本目と同じ
import os, importlib.util
import numpy as np
_sp = importlib.util.spec_from_file_location("sfx_ep03", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ep03_ad", "anim", "sfx.py"))
S3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S3)


def make(kind, sr=48000):
    if kind == "click":   # 乾いた短い 2 つの音（押す・離す）
        a = S3._mx(S3._noise(0.025, sr, 2000, 9000, a=0.0005, d=0.004), 0.5 * S3._tone(2600, 2400, 0.02, sr, a=0.0005, d=0.004))
        return 0.5 * np.concatenate([a, np.zeros(int(0.07 * sr)), 0.6 * a])
    if kind == "down":
        return 0.22 * S3._tone(700, 350, 0.45, sr, a=0.02, d=0.3)
    if kind in MARU_BEEPS: return _maru_beep(kind, sr)
    return S3.make(kind, sr)


# ---- まるロボの電子音（2026-11-17 本物のまるロボに替えたとき。1本目 ep01/stage/maru/maru_reel_assemble.py と同じ作り。
#      references/maru_motions.md の「音」。marumotion の予定の events の種類の名前のまま）
MARU_BEEPS = ("beep_yes", "beep_no", "beep_surprise", "beep_happy", "beep_think", "beep_question", "beep_hello", "beep_present", "ding", "sigh", "zoom")


def _env_ad(n, sr, a=0.004, d=0.08):
    t = np.arange(n) / sr; return np.minimum(t / a, 1.0) * np.exp(-np.maximum(t - a, 0) / d)


def _tone(f0, f1, dur, amp, sr, d=None, shape="sine"):
    import math
    n = int(dur * sr); t = np.arange(n) / sr; f = f0 + (f1 - f0) * t / dur
    ph = 2 * math.pi * np.cumsum(f) / sr
    x = np.sin(ph) if shape == "sine" else (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph))
    return amp * x * _env_ad(n, sr, 0.004, d or dur * 0.6)


def _at(parts, sr):
    """[(秒, 音)] を 1 本にする"""
    n = max(int(t * sr) + len(x) for t, x in parts); out = np.zeros(n)
    for t, x in parts: i = int(t * sr); out[i:i + len(x)] += x
    return out


def _maru_beep(k, sr):
    import math
    T = lambda *a, **kw: _tone(*a, sr=sr, **kw)
    if k == "beep_yes": return _at([(0, T(880, 880, 0.08, 0.16)), (0.11, T(1175, 1175, 0.10, 0.16))], sr)
    if k == "beep_no": return _at([(0, T(700, 660, 0.09, 0.16)), (0.13, T(480, 440, 0.12, 0.16))], sr)
    if k == "beep_surprise": return _at([(0, T(600, 1900, 0.14, 0.20)), (0.17, T(1900, 1900, 0.05, 0.12))], sr)
    if k == "beep_happy": return _at([(0.075 * i, T(f, f, 0.07, 0.13)) for i, f in enumerate((1047, 1319, 1568, 2093))], sr)
    if k == "beep_think": return T(520, 520, 0.05, 0.08)
    if k == "beep_question": return _at([(0, T(520, 560, 0.10, 0.13)), (0.14, T(600, 980, 0.22, 0.14))], sr)
    if k == "beep_hello": return _at([(0, T(784, 784, 0.10, 0.13)), (0.13, T(1047, 1047, 0.18, 0.13))], sr)
    if k == "beep_present": return _at([(0, T(988, 988, 0.11, 0.14)), (0.15, T(1319, 1319, 0.16, 0.14))], sr)
    if k == "ding":
        n = int(0.9 * sr); tt = np.arange(n) / sr
        return 0.16 * sum(w * np.sin(2 * math.pi * f * tt) * np.exp(-tt / d) for f, w, d in ((1568, 1.0, 0.35), (3136, 0.4, 0.15), (4700, 0.2, 0.08)))
    if k == "sigh":
        n = int(0.95 * sr); tt = np.arange(n) / sr; rng = np.random.default_rng(3)
        nz = np.convolve(rng.normal(0, 1, n), np.ones(8) / 8, "same") * np.sin(math.pi * tt / 0.95) ** 2 * 0.10
        return nz + T(420, 230, 0.95, 0.07, d=0.6)
    if k == "zoom": return T(900, 1400, 0.25, 0.05, shape="buzz")
