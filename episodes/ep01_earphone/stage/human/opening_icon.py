# 冒頭（第1〜2章）：線画アイコン風の人（点の目＋服の色分け、主人公だけ目印の服装）で描き直し
# 使い方: blender -b maru_opening.blend --python opening_v2.py -- --mode stills|anim|layout --out DIR
#         [--shots 1,2,3] [--res W H] [--samples N] [--frames A:B] [--blur 0|1]
import bpy, bmesh, sys, os, math, argparse, random, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import hchar, hrig, pose_lib, people, motion, hero_anim, iconfig

ap = argparse.ArgumentParser()
ap.add_argument("--mode", default="layout"); ap.add_argument("--out", default="/tmp/op2")
ap.add_argument("--shots", default="1,2,3"); ap.add_argument("--res", nargs=2, type=int, default=[960, 540])
ap.add_argument("--samples", type=int, default=16); ap.add_argument("--frames", default="1:192"); ap.add_argument("--blur", type=int, default=1)
ap.add_argument("--only-hero", type=int, default=0); ap.add_argument("--outfit", default="cap"); ap.add_argument("--video", type=int, default=0); ap.add_argument("--look", default="3d")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
scene = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials
scene.frame_set(1); t0 = time.time()
S = 1.65            # この電車は実寸の約1.65倍で作られている（座面0.76m＝実寸0.46m）
FPS = 24


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


# ---------------------------------------------------------------- 場面の準備（v1と同じ）
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
for ob in O:
    if ob.name.startswith("Window") and ob.type == "MESH": ob.visible_shadow = False
# Codex版の乗客は隠す（新しい人物に置き換える）
OLD = {n: (O[n].matrix_world.translation.copy(), O[n].matrix_world.to_euler().z) for n in people.PEOPLE if n in O}
for n in OLD:
    for ob in hier(O[n]): ob.hide_render = True; ob.hide_viewport = True
robot = O["MARU / pause"]; button = O["Pause button"]; pulse = O["Pause pulse"]
r_torso = next(o for o in hier(robot) if o.name.endswith("• torso"))
r_ant = next((o for o in hier(robot) if "antenna" in o.name and "•" in o.name), None)
robot.scale = (0, 0, 0)

# ---------------------------------------------------------------- 人物（線画アイコン風）
coll = bpy.data.collections.new("PEOPLE icon"); scene.collection.children.link(coll)
P = {}
names = ["PASSENGER 00"] if A.only_hero else list(people.PEOPLE)
for i, n in enumerate(names):
    cfg = dict(people.PEOPLE[n])
    if n == "PASSENGER 00":
        ch = iconfig.make_icon("Hero", iconfig.HERO_COLORS, outfit=A.outfit, coll=coll, S=S, quality=1.0, look=A.look)
    else:
        cols = dict(top=iconfig.MUTED_TOPS[(i * 4) % len(iconfig.MUTED_TOPS)], pants=iconfig.MUTED_PANTS[(i * 3) % len(iconfig.MUTED_PANTS)],
                    skin=iconfig.SKINS[(i * 5) % len(iconfig.SKINS)])
        ch = iconfig.make_icon(f"P{n[-2:]}", cols, outfit=None, coll=coll, S=S, quality=0.8, look=A.look)
    arm = ch["arm"]; loc, rz = OLD[n]
    arm.location = loc; arm.rotation_euler = (0, 0, rz)
    rig = hrig.Rig(arm); rig.eye_gain = ch.get("eye_gain", 1.0)
    person = dict(ch, rig=rig, kind=cfg["pose"], phase=random.Random(i).uniform(0, 4), breath=random.Random(i + 9).uniform(3.6, 4.6),
                  headz=random.Random(i + 3).uniform(-4, 4), headx=random.Random(i + 5).uniform(-3, 4))
    person["sp_neck"] = motion.Spring(2.2, 0.5); person["sp_head"] = motion.Spring(3.0, 0.45)
    ph, so = hchar.make_phone(f"{n} phone", coll, os.path.join(HERE, "screens", cfg["screen"]), S=S)
    person["phone"] = ph; P[n] = person
    print(f"PERSON {n} built {round(time.time() - t0, 1)}s", flush=True)
hero = P["PASSENGER 00"]
hero_bud_rest = hero["bud_R"]   # 右耳のイヤホン（休み姿勢）
LS = iconfig.freestyle(scene, bpy.context.view_layer, 3.4, collection=coll) if A.look == "toon" else None   # 3Dの見た目では線を引かない


def apply_pose(person):
    for nme in person["rig"].names:
        pb = person["arm"].pose.bones[nme]; pb.rotation_quaternion = person["rig"].q[nme]; pb.location = person["rig"].loc[nme]


def attach_phone(person, C, R, bone="hand.L"):
    """スマホを手の骨に固定（その時の手の姿勢に対する相対位置で）"""
    rig = person["rig"]; arm = person["arm"]; ph = person["phone"]
    Mw = arm.matrix_world @ hrig.to_mat4(R, C)
    Mb = arm.matrix_world @ rig.M[bone] @ Matrix.Translation((0, rig.length[bone], 0))
    ph.parent = arm; ph.parent_type = "BONE"; ph.parent_bone = bone
    ph.matrix_parent_inverse = Matrix.Identity(4)
    ph.matrix_basis = Mb.inverted() @ Mw


def pose_hero_still(t):
    ex = {}
    hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
    hero_anim.pose_at(hero, t, 0.0, hero_bud_rest, ex)
    return ex


for n, person in P.items():
    if n == "PASSENGER 00":
        ex = pose_hero_still(0.0); C, R = ex["C"], ex["R"]
    else:
        C, R = people.base_pose(person, 0.0)
    apply_pose(person); attach_phone(person, C, R, "hand.L")
bpy.context.view_layer.update()
print("POSED", round(time.time() - t0, 1), flush=True)

# ---------------------------------------------------------------- ほこり・光・カメラ（v1と同じ考え方）
mote_m = M.new("Dust mote"); mote_m.use_nodes = True; _b = mote_m.node_tree.nodes["Principled BSDF"]
_b.inputs["Base Color"].default_value = (1, 0.97, 0.9, 1); _b.inputs["Emission Color"].default_value = (1, 0.95, 0.85, 1); _b.inputs["Emission Strength"].default_value = 0.25
me = bpy.data.meshes.new("Dust"); bm = bmesh.new(); rnd = random.Random(11)
for i in range(160):
    c = Vector((0.14, -3.65, 0.9)) + Vector((rnd.uniform(-1.4, 1.4), rnd.uniform(-1.6, 1.6), rnd.uniform(-0.75, 1.2)))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rnd.uniform(0.004, 0.011), matrix=Matrix.Translation(c))
bm.to_mesh(me); bm.free(); dust = link(O.new("Dust", me)); me.materials.append(mote_m); dust.hide_render = True


def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = link(O.new(name, ld)); ob.location = loc; return ob


def aim(ob, target): ob.rotation_euler = (ob.location - Vector(target)).to_track_quat("Z", "Y").to_euler()


sun = light("Window sun", "SUN", 4.0, kelvin(5600)); sun.data.angle = math.radians(1.5)
sun.rotation_euler = Vector((-0.80, -0.30, 0.52)).to_track_quat("Z", "Y").to_euler()
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


def W(person, p_local):
    return person["arm"].matrix_world @ Vector(tuple(float(x) for x in p_local))


def hero_points():
    rig = hero["rig"]; rig.fk()
    hp = W(hero, rig.posed_point("head", hero["hc"]))      # 頭の中心（耳の高さ）
    bud = W(hero, rig.posed_point("head", hero_bud_rest))
    return hp, bud


def pause_parts(show):
    for n in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
        if n in O: O[n].hide_render = not show


def light_A():
    sun.data.energy = 4.0; ceil.data.energy = 900.0; spot.data.energy = 0; glow.data.energy = 0
    scene.view_settings.exposure = 0.0; haze.hide_render = True; dust.hide_render = True


def shot_A_wide():
    set_cam((0.45, -7.25, 1.45), (-0.25, 3.0, 1.15), 24); light_A(); pause_parts(False)
    if LS: LS.linestyle.thickness = 2.6 * A.res[1] / 540


def shot_C_dropout():
    pause_parts(False)
    if LS: LS.linestyle.thickness = 4.2 * A.res[1] / 540
    ex = pose_hero_still(hero_anim.T_DROP + 0.62); apply_pose(hero); set_mouth(hero, ex["mouth_o"])
    bpy.context.view_layer.update()
    hp, bud = hero_points()
    # 点の目が2つとも見え、右耳のイヤホンも見える角度（正面から右へ約25°）
    set_cam((hp.x - 1.38, hp.y + 0.64, hp.z + 0.02), (hp.x, hp.y + 0.06, hp.z - 0.16), 35, dof=(hp, 2.4))
    sun.data.energy = 0.6; ceil.data.energy = 120.0; scene.view_settings.exposure = -1.0
    spot.location = (hp.x - 0.6, hp.y - 0.4, 2.9); aim(spot, (hp.x, hp.y, hp.z - 0.3)); spot.data.energy = 260.0; spot.data.color = kelvin(7000)
    haze.hide_render = False; vs.inputs["Density"].default_value = 0.035; dust.hide_render = True


def shot_C_freeze():
    pause_parts(True)
    if LS: LS.linestyle.thickness = 3.0 * A.res[1] / 540
    ex = pose_hero_still(0.0); apply_pose(hero); set_mouth(hero, 0.0)
    b = button.location.copy(); robot.scale = (0.55, 0.55, 0.55)
    robot.location = (b.x, b.y, 0.14); robot.rotation_euler = (0, 0, math.radians(150))
    r_torso.rotation_euler.x = -math.radians(7)
    if r_ant: r_ant.rotation_euler.x = -math.radians(16)
    button.location.z = 0.10
    pulse.scale = (2.6, 2.6, 2.6); pulse.location.z = 0.02
    pulse.data.materials.clear(); pulse.data.materials.append(mat_emit("Pulse glow", (0.3, 1.0, 0.9), 6.0))
    # カメラ：まるロボの後ろに人の頭が重ならない位置を計算で選んだ（--mode search3）
    set_cam((b.x - 1.00, b.y - 1.60, 0.40), (b.x + 0.25, b.y + 0.25, 0.44), 24, dof=((b.x, b.y, 0.45), 2.8))
    sun.data.energy = 1.4; ceil.data.energy = 60.0; scene.view_settings.exposure = -1.2
    spot.location = (b.x - 0.3, b.y - 0.5, 2.9); aim(spot, (b.x, b.y, 0.3)); spot.data.energy = 220.0; spot.data.color = kelvin(3500)
    glow.data.energy = 60.0; haze.hide_render = False; vs.inputs["Density"].default_value = 0.05; dust.hide_render = False


def set_mouth(person, o):
    if person.get("mouth") is None: return
    kb = person["mouth"].data.shape_keys.key_blocks; kb["o"].value = o


ee = scene.eevee; scene.render.engine = "BLENDER_EEVEE_NEXT"; ee.taa_render_samples = A.samples; ee.use_shadows = True; ee.use_raytracing = False
for k, v in (("volumetric_start", 0.1), ("volumetric_end", 40.0), ("volumetric_samples", 64), ("use_volumetric_shadows", True)):
    if hasattr(ee, k): setattr(ee, k, v)
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "None"
scene.render.resolution_x, scene.render.resolution_y = A.res; scene.render.resolution_percentage = 100
SHOTS = {"1": shot_A_wide, "2": shot_C_dropout, "3": shot_C_freeze}

if A.mode in ("layout", "stills"):
    for key in A.shots.split(","):
        SHOTS[key](); bpy.context.view_layer.update()
        if A.mode == "layout":
            pts = {f"{n[-2:]}head": W(p, p["rig"].head_pos("head") + np.array([0, 0, 0.06])) for n, p in P.items()}
            pts["robot"] = robot.matrix_world.translation + Vector((0, 0, 0.4))
            print(f"LAYOUT shot{key} " + " ".join(f"{k}=({c.x:.2f},{c.y:.2f},{c.z:.1f})" for k, c in ((k, world_to_camera_view(scene, cam, v)) for k, v in pts.items())), flush=True)
            continue
        scene.render.filepath = os.path.join(A.out, f"opening_icon_shot{key}.png"); bpy.ops.render.render(write_still=True)
        print("STILL", scene.render.filepath, round(time.time() - t0, 1), flush=True)

if A.mode == "anim":
    exec(open(os.path.join(HERE, "opening_v2_anim.py")).read())   # 動きは同じ（線画アイコン風の人にもそのまま使える）

if A.mode == "seq":
    exec(open(os.path.join(HERE, "opening_seq_anim.py")).read())   # 冒頭の動き（3ショット）

if A.mode == "search3":
    # ショット3のカメラ候補：まるロボの後ろに人の頭が重ならない位置を探す
    shot_C_freeze(); bpy.context.view_layer.update()
    b = button.location.copy(); best = []
    for dx in (-1.75, -1.6, -1.45, -1.3, -1.15, -1.0):
        for dy in (-1.6, -1.45, -1.3, -1.15, -1.0):
            for tx in (-0.15, 0.05, 0.25):
                set_cam((b.x + dx, b.y + dy, 0.40), (b.x + tx, b.y + 0.25, 0.44), 24); bpy.context.view_layer.update()
                rb = world_to_camera_view(scene, cam, robot.matrix_world.translation + Vector((0, 0, 0.25)))
                heads = [world_to_camera_view(scene, cam, W(p, p["rig"].head_pos("head") + np.array([0, 0, 0.06]))) for p in P.values()]
                vis = [h for h in heads if h.z > 0 and -0.05 < h.x < 1.05 and -0.05 < h.y < 1.08]
                gap = min([abs(h.x - rb.x) for h in vis] + [1.0])
                edge = min([min(abs(h.y - 1.0), abs(h.x), abs(h.x - 1.0)) for h in vis] + [1.0])
                score = gap - 2.0 * abs(rb.x - 0.45) - 1.5 * abs(rb.y - 0.42) + 0.3 * min(edge, 0.08)
                best.append((score, dx, dy, tx, round(rb.x, 2), round(rb.y, 2), round(gap, 2), len(vis)))
    best.sort(reverse=True)
    for r in best[:6]: print("SEARCH3", r, flush=True)
