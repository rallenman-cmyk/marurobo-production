import bpy
from mathutils import Vector
s=bpy.context.scene; s.frame_set(1)
O=bpy.data.objects; dg=bpy.context.evaluated_depsgraph_get()
def hier(o):
    r=[o]
    for c in o.children: r+=hier(c)
    return r
def bbox(objs):
    pts=[]
    for o in objs:
        if o.type in {"MESH","CURVE","FONT"}:
            e=o.evaluated_get(dg)
            try: me=e.to_mesh()
            except Exception: continue
            pts+=[o.matrix_world@v.co for v in me.vertices]; e.to_mesh_clear()
    if not pts: return None
    mn=[min(p[i] for p in pts) for i in range(3)]; mx=[max(p[i] for p in pts) for i in range(3)]
    return [round(v,3) for v in mn],[round(v,3) for v in mx]
for n in ["Inside 04","Inside 05","Inside 06","Maru cargo","Maru"]:
    r=O[n]; hs=hier(r)
    print("PROBE",n,"type",r.type,"loc",[round(v,2) for v in r.matrix_world.translation],"scale",[round(v,2) for v in r.scale],"kids",[h.name for h in hs[1:]][:8],"bbox",bbox(hs),"hide",r.hide_render)
for n in ["Maru • torso","Maru • leg","Maru • leg.001","Maru • tilting delivery cradle","Maru • antenna","Inner lens ring","Eye lens"]:
    o=O[n]; print("PROBE",n,"loc",[round(v,3) for v in o.location],"rot",[round(v,3) for v in o.rotation_euler],"parent",o.parent.name if o.parent else None,"kids",[c.name for c in o.children][:6])
print("PROBE mats",[m.name for m in bpy.data.materials])
print("PROBE fonts",[f.name for f in bpy.data.fonts])
