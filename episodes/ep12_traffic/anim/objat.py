# 12本目 v3 の点検：画面のある所（左下 0,0〜右上 1,1）に映っている物の名前を出す（何か分からない白い物を探すため）
#   blender -b --factory-startup --python objat.py -- <カット> <秒> <x0,y0,x1,y1>
import bpy, sys, os
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index("--") + 1:]
name, tt, box = _a[0], float(_a[1]), [float(v) for v in _a[2].split(",")]
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [name, "/tmp/objat_" + name, "--track"]
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "scenes.py")}
exec(open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read(), g)
sc = bpy.context.scene; t0 = g["CLIPS"][name][1]
sc.frame_set(max(sc.frame_start, round((tt - t0) * sc.render.fps)))
dg = bpy.context.evaluated_depsgraph_get()
for ob in sc.objects:
    if ob.type != "MESH" or ob.hide_render: continue
    w = ob.matrix_world.translation
    q = world_to_camera_view(sc, sc.camera, w)
    if q.z > 0 and box[0] <= q.x <= box[2] and box[1] <= q.y <= box[3]:
        print("OBJAT %s 画面 %.2f %.2f 距離 %.1f 世界 %.1f %.1f %.1f 大きさ %.2f" % (ob.name, q.x, q.y, q.z, w.x, w.y, w.z, max(ob.matrix_world.to_scale())))
