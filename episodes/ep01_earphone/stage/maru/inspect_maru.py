import bpy, json
from mathutils import Vector
O = bpy.data.objects
def hier(o):
    out=[o]
    for c in o.children: out+=hier(c)
    return out
root = O["Maru"]
res = []
for o in hier(root):
    bb = None
    if o.type == "MESH":
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        bb = [[round(min(v[i] for v in ws),3) for i in range(3)], [round(max(v[i] for v in ws),3) for i in range(3)]]
    mats = [m.name for m in o.data.materials] if o.type == "MESH" else []
    res.append(dict(name=o.name, type=o.type, parent=o.parent.name if o.parent else None, loc=[round(x,3) for x in o.location], rot=[round(x,3) for x in o.rotation_euler], scl=[round(x,3) for x in o.scale], mats=mats, bb=bb, nverts=len(o.data.vertices) if o.type=="MESH" else 0, mods=[m.type for m in o.modifiers]))
for r in res: print("OBJ", json.dumps(r, ensure_ascii=False))
m = bpy.data.materials.get("Amber status")
if m and m.node_tree:
    for n in m.node_tree.nodes: print("NODE", n.bl_idname, n.name, [ (i.name, getattr(i,'default_value',None) if not hasattr(getattr(i,'default_value',None),'__len__') else list(i.default_value)) for i in n.inputs if i.name in ("Emission Strength","Strength","Base Color","Color","Emission Color")])
print("ROOTWORLD", [list(r) for r in root.matrix_world])
