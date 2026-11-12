# 会話と広告の回：YouTube 一式（もくじの時刻・字幕ファイル）を作る
#   python3 make_youtube_kit.py [字幕の時刻のずれ（秒・本番で頭に何か足したとき）]
#   出力：会話と広告の回_YouTube一式.md（もくじの時刻を埋める）・ad_ep03_ja.srt
#   時刻は voice/placement.json（場面の最初の声の 0.4 秒前）から。長さが変わったら走らせ直す
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); EP = os.path.join(HERE, "..")
OFF = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
P = json.load(open(os.path.join(EP, "voice", "placement.json"), encoding="utf-8"))
SID = {e["no"]: e for e in json.load(open(os.path.join(EP, "voice", "script_v1_0.json"), encoding="utf-8"))}
SC = {}
for p in P: SC.setdefault(SID[p["no"]]["scene"], max(0.0, p["start"] - 0.4))
SC["S00"] = 0.0
CH = [("S00", "冒頭　さっき話しただけなのに、テントの広告が？"), ("S05", "容疑者は3人"),
      ("S06", "容疑者①　マイク　スマホの中に入って確かめる"), ("S10", "容疑者②　スマホから出ていく手がかり"),
      ("S15", "容疑者③　わたしたちの記憶"), ("S17", "どんでん返し「会話を聞ける」と言った会社"),
      ("S19", "事件のまとめ"), ("S21", "オチ　犯人は……")]
def mmss(t): t = int(t + OFF + 0.5) if t else 0; return "%d:%02d" % (t // 60, t % 60)
toc = "\n".join("%s %s" % (mmss(SC[s]), name) for s, name in CH)
ev = json.load(open(os.path.join(EP, "animatic", "subs_events.json"), encoding="utf-8"))
def ts(x): x += OFF; ms = int(round(x * 1000)); return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
srt = "\n".join("%d\n%s --> %s\n%s\n" % (i + 1, ts(a), ts(b), t) for i, (a, b, t) in enumerate(ev))
open(os.path.join(HERE, "ad_ep03_ja.srt"), "w", encoding="utf-8").write(srt)
src = open(os.path.join(HERE, "template.md"), encoding="utf-8").read()
end = P[-1]["end"] + 2.0
out = src.replace("{{TOC}}", toc).replace("{{LEN}}", "%d:%02d" % (int(end + OFF) // 60, int(end + OFF) % 60)).replace("{{NSUB}}", str(len(ev)))
open(os.path.join(HERE, "会話と広告の回_YouTube一式.md"), "w", encoding="utf-8").write(out)
print(toc); print("字幕", len(ev), "行")
