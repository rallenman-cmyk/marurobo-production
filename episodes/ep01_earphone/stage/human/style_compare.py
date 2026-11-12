# 作風ごとに主人公を作り、全身（座ってスマホ）と顔のアップを撮る
# 使い方: blender -b --factory-startup --python style_compare.py -- OUT STYLE [RES]
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix
import hchar, hrig, people, styles, motion
from hbuild import srgb
argv = sys.argv[sys.argv.index("--") + 1:]
out, style = argv[0], argv[1]; res = int(argv[2]) if len(argv) > 2 else 640
os.makedirs(out, exist_ok=True)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene; t0 = time.time()
cfg = dict(styles.STYLES[style]["cfg"])
C = hchar.make_character("Hero", cfg, S=1.0)
rig = hrig.Rig(C["arm"])
person = dict(C, rig=rig, kind="phone_left", phase=0.0, neck=-4.0, headx=-6.0, headz=0.0, phone_c=(0.035, -0.305, 0.975), blink_T=99.0)
PC, PR = people.base_pose(person, 0.3)
# 比べやすいよう、目はスマホから少し上げてカメラの近くを見る（まぶたの追従は控えめ）
rig.fk(); hc0 = np.array(rig.posed_point("head", C["hc"])); k = C["P"]["hs"] / 1.12
look_at = hc0 + np.array([0.26, -0.80, -0.16]) * k
for sd in ("L", "R"):
    yaw, pitch = rig.look("eye." + sd, look_at)
    rig.rot("lid_up." + sd, x=0.30 * pitch); rig.rot("lid_lo." + sd, x=0.15 * pitch)
rig.fk()
for n in rig.names:
    pb = C["arm"].pose.bones[n]; pb.rotation_quaternion = rig.q[n]; pb.location = rig.loc[n]
C["mouth"].data.shape_keys.key_blocks["smile"].value = 0.45
ph, so = hchar.make_phone("Phone", None, os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens", "music.png"), S=1.0, style=cfg.get("style", "real"))
ph.matrix_world = hrig.to_mat4(PR, PC)
print("BUILD", style, round(time.time() - t0, 1), flush=True)
def box(name, lo, hi, hexc, rough=0.6):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=[h - l for l, h in zip(lo, hi)], verts=bm.verts); bmesh.ops.translate(bm, vec=[(l + h) / 2 for l, h in zip(lo, hi)], verts=bm.verts)
    bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*srgb(hexc), 1); b.inputs["Roughness"].default_value = rough
    me.materials.append(m); bv = ob.modifiers.new("b", "BEVEL"); bv.width = 0.02; bv.segments = 3; return ob
box("Seat", (-0.7, -0.248, 0.30), (0.7, 0.197, 0.46), "#3F7F78"); box("Back", (-0.7, 0.197, 0.30), (0.7, 0.29, 0.95), "#3F7F78")
box("Floor", (-3, -3, -0.02), (3, 3, 0.0), "#9AA0A6", 0.8); box("Wall", (-3, 0.6, 0), (3, 0.62, 3), "#C9D3DB", 0.9)
def area(name, e, loc, size, col="#FFF4E8", tgt=(0, -0.1, 0.95)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = size; ld.color = srgb(col)
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(loc) - Vector(tgt)).to_track_quat("Z", "Y").to_euler(); return o
area("Key", 300, (1.3, -1.9, 2.1), 1.4); area("Fill", 90, (-1.9, -1.4, 1.2), 2.2, "#E6EEFF"); area("Rim", 170, (-0.9, 1.4, 2.2), 1.0)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb("#AFC2D2"), 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 24; sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.resolution_x = sc.render.resolution_y = res
rig.fk(); hcw = np.array(rig.posed_point("head", C["hc"]))
kk = C["P"]["hs"] / 1.12 * 1.12
VIEWS = {"face": ((hcw[0] + 0.30 * kk, hcw[1] - 0.80 * kk, hcw[2] - 0.02), (hcw[0], hcw[1] - 0.02, hcw[2] - 0.03), 58),
         "full": ((1.15, -1.85, 1.12), (0.0, -0.12, 0.83), 42)}
for v, (pos, tgt, lens) in VIEWS.items():
    cd.lens = lens; cam.location = Vector(pos); cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, f"{style}_{v}.png"); bpy.ops.render.render(write_still=True)
    print("SHOT", style, v, round(time.time() - t0, 1), flush=True)
