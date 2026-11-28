# 19本目（メッセージの旅）：3D の場面を声の時刻に合わせて動かして描く（17本目の scenes.py と同じ作り方）
# blender -b --factory-startup --python scenes19.py -- <クリップ> <出力フォルダ> [--samples 4] [--res 480 270] [--step 3] [--stills 秒,秒] [--track]
#   舞台：A＝まるロボの部屋（b_room。16・17本目と同じ部屋に、大きなスマホ）／B＝スマホの中（b_inside。基板の町）／C＝町の上の空（b_sky）
#   舞台の組み立て（b_*）は、その舞台の動きを全部作り、カメラだけをクリップごとに選ぶ。絵コンテ表：../絵コンテ_v1.md
#   決まり：3D の中に字を書かない／まるロボは喋らない・本物の体を marumotion の予定で動かす（maru17.py）／動きは言い終えてから
#   この版は冒頭・1章（S01〜S08）。§2.6：章ごとに動く下書きで OK をもらう
import os, sys, math, json, random
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.read_factory_settings(use_empty=True)
TEX = os.environ.get("TEX17") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "tex17")
TEX19 = os.environ.get("TEX19") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "tex19")
exec(open(os.path.join(KIT_HERE, "kit17.py"), encoding="utf-8").read())
_K7 = KIT_HERE
exec(open(os.path.join(KIT_HERE, "..", "..", "ep06_haizen", "anim", "core.py"), encoding="utf-8").read().replace(
    'VO = os.path.join(KIT_HERE, "..", "voice")', 'VO = os.path.join(_K7, "..", "voice")'))
exec(open(os.path.join(KIT_HERE, "timing.py"), encoding="utf-8").read())
CLIPNAME = _argv[0]; OUTDIR = _argv[1] if len(_argv) > 1 else "/tmp/x"
_SRC_DEFAULT = {"step": "maru_c", "jump": "maru_c", "land": "maru_c", "takeoff": "maru_c", "step_turn": "maru_c"}


def ev(t, kind, gain=1.0, src=None):
    EVENTS.append((round(t, 3), kind, gain, src if src is not None else _SRC_DEFAULT.get(kind, "")))


def _opt(name, n=1, default=None):
    if name in _argv:
        i = _argv.index(name); v = _argv[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default


SAMPLES = int(_opt("--samples", 1, 4)); RES = tuple(int(x) for x in _opt("--res", 2, ("480", "270"))); STEP = int(_opt("--step", 1, 3))
STILLS = [float(x) for x in _opt("--stills", 1, "").split(",") if x]
TRACK_ONLY = "--track" in _argv
_M_ = [None]
exec(open(os.path.join(_K7, "maru17.py"), encoding="utf-8").read())


def cam(loc, target, lens=35, t0=None, t1=None, loc1=None, target1=None, lens1=None):
    c, tg = cam_rig(loc, target, lens)
    c.data.dof.use_dof = False; c.data.dof.aperture_fstop = 64.0
    if t0 is not None:
        cam_move(c, tg, t0, t1, loc, loc1 or loc, target, target1 or target, lens, lens1 or lens)
    return c, tg


def C(loc, tgt, lens=35, loc1=None, tgt1=None, lens1=None, d=8.0):
    """決まったカメラ（d 秒かけて loc → loc1 へゆっくり動く）"""
    def mk(t0):
        return cam(loc, tgt, lens, t0, t0 + d, loc1 or loc, tgt1 or tgt, lens1 or lens)
    return mk


def CA(t0_, t1_, loc, tgt, lens, loc1, tgt1, lens1=None):
    """決まった時刻（場面の時刻）に動くカメラ（寄り続ける・追いかける所）"""
    def mk(t0):
        return cam(loc, tgt, lens, t0_, t1_, loc1, tgt1, lens1 or lens)
    return mk


def pop_in(ob, t, s1=1.0, d=0.3):
    key(ob, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(ob, "scale", t, (0.001, 0.001, 0.001)); key(ob, "scale", t + d, (s1, s1, s1))


def pop_out(ob, t, s0=1.0, d=0.25):
    key(ob, "scale", t, (s0, s0, s0)); key(ob, "scale", t + d, (0.001, 0.001, 0.001), "CONSTANT")


def white_in(cam_ob, t, d=0.7):
    """白から溶ける（舞台が替わった所。前の舞台は白い光の中で終わる）：カメラのすぐ前の白い板の透け具合を 1 → 0"""
    m = bpy.data.materials.new("white_in"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); mx = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 1, 1, 1); em.inputs["Strength"].default_value = 1.0
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
    fac = mx.inputs["Fac"]
    for tt, v in ((-100.0, 1.0), (t, 1.0), (t + d, 0.0)):
        fac.default_value = v; fac.keyframe_insert("default_value", frame=f(tt))
    bpy.ops.mesh.primitive_plane_add(size=1.0); p = bpy.context.object; p.data.materials.append(m)
    p.parent = cam_ob; p.location = (0, 0, -0.12); p.scale = (1.0, 1.0, 1.0)
    p.visible_shadow = False
    return p


def screen_mat(name, states, glow=1.0, white_at=None):
    """スマホの画面（12本目の決まり：地の色は黒・つやなし。絵は自分で光るだけ）。states：[(時刻, 絵)]。white_at：(t0, t1) で白く光る"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1); b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.0; b.inputs["Coat Weight"].default_value = 0.0
    imgs = {}
    def tn(path):
        t = nt.nodes.new("ShaderNodeTexImage")
        if path not in imgs: imgs[path] = bpy.data.images.load(path)
        t.image = imgs[path]; return t
    col = tn(states[0][1]).outputs["Color"]
    for (t, path) in states[1:]:
        tx = tn(path); mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
        nt.links.new(col, mx.inputs[6]); nt.links.new(tx.outputs["Color"], mx.inputs[7])
        fi = mx.inputs["Factor"]
        fi.default_value = 0.0; fi.keyframe_insert("default_value", frame=f(t - 0.12))
        fi.default_value = 1.0; fi.keyframe_insert("default_value", frame=f(t))
        col = mx.outputs[2]
    nt.links.new(col, b.inputs["Emission Color"])
    es = b.inputs["Emission Strength"]
    es.default_value = glow; es.keyframe_insert("default_value", frame=f(-100.0))
    if white_at:
        es.keyframe_insert("default_value", frame=f(white_at[0]))
        es.default_value = 40.0; es.keyframe_insert("default_value", frame=f(white_at[1]))
    return m


# ======================================================================== 12本目の空と町（kit12.py から写した）
def sky_day():
    world("#BFD8EE", 1.0)
    bpy.ops.object.light_add(type='SUN', rotation=(R(40), 0, R(35))); s_ = bpy.context.object
    s_.data.energy = 4.0; s_.data.color = srgb("#FFF4E5")[:3]; s_.data.angle = R(4)
    return s_


def town_grid(n=7, block=60.0, seed=5):
    """上から見た町：道の網とブロックの建物。まん中は (0,0)"""
    rnd = random.Random(seed)
    asph = _m("t_asph", "#55595F", rough=0.85); big = _m("t_big", "#4A4E54", rough=0.8)
    grass = noise_mat("t_grass", "#8DB27A", "#7DA06B", 0.2, 0.95)
    half = n * block / 2
    cube(grass, (0, 0, -0.1), (n * block + 400, n * block + 400, 0.1))
    for k in range(n + 1):
        u = -half + k * block; wide = (k % 3 == 0)
        ww = 14.0 if wide else 6.0
        cube(big if wide else asph, (u, 0, 0.02), (ww, n * block, 0.04))
        cube(big if wide else asph, (0, u, 0.02), (n * block, ww, 0.04))
    cols = ["#D9CFC0", "#C9B8A2", "#B8C4CF", "#E3D9CC", "#C2B2A0", "#A9B7C2"]
    BLD = []
    for i in range(n):
        for j in range(n):
            cx = -half + (i + 0.5) * block; cy = -half + (j + 0.5) * block
            for _ in range(rnd.randint(2, 4)):
                bw = rnd.uniform(12, 22); bd = rnd.uniform(12, 22); bh = rnd.uniform(6, 26)
                p = (cx + rnd.uniform(-12, 12), cy + rnd.uniform(-12, 12))
                BLD.append((p, bw, bd, bh))
    return BLD, half, cols, rnd


# ======================================================================== A：まるロボの部屋（冒頭 S01〜S03）
HOUSE_S = 0.40
PHC = (0.6, 0.6, 0.0)                       # 床に寝かせた大きなスマホのまん中（長い向きが y。画面の上＝+y）。試しの絵：x 1.6 ではベッド（x 1.25〜2.9・y −0.35 まで）のすぐ横で、手前のカメラがベッドの中に入った → 左へ
PH_W, PH_L, PH_T = 0.65, 1.30, 0.05         # はば・長さ・厚さ（m）。まるロボ（0.40 倍、高さ約 0.5 m）が画面の上を跳ねられる大きさ
SCR_W, SCR_L = 0.57, 1.22                   # 画面の所
TOP = PH_T                                  # 画面の高さ


def scr(u, v):
    """画面の上の点（絵の 0〜1。左上が 0,0）→ 部屋の座標"""
    return (PHC[0] - SCR_W / 2 + u * SCR_W, PHC[1] + SCR_L / 2 - v * SCR_L, TOP)


SEND = scr(0.86, 0.935); PICK_ST = scr(0.22, 0.70); PICK_PH = scr(0.50, 0.62); MID = scr(0.55, 0.42)
START = (-0.08, 0.6, 0.0)


def town_view19(x1=3.0):
    """窓の外：遠くの町の建物（17本目の town_view17 から、塔を外した）。友だちの町は山の向こう（02-03）"""
    random.seed(7)
    for k in range(7):
        y = -3.2 + k * 1.05; h = random.uniform(2.6, 3.8)
        o = cube(mat("townb%d" % k, random.choice(["#B9C3CF", "#C7CED8", "#AEB9C6"]), rough=0.8), (x1 + 6.4, y, h / 2 - 0.3), (0.4, 0.9, h)); o.visible_shadow = False
    bpy.ops.mesh.primitive_uv_sphere_add(radius=6.0, location=(x1 + 14.0, -0.5, -2.0), segments=24, ring_count=12)
    hl = bpy.context.object; hl.scale = (0.6, 2.0, 1.0); hl.data.materials.append(mat("hill19", "#7FA474", rough=0.9)); hl.visible_shadow = False


PKO = []


def big_phone(states, white_at=None):
    e_ = empty(PHC, 0.0)
    cube(mat("bph_body", "#1D2126", rough=0.35, metal=0.4), (0, 0, PH_T / 2), (PH_W, PH_L, PH_T), bevel=0.03, parent=e_)
    cube(mat("bph_edge", "#8A9099", rough=0.25, metal=0.9), (0, 0, PH_T / 2), (PH_W + 0.006, PH_L + 0.006, PH_T * 0.7), bevel=0.03, parent=e_)
    m = screen_mat("bph_scr", states, glow=1.0, white_at=white_at)
    sc_ = plane(m, (0, 0, PH_T + 0.0015), (SCR_W, SCR_L), parent=e_)
    return e_, sc_


def b_room(cl):
    """S01〜S03：朝の部屋。スタンプと写真を送る → 一瞬で既読 → 問い → 題 → 時計 → もう一度送信 → 小さくなって画面の中へ"""
    room(window=True); door17(); town_view19()
    hat_rack((0.12, 1.32, 0.0)); trash_can((1.95, 1.45, 0.0))
    t_st = wp("01-02", "ネジ") - 0.1; t_ph = wp("01-03", "写真") - 0.1
    t_send = wp("01-04", "えいっ") + 0.15; t_out = s("01-05") + 0.05; t_read = wp("01-06", "印") - 0.15
    states = [(0.0, os.path.join(TEX19, "ph_home.png")), (t_st, os.path.join(TEX19, "ph_stamp.png")), (t_ph, os.path.join(TEX19, "ph_photo.png")),
              (t_out, os.path.join(TEX19, "ph_sent.png")), (t_read, os.path.join(TEX19, "ph_read.png")),
              (wp("03-06", "えいっ") + 0.1, os.path.join(TEX19, "ph_stamp.png"))]
    t_dive0 = s("03-07") + 0.2; t_dive1 = e("03-07") + 0.6
    ph, sc_ = big_phone(states, white_at=(t_dive1 - 0.9, t_dive1))
    track("phone", ph, 0.05); track("send", empty(SEND), 0.0)
    ev(t_out, "slip", 0.35, "phone"); ev(t_read, "tap", 0.3, "phone")
    M = MaruR(START, face=90.0, s=HOUSE_S); track("maru", M.body, 0.25); track("maru_top", M.body, 0.32)
    # 01：窓の外を見る → ぴょん（画面に跳び乗る）→ 写真の所へ → ぴょん、ぴょん → えいっ（送信）
    M.at(s("01-01") + 0.5, look=8)
    M.at(e("01-01") - 0.2, look=0)
    M.jump(t_st, MID)
    M.hopto(t_ph + 0.05, PICK_PH)
    p1 = wp("01-04", "ぴょん", 0) + 0.25; p2 = wp("01-04", "ぴょん", 1) + 0.25
    M.path([scr(0.70, 0.78), scr(0.80, 0.88)], [p1, p2])
    for pp_ in (p1, p2): ev(pp_ - 0.3, "jump", 0.25, "maru_c")          # 声がまねする「ぴょん」：言葉の時刻に跳ぶ音（跳ぶ道は音なしの作りなので足す）
    M.hopto(t_send - 0.05, SEND)
    ev(t_send - 0.03, "tap", 0.4, "send")
    # 向きは窓の方（+x）のまま（カメラの方へ 90 度向き直ると 1.9 秒おくれた）。顔を写すカメラは窓の側に置く
    M.confused(t_read + 0.4)
    # 02：まばたき → 窓へ向く → 首をかしげる → スマホを見下ろす
    M.blink(wp("02-02", "まばたき") + 0.1)
    M.confused(s("02-04") + 0.6)
    M.at(s("02-08") + 0.2, look=-22)
    M.at(e("02-09") + 0.2, look=0)
    # 03：顔を上げる → 気合い → もう一度送信（えいっ）→ 小さくなる
    M.wobble(s("03-02") + 0.6, s("03-02") + 1.6, deg=8, period=0.25)
    t_e2 = wp("03-06", "えいっ")
    M.hop(t_e2 - 0.15); ev(t_e2 + 0.15, "tap", 0.4, "send")
    MARU_SHRINK[:] = [(t_dive0, t_dive0 + 1.2)]
    ev(t_dive0, "shimmer", 0.35, "maru_c")
    return M


MARU_SHRINK = []


def shrink_after_bake(M):
    """（03-07）体のまん中を中心に小さくする（SKILL：root は足もとなので、delta_location で持ち上げる）"""
    if not MARU_SHRINK: return
    par = M.h.parent; t0, t1 = MARU_SHRINK[0]
    c = 0.30 * M.s
    # 通しの点検（v1h）：親の原点（はじめの立ち位置）を中心に小さくしていたので、まるロボが送信のボタンから原点の方へ飛んでいった
    #   （うしろからのカメラでは見えなかった）→ 小さくなりはじめのまるロボの足もと（xy）を中心にする
    sc = bpy.context.scene; sc.frame_set(int(round(f(t0)))); bpy.context.view_layer.update()
    P = M.body.matrix_world.translation.copy(); O = par.matrix_world.translation.copy()
    for k in range(9):      # 試しの絵：1.0 から打っていて、はじめからずっと 1.0 倍（大きなまるロボ）になっていた → いまの大きさ（M.s）にかける
        u = k / 8; sc_ = 1.0 - 0.9 * (u * u * (3 - 2 * u))
        key(par, "scale", t0 + (t1 - t0) * u, (M.s * sc_,) * 3)
        key(par, "delta_location", t0 + (t1 - t0) * u, ((P.x - O.x) * (1 - sc_), (P.y - O.y) * (1 - sc_), c * (1 - sc_)))


# ======================================================================== B：スマホの中（1章 S04〜S08 の前半）
BS = 1.0
B_MARU = (0.0, -0.6, 0.0)
PLATE = (0.0, 1.6, 1.25)        # 宙のスタンプの板（まん中）
DOTS_Y, DOTS_Z = 1.6, 1.25
PK = (0.0, 1.6, 0.0)            # 包み（下のまん中）
PK_S = 1.0       # 試しの絵：0.6 ではまるロボ（1.0 倍）より小さく、「しがみつく」に見えなかった
TOPZ = PK_S * 0.92 + 0.065   # 包みの上の面（ふたの上）。点検（hitcheck）：0.92 に立たせると、足がふたに 6 cm めりこんでいた


def pcb_floor():
    m = bpy.data.materials.new("pcb"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(TEX19, "pcb.png"))
    mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord"); mp.inputs["Scale"].default_value = (6, 6, 1)
    nt.links.new(tc.outputs["UV"], mp.inputs[0]); nt.links.new(mp.outputs[0], t.inputs[0]); nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55; b.inputs["Metallic"].default_value = 0.1
    plane(m, (0, 6, 0), (60, 60))


def chip(loc, w, d, h, pins=True, col="#15171B"):
    e_ = empty(loc)
    cube(mat("chip", col, rough=0.5), (0, 0, h / 2), (w, d, h), bevel=0.04, parent=e_)
    cube(mat("chip_top", "#23262C", rough=0.4), (0, 0, h + 0.005), (w * 0.8, d * 0.8, 0.01), parent=e_)
    if pins:
        pm = mat("pin", "#C9CED6", rough=0.25, metal=0.9)
        n = max(3, int(w / 0.35))
        for k in range(n):
            x = -w / 2 + (k + 0.5) * w / n
            for sy in (-1, 1): cube(pm, (x, sy * (d / 2 + 0.08), 0.05), (0.08, 0.18, 0.06), parent=e_)
    return e_


def cap(loc, r, h, col="#2E5FA8"):
    cyl(mat("cap" + col, col, rough=0.35, metal=0.3), (loc[0], loc[1], h / 2), r, h, verts=24)
    cyl(mat("cap_top", "#C9CED6", rough=0.3, metal=0.8), (loc[0], loc[1], h + 0.01), r * 0.92, 0.02, verts=24)


def tex_plane(name, path, loc, size, rot=(R(90), 0, 0)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Emission Strength"].default_value = 0.6; b.inputs["Roughness"].default_value = 0.6
    m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot); p = bpy.context.object; p.scale = (size, size, 1); p.data.materials.append(m)
    p.name = name
    return p, b


def packet(loc):
    """包み：青緑の箱（ふたは上・横の面に白い札 3 枚。字なし）"""
    e_ = empty(loc)
    pm = mat("pk_body", "#2FC9B8", rough=0.35)
    cube(pm, (0, 0, PK_S / 2), (PK_S, PK_S, PK_S * 0.92), bevel=0.03, parent=e_)
    lid_h = empty((0, PK_S / 2, PK_S * 0.92)); lid_h.parent = e_
    cube(mat("pk_lid", "#26B3A3", rough=0.35), (0, -PK_S / 2, 0.03), (PK_S + 0.03, PK_S + 0.03, 0.06), bevel=0.02, parent=lid_h)
    tags = []
    for k in range(3):
        tm = glow_mat("tag%d" % k, "#FFFFFF", 0.0)
        tg = cube(tm, ((-0.3 + k * 0.3) * PK_S, -PK_S / 2 - 0.006, PK_S * 0.5), (0.22 * PK_S, 0.012, 0.28 * PK_S), bevel=0.01, parent=e_)
        tags.append((tg, tm))
    return e_, lid_h, tags


def b_inside(cl):
    """S04〜S08 前半：スマホの中。スタンプ → 光る粒の列 → 包み → 札 3 枚 → しがみつく → 浮いて、光る出口へ"""
    world("#1B3346", 1.0)                                                # 試しの絵：真っ黒の空でさびしかった → こい紺
    bpy.ops.object.light_add(type='SUN', rotation=(R(35), 0, R(30))); sn = bpy.context.object; sn.data.energy = 2.2; sn.data.color = (0.85, 0.95, 1.0)
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 6)); ar = bpy.context.object; ar.data.energy = 900; ar.data.size = 10
    pcb_floor()
    random.seed(4)
    chip((0.0, 7.5, 0), 4.2, 3.0, 1.6)                                # 計算する部品（まん中の大きなチップ）
    track("cpu", empty((0.0, 7.5, 1.6)), 0.0)
    for (x, y, w_, d_, h_) in ((-5.5, 4.0, 2.4, 2.0, 1.1), (5.2, 4.5, 2.0, 2.6, 0.9), (-4.0, 10.5, 3.0, 2.0, 1.3), (5.5, 10.0, 2.4, 2.4, 1.5),
                               (-7.5, 0.5, 1.6, 1.6, 0.8), (7.2, 0.0, 1.8, 1.4, 0.7), (-2.6, 13.0, 2.0, 1.6, 1.0), (2.8, 13.5, 2.2, 1.8, 1.2)):
        chip((x, y, 0), w_, d_, h_)
    for (x, y, r, h, c) in ((-2.8, 3.2, 0.35, 1.1, "#2E5FA8"), (2.9, 2.8, 0.3, 0.9, "#8A4FC0"), (-6.5, 7.5, 0.4, 1.3, "#2E5FA8"), (6.8, 7.2, 0.35, 1.0, "#C08A2E"),
                            (-1.2, 10.5, 0.25, 0.8, "#2E5FA8"), (1.6, 10.8, 0.3, 0.9, "#8A4FC0")):
        cap((x, y), r, h, c)
    # 金色の太い線（基板の道）を少し浮かせて、ゆっくり光を流す
    # 宙のスタンプの板 → 光る粒の列（04-02）
    pl, pb = tex_plane("stamp", os.path.join(TEX19, "stamp_screw.png"), PLATE, 1.3)
    t_un0 = wp("04-02", "ネジ") + 0.4; t_un1 = t_un0 + 2.2
    sc0 = pl.scale.copy()
    key(pl, "scale", t_un0, tuple(sc0)); key(pl, "scale", t_un1, (0.001, sc0[1], 1.0))
    key(pl, "location", t_un0, PLATE); key(pl, "location", t_un1, (PLATE[0] + 0.65, PLATE[1], PLATE[2]))
    ev(t_un0, "shimmer", 0.3, "plate"); track("plate", pl, 0.0)
    N = 36; L0 = -2.6; L1 = 2.6
    dots = []
    hi = glow_mat("dot_hi", "#BFF8FF", 6.0); lo = glow_mat("dot_lo", "#2A6F78", 1.2)
    for k in range(N):
        x = L0 + (L1 - L0) * k / (N - 1)
        d_ = sphere(hi if random.random() < 0.5 else lo, (x, DOTS_Y, DOTS_Z), 0.055, seg=12)
        t_ = t_un0 + (t_un1 - t_un0) * (k / (N - 1)) * 0.95
        pop_in(d_, t_, 1.0, 0.2)
        dots.append(d_)
    track("dots", dots[N // 2], 0.0); track("dots_l", dots[0], 0.0); track("dots_r", dots[-1], 0.0)
    # 包み（05-02）：下からせり上がり → 粒が中へ流れこむ → ふたが閉まる
    ZH = -2.3                                                          # 床の下にかくしておく（試しの絵：開いたふたが床から突き出ていた）
    pk, lid, tags = packet((PK[0], PK[1], ZH)); PKO.append(pk)
    track("packet", pk, PK_S * 0.5); track("tags", tags[1][0], 0.0)
    for k_, (tg, tm) in enumerate(tags): track("tag%d" % k_, tg, 0.0)
    t_up = s("05-02") + 0.1
    key(pk, "location", -100.0, (PK[0], PK[1], ZH), "CONSTANT"); key(pk, "location", t_up - 0.6, (PK[0], PK[1], ZH)); key(pk, "location", t_up + 0.7, PK)
    key(lid, "rotation_euler", -100.0, (R(-110), 0, 0), "CONSTANT"); key(lid, "rotation_euler", t_up + 0.7, (R(-110), 0, 0))
    t_in0 = t_up + 0.8; t_in1 = t_in0 + 1.2
    for k, d_ in enumerate(dots):
        p0 = d_.location.copy(); tk = t_in0 + (t_in1 - t_in0) * (abs(k - N / 2) / (N / 2))
        # 包みの中では、下の方に短い列で並ぶ（07-04「すっぽり入りました」：箱の半分にも足りないのが、透かしたときに見えるように。通しの点検：1 か所に固まって見えなかった）
        key(d_, "location", tk - 0.35, tuple(p0)); key(d_, "location", tk, (PK[0] - 0.3 + 0.6 * k / (N - 1), PK[1] - 0.15, 0.2))
        key(d_, "scale", tk - 0.05, (1, 1, 1)); key(d_, "scale", tk, (0.55, 0.55, 0.55))
    ev(t_in0, "shimmer", 0.25, "packet")
    t_lid = t_in1 + 0.15
    key(lid, "rotation_euler", t_lid, (R(-110), 0, 0)); key(lid, "rotation_euler", t_lid + 0.35, (0, 0, 0))
    ev(t_lid + 0.33, "door_shut", 0.3, "packet")
    # 07-01：中を少し透かす（粒が見える）→ 07-04 のあと戻す
    body = [c for c in pk.children if c.type == 'MESH'][0]
    bm = body.active_material
    try:
        bm.blend_method = "BLEND"
    except Exception:
        pass
    al = bm.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    for tt, v in ((-100.0, 1.0), (s("07-01") + 0.2, 1.0), (s("07-01") + 0.8, 0.35), (e("07-04"), 0.35), (e("07-04") + 0.5, 1.0)):
        al.default_value = v; al.keyframe_insert("default_value", frame=f(tt))
    # 札が 1 枚ずつ光る（06-02・06-06・06-09。06-11 で 3 枚目がもう一度）
    for k_, (lid_, wd) in enumerate((("06-02", "あて先"), ("06-06", "送り主"), ("06-09", "番号"))):
        tg, tm = tags[k_]; tt = wp(lid_, wd) - 0.05
        emit_key(tm, tt - 0.01, 0.0); emit_key(tm, tt + 0.2, 4.0); emit_key(tm, tt + (1.6 if k_ == 2 else 1.0), 1.2)
        ev(tt, "pi", 0.3, "tag%d" % k_)
    tm3 = tags[2][1]; t11 = s("06-11") + 0.3
    emit_key(tm3, t11, 1.2); emit_key(tm3, t11 + 0.3, 4.0); emit_key(tm3, t11 + 1.2, 1.2)
    for tg, tm in tags: emit_key(tm, e("06-12"), 1.2); emit_key(tm, e("06-12") + 0.4, 0.6)
    # まるロボ（1.0 倍）
    M = MaruR(B_MARU, face=180.0, s=BS); track("maru", M.body, 0.5); track("maru_top", M.body, 0.75)
    M.at(s("04-01") + 0.2, look=14)
    M.at(e("04-01"), look=0)
    M.confused(s("04-03") + 0.3)
    M.at(s("04-04") + 0.2, look=10); M.at(e("04-05"), look=0)
    M.nod(s("04-12") + 0.4)
    SIDE = (1.25, 0.6, 0.0)                                            # 包みの斜め前（札を写すカメラとの間に立たない。試しの絵：前に立つと札が体で隠れた）
    M.walk(s("05-02") - 0.2, e("05-02") + 0.1, SIDE)
    M.push(s("05-03") + 0.2, 0.25); ev(s("05-03") + 0.45, "tap", 0.3, "packet")
    # 05-05：包みのまわりを回る（右から後ろ、左、前へもどる）
    t5 = s("05-05")
    M.walk(t5 + 0.1, t5 + 1.8, (1.25, 2.3, 0.0))
    M.walk(t5 + 1.9, e("05-06") - 0.3, SIDE)
    M.at(s("06-02"), face=-128.0)                                        # 包みの方を向く
    M.confused(s("06-10") + 0.3)
    # 07-05：跳び乗って、しがみつく
    t_on = wp("07-05", "ぎゅっ") - 0.1
    M.jump(t_on, (PK[0], PK[1], TOPZ))
    M.lean(t_on + 0.3, t_on + 0.8, 14.0, hold=20.0)
    # 08-01〜08-02：包みが浮いて、光る出口（上）へ。まるロボも一緒に運ばれる
    t_f0 = s("08-01") + 0.2; t_f1 = s("08-02") + 0.4; t_ex = e("08-02") + 0.4
    EXIT = (0.0, 9.0, 14.0)
    def pth(t):
        if t <= t_f0: return (0.0, 0.0, 0.0)
        if t <= t_f1:
            u = (t - t_f0) / (t_f1 - t_f0); u = u * u * (3 - 2 * u); return (0.0, 0.0, 0.9 * u)
        u = min(1.0, (t - t_f1) / (t_ex - t_f1)); u = u * u
        return (EXIT[0] * u, (EXIT[1] - PK[1]) * u, 0.9 + (EXIT[2] - 0.9) * u)
    n_ = int((t_ex + 1.0 - t_f0) * FPS)
    for k in range(n_ + 1):
        tt = t_f0 + k / FPS; o = pth(tt)
        key(pk, "location", tt, (PK[0] + o[0], PK[1] + o[1], PK[2] + o[2]), "LINEAR")
    M.carry(t_f0, t_ex + 1.0, pth)
    ev(t_f0, "float", 0.35, "packet")
    ex_ = cyl(glow_mat("exit", "#EAFBFF", 30.0), EXIT, 2.2, 0.05, verts=48); track("exit", ex_, 0.0)
    ev(t_f1, "zoom", 0.35, "packet")
    return M


# ======================================================================== C：町の上の空（08-02 の後半〜08-10）
ANT = (150.0, 60.0, 0.0)        # アンテナの立つビル（屋上の高さ ANT_H）
ANT_H = 30.0
HOME_W = (0.0, -1.2, 5.0)        # まるロボの家の窓の前（包みが出てくる所）。試しの絵：y 0 では家のかべに半分めりこんだ
PAD = (ANT[0] - 3.0, ANT[1], ANT_H + 0.35)    # アンテナの台（包みが着く所）


def b_sky(cl):
    sky_day()
    BLD, half, cols, rnd = town_grid(7, 60.0, seed=19)
    for (p, bw, bd, bh) in BLD:
        if math.hypot(p[0] - ANT[0], p[1] - ANT[1]) < 25 or math.hypot(p[0], p[1]) < 20: continue
        if abs(p[1] * ANT[0] - p[0] * ANT[1]) / math.hypot(*ANT[:2]) < 14 and 0 < p[0] < ANT[0]: bh = min(bh, 14.0)   # 飛ぶ道の下の建物は低く（通りぬけない）
        cube(_m("tb%d" % rnd.randint(0, 5), rnd.choice(cols), rough=0.85), (p[0], p[1], bh / 2), (bw, bd, bh))
    # まるロボの家（窓のある小さな家）
    cube(_m("home", "#F2D9B5", rough=0.8), (0, 3.0, 3.5), (8, 6, 7))
    cube(_m("home_roof", "#B8574A", rough=0.7), (0, 3.0, 7.4), (8.6, 6.6, 0.8))
    cube(glow_mat("home_win", "#FFF2D0", 1.5), (0, -0.02, 4.8), (1.6, 0.05, 1.3))
    # アンテナのビルと、屋上のアンテナ（柱・3 枚の板・台）
    cube(_m("ant_bld", "#B8C4CF", rough=0.8), (ANT[0], ANT[1], ANT_H / 2), (16, 16, ANT_H))
    pm = mat("ant_pole", "#D5D9DE", rough=0.4, metal=0.6)
    cyl(pm, (ANT[0], ANT[1], ANT_H + 6.0), 0.35, 12.0, verts=16)
    for k in range(3):
        a = R(120 * k + 30)
        pn = cube(mat("ant_panel", "#EEF1F4", rough=0.5), (ANT[0] + 0.9 * math.cos(a), ANT[1] + 0.9 * math.sin(a), ANT_H + 10.0), (0.35, 1.0, 3.0))
        pn.rotation_euler = (0, 0, a)
    cube(mat("ant_pad", "#8C939C", rough=0.6, metal=0.5), (PAD[0], PAD[1], ANT_H + 0.15), (4.0, 4.0, 0.3))
    track("antenna", empty((ANT[0], ANT[1], ANT_H + 8.0)), 0.0); track("pad", empty(PAD), 0.0)
    # 包み（まるロボが乗っている）と電波の輪
    pk, lid, tags = packet(HOME_W); PKO.append(pk)
    track("packet", pk, PK_S * 0.5)
    t0 = s("08-02") + 0.3; t1 = wp("08-06", "着いて") - 0.1
    P0 = Vector(HOME_W); P1 = Vector(PAD)
    def pos(t):
        u = max(0.0, min(1.0, (t - t0) / (t1 - t0))); us = u * u * (3 - 2 * u)
        # 通しの点検（v1b）：出てすぐ家の方（+y）へ進みながら上がり、家のかべを突き抜けた → 先に屋根より上へ上がってから進む
        sm = lambda x: (lambda c: c * c * (3 - 2 * c))(max(0.0, min(1.0, x)))
        uy = sm((u - 0.04) / 0.96)
        p = P0.lerp(P1, uy); p.z = P0.z + (P1.z - P0.z) * uy + 22.0 * math.sin(math.pi * us)
        p.z += 4.0 * sm(u / 0.06) * (1.0 - sm((u - 0.85) / 0.15))
        return p
    n_ = int((t1 + 0.5 - (t0 - 1.0)) * FPS)
    for k in range(n_ + 1):
        tt = t0 - 1.0 + k / FPS; p = pos(tt)
        key(pk, "location", tt, tuple(p), "LINEAR")
    ev(t1, "thud", 0.4, "packet")
    # 輪（電波）：包みのまわりに、うすい水色の輪が次々に広がって消える
    rm = glow_mat("wave", "#9FE6FF", 2.0)
    try:
        rm.blend_method = "BLEND"
    except Exception:
        pass
    for k in range(int((t1 - t0) / 0.45)):
        tk = t0 + k * 0.45
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.04, location=tuple(pos(tk)))
        rg = bpy.context.object; rg.data.materials.append(rm); rg.rotation_euler = (R(90), 0, math.atan2(P1.y - P0.y, P1.x - P0.x) + R(90))
        hide_key(rg, tk - 0.01, True); hide_key(rg, tk, False); key(rg, "scale", tk, (0.6, 0.6, 0.6)); key(rg, "scale", tk + 0.9, (2.0, 2.0, 2.0)); hide_key(rg, tk + 0.9, True)   # 通しの点検：3 倍ではカメラの前を大きな白い弧が横切った → 2 倍
    ev(t0, "float", 0.4, "packet")
    # まるロボ：包みの上に乗ったまま運ばれる → 着いたら、ころんと転がって台に落ちる → 起きて、柱の下を見る
    M = MaruR((HOME_W[0], HOME_W[1], HOME_W[2] + TOPZ + 0.025),          # 点検（hitcheck）：08-05 の驚くしゃがみで体の下がふたに 2 cm 入った → 2.5 cm 上げる（遠くからの絵なので浮きは見えない）
              face=-90.0 + math.degrees(math.atan2(P1.y - P0.y, P1.x - P0.x)) + 90.0, s=BS)
    track("maru", M.body, 0.5); track("maru_top", M.body, 0.75)
    M.lean(t0 - 0.5, t0 - 0.2, 8.0, hold=3.0)                            # 点検（hitcheck）：14° では、飛んでいる途中に足先がふたに入った
    def off(t): p = pos(t); return (p.x - HOME_W[0], p.y - HOME_W[1], p.z - HOME_W[2])
    M.carry(t0, t1 + 0.05, off)
    M.at(s("08-03") + 0.2, look=6); M.at(s("08-04"), look=0)
    M.surprise(wp("08-05", "あれ") + 0.1)
    t_k = wp("08-09", "ころん") - 0.35
    M.jump(s("08-09") + 0.7, (PAD[0] - 1.3, PAD[1] - 0.4, ANT_H + 0.3))      # 包みから跳び降りて、少し立ちつくす（拍子ぬけ）
    # 「ころん」：横へ転がって寝ころぶ（部品一覧の roll_over。約 1.3 秒）→ 起き上がる（約 1.4 秒）。
    #   ひっくり返る（flip）は、床の高さを 0 として作られていて、屋上（30 m）では体が画面の外へ出た（試しの絵で見つけた）
    # 通しの点検（v1b・高さを測る道具）：roll_over は 0.35 秒で 80° 倒れて 16° 行き過ぎるので、アンテナの先が 0.2 秒、台に 30 cm 入った
    #   → ここは「傾く」（tilt）で 0.45 秒かけて 72° まで倒す（行き過ぎない）。音は前と同じ
    M.tilt(t_k + 0.05, 72.0, d=0.45); ev(t_k + 0.35, "roll", 0.4, "maru_c")
    M.act(t_k + 1.5, "get_up")
    M.at(t_k + 3.0, look=-20)                                             # 向き直らずに、下（柱の根元）を見る（90 度向き直ると 2.4 秒おくれた）
    M.confused(e("08-10") - 1.0)
    return M


# ======================================================================== クリップ（カメラ）
CUTS = [
    # 冒頭（A まるロボの部屋）。スマホは (0.6, 0.6)。まるロボは画面の上で窓（+x）を向く。顔を写すカメラは +x の側。ベッド（x 1.25〜・y −0.35 まで）の上にカメラを置かない
    ("A01", b_room, s("01-01") - 0.5, C((-0.8, -1.4, 1.4), (0.8, 0.6, 0.2), 24, (-0.7, -1.3, 1.35)), "A"),
    ("A01b", b_room, s("01-02"), C((-0.45, -0.6, 1.05), (0.55, 0.6, 0.12), 28), "A"),
    ("A01c", b_room, s("01-03"), C((0.6, -0.45, 1.35), (0.6, 0.45, 0.0), 28), "A"),
    ("A01d", b_room, s("01-04"), C((1.85, 0.15, 0.78), (0.62, 0.3, 0.12), 28), "A"),   # 通しの点検（v1g）：背中ばかりで顔が見えなかった（絵コンテ「顔が見える」）→ 窓の側から
    ("A01d2", b_room, s("01-05"), C((1.8, 0.4, 1.15), (0.72, 0.45, 0.05), 26), "A"),   # 通しの点検（v1g）：体で画面がかくれ、送った絵が見えなかった → 窓の側の上から、画面のやりとりと顔を一緒に
    ("A01e", b_room, s("01-06"), C((1.75, 0.0, 0.45), (0.8, 0.07, 0.22), 28), "A"),
    ("A02", b_room, s("02-01"), C((-0.8, -1.4, 1.4), (0.8, 0.6, 0.2), 24), "A"),
    ("A02b", b_room, s("02-02"), C((1.75, 0.1, 0.33), (0.8, 0.07, 0.25), 48), "A"),
    ("A02c", b_room, s("02-03"), C((0.0, -0.25, 0.62), (3.0, -0.3, 1.25), 26), "A"),
    ("A02d", b_room, s("02-04"), C((1.8, 0.4, 0.7), (0.8, 0.1, 0.25), 30), "A"),
    ("A02e", b_room, s("02-05"), C((-0.8, -1.4, 1.4), (0.8, 0.6, 0.2), 24, (-0.65, -1.25, 1.3)), "A"),
    ("A02e2", b_room, s("02-06"), C((-0.1, -0.75, 0.75), (0.8, 0.2, 0.2), 28), "A"),
    ("A02e3", b_room, s("02-07"), C((1.2, -0.8, 0.95), (0.7, 0.35, 0.15), 26), "A"),
    ("A02f", b_room, s("02-08"), C((0.15, -0.7, 0.95), (0.8, 0.1, 0.1), 30), "A"),
    ("A02g", b_room, s("02-09"), C((0.0, -0.45, 0.9), (0.0, 0.65, 0.0), 30, (0.0, -0.1, 0.35), (0.0, 0.75, 0.0)), "A"),
    ("A03", b_room, s("03-01"), C((1.78, 0.05, 0.38), (0.8, 0.07, 0.25), 29), "A"),
    ("A03b", b_room, s("03-03"), C((-0.8, -1.4, 1.4), (0.8, 0.6, 0.2), 24), "A"),
    ("A03b2", b_room, s("03-04"), C((1.2, -0.9, 0.9), (0.75, 0.25, 0.2), 28), "A"),
    ("A03b3", b_room, s("03-05"), C((0.0, -1.05, 0.55), (0.8, 0.1, 0.25), 30, (0.15, -0.95, 0.55)), "A"),
    ("A03c", b_room, s("03-06"), None, "A"),
    # 1章（B スマホの中）
    ("B04", None, s("04-01") - 0.6, C((1.6, -3.4, 0.7), (0.0, 6.0, 2.2), 22, (1.5, -3.0, 0.8)), "B"),   # 通しの点検：スタンプの板がまるロボの頭のすぐ上に重なり、帽子に見えた → 横へ
    ("B04b", None, s("04-02"), C((3.2, -0.6, 1.5), (0.0, 1.4, 1.1), 26), "B"),
    ("B04c", None, s("04-03"), C((1.3, 0.6, 1.0), (0.0, -0.6, 0.7), 30), "B"),
    ("B04d", None, s("04-04"), C((-2.6, 1.6, 3.0), (0.0, 7.5, 0.8), 26, (-2.3, 2.0, 3.0)), "B"),
    ("B04e", None, s("04-05"), C((-1.6, -1.0, 1.5), (0.0, 1.6, 1.2), 28), "B"),
    ("B04e2", None, s("04-06"), C((-4.6, 3.0, 2.0), (0.0, 7.5, 1.0), 26), "B"),
    ("B04e3", None, s("04-07"), C((1.6, 0.9, 1.2), (0.0, -0.4, 0.8), 28), "B"),
    ("B04e4", None, s("04-08"), C((0.0, -3.0, 6.5), (0.0, 4.0, 0.0), 24, (0.6, -2.6, 6.2)), "B"),
    ("B04e5", None, s("04-09"), C((-2.2, 0.4, 1.6), (0.0, 1.6, 1.25), 30), "B"),
    ("B04f", None, s("04-10"), C((-3.2, -3.2, 1.7), (-1.0, 1.6, 1.25), 30, (2.8, -3.2, 1.7), (1.2, 1.6, 1.25), d=6.0), "B"),   # 点検（camdist）：y −1.2 ではまるロボのすぐ横（0.88 m）を通った
    ("B04f2", None, s("04-11"), C((0.0, -2.8, 2.6), (0.0, 1.6, 1.0), 26), "B"),
    ("B04g", None, s("04-12"), C((-1.3, 0.6, 1.0), (0.0, -0.6, 0.7), 30), "B"),
    ("B05", None, s("05-01"), C((2.6, -1.6, 1.3), (0.0, 1.2, 1.0), 26), "B"),
    ("B05a", None, s("05-02"), C((-1.6, -0.6, 1.3), (0.0, 1.6, 0.8), 28), "B"),
    ("B05b", None, s("05-03"), C((-1.2, -0.9, 1.2), (0.6, 1.0, 0.55), 28), "B"),   # 試しの絵：横からでは、まるロボの体が画面をふさいだ → 左前から
    ("B05c", None, s("05-05"), C((2.8, -2.8, 2.6), (0.5, 1.5, 0.4), 26), "B"),
    ("B05d", None, s("05-06"), C((-0.35, -0.6, 0.7), (0.0, 1.1, 0.5), 30), "B"),
    ("B05e", None, s("06-01"), C((-0.9, -0.4, 0.9), (0.0, 1.1, 0.5), 30), "B"),
    ("B05f", None, s("06-02"), C((-0.6, 0.0, 0.6), (-0.3, 1.1, 0.5), 36), "B"),
    ("B05f2", None, s("06-03"), C((-1.9, -1.6, 1.7), (0.5, 1.1, 0.5), 26), "B"),
    ("B05g", None, s("06-04"), C((-2.0, 0.0, 1.6), (0.3, 1.3, 0.5), 28), "B"),
    ("B05h", None, s("06-05"), C((-2.6, -2.2, 2.6), (0.0, 1.4, 0.5), 24), "B"),
    ("B06", None, s("06-06"), C((0.0, -0.1, 0.6), (0.0, 1.1, 0.5), 36), "B"),
    ("B06a", None, s("06-07"), C((-0.8, -1.5, 1.3), (0.6, 1.0, 0.5), 28), "B"),
    ("B06a2", None, s("06-08"), C((-2.2, -1.9, 1.6), (0.0, 1.4, 0.5), 26), "B"),
    ("B06a3", None, s("06-09"), C((0.45, -0.1, 0.6), (0.3, 1.1, 0.5), 36), "B"),
    ("B06b", None, s("06-10"), C((1.25, 2.1, 1.0), (1.25, 0.6, 0.7), 30), "B"),   # 包みの右うしろから、まるロボの顔
    ("B06c", None, s("06-11"), C((0.45, -0.1, 0.6), (0.3, 1.1, 0.5), 42), "B"),
    ("B06d", None, s("06-12"), C((2.4, -1.9, 1.6), (0.2, 1.4, 0.5), 26), "B"),
    ("B07", None, s("07-01"), C((-1.4, -0.6, 1.6), (0.0, 1.6, 0.5), 30), "B"),
    ("B07a", None, s("07-02"), C((-1.8, 0.4, 2.2), (0.0, 1.6, 0.5), 28), "B"),
    ("B07a2", None, s("07-03"), C((-1.9, 0.0, 1.2), (0.6, 1.05, 0.62), 28), "B"),   # 通しの点検（v1d）：体が画面の半分をふさぎ、顔が端で切れた → 前から、包みと顔を一緒に
    ("B07a3", None, s("07-04"), C((-1.3, -0.5, 0.75), (0.0, 1.5, 0.3), 30), "B"),   # 通しの点検：上からでは中の粒が見えなかった → 横から
    ("B07b", None, s("07-05"), C((-3.4, -1.4, 2.2), (0.1, 1.5, 1.4), 26), "B"),   # 通しの点検：乗ったあと頭が画面の上で切れた → 上へ向ける
    ("B08", None, s("08-01"), None, "B"),
    # 1章（C 空）
    ("C08", None, s("08-02") + 0.4, None, "C"),
    ("C08a", None, s("08-03"), None, "C"),
    ("C08b", None, s("08-04"), None, "C"),
    ("C08c", None, s("08-05"), C((PAD[0] - 24.0, PAD[1] - 10.0, ANT_H + 9.0), (ANT[0], ANT[1], ANT_H + 4.0), 30), "C"),
    ("C08d", None, s("08-06"), C((PAD[0] - 9.0, PAD[1] - 9.0, ANT_H + 5.0), (PAD[0], PAD[1], ANT_H + 1.2), 28), "C"),
    ("C08e", None, s("08-07"), C((ANT[0] - 60.0, ANT[1] - 120.0, 120.0), (ANT[0] * 0.5, ANT[1] * 0.5, 0.0), 26), "C"),
    ("C08f", None, s("08-09") - 0.3, C((PAD[0] - 5.5, PAD[1] - 5.0, ANT_H + 2.4), (PAD[0] - 1.3, PAD[1] - 0.4, ANT_H + 0.8), 30), "C"),
    ("C08g", None, s("08-10"), C((PAD[0] - 5.5, PAD[1] + 2.0, ANT_H + 2.2), (ANT[0], ANT[1], ANT_H + 0.3), 30), "C"),
]
STAGE = {"A": b_room, "B": b_inside, "C": b_sky}


def _follow_pk(dx, dy, dz, lens=30, tx=0.0, ty=0.0, tz=0.3):
    """包みを追うカメラ（包みの名前で探す）"""
    def mk(t0):
        c = cam_follow(PKO[0], (dx, dy, dz), tz, lens); c.data.dof.aperture_fstop = 64.0
        return c
    return mk


def _cam_dive(t0):
    """03-06〜03-07：送信のボタンのまるロボを前から → 小さくなる → 画面へ寄り続けて白い光の中へ"""
    a = s("03-07") + 0.3; b = e("03-07") + 0.6
    # 通しの点検（v1g）：はじめは背中で、顔が見えなかった → 窓の側の斜め前から始めて、画面へ寄る
    return cam((1.85, 0.15, 0.65), (0.8, 0.12, 0.14), 30, a, b, (0.62, -0.1, 0.16), (0.6, 0.3, 0.05), 40)   # 通しの点検（v1i）：小さくなる中心を足もとにしたら、寄る道がまるロボを通りぬけた → 20 cm 横へ


def _cam_up(t0):
    """08-01〜08-02：包みと一緒に上がり、光る出口の白へ"""
    # 通しの点検（v1b）：カメラが包みより先に上を向き、約 1 秒、何も映らない暗い画面になった → 包みの上がる 0.9 m に合わせて上げる
    c, tg = cam((2.4, -1.6, 1.5), (0.0, 1.6, 1.1), 26, s("08-01") + 0.2, s("08-02") + 0.4, (2.6, -1.8, 2.5), (0.0, 1.7, 2.2), 26)
    return c, tg


def _cam_fly(t0):
    """08-02〜08-03：窓の外へ飛び出す包みの横を一緒に飛ぶ（追う）"""
    return _follow_pk(-4.0, -6.0, 1.6, 26)(t0)


def _cam_side(t0):
    return _follow_pk(5.5, -1.0, 2.2, 24, tz=0.6)(t0)


def _cam_brace(t0):
    return _follow_pk(2.1, -3.4, 1.45, 30, tz=1.5)(t0)   # 通しの点検（v1c）：顔が画面の上で切れた → 少し引いて上へ


CUTS = [(n, STAGE[p], t, {"A03c": _cam_dive, "B08": _cam_up, "C08": _cam_fly, "C08a": _cam_side, "C08b": _cam_brace}.get(n, cm), p) for (n, _f, t, cm, p) in CUTS]
END_T = e("08-10") + 1.5
CUTS.sort(key=lambda c: c[2])
CLIPS = {}
for i, (nm, fn, tc, cm, par) in enumerate(CUTS):
    t0 = max(0.0, tc - 0.1)
    t1 = (CUTS[i + 1][2] + 0.75) if i + 1 < len(CUTS) else END_T
    CLIPS[nm] = (fn, t0, t1, cm, par)


if __name__ == "__main__" or True:
    if CLIPNAME == "--list":
        print(json.dumps({k: [round(v[1], 3), round(v[2], 3), round(([c[2] for c in CUTS if c[0] == k] or [v[1]])[0], 3), v[4]] for k, v in CLIPS.items()}))
    else:
        fn, t0, t1, cm, par = CLIPS[CLIPNAME]
        CLOCK["T0"] = t0; CLOCK["T1"] = t1
        M_ = fn(par)
        if os.environ.get("MARU_PLANONLY"):
            for m_ in MARU_ALL:
                m_.plan(END_T)
            print("MARU_LATE", json.dumps(MARU_LATE, ensure_ascii=False)); sys.exit(0)
        bake_maru(t0, t1)
        if par == "A": shrink_after_bake(M_)
        c_ = cm(t0) if cm is not None else None
        cobj = c_[0] if isinstance(c_, tuple) else c_
        if cobj is not None:
            bpy.context.scene.camera = cobj
            if par == "B" and CLIPNAME == "B04": white_in(cobj, t0 + 0.1, 0.7)
            if par == "C" and CLIPNAME == "C08": white_in(cobj, t0 + 0.05, 0.7)
        FRS = tuple(int(x) for x in _opt("--frames", 2, ())) or None
        render_clip(CLIPNAME, t0, t1, OUTDIR, SAMPLES, RES, 1 if FRS else STEP, fr=FRS, stills=STILLS or None)
