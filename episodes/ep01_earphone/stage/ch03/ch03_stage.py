# 第3章「音楽を届ける、小さな旅」舞台の部分（C3〜C11、本編 1:40.2〜2:29.8）
#   巨大スマホの台座の積み込み口で荷物を積む → 歩く → 巨大イヤホンの受付ボックスのローラー台へ後ろ向きに降ろす → 曲が鳴る
# 使い方: blender -b story.blend --python ch03_stage.py -- --out DIR [--still T,T,..] [--frames A:B] [--res W H] [--samples N] [--sun 140] [--save]
#   T は予定の時刻（0 ＝ 本編 100.2 秒）。光は本物の光だけ：太陽・物理の空・物が出す光（スマホの画面、窓と受付ボックスの中の照明、灯）
import bpy, bmesh, sys, os, math, json, argparse, wave
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import numpy as np
from mathutils import Vector, Matrix
import marumotion as mm, marurig as mr
import ch03_plan as cp

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/ch03"); ap.add_argument("--frames", default=""); ap.add_argument("--still", default="")
ap.add_argument("--res", nargs=2, type=int, default=[640, 360]); ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--sun", type=float, default=15.0, help="太陽の方位（度。+X から左回り）。道の右側（カメラを置く側）から照らす"); ap.add_argument("--sun_el", type=float, default=50.0)
ap.add_argument("--sky", type=float, default=0.10, help="物理の空の明るさ（カメラに見える空と、照らす光は同じ）")
ap.add_argument("--sun_e", type=float, default=4.0); ap.add_argument("--exposure", type=float, default=0.0)
ap.add_argument("--font", default=""); ap.add_argument("--song", default=os.path.join(HERE, "..", "human", "audio", "song_mono.wav"))
ap.add_argument("--save", action="store_true"); ap.add_argument("--video", type=int, default=0)
ap.add_argument("--closeup", default="", help="確かめ用：r＝右横、l＝左横、b＝後ろ、f＝右前 から頭と荷物のアップ（静止画だけ）")
ap.add_argument("--engine", default="eevee", help="eevee＝本番と同じ光、workbench＝動きの確認用の簡易描画（速い）")
ap.add_argument("--eb2", type=int, default=1, help="1＝巨大イヤホン v2（なめらかな形・本物らしい材質）、0＝Codex版のまま")
ap.add_argument("--eb_views", type=int, default=0, help="1＝静止画のあとに、イヤホンを見る確かめ用のカメラ（全体・頭のアップ）でも描く")
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
plan, t_arrive = cp.ch03_plan()
frames = mm.simulate(plan, fps=FPS)
N = len(frames); T_END = 49.6 + cp.DV2                        # v2：C11b の終わり（本編 153.6「いま聞こえたのは」）
N = min(N, int(round(T_END * FPS)) + 1)
frames = frames[:N]
MONT = cp.montage_plans()                       # 道のり（M1〜M3）は別の予定で動かし、そのカットの時間だけ差し替える（時間を飛ばす）
for a_, b_, q_, nm_ in MONT:
    fq = mm.simulate(q_, fps=FPS); i0, i1 = int(round(cp.A(a_) * FPS)), int(round(cp.A(b_) * FPS))
    for i in range(i0, min(i1, N)): frames[i] = fq[min(i, len(fq) - 1)]
    plan.events = [e for e in plan.events if not (cp.A(a_) <= e["t"] < cp.A(b_))] + [e for e in q_.events if cp.A(a_) <= e["t"] < cp.A(b_)]
    plan.labels += [(a__, b__, tx) for a__, b__, tx in q_.labels if a__ is not None and cp.A(a_) <= a__ < cp.A(b_)]
plan.events.sort(key=lambda e: e["t"])
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
ld = plan.loads[0]; dk = ld["deck"]; un = plan.unloads[0]
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
scr_img = os.path.join(HERE, "screens", "music_k3.png")             # 巨大スマホの画面：いま送っているまとまり 03 が光る（ch03_screen.py）
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

# ================================================================ 荷物：03（まるロボが運ぶ）・04・05（窓の中で待つ）。札は両面：番号・丸印・この曲のその部分の波形
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
for fc in (-1, 1): label(cargo_root, "03", fc)
label_top(cargo_root, "03")
queue = []
for k, num in enumerate(("04", "05")):
    root = link(O.new("PARCEL " + num, None)); root.parent = DOCKROOT
    body = link(O.new("PARCEL BODY " + num, None)); body.parent = root; body.location = (0, 0, mm.CARGO_HALF[1] - 0.34)   # 箱はトレーの上（3cm 上げる）
    cs = cargo_case.copy(); cs.data = cargo_case.data; link(cs); cs.parent = body; cs.matrix_parent_inverse = Matrix.Identity(4); cs.location = (0, 0, 0); cs.rotation_euler = (0, 0, 0)
    for fc in (-1, 1): label(body, num, fc)
    tr = TRAY_SRC.copy(); tr.data = TRAY_SRC.data; link(tr); tr.parent = root; tr.matrix_parent_inverse = Matrix.Identity(4)
    tr.location = (0, 0, -mm.CARGO_HALF[1] + mm.TRAY_H / 2); tr.rotation_euler = (0, 0, 0); tr.scale = (1, 1, mm.TRAY_H / 0.08)
    label_top(body, num)
    queue.append(root)
GAP = 0.12
F03 = ld["x0"]                                                   # 03 の中心（荷台の中心から前へ）
F_Q = [F03 - CARGO_D - GAP, F03 - 2 * CARGO_D - GAP - 0.04]       # 04・05 の中心
ZC = TOP + mm.CARGO_HALF[1]

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

# シャッター（上から巻き下りる）、受付の灯（琥珀→緑）、自分の印（○）
shutter = bx_obj(box("Booth shutter", (BX["open_w"], 0.02, 1.0), mat("Shutter", srgb("#8C949B"), 0.35, 0.8)), y_front - 0.04, 0.0, DZ + oh)
for o in shutter.data.vertices: o.co.z -= 0.5                     # 原点を上の端に（下へ伸ばす）
lamp_m = mat_emit("Receipt lamp", srgb("#F2A33A"), 4.0); lamp_col = lamp_m.node_tree.nodes["Emission"].inputs["Color"]
lamp = bx_obj(cyl("Receipt lamp", 0.06, 0.03, lamp_m, 24), y_front + 0.02, 0.0, DZ + oh + 0.17); lamp.rotation_euler = (math.pi / 2, 0, 0)
ring = bx_obj(torus("Own mark", 0.26, 0.04, mat_emit("Own mark glow", teal, 2.5)), 0.06, 0.0, BX["height"] + 0.45); ring.rotation_euler = (math.pi / 2, 0, 0)   # 軸の面に付いた印

# ================================================================ まるロボを動かす
rig = mr.MaruRig(maru); bk = mr.Baker()
for i, fr in enumerate(frames): rig.apply(fr, i + 1, bk)

# 荷物の後の動き：受付ボックスの中で止まったら、そのまま（隠れる）。シャッター・灯・曲の時刻を荷物の位置から決める
def cargo_world(fr):
    c = fr["cargo"]
    return np.array(c[1]) if c[0] == "free" else None
t_in = None
for fr in frames:
    Mw = cargo_world(fr)
    if Mw is None or fr["t"] < un["tp"]: continue
    back = -float((Mw[:2, 3] - cp.U) @ NG)                         # ロボの中心から台の奥へ
    if t_in is None and back - mm.CARGO_HALF[0] > DK["near"] + DK["outside"] + 0.06: t_in = fr["t"]
t_in = t_in if t_in is not None else un["t0"] + 4.0
T_SHUT = t_in + 0.10; T_LAMP = T_SHUT + 0.55; T_MUSIC = T_LAMP + 0.25          # シャッターが閉まりきると灯が緑、すぐ曲
print("TIMES in %.2f shutter %.2f lamp %.2f music %.2f (本編 %.2f)" % (t_in, T_SHUT, T_LAMP, T_MUSIC, T_MUSIC + cp.T0), flush=True)

# 押し出し板・04/05・ローラー・シャッター・灯
def mjv(t, t0, T): return mm.mj(t, t0, T)
t_lower = ld["tp"] - 0.85; t_up = ld["t_end"] + 0.15; t_back = t_up + 0.7
t_adv = 31.0                                                       # まるロボが出たあと、04 が前へ進む（0.25m/s）
x_end = ld["x0"]; y_grip = Y_CR + un["x0"] - TRAY_HD + 0.06
for i in range(N):
    t = i / FPS; f = i + 1
    x, v = plan.load_x(ld, t)
    down = mjv(t, t_lower, 0.75) - mjv(t, t_up, 0.6)
    cg = frames[i]["cargo"]
    if ld["tp"] <= t <= ld["t_end"] and cg[0] == "free":            # 押し出し板は荷物の後ろの面に付いて動く（ロボが踏ん張って頭が動いても、離れも、めり込みもしない）
        x_end = float((np.array(cg[1])[:2, 3] - C0) @ F1)
    if t < ld["tp"]: fpos = F03 - mm.CARGO_HALF[0] - 0.03
    elif t < t_back: fpos = (x_end if t <= ld["t_end"] else x_end) - mm.CARGO_HALF[0] - 0.03
    else: fpos = (x_end - mm.CARGO_HALF[0] - 0.03) + (F03 - x_end - 0.25) * mjv(t, t_back, 1.2)
    zp = ZC + 1.32 * (1 - down)                                    # 下りると荷物の高さ、上がると天井の中にしまわれる
    for k_, val in enumerate((0.0, fpos, zp)): bk.put(pusher, "location", k_, f, val)
    for k_, val in enumerate((0.0, fpos, zp + 0.45)): bk.put(pusher_rod, "location", k_, f, val)
    adv = 0.0 if t < t_adv else (F03 - F_Q[0]) * mjv(t, t_adv, 2.6)
    for q, fq in zip(queue, F_Q):
        for k_, val in enumerate((0.0, fq + adv, ZC)): bk.put(q, "location", k_, f, val)
    # 引き込み腕：ふだんはボックスの中。ロボが後ずさりで寄せてくる間に台の端の手前まで伸び、止まってからトレーの横へ出て爪を閉じ（「カチッ」）、
    # トレーと一緒に引き、爪を開く（腕はそこで止まる＝ボックスの中）。爪はトレーの後ろの端から 6cm の所をはさむ
    yb0 = Y_CR + un["x0"] - TRAY_HD + 0.06
    if t < un["t0"]: yc = Y_ARM_REST + (Y_ARM_WAIT - Y_ARM_REST) * mjv(t, un["t0"] - 1.0, 0.95)
    elif t < un["tp"]: yc = Y_ARM_WAIT + (yb0 - Y_ARM_WAIT) * mjv(t, un["t0"] + 0.05, un["tp"] - 0.47 - (un["t0"] + 0.05))
    else:                                                            # 爪はトレーの横をはさんだまま、トレーと一緒に動く（ロボが踏ん張って頭が動いても）
        if t <= un["t_end"] + 0.02 and cg[0] == "free": y_grip = float((np.array(cg[1])[:2, 3] - BO2) @ NG) - TRAY_HD + 0.06
        yc = y_grip
    grip = mjv(t, un["tp"] - 0.42, 0.12) - mjv(t, un["t_end"] + 0.02, 0.15)
    for s_, arm, claw in arms:
        xa = s_ * (DK["width"] / 2 - 0.03)
        for k_, val in enumerate((xa, yc - ARM_L / 2 + 0.02, DZ + 0.0175)): bk.put(arm, "location", k_, f, val)   # レールの上
        for k_, val in enumerate((-s_ * (CLAW_OPEN - (CLAW_OPEN - CLAW_SHUT) * grip), ARM_L / 2 - 0.02, 0.0)): bk.put(claw, "location", k_, f, val)
    s_sh = mjv(t, T_SHUT, 0.55) * oh
    bk.put(shutter, "scale", 2, f, max(s_sh, 0.001))
    g_ = mjv(t, T_LAMP, 0.12)
    amb, grn = srgb("#F2A33A"), srgb("#48D16A")
    for c_ in range(3): bk.put(lamp_m.node_tree, 'nodes["Emission"].inputs[0].default_value', c_, f, amb[c_] * (1 - g_) + grn[c_] * g_)

# ================================================================ カメラ（場面ごと。カットは1コマで切り替える）
cam_d = bpy.data.cameras.new("Ch03 camera"); cam = link(O.new("Ch03 camera", cam_d)); scene.camera = cam
cam_d.sensor_width = 36; cam_d.clip_start = 0.05; cam_d.clip_end = 600; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
V = lambda *a: np.array(a, float)
LP = np.array(cp.L); R_ = np.array(mm.rgt(psi1)); F_ = np.array(mm.fwd(psi1))
def at2(p2, z): return np.array([p2[0], p2[1], z])
def robot_xy(t):
    i = min(max(int(round(t * FPS)), 0), N - 1); return np.array(frames[i]["root"][:2])
HEAD = np.array([-5.6, 10.2, 14.6]); STEMTOP = np.array([0.0, 11.12, 9.0])
perp = np.array([-NG[1], NG[0]])                                  # 受付ボックスの横（左回り）
R2 = np.array(mm.rgt(math.radians(cp.heading_of(-NG))))           # 2本目の道の右
sun2 = np.array([math.cos(SUN_AZ), math.sin(SUN_AZ)]); side_sun = perp if perp @ sun2 > 0 else -perp
win_c = at2(C0 + F1 * (f_front - 0.4), TOP + 0.35)
def lerp(a, b, u): return a + (b - a) * u
C6_END = cc.c6_end()
def shot(t):
    """→ (位置, 見る点, レンズ mm, ピントを合わせる点, 名前)"""
    if t < 5.2:                                                    # C3 画面 → 下へ、積み込み口の03
        u = mm.smooth((t - 1.4) / 3.2)
        sc_ = np.array(SCREEN_C); p0 = sc_ + at2(F_ * 9.5 + R_ * 0.0, -1.6); t0_ = sc_ + V(0, 0, 1.2)      # 画面の上のまとまりの帯（03 が光る）も入れる
        p1 = at2(LP + F_ * 4.9 + R_ * 0.9, 1.75); t1_ = win_c - V(0, 0, 0.25)
        return lerp(p0, p1, u), lerp(t0_, t1_, u), lerp(42.0, 28.0, u), lerp(sc_, win_c, u), "C3"
    if t < 11.5:                                                   # C4 窓の中の 03・04・05（台本 v2：「番号は、曲の順番です」まで 6.3 秒）
        u = mm.smooth((t - 5.2) / 6.3)
        p = at2(C0 + F_ * lerp(1.55, 1.35, u) + R_ * lerp(0.95, 0.75, u), TOP + 1.55); tg = at2(C0 + F_ * (F03 - 0.55), TOP + 0.55)
        return p, tg, 30.0, at2(C0 + F_ * (F03 - 0.3), TOP + 0.6), "C4"
    if t < cp.A(116.9):                                            # C5 あいさつ（v2：111.7〜116.9）
        r = robot_xy(t); p = at2(r + F_ * 3.6 + R_ * 0.35, 1.0); tg = at2(r + F_ * 0.0, 1.05)
        return p, tg, 30.0, tg, "C5"
    if t < cp.A(120.6): return cc.c6a(t, robot_xy)                 # C6a まるロボの右前から右横へ回りこむ（v2：116.9〜120.6）
    if t < 19.4 + cp.DV2: return cc.c6b(t)                         # C6b「目指すのは、あのイヤホン」：遠くの巨大イヤホン
    if t < 22.2 + cp.DV2:                                          # C7 見上げる顔（右前の低い所から。イヤホンはカメラの後ろ、遠く上）
        r = robot_xy(t); u = mm.smooth((t - 19.4 - cp.DV2) / 2.8)
        p = at2(LP + F_ * lerp(2.4, 2.2, u) + R_ * 1.1, 0.5); tg = at2(r, 0.85)
        return p, tg, 30.0, at2(r, 0.9), "C7"
    if t < 27.7 + cp.DV2:                                          # C8 積み込み（右横から）
        r = robot_xy(t); p = at2(r + R_ * 3.9 - F_ * 0.1, 1.35); tg = at2(r - F_ * 0.25, 1.05)
        return p, tg, 26.0, at2(r - F_ * 0.3, 1.3), "C8"
    return cc.shot(t, robot_xy)                                    # C9a・道のり（M1〜M3）・C10・C10b・C11・C11b（ch03_cams.py）

cam.rotation_mode = "QUATERNION"; shots = []
for i in range(N):
    t = i / FPS; p, tg, lens, fp, nm = shot(t)
    q = (Vector(tg) - Vector(p)).to_track_quat("-Z", "Y")
    for k in range(3): bk.put(cam, "location", k, i + 1, p[k])
    for k in range(4): bk.put(cam, "rotation_quaternion", k, i + 1, q[k])
    bk.put(cam_d, "lens", 0, i + 1, lens); bk.put(cam_d, "dof.focus_distance", 0, i + 1, float(np.linalg.norm(np.array(fp) - p)))
    if not shots or shots[-1][1] != nm: shots.append([round(t, 3), nm])
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
log = dict(fps=FPS, frames=N, t0=cp.T0, labels=[[round(a, 3), round(b, 3) if b else None, tx] for a, b, tx in plan.labels], events=plan.events,
           cuts=[s_[0] for s_ in shots[1:]], shots=shots, montage=[[cp.A(a_), cp.A(b_), nm_] for a_, b_, q_, nm_ in MONT], times=dict(t_in=t_in, shutter=T_SHUT, lamp=T_LAMP, music=T_MUSIC, arrive=t_arrive,
                                                     conv=un.get("t_conv", t_in - 1.6), conv_T=un["run"] / un["conv"] + 0.6 if "run" in un else 2.0))
json.dump(log, open(os.path.join(A.out, "ch03_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, default=float)
print("CH03 frames", N, "shots", shots, flush=True)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "ch03_stage.blend"))
if A.still:
    if A.closeup:
        dcd = bpy.data.cameras.new("Debug camera"); dcam = link(O.new("Debug camera", dcd)); dcd.sensor_width = 36; dcd.lens = 32; dcd.clip_start = 0.02
    for tt in A.still.split(","):
        f = int(round(float(tt) * FPS)) + 1; scene.frame_set(f)
        if A.closeup:
            fr_ = frames[f - 1]; r_ = np.array(fr_["root"][:2]); fw_ = np.array(mm.fwd(fr_["psi"])); rt_ = np.array(mm.rgt(fr_["psi"]))
            off = {"r": rt_ * 2.3 + fw_ * 0.2, "l": -rt_ * 2.3 + fw_ * 0.2, "b": -fw_ * 2.6 + rt_ * 0.9, "f": fw_ * 2.2 + rt_ * 1.3,
                   "s": rt_ * 1.75 - fw_ * 0.10, "t": -rt_ * 1.75 - fw_ * 0.10}[A.closeup]
            pc = Vector((*(r_ + off), 1.55 if A.closeup not in "st" else 1.62)); tgc = Vector((*(r_ - fw_ * (0.15 if A.closeup not in "st" else 0.32)), 1.12 if A.closeup not in "st" else 1.28))
            dcd.lens = 32 if A.closeup not in "st" else 26
            dcam.location = pc; dcam.rotation_euler = (tgc - pc).to_track_quat("-Z", "Y").to_euler(); scene.camera = dcam
        scene.render.filepath = os.path.join(A.out, "still_%05.2f%s.png" % (float(tt), ("_" + A.closeup) if A.closeup else "")); bpy.ops.render.render(write_still=True)
        print("STILL", tt, flush=True)
    if A.eb_views:                                                 # イヤホンを見る確かめ用（全体・頭と耳の先のアップ・軸の足もと）
        ecd = bpy.data.cameras.new("EB check camera"); ecam = link(O.new("EB check camera", ecd)); ecd.sensor_width = 36; ecd.clip_start = 0.1; scene.camera = ecam
        P = {k: Vector(tuple(float(x) for x in v)) for k, v in cc.EB_PTS.items()}
        views = [("full", P["eb_base"] + Vector((-24.0, -42.0, 8.0)), (P["eb_base"] + P["eb_top"]) * 0.5 + Vector((0, -2.0, 0)), 24),
                 ("head", P["eb_tip"] + Vector((-20.0, -17.0, -3.0)), (P["eb_tip"] * 0.5 + P["eb_head"] * 0.5), 50),
                 ("back", P["eb_head"] + Vector((22.0, 16.0, -6.0)), (P["eb_head"] * 0.7 + P["eb_stem"] * 0.3), 40),
                 ("base", P["eb_base"] + Vector((-9.0, -13.0, 3.2)), P["eb_base"] + Vector((0, -1.5, 2.4)), 35)]
        for nm_, pc_, tg_, lens_ in views:
            ecd.lens = lens_; ecam.location = pc_; ecam.rotation_euler = (tg_ - pc_).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(A.out, "ebview_%s.png" % nm_); bpy.ops.render.render(write_still=True); print("EBVIEW", nm_, flush=True)
elif A.frames:
    f0, f1 = [int(x) for x in A.frames.split(":")]
    scene.frame_start, scene.frame_end = f0, min(f1, N); scene.render.use_overwrite = False; scene.render.use_placeholder = True   # 何本かで分けて描く（できている絵は飛ばす）
    scene.render.filepath = os.path.join(A.out, "frames", "f_")
    if A.video:                                                       # PC の本番用：範囲ごとに mp4（H.264・ほぼ劣化なし）で書き出す（あとでこちらで字幕・声・図と合わせる）
        scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
        ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "PERC_LOSSLESS"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
        scene.render.use_overwrite = True; scene.render.use_placeholder = False
        scene.render.filepath = os.path.join(A.out, "ch03_stage_")
    bpy.ops.render.render(animation=True)
    print("SEQ DONE", flush=True)
