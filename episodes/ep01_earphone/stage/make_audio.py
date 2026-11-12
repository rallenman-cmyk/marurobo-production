# 30秒サンプルの音：曲（Codex版の曲を流用）＋ 動きの記録から合成した効果音
# 使い方: python3 make_audio.py motion_log.json song.wav out.wav
import json, sys, wave, math
import numpy as np

SR = 48000; DUR = 30.0; N = int(SR * DUR)
log_path, song_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
j = json.load(open(log_path)); rng = np.random.default_rng(42)

def load_wav(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        return a.reshape(-1, w.getnchannels())
song = load_wav(song_path)[:N]
if song.shape[0] < N: song = np.pad(song, ((0, N - song.shape[0]), (0, 0)))
fade = np.clip(np.arange(N) / (0.3 * SR), 0, 1) * np.clip((N - np.arange(N)) / (0.8 * SR), 0, 1)
mix = song * 0.55 * fade[:, None]

def env(n, tau): t = np.arange(n) / SR; return np.exp(-t / tau)
def add(t0, mono, pan=0.0, gain=1.0):
    i0 = int(t0 * SR); n = min(len(mono), N - i0)
    if n <= 0: return
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)  # 等パワーの定位
    mix[i0:i0 + n, 0] += mono[:n] * gain * l; mix[i0:i0 + n, 1] += mono[:n] * gain * r

def thud(v):  # 箱の着地：強さは着地の速さに比例（中空の金属ケース）
    n = int(0.35 * SR); t = np.arange(n) / SR
    body = 0.6 * np.sin(2 * np.pi * 150 * t) * env(n, 0.09) + 0.35 * np.sin(2 * np.pi * 430 * t) * env(n, 0.05)
    click = rng.normal(0, 1, n) * env(n, 0.006) * 0.5
    return (body + click) * min(1.0, v / 6.0)
def clack(strength, low=False):  # 扉の開閉
    n = int(0.25 * SR); t = np.arange(n) / SR; f = 900 if not low else 520
    s = rng.normal(0, 1, n) * env(n, 0.012) * 0.6 + np.sin(2 * np.pi * f * t) * env(n, 0.03) * 0.4
    if not low:
        w = np.sin(2 * np.pi * (400 * t + 900 * t * t)) * np.clip(1 - t / 0.12, 0, 1) * 0.15  # 小さなモーター音
        s += w
    return s * strength
def step(v):  # 足音（金属の通路をゴムの足で踏む）
    n = int(0.12 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 190 * t) * env(n, 0.03) * 0.5 + rng.normal(0, 1, n) * env(n, 0.008) * 0.25) * min(1.0, v / 1.3)
def scrape(dur):  # 荷台を滑る音
    n = int(dur * SR); x = rng.normal(0, 1, n); y = np.convolve(x, np.ones(24) / 24, mode="same")
    ramp = np.clip(np.arange(n) / n, 0, 1) ** 1.5
    return y * ramp * 0.5
def chirp_sigh():  # まるロボの「ほっ」（電子音）
    n = int(0.45 * SR); t = np.arange(n) / SR; f = 880 - 300 * (t / t[-1])
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.sin(np.pi * t / t[-1]) * 0.18

TOWER_PAN, ROBOT_PAN = 0.35, 0.0
tm = j["timing"]
for (t, kind, s, name) in j["events"]:
    if kind == "impact": add(t, thud(s), TOWER_PAN, 0.9)
    elif kind == "gate": add(t, clack(s, low=(name == "close")), TOWER_PAN, 0.5)
    elif kind == "step": add(t, step(s), -0.3 + 0.5 * min(1, max(0, (t - 7.5) / 6)), 0.35)
    elif kind == "slide_off": pass
add(tm["release"] - 0.5, scrape(0.5), 0.15, 0.35)
add(tm["relief"] + 0.05, chirp_sigh(), 0.15, 1.0)
peak = np.max(np.abs(mix)); mix = mix / max(peak, 1e-6) * 0.89
with wave.open(out_path, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print("audio ok", out_path, "peak", round(float(peak), 3))
