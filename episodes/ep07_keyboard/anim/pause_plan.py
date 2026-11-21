# 2 秒に足りない字幕のために、声に足す間を決める（7本目 v9。ユーザー「声のあとに間を足す」）
#   MARU_WORK=<作業> python3 pause_plan.py   → 足す間の一覧（文の途中：声のファイルの中へ／文の終わり：次の文の前へ）を出す
#   文の途中は voice/add_pause.py の引数、文の終わりは voice/make_timing.py の PLUS に足す秒
import os, sys, json, wave
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "..", "..", "..", "skill", "marurobo-video-production", "scripts")); sys.path.insert(0, H)
import subs_jp as SJ, subs_one as SO
P = json.load(open(os.path.join(H, "..", "voice", "placement.json"), encoding="utf-8"))
I = {x["no"]: x["id"] for x in json.load(open(os.path.join(H, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
mid, end = [], {}
for i, p in enumerate(P):
    nx = P[i + 1]["start"] - 0.05 if i + 1 < len(P) else p["end"] + 2
    wav = os.path.join(SJ.VOICE, "line_%03d.wav" % p["no"])
    ev = SO.events(p["start"], p["end"], p["text"], wav, SJ, speed=p.get("speed", 1.0), c_max=nx)
    for k, (a, b, t) in enumerate(ev):
        n = len(t.replace(" ", "")); need = max(SO.MIN, n / 8.0 + 0.02) - (b - a)
        if need <= 0.005: continue
        add = round(need + 0.05, 2)
        if k + 1 < len(ev):
            # 次の字幕の声が出る少し前（字幕の切り替わり＋0.02 秒）。そこがいちばん静かな所になるよう、前後 0.1 秒で探す
            with wave.open(wav) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            at = ev[k + 1][0] - p["start"] + 0.02
            best = min((abs(np.sqrt((x[int((at + d - 0.01) * sr):int((at + d + 0.01) * sr)] ** 2).mean())), at + d) for d in np.arange(-0.1, 0.06, 0.01))
            db = 20 * np.log10(best[0] + 1e-9)
            mid.append((p["no"], round(float(best[1]), 2), add, round(float(db), 1), t))
        elif i + 1 < len(P):
            end[I[P[i + 1]["no"]]] = round(end.get(I[P[i + 1]["no"]], 0) + add, 2)
            print("文の終わり：", I[p["no"]], t, "→ 次の文", I[P[i + 1]["no"]], "の前に", add, "秒")
for m in mid: print("文の途中：", m[0], I[m[0]], m[4], "→", m[1], "秒の所（%s dB）に" % m[3], m[2], "秒")
print("ADD_PAUSE", " ".join("%d %s %s" % (m[0], m[1], m[2]) for m in mid))
print("PLUS", json.dumps(end, ensure_ascii=False))
