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
ap.add_argument("--who", default="M1,W1,G1")
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
Y0, Y1 = -3.0, 7.0
WIN_Z0, WIN_Z1 = 1.01, 1.86
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
    PITCH, WW = 1.54, 1.20
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

# ---------------------------------------------------------------- 人
coll = bpy.data.collections.new("PEOPLE ref"); sc.collection.children.link(coll)
SPACING = 0.56
YAW = {"M1": -25.0, "W1": -2.0, "G1": 6.0, "X1": 4.0, "X2": 0.0}
PHONE = {"M1": "#2A3045", "W1": "#E4E7EA", "G1": "#1C1D22", "X1": "#2B2E36", "X2": "#C9B9A5"}
order = A.who.split(",")
P = {}
for i, key in enumerate(order):
    cfg = dict(ref_people.PEOPLE[key])
    ch = hchar.make_character(f"R{key}", cfg, coll, S=1.0)
    ch["arm"].location = (0.0, SPACING * i, 0.0); ch["arm"].rotation_euler = (0, 0, math.radians(-90 + YAW.get(key, 0.0)))
    rig = hrig.Rig(ch["arm"])
    person = dict(ch, rig=rig, kind=cfg["pose"], phase=0.7 * i, headz=0.0, headx=-7.0, neck=-3.0, blink_T=99.0)
    if "phone_c" in cfg: person["phone_c"] = cfg["phone_c"]
    C, R = people.base_pose(person, 0.4)
    for nme in rig.names:
        pb = ch["arm"].pose.bones[nme]; pb.rotation_quaternion = rig.q[nme]; pb.location = rig.loc[nme]
    ph, so = hchar.make_phone(f"{key} phone", coll, os.path.join(HERE, "screens", cfg["screen"]), S=1.0, style="clay")
    ph.data.materials[0] = mat(f"{key} phone body", PHONE.get(key, "#2A2C33"), 0.32, coat=0.4); ph.scale = (1.3, 1.3, 1.3)
    bpy.context.view_layer.update()
    Mb = ch["arm"].matrix_world @ rig.M["hand.L"] @ Matrix.Translation((0, rig.length["hand.L"], 0))
    ph.parent = ch["arm"]; ph.parent_type = "BONE"; ph.parent_bone = "hand.L"; ph.matrix_parent_inverse = Matrix.Identity(4)
    ph.matrix_basis = Mb.inverted() @ (ch["arm"].matrix_world @ hrig.to_mat4(R, C)) @ Matrix.Scale(1.3, 4)
    P[key] = person
    print("PERSON", key, round(time.time() - t0, 1), flush=True)
bpy.context.view_layer.update()


def head_pts(p):
    rig = p["rig"]; rig.fk(); Mw = p["arm"].matrix_world; hc = np.asarray(p["hc"]); s = p["s"]
    f = lambda q: np.array(Mw @ Vector(tuple(rig.posed_point("head", hc + np.asarray(q) * s))))
    return f((0, 0, 0)), f((0, -0.02, 0.17)), f((0, -0.075, -0.105))     # 中心、髪の上、あご


# ---------------------------------------------------------------- カメラ：参考と同じ位置に頭が来るように（手前の男性の頭＝右上、女性＝中央、眼鏡＝左）
# 胸の高さから少し見上げる。人は参考と同じく斜め横顔（カメラから見て顔の向きが60°前後）になるよう体の向きを合わせる
TARGET = {"M1": (0.79, 0.34, 0.50), "W1": (0.38, 0.49, 0.36), "G1": (0.15, 0.56, 0.28)}   # (x, 上からのy, 頭の高さ/画面の高さ)
VIEW_ANG = {"M1": 58.0, "W1": 62.0, "G1": 55.0}
asp = A.res[1] / A.res[0]; rng = np.random.default_rng(1)


def evaluate(cx, cy, cz, yaw, pit, lens, H):
    D = np.stack([np.cos(pit) * np.cos(yaw), np.cos(pit) * np.sin(yaw), np.sin(pit)], 1)
    Rt = np.stack([np.sin(yaw), -np.cos(yaw), np.zeros(len(yaw))], 1); Up = np.cross(Rt, D)
    def proj(Pw):
        v = Pw[None, :] - np.stack([cx, cy, cz], 1)
        zc = (v * D).sum(1); xc = (v * Rt).sum(1); yc = (v * Up).sum(1)
        return 0.5 + lens * xc / (zc * 36.0), 0.5 - lens * yc / (zc * 36.0 * asp), zc
    err = np.zeros(len(yaw))
    for k, (tx_, ty_, th_) in TARGET.items():
        if k not in H: continue
        c_, top_, chin_ = H[k]
        x0, y0, z0 = proj(c_); _, yt, _ = proj(top_); _, yb, _ = proj(chin_)
        err += (x0 - tx_) ** 2 + (y0 - ty_) ** 2 + 0.35 * ((yb - yt) - th_) ** 2 + 10.0 * (z0 < 0.3)
    return err, D


def solve(H):
    m1 = H[order[0]][0]; N = 160000
    S = dict(cx=m1[0] - rng.uniform(0.30, 1.30, N), cy=m1[1] - rng.uniform(-0.10, 1.20, N), cz=rng.uniform(1.00, 1.16, N),
             yaw=rng.uniform(math.radians(30), math.radians(100), N), pit=rng.uniform(math.radians(0), math.radians(11), N), lens=rng.uniform(28, 45, N))
    lim = dict(cz=(1.00, 1.16), pit=(0.0, math.radians(11)), lens=(28, 45))
    err, D = evaluate(S["cx"], S["cy"], S["cz"], S["yaw"], S["pit"], S["lens"], H)
    for it in range(3):
        idx = np.argsort(err)[:200]; n2 = 40000; j = rng.choice(idx, n2); f = 0.5 ** it
        sig = dict(cx=0.03, cy=0.03, cz=0.02, yaw=0.02, pit=0.02, lens=0.8)
        Nw = {k: S[k][j] + rng.normal(0, sig[k] * f, n2) for k in S}
        for k, (lo, hi) in lim.items(): Nw[k] = np.clip(Nw[k], lo, hi)
        e2, D2 = evaluate(Nw["cx"], Nw["cy"], Nw["cz"], Nw["yaw"], Nw["pit"], Nw["lens"], H)
        S = {k: np.concatenate([S[k], Nw[k]]) for k in S}; err = np.concatenate([err, e2]); D = np.concatenate([D, D2])
    b = int(np.argmin(err)); return {k: float(S[k][b]) for k in S}, D[b], float(err[b])


for rnd in range(3):
    H = {k: head_pts(P[k]) for k in P}
    best, Dbest, e = solve(H)
    print("CAM", rnd, round(e, 5), {k: round(v, 3) for k, v in best.items()}, flush=True)
    camp = np.array([best["cx"], best["cy"], best["cz"]])
    for k in order:        # 体の向き：カメラが人物の左側（正面から反時計回りに VIEW_ANG）に来るように
        hpos = np.array(P[k]["arm"].location); dc = camp[:2] - hpos[:2]; ang_c = math.atan2(dc[1], dc[0])
        face = ang_c - math.radians(VIEW_ANG.get(k, 60.0))
        P[k]["arm"].rotation_euler = (0, 0, face + math.radians(90))     # 回転0の正面は −Y（−90°）
        print("  YAW", k, round(math.degrees(face + math.radians(90)), 1), flush=True)
    bpy.context.view_layer.update()
H = {k: head_pts(P[k]) for k in P}
best, Dbest, e = solve(H)
print("CAM final", round(e, 5), {k: round(v, 3) for k, v in best.items()}, flush=True)
cd = bpy.data.cameras.new("Cam"); cam = O.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (best["cx"], best["cy"], best["cz"]); cd.lens = best["lens"]; cd.sensor_width = 36; cd.sensor_fit = "HORIZONTAL"
cam.rotation_euler = Vector(tuple(Dbest)).to_track_quat("-Z", "Y").to_euler()
eye_m1 = H[order[0]][0] + np.array([0, 0, 0.012])
cd.dof.use_dof = True; cd.dof.focus_distance = float(np.linalg.norm(eye_m1 - np.array(cam.location))); cd.dof.aperture_fstop = 4.0

# ---------------------------------------------------------------- 光：窓（人の後ろ＝＋X）から暖かい日差し、手前（カメラ側）から柔らかい光
def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = O.new(name, ld); sc.collection.objects.link(ob); ob.location = loc; return ob
def aim_l(ob, tgt): ob.rotation_euler = (Vector(tgt) - ob.location).to_track_quat("-Z", "Y").to_euler()
sun = light("Sun", "SUN", 8.5, kelvin(3400)); sun.data.angle = math.radians(1.5)
sun.rotation_euler = Vector((0.62, 0.55, 0.56)).to_track_quat("Z", "Y").to_euler()      # 窓の外・左奥・上から
camv = Vector(cam.location)
m1 = H[order[0]][0]
key = light("Key", "AREA", 260.0, kelvin(3700), tuple(camv + Vector((-0.65, 0.25, 0.75)))); key.data.size = 2.0; aim_l(key, tuple(m1))
fill = light("Fill", "AREA", 80.0, kelvin(6200), (-1.5, 1.2, 1.9)); fill.data.size = 3.0; aim_l(fill, (0.0, 0.6, 1.0))
win = light("Window glow", "AREA", 90.0, kelvin(6800), (0.30, 1.0, 1.45)); win.data.shape = "RECTANGLE"; win.data.size, win.data.size_y = 0.8, 7.0
aim_l(win, (-1.0, 1.0, 1.2))
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb("#C8D8E8"), 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.15
if A.layout:
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    for k in P:
        c_, top_, chin_ = H[k]; v = world_to_camera_view(sc, cam, Vector(tuple(c_)))
        vt = world_to_camera_view(sc, cam, Vector(tuple(top_))); vb = world_to_camera_view(sc, cam, Vector(tuple(chin_)))
        print("LAYOUT", k, "x", round(v.x, 3), "y_top", round(1 - v.y, 3), "h", round(vt.y - vb.y, 3), flush=True)

# ---------------------------------------------------------------- 描画とにじみ
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = A.samples; sc.eevee.use_shadows = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = 0.0
sc.render.resolution_x, sc.render.resolution_y = A.res
sc.use_nodes = True; ct = sc.node_tree; ct.nodes.clear()
rl = ct.nodes.new("CompositorNodeRLayers"); gl = ct.nodes.new("CompositorNodeGlare"); co = ct.nodes.new("CompositorNodeComposite")
gl.glare_type = "FOG_GLOW"; gl.threshold = 1.0; gl.size = 7; gl.mix = 0.04
ct.links.new(rl.outputs["Image"], gl.inputs["Image"]); ct.links.new(gl.outputs["Image"], co.inputs["Image"])
sc.render.filepath = os.path.join(A.out, f"ref_scene{A.tag}.png"); bpy.ops.render.render(write_still=True)
print("STILL", sc.render.filepath, round(time.time() - t0, 1), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, f"ref_scene{A.tag}.blend"))
