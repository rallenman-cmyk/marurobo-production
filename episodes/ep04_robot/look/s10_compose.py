# 見本 S10（3D）に 2D の札・字幕・声・効果音を重ねて mp4 に
# MARU_WORK=<作業> python3 s10_compose.py <3D のコマ（s10_####.png と s10_log.json）> <フォント package> <出力.mp4>
#   札は log の track（1280×720 の座標）に置く。出る時刻は字幕の切り替わりと同じ
import os, sys, json, glob, subprocess, wave
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "anim"))
import design as D
FR, FD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
D.FDIR[0] = FD; W = os.environ["MARU_WORK"]
EV = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
def said(text):
    for a, c, t in EV:
        if t.replace("\\N", "").startswith(text): return a
LG = json.load(open(os.path.join(FR, "s10_log.json")))
T0, T1, FPS, N = LG["t0"], LG["t1"], LG["fps"], LG["frames"]
TR = LG["track"]
t_y, t_who, t_res, t_fast, t_hum, t_hsec, t_wow = (said("2023年には"), said("ゆがんだ文字のテストを"), said("結果は"),
                                                  said("しかも、1問"), said("人は、正解"), said("1問に、9秒"), said("なんと"))
# 札：(sprite, track 名 or 固定の場所, ずれ, 出る時刻)
L = []
def add(spr, where, dxy, t):
    L.append((spr, where, dxy, t))
add(D.pill("2023年", 50, accent=D.ORANGE), (640, 62), (0, 0), t_y)
add(D.pill("人", 46, fg=D.WHITE, bg=D.ORANGE, tail=(0, 55)), "L_top", (0, -70), t_who)
add(D.pill("プログラム", 46, fg=D.WHITE, bg=D.TEAL, tail=(0, 55)), "R_top", (0, -70), t_who + 0.4)
add(D.pill("ほぼ全部", 40, accent=D.TEAL), "R_tube", (0, 0), t_res + 2.2)
add(D.pill("1秒未満", 40, accent=D.TEAL), "R_clock", (0, -78), t_fast)
add(D.pill("5〜8割", 40, accent=D.ORANGE), "L_tube", (0, 0), t_hum + 2.0)
add(D.pill("9〜15秒", 40, accent=D.ORANGE), "L_clock", (0, -78), t_hsec)
fs = sorted(glob.glob(os.path.join(FR, "s10_[0-9]*.png")))
ks = [int(p[-8:-4]) for p in fs]
tmp = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_s10c"); os.makedirs(tmp, exist_ok=True)
import bisect
for k in range(N):
    t = T0 + k / FPS
    j = max(0, bisect.bisect_right(ks, k) - 1)
    im = Image.open(fs[j]).convert("RGBA").resize((1280, 720), Image.LANCZOS)
    for spr, where, (dx, dy), ta in L:
        if t < ta: continue
        if isinstance(where, str):
            x, y = TR[where][min(k, N - 1)]
        else:
            x, y = where
        u = (t - ta) / 0.32; s = D.ease_out_back(u); al = D.ease(u * 1.6)
        sp, off = spr
        if abs(s - 1) > 0.004: sp = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)
        if al < 0.999:
            sp = sp.copy(); sp.putalpha(sp.split()[3].point(lambda v, al=al: int(v * al)))
        im.alpha_composite(sp, (int(x + dx + off[0] * s), int(y + dy + off[1] * s)))
    im.convert("RGB").save(os.path.join(tmp, "f_%05d.png" % k))
# 音：声＋BGM に効果音
sys.path.insert(0, "/home/user/marurobo-production/episodes/ep04_robot/anim"); import sfx
SR = 48000
r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % T0, "-t", "%.3f" % (N / FPS), "-i", W + "/animatic_tmp/voice.wav", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True)
a = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768; a = a.copy()
# 2026-11-14 ユーザー「SE があってない所がある」→ 3D の log の音は使わず、絵の動きごとに合う音を 1 つずつ決める
#   出る＝pop／考え中の点＝小さい pi／光がたまる＝rise／速い針＝whoosh／遅い針＝コチコチ（小さい click）／跳ねる＝jump・land
#   札の pop_ui は、ほかの音と 0.35 秒以内に重なるときは鳴らさない（同じ動きに音が 2 つ付かないように）
evs = [(t_who - 0.1, "pop", 0.6), (t_who + 0.3, "pop", 0.6)]
evs += [(t_res + 0.2 + j * 0.3, "pi", 0.18) for j in range(5)]
evs += [(t_res + 1.3, "rise", 0.5), (t_fast + 0.2, "whoosh", 0.35)]
evs += [(t_hum + 0.3, "rise", 0.4), (t_hum + 1.5, "rise", 0.35)]
evs += [(t_hsec + 0.2 + j * 0.33, "click", 0.25) for j in range(8)]
evs += [(t_wow + 0.1, "jump", 0.8), (t_wow + 0.55, "land", 0.8)]
for tt in (t_y, t_who, t_who + 0.4, t_res + 2.2, t_fast, t_hum + 2.0, t_hsec):
    if all(abs(tt - e[0]) > 0.35 for e in evs): evs.append((tt, "pop_ui", 0.5))
for tt, kind, g in evs:
    x = sfx.make(kind, SR)
    if x is None: continue
    i = int((tt - T0) * SR)
    if 0 <= i < len(a): a[i:i + len(x)] += (g * x)[:len(a) - i]
a /= max(1.0, np.abs(a).max() / 0.95)
wv = os.path.join(tmp, "a.wav")
with wave.open(wv, "wb") as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((a * 32767).astype(np.int16).tobytes())
sys.path.insert(0, W + "/tools"); import subs_jp as SJ
def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
rs = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
      "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
      SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP"), "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for s0, c, tx in EV:
    if c > T0 and s0 < T1: rs.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(max(0, s0 - T0)), ts(min(c, T1) - T0), tx))
ass = os.path.join(tmp, "s.ass"); open(ass, "w", encoding="utf-8").write("\n".join(rs) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", tmp + "/f_%05d.png", "-i", wv,
                "-vf", "subtitles=%s:fontsdir=%s" % (ass, FD + "/700Bold"), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-shortest", OUT], check=True)
print("COMPOSED", OUT)
