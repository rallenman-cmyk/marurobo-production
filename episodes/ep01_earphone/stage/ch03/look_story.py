# Codex版 story.blend の舞台を上から・横から見る（どこに何があるか）
import bpy, sys, os, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
s = bpy.context.scene; O = bpy.data.objects
s.frame_set(int(sys.argv[sys.argv.index("--") + 2]) if len(sys.argv) > sys.argv.index("--") + 2 else 1)
for o in list(O):
    if o.name.startswith(("Earbud cutaway", "Neighbor")):
        def hide(x):
            x.hide_render = True
            for c in x.children: hide(c)
        hide(o)
cam_d = bpy.data.cameras.new("look"); cam = O.new("look", cam_d); s.collection.objects.link(cam); s.camera = cam
cam_d.lens = 24; cam_d.clip_end = 500
s.render.engine = "BLENDER_EEVEE_NEXT"; s.eevee.taa_render_samples = 8
s.render.resolution_x, s.render.resolution_y = 640, 360
for name, loc, tgt in (("top", (-4, -22, 30), (-4, 4, 0)), ("side", (-26, 3, 5), (-3, 3, 4)), ("robot_view", (-12, -14, 1.8), (-2, 9, 6))):
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    s.render.filepath = os.path.join(out, "codex_%s.png" % name); bpy.ops.render.render(write_still=True)
    print("LOOK", name)
