# 16本目 4章（S22〜S24）：取り返しても（倉庫 → 夜の道 → 夜の家 → 倉庫 → 写しの図）
#   scenes.py から exec される（scenes_ch3.py のあと）。絵コンテ表：絵コンテ_v1.md の「4章（S22〜S24）」
#   倉庫の場面は 3章の b_e の世界に、4章の時刻の動きを足す（e4_extend）。家の場面は b_home4（1章の部屋を夜に）
import math

LB_STAND = (7.85, -0.95)            # 棚に残った箱（LEFT_BOX）の前。上の段の棚板（高さ 0.6）に頭が当たらない所（当たりの点検：0.72 で棚板と箱に入った）
COPY_X = [7.25 + 0.2 * k for k in range(6)]      # 23-04 の「まだ何枚も」：上の段（段 1）に立てて並ぶ名札の x
SAFE = (0.85, 2.1)                  # 家の金庫（机の左）。前の面は y = 1.89


def head_holder(M, z=0.42):
    """まるロボの頭のてっぺん（胴の子。17本目の帽子と同じ作り）。ここに名札を写して運ぶ"""
    hm = empty((0, 0, 0)); hm.parent = M.torso; hm.location = (0, 0.0, z)
    return hm


def follow(ob, target, t_on, d_on, t_off=None, d_off=0.5):
    """ob を target に重ねる強さを、t_on から d_on 秒で 0→1、t_off から d_off 秒で 1→0（ワープさせない。17本目 v1 の帽子の決まり）"""
    ct = ob.constraints.new("COPY_TRANSFORMS"); ct.target = target
    for t_, v_ in ((-100.0, 0.0), (t_on, 0.0), (t_on + d_on, 1.0)) + (((t_off, 1.0), (t_off + d_off, 0.0)) if t_off is not None else ()):
        ct.influence = v_; ct.keyframe_insert("influence", frame=f(t_))
    return ct


def dim_lens(M, t0, d=1.6, k=0.25):
    """目（レンズ）の光を t0 から d 秒で k 倍に下げる。marumotion の light はアンテナの光だけなので、レンズの光る色（青緑）の強さを直接動かす
    （試しの絵：24-08「目の光が下がって」で、目が明るいままだった）。本物のまるロボも、光る青緑の材質を同じ形で探す"""
    done = {}
    for o in [M.torso] + list(M.torso.children_recursive):
        for sl in getattr(o, "material_slots", []):
            m = sl.material
            if not m or not m.use_nodes or "light" in m.name.lower(): continue
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED": es, ec = n.inputs["Emission Strength"], n.inputs["Emission Color"]
                elif n.type == "EMISSION": es, ec = n.inputs["Strength"], n.inputs["Color"]
                else: continue
                c = ec.default_value
                if es.default_value > 0.5 and c[2] > c[0] * 1.3:
                    if m.name not in done:
                        m2 = m.copy(); m2.name = m.name + " dim"; done[m.name] = m2
                    sl.material = done[m.name]
    for m2 in done.values():
        for n in m2.node_tree.nodes:
            es = n.inputs.get("Emission Strength") if n.type == "BSDF_PRINCIPLED" else (n.inputs.get("Strength") if n.type == "EMISSION" else None)
            if es is None or es.default_value <= 0.5: continue
            base = es.default_value
            for t_, v_ in ((-100.0, base), (t0, base), (t0 + d, base * k)):
                es.default_value = v_; es.keyframe_insert("default_value", frame=f(t_))
    return len(done)


def box_lid(box):
    for c in box.children:
        if c.type == "MESH" and c.active_material and c.active_material.name.startswith("e_boxlid"): return c
    return None


def e4_extend(M):
    """3章の世界（b_e）に、4章の倉庫の場面の動きを足す"""
    lb = BOXES[LEFT_BOX]
    # ---- 22-01：がまんできない → 残った箱の前へ走る
    # 計画の点検：わきから箱の前へ走ると、向きを変えるのに 1.6〜2.6 秒遅れた → 22-01 の場面の替わり目で、箱の正面の手前（箱のほうを向く）へ置き直し、
    #   22-01 で、ぐっと前に乗り出してから、22-02 で前（+y）へまっすぐ走って寄る
    M.at(s("22-01") - 0.08, loc=(7.85, -1.65, 0.0), face=180.0, interp="CONSTANT")
    M.lean(s("22-01") + 0.6, s("22-01") + 1.5, 15.0)
    M.run(s("22-02") + 0.1, wv("22-02", "とびこむ") - 0.1, LB_STAND)
    ev(s("22-01") + 0.3, "beep_yes", 0.4, "maru_c")
    # ---- 22-02：ふたが開く → 頭から箱へつっこむ（前へ大きく傾く）→ 名札を頭に載せて起きる → 出口へ走る
    lid = box_lid(lb); t_lid = wv("22-02", "とびこむ") - 0.6
    if lid is not None:
        key(lid, "location", -100.0, tuple(lid.location), "CONSTANT"); key(lid, "location", t_lid, tuple(lid.location))
        key(lid, "location", t_lid + 0.3, (0.0, -BOX_D / 2 - 0.01, BOX_H + BOX_D / 2))
        key(lid, "rotation_euler", t_lid, (0, 0, 0)); key(lid, "rotation_euler", t_lid + 0.3, (R(90), 0, 0))
    ev(t_lid + 0.05, "pop", 0.25, "leftbox")
    (bx_, by_, bz_), fc_ = _box_world(LEFT_BOX)
    for k in range(3):        # 箱の中の名札（ふたが開くと、上のはしが見える）
        nameplate((bx_ - 0.1 + 0.1 * k, by_ - 0.06 + 0.04 * k, bz_ + BOX_H - 0.06), rot=(R(80), 0, R(180 + 6 * (k - 1))), w=0.22)
    t_dive = wv("22-02", "とびこむ") + 0.1
    # 当たりの点検：段と段のすきまは 22 cm で、まるロボの頭は箱にもぐれない（55 度で棚板と箱に入った）→ 箱へぐっと身を乗り出して小さく跳ね、
    #   その間に名札が箱から頭へ飛び乗る（follow で 0.45 秒）
    M.lean(t_dive, t_dive + 0.7, 12.0)
    M.hop(t_dive + 0.15)
    ev(t_dive + 0.5, "pop", 0.25, "")
    hm = head_holder(M)
    tg = nameplate((bx_, by_ - 0.02, bz_ + BOX_H - 0.04), rot=(R(80), 0, R(180)), w=0.40, glow=0.5)
    tg_h = empty((0, 0, 0)); tg_h.parent = hm; tg_h.location = (0, 0, 0.02); tg_h.rotation_euler = (R(-45), 0, 0)      # 頭の上に立てて載せる（試しの絵：寝かせると、下からのカメラで頭にかくれた）
    t_up = t_dive + 0.35          # 跳ねた所で、名札が箱から頭へ
    follow(tg, tg_h, t_up, 0.45)
    track("headtag", tg, 0.05)
    t_run = wv("22-02", "走り出し") - 1.6      # 向きを変えて走るので早めに
    M.run(t_run, s("22-03") - 0.2, (6.55, -1.15))      # つなげたコマ：0.7 m では走り出したように見えなかった → カメラのほうへ 1.3 m      # 場面が替わる前に走り終える（替わり目で道へ置き直す）
    # ---- 22-03：夜の道をこちらへ走ってくる（場面の替わり目で置き直す）
    t_road = s("22-03") - 0.08
    bpy.ops.object.light_add(type="POINT", location=(-15.0, -2.2, 3.0)); _ml = bpy.context.object      # 土の道の月明かり（試しの絵：真っ暗だった）
    _ml.data.energy = 140.0; _ml.data.color = (0.62, 0.72, 1.0); _ml.data.shadow_soft_size = 1.0
    M.at(t_road, loc=(-14.5, 0.35, 0.0), face=270.0, interp="CONSTANT")
    M.run(t_road + 0.15, wv("22-03", "名札") + 0.1, (-15.05, 0.35))      # 道の場面は 1.4 秒（走りは 1 秒に約 1.3 m）
    hide_key(tg, -100.0, False); hide_key(tg, wv("22-03", "名札") + 1.0, True)      # はじめは見せる（試しの絵：キーが 1 つだけで、ずっと隠れていた）       # 家の場面になったら、倉庫の世界の名札は消す（家の名札は別）
    # ---- 23-02：もう一度、市場へ（道 → 入口）
    M.at(s("23-02") - 0.08, loc=(-2.6, 0.45, 0.0), face=90.0, interp="CONSTANT")
    M.walk(s("23-02") + 0.3, e("23-02") + 0.4, (-0.9, 0.35))
    # ---- 23-03〜23-06：通路の奥の棚の前へ → 名札が何枚も → 固まる → 入口（家の方角）と棚を見比べる
    M.at(s("23-03") - 0.08, loc=(7.15, -1.1, 0.0), face=90.0, interp="CONSTANT")
    M.walk(s("23-03") + 0.1, s("23-04") + 1.0, (7.55, -1.05))
    M.at(s("23-04") + 2.4, face=180.0)
    M.surprise(wv("23-04", "まだ何枚") + 0.1)
    M.gaze(wv("23-04", "まだ何枚") + 1.4, 70.0, 0.6); M.gaze(s("23-05") + 0.8, 70.0, 0.6)       # 入口（家の方角）と棚を見比べる
    M.confused(wv("23-06", "どういう") - 0.2)
    # ---- 23-04 の名札の列：上の段（段 1）の箱を、まるロボが家にいる間に名札に替える
    t_sw = s("23-01")
    for k in [k_ for k_ in BOXES if k_[0] == 1 and k_[1] == 1 and 7.2 < k_[2] < 8.5]:
        key(BOXES[k], "scale", -100.0, (1, 1, 1), "CONSTANT"); key(BOXES[k], "scale", t_sw, (0.001,) * 3, "CONSTANT")
    cps = []
    for k, x in enumerate(COPY_X):
        n_ = nameplate((x, -0.33, LEVELS[1] + 0.065), rot=(R(84), 0, R(2 * (k % 3 - 1))), w=0.18)
        key(n_, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(n_, "scale", t_sw, (1, 1, 1), "CONSTANT"); cps.append(n_)
    track("copies", cps[2], 0.0)
    # 24-10：もう 1 枚ふえる
    n7 = nameplate((COPY_X[-1] + 0.2, -0.33, LEVELS[1] + 0.065), rot=(R(84), 0, 0), w=0.18)
    t_add = wv("24-10", "増えていく") + 0.1
    key(n7, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(n7, "scale", t_add, (0.001,) * 3); key(n7, "scale", t_add + 0.25, (1.15,) * 3); key(n7, "scale", t_add + 0.4, (1, 1, 1))
    ev(t_add + 0.1, "pop", 0.3, "newcopy"); track("newcopy", n7, 0.0)
    bpy.ops.object.light_add(type="POINT", location=(7.7, -1.1, 1.2)); _cl = bpy.context.object      # 名札の列を照らす
    _cl.data.energy = 18.0; _cl.data.color = (1.0, 0.88, 0.7); _cl.data.shadow_soft_size = 0.4
    # ---- 24-07：影が、平気な様子で、まるロボのお城の箱（写し）を棚に並べ直す（21-09 で売れた所）
    s4 = shadow((40.0, 40.0, 0.0), face=90.0, s=SHS2); track("shadow4", s4.root, 1.5 * SHS2)
    k4 = SOLD[0]; (qx, qy, qz), fq = _box_world(k4)
    nb = emblem_box((qx, qy, qz), "emb0", fq)
    t_put = wv("24-07", "このため") - 0.2
    key(nb, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(nb, "scale", t_put, (0.001,) * 3, "CONSTANT"); key(nb, "scale", t_put + 0.02, (1, 1, 1), "CONSTANT")
    cb = emblem_box((0, 0, 0), "emb0", -1); cb.parent = s4.root; cb.location = (0, -0.5, 0.75); cb.scale = (1 / SHS2,) * 3
    key(cb, "scale", -100.0, (1 / SHS2,) * 3, "CONSTANT"); key(cb, "scale", t_put, (1 / SHS2,) * 3, "CONSTANT"); key(cb, "scale", t_put + 0.02, (0.001,) * 3, "CONSTANT")
    stand = (qx, -0.85)
    sh_key(s4, s("24-07") - 0.3, (40.0, 40.0), 90.0, "CONSTANT"); sh_key(s4, s("24-07") - 0.15, (1.6, -1.1), 90.0, "CONSTANT")
    sh_key(s4, t_put - 0.9, (stand[0] - 0.6, stand[1]), 90.0); sh_key(s4, t_put - 0.5, stand, 180.0)
    key(s4.arm, "rotation_euler", t_put - 0.5, (R(-20), 0, 0)); key(s4.arm, "rotation_euler", t_put, (R(-60), 0, 0)); key(s4.arm, "rotation_euler", t_put + 0.5, (R(-15), 0, 0))
    ev(t_put, "thud", 0.18, "shadow4")
    sh_key(s4, t_put + 0.4, stand, 180.0); sh_key(s4, t_put + 1.0, stand, 270.0); sh_key(s4, e("24-07") + 0.6, (1.0, -1.1), 270.0)
    sh_key(s4, e("24-07") + 0.7, (40.0, 40.0), 270.0, "CONSTANT")
    # ---- 24-08：しょんぼり。目の光が下がる
    M.glow(s("24-08") + 0.6, 0.25, d=1.6)
    print("DIMLENS", dim_lens(M, s("24-08") + 0.6, 1.6, 0.2))
    M.sigh(s("24-08") + 0.9, sound=False)
    M.glow(s("24-10") + 0.2, 0.9, d=0.6)
    M.at(s("24-10") + 1.0, look=18)                     # 棚の名札の列を見上げる


# ======================================================================== A（夜の家）：22-03〜23-01
def night_house():
    """1章の部屋を夜に：部屋の明かりを弱く・電気スタンドを強く・窓の外の空を暗く。窓の外に、だれもいない夜の道と街灯 1 本"""
    room(window=True)
    world("#0A0F1E", 0.05)
    for o_, e_ in LIGHTS:
        tp = o_.data.type
        o_.data.energy = 0.0 if tp == "SUN" else (e_ * 0.12 if tp == "AREA" else e_ * 2.6)
    for em_, st_ in GLOWS_W:
        em_.inputs["Strength"].default_value = 0.05
    for o_ in bpy.data.objects:          # 窓のすぐ前の木（1章の昼の部屋の物）は隠す（試しの絵：木で窓の外の道が見えなかった）
        if o_.type == "MESH" and o_.active_material and o_.active_material.name.split(".")[0] in ("tree", "farhouse", "fence"):      # 遠くの家は段ボールに見えた
            o_.hide_render = True; o_.visible_camera = False
    x1 = 3.0
    cube(mat("n_ground", "#141C18", rough=0.95), (x1 + 6.0, -0.2, -0.06), (12.0, 16.0, 0.1))
    cube(mat("n_road", "#6A6C72", rough=0.9), (x1 + 3.2, -0.2, -0.005), (2.2, 16.0, 0.02))      # 試しの絵：暗い色で道が見えなかった
    for k in range(8): cube(mat("n_line", "#E8E4D8", rough=0.7), (x1 + 3.2, -4.0 + k * 1.1, 0.008), (0.08, 0.55, 0.004))      # まん中の白い線
    pole = mat("n_pole", "#2A2C30", rough=0.4, metal=0.6)
    cyl(pole, (x1 + 4.6, -1.8, 1.6), 0.05, 3.2, verts=12)
    cube(pole, (x1 + 4.35, -1.8, 3.2), (0.55, 0.08, 0.06))
    sphere(glow_mat("n_lampglow", "#FFD79A", 6.0), (x1 + 4.1, -1.8, 3.1), 0.14, seg=16)
    bpy.ops.object.light_add(type="POINT", location=(x1 + 4.0, -1.8, 2.9)); L = bpy.context.object
    L.data.energy = 260; L.data.color = srgb("#FFD08A")[:3]; L.data.shadow_soft_size = 0.4


def safe_box(loc):
    """金庫：灰色の金属の箱（中は暗い）。扉は左のちょうつがいで外へ開く（返す：扉の回る親）"""
    x, y = loc; W_, D_, H_ = 0.48, 0.42, 0.52; T_ = 0.03
    m = mat("safe", "#6E747C", rough=0.35, metal=0.7); mi = mat("safe_in", "#202226", rough=0.8)
    cube(m, (x, y + D_ / 2 - T_ / 2, H_ / 2), (W_, T_, H_))                     # 後ろ
    cube(m, (x - W_ / 2 + T_ / 2, y, H_ / 2), (T_, D_, H_)); cube(m, (x + W_ / 2 - T_ / 2, y, H_ / 2), (T_, D_, H_))
    cube(m, (x, y, H_ - T_ / 2), (W_, D_, T_)); cube(m, (x, y, T_ / 2 + 0.04), (W_, D_, T_))
    cube(mi, (x, y + 0.05, H_ / 2), (W_ - 2 * T_ - 0.01, D_ - 0.12, H_ - 2 * T_ - 0.05))     # 中の暗がり（奥）
    for dx in (-0.18, 0.18):
        cube(mat("safe_foot", "#3A3E44", rough=0.5), (x + dx, y, 0.02), (0.06, D_ - 0.04, 0.04))
    hinge = empty((x - W_ / 2, y - D_ / 2 - 0.016, 0.0))
    cube(m, (W_ / 2, 0, H_ / 2 + 0.02), (W_, 0.03, H_ - 0.04), bevel=0.006, parent=hinge)
    cyl(mat("safe_dial", "#C9CCD1", rough=0.25, metal=0.9), (W_ / 2, -0.03, H_ / 2 + 0.06), 0.065, 0.025, rot=(R(90), 0, 0), verts=32, parent=hinge)
    cube(mat("safe_handle", "#C9CCD1", rough=0.25, metal=0.9), (W_ * 0.8, -0.03, H_ / 2 - 0.08), (0.03, 0.03, 0.12), parent=hinge)
    return hinge


def b_home4(cl):
    night_house()
    hg = safe_box(SAFE); track("safe", hg, 0.3)
    OPEN = -70.0
    key(hg, "rotation_euler", -100.0, (0, 0, R(OPEN)), "CONSTANT")
    M = MaruR((40.0, -40.0, 0.0), face=180.0, s=HOUSE_S); track("maru", M.body, 0.25); track("maru_top", M.body, 0.32)
    hm = head_holder(M)
    t_in = wv("22-03", "名札") - 0.05                  # 家の場面の頭（文ごとの絵：道の場面が 1.4 秒で、ほとんど見えなかった → 0.3 秒のばす）
    M.at(t_in - 0.05, loc=(0.98, 1.36, 0.0), face=180.0, interp="CONSTANT")
    # 名札：はじめ頭の上 → 金庫の中へ（写しの強さを 1→0 にして、金庫の中の置き場所へ）
    tg = nameplate((0.85, 2.05, 0.2), rot=(R(80), 0, 0), w=0.40, glow=0.5)
    tg_h = empty((0, 0, 0)); tg_h.parent = hm; tg_h.location = (0, 0, 0.02); tg_h.rotation_euler = (R(-45), 0, 0)      # 頭の上に立てて載せる（試しの絵：寝かせると、下からのカメラで頭にかくれた）
    t_put = t_in + 0.6
    follow(tg, tg_h, -50.0, 0.1, t_off=t_put, d_off=0.55)
    track("hometag", tg, 0.05)
    M.lean(t_put - 0.1, t_put + 0.6, 25.0)
    # 扉を頭で押して閉める（扉のはしは、まるロボの左前 0.22 m。向きを変えると 2.5 秒遅れたので、前へ押す）
    t_cl = wv("22-03", "しっかり") + 0.4
    M.push(t_cl - 0.15, 0.3)
    key(hg, "rotation_euler", t_cl, (0, 0, R(OPEN))); key(hg, "rotation_euler", t_cl + 0.45, (0, 0, 0))
    ev(t_cl + 0.45, "clunk", 0.45, "safe")
    # 22-04：ぴょん、ぴょん
    M.hops(wv("22-04", "ぴょん") - 0.3, n=2, height=0.14)
    ev(wv("22-04", "取り返し"), "beep_happy", 0.45, "maru_c")
    # 22-05：ソファにぴょんと乗る（場面の替わり目で、ソファの前へ置き直す）→ ほっ
    M.at(s("22-05") - 0.08, loc=(-1.5, 1.2, 0.0), face=180.0, interp="CONSTANT")
    M.jump(s("22-05") + 1.0, (-1.5, 1.85, 0.49))      # 座面のクッションの上（当たりの点検：0.38 だとクッションに 11 cm 沈み、0.95 では向きを変えるとき背もたれに当たった）
    M.sigh(e("22-05") + 0.6, sound=False)
    # 22-06：窓のほうを見る → 22-07：首をかしげる
    M.at(e("22-06") - 0.3, face=63.0)          # 0.40 倍のまるロボは向きを変えるのが遅い（117 度で約 4 秒）
    M.confused(wv("22-07", "安いから") - 0.1)


# ======================================================================== カット（4章）
CUTS4 = [
    ("E22a", b_e, s("22-01"), C((6.85, -0.5, 0.85), (7.85, -1.6, 0.42), 24), "E"),                                                     # 棚の側から、まるロボの顔：ぐっと前に乗り出す
    ("E22b", b_e, s("22-02"), C((6.0, -1.75, 0.85), (7.85, -0.75, 0.5), 28), "E"),     # 左前から：箱へ身を乗り出す・頭の名札・こちらへ走り出す（つなげたコマ：右の真横からは走り出しが遠ざかるだけだった）                                                   # 横の引き：箱にとびこみ、名札を頭に載せて走り出す
    ("E22c", b_e, s("22-03"), C((-17.6, -0.7, 0.7), (-14.6, 0.35, 0.42), 30), "E"),     # 近くの前から（試しの絵：遠くて暗く、まるロボが豆つぶだった）                                                   # 夜の道：こちらへ走ってくる
    ("A22c", b_home4, wv("22-03", "名札") - 0.05, C((1.95, 1.0, 0.75), (0.85, 1.75, 0.3), 30), "A"),                                 # 家：金庫に入れて閉める・ぴょんぴょん
    ("A22e", b_home4, s("22-05"), C((-1.0, -0.6, 0.9), (-1.5, 1.85, 0.45), 30), "A"),                                                # ソファ
    ("A22f", b_home4, s("22-06"), C((-2.2, 2.25, 1.0), (3.0, -0.3, 1.1), 26), "A"),                                                  # まるロボの肩ごしに窓
    ("A22f2", b_home4, wv("22-06", "だれも") - 0.15, C((2.2, -0.2, 1.4), (7.5, -0.6, 0.2), 30), "A"),                              # 窓の外：だれもいない夜の道
    ("A22g", b_home4, s("22-07"), C((0.1, 1.0, 0.8), (-1.5, 1.95, 0.6), 30), "A"),                                                   # まるロボの前：首をかしげる
    ("A23a", b_home4, s("23-01"), C((-1.5, 0.25, 0.7), (-1.5, 1.95, 0.62), 30), "A"),                                                # 正面：考える
    ("E23b", b_e, s("23-02"), C((-7.6, -1.7, 1.5), (-0.6, 0.0, 1.1), 30), "E"),                                                      # 道の後ろから、倉庫へ入るまるロボ
    ("E23c", b_e, s("23-03"), C((5.3, -1.35, 1.1), (8.5, -0.9, 0.5), 26), "E"),                                                      # 通路の後ろから、棚の前へ
    ("E23d", b_e, s("23-04"), C((6.45, -1.6, 1.25), (7.75, -0.33, 0.68), 30), "E"),                                                    # まるロボの肩ごしに、名札の列
    ("E23e", b_e, s("23-05"), C((6.25, -0.55, 0.75), (7.55, -1.05, 0.45), 26), "E"),     # 試しの絵：顔に寄りすぎた                                                   # まるロボの横の前：固まる・見比べる（小窓）
    ("E24a", b_e, s("24-01"), C((5.6, -2.0, 1.3), (7.6, -0.5, 0.75), 26, (5.9, -1.9, 1.25), (7.6, -0.5, 0.75), 26, d=16.5), "E"),    # 図の下：棚とまるロボ（ゆっくり寄る）
    ("E24b", b_e, s("24-04"), C((8.9, -1.9, 1.1), (7.4, -0.5, 0.7), 26, (8.7, -1.8, 1.05), (7.4, -0.5, 0.7), 26, d=18.0), "E"),     # 図の下：反対側から
    ("E24c", b_e, s("24-07"), C((5.6, -1.6, 1.2), (3.3, -0.6, 0.6), 26), "E"),                                                       # 影が箱を並べ直す
    ("E24d", b_e, s("24-08"), C((6.75, -0.5, 0.62), (7.55, -1.05, 0.42), 28), "E"),                                                  # まるロボの前の寄り：目の光が下がる
    ("E24e", b_e, s("24-09"), C((5.6, -2.0, 1.3), (7.6, -0.5, 0.75), 26), "E"),                                                      # 図の下
    ("E24f", b_e, s("24-10"), C((6.0, -1.9, 0.95), (7.5, -0.45, 0.65), 26), "E"),                                                      # 棚の名札とまるロボ：もう 1 枚ふえる
]
