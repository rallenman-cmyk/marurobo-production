# 動画のコマごとの鋭さを測り、前後より急に落ちるコマ（カットのつなぎ目のブレなど）を探す
#   使い方: python3 blurscan.py 動画.mp4 [始まり秒 長さ秒]
import sys, subprocess
import numpy as np
v = sys.argv[1]; ss = sys.argv[2] if len(sys.argv) > 2 else "0"; dur = sys.argv[3] if len(sys.argv) > 3 else None
W, H = 480, 270
cmd = ["ffmpeg", "-v", "error", "-ss", ss] + (["-t", dur] if dur else []) + ["-i", v, "-vf", "scale=%d:%d" % (W, H), "-f", "rawvideo", "-pix_fmt", "gray", "-"]
raw = subprocess.run(cmd, capture_output=True).stdout
n = len(raw) // (W * H); a = np.frombuffer(raw[:n * W * H], np.uint8).reshape(n, H, W).astype(float)
s = []
for f in a:
    lap = f[1:-1, 1:-1] * 4 - f[:-2, 1:-1] - f[2:, 1:-1] - f[1:-1, :-2] - f[1:-1, 2:]; s.append(lap.var())
s = np.array(s); hits = []
for i in range(1, n - 1):
    if s[i] < 0.45 * min(s[i - 1], s[i + 1]) or (s[i] < 0.45 * s[i - 1] and i + 2 < n and s[i + 1] < 0.45 * s[i + 2]):
        hits.append(i)
print("frames", n, "dips", len(hits), ["%.2fs(%.0f/%.0f/%.0f)" % (float(ss) + i / 24.0, s[i - 1], s[i], s[i + 1]) for i in hits][:40])
