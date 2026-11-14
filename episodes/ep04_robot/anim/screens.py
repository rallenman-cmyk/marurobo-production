# ロボットではありません回：パソコンの画面の絵を、コマごとに作る（3D の画面の板に貼る。字は書かない）
# python3 screens.py <場面> <出力フォルダ> <t0> <t1> [間引き]
#   s04：矢印がチェック欄へ一直線（等しい速さ）→ カチッ → 欄がくるくる → 絵のテストに切り替わる
#   時刻は声の時刻（scenes.py と同じ表）から決める
import sys, os, json, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "..", "storyboard", "make_textures.py"), encoding="utf-8").read()
sys_argv = sys.argv; sys.argv = ["x", "/tmp"]
exec(_src.split("# 1. 買い物")[0])                # base・arrow・card・tent と色
exec(_src[_src.index("# 4. 絵のテスト"):].split("im.save(out + '/scr_test.png')")[0].replace("im, d = base()", "im, d = base()", 1) + "\nTEST = im.copy()")
sys.argv = sys_argv
SC, OUTD, T0, T1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
STEP = int(sys.argv[5]) if len(sys.argv) > 5 else 1
os.makedirs(OUTD, exist_ok=True)
SUBS = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
def said(text, after=0.0):
    for a, c, t in SUBS:
        if a >= after and t.replace("\\N", "").startswith(text): return a
    raise KeyError(text)
FPS = 24


def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def spinner(d, ang):
    d.rounded_rectangle([425, 460, 525, 560], 10, fill='white')
    d.arc([430, 465, 520, 555], ang, ang + 280, fill=TEAL, width=10)


if SC == "s04":
    click = said("カチッ")                         # 「カチッ」を言う瞬間
    a0, a1 = said("マウスで") + 0.3, click - 0.75    # 矢印が動く間（等しい速さ＝機械のようにまっすぐ）
    test_t = said("代わりに")
    P0, P1 = (1250, 820), (470, 505)
    for k in range(0, round((T1 - T0) * FPS), STEP):
        t = T0 + k / FPS
        if t >= test_t:
            im = TEST.copy(); d = ImageDraw.Draw(im)
            x = min(1, (t - test_t) / 0.25)      # ぱっと出る（少し下から）
            if x < 1:
                bg, _ = base(); bg = bg.copy(); ImageDraw.Draw(bg).rectangle([0, 90, W, H], fill=(214, 222, 232)); card(ImageDraw.Draw(bg), spin=True)
                im = Image.blend(bg, im, x)
        else:
            im, d = base(); d.rectangle([0, 90, W, H], fill=(214, 222, 232)); card(d)
            u = min(1, max(0, (t - a0) / (a1 - a0)))
            n = int(u * 14)
            for j in range(n):                    # 通った所に点の跡（まっすぐ）
                v = j / 13; x = P0[0] + (P1[0] - P0[0]) * v; y = P0[1] + 40 + (P1[1] - P0[1]) * v
                d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=TEAL)
            x = P0[0] + (P1[0] - P0[0]) * u; y = P0[1] + (P1[1] - P0[1]) * u
            if t >= click: spinner(d, (t - click) * 400)
            arrow(d, x, y, 1.6)
        im.save(os.path.join(OUTD, "%s_%04d.png" % (SC, k + 1)))
    print("screens", SC, round((T1 - T0) * FPS), "コマ", dict(a0=a0, a1=a1, click=click, test=test_t))
