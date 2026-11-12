# 電車の場面の連番がそろっているか（絵が開けるか・カメラの記録があるか）を確かめる
import os, json, sys
from PIL import Image
T = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/ch03/train_test"
need = list(range(0, 461)) + list(range(1651, 1752))
st = {}
for fn in sorted(os.listdir(T)):
    if fn.startswith("train_frames_log_") and fn.endswith(".json"):
        st.update(json.load(open(os.path.join(T, fn), encoding="utf-8"))["stills"])
bad, nolog = [], []
for i in need:
    fn = "t_%04d.png" % i; p = os.path.join(T, "frames_train", fn)
    try:
        im = Image.open(p); im.load(); assert im.size == (640, 360)
    except Exception as e: bad.append(i)
    if fn not in st: nolog.append(i)
print("frames", len(need), "bad/missing", len(bad), bad[:20], "no camera log", len(nolog), nolog[:20])
