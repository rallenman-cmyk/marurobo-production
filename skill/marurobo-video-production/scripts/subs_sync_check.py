# 字幕の切り替わりが、声の切れ目にあるかを数える（2026-11-21 7本目 ユーザー「なんでテロップのタイミングまだ治ってないの？治ったって言ったよね？」）
#   v8 は「2 秒以上・1 秒 8 字まで」だけを数えて「直った」とした。声とのずれは測っていなかったので、118 か所のうち 44 か所がずれたままだった。
#   python3 subs_sync_check.py <字幕.ass> <placement.json> <声のフォルダ（line_NNN.wav）> [字幕を聞き取った.json]
#   ① Main の字幕の始まりを 1 枚ずつ、その時の文の声のファイルと比べる。
#      文の頭（声の始まりから 0.2 秒以内）か、声の切れ目（声のない間 0.07 秒以上・言葉の切れ目で 6 dB 以上下がる谷）の 0.15 秒以内なら合う。
#      ほかは「声の途中で切り替わる」（字幕が早い・遅い）。
#   ①の続き（2026-11-23、9本目 v3。ユーザー「字幕のずれの治し方を繰り返さないようにルール化して」）：
#      文の頭の字幕は、本当の声の頭（息を除く）から 0.25 秒以内。句読点のあとの字幕は、その句読点に当てはまる声の間（subs_pause_align）の終わりから 0.15 秒以内。
#      句読点のない所で分けた字幕は、そこに 0.1 秒以上の声の間があること（ないなら「続けて読む所で分けた」）。どれも外れたら「ずれ」に数え、関所で止まる。
#   ② 4 つ目に、字幕 1 枚ずつの声を聞き取った結果（各回の anim/sub_hear.py などが作る [{at, score}]）を渡すと、似ている度 0.8 未満の数も書く。
#   <字幕.ass>.sync.json を作る。pre_upload_gate.py は、これがない・ずれが 1 つでもある・字幕が変わったあとの物なら不合格にする。
import os, sys, re, json, wave, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subs_pause_align as PA

ass, plp, vdir = sys.argv[1], sys.argv[2], sys.argv[3]
hearp = sys.argv[4] if len(sys.argv) > 4 else None
TOL, HEAD_TOL = 0.15, 0.2


def subs(ass):
    L = []
    for l in open(ass, encoding="utf-8"):
        if not l.startswith("Dialogue"): continue
        p = l.split(",", 9)
        if p[3] != "Main": continue
        f = lambda x: sum(float(v) * m for v, m in zip(x.split(":"), (3600, 60, 1)))
        L.append((f(p[1]), f(p[2]), re.sub(r"\{.*?\}", "", p[9].strip())))
    return sorted(L)


def cands(wav, speed=1.0):
    """声の切れ目：声が出はじめる時刻（文の声の頭からの秒）"""
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
            if j - i >= 7 and j < n: out.append(j * 0.01 / speed)
            i = j
        else: i += 1
    for k in range(15, n - 15):
        # 谷が無音まで下がっても数える（2026-11-21 v9：0.04〜0.06 秒だけ無音になる言葉の切れ目（「なぞを／確かめて」など 5 か所）が、
        # 「0.07 秒より短いので間でない」「無音なので谷でない」の両方から外れ、ずれと数えていた。聞き取りでは 5 か所とも言葉の切れ目）
        if db[k] == db[k - 5:k + 6].min() and min(db[k - 15:k].max(), db[k + 1:k + 16].max()) - db[k] >= 6:
            out.append((k * 0.01 + 0.03) / speed)
    return sorted(out)


P = json.load(open(plp, encoding="utf-8"))
C = {}
L = subs(ass); bad = []
for a, b, t in L:
    p = None
    for q in P:
        if q["start"] - HEAD_TOL <= a <= q["end"] + 0.05: p = q; break
    if p is None:
        nxt = [q for q in P if q["start"] > a]
        bad.append(dict(at=round(a, 2), text=t, why="声のない所で切り替わる（次の文の %.2f 秒前）" % ((nxt[0]["start"] - a) if nxt else 0))); continue
    on = p["start"] + PA.onset(os.path.join(vdir, "line_%03d.wav" % p["no"]))
    if a - p["start"] <= HEAD_TOL or a - on <= HEAD_TOL:
        # 2026-11-23（9本目 v3 の点検。ユーザー「字幕のずれの治し方を繰り返さないようにルール化して」）：文の頭の字幕は、
        #   文の声のファイルの頭ではなく、本当の声の頭（-40dB をこえる所、PA.onset）と比べる。頭に息があると 0.9 秒早く出ていた（37「出てきました！」）
        d0 = a + 0.05 - on
        if t.replace("\\N", "").startswith("……") and -0.85 <= d0 <= HEAD_TOL: continue     # 「……」でためる字幕は、声の前のためから出してよい
        if abs(d0) > 0.25: bad.append(dict(at=round(a, 2), text=t, why="文の声の頭とずれる（%+.2f 秒。声の頭は %.2f）" % (d0, on)))
        continue
    # 2026-11-23（9本目 v2「テロップの切り替わりが早い／遅い」11 件）：句読点のあとで替わる字幕は、その句読点に当てはまる声の本当の間
    # （subs_pause_align.py）の終わりと比べる。いちばん近い小さな谷に合っても、言葉の途中なら合格にしない
    tg = PA.target(p, t, os.path.join(vdir, "line_%03d.wav" % p["no"]))
    if tg is not None:
        if abs(a - tg) > TOL: bad.append(dict(at=round(a, 2), text=t, why="句読点のあとの声の間とずれる（%+.2f 秒。替えるのは %.2f）" % (a - tg, tg)))
        continue
    # 2026-11-23（同上）：句読点のない所で分けた字幕は、そこに声の間（0.1 秒以上の無音）がなければ「続けて読む所で分けた」（2 行の 1 枚にまとめる）
    #   言葉の中の小さな谷（「っ」の無音など）に合っても合格にしない（9本目 v3：「先へ進むように｜作られている」は 0.04 秒の無音だけだった）
    sil, _ = PA.silences(os.path.join(vdir, "line_%03d.wav" % p["no"]), p.get("speed", 1.0))
    if not any(e_ - s_ >= 0.10 and p["start"] + s_ - TOL <= a + 0.05 <= p["start"] + e_ + TOL for s_, e_ in sil):
        bad.append(dict(at=round(a, 2), text=t, why="句読点も声の間もない所で分けている（続けて読む所。前と 2 行の 1 枚にまとめる）")); continue
    if p["no"] not in C: C[p["no"]] = cands(os.path.join(vdir, "line_%03d.wav" % p["no"]), p.get("speed", 1.0))
    tv = a + 0.05 - p["start"]                    # 字幕は声が出る 0.05 秒前に出す
    d = min([abs(tv - c) for c in C[p["no"]]] or [9.0])
    if d > TOL: bad.append(dict(at=round(a, 2), text=t, why="声の途中で切り替わる（いちばん近い切れ目まで %.2f 秒）" % d))
hb = None
if hearp:
    H = json.load(open(hearp, encoding="utf-8"))
    hb = [h for h in H if h.get("score") is not None and h["score"] < 0.8]
sha = hashlib.sha256(open(ass, "rb").read()).hexdigest()
res = dict(ass_sha256=sha, subs=len(L), outside=len(bad), bad=bad, heard=(len(H) if hearp else None), heard_bad=(len(hb) if hb is not None else None),
           heard_bad_list=[dict(at=h["at"], text=h["text"], score=round(h["score"], 2)) for h in (hb or [])])
json.dump(res, open(ass + ".sync.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("字幕 %d 枚。声の途中で切り替わる：%d 枚" % (len(L), len(bad)) + ("。聞き取りで読みと合わない：%d 枚（%d 枚を聞いた）" % (len(hb), len(H)) if hearp else "。聞き取り：なし"))
for x in bad: print("  %7.2f  %s  %s" % (x["at"], x["why"], x["text"]))
for h in (hb or []): print("  %7.2f  聞き取りが読みと合わない（%.2f）  %s" % (h["at"], h["score"], h["text"]))
print("→", ass + ".sync.json")
