# 17本目 5章（23-01〜28-09、148〜192 番）の置き場所を、4章までの時刻を変えずに 22-08 のあとへ続けて置く（add_timing_ch4.py を写した）
#   間の決まりは make_timing.py と同じ：同じ場面の中 0.6 秒／場面が変わる所 0.9 秒／動きを見せる所は EXTRA（長い方）。章の頭は 1.5 秒
# MARU_WORK=<作業> python3 add_timing_ch3.py
import os, json
H = os.path.dirname(os.path.abspath(__file__)); W = os.environ["MARU_WORK"]
F = json.load(open(os.path.join(H, "script_v0_3.json"), encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
P = json.load(open(os.path.join(H, "placement.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(H, "script_v1_0.json"), encoding="utf-8"))
LAST = 192
EXTRA = {"23-01": 1.5,                                   # 章の頭（4章 → 5章）
         "23-03": 0.9, "23-05": 0.9,                     # 門番さんが出る・まるロボがとなりへ
         "24-01": 1.0, "24-02": 0.8, "24-03": 0.9, "24-04": 0.9, "24-05": 1.0, "24-06": 1.0,   # 影が来る・すると……・赤く光って……・ガシャン・跳ねて喜ぶ
         "25-01": 0.9, "25-02": 1.0, "25-03": 0.9, "25-04": 0.8,                               # テストを出す・すると……・ぴたっ
         "26-02": 0.8, "26-03": 1.0, "26-04": 1.0, "26-05": 0.9, "26-06": 0.9, "26-07": 0.8,   # 別のお店へ・札を入れる……・通ってしまう・そのとき
         "26-08": 1.0, "26-09": 0.9, "26-10": 0.9, "26-11": 0.9, "26-12": 1.0, "26-14": 0.8, "26-17": 0.9,   # スマホが震える・首を振る・すると……・パチン
         "27-01": 1.0, "27-02": 0.9, "27-03": 0.9,                                             # 小窓の金庫・うすくなる・本人確認が光る
         "28-01": 1.2, "28-02": 0.8, "28-03": 1.0, "28-04": 0.8, "28-05": 1.0, "28-06": 1.0, "28-07": 1.0}   # 家へ・スイッチを 1 つずつ押す
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
print(len(P), "文。5章の終わり", P[-1]["end"])
