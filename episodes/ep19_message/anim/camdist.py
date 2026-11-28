# 17本目：カメラとまるロボの近さを数える（試しの絵の点検：家の中の小さなまるロボ（0.40 倍）にカメラが 0.6〜0.8 m まで寄り、画面がまるロボでふさがった）
#   blender -b --factory-startup --python camdist.py -- <カット名>
#   カットの間 0.25 秒ごとに、カメラから まるロボの胴の真ん中までの距離と、まるロボが画面に占める高さの割合を出す。
#   出力の最後に「CAMDIST <カット> <いちばん近い距離 m> <画面の高さに占める最大の割合>」。家の中は 0.9 m 以上・割合 0.6 以下にする
import bpy, sys, os
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index("--") + 1:]
name = _a[0]
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [name, "/tmp/camdist_" + name, "--track"]
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "scenes.py")}
exec(open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read(), g)
sc = bpy.context.scene; FPS = sc.render.fps
M = g["MARU_ALL"][0] if g["MARU_ALL"] else None
if M is None:
    print("CAMDIST %s - -" % name); sys.exit(0)
t0, t1 = g["CLIPS"][name][1], g["CLIPS"][name][2]
dmin, hmax = 99.0, 0.0
for k in range(sc.frame_start, sc.frame_end + 1, max(1, FPS // 4)):
    sc.frame_set(k)
    cam = sc.camera; tp = M.torso.matrix_world.translation
    d = (cam.matrix_world.translation - tp).length
    top = tp.copy(); top.z += 0.5 * M.s; bot = tp.copy(); bot.z -= 0.5 * M.s
    a = world_to_camera_view(sc, cam, top); b = world_to_camera_view(sc, cam, bot)
    if 0 < a.z and -0.2 < (a.x + b.x) / 2 < 1.2:
        dmin = min(dmin, d); hmax = max(hmax, abs(a.y - b.y))
print("CAMDIST %s %.2f %.2f" % (name, dmin, hmax))
