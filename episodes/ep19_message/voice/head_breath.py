# 文の頭の、息を吸う音を探して切る（7本目 v6：通しを聞かせて「ナレーション前の吸気音」が何か所も出た）
# python3 head_breath.py <声のフォルダ> [cut]
#   声の頭の前に、-46〜-24 dB の音が 0.06 秒以上続き、その音の重心が 3000 Hz より低い（「し」「す」の息は高い）所を息とみなす
import sys, glob, wave, shutil, json, os
import numpy as np
D = sys.argv[1]; CUT = len(sys.argv) > 2 and sys.argv[2] == "cut"
SR = 24000; N = 240
out = []
for p in sorted(glob.glob(D + "/line_[0-9][0-9][0-9].wav")):
    x = np.frombuffer(wave.open(p).readframes(10 ** 8), np.int16).astype(np.float32) / 32768
    m = len(x) // N; d = 20 * np.log10(np.sqrt((x[:m * N].reshape(m, N) ** 2).mean(1)) + 1e-9)
    v = np.where(d > -20)[0]
    if not len(v): continue
    on = v[0]
    k = on - 1
    while k >= 0 and d[k] > -46: k -= 1
    st = k + 1; L = on - st
    if L < 6: continue
    seg = x[st * N:on * N]
    f = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fq = np.fft.rfftfreq(len(seg), 1 / SR)
    cen = (f * fq).sum() / f.sum()
    if cen > 3000: continue
    # 息と声の間に、はっきり小さくなる所（-30 dB 以下）があるか：あれば息は声と別
    gap = (d[st:on] < -30).any()
    no = int(os.path.basename(p)[5:8])
    out.append((no, round(st * 0.01, 2), round(L * 0.01, 2), int(cen), bool(gap)))
    if CUT:
        bk = p.replace(".wav", "_before_headbreath.wav")
        if not os.path.exists(bk): shutil.copy(p, bk)
        cut = max(0, on * N - int(0.03 * SR))
        y = x[cut:].copy(); fi = int(0.012 * SR); y[:fi] *= np.linspace(0, 1, fi) ** 2
        with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
for o in out: print("文 %d：頭 %.2f 秒から %.2f 秒の息（重心 %d Hz）" % o[:4])
print(len(out), "文")
