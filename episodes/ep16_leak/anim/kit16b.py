# 16本目 2章：お城の中（舞台 D）の部品。scenes.py が kit16.py のあとに exec で読む
#   まっすぐな廊下 1 本（x 0〜IN_L・y −IN_W/2〜+IN_W/2）。奥のかべ（y=+）に扉が 6 つ。手前（y=−）は窓のあるかべと柱。
#   扉の奥には部屋の箱（使い回し）。働く人の部屋・管理する人の部屋・名札の倉庫・予備の倉庫に中身を入れる。持ち主の部屋は別の所（OWN）。
#   決まり：3D の中に字を書かない。影の錠と鍵束は赤。名札＝白（お客さん）・青緑（まるロボ）。予備の倉庫の名札は少し薄い色。
#   絵コンテ表：../絵コンテ_v1.md の「2章」
IN_L = 18.0        # 廊下の長さ
IN_W = 3.2         # 廊下のはば
IN_H = 3.2         # 天井の高さ
WALL_T = 0.3       # 奥のかべの厚み（y = IN_W/2 〜 IN_W/2 + WALL_T）
ID_W, ID_H = 1.05, 2.0     # 部屋の扉
IDOORS = [("work", 2.6), ("admin", 5.2), ("hall2", 7.8), ("tags", 10.4), ("backup", 13.0), ("hall5", 15.6)]
ROOM_D = 3.0       # 部屋の奥行き
ROOM_W = 2.5
YB = IN_W / 2      # 奥のかべの廊下側の面
IN = {}            # 作った物（扉の蝶つがい・まん中・錠・印・窓の材質など）
OWN = (40.0, 0.0)  # 持ち主の部屋のまん中（廊下から離れた所）


def _inmat(name, col, **kw): return mat("in_" + name, col, **kw)


def _floor_mat(): return noise_mat("in_floor", "#8A6A4C", "#7A5C40", 2.0, 0.7, wave=True)


def _wall_mat(): return noise_mat("in_wall", "#B9AF9F", "#AAA090", 3.0, 0.9)


def _room_box(cx, y0, w, d, h, light_col="#FFE2B8", light_e=0.0, name="room"):
    """部屋の箱（床・3 つのかべ・天井）。y0＝入口側のかべの奥の面。返す：明かり（energy を時刻で替える）"""
    fm, wm = _floor_mat(), _wall_mat()
    if name == "backup": wm = noise_mat("in_wall_b", "#9FB2C6", "#93A6BA", 3.0, 0.9); fm = noise_mat("in_floor_b", "#6E7A86", "#64707C", 2.0, 0.8)      # 予備の倉庫：青みのかべと灰色の床（確認役：名札の倉庫と同じ絵で見分けがつかない）
    cube(fm, (cx, y0 + d / 2, -0.02), (w, d, 0.04))
    cube(wm, (cx, y0 + d + 0.1, h / 2), (w + 0.4, 0.2, h))
    cube(wm, (cx - w / 2 - 0.1, y0 + d / 2, h / 2), (0.2, d, h))
    cube(wm, (cx + w / 2 + 0.1, y0 + d / 2, h / 2), (0.2, d, h))
    cube(_inmat("ceil", "#8F877B", rough=0.9), (cx, y0 + d / 2, h + 0.05), (w + 0.4, d, 0.1))
    bpy.ops.object.light_add(type='POINT', location=(cx, y0 + d / 2, h - 0.4)); L = bpy.context.object
    L.data.energy = light_e; L.data.color = srgb(light_col)[:3]; L.data.shadow_soft_size = 0.6; L.name = "L_" + name
    return L


def _door(x, name):
    """廊下の奥のかべの扉。蝶つがいは左の端（廊下側の面）。開くと部屋の中（+y）へ回る（rotation z を +）"""
    wood = noise_mat("in_door", "#6E5034", "#5E4430", 1.2, 0.8, wave=True)
    if name == "backup": wood = noise_mat("in_door_b", "#4E6A82", "#44607A", 1.2, 0.8, wave=True)      # 予備の倉庫の扉は青い（確認役）
    hg = empty((x - ID_W / 2 + 0.02, YB + 0.05, 0.0))
    cube(wood, (ID_W / 2 - 0.01, 0.0, ID_H / 2), (ID_W - 0.06, 0.06, ID_H - 0.02), parent=hg)
    cyl(_inmat("knob", "#C9A24A", rough=0.3, metal=0.8), (ID_W - 0.16, -0.05, 1.0), 0.035, 0.05, rot=(R(90), 0, 0), parent=hg)
    c = empty((0, 0, 0)); c.parent = hg; c.location = (ID_W / 2, -0.04, 1.05)      # 扉のまん中（印・錠・音の印）
    IN["door_" + name] = hg; IN["dc_" + name] = c
    return hg


def red_lock(name, s=1.0):
    """影の赤い錠（1章の古い錠と同じ形。赤くつやのある物）。扉のまん中の少し下、廊下側に付ける。はじめは見えない（scale 0.001）"""
    hg = IN["door_" + name]
    root = empty((0, 0, 0)); root.parent = hg; root.location = (ID_W - 0.3, -0.09, 0.95); root.scale = (0.001, 0.001, 0.001)
    rm = _inmat("redlock", "#D2262A", rough=0.25, metal=0.4, emit=0.5)      # 暗い廊下でも赤い錠が見えるように、少し光らせる
    cube(rm, (0, 0, 0), (0.16 * s, 0.06 * s, 0.13 * s), bevel=0.01, parent=root)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0.09 * s), rotation=(R(90), 0, 0), major_radius=0.05 * s, minor_radius=0.012 * s)
    o = bpy.context.object; o.data.materials.append(_inmat("redshackle", "#9E1E22", rough=0.3, metal=0.7)); o.parent = root
    cyl(_inmat("keyhole", "#1A1410", rough=0.7), (0, -0.031 * s, -0.01 * s), 0.012 * s, 0.004, rot=(R(90), 0, 0), parent=root, verts=16)
    IN["lock_" + name] = root
    return root


def red_mark(name):
    """扉に付ける赤い × の印（はじめは見えない）"""
    hg = IN["door_" + name]
    root = empty((0, 0, 0)); root.parent = hg; root.location = (ID_W / 2, -0.04, 1.55); root.scale = (0.001, 0.001, 0.001)
    mm = _inmat("mark", "#E0322C", rough=0.5, emit=0.6)
    cyl(mm, (0, 0, 0), 0.13, 0.012, rot=(R(90), 0, 0), parent=root, verts=32)        # 赤い丸の印（確認役：×だと「ダメ」「使えない」に見えた）
    cyl(_inmat("markin", "#FFFFFF", rough=0.6), (0, -0.007, 0), 0.06, 0.004, rot=(R(90), 0, 0), parent=root, verts=24)
    IN["mark_" + name] = root
    return root


def key_bundle(loc=(0, 0, 0), parent=None, s=1.0):
    """管理する人の鍵束（赤い大きな輪に、赤い鍵が 5 本）"""
    e = empty(loc); e.scale = (s, s, s)
    if parent is not None: e.parent = parent
    rm = _inmat("bundle", "#D2262A", rough=0.25, metal=0.6)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), rotation=(R(90), 0, 0), major_radius=0.07, minor_radius=0.012)
    o = bpy.context.object; o.data.materials.append(rm); o.parent = e
    for k in range(5):
        a = R(-60 + k * 30)
        kk = key_obj((0.07 * math.sin(a), 0, -0.07 * math.cos(a)), rot=(0, R(90) - a, 0), col="#C8282C", s=0.9, parent=e)
    return e


def tag_shelf(cx, y_back, tex="tag_cust", n_rows=3, n_cols=7, special=None, metal=False):
    """名札の棚（奥のかべに沿って。名札を立てて並べる）。special＝(段, 列) の所だけ tag_maru。metal＝灰色の金属の棚（予備の倉庫）"""
    wood = _inmat("shelf", "#7A5A3C", rough=0.7) if not metal else _inmat("shelf_m", "#8C939C", rough=0.35, metal=0.6)
    W_, D_ = n_cols * 0.32 + 0.2, 0.4
    tags = []
    for r in range(n_rows + 1):
        cube(wood, (cx, y_back - D_ / 2, 0.35 + r * 0.55), (W_, D_, 0.04))
    for sx in (-1, 1):
        cube(wood, (cx + sx * W_ / 2, y_back - D_ / 2, 0.35 + n_rows * 0.55 / 2), (0.04, D_, n_rows * 0.55 + 0.04))
    for r in range(n_rows):
        for c in range(n_cols):
            tx = tex if special != (r, c) else "tag_maru"
            t_ = nameplate((cx - W_ / 2 + 0.26 + c * 0.32, y_back - D_ / 2, 0.37 + r * 0.55 + 0.12), rot=(R(80), 0, 0), tex=tx, w=0.26)
            tags.append(t_)
    return tags


def calendar(x, n=4):
    """かべのカレンダー（数字なし。紙の色だけ）。上の端を軸に、1 枚ずつ上へめくれる。返す：めくる紙の蝶つがい（手前の 1 枚目から）"""
    base = empty((x, YB - 0.01, 1.75))
    cube(_inmat("calback", "#5B4636", rough=0.8), (0, 0.0, 0.0), (0.5, 0.02, 0.62), parent=base)
    pages = []
    cols = ["#F6F1E6", "#EFE7D6", "#F6F1E6", "#EFE7D6", "#F6F1E6"]
    for k in range(n + 1):
        hg = empty((0, -0.012 - 0.003 * (n - k), 0.3)); hg.parent = base
        pg = cube(_inmat("calpage%d" % k, cols[k % len(cols)], rough=0.9), (0, 0, -0.28), (0.44, 0.002, 0.54), parent=hg)
        cube(_inmat("calred", "#C84B4B", rough=0.8), (0, -0.002, -0.06), (0.44, 0.002, 0.1), parent=hg)    # 上の赤い帯（字なし）
        for j in range(4):
            cube(_inmat("calline", "#B8AE9C", rough=0.9), (0, -0.002, -0.17 - j * 0.09), (0.36, 0.002, 0.012), parent=hg)
        pages.append(hg)
    pages.reverse()           # pages[0]＝いちばん手前（先にめくる）
    return pages


def inside(night=True):
    """廊下と、扉の奥の部屋の箱。night＝はじめの明るさ（時刻で替えるのは day_night()）"""
    world("#0E1220", 0.45)
    fm, wm = _floor_mat(), _wall_mat()
    cube(fm, (IN_L / 2, 0, -0.02), (IN_L + 2, IN_W + 0.4, 0.04))
    cube(_inmat("ceil", "#8F877B", rough=0.9), (IN_L / 2, 0, IN_H + 0.05), (IN_L + 2, IN_W + 0.8, 0.1))
    # 奥のかべ（扉の所に穴）
    xs = [-1.0]
    for nm, x in IDOORS: xs += [x - ID_W / 2, x + ID_W / 2]
    xs.append(IN_L + 1.0)
    yc = YB + WALL_T / 2
    for k in range(len(xs) - 1):
        x0, x1 = xs[k], xs[k + 1]
        if k % 2 == 0: cube(wm, ((x0 + x1) / 2, yc, IN_H / 2), (x1 - x0, WALL_T, IN_H))
        else: cube(wm, ((x0 + x1) / 2, yc, (ID_H + IN_H) / 2), (x1 - x0, WALL_T, IN_H - ID_H))
    # 扉の枠（木）と扉と部屋の箱
    fr = _inmat("frame", "#5A4330", rough=0.7)
    for nm, x in IDOORS:
        for sx in (-1, 1): cube(fr, (x + sx * (ID_W / 2 + 0.04), YB - 0.02, ID_H / 2), (0.08, 0.06, ID_H))
        cube(fr, (x, YB - 0.02, ID_H + 0.04), (ID_W + 0.16, 0.06, 0.08))
        _door(x, nm)
        IN["room_" + nm] = _room_box(x, YB + WALL_T, ROOM_W, ROOM_D, IN_H, name=nm)
    # 手前のかべ（窓が 6 つ）と柱
    ya = -IN_W / 2 - 0.15
    WX = [2.6 + k * 2.6 for k in range(6)]            # 窓は扉の向かい。柱は扉と扉の間（扉が柱に隠れない）
    xs = [-1.0]
    for x in WX: xs += [x - 0.45, x + 0.45]
    xs.append(IN_L + 1.0)
    for k in range(len(xs) - 1):
        x0, x1 = xs[k], xs[k + 1]
        if k % 2 == 0: cube(wm, ((x0 + x1) / 2, ya, IN_H / 2), (x1 - x0, 0.3, IN_H))
        else:
            cube(wm, ((x0 + x1) / 2, ya, 0.45), (x1 - x0, 0.3, 0.9)); cube(wm, ((x0 + x1) / 2, ya, (2.5 + IN_H) / 2), (x1 - x0, 0.3, IN_H - 2.5))
    wmat = bpy.data.materials.new("in_window"); wmat.use_nodes = True
    b = wmat.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.02, 0.03, 0.06, 1)
    b.inputs["Emission Color"].default_value = srgb("#6F86C8"); b.inputs["Emission Strength"].default_value = 0.6
    IN["win_mat"] = wmat
    for x in WX:
        cube(wmat, (x, ya - 0.1, 1.7), (0.9, 0.04, 1.6))
        cube(fr, (x, ya + 0.05, 1.7), (0.06, 0.04, 1.6)); cube(fr, (x, ya + 0.05, 1.7), (0.9, 0.04, 0.06))
    IN["pillars"] = [1.3 + k * 2.6 for k in range(7)]
    for px in IN["pillars"]:
        cube(_stone(), (px, -IN_W / 2 + 0.35, IN_H / 2), (0.42, 0.42, IN_H))     # 柱（扉と扉の間。まるロボがかげに隠れる）
    # はじめのかべ（x=0。裏口からの通路の出口）とつきあたりのかべ（x=IN_L。窓）
    # 出口は y −0.35〜0.85（はば 1.2 m）。v2 の入りこみの点検：かべが出口にかかり、通路が詰まった箱で、影がめりこんだ → かべを出口の外だけにし、通路は中が空の箱に
    cube(wm, (-0.15, -1.125, IN_H / 2), (0.3, 1.55, IN_H)); cube(wm, (-0.15, 1.375, IN_H / 2), (0.3, 1.05, IN_H))
    cube(wm, (-0.15, 0.25, (ID_H + IN_H) / 2), (0.3, 1.2, IN_H - ID_H))
    pm = _inmat("passage", "#06070A", rough=1.0)
    cube(pm, (-1.6, 0.25, -0.02), (2.6, 1.6, 0.04)); cube(pm, (-1.6, 0.25, ID_H + 0.05), (2.6, 1.6, 0.1))
    cube(pm, (-1.6, -0.45, ID_H / 2), (2.6, 0.1, ID_H)); cube(pm, (-1.6, 0.95, ID_H / 2), (2.6, 0.1, ID_H)); cube(pm, (-2.95, 0.25, ID_H / 2), (0.1, 1.6, ID_H))   # 暗い通路（裏口へ）
    cube(wm, (IN_L + 0.15, 0, IN_H / 2), (0.3, IN_W + 0.4, IN_H))
    ewm = bpy.data.materials.new("in_endwin"); ewm.use_nodes = True
    b = ewm.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.02, 0.03, 0.06, 1)
    b.inputs["Emission Color"].default_value = srgb("#6F86C8"); b.inputs["Emission Strength"].default_value = 0.8
    IN["endwin_mat"] = ewm
    cube(ewm, (IN_L - 0.02, 0.0, 1.8), (0.04, 1.2, 1.4))
    cube(fr, (IN_L - 0.05, 0.0, 1.8), (0.04, 0.06, 1.4)); cube(fr, (IN_L - 0.05, 0.0, 1.8), (0.04, 1.2, 0.06))
    # 明かり：月の光（手前の窓から）・廊下の小さなランプ 3 つ・昼の光（はじめは 0）
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10)); sn = bpy.context.object
    sn.rotation_euler = (R(60), 0, R(15)); sn.data.energy = 0.6; sn.data.color = srgb("#AFC4FF")[:3]; sn.data.angle = R(4)
    IN["moon"] = sn
    lamps = []
    for x in (3.9, 9.1, 14.3):
        bpy.ops.object.light_add(type='POINT', location=(x, YB - 0.25, 2.3)); L = bpy.context.object
        L.data.energy = 45; L.data.color = srgb("#FFDDB2")[:3]; L.data.shadow_soft_size = 0.3
        cyl(glow_mat("in_lamp", "#FFC27A", 3.0), (x, YB - 0.12, 2.3), 0.05, 0.14)
        lamps.append(L)
    IN["lamps"] = lamps
    a = area((IN_L / 2, -IN_W / 2 - 3.0, 2.6), (IN_L / 2, 0.5, 1.0), energy=0.0, size=12, col="#FFF1DC"); a.visible_camera = False
    IN["dayfill"] = a
    return IN


def day_night(keys):
    """keys：[(時刻, "day"|"night"), …]。窓の光・月・昼の光・ランプを時刻で替える（0.5 秒で）"""
    wm, ewm, sn, a = IN["win_mat"], IN["endwin_mat"], IN["moon"], IN["dayfill"]
    wb = wm.node_tree.nodes["Principled BSDF"]; eb = ewm.node_tree.nodes["Principled BSDF"]
    DAY = dict(wc=srgb("#FFF6DA"), ws=6.0, moon=0.0, fill=900.0, lamp=0.0)
    NIGHT = dict(wc=srgb("#22346E"), ws=0.45, moon=0.6, fill=120.0, lamp=45.0)      # 試しの絵：夜の廊下が暗くて錠・扉が見えなかった。窓は濃い紺（確認役 2 回目：明るい水色で昼の空に見えた）
    prev = None
    for t, kind in keys:
        v = DAY if kind == "day" else NIGHT
        for tt, vv in (((t - 0.5, prev) if prev else (None, None)), (t, v)):
            if tt is None: continue
            fr_ = f(tt)
            for bb in (wb, eb):
                bb.inputs["Emission Color"].default_value = vv["wc"]; bb.inputs["Emission Color"].keyframe_insert("default_value", frame=fr_)
                bb.inputs["Emission Strength"].default_value = vv["ws"]; bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr_)
            sn.data.energy = vv["moon"]; sn.data.keyframe_insert("energy", frame=fr_)
            a.data.energy = vv["fill"]; a.data.keyframe_insert("energy", frame=fr_)
            for L in IN["lamps"]:
                L.data.energy = vv["lamp"]; L.data.keyframe_insert("energy", frame=fr_)
        prev = v


def light_key(L, t, e_):
    L.data.energy = e_; L.data.keyframe_insert("energy", frame=f(t))


def work_room(people=True):
    """働く人の部屋（扉 work の奥）：机 2 つ・画面・座った働く人 2 人（後ろ姿。people のとき）。返す：画面の材質（赤く固まるのに使う）"""
    x0 = dict(IDOORS)["work"]; y0 = YB + WALL_T
    desk = _inmat("desk", "#8B6B4A", rough=0.6)
    scr_mats = []
    for k, dx in enumerate((-0.6, 0.6)):
        cube(desk, (x0 + dx, y0 + 2.2, 0.74), (1.0, 0.6, 0.05))
        for sx in (-1, 1): cube(desk, (x0 + dx + sx * 0.45, y0 + 2.2, 0.37), (0.05, 0.55, 0.72))
        cube(_inmat("mon", "#22262C", rough=0.4), (x0 + dx, y0 + 2.38, 1.02), (0.5, 0.03, 0.34))
        sm = bpy.data.materials.new("in_screen%d" % k); sm.use_nodes = True
        bb = sm.node_tree.nodes["Principled BSDF"]; bb.inputs["Base Color"].default_value = (0, 0, 0, 1)
        bb.inputs["Emission Color"].default_value = srgb("#CFE6FF"); bb.inputs["Emission Strength"].default_value = 1.6
        cube(sm, (x0 + dx, y0 + 2.36, 1.02), (0.46, 0.01, 0.3))
        scr_mats.append(sm)
        if people: person((x0 + dx, y0 + 1.6, 0.0), 180.0, shirt=["#5A7BA8", "#A86A5A"][k], sit=True)
    IN["work_screens"] = scr_mats
    cube(IN["win_mat"], (x0 - 1.2, y0 + 1.4, 1.8), (0.04, 1.0, 1.1))       # 左のかべの窓（確認役：昼か分からない）
    return scr_mats


def admin_room():
    """管理する人の部屋（扉 admin の奥）：大きな机と、手前に出る引き出し。返す：引き出し（y を手前に動かす）"""
    x0 = dict(IDOORS)["admin"]; y0 = YB + WALL_T
    desk = _inmat("bigdesk", "#6B4A30", rough=0.55)
    cube(desk, (x0, y0 + 1.9, 0.78), (1.6, 0.8, 0.06))
    cube(desk, (x0 - 0.55, y0 + 1.9, 0.38), (0.5, 0.75, 0.76))
    cube(desk, (x0 + 0.75, y0 + 1.9, 0.38), (0.06, 0.75, 0.76))
    dr = empty((x0 - 0.55, y0 + 1.55, 0.62))
    cube(_inmat("drawer", "#7C573A", rough=0.5), (0, 0, 0), (0.46, 0.04, 0.2), parent=dr)
    cube(_inmat("drawer_in", "#4A3424", rough=0.8), (0, 0.3, -0.06), (0.42, 0.6, 0.02), parent=dr)
    cyl(_inmat("knob", "#C9A24A", rough=0.3, metal=0.8), (0, -0.04, 0), 0.025, 0.04, rot=(R(90), 0, 0), parent=dr)
    cube(_inmat("chair", "#3F3A36", rough=0.7), (x0, y0 + 2.6, 0.5), (0.5, 0.5, 1.0))
    IN["drawer"] = dr
    return dr


def store_room(name, tex, special=None, pale=False):
    """名札の倉庫・予備の倉庫（扉の奥。奥のかべに沿って棚 1 つ）"""
    x0 = dict(IDOORS)[name]; y0 = YB + WALL_T
    tags = tag_shelf(x0, y0 + ROOM_D - 0.05, tex=tex, special=special, metal=(name == "backup"))
    IN["tags_" + name] = tags
    return tags


def owner_room():
    """持ち主の部屋（OWN）：大きな机・座った持ち主（後ろ姿。紫の服）・窓。返す：机の上の手紙を置く所（empty）"""
    ox, oy = OWN
    fm, wm = _floor_mat(), _wall_mat()
    cube(fm, (ox, oy, -0.02), (6, 6, 0.04))
    for (cx, cy, sx, sy) in ((ox, oy + 3.0, 6, 0.2), (ox - 3.0, oy, 0.2, 6), (ox + 3.0, oy, 0.2, 6), (ox, oy - 3.0, 6, 0.2)):      # 手前のかべも（17-04：まるロボの前から撮ると、かべのない所が黒く映った）
        cube(wm, (cx, cy, IN_H / 2), (sx, sy, IN_H))
    cube(_inmat("ceil", "#8F877B", rough=0.9), (ox, oy, IN_H + 0.05), (6.4, 6.4, 0.1))
    cube(_inmat("rug", "#7A2E3A", rough=0.9), (ox, oy + 0.8, 0.005), (3.2, 2.4, 0.01))
    desk = _inmat("ownerdesk", "#5A3A24", rough=0.5)
    cube(desk, (ox, oy + 1.6, 0.78), (2.0, 0.9, 0.06)); cube(desk, (ox, oy + 1.95, 0.4), (1.9, 0.1, 0.78))
    for sx in (-1, 1): cube(desk, (ox + sx * 0.9, oy + 1.6, 0.4), (0.12, 0.8, 0.78))
    p = person((ox, oy + 0.95, 0.0), 180.0, shirt="#5B3F7A", sit=True)        # 後ろ姿（机のほう＝+y を向く。試しの絵：0 では正面を向いていた）
    ow = bpy.data.materials.new("in_ownwin"); ow.use_nodes = True
    bb = ow.node_tree.nodes["Principled BSDF"]; bb.inputs["Emission Color"].default_value = srgb("#FFF0D0"); bb.inputs["Emission Strength"].default_value = 3.0
    cube(ow, (ox, oy + 2.88, 1.8), (1.4, 0.04, 1.2))
    bpy.ops.object.light_add(type='POINT', location=(ox, oy + 0.6, 2.6)); L = bpy.context.object
    L.data.energy = 140; L.data.color = srgb("#FFE2B8")[:3]; L.data.shadow_soft_size = 0.8
    a = area((ox, oy - 2.6, 2.4), (ox, oy + 1.6, 0.8), energy=220, size=3, col="#FFF1DC"); a.visible_camera = False
    pad = empty((ox, oy + 1.45, 0.815))
    return pad


def letter(loc, parent=None, col="#F4EEDC"):
    """手紙（封筒）。前＝上（+z）"""
    e = empty(loc)
    if parent is not None: e.parent = parent
    cube(_inmat("env", col, rough=0.8), (0, 0, 0), (0.3, 0.2, 0.006), parent=e)
    cube(_inmat("seal", "#C8282C", rough=0.5), (0, 0, 0.005), (0.05, 0.05, 0.004), rot=(0, 0, R(45)), parent=e)    # 赤い封（影から）
    return e


def tag_box(loc):
    """名札を入れる箱（ふたのない木の箱）"""
    e = empty(loc)
    bm_ = _inmat("box", "#A0784E", rough=0.8)
    cube(bm_, (0, 0, 0.01), (0.5, 0.36, 0.02), parent=e)
    for (x, y, sx, sy) in ((0, 0.17, 0.5, 0.02), (0, -0.17, 0.5, 0.02), (0.24, 0, 0.02, 0.36), (-0.24, 0, 0.02, 0.36)):
        cube(bm_, (x, y, 0.13), (sx, sy, 0.24), parent=e)
    return e
