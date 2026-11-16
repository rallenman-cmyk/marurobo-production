# 文ごとの声の大きさをそろえる（6本目 v1：06-01・30-01・30-02「声大きい」）
#   声の出ている所（-40 dB より大きい 20ms の固まり）だけの大きさ（RMS）をはかり、全部の文の中央値にそろえる。
#   中央値から ±1.0 dB 以内の文はさわらない。前の声は line_NNN_before_level.wav に残す（2 回目からは上書きしない）
# MARU_WORK=<作業フォルダ> python3 level_lines.py [--dry]
import os, sys, json, wave, shutil
import numpy as np
D = os.environ["MARU_WORK"] + "/stage/voice/achernar"
V = json.load(open(D + "/lines.json", encoding="utf-8"))
DRY = "--dry" in sys.argv


def rd(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, w.getframerate(), w.getparams()


def level(x, sr):
    h = int(0.02 * sr); n = len(x) // h
    e = np.sqrt(np.mean(x[:n * h].reshape(n, h) ** 2, 1))
    on = e[e > 10 ** (-40 / 20)]
    return 20 * np.log10(np.sqrt(np.mean(on ** 2)) + 1e-9) if len(on) else -99.0


# 前に一度そろえた文は、残してある元の声（_before_level）からはかる（何回使っても大きさが重ならないように。6本目 v3 で 2 回目に +2 dB ずつ重なった）
src = lambda n: D + "/line_%03d_before_level.wav" % n if os.path.exists(D + "/line_%03d_before_level.wav" % n) else D + "/line_%03d.wav" % n
lv = {}
for k in V:
    x, sr, _ = rd(src(int(k))); lv[int(k)] = level(x, sr)
med = float(np.median(list(lv.values())))
print("中央値 %.1f dB" % med)
for n, v in sorted(lv.items()):
    g = min(med - v, 2.0)   # 小さい文は上げすぎない（ささやく文はわざと小さい。例 27-04「すりすり」）
    if abs(g) <= 1.0:
        if os.path.exists(D + "/line_%03d_before_level.wav" % n) and not DRY: shutil.copy(D + "/line_%03d_before_level.wav" % n, D + "/line_%03d.wav" % n)   # 中央値が動いて、そろえなくてよくなった文は元に戻す
        continue
    print("line_%03d  %.1f dB → %+.1f dB" % (n, v, g))
    if DRY: continue
    p = D + "/line_%03d.wav" % n; b = D + "/line_%03d_before_level.wav" % n
    if not os.path.exists(b): shutil.copy(p, b)
    x, sr, prm = rd(b); y = np.clip(x * 10 ** (g / 20), -1, 1)
    with wave.open(p, "wb") as w:
        w.setparams(prm); w.writeframes((y * 32767).astype(np.int16).tobytes())
