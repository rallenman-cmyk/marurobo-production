# 3D の試し描き（--step で間引いたコマ）に、声と字幕を合わせた確認用の動画を作る
# MARU_WORK=<作業フォルダ> python3 preview.py <コマのフォルダ> <フォントのフォルダ> <出力.mp4> <舞台…（gate phone など）>
#   声：アニマティックの声（animatic_tmp/voice.wav、ピー入り）から舞台の時刻を切り出す。字幕：animatic/subs_events.json
import os, sys, json, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ["MARU_WORK"]
FRAMES, FONTS, OUT, MODES = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
ev = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
parts = []
for m in MODES:
    lg = json.load(open(os.path.join(FRAMES, m + "_log.json")))
    fs = sorted(glob.glob(os.path.join(FRAMES, m + "_*.png")))
    step = int(os.path.basename(fs[1])[len(m) + 1:-4]) - int(os.path.basename(fs[0])[len(m) + 1:-4]) if len(fs) > 1 else 1
    dur = lg["frames"] / lg["fps"]
    lst = os.path.join(FRAMES, m + "_list.txt")
    open(lst, "w").write("".join("file '%s'\nduration %.4f\n" % (p, step / lg["fps"]) for p in fs) + "file '%s'\n" % fs[-1])
    ass = os.path.join(FRAMES, m + ".ass")
    def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
    rows = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Main,Noto Sans JP,56,&H00FFFFFF,&H00FFFFFF,&H00301A10,&H96000000,-1,0,0,0,100,100,1,0,1,5,2.2,2,50,50,40,1",
            "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for a, c, t in ev:
        if c > lg["t0"] and a < lg["t0"] + dur:
            rows.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(max(0, a - lg["t0"])), ts(min(dur, c - lg["t0"])), t.replace("\n", "\\N")))
    open(ass, "w", encoding="utf-8").write("\n".join(rows) + "\n")
    out = os.path.join(FRAMES, m + "_prev.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-ss", "%.3f" % lg["t0"], "-t", "%.3f" % dur,
                    "-i", W + "/animatic_tmp/voice.wav", "-vf", "scale=1280:720,fps=24,subtitles=%s:fontsdir=%s" % (ass, FONTS),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest", out], check=True)
    parts.append(out)
lst = os.path.join(FRAMES, "all_list.txt")
open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT], check=True)
print(OUT, "%.1f MB" % (os.path.getsize(OUT) / 1e6))
