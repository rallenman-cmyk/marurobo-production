# 会話と広告の回：絵コンテのアニマティック（場面ごとの静止画を声の時刻に並べ、声に合わせた字幕を重ねる）
# MARU_WORK=<作業フォルダ> python3 animatic.py <フォントのフォルダ> <出力.mp4>
#   絵：storyboard/board/bXX_nosub.png（場面 S00〜S22 の 1 枚）。場面の最初の声の 0.4 秒前に切り替える
#   字幕：subs_jp.expand（25 字・2 行・声の間で分ける）。声：placement.json の時刻に置いた声（-20 dBFS にそろえる）
import os, sys, json, wave, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ["MARU_WORK"]
sys.path.insert(0, W + "/tools")
import subs_jp as SJ
FONTS, OUT = sys.argv[1], sys.argv[2]
V = W + "/stage/voice/achernar"
P = json.load(open(V + "/placement.json", encoding="utf-8"))
L = {e["no"]: e for e in json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))}
END = P[-1]["end"] + 2.0
tmp = W + "/animatic_tmp"; os.makedirs(tmp, exist_ok=True)

# 絵の並び
scenes = []
for p in P:
    sc = L[p["no"]]["scene"]
    if not scenes or scenes[-1][0] != sc:
        scenes.append([sc, max(0.0, p["start"] - 0.4)])
lst = []
for i, (sc, t0) in enumerate(scenes):
    t1 = scenes[i + 1][1] if i + 1 < len(scenes) else END
    img = os.path.join(HERE, "..", "storyboard", "board", "b%02d_nosub.png" % int(sc[1:]))
    lst.append("file '%s'\nduration %.3f" % (img, t1 - t0))
lst.append("file '%s'" % img)
open(tmp + "/list.txt", "w").write("\n".join(lst) + "\n")

# 声
sr = 24000
mix = np.zeros(int(END * sr), np.float32)
for p in P:
    with wave.open(V + "/line_%03d.wav" % p["no"]) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    r = np.sqrt((x ** 2)[np.abs(x) > 0.01].mean() + 1e-12)
    x *= 10 ** (-20 / 20) / r
    i = int(p["start"] * sr)
    mix[i:i + len(x)] += x[:len(mix) - i]
# 合言葉（声に出さない）の所の「ピー」：その文の 1.6 秒前から 0.7 秒（1 kHz・小さめ）
for p in P:
    if L[p["no"]]["id"] in ("08-08", "08-11"):
        i = int((p["start"] - 1.6 + 0.3) * sr); n = int(0.7 * sr)
        b = 0.12 * np.sin(2 * np.pi * 1000 * np.arange(n) / sr)
        f = int(0.01 * sr); b[:f] *= np.linspace(0, 1, f); b[-f:] *= np.linspace(1, 0, f)
        mix[i:i + n] += b
mix /= max(1.0, np.abs(mix).max() / 0.89)
with wave.open(tmp + "/voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())

# 字幕（声の終わり +0.35 秒、次の字幕の 0.05 秒前まで）
lines = []
for k, p in enumerate(P):
    nxt = P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.0
    lines.append((p["start"], min(max(p["end"] + 0.35, p["start"] + 1.0), nxt - 0.05), p["text"]))
ev = SJ.expand(lines)
def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
style = SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP")
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       style, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, t in ev:
    ass.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(a), ts(c), t.replace("\n", "\\N")))
open(tmp + "/subs.ass", "w", encoding="utf-8").write("\n".join(ass) + "\n")
json.dump(ev, open(os.path.join(HERE, "subs_events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp + "/list.txt", "-i", tmp + "/voice.wav",
                "-vf", "scale=1280:720,fps=24,subtitles=%s:fontsdir=%s" % (tmp + "/subs.ass", FONTS),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "64k", "-shortest", OUT], check=True)
print("字幕 %d 枚・絵 %d 場面・%.1f 秒 → %s（%.1f MB）" % (len(ev), len(scenes), END, OUT, os.path.getsize(OUT) / 1e6))
