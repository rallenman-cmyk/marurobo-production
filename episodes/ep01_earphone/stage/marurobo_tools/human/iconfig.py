# 線画アイコン風の人（決定版：点の目＋服の色分け）
# 白い頭と手足、上着とズボンだけ色。輪郭線は Freestyle（画面上で一定の太さ）か、裏返しの殻（Solidify）
# 部品を分けて作る：上着・腰（ズボン）・腕・手・脚・足・頭（首ごと）・目・イヤホン。主人公だけ目印の服装
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
import hgen, hbuild, sdf
from hbuild import srgb, NT, mk_mesh, bind

HEM_P0 = np.array([0, 0.06, 0.632]); HEM_N = hgen.norm((0, -0.2, 1.0))

# 乗客：落ち着いた色（主人公の青緑が目立つように）
MUTED_TOPS = ["#8C9096", "#B8A88F", "#71829A", "#A88272", "#7F8E7C", "#5F6672", "#C4BAA9", "#8B82A0", "#6E625A"]
MUTED_PANTS = ["#4B505A", "#6A6157", "#3F4653", "#5B5B5D", "#55504A"]
HERO_OUTFITS = {
    "beanie": dict(label="① ニット帽", note="からし色のニット帽。頭の形が変わるので遠くからでも主人公と分かる。耳とイヤホンは出しておく"),
    "cap": dict(label="② キャップ", note="からし色のキャップ（つばが前）。横顔でもつばで分かる。目が少し隠れやすい"),
    "scarf": dict(label="③ マフラー", note="からし色のマフラー。頭は他の人と同じで、首まわりの色で見分ける。顔まわりがいちばん見やすい"),
}
HERO_COLORS = dict(top="#2A9D8F", pants="#34486E", accent="#E3AE3A", string="#F4F1E8", skin="#F4D2B5")
SKINS = ["#F4D2B5", "#E9BE9A", "#D9A880", "#BC8A66", "#94654A", "#F1CDB0"]   # 乗客の肌の色（いろいろ）

_MATS = {}


def toon_mat(hexc, shade=0.86):
    """2段階の陰（光の当たる所＝元の色、陰＝少し暗い色）。同じ色は全員で共有"""
    key = ("toon", hexc, shade)
    if key in _MATS: return _MATS[key]
    m = bpy.data.materials.new(f"Icon {hexc}"); nt = NT(m)
    d = nt.n("ShaderNodeBsdfDiffuse"); s2r = nt.n("ShaderNodeShaderToRGB"); nt.l(d.outputs[0], s2r.inputs[0])
    bw = nt.n("ShaderNodeRGBToBW"); nt.l(s2r.outputs[0], bw.inputs[0])
    cr = nt.n("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    el = cr.color_ramp.elements; c = srgb(hexc)
    el[0].position = 0.0; el[0].color = (*[x * shade for x in c], 1); el[1].position = 0.16; el[1].color = (*c, 1)
    nt.l(bw.outputs[0], cr.inputs[0])
    em = nt.n("ShaderNodeEmission"); nt.l(cr.outputs[0], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
    o = nt.n("ShaderNodeOutputMaterial"); nt.l(em.outputs[0], o.inputs[0])
    _MATS[key] = m; return m


PBR = {  # 3Dの見た目：材質の種類ごとのつや・光の透け
    "skin": dict(rough=0.50, spec=0.35, sss=0.12, sss_r=(1.0, 0.45, 0.30), sss_s=0.004),
    "cloth": dict(rough=0.74, spec=0.30, sheen=0.45, sheen_r=0.5),
    "white": dict(rough=0.50, spec=0.40),
    "acc": dict(rough=0.62, spec=0.35, sheen=0.25, sheen_r=0.5),
    "string": dict(rough=0.60, spec=0.30),
    "bud": dict(rough=0.20, spec=0.60, coat=0.40, coat_r=0.15),
    "eye": dict(rough=0.10, spec=0.70, coat=0.60, coat_r=0.05),
    "mouth": dict(rough=0.55, spec=0.30),
    "pict": dict(rough=0.42, spec=0.45, coat=0.20, coat_r=0.25),      # ピクトグラム：つやの少しある樹脂の人形
}


def pbr_mat(hexc, kind):
    """3Dの材質（光と影で立体に見せる）。同じ色・種類は全員で共有"""
    key = ("pbr", hexc, kind)
    if key in _MATS: return _MATS[key]
    from hbuild import principled
    m = bpy.data.materials.new(f"Fig {kind} {hexc}"); nt = NT(m)
    principled(nt, base=srgb(hexc), **PBR[kind])
    _MATS[key] = m; return m


def flat_mat(hexc, cull=False):
    key = ("flat", hexc, cull)
    if key in _MATS: return _MATS[key]
    m = bpy.data.materials.new(f"Icon flat {hexc}"); nt = NT(m)
    em = nt.n("ShaderNodeEmission"); em.inputs["Color"].default_value = (*srgb(hexc), 1); em.inputs["Strength"].default_value = 1.0
    o = nt.n("ShaderNodeOutputMaterial"); nt.l(em.outputs[0], o.inputs[0]); m.use_backface_culling = cull
    _MATS[key] = m; return m


def add_outline(ob, width, hexc="#111111"):
    """裏返しの殻：外側へ width だけ太らせ、裏側だけを黒で描く（Freestyle を使わない時用）"""
    lm = flat_mat(hexc, cull=True); ob.data.materials.append(lm); idx = len(ob.data.materials) - 1
    md = ob.modifiers.new("Outline", "SOLIDIFY"); md.thickness = width; md.offset = 1.0
    md.use_flip_normals = True; md.use_rim = False; md.material_offset = idx
    return md


def _hands(B, J):
    hands = {}
    for sd, sx in (("L", 1), ("R", -1)):
        m_h, chains = hgen.hand_local(B); o, R = hgen.hand_frame(J, sd, sx)
        Pm = hgen.Placed(m_h, o, R, mirror=(sd == "L"))
        hands[sd] = dict(chains={f: dict(pts=[Pm.to_char(p) for p in ch["pts"]], z=[hgen.norm(Pm.to_char(z) - Pm.to_char(np.zeros(3))) for z in ch["z"]])
                                 for f, ch in chains.items()},
                         mcp_mid=Pm.to_char(np.array([-0.008, 0.098, 0.0])), dorsal=R[:, 2], palm=Pm.to_char(np.array([0, 0.05, 0.0])), R=R)
    return hands


def _part(prims, lo, hi, h, relax=3):
    m = sdf.Model(); m.prims = [dict(f=f, label=l, k=k, bones=b, group="g") for (f, l, k, b) in prims]
    V, Q = sdf.mesh(m, np.asarray(lo, float), np.asarray(hi, float), h, relax_iters=relax)
    bones = sorted({b for pr in m.prims for b in pr["bones"]})
    W = sdf.prim_weights(m, V, Q, bones, sigma=0.018) if len(bones) > 1 else None
    return V, Q, W, bones


def make_icon(name, colors, outfit=None, coll=None, S=1.0, quality=1.0, outline=None, look="3d", neck=True, Rh=0.122, hc_z=1.300):
    """colors: top / pants（/ accent / string）。outfit: None（乗客）か "beanie" / "cap" / "scarf"（主人公：フード付きパーカー＋目印）
    look="pict"：ピクトグラムの3D。全身1色（colors["body"]）、顔なし（colors["eyes"]=True で点の目）。neck=False で頭を体から離す"""
    coll = coll or bpy.context.scene.collection
    B = dict(hgen.BODY); J = hgen.skeleton(B); hands = _hands(B, J)
    hc = np.array([0, 0.045, hc_z]); kH = Rh / 0.122          # 頭の大きさの倍率（目・イヤホン・帽子も合わせる）
    pict = look == "pict"; use_eyes = (not pict) or colors.get("eyes", False)
    eyes = [hc + hgen.norm((sx * 0.30, -0.95, 0.06)) * Rh * 0.98 for sx in (1, -1)]
    brows = [e + np.array([0, -0.004, 0.035]) for e in eyes]
    # 目の骨は頭の中心に置く：回すと点の目が顔の表面をすべる（漫画のように目線が動く）
    bl = hgen.bone_list(J, [hc + np.array([0, 0, 0.0]), hc + np.array([0, 0, 0.0])], brows, hands,
                        hair=(hc + np.array([0, 0.02, 0.09]), hc + np.array([0, 0.06, 0.09])))
    arm = hbuild.build_armature(name, bl, coll); arm.data.display_type = "STICK"
    h = 0.0065 / quality
    def MAT(hexc, kind, shade=0.82):
        if pict: return pbr_mat(hexc, "pict" if kind in ("cloth", "skin", "white", "acc") else kind)
        return pbr_mat(hexc, kind) if look == "3d" else toon_mat(hexc, shade)
    if pict:
        WHITE = TOP = PANTS = SKIN = MAT(colors["body"], "cloth")
    else:
        WHITE = MAT("#F2F1EC" if look == "3d" else "#FFFFFF", "white", 0.86); TOP = MAT(colors["top"], "cloth", 0.80); PANTS = MAT(colors["pants"], "cloth", 0.80)
        SKIN = MAT(colors.get("skin", "#F4D2B5"), "skin", 0.84)
    objs = {}

    def put(nm, V, Q, mat_, W=None, bones=None, bone=None, line=1.0):
        ob = mk_mesh(f"{name} {nm}", V, Q, coll=coll, mats=[mat_], attrs={"rest": ("FLOAT_VECTOR", V)})
        if W is not None: bind(ob, arm, W, bones)
        else: bind(ob, arm, {bone or bones[0]: 1.0}, None)
        if outline: add_outline(ob, outline * line)
        objs[nm] = ob; return ob

    def plane(p): return (p - HEM_P0) @ HEM_N
    torso = sdf.cone((0, 0.070, 0.640), (0, 0.080, 0.900), 0.136, 0.150)
    shoulders = sdf.cone((0.16, 0.078, 1.005), (-0.16, 0.078, 1.005), 0.062, 0.062)
    top_prims = [(lambda p: smax_clip(torso(p), p), "torso", 0.0, {"spine": 0.5, "chest": 0.5}),
                 (shoulders, "shoulders", 0.07, {"chest": 1.0})]
    def smax_clip(d, p): return sdf.smax(d, -(plane(p) + 0.004), 0.006)
    if outfit and not pict:  # パーカー：首の後ろにフード（たまったかたまり）
        top_prims.append((sdf.ellipsoid((0, 0.150, 1.035), (0.118, 0.062, 0.075), hgen.rot(-25, 0, 0)), "hood", 0.03, {"chest": 1.0}))
    V, Q, W, bones = _part(top_prims, (-0.30, -0.15, 0.55), (0.30, 0.28, 1.12), h)
    put("top", V, Q, TOP, W, bones)
    V, Q, W, bones = _part([(sdf.ellipsoid((0, 0.075, 0.600), (0.148, 0.120, 0.110)), "pelvis", 0.0, {"hips": 1.0})], (-0.25, -0.12, 0.45), (0.25, 0.25, 0.75), h)
    put("hips", V, Q, PANTS, W, bones)
    for sd, sx in (("L", 1), ("R", -1)):
        sh, el, wr = J["shoulder." + sd], J["elbow." + sd], J["wrist." + sd]
        V, Q, W, bones = _part([(sdf.cone(sh, el, 0.050, 0.045), "uarm", 0.0, {"upper_arm." + sd: 1.0}),
                                (sdf.cone(el, wr, 0.045, 0.041), "farm", 0.012, {"forearm." + sd: 1.0})],
                               np.minimum(sh, wr) - 0.12, np.maximum(sh, wr) + 0.12, h)
        put("arm." + sd, V, Q, TOP, W, bones)
        hd = hands[sd]
        V, Q, W, bones = _part([(sdf.ellipsoid(hd["palm"] + hd["R"][:, 1] * 0.012, (0.042, 0.054, 0.029), hd["R"]), "hand", 0.0, {"hand." + sd: 1.0})],
                               hd["palm"] - 0.09, hd["palm"] + 0.09, h * 0.8)
        put("hand." + sd, V, Q, SKIN, bones=bones)
        hp, kn, an = J["hip." + sd], J["knee." + sd], J["ankle." + sd]
        V, Q, W, bones = _part([(sdf.cone(hp, kn, 0.074, 0.062), "thigh", 0.0, {"thigh." + sd: 1.0}),
                                (sdf.cone(kn, an + np.array([0, 0, 0.03]), 0.060, 0.054), "shin", 0.015, {"shin." + sd: 1.0})],
                               np.minimum(hp, an) - 0.12, np.maximum(hp, an) + 0.12, h)
        put("leg." + sd, V, Q, PANTS, W, bones)
        fwd = hgen.norm((J["ball." + sd] - an) * np.array([1, 1, 0])); Rf = np.stack([np.cross(fwd, [0, 0, 1.0]), fwd, [0, 0, 1.0]], 1)
        fc = an + fwd * 0.060 + np.array([0, 0, -0.043])
        V, Q, W, bones = _part([(sdf.ellipsoid(fc, (0.058, 0.105, 0.043), Rf), "foot", 0.0, {"foot." + sd: 1.0})], fc - 0.14, fc + 0.14, h)
        put("foot." + sd, V, Q, WHITE, bones=bones)
    # 頭（首ごと）
    hp_ = [(sdf.sphere(hc, Rh), "head", 0.0, {"head": 1.0})]
    if neck:
        hp_.append((sdf.cone(J["neck"] + np.array([0, 0, -0.03]), J["head"] + np.array([0, -0.003, 0.02]), 0.042, 0.040), "neck", 0.02, {"neck": 1.0}))
    V, Q, W, bones = _part(hp_, hc - np.array([0.2, 0.2, 0.36]), hc + np.array([0.2, 0.2, 0.2]), 0.0055 / quality, relax=2)
    put("head", V, Q, SKIN, W, bones)
    # 点の目（黒）：目の骨（頭の中心）で顔の上を動く。シェイプキー：まばたき（縦につぶす）・見開き（少し大きく）
    DOT = MAT("#141414", "eye") if look in ("3d", "pict") else flat_mat("#111111"); HL = flat_mat("#FFFFFF")
    for i, sd in enumerate(("L", "R") if use_eyes else ()):
        e = eyes[i]; n = hgen.norm(e - hc); x = hgen.norm(np.cross([0, 0, 1.0], n)); y = np.cross(n, x); R = np.stack([x, y, n], 1)
        U, Ff = hgen.uv_sphere(1.0, 24, 14); ctr = e + n * 0.002; sxx = 1 if sd == "L" else -1
        def shape(sx_, sy_):
            eye_v = (U * np.array([0.013 * sx_, 0.019 * sy_, 0.0065]) * kH) @ R.T + ctr
            if look not in ("3d", "pict"): return eye_v
            hl_c = ctr + (x * (-0.0042 * sxx) * sx_ + y * 0.0062 * sy_) * kH + n * 0.0050 * kH
            hl_v = (U * np.array([0.0034 * sx_, 0.0040 * sy_, 0.0016]) * kH) @ R.T + hl_c
            return np.concatenate([eye_v, hl_v])
        hl3 = look in ("3d", "pict")
        F2 = list(Ff) + ([tuple(int(k) + len(U) for k in f) for f in Ff] if hl3 else [])
        midx = [0] * len(Ff) + ([1] * len(Ff) if hl3 else [])
        ob = mk_mesh(f"{name} eye.{sd}", shape(1, 1), F2, coll=coll, mats=[DOT, HL] if hl3 else [DOT], mat_idx=midx)
        bind(ob, arm, {"eye." + sd: 1.0}, None)
        ob.shape_key_add(name="Basis")
        for nm_, (a_, b_) in (("blink", (1.15, 0.10)), ("wide", (1.22, 1.22))):
            kb = ob.shape_key_add(name=nm_, from_mix=False); kb.data.foreach_set("co", shape(a_, b_).ravel().astype(np.float32))
        objs["eye." + sd] = ob
    # 口：顔の球面に貼った形（ふだん小さな笑顔、シェイプキーで o・開く・まっすぐ）
    mouth = None
    if colors.get("mouth", False):   # 口なしに決定（点の目だけ）。入れたいときは colors["mouth"]=True
        D, MF = hgen.mouth_disc(4, 28)
        SH = {"smile": (0.150, 0.026, 0.060, -0.300), "o": (0.060, 0.066, 0.0, -0.320), "open": (0.105, 0.055, 0.015, -0.315),
              "flat": (0.120, 0.024, 0.0, -0.300)}      # 横の半幅・縦の半幅（角度ラジアン）・口角の上がり・高さ
        def mouth_v(nm_):
            w_, h_, c_, b0 = SH[nm_]
            a = D[:, 0] * w_; b = b0 + D[:, 1] * h_ + c_ * D[:, 0] ** 2
            d = np.stack([np.sin(a) * np.cos(b), -np.cos(a) * np.cos(b), np.sin(b)], 1)
            return hc + d * (Rh + 0.0012)
        MM = MAT("#4A2626", "mouth", 0.80) if look == "3d" else flat_mat("#2A1414")
        mouth = mk_mesh(f"{name} mouth", mouth_v("smile"), MF, coll=coll, mats=[MM]); bind(mouth, arm, {"head": 1.0}, None)
        mouth.shape_key_add(name="Basis")
        for nm_ in ("o", "open", "flat"):
            kb = mouth.shape_key_add(name=nm_, from_mix=False); kb.data.foreach_set("co", mouth_v(nm_).ravel().astype(np.float32))
        objs["mouth"] = mouth
    # イヤホン
    for sd, sx in (("L", 1), ("R", -1)):
        side = hc + np.array([sx * Rh * 0.99, 0.010, -0.010]); kb_ = kH ** 0.8
        V, Q, W, bones = _part([(sdf.sphere(side + np.array([sx * 0.004, 0, 0]) * kb_, 0.0125 * kb_), "bud", 0.0, {"head": 1.0}),
                                (sdf.cone(side + np.array([sx * 0.006, -0.004, -0.006]) * kb_, side + np.array([sx * 0.009, -0.012, -0.042]) * kb_,
                                          0.0055 * kb_, 0.0050 * kb_), "stem", 0.004, {"head": 1.0})],
                               side - 0.07, side + 0.05, 0.0012, relax=1)
        put("bud." + sd, V, Q, MAT("#F7F7F5", "bud", 0.86) if look in ("3d", "pict") else WHITE, bones=bones, line=0.55)
    # 主人公の目印
    if outfit:
        ACC = MAT(colors.get("accent", "#E3AE3A"), "acc", 0.80); STR = MAT(colors.get("string", "#F4F1E8"), "string", 0.86)
        for sd, sx in ((("L", 1), ("R", -1)) if not pict else ()):   # パーカーのひも
            a = np.array([sx * 0.030, -0.030, 1.000]); b_ = np.array([sx * 0.036, -0.078, 0.900])
            V, Q, W, bones = _part([(sdf.cone(a, b_, 0.0065, 0.0060), "string", 0.0, {"chest": 1.0}),
                                    (sdf.sphere(b_ + np.array([0, -0.002, -0.006]), 0.010), "tip", 0.004, {"chest": 1.0})],
                                   np.minimum(a, b_) - 0.04, np.maximum(a, b_) + 0.04, 0.0018, relax=1)
            put("string." + sd, V, Q, STR, bones=bones, line=0.6)
        if outfit == "beanie":   # ニット帽：耳より上をおおう半球＋折り返し＋ぼんぼり
            def beanie(p):
                q = p - hc
                cap = np.sqrt((q * q).sum(1)) - Rh * 1.055
                return sdf.smax(cap, -(q @ hgen.norm((0, 0.18, 1.0)) - 0.020), 0.006)
            band = sdf.torus(hc + hgen.norm((0, 0.18, 1.0)) * 0.026, np.stack([[1, 0, 0], hgen.norm(np.cross(hgen.norm((0, 0.18, 1.0)), [1, 0, 0])), hgen.norm((0, 0.18, 1.0))], 1), Rh * 1.02, 0.016)
            V, Q, W, bones = _part([(beanie, "beanie", 0.0, {"head": 1.0}), (band, "band", 0.01, {"head": 1.0}),
                                    (sdf.sphere(hc + hgen.norm((0, 0.15, 1.0)) * (Rh * 1.10 + 0.020), 0.030), "pom", 0.012, {"head": 1.0})],
                                   hc - 0.2, hc + 0.22, 0.0045)
            put("hat", V, Q, ACC, bones=bones)
        elif outfit == "cap":    # キャップ：頭の上半分＋前のつば
            def crown(p):
                q = p - hc
                return sdf.smax(np.sqrt((q * q).sum(1)) - Rh * 1.045, -(q @ hgen.norm((0, 0.10, 1.0)) - 0.035 * kH), 0.005)
            brim = sdf.ellipsoid(hc + np.array([0, -0.115, 0.050]) * kH, (0.105 * kH, 0.085 * kH, 0.010), hgen.rot(-12, 0, 0))
            V, Q, W, bones = _part([(crown, "crown", 0.0, {"head": 1.0}), (brim, "brim", 0.012, {"head": 1.0}),
                                    (sdf.sphere(hc + np.array([0, 0.0, Rh * 1.05]), 0.012), "button", 0.004, {"head": 1.0})],
                                   hc - 0.24, hc + 0.22, 0.0040)
            put("hat", V, Q, ACC, bones=bones)
        elif outfit == "scarf":  # マフラー：首に巻いた輪＋前に垂れる端
            nax = hgen.norm(J["head"] - J["neck"]); ctr = J["neck"] + nax * 0.045
            Rn = np.stack([[1, 0, 0], hgen.norm(np.cross(nax, [1, 0, 0])), nax], 1)
            V, Q, W, bones = _part([(sdf.torus(ctr, Rn, 0.060, 0.030), "wrap", 0.0, {"neck": 0.6, "chest": 0.4}),
                                    (sdf.rbox(ctr + np.array([0.035, -0.075, -0.095]), (0.033, 0.012, 0.085), 0.010, hgen.rot(12, 0, -8)), "tail", 0.02, {"chest": 1.0})],
                                   ctr - 0.2, ctr + 0.15, 0.0045)
            put("scarf", V, Q, ACC, W, bones)
    arm.scale = (S, S, S)
    return dict(arm=arm, objs=objs, J=J, hc=hc, hf=dict(eye=[e - hc for e in eyes], ear=[np.array([sx * Rh, 0.01, -0.01]) for sx in (1, -1)]),
                s=1.0, P=dict(lid_up=30.0, lid_lo=33.0), mouth=mouth, lid_up=30.0, lid_lo=33.0, Rh=Rh, dots=bool(use_eyes), eye_gain=0.45,
                bud_R=hc + np.array([-Rh * 0.99 - 0.004, 0.010, -0.010]))


def freestyle(scene, view_layer, thickness_px, collection=None):
    """輪郭線：Freestyle（画面上で一定の太さ）。collection を渡すと、その中の物だけに線を引く"""
    scene.render.use_freestyle = True; scene.render.line_thickness_mode = "ABSOLUTE"; scene.render.line_thickness = 1.0
    fs = view_layer.freestyle_settings; fs.crease_angle = math.radians(134); fs.use_culling = False
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("Lines")
    ls.select_by_visibility = True; ls.visibility = "VISIBLE"; ls.select_by_edge_types = True
    ls.select_silhouette = True; ls.select_border = True; ls.select_crease = False; ls.select_contour = True; ls.select_external_contour = True
    if collection is not None:
        ls.select_by_collection = True; ls.collection = collection; ls.collection_negation = "INCLUSIVE"
    lst = ls.linestyle; lst.color = (0.06, 0.06, 0.06); lst.thickness = thickness_px; lst.thickness_position = "CENTER"
    lst.chaining = "PLAIN"; lst.use_same_object = False
    return ls
