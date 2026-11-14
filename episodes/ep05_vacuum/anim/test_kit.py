# 部品の見た目の試し：blender -b --factory-startup --python test_kit.py -- <out.png> <view>
import os, sys
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:]
OUTP, VIEW = argv[0], argv[1]
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
room(front_wall=(VIEW == "top"), top_view=(VIEW == "top"))
A = senpai_lidar((0.3, 0.6, 0), face=20)
B = senpai_camera((-0.5, 0.2, 0), face=-30)
maru((0.0, -0.2, 0), face_deg=-15, s=0.26, hat=False, eye_glow=0.8)
pts = [(x, y, 0.0) for x, y in plan.map_points()]
point_cloud("map", pts)
if VIEW == "top":
    camera((0, -0.3, 9.0), (0, 0.0, 0), lens=30)
elif VIEW == "low":
    camera((0.9, -1.0, 0.35), (0.1, 0.5, 0.12), lens=32); focus_on((0.3, 0.6, 0.1), 4)
else:
    camera((1.2, -4.6, 2.4), (-0.2, 0.6, 0.3), lens=26)
render_settings(24, (960, 540))
bpy.context.scene.frame_set(10)
bpy.context.scene.render.filepath = OUTP
bpy.ops.render.render(write_still=True)
