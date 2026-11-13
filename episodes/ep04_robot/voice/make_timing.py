# 声の長さ（lines.json）から、台本 json の start/end を作り直す（narration.py がこの時刻に置く）
# 間の決まり（SKILL §3）：短い声のあと 0.8 秒／場面が変わる文の前 0.8 秒／「……」で始まる文の前 0.7 秒／前の文が「？」「……」で終わるとき 0.6 秒／ほか 0.4 秒
# MARU_WORK=<作業フォルダ> python3 make_timing.py
import os, json, re
W = os.environ["MARU_WORK"]
P = W + "/stage/script/script_v2_timed.json"
L = json.load(open(P, encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
BEEP = {}  # この回は合言葉がないので「ピー」はなし
EXTRA = {"22-05": 0.8, "23-01": 1.4}  # 少し暗いまとめの前で一息、オチの前は長めに（余韻）
t, prev = 0.5, None
for e in L:
    d = V[str(e["no"])]["dur"]
    if prev is None:
        g = 0.0
    elif e["id"] in EXTRA:
        g = EXTRA[e["id"]]
    elif e["id"] in BEEP:
        g = BEEP[e["id"]]  # 合言葉（声に出さない）を「ピー」で鳴らす時間＋見張り番の反応
    elif V[str(prev["no"])]["dur"] < 1.0:
        g = 0.8  # 短い声（「……一瞬！」など）のあとは、字幕が 1 秒以上出るように
    elif e["scene"] != prev["scene"]:
        g = 0.8
    elif e["text"].startswith("……"):
        g = 0.7
    elif re.search(r'[？?]$|……。?$', prev["text"]):
        g = 0.6
    else:
        g = 0.4
    t += g
    e["start"], e["end"] = round(t, 3), round(t + d, 3)
    e.pop("gap_before", None)
    if g >= 0.6:
        e["gap_before"] = g
    t += d
    prev = e
json.dump(L, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("声の合計 %.0f 秒・間を入れて %.0f 秒（%d 分 %02d 秒）" % (sum(V[k]["dur"] for k in V), t, t // 60, t % 60))
