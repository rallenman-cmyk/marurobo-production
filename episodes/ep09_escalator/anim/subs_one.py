# 7本目 v6：字幕を 1 行ずつにする（2026-11-16 ユーザー「メインのテロップを1行目と2行目で別にして」「ところがはテロップ別にして」「テロップのきりかわりはやい」）
#   ① 文の中の「。」「？」「！」で必ず分ける（「なるほど、と思いますよね。」「ところが……。」は別の字幕）
#   ② それぞれを subs_jp の区切り（読点・「……」）で 2 行ぶんに分け、その 2 行も別の字幕にする（1 回に 1 行だけ）
#   ③ 切り替える時刻は、声の間（無音）のうち、字数の割合にいちばん近い所。1 枚は 1.2 秒以上（短いときは、となりとまとめて 1 行に）
import re, itertools


def pieces(t, SJ):
    out = []
    for sen in [x for x in re.split(r'(?<=[。？！])(?=[^」』）])', t) if x.strip()]:
        for card in SJ.plan_tame(sen):
            out += [x for x in card.split("\\N") if x]
    return out


def events(a, c, t, wav, SJ, speed=1.0, MIN=1.2, c_max=None):
    """c_max：最後の 1 枚を、次の文の前までのばしてよい時刻（短い「ところが……」などを 1 枚にするため）"""
    c_max = max(c, c_max or c)
    ps = pieces(t, SJ)
    try: runs, dur = SJ.gaps(wav, speed)
    except Exception: runs, dur = [], c - a
    while True:
        if len(ps) == 1: return [(a, c, ps[0])]
        mr = []
        for g0, g1 in runs:
            if mr and g0 - mr[-1][1] < 0.15: mr[-1] = (mr[-1][0], g1)
            else: mr.append((g0, g1))
        cand = [(g0, g1) for g0, g1 in mr if g1 - g0 >= 0.1 and 0.3 <= g0 and g1 <= dur - 0.2]
        sil_before = lambda x: sum(min(g1, x) - g0 for g0, g1 in mr if g0 < x)
        vtot = dur - sil_before(dur)
        wt = [max(1, SJ._ylen(x)) for x in ps]; tot = sum(wt)
        tgt = [vtot * sum(wt[:k + 1]) / tot for k in range(len(ps) - 1)]
        cuts = None
        if len(cand) >= len(ps) - 1:
            best = None
            for combo in itertools.combinations(cand, len(ps) - 1):
                cost = sum(abs((g0 - sil_before(g0)) - tg) for (g0, g1), tg in zip(combo, tgt)) - 0.15 * sum(min(g1 - g0, 1.0) for g0, g1 in combo)
                if best is None or cost < best[0]: best = (cost, combo)
            cuts = [a + max(g0 + 0.05, g1 - 0.15) for g0, g1 in best[1]]
        else:
            cuts = [a + (c - a) * sum(wt[:k + 1]) / tot for k in range(len(ps) - 1)]
        ts = [a] + cuts + [c]
        if ts[-1] - ts[-2] < MIN: ts[-1] = min(c_max, ts[-2] + MIN)
        # 短い 1 枚があれば、切り替わりを前後に少しずらして、どれも MIN 以上にする（声の間から 0.6 秒まで）
        for _ in range(3):
            for i in range(1, len(ts) - 1):
                if ts[i] - ts[i - 1] < MIN: ts[i] = min(ts[i - 1] + MIN, ts[i] + 0.6)
                if ts[i + 1] - ts[i] < MIN: ts[i] = max(ts[i + 1] - MIN, ts[i] - 0.6)
        lens = [ts[i + 1] - ts[i] for i in range(len(ps))]
        k = min(range(len(ps)), key=lambda i: lens[i])
        if lens[k] >= MIN - 0.01: return [(ts[i], ts[i + 1], ps[i]) for i in range(len(ps))]
        # いちばん短い 1 枚を、となりの短い方とまとめる（1 行のまま）
        j = k + 1 if k == 0 else (k - 1 if k == len(ps) - 1 else (k - 1 if lens[k - 1] < lens[k + 1] else k + 1))
        i0, i1 = min(j, k), max(j, k)
        ps = ps[:i0] + [ps[i0] + ps[i1]] + ps[i1 + 1:]
