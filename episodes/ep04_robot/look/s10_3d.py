# 見本：S10「人とプログラムの比べっこ」（3:33〜4:05）を 3D で（2026-11-14 ユーザー「図の場面も 3D で作る」「3D も作り込む」）
# blender -b --factory-startup --python s10_3d.py -- <出力フォルダ> [samples] [--res W H] [--step N] --tex <絵>
#   画面の中の世界に、光るふちの台を 2 つ。左＝人（オレンジ）、右＝プログラム（青緑の画面の機械）。
#   台の後ろのガラスの柱に「正解」の光がたまる。台の上の時計の針が「時間」を回る。まるロボはまん中で見比べ、最後に跳ねる。
#   字は 3D に書かない（「人」「5〜8割」などは 2D の札。log の track の場所に置く）。光のにじみ（Glare）・ピント・カメラはゆっくり寄る
import os, sys, math
ARGS = sys.argv[sys.argv.index("--") + 1:]
_ANIM_HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "anim")
def opt(name, default):
    return [type(d)(ARGS[ARGS.index(name) + 1 + k]) for k, d in enumerate(default)] if name in ARGS else default
TEX, = opt("--tex", [os.path.join(_ANIM_HERE, "..", "storyboard", "tex")])
OUTDIR = ARGS[0]; N_SAMPLES = int(ARGS[1]) if len(ARGS) > 1 and ARGS[1].isdigit() else 32
RESX, RESY = opt("--res", [1920, 1080]); STEP, = opt("--step", [1]); TRACK_ONLY = "--track-only" in ARGS
exec(open(os.path.join(_ANIM_HERE, "common.py"), encoding="utf-8").read())
import bpy

T0, T1 = said("2023年には") - 0.4, said("では、どうやって") - 0.05
CLOCK["T0"] = T0
t_y, t_who, t_res, t_fast, t_hum, t_hsec, t_wow = (said("2023年には"), said("ゆがんだ文字のテストを"), said("結果は"),
                                                  said("しかも、1問"), said("人は、正解"), said("1問に、9秒"), said("なんと"))
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 0, round((T1 - T0) * FPS)

# ---------- 舞台：画面の中の世界（門も門番もなし）
screen_world(gate=False, gatekeeper=False)
OR, TE = "#FF8A2A", "#2CD3C2"
XL, XR, Y = -2.3, 2.3, 4.2


def podium(x, col, name):
    base = mat("pod_" + name, "#1E3352", rough=0.25, coat=0.6)
    cyl(base, (x, Y, 0.18), 1.25, 0.36)
    cyl(mat("pod_top_" + name, "#E9F1F7", rough=0.3), (x, Y, 0.37), 1.12, 0.03)
    rim = mat("rim_" + name, col, emit=5.0)
    bpy.ops.mesh.primitive_torus_add(location=(x, Y, 0.37), major_radius=1.18, minor_radius=0.025)
    o = bpy.context.object; o.data.materials.append(rim)
    # 床に落ちる色の光
    bpy.ops.object.light_add(type='POINT', location=(x, Y - 0.6, 0.9)); L = bpy.context.object
    L.data.energy = 120; L.data.color = srgb(col)[:3]; L.data.shadow_soft_size = 0.8
    return rim


def person(x):
    skin = mat("p_skin", "#F6D4B8", rough=0.55); shirt = mat("p_shirt", "#3E7CB1", rough=0.5)
    hair = mat("p_hair", "#46342C", rough=0.6); pants = mat("p_pants", "#2B3A55", rough=0.6)
    root = empty((x, Y, 0.38))
    for sx in (-0.13, 0.13): cyl(pants, (x + sx, Y, 0.38 + 0.32), 0.1, 0.64)
    cyl(shirt, (x, Y, 1.25), 0.3, 0.62); sphere(shirt, (x, Y, 1.55), 0.3, scale=(1, 0.8, 0.45))
    sphere(shirt, (x, Y, 0.95), 0.3, scale=(1, 0.85, 0.35))
    for sx in (-0.37, 0.37): cyl(shirt, (x + sx, Y, 1.2), 0.08, 0.55, rot=(0, R(8 if sx < 0 else -8), 0))
    for sx in (-0.4, 0.4): sphere(skin, (x + sx, Y, 0.9), 0.08)
    cyl(skin, (x, Y, 1.72), 0.07, 0.14)
    head = sphere(skin, (x, Y, 1.98), 0.25)
    sphere(hair, (x, Y + 0.03, 2.05), 0.262, scale=(1, 1, 0.82))
    sphere(skin, (x, Y - 0.04, 1.95), 0.245)
    for sx in (-0.08, 0.08): sphere(mat("p_eye", "#1B2233", rough=0.2), (x + sx, Y - 0.24, 1.98), 0.028)
    return head


def program(x):
    body = mat("pg_body", "#DCE6EE", rough=0.3, coat=0.5); dark = mat("pg_dark", "#1E3352", rough=0.3)
    cube(body, (x, Y, 1.25), (1.3, 0.55, 0.95), bevel=0.12)
    cube(dark, (x, Y - 0.24, 1.25), (1.1, 0.1, 0.75), bevel=0.06)
    scr = mat("pg_screen", TE, emit=2.2)
    cube(scr, (x, Y - 0.3, 1.25), (1.0, 0.02, 0.65), bevel=0.02)
    cyl(body, (x, Y, 0.62), 0.09, 0.5); cyl(body, (x, Y, 0.42), 0.4, 0.06)
    # 目の代わりの 3 つの点（考え中に順に光る）
    dots = []
    for k in range(3):
        m = bpy.data.materials.new("pg_dot%d" % k); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (1, 1, 1, 1)
        b.inputs["Emission Color"].default_value = (1, 1, 1, 1); b.inputs["Emission Strength"].default_value = 1.0
        o = sphere(m, (x - 0.25 + k * 0.25, Y - 0.33, 1.25), 0.07); dots.append(m)
    return dots


def tube(x, col, name):
    glass = mat("glass_" + name, "#CFE9F5", rough=0.05, trans=0.95, alpha=0.35)
    cx = x + (1.75 if x > 0 else -1.75)
    cyl(glass, (cx, Y + 0.3, 1.7), 0.32, 3.0)
    cyl(mat("tcap_" + name, "#1E3352", rough=0.3), (cx, Y + 0.3, 0.12), 0.42, 0.24)
    cyl(mat("tcap_" + name, "#1E3352", rough=0.3), (cx, Y + 0.3, 3.24), 0.38, 0.1)
    liq = cyl(mat("liq_" + name, col, emit=2.8, alpha=0.9), (cx, Y + 0.3, 0.24), 0.27, 1.0)
    liq.scale = (1, 1, 0.001); liq.location.z = 0.24
    for k in range(1, 10):                         # 目盛り
        z = 0.24 + 2.9 * k / 10
        bpy.ops.mesh.primitive_torus_add(location=(cx, Y + 0.3, z), major_radius=0.325, minor_radius=0.006)
        bpy.context.object.data.materials.append(mat("tick", "#FFFFFF", emit=0.8))
    return liq, cx


def fill(liq, t, frac, d=1.2):
    H = 2.9
    key(liq, ("scale", 2), f(t), liq.scale[2]); key(liq, ("location", 2), f(t), liq.location.z)
    liq.scale[2] = max(frac * H, 0.001); liq.location.z = 0.24 + frac * H / 2
    key(liq, ("scale", 2), f(t + d), liq.scale[2]); key(liq, ("location", 2), f(t + d), liq.location.z)


def clock(x, z=2.75):
    face = mat("clk_face", "#F4F8FB", rough=0.3); ring = mat("clk_ring", "#1E3352", rough=0.3)
    cx = x; yy = Y + 0.3
    cyl(ring, (cx, yy, z - 0.42), 0.05, 0.3)
    o = cyl(ring, (cx, yy, z), 0.42, 0.08, rot=(R(90), 0, 0))
    cyl(face, (cx, yy - 0.05, z), 0.36, 0.02, rot=(R(90), 0, 0))
    piv = empty((cx, yy - 0.07, z)); piv.rotation_euler = (0, 0, 0)
    hand = cube(mat("clk_hand", "#E24C42", emit=0.6), (cx, yy - 0.07, z + 0.14), (0.04, 0.01, 0.3), parent=None)
    hand.parent = piv; hand.location = (0, 0, 0.14)
    root = empty((cx, Y - 0.1, z)); return piv


podium(XL, OR, "L"); podium(XR, TE, "R")
head = person(XL); dots = program(XR)
liqL, cxL = tube(XL, OR, "L"); liqR, cxR = tube(XR, TE, "R")
clkL = clock(cxL, 3.85); clkR = clock(cxR, 3.85)   # 時計はガラスの柱の上
for piv, t_, dur, turns in ((clkR, t_fast + 0.2, 0.8, 1.0), (clkL, t_hsec + 0.2, 2.6, 2.0)):
    key(piv, ("rotation_euler", 1), f(t_), 0.0); key(piv, ("rotation_euler", 1), f(t_ + dur), R(360 * turns))
# 出るのは「人とプログラムに」で
for prefix, t_ in (("p_", t_who - 0.1), ("pg_", t_who + 0.3)):
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and o.active_material and o.active_material.name.startswith(prefix)]
    for o in obs:
        s0 = o.scale.copy()
        key(o, "scale", f(T0), (0.001, 0.001, 0.001)); key(o, "scale", f(t_), (0.001, 0.001, 0.001))
        key(o, "scale", f(t_ + 0.3), tuple(v * 1.08 for v in s0)); key(o, "scale", f(t_ + 0.45), tuple(s0))
ev(t_who - 0.1, "pop_ui"); ev(t_who + 0.3, "pop_ui")
# プログラム：考え中の点 → 正解がたまる
for k, m in enumerate(dots):
    for j in range(5):
        tt = t_res + 0.2 + j * 0.3 + k * 0.1
        matkey(m, f(tt), 1.0); matkey(m, f(tt + 0.08), 6.0); matkey(m, f(tt + 0.2), 1.0)
fill(liqR, t_res + 1.3, 0.97, 0.9); ev(t_res + 1.3, "pop_ui")
fill(liqL, t_hum + 0.3, 0.5, 1.0); fill(liqL, t_hum + 1.5, 0.8, 1.4)
# ---------- まるロボ：まん中の手前で見比べる
root = maru((0, 2.4, 0), face_deg=90, s=0.75, hat=False, eye_glow=1.0, look_up=12)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.1, face=20, look=12)
mr.at(t_who - 0.1, face=-70); mr.at(t_who + 0.4, face=80)
mr.at(t_res, face=85, look=16); mr.at(t_hum, face=-80, look=16)
mr.at(t_wow - 0.2, face=10, look=8)
mr.hop(t_wow + 0.1, 0.35, 0.45); mr.hop(t_wow + 0.65, 0.25, 0.4); ev(t_wow + 0.1, "jump"); ev(t_wow + 0.55, "land")
mr.glow(t_wow + 0.1, 1.0, 2.6, 0.2); mr.glow(t_wow + 1.4, 2.6, 1.0, 0.6)
# 息
t = T0 + 0.6
while t < T1 - 1:
    if not (t_wow - 0.5 < t < t_wow + 1.6):
        key(mr.body, ("location", 2), f(t), mr.z0); key(mr.body, ("location", 2), f(t + 0.45), mr.z0 + 0.02); key(mr.body, ("location", 2), f(t + 0.9), mr.z0)
    t += 1.8
# ---------- カメラ：ゆっくり寄りながら少し回る。ピントは台のあたり
for o in list(bpy.data.objects):
    if o.type == 'CAMERA': bpy.data.objects.remove(o)
cam = camera((0.9, -6.8, 3.4), (0, Y, 1.4), 30)
tgt = empty((0, Y, 1.4));
for o in cam.constraints: cam.constraints.remove(o)
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
key(cam, "location", f(T0), (1.0, -7.6, 3.7)); key(cam, "location", f(T1), (-0.6, -6.3, 3.1))
key(tgt, "location", f(T0), (0, Y, 1.9)); key(tgt, "location", f(T1), (0, Y, 1.7))
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = 3.2
sc.camera = cam
# ---------- 光のにじみ
sc.use_nodes = True; nt = sc.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
rl = nt.nodes.new("CompositorNodeRLayers"); gl = nt.nodes.new("CompositorNodeGlare"); co = nt.nodes.new("CompositorNodeComposite")
gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'; gl.threshold = 0.9; gl.size = 8; gl.mix = -0.3
nt.links.new(rl.outputs["Image"], gl.inputs["Image"]); nt.links.new(gl.outputs["Image"], co.inputs["Image"])
# ---------- 札の場所（2D）
TRACK["maru"] = (mr.body, 0.6); TRACK["L_top"] = (head, 0.45)
an = empty((XR, Y, 1.85)); TRACK["R_top"] = (an, 0.0)
aL = empty((cxL, Y + 0.3, 1.9)); TRACK["L_tube"] = (aL, 0.0)
aR = empty((cxR, Y + 0.3, 1.9)); TRACK["R_tube"] = (aR, 0.0)
cL = empty((cxL, Y + 0.3, 3.85)); TRACK["L_clock"] = (cL, 0.0)
cR = empty((cxR, Y + 0.3, 3.85)); TRACK["R_clock"] = (cR, 0.0)
render("s10", T0, T1, OUTDIR, N_SAMPLES, (RESX, RESY), STEP)
print("S10DONE")
