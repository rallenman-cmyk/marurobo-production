# 部品の試し描き：blender -b --factory-startup --python test_kit.py -- <出力.png> [カメラ: wide|robot|top|ceil]
import os, sys
KIT_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv[sys.argv.index("--") + 1:]
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(KIT_HERE, "kit.py"), encoding="utf-8").read())
OUT = _argv[0]; VIEW = _argv[1] if len(_argv) > 1 else "wide"
restaurant(ceiling=VIEW != "top", top_view=VIEW == "top")
sp = senpai_serve((0.0, 0.3), 0)
ramen(sp["trays"][1], (0, 0, 0.01))
for k, g in sp["face"].items(): g.hide_render = (k != "happy")
maru((0.0, -0.6, 0), face_deg=180, s=0.26, hat=False, eye_glow=0.9)
seated(11, 'in', "#C0504D"); seated(11, 'out', "#4F81BD"); seated(21, 'out', "#9BBB59", kid=True); seated(10, 'in', "#E8A04D")
w = walker((-0.2, 1.6), 0, shirt="#7E57C2")
st = walker((0.3, 2.4), 180, shirt="#2B2F36", apron=True)
cams = {"wide": ((2.8, -3.0, 1.9), (0.0, 0.6, 0.7), 26), "robot": ((0.9, -1.0, 1.1), (0.0, 0.3, 0.8), 40),
        "top": ((0, 0.1, 9.5), (0, 0.1, 0), 24), "ceil": ((0.3, -0.6, 0.5), (0.0, 0.6, 2.6), 22)}
l, t, lens = cams[VIEW]
camera(l, t, lens)
render_settings(16, (640, 360))
bpy.context.scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
