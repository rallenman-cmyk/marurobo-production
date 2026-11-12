# 資料の絵を3Dに貼る材質（Blender）：頂点の休み姿勢の位置 rest から、各向きの絵の上の位置を計算して色を取り、重みで混ぜる
import os, json, math
import numpy as np
import bpy
from hbuild import NT
HERE = os.path.dirname(os.path.abspath(__file__)); SH = os.path.join(HERE, "..", "..", "sheets")
VIEWS = ["front", "left45", "left", "back", "right"]
ANG = {"front": 0.0, "left45": 45.0, "left": 90.0, "back": 180.0, "right": 270.0}


def _math(nt, op, a, b=None):
    nd = nt.n("ShaderNodeMath", operation=op)
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): nd.inputs[i].default_value = float(x)
        else: nt.l(x, nd.inputs[i])
    return nd.outputs[0]


def material(name, k, hc, expr=None, emit=0.55, rough=0.75, extra_images=None):
    """expr：表情（front と left45 の絵を、表情シートから作った絵に差し替える）"""
    sp = json.load(open(os.path.join(SH, f"spec_{k}.json"), encoding="utf-8")); S, v0 = sp["reg"]["S"], sp["reg"]["v0"]
    reg = json.load(open(os.path.join(SH, f"reg_{k}.json"), encoding="utf-8"))
    m = bpy.data.materials.new(name); nt = NT(m)
    rest = nt.n("ShaderNodeAttribute", attribute_name="rest").outputs["Vector"]
    sub = nt.n("ShaderNodeVectorMath", operation="SUBTRACT"); nt.l(rest, sub.inputs[0]); sub.inputs[1].default_value = tuple(float(x) for x in hc)
    q = sub.outputs[0]
    sep = nt.n("ShaderNodeSeparateXYZ"); nt.l(q, sep.inputs[0])
    acc = None
    for i, view in enumerate(VIEWS):
        path = os.path.join(SH, f"{k}_{view}.png")
        if expr and view in ("front", "left45"):
            p2 = os.path.join(SH, f"{k}_{view}__{expr}.png")
            if os.path.exists(p2): path = p2
        img = bpy.data.images.load(path, check_existing=True); W_, H_ = img.size
        a = math.radians(ANG[view])
        dp = nt.n("ShaderNodeVectorMath", operation="DOT_PRODUCT"); nt.l(q, dp.inputs[0]); dp.inputs[1].default_value = (math.cos(a), math.sin(a), 0.0)
        u = _math(nt, "MULTIPLY_ADD", dp.outputs["Value"], S); nd = u.node; nd.inputs[2].default_value = reg[view]
        U = _math(nt, "DIVIDE", u, float(W_))
        vpx = _math(nt, "MULTIPLY_ADD", sep.outputs[2], -S); vpx.node.inputs[2].default_value = v0
        Vv = _math(nt, "SUBTRACT", 1.0, _math(nt, "DIVIDE", vpx, float(H_)))
        cmb = nt.n("ShaderNodeCombineXYZ"); nt.l(U, cmb.inputs[0]); nt.l(Vv, cmb.inputs[1])
        tx = nt.n("ShaderNodeTexImage"); tx.image = img; tx.extension = "EXTEND"; tx.interpolation = "Linear"; nt.l(cmb.outputs[0], tx.inputs["Vector"])
        w = nt.n("ShaderNodeAttribute", attribute_name=f"pw_{i}").outputs["Fac"]
        sc = nt.n("ShaderNodeVectorMath", operation="SCALE"); nt.l(tx.outputs["Color"], sc.inputs[0]); nt.l(w, sc.inputs["Scale"])
        if acc is None: acc = sc.outputs[0]
        else:
            ad = nt.n("ShaderNodeVectorMath", operation="ADD"); nt.l(acc, ad.inputs[0]); nt.l(sc.outputs[0], ad.inputs[1]); acc = ad.outputs[0]
    o = nt.n("ShaderNodeOutputMaterial")
    if emit is None:          # 絵の色そのまま（光の影響なし）：資料との比較用
        em = nt.n("ShaderNodeEmission"); nt.l(acc, em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0; nt.l(em.outputs[0], o.inputs[0])
        return m
    bsdf = nt.n("ShaderNodeBsdfPrincipled"); nt.l(acc, bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    nt.l(acc, bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = emit
    nt.l(bsdf.outputs[0], o.inputs[0])
    return m


def attach(ob, Wt):
    """頂点ごとの重み（N×5）を属性 pw_0..pw_4 として付ける"""
    me = ob.data
    for i in range(Wt.shape[1]):
        a = me.attributes.get(f"pw_{i}") or me.attributes.new(f"pw_{i}", "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(Wt[:, i], dtype=np.float32))


def material_views(name, views, emit=0.35, rough=0.8):
    """一般の投影：views = [dict(path, ang(度), S, u0, vb)]。絵の上の位置 u = u0 + S(x cosA + y sinA)、v = vb − S z（rest 属性の座標）"""
    m = bpy.data.materials.new(name); nt = NT(m)
    rest = nt.n("ShaderNodeAttribute", attribute_name="rest").outputs["Vector"]
    sep = nt.n("ShaderNodeSeparateXYZ"); nt.l(rest, sep.inputs[0]); acc = None
    for i, vw in enumerate(views):
        img = bpy.data.images.load(vw["path"], check_existing=True); W_, H_ = img.size; a = math.radians(vw["ang"])
        dp = nt.n("ShaderNodeVectorMath", operation="DOT_PRODUCT"); nt.l(rest, dp.inputs[0]); dp.inputs[1].default_value = (math.cos(a), math.sin(a), 0.0)
        u = _math(nt, "MULTIPLY_ADD", dp.outputs["Value"], vw["S"]); u.node.inputs[2].default_value = vw["u0"]
        U = _math(nt, "DIVIDE", u, float(W_))
        vpx = _math(nt, "MULTIPLY_ADD", sep.outputs[2], -vw["S"]); vpx.node.inputs[2].default_value = vw["vb"]
        Vv = _math(nt, "SUBTRACT", 1.0, _math(nt, "DIVIDE", vpx, float(H_)))
        cmb = nt.n("ShaderNodeCombineXYZ"); nt.l(U, cmb.inputs[0]); nt.l(Vv, cmb.inputs[1])
        tx = nt.n("ShaderNodeTexImage"); tx.image = img; tx.extension = "EXTEND"; tx.interpolation = "Linear"; nt.l(cmb.outputs[0], tx.inputs["Vector"])
        w = nt.n("ShaderNodeAttribute", attribute_name=f"pw_{i}").outputs["Fac"]
        sc = nt.n("ShaderNodeVectorMath", operation="SCALE"); nt.l(tx.outputs["Color"], sc.inputs[0]); nt.l(w, sc.inputs["Scale"])
        if acc is None: acc = sc.outputs[0]
        else:
            ad = nt.n("ShaderNodeVectorMath", operation="ADD"); nt.l(acc, ad.inputs[0]); nt.l(sc.outputs[0], ad.inputs[1]); acc = ad.outputs[0]
    o = nt.n("ShaderNodeOutputMaterial")
    bsdf = nt.n("ShaderNodeBsdfPrincipled"); nt.l(acc, bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    nt.l(acc, bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = emit
    nt.l(bsdf.outputs[0], o.inputs[0])
    return m
