# 17本目 3章（15-01〜19-05、80〜127 番）の置き場所を、2章までの時刻を変えずに 14-10 のあとへ続けて置く
#   間の決まりは make_timing.py と同じ：同じ場面の中 0.6 秒／場面が変わる所 0.9 秒／動きを見せる所は EXTRA（長い方）。章の頭は 1.5 秒
# MARU_WORK=<作業> python3 add_timing_ch3.py
import os, json
H = os.path.dirname(os.path.abspath(__file__)); W = os.environ["MARU_WORK"]
F = json.load(open(os.path.join(H, "script_v0_3.json"), encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
P = json.load(open(os.path.join(H, "placement.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(H, "script_v1_0.json"), encoding="utf-8"))
LAST = 127
EXTRA = {"15-01": 1.5,                                   # 章の頭（2章 → 3章）
         "15-04": 0.9, "15-05": 1.0, "15-09": 0.9, "15-11": 0.8, "15-12": 0.9,   # カタカタ → 札が出る・札に寄る・影が出ていく
         "16-01": 1.2, "16-03": 0.8, "16-04": 0.9, "16-05": 1.0, "16-07": 0.8, "16-08": 1.0, "16-10": 0.9, "16-12": 0.8,   # 光の玉が飛ぶ・戻る・札が落ちる
         "17-03": 1.0, "17-04": 0.9, "17-07": 1.0, "17-08": 0.9,                   # 速くなる・ピンポン
         "18-03": 0.9, "18-04": 1.4, "18-05": 1.0, "18-09": 0.9,                   # 光が家へ飛ぶ・金庫のカードが光る・ころころ
         "19-01": 1.0, "19-04": 0.9, "19-05": 0.8}
have = {p["no"] for p in P}
t = P[-1]["end"]; prev = next(x for x in F if x["no"] == P[-1]["no"])
for e in F:
    if e["no"] in have or e["no"] > LAST: continue
    g = 0.9 if e["scene"] != prev["scene"] else 0.6
    g = max(g, EXTRA.get(e["id"], 0.0))
    d = V[str(e["no"])]["dur"]; t += g
    P.append(dict(no=e["no"], start=round(t, 3), end=round(t + d, 3), speed=1.0, slot=[round(t, 3), round(t + d, 3)], text=e["text"]))
    t += d; prev = e
    if e["no"] not in {x["no"] for x in S1}: S1.append(dict(e, start=round(t - d, 3), end=round(t, 3)))
json.dump(P, open(os.path.join(H, "placement.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(S1, open(os.path.join(H, "script_v1_0.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(P), "文。3章の終わり", P[-1]["end"])
