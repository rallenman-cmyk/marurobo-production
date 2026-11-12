import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector
import hchar, hrig, people, ref_people
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
cfg = dict(ref_people.PEOPLE["M1"]); coll = bpy.data.collections.new("P"); bpy.context.scene.collection.children.link(coll)
ch = hchar.make_character("TM1", cfg, coll, S=1.0); rig = hrig.Rig(ch["arm"])
person = dict(ch, rig=rig, kind=cfg["pose"], phase=0.0, headz=0.0, headx=0.0, blink_T=99.0)
people.base_pose(person, 0.4)
for nme in rig.names:
    pb = ch["arm"].pose.bones[nme]; pb.rotation_quaternion = rig.q[nme]; pb.location = rig.loc[nme]
bpy.context.view_layer.update(); rig.fk()
hc = np.asarray(ch["hc"]); s = ch["s"]
p_rest = hc + np.array([0.0077, -0.0985, -0.0247]); pw = ch["arm"].matrix_world @ Vector(tuple(rig.posed_point("head", p_rest)))
print("PROBE point", tuple(round(x, 4) for x in pw))
dg = bpy.context.evaluated_depsgraph_get()
for ob in coll.objects:
    if ob.type != "MESH": continue
    e = ob.evaluated_get(dg); me = e.to_mesh()
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    M = np.array(e.matrix_world); Vw = V @ M[:3, :3].T + M[:3, 3]
    d = np.linalg.norm(Vw - np.array(pw), axis=1).min()
    if d < 0.02: print("NEAR", ob.name, round(float(d), 4), len(V))
    e.to_mesh_clear()
