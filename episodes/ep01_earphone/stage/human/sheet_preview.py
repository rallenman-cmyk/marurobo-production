# 作った頭と髪を、6面図と同じ正投影の6方向から陰影つきで描く（Blender）
# 使い方: blender -b --factory-startup --python sheet_preview.py -- M1 OUT.png
import bpy, bmesh, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix
from hbuild import mk_mesh, srgb, NT, principled
k, out = sys.argv[sys.argv.index("--") + 1:][:2]
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
D = np.load(os.path.join(HERE, "..", "..", "sheets", f"mesh_{k}.npz")); V, Q, Vh, Qh = D["V"], D["Q"], D["Vh"], D["Qh"]
def mat(n, c, r=0.6):
    mm = bpy.data.materials.new(n); nt = NT(mm); principled(nt, base=srgb(c), rough=r, spec=0.3); return mm
head = mk_mesh("head", V, [tuple(q) for q in Q], coll=sc.collection, mats=[mat("skin", "#E9A27A")]); head.data.shade_smooth()
hair = mk_mesh("hair", Vh, [tuple(q) for q in Qh], coll=sc.collection, mats=[mat("hair", "#262B45", 0.85)])
md = hair.modifiers.new("d", "DECIMATE"); md.ratio = min(1.0, 1400 / max(1, len(Qh))); hair.data.shade_flat()
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sun = bpy.data.lights.new("S", "SUN"); sun.energy = 3.0; so = bpy.data.objects.new("S", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(-30))
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.82, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = 8; sc.render.resolution_x, sc.render.resolution_y = 360, 420
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
tiles = []
for nm, az, el in (("front", 0, 0), ("left45", 45, 0), ("left", 90, 0), ("back", 180, 0), ("right", 270, 0), ("top", 0, 90)):
    d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    tgt = Vector((0, 0.0, 0.0)) if nm != "top" else Vector((0, 0.0, 0.0))
    cam.location = tgt + d * 2.0
    up = Vector((0, 0, 1)) if nm != "top" else Vector((0, 1, 0))
    zc = d.normalized(); xc = up.cross(zc).normalized(); yc = zc.cross(xc)
    cam.matrix_world = Matrix(((xc.x, yc.x, zc.x, cam.location.x), (xc.y, yc.y, zc.y, cam.location.y), (xc.z, yc.z, zc.z, cam.location.z), (0, 0, 0, 1)))
    sc.render.filepath = f"/tmp/_pv_{nm}.png"; bpy.ops.render.render(write_still=True); tiles.append(sc.render.filepath)
import subprocess
open(out + ".list", "w").write("\n".join(tiles))
print("TILES", out)
