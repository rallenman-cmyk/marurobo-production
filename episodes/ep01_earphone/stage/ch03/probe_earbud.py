import bpy, numpy as np
from mathutils import Vector
O = bpy.data.objects; bpy.context.scene.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
pts = []
def hier(o):
    r = [o]
    for c in o.children: r += hier(c)
    return r
for o in hier(O["Earbud exterior"]):
    if o.type != "MESH" or o.hide_render: continue
    e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
    P = np.array([tuple(mw @ v.co) for v in me.vertices]); e.to_mesh_clear()
    print("PROBE part %-28s z %.1f..%.1f  x %.1f..%.1f  y %.1f..%.1f" % (o.name[:28], P[:, 2].min(), P[:, 2].max(), P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()))
    pts.append(P)
P = np.concatenate(pts)
for z0, z1 in ((0, 3), (3, 7), (7, 10), (10, 12), (12, 14), (14, 16), (16, 19)):
    b = P[(P[:, 2] >= z0) & (P[:, 2] < z1)]
    if len(b): print("PROBE band z%2d-%2d  x %.2f..%.2f (c %.2f)  y %.2f..%.2f (c %.2f)" % (z0, z1, b[:, 0].min(), b[:, 0].max(), b[:, 0].mean(), b[:, 1].min(), b[:, 1].max(), b[:, 1].mean()))
