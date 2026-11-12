import bpy, sys, os, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
s = bpy.context.scene; O = bpy.data.objects; s.frame_set(1)
def hier(o):
    r = [o]
    for c in o.children: r += hier(c)
    return r
keep = set(hier(O["Maru cargo"])) | set(hier(O["Inside 04"]))
for o in O:
    if o not in keep and o.type != "LIGHT": o.hide_render = True
case = O["Maru cargo case"]; c = case.matrix_world.translation.copy()
b4 = [x for x in hier(O["Inside 04"]) if x.type == "MESH"]
c4 = sum((x.matrix_world.translation for x in b4), Vector()) / len(b4)
print("PARCEL maru cargo center", tuple(round(v, 2) for v in c), "inside04 center", tuple(round(v, 2) for v in c4))
for x in hier(O["Inside 04"]): print("PARCEL in04 part", x.name, x.type, tuple(round(v, 2) for v in x.matrix_world.translation), tuple(round(v, 2) for v in x.dimensions))
cam_d = bpy.data.cameras.new("c"); cam = O.new("c", cam_d); s.collection.objects.link(cam); s.camera = cam; cam_d.lens = 50
s.render.engine = "BLENDER_WORKBENCH"; s.display.shading.light = "STUDIO"; s.display.shading.color_type = "MATERIAL"
s.render.resolution_x, s.render.resolution_y = 400, 300
R = O["Maru"].matrix_world.to_3x3()
for name, d in (("front", (0, 1, 0)), ("back", (0, -1, 0)), ("left", (-1, 0, 0)), ("right", (1, 0, 0)), ("top", (0.3, -0.5, 1))):
    dv = R @ Vector(d); dv.normalize()
    cam.location = c + dv * 3.0; cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.render.filepath = os.path.join(out, "parcel_%s.png" % name); bpy.ops.render.render(write_still=True)
