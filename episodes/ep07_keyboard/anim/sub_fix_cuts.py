# 聞き取りで、字幕の切り替わりを正しい声の切れ目に直す（7本目 v9）
#   sub_hear.py で「読みと合わない」と出た字幕の、前後の切り替わりを、声の切れ目の候補（前後 1.2 秒）から選び直す。
#   候補は声が止まる間（0.07 秒以上）だけ。それぞれの候補で、左の字幕と右の字幕の声を聞き取り、読みとの似ている度の合計がいちばん高い所にする。
#   結果は voice/sub_cuts.json（文 → [[声の頭からの秒, 字幕の字], …]）に書き、subs_one.events はその文をそのとおりに切る。
#   MARU_WORK=<作業> python3 sub_fix_cuts.py <sub_hear の結果.json>
import os, sys, json, wave, difflib, re, base64, io, urllib.request, time
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "..", "..", "..", "skill", "marurobo-video-production", "scripts")); sys.path.insert(0, H)
import subs_jp as SJ, subs_one as SO
src = open(os.path.join(H, "sub_hear.py"), encoding="utf-8").read()
exec(src[src.index("KEY = "):src.index("jobs = []")])          # hear・norm などを借りる
YC = json.load(open(os.path.join(os.environ["MARU_WORK"], "sub_yomi_cache.json"), encoding="utf-8"))
R = json.load(open(sys.argv[1], encoding="utf-8"))
P = json.load(open(os.path.join(H, "..", "voice", "placement.json"), encoding="utf-8"))
CP = os.path.join(H, "..", "voice", "sub_cuts.json")
CUTS = json.load(open(CP, encoding="utf-8")) if os.path.exists(CP) else {}
badno = sorted({r["no"] for r in R if r["score"] is not None and r["score"] < 0.8})
sim = lambda ref, h: difflib.SequenceMatcher(None, norm(ref), norm(h)).ratio()
for no in badno:
    p = [q for q in P if q["no"] == no][0]; i = P.index(p)
    nx = P[i + 1]["start"] - 0.05 if i + 1 < len(P) else p["end"] + 2
    wav = os.path.join(SJ.VOICE, "line_%03d.wav" % no)
    ev = SO.events(p["start"], p["end"], p["text"], wav, SJ, speed=p.get("speed", 1.0), c_max=nx)
    with wave.open(wav) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    C, head, tail, gaps = SO._cands(wav, 1.0, SJ)
    offs = [e[0] - p["start"] for e in ev] + [len(x) / sr]
    texts = [e[2] for e in ev]
    ref = [YC.get(tx + "|" + str(no)) for tx in texts]
    if any(r_ is None for r_ in ref): print(no, "読みがない（sub_hear.py を先に）"); continue
    bads = [k for k, tx in enumerate(texts) if any(r["no"] == no and r["text"] == tx and r["score"] is not None and r["score"] < 0.8 for r in R)]
    for k in sorted({b for k in bads for b in (k, k + 1) if 1 <= b < len(texts)}):   # 直す切り替わり（k 番目の字幕の頭）
        cur = offs[k]; lo, hi = offs[k - 1] + 0.3, offs[k + 1] - 0.3
        cand = sorted({round(cur, 2)} | {round(tc - 0.05, 2) for tc, st in C if st >= 3.0 and abs(tc - 0.05 - cur) <= 2.0 and lo < tc - 0.05 < hi})   # 候補は声が止まる間だけ（言葉の途中の谷では、聞き取りがゆれて「せんせい／せいが」のように選んだ）
        best = None
        for cc in cand:
            L_ = hear(x[int(offs[k - 1] * sr):int(cc * sr)], sr); R_ = hear(x[int(cc * sr):int(offs[k + 1] * sr)], sr)
            sc = sim(ref[k - 1], L_) + sim(ref[k], R_)
            print("  %d 切り替わり %d：%.2f 秒 → 似ている度 %.2f（%s ／ %s）" % (no, k, cc, sc, L_, R_), flush=True)
            if best is None or sc > best[0] + 0.02: best = (sc, cc)
        offs[k] = best[1]
        print(no, texts[k], "：", round(cur, 2), "→", best[1], "秒", flush=True)
    CUTS[p["text"]] = [[round(offs[k], 3), texts[k]] for k in range(len(texts))]
json.dump(CUTS, open(CP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("→", CP, len(CUTS), "文")
