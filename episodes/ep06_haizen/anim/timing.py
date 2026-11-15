# 6本目：声の時刻（core.py と同じ計算を、Blender の外でも使う）。s(ID)・e(ID)・w(ID, 言葉)
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, "..", "voice")
P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
L = {e["no"]: e for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
T, TEXT, SCENE = {}, {}, {}
for p in P:
    i = L[p["no"]]["id"]; T[i] = (p["start"], p["end"]); TEXT[i] = L[p["no"]]["text"]; SCENE[i] = L[p["no"]]["scene"]


def s(i): return T[i][0]
def e(i): return T[i][1]


def w(i, word, end=False):
    t = TEXT[i]; k = t.index(word) + (len(word) if end else 0)
    wt = lambda u: sum(0.35 if ch in "…" else (0.6 if ch in "、。？！「」　" else 1.0) for ch in u)
    return s(i) + (e(i) - s(i)) * wt(t[:k]) / max(1e-6, wt(t))


END = P[-1]["end"] + 2.5
