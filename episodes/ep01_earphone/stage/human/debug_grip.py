import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
from mathutils import Vector
import hchar, hrig, pose_lib
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
C = hchar.make_character("Hero", hchar.HERO, S=1.0); arm = C["arm"]; rig = hrig.Rig(arm); J = C["J"]
rig.rot("spine", x=4); rig.rot("chest", x=5); rig.rot("neck", x=7); rig.rot("head", x=12); rig.fk()
eye_mid = (rig.head_pos("eye.L") + rig.head_pos("eye.R")) / 2
PC, PR = pose_lib.phone_frame(J, eye_mid)
wl, Rl = pose_lib.left_grip(PC, PR)
E = rig.ik2("upper_arm.L", "forearm.L", wl, pole=(0.7, 0.4, -1.0), end="hand.L", end_R=Rl)
rig.fk()
for n in rig.names: arm.pose.bones[n].rotation_quaternion = rig.q[n]
bpy.context.view_layer.update()
pb = arm.pose.bones["hand.L"]
print("DBG target wrist", np.round(wl, 3), "fk wrist", np.round(rig.head_pos("hand.L"), 3), "blender wrist", np.round(np.array(pb.head), 3))
Mh = rig.M["hand.L"]; Rh = hrig.m3(Mh)
print("DBG hand Z (dorsal)", np.round(Rh[:, 2], 2), "want", np.round(Rl[:, 2], 2), " Y", np.round(Rh[:, 1], 2), "want", np.round(Rl[:, 1], 2))
print("DBG blender hand matrix Z", np.round(np.array(pb.matrix.to_3x3().col[2]), 2))
# 変形後の手の網目の中心
ob = C["objs"]["hand.L"]; dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh()
V = np.array([v.co[:] for v in me.vertices]); ev.to_mesh_clear()
print("DBG hand mesh centroid", np.round(V.mean(0), 3), "palm target", np.round(PC - PR[:, 0] * 0.016 - PR[:, 1] * 0.030 - PR[:, 2] * 0.0172, 3))
print("DBG phone C", np.round(PC, 3), "n", np.round(PR[:, 2], 2), "x", np.round(PR[:, 0], 2), "long", np.round(PR[:, 1], 2))
# 休み姿勢の手の網目は骨の近くにあるか
rest_V = C["objs"]["hand.L"].data.vertices
RV = np.array([v.co[:] for v in rest_V]); print("DBG rest hand centroid", np.round(RV.mean(0), 3), "rest wrist", np.round(J["wrist.L"], 3))
b = arm.data.bones["hand.L"]; print("DBG rest hand bone Z", np.round(np.array(b.matrix_local.to_3x3().col[2]), 2), "Y", np.round(np.array(b.matrix_local.to_3x3().col[1]), 2))
