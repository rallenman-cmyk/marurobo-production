# 人物を1人組み立てる：形（キャッシュ付き）→ 骨格 → 重み → 材質（全員で共有、色は人物ごとの属性）
import os, json, hashlib, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
import hgen, hbuild, chunkhair
from hbuild import srgb, NT, principled, mk_mesh, bind, add_subsurf

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE, exist_ok=True)

QUALITY = {"hero": dict(head=0.0022, body=0.0055, hand=0.0013, shoe=0.0028, bud=0.0006, sub=1),
           "look": dict(head=0.0024, body=0.0065, hand=0.0015, shoe=0.0032, bud=0.0007, sub=1),
           "mid": dict(head=0.0030, body=0.0072, hand=0.0017, shoe=0.0035, bud=0.0008, sub=0),
           "far": dict(head=0.0040, body=0.0095, hand=0.0024, shoe=0.0045, bud=0.0010, sub=0)}


def _key(*objs):
    return hashlib.md5(json.dumps(objs, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _cached(name, key, fn):
    p = os.path.join(CACHE, f"{name}_{key}.npz")
    if os.path.exists(p):
        d = np.load(p, allow_pickle=True); return {k: d[k] for k in d.files}
    out = fn(); np.savez(p, **out); return out


# ------------------------------------------------------------ 共有の材質（色は物体の属性から）
def _objattr(nt, name, kind="Color"):
    a = nt.n("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name=name); return a.outputs[kind]


def _smooth(nt, x, a, b):
    mr = nt.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP"); mr.inputs["From Min"].default_value = a; mr.inputs["From Max"].default_value = b
    nt.l(x, mr.inputs["Value"]); return mr.outputs["Result"]


def _mix(nt, fac, c1, c2):
    mx = nt.n("ShaderNodeMix", data_type="RGBA")
    for sock, v in ((mx.inputs[0], fac), (mx.inputs[6], c1), (mx.inputs[7], c2)):
        if isinstance(v, (tuple, list)): sock.default_value = v if len(v) == 4 else (*v, 1)
        elif isinstance(v, float): sock.default_value = v
        else: nt.l(v, sock)
    return mx.outputs[2]


def _scale_color(nt, c, k):
    m = nt.n("ShaderNodeVectorMath", operation="SCALE"); m.inputs["Scale"].default_value = k; nt.l(c, m.inputs[0]); return m.outputs[0]


def _bump(nt, h, strength, dist, b):
    bp = nt.n("ShaderNodeBump", i_Strength=strength, i_Distance=dist); nt.l(h, bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])


def _rest(nt): return nt.n("ShaderNodeAttribute", attribute_name="rest").outputs["Vector"]


_MATS = {}
# 作風ごとの材質（real＝今の版、soft＝ふんわり、film＝くっきり、toy＝おもちゃ）
STYLE_MAT = {
    "real": dict(skin_r=0.46, skin_sp=0.38, sss=0.32, skin_bump=0.05, knit_bump=0.16, rib_bump=0.35, knit_wave=0.35, knit_r=0.86, knit_sh=0.7,
                 pants_bump=0.18, hair_r=0.56, hair_bump=0.22, hair_sp=0.36, coat=0.0, cloth_coat=0.0, eye_r=0.05),
    "soft": dict(skin_r=0.60, skin_sp=0.28, sss=0.22, skin_bump=0.0, knit_bump=0.05, rib_bump=0.16, knit_wave=0.20, knit_r=0.92, knit_sh=0.9,
                 pants_bump=0.04, hair_r=0.62, hair_bump=0.07, hair_sp=0.28, coat=0.0, cloth_coat=0.0, eye_r=0.03),
    "film": dict(skin_r=0.44, skin_sp=0.42, sss=0.30, skin_bump=0.0, knit_bump=0.09, rib_bump=0.25, knit_wave=0.30, knit_r=0.84, knit_sh=0.6,
                 pants_bump=0.09, hair_r=0.46, hair_bump=0.14, hair_sp=0.42, coat=0.0, cloth_coat=0.0, eye_r=0.03),
    "facet": dict(skin_r=0.55, skin_sp=0.30, sss=0.05, skin_bump=0.0, knit_bump=0.0, rib_bump=0.0, knit_wave=0.0, knit_r=0.80, knit_sh=0.08,
                  pants_bump=0.0, hair_r=0.70, hair_bump=0.0, hair_sp=0.25, coat=0.0, cloth_coat=0.0, eye_r=0.04),
    "clay": dict(skin_r=0.62, skin_sp=0.30, sss=0.0, skin_bump=0.0, knit_bump=0.06, rib_bump=0.30, knit_wave=0.0, knit_r=0.92, knit_sh=0.7,
                 pants_bump=0.05, hair_r=0.88, hair_bump=0.0, hair_sp=0.22, coat=0.0, cloth_coat=0.0, eye_r=0.22),
    "toy": dict(skin_r=0.28, skin_sp=0.50, sss=0.06, skin_bump=0.0, knit_bump=0.0, rib_bump=0.10, knit_wave=0.0, knit_r=0.40, knit_sh=0.0,
                pants_bump=0.0, hair_r=0.22, hair_bump=0.0, hair_sp=0.55, coat=0.35, cloth_coat=0.25, eye_r=0.02),
}


def _m(nt, op, a, b=None, clamp=False):
    nd = nt.n("ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): nd.inputs[i].default_value = float(x)
        else: nt.l(x, nd.inputs[i])
    return nd.outputs[0]


def _edge(nt, c, center, sharp):
    """c が center を越えるとなめらかに 0→1（幅 1/sharp）"""
    x = _m(nt, "SUBTRACT", c, center); x = _m(nt, "MULTIPLY", x, float(sharp)); x = _m(nt, "ADD", x, 0.5, clamp=True)
    mr = nt.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP"); nt.l(x, mr.inputs["Value"]); return mr.outputs["Result"]


def shared_mats(S=1.0, style="real"):
    key = (round(S, 4), style)
    if key in _MATS: return _MATS[key]
    st = STYLE_MAT[style]; tag = "" if style == "real" else f" {style}"
    M = {}
    # 肌：内部散乱（光が少し透けて赤みが出る）。頬・鼻・耳・唇は血色
    m = bpy.data.materials.new("H Skin" + tag); nt = NT(m)
    b = principled(nt, rough=st["skin_r"], spec=st["skin_sp"], sss=st["sss"], sss_r=(1.0, 0.36, 0.19), sss_s=0.0035 * S, coat=st["coat"], coat_r=0.3)
    base = _objattr(nt, "skin"); blush = nt.n("ShaderNodeAttribute", attribute_name="blush").outputs["Fac"]
    red = nt.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); red.inputs[0].default_value = 1.0
    nt.l(base, red.inputs[6]); red.inputs[7].default_value = (1.0, 0.62, 0.58, 1)
    nt.l(_mix(nt, blush, base, red.outputs[2]), b.inputs["Base Color"])
    nz = nt.n("ShaderNodeTexNoise", i_Scale=900.0, i_Detail=4.0); nt.l(_rest(nt), nz.inputs["Vector"])
    if st["skin_bump"] > 0: _bump(nt, nz.outputs["Fac"], st["skin_bump"], 0.0004 * S, b)
    M["skin"] = m
    # 髪：毛の流れ（つむじから渦を巻く角度）に沿った筋
    m = bpy.data.materials.new("H Hair" + tag); nt = NT(m)
    b = principled(nt, rough=st["hair_r"], spec=st["hair_sp"], sheen=0.35, sheen_r=0.4, coat=st["coat"], coat_r=0.2)
    sub = nt.n("ShaderNodeVectorMath", operation="SUBTRACT"); nt.l(_rest(nt), sub.inputs[0]); nt.l(_objattr(nt, "h_c", "Vector"), sub.inputs[1])
    nrm = nt.n("ShaderNodeVectorMath", operation="NORMALIZE"); nt.l(sub.outputs[0], nrm.inputs[0])
    dots = []
    for nmv in ("h_e1", "h_e2", "h_cr"):
        d = nt.n("ShaderNodeVectorMath", operation="DOT_PRODUCT"); nt.l(nrm.outputs[0], d.inputs[0]); nt.l(_objattr(nt, nmv, "Vector"), d.inputs[1]); dots.append(d)
    at2 = nt.n("ShaderNodeMath", operation="ARCTAN2"); nt.l(dots[1].outputs["Value"], at2.inputs[0]); nt.l(dots[0].outputs["Value"], at2.inputs[1])
    ac = nt.n("ShaderNodeMath", operation="ARCCOSINE", use_clamp=True); nt.l(dots[2].outputs["Value"], ac.inputs[0])
    sw = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); nt.l(ac.outputs[0], sw.inputs[0]); nt.l(_objattr(nt, "h_swirl", "Fac"), sw.inputs[1]); nt.l(at2.outputs[0], sw.inputs[2])
    mul = nt.n("ShaderNodeMath", operation="MULTIPLY"); mul.inputs[1].default_value = 90.0; nt.l(sw.outputs[0], mul.inputs[0])
    sn = nt.n("ShaderNodeMath", operation="SINE"); nt.l(mul.outputs[0], sn.inputs[0])
    nz = nt.n("ShaderNodeTexNoise", i_Scale=160.0, i_Detail=3.0); nt.l(_rest(nt), nz.inputs["Vector"])
    ad = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); ad.inputs[1].default_value = 0.5; nt.l(nz.outputs["Fac"], ad.inputs[0]); nt.l(sn.outputs[0], ad.inputs[2])
    if st["hair_bump"] > 0: _bump(nt, ad.outputs[0], st["hair_bump"], 0.0005 * S, b)
    hc = _objattr(nt, "hair_col")
    nt.l(_mix(nt, nz.outputs["Fac"], _scale_color(nt, hc, 0.75), _scale_color(nt, hc, 1.25)), b.inputs["Base Color"])
    M["hair"] = m
    # 眉：髪の色を少し明るく
    m = bpy.data.materials.new("H Brow" + tag); nt = NT(m); b = principled(nt, rough=0.75, spec=0.3)
    nt.l(_scale_color(nt, _objattr(nt, "hair_col"), 1.15), b.inputs["Base Color"]); M["brow"] = m
    # 目：白目→虹彩の縁（暗い輪）→虹彩（外→内のグラデーション）→瞳孔。つやが強い（映り込み）
    m = bpy.data.materials.new("H Eye" + tag); nt = NT(m); b = principled(nt, rough=st["eye_r"], spec=0.8)
    sp = nt.n("ShaderNodeSeparateXYZ"); nt.l(nt.n("ShaderNodeAttribute", attribute_name="dir").outputs["Vector"], sp.inputs[0])
    c = _m(nt, "MULTIPLY", sp.outputs[1], -1.0)
    ic = _objattr(nt, "iris_c", "Fac"); pc = _objattr(nt, "pupil_c", "Fac")
    sclera = _mix(nt, _smooth(nt, c, 0.2, 0.8), srgb("#DED2CE"), srgb("#F6F4F2"))
    t_ir = _m(nt, "DIVIDE", _m(nt, "SUBTRACT", c, ic), _m(nt, "SUBTRACT", pc, ic)); t_ir = _m(nt, "ADD", t_ir, 0.0, clamp=True)
    iris = _mix(nt, t_ir, _objattr(nt, "iris1"), _objattr(nt, "iris2"))
    m_ir = _edge(nt, c, ic, 110.0)
    col = _mix(nt, m_ir, sclera, iris)
    ring = _m(nt, "MULTIPLY", m_ir, _m(nt, "SUBTRACT", 1.0, _edge(nt, c, _m(nt, "ADD", ic, 0.022), 60.0)))
    col = _mix(nt, _m(nt, "MULTIPLY", ring, 0.85), col, srgb("#140E0A"))
    col = _mix(nt, _edge(nt, c, pc, 170.0), col, srgb("#040303"))
    nt.l(col, b.inputs["Base Color"]); M["eye"] = m
    # ニット（胴・袖）とリブ（裾・袖口・襟）
    for key2, rib in (("knit", False), ("rib", True)):
        m = bpy.data.materials.new("H " + key2 + tag); nt = NT(m)
        b = principled(nt, rough=st["knit_r"], spec=0.25 if style != "toy" else 0.45, sheen=st["knit_sh"], sheen_r=0.45, coat=st["cloth_coat"], coat_r=0.3)
        r = _rest(nt)
        wv = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", wave_profile="SIN", i_Scale=(110.0 if rib else 190.0)); nt.l(r, wv.inputs["Vector"])
        wv3 = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", wave_profile="SIN", i_Scale=(110.0 if rib else 190.0)); nt.l(r, wv3.inputs["Vector"])
        wv2 = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z", wave_profile="SAW", i_Scale=230.0); nt.l(r, wv2.inputs["Vector"])
        mx = nt.n("ShaderNodeMath", operation="MAXIMUM"); nt.l(wv.outputs["Fac"], mx.inputs[0]); nt.l(wv3.outputs["Fac"], mx.inputs[1])
        mu = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); mu.inputs[1].default_value = 0.0 if rib else st["knit_wave"]; nt.l(wv2.outputs["Fac"], mu.inputs[0]); nt.l(mx.outputs[0], mu.inputs[2])
        nz = nt.n("ShaderNodeTexNoise", i_Scale=700.0, i_Detail=2.0); nt.l(r, nz.inputs["Vector"])
        ad = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); ad.inputs[1].default_value = 0.08; nt.l(nz.outputs["Fac"], ad.inputs[0]); nt.l(mu.outputs[0], ad.inputs[2])
        if (st["rib_bump"] if rib else st["knit_bump"]) > 0: _bump(nt, ad.outputs[0], st["rib_bump"] if rib else st["knit_bump"], 0.0010 * S, b)
        tc = _objattr(nt, "top_col")
        nt.l(_mix(nt, ad.outputs[0], _scale_color(nt, tc, 0.72), tc), b.inputs["Base Color"])
        M[key2] = m
    # ズボン（綾織り）
    m = bpy.data.materials.new("H Pants" + tag); nt = NT(m); b = principled(nt, rough=0.78 if style != "toy" else 0.42, spec=0.3, sheen=0.3, sheen_r=0.5, coat=st["cloth_coat"], coat_r=0.3)
    mp = nt.n("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(35), 0); nt.l(_rest(nt), mp.inputs["Vector"])
    wv = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", i_Scale=420.0); nt.l(mp.outputs[0], wv.inputs["Vector"])
    nz = nt.n("ShaderNodeTexNoise", i_Scale=60.0, i_Detail=3.0); nt.l(_rest(nt), nz.inputs["Vector"])
    ad = nt.n("ShaderNodeMath", operation="MULTIPLY_ADD"); ad.inputs[1].default_value = 0.5; nt.l(nz.outputs["Fac"], ad.inputs[0]); nt.l(wv.outputs["Fac"], ad.inputs[2])
    if st["pants_bump"] > 0: _bump(nt, ad.outputs[0], st["pants_bump"], 0.0008 * S, b)
    pc = _objattr(nt, "pants_col"); nt.l(_mix(nt, nz.outputs["Fac"], _scale_color(nt, pc, 0.8), _scale_color(nt, pc, 1.15)), b.inputs["Base Color"])
    M["pants"] = m
    # 靴（布の甲とゴム底）
    m = bpy.data.materials.new("H Shoe" + tag); nt = NT(m); b = principled(nt, rough=0.7, spec=0.3, sheen=0.2)
    nt.l(_objattr(nt, "shoe_col"), b.inputs["Base Color"]); M["shoe"] = m
    m = bpy.data.materials.new("H Sole" + tag); nt = NT(m); b = principled(nt, rough=0.55, spec=0.4)
    nt.l(_objattr(nt, "sole_col"), b.inputs["Base Color"]); M["sole"] = m
    M["mouth"] = hbuild.mat_simple("H Mouth" + tag, "#4A2422", 0.55, 0.3)
    M["lash"] = hbuild.mat_simple("H Lash" + tag, "#1B1310", 0.6, 0.3)
    M["rim"] = hbuild.mat_simple("H Lid rim" + tag, "#C98C80", 0.4, 0.5)
    M["bud"] = hbuild.mat_simple("H Earbud" + tag, "#F3F3F1", 0.22, 0.6, coat=0.4)
    M["phone"] = hbuild.mat_simple("H Phone" + tag, "#1E2126", 0.35, 0.5)
    if style == "clay": clay_overrides(M, S)
    _MATS[key] = M
    return M


def clay_overrides(M, S):
    """参考画像の質感：髪はフェルトのようなつや消し（毛の筋なし）、まぶたの縁は肌の色、まつげは黒"""
    m = bpy.data.materials.new("H Hair clay felt"); nt = NT(m)
    b = principled(nt, rough=0.88, spec=0.25, sheen=0.22, sheen_r=0.35)
    nz = nt.n("ShaderNodeTexNoise", i_Scale=38.0, i_Detail=2.0); nt.l(_rest(nt), nz.inputs["Vector"])
    hc = _objattr(nt, "hair_col")
    nt.l(_mix(nt, nz.outputs["Fac"], _scale_color(nt, hc, 0.86), _scale_color(nt, hc, 1.16)), b.inputs["Base Color"])
    fz = nt.n("ShaderNodeTexNoise", i_Scale=1400.0, i_Detail=6.0); nt.l(_rest(nt), fz.inputs["Vector"])
    _bump(nt, fz.outputs["Fac"], 0.12, 0.00025 * S, b)
    M["hair"] = m
    M["brow"] = hbuild.mat_simple("H Brow clay", "#17151B", 0.85, 0.2)     # 参考の眉は黒に近い
    # 服（フェルトのような布）：Vネックの中の服とネクタイは、形の座標から材質の中で描く（ふちがきれいに出る）
    m = bpy.data.materials.new("H knit clay"); nt = NT(m)
    b = principled(nt, rough=0.92, spec=0.22, sheen=0.28, sheen_r=0.45)
    sp = nt.n("ShaderNodeSeparateXYZ"); nt.l(_rest(nt), sp.inputs[0]); x, y, z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    ax = _m(nt, "ABSOLUTE", x)
    vw = _m(nt, "MULTIPLY_ADD", _m(nt, "DIVIDE", _m(nt, "SUBTRACT", z, 0.80), 0.26, clamp=True), 0.072); vw = _m(nt, "ADD", vw, 0.010)
    front = _smooth(nt, _m(nt, "MULTIPLY", y, -1.0), -0.016, -0.008)
    vm = _m(nt, "MULTIPLY", _m(nt, "MULTIPLY", _smooth(nt, _m(nt, "SUBTRACT", vw, ax), -0.0012, 0.0012), _smooth(nt, z, 0.798, 0.803)), front)
    vm = _m(nt, "MULTIPLY", vm, _objattr(nt, "vneck", "Fac"))
    tw = _m(nt, "ADD", _m(nt, "MULTIPLY", _m(nt, "DIVIDE", _m(nt, "SUBTRACT", 1.04, z), 0.20, clamp=True), 0.004), 0.011)
    tm = _m(nt, "MULTIPLY", _smooth(nt, _m(nt, "SUBTRACT", tw, ax), -0.0009, 0.0009), _smooth(nt, z, 0.818, 0.824))
    tm = _m(nt, "MULTIPLY", _m(nt, "MULTIPLY", tm, _m(nt, "SUBTRACT", 1.0, _smooth(nt, z, 1.040, 1.046))), _m(nt, "MULTIPLY", front, _objattr(nt, "tie", "Fac")))
    nz = nt.n("ShaderNodeTexNoise", i_Scale=45.0, i_Detail=2.0); nt.l(_rest(nt), nz.inputs["Vector"])
    tc = _objattr(nt, "top_col"); col = _mix(nt, nz.outputs["Fac"], _scale_color(nt, tc, 0.90), _scale_color(nt, tc, 1.08))
    col = _mix(nt, vm, col, _objattr(nt, "inner_col")); col = _mix(nt, tm, col, _objattr(nt, "tie_col"))
    nt.l(col, b.inputs["Base Color"])
    fz = nt.n("ShaderNodeTexNoise", i_Scale=1100.0, i_Detail=6.0); nt.l(_rest(nt), fz.inputs["Vector"]); _bump(nt, fz.outputs["Fac"], 0.10, 0.0003 * S, b)
    M["knit"] = m
    # 中の服の襟（リブ）：色は inner_col
    m = bpy.data.materials.new("H rib inner clay"); nt = NT(m)
    b = principled(nt, rough=0.9, spec=0.22, sheen=0.5, sheen_r=0.45)
    wv = nt.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", wave_profile="SIN", i_Scale=110.0); nt.l(_rest(nt), wv.inputs["Vector"])
    _bump(nt, wv.outputs["Fac"], 0.25, 0.0008 * S, b)
    ic = _objattr(nt, "inner_col"); nt.l(_mix(nt, wv.outputs["Fac"], _scale_color(nt, ic, 0.85), ic), b.inputs["Base Color"])
    M["rib_inner"] = m
    M["rim"] = hbuild.mat_simple("H Lid rim clay", "#D49C7C", 0.6, 0.3)
    M["lash"] = hbuild.mat_simple("H Lash clay", "#151112", 0.7, 0.2)
    M["mouth"] = hbuild.mat_simple("H Mouth clay", "#5E2C24", 0.7, 0.2)


# ------------------------------------------------------------ 形（キャッシュ）
def blush_of(X, hc, s):
    b = np.zeros(len(X))
    for c, a, r in [((0.044, -0.062, -0.022), 0.55, 0.019), ((-0.044, -0.062, -0.022), 0.55, 0.019), ((0, -0.100, -0.021), 0.30, 0.012),
                    ((0.083, 0.008, -0.004), 0.5, 0.024), ((-0.083, 0.008, -0.004), 0.5, 0.024), ((0, -0.080, -0.052), 0.30, 0.014)]:
        d2 = ((X - hc - np.array(c) * s) ** 2).sum(1); b = np.maximum(b, a * np.exp(-d2 / (r * s) ** 2))
    return b


def geometry(cfg):
    q = QUALITY[cfg.get("quality", "hero")]
    B = dict(hgen.BODY); B.update(cfg.get("body", {}))
    P = dict(hgen.HEAD); P.update(cfg.get("head", {}))
    HP = dict(hgen.HAIR); HP.update(cfg.get("hair", {}))
    SHEET = None
    if cfg.get("sheet"):        # 6面図から起こした頭と髪（網目は Blender の外で作って保存したもの）
        sd_ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sheets")
        P["loft"] = json.load(open(os.path.join(sd_, f"loftP_{cfg['sheet']}.json"), encoding="utf-8"))
        SHEET = np.load(os.path.join(sd_, f"mesh_{cfg['sheet']}.npz"))
    J = hgen.skeleton(B); hc = J["head_center"]; s = P["hs"]; hf = hgen.head_frame(P)
    G = {}

    def head():
        if SHEET is not None:
            m = hgen.head_model(P, hc); V = SHEET["V"] + hc; Q = SHEET["Q"]
        else:
            m, V, Q = hgen.head_mesh(P, hc, q["head"])
        W = __import__("sdf").prim_weights(m, V, Q, ["head", "neck"], sigma=0.010 * s)
        if not P.get("socket", True):   # アニメ顔：あごの下は頭と一緒に動く（うつむいても二重あごにならない）
            pv = np.asarray(J["head"]) - hc; rel = V - hc
            hh = (rel[:, 2] - pv[2]) + 0.9 * (pv[1] - rel[:, 1])
            wr = np.clip((hh + 0.030 * s) / (0.030 * s), 0, 1); wr = wr * wr * (3 - 2 * wr) * (rel[:, 1] < pv[1] + 0.01 * s)
            W[:, 0] = np.maximum(W[:, 0], wr); W[:, 1] = 1 - W[:, 0]
        bv = hgen.brows(m, hc, P, s); shapes, mf = hgen.mouth_shapes(m, hc, P, s)
        out = dict(V=V, Q=Q, W=W, b0V=bv[0][0], b0F=np.array(bv[0][1], dtype=object), b1V=bv[1][0], b1F=np.array(bv[1][1], dtype=object),
                   mF=np.array(mf, dtype=object), **{f"m_{k}": v for k, v in shapes.items()})
        return out
    G["head"] = _cached("head", _key(P, q["head"], "v8", cfg.get("sheet"), float(SHEET["V"].sum()) if SHEET is not None else 0), head)

    def hair():
        m = hgen.head_model(P, hc)
        if SHEET is not None: V = SHEET["Vh"] + hc; Q = SHEET["Qh"]
        elif HP["style"] == "locks": _, V, Q = hgen.hair_locks_mesh(m, HP, hc, s, P, q["head"])
        elif HP["style"] in chunkhair.STYLES: _, V, Q = chunkhair.chunk_hair_mesh(m, P, HP, hc, s, q["head"])
        else: F, V, Q, phi = hgen.hair_mesh(m, HP, hc, s, q["head"])
        # 揺れの重み：頭の面から外側ほど・上と前ほど大きい（根元は動かない）
        d = m(V); u = (V - hc) / np.linalg.norm(V - hc, axis=1, keepdims=True)
        top = np.clip((u[:, 2] + 0.1) / 0.6, 0, 1)
        wh = np.clip(d / (0.016 * s), 0, 1) ** 1.3 * 0.8 * top
        return dict(V=V, Q=Q, wh=wh)
    G["hair"] = _cached("hair", _key(P, HP, q["head"], "v8", chunkhair.STYLES.get(HP["style"], 0), cfg.get("sheet"), float(SHEET["Vh"].sum()) if SHEET is not None else 0), hair)

    def body():
        m, mp, (Vs, Qs, mat), (Vp, Qp) = hgen.body_mesh(B, J, q["body"])
        bn = sorted({b for mm in (m, mp) for pr in mm.prims for b in pr["bones"]})
        W = __import__("sdf").prim_weights(m, Vs, Qs, bn, sigma=0.015, neighbors=hgen.BODY_NEIGHBORS)
        Wp = __import__("sdf").prim_weights(mp, Vp, Qp, bn, sigma=0.015, neighbors=hgen.BODY_NEIGHBORS)
        return dict(V=Vs, Q=Qs, mat=mat, W=W, Vp=Vp, Qp=Qp, Wp=Wp, bn=np.array(bn))
    G["body"] = _cached("body", _key(B, q["body"], "v9"), body)

    if cfg.get("eyes") == "anime":
        def aeye():
            import animeface
            AE = animeface.eye_set(hgen.head_model(P, hc), hc, P, s); out = {}
            for sd, a in AE.items():
                for nm in ("rest", "close", "wide"):
                    out[f"{sd}_white_{nm}"] = a["white"][nm]; out[f"{sd}_lash_{nm}"] = a["lash"][nm]
                out[f"{sd}_white_F"] = np.array(a["white_F"]); out[f"{sd}_lash_F"] = np.array(a["lash_F"])
                out[f"{sd}_low"] = a["low"]; out[f"{sd}_low_F"] = np.array(a["low_F"])
                out[f"{sd}_u"] = a["u"]; out[f"{sd}_v"] = a["v"]; out[f"{sd}_ec"] = a["ec"]; out[f"{sd}_depth"] = np.array(a["depth"])
            return out
        G["aeye"] = _cached("aeye", _key(P, q["head"], "a4"), aeye)
    for sd, sx in (("L", 1), ("R", -1)):
        def hand(sd=sd, sx=sx):
            Pm, V, Q, info = hgen.hand_mesh(B, J, sd, sx, q["hand"])
            bn = ["forearm", "hand", "thumb_01", "thumb_02", "thumb_03"] + [f"{f}_{i:02d}" for f in ("index", "middle", "ring", "pinky") for i in (1, 2, 3)]
            W = __import__("sdf").prim_weights(Pm, V, Q, bn, sigma=0.004, neighbors=hgen.HAND_NEIGHBORS)
            ch = info["chains"]
            return dict(V=V, Q=Q, W=W, bn=np.array([f"{b}.{sd}" for b in bn]), mcp=info["mcp_mid"], dorsal=info["dorsal"],
                        **{f"c_{f}_p": np.array(ch[f]["pts"]) for f in ch}, **{f"c_{f}_z": np.array(ch[f]["z"]) for f in ch})
        G["hand." + sd] = _cached("hand" + sd, _key(B, q["hand"], sd, "v4"), hand)
        def shoe(sd=sd):
            m, V, Q, mat = hgen.shoe_mesh(J, sd, q["shoe"]); return dict(V=V, Q=Q, mat=mat)
        G["shoe." + sd] = _cached("shoe" + sd, _key(B, q["shoe"], sd, "v4"), shoe)
    if cfg.get("earbuds", True):
        for i, (sd, sx) in enumerate((("L", 1), ("R", -1))):
            def bud(i=i, sx=sx):
                V, Q = hgen.earbud_mesh(hf, hc, i, sx, s, q["bud"]); return dict(V=V, Q=Q)
            G["bud." + sd] = _cached("bud" + sd, _key(P, q["bud"], sd, "v8"), bud)
    return dict(G=G, B=B, P=P, HP=HP, J=J, hc=hc, s=s, hf=hf, q=q)


# ------------------------------------------------------------ 組み立て
def make_character(name, cfg, coll=None, S=1.0):
    coll = coll or bpy.context.scene.collection
    D = geometry(cfg); G = D["G"]; J, hc, s, hf, P, HP = D["J"], D["hc"], D["s"], D["hf"], D["P"], D["HP"]
    M = shared_mats(S, cfg.get("style", "real"))
    hands = {}
    for sd in ("L", "R"):
        g = G["hand." + sd]
        hands[sd] = dict(mcp_mid=g["mcp"], dorsal=g["dorsal"],
                         chains={f: dict(pts=list(g[f"c_{f}_p"]), z=list(g[f"c_{f}_z"])) for f in ("index", "middle", "ring", "pinky", "thumb")})
    eyes = [hc + e for e in hf["eye"]]; brows = [hc + b for b in hf["brow"]]
    hb = (hc + np.array([0, 0.020, 0.090]) * s, hc + np.array([0, 0.060, 0.090]) * s)
    bl = hgen.bone_list(J, eyes, brows, hands, hair=hb)
    arm = hbuild.build_armature(name, bl, coll)
    arm.data.display_type = "STICK"
    C = cfg["colors"]
    props = dict(skin=srgb(C["skin"]), hair_col=srgb(C["hair"]), iris1=srgb(C.get("iris1", "#4A3020")), iris2=srgb(C.get("iris2", "#8A6238")),
                 top_col=srgb(C["top"]), pants_col=srgb(C["pants"]), shoe_col=srgb(C["shoe"]), sole_col=srgb(C["sole"]))
    cr, e1, e2 = hgen.hair_frame(HP)
    props.update(h_c=tuple(hc), h_e1=tuple(e1), h_e2=tuple(e2), h_cr=tuple(cr), h_swirl=float(HP["swirl"]),
                 iris_c=math.cos(math.radians(P["iris"])), pupil_c=math.cos(math.radians(P["pupil"])))
    objs = {}

    def new(nm, V, F, mats, **kw):
        ob = mk_mesh(f"{name} {nm}", V, F, coll=coll, mats=mats, **kw)
        for k, v in props.items(): ob[k] = v
        objs[nm] = ob; return ob
    h = G["head"]
    ob = new("head", h["V"], h["Q"], [M["skin"]], attrs={"rest": ("FLOAT_VECTOR", h["V"]), "blush": ("FLOAT", blush_of(h["V"], hc, s) * cfg.get("blush", 1.0))})
    bind(ob, arm, h["W"], ["head", "neck"])
    ob = new("hair", G["hair"]["V"], G["hair"]["Q"], [M["hair"]], attrs={"rest": ("FLOAT_VECTOR", G["hair"]["V"])})
    wh = G["hair"]["wh"]; bind(ob, arm, np.stack([1 - wh, wh], 1), ["head", "hair"])
    anime = cfg.get("eyes") == "anime"
    if anime:
        import animeeyes_bl
        g = G["aeye"]; AE = {}
        for sd in ("L", "R"):
            AE[sd] = dict(white={nm: g[f"{sd}_white_{nm}"] for nm in ("rest", "close", "wide")}, lash={nm: g[f"{sd}_lash_{nm}"] for nm in ("rest", "close", "wide")},
                          white_F=[tuple(f) for f in g[f"{sd}_white_F"]], lash_F=[tuple(f) for f in g[f"{sd}_lash_F"]], low=g[f"{sd}_low"],
                          low_F=[tuple(f) for f in g[f"{sd}_low_F"]], u=g[f"{sd}_u"], v=g[f"{sd}_v"], ec=g[f"{sd}_ec"], depth=float(g[f"{sd}_depth"]))
        animeeyes_bl.build(name, cfg, arm, hc, s, P, M, new, AE, coll)
    for i, sd in enumerate(("L", "R")):
        if anime:
            bv, bf = h[f"b{i}V"], [tuple(f) for f in h[f"b{i}F"]]
            bind(new("brow." + sd, bv, bf, [M["brow"]]), arm, {"brow." + sd: 1.0}, None)
            continue
        ev, ef, ed = hgen.eyeball(hc + hf["eye"][i], hf["re"])
        bind(new("eye." + sd, ev, ef, [M["eye"]], attrs={"dir": ("FLOAT_VECTOR", ed)}), arm, {"eye." + sd: 1.0}, None)
        for up in (True, False):
            lash = cfg.get("lash", 0) if up else 0
            lv, lf, mg = hgen.lid_shell(hc + hf["eye"][i], hf["re"], upper=up, a_rest=P["lid_up"] if up else P["lid_lo"],
                                        thick=0.0017 + 0.0009 * (lash > 0), extra=lash)
            ob = new(f"lid_{'up' if up else 'lo'}.{sd}", lv, lf, [M["skin"], M["lash"] if up else M["rim"]], mat_idx=[1 if x else 0 for x in mg],
                     attrs={"rest": ("FLOAT_VECTOR", lv), "blush": ("FLOAT", np.full(len(lv), 0.12))})
            bind(ob, arm, {f"lid_{'up' if up else 'lo'}.{sd}": 1.0}, None)
        bv, bf = h[f"b{i}V"], [tuple(f) for f in h[f"b{i}F"]]
        bind(new("brow." + sd, bv, bf, [M["brow"]]), arm, {"brow." + sd: 1.0}, None)
    mf = [tuple(f) for f in h["mF"]]
    mo = new("mouth", h["m_rest"], mf, [M["mouth"]])
    mo.shape_key_add(name="Basis")
    for k in ("o", "open", "flat", "smile"):
        kb = mo.shape_key_add(name=k, from_mix=False); kb.data.foreach_set("co", h["m_" + k].ravel().astype(np.float32))
    bind(mo, arm, {"head": 1.0}, None)
    b = G["body"]
    ob = new("top", b["V"], b["Q"], [M["knit"], M["rib"]], mat_idx=b["mat"], attrs={"rest": ("FLOAT_VECTOR", b["V"])})
    bind(ob, arm, b["W"], [str(x) for x in b["bn"]])
    ob = new("pants", b["Vp"], b["Qp"], [M["pants"]], attrs={"rest": ("FLOAT_VECTOR", b["Vp"])})
    bind(ob, arm, b["Wp"], [str(x) for x in b["bn"]])
    for sd in ("L", "R"):
        g = G["hand." + sd]
        ob = new("hand." + sd, g["V"], g["Q"], [M["skin"]], attrs={"rest": ("FLOAT_VECTOR", g["V"]), "blush": ("FLOAT", np.full(len(g["V"]), 0.15))})
        bind(ob, arm, g["W"], [str(x) for x in g["bn"]])
        g = G["shoe." + sd]
        ob = new("shoe." + sd, g["V"], g["Q"], [M["shoe"], M["sole"]], mat_idx=g["mat"]); bind(ob, arm, {"foot." + sd: 1.0}, None)
        if "bud." + sd in G:
            g = G["bud." + sd]; bind(new("bud." + sd, g["V"], g["Q"], [M["bud"]]), arm, {"head": 1.0}, None)
    extras_and_style(cfg, objs, arm, J, hc, hf, s, P, M, new, coll)
    facet = cfg.get("facet") or {}
    if cfg.get("projtex") and cfg.get("sheet"):    # 資料の絵を貼る：頭と髪の材質を差し替え、描いた目・眉・口・眼鏡は隠す（絵に描かれている）
        import projtex_bl
        sd_ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sheets")
        PW = np.load(cfg.get("projw") or os.path.join(sd_, f"projw_{cfg['sheet']}.npz"))
        pm = projtex_bl.material(f"{name} proj", cfg["sheet"], hc, expr=cfg.get("expr"), emit=cfg.get("proj_emit", 0.55) if cfg.get("proj_mode") != "flat" else None)
        for nm_, key_ in (("head", "Wh"), ("hair", "Whair")):
            ob_ = objs[nm_]; ob_.data.materials.clear(); ob_.data.materials.append(pm); projtex_bl.attach(ob_, PW[key_]); ob_.data.shade_smooth()
        for nm_, ob_ in objs.items():
            if nm_.split(".")[0] in ("eye", "lash", "lowline", "brow", "mouth", "glasses", "eyehl", "wing", "lid_up", "lid_lo", "bud"):
                ob_.hide_render = True; ob_.hide_viewport = True
        objs["mouth"].hide_render = True; objs["mouth"].hide_viewport = True
        facet = {k_: v_ for k_, v_ in facet.items() if k_ != "hair"}
    if D["q"]["sub"]:
        for nm in ("head", "hair"):
            if nm not in facet: add_subsurf(objs[nm], D["q"]["sub"])
    for nm, ratio in facet.items():     # 面をカクカクにする：形を減らして（変形の前に）平らな陰影で描く
        for key, ob in objs.items():
            if key == nm or key.startswith(nm + "."):
                r_ = ratio if ratio <= 1 else min(1.0, ratio / max(1, len(ob.data.polygons)))
                md = ob.modifiers.new("Facet", "DECIMATE"); md.decimate_type = "COLLAPSE"; md.ratio = r_; md.use_collapse_triangulate = False
                ob.modifiers.move(len(ob.modifiers) - 1, 0); ob.data.shade_flat()
    arm.scale = (S, S, S)
    return dict(arm=arm, objs=objs, J=J, hc=hc, hf=hf, s=s, P=P, HP=HP, mouth=mo, cfg=cfg, lid_up=P["lid_up"], lid_lo=P["lid_lo"])


def _solid(name, hexc, rough=0.6, emit=0.0):
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, base=srgb(hexc), rough=rough, spec=0.35)
    if emit > 0: b.inputs["Emission Color"].default_value = (*srgb(hexc), 1); b.inputs["Emission Strength"].default_value = emit
    return m


def _lapel_geom(B, J, outfit):
    import sdf as _sdf
    top = hgen.body_model(B, J, "top")
    zs = [0.785, 0.80, 0.90, 0.975, 0.992, 1.000, 1.070, 1.085]
    ws = [0.0, 0.004, 0.034, 0.058, 0.058, 0.030, 0.027, 0.0]
    def xv(z): return 0.010 + 0.072 * np.clip((z - 0.80) / 0.26, 0, 1)
    def F(p):
        z = p[:, 2]; ax = np.abs(p[:, 0]); x0 = xv(z) - 0.002; w = np.interp(z, zs, ws)
        reg = np.maximum.reduce([x0 - ax, ax - (x0 + w), p[:, 1] - 0.035, 0.0005 - w])
        sh = np.abs(top(p) - 0.0042) - 0.0021
        return np.maximum(sh, reg)
    V, Q = _sdf.mesh(F, np.array([-0.20, -0.10, 0.77]), np.array([0.20, 0.07, 1.10]), 0.0016, relax_iters=2)
    return dict(V=V, Q=Q)


def _turtle_geom_loft(J, N, hcl, notch=False):
    """6面図の首に合わせたタートルネック：楕円の筒（首より9mm太い）、上は前が低く後ろが高い（あごの下まで）"""
    import sdf as _sdf
    hcl = np.asarray(hcl, float); rx, ry = N["r"][0] + 0.009, N["r"][1] + 0.009; yc = hcl[1] + N["c"][1]
    zf, zb = hcl[2] + N.get("tn_front", -0.115), hcl[2] + N.get("tn_back", -0.104); z0 = np.asarray(J["neck"])[2] - 0.035
    def F(p):
        X = p[:, 0] / rx; Y = (p[:, 1] - yc) / ry; r = np.sqrt(X * X + Y * Y)
        f = (r - 1) * min(rx, ry)
        f = np.maximum(f, -(f + 0.010))                                  # 厚さ1cmの筒
        ztop = zf + (zb - zf) * np.clip((p[:, 1] - (yc - ry)) / (2 * ry), 0, 1)
        f = _sdf.smax(f, p[:, 2] - ztop, 0.004); f = np.maximum(f, z0 - p[:, 2])
        if notch:      # シャツの襟：前の真ん中をV字に開ける（ネクタイの結び目が見える）
            dn = (0.007 + (ztop - p[:, 2]) * 0.55) - np.abs(p[:, 0])
            f = np.maximum(f, np.minimum(dn, (yc - p[:, 1])))
        # 上の折り返し（少し太い）
        rim = np.sqrt(np.maximum((r - 1) * min(rx, ry) + 0.002, 0) ** 2 + 0.0) - 0.0
        return f
    lo = np.array([-rx - 0.02, yc - ry - 0.02, z0 - 0.01]); hi = np.array([rx + 0.02, yc + ry + 0.02, zb + 0.02])
    V, Q = _sdf.mesh(F, lo, hi, 0.0018, relax_iters=2)
    return dict(V=V, Q=Q)


def _turtle_geom(J):
    import sdf as _sdf
    nb = np.asarray(J["neck"], float); nax = hgen.norm(np.asarray(J["head"]) - nb)
    a = nb + nax * 0.000; b = nb + nax * 0.062
    outer = _sdf.cone(a, b, 0.064, 0.056); inner = _sdf.cone(a - nax * 0.02, b + nax * 0.02, 0.047, 0.044)
    R = np.stack([hgen.norm(np.cross([0, 1.0, 0], nax)), hgen.norm(np.cross(nax, np.cross([0, 1.0, 0], nax))), nax], 1)
    roll = _sdf.torus(b, R, 0.054, 0.0085)
    def F(p): return np.maximum(_sdf.smin(outer(p), roll(p), 0.006), -inner(p))
    lo = nb - np.array([0.09, 0.09, 0.02]); hi = nb + np.array([0.09, 0.09, 0.10])
    V, Q = _sdf.mesh(F, lo, hi, 0.0018, relax_iters=2)
    return dict(V=V, Q=Q)


def _lapels_turtle(cfg, outfit, C, J, M, new, arm, P=None):
    if cfg.get("lapels", False):   # ジャケットの襟（下襟）：胴の面から少し浮いた布。下はボタン、上は首の後ろへ
        B_ = dict(hgen.BODY); B_.update(cfg.get("body", {}))
        g = _cached("lapel", _key(B_, outfit, "l3"), lambda: _lapel_geom(B_, J, outfit))
        lap = new("lapel", g["V"], g["Q"], [M["knit"]], attrs={"rest": ("FLOAT_VECTOR", g["V"])})
        z_ = g["V"][:, 2]; wc = np.clip((z_ - 0.80) / 0.16, 0, 1)
        bind(lap, arm, np.stack([wc, 1 - wc], 1), ["chest", "spine"]); lap.data.shade_smooth()
    if outfit == "suit" and P is not None and P.get("loft"):   # シャツの襟（白、前はV字）
        N = dict(P["loft"]["neck"], tn_front=-0.150, tn_back=-0.112); hcl = J["head_center"]
        g = _cached("shirtcol", _key(np.asarray(J["neck"]).tolist(), N, np.asarray(hcl).tolist(), "sc1"), lambda: _turtle_geom_loft(J, N, hcl, notch=True))
        sc_ = new("shirt_collar", g["V"], g["Q"], [M["rib_inner"]], attrs={"rest": ("FLOAT_VECTOR", g["V"])})
        sc_["inner_col"] = srgb(C.get("inner", "#E9E8E4"))
        wn = np.clip((g["V"][:, 2] - 1.075) / 0.045, 0, 1); bind(sc_, arm, np.stack([wn, 1 - wn], 1), ["neck", "chest"]); sc_.data.shade_smooth()
    if outfit == "jacket_turtle":  # タートルネック：首を包む筒（上は折り返し）
        if P is not None and P.get("loft"):
            N = P["loft"]["neck"]; hcl = J["head_center"]
            g = _cached("turtle", _key(np.asarray(J["neck"]).tolist(), N, np.asarray(hcl).tolist(), "tL1"), lambda: _turtle_geom_loft(J, N, hcl))
        else:
            g = _cached("turtle", _key(np.asarray(J["neck"]).tolist(), np.asarray(J["head"]).tolist(), "t2"), lambda: _turtle_geom(J))
        tn = new("turtle", g["V"], g["Q"], [M["rib_inner"]], attrs={"rest": ("FLOAT_VECTOR", g["V"])})
        tn["inner_col"] = srgb(C.get("inner", "#182033"))
        wn = np.clip((g["V"][:, 2] - 1.075) / 0.045, 0, 1); bind(tn, arm, np.stack([wn, 1 - wn], 1), ["neck", "chest"]); tn.data.shade_smooth()


def extras_and_style(cfg, objs, arm, J, hc, hf, s, P, M, new, coll):
    """服の作り分け（ジャケットと中の服・ネクタイ）、目の光、眼鏡、キャップ、パーカーのフードとひも"""
    import sdf as _sdf
    C = cfg["colors"]; outfit = cfg.get("outfit")
    top = objs["top"]
    if outfit in ("suit", "blazer", "jacket_turtle") and cfg.get("style") == "clay":
        top["vneck"] = 1.0; top["inner_col"] = srgb(C.get("inner", "#E9E8E4")); top["tie"] = 1.0 if outfit == "suit" else 0.0
        top["tie_col"] = srgb(C.get("tie", "#252830"))
        V = np.array([v.co[:] for v in top.data.vertices]); Q = [tuple(p.vertices) for p in top.data.polygons]
        cz = np.array([V[list(q)][:, 2].mean() for q in Q]); mi = np.array([p.material_index for p in top.data.polygons])
        top.data.materials.append(M["rib_inner"]); idx_in = len(top.data.materials) - 1
        rib = mi == 1; mi[rib & (cz <= 1.0)] = 0; mi[rib & (cz > 1.0)] = 0 if outfit == "suit" else idx_in   # 袖口・裾は上着の布、襟は中の服（スーツは上着の襟）
        top.data.polygons.foreach_set("material_index", mi.astype(np.int32))
        _lapels_turtle(cfg, outfit, C, J, M, new, arm, P)
    elif outfit in ("suit", "blazer", "jacket_turtle"):
        V = np.array([v.co[:] for v in top.data.vertices]); Q = [tuple(p.vertices) for p in top.data.polygons]
        cen = np.array([V[list(q)].mean(0) for q in Q]); mi = np.array([p.material_index for p in top.data.polygons])
        x, y, z = cen[:, 0], cen[:, 1], cen[:, 2]
        front = y < 0.012
        vw = 0.010 + 0.072 * np.clip((z - 0.80) / 0.26, 0, 1)
        vreg = front & (z > 0.80) & (np.abs(x) < vw) & (mi == 0)
        top.data.materials.append(_solid(top.name + " inner", C.get("inner", "#E9E8E4"), 0.7)); idx_in = len(top.data.materials) - 1
        mi[vreg] = idx_in
        if outfit in ("jacket_turtle", "blazer"): mi[mi == 1] = idx_in   # 襟（リブ）も中の服の色
        if outfit == "suit": mi[mi == 1] = idx_in
        if outfit == "suit":
            top.data.materials.append(_solid(top.name + " tie", C.get("tie", "#252830"), 0.5)); idx_t = len(top.data.materials) - 1
            treg = front & (z > 0.82) & (z < 1.04) & (np.abs(x) < 0.012 + 0.004 * np.clip((1.04 - z) / 0.2, 0, 1))
            mi[treg] = idx_t
        top.data.polygons.foreach_set("material_index", mi.astype(np.int32))
    if cfg.get("eye_hl", False):   # 目の光の点（白く光る小さな点。目と一緒に動く）
        HL = _solid("Eye highlight", "#FFFFFF", 0.3, emit=3.0)
        for i, sd in enumerate(("L", "R")):
            sx = 1 if sd == "L" else -1
            ec = hc + hf["eye"][i]; d = hgen.norm(np.array([sx * 0.30, -1.0, 0.45]))
            pos = ec + d * (hf["re"] + 0.0006)
            x_ = hgen.norm(np.cross([0, 0, 1.0], d)); y_ = np.cross(d, x_); R = np.stack([x_, y_, d], 1)
            Vv, Ff = hgen.uv_sphere(1.0, 16, 10); Vv = (Vv * np.array([0.0024, 0.0028, 0.0010]) * s) @ R.T + pos
            hb = new("eyehl." + sd, Vv, Ff, [HL]); bind(hb, arm, {"eye." + sd: 1.0}, None)
    if cfg.get("wing"):           # 目尻のアイライン：上まぶたの縁から外へ少し伸びる（まぶたと一緒に動く）
        LM = M["lash"]
        for i, sd in enumerate(("L", "R")):
            sx = 1 if sd == "L" else -1; ec = hc + hf["eye"][i]; re = hf["re"]
            a = ec + np.array([sx * re * 0.86, -re * 0.48, re * 0.16]); b_ = a + np.array([sx * 0.0075, 0.0035, 0.0030]) * s
            wm = _sdf.Model(); wm.add(_sdf.cone(a, b_, 0.00125 * s, 0.00035 * s), "wing")
            Vw, Qw = _sdf.mesh(wm, np.minimum(a, b_) - 0.006 * s, np.maximum(a, b_) + 0.006 * s, 0.00028 * s, relax_iters=1)
            bind(new("wing." + sd, Vw, Qw, [LM]), arm, {"lid_up." + sd: 1.0}, None)
    GS = P.get("loft", {}).get("feat", {}).get("glasses") if P.get("loft") else None
    if cfg.get("glasses") and GS:   # 6面図の眼鏡：大きな四角いレンズ、太い黒ぶち、つるは耳まで
        GM = _solid("Glasses", C.get("glasses", "#141416"), 0.35)
        gm = _sdf.Model(); cx, cz = GS["c"]; hx, hz = GS["half"]; th = GS["thick"]; yf = GS["y_front"]
        ear = P["loft"]["feat"]["ear"]
        for sx in (1, -1):
            c = hc + np.array([sx * cx, yf, cz])
            outer = _sdf.rbox(c, np.array([hx, th * 0.55, hz]), 0.008)
            inner = _sdf.rbox(c, np.array([hx - th, 0.02, hz - th]), 0.006)
            gm.add(lambda p, o=outer, n=inner: _sdf.smax(o(p), -n(p), 0.0006), "frame")
            a = hc + np.array([sx * (cx + hx - th * 0.4), yf + 0.004, GS["temple_z"]]); b_ = hc + np.array([sx * (abs(ear[0][0]) + 0.004), ear[0][1] - 0.006, GS["temple_z"] - 0.006])
            gm.add(_sdf.cone(a, b_, 0.0022, 0.0018), "temple", k=0.002)
        gm.add(_sdf.cone(hc + np.array([cx - hx + th * 0.5, yf, cz + hz * 0.35]), hc + np.array([-(cx - hx + th * 0.5), yf, cz + hz * 0.35]), 0.0026, 0.0026), "bridge", k=0.002)
        Vg, Qg = _sdf.mesh(gm, hc + np.array([-0.13, yf - 0.02, cz - hz - 0.02]), hc + np.array([0.13, 0.06, cz + hz + 0.03]), 0.0008, relax_iters=1)
        bind(new("glasses", Vg, Qg, [GM]), arm, {"head": 1.0}, None)
    elif cfg.get("glasses"):        # 眼鏡：角の丸い四角い枠＋つる
        GM = _solid("Glasses", C.get("glasses", "#1C1C1E"), 0.35)
        gm = _sdf.Model()
        for i, sx in enumerate((1, -1)):
            ec = hc + hf["eye"][i]; c = ec + np.array([0, -(hf["re"] + 0.010 * s), -0.002 * s])
            gw = cfg.get("glasses_w", 1.0)      # 枠の太さ（倍率）
            outer = _sdf.rbox(c, np.array([0.021, 0.0022 * gw, 0.0150]) * s, 0.0060 * s)
            inner = _sdf.rbox(c, np.array([0.021 - 0.0032 * gw, 0.010, 0.0150 - 0.0032 * gw]) * s, 0.0045 * s)
            gm.add(lambda p, o=outer, n=inner: _sdf.smax(o(p), -n(p), 0.0004), "frame")
            ear = hc + np.array([sx * 0.081 * s, 0.010 * s, 0.004 * s])
            gm.add(_sdf.cone(c + np.array([sx * 0.020 * s, 0.002 * s, 0.006 * s]), ear + np.array([0, -0.004 * s, 0.006 * s]), 0.0013 * s, 0.0012 * s), "temple", k=0.001)
        e0, e1 = hc + hf["eye"][0], hc + hf["eye"][1]
        gm.add(_sdf.cone(e0 + np.array([-0.012 * s, -(hf["re"] + 0.010 * s), 0.004 * s]), e1 + np.array([0.012 * s, -(hf["re"] + 0.010 * s), 0.004 * s]),
                         0.0013 * s, 0.0013 * s), "bridge", k=0.001)
        Vg, Qg = _sdf.mesh(gm, hc - np.array([0.11, 0.13, 0.05]) * s, hc + np.array([0.11, 0.05, 0.05]) * s, 0.0007 * s, relax_iters=1)
        bind(new("glasses", Vg, Qg, [GM]), arm, {"head": 1.0}, None)
    if cfg.get("cap"):            # キャップ：髪の上にかぶる（頭の上半分＋前のつば）
        CM = _solid("Cap", C.get("cap", "#E3AE3A"), 0.62)
        R0 = 0.104 * s * P.get("cran", 1.0) + 0.030 * s      # 髪の上にかぶる（髪が突き抜けないよう余裕をもたせる）
        cm = _sdf.Model()
        cc = hc + np.array([0, 0.012 * s, 0.040 * s])
        def crown(p, cc=cc, R0=R0):
            q = p - cc; return _sdf.smax(np.sqrt((q * q).sum(1)) - R0, -(q @ hgen.norm((0, 0.15, 1.0)) - 0.004 * s), 0.004 * s)
        cm.add(crown, "crown")
        cm.add(_sdf.ellipsoid(cc + np.array([0, -R0 * 0.95, 0.010 * s]), np.array([0.088, 0.070, 0.008]) * s, hgen.rot(-14, 0, 0)), "brim", k=0.010 * s)
        cm.add(_sdf.sphere(cc + np.array([0, 0.02 * s, R0 * 0.985]), 0.010 * s), "button", k=0.004 * s)
        Vc, Qc = _sdf.mesh(cm, cc - np.array([0.16, 0.20, 0.06]) * s, cc + np.array([0.16, 0.16, 0.16]) * s, 0.0030 * s, relax_iters=2)
        bind(new("cap", Vc, Qc, [CM]), arm, {"head": 1.0}, None)
    if cfg.get("hood"):           # パーカー：首の後ろのフードと、胸のひも
        HM = M["knit"]; SM = _solid("Hoodie string", C.get("string", "#F1EEE6"), 0.6)
        hm = _sdf.Model(); hm.add(_sdf.ellipsoid((0, 0.165, 1.060), (0.125, 0.065, 0.080), hgen.rot(-25, 0, 0)), "hood")
        Vh, Qh = _sdf.mesh(hm, np.array([-0.2, 0.05, 0.95]), np.array([0.2, 0.28, 1.17]), 0.004, relax_iters=2)
        ob = new("hood", Vh, Qh, [HM], attrs={"rest": ("FLOAT_VECTOR", Vh)}); bind(ob, arm, {"chest": 1.0}, None)
        for sx in (1, -1):
            a = np.array([sx * 0.028, -0.046, 1.040]); b_ = np.array([sx * 0.034, -0.090, 0.910])
            sm = _sdf.Model(); sm.add(_sdf.cone(a, b_, 0.0042, 0.0040), "string"); sm.add(_sdf.sphere(b_ + np.array([0, -0.001, -0.004]), 0.0065), "tip", k=0.003)
            Vs, Qs = _sdf.mesh(sm, np.minimum(a, b_) - 0.03, np.maximum(a, b_) + 0.03, 0.0012, relax_iters=1)
            bind(new("string." + ("L" if sx > 0 else "R"), Vs, Qs, [SM]), arm, {"chest": 1.0}, None)


def make_phone(name, coll=None, screen_img=None, S=1.0, style="real"):
    """スマホ：0.072×0.150×0.0085m。画面は光る（画像があれば貼る）"""
    import bmesh
    coll = coll or bpy.context.scene.collection
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.072, 0.150, 0.0085), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = 0.0035; bv.segments = 4; bv.limit_method = "NONE"
    me.materials.append(shared_mats(S, style)["phone"]); me.shade_smooth()
    # 画面
    sm = bpy.data.meshes.new(name + " screen"); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5); bmesh.ops.scale(bm, vec=(0.066, 0.142, 1), verts=bm.verts)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops: l[uv].uv = (l.vert.co.x / 0.066 + 0.5, l.vert.co.y / 0.142 + 0.5)
    bm.to_mesh(sm); bm.free()
    so = bpy.data.objects.new(name + " screen", sm); coll.objects.link(so); so.parent = ob; so.location = (0, 0, 0.00430)
    m = bpy.data.materials.new(name + " screen"); nt = NT(m)
    em = nt.n("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.6
    if screen_img:
        tx = nt.n("ShaderNodeTexImage"); tx.image = bpy.data.images.load(screen_img); nt.l(tx.outputs["Color"], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = (0.55, 0.78, 1.0, 1)
    gl = nt.n("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.05
    ad = nt.n("ShaderNodeAddShader"); nt.l(em.outputs[0], ad.inputs[0]); nt.l(gl.outputs[0], ad.inputs[1])
    o = nt.n("ShaderNodeOutputMaterial"); nt.l(ad.outputs[0], o.inputs[0])
    sm.materials.append(m)
    return ob, so


HERO = dict(quality="hero", earbuds=True, head=dict(), hair=dict(style="short"), body=dict(),
            colors=dict(skin="#E8B596", hair="#2B1F19", iris1="#3E2818", iris2="#7A5634", top="#2F8A86", pants="#2A303C",
                        shoe="#ECEAE4", sole="#D9D3C8"))
