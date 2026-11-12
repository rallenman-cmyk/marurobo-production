# 第5章（台本 v2：本編 426.98〜654.96 秒）の確認用動画：図（ch05_diagram.py）＋ナレーションの字幕（声は未収録）＋効果音
# 使い方: python3 ch05_assemble.py OUT_DIR   （OUT_DIR/ch05/c_%04d.png がなければ描く）→ OUT_DIR/ch05_v2.mp4（v2：荷物は光の道を通り、壊れたら落ちる）
import sys, os, json, math, wave, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ch05_diagram as c5

OUT = sys.argv[1]; FPS = 24; SR = 48000
FONTS = os.path.join(HERE, "..", "av", "fonts")
SRT = os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")                         # 声に合わせた字幕
T0, T1 = c5.T_A, c5.T_B; T = T1 - T0; N = int(round(T * FPS))
SEQ = os.path.join(OUT, "ch05"); os.makedirs(SEQ, exist_ok=True)

# ---------------------------------------------------------------- 絵（できているコマは飛ばす）
for i in range(N):
    fp = os.path.join(SEQ, "c_%04d.png" % (i + 1))
    if os.path.exists(fp) and "--redo" not in sys.argv: continue
    c5.frame(T0 + i / FPS).save(fp, compress_level=1)
print("frames", N, flush=True)


# ---------------------------------------------------------------- 字幕
def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def srt_lines(path):
    out = []
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        L = b.split("\n")
        if len(L) < 3 or " --> " not in L[1]: continue
        def sec(x):
            h, m, r = x.strip().split(":"); s_, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(s_) + int(ms) / 1000
        a, c = L[1].split(" --> "); out.append((sec(a), sec(c), " ".join(L[2:])))
    return out


def wrap_jp(txt, n=26):
    if len(txt) <= n: return txt
    cands = [i + 1 for i, ch in enumerate(txt[:-1]) if ch in "、。" and 6 <= i + 1 <= len(txt) - 4]
    cut = min(cands, key=lambda i: abs(i - len(txt) / 2)) if cands else len(txt) // 2
    return txt[:cut] + "\\N" + txt[cut:]


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Main,Noto Sans CJK JP,36,&H00FFFFFF,&H00FFFFFF,&H00302418,&H64000000,-1,0,0,0,100,100,0,0,1,3.2,0,2,60,60,30,1",
       "Style: Note,Noto Sans CJK JP,18,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,3,6,0,9,0,24,18,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
ass.append("Dialogue: 0,%s,%s,Note,,0,0,0,,第5章 v2（台本 v2：7:07〜10:55）動きの確認用・声は Gemini（Achernar）" % (ts(0), ts(T)))
for a, b, txt in srt_lines(SRT):
    if b <= T0 or a >= T1: continue
    ass.append("Dialogue: 1,%s,%s,Main,,0,0,0,,{\\fad(120,120)}%s" % (ts(max(a, T0) - T0), ts(min(b, T1) - T0), wrap_jp(txt)))
if os.environ.get("MARU_FINAL") == "1": ass = [l_ for l_ in ass if ",Note,," not in l_ and ",Shot,," not in l_]   # 本番（MARU_FINAL=1）：確認用の札（場面名・注記）を出さない
open(os.path.join(OUT, "ch05_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 効果音（図の出来事から）
Nn = int(T * SR); mix = np.zeros(Nn, np.float32); rng = np.random.default_rng(5)


def add(at, s, g=1.0):
    i0 = int((at - T0) * SR)
    if i0 < 0 or i0 >= Nn: return
    m = min(len(s), Nn - i0); mix[i0:i0 + m] += s[:m] * g


def tone(fs, dur, tau, amp=1.0):
    tt = np.arange(int(dur * SR)) / SR
    return sum(np.sin(2 * math.pi * f * tt) * a for f, a in fs) * np.exp(-tt / tau) * (1 - np.exp(-tt / 0.004)) * amp


def noise(dur, tau, lp=0.0):
    x = rng.normal(0, 1, int(dur * SR)); tt = np.arange(len(x)) / SR
    if lp: k = int(SR / lp); x = np.convolve(x, np.ones(k) / k, mode="same")
    return x * np.exp(-tt / tau)


SND = dict(send=lambda: tone([(880, 0.5), (1320, 0.2)], 0.07, 0.02) * 0.18,
           ok=lambda: np.concatenate([tone([(1175, 0.5)], 0.07, 0.04), tone([(1568, 0.5)], 0.18, 0.08)]) * 0.28,
           bad=lambda: (tone([(196, 0.7), (233, 0.5)], 0.30, 0.10) + noise(0.30, 0.08, 1200) * 0.18) * 0.45,
           clash=lambda: (noise(0.35, 0.10, 2500) * 0.6 + tone([(330, 0.5), (349, 0.5)], 0.35, 0.12)) * 0.45,
           switch=lambda: tone([(2200, 0.5), (3300, 0.2)], 0.04, 0.008) * 0.22,
           appear=lambda: tone([(660, 0.5), (990, 0.25)], 0.16, 0.05) * 0.25,
           close=lambda: (noise(0.12, 0.02, 1500) * 0.5 + tone([(260, 0.6)], 0.12, 0.03)) * 0.35)
for f in c5.FL:                                                    # v2：荷物は光の道を通り、壊れた所で落ちる（音もその時刻に）
    t0, who, res, dur = f["t0"], f["who"], f["res"], f["dur"]
    many = t0 >= c5.T_MANY
    if who == "nb" and many: continue                              # 隣の組の荷物の音は出さない（多すぎる）
    add(t0, SND["send"](), 0.6 if many else 1.0)
    if who != "me": continue
    if res == "ok": add(t0 + dur, SND["ok"](), 0.5 if many else 1.0)
    elif res == "clash": add(t0 + dur * c5.U_FAIL["clash"], SND["clash"]())
    else: add(t0 + dur * c5.U_FAIL[res], SND["bad"]())
for t_ in (c5.T_COL_IN, c5.T_SAME, c5.T_THREE, c5.T_FREQ, c5.T_MANY, c5.T_NB_BACK, c5.T_SHARE): add(t_, SND["appear"]())
for t_ in (c5.T_PH_MOVE, c5.T_BOTH, c5.T_NEXT1, c5.T_NEXT2): add(t_, SND["switch"]())
add(c5.T_AFH_CLOSE, SND["close"]())
room = noise(T, 1e9, 200) * 0.003; mix += room[:Nn]
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import narration as NAR
mix = NAR.mix_voice(mix, T0, SR, bus_peak=0.45, duck_db=4.0).astype(np.float32)
wav = os.path.join(OUT, "ch05_audio.wav")
with wave.open(wav, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
mp4 = os.path.join(OUT, "ch05_v2_voice.mp4")                                   # 声入り
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(SEQ, "c_%04d.png"), "-i", wav,
                "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch05_subs.ass"), FONTS),
                "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], check=True)
print("WROTE", mp4)
