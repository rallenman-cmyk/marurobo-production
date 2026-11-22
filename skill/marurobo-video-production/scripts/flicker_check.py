# PC の本番描画で「1 コマだけ違う絵」（1 コマおきの乱れ）を、全部の場面の全部のコマで探す（2026-11-22、6本目。
#   5本目で、PC のグラフィックボードで描いたときだけ、動く親に付けた点の雲が 1 コマおきに乱れて映った。pc_render/README.md の末尾）
#   python3 flicker_check.py <pc_frames.py の出力フォルダ（<場面>_<4桁>.jpg）> [しきい=6]
#   コマ i が、前（i-1）とも後（i+1）とも大きく違うのに、前と後どうしは似ている所を書き出す（ちらつき）。
#   数＝ min(差(i-1,i), 差(i,i+1)) − 差(i-1,i+1)（明るさ 0〜255 の差。16×9 の区画ごとに出して、いちばん大きい区画）
import os, sys, re, glob
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor

D = sys.argv[1]; TH = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
clips = {}
for f in glob.glob(os.path.join(D, "*_[0-9][0-9][0-9][0-9].jpg")):
    m = re.match(r"(.+)_(\d{4})\.jpg$", os.path.basename(f)); clips.setdefault(m.group(1), []).append((int(m.group(2)), f))


def small(f):
    return np.asarray(Image.open(f).convert("L").resize((192, 108), Image.BILINEAR), np.float32)


def one(k):
    fs = [f for _, f in sorted(clips[k])]; a = [small(f) for f in fs]; out = []
    for i in range(1, len(a) - 1):
        # 画面を 16×9 の区画に分け、区画ごとに比べる（点の雲のような小さな所のちらつきを、画面全体の平均で薄めない）
        blk = lambda x: np.abs(x).reshape(9, 12, 16, 12).mean((1, 3))
        d1 = blk(a[i] - a[i - 1]); d2 = blk(a[i + 1] - a[i]); d0 = blk(a[i + 1] - a[i - 1])
        s = float((np.minimum(d1, d2) - d0).max())
        if s > TH: out.append((i, round(float(s), 1)))
    return k, len(fs), out


with ProcessPoolExecutor(4) as ex:
    res = sorted(ex.map(one, sorted(clips)))
n = 0
for k, nf, out in res:
    if out: n += len(out); print("%s（%d コマ）：%d か所 %s" % (k, nf, len(out), out[:12]))
print("場面 %d・ちらつくコマ %d" % (len(res), n))
