# 作った人物を、6面図と同じ縮尺・位置合わせの正投影で5方向から描き、シートと並べる（顔・髪・目・眉・口ごと確認）
# 使い方: blender -b --factory-startup --python sheet_turn.py -- M1 OUTDIR
import bpy, sys, os, math, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix
import hchar, hrig, ref_people
from hbuild import srgb
k, outdir = sys.argv[sys.argv.index("--") + 1:][:2]; os.makedirs(outdir, exist_ok=True)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene; t0 = time.time()
SH = os.path.join(HERE, "..", "..", "sheets")
cfg = dict(ref_people.PEOPLE[k]); cfg["sheet"] = k
if "--proj" in sys.argv: cfg["projtex"] = True; cfg["proj_mode"] = "flat"
coll = bpy.data.collections.new("P"); sc.collection.children.link(coll)
ch = hchar.make_character("T" + k, cfg, coll, S=1.0)
hc = np.asarray(ch["hc"]); print("BUILT", round(time.time() - t0, 1), flush=True)
lay = json.load(open(os.path.join(SH, "layout.json")))[k]["panels"]
spec = json.load(open(os.path.join(SH, f"spec_{k}.json"))); S = spec["reg"]["S"]; v0 = spec["reg"]["v0"]
reg_u = json.load(open(os.path.join(SH, f"reg_{k}.json")))
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb("#D9D9DB"), 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.35
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
ld = bpy.data.lights.new("K", "SUN"); ld.energy = 2.8; ld.angle = math.radians(20); key = bpy.data.objects.new("K", ld); sc.collection.objects.link(key)
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 16
sc.view_settings.view_transform = "Standard" if "--proj" in sys.argv else "AgX"
if "--proj" not in sys.argv: sc.view_settings.look = "AgX - Base Contrast"
NAMES = ["front", "left45", "left", "back", "right"]; ANG = [0, 45, 90, 180, 270]
for i, (nm, a) in enumerate(zip(NAMES, ANG)):
    pw = lay[i][1] - lay[i][0]; ph = 500
    sc.render.resolution_x, sc.render.resolution_y = pw, ph; cd.ortho_scale = max(pw, ph) / S
    ar = math.radians(a); cdir = Vector((math.sin(ar), -math.cos(ar), 0.0)); right = Vector((math.cos(ar), math.sin(ar), 0.0))
    uc = pw / 2.0; vc = 60 + ph / 2.0
    off_r = (uc - reg_u[nm]) / S; zc = (v0 - vc) / S
    center = Vector(tuple(hc)) + right * off_r + Vector((0, 0, zc))
    cam.location = center + cdir * 1.5
    zc_ = cdir; xc_ = right; yc_ = zc_.cross(xc_)
    cam.matrix_world = Matrix(((xc_.x, yc_.x, zc_.x, cam.location.x), (xc_.y, yc_.y, zc_.y, cam.location.y), (xc_.z, yc_.z, zc_.z, cam.location.z), (0, 0, 0, 1)))
    ldir = (cdir + Vector((0, 0, 0.9)) + right * -0.4).normalized()
    key.rotation_euler = ldir.to_track_quat("Z", "Y").to_euler()
    sc.render.filepath = os.path.join(outdir, f"{k}_{nm}.png"); bpy.ops.render.render(write_still=True)
print("DONE", round(time.time() - t0, 1), flush=True)
