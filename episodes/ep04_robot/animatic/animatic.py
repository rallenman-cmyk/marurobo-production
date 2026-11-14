# ロボットではありません回：確認用の通し（絵コンテの静止画を声の時刻に並べ、字幕を重ねる）
# MARU_WORK=<作業フォルダ> python3 animatic.py <ショットのフォルダ> <フォントのフォルダ> <出力.mp4>
#   絵：<ショット>/shots.json（どの台詞からどの絵か）。場面の頭の絵は、その場面の最初の声の 0.4 秒前、場面の中の絵はその台詞の 0.15 秒前に切り替える
#   字幕：subs_jp.expand（25 字・2 行・声の間で分ける）。声：placement.json の時刻（-20 dBFS にそろえる）
#   点検：<出力>_check.txt（2.2 秒以上の間・1.0 秒未満の字幕・絵の足りない所）
import os, sys, json, wave, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ["MARU_WORK"]
sys.path.insert(0, W + "/tools")
import subs_jp as SJ
SJ.OVERRIDES.update({   # この回で、自動の改行が不自然だった所（2026-11-13 一覧で読んで決めた）
    "代わりに、「信号機を全部選んでください」という絵のテストが出てきました。": ["代わりに、「信号機を全部選んでください」という\\N絵のテストが出てきました。"],
    "では、どうやって人間とロボットを見分けるのでしょうか？": ["では、どうやって\\N人間とロボットを見分けるのでしょうか？"],
    "そのパソコンが、これまでネットでどう過ごしてきたか、という記録です。": ["そのパソコンが、これまでネットで\\Nどう過ごしてきたか、という記録です。"],
    "そして、ロボットであるAIが、自分で「人間です」のチェックを入れて、先へ進んでしまったのです。": ["そして、ロボットであるAIが、\\N自分で「人間です」のチェックを入れて、", "先へ進んでしまったのです。"],
})
for _k, _v in SJ.OVERRIDES.items():
    assert "".join(_v).replace("\\N", "") == _k, _k
SH, FONTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
V = W + "/stage/voice/achernar"
P = json.load(open(V + "/placement.json", encoding="utf-8"))
L = {e["no"]: e for e in json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))}
ID = {L[p["no"]]["id"]: p for p in P}
END = max(P[-1]["end"] + 0.5, float(os.environ.get("END_AT", P[-1]["end"] + 2.5)))   # v3：動画の終わり（ユーザー「10分42.5秒くらいで終わらせて」→ END_AT=642.5）
tmp = W + "/animatic_tmp"; os.makedirs(tmp, exist_ok=True)

# 絵の並び
first_of_scene = set()
prev = None
for p in P:
    sc = L[p["no"]]["scene"]
    if sc != prev: first_of_scene.add(L[p["no"]]["id"])
    prev = sc
shots = json.load(open(SH + "/shots.json", encoding="utf-8"))
seq = []
for s in shots:
    p = ID[s["id"]]
    t = p["start"] - (0.4 if s["id"] in first_of_scene else 0.15) + s.get("dt", 0.0)
    seq.append((max(0.0, t), os.path.join(SH, s["img"])))
seq.sort()
seq[0] = (0.0, seq[0][1])
# v3（コメント「少しずつ拡大して戻って…のカメラの動きはやめて」）：寄る動きはやめ、絵は止めて置く（ZOOM=0.03 で前の寄る形）
clips = []
for i, (t0, img) in enumerate(seq):
    t1 = seq[i + 1][0] if i + 1 < len(seq) else END
    n = max(1, round(t1 * 24) - round(t0 * 24))   # 区切りを通しのコマ番号で決める（1 枚ずつ丸めると、ずれがたまる）
    c = tmp + "/clip_%03d.mp4" % i
    z = "1+%s*on/%d" % (os.environ.get("ZOOM", "0"), max(1, n - 1))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", img, "-frames:v", str(n),
                    "-vf", "scale=2560:1440,zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24" % z,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", c], check=True)
    clips.append(c)
open(tmp + "/list.txt", "w").write("".join("file '%s'\n" % c for c in clips))

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
mix /= max(1.0, np.abs(mix).max() / 0.89)
with wave.open(tmp + "/voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())

# 字幕（声の終わり +0.35 秒、次の字幕の 0.05 秒前まで。1.2 秒未満なら次の前までのばす）
lines = []
for k, p in enumerate(P):
    nxt = P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.0
    end = max(p["end"] + 0.35, p["start"] + 1.2)
    lines.append((p["start"], min(end, nxt - 0.05), p["text"]))
ev = []   # v3：分けた字幕は、声の出ている時間の割合で替える（events_v。前の events は「OpenAIが」の後で替わって遅れた・20-04 で早く替わった）
for a, c, t in lines:
    ev += SJ.events_v(a, c, t)
def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
style = SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP")
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       style, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, t in ev:
    ass.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(a), ts(c), t.replace("\n", "\\N")))
open(tmp + "/subs.ass", "w", encoding="utf-8").write("\n".join(ass) + "\n")
json.dump(ev, open(os.path.join(HERE, "subs_events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

# 点検
chk = []
gaps = [(P[k]["end"], P[k + 1]["start"] - P[k]["end"], L[P[k + 1]["no"]]["id"]) for k in range(len(P) - 1) if P[k + 1]["start"] - P[k]["end"] >= 2.2]
chk.append("2.2 秒以上の間：" + ("、".join("%.1f 秒（%s の前）" % (g, i) for _, g, i in gaps) or "なし"))
short = [(a, c - a, t) for a, c, t in ev if c - a < 1.0]
chk.append("1.0 秒未満の字幕：" + ("、".join("%.1f秒 %.2f 秒「%s」" % (a, d, t[:12]) for a, d, t in short) or "なし"))
miss = [s["id"] for s in shots if not os.path.exists(os.path.join(SH, s["img"]))]
chk.append("絵の足りないショット：" + ("、".join(miss) or "なし"))
over = [t for a, c, t in ev if any(SJ.width(r) > 25 for r in t.split("\\N")) or t.count("\\N") > 1]
chk.append("25 字・2 行をこえる字幕：" + ("、".join(over) or "なし"))
open(os.path.splitext(OUT)[0] + "_check.txt", "w", encoding="utf-8").write("\n".join(chk) + "\n")
print("\n".join(chk))

subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp + "/list.txt", "-i", tmp + "/voice.wav",
                "-vf", "subtitles=%s:fontsdir=%s" % (tmp + "/subs.ass", FONTS),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "32", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "96k", "-shortest", OUT], check=True)
print("字幕 %d 枚・絵 %d 枚・%.1f 秒 → %s（%.1f MB）" % (len(ev), len(seq), END, OUT, os.path.getsize(OUT) / 1e6))
