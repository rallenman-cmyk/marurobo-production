# 17本目 4章（20-01〜22-08、128〜147 番）の置き場所を、3章までの時刻を変えずに 19-05 のあとへ続けて置く（add_timing_ch3.py を写した）
#   間の決まりは make_timing.py と同じ：同じ場面の中 0.6 秒／場面が変わる所 0.9 秒／動きを見せる所は EXTRA（長い方）。章の頭は 1.5 秒
# MARU_WORK=<作業> python3 add_timing_ch3.py
import os, json
H = os.path.dirname(os.path.abspath(__file__)); W = os.environ["MARU_WORK"]
F = json.load(open(os.path.join(H, "script_v0_3.json"), encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
P = json.load(open(os.path.join(H, "placement.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(H, "script_v1_0.json"), encoding="utf-8"))
LAST = 147
EXTRA = {"20-01": 1.5,                                   # 章の頭（3章 → 4章）
         "20-03": 0.8,                                   # 問い
         "21-01": 1.2, "21-05": 1.0, "21-07": 0.9, "21-08": 0.9, "21-09": 0.8,   # 塔の中へ・ランプがともる・カードが金庫へ・問い合わせがランプを照らす
         "22-01": 0.9, "22-03": 1.0, "22-04": 1.0, "22-07": 0.8, "22-08": 0.8}   # しょんぼり・数字の図・金庫と台帳を並べる
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
print(len(P), "文。4章の終わり", P[-1]["end"])
