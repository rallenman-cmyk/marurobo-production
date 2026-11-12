# 見本リールの仕上げ：字幕（動きの名前と数値）と、出来事の記録から作る電子音（声は使わない：バイブル）→ mp4
# 使い方: python3 maru_reel_assemble.py OUT_DIR（reel_log.json と frames/ がある所）
import sys, os, json, math, subprocess, wave
import numpy as np

OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "av", "fonts")
log = json.load(open(os.path.join(OUT, "reel_log.json"), encoding="utf-8"))
FPS, N = log["fps"], log["frames"]; T = N / FPS
SR = 48000


def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


# ---------------------------------------------------------------- 字幕
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Name,Noto Sans CJK JP,34,&H00FFFFFF,&H00FFFFFF,&H00302418,&H78000000,-1,0,0,0,100,100,0,0,3,10,0,1,40,40,92,1",
       "Style: Detail,Noto Sans CJK JP,21,&H00F2F2F2,&H00FFFFFF,&H00302418,&H78000000,0,0,0,0,100,100,0,0,3,8,0,1,40,40,40,1",
       "Style: Head,Noto Sans CJK JP,19,&H00404040,&H00FFFFFF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,9,0,30,22,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
ass.append("Dialogue: 0,%s,%s,Head,,0,0,0,,まるロボ 動きの部品集（見本）｜物理と生体力学で計算した動き" % (ts(0), ts(T)))
for a, b, txt in log["labels"]:
    if b is None or b - a < 0.3: continue
    name, _, detail = txt.partition("｜")
    fade = "{\\fad(150,150)}"
    ass.append("Dialogue: 1,%s,%s,Name,,0,0,0,,%s%s" % (ts(a + 0.05), ts(b), fade, name))
    if detail:
        ass.append("Dialogue: 1,%s,%s,Detail,,0,0,0,,%s%s" % (ts(a + 0.05), ts(b), fade, detail))
open(os.path.join(OUT, "reel_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 電子音（出来事の時刻に置く）
audio = np.zeros(int((T + 1.0) * SR)); rng = np.random.default_rng(3)


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
    nz = lowpass(rng.normal(0, 1, n), 1800) * np.exp(-t / 0.012) * click
    return amp * (body + nz)


def clank(amp, dur=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(w * np.sin(2 * math.pi * f * t) * np.exp(-t / dd) for f, w, dd in ((820, 1.0, 0.09), (1310, 0.6, 0.06), (2170, 0.35, 0.04)))
    return amp * x


def add(t, x):
    i = int(t * SR)
    if i < 0 or i >= len(audio): return
    j = min(len(audio), i + len(x)); audio[i:j] += x[:j - i]


for e in log["events"]:
    t, k, s = e["t"], e["kind"], e["strength"]
    if k == "step": add(t, thump(0.22 * (0.4 + 0.6 * s), f=95.0))
    elif k == "step_turn": add(t, thump(0.10, f=110.0, click=0.2))
    elif k == "takeoff": add(t - 0.05, tone(320, 700, 0.12, 0.06, shape="buzz"))
    elif k == "land":
        v = min(s / 3.0, 1.0); add(t, thump(0.25 + 0.45 * v, dur=0.14, f=70.0, click=0.5)); add(t, clank(0.05 + 0.10 * v))
    elif k == "beep_yes":
        add(t, tone(880, 880, 0.08, 0.16)); add(t + 0.11, tone(1175, 1175, 0.10, 0.16))
    elif k == "beep_no":
        add(t, tone(700, 660, 0.09, 0.16)); add(t + 0.13, tone(480, 440, 0.12, 0.16))
    elif k == "beep_surprise":
        add(t, tone(600, 1900, 0.14, 0.20)); add(t + 0.17, tone(1900, 1900, 0.05, 0.12))
    elif k == "beep_happy":
        for i, f in enumerate((1047, 1319, 1568, 2093)): add(t + 0.075 * i, tone(f, f, 0.07, 0.13))
    elif k == "beep_think": add(t, tone(520, 520, 0.05, 0.08))
    elif k == "beep_question":
        add(t, tone(520, 560, 0.10, 0.13)); add(t + 0.14, tone(600, 980, 0.22, 0.14))
    elif k == "beep_hello":
        add(t, tone(784, 784, 0.10, 0.13)); add(t + 0.13, tone(1047, 1047, 0.18, 0.13))
    elif k == "power_down": add(t, tone(900, 180, 1.1, 0.10, d=0.8))
    elif k == "boot":
        add(t, tone(220, 1100, 0.35, 0.10, d=0.3)); add(t + 0.38, tone(1319, 1319, 0.12, 0.12))
    elif k == "beep_present":
        add(t, tone(988, 988, 0.11, 0.14)); add(t + 0.15, tone(1319, 1319, 0.16, 0.14))
    elif k == "ding":
        n = int(0.9 * SR); tt = np.arange(n) / SR
        add(t, 0.16 * sum(w * np.sin(2 * math.pi * f * tt) * np.exp(-tt / d) for f, w, d in ((1568, 1.0, 0.35), (3136, 0.4, 0.15), (4700, 0.2, 0.08))))
    elif k == "sigh":
        n = int(0.95 * SR); tt = np.arange(n) / SR
        nz = lowpass(rng.normal(0, 1, n), 2500) * np.sin(math.pi * tt / 0.95) ** 2 * 0.10
        add(t, nz + tone(420, 230, 0.95, 0.07, d=0.6))
    elif k == "zoom": add(t, tone(900, 1400, 0.25, 0.05, shape="buzz"))
    elif k == "cradle_out": add(t, tone(180, 260, 0.5, 0.05, d=0.4, shape="buzz"))
    elif k == "cradle_in": add(t, tone(260, 170, 0.6, 0.05, d=0.5, shape="buzz"))
    elif k == "unload": add(t, tone(110, 150, 1.0, 0.06, d=0.8, shape="buzz"))
peak = np.abs(audio).max(); audio = audio / max(peak, 1e-9) * 0.7
with wave.open(os.path.join(OUT, "reel_sfx.wav"), "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((audio * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 動画
mp4 = os.path.join(OUT, "maru_reel.mp4")
cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(OUT, "frames", "f_%04d.png"), "-i", os.path.join(OUT, "reel_sfx.wav"),
       "-vf", "hqdn3d=2:1.5:3:3,scale=1280:720:flags=lanczos,subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "reel_subs.ass"), FONTS),
       "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-18:TP=-2", "-shortest", mp4]
subprocess.run(cmd, check=True)
print("WROTE", mp4)
