# 5本目（ロボット掃除機）：3D の部品（scenes.py が exec で読む。前提：KIT_HERE を決めてから読む）
#   まるロボ・材質・光・カメラは 3本目（ep03_ad/storyboard/scenes.py）の部品をそのまま使う
#   部屋・家具・先輩（光の物差しの先輩・カメラの先輩・昔の先輩）・スマホ・点の地図・通った道の線
#   間取りは plan.py（スマホの地図・光の点と同じ形）
#   決まり：3D の中に字を書かない。まるロボも先輩も喋らない。光の点＝青緑で最後まで同じ表し方
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector
R = math.radians
_sv = sys.argv
sys.argv = [sys.argv[0], "--", "x", "x.png", "8"]
exec(open(os.path.join(KIT_HERE, "..", "..", "ep03_ad", "storyboard", "scenes.py"), encoding="utf-8").read().split("# ---------------- 場面\n")[0])
sys.argv = _sv
sys.path.insert(0, KIT_HERE)
import plan
FPS = 24
TEAL = "#2FD9C8"          # 光の点・光の物差しの光（最後まで同じ色）
WHITE_PT = "#F4F7FF"      # 4 章：いま見えている形（白っぽい点。地図の点と分ける）
RUGOBJ = []
LIGHTS = []               # 部屋の明かり（電気を消す場面で、まとめて消す）：(光, 元の強さ)
GLOWS = []                # 光る材質（照明のかさ・窓の空）：(材質, 元の強さ)


def noise_mat(name, c1, c2, scale=6.0, rough=0.5, wave=False, bump=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexWave" if wave else "ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = scale
    if wave: tx.inputs["Distortion"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = srgb(c1); ramp.color_ramp.elements[1].color = srgb(c2)
    nt.links.new(tx.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if bump:
        bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump
        nt.links.new(tx.outputs["Fac"], bn.inputs["Height"]); nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


def glow_mat(name, col, strength):
    m = mat(name, col, rough=0.4, emit=strength)
    GLOWS.append((m, strength))
    return m


def focus_on(loc, fstop=2.8):
    cam = bpy.context.scene.camera
    t = empty(loc); cam.data.dof.use_dof = True; cam.data.dof.focus_object = t; cam.data.dof.aperture_fstop = fstop
    return t


def arc_band(m, r_out, r_in, z0, z1, a0, a1, parent=None, seg=40):
    """円の一部の帯（前のバンパー）。角度は度、0 度＝-y（前）"""
    me = bpy.data.meshes.new("band"); bm = bmesh.new(); vs = []
    for i in range(seg + 1):
        a = R(a0 + (a1 - a0) * i / seg)
        ring = []
        for r in (r_out, r_in):
            for z in (z0, z1):
                ring.append(bm.verts.new((r * math.sin(a), -r * math.cos(a), z)))
        vs.append(ring)
    for i in range(seg):
        A, B = vs[i], vs[i + 1]
        for (p, q) in ((0, 1), (1, 3), (3, 2), (2, 0)):
            bm.faces.new((A[p], A[q], B[q], B[p]))
    bm.faces.new((vs[0][0], vs[0][1], vs[0][3], vs[0][2])); bm.faces.new((vs[-1][2], vs[-1][3], vs[-1][1], vs[-1][0]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("band", me); bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o


# ---------------- 部屋
def room(front_wall=False, ceiling=False, window=True, top_view=False, rug=False, hall_walls=(True, True)):
    """昼の部屋。front_wall＝手前の壁も建てる（上からの絵）。ceiling＝天井と丸い照明（カメラの先輩が見上げる絵）"""
    world("#F2ECE2", 0.22)
    x0, y0, x1, y1 = plan.ROOM
    floor = noise_mat("floorwood", "#A88464", "#977353", 2.2, 0.38, wave=True, bump=0.05)
    plane(floor, ((x0 + x1) / 2, (y0 + y1) / 2, 0), (x1 - x0, y1 - y0))
    # 廊下と、下へ降りる段差（玄関の土間）
    plane(floor, ((x0 + plan.STEP_X) / 2, sum(plan.DOOR) / 2, 0), (x0 - plan.STEP_X, plan.DOOR[1] - plan.DOOR[0]))
    tile = noise_mat("tile", "#8C8F94", "#7D8085", 18, 0.6)
    cube(tile, ((plan.STEP_X + plan.HALL_X) / 2, sum(plan.DOOR) / 2, -plan.STEP_H - 0.01), (plan.STEP_X - plan.HALL_X, plan.DOOR[1] - plan.DOOR[0] + 0.4, 0.02))
    cube(mat("stepedge", "#9C7048", rough=0.5), (plan.STEP_X + 0.02, sum(plan.DOOR) / 2, -plan.STEP_H / 2), (0.04, plan.DOOR[1] - plan.DOOR[0], plan.STEP_H))
    # 壁
    wall = noise_mat("wallpaper", "#EEE8DE", "#E9E2D6", 60, 0.9)
    base = mat("baseboard", "#FFFFFF", rough=0.5)
    H = plan.CEIL; T = 0.1
    cube(wall, ((x0 + x1) / 2, y1 + T / 2, H / 2), (x1 - x0 + 2 * T, T, H))
    cube(base, ((x0 + x1) / 2, y1 - 0.01, 0.05), (x1 - x0, 0.02, 0.1))
    cube(wall, (x1 + T / 2, (y0 + y1) / 2, H / 2), (T, y1 - y0, H))
    cube(base, (x1 - 0.01, (y0 + y1) / 2, 0.05), (0.02, y1 - y0, 0.1))
    d0, d1 = plan.DOOR
    cube(wall, (x0 - T / 2, (d1 + y1) / 2, H / 2), (T, y1 - d1, H))
    cube(wall, (x0 - T / 2, (y0 + d0) / 2, H / 2), (T, d0 - y0, H))
    cube(wall, (x0 - T / 2, (d0 + d1) / 2, (2.05 + H) / 2), (T, d1 - d0, H - 2.05))
    cube(mat("doorframe", "#C9A57A", rough=0.5), (x0, (d0 + d1) / 2, 2.05), (0.14, d1 - d0 + 0.1, 0.06))
    # 廊下の壁（短く）
    for yy, on in zip((d0 - T / 2, d1 + T / 2), hall_walls):
        if on: cube(wall, ((x0 + plan.HALL_X) / 2, yy, H / 2), (x0 - plan.HALL_X, T, H))
    cube(wall, (plan.HALL_X - T / 2, (d0 + d1) / 2, H / 2), (T, d1 - d0 + 2 * T, H + 0.4))      # 廊下のつきあたり
    if front_wall:
        cube(wall, ((x0 + x1) / 2, y0 - T / 2, 0.35 if top_view else H / 2), (x1 - x0 + 2 * T, T, 0.7 if top_view else H))
    if top_view:
        pass
    # 右の壁の窓（昼の空）と、カーテン
    if window:
        cube(mat("winf", "#FFFFFF", rough=0.4), (x1 - 0.02, -0.2, 1.45), (0.06, 1.7, 1.3), bevel=0.02)
        cube(glow_mat("sky", "#CFE6F7", 1.6), (x1 - 0.04, -0.2, 1.45), (0.02, 1.56, 1.16))
        cube(mat("winbar", "#FFFFFF", rough=0.4), (x1 - 0.06, -0.2, 1.45), (0.02, 0.03, 1.16))
        for sy in (-1, 1):
            for k in range(5):
                cyl(mat("curtain", "#D8C3A0", rough=0.9), (x1 - 0.12, -0.2 + sy * (0.9 + k * 0.05), 1.3), 0.04, 2.0)
    # 壁の絵（字なし）
    cube(mat("frame", "#5B4636", rough=0.5), (-1.9, y1 - 0.02, 1.55), (0.7, 0.03, 0.5))
    cube(mat("art", "#7FB3A8", rough=0.7), (-1.9, y1 - 0.04, 1.55), (0.6, 0.02, 0.4))
    sphere(mat("artsun", "#F2C14E", rough=0.7), (-1.75, y1 - 0.05, 1.6), 0.07, scale=(1, 0.2, 1))
    # 天井と丸い照明
    if ceiling:
        cube(mat("ceil", "#F7F3EC", rough=0.9), ((x0 + x1) / 2, (y0 + y1) / 2, H + 0.02), (x1 - x0 + 0.2, y1 - y0 + 0.2, 0.04))
        cyl(glow_mat("ceillamp", "#FFF3DA", 6.0), (0.0, 0.2, H - 0.03), 0.28, 0.05)
        bpy.ops.object.light_add(type='POINT', location=(0.0, 0.2, H - 0.25)); pl = bpy.context.object; pl.data.energy = 260; pl.data.shadow_soft_size = 0.3; pl.data.color = srgb("#FFF1DC")[:3]; LIGHTS.append((pl, 260))
        for (cx, cy) in ((x0 + 0.02, y1 - 0.02), (x1 - 0.02, y1 - 0.02), (x0 + 0.02, y0 + 0.02), (x1 - 0.02, y0 + 0.02)):
            cube(mat("crown", "#FFFFFF", rough=0.5), (cx, cy, H - 0.04), (0.06, 0.06, 0.08))
        cyl(mat("ceilrim", "#E8E2D6", rough=0.4), (0.0, 0.2, H - 0.01), 0.31, 0.02)
    furniture(rug)
    # 明かり：窓からの光・部屋の上の大きな光
    sun_o = None
    bpy.ops.object.light_add(type='SUN', rotation=(R(55), 0, R(-70))); s_ = bpy.context.object; s_.data.energy = 2.2; s_.data.color = srgb("#FFF1DC")[:3]; s_.data.angle = R(6)
    LIGHTS.append((s_, 2.2))
    a = area((0.0, 0.0, 3.6), (0.0, 0.0, 0.0), energy=300, size=5.0, col="#FFF6EA", shape='SQUARE'); LIGHTS.append((a, 300))
    a2 = area((-1.5, -4.5, 2.2), (0.0, 0.5, 0.3), energy=140, size=3.0, col="#FFE9D2"); LIGHTS.append((a2, 140))


def furniture(rug=False):
    F = plan.FURN
    # ソファ（足の下に光が通る）
    x0, y0, x1, y1 = F["sofa"][:4]
    sofa = noise_mat("sofa", "#5E8C8A", "#679795", 30, 0.85)
    cube(sofa, ((x0 + x1) / 2, (y0 + y1) / 2, 0.27), (x1 - x0, y1 - y0, 0.22), bevel=0.05)
    cube(sofa, ((x0 + x1) / 2, y1 - 0.12, 0.6), (x1 - x0, 0.22, 0.5), bevel=0.06)
    for sx in (x0 + 0.1, x1 - 0.1):
        cube(sofa, (sx, (y0 + y1) / 2, 0.47), (0.2, y1 - y0, 0.24), bevel=0.06)
    for k in range(2):
        cube(noise_mat("cush%d" % k, "#6E9E9B", "#78A8A5", 30, 0.9), (x0 + 0.55 + k * 0.8, (y0 + y1) / 2 - 0.05, 0.43), (0.72, (y1 - y0) - 0.3, 0.12), bevel=0.05)
    cube(mat("pillow", "#F2C14E", rough=0.9), (x0 + 0.35, y1 - 0.3, 0.6), (0.36, 0.12, 0.3), bevel=0.05)
    for (lx, ly) in plan.legs("sofa"):
        cyl(mat("woodleg", "#6E5236", rough=0.5), (lx, ly, 0.08), plan.LEG / 2, 0.16)
    # 机（足の下に光が通る）とスマホの台
    x0, y0, x1, y1 = F["desk"][:4]
    cube(noise_mat("deskwood", "#C79A6B", "#B98C5E", 2.5, 0.45, wave=True), ((x0 + x1) / 2, (y0 + y1) / 2, 0.73), (x1 - x0, y1 - y0, 0.05), bevel=0.012)
    for (lx, ly) in plan.legs("desk"):
        cube(mat("deskleg", "#3E3A36", rough=0.5, metal=0.4), (lx, ly, 0.36), (plan.LEG, plan.LEG, 0.72))
    cyl(mat("mug", "#F4F1EA", rough=0.3, coat=0.5), (2.55, 2.2, 0.81), 0.05, 0.11)
    cyl(mat("pot", "#D9774B", rough=0.6), (1.35, 2.25, 0.82), 0.07, 0.13)
    for k in range(9):
        a = k * 0.7; sphere(mat("leaf", "#5E9E57", rough=0.5), (1.35 + 0.08 * math.cos(a), 2.25 + 0.05 * math.sin(a), 0.96 + 0.04 * (k % 3)), 0.06, scale=(1.4, 0.6, 0.5))
    cube(mat("book_d", "#4F81BD", rough=0.6), (2.25, 2.25, 0.77), (0.3, 0.22, 0.03), bevel=0.005)
    # ベッド
    x0, y0, x1, y1 = F["bed"][:4]
    cube(mat("bedbase", "#9C7552", rough=0.55), ((x0 + x1) / 2, (y0 + y1) / 2, 0.15), (x1 - x0, y1 - y0, 0.3), bevel=0.02)
    cube(mat("mattress", "#F5F2EC", rough=0.9), ((x0 + x1) / 2, (y0 + y1) / 2, 0.38), (x1 - x0 - 0.06, y1 - y0 - 0.06, 0.16), bevel=0.05)
    cube(noise_mat("duvet", "#8FB3D9", "#9DBFE2", 12, 0.95), ((x0 + x1) / 2, (y0 + y1) / 2 + 0.25, 0.48), (x1 - x0 - 0.02, y1 - y0 - 0.55, 0.08), bevel=0.04)
    cube(mat("pillow2", "#FFFFFF", rough=0.9), ((x0 + x1) / 2, y0 + 0.28, 0.5), (0.9, 0.35, 0.12), bevel=0.05)
    cube(mat("headb", "#7A5A40", rough=0.5), ((x0 + x1) / 2, y0 + 0.02, 0.55), (x1 - x0, 0.06, 1.1), bevel=0.02)
    # 本棚（左の壁）
    x0, y0, x1, y1 = F["shelf"][:4]
    sh = mat("shelfwood", "#B98C5E", rough=0.5)
    cube(sh, ((x0 + x1) / 2, (y0 + y1) / 2, 0.45), (x1 - x0, y1 - y0, 0.9), bevel=0.01)
    random.seed(5)
    for lev in (0.12, 0.42, 0.72):
        y = y0 + 0.06
        while y < y1 - 0.1:
            w = random.uniform(0.04, 0.08); h = random.uniform(0.18, 0.26)
            col = random.choice(["#C0504D", "#4F81BD", "#9BBB59", "#F2C14E", "#8064A2", "#E8E2D6"])
            cube(mat("bk" + col, col, rough=0.6), (x1 + 0.01, y + w / 2, lev + h / 2), (0.04, w, h)); y += w + 0.01
    cyl(mat("pot2", "#E8E2D6", rough=0.6), (x0 + 0.16, y1 - 0.2, 0.98), 0.08, 0.16)
    for k in range(10):
        a = k * 0.63; sphere(mat("leaf", "#5E9E57", rough=0.5), (x0 + 0.16 + 0.1 * math.cos(a), y1 - 0.2 + 0.1 * math.sin(a), 1.12 + 0.05 * (k % 3)), 0.07, scale=(1.3, 0.7, 0.6))
    # じゅうたん（16 章で「置いてみました」。それより前の場面にはない）
    if rug:
        x0, y0, x1, y1 = plan.RUG
        RUGOBJ.append(empty(((x0 + x1) / 2, (y0 + y1) / 2, 0.0)))
        cube(noise_mat("rug", "#C98F6B", "#D49C78", 80, 0.98, bump=0.4), (0, 0, 0.012), (x1 - x0, y1 - y0, 0.024), bevel=0.008, parent=RUGOBJ[-1])
        cube(mat("rugedge", "#E9D8C4", rough=0.95), (0, 0, 0.008), (x1 - x0 + 0.06, y1 - y0 + 0.06, 0.016), parent=RUGOBJ[-1])
    # 充電の台
    x0, y0, x1, y1 = F["dock"][:4]
    cx = (x0 + x1) / 2
    cube(mat("dock", "#E9ECEF", rough=0.3, coat=0.4), (cx, y1 - 0.05, 0.07), (x1 - x0, 0.08, 0.14), bevel=0.02)
    cube(mat("dockbase", "#D5D9DD", rough=0.4), (cx, (y0 + y1) / 2 - 0.05, 0.006), (x1 - x0, y1 - y0 + 0.12, 0.012), bevel=0.004)
    sphere(glow_mat("dockled", "#7CE8B0", 3.0), (cx, y1 - 0.095, 0.11), 0.008)


def door_leaf(open_=False):
    """出入り口の引き戸（2〜8 章は閉めておく。まるロボが廊下へ出ないように）"""
    x0 = plan.ROOM[0]; d0, d1 = plan.DOOR
    y = (d0 + d1) / 2 if not open_ else d1 + 0.45
    cube(mat("door", "#E8DCC8", rough=0.5), (x0 - 0.02, y, 1.02), (0.04, d1 - d0 - 0.02, 2.02), bevel=0.01)
    cube(mat("doorknob", "#B9A27A", rough=0.3, metal=0.7), (x0 + 0.01, y - 0.35, 1.0), (0.02, 0.03, 0.12))


def lights_off(t0, t1, sky=0.02, world_s=0.03, keep=()):
    """t0 から t1 で部屋の明かりを消す（電気を消す・明かりを落とす場面）"""
    from_frame = f   # core.py の f（クリップの頭からのコマ）
    for o, e in LIGHTS:
        if o in keep: continue
        o.data.energy = e; o.data.keyframe_insert("energy", frame=from_frame(t0))
        o.data.energy = e * sky; o.data.keyframe_insert("energy", frame=from_frame(t1))
    for m, e in GLOWS:
        b = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        b.default_value = e; b.keyframe_insert("default_value", frame=from_frame(t0))
        b.default_value = e * sky; b.keyframe_insert("default_value", frame=from_frame(t1))
    w = bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"]
    v = w.default_value
    w.keyframe_insert("default_value", frame=from_frame(t0)); w.default_value = world_s; w.keyframe_insert("default_value", frame=from_frame(t1)); w.default_value = v


def lights_on(t0, t1):
    from_frame = f   # core.py の f（クリップの頭からのコマ）
    for o, e in LIGHTS:
        o.data.energy = o.data.energy; o.data.keyframe_insert("energy", frame=from_frame(t0))
        o.data.energy = e; o.data.keyframe_insert("energy", frame=from_frame(t1))
    for m, e in GLOWS:
        b = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        b.keyframe_insert("default_value", frame=from_frame(t0)); b.default_value = e; b.keyframe_insert("default_value", frame=from_frame(t1))
    w = bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"]
    w.keyframe_insert("default_value", frame=from_frame(t0)); w.default_value = 0.22; w.keyframe_insert("default_value", frame=from_frame(t1))


# ---------------- 先輩（ロボット掃除機）。前＝-y（まるロボと同じ向きの決め方）
def _v3(p): return (p[0], p[1], p[2] if len(p) > 2 else 0.0)


class Senpai:
    """root（場所・向き）、spin（光の物差しの回る頭）、led（上の小さな光）、wheels、brush、bumper"""
    pass


def _senpai_body(root, top_col, side_col, h=0.075, r=0.17):
    top = mat("sp_top_" + top_col, top_col, rough=0.25, coat=0.7)
    side = mat("sp_side_" + side_col, side_col, rough=0.35, coat=0.3)
    cyl(side, (0, 0, 0.012 + h / 2), r - 0.004, h, parent=root, verts=64)
    cyl(top, (0, 0, 0.012 + h + 0.004), r - 0.012, 0.008, parent=root, verts=64)
    # 前のバンパー（前の半分。黒っぽい帯）
    bump = empty((0, 0, 0)); bump.parent = root
    arc_band(mat("sp_bumper", "#3A3F45", rough=0.5), r + 0.004, r - 0.01, 0.018, 0.012 + h - 0.006, -95, 95, parent=bump)
    # 車輪（横から少し見える）
    wheels = []
    for sx in (-1, 1):
        w = cyl(mat("sp_wheel", "#22262A", rough=0.7), (sx * (r - 0.03), 0.0, 0.03), 0.032, 0.022, rot=(0, R(90), 0), parent=root, verts=24)
        cyl(mat("sp_hub", "#8C949B", rough=0.4, metal=0.6), (0, 0, 0), 0.012, 0.024, parent=w, verts=16)
        wheels.append(w)
    # 横のブラシ（前の右）
    br = empty((0.11, -0.11, 0.008)); br.parent = root
    for k in range(3):
        a = R(k * 120)
        cube(mat("sp_brush", "#E8B04A", rough=0.8), (0.035 * math.cos(a), 0.035 * math.sin(a), 0), (0.07, 0.006, 0.004), rot=(0, 0, a), parent=br)
    # おなかの下の小さな窓（段差を見る光）
    belly = cube(mat("sp_belly", "#101418", rough=0.2), (0, -0.13, 0.009), (0.05, 0.02, 0.004), parent=root)
    return bump, wheels, br, belly


def senpai_lidar(loc=(0, 0, 0), face=0.0):
    root = empty(_v3(loc), R(face))
    bump, wheels, br, belly = _senpai_body(root, "#F3F5F7", "#DDE2E6")
    top_z = 0.012 + 0.075 + 0.008
    # 頭の上の丸いふた（中で光の物差しが回る）
    cyl(mat("lid_base", "#2E3338", rough=0.35, metal=0.3), (0, 0.035, top_z + 0.012), 0.052, 0.024, parent=root, verts=48)
    lid = cyl(mat("lid_glass", "#3C4C58", rough=0.05, trans=0.85, alpha=1.0), (0, 0.035, top_z + 0.034), 0.05, 0.022, parent=root, verts=48)
    cyl(mat("lid_cap", "#2E3338", rough=0.3, metal=0.3), (0, 0.035, top_z + 0.048), 0.052, 0.008, parent=root, verts=48)
    spin = empty((0, 0.035, top_z + 0.032)); spin.parent = root
    cube(mat("lid_head", "#1C2328", rough=0.3), (0, 0, 0), (0.05, 0.025, 0.014), parent=spin)
    sphere(glow_mat("lid_eye", TEAL, 4.0), (0, -0.014, 0), 0.006, parent=spin)
    led = sphere(glow_mat("sp_led", "#7CE8B0", 2.0), (0, -0.12, top_z + 0.002), 0.008, scale=(1, 1, 0.5), parent=root)
    return dict(root=root, spin=spin, led=led, wheels=wheels, brush=br, bumper=bump, belly=belly, lid=lid, top_z=top_z, kind="lidar")


def senpai_camera(loc=(0, 0, 0), face=0.0):
    root = empty(_v3(loc), R(face))
    bump, wheels, br, belly = _senpai_body(root, "#F6D9C8", "#E8C6B2", h=0.07)
    top_z = 0.012 + 0.07 + 0.008
    # 前のカメラ（バンパーの上、少し上を向く）
    cam = empty((0, -0.15, top_z - 0.02)); cam.parent = root; cam.rotation_euler = (R(-35), 0, 0)
    cyl(mat("cam_rim", "#2E3338", rough=0.3, metal=0.4), (0, 0, 0), 0.024, 0.012, rot=(R(90), 0, 0), parent=cam)
    sphere(mat("cam_lens", "#0E1A22", rough=0.05, coat=1.0), (0, -0.006, 0), 0.016, scale=(1, 0.4, 1), parent=cam)
    sphere(glow_mat("cam_ring", TEAL, 1.2), (0, -0.003, 0), 0.02, scale=(1, 0.15, 1), parent=cam)
    head = sphere(glow_mat("cam_head", "#FFF6E0", 0.0), (0.04, -0.155, top_z - 0.026), 0.008, parent=root)   # 自分で照らすライト（21 章）
    led = sphere(glow_mat("sp_led2", "#7CE8B0", 2.0), (0, -0.09, top_z + 0.002), 0.008, scale=(1, 1, 0.5), parent=root)
    cyl(mat("cam_btn", "#E2B9A3", rough=0.3), (0, 0.02, top_z + 0.002), 0.03, 0.006, parent=root)
    return dict(root=root, cam=cam, led=led, wheels=wheels, brush=br, bumper=bump, belly=belly, headlight=head, top_z=top_z, kind="camera")


def senpai_old(loc=(0, 0, 0), face=0.0):
    root = empty(_v3(loc), R(face))
    bump, wheels, br, belly = _senpai_body(root, "#C9CDD1", "#A9AFB5", h=0.085)
    top_z = 0.012 + 0.085 + 0.008
    cyl(mat("old_btn", "#8E959C", rough=0.3, metal=0.5), (0, 0.0, top_z + 0.004), 0.05, 0.01, parent=root)
    cyl(mat("old_handle", "#7D848B", rough=0.4), (0, 0.06, top_z + 0.004), 0.06, 0.006, parent=root)
    led = sphere(glow_mat("old_led", "#7CE8B0", 1.5), (0, -0.11, top_z + 0.002), 0.007, scale=(1, 1, 0.5), parent=root)
    return dict(root=root, led=led, wheels=wheels, brush=br, bumper=bump, belly=belly, top_z=top_z, kind="old")


# ---------------- スマホ（画面の絵は map_tex.py で作る。字なし）
def phone(loc, rot_z=0.0, tex=None, glow=1.4, tilt=0.0):
    e = empty(loc, R(rot_z)); e.rotation_euler = (R(tilt), 0, R(rot_z))
    cube(mat("ph_body", "#1D2126", rough=0.3, metal=0.4), (0, 0, 0.004), (0.078, 0.158, 0.008), bevel=0.006, parent=e)
    if tex:
        sc = plane(img_mat("ph_scr_" + os.path.basename(tex), tex, emit=glow), (0, 0, 0.0085), (0.07, 0.15), parent=e)
    else:
        sc = plane(mat("ph_off", "#0B0E12", rough=0.1, coat=1.0), (0, 0, 0.0085), (0.07, 0.15), parent=e)
    return e, sc


# ---------------- 点の地図（光の物差しが当たった所）。生まれたコマから出て、少しのあいだ明るく光る
def _points_group(name, radius, life):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    m2p = N.new("GeometryNodeMeshToPoints"); m2p.inputs["Radius"].default_value = radius
    st = N.new("GeometryNodeInputSceneTime")
    na = N.new("GeometryNodeInputNamedAttribute"); na.data_type = 'FLOAT'; na.inputs["Name"].default_value = "birth"
    age = N.new("ShaderNodeMath"); age.operation = 'SUBTRACT'
    L.new(st.outputs["Frame"], age.inputs[0]); L.new(na.outputs["Attribute"], age.inputs[1])
    notyet = N.new("ShaderNodeMath"); notyet.operation = 'LESS_THAN'; notyet.inputs[1].default_value = 0.0
    L.new(age.outputs[0], notyet.inputs[0])
    sel = notyet
    if life:
        old = N.new("ShaderNodeMath"); old.operation = 'GREATER_THAN'; old.inputs[1].default_value = life
        L.new(age.outputs[0], old.inputs[0])
        orr = N.new("ShaderNodeMath"); orr.operation = 'MAXIMUM'
        L.new(notyet.outputs[0], orr.inputs[0]); L.new(old.outputs[0], orr.inputs[1]); sel = orr
    dg = N.new("GeometryNodeDeleteGeometry"); dg.domain = 'POINT'
    L.new(gi.outputs[0], m2p.inputs["Mesh"]); L.new(m2p.outputs["Points"], dg.inputs["Geometry"]); L.new(sel.outputs[0], dg.inputs["Selection"])
    sa = N.new("GeometryNodeStoreNamedAttribute"); sa.data_type = 'FLOAT'; sa.domain = 'POINT'; sa.inputs["Name"].default_value = "age"
    L.new(dg.outputs["Geometry"], sa.inputs["Geometry"]); L.new(age.outputs[0], sa.inputs["Value"])
    L.new(sa.outputs["Geometry"], go.inputs[0])
    return ng


def _points_mat(name, col, base, pop, decay):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = 'GEOMETRY'; at.attribute_name = "age"
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = -1.0 / decay
    ex = nt.nodes.new("ShaderNodeMath"); ex.operation = 'EXPONENT'
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY_ADD'; m2.inputs[1].default_value = pop; m2.inputs[2].default_value = base
    nt.links.new(at.outputs["Fac"], m1.inputs[0]); nt.links.new(m1.outputs[0], ex.inputs[0]); nt.links.new(ex.outputs[0], m2.inputs[0])
    em.inputs["Color"].default_value = srgb(col)
    nt.links.new(m2.outputs[0], em.inputs["Strength"]); nt.links.new(em.outputs[0], out.inputs[0])
    m["base"] = base
    return m


def point_cloud(name, pts, col=TEAL, radius=0.018, z=None, base=2.2, pop=8.0, decay=8.0, life=None, t_offset=0.0):
    """pts：(x, y, 生まれた秒) の一覧。秒は場面の頭（CLOCK T0）からの秒"""
    z = plan.LIDAR_Z if z is None else z
    me = bpy.data.meshes.new(name); me.from_pydata([(x, y, z) for x, y, t in pts], [], [])
    a = me.attributes.new("birth", 'FLOAT', 'POINT'); a.data.foreach_set("value", [(t - t_offset) * FPS for x, y, t in pts])
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    mod = ob.modifiers.new("pts", 'NODES'); mod.node_group = _points_group(name + "_g", radius, life * FPS if life else None)
    m = _points_mat(name + "_m", col, base, pop, decay)
    me.materials.append(m)
    # Set Material（点にした後に材質を付ける）
    ng = mod.node_group; sm = ng.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = m
    go = [n for n in ng.nodes if n.type == 'GROUP_OUTPUT'][0]; src = go.inputs[0].links[0].from_socket
    ng.links.new(src, sm.inputs["Geometry"]); ng.links.new(sm.outputs["Geometry"], go.inputs[0])
    ob.visible_shadow = False
    return ob, m


def line_path(name, pts, col=TEAL, width=0.012, z=0.006, emit=2.5):
    """通った道の線（bevel_factor_end を 0→1 に動かすと、線が伸びる）"""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts): sp.points[i].co = (x, y, z, 1)
    cu.bevel_depth = width; cu.bevel_resolution = 2; cu.bevel_factor_mapping_end = 'SPLINE'
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat(name + "_m", col, rough=0.4, emit=emit))
    ob.visible_shadow = False
    return ob


def beam(parent, length=1.0, col=TEAL, r=0.0025, strength=6.0):
    """光の物差しの光の線（parent の -y 方向へ伸びる）。長さは scale.y で変える"""
    e = empty((0, 0, 0)); e.parent = parent
    b = cyl(glow_mat("beam", col, strength), (0, -0.5, 0), r, 1.0, rot=(R(90), 0, 0), parent=e, verts=8)
    b.visible_shadow = False
    e.scale = (1, length, 1)
    return e


def flat_mat(name, col, strength=1.0):
    """影のない光る色（2D の印に近い物。3D の中の矢印・枠）"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = srgb(col); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def ring_marker(loc, r=0.25, col="#FFD24A", w=0.012, z=0.012):
    """床の上の光る輪（ここを見て、の印。字なし）"""
    bpy.ops.mesh.primitive_torus_add(location=(loc[0], loc[1], z), major_radius=r, minor_radius=w, major_segments=64, minor_segments=8)
    o = bpy.context.object; o.data.materials.append(flat_mat("ring_" + col, col, 3.0)); o.visible_shadow = False
    return o


def poop(loc, s=1.0):
    """ペットのうんち（かわいい絵文字くらいの形。3 段の丸）"""
    e = empty(loc, 0.0, s)
    m = mat("poop", "#7A4B2A", rough=0.5, coat=0.6)
    for k, (r, z) in enumerate(((0.05, 0.02), (0.038, 0.055), (0.024, 0.083))):
        sphere(m, (0, 0, z), r, scale=(1, 1, 0.6), parent=e)
    cone = bpy.ops.mesh.primitive_cone_add(radius1=0.012, depth=0.03, location=(0.004, 0, 0.105)); c = bpy.context.object; c.data.materials.append(m); c.parent = e
    return e


def sock(loc, rz=0.0):
    e = empty(loc, R(rz))
    m = mat("sock", "#E65A5A", rough=0.9); m2 = mat("sockstripe", "#FFFFFF", rough=0.9)
    cube(m, (0, 0, 0.012), (0.08, 0.2, 0.022), bevel=0.01, parent=e)
    cube(m, (0.05, -0.1, 0.012), (0.12, 0.07, 0.022), bevel=0.01, parent=e)
    cube(m2, (0, 0.06, 0.012), (0.082, 0.025, 0.024), parent=e)
    return e


def cord(pts, z=0.01):
    cu = bpy.data.curves.new("cord", 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        bp = sp.bezier_points[i]; bp.co = (x, y, z); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.bevel_depth = 0.006; cu.bevel_resolution = 3
    ob = bpy.data.objects.new("cord", cu); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat("cordm", "#2A2E33", rough=0.5))
    return ob


def render_settings(samples, res, fps=FPS):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    dev = os.environ.get("CYCLES_DEVICE", "CPU"); sc.cycles.device = 'GPU' if dev != "CPU" else 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.fps = fps
    sc.render.use_persistent_data = True
    sc.cycles.max_bounces = 6
