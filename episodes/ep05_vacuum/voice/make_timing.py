# 声の長さ（lines.json）から、台本 json の start/end を作り直す（narration.py がこの時刻に置く）
# 5本目（ep04 から写した）。間の決まり（SKILL §3）：短い声のあと 0.8 秒／場面が変わる文の前 0.8 秒／「……」で始まる文の前 0.7 秒／前の文が「？」「……」で終わるとき 0.6 秒／ほか 0.4 秒
# MARU_WORK=<作業フォルダ> python3 make_timing.py
import os, json, re
W = os.environ["MARU_WORK"]
P = W + "/stage/script/script_v2_timed.json"
L = json.load(open(P, encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
BEEP = {}  # この回は合言葉がないので「ピー」はなし
# 5本目：動きを見せる所は、言い終えてから動き、結果を少し止めて見せる（SKILL §3）
EXTRA = {"04-01": 2.8,                 # 前にオープニング（題名 2 秒。4本目 v5 のコメント）
         "02-02": 1.0,                 # スマホが光るのを見せる
         "07-03": 0.9,                 # 目の光を消してから歩き出す
         "09-02": 1.6,                 # 先輩が走り出して、壁の手前で曲がるまで
         "10-03": 1.1,                 # ふたが透けるまで
         "11-03": 1.3,                 # 明かりが落ちるまで（落ちる前に部屋の全体は見せてある）
         "12-02": 1.4,                 # 点がつながるまで
         "17-09": 1.2,                 # 地図を引き戻して、ぴたっと重なるまで
         "19-03": 1.1,                 # 照明が後ろへずれるのを見せる
         "20-02": 1.1,                 # パチン（電気を消す音）のあと 0.6 秒以上あける
         "21-02": 1.0,                 # 目の光で照らす
         "22-06": 1.0,                 # ころん（落ちる音）のあと
         "25-08": 1.1,                 # のけぞる → 足もと（ため）
         "26-01": 1.0,                 # まとめの前で一息
         "27-01": 1.4,                 # オチの前は長めに（余韻）
         "27-03": 1.0,                 # 地図が出るのを見せる
         "27-05": 1.1}
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
