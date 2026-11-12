# 参考画像の作風で、電車の中の3人（＋奥の2人）を同じ構図で撮るサンプル
# 使い方: blender -b maru_opening.blend --python facet_sample.py -- --variant A|B --out DIR [--res W H] [--samples N]
import bpy, sys, os, math, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix
import hchar, hrig, people, facet_people

ap = argparse.ArgumentParser(); ap.add_argument("--variant", default="A"); ap.add_argument("--out", default="/tmp/fs")
ap.add_argument("--res", nargs=2, type=int, default=[1280, 720]); ap.add_argument("--samples", type=int, default=24)
ap.add_argument("--close", type=int, default=0); ap.add_argument("--only", default="")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []); os.makedirs(A.out, exist_ok=True)
scene = bpy.context.scene; O = bpy.data.objects; t0 = time.time(); S = 1.65
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
# 場面の準備（Codex版の乗客・ロボ・ボタンなどを隠し、光を消す）
for ob in list(O):
    if ob.animation_data:
        loc, rot, scl, hr = ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy(), ob.hide_render
        ob.animation_data_clear(); ob.location, ob.rotation_euler, ob.scale, ob.hide_render = loc, rot, scl, hr
for n in ["PHONE / opening", "Phone cover hinge", "Screw", "SCREWDRIVER", "Pause button", "Pause button base", "Pause pulse"]:
    if n in O:
        for ob in hier(O[n]): ob.hide_render = True
O["MARU / pause"].scale = (0, 0, 0)
for ob in list(O):
    if ob.type == "LIGHT": O.remove(ob, do_unlink=True)
for ob in O:
    if ob.name.startswith("Window") and ob.type == "MESH": ob.visible_shadow = False
OLD = {}
for n in people.PEOPLE:
    if n in O:
        OLD[n] = (O[n].matrix_world.translation.copy(), O[n].matrix_world.to_euler().z)
        for ob in hier(O[n]): ob.hide_render = True
coll = bpy.data.collections.new("PEOPLE facet"); scene.collection.children.link(coll)
seat_of = {"A": "PASSENGER 00", "B": "PASSENGER 00", "P01": "PASSENGER 01", "P02": "PASSENGER 02", "P03": "PASSENGER 03", "P04": "PASSENGER 04"}
P = {}
KEYS = [k for k in (A.variant, "P01", "P02", "P03", "P04") if not A.only or k in A.only.split(",")]
for key in KEYS:
    cfg = dict(facet_people.PEOPLE[key]); seat = seat_of[key]
    ch = hchar.make_character(f"F{key}", cfg, coll, S=S)
    loc, rz = OLD[seat]; ch["arm"].location = loc; ch["arm"].rotation_euler = (0, 0, rz)
    rig = hrig.Rig(ch["arm"])
    person = dict(ch, rig=rig, kind=cfg["pose"], phase=hash(key) % 7 * 0.5, headz=0.0, headx=0.0, blink_T=99.0)
    C, R = people.base_pose(person, 0.4)
    for nme in rig.names:
        pb = ch["arm"].pose.bones[nme]; pb.rotation_quaternion = rig.q[nme]; pb.location = rig.loc[nme]
    ph, so = hchar.make_phone(f"{key} phone", coll, os.path.join(HERE, "screens", cfg["screen"]), S=S)
    Mw = ch["arm"].matrix_world @ hrig.to_mat4(R, C)
    Mb = ch["arm"].matrix_world @ rig.M["hand.L"] @ Matrix.Translation((0, rig.length["hand.L"], 0))
    ph.parent = ch["arm"]; ph.parent_type = "BONE"; ph.parent_bone = "hand.L"; ph.matrix_parent_inverse = Matrix.Identity(4); ph.matrix_basis = Mb.inverted() @ Mw
    P[key] = person
    print("PERSON", key, round(time.time() - t0, 1), flush=True)
# 光：正面左上から暖かい主光（顔を照らす）＋後ろの窓からの日差し（髪と肩の縁を光らせる）＋天井の弱い明かり
def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = bpy.data.objects.new(name, ld); scene.collection.objects.link(ob); ob.location = loc; return ob
def aim_l(ob, tgt): ob.rotation_euler = (ob.location - Vector(tgt)).to_track_quat("Z", "Y").to_euler()
sun = light("Window sun (rim)", "SUN", 5.0, kelvin(3800)); sun.data.angle = math.radians(2.0)
sun.rotation_euler = Vector((0.85, 0.15, 0.45)).to_track_quat("Z", "Y").to_euler()
key = light("Key", "AREA", 420.0, kelvin(4200), (-0.05, -3.9, 2.45)); key.data.size = 2.4; aim_l(key, (1.55, -3.2, 1.75))
ceil = light("Ceiling", "AREA", 140.0, kelvin(5200), (0, 0, 2.85)); ceil.data.shape = "RECTANGLE"; ceil.data.size, ceil.data.size_y = 1.2, 13.0
w = scene.world or bpy.data.worlds.new("World"); scene.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
bg = nt.nodes.new("ShaderNodeBackground"); wo = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(bg.outputs[0], wo.inputs["Surface"])
bg.inputs[0].default_value = (0.62, 0.72, 0.86, 1); bg.inputs[1].default_value = 0.30
# カメラ：通路側から、右の座席の列を斜めに見る（参考画像と同じ並び：手前右に主人公、奥へ2人）
cd = bpy.data.cameras.new("Ref cam"); cam = bpy.data.objects.new("Ref cam", cd); scene.collection.objects.link(cam); scene.camera = cam
bpy.context.view_layer.update()
hero = P[A.variant]; hero["rig"].fk(); hp = hero["arm"].matrix_world @ Vector(tuple(hero["rig"].posed_point("head", hero["hc"])))
if A.close:   # 顔のアップ（顔立ちの確認用）
    cam.location = hp + Vector((-0.95, -0.55, 0.02)); tgt = hp + Vector((0.0, 0.02, -0.06)); cd.lens = 60
else:
    cam.location = Vector((0.80, -5.62, 1.98)); tgt = Vector((1.70, -2.35, 1.66)); cd.lens = 30
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler(); cd.sensor_width = 36
bpy.context.view_layer.update()
_hd = hero["objs"]["head"]; _dg = bpy.context.evaluated_depsgraph_get(); _ev = _hd.evaluated_get(_dg); _me = _ev.to_mesh()
_pts = np.array([(_hd.matrix_world @ v.co)[:] for v in _me.vertices]); _ev.to_mesh_clear()
print("DBG hp", tuple(round(x, 3) for x in hp), "head bbox", _pts.min(0).round(3), _pts.max(0).round(3), "cam", tuple(round(x, 3) for x in cam.location), flush=True)
cd.dof.use_dof = True; cd.dof.focus_distance = (hp - cam.location).length; cd.dof.aperture_fstop = 4.0
ee = scene.eevee; scene.render.engine = "BLENDER_EEVEE_NEXT"; ee.taa_render_samples = A.samples; ee.use_shadows = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"; scene.view_settings.exposure = -0.15
scene.render.resolution_x, scene.render.resolution_y = A.res
scene.render.filepath = os.path.join(A.out, f"facet_{A.variant}{'_close' if A.close else ''}.png"); bpy.ops.render.render(write_still=True)
print("STILL", scene.render.filepath, round(time.time() - t0, 1), flush=True)
