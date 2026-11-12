# 第4章 D7「ペアリング」の3D（本編 4:07.6〜4:24.4。その前の 4:04.6〜 は 2D のペアリング画面）：絵の具を混ぜて、同じ色の鍵を作る（鍵そのものは送らない）
#   スマホの台（左）とイヤホンの台（右）。みんなが知っている色（白）をタンクから両方のバケツへ → それぞれ自分のひみつの色を足す（青・赤）
#   → スマホの台のクレーンが水色のバケツをまるロボの背中へ → まるロボがイヤホンの台へ運ぶ → クレーンが受け取り、桃色のバケツを背中へ
#   → まるロボが持ち帰る → 受け取った側がそれぞれ自分のひみつの色を足す → どちらも同じ藤色 → 色が鍵の型に満ちて、鍵ができ、鍵穴へ
#   イヤホンの側の鍵が先、スマホの側があと（鍵は二台がそれぞれ作る）。運ばれたのは混ぜた色だけ（隣のイヤホンには同じ色は作れない）
#   物理：まるロボは marumotion（歩く・止まる・向きを変える）。クレーンは伸び縮みする硬い棒で吊るので振れない（kit.hoist rigid）。背中や吊ったバケツの液面は加速で揺れる（kit.carry.slosh）
#   時刻は、まるロボの動きを計算した結果（着いた時刻）から、クレーン・注ぐ・型の時刻を決める
# 使い方: blender -b story.blend --python ch04_pairing.py -- --out DIR [--engine workbench|eevee] [--res W H] [--samples N] [--still 秒,秒] [--frames A:B]
import bpy, sys, os, math, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); STAGE = os.path.abspath(os.path.join(HERE, ".."))
for p_ in (HERE, STAGE, os.path.join(STAGE, "maru"), os.path.join(STAGE, "human")):
    if p_ not in sys.path: sys.path.insert(0, p_)
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
import marumotion as mm, marurig as mr
from kit import world as kw, props as kp, carry as kc, colormix as cm
from kit.hoist import Hoist

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/ch04_pairing"); ap.add_argument("--engine", default="workbench"); ap.add_argument("--res", nargs=2, type=int, default=[640, 360])
ap.add_argument("--samples", type=int, default=16); ap.add_argument("--still", default=""); ap.add_argument("--frames", default="")
ap.add_argument("--sun", type=float, default=-55.0); ap.add_argument("--sun_el", type=float, default=48.0); ap.add_argument("--exposure", type=float, default=0.0)
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
scene = bpy.context.scene; O = bpy.data.objects
FPS = 24; T0S, T1S = 247.60, 264.40; N = int(round((T1S - T0S) * FPS)) + 1
def TL(t): return t - T0S                                   # 本編の秒 → この場面の秒（まるロボの予定の時計）
def FR(t): return int(round((t - T0S) * FPS)) + 1           # 本編の秒 → コマ


def mjv(u): u = min(max(u, 0.0), 1.0); return u * u * u * (10 - 15 * u + 6 * u * u)
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out


# ================================================================ Codex版から使う物だけ（まるロボ・イヤホン・スマホ）
scene.frame_set(1)
keep = set()
for n_ in ("Maru", "Earbud exterior", "Smartphone exterior"): keep |= set(hier(O[n_]))
for ob in list(O):
    if ob not in keep: O.remove(ob, do_unlink=True)
for ob in keep:
    if ob.animation_data and ob.name not in [x.name for x in hier(O["Maru"])]:
        mb = ob.matrix_basis.copy(); hr = ob.hide_render; ob.animation_data_clear(); ob.matrix_basis = mb; ob.hide_render = hr
for coll_ in (bpy.data.materials, bpy.data.worlds, bpy.data.lights):
    for idb in coll_:
        if getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt_ = getattr(idb, "node_tree", None)
        if nt_ and nt_.animation_data: nt_.animation_data_clear()
maru = O["Maru"]; earbud_old = O["Earbud exterior"]; phone = O["Smartphone exterior"]

# ================================================================ 配置（m）。まるロボは y＝0 の線を歩く。台は線の後ろ（+y）
X_P, X_E = -1.00, 1.00                     # スマホの台・イヤホンの台（まるロボが止まる所の x）
TABLE_Z = 0.95; B_Y, A_Y = 0.80, 1.20      # 台の高さ、送るバケツの所（B）・受け取るバケツの所（A）
Z_BEAM = 2.65; RAIL = (-0.45, 1.62)        # クレーンの梁の高さ・レールの範囲（y）。柱は後ろだけ（片持ち）
TANK = (0.0, 2.45)
INNER = {"P": 1.0, "E": -1.0}              # 台の内側（真ん中の向き）
KEY_S = 1.6                                # 鍵の大きさ（見やすく）
KEY_FLY = 0.88                             # 鍵が型を出てから錠に差さるまで（秒）
KEY_OUT = 0.25                             # 差したとき、鍵の輪の中心が錠の上の面から出ている高さ（m）
XS = {"P": X_P, "E": X_E}

# ================================================================ まるロボの予定（背中に受け皿とトレー。荷物の箱は使わない）
G0 = dict(lamps=247.70, white=247.88, secret1=248.55, load_p=249.45)    # 前半の時刻（本編の秒）。2D のペアリング画面から入ってすぐ
T_GO = G0["load_p"] + 1.20                                                # 水色のバケツが背中に載ったら走り出す
V_GO = mm.V_RUN                                                           # 走る（2.0m/s。20秒足らずで往復するので）


def make_plan(xp_back):
    q = mm.Plan(pos=(X_P, 0.0), heading=-90.0, carry=True, seed=12)     # +x を向いて、スマホの台の前に立つ
    q.idle(TL(T_GO), shifts=False, glance=False)
    q.run_to((X_E, 0.0), speed=V_GO, label="水色のバケツを運ぶ"); t_arr_e = q.t
    q.idle(0.50, shifts=False, glance=False)                              # クレーンが水色のバケツを持ち上げる
    q.turn_to(heading=90.0, step=0.22, gap=0.03); t_turn = q.t            # 急いで向きを変える間に、クレーンが桃色のバケツを取ってくる
    q.idle(0.50, shifts=False, glance=False)                              # 桃色のバケツが背中に載る
    q.run_to((xp_back, 0.0), speed=V_GO, label="桃色のバケツを持ち帰る"); t_arr_p = q.t
    q.idle(max(TL(T1S) + 0.5 - q.t, 0.1), shifts=False, glance=True)
    return q, t_arr_e, t_turn, t_arr_p


rig = mr.MaruRig(maru)
plan, tE, tTurn, tP = make_plan(X_P)
frames = mm.simulate(plan, fps=FPS)
def tray_top(f):
    """f コマ目（1から）のトレーの上面の中心（世界）"""
    W_ = rig.world_mats(frames[min(f - 1, len(frames) - 1)]); return W_["cargo"] @ Vector((0, 0, rig.TRAY_TOP))
x0 = tray_top(1).x; x1 = tray_top(int(round((tP + 0.6) * FPS)) + 1).x
plan, tE, tTurn, tP = make_plan(X_P + (x0 - x1))                       # 帰りは、トレーの中心が行きと同じ所に来るように止まる
frames = mm.simulate(plan, fps=FPS)
T_ARR_E, T_TURN, T_ARR_P = T0S + tE, T0S + tTurn, T0S + tP
print("PLAN arrive E %.2f  turn %.2f  arrive P %.2f  frames %d" % (T_ARR_E, T_TURN, T_ARR_P, len(frames)), flush=True)
xa_, xb_ = tray_top(FR(T_ARR_E) + 6).x, tray_top(FR(T_TURN) + 3).x       # 向きを変える前と後のトレーの位置（受け皿の軸が体の中心から 2cm ずれている）
RAIL_X = {"P": tray_top(1).x, "E": 0.5 * (xa_ + xb_)}                    # クレーンの梁はトレーの真上
TRAY_Y = {"P": tray_top(1).y, "E": tray_top(FR(T_ARR_E) + 6).y}
print("TRAY x before/after turn %.3f %.3f" % (xa_, xb_), flush=True)

# ================================================================ 材質
m_frame = kw.mat("Station frame", kw.srgb("#5C6168"), 0.4, 0.7); m_cable = kw.mat("Cable", kw.srgb("#2E3236"), 0.5, 0.6)
m_top = kw.mat("Station top", kw.srgb("#D9DDE1"), 0.45, 0.0, coat=0.2); m_leg = kw.mat("Station leg", kw.srgb("#4A4F55"), 0.5, 0.5)
m_teal = kw.mat("Station teal", kw.srgb("#1F5E66"), 0.35, 0.6); m_dark = kw.mat("Station dark", kw.srgb("#1A1E22"), 0.7)
m_pail = kp.clear_mat("Pail clear", kw.srgb("#E6ECEF"), alpha=0.28); m_trim = kw.mat("Pail trim", kw.srgb("#AEB4BA"), 0.3, 0.8)
m_glass = kp.clear_mat("Jar glass", kw.srgb("#EEF4F6"), alpha=0.25, rough=0.06)
m_tank = kw.mat("Tank", kw.srgb("#E4E7EA"), 0.3, 0.3, coat=0.3); m_amber = kw.mat("Neighbor amber", kw.srgb("#D6802C"), 0.4, 0.2)
PIG = dict(cm.PIGMENTS); cm.PIGMENTS.update(PIG)
WHITE, BLUE, RED = cm.Paint(白=1.0), cm.Paint(青=0.8), cm.Paint(赤=0.8)
C_WHITE = WHITE.linear(); C_SEND_P = (WHITE + BLUE).linear(); C_SEND_E = (WHITE + RED).linear(); C_KEY = (WHITE + BLUE + RED).linear()
C_BLUE = cm.Paint(青=1).linear(); C_RED = cm.Paint(赤=1).linear()
assert (WHITE + BLUE + RED).same_as((WHITE + RED) + BLUE)
m_white_paint = kp.paint_mat("Common white paint", C_WHITE); m_blue = kp.paint_mat("Secret blue", C_BLUE); m_red = kp.paint_mat("Secret red", C_RED)

# ================================================================ 床・空・太陽
floor = kw.box("Ground", (120.0, 120.0, 0.02), kw.slate_material()); floor.location = (0, 20.0, -0.01)
sun, SUN_DIR = kw.sky_and_sun(scene, az_deg=A.sun, el_deg=A.sun_el, sky_strength=0.10, sun_energy=4.0)

# ================================================================ 台（2つ）：台・クレーン・ひみつの色の小びん・鍵の型・鍵穴
ST = {}
for k, col_secret, m_secret in (("P", C_BLUE, m_blue), ("E", C_RED, m_red)):
    X = RAIL_X[k]; inner = INNER[k]
    TW = 1.40; TX = X + inner * 0.15                                     # 台は内側へ広い（型と錠を、バケツ・白い管から離して置く）
    t_ = kp.table("Table " + k, TW, 0.90, TABLE_Z, m_top, m_leg); t_.location = (TX, 1.00, 0)
    stripe = kw.box("Table stripe " + k, (TW, 0.012, 0.06), m_teal); stripe.location = (TX, 0.546, TABLE_Z - 0.07)
    h = kp.hoist("Hoist " + k, RAIL[0], RAIL[1], Z_BEAM, m_frame, m_frame, posts=(1,), rod=True); h["root"].location = (X, 0, 0)
    ja = kp.jar_arm("Jar " + k, m_frame, m_glass, m_secret); ja["root"].location = (X - inner * 0.42, 1.00, TABLE_Z)
    md = kp.key_mold("Mold " + k, m_top, m_dark, kp.paint_mat("Mold paint " + k, C_KEY), s=KEY_S); md["root"].location = (X + inner * 0.52, 1.18, TABLE_Z)
    md["root"].rotation_euler = (0, 0, math.pi if inner < 0 else 0.0)
    kw.box("Channel " + k, (0.20, 0.05, 0.02), m_frame).location = (X + inner * 0.20, A_Y + 0.02, TABLE_Z + 0.01)   # A の所 → 型
    kh = kp.lock_box("Lock " + k, m_teal, m_top, m_dark, s=1.4); kh["root"].location = (X + inner * 0.72, 0.72, TABLE_Z)   # 台の上、内側の手前の角（まるロボの陰にならない）
    ring = kw.torus("Tray ring " + k, 0.185, 0.012, m_frame)            # バケツの受け台（台の上の B と A）
    ring.location = (X, B_Y, TABLE_Z + 0.012)
    ring2 = kw.torus("Spot A ring " + k, 0.185, 0.012, m_frame); ring2.location = (X, A_Y, TABLE_Z + 0.012)
    ST[k] = dict(X=X, inner=inner, hoist=h, jar=ja, mold=md, keyhole=kh, secret=col_secret)

# まるロボのトレーの上の受け台（バケツが滑らない輪）
cargo_ring = kw.torus("Cargo ring", 0.19, 0.014, m_frame)

# ================================================================ みんなが知っている色のタンクと管（白）
tk = kp.tank("Common tank", m_tank, m_leg, m_white_paint, height=1.55); tk["root"].location = (TANK[0], TANK[1], 0)
SPOUT = {}
for k in ("P", "E"):
    X = ST[k]["X"]; inner = ST[k]["inner"]; sx = X + inner * 0.24
    pts = [(TANK[0], TANK[1], 1.55), (TANK[0], TANK[1], 1.42), (sx, TANK[1], 1.42), (sx, B_Y + 0.12, 1.42), (sx, B_Y + 0.04, 1.62)]
    kw.tube("Pipe " + k, pts, 0.035, m_tank)
    sp = kw.cyl("Spout " + k, 0.03, 0.08, m_frame, 16); sp.location = (sx, B_Y, 1.62)
    st_ = kw.cyl("White stream " + k, 0.014, 1.0, m_white_paint, 12)
    for v in st_.data.vertices: v.co.z -= 0.5
    st_.hide_render = True
    SPOUT[k] = dict(p=Vector((sx, B_Y, 1.58)), stream=st_)

# ================================================================ ペアリングの灯（地面。スマホの台からイヤホンの台へ、順に灯る）
LAMPS = kp.lamps("Pairing lamp", (X_P - 0.3, -0.75), (X_E + 0.3, -0.75), 7, m_frame)

# ================================================================ バケツ（A＝スマホが送る水色、B＝イヤホンが送る桃色）
BK = {}
for nm_, k0 in (("A", "P"), ("B", "E")):
    pm = kp.paint_mat("Bucket paint " + nm_, C_WHITE)
    BK[nm_] = kp.bucket("Bucket " + nm_, m_pail, pm, m_trim); BK[nm_]["home"] = k0

# ================================================================ 背景：巨大スマホ（左の台の後ろ）・巨大イヤホン（右の台の後ろ）・隣のイヤホン（遠く、橙の帯）
bpy.context.view_layer.update()
ph_parts = [o for o in hier(phone) if o.type == "MESH"]
PHONE_C = Vector((-10.0, -6.0, 0.04))
zs = [(o.matrix_world @ Vector(c)).z for o in ph_parts for c in o.bound_box]; ph_h = max(zs) - min(zs)
PH_H = 3.2; DEV_P = Vector((X_P - 0.45, 3.15, 0.0))                    # 巨大スマホ：スマホの台の真後ろ
s_ph = PH_H / max(ph_h, 1e-6)
Mph = Matrix.Translation(DEV_P) @ Matrix.Scale(s_ph, 4) @ Matrix.Translation(-PHONE_C)
for o in ph_parts:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mph @ mw
    if o.name.startswith(("Source phone / album", "Source phone / progress", "Static / Cyan", "Static / White markings")) or o.name == "Source phone / screen":
        o.hide_render = True; o.hide_viewport = True
import bmesh as _bm                                                       # 画面：ペアリング中（物が出す光）。第3章と同じ板の作り
sm = bpy.data.materials.new("Giant phone pairing screen"); sm.use_nodes = True; snt = sm.node_tree; snt.nodes.clear()
sem = snt.nodes.new("ShaderNodeEmission"); sem.inputs["Strength"].default_value = 2.0
tx = snt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(HERE, "screens", "pairing.png")); snt.links.new(tx.outputs["Color"], sem.inputs["Color"])
so = snt.nodes.new("ShaderNodeOutputMaterial"); snt.links.new(sem.outputs[0], so.inputs[0]); sm.diffuse_color = (0.2, 0.25, 0.3, 1)
bmq = _bm.new(); _bm.ops.create_grid(bmq, x_segments=1, y_segments=1, size=0.5); uvl = bmq.loops.layers.uv.new("UVMap")
for f_ in bmq.faces:
    for l_ in f_.loops: l_[uvl].uv = (l_.vert.co.x + 0.5, l_.vert.co.y + 0.5)
for v in bmq.verts: v.co = Vector((v.co.x * 3.22, 0.0, v.co.y * 6.80))
scr_plane = kw.mesh_obj("Giant phone screen", bmq, sm); scr_plane.matrix_world = Mph @ Matrix.Translation(Vector((-10.0, -6.335, 3.69)))
import earbud_v2 as eb2
EB_SRC = Vector((0.0, 11.12, 0.36)); s_eb = 4.8 / 17.8
eb_old_meshes = [o for o in hier(earbud_old) if o.type == "MESH"]
for o in eb_old_meshes: o.hide_render = True; o.hide_viewport = True
EB_H = 3.4; DEV_E = Vector((X_E + 0.50, 3.25, -0.02))                 # 巨大イヤホン：イヤホンの台の真後ろ
EBX = kw.empty("EARBUD PLACE"); EBX.matrix_world = Matrix.Translation(DEV_E) @ Matrix.Scale(EB_H / 17.8, 4) @ Matrix.Translation(-EB_SRC)
r_eb, parts_eb = eb2.build(bpy); r_eb.parent = EBX; r_eb.matrix_parent_inverse = Matrix.Identity(4)
NBX = kw.empty("NEIGHBOR EARBUD PLACE"); NBX.matrix_world = Matrix.Translation((14.0, 26.0, -0.02)) @ Matrix.Rotation(math.radians(35), 4, "Z") @ Matrix.Scale(s_eb, 4) @ Matrix.Translation(-EB_SRC)
nb_root = kw.empty("Neighbor earbud"); nb_root.parent = NBX; nb_root.matrix_parent_inverse = Matrix.Identity(4)
for o in parts_eb:
    c_ = o.copy(); scene.collection.objects.link(c_); c_.parent = nb_root; c_.matrix_parent_inverse = Matrix.Identity(4)
band = kw.torus("Neighbor band", 1.45, 0.32, m_amber, 48, 10); band.parent = NBX; band.matrix_parent_inverse = Matrix.Identity(4); band.location = (0.0, 11.12, 6.0)
NB_ANCHOR = NBX.matrix_world @ Vector((-2.2, 11.12, 18.0))            # 隣のイヤホンの頭の上（文字の位置）

# ================================================================ 時刻の割り振り（本編の秒）。クレーンは区間ごとに躍度最小
Z_PARK = 2.10; Z_TRAVEL = 1.48 + kp.D_LOAD                              # フックの待つ高さ・運ぶ高さ（バケツの底 1.48m）
Z_TABLE = TABLE_Z + 0.006 + kp.D_LOAD                                   # 台のバケツの取っ手をつかむ高さ
def z_on_tray(t): return tray_top(FR(t)).z + 0.004 + kp.D_LOAD         # トレーのバケツの取っ手
H = {}
for k in ("P", "E"):
    hz = ST[k]["hoist"]
    H[k] = Hoist(y0=B_Y if k == "P" else TRAY_Y["E"], z0=Z_PARK if k == "P" else Z_TRAVEL, z_top=hz["z_top"], d_load=kp.D_LOAD, rigid=True)
EV = []                                                                  # 効果音の時刻
# スマホの台：A（水色）を背中へ
h = H["P"]; t = G0["load_p"]
t = h.move(t, 0.22, z=Z_TABLE); h.grab(t, "A"); EV.append(("clunk", t)); t = h.move(t, 0.22, z=Z_TRAVEL)
t = h.move(t, 0.36, y=TRAY_Y["P"]); t_rel = t + 0.18; h.move(t, 0.20, z=z_on_tray(t_rel)); h.release(t_rel); EV.append(("clunk", t_rel))
A_ON_TRAY = t_rel; h.move(t_rel, 0.22, z=Z_TRAVEL)
assert t_rel + 0.20 < T_GO, ("クレーンが間に合わない", t_rel, T_GO)
# イヤホンの台：着いたら A を受け取り（A へ置く）、B（桃色）を背中へ
h = H["E"]; t = T_ARR_E + 0.05
t_g = t + 0.22; h.move(t, 0.22, z=z_on_tray(t_g)); h.grab(t_g, "A"); EV.append(("clunk", t_g)); A_OFF_TRAY = t_g
t = h.move(t_g, 0.22, z=Z_TRAVEL); t = h.move(t, 0.40, y=A_Y); t = h.move(t, 0.20, z=Z_TABLE); h.release(t); EV.append(("clunk", t)); A_AT_E = t
t = h.move(t, 0.16, z=Z_TRAVEL); t = h.move(t, 0.28, y=B_Y); t = h.move(t, 0.18, z=Z_TABLE); h.grab(t, "B"); EV.append(("clunk", t))
t = h.move(t, 0.20, z=Z_TRAVEL); t = h.move(t, 0.38, y=TRAY_Y["E"])
assert t < T_TURN, ("向きを変え終わる前に、桃色のバケツが上で待てない", t, T_TURN)
t = max(t, T_TURN + 0.02); t_rel = t + 0.22; h.move(t, 0.22, z=z_on_tray(t_rel)); h.release(t_rel); EV.append(("clunk", t_rel))
B_ON_TRAY = t_rel; h.move(t_rel, 0.22, z=Z_TRAVEL)
assert t_rel + 0.30 < T_TURN + 0.50 + 0.25, ("まるロボが走り出す前に置けない", t_rel)
# スマホの台：着いたら B を受け取り（A の所へ置く）
h = H["P"]; t = T_ARR_P + 0.05
t_g = t + 0.22; h.move(t, 0.22, z=z_on_tray(t_g)); h.grab(t_g, "B"); EV.append(("clunk", t_g)); B_OFF_TRAY = t_g
t = h.move(t_g, 0.20, z=Z_TRAVEL); t = h.move(t, 0.38, y=A_Y); t = h.move(t, 0.18, z=Z_TABLE); h.release(t); EV.append(("clunk", t)); B_AT_P = t
h.move(t, 0.25, z=Z_PARK)
# 注ぐ・混ぜる・型・鍵（本編の秒）
POUR = dict(white=G0["white"], secret1=G0["secret1"], secretE=A_AT_E + 0.40, secretP=B_AT_P + 0.40)   # フックが上がってから、小びんの腕を回して注ぐ
MOLD = dict(E=POUR["secretE"] + 0.62, P=POUR["secretP"] + 0.62)
KEYT = dict(E=MOLD["E"] + 0.45, P=MOLD["P"] + 0.45)
print("TIMES", {k: round(v, 2) for k, v in dict(A_ON_TRAY=A_ON_TRAY, A_AT_E=A_AT_E, B_ON_TRAY=B_ON_TRAY, B_AT_P=B_AT_P, **{"pour_" + k: v for k, v in POUR.items()},
                                                **{"key_" + k: v for k, v in KEYT.items()}).items()}, flush=True)

# ================================================================ まるロボを動かす（荷物の箱は隠し、トレーだけ残す）
bk = mr.Baker()
for i in range(N): rig.apply(frames[min(i, len(frames) - 1)], i + 1, bk)
bk.write()
for o in rig.cargo_meshes:
    if not o.name.startswith("Cradle"):
        if o.animation_data: o.animation_data_clear()
        o.hide_render = True; o.hide_viewport = True
SH = {k: H[k].sample(FPS, T0S, T1S + 0.1) for k in H}

# ================================================================ 1コマごと：バケツ・液面・取っ手・クレーン・小びん・流れ・型・鍵・灯
bkp = mr.Baker()
def put_mat(ob, M_, f):
    loc, q, sc = M_.decompose()
    for i_ in range(3): bkp.put(ob, "location", i_, f, loc[i_])
    ob.rotation_mode = "QUATERNION"
    for i_ in range(4): bkp.put(ob, "rotation_quaternion", i_, f, q[i_])
SPOT = {("P", "B"): Vector((RAIL_X["P"], B_Y, TABLE_Z + 0.006)), ("P", "A"): Vector((RAIL_X["P"], A_Y, TABLE_Z + 0.006)),
        ("E", "B"): Vector((RAIL_X["E"], B_Y, TABLE_Z + 0.006)), ("E", "A"): Vector((RAIL_X["E"], A_Y, TABLE_Z + 0.006))}
def bucket_state(nm_, t, f):
    """('table', 位置) / ('hook', 台) / ('tray',)"""
    for k in ("P", "E"):
        if SH[k]["hold"][f - 1] == nm_: return ("hook", k)
    if nm_ == "A":
        if t < A_ON_TRAY: return ("table", SPOT[("P", "B")])
        if t < A_OFF_TRAY: return ("tray",)
        return ("table", SPOT[("E", "A")])
    if t < B_ON_TRAY: return ("table", SPOT[("E", "B")])
    if t < B_OFF_TRAY: return ("tray",)
    return ("table", SPOT[("P", "A")])
# 液の量と色の予定
def paint_level(nm_, t):
    """液面の高さ（底から）。白が注がれて満ち、型へ流れると少し下がる"""
    lv = 0.30 * mjv((t - POUR["white"] - 0.10) / 0.75)
    st_k = "E" if nm_ == "A" else "P"
    lv -= 0.035 * mjv((t - MOLD[st_k]) / 0.55)
    return lv
def paint_color(nm_, t):
    c = C_WHITE
    send = C_SEND_P if nm_ == "A" else C_SEND_E
    c = cm.lerp_lin(c, send, mjv((t - POUR["secret1"] - 0.30) / 0.45))
    t2 = POUR["secretE"] if nm_ == "A" else POUR["secretP"]
    c = cm.lerp_lin(c, C_KEY, mjv((t - t2 - 0.30) / 0.45))
    return c
# 液面の揺れ：バケツの世界の位置から加速度 → 2方向の傾き
POS = {nm_: [] for nm_ in BK}; ROT = {nm_: [] for nm_ in BK}
for f in range(1, N + 1):
    t = T0S + (f - 1) / FPS
    fr = frames[min(f - 1, len(frames) - 1)]
    for nm_, b in BK.items():
        st = bucket_state(nm_, t, f)
        if st[0] == "table": M_ = Matrix.Translation(st[1])
        elif st[0] == "tray":
            Wm = rig.world_mats(fr); Mc = Wm["cargo"]; p0 = Mc @ Vector((0, 0, rig.TRAY_TOP + 0.004))
            M_ = Matrix.Translation(p0) @ Mc.to_quaternion().to_matrix().to_4x4()
        else:
            k = st[1]; (x_, y_, z_), th = H[k].load_pose(SH[k], f - 1, RAIL_X[k])
            M_ = Matrix.Translation((x_, y_, z_)) @ Matrix.Rotation(-th, 4, "X")
        POS[nm_].append(np.array(M_.translation)); ROT[nm_].append(M_)
for nm_, b in BK.items():
    P_ = np.array(POS[nm_]); acc_w = kc.accel(P_, FPS)
    acc = np.array([np.array(ROT[nm_][i].to_3x3().transposed() @ Vector(acc_w[i])) for i in range(len(acc_w))])   # バケツの向きで見た加速度
    sx = np.clip(kc.slosh(acc[:, 0], FPS), -0.21, 0.21); sy = np.clip(kc.slosh(acc[:, 1], FPS), -0.21, 0.21)
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS
        put_mat(b["root"], ROT[nm_][f - 1], f)
        lv = paint_level(nm_, t); vis = lv > 0.012
        b["liquid"].rotation_mode = "XYZ"
        bkp.put(b["liquid"], "location", 2, f, max(lv, 0.012)); bkp.put(b["liquid"], "rotation_euler", 0, f, sy[f - 1]); bkp.put(b["liquid"], "rotation_euler", 1, f, -sx[f - 1])
        for o_ in (b["paint"],): bkp.put(o_, "hide_render", 0, f, 0.0 if vis else 1.0)
        bkp.put(b["paint_body"], "scale", 2, f, max(lv, 0.012) / kp.BUCKET["fill"])
        bkp.put(b["paint_body"], "location", 2, f, max(lv, 0.012) * 0.5)
        bkp.put(b["paint_body"], "hide_render", 0, f, 0.0 if vis else 1.0)
        st = bucket_state(nm_, t, f); up = 1.0 if st[0] == "hook" else 0.0
        near = min([abs(t - tt) for tt in (A_ON_TRAY, A_OFF_TRAY, A_AT_E, B_ON_TRAY, B_OFF_TRAY, B_AT_P, G0["load_p"] + 0.3, A_AT_E + 1.07)] + [9])
        up = max(up, 1.0 - mjv((near - 0.15) / 0.25)) if st[0] != "hook" else 1.0
        b["handle"].rotation_mode = "XYZ"; bkp.put(b["handle"], "rotation_euler", 0, f, math.radians(72.0) * (1.0 - up))
    # 色（材質ごとに直接キー：中の節点の木の名前が同じでまとめ書きできないため）
    sock = b["mat"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
    for f in range(1, N + 1, 2):
        c = paint_color(nm_, T0S + (f - 1) / FPS); sock.default_value = (*c, 1.0); sock.keyframe_insert("default_value", frame=f)
        b["mat"].diffuse_color = (*c, 1.0); b["mat"].keyframe_insert("diffuse_color", frame=f)
# まるロボの受け台（トレーの上の輪）
for f in range(1, N + 1):
    Wm = rig.world_mats(frames[min(f - 1, len(frames) - 1)]); Mc = Wm["cargo"]
    put_mat(cargo_ring, Matrix.Translation(Mc @ Vector((0, 0, rig.TRAY_TOP + 0.012))) @ Mc.to_quaternion().to_matrix().to_4x4(), f)
# クレーン
for k in ("P", "E"):
    hz = ST[k]["hoist"]; S_ = SH[k]
    for f in range(1, N + 1):
        y_, z_, th = S_["y"][f - 1], S_["z"][f - 1], S_["theta"][f - 1]
        L_ = hz["z_top"] - z_
        bkp.put(hz["trolley"], "location", 1, f, y_)
        hz["swing"].rotation_mode = "XYZ"; bkp.put(hz["swing"], "rotation_euler", 0, f, -th)
        bkp.put(hz["cable"], "scale", 2, f, max(L_ - 0.04, 0.02)); bkp.put(hz["hook"], "location", 2, f, -(L_ - 0.04))
# ひみつの色の小びん：腕の向き（B → A）・傾き（注ぐ）・流れ
def yaw_to(k, spot_y):
    X = ST[k]["X"]; inner = ST[k]["inner"]; dx = inner * 0.42; dy = spot_y - 1.00
    return math.atan2(-dx, dy)
for k in ("P", "E"):
    ja = ST[k]["jar"]; ja["yaw"].rotation_mode = "XYZ"; ja["tilt"].rotation_mode = "XYZ"
    t_a = POUR["secretE"] if k == "E" else POUR["secretP"]
    y_B, y_A = yaw_to(k, B_Y), yaw_to(k, A_Y); y_OUT = math.atan2(ST[k]["inner"] * 1.0, 0.0)     # 外（台の外側）を向く
    def unwrap_to(a, ref): return ref + (a - ref + math.pi) % (2 * math.pi) - math.pi
    y_OUT = unwrap_to(y_OUT, y_B); y_A = unwrap_to(y_A, y_OUT)
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS
        yw = y_B + (y_OUT - y_B) * mjv((t - (POUR["secret1"] + 0.85)) / 0.30)
        yw = yw + (y_A - y_OUT) * mjv((t - (t_a - 0.28)) / 0.26) - (y_A - y_OUT) * mjv((t - (t_a + 0.95)) / 0.30)
        bkp.put(ja["yaw"], "rotation_euler", 2, f, yw)
        tilt = 0.0
        for t0 in (POUR["secret1"], t_a):
            tilt = max(tilt, mjv((t - t0) / 0.28) * (1 - mjv((t - t0 - 0.62) / 0.28)))
        sgn = -1.0 if k == "P" else 1.0
        bkp.put(ja["tilt"], "rotation_euler", 1, f, sgn * math.radians(118) * tilt)
    # 流れ（びんが傾いている間）：口から真下のバケツの液面へ
    for t0, spot in ((POUR["secret1"], B_Y), (t_a, A_Y)):
        pass
# 流れは、描くコマで位置を計算する（びんの口の世界の位置が要る）→ 下でまとめて
# 白の流れ（タンク → B）
for k in ("P", "E"):
    st_ = SPOUT[k]["stream"]; top = SPOUT[k]["p"]
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS
        on = 1.0 if POUR["white"] <= t < POUR["white"] + 0.90 else 0.0
        target = SPOT[(k, "B")] + Vector((0, 0, max(paint_level("A" if k == "P" else "B", t), 0.0)))
        d = target - top; L_ = d.length
        q = Vector((0, 0, -1)).rotation_difference(d.normalized())
        grow = mjv((t - POUR["white"]) / 0.12); shrink = mjv((t - POUR["white"] - 0.74) / 0.14)
        st_.rotation_mode = "QUATERNION"
        p_top = top + d * shrink
        for i_ in range(3): bkp.put(st_, "location", i_, f, p_top[i_])
        for i_ in range(4): bkp.put(st_, "rotation_quaternion", i_, f, q[i_])
        bkp.put(st_, "scale", 2, f, max(L_ * (grow - shrink), 1e-3)); bkp.put(st_, "hide_render", 0, f, 0.0 if on and grow - shrink > 0.01 else 1.0)
# 鍵の型：色が満ちる → 鍵が浮かんで鍵穴へ（鍵の本体は別に作り、型の位置から動かす）
KEYS = {}; KEY_END = {}
for k in ("P", "E"):
    md = ST[k]["mold"]; mk = kp.key("Key " + k, kp.paint_mat("Key paint " + k, C_KEY), s=KEY_S); KEYS[k] = mk; inner_ = ST[k]["inner"]
    kh = ST[k]["keyhole"]
    bpy.context.view_layer.update()
    p_mold = md["recess"].matrix_world.translation.copy()
    R_mold = md["recess"].matrix_world.to_quaternion() @ Euler(md.get("key_rot", (0, 0, 0))).to_quaternion()   # 型の中の鍵の向き（寝ている）
    p_top = kh["root"].matrix_world @ Vector(kh["top"])                 # 錠の鍵穴（上の面）
    p_end = p_top + Vector((0, 0, KEY_OUT)); p_hov = p_end + Vector((0, 0, 0.36))
    Rk = Quaternion((0, 1, 0), math.pi / 2)                               # 軸が真下、平らな面が前（−Y）、歯は −X
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS; t_m = MOLD[k]; t_k = KEYT[k]
        fl = mjv((t - t_m) / 0.55)
        bkp.put(md["fill"], "location", 2, f, -0.004 + 0.009 * fl)
        for ch in hier(md["fill"])[1:]:                                   # 色の層（形の板）は、満ちてから鍵が出ていくまでだけ見せる（空の親を隠しても子は隠れない）
            bkp.put(ch, "hide_render", 0, f, 0.0 if 0.02 < fl and t < t_k + 0.05 else 1.0)
        u = (t - t_k) / KEY_FLY
        if u < 0: p = p_mold + Vector((0, 0, 0.003)); R = R_mold; vis = 0.0
        else:
            u1 = mjv(u / 0.25); u2 = mjv((u - 0.15) / 0.30); u3 = mjv((u - 0.40) / 0.30); u4 = mjv((u - 0.68) / 0.32)
            p1 = p_mold + Vector((inner_ * 0.26, 0, 0.12))                # 型から内側へ滑り出る（上の白い管の真下を避ける）
            p2 = p1 + Vector((0, 0, 0.50))                                # 上がりながら立つ
            p = p_mold.lerp(p1, u1); p = p.lerp(p2, u2); p = p.lerp(p_hov, u3); p = p.lerp(p_end, u4)
            R = R_mold.slerp(Rk, mjv((u - 0.18) / 0.40)); vis = 1.0
        put_mat(mk, Matrix.Translation(p) @ R.to_matrix().to_4x4(), f)
        for ch in hier(mk)[1:]: bkp.put(ch, "hide_render", 0, f, 1.0 - vis)
    gl = kh["glow"].node_tree.nodes["Emission"].inputs["Strength"]
    t_lock = KEYT[k] + KEY_FLY
    for t_, v_ in ((T0S, 0.0), (t_lock - 0.02, 0.0), (t_lock + 0.15, 6.0), (t_lock + 0.9, 4.0)):
        gl.default_value = v_; gl.keyframe_insert("default_value", frame=FR(t_))
    KEY_END[k] = p_end.copy()
    EV += [("key", KEYT[k] + 0.05), ("lock", KEYT[k] + KEY_FLY - 0.02)]
# 地面の灯：スマホの台からイヤホンの台へ、順に灯る
for L_ in LAMPS:
    s_ = L_["glow"].node_tree.nodes["Emission"].inputs["Strength"]; t_on = G0["lamps"] + 0.9 * L_["u"]
    for t_, v_ in ((T0S, 0.0), (t_on, 0.0), (t_on + 0.12, 9.0), (t_on + 0.6, 4.0)):
        s_.default_value = v_; s_.keyframe_insert("default_value", frame=FR(t_))
EV += [("step", T0S + e_["t"]) for e_ in plan.events if e_["kind"] in ("step", "step_turn") and T0S + e_["t"] < T1S]   # まるロボの足音
EV += [("pop", G0["lamps"] + 0.9 * L_["u"]) for L_ in LAMPS] + [("whoosh", POUR["white"]), ("drip", POUR["secret1"] + 0.35), ("drip", POUR["secretE"] + 0.35),
                                                                  ("drip", POUR["secretP"] + 0.35), ("whoosh", MOLD["E"]), ("whoosh", MOLD["P"])]
bkp.write()
for ob_ in bpy.data.objects:                                              # 見せる・隠すは段で切り替える
    ad = ob_.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path == "hide_render":
                for kp_ in fc.keyframe_points: kp_.interpolation = "CONSTANT"

# ================================================================ 小びんの流れ（口の世界の位置から、毎コマ）
bk2 = mr.Baker()
for k in ("P", "E"):
    ja = ST[k]["jar"]; st_ = ja["stream"]; st_.rotation_mode = "QUATERNION"
    t_a = POUR["secretE"] if k == "E" else POUR["secretP"]
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS
        on_spot = None
        for t0, spot in ((POUR["secret1"], "B"), (t_a, "A")):
            if t0 + 0.22 <= t < t0 + 0.72: on_spot = (t0, spot)
        if on_spot is None:
            bk2.put(st_, "hide_render", 0, f, 1.0); continue
        scene.frame_set(f); mouth = ja["tilt"].matrix_world @ Vector(ja["mouth"])
        nm_ = "A" if (k == "P") == (on_spot[1] == "B") else "B"
        tgt = SPOT[(k, on_spot[1])] + Vector((0, 0, max(paint_level(nm_, t), 0.05)))
        d = tgt - mouth; q = Vector((0, 0, -1)).rotation_difference(d.normalized()); Mi = st_.parent.matrix_world.inverted()
        loc = Mi @ mouth
        for i_ in range(3): bk2.put(st_, "location", i_, f, loc[i_])
        qq = (Mi.to_quaternion() @ q)
        for i_ in range(4): bk2.put(st_, "rotation_quaternion", i_, f, qq[i_])
        bk2.put(st_, "scale", 2, f, max(d.length, 1e-3)); bk2.put(st_, "hide_render", 0, f, 0.0)
bk2.write()
for k in ("P", "E"):
    ad = ST[k]["jar"]["stream"].animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path == "hide_render":
                for kp_ in fc.keyframe_points: kp_.interpolation = "CONSTANT"

# ================================================================ カメラ（5カット）
cd_ = bpy.data.cameras.new("Pairing camera"); cam = kw.link(O.new("Pairing camera", cd_)); cd_.sensor_width = 36; cd_.clip_start = 0.05
cd_.dof.use_dof = True; cd_.dof.aperture_fstop = 4.0; scene.camera = cam; cam.rotation_mode = "QUATERNION"
def robot_xy(f):
    fr = frames[min(f - 1, len(frames) - 1)]; return Vector((fr["root"][0], fr["root"][1], 0.0))
T_LOCK = {k_: KEYT[k_] + KEY_FLY for k_ in KEYT}
SHOTS = [(T0S, "S1"), (G0["load_p"] - 0.05, "S2"), (T_ARR_E - 0.35, "S3"), (T_LOCK["E"] + 1.15, "S5")]   # S3 は鍵が錠に差さって光るまで
def shot_of(t):
    nm_ = SHOTS[0][1]
    for a_, n_ in SHOTS:
        if t >= a_: nm_ = n_
    return nm_
def shot(t, f):
    nm_ = shot_of(t)
    if nm_ == "S1":                                                    # 全景：両方の台・タンク・灯・後ろに巨大スマホと巨大イヤホン
        u = mjv((t - T0S) / (G0["load_p"] - T0S)); p = Vector((0.0, -5.9 + 0.4 * u, 2.45 - 0.05 * u)); tg = Vector((0.0, 1.8, 1.70))
        return p, tg, 26.0, Vector((0.0, 1.0, 1.2))
    if nm_ in ("S2", "S4"):                                            # まるロボと並んで歩く（横から少し前）
        r = robot_xy(f); cx_ = 0.55 * r.x
        p = Vector((cx_ - 0.35, -4.4, 2.45)); tg = Vector((cx_ + 0.10, 0.65, 1.20))
        return p, tg, 27.0, Vector((r.x, 0.0, 1.3))
    if nm_ == "S3":                                                    # イヤホンの台：受け渡し・ひみつの色・型・鍵
        X = ST["E"]["X"]; u = mjv((t - T_ARR_E) / 3.0)                  # 高い所から見下ろす：背中のバケツ・台の上・鍵の型・鍵穴が同時に見える
        p = Vector((X - 0.75 + 0.15 * u, -2.55 + 0.15 * u, 3.15)); tg = Vector((X + 0.02, 0.62, 0.98))
        return p, tg, 24.0, Vector((X, 0.5, 1.1))
    X = ST["P"]["X"]; u = mjv((t - (T_LOCK["P"] - 0.30)) / 1.5)          # スマホの台（少し高い所から：まるロボの陰にならない）→ 両方の台が見える全景へ下がる
    p = Vector((X + 1.30, -2.9, 3.0)).lerp(Vector((0.0, -5.0, 2.55)), u); tg = Vector((X + 0.15, 0.85, 1.0)).lerp(Vector((0.0, 1.3, 1.45)), u)   # 最後は二本の鍵と巨大な二台が入る近さ
    return p, tg, 28.0 - 2.0 * u, Vector((X, 0.6, 1.1)).lerp(Vector((0.0, 0.6, 1.1)), u)
bkc = mr.Baker(); ANCH = []
from bpy_extras.object_utils import world_to_camera_view
for f in range(1, N + 1):
    t = T0S + (f - 1) / FPS; p, tg, lens, fp = shot(t, f); q = (tg - p).to_track_quat("-Z", "Y")
    for i_ in range(3): bkc.put(cam, "location", i_, f, p[i_])
    for i_ in range(4): bkc.put(cam, "rotation_quaternion", i_, f, q[i_])
    bkc.put(cd_, "lens", 0, f, lens); bkc.put(cd_, "dof.focus_distance", 0, f, max((fp - p).length, 0.1))
bkc.write()
for fc in cam.animation_data.action.fcurves:
    for kp_ in fc.keyframe_points: kp_.interpolation = "LINEAR"
# 文字を重ねる所（画面の位置）を書き出す
bpy.context.view_layer.update()
anchors_w = dict(lamps=Vector((0.0, -0.75, 0.25)), tank=Vector((TANK[0], TANK[1], 3.05)), jarP=None, jarE=None, nb=NB_ANCHOR,
                 holeP=KEY_END["P"] + Vector((0, 0, 0.24)), holeE=KEY_END["E"] + Vector((0, 0, 0.24)),
                 keyP=KEY_END["P"], keyE=KEY_END["E"],
                 devP=DEV_P + Vector((0, 0, PH_H + 0.30)), devE=DEV_E + Vector((-0.15, 0, EB_H + 0.25)),
                 tagP=Vector((ST["P"]["X"], 1.0, 2.35)), tagE=Vector((ST["E"]["X"], 1.0, 2.35)))
for f in range(1, N + 1):
    scene.frame_set(f); row = {}
    for nm_, w_ in anchors_w.items():
        if nm_ in ("jarP", "jarE"): w_ = ST[nm_[-1]]["jar"]["tilt"].matrix_world.translation + Vector((0, 0, 0.32))
        v = world_to_camera_view(scene, cam, w_); row[nm_] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
    ANCH.append(row)
def screen_box(objs, f):                                                  # 物の画面の上の箱（0〜1）
    scene.frame_set(f); xs, ys = [], []
    for o in objs:
        for c in o.bound_box:
            v = world_to_camera_view(scene, cam, o.matrix_world @ Vector(c)); xs.append(v.x); ys.append(1 - v.y)
    return [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)]
MATCH = dict(P=screen_box([o for o in ph_parts if not o.hide_render] + [scr_plane], 1), E=screen_box([o for o in hier(r_eb) if o.type == "MESH" and not o.hide_render], 1))
json.dump(dict(t0=T0S, fps=FPS, frames=N, match=MATCH, g0=G0, t_go=T_GO, shots=[[round(a_, 3), n_] for a_, n_ in SHOTS], events=[dict(kind=k_, t=round(t_, 3)) for k_, t_ in sorted(EV, key=lambda e: e[1])],
               times=dict(arrive_e=T_ARR_E, turn=T_TURN, arrive_p=T_ARR_P, a_at_e=A_AT_E, b_at_p=B_AT_P, pour=POUR, mold=MOLD, key=KEYT, lock=T_LOCK), anchors=ANCH),
          open(os.path.join(A.out, "pairing_log.json"), "w"), indent=0, ensure_ascii=False)
print("BAKED", flush=True)

# ================================================================ かすみ・描き方
for m_ in list(bpy.data.materials):
    if m_.use_nodes: kw.hazify(m_)
kw.render_setup(scene, A.engine, tuple(A.res), A.samples, A.exposure, SUN_DIR)
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
if A.still:
    for tt in A.still.split(","):
        f = FR(float(tt)); scene.frame_set(f)
        scene.render.filepath = os.path.join(A.out, "still_%06.2f.png" % float(tt)); bpy.ops.render.render(write_still=True); print("STILL", tt, flush=True)
elif A.frames:
    f0, f1 = [int(x) for x in A.frames.split(":")]
    scene.frame_start, scene.frame_end = f0, min(f1, N); scene.render.use_overwrite = False; scene.render.use_placeholder = True
    scene.render.filepath = os.path.join(A.out, "frames", "p_"); bpy.ops.render.render(animation=True); print("SEQ DONE", flush=True)
