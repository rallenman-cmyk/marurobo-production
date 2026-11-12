# 巨大イヤホン v2：Codex版と同じ位置・大きさ（元の座標）で、なめらかな形と本物らしい材質に作り直す
#   体：耳に入る丸い頭（楕円体）＋軸（角を丸めた円柱。底は平ら）をなめらかにつなぐ（つなぎ目の丸み 1.6）
#   耳の先：頭から出た短い筒に、シリコンの耳の先（きのこ形。後ろは頭の丸みに沿う）をかぶせる。先の口から黒い網が見える
#   細部：センサーの小窓（黒いガラス、面とほぼ同じ高さ）・マイクの網目・軸の先の金属のふた・継ぎ目・頭の合わせ目（細い溝）
#   材質：つやのある白い樹脂（表面のコート＋わずかな透け）。光は太陽と空だけ（自分では光らない）
#   形は距離の式（SDF）から網目にして、cache/ に保存する（2回目からは読むだけ）
import os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "human"))
import sdf

VERSION = 4                                         # 形を変えたら上げる（古い cache を使わない）
HC = np.array([-2.2, 11.12, 14.75])                 # 頭の中心（元の座標）
TIP = np.array([-5.6, 10.2, 15.1])                  # 耳の先（元の EB_PTS の eb_tip と同じ）
D = (TIP - HC) / np.linalg.norm(TIP - HC)           # 耳の先の向き
HEAD_R = (3.40, 2.90, 3.45)
STEM_C = np.array([0.0, 11.12]); STEM_R = 1.38; Z0 = 0.36; Z_CAP = 1.02; Z_TOP = 12.6
GAP = 0.10                                          # 耳の先の後ろの縁と頭のすき間
S_FRONT = 5.20; R_MOUTH = 0.56; S_MOUTH = 4.90      # 耳の先の前の面・口の半径・口の底（頭の中心から D の向きの距離）


def rcyl(c_xy, r, z0, z1, rr):
    """角を丸めた円柱（底と上が平ら）。c_xy：中心、r：半径、rr：角の丸み"""
    cx, cy = c_xy; zc = 0.5 * (z0 + z1); hh = 0.5 * (z1 - z0)
    def f(p):
        q0 = np.sqrt((p[:, 0] - cx) ** 2 + (p[:, 1] - cy) ** 2) - r + rr; q1 = np.abs(p[:, 2] - zc) - hh + rr
        return np.sqrt(np.maximum(q0, 0) ** 2 + np.maximum(q1, 0) ** 2) + np.minimum(np.maximum(q0, q1), 0) - rr
    return f


def disc(c, n, r, t, rr=0.02):
    """向き n の円柱（厚さ t、角の丸み rr）"""
    c = np.asarray(c, float); n = np.asarray(n, float) / np.linalg.norm(n)
    def f(p):
        q = p - c; h = q @ n; rad = np.sqrt(np.maximum((q * q).sum(1) - h * h, 0))
        q0 = rad - r + rr; q1 = np.abs(h) - t / 2 + rr
        return np.sqrt(np.maximum(q0, 0) ** 2 + np.maximum(q1, 0) ** 2) + np.minimum(np.maximum(q0, q1), 0) - rr
    return f


def axial(s0, s1, r, rr):
    """耳の先の向き D の円柱（頭の中心から s0〜s1）"""
    return disc(HC + D * 0.5 * (s0 + s1), D, r, s1 - s0, rr)


def head_sdf(): return sdf.ellipsoid(HC, HEAD_R)


def body_sdf():
    head = head_sdf(); stem = rcyl(STEM_C, STEM_R, Z_CAP, Z_TOP, 0.30)
    nozzle = axial(2.3, 4.05, 1.10, 0.22)                              # 耳の先をはめる短い筒（ほとんど耳の先に隠れる）
    def f(p):
        d = sdf.smin(head(p), stem(p), 1.6)
        return sdf.smin(d, nozzle(p), 0.35)
    return f


def eartip_sdf():
    head = head_sdf()
    dome = sdf.cone(HC + D * 3.45, HC + D * 4.40, 1.85, 1.12)       # きのこ形（後ろが広い）
    def f(p):
        d = sdf.smax(dome(p), (p - HC) @ D - S_FRONT, 0.18)           # 前を平らに（角は丸く）
        d = sdf.smax(d, -(head(p) - GAP), 0.08)                       # 後ろは頭の丸みに沿う（すき間 GAP）
        mouth = axial(S_MOUTH, S_FRONT + 0.6, R_MOUTH, 0.0)
        return sdf.smax(d, -mouth(p), 0.05)                           # 先の口（音の出る穴）
    return f


def cap_sdf():
    return rcyl(STEM_C, STEM_R + 0.004, Z0, Z_CAP + 0.04, 0.22)


def surface_point(F, p0, it=12):
    """p0 から一番近い面の点と、その外向きの向き"""
    p = np.asarray(p0, float)[None, :]
    for _ in range(it):
        d = F(p); g = sdf.grad(F, p, 1e-3); g /= np.linalg.norm(g)
        p = p - d[:, None] * g
    g = sdf.grad(F, p, 1e-3)[0]; return p[0], g / np.linalg.norm(g)


def flush_patch(F, p0, half, depth=0.03, k=0.015):
    """面にほぼ同じ高さで埋めた楕円の板（小窓・網）。面の丸みに沿い、depth だけ出る。half＝(横, 縦) の半径"""
    p, n = surface_point(F, p0)
    a = np.cross(n, [0, 0, 1.0]); a = a / np.linalg.norm(a) if np.linalg.norm(a) > 1e-6 else np.array([1.0, 0, 0]); b = np.cross(n, a)
    ra, rb = half
    def f(q):
        v = q - p; x = v @ a; y = v @ b
        e = (np.sqrt((x / ra) ** 2 + (y / rb) ** 2) - 1.0) * min(ra, rb)
        fb = F(q)
        return np.maximum(sdf.smax(fb - depth, e, k), -(fb + 0.12))
    return f, p, n


def mesh_cached(name, F, lo, hi, h):
    os.makedirs(os.path.join(HERE, "cache"), exist_ok=True)
    path = os.path.join(HERE, "cache", "earbud_v%d_%s_%g.npz" % (VERSION, name, h))
    if os.path.exists(path):
        z = np.load(path); return z["V"], z["Q"]
    V, Q = sdf.mesh(F, lo, hi, h)
    np.savez_compressed(path, V=V, Q=Q); return V, Q


def all_meshes(h=0.07):
    """部品の網目（元の座標）：{名前: (V, Q)}"""
    out = {}
    bF = body_sdf()
    out["body"] = mesh_cached("body", bF, (-6.4, 7.9, Z_CAP - 0.1), (1.9, 14.4, 18.5), h)
    tip_c = HC + D * 4.2
    out["tip"] = mesh_cached("tip", eartip_sdf(), tuple(tip_c - 2.3), tuple(tip_c + 2.3), h * 0.6)
    out["cap"] = mesh_cached("cap", cap_sdf(), (-1.6, 9.5, Z0 - 0.1), (1.6, 12.8, Z_CAP + 0.2), h * 0.6)
    gc = HC + D * (S_MOUTH + 0.03)
    out["grille"] = mesh_cached("grille", disc(gc, D, R_MOUTH + 0.04, 0.06, 0.01), tuple(gc - 0.8), tuple(gc + 0.8), 0.02)
    sen, sp, _ = flush_patch(bF, HC + np.array([-0.9, -3.0, 0.55]), (0.46, 0.30))       # 耳に当たる側のセンサーの小窓
    out["sensor"] = mesh_cached("sensor", sen, tuple(sp - 0.7), tuple(sp + 0.7), 0.025)
    mic, mp, _ = flush_patch(bF, np.array([STEM_R + 0.5, 11.12, 10.4]), (0.13, 0.80))    # 軸の外側のマイクの網目（縦長）
    out["mic"] = mesh_cached("mic", mic, tuple(mp - 1.0), tuple(mp + 1.0), 0.025)
    tm, tp, _ = flush_patch(bF, HC + np.array([1.6, 0.0, 3.4]), (0.42, 0.22))           # 頭の上の外側のマイク
    out["topmic"] = mesh_cached("topmic", tm, tuple(tp - 0.6), tuple(tp + 0.6), 0.025)
    seam = sdf.torus(np.array([0.0, 11.12, Z_CAP + 0.05]), np.eye(3), STEM_R - 0.004, 0.035)   # 金属のふたと樹脂の継ぎ目
    out["seam"] = mesh_cached("seam", seam, (-1.6, 9.5, Z_CAP - 0.1), (1.6, 12.8, Z_CAP + 0.2), 0.02)
    return out


def build(bpy, coll=None, h=0.07, hide_old=None):
    """元の座標で巨大イヤホン v2 を作る → 親（空）と部品を返す。hide_old：Codex版の部品（隠す）"""
    from mathutils import Matrix
    from hbuild import mk_mesh, NT, principled, srgb
    coll = coll or bpy.context.scene.collection
    root = bpy.data.objects.new("Earbud v2", None); coll.objects.link(root)
    COL = {}

    def M(name, hexc, **kw):
        m = bpy.data.materials.new(name); nt = NT(m); b = principled(nt, base=srgb(hexc), **kw); COL[name] = hexc; return m, nt, b
    # つやのある白い樹脂。頭の合わせ目（耳の先の向きに垂直な面で頭を二つに分ける線）を細い溝として凹凸で描く
    m_body, nt, b = M("Earbud gloss white", "#F1F1EE", rough=0.20, spec=0.5, coat=0.55, coat_r=0.05, sss=0.06, sss_r=(1.0, 0.85, 0.7), sss_s=0.06)
    tc = nt.n("ShaderNodeTexCoord")
    dp = nt.n("ShaderNodeVectorMath", operation="DOT_PRODUCT"); dp.inputs[1].default_value = tuple(float(x) for x in D)
    nt.l(tc.outputs["Object"], dp.inputs[0])
    sub = nt.n("ShaderNodeMath", operation="SUBTRACT"); sub.inputs[1].default_value = float(HC @ D + 1.15)    # 合わせ目は頭の中心から 1.15 前
    nt.l(dp.outputs["Value"], sub.inputs[0]); ab = nt.n("ShaderNodeMath", operation="ABSOLUTE"); nt.l(sub.outputs[0], ab.inputs[0])
    mr_ = nt.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP"); mr_.inputs["From Min"].default_value = 0.012; mr_.inputs["From Max"].default_value = 0.045
    nt.l(ab.outputs[0], mr_.inputs["Value"])                          # 溝の外＝1、溝の中＝0
    bp = nt.n("ShaderNodeBump", i_Strength=0.9, i_Distance=0.03); nt.l(mr_.outputs["Result"], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
    dk = nt.n("ShaderNodeMix", data_type="RGBA"); dk.inputs[6].default_value = (*srgb("#B9BCBD"), 1); dk.inputs[7].default_value = (*srgb("#F1F1EE"), 1)
    nt.l(mr_.outputs["Result"], dk.inputs[0]); nt.l(dk.outputs[2], b.inputs["Base Color"])
    m_tip, _, _ = M("Earbud silicone", "#DADDE0", rough=0.55, spec=0.35, sss=0.35, sss_r=(1.0, 0.9, 0.8), sss_s=0.25)
    m_cap, _, _ = M("Earbud chrome", "#CDD1D6", rough=0.12, metal=1.0)
    m_win, _, _ = M("Earbud sensor glass", "#0B0C0E", rough=0.06, spec=0.6, coat=0.6, coat_r=0.03)
    m_seam, _, _ = M("Earbud seam", "#9EA3A8", rough=0.4)
    # 網目（音の口・マイク）：細かい穴の並び（凹凸）。黒い金属の網
    m_mesh, nt, b = M("Earbud grille", "#24282C", rough=0.45, metal=0.6)
    tc = nt.n("ShaderNodeTexCoord"); vo = nt.n("ShaderNodeTexVoronoi", i_Scale=30.0, i_Randomness=0.0); nt.l(tc.outputs["Object"], vo.inputs["Vector"])
    bp = nt.n("ShaderNodeBump", i_Strength=0.6, i_Distance=0.01); nt.l(vo.outputs["Distance"], bp.inputs["Height"]); nt.l(bp.outputs[0], b.inputs["Normal"])
    for m_ in (m_body, m_tip, m_cap, m_win, m_seam, m_mesh): m_.diffuse_color = (*srgb(COL[m_.name]), 1)   # 簡易描画での色

    MS = all_meshes(h)
    use = [("body", "Earbud v2 body", m_body), ("tip", "Earbud v2 eartip", m_tip), ("cap", "Earbud v2 metal cap", m_cap),
           ("grille", "Earbud v2 grille", m_mesh), ("sensor", "Earbud v2 sensor", m_win), ("mic", "Earbud v2 mic", m_mesh),
           ("topmic", "Earbud v2 top mic", m_mesh), ("seam", "Earbud v2 seam", m_seam)]
    parts = []
    for key, nm, m_ in use:
        V, Q = MS[key]; o = mk_mesh(nm, V, Q, coll, mats=[m_]); o.parent = root; o.matrix_parent_inverse = Matrix.Identity(4); parts.append(o)
    for o in (hide_old or []):
        o.hide_render = True; o.hide_viewport = True
    return root, parts


if __name__ == "__main__":                                            # 網目だけ作って大きさを確かめる（Blender なし）
    import time
    t0 = time.time()
    for k, (V, Q) in all_meshes().items():
        print("%-7s v=%6d q=%6d lo=%s hi=%s" % (k, len(V), len(Q), V.min(0).round(2), V.max(0).round(2)))
    print("%.1fs" % (time.time() - t0))
