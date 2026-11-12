# 台本 v2 の時刻つき字幕（声を録るまでの仮の時刻）。script_v2.json と、元の字幕（直し1）の時刻から作る
#   ・変えていない文：元の長さと、前の文との間をそのまま保つ（後ろへずれる分だけずらす）
#   ・変えた文：元の枠（まとめた文があれば、その分も含む）に収まれば元の枠のまま。長くなった分だけ後ろをずらす
#   ・足した文：前の文の 0.25 秒あと。字数 ÷ 5.3字/秒（元の声の速さ）
#   ・ペアリング（元の 51〜55 の枠）：17文を、動きを見せる間（PAUSE）を入れて並べ直す
#   使い方: python3 make_srt_v2.py [PAUSE の上書き json]
import json, re, sys
CPS = 5.3
def dur(s): return max(1.0, len(s) / CPS)
def sec(x):
    hh, mm, rr = x.strip().split(":"); s_, ms = rr.split(","); return int(hh) * 3600 + int(mm) * 60 + int(s_) + int(ms) / 1000
def stamp(x):
    ms = int(round(x * 1000)); return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
O = {}
for i, b in enumerate(open("bluetooth_full_native_rev1.srt", encoding="utf-8").read().strip().split("\n\n")):
    x = b.split("\n"); a, c = x[1].split(" --> "); O[i + 1] = (sec(a), sec(c), " ".join(x[2:]))
ABSORB = {11: 12, 166: 168}
FIT = {11}                                     # 第1・2章（OK済み）の時刻を変えない                    # 変えた文が、元のどこまでの枠を使うか（まとめた文）
P_FIRST, P_LAST = 51, 55                       # 元のペアリングの枠
PAUSE = {1: 0.3, 2: 1.0, 3: 0.5, 4: 0.5, 5: 0.5, 6: 0.5, 7: 1.5, 8: 1.6, 9: 2.2, 10: 0.3, 11: 7.0, 12: 2.6, 13: 1.0, 14: 0.5, 15: 1.6, 16: 1.6, 17: 0.3}
if len(sys.argv) > 1: PAUSE.update({int(k): v for k, v in json.load(open(sys.argv[1])).items()})
GAP = 0.30
V2 = json.load(open("script_v2.json", encoding="utf-8"))
out = []; delta = 0.0; prev_end = 0.0; pk = 0; p_start = None
for e in V2:
    k = e["kind"]; s_txt = e["text"]
    if k == "pairing":
        pk += 1
        if pk == 1: p_start = O[P_FIRST][0] + delta; st = p_start
        else: st = prev_end + GAP + PAUSE.get(pk - 1, 0.0)
        en = st + dur(s_txt); out.append((st, en, s_txt, e["no"], "P%d" % pk)); prev_end = en
        if pk == 17:
            block_end_old = O[P_LAST][1] + delta; delta += (en + PAUSE[17]) - block_end_old; prev_end = en
        continue
    if k == "keep":
        a, c, _ = O[e["old_no"]]; st, en = a + delta, c + delta
    elif k == "change":
        a = O[e["old_no"]][0]; c = O[ABSORB.get(e["old_no"], e["old_no"])][1]; need = dur(s_txt)
        st = a + delta
        if need <= c - a or e["old_no"] in FIT: en = c + delta           # FIT：OK済みの章の文は元の枠に収める（声を少し速く）
        else: en = st + need; delta += need - (c - a)
    else:                                                    # add
        st = prev_end + 0.25; en = st + dur(s_txt); delta += 0.25 + dur(s_txt)
    out.append((st, en, s_txt, e["no"], k)); prev_end = en
open("bluetooth_full_native_rev2.srt", "w", encoding="utf-8").write("\n\n".join("%d\n%s --> %s\n%s" % (i + 1, stamp(a), stamp(c), t) for i, (a, c, t, _, _) in enumerate(out)) + "\n")
json.dump([dict(no=n, start=round(a, 3), end=round(c, 3), text=t, tag=g) for a, c, t, n, g in out], open("script_v2_timed.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("lines", len(out), "end %.1f s (%d:%04.1f)  shift at end %+.1f s" % (out[-1][1], int(out[-1][1] // 60), out[-1][1] % 60, delta))
for a, c, t, n, g in out:
    if g.startswith("P") or n in (11, 33, 34, 35, 38, 51, 69, 70, 71): print("%3d %-6s %7.2f-%7.2f %s" % (n, g, a, c, t))
