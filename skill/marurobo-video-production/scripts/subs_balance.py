# 字幕の長さをならす（7本目 subs_one.py の balance を、どの回でも使えるように写したもの。2026-11-20）
#   2 秒に足りない 1 枚を、となりの字幕・声のない間から時間を借りて 2 秒にする。1 秒 8 字をこえる 1 枚は、うしろの声のない間へのばす
#   字は 2 行（\\N か改行で分けた物）でもよい。字数は行の分け目を数えない
MIN = 2.0


def _vlen(p):
    return len(p.replace(" ", "").replace("\\N", "").replace("\n", ""))


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
            if need > 0.005 and (i + 1 == len(L) or L[i + 1][0] - x[1] > 0.06):   # 6本目 v10：うしろが声のない間なら、次の字幕の 0.05 秒前までのばす（「ころん。」「ぴたっ。」）
                lim = (L[i + 1][0] - 0.05) if i + 1 < len(L) else x[1] + 1.0
                d = max(0.0, min(need, lim - x[1]))
                if d > 0: x[1] += d; need -= d
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
            if need > 0.005:
                lim = (L[i + 1][0] - 0.05) if i + 1 < len(L) else x[1] + 1.0
                x[1] += max(0.0, min(need, lim - x[1]))
    return [tuple(x) for x in L]

