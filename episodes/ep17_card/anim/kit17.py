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
NUM = "35280471"; WRONG = "35280481"; OTHER = "49280476"      # v1 のコメント「計算で決まる数字」：かんたんな決まり（前の 7 けたを足して、ちょうど 10 のまとまりになるように最後を決める）に合わせた。3+5+2+8+0+4+7=29 → 1。まちがえた番号は 3+5+2+8+0+4+8=30 → 0 のはずが 1。別の会社 4+9+2+8+0+4+7=34 → 6     # WRONG：7 つ目を打ちまちがえた番号（make_tex17.py と同じ）


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


def door17(x1=3.0, y0=1.12, y1=1.78, h=1.9):
    """窓の右どなりの、部屋の出入りのとびら（右のかべ x=3 の内がわ）。下に暗いすき間（05-02「とびらのすき間」。v1 の点検でユーザーが「とびらを足す」を選んだ）"""
    yc = (y0 + y1) / 2; w_ = y1 - y0
    wd = noise_mat("door17", "#B98C5E", "#A97C50", 3.0, 0.6, wave=True)
    cube(wd, (x1 - 0.055, yc, (h + 0.04) / 2), (0.04, w_ - 0.04, h - 0.04), bevel=0.006)      # かべの下の白い板（はば木）より手前
    for zz in (0.55, 1.35):
        cube(_m("door17in", "#C99C6E", rough=0.6), (x1 - 0.078, yc, zz), (0.008, w_ - 0.22, 0.55), bevel=0.004)
    cube(_m("door17gap", "#0A0807", rough=1.0), (x1 - 0.04, yc, 0.02), (0.012, w_ - 0.04, 0.04))      # 下のすき間（暗い。v1 の点検：はば木にかくれて見えなかった → 手前へ）
    fr = _m("door17fr", "#C9A57A", rough=0.5)
    for yy in (y0, y1): cube(fr, (x1 - 0.045, yy, h / 2 + 0.03), (0.09, 0.05, h + 0.06))
    cube(fr, (x1 - 0.045, yc, h + 0.04), (0.09, w_ + 0.05, 0.06))
    sphere(_m("door17knob", "#D9B24A", rough=0.3, metal=0.8), (x1 - 0.105, y0 + 0.1, 0.95), 0.035, seg=16)


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
    # v1 の点検（確認役）：アンテナが帽子を突き抜けて見えた → てっぺんに、アンテナを通す穴のふち（こげ茶の輪）を付け、穴から出ている形にする
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), major_radius=0.07, minor_radius=0.022)
    o = bpy.context.object; o.data.materials.append(band); o.parent = he; o.location = (0, 0.0, 0.255)
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
def tile_row(center, n=8, size=0.12, gap=0.03, face=0.0, parent=None, num=None):
    """数字のタイルを横 1 列に（前＝−y）。戻り値：[dict(root, glow（色のふちの材質）)]。数字は num（なければ NUM）"""
    num = num or NUM
    base = empty(center, R(face))
    if parent is not None: base.parent = parent
    out = []
    W = n * size + (n - 1) * gap
    for k in range(n):
        x = -W / 2 + size / 2 + k * (size + gap)
        r = empty((x, 0, 0)); r.parent = base
        cube(_m("tileback", "#FFFFFF", rough=0.4), (0, 0.006, 0), (size, 0.012, size), bevel=0.012, parent=r)
        plane(img_mat("tileface_" + num[k], os.path.join(TEX, "tile_%s.png" % num[k]), emit=0.35), (0, -0.0005, 0), (size * 0.92, size * 0.92), rot=(R(90), 0, 0), parent=r)
        gm = mat("tileglow%d_%d" % (len(TILES_ALL), k), "#FFFFFF", rough=0.4, emit=0.001)
        fr = cube(gm, (0, 0.014, 0), (size * 1.24, 0.006, size * 1.24), bevel=0.016, parent=r)      # ふちを太く（試しの絵：光ってもうすかった）
        out.append(dict(root=r, glow=gm, frame=fr))
    TILES_ALL.append(out)
    return base, out


TILES_ALL = []


def _col_key(m, t, rgba):
    """ふちの地の色と光の色を、時刻 t の値としてキーを打つ"""
    b = m.node_tree.nodes["Principled BSDF"]
    for nm in ("Base Color", "Emission Color"):
        b.inputs[nm].default_value = rgba; b.inputs[nm].keyframe_insert("default_value", frame=f(t))


def tile_color(tl, t, col, strength=1.2, d=0.25):
    """タイルのふちを色で光らせる（t から d 秒で）。
    17本目 v1 の点検：光の強さ 9 で、青・紫・橙が白に飛んで見分けられなかった（11-01〜14-07）→ 強さ 1.2 にして（3 でもまだうすかった）、ふちの地の色も同じ色にする。
    地の色は t まで白（試しの絵の点検：はじめから地に色を付けると、光らせる前から色が付いた）→ 色は時刻でキーを打って替える"""
    m = tl["glow"]; c = srgb(col); c = tuple(c) + (1.0,) if len(c) == 3 else tuple(c)
    prev = tl.get("_col", (1.0, 1.0, 1.0, 1.0))
    if "_col" not in tl: _col_key(m, -100.0, prev)
    _col_key(m, t, prev); _col_key(m, t + d, c); tl["_col"] = c
    emit_key(m, -100.0, 0.0); emit_key(m, t, 0.0 if not tl.get("_on") else tl["_on"]); emit_key(m, t + d, strength); tl["_on"] = strength


def tile_off(tl, t, d=0.25, s0=None):
    s0 = tl.get("_on", 3.0) if s0 is None else s0
    emit_key(tl["glow"], t, s0); emit_key(tl["glow"], t + d, 0.0); tl["_on"] = 0.0
    prev = tl.get("_col", (1.0, 1.0, 1.0, 1.0)); w_ = (1.0, 1.0, 1.0, 1.0)
    _col_key(tl["glow"], t, prev); _col_key(tl["glow"], t + d, w_); tl["_col"] = w_


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
    lamp.hide_render = True; lamp.hide_viewport = False      # v1 のコメント「監視カメラが丸印つくのは理解できない」：門の上のランプが監視カメラに見えた → 描かない（位置は札・音の目じるしに使う）
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
        p = plane(img_mat("regtex_" + nm, os.path.join(TEX, nm + ".png"), emit=glow), (0, -0.012 - 0.0004 * k, 0), (0.78, 0.29), rot=(R(90), 0, 0), parent=scr_parent)
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

# ======================================================================== 3章（2026-11-24）：影の部屋・箱の機械・番号の札
def slip_obj(loc=(0, 0, 0), rot=(0, 0, 0), tex="slip_0", w=0.30, parent=None):
    """番号の札（横長の白い板。厚み 3 mm。上の面に 8 つのますと数字）。上の面が +z"""
    e = empty(loc); e.rotation_euler = rot
    if parent is not None: e.parent = parent
    h = w * 180 / 1000
    cube(_m("slipedge", "#E6E6E0", rough=0.5), (0, 0, 0), (w, h, 0.004), bevel=0.001, parent=e)
    plane(img_mat("slipface_" + tex, os.path.join(TEX, tex + ".png"), emit=0.35), (0, 0, 0.0021), (w, h), parent=e)
    return e


def machine(loc, face=0.0):
    """箱の形の機械（灰色の箱。前＝−y に札が出る口、上に小さなランプ。字・印・画面はなし。手口は見せない）。
    戻り値：dict(root, body（ゆらす）, lamp（光る材質）, slot（札が出る所の empty）)"""
    root = empty(loc, R(face))
    body = empty((0, 0, 0)); body.parent = root
    cube(_m("machine", "#6E7480", rough=0.45, metal=0.3), (0, 0, 0.42), (0.72, 0.56, 0.84), bevel=0.03, parent=body)
    cube(_m("machtrim", "#4A505A", rough=0.5), (0, 0, 0.86), (0.6, 0.46, 0.04), bevel=0.01, parent=body)
    cube(_m("slotdark", "#15171B", rough=0.9), (0, -0.281, 0.34), (0.42, 0.01, 0.06), parent=body)       # 札が出る口
    for k in range(4): cube(_m("vent", "#3E434C", rough=0.6), (0.24, -0.282, 0.6 - k * 0.05), (0.14, 0.006, 0.018), parent=body)
    lm = mat("machlamp", "#FFB347", rough=0.3, emit=0.001)
    sphere(lm, (-0.2, -0.05, 0.92), 0.05, seg=20, parent=body)
    slot = empty((0, -0.30, 0.34)); slot.parent = body
    return dict(root=root, body=body, lamp=lm, slot=slot)


def dark_room():
    """B：影の部屋（夜。奥のかべ y=2.8 に窓。左のかべ x=-2.6 にドア。机と黄色い電気スタンド）。床は 0。前（−y）は開けておく"""
    world("#0B1020", 0.05)
    fl = wood_floor("dfloor", "#5A4A3C", "#4E4034", "#3A3029", 0.9, 0.14, 0.0, 0.15)   # 別の目の点検：床のつやに電気スタンドが白い丸に映り、何の光か分からなかった → つやなし
    plane(fl, (0, 0.9, 0), (5.4, 4.0))
    wl = noise_mat("dwall", "#4A4F5C", "#434856", 6.0, 0.9)
    WX0, WX1, WZ0, WZ1 = -1.75, -0.65, 0.72, 1.62                           # 窓（奥のかべ）
    for (x0, x1, z0, z1) in ((-2.7, WX0, 0, 2.6), (WX1, 2.7, 0, 2.6), (WX0, WX1, 0, WZ0), (WX0, WX1, WZ1, 2.6)):
        cube(wl, ((x0 + x1) / 2, 2.85, (z0 + z1) / 2), (x1 - x0, 0.1, z1 - z0))
    fr = _m("dwinfr", "#8A8F99", rough=0.5)
    for (xx, zz, ww, hh) in (((WX0 + WX1) / 2, WZ0 - 0.02, WX1 - WX0 + 0.1, 0.05), ((WX0 + WX1) / 2, WZ1 + 0.02, WX1 - WX0 + 0.1, 0.05),
                             (WX0 - 0.02, (WZ0 + WZ1) / 2, 0.05, WZ1 - WZ0), (WX1 + 0.02, (WZ0 + WZ1) / 2, 0.05, WZ1 - WZ0), ((WX0 + WX1) / 2, (WZ0 + WZ1) / 2, 0.03, WZ1 - WZ0)):
        cube(fr, (xx, 2.79, zz), (ww, 0.06, hh))
    for (y0, y1, z0, z1) in ((-1.1, 0.2, 0, 2.6), (1.1, 2.9, 0, 2.6), (0.2, 1.1, 1.92, 2.6)):   # 左のかべ（ドアの穴は y 0.2〜1.1、高さ 1.92）
        cube(wl, (-2.65, (y0 + y1) / 2, (z0 + z1) / 2), (0.1, y1 - y0, z1 - z0))
    door_g = noise_mat("ddoor", "#3B302A", "#33291F", 3.0, 0.6, wave=True)
    hinge = empty((-2.62, 0.2, 0.0))                                          # 蝶つがい（rz を + に回すと外へ開く）
    cube(door_g, (0, 0.45, 0.95), (0.04, 0.88, 1.9), parent=hinge)
    sphere(_m("dknob", "#C9A24A", rough=0.3, metal=0.8), (0.04, 0.8, 0.95), 0.035, seg=12, parent=hinge)
    plane(_m("doutside", "#05070C", rough=1.0), (-3.4, 0.65, 1.0), (2.0, 2.2), rot=(0, R(90), 0))   # ドアの外（暗い廊下）
    cube(wl, (2.65, 0.9, 1.3), (0.1, 4.0, 2.6))
    plane(mat("nightsky", "#16234A", rough=1.0, emit=0.6), (-1.2, 6.0, 1.5), (14, 6), rot=(R(90), 0, 0))
    for k in range(5):                                                       # 窓の外の遠い建物（暗い）
        cube(_m("nbld%d" % k, "#0F1526", rough=0.9), (-3.0 + k * 1.2, 5.5, 0.6 + 0.25 * k % 3), (0.9, 0.3, 1.2 + 0.4 * (k % 3)))
    dw = noise_mat("ddesk", "#6B5440", "#5E4936", 3.0, 0.6, wave=True)
    cube(dw, (1.5, 2.35, 0.74), (1.3, 0.6, 0.04))
    for sx in (-1, 1):
        for sy in (-1, 1): cube(_m("ddeskleg", "#2E2A28", rough=0.5), (1.5 + sx * 0.58, 2.35 + sy * 0.24, 0.37), (0.04, 0.04, 0.74))
    cyl(_m("lampbase2", "#2F3138", rough=0.4), (1.85, 2.45, 0.77), 0.08, 0.02)
    cyl(_m("lamppole", "#2F3138", rough=0.4), (1.85, 2.45, 0.98), 0.012, 0.42)
    cyl(glow_mat("lampshade", "#FFD68A", 3.0), (1.85, 2.38, 1.2), 0.1, 0.12)
    bpy.ops.object.light_add(type='POINT', location=(1.85, 2.3, 1.12)); l = bpy.context.object; l.data.energy = 60.0; l.data.color = (1.0, 0.82, 0.55); l.data.shadow_soft_size = 0.2
    bpy.ops.object.light_add(type='AREA', location=(0.0, -1.6, 2.6)); a = bpy.context.object; a.data.energy = 90.0; a.data.size = 3.0; a.data.color = (0.6, 0.7, 1.0); a.rotation_euler = (R(35), 0, 0)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5)); m = bpy.context.object; m.rotation_euler = (R(60), 0, R(200)); m.data.energy = 0.25; m.data.color = (0.6, 0.7, 1.0)
    cube(_m("outbox", "#20242E", rough=0.9), (-0.9, 3.45, 0.17), (2.6, 0.9, 0.34))   # 窓の外の台（まるロボが乗る。部屋からは見えない）
    return dict(win=((WX0 + WX1) / 2, 2.85, (WZ0 + WZ1) / 2), door=(-2.6, 0.65, 0.0), hinge=hinge)



# ======================================================================== 4章（2026-11-26）：塔の中（台帳）
LEDGER_COLS, LEDGER_ROWS = 16, 8
LEDGER_X0, LEDGER_DX, LEDGER_Z0, LEDGER_DZ, LEDGER_Y = -3.0, 0.4, 3.8, 0.4, 3.9
MY_LAMP = (10, 3)          # まるロボのランプ（左から 11 個目・上から 4 段目）


def ledger_lamp_pos(c, r):
    return (LEDGER_X0 + c * LEDGER_DX, LEDGER_Y, LEDGER_Z0 - r * LEDGER_DZ)


def ledger_room():
    """D：塔の中の明るい丸い部屋。奥のかべ（y=4）一面に台帳のランプ（横 16 × 縦 8。数字は書かない）。
    左のかべ（x=-4.5）に入口（y -0.6〜0.6 の穴）と、光の玉が入る丸い窓（高さ 3.2 m）。
    戻り値：dict(my=まるロボのランプの材質, my_ob, win=丸い窓の場所, door=入口)"""
    world("#F2F4F8", 0.45)                       # 試しの絵の点検：明るすぎて白く飛び、ともったランプが見分けにくかった
    plane(noise_mat("ledfloor", "#C9CED6", "#C0C5CE", 5.0, 0.7), (0, 1.0, 0), (10, 7))
    wall = _m("ledwall", "#ECE8E0", rough=0.8)
    cube(wall, (0, 4.05, 2.4), (9.2, 0.1, 4.8))
    cube(_m("ledband", "#3478E6", rough=0.6), (0, 3.98, 4.45), (9.2, 0.04, 0.25))
    for (y0, y1, z0, z1) in ((-2.5, -0.6, 0, 4.8), (0.6, 4.0, 0, 4.8), (-0.6, 0.6, 2.2, 4.8)):
        cube(wall, (-4.55, (y0 + y1) / 2, (z0 + z1) / 2), (0.1, y1 - y0, z1 - z0))
    cube(wall, (4.55, 0.75, 2.4), (0.1, 6.5, 4.8))
    cube(_m("ledceil", "#F7F7F5", rough=0.8), (0, 0.75, 4.85), (9.2, 6.5, 0.1))
    door_fr = _m("leddoorfr", "#7A5A40", rough=0.6)                 # 入口のわく（別の目の点検：入口がはっきりしなかった）
    for yy in (-0.66, 0.66): cube(door_fr, (-4.49, yy, 1.1), (0.14, 0.12, 2.2))
    cube(door_fr, (-4.49, 0.0, 2.25), (0.14, 1.44, 0.12))
    plane(_m("ledcorridor", "#2A2F38", rough=1.0), (-5.6, 0.0, 1.2), (1.4, 2.4), rot=(0, R(90), 0))   # 入口の外（暗い通路）
    cyl(_m("ledwinfr", "#8A8F99", rough=0.5), (-4.5, 2.2, 3.2), 0.36, 0.14, rot=(0, R(90), 0))
    cyl(mat("ledwinsky", "#9FCBE8", rough=0.3, emit=0.6), (-4.49, 2.2, 3.2), 0.3, 0.16, rot=(0, R(90), 0))
    cube(_m("ledpanel", "#3C4352", rough=0.7), (0, 3.99, 2.4), (6.9, 0.02, 3.4), bevel=0.02)      # 台帳の板（こい色にして、ランプを目立たせる）
    off = _m("lampoff", "#6E7682", rough=0.5)
    # v5 のコメント（10:40「画面が切り替わると、どれがまるロボのか分からない。光の色を変えて」）：ほかの人のランプは、あたたかい白。
    #   まるロボのランプだけ、まるロボの名札の色（青緑）と輪で、どのカットでも見分けられるようにする
    on = glow_mat("lampon", "#FFE2A6", 3.0)
    _b = on.node_tree.nodes["Principled BSDF"]; _b.inputs["Emission Color"].default_value = tuple(srgb("#FFE2A6"))[:3] + (1.0,)
    import random as _r
    rr = _r.Random(21)
    for c in range(LEDGER_COLS):
        for r in range(LEDGER_ROWS):
            if (c, r) == MY_LAMP: continue
            cyl(on if rr.random() < 0.12 else off, ledger_lamp_pos(c, r), 0.11, 0.06, rot=(R(90), 0, 0), verts=24)
    mym = mat("lampmine", "#6E7682", rough=0.5, emit=0.0)
    myo = cyl(mym, ledger_lamp_pos(*MY_LAMP), 0.11, 0.06, rot=(R(90), 0, 0), verts=24)
    _mp = ledger_lamp_pos(*MY_LAMP)
    myring = cyl(glow_mat("lampminering", "#2FD9C8", 5.0), (_mp[0], _mp[1] + 0.03, _mp[2]), 0.17, 0.02, rot=(R(90), 0, 0), verts=32)   # まるロボのランプの輪（ともってから出す）
    for (x, y) in ((-2.0, 0.5), (2.0, 0.5), (0.0, 2.6)):
        cyl(glow_mat("ledceillamp", "#FFF8EA", 2.5), (x, y, 4.79), 0.35, 0.03)
    sun(rot=(55, 0, 20), energy=0.7, col="#FFF4E5", angle=10)
    a = area((0, -3.0, 3.5), (0, 3.0, 2.0), energy=260, size=6, col="#FFFFFF"); a.visible_camera = False
    return dict(my=mym, my_ob=myo, my_ring=myring, win=(-4.4, 2.2, 3.2), door=(-4.5, 0.0, 0.0))


def lamp_color(m, t, col, strength=4.0, d=0.2):
    """まるロボのランプの色と光を t から d 秒で替える（材質の地の色と光の色を時刻でキー）"""
    b = m.node_tree.nodes["Principled BSDF"]
    c = tuple(srgb(col))[:3] + (1.0,)
    prev = tuple(m["_c"]) if "_c" in m else None
    for nm in ("Base Color", "Emission Color"):
        inp = b.inputs[nm]
        if prev is not None:
            inp.default_value = prev; inp.keyframe_insert("default_value", frame=f(t))
        else:
            inp.default_value = tuple(srgb("#6E7682"))[:3] + (1.0,); inp.keyframe_insert("default_value", frame=f(-100.0)); inp.keyframe_insert("default_value", frame=f(t))
        inp.default_value = c; inp.keyframe_insert("default_value", frame=f(t + d))
    m["_c"] = c
    if not m.get("_e"): emit_key(m, -100.0, 0.0); m["_e"] = 1
    emit_key(m, t, m.get("_s", 0.0)); emit_key(m, t + d, strength); m["_s"] = strength


# ======================================================================== 5章（2026-11-27）：門番さん・閉まる門・テストの板・別のお店・大きな設定のスマホ
class Guard:
    pass


def guard(loc, face=0.0, s=1.0):
    """門番さん（無口で、目がいい）。影と同じ丸い胴と丸い頭（すそで足は見せない）に、紺の服・白い丸い顔・大きな丸い目 2 つ・紺の帽子と黄色い帯。口はない。
    前＝−y。root を動かす。arm を回して手を上げる・板を出す。pupils（黒目）を左右へ動かして見回す"""
    navy = _m("gd_navy", "#2B3D6B", rough=0.6); face_m = _m("gd_face", "#F4E3CF", rough=0.6)
    white = _m("gd_eyew", "#FFFFFF", rough=0.3); black = _m("gd_eyeb", "#15171B", rough=0.2, coat=1.0)
    root = empty(loc, R(face), s)
    sphere(navy, (0, 0, 0.82), 0.42, scale=(0.95, 0.75, 1.35), parent=root, seg=32)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.48, radius2=0.2, depth=0.5, location=(0, 0, 0.25))
    sk = bpy.context.object; sk.data.materials.append(navy); sk.parent = root
    for zz in (0.95, 0.72): sphere(_m("gd_btn", "#E8C24A", rough=0.4, metal=0.6), (0, -0.315, zz), 0.035, parent=root, seg=12)   # 服のボタン
    head = empty((0, 0, 1.55)); head.parent = root
    sphere(face_m, (0, 0, 0), 0.26, parent=head, seg=32)
    pupils = []
    for sx in (-1, 1):
        sphere(white, (sx * 0.1, -0.2, 0.02), 0.085, scale=(1.0, 0.6, 1.1), parent=head, seg=24)
        pe = empty((sx * 0.1, -0.245, 0.02)); pe.parent = head
        sphere(black, (0, 0, 0), 0.045, scale=(1.0, 0.5, 1.0), parent=pe, seg=16); pupils.append(pe)
    cyl(navy, (0, 0, 0.2), 0.27, 0.16, parent=head, verts=32)                                   # 帽子
    cyl(_m("gd_band", "#F2C230", rough=0.5), (0, 0, 0.14), 0.275, 0.05, parent=head, verts=32)  # 黄色い帯
    cube(navy, (0, -0.25, 0.13), (0.4, 0.16, 0.025), parent=head)                               # つば
    arm = empty((0.33, -0.05, 1.12)); arm.parent = root
    cyl(navy, (0, -0.2, 0), 0.06, 0.4, rot=(R(90), 0, 0), parent=arm, verts=16)
    hand = empty((0, -0.42, 0)); hand.parent = arm
    sphere(_m("gd_glove", "#FFFFFF", rough=0.6), (0, 0, 0), 0.08, parent=hand, seg=16)
    arm.rotation_euler = (R(60), 0, 0)      # 試しの絵の点検：x の角度が − だと腕が上がる（+60 で下ろす・−80 で手を上げる・−5 で前へ出す）
    g = Guard(); g.root = root; g.arm = arm; g.hand = hand; g.head = head; g.pupils = pupils
    return g


def guard_look(g, t, dx, d=0.35):
    """門番さんの黒目を左右へ（dx：m。＋で門番さんの左＝画面の右）"""
    for pe in g.pupils:
        x0 = pe.location[0] if not pe.get("_x0") else pe["_x0"]
        pe["_x0"] = x0
        cur = pe.get("_dx", 0.0)
        key(pe, "location", t, (x0 + cur, pe.location[1], pe.location[2])); key(pe, "location", t + d, (x0 + dx, pe.location[1], pe.location[2]))
        pe["_dx"] = dx


def gate_bar_lamp():
    """門の上の細長いランプ（v1 のコメント「監視カメラに見えた」丸いランプのかわり。横長の光る棒＝明かりと分かる形）。戻り値：材質（色を時刻で替える）"""
    GH = 2.4
    m = mat("gatebar", "#E6E6E0", rough=0.3, emit=0.0)
    cube(_m("gatebarbase", "#3A3D42", rough=0.5), (0, -0.24, GH + 0.3), (0.86, 0.12, 0.2), bevel=0.03)
    o = cyl(m, (0, -0.31, GH + 0.3), 0.07, 0.76, rot=(0, R(90), 0), verts=24)
    return m, o


def gate_grille(t_drop=None, d=0.28):
    """門をふさぐ格子（灰色の縦の棒と横の棒）。アーチの上にたたんであり、t_drop に上から落ちて門をふさぐ（上を軸に z を伸ばす）"""
    GW, GH = 1.9, 2.4
    top = empty((0, -0.24, GH)); gm = _m("grille", "#8A9099", rough=0.4, metal=0.7)
    for k in range(9):
        cube(gm, (-0.84 + k * 0.21, 0, -GH / 2), (0.05, 0.05, GH), parent=top)
    for zz in (0.25, 0.9, 1.6, 2.25):
        cube(gm, (0, 0, -zz), (GW, 0.05, 0.06), parent=top)
    top.scale = (1, 1, 0.001)
    if t_drop is not None:
        hide_key(top, -100.0, True); hide_key(top, t_drop - 0.02, False)
        key(top, "scale", -100.0, (1, 1, 0.001), "CONSTANT"); key(top, "scale", t_drop, (1, 1, 0.001), "LINEAR"); key(top, "scale", t_drop + d, (1, 1, 1.0))
        key(top, "scale", t_drop + d + 0.06, (1, 1, 0.97)); key(top, "scale", t_drop + d + 0.14, (1, 1, 1.0))   # 落ちて小さくはねる
    return top


def test_board(parent=None, loc=(0, 0, 0), rot=(R(90), 0, 0), w=0.62):
    """絵のテストの板（3×3 のますに、りんご・車・木などの絵。字なし）。面は +z（rot で立てる）"""
    e = empty(loc); e.rotation_euler = rot
    if parent is not None: e.parent = parent
    cube(_m("tbframe", "#2E3440", rough=0.5), (0, 0, -0.006), (w + 0.05, w + 0.05, 0.012), bevel=0.006, parent=e)
    plane(img_mat("testboard", os.path.join(TEX, "test_board.png"), emit=0.35), (0, 0, 0.001), (w, w), parent=e)
    return e


def shop_recolor(awn="#3FA66A", brick=("#F2D9B5", "#E6C99E"), sign="#3F7F4A"):
    """別のお店（C2）：同じ形で、日よけのしまを緑・れんがを明るく・看板の板を緑に（shop() のあとに呼ぶ）"""
    for m_ in bpy.data.materials:
        b_ = m_.node_tree.nodes.get("Principled BSDF") if m_.use_nodes else None
        if b_ is None: continue
        if m_.name.startswith("awn0"): b_.inputs["Base Color"].default_value = srgb(awn)
        elif m_.name.startswith("signbd"): b_.inputs["Base Color"].default_value = srgb(sign)


def settings_phone(loc, face=0.0, h=0.62):
    """S28 の大きな設定のスマホ（まるロボの前に立てる。架空。字なし）：4 つの段（絵は画面の絵）と、段ごとのスイッチ（灰色 → 押すと右へ動いて緑）。
    前＝−y。戻り値：dict(root, sw=[スイッチの動く部分 4 つ], swm=[材質 4 つ], rows=[段の中心 4 つ（札の目じるし）])"""
    w = h * 0.5
    e = empty(loc, R(face))
    cube(mat("sp_body", "#1D2126", rough=0.3, metal=0.4), (0, 0, h / 2 + 0.06), (w, 0.03, h), bevel=0.025, parent=e)
    cube(mat("sp_edge", "#8A9099", rough=0.25, metal=0.9), (0, 0.002, h / 2 + 0.06), (w + 0.01, 0.026, h + 0.01), bevel=0.025, parent=e)
    plane(img_mat("sp_screen", os.path.join(TEX, "set_screen.png"), emit=1.2), (0, -0.0165, h / 2 + 0.06), (w * 0.9, h * 0.92), rot=(R(90), 0, 0), parent=e)
    cube(mat("sp_stand", "#5A6475", rough=0.5), (0, 0.12, 0.03), (w * 0.8, 0.3, 0.06), parent=e)     # 立てる台
    sw, swm, rows = [], [], []
    for k in range(4):
        zc = 0.06 + h * 0.92 * (0.5 - (k + 0.5) / 4) + h / 2      # 画面の段（上から）
        track_x = w * 0.27
        cube(mat("sp_track%d" % k, "#C9CED6", rough=0.4), (track_x, -0.02, zc), (0.085, 0.01, 0.045), bevel=0.02, parent=e)
        m_ = mat("sp_knob%d" % k, "#9AA4B2", rough=0.4, emit=0.0)
        kn = empty((track_x - 0.02, -0.03, zc)); kn.parent = e
        sphere(m_, (0, 0, 0), 0.026, scale=(1, 0.6, 1), parent=kn, seg=16)
        sw.append(kn); swm.append(m_)
        r_ = empty((0.0, -0.03, zc)); r_.parent = e; rows.append(r_)
    return dict(root=e, sw=sw, swm=swm, rows=rows)


def switch_on(sp, k, t, col="#34B266"):
    """設定のスイッチ k を、t に右へ動かして緑にする"""
    kn = sp["sw"][k]; p0 = tuple(kn.location)
    key(kn, "location", t, p0); key(kn, "location", t + 0.18, (p0[0] + 0.04, p0[1], p0[2]))
    lamp_color(sp["swm"][k], t, col, 1.5, 0.18)
