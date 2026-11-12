# ch03_stage.py のあとに走らせて、トレー・受け皿・荷物の大きさを調べる
import bpy
from mathutils import Vector
sc = bpy.context.scene
for t in (30.0,):
    sc.frame_set(int(round(t * 24)) + 1); bpy.context.view_layer.update()
    for o in bpy.data.objects:
        n = o.name
        if o.type != "MESH" or not any(k in n for k in ("Cradle", "Brass", "saddle", "PARCEL", "Parcel", "Label", "label", "cargo", "Cargo", "Pull")): continue
        if o.hide_render: continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = [min(v[i] for v in bb) for i in range(3)]; hi = [max(v[i] for v in bb) for i in range(3)]
        # ロボの向きのローカルで測る：親（荷物）の行列で
        par = o.parent
        print("PROBE %-40s parent=%-28s size(local)=%s  zmin %.3f zmax %.3f" % (n[:40], (par.name if par else "-")[:28], tuple(round(d, 3) for d in o.dimensions), lo[2], hi[2]))
