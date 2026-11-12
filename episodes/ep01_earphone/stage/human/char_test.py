# 主人公を1人組み立て、スマホを持って座らせて撮る（形と姿勢の確認）
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
from mathutils import Vector, Matrix
import hchar, hrig, pose_lib
from hbuild import srgb
argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]; views = argv[1].split(",") if len(argv) > 1 else ["q34", "side", "hands"]
res = int(argv[2]) if len(argv) > 2 else 640
os.makedirs(out, exist_ok=True)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene; t0 = time.time()
C = hchar.make_character("Hero", hchar.HERO, S=1.0)
arm = C["arm"]; rig = hrig.Rig(arm); J = C["J"]; hc = C["hc"]; hf = C["hf"]
print("BUILD", round(time.time() - t0, 1), "s")
# 回転の向きの確認（+X で前へ曲がるか）
rig.fk(); h0 = rig.tail_pos("head"); rig.rot("head", x=20); rig.fk(); h1 = rig.tail_pos("head"); rig.reset(); rig.fk()
print("SIGN head +x moves tail by", np.round(h1 - h0, 3))
# ---- 姿勢：スマホを見る
rig.rot("spine", x=4); rig.rot("chest", x=5); rig.rot("neck", x=7); rig.rot("head", x=12)
rig.fk()
eye_mid = (rig.head_pos("eye.L") + rig.head_pos("eye.R")) / 2
PC, PR = pose_lib.phone_frame(J, eye_mid)
wl, Rl = pose_lib.left_grip(PC, PR)
rig.ik2("upper_arm.L", "forearm.L", wl, pole=(0.7, 0.4, -1.0), end="hand.L", end_R=Rl)
pose_lib.curl(rig, "L", 38, 70, 38, thumb=(6, 8, 6))
wr, Rr = pose_lib.thigh_rest(J, "R", -1)
rig.ik2("upper_arm.R", "forearm.R", wr, pole=(-0.6, 0.5, -1.0), end="hand.R", end_R=Rr)
pose_lib.curl(rig, "R", 14, 22, 12, thumb=(6, 6, 4), spread=2)
rig.fk()
scr = PC + PR[:, 2] * 0.006
for sd in ("L", "R"): rig.look("eye." + sd, scr)
rig.fk()
for n in rig.names:
    pb = arm.pose.bones[n]; pb.rotation_quaternion = rig.q[n]
bpy.context.view_layer.update()
ph, scr_ob = hchar.make_phone("Hero phone")
ph.matrix_world = hrig.to_mat4(PR, PC)
print("POSE ok; phone at", np.round(PC, 3))
# ---- 座席・床
def box(name, lo, hi, hexc, rough=0.6):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=[h - l for l, h in zip(lo, hi)], verts=bm.verts); bmesh.ops.translate(bm, vec=[(l + h) / 2 for l, h in zip(lo, hi)], verts=bm.verts)
    bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*srgb(hexc), 1); b.inputs["Roughness"].default_value = rough
    me.materials.append(m); return ob
box("Seat", (-0.6, -0.248, 0.30), (0.6, 0.197, 0.46), "#3E6E68"); box("Back", (-0.6, 0.197, 0.30), (0.6, 0.29, 0.93), "#3E6E68")
box("Floor", (-2, -2, -0.02), (2, 2, 0.0), "#8B8F92", 0.8)
# ---- 光とカメラ
def area(name, e, loc, size, col="#FFF4E8", tgt=(0, -0.1, 0.9)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = size; ld.color = srgb(col)
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(tgt)).to_track_quat("Z", "Y").to_euler(); return o
area("Key", 260, (1.4, -1.8, 2.0), 1.2); area("Fill", 70, (-1.8, -1.2, 1.0), 2.0, "#E8F0FF"); area("Rim", 160, (-0.8, 1.6, 2.0), 1.0)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.20, 0.22, 0.25, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 24; sc.view_settings.view_transform = "AgX"
sc.render.resolution_x = sc.render.resolution_y = res
VIEWS = {"q34": ((1.25, -1.75, 1.25), (0.0, -0.12, 0.86), 45), "side": ((2.1, -0.15, 0.95), (0.0, -0.12, 0.80), 50),
         "hands": ((0.55, -0.95, 1.30), (0.02, -0.26, 0.86), 50), "face": ((0.35, -0.80, 1.20), (0.0, 0.00, 1.18), 70),
         "front": ((0.0, -2.2, 1.0), (0.0, -0.1, 0.80), 45),
         "pov": ((0.0, -0.05, 1.27), (0.035, -0.30, 0.93), 40), "lside": ((0.75, -0.40, 1.00), (0.03, -0.29, 0.93), 45)}
for v in views:
    pos, tgt, lens = VIEWS[v]; cd.lens = lens
    cam.location = Vector(pos); cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, f"char_{v}.png"); bpy.ops.render.render(write_still=True)
    print("SHOT", v, round(time.time() - t0, 1), "s")
