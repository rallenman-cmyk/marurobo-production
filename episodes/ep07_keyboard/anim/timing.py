# 7本目：声の時刻（core.py と同じ計算を、Blender の外でも使う）。s(ID)・e(ID)・w(ID, 言葉)
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


_wt = lambda u: sum(0.35 if ch in "…" else (0.6 if ch in "、。？！「」　" else 1.0) for ch in u)
# 声の途中に足した間（voice/add_pause.py が voice/pauses.json に書く。{ID: [[足した所（秒）, 長さ（秒）, 間の前の字], …]}）
# v9：17-08「なんと」のあとに 0.5 秒足したのに、w() は字の割合で時刻を出すので「もっと速く！」の札が声より先に出た。
#     足した間は、いちばん近い句読点（、。」…のあと・「の前）にあるとみて、そこから後の言葉を、その長さだけ遅らせる
_PZ = json.load(open(os.path.join(VO, "pauses.json"), encoding="utf-8")) if os.path.exists(os.path.join(VO, "pauses.json")) else {}


def _pauses(i):
    """[(字の位置, 足した長さ)]"""
    t = TEXT[i]; ps = _PZ.get(i, []); d0 = (e(i) - s(i)) - sum(x[1] for x in ps); out = []
    cand = [k for k in range(1, len(t)) if (t[k - 1] in "、。」…" and t[k] not in "、。」…") or t[k] == "「"]     # 「の前も（17-08「なんと／「もっと速く！」」）
    for x in ps:
        at, add = x[0], x[1]
        if len(x) > 2: out.append((len(x[2]), add, at)); continue        # 間の前の字（[秒, 長さ, 前の字]）が書いてあれば、それを使う
        f = at / max(1e-6, d0); k = min(cand, key=lambda k: abs(_wt(t[:k]) / _wt(t) - f)); out.append((k, add, at))
    return out, d0


def w(i, word, end=False):
    t = TEXT[i]; k = t.index(word) + (len(word) if end else 0)
    ps, d0 = _pauses(i)
    x = s(i) + d0 * _wt(t[:k]) / max(1e-6, _wt(t)) + sum(a for kp, a, _ in ps if k >= kp)
    for kp, a, at in ps:          # 間のあとの言葉は、間が終わってから（声のファイルの at + a 秒より前には出ない）。間の前の言葉は、間より前
        x = max(x, s(i) + at + a) if k >= kp else min(x, s(i) + at)
    return x


END = P[-1]["end"] + 2.5


# 字を言う瞬間（voice/letter_times.json。声の大きさで測った、字ごとのかたまりの始まり）
_LT = json.load(open(os.path.join(VO, "letter_times.json"), encoding="utf-8"))


def lt(i, ch): return s(i) + _LT[i][ch]
