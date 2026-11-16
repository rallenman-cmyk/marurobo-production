# 3本目：作り込んだ舞台（2026-11-16 ユーザー「電車の中がチープすぎる、冒頭まし維持率気になる」・ほかの回の「チープ感」の直しの横展開）
#   scenes_all.py が common.py のあとで exec する。部品（cube・sphere・mat など）は storyboard の scenes.py / board.py のもの
#   決まり：3D の中に字を書かない。テントの絵の広告は 3 枚のまま（11:06「何枚あったでしょう」の答え）・場所も変えない
import bmesh


def tex_mat(name, c1, c2, scale=8.0, rough=0.6, bump=0.0, metal=0.0, coat=0.0):
    """色に細かいむらのある材質（のっぺりした一色をやめる）"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeNewGeometry")
    tx = nt.nodes.new("ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = scale; tx.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Position"], tx.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = srgb(c1); ramp.color_ramp.elements[1].color = srgb(c2)
    nt.links.new(tx.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if coat: b.inputs["Coat Weight"].default_value = coat
    if bump:
        bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump
        nt.links.new(tx.outputs["Fac"], bn.inputs["Height"]); nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


def sky_mat(name, bottom, top, strength=1.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = srgb(bottom); ramp.color_ramp.elements[1].color = srgb(top)
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def link_copy(src, loc, scale=None):
    o = src.copy(); bpy.context.collection.objects.link(o); o.location = loc
    if scale: o.scale = scale
    return o


# ---------------------------------------------------------------- 電車の中
TRAIN_WIN_X = (-3.6, -1.2, 1.2, 3.6)
TRAIN_WIN_W, TRAIN_WIN_Z0, TRAIN_WIN_Z1 = 1.62, 1.12, 2.02
TRAIN_WALL_Y = 1.6


def train_outside(speed=2.2):
    """窓の外：空・遠くの山・流れていく紅葉の並木・電柱。並木と電柱は左へ流れる（電車が走っている）"""
    sky = cube(sky_mat("tr_sky", "#FFF1D6", "#7FB6E6", 1.5), (0, 14.0, 2.5), (60, 0.05, 14)); sky.visible_shadow = False
    hills = [mat("tr_hill%d" % i, c, rough=0.9) for i, c in enumerate(("#B98A4E", "#A6713E", "#C29A5A"))]   # 秋の山
    random.seed(31)
    for k in range(9):                                                   # 遠くの山（動かない）
        x = -24 + k * 6 + random.uniform(-1, 1)
        sphere(hills[k % 3], (x, 12.0, -0.6), random.uniform(3.5, 5.5), scale=(1.6, 0.3, 0.7), seg=24).visible_shadow = False
    cube(tex_mat("tr_field", "#C9B37A", "#A99560", 0.6, rough=0.9), (0, 7.5, 0.35), (80, 12, 0.05)).visible_shadow = False
    mover = empty((0, 0, 0)); mover.name = "外の景色"
    # 動きはクリップの頭ではなく、十分前と十分あとに置く（7本目「動きの鍵を CLOCK の頭に置かない」）
    key(mover, "location", -400, (0.0, 0, 0), "LINEAR"); key(mover, "location", 3400, (-speed * 3800 / 24, 0, 0), "LINEAR")
    trunk = mat("tr_trunk", "#5B3E28", rough=0.8)
    leaves = [mat("tr_leaf%d" % i, c, rough=0.75, emit=0.2) for i, c in enumerate(("#E0301E", "#F5A623", "#C2410C", "#E86A2C", "#D9B23A", "#8FA34A"))]
    # 木 1 本＝幹＋小さな葉のかたまり 3 つ。同じ形を並べる（速い）。窓の上半分には空と山が見えるように、低めに置く
    t_src = cyl(trunk, (0, 0, 0), 0.05, 1.0, verts=8)
    l_src = [sphere(lm, (0, 0, 0), 0.36, scale=(1, 0.9, 1.05), seg=12) for lm in leaves]
    span_x = speed * 3800 / 24 + 30
    for yy, s_, step, zb in ((4.6, 0.85, 1.5, 0.45), (7.4, 1.1, 1.8, 0.55)):
        x = -16.0; i = 0
        while x < span_x:
            xx = x + random.uniform(-0.3, 0.3); h = random.uniform(0.85, 1.25) * s_
            t = link_copy(t_src, (xx, yy, zb + 0.5 * h), (s_, s_, h)); t.parent = mover; t.visible_shadow = False
            pal = random.choice(((0, 2, 3), (1, 4, 3), (0, 3, 1), (2, 0, 4), (5, 1, 4)))
            for (dx, dz, k) in ((-0.22, 0.0, 0), (0.22, 0.05, 1), (0.0, 0.32, 2)):
                l = link_copy(l_src[pal[k]], (xx + dx * s_, yy + random.uniform(-0.1, 0.1), zb + h + dz * s_), (s_, s_, s_)); l.parent = mover; l.visible_shadow = False
            x += step * random.uniform(0.75, 1.25); i += 1
    hedge = tex_mat("tr_hedge", "#7E9A4E", "#6A8540", 3.0, rough=0.9)
    cube(hedge, (span_x / 2 - 20, 3.4, 0.55), (span_x + 40, 0.5, 0.45)).parent = mover          # 線路ぎわの草の土手
    pole_m = mat("tr_pole", "#7A7D80", rough=0.5, metal=0.4)
    p_src = cyl(pole_m, (0, 0, 0), 0.06, 4.2, verts=10)
    x = -12.0
    while x < span_x:                                                    # 電柱（手前・速く見える）
        p = link_copy(p_src, (x, 2.9, 1.4)); p.parent = mover; p.visible_shadow = False
        x += 9.0
    for o in [t_src, p_src] + l_src: o.location = (0, 0, -50)            # 元の形は見えない所へ


def train_wall():
    """窓のある奥の壁（窓は本当に穴）。腰の板・窓の間の柱・窓の上の帯・アルミの窓わく"""
    Y, T = TRAIN_WALL_Y, 0.08
    panel = tex_mat("tr_panel", "#ECE8DF", "#E2DDD2", 3.0, rough=0.55)
    trim = mat("tr_trim", "#C9CED3", rough=0.3, metal=0.6)
    frame = mat("tr_frame", "#B9BEC4", rough=0.25, metal=0.85)
    X0, X1 = -6.0, 6.0
    cube(panel, (0, Y, TRAIN_WIN_Z0 / 2), (X1 - X0, T, TRAIN_WIN_Z0))                         # 窓の下
    cube(panel, (0, Y, (TRAIN_WIN_Z1 + 2.62) / 2), (X1 - X0, T, 2.62 - TRAIN_WIN_Z1))          # 窓の上
    edges = [X0] + [v for x in TRAIN_WIN_X for v in (x - TRAIN_WIN_W / 2, x + TRAIN_WIN_W / 2)] + [X1]
    for a, b in zip(edges[0::2], edges[1::2]):                                                 # 窓の間の柱
        cube(panel, ((a + b) / 2, Y, (TRAIN_WIN_Z0 + TRAIN_WIN_Z1) / 2), (b - a, T, TRAIN_WIN_Z1 - TRAIN_WIN_Z0))
    for x in TRAIN_WIN_X:                                                                      # アルミの窓わく（丸い角）・真ん中の桟
        W, H, zc = TRAIN_WIN_W, TRAIN_WIN_Z1 - TRAIN_WIN_Z0, (TRAIN_WIN_Z0 + TRAIN_WIN_Z1) / 2
        for (dx, dz, sx, sz) in ((0, H / 2, W + 0.06, 0.05), (0, -H / 2, W + 0.06, 0.07), (-W / 2, 0, 0.05, H), (W / 2, 0, 0.05, H)):
            cube(frame, (x + dx, Y - 0.05, zc + dz), (sx, 0.06, sz), bevel=0.015)
        cube(frame, (x, Y - 0.03, zc + 0.12), (0.035, 0.04, H - 0.04), bevel=0.01)          # 縦の桟（2 枚の窓）
        cube(mat("tr_blind", "#E9E4D6", rough=0.7), (x, Y - 0.07, TRAIN_WIN_Z1 - 0.03), (W - 0.02, 0.05, 0.07), bevel=0.01)  # 巻き上げた日よけ
    cube(trim, (0, Y - 0.05, TRAIN_WIN_Z0 - 0.06), (X1 - X0, 0.08, 0.04), bevel=0.01)        # 窓の下の手すりの帯
    for s_ in (-1, 1):                                                                         # 車両のはしの壁と、となりの車両への扉（窓つき）
        cube(panel, (s_ * 6.0, 0, 1.33), (0.08, 3.3, 2.66))
        cube(mat("tr_gangway", "#C3C8CD", rough=0.3, metal=0.7), (s_ * 5.95, 0, 1.0), (0.04, 0.95, 2.0), bevel=0.02)
        cube(mat("tr_gwin", "#2A3340", rough=0.1, coat=1.0), (s_ * 5.92, 0, 1.45), (0.01, 0.55, 0.8))
    # 窓の上の広告わく（テントの絵ではない。色と形だけ・字なし）
    random.seed(7)
    adcols = ["#F2D6A2", "#B9D8EE", "#F4C2CF", "#CFE5BE", "#E8E0F5"]
    for k, x in enumerate((-4.8, -2.4, 0.0, 2.4, 4.8)):
        cube(frame, (x, Y - 0.05, 2.32), (1.5, 0.03, 0.42), bevel=0.01)
        cube(mat("tr_wad%d" % k, adcols[k], rough=0.6, emit=0.15), (x, Y - 0.068, 2.32), (1.42, 0.01, 0.34))
        cube(mat("tr_wads%d" % k, ("#E07A3A", "#2F6FA8", "#C24B6E", "#4F8C3A", "#7A5BB8")[k], rough=0.6), (x - 0.4, Y - 0.074, 2.32), (0.3, 0.01, 0.22))


def train_seat():
    """長い座席：区切りのあるクッション・背もたれ・ステンレスの仕切り・座席の下の暖房の板。人とまるロボの座る高さ（0.51）は前のまま"""
    moq = tex_mat("tr_moquette", "#3B6C9C", "#2F5B86", 40.0, rough=0.95, bump=0.15)
    edge = mat("tr_steel", "#D3D7DB", rough=0.18, metal=0.95)
    dark = tex_mat("tr_under", "#4A4E54", "#3E4247", 20.0, rough=0.6)
    X0, X1 = -4.45, 4.45
    n = 7; w = (X1 - X0) / n
    for k in range(n):                                                        # 座面（7 人がけ・区切りのくぼみ）
        x = X0 + w * (k + 0.5)
        cube(moq, (x, 1.2, 0.44), (w - 0.025, 0.6, 0.15), bevel=0.05)
        cube(moq, (x, 1.47, 0.83), (w - 0.025, 0.13, 0.56), bevel=0.05)
    cube(dark, (0, 1.25, 0.18), (X1 - X0, 0.5, 0.36))                         # 座席の下
    for x in (X0 + 0.25 + i * 0.5 for i in range(int((X1 - X0) / 0.5))):    # 暖房のすき間
        cube(mat("tr_grill", "#2C2F33", rough=0.6), (x, 0.995, 0.18), (0.36, 0.01, 0.02))
    for s_ in (-1, 1):                                                        # 端の仕切り（板と曲げたパイプ）
        xe = s_ * (X1 + 0.06)
        cube(mat("tr_partition", "#CFD6DC", rough=0.35, metal=0.2, trans=0.0), (xe, 1.15, 0.95), (0.03, 0.72, 0.95), bevel=0.02)
        cyl(edge, (xe, 0.8, 1.1), 0.022, 2.2, verts=16)                       # 縦の手すり（床から網棚まで）
        cyl(edge, (xe, 1.15, 1.45), 0.02, 0.72, rot=(R(90), 0, 0), verts=16)
    for x in (-1.6, 1.6):                                                     # 途中の縦の手すり（人の間をふさがない所）
        cyl(edge, (x, 0.98, 1.3), 0.02, 1.62, verts=16)


def train_ceiling():
    """網棚・天井（なだらかな曲面）・照明の帯・冷房の吹き出し・つり革"""
    steel = mat("tr_steel2", "#C8CDD2", rough=0.2, metal=0.9)
    for y in (1.12, 1.26, 1.4):                                               # 網棚の棒
        cyl(steel, (0, y, 2.08), 0.012, 9.6, rot=(0, R(90), 0), verts=10)
    for x in [i * 1.2 - 4.8 for i in range(9)]:                               # 網棚の受け
        cube(steel, (x, 1.34, 2.1), (0.03, 0.5, 0.03), bevel=0.008)
    ceil = tex_mat("tr_ceil", "#F4F2EE", "#EAE7E1", 2.0, rough=0.6)
    cube(ceil, (0, 0, 2.7), (12, 3.4, 0.08))
    for s_ in (-1, 1):                                                        # 天井の端の斜めの板
        cube(ceil, (0, s_ * 1.42, 2.58), (12, 0.5, 0.06), rot=(R(-s_ * 28), 0, 0))
    lightm = mat("tr_lamp", "#FFFFFF", rough=0.3, emit=6.0)
    for s_ in (-1, 1):                                                        # 照明の帯（光る）
        for k in range(6):
            cube(lightm, (-5.0 + k * 2.0, s_ * 0.62, 2.64), (1.7, 0.14, 0.02))
    cube(mat("tr_duct", "#E4E1DB", rough=0.5), (0, 0, 2.63), (12, 0.6, 0.06), bevel=0.02)  # 冷房の通り道
    for k in range(5):
        cube(mat("tr_vent", "#B5B9BE", rough=0.4, metal=0.4), (-4.0 + k * 2.0, 0, 2.598), (0.5, 0.4, 0.01))
    rail = mat("tr_rail", "#C9CDD1", metal=0.9, rough=0.2)
    strap = mat("tr_strap", "#F2F2F2", rough=0.4)
    band = mat("tr_strapband", "#E8C547", rough=0.5)
    for y in (-0.9, 0.86):                                                    # つり革（手前と奥）
        cyl(rail, (0, y, 2.22), 0.022, 11, rot=(0, R(90), 0), verts=16)
        for x in (-4.5, -3.5, -2.5, -1.5, 1.5, 2.5, 3.5, 4.5):
            cube(band, (x, y, 2.07), (0.03, 0.012, 0.26))
            add(bpy.ops.mesh.primitive_torus_add, strap, (x, y, 1.9), (R(90), 0, 0), major_radius=0.075, minor_radius=0.014)


def train_doors():
    """車両の両はしの扉（窓つき・ステンレス）"""
    st = tex_mat("tr_door", "#C3C8CD", "#B5BAC0", 6.0, rough=0.3, metal=0.75)
    for s_ in (-1, 1):
        x = s_ * 5.3
        for dx in (-0.33, 0.33):
            cube(st, (x + dx, TRAIN_WALL_Y - 0.02, 1.05), (0.64, 0.05, 2.1), bevel=0.02)
            cube(sky_mat("tr_dsky", "#FFF1D6", "#8FC0EA", 1.2), (x + dx, TRAIN_WALL_Y - 0.05, 1.45), (0.42, 0.01, 0.75))
        cube(mat("tr_dfloor", "#E7C64A", rough=0.6), (x, 1.2, 0.006), (1.3, 0.5, 0.01))  # 扉の前の黄色い線


def train_floor():
    fl = tex_mat("tr_floor", "#9C988F", "#8C877E", 25.0, rough=0.7, bump=0.08)
    cube(fl, (0, 0, -0.02), (12, 3.3, 0.04))
    cube(tex_mat("tr_floor2", "#7F7B73", "#737069", 25.0, rough=0.7), (0, 1.05, 0.001), (9.0, 0.22, 0.004))


def train_rich(wifi=True, tents=(-2.8, 0.0, 2.8)):
    """電車の中をまとめて作る。人（ハルさん・ソラさん）とつり広告（テント 3 枚）は前と同じ場所"""
    world("#F2E6D2", 0.5)
    train_floor(); train_wall(); train_seat(); train_ceiling(); train_doors(); train_outside()
    cube(mat("tr_frontwall", "#ECE8DF", rough=0.6), (0, -1.6, 1.3), (12, 0.08, 2.6))
    # つり広告（テントの絵が 3 枚。ほかは色だけ）：場所・大きさは前と同じ
    tent = img_mat("tentposter", os.path.join(HERE, "tent.png"), emit=0.6)
    others = ["#9BC4E2", "#F6B8C8", "#C9E4B4", "#FFE3A3"]
    xs = [-4.2, -2.8, -1.4, 0.0, 1.4, 2.8, 4.2]
    tent_at = set(tents)
    wire = mat("wire", "#888888", metal=0.8, rough=0.3)
    for i, x in enumerate(xs):
        y = 0.25
        cyl(wire, (x - 0.24, y, 2.47), 0.006, 0.36, verts=8); cyl(wire, (x + 0.24, y, 2.47), 0.006, 0.36, verts=8)
        cube(mat("tr_adbar", "#D5D9DD", metal=0.7, rough=0.3), (x, y, 2.37), (0.64, 0.025, 0.025))
        m = tent if x in tent_at else mat("adc" + str(i), others[i % 4], rough=0.6, emit=0.4)
        plane(m, (x, y, 1.95), (0.6, 0.8), rot=(math.radians(90), 0, 0))
    person((-0.9, 1.15, 0), face_deg=180, shirt="#4E8FC7", hair="#2B2220", head_down=5)
    person((0.9, 1.15, 0), face_deg=180, shirt="#E58C5A", hair="#6A4A3A", phone=True, head_down=30)
    if wifi:
        cube(mat("wifi_box", "#F4F4F4", rough=0.4), (0, 0.6, 2.56), (0.5, 0.3, 0.1), bevel=0.03)
    # 光：窓から差しこむ日の光（床と座席に窓の形の明るい所）・天井の照明・やわらかい明るさ
    sun((-58, 0, 12), 3.2, "#FFE7C2", angle=3)
    area((0, -1.0, 2.5), (0, 0.5, 1), 260, 4, "#FFF6E8", shape='RECTANGLE')
    area((0, 0.0, 2.55), (0, 0, 0), 180, 6, "#FFFFFF", shape='RECTANGLE')


# ---------------------------------------------------------------- 部屋（和室）
#   v8：一色の床・平らな壁をやめる。畳・柱・ふすま・本当に穴のあいた窓（夜は月と星、昼は空と木）・あんどん・ちゃぶ台・本棚・植木
#   ふとん・枕・帽子かけの場所は前と同じ（まるロボが歩く道：x -1.6〜1.75・y -1.6〜1.4 はふさがない）
def tatami_mat(name="tatami"):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 60.0; wv.inputs["Distortion"].default_value = 0.4
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = srgb("#C9C08A"); ramp.color_ramp.elements[1].color = srgb("#B5AC74")
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.75
    bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = 0.12
    nt.links.new(wv.outputs["Fac"], bn.inputs["Height"]); nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


def room_rich(night=True, hook_hat=False):
    world("#0C1426", 0.12) if night else world("#F3E6D2", 0.6)
    X0, X1, Y0, Y1 = -3.2, 3.2, -3.6, 2.0
    cube(mat("under_floor", "#3A3226"), (0, -0.8, -0.03), (8, 7, 0.04))
    tm = tatami_mat(); heri = mat("heri", "#2E3A2F", rough=0.6)
    # 畳（0.9×1.8）：向きを交互に
    for i, x in enumerate([X0 + 0.9 * k + 0.45 for k in range(7)]):
        for j, y in enumerate([Y1 - 1.8 * k - 0.9 for k in range(3)]):
            if (i + j) % 2 == 0:
                o = cube(tm, (x, y, 0.012), (0.88, 1.78, 0.024), bevel=0.006)
                for dx in (-0.435, 0.435): cube(heri, (x + dx, y, 0.026), (0.03, 1.78, 0.006))
            else:
                for dy in (-0.45, 0.45):
                    o = cube(tm, (x, y + dy, 0.012), (0.88, 0.88, 0.024), bevel=0.006); o.rotation_euler[2] = R(90)
                    for dd in (-0.435, 0.435): cube(heri, (x, y + dy + dd, 0.026), (0.88, 0.03, 0.006))
    plaster = tex_mat("plaster", "#D9CDB4" if not night else "#C9BEA6", "#CFC2A6", 4.0, rough=0.9, bump=0.05)
    wood = tex_mat("hashira", "#8A6440", "#7A5636", 12.0, rough=0.5)
    W_X, W_Z0, W_Z1, W_W = -1.95, 0.85, 1.75, 1.3                       # 窓
    def wallY(xa, xb, za, zb): cube(plaster, ((xa + xb) / 2, Y1 + 0.05, (za + zb) / 2), (xb - xa, 0.1, zb - za))
    wallY(X0, W_X - W_W / 2, 0, 2.5); wallY(W_X + W_W / 2, -0.9, 0, 2.5)
    wallY(W_X - W_W / 2, W_X + W_W / 2, 0, W_Z0); wallY(W_X - W_W / 2, W_X + W_W / 2, W_Z1, 2.5)
    # ふすま（右）：x -0.9〜3.2
    fus = tex_mat("fusuma", "#EFE6D2", "#E3D7BE", 5.0, rough=0.85)
    for k in range(4):
        x = -0.9 + 0.775 * (k + 0.5)
        cube(fus, (x, Y1 + 0.03, 0.95), (0.76, 0.06, 1.9))
        for zz in (0.02, 1.88): cube(wood, (x, Y1 - 0.005, zz), (0.76, 0.03, 0.04))
        for xx in (-0.37, 0.37): cube(wood, (x + xx, Y1 - 0.005, 0.95), (0.03, 0.03, 1.9))
        cyl(mat("hikite", "#3B2F26", rough=0.4, metal=0.5), (x + (0.28 if k % 2 == 0 else -0.28), Y1 - 0.005, 0.95), 0.03, 0.01, rot=(R(90), 0, 0), verts=16)
    cube(plaster, (1.15, Y1 + 0.05, 2.2), (4.1, 0.1, 0.6))
    for x in (X0 + 0.05, -0.9, X1 - 0.05):                                # 柱
        cube(wood, (x, Y1 - 0.02, 1.25), (0.11, 0.12, 2.5), bevel=0.01)
    cube(wood, (0, Y1 - 0.03, 1.92), (6.4, 0.08, 0.12), bevel=0.01)       # 長押（横の木）
    cube(wood, (0, Y1 - 0.02, 0.04), (6.4, 0.06, 0.08))                   # 畳寄せ
    for xs in (X0, X1):                                                   # 左右の壁
        cube(plaster, (xs, (Y0 + Y1) / 2, 1.25), (0.1, Y1 - Y0, 2.5))
        cube(wood, (xs + (0.05 if xs < 0 else -0.05), (Y0 + Y1) / 2, 1.92), (0.08, Y1 - Y0, 0.12))
    # 窓：わく・障子（左半分を少し閉めた形）・外
    for (dx, dz, sx, sz) in ((0, (W_Z1 - W_Z0) / 2, W_W + 0.08, 0.06), (0, -(W_Z1 - W_Z0) / 2, W_W + 0.08, 0.08), (-W_W / 2, 0, 0.06, W_Z1 - W_Z0), (W_W / 2, 0, 0.06, W_Z1 - W_Z0)):
        cube(wood, (W_X + dx, Y1 - 0.02, (W_Z0 + W_Z1) / 2 + dz), (sx, 0.1, sz), bevel=0.01)
    shoji = mat("shoji", "#F7F2E6", rough=0.9, emit=0.15 if night else 0.6)
    sx0 = W_X - W_W / 2 + 0.3
    cube(shoji, (sx0, Y1 - 0.08, (W_Z0 + W_Z1) / 2), (0.58, 0.015, W_Z1 - W_Z0 - 0.04))
    for k in range(1, 4): cube(wood, (sx0 - 0.29 + 0.145 * k, Y1 - 0.09, (W_Z0 + W_Z1) / 2), (0.015, 0.02, W_Z1 - W_Z0 - 0.04))
    for k in range(1, 5): cube(wood, (sx0, Y1 - 0.09, W_Z0 + 0.02 + (W_Z1 - W_Z0 - 0.04) * k / 5), (0.58, 0.02, 0.015))
    if night:
        cube(sky_mat("nightsky", "#22305E", "#0A1230", 1.0), (W_X, 6.0, 1.6), (8, 0.05, 6)).visible_shadow = False
        sphere(mat("moon", "#FFF6D8", emit=6.0), (W_X + 0.35, 5.8, 1.62), 0.18).visible_shadow = False
        random.seed(5)
        star = mat("star", "#FFFFFF", emit=8.0)
        for k in range(26):
            sphere(star, (W_X + random.uniform(-1.6, 1.6), 5.9, random.uniform(1.0, 2.6)), random.uniform(0.008, 0.016), seg=8).visible_shadow = False
        for k in range(5):                                                # 遠くの家の屋根と窓の明かり
            x = W_X - 1.6 + k * 0.8
            cube(mat("nroof", "#141B33", rough=0.8), (x, 5.2, 0.9), (0.7, 0.3, 0.5)).visible_shadow = False
            cube(mat("nwin", "#FFD27A", emit=3.0), (x + 0.1, 5.04, 0.95), (0.08, 0.01, 0.08)).visible_shadow = False
    else:
        cube(sky_mat("daysky", "#FFF4DE", "#8EC3EA", 1.6), (W_X, 6.0, 1.6), (8, 0.05, 6)).visible_shadow = False
        random.seed(6)
        for k in range(6):
            sphere(mat("dtree%d" % (k % 3), ("#E07A3A", "#D9B23A", "#7DA35E")[k % 3], rough=0.8), (W_X - 1.4 + k * 0.55, 4.6, random.uniform(0.9, 1.3)), random.uniform(0.35, 0.5), seg=16).visible_shadow = False
        sun((-48, 0, 25), 3.5, "#FFE9C8", angle=3)
    # 小物
    lampm = mat("andon", "#FFE6B5", rough=0.9, emit=2.2 if night else 0.3)
    ax, ay = -1.75, -0.3                                                  # あんどん（ふとんの頭の左）
    cube(lampm, (ax, ay, 0.32), (0.26, 0.26, 0.5))
    for dx in (-0.13, 0.13):
        for dy in (-0.13, 0.13): cube(wood, (ax + dx, ay + dy, 0.33), (0.025, 0.025, 0.66))
    cube(wood, (ax, ay, 0.66), (0.3, 0.3, 0.02))
    if night:
        bpy.ops.object.light_add(type='POINT', location=(ax, ay, 0.35)); l = bpy.context.object.data; l.energy = 18; l.color = srgb("#FFC983")[:3]; l.shadow_soft_size = 0.2
    tx, ty = -2.35, 0.95                                                  # ちゃぶ台と湯のみ
    cyl(wood, (tx, ty, 0.32), 0.42, 0.04, verts=40)
    for a in (45, 135, 225, 315):
        cube(wood, (tx + 0.25 * math.cos(R(a)), ty + 0.25 * math.sin(R(a)), 0.15), (0.05, 0.05, 0.3))
    cyl(mat("yunomi", "#4F6D7A", rough=0.3, coat=0.5), (tx + 0.1, ty - 0.05, 0.38), 0.045, 0.09, verts=24)
    bx = X1 - 0.2                                                         # 本棚（右の壁）
    cube(wood, (bx + 0.14, 0.7, 0.55), (0.04, 0.9, 1.1))                  # 背板
    for yy in (0.27, 1.13): cube(wood, (bx, yy, 0.55), (0.32, 0.04, 1.1))  # 側板
    for zz in (0.02, 0.4, 0.77, 1.12): cube(wood, (bx, 0.7, zz), (0.32, 0.9, 0.035))  # 棚板
    random.seed(9)
    for row, z in enumerate((0.17, 0.55, 0.92)):
        y = 0.32
        while y < 1.06:
            w = random.uniform(0.03, 0.06); h = random.uniform(0.2, 0.28)
            cube(mat("book%d" % (int(y * 100) % 5), random.choice(["#8E3B2F", "#2F5B86", "#C9A44A", "#4F7A4A", "#6B4E7A"]), rough=0.6), (bx - 0.02, y + w / 2, z + h / 2 - 0.13), (0.22, w, h))
            y += w + 0.006
    px, py = X1 - 0.35, Y1 - 0.35                                         # 植木（右奥のすみ）
    cyl(mat("pot", "#B3714A", rough=0.6), (px, py, 0.15), 0.14, 0.3, verts=24)
    for k in range(5):
        sphere(mat("leafp", "#5E9150", rough=0.7), (px + 0.1 * math.cos(k * 1.3), py + 0.1 * math.sin(k * 1.3), 0.45 + 0.08 * k), 0.15, seg=12)
    # ふとん（前と同じ大きさ・場所）：やわらかい形と、かけぶとんの柄
    cube(tex_mat("futon_r", "#F1EBDD", "#E6DECC", 6.0, rough=0.9), (0, 0.4, 0.12), (2.4, 1.6, 0.24), bevel=0.1)
    cube(tex_mat("blanket_r", "#5B7DB8", "#4E6EA6", 9.0, rough=0.9, bump=0.1), (0, 0.6, 0.27), (2.3, 1.2, 0.12), bevel=0.06)
    cube(tex_mat("pillow_r", "#F7F4EC", "#ECE7DC", 8.0, rough=0.9), (0, -0.25, 0.32), (0.8, 0.35, 0.16), bevel=0.07)
    if hook_hat:
        cyl(mat("hook", "#8A6A48", rough=0.4, metal=0.4), (1.4, 1.85, 1.55), 0.03, 0.25, rot=(R(80), 0, 0))
