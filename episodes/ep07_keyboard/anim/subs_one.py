# 7本目：字幕を 1 行ずつにする（2026-11-16 ユーザー「メインのテロップを1行目と2行目で別にして」「ところがはテロップ別にして」）
#   ① 文の中の「。」「？」「！」で必ず分ける（「なるほど、と思いますよね。」「ところが……。」は別の字幕）
#   ② それぞれを subs_jp の区切り（読点・「……」）で 2 行ぶんに分け、その 2 行も別の字幕にする（1 回に 1 行だけ）
#   ③ 切り替える時刻（v8 で作り直し。2026-11-20 ユーザー「テロップの切り替わりがすごい早い」25 件）：
#      読みがなの長さの割合から「その行を読み始める時刻」を出し、その前後 0.35 秒の中にある声の切れ目にだけ合わせる。
#      v7 までは「字数の割合にいちばん近い切れ目」を、どれだけ離れていても使っていた。0.1 秒より短い切れ目を候補から外していたので、
#      読点の長い切れ目ばかり選ばれ、1 行目が 1.2 秒で消えて 2 行目が声より先に出ていた。
#   ④ 1 枚は MIN（2.0 秒）以上。短い 1 枚は、となりとまとめても 1 行（LINE_MAX 字）に入るならまとめる
#   ⑤ 分け方を決めた文（PIECES）は、そのとおりに分ける（ユーザーの指定）
import re

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


def events(a, c, t, wav, SJ, speed=1.0, MIN=MIN, c_max=None, log=None):
    """文 t（声 a〜c 秒）の 1 行ずつの字幕 [(始め, 終わり, 字), …]。c_max：最後の 1 枚をのばしてよい時刻"""
    c_max = max(c, c_max or c)
    sid = []; ps = pieces(t, SJ, sid)
    try: runs, dur = SJ.gaps(wav, speed)
    except Exception: runs, dur = [], c - a
    if len(ps) == 1: return [(a, max(c, min(c_max, a + MIN)), ps[0])]
    # 声の切れ目（0.05 秒以上。近いものはまとめる）
    mr = []
    for g0, g1 in runs:
        if mr and g0 - mr[-1][1] < 0.15: mr[-1] = (mr[-1][0], g1)
        else: mr.append((g0, g1))
    head = mr[0][1] if mr and mr[0][0] <= 0.02 else 0.0
    tail = mr[-1][0] if mr and mr[-1][1] >= dur - 0.02 else dur
    gaps = [(g0, g1) for g0, g1 in mr if g1 - g0 >= 0.05 and head < g0 and g1 < tail]
    sil_in = lambda x: sum(max(0.0, min(g1, x) - max(g0, head)) for g0, g1 in gaps if g0 < x)
    vtot = (tail - head) - sum(g1 - g0 for g0, g1 in gaps)

    def real(v):           # 声の出ている時間 v → 声のファイルの時刻
        x = head + v
        for g0, g1 in gaps:
            if g0 < x: x += g1 - g0
        return x

    def cut_times(ps):
        wt = [max(1, SJ._ylen(x)) for x in ps]; tot = sum(wt); out = []
        for k in range(len(ps) - 1):
            tg = real(vtot * sum(wt[:k + 1]) / tot)
            near = [(abs(g1 - 0.05 - tg), g0, g1) for g0, g1 in gaps if abs(g0 - tg) <= 0.35 or abs(g1 - tg) <= 0.35 or g0 <= tg <= g1]
            if near:
                _, g0, g1 = min(near); x = max(g0 + 0.03, g1 - 0.08)     # 切れ目の終わり近く（次の行を読み始める少し前）
            else: x = tg
            out.append(a + x)
        return out

    while True:
        ts = [a] + cut_times(ps) + [c]
        if c - ts[-2] < MIN: ts[-1] = min(c_max, ts[-2] + MIN)
        lens = [ts[i + 1] - ts[i] for i in range(len(ps))]
        short = [i for i in range(len(ps)) if lens[i] < MIN - 0.01]
        # まとめても 1 行に入る短い 1 枚があれば、となりとまとめる
        merged = False
        for k in sorted(short, key=lambda i: lens[i]):
            for j in sorted([k - 1, k + 1], key=lambda j: lens[j] if 0 <= j < len(ps) else 99):
                # 別の文（「。」「？」のあと）とはまとめない（v8 で「なるほど、と思いますよね。ところが……。」が 1 枚になった。ユーザー「ところがはテロップ別にして」）
                if 0 <= j < len(ps) and sid[j] == sid[k] and _vlen(ps[min(j, k)] + ps[max(j, k)]) <= LINE_MAX:
                    i0, i1 = min(j, k), max(j, k); ps = ps[:i0] + [ps[i0] + ps[i1]] + ps[i1 + 1:]; sid = sid[:i1] + sid[i1 + 1:]; merged = True; break
            if merged: break
        if not merged:
            # まとめられない短い 1 枚は、次の 1 枚の頭を 0.6 秒まで遅らせて MIN にする（次の 1 枚も MIN 以上残るときだけ）
            for _ in range(2):
                for i in range(len(ps) - 1):
                    li, ln = ts[i + 1] - ts[i], ts[i + 2] - ts[i + 1]
                    if li < MIN - 0.01:
                        d = min(MIN - li, 0.6, max(0.0, ln - MIN), max(0.0, ln - _vlen(ps[i + 1]) / 8.0))   # 次の 1 枚が 1 秒 8 字より速くならない所まで
                        ts[i + 1] += d
            if c_max > ts[-1] and ts[-1] - ts[-2] < MIN: ts[-1] = min(c_max, ts[-2] + MIN)
            lens = [ts[i + 1] - ts[i] for i in range(len(ps))]
            short = [i for i in range(len(ps)) if lens[i] < MIN - 0.01]
            if log is not None:
                for i in short: log.append((round(ts[i], 2), round(lens[i], 2), ps[i]))
            return [(ts[i], ts[i + 1], ps[i]) for i in range(len(ps))]


def balance(L, MIN=MIN, CPS=8.0, BORROW_NEXT=0.35, BORROW_PREV=0.5):
    """全部の字幕を並べたあとで、2 秒に足りない 1 枚を、となりから時間を借りて 2 秒にする（v8）。
    ① うしろへ：次の 1 枚の頭を BORROW_NEXT 秒まで遅らせる（次の 1 枚が MIN 以上・1 秒 CPS 字以下のまま残るときだけ）
    ② まえへ：自分の頭を BORROW_PREV 秒まで早める（前の 1 枚が MIN 以上・CPS 字以下のまま残るときだけ。声より少し先に出る）"""
    L = [list(x) for x in sorted(L)]
    n_ = lambda t: max(1, _vlen(t))
    for _ in range(3):
        for i, x in enumerate(L):
            need = MIN - (x[1] - x[0])
            if need <= 0.005: continue
            if i + 1 < len(L) and abs(L[i + 1][0] - x[1]) < 0.3:
                nx = L[i + 1]
                gap = (L[i + 2][0] - nx[1]) if i + 2 < len(L) else 1.0       # 次の 1 枚のあとの、声のない間（次の 1 枚の終わりをここへのばしてよい）
                ext = max(0.0, min(1.2, gap - 0.05))
                d = min(need, BORROW_NEXT)                                   # 次の 1 枚の頭は 0.35 秒までしか遅らせない（声より遅れすぎない）
                keep = max(MIN, n_(nx[2]) / CPS)                             # 次の 1 枚に残したい長さ
                grow = max(0.0, keep - ((nx[1] - nx[0]) - d))                # そのためにのばす終わり
                if grow > ext: d = max(0.0, d - (grow - ext)); grow = ext
                if d > 0.005:
                    nx[0] += d; nx[1] += grow; x[1] += d; need -= d
            if need > 0.005:                                                 # 自分の頭の前が声のない間なら、そこへ 0.35 秒まで早める
                lim = (L[i - 1][1] + 0.05) if i > 0 else x[0] - 0.35
                d = max(0.0, min(need, 0.35, x[0] - lim))
                if d > 0: x[0] -= d; need -= d
            if need > 0.005 and i > 0 and abs(L[i - 1][1] - x[0]) < 0.06:
                pv = L[i - 1]; room = min(BORROW_PREV, (pv[1] - pv[0]) - MIN, (pv[1] - pv[0]) - n_(pv[2]) / CPS)
                d = max(0.0, min(need, room))
                if d > 0: pv[1] -= d; x[0] -= d; need -= d
        for i, x in enumerate(L):                                            # 速すぎる（1 秒 CPS 字こえ）1 枚は、うしろの声のない間へのばす
            need = n_(x[2]) / CPS - (x[1] - x[0])
            if need > -0.01:
                need += 0.02                                                 # ちょうど 8.0 字/秒は、数え方の丸めで「こえ」になるので少しゆとりを持たせる
                lim = (L[i + 1][0] - 0.05) if i + 1 < len(L) else x[1] + 1.0
                d = max(0.0, min(need, lim - x[1])); x[1] += d; need -= d
            if need > 0.0 and i > 0 and abs(L[i - 1][1] - x[0]) < 0.06:   # まだ速いなら、前の 1 枚（ゆとりがあるとき）から頭を借りる（v8「もっと速く！」8.02 字/秒）
                pv = L[i - 1]; room = min(BORROW_PREV, (pv[1] - pv[0]) - MIN, (pv[1] - pv[0]) - n_(pv[2]) / CPS)
                d = max(0.0, min(need + 0.02, room))
                if d > 0: pv[1] -= d; x[0] -= d
    return [tuple(x) for x in L]

