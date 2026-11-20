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
XR_PIT = G.X_HI_END + G.RG + 2.4      # 上の機械の部屋の右の端（歯車の右に、まるロボが立てる所とモーター）
Z_PIT_HI = G.H - (2 * G.TREAD_DZ + G.DIP + 2 * G.RG + 0.2)   # 上の機械の部屋の床（戻る段のいちばん下より 0.2 下）
XL_PIT = G.X_LO_END - G.RG - 1.5      # 下の機械の部屋の左の端（下の歯車の左に、まるロボが立てる所）
Z_PIT_LO = -(2 * G.TREAD_DZ + G.DIP + 2 * G.RG + 0.2)         # 下の機械の部屋の床（戻る段のいちばん下より 0.2 下）
LID_HI = (G.X_HI_END + G.RG + 0.35, G.X_HI_END + G.RG + 1.75)   # 上のふた（歯車の右の上。下りると機械の部屋の床）
LID_LO = (XL_PIT + 0.1, G.X_LO_END - G.RG - 0.3)                 # 下のふた
Y_HR = YW + 0.17            # 手すり


def _m(name, col, **kw): return mat(name, col, **kw)


M = dict(tread=_m("tread", "#4A5056", rough=0.55, metal=0.2), cleat=_m("cleat", "#8E959C", rough=0.4, metal=0.3),
         yellow=_m("yellow", YELLOW_C, rough=0.5), riser=_m("riser", "#4C5258", rough=0.5, metal=0.5),
         frame=_m("frame", "#3A3F45", rough=0.6, metal=0.4), fw=_m("fw", ORANGE_W, rough=0.5), rw=_m("rw", PURPLE_W, rough=0.5),
         chain=_m("chain", "#6E747A", rough=0.35, metal=0.9), gear=_m("gear", "#A7AEB6", rough=0.35, metal=0.55),
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
    rib = cube(M["cleat"], ((x0 + x1) / 2, -YW + 0.03, tz + 0.006), (x1 - x0 - 0.04, 0.012, 0.012), parent=root)
    ar = rib.modifiers.new("arr", "ARRAY"); ar.count = 20; ar.relative_offset_displace = (0, 0, 0)
    ar.use_relative_offset = False; ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0.0495 / rib.scale[1], 0)          # 大きさを scale に持つので、ずらす量も scale で割る
    # 黄色いふち（前と左右）
    # 前のふちは、溝の山と同じ形で黄色に（くしの歯が通れるように。べたの帯だと歯を突き抜ける）
    cube(M["yellow"], (x1 - 0.02, 0, tz - 0.004), (0.04, G.WID, 0.01), parent=root)
    yr = cube(M["yellow"], (x1 - 0.02, -YW + 0.03, tz + 0.006), (0.04, 0.013, 0.0125), parent=root)
    ar = yr.modifiers.new("arr", "ARRAY"); ar.count = 20; ar.relative_offset_displace = (0, 0, 0)
    ar.use_relative_offset = False; ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0.0495 / yr.scale[1], 0)
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
    xl = XL_PIT; xr = XR_PIT
    drop = 2 * G.RG + 2 * G.TREAD_DZ + G.DIP + 0.2; zr = Z_PIT_HI; xm = G.X_HI_END - 0.8
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
                bpy.ops.mesh.primitive_torus_add(location=(0, sy * Y_CHAIN, 0), rotation=(R(90), 0, 0), major_radius=G.RG - 0.05, minor_radius=0.035)
                d = bpy.context.object; d.data.materials.append(M["gear"]); d.parent = g
                hub = cyl(M["gear"], (0, sy * Y_CHAIN, 0), 0.1, 0.06, rot=(R(90), 0, 0), parent=g, verts=32)
                if sy < 0: self.near += [d, hub]
                for j in range(18):                      # 歯
                    a = 2 * math.pi * j / 18
                    t_ = cube(M["gear"], ((G.RG - 0.005) * math.cos(a), sy * Y_CHAIN, (G.RG - 0.005) * math.sin(a)), (0.05, 0.035, 0.035),
                              rot=(0, -a, 0), parent=g)
                    if sy < 0: self.near.append(t_)
                for j in range(5):                       # 輻（回っているのが分かるように）
                    a = 2 * math.pi * j / 5
                    sp = cube(M["frame"], ((G.RG / 2) * math.cos(a), sy * Y_CHAIN, (G.RG / 2) * math.sin(a)), (G.RG - 0.12, 0.03, 0.05), rot=(0, -a, 0), parent=g)
                    if sy < 0: self.near.append(sp)
            cyl(M["gear"], (0, 0, 0), 0.04, 2 * Y_CHAIN + 0.1, rot=(R(90), 0, 0), parent=g, verts=24)
            self.gears[nm] = g
        cx, cz = self.gear_c["hi"]
        mx, mz = XR_PIT - 0.55, Z_PIT_HI + 0.32      # モーター：機械の部屋の右の奥（まるロボが立つ所の奥）
        self.motor = cube(M["motor"], (mx, 0.45, mz), (0.6, 0.5, 0.6), bevel=0.04)
        cyl(M["motor"], (mx, 0.45, mz), 0.26, 0.56, rot=(R(90), 0, 0), verts=32)
        self.motor_c = (mx, 0.45, mz)
        # モーターから歯車への鎖（ベルトのように回る輪）：歯車の軸とモーターの軸をつなぐ
        pts = []
        for a_ in [i * math.pi / 12 for i in range(13)]: pts.append((cx + 0.12 * math.cos(math.pi / 2 + a_), cz + 0.12 * math.sin(math.pi / 2 + a_)))
        for a_ in [i * math.pi / 12 for i in range(13)]: pts.append((mx + 0.1 * math.cos(-math.pi / 2 + a_), mz + 0.1 * math.sin(-math.pi / 2 + a_)))
        self.drive = tube("drive_chain", pts + pts[:1], 0.012, M["chain"], y=0.62)

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
            # くしの板：段の上に少し浮いた板（下の面 +0.02）。平らになった段は、この板の下をすべって出入りする（2026-11-19 くしで段がはみ出た直し）
            #   黄色い所（くし）0.14 ＋ 灰色の板 0.41 ＋ 床へ下りる坂 0.12
            hw = CLAD_Y + 0.01
            cube(M["yellow"], (-d * 0.07, 0, 0.029), (0.14, 2 * hw, 0.018), parent=c)
            cube(M["plate"], (-d * 0.345, 0, 0.029), (0.41, 2 * hw, 0.018), parent=c)
            cube(M["plate"], (-d * 0.61, 0, 0.019), (0.125, 2 * hw, 0.01), rot=(0, R(-d * 17), 0), parent=c)
            # 歯：板のふちから段の溝（山と山の間）へ下がって、先が入る
            tooth = cube(M["yellow"], (d * 0.05, -YW + 0.0548, 0.02), (0.12, 0.022, 0.012), rot=(0, R(d * 14), 0), parent=c)
            ar = tooth.modifiers.new("arr", "ARRAY"); ar.count = 19; ar.use_relative_offset = False
            ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0.0495 / tooth.scale[1], 0)
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
        # 手すりを動かす車（戻る所の途中で、上と下からはさんで、こすって送る）。奥（+y）の手すりだけ（断面の絵で見える）
        import bisect
        xr_ = 5.5; best = min(range(len(path)), key=lambda i: abs(path[i][0] - xr_) + (0 if path[i][1] < (G.top_point(G.LTOP * 0.5)[0][1] + HR_H) - 0.5 else 9))
        rx_, rz_ = path[best]
        self.hr_rollers = []
        for dz in (0.035 + 0.055, -(0.035 + 0.055)):
            rr = cyl(M["gear"], (rx_, Y_HR, rz_ + dz), 0.055, 0.1, rot=(R(90), 0, 0), verts=32)
            cyl(M["frame"], (rx_ + 0.03, Y_HR - 0.051, rz_ + dz), 0.012, 0.004, rot=(R(90), 0, 0), verts=12, parent=rr)    # 回るのが分かる印
            self.hr_rollers.append(rr)
        self.hr_roll_c = (rx_, rz_)
        # 手すりの両端の台（手すりが下へ入っていく所を包む。手すりの入口＝インレットはここ）
        self.inlets = {}
        for nm, xa, xb, z0 in (("lo", x0 - 0.05, tl[0][0] - 0.25, 0.0), ("hi", tl[-1][0] + 0.25, x1 + 0.05, G.H)):
            for sy in (-1, 1):
                nb = cube(M["panel"], ((xa + xb) / 2, sy * Y_HR, z0 + (HR_H - 0.12) / 2), (xb - xa, 0.11, HR_H - 0.12), bevel=0.02)
                cap = cube(M["hr"], (x0 if nm == "lo" else x1, sy * Y_HR, z0 + HR_H - 2 * r), (0.1, 0.12, 0.05), bevel=0.015)   # ゴムのカバー（入口）。手すりが台の中へ入る所（端の半円の下）
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
                for ob in pair:
                    if not ob.hide_render: ob.hide_render = True; ob.hide_viewport = True
                continue
            L = math.hypot(b[0] - a[0], b[1] - a[1]); ang = math.atan2(b[1] - a[1], b[0] - a[0])
            for ob in pair:
                if ob.hide_render and not self.cutaway_on(ob): ob.hide_render = False; ob.hide_viewport = False
                ob.location = ((a[0] + b[0]) / 2, ob.location.y, (a[1] + b[1]) / 2)
                ob.rotation_euler = (0, -ang, 0); ob.scale = (L * 0.5, 0.0125, 0.0175)   # cube() は大きさを scale に持つ（1 辺 2 の箱）
        for g in self.gears.values(): g.rotation_euler = (0, p / G.RG, 0)
        hp = self.hr_speed.pos(t)
        for j, rr in enumerate(getattr(self, "hr_rollers", [])): rr.rotation_euler = (R(90), (1 if j else -1) * hp / 0.055, 0)
        for ms in self.marks:
            for j, mk in enumerate(ms):
                x, z, a = self.hr_point(hp + j * 0.6)
                mk.location = (x, mk.location.y, z); mk.rotation_euler = (0, -a, 0)

    def set_cutaway(self, on=True):
        self._cut = on
        for ob in self.near: ob.hide_render = on; ob.hide_viewport = on

    def cutaway_on(self, ob):
        """断面の絵で、手前の部品は消したまま（コマごとの置き直しで出さない）"""
        return getattr(self, "_cut", False) and ob in self._near_set()

    def _near_set(self):
        if not hasattr(self, "_ns"): self._ns = set(self.near)
        return self._ns


# ======================================================================== 駅（昼・夜）
def station(night=False):
    """下の床（z=0）・上の床（z=H。厚さ 0.45）・奥の壁・横の階段・天井の明かり。段とふたの所は床に穴を開ける"""
    hy = CLAD_Y + 0.01
    xl0 = G.COMB_LO_X - 0.18                     # 下のくし
    xh0 = G.COMB_HI_X - 0.18                     # 上のくし
    lid_lo = LID_LO; lid_hi = LID_HI
    rise_x = 5.2                                 # 外の板の下が床から出る所
    # 下の床（厚さ 2.2）：穴＝x が lid_lo[0]〜rise_x、|y|<hy
    def box(m, xa, xb, ya, yb, za, zb):
        return cube(m, ((xa + xb) / 2, (ya + yb) / 2, (za + zb) / 2), (xb - xa, yb - ya, zb - za))
    box(M["floor"], -14, lid_lo[0], -8, 8, -2.6, 0)
    box(M["floor"], rise_x, 26, -8, 8, -2.6, 0)
    box(M["floor"], lid_lo[0], rise_x, -8, -hy, -2.6, 0); box(M["floor"], lid_lo[0], rise_x, hy, 8, -2.6, 0)
    # 下のくしからふたまでの間の床の板（段の手前）
    box(M["plate"], lid_lo[1], xl0 - 0.55, -hy, hy, -0.03, 0.0)
    # 上の床：左のふち SL。穴＝x が SL〜lid_hi[1]、|y|<hy
    SL = 7.6
    box(M["floor2"], lid_hi[1], 26, -8, 8, G.H - 0.45, G.H)
    box(M["floor2"], SL, lid_hi[1], -8, -hy, G.H - 0.45, G.H); box(M["floor2"], SL, lid_hi[1], hy, 8, G.H - 0.45, G.H)
    # 上のくしからふたまでの間の床の板
    box(M["plate"], xh0 + 0.55, lid_hi[0], -hy, hy, G.H - 0.03, G.H)
    lids = {}
    for nm, (xa, xb), z in (("lo", lid_lo, 0.0), ("hi", lid_hi, G.H)):
        lids[nm] = cube(M["plate"], ((xa + xb) / 2, 0, z - 0.012), (xb - xa, 2 * hy, 0.03), bevel=0.003)
    # 上の床の右のふち（上の床の穴の右）：lid_hi の右から
    box(M["floor2"], lid_hi[1], lid_hi[1] + 0.01, -hy, hy, G.H - 0.45, G.H - 0.44)
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
    """床の下の機械の部屋（外の板の中）：作業の明かり（上と下）。床は外の板の下の面"""
    L = []
    for loc in ((XR_PIT - 1.1, -0.45, Z_PIT_HI + 1.05), (G.X_HI_END - 1.5, -0.45, G.H - 0.9), (XL_PIT + 0.7, -0.45, Z_PIT_LO + 1.1), (3.5, -0.45, 0.2)):
        bpy.ops.object.light_add(type='POINT', location=loc); lt = bpy.context.object; lt.data.energy = 90; lt.data.color = srgb("#FFE2B8")[:3]
        lt.data.shadow_soft_size = 0.15; L.append(lt)
    return L


# ======================================================================== 人（点検のおじさん・お客さん）
def ojisan(loc, face=0.0):
    """点検のおじさん：作業着（紺）・ヘルメット（白）。立ち姿"""
    w_ = walker(loc, face, shirt="#2E4A6B", pants="#2E4A6B", skin="#E9BE98", hair="#3A3430")
    if len(loc) > 2: w_.root.location.z = loc[2]          # walker は高さを 0 にするので、上の床に立たせるときは高さを入れ直す（9本目：おじさんが床の下に埋まっていた）
    sphere(mat("helmet", "#F4F4F0", rough=0.3), (0, 0, 0.09), 0.19, scale=(1.0, 1.05, 0.7), parent=w_.head)
    return w_


# ======================================================================== 速さ（とばし付き）・段を探す・乗る
class SpeedS(G.Speed):
    """G.Speed に「とばし」を足した物：skips＝[(時刻, 長さ)]。カメラが切りかわる瞬間に、輪を先へ進める（見えない所で時間を縮める）"""

    def __init__(self, keys, skips=(), **kw):
        super().__init__(keys, **kw); self.skips = list(skips)

    def pos(self, t, t_from=-30.0):
        return super().pos(t, t_from) + sum(d for ts, d in self.skips if t >= ts)


def _esc_helpers():
    def step_at(self, k, t):
        (x, z), r, _ = G.step_pose(k, self.pos(t)); return x, z, r

    def find_step(self, t, x_target):
        """t に、前の車輪が x_target のいちばん近くにある、人が乗る側（表）の段"""
        best = None
        for k in range(G.N_STEPS):
            x, z, r = self.step_at(k, t)
            if abs(r) > 0.5: continue
            d = abs(x - x_target)
            if best is None or d < best[0]: best = (d, k)
        return best[1]

    def tread(self, k, t, lx=-0.18, ly=0.0):
        """段 k の踏む面の上の点（表のとき）"""
        x, z, r = self.step_at(k, t)
        wx, wz = G.local_to_world(x, z, r, lx, G.TREAD_DZ)
        return (wx, ly, wz)

    def back(self, k, t, lx=-0.18, ly=0.0):
        """段 k がさかさまのときの、上を向いた裏の上の点"""
        x, z, r = self.step_at(k, t)
        wx, wz = G.local_to_world(x, z, r, lx, -0.03)
        return (wx, ly, wz)

    def carry_fn(self, k, t0, lx=-0.18, back=False):
        P = self.back if back else self.tread
        a = P(k, t0, lx)
        return lambda t: tuple(b - c for b, c in zip(P(k, t, lx), a))

    def sticker(self, k, t_show):
        """段 k の踏む面の後ろの方に、まるロボの顔のシール（字のない絵：白い丸に青緑の目）"""
        st = self.steps[k]
        d = cyl(mat("stk", "#F7F7F2", rough=0.4), (-0.27, -0.25, G.TREAD_DZ + 0.011), 0.075, 0.004, parent=st, verts=32)
        cyl(mat("stk_eye", "#1FB8AC", rough=0.3, emit=0.6), (-0.27, -0.25, G.TREAD_DZ + 0.0135), 0.03, 0.002, parent=st, verts=24)
        for ob in [d] + [c for c in st.children if c.name.startswith("Cylinder") and abs(c.location.z - (G.TREAD_DZ + 0.0135)) < 1e-4]:
            hide_key(ob, -100.0, True); hide_key(ob, t_show, False)
        return d

    def add_rider(self, wk, k, y=0.15):
        self.riders.append((wk, k, y))

    def _riders(self, p):
        s_board, s_alight = G.DIP_LEN + 0.45, G.LTOP - G.DIP_LEN - 0.3
        xb, _ = G.top_point(s_board)[0]; xa, _ = G.top_point(s_alight)[0]
        for wk, k, y in self.riders:
            sk = (p + k * G.PITCH) % G.LOOP
            u = sk - s_board
            if u > G.LOOP / 2: u -= G.LOOP
            Lr = s_alight - s_board
            if u < 0: x, z, walk = xb + u, 0.0, True
            elif u <= Lr:
                (fx, fz), _ = G.top_point(sk); x, z, walk = fx - 0.18, fz + G.TREAD_DZ, False
            else: x, z, walk = xa + (u - Lr), G.H, True
            wk.root.location = (x, y, z)
            vis = -11.0 < x < 22.0 and not any(a_ <= self._t_now <= b_ for a_, b_ in getattr(self, "rider_hide", []))
            if getattr(wk, "_vis", None) != vis:          # 変わったときだけ（毎コマ書くと、Blender が全部を組み直して遅い）
                wk._vis = vis
                for ob in [wk.root] + list(wk.root.children_recursive): ob.hide_render = not vis
            sw = 0.45 * math.sin(2 * math.pi * x / 1.1) if walk else 0.0
            wk.hips[0].rotation_euler = (sw, 0, 0); wk.hips[1].rotation_euler = (-sw, 0, 0)

    Esc.step_at, Esc.find_step, Esc.tread, Esc.back, Esc.carry_fn, Esc.sticker, Esc.add_rider, Esc._riders = \
        step_at, find_step, tread, back, carry_fn, sticker, add_rider, _riders


_esc_helpers()
_esc_init0 = Esc.__init__
_esc_upd0 = Esc.update


def _esc_init(self, *a, **kw):
    self.riders = []
    _esc_init0(self, *a, **kw)


def _esc_update(self, scene, *_):
    _esc_upd0(self, scene)
    self._t_now = self.t_of(scene)
    if self.riders: self._riders(self.pos(self._t_now))


Esc.__init__ = _esc_init
Esc.update = _esc_update


# ======================================================================== 断面の絵（D）：手前の床・板を外した絵
def station_back(bg="#E9EEF3"):
    """断面の絵の舞台：奥側（y > 段の幅）の床だけ。手前は切った面を見せる。背景は明るい灰色"""
    hy = CLAD_Y + 0.01
    def box(m, xa, xb, ya, yb, za, zb):
        return cube(m, ((xa + xb) / 2, (ya + yb) / 2, (za + zb) / 2), (xb - xa, yb - ya, zb - za))
    cut = mat("cutface", "#B9B2A6", rough=0.7)
    box(cut, -6, 0.0, hy, 4, -2.2, 0); box(cut, 5.2, 16, hy, 4, -2.2, 0); box(cut, 0.0, 5.2, hy, 4, -2.2, 0)
    box(cut, 7.6, 18, hy, 4, G.H - 0.45, G.H)
    world(bg, 1.0)
    area((5, -6, 8), (5, 0, 1), energy=2500, size=8, col="#FFFFFF")
    area((5, 4, 6), (5, 0, 1), energy=600, size=6, col="#FFFFFF")


# ======================================================================== 作業台（C）：外した段・段 3 枚の模型
def bench_room():
    """機械の部屋の作業場（明るい作業の明かり）。床 z=0"""
    cube(mat("wfloor", "#8C9096", rough=0.8), (0, 0, -0.05), (12, 10, 0.1))
    cube(mat("wwall", "#5E646B", rough=0.85), (0, 3.0, 2.0), (12, 0.2, 4.0))
    world("#3B4148", 0.35)
    area((0, -2.5, 4.0), (0, 0.5, 0.4), energy=1500, size=4, col="#FFF1DC")
    area((-3, 1.0, 3.5), (0, 0.5, 0.3), energy=500, size=3, col="#FFE2B8")


class Model3:
    """段 3 枚と 2 本のレール（坂 30°）。段の回り角を変えると、後ろの車輪が前のレール上（傾く）か後ろのレール上（水平）になる"""

    def __init__(self, origin=(0.0, 0.0, 0.0)):
        ox, oy, oz = origin
        self.o = origin; self.steps = []
        a = G.ANG
        self.L = 2.4
        x0, z0 = ox - 0.3, oz + 0.45
        self.front_line = [(x0 + u * math.cos(a), z0 + u * math.sin(a)) for u in (0.0, self.L)]
        # 後ろのレール：段が水平のとき、後ろの車輪が通る線（前の線を REAR だけずらす）
        rx, rz = G.REAR
        self.rear_line = [(x + rx, z + rz) for x, z in self.front_line]
        for sy in (-1, 1):
            tube("m_rail_f%d" % sy, self.front_line, 0.014, M["rail_f"], y=oy + sy * Y_FW)
            tube("m_rail_r%d" % sy, self.rear_line, 0.014, M["rail_r"], y=oy + sy * Y_RW)
        # 脚（台）
        for u in (0.2, self.L - 0.2):
            x, z = x0 + u * math.cos(a), z0 + u * math.sin(a)
            for sy in (-1, 1):
                cube(M["frame"], (x, oy + sy * (Y_RW + 0.04), (z + oz) / 2 - 0.04), (0.06, 0.06, z - oz))
        self.base = [(x0 + (0.45 + 0.75 * i) * math.cos(a), z0 + (0.45 + 0.75 * i) * math.sin(a)) for i in range(3)]
        for i in range(3):
            st = make_step(100 + i); st.location = (self.base[i][0], oy, self.base[i][1]); self.steps.append(st)

    def set_rot(self, t, deg, interp="BEZIER"):
        for st in self.steps: key(st, ("rotation_euler", 1), t, math.radians(deg), interp)

    def tread(self, i, deg=0.0, lx=-0.18):
        x, z = self.base[i]; wx, wz = G.local_to_world(x, z, deg, lx, G.TREAD_DZ)
        return (wx, self.o[1], wz)
