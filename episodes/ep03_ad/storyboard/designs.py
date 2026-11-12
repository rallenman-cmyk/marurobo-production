# 会話と広告の回：人（ハルさん・ソラさん）と番犬の見た目の案（同じ構図で 1 枚ずつ）
# blender -b --factory-startup --python designs.py -- <p1|p2|p3|d1|d2|d3|d4> <out.png> [samples]
# 人：p1＝EP01 と同じピクトグラム（全身1色・点の目・口なし）＋目印／p2＝服と肌の色を分けた立体／p3＝いまの絵コンテ（顔なしの記号）
# 犬：d1 柴犬／d2 白いふわふわ（両耳を立てる）／d3 ぶちの垂れ耳＋見張りの帽子／d4 黒い犬（片耳を立てる）
import os, sys, math, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "board.py"), encoding="utf-8").read()
exec(_src.split("\n# ---------------- 場面（台本 v1.0")[0])
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep01_earphone", "stage", "human"))
HARU, SORA = "#3E7CB1", "#E58C5A"


def studio(floor="#DCE6EC"):
    world("#EEF3F6", 0.8)
    ground(floor, rough=0.7)
    cube(mat("backdrop", "#E7EEF2", rough=0.9), (0, 3.0, 2.0), (12, 0.1, 4))
    sun((55, 0, -30), 2.2)
    area((-3, -4, 3), (0, 0, 1), 500, 4, "#FFF4E5")
    area((3, -2, 2.5), (0, 0, 1), 250, 3, "#DDEBFF")


def icon_person(name, colors, outfit, x, look):
    import iconfig
    ch = iconfig.make_icon(name, colors, outfit=outfit, look=look, neck=look != "pict", Rh=0.140 if look == "pict" else 0.122, hc_z=1.226 if look == "pict" else 1.300)
    arm = ch["arm"]
    arm.location = (x, 0, 0)
    arm.scale = (1.25, 1.25, 1.25)
    for o in bpy.data.objects:  # 点の目を見せる
        if o.name.startswith(name + " eye."):
            o.hide_render = False
    return ch


def people(kind):
    studio()
    cube(mat("bench", "#9AA3AB", rough=0.8), (0, 0.25, 0.33), (2.6, 0.7, 0.66), bevel=0.05)  # 座席（人は座った形で作ってある）
    cube(mat("bench", "#9AA3AB", rough=0.8), (0, 0.6, 0.95), (2.6, 0.15, 0.9), bevel=0.05)
    if kind == "p1":
        icon_person("Haru", dict(body=HARU, eyes=True, accent="#E3AE3A"), "cap", -0.55, "pict")
        icon_person("Sora", dict(body=SORA, eyes=True, accent="#2A9D8F"), "scarf", 0.55, "pict")
    elif kind == "p2":
        icon_person("Haru", dict(top=HARU, pants="#34486E", accent="#E3AE3A", skin="#F4D2B5"), "cap", -0.55, "3d")
        icon_person("Sora", dict(top=SORA, pants="#6A4A3A", accent="#2A9D8F", skin="#E9BE9A"), "scarf", 0.55, "3d")
    else:
        person((-0.55, 0.15, 0.2), face_deg=0, shirt="#4E8FC7", hair="#2B2220", sit=True, s=1.25)
        person((0.55, 0.15, 0.2), face_deg=0, shirt="#E58C5A", hair="#6A4A3A", sit=True, s=1.25)
    maru((1.35, -0.35, 0), face_deg=-20, s=0.55, hat=False, eye_glow=1.0, look_up=12)
    camera((0.15, -4.8, 1.3), (0.15, 0, 1.0), lens=38)


def dogs(kind):
    studio("#D7E2E8")
    opt = dict(d1=dict(), d2=dict(fur_c="#F4F1EA", light_c="#FFFFFF", ears="both_up", fluffy=True),
               d3=dict(fur_c="#F2EBDD", light_c="#FFFFFF", ears="flop", cap=True, patch="#8A5A34"),
               d4=dict(fur_c="#2B2B33", light_c="#C9B08A", ears="one_up"))[kind]
    dog((0.3, 0.3, 0), -20, eyes="closed", **opt)
    maru((-1.15, -0.3, 0), face_deg=40, s=1.0, hat=True, eye_glow=1.0, look_up=18)
    camera((-0.3, -5.6, 1.5), (-0.1, 0.2, 1.1), lens=36)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
(people if SCENE.startswith("p") else dogs)(SCENE)
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
