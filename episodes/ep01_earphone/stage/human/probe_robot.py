import bpy
from mathutils import Vector
O = bpy.data.objects; bpy.context.scene.frame_set(1)
def hier(o, d=0):
    r = [(o, d)]
    for c in o.children: r += hier(c, d + 1)
    return r
dg = bpy.context.evaluated_depsgraph_get()
def bb(o):
    if o.type not in {"MESH", "CURVE"}: return None
    e = o.evaluated_get(dg)
    try: me = e.to_mesh()
    except Exception: return None
    pts = [o.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    if not pts: return None
    return [[round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)]]
r = O["MARU / pause"]
print("ROBOT root loc", [round(v, 3) for v in r.location], "rot", [round(v, 3) for v in r.rotation_euler], "scale", [round(v, 3) for v in r.scale], "anim", bool(r.animation_data))
r.scale = (0.55, 0.55, 0.55); r.location = (0.14, -3.65, 0.14); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
for o, d in hier(r):
    print("ROBOT", "  " * d + o.name, o.type, "loc", [round(v, 3) for v in o.location], "rot", [round(v, 2) for v in o.rotation_euler], "bb", bb(o))
for n in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
    o = O.get(n)
    if o: print("BUTTON", n, o.type, "loc", [round(v, 3) for v in o.location], "scale", [round(v, 3) for v in o.scale], "parent", o.parent.name if o.parent else None, "bb", bb(o))
