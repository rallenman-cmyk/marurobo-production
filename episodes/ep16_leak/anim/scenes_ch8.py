# 16本目 8章（S33〜S35）：想像（家のスマホ・入力の画面は 2D）→ 夜の別のお城（N'：1章の夜のお城と同じ形、石の色だけ赤茶色）で、
#   鍵が影の手に落ちてくる → 鍵束 → 会社で働く人の鍵が光る → 影が裏口へ → 「あれ？」1章の場面を小窓で（overlays8.py）→
#   上から見た輪（H）：5 つの所の台が言う順に光り、まるロボがまん中で見回して、ぼうぜんと立ちつくす。
#   scenes.py が scenes_ch7.py のあとに exec で読む。絵コンテ表：../絵コンテ_v1.md の「8章」
#   名前は 8章だけの物にする（前の部品・章の名前を上書きしない。collide_check.py が 0 であること）
N8_STONE = ("#B0735A", "#9A6150")               # 別のお城の石の色（赤茶色）
N8_START = (X_SIDE + 2.6, DOOR_Y - 3.0)         # 影が鍵を受け取る所（1章 12-02 で影が現れた所と同じ）


def _n8_hand(root_xy, s_):
    """影の手のおおよその世界の位置（腕を前へ R(-5) にしたとき）。落ちてくる鍵の行き先"""
    return (root_xy[0] + 0.30 * s_, root_xy[1] - 0.05 * s_ - 0.42 * s_, 1.12 * s_ - 0.04)


def n8_glow(name, col, keys):
    """光る素材：光の色を決め、(時刻, 強さ) で強さを動かす（はじめは光らない）"""
    m = mat(name, col, rough=0.4)
    b_ = m.node_tree.nodes["Principled BSDF"]; b_.inputs["Emission Color"].default_value = srgb(col)
    inp = b_.inputs["Emission Strength"]
    for t_, v_ in keys:
        inp.default_value = v_; inp.keyframe_insert("default_value", frame=f(t_))
    return m


def keyring8(parent, glow_t):
    """影の鍵束：輪 1 つに色のちがう鍵 4 本（金・銀・青緑・赤）。1 本（青緑）には小さなビルの札（会社で働く人の鍵）。glow_t で青緑の鍵と札が光る"""
    ring = empty((0, 0, 0)); ring.parent = parent; ring.location = (0.0, -0.06, -0.02)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), rotation=(R(90), 0, 0), major_radius=0.05, minor_radius=0.008)
    o = bpy.context.object; o.data.materials.append(mat("n8_ring", "#B9BEC6", rough=0.3, metal=0.9)); o.parent = ring
    keys = []
    for k, (col, a_) in enumerate((("#C9A24A", -40), ("#AEB4BC", -15), ("#2FD9C8", 12), ("#C8584A", 38))):
        ky = key_obj((0.0, 0.0, -0.05), rot=(0, R(90 + a_), 0), col=col, s=1.0, parent=ring); keys.append(ky)
    # 青緑の鍵の札（小さなビルの絵）
    tgm = n8_glow("n8_tag", "#F4F7FA", ((-100.0, 0.0), (glow_t - 0.05, 0.0), (glow_t + 0.25, 4.0), (glow_t + 3.0, 4.0), (glow_t + 3.6, 0.6)))
    cube(tgm, (0.03, -0.012, -0.12), (0.05, 0.006, 0.06), parent=keys[2])
    for zz in (-0.105, -0.12, -0.135):
        for xx in (0.02, 0.04):
            cube(mat("n8_win", "#30405A", rough=0.6), (xx, -0.016, zz), (0.01, 0.002, 0.008), parent=keys[2])
    track("n8_wkey", keys[2], 0.0)
    return ring


def b_night8(cl):
    C_, gk = _castle_common(True)
    m_ = bpy.data.materials.get("stone")                    # 別のお城：石の色だけ赤茶色に（形・カメラは 1章と同じ）
    if m_:
        for n_ in m_.node_tree.nodes:
            if n_.type == 'TEX_BRICK':
                n_.inputs["Color1"].default_value = srgb(N8_STONE[0]); n_.inputs["Color2"].default_value = srgb(N8_STONE[1])
    SHS = 0.76
    sh = shadow((N8_START[0], N8_START[1], 0.0), face=0.0, s=SHS); track("shadow", sh.root, 1.5 * SHS)
    t_c = wv("33-02", "影の手") - 0.1                       # 鍵が手に落ちてくる時刻
    pop_in(sh.root, s("33-02") - 0.3, SHS, 0.5); ev(s("33-02") - 0.2, "swish", 0.25, "shadow")
    key(sh.arm, "rotation_euler", t_c - 0.8, (R(-60), 0, 0)); key(sh.arm, "rotation_euler", t_c - 0.3, (R(-5), 0, 0))      # 手を前に出して受ける
    # 上から落ちてくる 1 本の鍵（受けたら消えて、手の鍵束が出る）
    hx, hy, hz = _n8_hand(N8_START, SHS)
    fk = key_obj((hx, hy, 3.2), rot=(0, 0, R(-90)), s=2.0); track("n8_fall", fk, 0.0)
    key(fk, "location", -100.0, (hx, hy, 3.2), "CONSTANT"); key(fk, "location", t_c - 0.5, (hx, hy, 3.2)); key(fk, "location", t_c, (hx, hy, hz + 0.05))
    hide_key(fk, -100.0, True); hide_key(fk, t_c - 0.5, False); hide_key(fk, t_c + 0.04, True)
    ev(t_c, "jingle", 0.45, "shadow")
    ring = keyring8(sh.hand, wv("33-04", "会社で働く人") - 0.1)
    ring.scale = (0.001, 0.001, 0.001); key(ring, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(ring, "scale", t_c, (0.001, 0.001, 0.001), "CONSTANT")
    key(ring, "scale", t_c + 0.04, (1.6, 1.6, 1.6))
    ev(wv("33-04", "会社で働く人") - 0.1, "tick", 0.35, "n8_wkey")
    # 鍵束を照らす小さな明かり（夜で暗い）
    bpy.ops.object.light_add(type='POINT', location=(hx + 0.5, hy - 0.6, hz + 0.5)); kl = bpy.context.object; kl.data.shadow_soft_size = 0.2; kl.data.color = (1.0, 0.88, 0.66)
    for t_, e_ in ((-100.0, 0.0), (t_c - 0.2, 0.0), (t_c + 0.2, 22.0), (e("33-04") + 0.3, 22.0), (e("33-04") + 0.8, 0.0)):
        kl.data.energy = e_; kl.data.keyframe_insert("energy", frame=f(t_))
    # 33-05：裏口のほうへ歩き出す → 33-06：裏口の前に着く（1章 12-02 と同じ道）
    t_w = s("33-05") + 0.2
    key(sh.arm, "rotation_euler", t_w, (R(-5), 0, 0)); key(sh.arm, "rotation_euler", t_w + 0.6, (R(-60), 0, 0))
    key(sh.root, "location", t_w, (N8_START[0], N8_START[1], 0.0)); key(sh.root, "location", s("33-06") + 0.6, (X_SIDE + 0.95, DOOR_Y + 0.25, 0.0))
    key(sh.root, "rotation_euler", t_w + 0.6, (0, 0, R(0))); key(sh.root, "rotation_euler", s("33-06") + 0.8, (0, 0, R(-90)))
    ev(t_w, "swish", 0.25, "shadow")
    # 34-01：鍵を取り出す（1章 12-03 と同じ形）→ 34-02 から錠の前で鍵を差しかけたまま（扉は開けない）
    t_up = s("34-01") + 0.3
    key(sh.arm, "rotation_euler", t_up, (R(-60), 0, 0)); key(sh.arm, "rotation_euler", t_up + 0.8, (R(-5), 0, 0))
    t_in = s("34-02") + 0.6
    key(sh.root, "location", t_in - 0.6, (X_SIDE + 0.95, DOOR_Y + 0.25, 0.0)); key(sh.root, "location", t_in + 0.4, (KX, KY, 0.0))
    key(sh.arm, "rotation_euler", t_in - 0.5, (R(-5), 0, 0)); key(sh.arm, "rotation_euler", t_in + 0.2, (R(KA), 0, 0))
    track("n8_key", ring, 0.0)
    # 錠の前で鍵束を照らす小さな明かり（1章 12-03〜12-05 と同じ所。v20 の点検：34-04 の鍵の寄りで鍵束が暗かった）
    bpy.ops.object.light_add(type='POINT', location=(X_SIDE + 0.6, DOOR_Y - 0.6, 1.7)); kl2 = bpy.context.object; kl2.data.shadow_soft_size = 0.2; kl2.data.color = (1.0, 0.85, 0.6)
    for t_, e_ in ((-100.0, 0.0), (s("34-01") - 0.1, 0.0), (s("34-01") + 0.3, 18.0), (s("35-01") + 1.0, 18.0)):
        kl2.data.energy = e_; kl2.data.keyframe_insert("energy", frame=f(t_))
    # まるロボ：石の台のかげからのぞく（1章 12-06 と同じ所）。34-02 で「！」（2D）
    M = MaruR((30.0, 30.0, 0.0), face=180.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    M.at(s("34-02") - 0.07, loc=(X_SIDE + 0.8, DOOR_Y + 1.8, 0.0), face=-20.0, interp="CONSTANT")      # 34-02 から（試しの絵：34-01 の横からの絵で、影のうしろに大きく映った）
    M.surprise(s("34-02") + 0.8)                                                  # 「！」と同じ時刻（場面のつなぎのあと）
    cube(_stone(), (LEDGE[0], LEDGE[1], 0.4), (0.5, 1.3, 0.8))            # 石の台（1章と同じ。まるロボのかくれる所）
    return C_, M


# ======================================================================== H：上から見た輪（35）
RING_R = 3.0
RING_A = [90.0, 18.0, -54.0, -126.0, 162.0]         # 上から時計回り：お城・市場・影の机・町のドアと家・次のお城
RING_NAME = ["st_castle", "st_market", "st_desk", "st_town", "st_next"]


def _ring_xy(a_deg, r=RING_R):
    return (r * math.cos(math.radians(a_deg)), r * math.sin(math.radians(a_deg)))


def _glow_disc(x, y, name, times):
    """所の台（丸い板）。times の (時刻, 光の強さ) で光る"""
    gm = n8_glow("rd_" + name, "#2FD9C8", times)
    d_ = cyl(gm, (x, y, 0.04), 0.95, 0.06, verts=48)
    cyl(mat("rd_base", "#DDE3EA", rough=0.7), (x, y, 0.01), 1.05, 0.02, verts=48)
    return d_


def b_ring(cl):
    world("#E9EEF3", 0.9); sun(rot=(30, 0, 20), energy=2.6)
    plane(mat("rg_floor", "#C9D3DD", rough=0.9), (0, 0, 0), (30, 30))
    # 言う順に光る時刻（35-02・35-03）→ 35-04 で全部
    t_lit = [wv("35-02", "お城") - 0.1, wv("35-02", "市場") - 0.1, wv("35-02", "影の机") - 0.1, wv("35-03", "町のドア") - 0.1, wv("35-03", "次のお城") - 0.1]
    t_all = wv("35-04", "輪になって") - 0.1
    for i, (a_, nm) in enumerate(zip(RING_A, RING_NAME)):
        x, y = _ring_xy(a_)
        _glow_disc(x, y, nm, [(-100.0, 0.0), (t_lit[i] - 0.05, 0.0), (t_lit[i] + 0.25, 2.2), (t_lit[i] + 1.4, 0.8), (t_all - 0.05, 0.8), (t_all + 0.3, 2.6)])
        ev(t_lit[i], "tick", 0.3, nm)
        tr = empty((x, y, 0.9)); track(nm, tr, 0.0)
    # 5 つの所の模型（上から見て分かる形）
    x, y = _ring_xy(RING_A[0]); castle_model((x, y, 0.07), 1.6)
    x, y = _ring_xy(RING_A[1])                                                   # 市場：台と、しまの屋根
    cube(mat("rg_stall", "#8A6A4A", rough=0.7), (x, y, 0.3), (0.9, 0.55, 0.5))
    for j in range(5): cube(mat("rg_awn%d" % (j % 2), "#E06A5A" if j % 2 == 0 else "#FFFFFF", rough=0.6), (x - 0.4 + j * 0.2, y, 0.68), (0.2, 0.75, 0.06))
    x, y = _ring_xy(RING_A[2])                                                   # 影の机：低い机と、青緑の名簿
    cube(mat("rg_desk", "#5A4636", rough=0.7), (x, y, 0.3), (0.95, 0.6, 0.06)); cube(mat("rg_book", "#1FA89A", rough=0.5), (x, y, 0.36), (0.4, 0.3, 0.06))
    for dx, dy in ((-0.4, -0.25), (0.4, -0.25), (-0.4, 0.25), (0.4, 0.25)): cube(mat("rg_desk", "#5A4636", rough=0.7), (x + dx, y + dy, 0.14), (0.05, 0.05, 0.28))
    x, y = _ring_xy(RING_A[3])                                                   # 町のドアとまるロボの家：ドア 3 枚の小さな家並みと、青緑の屋根の家
    for j in range(3):
        cube(mat("rg_wall", "#EDE4D4", rough=0.8), (x - 0.5 + j * 0.42, y + 0.25, 0.35), (0.38, 0.2, 0.7))
        cube(mat("rg_door", "#7A5536", rough=0.6), (x - 0.5 + j * 0.42, y + 0.14, 0.22), (0.16, 0.02, 0.38))
    cube(mat("rg_house", "#F6F2EA", rough=0.7), (x + 0.15, y - 0.35, 0.3), (0.55, 0.45, 0.6)); cube(mat("rg_hroof", "#3E8C84", rough=0.7), (x + 0.15, y - 0.35, 0.66), (0.62, 0.5, 0.12))
    x, y = _ring_xy(RING_A[4])                                                   # 次のお城（赤茶色の小さなお城）
    nc = castle_model((x, y, 0.07), 1.6)
    for ob in [o for o in bpy.data.objects if o.parent is nc]:                    # 次のお城は、かべを赤茶色・屋根を緑に（試しの絵：最初のお城と見分けがつかなかった）
        if ob.type == 'MESH' and ob.data.materials:
            nm0 = ob.data.materials[0].name
            if nm0.startswith("stone_model"): ob.data.materials[0] = mat("rg_nextwall", "#A0483A", rough=0.8)
            elif nm0.startswith("roof"): ob.data.materials[0] = mat("rg_nextroof", "#3F7A4A", rough=0.6)
    # 輪の上の点（35-04 で順に光って 1 周する）
    for k in range(20):
        a_ = 90.0 - k * 18.0; px, py = _ring_xy(a_, RING_R)
        if min(abs(((a_ - b_) + 180) % 360 - 180) for b_ in RING_A) < 12: continue
        tk = t_all + 0.1 + k * 0.08
        sphere(n8_glow("rg_dot%d" % k, "#2FD9C8", ((-100.0, 0.0), (tk - 0.02, 0.0), (tk + 0.08, 3.0), (e("35-05") + 0.3, 3.0))), (px, py, 0.08), 0.09, seg=16)
    # まるロボ：輪のまん中。光る所を順に向き、35-06 でくるっと 1 回まわって、ぼうぜんと止まる
    M = MaruR((0.0, 0.0, 0.0), face=180.0, s=0.9); track("maru", M.body, 0.75); track("maru_top", M.body, 0.95); track("maru_c", M.body, 0.4)
    for i, a_ in enumerate(RING_A):
        M.at(t_lit[i] + 0.2, face=(a_ + 90.0) % 360.0, fast=True)               # 光る所を向く（face：0＝−y・90＝+x・180＝+y・270＝−x）
    FCAM = 32.0                                                                  # 35-06 のカメラのほう
    M.at(t_all + 1.2, face=FCAM, fast=True)
    t6 = s("35-06") + 0.3                                                        # くるっと 1 回まわって（120° を 3 回）、カメラのほうで止まる
    for k in range(1, 4): M.at(t6 + 0.75 * k, face=(FCAM + 120.0 * k) % 360.0, fast=True)      # 0.45 秒おきでは 1.1 秒遅れた
    M.glow(t6 + 2.6, 0.45, 0.6)                                                  # ぼうぜん：目の光を落とす（電子音なし）
    return None, M


# ======================================================================== カット（8章）
#   2D の札の下で絵を替えない（札がつなぎの途中に出る。7章 v19 の点検）。想像の色は 2D（tint）で 33-01〜33-06
CUTS8 = [
    ("A33a", b_house7, s("33-01"), C((1.97, 0.4, 0.36), (1.95, 0.65, 0.0), 32), "A"),                                         # スマホの寄り（入力の画面は 2D）
    ("N33a", b_night8, s("33-02"), C((X_SIDE + 4.4, DOOR_Y - 4.6, 1.4), (N8_START[0], N8_START[1], 1.0), 30), "N"),            # 夜の別のお城の前の影（横から）
    ("N33b", b_night8, s("33-03"), C((N8_START[0] + 0.95, N8_START[1] - 1.25, 1.05), (N8_START[0] + 0.23, N8_START[1] - 0.36, 0.84), 40), "N"),   # 鍵束の寄り
    ("N33d", b_night8, s("33-05"), C((DX + 5.0, DOOR_Y - 5.0, 2.2), (DX + 0.6, DOOR_Y, 0.9), 28), "N"),                          # 1章 N12 と同じ引き
    ("N34a", b_night8, s("34-01"), C((DX + 0.6, DOOR_Y - 1.3, 1.3), (DX + 0.35, DOOR_Y + 0.15, 1.1), 32), "N"),                 # 1章 N12b と同じ横から
    ("N34b", b_night8, s("34-02"), C((DX + 3.6, DOOR_Y - 1.8, 1.3), (DX + 0.4, DOOR_Y, 0.9), 30), "N"),                          # 影とまるロボ（1章 N12e と同じ）
    ("N34c", b_night8, s("34-04"), C((DX + 1.7, DOOR_Y - 0.6, 1.1), (DX + 0.2, DOOR_Y + 0.3, 0.85), 32), "N"),                  # 鍵を差す所の寄り（1章 N12c と同じ向き。34-05 の見比べの右の絵。v20 の点検：横からだと影のうしろにまるロボが大きく映った）
    ("H35a", b_ring, s("35-01"), C((0.0, -0.4, 15.0), (0.0, 0.0, 0.0), 30, (0.0, -0.4, 12.0), (0.0, 0.0, 0.0), 30, d=4.0), "H"),   # 真上から、ゆっくり下りる
    ("H35b", b_ring, s("35-04"), C((0.0, -0.4, 12.0), (0.0, 0.0, 0.0), 30, (0.0, -0.5, 14.0), (0.0, 0.0, 0.0), 30, d=6.0), "H"),   # 少し引く
    ("H35c", b_ring, s("35-06"), C((1.6, -2.6, 1.3), (0.0, 0.0, 0.55), 30), "H"),                                                  # まるロボの寄り（輪が後ろに）
]
