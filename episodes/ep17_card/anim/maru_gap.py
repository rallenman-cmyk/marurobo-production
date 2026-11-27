# 17本目 v7 のコメント「スマホに貫通」から：まるロボ（track "maru" の形を全部）と、ある物（材質の名前）とのすき間を、0.125 秒ごとに出す
#   blender -b --factory-startup --python maru_gap.py -- <カット> <材質の名前=sp_body>
#   行ごとに「時刻 中に入った点の数 いちばん近いすき間(m)」。中に入った点 0・押すときのすき間 1 cm 以下が、当たって見える押し方
import bpy, sys, os
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index("--") + 1:]
name = _a[0]; MAT = _a[1] if len(_a) > 1 else "sp_body"
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [name, "/tmp/gap_" + name, "--track"]
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "scenes.py")}
exec(open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read(), g)
sc = bpy.context.scene; TR = g["TRACK"]; FPS = sc.render.fps
top = TR["maru"][0]
while top.parent is not None: top = top.parent
ms = [o for o in [top] + list(top.children_recursive) if o.type == "MESH" and not o.hide_render]
tg = [o for o in sc.objects if o.type == "MESH" and any(sl.material and sl.material.name.startswith(MAT) for sl in o.material_slots)]
for k in range(sc.frame_start, sc.frame_end + 1, max(1, FPS // 8)):
    sc.frame_set(k)
    pts = [m.matrix_world @ v.co for m in ms for v in m.data.vertices]
    ins = 0; gap = 9.0
    for o in tg:
        inv = o.matrix_world.inverted(); sz = o.matrix_world.to_scale()
        lo = Vector([min(c[i] for c in o.bound_box) for i in range(3)]); hi = Vector([max(c[i] for c in o.bound_box) for i in range(3)])
        for p in pts:
            lp = inv @ p
            if all(lo[i] < lp[i] < hi[i] for i in range(3)): ins += 1; continue
            d = Vector([max(lo[i] - lp[i], 0, lp[i] - hi[i]) * sz[i] for i in range(3)]).length
            gap = min(gap, d)
    print("GAP %.3f %d %.3f" % (k / FPS, ins, gap))
