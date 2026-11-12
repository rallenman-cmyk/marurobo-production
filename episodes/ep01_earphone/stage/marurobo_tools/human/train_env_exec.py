# 晴れた電車の車内（紺の布の座席・角の丸い窓・明るい街・握り棒）。ref_scene.py から切り出した共通部分
# 使い方: 呼ぶ側で bpy, bmesh, math, os, np, sdf, Vector, Matrix, mk_mesh, NT, principled, srgb, sc, O, HERE を用意してから exec する
def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexc, rough=0.6, sheen=0.0, metal=0.0, felt=0.0, coat=0.0):
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, base=srgb(hexc), rough=rough, spec=0.35, sheen=sheen, sheen_r=0.45, metal=metal, coat=coat, coat_r=0.2)
    if felt > 0:   # フェルトのような細かい凹凸と色むら
        tc = nt.n("ShaderNodeTexCoord"); nz = nt.n("ShaderNodeTexNoise", i_Scale=380.0, i_Detail=8.0); nt.l(tc.outputs["Object"], nz.inputs["Vector"])
        bp = nt.n("ShaderNodeBump", i_Strength=felt, i_Distance=0.0015); nt.l(nz.outputs["Fac"], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
        n2 = nt.n("ShaderNodeTexNoise", i_Scale=9.0, i_Detail=2.0); nt.l(tc.outputs["Object"], n2.inputs["Vector"])
        mx = nt.n("ShaderNodeMix", data_type="RGBA"); mx.inputs[6].default_value = (*[c * 0.86 for c in srgb(hexc)], 1); mx.inputs[7].default_value = (*srgb(hexc), 1)
        nt.l(n2.outputs["Fac"], mx.inputs[0]); nt.l(mx.outputs[2], b.inputs["Base Color"])
    return m


def box(name, lo, hi, material, bevel=0.01, seg=3, shadow=True):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=[h - l for l, h in zip(lo, hi)], verts=bm.verts); bmesh.ops.translate(bm, vec=[(l + h) / 2 for l, h in zip(lo, hi)], verts=bm.verts)
    bm.to_mesh(me); bm.free(); ob = O.new(name, me); sc.collection.objects.link(ob); me.materials.append(material)
    if bevel > 0:
        bv = ob.modifiers.new("b", "BEVEL"); bv.width = bevel; bv.segments = seg; bv.limit_method = "NONE"
        me.shade_smooth(); ob.modifiers.new("ws", "WEIGHTED_NORMAL")
    ob.visible_shadow = shadow
    return ob


# ---------------------------------------------------------------- 車内（人の背中側＝＋X が窓）。反対側（−X）にも同じ列
SEAT = mat("Seat fabric", "#2C4A86", 0.92, sheen=0.55, felt=0.30)
WALL = mat("Wall", "#D8D3CA", 0.62); FRAME = mat("Window frame", "#C3C7CD", 0.28, metal=0.75)
SKIRT = mat("Seat skirt", "#525760", 0.5)
FLOOR = mat("Floor", "#9A9C9E", 0.5, felt=0.05); CEIL = mat("Ceiling", "#ECEAE5", 0.6); POLE = mat("Pole", "#CDD1D6", 0.15, metal=1.0)
Y0, Y1 = -3.0, 7.0
WIN_Z0, WIN_Z1 = 1.01, 1.86
for side in (1, -1):
    xw = 0.33 if side > 0 else -2.62     # 壁の内側の面
    def X(a, b): return (min(xw + side * a, xw + side * b), max(xw + side * a, xw + side * b))
    xa, xb = X(-0.59, -0.12)              # 座面（壁から 0.12〜0.59m）
    box("Seat cushion", (xa, Y0, 0.33), (xb, Y1, 0.465), SEAT, 0.045, 4)
    sa, sb = X(-0.57, -0.24); box("Seat skirt", (sa, Y0, 0.04), (sb, Y1, 0.33), SKIRT, 0.01)
    ba, bb = X(-0.16, -0.03); box("Seat back", (ba, Y0, 0.44), (bb, Y1, 0.985), SEAT, 0.045, 4)
    wa, wb = X(0.0, 0.06)
    box("Wall low", (wa, Y0 - 1, 0.0), (wb, Y1 + 1, WIN_Z0), WALL, 0.0)
    box("Wall high", (wa, Y0 - 1, WIN_Z1), (wb, Y1 + 1, 2.30), WALL, 0.0)
    # 窓：幅1.20m、柱0.34m。枠は角の丸い四角（外側は柱に重なる）＋上の横の桟
    PITCH, WW = 1.54, 1.20
    y = Y0
    while y < Y1:
        box("Pillar", (wa, y, WIN_Z0), (wb, y + PITCH - WW, WIN_Z1), WALL, 0.012)
        y += PITCH
    def frame_sdf(cy, cz, hw, hh, xw=xw, side=side):
        c = np.array([xw - side * 0.006, cy, cz])
        outer = sdf.rbox(c, np.array([0.016, hw + 0.035, hh + 0.035]), 0.010)
        inner = sdf.rbox(c, np.array([0.05, hw - 0.012, hh - 0.012]), 0.075)
        bar = sdf.rbox(np.array([xw - side * 0.004, cy, WIN_Z1 - 0.20]), np.array([0.012, hw, 0.016]), 0.006)
        return lambda p: np.minimum(np.maximum(outer(p), -inner(p)), bar(p))
    fm = sdf.Model(); y = Y0 + PITCH - WW
    while y < Y1:
        cy = y + WW / 2
        fm.add(sdf.bounded(frame_sdf(cy, (WIN_Z0 + WIN_Z1) / 2, WW / 2, (WIN_Z1 - WIN_Z0) / 2),
                           (xw - 0.1, cy - 0.8, WIN_Z0 - 0.1), (xw + 0.1, cy + 0.8, WIN_Z1 + 0.1), 0.02), "frame")
        y += PITCH
    Vf, Qf = sdf.mesh(fm, np.array([xw - 0.05, Y0, WIN_Z0 - 0.06]), np.array([xw + 0.05, Y1, WIN_Z1 + 0.06]), 0.006, relax_iters=1)
    fo = mk_mesh("Window frames", Vf, [tuple(q) for q in Qf], coll=sc.collection, mats=[FRAME]); fo.data.shade_smooth()
for yy in (1.62,):   # 握り棒（縦）
    me = bpy.data.meshes.new("Pole"); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.018, radius2=0.018, depth=2.30)
    bm.to_mesh(me); bm.free(); ob = O.new("Pole", me); sc.collection.objects.link(ob); ob.location = (-0.33, yy, 1.15); me.materials.append(POLE)
    me.shade_smooth()
box("Floor", (-3.0, Y0 - 1, -0.02), (0.40, Y1 + 1, 0.0), FLOOR, 0.0)
box("Ceiling", (-3.0, Y0 - 1, 2.30), (0.40, Y1 + 1, 2.36), CEIL, 0.0)
# 窓の外の街（光る絵、少しかすませる。影は作らない）
city = bpy.data.images.load(os.path.join(HERE, "refscene", "city.png"))
cm = bpy.data.materials.new("City"); nt = NT(cm)
tx = nt.n("ShaderNodeTexImage"); tx.image = city; tx.extension = "MIRROR"
hz = nt.n("ShaderNodeMix", data_type="RGBA"); hz.inputs[0].default_value = 0.06; hz.inputs[7].default_value = (*srgb("#EEF4F8"), 1); nt.l(tx.outputs["Color"], hz.inputs[6])
em = nt.n("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.9; nt.l(hz.outputs[2], em.inputs["Color"])
o_ = nt.n("ShaderNodeOutputMaterial"); nt.l(em.outputs[0], o_.inputs[0])
for side, xc in ((1, 4.6), (-1, -7.0)):
    me = bpy.data.meshes.new("City"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f_ in bm.faces:
        for l_ in f_.loops: l_[uvl].uv = ((l_.vert.co.x + 0.5) * 1.6, l_.vert.co.y + 0.5)
    bm.to_mesh(me); bm.free(); co_ = O.new("City", me); sc.collection.objects.link(co_); me.materials.append(cm)
    co_.location = (xc, 2.0, 2.2); co_.rotation_euler = (math.radians(90), 0, math.radians(-90 if side > 0 else 90)); co_.scale = (26.0, 6.0, 1)
    co_.visible_shadow = False; co_.visible_diffuse = False

# 車両の端の壁と貫通扉（奥が暗い穴に見えないように）
END_W = mat("End wall", "#D8D3CA", 0.62); DOOR = mat("Gangway door", "#AEB3BA", 0.35, metal=0.35)
DWIN = bpy.data.materials.new("Door window"); _nt = NT(DWIN); _em = _nt.n("ShaderNodeEmission"); _em.inputs["Color"].default_value = (*srgb("#DCE6EE"), 1)
_em.inputs["Strength"].default_value = 1.4; _o = _nt.n("ShaderNodeOutputMaterial"); _nt.l(_em.outputs[0], _o.inputs[0])
for yy, sg in ((Y0, -1), (Y1, 1)):
    box("End wall", (-3.0, yy + sg * 0.0, 0.0), (0.40, yy + sg * 0.06, 2.30), END_W, 0.0)
    box("Gangway door", (-1.56, yy - sg * 0.035, 0.0), (-0.74, yy + sg * 0.01, 1.95), DOOR, 0.008)
    box("Door window", (-1.40, yy - sg * 0.045, 1.08), (-0.90, yy - sg * 0.030, 1.72), DWIN, 0.004, shadow=False)
    box("Door frame top", (-1.62, yy - sg * 0.04, 1.95), (-0.68, yy + sg * 0.01, 2.02), FRAME, 0.004)
