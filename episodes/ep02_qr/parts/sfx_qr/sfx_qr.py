# QRコード回の効果音の部品（48kHz・モノラル・float32 の numpy 配列）。確認用動画と本番の組み立ての両方で使う
#   python3 sfx_qr.py → 1つずつの wav と、全部を並べた試聴用 preview.wav を書き出す
#   決まり：同じ音は同じ大きさ（ここで決めた amp のまま使う）。大事な音は声と重ねない（置く側で 0.6〜0.7 秒あける）
import math, os, wave
import numpy as np
SR = 48000
_rng = np.random.default_rng(7)
def _t(d): return np.arange(int(d * SR)) / SR
def _lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s = a * s + (1 - a) * v; y[i] = s
    return y
def _hp(x, fc): return x - _lp(x, fc)
def _env(n, att=0.004, rel=0.08):
    t = np.arange(n) / SR; return np.minimum(t / max(att, 1e-4), 1.0) * np.exp(-t / rel)
def norm(x, peak): m = np.abs(x).max() + 1e-9; return (x / m * peak).astype(np.float32)
# ---- 部品
def tile_flip(pitch=1.0):
    """マスが1枚起き上がる「カタッ」（木の板のような短い音）"""
    t = _t(0.09); n = len(t)
    body = sum(w * np.sin(2 * math.pi * f * pitch * t) * np.exp(-t / d) for f, w, d in ((520, 1.0, 0.025), (910, 0.5, 0.018), (1650, 0.25, 0.01)))
    click = _hp(_rng.normal(0, 1, n), 2500) * np.exp(-t / 0.004) * 0.6
    return norm(body + click, 0.22)
def fold(n=8, dt=0.075):
    """8マスがたたまれて箱になる：カタッが8回、少しずつ高く ＋ 最後にふたが閉まるコトン"""
    out = np.zeros(int((n * dt + 0.35) * SR), np.float32)
    for k in range(n):
        x = tile_flip(1.0 + 0.04 * k); i = int(k * dt * SR); out[i:i + len(x)] += x
    x = place(0.20); i = int(n * dt * SR + 0.05 * SR); out[i:i + len(x)] += x[:len(out) - i]
    return out
def place(amp=0.26):
    """箱を置く・ふたが閉まる「コトン」"""
    t = _t(0.16); body = np.sin(2 * math.pi * 140 * t * (1 - 0.25 * t / 0.16)) * np.exp(-t / 0.045)
    knock = sum(w * np.sin(2 * math.pi * f * t) * np.exp(-t / d) for f, w, d in ((380, 0.6, 0.03), (760, 0.3, 0.02)))
    nz = _lp(_rng.normal(0, 1, len(t)), 1800) * np.exp(-t / 0.01) * 0.4
    return norm(body + knock + nz, amp)
def lid_open(amp=0.20):
    """ふたが開く：軽いきしみ＋ポン"""
    t = _t(0.35); f = 600 + 500 * t / 0.35
    creak = np.sin(2 * math.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * math.pi * 38 * t)) * np.exp(-((t - 0.12) / 0.09) ** 2) * 0.35
    pop = np.zeros_like(t); i = int(0.22 * SR); tt = t[: len(t) - i]
    pop[i:] = np.sin(2 * math.pi * 330 * tt) * np.exp(-tt / 0.05)
    return norm(creak + pop, amp)
def drop(amp=0.30):
    """汚れ・インクのしずくが落ちる「ポトッ」（下がる音＋小さな水はね）"""
    t = _t(0.28); f = 1100 * np.exp(-t / 0.05) + 260
    bloop = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t / 0.06)
    sp = _hp(_rng.normal(0, 1, len(t)), 3000) * np.exp(-((t - 0.035) / 0.012) ** 2) * 0.5
    return norm(bloop + sp, amp)
def drops(k=12, gap=0.11, amp=0.24):
    """しずくが次々に落ちる"""
    out = np.zeros(int((k * gap + 0.3) * SR), np.float32)
    for j in range(k):
        x = drop(amp) * (0.85 + 0.3 * _rng.random()); i = int((j * gap + 0.02 * _rng.random()) * SR); out[i:i + len(x)] += x[:len(out) - i]
    return out
def chime(amp=0.18, base=880.0):
    """札・式が出る「ポン」（明るく短い）"""
    t = _t(0.35); x = sum(w * np.sin(2 * math.pi * base * m * t) * np.exp(-t / d) for m, w, d in ((1, 1.0, 0.12), (2, 0.35, 0.07), (3, 0.15, 0.05)))
    return norm(x * _env(len(t), 0.003, 1.0), amp)
def gather(dur=2.2, amp=0.16):
    """予備の箱から光の線が集まる：上がっていくきらきら"""
    t = _t(dur); out = np.zeros(len(t))
    for k in range(18):
        t0 = dur * 0.85 * k / 18; f = 900 * 2 ** (k / 12)
        tt = np.clip(t - t0, 0, None); out += (t >= t0) * np.sin(2 * math.pi * f * tt) * np.exp(-tt / 0.12) * 0.5
    swell = _lp(_rng.normal(0, 1, len(t)), 2500) * np.minimum(t / dur, 1) ** 2 * 0.15
    return norm(out + swell, amp)
def assemble(amp=0.20):
    """箱が組み上がる「シャラン」"""
    return norm(chime(1.0, 660)[: int(0.35 * SR)] + 0.6 * np.pad(chime(1.0, 990), (int(0.06 * SR), 0))[: int(0.35 * SR)], amp)
def meter_tick(amp=0.12):
    """メーターの目盛りが1つ埋まる「ピッ」"""
    t = _t(0.06); return norm(np.sin(2 * math.pi * 1500 * t) * _env(len(t), 0.002, 0.02), amp)
def overflow(amp=0.18):
    """メーターがあふれる「ブブー」（やさしめ）"""
    t = _t(0.55); f = 220; sq = np.sign(np.sin(2 * math.pi * f * t)) * 0.4 + np.sin(2 * math.pi * f * 1.5 * t) * 0.3
    gate = ((t % 0.27) < 0.22).astype(float); return norm(_lp(sq, 1600) * gate * _env(len(t), 0.005, 0.5), amp)
def beam(dur=0.6, amp=0.12):
    """目の光が伸びる「スーッ」"""
    t = _t(dur); nz = _rng.normal(0, 1, len(t)); x = _hp(_lp(nz, 6000), 1200) * np.sin(math.pi * t / dur) ** 2
    return norm(x + 0.3 * np.sin(2 * math.pi * (1200 + 600 * t / dur) * t) * np.sin(math.pi * t / dur), amp)
def step(amp=0.10, soft=1.0):
    """まるロボの足音（小さく軽い。マスの上なので少し固い）"""
    t = _t(0.07); body = np.sin(2 * math.pi * 210 * t) * np.exp(-t / 0.018)
    tick = _hp(_rng.normal(0, 1, len(t)), 2000) * np.exp(-t / 0.005) * 0.5 * soft
    return norm(body + tick, amp)
def hop_land(amp=0.16):
    x = place(1.0)[: int(0.12 * SR)].copy(); s = step(1.0); x[:len(s)] += s; return norm(x, amp)
LIB = {'fold': fold, 'place': place, 'lid_open': lid_open, 'drop': drop, 'drops12': drops, 'chime': chime, 'gather': gather, 'assemble': assemble,
       'meter_tick': meter_tick, 'overflow': overflow, 'beam': beam, 'step': step, 'hop_land': hop_land}
def write(path, x):
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__)); parts = []
    for k, f in LIB.items():
        x = f(); write(os.path.join(here, k + '.wav'), x); parts += [x, np.zeros(int(0.6 * SR), np.float32)]
        print(k, round(len(x) / SR, 2), 's peak', round(float(np.abs(x).max()), 2))
    write(os.path.join(here, 'preview.wav'), np.concatenate(parts))
