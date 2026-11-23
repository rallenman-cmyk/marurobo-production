# 16本目 v1 のコメント（「テロップの切り替わりが早い」2 件・「間のばらつき・食い気味」）から作った、声の中の「区切り」を探す道具
#   文の中の読点・句点（、。？！……）の位置を、読み（カナ）の長さの割合で声の中の時刻に直し、いちばん近い声の切れ目（無音）を返す。
#   声の出ている所だけで割合を数える（無音は数えない）ので、間の長さに引っぱられない。
#   import pauses as PZ; PZ.marks(text) → [(文字の位置, 記号)]、PZ.cut_time(wav, tts, k) → k 番目の記号のあとの (無音の始め, 終わり)
import re, wave
import numpy as np
import pykakasi
_K = pykakasi.kakasi()
PUNCT = re.compile(r"……|[、。？！]")


def kana_len(s):
    s = re.sub(r"[「」『』（）\s　]", "", s)
    n = 0
    for it in _K.convert(s):
        h = it["hira"]
        n += len(re.sub(r"[ゃゅょぁぃぅぇぉ、。？！…]", "", h))
    return n


def marks(text):
    """文の中の区切り記号の位置（最後の記号は除く）"""
    out = [(m.end(), m.group()) for m in PUNCT.finditer(text)]
    return [o for o in out if text[o[0]:].strip("。？！…、　 」") != ""]


def env(path, hop=0.01, thr=-40.0):
    with wave.open(path) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    n = int(hop * sr); m = len(x) // n
    db = 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9)
    return db > thr, hop


def runs(v, hop, min_len=0.03):
    """声の中の無音（頭と終わりの無音は除く）：[(始め秒, 終わり秒)]"""
    idx = np.where(v)[0]
    if not len(idx): return []
    a, b = idx[0], idx[-1]; r = []; s = None
    for i in range(a, b + 1):
        if not v[i] and s is None: s = i
        if v[i] and s is not None:
            if (i - s) * hop >= min_len: r.append((s * hop, i * hop))
            s = None
    return r


def cut_time(path, tts, k):
    """tts（読みの文）の k 番目の区切り記号のあとの、声の切れ目 (始め, 終わり)。見つからなければ None"""
    v, hop = env(path)
    rs = runs(v, hop)
    if not rs: return None
    mk = marks(tts)
    if k >= len(mk): return None
    pos = mk[k][0]
    frac = kana_len(tts[:pos]) / max(1, kana_len(tts))
    voiced = np.cumsum(v) * hop                      # 声の出ている時間の積み上げ
    total = voiced[-1]
    target = frac * total
    best = None
    for (s, e) in rs:
        vpos = voiced[min(len(voiced) - 1, int(round(s / hop)))]
        d = abs(vpos - target) - 0.15 * min(e - s, 0.6)   # 近さを第一に、少しだけ長い無音をひいきする
        if best is None or d < best[0]: best = (d, s, e, abs(vpos - target))
    return (best[1], best[2]) if best else None


def cut_all(path, tts, miss=0.50):
    """全部の区切り記号を、順番を守って別々の切れ目に割りふる（切れ目のない記号は None）。[(記号の位置, 記号, (始め, 終わり) or None)]"""
    v, hop = env(path); rs = runs(v, hop); mk = marks(tts)
    if not mk: return []
    voiced = np.cumsum(v) * hop; total = voiced[-1] if len(voiced) else 1
    # 区切りごとの読みの長さ。「え？」のような短い声は、のばして読むので 4 文字ぶんとして数える
    seg = []; prev = 0
    for p_, c_ in mk + [(len(tts), "")]:
        k_ = kana_len(tts[prev:p_]); seg.append(max(k_, 4) if c_ in ("？", "！") or (p_ == len(tts) and k_ <= 2) else k_); prev = p_
    tot = max(1, sum(seg)); T = [sum(seg[:i + 1]) / tot * total for i in range(len(mk))]
    P = [voiced[min(len(voiced) - 1, int(round(s / hop)))] for s, e in rs]
    n, m = len(mk), len(rs)
    INF = 1e9
    # dp[i][j]：記号 i 個と切れ目 j 個まで見たときの最小の費用
    dp = [[INF] * (m + 1) for _ in range(n + 1)]; bk = [[None] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1): dp[0][j] = 0.0
    for i in range(1, n + 1):
        for j in range(0, m + 1):
            c = dp[i - 1][j] + miss                       # 記号 i に切れ目なし
            if c < dp[i][j]: dp[i][j], bk[i][j] = c, ("miss", j)
            if j >= 1:
                c = dp[i][j - 1]                          # 切れ目 j を使わない
                if c < dp[i][j]: dp[i][j], bk[i][j] = c, ("skip", j - 1)
                s, e = rs[j - 1]
                # 長い無音ほど、どれかの記号の切れ目（「え？」のように、のばして読む所は割合より長くなるため、長い無音を強くひいきする）。文の終わり（。？！）はさらにひいき
                c = dp[i - 1][j - 1] + abs(P[j - 1] - T[i - 1]) - 0.5 * min(e - s, 0.6) - (0.2 if mk[i - 1][1] in "。？！" and e - s >= 0.2 else 0.0) - (0.6 if mk[i - 1][1] == "……" and e - s >= 0.4 else 0.0)   # 「……」はためて読むので、長い間がほぼ必ずそのあと
                if c < dp[i][j]: dp[i][j], bk[i][j] = c, ("use", j - 1)
    out = [None] * n; i, j = n, m
    while i > 0:
        kind, jj = bk[i][j]
        if kind == "use": out[i - 1] = rs[jj]; i -= 1; j = jj
        elif kind == "miss": i -= 1
        else: j = jj
    return [(mk[k][0], mk[k][1], out[k]) for k in range(n)]
