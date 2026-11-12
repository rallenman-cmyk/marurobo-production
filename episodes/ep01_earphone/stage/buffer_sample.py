# バッファの章 30秒サンプル（舞台モデル2：貯蔵タワー）
# 使い方: blender -b story.blend --python buffer_sample.py -- --mode layout|stills|anim --out DIR [--res W H] [--samples N] [--frames A:B] [--font PATH]
import bpy, bmesh, sys, os, math, json, argparse
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

ap = argparse.ArgumentParser()
ap.add_argument("--mode", default="layout"); ap.add_argument("--out", default="/tmp/bs")
ap.add_argument("--res", nargs=2, type=int, default=[640, 360]); ap.add_argument("--samples", type=int, default=8)
ap.add_argument("--frames", default="1:720"); ap.add_argument("--font", default="")
ap.add_argument("--still-times", default="3.4,12.6")
ap.add_argument("--video", action="store_true", help="PNG連番ではなくmp4を直接書き出す（PC用）")
ap.add_argument("--final", action="store_true", help="本番画質（影の解像度などを上げる）")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)

FPS, T_END, G = 24, 30.0, 9.81
NF = int(T_END * FPS)
scene = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials
scene.frame_set(1)

# ------------------------------------------------------------------ 数学の部品
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def minjerk(u):  # 躍度最小（5次）の補間
    u = clamp(u); return u * u * u * (10 - 15 * u + 6 * u * u)
def mj(t, t0, t1, a, b):
    if t <= t0: return a
    if t >= t1: return b
    return a + (b - a) * minjerk((t - t0) / (t1 - t0))
def quintic(t, T, x0, v0, a0, x1, v1, a1):  # 境界条件つき躍度最小軌道 → (x, v, a)
    T2, T3, T4, T5 = T * T, T ** 3, T ** 4, T ** 5
    c3 = (20 * (x1 - x0) - (8 * v1 + 12 * v0) * T - (3 * a0 - a1) * T2) / (2 * T3)
    c4 = (30 * (x0 - x1) + (14 * v1 + 16 * v0) * T + (3 * a0 - 2 * a1) * T2) / (2 * T4)
    c5 = (12 * (x1 - x0) - 6 * (v1 + v0) * T - (a0 - a1) * T2) / (2 * T5)
    x = x0 + v0 * t + a0 / 2 * t * t + c3 * t ** 3 + c4 * t ** 4 + c5 * t ** 5
    v = v0 + a0 * t + 3 * c3 * t * t + 4 * c4 * t ** 3 + 5 * c5 * t ** 4
    a = a0 + 6 * c3 * t + 12 * c4 * t * t + 20 * c5 * t ** 3
    return x, v, a
def pulse(t, t0, rise, hold, fall):
    return mj(t, t0, t0 + rise, 0, 1) - mj(t, t0 + rise + hold, t0 + rise + hold + fall, 0, 1)
def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

# ------------------------------------------------------------------ 場面の準備（Codex版の部品を流用）
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
for ob in list(O):
    if ob.animation_data:
        loc, rot, scl, hr = ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy(), ob.hide_render
        ob.animation_data_clear(); ob.location, ob.rotation_euler, ob.scale, ob.hide_render = loc, rot, scl, hr
for coll in (bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
    for idb in coll:
        if getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt = getattr(idb, "node_tree", None)
        if nt and nt.animation_data: nt.animation_data_clear()
maru = O["Maru"]; floor = O["Shared slate floor"]
boxes = {n: O["Inside " + n] for n in ("04", "05", "06")}
keep = set(hier(maru)) | {floor}
for b in boxes.values():
    mw = b.matrix_world.copy(); b.parent = None; b.matrix_world = mw; keep |= set(hier(b))
for ob in list(O):
    if ob.type == "LIGHT": O.remove(ob, do_unlink=True); continue
    if ob not in keep and ob.type != "CAMERA": ob.hide_render = True; ob.hide_viewport = True
floor.scale = (6, 6, 1)
O["Maru cargo"].scale = (0, 0, 0)          # 03番の箱は使わず、6番を運ぶ
for b in boxes.values(): b.scale = (1, 1, 1); b.rotation_euler = (0, 0, 0)

# ------------------------------------------------------------------ 形を作る部品
def link(ob): scene.collection.objects.link(ob); return ob
def mat_basic(name, rgb, rough=0.5, metal=0.0):
    m = M.new(name); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    return m
def mat_emit(name, rgb, strength):
    m = M.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); return m
def emit_input(m): return m.node_tree.nodes["Emission"].inputs["Strength"]
def box(name, size, loc, mat, bevel=0.0, origin_off=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0] - origin_off[0], v.co.y * size[1] - origin_off[1], v.co.z * size[2] - origin_off[2]))
    bm.to_mesh(me); bm.free(); ob = link(O.new(name, me)); ob.location = loc; me.materials.append(mat)
    if bevel > 0:
        b = ob.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    return ob
def cylinder(name, r1, r2, depth, loc, rot, mat, seg=48):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=depth)
    bm.to_mesh(me); bm.free(); ob = link(O.new(name, me)); ob.location = loc; ob.rotation_euler = rot; me.materials.append(mat)
    for f in me.polygons: f.use_smooth = True
    return ob
def torus(name, major, minor, loc, rot, mat, seg=48, rseg=10):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        for j in range(rseg):
            bm.faces.new((rings[i][j], rings[(i + 1) % seg][j], rings[(i + 1) % seg][(j + 1) % rseg], rings[i][(j + 1) % rseg]))
    bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    ob = link(O.new(name, me)); ob.location = loc; ob.rotation_euler = rot; me.materials.append(mat); return ob

alu = M.get("Petrol aluminium"); ti = M.get("Titanium"); gra = M.get("Graphite"); mid = M.get("Midnight") or gra
wall_mat = mat_basic("Interior wall", (0.60, 0.62, 0.64), 0.6)
seam_mat = M.get("Ceramic seam") or gra

# ------------------------------------------------------------------ 舞台：イヤホンの中の倉庫（貯蔵タワー）
Z_GATE, BOX_H, Z_SEAT, Z_COLTOP, Z_RIM, Z_DECK = 1.78, 0.68, 1.00, 3.20, 3.45, 2.85
# 奥の壁（曲面）と目地
me = bpy.data.meshes.new("Back wall"); bm = bmesh.new(); R_W, CX, CY = 15.0, -1.5, -6.0; prev = None
for i in range(41):
    a = math.radians(-70 + 140 * i / 40); x, y = CX + R_W * math.sin(a), CY + R_W * math.cos(a)
    v0, v1 = bm.verts.new((x, y, 0)), bm.verts.new((x, y, 16))
    if prev: bm.faces.new((prev[0], prev[1], v1, v0))
    prev = (v0, v1)
bm.to_mesh(me); bm.free(); link(O.new("Back wall", me)).data.materials.append(wall_mat)
for zz in (3.6, 7.2, 10.8):
    torus(f"Wall seam {zz}", R_W - 0.02, 0.03, (CX, CY, zz), (0, 0, 0), seam_mat, seg=96, rseg=6)
# スピーカー（再生装置）
box("Playback unit", (1.7, 1.25, 1.0), (0, 0, 0.5), gra, bevel=0.06)
box("Playback slot", (1.12, 0.66, 0.01), (0, 0, 1.0), mid)
cone = cylinder("Speaker cone", 0.36, 0.12, 0.10, (0, -0.64, 0.5), (math.pi / 2, 0, 0), ti)
torus("Speaker surround", 0.40, 0.035, (0, -0.63, 0.5), (math.pi / 2, 0, 0), alu)
play_mat = mat_emit("Play lamp", (0.35, 1.0, 0.45), 6.0)
cylinder("Play lamp", 0.05, 0.05, 0.03, (0.62, -0.635, 0.86), (math.pi / 2, 0, 0), play_mat, seg=24)
# タワー：柱4本、1箱ごとの帯（目盛り）、底の扉、上の漏斗
for sx in (-0.6, 0.6):
    for sy in (-0.38, 0.38):
        box(f"Tower post {sx} {sy}", (0.07, 0.07, Z_COLTOP - Z_SEAT + 0.04), (sx, sy, (Z_SEAT + Z_COLTOP) / 2), alu)
for k in range(3):
    zz = Z_GATE + k * BOX_H if k < 2 else Z_COLTOP
    for (sx, sy, lx, ly) in ((0, -0.38, 1.2, 0.04), (0, 0.38, 1.2, 0.04), (-0.6, 0, 0.04, 0.76), (0.6, 0, 0.04, 0.76)):
        box(f"Tower band {k} {sx} {sy}", (lx, ly, 0.035), (sx, sy, zz), alu)
flap_mat = ti
flapL = box("Gate flap L", (0.6, 0.74, 0.04), (-0.6, 0, Z_GATE + 0.02), flap_mat, origin_off=(-0.3, 0, 0))
flapR = box("Gate flap R", (0.6, 0.74, 0.04), (0.6, 0, Z_GATE + 0.02), flap_mat, origin_off=(0.3, 0, 0))
me = bpy.data.meshes.new("Funnel"); bm = bmesh.new()
inner = [(-0.62, -0.4), (0.62, -0.4), (0.62, 0.4), (-0.62, 0.4)]; outer = [(-0.95, -0.65), (0.95, -0.65), (0.95, 0.65), (-0.95, 0.65)]
vi = [bm.verts.new((x, y, Z_COLTOP)) for x, y in inner]; vo = [bm.verts.new((x, y, Z_RIM)) for x, y in outer]
for i in range(4): bm.faces.new((vi[i], vi[(i + 1) % 4], vo[(i + 1) % 4], vo[i]))
bm.to_mesh(me); bm.free(); fun = link(O.new("Funnel", me)); me.materials.append(alu)
sol = fun.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.04
# 「バッファです」で光る緑の縁と札
green = mat_emit("Buffer glow", (0.30, 1.0, 0.45), 0.0)
for sx in (-0.6, 0.6):
    box(f"Buffer strip {sx}", (0.03, 0.012, Z_COLTOP - Z_GATE), (sx, -0.42, (Z_GATE + Z_COLTOP) / 2), green)
label_mat = mat_emit("Buffer label", (0.80, 1.0, 0.85), 0.0)
cu = bpy.data.curves.new("Buffer label", "FONT"); cu.body = "バッファ"; cu.size = 0.25; cu.align_x = "CENTER"; cu.extrude = 0.01
font_ok = False
for fp in [A.font, "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"]:
    if fp and os.path.exists(fp):
        try: cu.font = bpy.data.fonts.load(fp); font_ok = True; break
        except Exception as e: print("FONT_FAIL", fp, e)
label = link(O.new("Buffer label", cu)); label.location = (0, -0.46, 2.84); label.rotation_euler = (math.pi / 2, 0, 0)
plate = box("Buffer plate", (1.16, 0.03, 0.36), (0, -0.43, 2.92), mid, bevel=0.03)
cu.materials.append(label_mat); print("FONT_OK", font_ok)
# 通路（まるロボが来る道）
box("Catwalk deck", (7.3, 1.1, 0.10), (-4.35, 0, Z_DECK - 0.05), alu, bevel=0.02)
for px in (-6.6, -3.2):
    box(f"Catwalk post {px}", (0.09, 0.09, Z_DECK - 0.1), (px, 0.4, (Z_DECK - 0.1) / 2), alu)
# 音の輪（音楽が流れている印）
ring_mats, rings = [], []
def mat_emit_fade(name, rgb):  # 光る＋透明（明るさ0で黒くならず、消える）
    m = M.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = 0.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ad = nt.nodes.new("ShaderNodeAddShader"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], o.inputs[0])
    if hasattr(m, "surface_render_method"): m.surface_render_method = "BLENDED"
    return m
for i in range(5):
    m = mat_emit_fade(f"Sound ring {i}", (0.75, 1.0, 0.95)); ring_mats.append(m)
    rings.append(torus(f"Sound ring {i}", 0.42, 0.008, (0, -0.7, 0.5), (math.pi / 2, 0, 0), m, seg=64, rseg=6))
# 強調用の光と、かすみの箱
def light(name, kind, energy, color, loc=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = link(O.new(name, ld)); ob.location = loc; return ob
def aim(ob, target): ob.rotation_euler = (ob.location - Vector(target)).to_track_quat("Z", "Y").to_euler()
sun_key = light("Key A", "SUN", 4.0, kelvin(5600)); sun_key.data.angle = math.radians(3)
sun_key.rotation_euler = Vector((-0.4545, -0.4545, 0.766)).to_track_quat("Z", "Y").to_euler()  # 左前45°・高さ50°
sun_fill = light("Fill A", "SUN", 1.6, kelvin(6500)); sun_fill.data.use_shadow = False; sun_fill.data.angle = math.radians(10)
sun_fill.rotation_euler = Vector((0.852, -0.310, 0.423)).to_track_quat("Z", "Y").to_euler()  # 右70°・高さ25°
hl04 = light("Highlight 04", "POINT", 0.0, kelvin(4500), (0.0, -1.0, 1.8)); hl04.data.shadow_soft_size = 0.4
hl05 = light("Highlight 05", "POINT", 0.0, kelvin(4500), (0.0, -1.1, 2.2)); hl05.data.shadow_soft_size = 0.4
spot_robot = light("Robot spot C", "SPOT", 0.0, kelvin(3500), (0, 0, Z_DECK + 4.0)); spot_robot.data.spot_size = math.radians(34); spot_robot.data.spot_blend = 0.45; spot_robot.data.shadow_soft_size = 0.3
spot_tower = light("Tower spot C", "SPOT", 0.0, (0.35, 0.95, 0.9), (0.0, -0.6, 6.2)); spot_tower.data.spot_size = math.radians(28); spot_tower.data.spot_blend = 0.5
aim(spot_tower, (0, 0, Z_GATE))
w = bpy.data.worlds.new("Buffer world"); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
bg = nt.nodes.new("ShaderNodeBackground"); wo = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(bg.outputs[0], wo.inputs["Surface"]); scene.world = w
bg.inputs[0].default_value = (0.55, 0.63, 0.72, 1); bg.inputs[1].default_value = 0.45
hz_me = bpy.data.meshes.new("Haze"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(hz_me); bm.free()
haze = link(O.new("Haze volume", hz_me)); haze.location = (-1.5, 2, 6); haze.scale = (40, 30, 14)
hm = M.new("Haze"); hm.use_nodes = True; hnt = hm.node_tree; hnt.nodes.clear()
vs = hnt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Anisotropy"].default_value = 0.4; ho = hnt.nodes.new("ShaderNodeOutputMaterial")
hnt.links.new(vs.outputs[0], ho.inputs["Volume"]); hz_me.materials.append(hm); haze_d = vs.inputs["Density"]

# ------------------------------------------------------------------ カメラ
cam_d = bpy.data.cameras.new("Buffer camera"); cam = link(O.new("Buffer camera", cam_d)); scene.camera = cam
cam_d.lens = 28; cam_d.sensor_width = 36; cam_d.clip_end = 300
CAM_KEYS = [  # (時刻, 位置, 注視点)
    (0.0, (-1.75, -8.4, 2.4), (-1.6, 0, 2.3)),
    (5.4, (-0.55, -6.2, 1.75), (-0.25, 0, 1.55)),
    (6.6, (-0.55, -6.2, 1.75), (-0.25, 0, 1.55)),
    (8.4, (-1.9, -8.6, 2.5), (-1.7, 0, 2.4)),
    (24.4, (-1.9, -8.6, 2.5), (-1.7, 0, 2.4)),
    (26.6, (-1.25, -7.4, 2.45), (-0.9, 0, 2.35)),
    (30.0, (-1.25, -7.4, 2.45), (-0.9, 0, 2.35)),
]
def cam_at(t):
    for (t0, p0, q0), (t1, p1, q1) in zip(CAM_KEYS, CAM_KEYS[1:]):
        if t0 <= t <= t1:
            u = minjerk((t - t0) / (t1 - t0)) if t1 > t0 else 1
            return Vector(p0).lerp(Vector(p1), u), Vector(q0).lerp(Vector(q1), u)
    return Vector(CAM_KEYS[-1][1]), Vector(CAM_KEYS[-1][2])

# ------------------------------------------------------------------ 物理：まるロボの歩き（倒立振子＋フルード数）
L_LEG, HIP_X, BETA, LIFT = 0.43, 0.255, 0.60, 0.07
def stride(v):  # Alexanderの関係：歩幅/脚長 = 2.3 × (v²/gL)^0.3
    return 2.3 * L_LEG * max(v * v / (G * L_LEG), 1e-9) ** 0.3
X_IN, T_IN, V_WALK, X_STOP, T_DEC = -8.4, 7.4, 1.3, -1.45, 1.4
X_DEC = X_STOP - V_WALK * T_DEC / 2
T_DEC0 = T_IN + (X_DEC - X_IN) / V_WALK
def robot_x(t):
    if t < T_IN: return X_IN, 0.0, 0.0
    if t < T_DEC0: return X_IN + V_WALK * (t - T_IN), V_WALK, 0.0
    if t < T_DEC0 + T_DEC: return quintic(t - T_DEC0, T_DEC, X_DEC, V_WALK, 0, X_STOP, 0, 0)
    return X_STOP, 0.0, 0.0
T_STOP = T_DEC0 + T_DEC
# 演技のタイミング
T_BOW0, T_BOW1, T_REL_BACK = T_STOP + 0.10, T_STOP + 0.48, T_STOP + 1.25
T_RELIEF = 25.3; BLINKS = [16.4, 20.7, 25.5, 28.9]
T_04_END, T_PLAY = 7.0, 19.0
V_PLAY = BOX_H / T_PLAY
# 時間ステップで動きを積分（バネ・位相）
DT = 1.0 / 240
spring_cargo = {"x": 0.0, "v": 0.0}; spring_ant = {"x": 0.0, "v": 0.0}
phase = 0.0; sim = []; t = 0.0
prev_pitch_v = 0.0
while t <= T_END + 1e-9:
    x, v, a = robot_x(t)
    if v > 0.02: phase += v / stride(v) * DT
    # 荷物（荷台の上）：慣性で前後に滑る。f=2.2Hz、減衰比0.35、±7cm
    w_c, z_c = 2 * math.pi * 2.2, 0.35
    ac = -w_c * w_c * spring_cargo["x"] - 2 * z_c * w_c * spring_cargo["v"] - a
    spring_cargo["v"] += ac * DT; spring_cargo["x"] = clamp(spring_cargo["x"] + spring_cargo["v"] * DT, -0.07, 0.07)
    # アンテナ：根元の加速度で揺れる。f=2.5Hz、減衰比0.2
    w_a, z_a = 2 * math.pi * 2.5, 0.20
    aa = -w_a * w_a * spring_ant["x"] - 2 * z_a * w_a * spring_ant["v"] - 12.0 * a
    spring_ant["v"] += aa * DT; spring_ant["x"] += spring_ant["v"] * DT
    sim.append((t, x, v, a, phase, spring_cargo["x"], spring_ant["x"]))
    t += DT
def sim_at(t):
    i = min(len(sim) - 1, max(0, int(round(t / DT)))); return sim[i]

def pose_robot(t):
    tt, x, v, a, ph, cx, ant = sim_at(t)
    lam = stride(max(v, 0.05)) if v > 0.02 else 0.0
    walk = clamp(v / 0.4)
    offs, lifts = [], []
    for j in (0, 1):
        p = (ph + 0.5 * j) % 1.0
        if p < BETA:
            off = lam * BETA / 2 - lam * p; lift = 0.0
        else:
            q = (p - BETA) / (1 - BETA)
            off = -lam * BETA / 2 + lam * BETA * minjerk(q); lift = LIFT * math.sin(math.pi * q) * walk
        offs.append(off * walk); lifts.append(lift)
    # 倒立振子：立脚の足と腰の距離が脚長Lになる高さ
    hips = []
    for j in (0, 1):
        p = (ph + 0.5 * j) % 1.0
        if p < BETA: hips.append(math.sqrt(max(L_LEG ** 2 - offs[j] ** 2, 0.01)))
    hip_h = min(hips) if hips else L_LEG
    drop = L_LEG - hip_h
    # 横揺れ（ペンギンの歩き）：支えている脚の側へ±5°
    roll = -math.radians(5.0) * walk * math.cos(2 * math.pi * (ph - BETA / 2))
    # 前傾：加速度に比例 θ = atan(a/g)、歩行中は少し前へ
    lean = math.atan2(a, G) + math.radians(2.0) * walk
    # 待機の呼吸（約0.25Hz、±0.8cm）
    idle = 1 - walk
    breath = 0.008 * math.sin(2 * math.pi * 0.25 * t) * idle
    # おじぎ（荷物を滑らせる）：先に少し反る（予備動作）→ 前へ32°
    bow = mj(t, T_BOW0 - 0.16, T_BOW0, 0, -math.radians(4)) + mj(t, T_BOW0, T_BOW1, 0, math.radians(36)) \
        - mj(t, T_REL_BACK, T_REL_BACK + 0.55, 0, math.radians(32))
    look = mj(t, T_REL_BACK + 0.3, T_REL_BACK + 0.9, 0, math.radians(8)) + mj(t, T_05_END + 0.10, T_05_END + 0.28, 0, math.radians(6))
    sigh = -0.03 * pulse(t, T_RELIEF, 0.35, 0.15, 0.9)  # ほっと一息で沈む
    return dict(x=x, v=v, a=a, offs=offs, lifts=lifts, drop=drop, roll=roll, lean=lean, breath=breath,
                bow=bow, look=look, sigh=sigh, cargo_x=cx, ant=ant)

torso = O["Maru • torso"]; legs = [O["Maru • leg"], O["Maru • leg.001"]]; antenna = O["Maru • antenna"]
cradle = O["Maru • tilting delivery cradle"]; iris = O["Inner lens ring"]
ANT_REST = antenna.rotation_euler.copy(); IRIS_REST = iris.scale.copy()
def apply_robot(t, P):
    maru.location = (P["x"], 0.0, Z_DECK - 0.01 - P["drop"] + P["sigh"])  # 足裏が通路にぴったり接する
    maru.rotation_euler = Euler((-P["lean"], 0.0, -math.pi / 2), "XYZ")
    torso.location = (0, 0, 0.73 + P["breath"])
    torso.rotation_euler = Euler((-(P["bow"] + P["look"]), P["roll"], 0), "XYZ")
    for j, leg in enumerate(legs):
        off = P["offs"][j]; ang = math.atan2(off, L_LEG)
        leg.location = ((2 * j - 1) * HIP_X, 0, 0.43 + P["lifts"][j]); leg.rotation_euler = (ang, 0, 0)
    antenna.rotation_euler = (ANT_REST.x - 0.06 * P["ant"] - 0.5 * P["roll"], ANT_REST.y + 0.5 * P["roll"], ANT_REST.z)
    cradle.rotation_euler = (-mj(t, T_BOW0 + 0.1, T_BOW1, 0, math.radians(10)) + mj(t, T_REL_BACK, T_REL_BACK + 0.5, 0, math.radians(10)), 0, 0)
    bl = max([pulse(t, tb, 2 / FPS, 1 / FPS, 4 / FPS) for tb in BLINKS] + [0])
    s = 1 - 0.85 * bl; iris.scale = (IRIS_REST.x * s, IRIS_REST.y * s, IRIS_REST.z * s)

# ------------------------------------------------------------------ 物理：荷物（重力・反発・摩擦）
E_BOX = 0.30; MU_K = 0.28
events = []  # 音のための出来事（時刻, 種類, 強さ）
def fall_track(t0, z0, v0, z_floor, e=E_BOX, name=""):
    """自由落下と跳ね返り。返り値: 時刻→高さ の関数と、着地時刻"""
    segs = []; t, z, v = t0, z0, v0; first = True
    while True:
        # z(t') = z + v t' - g t'^2 / 2 = z_floor の正の解
        disc = v * v + 2 * G * (z - z_floor); dt = (v + math.sqrt(disc)) / G
        segs.append((t, z, v, dt)); t += dt; vin = v - G * dt
        events.append((t, "impact", abs(vin), name)); v = -vin * e; z = z_floor
        if v < 0.06 or not first and v < 0.12:
            break
        first = False
    t_rest = t
    def f(tq):
        if tq < t0: return z0
        for (ts, zs, vs, d) in segs:
            if tq <= ts + d: u = tq - ts; return zs + vs * u - G * u * u / 2
        return z_floor
    return f, t_rest

# 4番：再生中（一定の速さで沈む）
z04 = lambda t: (Z_SEAT - V_PLAY * (T_PLAY - T_04_END)) - V_PLAY * t
# 5番：扉の上で待つ → 扉が開いて座席へ落ちる → 再生
Z_REST = Z_GATE + 0.04
f05, t05_land = fall_track(T_04_END + 0.06, Z_REST, 0.0, Z_SEAT, e=0.25, name="05 seat")
T_05_PLAY = t05_land + 0.08; T_05_END = T_05_PLAY + T_PLAY
def z05(t):
    if t < T_05_PLAY: return f05(t)
    return Z_SEAT - V_PLAY * (t - T_05_PLAY)
events.append((T_04_END, "gate", 1.0, "open")); events.append((T_04_END + 0.45, "gate", 0.7, "close"))
events.append((T_05_END, "gate", 1.0, "open")); events.append((T_05_END + 0.45, "gate", 0.7, "close"))
def gate_angle(t):
    a = 0.0
    for t0 in (T_04_END, T_05_END):
        a = max(a, mj(t, t0 - 0.02, t0 + 0.10, 0, math.radians(82)) - mj(t, t0 + 0.32, t0 + 0.47, 0, math.radians(82)))
    return a

# 6番：荷台から滑り落ちて漏斗へ → タワーの底へ落ちる（シミュレーション）
def cradle_matrix_at(t):
    apply_robot(t, pose_robot(t)); bpy.context.view_layer.update(); return cradle.matrix_world.copy()
CARGO_LOCAL = Vector((0, 0, 0.38))
T_SLIDE0 = T_BOW0 + 0.22
slide = {"s": 0.0, "v": 0.0}; box6 = []  # (t, 位置, 回転y)
S_EDGE = 0.55; released = None
t = 0.0
while t <= T_END + 1e-9:
    if released is None:
        mw = cradle_matrix_at(t)
        fwd = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
        incline = math.asin(clamp(-fwd.z, -1, 1))  # 前下がりの角度
        if t >= T_SLIDE0 and incline > math.atan(0.35):
            acc = G * (math.sin(incline) - MU_K * math.cos(incline)); slide["v"] += acc * DT; slide["s"] += slide["v"] * DT
        pos = mw @ (CARGO_LOCAL + Vector((0, slide["s"], 0)))
        rot_y = math.atan2(fwd.z, fwd.x) * -1  # 荷台の傾きと同じだけ回る
        box6.append((t, pos.copy(), incline))
        if slide["s"] >= S_EDGE:
            vel = fwd * slide["v"]; released = (t, pos.copy(), vel, incline)
            events.append((t, "slide_off", slide["v"], "06"))
        t += DT; continue
    break
# 放物線 → 漏斗で中央へ寄せられる → 柱の中を落下
tr, p, vel, rot0 = released; p = p.copy(); vel = vel.copy(); rot = rot0; omega = 3.5; inside = False; t = tr
while t <= T_END and p.z > Z_COLTOP - 0.1:
    vel.z -= G * DT
    if p.z - BOX_H / 2 < Z_RIM + 0.05 and abs(p.x) < 0.95:  # 漏斗の内側：壁に押されて中央へ、姿勢もまっすぐに
        inside = True
        vel.x += (-60.0 * p.x - 12.0 * vel.x) * DT
        omega += (-80.0 * rot - 14.0 * omega) * DT
    else:
        pass
    rot += omega * DT; p += vel * DT; t += DT
    box6.append((t, p.copy(), rot))
t_enter, x_enter, vz_enter = t, p.x, vel.z
f06, t06_land = fall_track(t_enter, p.z - BOX_H / 2, vel.z, Z_REST, name="06 gate")
T_06_ARRIVE = t06_land
f06b, t06_seat = fall_track(T_05_END + 0.06, Z_REST, 0.0, Z_SEAT, e=0.25, name="06 seat")
T_06_PLAY = t06_seat + 0.08
def box6_at(t):
    if t <= box6[-1][0]:
        i = min(len(box6) - 1, max(0, int(round(t / DT)))); _, pp, rr = box6[i]; return pp, rr
    x_lock = x_enter * math.exp(-(t - t_enter) * 25.0)
    rr = box6[-1][2] * math.exp(-(t - t_enter) * 20.0)
    if t < T_05_END + 0.06: zb = f06(t)
    elif t < T_06_PLAY: zb = f06b(t)
    else: zb = Z_SEAT - V_PLAY * (t - T_06_PLAY)
    return Vector((x_lock, 0.0, zb + BOX_H / 2)), rr
print(f"TIMING stop={T_STOP:.2f} slide={T_SLIDE0:.2f} release={released[0]:.2f} enter={t_enter:.2f} land06={T_06_ARRIVE:.2f} 05end={T_05_END:.2f} 06play={T_06_PLAY:.2f}")

# ------------------------------------------------------------------ 光の切り替え（基本A ↔ 山場C）
T_C0, T_C1 = 9.9, T_06_ARRIVE
def c_amount(t): return mj(t, T_C0, T_C0 + 0.7, 0, 1) - mj(t, T_C1, T_C1 + 0.8, 0, 1)
def apply_lights(t):
    c = c_amount(t)
    sun_key.data.energy = 4.0 * (1 - c) + 0.3 * c; sun_fill.data.energy = 1.6 * (1 - c) + 0.12 * c
    # 空は固定（毎コマの空の光の計算を避ける）。夜の暗さは露出で作り、スポットはその分強くする
    scene.view_settings.exposure = -2.5 * c; boost = 2 ** (2.5 * c)
    haze_d.default_value = 0.012 * c
    rx = robot_x(t)[0]; spot_robot.location = (rx, -0.4, Z_DECK + 4.2); aim(spot_robot, (rx, 0, Z_DECK + 0.6))
    spot_robot.data.energy = 1800.0 * c * boost; spot_tower.data.energy = 1300.0 * c * boost
    hl04.data.energy = 90.0 * pulse(t, 0.9, 0.35, 0.8, 0.5); hl05.data.energy = 90.0 * pulse(t, 3.1, 0.35, 0.9, 0.5)
    emit_input(green).default_value = 5.0 * mj(t, T_RELIEF - 0.1, T_RELIEF + 0.5, 0, 1)
    emit_input(label_mat).default_value = 3.0 * mj(t, T_RELIEF - 0.1, T_RELIEF + 0.5, 0, 1)
    s = 0.0 if t < T_RELIEF - 0.12 else 0.85 + 0.15 * mj(t, T_RELIEF - 0.1, T_RELIEF + 0.5, 0, 1); label.scale = (s, s, s); plate.scale = (s, s, s)
    # 使っていない光とかすみは止める（描画時間の節約）
    for lo in (hl04, hl05, spot_robot, spot_tower): lo.hide_render = lo.data.energy < 1e-3
    haze.hide_render = c < 0.01

def apply_world(t):
    apply_robot(t, pose_robot(t))
    boxes["04"].location = (0, 0, z04(t) + BOX_H / 2); boxes["04"].scale = (1, 1, 1) if t < T_04_END else (0, 0, 0)
    boxes["05"].location = (0, 0, z05(t) + BOX_H / 2); boxes["05"].scale = (1, 1, 1) if t < T_05_END else (0, 0, 0)
    vis06 = t >= T_IN - 0.5
    p6, r6 = box6_at(t); boxes["06"].location = p6; boxes["06"].rotation_euler = (0, r6, 0); boxes["06"].scale = (1, 1, 1) if vis06 else (0, 0, 0)
    ga = gate_angle(t); flapL.rotation_euler = (0, ga, 0); flapR.rotation_euler = (0, -ga, 0)
    cone.location = (0, -0.64 + 0.012 * math.sin(2 * math.pi * 5 * t), 0.5)
    for i, (rg, rm) in enumerate(zip(rings, ring_mats)):
        k = math.floor((t - i * 0.5) / 2.5); age = t - (k * 2.5 + i * 0.5)
        u = clamp(age / 1.2); vis = 0 <= age <= 1.2
        sc = 1.0 + 1.1 * u; rg.scale = (sc, sc, sc) if vis else (0, 0, 0)
        rg.location = (0, -0.7 - 0.9 * u, 0.5); emit_input(rm).default_value = 2.5 * (1 - u) ** 2 * 2 ** (2.5 * c_amount(t)) if vis else 0.0
    apply_lights(t)
    p, q = cam_at(t); cam.location = p; cam.rotation_euler = (q - p).to_track_quat("-Z", "Y").to_euler()

# ------------------------------------------------------------------ 描画設定
ee = scene.eevee; scene.render.engine = "BLENDER_EEVEE_NEXT"; ee.taa_render_samples = A.samples
ee.use_shadows = True; ee.use_raytracing = False
if hasattr(ee, "shadow_resolution_scale"): ee.shadow_resolution_scale = 1.0 if A.final else 0.5
for k, v in (("volumetric_start", 0.1), ("volumetric_end", 120.0), ("volumetric_samples", 48), ("use_volumetric_shadows", True)):
    if hasattr(ee, k): setattr(ee, k, v)
scene.render.use_motion_blur = (os.environ.get("BS_BLUR","1")=="1"); scene.render.motion_blur_shutter = 0.5
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0.0
scene.render.resolution_x, scene.render.resolution_y = A.res; scene.render.resolution_percentage = 100
scene.render.fps = FPS; scene.render.image_settings.file_format = "PNG"; scene.render.film_transparent = False

# ------------------------------------------------------------------ 実行
KEY_OBJS = [maru, torso, antenna, cradle, iris, *legs, *boxes.values(), flapL, flapR, cone, *rings, cam, label, plate, spot_robot]
def key_frame(f):
    for ob in KEY_OBJS:
        ob.keyframe_insert("location", frame=f); ob.keyframe_insert("rotation_euler", frame=f); ob.keyframe_insert("scale", frame=f)
    for ld in (sun_key.data, sun_fill.data, hl04.data, hl05.data, spot_robot.data, spot_tower.data): ld.keyframe_insert("energy", frame=f)
    for ob in (hl04, hl05, spot_robot, spot_tower, haze): ob.keyframe_insert("hide_render", frame=f)
    scene.view_settings.keyframe_insert("exposure", frame=f)
    for inp in (haze_d, emit_input(green), emit_input(label_mat), *[emit_input(m) for m in ring_mats]):
        inp.keyframe_insert("default_value", frame=f)

log = []
if A.mode == "layout":
    for tq in (0.0, 3.4, 9.0, 12.6, T_STOP, 15.5, 25.6):
        apply_world(tq); bpy.context.view_layer.update()
        pts = {"robot": maru.matrix_world.translation + Vector((0, 0, 0.9)), "box06": boxes["06"].location, "gate": Vector((0, 0, Z_GATE)),
               "label": label.location, "speaker": Vector((0, -0.64, 0.5)), "deck_left": Vector((-7.5, 0, Z_DECK))}
        s = " ".join(f"{k}=({c.x:.2f},{c.y:.2f})" for k, c in ((k, world_to_camera_view(scene, cam, v)) for k, v in pts.items()))
        print(f"LAYOUT t={tq:.1f} {s}")
    sys.exit(0)

if A.mode == "stills":
    for tq in [float(x) for x in A.still_times.split(",")]:
        apply_world(tq); bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(A.out, f"buffer_still_{tq:05.1f}.png"); bpy.ops.render.render(write_still=True)
        print("STILL", scene.render.filepath)
    sys.exit(0)

# anim：全フレームにキーを打ってから描画
f0, f1 = [int(x) for x in A.frames.split(":")]
prev_p = [0.5, 0.0]
for f in range(1, NF + 1):
    tq = (f - 1) / FPS; apply_world(tq); key_frame(f)
    P = pose_robot(tq)
    ph = sim_at(tq)[4]
    for j in (0, 1):  # 足が着いた瞬間（立脚の始まり）を足音として記録
        pj = (ph + 0.5 * j) % 1.0
        if prev_p[j] > 0.8 and pj < 0.2 and P["v"] > 0.3: events.append((tq, "step", P["v"], f"leg{j}"))
        prev_p[j] = pj
    log.append(dict(t=tq, x=P["x"], v=P["v"], a=P["a"], lean_deg=math.degrees(P["lean"]), roll_deg=math.degrees(P["roll"]),
                    drop_cm=100 * P["drop"], cargo_cm=100 * P["cargo_x"], antenna=P["ant"], bow_deg=math.degrees(P["bow"]),
                    z04=z04(tq), z05=z05(tq), z06=boxes["06"].location.z - BOX_H / 2, c=c_amount(tq)))
for ob in KEY_OBJS:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
json.dump(dict(log=log, events=sorted(events), timing=dict(stop=T_STOP, release=released[0], land06=T_06_ARRIVE, end05=T_05_END,
          play06=T_06_PLAY, c0=T_C0, c1=T_C1, relief=T_RELIEF)), open(os.path.join(A.out, "motion_log.json"), "w", encoding="utf-8"), ensure_ascii=False)
scene.frame_start, scene.frame_end = f0, f1
if A.video:  # PC用：Blenderから直接mp4（H.264）で書き出す
    scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
    ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "HIGH"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
    scene.render.filepath = os.path.join(A.out, "buffer_sample_")
else:
    scene.render.filepath = os.path.join(A.out, "frames", "f_"); scene.render.use_overwrite = False; scene.render.use_placeholder = True
bpy.ops.render.render(animation=True)
print("ANIM_DONE")
