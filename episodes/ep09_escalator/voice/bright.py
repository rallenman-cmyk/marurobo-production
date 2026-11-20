# 声が張って（明るく強く）聞こえる文を探す（7本目 v5「声大きい」）。音の重心（Hz）がまわりより高い文を出す
# python3 bright.py <声のフォルダ> [しきい Hz=1850]
import sys, glob, wave, numpy as np
D = sys.argv[1]; TH = float(sys.argv[2]) if len(sys.argv) > 2 else 1850
def feat(p):
    x = np.frombuffer(wave.open(p).readframes(10 ** 8), np.int16).astype(np.float32) / 32768
    v = x[np.abs(x) > 0.01]; x = x / np.sqrt((v ** 2).mean())
    n = 1024; fr = [x[i:i + n] for i in range(0, len(x) - n, n)]
    S = np.array([np.abs(np.fft.rfft(f * np.hanning(n))) for f in fr if np.sqrt((f ** 2).mean()) > 0.3])
    fq = np.fft.rfftfreq(n, 1 / 24000)
    return float(np.median((S * fq).sum(1) / S.sum(1)))
R = {int(p.split("_")[-1][:3]): feat(p) for p in sorted(glob.glob(D + "/line_[0-9][0-9][0-9].wav"))}
print("中央 %.0f Hz" % np.median(list(R.values())))
for k, c in sorted(R.items()):
    if c > TH: print(k, "%.0f Hz" % c)
