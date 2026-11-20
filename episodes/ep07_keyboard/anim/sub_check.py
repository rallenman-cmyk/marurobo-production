# 字幕を数で点検する（7本目 v8：2026-11-20「テロップの切り替わりがすごい早い」25 件の振り返り）
#   MARU_WORK=<作業> python3 sub_check.py [subs.ass]
#   ① subs.ass があれば、焼きこんだ字幕そのものを測る。なければ subs_one で作り直して測る
#   ② 1 枚の長さ 2.0 秒未満・1 秒あたり 8 字をこえる字幕・1 行 25 字をこえる字幕を全部出す（出たら直してから出す）
import os, sys, re, json, statistics
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "..", "..", "..", "skill", "marurobo-video-production", "scripts")); sys.path.insert(0, H)
L = []
if len(sys.argv) > 1:
    for l in open(sys.argv[1], encoding="utf-8"):
        if not l.startswith("Dialogue"): continue
        p = l.split(",", 9); f = lambda x: sum(float(v) * m for v, m in zip(x.split(":"), (3600, 60, 1)))
        if p[3] != "Main": continue
        L.append((f(p[1]), f(p[2]), re.sub(r"\{.*?\}", "", p[9].strip())))
else:
    import subs_jp as SJ, subs_one as SO
    P = json.load(open(os.path.join(H, "..", "voice", "placement.json"), encoding="utf-8"))
    for i, p in enumerate(P):
        nx = P[i + 1]["start"] - 0.05 if i + 1 < len(P) else p["end"] + 2
        L += SO.events(p["start"], p["end"], p["text"], os.path.join(SJ.VOICE, "line_%03d.wav" % p["no"]), SJ, speed=p.get("speed", 1.0), c_max=nx)
L.sort()
d = [b - a for a, b, _ in L]; cps = [len(t.replace(" ", "")) / (b - a) for a, b, t in L]
print("字幕 %d 枚・長さ いちばん短い %.2f 秒・まん中 %.2f 秒" % (len(L), min(d), statistics.median(d)))
bad = [(a, b - a, len(t.replace(" ", "")) / (b - a), t) for a, b, t in L if b - a < 2.0 or len(t.replace(" ", "")) / (b - a) > 8.0 or len(t.replace(" ", "")) > 25]
print("2 秒未満・8 字/秒こえ・25 字こえ：%d 枚" % len(bad))
for a, du, c, t in bad: print("  %6.2f  %.2f 秒  %.1f 字/秒  %s" % (a, du, c, t))
