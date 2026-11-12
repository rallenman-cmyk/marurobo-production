# アニメ風の目（Blender側）：白目・上の線・下の線を作り、目の骨と一緒に回る「目の座標」から黒目を描く
# まばたき・見開き・下を見る時のまぶたは、上まぶたの骨の回転（X）からシェイプキーへ（ドライバー）
import math
import numpy as np
import bpy
from mathutils import Matrix, Vector
from hbuild import srgb, NT, principled, bind, mat_simple


def _m(nt, op, a, b=None, clamp=False):
    nd = nt.n("ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): nd.inputs[i].default_value = float(x)
        else: nt.l(x, nd.inputs[i])
    return nd.outputs[0]


def _range(nt, x, a, b):
    mr = nt.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP"); mr.inputs["From Min"].default_value = a; mr.inputs["From Max"].default_value = b
    nt.l(x, mr.inputs["Value"]); return mr.outputs["Result"]


def _mix(nt, fac, c1, c2, blend="MIX"):
    mx = nt.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
    for sock, v in ((mx.inputs[0], fac), (mx.inputs[6], c1), (mx.inputs[7], c2)):
        if isinstance(v, (tuple, list)): sock.default_value = v if len(v) == 4 else (*v, 1)
        elif isinstance(v, float): sock.default_value = v
        else: nt.l(v, sock)
    return mx.outputs[2]


def eye_material(name, empty, depth, s, E, sx, cols):
    """黒目の半径 r_i（顔の上の大きさ）→ 目の中心から見た角度 ang_i。目の座標で −Y＝前、+Z＝上、+X＝人物の左"""
    r_i = cols["iris_r"] if "iris_r" in cols else 0.0098 * s * E * cols.get("iris_k", 1.0)
    ang_i = math.atan(r_i / depth)
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, rough=0.32, spec=0.35)
    tc = nt.n("ShaderNodeTexCoord"); tc.object = empty
    nv = nt.n("ShaderNodeVectorMath", operation="NORMALIZE"); nt.l(tc.outputs["Object"], nv.inputs[0])
    sp = nt.n("ShaderNodeSeparateXYZ"); nt.l(nv.outputs[0], sp.inputs[0])
    c = _m(nt, "MULTIPLY", sp.outputs[1], -1.0)
    t = _m(nt, "DIVIDE", _m(nt, "ARCCOSINE", c, clamp=False), ang_i)          # 黒目の中心0 → ふち1
    vz = _m(nt, "DIVIDE", sp.outputs[2], math.sin(ang_i))                     # 黒目の中の高さ（上+1、下−1）
    g = _range(nt, vz, 0.30, -0.95)
    iris = _mix(nt, g, srgb(cols.get("iris_top", "#1A110D")), srgb(cols.get("iris_bot", "#6A4630")))
    iris = _mix(nt, _m(nt, "MULTIPLY", _range(nt, t, 0.70, 1.0), 0.75), iris, srgb("#0E0907"))
    iris = _mix(nt, _m(nt, "MULTIPLY", _m(nt, "SUBTRACT", 1.0, _range(nt, t, 0.36, 0.46)), 0.70), iris, srgb("#080504"))
    m_ir = _m(nt, "SUBTRACT", 1.0, _range(nt, t, 0.965, 1.035))
    col = _mix(nt, m_ir, srgb(cols.get("sclera", "#F4EBE3")), iris)
    # 上まつげの下の影と、目頭・目尻の暗さ
    v = nt.n("ShaderNodeAttribute", attribute_name="eyev").outputs["Fac"]; u = nt.n("ShaderNodeAttribute", attribute_name="eyeu").outputs["Fac"]
    sh = _m(nt, "MULTIPLY", _range(nt, v, 0.05, 1.0), 0.42)
    k = _m(nt, "MULTIPLY", _range(nt, _m(nt, "ABSOLUTE", _m(nt, "SUBTRACT", _m(nt, "MULTIPLY", u, 2.0), 1.0)), 0.65, 1.0), 0.30)
    dim = _m(nt, "SUBTRACT", 1.0, _m(nt, "MAXIMUM", sh, k))
    shade = nt.n("ShaderNodeCombineColor"); [nt.l(dim, shade.inputs[j]) for j in range(3)]
    col = _mix(nt, 1.0, col, shade.outputs[0], "MULTIPLY")
    nt.l(col, b.inputs["Base Color"])
    # 目の光（黒目の右上に大きめ、左下に小さく）
    fwd = np.array([0, -1.0, 0]); up = np.array([0, 0, 1.0]); out = np.array([sx, 0, 0.0])
    def spot(du, dout, rad, gain):
        h = fwd + up * math.tan(du * ang_i) + out * math.tan(dout * ang_i); h /= np.linalg.norm(h)
        dp = nt.n("ShaderNodeVectorMath", operation="DOT_PRODUCT"); nt.l(nv.outputs[0], dp.inputs[0]); dp.inputs[1].default_value = tuple(h)
        return _m(nt, "MULTIPLY", _range(nt, dp.outputs["Value"], math.cos(rad * ang_i * 1.25), math.cos(rad * ang_i * 0.85)), gain)
    hl = _m(nt, "MAXIMUM", spot(0.42, 0.30, 0.20, 1.0), spot(-0.48, -0.30, 0.09, 0.55))
    hl = _m(nt, "MULTIPLY", hl, m_ir)
    b.inputs["Emission Color"].default_value = (1, 1, 1, 1); nt.l(_m(nt, "MULTIPLY", hl, 2.6), b.inputs["Emission Strength"])
    return m


def _keyed(ob, shapes):
    ob.shape_key_add(name="Basis")
    for nm, V in shapes.items():
        kb = ob.shape_key_add(name=nm, from_mix=False); kb.data.foreach_set("co", np.asarray(V, np.float32).ravel())


def _drive(ob, key, arm, bone, expr):
    fc = ob.data.shape_keys.key_blocks[key].driver_add("value"); d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "rx"; v.type = "TRANSFORMS"
    tg = v.targets[0]; tg.id = arm; tg.bone_target = bone; tg.transform_type = "ROT_X"; tg.transform_space = "LOCAL_SPACE"
    d.expression = expr


def build(name, cfg, arm, hc, s, P, M, new, AE, coll):
    """AE＝animeface.eye_set の結果（キャッシュから）"""
    C = cfg["colors"]; E = P.get("aeye", 1.0)
    low = mat_simple(f"{name} eye lower line", C.get("lowline", "#5A372C"), 0.7, 0.2)
    K_close = math.radians(P["lid_up"] + 12.0)
    for i, sd in enumerate(("L", "R")):
        a = AE[sd]; sx = 1 if sd == "L" else -1
        emp = bpy.data.objects.new(f"{name} eyeframe.{sd}", None); coll.objects.link(emp); emp.empty_display_size = 0.01
        emp.parent = arm; emp.parent_type = "BONE"; emp.parent_bone = "eye." + sd
        bn = arm.data.bones["eye." + sd]; Mt = bn.matrix_local @ Matrix.Translation((0, bn.length, 0))
        up = math.radians(0.0 if P.get("loft") else C.get("iris_up", 0.0))      # 黒目を上へ（アニメの目は黒目が上のまつげの線に接する）
        emp.matrix_parent_inverse = Matrix.Identity(4); emp.matrix_basis = Mt.inverted() @ Matrix.Translation(Vector(tuple(a["ec"]))) @ Matrix.Rotation(-up, 4, "X")
        Cc = dict(C)
        if P.get("loft"): Cc["iris_r"] = P["loft"]["feat"]["iris_r"]; Cc["iris_up"] = 0.0
        em = eye_material(f"{name} eye.{sd}", emp, a["depth"], s, E, sx, Cc)
        w = new("eye." + sd, a["white"]["rest"], a["white_F"], [em], attrs={"eyeu": ("FLOAT", a["u"]), "eyev": ("FLOAT", a["v"])})
        _keyed(w, {"close": a["white"]["close"], "wide": a["white"]["wide"]}); w.data.shade_smooth()
        bind(w, arm, {"head": 1.0}, None)
        l = new("lash." + sd, a["lash"]["rest"], a["lash_F"], [M["lash"]])
        _keyed(l, {"close": a["lash"]["close"], "wide": a["lash"]["wide"]}); l.data.shade_smooth()
        bind(l, arm, {"head": 1.0}, None)
        lo = new("lowline." + sd, a["low"], a["low_F"], [low]); lo.data.shade_smooth(); bind(lo, arm, {"head": 1.0}, None)
        for ob in (w, l):
            _drive(ob, "close", arm, "lid_up." + sd, f"max(0.0, -rx - 0.30) / {K_close - 0.30:.4f}")   # 下を見る程度では少しだけ下がる
            _drive(ob, "wide", arm, "lid_up." + sd, "max(0.0, rx) / 0.1047")
