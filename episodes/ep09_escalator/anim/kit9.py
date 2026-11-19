# 9本目（エスカレーター）：3D の部品（scenes.py が exec で読む。前提：KIT_HERE を決めてから読む）
#   まるロボ・人・材質・光・カメラは 6本目（ep06_haizen/anim/kit.py → 3本目の部品）をそのまま読み込んで使う
#   新しく作った物：エスカレーター（段の輪・2 本のレール・鎖・上と下の歯車・モーター・くし・手すり・段の横の壁・外の板）、
#     駅（下の床・上の床・横の階段・壁・天井の明かり）、床の下の機械の部屋（ふた・暗い通り道）、作業台（外した段・模型）
#   形と動きの計算は esc_geom.py（Blender の外でも同じ）。段・鎖・歯車・手すりの印は、コマごとに場所を計算して置く（frame_change_pre）
#   決まり：3D の中に字を書かない。まるロボは喋らない。前の車輪と前のレール＝オレンジ、後ろの車輪と後ろのレール＝紫（最後まで同じ）。くしと段のふちの線は黄色
import os, sys, math
_K9 = KIT_HERE
KIT_HERE = os.path.join(_K9, "..", "..", "ep06_haizen", "anim")
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
KIT_HERE = _K9
sys.path.insert(0, _K9)
import importlib, esc_geom as G
importlib.reload(G)

ORANGE_W = "#FF8A1F"       # 前の車輪・前のレール
PURPLE_W = "#8A4DFF"       # 後ろの車輪・後ろのレール
YELLOW_C = "#FFC928"       # くし・段のふちの線
STEEL = "#B9C0C8"
DARK = "#2B3036"
YW = G.WID / 2              # 段の幅の半分
Y_CHAIN = YW + 0.03         # 鎖
Y_FW = YW + 0.07            # 前の車輪と前のレール
Y_RW = YW + 0.13            # 後ろの車輪と後ろのレール（前の車輪より外。レールがぶつからない）
Y_SKIRT = YW + 0.005        # 段の横の壁（すき間 5mm）
HR_H = 0.95                 # 手すりの高さ（踏む面から）
CLAD_Y = YW + 0.24          # 外の板（骨組みのおおい）の y
Y_HR = YW + 0.17            # 手すり


def _m(name, col, **kw): return mat(name, col, **kw)


M = dict(tread=_m("tread", "#5B6168", rough=0.45, metal=0.6), cleat=_m("cleat", "#7B828A", rough=0.4, metal=0.7),
         yellow=_m("yellow", YELLOW_C, rough=0.5), riser=_m("riser", "#4C5258", rough=0.5, metal=0.5),
         frame=_m("frame", "#3A3F45", rough=0.6, metal=0.4), fw=_m("fw", ORANGE_W, rough=0.5), rw=_m("rw", PURPLE_W, rough=0.5),
         chain=_m("chain", "#6E747A", rough=0.35, metal=0.9), gear=_m("gear", "#8D949B", rough=0.3, metal=0.9),
         rail_f=_m("rail_f", ORANGE_W, rough=0.4, metal=0.3), rail_r=_m("rail_r", PURPLE_W, rough=0.4, metal=0.3),
         skirt=_m("skirt", "#C9CFD5", rough=0.25, metal=0.9), panel=_m("panel", "#E8E4DC", rough=0.5),
         clad=_m("clad", "#C3C8CD", rough=0.45, metal=0.15), hr=_m("hr", "#1E2226", rough=0.35), hr_mark=_m("hr_mark", "#9AA3AD", rough=0.4),
         plate=_m("plate", "#A9AFB5", rough=0.3, metal=0.9), motor=_m("motor", "#3E6E8E", rough=0.5, metal=0.3),
         floor=_m("floor", "#D8D2C8", rough=0.6), floor2=_m("floor2", "#C9C2B6", rough=0.6), wall=_m("wall", "#EDEAE4", rough=0.8),
         pit=_m("pit", "#3B3F44", rough=0.85), truss=_m("truss", "#6D747B", rough=0.6, metal=0.5))


# ======================================================================== 段
def make_step(k):
    """段 1 枚（基準＝前の車輪の中心）。踏む面は z=+TREAD_DZ。前は +x"""
    root = empty((0, 0, 0)); root.name = "step%02d" % k
    tz = G.TREAD_DZ
    x0, x1 = -0.38, 0.02
    cube(M["tread"], ((x0 + x1) / 2, 0, tz - 0.015), (x1 - x0, G.WID, 0.03), parent=root)
    # 溝（くしの歯がかみ合う細い山）：進む向きにのびる。配列で並べる
    rib = cube(M["cleat"], ((x0 + x1) / 2, -YW + 0.03, tz + 0.004), (x1 - x0 - 0.04, 0.012, 0.008), parent=root)
    ar = rib.modifiers.new("arr", "ARRAY"); ar.count = 20; ar.relative_offset_displace = (0, 0, 0)
    ar.use_relative_offset = False; ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0.0495 / rib.scale[1] if False else 0.0495, 0)
    # 黄色いふち（前と左右）
    cube(M["yellow"], (x1 - 0.02, 0, tz + 0.001), (0.04, G.WID, 0.03), parent=root)
    for sy in (-1, 1): cube(M["yellow"], ((x0 + x1) / 2, sy * (YW - 0.02), tz + 0.001), (x1 - x0, 0.04, 0.03), parent=root)
    # 立ち上がり（後ろ）
    cube(M["riser"], (x0 + 0.006, 0, tz - 0.1), (0.012, G.WID - 0.02, 0.2), parent=root)
    # 横の骨組み（左右）・車軸
    for sy in (-1, 1):
        cube(M["frame"], (-0.17, sy * (YW - 0.03), 0.09), (0.36, 0.025, 0.16), parent=root)
    cyl(M["frame"], (0, 0, 0), 0.018, 2 * Y_FW, rot=(R(90), 0, 0), parent=root, verts=12)
    cyl(M["frame"], (G.REAR[0], 0, G.REAR[1]), 0.015, 2 * Y_RW, rot=(R(90), 0, 0), parent=root, verts=12)
    for sy in (-1, 1):
        cyl(M["fw"], (0, sy * Y_FW, 0), 0.05, 0.035, rot=(R(90), 0, 0), parent=root, verts=24)
        cyl(M["rw"], (G.REAR[0], sy * Y_RW, G.REAR[1]), 0.045, 0.035, rot=(R(90), 0, 0), parent=root, verts=24)
    return root


def tube(name, pts, r, m, y=0.0, closed=False):
    """(x, z) の点を通る管（y に置く）"""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, (x, z) in enumerate(pts): sp.points[i].co = (x, y, z, 1)
    sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(m)
    return ob


def ribbon(name, pts_lo, pts_hi, y, m, thick=0.01):
    """2 本の線（下・上。どちらも (x, z) を同じ数）の間の板（y の所。厚み thick）"""
    me = bpy.data.meshes.new(name); n = len(pts_lo)
    vs = [(x, y, z) for x, z in pts_lo] + [(x, y, z) for x, z in pts_hi]
    fs = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
    me.from_pydata(vs, [], fs); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(m)
    if thick:
        so = ob.modifiers.new("sol", "SOLIDIFY"); so.thickness = thick
    return ob


def _tread_line(n=160, x_lo=None, x_hi=None):
    """人が乗る側の踏む面の線（x, z）"""
    out = []
    for i in range(n + 1):
        (x, z), _ = G.top_point(G.LTOP * i / n)
        out.append((x - 0.18, max(0.0, z + G.TREAD_DZ) if x < 3 else z + G.TREAD_DZ))
    return out


def clad_profile(n=220):
    """外の板の形：x ごとの (x, 上の z, 下の z)。上＝デッキの線、下＝戻る側の下。右の端は機械の部屋（モーターが入る）を包む"""
    tl = _tread_line(300)
    xs = [x for x, _ in tl]; zs = [z for _, z in tl]
    import bisect
    def tz(x):
        if x <= xs[0]: return zs[0]
        if x >= xs[-1]: return zs[-1]
        i = bisect.bisect_right(xs, x) - 1; u = (x - xs[i]) / max(1e-9, xs[i + 1] - xs[i]); return zs[i] + (zs[i + 1] - zs[i]) * u
    xl = G.X_LO_END - G.RG - 0.55; xr = G.X_HI_END + G.RG + 1.7
    drop = 2 * G.RG + G.TREAD_DZ + 0.55; zr = G.H - 1.75; xm = G.X_HI_END - 0.8
    out = []
    for k in range(n + 1):
        x = xl + (xr - xl) * k / n
        if x < xs[0] - 0.3: top = 0.0                       # 下の乗り口の前：床と同じ高さ
        elif x < xs[-1] + 0.3: top = tz(x) + 0.25
        else: top = G.H
        bot = zr if x >= xm else min(tz(x) - drop, -0.3 if x < 1.0 else 9)
        out.append((x, top, min(bot, top - 0.3)))
    return out


# ======================================================================== エスカレーター
class Esc:
    """エスカレーター 1 台。speed：G.Speed（段の速さ）。hr_speed：手すりの速さ（None なら段と同じ）"""

    def __init__(self, speed, hr_speed=None, cutaway=False, inside=False, lid=True):
        self.speed = speed; self.hr_speed = hr_speed or speed
        self.steps = [make_step(k) for k in range(G.N_STEPS)]
        self.cutaway = cutaway
        self.near = []          # 手前（-y）側の板（断面の絵で消す）
        self._rails(); self._chain(); self._gears(); self._skirt_and_balustrade(); self._combs(); self._handrail()
        self.override = {}      # 段ごとの置き直し（模型など）
        bpy.app.handlers.frame_change_pre.append(self.update)
        bpy.context.scene.render.use_lock_interface = True

    # ---------------------------------------------------------------- レール
    def _rails(self):
        def seg_pts(which):
            out = []; cur = []
            for i in range(1201):
                s = G.LOOP * i / 1200
                x, z, r = G.loop_pose(s)
                if which == "rear": x, z = G.local_to_world(x, z, r, *G.REAR)
                flip = 1 if abs(((r + 90) % 360) - 90) < 1 else (-1 if abs(r % 360 - 180) < 1 else 0)
                if flip == 0:
                    if len(cur) > 1: out.append(cur)
                    cur = []; continue
                rr = 0.05 if which == "front" else 0.045
                cur.append((x, z - rr * flip - 0.012 * flip))
            if len(cur) > 1: out.append(cur)
            return out
        self.rails = {"front": [], "rear": []}
        for which, m, yy in (("front", M["rail_f"], Y_FW), ("rear", M["rail_r"], Y_RW)):
            for j, pts in enumerate(seg_pts(which)):
                for sy in (-1, 1):
                    ob = tube("rail_%s_%d_%d" % (which, j, sy), pts, 0.012, m, y=sy * yy)
                    self.rails[which].append(ob)
                    if sy < 0: self.near.append(ob)

    # ---------------------------------------------------------------- 鎖（段の前の車輪どうしをつなぐ。コマごとに置く）
    def _chain(self):
        self.links = []
        for k in range(G.N_STEPS):
            pair = []
            for sy in (-1, 1):
                ob = cube(M["chain"], (0, sy * Y_CHAIN, 0), (1.0, 0.025, 0.035), bevel=0.008)
                pair.append(ob)
                if sy < 0: self.near.append(ob)
            self.links.append(pair)

    # ---------------------------------------------------------------- 歯車とモーター
    def _gears(self):
        (ex, ez), _ = G.top_point(G.LTOP); (bx, bz), _ = G.top_point(0.0)
        self.gear_c = {"hi": (ex, ez - G.RG), "lo": (bx, bz - G.RG)}
        self.gears = {}
        for nm, (cx, cz) in self.gear_c.items():
            g = empty((cx, 0, cz)); g.name = "gear_" + nm
            for sy in (-1, 1):
                d = cyl(M["gear"], (0, sy * Y_CHAIN, 0), G.RG - 0.02, 0.04, rot=(R(90), 0, 0), parent=g, verts=48)
                if sy < 0: self.near.append(d)
                for j in range(18):                      # 歯
                    a = 2 * math.pi * j / 18
                    t_ = cube(M["gear"], ((G.RG - 0.005) * math.cos(a), sy * Y_CHAIN, (G.RG - 0.005) * math.sin(a)), (0.05, 0.035, 0.035),
                              rot=(0, -a, 0), parent=g)
                    if sy < 0: self.near.append(t_)
                for j in range(5):                       # 輻（回っているのが分かるように）
                    a = 2 * math.pi * j / 5
                    sp = cube(M["frame"], (0.12 * math.cos(a), sy * (Y_CHAIN + 0.025), 0.12 * math.sin(a)), (0.22, 0.01, 0.04), rot=(0, -a, 0), parent=g)
                    if sy < 0: self.near.append(sp)
            cyl(M["gear"], (0, 0, 0), 0.04, 2 * Y_CHAIN + 0.1, rot=(R(90), 0, 0), parent=g, verts=24)
            self.gears[nm] = g
        cx, cz = self.gear_c["hi"]
        self.motor = cube(M["motor"], (cx + 0.75, 0.2, cz - 0.15), (0.6, 0.45, 0.4), bevel=0.04)
        cyl(M["motor"], (cx + 0.75, 0.2, cz - 0.15), 0.2, 0.62, rot=(R(90), 0, 0), verts=32)
        # モーターから歯車への小さな鎖（輪）
        self.drive = tube("drive_chain", [(cx + 0.75 + 0.12 * math.cos(a), cz - 0.15 + 0.12 * math.sin(a)) for a in [i * 2 * math.pi / 24 for i in range(25)]],
                          0.012, M["chain"], y=0.55)

    # ---------------------------------------------------------------- 段の横の壁・手すりの下の板・外の板（骨組みのおおい）
    def _skirt_and_balustrade(self):
        tl = _tread_line()
        x0, x1 = tl[0][0] - 0.3, tl[-1][0] + 0.3
        lo = [(x0, tl[0][1])] + tl + [(x1, tl[-1][1])]
        deck = [(x, z + 0.25) for x, z in lo]
        self.skirts = []; self.far = []
        for sy in (-1, 1):
            sk = ribbon("skirt%d" % sy, lo, deck, sy * (Y_SKIRT + 0.005), M["skirt"], thick=0.01)
            b = ribbon("balu%d" % sy, deck, [(x, z + HR_H - 0.06) for x, z in lo], sy * (Y_HR - 0.02), M["panel"], thick=0.02)
            # デッキ（段の横の壁の上から外の板までの、上のふた）
            me = bpy.data.meshes.new("deck%d" % sy); n = len(deck)
            ya, yb = sy * (Y_SKIRT + 0.01), sy * (CLAD_Y + 0.01)
            vs = [(x, ya, z) for x, z in deck] + [(x, yb, z) for x, z in deck]
            me.from_pydata(vs, [], [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]); me.update()
            dk = bpy.data.objects.new("deck%d" % sy, me); bpy.context.scene.collection.objects.link(dk); dk.data.materials.append(M["clad"])
            so = dk.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.02
            self.skirts.append(sk)
            (self.near if sy < 0 else self.far).extend([sk, b, dk])
        # 外の板：輪ぜんぶと、上の端の機械の部屋を包む箱（横の面＝帯、下の面、両端）
        pr = clad_profile()
        for sy in (-1, 1):
            ob = ribbon("clad%d" % sy, [(x, b) for x, t, b in pr], [(x, t) for x, t, b in pr], sy * CLAD_Y, M["clad"], thick=0.03)
            (self.near if sy < 0 else self.far).append(ob)
        me = bpy.data.meshes.new("clad_bottom"); n = len(pr)
        vs = [(x, -CLAD_Y, b) for x, t, b in pr] + [(x, CLAD_Y, b) for x, t, b in pr]
        fs = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        x, t, b = pr[0]; vs += [(x, -CLAD_Y, t), (x, CLAD_Y, t)]; fs.append((0, n, 2 * n + 1, 2 * n))
        x, t, b = pr[-1]; vs += [(x, -CLAD_Y, t), (x, CLAD_Y, t)]; fs.append((n - 1, 2 * n - 1, 2 * n + 3, 2 * n + 2))
        me.from_pydata(vs, [], fs); me.update()
        ob = bpy.data.objects.new("clad_bottom", me); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(M["clad"])
        self.rim = ob

    # ---------------------------------------------------------------- くし（降り口と乗り口）
    def _combs(self):
        self.combs = {}
        for nm, xc, d in (("lo", G.COMB_LO_X - 0.18, +1), ("hi", G.COMB_HI_X - 0.18, -1)):
            z = 0.0 if nm == "lo" else G.H
            c = empty((xc, 0, z)); c.name = "comb_" + nm
            cube(M["yellow"], (-d * 0.06, 0, -0.012), (0.12, G.WID + 0.02, 0.024), parent=c)
            tooth = cube(M["yellow"], (d * 0.045, -YW + 0.0245, -0.022), (0.09, 0.008, 0.012), rot=(0, R(d * 12), 0), parent=c)
            ar = tooth.modifiers.new("arr", "ARRAY"); ar.count = 20; ar.use_relative_offset = False
            ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0.0495, 0)
            self.combs[nm] = c

    # ---------------------------------------------------------------- 手すり（輪。見える所は上の線と、両端の半円）
    def _handrail(self):
        tl = _tread_line(120)
        x0, x1 = tl[0][0] - 0.6, tl[-1][0] + 0.6
        top = [(x0, HR_H)] + [(x, z + HR_H) for x, z in tl] + [(x1, G.H + HR_H)]
        r = 0.22
        # 戻る所は見えない所を通る：上の端は上の床の板の中へ下り、外の板の中（デッキの下）を通って、下の端は床の下から上がってくる
        loop = [(x1 + r * math.sin(a), G.H + HR_H - r + r * math.cos(a)) for a in [i * math.pi / 16 for i in range(17)]]
        under = [(x1, G.H - 0.2), (x1 - 0.7, G.H - 0.2)] + [(x, z - HR_H - 0.15) for x, z in reversed(top[1:-1]) if x0 + 1.2 < x < x1 - 0.8] + \
                [(x0 + 1.0, -0.3), (x0, -0.3)]
        loop2 = [(x0 - r * math.sin(a), HR_H - r - r * math.cos(a)) for a in [i * math.pi / 16 for i in range(17)]]
        path = top + loop + under + loop2
        # 長さで割り付け（手すりの印を置く）
        acc = [0.0]
        for (a, b), (c, d) in zip(path, path[1:]): acc.append(acc[-1] + math.hypot(c - a, d - b))
        self.hr_path, self.hr_acc = path, acc
        # 手すりの両端の台（手すりが下へ入っていく所を包む。手すりの入口＝インレットはここ）
        self.inlets = {}
        for nm, xa, xb, z0 in (("lo", x0 - 0.05, tl[0][0] - 0.25, 0.0), ("hi", tl[-1][0] + 0.25, x1 + 0.05, G.H)):
            for sy in (-1, 1):
                nb = cube(M["panel"], ((xa + xb) / 2, sy * Y_HR, z0 + (HR_H - 0.12) / 2), (xb - xa, 0.11, HR_H - 0.12), bevel=0.02)
                cap = cube(M["hr"], (x0 if nm == "lo" else x1, sy * Y_HR, z0 + HR_H - 0.13), (0.1, 0.12, 0.05), bevel=0.015)   # ゴムのカバー（入口）
                if sy < 0: self.near += [nb, cap]; self.inlets[nm] = cap
        self.hrs, self.marks = [], []
        for sy in (-1, 1):
            ob = tube("handrail%d" % sy, path, 0.035, M["hr"], y=sy * Y_HR, closed=True)
            ob.scale = (1, 1, 1); self.hrs.append(ob)
            if sy < 0: self.near.append(ob)
            ms = []
            for j in range(int(acc[-1] / 0.6)):
                mk = cube(M["hr_mark"], (0, sy * Y_HR, 0), (0.05, 0.075, 0.075))
                ms.append(mk)
                if sy < 0: self.near.append(mk)
            self.marks.append(ms)

    def hr_point(self, s):
        s %= self.hr_acc[-1]
        import bisect
        i = max(0, min(len(self.hr_acc) - 2, bisect.bisect_right(self.hr_acc, s) - 1))
        (a, b), (c, d) = self.hr_path[i], self.hr_path[i + 1]
        u = (s - self.hr_acc[i]) / max(1e-9, self.hr_acc[i + 1] - self.hr_acc[i])
        return a + (c - a) * u, b + (d - b) * u, math.atan2(d - b, c - a)

    # ---------------------------------------------------------------- 時刻ごとの置き場所
    def t_of(self, scene):
        return CLOCK["T0"] + scene.frame_current / FPS

    def pos(self, t): return self.speed.pos(t)

    def step_world(self, k, t):
        """k 番目の段の、前の車輪の世界の場所 (x, z) と回り角"""
        (x, z), r, _ = G.step_pose(k, self.pos(t))
        return x, z, r

    def update(self, scene, *_):
        t = self.t_of(scene); p = self.pos(t)
        W = []
        for k, st in enumerate(self.steps):
            if k in self.override:
                self.override[k](st, t); W.append(None); continue
            (x, z), r, _ = G.step_pose(k, p)
            st.location = (x, 0, z); st.rotation_euler = (0, math.radians(r), 0)
            W.append((x, z))
        for k, pair in enumerate(self.links):
            a = W[k]; b = W[(k + 1) % len(W)]
            if a is None or b is None:
                for ob in pair: ob.hide_render = True; ob.hide_viewport = True
                continue
            L = math.hypot(b[0] - a[0], b[1] - a[1]); ang = math.atan2(b[1] - a[1], b[0] - a[0])
            for ob in pair:
                ob.hide_render = False; ob.hide_viewport = False
                ob.location = ((a[0] + b[0]) / 2, ob.location.y, (a[1] + b[1]) / 2)
                ob.rotation_euler = (0, -ang, 0); ob.scale = (L * 0.5, 0.0125, 0.0175)   # cube() は大きさを scale に持つ（1 辺 2 の箱）
        for g in self.gears.values(): g.rotation_euler = (0, p / G.RG, 0)
        hp = self.hr_speed.pos(t)
        for ms in self.marks:
            for j, mk in enumerate(ms):
                x, z, a = self.hr_point(hp + j * 0.6)
                mk.location = (x, mk.location.y, z); mk.rotation_euler = (0, -a, 0)

    def set_cutaway(self, on=True):
        for ob in self.near: ob.hide_render = on; ob.hide_viewport = on


# ======================================================================== 駅（昼・夜）
def station(night=False):
    """下の床（z=0）・上の床（z=H。厚さ 0.45）・奥の壁・横の階段・天井の明かり。段とふたの所は床に穴を開ける"""
    hy = CLAD_Y + 0.01
    xl0 = G.COMB_LO_X - 0.18                     # 下のくし
    xh0 = G.COMB_HI_X - 0.18                     # 上のくし
    lid_lo = (xl0 - 1.2, xl0); lid_hi = (xh0, xh0 + 1.3)
    rise_x = 5.2                                 # 外の板の下が床から出る所
    # 下の床（厚さ 2.2）：穴＝x が lid_lo[0]〜rise_x、|y|<hy
    def box(m, xa, xb, ya, yb, za, zb):
        return cube(m, ((xa + xb) / 2, (ya + yb) / 2, (za + zb) / 2), (xb - xa, yb - ya, zb - za))
    box(M["floor"], -14, lid_lo[0], -8, 8, -2.2, 0)
    box(M["floor"], rise_x, 26, -8, 8, -2.2, 0)
    box(M["floor"], lid_lo[0], rise_x, -8, -hy, -2.2, 0); box(M["floor"], lid_lo[0], rise_x, hy, 8, -2.2, 0)
    # 上の床：左のふち SL。穴＝x が SL〜lid_hi[1]、|y|<hy
    SL = 7.6
    box(M["floor2"], lid_hi[1], 26, -8, 8, G.H - 0.45, G.H)
    box(M["floor2"], SL, lid_hi[1], -8, -hy, G.H - 0.45, G.H); box(M["floor2"], SL, lid_hi[1], hy, 8, G.H - 0.45, G.H)
    # くしの手前から上のくしまでの間の床の板（くしの外側の、段がない所）は穴のまま（段と外の板でふさがる）
    lids = {}
    for nm, (xa, xb), z in (("lo", lid_lo, 0.0), ("hi", lid_hi, G.H)):
        lids[nm] = cube(M["plate"], ((xa + xb) / 2, 0, z - 0.012), (xb - xa, 2 * hy, 0.03), bevel=0.003)
    # 奥の壁
    cube(M["wall"], (6.0, 8.0, 3.0), (40.0, 0.3, 9.0))
    # 横の階段（奥 y=+2.6。下の床 → 上の床）
    n = 18; rise = G.H / n; run = 0.3; x_start = SL - n * run
    for i in range(n):
        box(M["floor2"], x_start + i * run, x_start + (i + 1) * run, 1.9, 3.3, 0, rise * (i + 1))
    world("#DCE6EE" if not night else "#2A3340", 0.9 if not night else 0.25)
    for i, x in enumerate([-3, 1, 5, 9, 13]):
        if night and i % 2: continue
        area((x, 0.5, 6.5), (x, 0.5, 0), energy=900 if not night else 380, size=2.5, col="#FFF6E8")
    if not night: sun((48, 0, 28))
    return lids


# ======================================================================== 床の下（機械の部屋）
def pit():
    """上の降り口の下の部屋。暗い壁と、作業の明かり"""
    (xh, zh), _ = G.top_point(G.LTOP)
    cx, cz = xh, zh - G.RG
    cube(M["pit"], (cx + 0.6, 0, cz - 1.0), (3.4, 2.6, 0.1))           # 床
    cube(M["pit"], (cx + 2.3, 0, cz + 0.3), (0.1, 2.6, 2.6))           # 奥の壁（右）
    for sy in (-1, 1): cube(M["pit"], (cx + 0.6, sy * 1.3, cz + 0.3), (3.4, 0.1, 2.6))
    bpy.ops.object.light_add(type='POINT', location=(cx + 1.2, -0.6, cz + 0.6)); lt = bpy.context.object; lt.data.energy = 120; lt.data.color = srgb("#FFE2B8")[:3]
    return lt


# ======================================================================== 人（点検のおじさん・お客さん）
def ojisan(loc, face=0.0):
    """点検のおじさん：作業着（紺）・ヘルメット（白）。立ち姿"""
    w_ = walker(loc, face, shirt="#2E4A6B", pants="#2E4A6B", skin="#E9BE98", hair="#3A3430")
    sphere(mat("helmet", "#F4F4F0", rough=0.3), (0, 0, 0.09), 0.19, scale=(1.0, 1.05, 0.7), parent=w_.head)
    return w_
