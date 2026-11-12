import bpy
from mathutils import Vector
s=bpy.context.scene; O=bpy.data.objects
def hier(o):
    r=[o]
    for c in o.children: r+=hier(c)
    return r
def bbox(objs, dg):
    pts=[]
    for o in objs:
        if o.type in {"MESH","CURVE","FONT"} and not o.hide_render:
            e=o.evaluated_get(dg)
            try: me=e.to_mesh()
            except Exception: continue
            pts+=[o.matrix_world@v.co for v in me.vertices]; e.to_mesh_clear()
    if not pts: return None
    return [round(min(p[i] for p in pts),2) for i in range(3)],[round(max(p[i] for p in pts),2) for i in range(3)]
for f in (1, 300, 560):
    s.frame_set(f); dg=bpy.context.evaluated_depsgraph_get()
    print(f"PROBE frame {f}")
    tr=O["TRAIN / fixed carriage"]
    print("PROBE  train bbox", bbox(hier(tr)[:12], dg))
    for n in ["PASSENGER 00","PASSENGER 02","PASSENGER 07"]:
        o=O.get(n)
        if o: print("PROBE ",n,"loc",[round(v,2) for v in o.matrix_world.translation],"bbox",bbox(hier(o),dg),"kids",[c.name for c in o.children][:6])
    for n in ["MARU / pause","Pause button","Pause button base","PHONE / opening","Director camera"]:
        o=O.get(n)
        if o: print("PROBE ",n,"loc",[round(v,2) for v in o.matrix_world.translation],"scale",[round(v,2) for v in o.scale],"hide",o.hide_render)
names=[o.name for o in O]
print("PROBE earbud-like:",[n for n in names if any(k in n.lower() for k in ["bud","ear","head","phone"])][:30])
print("PROBE lights:",[(o.name,o.data.type,round(o.data.energy,1)) for o in O if o.type=="LIGHT"])
