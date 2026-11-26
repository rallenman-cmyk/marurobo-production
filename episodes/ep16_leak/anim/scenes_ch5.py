# 16本目 5章（S25〜S26）：影の部屋の低い机（F）。3 枚の札 → 手紙の絵が同時に光る → 重なって 1 冊の名簿 → 厚くなる
#   scenes.py が scenes_ch4.py のあとに exec で読む。絵コンテ表：../絵コンテ_v1.md の「5章」
#   1〜4章の直しを最初から入れる：後ろへ跳ばない（下がるときは後ずさり）・物は急に出さない・通り道はカメラから 2 m 以上・
#   声がまねする音はこの章にない・ため息は電子音なし・語り手の「？」は画面のすみ（overlays5.py）
DESK_H = 0.30                                   # 低い机の高さ（0.40 倍のまるロボの目が、机の上の高さ）
CARD_W = 0.15
CARDS5 = [("tag_maru", -0.19, "emb0"), ("tag_orange", 0.0, "emb3"), ("tag_green", 0.19, "emb2")]      # 試しの絵：緑の札に橙の印で分かりにくかった → 札と同じ色の印      # 左から：まるロボの名札・橙・緑（それぞれのお城の印）
MAIL_UV = {"tag_maru": (0.73, 0.72), "tag_orange": (0.2, 0.5), "tag_green": (0.8, 0.5)}               # 札の絵の中の手紙の位置（make_tex16.py の card と同じ）
MARU_DESK = (0.0, -0.50)                        # まるロボが立つ所（机の前のはしの前）


def f_room():
    """うす暗い影の部屋：暗い床とかべ、低い机、電気スタンド（暖かい光）、机のはしに、だいだい色に光る高い帽子"""
    world("#10141E", 0.25)      # 試しの絵：部屋が真っ暗で、机とまるロボしか見えなかった
    cube(mat("f_floor", "#2A2522", rough=0.9), (0, 0.5, -0.02), (8.0, 8.0, 0.04))
    cube(mat("f_wall", "#1E2230", rough=0.95), (0, 2.2, 1.4), (8.0, 0.1, 2.8))
    cube(mat("f_wall", "#1E2230", rough=0.95), (-3.0, 0.5, 1.4), (0.1, 6.0, 2.8))
    wood = mat("f_desk", "#5B4030", rough=0.6)
    cube(wood, (0, 0.0, DESK_H - 0.02), (0.90, 0.55, 0.04), bevel=0.008)
    for dx in (-0.40, 0.40):
        for dy in (-0.22, 0.22): cube(wood, (dx, dy, (DESK_H - 0.04) / 2), (0.05, 0.05, DESK_H - 0.04))
    # 電気スタンド（机の右奥）
    dk = mat("f_lamp", "#2C2F36", rough=0.4, metal=0.6)
    cyl(dk, (0.33, 0.17, DESK_H + 0.01), 0.05, 0.02, verts=24)
    cyl(dk, (0.33, 0.17, DESK_H + 0.13), 0.008, 0.24, verts=12)
    cyl(dk, (0.27, 0.12, DESK_H + 0.25), 0.045, 0.06, rot=(R(30), R(-30), 0), verts=24)
    sphere(glow_mat("f_bulb", "#FFE2B0", 5.0), (0.25, 0.10, DESK_H + 0.22), 0.018, seg=12)
    bpy.ops.object.light_add(type="SPOT", location=(0.24, 0.09, DESK_H + 0.30)); L = bpy.context.object
    L.data.energy = 30; L.data.spot_size = R(100); L.data.color = srgb("#FFD9A8")[:3]; L.data.shadow_soft_size = 0.05
    L.rotation_euler = (R(20), R(10), 0)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -1.2, 1.4)); A = bpy.context.object      # 札と、まるロボの顔が見えるだけの弱い明かり
    A.data.energy = 60; A.data.size = 1.6; A.data.color = srgb("#BFC8E8")[:3]; A.rotation_euler = (R(45), 0, 0)
    # 高い帽子（3章 21-08 の、箱ごと買っていった影の物。輪郭がだいだい色に光る）
    hat = empty((-0.36, 0.16, DESK_H)); hat.rotation_euler = (R(-6), 0, R(20))
    hm = _shadow_mat("#E0822E")
    cyl(hm, (0, 0, 0.006), 0.075, 0.012, parent=hat, verts=32); cyl(hm, (0, 0, 0.06), 0.045, 0.10, parent=hat, verts=32)


def mail_glow(card, tex, t_on):
    """札の手紙の絵の上に、黄色い光の輪（t_on で 0→1 にふくらむ。ずっと残る）"""
    u, v = MAIL_UV[tex]; h = CARD_W * 380 / 600
    bpy.ops.mesh.primitive_torus_add(location=((u - 0.5) * CARD_W, (0.5 - v) * h, 0.006), major_radius=0.016, minor_radius=0.0028)
    g = bpy.context.object; g.data.materials.append(glow_mat("f_mailglow", "#FFE066", 9.0)); g.parent = card
    key(g, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(g, "scale", t_on - 0.02, (0.001,) * 3); key(g, "scale", t_on + 0.12, (1.25,) * 3); key(g, "scale", t_on + 0.3, (1, 1, 1))
    return g


def book5(loc):
    """名簿（青緑の表紙の 1 冊。厚さは scale の z で変える）"""
    b = empty(loc)
    cube(mat("f_cover", "#1FA89A", rough=0.5), (0, 0, 0.012), (0.17, 0.22, 0.024), bevel=0.004, parent=b)
    cube(mat("f_pages", "#F4F1E8", rough=0.8), (0.006, 0, 0.012), (0.16, 0.205, 0.018), parent=b)
    plane(img_mat("f_cover_tag", os.path.join(TEX, "tag_maru.png")), (0, 0.0, 0.0245), (0.11, 0.07), parent=b)      # 表紙にまるロボの名札の絵（だれの名簿か分かる）
    return b


def b_f(cl):
    f_room()
    cards = []
    for k, (tex, x, emb) in enumerate(CARDS5):
        c = nameplate((x, 0.02, DESK_H + 0.006), rot=(0, 0, R(3 * (k - 1))), tex=tex, w=CARD_W, glow=0.25)
        track("card%d" % k, c, 0.0); cards.append(c)
        cube(mat("f_stand", "#3A3D44", rough=0.6), (x, 0.13, DESK_H + 0.035), (0.012, 0.012, 0.07))      # 札のうしろの、お城の印の立て札
        plane(img_mat("f_emb_" + emb, os.path.join(TEX, emb + ".png"), emit=0.3), (x, 0.124, DESK_H + 0.085), (0.06, 0.06), rot=(R(90), 0, 0))
    # 26-02：「同時に」で 3 つの手紙の絵が同じ時刻に光る（線でつながない）
    t_g = wv("26-02", "同時に") - 0.05
    for c, (tex, _x, _e) in zip(cards, CARDS5): mail_glow(c, tex, t_g)
    ev(t_g + 0.05, "ding", 0.3, "card1")
    # 26-04：3 枚がまん中へすべって重なる →「1冊」で名簿に替わる（重なった所で入れかえる。急に出さない）
    t_sl = wv("26-04", "重なって") - 0.2; t_bk = wv("26-04", "1冊") - 0.1
    for k, c in enumerate(cards):
        x0 = CARDS5[k][1]
        key(c, "location", -100.0, (x0, 0.02, DESK_H + 0.006), "CONSTANT"); key(c, "location", t_sl, (x0, 0.02, DESK_H + 0.006))
        key(c, "location", t_sl + 0.7, (0.0, 0.0, DESK_H + 0.006 + 0.008 * k))
        key(c, "scale", -100.0, (1, 1, 1), "CONSTANT"); key(c, "scale", t_bk, (1, 1, 1)); key(c, "scale", t_bk + 0.15, (0.001,) * 3)
    bk = book5((0.0, 0.0, DESK_H)); track("book", bk, 0.03)
    key(bk, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(bk, "scale", t_bk, (0.001,) * 3); key(bk, "scale", t_bk + 0.18, (1.1, 1.1, 1.1)); key(bk, "scale", t_bk + 0.32, (1, 1, 1))
    ev(t_bk + 0.15, "thud", 0.3, "book")
    # 26-07：名簿がむくむくと厚くなる（「くわしく」で）
    t_th = wv("26-07", "くわしく") - 0.6
    key(bk, "scale", t_th, (1, 1, 1)); key(bk, "scale", t_th + 1.4, (1.06, 1.06, 4.2))
    # まるロボ：左から歩いて来て、机の前で止まり、のぞく
    M = MaruR((40.0, -40.0, 0.0), face=90.0, s=HOUSE_S); track("maru", M.body, 0.25); track("maru_top", M.body, 0.40); track("maru_c", M.body, 0.15)
    M.at(s("25-01") - 0.3, loc=(-1.1, -0.62, 0.0), face=90.0, interp="CONSTANT")
    M.walk(s("25-01") + 0.1, e("25-01") - 1.3, MARU_DESK)
    M.at(e("25-01") + 0.4, face=180.0)                    # 計画の点検：歩いたあとの 90 度の向き直りが 1.5 秒遅れた → 歩きを早く終える
    M.peer(s("25-02") + 0.5, 1.6)
    M.confused(wv("25-06", "なぜ") + 0.1)
    M.surprise(t_g + 0.1)                                  # 光った瞬間、びくっ
    M.at(wv("26-07", "くわしく"), look=12)                 # ふくらむ名簿を見る
    # 26-09：後ずさりで 1 歩下がる（後ろへは跳ばない）
    M.backstep(wv("26-09", "一歩") - 0.3, 0.16)
    M.sigh(s("26-10") + 0.4, sound=False)                  # 体をちぢめる（電子音なし）
    M.glow(s("26-10") + 0.4, 0.45, d=1.2)
    M.glow(s("26-11") + 0.6, 0.9, d=0.6)
    M.at(s("26-11") + 0.5, look=14)                        # 名簿を見上げる
    return None, M


# ======================================================================== カット（5章）
CUTS5 = [
    ("F25a", b_f, s("25-01"), C((1.7, -2.3, 1.05), (-0.2, 0.0, 0.25), 30), "F"),                                       # 部屋の引き：机・帽子・歩いて来るまるロボ
    ("F25b", b_f, s("25-02"), C((-0.05, -1.0, 0.72), (0.0, 0.03, DESK_H), 30), "F"),                                   # まるロボの頭ごしに、机の上の 3 枚
    ("F25c", b_f, s("25-03"), C((0.0, -0.42, 0.58), (0.0, 0.05, DESK_H + 0.02), 30), "F"),                             # 橙の札と印に寄る
    ("F25d", b_f, s("25-04"), C((0.19, -0.42, 0.58), (0.19, 0.05, DESK_H + 0.02), 30), "F"),                           # 緑の札と印に寄る
    ("F25e", b_f, s("25-05"), C((0.75, -0.85, 1.15), (0.0, 0.04, DESK_H + 0.02), 30), "F"),                             # 机の正面の斜め上の引き：3 枚と 3 つの印（試しの絵：低いとまるロボの頭が手前をふさいだ）
    ("F25f", b_f, s("25-06"), C((-0.12, 0.95, 0.62), (0.0, -0.45, 0.25), 32), "F"),                                    # 机の向こうから：まるロボが首をかしげる（試しの絵：スタンドが手前をふさいだ → 反対側から）
    ("F26a", b_f, s("26-01"), C((0.0, -0.25, 0.86), (0.0, 0.02, DESK_H), 30), "F"),                                    # 札の真上ぎみ：手紙の絵が同時に光る（試しの絵：右の札の手紙がふちで切れた → 広く）
    ("F26b", b_f, s("26-03"), C((-0.15, 0.70, 0.55), (0.0, -0.45, 0.30), 30), "F"),                                    # 机の向こうから：まるロボの顔がびくっ（手前に光る札。試しの絵：うしろからで顔が見えなかった）
    ("F26c", b_f, s("26-04"), C((0.45, -0.75, 0.68), (0.0, 0.0, DESK_H), 30), "F"),                                    # 机の上の斜め：重なって名簿に
    ("F26d", b_f, s("26-05"), C((-0.6, -1.2, 0.8), (0.0, 0.0, 0.3), 30, (-0.5, -1.15, 0.78), (0.0, 0.0, 0.3), 30, d=12.0), "F"),   # 2D の名簿・小窓の下（ゆっくり）
    ("F26e", b_f, s("26-07"), C((0.85, -0.25, 0.50), (-0.1, -0.25, 0.32), 32), "F"),                                   # 横から：まるロボと、厚くなる名簿を並べて（試しの絵：まるロボの頭が手前をふさいだ）
    ("F26f", b_f, s("26-08"), C((1.6, -2.2, 1.1), (0.0, -0.1, 0.3), 30), "F"),                                         # 机の引き
    ("F26g", b_f, s("26-09"), C((1.25, -0.62, 0.42), (0.0, -0.62, 0.25), 30), "F"),                                    # まるロボの横：後ずさり
    ("F26h", b_f, s("26-10"), C((-0.22, 0.70, 0.78), (0.0, -0.70, 0.25), 30), "F"),                                    # 机の向こうの高い所から、まるロボの顔（試しの絵：スタンドと厚い名簿で顔がかくれた）
    ("F26i", b_f, s("26-11"), C((0.95, 0.95, 0.95), (0.0, -0.4, 0.3), 30), "F"),                                       # 机とまるロボの引き
]
