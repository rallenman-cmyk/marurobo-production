# まるロボの切り抜き（背景が透明な PNG）。2D の図の場面に、まるロボを当事者として置くため（2026-11-14 ユーザー「チープ感」）
# blender -b --factory-startup --python cutout.py -- <出力フォルダ> [samples] [--tex <絵>]
#   ポーズ：front（正面）・q（首をかしげる）・up（見上げる）・joy（跳ねて目が光る）・side（横を向く）・down（しょんぼり）
import os, sys, math, bpy
_ANIM_HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "anim")
A = sys.argv[sys.argv.index("--") + 1:]
OUTD = A[0]; SAMP = int(A[1]) if len(A) > 1 and A[1].isdigit() else 32
TEX = A[A.index("--tex") + 1] if "--tex" in A else os.path.join(_ANIM_HERE, "..", "storyboard", "tex")
ARGS = []
exec(open(os.path.join(_ANIM_HERE, "common.py"), encoding="utf-8").read())
os.makedirs(OUTD, exist_ok=True)
POSES = dict(front=dict(face=0), q=dict(face=-12, tilt=16), up=dict(face=-8, look=14),
             joy=dict(face=0, jump=0.12, glow=2.2), side=dict(face=-55), down=dict(face=-5, look=-12, glow=0.25))
sc = bpy.context.scene
world("#DDE8F0", 0.6)
root = maru((0, 0, 0), hat=False); M = Maru(root)
area((-2.2, -3.0, 3.2), (0, 0, 0.6), 900, 3.0)
area((2.6, -1.5, 1.8), (0, 0, 0.6), 350, 2.0, "#CFF4EF")
area((0, 3.0, 2.5), (0, 0, 0.8), 600, 2.0)
camera((0, -4.2, 1.15), (0, 0, 0.62), 50)
sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMP; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x = sc.render.resolution_y = 700
sc.render.film_transparent = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
B = M.lens.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]; G0 = B.default_value
for name, kw in POSES.items():
    root.rotation_euler[2] = R(kw.get("face", 0))
    M.body.rotation_euler[0] = R(-kw.get("look", 0)); M.body.rotation_euler[1] = R(kw.get("tilt", 0))
    M.body.location.z = M.z0 + kw.get("jump", 0); B.default_value = kw.get("glow", G0)
    sc.render.filepath = os.path.join(OUTD, "maru_%s.png" % name)
    bpy.ops.render.render(write_still=True)
print("CUTDONE")
