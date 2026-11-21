# 声の長さ（lines.json）から、台本 json の start/end を作り直す（narration.py がこの時刻に置く）
# 7本目（6本目から写した）。間の決まり（SKILL §3）：短い声のあと 0.8 秒／場面が変わる文の前 0.8 秒／「……」で始まる文の前 0.7 秒／前の文が「？」「……」で終わるとき 0.6 秒／ほか 0.4 秒
# MARU_WORK=<作業フォルダ> python3 make_timing.py
import os, json, re
W = os.environ["MARU_WORK"]
P = W + "/stage/script/script_v2_timed.json"
L = json.load(open(P, encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
BEEP = {}  # この回は合言葉がないので「ピー」はなし
# 7本目：動きを見せる所は、言い終えてから動き、結果を少し止めて見せる（SKILL §3）
EXTRA = {"03-01": 0.9,                 # 上から見た絵へ
         "04-01": 2.8,                 # 前にオープニング（題名 2 秒。4本目 v5 のコメント）
         "05-05": 1.0,                 # ABC 順のキーボードへ移る
         "06-01": 1.1,                 # 打ち終わり → 上から結果
         "07-04": 0.9,                 # いろは歌の線が伸びきる
         "08-01": 0.9, "09-01": 1.0,   # 作業場へ・机に跳び乗る
         "10-07": 0.8, "10-08": 1.0,   # 台車で運ぶ・作業台に跳び乗る
         "12-01": 1.0,
         "13-02": 0.8, "13-04": 0.8,   # 棒がからまる・ほどく
         "15-04": 1.0,                 # わざとゆっくり跳ねる
         "17-01": 1.0, "17-03": 0.8,   # 受信機がカチカチ
         "18-02": 0.9, "18-04": 0.8,   # 18-02：v9 で 0.1 足した（「聞いてみましょう。」を 2 秒）
         "22-07": 1.4,                 # 5 つの会社がまとまる
         "24-05": 1.0,                 # もしも：キーが入れかわる
         "28-05": 2.6,                 # いろは歌を打つ（となりへ 1 歩ずつ）
         "28-07": 1.2, "28-08": 0.9}   # カメラが引く・人の手が来る
# v9：前の文の最後の字幕を 2 秒出すために、いつもの間に足す秒（ユーザー「声のあとに間を足す」。EXTRA は置きかえ、PLUS は足す）
PLUS = {"13-05": 0.15,   # 「だから、ばらばらに見える」。」
        "14-01": 0.5,    # 「ところが……。」
        "21-02": 0.15,   # 「でも、ちょっと待ってください。」
        "23-05": 0.4}    # 「そう言われていました。」
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
    t += g + PLUS.get(e["id"], 0.0)
    e["start"], e["end"] = round(t, 3), round(t + d, 3)
    e.pop("gap_before", None)
    if g >= 0.6:
        e["gap_before"] = g
    t += d
    prev = e
json.dump(L, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("声の合計 %.0f 秒・間を入れて %.0f 秒（%d 分 %02d 秒）" % (sum(V[k]["dur"] for k in V), t, t // 60, t % 60))
