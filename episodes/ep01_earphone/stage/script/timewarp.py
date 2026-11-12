# 台本 v1（元の時刻）→ 台本 v2（新しい時刻）の時刻の対応。すでに作った絵（図など）を、新しい台本の時刻に合わせて流すのに使う
#   ・変えていない文：同じ長さ・同じ間なので、元の時刻をそのままずらす
#   ・新しく足した文の間：直前の文の終わりの絵で止めて待つ（元の時刻は進まない）
#   使い方：W = Warp(t0_old, t1_old)。W.old_of(新しい時刻) → 元の時刻、W.new_of(元の時刻) → 新しい時刻
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))


def _sec(x):
    hh, mm, rr = x.strip().split(":"); s_, ms = rr.split(","); return int(hh) * 3600 + int(mm) * 60 + int(s_) + int(ms) / 1000


def old_lines():
    O = {}
    for i, b in enumerate(open(os.path.join(HERE, "bluetooth_full_native_rev1.srt"), encoding="utf-8").read().strip().split("\n\n")):
        x = b.split("\n"); a, c = x[1].split(" --> "); O[i + 1] = (_sec(a), _sec(c), " ".join(x[2:]))
    return O


def new_lines():
    V2 = {e["no"]: e for e in json.load(open(os.path.join(HERE, "script_v2.json"), encoding="utf-8"))}
    TM = {e["no"]: e for e in json.load(open(os.path.join(HERE, "script_v2_timed.json"), encoding="utf-8"))}
    return V2, TM


class Warp:
    def __init__(self, t0_old, t1_old):
        O = old_lines(); V2, TM = new_lines()
        knots = []                                                       # (新, 元)：変えていない文の始めと終わり
        for no, e in V2.items():
            if e["kind"] != "keep": continue
            a, c, _ = O[e["old_no"]]
            if not (t0_old - 1e-6 <= a < t1_old): continue
            na, nc = TM[no]["start"], TM[no]["end"]
            knots.append((na, a)); knots.append((nc, c))
        knots.sort()
        # 足した文の所：前の文の終わり（元）で止めて待ち、次の文の始めの「元の間」の分だけ前から動き出す
        out = [knots[0]]
        for (n1, o1) in knots[1:]:
            n0, o0 = out[-1]
            gap_old = o1 - o0; gap_new = n1 - n0
            if gap_new > gap_old + 0.05 and gap_old >= 0: out.append((n1 - gap_old, o0))
            out.append((n1, o1))
        self.k = out

    def old_of(self, tn):
        k = self.k
        if tn <= k[0][0]: return k[0][1] + (tn - k[0][0])
        for (n0, o0), (n1, o1) in zip(k, k[1:]):
            if tn <= n1: return o0 + (o1 - o0) * (tn - n0) / max(n1 - n0, 1e-9)
        return k[-1][1] + (tn - k[-1][0])

    def new_of(self, to):
        k = self.k
        if to <= k[0][1]: return k[0][0] + (to - k[0][1])
        for (n0, o0), (n1, o1) in zip(k, k[1:]):
            if to <= o1 and o1 > o0: return n0 + (n1 - n0) * (to - o0) / (o1 - o0)
        return k[-1][0] + (to - k[-1][1])


def line_time(no):
    """台本 v2 の通し番号 → (始め, 終わり, 文)"""
    _, TM = new_lines(); e = TM[no]; return e["start"], e["end"], e["text"]


def find(text_head):
    """文の頭で、台本 v2 の文を探す → (通し番号, 始め, 終わり)"""
    _, TM = new_lines()
    for no, e in sorted(TM.items()):
        if e["text"].startswith(text_head): return no, e["start"], e["end"]
    raise KeyError(text_head)


if __name__ == "__main__":
    W = Warp(161.0, 244.7)
    for tn, to in W.k: print("new %7.2f  old %7.2f" % (tn, to))
    for t in (180.0, 186.0, 192.0, 194.0, 230.0, 260.0, 270.0, 274.0): print(t, "->", round(W.old_of(t), 2))
