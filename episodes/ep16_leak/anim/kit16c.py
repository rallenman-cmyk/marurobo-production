# 16本目 3章（S18〜S21）の 3D の部品：夜の道（E1）・荷車・かくれた市場の倉庫（E2）・棚・印の付いた箱・値札・硬貨
#   scenes_ch3.py が exec で読む（前提：kit16.py・kit16b.py を読んだあと）。絵コンテ表：../絵コンテ_v1.md の「3章」
#   決まり：3D の中に字を書かない。箱の印はお城の形の絵（emb0＝冒頭のメールのお店の印＝まるロボのお城、emb1〜5＝ほかのお城）
#   座標：道は −x から倉庫の入口（x=0, y=0）へまっすぐ。倉庫の中は x 0〜WH_L、y −WH_W/2〜+WH_W/2
ROAD_X0 = -60.0          # 道のはじめ（お城の側）
ROAD_STONE_END = -34.0   # ここまで石の道と街灯。この先は土の道で、だんだん細くなる
WH_L, WH_W, WH_H = 10.0, 8.0, 3.4      # 倉庫の中の長さ・はば・高さ
WH_DOOR_W, WH_DOOR_H = 1.4, 2.2
ROWS = [(-2.6, +1), (-0.2, -1), (0.2, +1), (2.6, -1)]      # 棚の面（y, 箱の前が向く向き ±y）。y=-1.4 と +1.4 が通路
SHELF_X0, SHELF_X1 = 2.0, 9.2
LEVELS = (0.12, 0.62, 1.12)        # 棚の段の高さ（箱の底）
BOX_W, BOX_D, BOX_H = 0.42, 0.32, 0.26
MARKET = {}


def road_width(x):
    """道のはば：石の道は 3.2 m、土の道は −34 m から 0 m までで 3.0 → 1.3 m に細くなる"""
    if x <= ROAD_STONE_END: return 3.2
    u = min(1.0, (x - ROAD_STONE_END) / (0.0 - ROAD_STONE_END - 4.0))
    return 3.0 - 1.7 * u


def night_road():
    """夜の道（E1）：はじめは石の道と街灯、先は細い土の道（街灯なし）。両側に木。つきあたりは倉庫"""
    world("#0B1020", 0.35)
    bpy.ops.object.light_add(type='SUN', rotation=(R(55), 0, R(-30))); mn = bpy.context.object
    mn.data.energy = 0.35; mn.data.color = srgb("#9FB4E8")[:3]; MARKET["moon"] = mn
    grass = noise_mat("e_grass", "#1C2A22", "#16221B", 3.0, 0.95)
    cube(grass, ((ROAD_X0 + 20) / 2, 0, -0.06), (abs(ROAD_X0) + 40, 60, 0.1))
    stone = noise_mat("e_stone", "#6E6A63", "#5E5A54", 1.6, 0.8)
    dirt = noise_mat("e_dirt", "#5A4836", "#4A3B2C", 2.2, 0.95)
    cube(stone, ((ROAD_X0 + ROAD_STONE_END) / 2, 0, -0.011), (ROAD_STONE_END - ROAD_X0, 3.2, 0.02))      # 上の面を 0 に（影の足が板に入っていた）
    x = ROAD_STONE_END
    while x < 0.0:          # 土の道は 2 m ずつ、だんだん細く
        w_ = road_width(x + 1.0)
        cube(dirt, (x + 1.0, 0, -0.0105), (2.02, w_, 0.02)); x += 2.0
    pole = mat("e_pole", "#2A2C30", rough=0.4, metal=0.6)
    glow = bpy.data.materials.new("e_lampglow"); glow.use_nodes = True
    bb = glow.node_tree.nodes["Principled BSDF"]; bb.inputs["Emission Color"].default_value = srgb("#FFD79A"); bb.inputs["Emission Strength"].default_value = 6.0
    lamps = []
    for lx in (-58.0, -50.0, -42.0, -36.0):      # 街灯は石の道だけ（土の道へ入ると暗くなる。18-03）
        cyl(pole, (lx, 2.0, 1.6), 0.05, 3.2, verts=12)
        cube(pole, (lx, 1.75, 3.2), (0.08, 0.55, 0.06))
        sphere(glow, (lx, 1.5, 3.1), 0.14, seg=16)
        bpy.ops.object.light_add(type='POINT', location=(lx, 1.4, 2.9)); L = bpy.context.object
        L.data.energy = 220; L.data.color = srgb("#FFD08A")[:3]; L.data.shadow_soft_size = 0.4; lamps.append(L)
    MARKET["lamps"] = lamps
    trunk = mat("e_trunk", "#2B2119", rough=0.9); leaf = noise_mat("e_leaf", "#13261B", "#0F1F16", 2.5, 0.9)
    import random
    rnd = random.Random(1801)
    tx = ROAD_X0 + 2.0
    while tx < -3.0:
        for sgn in (-1, 1):
            y = sgn * (road_width(tx) / 2 + 1.2 + rnd.uniform(0, 1.5)); h = rnd.uniform(2.6, 4.2)
            cyl(trunk, (tx + rnd.uniform(-0.8, 0.8), y, h * 0.3), 0.12, h * 0.6, verts=10)
            bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=rnd.uniform(0.9, 1.3), radius2=0.0, depth=h * 0.8, location=(tx, y, h * 0.6 + h * 0.4))
            c_ = bpy.context.object; c_.data.materials.append(leaf)
        tx += rnd.uniform(3.0, 4.5) if tx < ROAD_STONE_END else rnd.uniform(2.0, 3.0)      # 土の道は木を多く（道が細く暗くなる）
    return lamps


def cart(loc, face=0.0):
    """荷車（2章 16-01 で箱を積んだ物と同じ形）。前（引く棒の側）＝+x。返す：(根もと, 車輪のリスト, 荷台の上の高さ)"""
    root = empty(loc, R(face))
    cw_ = mat("cart", "#3A2C22", rough=0.8); BED = 0.46
    cube(cw_, (0, 0, BED - 0.03), (0.8, 0.62, 0.05), parent=root)
    for sx in (-1, 1): cube(cw_, (sx * 0.4, 0, BED + 0.08), (0.04, 0.62, 0.2), parent=root)
    for sy in (-1, 1): cube(cw_, (0, sy * 0.31, BED + 0.08), (0.8, 0.04, 0.2), parent=root)
    wheels = []
    for sy in (-1, 1):
        wh = empty((0, sy * 0.36, 0.25)); wh.parent = root
        cyl(mat("wheel", "#1E1712", rough=0.8), (0, 0, 0), 0.25, 0.06, rot=(R(90), 0, 0), parent=wh, verts=20)
        cube(mat("spoke", "#5A4634", rough=0.7), (0, 0, 0), (0.46, 0.065, 0.04), parent=wh)
        wheels.append(wh)
    for sy in (-1, 1): cube(cw_, (0.75, sy * 0.18, 0.42), (0.75, 0.04, 0.04), rot=(0, R(-12), 0), parent=root)     # 引く棒（+x）
    return root, wheels, BED


def roll_cart(root, wheels, keys):
    """荷車を keys＝[(t, (x, y))] の順に動かし、進んだ道のりで車輪を回す（すべって見えないように）"""
    dist = 0.0; prev = None
    for t, (x, y) in keys:
        if prev is not None: dist += math.hypot(x - prev[0], y - prev[1])
        key(root, "location", t, (x, y, 0.0), "LINEAR")
        for wh in wheels: key(wh, "rotation_euler", t, (0, dist / 0.25, 0), "LINEAR")
        prev = (x, y)


def warehouse():
    """かくれた市場の倉庫（E2）。入口は x=0 の面（−x を向く）のまん中。中はうす暗いが、棚の箱が見える明るさ（絵コンテ表）"""
    wood = noise_mat("e_whwall", "#3E342C", "#342B24", 2.0, 0.9, wave=True)
    floor = noise_mat("e_whfloor", "#4A4038", "#3E352E", 2.5, 0.9)
    cube(floor, (WH_L / 2, 0, -0.02), (WH_L, WH_W, 0.04))
    cube(mat("e_ceil", "#24201C", rough=0.95), (WH_L / 2, 0, WH_H + 0.05), (WH_L + 0.4, WH_W + 0.4, 0.1))
    T = 0.2
    cube(wood, (WH_L + T / 2, 0, WH_H / 2), (T, WH_W + 2 * T, WH_H))                  # 奥のかべ
    for sy in (-1, 1): cube(wood, (WH_L / 2, sy * (WH_W / 2 + T / 2), WH_H / 2), (WH_L + 2 * T, T, WH_H))
    # 入口のかべ（x=0）：入口の穴をあける（板を貼らずに、本当に穴をあける。SKILL §2.6）
    side = (WH_W - WH_DOOR_W) / 2
    for sy in (-1, 1): cube(wood, (-T / 2, sy * (WH_DOOR_W / 2 + side / 2), WH_H / 2), (T, side, WH_H))
    cube(wood, (-T / 2, 0, (WH_DOOR_H + WH_H) / 2), (T, WH_DOOR_W, WH_H - WH_DOOR_H))
    roof = mat("e_roof", "#2A2420", rough=0.9)
    cube(roof, (WH_L / 2, 0, WH_H + 0.45), (WH_L + 0.8, WH_W + 0.8, 0.12), rot=(0, 0, 0))
    for bx in (2.0, 5.0, 8.0): cube(mat("e_beam", "#2E2620", rough=0.9), (bx, 0, WH_H - 0.12), (0.16, WH_W, 0.16))
    # 入口の上の小さなランプ（外）と、中の天井から下がるランプ
    glow = bpy.data.materials.new("e_whglow"); glow.use_nodes = True
    bb = glow.node_tree.nodes["Principled BSDF"]; bb.inputs["Emission Color"].default_value = srgb("#FFC878"); bb.inputs["Emission Strength"].default_value = 5.0
    sphere(glow, (-0.35, 0, WH_DOOR_H + 0.35), 0.09, seg=16)
    bpy.ops.object.light_add(type='POINT', location=(-0.6, 0, WH_DOOR_H + 0.3)); L = bpy.context.object
    L.data.energy = 60; L.data.color = srgb("#FFC070")[:3]; L.data.shadow_soft_size = 0.3
    for lx in (3.0, 6.0, 8.6):
        for ly in (-1.4, 1.4):
            cyl(mat("e_cord", "#151210"), (lx, ly, WH_H - 0.35), 0.01, 0.7, verts=6)
            sphere(glow, (lx, ly, WH_H - 0.72), 0.07, seg=12)
            bpy.ops.object.light_add(type='POINT', location=(lx, ly, WH_H - 0.8)); L = bpy.context.object
            L.data.energy = 55; L.data.color = srgb("#FFCF90")[:3]; L.data.shadow_soft_size = 0.35
    a = area((WH_L / 2, 0, WH_H - 0.2), (WH_L / 2, 0, 0), energy=60, size=6, col="#C9B8A0"); a.visible_camera = False


def emblem_box(loc, emb, face=1, parent=None):
    """印の付いた箱（ふたのある段ボールの色の箱。前の面に印の絵）。face＝前が向く向き（+1＝+y、−1＝−y）"""
    e = empty(loc)
    if parent is not None: e.parent = parent
    if face < 0: e.rotation_euler = (0, 0, R(180))
    cube(mat("e_box", "#B48A5A", rough=0.85), (0, 0, BOX_H / 2), (BOX_W, BOX_D, BOX_H), bevel=0.006, parent=e)
    cube(mat("e_boxlid", "#A27A4C", rough=0.85), (0, 0, BOX_H + 0.008), (BOX_W + 0.01, BOX_D + 0.01, 0.016), parent=e)
    plane(img_mat("emb_" + emb, os.path.join(TEX, emb + ".png")), (0, BOX_D / 2 + 0.002, BOX_H / 2), (0.2, 0.2), rot=(R(-90), 0, R(180)), parent=e)
    return e


def shelves(special):
    """棚 2 本（両面に箱）。special＝{(行, 段, x): 印}。ほかは emb1〜emb5 をまぜる。返す：{(行, 段, x): 箱}"""
    wood = mat("e_shelf", "#5A4632", rough=0.8)
    boxes = {}
    import random
    rnd = random.Random(1903)
    for yc in (-0.0,):
        pass
    for yb in (-2.4, 2.4, 0.0):
        d_ = 0.42 if yb != 0.0 else 0.84
        for lv in LEVELS: cube(wood, ((SHELF_X0 + SHELF_X1) / 2, yb, lv - 0.02), (SHELF_X1 - SHELF_X0, d_, 0.03))
        for xx in (SHELF_X0, (SHELF_X0 + SHELF_X1) / 2, SHELF_X1):
            cube(wood, (xx, yb, 0.85), (0.05, d_, 1.7))
    for ri, (ry, fc) in enumerate(ROWS):
        yb = -2.4 if ry < -1 else (2.4 if ry > 1 else 0.0)
        for lv in range(3):
            x = SHELF_X0 + 0.35
            while x < SHELF_X1 - 0.3:
                if abs(x - (SHELF_X0 + SHELF_X1) / 2) < 0.28: x += 0.5; continue      # まん中の柱をよける
                emb = special.get((ri, lv, round(x, 2))) or "emb%d" % rnd.randint(1, 5)
                by = yb + fc * (0.0 if yb != 0.0 else 0.21)
                boxes[(ri, lv, round(x, 2))] = emblem_box((x, by, LEVELS[lv]), emb, fc)
                x += 0.5
    return boxes


def price_tag(box, side=1):
    """値札：箱の前の右下に、ひもで下がる白い札（硬貨の絵が 1 つ。数字なし）。表を前（箱の前の向き）に。返す：札の empty"""
    e = empty((side * (BOX_W / 2 - 0.06), BOX_D / 2 + 0.02, 0.02)); e.parent = box
    cyl(mat("e_string", "#8C7A60"), (0, 0, 0.04), 0.002, 0.08, verts=6, parent=e)
    t = empty((0, 0, -0.02)); t.parent = e
    cube(mat("e_tagback", "#F2EFE6", rough=0.6), (0, 0, -0.06), (0.085, 0.004, 0.12), parent=t)
    plane(img_mat("pricetag", os.path.join(TEX, "pricetag.png")), (0, 0.0025, -0.06), (0.085, 0.12), rot=(R(90), 0, 0), parent=t)
    return e


def coin3d(loc, s=1.0):
    """硬貨（金色の平たい円柱）"""
    e = empty(loc, 0.0, s)
    cyl(mat("e_coin", "#E8B84A", rough=0.3, metal=0.9), (0, 0, 0.006), 0.045, 0.012, verts=24, parent=e)
    return e
