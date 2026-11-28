# 文の頭の音がにごっていないかを数える（SKILL §2.6 の 17本目 v2：「どころが」と言われた。聞き取りの AI は「ところが」と書くので見つからない）
#   カ行・サ行・タ行・ハ行（とパ行）で始まる文だけ。声の頭（-40 dB をこえた所）から 0.02 秒の、低い音（80〜500 Hz）と高い音（2500 Hz〜）の割合を出す。
#   割合が 1.0 をこえる文は、にごって聞こえるおそれがあるので、作り直す候補（決まり）
# MARU_WORK=<作業フォルダ> python3 head_voicing.py [しきい=1.0]
import os, sys, json, wave
import numpy as np
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
L = json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
UNV = set("かきくけこさしすせそたちつてとはひふへほぱぴぷぺぽカキクケコサシスセソタチツテトハヒフヘホパピプペポ")
import pykakasi
kk = pykakasi.kakasi()
out = []
for e in L:
    h = "".join(x["hira"] for x in kk.convert(e["tts"].lstrip("…「")))
    if not h or h[0] not in UNV: continue
    p = D + "/line_%03d.wav" % e["no"]
    w = wave.open(p); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; w.close()
    fr = int(0.005 * sr); n = len(x) // fr
    db = 20 * np.log10(np.sqrt((x[:n * fr].reshape(n, fr) ** 2).mean(1)) + 1e-9)
    on = next((k for k in range(n) if db[k] > -40), 0) * fr
    seg = x[on:on + int(0.02 * sr)] * np.hanning(int(0.02 * sr))[:len(x[on:on + int(0.02 * sr)])]
    sp = np.abs(np.fft.rfft(seg, 4096)) ** 2; fq = np.fft.rfftfreq(4096, 1 / sr)
    lo = sp[(fq >= 80) & (fq < 500)].sum(); hi = sp[fq >= 2500].sum() + 1e-12
    r = lo / hi
    out.append((round(r, 2), e["no"], e["id"], h[:6]))
bad = [o for o in out if o[0] > TH]
print("調べた文", len(out), "割合が %.1f をこえた文" % TH, len(bad))
for o in sorted(bad, reverse=True): print(o)
