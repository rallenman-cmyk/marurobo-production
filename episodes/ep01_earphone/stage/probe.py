import bpy
from mathutils import Vector
s=bpy.context.scene; s.frame_set(1)
O=bpy.data.objects
def hier(o): 
    r=[o]
    for c in o.children: r+=hier(c)
    return r
for n in ["Eye lens","Lens black housing","Maru • tilting delivery cradle","Maru cargo","Maru • antenna"]:
    o=O.get(n)
    if o: print("PROBE",n,"world",[round(v,2) for v in o.matrix_world.translation],"hide",o.hide_render)
m=O["Maru"]; print("PROBE Maru loc",[round(v,2) for v in m.location],"rotz",round(m.rotation_euler.z,3),"hide",m.hide_render)
dg=bpy.context.evaluated_depsgraph_get()
for n in ["Static / Porcelain.003","Static / Graphite.002","Static / Titanium"]:
    o=O.get(n)
    if not o: continue
    e=o.evaluated_get(dg); me=e.to_mesh(); mw=o.matrix_world
    pts=[mw@v.co for v in me.vertices]
    for z0,z1 in [(0.5,1.5),(2,3),(5,7),(10,12)]:
        band=[p for p in pts if z0<=p.z<=z1]
        if band:
            xs=[p.x for p in band]; ys=[p.y for p in band]
            print("PROBE",n,f"z{z0}-{z1}","x",round(min(xs),2),round(max(xs),2),"y",round(min(ys),2),round(max(ys),2),"hide",o.hide_render)
    zs=[p.z for p in pts]; print("PROBE",n,"zrange",round(min(zs),2),round(max(zs),2)); e.to_mesh_clear()
print("PROBE earbud hidden:",[ (o.name,o.hide_render) for o in hier(O["Earbud exterior"]) if o.hide_render])
print("PROBE materials:",[m.name for m in bpy.data.materials][:40])
