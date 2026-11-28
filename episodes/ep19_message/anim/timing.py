# 9本目：声の時刻（core.py と同じ計算を、Blender の外でも使う）。s(ID)・e(ID)・w(ID, 言葉)
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




# 3章から：言葉の時刻を、声の本当の間（句読点のあとの声の頭）から出す（SKILL §3。字数の見積もり w() は句の中だけに使う）
#   ../voice/phrase_t.json（voice/phrase_times.py が作る）：文の番号 → [[句の頭の字の位置, 声の頭, 声の終わり], ...]
_PT_P = os.path.join(VO, "phrase_t.json")
_PT = json.load(open(_PT_P, encoding="utf-8")) if os.path.exists(_PT_P) else {}
_NO = {L[p["no"]]["id"]: p["no"] for p in P}
_PTX = {p["no"]: p["text"] for p in P}


def wp(i, word, occ=0, end=False):
    """台詞 i の中で word（occ 番目）を言う時刻。句の頭なら声の頭そのもの。句の中は、その句の声の長さを字数で割る"""
    n = _NO[i]; t = _PTX[n]; rows = _PT.get(str(n))
    k = -1
    for _ in range(occ + 1): k = t.index(word, k + 1)
    if end: k += len(word)
    if not rows: return w(i, word, end)
    j = max(q for q in range(len(rows)) if rows[q][0] <= k)
    p0 = rows[j][0]; p1 = rows[j + 1][0] if j + 1 < len(rows) else len(t)
    seg = t[p0:p1].rstrip("、。？！…　」")
    fr = min(1.0, (k - p0) / max(1, len(seg)))
    return rows[j][1] + (rows[j][2] - rows[j][1]) * fr
