# 会話と広告の回：絵コンテの静止画（確認用。まるロボは見た目を似せた仮のモデル）
# blender -b --factory-startup --python scenes.py -- <scene> <out.png> [samples]
import bpy, bmesh, math, sys, os
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:]
SCENE, OUT = argv[0], argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 48
RES = (1280, 720)


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


_mats = {}


def mat(name, col, rough=0.45, metal=0.0, coat=0.0, emit=0.0, alpha=1.0, trans=0.0):
    key = (name, col, rough, metal, coat, emit, alpha, trans)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(col)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = srgb(col)
        b.inputs["Emission Strength"].default_value = emit
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    _mats[key] = m
    return m


def img_mat(name, path, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.5
    if emit:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit
    return m


def checker_mat(name, c1, c2, scale=14):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexChecker")
    t.inputs["Color1"].default_value = srgb(c1)
    t.inputs["Color2"].default_value = srgb(c2)
    t.inputs["Scale"].default_value = scale
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    return m


def add(op, m, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), smooth=True, parent=None, **kw):
    op(location=loc, rotation=rot, **kw)
    o = bpy.context.object
    o.scale = scale
    if m:
        o.data.materials.append(m)
    if smooth and hasattr(o.data, "polygons"):
        for p in o.data.polygons:
            p.use_smooth = True
    if parent:
        o.parent = parent
    return o


def sphere(m, loc, r, scale=(1, 1, 1), parent=None, seg=48):
    return add(bpy.ops.mesh.primitive_uv_sphere_add, m, loc, scale=scale, parent=parent, radius=r, segments=seg, ring_count=seg // 2)


def cyl(m, loc, r, depth, rot=(0, 0, 0), scale=(1, 1, 1), parent=None, verts=48):
    return add(bpy.ops.mesh.primitive_cylinder_add, m, loc, rot, scale, parent=parent, radius=r, depth=depth, vertices=verts)


def cube(m, loc, size, rot=(0, 0, 0), bevel=0.0, parent=None):
    o = add(bpy.ops.mesh.primitive_cube_add, m, loc, rot, (size[0] / 2, size[1] / 2, size[2] / 2), smooth=False, parent=parent, size=2)
    if bevel:
        bm = o.modifiers.new("bev", "BEVEL")
        bm.width = bevel
        bm.segments = 3
        bm.affect = 'EDGES'
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o


def plane(m, loc, size, rot=(0, 0, 0), parent=None):
    o = add(bpy.ops.mesh.primitive_plane_add, m, loc, rot, (size[0] / 2, size[1] / 2, 1), smooth=False, parent=parent, size=2)
    return o


def empty(loc=(0, 0, 0), rot_z=0.0, s=1.0):
    bpy.ops.object.empty_add(location=loc)
    e = bpy.context.object
    e.rotation_euler = (0, 0, rot_z)
    e.scale = (s, s, s)
    return e


# ---------------- まるロボ（仮のモデル）：白い球・青緑の一つ目・先がオレンジのアンテナ・短い2本脚と平たい足
def maru(loc=(0, 0, 0), face_deg=0.0, s=1.0, hat=True, eye_glow=0.6, look_up=0.0, jump=0.0, tilt=0.0):
    root = empty(loc, math.radians(face_deg), s)
    body = empty((0, 0, 0.69 + jump))
    body.parent = root
    body.rotation_euler = (math.radians(-look_up), math.radians(tilt), 0)
    white = mat("maru_white", "#F4F6F7", rough=0.22, coat=0.6)
    sphere(white, (0, 0, 0), 0.5, parent=body)
    rim = mat("maru_rim", "#2E3A40", rough=0.35, metal=0.5)
    lens = mat("maru_lens", "#21C1B3", rough=0.08, coat=1.0, emit=eye_glow)
    pupil = mat("maru_pupil", "#0B2730", rough=0.1, coat=1.0)
    hl = mat("maru_hl", "#FFFFFF", rough=0.1, emit=2.0)
    r90 = math.radians(90)
    cyl(rim, (0, -0.445, 0.04), 0.27, 0.10, rot=(r90, 0, 0), parent=body)
    sphere(lens, (0, -0.47, 0.04), 0.225, scale=(1, 0.35, 1), parent=body)
    sphere(pupil, (0, -0.545, 0.04), 0.085, scale=(1, 0.3, 1), parent=body)
    sphere(hl, (0.07, -0.55, 0.11), 0.03, scale=(1, 0.4, 1), parent=body)
    grey = mat("maru_grey", "#9AA4AA", rough=0.4, metal=0.6)
    orange = mat("maru_orange", "#FF8A2A", rough=0.3, coat=0.5, emit=0.3)
    cyl(grey, (0.0, 0.02, 0.62), 0.016, 0.28, parent=body)
    sphere(orange, (0.0, 0.02, 0.78), 0.065, parent=body)
    legm = mat("maru_leg", "#C9D1D5", rough=0.35)
    footm = mat("maru_foot", "#1F8C84", rough=0.4, coat=0.3)
    for x in (-0.17, 0.17):
        cyl(legm, (x, 0, -0.55 - jump), 0.055, 0.22 + 2 * jump, parent=body)
        sphere(footm, (x, -0.05, -0.66 - jump), 0.1, scale=(1.1, 1.5, 0.42), parent=body)
    if hat:
        plaid = checker_mat("hat_plaid", "#B88A55", "#8A6239", 9)
        band = mat("hat_band", "#5B3B22", rough=0.6)
        hat_e = empty((0, 0.03, 0.40))
        hat_e.parent = body
        hat_e.rotation_euler = (math.radians(-8), 0, 0)
        sphere(plaid, (0, 0, 0.02), 0.35, scale=(1, 1.02, 0.7), parent=hat_e)
        cyl(band, (0, 0, -0.03), 0.352, 0.07, parent=hat_e)
        # 前と後ろのつば（体の外へ出す）
        for sy, ang in ((-1, -18), (1, 18)):
            cyl(plaid, (0, sy * 0.40, -0.03), 0.2, 0.03, rot=(math.radians(ang), 0, 0), scale=(1.05, 0.62, 1), parent=hat_e)
        # 横の耳あて（上で結んである）と、上の小さなリボン
        for sx in (-1, 1):
            sphere(plaid, (sx * 0.3, 0, -0.02), 0.1, scale=(0.35, 1, 1.1), parent=hat_e)
        sphere(band, (0, 0, 0.26), 0.05, scale=(1.6, 0.8, 0.8), parent=hat_e)
    return root


# ---------------- 人（記号としての人。顔は描かない）
def person(loc, face_deg=0, shirt="#3E7CB1", pants="#2D3640", skin="#F1C7A5", hair="#2B2220", sit=True, phone=False, head_down=0.0, s=1.0):
    root = empty(loc, math.radians(face_deg), s)
    sm = mat("shirt" + shirt, shirt, rough=0.7)
    pm = mat("pants" + pants, pants, rough=0.7)
    km = mat("skin", skin, rough=0.55)
    hm = mat("hair" + hair, hair, rough=0.6)
    if sit:
        cube(pm, (0, -0.2, 0.47), (0.36, 0.5, 0.16), bevel=0.06, parent=root)
        cube(pm, (0, -0.47, 0.24), (0.34, 0.14, 0.46), bevel=0.05, parent=root)
        torso_z = 0.85
    else:
        cube(pm, (0, 0, 0.42), (0.34, 0.2, 0.84), bevel=0.06, parent=root)
        torso_z = 1.15
    sphere(sm, (0, 0, torso_z), 0.3, scale=(0.75, 0.5, 1.15), parent=root)
    he = empty((0, 0, torso_z + 0.5))
    he.parent = root
    he.rotation_euler = (math.radians(-head_down), 0, 0)
    sphere(km, (0, 0, 0), 0.2, scale=(0.95, 1.0, 1.08), parent=he)
    sphere(hm, (0, 0.04, 0.06), 0.205, scale=(0.98, 1.0, 1.0), parent=he)
    if phone:
        pe = empty((0, -0.33, torso_z + 0.05))
        pe.parent = root
        pe.rotation_euler = (math.radians(60), 0, 0)
        cube(mat("phone_body", "#22262B", rough=0.3), (0, 0, 0), (0.13, 0.26, 0.015), bevel=0.01, parent=pe)
        scr = plane(img_mat("phone_tent", os.path.join(HERE, "phone_ad.png"), emit=1.5), (0, 0, 0.009), (0.115, 0.23), parent=pe)
        scr.rotation_euler = (0, 0, math.radians(180))
        for sx in (-1, 1):
            sphere(km, (sx * 0.07, -0.02, -0.02), 0.045, parent=pe)
    return root


# ---------------- 場面の共通
def world(col="#CFE2EA", strength=1.0):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb(col)
    bg.inputs["Strength"].default_value = strength


def sun(rot=(50, 0, 30), energy=3.0, col="#FFF4E5", angle=8):
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])))
    l = bpy.context.object.data
    l.energy = energy
    l.color = srgb(col)[:3]
    l.angle = math.radians(angle)


def area(loc, target, energy=300, size=3, col="#FFFFFF", shape='DISK'):
    bpy.ops.object.light_add(type='AREA', location=loc)
    o = bpy.context.object
    o.data.energy = energy
    o.data.size = size
    o.data.shape = shape
    o.data.color = srgb(col)[:3]
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o


def spot(loc, target, energy=800, angle=30, col="#FFFFFF", blend=0.3):
    bpy.ops.object.light_add(type='SPOT', location=loc)
    o = bpy.context.object
    o.data.energy = energy
    o.data.spot_size = math.radians(angle)
    o.data.spot_blend = blend
    o.data.color = srgb(col)[:3]
    o.data.shadow_soft_size = 0.3
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o


def camera(loc, target, lens=40):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object
    c.data.lens = lens
    d = Vector(target) - Vector(loc)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = c
    return c


def ground(col, size=60, z=0.0, rough=0.6):
    return plane(mat("ground" + col, col, rough=rough), (0, 0, z), (size, size))


# ---------------- 場面
def s1_detective():
    world("#BFDCE4", 0.9)
    ground("#7FCFC6", size=200)
    # 丸い台
    cyl(mat("dais", "#E9F3F2", rough=0.4, coat=0.3), (0, 0, 0.06), 1.4, 0.12)
    cyl(mat("dais_rim", "#1F8C84", rough=0.4), (0, 0, 0.02), 1.48, 0.04)
    maru((0, 0, 0.12), face_deg=14, eye_glow=0.8, look_up=4)
    # 足元の虫めがね（探偵の小道具。腕がないので置いてある）
    mg = empty((0.62, -0.35, 0.14), math.radians(40))
    cyl(mat("mg_frame", "#3A2A1C", rough=0.35, metal=0.2), (0, 0, 0.03), 0.26, 0.05, parent=mg)
    cyl(mat("mg_glass", "#DDF4F6", rough=0.02, trans=1.0), (0, 0, 0.035), 0.22, 0.052, parent=mg)
    cube(mat("mg_handle", "#6B4528", rough=0.5), (0.0, -0.45, 0.03), (0.08, 0.42, 0.06), bevel=0.03, parent=mg)
    sun((55, 0, -35), 2.5)
    area((-2.5, -3.0, 3.0), (0, 0, 0.8), 500, 3, "#FFF1DD")
    area((3.0, 1.5, 2.0), (0, 0, 0.9), 250, 2, "#BFEFFF")
    camera((1.0, -4.6, 1.55), (0.1, 0, 0.82), lens=48)


def s2_suspects():
    world("#1B2733", 0.25)
    ground("#2C3A47", rough=0.5)
    xs = (-2.3, 0.0, 2.3)
    ped = mat("ped", "#E8EEF1", rough=0.35, coat=0.3)
    cols = ("#E5484D", "#F2A93B", "#8E6CEF")  # 容疑者の色（最後まで同じ色で示す）
    for x, c in zip(xs, cols):
        cyl(ped, (x, 1.2, 0.45), 0.55, 0.9)
        cyl(mat("pedband" + c, c, rough=0.4, emit=0.6), (x, 1.2, 0.86), 0.57, 0.08)
        spot((x, 0.2, 5.2), (x, 1.2, 1.1), 1400, 32, "#FFF6E8")
    # ① マイク
    grille = mat("grille", "#B9C2C8", rough=0.3, metal=0.9)
    sphere(grille, (xs[0], 1.2, 1.55), 0.26)
    cyl(mat("micband", "#E5484D", rough=0.3, metal=0.3), (xs[0], 1.2, 1.32), 0.17, 0.08)
    cyl(mat("michandle", "#30363C", rough=0.35, metal=0.4), (xs[0], 1.2, 1.1), 0.1, 0.42)
    # ② 出ていく手がかり（荷物：位置＝しずくの印、見たページ＝四角、一緒にいた人＝丸2つ）
    box = mat("boxc", "#F2D6A2", rough=0.6)
    cube(box, (xs[1] - 0.22, 1.2, 1.1), (0.38, 0.38, 0.38), bevel=0.03)
    cube(box, (xs[1] + 0.22, 1.15, 1.1), (0.38, 0.38, 0.38), bevel=0.03)
    cube(box, (xs[1], 1.2, 1.48), (0.38, 0.38, 0.38), bevel=0.03)
    mark = mat("mark2", "#F2A93B", rough=0.35, emit=0.4)
    sphere(mark, (xs[1] - 0.22, 0.99, 1.13), 0.08, scale=(1, 0.3, 1))
    cube(mark, (xs[1] + 0.22, 0.95, 1.1), (0.15, 0.03, 0.15))
    sphere(mark, (xs[1] - 0.06, 0.99, 1.48), 0.06, scale=(1, 0.3, 1))
    sphere(mark, (xs[1] + 0.06, 0.99, 1.48), 0.06, scale=(1, 0.3, 1))
    # ③ わたしたちの記憶（ガラスの箱と、中で光るカード）
    cube(mat("glass", "#E6F4F8", rough=0.03, trans=1.0), (xs[2], 1.2, 1.3), (0.62, 0.5, 0.75), bevel=0.04)
    for i, (dx, dz, rz) in enumerate(((-0.12, 1.12, 10), (0.1, 1.2, -15), (-0.02, 1.36, 25), (0.12, 1.5, -5))):
        cc = ("#8E6CEF", "#B9A6FF", "#8E6CEF", "#FFE07A")[i]
        cube(mat("card" + str(i), cc, rough=0.4, emit=1.2 if i == 3 else 0.3), (xs[2] + dx, 1.2, dz), (0.24, 0.02, 0.16), rot=(0.2, 0, math.radians(rz)))
    maru((0.15, -1.45, 0), face_deg=170, eye_glow=1.0, look_up=12)
    area((0, -4, 3), (0, 0.5, 1), 220, 4, "#A9C8FF")
    camera((0.6, -5.4, 2.2), (0.0, 0.6, 1.05), lens=36)


def s3_gate():
    world("#0E1A2B", 0.3)
    fl = ground("#14263B", rough=0.4)
    # 回路の光る線（スマホの中の町）
    line = mat("circuit", "#2CD3C2", rough=0.4, emit=2.2)
    for x in (-3.5, -1.8, 1.8, 3.5):
        cube(line, (x, 3, 0.005), (0.05, 14, 0.01))
    for y in (-1.2, 1.0, 3.5, 6.5):
        cube(line, (0, y, 0.005), (14, 0.05, 0.01))
    # 遠くの部品（ビル）
    bm = mat("chipb", "#22354D", rough=0.5)
    for x, y, h in ((-4, 7, 2.2), (-2.5, 9, 3.0), (3.2, 8, 2.6), (4.6, 6, 1.6), (0.8, 11, 3.6)):
        cube(bm, (x, y, h / 2), (1.4, 1.4, h), bevel=0.05)
        cube(mat("chipwin", "#5BE0D3", emit=1.5), (x, y - 0.71, h * 0.7), (0.9, 0.01, 0.08))
    # マイクの門：2本の柱と、上の音の穴の板、閉じた格子
    pil = mat("gatep", "#C7D0D6", rough=0.3, metal=0.7)
    for x in (-1.3, 1.3):
        cube(pil, (x, 1.8, 1.3), (0.4, 0.4, 2.6), bevel=0.05)
        sphere(mat("lampr", "#E5484D", emit=3.0), (x, 1.58, 2.45), 0.08)
    top = cube(pil, (0, 1.8, 2.75), (3.2, 0.5, 0.45), bevel=0.06)
    hole = mat("hole", "#0B1220", rough=0.8)
    for i in range(-5, 6):
        cyl(hole, (i * 0.22, 1.54, 2.75), 0.055, 0.02, rot=(math.radians(90), 0, 0), verts=16)
    bar = mat("bar", "#8A97A1", rough=0.25, metal=0.9)
    for i in range(-4, 5):
        cyl(bar, (i * 0.26, 1.8, 1.25), 0.04, 2.5, verts=16)
    # 見張り番：大きな耳（皿）を持つ細いロボ。合言葉以外は聞き流す（目を閉じている）
    g = empty((1.95, 1.2, 0), math.radians(-20))
    gm = mat("guard", "#3D5A80", rough=0.35, coat=0.4)
    cyl(gm, (0, 0, 0.75), 0.22, 1.5, parent=g)
    sphere(gm, (0, 0, 1.6), 0.3, parent=g)
    ear = mat("ear", "#F2C14E", rough=0.3, metal=0.3, emit=0.2)
    sphere(ear, (0.32, 0, 1.65), 0.26, scale=(0.35, 1, 1), parent=g)
    cube(mat("eyeclosed", "#9FB6CC", emit=0.5), (0, -0.29, 1.62), (0.2, 0.03, 0.03), parent=g)
    maru((-0.5, -0.4, 0), face_deg=-160, eye_glow=1.2, look_up=10, jump=0.05)
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF")
    spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    camera((-2.3, -5.0, 1.6), (0.2, 1.0, 1.15), lens=34)


def s4_auction():
    world("#2A1E3B", 0.3)
    ground("#3A2C50", rough=0.45)
    # 広告の枠（まだ空。ここに出る広告を、一瞬で決める）
    fr = mat("frame", "#FFD166", rough=0.3, metal=0.6, emit=0.4)
    cube(fr, (0, 3.2, 2.3), (2.6, 0.12, 1.7), bevel=0.04)
    cube(mat("slot", "#FFFFFF", emit=2.5), (0, 3.12, 2.3), (2.3, 0.02, 1.4))
    cyl(mat("stand", "#5A4A73", rough=0.4), (0, 3.25, 0.7), 0.12, 1.4)
    # 会社の人たち（ブロックの体と、札を上げる腕）
    import random
    random.seed(4)
    cols = ["#E5484D", "#3E7CB1", "#2BB3A6", "#F2A93B", "#8E6CEF", "#E86FA3", "#5DBB63", "#4C6EF5"]
    n = 11
    for i in range(n):
        a = math.radians(-70 + 140 * i / (n - 1))
        r = 3.2
        x, y = r * math.sin(a), 3.2 - r * math.cos(a) * 0.95
        c = cols[i % len(cols)]
        e = empty((x, y, 0), math.atan2(x - 0, -(y - 3.2)) + math.pi)
        bm_ = mat("rep" + c, c, rough=0.45, coat=0.3)
        cube(bm_, (0, 0, 0.5), (0.42, 0.32, 1.0), bevel=0.12, parent=e)
        sphere(mat("rephead", "#F3E3D3", rough=0.5), (0, 0, 1.22), 0.2, parent=e)
        up = random.random() < 0.8
        h = 1.65 + (random.random() * 0.35 if up else -0.6)
        cyl(mat("stick", "#DDDDDD", rough=0.5), (0.26, 0, h - 0.25), 0.025, 0.6, parent=e)
        cyl(mat("paddle" + c, "#FFFFFF", rough=0.4, emit=0.3), (0.26, -0.01, h + 0.12), 0.17, 0.03, rot=(math.radians(90), 0, 0), parent=e)
        cyl(mat("pdot" + c, c, rough=0.4, emit=1.0), (0.26, -0.03, h + 0.12), 0.08, 0.02, rot=(math.radians(90), 0, 0), parent=e)
    # 一瞬で決まる：光のすじ（札から枠へ）
    maru((-2.9, -1.6, 0), face_deg=-140, eye_glow=1.2, look_up=14, jump=0.25)
    spot((0, 0.5, 6), (0, 2.6, 1.2), 1600, 60, "#FFE9C7")
    area((-3, -4, 3), (0, 2, 1), 300, 4, "#C8B8FF")
    camera((-0.6, -5.6, 2.4), (0.0, 2.0, 1.25), lens=30)


def s5_train():
    world("#E8D9C5", 0.6)
    fl = ground("#8D8577", size=30)
    # 車内（ゆかの縞・長い座席・窓・つり広告）
    wall = mat("trainwall", "#EDEAE3", rough=0.6)
    seat = mat("seat", "#3E6E9E", rough=0.8)
    cube(wall, (0, 1.55, 1.4), (12, 0.1, 2.8))
    cube(wall, (0, -1.55, 1.4), (12, 0.1, 2.8))
    cube(wall, (0, 0, 2.55), (12, 3.2, 0.1))
    # 窓の外は秋（赤と黄の木々）
    outside = mat("autumn", "#E07A3A", rough=0.9, emit=1.4)
    outside2 = mat("autumn2", "#F2C14E", rough=0.9, emit=1.4)
    for x in (-3.6, -1.2, 1.2, 3.6):
        cube(mat("frame_w", "#B8B2A6", metal=0.6, rough=0.3), (x, 1.49, 1.55), (1.9, 0.04, 0.95))
        cube(outside if x < 0 else outside2, (x, 1.52, 1.55), (1.75, 0.03, 0.8))
        cube(mat("sky_o", "#BFE3F2", emit=1.4), (x, 1.515, 1.85), (1.75, 0.03, 0.25))
    cube(seat, (0, 1.2, 0.42), (9, 0.6, 0.18), bevel=0.06)
    cube(seat, (0, 1.45, 0.8), (9, 0.12, 0.6), bevel=0.05)
    # つり広告（テントの絵が3枚。ほかの広告は色だけ）
    tent = img_mat("tentposter", os.path.join(HERE, "tent.png"), emit=0.6)
    others = ["#9BC4E2", "#F6B8C8", "#C9E4B4", "#FFE3A3"]
    xs = [-4.2, -2.8, -1.4, 0.0, 1.4, 2.8, 4.2]
    tent_at = {-2.8, 0.0, 2.8}
    for i, x in enumerate(xs):
        y = 0.25
        cyl(mat("wire", "#888888", metal=0.8, rough=0.3), (x, y, 2.38), 0.01, 0.25, verts=8)
        m = tent if x in tent_at else mat("adc" + str(i), others[i % 4], rough=0.6, emit=0.4)
        p = plane(m, (x, y, 1.95), (0.6, 0.8), rot=(math.radians(90), 0, 0))
    # つり革と手すり
    cyl(mat("rail", "#C9CDD1", metal=0.9, rough=0.2), (0, -0.9, 2.2), 0.025, 12, rot=(0, math.radians(90), 0))
    for x in (-3.5, -2.5, -1.5, 1.5, 2.5, 3.5):
        add(bpy.ops.mesh.primitive_torus_add, mat("strap", "#F2F2F2", rough=0.4), (x, -0.9, 1.85), (math.radians(90), 0, 0), major_radius=0.08, minor_radius=0.015)
    # 人：A（話している）と B（テントの写真を見ている）。まるロボはそのあいだ
    person((-0.9, 1.15, 0), face_deg=180, shirt="#4E8FC7", hair="#2B2220", head_down=5)
    person((0.9, 1.15, 0), face_deg=180, shirt="#E58C5A", hair="#6A4A3A", phone=True, head_down=30)
    maru((0.0, 1.05, 0.5), face_deg=180, s=0.55, hat=False, eye_glow=0.6, look_up=0)
    area((0, -1.0, 2.4), (0, 0.5, 1), 500, 4, "#FFF6E8", shape='RECTANGLE')
    sun((60, 0, 160), 1.5)
    camera((0.3, -1.45, 1.35), (0.0, 1.0, 1.4), lens=22)


def s6_ending():
    world("#0C1426", 0.15)
    ground("#2A2F45", size=20)
    # 夜の部屋：ふとん、スマホの光
    cube(mat("futon", "#E9E2D4", rough=0.9), (0, 0.4, 0.12), (2.4, 1.6, 0.24), bevel=0.1)
    cube(mat("blanket", "#5B7DB8", rough=0.9), (0, 0.6, 0.27), (2.3, 1.2, 0.12), bevel=0.06)
    cube(mat("pillow", "#F4F1EA", rough=0.9), (0, -0.25, 0.32), (0.8, 0.35, 0.16), bevel=0.07)
    pe = empty((0.35, -0.85, 0.02), math.radians(10))
    cube(mat("phone_body2", "#22262B", rough=0.3), (0, 0, 0.012), (0.36, 0.72, 0.03), bevel=0.02, parent=pe)
    scr = plane(img_mat("phone_ad2", os.path.join(HERE, "phone_ad.png"), emit=3.0), (0, 0, 0.03), (0.32, 0.64), parent=pe)
    scr.rotation_euler = (0, 0, math.radians(180))
    bpy.ops.object.light_add(type='POINT', location=(0.35, -0.85, 0.6))
    l = bpy.context.object.data
    l.energy = 60
    l.color = srgb("#CFEFFF")[:3]
    maru((-0.55, -1.0, 0), face_deg=-205, eye_glow=1.5, look_up=-12, jump=0.32, tilt=8)
    # 窓の月明かり
    area((-3, 2, 3), (0, 0, 0), 120, 2, "#7F9CFF")
    camera((0.2, -3.6, 1.7), (-0.15, -0.6, 0.55), lens=36)


SCENES = dict(s1=s1_detective, s2=s2_suspects, s3=s3_gate, s4=s4_auction, s5=s5_train, s6=s6_ending)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
SCENES[SCENE]()
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = RES
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Punchy'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT)
