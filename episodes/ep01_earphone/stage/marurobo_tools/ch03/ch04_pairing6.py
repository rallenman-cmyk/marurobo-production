# 第4章 ペアリング v6（台本 v2、2026-11-06）：絵の具のたとえを、実験の進め方でゆっくり見せる 3D
#   台はそのままスマホ（寝かせた大きなスマホ）とイヤホン（閉じたケース）の形。右の奥に「隣のイヤホン」（橙の帯のケース）
#   台の上：コップ二つ（手前の送る口・受け取る口。送る口は内側）、ひみつの色のびん（真ん中。左右どちらにも傾く）、白のびん（送る口の外）
#   動きは二つだけ：「びんが傾いて注ぐ」「まるロボの背中の板と台の間で、コップ（下の皿ごと）が滑って移る」
#   まるロボは台に背を向けたまま、横歩きで台の間を行き来する（カメラのほうを向いたまま）
#   時刻は stage/script/script_v2_timed.json（台本 v2 の仮の時刻）の P1〜P17 から決める
# 使い方: blender -b story.blend --python ch04_pairing6.py -- --out DIR [--engine eevee|workbench] [--res W H] [--samples N] [--still 秒,…] [--frames A:B]
import bpy, sys, os, math, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); STAGE = os.path.abspath(os.path.join(HERE, ".."))
for p_ in (HERE, STAGE, os.path.join(STAGE, "maru"), os.path.join(STAGE, "human")):
    if p_ not in sys.path: sys.path.insert(0, p_)
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
import marumotion as mm, marurig as mr
from kit import world as kw, props as kp, carry as kc, colormix as cm

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/ch04_pairing6"); ap.add_argument("--engine", default="eevee"); ap.add_argument("--res", nargs=2, type=int, default=[640, 360])
ap.add_argument("--samples", type=int, default=12); ap.add_argument("--still", default=""); ap.add_argument("--frames", default="")
ap.add_argument("--video", type=int, default=0, help="1＝連番ではなく、範囲ごとの mp4（H.264・ほぼ劣化なし）で書き出す（PC の本番用：ch04_pair_0001-0100.mp4 …）")
ap.add_argument("--phone", default="2.40,1.12,0.10", help="スマホの台の大きさ：長い辺,短い辺,厚さ（m）。ケースは 1.20×0.74。v8 で 1.34×0.70×0.06 から大きくした（本物の比に近い）")
ap.add_argument("--sun", type=float, default=-55.0); ap.add_argument("--sun_el", type=float, default=48.0); ap.add_argument("--exposure", type=float, default=0.0)
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
scene = bpy.context.scene; O = bpy.data.objects
FPS = 24

# ================================================================ 時刻（台本 v2 の仮の時刻）
TJ = json.load(open(os.path.join(STAGE, "script", "script_v2_timed.json"), encoding="utf-8"))
P = {int(t["tag"][1:]): (t["start"], t["end"]) for t in TJ if t["tag"].startswith("P")}
def at_char(k, n_chars):                                                     # P k の文の、n 文字目を話す時刻（字数で比例）
    txt = [t["text"] for t in TJ if t["tag"] == "P%d" % k][0]; a, b = P[k]; return a + (b - a) * n_chars / len(txt)
T0S = P[2][1] - 1.0                                                          # 2D（中では…？）から 3D へ
T1S = P[16][1] + 1.6                                                         # 鍵が台にしまわれるまで → 2D の「接続しました」へ
N = int(round((T1S - T0S) * FPS)) + 1
def FR(t): return int(round((t - T0S) * FPS)) + 1
def mjv(u): u = min(max(u, 0.0), 1.0); return u * u * u * (10 - 15 * u + 6 * u * u)
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out

# ================================================================ Codex版から使う物：まるロボだけ
scene.frame_set(1)
keep = set(hier(O["Maru"]))
for ob in list(O):
    if ob not in keep: O.remove(ob, do_unlink=True)
for coll_ in (bpy.data.materials, bpy.data.worlds, bpy.data.lights):
    for idb in coll_:
        if getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt_ = getattr(idb, "node_tree", None)
        if nt_ and nt_.animation_data: nt_.animation_data_clear()
maru = O["Maru"]; rig = mr.MaruRig(maru)

# ================================================================ 配置（m）。台の手前の縁は y＝Y_EDGE、まるロボは手前（−y）で台に背を向けて止まる
X_P, X_E = -1.15, 1.15; XS = dict(P=X_P, E=X_E); INNER = dict(P=1.0, E=-1.0)
Y_EDGE = 0.30; Y_SLOT = Y_EDGE + 0.17                                        # コップ（下の皿）の真ん中
DX_SLOT = 0.17                                                               # 送る口・受け取る口：台の真ん中から左右へ
DX_WHITE = 0.37                                                              # 白のびん：送る口の外側
NB = Vector((3.30, 1.95, 0.0)); NB_YAW = math.radians(-22.0)                 # 隣のイヤホン（ケースの台）
CUP_R, CUP_H = 0.10, 0.20

# まるロボの止まる所と、背中の板の高さ（止まって台に背を向けた姿勢で測る）
def probe(heading, pos):
    q = mm.Plan(pos=pos, heading=heading, carry=True, seed=3); q.idle(1.0, shifts=False, glance=False)
    fr = mm.simulate(q, fps=FPS)[-1]; W_ = rig.world_mats(fr); return W_["cargo"], Vector((fr["root"][0], fr["root"][1], 0))
Mc0, R0 = probe(180.0, (0.0, 0.0))
PLATE_TOP = rig.TRAY_TOP                                                     # 板の上面（cargo の局所 z）
c_w = Mc0 @ Vector((0, 0, PLATE_TOP))
H_TOP = c_w.z                                                                # 台の上面＝背中の板の上面
PLATE_D = 0.36; PLATE_W = 0.64                                               # 板（前後・左右）
DY_C = c_w.y - R0.y                                                          # 体の中心 → 板の真ん中（前後）
Y_PARK = (Y_EDGE - 0.02 - PLATE_D / 2) - DY_C                                # 板の後ろの端が、台の手前の端の 2cm 手前
print("H_TOP %.3f  DY_C %.3f  Y_PARK %.3f" % (H_TOP, DY_C, Y_PARK), flush=True)

# ================================================================ 時刻の割り振り（本編の秒）
T_WALKIN = P[7][0] + 0.15                                                    # 「では、ペアリングをやってみましょう」で歩いてくる
T_WHITE = P[8][0] + 0.55                                                     # 「まず、どちらのコップにも同じ白を」
T_SEC1 = dict(P=at_char(9, 6), E=at_char(9, 26))                             # 「そこへ、自分のひみつの色を混ぜると、スマホは水色、イヤホンは桃色に」
T_EX = at_char(10, 23)                                                       # 「では、まるロボに運んでもらいましょう」の「まるロボに」
T_SEC2 = dict(P=at_char(12, 4), E=at_char(12, 17))                           # 「受け取った色に、もう一度、自分のひみつの色を混ぜます」
T_MERGE = at_char(15, 14)                                                    # 「もし、隣のイヤホンが見えた二つを混ぜても……」
T_KEY = P[16][0] + 0.45; T_KEY_IN = at_char(16, 16)                          # 「この二台だけの紫色が『鍵』」→「鍵そのものは、一度も送っていません」
POUR_T = 0.75                                                                # びんが傾いて戻るまで（流れは 0.25〜0.60）
SLIDE_T = 1.30                                                               # コップが滑って移る

# ================================================================ まるロボの予定：左から歩いてきて、スマホの台に背を向けて止まる → 横歩きで行き来
plan = mm.Plan(pos=(-3.7, Y_PARK), heading=-90.0, carry=True, seed=21)
plan.idle(max(T_WALKIN - T0S, 0.1), shifts=False, glance=False)
plan.walk_to((X_P, Y_PARK), speed=mm.V_WALK, label="歩いてくる")
plan.turn_to(heading=180.0, step=0.24, gap=0.04)
t_ready = plan.t
for k_, t_ in (("P", T_WHITE), ("E", T_WHITE + 0.9), ("P", T_SEC1["P"]), ("E", T_SEC1["E"])):   # 注ぐ台を見る（左が＋。スマホの台は右後ろ）
    plan.look(yaw=(-35.0 if k_ == "P" else 35.0), pitch=-8.0, hold=0.6, at=t_ - T0S - 0.2)
plan.look(yaw=0.0, pitch=0.0, hold=0.4, at=T_SEC1["E"] + 1.4 - T0S)         # 体を正面に戻す（背中の板が台とまっすぐになるように）
plan.idle(max(T_EX - T0S - plan.t, 0.1), shifts=True, glance=False)
EXS = []                                                                    # 滑る予定：(始め, 終わり, コップ, 向き 'off'＝台へ／'on'＝背中へ, 台, 口, 背中の位置 ±1)
t = plan.t; plan.look(yaw=-30.0, pitch=-10.0, hold=0.3, at=t, body=False)
EXS.append((t + 0.20, t + 0.20 + SLIDE_T, "A", "on", "P", "send", +1)); plan.idle(SLIDE_T + 0.45, shifts=False, glance=False)
plan.look(yaw=40.0, pitch=0.0, hold=0.5, at=plan.t, body=False)
plan.back_to((X_E, Y_PARK), step=0.36, sw=0.26, gap=0.04, look=False, label="横歩きでイヤホンの台へ")
t = plan.t; plan.look(yaw=30.0, pitch=-10.0, hold=0.3, at=t, body=False)
EXS.append((t + 0.20, t + 0.20 + SLIDE_T, "A", "off", "E", "recv", +1)); t2 = t + 0.20 + SLIDE_T + 0.25
EXS.append((t2, t2 + SLIDE_T, "B", "on", "E", "send", -1)); plan.idle(t2 + SLIDE_T + 0.40 - plan.t, shifts=False, glance=False)
plan.look(yaw=-40.0, pitch=0.0, hold=0.5, at=plan.t, body=False)
plan.back_to((X_P, Y_PARK), step=0.36, sw=0.26, gap=0.04, look=False, label="横歩きでスマホの台へ")
t = plan.t; plan.look(yaw=-30.0, pitch=-10.0, hold=0.3, at=t, body=False)
EXS.append((t + 0.20, t + 0.20 + SLIDE_T, "B", "off", "P", "recv", -1)); plan.idle(SLIDE_T + 0.6, shifts=False, glance=False)
plan.look(yaw=0.0, pitch=0.0, hold=0.5, at=plan.t)
for k_, t_ in (("P", T_SEC2["P"]), ("E", T_SEC2["E"])): plan.look(yaw=(-35.0 if k_ == "P" else 35.0), pitch=-8.0, hold=0.6, at=t_ - T0S - 0.2)
plan.look(yaw=0.0, pitch=0.0, hold=0.4, at=T_SEC2["E"] + 1.4 - T0S)
plan.idle(max(T1S - T0S + 0.5 - plan.t, 0.1), shifts=True, glance=True)
EXS = [(T0S + a, T0S + b, c, d, e, g, h) for (a, b, c, d, e, g, h) in EXS]
frames = mm.simulate(plan, fps=FPS)
T_EX_END = EXS[-1][1]
print("EXCHANGE", [(round(a, 2), round(b, 2), c, d, e) for a, b, c, d, e, g, h in EXS], "P12 starts %.2f" % P[12][0], flush=True)
assert T_EX_END + 0.3 < T_SEC2["P"], ("受け渡しが、二回目の色を混ぜる前に終わらない", T_EX_END, T_SEC2["P"])

# ================================================================ 材質
m_ped = kw.mat("Pedestal", kw.srgb("#8A939C"), 0.45, 0.6); m_frame = kw.mat("Holder frame", kw.srgb("#5C6168"), 0.35, 0.8)
m_phone = kw.mat("Phone body", kw.srgb("#1D2228"), 0.25, 0.3, coat=0.6); m_case = kw.mat("Case white", kw.srgb("#F3F2EE"), 0.18, 0.0, coat=1.0)
m_seam = kw.mat("Case seam", kw.srgb("#B9BDC2"), 0.4); m_amber = kw.mat("Neighbor amber", kw.srgb("#D6802C"), 0.4, 0.1)
m_plate = kw.mat("Maru plate", kw.srgb("#6F7882"), 0.35, 0.6); m_slot = kw.mat("Slot ring", kw.srgb("#7A838C"), 0.4, 0.5)
m_glass = kp.clear_mat("Cup clear", kw.srgb("#E6ECEF"), alpha=0.26, rough=0.06)
m_trim = kw.mat("Cup trim", kw.srgb("#AEB4BA"), 0.3, 0.8)
PIG = cm.PIGMENTS
WHITE, BLUE, RED = cm.Paint(白=1.0), cm.Paint(青=0.8), cm.Paint(赤=0.8)
C_WHITE = WHITE.linear(); C_SEND = dict(A=(WHITE + BLUE).linear(), B=(WHITE + RED).linear()); C_KEY = (WHITE + BLUE + RED).linear(); C_PALE = (WHITE + WHITE + BLUE + RED).linear()
assert (WHITE + BLUE + RED).same_as((WHITE + RED) + BLUE)
def smooth_clear(m):
    """半透明を「重ねて混ぜる」描き方にする（ディザは少ないサンプルだと砂のようにザラつき、動画でちらつく）。
    同じ物の中では一番手前の面だけを描く（重なりの順番の乱れを防ぐ）。影は透け具合に合わせて薄く"""
    try: m.surface_render_method = "BLENDED"
    except Exception: pass
    for at, v in (("use_transparency_overlap", False), ("use_backface_culling", False), ("use_transparent_shadow", True)):
        try: setattr(m, at, v)
        except Exception: pass
    return m
def tinted_glass(name, rgb_lin, alpha=0.62):
    m = kw.mat(name, rgb_lin, rough=0.08, coat=0.5); bs = m.node_tree.nodes["Principled BSDF"]; bs.inputs["Alpha"].default_value = alpha
    smooth_clear(m)
    m.diffuse_color = (*rgb_lin, alpha); return m
m_bottle = dict(P=tinted_glass("Secret bottle blue", cm.Paint(青=1).linear()), E=tinted_glass("Secret bottle red", cm.Paint(赤=1).linear()))
m_wbottle = tinted_glass("White bottle", C_WHITE, 0.85)
smooth_clear(m_glass)
print("GLASS", m_glass.surface_render_method, getattr(m_glass, "use_transparency_overlap", None), getattr(m_glass, "use_transparent_shadow", None), flush=True)
m_secret_paint = dict(P=kp.paint_mat("Secret blue paint", cm.Paint(青=1).linear()), E=kp.paint_mat("Secret red paint", cm.Paint(赤=1).linear()))
m_white_paint = kp.paint_mat("Common white paint", C_WHITE)

# ================================================================ 床・空・太陽
floor = kw.box("Ground", (120.0, 120.0, 0.02), kw.slate_material()); floor.location = (0, 20.0, -0.01)
sun, SUN_DIR = kw.sky_and_sun(scene, az_deg=A.sun, el_deg=A.sun_el, sky_strength=0.10, sun_energy=4.0)

# ================================================================ 台：スマホ（寝かせた大きなスマホ）とイヤホン（閉じたケース）
import bmesh as _bm
def rounded_slab(name, w, d, t, r, m, segs=10):
    """角の丸い板（上から見て角丸の長方形）。原点は上面の真ん中"""
    bm = _bm.new(); pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for j in range(segs + 1):
            a = math.radians(a0 + 90 * j / segs); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    top = [bm.verts.new((x, y, 0.0)) for x, y in pts]; bot = [bm.verts.new((x, y, -t)) for x, y in pts]
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    n = len(pts)
    for j in range(n): bm.faces.new((bot[j], bot[(j + 1) % n], top[(j + 1) % n], top[j]))
    ob = kw.mesh_obj(name, bm, m)
    b = ob.modifiers.new("bevel", "BEVEL"); b.width = min(0.02, t * 0.35); b.segments = 3; b.limit_method = "ANGLE"
    return ob
TOP = {}
def screen_material():
    sm = bpy.data.materials.new("Phone screen"); sm.use_nodes = True; nt = sm.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.4
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(HERE, "screens", "pairing.png")); nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    oo = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], oo.inputs[0]); sm.diffuse_color = (0.2, 0.25, 0.3, 1); return sm
# スマホ：横向きに寝かせる（長い辺が x）。画面は上。台の脚は濃い灰の箱
W_PH, D_PH, T_PH = [float(v) for v in A.phone.split(",")]
R_PH = 0.09 * W_PH / 1.34                                                    # 角の丸み・縁・カメラは長さに比例
ph = rounded_slab("Phone top", W_PH, D_PH, T_PH, R_PH, m_phone); ph.location = (X_P, Y_EDGE + D_PH / 2, H_TOP)
bmq = _bm.new(); _bm.ops.create_grid(bmq, x_segments=1, y_segments=1, size=0.5); uvl = bmq.loops.layers.uv.new("UVMap")
for f_ in bmq.faces:
    for l_ in f_.loops: l_[uvl].uv = (0.5 - l_.vert.co.y, l_.vert.co.x + 0.5)       # 縦長の画像を横に寝かせる
for v in bmq.verts: v.co = Vector((v.co.x * (W_PH - 0.10 * W_PH / 1.34), v.co.y * (D_PH - 0.08 * W_PH / 1.34), 0.0015))
scr = kw.mesh_obj("Phone screen", bmq, screen_material()); scr.parent = ph; scr.matrix_parent_inverse = Matrix.Identity(4)
cam_bump = kw.cyl("Phone camera", 0.035 * W_PH / 1.34, 0.012, m_phone, 24); cam_bump.parent = ph; cam_bump.matrix_parent_inverse = Matrix.Identity(4); cam_bump.location = (-W_PH / 2 + 0.07 * W_PH / 1.34, 0.0, 0.006)
def column(name, x, y, h_):                                                   # 細い柱と丸い足（台の脚）
    c_ = kw.cyl(name, 0.07, h_, m_ped, 32); c_.location = (x, y, h_ / 2)
    b_ = kw.cyl(name + " foot", 0.30, 0.04, m_ped, 48); b_.location = (x, y, 0.02); return c_
column("Phone column", X_P, Y_EDGE + D_PH / 2, H_TOP - T_PH)
TOP["P"] = dict(obj=ph)
def loft_rrect(name, w, d, r, prof, m, y_off=0.0, segs=8):
    """角の丸い長方形（上から見て）を、prof＝[(内へ入る量, 高さ z), …]（下から上へ）の輪でつないだ立体。両端はふさぐ。
    内へ入った輪の角の丸みは r−入る量（外形からの等距離の線なので、側面の丸みが正しくつながる）"""
    bm = _bm.new(); rings = []
    for inset, z in prof:
        rr = max(r - inset, 0.004); hw, hd = w / 2 - inset, d / 2 - inset; pts = []
        for cx, cy, a0 in ((hw - rr, hd - rr, 0), (-hw + rr, hd - rr, 90), (-hw + rr, -hd + rr, 180), (hw - rr, -hd + rr, 270)):
            for j in range(segs + 1):
                a = math.radians(a0 + 90 * j / segs); pts.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a) + y_off, z)))
        rings.append(pts)
    n = len(rings[0])
    for a_, b_ in zip(rings, rings[1:]):
        for j in range(n): bm.faces.new((a_[j], a_[(j + 1) % n], b_[(j + 1) % n], b_[j]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    _bm.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    ob = kw.mesh_obj(name, bm, m, smooth=True)
    ob.data.set_sharp_from_angle(angle=math.radians(40)) if hasattr(ob.data, "set_sharp_from_angle") else None
    return ob
def arc_prof(inset0, z0, rad, up=True, n=7):
    """四分の一の円の丸み：(内へ入る量, 高さ) の点。up＝True は上へ行くほど内へ（上の角）、False は下へ行くほど内へ（下の角）"""
    out = []
    for j in range(n + 1):
        a = math.pi / 2 * j / n
        out.append((inset0 + rad * (1 - math.cos(a)), z0 + rad * math.sin(a)) if up else (inset0 + rad * (1 - math.cos(a)), z0 - rad * math.sin(a)))
    return out
# ケースの中の小さなイヤホン：第3章の巨大イヤホン v2 と同じ形（同じ網目を使い回す。白いつやの樹脂・シリコンの耳の先・黒い網）
EB_TEMPLATE = None
def earbud_template():
    global EB_TEMPLATE
    if EB_TEMPLATE is None:
        import earbud_v2 as ebv
        r0, parts = ebv.build(bpy, h=0.22)                                    # 画面では小さい（幅 20〜60 画素）：網目は粗くてよい（細かい 0.07 だと描くのが 2 倍遅かった）
        for o in parts:
            o.hide_render = True; o.hide_viewport = True
            for m_ in o.data.materials:                                         # 肌の透け（SSS）も、この大きさでは見えないので切る（描く時間のため）
                for nd in m_.node_tree.nodes:
                    if nd.type == "BSDF_PRINCIPLED" and "Subsurface Weight" in nd.inputs: nd.inputs["Subsurface Weight"].default_value = 0.0
        EB_TEMPLATE = (ebv, parts)
    return EB_TEMPLATE
EB_S = 0.030; EB_Z_SURF = 10.6                                                 # 大きさ（頭の幅 約0.2m）、ケースの上面に来る元の高さ（軸が少し見える）
def place_earbud(name, parent_, xy, tip_dir, mirror):
    """parent_ の局所の xy に、軸を立てて差す。tip_dir：耳の先の向き（局所の xy）。mirror：左のイヤホン（左右反転）"""
    ebv, parts = earbud_template()
    er = kw.empty(name, size=0.05); er.parent = parent_; er.matrix_parent_inverse = Matrix.Identity(4)
    d_nat = (ebv.TIP - ebv.HC)[:2]; d_nat = (-d_nat[0] if mirror else d_nat[0], d_nat[1])
    th = math.atan2(tip_dir[1], tip_dir[0]) - math.atan2(d_nat[1], d_nat[0])
    er.location = (xy[0], xy[1], H_TOP - EB_Z_SURF * EB_S); er.rotation_euler = (0, 0, th); er.scale = (-EB_S if mirror else EB_S, EB_S, EB_S)
    out = [er]
    for o in parts:
        c_ = o.copy(); c_.name = name + " " + o.name.replace("Earbud v2 ", ""); bpy.context.scene.collection.objects.link(c_)
        c_.hide_render = False; c_.hide_viewport = False
        c_.parent = er; c_.matrix_parent_inverse = Matrix.Identity(4); c_.location = (-float(ebv.STEM_C[0]), -float(ebv.STEM_C[1]), 0.0); c_.rotation_euler = (0, 0, 0); c_.scale = (1, 1, 1)
        out.append(c_)
    return out
m_well = kw.mat("Case well", kw.srgb("#5F666D"), 0.55)                        # イヤホンを差す穴（影で暗い）
m_lid_in = kw.mat("Case lid inside", kw.srgb("#C6CCD2"), 0.35, 0.0, coat=0.4)   # ふたの内側（白い流れが見えるように、少し灰）
LID_OPEN = math.radians(104.0)
# イヤホンのケース：白く丸い箱。ふたは後ろの蝶番で開いていて、中に白いイヤホンが二つ差さっている。前に小さな灯
def case_table(name, X, Y, yaw, m_body, band=None):
    root = kw.empty(name); root.location = (X, Y, 0); root.rotation_euler = (0, 0, yaw)
    W_, D_, T_ = 1.20, 0.74, 0.38
    # 体：下の角は大きく丸く（0.16）、上の縁（開いた口）は小さく丸い（0.02）
    prof = list(reversed(arc_prof(0.0, H_TOP - T_ + 0.16, 0.16, up=False))) + arc_prof(0.0, H_TOP - 0.02, 0.02, up=True, n=3)
    bx = loft_rrect(name + " case", W_, D_, 0.16, prof, m_body); bx.parent = root; bx.matrix_parent_inverse = Matrix.Identity(4)
    extra = []
    # ふた：閉じたときは上に 0.13 の厚み（上の角が丸い）。後ろの縁を軸に LID_OPEN だけ開く（内側が前を向く）
    lp = [(0.012, 0.0), (0.0035, 0.0035), (0.0, 0.012), (0.0, 0.035)] + arc_prof(0.0, 0.035, 0.095, up=True, n=7)[1:]
    lid = loft_rrect(name + " lid", W_, D_, 0.16, lp, m_body, y_off=-D_ / 2); lid.parent = root; lid.matrix_parent_inverse = Matrix.Identity(4)
    lid.location = (0, D_ / 2, H_TOP); lid.rotation_euler = (-LID_OPEN, 0, 0)
    li = rounded_slab(name + " lid inside", W_ - 0.11, D_ - 0.11, 0.004, 0.105, m_lid_in); li.parent = lid; li.matrix_parent_inverse = Matrix.Identity(4); li.location = (0, -D_ / 2, 0.0)
    # ↑ 板は局所 z＝0〜−0.004：ふたの内側の面（z＝0、−z 向き）から 4mm 出る
    extra += [lid, li]
    # 中のイヤホン：後ろの左右に差す。耳の先は内側（少し前）を向く（正面を向けると、黒い網が目玉のように見えた）
    for sx in (-1, 1):
        xy = (sx * 0.45, 0.235)
        wl = kw.cyl(name + " well %d" % sx, 0.078, 0.004, m_well, 40); wl.parent = root; wl.matrix_parent_inverse = Matrix.Identity(4); wl.location = (xy[0], xy[1], H_TOP + 0.0012)
        extra.append(wl)
        extra += place_earbud(name + " bud %s" % ("R" if sx > 0 else "L"), root, xy, (-sx * math.cos(math.radians(20)), -math.sin(math.radians(20))), mirror=(sx < 0))
    led_m = kw.mat_emit(name + " led", (0.30, 0.95, 0.55), 2.0)
    led = kw.cyl(name + " led", 0.018, 0.01, led_m, 16); led.parent = root; led.matrix_parent_inverse = Matrix.Identity(4); led.location = (0, -D_ / 2 - 0.001, H_TOP - 0.24); led.rotation_euler = (math.pi / 2, 0, 0)
    ped = kw.cyl(name + " column", 0.07, H_TOP - T_, m_ped, 32); ped.parent = root; ped.matrix_parent_inverse = Matrix.Identity(4); ped.location = (0, 0, (H_TOP - T_) / 2)
    ft = kw.cyl(name + " foot", 0.30, 0.04, m_ped, 48); ft.parent = root; ft.matrix_parent_inverse = Matrix.Identity(4); ft.location = (0, 0, 0.02)
    if band:
        b_ = kw.box(name + " band", (W_ + 0.02, D_ + 0.02, 0.07), band, 0.0); b_.parent = root; b_.matrix_parent_inverse = Matrix.Identity(4); b_.location = (0, 0, H_TOP - 0.27); b_.scale = (0.99, 0.985, 1.0)
    return dict(root=root, led=led_m, W=W_, D=D_, extra=extra)
TOP["E"] = case_table("Earbud case", X_E, Y_EDGE + 0.37, 0.0, m_case)
NBT = case_table("Neighbor case", NB.x, NB.y, NB_YAW, m_case, band=m_amber)

# ================================================================ 台の上：口の輪、コップ（下の皿ごと）、ひみつの色のびん、白のびん
def slot_pos(k, which):
    return Vector((XS[k] + (INNER[k] if which == "send" else -INNER[k]) * DX_SLOT, Y_SLOT, H_TOP))
for k in ("P", "E"):
    for which in ("send", "recv"):
        rg = kw.torus("Slot ring %s %s" % (k, which), 0.125, 0.006, m_slot, 48, 8); rg.location = slot_pos(k, which) + Vector((0, 0, 0.003))
def coaster(name):
    c_ = kw.cyl(name, 0.118, 0.016, m_plate, 48);
    for v in c_.data.vertices: v.co.z += 0.008
    return c_
CUP = {}
for nm_, k0 in (("A", "P"), ("B", "E")):
    pm = kp.paint_mat("Cup paint " + nm_, C_WHITE)
    cu = kp.cup("Cup " + nm_, m_glass, pm, r=CUP_R, h=CUP_H, m_trim=m_trim)
    co = coaster("Coaster " + nm_); cu["root"].parent = co; cu["root"].matrix_parent_inverse = Matrix.Identity(4); cu["root"].location = (0, 0, 0.016)
    CUP[nm_] = dict(cup=cu, coaster=co, home=k0)
HOLD = {}
for k in ("P", "E"):
    X = XS[k]; inner = INNER[k]
    hb = kp.tilt_holder("Secret %s" % k, m_frame, m_bottle[k], None, kind="bottle", axis="y", r=0.06, h=0.24, post_h=0.42)
    hb["root"].location = (X, Y_SLOT, H_TOP)
    hw = kp.tilt_holder("White %s" % k, m_frame, m_wbottle, None, kind="bottle", axis="y", r=0.055, h=0.22, post_h=0.40)
    hw["root"].location = (X + inner * DX_WHITE, Y_SLOT, H_TOP)
    HOLD[k] = dict(secret=hb, white=hw)
# まるロボの背中の板（コップの皿が載る。左右に二つの置き場）
plate = rounded_slab("Maru plate", PLATE_W, PLATE_D, 0.022, 0.05, m_plate)
for s_ in (-1, 1):
    rg = kw.torus("Plate ring %d" % s_, 0.125, 0.006, m_slot, 48, 8); rg.parent = plate; rg.matrix_parent_inverse = Matrix.Identity(4); rg.location = (s_ * DX_SLOT, 0, 0.003)
# 隣のイヤホンの台の上：見えた色の写し（薄く光る）と、混ぜた写し
def ghost_mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1); em.inputs["Strength"].default_value = 1.2
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.55
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    oo = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(mx.outputs[0], oo.inputs[0])
    try: m.surface_render_method = "BLENDED"
    except Exception: pass
    m.diffuse_color = (*rgb, 0.5); return m
GH = {}
for nm_, rgb in (("A", C_SEND["A"]), ("B", C_SEND["B"]), ("M", C_PALE)):
    gm = ghost_mat("Ghost " + nm_, rgb)
    g = kp.cup("Ghost cup " + nm_, gm, gm, r=CUP_R * 0.9, h=CUP_H * 0.9)
    GH[nm_] = g
NB_M = Matrix.Translation(NB) @ Matrix.Rotation(NB_YAW, 4, "Z")
GH_POS = dict(A=NB_M @ Vector((-0.20, -0.05, H_TOP)), B=NB_M @ Vector((0.20, -0.05, H_TOP)), M=NB_M @ Vector((0.0, -0.05, H_TOP)))

# ================================================================ 注ぐ予定・絵の具の量と色
# 誰が・いつ・どのコップへ：（時刻, 台, びん, 向き ±1（+x へ傾く＝+1）, コップ, 加える絵の具）
def tilt_dir(k, which): return 1.0 if (INNER[k] if which == "send" else -INNER[k]) > 0 else -1.0
POURS = []
for k in ("P", "E"):
    POURS.append((T_WHITE, k, "white", -INNER[k], "A" if k == "P" else "B", WHITE))
    POURS.append((T_SEC1[k], k, "secret", tilt_dir(k, "send"), "A" if k == "P" else "B", BLUE if k == "P" else RED))
    POURS.append((T_SEC2[k], k, "secret", tilt_dir(k, "recv"), "B" if k == "P" else "A", BLUE if k == "P" else RED))
LV_WHITE, LV_DROP = 0.105, 0.012                                              # 白で満ちる高さ、ひみつの色で増える高さ
# 白は量が多い（内径 0.176m × 高さ 0.105m ≒ 2.5L）。口いっぱいの流れ（太さ約2.6cm・落ちる速さ約2m/秒 → 約1.1L/秒）で約2.3秒かけて注ぐ。
# 傾けるのに 0.45 秒、流れは傾きが 9 割になった所で始まり、びんが空になって止む。ひみつの色（約0.3L）は細い流れで約0.35秒（前のまま）
POUR_W = dict(ti=0.45, fs=0.34, fe=0.34 + 2.30, to=0.45, ramp=0.15, thick=1.3)
def trap_q(t, a, b, r):
    """流れの強さ（0〜1）：a で始まり r 秒で強まって一定、b の r 秒前から弱まり b で止む"""
    if t <= a or t >= b: return 0.0
    return min(1.0, (t - a) / r, (b - t) / r)
def trap_u(t, a, b, r):
    """注いだ量の割合（0→1）：trap_q の積分"""
    if t <= a: return 0.0
    if t >= b: return 1.0
    T_ = b - a; x = t - a
    if x < r: ar = 0.5 * x * x / r
    elif x <= T_ - r: ar = 0.5 * r + (x - r)
    else: y = T_ - x; ar = (T_ - r) - 0.5 * y * y / r
    return ar / (T_ - r)
def contents(nm_, t):
    """（絵の具, 液の高さ）：注がれた分だけ（流れの間に少しずつ）"""
    pt = cm.Paint(); lv = 0.0; last = None
    for t0, k, kind, dr, cup_, paint in POURS:
        if cup_ != nm_: continue
        u = trap_u(t, t0 + POUR_W["fs"], t0 + POUR_W["fe"], POUR_W["ramp"]) if kind == "white" else mjv((t - t0 - 0.25) / 0.35)
        if u <= 0: continue
        for pg, amt in paint.items(): pt[pg] = pt.get(pg, 0.0) + amt * u
        lv += (LV_WHITE if kind == "white" else LV_DROP) * u
    if t >= T_KEY: lv -= 0.03 * mjv((t - T_KEY) / 0.8)                      # 鍵になって少し減る
    return pt, lv
def paint_rgb(pt):
    if pt.amount() < 1e-6: return C_WHITE
    return pt.linear()

# ================================================================ コップの位置（台・背中・滑る）
def cup_pos(nm_, f):
    """コップ（下の皿）の世界の位置と向き：台の口 → 滑って背中の板 → 背中 → 滑って相手の台の口"""
    t = T0S + (f - 1) / FPS
    fr = frames[min(f - 1, len(frames) - 1)]; Mc = rig.world_mats(fr)["cargo"]; qc = Mc.to_quaternion()
    ev = [e for e in EXS if e[2] == nm_]                                     # 時刻の順：on（台→背中）、off（背中→台）
    def back(side): return Mc @ Vector((SGN_X * side * DX_SLOT, 0, PLATE_TOP))
    pos, q = slot_pos(CUP[nm_]["home"], "send"), Quaternion()
    for (a, b, c, d, k, which, side) in ev:
        tbl = slot_pos(k, which)
        if t < a: return pos, q
        if t < b:
            u = mjv((t - a) / (b - a))
            if d == "on": return tbl.lerp(back(side), u), Quaternion().slerp(qc, u)
            return back(side).lerp(tbl, u), qc.slerp(Quaternion(), u)
        pos, q = (back(side), qc) if d == "on" else (tbl, Quaternion())
    return pos, q
# 背中の板の向き：体の右（−x）の置き場は板の局所 −x。体が −y を向くので、体の左＝+x＝局所 +x… を確かめる
fr_test = rig.world_mats(frames[min(FR(T_EX - 1.0) - 1, len(frames) - 1)]); lx = fr_test["cargo"].to_3x3().col[0]
SGN_X = 1.0 if lx.x > 0 else -1.0                                          # 背中の板の局所 x が、世界の +x か −x か（台に背を向けたとき）
print("cargo local x in world", [round(v, 2) for v in lx], "SGN_X", SGN_X, flush=True)

# ================================================================ 鍵（受け取ったコップの紫が、鍵の形になって台にしまわれる）
m_key = kp.paint_mat("Key paint", C_KEY)
KEYS = {}
for k in ("P", "E"):
    ky = kp.key("Key " + k, m_key, s=1.35); KEYS[k] = ky
KEY_REST = {"P": Vector((X_P - 0.30, Y_EDGE + 0.50, H_TOP + 0.004)), "E": Vector((X_E - 0.15, Y_EDGE + 0.43, H_TOP + 0.004))}   # E：ケースの中の左右のイヤホンの間の手前（耳の先・びんの台に当たらない）

# ================================================================ 1コマごとに焼く
bk = mr.Baker()
for i in range(N): rig.apply(frames[min(i, len(frames) - 1)], i + 1, bk)
bk.write()
for o in rig.cargo_meshes:                                                 # 元の荷物（箱とトレー）は使わない。背中の板に置き換える
    if o.animation_data: o.animation_data_clear()
    o.hide_render = True; o.hide_viewport = True
bkp = mr.Baker()
def put_mat(ob, M_, f):
    loc, q, sc = M_.decompose()
    for i_ in range(3): bkp.put(ob, "location", i_, f, loc[i_])
    ob.rotation_mode = "QUATERNION"
    for i_ in range(4): bkp.put(ob, "rotation_quaternion", i_, f, q[i_])
for f in range(1, N + 1):
    Wm = rig.world_mats(frames[min(f - 1, len(frames) - 1)]); Mc = Wm["cargo"]
    put_mat(plate, Matrix.Translation(Mc @ Vector((0, 0, PLATE_TOP))) @ Mc.to_quaternion().to_matrix().to_4x4(), f)
# コップ：位置・液面の揺れ（加速度から）・量・色
for nm_, C_ in CUP.items():
    POS = []; ROT = []
    for f in range(1, N + 1):
        p_, q_ = cup_pos(nm_, f); POS.append(np.array(p_)); ROT.append(q_)
    P_ = np.array(POS); acc_w = kc.accel(P_, FPS)
    acc = np.array([np.array(ROT[i].to_matrix().transposed() @ Vector(acc_w[i])) for i in range(len(acc_w))])
    sx = np.clip(kc.slosh(acc[:, 0], FPS, R=CUP_R, h=0.1), -0.25, 0.25); sy = np.clip(kc.slosh(acc[:, 1], FPS, R=CUP_R, h=0.1), -0.25, 0.25)
    cu = C_["cup"]; cu["liquid"].rotation_mode = "XYZ"
    sock = cu["mat"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS
        put_mat(C_["coaster"], Matrix.Translation(Vector(POS[f - 1])) @ ROT[f - 1].to_matrix().to_4x4(), f)
        pt, lv = contents(nm_, t); vis = lv > 0.004
        bkp.put(cu["liquid"], "location", 2, f, 0.01 + max(lv, 0.004)); bkp.put(cu["liquid"], "rotation_euler", 0, f, float(sy[f - 1])); bkp.put(cu["liquid"], "rotation_euler", 1, f, float(-sx[f - 1]))
        bkp.put(cu["paint"], "hide_render", 0, f, 0.0 if vis else 1.0)
        bkp.put(cu["paint_body"], "scale", 2, f, max(lv, 0.004)); bkp.put(cu["paint_body"], "hide_render", 0, f, 0.0 if vis else 1.0)
        if f % 2 == 1 or f == N:
            c = paint_rgb(pt); sock.default_value = (*c, 1.0); sock.keyframe_insert("default_value", frame=f)
            cu["mat"].diffuse_color = (*c, 1.0); cu["mat"].keyframe_insert("diffuse_color", frame=f)
# びん：傾き（注ぐ）と流れ
STREAM = {}
for k in ("P", "E"):
    for kind in ("secret", "white"):
        st_ = kw.cyl("Stream %s %s" % (k, kind), 0.010, 1.0, m_secret_paint[k] if kind == "secret" else m_white_paint, 12)
        for v in st_.data.vertices: v.co.z -= 0.5
        st_.rotation_mode = "QUATERNION"; STREAM[(k, kind)] = st_
TILT = math.radians(108.0)
for k in ("P", "E"):
    for kind in ("secret", "white"):
        hd = HOLD[k][kind]; pv = hd["pivot"]; pv.rotation_mode = "XYZ"; st_ = STREAM[(k, kind)]
        mine = [(t0, dr, cup_) for (t0, kk, kd, dr, cup_, pt_) in POURS if kk == k and kd == kind]
        for f in range(1, N + 1):
            t = T0S + (f - 1) / FPS; ang = 0.0; flow = None; qq = 1.0
            for t0, dr, cup_ in mine:
                if kind == "white":
                    a_ = mjv((t - t0) / POUR_W["ti"]) * (1 - mjv((t - t0 - POUR_W["fe"] + 0.11) / POUR_W["to"]))
                    on_ = t0 + POUR_W["fs"] <= t < t0 + POUR_W["fe"]; q_ = trap_q(t, t0 + POUR_W["fs"], t0 + POUR_W["fe"], POUR_W["ramp"])
                else:
                    a_ = mjv((t - t0) / 0.22) * (1 - mjv((t - t0 - 0.55) / 0.22))
                    on_ = t0 + 0.24 <= t < t0 + 0.60; q_ = 1.0
                if a_ > 0: ang = dr * TILT * a_
                if on_: flow = (t0, cup_); qq = q_
            bkp.put(pv, "rotation_euler", 1, f, ang)                          # y 軸まわり（+ で +x へ傾く）
            if flow is None: bkp.put(st_, "hide_render", 0, f, 1.0); continue
            scene_mouth = (Matrix.Translation(hd["root"].location) @ Matrix.Translation((0, 0, hd["post_h"])) @ Matrix.Rotation(ang, 4, "Y")) @ Vector(hd["mouth"])
            cp, _ = cup_pos(flow[1], f); _, lv = contents(flow[1], t)
            tgt = cp + Vector((0, 0, 0.016 + 0.01 + max(lv, 0.004)))
            d_ = tgt - scene_mouth; q_ = Vector((0, 0, -1)).rotation_difference(d_.normalized())
            for i_ in range(3): bkp.put(st_, "location", i_, f, scene_mouth[i_])
            for i_ in range(4): bkp.put(st_, "rotation_quaternion", i_, f, q_[i_])
            bkp.put(st_, "scale", 2, f, max(d_.length, 1e-3)); bkp.put(st_, "hide_render", 0, f, 0.0)
            if kind == "white":                                               # 流れの太さ：量に合わせて（断面積 ∝ 流れの強さ）
                sxy = POUR_W["thick"] * max(qq, 0.12) ** 0.5
                bkp.put(st_, "scale", 0, f, sxy); bkp.put(st_, "scale", 1, f, sxy)
# 隣のイヤホン：見えた写し（運ばれている間に現れる）→ 混ぜて薄い紫
t_seenA = EXS[0][1] + 0.4; t_seenB = EXS[2][1] + 0.4
for nm_, g in GH.items():
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS
        if nm_ == "A": s_ = mjv((t - t_seenA) / 0.5) * (1 - mjv((t - T_MERGE - 0.55) / 0.25)); p_ = GH_POS["A"].lerp(GH_POS["M"], mjv((t - T_MERGE) / 0.6))
        elif nm_ == "B": s_ = mjv((t - t_seenB) / 0.5) * (1 - mjv((t - T_MERGE - 0.55) / 0.25)); p_ = GH_POS["B"].lerp(GH_POS["M"], mjv((t - T_MERGE) / 0.6))
        else: s_ = mjv((t - T_MERGE - 0.45) / 0.35); p_ = GH_POS["M"]
        put_mat(g["root"], Matrix.Translation(p_) @ Matrix.Rotation(NB_YAW, 4, "Z"), f)
        bkp.put(g["root"], "scale", 0, f, max(s_, 1e-3)); bkp.put(g["root"], "scale", 1, f, max(s_, 1e-3)); bkp.put(g["root"], "scale", 2, f, max(s_, 1e-3))
        lv = 0.11 if nm_ != "M" else 0.13
        bkp.put(g["liquid"], "location", 2, f, 0.01 + lv); bkp.put(g["paint_body"], "scale", 2, f, lv)
# 鍵：受け取ったコップから浮かび、立って前を向き、台に寝て、しまわれる（台の上で光る）
for k in ("P", "E"):
    ky = KEYS[k]; nm_ = "B" if k == "P" else "A"
    for f in range(1, N + 1):
        t = T0S + (f - 1) / FPS
        cp, _ = cup_pos(nm_, f)
        u1 = mjv((t - T_KEY) / 0.9); u2 = mjv((t - T_KEY_IN) / 1.2)
        up_ = cp + Vector((-INNER[k] * 0.10, -0.32, CUP_H + 0.30)); rest = KEY_REST[k]   # 台の手前の上に浮かぶ（びんに隠れない）
        if k == "E": up_ = Vector((X_E - 0.19, up_.y, up_.z))                # 鍵の真ん中を台の真ん中の上に（外へ出ると隣の台に重なって見える）
        p_ = (cp + Vector((0, 0, 0.09))).lerp(up_, u1).lerp(rest, u2)
        R_up = Quaternion((0, 0, 1), 0.0)                                       # 鍵は x 向き・平らな面が前（局所 xz 面）
        R_flat = Quaternion((1, 0, 0), -math.pi / 2)                            # 寝かせる（平らな面が上）
        R_ = R_up.slerp(R_flat, u2)
        sc = max(u1, 1e-3) if t < T_KEY_IN else 1.0
        put_mat(ky, Matrix.Translation(p_) @ R_.to_matrix().to_4x4(), f)
        for ch in hier(ky)[1:]: bkp.put(ch, "hide_render", 0, f, 0.0 if t >= T_KEY + 0.05 else 1.0)
# しまわれたら、ケースの灯が紫に、スマホの画面が少し明るく
led = TOP["E"]["led"].node_tree.nodes["Emission"]
for t_, c_ in ((T0S, (0.30, 0.95, 0.55)), (T_KEY_IN + 1.0, (0.30, 0.95, 0.55)), (T_KEY_IN + 1.3, C_KEY)):
    led.inputs["Color"].default_value = (*c_, 1); led.inputs["Color"].keyframe_insert("default_value", frame=max(1, FR(t_)))
bkp.write()
for ob_ in bpy.data.objects:
    ad = ob_.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path == "hide_render":
                for kp_ in fc.keyframe_points: kp_.interpolation = "CONSTANT"

# ================================================================ カメラ（引きの画が基本。寄るのは色が変わる所と、びんの紹介だけ）
cd_ = bpy.data.cameras.new("Pairing camera"); cam = kw.link(O.new("Pairing camera", cd_)); cd_.sensor_width = 36; cd_.clip_start = 0.05
cd_.dof.use_dof = True; cd_.dof.aperture_fstop = 5.6; scene.camera = cam; cam.rotation_mode = "QUATERNION"
CAM = {
    "WIDE": (Vector((0.0, -4.0, 2.80)), Vector((0.0, 0.50, 1.38)), 30.0),
    "WIDE_N": (Vector((0.95, -4.9, 2.95)), Vector((1.05, 0.85, 1.35)), 28.0),     # 受け渡し：隣のイヤホンも入る
    "CU_P": (Vector((X_P + 0.10, Y_SLOT - 1.25, H_TOP + 0.62)), Vector((X_P, Y_SLOT, H_TOP + 0.40)), 42.0),
    "CU_E": (Vector((X_E - 0.10, Y_SLOT - 1.25, H_TOP + 0.62)), Vector((X_E, Y_SLOT, H_TOP + 0.40)), 42.0),
    "MED_P": (Vector((X_P + 0.30, Y_SLOT - 1.45, H_TOP + 1.35)), Vector((X_P, Y_SLOT + 0.10, H_TOP + 0.18)), 32.0),     # 高い所から：手前のまるロボの背中の板を越えて
    "MED_E": (Vector((X_E - 0.30, Y_SLOT - 1.45, H_TOP + 1.35)), Vector((X_E, Y_SLOT + 0.10, H_TOP + 0.18)), 32.0),
    "TWO": (Vector((0.0, -3.1, 2.65)), Vector((0.0, 0.55, 1.42)), 26.0),                                                # 二つの紫を並べて見る
    "NB": (Vector((NB.x - 1.10, NB.y - 2.95, H_TOP + 1.12)), Vector((NB.x - 0.05, NB.y - 0.05, H_TOP + 0.24)), 32.0),   # v7：上の式の札の下に、開いたふたが見えるように（ケースを画面の下寄りに）
}
SHOTS = [(T0S, "WIDE"), (P[4][0] + 0.10, "CU_P"), (at_char(4, 10), "CU_E"), (P[5][0] - 0.30, "WIDE"),
         (T_SEC1["P"] - 0.55, "MED_P"), (T_SEC1["E"] - 0.55, "MED_E"), (T_SEC1["E"] + 1.6, "WIDE"), (EXS[0][0] - 0.9, "WIDE_N"),
         (T_SEC2["P"] - 0.55, "MED_P"), (T_SEC2["E"] - 0.55, "MED_E"), (T_SEC2["E"] + 1.7, "TWO"), (P[15][0] - 0.25, "NB"), (P[16][0] - 0.30, "TWO")]
SKIP = (P[5][0] - 0.30, P[6][0] - 0.30)                                     # 十人十色（車内の 2D）の間は描かない
def shot_of(t):
    nm_ = SHOTS[0][1]; t_in = SHOTS[0][0]
    for a_, n_ in SHOTS:
        if t >= a_: nm_ = n_; t_in = a_
    return nm_, t_in
def shot(t):
    nm_, t_in = shot_of(t); p, tg, lens = CAM[nm_]; u = t - t_in
    push = 0.035 * min(u, 8.0)                                              # ゆっくり寄る（1秒に 3.5cm）
    d_ = (tg - p).normalized(); return p + d_ * push, tg, lens
bkc = mr.Baker(); ANCH = []
from bpy_extras.object_utils import world_to_camera_view
for f in range(1, N + 1):
    t = T0S + (f - 1) / FPS; p, tg, lens = shot(t); q = (tg - p).to_track_quat("-Z", "Y")
    for i_ in range(3): bkc.put(cam, "location", i_, f, p[i_])
    for i_ in range(4): bkc.put(cam, "rotation_quaternion", i_, f, q[i_])
    bkc.put(cd_, "lens", 0, f, lens); bkc.put(cd_, "dof.focus_distance", 0, f, max((tg - p).length, 0.1))
bkc.write()
for fc in cam.animation_data.action.fcurves:
    for kp_ in fc.keyframe_points: kp_.interpolation = "LINEAR"
# 文字を重ねる所（画面の位置）
bpy.context.view_layer.update()
def anchors_world(f):
    t = T0S + (f - 1) / FPS
    a = dict(tagP=Vector((X_P, Y_EDGE + 0.35, H_TOP + 0.95)), tagE=Vector((X_E, Y_EDGE + 0.37, H_TOP + 0.95)), tagN=NB + Vector((0, 0, H_TOP + 0.75)),
             secP=HOLD["P"]["secret"]["root"].location + Vector((0, 0, 0.78)), secE=HOLD["E"]["secret"]["root"].location + Vector((0, 0, 0.78)),
             whiteP=HOLD["P"]["white"]["root"].location + Vector((0, 0, 0.74)), whiteE=HOLD["E"]["white"]["root"].location + Vector((0, 0, 0.74)),
             ghostA=GH_POS["A"] + Vector((0, 0, 0.30)), ghostB=GH_POS["B"] + Vector((0, 0, 0.30)), ghostM=GH_POS["M"] + Vector((0, 0, 0.34)),
             keyP=KEY_REST["P"], keyE=KEY_REST["E"])
    for nm_ in ("A", "B"):
        cp, _ = cup_pos(nm_, f); a["cup" + nm_] = cp + Vector((0, 0, CUP_H + 0.10)); a["cupb" + nm_] = cp + Vector((0, 0, CUP_H * 0.5))
    return a
for f in range(1, N + 1):
    scene.frame_set(f); row = {}
    for nm_, w_ in anchors_world(f).items():
        v = world_to_camera_view(scene, cam, w_); row[nm_] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
    ANCH.append(row)
def screen_box(objs, f):
    scene.frame_set(f); xs, ys = [], []
    for o in objs:
        for c in o.bound_box:
            v = world_to_camera_view(scene, cam, o.matrix_world @ Vector(c)); xs.append(v.x); ys.append(1 - v.y)
    return [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)]
MATCH = dict(P=screen_box([ph], 1), E=screen_box([o for o in hier(TOP["E"]["root"]) if o.type == "MESH" and o not in TOP["E"]["extra"]], 1))   # 2D から寄る先は箱だけ（ふた・イヤホンを除く。前と同じ所）
EV = [("pop", T0S + 0.6)]
for t0, k, kind, dr, cup_, pt_ in POURS: EV += [("tilt", t0), ("pour", t0 + POUR_W["fs"])] if kind == "white" else [("tilt", t0), ("drip", t0 + 0.32)]
for (a, b, c, d, k, w_, s_) in EXS: EV += [("slide", a), ("clunk", b)]
EV += [("step", T0S + e_["t"]) for e_ in plan.events if e_["kind"] in ("step", "step_turn") and T0S + e_["t"] < T1S]
EV += [("pop", t_seenA), ("pop", t_seenB), ("whoosh", T_MERGE), ("key", T_KEY), ("lock", T_KEY_IN + 1.15)]
json.dump(dict(t0=T0S, t1=T1S, fps=FPS, frames=N, match=MATCH, skip=list(SKIP), shots=[[round(a_, 3), n_] for a_, n_ in SHOTS],
               events=[dict(kind=k_, t=round(t_, 3)) for k_, t_ in sorted(EV, key=lambda e: e[1])],
               times=dict(white=T_WHITE, sec1=T_SEC1, sec2=T_SEC2, exchange=[[round(a, 3), round(b, 3), c, d, k] for a, b, c, d, k, w_, s_ in EXS],
                          seenA=t_seenA, seenB=t_seenB, merge=T_MERGE, key=T_KEY, key_in=T_KEY_IN, P={k_: list(v_) for k_, v_ in P.items()}), anchors=ANCH),
          open(os.path.join(A.out, "pairing_log.json"), "w"), indent=0, ensure_ascii=False)
print("BAKED frames", N, flush=True)

# ================================================================ かすみ・描き方
for m_ in list(bpy.data.materials):
    if m_.use_nodes and not m_.name.startswith("Ghost"): kw.hazify(m_)
kw.render_setup(scene, A.engine, tuple(A.res), A.samples, A.exposure, SUN_DIR)
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
if A.still:
    for tt in A.still.split(","):
        f = FR(float(tt)); scene.frame_set(f)
        scene.render.filepath = os.path.join(A.out, "still_%06.2f.png" % float(tt)); bpy.ops.render.render(write_still=True); print("STILL", tt, flush=True)
elif A.frames:
    f0, f1 = [int(x) for x in A.frames.split(":")]
    scene.frame_start, scene.frame_end = f0, min(f1, N); scene.render.use_overwrite = False; scene.render.use_placeholder = True
    scene.render.filepath = os.path.join(A.out, "frames", "p_")
    if A.video:                                                       # PC の本番用：範囲ごとに mp4（あとでこちらで連番に戻して、図・字幕・声と合わせる）
        scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
        ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "PERC_LOSSLESS"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
        scene.render.use_overwrite = True; scene.render.use_placeholder = False
        scene.render.filepath = os.path.join(A.out, "ch04_pair_")
    bpy.ops.render.render(animation=True); print("SEQ DONE", flush=True)
