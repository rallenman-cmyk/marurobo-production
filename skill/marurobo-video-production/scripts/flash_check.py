"""出来上がった動画の「一瞬だけ映る絵」を、1 コマずつ機械で探す（2026-11-14 ユーザー「送る前の確認が雑」）。
12 秒ごとの絵を見るだけでは、0.3〜1 秒だけ映る場面（差し込みのすき間にのぞく元の場面など）は見つからないため。
使い方：python3 flash_check.py 動画.mp4 [短い=1.2] [出力フォルダ]
  ・絵が大きく変わる所（切り替わり）を全コマで探し、切り替わりの間が「短い」秒より短い所を書き出す
  ・重ねてゆっくり変わる所（0.3〜0.7 秒のつなぎ）は 1 つの切り替わりにまとめる
  ・出力フォルダを付けると、見つけた所の前後 1.5 秒のコマを並べた絵（flash_<秒>.png）を作る。必ず目で見る
字幕は下の帯を除いて比べる（字幕の切り替わりを場面の切り替わりと取り違えないため）。
"""
import os, subprocess, sys
import numpy as np

W, H, FPS = 96, 54, 24


def frames(src):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", "fps=%d,scale=%d:%d,format=gray" % (FPS, W, H),
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    x = np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W).astype(np.float32)
    return x[:, : int(H * 0.78)]                     # 字幕の帯（下 22%）は比べない


def scan(x, soft=2.5, thr=14.0, short=1.2):
    """止まっている所（コマの差が小さいコマが続く所）と、変わっている所に分ける。
    ① 止まっている所が short 秒より短く、前後が大きく変わる → 一瞬だけ映る絵
    ② 変わっている所の途中に、前の絵と次の絵のどちらとも違う絵が混ざる → つなぎ目で別の絵が透ける（溶かしの重ねの途中に元の場面など）"""
    d = np.abs(np.diff(x, axis=0)).mean(axis=(1, 2))
    st = d < soft
    runs, i, n = [], 0, len(d)
    while i < n:                                     # 止まっている所 [始めのコマ, 終わりのコマ]
        if st[i]:
            j = i
            while j < n and st[j]: j += 1
            runs.append((i, j)); i = j
        else: i += 1
    found = []
    for (a0, a1), (b0, b1), (c0, c1) in zip(runs, runs[1:], runs[2:]):
        if (b1 - b0) / FPS < short and b0 - a1 < 2 * FPS and c0 - b1 < 2 * FPS:
            e1 = np.abs(x[b0] - x[a1]).mean(); e2 = np.abs(x[b1] - x[c0]).mean()
            if e1 > thr and e2 > thr: found.append((b0 / FPS, (b1 - b0) / FPS, "一瞬だけ映る絵"))
    for (a0, a1), (b0, b1) in zip(runs, runs[1:]):
        if b0 - a1 > 2 * FPS or b0 - a1 < 3: continue
        A, B = x[a1], x[b0]; L = b0 - a1
        res = [np.abs(x[k] - (A + (B - A) * (k - a1) / L)).mean() for k in range(a1 + 1, b0)]
        k = int(np.argmax(res))
        if res[k] > thr * 0.7: found.append(((a1 + 1 + k) / FPS, L / FPS, "つなぎの途中に別の絵"))
    return sorted(found)


def main():
    src = sys.argv[1]; short = float(sys.argv[2]) if len(sys.argv) > 2 else 1.2
    outd = sys.argv[3] if len(sys.argv) > 3 else None
    x = frames(src); found = scan(x, short=short)
    for t, du, why in found:
        print("%d:%05.2f  %.2f 秒  %s" % (t // 60, t % 60, du, why))
    print("一瞬だけ映る所・つなぎで別の絵が透ける所：%d か所" % len(found))
    if outd and found:
        from PIL import Image, ImageDraw
        os.makedirs(outd, exist_ok=True)
        for t, du, why in found:
            png = os.path.join(outd, "flash_%07.2f.png" % t)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.2f" % max(0, t - 1.0), "-t", "%.2f" % (du + 2.0), "-i", src,
                            "-vf", "fps=8,scale=240:-2,tile=6x%d" % int(np.ceil((du + 2.0) * 8 / 6)), "-frames:v", "1", png], check=True)


if __name__ == "__main__":
    main()
