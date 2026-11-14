# 図の場面を 3D で作るための共通の部品（2026-11-14 ユーザー「図の場面も 3D で」。見本 S10 で決まった形）
#   各場面の台本で common.py のあとに exec する：exec(open(<look>/kit3d.py).read())
#   舞台＝画面の中の世界（おとなしい背景）。光る台・ガラスの柱・宙に浮く板（絵を貼る）・人・機械・AI の吹き出し・〇×✓・光の線
#   字は 3D に書かない。札は 2D（compose3d.py）で、TRACK の場所に重ねる
import bpy, math
OR, TE, RED, GRN, NV = "#FF8A2A", "#2CD3C2", "#E24C42", "#3FBF6A", "#1E3352"


def setup_stage():
    screen_world(gate=False, gatekeeper=False)


def glare():
    sc = bpy.context.scene; sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new("CompositorNodeRLayers"); gl = nt.nodes.new("CompositorNodeGlare"); co = nt.nodes.new("CompositorNodeComposite")
    gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'; gl.threshold = 0.9; gl.size = 8; gl.mix = -0.3
    nt.links.new(rl.outputs["Image"], gl.inputs["Image"]); nt.links.new(gl.outputs["Image"], co.inputs["Image"])


def dolly(keys, lens=30, fstop=3.2):
    """keys：[(t, カメラの場所, 見る所), …]。いつもゆっくり動く（止まらない）"""
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    cam = camera(keys[0][1], keys[0][2], lens)
    tgt = empty(keys[0][2])
    for c in list(cam.constraints): cam.constraints.remove(c)
    c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    for t, p, q in keys:
        key(cam, "location", f(t), p); key(tgt, "location", f(t), q)
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = fstop
    bpy.context.scene.camera = cam
    return cam, tgt


def group(objs, pivot):
    """物をまとめて 1 つの空の物の子にする（出る・消える・動くをまとめて）"""
    g = empty(pivot)
    bpy.context.view_layer.update()
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = g; o.matrix_world = mw
    return g


def _new_objs(fn):
    before = set(bpy.data.objects); r = fn(); return r, [o for o in bpy.data.objects if o not in before]


def build(fn, pivot):
    """fn() で作った物を、pivot の空の物の子にまとめる → (fn の戻り値, まとめ)"""
    r, obs = _new_objs(fn)
    return r, group([o for o in obs if o.parent is None], pivot)


def _lights(g):
    return [o for o in g.children_recursive if o.type == 'LIGHT']


def pop(g, t, d=0.45, s=1.0):
    """ぽんと出る（その前は見えない。中の明かりも消しておく）"""
    key(g, "scale", f(CLOCK["T0"]), (0.001,) * 3); key(g, "scale", f(t), (0.001,) * 3)
    key(g, "scale", f(t + d * 0.65), (s * 1.08,) * 3); key(g, "scale", f(t + d), (s,) * 3)
    for L in _lights(g):
        e = L.data.energy
        for fr, v in ((f(CLOCK["T0"]), 0.0), (f(t), 0.0), (f(t + d), e)):
            L.data.energy = v; L.data.keyframe_insert("energy", frame=fr)


def vanish(g, t, d=0.3, s=1.0):
    key(g, "scale", f(t), (s,) * 3); key(g, "scale", f(t + d), (0.001,) * 3)
    for L in _lights(g):
        fc = L.data.animation_data.action.fcurves[0] if L.data.animation_data else None
        e = fc.evaluate(f(t)) if fc else L.data.energy
        for fr, v in ((f(t), e), (f(t + d), 0.0)):
            L.data.energy = v; L.data.keyframe_insert("energy", frame=fr)


def rise(g, t, dz=1.0, d=0.8):
    """下から上がってくる"""
    z = g.location.z
    key(g, ("location", 2), f(CLOCK["T0"]), z - dz); key(g, ("location", 2), f(t), z - dz); key(g, ("location", 2), f(t + d), z)


def bob(g, t0, t1, a=0.06, per=2.4):
    """ふわふわ浮く"""
    z = g.location.z; t = t0
    while t < t1:
        key(g, ("location", 2), f(t), z); key(g, ("location", 2), f(t + per / 2), z + a); t += per
    key(g, ("location", 2), f(t), z)


def podium(x, y, col, name):
    cyl(mat("pod_" + name, NV, rough=0.25, coat=0.6), (x, y, 0.18), 1.25, 0.36)
    cyl(mat("pod_top_" + name, "#E9F1F7", rough=0.3), (x, y, 0.37), 1.12, 0.03)
    rim = mat("rim_" + name, col, emit=5.0)
    bpy.ops.mesh.primitive_torus_add(location=(x, y, 0.37), major_radius=1.18, minor_radius=0.025)
    bpy.context.object.data.materials.append(rim)
    bpy.ops.object.light_add(type='POINT', location=(x, y - 0.6, 0.9)); L = bpy.context.object
    L.data.energy = 120; L.data.color = srgb(col)[:3]; L.data.shadow_soft_size = 0.8
    return rim


def person(x, y, z=0.38, shirt_c="#3E7CB1", name="p"):
    """おもちゃのような人（足もとが z）。頭の物を返す"""
    skin = mat(name + "_skin", "#F6D4B8", rough=0.55); shirt = mat(name + "_shirt", shirt_c, rough=0.5)
    hair = mat(name + "_hair", "#46342C", rough=0.6); pants = mat(name + "_pants", "#2B3A55", rough=0.6)
    b = z - 0.38
    for sx in (-0.13, 0.13): cyl(pants, (x + sx, y, b + 0.7), 0.1, 0.64)
    cyl(shirt, (x, y, b + 1.25), 0.3, 0.62); sphere(shirt, (x, y, b + 1.55), 0.3, scale=(1, 0.8, 0.45))
    sphere(shirt, (x, y, b + 0.95), 0.3, scale=(1, 0.85, 0.35))
    for sx in (-0.37, 0.37): cyl(shirt, (x + sx, y, b + 1.2), 0.08, 0.55, rot=(0, R(8 if sx < 0 else -8), 0))
    for sx in (-0.4, 0.4): sphere(skin, (x + sx, y, b + 0.9), 0.08)
    cyl(skin, (x, y, b + 1.72), 0.07, 0.14)
    head = sphere(skin, (x, y, b + 1.98), 0.25)
    sphere(hair, (x, y + 0.03, b + 2.05), 0.262, scale=(1, 1, 0.82))
    sphere(skin, (x, y - 0.04, b + 1.95), 0.245)
    for sx in (-0.08, 0.08): sphere(mat("p_eye", "#1B2233", rough=0.2), (x + sx, y - 0.24, b + 1.98), 0.028)
    return head


def dot_mats(prefix, n=3):
    ms = []
    for k in range(n):
        m = bpy.data.materials.new("%s_dot%d" % (prefix, k)); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (1, 1, 1, 1)
        b.inputs["Emission Color"].default_value = (1, 1, 1, 1); b.inputs["Emission Strength"].default_value = 1.0
        ms.append(m)
    return ms


def think(ms, t, n=5, gap=0.3):
    """3 つの点が順に光る（考え中）"""
    for k, m in enumerate(ms):
        for j in range(n):
            tt = t + j * gap + k * 0.1
            matkey(m, f(tt), 1.0); matkey(m, f(tt + 0.08), 6.0); matkey(m, f(tt + 0.2), 1.0)


def machine(x, y, z=0.38):
    """画面のある機械（プログラム）。3 つの点の材料を返す"""
    body = mat("pg_body", "#DCE6EE", rough=0.3, coat=0.5); dark = mat("pg_dark", NV, rough=0.3)
    b = z - 0.38
    cube(body, (x, y, b + 1.25), (1.3, 0.55, 0.95), bevel=0.12)
    cube(dark, (x, y - 0.24, b + 1.25), (1.1, 0.1, 0.75), bevel=0.06)
    cube(mat("pg_screen", TE, emit=2.2), (x, y - 0.3, b + 1.25), (1.0, 0.02, 0.65), bevel=0.02)
    cyl(body, (x, y, b + 0.62), 0.09, 0.5); cyl(body, (x, y, b + 0.42), 0.4, 0.06)
    ms = dot_mats("pg%d" % int(x * 10))
    for k, m in enumerate(ms): sphere(m, (x - 0.25 + k * 0.25, y - 0.33, b + 1.25), 0.07)
    return ms


def chatbot(x, y, z, s=1.0, col="#1FAE9F", name="ai"):
    """AI の印：青緑の吹き出しの形に 3 つの点（本物のロゴに似せない）。点の材料を返す"""
    body = mat(name + "_body", col, rough=0.25, coat=0.7, emit=0.12)
    cube(body, (x, y, z), (1.6 * s, 0.5 * s, 1.15 * s), bevel=0.4 * s)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.26 * s, radius2=0.0, depth=0.55 * s,
                                    location=(x - 0.42 * s, y, z - 0.68 * s), rotation=(0, R(-155), 0))
    bpy.context.object.data.materials.append(body)
    ms = dot_mats(name)
    for k, m in enumerate(ms): sphere(m, (x + (k - 1) * 0.42 * s, y - 0.26 * s, z + 0.03 * s), 0.11 * s)
    return ms


def board(tex, x, y, z, w, h, emit=1.1, frame_c=NV, name=None):
    """宙に浮く板：紺のふちに絵を貼る（正面は −Y）。絵の材料を返す"""
    name = name or ("bd_" + tex)
    cube(mat(name + "_back", frame_c, rough=0.3, coat=0.5), (x, y + 0.06, z), (w + 0.24, 0.1, h + 0.24), bevel=0.06)
    m = img(tex, emit=emit)
    plane(m, (x, y - 0.0, z), (w, h), rot=(R(90), 0, 0))
    return m


def swap_tex(m, tex, t):
    """板の絵を、ある時刻で替える（混ぜる量をキーで 0→1）"""
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; t0 = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = bpy.data.images.load(os.path.join(TEX, tex + ".png"))
    mx = nt.nodes.new("ShaderNodeMixRGB"); mx.inputs[0].default_value = 0.0
    nt.links.new(t0.outputs["Color"], mx.inputs[1]); nt.links.new(t1.outputs["Color"], mx.inputs[2])
    nt.links.new(mx.outputs[0], b.inputs["Base Color"]); nt.links.new(mx.outputs[0], b.inputs["Emission Color"])
    mx.inputs[0].keyframe_insert("default_value", frame=f(t) - 2)
    mx.inputs[0].default_value = 1.0; mx.inputs[0].keyframe_insert("default_value", frame=f(t) + 2)


def frame_rect(x, y, z, w, h, col, name, th=0.05, emit=4.0):
    """光る四角い枠（板の前）"""
    m = mat(name, col, emit=emit)
    for dz in (-h / 2, h / 2): cube(m, (x, y, z + dz), (w + th, th, th))
    for dx in (-w / 2, w / 2): cube(m, (x + dx, y, z), (th, th, h + th))
    return m


def xmark(x, y, z, s=1.0, col=RED, name="x"):
    m = mat(name, col, rough=0.3, emit=1.6)
    for a in (45, -45): cube(m, (x, y, z), (1.2 * s, 0.14 * s, 0.2 * s), rot=(0, R(a), 0), bevel=0.05 * s)


def check3d(x, y, z, s=1.0, col=GRN, name="ck"):
    m = mat(name, col, rough=0.3, emit=1.4)
    cyl(m, (x, y + 0.05, z), 0.55 * s, 0.1 * s, rot=(R(90), 0, 0))
    w = mat(name + "_w", "#FFFFFF", emit=1.5)
    cube(w, (x - 0.14 * s, y - 0.03, z - 0.05 * s), (0.3 * s, 0.06, 0.09 * s), rot=(0, R(45), 0))
    cube(w, (x + 0.09 * s, y - 0.03, z + 0.03 * s), (0.55 * s, 0.06, 0.09 * s), rot=(0, R(-55), 0))


def ring3d(x, y, z, r, col, name, minor=0.04, emit=4.0, rot=(R(90), 0, 0)):
    bpy.ops.mesh.primitive_torus_add(location=(x, y, z), rotation=rot, major_radius=r, minor_radius=minor)
    o = bpy.context.object; o.data.materials.append(mat(name, col, emit=emit)); return o


def arrow_up(x, y, z, s=1.0, col=OR, name="arw"):
    m = mat(name, col, rough=0.3, emit=1.5)
    cyl(m, (x, y, z), 0.13 * s, 0.9 * s)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.32 * s, depth=0.5 * s, location=(x, y, z + 0.68 * s))
    bpy.context.object.data.materials.append(m)


def beam(p0, p1, col, name, r=0.02, emit=4.0):
    """光の線（p0→p1）。伸びる動きは grow で"""
    import mathutils
    a, b = mathutils.Vector(p0), mathutils.Vector(p1); d = b - a
    g = empty(p0)
    o = cyl(mat(name, col, emit=emit), (0, 0, d.length / 2), r, d.length)
    o.parent = g
    g.rotation_mode = 'QUATERNION'; g.rotation_quaternion = mathutils.Vector((0, 0, 1)).rotation_difference(d)
    return g


def grow(g, t, d=0.5):
    key(g, "scale", f(CLOCK["T0"]), (1, 1, 0.001)); key(g, "scale", f(t), (1, 1, 0.001)); key(g, "scale", f(t + d), (1, 1, 1))


def track(name, ob, dz=0.0):
    TRACK[name] = (ob, dz)


def anchor_at(name, loc):
    TRACK[name] = (empty(loc), 0.0)


def breathe(mr, t0, t1, skip=()):
    """まるロボの息（ゆっくり上下）。skip＝[(a, b), …] の間は止める（跳ぶ所など）"""
    t = t0
    while t < t1 - 1:
        if not any(a - 0.5 < t < b for a, b in skip):
            key(mr.body, ("location", 2), f(t), mr.z0); key(mr.body, ("location", 2), f(t + 0.45), mr.z0 + 0.02); key(mr.body, ("location", 2), f(t + 0.9), mr.z0)
        t += 1.8


def tube(cx, cy, col, name, h=3.0):
    """ガラスの柱。中の光（liq）がたまる。(liq, 高さ) を返す"""
    glass = mat("glass_" + name, "#CFE9F5", rough=0.05, trans=0.95, alpha=0.35)
    cyl(glass, (cx, cy, 0.2 + h / 2), 0.32, h)
    cyl(mat("tcap_" + name, NV, rough=0.3), (cx, cy, 0.12), 0.42, 0.24)
    cyl(mat("tcap_" + name, NV, rough=0.3), (cx, cy, 0.24 + h), 0.38, 0.1)
    liq = cyl(mat("liq_" + name, col, emit=2.8, alpha=0.9), (cx, cy, 0.24), 0.27, 1.0)
    liq.scale = (1, 1, 0.001); liq.location.z = 0.24
    for k in range(1, 10):
        bpy.ops.mesh.primitive_torus_add(location=(cx, cy, 0.24 + (h - 0.1) * k / 10), major_radius=0.325, minor_radius=0.006)
        bpy.context.object.data.materials.append(mat("tick", "#FFFFFF", emit=0.8))
    return liq, h - 0.1


def fill(liq, H, t, frac, d=1.2):
    key(liq, ("scale", 2), f(t), liq.scale[2]); key(liq, ("location", 2), f(t), liq.location.z)
    liq.scale[2] = max(frac * H, 0.001); liq.location.z = 0.24 + frac * H / 2
    key(liq, ("scale", 2), f(t + d), liq.scale[2]); key(liq, ("location", 2), f(t + d), liq.location.z)


def scan(x0, x1, y, z, h, t0, t1, per=1.4, col=TE, name="scan"):
    """光の線が板の上を左右に走る（機械が読む）"""
    o = cube(mat(name, col, emit=6.0, alpha=0.9), (x0, y, z), (0.05, 0.03, h)); s0 = tuple(o.scale)
    on, off = s0, (0.0001, 0.0001, 0.0001)
    key(o, "scale", f(CLOCK["T0"]), off); key(o, "scale", f(t0), off); key(o, "scale", f(t0 + 0.2), on)
    t = t0; a = True
    while t < t1:
        key(o, ("location", 0), f(t), x0 if a else x1); t += per / 2; a = not a
    key(o, ("location", 0), f(t), x0 if a else x1)
    key(o, "scale", f(t1), on); key(o, "scale", f(t1 + 0.2), off)
    return o


def cursor(name="cur"):
    """マウスの矢印（白・紺のふち）。先が原点。動きは location にキーで"""
    def mk():
        w = mat(name + "_w", "#FFFFFF", rough=0.3, emit=0.8)
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.22, depth=0.06, location=(0.1, 0, -0.16), rotation=(R(90), R(-30), 0))
        bpy.context.object.data.materials.append(w)
        cube(w, (0.17, 0, -0.38), (0.07, 0.05, 0.28), rot=(0, R(-28), 0))
    _, g = build(mk, (0, 0, 0)); return g
