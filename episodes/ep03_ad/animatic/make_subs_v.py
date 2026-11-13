# 会話と広告の回：字幕の時刻を作り直す（QR回 v10→v11 の決まりを横展開、2026-11-13）
#   ・「……」でためた答えは次の字幕に分ける（subs_jp.plan_tame）＝答えを先に見せない
#   ・2 枚以上に分けた文の切り替わりは、声が出ている時間の割合で選ぶ（subs_jp.events_v）
#   ・台本の指示「（間）」は出さない。1.2 秒未満で消える字幕は、次の字幕の前まで延ばす
#   MARU_WORK=<作業フォルダ> python3 make_subs_v.py   → subs_events.json（前の版は subs_events_v1.json）
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ["MARU_WORK"]
os.environ.setdefault("MARU_VOICE", W + "/stage/voice/achernar")
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
import subs_jp as SJ
V = os.environ["MARU_VOICE"]
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
ev = []
for k, p in enumerate(P):
    nxt = P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.0
    end = min(max(p["end"] + 0.35, p["start"] + 1.0), nxt - 0.05)
    wav = os.path.join(V, "line_%03d.wav" % p["no"])
    for a, c, t in SJ.events_v(p["start"], end, p["text"], wav=wav, speed=p.get("speed", 1.0)):
        # events_v で分けきれなかった「……答え」（ためが 3 字以下・声の間が短い）も、ここで必ず次の字幕に分ける
        flat = t.replace("\\N", "")
        k = flat.find("……")
        if 2 <= k and len(flat) - (k + 2) >= 2 and not flat.startswith("……"):
            k2 = k + 2 + (1 if flat[k + 2:k + 3] in "。、" else 0)
            g, d = SJ.gaps(wav, p.get("speed", 1.0))
            tgt = (a - p["start"]) + (c - a) * k2 / len(flat)
            cand = [(g0, g1) for g0, g1 in g if g1 - g0 >= 0.05 and a - p["start"] + 0.4 < g0 < c - p["start"] - 0.4]
            cut = p["start"] + (min(cand, key=lambda x: abs(x[0] - tgt))[1] - 0.08 if cand else tgt)
            ev += [(a, cut, flat[:k2]), (cut, c, flat[k2:])]
        else:
            ev.append((a, c, t))
ev = [(a, c, re.sub(r"（間）|\(間\)", "", t).strip()) for a, c, t in ev]
ev = [e for e in ev if e[2]]
# 1 秒もたない短い字幕（「そう。」など）は、次の字幕の頭につなげる（2 行・25 字に収まるとき）
ev2 = []; k = 0
while k < len(ev):
    a, c, t = ev[k]
    if k + 1 < len(ev) and ev[k + 1][0] - a < 1.0 and len(t.replace("\\N", "")) <= 4:
        a2, c2, t2 = ev[k + 1]; flat = t2.replace("\\N", "")
        if "\\N" not in t2 and len(t) + len(flat) <= 25: ev2.append((a, c2, t + flat)); k += 2; continue
        if "\\N" not in t2: ev2.append((a, c2, t + "\\N" + t2)); k += 2; continue
        ls = t2.split("\\N")
        if len(t) + len(ls[0]) <= 25: ls[0] = t + ls[0]; ev2.append((a, c2, "\\N".join(ls))); k += 2; continue
    ev2.append((a, c, t)); k += 1
ev = ev2
ev = [(a, min(max(c, a + 1.2), ev[k + 1][0] - 0.05) if k + 1 < len(ev) else max(c, a + 1.2), t) for k, (a, c, t) in enumerate(ev)]
json.dump([[round(a, 3), round(c, 3), t] for a, c, t in ev], open(os.path.join(HERE, "subs_events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(ev), "枚")
