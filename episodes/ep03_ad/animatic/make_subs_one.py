# 3本目 v11：字幕を 1 行ずつにして、上げる前の関所の決まり（1 枚 2 秒以上・1 秒 8 字まで・1 行 25 字まで）に合わせる
#   7本目の作り方（episodes/ep07_keyboard/anim/subs_one.py：文の中の「。？！」と読点・「……」で 1 行ずつに分け、声の切れ目で切り替え、
#   2 秒に足りない 1 枚はまとめる・となりから時間を借りる）をそのまま使う
#   MARU_WORK=<作業フォルダ> python3 make_subs_one.py → subs_events.json（v10 までの 2 行の字幕は subs_events_v10.json）
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ["MARU_WORK"]
os.environ.setdefault("MARU_VOICE", W + "/stage/voice/achernar")
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
sys.path.insert(0, HERE)
import subs_jp as SJ, subs_one3 as SO           # 7本目の subs_one.py の写し（「……」で終わる 1 枚はまとめない）
SO.PIECES = {                                        # 7本目だけの分け方は使わない。3本目で決まりに入らなかった 2 文だけ、分け方を決める
    "どうやら、今度の休みに、二人でキャンプへ行く話がまとまったみたいです。": ["どうやら、今度の休みに、二人で", "キャンプへ行く話がまとまったみたいです。"],   # 1 秒 8 字をこえた
    "このように、同じWi-Fiにいた人が調べた物の広告が、出てくることもあるのです。": ["このように、", "同じWi-Fiにいた人が調べた物の広告が、", "出てくることもあるのです。"],   # 1 行 25 字をこえた
}
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
L, log = [], []
for i, p in enumerate(P):
    if p["text"].strip() in ("（間）", ""): continue
    nx = P[i + 1]["start"] - 0.05 if i + 1 < len(P) else p["end"] + 2.0
    L += SO.events(p["start"], p["end"], p["text"].replace("（間）", ""), os.path.join(os.environ["MARU_VOICE"], "line_%03d.wav" % p["no"]), SJ, speed=p.get("speed", 1.0), c_max=nx, log=log)
L = SO.balance(L)
# まだ 2 秒に足りない 1 枚：次の 1 枚の頭を遅らせ、その分、次の 1 枚の終わりと、その次の 1 枚の頭も 0.3 秒まで遅らせる
#   （3本目「その先には……／大きな会場！」：前後がどちらもちょうど 2 秒で、まとめると答えが先に出るため）
L = [list(x) for x in sorted(L)]
for i in range(len(L) - 2):
    need = 2.0 - (L[i][1] - L[i][0])
    if need <= 0.005 or abs(L[i + 1][0] - L[i][1]) > 0.1: continue
    d = min(need, 0.3)
    if (L[i + 2][1] - L[i + 2][0]) - d < 2.0 or len(L[i + 2][2]) / ((L[i + 2][1] - L[i + 2][0]) - d) > 8.0: continue
    L[i][1] += d; L[i + 1][0] += d; L[i + 1][1] += d; L[i + 2][0] += d
L = [tuple(x) for x in L]
json.dump([[round(a, 3), round(b, 3), t] for a, b, t in sorted(L)], open(os.path.join(HERE, "subs_events.json"), "w"), ensure_ascii=False, indent=0)
n = lambda t: len(t.replace(" ", ""))
bad = [(round(a, 2), round(b - a, 2), t) for a, b, t in L if b - a < 1.99 or n(t) / (b - a) > 8.0 or n(t) > 25]
print("字幕 %d 枚。決まりの外 %d 枚" % (len(L), len(bad)))
for x in bad: print(" ", x)
