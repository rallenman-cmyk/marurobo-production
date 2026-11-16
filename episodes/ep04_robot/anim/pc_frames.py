# PC の本番描画（100 コマずつの mp4）を、組み立て（assemble.py）が読めるコマの絵にする
#   python3 pc_frames.py <落としたフォルダ（*_0000-0099.mp4 と *_log.json）> <出力フォルダ> [幅=1280]
#   出力：<場面>_<コマ番号4桁>.jpg と <場面>_log.json。jpg にするのは、png だと 2 万コマで 20GB を超えるため
#   コマの数が足りない mp4 があれば止める（そろわないまま組み立てない）
import os, sys, re, glob, json, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor

src, out = sys.argv[1], sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 1280
os.makedirs(out, exist_ok=True)
jobs, bad = [], []
for mp4 in sorted(glob.glob(os.path.join(src, "*_[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9].mp4"))):
    m = re.match(r"(.+)_(\d{4})-(\d{4})\.mp4$", os.path.basename(mp4))
    k, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    jobs.append((mp4, k, a, b))
for lg in glob.glob(os.path.join(src, "*_log.json")):
    shutil.copy(lg, out)


def one(j):
    mp4, k, a, b = j
    if os.path.exists(os.path.join(out, "%s_%04d.jpg" % (k, b))): return None   # もうある
    tmp = os.path.join(out, "_t_%s_%04d" % (k, a)); os.makedirs(tmp, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "scale=%d:-2" % W, "-q:v", "2",
                    os.path.join(tmp, "f_%05d.jpg")], check=True)
    fs = sorted(os.listdir(tmp))
    if len(fs) != b - a + 1:
        shutil.rmtree(tmp); return "%s のコマが %d（%d のはず）" % (os.path.basename(mp4), len(fs), b - a + 1)
    for i, f in enumerate(fs):
        os.replace(os.path.join(tmp, f), os.path.join(out, "%s_%04d.jpg" % (k, a + i)))
    os.rmdir(tmp)
    return None


with ThreadPoolExecutor(4) as ex:
    for r in ex.map(one, jobs):
        if r: bad.append(r)
print("mp4", len(jobs), "本", "／足りない", bad or "なし")
if bad: sys.exit(1)
