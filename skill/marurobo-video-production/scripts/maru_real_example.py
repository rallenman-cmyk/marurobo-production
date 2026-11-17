# maru_real の見本：代わりの体（PC では本物）を置き、2m 歩いて 90 度回る。blender -b --factory-startup --python maru_real_example.py
import sys, bpy, math
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maru_real as MR, marumotion as mm
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=20); 
h = MR.place(loc=(0, 0, 0), heading=0, scale=1.0)
p = mm.Plan(pos=(0, 0), heading=0); p.wait(0.5); p.walk_to((0, 2.0)); p.turn_to(90); p.wait(0.5)
fr = mm.simulate(p, fps=24); print("frames", len(fr)); h.bake(fr, f0=1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (4.5, 1.0, 1.6); cam.rotation_euler = (math.radians(80), 0, math.radians(90))
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (0.6, 0.2, 0.5)
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.render.resolution_x, sc.render.resolution_y = 480, 270
import os
for f in (1, 20, 30, 40, 50, 60, 75, len(fr) - 1):
    sc.frame_set(f); sc.render.filepath = os.path.join(os.environ.get("OUT", "."), "f%03d.png") % f; bpy.ops.render.render(write_still=True)
