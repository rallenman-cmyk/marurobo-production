# 17本目 3章：決めた場所（世界の座標）や動く物が、カットの画面に入るかを数で出す（通しの点検：落ちる札・戻る玉が画面の外だった。カメラの見える範囲を頭で計算してまちがえた）
#   blender -b --factory-startup --python ptcheck.py -- <カット> <x,y,z | track名@秒> ...
#   出力：各点の画面の位置（左下 0,0 〜 右上 1,1）。0〜1 の外なら「外」
import bpy, sys, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index("--") + 1:]
name, pts = _a[0], _a[1:]
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [name, "/tmp/ptcheck_" + name, "--track"]
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "scenes19.py")}
exec(open(os.path.join(HERE, "scenes19.py"), encoding="utf-8").read(), g)
sc = bpy.context.scene; t0 = g["CLIPS"][name][1]
for p in pts:
    if "@" in p:
        nm, t = p.split("@"); fr = round((float(t) - t0) * sc.render.fps); sc.frame_set(max(sc.frame_start, fr))
        ob, dz = g["TRACK"][nm]; w = ob.matrix_world.translation.copy(); w.z += dz
    else:
        sc.frame_set((sc.frame_start + sc.frame_end) // 2); w = Vector(tuple(float(v) for v in p.split(",")))
    q = world_to_camera_view(sc, sc.camera, w)
    ok = 0 <= q.x <= 1 and 0 <= q.y <= 1 and q.z > 0
    print("PT %s %s → %.2f %.2f %s" % (name, p, q.x, q.y, "中" if ok else "外"))
