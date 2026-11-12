# Blender側：網目・材質・骨格を作る
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix


def srgb(hexstr):
    h = hexstr.lstrip("#"); c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mk_mesh(name, V, F, coll=None, smooth=True, attrs=None, mat_idx=None, mats=None):
    me = bpy.data.meshes.new(name)
    V = np.asarray(V, float)
    F = [tuple(int(i) for i in f) for f in F] if not isinstance(F, np.ndarray) else F.astype(int).tolist()
    me.from_pydata(V.tolist(), [], F)
    me.update()
    if smooth: me.shade_smooth()
    for nm, (kind, arr) in (attrs or {}).items():
        a = me.attributes.new(nm, kind, "POINT"); arr = np.asarray(arr, np.float32)
        a.data.foreach_set("vector" if kind == "FLOAT_VECTOR" else "value", arr.ravel())
    for m in (mats or []): me.materials.append(m)
    if mat_idx is not None:
        me.polygons.foreach_set("material_index", np.asarray(mat_idx, np.int32))
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


# ------------------------------------------------------------ 材質
class NT:
    def __init__(self, mat):
        mat.use_nodes = True; self.t = mat.node_tree; self.t.nodes.clear(); self.m = mat
    def n(self, kind, **kw):
        nd = self.t.nodes.new(kind)
        for k, v in kw.items():
            if k.startswith("i_"):
                key = k[2:].replace("_", " ")
                nd.inputs[key].default_value = v
            else:
                setattr(nd, k, v)
        return nd
    def l(self, a, b): self.t.links.new(a, b)


def principled(nt, **kw):
    b = nt.n("ShaderNodeBsdfPrincipled")
    names = {"base": "Base Color", "rough": "Roughness", "spec": "Specular IOR Level", "sss": "Subsurface Weight",
             "sss_r": "Subsurface Radius", "sss_s": "Subsurface Scale", "sheen": "Sheen Weight", "sheen_r": "Sheen Roughness",
             "coat": "Coat Weight", "coat_r": "Coat Roughness", "emit": "Emission Color", "emit_s": "Emission Strength", "metal": "Metallic"}
    for k, v in kw.items():
        val = v if not isinstance(v, tuple) or len(v) != 3 or k in ("sss_r",) else (*v, 1.0)
        if k == "sss_r": val = v
        b.inputs[names[k]].default_value = val
    o = nt.n("ShaderNodeOutputMaterial"); nt.l(b.outputs[0], o.inputs[0])
    return b


def mat_skin(name, base_hex, scale=1.0, blush_hex="#D9826E"):
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, rough=0.46, spec=0.38, sss=0.32, sss_r=(1.0, 0.36, 0.19), sss_s=0.0035 * scale)
    at = nt.n("ShaderNodeAttribute", attribute_name="blush")
    mix = nt.n("ShaderNodeMix", data_type="RGBA"); mix.inputs[6].default_value = (*srgb(base_hex), 1); mix.inputs[7].default_value = (*srgb(blush_hex), 1)
    nt.l(at.outputs["Fac"], mix.inputs[0]); nt.l(mix.outputs[2], b.inputs["Base Color"])
    # 細かい肌のむら（ごく弱い凹凸）
    tc = nt.n("ShaderNodeAttribute", attribute_name="rest")
    nz = nt.n("ShaderNodeTexNoise", i_Scale=900.0 / max(scale, 1e-3), i_Detail=4.0)
    nt.l(tc.outputs["Vector"], nz.inputs["Vector"])
    bp = nt.n("ShaderNodeBump", i_Strength=0.06, i_Distance=0.0004 * scale)
    nt.l(nz.outputs["Fac"], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
    return m


def mat_simple(name, hexc, rough=0.5, spec=0.5, sheen=0.0, coat=0.0):
    m = bpy.data.materials.new(name); nt = NT(m)
    principled(nt, base=srgb(hexc), rough=rough, spec=spec, sheen=sheen, coat=coat)
    return m


def mat_hair(name, hexc, hc, HP, scale=1.0):
    """髪：毛の流れ（つむじからの角度）に沿った細い筋。角度は画素ごとに計算（継ぎ目が出ない）"""
    import hgen
    cr, e1, e2 = hgen.hair_frame(HP)
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, base=srgb(hexc), rough=0.56, spec=0.36, sheen=0.35, sheen_r=0.4)
    tc = nt.n("ShaderNodeAttribute", attribute_name="rest")
    sub = nt.n("ShaderNodeVectorMath", operation="SUBTRACT"); sub.inputs[1].default_value = tuple(float(x) for x in hc)
    nt.l(tc.outputs["Vector"], sub.inputs[0])
    nrm = nt.n("ShaderNodeVectorMath", operation="NORMALIZE"); nt.l(sub.outputs[0], nrm.inputs[0])
    dots = []
    for v in (e1, e2, cr):
        d = nt.n("ShaderNodeVectorMath", operation="DOT_PRODUCT"); d.inputs[1].default_value = tuple(float(x) for x in v)
        nt.l(nrm.outputs[0], d.inputs[0]); dots.append(d)
    at2 = nt.n("ShaderNodeMath", operation="ARCTAN2"); nt.l(dots[1].outputs["Value"], at2.inputs[0]); nt.l(dots[0].outputs["Value"], at2.inputs[1])
    ac = nt.n("ShaderNodeMath", operation="ARCCOSINE", use_clamp=True); nt.l(dots[2].outputs["Value"], ac.inputs[0])
    sw = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); sw.inputs[1].default_value = HP["swirl"]
    nt.l(ac.outputs[0], sw.inputs[0]); nt.l(at2.outputs[0], sw.inputs[2])
    mul = nt.n("ShaderNodeMath", operation="MULTIPLY"); mul.inputs[1].default_value = 90.0
    nt.l(sw.outputs[0], mul.inputs[0])
    sn = nt.n("ShaderNodeMath", operation="SINE"); nt.l(mul.outputs[0], sn.inputs[0])
    nz = nt.n("ShaderNodeTexNoise", i_Scale=160.0 / max(scale, 1e-3), i_Detail=3.0)
    nt.l(tc.outputs["Vector"], nz.inputs["Vector"])
    ad = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); ad.inputs[1].default_value = 0.5
    nt.l(nz.outputs["Fac"], ad.inputs[0]); nt.l(sn.outputs[0], ad.inputs[2])
    bp = nt.n("ShaderNodeBump", i_Strength=0.22, i_Distance=0.0005 * scale)
    nt.l(ad.outputs[0], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
    cm = nt.n("ShaderNodeMix", data_type="RGBA"); cm.inputs[6].default_value = (*[c * 0.75 for c in srgb(hexc)], 1); cm.inputs[7].default_value = (*[min(1, c * 1.25) for c in srgb(hexc)], 1)
    nt.l(nz.outputs["Fac"], cm.inputs[0]); nt.l(cm.outputs[2], b.inputs["Base Color"])
    return m


def mat_eye(name, iris_hex="#5A3A22", iris_hex2="#8A6238"):
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, rough=0.05, spec=0.75, coat=0.0)
    at = nt.n("ShaderNodeAttribute", attribute_name="dir")
    sp = nt.n("ShaderNodeSeparateXYZ"); nt.l(at.outputs["Vector"], sp.inputs[0])
    neg = nt.n("ShaderNodeMath", operation="MULTIPLY"); neg.inputs[1].default_value = -1.0; nt.l(sp.outputs[1], neg.inputs[0])
    cr = nt.n("ShaderNodeValToRGB"); el = cr.color_ramp.elements
    el[0].position = 0.0; el[0].color = (*srgb("#E7DCD6"), 1)
    el[1].position = 0.80; el[1].color = (*srgb("#F2EEEA"), 1)
    for pos, hx in ((0.855, "#E9E4E0"), (0.866, "#1E140E"), (0.878, iris_hex), (0.93, iris_hex2), (0.966, iris_hex), (0.972, "#050404")):
        e = el.new(pos); e.color = (*srgb(hx), 1)
    nt.l(neg.outputs[0], cr.inputs[0]); nt.l(cr.outputs[0], b.inputs["Base Color"])
    return m


def mat_emit(name, rgb, s):
    m = bpy.data.materials.new(name); nt = NT(m)
    e = nt.n("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = s
    o = nt.n("ShaderNodeOutputMaterial"); nt.l(e.outputs[0], o.inputs[0]); return m


def mat_knit(name, hexc, scale=1.0, rib=False):
    """ニット：縦の編み目（リブ）＋細かい毛羽"""
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, base=srgb(hexc), rough=0.86, spec=0.25, sheen=0.7, sheen_r=0.45)
    tc = nt.n("ShaderNodeAttribute", attribute_name="rest")
    wv = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", wave_profile="SIN",
              i_Scale=(110.0 if rib else 190.0) / max(scale, 1e-3), i_Distortion=0.0)
    wv2 = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z", wave_profile="SAW",
               i_Scale=230.0 / max(scale, 1e-3), i_Distortion=0.0)
    nt.l(tc.outputs["Vector"], wv.inputs["Vector"]); nt.l(tc.outputs["Vector"], wv2.inputs["Vector"])
    wv3 = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", wave_profile="SIN",
               i_Scale=(110.0 if rib else 190.0) / max(scale, 1e-3), i_Distortion=0.0)
    nt.l(tc.outputs["Vector"], wv3.inputs["Vector"])
    mx = nt.n("ShaderNodeMath", operation="MAXIMUM"); nt.l(wv.outputs["Fac"], mx.inputs[0]); nt.l(wv3.outputs["Fac"], mx.inputs[1])
    mul = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); mul.inputs[1].default_value = 0.0 if rib else 0.35
    nt.l(wv2.outputs["Fac"], mul.inputs[0]); nt.l(mx.outputs[0], mul.inputs[2])
    nz = nt.n("ShaderNodeTexNoise", i_Scale=700.0 / max(scale, 1e-3), i_Detail=2.0)
    nt.l(tc.outputs["Vector"], nz.inputs["Vector"])
    ad = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); ad.inputs[1].default_value = 0.25
    nt.l(nz.outputs["Fac"], ad.inputs[0]); nt.l(mul.outputs[0], ad.inputs[2])
    bp = nt.n("ShaderNodeBump", i_Strength=0.45 if rib else 0.30, i_Distance=0.0012 * scale)
    nt.l(ad.outputs[0], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
    # 編み目の影で色に少し濃淡
    cm = nt.n("ShaderNodeMix", data_type="RGBA"); cm.inputs[6].default_value = (*[c * 0.72 for c in srgb(hexc)], 1); cm.inputs[7].default_value = (*srgb(hexc), 1)
    nt.l(ad.outputs[0], cm.inputs[0]); nt.l(cm.outputs[2], b.inputs["Base Color"])
    return m


def mat_twill(name, hexc, scale=1.0):
    """ズボン：斜めの綾織り"""
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, base=srgb(hexc), rough=0.78, spec=0.3, sheen=0.3, sheen_r=0.5)
    tc = nt.n("ShaderNodeAttribute", attribute_name="rest")
    mp = nt.n("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(35), 0)
    nt.l(tc.outputs["Vector"], mp.inputs["Vector"])
    wv = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", i_Scale=420.0 / max(scale, 1e-3))
    nt.l(mp.outputs[0], wv.inputs["Vector"])
    nz = nt.n("ShaderNodeTexNoise", i_Scale=60.0 / max(scale, 1e-3), i_Detail=3.0)
    nt.l(tc.outputs["Vector"], nz.inputs["Vector"])
    ad = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); ad.inputs[1].default_value = 0.5
    nt.l(nz.outputs["Fac"], ad.inputs[0]); nt.l(wv.outputs["Fac"], ad.inputs[2])
    bp = nt.n("ShaderNodeBump", i_Strength=0.18, i_Distance=0.0008 * scale)
    nt.l(ad.outputs[0], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
    cm = nt.n("ShaderNodeMix", data_type="RGBA"); cm.inputs[6].default_value = (*[c * 0.8 for c in srgb(hexc)], 1); cm.inputs[7].default_value = (*[min(1, c * 1.15) for c in srgb(hexc)], 1)
    nt.l(nz.outputs["Fac"], cm.inputs[0]); nt.l(cm.outputs[2], b.inputs["Base Color"])
    return m


# ------------------------------------------------------------ 骨格
def build_armature(name, bones, coll=None):
    """bones: list of dict(name, head, tail, parent, z(roll基準ベクトル), deform)"""
    ad = bpy.data.armatures.new(name); ob = bpy.data.objects.new(name, ad)
    (coll or bpy.context.scene.collection).objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for b in bones:
        e = ad.edit_bones.new(b["name"]); e.head = Vector(b["head"]); e.tail = Vector(b["tail"])
        e.align_roll(Vector(b.get("z", (0, -1, 0))))
        e.use_deform = b.get("deform", True)
        eb[b["name"]] = e
    for b in bones:
        if b.get("parent"): eb[b["name"]].parent = eb[b["parent"]]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones: pb.rotation_mode = "QUATERNION"
    return ob


def bind(ob, arm, weights, bone_names, dq=True):
    """weights: (N, B) 配列 or {bone: 1.0}（全体を1本の骨に）"""
    ob.parent = arm; ob.matrix_parent_inverse = Matrix.Identity(4)
    if isinstance(weights, dict):
        for b, w in weights.items():
            vg = ob.vertex_groups.new(name=b); vg.add(list(range(len(ob.data.vertices))), w, "REPLACE")
    else:
        W = np.asarray(weights)
        for j, b in enumerate(bone_names):
            col = W[:, j]; nz = np.nonzero(col > 0.002)[0]
            if len(nz) == 0: continue
            vg = ob.vertex_groups.new(name=b)
            # 同じ重みごとにまとめて登録（速くするため 1/200 刻みに丸める）
            q = np.round(col[nz] * 200).astype(int)
            for val in np.unique(q):
                ids = nz[q == val]
                vg.add(ids.tolist(), float(val) / 200.0, "REPLACE")
    md = ob.modifiers.new("Armature", "ARMATURE"); md.object = arm; md.use_deform_preserve_volume = dq
    return md


def add_subsurf(ob, render_levels=1, view_levels=0):
    md = ob.modifiers.new("Subdivision", "SUBSURF"); md.levels = view_levels; md.render_levels = render_levels
    return md
