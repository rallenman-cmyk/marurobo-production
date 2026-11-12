# ピクトグラムの主人公の見分け方の比較：保存した場面（pict_f0.blend）を開き、主人公の色・服・模様・線・形だけ変えて同じ構図で撮る
# 使い方: blender -b pict_out/pict_f0.blend --python pict_variants.py -- --out DIR [--res W H] [--samples N]
import bpy, sys, os, math, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector
import sdf, iconfig
from hbuild import srgb, NT, principled, mk_mesh, bind

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="/tmp/pv"); ap.add_argument("--res", nargs=2, type=int, default=[640, 360])
ap.add_argument("--samples", type=int, default=24)
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:]); os.makedirs(A.out, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects

# ---- 全景のカメラと光に戻す（保存時はアップの位置になっている）
CAM = dict(cx=-1.42, cy=-0.277, cz=1.0, yaw=0.522, pit=0.024, lens=25.649)
cam = sc.camera; cd = cam.data
cam.location = (CAM["cx"], CAM["cy"], CAM["cz"]); cd.lens = CAM["lens"]
D = Vector((math.cos(CAM["pit"]) * math.cos(CAM["yaw"]), math.cos(CAM["pit"]) * math.sin(CAM["yaw"]), math.sin(CAM["pit"])))
cam.rotation_euler = D.to_track_quat("-Z", "Y").to_euler()
arm = O["Hero"]; bpy.context.view_layer.update()
hc_w = arm.matrix_world @ arm.pose.bones["eye.L"].head          # 目の骨は頭の中心にある
cd.dof.focus_distance = (hc_w - cam.location).length; cd.dof.aperture_fstop = 4.0
key = O["Key"]; key.location = cam.location + Vector((-0.65, 0.25, 0.75))
key.rotation_euler = (hc_w - key.location).to_track_quat("-Z", "Y").to_euler()
for nm in ("Hero eye.L", "Hero eye.R"): O[nm].hide_render = False   # 主人公は点の目あり（決定）
sc.render.resolution_x, sc.render.resolution_y = A.res; sc.eevee.taa_render_samples = A.samples

BODY_PARTS = ["head", "hips", "leg.L", "leg.R", "foot.L", "foot.R", "hand.L", "hand.R"]
TOP_PARTS = ["top", "arm.L", "arm.R"]


def solid(hexc):
    m = bpy.data.materials.new(f"Var {hexc}"); nt = NT(m); principled(nt, base=srgb(hexc), **iconfig.PBR["pict"]); return m


def stripes(c1, c2, period=0.052):
    """しま模様：休み姿勢の高さ（rest の z）で横じま"""
    m = bpy.data.materials.new("Var stripes"); nt = NT(m); b = principled(nt, base=srgb(c2), **iconfig.PBR["pict"])
    at = nt.n("ShaderNodeAttribute", attribute_name="rest"); sp = nt.n("ShaderNodeSeparateXYZ"); nt.l(at.outputs["Vector"], sp.inputs[0])
    mu = nt.n("ShaderNodeMath", operation="MULTIPLY"); mu.inputs[1].default_value = 1.0 / period; nt.l(sp.outputs[2], mu.inputs[0])
    fr = nt.n("ShaderNodeMath", operation="FRACT"); nt.l(mu.outputs[0], fr.inputs[0])
    lt = nt.n("ShaderNodeMath", operation="LESS_THAN"); lt.inputs[1].default_value = 0.5; nt.l(fr.outputs[0], lt.inputs[0])
    mx = nt.n("ShaderNodeMix", data_type="RGBA"); nt.l(lt.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = (*srgb(c2), 1); mx.inputs[7].default_value = (*srgb(c1), 1); nt.l(mx.outputs[2], b.inputs["Base Color"])
    return m


def set_mat(parts, m):
    for p in parts:
        ob = O[f"Hero {p}"]; ob.data.materials[0] = m


# ---- アホ毛（頭のてっぺんから前へ曲がる一房）：頭の骨に付ける。ふだんは隠す
hc = np.array([0, 0.045, 1.226]); Rh = 0.140
top = hc + np.array([0, 0.010, Rh * 0.985])
pts = [top + np.array(d) for d in ((0, 0, -0.01), (0, -0.004, 0.035), (0, -0.026, 0.066), (0, -0.058, 0.078), (0, -0.082, 0.064))]
rads = [0.013, 0.011, 0.008, 0.006, 0.004]
prims = [(sdf.cone(pts[j], pts[j + 1], rads[j], rads[j + 1]), "tuft", 0.006 if j else 0.0, {"head": 1.0}) for j in range(len(pts) - 1)]
V, Q, W, bones = iconfig._part(prims, top - 0.12, top + 0.14, 0.0022, relax=2)
ahoge = mk_mesh("Hero ahoge", V, [tuple(q) for q in Q], coll=O["Hero top"].users_collection[0], mats=[O["Hero head"].data.materials[0]],
                attrs={"rest": ("FLOAT_VECTOR", V)})
bind(ahoge, arm, {"head": 1.0}, None); ahoge.data.shade_smooth(); ahoge.hide_render = True

# ---- 輪郭線（主人公だけ）
line_coll = bpy.data.collections.new("Hero line"); sc.collection.children.link(line_coll)
for p in BODY_PARTS + TOP_PARTS + ["hat"]: line_coll.objects.link(O[f"Hero {p}"])
line_coll.objects.link(ahoge)
iconfig.freestyle(sc, bpy.context.view_layer, 2.2, collection=line_coll); sc.render.use_freestyle = False

WHITE = "#F1EFEA"; NAVY = "#2D3A5A"
VARIANTS = [
    ("1_orange", dict(body="#F07C3A", cap=NAVY)),
    ("2_yellow", dict(body="#F2B82E", cap=NAVY)),
    ("3_jacket", dict(body=WHITE, top="#D64541", cap="#D64541")),
    ("4_stripes", dict(body=WHITE, stripes=(NAVY, "#F6F4EE"), cap="#F2B82E")),
    ("5_outline", dict(body=WHITE, cap="#F2B82E", outline=True)),
    ("6_ahoge", dict(body=WHITE, cap=None, ahoge=True)),
]
for name, v in VARIANTS:
    mb = solid(v["body"]); set_mat(BODY_PARTS, mb)
    if "top" in v: set_mat(TOP_PARTS, solid(v["top"]))
    elif "stripes" in v: set_mat(TOP_PARTS, stripes(*v["stripes"]))
    else: set_mat(TOP_PARTS, mb)
    hat = O["Hero hat"]; hat.hide_render = v["cap"] is None
    if v["cap"]: hat.data.materials[0] = solid(v["cap"])
    ahoge.hide_render = not v.get("ahoge", False); ahoge.data.materials[0] = mb
    sc.render.use_freestyle = bool(v.get("outline", False))
    sc.render.filepath = os.path.join(A.out, f"var_{name}.png"); bpy.ops.render.render(write_still=True)
    print("VAR", name, flush=True)
