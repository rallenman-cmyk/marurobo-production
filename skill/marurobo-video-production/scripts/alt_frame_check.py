# 1 コマおきに変わる所（i-1 と i+1 は似ているのに、i だけ違う）を全コマで探す。python3 alt_frame_check.py 通し.mp4（5本目の本番で、PC のグラフィックボードが動く親につけた点の雲を 1 コマおきに別の場所で描いた）
import subprocess, sys, numpy as np
v = sys.argv[1]; W, H = 160, 90
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", v, "-vf", "scale=%d:%d,format=gray" % (W, H), "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
fr = []; i = 0; hits = []
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    fr.append(np.frombuffer(b, np.uint8).astype(np.float32))
    if len(fr) > 3: fr.pop(0)
    if len(fr) == 3:
        a, c, d = fr
        s = np.abs(c - a).mean(); s2 = np.abs(c - d).mean(); o = np.abs(a - d).mean()
        if min(s, s2) > 1.5 and o < 0.35 * min(s, s2): hits.append((i - 1) / 24.0)
    i += 1
gr = []
for t in hits:
    if gr and t - gr[-1][-1] < 0.3: gr[-1].append(t)
    else: gr.append([t])
for g in gr: print("%d:%05.2f〜%05.2f  %d コマ" % (g[0] // 60, g[0] % 60, g[-1] % 60, len(g)))
print("全", i, "コマ・見つかった所", len(gr))
