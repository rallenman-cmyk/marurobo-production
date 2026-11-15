# 1 文ずつに切った声（line_NNN.wav）の前後をきれいにする（ロボットではありません回 v1 のコメント：クリック音・息継ぎが途切れ途切れ）
#   原因：切った文の前後に、息や次の文の頭がほんの少し（0.1 秒たらず）残っていて、無音をはさんで「プツッ」と鳴っていた
#   直し方：声の中心（-38 dB より大きい所の固まり）から 0.12 秒以上離れた、ごく短い（0.06 秒未満）音の切れはしだけを前後から取り除く。
#           （0.15 秒で落とすと「いったい」の「いっ」・「カチッ」・「結果は」の頭まで消えた。書き起こしで確かめること）
#           残した所の前は -50 dB まで（最大 0.08 秒）、後ろは -55 dB まで（最大 0.15 秒）のばし、頭 15ms・終わり 40ms で溶かす
# MARU_WORK=<作業フォルダ> python3 clean_edges.py [番号,…]   （番号なしで全部。lines.json の dur も直す）
import os, sys, json, wave
import numpy as np
D = os.environ["MARU_WORK"] + "/stage/voice/achernar"
V = json.load(open(D + "/lines.json", encoding="utf-8"))
ONLY = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [int(k) for k in V]
FR = 0.01
rep = []
for n in ONLY:
    p = D + "/line_%03d.wav" % n
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    h = int(FR * sr); m = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:m * h].reshape(m, h) ** 2).mean(1)) + 1e-9)
    on = db > -38
    segs = []; i = 0
    while i < m:
        if on[i]:
            j = i
            while j < m and on[j]: j += 1
            segs.append([i, j]); i = j
        else: i += 1
    if not segs: continue
    # 前後のごく短い切れはしを落とす（0.06 秒未満で、次の固まりと 0.12 秒以上離れているもの）
    while len(segs) > 1 and (segs[0][1] - segs[0][0]) * FR < 0.06 and (segs[1][0] - segs[0][1]) * FR >= 0.12: segs.pop(0)
    while len(segs) > 1 and (segs[-1][1] - segs[-1][0]) * FR < 0.06 and (segs[-1][0] - segs[-2][1]) * FR >= 0.12: segs.pop()
    a, b = segs[0][0], segs[-1][1]
    k = 0
    while a > 0 and db[a - 1] > -50 and k < 8: a -= 1; k += 1
    k = 0
    while b < m and db[b] > -55 and k < 15: b += 1; k += 1
    y = x[a * h:b * h].copy()
    fi, fo = int(0.015 * sr), int(0.04 * sr)
    y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo)
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype(np.int16).tobytes())
    old = V[str(n)]["dur"]; V[str(n)]["dur"] = round(len(y) / sr, 3)
    if abs(old - V[str(n)]["dur"]) > 0.05: rep.append((n, old, V[str(n)]["dur"]))
json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("きれいにした文", len(ONLY), "長さが 0.05 秒以上変わった文", len(rep), rep[:20])
