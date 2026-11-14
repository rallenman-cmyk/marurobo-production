# ロボットではありません回：舞台の作り込み（2026-11-14 ユーザー「絵がチープすぎる」→「舞台を作り込む」）
# board.py が --rich のときに読み込み、部屋・画面の中の床・マスの床の作り方を差し替える
#   部屋：壁紙・腰板・夜景の窓とカーテン・棚の本・植木・マグ・ノート・ラグ・キーボードのキー・暖かい電気スタンドと縁の光
#   画面の中：上へいくほど青い空（ドーム）・つやのある床と光る線・遠くに浮かぶ白い板とデータの柱・門の光るふち・台座
#   どちらも、まるロボ（または見せたい物）にピントを合わせ、手前と奥を少しぼかす
import random


def grad_dome(bottom="#EAF2F8", top="#5B8DB8", r=80, strength=1.0):
    """上へいくほど色が変わる大きなドーム（空の代わり）"""
    m = bpy.data.materials.new("dome"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Object"], sep.inputs[0]); mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = r * 0.6
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = srgb(bottom); ramp.color_ramp.elements[1].color = srgb(top)
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0, 0, 0)); o = bpy.context.object
    o.data.materials.append(m); o.visible_shadow = False
    for p in o.data.polygons: p.use_smooth = True
    return o


def noise_mat(name, c1, c2, scale=6.0, rough=0.5, wave=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexWave" if wave else "ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = scale
    if wave: tx.inputs["Distortion"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = srgb(c1); ramp.color_ramp.elements[1].color = srgb(c2)
    nt.links.new(tx.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m


def focus_on(loc, fstop=2.8):
    cam = bpy.context.scene.camera
    t = empty(loc); cam.data.dof.use_dof = True; cam.data.dof.focus_object = t; cam.data.dof.aperture_fstop = fstop


# ---------------- 部屋
def desk_room():
    world("#0A1224", 0.08)
    plane(noise_mat("floorwood", "#5A3E2A", "#6E4C33", 3.0, 0.5, wave=True), (0, 0, 0), (20, 20))
    cube(noise_mat("rug", "#3D5A80", "#476A94", 40, 0.95), (0.2, -0.6, 0.005), (3.2, 2.2, 0.01))
    wall = noise_mat("wallpaper", "#33405E", "#3A4868", 30, 0.9, wave=True)
    cube(wall, (0, 2.2, 1.6), (10, 0.1, 3.2))
    cube(mat("baseboard", "#E8E2D6", rough=0.5), (0, 2.13, 0.08), (10, 0.04, 0.16))
    # 夜景の窓・カーテン
    cube(mat("winf", "#D9D3C6", rough=0.4), (-2.3, 2.12, 1.85), (1.5, 0.05, 1.25), bevel=0.02)
    cube(mat("night", "#13224A", emit=0.5), (-2.3, 2.1, 1.85), (1.36, 0.02, 1.1))
    random.seed(3)
    for k in range(26):
        x = -2.95 + k * 0.05 + random.uniform(-0.01, 0.01); h = random.uniform(0.12, 0.45)
        cube(mat("bld", "#0B1430"), (x, 2.085, 1.3 + h / 2), (0.05, 0.01, h))
        if random.random() < 0.6:
            cube(mat("citylight", "#FFD58A", emit=3.0), (x, 2.08, 1.3 + random.uniform(0.04, h - 0.03)), (0.012, 0.005, 0.012))
    cube(mat("winbar", "#D9D3C6", rough=0.4), (-2.3, 2.08, 1.85), (0.03, 0.02, 1.1))
    for sx in (-1, 1):
        for k in range(5):
            cyl(mat("curtain", "#C9A46A", rough=0.9), (-2.3 + sx * (0.78 + k * 0.05), 2.0, 1.75), 0.04, 1.6)
    # 棚と本・植木
    cube(mat("shelf", "#8A6544", rough=0.5), (1.6, 2.05, 2.0), (1.6, 0.25, 0.05), bevel=0.01)
    x = 0.95
    for k in range(11):
        w = random.uniform(0.05, 0.09); h = random.uniform(0.22, 0.33)
        col = random.choice(["#C0504D", "#4F81BD", "#9BBB59", "#F2C14E", "#8064A2", "#E8E2D6"])
        cube(mat("book%d" % k, col, rough=0.6), (x + w / 2, 2.05, 2.03 + h / 2), (w, 0.2, h), bevel=0.005); x += w + 0.008
    cyl(mat("pot", "#D9774B", rough=0.6), (2.15, 2.05, 2.12), 0.08, 0.16)
    for k in range(9):
        a = k * 0.7; sphere(mat("leaf", "#5E9E57", rough=0.5), (2.15 + 0.1 * math.cos(a), 2.05 + 0.06 * math.sin(a), 2.28 + 0.05 * (k % 3)), 0.07, scale=(1.4, 0.6, 0.5))
    # 机
    cube(noise_mat("deskwood", "#9A6E46", "#B0825A", 2.5, 0.45, wave=True), (0, 0.6, 0.72), (3.4, 1.6, 0.06), bevel=0.015)
    for x in (-1.6, 1.6):
        for y in (0.0, 1.3):
            cube(mat("deskleg", "#6E5236", rough=0.6), (x, y, 0.35), (0.06, 0.06, 0.7))
    # 机の上：マグ・ノート・ペン・電気スタンド
    cyl(mat("mug", "#F4F1EA", rough=0.3, coat=0.5), (-1.0, 0.35, 0.82), 0.07, 0.15)
    cyl(mat("coffee", "#3B2416", rough=0.2), (-1.0, 0.35, 0.89), 0.06, 0.005)
    cube(mat("note", "#F2E6C8", rough=0.8), (-1.15, 0.9, 0.76), (0.42, 0.3, 0.02), rot=(0, 0, R(12)))
    cyl(mat("pen", "#2F4A73", rough=0.3), (-1.1, 0.88, 0.78), 0.008, 0.25, rot=(0, R(90), R(30)))
    cyl(mat("lamp_base", "#59616B", rough=0.4, metal=0.5), (1.5, 1.25, 0.77), 0.09, 0.03)
    cyl(mat("lamp_arm", "#59616B", rough=0.4, metal=0.5), (1.5, 1.25, 0.95), 0.012, 0.36)
    cyl(mat("lamp_shade", "#E8D9B0", rough=0.5, emit=0.8), (1.5, 1.15, 1.13), 0.09, 0.08, rot=(R(60), 0, 0))
    bpy.ops.object.light_add(type='POINT', location=(1.45, 1.05, 1.05)); L = bpy.context.object; L.data.energy = 120; L.data.color = srgb("#FFC98A")[:3]; L.data.shadow_soft_size = 0.15
    area((1.8, -1.2, 2.2), (0.3, 0.5, 0.8), 60, 1.5, "#FFE2B8")      # 手前の暖かい光
    area((-0.5, 1.8, 1.6), (0.5, 0.3, 0.9), 80, 0.6, "#8FD8FF")       # まるロボの縁の光（後ろから）


_laptop0 = laptop
def laptop(loc, screen, glow=1.8, rz=0.0, open_deg=105):
    e, h, c = _laptop0(loc, screen, glow, rz, open_deg)
    km = mat("key", "#3E444C", rough=0.5)
    for r in range(4):
        for k in range(12):
            cube(km, (-0.5 + k * 0.09, -0.2 + r * 0.075, 0.05), (0.075, 0.06, 0.012), bevel=0.004).parent = e
    cube(mat("pad", "#9AA3AC", rough=0.4), (0, -0.3, 0.043), (0.32, 0.18, 0.004)).parent = e
    return e, h, c


_room_shot0 = room_shot
def room_shot(screen, maru_loc=(0.55, 0.45, 0.75), **kw):
    _room_shot0(screen, maru_loc=maru_loc, **kw)
    focus_on((maru_loc[0], maru_loc[1], maru_loc[2] + 0.2), 2.4)


# ---------------- 画面の中
FLOOR = "#13213A"     # 画面の中は、夜の青い電子の世界（床は濃い紺のつや、線は青緑に光る）


def digital_bg():
    for o in list(bpy.data.objects):            # 前の昼の光（太陽）は弱める
        if o.type == 'LIGHT' and o.data.type == 'SUN': o.data.energy = 0.6
    world("#0B1530", 0.25)
    grad_dome("#2F7FA6", "#081226", 90, 1.0)
    for L in (area((0, 2, 9), (0, 6, 0), 1500, 10, "#CFE9FF"), area((-6, -4, 4), (0, 5, 1), 500, 4, "#7FD9EE")):   # 上からの広い光・横からの青い光
        L.visible_glossy = False                               # つやのある床に、光の丸い形が映らないように
    random.seed(7)
    panel = mat("panel", "#BFE6F5", rough=0.3, emit=1.2, alpha=0.85)
    for k in range(14):
        x = random.uniform(-24, 24); y = random.uniform(20, 40); z = random.uniform(3, 12)
        if abs(x) < 4 and z < 6: x += 8
        cube(panel, (x, y, z), (random.uniform(1.5, 3.5), 0.08, random.uniform(1.0, 2.2)), bevel=0.15)
    tower = mat("tower", "#1F3557", rough=0.4)
    strip = mat("towerstrip", "#2CD3C2", emit=3.0)
    for k in range(10):
        x = random.choice([-1, 1]) * random.uniform(9, 26); y = random.uniform(14, 36); h = random.uniform(4, 12)
        cube(tower, (x, y, h / 2), (1.2, 1.2, h), bevel=0.08)
        cube(strip, (x, y - 0.61, h * 0.5), (0.12, 0.02, h * 0.8))


_screen_world0 = screen_world
def screen_world(gate_alpha=1.0, gatekeeper=True, dog_down=False, gate=True):
    _screen_world0(gate_alpha, gatekeeper, dog_down, gate)
    for o in list(bpy.data.objects):            # 前の平らな床・灰色の線を、つやのある床と光る線に替える
        if o.type == 'MESH' and o.active_material and o.active_material.name.startswith(("ground", "grid_line")):
            bpy.data.objects.remove(o)
    plane(mat("floor_gloss", FLOOR, rough=0.15, coat=0.8), (0, 0, 0), (60, 60))
    glow = mat("grid_glow", "#2CD3C2", rough=0.4, emit=2.5)
    for k in range(-12, 13):
        cube(glow, (k * 1.5, 6, 0.003), (0.02, 30, 0.003))
        cube(glow, (0, k * 1.5 + 6, 0.003), (36, 0.02, 0.003))
    digital_bg()
    if gate:
        gx, gy = 0.0, 9.0
        edge = mat("gate_edge", "#2CD3C2", emit=4.0, alpha=gate_alpha)
        for sx in (-1, 1): cube(edge, (gx + sx * 1.52, gy - 0.16, 1.4), (0.04, 0.02, 2.8))
        cube(edge, (gx, gy - 0.16, 3.12), (3.1, 0.02, 0.04))
        cube(mat("gate_base", "#2F4A73", rough=0.35, alpha=gate_alpha), (gx, gy, 0.06), (3.6, 1.2, 0.12), bevel=0.04)
        spot((gx, gy - 3, 7), (gx, gy, 1.2), 900, 40, "#E8F7FF")


_street0 = street_floor
def street_floor(selected=(), edge=False):
    _street0(selected, edge)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.active_material and o.active_material.name.startswith("ground"):
            bpy.data.objects.remove(o)
    plane(mat("floor_gloss", FLOOR, rough=0.15, coat=0.8), (0, 0, 0), (60, 60))
    glow = mat("grid_glow2", "#2CD3C2", rough=0.4, emit=2.0)
    for k in range(-12, 13):
        if abs(k * 1.5) > 3.5: cube(glow, (k * 1.5, 6, 0.003), (0.02, 30, 0.003))
    cube(mat("slab", "#2F4A73", rough=0.4), (0, 4, -0.06), (6.3, 6.3, 0.12), bevel=0.03)
    digital_bg()
