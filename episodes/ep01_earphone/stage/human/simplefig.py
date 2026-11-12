# 簡単な形の人（棒人間・ピクト・マメ・デッサン人形）。骨格と動きはこれまでの人物と同じ
# 部品は単純な形（球・両端が丸い筒・角を丸めた箱）で、それぞれ1本の骨に固定する（曲がる所は関節の球で隠す）
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
import hgen, hbuild, sdf
from hbuild import srgb, NT, principled, mk_mesh, bind


def _frame(z):
    z = z / np.linalg.norm(z)
    x = np.cross(z, [0, 0, 1.0])
    if np.linalg.norm(x) < 1e-6: x = np.cross(z, [0, 1.0, 0])
    x /= np.linalg.norm(x); return x, np.cross(z, x), z


def lathe(rings, x, y, nseg=24):
    V = []; idx = []
    for c, r in rings:
        if r < 1e-7: idx.append([len(V)]); V.append(np.asarray(c, float)); continue
        row = []
        for j in range(nseg):
            a = 2 * math.pi * j / nseg; row.append(len(V)); V.append(np.asarray(c) + (x * math.cos(a) + y * math.sin(a)) * r)
        idx.append(row)
    F = []
    for i in range(len(idx) - 1):
        A, B = idx[i], idx[i + 1]
        for j in range(nseg):
            a0 = A[0] if len(A) == 1 else A[j]; a1 = A[0] if len(A) == 1 else A[(j + 1) % nseg]
            b0 = B[0] if len(B) == 1 else B[j]; b1 = B[0] if len(B) == 1 else B[(j + 1) % nseg]
            if len(A) == 1: F.append((a0, b1, b0))
            elif len(B) == 1: F.append((a0, a1, b0))
            else: F.append((a0, a1, b1, b0))
    return np.array(V), F


def capsule(a, b, r1, r2=None, nseg=24, ncap=6):
    """両端が半球の筒（a→b、太さ r1→r2）"""
    r2 = r1 if r2 is None else r2
    a = np.asarray(a, float); b = np.asarray(b, float); x, y, z = _frame(b - a)
    rings = []
    for i in range(ncap + 1):
        t = -math.pi / 2 + (math.pi / 2) * i / ncap; rings.append((a + z * r1 * math.sin(t), r1 * math.cos(t)))
    for i in range(0, ncap + 1):
        t = (math.pi / 2) * i / ncap; rings.append((b + z * r2 * math.sin(t), r2 * math.cos(t)))
    return lathe(rings, x, y, nseg)


def ellipsoid_mesh(c, r, R=None, nu=32, nv=20):
    V, F = hgen.uv_sphere(1.0, nu, nv)
    V = V * np.asarray(r, float)
    if R is not None: V = V @ np.asarray(R).T
    return V + np.asarray(c, float), F


def sdf_mesh(model, lo, hi, h):
    V, Q = sdf.mesh(model, lo, hi, h, relax_iters=3)
    return V, Q


def mat(name, hexc, rough=0.5, spec=0.4, coat=0.0, wood=False):
    m = bpy.data.materials.new(name); nt = NT(m)
    b = principled(nt, base=srgb(hexc), rough=rough, spec=spec, coat=coat, coat_r=0.25)
    if wood:  # 木目（帯状の模様＋ゆらぎ）
        tc = nt.n("ShaderNodeAttribute", attribute_name="rest")
        wv = nt.n("ShaderNodeTexWave", wave_type="RINGS", rings_direction="Z", i_Scale=38.0, i_Distortion=6.0, i_Detail=2.0)
        nt.l(tc.outputs["Vector"], wv.inputs["Vector"])
        mx = nt.n("ShaderNodeMix", data_type="RGBA"); mx.inputs[6].default_value = (*[c * 0.78 for c in srgb(hexc)], 1); mx.inputs[7].default_value = (*srgb(hexc), 1)
        nt.l(wv.outputs["Fac"], mx.inputs[0]); nt.l(mx.outputs[2], b.inputs["Base Color"])
    return m


KINDS = ("stick", "picto", "bean", "doll")
LABELS = {"stick": "① 棒人間", "picto": "② ピクト", "bean": "③ マメ", "doll": "④ デッサン人形"}
NOTES = {"stick": "球の頭と細い棒の手足。点の目だけ。いちばん記号的で、まるロボがいちばん目立つ",
         "picto": "案内表示の人の形。顔なし・1人1色。頭と体のすき間が目印。誰が何をしているかが一目で分かる",
         "bean": "頭と体がひと続きの豆の形に、大きな点の目。かわいく、表情は目と体の傾きで出す",
         "doll": "木のデッサン人形。顔なしで、関節の球が見える。「体の仕組み・動きの物理」を見せるのに向く"}


def make_figure(name, kind, colors, coll=None, S=1.0):
    coll = coll or bpy.context.scene.collection
    B = dict(hgen.BODY); J = hgen.skeleton(B)
    top, pants, skin = colors["top"], colors["pants"], colors.get("skin", "#F1C9A5")
    # 頭の中心と大きさ
    if kind == "stick": hc = np.array([0, 0.040, 1.300]); Rh = 0.115
    elif kind == "picto": hc = np.array([0, 0.045, 1.305]); Rh = 0.105
    elif kind == "bean": hc = np.array([0, 0.050, 1.150]); Rh = 0.180
    else: hc = np.array([0, 0.040, 1.275]); Rh = 0.095
    # 目（点）の位置：顔の前の面
    eyes = []
    for sx in (1, -1):
        d = hgen.norm((sx * 0.33, -0.94, 0.10 if kind != "bean" else 0.18))
        eyes.append(hc + d * Rh * (0.97 if kind != "doll" else 1.1))
    brows = [e + np.array([0, -0.005, 0.04]) for e in eyes]
    hands = {}
    for sd, sx in (("L", 1), ("R", -1)):
        m_h, chains = hgen.hand_local(B); o, R = hgen.hand_frame(J, sd, sx)
        Pm = hgen.Placed(m_h, o, R, mirror=(sd == "L"))
        hands[sd] = dict(chains={f: dict(pts=[Pm.to_char(p) for p in ch["pts"]], z=[hgen.norm(Pm.to_char(z) - Pm.to_char(np.zeros(3))) for z in ch["z"]])
                                 for f, ch in chains.items()},
                         mcp_mid=Pm.to_char(np.array([-0.008, 0.098, 0.0])), dorsal=R[:, 2], palm=Pm.to_char(np.array([0, 0.05, 0.0])), R=R)
    bl = hgen.bone_list(J, eyes, brows, hands, hair=(hc + np.array([0, 0.02, 0.09]), hc + np.array([0, 0.06, 0.09])))
    arm = hbuild.build_armature(name, bl, coll); arm.data.display_type = "STICK"
    objs = {}
    M = {}

    def part(nm, V, F, material, bone=None, weights=None, bones=None, smooth=True):
        ob = mk_mesh(f"{name} {nm}", V, F, coll=coll, mats=[material], smooth=smooth, attrs={"rest": ("FLOAT_VECTOR", V)})
        if weights is not None: bind(ob, arm, weights, bones)
        else: bind(ob, arm, {bone: 1.0}, None)
        objs[nm] = ob; return ob

    sides = (("L", 1), ("R", -1))
    if kind == "stick":
        M["head"] = mat(name + " head", skin, 0.55, 0.35); M["top"] = mat(name + " top", top, 0.5, 0.4); M["pants"] = mat(name + " pants", pants, 0.5, 0.4)
        M["dot"] = mat(name + " dot", "#141414", 0.15, 0.6); M["white"] = mat(name + " white", "#FFFFFF", 0.3, 0.5)
        r = 0.020; rj = 0.024
        V, F = ellipsoid_mesh(hc, (Rh, Rh, Rh)); part("head", V, F, M["head"], "head")
        for i, (sd, sx) in enumerate(sides):   # 点の目（白い光の点つき）
            e = eyes[i]; n = hgen.norm(e - hc); Rm = np.stack(_frame(n), 1)
            V, F = ellipsoid_mesh(e + n * 0.003, (0.0135, 0.0175, 0.006), Rm); part("eye." + sd, V, F, M["dot"], "head")
            V, F = ellipsoid_mesh(e + n * 0.008 + np.array([sx * 0.004, 0, 0.007]), (0.004, 0.004, 0.003), Rm); part("hl." + sd, V, F, M["white"], "head")
        pts = [np.array([0, 0.068, 0.560]), J["spine"], J["chest"], J["neck"] + np.array([0, 0, -0.02]), J["head"]]
        for nm, a, b_, bone, mm in (("hips", pts[0], pts[1], "hips", "pants"), ("spine", pts[1], pts[2], "spine", "top"),
                                    ("chest", pts[2], pts[3], "chest", "top"), ("neck", pts[3], pts[4], "neck", "top")):
            V, F = capsule(a, b_, r); part("st_" + nm, V, F, M[mm], bone)
        for sd, sx in sides:
            sh, el, wr = J["shoulder." + sd], J["elbow." + sd], J["wrist." + sd]
            V, F = capsule(J["neck"] + np.array([0, 0.0, -0.035]), sh, r); part("clav." + sd, V, F, M["top"], "clav." + sd)
            V, F = capsule(sh, el, r); part("uarm." + sd, V, F, M["top"], "upper_arm." + sd)
            V, F = capsule(el, wr, r); part("farm." + sd, V, F, M["top"], "forearm." + sd)
            V, F = ellipsoid_mesh(hands[sd]["palm"], (0.030, 0.030, 0.030)); part("hand." + sd, V, F, M["head"], "hand." + sd)
            hp, kn, an = J["hip." + sd], J["knee." + sd], J["ankle." + sd]
            V, F = capsule(np.array([0, 0.068, 0.560]), hp, r); part("pel." + sd, V, F, M["pants"], "hips")
            V, F = capsule(hp, kn, r * 1.1); part("thigh." + sd, V, F, M["pants"], "thigh." + sd)
            V, F = capsule(kn, an, r * 1.1); part("shin." + sd, V, F, M["pants"], "shin." + sd)
            V, F = capsule(an + np.array([0, 0.01, -0.06]), J["toe." + sd] + np.array([0, 0.03, 0.0]), 0.026); part("foot." + sd, V, F, M["pants"], "foot." + sd)
            for jn, bone, mm in ((el, "upper_arm." + sd, "top"), (kn, "thigh." + sd, "pants")):
                V, F = ellipsoid_mesh(jn, (rj, rj, rj), nu=16, nv=10); part(f"j_{bone}_{jn[2]:.3f}", V, F, M[mm], bone)
    elif kind == "picto":
        M["body"] = mat(name + " body", top, 0.55, 0.35)
        V, F = ellipsoid_mesh(hc, (Rh, Rh, Rh)); part("head", V, F, M["body"], "head")
        m = sdf.Model()
        m.add(sdf.rbox((0, 0.080, 0.925), (0.150, 0.075, 0.150), 0.060), "chest", bones={"chest": 1}, group="torso")
        m.add(sdf.rbox((0, 0.075, 0.640), (0.125, 0.072, 0.095), 0.055), "pelvis", k=0.06, bones={"hips": 1}, group="torso")
        V, Q = sdf_mesh(m, (-0.25, -0.10, 0.48), (0.25, 0.22, 1.13), 0.006)
        W = sdf.prim_weights(m, V, Q, ["chest", "hips"], sigma=0.03)
        part("torso", V, Q, M["body"], weights=W, bones=["chest", "hips"])
        for sd, sx in sides:
            sh, el, wr = J["shoulder." + sd], J["elbow." + sd], J["wrist." + sd]
            V, F = capsule(sh, el, 0.042, 0.040); part("uarm." + sd, V, F, M["body"], "upper_arm." + sd)
            V, F = capsule(el, wr, 0.038, 0.035); part("farm." + sd, V, F, M["body"], "forearm." + sd)
            V, F = ellipsoid_mesh(hands[sd]["palm"], (0.040, 0.040, 0.040)); part("hand." + sd, V, F, M["body"], "hand." + sd)
            hp, kn, an = J["hip." + sd], J["knee." + sd], J["ankle." + sd]
            V, F = capsule(hp, kn, 0.058, 0.052); part("thigh." + sd, V, F, M["body"], "thigh." + sd)
            V, F = capsule(kn, an, 0.050, 0.046); part("shin." + sd, V, F, M["body"], "shin." + sd)
            V, F = capsule(an + np.array([0, 0.02, -0.045]), J["toe." + sd] + np.array([0, 0.02, -0.005]), 0.042); part("foot." + sd, V, F, M["body"], "foot." + sd)
    elif kind == "bean":
        M["body"] = mat(name + " body", top, 0.38, 0.45, coat=0.2); M["pants"] = mat(name + " pants", pants, 0.45, 0.4)
        M["dot"] = mat(name + " dot", "#121212", 0.1, 0.7); M["white"] = mat(name + " white", "#FFFFFF", 0.2, 0.5)
        M["cheek"] = mat(name + " cheek", "#F49A8A", 0.6, 0.3)
        m = sdf.Model()
        m.add(sdf.ellipsoid((0, 0.075, 0.640), (0.185, 0.165, 0.150)), "pelvis", bones={"hips": 1}, group="t")
        m.add(sdf.ellipsoid((0, 0.070, 0.860), (0.180, 0.155, 0.190)), "chest", k=0.10, bones={"chest": 1}, group="t")
        m.add(sdf.ellipsoid((0, 0.050, 1.140), (0.185, 0.170, 0.175)), "head", k=0.12, bones={"head": 1}, group="t")
        V, Q = sdf_mesh(m, (-0.25, -0.15, 0.45), (0.25, 0.27, 1.34), 0.006)
        W = sdf.prim_weights(m, V, Q, ["hips", "chest", "head"], sigma=0.05)
        part("body", V, Q, M["body"], weights=W, bones=["hips", "chest", "head"])
        for i, (sd, sx) in enumerate(sides):
            e = eyes[i]; n = hgen.norm(e - hc)
            Rm = np.stack(_frame(n), 1)
            V, F = ellipsoid_mesh(e + n * 0.004, (0.024, 0.031, 0.010), Rm); part("eye." + sd, V, F, M["dot"], "head")
            V, F = ellipsoid_mesh(e + n * 0.012 + np.array([sx * 0.007, 0, 0.012]), (0.007, 0.007, 0.004), Rm); part("hl." + sd, V, F, M["white"], "head")
            ck = hc + hgen.norm((sx * 0.58, -0.80, -0.12)) * Rh * 1.0
            V, F = ellipsoid_mesh(ck, (0.026, 0.016, 0.006), np.stack(_frame(hgen.norm(ck - hc)), 1)); part("cheek." + sd, V, F, M["cheek"], "head")
            sh, el, wr = J["shoulder." + sd] + np.array([-sx * 0.01, 0, -0.07]), J["elbow." + sd], J["wrist." + sd]
            V, F = capsule(sh, el, 0.030); part("uarm." + sd, V, F, M["body"], "upper_arm." + sd)
            V, F = capsule(el, wr, 0.030); part("farm." + sd, V, F, M["body"], "forearm." + sd)
            V, F = ellipsoid_mesh(hands[sd]["palm"], (0.036, 0.036, 0.036)); part("hand." + sd, V, F, M["body"], "hand." + sd)
            hp, kn, an = J["hip." + sd], J["knee." + sd], J["ankle." + sd]
            V, F = capsule(hp, kn, 0.060, 0.055); part("thigh." + sd, V, F, M["pants"], "thigh." + sd)
            V, F = capsule(kn, an, 0.052, 0.048); part("shin." + sd, V, F, M["pants"], "shin." + sd)
            V, F = capsule(an + np.array([0, 0.02, -0.045]), J["toe." + sd] + np.array([0, 0.02, -0.005]), 0.045); part("foot." + sd, V, F, M["body"], "foot." + sd)
    else:  # doll（デッサン人形）
        M["wood"] = mat(name + " wood", colors.get("wood", "#D9B48A"), 0.45, 0.45, wood=True)
        M["top"] = mat(name + " paint top", top, 0.42, 0.45, wood=True); M["pants"] = mat(name + " paint pants", pants, 0.42, 0.45, wood=True)
        M["joint"] = mat(name + " joint", "#B9895C", 0.4, 0.45, wood=True)
        R = hgen.rot(-10, 0, 0)
        V, F = ellipsoid_mesh(hc, (0.078, 0.092, 0.112), R); part("head", V, F, M["wood"], "head")
        V, F = capsule(J["neck"] + np.array([0, 0, -0.01]), J["head"] + np.array([0, -0.005, 0.03]), 0.030); part("neck", V, F, M["wood"], "neck")
        V, F = ellipsoid_mesh((0, 0.080, 0.905), (0.150, 0.090, 0.150)); part("chest", V, F, M["top"], "chest")
        V, F = ellipsoid_mesh(J["spine"] + np.array([0, 0, 0.0]), (0.075, 0.065, 0.060)); part("waist", V, F, M["joint"], "spine")
        V, F = ellipsoid_mesh((0, 0.075, 0.600), (0.135, 0.085, 0.085)); part("pelvis", V, F, M["pants"], "hips")
        for sd, sx in sides:
            sh, el, wr = J["shoulder." + sd], J["elbow." + sd], J["wrist." + sd]
            for jn, bone in ((sh, "upper_arm." + sd), (el, "forearm." + sd), (wr, "hand." + sd)):
                V, F = ellipsoid_mesh(jn, (0.033, 0.033, 0.033), nu=20, nv=12); part(f"j_{bone}", V, F, M["joint"], bone)
            V, F = capsule(sh + (el - sh) * 0.12, el - (el - sh) * 0.12, 0.040, 0.030); part("uarm." + sd, V, F, M["top"], "upper_arm." + sd)
            V, F = capsule(el + (wr - el) * 0.12, wr - (wr - el) * 0.12, 0.033, 0.024); part("farm." + sd, V, F, M["top"], "forearm." + sd)
            Rh_ = hands[sd]["R"]
            V, F = ellipsoid_mesh(hands[sd]["palm"] + Rh_[:, 1] * 0.012, (0.036, 0.060, 0.016), Rh_); part("hand." + sd, V, F, M["wood"], "hand." + sd)
            hp, kn, an = J["hip." + sd], J["knee." + sd], J["ankle." + sd]
            for jn, bone in ((hp, "thigh." + sd), (kn, "shin." + sd), (an, "foot." + sd)):
                V, F = ellipsoid_mesh(jn, (0.040, 0.040, 0.040), nu=20, nv=12); part(f"j_{bone}", V, F, M["joint"], bone)
            V, F = capsule(hp + (kn - hp) * 0.12, kn - (kn - hp) * 0.12, 0.055, 0.038); part("thigh." + sd, V, F, M["pants"], "thigh." + sd)
            V, F = capsule(kn + (an - kn) * 0.12, an - (an - kn) * 0.12, 0.040, 0.028); part("shin." + sd, V, F, M["pants"], "shin." + sd)
            V, F = capsule(an + np.array([0, 0.03, -0.05]), J["toe." + sd] + np.array([0, 0.02, -0.01]), 0.035, 0.030); part("foot." + sd, V, F, M["wood"], "foot." + sd)
    # イヤホン（左右の耳の位置＝頭の横）
    M["bud"] = mat(name + " earbud", "#F4F4F2", 0.22, 0.6, coat=0.4)
    for i, (sd, sx) in enumerate(sides):
        side = hc + np.array([sx * Rh * (1.0 if kind != "doll" else 0.85), 0.012, -0.005 if kind != "bean" else -0.0])
        V, F = ellipsoid_mesh(side + np.array([sx * 0.004, 0, 0]), (0.011, 0.012, 0.012)); part("bud." + sd, V, F, M["bud"], "head")
        V, F = capsule(side + np.array([sx * 0.006, -0.004, -0.006]), side + np.array([sx * 0.008, -0.012, -0.040]), 0.0045); part("stem." + sd, V, F, M["bud"], "head")
    arm.scale = (S, S, S)
    bud_R = hc + np.array([-Rh, 0.012, 0.0])
    return dict(arm=arm, objs=objs, J=J, hc=hc, hf=dict(eye=[e - hc for e in eyes], ear=[np.array([sx * Rh, 0.012, 0]) for sx in (1, -1)]),
                s=1.0, P=dict(lid_up=30.0, lid_lo=33.0), mouth=None, cfg=dict(kind=kind, colors=colors), lid_up=30.0, lid_lo=33.0, bud_R=bud_R, Rh=Rh)
