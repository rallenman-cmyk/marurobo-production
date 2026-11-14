# 3D の試し描き（--step で間引いたコマ）に、2D の層・字幕・声と BGM・効果音を合わせた確認用の動画を作る
# MARU_WORK=<作業フォルダ> python3 preview.py <3D のコマ> <2D の層（overlay_layers.py の出力）> <絵コンテのショット（shots5）> <フォント> <出力.mp4> <場面…>
#   声と BGM：アニマティックの音（animatic_tmp/voice.wav）から場面の時刻を切り出す。効果音：<場面>_log.json の events と steps
#   2D の層：ショットの切り替えはアニマティックと同じ（場面の頭は声の 0.4 秒前、場面の中は 0.15 秒前、dt）
import os, sys, json, glob, subprocess, wave
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx
W = os.environ["MARU_WORK"]
FR, LY, SH, FONTS, OUT, MODES = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6:]
FULL = {"s_op"}                                  # 3D の絵そのものに手を加えた 2D（暗くする等）は、絵コンテの絵をそのまま使う
VO = os.path.join(HERE, "..", "voice")
P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
L = {e["no"]: e for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
ID, first, prev = {}, set(), None
for p in P:
    ID.setdefault(L[p["no"]]["id"], p)
    if L[p["no"]]["scene"] != prev: first.add(L[p["no"]]["id"])
    prev = L[p["no"]]["scene"]
shots = json.load(open(os.path.join(LY, "shots.json"), encoding="utf-8"))
for s_ in shots: s_["t"] = ID[s_["id"]]["start"] - (0.4 if s_["id"] in first else 0.15) + s_.get("dt", 0.0)
shots.sort(key=lambda s_: s_["t"])
ev = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
SR = 48000
r = subprocess.run(["ffmpeg", "-v", "error", "-i", W + "/animatic_tmp/voice.wav", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True)
VOICE = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
tmp = os.path.join(FR, "_prev"); os.makedirs(tmp, exist_ok=True)


def shot_at(t):
    cur = shots[0]
    for s_ in shots:
        if s_["t"] <= t + 1e-6: cur = s_
    return cur


parts = []
for m in MODES:
    lg = json.load(open(os.path.join(FR, m + "_log.json")))
    fs = sorted(glob.glob(os.path.join(FR, m + "_[0-9]*.png")))
    ks = [int(os.path.basename(p)[len(m) + 1:-4]) for p in fs]
    step = ks[1] - ks[0] if len(ks) > 1 else 1
    t0, fps, n = lg["t0"], lg["fps"], lg["frames"]
    rows = []
    for p, k in zip(fs, ks):
        t = t0 + k / fps; s_ = shot_at(t); name = s_["img"][:-4]
        if s_.get("base") and name not in FULL:
            im = Image.open(p).convert("RGB").resize((1280, 720), Image.LANCZOS).convert("RGBA")
            im.alpha_composite(Image.open(os.path.join(LY, s_["img"])).convert("RGBA"))
        else:
            im = Image.open(os.path.join(SH, s_["img"])).convert("RGBA")
        q = os.path.join(tmp, "%s_%04d.png" % (m, k)); im.convert("RGB").save(q); rows.append(q)
    lst = os.path.join(tmp, m + "_list.txt")
    open(lst, "w").write("".join("file '%s'\nduration %.4f\n" % (q, step / fps) for q in rows) + "file '%s'\n" % rows[-1])
    dur = n / fps
    # 音：声と BGM ＋ 効果音
    a = VOICE[int(t0 * SR):int(t0 * SR) + int(dur * SR)].copy()
    hits = [(t, k, g) for t, k, g in lg["events"]] + [(t, "step", 0.6) for t in lg["steps"]]
    for t, k, g in hits:
        x = sfx.make(k, SR)
        if x is None: print("効果音がない", k); continue
        i = int((t - t0) * SR)
        if 0 <= i < len(a): a[i:i + len(x)] += (g * x)[:len(a) - i]
    a /= max(1.0, np.abs(a).max() / 0.95)
    wv = os.path.join(tmp, m + ".wav")
    with wave.open(wv, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())
    def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
    rs = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
          "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
          "Style: Main,Noto Sans JP,56,&H00FFFFFF,&H00FFFFFF,&H00301A10,&H96000000,-1,0,0,0,100,100,1,0,1,5,2.2,2,50,50,40,1",
          "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for a_, c_, tx in ev:
        if c_ > t0 and a_ < t0 + dur:
            rs.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(max(0, a_ - t0)), ts(min(dur, c_ - t0)), tx.replace("\n", "\\N")))
    ass = os.path.join(tmp, m + ".ass"); open(ass, "w", encoding="utf-8").write("\n".join(rs) + "\n")
    out = os.path.join(tmp, m + "_prev.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wv,
                    "-vf", "fps=24,subtitles=%s:fontsdir=%s" % (ass, FONTS), "-t", "%.3f" % dur,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", out], check=True)
    parts.append(out)
lst = os.path.join(tmp, "all_list.txt")
open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
print(OUT, "%.1f MB" % (os.path.getsize(OUT) / 1e6))
