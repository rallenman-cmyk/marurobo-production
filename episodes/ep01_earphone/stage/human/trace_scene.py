# 参考画像と同じ場面：紺の布の座席、角の丸い大きな窓と明るい街、後ろから暖かい日差し。手前に大きく男性、真ん中に女性、奥に眼鏡の男性
# 使い方: blender -b --factory-startup --python ref_scene.py -- --out DIR [--res W H] [--samples N] [--layout 1]
import bpy, bmesh, sys, os, math, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix
import hchar, hrig, people, ref_people, sdf
from hbuild import srgb, NT, principled, mk_mesh

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="/tmp/rs"); ap.add_argument("--res", nargs=2, type=int, default=[1280, 720])
ap.add_argument("--samples", type=int, default=32); ap.add_argument("--layout", type=int, default=0); ap.add_argument("--tag", default="")
ap.add_argument("--who", default="M1,W1,G1"); ap.add_argument("--fit", default=""); ap.add_argument("--body_yaw_off", type=float, default=0.0); ap.add_argument("--phones", default=""); ap.add_argument("--phone_fit", type=int, default=1); ap.add_argument("--proj", type=int, default=0); ap.add_argument("--proj_emit", type=float, default=0.55); ap.add_argument("--hair_dir", default="")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []); os.makedirs(A.out, exist_ok=True)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene; O = bpy.data.objects; t0 = time.time()


def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexc, rough=0.6, sheen=0.0, metal=0.0, felt=0.0, coat=0.0):
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, base=srgb(hexc), rough=rough, spec=0.35, sheen=sheen, sheen_r=0.45, metal=metal, coat=coat, coat_r=0.2)
    if felt > 0:   # フェルトのような細かい凹凸と色むら
        tc = nt.n("ShaderNodeTexCoord"); nz = nt.n("ShaderNodeTexNoise", i_Scale=380.0, i_Detail=8.0); nt.l(tc.outputs["Object"], nz.inputs["Vector"])
        bp = nt.n("ShaderNodeBump", i_Strength=felt, i_Distance=0.0015); nt.l(nz.outputs["Fac"], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
        n2 = nt.n("ShaderNodeTexNoise", i_Scale=9.0, i_Detail=2.0); nt.l(tc.outputs["Object"], n2.inputs["Vector"])
        mx = nt.n("ShaderNodeMix", data_type="RGBA"); mx.inputs[6].default_value = (*[c * 0.86 for c in srgb(hexc)], 1); mx.inputs[7].default_value = (*srgb(hexc), 1)
        nt.l(n2.outputs["Fac"], mx.inputs[0]); nt.l(mx.outputs[2], b.inputs["Base Color"])
    return m


def box(name, lo, hi, material, bevel=0.01, seg=3, shadow=True):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=[h - l for l, h in zip(lo, hi)], verts=bm.verts); bmesh.ops.translate(bm, vec=[(l + h) / 2 for l, h in zip(lo, hi)], verts=bm.verts)
    bm.to_mesh(me); bm.free(); ob = O.new(name, me); sc.collection.objects.link(ob); me.materials.append(material)
    if bevel > 0:
        bv = ob.modifiers.new("b", "BEVEL"); bv.width = bevel; bv.segments = seg; bv.limit_method = "NONE"
        me.shade_smooth(); ob.modifiers.new("ws", "WEIGHTED_NORMAL")
    ob.visible_shadow = shadow
    return ob


# ---------------------------------------------------------------- 車内（人の背中側＝＋X が窓）。反対側（−X）にも同じ列
SEAT = mat("Seat fabric", "#2C4A86", 0.92, sheen=0.55, felt=0.30)
WALL = mat("Wall", "#D8D3CA", 0.62); FRAME = mat("Window frame", "#C3C7CD", 0.28, metal=0.75)
SKIRT = mat("Seat skirt", "#525760", 0.5)
FLOOR = mat("Floor", "#9A9C9E", 0.5, felt=0.05); CEIL = mat("Ceiling", "#ECEAE5", 0.6); POLE = mat("Pole", "#CDD1D6", 0.15, metal=1.0)
Y0, Y1 = -3.922, 7.0     # 参考の窓の位置に合わせる（窓の幅0.70m・柱0.44m、下1.08m・上1.76m）
WIN_Z0, WIN_Z1 = 1.08, 1.76
for side in (1, -1):
    xw = 0.33 if side > 0 else -2.62     # 壁の内側の面
    def X(a, b): return (min(xw + side * a, xw + side * b), max(xw + side * a, xw + side * b))
    xa, xb = X(-0.59, -0.12)              # 座面（壁から 0.12〜0.59m）
    box("Seat cushion", (xa, Y0, 0.33), (xb, Y1, 0.465), SEAT, 0.045, 4)
    sa, sb = X(-0.57, -0.24); box("Seat skirt", (sa, Y0, 0.04), (sb, Y1, 0.33), SKIRT, 0.01)
    ba, bb = X(-0.16, -0.03); box("Seat back", (ba, Y0, 0.44), (bb, Y1, 0.985), SEAT, 0.045, 4)
    wa, wb = X(0.0, 0.06)
    box("Wall low", (wa, Y0 - 1, 0.0), (wb, Y1 + 1, WIN_Z0), WALL, 0.0)
    box("Wall high", (wa, Y0 - 1, WIN_Z1), (wb, Y1 + 1, 2.30), WALL, 0.0)
    # 窓：幅1.20m、柱0.34m。枠は角の丸い四角（外側は柱に重なる）＋上の横の桟
    PITCH, WW = 1.138, 0.70
    y = Y0
    while y < Y1:
        box("Pillar", (wa, y, WIN_Z0), (wb, y + PITCH - WW, WIN_Z1), WALL, 0.012)
        y += PITCH
    def frame_sdf(cy, cz, hw, hh, xw=xw, side=side):
        c = np.array([xw - side * 0.006, cy, cz])
        outer = sdf.rbox(c, np.array([0.016, hw + 0.035, hh + 0.035]), 0.010)
        inner = sdf.rbox(c, np.array([0.05, hw - 0.012, hh - 0.012]), 0.075)
        bar = sdf.rbox(np.array([xw - side * 0.004, cy, WIN_Z1 - 0.20]), np.array([0.012, hw, 0.016]), 0.006)
        return lambda p: np.minimum(np.maximum(outer(p), -inner(p)), bar(p))
    fm = sdf.Model(); y = Y0 + PITCH - WW
    while y < Y1:
        cy = y + WW / 2
        fm.add(sdf.bounded(frame_sdf(cy, (WIN_Z0 + WIN_Z1) / 2, WW / 2, (WIN_Z1 - WIN_Z0) / 2),
                           (xw - 0.1, cy - 0.8, WIN_Z0 - 0.1), (xw + 0.1, cy + 0.8, WIN_Z1 + 0.1), 0.02), "frame")
        y += PITCH
    Vf, Qf = sdf.mesh(fm, np.array([xw - 0.05, Y0, WIN_Z0 - 0.06]), np.array([xw + 0.05, Y1, WIN_Z1 + 0.06]), 0.006, relax_iters=1)
    fo = mk_mesh("Window frames", Vf, [tuple(q) for q in Qf], coll=sc.collection, mats=[FRAME]); fo.data.shade_smooth()
for yy in (1.62,):   # 握り棒（縦）
    me = bpy.data.meshes.new("Pole"); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.018, radius2=0.018, depth=2.30)
    bm.to_mesh(me); bm.free(); ob = O.new("Pole", me); sc.collection.objects.link(ob); ob.location = (-0.33, yy, 1.15); me.materials.append(POLE)
    me.shade_smooth()
box("Floor", (-3.0, Y0 - 1, -0.02), (0.40, Y1 + 1, 0.0), FLOOR, 0.0)
box("Ceiling", (-3.0, Y0 - 1, 2.30), (0.40, Y1 + 1, 2.36), CEIL, 0.0)
# 窓の外の街（光る絵、少しかすませる。影は作らない）
city = bpy.data.images.load(os.path.join(HERE, "refscene", "city.png"))
cm = bpy.data.materials.new("City"); nt = NT(cm)
tx = nt.n("ShaderNodeTexImage"); tx.image = city; tx.extension = "MIRROR"
hz = nt.n("ShaderNodeMix", data_type="RGBA"); hz.inputs[0].default_value = 0.06; hz.inputs[7].default_value = (*srgb("#EEF4F8"), 1); nt.l(tx.outputs["Color"], hz.inputs[6])
em = nt.n("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.9; nt.l(hz.outputs[2], em.inputs["Color"])
o_ = nt.n("ShaderNodeOutputMaterial"); nt.l(em.outputs[0], o_.inputs[0])
for side, xc in ((1, 4.6), (-1, -7.0)):
    me = bpy.data.meshes.new("City"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f_ in bm.faces:
        for l_ in f_.loops: l_[uvl].uv = ((l_.vert.co.x + 0.5) * 1.6, l_.vert.co.y + 0.5)
    bm.to_mesh(me); bm.free(); co_ = O.new("City", me); sc.collection.objects.link(co_); me.materials.append(cm)
    co_.location = (xc, 2.0, 2.2); co_.rotation_euler = (math.radians(90), 0, math.radians(-90 if side > 0 else 90)); co_.scale = (26.0, 6.0, 1)
    co_.visible_shadow = False; co_.visible_diffuse = False

# ---------------------------------------------------------------- 人：参考画像から逆算した頭の位置・向き（trace_fit.py の結果）に合わせて置く
import json
FIT = json.load(open(A.fit))
PH = json.load(open(A.phones)) if A.phones else None
PHONE_OBS = {"M1": dict(tl=(850, 555), tr=(955, 532), edge=(1085, 730)), "W1": dict(tl=(350, 680), tr=(425, 665), edge=(480, 770)),
             "G1": dict(tl=(70, 675), tr=(115, 665), edge=(145, 730))} if A.phone_fit else {}
def proj_px(Pw, cam):
    Cc, yaw, pit, roll, f = cam
    d = np.array([math.cos(pit) * math.cos(yaw), math.cos(pit) * math.sin(yaw), math.sin(pit)])
    r0 = np.array([math.sin(yaw), -math.cos(yaw), 0.0]); u0 = np.cross(r0, d)
    r = r0 * math.cos(roll) + u0 * math.sin(roll); u = -r0 * math.sin(roll) + u0 * math.cos(roll)
    v = Pw - Cc; zc = v @ d; fx = f / 36.0 * 1672
    return np.stack([836 + fx * (v @ r) / zc, 470.5 - fx * (v @ u) / zc], -1), zc
import pose_lib
coll = bpy.data.collections.new("PEOPLE ref"); sc.collection.children.link(coll)
PHONE = {"M1": "#2A3045", "W1": "#E4E7EA", "G1": "#1C1D22", "X1": "#2B2E36", "X2": "#C9B9A5"}
order = A.who.split(",")
P = {}
for i, key in enumerate(order):
    cfg = dict(ref_people.PEOPLE[key]); hf_ = FIT["heads"][key]
    if A.proj:      # 資料の絵を頭に貼る（表情は「下を見る」、重みは場面のカメラに合わせたもの）
        cfg.update(projtex=True, expr="lookdown", projw=os.path.join(HERE, "..", "..", "sheets", f"projw_{key}_scene.npz"), proj_emit=A.proj_emit)
    hov = os.path.join(A.hair_dir, f"hopt_{key}.json") if A.hair_dir else ""
    if hov and os.path.exists(hov):      # 参考の輪郭に合わせた髪の形
        cfg["hair"] = dict(cfg["hair"], over=json.load(open(hov))); print("HAIR override", key, flush=True)
    ch = hchar.make_character(f"R{key}", cfg, coll, S=1.0)
    ch["arm"].location = (0.0, 0.0, 0.0); ch["arm"].rotation_euler = (0, 0, hf_["psi"] + math.radians(A.body_yaw_off))
    rig = hrig.Rig(ch["arm"]); rig.eye_gain = 0.5          # 描いた目は黒目が目の中に収まるよう、視線の動きを半分に
    person = dict(ch, rig=rig, kind=cfg["pose"], phase=0.7 * i, headz=0.0, headx=0.0, neck=0.0, blink_T=99.0)
    if "phone_c" in cfg: person["phone_c"] = cfg["phone_c"]
    C, R = people.base_pose(person, 0.4)
    # 頭の向き：骨格空間で R_arm^T · R_fit · R_rest
    bpy.context.view_layer.update()
    Ra = np.array(ch["arm"].matrix_world.to_3x3()); Rf = np.array(hf_["R"]); Rrest = hrig.m3(rig.rest["head"])
    rig.set_world_rot("head", Ra.T @ Rf @ Rrest)
    for sd in ("L", "R"): rig.look("eye." + sd, C)
    rig.fk()
    # 頭の中心が合わせた位置に来るよう、体ごと動かす
    hc = np.asarray(ch["hc"]); pc = np.array(ch["arm"].matrix_world @ Vector(tuple(rig.posed_point("head", hc))))
    ch["arm"].location = Vector(tuple(np.array(hf_["H"]) - pc))
    bpy.context.view_layer.update()
    if key in PHONE_OBS:     # スマホ：胸の前の自然な範囲で、参考の角の位置に一番近くなる所を探す（画面は目の方、左手で持つ）
        Ra = np.array(ch["arm"].matrix_world.to_3x3()); Ta = np.array(ch["arm"].matrix_world.translation)
        eye_mid = (rig.head_pos("eye.L") + rig.head_pos("eye.R")) / 2
        camT = (np.array(FIT["camera"]["C"]), FIT["camera"]["yaw"], FIT["camera"]["pitch"], FIT["camera"]["roll"], FIT["camera"]["lens"])
        o = PHONE_OBS[key]; tl, tr, ed = (np.array(o[n], float) for n in ("tl", "tr", "edge"))
        def frame(c, tilt, tw):
            C_, R_ = pose_lib.phone_frame(person["J"], eye_mid, center=c, tilt_up=tilt)
            ct, st_ = math.cos(tw), math.sin(tw); Rz = np.array([[ct, -st_, 0], [st_, ct, 0], [0, 0, 1.0]])
            return C_, Rz @ R_                     # 縦軸まわりに少し回す（参考の絵ではスマホの裏がカメラに向いている）
        def cost(c, tilt, tw=0.0):
            C_, R_ = frame(c, tilt, tw)
            xa, ya, nn = R_[:, 0] * 1.3, R_[:, 1] * 1.3, R_[:, 2]
            cor = np.array([C_ + ya * 0.075 - xa * 0.036, C_ + ya * 0.075 + xa * 0.036, C_ - ya * 0.075 + xa * 0.036, C_ - ya * 0.075 - xa * 0.036])
            uv, zc = proj_px((cor @ Ra.T) + Ta, camT)
            i0, i1 = (0, 1) if uv[0][0] < uv[1][0] else (1, 0)
            a, b = uv[i0], uv[i1]; bb = uv[2] if i1 == 1 else uv[3]
            dv = (bb - b) / (np.linalg.norm(bb - b) + 1e-9); w = ed - b
            e = np.sum((a - tl) ** 2) + np.sum((b - tr) ** 2) + (dv[0] * w[1] - dv[1] * w[0]) ** 2
            back = (np.array(FIT["camera"]["C"]) - ((C_ @ Ra.T) + Ta)) @ (Ra @ nn)        # >0 ならカメラから画面が見える
            return e + (4000.0 * back if back > 0 else 0.0)
        rng_ = np.random.default_rng(3); best = None
        for _ in range(2500):
            c = np.array([rng_.uniform(-0.10, 0.12), rng_.uniform(-0.36, -0.20), rng_.uniform(0.90, 1.06)]); tilt = rng_.uniform(0.0, 0.8); tw = rng_.uniform(-0.7, 0.7)
            v = cost(c, tilt, tw)
            if best is None or v < best[0]: best = (v, c, tilt, tw)
        v, c, tilt, tw = best
        for _ in range(1200):
            c2 = np.clip(c + rng_.normal(0, 0.01, 3), [-0.10, -0.36, 0.90], [0.12, -0.20, 1.06]); t2 = float(np.clip(tilt + rng_.normal(0, 0.05), 0.0, 0.8))
            w2 = float(np.clip(tw + rng_.normal(0, 0.05), -0.7, 0.7)); v2 = cost(c2, t2, w2)
            if v2 < v: v, c, tilt, tw = v2, c2, t2, w2
        print("PHONE", key, "c", np.round(c, 3), "tilt", round(tilt, 2), "twist", round(math.degrees(tw), 1), "err px", round(math.sqrt(v / 5), 1), flush=True)
        C, R = frame(c, tilt, tw)
        wl, Rl = pose_lib.left_grip(C, R)
        rig.ik2("upper_arm.L", "forearm.L", wl, pole=(0.7, 0.4, -1.0), end="hand.L", end_R=Rl)
        pose_lib.curl(rig, "L", 38, 70, 38, thumb=(6, 8, 6))
        wr, Rr = pose_lib.thigh_rest(person["J"], "R", -1)
        rig.ik2("upper_arm.R", "forearm.R", wr, pole=(-0.6, 0.5, -1.0), end="hand.R", end_R=Rr)
        pose_lib.curl(rig, "R", 14, 22, 12, thumb=(6, 6, 4), spread=2)
        rig.fk()
        for sd in ("L", "R"): rig.look("eye." + sd, C + R[:, 2] * 0.006)
        LID = {"M1": -24.7, "W1": -26.1, "G1": -23.8} if cfg.get("sheet") else {}
        for sd in ("L", "R"): rig.rot("lid_up." + sd, x=LID.get(key, 3.0))   # 下を見る：上まぶたを少し下げる（6面図の LOOK DOWN と同じ）
        rig.fk()
    hip = np.array(ch["arm"].matrix_world @ Vector(tuple(rig.head_pos("hips"))))
    print("PLACE", key, "root", np.round(np.array(ch["arm"].location), 3), "hips z", round(float(hip[2]), 3), flush=True)
    for nme in rig.names:
        pb = ch["arm"].pose.bones[nme]; pb.rotation_quaternion = rig.q[nme]; pb.location = rig.loc[nme]
    ph, so = hchar.make_phone(f"{key} phone", coll, os.path.join(HERE, "screens", cfg["screen"]), S=1.0, style="clay")
    ph.data.materials[0] = mat(f"{key} phone body", PHONE.get(key, "#2A2C33"), 0.32, coat=0.4)
    bpy.context.view_layer.update()
    Mb = ch["arm"].matrix_world @ rig.M["hand.L"] @ Matrix.Translation((0, rig.length["hand.L"], 0))
    ph.parent = ch["arm"]; ph.parent_type = "BONE"; ph.parent_bone = "hand.L"; ph.matrix_parent_inverse = Matrix.Identity(4)
    ph.matrix_basis = Mb.inverted() @ (ch["arm"].matrix_world @ hrig.to_mat4(R, C)) @ Matrix.Scale(1.3, 4)
    P[key] = person
    print("PERSON", key, round(time.time() - t0, 1), flush=True)
bpy.context.view_layer.update()

# ---------------------------------------------------------------- カメラ（合わせた結果）
cf = FIT["camera"]
cd = bpy.data.cameras.new("Cam"); cam = O.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
yaw, pit, roll = cf["yaw"], cf["pitch"], cf["roll"]
d_ = Vector((math.cos(pit) * math.cos(yaw), math.cos(pit) * math.sin(yaw), math.sin(pit)))
r0 = Vector((math.sin(yaw), -math.cos(yaw), 0.0)); u0 = r0.cross(d_)
r_ = r0 * math.cos(roll) + u0 * math.sin(roll); u_ = -r0 * math.sin(roll) + u0 * math.cos(roll)
Mc = Matrix(((r_.x, u_.x, -d_.x), (r_.y, u_.y, -d_.y), (r_.z, u_.z, -d_.z)))
cam.matrix_world = Matrix.Translation(Vector(cf["C"])) @ Mc.to_4x4()
cd.lens = cf["lens"]; cd.sensor_width = 36; cd.sensor_fit = "HORIZONTAL"
m1 = np.array(FIT["heads"][order[0]]["H"])
cd.dof.use_dof = True; cd.dof.focus_distance = float(np.linalg.norm(m1 - np.array(cf["C"]))); cd.dof.aperture_fstop = 4.0
H = {k: (np.array(FIT["heads"][k]["H"]),) for k in P}

# ---------------------------------------------------------------- 光：窓（人の後ろ＝＋X）から暖かい日差し、手前（カメラ側）から柔らかい光
def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = O.new(name, ld); sc.collection.objects.link(ob); ob.location = loc; return ob
def aim_l(ob, tgt): ob.rotation_euler = (Vector(tgt) - ob.location).to_track_quat("-Z", "Y").to_euler()
sun = light("Sun", "SUN", 8.5, kelvin(3800)); sun.data.angle = math.radians(1.5)
sun.rotation_euler = Vector((0.62, 0.55, 0.56)).to_track_quat("Z", "Y").to_euler()      # 窓の外・左奥・上から
camv = Vector(cam.location)
key = light("Key", "AREA", 260.0, kelvin(4400), tuple(camv + Vector((-0.65, 0.25, 0.75)))); key.data.size = 2.0; aim_l(key, tuple(m1))
fill = light("Fill", "AREA", 40.0, kelvin(6200), (-1.5, 1.2, 1.9)); fill.data.size = 3.0; aim_l(fill, (0.0, 0.6, 1.0))
facefill = light("Face fill", "AREA", 70.0, kelvin(4300), tuple(Vector(cf["C"]) + Vector((0.0, 0.0, 0.35)))); facefill.data.size = 2.4; aim_l(facefill, tuple(m1))   # 顔の陰影を平らに（参考の柔らかい光）
top = light("Top sky", "AREA", 110.0, kelvin(9000), (-0.35, 0.6, 2.25)); top.data.shape = "RECTANGLE"; top.data.size, top.data.size_y = 0.5, 2.4; aim_l(top, (-0.1, 0.8, 1.0))   # 髪の上の面を青白く
win = light("Window glow", "AREA", 90.0, kelvin(6800), (0.30, 1.0, 1.45)); win.data.shape = "RECTANGLE"; win.data.size, win.data.size_y = 0.8, 7.0
aim_l(win, (-1.0, 1.0, 1.2))
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb("#AFC6E6"), 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.12
# ---------------------------------------------------------------- 描画とにじみ
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = A.samples; sc.eevee.use_shadows = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = 0.0
sc.render.resolution_x, sc.render.resolution_y = A.res
sc.use_nodes = True; ct = sc.node_tree; ct.nodes.clear()
rl = ct.nodes.new("CompositorNodeRLayers"); gl = ct.nodes.new("CompositorNodeGlare"); co = ct.nodes.new("CompositorNodeComposite")
gl.glare_type = "FOG_GLOW"; gl.threshold = 1.0; gl.size = 7; gl.mix = 0.025
ct.links.new(rl.outputs["Image"], gl.inputs["Image"]); ct.links.new(gl.outputs["Image"], co.inputs["Image"])
sc.render.filepath = os.path.join(A.out, f"trace{A.tag}.png"); bpy.ops.render.render(write_still=True)
print("STILL", sc.render.filepath, round(time.time() - t0, 1), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, f"trace{A.tag}.blend"))
