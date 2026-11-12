import bpy, json
from mathutils import Vector
O = bpy.data.objects; s = bpy.context.scene; s.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
def hier(o):
    r = [o]
    for c in o.children: r += hier(c)
    return r
def bb(o):
    if o.type not in {"MESH", "CURVE", "FONT"}: return None
    e = o.evaluated_get(dg)
    try: me = e.to_mesh()
    except Exception: return None
    pts = [o.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    if not pts: return None
    return [[round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)]]
out = {}
for n in ["PASSENGER 00", "PASSENGER 05"]:
    p = O[n]; out[n] = {"loc": [round(v, 3) for v in p.matrix_world.translation], "rot": [round(v, 3) for v in p.rotation_euler], "scale": [round(v, 3) for v in p.scale], "parts": {}}
    for o in hier(p):
        out[n]["parts"][o.name] = {"type": o.type, "bb": bb(o), "parent": o.parent.name if o.parent else None,
                                   "mats": [m.name for m in o.data.materials if m] if o.type in {"MESH", "CURVE"} else None}
pas = sorted([o.name for o in O if o.name.startswith("PASSENGER") and o.parent is None])
out["passengers"] = {n: {"loc": [round(v, 3) for v in O[n].matrix_world.translation], "rotz": round(O[n].rotation_euler.z, 3), "nchild": len(hier(O[n]))} for n in pas}
seats = [o for o in O if "seat" in o.name.lower() or "bench" in o.name.lower()]
out["seats"] = {o.name: bb(o) for o in seats[:12]}
floor = [o for o in O if "floor" in o.name.lower()]
out["floors"] = {o.name: bb(o) for o in floor[:5]}
json.dump(out, open("/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/human/probe.json", "w"), ensure_ascii=False, indent=1)
print("PROBE done")
