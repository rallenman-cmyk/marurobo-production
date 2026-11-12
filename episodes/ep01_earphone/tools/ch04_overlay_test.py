# 3D の試し描き（still_*.png）に、組み立ての札を重ねて確かめる
import sys, os, json, importlib.util
from PIL import Image, ImageDraw
ST = sys.argv[1]; OUT = sys.argv[2]; times = [float(x) for x in sys.argv[3].split(",")]; dst = sys.argv[4]
sys.argv = ["x", OUT, "--pair=" + ST]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stage", "ch03", "ch04_assemble6.py"), encoding="utf-8").read()
src = src[:src.index("# ---------------------------------------------------------------- 絵")]          # 札を描く所まで
g = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stage", "ch03", "ch04_assemble6.py")}
exec(compile(src, "assemble6_head", "exec"), g)
PL = g["PL"]; W, H = 1280, 720
tiles = []
for t in times:
    k = min(max(int(round((t - PL["t0"]) * 24)) + 1, 1), PL["frames"])
    im = Image.open(os.path.join(ST, "still_%06.2f.png" % t)).convert("RGB").resize((W, H), Image.LANCZOS)
    g["pair_overlay"](im, t, PL["anchors"][k - 1]); ImageDraw.Draw(im).text((8, 8), "t=%.2f" % t, fill=(255, 0, 0)); tiles.append(im.resize((640, 360), Image.LANCZOS))
cols = 3; sh = Image.new("RGB", (640 * cols, 360 * ((len(tiles) + cols - 1) // cols)))
for j, im in enumerate(tiles): sh.paste(im, ((j % cols) * 640, (j // cols) * 360))
sh.save(dst, quality=88); print(dst)
