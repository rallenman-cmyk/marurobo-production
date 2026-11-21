# 9本目 v2 の点検：字幕の切り替わりを、声の切れ目に合わせる（関所 subs_sync_check.py で「声の途中で切り替わる」が 10 枚あった）
#   7本目の決まり（SKILL §7「字幕の切り替わりは、声の切れ目で」）：時刻をずらして長さを合わせない。2 秒に足りない 1 枚は、となりとまとめる。
#   balance（となりから時間を借りる）のあとに通す：
#     ① 切り替わりが文の声の途中なら、いちばん近い声の切れ目（subs_sync_check.py と同じ見つけ方）へ動かす。
#     ② 声のない所（文と文の間）で切り替わるなら、次の文の声の頭（0.05 秒前）へ動かす。
#     ③ 動かして 2 秒に足りない・1 秒 8 字をこえる 1 枚は、となりと 2 行の 1 枚にまとめる（1 行 25 字まで）。
#        短い 1 枚（ぺたっ。など）は、声より先に出さないよう、うしろの 1 枚とまとめる。
import os, sys, json, wave
import numpy as np

HEAD_TOL, TOL = 0.2, 0.15


def cands(wav, speed=1.0):
    """声の切れ目（文の声の頭からの秒）。scripts/subs_sync_check.py の cands と同じ"""
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
        if db[k] == db[k - 5:k + 6].min() and min(db[k - 15:k].max(), db[k + 1:k + 16].max()) - db[k] >= 6:
            out.append((k * 0.01 + 0.03) / speed)
    return sorted(out)


def _w(t): return len(t.replace("\\N", "").replace("\n", ""))


def _ok(a, c, t, MIN, CPS):
    return c - a >= MIN and _w(t) / max(1e-6, c - a) <= CPS and all(len(r) <= 25 for r in t.split("\\N")) and t.count("\\N") <= 1


def fix(SUBS, P, vdir, MIN=2.02, CPS=7.9, log=print):
    C = {}
    S = [list(x) for x in sorted(SUBS)]
    for _ in range(6):
        changed = False
        i = 1
        while i < len(S):
            a = S[i][0]
            p = next((q for q in P if q["start"] - HEAD_TOL <= a <= q["end"] + 0.05), None)
            if p is None:                                           # ② 声のない所
                nxt = [q for q in P if q["start"] > a]
                if not nxt: i += 1; continue
                na = round(nxt[0]["start"] - 0.05, 3)
            elif a - p["start"] <= HEAD_TOL: i += 1; continue
            else:                                                   # ① 声の途中
                if p["no"] not in C: C[p["no"]] = cands(os.path.join(vdir, "line_%03d.wav" % p["no"]), p.get("speed", 1.0))
                tv = a + 0.05 - p["start"]
                cs = C[p["no"]]
                if not cs: i += 1; continue
                c = min(cs, key=lambda c_: abs(tv - c_))
                if abs(tv - c) <= TOL: i += 1; continue
                na = round(p["start"] + c - 0.05, 3)
            old = (S[i - 1][1], S[i][0])
            if abs(S[i - 1][1] - a) < 0.06: S[i - 1][1] = na      # となりとつながっていたら、前の終わりもいっしょに動かす
            elif S[i - 1][1] > na: S[i - 1][1] = na
            S[i][0] = na
            log("SYNC 動かした %7.2f → %7.2f  %s" % (a, na, S[i][2]))
            changed = True
            # ③ 決まりに合わなくなったら、まとめる
            for j in (i, i - 1):
                if j < 0 or j >= len(S) or _ok(*S[j], MIN, CPS): continue
                def line_of(t_):
                    return next((q["no"] for q in P if q["start"] - HEAD_TOL <= t_ <= q["end"] + 0.05), None)
                opts = []
                if j + 1 < len(S) and S[j + 1][0] - S[j][1] < 0.7 and _ok(S[j][0], S[j + 1][1], S[j][2] + "\\N" + S[j + 1][2], MIN, CPS):
                    opts.append((0 if line_of(S[j][0] + 0.1) == line_of(S[j + 1][0] + 0.1) else 1, 1, j + 1))
                if j > 0 and _w(S[j][2]) > 6 and S[j][0] - S[j - 1][1] < 0.7 and _ok(S[j - 1][0], S[j][1], S[j - 1][2] + "\\N" + S[j][2], MIN, CPS):
                    opts.append((0 if line_of(S[j][0] + 0.1) == line_of(S[j - 1][0] + 0.1) else 1, 0, j - 1))
                k = min(opts)[2] if opts else None     # 同じ文の中のとなりを先に（話の変わる所をまたいでまとめない）
                if k is None:
                    log("SYNC まとめられない %7.2f %s" % (S[j][0], S[j][2])); continue
                lo, hi = min(j, k), max(j, k)
                S[lo] = [S[lo][0], S[hi][1], S[lo][2] + "\\N" + S[hi][2]]; del S[hi]
                log("SYNC まとめた %7.2f  %s" % (S[lo][0], S[lo][2]))
                break
            i += 1
        if not changed: break
    # 聞き取りで、となりの言葉が入っていた 1 枚（subs_merge.json）は、次の 1 枚と 2 行の 1 枚にまとめる
    mp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subs_merge.json")
    for tx in (json.load(open(mp, encoding="utf-8")).get("merge_next", []) if os.path.exists(mp) else []):
        k = next((i for i, x in enumerate(S) if x[2] == tx), None)
        if k is None or k + 1 >= len(S): log("SYNC まとめる字幕が見つからない %s" % tx); continue
        if _ok(S[k][0], S[k + 1][1], S[k][2] + "\\N" + S[k + 1][2], MIN, CPS):
            S[k] = [S[k][0], S[k + 1][1], S[k][2] + "\\N" + S[k + 1][2]]; del S[k + 1]; log("SYNC 聞き取りでまとめた %7.2f %s" % (S[k][0], S[k][2]))
        else: log("SYNC 聞き取りでまとめられない %s" % tx)
    return [tuple(x) for x in S]


if __name__ == "__main__":
    # 試し：python3 subs_sync.py subs_events.json placement.json 声のフォルダ
    SUBS = [tuple(x) for x in json.load(open(sys.argv[1], encoding="utf-8"))]
    P = json.load(open(sys.argv[2], encoding="utf-8"))
    out = fix(SUBS, P, sys.argv[3])
    print(len(SUBS), "→", len(out))
