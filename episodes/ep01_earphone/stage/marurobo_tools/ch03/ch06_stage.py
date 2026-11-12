# 第6章「送り直し（再送）」の舞台（本編 10:54.7〜12:10.4、台本 v2 の 114〜127）
#   第3章の舞台（巨大スマホの積み込み口・道・細い橋・巨大イヤホンの受付ボックス）をそのまま使い、六番の荷物を二回運ぶ
#   1回目：受付ボックスの中で光がなぞる → 誤り（灯が赤）→ スマホの返事ランプのまわりの輪が一周しても返事が来ない → まるロボはスマホへ戻る
#   2回目：スマホに残しておいた 06 をもう一度運ぶ → 光がなぞる → 灯が緑 → 返事の光がスマホへ飛び、返事ランプが緑 → 曲に合わせて揺れる
# 使い方: blender -b story.blend --python ch06_stage.py -- --out DIR [--still T,T,..] [--abs] [--frames A:B] [--res W H] [--samples N] [--engine eevee|workbench]
#   T は予定の時刻（0 ＝ 本編 654.66 秒）。--abs のときは本編の秒。光は本物の光だけ：太陽・物理の空・物が出す光
#   （スマホの画面、窓と受付ボックスの中の照明、灯、なぞる光、返事ランプ、返事の光）
import bpy, bmesh, sys, os, math, json, argparse, wave
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import numpy as np
from mathutils import Vector, Matrix
import marumotion as mm, marurig as mr
import ch03_plan as cp
import ch06_plan as p6

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/ch06"); ap.add_argument("--frames", default=""); ap.add_argument("--still", default="")
ap.add_argument("--abs", action="store_true", help="--still の時刻を本編の秒で書く")
ap.add_argument("--res", nargs=2, type=int, default=[640, 360]); ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--sun", type=float, default=15.0, help="太陽の方位（度。+X から左回り）。道の右側（カメラを置く側）から照らす"); ap.add_argument("--sun_el", type=float, default=50.0)
ap.add_argument("--sky", type=float, default=0.10, help="物理の空の明るさ（カメラに見える空と、照らす光は同じ）")
ap.add_argument("--sun_e", type=float, default=4.0); ap.add_argument("--exposure", type=float, default=0.0)
ap.add_argument("--font", default=""); ap.add_argument("--song", default=os.path.join(HERE, "..", "human", "audio", "song_mono.wav"))
ap.add_argument("--save", action="store_true"); ap.add_argument("--video", type=int, default=0)
ap.add_argument("--closeup", default="", help="確かめ用：r＝右横、l＝左横、b＝後ろ、f＝右前 から頭と荷物のアップ（静止画だけ）")
ap.add_argument("--engine", default="eevee", help="eevee＝本番と同じ光、workbench＝動きの確認用の簡易描画（速い）")
ap.add_argument("--eb2", type=int, default=1, help="1＝巨大イヤホン v2（なめらかな形・本物らしい材質）、0＝Codex版のまま")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
FPS = 24
scene = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials


# ================================================================ 道具
def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def srgb(hexs):
    h = hexs.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out


def link(ob, coll=None): (coll or scene.collection).objects.link(ob); return ob


def mat(name, rgb, rough=0.5, metal=0.0, coat=0.0):
    m = M.new(name); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    if coat: bs.inputs["Coat Weight"].default_value = coat
    m.diffuse_color = (*rgb, 1)                                      # 簡易描画での色
    return m


def mat_emit(name, rgb, strength):
    m = M.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); m.diffuse_color = (*[min(1.0, c * 1.2) for c in rgb], 1); return m


def mesh_obj(name, bm, m, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); ob = link(O.new(name, me))
    if m: me.materials.append(m)
    if smooth:
        for f in me.polygons: f.use_smooth = True
    return ob


def box(name, size, m, bevel=0.0, seg=3):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = mesh_obj(name, bm, m)
    if bevel > 0:
        b = ob.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = seg; b.limit_method = "ANGLE"
    return ob


def cyl(name, r, depth, m, seg=24):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    return mesh_obj(name, bm, m, smooth=True)


def torus(name, major, minor, m, seg=48, rseg=10):
    bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        for j in range(rseg):
            bm.faces.new((rings[i][j], rings[(i + 1) % seg][j], rings[(i + 1) % seg][(j + 1) % rseg], rings[i][(j + 1) % rseg]))
    return mesh_obj(name, bm, m, smooth=True)


def place(ob, pos, psi=0.0, parent=None):
    """pos：世界の位置、psi：marumotion の向き（ローカル +Y が fwd(psi) を向く）"""
    ob.rotation_euler = (0, 0, psi); ob.location = Vector(pos)
    if parent is not None: ob.parent = parent
    return ob


def frame_mat(psi, origin):
    return Matrix.Translation(Vector(origin)) @ Matrix.Rotation(psi, 4, "Z")


FONT = None
for fp in [A.font, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
    if fp and os.path.exists(fp):
        try: FONT = bpy.data.fonts.load(fp); break
        except Exception: pass


def text(name, body, size, m):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.002
    if FONT: cu.font = FONT
    ob = link(O.new(name, cu)); cu.materials.append(m); return ob


# ================================================================ Codex版から使う物だけ残す（まるロボ・巨大イヤホン・巨大スマホ）
scene.frame_set(1)
keep = set()
for n in ("Maru", "Earbud exterior", "Smartphone exterior"): keep |= set(hier(O[n]))
for ob in list(O):
    if ob not in keep: O.remove(ob, do_unlink=True)
for ob in keep:
    if ob.animation_data and ob.name not in [x.name for x in hier(O["Maru"])]:
        mb = ob.matrix_basis.copy(); hr = ob.hide_render; ob.animation_data_clear(); ob.matrix_basis = mb; ob.hide_render = hr
for coll in (bpy.data.materials, bpy.data.worlds, bpy.data.lights):
    for idb in coll:
        if getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt = getattr(idb, "node_tree", None)
        if nt and nt.animation_data: nt.animation_data_clear()
earbud = O["Earbud exterior"]; phone = O["Smartphone exterior"]; maru = O["Maru"]
for o in hier(earbud):
    if o.type == "MESH": o.hide_render = False; o.hide_viewport = False
import ch03_cams as cc
EBX = link(O.new("EARBUD PLACE", None)); earbud.parent = EBX; earbud.matrix_parent_inverse = Matrix.Identity(4)
EBX.matrix_world = Matrix([list(map(float, row)) for row in cc.EBM])   # 2倍、スマホから約 75m 先、耳の先をスマホへ
if A.eb2:                                                          # 作り直した巨大イヤホン（同じ位置・大きさ）。Codex版の部品は隠す
    import earbud_v2 as eb2
    EB2_ROOT, EB2_PARTS = eb2.build(bpy, hide_old=[o for o in hier(earbud) if o.type == "MESH"])
    EB2_ROOT.parent = EBX; EB2_ROOT.matrix_parent_inverse = Matrix.Identity(4)

# ================================================================ まるロボの動き（先に計算：積み込み口の高さ・位置もここで決まる）
TA = p6.A
plan, plan2 = p6.ch06_plan()                     # 前半（1回目）と後半（2回目）。荷物の動きは一つの予定で一回ずつなので、T_BACK（S7 のカット）でつなぐ
fr1 = mm.simulate(plan, fps=FPS); fr2 = mm.simulate(plan2, fps=FPS)
N = int(round(TA(p6.T1) * FPS)) + 1
iB = int(round(TA(p6.T_BACK) * FPS))
frames = [(fr1[min(i, len(fr1) - 1)] if i < iB else fr2[min(i, len(fr2) - 1)]) for i in range(N)]
EVENTS = [e for e in plan.events if e["t"] < TA(p6.T_BACK)] + [e for e in plan2.events if e["t"] >= TA(p6.T_BACK)]
LABELS = [x for x in plan.labels if x[0] is not None and x[0] < TA(p6.T_BACK)] + [x for x in plan2.labels if x[0] is not None and x[0] >= TA(p6.T_BACK)]
MONT = p6.montages()                             # 道のり（スマホへ戻る・もう一度イヤホンへ）は別の予定で動かし、そのカットの時間だけ差し替える（時間を飛ばす）
for a_, b_, q_, nm_ in MONT:
    fq = mm.simulate(q_, fps=FPS); i0, i1 = int(round(TA(a_) * FPS)), int(round(TA(b_) * FPS)); carry_q = bool(q_.carry[0][1])
    for i in range(i0, min(i1, N)):
        f_ = dict(fq[min(i, len(fq) - 1)])
        if not carry_q: f_["cargo"] = frames[i]["cargo"]; f_["cargo_vis"] = frames[i]["cargo_vis"]   # 荷物なしで戻る：荷物は本筋のまま（ボックスの中）
        frames[i] = f_
    EVENTS = [e for e in EVENTS if not (TA(a_) <= e["t"] < TA(b_))] + [e for e in q_.events if TA(a_) <= e["t"] < TA(b_)]
    LABELS += [x for x in q_.labels if x[0] is not None and TA(a_) <= x[0] < TA(b_)]
EVENTS.sort(key=lambda e: e["t"])
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
ld = plan.loads[0]; dk = ld["deck"]; un = plan.unloads[0]
ld2 = plan2.loads[0]; un2 = plan2.unloads[0]
print("DECK1", dk, "DECK2", ld2["deck"], "DZ", un["deck"]["top_z"], un2["deck"]["top_z"], flush=True)
psi1 = ld["psi"]; F1 = np.array(mm.fwd(psi1)); R1 = np.array(mm.rgt(psi1))
C0 = np.array(dk["center"])                    # 押し始めの荷台の中心（水平）
TOP = dk["top_z"]                              # 積み込み口の台の上面＝荷台の上面
def P2(f, r, z=0.0):                           # 積み込み口の座標（前 f・右 r）→ 世界
    v = C0 + F1 * f + R1 * r; return Vector((v[0], v[1], z))

# ================================================================ 材質
m_slate = None
m_petrol = M.get("Petrol aluminium") or mat("Petrol aluminium", srgb("#1F5E66"), 0.35, 0.6)
m_graphite = M.get("Graphite") or mat("Graphite", srgb("#2A2D31"), 0.45, 0.2)
m_titan = M.get("Titanium") or mat("Titanium", srgb("#8E9399"), 0.3, 1.0)
m_steel = mat("Dock steel", srgb("#5C6168"), 0.4, 0.7)
m_roller = mat("Roller", srgb("#C9CCD0"), 0.22, 1.0)
m_dark = mat("Interior dark", srgb("#1A1E22"), 0.7)
m_white = mat("Label white", srgb("#E9ECEE"), 0.45)
m_cyan = M.get("Cyan") or mat("Cyan", srgb("#3FC6C9"), 0.35)
m_plinth = mat("Phone dock", srgb("#A9AFB5"), 0.40, 0.0, coat=0.35)

# ================================================================ 床（1m の石の目地。遠くは空の色へかすむ：e^(−距離/260)）
fm = M.new("Stage slate"); fm.use_nodes = True; nt = fm.node_tree; bs = nt.nodes["Principled BSDF"]
bs.inputs["Roughness"].default_value = 0.62
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
def seam(sock):
    fr_ = nt.nodes.new("ShaderNodeMath"); fr_.operation = "PINGPONG"; fr_.inputs[1].default_value = 0.5; nt.links.new(sock, fr_.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.006; nt.links.new(fr_.outputs[0], lt.inputs[0])
    return lt.outputs[0]
mx_ = nt.nodes.new("ShaderNodeMath"); mx_.operation = "MAXIMUM"; nt.links.new(seam(sep.outputs[0]), mx_.inputs[0]); nt.links.new(seam(sep.outputs[1]), mx_.inputs[1])
cell = nt.nodes.new("ShaderNodeTexVoronoi"); cell.feature = "F1"; cell.inputs["Scale"].default_value = 1.0; cell.inputs["Randomness"].default_value = 0.0
nt.links.new(tc.outputs["Object"], cell.inputs["Vector"])
var = nt.nodes.new("ShaderNodeMapRange"); var.inputs[3].default_value = 0.92; var.inputs[4].default_value = 1.06; nt.links.new(cell.outputs["Color"], var.inputs[0])
base = nt.nodes.new("ShaderNodeMix"); base.data_type = "RGBA"; nt.links.new(mx_.outputs[0], base.inputs[0])
base.inputs[6].default_value = (*srgb("#59616A"), 1); base.inputs[7].default_value = (*srgb("#3E454C"), 1)
tint = nt.nodes.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs[0].default_value = 1.0
nt.links.new(base.outputs[2], tint.inputs[6]); nt.links.new(var.outputs[0], tint.inputs[7]); nt.links.new(tint.outputs[2], bs.inputs["Base Color"])
camd = nt.nodes.new("ShaderNodeCameraData"); fog = nt.nodes.new("ShaderNodeMath"); fog.operation = "MULTIPLY"; fog.inputs[1].default_value = -1.0 / 260.0
nt.links.new(camd.outputs["View Distance"], fog.inputs[0]); ex_ = nt.nodes.new("ShaderNodeMath"); ex_.operation = "EXPONENT"; nt.links.new(fog.outputs[0], ex_.inputs[0])
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; nt.links.new(ex_.outputs[0], inv.inputs[1])
haze = nt.nodes.new("ShaderNodeEmission"); haze.inputs["Color"].default_value = (*srgb("#C3CFDA"), 1); haze.inputs["Strength"].default_value = 1.0
HAZE_EMIT = haze
mixs = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(inv.outputs[0], mixs.inputs[0]); nt.links.new(bs.outputs[0], mixs.inputs[1]); nt.links.new(haze.outputs[0], mixs.inputs[2])
nt.links.new(mixs.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
def W3(s, r, z): xy = cp.RP(s, r); return Vector((float(xy[0]), float(xy[1]), z))
def quads(name, qs, m):
    """道の座標の四角（(s, r, z) の4点）を、世界の座標のままの面にする（床の目地が世界の 1m にそろう）"""
    bm = bmesh.new()
    for q in qs: bm.faces.new([bm.verts.new(W3(*c)) for c in q])
    return mesh_obj(name, bm, m)
def rbox(name, s0, s1, r0, r1, z0, z1, m):
    """道に沿った箱（世界の座標のまま）"""
    return quads(name, [[(s0, r0, z1), (s1, r0, z1), (s1, r1, z1), (s0, r1, z1)], [(s0, r0, z0), (s0, r1, z0), (s1, r1, z0), (s1, r0, z0)],
                        [(s0, r0, z0), (s1, r0, z0), (s1, r0, z1), (s0, r0, z1)], [(s0, r1, z0), (s0, r1, z1), (s1, r1, z1), (s1, r1, z0)],
                        [(s0, r0, z0), (s0, r0, z1), (s0, r1, z1), (s0, r1, z0)], [(s1, r0, z0), (s1, r1, z0), (s1, r1, z1), (s1, r0, z1)]], m)
CN, TR, GR, BR = cp.CANAL, cp.TERRACE, cp.GROOVE, cp.BRIDGE; BIG = 400.0
floor = quads("Stage floor", [[(-BIG, -BIG, 0.0), (CN["s0"], -BIG, 0.0), (CN["s0"], BIG, 0.0), (-BIG, BIG, 0.0)],
                              [(CN["s1"], -BIG, 0.0), (BIG, -BIG, 0.0), (BIG, BIG, 0.0), (CN["s1"], BIG, 0.0)]], fm)
def stone_variant(name, c1, c2):
    m_ = fm.copy(); m_.name = name
    for n_ in m_.node_tree.nodes:
        if n_.bl_idname == "ShaderNodeMix" and n_.data_type == "RGBA" and n_.blend_type == "MIX": n_.inputs[6].default_value = (*srgb(c1), 1); n_.inputs[7].default_value = (*srgb(c2), 1)
    m_.diffuse_color = (*srgb(c1), 1); return m_
m_canal = stone_variant("Canal stone", "#4A5158", "#363C42"); m_terr = stone_variant("Terrace stone", "#78808A", "#5C646D")
quads("Canal bed", [[(CN["s0"], -BIG, -CN["depth"]), (CN["s1"], -BIG, -CN["depth"]), (CN["s1"], BIG, -CN["depth"]), (CN["s0"], BIG, -CN["depth"])]], m_canal)
quads("Canal wall", [[(CN["s0"], -BIG, -CN["depth"]), (CN["s0"], BIG, -CN["depth"]), (CN["s0"], BIG, 0.0), (CN["s0"], -BIG, 0.0)],
                     [(CN["s1"], BIG, -CN["depth"]), (CN["s1"], -BIG, -CN["depth"]), (CN["s1"], -BIG, 0.0), (CN["s1"], BIG, 0.0)]], m_canal)
rbox("Terrace", TR["s0"], GR["s0"], -TR["half"], TR["half"], 0.0, TR["h"], m_terr)
rbox("Terrace", GR["s1"], TR["s1"], -TR["half"], TR["half"], 0.0, TR["h"], m_terr)
m_bridge = mat("Bridge steel", srgb("#7D848C"), 0.38, 0.75)
rbox("Bridge deck", BR["s0"], BR["s1"], -BR["w"] / 2, BR["w"] / 2, -BR["thick"], 0.0, m_bridge)
for sg in (-1, 1):                                                 # 橋の両の縁の低い縁石（高さ 4cm）
    r0_, r1_ = sorted((sg * (BR["w"] / 2 - 0.04), sg * BR["w"] / 2)); rbox("Bridge curb", BR["s0"], BR["s1"], r0_, r1_, 0.0, 0.04, m_bridge)

# ================================================================ 空と太陽（物理の空。太陽の高さ50°、色は計算どおり）
SUN_AZ = math.radians(A.sun); SUN_EL = math.radians(A.sun_el)
SUN_DIR = Vector((math.cos(SUN_AZ) * math.cos(SUN_EL), math.sin(SUN_AZ) * math.cos(SUN_EL), math.sin(SUN_EL)))
wd = bpy.data.worlds.new("Stage sky"); scene.world = wd; wd.use_nodes = True; wn = wd.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"; sky.sun_disc = False
sky.sun_elevation = SUN_EL; sky.sun_rotation = math.atan2(SUN_DIR.y, SUN_DIR.x) - math.pi / 2 + math.pi
sky.altitude = 30.0; sky.air_density = 1.0; sky.dust_density = 0.9; sky.ozone_density = 1.0
bgw = wn.nodes.new("ShaderNodeBackground"); bgw.inputs[1].default_value = A.sky; wn.links.new(sky.outputs[0], bgw.inputs[0])
wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(bgw.outputs[0], wo.inputs["Surface"])
sun_ld = bpy.data.lights.new("Sun", "SUN"); sun_ld.energy = A.sun_e; sun_ld.color = kelvin(5600); sun_ld.angle = math.radians(0.53)
sun = link(O.new("Sun", sun_ld)); sun.rotation_euler = SUN_DIR.to_track_quat("Z", "Y").to_euler()

# ================================================================ 巨大スマホ：積み込み口のある台座の上に立てる。画面は主人公のスマホと同じ曲の画面
PL = dict(w=4.0, d=2.4, h=2.75, win_w=1.5, win_h=1.40, ledge=0.25)
EDGE = dk["edge"]                              # 積み込み口の台の手前の端（受け皿の中心から前へ。マイナス＝後ろ）
f_front = EDGE - PL["ledge"]                   # 台座の前の面
f_mid = f_front - PL["d"] / 2
DOCKROOT = link(O.new("PHONE DOCK", None)); DOCKROOT.matrix_world = frame_mat(psi1, P2(0, 0, 0))
def dk_obj(ob, f, r, z):
    ob.parent = DOCKROOT; ob.location = (r, f, z); return ob     # 台座の座標：ローカル X＝右、Y＝前
wz0 = TOP - 0.03; wz1 = wz0 + PL["win_h"]                       # 窓の下と上
# 台座：窓のまわりの4つの塊で作る（窓に穴を開けるかわり）
W2, D2 = PL["w"] / 2, PL["d"]; ww = PL["win_w"] / 2
dk_obj(box("Dock base", (PL["w"], D2, wz0), m_plinth, 0.02), f_mid, 0.0, wz0 / 2)
dk_obj(box("Dock top", (PL["w"], D2, PL["h"] - wz1), m_plinth, 0.02), f_mid, 0.0, (wz1 + PL["h"]) / 2)
for s_ in (-1, 1):
    dk_obj(box("Dock side", (W2 - ww, D2, wz1 - wz0), m_plinth, 0.0), f_mid, s_ * (ww + (W2 - ww) / 2), (wz0 + wz1) / 2)
dk_obj(box("Dock window back", (PL["win_w"], 0.05, wz1 - wz0), m_dark), f_front - D2 + 0.03, 0.0, (wz0 + wz1) / 2)
for s_ in (-1, 1):
    dk_obj(box("Dock window wall", (0.04, D2 - 0.06, wz1 - wz0), m_dark), f_mid, s_ * (ww - 0.02), (wz0 + wz1) / 2)
dk_obj(box("Dock window ceiling", (PL["win_w"], D2 - 0.06, 0.04), m_dark), f_mid, 0.0, wz1 - 0.02)
dk_obj(box("Dock window frame top", (PL["win_w"] + 0.12, 0.06, 0.06), m_titan, 0.01), f_front + 0.02, 0.0, wz1 + 0.03)
for s_ in (-1, 1):
    dk_obj(box("Dock window frame side", (0.06, 0.06, wz1 - wz0 + 0.12), m_titan, 0.01), f_front + 0.02, s_ * (ww + 0.03), (wz0 + wz1) / 2)
# 窓の中の天井の照明（本物の光：見える帯＋同じ場所の面光源）
strip_m = mat_emit("Dock strip", kelvin(5000), 6.0)
dk_obj(box("Dock light strip", (PL["win_w"] - 0.2, 1.6, 0.012), strip_m), f_front - 0.95, 0.0, wz1 - 0.045)
la = bpy.data.lights.new("Dock window light", "AREA"); la.shape = "RECTANGLE"; la.size, la.size_y = PL["win_w"] - 0.2, 1.6; la.energy = 160.0; la.color = kelvin(5000)
lo = link(O.new("Dock window light", la)); dk_obj(lo, f_front - 0.95, 0.0, wz1 - 0.06)
# 台：外へ出た棚（ローラー）と中のローラー
deck_len = PL["ledge"] + D2 - 0.08
dk_obj(box("Deck frame", (1.20, deck_len, 0.02), m_steel, 0.004), EDGE - deck_len / 2, 0.0, TOP - 0.034)   # 手前はまるロボの頭の上に張り出すので薄く
deck_rollers = []
for k in range(int(deck_len / 0.12)):
    f_ = EDGE - 0.06 - k * 0.12
    r_ = dk_obj(cyl("Deck roller", 0.024, 1.14, m_roller, 16), f_, 0.0, TOP - 0.024); r_.rotation_euler = (0, math.pi / 2, 0); deck_rollers.append(r_)
# 押し出し板：天井のレールから下りて、荷物を押す
pusher = dk_obj(box("Pusher plate", (1.0, 0.04, 0.50), m_titan, 0.008), 0.0, 0.0, 0.0)
pusher_rod = dk_obj(box("Pusher rod", (0.05, 0.05, 0.40), m_titan), 0.0, 0.0, 0.0)
# 台座の上のスマホ（Codex版の形。画面のまわりの部品は使わず、画面に主人公と同じ曲の画像を貼る）
ph_parts = [o for o in hier(phone) if o.type == "MESH"]
PHONE_C = Vector((-10.0, -6.0, 0.04))           # Codex版のスマホの足もとの中心（画面は −Y を向く）
Mph = frame_mat(psi1, P2(f_mid, 0.0, PL["h"] - 0.04)) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation(-PHONE_C)
for o in ph_parts:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mph @ mw
    if o.name.startswith(("Source phone / album", "Source phone / progress", "Static / Cyan", "Static / White markings")) or o.name == "Source phone / screen":
        o.hide_render = True; o.hide_viewport = True
scr_img = os.path.join(HERE, "screens", "music_c6.png")             # 巨大スマホの画面：いま送っているまとまり 06 が光る（ch03_screen.py）
if not os.path.exists(scr_img): scr_img = os.path.join(HERE, "..", "human", "screens", "music.png")
sm = M.new("Giant phone screen"); sm.use_nodes = True; snt = sm.node_tree; snt.nodes.clear()
sem = snt.nodes.new("ShaderNodeEmission"); sem.inputs["Strength"].default_value = 2.2
if os.path.exists(scr_img):
    stx = snt.nodes.new("ShaderNodeTexImage"); stx.image = bpy.data.images.load(scr_img); snt.links.new(stx.outputs["Color"], sem.inputs["Color"])
sgl = snt.nodes.new("ShaderNodeBsdfGlossy"); sgl.inputs["Roughness"].default_value = 0.04
sfr = snt.nodes.new("ShaderNodeFresnel"); sfr.inputs["IOR"].default_value = 1.5              # ガラスの反射：正面で約4%（物理どおり）
smx = snt.nodes.new("ShaderNodeMixShader"); snt.links.new(sfr.outputs[0], smx.inputs[0]); snt.links.new(sem.outputs[0], smx.inputs[1]); snt.links.new(sgl.outputs[0], smx.inputs[2])
sout = snt.nodes.new("ShaderNodeOutputMaterial"); snt.links.new(smx.outputs[0], sout.inputs[0])
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
uvl = bm.loops.layers.uv.new("UVMap")
for f_ in bm.faces:
    for l_ in f_.loops: l_[uvl].uv = (l_.vert.co.x + 0.5, l_.vert.co.y + 0.5)
for v in bm.verts: v.co = Vector((v.co.x * 3.22, 0.0, v.co.y * 6.80))
screen = mesh_obj("Giant phone screen", bm, sm)
screen.matrix_world = Mph @ Matrix.Translation(Vector((-10.0, -6.335, 3.69)))
SCREEN_C = screen.matrix_world.translation.copy()


# ================================================================ スマホの返事ランプ（台座の正面、窓の右。正面から見て）
#   まんなかのレンズ（返事が届くと緑に光り、前を照らす）と、まわりの 24 の小さな灯（返事を待つ時間。12時から時計回りに一つずつ点く）
LAMP_X, LAMP_Z = -1.40, 2.00                     # 台座の座標（右 −1.40 ＝ 正面から見て窓の右）
GREEN = srgb("#48D16A"); RED = srgb("#E5484D"); AMBER = srgb("#F2A33A"); AMBER_LED = srgb("#FFB13B")
m_bezel = mat("Reply lamp bezel", srgb("#24282D"), 0.45, 0.3)
dk_obj(cyl("Reply lamp bezel", 0.40, 0.05, m_bezel, 48), f_front + 0.025, LAMP_X, LAMP_Z).rotation_euler = (math.pi / 2, 0, 0)
def principled_emit(name, base_hex, emit_rgb, rough=0.3):
    """ふだんは暗い色の面、光らせると emit_rgb で光る材質 → (材質, 光の強さの path)"""
    m_ = mat(name, srgb(base_hex), rough); bs_ = m_.node_tree.nodes["Principled BSDF"]
    bs_.inputs["Emission Color"].default_value = (*emit_rgb, 1); bs_.inputs["Emission Strength"].default_value = 0.0
    idx = list(bs_.inputs).index(bs_.inputs["Emission Strength"])
    return m_, 'nodes["Principled BSDF"].inputs[%d].default_value' % idx
ring_leds = []
for k in range(24):
    th = math.radians(90.0 - (k + 0.5) * 15.0)                    # 正面から見た角度（右が 0、上が 90°）。台座の右（＋X）は、正面から見ると左
    m_, path_ = principled_emit("Reply ring LED %02d" % k, "#3A3F45", AMBER_LED, 0.35)
    sg = dk_obj(box("Reply ring LED", (0.072, 0.016, 0.034), m_, 0.004, 2), f_front + 0.058, LAMP_X - 0.31 * math.cos(th), LAMP_Z + 0.31 * math.sin(th))
    sg.rotation_euler = (0, th - math.pi / 2, 0)                 # 長い辺が円の接線に沿う
    ring_leds.append((m_, path_))
m_lens, LENS_PATH = principled_emit("Reply lamp lens", "#2C3A33", GREEN, 0.22)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=0.22)
for v in bm.verts: v.co.y *= 0.35                                 # 平たい丸いレンズ（前へ 7.7cm ふくらむ）
lens_obj = dk_obj(mesh_obj("Reply lamp lens", bm, m_lens, smooth=True), f_front + 0.05, LAMP_X, LAMP_Z)
ll = bpy.data.lights.new("Reply lamp light", "POINT"); ll.color = GREEN; ll.energy = 0.0; ll.shadow_soft_size = 0.12
lamp_light = dk_obj(link(O.new("Reply lamp light", ll)), f_front + 0.30, LAMP_X, LAMP_Z)
LAMP_W = DOCKROOT.matrix_world @ Vector((LAMP_X, f_front + 0.05 + 0.077, LAMP_Z))      # レンズの前の面（世界）

# ================================================================ 荷物：06（まるロボが運ぶ）・07・08（窓の中で待つ）・残しておく 06。札は両面：番号・丸印・この曲のその部分の波形
def song_bars(part, n=9):
    """曲（主人公が聴いていた部分：本編 81.0〜84.5 秒）を区切った part 番目の音の大きさ"""
    try:
        w = wave.open(A.song); sr = w.getframerate(); w.setpos(int(81.0 * sr)); x = np.frombuffer(w.readframes(int(3.5 * sr)), np.int16).astype(float)
        seg = np.array_split(x, 8)[min(part, 7)]; rms = np.array([math.sqrt(float((c ** 2).mean()) + 1e-9) for c in np.array_split(seg, n)])
        return list(0.35 + 0.65 * rms / max(rms.max(), 1e-9))
    except Exception:
        rng = np.random.default_rng(part); return list(rng.uniform(0.35, 1.0, n))


def label(parent, num, face):
    """face：+1＝ローカル +Y の面、−1＝−Y の面。荷物の大きさ：幅1.04・奥行き0.62・高さ0.68（中心が原点）"""
    y = face * (0.31 + 0.006); rot = 0.0 if face < 0 else math.pi
    root = link(O.new("Label %s %+d" % (num, face), None)); root.parent = parent; root.location = (0, y, 0.02); root.rotation_euler = (math.pi / 2, 0, rot)
    pl = box("Label plate", (0.86, 0.48, 0.01), m_graphite, 0.02); pl.parent = root; pl.location = (0, 0, 0)
    rg = torus("Label ring", 0.055, 0.011, m_cyan, 32, 8); rg.parent = root; rg.location = (-0.30, 0.11, 0.008)
    tx = text("Label number", num, 0.17, m_white); tx.parent = root; tx.location = (0.10, 0.11, 0.006)
    hs = song_bars(int(num))
    for i, hh in enumerate(hs):
        b_ = box("Label bar", (0.026, 0.15 * hh, 0.006), m_white); b_.parent = root; b_.location = (-0.30 + i * 0.075, -0.11, 0.008)
    return root


def label_top(parent, num):
    """上の面の札（番号と波形）：窓の中に並ぶ荷物を上から見ても、一つひとつ違う部分だと分かる"""
    root = link(O.new("Label %s top" % num, None)); root.parent = parent; root.location = (0, 0, 0.34 + 0.004); root.rotation_euler = (0, 0, math.pi)
    pl = box("Label plate", (0.62, 0.34, 0.008), m_graphite, 0.02); pl.parent = root
    tx = text("Label number", num, 0.13, m_white); tx.parent = root; tx.location = (-0.17, 0.0, 0.006)
    for i, hh in enumerate(song_bars(int(num), 7)):
        b_ = box("Label bar", (0.022, 0.20 * hh, 0.006), m_white); b_.parent = root; b_.location = (0.02 + i * 0.04, 0.0, 0.007)
    return root


cargo_root = O["Maru cargo"]; cargo_case = O["Maru cargo case"]
TRAY_SRC = O["Cradle"]                                           # トレー＝前の荷台の板（まるロボの分は MaruRig が荷物の下へ移す）
for o in hier(cargo_root)[1:]:
    if o is not cargo_case: o.hide_render = True; o.hide_viewport = True
CARGO_D = 2 * mm.CARGO_HALF[0]
NUMS = ["06", "07", "08"]                                        # 運ぶ荷物 06、窓の中で待つ 07・08
for fc in (-1, 1): label(cargo_root, NUMS[0], fc)
label_top(cargo_root, NUMS[0])
def parcel_copy(num, name):
    """窓の中に置く荷物（箱・両面の札・上の札・トレー）。台座の座標で (0, 前, 高さ) に置く"""
    root = link(O.new(name, None)); root.parent = DOCKROOT
    body = link(O.new(name + " BODY", None)); body.parent = root; body.location = (0, 0, mm.CARGO_HALF[1] - 0.34)   # 箱はトレーの上（3cm 上げる）
    cs = cargo_case.copy(); cs.data = cargo_case.data; link(cs); cs.parent = body; cs.matrix_parent_inverse = Matrix.Identity(4); cs.location = (0, 0, 0); cs.rotation_euler = (0, 0, 0)
    for fc in (-1, 1): label(body, num, fc)
    tr = TRAY_SRC.copy(); tr.data = TRAY_SRC.data; link(tr); tr.parent = root; tr.matrix_parent_inverse = Matrix.Identity(4)
    tr.location = (0, 0, -mm.CARGO_HALF[1] + mm.TRAY_H / 2); tr.rotation_euler = (0, 0, 0); tr.scale = (1, 1, mm.TRAY_H / 0.08)
    label_top(body, num)
    return root
queue = [parcel_copy(num, "PARCEL " + num) for num in NUMS[1:3]]
copies = [parcel_copy("06", "PARCEL 06 KEEP A"), parcel_copy("06", "PARCEL 06 KEEP B")]   # スマホに残しておく 06（返事が来るまで消さない）
GAP = 0.12
F03 = ld["x0"]                                                   # 06 の中心（荷台の中心から前へ）
F_Q = [F03 - CARGO_D - GAP, F03 - 2 * CARGO_D - GAP - 0.04]       # 07・08 の中心
ZC = TOP + mm.CARGO_HALF[1]
for c_ in copies: c_.location = (0.0, F03, ZC)

# ================================================================ 受付ボックス（巨大イヤホンの軸に付く）と動力ローラー台
NG = cp.NG; E = cp.E; BX = cp.BOOTH; DK = cp.DOCK
psi_g = math.atan2(-NG[0], NG[1])                                 # ボックスのローカル +Y が外（NG）を向く
BOOTH = link(O.new("RECEIVING BOOTH", None)); BOOTH.matrix_world = frame_mat(psi_g, Vector((*(E + NG * cp.R_STEM), 0.0)))
def bx_obj(ob, y, x, z):
    ob.parent = BOOTH; ob.location = (x, y, z); return ob            # ローカル Y＝軸の面から外へ
y_front = BX["depth"]; emb = 0.45                                  # 前の面、軸の中へ埋める深さ（曲面との隙間をなくす）
DZ = un["deck"]["top_z"] if "deck" in un else DK["height"]   # 受け取り台の上面＝引き取り始めの受け皿の上面
ow, oh = BX["open_w"] / 2, BX["open_h"]
yb_mid = (y_front - emb) / 2
bx_obj(box("Booth lower", (BX["width"], y_front + emb, DZ - 0.05), m_petrol, 0.03), yb_mid, 0.0, (DZ - 0.05) / 2)
bx_obj(box("Booth upper", (BX["width"], y_front + emb, BX["height"] - DZ - oh), m_petrol, 0.03), yb_mid, 0.0, DZ + oh + (BX["height"] - DZ - oh) / 2)
for s_ in (-1, 1):
    bx_obj(box("Booth side", (BX["width"] / 2 - ow, y_front + emb, oh + 0.05), m_petrol, 0.0), yb_mid, s_ * (ow + (BX["width"] / 2 - ow) / 2), DZ - 0.05 + (oh + 0.05) / 2)
bx_obj(box("Booth inside back", (BX["open_w"], 0.04, oh), m_dark), 0.10, 0.0, DZ + oh / 2)
for s_ in (-1, 1): bx_obj(box("Booth inside wall", (0.03, y_front - 0.1, oh), m_dark), (y_front + 0.1) / 2, s_ * (ow - 0.015), DZ + oh / 2)
bx_obj(box("Booth inside ceiling", (BX["open_w"], y_front - 0.1, 0.03), m_dark), (y_front + 0.1) / 2, 0.0, DZ + oh - 0.015)
teal = (0.25, 0.95, 0.88)
bx_obj(box("Booth glow strip", (BX["open_w"] - 0.2, 0.6, 0.012), mat_emit("Booth glow", teal, 5.0)), y_front * 0.5, 0.0, DZ + oh - 0.04)
lb = bpy.data.lights.new("Booth inside light", "AREA"); lb.shape = "RECTANGLE"; lb.size, lb.size_y = BX["open_w"] - 0.2, 0.6; lb.energy = 90.0; lb.color = teal
bx_obj(link(O.new("Booth inside light", lb)), y_front * 0.5, 0.0, DZ + oh - 0.06)
# ローラー台（外に0.6m・中に0.9m。0.35m/s で奥へ回る）
dock_len = DK["depth"]; y_d0 = y_front + DK["outside"]               # 台の手前の端
bx_obj(box("Dock frame", (DK["width"], dock_len, 0.05), m_steel, 0.006), y_d0 - dock_len / 2, 0.0, DZ - 0.055)
for s_ in (-1, 1):
    for yy in (y_d0 - 0.05, y_front + 0.08):
        bx_obj(box("Dock leg", (0.05, 0.05, DZ - 0.08), m_steel), yy, s_ * (DK["width"] / 2 - 0.05), (DZ - 0.08) / 2)
dock_rollers = []
for k in range(int(dock_len / 0.10)):
    r_ = bx_obj(cyl("Dock roller", 0.022, DK["width"] - 0.06, m_roller, 16), y_d0 - 0.05 - k * 0.10, 0.0, DZ - 0.022); r_.rotation_euler = (0, math.pi / 2, 0)
    dock_rollers.append(r_)
# 引き込み腕：台の左右のレールから外へ伸び、爪でトレーの横をはさんで、トレーごと台へ引き取る（ロボの受け皿は動かない）
BO2 = E + NG * cp.R_STEM                                           # ボックスの原点（軸の面）
CLAW_OPEN, CLAW_SHUT = 0.005, 0.0265; ARM_L = 0.75; Y_ARM_REST = 0.95; Y_ARM_WAIT = 1.56; TRAY_HD = 0.295; Y_CR = BX["depth"] + DK["outside"] + DK["near"] + float(mm.CRADLE[1])   # 受け皿の中心（ボックスのローカル Y）
arms = []
for s_ in (-1, 1):
    rail = bx_obj(box("Pull rail", (0.05, dock_len, 0.025), m_steel, 0.004), y_d0 - dock_len / 2, s_ * (DK["width"] / 2 - 0.025), DZ - 0.0125)   # 上面がローラーの上と同じ高さ（シャッターが閉まっても当たらない）
    arm = bx_obj(box("Pull arm", (0.035, ARM_L, 0.035), m_titan, 0.006), 0.0, 0.0, 0.0)
    claw = box("Pull claw", (0.04, 0.035, 0.03), m_titan, 0.004); claw.parent = arm      # 開くと内側の端がトレーの横（0.525）から2cm、閉じると触れる
    arms.append((s_, arm, claw))

# シャッター（上から巻き下りる）、受付の灯（琥珀→赤→琥珀→緑）、自分の印（○）
shutter = bx_obj(box("Booth shutter", (BX["open_w"], 0.02, 1.0), mat("Shutter", srgb("#8C949B"), 0.35, 0.8)), y_front - 0.04, 0.0, DZ + oh)
for o in shutter.data.vertices: o.co.z -= 0.5                     # 原点を上の端に（下へ伸ばす）
lamp_m = mat_emit("Receipt lamp", srgb("#F2A33A"), 4.0); lamp_col = lamp_m.node_tree.nodes["Emission"].inputs["Color"]
lamp = bx_obj(cyl("Receipt lamp", 0.06, 0.03, lamp_m, 24), y_front + 0.02, 0.0, DZ + oh + 0.17); lamp.rotation_euler = (math.pi / 2, 0, 0)
ring = bx_obj(torus("Own mark", 0.26, 0.04, mat_emit("Own mark glow", teal, 2.5)), 0.06, 0.0, BX["height"] + 0.45); ring.rotation_euler = (math.pi / 2, 0, 0)   # 軸の面に付いた印

lamp.scale = (1.25, 1.25, 1.0)                                    # 第6章では灯の色が話の中心なので、少し大きく（半径 7.5cm）
lpl = bpy.data.lights.new("Receipt lamp light", "POINT"); lpl.color = AMBER; lpl.energy = 1.5; lpl.shadow_soft_size = 0.05
bx_obj(link(O.new("Receipt lamp light", lpl)), y_front + 0.10, 0.0, DZ + oh + 0.17)                  # 灯の光（灯の前 6cm から、まわりを照らす）
# 調べる門：ボックスの中を前後に動く「∩」の形の枠。荷物はくぐって入る。内側の縁が光り、荷物の上と左右の面を照らしながら、前から奥へなぞる
SCAN_RGB = (0.62, 0.96, 1.0)
m_scan = mat_emit("Scan light", SCAN_RGB, 0.0); SCAN_PATH = 'nodes["Emission"].inputs[1].default_value'
Y_GATE_FRONT, Y_GATE_BACK = 0.885, 0.145                         # ボックスの口のすぐ内側 ⇔ 奥の壁の手前（枠は荷物のまわりを通るので、荷物には当たらない）
GATE = link(O.new("SCAN GATE", None)); GATE.parent = BOOTH; GATE.location = (0.0, Y_GATE_FRONT, DZ)
def gt(ob, x, y, z): ob.parent = GATE; ob.location = (x, y, z); return ob
gt(box("Scan gate top", (1.20, 0.04, 0.04), m_titan, 0.006), 0.0, 0.0, 0.80)                         # 荷物の上 4cm
for s_ in (-1, 1): gt(box("Scan gate leg", (0.04, 0.04, 0.71), m_titan, 0.006), s_ * 0.58, 0.0, 0.07 + 0.355)   # 荷物の横 4cm。下の端は腕より上
gt(box("Scan gate strip", (1.08, 0.026, 0.006), m_scan), 0.0, 0.0, 0.80 - 0.02 - 0.003)
for s_ in (-1, 1): gt(box("Scan gate strip", (0.006, 0.026, 0.65), m_scan), s_ * (0.58 - 0.02 - 0.003), 0.0, 0.07 + 0.355)
scan_lights = []
la_ = bpy.data.lights.new("Scan light top", "AREA"); la_.shape = "RECTANGLE"; la_.size, la_.size_y = 1.06, 0.024; la_.color = SCAN_RGB; la_.energy = 0.0
scan_lights.append(gt(link(O.new("Scan light top", la_)), 0.0, 0.0, 0.80 - 0.03))                    # 下を照らす
for s_ in (-1, 1):
    lb_ = bpy.data.lights.new("Scan light side", "AREA"); lb_.shape = "RECTANGLE"; lb_.size, lb_.size_y = 0.64, 0.024; lb_.color = SCAN_RGB; lb_.energy = 0.0
    o_ = gt(link(O.new("Scan light side", lb_)), s_ * (0.58 - 0.03), 0.0, 0.07 + 0.355); o_.rotation_euler = (0, s_ * math.pi / 2, 0)   # 内側を照らす
    scan_lights.append(o_)

# ================================================================ まるロボを動かす
class Baker6(mr.Baker):
    """毎コマの値をため、最後にまとめてFカーブにする。材質の中の節の木はどれも同じ名前（Shader Nodetree）なので、名前ではなく物そのもので分ける"""
    def put(self, idb, path, index, frame, value):
        self.ch.setdefault((idb.as_pointer(), path, index), [idb, []])[1].append((frame, float(value)))
    def write(self, interp="LINEAR"):
        for (ptr, path, index), (idb, kv) in self.ch.items():
            ad = idb.animation_data or idb.animation_data_create()
            if ad.action is None: ad.action = bpy.data.actions.new(idb.name + " action")
            fc = ad.action.fcurves.find(path, index=index) or ad.action.fcurves.new(path, index=index)
            kv.sort(); fc.keyframe_points.add(len(kv))
            fc.keyframe_points.foreach_set("co", np.array(kv, np.float32).ravel())
            fc.keyframe_points.foreach_set("interpolation", np.full(len(kv), 1 if interp == "LINEAR" else 0, np.int32))
            fc.update()
rig = mr.MaruRig(maru); bk = Baker6()
for i, fr in enumerate(frames): rig.apply(fr, i + 1, bk)

# ---- 出来事の時刻（予定の秒）
T_SCAN = [TA(p6.T_SCAN1), TA(p6.T_SCAN2)]; SCAN_T = p6.SCAN_T
T_SH = [T_SCAN[0] + SCAN_T + 0.10, T_SCAN[1] + SCAN_T + 0.05]       # 光がなぞり終えたら、シャッターが下りる
T_OPEN2 = TA(p6.T_BOX2) - 2.2                                       # 2回目の前に、シャッターが開き、灯が琥珀に戻る（見えない間に）
T_RED_, T_GRN_ = TA(p6.T_RED), TA(p6.T_GREEN)
T_KEEP = [(TA(p6.T_BOX1) + 0.1, TA(p6.T_BACK)), (TA(p6.T_S8) + 0.05, TA(p6.T_DROP))]   # 窓に残しておく 06（入れ替わるのは、窓が見えていない間）
T_ADV_ = TA(p6.T_ADV)
T_R0, T_R1, T_LOST_ = TA(p6.T_RING0), TA(p6.T_RING1), TA(p6.T_LOST)
T_RP0, T_RP1, T_OK_ = TA(p6.T_REPLY0), TA(p6.T_REPLY1), TA(p6.T_LAMP_OK)


def mjv(t, t0, T): return mm.mj(t, t0, T)


def ring_level(t, k):
    """返事を待つ輪の k 番目の灯（0〜1）：順に点き、一周しても返事がないと2回またたいて消える"""
    on = mjv(t, T_R0 + (T_R1 - T_R0) * k / 24.0, 0.06)
    blink = 1.0 - sum(mjv(t, T_LOST_ + a_, 0.03) - mjv(t, T_LOST_ + b_, 0.03) for a_, b_ in ((0.0, 0.16), (0.32, 0.48)))
    return on * blink * (1.0 - mjv(t, T_LOST_ + 0.70, 0.25))


CYC = [dict(ld=ld, un=un), dict(ld=ld2, un=un2)]                    # 1回目・2回目の積む・降ろす
for c in CYC:
    c["t_lower"] = c["ld"]["tp"] - 0.85; c["t_up"] = c["ld"]["t_end"] + 0.15; c["t_back"] = c["t_up"] + 0.7
    c["x_end"] = c["ld"]["x0"]; c["y_grip"] = Y_CR + c["un"]["x0"] - TRAY_HD + 0.06
for i in range(N):
    t = i / FPS; f = i + 1; c = CYC[0] if t < TA(p6.T_BACK) else CYC[1]; ldc = c["ld"]; unc = c["un"]
    cg = frames[i]["cargo"]
    # 押し出し板：荷物の後ろの面に付いて動く（ロボが踏ん張って頭が動いても、離れも、めり込みもしない）
    down = mjv(t, c["t_lower"], 0.75) - mjv(t, c["t_up"], 0.6)
    if ldc["tp"] <= t <= ldc["t_end"] and cg[0] == "free": c["x_end"] = float((np.array(cg[1])[:2, 3] - C0) @ F1)
    if t < ldc["tp"]: fpos = F03 - mm.CARGO_HALF[0] - 0.03
    elif t < c["t_back"]: fpos = c["x_end"] - mm.CARGO_HALF[0] - 0.03
    else: fpos = (c["x_end"] - mm.CARGO_HALF[0] - 0.03) + (F03 - c["x_end"] - 0.25) * mjv(t, c["t_back"], 1.2)
    zp = ZC + 1.32 * (1 - down)                                    # 下りると荷物の高さ、上がると天井の中にしまわれる
    for k_, val in enumerate((0.0, fpos, zp)): bk.put(pusher, "location", k_, f, val)
    for k_, val in enumerate((0.0, fpos, zp + 0.45)): bk.put(pusher_rod, "location", k_, f, val)
    # 窓の中：07・08 は「再送」のあとで前へ（0.3m/s）。残しておく 06 は、返事が来るまで窓の前に
    adv = (F03 - F_Q[0]) * mjv(t, T_ADV_, 2.6)
    for q, fq_ in zip(queue, F_Q):
        for k_, val in enumerate((0.0, fq_ + adv, ZC)): bk.put(q, "location", k_, f, val)
    for cp_, (a_, b_) in zip(copies, T_KEEP):
        vis = a_ <= t < b_
        for o in hier(cp_):
            if o.type in ("MESH", "FONT", "CURVE"): bk.put(o, "hide_render", 0, f, 0.0 if vis else 1.0); bk.put(o, "hide_viewport", 0, f, 0.0 if vis else 1.0)
    # 引き込み腕：ロボが寄せてくる間に台の端の手前まで伸び、止まってからトレーの横へ出て爪を閉じ、トレーと一緒に引き、爪を開く（ボックスの中で止まる）
    #   2回目の前は、シャッターが開いてから、ボックスの中から台の端の手前まで伸びる（見えない間に）
    yb0 = Y_CR + unc["x0"] - TRAY_HD + 0.06
    if t < unc["t0"]:
        if c is CYC[0]: yc = Y_ARM_REST + (Y_ARM_WAIT - Y_ARM_REST) * mjv(t, unc["t0"] - 1.0, 0.95)
        else: y_s = CYC[0]["y_grip"]; yc = y_s + (Y_ARM_WAIT - y_s) * mjv(t, unc["t0"] - 1.4, 1.3)
    elif t < unc["tp"]: yc = Y_ARM_WAIT + (yb0 - Y_ARM_WAIT) * mjv(t, unc["t0"] + 0.05, unc["tp"] - 0.47 - (unc["t0"] + 0.05))
    else:                                                            # 爪はトレーの横をはさんだまま、トレーと一緒に動く
        if t <= unc["t_end"] + 0.02 and cg[0] == "free": c["y_grip"] = float((np.array(cg[1])[:2, 3] - BO2) @ NG) - TRAY_HD + 0.06
        yc = c["y_grip"]
    grip = mjv(t, unc["tp"] - 0.42, 0.12) - mjv(t, unc["t_end"] + 0.02, 0.15)
    for s_, arm, claw in arms:
        xa = s_ * (DK["width"] / 2 - 0.03)
        for k_, val in enumerate((xa, yc - ARM_L / 2 + 0.02, DZ + 0.0175)): bk.put(arm, "location", k_, f, val)   # レールの上
        for k_, val in enumerate((-s_ * (CLAW_OPEN - (CLAW_OPEN - CLAW_SHUT) * grip), ARM_L / 2 - 0.02, 0.0)): bk.put(claw, "location", k_, f, val)
    # シャッター：光がなぞり終えたら下りる（2回目の前に、見えない間に開く）
    s_sh = (mjv(t, T_SH[0], 0.55) - mjv(t, T_OPEN2, 0.55) + mjv(t, T_SH[1], 0.55)) * oh
    bk.put(shutter, "scale", 2, f, max(s_sh, 0.001))
    # 受付の灯：琥珀（待っている）→ 赤（誤りがあった）→ 琥珀 → 緑（受け取れた）。灯の光も同じ色
    w_r = mjv(t, T_RED_, 0.12) - mjv(t, T_OPEN2, 0.12); w_g = mjv(t, T_GRN_, 0.12)
    col = [AMBER[j] * (1 - w_r - w_g) + RED[j] * w_r + GREEN[j] * w_g for j in range(3)]
    for c_ in range(3): bk.put(lamp_m.node_tree, 'nodes["Emission"].inputs[0].default_value', c_, f, col[c_]); bk.put(lpl, "color", c_, f, col[c_])
    bk.put(lamp_m.node_tree, 'nodes["Emission"].inputs[1].default_value', 0, f, 2.5 + 0.6 * w_r + 0.5 * w_g)
    bk.put(lpl, "energy", 0, f, 1.5 + 4.5 * (w_r + w_g))
    # 調べる門：前から奥へなぞる（1.4秒）。シャッターが下りたら、口のすぐ内側へ戻る
    yg = Y_GATE_FRONT
    for k_ in range(2):
        if t >= T_SCAN[k_] - 1e-6: yg = Y_GATE_FRONT + (Y_GATE_BACK - Y_GATE_FRONT) * (mjv(t, T_SCAN[k_], SCAN_T) - mjv(t, T_SH[k_] + 0.7, 1.2))
    bk.put(GATE, "location", 1, f, yg)
    lv = sum(mm.env(t, T_SCAN[k_] - 0.12, 0.12, SCAN_T, 0.2) for k_ in range(2))
    bk.put(m_scan.node_tree, SCAN_PATH, 0, f, 6.0 * lv)
    for o_, e_ in zip(scan_lights, (12.0, 6.0, 6.0)): bk.put(o_.data, "energy", 0, f, e_ * lv)
    # スマホの返事ランプ：待つ間の輪（1回目だけ）、返事が届くとレンズが緑に光る（2回目）
    for k_, (m_, path_) in enumerate(ring_leds): bk.put(m_.node_tree, path_, 0, f, 6.0 * ring_level(t, k_))
    g_ok = mjv(t, T_OK_, 0.08)
    bk.put(m_lens.node_tree, LENS_PATH, 0, f, 4.0 * g_ok + 3.0 * (g_ok - mjv(t, T_OK_ + 0.1, 0.4)))   # 届いた瞬間に少し強く
    bk.put(ll, "energy", 0, f, 12.0 * g_ok)

# ================================================================ 返事の光：受付の灯の前から、スマホの返事ランプのレンズへ（まっすぐ、約 71m を 2.7秒）
#   出るときと着くときに 0.45 秒かけて速さを上げ下げする。速いほど進む向きに細長く見える光の玉（緑）。玉そのものが光り、まわりも照らす
P_START = BOOTH.matrix_world @ Vector((0.0, y_front + 0.02 + 0.05, DZ + oh + 0.17))
P_END = LAMP_W
D_ORB = P_END - P_START; DIR = D_ORB.normalized()
TF = T_RP1 - T_RP0; ta_ = 0.45
_tt = np.linspace(0.0, TF, 2001); _v = np.array([min(mm.smooth(x / ta_), 1.0, mm.smooth((TF - x) / ta_)) for x in _tt])
_ss = np.concatenate([[0.0], np.cumsum((_v[1:] + _v[:-1]) / 2 * np.diff(_tt))]); _ss /= _ss[-1]
m_orb = mat_emit("Reply orb", GREEN, 12.0)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.11)
orb = mesh_obj("Reply orb", bm, m_orb, smooth=True); orb.rotation_mode = "QUATERNION"; orb.rotation_quaternion = DIR.to_track_quat("Y", "Z")
ol = bpy.data.lights.new("Reply orb light", "POINT"); ol.color = GREEN; ol.energy = 0.0; ol.shadow_soft_size = 0.11
orb_l = link(O.new("Reply orb light", ol))
ORB_W = []
for i in range(N):
    t = i / FPS; f = i + 1; vis = T_RP0 <= t <= T_RP1 + 0.05
    u = float(np.interp(t - T_RP0, _tt, _ss)); vn = float(np.interp(t - T_RP0, _tt, _v)) if vis else 0.0
    p = P_START + D_ORB * u
    sc = (0.25 + 0.75 * mjv(t, T_RP0, 0.12)) * (1.0 - mjv(t, T_RP1 - 0.05, 0.08))
    for k_ in range(3): bk.put(orb, "location", k_, f, p[k_]); bk.put(orb_l, "location", k_, f, p[k_])
    for k_, val in enumerate((sc, sc * (1.0 + 1.8 * vn), sc)): bk.put(orb, "scale", k_, f, max(val, 0.001))
    bk.put(orb, "hide_render", 0, f, 0.0 if vis else 1.0); bk.put(orb, "hide_viewport", 0, f, 0.0 if vis else 1.0)
    bk.put(ol, "energy", 0, f, 40.0 * sc if vis else 0.0)
    ORB_W.append([round(p[0], 3), round(p[1], 3), round(p[2], 3)] if vis else None)

# ================================================================ カメラ（場面ごと。カットは1コマで切り替える。場面の名前と始まりは ch06_plan.SHOTS）
import ch03_cams as cc
cam_d = bpy.data.cameras.new("Ch06 camera"); cam = link(O.new("Ch06 camera", cam_d)); scene.camera = cam
cam_d.sensor_width = 36; cam_d.clip_start = 0.05; cam_d.clip_end = 600; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
V = lambda *a: np.array(a, float)
LP = np.array(cp.L); R_ = np.array(mm.rgt(psi1)); F_ = np.array(mm.fwd(psi1)); P3 = cc.P3; S_U = cp.S_U
def at2(p2, z): return np.array([p2[0], p2[1], z])
def robot_xy(t):
    i = min(max(int(round(t * FPS)), 0), N - 1); return np.array(frames[i]["root"][:2])
def route_s(t): return float((robot_xy(t) - LP) @ F_)
def lerp(a, b, u): return a + (b - a) * u
LAMPW = np.array(LAMP_W)
LAMP_CAM, LAMP_TGT = P3(3.4, -1.85, 2.12), P3(-0.55, -1.15, 1.95)    # 返事ランプ：正面のやや左から。左に窓（残しておいた 06）、右にランプ
SHOT_T = [(TA(t_), nm.split()[0]) for t_, nm in p6.SHOTS]
def shot_span(t):
    for j, (t0_, nm) in enumerate(SHOT_T):
        t1_ = SHOT_T[j + 1][0] if j + 1 < len(SHOT_T) else TA(p6.T1) + 1.0
        if t < t1_ - 1e-6: return nm, t0_, t1_
    return SHOT_T[-1][1], SHOT_T[-1][0], TA(p6.T1) + 1.0
def win_shot(u, far=False):
    if far: return at2(C0 + F_ * lerp(1.62, 1.50, u) + R_ * lerp(0.95, 0.85, u), TOP + 1.65), at2(C0 + F_ * (F03 - 0.65), TOP + 0.5), 28.0, at2(C0 + F_ * (F03 - 0.4), TOP + 0.6)
    return at2(C0 + F_ * lerp(1.50, 1.40, u) + R_ * lerp(0.92, 0.84, u), TOP + 1.55), at2(C0 + F_ * (F03 - 0.45), TOP + 0.55), 30.0, at2(C0 + F_ * (F03 - 0.2), TOP + 0.6)
T14 = [t0_ for t0_, nm in SHOT_T if nm == "S14"][0]; T15 = TA(p6.T_IN); TEND = TA(p6.T1)
import earbud_v2 as _e2                                            # 耳の先の口（音の出口）：口の底の黒い網の中心と、耳の先の向き（世界）
MOUTH = cc.eb(_e2.HC + _e2.D * (_e2.S_MOUTH + 0.03)); MDIR = cc.eb(_e2.HC + _e2.D * (_e2.S_MOUTH + 1.03)) - MOUTH; MDIR = MDIR / np.linalg.norm(MDIR)
MOUTH_FRONT = float((cc.eb(_e2.HC + _e2.D * _e2.S_FRONT) - MOUTH) @ MDIR)   # 口の底から前の面まで（世界の m）
def shot(t):
    """→ (位置, 見る点, レンズ mm, ピントを合わせる点, 名前)"""
    nm, t0_, t1_ = shot_span(t); u = mm.smooth((t - t0_) / max(t1_ - t0_, 1e-6))
    if nm == "S1":                                                 # 第3章の C3 と同じく、巨大スマホの画面（いま送るまとまり 06 が光る帯）から、窓の前のまるロボへ下りる
        u1 = mm.smooth((t - 0.35) / 2.45); sc_ = np.array(SCREEN_C); win_c = at2(C0 + F1 * (f_front - 0.4), TOP + 0.35)
        p0 = sc_ + at2(F_ * 9.5, -1.6); t0_ = sc_ + V(0, 0, 1.2); p1 = at2(LP + F_ * 4.9 + R_ * 0.9, 1.75); t1_ = win_c - V(0, 0, 0.25)
        return lerp(p0, p1, u1), lerp(t0_, t1_, u1), lerp(42.0, 28.0, u1), lerp(sc_, win_c, u1), nm
    if nm in ("S2", "S7"):                                         # 窓の中の 06・07・08（積む前から、押し出されるまで）
        p, tg, lens, fp = win_shot(u); return p, tg, lens, fp, nm
    if nm in ("S2b", "S7b"):                                       # 積み込み：右横から（第3章の C8 と同じ）
        r = robot_xy(t); return at2(r + R_ * 3.9 - F_ * 0.1, 1.35), at2(r - F_ * 0.25, 1.05), 26.0, at2(r - F_ * 0.3, 1.3), nm
    if nm == "S3a":                                                # 「受け取る側は、」：低い所から、巨大イヤホンを丸ごと見上げる（足もとに受付ボックスとまるロボ）。少しずつ寄る
        return P3(S_U - lerp(24.0, 22.6, u), lerp(-26.0, -24.8, u), 2.0), P3(S_U + 2.0, 0.5, 15.5), 20.0, P3(S_U, 0.0, 1.5), nm
    if nm in ("S3", "S9"):                                         # 受付ボックス：正面の左の高い所から、まるロボの頭ごしに口の中（腕・なぞる光）
        return P3(S_U - lerp(2.75, 2.60, u), -1.55, 2.70), P3(S_U + 0.95, 0.15, 1.45), 26.0, P3(S_U + 1.2, 0.0, 1.5), nm
    if nm in ("S4", "S11"):                                        # 引き：左に遠くのスマホ、右に巨大イヤホン（図と同じ左右）
        cam_ = P3(lerp(29.0, 30.0, u), lerp(64.0, 65.5, u), lerp(9.0, 9.6, u))
        tg, lens = cc.aim(cam_, cc.PHONE_TOP, -0.80, cc.EB_PTS["eb_stem"], 0.62, cc.EB_PTS["eb_top"], 0.86)
        return cam_, tg, lens, P3(38.0, 0.0, 6.0), nm
    if nm == "S5":                                                 # 灯が赤：右前の低い所から、見上げるまるロボと灯
        return P3(S_U - lerp(3.35, 3.2, u), 2.15, 0.70), P3(S_U + 0.65, -0.15, 1.55), 26.0, P3(S_U + 0.3, 0.0, 1.5), nm
    if nm in ("S6", "S10b"):                                       # スマホの返事ランプ（S10b は S6 と同じ向き：暗いまま → 緑）
        if nm == "S10b": return LAMP_CAM, LAMP_TGT, 45.0, LAMPW, nm
        w6 = mm.smooth((t - t0_) / 2.3)                            # 「返事が来ないので、スマホも」：巨大スマホが丸ごと見える引きから、返事ランプへ寄る
        return lerp(P3(11.0, -3.0, 2.0), LAMP_CAM, w6), lerp(P3(-0.8, -0.9, 4.8), LAMP_TGT, w6), lerp(22.0, lerp(42.0, 45.0, u), w6), LAMPW, nm
    if nm == "S6b":                                                # スマホへ戻る：運河の中の低い所から細い橋を見上げる（右から左へ。来たときと逆）
        return P3(lerp(59.55, 58.45, u), 3.4, -0.80), P3(lerp(59.35, 58.25, u), -0.2, 0.80), 19.0, P3(route_s(t), 0.0, 0.8), nm   # カメラは運河（56.0〜60.0）の内側だけを動く
    if nm == "S8":                                                 # もう一度イヤホンへ：同じ所から（左から右へ）
        return P3(lerp(56.45, 57.55, u), 3.4, -0.80), P3(lerp(56.65, 57.75, u), -0.2, 0.80), 19.0, P3(route_s(t), 0.0, 0.8), nm   # 運河の内側だけ（前は地面の中から始まって暗かった）
    if nm == "S10":                                                # 返事の光：受付ボックスの上から、道の先のスマホを見る（光が遠ざかる）
        return P3(71.35, 0.30, 3.0), P3(-0.55, -0.7, 4.5), 90.0, LAMPW, nm
    if nm == "S12":                                                # 窓：07・08 が前へ
        p, tg, lens, fp = win_shot(u, far=True); return p, tg, lens, fp, nm
    if nm == "S13":                                                # 曲に合わせて揺れる：右前の低い所から（第3章の C11 と同じ）。少しずつ寄る
        return P3(S_U - lerp(3.4, 2.9, u), lerp(2.6, 2.3, u), 1.0), P3(S_U + 0.3, -0.3, 1.25), 26.0, P3(S_U, 0.0, 1.0), nm
    if nm in ("S14", "S15"):                                       # 一つの動き。揺れるまるロボ（巨大イヤホンの足もと）から、昇りながらイヤホンの頭へ寄る
        w = mm.smooth((t - T14) / (T15 - T14)); wt = mm.smooth((t - (T14 + 3.6)) / 5.0)   # 「曲は続いていました」まではまるロボを見て、そのあと頭へ
        cam_ = lerp(P3(51.0, 15.0, 1.6), P3(46.0, 14.0, 22.0), w); tg = lerp(P3(S_U, 0.0, 1.1), P3(69.0, 0.6, 28.6), wt)
        return cam_, tg, lerp(32.0, 38.0, w), tg, nm
    # S16「イヤホンの中を見てみましょう」：耳の先の前へ回りこみ、口の奥の黒い網が画面いっぱいになるまで寄る（次の章のイヤホンの中へ）
    u = mm.smooth((t - T15) / (TEND - T15)); a0 = P3(46.0, 14.0, 22.0); c_ = MOUTH + MDIR * 16.0 + V(0.0, 0.0, 2.5); b0 = MOUTH + MDIR * (MOUTH_FRONT + 0.10)
    cam_ = (1 - u) ** 2 * a0 + 2 * u * (1 - u) * c_ + u ** 2 * b0
    tg = lerp(P3(69.0, 0.6, 28.6), MOUTH - MDIR * 2.0, mm.smooth(min(1.0, (t - T15) / (0.7 * (TEND - T15)))))
    return cam_, tg, lerp(38.0, 30.0, u), MOUTH, nm

cam.rotation_mode = "QUATERNION"; shots = []; CAM_LOG = []
for i in range(N):
    t = i / FPS; p, tg, lens, fp, nm = shot(t)
    q = (Vector(tg) - Vector(p)).to_track_quat("-Z", "Y")
    for k in range(3): bk.put(cam, "location", k, i + 1, p[k])
    for k in range(4): bk.put(cam, "rotation_quaternion", k, i + 1, q[k])
    bk.put(cam_d, "lens", 0, i + 1, lens); bk.put(cam_d, "dof.focus_distance", 0, i + 1, float(np.linalg.norm(np.array(fp) - p)))
    if not shots or shots[-1][1] != nm: shots.append([round(t, 3), nm])
    CAM_LOG.append([round(float(x), 4) for x in (*p, *q, lens)])
bk.write()

# ================================================================ 遠くの物のかすみ（空気の遠近法）：見える光 ＝ 物の光 × e^(−距離/260) ＋ 空の光 × (1 − e^(−距離/260))
# 床と同じ式・同じ空の色を、すべての物に。近く（10m）ではほぼ変わらず、75m 先のイヤホンは約 25% かすむ
def hazify(m_):
    nt_ = m_.node_tree
    if nt_ is None or any(n_.bl_idname == "ShaderNodeCameraData" for n_ in nt_.nodes): return False
    outs = [n_ for n_ in nt_.nodes if n_.bl_idname == "ShaderNodeOutputMaterial" and n_.is_active_output] or [n_ for n_ in nt_.nodes if n_.bl_idname == "ShaderNodeOutputMaterial"]
    if not outs or not outs[0].inputs["Surface"].links: return False
    out = outs[0]; src = out.inputs["Surface"].links[0].from_socket
    cd = nt_.nodes.new("ShaderNodeCameraData"); mu_ = nt_.nodes.new("ShaderNodeMath"); mu_.operation = "MULTIPLY"; mu_.inputs[1].default_value = -1.0 / 260.0
    nt_.links.new(cd.outputs["View Distance"], mu_.inputs[0]); ex2 = nt_.nodes.new("ShaderNodeMath"); ex2.operation = "EXPONENT"; nt_.links.new(mu_.outputs[0], ex2.inputs[0])
    iv = nt_.nodes.new("ShaderNodeMath"); iv.operation = "SUBTRACT"; iv.inputs[0].default_value = 1.0; nt_.links.new(ex2.outputs[0], iv.inputs[1])
    he = nt_.nodes.new("ShaderNodeEmission"); he.inputs["Color"].default_value = tuple(HAZE_EMIT.inputs["Color"].default_value); he.inputs["Strength"].default_value = HAZE_EMIT.inputs["Strength"].default_value
    mx2 = nt_.nodes.new("ShaderNodeMixShader"); nt_.links.new(iv.outputs[0], mx2.inputs[0]); nt_.links.new(src, mx2.inputs[1]); nt_.links.new(he.outputs[0], mx2.inputs[2])
    nt_.links.new(mx2.outputs[0], out.inputs["Surface"]); return True
n_hz = sum(1 for m_ in list(M) if m_.use_nodes and hazify(m_))
print("HAZE materials", n_hz, flush=True)

# ================================================================ 描画の設定と、字幕・効果音のための記録
scene.render.resolution_x, scene.render.resolution_y = A.res; scene.render.resolution_percentage = 100
fm.diffuse_color = (*srgb("#535B63"), 1)
for mn, col in (("Porcelain", "#E8E6E1"), ("Petrol aluminium", "#1F5E66"), ("Graphite", "#2A2D31"), ("Titanium", "#8E9399"), ("Brass", "#B08A4A"),
                ("Silicone", "#D9DCDF"), ("Ivory ceramic", "#ECE8DF"), ("Cyan", "#3FC6C9")):
    for m_ in M:
        if m_.name.startswith(mn) and tuple(m_.diffuse_color)[:3] == (0.800000011920929, 0.800000011920929, 0.800000011920929): m_.diffuse_color = (*srgb(col), 1)
if A.engine == "workbench":                                       # 動きの確認用：光の向きは太陽と同じ、影あり
    scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
    sh.light = "STUDIO"; sh.color_type = "TEXTURE"; sh.show_shadows = True; sh.shadow_intensity = 0.55; sh.show_cavity = True; sh.cavity_type = "WORLD"
    sh.background_type = "WORLD"; scene.world.color = srgb("#AFC3D6"); scene.display.light_direction = tuple(SUN_DIR)
    scene.render.film_transparent = False; fm.diffuse_color = (*srgb("#8E979F"), 1)
scene.render.engine = scene.render.engine if A.engine == "workbench" else "BLENDER_EEVEE_NEXT"; ee = scene.eevee; ee.taa_render_samples = A.samples
ee.use_shadows = True; ee.shadow_resolution_scale = 1.0
try: ee.use_raytracing = False
except Exception: pass
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"; scene.view_settings.exposure = A.exposure
if A.engine == "workbench": scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"
scene.render.image_settings.file_format = "PNG"
for _ld in [l_ for l_ in bpy.data.lights if l_.name.startswith(("Receipt lamp light", "Scan light", "Reply lamp light", "Reply orb light"))]: _ld.use_shadow = False   # 小さな灯の光は影なし（描く時間を減らす）
CARGO_W = []
for fr in frames:
    try: CARGO_W.append([round(float(x), 3) for x in rig.world_mats(fr)["cargo"].translation])
    except Exception: CARGO_W.append(None)
POINTS = dict(phone_lamp=list(LAMP_W), booth_lamp=list(P_START), slot=list(DOCKROOT.matrix_world @ Vector((0.0, F03, ZC + 0.2))),
              eb_head=[float(x) for x in cc.EB_PTS["eb_head"]], eb_tip=[float(x) for x in cc.EB_PTS["eb_tip"]], booth_open=list(BOOTH.matrix_world @ Vector((0.0, y_front, DZ + oh / 2))))
log = dict(fps=FPS, frames=N, t0=p6.T0, labels=[[round(a, 3), round(b, 3) if b else None, tx] for a, b, tx in LABELS], events=EVENTS,
           cuts=[s_[0] for s_ in shots[1:]], shots=shots, montage=[[TA(a_), TA(b_), nm_] for a_, b_, q_, nm_ in MONT],
           times=dict(scan=T_SCAN, scan_T=SCAN_T, shut=T_SH, open2=T_OPEN2, red=T_RED_, green=T_GRN_, ring0=T_R0, ring1=T_R1, lost=T_LOST_, reply0=T_RP0, reply1=T_RP1,
                      lamp_ok=T_OK_, keep=T_KEEP, adv=T_ADV_, back=TA(p6.T_BACK), groove=TA(p6.T_GROOVE)),
           sensor=36.0, cam=CAM_LOG, points=POINTS, cargo=CARGO_W, orb=ORB_W)
json.dump(log, open(os.path.join(A.out, "ch06_log.json"), "w", encoding="utf-8"), ensure_ascii=False, default=float)
print("CH06 frames", N, "shots", shots, flush=True)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "ch06_stage.blend"))
if A.still:
    if A.closeup:
        dcd = bpy.data.cameras.new("Debug camera"); dcam = link(O.new("Debug camera", dcd)); dcd.sensor_width = 36; dcd.lens = 32; dcd.clip_start = 0.02
    for tt in A.still.split(","):
        tp_ = float(tt) - p6.T0 if A.abs else float(tt)
        f = int(round(tp_ * FPS)) + 1; scene.frame_set(f)
        if A.closeup:
            fr_ = frames[f - 1]; r_ = np.array(fr_["root"][:2]); fw_ = np.array(mm.fwd(fr_["psi"])); rt_ = np.array(mm.rgt(fr_["psi"]))
            off = {"r": rt_ * 2.3 + fw_ * 0.2, "l": -rt_ * 2.3 + fw_ * 0.2, "b": -fw_ * 2.6 + rt_ * 0.9, "f": fw_ * 2.2 + rt_ * 1.3}[A.closeup]
            pc = Vector((*(r_ + off), 1.55)); tgc = Vector((*(r_ - fw_ * 0.15), 1.12))
            dcam.location = pc; dcam.rotation_euler = (tgc - pc).to_track_quat("-Z", "Y").to_euler(); scene.camera = dcam
        scene.render.filepath = os.path.join(A.out, "still_%s%s.png" % (tt, ("_" + A.closeup) if A.closeup else "")); bpy.ops.render.render(write_still=True)
        print("STILL", tt, "frame", f, flush=True)
elif A.frames:
    f0, f1 = [int(x) for x in A.frames.split(":")]
    scene.frame_start, scene.frame_end = f0, min(f1, N); scene.render.use_overwrite = False; scene.render.use_placeholder = True   # 何本かで分けて描く（できている絵は飛ばす）
    scene.render.filepath = os.path.join(A.out, "frames", "f_")
    if A.video:                                                       # PC の本番用：範囲ごとに mp4（H.264・ほぼ劣化なし）で書き出す（あとでこちらで字幕・声・図と合わせる）
        scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
        ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "PERC_LOSSLESS"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
        scene.render.use_overwrite = True; scene.render.use_placeholder = False
        scene.render.filepath = os.path.join(A.out, "ch06_stage_")
    bpy.ops.render.render(animation=True)
    print("SEQ DONE", flush=True)
