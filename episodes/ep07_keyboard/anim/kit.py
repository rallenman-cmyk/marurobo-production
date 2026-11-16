# 7本目（キーボード）：3D の部品（scenes.py が exec で読む。前提：KIT_HERE を決めてから読む）
#   まるロボ・人・材質・光・カメラ・床・壁・光る線・歩く人は、6本目（ep06_haizen/anim/kit.py）をそのまま読み込んで使う
#   新しく作った物：夜の机（巨大なキーボード・画面・電気スタンド・窓の夜景・小物）、キーボード（クワーティ・ABC 順・速い並び・いろは歌の 1 列）、
#     1868年の作業場（ピアノのようなタイプライター・新聞・ランプ）、タイプライターの中（円く並ぶ打つ棒）、電信の部屋（受信機・送る機械・電線）、
#     打つ人（腕あり）、教室・大会の会場・事務所・スマホ
#   決まり：3D の中に字を書かない（キーの字は全部 2D で重ねる。キーの場所は TRACK で書き出す）。まるロボは喋らない
import os
_K7 = KIT_HERE
KIT_HERE = os.path.join(_K7, "..", "..", "ep06_haizen", "anim")
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
KIT_HERE = _K7

KEY = 0.16            # キー 1 個の幅（まるロボの体はキー 2 個分くらい）
KEY_TOP = 0.0         # キーボードの置き場所の高さ（机の面）
BLUE_L = "#3D8BFF"    # クワーティの道のり（最後まで同じ色）
ORANGE_L = "#FF9A3C"  # ABC 順の道のり
GREEN_L = "#3CCB6A"   # いろは歌専用の道のり
ROWS_Q = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
ROWS_ABC = ["ABCDEFGHIJ", "KLMNOPQRS", "TUVWXYZ"]
ROWS_DV = ["PYFGCRL", "AOEUIDHTNS", "QJKXBMWVZ"]
OFFS = (0.0, 0.25, 0.75)   # 段のずれ（キー何個分）。hop.py と同じ


def key_pos(rows, ch, origin=(0, 0), k=KEY, offs=OFFS):
    """キー ch の中心（キーボードの左上の段の左端＝origin。奥が +y）"""
    for r, row in enumerate(rows):
        if ch in row:
            c = row.index(ch)
            return (origin[0] + (c + offs[r] + 0.5) * k, origin[1] - r * k)
    raise KeyError(ch)


def keycap(m, loc, k=KEY, parent=None, h=0.07, w=1.0):
    """丸みのあるキー（上の面が少しくぼんだ形の代わりに、角を丸めた台形ぎみの箱）"""
    o = cube(m, loc, (k * 0.88 * w, k * 0.88, h), bevel=k * 0.12, parent=parent)
    return o


class Board:
    """キーボード：root（場所）、keys（字 → キー）。キーを押す（沈む）・光らせる。字は 2D（track 名は prefix+字）"""
    def __init__(self, rows, origin=(0, 0), k=KEY, name="kb", case_col="#2A2F38", key_col="#E9ECEF", offs=OFFS, extra_rows=True, prefix="k_"):
        self.rows, self.k, self.origin, self.offs = rows, k, origin, offs
        self.root = empty((0, 0, KEY_TOP))
        cm = mat(name + "_case", case_col, rough=0.35, coat=0.3)
        kmat = mat(name + "_key", key_col, rough=0.38, coat=0.2)
        mod_m = mat(name + "_mod", "#C9CED4", rough=0.4, coat=0.2)
        w_ = max(len(r) + offs[i] for i, r in enumerate(rows)) * k
        nrow = len(rows) + (2 if extra_rows else 0)
        x0 = origin[0] - (0.6 * k if extra_rows else 0.25 * k); x1 = origin[0] + w_ + (1.8 * k if extra_rows else 0.25 * k)
        y1 = origin[1] + (1.6 * k if extra_rows else 0.6 * k); y0 = origin[1] - (len(rows) - 1) * k - (1.6 * k if extra_rows else 0.6 * k)
        self.case = cube(cm, ((x0 + x1) / 2, (y0 + y1) / 2, -0.03), (x1 - x0, y1 - y0, 0.09), bevel=0.05, parent=self.root)
        self.keys, self.mat = {}, kmat
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                x, y = key_pos(rows, ch, origin, k, offs)
                self.keys[ch] = keycap(kmat, (x, y, 0.045), k, parent=self.root)
        if extra_rows:   # 数字の段・空白の段（字のない灰色のキー。本物らしさのため。字は出さない）
            for c in range(10):
                keycap(mod_m, (origin[0] + (c + 0.5) * k - 0.25 * k, origin[1] + k, 0.045), k, parent=self.root)
            keycap(mod_m, (origin[0] + 4.6 * k, origin[1] - len(rows) * k, 0.045), k, w=5.0, parent=self.root)
            keycap(mod_m, (origin[0] + w_ + 0.9 * k, origin[1] - 1 * k, 0.045), k, w=1.6, parent=self.root)
        self.glows = {}

    def pos(self, ch, z=0.09):
        x, y = key_pos(self.rows, ch, self.origin, self.k, self.offs)
        return (x, y, KEY_TOP + z)

    def press(self, ch, t, d=0.14, sound=True, gain=0.5):
        o = self.keys[ch]; z = o.location.z
        key(o, ("location", 2), t - 0.01, z); key(o, ("location", 2), t + 0.04, z - 0.03); key(o, ("location", 2), t + d, z)
        if sound: ev(t, "key", gain)

    def light(self, ch, t0, t1=None, col="#FFD24A", strength=2.5, d=0.25):
        """キーを光らせる（その字のキーの上の面に光る板）。t1 で消す"""
        o = self.keys[ch]
        if ch not in self.glows:   # 大きさを scale で付けた物に scale_pop を使わない（SKILL）：空の親を弾ませる
            gm = flat_mat("kglow_" + ch + str(id(self)), col, strength)
            g = empty((o.location.x, o.location.y, o.location.z + 0.038)); g.parent = self.root
            gl = cube(gm, (0, 0, 0), (self.k * 0.8, self.k * 0.8, 0.004), parent=g); gl.visible_shadow = False
            self.glows[ch] = g; hide_key(g, -100.0, True)
        g = self.glows[ch]
        hide_key(g, t0, False); scale_pop(g, t0, 1.0, d)
        if t1 is not None: hide_key(g, t1, True)

    def track_all(self, prefix="k_", dz=0.06):
        for ch, o in self.keys.items(): track(prefix + ch, o, dz)


def hop_path(B, word, t0, dt, M=None, col=BLUE_L, z=0.1, name="path", h=0.18, line=True):
    """まるロボが word の字を順に跳ねて打つ（dt 秒ごと）。跳ねた道のりを光る線で残す（言った字まで伸びる）"""
    word = [c for c in word.upper() if c in B.keys]
    pts = [B.pos(c)[:2] for c in word]
    ln = None
    if line and len(pts) > 1:
        ln = line_path(name, pts, col=col, width=0.018, z=KEY_TOP + z, emit=3.0)
        ln.data.bevel_factor_end = 0.0; ln.data.keyframe_insert("bevel_factor_end", frame=f(t0))
        L = [0.0]
        for a, b in zip(pts, pts[1:]): L.append(L[-1] + math.dist(a, b))
        for i in range(1, len(pts)):
            ln.data.bevel_factor_end = L[i] / L[-1]; ln.data.keyframe_insert("bevel_factor_end", frame=f(t0 + i * dt))
        for fc in ln.data.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    if M is not None:
        for i, c in enumerate(word):
            p = B.pos(c, z=0.075)
            ta = t0 + i * dt
            if i == 0:
                M.at(ta - 0.3, loc=p)
            else:
                M.at(ta - dt * 0.85, loc=B.pos(word[i - 1], z=0.075), interp="LINEAR"); M.at(ta - 0.02, loc=p, interp="LINEAR")
                M.hop(ta - dt * 0.85, h=h, d=dt * 0.83, sound=False)
            B.press(c, ta, gain=0.35 if dt < 0.3 else 0.5)
    return ln


# ======================================================================== A：夜の机
def night_window(x0, x1, y, z0, z1):
    """奥の窓：夜の町（遠くのビルの窓の明かり。字なし）"""
    sky = bpy.data.materials.new("nightsky"); sky.use_nodes = True; nt = sky.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = srgb("#3A3F66"); ramp.color_ramp.elements[1].color = srgb("#0E1428")
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs[0])
    o = cube(sky, ((x0 + x1) / 2, y + 6.0, (z0 + z1) / 2 + 1.0), (x1 - x0 + 8, 0.05, (z1 - z0) + 6)); o.visible_shadow = False
    random.seed(7)
    bm = mat("bld", "#1B2236", rough=0.9); wm = glow_mat("bldwin", "#FFD58A", 2.2)
    for k in range(14):
        x = x0 - 2 + k * (x1 - x0 + 4) / 14 + random.uniform(-0.2, 0.2); h = random.uniform(1.5, 4.0); wd = random.uniform(0.6, 1.1)
        cube(bm, (x, y + 4.5, z0 - 1.5 + h / 2), (wd, 0.4, h)).visible_shadow = False
        for j in range(int(h / 0.45)):
            for i_ in range(2):
                if random.random() < 0.45:
                    cube(wm, (x - wd / 4 + i_ * wd / 2, y + 4.28, z0 - 1.3 + j * 0.45), (0.14, 0.02, 0.18)).visible_shadow = False
    # 窓わく
    fm = mat("winframe", "#E9E4DA", rough=0.5)
    for xx in (x0, x1, (x0 + x1) / 2): cube(fm, (xx, y, (z0 + z1) / 2), (0.12, 0.12, z1 - z0))
    for zz in (z0, z1): cube(fm, ((x0 + x1) / 2, y, zz), (x1 - x0 + 0.12, 0.12, 0.12))


def desk_room(dark=True):
    """夜の机の上（巨大な世界。キー 1 個＝0.16）。机の面 z=0。奥の壁と窓・電気スタンド・画面・マグ・ペン立て・植木・ノート"""
    world("#0B1020", 0.25)
    dm = wood_floor("deskwood", c1="#8A5F3C", c2="#7A5233", mortar="#5E3E26", width=3.0, row=0.6, coat=0.35, grain=0.35)
    cube(dm, (0.8, -1.2, -0.15), (14.0, 9.0, 0.3))
    # 奥の壁（壁紙）と窓
    wall = stripe_wall("deskwall", 'X')
    for xs, xe in ((-6.0, -1.6), (3.4, 8.0)):
        cube(wall, ((xs + xe) / 2, 3.4, 2.5), (xe - xs, 0.1, 5.4))
    cube(wall, (0.9, 3.4, -0.2 + 0.45), (5.0, 0.1, 0.9)); cube(wall, (0.9, 3.4, 4.6), (5.0, 0.1, 1.2))
    night_window(-1.6, 3.4, 3.42, 0.7, 4.0)
    # 画面（モニター）：奥。光る面（字は 2D）
    st = mat("monstand", "#2B2F36", rough=0.35, metal=0.4)
    cyl(st, (0.9, 2.2, 0.05), 0.5, 0.06); cube(st, (0.9, 2.35, 0.9), (0.25, 0.12, 1.7))
    cube(mat("monframe", "#1C2027", rough=0.3), (0.9, 2.2, 2.0), (4.4, 0.16, 2.6), bevel=0.06)
    scr = cube(glow_mat("monscreen", "#CFE0F5", 1.6), (0.9, 2.11, 2.0), (4.15, 0.02, 2.35))
    track("screen", scr, 0.3)
    # 電気スタンド（左の奥。あたたかい光）
    lm = mat("lampmetal", "#C9A96B", rough=0.3, metal=0.8)
    cyl(lm, (-2.6, 1.6, 0.04), 0.45, 0.08); cyl(lm, (-2.6, 1.6, 1.3), 0.05, 2.5)
    shade = cyl(mat("lampshade", "#F2E2BE", rough=0.6, emit=1.5), (-2.3, 1.2, 2.6), 0.55, 0.6, rot=(R(30), 0, 0))
    bpy.ops.object.light_add(type='POINT', location=(-2.2, 1.0, 2.2)); L1 = bpy.context.object; L1.data.energy = 900; L1.data.color = srgb("#FFD9A0")[:3]; L1.data.shadow_soft_size = 0.4
    # 画面の光（青白い）・部屋の弱い光
    area((0.9, 1.6, 2.0), (0.9, -1.0, 0.0), energy=260, size=4.0, col="#BFD6FF")
    area((4.0, -4.0, 5.0), (0.5, 0.0, 0.0), energy=420, size=6.0, col="#9FB3E0")
    # 小物（右）：マグ・ペン立て・植木・ノート
    cyl(mat("mug", "#D8574A", rough=0.3, coat=0.5), (4.6, 1.2, 0.55), 0.42, 1.1)
    cyl(mat("mugin", "#3B2418", rough=0.2), (4.6, 1.2, 1.08), 0.36, 0.04)
    cyl(mat("pencup", "#5B6E86", rough=0.5), (5.6, 2.2, 0.6), 0.32, 1.2)
    for k, c in enumerate(("#F2C14E", "#4F81BD", "#E57373")):
        cyl(mat("pencil" + c, c, rough=0.5), (5.5 + 0.12 * k, 2.2, 1.5), 0.05, 1.2, rot=(R(8 - 8 * k), R(6), 0))
    cyl(mat("pot", "#C98A5B", rough=0.6), (-4.2, 2.4, 0.4), 0.45, 0.8)
    for k in range(7):
        a = k * 2 * math.pi / 7
        sphere(mat("leaf", "#5E9150", rough=0.7), (-4.2 + 0.35 * math.cos(a), 2.4 + 0.35 * math.sin(a), 1.2 + 0.2 * (k % 2)), 0.32, scale=(1, 0.6, 1.4))
    cube(mat("note", "#F5F0E1", rough=0.8), (-3.6, -2.4, 0.03), (1.6, 2.1, 0.06), rot=(0, 0, R(12)), bevel=0.02)
    cube(mat("notecover", "#3E7CB1", rough=0.6), (-3.62, -2.42, 0.0), (1.66, 2.16, 0.04), rot=(0, 0, R(12)))


# ======================================================================== C：1868年の作業場（ランプのあかり・木の机・新聞・窓の外は昼の町）
def workshop(night=False):
    world("#2A2118" if night else "#6E6150", 0.35)
    fl = wood_floor("shopfloor", c1="#6B4A30", c2="#5C3E27", mortar="#3D2817", width=1.4, row=0.22, coat=0.05, grain=0.3)
    cube(fl, (0, 0, -0.05), (12, 10, 0.1))
    br = noise_mat("brick", "#8C5A44", "#6E4433", scale=14, rough=0.85, bump=0.15)
    cube(br, (0, 2.6, 1.8), (12, 0.2, 3.6)); cube(br, (-3.6, 0, 1.8), (0.2, 10, 3.6))
    # 窓（右の奥）。外は昼の光（夜は暗い）
    cube(mat("shopwin", "#F6E9C8" if not night else "#1A2238", rough=0.5, emit=1.6 if not night else 0.3), (1.6, 2.49, 1.9), (1.4, 0.02, 1.4))
    for xx in (0.9, 1.6, 2.3): cube(mat("winwood", "#4A3220", rough=0.6), (xx, 2.47, 1.9), (0.06, 0.06, 1.46))
    for zz in (1.2, 1.9, 2.6): cube(mat("winwood", "#4A3220", rough=0.6), (1.6, 2.47, zz), (1.46, 0.06, 0.06))
    # 大きな木の机（作業台）
    tw = wood_floor("benchwood", c1="#8A6342", c2="#7B5638", mortar="#5A3D26", width=2.0, row=0.3, coat=0.2, grain=0.3)
    cube(tw, (0, 0.6, 0.9), (3.6, 1.6, 0.08))
    for xx in (-1.7, 1.7):
        for yy in (-0.1, 1.3): cube(mat("benchleg", "#5A3D26", rough=0.6), (xx, yy, 0.43), (0.1, 0.1, 0.86))
    # 新聞の束・工具・インク壺（字は書かない。灰色の線の模様だけ）
    npm = noise_mat("newsprint", "#E8E0CC", "#CFC6B0", scale=40, rough=0.9)
    for k in range(4): cube(npm, (-1.3, 1.1, 0.95 + k * 0.012), (0.55, 0.4, 0.01), rot=(0, 0, R(4 * k - 6)))
    cyl(mat("ink", "#1E2430", rough=0.2, coat=0.6), (1.2, 1.2, 0.98), 0.07, 0.1)
    for k in range(3): cube(mat("tool", "#7A7F86", rough=0.3, metal=0.8), (1.3 + k * 0.12, 0.2, 0.95), (0.03, 0.3, 0.02), rot=(0, 0, R(10 * k)))
    # ランプ（あたたかい光）
    cyl(mat("lampbase", "#9C7A3C", rough=0.3, metal=0.8), (-1.0, 1.3, 1.0), 0.09, 0.14)
    sphere(mat("lampglass", "#FFE2A8", rough=0.2, emit=4.0 if night else 2.0), (-1.0, 1.3, 1.2), 0.12, scale=(1, 1, 1.3))
    bpy.ops.object.light_add(type='POINT', location=(-1.0, 1.2, 1.4)); L = bpy.context.object; L.data.energy = 220 if night else 90; L.data.color = srgb("#FFC878")[:3]
    if not night:
        area((1.6, 2.3, 2.0), (0.0, 0.4, 0.9), energy=380, size=1.6, col="#FFF1D6")
    area((0, -3.0, 3.0), (0, 0.6, 0.9), energy=160 if not night else 50, size=4.0, col="#FFE3BC")
    # 棚と道具（左の壁）
    for zz in (1.5, 2.1): cube(mat("shelf", "#5A3D26", rough=0.6), (-3.4, 0.6, zz), (0.3, 1.8, 0.05))
    for k in range(5): cube(mat("box" + str(k), ["#8C6A4A", "#A07E58", "#6E5038", "#9A8466", "#7F6247"][k], rough=0.7), (-3.4, -0.1 + k * 0.33, 1.62), (0.24, 0.24, 0.2))


def piano_typewriter(loc=(0, 0.55, 0.94), k=0.13):
    """1868年の最初のタイプライター（ピアノのような 2 列の鍵盤。手前 A→N、奥 O→Z を右から左）。keys：字 → キー"""
    root = empty(loc)
    wood = mat("pianowood", "#3B2414", rough=0.35, coat=0.6)
    white = mat("pianokey", "#F2EBDD", rough=0.3, coat=0.4)
    black = mat("pianokeyb", "#1A1612", rough=0.3, coat=0.4)
    n = 14
    cube(wood, (n * k / 2, 0.25, 0.05), (n * k + 0.3, 0.9, 0.1), bevel=0.02, parent=root)
    cube(wood, (n * k / 2, 0.55, 0.32), (n * k + 0.3, 0.3, 0.5), bevel=0.02, parent=root)   # 奥の箱（中に棒）
    cube(mat("platen", "#22262C", rough=0.3), (n * k / 2, 0.55, 0.62), (n * k * 0.8, 0.12, 0.12), bevel=0.04, parent=root)
    keys = {}
    front = "ABCDEFGHIJKLMN"; back = "OPQRSTUVWXYZ"
    for i, ch in enumerate(front):
        keys[ch] = cube(white, ((i + 0.5) * k, -0.05, 0.14), (k * 0.92, 0.32, 0.06), bevel=0.01, parent=root)
    for i, ch in enumerate(back):   # 右から左
        x = (n - 0.5 - i) * k - k * 0.5
        keys[ch] = cube(black, (x, 0.2, 0.2), (k * 0.7, 0.2, 0.06), bevel=0.01, parent=root)
    return root, keys


def modern_typewriter(loc=(0, 0.55, 0.94), k=0.13, period=True, layout=None, col="#2B2B2B", name="tw"):
    """1870年代のタイプライター（4 段の丸いキー・円く並ぶ棒の箱）。layout：上の段の字（R の所がピリオドなら '.'）"""
    root = empty(loc)
    body = mat(name + "_body", col, rough=0.3, coat=0.7, metal=0.2)
    gold = mat(name + "_gold", "#C9A24E", rough=0.25, metal=0.9)
    cube(body, (0, 0.15, 0.12), (1.5, 1.0, 0.24), bevel=0.06, parent=root)
    cube(body, (0, 0.45, 0.42), (1.3, 0.5, 0.45), bevel=0.08, parent=root)
    cyl(mat(name + "_platen", "#15171A", rough=0.4), (0, 0.55, 0.72), 0.09, 1.5, rot=(0, R(90), 0), parent=root)
    cube(mat(name + "_paper", "#F4EFE3", rough=0.8), (0, 0.62, 0.95), (0.9, 0.02, 0.45), parent=root)
    keys = {}
    rows = layout or ["QWE.TYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    km = mat(name + "_keytop", "#F1EEE6", rough=0.3, coat=0.5)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            x = -0.62 + (c + OFFS[r]) * k; y = -0.05 - r * k * 0.9; z = 0.28 - r * 0.04
            cyl(gold, (x, y, z - 0.02), k * 0.4, 0.03, parent=root)
            keys[ch] = cyl(km, (x, y, z), k * 0.34, 0.025, parent=root)
    return root, keys


def typebar_basket(center=(0, 0, 0), r=1.2, n=36, bars=None):
    """タイプライターの中：円く並ぶ打つ棒（半円）。棒の先は真ん中の打つ所へ。bars：字 → 棒の pivot（empty）。
    棒を上げる＝pivot を x 軸で回す。E と R はとなり同士（論文の表の通り。ほかの字の並びはだいたい）"""
    order = list("ZXCVBNM,.;LKJHGFDSAQWERTYUIOP-/:?'&")[:n]
    i_e = order.index("E"); i_r = order.index("R")
    root = empty(center)
    steel = mat("barsteel", "#A9B0B8", rough=0.25, metal=0.95)
    seg = mat("segment", "#3A3530", rough=0.4, metal=0.6)
    arc_band(seg, r + 0.12, r - 0.08, -0.08, 0.02, R(0), R(180), parent=root)
    pv = {}
    for i, ch in enumerate(order):
        a = math.pi * (i + 0.5) / n
        p = empty((r * math.cos(a), r * math.sin(a) * 0.55, 0)); p.parent = root
        p.rotation_euler = (0, 0, a + math.pi / 2)
        b = cube(steel, (0, -r * 0.45, 0.02), (0.035, r * 0.9, 0.025), parent=p)
        cube(mat("typehead", "#2A2D31", rough=0.3, metal=0.7), (0, -r * 0.9, 0.04), (0.06, 0.06, 0.06), parent=p)
        pv[ch] = p
    cyl(mat("guide", "#55504A", rough=0.4, metal=0.7), (0, 0, 0.9), 0.12, 0.1, parent=root)
    return root, pv


def bar_up(p, t, d=0.35, back=True, ang=78):
    key(p, ("rotation_euler", 0), t, 0.0); key(p, ("rotation_euler", 0), t + d * 0.5, R(-ang))   # 棒は x 軸の負の向きに回すと上がる（正だと床の下へ。7本目 v2 で見えなかった）
    if back: key(p, ("rotation_euler", 0), t + d, 0.0)


# ======================================================================== 打つ人（腕あり。手はキーの上で上下）
class Typist:
    pass


def typist(loc, face=0.0, shirt="#5B6E86", sit=True, hair="#2B2220", skin="#F1C7A5", s=1.0, dress=False):
    root = empty(loc, R(face), s)
    p = person((0, 0, 0), 0, shirt=shirt, pants="#2D3640" if not dress else "#4A2F3A", skin=skin, hair=hair, sit=sit)
    p.parent = root
    sm = mat("shirt" + shirt, shirt, rough=0.7); km = mat("skin", skin, rough=0.55)
    tz = 0.85 if sit else 1.15
    arms = []
    for sx in (-0.22, 0.22):
        ap = empty((sx, -0.05, tz + 0.25)); ap.parent = root; ap.rotation_euler = (R(-62), 0, 0)
        cyl(sm, (0, 0, -0.24), 0.05, 0.5, parent=ap, verts=12)
        sphere(km, (0, 0, -0.5), 0.055, scale=(1, 1.4, 0.7), parent=ap, seg=12)
        arms.append(ap)
    t_ = Typist(); t_.root = root; t_.arms = arms
    return t_


def type_motion(T_, t0, t1, rate=6.0, gain=0.0):
    """手を交互に小さく上下（打っている）。gain>0 なら打つ音も"""
    k = 0; t = t0
    while t < t1:
        a = T_.arms[k % 2]
        key(a, ("rotation_euler", 0), t, R(-62)); key(a, ("rotation_euler", 0), t + 0.5 / rate, R(-55)); key(a, ("rotation_euler", 0), t + 1 / rate, R(-62))
        if gain: ev(t + 0.5 / rate, "key", gain)
        t += 1 / rate; k += 1


# ======================================================================== D：電信の部屋
def telegraph_room():
    world("#2C2620", 0.3)
    fl = wood_floor("telfloor", c1="#6E5036", c2="#5E432C", mortar="#3D2A1B", width=1.2, row=0.2, coat=0.05, grain=0.3)
    cube(fl, (0, 0, -0.05), (12, 10, 0.1))
    wp = stripe_wall("telwall", 'X')
    cube(wp, (0, 2.6, 1.8), (12, 0.2, 3.6)); cube(mat("telwainscot", "#5A3F2A", rough=0.6), (0, 2.48, 0.5), (12, 0.04, 1.0))
    cube(wp, (-3.6, 0, 1.8), (0.2, 10, 3.6))
    # 壁の電線（白い磁器のつまみと線）
    wm = mat("wire", "#2A2420", rough=0.5)
    for zz in (2.4, 2.55):
        cyl(wm, (0, 2.45, zz), 0.01, 8.0, rot=(0, R(90), 0))
        for xx in (-2.5, -1.0, 0.5, 2.0): sphere(mat("insul", "#F2EFE6", rough=0.2, coat=0.6), (xx, 2.45, zz), 0.04)
    # 長い机
    tw = wood_floor("telbench", c1="#8A6342", c2="#7B5638", mortar="#5A3D26", width=2.0, row=0.3, coat=0.2, grain=0.3)
    cube(tw, (0, 0.8, 0.88), (5.0, 1.0, 0.07))
    for xx in (-2.3, 2.3):
        for yy in (0.4, 1.2): cube(mat("benchleg", "#5A3D26", rough=0.6), (xx, yy, 0.42), (0.08, 0.08, 0.84))
    # 時計（字なし）・窓
    cyl(mat("clockface", "#F4EFE3", rough=0.4), (2.6, 2.48, 2.6), 0.28, 0.05, rot=(R(90), 0, 0))
    cyl(mat("clockrim", "#5A3D26", rough=0.4), (2.6, 2.5, 2.6), 0.31, 0.04, rot=(R(90), 0, 0))
    cube(mat("telwin", "#F3E6C4", rough=0.5, emit=1.4), (-1.8, 2.49, 2.0), (1.2, 0.02, 1.2))
    for k in range(3):
        bpy.ops.object.light_add(type='POINT', location=(-2 + 2 * k, 0.6, 2.4)); L = bpy.context.object; L.data.energy = 130; L.data.color = srgb("#FFCF8A")[:3]
        cyl(mat("pendshade", "#2E4A3A", rough=0.4), (-2 + 2 * k, 0.6, 2.55), 0.18, 0.1)
    area((0, -3, 3), (0, 0.8, 0.9), energy=140, size=4, col="#FFE3BC")


def sounder(loc):
    """受信機（カチカチ鳴る：上の腕が上下する）。arm を返す"""
    root = empty(loc)
    brass = mat("brass", "#C9A24E", rough=0.25, metal=0.9)
    cube(mat("sndbase", "#4A3220", rough=0.5), (0, 0, 0.02), (0.36, 0.22, 0.04), parent=root)
    for xx in (-0.08, 0.08): cyl(brass, (xx, 0, 0.09), 0.035, 0.12, parent=root)
    arm = empty((-0.12, 0, 0.17)); arm.parent = root
    cube(brass, (0.13, 0, 0), (0.3, 0.03, 0.025), parent=arm)
    return root, arm


def morse_key(loc):
    root = empty(loc)
    brass = mat("brass", "#C9A24E", rough=0.25, metal=0.9)
    cube(mat("keybase", "#4A3220", rough=0.5), (0, 0, 0.02), (0.3, 0.14, 0.04), parent=root)
    lever = empty((-0.1, 0, 0.07)); lever.parent = root
    cube(brass, (0.12, 0, 0), (0.26, 0.025, 0.02), parent=lever)
    cyl(mat("knob", "#1A1612", rough=0.3), (0.24, 0, 0.03), 0.035, 0.03, parent=lever)
    return root, lever


def click_seq(arm, t0, pattern, unit=0.09, gain=0.6, ang=8):
    """モールス信号の音と動き。pattern：'.'＝トン、'-'＝ツー、' '＝少しあき。終わりの時刻を返す"""
    t = t0
    for ch in pattern:
        if ch == ' ':
            t += unit * 2.5; continue
        d = unit if ch == '.' else unit * 3
        key(arm, ("rotation_euler", 1), t - 0.005, 0.0); key(arm, ("rotation_euler", 1), t + 0.02, R(ang)); key(arm, ("rotation_euler", 1), t + d, R(ang)); key(arm, ("rotation_euler", 1), t + d + 0.02, 0.0)
        ev(t, "tick", gain)
        t += d + unit
    return t


# ======================================================================== E：教室・大会の会場・事務所
def hall(col_wall="#D9CDB8", floor=("#9A7452", "#8A6446"), w=12, d=10, lamps=4):
    world("#40372C", 0.3)
    fl = wood_floor("hallfloor" + col_wall, c1=floor[0], c2=floor[1], mortar="#5A3D26", width=1.3, row=0.16, coat=0.1, grain=0.25)
    cube(fl, (0, 0, -0.05), (w, d, 0.1))
    cube(mat("hallwall" + col_wall, col_wall, rough=0.85), (0, d / 2 - 1.0, 2.0), (w, 0.2, 4.0))
    cube(mat("hallwain", "#6B4A30", rough=0.6), (0, d / 2 - 1.12, 0.55), (w, 0.04, 1.1))
    for k in range(lamps):
        x = -w / 2 + (k + 0.5) * w / lamps
        bpy.ops.object.light_add(type='POINT', location=(x, 0.0, 3.0)); L = bpy.context.object; L.data.energy = 260; L.data.color = srgb("#FFD9A0")[:3]
        sphere(mat("hallglobe", "#FFE7B8", rough=0.2, emit=3.0), (x, 0.0, 3.2), 0.16)
    for k in range(3):   # 窓
        x = -w / 2 + (k + 1) * w / 4
        cube(mat("hallwin", "#F3E6C4", rough=0.5, emit=1.2), (x, d / 2 - 1.09, 2.2), (1.1, 0.02, 1.5))
    area((0, -d / 2 + 1, 3.5), (0, 0, 0.8), energy=260, size=6, col="#FFE3BC")


def office_room():
    """今の事務所（明るい。机と画面とキーボードがずらり）"""
    world("#DDE6EE", 0.6)
    fl = noise_mat("carpet", "#7E8A96", "#6E7A86", scale=60, rough=0.95)
    cube(fl, (0, 0, -0.05), (16, 12, 0.1))
    cube(mat("offwall", "#EEF1F4", rough=0.8), (0, 4.5, 2.0), (16, 0.2, 4.0))
    cube(mat("offwin", "#CFE6FA", rough=0.4, emit=1.3), (0, 4.38, 2.1), (10, 0.02, 2.2))
    for xx in range(-5, 6, 2): cube(mat("mullion", "#B9C2CB", rough=0.4, metal=0.5), (xx, 4.36, 2.1), (0.06, 0.04, 2.3))
    sun((55, 0, 160), energy=2.5, col="#FFF4E5")
    area((0, 0, 3.6), (0, 0, 0), energy=900, size=8, col="#FFFFFF", shape='RECTANGLE')


def office_desk(x, y, face=0.0, shirt="#3E7CB1", person_on=True, kb_glow=False):
    """事務所の机 1 つ（画面・キーボード・打つ人）。キーボードは小さな箱（字は出さない）"""
    root = empty((x, y, 0), R(face))
    cube(mat("offdesk", "#E8E2D6", rough=0.5), (0, 0, 0.74), (1.4, 0.75, 0.04), parent=root)
    for sx in (-0.65, 0.65): cube(mat("offleg", "#8A929A", rough=0.4, metal=0.6), (sx, 0, 0.37), (0.04, 0.7, 0.74), parent=root)
    cube(mat("offmon", "#1C2027", rough=0.3), (0, 0.22, 1.08), (0.62, 0.04, 0.38), parent=root)
    cube(glow_mat("offscr", "#BFD6FF", 1.2), (0, 0.199, 1.08), (0.58, 0.005, 0.34), parent=root)
    kb = cube(mat("offkb", "#2A2F38", rough=0.4), (0, -0.12, 0.775), (0.44, 0.15, 0.02), parent=root)
    tp = None
    if person_on:
        tp = typist((0, -0.62, 0), 0, shirt=shirt); tp.root.parent = root
    return root, tp, kb


def smartphone(loc, s=1.0):
    """今のスマホ（薄い板・画面は光る。キーボードの絵は 2D で重ねる）。screen を返す"""
    root = empty(loc, 0, s)
    cube(mat("phonebody", "#1E2228", rough=0.25, metal=0.5), (0, 0, 0.04), (1.6, 3.2, 0.08), bevel=0.18, parent=root)
    scr = cube(glow_mat("phonescr", "#E9EEF5", 1.3), (0, 0, 0.081), (1.46, 3.0, 0.004), parent=root)
    cube(glow_mat("phonekbd", "#D5DBE3", 1.1), (0, -0.85, 0.084), (1.46, 1.2, 0.002), parent=root)
    return root, scr
