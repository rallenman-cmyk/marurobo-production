# ロボットではありません回：動きの入った通しを組み立てる（3D のクリップ＋2D の層、2D だけの絵、字幕、声と BGM、効果音）
# MARU_WORK=<作業フォルダ> python3 assemble.py <層のフォルダ> <絵コンテのショット（shots5）> <フォント> <出力.mp4> <3D のコマのフォルダ…>
#   3D のコマ：<名前>_####.png と <名前>_log.json（clip_anim.py・scenes.py の出力）。いくつかのフォルダから探す
#   ショットの切り替えはアニマティックと同じ。3D のショットは、その時刻を含むクリップの、いちばん近い前のコマを使う
#   声と BGM：animatic_tmp/voice.wav（animatic.py の音）。効果音：各 log の events と steps（足音）
#   点検：<出力>_check.txt（3D のコマが足りない所・効果音のない種類・効果音が声と重なる所）
import os, sys, json, glob, subprocess, wave, bisect
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx
LY, SH, FONTS, OUT, DIRS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:]
W = os.environ["MARU_WORK"]
END = float(os.environ.get("END_AT", "642.27"))
src = open(os.path.join(HERE, "preview.py"), encoding="utf-8").read()
exec(src[src.index("FULL = "):src.index("ev = json.load")])        # FULL・FOLLOW・tag・ショットの時刻（shots）
ev = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
tmp = os.path.join(W, "assemble_tmp"); os.makedirs(tmp, exist_ok=True)

# 3D のクリップ
CL = []
for d in DIRS:
    for lg in glob.glob(os.path.join(d, "*_log.json")):
        nm = os.path.basename(lg)[:-9]; L_ = json.load(open(lg))
        fs = sorted(glob.glob(os.path.join(d, nm + "_[0-9][0-9][0-9][0-9].png")))
        if not fs: continue
        ks = [int(p[-8:-4]) for p in fs]
        CL.append(dict(name=nm, t0=L_["t0"], t1=L_["t0"] + L_["frames"] / L_["fps"], fps=L_["fps"], ks=ks, fs=fs, log=L_))
CL.sort(key=lambda c: c["t0"])
def clip_at(t):
    for c in CL:
        if c["t0"] - 1e-6 <= t < c["t1"] - 1e-6: return c
    for c in CL:  # 区切りの端数（コマ数の丸め）で 1 コマ足りないときは、すぐ前のクリップの最後のコマを使う
        if c["t1"] - 1e-6 <= t < c["t1"] + 0.1: return c


def shot_i(t):
    i = 0
    for j, s_ in enumerate(shots):
        if s_["t"] <= t + 1e-6: i = j
    return i


# 並び：（始まりの時刻, 絵のファイル）。2D だけのショットは 1 枚、3D は描いたコマごと
seq, miss = [], []
fps = 24; N = round(END * fps); k = 0
cache = {}
while k < N:
    t = k / fps; si = shot_i(t); s_ = shots[si]; name = s_["img"][:-4]
    tn = shots[si + 1]["t"] if si + 1 < len(shots) else END
    if s_.get("base") and name not in FULL:
        # 絵の切り替えを字幕にそろえて動かした分（t_old との差）は、そのショットのクリップの中で、端のコマで埋める
        c = clip_at(s_["t_old"] + 0.05) or clip_at(t)
        if not c:
            miss.append(round(t, 2)); q = os.path.join(SH, s_["img"]); seq.append((t, q)); k += 1; continue
        kk = round((min(max(t, c["t0"]), c["t1"] - 1e-3) - c["t0"]) * c["fps"]); j = bisect.bisect_right(c["ks"], kk) - 1; j = max(0, j)
        key_ = (name, c["name"], c["ks"][j])
        if key_ not in cache:
            im = Image.open(c["fs"][j]).convert("RGB").resize((1280, 720), Image.LANCZOS).convert("RGBA")
            if name in FOLLOW and "maru" in c["log"].get("track", {}):
                lay, text, (cx, cy), who = FOLLOW[name]
                im.alpha_composite(Image.open(os.path.join(LY, lay + ".png")).convert("RGBA"))
                tag(im, text, cx, cy, tuple(c["log"]["track"][who][min(c["ks"][j], len(c["log"]["track"][who]) - 1)]))
            else:
                im.alpha_composite(Image.open(os.path.join(LY, s_["img"])).convert("RGBA"))
            q = os.path.join(tmp, "%s__%s_%04d.png" % (name, c["name"], c["ks"][j])); im.convert("RGB").save(q); cache[key_] = q
        if not seq or seq[-1][1] != cache[key_]: seq.append((t, cache[key_]))
        k += 1
    else:
        seq.append((t, os.path.join(SH, s_["img"]))); k = max(k + 1, round(tn * fps))
lst = os.path.join(tmp, "list.txt")
with open(lst, "w") as fo:
    for i, (t, q) in enumerate(seq):
        t2 = seq[i + 1][0] if i + 1 < len(seq) else END
        fo.write("file '%s'\nduration %.5f\n" % (q, t2 - t))
    fo.write("file '%s'\n" % seq[-1][1])

# 音
SR = 48000
r = subprocess.run(["ffmpeg", "-v", "error", "-i", W + "/animatic_tmp/voice.wav", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True)
a = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
a = np.concatenate([a, np.zeros(max(0, int(END * SR) - len(a)), np.float32)])[:int(END * SR)].copy()
VO = os.path.join(HERE, "..", "voice")
P_ = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
nos, over, moved = set(), [], []
_VE = {}
def talking(t, d):
    """その時刻に声が出ているか（声の音そのものの大きさで見る。台詞の中の「……」の無音は、出ていない）"""
    for p in P_:
        if p["start"] - 0.05 < t + d and t < p["end"] + 0.05:
            if p["no"] not in _VE:
                with wave.open(W + "/stage/voice/achernar/line_%03d.wav" % p["no"]) as w_:
                    x = np.frombuffer(w_.readframes(w_.getnframes()), np.int16) / 32768; sr = w_.getframerate()
                h = int(0.02 * sr); _VE[p["no"]] = (np.sqrt((x[:len(x) // h * h].reshape(-1, h) ** 2).mean(1)), 0.02)
            e, hs = _VE[p["no"]]
            a_ = max(0, int((t - p["start"]) / hs)); b_ = int((t + d - p["start"]) / hs) + 1
            if (e[a_:b_] > 0.02).any(): return True
    return False
for c in CL:
    hits = [tuple(e) for e in c["log"]["events"]] + [(t_, "step", 0.6) for t_ in c["log"]["steps"]]
    for t_, kind, g in hits:
        if not (c["t0"] <= t_ < c["t1"]): continue
        x = sfx.make(kind, SR)
        if x is None: nos.add(kind); continue
        if kind in ("click", "pop_ui", "pi") and talking(t_, len(x) / SR):
            # 大事な音が声と重なるときは、前後 0.5 秒以内のいちばん近い声のすき間へずらす（ずらせなければ報告）
            for sh in sorted((k_ * 0.02 for k_ in range(-25, 26)), key=abs):
                if t_ + sh >= 0 and not talking(t_ + sh, len(x) / SR):
                    moved.append("%s %.1f→%.2f" % (kind, t_, t_ + sh)); t_ += sh; break
            else: over.append("%s %.1f" % (kind, t_))
        i = int(t_ * SR); a[i:i + len(x)] += (g * x)[:len(a) - i]
a /= max(1.0, np.abs(a).max() / 0.95)
wv = os.path.join(tmp, "audio.wav")
with wave.open(wv, "wb") as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((a * 32767).astype(np.int16).tobytes())

# 字幕
def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
rs = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
      "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
sys.path.insert(0, W + "/tools"); import subs_jp as SJ
rs.append(SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP"))
rs += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a_, c_, tx in ev: rs.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(a_), ts(c_), tx.replace("\n", "\\N")))
ass = os.path.join(tmp, "subs.ass"); open(ass, "w", encoding="utf-8").write("\n".join(rs) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wv,
                "-vf", "fps=24,scale=1280:720,subtitles=%s:fontsdir=%s" % (ass, FONTS), "-t", "%.3f" % END,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", OUT], check=True)
chk = ["3D のコマが足りない所（絵コンテの絵で代わりに出した時刻）：" + (", ".join(map(str, miss[:30])) + (" ほか" if len(miss) > 30 else "") if miss else "なし"),
       "効果音のない種類：" + ("、".join(sorted(nos)) or "なし"),
       "大事な効果音が声と重なる所：" + ("、".join(over) or "なし"),
       "声のすき間へずらした効果音：" + ("、".join(moved) or "なし"),
       "3D のクリップ：%d" % len(CL)]
open(os.path.splitext(OUT)[0] + "_check.txt", "w", encoding="utf-8").write("\n".join(chk) + "\n")
print("\n".join(chk)); print(OUT, "%.1f MB" % (os.path.getsize(OUT) / 1e6))
