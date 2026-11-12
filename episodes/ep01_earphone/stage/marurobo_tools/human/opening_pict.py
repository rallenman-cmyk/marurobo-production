# 冒頭の動き（22秒）を、晴れた電車＋ピクトグラムの人（A案・主人公は④：白い体＋しま模様の上着＋黄色いキャップ＋点の目）で作る
# まるロボと一時停止ボタンは maru_opening.blend から持ってくる。跳躍の物理は前と同じ（電車1.65倍の座標のまま、縮めて置く）
# 使い方: blender -b --factory-startup --python opening_pict.py -- --out DIR [--res W H] [--samples N] [--frames A:B] [--dry 1]
import bpy, bmesh, sys, os, math, argparse, random, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix
import hchar, hrig, pose_lib, people, motion, hero_anim, iconfig, sdf
from hbuild import srgb, NT, principled, mk_mesh

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/opp"); ap.add_argument("--res", nargs=2, type=int, default=[960, 540])
ap.add_argument("--samples", type=int, default=12); ap.add_argument("--frames", default="1:528"); ap.add_argument("--blur", type=int, default=1)
ap.add_argument("--dry", type=int, default=0); ap.add_argument("--dry_frames", default="40,118,140,200,232,330,360,368,376,400,480")
ap.add_argument("--blend", default="", help="maru_opening.blend の場所（PCではこれで指定する）")
ap.add_argument("--video", type=int, default=0, help="1＝連番ではなく mp4（H.264）で書き出す（PC用）")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []); os.makedirs(A.out, exist_ok=True)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
scene = sc = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials; t0 = time.time()
FPS = 24
S = 1.65                      # まるロボとボタンの座標は「1.65倍の電車」のまま（下の OldWorld で縮めて置く）
BLEND = A.blend or next((p_ for p_ in (os.path.join(HERE, "..", "..", d_, "bluetooth_handoff_restored", "restore", "v3", "bt_opening", "output", "maru_opening.blend")
                                        for d_ in ("handoff", "")) if os.path.exists(p_)), "")
assert os.path.exists(BLEND), "maru_opening.blend が見つからない。--blend で場所を指定する"


def link(ob): scene.collection.objects.link(ob); return ob


def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out


def mat_emit(name, rgb, s):
    m = M.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = s
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); return m


# ---------------------------------------------------------------- 車内
exec(open(os.path.join(HERE, "train_env_exec.py"), encoding="utf-8").read())

# ---------------------------------------------------------------- まるロボと一時停止ボタン（前の場面ファイルから）
want = {"MARU / pause", "Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"}
with bpy.data.libraries.load(BLEND, link=False) as (src, dst):
    names = list(src.objects)
    dst.objects = [n for n in names]
loaded = [o for o in dst.objects if o is not None]
keep = set()
for o in loaded:
    if o.name in want:
        for c in hier(o): keep.add(c.name)
for o in loaded:
    if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
for n in sorted(keep): link(O[n])
for n in keep:     # 前の場面の動きの記録を消す（今の位置・大きさはそのまま）
    ob = O[n]
    if ob.animation_data:
        loc, rot, scl, hr = ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy(), ob.hide_render
        ob.animation_data_clear(); ob.location, ob.rotation_euler, ob.scale, ob.hide_render = loc, rot, scl, hr
    for idb in [ob.data] + [s_.material for s_ in ob.material_slots if s_.material]:
        if idb is not None and getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt_ = getattr(idb, "node_tree", None)
        if nt_ is not None and nt_.animation_data: nt_.animation_data_clear()
    if ob.type == "MESH" and ob.data.shape_keys and ob.data.shape_keys.animation_data: ob.data.shape_keys.animation_data_clear()
robot = O["MARU / pause"]; button = O["Pause button"]; pulse = O["Pause pulse"]
r_torso = next(o for o in hier(robot) if o.name.endswith("• torso"))
r_ant = next((o for o in hier(robot) if "antenna" in o.name and "•" in o.name), None)
robot.scale = (0, 0, 0)
# 古い座標（1.65倍）→ 新しい電車：ボタンを主人公の足もとの通路に置き、カメラCの向きが通路の奥→座席を見る向きになるよう回す
B_OLD = Vector((0.14, -3.65, 0.0)); B_NEW = Vector((-0.92, -0.10, 0.0))
d_old = Vector((-1.00, -1.60)).normalized(); d_new = Vector((-0.42, -1.00)).normalized()
PHI = math.atan2(d_new.y, d_new.x) - math.atan2(d_old.y, d_old.x)
oldw = link(O.new("OldWorld", None))
oldw.matrix_world = Matrix.Translation(B_NEW) @ Matrix.Rotation(PHI, 4, "Z") @ Matrix.Scale(1.0 / S, 4) @ Matrix.Translation(-B_OLD)
for o in (robot, button, O["Pause button base"], pulse):
    o.parent = oldw; o.matrix_parent_inverse = Matrix.Identity(4)
bpy.context.view_layer.update()
E = oldw.matrix_world.copy(); Einv = E.inverted()
def to_w(p): return E @ Vector(p)
def to_old(p): return Einv @ Vector(p)

# ---------------------------------------------------------------- 人（ピクトグラム A案）
coll = bpy.data.collections.new("PEOPLE pict"); scene.collection.children.link(coll)
PASS = "#B9BDC4"
HERO_C = dict(body="#F1EFEA", accent="#F2B82E", eyes=True)
HEAD = dict(neck=False, Rh=0.140, hc_z=1.226)
XR, XL = 0.0, -2.29                      # 右の座席（窓＝＋X）と左の座席の、人の位置
ROSTER = [  # 名前, x, y, 向き(度), 持ち方, 画面
    ("H", XR, 0.00, -92, "phone_left", "music.png"), ("P1", XR, 0.82, -88, "phone_left", "news.png"), ("P2", XR, 1.47, -94, "phone_both", "game.png"),
    ("P3", XR, 2.12, -89, "phone_left", "chat.png"), ("P4", XR, 2.77, -92, "phone_left", "news.png"), ("P5", XR, 3.80, -90, "phone_both", "music.png"),
    ("L1", XL, 0.40, 88, "phone_left", "chat.png"), ("L2", XL, 1.48, 93, "phone_both", "game.png"), ("L3", XL, 2.50, 90, "phone_left", "news.png"),
    ("L4", XL, 3.55, 87, "phone_left", "music.png")]
P = {}; rnd = random.Random(7)
for i, (key, x, y, yaw, pose, scr) in enumerate(ROSTER):
    if key == "H": ch = iconfig.make_icon("Hero", HERO_C, outfit="cap", coll=coll, S=1.0, quality=1.0, look="pict", **HEAD)
    else: ch = iconfig.make_icon(key, dict(body=PASS), outfit=None, coll=coll, S=1.0, quality=0.85, look="pict", **HEAD)
    ch["arm"].location = (x, y, 0.0); ch["arm"].rotation_euler = (0, 0, math.radians(yaw))
    rig = hrig.Rig(ch["arm"]); rig.eye_gain = ch.get("eye_gain", 1.0)
    person = dict(ch, rig=rig, kind=pose, phase=rnd.uniform(0, 4), breath=rnd.uniform(3.6, 4.6), headz=rnd.uniform(-4, 4), headx=rnd.uniform(-3, 4) - 4.0,
                  neck=-2.0, blink_T=rnd.uniform(3.6, 5.0), idx=i)
    person["sp_neck"] = motion.Spring(2.2, 0.5); person["sp_head"] = motion.Spring(3.0, 0.45)
    ph, so = hchar.make_phone(f"{key} phone", coll, os.path.join(HERE, "screens", scr), S=1.0)
    person["phone"] = ph; P[key] = person
    print("PERSON", key, round(time.time() - t0, 1), flush=True)
hero = P["H"]; hero_bud_rest = hero["bud_R"]


def stripes_mat(c1, c2, period=0.052):
    m = M.new("Hero stripes"); nt = NT(m); b = principled(nt, base=srgb(c2), **iconfig.PBR["pict"])
    at = nt.n("ShaderNodeAttribute", attribute_name="rest"); sp = nt.n("ShaderNodeSeparateXYZ"); nt.l(at.outputs["Vector"], sp.inputs[0])
    mu = nt.n("ShaderNodeMath", operation="MULTIPLY"); mu.inputs[1].default_value = 1.0 / period; nt.l(sp.outputs[2], mu.inputs[0])
    fr = nt.n("ShaderNodeMath", operation="FRACT"); nt.l(mu.outputs[0], fr.inputs[0])
    lt = nt.n("ShaderNodeMath", operation="LESS_THAN"); lt.inputs[1].default_value = 0.5; nt.l(fr.outputs[0], lt.inputs[0])
    mx = nt.n("ShaderNodeMix", data_type="RGBA"); nt.l(lt.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = (*srgb(c2), 1); mx.inputs[7].default_value = (*srgb(c1), 1); nt.l(mx.outputs[2], b.inputs["Base Color"])
    return m


ST = stripes_mat("#2D3A5A", "#F6F4EE")
for p_ in ("top", "arm.L", "arm.R"): O[f"Hero {p_}"].data.materials[0] = ST


def apply_pose(person):
    for nme in person["rig"].names:
        pb = person["arm"].pose.bones[nme]; pb.rotation_quaternion = person["rig"].q[nme]; pb.location = person["rig"].loc[nme]


def attach_phone(person, C, R, bone="hand.L", scale=1.15):
    rig = person["rig"]; arm = person["arm"]; ph = person["phone"]
    bpy.context.view_layer.update()
    Mb = arm.matrix_world @ rig.M[bone] @ Matrix.Translation((0, rig.length[bone], 0))
    ph.parent = arm; ph.parent_type = "BONE"; ph.parent_bone = bone; ph.matrix_parent_inverse = Matrix.Identity(4)
    ph.matrix_basis = Mb.inverted() @ (arm.matrix_world @ hrig.to_mat4(R, C)) @ Matrix.Scale(scale, 4)


for n, person in P.items():
    if n == "H":
        ex = {}; hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
        hero_anim.pose_at(hero, 0.0, 0.0, hero_bud_rest, ex); C, R = ex["C"], ex["R"]
    else:
        C, R = people.base_pose(person, 0.0)
    apply_pose(person); attach_phone(person, C, R)
bpy.context.view_layer.update()
print("POSED", round(time.time() - t0, 1), flush=True)


def W(person, p_local):
    return person["arm"].matrix_world @ Vector(tuple(float(x) for x in p_local))


def hero_points():
    rig = hero["rig"]; rig.fk()
    return W(hero, rig.posed_point("head", hero["hc"])), W(hero, rig.posed_point("head", hero_bud_rest))


# ---------------------------------------------------------------- ほこり（ショットCだけ）：古い座標でボタンのまわりに作り、OldWorld に付ける
mote_m = M.new("Dust mote"); mote_m.use_nodes = True; _b = mote_m.node_tree.nodes["Principled BSDF"]
_b.inputs["Base Color"].default_value = (1, 0.97, 0.9, 1); _b.inputs["Emission Color"].default_value = (1, 0.95, 0.85, 1); _b.inputs["Emission Strength"].default_value = 0.6
me = bpy.data.meshes.new("Dust"); bm = bmesh.new(); rd = random.Random(11)
for i in range(160):
    c = Vector((0.14, -3.65, 0.9)) + Vector((rd.uniform(-1.4, 1.4), rd.uniform(-1.6, 1.6), rd.uniform(-0.75, 1.2)))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rd.uniform(0.004, 0.011), matrix=Matrix.Translation(c))
bm.to_mesh(me); bm.free(); dust = link(O.new("Dust", me)); me.materials.append(mote_m); dust.hide_render = True
dust.parent = oldw; dust.matrix_parent_inverse = Matrix.Identity(4)

# ---------------------------------------------------------------- 光（晴れた日差し → 音が止まると暗く、主人公／まるロボにスポット）
def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = link(O.new(name, ld)); ob.location = loc; return ob
def aim(ob, tgt): ob.rotation_euler = (Vector(tgt) - ob.location).to_track_quat("-Z", "Y").to_euler()
sun = light("Sun", "SUN", 8.5, kelvin(3400)); sun.data.angle = math.radians(1.5)
sun.rotation_euler = Vector((0.62, 0.55, 0.56)).to_track_quat("Z", "Y").to_euler()
key = light("Key", "AREA", 260.0, kelvin(3700), (-1.75, -1.3, 2.05)); key.data.size = 2.0; aim(key, (0.0, 0.7, 1.05))
fill = light("Fill", "AREA", 80.0, kelvin(6200), (-1.5, 1.2, 1.9)); fill.data.size = 3.0; aim(fill, (0.0, 0.6, 1.0))
win = light("Window glow", "AREA", 90.0, kelvin(6800), (0.30, 1.0, 1.45)); win.data.shape = "RECTANGLE"; win.data.size, win.data.size_y = 0.8, 7.0
aim(win, (-1.0, 1.0, 1.2))
spot = light("Subject spot", "SPOT", 0.0, kelvin(7000)); spot.data.spot_size = math.radians(32); spot.data.spot_blend = 0.6; spot.data.shadow_soft_size = 0.2
glow = light("Button glow", "POINT", 0.0, (0.3, 0.95, 0.9), tuple(to_w((0.14, -3.65, 0.35)))); glow.data.shadow_soft_size = 0.15
w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True
wbg = w.node_tree.nodes["Background"]; wbg.inputs[0].default_value = (*srgb("#C8D8E8"), 1); wbg.inputs[1].default_value = 0.15
hz_me = bpy.data.meshes.new("Haze"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(hz_me); bm.free()
haze = link(O.new("Haze volume", hz_me)); haze.location = (-1.15, 1.5, 1.15); haze.scale = (3.4, 11.0, 2.3)
hm = M.new("Haze"); hm.use_nodes = True; hnt = hm.node_tree; hnt.nodes.clear()
vs = hnt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Anisotropy"].default_value = 0.45; vs.inputs["Density"].default_value = 0.0
ho = hnt.nodes.new("ShaderNodeOutputMaterial"); hnt.links.new(vs.outputs[0], ho.inputs["Volume"]); hz_me.materials.append(hm)

# ---------------------------------------------------------------- 描画の設定
ee = scene.eevee; scene.render.engine = "BLENDER_EEVEE_NEXT"; ee.taa_render_samples = A.samples; ee.use_shadows = True; ee.use_raytracing = False
for k_, v_ in (("volumetric_start", 0.1), ("volumetric_end", 12.0), ("volumetric_samples", 24), ("volumetric_tile_size", "16"),
               ("use_volumetric_shadows", False), ("shadow_resolution_scale", 0.6)):
    if hasattr(ee, k_): setattr(ee, k_, v_)
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"; scene.view_settings.exposure = 0.0
scene.render.resolution_x, scene.render.resolution_y = A.res; scene.render.resolution_percentage = 100
scene.use_nodes = True; ct = scene.node_tree; ct.nodes.clear()
rl = ct.nodes.new("CompositorNodeRLayers"); gl = ct.nodes.new("CompositorNodeGlare"); co = ct.nodes.new("CompositorNodeComposite")
gl.glare_type = "FOG_GLOW"; gl.threshold = 1.0; gl.size = 7; gl.mix = 0.04
ct.links.new(rl.outputs["Image"], gl.inputs["Image"]); ct.links.new(gl.outputs["Image"], co.inputs["Image"])

exec(open(os.path.join(HERE, "opening_pict_seq.py"), encoding="utf-8").read())
