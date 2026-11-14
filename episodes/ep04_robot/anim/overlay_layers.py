# ロボットではありません回：絵コンテの 2D（札・チェック欄など）を、3D の上に重ねる「透明な層」として書き出す
# python3 overlay_layers.py <3D の絵のフォルダ（board_rich）> <フォントのフォルダ> <出力フォルダ>
#   board_overlay.py をそのまま走らせ、3D の絵（load('b..')）の代わりに透明な板を渡す。
#   出力：<出力>/<ショット>.png（RGBA）と shots.json（ショットごとに、3D の上の層か〈base＝3D の場面名〉、2D だけの絵か）
import os, sys, json
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SRC0, F, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(os.path.join(HERE, "..", "storyboard", "board_overlay.py"), encoding="utf-8").read()
sys.argv = [sys.argv[0], SRC0, F, OUT]
BASE = {}


class Layer(Image.Image):
    pass


def _load(name):
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); im.info["base"] = name
    return im


g = {"__name__": "ov", "__file__": os.path.join(HERE, "..", "storyboard", "board_overlay.py")}
src = src.replace("\ndef anch(name):", "\n_load_real = load\nload = __LOAD__\ndef anch(name):", 1)
src = src.replace("def save(im, name, start_id, dt=0.0):\n", "def save(im, name, start_id, dt=0.0):\n    __BASE__[name] = im.info.get('base')\n", 1)
g["__LOAD__"] = _load; g["__BASE__"] = BASE
exec(compile(src, "board_overlay.py", "exec"), g)
sh = json.load(open(os.path.join(OUT, "shots.json"), encoding="utf-8"))
for s in sh: s["base"] = BASE.get(s["img"][:-4])
json.dump(sh, open(os.path.join(OUT, "shots.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("層", sum(1 for s in sh if s["base"]), "／ 2D だけ", sum(1 for s in sh if not s["base"]))
