# 共通の部品（Blender）：小物。どれも原点のまわりに作り、根元の空（root）を返す。場面の側で置き場所を決めて動かす
#   バケツ（取っ手は支点で回り、液面は傾く）・ひみつの色の小びん（回る腕と傾けるフォーク）・共通の色のタンク（管と注ぎ口）
#   透明なコップ（中の色が見える）・傾けて注ぐ入れ物（びん・缶とU字の腕）・台・天井クレーン（台車・振れる綱・フック）・鍵（歯の並びで形が変わる）・鍵穴の板（差すと輪が光る）・錠の箱（上から差す。輪と灯が光る）・鍵の型（色が満ちる）・地面の灯
#   大きさの単位は m。まるロボ（高さ約1.2m、背中の受け皿の上面は床から約1.3m）に合わせてある
import math
import bpy, bmesh
from mathutils import Vector, Matrix
from .world import mat, mat_emit, mesh_obj, box, cyl, torus, tube, empty, link, srgb

BUCKET = dict(r_top=0.20, r_bot=0.165, h=0.40, rim=0.012, lug_z=0.37, handle_r=0.205, fill=0.34)
HOOK_OFFSET = 0.045                                                # フックの先 → 取っ手のてっぺん
D_LOAD = BUCKET["lug_z"] + BUCKET["handle_r"] + HOOK_OFFSET        # フック → バケツの底（吊ったとき）0.62


def parent(ch, par, loc=(0, 0, 0)):
    ch.parent = par; ch.matrix_parent_inverse = Matrix.Identity(4); ch.location = loc; return ch


def clear_mat(name, rgb_lin, alpha=0.30, rough=0.12):
    """すけて中が見える樹脂（透明なバケツ・小びん）。EEVEE ではディザで半透明"""
    m = mat(name, rgb_lin, rough=rough, coat=0.3); bs = m.node_tree.nodes["Principled BSDF"]; bs.inputs["Alpha"].default_value = alpha
    try: m.surface_render_method = "DITHERED"
    except Exception: pass
    m.diffuse_color = (*rgb_lin, 0.35); return m


def paint_mat(name, rgb_lin, gloss=0.18):
    """絵の具：つやのある液面。色は場面の側でキーを打つ（inputs["Base Color"]）"""
    m = mat(name, rgb_lin, rough=gloss, coat=0.4); return m


def bucket(name, m_body, m_paint, m_trim=None, coll=None):
    """バケツ：m_body（胴と底。すける樹脂にすると中の色が見える）、m_trim（縁・取っ手の付け根）"""
    B = BUCKET; root = empty(name, coll, 0.2); m_trim = m_trim or m_body
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=B["r_bot"], radius2=B["r_top"], depth=B["h"])
    for v in bm.verts: v.co.z += B["h"] / 2
    body = parent(mesh_obj(name + " body", bm, m_body, smooth=True, coll=coll), root)
    sol = body.modifiers.new("wall", "SOLIDIFY"); sol.thickness = 0.008; sol.offset = -1
    floor_ = parent(cyl(name + " floor", B["r_bot"], 0.01, m_body, 48, coll=coll), root, (0, 0, 0.005))
    rim = parent(torus(name + " rim", B["r_top"], B["rim"], m_trim, 64, 10, coll=coll), root, (0, 0, B["h"]))
    parent(torus(name + " base ring", B["r_bot"], 0.008, m_trim, 64, 8, coll=coll), root, (0, 0, 0.008))
    for s in (-1, 1):
        lug = parent(cyl(name + " lug", 0.022, 0.03, m_trim, 16, coll=coll), root, (s * (B["r_top"] - 0.004), 0, B["lug_z"])); lug.rotation_euler = (0, math.pi / 2, 0)
    hp = parent(empty(name + " handle pivot", coll, 0.05), root, (0, 0, B["lug_z"]))
    m_wire = mat(name + " wire", srgb("#8C939A"), 0.3, 1.0)
    h = torus(name + " handle", B["handle_r"], 0.007, m_wire, 32, 8, arc=math.pi, coll=coll)
    h.rotation_euler = (math.pi / 2, 0, 0); parent(h, hp); h.rotation_euler = (math.pi / 2, 0, 0)
    lp = parent(empty(name + " liquid pivot", coll, 0.05), root, (0, 0, B["fill"]))
    r_liq = B["r_bot"] + (B["r_top"] - B["r_bot"]) * B["fill"] / B["h"] - 0.008
    liq = parent(cyl(name + " paint", r_liq, 0.012, m_paint, 48, coll=coll), lp)
    deep = parent(cyl(name + " paint body", B["r_bot"] - 0.01, B["fill"], m_paint, 48, r2=r_liq - 0.002, coll=coll), root, (0, 0, B["fill"] / 2))
    return dict(root=root, handle=hp, liquid=lp, paint=liq, paint_body=deep, mat=m_paint, r_liq=r_liq)


def cup(name, m_body, m_paint, r=0.10, h=0.20, m_trim=None, coll=None):
    """透明なコップ（中の絵の具が横から見える）。原点は底の真ん中。
    絵の具は二つ：液面（liquid：z＝底からの高さ、回転＝揺れ）と、絵の具の体（paint_body：高さ1の柱。scale.z＝高さ）。量が0なら隠す"""
    root = empty(name, coll, 0.1); m_trim = m_trim or m_body; r0 = r * 0.96
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=r0, radius2=r, depth=h)
    for v in bm.verts: v.co.z += h / 2
    body = parent(mesh_obj(name + " body", bm, m_body, smooth=True, coll=coll), root)
    sol = body.modifiers.new("wall", "SOLIDIFY"); sol.thickness = 0.006; sol.offset = -1
    parent(cyl(name + " floor", r0, 0.01, m_body, 48, coll=coll), root, (0, 0, 0.005))
    parent(torus(name + " rim", r, 0.006, m_trim, 64, 8, coll=coll), root, (0, 0, h))
    lp = parent(empty(name + " liquid pivot", coll, 0.04), root, (0, 0, 0.05))
    liq = parent(cyl(name + " paint", r0 - 0.008, 0.008, m_paint, 48, coll=coll), lp)
    bmb = bmesh.new(); bmesh.ops.create_cone(bmb, cap_ends=True, segments=48, radius1=r0 - 0.008, radius2=r0 - 0.008, depth=1.0)
    for v in bmb.verts: v.co.z += 0.5
    deep = parent(mesh_obj(name + " paint body", bmb, m_paint, smooth=True, coll=coll), root, (0, 0, 0.01))
    return dict(root=root, liquid=lp, paint=liq, paint_body=deep, mat=m_paint, r=r, h=h)


def tilt_holder(name, m_frame, m_body, m_paint=None, kind="bottle", axis="y", r=0.06, h=0.20, post_h=0.42, coll=None):
    """傾けて注ぐ入れ物（びん・缶）と、その台：柱の上の U 字の腕が、入れ物の真ん中を axis のまわりに回せるように持つ。
    pivot を axis のまわりに回すと傾く（ふだんは口が上）。mouth：pivot の局所の口の位置（流れの出どころ）。
    kind：bottle（色ガラスのびん。肩がすぼまって首と口）／can（缶。口は上の縁、内側に絵の具の面）"""
    root = empty(name, coll, 0.1)
    w = r + 0.022; zb = post_h - h / 2 - 0.035                            # U 字の腕の幅、腕の下の横棒の高さ
    parent(cyl(name + " foot", 0.075, 0.018, m_frame, 32, coll=coll), root, (0, 0, 0.009))
    parent(cyl(name + " post", 0.016, zb, m_frame, 16, coll=coll), root, (0, 0, zb / 2))
    side = (1.0, 0.0) if axis == "x" else (0.0, 1.0)                     # 腕は回る軸の向きに並ぶ
    bar = parent(box(name + " yoke bar", (2 * w + 0.02 if axis == "x" else 0.024, 2 * w + 0.02 if axis == "y" else 0.024, 0.02), m_frame, 0.004, coll=coll), root, (0, 0, zb))
    for s_ in (-1, 1):
        parent(box(name + " yoke arm", (0.02, 0.02, post_h - zb + 0.02), m_frame, 0.003, coll=coll), root, (s_ * w * side[0], s_ * w * side[1], (zb + post_h) / 2))
    pv = parent(empty(name + " pivot", coll, 0.05), root, (0, 0, post_h))
    for s_ in (-1, 1):
        pin = parent(cyl(name + " pin", 0.012, 0.03, m_frame, 12, coll=coll), pv, (s_ * (w - 0.012) * side[0], s_ * (w - 0.012) * side[1], 0))
        pin.rotation_euler = (math.pi / 2, 0, 0) if axis == "y" else (0, math.pi / 2, 0)
    parent(torus(name + " clamp", r + 0.007, 0.007, m_frame, 40, 8, coll=coll), pv)
    if kind == "bottle":
        bm = bmesh.new()
        prof = [(0.0, -h / 2), (r, -h / 2), (r, h / 2 - 0.03), (r * 0.45, h / 2 + 0.03), (r * 0.42, h / 2 + 0.08), (r * 0.50, h / 2 + 0.09), (0.0, h / 2 + 0.09)]
        ring_n = 40; rings = []
        for (rr, zz) in prof:
            rings.append([bm.verts.new((rr * math.cos(2 * math.pi * j / ring_n), rr * math.sin(2 * math.pi * j / ring_n), zz)) for j in range(ring_n)])
        for a_, b_ in zip(rings, rings[1:]):
            for j in range(ring_n): bm.faces.new((a_[j], a_[(j + 1) % ring_n], b_[(j + 1) % ring_n], b_[j]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        parent(mesh_obj(name + " bottle", bm, m_body, smooth=True, coll=coll), pv)
        mouth = (0.0, 0.0, h / 2 + 0.09)
    else:
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=r, radius2=r, depth=h)
        parent(mesh_obj(name + " can", bm, m_body, smooth=True, coll=coll), pv)
        parent(cyl(name + " can bottom", r, 0.006, m_body, 48, coll=coll), pv, (0, 0, -h / 2))
        parent(torus(name + " can rim", r, 0.005, m_body, 48, 8, coll=coll), pv, (0, 0, h / 2))
        if m_paint: parent(cyl(name + " can paint", r - 0.004, 0.004, m_paint, 48, coll=coll), pv, (0, 0, h / 2 - 0.02))
        mouth = (0.0, -r * 0.9 if axis == "x" else 0.0, h / 2)            # 傾ける向き（−Y）の縁から注ぐ
    return dict(root=root, pivot=pv, mouth=mouth, axis=axis, post_h=post_h)


def jar_arm(name, m_post, m_glass, m_paint, arm_len=0.465, post_h=0.62, coll=None):
    """ひみつの色の小びん：台に立つ柱、柱の上で回る腕（yaw：腕はローカル +Y の向き）、腕の先で傾くフォーク（tilt：腕の向きの軸まわり）。
    びんは口を上にしてフォークに立つ。傾けると口が横・下へ回り、口（mouth：tilt から見た位置）から流れ（stream）が落ちる"""
    root = empty(name, coll, 0.2)
    parent(cyl(name + " post", 0.025, post_h, m_post, 16, coll=coll), root, (0, 0, post_h / 2))
    yaw = parent(empty(name + " yaw", coll, 0.05), root, (0, 0, post_h))
    parent(box(name + " arm", (0.04, arm_len, 0.03), m_post, 0.006, coll=coll), yaw, (0, arm_len / 2, 0))
    tilt = parent(empty(name + " tilt", coll, 0.05), yaw, (0, arm_len, 0))
    parent(box(name + " fork", (0.15, 0.03, 0.02), m_post, 0.004, coll=coll), tilt, (0, 0, -0.01))
    parent(cyl(name + " jar", 0.085, 0.21, m_glass, 32, coll=coll), tilt, (0, 0, 0.105))
    parent(cyl(name + " color", 0.075, 0.15, m_paint, 32, coll=coll), tilt, (0, 0, 0.08))
    parent(torus(name + " lip", 0.083, 0.008, m_post, 32, 8, coll=coll), tilt, (0, 0, 0.21))
    st = parent(cyl(name + " stream", 0.011, 1.0, m_paint, 12, coll=coll), root, (0, 0, 0)); st.hide_render = True
    for v in st.data.vertices: v.co.z -= 0.5                         # 原点を上の端に（下へ伸ばす）
    return dict(root=root, yaw=yaw, tilt=tilt, stream=st, arm_len=arm_len, post_h=post_h, mouth=(0.0, 0.0, 0.21))


def stream_between(st, p_top, p_bot, r=None):
    """流れの円柱を、p_top（上の端）から p_bot（下の端）まで（世界の座標）に合わせる → (location, rotation, scale_z)"""
    a = Vector(p_top); b = Vector(p_bot); d = b - a; L = max(d.length, 1e-4)
    q = Vector((0, 0, -1)).rotation_difference(d.normalized())
    return a, q, L


def table(name, w, d, h, m_top, m_leg, coll=None):
    root = empty(name, coll, 0.2)
    parent(box(name + " top", (w, d, 0.05), m_top, 0.01, coll=coll), root, (0, 0, h - 0.025))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parent(box(name + " leg", (0.05, 0.05, h - 0.05), m_leg, 0.004, coll=coll), root, (sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), (h - 0.05) / 2))
    return root


def hoist(name, y0, y1, z_beam, m_frame, m_cable, coll=None, posts=(0, 1), rod=False):
    """天井クレーン（レールは y の向き）：柱と梁、梁の下を走る台車、綱（rod＝True なら伸び縮みする硬い棒）とフック。root は x の位置に置く。
    posts：柱を立てる端（0＝y0、1＝y1）。(1,) なら後ろの柱だけの片持ち（前に柱がなく、カメラをふさがない）"""
    root = empty(name, coll, 0.2)
    for i_, y in enumerate((y0, y1)):
        if i_ not in posts: continue
        parent(box(name + " post", (0.12 if len(posts) == 1 else 0.08, 0.12 if len(posts) == 1 else 0.08, z_beam), m_frame, 0.006, coll=coll), root, (0, y, z_beam / 2))
        if len(posts) == 1:                                        # 片持ちの方づえ（斜めの支え）
            sgn = 1 if i_ == 0 else -1; b_ = parent(box(name + " brace", (0.06, 0.70, 0.06), m_frame, 0.004, coll=coll), root, (0, y + sgn * 0.30, z_beam - 0.30)); b_.rotation_euler = (sgn * -0.75, 0, 0)
    parent(box(name + " beam", (0.10, y1 - y0 + 0.08, 0.10), m_frame, 0.008, coll=coll), root, (0, (y0 + y1) / 2, z_beam + 0.05))
    trolley = parent(empty(name + " trolley", coll, 0.08), root, (0, (y0 + y1) / 2, z_beam - 0.06))
    parent(box(name + " carriage", (0.16, 0.20, 0.08), m_frame, 0.01, coll=coll), trolley, (0, 0, 0.0))
    swing = parent(empty(name + " swing", coll, 0.05), trolley, (0, 0, -0.04))
    cable = parent(cyl(name + " cable", 0.016 if rod else 0.006, 1.0, m_cable, 12, coll=coll), swing, (0, 0, 0))
    for v in cable.data.vertices: v.co.z -= 0.5                     # 原点を上の端に（長さは scale.z）
    hook = parent(empty(name + " hook", coll, 0.05), swing, (0, 0, -1.0))
    parent(cyl(name + " block", 0.03, 0.07, m_frame, 16, coll=coll), hook, (0, 0, 0.035))
    hk = torus(name + " hook bend", 0.03, 0.007, m_cable, 24, 8, arc=math.pi * 1.4, coll=coll); parent(hk, hook, (0, 0, -0.02)); hk.rotation_euler = (math.pi / 2, 0, -0.4)
    return dict(root=root, trolley=trolley, swing=swing, cable=cable, hook=hook, z_top=z_beam - 0.10)


KEY_TEETH = (1, 0, 1, 1)


def key(name, m, teeth=KEY_TEETH, s=1.0, coll=None):
    """鍵：輪（つまみ）・軸・歯（teeth の 1 の所に歯）。原点は輪の中心、軸は +X の向き。大きさは s 倍"""
    root = empty(name, coll, 0.1)
    parent(torus(name + " bow", 0.062 * s, 0.018 * s, m, 32, 10, coll=coll), root).rotation_euler = (math.pi / 2, 0, 0)
    parent(box(name + " shaft", (0.24 * s, 0.022 * s, 0.03 * s), m, 0.004 * s, coll=coll), root, (0.18 * s, 0, 0))
    for k, on in enumerate(teeth):
        if on: parent(box(name + " tooth", (0.026 * s, 0.022 * s, 0.05 * s), m, 0.003 * s, coll=coll), root, ((0.17 + 0.05 * k) * s, 0, -0.035 * s))
    return root


def keyhole(name, m_plate, m_dark, glow_rgb=(0.4, 0.95, 0.8), s=1.0, coll=None):
    """鍵穴の板（台の前の面に付ける）。鍵が入ると輪が光る（材質の Strength にキー）。大きさは s 倍"""
    root = empty(name, coll, 0.1)
    parent(box(name + " plate", (0.22 * s, 0.03, 0.30 * s), m_plate, 0.01, coll=coll), root)
    hole = parent(cyl(name + " hole", 0.03 * s, 0.035, m_dark, 24, coll=coll), root, (0, -0.002, 0.03 * s)); hole.rotation_euler = (math.pi / 2, 0, 0)
    parent(box(name + " slot", (0.022 * s, 0.035, 0.07 * s), m_dark, 0.0, coll=coll), root, (0, -0.002, -0.025 * s))
    mg = mat_emit(name + " glow", glow_rgb, 0.0)
    ring = parent(torus(name + " ring", 0.075 * s, 0.008 * s, mg, 40, 8, coll=coll), root, (0, -0.018, 0.0)); ring.rotation_euler = (math.pi / 2, 0, 0)
    return dict(root=root, glow=mg, ring=ring)


def lock_box(name, m_body, m_plate, m_dark, glow_rgb=(0.4, 0.95, 0.8), size=(0.26, 0.24, 0.28), s=1.4, coll=None):
    """錠の箱（台の上に置く）：鍵は上の面の鍵穴に、真上から差す（鍵は立ち、平らな面が前（−Y）を向く）。
    鍵の歯は −X の向き（鍵穴の切り欠きも −X）。差すと上の輪と前の灯が光る（材質 glow の Strength にキー）。
    s は鍵穴の大きさ（kit の鍵 s≈1.15×s と組む）。原点は箱の底の真ん中。top＝鍵穴の中心（箱の局所）"""
    w, d, h = size; root = empty(name, coll, 0.1)
    parent(box(name + " body", (w, d, h), m_body, 0.012, coll=coll), root, (0, 0, h / 2))
    parent(box(name + " top plate", (w - 0.03, d - 0.03, 0.012), m_plate, 0.003, coll=coll), root, (0, 0, h + 0.006))
    zt = h + 0.012
    parent(cyl(name + " hole", 0.03 * s, 0.004, m_dark, 24, coll=coll), root, (0, 0, zt + 0.0005))
    parent(box(name + " slot", (0.07 * s, 0.022 * s, 0.004), m_dark, 0.0, coll=coll), root, (-0.035 * s, 0, zt + 0.0005))
    mg = mat_emit(name + " glow", glow_rgb, 0.0)
    ring = parent(torus(name + " ring", 0.075 * s, 0.008 * s, mg, 40, 8, coll=coll), root, (0, 0, zt + 0.002))
    bez = parent(cyl(name + " lamp bezel", 0.042, 0.010, m_dark, 24, coll=coll), root, (0, -d / 2 - 0.004, h * 0.60)); bez.rotation_euler = (math.pi / 2, 0, 0)
    lamp = parent(cyl(name + " lamp", 0.030, 0.012, mg, 24, coll=coll), root, (0, -d / 2 - 0.008, h * 0.60)); lamp.rotation_euler = (math.pi / 2, 0, 0)
    return dict(root=root, glow=mg, ring=ring, lamp=lamp, top=(0.0, 0.0, zt), depth=h)


def key_mold(name, m_block, m_dark, m_paint, teeth=KEY_TEETH, s=1.0, coll=None):
    """鍵の型：台の上の板に、鍵の形のくぼみ。絵の具が流れ込むと、色の層（fill）がくぼみの底から満ちる。鍵の大きさ s 倍"""
    root = empty(name, coll, 0.1)
    parent(box(name + " block", (0.44 * s, 0.30 * s, 0.06), m_block, 0.01, coll=coll), root, (0, 0, 0.03))
    rec = empty(name + " recess", coll, 0.05); parent(rec, root, (-0.15 * s, 0, 0.056))
    KR = (math.pi / 2, 0, 0)                                               # 鍵を寝かせる（平らな面が上、歯は +Y）。上から鍵の形に見える
    k_dark = key(name + " cavity", m_dark, teeth, s, coll); parent(k_dark, rec); k_dark.rotation_euler = KR; k_dark.scale = (1.0, 0.25, 1.0)
    fill = empty(name + " fill", coll, 0.05); parent(fill, rec, (0, 0, -0.004))
    k_fill = key(name + " fill shape", m_paint, teeth, s, coll); parent(k_fill, fill); k_fill.rotation_euler = KR; k_fill.scale = (1.0, 0.28, 1.0)
    return dict(root=root, recess=rec, fill=fill, key_rot=KR)


def lamps(name, p0, p1, n, m_off, coll=None):
    """地面の灯（ペアリングの道）：n個。灯ごとに材質を分ける（明るさを順にキーで上げる）"""
    out = []
    for i in range(n):
        u = (i + 0.5) / n; p = Vector(p0).lerp(Vector(p1), u)
        base = cyl("%s %d" % (name, i), 0.06, 0.03, m_off, 24, coll=coll); base.location = (p.x, p.y, 0.015)
        mg = mat_emit("%s glow %d" % (name, i), (0.35, 0.95, 0.85), 0.0)
        cap = cyl("%s cap %d" % (name, i), 0.04, 0.01, mg, 24, coll=coll); cap.location = (p.x, p.y, 0.035)
        out.append(dict(base=base, cap=cap, glow=mg, u=u))
    return out


def tank(name, m_body, m_leg, m_paint, height=1.5, r=0.42, coll=None):
    """みんなが知っている色のタンク：脚の上の円柱と円すいの底。出口は底の中心（outlet を返す）"""
    root = empty(name, coll, 0.2)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        parent(box(name + " leg", (0.06, 0.06, height), m_leg, 0.005, coll=coll), root, (math.cos(a) * r * 0.8, math.sin(a) * r * 0.8, height / 2))
    parent(cyl(name + " shell", r, 0.75, m_body, 48, coll=coll), root, (0, 0, height + 0.375 + 0.15))
    parent(cyl(name + " funnel", r, 0.3, m_body, 48, r2=0.06, coll=coll), root, (0, 0, height + 0.15)).rotation_euler = (math.pi, 0, 0)
    parent(cyl(name + " lid", r * 1.02, 0.05, m_leg, 48, coll=coll), root, (0, 0, height + 0.9 + 0.025))
    win = parent(cyl(name + " window", r * 1.003, 0.32, m_paint, 48, coll=coll), root, (0, 0, height + 0.5))   # 中の白が見える窓（帯）
    return dict(root=root, outlet=(0, 0, height))
