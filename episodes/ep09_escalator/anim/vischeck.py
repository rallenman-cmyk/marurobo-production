# python3 vischeck.py <描いたフォルダ>：絵コンテの文ごとに、言っている人・物（まるロボ・おじさん）が画面に入っているかを、描いたときの目印の記録で数える
import json, os, re, sys
A = "/home/user/marurobo-production/episodes/ep09_escalator/anim"; sys.path.insert(0, A)
import timing as T
R = sys.argv[1]
clips = json.load(open(A + "/clips.json"))
cuts = sorted((v[2], k) for k, v in clips.items())
def clip_at(t):
    c = None
    for tc, k in cuts:
        if tc <= t: c = k
    return c
rows = []
for ln in open(A + "/../絵コンテ_v1.md", encoding="utf-8"):
    m = re.match(r"\| *(\d\d-\d\d) *\|([^|]*)\|([^|]*)\|", ln)
    if m and m.group(1) in T.T: rows.append((m.group(1), m.group(2).strip(), m.group(3).strip()))
LOG = {}
def vis(k, nm, t0, t1):
    if k not in LOG:
        p = f"{R}/{k}/{k}_log.json"; LOG[k] = json.load(open(p)) if os.path.exists(p) else None
    L = LOG[k]
    if not L or nm not in L["track"]: return None
    pts = [p for p in L["track"][nm] if t0 <= L["t0"] + p[0] / L["fps"] <= t1]
    if not pts: return None
    return sum(1 for _, x, y, z in pts if z > 0 and 0 <= x <= 1280 and 0 <= y <= 720) / len(pts)
for i, txt, show in rows:
    a, b = T.s(i), T.e(i)
    ks = sorted({clip_at(a + (b - a) * u / 8) for u in range(9)})
    out = []
    for nm, words in (("maru_c", ("まるロボ",)), ("ojisan", ("おじさん",))):
        if not any(wd in show for wd in words): continue
        best = max([v for v in (vis(k, nm, a, b) for k in ks) if v is not None] or [-1])
        if best < 0.5: out.append(f"{nm} {best:.2f}")
    if out: print(i, ",".join(ks), " / ".join(out), "|", show[:50])
