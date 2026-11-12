# 共通の部品（Blender）：色・材質・形の道具、石の床、物理の空と太陽、遠くのかすみ、描き方（EEVEE／簡易描画）
#   第3章の舞台（ch03_stage.py）と同じ見た目になるように、そこから取り出してまとめたもの
import math
import bpy, bmesh
from mathutils import Vector, Matrix


def srgb(hexs):
    h = hexs.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def lin(rgb255):
    """0〜255 の sRGB → 線形"""
    return tuple((c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb255)


def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def link(ob, coll=None): (coll or bpy.context.scene.collection).objects.link(ob); return ob


def mat(name, rgb, rough=0.5, metal=0.0, coat=0.0, alpha=1.0, transmission=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    if coat: bs.inputs["Coat Weight"].default_value = coat
    if transmission: bs.inputs["Transmission Weight"].default_value = transmission
    m.diffuse_color = (*rgb, 1)
    return m


def mat_emit(name, rgb, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); m.diffuse_color = (*[min(1.0, c * 1.2) for c in rgb], 1)
    return m


def mesh_obj(name, bm, m, smooth=False, coll=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); ob = link(bpy.data.objects.new(name, me), coll)
    if m: me.materials.append(m)
    if smooth:
        for f in me.polygons: f.use_smooth = True
    return ob


def box(name, size, m, bevel=0.0, seg=3, coll=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = mesh_obj(name, bm, m, coll=coll)
    if bevel > 0:
        b = ob.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = seg; b.limit_method = "ANGLE"
    return ob


def cyl(name, r, depth, m, seg=32, r2=None, coll=None, caps=True):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=caps, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    return mesh_obj(name, bm, m, smooth=True, coll=coll)


def torus(name, major, minor, m, seg=48, rseg=12, arc=2 * math.pi, coll=None):
    bm = bmesh.new(); rings = []; closed = arc >= 2 * math.pi - 1e-6; ns = seg if closed else seg + 1
    for i in range(ns):
        a = arc * i / seg; ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        i2 = (i + 1) % ns if closed else i + 1
        for j in range(rseg):
            bm.faces.new((rings[i][j], rings[i2][j], rings[i2][(j + 1) % rseg], rings[i][(j + 1) % rseg]))
    return mesh_obj(name, bm, m, smooth=True, coll=coll)


def tube(name, pts, r, m, seg=12, coll=None):
    """点の列に沿った管（曲線の面取りで作る）"""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1.0)
    ob = link(bpy.data.objects.new(name, cu), coll); cu.materials.append(m); return ob


def empty(name, coll=None, size=0.1):
    e = bpy.data.objects.new(name, None); e.empty_display_size = size; return link(e, coll)


def slate_material(name="Stage slate", c1="#59616A", c2="#3E454C", haze_dist=260.0, haze_col="#C3CFDA"):
    """1m の石の目地の床。遠くは空の色へかすむ：e^(−距離/haze_dist)"""
    fm = bpy.data.materials.new(name); fm.use_nodes = True; nt = fm.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.62
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    def seam(sock):
        fr_ = nt.nodes.new("ShaderNodeMath"); fr_.operation = "PINGPONG"; fr_.inputs[1].default_value = 0.5; nt.links.new(sock, fr_.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.006; nt.links.new(fr_.outputs[0], lt.inputs[0])
        return lt.outputs[0]
    mx_ = nt.nodes.new("ShaderNodeMath"); mx_.operation = "MAXIMUM"; nt.links.new(seam(sep.outputs[0]), mx_.inputs[0]); nt.links.new(seam(sep.outputs[1]), mx_.inputs[1])
    cell = nt.nodes.new("ShaderNodeTexVoronoi"); cell.feature = "F1"; cell.inputs["Scale"].default_value = 1.0; cell.inputs["Randomness"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], cell.inputs["Vector"])
    var = nt.nodes.new("ShaderNodeMapRange"); var.inputs[3].default_value = 0.92; var.inputs[4].default_value = 1.06; nt.links.new(cell.outputs["Color"], var.inputs[0])
    base = nt.nodes.new("ShaderNodeMix"); base.data_type = "RGBA"; nt.links.new(mx_.outputs[0], base.inputs[0])
    base.inputs[6].default_value = (*srgb(c1), 1); base.inputs[7].default_value = (*srgb(c2), 1)
    tint = nt.nodes.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs[0].default_value = 1.0
    nt.links.new(base.outputs[2], tint.inputs[6]); nt.links.new(var.outputs[0], tint.inputs[7]); nt.links.new(tint.outputs[2], bs.inputs["Base Color"])
    fm.diffuse_color = (*srgb(c1), 1)
    return fm


def hazify(m_, haze_col="#C3CFDA", strength=1.0, dist=260.0):
    """材質の出力に、カメラからの距離で空の色を混ぜる（1 − e^(−距離/dist)）。二度はかけない"""
    nt_ = m_.node_tree
    if nt_ is None or any(n_.bl_idname == "ShaderNodeCameraData" for n_ in nt_.nodes): return False
    outs = [n_ for n_ in nt_.nodes if n_.bl_idname == "ShaderNodeOutputMaterial" and n_.is_active_output] or [n_ for n_ in nt_.nodes if n_.bl_idname == "ShaderNodeOutputMaterial"]
    if not outs or not outs[0].inputs["Surface"].links: return False
    out = outs[0]; src = out.inputs["Surface"].links[0].from_socket
    cd = nt_.nodes.new("ShaderNodeCameraData"); mu_ = nt_.nodes.new("ShaderNodeMath"); mu_.operation = "MULTIPLY"; mu_.inputs[1].default_value = -1.0 / dist
    nt_.links.new(cd.outputs["View Distance"], mu_.inputs[0]); ex2 = nt_.nodes.new("ShaderNodeMath"); ex2.operation = "EXPONENT"; nt_.links.new(mu_.outputs[0], ex2.inputs[0])
    iv = nt_.nodes.new("ShaderNodeMath"); iv.operation = "SUBTRACT"; iv.inputs[0].default_value = 1.0; nt_.links.new(ex2.outputs[0], iv.inputs[1])
    he = nt_.nodes.new("ShaderNodeEmission"); he.inputs["Color"].default_value = (*srgb(haze_col), 1); he.inputs["Strength"].default_value = strength
    mx2 = nt_.nodes.new("ShaderNodeMixShader"); nt_.links.new(iv.outputs[0], mx2.inputs[0]); nt_.links.new(src, mx2.inputs[1]); nt_.links.new(he.outputs[0], mx2.inputs[2])
    nt_.links.new(mx2.outputs[0], out.inputs["Surface"]); return True


def sky_and_sun(scene, az_deg=15.0, el_deg=50.0, sky_strength=0.10, sun_energy=4.0, coll=None):
    """物理の空（Nishita）と太陽。向きは +X から左回りの方位・高さ。光は本物の光だけ（空と太陽）"""
    az, el = math.radians(az_deg), math.radians(el_deg)
    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    wd = bpy.data.worlds.new("Stage sky"); scene.world = wd; wd.use_nodes = True; wn = wd.node_tree; wn.nodes.clear()
    sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"; sky.sun_disc = False
    sky.sun_elevation = el; sky.sun_rotation = math.atan2(d.y, d.x) - math.pi / 2 + math.pi
    sky.altitude = 30.0; sky.air_density = 1.0; sky.dust_density = 0.9; sky.ozone_density = 1.0
    bgw = wn.nodes.new("ShaderNodeBackground"); bgw.inputs[1].default_value = sky_strength; wn.links.new(sky.outputs[0], bgw.inputs[0])
    wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(bgw.outputs[0], wo.inputs["Surface"])
    sl = bpy.data.lights.new("Sun", "SUN"); sl.energy = sun_energy; sl.color = kelvin(5600); sl.angle = math.radians(0.53)
    sun = link(bpy.data.objects.new("Sun", sl), coll); sun.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return sun, d


def render_setup(scene, engine="eevee", res=(640, 360), samples=16, exposure=0.0, sun_dir=None, world_col="#AFC3D6"):
    scene.render.resolution_x, scene.render.resolution_y = res; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if engine == "workbench":                                      # 動きの確認用：材質の基本色、太陽と同じ向きの影
        scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
        sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_shadows = True; sh.shadow_intensity = 0.55; sh.show_cavity = True; sh.cavity_type = "WORLD"
        sh.background_type = "WORLD"; scene.world.color = srgb(world_col)
        if sun_dir is not None: scene.display.light_direction = tuple(sun_dir)
        scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"
    else:
        scene.render.engine = "BLENDER_EEVEE_NEXT"; ee = scene.eevee; ee.taa_render_samples = samples; ee.use_shadows = True
        try: ee.use_raytracing = False
        except Exception: pass
        scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"; scene.view_settings.exposure = exposure
