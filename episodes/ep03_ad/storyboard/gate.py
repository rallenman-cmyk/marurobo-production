# 会話と広告の回：マイクの門と見張り番（絵コンテ）。scenes.py の部品を使う
# blender -b --factory-startup --python gate.py -- <A|B|C> <out.png> [samples]
import os, sys, math, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read()
exec(src.split("# ---------------- 場面\n")[0])  # 部品（mat・sphere・maru など）と argv
V = SCENE  # A：泡が頭の上で消える／B：片目だけ開く／C：門が開いてランプが光る


def icon_mat(name, path, glow=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = glow
    return m


def bubble(loc, r=0.3, icon=None, glow=0.0):
    e = empty(loc)
    g = mat("bubble%.1f" % glow, "#DDF6FF", rough=0.02, trans=1.0, emit=glow)
    o = sphere(g, (0, 0, 0), r, parent=e)
    b = o.data.materials[0].node_tree.nodes["Principled BSDF"]
    b.inputs["IOR"].default_value = 1.05
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Thin Film Thickness"].default_value = 450
    if icon:
        p = plane(icon_mat("ic" + icon, os.path.join(HERE, icon)), (0, 0, 0), (r * 1.15, r * 1.15), rot=(math.radians(90), 0, 0), parent=e)
        p.rotation_euler = (math.radians(80), 0, math.radians(-12))
    return e


def burst(loc, r=0.35, n=14, seed=1):
    import random
    random.seed(seed)
    dm = mat("drop", "#E6FAFF", rough=0.05, trans=1.0, emit=0.6)
    for k in range(n):
        a = 2 * math.pi * k / n + random.uniform(-0.2, 0.2)
        el = random.uniform(-0.7, 0.9)
        rr = r * random.uniform(0.85, 1.25)
        x = loc[0] + rr * math.cos(a) * math.cos(el)
        y = loc[1] + rr * math.sin(a) * math.cos(el) * 0.6
        z = loc[2] + rr * math.sin(el)
        sphere(dm, (x, y, z), random.uniform(0.025, 0.05), seg=16)
    # 一瞬の光の輪
    add(bpy.ops.mesh.primitive_torus_add, mat("pop", "#FFFFFF", emit=3.0), loc, (math.radians(75), 0, 0), major_radius=r * 0.8, minor_radius=0.008)


def guard(loc, face_deg, eyes="closed"):
    g = empty(loc, math.radians(face_deg), 1.22)
    navy = mat("g_navy", "#2F4A73", rough=0.35, coat=0.4)
    light = mat("g_head", "#8FB3D9", rough=0.3, coat=0.5)
    gold = mat("g_gold", "#F2C14E", rough=0.25, metal=0.8)
    dark = mat("g_dark", "#14243A", rough=0.4)
    for x in (-0.13, 0.13):
        sphere(dark, (x, -0.05, 0.07), 0.1, scale=(1.0, 1.6, 0.6), parent=g)
    cyl(navy, (0, 0, 0.72), 0.3, 1.3, parent=g)
    sphere(navy, (0, 0, 1.37), 0.3, scale=(1, 1, 0.3), parent=g)
    cyl(gold, (0, 0, 0.62), 0.31, 0.07, parent=g)
    cyl(mat("g_badge", "#FFD166", rough=0.2, metal=0.6, emit=0.4), (0.0, -0.3, 1.05), 0.07, 0.03, rot=(math.radians(90), 0, 0), parent=g)
    hd = empty((0, 0, 1.78))
    hd.parent = g
    sphere(light, (0, 0, 0), 0.36, parent=hd)
    # 帽子（見張りの帽子）
    cyl(dark, (0, 0, 0.27), 0.33, 0.2, parent=hd)
    cyl(dark, (0, -0.2, 0.18), 0.24, 0.03, rot=(math.radians(-12), 0, 0), scale=(1, 0.7, 1), parent=hd)
    cyl(gold, (0, -0.33, 0.29), 0.05, 0.02, rot=(math.radians(90), 0, 0), parent=hd)
    # 大きな耳（片方だけ。音を聞く係）
    ear = mat("g_ear", "#F2B33D", rough=0.35, coat=0.6)
    inner = mat("g_ear_in", "#B86A1E", rough=0.6)
    ee = empty((0.4, 0.0, 0.02))
    ee.parent = hd
    ee.rotation_euler = (0, 0, math.radians(-55))  # 耳の穴を少し前へ向ける
    sphere(ear, (0.07, 0, 0), 0.38, scale=(0.3, 0.75, 1.0), parent=ee)
    sphere(inner, (0.15, 0, 0), 0.3, scale=(0.18, 0.62, 0.84), parent=ee)
    sphere(mat("g_ear_deep", "#5A2E0C", rough=0.8), (0.17, 0, -0.02), 0.12, scale=(0.15, 0.6, 0.8), parent=ee)
    sphere(ear, (-0.34, 0.0, 0.0), 0.07, scale=(0.5, 0.8, 1.0), parent=hd)
    # 目
    for i, x in enumerate((-0.12, 0.12)):
        is_open = eyes == "open" or (eyes == "one" and i == 1)
        if is_open:
            sphere(mat("g_eyew", "#FFFFFF", rough=0.2), (x, -0.31, 0.04), 0.085, scale=(1, 0.45, 1.1), parent=hd)
            sphere(mat("g_pupil", "#0E1A2B", rough=0.1), (x, -0.355, 0.04), 0.04, scale=(1, 0.4, 1), parent=hd)
        else:
            cyl(dark, (x, -0.335, 0.03), 0.012, 0.13, rot=(0, math.radians(90), 0), parent=hd)
    cyl(dark, (0, -0.345, -0.12), 0.01, 0.08, rot=(0, math.radians(90), 0), parent=hd)
    return g


def build():
    world("#0E1A2B", 0.3)
    ground("#14263B", rough=0.4)
    line = mat("circuit", "#2CD3C2", rough=0.4, emit=2.2)
    for x in (-3.5, -1.8, 1.8, 3.5):
        cube(line, (x, 3, 0.005), (0.05, 14, 0.01))
    for y in (-1.2, 0.6, 3.5, 6.5):
        cube(line, (0, y, 0.005), (14, 0.05, 0.01))
    bm = mat("chipb", "#22354D", rough=0.5)
    for x, y, h in ((-4.2, 7, 2.2), (-2.6, 9, 3.0), (3.2, 8, 2.6), (4.8, 6, 1.6), (0.9, 11, 3.6)):
        cube(bm, (x, y, h / 2), (1.4, 1.4, h), bevel=0.05)
        cube(mat("chipwin", "#5BE0D3", emit=1.5), (x, y - 0.71, h * 0.7), (0.9, 0.01, 0.08))
    # 門
    pil = mat("gatep", "#C7D0D6", rough=0.3, metal=0.7)
    lamp_on = V == "C"
    for x in (-1.3, 1.3):
        cube(pil, (x, 1.8, 1.3), (0.42, 0.42, 2.6), bevel=0.05)
        lm = mat("lamp_on" if lamp_on else "lamp_off", "#FF7A00" if lamp_on else "#5A3A2A", rough=0.3, emit=2.2 if lamp_on else 0.0)
        sphere(lm, (x, 1.57, 2.42), 0.09)
        if lamp_on:
            bpy.ops.object.light_add(type='POINT', location=(x, 1.3, 2.42))
            bpy.context.object.data.energy = 60
            bpy.context.object.data.color = srgb("#FF7A00")[:3]
    cube(pil, (0, 1.8, 2.78), (3.2, 0.5, 0.48), bevel=0.06)
    # スマホの下の穴と同じ並び（丸い穴 6 つの組を 2 つ）
    hole = mat("hole", "#0B1220", rough=0.8)
    for cx in (-0.75, 0.75):
        for i in range(6):
            cyl(hole, (cx + (i - 2.5) * 0.16, 1.54, 2.78), 0.05, 0.02, rot=(math.radians(90), 0, 0), verts=16)
    bar = mat("bar", "#8A97A1", rough=0.25, metal=0.9)
    lift = 2.2 if V == "C" else 0.0
    for i in range(-4, 5):
        cyl(bar, (i * 0.26, 1.8, 1.25 + lift), 0.04, 2.5, verts=16)
    cube(bar, (0, 1.8, 0.05 + lift), (2.3, 0.08, 0.08))
    # 見張り番
    guard((2.05, 1.0, 0), -35, eyes={"A": "closed", "B": "one", "C": "open"}[V])
    # 泡と、まるロボ
    if V == "A":
        bubble((0.15, 1.75, 1.55), 0.3, "icon_clock.png")  # 門を通ってくる泡
        bubble((1.0, 1.1, 1.95), 0.3, "icon_car.png")
        burst((2.0, 0.55, 2.45), 0.3, seed=3)  # 見張り番の耳の前で消えた泡
        burst((-0.6, -0.5, 1.95), 0.42, n=18, seed=7)  # まるロボの頭の上で消えた泡
        maru((-0.6, -0.5, 0), face_deg=35, eye_glow=1.2, look_up=22, jump=0.18)
    elif V == "B":
        bubble((1.35, 0.7, 2.3), 0.3, None, glow=0.4)  # 似た言葉（字は 2D で重ねる）
        maru((-0.5, -0.5, 0), face_deg=55, eye_glow=1.4, look_up=26, tilt=-8)
    else:
        bubble((0.35, 1.6, 1.7), 0.32, None, glow=1.5)  # 本物の合言葉（字は 2D で重ねる）
        maru((-0.6, -0.5, 0), face_deg=30, eye_glow=1.6, look_up=14, jump=0.35)
        bpy.data.materials["maru_orange"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 8.0
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF")
    spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    camera((-2.4, -5.0, 1.5), (0.25, 1.0, 1.25), lens=33)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
build()
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
