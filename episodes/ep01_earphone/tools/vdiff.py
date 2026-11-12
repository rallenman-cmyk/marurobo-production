# 二つの動画の絵の違う所（時刻の区間）を探す：小さく（160×90、4コマ/秒）して、コマごとの差の平均
import sys, subprocess, numpy as np
def frames(p, fps=4, w=160, h=90):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", "fps=%d,scale=%d:%d" % (fps, w, h), "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8); return a.reshape(-1, h, w).astype(np.float32)
a, b = frames(sys.argv[1]), frames(sys.argv[2]); n = min(len(a), len(b))
d = np.abs(a[:n] - b[:n]).mean(axis=(1, 2)); mx = np.abs(a[:n] - b[:n]).max(axis=(1, 2))
segs = []; on = False
for i in range(n):
    hit = mx[i] > 60 and d[i] > 0.15
    if hit and not on: s0 = i; on = True
    if not hit and on: segs.append((s0 / 4, i / 4)); on = False
if on: segs.append((s0 / 4, n / 4))
print("frames", len(a), len(b), "diff segments", len(segs))
for s0, s1 in segs: print("  %.2f-%.2f" % (s0, s1))
