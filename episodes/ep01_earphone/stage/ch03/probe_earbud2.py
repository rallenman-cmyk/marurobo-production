import bpy
from mathutils import Vector
O = bpy.data.objects
def hier(o, d=0):
    out = [(o, d)]
    for c in o.children: out += hier(c, d + 1)
    return out
bpy.context.scene.frame_set(1)
for root in ("Earbud exterior",):
    allp = []
    for o, d in hier(O[root]):
        if o.type == "MESH":
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]; allp += pts
            lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
            print("EB %s%-34s x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % ("  " * d, o.name[:34], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
        else:
            print("EB %s%-34s (%s) loc %s" % ("  " * d, o.name[:34], o.type, tuple(round(v, 2) for v in o.matrix_world.translation)))
    lo = [min(p[i] for p in allp) for i in range(3)]; hi = [max(p[i] for p in allp) for i in range(3)]
    print("EB TOTAL x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    r = O[root]; print("EB root matrix", [list(map(lambda v: round(v, 3), row)) for row in r.matrix_world], "parent", r.parent)
