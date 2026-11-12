# 冒頭（第1〜2章）の静止画3案。Codex版の電車の場面（maru_opening.blend）を流用
# 使い方: blender -b maru_opening.blend --python opening_stills.py -- --mode layout|render --out DIR [--shots 1,2,3] [--res W H] [--samples N]
import bpy, bmesh, sys, os, math, argparse, random
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ap = argparse.ArgumentParser()
ap.add_argument("--mode", default="layout"); ap.add_argument("--out", default="/tmp/op")
ap.add_argument("--shots", default="1,2,3"); ap.add_argument("--res", nargs=2, type=int, default=[960, 540]); ap.add_argument("--samples", type=int, default=16)
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
scene = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials
scene.frame_set(1)

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
def link(ob): scene.collection.objects.link(ob); return ob
def mat_emit(name, rgb, s):
    m = M.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = s
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); return m

# 動きを1コマ目で止め、使わない物を隠す
for ob in list(O):
    if ob.animation_data:
        loc, rot, scl, hr = ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy(), ob.hide_render
        ob.animation_data_clear(); ob.location, ob.rotation_euler, ob.scale, ob.hide_render = loc, rot, scl, hr
for coll in (bpy.data.materials, bpy.data.lights, bpy.data.worlds):
    for idb in coll:
        if getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt = getattr(idb, "node_tree", None)
        if nt and nt.animation_data: nt.animation_data_clear()
for n in ["PHONE / opening", "Phone cover hinge", "Screw", "SCREWDRIVER"]:
    if n in O:
        for ob in hier(O[n]): ob.hide_render = True
for ob in list(O):
    if ob.type == "LIGHT": O.remove(ob, do_unlink=True)
for ob in O:  # 窓は光を通す（窓板は影を作らない）
    if ob.name.startswith("Window") and ob.type == "MESH": ob.visible_shadow = False
# スマホの画面は光る（画面は自分で光を出すので、実際にも明るく見える）
screen = mat_emit("Phone screen glow", (0.55, 0.78, 1.0), 2.2)
for ob in O:
    if ob.name.startswith("Phone display") and ob.type == "MESH":
        ob.data.materials.clear(); ob.data.materials.append(screen)

hero = O["PASSENGER 00"]; robot = O["MARU / pause"]; button = O["Pause button"]; pulse = O["Pause pulse"]
head = next(o for o in hier(hero) if o.name.startswith("Head"))
r_torso = next(o for o in hier(robot) if o.name.endswith("• torso"))
r_ant = next((o for o in hier(robot) if "antenna" in o.name and "•" in o.name), None)
robot.scale = (0, 0, 0)

# ほこり（光の筋の中で見える。時間が止まると空中で止まる）
mote_m = M.new("Dust mote"); mote_m.use_nodes = True; _b = mote_m.node_tree.nodes["Principled BSDF"]; _b.inputs["Base Color"].default_value = (1, 0.97, 0.9, 1); _b.inputs["Emission Color"].default_value = (1, 0.95, 0.85, 1); _b.inputs["Emission Strength"].default_value = 0.25
me = bpy.data.meshes.new("Dust"); bm = bmesh.new(); rnd = random.Random(11)
for i in range(160):
    c = Vector((0.14, -3.65, 0.9)) + Vector((rnd.uniform(-1.4, 1.4), rnd.uniform(-1.6, 1.6), rnd.uniform(-0.75, 1.2)))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rnd.uniform(0.004, 0.011), matrix=Matrix.Translation(c))
bm.to_mesh(me); bm.free(); dust = link(O.new("Dust", me)); me.materials.append(mote_m); dust.hide_render = True

# 光
def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = link(O.new(name, ld)); ob.location = loc; return ob
def aim(ob, target): ob.rotation_euler = (ob.location - Vector(target)).to_track_quat("Z", "Y").to_euler()
sun = light("Window sun", "SUN", 4.0, kelvin(5600)); sun.data.angle = math.radians(1.5)
sun.rotation_euler = Vector((-0.80, -0.30, 0.52)).to_track_quat("Z", "Y").to_euler()  # 左の窓から、やや前方・高さ約31°
ceil = light("Ceiling panels", "AREA", 900.0, kelvin(4500), (0, 0, 2.85)); ceil.data.shape = "RECTANGLE"; ceil.data.size, ceil.data.size_y = 1.2, 13.0
spot = light("Subject spot", "SPOT", 0.0, kelvin(3500)); spot.data.spot_size = math.radians(30); spot.data.spot_blend = 0.5; spot.data.shadow_soft_size = 0.25
glow = light("Button glow", "POINT", 0.0, (0.3, 0.95, 0.9), (0.14, -3.65, 0.35)); glow.data.shadow_soft_size = 0.3
w = scene.world or bpy.data.worlds.new("World"); scene.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
bg = nt.nodes.new("ShaderNodeBackground"); wo = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(bg.outputs[0], wo.inputs["Surface"])
bg.inputs[0].default_value = (0.62, 0.72, 0.85, 1); bg.inputs[1].default_value = 0.6
hz_me = bpy.data.meshes.new("Haze"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(hz_me); bm.free()
haze = link(O.new("Haze volume", hz_me)); haze.location = (0, 0, 1.5); haze.scale = (4.6, 15, 3.0)
hm = M.new("Haze"); hm.use_nodes = True; hnt = hm.node_tree; hnt.nodes.clear()
vs = hnt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Anisotropy"].default_value = 0.45; ho = hnt.nodes.new("ShaderNodeOutputMaterial")
hnt.links.new(vs.outputs[0], ho.inputs["Volume"]); hz_me.materials.append(hm); haze.hide_render = True

cam_d = bpy.data.cameras.new("Opening camera"); cam = link(O.new("Opening camera", cam_d)); scene.camera = cam; cam_d.sensor_width = 36
def set_cam(pos, tgt, lens, dof=None):
    cam.location = Vector(pos); cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler(); cam_d.lens = lens
    cam_d.dof.use_dof = dof is not None
    if dof: cam_d.dof.focus_distance, cam_d.dof.aperture_fstop = (Vector(dof[0]) - cam.location).length, dof[1]

def shot_A_wide():   # 1. 車両の全景（A案）
    set_cam((0.45, -7.25, 1.45), (-0.25, 3.0, 1.15), 24)
    sun.data.energy = 4.0; ceil.data.energy = 900.0; spot.data.energy = 0; glow.data.energy = 0
    scene.view_settings.exposure = 0.0; haze.hide_render = True; dust.hide_render = True
    for n in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
        if n in O: O[n].hide_render = True
def shot_C_dropout():  # 2. 音が途切れる瞬間（C案）
    for n in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
        if n in O: O[n].hide_render = True
    hp = head.matrix_world.translation.copy()
    buds = [o for o in hier(hero) if o.name.startswith("Earbud") and "stem" not in o.name]
    bud = max(buds, key=lambda o: o.matrix_world.translation.y).matrix_world.translation.copy()  # 右耳（+Y側）
    face = Vector((-1, 0, 0))  # 主人公は通路（-X）を向いて座っている
    mw = head.matrix_world.copy(); R = Matrix.Rotation(math.radians(-12), 4, face)
    head.matrix_world = Matrix.Translation(hp) @ R @ Matrix.Translation(-hp) @ mw  # 「あれ？」と首を傾げる
    # 表情：笑った口を隠し、小さな「o」の口にする。目はイヤホンの方（右）へ少し寄せる
    smile = next((o for o in hier(hero) if o.name.startswith("Smile")), None)
    if smile:
        dg = bpy.context.evaluated_depsgraph_get(); ev = smile.evaluated_get(dg); me_s = ev.to_mesh()
        pts = [smile.matrix_world @ v.co for v in me_s.vertices]; ev.to_mesh_clear()
        mp = sum(pts, Vector()) / max(len(pts), 1); smile.hide_render = True
        mouth_m = M.new("Mouth"); mouth_m.use_nodes = True; mouth_m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.05, 0.05, 1)
        mme = bpy.data.meshes.new("Mouth o"); tb = bmesh.new()
        outer = [tb.verts.new((0, 0.030 * math.cos(2 * math.pi * i / 32), 0.024 * math.sin(2 * math.pi * i / 32))) for i in range(32)]
        inner = [tb.verts.new((0, 0.017 * math.cos(2 * math.pi * i / 32), 0.012 * math.sin(2 * math.pi * i / 32))) for i in range(32)]
        for i in range(32): tb.faces.new((outer[i], outer[(i + 1) % 32], inner[(i + 1) % 32], inner[i]))
        tb.to_mesh(mme); tb.free(); mo = link(O.new("Mouth o", mme)); mo.data.materials.append(mouth_m)
        mo.location = mp + Vector((0, 0, 0.01)); mo.parent = head; mo.matrix_parent_inverse = head.matrix_world.inverted()
    for o in hier(hero):
        if o.name.startswith("Eye"): o.matrix_world = Matrix.Translation(Vector((0, 0.025, 0.01))) @ o.matrix_world
    set_cam((bud.x - 1.1, bud.y + 1.05, bud.z + 0.02), (hp.x - 0.12, hp.y + 0.2, hp.z - 0.22), 35, dof=(bud, 2.2))
    sun.data.energy = 0.6; ceil.data.energy = 120.0; scene.view_settings.exposure = -1.0
    spot.location = (hp.x - 0.6, hp.y - 0.4, 2.9); aim(spot, (hp.x, hp.y, hp.z - 0.3)); spot.data.energy = 260.0; spot.data.color = kelvin(7000)
    haze.hide_render = False; vs.inputs["Density"].default_value = 0.035; dust.hide_render = True
def shot_C_freeze():   # 3. 時間が止まる瞬間（C案）
    for n in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
        if n in O: O[n].hide_render = False
    b = button.location.copy(); robot.scale = (0.55, 0.55, 0.55)
    robot.location = (b.x, b.y, 0.14); robot.rotation_euler = (0, 0, math.radians(150))
    r_torso.rotation_euler.x = -math.radians(7)   # 着地の衝撃を受け止めて少し前へ
    if r_ant: r_ant.rotation_euler.x += math.radians(-16)  # アンテナは慣性で前へしなる
    button.location.z = 0.10                        # ボタンが押し込まれる
    pulse.scale = (2.6, 2.6, 2.6); pulse.location.z = 0.02
    pulse.data.materials.clear(); pulse.data.materials.append(mat_emit("Pulse glow", (0.3, 1.0, 0.9), 6.0))
    set_cam((b.x - 1.15, b.y - 1.55, 0.36), (b.x + 0.05, b.y + 0.3, 0.42), 24, dof=((b.x, b.y, 0.45), 2.8))
    sun.data.energy = 1.4; ceil.data.energy = 60.0; scene.view_settings.exposure = -1.2
    spot.location = (b.x - 0.3, b.y - 0.5, 2.9); aim(spot, (b.x, b.y, 0.3)); spot.data.energy = 220.0; spot.data.color = kelvin(3500)
    glow.data.energy = 60.0; haze.hide_render = False; vs.inputs["Density"].default_value = 0.05; dust.hide_render = False

ee = scene.eevee; scene.render.engine = "BLENDER_EEVEE_NEXT"; ee.taa_render_samples = A.samples; ee.use_shadows = True; ee.use_raytracing = False
for k, v in (("volumetric_start", 0.1), ("volumetric_end", 40.0), ("volumetric_samples", 64), ("use_volumetric_shadows", True)):
    if hasattr(ee, k): setattr(ee, k, v)
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "None"
scene.render.resolution_x, scene.render.resolution_y = A.res; scene.render.resolution_percentage = 100
SHOTS = {"1": shot_A_wide, "2": shot_C_dropout, "3": shot_C_freeze}
for key in A.shots.split(","):
    SHOTS[key](); bpy.context.view_layer.update()
    if A.mode == "layout":
        pts = {"hero_head": head.matrix_world.translation, "button": button.matrix_world.translation, "robot": robot.matrix_world.translation + Vector((0, 0, 0.4)),
               "p05": O["PASSENGER 05"].matrix_world.translation + Vector((0, 0, 1.7)), "far_end": Vector((0, 7.0, 1.5))}
        print(f"LAYOUT shot{key} " + " ".join(f"{k}=({c.x:.2f},{c.y:.2f},{c.z:.1f})" for k, c in ((k, world_to_camera_view(scene, cam, v)) for k, v in pts.items())))
        continue
    scene.render.filepath = os.path.join(A.out, f"opening_shot{key}.png"); bpy.ops.render.render(write_still=True); print("STILL", scene.render.filepath)
