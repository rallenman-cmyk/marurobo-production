# ロボットではありません回：台本 v1.0 の絵コンテ（3D の場面を 1 枚ずつ。字のない 3D。字・札は board_overlay.py で 2D に重ねる）
# blender -b --factory-startup --python board.py -- <場面> <out.png> [samples] [--tex <絵のフォルダ>]
#   v3 で足した場面：b20d（門番が伏せて半ばあきらめる）・b21w（まっすぐ歩くまるロボ）・b21i（門のない床。遠くで門番が見ている）・b23l・b23r（ふらふら）
#   場面：b01 b02 b03 b04a b04b b05a b05b b08 b12 b13 b13e b13h b14 b15 b16 b17 b17n b18 b21 b22 b23（e＝足あとなし、h＝私の足あとだけ、n＝まだ選んでいない）
#   一緒に <out>.json：札を重ねる場所（3D の点を画面の座標にしたもの）
# 部品は 3本目（ep03_ad/storyboard）のもの：まるロボ（仮のモデル）・番犬（門番に使う）・光・材質
# 決まり：3D の中に字を書かない。まるロボは喋らない（腕はない。マウスは体で押す）
import os, sys, json, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
EP03 = os.path.join(HERE, "..", "..", "ep03_ad", "storyboard")
_a = sys.argv[sys.argv.index("--") + 1:]
TEX = _a[_a.index("--tex") + 1] if "--tex" in _a else os.path.join(HERE, "tex")
RICH = "--rich" in _a                                      # 舞台を作り込んだ版（rich.py）
_a = [x for x in _a if x != "--rich"]
sys.argv = [sys.argv[0], "--"] + [x for i, x in enumerate(_a) if x != "--tex" and (i == 0 or _a[i - 1] != "--tex")]
_src = open(os.path.join(EP03, "scenes.py"), encoding="utf-8").read()
exec(_src.split("# ---------------- 場面\n")[0])          # mat・sphere・cyl・cube・plane・maru・world・area・spot・camera・ground（SCENE, OUT, SAMPLES もここで決まる）
_g = open(os.path.join(EP03, "guards.py"), encoding="utf-8").read()
NAVY, DARK, GOLD = "#2F4A73", "#14243A", "#F2C14E"
exec(_g[_g.index("def closed_eye"):_g.index("def owl")])
exec(_g[_g.index("def dog"):_g.index("def chip")])
DOG = dict(fur_c="#F2EBDD", light_c="#FFFFFF", ears="flop", cap=True, patch="#8A5A34")   # 3本目と同じ番犬（ここでは門番）
R = math.radians
ANCH = {}            # 札を重ねる点（名前 → 3D の場所）


def anchor(name, loc):
    ANCH[name] = Vector(loc)


def img(name, emit=1.0):
    return img_mat(name, os.path.join(TEX, name + ".png"), emit=emit)


# ---------------- 部品
def desk_room():
    world("#0C1426", 0.12)
    ground("#2A2F45", size=20)
    cube(mat("wall", "#3A4766", rough=0.9), (0, 2.2, 1.6), (10, 0.1, 3.2))
    cube(mat("winf", "#C9C2B5", rough=0.4), (-2.6, 2.14, 1.9), (1.2, 0.03, 1.0))
    cube(mat("winsky", "#1C2B55", emit=0.6), (-2.6, 2.12, 1.9), (1.1, 0.02, 0.9))
    cube(mat("desk", "#A07850", rough=0.55), (0, 0.6, 0.72), (3.4, 1.6, 0.06), bevel=0.01)
    for x in (-1.6, 1.6):
        for y in (0.0, 1.3):
            cube(mat("deskleg", "#6E5236", rough=0.6), (x, y, 0.35), (0.06, 0.06, 0.7))
    cyl(mat("lamp_base", "#59616B", rough=0.4, metal=0.5), (1.5, 1.25, 0.77), 0.09, 0.03)
    cyl(mat("lamp_arm", "#59616B", rough=0.4, metal=0.5), (1.5, 1.25, 0.95), 0.012, 0.36)
    cyl(mat("lamp_shade", "#E8D9B0", rough=0.5, emit=0.6), (1.5, 1.15, 1.13), 0.09, 0.08, rot=(R(60), 0, 0))
    bpy.ops.object.light_add(type='POINT', location=(1.4, 1.0, 1.4)); L = bpy.context.object; L.data.energy = 90; L.data.color = srgb("#FFD9A0")[:3]


def laptop(loc, screen, glow=1.8, rz=0.0, open_deg=105):
    e = empty(loc, R(rz))
    gray = mat("lap_body", "#B8C0C8", rough=0.35, metal=0.5)
    cube(gray, (0, 0, 0.02), (1.3, 0.85, 0.04), bevel=0.015, parent=e)
    cube(mat("lap_keys", "#59616B", rough=0.6), (0, -0.05, 0.043), (1.12, 0.45, 0.005), parent=e)
    hinge = empty((0, 0.42, 0.04)); hinge.parent = e; hinge.rotation_euler = (R(open_deg - 90), 0, 0)
    cube(gray, (0, 0.0, 0.43), (1.3, 0.03, 0.86), bevel=0.015, parent=hinge)
    scr = plane(img(screen, glow), (0, -0.017, 0.44), (1.2, 0.75), rot=(R(90), 0, 0), parent=hinge)
    scr.rotation_euler = (R(90), 0, 0)
    c = empty((0, -0.02, 0.44)); c.parent = hinge
    return e, hinge, c


def mouse(loc, rz=0.0):
    e = empty(loc, R(rz))
    sphere(mat("mouse", "#E9EDF1", rough=0.3, coat=0.5), (0, 0, 0.03), 0.09, scale=(0.75, 1.15, 0.45), parent=e)
    cube(mat("mouse_line", "#9AA4AA", rough=0.4), (0, -0.05, 0.072), (0.004, 0.08, 0.004), parent=e)
    return e


def screen_world(gate_alpha=1.0, gatekeeper=True, dog_down=False, gate=True):
    """画面の中：明るい広い床。奥にチェック欄の門（四角い枠）と、横に門番（番犬）"""
    world("#DCE8F2", 0.9)
    ground("#EEF3F7", size=60, rough=0.5)
    line = mat("grid_line", "#C9D6E2", rough=0.5)
    for k in range(-12, 13):
        cube(line, (k * 1.5, 6, 0.004), (0.03, 30, 0.004))
        cube(line, (0, k * 1.5 + 6, 0.004), (36, 0.03, 0.004))
    fr = mat("gate_frame", "#2F4A73", rough=0.35, alpha=gate_alpha)
    gx, gy = 0.0, 9.0
    if not gate:
        sun((55, 0, 25), 3.2)
        if gatekeeper:
            dog((5.5, 16, 0), 200, eyes="open", **DOG); anchor("dog", (5.5, 15.8, 2.6))
        return
    for sx in (-1, 1):
        cube(fr, (gx + sx * 1.35, gy, 1.4), (0.3, 0.3, 2.8), bevel=0.04)
    cube(fr, (gx, gy, 2.95), (3.0, 0.3, 0.3), bevel=0.04)
    cube(mat("gate_door", "#FFFFFF", rough=0.4, alpha=gate_alpha * 0.9), (gx, gy, 1.4), (2.4, 0.08, 2.6), bevel=0.02)
    cube(mat("gate_box", "#2F4A73", rough=0.3, alpha=gate_alpha), (gx, gy - 0.06, 1.55), (1.0, 0.04, 1.0), bevel=0.02)
    cube(mat("gate_box_in", "#FFFFFF", rough=0.3, alpha=gate_alpha), (gx, gy - 0.085, 1.55), (0.82, 0.02, 0.82))
    anchor("gate", (gx, gy, 3.3))
    sun((55, 0, 25), 3.2)
    if gatekeeper and dog_down:   # 伏せて、半ばあきらめている（体を低く、頭を前に下げ、目を閉じる）
        before = set(bpy.data.objects)
        dog((2.4, gy - 0.4, 0), 15, eyes="closed", **DOG)
        new = [o for o in set(bpy.data.objects) - before if o.parent is None]
        for o in new:
            if o.type == 'EMPTY':
                o.scale = (1.15, 1.3, 0.55); o.location.z = -0.05
                for c in o.children:
                    if c.type == 'EMPTY' and c.location.z > 1.5:
                        c.location.z = 1.05; c.location.y -= 0.35; c.rotation_euler[0] = R(25); c.scale = (0.9, 0.9, 1.6)
        anchor("dog", (2.4, gy - 0.6, 1.4))
    elif gatekeeper:
        dog((2.4, gy - 0.4, 0), 15, eyes="open", **DOG)
        anchor("dog", (2.4, gy - 0.6, 2.6))


def steps(points, col, name, size=0.16):
    m = mat("fp_" + name, col, rough=0.5, emit=0.8)
    for i in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        a = math.atan2(y1 - y0, x1 - x0)
        for sx in (-1, 1):
            ox, oy = -math.sin(a) * 0.12 * sx, math.cos(a) * 0.12 * sx
            o = sphere(m, (x0 + ox, y0 + oy, 0.01), size, scale=(1.3, 0.75, 0.08))
            o.rotation_euler = (0, 0, a)


def path_human(n=34):
    pts = []
    for k in range(n):
        t = k / (n - 1)
        x = -4.0 + 4.0 * t + 1.3 * math.sin(t * 9.0) * (1 - t) ** 0.7
        y = -1.0 + 9.0 * t - 0.5 * math.sin(t * 6.0) * (1 - t)
        pts.append((x, y))
    return pts


def path_robot(n=22):
    return [(4.0 - 4.0 * k / (n - 1), -1.0 + 9.0 * k / (n - 1)) for k in range(n)]


def stamp_book(loc, rz=0.0):
    e = empty(loc, R(rz))
    cube(mat("book_cover", "#2F4A73", rough=0.5), (0, 0, 0.03), (1.9, 1.35, 0.06), bevel=0.02, parent=e)
    plane(img("stamps", 0.4), (0, 0, 0.065), (1.8, 1.28), parent=e)
    return e


def meter(loc, level):
    e = empty(loc)
    cube(mat("meter_case", "#2F4A73", rough=0.4), (0, 0, 1.5), (0.5, 0.3, 3.0), bevel=0.05, parent=e)
    cube(mat("meter_in", "#14243A", rough=0.4), (0, -0.16, 1.5), (0.34, 0.02, 2.8), parent=e)
    h = 2.8 * level
    cube(mat("meter_fill", "#21C1B3", rough=0.3, emit=2.5), (0, -0.18, 0.1 + h / 2), (0.3, 0.02, h), parent=e)
    for k, z in enumerate((0.6, 1.5, 2.4)):
        cube(mat("meter_tick", "#FFFFFF", emit=0.5), (0.3, -0.16, z), (0.15, 0.02, 0.03), parent=e)
    anchor("meter_top", (loc[0], loc[1], loc[2] + 3.2))
    anchor("meter_mid", (loc[0] + 0.6, loc[1], loc[2] + 1.5))
    return e


def street_floor(selected=(), edge=False):
    """床いっぱいの町の写真を 4×4 のマスで区切る（マス 1.5、真ん中 (0, 4)）"""
    world("#DCE8F2", 0.9); sun((55, 0, 25), 3.0)
    ground("#EEF3F7", size=60, rough=0.5)
    plane(img("street", 0.25), (0, 4, 0.006), (6.0, 6.0))
    ln = mat("cell_line", "#FFFFFF", rough=0.4, emit=0.8)
    for k in range(5):
        cube(ln, (-3 + k * 1.5, 4, 0.02), (0.06, 6.0, 0.02))
        cube(ln, (0, 1 + k * 1.5, 0.02), (6.0, 0.06, 0.02))
    blue = mat("cell_sel", "#3B82F6", rough=0.3, alpha=0.45, emit=0.6)
    for (c, r) in selected:          # c=0..3（左→右）、r=0..3（奥→手前）
        cube(blue, (-2.25 + c * 1.5, 6.25 - r * 1.5, 0.03), (1.42, 1.42, 0.02))
    if edge:
        anchor("edge", (2.25, 6.25, 0.4))


def newspapers():
    world("#3B3326", 0.25)
    ground("#5A4A36", size=40, rough=0.8)
    paper = img("newspaper", 0.15)
    import random; random.seed(2)
    for x, y, n in ((-3.2, 3, 9), (-1.5, 4.2, 14), (0.4, 3.6, 7), (2.2, 4.4, 12), (3.6, 2.8, 6), (-2.6, 6, 16), (1.0, 6.5, 18)):
        for k in range(n):
            o = plane(paper, (x + random.uniform(-0.05, 0.05), y, 0.02 + k * 0.045), (1.4, 1.8))
            o.rotation_euler = (0, 0, R(random.uniform(-6, 6)))
            cube(mat("paper_edge", "#D8CBAE", rough=0.9), (x, y, 0.0 + k * 0.045), (1.38, 1.78, 0.04))
    glow = mat("faded_word", "#FFD36B", rough=0.4, emit=4.0, alpha=0.9)
    for x, y, z in ((-1.4, 4.0, 0.68), (2.3, 4.2, 0.58), (1.1, 6.3, 0.86), (-2.5, 5.8, 0.77), (0.5, 3.4, 0.36)):
        cube(glow, (x, y, z), (0.32, 0.08, 0.01))
    spot((0, -1, 6), (0, 4, 0), 2500, 55, "#FFE6B0")
    anchor("papers", (0, 4.5, 1.6))


# ---------------- 場面（台本 v1.0 の場面番号）
def room_shot(screen, maru_loc=(0.55, 0.45, 0.75), face=-20, look=0, cam=((0.9, -2.3, 1.75), (0.1, 0.7, 1.0), 38), tilt=0, jump=0, glow=0.9, mouse_loc=(0.45, 0.2, 0.75)):
    desk_room()
    e, h, c = laptop((-0.05, 0.75, 0.75), screen)
    anchor("screen", c.matrix_world.translation if False else (-0.05, 0.75 + 0.42, 0.75 + 0.48))
    mouse(mouse_loc)
    maru(maru_loc, face_deg=face, s=0.22, hat=False, eye_glow=glow, look_up=look, tilt=tilt, jump=jump)
    anchor("maru", (maru_loc[0], maru_loc[1], maru_loc[2] + 0.34))
    area((-1.5, -1.5, 2.5), (0, 0.6, 0.8), 140, 2, "#9FB8FF")
    camera(*cam[:2], lens=cam[2])


def b01(): room_shot("scr_shop", maru_loc=(0.62, 0.32, 0.75), face=-35)
def b02(): room_shot("scr_check", maru_loc=(0.62, 0.32, 0.75), face=-25, look=8, cam=((0.5, -1.4, 1.35), (-0.05, 1.0, 1.15), 38))
def b03(): room_shot("scr_check", maru_loc=(0.2, 0.25, 0.75), face=-5, look=6, cam=((0.15, -1.1, 1.3), (-0.05, 1.0, 1.18), 32))
def b04a(): room_shot("scr_robot_path", maru_loc=(0.62, 0.12, 0.75), face=-10, mouse_loc=(0.62, 0.32, 0.75))
def b04b(): room_shot("scr_test", maru_loc=(0.8, 0.0, 0.75), face=-30, look=10, jump=0.25, glow=1.6, mouse_loc=(0.62, 0.32, 0.75))
def b05a(): room_shot("scr_human_pass", maru_loc=(1.15, 0.35, 0.75), face=-60, look=6, mouse_loc=(0.5, 0.25, 0.75))
def b05b(): room_shot("scr_pass", maru_loc=(0.75, 0.25, 0.75), face=-30, look=12, glow=1.6, cam=((0.5, -1.4, 1.35), (-0.05, 1.0, 1.15), 38))
def b11(): room_shot("scr_check", maru_loc=(0.62, 0.32, 0.75), face=-25, look=8, cam=((0.0, -1.05, 1.25), (-0.05, 1.0, 1.2), 34))
def b22(): room_shot("scr_check", maru_loc=(0.45, 0.3, 0.75), face=-15, look=8, cam=((0.3, -1.6, 1.4), (-0.05, 1.0, 1.1), 36))
def b23(): room_shot("scr_human_pass", maru_loc=(0.62, 0.15, 0.75), face=-20, look=-8, tilt=14, glow=0.3, mouse_loc=(0.5, 0.32, 0.75))


def b08():
    newspapers()
    maru((0.2, 1.2, 0), face_deg=10, s=0.8, hat=False, eye_glow=1.0, look_up=18)
    camera((1.5, -3.5, 2.4), (0.0, 4.0, 0.7), 30)


def b12():
    screen_world()
    maru((0, 1.0, 0), face_deg=180, s=0.9, hat=False, eye_glow=1.0, look_up=10)
    anchor("maru", (0, 1.0, 1.6))
    camera((0.8, -5.5, 2.4), (0.3, 7.0, 1.4), 30)


def b13(human=True, robot=True):
    screen_world()
    if human: steps(path_human(), "#FF8A2A", "h")
    if robot: steps(path_robot(), "#21C1B3", "r")
    maru((4.4, -1.6, 0), face_deg=200, s=0.8, hat=False, eye_glow=0.6, look_up=-15)
    anchor("human_path", (-2.6, 2.0, 0.3)); anchor("robot_path", (2.2, 3.5, 0.3))
    camera((0, -7.5, 11.5), (0, 4.0, 0), 28)


def b13e(): b13(False, False)
def b13h(): b13(True, False)


def b14():
    screen_world()
    steps(path_human(), "#FF8A2A", "h")
    steps(path_robot(), "#21C1B3", "r")
    spot((2.4, 7.0, 6), (0.5, 3.5, 0), 1800, 40, "#FFF0C0")
    maru((4.6, -0.8, 0), face_deg=190, s=0.8, hat=False, eye_glow=0.3, look_up=-25, tilt=8)
    camera((5.5, -3.5, 3.4), (1.0, 6.5, 1.0), 28)


def b15():
    screen_world()
    stamp_book((1.0, 6.4, 0.8), rz=8)
    cube(mat("stand", "#2F4A73", rough=0.4), (1.0, 6.4, 0.38), (1.6, 1.0, 0.76), bevel=0.04)
    maru((-1.3, 4.6, 0), face_deg=215, s=0.8, hat=False, eye_glow=1.0, look_up=20)
    anchor("book", (1.0, 6.4, 1.3))
    camera((-2.6, 0.2, 3.4), (0.6, 7.0, 0.9), 34)


def b16():
    screen_world()
    meter((-2.4, 8.4, 0), 0.55)
    maru((-0.6, 5.0, 0), face_deg=200, s=0.8, hat=False, eye_glow=1.0, look_up=25)
    camera((0.6, -1.5, 2.4), (-0.5, 8.0, 1.6), 30)


def b17():
    street_floor(selected=((2, 0), (2, 1)))
    maru((0.75, 5.5, 0.03), face_deg=180, s=0.7, hat=False, eye_glow=1.0, look_up=-10)
    camera((0, -4.2, 7.2), (0, 4.0, 0), 34)


def b17n():
    street_floor(selected=())
    maru((-2.6, 0.2, 0.03), face_deg=170, s=0.7, hat=False, eye_glow=1.0, look_up=-10)
    camera((0, -4.2, 7.2), (0, 4.0, 0), 34)


def b18():
    street_floor(selected=((2, 0), (2, 1)), edge=True)
    maru((2.25, 4.9, 0.03), face_deg=170, s=0.7, hat=False, eye_glow=1.2, look_up=-20, tilt=-10)
    anchor("maru", (2.25, 4.9, 1.3))
    camera((3.0, -0.4, 4.2), (2.0, 5.9, 0.2), 30)


def b21():
    screen_world(gate_alpha=0.25)
    maru((0, 3.0, 0), face_deg=180, s=0.9, hat=False, eye_glow=0.8, look_up=15)
    camera((0.8, -4.5, 2.6), (0.3, 7.0, 1.4), 30)


def b20d():
    screen_world(dog_down=True)
    maru((-0.8, 4.0, 0), face_deg=200, s=0.8, hat=False, eye_glow=0.8, look_up=10)
    camera((3.2, 1.2, 2.2), (1.6, 8.6, 0.8), 32)


def b21w():
    screen_world()
    steps(path_robot(), "#21C1B3", "r")
    maru((2.0, 3.5, 0), face_deg=200, s=0.8, hat=False, eye_glow=1.0, look_up=0)
    anchor("maru", (2.0, 3.5, 1.4))
    camera((5.6, -2.5, 3.0), (1.2, 5.5, 0.6), 30)


def b21i():
    screen_world(gate=False)
    maru((0, 3.0, 0), face_deg=180, s=0.9, hat=False, eye_glow=0.9, look_up=5)
    meter((4.2, 15.0, 0), 0.75)
    camera((0.8, -4.5, 2.6), (1.5, 9.0, 1.2), 30)


def b23l(): room_shot("scr_check", maru_loc=(0.55, 0.15, 0.75), face=-10, look=-8, tilt=-16, glow=0.3, mouse_loc=(0.45, 0.32, 0.75))
def b23r(): room_shot("scr_check", maru_loc=(0.68, 0.18, 0.75), face=-30, look=-8, tilt=16, glow=0.3, mouse_loc=(0.5, 0.32, 0.75))


if RICH:
    exec(open(os.path.join(HERE, "rich.py"), encoding="utf-8").read())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
globals()[SCENE]()
if RICH and not sc.camera.data.dof.use_dof:
    for k in ("maru", "book", "edge", "gate", "dog"):
        if k in ANCH: focus_on(tuple(ANCH[k]), 4.0); break
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = RES
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Punchy'
sc.render.filepath = OUT
bpy.context.view_layer.update()
from bpy_extras.object_utils import world_to_camera_view
pos = {}
for k, v in ANCH.items():
    p = world_to_camera_view(sc, sc.camera, v)
    pos[k] = [round(p.x * RES[0]), round((1 - p.y) * RES[1])]
json.dump(pos, open(os.path.splitext(OUT)[0] + ".json", "w"))
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT, pos)
