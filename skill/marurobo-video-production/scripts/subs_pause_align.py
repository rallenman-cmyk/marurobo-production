# 文の中の句読点（、。？！……）を、声の本当の間（無音）に 1 つずつ当てはめる（2026-11-23、9本目 v2 のコメント「テロップの切り替わりが早い／遅い」11 件）
#   v2 までは「字幕の切り替わりの近くにある、いちばん近い声の切れ目（小さな谷も入れる）」に合わせていた。
#   そのため、文の区切りの長い間（0.5〜0.9 秒）ではなく、その手前の言葉の中の小さな谷に合わせてしまい、字幕が 1〜1.5 秒早く替わった
#   （「上では消えて、下では出てくる。｜いったい…」が「出てくる」の途中で替わった）。関所の測り（subs_sync_check.py）も同じ見つけ方だったので、通ってしまった。
#   ここでは：
#     ① 声の無音（0.12 秒以上）を全部出す
#     ② 文の句読点を、読みの長さの割合から出した時刻の順に、無音へ 1 対 1 で当てはめる（順番は入れかえない。間のない句読点もある）。
#        「。？！……」は長い間になりやすいので、長い無音ほど当てやすくする
#     ③ 句読点ごとに「その句読点のあとで声がまた出る時刻（無音の終わり）」を返す。字幕は、そこから 0.05 秒前に替える
#   使い方：import subs_pause_align as PA;  PA.align(text, start, wav_path, speed=1.0) → [(句読点の字の位置（その字の次）, 無音の終わりの時刻 or None, 無音の長さ), ...]
import wave
import numpy as np

STRONG = "。？！?!…"
PUNCT = "、。？！?!…"


def silences(wav, speed=1.0, min_len=0.12):
    """文の声の中の無音（文の頭・終わりは除く）：[(始め, 終わり)]（文の声の頭からの秒）"""
    with wave.open(wav) as w:
        sr, ch = w.getframerate(), w.getnchannels(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    hop = int(0.01 * sr); n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    db = np.convolve(db, np.ones(3) / 3, mode="same")
    sil = db < db.max() - 38
    out = []; i = 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]: j += 1
            if i > 0 and j < n and (j - i) * 0.01 >= min_len: out.append((i * 0.01 / speed, j * 0.01 / speed))
            i = j
        else: i += 1
    return out, n * 0.01 / speed


def _wt(u):
    return sum(0.35 if ch in "…" else (0.6 if ch in "、。？！「」　" else 1.0) for ch in u)


def align(text, start, wav, speed=1.0):
    """句読点ごとの (位置, 無音の終わりの時刻, 無音の長さ)。当てはまらない句読点は (位置, None, 0)"""
    S, dur = silences(wav, speed)
    # 句読点（続く「……」「。」は 1 つにまとめる）。文の最後の句読点は数えない
    P = []; k = 0
    while k < len(text):
        if text[k] in PUNCT:
            j = k
            while j < len(text) and text[j] in PUNCT: j += 1
            if j < len(text.rstrip(PUNCT + "　 ")) + 0:
                strong = any(c in STRONG for c in text[k:j])
                P.append((j, dur * _wt(text[:j]) / max(1e-6, _wt(text)), strong))
            k = j
        else: k += 1
    n, m = len(P), len(S)
    INF = 1e9
    # dp[i][j]：句読点 i 個・無音 j 個まで見たときの、いちばん小さい費用
    dp = [[INF] * (m + 1) for _ in range(n + 1)]; bk = [[None] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1): dp[0][j] = 0.0
    for i in range(1, n + 1):
        pos, est, strong = P[i - 1]
        for j in range(0, m + 1):
            # 句読点 i を当てない（間のない読点。「。」で間がないのは珍しいので重く）
            c = dp[i - 1][j] + (2.0 if strong else 1.0)
            if c < dp[i][j]: dp[i][j] = c; bk[i][j] = ("skip", j)
            # 無音 j を使わない（言葉の中の小さな無音）
            if j > 0 and dp[i][j - 1] < dp[i][j]: dp[i][j] = dp[i][j - 1]; bk[i][j] = ("free", j - 1)
            # 句読点 i を無音 j に当てる
            if j > 0:
                a, b = S[j - 1]; L = b - a
                c = dp[i - 1][j - 1] + abs(b - est) - (1.0 if strong else 0.3) * min(L, 0.8)
                if c < dp[i][j]: dp[i][j] = c; bk[i][j] = ("match", j - 1)
    res = [None] * n; i, j = n, m
    while i > 0:
        kind, jj = bk[i][j]
        if kind == "match": res[i - 1] = S[jj]; i, j = i - 1, jj
        elif kind == "skip": i, j = i - 1, jj
        else: j = jj
    return [(P[q][0], (start + res[q][1]) if res[q] else None, (res[q][1] - res[q][0]) if res[q] else 0.0) for q in range(n)]


def _nz(u):
    import re
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
        if pos == k: return None if tt is None else round(tt - 0.05, 3)
    return None
