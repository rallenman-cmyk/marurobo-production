# 文の終わり・頭の息の音（声が終わったあとの、小さいがはっきりした音）を探す（7本目 v5「というわけですの後に変な呼吸音入ってる」）
# python3 tail_breath.py <声のフォルダ> [cut]   cut を付けると、見つけた息の手前で切る（前のファイルは _before_breath.wav に残す）
import sys, glob, wave, shutil, numpy as np
D = sys.argv[1]; CUT = len(sys.argv) > 2 and sys.argv[2] == "cut"
def db(x, n=240):
    m = len(x) // n; return 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9)
for p in sorted(glob.glob(D + "/line_[0-9][0-9][0-9].wav")):
    x = np.frombuffer(wave.open(p).readframes(10 ** 8), np.int16).astype(np.float32) / 32768
    d = db(x); loud = np.where(d > -28)[0]
    if not len(loud): continue
    for side in ("tail", "head"):
        if side == "tail":
            seg = d[loud[-1] + 1:]; base = loud[-1] + 1
        else:
            seg = d[:loud[0]][::-1]; base = loud[0]
        # 声の終わりから 0.08 秒より先に、-48〜-28 dB の音が 0.12 秒以上続く所
        k = np.where(seg[8:] > -48)[0]
        if len(k) >= 12:
            t = (base + (8 + k[0]) * (1 if side == "tail" else -1)) * 0.01
            print(p.split("/")[-1], side, "息らしい音 %.2f 秒（長さ %.2f 秒、最大 %.0f dB）" % (t, len(k) * 0.01, seg[8:].max()))
            if CUT and side == "tail":
                shutil.copy(p, p.replace(".wav", "_before_breath.wav"))
                y = x[:int((base + 8 + k[0]) * 240)].copy(); f = np.linspace(1, 0, 480) ** 2; y[-480:] *= f
                with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes((y * 32767).astype(np.int16).tobytes())
