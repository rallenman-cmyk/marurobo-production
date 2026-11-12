# 冒頭の動き（22秒）の音：曲 → 途切れる → 電車の音 → まるロボ（跳ぶ・着地・ボタン）→ 時間が止まる
# 使い方: python3 make_audio_opening.py song.flac opening_log.json out.wav
import sys, json, wave, math, subprocess, numpy as np
SR = 48000
song_path, log_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
L = json.load(open(log_path))
DUR = 22.0; N = int(SR * DUR); t = np.arange(N) / SR
T_DROP, T_TAKE, T_LAND, T_FREEZE = L["T_DROP"], L["T_TAKE"], L["T_LAND"], L["T_FREEZE"]
T_PRESS, T_C, V_IMP, T_TURN = L["T_PRESS"], L["T_C"], L["V_IMPACT"], L["T_TURN_CAM"]
SONG_START = 20.0 - (T_DROP - 3.0)      # 主人公のうなずき（曲の20.0秒＝主人公の時間0）と拍が合う位置
rng = np.random.default_rng(11)

raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(SONG_START), "-t", str(T_DROP + 0.2), "-i", song_path, "-ac", "2", "-ar", str(SR),
                      "-f", "s16le", "-"], capture_output=True, check=True).stdout
song = np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, 2) / 32768.0
mix = np.zeros((N, 2), np.float32)
n = min(len(song), int(T_DROP * SR)); fade = np.ones(n, np.float32)
fade[-int(0.012 * SR):] = np.linspace(1, 0, int(0.012 * SR)); fade[:int(0.5 * SR)] *= np.linspace(0, 1, int(0.5 * SR))
mix[:n] += song[:n] * fade[:, None] * 0.85

# 電車の走行音（うなり＋レールの継ぎ目）
b = np.cumsum(rng.normal(0, 1, N)).astype(np.float32); b -= np.convolve(b, np.ones(4800) / 4800, mode="same")
b = np.convolve(b, np.ones(60) / 60, mode="same"); b /= np.abs(b).max() + 1e-9
amb = np.stack([b, np.roll(b, 300)], 1) * 0.55
rails = np.zeros((N, 2), np.float32)
def add(buf, at, s, pan=0.0, g=1.0):
    i = int(at * SR)
    if i >= N or i < 0: return
    m = min(len(s), N - i); l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:i + m, 0] += s[:m] * g * l; buf[i:i + m, 1] += s[:m] * g * r
def thump(f1, f2, tau, n_amp=0.15, dur=0.2):
    tt = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * math.pi * f1 * tt) * 0.8 + np.sin(2 * math.pi * f2 * tt) * 0.3) * np.exp(-tt / tau) + rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.01) * n_amp
for k0 in np.arange(0.35, DUR, 1.5):
    for d, a in ((0.0, 1.0), (0.126, 0.85), (0.83, 0.8), (0.956, 0.7)):
        add(rails, k0 + d, thump(58, 120, 0.045), 0.0, a)
train = amb * 0.28 + rails * 0.35
# 聞こえ方：曲の間は小さく、途切れた0.4秒後からふくらむ
gate = np.where(t < T_DROP, 0.25, 0.25 + 0.75 * np.clip((t - (T_DROP + 0.4)) / 1.2, 0, 1) ** 1.5)
train = train * gate[:, None]
# 時間が止まる：電車の音がテープのように0.35秒で低くなって止まる
i0 = int(T_FREEZE * SR); L_ts = int(0.35 * SR)
rate = 1 - (np.arange(L_ts) / L_ts) ** 1.6; pos = i0 + np.cumsum(rate).astype(int)
ts = train[np.clip(pos, 0, N - 1)] * (1 - np.arange(L_ts) / L_ts)[:, None]
train[i0:i0 + L_ts] = ts; train[i0 + L_ts:] = 0
mix += train

fx = np.zeros((N, 2), np.float32)
# イヤホンを押す「カチ」
tt = np.arange(int(0.03 * SR)) / SR
click = rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.002) * 0.5 + np.sin(2 * math.pi * 3200 * tt) * np.exp(-tt / 0.004) * 0.4
add(fx, T_PRESS, click, 0.4, 0.25)
# まるロボ：向きを変えるモーター音（小さく）
def servo(dur):
    tt = np.arange(int(dur * SR)) / SR; f = 520 + 260 * np.sin(math.pi * tt / dur)
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.sin(math.pi * tt / dur) * 0.10 + rng.normal(0, 1, len(tt)) * 0.01
add(fx, T_C + 0.8, servo(0.6), -0.1, 1.0); add(fx, T_TURN, servo(0.6), 0.0, 1.0)
# しゃがむ（空気が抜ける小さな音）→ 蹴る → 空中の風切り → 着地（強さは着地の速さに比例）→ ボタンのカチッ
tt = np.arange(int(0.3 * SR)) / SR
squeeze = np.convolve(rng.normal(0, 1, len(tt)), np.ones(30) / 30, mode="same") * np.sin(math.pi * tt / tt[-1]) * 0.25
add(fx, T_TAKE - 0.48, squeeze, 0.0, 0.6)
add(fx, T_TAKE, thump(140, 300, 0.03, 0.2, 0.15), 0.0, 0.5)
tt = np.arange(int((T_LAND - T_TAKE) * SR)) / SR
whoosh = np.convolve(rng.normal(0, 1, len(tt)), np.ones(12) / 12, mode="same") * np.sin(math.pi * tt / tt[-1]) * 0.18
add(fx, T_TAKE, whoosh, 0.0, 1.0)
add(fx, T_LAND, thump(150, 430, 0.06, 0.4, 0.35) * min(1.0, V_IMP / 3.0), 0.0, 0.9)
tt = np.arange(int(0.08 * SR)) / SR
btn = rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.003) * 0.6 + np.sin(2 * math.pi * 1800 * tt) * np.exp(-tt / 0.012) * 0.5
add(fx, T_LAND + 0.025, btn, 0.0, 0.9)
# 時間が止まった合図：澄んだ高い音（ゆっくり消える）
tt = np.arange(int(5.0 * SR)) / SR
shimmer = sum(np.sin(2 * math.pi * f * tt + p) for f, p in ((1568, 0), (2093, 1.1), (2637, 2.3))) / 3 * np.exp(-tt / 1.6) * (1 - np.exp(-tt / 0.02)) * 0.16
add(fx, T_FREEZE, shimmer, 0.0, 1.0)
mix += fx
mix /= max(np.abs(mix).max(), 1e-6) / 0.89
with wave.open(out, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print("audio ok", out, "song from", round(SONG_START, 2), "s")
