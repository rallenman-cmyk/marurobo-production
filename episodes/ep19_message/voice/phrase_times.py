# 文の中の「句読点のあとの声の頭」を、声の本当の間から測って書き出す（SKILL §3：札・音・動きを言葉に合わせるときも、字数の見積もりでなく声の間で）
# MARU_WORK=<作業フォルダ> python3 phrase_times.py <番号の始め> <番号の終わり>  → phrase_t.json（scenes.py の wp() が読む）
#   1 文 = [[字の位置, 声の頭, 声の終わり（次の間の始め）], ...]。句読点で区切った句ごと
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
import subs_pause_align as PA
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "placement.json"), encoding="utf-8"))
out_p = os.path.join(HERE, "phrase_t.json")
OUT = json.load(open(out_p, encoding="utf-8")) if os.path.exists(out_p) else {}
a, b = int(sys.argv[1]), int(sys.argv[2])
for p in P:
    n = p["no"]
    if not (a <= n <= b): continue
    wav = D + "/line_%03d.wav" % n; sp = p.get("speed", 1.0); st = p["start"]
    on = st + PA.onset(wav) / sp
    S, dur = PA.silences(wav, sp)
    al = PA.align(p["text"], st, wav, sp)
    ph = [[0, round(on, 3)]]
    for pos, t, L in al:
        if t is not None: ph.append([pos, round(t, 3)])
    # 各句の終わり＝次の句の頭の前の間の始め（文の最後は声の終わり）
    rows = []
    for k, (pos, t0) in enumerate(ph):
        if k + 1 < len(ph):
            t1 = ph[k + 1][1] - next((e_ - s_ for s_, e_ in S if abs(st + e_ - ph[k + 1][1]) < 0.02), 0.0)
        else:
            t1 = p["end"]
        rows.append([pos, t0, round(t1, 3)])
    OUT[str(n)] = rows
json.dump(OUT, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("phrases", sum(len(OUT[k]) for k in OUT), "lines", len(OUT))
