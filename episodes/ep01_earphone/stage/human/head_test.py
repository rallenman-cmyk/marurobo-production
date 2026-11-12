# 顔と髪の確認用：1人を作って、参考と同じ向き（左前から）・正面・横から頭を撮る
# 使い方: blender -b --factory-startup --python head_test.py -- --who M1 --out DIR [--views ref,front,side] [--res 640 640]
import bpy, sys, os, math, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix
import hchar, hrig, people, ref_people
from hbuild import srgb

ap = argparse.ArgumentParser(); ap.add_argument("--who", default="M1"); ap.add_argument("--out", default="/tmp/ht")
ap.add_argument("--views", default="ref,front,side"); ap.add_argument("--res", nargs=2, type=int, default=[640, 640])
ap.add_argument("--samples", type=int, default=16); ap.add_argument("--pose", type=int, default=1)
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []); os.makedirs(A.out, exist_ok=True)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene; O = bpy.data.objects; t0 = time.time()

cfg = dict(ref_people.PEOPLE[A.who])
coll = bpy.data.collections.new("P"); sc.collection.children.link(coll)
ch = hchar.make_character("T" + A.who, cfg, coll, S=1.0)
rig = hrig.Rig(ch["arm"])
person = dict(ch, rig=rig, kind=cfg["pose"], phase=0.0, headz=0.0, headx=0.0, blink_T=99.0)
if A.pose:
    C, R = people.base_pose(person, 0.4)
    for nme in rig.names:
        pb = ch["arm"].pose.bones[nme]; pb.rotation_quaternion = rig.q[nme]; pb.location = rig.loc[nme]
bpy.context.view_layer.update(); rig.fk()
print("BUILT", round(time.time() - t0, 1), flush=True)
hp = ch["arm"].matrix_world @ Vector(tuple(rig.posed_point("head", ch["hc"])))
Mh = ch["arm"].matrix_world @ rig.M["head"]
fwd = -(Mh.to_3x3() @ Vector((0, 0, 1))).normalized() if False else None


def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = O.new(name, ld); sc.collection.objects.link(ob); ob.location = loc; return ob
def aim(ob, tgt, axis="-Z"): ob.rotation_euler = (Vector(tgt) - ob.location).to_track_quat(axis, "Y").to_euler()
# 人物は −Y を向いている（人物の左＝＋X）。参考：窓（人物の後ろ＝＋Y）から暖かい日差し、手前の左前から柔らかい光
sun = light("Sun", "SUN", 4.0, kelvin(3800)); sun.data.angle = math.radians(2)
sun.rotation_euler = Vector((0.55, 0.85, 0.65)).to_track_quat("Z", "Y").to_euler()
key = light("Key", "AREA", 60.0, kelvin(4600), tuple(hp + Vector((0.9, -1.0, 0.45)))); key.data.size = 1.2; aim(key, hp)
fill = light("Fill", "AREA", 25.0, kelvin(7000), tuple(hp + Vector((-1.0, -0.8, 0.1)))); fill.data.size = 1.5; aim(fill, hp)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb("#BCD3E8"), 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.35

cd = bpy.data.cameras.new("Cam"); cam = O.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam; cd.lens = 85
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = A.samples
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.resolution_x, sc.render.resolution_y = A.res
VIEWS = {"ref": (62.0, -6.0, 0.62), "front": (0.0, 6.0, 0.66), "side": (90.0, 0.0, 0.66), "back": (150.0, 10.0, 0.70), "top": (30.0, 40.0, 0.70),
         "bust": (45.0, 4.0, 1.55, -0.20), "bustf": (0.0, 4.0, 1.55, -0.20)}
for v in A.views.split(","):
    az, el, dist = VIEWS[v][:3]; dz = VIEWS[v][3] if len(VIEWS[v]) > 3 else 0.0
    d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    tgt = hp + Vector((0, 0, -0.012 + dz))
    cam.location = tgt + d * dist; aim(cam, tgt)
    sc.render.filepath = os.path.join(A.out, f"{A.who}_{v}.png"); bpy.ops.render.render(write_still=True)
    print("VIEW", v, round(time.time() - t0, 1), flush=True)
