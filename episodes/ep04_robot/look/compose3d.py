# 図の場面の 3D（kit3d.py で描いたコマ）に、2D の札を重ねる。札と効果音は labels.py に場面ごとに書く
# MARU_WORK=<作業> python3 compose3d.py <場面名> <3D のコマのフォルダ> <フォント package> <出力フォルダ> [--mp4 <見本.mp4>]
#   出力：<出力>/L<場面名>_####.png（1280×720・字幕なし）と L<場面名>_log.json（clip と同じ形。events＝効果音）
#   → assemble.py が、このクリップの時刻ではショットの絵の代わりにこれを使う
#   --mp4：声・BGM・効果音・字幕を付けた確かめ用の動画も作る
import os, sys, json, glob, subprocess, wave, bisect
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "anim"))
import design as D
NAME, FR, FD, OD = sys.argv[1:5]
MP4 = sys.argv[sys.argv.index("--mp4") + 1] if "--mp4" in sys.argv else None
D.FDIR[0] = FD; W = os.environ["MARU_WORK"]
import labels as LB
LG = json.load(open(os.path.join(FR, NAME + "_log.json")))
T0, T1, FPS, N = LG["t0"], LG["t1"], LG["fps"], LG["frames"]
TR = LG["track"]
spec = LB.SCENES[NAME]
LBL, EVS = spec["labels"](), spec["sfx"]()
if spec.get("use_log"): EVS = [tuple(e) for e in LG["events"]] + list(EVS)   # 新しい台本は、音を 3D の台本の中で決めている
# 札の pop_ui：ほかの音と 0.35 秒以内なら鳴らさない（同じ動きに音を 2 つ付けない）
evs = list(EVS)
for L_ in LBL:
    if L_.get("quiet"): continue
    if all(abs(L_["t"] - e[0]) > 0.35 for e in evs): evs.append((L_["t"], "pop_ui", 0.5))
evs.sort()
SPR = []
for L_ in LBL:
    col = {"te": D.TEAL, "or": D.ORANGE, "nv": D.NAVY2, "rd": D.RED, "gr": D.GREEN}[L_.get("col", "te")]
    if L_.get("solid"):
        spr = D.pill(L_["text"], L_.get("size", 46), fg=D.WHITE, bg=col, tail=L_.get("tail"))
    else:
        spr = D.pill(L_["text"], L_.get("size", 44), accent=None if L_.get("plain") else col, tail=L_.get("tail"))
    SPR.append(spr)
fs = sorted(glob.glob(os.path.join(FR, NAME + "_[0-9]*.png")))
ks = [int(p[-8:-4]) for p in fs]
os.makedirs(OD, exist_ok=True)
outs = []
for j, (p, k) in enumerate(zip(fs, ks)):
    t = T0 + k / FPS
    im = Image.open(p).convert("RGBA").resize((1280, 720), Image.LANCZOS)
    for L_, (sp0, off) in zip(LBL, SPR):
        ta, tb = L_["t"], L_.get("out", 1e9)
        if t < ta or t >= tb + 0.3: continue
        at = L_["at"]
        x, y = (TR[at][min(k, N - 1)] if isinstance(at, str) else at)
        dx, dy = L_.get("d", (0, 0))
        u = (t - ta) / 0.32; s = D.ease_out_back(u); al = D.ease(u * 1.6)
        if t > tb: v = (t - tb) / 0.3; al *= 1 - v; s *= 1 - 0.3 * v
        sp = sp0
        if abs(s - 1) > 0.004: sp = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)
        if al < 0.999:
            sp = sp.copy(); sp.putalpha(sp.split()[3].point(lambda v_, al=al: int(v_ * al)))
        im.alpha_composite(sp, (int(x + dx + off[0] * s), int(y + dy + off[1] * s)))
    q = os.path.join(OD, "L%s_%04d.png" % (NAME, k)); im.convert("RGB").save(q); outs.append(q)
lg2 = dict(LG); lg2["events"] = [list(e) for e in evs]; lg2["steps"] = []
json.dump(lg2, open(os.path.join(OD, "L%s_log.json" % NAME), "w"))
print("FRAMES", len(outs))
if not MP4: sys.exit()
# 確かめ用の動画：声＋BGM＋効果音＋字幕
import sfx
SR = 48000
r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % T0, "-t", "%.3f" % (N / FPS), "-i", W + "/animatic_tmp/voice.wav", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True)
a = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768; a = a.copy()
for tt, kind, g in evs:
    x = sfx.make(kind, SR)
    if x is None: print("音がない", kind); continue
    i = int((tt - T0) * SR)
    if 0 <= i < len(a): a[i:i + len(x)] += (g * x)[:len(a) - i]
a /= max(1.0, np.abs(a).max() / 0.95)
tmp = os.path.join(OD, "_mp4"); os.makedirs(tmp, exist_ok=True)
wv = os.path.join(tmp, "a.wav")
with wave.open(wv, "wb") as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((a * 32767).astype(np.int16).tobytes())
lst = os.path.join(tmp, "list.txt")
with open(lst, "w") as fo:
    for i, (q, k) in enumerate(zip(outs, ks)):
        k2 = ks[i + 1] if i + 1 < len(ks) else N
        fo.write("file '%s'\nduration %.5f\n" % (q, (k2 - k) / FPS))
    fo.write("file '%s'\n" % outs[-1])
sys.path.insert(0, W + "/tools"); import subs_jp as SJ
EV = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
rs = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
      "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
      SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP"), "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for s0, c, tx in EV:
    if c > T0 and s0 < T1: rs.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(max(0, s0 - T0)), ts(min(c, T1) - T0), tx))
ass = os.path.join(tmp, "s.ass"); open(ass, "w", encoding="utf-8").write("\n".join(rs) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wv,
                "-vf", "fps=24,subtitles=%s:fontsdir=%s" % (ass, FD + "/700Bold"), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-shortest", MP4], check=True)
print("MP4", MP4)
