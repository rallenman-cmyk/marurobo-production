# 会話と広告の回：台本 v1.0 の絵コンテ（場面ごとに 1 枚。字のない 3D。字幕と札は board_overlay.py で重ねる）
# blender -b --factory-startup --python board.py -- <b00..b22> <out.png> [samples]
# 2D の場面（b03・b09・b20）は board_overlay.py が PIL で描く（ここでは描かない）
# まるロボは見た目を似せた仮のモデル。見張り番は番犬（guards.py の dog）
import os, math, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "gate.py"), encoding="utf-8").read()
exec(_src.split("\ndef guard(")[0])  # scenes.py の部品・bubble・burst
_g = open(os.path.join(HERE, "guards.py"), encoding="utf-8").read()
exec(_g[_g.index("def closed_eye"):_g.index("def owl")])
exec(_g[_g.index("def dog"):_g.index("def chip")])
NAVY, DARK, GOLD = "#2F4A73", "#14243A", "#F2C14E"
_sc = open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read()
exec(_sc[_sc.index("def s2_suspects"):_sc.index("SCENES = dict")])  # 元の場面（部品として使う）
R = math.radians


# ---------------- 部品
def phone(loc, rz=0.0, screen="phone_ad.png", glow=2.5, s=1.0, holes=True, lie=True, tilt=0.0):
    e = empty(loc, R(rz), s)
    if not lie:
        e.rotation_euler = (R(90 - tilt), 0, R(rz))
    cube(mat("ph_body", "#22262B", rough=0.3, metal=0.2), (0, 0, 0.02), (0.36, 0.74, 0.04), bevel=0.03, parent=e)
    if screen:
        p = plane(img_mat("ph_" + screen, os.path.join(HERE, screen), emit=glow), (0, 0, 0.041), (0.32, 0.66), parent=e)
        p.rotation_euler = (0, 0, R(180))
    else:
        plane(mat("ph_off", "#0B0E12", rough=0.15, coat=1.0), (0, 0, 0.041), (0.32, 0.66), parent=e)
    if holes:  # 下の端のマイクの穴（6 つ）
        hm = mat("ph_hole", "#05070A", rough=0.8)
        for i in range(6):
            cyl(hm, ((i - 2.5) * 0.028, -0.371, 0.02), 0.008, 0.01, rot=(R(90), 0, 0), verts=12, parent=e)
    return e


def room(night=True, hook_hat=False, wall=True):
    if night:
        world("#0C1426", 0.15)
    else:
        world("#F3E6D2", 0.7)
    ground("#2A2F45" if night else "#B9A58A", size=20)
    cube(mat("futon", "#E9E2D4", rough=0.9), (0, 0.4, 0.12), (2.4, 1.6, 0.24), bevel=0.1)
    cube(mat("blanket", "#5B7DB8", rough=0.9), (0, 0.6, 0.27), (2.3, 1.2, 0.12), bevel=0.06)
    cube(mat("pillow", "#F4F1EA", rough=0.9), (0, -0.25, 0.32), (0.8, 0.35, 0.16), bevel=0.07)
    if wall:
        cube(mat("wall", "#3A4766" if night else "#F1E7D8", rough=0.9), (0, 2.0, 1.5), (8, 0.1, 3))
        # 窓
        cube(mat("winf", "#C9C2B5", rough=0.4), (-1.9, 1.94, 1.6), (1.1, 0.03, 0.9))
        cube(mat("winsky", "#1C2B55" if night else "#BFE3F2", emit=0.6 if night else 1.2), (-1.9, 1.92, 1.6), (1.0, 0.02, 0.8))
    if hook_hat:
        cyl(mat("hook", "#8A6A48", rough=0.4, metal=0.4), (1.4, 1.85, 1.55), 0.03, 0.25, rot=(R(80), 0, 0))
    return


def hat_on_hook(loc):
    plaid = checker_mat("hat_plaid2", "#B88A55", "#8A6239", 9)
    e = empty(loc)
    sphere(plaid, (0, 0, 0), 0.3, scale=(1, 1.0, 0.7), parent=e)
    cyl(mat("hat_band2", "#5B3B22", rough=0.6), (0, 0, -0.05), 0.302, 0.06, parent=e)
    cyl(plaid, (0, -0.3, -0.05), 0.17, 0.03, rot=(R(-18), 0, 0), scale=(1.05, 0.62, 1), parent=e)


def person_lie(loc):
    # ふとんで寝ている人（頭と、ふくらんだ毛布）
    sphere(mat("skin", "#F1C7A5", rough=0.55), (loc[0], loc[1], loc[2]), 0.2)
    sphere(mat("hair#2B2220", "#2B2220", rough=0.6), (loc[0], loc[1] + 0.05, loc[2] + 0.04), 0.205)
    sphere(mat("blanket", "#5B7DB8", rough=0.9), (loc[0], loc[1] + 0.75, loc[2] - 0.05), 0.5, scale=(0.9, 1.4, 0.35))


def towel(loc, rz=0.0):
    e = empty(loc, R(rz))
    t = cube(mat("towel", "#F5B7C5", rough=0.95), (0, 0, 0.02), (0.6, 0.5, 0.05), bevel=0.02, parent=e)
    cube(mat("towel_l", "#F8D3DC", rough=0.95), (0, -0.18, 0.05), (0.6, 0.06, 0.02), parent=e)
    return e


def city_floor():
    world("#0E1A2B", 0.3)
    ground("#14263B", rough=0.4)
    line = mat("circuit", "#2CD3C2", rough=0.4, emit=2.2)
    for x in (-3.5, -1.8, 1.8, 3.5):
        cube(line, (x, 3, 0.005), (0.05, 14, 0.01))
    for y in (-1.2, 0.6, 3.5, 6.5):
        cube(line, (0, y, 0.005), (14, 0.05, 0.01))
    bm = mat("chipb", "#22354D", rough=0.5)
    for x, y, h in ((-4.2, 7, 2.2), (-2.6, 9, 3.0), (3.2, 8, 2.6), (4.8, 6, 1.6), (0.9, 11, 3.6), (-5.5, 4, 1.8), (5.8, 3, 2.4)):
        cube(bm, (x, y, h / 2), (1.4, 1.4, h), bevel=0.05)
        cube(mat("chipwin", "#5BE0D3", emit=1.5), (x, y - 0.71, h * 0.7), (0.9, 0.01, 0.08))


def mic_gate(open_=False, lamp=False):
    pil = mat("gatep", "#C7D0D6", rough=0.3, metal=0.7)
    for x in (-1.3, 1.3):
        cube(pil, (x, 1.8, 1.3), (0.42, 0.42, 2.6), bevel=0.05)
        lm = mat("lamp_on" if lamp else "lamp_off", "#FF7A00" if lamp else "#5A3A2A", rough=0.3, emit=2.5 if lamp else 0.0)
        sphere(lm, (x, 1.57, 2.42), 0.09)
        if lamp:
            bpy.ops.object.light_add(type='POINT', location=(x, 1.3, 2.42))
            bpy.context.object.data.energy = 60
            bpy.context.object.data.color = srgb("#FF7A00")[:3]
    cube(pil, (0, 1.8, 2.78), (3.2, 0.5, 0.48), bevel=0.06)
    hole = mat("hole", "#0B1220", rough=0.8)
    for cx in (-0.75, 0.75):
        for i in range(6):
            cyl(hole, (cx + (i - 2.5) * 0.16, 1.54, 2.78), 0.05, 0.02, rot=(R(90), 0, 0), verts=16)
    bar = mat("bar", "#8A97A1", rough=0.25, metal=0.9)
    lift = 2.2 if open_ else 0.0
    for i in range(-4, 5):
        cyl(bar, (i * 0.26, 1.8, 1.25 + lift), 0.04, 2.5, verts=16)
    cube(bar, (0, 1.8, 0.05 + lift), (2.3, 0.08, 0.08))


def box(loc, kind, s=1.0, rz=0.0):
    # 手がかりの荷物（橙の箱）：drop＝いた場所／square＝見たページ／two＝一緒にいた人
    e = empty(loc, R(rz), s)
    cube(mat("boxc", "#F2D6A2", rough=0.6), (0, 0, 0.19), (0.38, 0.38, 0.38), bevel=0.03, parent=e)
    mk = mat("mark2", "#F2A93B", rough=0.35, emit=0.6)
    if kind == "drop":
        sphere(mk, (0, -0.2, 0.19), 0.08, scale=(1, 0.3, 1), parent=e)
        add(bpy.ops.mesh.primitive_cone_add, mk, (0, -0.2, 0.28), (R(0), 0, 0), radius1=0.07, radius2=0.0, depth=0.12, vertices=24, scale=(1, 0.3, 1), parent=e)
    elif kind == "square":
        cube(mk, (0, -0.2, 0.19), (0.15, 0.03, 0.15), parent=e)
    else:
        for dx in (-0.06, 0.06):
            sphere(mk, (dx, -0.2, 0.19), 0.06, scale=(1, 0.3, 1), parent=e)
    return e


def mirror(loc, s=1.0, glow=0.0, card=False, maru_in=False):
    # 3人目の台：紫のふちの鏡（映っているのは自分）
    e = empty(loc, 0, s)
    rim = mat("mir_rim", "#8E6CEF", rough=0.3, metal=0.5, emit=0.5 + glow)
    add(bpy.ops.mesh.primitive_torus_add, rim, (0, 0, 0.55), (R(90), 0, 0), major_radius=0.42, minor_radius=0.05, parent=e)
    gl = mat("mir_glass", "#DDE6F0", rough=0.02, metal=1.0)
    cyl(gl, (0, 0.01, 0.55), 0.4, 0.02, rot=(R(90), 0, 0), parent=e)
    cyl(rim, (0, 0.02, 0.06), 0.18, 0.08, parent=e)
    cyl(rim, (0, 0.02, 0.1), 0.03, 0.12, parent=e)
    if card:
        cube(mat("card_tent", "#FFE07A", rough=0.4, emit=2.0), (0, -0.04, 0.55), (0.3, 0.02, 0.2), parent=e)
    return e


def pedestals(lit=(1, 1, 1), third="mirror", items=True):
    world("#1B2733", 0.25)
    ground("#2C3A47", rough=0.5)
    xs = (-2.3, 0.0, 2.3)
    ped = mat("ped", "#E8EEF1", rough=0.35, coat=0.3)
    cols = ("#E5484D", "#F2A93B", "#8E6CEF")
    for x, c, l in zip(xs, cols, lit):
        cyl(ped, (x, 1.2, 0.45), 0.55, 0.9)
        cyl(mat("pedband" + c, c, rough=0.4, emit=0.6 if l else 0.1), (x, 1.2, 0.86), 0.57, 0.08)
        if l:
            spot((x, 0.2, 5.2), (x, 1.2, 1.1), 1400 * l, 32, "#FFF6E8")
    if items:
        grille = mat("grille", "#B9C2C8", rough=0.3, metal=0.9)
        sphere(grille, (xs[0], 1.2, 1.55), 0.26)
        cyl(mat("micband", "#E5484D", rough=0.3, metal=0.3), (xs[0], 1.2, 1.32), 0.17, 0.08)
        cyl(mat("michandle", "#30363C", rough=0.35, metal=0.4), (xs[0], 1.2, 1.1), 0.1, 0.42)
        box((xs[1] - 0.22, 1.2, 0.9), "drop")
        box((xs[1] + 0.22, 1.15, 0.9), "square")
        box((xs[1], 1.2, 1.28), "two")
        mirror((xs[2], 1.2, 0.9))
    return xs


def train_windows():
    # s5_train の窓は壁に埋もれて見えないので、壁の手前に窓（秋の外の景色）を足す
    outside = mat("autumn_f", "#E07A3A", rough=0.9, emit=1.6)
    outside2 = mat("autumn2_f", "#F2C14E", rough=0.9, emit=1.6)
    for x in (-3.6, -1.2, 1.2, 3.6):
        cube(mat("frame_wf", "#B8B2A6", metal=0.6, rough=0.3), (x, 1.485, 1.6), (1.9, 0.02, 0.95))
        cube(outside if x < 0 else outside2, (x, 1.47, 1.5), (1.75, 0.02, 0.55))
        cube(mat("sky_of", "#BFE3F2", emit=1.4), (x, 1.47, 1.92), (1.75, 0.02, 0.25))
        for k in range(5):  # 紅葉の木（丸）
            sphere(mat("leaf%d" % (k % 2), ("#D9472B", "#F2A93B")[k % 2], rough=0.8, emit=1.2), (x - 0.7 + k * 0.35, 1.455, 1.62 + 0.06 * (k % 2)), 0.16, scale=(1, 0.1, 1))


def train(hat=False, maru_window=False, wifi=False, sora_phone_zoom=False):
    s5_train()
    train_windows()
    if wifi:  # 車内の無料 Wi-Fi の機械（天井。扇の印は 2D で重ねる）
        cube(mat("wifi_box", "#F4F4F4", rough=0.4), (0, 0.6, 2.45), (0.5, 0.3, 0.1), bevel=0.03)
        sphere(mat("wifi_led", "#2BB3A6", emit=3.0), (0, 0.44, 2.43), 0.025)


# ---------------- 場面（台本 v1.0 の S00〜S22）
def b00():  # S00 いきなり夜：テントの広告に、まるロボがびくっと
    room(night=True)
    person_lie((0.15, -0.15, 0.42))
    phone((0.35, -0.9, 0.0), 10)
    bpy.ops.object.light_add(type='POINT', location=(0.35, -0.9, 0.6))
    bpy.context.object.data.energy = 60
    bpy.context.object.data.color = srgb("#CFEFFF")[:3]
    maru((-0.25, -1.0, 0), face_deg=40, s=0.42, hat=False, eye_glow=1.6, look_up=-12, jump=0.3, tilt=8)
    area((-3, 2, 3), (0, 0, 0), 120, 2, "#7F9CFF")
    camera((0.3, -3.0, 1.3), (0.0, -0.75, 0.35), lens=38)


def b01():  # S01 電車：ハルさんとソラさん、まるロボはわくわく
    train(wifi=True)


def b02():  # S02 その夜：タオルでマイクをふさぐ
    room(night=True)
    person_lie((0.15, -0.15, 0.42))
    phone((0.35, -0.9, 0.0), 10, screen=None)
    towel((0.38, -1.05, 0.04), 18)
    bpy.ops.object.light_add(type='POINT', location=(0.2, -1.2, 0.8))
    bpy.context.object.data.energy = 25
    bpy.context.object.data.color = srgb("#CFEFFF")[:3]
    maru((-0.25, -1.15, 0), face_deg=35, s=0.42, hat=False, eye_glow=1.0, look_up=-15)
    area((-3, 2, 3), (0, 0, 0), 120, 2, "#7F9CFF")
    area((2, -3, 2.5), (0, -1, 0.3), 60, 2, "#FFE2B8")
    camera((0.35, -3.0, 1.3), (0.1, -0.9, 0.3), lens=40)


def b04():  # S04 フックの帽子をかぶって探偵に
    room(night=False, hook_hat=True)
    maru((1.35, 1.35, 0.3), face_deg=190, s=0.55, eye_glow=1.4, look_up=-8, jump=0.4)
    sun((50, 0, 200), 2.0)
    area((0, -3, 2.5), (1.2, 1.2, 1.2), 350, 3, "#FFF1DD")
    camera((0.2, -2.6, 1.2), (1.1, 1.3, 0.95), lens=38)


def b05():  # S05 容疑者は3人（③は紫のふちの鏡）
    pedestals()
    maru((0.95, -0.9, 0), face_deg=150, s=0.7, eye_glow=1.3, look_up=14, tilt=-6)
    area((0, -4, 3), (0, 0.5, 1), 220, 4, "#A9C8FF")
    camera((0.4, -5.6, 2.1), (0.1, 0.8, 1.05), lens=34)


def b06():  # S06 スマホの下の小さな穴をのぞく
    world("#0C1426", 0.15)
    ground("#E9E2D4", size=20)
    phone((0, 0, 0.0), 0, screen=None, s=3.0)
    maru((-0.55, -1.5, 0), face_deg=60, eye_glow=1.6, look_up=-12, s=0.5)
    area((-2, -3, 3), (-0.5, 0, 0), 300, 3, "#BFD9FF")
    area((2, 2, 2), (0, 0, 0), 80, 2, "#7F9CFF")
    camera((0.4, -3.1, 0.75), (-0.25, -1.15, 0.12), lens=38)


def b07():  # S07 マイクの門と、見張り番の番犬（目を閉じて待つ）
    city_floor()
    mic_gate()
    ear = dog((2.35, 1.0, 0), -40, eyes="closed")
    bubble((0.2, 1.5, 1.6), 0.3, "icon_clock.png")
    bubble((1.05, 1.0, 2.05), 0.3, "icon_car.png")
    burst((1.8, 0.3, 2.45), 0.3, seed=3)
    maru((-1.7, -0.5, 0), face_deg=55, eye_glow=1.2, look_up=18)
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF")
    area((4, -3, 3), (2.3, 1, 1.5), 250, 3, "#FFE9C7")
    spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    camera((-0.9, -7.6, 2.0), (0.6, 1.0, 1.55), lens=32)


def b08():  # S08 本物の合言葉：番犬がぱっと目を開け、門が開いてランプがオレンジ
    city_floor()
    mic_gate(open_=True, lamp=True)
    dog((2.35, 1.0, 0), -40, eyes="open")
    bubble((0.3, 1.4, 1.7), 0.34, None, glow=1.5)
    maru((-1.7, -0.5, 0), face_deg=40, eye_glow=1.6, look_up=14, jump=0.35)
    bpy.data.materials["maru_orange"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 8.0
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF")
    area((4, -3, 3), (2.3, 1, 1.5), 250, 3, "#FFE9C7")
    spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    camera((-0.9, -7.6, 2.0), (0.6, 1.0, 1.55), lens=32)


def b10():  # S10 出ていく荷物：光る道を箱が次々に
    city_floor()
    road = mat("road", "#2CD3C2", rough=0.3, emit=1.2)
    cube(road, (0, 3, 0.02), (1.0, 16, 0.03))
    for i, (y, k) in enumerate(((-0.4, "drop"), (1.2, "square"), (2.8, "two"), (4.4, "drop"), (6.0, "square"), (7.6, "two"))):
        box((0.0, y, 0.04), k, s=1.3 if i < 3 else 1.0)
    # 出口（遠くの光）
    cube(mat("exit", "#FFFFFF", emit=6.0), (0, 11.5, 1.2), (1.6, 0.05, 2.4))
    maru((-1.3, -1.2, 0), face_deg=-30, eye_glow=1.2, look_up=4)
    area((-2, -4, 3.5), (0, 1, 0.5), 300, 4, "#BFD9FF")
    camera((-2.6, -4.6, 1.6), (0.2, 2.0, 0.5), lens=30)


def b11():  # S11 箱が電波に乗って、町をこえ、山をこえて
    world("#3A4A78", 1.0)
    ground("#22314F", size=200)
    for x, y, h in ((-6, 10, 1.2), (-3, 12, 2.0), (1, 9, 1.4), (5, 11, 2.4), (8, 13, 1.6)):
        cube(mat("town", "#33456B", rough=0.6), (x, y, h / 2), (1.2, 1.2, h), bevel=0.05)
    for x, y, r in ((-8, 30, 6), (0, 34, 9), (10, 30, 7)):
        add(bpy.ops.mesh.primitive_cone_add, mat("mtn", "#2E3F66", rough=0.8), (x, y, r * 0.5), radius1=r, radius2=0.0, depth=r, vertices=6)
    # 光の線（電波の道）
    road = mat("radio", "#2CD3C2", rough=0.3, emit=3.0)
    pts = [(-3, -1, 0.5), (-1, 4, 2.5), (1, 10, 4.2), (2, 18, 6.0), (3, 30, 9.5)]
    for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
        L = math.dist((x0, y0, z0), (x1, y1, z1))
        o = cyl(road, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), 0.05, L, verts=12)
        d = Vector((x1 - x0, y1 - y0, z1 - z0))
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    for t, k in ((0.35, "drop"), (0.6, "square"), (0.8, "two")):
        i = int(t * 4)
        a, b = pts[i], pts[i + 1]
        f = t * 4 - i
        p = tuple(a[j] + (b[j] - a[j]) * f for j in range(3))
        box((p[0], p[1], p[2] + 0.05), k, s=2.6)
    maru((-2.4, -1.2, 0.0), face_deg=-20, eye_glow=1.3, look_up=25, jump=0.2)
    sun((40, 0, 160), 3.0, "#C8D8FF")
    area((-3, -5, 4), (0, 3, 2), 400, 5, "#BFD9FF")
    camera((-4.5, -5.5, 1.8), (0.3, 6.0, 3.0), lens=26)


def b12():  # S12 競り：テントの会社が一番高く、枠にテントの広告
    s4_auction()
    bpy.data.materials["slot"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.0
    p = plane(img_mat("tent_slot", os.path.join(HERE, "tent.png"), emit=1.2), (0, 3.1, 2.3), (1.0, 1.4), rot=(R(90), 0, 0))
    p.scale = (2.3, 1.0, 1.0)
    for k, x in (("drop", -0.5), ("square", 0.0), ("two", 0.5)):
        box((x, 1.4, 0.0), k, s=1.0)


def b13():  # S13 ソラさんのスマホにテントの写真。二人とも電車の Wi-Fi に
    train(wifi=True)
    for o in bpy.data.objects:
        if o.type == 'CAMERA':
            bpy.data.objects.remove(o)
    camera((0.3, -1.35, 1.5), (0.3, 1.0, 1.55), lens=22)


def b14():  # S14 まるロボが窓の外の紅葉に気づく
    _m = globals()["maru"]
    globals()["maru"] = lambda *a, **k: empty()
    s5_train()
    globals()["maru"] = _m
    train_windows()
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA':
            bpy.data.objects.remove(o)
    maru((-3.0, 1.05, 0.5), face_deg=170, s=0.55, hat=False, eye_glow=1.6, look_up=12, jump=0.1)
    camera((-1.6, -0.9, 1.25), (-3.3, 1.4, 1.4), lens=26)


def b15():  # S15 つり広告のテントの絵は 3 枚（引き）
    train()
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA':
            bpy.data.objects.remove(o)
    camera((0.0, -1.45, 1.1), (0.0, 0.8, 1.9), lens=11)


def b16():  # S16 紫の舞台：鏡に残るのはテントの 1 枚、外れのカードは灰色の山
    world("#1E1433", 0.3)
    ground("#2B1F45", rough=0.5)
    mirror((0, 1.0, 0), s=2.6, card=True)
    spot((0, -1, 5), (0, 1, 1.4), 1500, 35, "#E8DDFF")
    import random
    random.seed(5)
    gm = mat("card_grey", "#6D6880", rough=0.7)
    for i in range(46):
        x = 2.4 + random.uniform(-0.7, 0.7)
        y = 1.2 + random.uniform(-0.6, 0.6)
        z = 0.03 + i * 0.022
        cube(gm, (x, y, z), (0.45, 0.3, 0.02), rot=(0, 0, R(random.uniform(0, 180))))
    cols = ["#F6B8C8", "#9BC4E2", "#C9E4B4", "#FFE3A3"]
    for i, x in enumerate((-2.6, -1.8)):
        cube(mat("card_f%d" % i, cols[i], rough=0.5, emit=0.5), (x, 0.6, 1.3 + i * 0.3), (0.45, 0.02, 0.3), rot=(R(10), R(15), 0))
    maru((-1.0, -0.6, 0), face_deg=20, eye_glow=1.2, look_up=22)
    area((-3, -4, 3), (0, 1, 1), 250, 4, "#C8B8FF")
    camera((0.0, -6.2, 2.0), (0.4, 1.0, 1.3), lens=32)


def salesman(loc, headphones=True, list_behind=False):
    e = empty(loc, R(180))
    c = "#4A5568"
    cube(mat("sm_body", c, rough=0.45, coat=0.3), (0, 0, 0.6), (0.55, 0.38, 1.2), bevel=0.14, parent=e)
    sphere(mat("rephead", "#F3E3D3", rough=0.5), (0, 0, 1.45), 0.25, parent=e)
    cube(mat("sm_tie", "#E5484D", rough=0.4), (0, 0.2, 0.95), (0.08, 0.02, 0.35), parent=e)
    hp = mat("sm_hp", "#1F2328", rough=0.3, metal=0.3)
    if headphones:
        add(bpy.ops.mesh.primitive_torus_add, hp, (0, 0, 1.5), (0, R(90), 0), major_radius=0.29, minor_radius=0.03, parent=e)
        for sx in (-1, 1):
            cyl(hp, (sx * 0.28, 0, 1.43), 0.11, 0.1, rot=(0, R(90), 0), parent=e)
    else:  # 外れて床に落ちたヘッドホン（何もつながっていない）
        add(bpy.ops.mesh.primitive_torus_add, hp, (0.45, -0.5, 0.05), (0, 0, 0), major_radius=0.29, minor_radius=0.03, parent=e)
        for sx in (-1, 1):
            cyl(hp, (0.45 + sx * 0.28, -0.5, 0.06), 0.11, 0.1, parent=e)
    if list_behind:  # 背中に隠した名簿の束（字は書かない）
        for i in range(6):
            cube(mat("paper", "#F4F1EA", rough=0.9), (0.3, -0.32, 0.55 + i * 0.025), (0.42, 0.3, 0.02), rot=(0, 0, R(i * 3)), parent=e)
        for i in range(4):
            cube(mat("lines", "#9AA4AA", rough=0.9), (0.3, -0.32 - 0.02 * 0, 0.7), (0.32, 0.005, 0.01), parent=e).location.z = 0.7 - i * 0.0
    return e


def b17():  # S17 新たな容疑者：大きなヘッドホンの会社の人
    world("#120D1C", 0.2)
    ground("#2A2238", rough=0.5)
    cyl(mat("ped2", "#E8EEF1", rough=0.35, coat=0.3), (0, 1.2, 0.3), 0.8, 0.6)
    salesman((0, 1.2, 0.6))
    spot((0, -0.5, 5.5), (0, 1.2, 1.4), 2200, 28, "#FFE9C7")
    maru((-1.5, -0.6, 0), face_deg=25, eye_glow=1.6, look_up=20, jump=0.25, tilt=-10)
    area((-3, -4, 3), (0, 1, 1), 150, 4, "#C8B8FF")
    camera((-0.6, -5.4, 1.7), (-0.2, 1.0, 1.3), lens=34)


def b18():  # S18 ヘッドホンはぽろり、中は何もつながっていない。後ろに名簿
    world("#120D1C", 0.2)
    ground("#2A2238", rough=0.5)
    cyl(mat("ped2", "#E8EEF1", rough=0.35, coat=0.3), (0, 1.2, 0.3), 0.8, 0.6)
    salesman((0, 1.2, 0.6), headphones=False, list_behind=True)
    spot((0, -0.5, 5.5), (0, 1.2, 1.4), 2200, 28, "#FFE9C7")
    maru((-1.3, -0.6, 0), face_deg=25, eye_glow=1.1, look_up=10, tilt=18)
    area((-3, -4, 3), (0, 1, 1), 150, 4, "#C8B8FF")
    camera((1.4, -5.0, 1.8), (0.1, 1.0, 1.0), lens=34)


def b19():  # S19 3人の容疑者に戻る：①は消え、②③が強く光る。鏡にまるロボ
    pedestals(lit=(0, 1.6, 1.6))
    maru((-1.15, -1.0, 0), face_deg=200, s=0.75, eye_glow=1.5, look_up=8)
    area((0, -4, 3), (0, 0.5, 1), 160, 4, "#A9C8FF")
    camera((0.4, -5.8, 2.3), (0.1, 0.8, 1.0), lens=33)


def b21():  # S21 その夜：まるロボがこそこそマイクに「ピポ、ピポ」
    room(night=True)
    person_lie((0.15, -0.15, 0.42))
    phone((0.35, -0.9, 0.0), 10, screen=None)
    maru((0.3, -1.55, 0), face_deg=160, hat=True, eye_glow=1.3, look_up=-20, s=0.42)
    bubble((0.55, -1.5, 0.78), 0.14, "icon_tent.png")
    area((-3, 2, 3), (0, 0, 0), 120, 2, "#7F9CFF")
    area((2, -3, 2.5), (0, -1, 0.3), 40, 2, "#FFE2B8")
    camera((1.2, -3.0, 1.0), (0.3, -1.25, 0.35), lens=40)


def b22():  # S22 次の朝：テントの広告に、まるロボがひっくり返っている
    room(night=False)
    phone((0.35, -0.9, 0.0), 10, glow=1.5)
    e = maru((-0.2, -1.2, 0.56), face_deg=-200, s=0.45, hat=True, eye_glow=1.6, look_up=0)
    e.rotation_euler = (R(165), 0, R(-160))
    sun((50, 0, 200), 2.0)
    area((0, -3, 2.5), (0, -1, 0.3), 300, 3, "#FFF1DD")
    camera((0.3, -3.0, 1.2), (0.05, -1.0, 0.3), lens=38)


SC = {k: v for k, v in globals().items() if k.startswith("b") and len(k) == 3 and callable(v)}
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
SC[SCENE]()
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
