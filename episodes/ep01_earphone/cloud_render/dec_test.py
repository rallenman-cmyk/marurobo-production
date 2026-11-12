import bpy, sys, os, numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/human")
from hbuild import mk_mesh
D = np.load("/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/sheets/mesh_W1.npz")
ob = mk_mesh("h", D["Vh"], [tuple(q) for q in D["Qh"]], coll=bpy.context.scene.collection, mats=[])
print("BBOX before", np.round(np.min(D["Vh"], 0), 3), np.round(np.max(D["Vh"], 0), 3))
for r in (0.022, 0.05, 0.1):
    md = ob.modifiers.new("d", "DECIMATE"); md.ratio = r; md.use_collapse_triangulate = False
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); me = e.to_mesh()
    V = np.array([v.co[:] for v in me.vertices]); print("ratio", r, "faces", len(me.polygons), "bbox", np.round(V.min(0), 3), np.round(V.max(0), 3))
    e.to_mesh_clear(); ob.modifiers.remove(md)
