# 6本目（配膳ロボット）：3D の部品（scenes.py が exec で読む。前提：KIT_HERE を決めてから読む）
#   まるロボ・人・材質・光・カメラは 3本目（ep03_ad/storyboard/scenes.py）の部品をそのまま使う
#   材質・壁・点の地図・光る線などは 5本目（ep05_vacuum/anim/kit.py）から写した（下の「5本目から」）
#   新しく作った物：ファミレスの店（テーブル・いす・台所の出口・天井の目印・窓・照明）、先輩（配膳ロボット）、料理（ラーメン・ハンバーグ・デザート）
#   間取りは plan.py（3D の店・上から見た地図・光の点と同じ形）
#   決まり：3D の中に字を書かない。まるロボも先輩も喋らない。止まった物の点＝青緑、動く人の点＝橙、席の点＝白い丸（最後まで同じ）
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector
R = math.radians
_sv = sys.argv
sys.argv = [sys.argv[0], "--", "x", "x.png", "8"]
exec(open(os.path.join(KIT_HERE, "..", "..", "ep03_ad", "storyboard", "scenes.py"), encoding="utf-8").read().split("# ---------------- 場面\n")[0])
sys.argv = _sv
sys.path.insert(0, KIT_HERE)
import plan
FPS = 24
TEAL = "#2FD9C8"          # 止まった物の点・光の物差しの光（最後まで同じ色）
ORANGE_PT = "#FF9A3C"     # 動く人の足の点
WHITE_PT = "#F4F7FF"      # 席の点
LIGHTS = []               # 店の明かり（暗くする場面で、まとめて消す）：(光, 元の強さ)
GLOWS = []                # 光る材質：(材質, 元の強さ)

# ======================================================================== 5本目から
def noise_mat(name, c1, c2, scale=6.0, rough=0.5, wave=False, bump=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexWave" if wave else "ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = scale
    if wave: tx.inputs["Distortion"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = srgb(c1); ramp.color_ramp.elements[1].color = srgb(c2)
    nt.links.new(tx.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if bump:
        bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump
        nt.links.new(tx.outputs["Fac"], bn.inputs["Height"]); nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


def glow_mat(name, col, strength):
    m = mat(name, col, rough=0.4, emit=strength)
    GLOWS.append((m, strength))
    return m


def focus_on(loc, fstop=2.8):
    cam = bpy.context.scene.camera
    t = empty(loc); cam.data.dof.use_dof = True; cam.data.dof.focus_object = t; cam.data.dof.aperture_fstop = fstop
    return t


def arc_band(m, r_out, r_in, z0, z1, a0, a1, parent=None, seg=40):
    """円の一部の帯（前のバンパー）。角度は度、0 度＝-y（前）"""
    me = bpy.data.meshes.new("band"); bm = bmesh.new(); vs = []
    for i in range(seg + 1):
        a = R(a0 + (a1 - a0) * i / seg)
        ring = []
        for r in (r_out, r_in):
            for z in (z0, z1):
                ring.append(bm.verts.new((r * math.sin(a), -r * math.cos(a), z)))
        vs.append(ring)
    for i in range(seg):
        A, B = vs[i], vs[i + 1]
        for (p, q) in ((0, 1), (1, 3), (3, 2), (2, 0)):
            bm.faces.new((A[p], A[q], B[q], B[p]))
    bm.faces.new((vs[0][0], vs[0][1], vs[0][3], vs[0][2])); bm.faces.new((vs[-1][2], vs[-1][3], vs[-1][1], vs[-1][0]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("band", me); bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o


# ---------------- 部屋（2026-11-14 作り込み：ep04「チープ感」・ep02「急にチープ、3D に」を最初から当てる）
#   板の床（板の継ぎ目と木目）・しま模様の壁紙と腰板・窓の外（空・木・遠くの家）・窓から差しこむ日の光・
#   天井（カメラには映らない。日の光が窓からだけ入る）・小物（床の植木・電気スタンド・時計・壁の棚）
def wood_floor(name="floorwood", c1="#B08A66", c2="#9A7452", mortar="#7A5A40", width=1.1, row=0.14, coat=0.15, grain=0.22):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeNewGeometry")      # 世界の位置（物の大きさで模様がのびない）
    br = nt.nodes.new("ShaderNodeTexBrick"); nt.links.new(tc.outputs["Position"], br.inputs["Vector"])
    br.offset = 0.5; br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = width; br.inputs["Row Height"].default_value = row
    br.inputs["Mortar Size"].default_value = 0.0025; br.inputs["Mortar Smooth"].default_value = 0.3; br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = srgb(c1); br.inputs["Color2"].default_value = srgb(c2); br.inputs["Mortar"].default_value = srgb(mortar)
    wv = nt.nodes.new("ShaderNodeTexWave"); nt.links.new(tc.outputs["Position"], wv.inputs["Vector"])
    wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 8.0; wv.inputs["Detail"].default_value = 4.0
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs["Factor"].default_value = grain
    nt.links.new(br.outputs["Color"], mix.inputs[6]); nt.links.new(wv.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.32; b.inputs["Coat Weight"].default_value = coat
    bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = 0.25; bn.invert = True
    nt.links.new(br.outputs["Fac"], bn.inputs["Height"]); nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


def stripe_wall(name, axis):
    """縦じまの壁紙（axis：壁が伸びる向き 'X' か 'Y'）。色の差は小さく"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeNewGeometry")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = axis; wv.wave_profile = 'SAW'
    nt.links.new(tc.outputs["Position"], wv.inputs["Vector"])
    wv.inputs["Scale"].default_value = 2.5; wv.inputs["Distortion"].default_value = 0.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].color = srgb("#F1E9DC"); ramp.color_ramp.elements[1].position = 0.55; ramp.color_ramp.elements[1].color = srgb("#E9DFCF")
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    return m


WALL_MATS = {}


def wall_seg(axis, c, a0, a1, z0, z1, inward, T=0.1, trim=True):
    """壁の一部。axis＝伸びる向き（'X'：y=c の壁、'Y'：x=c の壁）、a0〜a1＝伸びる範囲、inward＝部屋の内側の向き（+1/-1）。
    trim＝腰板・腰の木の帯・はばき（下の板）を付ける"""
    if axis not in WALL_MATS: WALL_MATS[axis] = stripe_wall("wallpaper_" + axis, axis)
    wm = WALL_MATS[axis]
    L = a1 - a0; mid = (a0 + a1) / 2; zc = (z0 + z1) / 2; H = z1 - z0
    def box(m, off, along, zz, h, th, bevel=0.0):
        if axis == 'X': return cube(m, (mid if along is None else along, c - inward * (T / 2) + inward * off, zz), (L if along is None else 0.02, th, h), bevel=bevel)
        return cube(m, (c - inward * (T / 2) + inward * off, mid if along is None else along, zz), (th, L if along is None else 0.02, h), bevel=bevel)
    box(wm, 0.0, None, zc, H, T)
    if trim and z0 < 0.05:
        WH = 0.86
        box(mat("wainscot", "#C3CFBC", rough=0.6), T / 2 + 0.006, None, min(WH, z1) / 2, min(WH, z1), 0.012)
        if z1 > WH: box(mat("chairrail", "#FBF8F2", rough=0.4), T / 2 + 0.014, None, WH, 0.04, 0.03, bevel=0.006)
        box(mat("baseboard", "#FBF8F2", rough=0.4), T / 2 + 0.012, None, 0.05, 0.1, 0.024, bevel=0.004)
        n = int(L / 0.42)
        for k in range(1, n):
            g = a0 + k * L / n
            box(mat("wsgroove", "#A9B7A2", rough=0.7), T / 2 + 0.013, g, min(WH, z1) / 2 + 0.06, min(WH, z1) - 0.24, 0.004)


def outside_view(x1):
    """右の窓の外：空のグラデーション・木・遠くの家（字なし）"""
    m = bpy.data.materials.new("outsky"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = srgb("#F6EEDC"); ramp.color_ramp.elements[1].color = srgb("#8EC3EA")
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.6
    nt.links.new(em.outputs[0], out.inputs[0])
    GLOWS_W.append((em, 1.6))
    o = cube(m, (x1 + 6.0, -0.2, 2.0), (0.05, 16.0, 7.0)); o.visible_shadow = False
    random.seed(11)
    for k in range(6):   # 遠くの家（うすい色）
        y = -5.0 + k * 1.8 + random.uniform(-0.3, 0.3); h = random.uniform(1.4, 2.6)
        cube(mat("farhouse", random.choice(["#D9CDBB", "#CBBFAE", "#E3D8C6"]), rough=0.8), (x1 + 5.2, y, h / 2 - 0.5), (0.3, 1.4, h)).visible_shadow = False
    for k in range(9):   # 木
        y = -3.0 + k * 0.75 + random.uniform(-0.2, 0.2); z = random.uniform(0.9, 1.6); r = random.uniform(0.45, 0.7)
        sphere(mat("tree", random.choice(["#6FA35E", "#5E9150", "#7DB36A"]), rough=0.8), (x1 + 2.6 + random.uniform(0, 1.0), y, z), r, scale=(1, 1, 1.15), seg=16).visible_shadow = False
    cube(mat("fence", "#E8E2D6", rough=0.7), (x1 + 1.8, -0.2, 0.25), (0.05, 8.0, 0.08)).visible_shadow = False
    cube(mat("lawn", "#9CC47F", rough=0.9), (x1 + 3.0, -0.2, -0.3), (6.0, 16.0, 0.05)).visible_shadow = False


DESK_TOP = 0.755
GLOWS_W = []      # 光る節（窓の外の空）：(Emission 節, 元の強さ)。電気を消す場面で一緒に暗くする


def _points_group(name, radius, life):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    m2p = N.new("GeometryNodeMeshToPoints"); m2p.inputs["Radius"].default_value = radius
    st = N.new("GeometryNodeInputSceneTime")
    na = N.new("GeometryNodeInputNamedAttribute"); na.data_type = 'FLOAT'; na.inputs["Name"].default_value = "birth"
    age = N.new("ShaderNodeMath"); age.operation = 'SUBTRACT'
    L.new(st.outputs["Frame"], age.inputs[0]); L.new(na.outputs["Attribute"], age.inputs[1])
    notyet = N.new("ShaderNodeMath"); notyet.operation = 'LESS_THAN'; notyet.inputs[1].default_value = 0.0
    L.new(age.outputs[0], notyet.inputs[0])
    sel = notyet
    if life:
        old = N.new("ShaderNodeMath"); old.operation = 'GREATER_THAN'; old.inputs[1].default_value = life
        L.new(age.outputs[0], old.inputs[0])
        orr = N.new("ShaderNodeMath"); orr.operation = 'MAXIMUM'
        L.new(notyet.outputs[0], orr.inputs[0]); L.new(old.outputs[0], orr.inputs[1]); sel = orr
    dg = N.new("GeometryNodeDeleteGeometry"); dg.domain = 'POINT'
    L.new(gi.outputs[0], m2p.inputs["Mesh"]); L.new(m2p.outputs["Points"], dg.inputs["Geometry"]); L.new(sel.outputs[0], dg.inputs["Selection"])
    sa = N.new("GeometryNodeStoreNamedAttribute"); sa.data_type = 'FLOAT'; sa.domain = 'POINT'; sa.inputs["Name"].default_value = "age"
    L.new(dg.outputs["Geometry"], sa.inputs["Geometry"]); L.new(age.outputs[0], sa.inputs["Value"])
    L.new(sa.outputs["Geometry"], go.inputs[0])
    return ng


def _points_mat(name, col, base, pop, decay):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = 'GEOMETRY'; at.attribute_name = "age"
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = -1.0 / decay
    ex = nt.nodes.new("ShaderNodeMath"); ex.operation = 'EXPONENT'
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY_ADD'; m2.inputs[1].default_value = pop; m2.inputs[2].default_value = base
    nt.links.new(at.outputs["Fac"], m1.inputs[0]); nt.links.new(m1.outputs[0], ex.inputs[0]); nt.links.new(ex.outputs[0], m2.inputs[0])
    em.inputs["Color"].default_value = srgb(col)
    nt.links.new(m2.outputs[0], em.inputs["Strength"]); nt.links.new(em.outputs[0], out.inputs[0])
    m["base"] = base
    return m


def point_cloud(name, pts, col=TEAL, radius=0.018, z=None, base=2.2, pop=8.0, decay=8.0, life=None, t_offset=0.0):
    """pts：(x, y, 生まれた秒) の一覧。秒は場面の頭（CLOCK T0）からの秒"""
    z = plan.LIDAR_Z if z is None else z
    me = bpy.data.meshes.new(name); me.from_pydata([(x, y, z) for x, y, t in pts], [], [])
    a = me.attributes.new("birth", 'FLOAT', 'POINT'); a.data.foreach_set("value", [(t - t_offset) * FPS for x, y, t in pts])
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    mod = ob.modifiers.new("pts", 'NODES'); mod.node_group = _points_group(name + "_g", radius, life * FPS if life else None)
    m = _points_mat(name + "_m", col, base, pop, decay)
    me.materials.append(m)
    # Set Material（点にした後に材質を付ける）
    ng = mod.node_group; sm = ng.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = m
    go = [n for n in ng.nodes if n.type == 'GROUP_OUTPUT'][0]; src = go.inputs[0].links[0].from_socket
    ng.links.new(src, sm.inputs["Geometry"]); ng.links.new(sm.outputs["Geometry"], go.inputs[0])
    ob.visible_shadow = False
    return ob, m


def line_path(name, pts, col=TEAL, width=0.012, z=0.006, emit=2.5):
    """通った道の線（bevel_factor_end を 0→1 に動かすと、線が伸びる）"""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts): sp.points[i].co = (x, y, z, 1)
    cu.bevel_depth = width; cu.bevel_resolution = 2; cu.bevel_factor_mapping_end = 'SPLINE'
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat(name + "_m", col, rough=0.4, emit=emit))
    ob.visible_shadow = False
    return ob


def beam(parent, length=1.0, col=TEAL, r=0.0025, strength=6.0):
    """光の物差しの光の線（parent の -y 方向へ伸びる）。長さは scale.y で変える"""
    e = empty((0, 0, 0)); e.parent = parent
    b = cyl(glow_mat("beam", col, strength), (0, -0.5, 0), r, 1.0, rot=(R(90), 0, 0), parent=e, verts=8)
    b.visible_shadow = False
    e.scale = (1, length, 1)
    return e


def flat_mat(name, col, strength=1.0):
    """影のない光る色（2D の印に近い物。3D の中の矢印・枠）"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = srgb(col); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def ring_marker(loc, r=0.25, col="#FFD24A", w=0.012, z=0.012):
    """床の上の光る輪（ここを見て、の印。字なし）"""
    bpy.ops.mesh.primitive_torus_add(location=(loc[0], loc[1], z), major_radius=r, minor_radius=w, major_segments=64, minor_segments=8)
    o = bpy.context.object; o.data.materials.append(flat_mat("ring_" + col, col, 3.0)); o.visible_shadow = False
    return o


def render_settings(samples, res, fps=FPS):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    dev = os.environ.get("CYCLES_DEVICE", "CPU"); sc.cycles.device = 'GPU' if dev != "CPU" else 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.fps = fps
    sc.render.use_persistent_data = True
    sc.cycles.max_bounces = 6
    # 光のにじみ（ep04 kit3d.glare と同じ考え。光る点・窓・電気スタンドが少しにじむ）
    sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new("CompositorNodeRLayers"); gl = nt.nodes.new("CompositorNodeGlare"); co = nt.nodes.new("CompositorNodeComposite")
    gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'; gl.threshold = 1.0; gl.size = 7; gl.mix = -0.55
    nt.links.new(rl.outputs["Image"], gl.inputs["Image"]); nt.links.new(gl.outputs["Image"], co.inputs["Image"])
    # ピント：決めていないカメラは、見る点に合わせて奥と手前を少しぼかす（上から見る絵はそのまま）
    cam = sc.camera
    if cam and not cam.data.dof.use_dof:
        tt = [c for c in cam.constraints if c.type == 'TRACK_TO']
        if tt:
            cam.data.dof.use_dof = True; cam.data.dof.focus_object = tt[0].target; cam.data.dof.aperture_fstop = 5.6


# ======================================================================== 6本目：ファミレスの店
#   作り込み（3・4・5本目の「チープ感」の直しを最初から当てる）：板の床・腰板と壁紙・窓の外・テーブルごとのつり下げ照明・
#   植木・仕切りの棚・台所の出口（奥は暖かい光）・天井の目印のシール。字・ロゴ・メニューの字は書かない
def _chair(c, face, col="#B5502F"):
    """いす：座面・背もたれ・4 本の脚。face＝座った人が向く向き（度。0＝-y）"""
    e = empty((c[0], c[1], 0), R(face))
    wood = mat("chairwood", "#7A5233", rough=0.45, coat=0.2)
    cush = mat("cush" + col, col, rough=0.75)
    cube(cush, (0, 0, 0.46), (0.42, 0.42, 0.06), bevel=0.02, parent=e)
    cube(wood, (0, 0, 0.42), (0.42, 0.42, 0.03), bevel=0.008, parent=e)
    cube(wood, (0, 0.19, 0.72), (0.42, 0.04, 0.5), bevel=0.01, parent=e)
    cube(cush, (0, 0.165, 0.74), (0.36, 0.02, 0.34), bevel=0.01, parent=e)
    for (lx, ly) in ((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17)):
        cyl(wood, (lx, ly, 0.2), 0.018, 0.4, parent=e, verts=12)
    return e


def _table(n, cloth="#F4EFE6"):
    x, y = plan.TABLE[n]; T = plan.TSIZE
    top = mat("tabletop", "#8A5E3B", rough=0.3, coat=0.4)
    cube(top, (x, y, 0.72), (T, T, 0.04), bevel=0.01)
    cube(mat("runner", "#E9DCC6", rough=0.8), (x, y, 0.742), (T * 0.36, T, 0.004))
    for (lx, ly) in plan.table_legs(n):
        cube(mat("tableleg", "#3E2E24", rough=0.4, metal=0.2), (lx, ly, 0.35), (plan.TLEG, plan.TLEG, 0.7))
    # 卓上の小物：調味料の小びん・紙ナプキン入れ・コップ（字なし）
    sg = 1 if x > 0 else -1
    for k, col in enumerate(("#C0392B", "#F2C14E")):
        cyl(mat("cond" + col, col, rough=0.3, coat=0.5), (x + sg * 0.3, y - 0.05 + k * 0.08, 0.79), 0.022, 0.09, verts=16)
    cube(mat("napkin", "#C9CED3", rough=0.3, metal=0.6), (x + sg * 0.3, y + 0.2, 0.78), (0.08, 0.05, 0.08), bevel=0.006)
    glass = mat("cup", "#DDEFF5", rough=0.05, trans=0.9)
    for dy in (-0.22, 0.22):
        cyl(glass, (x - sg * 0.12, y + dy, 0.8), 0.033, 0.11, verts=20)


def pendant(x, y, z=1.95):
    """テーブルの上のつり下げ照明（暖かい光）"""
    cyl(mat("pcord", "#2A2522", rough=0.5), (x, y, (plan.CEIL + z) / 2 + 0.1), 0.005, plan.CEIL - z - 0.2, verts=8)
    shade = mat("pshade", "#2F3A3A", rough=0.35, metal=0.4)
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, radius2=0.05, depth=0.2, location=(x, y, z + 0.1), vertices=32)
    c = bpy.context.object; c.data.materials.append(shade); bpy.ops.object.shade_smooth()
    sphere(glow_mat("bulb", "#FFE3B0", 6.0), (x, y, z + 0.02), 0.05, seg=16)
    bpy.ops.object.light_add(type='POINT', location=(x, y, z - 0.05)); pl = bpy.context.object
    pl.data.energy = 60; pl.data.shadow_soft_size = 0.1; pl.data.color = srgb("#FFCF94")[:3]; LIGHTS.append((pl, 60))


def plant(x, y, h=1.1):
    cyl(mat("pot", "#CBB89A", rough=0.6), (x, y, 0.18), 0.17, 0.36, verts=24)
    random.seed(int(x * 100 + y * 10))
    for k in range(14):
        a = k * 2.4; r = random.uniform(0.05, 0.25); z = 0.45 + random.uniform(0, h - 0.4)
        sphere(mat("leaf", "#4E8F4A", rough=0.5), (x + r * math.cos(a), y + r * math.sin(a), z), random.uniform(0.09, 0.15), scale=(1.4, 0.7, 0.5), seg=12)


def restaurant(ceiling=True, top_view=False, pull=None, seated=True):
    """お昼のファミレス。ceiling＝天井を映す（見上げる絵）。top_view＝上から見る絵（天井と手前の壁を映さない）
       pull：{テーブル番号: 通路がわのいすを引き出す長さ}（23 章）。返り値：{通路がわのいす: 物}"""
    world("#F4EADC", 0.2)
    x0, y0, x1, y1 = plan.ROOM; H = plan.CEIL; T = 0.1
    floor = wood_floor("floorwood", "#A97F58", "#94704C", "#6E5038", 1.0, 0.16, 0.2, 0.2)
    plane(floor, ((x0 + x1) / 2, (y0 + y1) / 2, 0), (x1 - x0, y1 - y0))
    # 通路の床だけ、少し明るいタイル（通路が分かるように）
    tile = wood_floor("aisletile", "#D9CFC0", "#CFC4B3", "#A99C8A", 0.4, 0.4, 0.15, 0.06)
    plane(tile, (0, (y0 + y1) / 2, 0.002), (1.08, y1 - y0))
    # 奥の壁（台所の出口の穴）
    k0, k1 = plan.KITCHEN
    wall_seg('X', y1, x0 - T, k0, 0, H, -1); wall_seg('X', y1, k1, x1 + T, 0, H, -1); wall_seg('X', y1, k0, k1, 2.1, H, -1, trim=False)
    cube(mat("kframe", "#6E4B30", rough=0.4), ((k0 + k1) / 2, y1, 2.12), (k1 - k0 + 0.12, 0.16, 0.06))
    for xx in (k0, k1): cube(mat("kframe", "#6E4B30", rough=0.4), (xx, y1, 1.05), (0.06, 0.16, 2.1))
    # 台所（出口の奥）：明るい壁・台・鍋の棚。暖かい光
    cube(mat("kwall", "#F2EDE4", rough=0.8), ((k0 + k1) / 2, y1 + 1.3, H / 2), (2.6, 0.1, H))
    cube(mat("kfloor", "#C9C2B6", rough=0.6), ((k0 + k1) / 2, y1 + 0.65, 0.001), (2.6, 1.3, 0.002))
    cube(mat("steel", "#B9C0C6", rough=0.25, metal=0.8), ((k0 + k1) / 2, y1 + 1.0, 0.45), (2.2, 0.5, 0.9), bevel=0.01)
    for k in range(3):
        cyl(mat("pot_s", "#9AA3AA", rough=0.25, metal=0.8), ((k0 + k1) / 2 - 0.6 + k * 0.6, y1 + 1.0, 1.0), 0.13, 0.2, verts=24)
    bpy.ops.object.light_add(type='POINT', location=((k0 + k1) / 2, y1 + 0.7, 2.2)); pl = bpy.context.object
    pl.data.energy = 220; pl.data.shadow_soft_size = 0.4; pl.data.color = srgb("#FFE6C0")[:3]; LIGHTS.append((pl, 220))
    # 右の壁（大きな窓 3 つ）
    WZ0, WZ1 = 0.85, 2.25; WINS = [(-2.6, -1.1), (-0.8, 0.7), (1.0, 2.5)]
    ys = [y0] + [v for w_ in WINS for v in w_] + [y1]
    for i in range(0, len(ys), 2): wall_seg('Y', x1, ys[i], ys[i + 1], 0, H, -1)
    fr = mat("winf", "#3A3330", rough=0.35, metal=0.3)
    for (a_, b_) in WINS:
        wall_seg('Y', x1, a_, b_, 0, WZ0, -1); wall_seg('Y', x1, a_, b_, WZ1, H, -1, trim=False)
        for (yy, zz, sy, sz) in ((a_, (WZ0 + WZ1) / 2, 0.05, WZ1 - WZ0), (b_, (WZ0 + WZ1) / 2, 0.05, WZ1 - WZ0), ((a_ + b_) / 2, WZ1, b_ - a_, 0.05), ((a_ + b_) / 2, WZ0, b_ - a_, 0.05), ((a_ + b_) / 2, (WZ0 + WZ1) / 2, 0.03, WZ1 - WZ0)):
            cube(fr, (x1 - 0.03, yy, zz), (0.06, sy, sz))
        g = cube(mat("glass", "#FFFFFF", rough=0.02, trans=1.0), (x1, (a_ + b_) / 2, (WZ0 + WZ1) / 2), (0.006, b_ - a_, WZ1 - WZ0)); g.visible_shadow = False
    outside_view(x1)
    # 左の壁（絵と、仕切りの棚）
    wall_seg('Y', x0, y0, y1, 0, H, +1)
    for k, yy in enumerate((-1.85, -0.25, 1.35)):
        cube(mat("frame", "#5B4636", rough=0.5), (x0 + 0.02, yy, 1.6), (0.03, 0.7, 0.5), bevel=0.01)
        cube(mat("art%d" % k, ("#7FB3A8", "#E9B48A", "#A7B8D8")[k], rough=0.7), (x0 + 0.04, yy, 1.6), (0.02, 0.6, 0.4))
        sphere(mat("artsun", "#F2C14E", rough=0.7), (x0 + 0.05, yy + 0.12, 1.66), 0.07, scale=(0.2, 1, 1))
    # 手前の壁（上からの絵では低く・ふつうは影を落とさない）
    if top_view: cube(WALL_MATS['X'], ((x0 + x1) / 2, y0 - T / 2, 0.35), (x1 - x0 + 2 * T, T, 0.7))
    # 天井（板・目印のシール・照明のレール）
    cm = mat("ceil", "#F3EEE6", rough=0.9)
    cc = cube(cm, ((x0 + x1) / 2, (y0 + y1) / 2, H + 0.03), (x1 - x0 + 0.4, y1 - y0 + 0.4, 0.06))
    if not ceiling or top_view: cc.visible_camera = False; cc.visible_glossy = False
    marks = []
    for (mx, my) in plan.CEIL_MARKS:
        o_ = cyl(glow_mat("mark", "#E9EEF2", 0.0), (mx, my, H - 0.002), 0.06, 0.004, verts=24)
        rim_ = cyl(mat("markrim", "#2B3440", rough=0.4), (mx, my, H - 0.001), 0.075, 0.003, verts=24)
        if top_view: o_.visible_camera = False; rim_.visible_camera = False
        marks.append(o_)
    # テーブル・いす・照明
    chairs_in = {}
    for n in plan.TABLE:
        _table(n)
        x, y = plan.TABLE[n]; sg = 1 if x > 0 else -1
        ci = plan.chair_pos(n, 'in', (pull or {}).get(n, 0.0)); co_ = plan.chair_pos(n, 'out')
        chairs_in[n] = _chair(ci, 90 * sg)        # 通路がわ：テーブルの方（外）を向いて座る
        _chair(co_, -90 * sg)
        if ceiling and not top_view: pendant(x, y)
    # 植木（すみ）
    for (px_, py_) in ((x0 + 0.35, y1 - 0.35), (x1 - 0.35, y1 - 0.35), (x0 + 0.35, y0 + 0.5)):
        plant(px_, py_)
    # 明かり：大きなやわらかい光・窓からの日の光・手前の弱い光
    a = area((0.0, 0.0, H - 0.1), (0.0, 0.0, 0.0), energy=420, size=6.0, col="#FFF6EA", shape='SQUARE'); LIGHTS.append((a, 420))
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5)); s_ = bpy.context.object
    s_.rotation_euler = Vector((-0.8, 0.25, -0.55)).normalized().to_track_quat('-Z', 'Y').to_euler()
    s_.data.energy = 4.0; s_.data.color = srgb("#FFE6C4")[:3]; s_.data.angle = R(3); LIGHTS.append((s_, 4.0))
    a2 = area((0.0, -5.5, 2.0), (0.0, 0.5, 0.6), energy=150, size=4.0, col="#FFE9D2"); LIGHTS.append((a2, 150))
    for o in (a, a2): o.visible_camera = False
    return dict(chairs=chairs_in, marks=marks)


def seated(n, side, shirt, hair="#2B2220", s=1.0, kid=False):
    """テーブル n のいすに座っている人（3本目の person）"""
    x, y = plan.TABLE[n]; sg = 1 if x > 0 else -1
    c = plan.chair_pos(n, side); face = 90 * sg if side == 'in' else -90 * sg
    fx, fy = -math.sin(R(face)) * 0.05, math.cos(R(face)) * 0.05
    return person((c[0] - fx, c[1] - fy, 0.0), face_deg=face, shirt=shirt, hair=hair, sit=True, s=0.62 if kid else s)


class Walker:
    """歩く人（足が 2 本。光の物差しの高さで足が見える）。root（場所・向き）・hipL/hipR（足の付け根。前後に振る）"""
    pass


def walker(loc, face=0.0, shirt="#3E7CB1", pants="#2D3640", skin="#F1C7A5", hair="#2B2220", s=1.0, apron=False):
    root = empty((loc[0], loc[1], 0), R(face), s)
    sm = mat("shirt" + shirt, shirt, rough=0.7); pm = mat("pants" + pants, pants, rough=0.7)
    km = mat("skin", skin, rough=0.55); hm = mat("hair" + hair, hair, rough=0.6); sh = mat("shoe", "#2A2522", rough=0.5)
    hips = []
    for sx in (-0.1, 0.1):
        hp = empty((sx, 0, 0.86)); hp.parent = root
        cyl(pm, (0, 0, -0.42), 0.065, 0.84, parent=hp, verts=16)
        cube(sh, (0, -0.04, -0.84), (0.11, 0.24, 0.07), bevel=0.02, parent=hp)
        hips.append(hp)
    cube(pm, (0, 0, 0.9), (0.34, 0.2, 0.16), bevel=0.05, parent=root)
    sphere(sm, (0, 0, 1.2), 0.3, scale=(0.72, 0.48, 0.9), parent=root)
    if apron: cube(mat("apron", "#2B2F36", rough=0.7), (0, -0.14, 1.0), (0.36, 0.02, 0.5), bevel=0.01, parent=root)
    arms = []
    for sx in (-0.25, 0.25):
        ap = empty((sx, 0, 1.38)); ap.parent = root
        cyl(sm, (0, 0, -0.26), 0.05, 0.52, parent=ap, verts=12); sphere(km, (0, 0, -0.55), 0.055, parent=ap, seg=12)
        arms.append(ap)
    he = empty((0, 0, 1.62)); he.parent = root
    sphere(km, (0, 0, 0), 0.17, scale=(0.95, 1.0, 1.08), parent=he)
    sphere(hm, (0, 0.035, 0.05), 0.175, parent=he)
    w_ = Walker(); w_.root = root; w_.hips = hips; w_.arms = arms; w_.head = he; w_.s = s
    return w_


# ======================================================================== 6本目：先輩（配膳ロボット）。前＝-y
#   どこの機械とも言えない形：白い丸い台・回る光の物差しの窓（台の上の黒い帯）・何段かの丸いトレー・上に画面の顔（丸い目 2 つと口の線）・頭に小さな丸い耳
#   前のカメラは 3 つ：台の前に 2 つ（低い所）、頭の下に 1 つ（高い所）
def _ring_dots(m, cx, cz, r, a0, a1, n, parent, y=0.0, dot=0.011):
    """画面の上の、点を並べた弧（口・目を細めた弧）。角度は度（0＝右、反時計回り）"""
    for k in range(n):
        a = R(a0 + (a1 - a0) * k / max(1, n - 1))
        sphere(m, (cx + r * math.cos(a), y, cz + r * math.sin(a)), dot, scale=(1, 0.4, 1), parent=parent, seg=10)


SV_S = 0.88               # 先輩の大きさ（高さ約 1.25 m。まるロボが机の上から耳に届くように少し小さめ）


def senpai_serve(loc=(0, 0), face=0.0, s=SV_S):
    root = empty((loc[0], loc[1], 0), R(face), s)
    LZ = plan.LIDAR_Z / s
    white = mat("sv_white", "#F5F6F7", rough=0.25, coat=0.6)
    grey = mat("sv_grey", "#C9CED3", rough=0.35)
    dark = mat("sv_dark", "#1C2328", rough=0.15, coat=0.8)
    # 台（タイヤは中に隠れる）
    cyl(white, (0, 0, (LZ - 0.03) / 2), 0.245, LZ - 0.03, parent=root, verts=64)
    cyl(grey, (0, 0, 0.015), 0.235, 0.03, parent=root, verts=64)
    # 回る光の物差しの窓（黒い帯）と、中で回る頭
    win = cyl(mat("sv_lidwin", "#20303A", rough=0.05, trans=0.6, coat=1.0), (0, 0, LZ), 0.228, 0.06, parent=root, verts=64)
    spin = empty((0, 0, LZ)); spin.parent = root
    cube(mat("sv_lidhead", "#2A3238", rough=0.3), (0, 0, 0), (0.08, 0.05, 0.03), parent=spin)
    sphere(glow_mat("sv_lideye", TEAL, 4.0), (0, -0.03, 0), 0.008, parent=spin)
    cyl(white, (0, 0, LZ + 0.06), 0.24, 0.06, parent=root, verts=64)
    # 前のカメラ（低い所 2 つ）
    lenses = []
    for sx in (-0.08, 0.08):
        e_ = empty((sx, -0.235, 0.17)); e_.parent = root; e_.rotation_euler = (R(-12), 0, 0)
        cyl(mat("sv_camrim", "#2E3338", rough=0.3, metal=0.4), (0, 0, 0), 0.026, 0.02, rot=(R(90), 0, 0), parent=e_)
        sphere(mat("sv_lens", "#0E1A22", rough=0.05, coat=1.0), (0, -0.008, 0), 0.018, scale=(1, 0.4, 1), parent=e_)
        lenses.append(e_)
    # 背骨（後ろの柱）とトレー 3 段
    cube(white, (0, 0.17, 0.75), (0.3, 0.08, 0.8), bevel=0.03, parent=root)
    trays = []
    for z in (0.52, 0.76, 1.0):
        t_ = empty((0, -0.02, z)); t_.parent = root
        cyl(mat("sv_tray", "#E3E7EA", rough=0.4), (0, 0, 0), 0.23, 0.018, parent=t_, verts=48)
        bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0.012), major_radius=0.225, minor_radius=0.008, major_segments=48, minor_segments=8)
        rim = bpy.context.object; rim.data.materials.append(grey); rim.parent = t_
        trays.append(t_)
    # 首と頭（画面の顔）
    cube(white, (0, 0.13, 1.12), (0.2, 0.1, 0.16), bevel=0.03, parent=root)
    head = empty((0, 0.04, 1.3)); head.parent = root
    cube(white, (0, 0, 0), (0.42, 0.22, 0.3), bevel=0.08, parent=head)
    scr = cube(mat("sv_screen", "#14202C", rough=0.1, coat=1.0, emit=0.15), (0, -0.103, 0), (0.34, 0.02, 0.22), bevel=0.04, parent=head)
    # 高い所のカメラ（頭の下）
    e_ = empty((0, -0.09, -0.17)); e_.parent = head; e_.rotation_euler = (R(-25), 0, 0)
    cyl(mat("sv_camrim", "#2E3338", rough=0.3, metal=0.4), (0, 0, 0), 0.022, 0.02, rot=(R(90), 0, 0), parent=e_)
    sphere(mat("sv_lens", "#0E1A22", rough=0.05, coat=1.0), (0, -0.008, 0), 0.015, scale=(1, 0.4, 1), parent=e_)
    lenses.append(e_)
    # 上を向いたカメラ（天井の目印を見る。頭の上の小さな窓）
    upcam = cyl(mat("sv_up", "#0E1A22", rough=0.05, coat=1.0), (0, 0.02, 0.152), 0.03, 0.008, parent=head)
    # 耳（小さな丸）
    ears = []
    for sx in (-0.13, 0.13):
        ep = empty((sx, 0.0, 0.15)); ep.parent = head
        sphere(white, (0, 0, 0.03), 0.06, scale=(1, 0.7, 1), parent=ep)
        sphere(mat("sv_earin", "#F4C7C3", rough=0.6), (0, -0.035, 0.03), 0.035, scale=(1, 0.3, 1), parent=ep)
        ears.append(ep)
    # 顔（画面の上。表情ごとに組を作り、見せる組を替える）
    eyem = glow_mat("sv_eye", "#BFF7EF", 5.0); mouthm = glow_mat("sv_mouth", "#BFF7EF", 4.0); browm = glow_mat("sv_brow", "#BFF7EF", 4.0)
    y_ = -0.116; F = {}
    def grp(name):
        g = empty((0, 0, 0)); g.parent = head; F[name] = g; return g
    g = grp("normal")
    for sx in (-0.075, 0.075): sphere(eyem, (sx, y_, 0.025), 0.032, scale=(1, 0.3, 1.1), parent=g, seg=20)
    _ring_dots(mouthm, 0, -0.035, 0.035, 200, 340, 7, g, y_)
    g = grp("happy")      # 目を細めて、にこっ（∩∩ の弧と大きな笑い）
    for sx in (-0.075, 0.075): _ring_dots(eyem, sx, 0.012, 0.03, 20, 160, 7, g, y_, 0.012)
    _ring_dots(mouthm, 0, -0.03, 0.045, 195, 345, 9, g, y_)
    g = grp("trouble")    # 困り顔（眉が八の字・口は波）
    for sx in (-0.075, 0.075): sphere(eyem, (sx, y_, 0.02), 0.026, scale=(1, 0.3, 1.1), parent=g, seg=20)
    for sx, rot in ((-0.075, -18), (0.075, 18)):
        b_ = cube(browm, (sx, y_, 0.07), (0.05, 0.01, 0.011), parent=g); b_.rotation_euler = (0, R(rot), 0)
    for k in range(5):
        sphere(mouthm, (-0.03 + k * 0.015, y_, -0.045 + (0.006 if k % 2 else -0.004)), 0.009, scale=(1, 0.4, 1), parent=g, seg=10)
    g = grp("angry")      # 怒り顔（眉がつり上がる・目は細く・口はへの字）
    for sx in (-0.075, 0.075): sphere(eyem, (sx, y_, 0.015), 0.03, scale=(1, 0.3, 0.45), parent=g, seg=20)
    for sx, rot in ((-0.075, 25), (0.075, -25)):
        b_ = cube(browm, (sx, y_, 0.062), (0.06, 0.01, 0.013), parent=g); b_.rotation_euler = (0, R(rot), 0)
    _ring_dots(mouthm, 0, -0.07, 0.035, 25, 155, 7, g, y_)
    g = grp("dots")       # 「…」（にらめっこ）
    for sx in (-0.075, 0.075): sphere(eyem, (sx, y_, 0.025), 0.032, scale=(1, 0.3, 1.1), parent=g, seg=20)
    for k in range(3): sphere(mouthm, (-0.03 + k * 0.03, y_, -0.045), 0.011, scale=(1, 0.4, 1), parent=g, seg=10)
    led = sphere(glow_mat("sv_led", "#7CE8B0", 2.0), (0.17, -0.105, -0.12), 0.008, parent=head)
    return dict(root=root, spin=spin, head=head, face=F, ears=ears, trays=trays, lenses=lenses, upcam=upcam, led=led, screen=scr, lidwin=win)


# ======================================================================== 6本目：料理（字なし）
def ramen(parent=None, loc=(0, 0, 0), steam=True):
    e = empty(loc); 
    if parent: e.parent = parent
    bowl = mat("bowl", "#B8372B", rough=0.25, coat=0.7); inner = mat("bowlin", "#F4F1EA", rough=0.3, coat=0.5)
    bpy.ops.mesh.primitive_cone_add(radius1=0.045, radius2=0.09, depth=0.07, location=(0, 0, 0.035), vertices=40)
    c = bpy.context.object; c.data.materials.append(bowl); c.parent = e; bpy.ops.object.shade_smooth()
    cyl(inner, (0, 0, 0.0715), 0.089, 0.002, parent=e, verts=40)
    broth = cyl(mat("broth", "#D9A35A", rough=0.15, coat=1.0), (0, 0, 0.0735), 0.08, 0.002, parent=e, verts=40)
    random.seed(3)
    for k in range(9):
        a = k * 0.7; r = 0.02 + 0.03 * (k % 3) / 2
        sphere(mat("noodle", "#F2D27A", rough=0.4), (r * math.cos(a), r * math.sin(a), 0.075), 0.025, scale=(1.4, 0.5, 0.15), parent=e, seg=12)
    for k, (dx, dy) in enumerate(((-0.035, 0.02), (-0.01, 0.04))):
        cyl(mat("chashu", "#C98C66", rough=0.5), (dx, dy, 0.077), 0.028, 0.006, parent=e, verts=24)
    sphere(mat("egg", "#FFFFFF", rough=0.3), (0.035, -0.02, 0.076), 0.02, scale=(1, 1, 0.45), parent=e, seg=16)
    sphere(mat("yolk", "#F2A93B", rough=0.3), (0.035, -0.02, 0.081), 0.011, scale=(1, 1, 0.4), parent=e, seg=12)
    for k in range(6):
        sphere(mat("negi", "#5FA84E", rough=0.5), (0.02 - 0.01 * k, -0.04 + 0.012 * k, 0.077), 0.006, parent=e, seg=8)
    st = []
    if steam:
        sm = mat("steam", "#FFFFFF", rough=0.9, alpha=0.18)
        for k in range(4):
            o_ = sphere(sm, (0.02 * math.cos(k * 1.7), 0.02 * math.sin(k * 1.7), 0.11 + 0.04 * k), 0.03, parent=e, seg=12); o_.visible_shadow = False
            st.append(o_)
    return dict(root=e, broth=broth, steam=st)


def hamburg(parent=None, loc=(0, 0, 0)):
    e = empty(loc)
    if parent: e.parent = parent
    cyl(mat("plate", "#FBFBF8", rough=0.25, coat=0.5), (0, 0, 0.008), 0.12, 0.016, parent=e, verts=40)
    sphere(mat("hamb", "#6B3E24", rough=0.5), (-0.01, 0, 0.03), 0.06, scale=(1.3, 1, 0.45), parent=e)
    sphere(mat("sauce", "#5A2412", rough=0.2, coat=0.8), (-0.01, 0, 0.042), 0.05, scale=(1.3, 1, 0.25), parent=e)
    for k, col in enumerate(("#E08A3A", "#5FA84E", "#F2D27A")):
        sphere(mat("side" + col, col, rough=0.5), (0.07, -0.04 + k * 0.04, 0.025), 0.02, parent=e, seg=12)
    return e


def light_plane(parent, r=1.6, col=TEAL, a=0.12):
    """回る光が見ている高さ（水平に広がる、うすい光の板）"""
    m = mat("lplane", col, rough=0.5, emit=0.35, alpha=a)
    o = cyl(m, (0, 0, 0), r, 0.004, parent=parent, verts=64); o.visible_shadow = False
    return o, m


def cam_fan(parent, near=0.05, far=1.2, a_lo=-40, a_hi=55, half_w=35, col="#FFE27A", alpha=0.16):
    """前のカメラが見ている範囲（上下に広がる扇）。前＝-y。角度は水平から上を + の度"""
    me = bpy.data.meshes.new("fan"); bm = bmesh.new()
    vs = []
    o = bm.verts.new((0, -near, 0))
    for i in range(9):
        el = R(a_lo + (a_hi - a_lo) * i / 8)
        row = []
        for j in range(5):
            az = R(-half_w + 2 * half_w * j / 4)
            row.append(bm.verts.new((far * math.cos(el) * math.sin(az), -far * math.cos(el) * math.cos(az), far * math.sin(el))))
        vs.append(row)
    for i in range(8):
        for j in range(4): bm.faces.new((vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]))
    for i in range(8):
        bm.faces.new((o, vs[i][0], vs[i + 1][0])); bm.faces.new((o, vs[i + 1][4], vs[i][4]))
    for j in range(4):
        bm.faces.new((o, vs[0][j + 1], vs[0][j])); bm.faces.new((o, vs[8][j], vs[8][j + 1]))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("fan", me); bpy.context.collection.objects.link(ob); ob.parent = parent
    m = mat("fanm", col, rough=0.5, emit=1.0, alpha=alpha); ob.data.materials.append(m); ob.visible_shadow = False
    return ob, m
