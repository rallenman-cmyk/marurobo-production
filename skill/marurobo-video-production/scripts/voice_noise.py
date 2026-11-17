# 声のファイルの「ザザッ」（白い雑音のかたまり）を探す・切る
#   探す：python3 voice_noise.py check <wav>…   → 雑音が 3 窓（60ms）以上続く所を一覧（1 窓だけは「サ行」なので数えない）
#   切る：python3 voice_noise.py fix <wav>… --backup <dir>   → 終わりの雑音を、最後の声の所 +0.06 秒で切り、10ms でしぼる
#   声を作る AI（Gemini TTS）は、まれに言い終わりのあとに 0.1〜0.2 秒の雑音を付けて返す。音の大きさだけで声の範囲を決めると残ってしまう（QR回 v13）
import sys, os, wave, shutil, numpy as np
W = 0.02
def load(p):
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x, sr
def save(p, x, sr):
    with wave.open(p, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
def flat(s):
    S = np.abs(np.fft.rfft(s * np.hanning(len(s)))) + 1e-9; return float(np.exp(np.mean(np.log(S))) / np.mean(S))
def scan(x, sr):
    w = int(W * sr); rows = []
    for i in range(0, len(x) - w, w):
        s = x[i:i + w]; r = float(np.sqrt(np.mean(s ** 2))); rows.append((i, r, flat(s) if r > 0.002 else 0.0))
    return rows, w
def runs(rows):
    out = []; cur = []
    for i, r, f in rows:
        if r > 0.05 and f > 0.7: cur.append(i)
        else:
            if len(cur) >= 3: out.append((cur[0], cur[-1]))
            cur = []
    if len(cur) >= 3: out.append((cur[0], cur[-1]))
    return out
if __name__ == '__main__':
    mode, args = sys.argv[1], sys.argv[2:]
    bk = None
    if '--backup' in args: k = args.index('--backup'); bk = args[k + 1]; args = args[:k] + args[k + 2:]
    bad = 0
    for p in args:
        x, sr = load(p); rows, w = scan(x, sr); rr = runs(rows)
        if not rr: continue
        bad += 1; print(os.path.basename(p), round(len(x) / sr, 2), 's  雑音:', [(round(a / sr, 2), round((b + w) / sr, 2)) for a, b in rr])
        if mode == 'fix':
            a0 = rr[-1][0]
            if (len(x) - a0) / sr > 0.5: print('   終わりの雑音ではないので切らない（手で確かめる）'); continue
            voiced = [i for i, r, f in rows if i < a0 and r > 0.01 and f < 0.5]
            cut = min(a0, (voiced[-1] + w if voiced else a0) + int(0.06 * sr))
            if bk: os.makedirs(bk, exist_ok=True); shutil.copy(p, os.path.join(bk, os.path.basename(p)))
            y = x[:cut].copy(); f = int(0.01 * sr); y[-f:] *= np.linspace(1, 0, f); save(p, y, sr)
            print('   切った：%.2f → %.2f 秒' % (len(x) / sr, len(y) / sr))
    print('雑音のあるファイル', bad)
