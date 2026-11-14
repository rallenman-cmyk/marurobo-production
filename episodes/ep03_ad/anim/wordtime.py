# 会話と広告の回：文の中の言葉を「言い始める時刻」を声から求める（QR回 v11 の anim2.word_time と同じやり方、2026-11-13）
#   札・図の答えは、その言葉を言う瞬間に出す（答えを先に見せない）。使い方：import wordtime; wordtime.W("05-02", "マイク") → 本編の秒
#   文を読点・句点のまとまりに分け、声の出ている区間（0.12 秒以上の間で区切る）に、読みの長さが合うように順に当てはめる
import os, re, math, json, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, "..", "voice")
WAV = os.environ.get("MARU_VOICE") or os.path.join(os.environ.get("MARU_WORK", "."), "stage", "voice", "achernar")
_P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
_ID = {e["no"]: e["id"] for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
V = {_ID[p["no"]]: dict(text=p["text"], start=p["start"], end=p["end"], speed=p.get("speed", 1.0), wav=os.path.join(WAV, "line_%03d.wav" % p["no"])) for p in _P}


def _ylen(t): return max(0, sum(1 for ch in t if ch not in "、。？！…「」（）・ 　"))


def _segments(wav, gap=0.12):
    with wave.open(wav) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    h = int(sr * 0.01); n = len(x) // h; db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12)); on = db > db.max() - 38
    segs = []; j = 0
    while j < n:
        if on[j]:
            q = j
            while q < n and on[q]: q += 1
            if segs and j * 0.01 - segs[-1][1] < gap: segs[-1] = (segs[-1][0], q * 0.01)
            else: segs.append((j * 0.01, q * 0.01))
            j = q
        else: j += 1
    return [g for g in segs if g[1] - g[0] >= 0.05]


_WT = {}
def rel(i, frag):
    """文 i の声の頭から、frag を言い始めるまでの秒"""
    v = V[i]; t = v["text"]; k = t.find(frag)
    if k < 0: raise KeyError("%s に「%s」がない" % (i, frag))
    if i not in _WT:
        cut = [0] + [m.end() for m in re.finditer(r"[、。？！]+|……", t)] + [len(t)]
        ch = []
        for a, b in zip(cut, cut[1:]):
            if b > a and _ylen(t[a:b]) > 0: ch.append((a, b))
            elif ch and b > a: ch[-1] = (ch[-1][0], b)
        segs = _segments(v["wav"]); L = [max(1, _ylen(t[a:b])) for a, b in ch]
        rate = sum(g1 - g0 for g0, g1 in segs) / sum(L); nC, nS = len(ch), len(segs); INF = 1e18
        if nS < nC: _WT[i] = None
        else:
            D = [[INF] * (nS + 1) for _ in range(nC + 1)]; B = [[None] * (nS + 1) for _ in range(nC + 1)]; D[0][0] = 0
            for c in range(1, nC + 1):
                for sj in range(c, nS - (nC - c) + 1):
                    for sp in range(c - 1, sj):
                        if D[c - 1][sp] >= INF: continue
                        dur = segs[sj - 1][1] - segs[sp][0]; cost = D[c - 1][sp] + math.log(max(dur, 0.05) / (L[c - 1] * rate)) ** 2
                        if cost < D[c][sj]: D[c][sj] = cost; B[c][sj] = sp
            asg = []; sj = nS
            for c in range(nC, 0, -1): sp = B[c][sj]; asg.append((segs[sp][0], segs[sj - 1][1])); sj = sp
            _WT[i] = (ch, asg[::-1])
    sp = v["speed"] or 1.0
    if _WT[i] is None: return (v["end"] - v["start"]) * _ylen(t[:k]) / max(1, _ylen(t))
    ch, asg = _WT[i]
    for (a, b), (g0, g1) in zip(ch, asg):
        if a <= k < b: return (g0 + (g1 - g0) * _ylen(t[a:k]) / max(1, _ylen(t[a:b]))) / sp
    return asg[-1][0] / sp


def W(i, frag, o=0.0):
    """本編の秒：文 i で frag を言い始める時刻（＋ずらし o）"""
    return V[i]["start"] + rel(i, frag) + o


def dump(path):
    """PC の Blender でも言葉の時刻を使えるように、文ごとの「まとまり → 声の区間」を JSON に書く（声のファイルなしで W が出せる）"""
    out = {}
    for i, v in V.items():
        rel(i, v["text"][:1])
        out[i] = dict(text=v["text"], start=v["start"], end=v["end"], speed=v["speed"] or 1.0, wt=_WT[i])
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)


def load_table(path):
    """dump した表から W を作る（Blender の中で使う）。返り値：W(i, frag, o=0.0)"""
    tb = json.load(open(path, encoding="utf-8"))
    def Wt(i, frag, o=0.0):
        v = tb[i]; t = v["text"]; k = t.find(frag)
        if k < 0: raise KeyError("%s に「%s」がない" % (i, frag))
        sp = v["speed"]
        if v["wt"] is None: return v["start"] + (v["end"] - v["start"]) * _ylen(t[:k]) / max(1, _ylen(t)) + o
        ch, asg = v["wt"]
        for (a, b), (g0, g1) in zip(ch, asg):
            if a <= k < b: return v["start"] + (g0 + (g1 - g0) * _ylen(t[a:k]) / max(1, _ylen(t[a:b]))) / sp + o
        return v["start"] + asg[-1][0] / sp + o
    return Wt


if __name__ == "__main__":
    import sys
    dump(sys.argv[1] if len(sys.argv) > 1 else os.path.join(VO, "word_times.json")); print("ok")
