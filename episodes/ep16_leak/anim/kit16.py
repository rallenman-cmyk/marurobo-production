# 16本目（情報流出）：3D の部品（scenes.py が exec で読む。前提：KIT_HERE と TEX（絵のフォルダ）を決めてから読む）
#   まるロボ・人・材質・光・カメラは 6本目（ep06_haizen/anim/kit.py → 3本目の部品）をそのまま読み込む（9本目の kit9.py と同じ）
#   まるロボの家（部屋・家具・スマホ）は 5本目（ep05_vacuum/anim/kit.py）の room・furniture・phone_seq をそのまま読み込む
#   新しく作った物：お城（正面の門・石のかべ・塔・横の裏口）・門番さん・名札・影・鍵・古い錠・部品の箱・お店の模型・机
#   決まり：3D の中に字を書かない。まるロボは喋らない。名札＝青緑（まるロボ）・橙・緑。影は黒（輪郭だけ紫）。影の錠は赤（2章）
#   絵コンテ表：../絵コンテ_v1.md
import os, sys, math, importlib.util
_K16 = KIT_HERE
KIT_HERE = os.path.join(_K16, "..", "..", "ep06_haizen", "anim")
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
KIT_HERE = _K16
# ---------------------------------------------------------------- 5本目の部屋（間取り plan は 5本目の物を別の名前で読む）
_sp5 = importlib.util.spec_from_file_location("plan5", os.path.join(_K16, "..", "..", "ep05_vacuum", "anim", "plan.py"))
plan5 = importlib.util.module_from_spec(_sp5); _sp5.loader.exec_module(plan5)
RUGOBJ = []
_src5 = open(os.path.join(_K16, "..", "..", "ep05_vacuum", "anim", "kit.py"), encoding="utf-8").read()
_a5 = _src5.index("DESK_TOP = 0.755"); _b5 = _src5.index("# ---------------- 点の地図")
exec(_src5[_a5:_b5].replace("plan.", "plan5."))

PURPLE = "#7B5BD6"
STONE1, STONE2 = "#B7AE9F", "#A39A8B"


def _m(name, col, **kw): return mat(name, col, **kw)


# ======================================================================== お城（B・C）
#   お城の正面は y=0 の面（手前が −y）。門は x=0。横の裏口は右のかべ（x=+CW/2）の、y=CY0+2.0 の所
CW = 14.0          # お城の横の長さ
CD = 10.0          # 奥行き
CH = 5.6           # かべの高さ
GATE_W, GATE_H = 2.8, 3.6
DOOR_Y = 3.2       # 裏口のまん中の y（右のかべ）
DOOR_W, DOOR_H = 0.9, 1.45
X_SIDE = CW / 2    # 右のかべの外の面の x
CASTLE = {}


_STONE = []


def _stone():
    """石を積んだかべ（石の目地と、石ごとの色のちがい・でこぼこ）。一色の面にしない（SKILL §5 作り込んだ舞台）"""
    if _STONE: return _STONE[0]
    m = bpy.data.materials.new("stone"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0.5; br.squash = 1.0
    br.inputs["Scale"].default_value = 1.6; br.inputs["Mortar Size"].default_value = 0.025; br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = 0.6; br.inputs["Row Height"].default_value = 0.3
    br.inputs["Color1"].default_value = srgb(STONE1); br.inputs["Color2"].default_value = srgb(STONE2); br.inputs["Mortar"].default_value = srgb("#8A8275")
    # かべの向きに関係なく、横に積む：u＝世界の x＋y、v＝高さ z（縦じまにならない）
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sp.inputs[0])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'ADD'; nt.links.new(sp.outputs[0], ad.inputs[0]); nt.links.new(sp.outputs[1], ad.inputs[1])
    cb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(ad.outputs[0], cb.inputs[0]); nt.links.new(sp.outputs[2], cb.inputs[1])
    nt.links.new(cb.outputs[0], br.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.2
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs["Factor"].default_value = 0.18
    nt.links.new(br.outputs["Color"], mx.inputs[6]); nt.links.new(nz.outputs["Color"], mx.inputs[7])
    nt.links.new(mx.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.88
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.35
    nt.links.new(br.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    _STONE.append(m)
    return m


def castle(night=False):
    """お城の外（正面・右の横・塔・門・裏口）。night＝夜（月の光・窓の明かり・門のランタン）"""
    if night:
        world("#1B2440", 0.35)
    else:
        world("#BFDDF2", 0.9)
    st = _stone()
    # 地面（芝生）と、門へ続く石の道、右の横の細い道
    plane(noise_mat("grass", "#7DB36A", "#6FA35E", 6.0, 0.95), (0, -10, 0), (90, 90))
    plane(noise_mat("path", "#CDBFA6", "#BFB196", 4.0, 0.9), (0, -9.0, 0.005), (3.4, 18.0))
    plane(noise_mat("path", "#CDBFA6", "#BFB196", 4.0, 0.9), (X_SIDE + 1.2, DOOR_Y - 4.0, 0.006), (1.2, 12.0))
    # かべ（正面は門の穴をあけて 3 つに分ける）
    gx = GATE_W / 2
    cube(st, (-(CW / 2 + gx) / 2, 0.75, CH / 2), (CW / 2 - gx, 1.5, CH))
    cube(st, ((CW / 2 + gx) / 2, 0.75, CH / 2), (CW / 2 - gx, 1.5, CH))
    cube(st, (0, 0.75, (GATE_H + CH) / 2), (GATE_W, 1.5, CH - GATE_H))
    # 横と奥のかべ・中の中庭の床（中は見せない）
    cube(st, (X_SIDE - 0.75, CD / 2, CH / 2), (1.5, CD, CH))
    cube(st, (-X_SIDE + 0.75, CD / 2, CH / 2), (1.5, CD, CH))
    cube(st, (0, CD - 0.75, CH / 2), (CW, 1.5, CH))
    cube(_m("court", "#8E8576", rough=0.9), (0, CD / 2, 0.02), (CW - 2, CD - 2, 0.04))
    # 上のぎざぎざ（正面と右）
    for k in range(int(CW / 0.9)):
        x = -CW / 2 + 0.45 + k * 0.9
        if k % 2 == 0: cube(st, (x, 0.2, CH + 0.3), (0.55, 0.4, 0.6))
    for k in range(int(CD / 0.9)):
        y = 0.45 + k * 0.9
        if k % 2 == 0: cube(st, (X_SIDE - 0.2, y, CH + 0.3), (0.4, 0.55, 0.6))
    # 角の塔（丸い塔に三角の屋根）
    roof = _m("roof", "#5B6FA8", rough=0.6)
    for (tx, ty) in ((-CW / 2, 0.4), (CW / 2, 0.4), (CW / 2, CD - 0.4), (-CW / 2, CD - 0.4)):
        cyl(st, (tx, ty, (CH + 2.2) / 2), 1.4, CH + 2.2)
        bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=1.65, radius2=0.0, depth=2.4, location=(tx, ty, CH + 2.2 + 1.2))
        o = bpy.context.object; o.data.materials.append(roof)
        for j in range(3):   # 塔の窓（夜は明かり）
            a_ = R(-90 + j * 40)
            cube(glow_mat("twin", "#FFC870", 2.2) if night else _m("twin_d", "#2E2A26", rough=0.6),
                 (tx + 1.41 * math.cos(a_), ty + 1.41 * math.sin(a_), CH + 0.8), (0.1, 0.1, 0.5), rot=(0, 0, a_ + R(90)))
    # 門（木の 2 枚の扉に鉄の帯と鋲。アーチの上の石）
    wood = noise_mat("gatewood", "#7A5432", "#6B4A2C", 1.5, 0.7, wave=True)
    iron = _m("iron", "#3A3D42", rough=0.45, metal=0.8)
    # 左右 2 枚の扉。それぞれ外の端（蝶つがい）を中心に開く（07-01 の想像の場面で開く）
    leaves = []
    for sx in (-1, 1):
        hg = empty((sx * GATE_W / 2, -0.02, 0))
        lw = GATE_W / 2 - 0.02
        cube(wood, (-sx * lw / 2, 0.05, GATE_H / 2), (lw, 0.18, GATE_H), parent=hg)
        for zz in (0.6, 1.8, 3.0):
            cube(iron, (-sx * lw / 2, -0.05, zz), (lw - 0.08, 0.03, 0.14), parent=hg)
            for kk in range(4):
                sphere(iron, (-sx * (0.2 + kk * 0.32), -0.07, zz), 0.03, parent=hg, seg=12)
        cyl(iron, (-sx * (lw - 0.25), -0.08, 1.6), 0.09, 0.03, rot=(R(90), 0, 0), parent=hg)
        leaves.append(hg)
    CASTLE["gate"] = leaves
    # 旗（字なし）
    for sx in (-1, 1):
        cyl(iron, (sx * 3.2, -0.1, CH + 1.2), 0.03, 2.4)
        cube(_m("flag", "#C84B4B", rough=0.8), (sx * 3.2 + 0.32, -0.1, CH + 2.05), (0.6, 0.02, 0.38))
    # 裏口（右のかべの外の面。低い所の小さな木の扉。古い錠）
    door_wood = noise_mat("doorwood", "#7C6448", "#6A5440", 1.2, 0.85, wave=True)
    hinge = empty((X_SIDE + 0.02, DOOR_Y - DOOR_W / 2, 0.0))      # 蝶つがい（扉の手前の端）。z 回りに開く
    cube(door_wood, (0.04, DOOR_W / 2, DOOR_H / 2), (0.08, DOOR_W, DOOR_H), parent=hinge)
    for zz in (0.3, 1.15):
        cube(_m("rust", "#6E4A2E", rough=0.8, metal=0.5), (0.09, DOOR_W / 2, zz), (0.02, DOOR_W - 0.08, 0.08), parent=hinge)
    door_hole(DOOR_Y)
    CASTLE["door"] = hinge
    lk = old_lock((X_SIDE + 0.16, DOOR_Y + DOOR_W / 2 - 0.14, 0.82), face=90.0)
    lk["root"].parent = hinge; lk["root"].location = (0.12, DOOR_W - 0.14, 0.82)
    CASTLE["lock"] = lk
    # 明かり
    if night:
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 10)); s_ = bpy.context.object
        s_.rotation_euler = (R(55), 0, R(-35)); s_.data.energy = 0.55; s_.data.color = srgb("#AFC4FF")[:3]; s_.data.angle = R(3)
        bpy.ops.object.light_add(type='POINT', location=(1.6, -1.2, 2.2)); lt = bpy.context.object; lt.data.energy = 120; lt.data.color = srgb("#FFB25E")[:3]; lt.data.shadow_soft_size = 0.2
        cyl(glow_mat("lantern", "#FFC26E", 4.0), (1.6, -1.2, 2.2), 0.09, 0.22)
        bpy.ops.object.light_add(type='POINT', location=(X_SIDE + 2.0, DOOR_Y, 2.4)); l2 = bpy.context.object; l2.data.energy = 35; l2.data.color = srgb("#9FB6FF")[:3]; l2.data.shadow_soft_size = 0.5
    else:
        sun(rot=(48, 0, -30), energy=3.4, col="#FFF1DC", angle=6)
        a = area((0, -14, 6), (0, 0, 2), energy=1400, size=8, col="#EAF2FF"); a.visible_camera = False
        a2 = area((X_SIDE + 8, DOOR_Y - 4, 4), (X_SIDE, DOOR_Y, 1), energy=600, size=5, col="#FFF4E2"); a2.visible_camera = False
    # 遠くの木（背景の形）
    random.seed(16)
    for k in range(26):
        x = random.uniform(-30, 30); y = random.uniform(14, 30)
        if abs(x) < 9 and y < 16: continue
        r = random.uniform(1.0, 2.0)
        sphere(_m("tree_far", random.choice(["#5E9150", "#6FA35E", "#4F8045"]), rough=0.8), (x, y, r * 0.9), r, scale=(1, 1, 1.2), seg=16)
    return CASTLE


def gatekeeper(loc, face=0.0, night=False):
    """門番さん（紺の服に帽子。喋らない）。前＝−y（face=0 で正面の外を向く）"""
    wk = walker(loc, face, shirt="#2E3F6B", pants="#262C3A", hair="#2B2220")
    cyl(_m("cap", "#1E2A4A", rough=0.6), (0, 0, 0.13), 0.19, 0.12, parent=wk.head)
    cube(_m("capvisor", "#1E2A4A", rough=0.5), (0, -0.17, 0.08), (0.24, 0.12, 0.02), parent=wk.head)
    cyl(_m("badge", "#E8C35A", rough=0.3, metal=0.7), (0.09, -0.19, 1.32), 0.035, 0.01, rot=(R(90), 0, 0), parent=wk.root)
    return wk


# ======================================================================== 名札・鍵・錠・影
def nameplate(loc, rot=(0, 0, 0), tex="tag_maru", w=0.30, parent=None, glow=0.0):
    """名札（はがきの形の白い板に、字のない絵の面）。w＝横の長さ（m）"""
    e = empty(loc); e.rotation_euler = rot
    if parent is not None: e.parent = parent
    h = w * 380 / 600
    cube(_m("tagback", "#F4F6F8", rough=0.5), (0, 0, 0), (w, h, 0.008), bevel=0.004, parent=e)
    plane(img_mat("tagface_" + tex, os.path.join(TEX, tex + ".png"), emit=glow), (0, 0, 0.0045), (w, h), parent=e)
    return e


def key_obj(loc, rot=(0, 0, 0), col="#C9A24A", simple=False, s=1.0, parent=None):
    """鍵（輪・軸・歯）。simple＝歯が 1 つだけの、短くかんたんな形の鍵（10-07）。前＝+x"""
    e = empty(loc); e.rotation_euler = rot; e.scale = (s, s, s)
    if parent is not None: e.parent = parent
    m = _m("key" + col, col, rough=0.3, metal=0.85)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), rotation=(R(90), 0, 0), major_radius=0.045, minor_radius=0.012)
    o = bpy.context.object; o.data.materials.append(m); o.parent = e
    L = 0.08 if simple else 0.14
    cyl(m, (0.045 + L / 2, 0, 0), 0.011, L, rot=(0, R(90), 0), parent=e, verts=16)
    teeth = [(0.045 + L - 0.02, 0.03)] if simple else [(0.12, 0.028), (0.145, 0.018), (0.165, 0.032), (0.18, 0.022)]
    for (x, h) in teeth:
        cube(m, (x, 0, -0.011 - h / 2), (0.014, 0.008, h), parent=e)
    return e


def old_lock(loc, face=0.0, crack=True):
    """古い錠（錆びた四角い錠前と、上の輪）。face＝錠の前の向き（度。0＝−y）。crack＝弱い所のひび（10-05 で赤く光らせる）"""
    root = empty(loc, R(face))
    rust = noise_mat("rustlock", "#8C5A34", "#6E4426", 18.0, 0.8, bump=0.5)
    cube(rust, (0, 0, 0), (0.16, 0.06, 0.13), bevel=0.01, parent=root)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0.09), rotation=(R(90), 0, 0), major_radius=0.05, minor_radius=0.011)
    sh = bpy.context.object; sh.data.materials.append(_m("shackle", "#7A6A58", rough=0.6, metal=0.6)); sh.parent = root
    cyl(_m("keyhole", "#1A1410", rough=0.7), (0, -0.031, -0.01), 0.012, 0.004, rot=(R(90), 0, 0), parent=root, verts=16)
    out = dict(root=root, crack=None, crack_objs=[])
    if crack:
        cm = mat("crack_glow", "#FF3B2F", rough=0.4, emit=0.001)
        c = cube(cm, (0.035, -0.0315, 0.02), (0.006, 0.002, 0.07), rot=(0, R(25), 0), parent=root)
        c2 = cube(cm, (0.05, -0.0315, -0.02), (0.005, 0.002, 0.04), rot=(0, R(-35), 0), parent=root)
        for o in (c, c2): o.hide_render = True        # ふだんは見えない（弱い所を先に見せない）。10-05 で出す
        out["crack"] = cm; out["crack_objs"] = [c, c2]
    return out


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


def parts_box(loc, s=1.0):
    """部品の入った小さな箱（10-03・10-05。段ボールの色。字なし）"""
    e = empty(loc, 0.0, s)
    cube(_m("cardboard", "#C9A16E", rough=0.85), (0, 0, 0.09), (0.32, 0.24, 0.18), bevel=0.006, parent=e)
    cube(_m("tape", "#E8D8B8", rough=0.6), (0, 0, 0.181), (0.33, 0.05, 0.003), parent=e)
    return e


# ======================================================================== 机の上のたとえ（05）・小窓の部品
def shop_model(loc, s=1.0):
    """お店の模型（小さな建物にしまの日よけ。字・印なし）"""
    e = empty(loc, 0.0, s)
    cube(_m("shopwall", "#F4EFE6", rough=0.6), (0, 0, 0.1), (0.3, 0.2, 0.2), parent=e)
    for k in range(6):
        cube(_m("awn" + str(k % 2), "#D9534F" if k % 2 == 0 else "#FFFFFF", rough=0.7), (-0.125 + k * 0.05, -0.12, 0.17), (0.05, 0.06, 0.02), rot=(R(25), 0, 0), parent=e)
    cube(_m("shopdoor", "#8EC5E8", rough=0.2), (0, -0.101, 0.07), (0.08, 0.004, 0.12), parent=e)
    cube(_m("shoproof", "#7A5A40", rough=0.6), (0, 0, 0.215), (0.34, 0.24, 0.03), parent=e)
    return e


def door_hole(yc):
    """裏口の奥の暗がり（扉が開くと見える）と、まわりの石の枠（少し出っぱる）。v1：開いても、うしろの石のかべが見えるだけだった"""
    cube(_m("doorhole", "#121214", rough=1.0), (X_SIDE + 0.004, yc, DOOR_H / 2), (0.004, DOOR_W, DOOR_H))
    for (yy, zz, sy, sz) in ((yc - DOOR_W / 2 - 0.1, DOOR_H / 2, 0.2, DOOR_H), (yc + DOOR_W / 2 + 0.1, DOOR_H / 2, 0.2, DOOR_H), (yc, DOOR_H + 0.1, DOOR_W + 0.4, 0.2)):
        cube(_m("doorframe_st", "#9C9384", rough=0.85), (X_SIDE + 0.05 + (0.01 if sz < 0.5 else 0), yy, zz), (0.12 + (0.02 if sz < 0.5 else 0), sy, sz))


def castle_model(loc, s=1.0):
    """お城の模型（05 の机の上。本物のお城と同じ色・形を小さく）"""
    e = empty(loc, 0.0, s)
    st = _m("stone_model", "#A99E8C", rough=0.9)      # 模型は無地の石の色（大きなお城の石の模様は、小さな模型では太い帯に見え、白っぽく見えた。v1 の点検）
    cube(st, (0, 0, 0.09), (0.36, 0.24, 0.18), parent=e)
    for (tx, ty) in ((-0.18, -0.12), (0.18, -0.12), (0.18, 0.12), (-0.18, 0.12)):
        cyl(st, (tx, ty, 0.13), 0.05, 0.26, parent=e, verts=24)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.06, radius2=0, depth=0.08, location=(0, 0, 0))
        o = bpy.context.object; o.data.materials.append(_m("roof", "#5B6FA8", rough=0.6)); o.parent = e; o.location = (tx, ty, 0.30)
    cube(noise_mat("gatewood", "#7A5432", "#6B4A2C", 1.5, 0.7, wave=True), (0, -0.121, 0.06), (0.09, 0.004, 0.11), parent=e)
    return e


def board(loc, tex, w=0.22, h=0.26, rot_z=0.0, glow=0.6):
    """立てた板（入力の画面など。絵の面だけ）"""
    e = empty(loc, R(rot_z))
    cube(_m("boardback", "#E8ECF2", rough=0.5), (0, 0.006, h / 2), (w + 0.01, 0.01, h + 0.01), parent=e)
    plane(img_mat("board_" + tex, os.path.join(TEX, tex + ".png"), emit=glow), (0, 0, h / 2), (w, h), rot=(R(90), 0, 0), parent=e)
    return e


def pw_board(loc, w=0.22, h=0.08):
    """パスワードの欄（白い板に黒い丸が 4 つ。字ではない）"""
    e = empty(loc)
    cube(_m("pwback", "#FFFFFF", rough=0.5), (0, 0, h / 2), (w, 0.012, h), bevel=0.004, parent=e)
    for k in range(4):
        sphere(_m("pwdot", "#1D2433", rough=0.4), (-0.06 + k * 0.04, -0.008, h / 2), 0.011, scale=(1, 0.4, 1), parent=e, seg=16)
    return e


def table_set(loc=(0, 0, 0)):
    """05 の机（木の天板。まわりは部屋の壁の色をぼかした地）"""
    cube(noise_mat("deskwood", "#C79A6B", "#B98C5E", 2.5, 0.45, wave=True), (loc[0], loc[1], loc[2] - 0.025), (1.6, 0.9, 0.05), bevel=0.01)
    world("#F2ECE2", 0.22)      # v1 の点検：白く飛んでいた（0.5・160・60）
    a = area((loc[0] - 0.6, loc[1] - 1.2, loc[2] + 1.2), loc, energy=85, size=1.6, col="#FFF4E6"); a.visible_camera = False
    a2 = area((loc[0] + 0.9, loc[1] + 0.2, loc[2] + 0.9), loc, energy=30, size=1.0, col="#FFE2C0"); a2.visible_camera = False
    cube(_m("deskbg", "#CDBBA3", rough=0.9), (loc[0], loc[1] + 1.2, loc[2] + 0.4), (4.0, 0.05, 2.0))


def dark_room():
    """07-01 の想像の場面：暗い部屋の机と画面とキーボード（画面の光だけ）"""
    world("#0B0E18", 0.2)
    cube(_m("dkdesk", "#2A2420", rough=0.7), (0, 0, 0.72), (1.4, 0.7, 0.05))
    cube(_m("kb", "#1E2228", rough=0.5), (0, -0.12, 0.755), (0.45, 0.15, 0.02), bevel=0.004)
    for i in range(3):
        for j in range(12):
            cube(_m("kbkey", "#3A4048", rough=0.5), (-0.2 + j * 0.036, -0.17 + i * 0.04, 0.768), (0.03, 0.032, 0.008))
    cube(_m("mon", "#15181E", rough=0.4), (0, 0.18, 1.05), (0.62, 0.04, 0.38), bevel=0.01)
    scr = cube(glow_mat("monscr", "#3FD1FF", 3.0), (0, 0.159, 1.05), (0.58, 0.004, 0.34))
    bpy.ops.object.light_add(type='AREA', location=(0, 0.1, 1.05)); l = bpy.context.object; l.data.energy = 60; l.data.size = 0.5; l.data.color = srgb("#7FD8FF")[:3]
    l.rotation_euler = (R(90), 0, 0)
    return scr
