# 17本目（カード）：3D の部品（16本目の kit16.py から写した）（scenes.py が exec で読む。前提：KIT_HERE と TEX（絵のフォルダ）を決めてから読む）
#   まるロボ・人・材質・光・カメラは 6本目（ep06_haizen/anim/kit.py → 3本目の部品）をそのまま読み込む（9本目の kit9.py と同じ）
#   まるロボの家（部屋・家具・スマホ）は 5本目（ep05_vacuum/anim/kit.py）の room・furniture・phone_seq をそのまま読み込む
#   新しく作った物：お城（正面の門・石のかべ・塔・横の裏口）・門番さん・名札・影・鍵・古い錠・部品の箱・お店の模型・机
#   決まり：3D の中に字を書かない。まるロボは喋らない。名札＝青緑（まるロボ）・橙・緑。影は黒（輪郭だけ紫）。影の錠は赤（2章）
#   絵コンテ表：../絵コンテ_v1.md
import os, sys, math, importlib.util
_K17 = KIT_HERE
KIT_HERE = os.path.join(_K17, "..", "..", "ep06_haizen", "anim")
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
KIT_HERE = _K17
# ---------------------------------------------------------------- 5本目の部屋（間取り plan は 5本目の物を別の名前で読む）
_sp5 = importlib.util.spec_from_file_location("plan5", os.path.join(_K17, "..", "..", "ep05_vacuum", "anim", "plan.py"))
plan5 = importlib.util.module_from_spec(_sp5); _sp5.loader.exec_module(plan5)
RUGOBJ = []
_src5 = open(os.path.join(_K17, "..", "..", "ep05_vacuum", "anim", "kit.py"), encoding="utf-8").read()
_a5 = _src5.index("DESK_TOP = 0.755"); _b5 = _src5.index("# ---------------- 点の地図")
exec(_src5[_a5:_b5].replace("plan.", "plan5."))

PURPLE = "#7B5BD6"
BLUE_C, PURP_C, ORANGE_C, GREY_C, GREEN_C, RED_C = "#3478E6", "#8A5BD6", "#FF8A1F", "#9AA4B2", "#34B266", "#E23A30"
NUM = "35280476"


def _m(name, col, **kw): return mat(name, col, **kw)


# ======================================================================== 家の物（金庫・帽子かけ・帽子・ゴミ箱・封筒・カード）
SAFE_W, SAFE_D, SAFE_H = 0.46, 0.42, 0.50


def safe(loc, face=0.0):
    """金庫（濃い灰色の箱。正面＝−y にダイヤルと取っ手。とびらは左の蝶つがいで開く。中に棚 1 段）。
    戻り値：dict(root, door（蝶つがい。z 回りに開く）, dial（回す）, shelf（カードを置く高さの empty）, glow（中を照らす光）)"""
    root = empty(loc, R(face))
    body = _m("safebody", "#4A5260", rough=0.45, metal=0.6)
    inner = _m("safein", "#2A2F38", rough=0.8)
    W, D, H, T = SAFE_W, SAFE_D, SAFE_H, 0.04
    cube(body, (0, 0, T / 2), (W, D, T), parent=root); cube(body, (0, 0, H - T / 2), (W, D, T), parent=root)
    cube(body, (-W / 2 + T / 2, 0, H / 2), (T, D, H), parent=root); cube(body, (W / 2 - T / 2, 0, H / 2), (T, D, H), parent=root)
    cube(body, (0, D / 2 - T / 2, H / 2), (W, T, H), parent=root)
    cube(inner, (0, 0.0, T + 0.005), (W - 2 * T, D - 2 * T, 0.01), parent=root)
    cube(inner, (0, 0.0, H * 0.42), (W - 2 * T, D - 2 * T, 0.015), parent=root)         # 棚
    shelf = empty((0, -0.02, H * 0.42 + 0.012)); shelf.parent = root
    for sx in (-1, 1): cyl(_m("safefoot", "#2A2F38", rough=0.6), (sx * (W / 2 - 0.06), -D / 2 + 0.06, -0.01), 0.025, 0.02, parent=root)
    door = empty((-W / 2, -D / 2, 0.0)); door.parent = root
    cube(body, (W / 2, -0.02, H / 2), (W - 0.01, 0.04, H - 0.01), bevel=0.006, parent=door)
    dial = empty((W / 2 + 0.03, -0.045, H * 0.58)); dial.parent = door
    cyl(_m("dial", "#C9CED6", rough=0.25, metal=0.9), (0, 0, 0), 0.055, 0.02, rot=(R(90), 0, 0), parent=dial)
    for k in range(12):
        a = R(k * 30); cube(_m("dialtick", "#2A2F38", rough=0.5), (0.045 * math.cos(a), -0.011, 0.045 * math.sin(a)), (0.006, 0.003, 0.012), rot=(0, -a, 0), parent=dial)
    cube(_m("dialmark", "#E23A30", rough=0.5), (0, -0.012, 0.03), (0.008, 0.003, 0.02), parent=dial)
    cyl(_m("handle", "#C9CED6", rough=0.25, metal=0.9), (W / 2 + 0.03, -0.055, H * 0.33), 0.012, 0.13, rot=(0, R(90), 0), parent=door)
    bpy.ops.object.light_add(type='POINT', location=(0, 0, H * 0.75)); gl = bpy.context.object; gl.parent = root
    gl.data.energy = 0.0; gl.data.shadow_soft_size = 0.1; gl.data.color = (1.0, 0.92, 0.78)
    return dict(root=root, door=door, dial=dial, shelf=shelf, glow=gl)


def safe_open(sf, t, d=0.6, deg=-105):
    key(sf["door"], "rotation_euler", t, (0, 0, 0)); key(sf["door"], "rotation_euler", t + d, (0, 0, R(deg)))
    l = sf["glow"].data
    l.energy = 0.0; l.keyframe_insert("energy", frame=f(t)); l.energy = 6.0; l.keyframe_insert("energy", frame=f(t + d))


def safe_close(sf, t, d=0.5, deg=-105):
    key(sf["door"], "rotation_euler", t, (0, 0, R(deg))); key(sf["door"], "rotation_euler", t + d, (0, 0, 0))
    l = sf["glow"].data
    l.energy = 6.0; l.keyframe_insert("energy", frame=f(t)); l.energy = 0.0; l.keyframe_insert("energy", frame=f(t + d))


def safe_dial(sf, t, turns=1.5, d=1.2):
    key(sf["dial"], "rotation_euler", t, (0, 0, 0)); key(sf["dial"], "rotation_euler", t + d * 0.5, (0, R(360 * turns * 0.6), 0))
    key(sf["dial"], "rotation_euler", t + d, (0, R(360 * turns * 0.2), 0))


def card_obj(loc=(0, 0, 0), rot=(0, 0, 0), tex="card_blue", w=0.17, parent=None):
    """カード（厚み 2 mm の板。上の面に柄）。前の向き：上の面が +z"""
    e = empty(loc); e.rotation_euler = rot
    if parent is not None: e.parent = parent
    h = w * 540 / 856
    cube(_m("cardedge", "#E8ECF2", rough=0.4), (0, 0, 0), (w, h, 0.003), bevel=0.001, parent=e)
    plane(img_mat("cardface_" + tex, os.path.join(TEX, tex + ".png"), emit=0.25), (0, 0, 0.0016), (w, h), parent=e)
    return e


def envelope(loc, rz=0.0):
    e = empty(loc, R(rz))
    cube(_m("env", "#F3EBDD", rough=0.8), (0, 0, 0.006), (0.24, 0.16, 0.012), bevel=0.002, parent=e)
    cube(_m("envflap", "#E7DCC8", rough=0.8), (0, 0.04, 0.013), (0.24, 0.08, 0.002), parent=e)
    return e


def hat_rack(loc):
    """帽子かけ（床に立つ細い木の柱と、上のかぎ）"""
    e = empty(loc)
    wd = _m("rackwood", "#7A5A40", rough=0.6)
    cyl(wd, (0, 0, 0.02), 0.13, 0.04, parent=e); cyl(wd, (0, 0, 0.42), 0.022, 0.84, parent=e)
    for a in (0, 120, 240):
        cyl(wd, (0.06 * math.cos(R(a)), 0.06 * math.sin(R(a)), 0.80), 0.012, 0.14, rot=(0, R(55), R(a)), parent=e)
    return e


def hat_parts(parent):
    """探偵の帽子（3本目と同じ形・柄。つばの右に小さな虫めがね）。parent の原点がかぶる所。前＝+y（本物のまるロボの前）"""
    plaid = checker_mat("hat_plaid", "#B88A55", "#8A6239", 9); band = _m("hat_band", "#5B3B22", rough=0.6)
    he = empty((0, 0, 0)); he.parent = parent
    sphere(plaid, (0, 0, 0.02), 0.35, scale=(1, 1.02, 0.7), parent=he); cyl(band, (0, 0, -0.03), 0.352, 0.07, parent=he)
    for sy, ang in ((1, 18), (-1, -18)):
        cyl(plaid, (0, sy * 0.40, -0.03), 0.2, 0.03, rot=(R(ang), 0, 0), scale=(1.05, 0.62, 1), parent=he)
    for sx in (-1, 1): sphere(plaid, (sx * 0.3, 0, -0.02), 0.1, scale=(0.35, 1, 1.1), parent=he)
    sphere(band, (0, 0, 0.26), 0.05, scale=(1.6, 0.8, 0.8), parent=he)
    gold = _m("loupe", "#D9B24A", rough=0.3, metal=0.9)
    lp = empty((0.33, 0.30, 0.02)); lp.parent = he; lp.rotation_euler = (0, R(-20), R(30))
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), rotation=(0, R(90), 0), major_radius=0.09, minor_radius=0.016)
    o = bpy.context.object; o.data.materials.append(gold); o.parent = lp
    cyl(_m("loupeglass", "#CFE9F5", rough=0.05), (0, 0, 0), 0.08, 0.006, rot=(0, R(90), 0), parent=lp)
    cyl(_m("loupehdl", "#5B3B22", rough=0.5), (0, 0, -0.16), 0.02, 0.14, parent=lp)
    return he


def hat_on_maru(M, t_on, rack_loc=None, rack_h=0.86):
    """帽子：t_on まではかけの上、t_on からまるロボの頭（胴の子。頭のてっぺんは胴の中心から 0.40）"""
    hatw = empty((0, 0, 0)); hp = hat_parts(hatw)
    hm = empty((0, 0, 0)); hm.parent = M.torso; hm.location = (0, -0.03, 0.40); hm.rotation_euler = (R(8), 0, 0); hm.scale = (1.02, 0.93, 1.0)
    hat2 = hat_parts(hm)
    if rack_loc is not None:
        s_ = M.s
        hatw.location = (rack_loc[0], rack_loc[1], rack_h + 0.06 * s_ / 0.4); hatw.scale = (s_, s_, s_)
        # v1 の点検：帽子が、かけの上から頭の上へ一瞬で移っていた（ワープ）→ 跳んだまるロボに当たって、かけから頭へ落ちる（0.45 秒）
        #   頭の上の帽子（hm）に写しを重ねる強さを 0→1 にして、かけの上から頭の上へ動かす。重なりきった t_on で頭の帽子に替える
        ct = hatw.constraints.new("COPY_TRANSFORMS"); ct.target = hm
        ct.influence = 0.0; ct.keyframe_insert("influence", frame=f(t_on - 0.45))
        ct.influence = 1.0; ct.keyframe_insert("influence", frame=f(t_on))
        hide_key(hatw, -100.0, False); hide_key(hatw, t_on + 0.05, True)
        for o in hatw.children_recursive: hide_key(o, -100.0, False); hide_key(o, t_on, True)
    else:
        hide_key(hatw, -100.0, True)
        for o in hatw.children_recursive: hide_key(o, -100.0, True)
    for o in [hm] + list(hm.children_recursive): hide_key(o, -100.0, True); hide_key(o, t_on, False)
    return hm


def trash_can(loc):
    """ゴミ箱（低い円筒。倒すと中の紙くずが出る）。戻り値：dict(root（足もとのふち＝倒れる軸）, papers)"""
    root = empty(loc)
    can = _m("trash", "#7DA6C9", rough=0.5)
    body = empty((0, 0, 0)); body.parent = root
    cyl(can, (0, 0, 0.11), 0.10, 0.22, parent=body)
    cyl(_m("trashin", "#3A4250", rough=0.8), (0, 0, 0.215), 0.09, 0.01, parent=body)
    papers = []
    for k in range(5):
        p = sphere(_m("crumple", "#F4F1EA", rough=0.9), (0.0, 0.0, 0.18), 0.04, scale=(1, 0.9, 0.8), seg=10, parent=root)
        papers.append(p)
    return dict(root=root, body=body, papers=papers)


# ======================================================================== 数字のタイル
def tile_row(center, n=8, size=0.12, gap=0.03, face=0.0, parent=None):
    """数字のタイルを横 1 列に（前＝−y）。戻り値：[dict(root, glow（色のふちの材質）)]。数字は NUM"""
    base = empty(center, R(face))
    if parent is not None: base.parent = parent
    out = []
    W = n * size + (n - 1) * gap
    for k in range(n):
        x = -W / 2 + size / 2 + k * (size + gap)
        r = empty((x, 0, 0)); r.parent = base
        cube(_m("tileback", "#FFFFFF", rough=0.4), (0, 0.006, 0), (size, 0.012, size), bevel=0.012, parent=r)
        plane(img_mat("tileface_" + NUM[k], os.path.join(TEX, "tile_%s.png" % NUM[k]), emit=0.35), (0, -0.0005, 0), (size * 0.92, size * 0.92), rot=(R(90), 0, 0), parent=r)
        gm = mat("tileglow%d_%d" % (len(TILES_ALL), k), "#FFFFFF", rough=0.4, emit=0.001)
        fr = cube(gm, (0, 0.014, 0), (size * 1.24, 0.006, size * 1.24), bevel=0.016, parent=r)      # ふちを太く（試しの絵：光ってもうすかった）
        out.append(dict(root=r, glow=gm, frame=fr))
    TILES_ALL.append(out)
    return base, out


TILES_ALL = []


def tile_color(tl, t, col, strength=9.0, d=0.25):
    """タイルのふちを色で光らせる（t から d 秒で）"""
    m = tl["glow"]; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = srgb(col)      # 地の色は白のまま（試しの絵の点検：地の色を替えると、光らせる前から色が付いた）
    emit_key(m, -100.0, 0.0); emit_key(m, t, 0.0); emit_key(m, t + d, strength)


def tile_off(tl, t, d=0.25, s0=9.0):
    emit_key(tl["glow"], t, s0); emit_key(tl["glow"], t + d, 0.0)


# ======================================================================== 塔（カードの会社）・お店（C）・想像の家
def tower(loc, flag="#3478E6", s=1.0, night=False):
    """カードの会社の塔（白い丸い塔に、三角の屋根と旗。字なし）。戻り値：dict(root, flag, top（光が届く所）)"""
    e = empty(loc, 0.0, s)
    wall = _m("towerwall", "#ECE8E0", rough=0.7)
    cyl(wall, (0, 0, 2.0), 0.9, 4.0, parent=e, verts=32)
    cyl(_m("towerband", flag, rough=0.6), (0, 0, 3.3), 0.92, 0.25, parent=e, verts=32)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.1, radius2=0, depth=1.4, location=(0, 0, 0))
    o = bpy.context.object; o.data.materials.append(_m("towerroof", "#5B6FA8", rough=0.6)); o.parent = e; o.location = (0, 0, 4.7)
    cyl(_m("pole", "#3A3D42", metal=0.7, rough=0.4), (0, 0, 5.9), 0.03, 1.2, parent=e)
    fl = cube(_m("flag" + flag, flag, rough=0.8), (0.32, 0, 6.25), (0.6, 0.02, 0.38), parent=e)
    for j in range(3):
        a_ = R(-90 + (j - 1) * 30)
        cube(glow_mat("twin" + flag, "#FFC870", 1.5) if night else _m("twin_d", "#2E3A55", rough=0.6), (0.91 * math.cos(a_), 0.91 * math.sin(a_), 2.6), (0.12, 0.12, 0.5), rot=(0, 0, a_ + R(90)), parent=e)
    top = empty((0, -0.9, 3.0)); top.parent = e
    return dict(root=e, flag=fl, top=top)


GATE_Y = 0.0
REG = (0.0, 1.4, 0.0)      # レジ（門の内側）


def shop(with_register=True):
    """ネットのお店（C）：町の一角の店先。れんがのかべ・しまの日よけ・アーチの門（上にランプ）・門の内側のレジ・となりの建物・石の歩道・街灯・植木。
    前＝−y。字・印・看板の字は描かない（試しの絵の点検：白い箱だけで、作りが足りなかった）"""
    world("#A9D2F0", 0.85)
    plane(noise_mat("road", "#8E9399", "#868B91", 6.0, 0.9), (0, -9, -0.01), (60, 12))
    walk = wood_floor("sidewalk", "#CFC6B6", "#C3BAA9", "#A39B8C", 0.6, 0.6, 0.1, 0.1)
    plane(walk, (0, -1.6, 0.0), (30, 3.4))
    cube(_m("curb", "#B8B0A2", rough=0.8), (0, -3.35, 0.05), (30, 0.2, 0.12))
    sun(rot=(50, 0, -25), energy=3.2, col="#FFF1DC", angle=6)
    a = area((0, -8, 5), (0, 0, 1.5), energy=900, size=6, col="#EAF2FF"); a.visible_camera = False
    wallm = noise_mat("shopbrick", "#E9C9A8", "#DDB892", 9.0, 0.85, bump=0.2)
    trim = _m("shoptrim", "#7A5A40", rough=0.6)
    GW, GH, HW, HH = 1.9, 2.4, 7.0, 3.6
    cube(wallm, (-(HW / 2 + GW / 2) / 2, 0.15, HH / 2), (HW / 2 - GW / 2, 0.3, HH))
    cube(wallm, ((HW / 2 + GW / 2) / 2, 0.15, HH / 2), (HW / 2 - GW / 2, 0.3, HH))
    cube(wallm, (0, 0.15, (GH + HH) / 2), (GW, 0.3, HH - GH))
    # 腰板（v1 の点検：入り口の前まで 1 本で通っていて、まるロボが通り抜けていた（hitcheck）→ 入り口の左右の 2 つに分ける）
    for sx in (-1, 1): cube(trim, (sx * (HW / 2 + GW / 2 + 0.13) / 2, -0.01, 0.35), (HW / 2 - GW / 2 - 0.13 + 0.01, 0.04, 0.7))
    cube(_m("cornice", "#F4EFE6", rough=0.5), (0, 0.05, HH + 0.08), (HW + 0.2, 0.5, 0.16))
    cube(_m("signbd", "#2E6E8E", rough=0.5), (0, -0.02, 3.35), (2.6, 0.06, 0.4))   # 看板の板（字なし）
    for j in range(3): sphere(_m("signdot", "#FFD24A", rough=0.4), (-0.6 + j * 0.6, -0.06, 3.35), 0.09, seg=16)
    for j in range(14):
        cube(_m("awn%d" % (j % 2), "#E06A5A" if j % 2 == 0 else "#FFFFFF", rough=0.6), (-3.25 + j * 0.5, -0.45, 3.0), (0.5, 0.9, 0.06), rot=(R(-18), 0, 0))
    for j in range(14):
        sphere(_m("awn%d" % (j % 2), "#E06A5A" if j % 2 == 0 else "#FFFFFF", rough=0.6), (-3.25 + j * 0.5, -0.88, 2.86), 0.25, scale=(1, 0.2, 0.5), seg=16)
    fr = noise_mat("gatefr", "#8A6A48", "#7A5A40", 2.0, 0.6, wave=True)
    for sx in (-1, 1): cube(fr, (sx * (GW / 2 + 0.06), -0.02, GH / 2), (0.14, 0.4, GH))
    cube(fr, (0, -0.02, GH + 0.07), (GW + 0.26, 0.4, 0.14))
    lampm = mat("gatelamp", "#FFFFFF", rough=0.3, emit=0.001)
    lamp = sphere(lampm, (0, -0.25, GH + 0.32), 0.14, seg=24)
    cube(_m("lampbase", "#3A3D42", metal=0.6, rough=0.4), (0, -0.2, GH + 0.17), (0.12, 0.12, 0.08))
    for sx in (-1, 1):
        cube(_m("shopwin", "#9FCBE8", rough=0.1), (sx * 2.4, -0.01, 1.55), (1.3, 0.02, 1.1))
        for (xx, zz, ww, hh) in ((sx * 2.4, 1.55, 1.42, 0.06), (sx * 2.4, 2.12, 1.42, 0.08), (sx * 2.4, 0.98, 1.42, 0.08), (sx * 2.4 - 0.68, 1.55, 0.06, 1.2), (sx * 2.4 + 0.68, 1.55, 0.06, 1.2), (sx * 2.4, 1.55, 0.04, 1.1)):
            cube(_m("winfr", "#FFFFFF", rough=0.5), (xx, -0.03, zz), (ww, 0.03, hh))
        cube(_m("wbox", "#7A5A40", rough=0.6), (sx * 2.4, -0.12, 0.9), (1.3, 0.22, 0.16))
        for j in range(5): sphere(_m("flw%d" % (j % 3), ["#E8627A", "#FFD24A", "#8E6CD8"][j % 3], rough=0.6), (sx * 2.4 - 0.5 + j * 0.25, -0.12, 1.02), 0.07, seg=12)
        cyl(_m("pot", "#B5502F", rough=0.6), (sx * 1.35, -0.6, 0.2), 0.2, 0.4)
        sphere(_m("bush", "#5E9150", rough=0.8), (sx * 1.35, -0.6, 0.62), 0.32, seg=16)
    # 街灯・ベンチ・となりの建物
    cyl(_m("lpost", "#2E3440", metal=0.6, rough=0.4), (-4.4, -2.9, 1.6), 0.05, 3.2)
    sphere(glow_mat("lglobe", "#FFF4DA", 1.2), (-4.4, -2.9, 3.25), 0.18, seg=16)
    cube(noise_mat("bench", "#9C7048", "#8A6040", 2.0, 0.6, wave=True), (3.6, -1.2, 0.45), (1.2, 0.4, 0.06))
    for sx in (-1, 1): cube(_m("benchleg", "#2E3440", rough=0.5), (3.6 + sx * 0.5, -1.2, 0.22), (0.06, 0.36, 0.44))
    for (x0, col, h) in ((-6.0, "#B7C9D8", 4.6), (6.1, "#D8C3A5", 4.2), (-9.2, "#C9B4C9", 5.0), (9.3, "#B5CDB2", 3.8)):
        cube(_m("nb" + col, col, rough=0.8), (x0, 0.6, h / 2), (3.0, 1.6, h))
        for i in range(2):
            for j in range(3): cube(_m("nbwin", "#7FA8C8", rough=0.2), (x0 - 0.9 + j * 0.9, -0.21, 1.4 + i * 1.3), (0.5, 0.02, 0.7))
    plane(noise_mat("shopfloor", "#C9B79C", "#BBA98E", 4.0, 0.7), (0, 2.5, 0.004), (6.6, 5.0))
    cube(_m("backwall", "#EADFCB", rough=0.8), (0, 5.0, 1.8), (7.0, 0.2, 3.6))
    # 店の中の天井と左右のかべ（試しの絵：中から見ると空が見えた）。天井には丸い照明
    cube(_m("ceil", "#F4EFE6", rough=0.8), (0, 2.65, 3.62), (7.0, 4.9, 0.08))
    for sx in (-1, 1): cube(_m("sidewall", "#EADFCB", rough=0.8), (sx * 3.45, 2.65, 1.8), (0.1, 4.9, 3.6))
    for (xx, yy) in ((-1.5, 1.6), (1.5, 1.6), (-1.5, 3.6), (1.5, 3.6)):
        cyl(glow_mat("ceilamp", "#FFF4DA", 2.0), (xx, yy, 3.56), 0.22, 0.04)
    for sx in (-1, 1):   # 中の棚（品物の箱。字なし）
        cube(_m("shelfin", "#A07850", rough=0.6), (sx * 1.9, 4.6, 1.0), (1.6, 0.5, 2.0))
        for i in range(3):
            for j in range(4): cube(_m("goods%d" % ((i + j) % 4), ["#E8627A", "#FFD24A", "#5AA9E6", "#7CC08A"][(i + j) % 4], rough=0.6), (sx * 1.9 - 0.55 + j * 0.37, 4.32, 0.45 + i * 0.55), (0.3, 0.25, 0.35))
    bpy.ops.object.light_add(type='POINT', location=(0, 2.4, 2.8)); il = bpy.context.object; il.data.energy = 220; il.data.color = (1.0, 0.93, 0.82); il.data.shadow_soft_size = 0.6
    out = dict(lamp=lamp, lampm=lampm)
    if with_register: out.update(register(REG))
    return out


def register(loc):
    """レジ（まるロボ 0.72 倍の背の高さの台）：上に 8 つのますの画面（絵を時刻で替える）、手前に数字のキー 10 個（2 列）"""
    e = empty(loc)
    cube(_m("regbody", "#5A6475", rough=0.5, metal=0.3), (0, 0, 0.45), (0.9, 0.5, 0.9), bevel=0.02, parent=e)
    scrn = empty((0, 0.05, 1.12)); scrn.parent = e
    cube(_m("regscr_fr", "#2A2F38", rough=0.4), (0, 0.02, 0), (0.86, 0.06, 0.36), bevel=0.01, parent=scrn)
    keys = {}
    for k, ch in enumerate("1234567890"):
        i, j = divmod(k, 5)
        kx = -0.32 + j * 0.16; ky = -0.27 - i * 0.0; kz = 0.82 - i * 0.16
        ke = empty((kx, ky, kz)); ke.parent = e
        cube(_m("keycap", "#F8F8FA", rough=0.4), (0, 0, 0), (0.13, 0.05, 0.13), bevel=0.012, parent=ke)
        plane(img_mat("keyface_" + ch, os.path.join(TEX, "key_%s.png" % ch), emit=0.2), (0, -0.026, 0), (0.11, 0.11), rot=(R(90), 0, 0), parent=ke)
        keys[ch] = ke
    return dict(reg=e, screen=scrn, keys=keys)


def reg_screen(scr_parent, states, glow=1.4):
    """レジの画面の絵を時刻で替える。states：[(時刻, 絵の名前), …]"""
    planes = []
    for k, (t, nm) in enumerate(states):
        p = plane(img_mat("regtex_" + nm, os.path.join(TEX, nm + ".png"), emit=glow), (0, -0.012 - 0.0004 * k, 0), (0.80, 0.30), rot=(R(90), 0, 0), parent=scr_parent)
        t1 = states[k + 1][0] if k + 1 < len(states) else 1e6
        hide_key(p, -100.0, True); hide_key(p, t, False); hide_key(p, t1, True)
        planes.append(p)
    return planes


def press_key(ke, t, depth=0.03):
    p0 = tuple(ke.location)
    key(ke, "location", t, p0); key(ke, "location", t + 0.08, (p0[0], p0[1] + depth, p0[2])); key(ke, "location", t + 0.22, p0)


def little_house(loc, face=0.0, wall="#F2D9B5"):
    """想像の場面の「知らない人の家」（小さな家とポスト）"""
    e = empty(loc, R(face))
    cube(_m("lh_wall" + wall, wall, rough=0.7), (0, 0, 1.0), (2.2, 1.8, 2.0), parent=e)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.75, radius2=0, depth=1.1, location=(0, 0, 0))
    o = bpy.context.object; o.data.materials.append(_m("lh_roof", "#B5502F", rough=0.6)); o.parent = e; o.location = (0, 0, 2.55); o.rotation_euler = (0, 0, R(45))
    cube(_m("lh_door", "#7A5A40", rough=0.6), (0.4, -0.91, 0.6), (0.5, 0.02, 1.2), parent=e)
    post = empty((-0.9, -1.4, 0)); post.parent = e
    cyl(_m("post_leg", "#3A3D42", rough=0.5), (0, 0, 0.45), 0.03, 0.9, parent=post)
    cube(_m("post_box", "#E23A30", rough=0.5), (0, 0, 1.0), (0.32, 0.24, 0.22), bevel=0.02, parent=post)
    return dict(root=e, post=post)


# ======================================================================== 影（3章から。2章の終わりにうっすら）
def _shadow_mat():
    """影の材質：黒。輪郭（横から見える所）だけ紫が少し光る"""
    m = bpy.data.materials.new("shadow"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.012, 0.010, 0.018, 1); b.inputs["Roughness"].default_value = 0.95
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    rp = nt.nodes.new("ShaderNodeMath"); rp.operation = 'POWER'; rp.inputs[1].default_value = 2.5
    nt.links.new(lw.outputs["Facing"], rp.inputs[0])
    b.inputs["Emission Color"].default_value = srgb(PURPLE)
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 1.3
    nt.links.new(rp.outputs[0], mu.inputs[0]); nt.links.new(mu.outputs[0], b.inputs["Emission Strength"])
    return m


class Shadow:
    pass


def shadow(loc, face=0.0, s=1.0):
    """影（泥棒）。顔も姿も描かない黒い丸い形（頭と胴と、細い腕 1 本）。前＝−y。root を動かす。arm（腕の付け根）を回して物を出す"""
    sm = _shadow_mat()
    root = empty(loc, R(face), s)
    sphere(sm, (0, 0, 0.82), 0.42, scale=(0.95, 0.7, 1.35), parent=root, seg=32)
    sphere(sm, (0, 0, 1.55), 0.24, scale=(1.0, 0.95, 1.05), parent=root, seg=32)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.48, radius2=0.2, depth=0.5, location=(0, 0, 0.25))
    sk = bpy.context.object; sk.data.materials.append(sm); sk.parent = root           # すそ（足を見せない）
    arm = empty((0.3, -0.05, 1.12)); arm.parent = root
    cyl(sm, (0, -0.2, 0), 0.055, 0.4, rot=(R(90), 0, 0), parent=arm, verts=16)
    hand = empty((0, -0.42, 0)); hand.parent = arm
    sphere(sm, (0, 0, 0), 0.07, parent=hand, seg=16)
    arm.rotation_euler = (R(-60), 0, 0)      # ふだんは腕を下ろす
    sh = Shadow(); sh.root = root; sh.arm = arm; sh.hand = hand; sh.mat = sm
    return sh


