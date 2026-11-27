# 16本目 9章（S36〜S38）：自分でできること。
#   H（上から見た輪のまん中のまるロボ）→ G'（まるロボのドアの通り：錠の板をドアごとにちがう色に替えて回る・機械の赤い鍵は 1 枚しか合わない・
#   家の青緑のドアにも新しい錠と 2 つ目の錠・影は 2 つ目の錠で止まる）→ A'（夕方の家のスマホ：リンクを押さない・いつものアプリから・すぐ信じない）→
#   B・C（昼のお城：門番さんとまるロボが裏口のほうを向く・裏口の錠が新しくなる・2 つ目の錠）→ I（はなれた島の予備の倉庫）→ C（働く人がそれぞれの鍵で入る）→ H（輪が止まる）
#   scenes.py が scenes_ch8.py のあとに exec で読む。絵コンテ表：../絵コンテ_v1.md の「9章」
#   名前は 9章だけの物にする（前の部品・章の名前を上書きしない。collide_check.py が 0 であること）
#   1〜8章の直しを最初から入れる：後ろへ跳ばない・物は急に出さない（小さく出てふくらむ）・置き直しは前の位置で止めてから・
#   ため息やぼうぜんは電子音なし・会社の見た目を出さない・3D の中に字を書かない
G9_X = [2.0 + 1.6 * k for k in range(4)]                  # まるロボのドア 4 枚（青緑の縁）。5 枚だと、5 枚目のあと家まで行く時間がない
G9_SIGNS = ["bag", "play", "mail", "phone"]
G9_NEW = ["#E0574A", "#4A7BE0", "#5DBB63", "#A066D8"]   # 替えたあとの錠の板の色（ドアごとにちがう形＝ちがう鍵）
G9_HOME = (G9_X[-1] + 3.2, G9_X[-1] + 4.8)                # まるロボの家（青緑の縁・だいだい色の縁）。6章と同じ見た目
G9_HOMENEW = "#59C3F0"                                    # 28 で開いたドアの新しい錠（水色）
G9_GOLD = "#C9A24A"                                       # はじめの錠の板（全部同じ金色＝同じパスワード）
G9_MY = GDOOR_Y - 0.6                                     # まるロボがドアの前に立つ y（体の前がドアから少しはなれる）


def g9_plate(hinge, col0, col1, t_ch, name):
    """ドアの鍵穴のまわりの、丸い錠の板（鍵の形）。t_ch に、くるっと回って col0 → col1 に替わる（小さくなって、新しい色がふくらむ）"""
    root = empty((GDOOR_W - 0.13, -0.058, KEY_Z - 0.14)); root.parent = hinge
    out = []
    for k_, col in enumerate((col0, col1)):
        e_ = empty((0, 0, 0)); e_.parent = root
        cyl(glow_mat("g9pl" + col, col, 0.35), (0, 0, 0), 0.08, 0.010, rot=(R(90), 0, 0), parent=e_, verts=32)
        cube(mat("g9_kh", "#1A1A1A", rough=0.9), (0, -0.007, -0.006), (0.014, 0.004, 0.034), parent=e_)
        out.append(e_)
    a_, b_ = out
    if t_ch is None:
        b_.scale = (0.001,) * 3; key(b_, "scale", -100.0, (0.001,) * 3, "CONSTANT")
        return root
    key(a_, "scale", -100.0, (1, 1, 1), "CONSTANT"); key(a_, "scale", t_ch - 0.02, (1, 1, 1)); key(a_, "scale", t_ch + 0.18, (0.001,) * 3)
    key(a_, "rotation_euler", t_ch - 0.02, (0, 0, 0)); key(a_, "rotation_euler", t_ch + 0.18, (0, R(180), 0))
    key(b_, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(b_, "scale", t_ch + 0.12, (0.001,) * 3); key(b_, "scale", t_ch + 0.34, (1.2, 1.2, 1.2)); key(b_, "scale", t_ch + 0.46, (1, 1, 1))
    key(b_, "rotation_euler", t_ch + 0.12, (0, R(-180), 0)); key(b_, "rotation_euler", t_ch + 0.4, (0, 0, 0))
    ev(t_ch + 0.1, "click", 0.4, name)
    track(name, root, 0.0)
    return root


def lock2(parent, loc, face_rot, t_on, name, t_red=None):
    """2 つ目の錠：小さな黒い箱に、青緑の 4 つの点（字は書かない）。t_on で小さく出てふくらむ。t_red から点が赤く光る（止めた）"""
    root = empty(loc); root.parent = parent; root.rotation_euler = face_rot
    cube(mat("l2_box", "#22262C", rough=0.35, metal=0.4), (0, 0, 0), (0.12, 0.035, 0.15), bevel=0.012, parent=root)
    dm = mat("l2_dot", "#2FD9C8", rough=0.4)
    b_ = dm.node_tree.nodes["Principled BSDF"]; b_.inputs["Emission Color"].default_value = srgb("#2FD9C8")
    ein = b_.inputs["Emission Strength"]; cin = b_.inputs["Emission Color"]
    ein.default_value = 3.0; ein.keyframe_insert("default_value", frame=f(-100.0))
    cin.default_value = srgb("#2FD9C8"); cin.keyframe_insert("default_value", frame=f(-100.0))
    if t_red is not None:
        cin.default_value = srgb("#2FD9C8"); cin.keyframe_insert("default_value", frame=f(t_red - 0.02))
        cin.default_value = srgb("#FF3B2F"); cin.keyframe_insert("default_value", frame=f(t_red + 0.06))
        ein.default_value = 3.0; ein.keyframe_insert("default_value", frame=f(t_red - 0.02))
        ein.default_value = 6.0; ein.keyframe_insert("default_value", frame=f(t_red + 0.06))
    for dx in (-0.028, 0.028):
        for dz in (-0.03, 0.03):
            cube(dm, (dx, -0.019, dz), (0.03, 0.006, 0.03), parent=root)
    key(root, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(root, "scale", t_on, (0.001,) * 3); key(root, "scale", t_on + 0.2, (1.2, 1.2, 1.2)); key(root, "scale", t_on + 0.32, (1, 1, 1))
    ev(t_on + 0.05, "tick", 0.35, name)
    track(name, root, 0.0)
    return root


def b_g9(cl):
    g_world()
    # ---- まるロボのドア 4 枚（青緑の縁）。錠の板ははじめ全部金色 → まるロボが 1 枚ずつ替える
    hs = [door_unit(x, sign=G9_SIGNS[k], frame="#2FD9C8", wall=["#EDE4D4", "#DCE6EE", "#F0E0D8"][k % 3], roof=["#9B4A3A", "#5E6E86", "#7A8A5A"][k % 3], name="g9d%d" % k)
          for k, x in enumerate(G9_X)]
    for k, h_ in enumerate(hs): track("g9door%d" % k, h_, KEY_Z)
    hh = [door_unit(G9_HOME[0], frame="#2FD9C8", wall="#F6F2EA", roof="#3E8C84", name="g9h0"), door_unit(G9_HOME[1], frame="#F0943A", wall="#F6F2EA", roof="#3E8C84", name="g9h1")]
    track("g9home0", hh[0], KEY_Z)
    # まるロボが替える時刻（頭で押してから 0.3 秒）。37-01 で 2 枚・37-02 で 2 枚 → 37-03 で家へ走る
    t0 = s("37-01") + 0.4
    t_push = [t0 + 2.6 * k for k in range(4)]                                  # 押す 0.6 秒＋横へ 3 回跳ぶ（歩く・走ると向きを変える分だけ 1〜1.6 秒遅れた）
    for k, h_ in enumerate(hs): g9_plate(h_, G9_GOLD, G9_NEW[k], t_push[k] + 0.3, "g9plate%d" % k)
    # 家の青緑のドア：37-04 で水色に。2 つ目の錠は 37-06「2つ目の錠」で。37-07 で影が止められて赤く光る
    t_home = wv("37-04", "新しい鍵") - 0.1
    g9_plate(hh[0], G9_GOLD, G9_HOMENEW, t_home + 0.3, "g9plateh")
    g9_plate(hh[1], "#AEB4BC", "#AEB4BC", None, "g9plateh1")
    t_l2 = wv("37-06", "2つ目の錠") - 0.1
    t_stop = wv("37-07", "入れません") - 0.6
    lock2(hh[0], (GDOOR_W - 0.12, -0.07, KEY_Z - 0.34), (0, 0, 0), t_l2, "g9lock2", t_red=t_stop)
    # ---- 37-03：機械（赤い鍵 1 本＝1 枚目のドアの鍵が漏れた）が来て、2 枚目・3 枚目に差す → 開かない（×）
    mc = Mach((-6.0, MACH_Y, 0.0)); track("g9mach", mc.root, 0.4); track("g9keys", mc.tip, 0.0)
    kids = [c for c in mc.ring.children]
    for j, c in enumerate(kids):
        if j != 1: c.scale = (0.001,) * 3                                       # 鍵は 1 本だけ
        else:
            for o in c.children:
                if o.type == 'MESH': o.data.materials[0] = mat("g9_redkey", G9_NEW[0], rough=0.3, metal=0.85)
    mc.put(-100.0, -6.0)
    ta = s("37-03")
    mc.put(ta - 0.07, G9_X[0] - 1.6)
    mc.go(ta + 0.1, ta + 1.1, G9_X[1]); ev(ta + 0.6, "squeak", 0.2, "g9mach")      # 画面に入ってから（組み立て：0.1 秒では映っていない扱いで鳴らなかった）
    mc.try_door(ta + 1.2, hs[1])
    mc.go(ta + 2.3, ta + 2.9, G9_X[2]); mc.try_door(ta + 3.0, hs[2])
    # ---- 37-07：影が来て、水色の鍵（盗まれた新しい鍵）を差す → カチャと回る → 2 つ目の錠で止まり、ドアはがたっ
    SHS = 0.76
    hx = G9_HOME[0] + KH_DX                                                      # 鍵穴の x
    sh = shadow((hx + 3.0, 0.2, 0.0), face=-90.0, s=SHS); track("g9shadow", sh.root, 1.5 * SHS)
    sh.root.scale = (0.001,) * 3; key(sh.root, "scale", -100.0, (0.001,) * 3, "CONSTANT")
    ts = s("37-07")
    pop_in(sh.root, ts + 0.1, SHS, 0.5); ev(ts + 0.45, "swish", 0.25, "g9shadow")      # 見えるくらい大きくなってから（組み立て：0.15 秒では映っていない扱いで鳴らなかった）
    SY = GDOOR_Y - 0.62                                                          # 影が立つ y（腕をのばして鍵の先が鍵穴に届く）
    key(sh.root, "location", ts + 0.1, (hx + 2.4, SY - 0.4, 0.0)); key(sh.root, "location", ts + 1.1, (hx, SY, 0.0))
    key(sh.root, "rotation_euler", ts + 0.1, (0, 0, R(-90))); key(sh.root, "rotation_euler", ts + 0.9, (0, 0, R(-90))); key(sh.root, "rotation_euler", ts + 1.3, (0, 0, R(-180)))
    sk = key_obj((0, 0, 0), rot=(0, 0, R(-90)), col=G9_HOMENEW, s=2.0, parent=sh.hand); sk.location = (0.0, -0.10, 0.0); track("g9skey", sk, 0.0)
    t_in = wv("37-07", "盗まれても") + 0.1
    key(sh.arm, "rotation_euler", ts + 1.2, (R(-60), 0, 0)); key(sh.arm, "rotation_euler", t_in, (R(-8), 0, 0))
    ev(t_in, "click", 0.4, "g9plateh")                                           # 鍵は合う（カチャと回る）
    hg = hh[0]
    for t_, a_ in ((t_stop - 0.02, 0.0), (t_stop + 0.08, 2.5), (t_stop + 0.18, -1.0), (t_stop + 0.3, 0.0)):
        key(hg, "rotation_euler", t_, (0, 0, R(a_)))                             # 押しても、2 つ目の錠で止まる
    ev(t_stop + 0.05, "rattle", 0.35, "g9lock2")
    t_out = e("37-07") - 0.9
    key(sh.arm, "rotation_euler", t_stop + 0.6, (R(-8), 0, 0)); key(sh.arm, "rotation_euler", t_stop + 1.0, (R(-60), 0, 0))
    pop_out(sh.root, t_out, SHS, 0.4); ev(t_out, "swish", 0.25, "g9shadow")     # 止められて、その場ですっと消える（試しの絵：去るときカメラの前を大きく横切った）
    # ---- まるロボ（0.72 倍）
    M = MaruR((G9_X[0], G9_MY, 0.0), face=180.0, s=MS6); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75); track("maru_c", M.body, 0.35)
    # 36-02：家の前で考える（目の光を上へ・首をかしげる）→ 36-03「でも」でひらめく
    M.at(s("36-02") - 0.12, loc=(G9_HOME[0] - 1.1, G9_MY - 0.35, 0.0), face=15.0, interp="CONSTANT")
    M.at(s("36-02") + 0.6, look=18); M.tilt(s("36-02") + 0.8, 12, 0.5)
    M.tilt(wv("36-03", "でも") - 0.1, 0, 0.2); M.at(wv("36-03", "でも"), look=0)
    M.surprise(wv("36-03", "でも") + 0.05); M.glow(wv("36-03", "でも") + 0.05, 1.3, 0.3)
    M.glow(e("36-04"), 0.9, 0.5)
    # 37-01〜37-03：1 枚ずつ、頭で押して替える → 次のドアへ歩く
    M.at(s("37-01") - 0.12, loc=(G9_X[0], G9_MY, 0.0), face=180.0, interp="CONSTANT")
    for k in range(4):
        M.push(t_push[k], 0.12)
        if k < 3:      # ドアのほうを向いたまま、横へ 3 回ぴょん（台本「跳ねるように移る」）
            ta_ = t_push[k] + 0.7; x0_ = G9_X[k]
            M.path([(x0_ + 0.533 * j, G9_MY, 0.0) for j in (1, 2, 3)], [ta_ + 0.42 * j for j in (1, 2, 3)], silent=False)
    # 37-03 の終わり〜37-04：4 枚目のあと、家の青緑のドアまで走る（置き直さない。場面の替わり目で消えて見えないように）→ 頭で押して替える
    M.run(t_push[3] + 0.6, s("37-03") + 3.6, (G9_HOME[0], G9_MY))
    M.at(s("37-04") + 0.7, face=180.0)                                          # 着いてからドアのほうを向く（走り終わりの向き直りは 2 秒かかる）
    M.push(t_home, 0.12)
    # 37-05：見上げてうなずく → ドアの左へよけて、2 つ目の錠と影を見る（37-06・37-07 はそこから）
    M.at(s("37-05") + 0.1, look=15); M.nod(wv("37-05", "もう1つ") - 0.1)
    M.at(wv("37-05", "もう1つ") + 0.6, look=0)
    M.hopto(wv("37-05", "もう1つ") + 2.1, (G9_HOME[0] - 0.36, G9_MY, 0.0)); M.hopto(wv("37-05", "もう1つ") + 3.4, (G9_HOME[0] - 0.72, G9_MY, 0.0))     # ドアのほうを向いたまま、横へよける
    M.nod(wv("37-07", "入れません") + 0.1)
    return None, M


# ======================================================================== A'：夕方の家のスマホ（37-08〜37-11）
def b_house9(cl):
    room(window=True); town_view(); evening_light()
    t_tap = wv("37-09", "いつものアプリ") - 0.2
    ph, scr = phone_seq(PH, 90.0, [(0.0, os.path.join(TEX, "ph_mail2.png")), (t_tap + 0.15, os.path.join(TEX, "ph_home.png"))], glow=1.6)
    track("phone", ph, 0.0)
    M = MaruR((1.72, 0.62, 0.0), face=90.0, s=HOUSE_S); track("maru", M.body, 0.25); track("maru_top", M.body, 0.32); track("maru_c", M.body, 0.12)
    M.at(s("37-08") + 0.3, look=-20)
    M.shake(wv("37-08", "押さない") - 0.2)                                      # リンクは押さない（首を横に振る）
    M.at(e("37-08"), look=0)
    M.push(t_tap - 0.1, 0.12); ev(t_tap + 0.05, "tap", 0.35, "phone")            # いつものアプリから入る（頭でちょんと押す）
    M.confused(wv("37-10", "名前で") + 0.2)                                      # 名前で呼ばれても → 首をかしげる（うたがう）
    M.squint(wv("37-10", "信じない") - 0.2, -0.3, 0.3); M.squint(e("37-10") + 0.1, 0.0, 0.3)
    M.nod(wv("37-11", "だまされにくく") - 0.1)
    return None, M


# ======================================================================== B・C：昼のお城（38-01〜38-03・38-06）
C9_LOCK = (0.12, DOOR_W - 0.14, 0.82)                    # 錠の板の上の場所（扉の板の上。1章と同じ）


def b_castle9(cl):
    C_, gk = _castle_common(False)
    hg = C_["door"]
    # 38-01：門番さんとまるロボが並んで、「お城の側」で右（裏口のほう）を向く
    M = MaruR((GK[0] - 1.0, GK[1] - 0.1, 0.0), face=0.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75); track("maru_c", M.body, 0.35)
    t_turn = wv("38-01", "お城の側") + 0.1
    key(gk.root, "rotation_euler", -100.0, (0, 0, 0), "CONSTANT"); key(gk.root, "rotation_euler", t_turn, (0, 0, 0)); key(gk.root, "rotation_euler", t_turn + 0.6, (0, 0, R(70)))
    M.at(t_turn + 0.15, face=70.0)
    # 38-02：古い錠が小さくなって消え、「新しい物」で銀の錠が出る
    t_new = wv("38-02", "新しい物")
    old = C_["lock"]["root"]
    key(old, "scale", -100.0, (1, 1, 1), "CONSTANT"); key(old, "scale", t_new - 0.45, (1, 1, 1)); key(old, "scale", t_new - 0.2, (0.001,) * 3)
    nl = old_lock((0, 0, 0), face=90.0, crack=False); nr = nl["root"]; nr.parent = hg; nr.location = C9_LOCK
    for o in nr.children:
        if o.type == 'MESH' and o.data.materials:
            nm0 = o.data.materials[0].name
            if nm0.startswith("rustlock"): o.data.materials[0] = mat("c9_newlock", "#C9D1DA", rough=0.18, metal=0.9)
            elif nm0.startswith("shackle"): o.data.materials[0] = mat("c9_newshackle", "#E2E7EC", rough=0.15, metal=0.95)
    key(nr, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(nr, "scale", t_new - 0.1, (0.001,) * 3); key(nr, "scale", t_new + 0.12, (1.2, 1.2, 1.2)); key(nr, "scale", t_new + 0.24, (1, 1, 1))
    ev(t_new, "click", 0.45, "c9lock"); track("c9lock", nr, 0.0)
    # 38-03：錠の下に 2 つ目の錠（37-06 と同じ形）
    lock2(hg, (0.0, DOOR_W - 0.14, 0.58), (0, 0, R(90)), wv("38-03", "2つ目の確かめ") - 0.1, "c9lock2")
    # 38-06：働く人が 3 人、それぞれちがう色の鍵を持って並ぶ。1 人目が差して、裏口が開いて入る
    wcols = [("#C8584A", "#7A6A5A"), ("#4A7BE0", "#5A6A7A"), ("#5DBB63", "#6A5A4A")]
    t6 = s("38-06") - 0.8                                                      # C38f の替わり目（一覧④がつなぎのあとに出るように 0.8 秒前から）
    qpos = [(X_SIDE + 0.95, DOOR_Y + 0.25), (X_SIDE + 1.05, DOOR_Y - 0.6), (X_SIDE + 1.1, DOOR_Y - 1.45)]      # かべにそって横に並ぶ（試しの絵：カメラのほうへ並ぶと、手前の人が裏口をかくした）
    wks = []
    for j, ((kc, sc), (qx, qy)) in enumerate(zip(wcols, qpos)):
        wk = walker((60.0 + j * 2, 60.0, 0.0), -90.0, shirt=sc, pants="#2D3640", hair=["#2B2220", "#5A3A22", "#3A3026"][j], s=0.78)
        key(wk.root, "location", -100.0, (60.0 + j * 2, 60.0, 0.0), "CONSTANT"); key(wk.root, "location", t6 - 0.12, (qx, qy, 0.02), "CONSTANT")
        key(wk.root, "rotation_euler", t6 - 0.12, (0, 0, R(-90)), "CONSTANT")
        ky = key_obj((0, 0, 0), rot=(0, 0, R(-90)), col=kc, s=3.2, parent=wk.arms[1]); ky.location = (0.0, -0.06, -0.62); track("c9wkey%d" % j, ky, 0.0)
        key(wk.arms[1], "rotation_euler", t6 - 0.12, (R(-35), 0, 0), "CONSTANT")       # 鍵を前に出して持つ
        wks.append(wk); track("c9wk%d" % j, wk.head, 0.2)
    t_key = wv("38-06", "使い回さない") - 0.2
    w0 = wks[0]
    key(w0.arms[1], "rotation_euler", t_key - 0.5, (R(-35), 0, 0)); key(w0.arms[1], "rotation_euler", t_key, (R(-62), 0, 0))
    ev(t_key + 0.05, "click", 0.4, "c9lock")
    t_op = t_key + 0.7
    key(hg, "rotation_euler", -100.0, (0, 0, 0), "CONSTANT"); key(hg, "rotation_euler", t_op, (0, 0, 0)); key(hg, "rotation_euler", t_op + 1.4, (0, 0, R(-94))); ev(t_op, "creak", 0.35, "door")
    key(w0.arms[1], "rotation_euler", t_op - 0.1, (R(-62), 0, 0)); key(w0.arms[1], "rotation_euler", t_op + 0.3, (R(-10), 0, 0))
    wk_walk(w0, t_op + 0.6, t_op + 2.4, qpos[0], (X_SIDE - 0.9, DOOR_Y), -90.0)
    pop_out(w0.root, t_op + 2.45, 0.78, 0.15)
    wk_walk(wks[1], t_op + 1.4, t_op + 2.6, qpos[1], (qpos[0][0] + 0.1, qpos[0][1] - 0.05), -90.0)
    wk_walk(wks[2], t_op + 1.7, t_op + 2.9, qpos[2], (qpos[1][0], qpos[1][1]), -90.0)
    # まるロボと門番さんは、裏口の横で見ている（38-06 のカットの替わり目で置き直す）
    key(gk.root, "location", -100.0, tuple(gk.root.location), "CONSTANT"); key(gk.root, "location", t6 - 0.12, (X_SIDE + 2.7, DOOR_Y + 1.7, 0.0), "CONSTANT")
    key(gk.root, "rotation_euler", t6 - 0.12, (0, 0, R(-60)), "CONSTANT")
    M.at(t6 - 0.12, loc=(X_SIDE + 2.0, DOOR_Y + 1.5, 0.0), face=-57.0, interp="CONSTANT")
    M.nod(wv("38-06", "守る") - 0.1)
    return C_, M


# ======================================================================== I：はなれた島の予備の倉庫（38-04〜38-05）
I_CASTLE = (-3.2, 0.6)
I_SHED = (-1.0, -0.8)            # お城とつながった予備の倉庫
I_ISLE = (5.2, 0.4)              # 橋のない島の予備の倉庫
I_NT = 4


def _shed(x, y, roof="#4A7BE0"):
    """小さな倉庫（白いかべ・青い屋根・青い扉）。前＝−y"""
    cube(mat("i_shedwall", "#F2F0EA", rough=0.8), (x, y, 0.32), (1.0, 0.75, 0.64))
    cube(mat("i_shedroof" + roof, roof, rough=0.6), (x, y, 0.69), (1.12, 0.86, 0.1))
    cube(mat("i_sheddoor", "#3E62B8", rough=0.6), (x, y - 0.38, 0.24), (0.34, 0.02, 0.44))


def _tiles_row(x, y, n, name, cols):
    """倉庫の前の、小さな名札（青緑の縁の白い札）の列。cols：[(時刻, 色)] で縁の色を変える（灰色＝使えない）"""
    m = mat("i_tile" + name, "#2FD9C8", rough=0.5)
    b_ = m.node_tree.nodes["Principled BSDF"]
    for t_, c_ in cols:
        b_.inputs["Base Color"].default_value = srgb(c_); b_.inputs["Base Color"].keyframe_insert("default_value", frame=f(t_))
    out = []
    for k in range(n):
        e_ = empty((x - 0.48 + k * 0.32, y - 0.75, 0.16)); out.append(e_)
        cube(m, (0, 0, 0), (0.28, 0.04, 0.2), parent=e_); cube(mat("i_tileface", "#FFFFFF", rough=0.6), (0, -0.022, 0), (0.22, 0.004, 0.14), parent=e_)
    return out


def b_isle(cl):
    world("#CFE6F3", 1.0); sun(rot=(50, 0, 30), energy=3.2)
    plane(mat("i_sea", "#4F8FC0", rough=0.15), (0, 0, -0.05), (60, 60))
    cube(noise_mat("i_land", "#7DB36A", "#6FA35E", 6.0, 0.95), (-6.0, 0.0, -0.06), (10.0, 9.0, 0.2))      # お城の陸（左）
    cyl(noise_mat("i_isle", "#86B86F", "#76A85F", 6.0, 0.95), (I_ISLE[0], I_ISLE[1], -0.06), 1.5, 0.2, verts=48)   # 橋のない島（右）
    cyl(mat("i_sand", "#E4D6AE", rough=0.9), (I_ISLE[0], I_ISLE[1], -0.07), 1.7, 0.18, verts=48)
    castle_model((I_CASTLE[0], I_CASTLE[1], 0.04), 2.4); track("i_castle", empty((I_CASTLE[0], I_CASTLE[1], 1.2)), 0.0)
    _shed(I_SHED[0], I_SHED[1]); _shed(I_ISLE[0], I_ISLE[1])
    cube(mat("i_path", "#CDBFA6", rough=0.9), ((I_CASTLE[0] + I_SHED[0]) / 2 + 0.3, (I_CASTLE[1] + I_SHED[1]) / 2, 0.045), (2.0, 0.5, 0.02), rot=(0, 0, math.atan2(I_SHED[1] - I_CASTLE[1], I_SHED[0] - I_CASTLE[0])))   # お城と倉庫はつながっている
    track("i_shed", empty((I_SHED[0], I_SHED[1], 0.9)), 0.0); track("i_isle", empty((I_ISLE[0], I_ISLE[1], 0.9)), 0.0)
    t_lock = wv("38-05", "錠を") - 0.1
    t_back = wv("38-05", "元に戻せ") - 0.1
    # お城の倉庫の名札：錠をかけられると灰色、戻ると青緑
    _tiles_row(I_SHED[0], I_SHED[1], I_NT, "home", [(-100.0, "#2FD9C8"), (t_lock + 0.2, "#2FD9C8"), (t_lock + 0.5, "#8C939C"), (t_back + 1.0, "#8C939C"), (t_back + 1.3, "#2FD9C8")])
    # 38-04「置いて」：写しが、お城の倉庫から島へ弧をえがいて飛び、島の倉庫の前に並ぶ（そのまま残る）
    t_cp = wv("38-04", "置いて") - 0.3
    isle = _tiles_row(I_ISLE[0], I_ISLE[1], I_NT, "isle", [(-100.0, "#2FD9C8")])
    for k, o in enumerate(isle):
        x1, y1, z1 = tuple(o.location); x0, y0 = I_SHED[0] - 0.48 + k * 0.32, I_SHED[1] - 0.75
        ta = t_cp + 0.07 * k
        key(o, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(o, "scale", ta, (0.001,) * 3); key(o, "scale", ta + 0.1, (1, 1, 1))
        for j in range(6):
            u = j / 5.0; key(o, "location", ta + 0.9 * u, (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, 0.16 + 1.6 * math.sin(math.pi * u)))
    ev(t_cp + 0.1, "swish", 0.35, "i_isle")
    # 38-05「錠を」：お城の倉庫に大きな赤い錠 →「元に戻せ」：島から写しが戻り、赤い錠が消える
    lk = empty((I_SHED[0], I_SHED[1] - 0.45, 0.42)); rm = mat("i_redlock", "#D2262A", rough=0.25, metal=0.4)
    cube(rm, (0, 0, 0), (0.42, 0.14, 0.34), bevel=0.02, parent=lk)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0.24), rotation=(R(90), 0, 0), major_radius=0.13, minor_radius=0.03)
    o_ = bpy.context.object; o_.data.materials.append(mat("i_redshackle", "#9E1E22", rough=0.3, metal=0.7)); o_.parent = lk
    key(lk, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(lk, "scale", t_lock, (0.001,) * 3); key(lk, "scale", t_lock + 0.22, (1.15,) * 3); key(lk, "scale", t_lock + 0.34, (1, 1, 1))
    ev(t_lock + 0.2, "clunk", 0.45, "i_shed"); track("i_lock", lk, 0.3)
    key(lk, "scale", t_back + 1.0, (1, 1, 1)); key(lk, "scale", t_back + 1.25, (0.001,) * 3)
    back = _tiles_row(I_ISLE[0], I_ISLE[1], I_NT, "back", [(-100.0, "#2FD9C8")])
    for k, o in enumerate(back):
        x0, y0, z0 = tuple(o.location); x1, y1 = I_SHED[0] - 0.48 + k * 0.32, I_SHED[1] - 0.75
        ta = t_back + 0.06 * k
        key(o, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(o, "scale", ta, (0.001,) * 3); key(o, "scale", ta + 0.08, (1, 1, 1))
        for j in range(6):
            u = j / 5.0; key(o, "location", ta + 0.8 * u, (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, 0.16 + 1.6 * math.sin(math.pi * u)))
        key(o, "scale", ta + 0.8, (1, 1, 1)); key(o, "scale", ta + 0.86, (0.001,) * 3)       # 着いたら、お城の倉庫の札にとけこむ
    ev(t_back + 0.1, "swish", 0.35, "i_isle"); ev(t_back + 1.1, "pop", 0.35, "i_shed")
    return None, None


# ======================================================================== H：上から見た輪（36-01・38-07）
def b_ring9(cl):
    C_, M = b_ring(cl)
    # 36-01「もう何もできない？」：まるロボが下を向く（目の光は弱いまま）
    M.at(wv("36-01", "何も") - 0.2, look=-18)
    # 38-07「止める」：輪の上の点が光るのをやめ、灰色になる（順に）→「1人1人の鍵」でまるロボが目の光を戻してうなずく
    t_st = wv("38-07", "止める") - 0.1
    for k in range(20):
        m_ = bpy.data.materials.get("rg_dot%d" % k)
        if not m_: continue
        b_ = m_.node_tree.nodes["Principled BSDF"]; inp = b_.inputs["Emission Strength"]; bc = b_.inputs["Base Color"]
        tk = t_st + 0.04 * k
        inp.default_value = 3.0; inp.keyframe_insert("default_value", frame=f(tk))
        inp.default_value = 0.0; inp.keyframe_insert("default_value", frame=f(tk + 0.2))
        bc.default_value = srgb("#2FD9C8"); bc.keyframe_insert("default_value", frame=f(tk))
        bc.default_value = srgb("#9AA3AD"); bc.keyframe_insert("default_value", frame=f(tk + 0.2))
    M.at(s("38-07") - 0.1, look=0)
    M.glow(wv("38-07", "1人1人") - 0.2, 0.95, 0.4)
    M.nod(wv("38-07", "鍵でも") - 0.1)
    return C_, M


# ======================================================================== カット（9章）
#   H36a は 8章の最後の H35c と同じカメラで、0.8 秒前から始める（H35c の終わりを変えない＝PC で描いている物をそのまま使う）。
#   2D の一覧・図が出る文の頭では絵を替えない（図がつなぎの途中に出る。7章 v19 の点検）
CUTS9 = [
    ("H36a", b_ring9, s("36-01") - 0.8, C((1.6, -2.6, 1.3), (0.0, 0.0, 0.55), 30), "H"),                                    # 輪のまん中のまるロボ（H35c と同じ）
    ("G36b", b_g9, s("36-02"), C((G9_HOME[0] - 0.2, -3.6, 1.5), (G9_HOME[0] - 0.4, GDOOR_Y - 0.2, 0.8), 30, (G9_HOME[0] - 0.5, -3.0, 1.4), (G9_HOME[0] - 0.6, GDOOR_Y - 0.2, 0.8), 30, d=e("36-04") + 0.6 - s("36-02")), "G"),   # 家の前（考える → ひらめく。36-03・36-04 は 2D の図の下。ゆっくり寄る）
    ("G37a", b_g9, s("37-01"), C((G9_X[0] + 0.3, -2.9, 1.4), (G9_X[0] + 0.3, GDOOR_Y, 0.9), 30, (G9_X[3] + 0.3, -2.9, 1.4), (G9_X[3] + 0.3, GDOOR_Y, 0.9), 30, d=e("37-02") + 0.3 - s("37-01")), "G"),   # ドアの並びに沿って横へ（37-02 まで）
    ("G37c", b_g9, s("37-03"), C((G9_X[0] - 1.6, -2.6, 1.6), (G9_X[2] + 0.6, GDOOR_Y - 0.3, 0.7), 28), "G"),               # 機械と 1〜3 枚目（うしろでまるロボが家へ走る）
    ("G37d", b_g9, s("37-04"), C((G9_HOME[0] - 0.3, -2.8, 1.3), (G9_HOME[0] - 0.2, GDOOR_Y, 0.8), 30, (G9_HOME[0] - 0.1, -2.2, 1.2), (G9_HOME[0] - 0.1, GDOOR_Y, 0.8), 30, d=e("37-05") + 0.6 - s("37-04")), "G"),   # 家の青緑のドア（37-05 まで。ゆっくり寄る）
    ("G37e", b_g9, s("37-06"), C((G9_HOME[0] + 1.3, -0.4, 0.95), (G9_HOME[0] + 0.15, GDOOR_Y - 0.4, 0.7), 30), "G"),       # 青緑のドアとまるロボの寄り（2 つ目の錠）
    ("G37f", b_g9, s("37-07"), C((G9_HOME[0] + 2.3, -1.6, 1.3), (G9_HOME[0] + 0.1, GDOOR_Y - 0.3, 0.75), 28), "G"),        # 影とまるロボと 2 つの錠
    ("A37g", b_house9, s("37-08") - 0.9, C((2.35, -0.1, 0.55), (1.78, 0.62, 0.14), 26), "A"),                               # まるロボとスマホ（7章 A30b と同じ。一覧③がつなぎのあとに出るように 0.9 秒前から）
    ("A37h", b_house9, s("37-09"), C((1.97, 0.4, 0.36), (1.95, 0.65, 0.0), 32), "A"),                                       # スマホの寄り（7章 A30c と同じ）
    ("A37i", b_house9, s("37-10") - 0.9, C((2.45, 0.35, 0.42), (1.72, 0.62, 0.18), 30), "A"),                               # まるロボの前（7章 A30d と同じ。一覧④）
    ("A37j", b_house9, s("37-11"), C((2.6, -0.1, 0.75), (1.75, 0.62, 0.2), 30), "A"),                                       # まるロボとスマホ：うなずく（7章 A32b と同じ）
    ("B38a", b_castle9, s("38-01"), C((-2.4, -8.0, 1.8), (0.6, -1.0, 1.2), 28), "B"),                                       # 正面の引き：門番さんとまるロボ
    ("C38b", b_castle9, s("38-02") - 0.9, C((DX + 1.4, DOOR_Y + 1.1, 1.0), (DX + 0.1, DOOR_Y + 0.38, 0.72), 34, (DX + 1.2, DOOR_Y + 0.95, 0.95), (DX + 0.1, DOOR_Y + 0.38, 0.7), 34, d=e("38-03") + 1.4 - s("38-02")), "B"),   # 裏口の錠の寄り（38-03 まで。一覧①）
    ("I38d", b_isle, s("38-04") - 0.8, C((0.9, -7.8, 4.5), (0.9, 0.0, 1.0), 30, (0.9, -7.2, 4.1), (0.9, 0.0, 1.0), 30, d=e("38-05") + 1.4 - s("38-04")), "I"),   # お城と島の引き（38-05 まで。一覧③）
    ("C38f", b_castle9, s("38-06") - 0.8, C((DX + 6.0, DOOR_Y - 2.6, 1.0), (DX + 0.9, DOOR_Y + 0.15, 1.35), 28), "B"),       # 裏口の斜め前の引き：働く人 3 人・まるロボと門番さん（一覧④。点検：一覧が手前の人の頭にかかった → 低い所から、頭が画面のまん中の高さに来るように）
    ("H38g", b_ring9, s("38-07"), C((0.0, -0.5, 14.0), (0.0, 0.0, 0.0), 30), "H"),                                          # 真上の引き（H35b の終わりと同じ）
]
