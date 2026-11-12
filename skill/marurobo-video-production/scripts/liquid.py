# 液体を注ぐ音（2026-11-09 ユーザー：白い絵の具を入れる音が、液体を入れる音に聞こえない）
#   注ぐ音の正体は「水の中にできる小さな泡が鳴る音」の集まり（van den Doel の泡のモデル）：
#     泡の半径 r（mm）→ 高さ f0 ≈ 3000/r Hz、減衰 d = 0.043·f0 + 0.0014·f0^1.5（/秒）、鳴りながら少し高くなる（σ = 0.1·d）
#   ＋ 流れが水面に当たる「サー」（高めの雑音を細かく揺らす）
#   ＋ コップにたまるほど、中の空気の柱が短くなって高く鳴る（共鳴の高さが上がる）＝ 注いでいると分かる手がかり
import math
import numpy as np


def _bandnoise(n, sr, lo, hi, rng):
    x = rng.normal(0, 1, n); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / sr)
    g = np.clip((f - lo * 0.7) / (lo * 0.3), 0, 1) * np.clip((hi * 1.3 - f) / (hi * 0.3), 0, 1)
    return np.fft.irfft(X * g, n)


def _smooth_noise(n, sr, fc, rng):
    k = max(1, int(sr / fc)); x = rng.normal(0, 1, n // k + 3)
    return np.interp(np.arange(n) / k, np.arange(len(x)), x)


def _resonator(x, sr, fc, q):
    """高さが時間で変わる共鳴（2 次の帯域フィルタ）。fc は各サンプルの中心の高さ"""
    y = np.zeros_like(x); y1 = y2 = 0.0; x1 = x2 = 0.0
    for i in range(len(x)):
        w = 2 * math.pi * fc[i] / sr; al = math.sin(w) / (2 * q); c = math.cos(w); a0 = 1 + al
        b0, b2, a1, a2 = al / a0, -al / a0, -2 * c / a0, (1 - al) / a0
        yi = b0 * x[i] + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, x[i]; y2, y1 = y1, yi; y[i] = yi
    return y


def pour(dur=2.3, sr=48000, seed=0, rate=(70, 160), r_mm=(1.0, 6.5), fill=0.40, f_cav=(520.0, 1250.0)):
    rng = np.random.default_rng(seed); n = int(dur * sr); t = np.arange(n) / sr
    bub = np.zeros(n); tt = 0.0
    while True:                                                         # 1) 泡（ポアソン過程。注ぎ始めはすぐ多くなる）
        u = tt / dur; lam = rate[0] + (rate[1] - rate[0]) * min(u * 4, 1.0)
        tt += rng.exponential(1.0 / lam)
        if tt >= dur - 0.03: break
        r = r_mm[0] * (r_mm[1] / r_mm[0]) ** (rng.random() ** 1.7) * (1.0 - fill * tt / dur)   # 小さい泡ほど多い。たまるほど小さく（高く）
        f0 = 3000.0 / r; d = 0.043 * f0 + 0.0014 * f0 ** 1.5; sig = 0.1 * d
        L = min(int(6.0 / d * sr), int(0.15 * sr)); tb = np.arange(L) / sr
        g = (r / 3.0) ** 1.2 * (0.45 + 0.55 * rng.random()) * np.sin(2 * math.pi * f0 * (tb + 0.5 * sig * tb * tb)) * np.exp(-d * tb) * (1 - np.exp(-tb / 0.0007))
        i0 = int(tt * sr); m = min(L, n - i0); bub[i0:i0 + m] += g[:m]
    am = np.clip(0.7 + 0.35 * _smooth_noise(n, sr, 35.0, rng), 0.25, 1.4)    # 2) 流れの「サー」（細かく揺れる）
    stream = _bandnoise(n, sr, 1800.0, 7000.0, rng) * am
    fc = f_cav[0] + (f_cav[1] - f_cav[0]) * (t / dur) ** 0.8                 # 3) たまるほど高くなる共鳴
    cav = _resonator(_bandnoise(n, sr, 200.0, 4000.0, rng) * am, sr, fc, 6.0)
    bub /= max(np.sqrt((bub ** 2).mean()), 1e-9); stream /= max(np.sqrt((stream ** 2).mean()), 1e-9); cav /= max(np.sqrt((cav ** 2).mean()), 1e-9)
    x = 1.0 * bub + 0.30 * stream + 0.45 * cav
    env = np.clip(np.minimum(t / 0.06, (dur - t) / 0.25), 0.0, 1.0)         # すっと入り、注ぎ終わりは少しずつ
    x = x * env
    return x / max(np.sqrt((x ** 2).mean()), 1e-9)                          # 大きさ（RMS）を 1 にそろえて返す


if __name__ == "__main__":
    import wave, sys
    sr = 48000; y = pour(seed=1) + 0.9 * pour(seed=2)
    y = y / np.abs(y).max() * 0.7
    with wave.open(sys.argv[1] if len(sys.argv) > 1 else "pour_test.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype(np.int16).tobytes())
