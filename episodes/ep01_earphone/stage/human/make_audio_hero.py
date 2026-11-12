# 主人公の動きテストの音：曲（3秒で途切れる）→ 静けさ → 電車の音がふくらむ ＋ イヤホンを押す「カチ」
# 使い方: python3 make_audio_hero.py song.flac out.wav
import sys, wave, math, subprocess, numpy as np
SR = 48000; DUR = 8.0; N = int(SR * DUR)
T_DROP = 3.0; SONG_START = 20.0; PRESS = T_DROP + 1.32 + 0.10
song_path, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(SONG_START), "-t", "3.2", "-i", song_path, "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
song = np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, 2) / 32768.0
songpart = np.zeros((N, 2), np.float32); rails = np.zeros((N, 2), np.float32)
n = min(len(song), int(T_DROP * SR)); seg = song[:n].copy()
fade = np.ones(n, np.float32); k = int(0.012 * SR); fade[-k:] = np.linspace(1, 0, k)   # 12ms で切れる（無線が途切れる感じ）
fi = int(0.25 * SR); fade[:fi] *= np.linspace(0, 1, fi)
songpart[:n] += seg * fade[:, None] * 0.9
rng = np.random.default_rng(7)
t = np.arange(N) / SR
# 電車の走行音：低いうなり（ブラウンノイズの低域）
b = np.cumsum(rng.normal(0, 1, N)).astype(np.float32); b -= np.convolve(b, np.ones(4800) / 4800, mode="same")
b = np.convolve(b, np.ones(60) / 60, mode="same"); b /= np.abs(b).max() + 1e-9
train = np.stack([b, np.roll(b, 300)], 1) * 0.55
# レールの継ぎ目：前の台車の2軸（0.126秒差）→ 0.83秒後に後ろの台車。25mレール・時速60kmで1.5秒ごと
def thump(at, amp):
    i = int(at * SR); L = int(0.18 * SR)
    if i >= N: return
    tt = np.arange(min(L, N - i)) / SR
    s = (np.sin(2 * math.pi * 58 * tt) * 0.8 + np.sin(2 * math.pi * 120 * tt) * 0.3) * np.exp(-tt / 0.045)
    s += rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.01) * 0.15
    rails[i:i + len(tt), 0] += s * amp; rails[i:i + len(tt), 1] += s * amp * 0.92
for k0 in np.arange(0.35, DUR, 1.5):
    for d, a in ((0.0, 1.0), (0.126, 0.85), (0.83, 0.8), (0.956, 0.7)):
        thump(k0 + d, a)
# 聞こえ方：曲が鳴っている間は電車の音は小さく（イヤホンで遮られる）。途切れた0.4秒後からふくらむ
gate = np.where(t < T_DROP, 0.18, 0.18 + 0.82 * np.clip((t - (T_DROP + 0.4)) / 1.2, 0, 1) ** 1.5)
final = songpart + (rails * 0.35 + train * 0.28) * gate[:, None]
# イヤホンを押す「カチ」（硬いプラスチックの小さな音、右側）
i = int(PRESS * SR); L = int(0.03 * SR); tt = np.arange(L) / SR
click = (rng.normal(0, 1, L) * np.exp(-tt / 0.002) * 0.5 + np.sin(2 * math.pi * 3200 * tt) * np.exp(-tt / 0.004) * 0.4)
final[i:i + L, 0] += click * 0.10; final[i:i + L, 1] += click * 0.35
final /= max(np.abs(final).max(), 1e-6) / 0.89
with wave.open(out, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(final, -1, 1) * 32767).astype(np.int16).tobytes())
print("audio ok", out)
