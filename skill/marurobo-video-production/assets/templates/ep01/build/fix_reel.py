# 2026-11-09 夜の直し（25か所＋2）：直した所だけをつないだ確認動画（1280×720・15MB 以下）と、新しい時刻の一覧
#   使い方: python3 fix_reel.py OUT_DIR   → OUT_DIR/fix_reel_1109b.mp4、OUT_DIR/fix_list_1109b.json
#   各章の始まりは、通しと同じく本番のコマ数から数える（24fps）。区間は「章の頭からの秒」で書く
import sys, os, json, subprocess
S = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; F = S + "/stage/final"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); TMP = os.path.join(OUT, "reel_tmp"); os.makedirs(TMP, exist_ok=True)
FONTS = S + "/stage/av/fonts"; FULL = F + "/bluetooth_full_1080.mp4"
CH = [("ch0102", F + "/ch0102_final_1080.mp4"), ("ch03", F + "/ch03_final_1080.mp4"), ("ch04", F + "/ch04_final_1080.mp4"), ("ch05", S + "/stage/ch03/ch5_final/ch05_final_1080.mp4"),
      ("ch06", F + "/ch06_final_1080.mp4"), ("ch07", F + "/ch07_final_1080.mp4"), ("ch08", F + "/ch08_final_1080.mp4"), ("sum", F + "/summary_final_1080.mp4")]
st = {}; t = 0.0
for k, p in CH:
    n = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())
    st[k] = t; t += n / 24.0
def mmss(x): return "%d:%02d" % (int(x // 60), int(x % 60))
# （章, 区間の頭, 区間の終わり, 見どころ（章の頭からの秒）, 前の時刻, 何を直したか）
SEG = [("ch03", 21.5, 27.0, 24.48, "1:45", "「一つひとつに」の前に間"),
       ("ch03", 29.0, 34.4, 31.94, "1:52", "「電波の代わりに」の前に間"),
       ("ch04", 0.5, 6.5, 4.03, "2:59", "「まずは、一つ目の疑問から」は二つの疑問を並べた絵のまま"),
       ("ch04", 29.5, 35.5, 32.50, "3:28", "長かった間を 0.8 秒に"),
       ("ch04", 47.5, 53.5, 50.42, "3:49", "「自分のイヤホンが」の前に間"),
       ("ch04", 118.5, 133.5, 120.90, "5:00〜5:09", "電車へ直接切り替え・黄色のすぐ隣が緑・「十人十色です」まで電車・「このひみつの色は」の前に間"),
       ("ch04", 137.5, 145.0, 140.39, "5:19", "白い絵の具を注ぐ音（液体の音に）"),
       ("ch04", 193.0, 200.5, 196.25, "6:16", "「この紫色は」の前に間"),
       ("ch05", 30.5, 42.5, 33.87, "7:43・7:53", "長かった間を 0.8 秒に（2か所）"),
       ("ch05", 66.0, 71.5, 68.88, "8:26", "「もう少し」の前に間"),
       ("ch05", 85.5, 91.5, 88.42, "8:45", "「では、スマホだけが」の前に間"),
       ("ch05", 118.0, 131.5, 128.62, "9:26", "「このチャンネルの」までを 1 秒短く"),
       ("ch06", 2.5, 13.0, 7.00, "11:06", "六番を積んだまるロボが橋を渡って運ぶ所を差し込み（足音つき）"),
       ("ch07", 34.0, 40.5, 37.43, "12:55", "「ほら、曲は」の前に間"),
       ("ch07", 45.5, 53.5, 46.47, "12:57ごろ", "まるロボの足音（第7章・第8章の塔・天びん）"),
       ("ch07", 72.5, 78.5, 75.62, "13:33", "「バッファが」の前に間"),
       ("ch07", 146.0, 152.5, 149.06, "14:47", "「あるいは」の前に間"),
       ("ch08", 46.5, 57.5, 51.61, "15:59", "言い終えてからパンチ・「ドン」を少し大きく・次の字幕までの間を短く"),
       ("ch08", 61.0, 68.0, 64.89, "16:14", "「ドン」のあと 0.65 秒で「音だけ」"),
       ("sum", 8.5, 14.5, 10.6, "17:18", "まとめの札の「第4章」などの章の表示を消した"),
       ("sum", 38.5, 44.5, 40.6, "17:48", "まとめの札の章の表示を消した")]
LIST = []
parts = []
for j, (ch, a, b, key, old, what) in enumerate(SEG):
    s0 = st[ch] + a; d = b - a; new = st[ch] + key
    LIST.append(dict(old=old, new=mmss(new), what=what, ch=ch))
    ass = os.path.join(TMP, "l_%02d.ass" % j)
    lab = "%s → 今 %s　%s" % (old, mmss(new), what)
    open(ass, "w", encoding="utf-8").write("\n".join([
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Lab,Noto Sans CJK JP,26,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64301A10,-1,0,0,0,100,100,0,0,3,10,0,7,24,24,20,1", "",
        "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        "Dialogue: 0,0:00:00.00,0:00:%05.2f,Lab,,0,0,0,,%s" % (d, lab)]) + "\n")
    mp = os.path.join(TMP, "p_%02d.mp4" % j)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % s0, "-i", FULL, "-t", "%.3f" % d, "-vf", "scale=1280:720:flags=lanczos,subtitles=%s:fontsdir=%s" % (ass, FONTS),
                    "-af", "afade=t=in:d=0.08,afade=t=out:st=%.3f:d=0.12" % (d - 0.12), "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", "24",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", mp], check=True)
    parts.append(mp)
lst = os.path.join(TMP, "list.txt"); open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
raw = os.path.join(TMP, "reel_raw.mp4"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw], capture_output=True, text=True).stdout)
out = os.path.join(OUT, "fix_reel_1109b.mp4")
vb = int((14.2e6 * 8 / dur - 128e3) / 1000)                        # 15MB 以下になる映像の速さ（kbps）
for pas in (1, 2):
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", raw, "-c:v", "libx264", "-b:v", "%dk" % vb, "-preset", "slow", "-pass", str(pas), "-passlogfile", os.path.join(TMP, "x264"), "-pix_fmt", "yuv420p"]
    cmd += (["-an", "-f", "mp4", "/dev/null"] if pas == 1 else ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
    subprocess.run(cmd, check=True, cwd=TMP)
json.dump(dict(starts={k: round(v, 2) for k, v in st.items()}, total=round(t, 2), fixes=LIST), open(os.path.join(OUT, "fix_list_1109b.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("REEL", out, "dur %.1f" % dur, "vb %dk" % vb, "size", os.path.getsize(out))
for k in st: print("  %s %s" % (k, mmss(st[k])))
