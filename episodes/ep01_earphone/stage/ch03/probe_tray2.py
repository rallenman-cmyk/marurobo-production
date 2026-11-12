import bpy
from mathutils import Vector
sc = bpy.context.scene; O = bpy.data.objects
sc.frame_set(int(round(30.0 * 24)) + 1); bpy.context.view_layer.update()
cargo = next(o for o in O if o.name.startswith("Maru cargo") and o.type == "EMPTY")
inv = cargo.matrix_world.inverted()
for o in O:
    if o.type != "MESH": continue
    if not (o.name.startswith(("Cradle", "Static / Brass", "Maru cargo case", "Maru saddle")) ): continue
    if o.parent and o.parent.name.startswith("PARCEL"): continue
    pts = [inv @ (o.matrix_world @ Vector(c)) for c in o.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    print("PROBE2 %-22s in cargo frame x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (o.name, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
