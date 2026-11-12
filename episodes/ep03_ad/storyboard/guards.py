# 会話と広告の回：見張り番の別案（ユーザー「違うのにしたい。何アングルも描かなくていいから、パターン違いで」2026-11-12）
# blender -b --factory-startup --python guards.py -- <owl|dog|chip|horn> <out.png> [samples]
# 構図はどれも同じ：門・見張り番（目を閉じて待つ）・耳の前で消える泡・見上げるまるロボ
import os, math, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "gate.py"), encoding="utf-8").read()
exec(src.split("\n\nbpy.ops.wm.read_factory_settings")[0])  # scenes.py の部品・bubble・burst・build（門）を読む
KIND = SCENE
NAVY, DARK, GOLD = "#2F4A73", "#14243A", "#F2C14E"


def closed_eye(m, x, y, z, w=0.13, parent=None):
    # 閉じた目：下向きの弧（細い円柱を 3 本）
    for dx, dz, a in ((-w * 0.33, 0.012, 20), (0, -0.004, 0), (w * 0.33, 0.012, -20)):
        cyl(m, (x + dx, y, z + dz), 0.011, w * 0.4, rot=(0, math.radians(90 + a), 0), parent=parent)


def owl(loc, face):
    # フクロウ：夜の見張りの鳥。耳のふさ（羽角）と、音を集める丸い顔。体に金のバッジ
    g = empty(loc, math.radians(face), 1.0)
    body = mat("o_body", "#8C6E52", rough=0.6, coat=0.1)
    belly = mat("o_belly", "#D8C2A0", rough=0.7)
    face_m = mat("o_face", "#F3E7D3", rough=0.5)
    dark = mat("o_dark", DARK, rough=0.4)
    gold = mat("o_gold", GOLD, rough=0.25, metal=0.8, emit=0.3)
    sphere(body, (0, 0, 0.9), 0.75, scale=(1, 0.9, 1.1), parent=g)
    sphere(belly, (0, -0.32, 0.95), 0.5, scale=(1, 0.6, 0.85), parent=g)
    for i, (bx, bz) in enumerate(((-0.18, 1.12), (0.18, 1.12), (0, 0.95), (-0.2, 0.78), (0.2, 0.78))):
        sphere(body, (bx, -0.6, bz), 0.05, scale=(1.4, 0.4, 0.5), parent=g)  # 胸の羽の模様
    for x in (-0.55, 0.55):  # たたんだ翼
        sphere(body, (x * 1.18, 0.05, 1.0), 0.32, scale=(0.4, 0.8, 1.5), parent=g)
    hd = empty((0, -0.05, 1.85)); hd.parent = g
    sphere(body, (0, 0, 0), 0.62, scale=(1.2, 0.95, 0.85), parent=hd)
    for x in (-0.3, 0.3):  # 顔の皿（音を集める）
        sphere(face_m, (x, -0.42, 0.0), 0.33, scale=(1, 0.35, 1), parent=hd)
        closed_eye(dark, x, -0.53, 0.02, 0.24, parent=hd)
    sphere(gold, (0, -0.58, -0.14), 0.07, scale=(0.8, 1.2, 1.3), parent=hd)  # くちばし
    for sx in (-1, 1):  # 耳のふさ
        e = empty((sx * 0.55, -0.1, 0.4)); e.parent = hd; e.rotation_euler = (0, math.radians(sx * 40), 0)
        add(bpy.ops.mesh.primitive_cone_add, body, (0, 0, 0.15), radius1=0.16, radius2=0.0, depth=0.45, vertices=24, parent=e)
    cyl(gold, (0, -0.68, 0.95), 0.1, 0.03, rot=(math.radians(90), 0, 0), parent=g)  # バッジ
    for x in (-0.25, 0.25):
        sphere(gold, (x, -0.3, 0.06), 0.12, scale=(1.3, 1.6, 0.4), parent=g)  # 足
    return (loc[0] - 0.5, loc[1] - 0.7, 2.35)  # 耳の前（泡が消える所）


def dog(loc, face, eyes="closed", ear_up=True, fur_c="#D9A35B", light_c="#F5E6CC", ears="one_up", cap=False, fluffy=False, patch=None):
    # 番犬：名前を呼ばれたときだけ起きる。片耳だけ立てて、寝ながらも聞いている
    g = empty(loc, math.radians(face), 1.0)
    fur = mat("d_fur" + fur_c, fur_c, rough=0.95 if fluffy else 0.6, coat=0.0 if fluffy else 0.1)
    light = mat("d_light" + light_c, light_c, rough=0.9 if fluffy else 0.6)
    dark = mat("d_dark", "#3A2614", rough=0.4)
    collar = mat("d_collar", "#2F4A73", rough=0.4)
    gold = mat("d_gold", GOLD, rough=0.25, metal=0.8, emit=0.3)
    sphere(fur, (0, 0.25, 0.7), 0.7, scale=(0.9, 1.1, 1.0), parent=g)  # 座った体
    sphere(light, (0, -0.25, 0.85), 0.42, scale=(0.9, 0.6, 1.2), parent=g)  # 胸
    for x in (-0.28, 0.28):  # 前足
        cyl(fur, (x, -0.35, 0.35), 0.12, 0.7, parent=g)
        sphere(light, (x, -0.45, 0.04), 0.14, scale=(1, 1.4, 0.6), parent=g)
    sphere(fur, (0.45, 0.85, 0.35), 0.12, scale=(0.8, 2.2, 0.8), parent=g)  # しっぽ
    hd = empty((0, -0.25, 1.75)); hd.parent = g
    sphere(fur, (0, 0, 0), 0.5, scale=(1, 0.95, 0.9), parent=hd)
    sphere(light, (0, -0.48, -0.12), 0.25, scale=(0.95, 1.35, 0.72), parent=hd)  # 前へ出た鼻先（犬らしく）
    sphere(dark, (0, -0.8, -0.05), 0.08, scale=(1.2, 0.8, 0.9), parent=hd)  # 鼻
    for i, x in enumerate((-0.2, 0.2)):
        if eyes == "open" or (eyes == "one" and i == 1):
            sphere(mat("d_eyew", "#FFFFFF", rough=0.2), (x, -0.43, 0.12), 0.085, scale=(1, 0.5, 1.1), parent=hd)
            sphere(mat("d_pupil", "#1A0F06", rough=0.1), (x, -0.475, 0.12), 0.05, scale=(1, 0.45, 1), parent=hd)
            sphere(mat("d_hl", "#FFFFFF", rough=0.1, emit=1.5), (x + 0.02, -0.5, 0.15), 0.015, parent=hd)
        else:
            closed_eye(dark, x, -0.44, 0.12, 0.15, parent=hd)
    if patch:  # 片目のまわりのぶち
        sphere(mat("d_patch" + patch, patch, rough=0.7), (-0.2, -0.3, 0.14), 0.2, scale=(1, 0.6, 0.9), parent=hd)
    if fluffy:  # ふわふわの首まわり
        for k in range(10):
            a = math.radians(k * 36)
            sphere(light, (0.42 * math.cos(a), -0.15 + 0.3 * math.sin(a) * 0.5, 1.28 + 0.05 * math.sin(a * 2)), 0.2, parent=g)
    ear_in = mat("d_ear_in", "#E59AA0", rough=0.6)
    for sx in (1, -1):
        up = ears == "both_up" or (ears == "one_up" and sx == 1)
        if up:  # 立てた耳（聞いている）
            e = empty((sx * 0.34, 0, 0.3)); e.parent = hd; e.rotation_euler = (math.radians(-15), math.radians(-30 * sx), 0)
            add(bpy.ops.mesh.primitive_cone_add, fur, (0, 0, 0.2), radius1=0.22, radius2=0.03, depth=0.46, vertices=32, scale=(1, 0.4, 1), parent=e)
            add(bpy.ops.mesh.primitive_cone_add, ear_in, (0, -0.06, 0.17), radius1=0.14, radius2=0.02, depth=0.32, vertices=32, scale=(1, 0.2, 1), parent=e)
        else:  # 垂れた耳
            e2 = empty((sx * 0.4, 0, 0.15)); e2.parent = hd; e2.rotation_euler = (0, math.radians(-35 * sx), 0)
            big = ears == "flop"
            sphere(mat("d_earflop" + (patch or fur_c), patch or fur_c, rough=0.6) if big else fur, (0, 0, -0.18 - (0.08 if big else 0)), 0.2 if big else 0.17, scale=(0.55, 0.45, 1.9 if big else 1.5), parent=e2)
    if cap:  # 見張りの帽子
        cyl(mat("d_cap", NAVY, rough=0.4), (0, 0.02, 0.45), 0.3, 0.16, parent=hd)
        cyl(mat("d_cap", NAVY, rough=0.4), (0, -0.2, 0.39), 0.25, 0.03, rot=(math.radians(-10), 0, 0), scale=(1, 0.75, 1), parent=hd)
        cyl(mat("d_gold", GOLD, rough=0.25, metal=0.8, emit=0.3), (0, -0.29, 0.48), 0.05, 0.02, rot=(math.radians(90), 0, 0), parent=hd)
    cyl(collar, (0, -0.2, 1.3), 0.36, 0.1, rot=(math.radians(-15), 0, 0), parent=g)  # 首輪
    cyl(gold, (0, -0.56, 1.18), 0.09, 0.03, rot=(math.radians(90), 0, 0), parent=g)  # 名札
    return (loc[0] - 0.55, loc[1] - 0.7, 2.45)


def chip(loc, face):
    # チップの門番：スマホの中の部品そのもの。黒い小さなチップの体に、ピンの足。頭に音を集める皿
    g = empty(loc, math.radians(face), 1.0)
    blk = mat("c_blk", "#1B2230", rough=0.35, coat=0.5)
    pin = mat("c_pin", "#C9D0D6", rough=0.2, metal=0.9)
    dish = mat("c_dish", "#DDE5EC", rough=0.25, metal=0.6)
    cyan = mat("c_cyan", "#2CD3C2", rough=0.3, emit=1.6)
    dark = mat("c_dark", "#5BE0D3", rough=0.3, emit=0.8)
    cube(blk, (0, 0, 1.1), (1.1, 0.5, 1.1), bevel=0.06, parent=g)
    for i in range(5):  # 横のピン
        for sx in (-1, 1):
            cube(pin, (sx * 0.6, 0, 0.72 + i * 0.19), (0.16, 0.08, 0.05), parent=g)
    for x in (-0.3, 0.3):  # ピンの足
        cyl(pin, (x, 0, 0.3), 0.05, 0.6, parent=g)
        cube(pin, (x, -0.08, 0.02), (0.18, 0.3, 0.04), parent=g)
    cube(mat("c_dot", "#3B4658", rough=0.5), (-0.38, -0.26, 1.5), (0.1, 0.01, 0.1), parent=g)  # 1 番ピンの印
    for x in (-0.22, 0.22):  # 光の目（閉じた形）
        closed_eye(dark, x, -0.26, 1.25, 0.2, parent=g)
    cube(cyan, (0, -0.26, 0.85), (0.5, 0.01, 0.04), parent=g)  # 小さな待機のランプ
    cyl(pin, (0, 0, 1.85), 0.04, 0.4, parent=g)  # 首
    e = empty((0, -0.05, 2.15)); e.parent = g; e.rotation_euler = (math.radians(60), 0, math.radians(75))
    sphere(dish, (0, 0, 0), 0.5, scale=(1, 1, 0.3), parent=e)  # 皿
    sphere(blk, (0, 0, 0.08), 0.32, scale=(1, 1, 0.25), parent=e)
    sphere(cyan, (0, 0, 0.15), 0.07, parent=e)
    return (loc[0] - 0.75, loc[1] - 0.4, 2.3)


def horn(loc, face):
    # ラッパ耳の門番：小さな門番ロボ。頭のラッパ（昔の蓄音機の形）で門の音を聞く。マントと帽子
    g = empty(loc, math.radians(face), 1.0)
    cape = mat("h_cape", NAVY, rough=0.45, coat=0.3)
    head = mat("h_head", "#E8ECEF", rough=0.25, coat=0.6)
    brass = mat("h_brass", "#D9A441", rough=0.2, metal=0.9)
    inner = mat("h_in", "#5A3A16", rough=0.6)
    dark = mat("h_dark", DARK, rough=0.4)
    gold = mat("h_gold", GOLD, rough=0.25, metal=0.8, emit=0.3)
    add(bpy.ops.mesh.primitive_cone_add, cape, (0, 0, 0.75), radius1=0.6, radius2=0.25, depth=1.5, vertices=48, parent=g)
    cyl(gold, (0, -0.42, 1.0), 0.08, 0.03, rot=(math.radians(90 - 14), 0, 0), parent=g)
    hd = empty((0, 0, 1.85)); hd.parent = g
    sphere(head, (0, 0, 0), 0.42, parent=hd)
    for x in (-0.15, 0.15):
        closed_eye(dark, x, -0.4, 0.03, 0.14, parent=hd)
    cyl(dark, (0, 0, 0.36), 0.3, 0.2, parent=hd)  # 帽子
    cyl(dark, (0, -0.15, 0.27), 0.33, 0.03, scale=(1, 0.9, 1), parent=hd)
    # ラッパ：首の横から上へのび、口を門へ向ける
    e = empty((-0.3, 0.0, 0.25)); e.parent = hd; e.rotation_euler = (math.radians(30), math.radians(-60), 0)
    cyl(brass, (0, 0, 0.2), 0.06, 0.4, parent=e)
    add(bpy.ops.mesh.primitive_cone_add, brass, (0, 0, 0.7), radius1=0.08, radius2=0.6, depth=0.7, vertices=48, parent=e)
    cyl(inner, (0, 0, 1.04), 0.56, 0.02, parent=e)
    return (loc[0] - 1.5, loc[1] - 0.8, 2.6)


def build2():
    global V
    V = "A"
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
    pil = mat("gatep", "#C7D0D6", rough=0.3, metal=0.7)
    for x in (-1.3, 1.3):
        cube(pil, (x, 1.8, 1.3), (0.42, 0.42, 2.6), bevel=0.05)
        sphere(mat("lamp_off", "#5A3A2A", rough=0.3), (x, 1.57, 2.42), 0.09)
    cube(pil, (0, 1.8, 2.78), (3.2, 0.5, 0.48), bevel=0.06)
    hole = mat("hole", "#0B1220", rough=0.8)
    for cx in (-0.75, 0.75):
        for i in range(6):
            cyl(hole, (cx + (i - 2.5) * 0.16, 1.54, 2.78), 0.05, 0.02, rot=(math.radians(90), 0, 0), verts=16)
    bar = mat("bar", "#8A97A1", rough=0.25, metal=0.9)
    for i in range(-4, 5):
        cyl(bar, (i * 0.26, 1.8, 1.25), 0.04, 2.5, verts=16)
    cube(bar, (0, 1.8, 0.05), (2.3, 0.08, 0.08))
    ear = {"owl": owl, "dog": dog, "chip": chip, "horn": horn}[KIND]((2.35, 1.0, 0), -40)
    bubble((0.2, 1.5, 1.6), 0.3, "icon_clock.png")
    bubble((1.05, 1.0, 2.05), 0.3, "icon_car.png")
    burst(ear, 0.3, seed=3)
    maru((-1.7, -0.5, 0), face_deg=55, eye_glow=1.2, look_up=18)
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF")
    area((4, -3, 3), (2.3, 1, 1.5), 250, 3, "#FFE9C7")
    spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    camera((-0.9, -7.6, 2.0), (0.6, 1.0, 1.55), lens=32)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
build2()
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
