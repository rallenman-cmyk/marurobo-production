import bpy
s=bpy.context.scene; O=bpy.data.objects; s.frame_set(1)
def hier(o):
    r=[o]
    for c in o.children: r+=hier(c)
    return r
for n in ["PASSENGER 00","PASSENGER 01","PASSENGER 05"]:
    p=O[n]; mats=set(); names=[]
    for o in hier(p):
        names.append(o.name)
        if o.type=="MESH":
            for m in o.data.materials:
                if m: mats.add(m.name)
    print("PROBE",n,"parts",names[:26]); print("PROBE   mats",sorted(mats))
for n in ["Window","Window.001","Carriage ceiling","Pause button","Pause pulse","Pause button base"]:
    o=O.get(n)
    if o: print("PROBE",n,"dims",[round(v,2) for v in o.dimensions],"mats",[m.name for m in o.data.materials if m] if o.type=="MESH" else o.type,"loc",[round(v,2) for v in o.matrix_world.translation])
for m in bpy.data.materials:
    if any(k in m.name.lower() for k in ["screen","glass","window","display","sky"]):
        nodes=[n.type for n in m.node_tree.nodes] if m.use_nodes else []
        print("PROBE mat",m.name,nodes[:6], getattr(m,"surface_render_method",None))
w=s.world; print("PROBE world", w.name if w else None)
