# 12本目（渋滞）：3D の部品（scenes.py が exec で読む。前提：KIT_HERE と TEX（絵のフォルダ）を決めてから読む）
#   まるロボ・人・材質・光・カメラは 6本目（ep06_haizen/anim/kit.py → 3本目の部品）をそのまま読み込む（17本目の kit17.py と同じ）
#   新しく作った物：大通り（片側 2 車線・歩道・街路樹・建物・街灯）・車（おじさんの水色の車は中まで。ほかの車は外だけ）・
#     スマホの台・歩道橋・感知器と張り出した柱・町の引き（道の網）・町はずれの道・地球
#   決まり：3D の中に字を書かない。まるロボは喋らない。地図の色：すいている＝緑・少しこむ＝黄・こんでいる＝赤・分からない＝灰色
#   絵コンテ表：../絵コンテ_v1.md
import os, sys, math, random
_K12 = KIT_HERE
KIT_HERE = os.path.join(_K12, "..", "..", "ep06_haizen", "anim")
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
KIT_HERE = _K12

GREEN_C, YELLOW_C, RED_C, GREY_C, WAVE_C, TEAL_C = "#34B266", "#F2C230", "#E23A30", "#9AA4B2", "#6FD0F0", "#2FD9C8"
LANE = 3.5                 # 1 車線のはば
ROAD_W = 4 * LANE          # 片側 2 車線 × 2
SIDEWALK = 3.0


def _m(name, col, **kw): return mat(name, col, **kw)


# ======================================================================== 空と光
def sky_evening():
    """夕方：だいだい色の低い太陽（西＝−x の少し北）と、うすい青紫の空"""
    world("#E9B98A", 0.9)
    bpy.ops.object.light_add(type='SUN', rotation=(R(78), 0, R(-75))); s_ = bpy.context.object
    s_.data.energy = 3.2; s_.data.color = srgb("#FFB070")[:3]; s_.data.angle = R(3)
    bpy.ops.object.light_add(type='SUN', rotation=(R(30), 0, R(120))); f_ = bpy.context.object
    f_.data.energy = 0.6; f_.data.color = srgb("#9FB0E8")[:3]
    return s_


def sky_day():
    world("#BFD8EE", 1.0)
    bpy.ops.object.light_add(type='SUN', rotation=(R(40), 0, R(35))); s_ = bpy.context.object
    s_.data.energy = 4.0; s_.data.color = srgb("#FFF4E5")[:3]; s_.data.angle = R(4)
    return s_


# ======================================================================== 道
def road_strip(c, length, axis="x", w=ROAD_W, center=(0.0, 0.0), lanes=True, name="road"):
    """まっすぐな道（アスファルト・白い線・歩道・縁石）。axis＝のびる向き。c＝(始め, 終わり) の座標"""
    asph = noise_mat(name + "_asph", "#4A4D52", "#3F4246", 9.0, 0.85)
    white = _m("lane_white", "#E8E8E4", rough=0.6); walk = noise_mat("walk", "#B9B2A6", "#A9A296", 4.0, 0.8); curb = _m("curb", "#CFCBC2", rough=0.7)
    a, b = c; mid = (a + b) / 2; L = abs(b - a)
    def P(u, v, z):      # u＝のびる向き、v＝横
        return (u, center[1] + v, z) if axis == "x" else (center[0] + v, u, z)
    def S(lu, lv, h):
        return (lu, lv, h) if axis == "x" else (lv, lu, h)
    cube(asph, P(mid, 0, -0.03), S(L, w, 0.06))
    for sg in (-1, 1):
        cube(walk, P(mid, sg * (w / 2 + SIDEWALK / 2 + 0.15), 0.07), S(L, SIDEWALK, 0.14))
        cube(curb, P(mid, sg * (w / 2 + 0.07), 0.08), S(L, 0.15, 0.16))
    if lanes:
        cube(_m("lane_yellow", "#E9C040", rough=0.6), P(mid, 0.0, 0.002), S(L, 0.15, 0.01))      # まん中の線
        for sg in (-1, 1):
            u = a
            while u < b:      # 車線の境（白い点線）
                cube(white, P(u + 1.5, sg * LANE, 0.002), S(3.0, 0.12, 0.01)); u += 8.0


def city_side(x0, x1, y_off, sgn, seed=1, axis="x", night=False):
    """道のわきの町：街路樹・街灯・低い建物（窓の列）。y_off＝道の中心から歩道の外のはしまで"""
    rnd = random.Random(seed)
    trunk = _m("trunk", "#5A4632", rough=0.9); leaf = noise_mat("leaf", "#4E8A47", "#3E7339", 3.0, 0.9)
    pole = _m("pole", "#5B6068", rough=0.4, metal=0.6); lampg = glow_mat("lampg", "#FFE2A8", 1.5 if not night else 6.0)
    cols = ["#D9CFC0", "#C9B8A2", "#B8C4CF", "#E3D9CC", "#C2B2A0", "#A9B7C2", "#D6C2A8"]
    winm = _m("bwin", "#5C6C7C", rough=0.15, metal=0.2)
    def P(u, v, z): return (u, v, z) if axis == "x" else (v, u, z)
    def S(lu, lv, h): return (lu, lv, h) if axis == "x" else (lv, lu, h)
    u = x0
    while u < x1:
        v = sgn * (y_off - 0.8)
        cyl(trunk, P(u, v, 1.0), 0.12, 2.0, verts=10)
        sphere(leaf, P(u, v, 2.6), 1.1, scale=(1, 1, 0.85), seg=12)
        u += rnd.uniform(9.0, 13.0)
    u = x0 + 5.0
    while u < x1:
        v = sgn * (y_off - 0.4)
        cyl(pole, P(u, v, 3.5), 0.07, 7.0, verts=10)
        cube(pole, P(u, v - sgn * 0.8, 7.0), S(0.15, 1.7, 0.1)); sphere(lampg, P(u, v - sgn * 1.5, 6.9), 0.2, seg=12)
        u += 26.0
    u = x0
    while u < x1:
        wb = rnd.uniform(9.0, 16.0); d_ = rnd.uniform(9.0, 14.0); h = rnd.choice([6.5, 9.5, 12.5, 15.5, 7.5])
        v = sgn * (y_off + 1.5 + d_ / 2)
        b_ = cube(_m("bld%d" % rnd.randint(0, 6), rnd.choice(cols), rough=0.85), P(u + wb / 2, v, h / 2), S(wb - 0.6, d_, h))
        for fz in range(1, int(h // 3)):       # 窓の列（道の側の面）
            cube(winm, P(u + wb / 2, sgn * (y_off + 1.47), fz * 3.0 + 0.2), S(wb - 2.0, 0.06, 1.2))
        u += wb
    return


# ======================================================================== 車
CAR_L, CAR_W = 3.9, 1.72
SEAT_TOP = 0.62            # 座席の上の面（車の床からではなく、地面から）
BOOST = 0.70               # 助手席のクッションの上（まるロボが立つ高さ）
PASS = (0.15, 0.40)        # 助手席（車の中の座標。前＝+x、左＝+y）
DRIVE = (0.15, -0.40)      # 運転席（日本の車は右）
PHONE_L = (0.95, 0.0, 1.02)   # スマホの台（前の台のまん中の上）


def _wheel(m, loc, parent):
    w_ = cyl(m, loc, 0.31, 0.22, rot=(R(90), 0, 0), parent=parent, verts=20)
    cyl(_m("hub", "#B9BEC6", rough=0.3, metal=0.8), (loc[0], loc[1] + (0.112 if loc[1] > 0 else -0.112), loc[2]), 0.16, 0.01, rot=(R(90), 0, 0), parent=parent, verts=16)
    return w_


def car(loc=(0, 0, 0), face=0.0, col="#7CC6E8", interior=False, brake=False, name="car"):
    """車（前＝+x）。interior=True はおじさんの車（窓に穴・座席・前の台・ハンドル・スマホの台）。brake＝赤いブレーキの光"""
    root = empty(loc, R(face)); root.name = name
    body = _m("cb_" + col, col, rough=0.28, coat=0.6)
    dark = _m("car_dark", "#22262C", rough=0.5); tire = _m("tire", "#1B1C1F", rough=0.8)
    glass = mat("glass", "#9CC4D8", rough=0.05, alpha=0.18) if interior else _m("glass_d", "#3B4D5C", rough=0.08, metal=0.3)
    # 下の胴（丸い箱）
    cube(body, (0, 0, 0.62), (CAR_L, CAR_W, 0.62), bevel=0.18, parent=root)
    # 上の箱（屋根と柱）
    if interior:
        cube(body, (-0.05, 0, 1.47), (2.1, CAR_W - 0.06, 0.08), bevel=0.04, parent=root)                 # 屋根
        for (px, w_) in ((0.98, 0.10), (0.02, 0.12), (-1.08, 0.18)):                                     # 前・まん中・後ろの柱
            for sg in (-1, 1):
                cube(body, (px, sg * (CAR_W / 2 - 0.06), 1.17), (w_, 0.08, 0.58), parent=root)
        cube(body, (1.05, 0, 0.97), (0.12, CAR_W - 0.06, 0.12), parent=root)                              # 前の窓の下のふち
        cube(body, (-1.13, 0, 1.17), (0.1, CAR_W - 0.1, 0.58), parent=root)                               # 後ろ（ガラスのかわりに暗い）
        plane(glass, (1.02, 0, 1.2), (0.6, CAR_W - 0.12), rot=(0, R(-62), 0), parent=root)               # 前のガラス（うすい）
        # 中
        seatm = _m("seat", "#3A3F47", rough=0.8)
        for (sx, sy) in (PASS, DRIVE):
            cube(seatm, (sx, sy, SEAT_TOP - 0.06), (0.52, 0.5, 0.12), bevel=0.04, parent=root)
            cube(seatm, (sx - 0.3, sy, SEAT_TOP + 0.33), (0.12, 0.5, 0.66), bevel=0.04, parent=root)
            cube(seatm, (sx - 0.32, sy, SEAT_TOP + 0.74), (0.12, 0.26, 0.16), bevel=0.04, parent=root)     # 頭の台
        cube(seatm, (-0.75, 0, SEAT_TOP - 0.06), (0.5, CAR_W - 0.2, 0.12), bevel=0.04, parent=root)       # 後ろの座席
        cube(seatm, (-1.0, 0, SEAT_TOP + 0.3), (0.12, CAR_W - 0.2, 0.6), bevel=0.04, parent=root)
        cube(_m("cushion", "#E07A5F", rough=0.85), (PASS[0] + 0.02, PASS[1], (SEAT_TOP + BOOST) / 2), (0.36, 0.36, BOOST - SEAT_TOP), bevel=0.03, parent=root)   # まるロボのクッション
        cube(_m("dash", "#2E333A", rough=0.6), (0.92, 0, 0.88), (0.42, CAR_W - 0.1, 0.18), bevel=0.05, parent=root)          # 前の台
        bpy.ops.mesh.primitive_torus_add(location=(0.62, DRIVE[1], 1.0), rotation=(0, R(62), 0), major_radius=0.17, minor_radius=0.022)
        wh = bpy.context.object; wh.data.materials.append(_m("wheel", "#1E2125", rough=0.5)); wh.parent = root
        cyl(_m("wheel", "#1E2125"), (0.73, DRIVE[1], 0.94), 0.03, 0.22, rot=(0, R(62), 0), parent=root, verts=10)
        # スマホの台（前の台のまん中）
        cyl(_m("holder", "#25282D", rough=0.4), (PHONE_L[0] + 0.02, 0, 0.98), 0.015, 0.08, parent=root, verts=10)
        cube(_m("holder", "#25282D"), (PHONE_L[0] + 0.03, 0, PHONE_L[2]), (0.02, 0.17, 0.09), parent=root)
    else:
        cube(dark, (-0.1, 0, 1.17), (2.0, CAR_W - 0.12, 0.5), bevel=0.12, parent=root)
        cube(body, (-0.1, 0, 1.45), (1.9, CAR_W - 0.18, 0.06), bevel=0.03, parent=root)
    for wx in (1.25, -1.25):
        for sg in (-1, 1): _wheel(tire, (wx, sg * (CAR_W / 2 - 0.08), 0.31), root)
    hl = glow_mat("headl", "#FFF6DA", 1.2)
    for sg in (-1, 1):
        sphere(hl, (CAR_L / 2 - 0.02, sg * 0.6, 0.72), 0.09, scale=(0.4, 1.2, 0.8), parent=root, seg=12)
    tl = glow_mat("tail_on" if brake else "tail_off", "#FF2A1F", 7.0 if brake else 0.6)
    tails = []
    for sg in (-1, 1):
        tails.append(cube(tl, (-CAR_L / 2 + 0.01, sg * 0.65, 0.78), (0.04, 0.26, 0.12), parent=root))
    root["tails"] = [t.name for t in tails]
    return root


# 5本目（ep05_vacuum/anim/kit.py）から写した：画面が時刻で替わるスマホ
def phone_seq(loc, rot_z, states, glow=2.2, fade=0.15):
    """画面が時刻で替わるスマホ（2026-11-14：大きな 2D のスマホの絵をやめ、3D のスマホに寄る。ep02「急にチープ、3D に」）。
    states：[(時刻, 絵のファイル), …]（最初の時刻は使わない＝はじめの絵）。替わるときは fade 秒で溶かす"""
    e = empty(loc, R(rot_z))
    cube(mat("ph_body", "#1D2126", rough=0.3, metal=0.4), (0, 0, 0.004), (0.078, 0.158, 0.008), bevel=0.006, parent=e)
    cube(mat("ph_edge", "#8A9099", rough=0.25, metal=0.9), (0, 0, 0.004), (0.0795, 0.1595, 0.006), bevel=0.006, parent=e)
    cyl(mat("ph_cam", "#0B0E12", rough=0.1, coat=1.0), (0, 0.068, 0.0088), 0.0035, 0.001, parent=e, verts=16)
    m = bpy.data.materials.new("ph_seq"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    imgs = {}
    def tex_node(path):
        t = nt.nodes.new("ShaderNodeTexImage")
        if path not in imgs: imgs[path] = bpy.data.images.load(path)
        t.image = imgs[path]; return t
    col = tex_node(states[0][1]).outputs["Color"]
    for (t, path) in states[1:]:
        tn = tex_node(path); mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
        nt.links.new(col, mx.inputs[6]); nt.links.new(tn.outputs["Color"], mx.inputs[7])
        fi = mx.inputs["Factor"]
        fi.default_value = 0.0; fi.keyframe_insert("default_value", frame=f(t - fade))
        fi.default_value = 1.0; fi.keyframe_insert("default_value", frame=f(t))
        col = mx.outputs[2]
    nt.links.new(col, b.inputs["Base Color"]); nt.links.new(col, b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = glow; b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Specular IOR Level"].default_value = 0.2
    sc = plane(m, (0, 0, 0.0086), (0.07, 0.15), parent=e)
    return e, sc


def phone_on_holder(parent, states, glow=1.6):
    """前の台のスマホ（横向き。画面は後ろ＝−x を向く）。states は phone_seq と同じ（時刻, 絵）"""
    e_, scr = phone_seq((0, 0, 0), 0.0, states, glow=glow)
    e_.parent = parent; e_.location = PHONE_L; e_.rotation_euler = (0, R(-80), R(90)); e_.scale = (1.15, 1.15, 1.15)
    return e_, scr


def ojisan(parent):
    """運転席のおじさん（前を向いたまま。腕はハンドルへ）。前＝+x"""
    p = person((DRIVE[0] - 0.05, DRIVE[1], SEAT_TOP - 0.55), face_deg=90, shirt="#8A6A4A", pants="#3B4450", hair="#9A9590", sit=True)
    p.parent = parent
    sm = _m("shirt#8A6A4A", "#8A6A4A", rough=0.7); km = _m("skin", "#F1C7A5", rough=0.55)
    head = [c for c in p.children if c.type == 'EMPTY'][0]
    gl = _m("glasses", "#2A2A2E", rough=0.3, metal=0.5)
    for sg in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(location=(0.19, sg * 0.07, 0.02), rotation=(0, R(90), 0), major_radius=0.045, minor_radius=0.007)
        g_ = bpy.context.object; g_.data.materials.append(gl); g_.parent = head
        # 腕：肩からハンドルへ
        sx, sy, sz = DRIVE[0] - 0.05, DRIVE[1] + sg * 0.2, SEAT_TOP - 0.55 + 0.85 + 0.25
        hx, hy, hz = 0.6, DRIVE[1] + sg * 0.15, 1.02
        dx, dy, dz = hx - sx, hy - sy, hz - sz; L_ = math.sqrt(dx * dx + dy * dy + dz * dz)
        a_ = cyl(sm, ((sx + hx) / 2, (sy + hy) / 2, (sz + hz) / 2), 0.05, L_, verts=12)
        a_.rotation_euler = (0, math.atan2(math.sqrt(dx * dx + dy * dy), dz), math.atan2(dy, dx)); a_.parent = parent
        sphere(km, (hx, hy, hz), 0.05, parent=parent, seg=12)
    return p, head


# ======================================================================== 歩道橋と感知器
def overpass(x=0.0, h=5.0, span=ROAD_W + 2 * SIDEWALK + 2.0, w=2.6):
    """道（+x へ）をまたぐ歩道橋。上の面は z=h。手すりは格子（すき間から下が見える）"""
    deck = _m("deck", "#8D949C", rough=0.7); railm = _m("rail", "#3E6F9E", rough=0.4, metal=0.5); colm = _m("col", "#9AA0A7", rough=0.6)
    cube(deck, (x, 0, h - 0.15), (w, span + 8.0, 0.3))
    cube(_m("deck_top", "#A8705A", rough=0.9), (x, 0, h + 0.005), (w - 0.1, span + 8.0, 0.01))
    for sx in (-1, 1):
        xx = x + sx * (w / 2 - 0.05)
        cube(railm, (xx, 0, h + 1.05), (0.07, span + 8.0, 0.07))
        cube(railm, (xx, 0, h + 0.12), (0.07, span + 8.0, 0.05))
        y = -(span + 8.0) / 2
        while y < (span + 8.0) / 2:
            cube(railm, (xx, y, h + 0.58), (0.03, 0.03, 0.95)); y += 0.16
    for sy in (-1, 1):
        cube(colm, (x, sy * (ROAD_W / 2 + SIDEWALK + 0.6), h / 2), (0.5, 0.5, h))
        # 階段（端の外へ下りる）
        for k in range(14):
            cube(deck, (x, sy * ((span + 8.0) / 2 + 0.2 + k * 0.3), h - (k + 1) * h / 14 + 0.1), (w, 0.32, 0.2))


SENSOR_X = 14.0


def gantry(x=SENSOR_X, lane_y=LANE * 1.5):
    """道の上に張り出した L 字の柱と、四角い感知器（下に丸い目）。lane_y＝感知器の真下の車線のまん中"""
    pm = _m("gpole", "#7A8088", rough=0.4, metal=0.6)
    py = ROAD_W / 2 + 0.8
    cyl(pm, (x, py, 3.4), 0.14, 6.8, verts=16)
    cube(pm, (x, (py + lane_y - 0.8) / 2, 6.75), (0.18, py - lane_y + 1.2, 0.18))
    box = cube(_m("sensor", "#C9CDD3", rough=0.5, metal=0.2), (x, lane_y, 6.45), (0.5, 0.42, 0.42), bevel=0.04)
    eye = cyl(_m("sensor_eye", "#1E2328", rough=0.1, coat=1.0), (x, lane_y, 6.22), 0.13, 0.06, verts=24)
    return box, eye


_CAR_CACHE = {}


def car_fast(loc=(0, 0, 0), face=0.0, col="#7CC6E8", brake=False, name="car"):
    """外だけの車を、1 つの形にまとめて写して使う（色とブレーキの光ごとに 1 回だけ作る。たくさん並べても速い）"""
    k_ = (col, brake)
    if k_ not in _CAR_CACHE:
        r_ = car((0, 0, -500.0), 0.0, col, interior=False, brake=brake, name="tpl")
        bpy.context.view_layer.update()
        kids = list(r_.children_recursive)
        bpy.ops.object.select_all(action='DESELECT')
        for o in kids:
            o.select_set(True)
        bpy.context.view_layer.objects.active = kids[0]
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.join()
        tpl = bpy.context.view_layer.objects.active; tpl.name = "tpl_%s_%d" % (col, brake)
        me = tpl.data
        me.transform(mathutils.Matrix.Translation((0, 0, 500.0)) @ tpl.matrix_world)   # 形を原点（地面）にもどす
        tpl.matrix_world = mathutils.Matrix.Identity(4)
        bpy.data.objects.remove(r_)
        tpl.hide_render = True; tpl.hide_viewport = True
        _CAR_CACHE[k_] = tpl
    o = _CAR_CACHE[k_].copy(); o.hide_render = False; o.hide_viewport = False
    bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, R(face)); o.name = name
    return o


# ======================================================================== ほかの車の流れ
CAR_COLS =["#E8E8E8", "#2B2F36", "#C8312B", "#3F6FB5", "#9AA3AD", "#F2F0EA", "#5A7F5A", "#D9A441", "#7A3F8F"]


def traffic(lanes, t0, t1, x0, x1, speed, gap, seed=3, axis="x", fixed_y=None):
    """流れる車：lanes＝[(横の位置, 向き ±1)]。t0〜t1 のあいだ、gap 秒ごとに車が x0→x1 を走る（向き −1 は逆）"""
    rnd = random.Random(seed); cars = []
    span = abs(x1 - x0); dur = span / speed
    for (ly, dr) in lanes:
        t = t0 - dur + rnd.uniform(0, gap)
        while t < t1:
            c_ = car_fast((0, 0, 0), 0.0 if dr > 0 else 180.0, rnd.choice(CAR_COLS), name="tr")
            a, b = (x0, x1) if dr > 0 else (x1, x0)
            def P(u): return (u, ly, 0.0) if axis == "x" else (ly, u, 0.0)
            if axis != "x": c_.rotation_euler = (0, 0, R(90 if dr > 0 else -90))
            key(c_, "location", t, P(a), "LINEAR"); key(c_, "location", t + dur, P(b), "LINEAR")
            hide_key(c_, -100.0, True); hide_key(c_, t, False); hide_key(c_, t + dur, True)
            cars.append((c_, t, t + dur, ly, dr))
            t += gap * rnd.uniform(0.7, 1.4)
    return cars


# ======================================================================== 町の引き（道の網）
def town_grid(n=9, block=60.0, seed=5, glow_lines=False):
    """上から見た町：道の網（大きな道は太く）とブロックの建物。まん中は (0,0)。はしに川と橋・山とトンネル"""
    rnd = random.Random(seed)
    asph = _m("t_asph", "#55595F", rough=0.85); big = _m("t_big", "#4A4E54", rough=0.8)
    grass = noise_mat("t_grass", "#8DB27A", "#7DA06B", 0.2, 0.95)
    half = n * block / 2
    cube(grass, (0, 0, -0.1), (n * block + 200, n * block + 200, 0.1))
    roads = []
    for k in range(n + 1):
        u = -half + k * block; wide = (k % 3 == 0)
        ww = 14.0 if wide else 6.0
        cube(big if wide else asph, (u, 0, 0.02), (ww, n * block, 0.04)); roads.append(("y", u, ww))
        cube(big if wide else asph, (0, u, 0.02), (n * block, ww, 0.04)); roads.append(("x", u, ww))
    cols = ["#D9CFC0", "#C9B8A2", "#B8C4CF", "#E3D9CC", "#C2B2A0", "#A9B7C2"]
    for i in range(n):
        for j in range(n):
            cx = -half + (i + 0.5) * block; cy = -half + (j + 0.5) * block
            if (i, j) in ((n - 1, 2), (n - 1, 3)): continue     # 川のそば
            for _ in range(rnd.randint(2, 4)):
                bw = rnd.uniform(12, 22); bd = rnd.uniform(12, 22); bh = rnd.uniform(6, 30) * (1.4 if abs(i - n // 2) + abs(j - n // 2) < 3 else 0.7)
                cube(_m("tb%d" % rnd.randint(0, 5), rnd.choice(cols), rough=0.85), (cx + rnd.uniform(-12, 12), cy + rnd.uniform(-12, 12), bh / 2), (bw, bd, bh))
    # 川と橋（東のはし）・山とトンネル（北のはし）
    water = _m("water", "#4F86B8", rough=0.1)
    cube(water, (half + 30, 0, 0.0), (26, n * block + 200, 0.05))
    br_ = cube(_m("bridge", "#A9AEB5", rough=0.6), (half + 30, -half + 3 * block, 1.2), (34, 9, 0.8)); br_.name = "bridge"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=70, location=(0, half + 80, -25), segments=24, ring_count=12)
    hill = bpy.context.object; hill.scale = (2.2, 1.0, 0.9); hill.data.materials.append(noise_mat("hill", "#5E8A55", "#4E7A47", 0.05, 0.95))
    tn_ = cube(_m("tunnel", "#1B1D20", rough=0.9), (-half + 6 * block, half + 12, 3.0), (10, 2, 6)); tn_.name = "tunnel"
    return roads, half


# ======================================================================== 町はずれの道
def field_road():
    sky_day()
    asph = noise_mat("f_asph", "#55585C", "#4A4D51", 9.0, 0.85)
    cube(asph, (0, 0, -0.03), (400, 7.0, 0.06))
    cube(_m("lane_white", "#E8E8E4"), (0, 3.3, 0.002), (400, 0.12, 0.01)); cube(_m("lane_white", "#E8E8E4"), (0, -3.3, 0.002), (400, 0.12, 0.01))
    u = -200.0
    while u < 200:
        cube(_m("lane_white", "#E8E8E4"), (u, 0, 0.002), (3.0, 0.12, 0.01)); u += 8.0
    for sg in (-1, 1):
        cube(noise_mat("bank", "#8FA868", "#7F985A", 1.0, 0.95), (0, sg * 6.0, -0.1), (400, 5.0, 0.3))
        cube(noise_mat("field%d" % sg, "#9DBB62" if sg > 0 else "#B7A35A", "#8CA955", 0.6, 0.95), (0, sg * 40.0, -0.25), (400, 60.0, 0.1))
    pm = _m("upole", "#6E5A46", rough=0.9); wire = _m("wire", "#222222", rough=0.6)
    for k in range(-6, 7):
        cyl(pm, (k * 30.0, 4.8, 4.5), 0.13, 9.0, verts=10)
    cyl(wire, (0, 4.8, 8.6), 0.012, 400, rot=(0, R(90), 0), verts=6)
    cyl(wire, (0, 4.8, 8.2), 0.012, 400, rot=(0, R(90), 0), verts=6)
    for k in range(5):      # 遠くの山
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=90 + k * 10, depth=40 + k * 8, location=(-150 + k * 80, 260 + k * 20, 10))
        c_ = bpy.context.object; c_.data.materials.append(noise_mat("mount", "#7E9A86", "#6F8B78", 0.02, 0.95))


# ======================================================================== 地球
def globe(loc=(0, 0, 0), r=3.0):
    sea = _m("sea", "#3F79C2", rough=0.35); land = _m("land", "#6FA86A", rough=0.8)
    g = sphere(sea, loc, r, seg=48)
    rnd = random.Random(9)
    for _ in range(14):
        th = rnd.uniform(0, 2 * math.pi); ph = rnd.uniform(-1.0, 1.0)
        p = (loc[0] + r * math.cos(ph) * math.cos(th), loc[1] + r * math.cos(ph) * math.sin(th), loc[2] + r * math.sin(ph))
        sphere(land, p, rnd.uniform(0.5, 1.2), scale=(1, 1, 0.35), seg=16).rotation_euler = (0, math.pi / 2 - ph, th)
    return g
