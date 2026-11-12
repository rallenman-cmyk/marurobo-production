# 第7章「イヤホンの中：バッファ」の舞台（本編 12:15.2〜14:39.2、台本 v2 の 129〜152）
#   イヤホンの中の部屋：貯蔵タワー（積み重なった荷物が、下の再生装置の口へゆっくり沈んでいく＝鳴らした分だけ減る）、
#   昇降機（受付ボックスから上がってきた荷物を、塔の上の扉へ押し出す）、塔の目盛り（積み重なりの高さ＝たまっている曲の長さ）、札「バッファ」
#   動きと時刻は ch07_plan.py（Blender の外でも同じ）。光は本物の光だけ：天井と壁の照明、再生装置の灯と読み取りの光、目盛りの小さな灯、札、昇降機の灯
# 使い方: blender -b story.blend --python ch07_stage.py -- --out DIR [--still T,T,..] [--abs] [--frames A:B] [--res W H] [--samples N] [--engine eevee|workbench]
import bpy, bmesh, sys, os, math, json, argparse, wave
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import numpy as np
from mathutils import Vector, Matrix
import marumotion as mm, marurig as mr
import ch07_plan as p7, ch06_plan as p6

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/ch07"); ap.add_argument("--frames", default=""); ap.add_argument("--still", default="")
ap.add_argument("--abs", action="store_true", help="--still の時刻を本編の秒で書く")
ap.add_argument("--res", nargs=2, type=int, default=[640, 360]); ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--exposure", type=float, default=0.0); ap.add_argument("--save", action="store_true"); ap.add_argument("--video", type=int, default=0)
ap.add_argument("--font", default=""); ap.add_argument("--song", default=os.path.join(HERE, "..", "human", "audio", "song_mono.wav"))
ap.add_argument("--engine", default="eevee", help="eevee＝本番と同じ光、workbench＝動きの確認用の簡易描画（速い）")
ap.add_argument("--wb_color", default="MATERIAL", help="workbench の色：MATERIAL（材質の色）／TEXTURE（画像の札も見せる）")
ap.add_argument("--no_robot", action="store_true", help="まるロボを出さない（2026-11-09 より前の版）")
ap.add_argument("--vprefix", default="", help="mp4 の名前の頭（PC：まるロボの版は ch07r_stage_／ch08r_tower_。前の版の『できた印』と分けるため）")
ap.add_argument("--part", default="ch7", help="ch7＝第7章（12:15.2〜14:39.2）、ch8＝第8章の前半（15:06.2〜15:27.4：たくさんためてから鳴らす）")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
FPS = 24
scene = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials
T_ORIG, T_LAST, SHOTS_P, LOGNAME = (p7.T0, p7.T1, p7.SHOTS, "ch07_log.json") if A.part == "ch7" else (p7.T0_8, p7.T2_8, p7.SHOTS8, "ch08_tower_log.json")
def TA(t_abs): return t_abs - T_ORIG
N = int(round(TA(T_LAST) * FPS)) + 1


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


# ================================================================ story.blend から使うのは、荷物の箱とトレーの形だけ
scene.frame_set(1)
CASE_ME = O["Maru cargo case"].data; TRAY_ME = O["Cradle"].data
TRAY_MATS = [s.material for s in O["Cradle"].material_slots]
ROBOT_KEEP = set(o.name for o in hier(O["Maru"])) if ("Maru" in O and not A.no_robot) else set()   # 2026-11-09：まるロボも部屋に出る（第6章と同じ姿）
for ob in list(O):
    if ob.name not in ROBOT_KEEP: O.remove(ob, do_unlink=True)
for coll in (bpy.data.materials, bpy.data.worlds, bpy.data.lights):
    for idb in coll:
        if getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt = getattr(idb, "node_tree", None)
        if nt and nt.animation_data: nt.animation_data_clear()
m_petrol = M.get("Petrol aluminium") or mat("Petrol aluminium", srgb("#1F5E66"), 0.35, 0.6)
m_graphite = M.get("Graphite") or mat("Graphite", srgb("#2A2D31"), 0.45, 0.2)
m_titan = M.get("Titanium") or mat("Titanium", srgb("#8E9399"), 0.3, 1.0)
m_cyan = M.get("Cyan") or mat("Cyan", srgb("#3FC6C9"), 0.35)
m_white = mat("Label white", srgb("#E9ECEE"), 0.45)
m_steel = mat("Steel", srgb("#5C6168"), 0.4, 0.7)
m_roller = mat("Roller", srgb("#C9CCD0"), 0.22, 1.0)
m_dark = mat("Interior dark", srgb("#14171A"), 0.7)
m_ivory = mat("Ivory ceramic", srgb("#E6E2DA"), 0.42, 0.0, coat=0.25)
m_copper = mat("Brake copper", srgb("#8A5A3C"), 0.35, 0.9)


class Baker6(mr.Baker):
    """毎コマの値をため、最後にまとめてFカーブにする。材質の中の節の木はどれも同じ名前なので、名前ではなく物そのもので分ける"""
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
bk = Baker6()


def obj_emit_mat(name, rgb, k):
    """一つの材質で、物ごとに光の強さを変える（物の色の R ＝ 強さ／k）。目盛りの灯など、たくさんの小さな灯に使う"""
    m_ = M.new(name); m_.use_nodes = True; nt = m_.node_tree; nt.nodes.clear()
    oi = nt.nodes.new("ShaderNodeObjectInfo"); sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(oi.outputs["Color"], sp.inputs[0])
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = k; nt.links.new(sp.outputs[0], mu.inputs[0])
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Base Color"].default_value = (0.10, 0.11, 0.12, 1); bs.inputs["Roughness"].default_value = 0.35
    bs.inputs["Emission Color"].default_value = (*rgb, 1); nt.links.new(mu.outputs[0], bs.inputs["Emission Strength"])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(bs.outputs[0], out.inputs[0]); m_.diffuse_color = (*rgb, 1); return m_


# ================================================================ 部屋：イヤホンの中（床は石の目地、奥は丸い壁、天井に照明）
Z_S, U = p7.Z_SEAT, p7.UNIT_H
fm = M.new("Inside floor"); fm.use_nodes = True; nt = fm.node_tree; bs = nt.nodes["Principled BSDF"]; bs.inputs["Roughness"].default_value = 0.55
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
def seam(sock, w=0.006):
    fr_ = nt.nodes.new("ShaderNodeMath"); fr_.operation = "PINGPONG"; fr_.inputs[1].default_value = 0.5; nt.links.new(sock, fr_.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = w; nt.links.new(fr_.outputs[0], lt.inputs[0]); return lt.outputs[0]
mx_ = nt.nodes.new("ShaderNodeMath"); mx_.operation = "MAXIMUM"; nt.links.new(seam(sep.outputs[0]), mx_.inputs[0]); nt.links.new(seam(sep.outputs[1]), mx_.inputs[1])
base = nt.nodes.new("ShaderNodeMix"); base.data_type = "RGBA"; nt.links.new(mx_.outputs[0], base.inputs[0])
base.inputs[6].default_value = (*srgb("#4A5158"), 1); base.inputs[7].default_value = (*srgb("#2E3338"), 1); nt.links.new(base.outputs[2], bs.inputs["Base Color"])
fm.diffuse_color = (*srgb("#4A5158"), 1)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=20.0); floor = mesh_obj("Inside floor", bm, fm)
# 奥の丸い壁（白い陶器の板と目地）と、左右の壁
R_W, CY = 9.0, -1.0
wm = M.new("Inside wall"); wm.use_nodes = True; wn = wm.node_tree; wb = wn.nodes["Principled BSDF"]; wb.inputs["Roughness"].default_value = 0.45
wtc = wn.nodes.new("ShaderNodeTexCoord"); wsep = wn.nodes.new("ShaderNodeSeparateXYZ"); wn.links.new(wtc.outputs["Object"], wsep.inputs[0])
wsc = wn.nodes.new("ShaderNodeMath"); wsc.operation = "MULTIPLY"; wsc.inputs[1].default_value = 1 / 1.6; wn.links.new(wsep.outputs[2], wsc.inputs[0])
wpp = wn.nodes.new("ShaderNodeMath"); wpp.operation = "PINGPONG"; wpp.inputs[1].default_value = 0.5; wn.links.new(wsc.outputs[0], wpp.inputs[0])
wlt = wn.nodes.new("ShaderNodeMath"); wlt.operation = "LESS_THAN"; wlt.inputs[1].default_value = 0.008; wn.links.new(wpp.outputs[0], wlt.inputs[0])
wmix = wn.nodes.new("ShaderNodeMix"); wmix.data_type = "RGBA"; wn.links.new(wlt.outputs[0], wmix.inputs[0])
wmix.inputs[6].default_value = (*srgb("#DCD8D0"), 1); wmix.inputs[7].default_value = (*srgb("#9A968F"), 1); wn.links.new(wmix.outputs[2], wb.inputs["Base Color"])
wm.diffuse_color = (*srgb("#DCD8D0"), 1)
bm = bmesh.new(); prev = None
for i in range(61):
    a = math.radians(-100 + 200 * i / 60); x, y = R_W * math.sin(a), CY + R_W * math.cos(a)
    v0, v1 = bm.verts.new((x, y, 0)), bm.verts.new((x, y, 9.0))
    if prev: bm.faces.new((prev[0], v0, v1, prev[1]))
    prev = (v0, v1)
wall = mesh_obj("Inside wall", bm, wm, smooth=True)
for zz in (3.2, 6.4):                                                 # 壁の帯（高さの目安）
    rg = torus("Wall band", R_W - 0.03, 0.035, m_titan, 120, 8); rg.location = (0, CY, zz); rg.scale = (1, 1, 1)
# 天井と照明（見える光の板＋同じ所の面光源。5000K）
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=12.0)
ceil = mesh_obj("Inside ceiling", bm, mat("Ceiling", srgb("#C9C6BF"), 0.6)); ceil.location = (0, CY, 9.0); ceil.rotation_euler = (math.pi, 0, 0)
LIGHT_W = kelvin(5000)
for k, (lx, ly) in enumerate(((-2.6, -1.2), (1.6, -1.2), (-0.5, 2.6))):
    pnl = box("Ceiling light panel", (2.6, 1.0, 0.04), mat_emit("Ceiling light %d" % k, LIGHT_W, 9.0)); pnl.location = (lx, ly, 8.97)
    la = bpy.data.lights.new("Ceiling light %d" % k, "AREA"); la.shape = "RECTANGLE"; la.size, la.size_y = 2.6, 1.0; la.energy = 700.0; la.color = LIGHT_W
    lo = link(O.new("Ceiling light %d" % k, la)); lo.location = (lx, ly, 8.93)
# 手前の壁の照明（カメラの後ろ。部屋の手前の壁に並ぶ、柔らかい光の板）
lf = bpy.data.lights.new("Front wall light", "AREA"); lf.shape = "RECTANGLE"; lf.size, lf.size_y = 8.0, 3.0; lf.energy = 900.0; lf.color = kelvin(4600)
lfo = link(O.new("Front wall light", lf)); lfo.location = (0.4, -11.0, 4.0); lfo.rotation_euler = (math.radians(-90), 0, 0)   # −Z を +Y（奥）へ
wd = bpy.data.worlds.new("Inside dark"); scene.world = wd; wd.use_nodes = True; wd.node_tree.nodes["Background"].inputs[1].default_value = 0.0

# ================================================================ 再生装置：上の口に荷物が沈む。前に大きなスピーカー、灯（緑＝鳴っている）、口のまわりの読み取りの光
PW, PD = 1.80, 1.30; SW, SD = 1.12, 0.72                           # 外の幅・奥行き、口の幅・奥行き
pz = Z_S
box("Player base", (PW, PD, Z_S - 0.06), m_graphite, 0.05).location = (0, 0, (Z_S - 0.06) / 2)
for sx in (-1, 1): box("Player top side", ((PW - SW) / 2, PD, 0.06), m_petrol, 0.012).location = (sx * (SW / 2 + (PW - SW) / 4), 0, Z_S - 0.03)
for sy in (-1, 1): box("Player top front", (SW, (PD - SD) / 2, 0.06), m_petrol, 0.012).location = (0, sy * (SD / 2 + (PD - SD) / 4), Z_S - 0.03)
box("Player slot inside", (SW + 0.02, SD + 0.02, 0.02), m_dark).location = (0, 0, 0.30)          # 口の中（暗い）
for sx in (-1, 1): box("Slot wall", (0.01, SD, Z_S - 0.30), m_dark).location = (sx * (SW / 2 + 0.005), 0, (Z_S + 0.30) / 2)
for sy in (-1, 1): box("Slot wall", (SW, 0.01, Z_S - 0.30), m_dark).location = (0, sy * (SD / 2 + 0.005), (Z_S + 0.30) / 2)
READ_RGB = (0.35, 1.0, 0.75)
m_read = mat_emit("Reader glow", READ_RGB, 0.0)
for sy in (-1, 1): box("Reader strip", (SW - 0.04, 0.012, 0.012), m_read).location = (0, sy * (SD / 2 - 0.004), Z_S - 0.012)
for sx in (-1, 1): box("Reader strip", (0.012, SD - 0.04, 0.012), m_read).location = (sx * (SW / 2 - 0.004), 0, Z_S - 0.012)
rl = bpy.data.lights.new("Reader light", "POINT"); rl.color = READ_RGB; rl.energy = 0.0; rl.shadow_soft_size = 0.3
link(O.new("Reader light", rl)).location = (0, 0, Z_S - 0.18)
# スピーカー（前の面）：枠・ふち（ゴム）・振動板・まん中のふた。振動板は曲の低い音に合わせて前後に動く
SPK_Z = 0.52; SPK_Y = -PD / 2
spk = link(O.new("SPEAKER", None)); spk.location = (0, SPK_Y, SPK_Z); spk.rotation_euler = (math.pi / 2, 0, 0)   # ローカル +Z が前（−Y）
fr_ = torus("Speaker frame", 0.43, 0.035, m_titan, 64, 10); fr_.parent = spk; fr_.location = (0, 0, 0.005)
sur = torus("Speaker surround", 0.385, 0.03, mat("Rubber", srgb("#1C1E21"), 0.8), 64, 10); sur.parent = spk; sur.location = (0, 0, 0.0)
cone_root = link(O.new("SPEAKER CONE", None)); cone_root.parent = spk
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=0.36, radius2=0.12, depth=0.10)
for v in bm.verts: v.co.z = -v.co.z                                   # 広い口が前
cone = mesh_obj("Speaker cone", bm, mat("Cone", srgb("#2C3036"), 0.55, 0.1), smooth=True); cone.parent = cone_root; cone.location = (0, 0, -0.06)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=12, radius=0.13)
for v in bm.verts: v.co.z = max(v.co.z, 0.0) * 0.45
cap = mesh_obj("Speaker cap", bm, m_titan, smooth=True); cap.parent = cone_root; cap.location = (0, 0, -0.11)
# 灯（鳴っている間は緑。止まると消える）
m_play = mat_emit("Play lamp", (0.30, 1.0, 0.42), 0.0)
pl = cyl("Play lamp", 0.05, 0.03, m_play, 24); pl.location = (0.70, SPK_Y - 0.01, 0.95); pl.rotation_euler = (math.pi / 2, 0, 0)
cyl("Play lamp ring", 0.07, 0.02, m_titan, 24).location = (0.70, SPK_Y - 0.002, 0.95); O["Play lamp ring"].rotation_euler = (math.pi / 2, 0, 0)
pll = bpy.data.lights.new("Play lamp light", "POINT"); pll.color = (0.30, 1.0, 0.42); pll.energy = 0.0; pll.shadow_soft_size = 0.05
link(O.new("Play lamp light", pll)).location = (0.70, SPK_Y - 0.08, 0.95)

# ================================================================ 貯蔵タワー：柱4本、ひと箱ごとの帯、内側のブレーキ（うず電流の銅の帯）、上の扉、目盛りの灯
TW, TD = 1.20, 0.80; Z_TOP = p7.Z_DOOR
for sx in (-1, 1):
    for sy in (-1, 1):
        box("Tower post", (0.06, 0.06, Z_TOP - Z_S + 0.10), m_petrol, 0.008).location = (sx * TW / 2, sy * TD / 2, (Z_S + Z_TOP + 0.10) / 2)
for k in range(p7.N_SLOT + 1):                                        # 帯：横と後ろ（前は空けて、中の荷物が見えるように）
    zz = Z_S + k * U if k < p7.N_SLOT else Z_TOP - 0.05
    for sx in (-1, 1): box("Tower band", (0.03, TD, 0.03), m_petrol).location = (sx * TW / 2, 0, zz)
    box("Tower band", (TW, 0.03, 0.03), m_petrol).location = (0, TD / 2, zz)
box("Tower band front top", (TW, 0.03, 0.05), m_petrol).location = (0, -TD / 2, Z_TOP - 0.05)
for sx in (-1, 1): box("Brake strip", (0.025, 0.14, Z_TOP - Z_S), m_copper, 0.004).location = (sx * 0.5475, 0, (Z_S + Z_TOP) / 2)   # 荷物の横から 1.5cm
# 上の扉（受け渡し台の続き）：左右に開いて、下へ落とす。蝶番は塔の左右の縁
doors = []
for sx in (-1, 1):
    hinge = link(O.new("DOOR HINGE", None)); hinge.location = (sx * 0.58, 0, Z_TOP)
    dr = box("Tower door", (0.58, 0.74, 0.03), m_steel, 0.006); dr.parent = hinge; dr.location = (-sx * 0.29, 0, -0.015)
    doors.append((sx, hinge))
# 塔の上のふた（漏斗の代わりの屋根）と、札「バッファ」
ROOF = 0.60
box("Tower roof", (TW + 0.10, TD + 0.10, 0.05), m_petrol, 0.01).location = (0, 0, Z_TOP + ROOF)
for sx in (-1, 1):
    for sy in (-1, 1): box("Roof post", (0.05, 0.05, ROOF), m_petrol).location = (sx * TW / 2, sy * TD / 2, Z_TOP + ROOF / 2)
JFONT = None
for fp in [A.font, os.path.join(HERE, "..", "av", "fonts", "japanese.ttc"),                                  # こちら
           os.path.join(os.path.dirname(bpy.data.filepath), "..", "assets", "japanese.ttc"),                  # PC：story.blend の隣の assets（同じフォント）
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "C:/Windows/Fonts/YuGothB.ttc", "C:/Windows/Fonts/meiryob.ttc"]:
    if fp and os.path.exists(fp):
        try: JFONT = bpy.data.fonts.load(fp); break
        except Exception as ex: print("JFONT fail", fp, ex)
print("JFONT", JFONT, flush=True)
SIGN_Z = Z_TOP + 0.30
m_sign = M.new("Buffer sign face"); m_sign.use_nodes = True; _nt = m_sign.node_tree; _bs = _nt.nodes["Principled BSDF"]   # 2026-11-09：大きく・はっきり（ユーザー）
_tx = _nt.nodes.new("ShaderNodeTexImage"); _tx.name = "Sign image"
_tx.image = bpy.data.images.load(os.path.join(HERE, "screens", "buffer_sign.png"), check_existing=True)   # 白い板に太く濃い「バッファ」（PIL で描いた絵。こちらも PC も同じ）
_mx = _nt.nodes.new("ShaderNodeMix"); _mx.data_type = "RGBA"; _mx.name = "Sign lit"; _mx.inputs[0].default_value = 0.12
_mx.inputs[6].default_value = (*srgb("#2E3337"), 1)
_nt.links.new(_tx.outputs["Color"], _mx.inputs[7]); _nt.links.new(_mx.outputs[2], _bs.inputs["Base Color"]); _nt.links.new(_tx.outputs["Color"], _bs.inputs["Emission Color"])
_bs.inputs["Emission Strength"].default_value = 0.0; _bs.inputs["Roughness"].default_value = 0.55
m_sign.diffuse_color = (*srgb("#E8ECEA"), 1)
plate = box("Buffer plate", (1.22, 0.04, 0.46), m_graphite, 0.02); plate.location = (0, -TD / 2 - 0.07, SIGN_Z)
box("Buffer plate frame", (1.28, 0.03, 0.52), m_petrol, 0.015).location = (0, -TD / 2 - 0.045, SIGN_Z)
_bm = bmesh.new(); bmesh.ops.create_grid(_bm, x_segments=1, y_segments=1, size=0.5)
for _v in _bm.verts: _v.co.x *= 1.20; _v.co.y *= 0.43
_uv = _bm.loops.layers.uv.new("UVMap")                               # 絵を貼る座標（板の左下 0,0 → 右上 1,1）
for _f in _bm.faces:
    for _l in _f.loops: _l[_uv].uv = (_l.vert.co.x / 1.20 + 0.5, _l.vert.co.y / 0.43 + 0.5)
sign = mesh_obj("Buffer sign", _bm, m_sign); sign.location = (0, -TD / 2 - 0.0915, SIGN_Z); sign.rotation_euler = (math.pi / 2, 0, 0)   # 板の前の面（−Y を向く）
sgl = bpy.data.lights.new("Buffer sign light", "AREA"); sgl.shape = "RECTANGLE"; sgl.size, sgl.size_y = 1.0, 0.25; sgl.color = (0.55, 1.0, 0.80); sgl.energy = 0.0
sglo = link(O.new("Buffer sign light", sgl)); sglo.location = (0, -TD / 2 - 0.16, SIGN_Z - 0.10); sglo.rotation_euler = (math.radians(-90), 0, 0)   # 前（−Y：部屋の側）を照らす。札の字は照らさない
# 目盛り：塔の左前の柱に、小さな灯を 32（ひと箱 8 つ）。積み重なりの高さまで点く
m_led = obj_emit_mat("Gauge LED", (0.25, 0.95, 0.85), 3.0)
GAUGE = []
N_LED = 8 * p7.N_SLOT
for k in range(N_LED):
    zc = Z_S + (k + 0.5) * (p7.N_SLOT * U / N_LED)
    ld_ = box("Gauge LED", (0.05, 0.012, 0.055), m_led, 0.004); ld_.location = (-TW / 2 - 0.05, -TD / 2 - 0.02, zc); ld_.color = (0, 0, 0, 1)
    GAUGE.append((zc, ld_))
box("Gauge rail", (0.08, 0.02, p7.N_SLOT * U + 0.06), m_graphite).location = (-TW / 2 - 0.05, -TD / 2 + 0.0, Z_S + p7.N_SLOT * U / 2)
for k in range(p7.N_SLOT + 1):
    box("Gauge tick", (0.12, 0.012, 0.012), m_white).location = (-TW / 2 - 0.05, -TD / 2 - 0.03, Z_S + k * U)

# ================================================================ 昇降機：受付ボックスから床の下の通路を通って上がってくる。上で押し出し板が、荷物を塔の上の扉へ押す
XL = p7.X_LIFT
for sx in (-1, 1):
    for sy in (-1, 1):
        box("Lift post", (0.06, 0.06, Z_TOP + 0.6), m_steel, 0.006).location = (XL + sx * 0.66, sy * 0.46, (Z_TOP + 0.6) / 2)
box("Lift top beam", (1.38, 0.06, 0.06), m_steel).location = (XL, -0.46, Z_TOP + 0.6); box("Lift top beam", (1.38, 0.06, 0.06), m_steel).location = (XL, 0.46, Z_TOP + 0.6)
# 床の穴（下の通路）と、そのふちの灯（琥珀：荷物が来るのを待っている）
box("Lift pit", (1.36, 0.96, 0.02), m_dark).location = (XL, 0, -1.2)
for sy in (-1, 1): box("Pit wall", (1.36, 0.02, 1.2), m_dark).location = (XL, sy * 0.48, -0.6)
for sx in (-1, 1): box("Pit wall", (0.02, 0.96, 1.2), m_dark).location = (XL + sx * 0.68, 0, -0.6)
m_pit = mat_emit("Pit edge", (1.0, 0.62, 0.20), 0.0)
for sy in (-1, 1): box("Pit edge", (1.40, 0.025, 0.012), m_pit).location = (XL, sy * 0.50, 0.006)
for sx in (-1, 1): box("Pit edge", (0.025, 1.0, 0.012), m_pit).location = (XL + sx * 0.70, 0, 0.006)
# 床（穴の所を空ける）：床は一枚なので、穴の上に床が見えないよう、穴の形の暗い面を少しだけ上に
box("Pit mouth", (1.36, 0.96, 0.004), m_dark).location = (XL, 0, 0.002)
plat = link(O.new("LIFT PLATFORM", None))
box("Lift deck", (1.22, 0.82, 0.05), m_steel, 0.006).parent = plat; O["Lift deck"].location = (0, 0, -0.025)
for k in range(9):
    r_ = cyl("Lift roller", 0.022, 0.78, m_roller, 12); r_.parent = plat; r_.location = (-0.54 + k * 0.135, 0, 0.0); r_.rotation_euler = (math.pi / 2, 0, 0)
# 受け渡し台（昇降機の上 → 塔の上の扉）：ローラー
for k in range(4):
    r_ = cyl("Bridge roller", 0.022, 0.78, m_roller, 12); r_.location = (0.66 + k * 0.135, 0, Z_TOP - 0.022); r_.rotation_euler = (math.pi / 2, 0, 0)
box("Bridge frame", (0.56, 0.84, 0.03), m_steel).location = (0.87, 0, Z_TOP - 0.06)
# 押し出し板（昇降機の右の上）
pusher = box("Lift pusher", (0.04, 0.70, 0.40), m_titan, 0.006); pusher_rod = box("Lift pusher rod", (0.9, 0.05, 0.05), m_titan)

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


# ================================================================ 荷物（箱・両面の札・上の札・トレー）
FONT_ = FONT
def parcel(num, name):
    root = link(O.new(name, None))
    body = link(O.new(name + " BODY", None)); body.parent = root; body.location = (0, 0, mm.CARGO_HALF[1] - 0.34)
    cs = link(O.new(name + " case", CASE_ME)); cs.parent = body
    for fc in (-1, 1): label(body, num, fc)
    tr = link(O.new(name + " tray", TRAY_ME)); tr.parent = root; tr.location = (0, 0, -mm.CARGO_HALF[1] + mm.TRAY_H / 2); tr.scale = (1, 1, mm.TRAY_H / 0.08)
    label_top(body, num)
    return root
PO = [parcel(p[0], "PARCEL %s%s" % (p[0], p[1])) for p in p7.PARCELS]
ZC_OFF = mm.CARGO_HALF[1]                                             # 荷物の中心 ＝ 底 ＋ 0.37

# ================================================================ 毎コマ：荷物・昇降機・押し出し板・扉・目盛り・灯・スピーカー・札
# スピーカーの振動板：曲（第6章からずっと同じ 3.08 秒のくり返し）の低い音の大きさに合わせて前後に（最大 1.2cm）
try:
    w = wave.open(A.song); sr0 = w.getframerate(); w.setpos(int(round(40.04 * sr0))); x = np.frombuffer(w.readframes(int(round(3.08 * sr0))), np.int16).astype(float) / 32768
    a_ = math.exp(-2 * math.pi * 120.0 / sr0); y = np.zeros_like(x); s_ = 0.0
    for i_, v_ in enumerate(np.concatenate([x, x])): s_ = a_ * s_ + (1 - a_) * v_; (y.__setitem__(i_ - len(x), s_) if i_ >= len(x) else None)
    hop = sr0 // 120; envb = np.array([np.abs(y[k * hop:(k + 1) * hop]).max() for k in range(len(y) // hop)]); envb = envb / max(envb.max(), 1e-9)
except Exception as ex:
    print("SONG env skipped", ex); envb = np.ones(370)
BEAT0_ABS = p6.T0 + 57.63                                             # 第6章で曲の拍の頭をそろえた時刻（本編 712.29）
def bass(t_abs):
    ph = ((t_abs - BEAT0_ABS) % 3.08) / 3.08; return float(envb[min(int(ph * len(envb)), len(envb) - 1)])
_t139 = p7.PLC[139]["text"]; SIGN_ON = p7.L(139) + (p7.LE(139) - p7.L(139)) * _t139.index("バッファ") / len(_t139) - 0.15   # 「…が、バッファです」の言葉で光る
CAM_LOG = []; PARCEL_W = []
for i in range(N):
    t = i / FPS; f = i + 1; ta = T_ORIG + t; play = p7.playing(ta); pst = p7.player_state(ta)
    pw = []
    for p, ob in zip(p7.PARCELS, PO):
        vis, x_, zb, st = p7.parcel_state(p, ta)
        for k_, val in enumerate((x_, 0.0, zb + ZC_OFF)): bk.put(ob, "location", k_, f, val)
        for o in hier(ob):
            if o.type in ("MESH", "FONT"): bk.put(o, "hide_render", 0, f, 0.0 if vis else 1.0); bk.put(o, "hide_viewport", 0, f, 0.0 if vis else 1.0)
        pw.append([round(x_, 3), round(zb + ZC_OFF, 3)] if vis else None)
    PARCEL_W.append(pw)
    # 昇降機と押し出し板・扉（届く荷物ごと）
    zl = p7.Z_LIFT_LOW; xp = XL + 0.55; dr = 0.0
    for key, a in p7.ARR.items():
        if p7.scene_of(ta) != key[-1]: continue
        if a["t_rise0"] - 0.5 <= ta < a["t_lower1"] + 0.5:
            if ta < a["t_lower0"]: zl = p7.Z_LIFT_LOW + (Z_TOP - p7.Z_LIFT_LOW) * p7.mj(ta, a["t_rise0"], a["t_rise1"] - a["t_rise0"])
            else: zl = Z_TOP - (Z_TOP - p7.Z_LIFT_LOW) * p7.mj(ta, a["t_lower0"], a["t_lower1"] - a["t_lower0"])
            push = p7.mj(ta, a["t_push0"], a["t_push1"] - a["t_push0"]) - p7.mj(ta, a["t_push1"] + 0.25, 1.0)
            xp = XL + 0.55 - XL * push
        dr = max(dr, p7.mj(ta, a["t_open"] - 0.02, 0.16) - p7.mj(ta, a["t_close"], 0.35))
    for k_, val in enumerate((XL, 0.0, zl)): bk.put(plat, "location", k_, f, val)
    for k_, val in enumerate((xp, 0.0, Z_TOP + 0.21)): bk.put(pusher, "location", k_, f, val)
    for k_, val in enumerate((xp + 0.47, 0.0, Z_TOP + 0.36)): bk.put(pusher_rod, "location", k_, f, val)
    for sx, hinge in doors: bk.put(hinge, "rotation_euler", 1, f, sx * math.radians(88.0) * dr)       # 下へ開く
    # 目盛り（積み重なりの高さまで点く）
    lev = p7.stack_top(ta)
    for zc, ld_ in GAUGE:
        on = min(max((Z_S + lev - (zc - 0.03)) / 0.06, 0.0), 1.0)
        bk.put(ld_, "color", 0, f, on)
    # 再生装置：灯・読み取りの光・スピーカー
    pe = 1.0 if play else 0.0; lc = (0.30, 1.0, 0.42) if pst != "wait" else (1.0, 0.62, 0.20)       # 緑（鳴っている）／琥珀（ためて待っている）
    for c_ in range(3): bk.put(m_play.node_tree, 'nodes["Emission"].inputs[0].default_value', c_, f, lc[c_]); bk.put(pll, "color", c_, f, lc[c_])
    le = 1.8 if pst == "play" else (1.8 if pst == "wait" else 0.0)
    bk.put(m_play.node_tree, 'nodes["Emission"].inputs[1].default_value', 0, f, le); bk.put(pll, "energy", 0, f, 0.5 * le)
    bk.put(m_read.node_tree, 'nodes["Emission"].inputs[1].default_value', 0, f, 5.0 * pe); bk.put(rl, "energy", 0, f, 25.0 * pe)
    bk.put(cone_root, "location", 2, f, 0.012 * bass(ta) * pe)
    # 床の穴のふち（琥珀）：後半は、届かない荷物を待って点滅（1秒に1回）
    pit = 0.0
    if p7.scene_of(ta) == "B": pit = 0.5 + 0.5 * math.cos(2 * math.pi * (ta - p7.T_B))
    bk.put(m_pit.node_tree, 'nodes["Emission"].inputs[1].default_value', 0, f, 2.5 * pit)
    # 札「バッファ」
    sg = p7.mj(ta, SIGN_ON, 0.5)
    bk.put(m_sign.node_tree, 'nodes["Principled BSDF"].inputs["Emission Strength"].default_value', 0, f, 2.4 * sg); bk.put(sgl, "energy", 0, f, 10.0 * sg)
    bk.put(m_sign.node_tree, 'nodes["Sign lit"].inputs[0].default_value', 0, f, 0.12 + 0.88 * sg)

# ================================================================ まるロボ（2026-11-09）：06 の到着とともに入ってきて、見守りながら一喜一憂（ch07_robot.py）
ROBOT_LOG = []
if ROBOT_KEEP:
    import ch07_robot as rb
    maru = O["Maru"]
    show = link(O.new("ROBOT SHOW", None)); maru.parent = show; maru.matrix_parent_inverse = Matrix.Identity(4)
    pl_r = rb.plan_ch7(T_ORIG) if A.part == "ch7" else rb.plan_ch8(T_ORIG)
    fr_r = mm.simulate(pl_r, fps=FPS, t_end=TA(T_LAST) + 1.0)
    rig_r = mr.MaruRig(maru)
    for i in range(N):
        fr_ = fr_r[min(i, len(fr_r) - 1)]; rig_r.apply(fr_, i + 1, bk); ROBOT_LOG.append([round(float(v), 3) for v in fr_["root"]])
    if A.part == "ch7":
        for f_, v_ in ((1, 0.0), (int(round(TA(rb.T_SHOW) * FPS)) + 1, 1.0)):
            for k_ in range(3): show.scale[k_] = v_
            show.keyframe_insert("scale", frame=f_)
        for fc in show.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
    print("ROBOT plan", round(pl_r.t, 2), "events", len(pl_r.events), flush=True)

# ================================================================ カメラ（場面ごと。カットは1コマで切り替える。場面の名前と始まりは ch07_plan.SHOTS）
cam_d = bpy.data.cameras.new("Ch07 camera"); cam = link(O.new("Ch07 camera", cam_d)); scene.camera = cam
cam_d.sensor_width = 36; cam_d.clip_start = 0.05; cam_d.clip_end = 200; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
V = lambda *a: np.array(a, float)
def lerp(a, b, u): return a + (b - a) * u
SHOT_T = [(TA(t_), nm.split()[0]) for t_, nm in SHOTS_P]
def shot_span(t):
    for j, (t0_, nm) in enumerate(SHOT_T):
        t1_ = SHOT_T[j + 1][0] if j + 1 < len(SHOT_T) else TA(T_LAST) + 1.0
        if t < t1_ - 1e-6: return nm, t0_, t1_
    return SHOT_T[-1][1], SHOT_T[-1][0], TA(T_LAST) + 1.0
SEAT = V(0, 0, Z_S)
def shot(t):
    """→ (位置, 見る点, レンズ mm, ピントの点, 名前)"""
    nm, t0_, t1_ = shot_span(t); u = mm.smooth((t - t0_) / max(t1_ - t0_, 1e-6)); ta = T_ORIG + t
    if nm == "C1": return lerp(V(-2.2, -6.0, 2.0), V(-1.9, -5.5, 1.95), u), V(0.45, -0.3, 2.0), 22.0, V(0.6, -0.9, 1.4), nm   # 第8章：空になった塔（まるロボが見上げる）
    if nm == "C2": return lerp(V(3.0, -5.4, 3.5), V(2.8, -5.1, 3.4), u), V(0.6, 0, 3.2), 26.0, V(0.3, 0, 3.0), nm     # 04 が届く（上の扉）
    if nm == "C3": return lerp(V(-1.6, -6.6, 2.0), V(-1.3, -6.0, 1.95), u), V(0.3, -0.3, 2.05), 22.0, V(0.4, -0.8, 1.6), nm   # いっぱいになってから鳴らす（まるロボが揺れる）
    if nm == "K1": return lerp(V(-3.3, -6.6, 2.6), V(-2.9, -6.0, 2.5), u), V(0.65, 0, 2.15), 26.0, V(0, 0, 1.8), nm
    if nm == "K2": return lerp(V(-0.95, -2.75, 1.30), V(-0.80, -2.45, 1.26), u), V(0.05, -0.25, 1.02), 32.0, V(0, -0.5, 1.0), nm
    if nm == "K3":
        tz = lerp(1.25, 2.15, mm.smooth((t - t0_) / 2.2))
        return V(-0.9, -2.9, 1.45), V(0.05, 0, tz), 30.0, V(0, 0, tz), nm
    if nm == "K4": return lerp(V(1.9, -5.2, 2.3), V(-1.5, -5.3, 2.3), u), V(0.25, 0, 1.95), 30.0, V(0, 0, 1.9), nm
    if nm == "K5": return lerp(V(0.95, -2.95, 1.62), V(0.75, -2.7, 1.58), u), V(0.0, 0, 1.45), 28.0, V(0, 0, 1.45), nm
    if nm == "K6":                                   # 06 が上がって塔へ → 落ちたあと、カメラが下りて、入ってきたまるロボを見せる
        w = mm.smooth((ta - 783.6) / 2.6); p0 = lerp(V(4.2, -6.1, 3.1), V(3.8, -5.6, 3.0), u)
        return lerp(p0, V(3.5, -6.2, 1.85), w), lerp(V(0.95, 0, 2.75), V(0.75, -0.55, 1.55), w), lerp(26.0, 24.0, w), lerp(V(0.9, 0, 2.8), V(1.05, -1.48, 1.0), w), nm
    if nm == "K7":                                   # 塔 → まるロボが下がってきて、光る札を見上げる（札は上、まるロボは下）
        w = mm.smooth((ta - 795.5) / 3.0); p0 = lerp(V(-0.55, -6.0, 2.9), V(-0.7, -6.6, 2.85), u)
        return lerp(p0, V(1.9, -6.6, 1.7), w), lerp(V(0.0, 0, 2.95), V(0.35, -0.6, 2.6), w), lerp(28.0, 21.0, w), lerp(V(0, -0.4, 2.8), V(0.3, -1.5, 3.2), w), nm
    if nm == "K7s":                                  # まるロボが見上げた先：札「バッファ」を正面やや下から大きく（画面の幅の半分ほど）。光る瞬間を見せる
        return lerp(V(0.30, -3.05, 3.85), V(0.22, -2.85, 3.90), u), V(0.0, -0.475, 4.62), 40.0, V(0.0, -0.52, 4.66), nm
    if nm == "K8": return lerp(V(3.0, -6.2, 2.05), V(2.7, -5.8, 2.0), u), V(0.95, -0.2, 2.15), 22.0, V(1.2, -0.8, 2.0), nm
    if nm == "K9": return lerp(V(-2.3, -4.8, 1.7), V(-2.0, -4.5, 1.65), u), V(0.45, -0.5, 1.3), 26.0, V(0.6, -0.9, 1.1), nm
    if nm == "K9b": return lerp(V(-4.4, -8.4, 3.3), V(-3.8, -7.5, 3.1), u), V(0.65, 0, 2.2), 24.0, V(0.3, 0, 2.0), nm
    if nm == "K10": return lerp(V(3.4, -6.5, 2.7), V(3.0, -6.0, 2.6), u), V(0.85, 0, 2.1), 24.0, V(0.6, 0, 1.8), nm
    if nm == "K11": return lerp(V(-0.9, -4.6, 1.75), V(-0.7, -4.2, 1.70), u), V(0.6, -0.6, 1.05), 24.0, V(0.8, -1.2, 1.0), nm
    return lerp(V(-1.35, -4.0, 1.62), V(-1.2, -3.7, 1.56), u), V(0.4, -0.6, 1.0), 26.0, V(0.5, -0.9, 1.0), nm      # K12：再生装置の口と、見つめるまるロボ（全身）
cam.rotation_mode = "QUATERNION"; shots = []
for i in range(N):
    t = i / FPS; p, tg, lens, fp, nm = shot(t)
    q = (Vector(tg) - Vector(p)).to_track_quat("-Z", "Y")
    for k in range(3): bk.put(cam, "location", k, i + 1, p[k])
    for k in range(4): bk.put(cam, "rotation_quaternion", k, i + 1, q[k])
    bk.put(cam_d, "lens", 0, i + 1, lens); bk.put(cam_d, "dof.focus_distance", 0, i + 1, float(np.linalg.norm(np.array(fp) - p)))
    if not shots or shots[-1][1] != nm: shots.append([round(t, 3), nm])
    CAM_LOG.append([round(float(x), 4) for x in (*p, *q, lens)])
bk.write()

# ================================================================ 描画の設定と記録
for _ld in [l_ for l_ in bpy.data.lights if l_.name.startswith(("Reader light", "Play lamp light", "Buffer sign light"))]: _ld.use_shadow = False   # 小さな灯の光は影なし（描く時間を減らす）
scene.render.resolution_x, scene.render.resolution_y = A.res; scene.render.resolution_percentage = 100
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
if A.engine == "workbench":
    scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
    sh.light = "STUDIO"; sh.color_type = A.wb_color; sh.show_shadows = True; sh.shadow_intensity = 0.5; sh.show_cavity = True; sh.cavity_type = "WORLD"
    sh.background_type = "WORLD"; scene.world.color = srgb("#3A3F45")
else:
    scene.render.engine = "BLENDER_EEVEE_NEXT"; ee = scene.eevee; ee.taa_render_samples = A.samples; ee.use_shadows = True
    try: ee.use_raytracing = False
    except Exception: pass
scene.view_settings.view_transform = "AgX" if A.engine != "workbench" else "Standard"; scene.view_settings.look = "AgX - Base Contrast" if A.engine != "workbench" else "None"
scene.view_settings.exposure = A.exposure; scene.render.image_settings.file_format = "PNG"
POINTS = dict(seat=[0, 0, Z_S], sign=[0, -TD / 2 - 0.075, SIGN_Z], gauge_bottom=[-TW / 2 - 0.05, -TD / 2 - 0.02, Z_S], gauge_top=[-TW / 2 - 0.05, -TD / 2 - 0.02, Z_S + p7.N_SLOT * U],
              lift_top=[XL, 0, Z_TOP], pit=[XL, 0, 0.0], speaker=[0, SPK_Y, SPK_Z], lamp=[0.70, SPK_Y, 0.95], door=[0, 0, Z_TOP])
log = dict(fps=FPS, frames=N, t0=T_ORIG, part=A.part, robot=ROBOT_LOG, shots=shots, cuts=[s_[0] for s_ in shots[1:]], sensor=36.0, cam=CAM_LOG, points=POINTS, parcels=[p[0] + p[1] for p in p7.PARCELS], parcel_w=PARCEL_W,
           arrivals={k: v for k, v in p7.ARR.items()}, times=dict(seam_a=p7.SEAM_A, t_b=p7.T_B, stop=p7.T_STOP, sign=SIGN_ON, t_p=p7.T_P, t_c=p7.T_C, start_c=p7.T_START_C))
json.dump(log, open(os.path.join(A.out, LOGNAME), "w", encoding="utf-8"), ensure_ascii=False, default=float)
print("CH07 frames", N, "shots", shots, flush=True)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "ch07_stage.blend"))
if A.still:
    for tt in A.still.split(","):
        tp_ = float(tt) - T_ORIG if A.abs else float(tt)
        f = int(round(tp_ * FPS)) + 1; scene.frame_set(f)
        scene.render.filepath = os.path.join(A.out, "still_%s.png" % tt); bpy.ops.render.render(write_still=True); print("STILL", tt, "frame", f, flush=True)
elif A.frames:
    f0, f1 = [int(x) for x in A.frames.split(":")]
    scene.frame_start, scene.frame_end = f0, min(f1, N); scene.render.use_overwrite = False; scene.render.use_placeholder = True
    scene.render.filepath = os.path.join(A.out, "frames", "f_")
    if A.video:                                                       # PC の本番用：範囲ごとに mp4（H.264・ほぼ劣化なし）で書き出す（あとでこちらで字幕・声・図と合わせる）
        scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
        ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "PERC_LOSSLESS"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
        scene.render.use_overwrite = True; scene.render.use_placeholder = False
        scene.render.filepath = os.path.join(A.out, A.vprefix or ("ch07_stage_" if A.part == "ch7" else "ch08_tower_"))
    bpy.ops.render.render(animation=True); print("SEQ DONE", flush=True)
