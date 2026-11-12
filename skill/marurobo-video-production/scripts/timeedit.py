# 章の中の時間の直し（2026-11-09 ユーザー：間が長い所を 0.8 秒に・声の前に間を足す）
#   元の時刻（本編の秒。絵・図・3D・効果音はこの時刻で作ってある）と、出す時刻の対応を、区間の並びで決める
#   区間 (s0, s1, L)：元の [s0, s1) を、出す長さ L にする
#     L = 0           … 切る（止まった絵の所を切る。輪の模様のように繰り返す絵は、繰り返しの長さで切ると継ぎ目が見えない）
#     s0 == s1, L > 0 … その時刻で絵を止めて L 秒のばす（声の前に間を足す）
#     0 < L < s1 - s0 … 少し速くする（動き続けている所を短くする）
#   声・字幕は「始まり」を写し、長さはそのまま（声を切ったり伸ばしたりしない）
class TimeEdit:
    def __init__(self, segs):
        self.S = sorted((float(a), float(b), float(L)) for a, b, L in segs)

    def out(self, t):
        """元の時刻 → 出す時刻"""
        off = 0.0
        for s0, s1, L in self.S:
            if t < s0: break
            if s1 > s0 and t < s1: return s0 + off + (t - s0) * L / (s1 - s0)
            off += L - (s1 - s0)
        return t + off

    def src(self, t):
        """出す時刻 → 元の時刻（絵をどの時刻で描くか）"""
        off = 0.0
        for s0, s1, L in self.S:
            o0 = s0 + off
            if t < o0: return t - off
            if t < o0 + L: return s0 if s1 <= s0 else s0 + (t - o0) * (s1 - s0) / L
            off += L - (s1 - s0)
        return t - off

    def shift(self, t):
        """その時刻で始まるものを、どれだけずらすか（出す − 元）"""
        return self.out(t) - t

    def place(self, P, override=None):
        """声の置き場所（placement の写し）を出す時刻へ。始まりを写し、長さはそのまま。
        override：{文の番号: 出す時刻での始まり}（間を決めて置く文）"""
        out = []
        for p in P:
            q = dict(p); a = self.out(p["start"]); d = p["end"] - p["start"]
            if override and p["no"] in override: a = override[p["no"]]
            q["start"], q["end"] = round(a, 4), round(a + d, 4); out.append(q)
        return out

    def subs(self, lines, override_txt=None):
        """字幕 [(始まり, 終わり, 文)] を出す時刻へ。始まりを写し、長さはそのまま（次の字幕の 0.05 秒前まで）
        override_txt：{文: 出す時刻での始まり}"""
        res = []
        for a, c, t in sorted(lines):
            a2 = override_txt[t] if override_txt and t in override_txt else self.out(a)
            res.append([a2, a2 + (c - a), t])
        res.sort()
        for i in range(len(res) - 1):
            res[i][1] = min(res[i][1], res[i + 1][0] - 0.05)
        return [tuple(r) for r in res]


if __name__ == "__main__":
    te = TimeEdit([(10, 13, 0), (20, 20, 0.5), (30, 37, 6)])
    for t in (5, 10, 11, 13, 15, 20, 21, 30, 33.5, 37, 40):
        o = te.out(t); print("src %.2f → out %.3f → src %.3f" % (t, o, te.src(o)))
