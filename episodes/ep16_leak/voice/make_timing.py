# 声の長さ（lines.json）から、台本 json の start/end を作り直す（narration.py がこの時刻に置く）
# 9本目（7本目から写した）。間の決まり（SKILL §3）：短い声のあと 0.8 秒／場面が変わる文の前 0.8 秒／「……」で始まる文の前 0.7 秒／前の文が「？」「……」で終わるとき 0.6 秒／ほか 0.4 秒
# MARU_WORK=<作業フォルダ> python3 make_timing.py
import os, json, re
W = os.environ["MARU_WORK"]
P = W + "/stage/script/script_v2_timed.json"
L = json.load(open(P, encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
BEEP = {}  # この回は合言葉がないので「ピー」はなし
# 9本目：動きを見せる所は、言い終えてから動き、結果を少し止めて見せる（SKILL §3）。値は前の文との間（秒）
EXTRA = {  # 16本目（情報流出）。間（秒）＝前の文との間。動きを見せる所・場面の変わり目で長めに
         "01-02": 1.0,                 # 通知で起きて、スマホへ歩く
         "02-01": 0.8, "02-02": 0.9,   # メールを開く → 驚く
         "02-07": 0.8,                 # 4 つが戻ってくる
         "03-01": 0.9,                 # 部屋をきょろきょろ
         "04-01": 0.9, "04-05": 1.4,   # ニュースの見出し／題
         "05-01": 1.0, "05-02": 0.9, "05-03": 0.9, "05-04": 0.9, "05-05": 0.8,   # お店 → お城・名札・鍵（1 つずつ替わる）
         "06-01": 0.9,                 # お城へ歩いてくる
         "06-05": 1.0, "06-07": 1.0, "06-08": 0.7,   # 門を押す → 体当たり → はね返る
         "07-01": 1.0, "07-02": 0.9,   # 想像の映画の場面
         "08-01": 1.0, "08-04": 0.9,   # お城を回る → ふり向いて驚く
         "09-01": 1.0, "09-03": 0.9,   # 裏口の前／小窓
         "10-01": 0.9, "10-03": 0.9, "10-07": 1.0,   # 近づく／箱が届く／かんたんな鍵で開く
         "11-01": 0.9, "11-02": 0.8, "11-10": 1.0,   # 図へ／図から正面へ
         "12-01": 1.4, "12-03": 0.9, "12-04": 0.8,   # 時間を巻きもどす／取り出す……本物の鍵
         "12-08": 0.9, "12-09": 0.9}
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
