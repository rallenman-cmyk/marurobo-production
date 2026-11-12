# 第4章の電車の場面（D1・D8）：第2章で時間が止まった車内（1944コマ目）をそのまま組み、カメラだけを置いて静止画を描く
#   D1（2:41〜2:45）主人公と隣の人の二人（K6 と同じ向き）。「では、隣の人のイヤホンが、近くにあったら？」
#   D8（4:24〜4:37）車両の端の高い所から全体（K4 と同じ向き）。組ごとに別の印を頭の上に出す（印は絵の上に重ねる：頭の位置を書き出す）
# 使い方: blender -b --factory-startup --python ch04_train.py -- --out DIR [--res W H] [--samples N] [--engine eevee|workbench]
import bpy, sys, os, math, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); HUMAN = os.path.abspath(os.path.join(HERE, "..", "human"))
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/ch04_train"); ap.add_argument("--res", nargs=2, type=int, default=[1920, 1080]); ap.add_argument("--samples", type=int, default=32)
ap.add_argument("--engine", default="eevee"); ap.add_argument("--only", default="", help="描くカットだけ（例 D8）"); ap.add_argument("--norender", type=int, default=0, help="1＝絵は描かず、頭とイヤホンの位置だけ書き出す")
A4 = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A4.out, exist_ok=True)
sys.argv = [sys.argv[0], "--", "--out", os.path.join(A4.out, "opening_build"), "--dry", "2", "--frames", "2:2", "--res", str(A4.res[0]), str(A4.res[1]),
            "--samples", str(A4.samples), "--blur", "0", "--engine", A4.engine, "--seq", "ch0102_seq.py", "--crowd", "1", "--world_len", "1450", "--acts", "1"]
G = {"__file__": os.path.join(HUMAN, "opening_phys.py"), "__name__": "__main__"}
exec(compile(open(G["__file__"], encoding="utf-8").read(), G["__file__"], "exec"), G)
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
scene = bpy.context.scene; O = bpy.data.objects
N_OPEN = int(round(G["T_END"] * 24)); scene.frame_set(N_OPEN); bpy.context.view_layer.update()
P = G["P"]
def head_w(key):
    pr = P[key]; rg = pr["rig"]; return pr["arm"].matrix_world @ Vector(tuple(float(v) for v in rg.posed_point("head", pr["hc"])))
# 止まった姿の頭の位置（1944コマ目の骨の姿勢から）
HEADS = {}
for k, pr in P.items():
    arm = pr["arm"]; pb = arm.pose.bones["head"]
    HEADS[k] = arm.matrix_world @ (pb.matrix @ (pb.bone.matrix_local.inverted() @ Vector(tuple(float(v) for v in pr["hc"]))))
BUDS = {}                                                              # 耳のイヤホン（左右）：頭の骨の休みの姿勢での位置（iconfig と同じ式）
for k in ("H", "P1"):
    pr = P[k]; arm = pr["arm"]; pb = arm.pose.bones["head"]; Rh = pr.get("Rh", 0.140)
    for sd, sx in (("L", 1), ("R", -1)):
        p_rest = Vector(tuple(float(v) for v in (np.asarray(pr["hc"]) + np.array([sx * Rh * 0.99 + sx * 0.004, 0.010, -0.010]))))
        BUDS[k + "_" + sd] = arm.matrix_world @ (pb.matrix @ (pb.bone.matrix_local.inverted() @ p_rest))
cam_d = bpy.data.cameras.new("Ch04 camera"); cam = O.new("Ch04 camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
scene.timeline_markers.clear()
cam_d.sensor_width = 36; cam_d.clip_start = 0.02; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
mid = (HEADS["H"] + HEADS["P1"]) * 0.5
SHOTS = {"D1": (mid + Vector((-1.62, 0.02, -0.04)), mid + Vector((0.0, 0.0, -0.18)), 30.0, mid),
         "D8": (Vector((-0.66, -2.92, 2.02)), Vector((-1.10, 5.6, 0.72)), 17.0, Vector((-0.9, 0.4, 1.0)))}   # 主人公の側の端から：手前に主人公と隣の人
jpath = os.path.join(A4.out, "ch04_heads.json")
out = json.load(open(jpath)) if os.path.exists(jpath) else {}
for nm, (p, tg, lens, fp) in SHOTS.items():
    if A4.only and nm not in A4.only.split(","): continue
    cam.location = p; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (tg - p).to_track_quat("-Z", "Y"); cam_d.lens = lens
    cam_d.dof.focus_distance = (fp - p).length; bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(A4.out, "%s.png" % nm); scene.render.image_settings.file_format = "PNG"
    if not A4.norender: bpy.ops.render.render(write_still=True)
    bproj = {}
    for k, bw in BUDS.items():
        v = world_to_camera_view(scene, cam, bw)
        if v.z > 0: bproj[k] = [round(v.x, 4), round(1.0 - v.y, 4), round(v.z, 3)]
    out[nm + "_buds"] = bproj
    proj = {}
    for k, hw in HEADS.items():
        v = world_to_camera_view(scene, cam, hw + Vector((0, 0, 0.24)))          # 頭の上 24cm（印を出す所）
        if 0.0 <= v.x <= 1.0 and 0.0 <= v.y <= 1.0 and v.z > 0: proj[k] = [round(v.x, 4), round(1.0 - v.y, 4), round(v.z, 3)]
    out[nm] = proj; print("SHOT", nm, len(proj), "heads in view", flush=True)
json.dump(out, open(jpath, "w"), indent=0)
print("CH04 TRAIN DONE", flush=True)
