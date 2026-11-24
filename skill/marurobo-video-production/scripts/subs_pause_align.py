# 文の中の句読点（、。？！……）を、声の本当の間（無音）に 1 つずつ当てはめる（2026-11-23、9本目 v2 のコメント「テロップの切り替わりが早い／遅い」11 件）
#   v2 までは「字幕の切り替わりの近くにある、いちばん近い声の切れ目（小さな谷も入れる）」に合わせていた。
#   そのため、文の区切りの長い間（0.5〜0.9 秒）ではなく、その手前の言葉の中の小さな谷に合わせてしまい、字幕が 1〜1.5 秒早く替わった。
#
#   2026-11-23 改め（9本目 v3 の点検。16本目の subs_mora.py の check で 6 枚ずれていた）：
#   はじめの作り（声の大きさの最大から -38dB を無音・0.12 秒以上・字数の割合）は、
#     ① 1 つの間が小さな音で 2 つに分かれ、前半の終わりに合わせた（「そろって、｜平らな床に」が 0.8 秒早い。3 枚）
#     ② 0.08 秒の短い間を拾えず、残った 1 つの長い間を別の読点に当てた（「おじさんが、｜段を」が 1.1 秒早い）
#     ③ 文の頭の息を声の頭と見た（「出てきました！」が 0.9 秒早い）
#   → 16本目の pauses.py と同じ見つけ方にした：無音は決まった大きさ（-40dB）より小さい所・0.03 秒から、
#     句読点の位置は「読み（かな）の長さ」の割合を「声の出ている時間だけ」に当てる。順番を守って 1 対 1 で当てはめる（間のない句読点もある）。
#     長い間ほど句読点に当てやすく、「。？！」「……」はさらに。文の頭は onset()（-40dB をこえる最初の所）。
#   使い方：import subs_pause_align as PA
#     PA.align(text, start, wav) → [(句読点の字の位置（その字の次）, 間の終わりの時刻 or None, 間の長さ), ...]
#     PA.target(line, sub_text, wav) → 字幕を替える時刻（声がまた出る 0.05 秒前） or None
#     PA.onset(wav) → 声の頭（文の声のファイルの頭からの秒）
import re, wave
import numpy as np

STRONG = "。？！?!…"
PUNCT = re.compile(r"……|…|[、。？！?!]")
THR, HOP, MIN_SIL = -40.0, 0.01, 0.03
try:
    import pykakasi
    _K = pykakasi.kakasi()
except Exception:                      # pykakasi がないときは、字数で数える
    _K = None


def kana_len(s):
    s = re.sub(r"[「」『』（）\s　]", "", s)
    # 数字は読むと長い（30＝さんじゅう、2024＝にせんにじゅうよ）。1 けたを かな 2.5 字として数える
    #   （182「1分間に30メートル」：数字を 1 字と数えて読点の位置を後ろに見積もり、「いっぷん」の「っ」の無音に当てた）
    s = re.sub(r"[0-9０-９]+", lambda m_: "ア" * int(2.5 * len(m_.group()) + 0.5), s)
    if _K is None: return len(re.sub(r"[、。？！…]", "", s))
    return sum(len(re.sub(r"[ゃゅょぁぃぅぇぉ、。？！…]", "", it["hira"])) for it in _K.convert(s))


def _db(wav):
    with wave.open(wav) as w:
        sr, ch = w.getframerate(), w.getnchannels(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    n = int(HOP * sr); m = len(x) // n
    return 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9)


def _env(wav):
    return _db(wav) > THR


def onset(wav):
    v = _env(wav); idx = np.where(v)[0]
    return idx[0] * HOP if len(idx) else 0.0


def silences(wav, speed=1.0, min_len=MIN_SIL):
    """文の声の中の無音（頭と終わりは除く）：[(始め, 終わり)]、声の長さ"""
    v = _env(wav); idx = np.where(v)[0]
    if not len(idx): return [], len(v) * HOP
    a, b = idx[0], idx[-1]; r = []; s = None
    for i in range(a, b + 1):
        if not v[i] and s is None: s = i
        if v[i] and s is not None:
            if (i - s) * HOP >= min_len: r.append((s * HOP / speed, i * HOP / speed))
            s = None
    # 0.1 秒以下の小さな音（息・口の音）で 2 つに分かれた間は、1 つの間にまとめる（182「エスカレーターは、｜いっぷんかんに」：
    #   本当の間 0.73 秒＋0.1 秒の音＋0.21 秒が分かれ、「いっぷん」の「っ」の 0.06 秒の無音に読点を当てて、字幕が 0.2 秒おくれた）
    #   ただし、まとめるのは、間にはさまった音が声より 15 dB 以上小さいときだけ（16本目 2章 15-06「からは、｜よ｜こ」：
    #   「よ」の 0.08 秒（-16 dB、ふつうの声と同じ大きさ）のあとに「こ」の前の詰まり 0.08 秒があり、「よ」を息と見て間をまとめ、
    #   「よ」の頭で正しく替わる字幕を「0.16 秒早い」と数えていた）
    db = _db(wav); pk = db.max()
    m = []
    for a_, b_ in r:
        quiet = m and db[int(m[-1][1] * speed / HOP):max(int(m[-1][1] * speed / HOP) + 1, int(a_ * speed / HOP))].max() < pk - 15
        if m and quiet and a_ - m[-1][1] <= 0.105 / speed and (b_ - a_) >= 0.08 / speed and (m[-1][1] - m[-1][0]) >= 0.08 / speed: m[-1] = (m[-1][0], b_)
        else: m.append((a_, b_))
    return m, len(v) * HOP / speed


def _marks(text):
    """文の中の句読点（続く記号は 1 つ。文の最後は除く）：[(記号の次の位置, 記号)]"""
    out = []
    for m in PUNCT.finditer(text):
        if out and m.start() == out[-1][0]: out[-1] = (m.end(), out[-1][1] + m.group()); continue
        out.append((m.end(), m.group()))
    # 文の頭の記号（「……え？」の「……」）は、前に声がないので間に当てない（17本目 v1：頭の「……」が「え」のあとの間を取り、
    #   「？」が次の読点の間に当たって、合っている字幕を「1.04 秒早い」と数えた）
    out = [o for o in out if text[:o[0]].strip("…、。？！?!　 「") != ""]
    return [o for o in out if text[o[0]:].strip("。？！?!…、　 」") != ""]


def align(text, start, wav, speed=1.0, miss=0.50):
    v = _env(wav); S, dur = silences(wav, speed)
    mk = _marks(text)
    if not mk: return []
    voiced = np.cumsum(v) * HOP; total = voiced[-1] if len(voiced) else 1.0
    seg = []; prev = 0
    for p_, c_ in mk + [(len(text), "")]:
        k_ = kana_len(text[prev:p_]); seg.append(max(k_, 4) if c_ in ("？", "！") or (p_ == len(text) and k_ <= 2) else k_); prev = p_
    tot = max(1, sum(seg)); T = [sum(seg[:i + 1]) / tot * total for i in range(len(mk))]
    Pv = [voiced[min(len(voiced) - 1, int(round(s * speed / HOP)))] for s, e in S]
    n, m = len(mk), len(S); INF = 1e9
    dp = [[INF] * (m + 1) for _ in range(n + 1)]; bk = [[None] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1): dp[0][j] = 0.0
    for i in range(1, n + 1):
        sym = mk[i - 1][1]
        for j in range(0, m + 1):
            c = dp[i - 1][j] + miss
            if c < dp[i][j]: dp[i][j], bk[i][j] = c, ("miss", j)
            if j >= 1:
                if dp[i][j - 1] < dp[i][j]: dp[i][j], bk[i][j] = dp[i][j - 1], ("skip", j - 1)
                s, e = S[j - 1]; L = e - s
                c = dp[i - 1][j - 1] + abs(Pv[j - 1] - T[i - 1]) - 0.5 * min(L, 0.6) \
                    - (0.2 if any(ch in "。？！?!" for ch in sym) and L >= 0.2 else 0.0) - (0.6 if "…" in sym and L >= 0.4 else 0.0)
                if c < dp[i][j]: dp[i][j], bk[i][j] = c, ("use", j - 1)
    res = [None] * n; i, j = n, m
    while i > 0:
        kind, jj = bk[i][j]
        if kind == "use": res[i - 1] = S[jj]; i -= 1; j = jj
        elif kind == "miss": i -= 1
        else: j = jj
    # 当てはまらなかった句読点：前後の当てはまった間のあいだに残った間（0.05 秒以上）から、見積もりにいちばん近い物を当てる
    #   （79「おじさんが、｜段を」：0.08 秒の短い間が、見積もりから少し離れていて当てられず、字幕が言葉の谷へ 0.43 秒早く替わった）
    used = set(id(x) for x in res if x)
    for q in range(n):
        if res[q] is not None: continue
        lo = max([res[r][1] for r in range(q) if res[r]] or [-1.0]); hi = min([res[r][0] for r in range(q + 1, n) if res[r]] or [1e9])
        cand = [(abs(Pv[j_] - T[q]), S[j_]) for j_ in range(m) if lo <= S[j_][0] and S[j_][1] <= hi and S[j_][1] - S[j_][0] >= 0.05 and id(S[j_]) not in used]
        if cand:
            d_, best = min(cand, key=lambda x: x[0])
            if d_ <= 0.8: res[q] = best; used.add(id(best))
    return [(mk[q][0], (start + res[q][1]) if res[q] else None, (res[q][1] - res[q][0]) if res[q] else 0.0) for q in range(n)]


def _nz(u):
    return re.sub(r"\{.*?\}|\\N|[\s　]", "", u)


_CACHE = {}


def target(line, sub_text, wav):
    """字幕 sub_text が、文 line（placement の 1 行）の途中から始まるとき、替える時刻（声がまた出る 0.05 秒前）。
    句読点のあとでない・間が当てはまらないときは None"""
    t = line["text"]; s0 = _nz(sub_text)[:8]
    k = t.find(s0) if s0 else -1
    if k <= 0: return None
    key = (line["no"], wav)
    if key not in _CACHE: _CACHE[key] = align(t, line["start"], wav, line.get("speed", 1.0))
    for pos, tt, L in _CACHE[key]:
        if pos <= k and t[pos:k].strip("　 「」") == "": return None if tt is None else round(tt - 0.05, 3)
    return None
