# 第8章の天びんに乗るまるロボ（ch08_seesaw.py の動き）を、透明な背景で描く。2D の図（ch08_game.py）に重ねる
#   まるロボは story.blend のまるロボそのもの（ほかの物は消す）。正面から平行投影。光は斜め上の主光・反対側の弱い光・後ろからの輪郭光
#   世界の原点 ＝ 天びんの支点の中心。DIR/<A|B>/f_0001.png …（RGBA）と DIR/seesaw_<A|B>.json（時刻・傾き・図との対応）
# 使い方: blender -b story.blend --python ch08_seesaw_render.py -- --out DIR --scene A|B [--engine eevee|workbench] [--samples 16] [--scale 1.0] [--still 1,50,...] [--frames a:b]
import bpy, sys, os, math, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import numpy as np
from mathutils import Vector, Matrix
import marumotion as mm, marurig as mr
import ch08_seesaw as ss

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--scene", default="A"); ap.add_argument("--engine", default="eevee")
ap.add_argument("--samples", type=int, default=16); ap.add_argument("--scale", type=float, default=1.0)
ap.add_argument("--still", default=""); ap.add_argument("--frames", default="")
A = ap.parse_args(argv)
SC = A.scene; OUT = os.path.join(A.out, SC); os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene


def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out


# ---------------------------------------------------------------- まるロボだけ残す
maru = bpy.data.objects["Maru"]
mw = maru.matrix_world.copy(); maru.parent = None; maru.matrix_world = mw
keep = set(hier(maru))
for o in list(bpy.data.objects):
    if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
for o in keep:                                                   # どの集まりに入っていても描かれるように
    if scene.collection.objects.get(o.name) is None:
        try: scene.collection.objects.link(o)
        except RuntimeError: pass

# ---------------------------------------------------------------- 動き（板の座標で歩かせ、天びんの傾きで世界へ）
d = ss.build(SC)
rig = mr.MaruRig(maru)


class Baker6(mr.Baker):
    """材質の節の木はどれも同じ名前なので、物そのもので分ける（ch07_stage.py と同じ）"""
    def put(self, idb, path, index, frame, value):
        self.ch.setdefault((idb.as_pointer(), path, index), [idb, []])[1].append((frame, float(value)))

    def write(self, interp="LINEAR"):
        for (ptr, path, index), (idb, kv) in self.ch.items():
            ad = idb.animation_data or idb.animation_data_create()
            if ad.action is None: ad.action = bpy.data.actions.new(idb.name + " action")
            fc = ad.action.fcurves.find(path, index=index) or ad.action.fcurves.new(path, index=index)
            kv.sort(); fc.keyframe_points.add(len(kv))
            fc.keyframe_points.foreach_set("co", np.array(kv, np.float32).ravel())
            fc.keyframe_points.foreach_set("interpolation", np.full(len(kv), 1 if interp == "LINEAR" else 0, np.int32))
            fc.update()


bk = Baker6()
for i, fr in enumerate(d["frames"]): rig.apply(fr, i + 1, bk)
bk.write()

# ---------------------------------------------------------------- カメラ（正面からの平行投影）・光・背景（透明）
cam_d = bpy.data.cameras.new("Seesaw camera"); cam_d.type = "ORTHO"; cam_d.ortho_scale = ss.VIEW_W; cam_d.clip_start = 0.1; cam_d.clip_end = 60.0
cam = bpy.data.objects.new("Seesaw camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (ss.VIEW_XC, -20.0, ss.VIEW_ZC); cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)


def sun(name, toward, energy, color=(1.0, 1.0, 1.0), angle=10.0):
    ld = bpy.data.lights.new(name, "SUN"); ld.energy = energy; ld.color = color; ld.angle = math.radians(angle)
    o = bpy.data.objects.new(name, ld); scene.collection.objects.link(o)
    o.rotation_euler = Vector((0, 0, -1)).rotation_difference(Vector(toward).normalized()).to_euler(); return o


# 背景（図）が明るいので、ふちが明るくなる後ろからの光は弱く：体のふちは少し暗く落ちて、明るい図から浮く
sun("Key", (0.55, 0.75, -0.65), 3.6, (1.0, 0.97, 0.92))           # 左手前の上から
sun("Fill", (-0.8, 0.5, -0.2), 0.6, (0.90, 0.95, 1.0), 25.0)       # 右手前から弱く
sun("Rim", (0.2, -0.9, -0.5), 0.6, (1.0, 1.0, 1.0), 6.0)           # 後ろの上から（ごく弱く）
wd = bpy.data.worlds.new("Seesaw world"); scene.world = wd; wd.use_nodes = True
bgn = wd.node_tree.nodes.get("Background"); bgn.inputs[0].default_value = (0.80, 0.83, 0.86, 1.0); bgn.inputs[1].default_value = 0.32

r = scene.render
r.resolution_x = int(round(ss.RES_W * A.scale / 2)) * 2; r.resolution_y = int(round(ss.RES_H * A.scale / 2)) * 2; r.resolution_percentage = 100
r.fps = ss.FPS; r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.compression = 15
if A.engine == "workbench":
    r.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
    sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_shadows = False; sh.show_cavity = True; sh.cavity_type = "WORLD"
    scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"
else:
    r.engine = "BLENDER_EEVEE_NEXT"; ee = scene.eevee; ee.taa_render_samples = A.samples; ee.use_shadows = True
    try: ee.use_raytracing = False
    except Exception: pass
    scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
scene.frame_start, scene.frame_end = 1, d["n"]

# ---------------------------------------------------------------- 記録（2D の図に重ねるための対応）
ox = (0.0 - (ss.VIEW_XC - ss.VIEW_W / 2)) / ss.VIEW_W * ss.RES_W
oy = ((ss.VIEW_ZC + ss.VIEW_H / 2) - 0.0) / ss.VIEW_H * ss.RES_H
json.dump(dict(scene=SC, t0=d["t0"], fps=d["fps"], n=d["n"], beta=[round(b, 6) for b in d["beta"]], rpxm=ss.RPXM, origin=[ox, oy], res=[ss.RES_W, ss.RES_H],
               pxm=ss.PXM, arm_m=ss.ARM_M, thick_px=ss.THICK_PX, labels=[[round(d["t0"] + a, 3), round(d["t0"] + (b if b is not None else a), 3), t] for a, b, t in d["plan"].labels]),
          open(os.path.join(A.out, "seesaw_%s.json" % SC), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

if A.still:
    for k in [int(v) for v in A.still.split(",")]:
        scene.frame_set(k); r.filepath = os.path.join(OUT, "still_%04d.png" % k); bpy.ops.render.render(write_still=True)
        print("STILL", SC, k, flush=True)
else:
    f0, f1 = (1, d["n"]) if not A.frames else [int(v) for v in A.frames.split(":")]
    scene.frame_start, scene.frame_end = f0, min(f1, d["n"]); r.use_overwrite = False; r.use_placeholder = True
    r.filepath = os.path.join(OUT, "f_")
    bpy.ops.render.render(animation=True)
    print("SEESAW FRAMES", SC, f0, f1, flush=True)
