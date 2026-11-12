# 晴れた朝の電車：車内の網棚・つり革・天井の照明と、窓の外の動く世界（地面・架線柱・建物・遠くの街・空）、物理に合わせた光
# train_env_exec.py の後に exec する（bpy, bmesh, math, os, np, Vector, Matrix, mat, box, kelvin, srgb, NT, principled, sc, O, HERE を使う）
#   電車は +Y へ時速60km（16.7m/s）で走る。外の物はすべて FLOW の子で、FLOW を −Y へ動かす（電車から見た相対運動）
#   太陽：朝・東（窓の側＝+X、少し前）・高さ28°・4800K・見かけの大きさ0.53°（本物の太陽と同じ＝影のふちのぼけ方が正しい）
#   空：Nishita の物理モデル（太陽の位置から空の色と明るさを計算）。カメラから見える空は明るく、車内を照らす分は窓の光として入れる
V_TRAIN = 60.0 / 3.6
SUN_DIR = Vector((0.80, 0.35, 0.47)).normalized()          # 太陽のある向き（ここから光が来る）
SUN_EL = math.asin(SUN_DIR.z)
GROUND_Z = -1.15                                           # 車内の床から地面（線路の砂利）まで
rngw = random.Random(21)


def emit_mat(name, rgb, strength):
    m = bpy.data.materials.new(name); nt_ = NT(m); e = nt_.n("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1)
    e.inputs["Strength"].default_value = strength; o = nt_.n("ShaderNodeOutputMaterial"); nt_.l(e.outputs[0], o.inputs[0]); return m


def cyl_mesh(name, r, depth, loc, rot, material, seg=24):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    bm.to_mesh(me); bm.free(); ob = O.new(name, me); sc.collection.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    me.materials.append(material); me.shade_smooth(); return ob


# ---------------------------------------------------------------- 網棚とつり革（つり革は振り子：seq で揺らす）
RACK = mat("Luggage rack", "#B9BEC4", 0.35, metal=0.8); STRAP_BAND = mat("Strap band", "#F2F0EA", 0.55); STRAP_RING = mat("Strap ring", "#E9E7E1", 0.35, coat=0.3)
for xw, sgn in ((0.33, 1), (-2.62, -1)):
    x_in = xw - sgn * 0.32
    box("Rack shelf", (min(xw, x_in), Y0, 1.785), (max(xw, x_in), Y1, 1.80), RACK, 0.004)
    cyl_mesh("Rack rail", 0.012, Y1 - Y0, (x_in, (Y0 + Y1) / 2, 1.80), (math.radians(90), 0, 0), RACK)
STRAP_X = (-0.32, -1.97); STRAP_Z = 1.96; STRAPS = []
for xs in STRAP_X:
    cyl_mesh("Strap bar", 0.013, Y1 - Y0, (xs, (Y0 + Y1) / 2, STRAP_Z), (math.radians(90), 0, 0), POLE)
    y = Y0 + 0.30
    while y < Y1 - 0.25:
        if not (xs > -1.0 and abs(y - 1.62) < 0.15):
            me = bpy.data.meshes.new("Strap"); bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            for v in bm.verts: v.co = Vector((v.co.x * 0.004, v.co.y * 0.026, v.co.z * 0.20 - 0.10))
            rr, rm = 0.052, 0.0085                         # 輪（握る所）
            rv = []
            for i in range(24):
                a0 = 2 * math.pi * i / 24
                for j in range(8):
                    b0 = 2 * math.pi * j / 8; r = rr + rm * math.cos(b0)
                    rv.append(bm.verts.new((rm * math.sin(b0), r * math.cos(a0), -0.20 - rr + r * math.sin(a0))))
            for i in range(24):
                for j in range(8):
                    bm.faces.new([rv[i * 8 + j], rv[((i + 1) % 24) * 8 + j], rv[((i + 1) % 24) * 8 + (j + 1) % 8], rv[i * 8 + (j + 1) % 8]])
            bm.to_mesh(me); bm.free()
            ob = O.new("Strap", me); sc.collection.objects.link(ob); ob.location = (xs, y, STRAP_Z - 0.012)
            me.materials.append(STRAP_BAND); me.materials.append(STRAP_RING)
            for poly in me.polygons: poly.material_index = 0 if poly.index < 6 else 1; poly.use_smooth = poly.index >= 6
            ob.rotation_mode = "XYZ"
            L = rngw.uniform(0.235, 0.265); zeta = rngw.uniform(0.04, 0.08)
            STRAPS.append(dict(ob=ob, L=L, zeta=zeta))
        y += 0.30

# ---------------------------------------------------------------- 天井の照明（LEDの帯。昼でも点いている）
LED = emit_mat("Ceiling LED", kelvin(5000), 5.0)
for xl in (-0.70, -1.92):
    box("Ceiling light", (xl - 0.08, Y0 + 0.2, 2.275), (xl + 0.08, Y1 - 0.2, 2.30), LED, 0.004, shadow=False)
    ld = bpy.data.lights.new("Ceiling light", "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = 0.16, Y1 - Y0 - 0.4
    ld.energy = 110.0; ld.color = kelvin(5000)
    lo = O.new("Ceiling light", ld); sc.collection.objects.link(lo); lo.location = (xl, (Y0 + Y1) / 2, 2.26)

# ---------------------------------------------------------------- 窓の外：電車に対して −Y へ流れる世界
FLOW = O.new("FLOW", None); sc.collection.objects.link(FLOW)
OUTSIDE = bpy.data.collections.new("Outside"); sc.collection.children.link(OUTSIDE)


def flow(ob):
    ob.parent = FLOW; ob.matrix_parent_inverse = Matrix.Identity(4)
    for c_ in list(ob.users_collection): c_.objects.unlink(ob)
    OUTSIDE.objects.link(ob); return ob


# 地面：線路のまわりは砂利、その外は草と土（物の座標で模様＝地面と一緒に流れる）
gm = bpy.data.materials.new("Ground"); nt_ = NT(gm); b_ = principled(nt_, base=srgb("#6E7A4E"), rough=0.95, spec=0.2)
tc_ = nt_.n("ShaderNodeTexCoord"); sx_ = nt_.n("ShaderNodeSeparateXYZ"); nt_.l(tc_.outputs["Object"], sx_.inputs[0])
d_ = nt_.n("ShaderNodeMath", operation="ABSOLUTE"); ad_ = nt_.n("ShaderNodeMath", operation="ADD"); ad_.inputs[1].default_value = 1.15
nt_.l(sx_.outputs[0], ad_.inputs[0]); nt_.l(ad_.outputs[0], d_.inputs[0])
st_ = nt_.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP"); st_.inputs["From Min"].default_value = 3.0; st_.inputs["From Max"].default_value = 3.9
nt_.l(d_.outputs[0], st_.inputs["Value"])
nz_ = nt_.n("ShaderNodeTexNoise", i_Scale=0.35, i_Detail=6.0); nt_.l(tc_.outputs["Object"], nz_.inputs["Vector"])
gr_ = nt_.n("ShaderNodeMix", data_type="RGBA"); gr_.inputs[6].default_value = (*srgb("#5E6B3F"), 1); gr_.inputs[7].default_value = (*srgb("#8A8160"), 1)
nt_.l(nz_.outputs["Fac"], gr_.inputs[0])
nz2 = nt_.n("ShaderNodeTexNoise", i_Scale=6.0, i_Detail=8.0); nt_.l(tc_.outputs["Object"], nz2.inputs["Vector"])
ba_ = nt_.n("ShaderNodeMix", data_type="RGBA"); ba_.inputs[6].default_value = (*srgb("#6D6A66"), 1); ba_.inputs[7].default_value = (*srgb("#8F8B85"), 1)
nt_.l(nz2.outputs["Fac"], ba_.inputs[0])
mx_ = nt_.n("ShaderNodeMix", data_type="RGBA"); nt_.l(st_.outputs["Result"], mx_.inputs[0]); nt_.l(ba_.outputs[2], mx_.inputs[6]); nt_.l(gr_.outputs[2], mx_.inputs[7])
nt_.l(mx_.outputs[2], b_.inputs["Base Color"])
me = bpy.data.meshes.new("Ground"); bm = bmesh.new()
WL_ = globals().get("WORLD_LEN", 480.0)                     # 窓の外の世界の長さ（第1〜2章は81秒走るので長くする）
for v in ((-200, -120, 0), (200, -120, 0), (200, WL_ + 40.0, 0), (-200, WL_ + 40.0, 0)): bm.verts.new(v)
bm.faces.new(bm.verts); bm.to_mesh(me); bm.free()
gnd = O.new("Ground", me); sc.collection.objects.link(gnd); gnd.location = (0, 0, GROUND_Z); me.materials.append(gm); flow(gnd)

# 架線柱：50mおき（時速60kmで3秒に1本）。窓の側（+X、太陽の側）の柱の影が車内を横切る
CONC = mat("Concrete pole", "#B8B6B0", 0.85)
for xp in (2.3, -5.6):
    for yp in np.arange(-40.0, WL_ - 10.0, 50.0):
        p_ = cyl_mesh("Catenary pole", 0.15, 9.0, (xp, float(yp) + (12.0 if xp < 0 else 0.0), GROUND_Z + 4.5), (0, 0, 0), CONC, seg=16); flow(p_)
        arm = box("Pole arm", (min(xp, -1.15), float(yp) - 0.08 + (12.0 if xp < 0 else 0.0), GROUND_Z + 7.2), (max(xp, -1.15), float(yp) + 0.08 + (12.0 if xp < 0 else 0.0), GROUND_Z + 7.4), CONC, 0.0)
        flow(arm)

# 建物：手前は低く（太陽をさえぎらない）、遠いほど高い。窓の並び（床の高さ3m・窓の間隔1.6m）はれんがの模様で
def facade(name, wall, glass):
    m = bpy.data.materials.new(name); nt2 = NT(m); bb = principled(nt2, base=srgb(wall), rough=0.75, spec=0.35)
    tc2 = nt2.n("ShaderNodeTexCoord"); sp2 = nt2.n("ShaderNodeSeparateXYZ"); nt2.l(tc2.outputs["Object"], sp2.inputs[0])
    cb = nt2.n("ShaderNodeCombineXYZ"); nt2.l(sp2.outputs[1], cb.inputs[0]); nt2.l(sp2.outputs[2], cb.inputs[1])
    br = nt2.n("ShaderNodeTexBrick", i_Scale=1.0, i_Mortar_Size=0.45, i_Bias=0.0, i_Brick_Width=1.6, i_Row_Height=3.0)
    br.offset = 0.0; br.squash = 1.0
    nt2.l(cb.outputs[0], br.inputs["Vector"])
    br.inputs["Color1"].default_value = (*srgb(glass), 1); br.inputs["Color2"].default_value = (*srgb(glass), 1); br.inputs["Mortar"].default_value = (*srgb(wall), 1)
    nt2.l(br.outputs["Color"], bb.inputs["Base Color"])
    return m
FACADES = [facade("Facade %d" % i, w_, g_) for i, (w_, g_) in enumerate((("#D9D4C8", "#8A9AAA"), ("#C9C2B2", "#7E8E9E"), ("#E4E2DC", "#93A2B0"), ("#BFB8A8", "#8696A5"), ("#D2CCC0", "#8C9BA8")))]
ROOF = mat("Roof", "#8C8A86", 0.9)
for side in (1, -1):
    y = -90.0
    while y < WL_:
        w_ = rngw.uniform(9.0, 24.0); gap = rngw.uniform(2.0, 14.0)
        near = rngw.uniform(14.0, 45.0); dpt = rngw.uniform(8.0, 16.0)
        far = near > 26.0
        H = rngw.uniform(9.0, 30.0) if far else rngw.uniform(4.5, 8.5)
        if side > 0: H = min(H, 0.45 * near)                # 太陽（高さ28°）をさえぎらない
        x0 = side * near if side > 0 else -near - 2.3
        lo = (min(x0, x0 + side * dpt), y, GROUND_Z); hi = (max(x0, x0 + side * dpt), y + w_, GROUND_Z + H)
        flow(box("Building", lo, hi, rngw.choice(FACADES), 0.0))
        y += w_ + gap
# 1棟だけ、線路の近くに高い建物（ショットAで太陽をさえぎり、車内の光が一度だけ陰る：本当の電車でよく起きる）
SHADE_T = 2.0                                               # 影が車内（y≈2）にかかる時刻
y_b = 2.0 + 0.44 * 13.5 + V_TRAIN * SHADE_T
flow(box("Building near", (9.0, y_b - 7.0, GROUND_Z), (18.0, y_b + 7.0, GROUND_Z + 17.0), FACADES[1], 0.0))

# 遠くの街：120〜320m 先の建物。空気の散乱で、遠いほど空の色に近づく（見える色＝本来の色×e^(−d/400)＋空の色×(1−e^(−d/400))）
SKY_HAZE = Vector(srgb("#C9D6E2"))
for side in (1, -1):
    y = -420.0
    while y < WL_ + 420.0:
        w_ = rngw.uniform(14.0, 40.0); gap = rngw.uniform(0.0, 18.0); d = rngw.uniform(120.0, 320.0); H = rngw.uniform(12.0, 60.0)
        base = Vector(srgb(rngw.choice(("#D6D0C2", "#B9B4A8", "#C8C9C6", "#A9AEB2", "#DCD8CE"))))
        lit = 1.0 if side < 0 else 0.62                           # 太陽の反対側（−X）は日が当たった面、太陽の側（+X）は日陰の面が見える
        k = math.exp(-d / 400.0); col = base * (lit * k) + SKY_HAZE * (1 - k)
        x0 = side * d if side > 0 else -d - 2.3
        far_m = emit_mat("Far building", tuple(col), 1.25)
        ob = box("Far building", (min(x0, x0 + side * 12), y, GROUND_Z - 1.0), (max(x0, x0 + side * 12), y + w_, GROUND_Z + H), far_m, 0.0, shadow=False)
        ob.visible_diffuse = False; flow(ob)
        y += w_ + gap

# 古い「止まった街の絵」は使わない
for ob_ in [o for o in O if o.name.startswith("City")]:
    O.remove(ob_, do_unlink=True)

# ---------------------------------------------------------------- 空と太陽（物理モデル）と、窓から入る空の光
wd = bpy.data.worlds.new("Sky"); sc.world = wd; wd.use_nodes = True; wn = wd.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"; sky.sun_disc = False
sky.sun_elevation = SUN_EL; sky.sun_rotation = math.atan2(SUN_DIR.y, SUN_DIR.x) - math.pi / 2 + math.pi
sky.altitude = 30.0; sky.air_density = 1.0; sky.dust_density = 1.8; sky.ozone_density = 1.0
bg_cam = wn.nodes.new("ShaderNodeBackground"); bg_cam.inputs[1].default_value = 0.075; wn.links.new(sky.outputs[0], bg_cam.inputs[0])
bg_lit = wn.nodes.new("ShaderNodeBackground"); bg_lit.inputs[0].default_value = (*srgb("#BFD3E6"), 1); bg_lit.inputs[1].default_value = 0.10
lp = wn.nodes.new("ShaderNodeLightPath"); mixw = wn.nodes.new("ShaderNodeMixShader")
wn.links.new(lp.outputs["Is Camera Ray"], mixw.inputs[0]); wn.links.new(bg_lit.outputs[0], mixw.inputs[1]); wn.links.new(bg_cam.outputs[0], mixw.inputs[2])
wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(mixw.outputs[0], wo.inputs["Surface"])
sun_ld = bpy.data.lights.new("Sun", "SUN"); sun_ld.energy = 6.0; sun_ld.color = kelvin(4800); sun_ld.angle = math.radians(0.53)
sun = O.new("Sun", sun_ld); sc.collection.objects.link(sun); sun.rotation_euler = SUN_DIR.to_track_quat("Z", "Y").to_euler()
sky_ld = bpy.data.lights.new("Sky fill (outside)", "SUN"); sky_ld.energy = 2.2; sky_ld.color = kelvin(8500); sky_ld.angle = math.radians(150)
sky_ld.use_shadow = False
sky_fill = O.new("Sky fill (outside)", sky_ld); sc.collection.objects.link(sky_fill); sky_fill.rotation_euler = Vector((-0.3, 0.1, 1.0)).to_track_quat("Z", "Y").to_euler()
try:
    sky_fill.light_linking.receiver_collection = OUTSIDE
except Exception as e_:
    print("LIGHT LINKING NOT AVAILABLE", e_)
# 窓の空：太陽の側（+X）は明るく少し暖かい、反対側（−X）は青い。窓の帯の大きさの面光源（窓そのものが空の明るさで光る）
for xw_, face, kel, en in ((0.30, -1, 6200, 60.0), (-2.59, 1, 9000, 45.0)):
    ld = bpy.data.lights.new("Window sky", "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = 0.85, Y1 - Y0; ld.energy = en; ld.color = kelvin(kel)
    lo = O.new("Window sky", ld); sc.collection.objects.link(lo); lo.location = (xw_, (Y0 + Y1) / 2, (WIN_Z0 + WIN_Z1) / 2)
    lo.rotation_euler = Vector((face, 0, 0)).to_track_quat("-Z", "Y").to_euler()
