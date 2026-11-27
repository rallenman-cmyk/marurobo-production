# 17本目 まとめ・オチ（29-01〜31-01、193〜205 番）の置き場所を、5章までの時刻を変えずに 28-09 のあとへ続けて置く（add_timing_ch5.py を写した）
#   間の決まりは make_timing.py と同じ：同じ場面の中 0.6 秒／場面が変わる所 0.9 秒／動きを見せる所は EXTRA（長い方）。章の頭は 1.5 秒
# MARU_WORK=<作業> python3 add_timing_ch3.py
import os, json
H = os.path.dirname(os.path.abspath(__file__)); W = os.environ["MARU_WORK"]
F = json.load(open(os.path.join(H, "script_v0_3.json"), encoding="utf-8"))
V = json.load(open(W + "/stage/voice/achernar/lines.json", encoding="utf-8"))
P = json.load(open(os.path.join(H, "placement.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(H, "script_v1_0.json"), encoding="utf-8"))
LAST = 205
EXTRA = {"29-01": 1.5,                                   # 章の頭（5章 → まとめ）
         "29-03": 0.8, "29-04": 0.8, "29-05": 0.8, "29-06": 0.8,   # 小窓が替わる・窓の外の塔・スマホ・家の引き
         "30-01": 1.6,                                   # 「数日後」：場面が替わる
         "30-02": 0.8,                                   # 箱を押し終える
         "30-03": 1.5,                                   # 「……」のあと、箱が開いて大きな金庫が出る（字幕「中から出てきたのは……」を 2 秒以上に）
         "30-04": 1.2,                                   # とびらが開いてから「しまって」
         "30-05": 1.2,                                   # 得意顔のまま止まる
         "30-06": 1.5,                                   # 「……まるロボ。」の字幕を 2 秒以上に
         "31-01": 2.6}                                   # がくっ → スマホの設定を見て、うなずく
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
