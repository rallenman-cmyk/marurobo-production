# 7本目：字幕を 1 行ずつにする（2026-11-16 ユーザー「メインのテロップを1行目と2行目で別にして」「ところがはテロップ別にして」）
#   ① 文の中の「。」「？」「！」で必ず分ける（「なるほど、と思いますよね。」「ところが……。」は別の字幕）
#   ② それぞれを subs_jp の区切り（読点・「……」）で 2 行ぶんに分け、その 2 行も別の字幕にする（1 回に 1 行だけ）
#   ③ 切り替える時刻（v8 で作り直し。2026-11-20 ユーザー「テロップの切り替わりがすごい早い」25 件）：
#      読みがなの長さの割合から「その行を読み始める時刻」を出し、その前後 0.35 秒の中にある声の切れ目にだけ合わせる。
#      v7 までは「字数の割合にいちばん近い切れ目」を、どれだけ離れていても使っていた。0.1 秒より短い切れ目を候補から外していたので、
#      読点の長い切れ目ばかり選ばれ、1 行目が 1.2 秒で消えて 2 行目が声より先に出ていた。
#   ④ 1 枚は MIN（2.0 秒）以上。短い 1 枚は、となりとまとめても 1 行（LINE_MAX 字）に入るならまとめる
#   ⑤ 分け方を決めた文（PIECES）は、そのとおりに分ける（ユーザーの指定）
import re, os, json

MIN = 2.0
LINE_MAX = 25          # 1 行に入る字数（assemble.py の「25 字をこえる字幕」の点検と同じ）
PIECES = {             # 文の最初の字 → 分け方（ユーザーの指定）
    "先生は、なんと「もっと速く！」と声をかけたそうです。": ["先生は、なんと", "「もっと速く！」と声をかけたそうです。"],   # v7 0:496「なんとの後から次のテロップにして」
    "タイプライターは、まず電信の仕事のための道具として、売りこまれていたのですね。": ["タイプライターは、", "まず電信の仕事のための道具として、", "売りこまれていたのですね。"],   # v7 0:505「として、で次のテロップにして」
}


def pieces(t, SJ, sid=None):
    """sid にリストを渡すと、それぞれの 1 枚がどの文（。？！で区切った文）から来たかを入れる"""
    if t in PIECES:
        if sid is not None: sid[:] = list(range(len(PIECES[t])))
        return list(PIECES[t])
    out = []
    for k, sen in enumerate([x for x in re.split(r'(?<=[。？！])(?=[^」』）])', t) if x.strip()]):
        for card in SJ.plan_tame(sen):
            for x in card.split("\\N"):
                if x:
                    out.append(x)
                    if sid is not None: sid.append(k)
    return out


def _vlen(p):
    return len(p.replace(" ", ""))


_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = {x["text"]: x for x in json.load(open(os.path.join(_HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
_PH = lambda s: [x for x in re.split(r'(?<=[、。？！…])(?![、。？！…」』）])', s) if x.strip()]
_KDROP = set("、。？！…「」『』（）・ 　,.!?")
KEEP_HEAD = ("ところが", "でも、", "しかし")      # この言葉で始まる 1 枚は、前とまとめない（ユーザー「ところがはテロップ別にして」）


def _klen(s):
    return max(1, sum(1 for ch in s if ch not in _KDROP))


def kana_weights(t, ps):
    """それぞれの 1 枚の、読み（声に読ませたかな）の長さ。字の数でなく読みで測る（「Z」は「ゼット」、「Q W E」は「キュー、ダブリュー、イー」）。
    字幕の文と読みがなを、句読点の区切りで合わせる。区切りの数が合わない文は、文（。？！）ごとに合わせて、その中は字の数の割合"""
    tts = _SCRIPT.get(t, {}).get("tts") or t
    a, b = _PH(t), _PH(tts)
    ends, k = [], 0
    for x in ps: k += len(x); ends.append(k)
    if len(a) == len(b):
        pos = []; k = 0
        for x in a: k += len(x); pos.append(k)
        if all(e in pos for e in ends):
            w = []; j0 = 0
            for e in ends:
                j1 = pos.index(e) + 1; w.append(sum(_klen(y) for y in b[j0:j1])); j0 = j1
            return w
    sen = lambda u: [x for x in re.split(r'(?<=[。？！])', u) if x.strip()]
    sa, sb = sen(t), sen(tts)
    if len(sa) != len(sb): sa, sb = [t], [tts]
    # 字の位置ごとの読みの重み
    per = []
    for x, y in zip(sa, sb): per += [_klen(y) / max(1, len(x))] * len(x)
    per += [1.0] * (len(t) - len(per))
    w = []; j0 = 0
    for e in ends: w.append(max(1.0, sum(per[j0:e]))); j0 = e
    return w


def _cands(wav, speed, SJ):
    """切ってよい所の候補：①声のない間（0.07 秒以上）②言葉の切れ目で声が小さくなる所（前後 0.15 秒の山より 6 dB 以上低い谷）。
    [(時刻＝次の声が出る所, 強さ)] と、声の出ている所の始まり・終わり（声の頭からの秒）"""
    import wave
    import numpy as np
    runs, dur = SJ.gaps(wav, speed)
    mr = []
    for g0, g1 in runs:
        if mr and g0 - mr[-1][1] < 0.06: mr[-1] = (mr[-1][0], g1)
        else: mr.append((g0, g1))
    head = mr[0][1] if mr and mr[0][0] <= 0.02 else 0.0
    tail = mr[-1][0] if mr and mr[-1][1] >= dur - 0.02 else dur
    gaps = [(g0, g1) for g0, g1 in mr if head < g0 and g1 < tail and g1 - g0 >= 0.07]
    out = [(g1, 3.0 + 4.0 * min(g1 - g0, 1.0)) for g0, g1 in gaps]     # 声が止まる間は、言葉の切れ目の谷よりずっと強く選ぶ（v9：「からむので、」の 0.5 秒の間より、手前の谷を選んでいた）
    with wave.open(wav) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    hop = int(0.01 * sr); n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    db = np.convolve(db, np.ones(3) / 3, mode="same")
    for k in range(15, n - 15):
        t = k * 0.01 / speed
        if not (head + 0.2 < t < tail - 0.2) or any(g0 - 0.05 <= t <= g1 + 0.05 for g0, g1 in gaps): continue
        if db[k] == db[k - 5:k + 6].min():
            depth = min(db[k - 15:k].max(), db[k + 1:k + 16].max()) - db[k]
            if depth >= 6: out.append((t + 0.03 / speed, 0.3 + min(depth, 20) / 40))
    return sorted(out), head, tail, gaps


def events(a, c, t, wav, SJ, speed=1.0, MIN=MIN, c_max=None, log=None):
    """文 t（声 a〜c 秒）の 1 行ずつの字幕 [(始め, 終わり, 字), …]。（v9、2026-11-21 ユーザー「なんでテロップのタイミングまだ治ってないの」）
    ① 切り替えるのは、声のない間（声が止まっている所）だけ。時刻をずらして長さを合わせることはしない
    ② どの間で切るかは、読み（かな）の長さで見積もった所に近く、長い間ほどよい組み合わせを、全部の組み合わせから選ぶ
    ③ 声が MIN 秒より短い 1 枚は、となりとまとめる（ユーザー「となりとまとめる」。1 行 LINE_MAX 字まで。「ところが」などで始まる 1 枚と、PIECES の分け方はまとめない）
    ④ 最後の 1 枚だけ、声のあとの無音（c_max まで）へのばして MIN にする"""
    c_max = max(c, c_max or c)
    ps = pieces(t, SJ)
    keep = set(range(1, len(ps))) if t in PIECES else {i for i in range(1, len(ps)) if ps[i].startswith(KEEP_HEAD)}
    try: C, head, tail, gaps = _cands(wav, speed, SJ)
    except Exception: C, head, tail, gaps = [], 0.0, c - a, []
    vt = lambda x: (x - head) - sum(max(0.0, min(g1, x) - g0) for g0, g1 in gaps if g0 < x)     # 声の出ている時間
    vtot = vt(tail)
    w = kana_weights(t, ps)
    # ② 切る所を選ぶ：k 個の切れ目を、候補の中から順に選ぶ（見積もり（読みの長さの割合）とのずれ（秒）の 2 乗 − 候補の強さ）
    def choose(ps, w):
        k = len(ps) - 1
        if k == 0: return []
        if len(C) < k: return None
        tot = sum(w); exp = [vtot * sum(w[:i + 1]) / tot for i in range(k)]
        G = [(vt(tc), st) for tc, st in C]
        INF = 1e9; n = len(G)
        dp = [[INF] * n for _ in range(k)]; bk = [[-1] * n for _ in range(k)]
        cost = lambda i, j: ((G[j][0] - exp[i]) / 0.6) ** 2 - G[j][1]
        for j in range(n): dp[0][j] = cost(0, j)
        for i in range(1, k):
            for j in range(i, n):
                best = min(range(i - 1, j), key=lambda q: dp[i - 1][q]); dp[i][j] = dp[i - 1][best] + cost(i, j); bk[i][j] = best
        j = min(range(k - 1, n), key=lambda q: dp[k - 1][q]); out = [j]
        for i in range(k - 1, 0, -1): j = bk[i][j]; out.append(j)
        return [C[q][0] for q in reversed(out)]
    def merge(i):          # i 番目と i+1 番目を 1 枚に
        nonlocal ps, w, keep
        ps = ps[:i] + [ps[i] + ps[i + 1]] + ps[i + 2:]; w = w[:i] + [w[i] + w[i + 1]] + w[i + 2:]
        keep = {x - 1 if x > i + 1 else x for x in keep if x != i + 1}
    can = lambda i: i + 1 not in keep and _vlen(ps[i] + ps[i + 1]) <= LINE_MAX
    while True:
        cut = choose(ps, w)
        if cut is None:    # 間が足りない：まとめられる所のうち、いちばん短い組をまとめる
            opts = [i for i in range(len(ps) - 1) if can(i)]
            if not opts: raise RuntimeError("声の間が足りず、まとめると 1 行に入らない：" + t)
            merge(min(opts, key=lambda i: w[i] + w[i + 1])); continue
        ts = [a] + [a + x - 0.05 for x in cut] + [c]     # 次の 1 枚は、声が出る少し前（0.05 秒）に出す
        lens = [ts[i + 1] - ts[i] for i in range(len(ps))]
        lens[-1] = min(c_max, ts[-2] + max(MIN, lens[-1])) - ts[-2]
        short = [i for i in range(len(ps)) if lens[i] < MIN - 0.005]
        # ③ 声が短い 1 枚は、となりとまとめる（短い方のとなりを先に）
        done = False
        for i in sorted(short, key=lambda i: lens[i]):
            for j in sorted([i - 1, i + 1], key=lambda j: lens[j] if 0 <= j < len(ps) else 99):
                if 0 <= j < len(ps) and can(min(i, j)): merge(min(i, j)); done = True; break
            if done: break
        if done: continue
        break
    ts = [a] + [a + x - 0.05 for x in cut]
    ends = ts[1:] + [max(c, min(c_max, ts[-1] + MIN))]
    out = [[ts[i], ends[i], ps[i]] for i in range(len(ps))]
    # ⑤ まとめると 1 行に入らない短い 1 枚は、となりと合わせた文を、別の言葉の切れ目で分け直す（両方 MIN 以上・LINE_MAX 字以内になる所）
    tot_w = sum(kana_weights(t, [x[2] for x in out])); full = "".join(x[2] for x in out)
    def at_time(pos):      # 文の pos 字目を読み始める時刻（読みの割合で見積もり、近い候補（0.3 秒以内）に合わせる）
        wv = kana_weights(t, [full[:pos], full[pos:]])[0] if 0 < pos < len(full) else 0
        est = vtot * wv / sum(kana_weights(t, [full]))
        near = [(abs(vt(tc) - est), tc) for tc, st in C if abs(vt(tc) - est) <= 0.45]
        if not near: return None
        return a + min(near)[1] - 0.05
    BRK = "、」…"           # 分け直すのは「、」「」」「……」のあとだけ（v9 の 1 回目は助詞のあとでも切り、「はずなの／に」のように言葉の途中で切った）
    for _ in range(3):
        for i in range(len(out)):
            if out[i][1] - out[i][0] >= MIN - 0.005: continue
            for j in ([i - 1, i + 1] if i > 0 else [i + 1]):
                if not (0 <= j < len(out)) or (max(i, j) in keep): continue
                i0, i1 = min(i, j), max(i, j); txt = out[i0][2] + out[i1][2]
                base = len("".join(x[2] for x in out[:i0]))
                best = None
                for k in range(2, len(txt) - 1):
                    if txt[k - 1] not in BRK or txt[k] in "、。？！…」』）" or _vlen(txt[:k]) > LINE_MAX or _vlen(txt[k:]) > LINE_MAX: continue
                    tm = at_time(base + k)
                    if tm is None: continue
                    l0, l1 = tm - out[i0][0], out[i1][1] - tm
                    if min(l0, l1) >= MIN - 0.005 and (best is None or min(l0, l1) > best[0]): best = (min(l0, l1), k, tm)
                if best:
                    _, k, tm = best
                    out[i0] = [out[i0][0], tm, txt[:k]]; out[i1] = [tm, out[i1][1], txt[k:]]; break
    out = [tuple(x) for x in out]
    if log is not None:
        for s0, s1, x in out:
            if s1 - s0 < MIN - 0.005: log.append((round(s0, 2), round(s1 - s0, 2), x))
    return out


def balance(L, MIN=MIN, CPS=8.0):
    """全部の字幕を並べたあと（v9）：始まりは動かさない（声の間で決めた時刻のまま）。
    2 秒に足りない・1 秒 CPS 字をこえる 1 枚だけ、終わりを次の 1 枚の始まりまで（声のない所へ）のばす"""
    L = [list(x) for x in sorted(L)]
    for i, x in enumerate(L):
        need = max(MIN, max(1, _vlen(x[2])) / CPS + 0.02)
        lim = L[i + 1][0] if i + 1 < len(L) else x[1] + 1.0
        if x[1] - x[0] < need: x[1] = max(x[1], min(lim, x[0] + need))
    return [tuple(x) for x in L]
