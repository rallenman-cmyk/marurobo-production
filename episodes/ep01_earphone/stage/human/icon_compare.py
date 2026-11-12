# 線画アイコン風の人を作り、座ってスマホを見る姿（上半身と全身）を撮る
# 使い方: blender -b --factory-startup --python icon_compare.py -- OUT VARIANT [RES]
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix
import iconfig, hchar, hrig, people
from hbuild import srgb
argv = sys.argv[sys.argv.index("--") + 1:]
out, var = argv[0], argv[1]; res = int(argv[2]) if len(argv) > 2 else 560
OUTFIT = None if var == "plain" else var
os.makedirs(out, exist_ok=True)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene; t0 = time.time()
C = iconfig.make_icon("Hero", iconfig.HERO_COLORS if OUTFIT else dict(top=iconfig.MUTED_TOPS[0], pants=iconfig.MUTED_PANTS[0]), outfit=OUTFIT, S=1.0)
rig = hrig.Rig(C["arm"])
person = dict(C, rig=rig, kind="phone_left", phase=0.0, neck=-2.0, headx=-4.0, headz=0.0, phone_c=(0.035, -0.320, 0.985), blink_T=99.0)
PC, PR = people.base_pose(person, 0.3)
for n in rig.names:
    pb = C["arm"].pose.bones[n]; pb.rotation_quaternion = rig.q[n]; pb.location = rig.loc[n]
ph, so = hchar.make_phone("Phone", None, os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens", "music.png"), S=1.0)
ph.matrix_world = hrig.to_mat4(PR, PC)
print("BUILD", var, round(time.time() - t0, 1), flush=True)
def box(name, lo, hi, hexc, outline=True):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=[h - l for l, h in zip(lo, hi)], verts=bm.verts); bmesh.ops.translate(bm, vec=[(l + h) / 2 for l, h in zip(lo, hi)], verts=bm.verts)
    bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    me.materials.append(iconfig.toon_mat(hexc, 0.90)); bv = ob.modifiers.new("b", "BEVEL"); bv.width = 0.02; bv.segments = 3
    return ob
box("Seat", (-0.7, -0.248, 0.30), (0.7, 0.197, 0.46), "#9CCFC8"); box("Back", (-0.7, 0.197, 0.30), (0.7, 0.29, 0.95), "#9CCFC8")
box("Floor", (-3, -3, -0.02), (3, 3, 0.0), "#E4E4E4", False); box("Wall", (-3, 0.6, 0), (3, 0.62, 3), "#EFEFEF", False)
def area(name, e, loc, size, tgt=(0, -0.1, 0.95)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = size
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(tgt)).to_track_quat("Z", "Y").to_euler(); return o
area("Key", 320, (1.3, -1.9, 2.1), 1.4); area("Fill", 60, (-1.9, -1.4, 1.2), 2.2)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb("#DADADA"), 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 16; sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = sc.render.resolution_y = res
# 線：Freestyle（画面上で一定の太さ。体どうしが重なる所にも線が出る）
iconfig.freestyle(sc, bpy.context.view_layer, 4.6 * res / 480)
rig.fk(); hcw = np.array(rig.posed_point("head", C["hc"]))
VIEWS = {"upper": ((hcw[0] + 0.55, hcw[1] - 1.15, hcw[2] - 0.08), (hcw[0], hcw[1] - 0.10, hcw[2] - 0.24), 50),
         "full": ((1.15, -1.85, 1.12), (0.0, -0.12, 0.83), 42)}
for v, (pos, tgt, lens) in VIEWS.items():
    cd.lens = lens; cam.location = Vector(pos); cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, f"{var}_{v}.png"); bpy.ops.render.render(write_still=True)
    print("SHOT", var, v, round(time.time() - t0, 1), flush=True)
