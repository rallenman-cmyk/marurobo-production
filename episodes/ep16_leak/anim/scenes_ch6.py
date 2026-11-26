# 16本目 6章（S27〜S29）：昼の町の通り（G）。ドアがずらり → 鍵束を持った機械が次々に試す → まるロボの家の 2 つのドア（1 つ目だけ開く）
#   → 上から：別の通りで、同じ鍵のドアだけが次々に開く。scenes.py が scenes_ch5.py のあとに exec で読む。絵コンテ表：../絵コンテ_v1.md の「6章」
#   1〜5章の直しを最初から入れる：後ろへ跳ばない・物は急に出さない（機械は走って入ってくる・×は小さく出てふくらむ）・通り道はカメラから 2 m 以上・
#   声がまねする音（ガチャ）は鳴らす物を付けず言葉の時刻に・ため息は電子音なし・語り手の「？」は 1 文に 1 つ・会社の見た目を出さない
DOOR_Y = 1.5                                    # 通りの家の正面（ドアの面）の y。ドアは −y を向く
DOOR_W, DOOR_H = 0.9, 1.9
STREET_X = [2.0 + 1.6 * k for k in range(10)]   # 通りのドア 10 枚
SIGNS6 = ["bag", "play", "mail", "phone", "cake", "bldg", "note", "house", "bag", "play"]
HOME_X = (20.4, 22.0)                           # 1.6 m おき（試しの絵：1.4 m だと 2 軒のかべが重なり、黒い線が出た）                           # まるロボの家のドア（左＝青緑の縁・右＝だいだい色の縁）
STREET2_X = [30.0 + 1.6 * k for k in range(12)] # 29 の別の通り（上から）。同じ鍵のドア（青緑の縁）は終わりの 3 枚
TEAL2 = (8, 10, 11)
MACH_Y = 0.75                                   # 機械の通る線（ドアから 0.75 m）
KEY_Z = 1.0                                     # ドアノブの高さ
KH_DX = DOOR_W / 2 - 0.12                       # 鍵穴：ドアのまん中から右へ
KH_Z = KEY_Z - 0.09                             # 鍵穴の高さ（ノブの下）
MS6 = 0.72                                      # まるロボの大きさ（3章の市場と同じ）


def g_world():
    """昼の町：空・地面・道・歩道、家の正面のかべ（ドアの所はあけて、奥に部屋の箱）"""
    world("#CFE2EA", 1.0)
    sun(rot=(52, 0, 28), energy=3.2)
    cube(mat("g_ground", "#B9B2A4", rough=0.9), (24.0, 0.0, -0.06), (70.0, 30.0, 0.1))
    cube(mat("g_road", "#8C8E94", rough=0.85), (24.0, -0.6, -0.005), (70.0, 2.4, 0.02))
    cube(mat("g_walk", "#D8D2C6", rough=0.85), (24.0, 1.0, 0.0), (70.0, 1.0, 0.03))


def door_unit(x, sign=None, frame=None, wall="#EDE4D4", roof="#9B4A3A", name="d"):
    """家の正面 1 軒分（はば 1.6 m）：かべ（ドアの所はあける）・奥の部屋・ドア（ちょうつがいは左。内側へ開く）・鍵穴・看板・縁の色。
    返す：ドアの回る親（hinge）"""
    wm = mat("g_wall" + wall, wall, rough=0.8)
    h_ = 3.0; y0 = DOOR_Y + 0.15
    cube(wm, (x - 0.625, y0, h_ / 2), (0.35, 0.3, h_))                       # 左のかべ
    cube(wm, (x + 0.625, y0, h_ / 2), (0.35, 0.3, h_))                       # 右のかべ
    cube(wm, (x, y0, (DOOR_H + h_) / 2), (0.9, 0.3, h_ - DOOR_H))             # ドアの上のかべ
    cube(mat("g_roof" + roof, roof, rough=0.7), (x, y0 + 0.2, h_ + 0.1), (1.62, 0.8, 0.2))
    room_m = mat("g_room", "#F0D9A8", rough=0.9)
    cube(room_m, (x, DOOR_Y + 1.2, DOOR_H / 2), (0.86, 1.8, DOOR_H))           # 奥の部屋（ドアが開くと見える明るい部屋）
    cube(mat("g_roomfloor", "#9C7A56", rough=0.8), (x, DOOR_Y + 0.75, 0.01), (0.86, 1.2, 0.02))
    if frame:
        fm = glow_mat("g_frame" + frame, frame, 0.6)
        for dx in (-0.48, 0.48): cube(fm, (x + dx, DOOR_Y - 0.03, DOOR_H / 2), (0.07, 0.06, DOOR_H + 0.05))
        cube(fm, (x, DOOR_Y - 0.03, DOOR_H + 0.03), (1.03, 0.06, 0.07))
    hinge = empty((x - DOOR_W / 2, DOOR_Y, 0.0)); hinge.name = name
    cube(mat("g_door", "#7A5536", rough=0.6), (DOOR_W / 2, 0.025, DOOR_H / 2), (DOOR_W - 0.02, 0.05, DOOR_H - 0.01), bevel=0.01, parent=hinge)
    cyl(mat("g_knob", "#C9B074", rough=0.3, metal=0.8), (DOOR_W - 0.12, -0.03, KEY_Z), 0.035, 0.04, rot=(R(90), 0, 0), parent=hinge, verts=16)
    cube(mat("g_keyhole", "#1A1A1A", rough=0.9), (DOOR_W - 0.12, -0.002, KEY_Z - 0.09), (0.018, 0.004, 0.04), parent=hinge)
    if sign:
        plane(img_mat("g_sign_" + sign, os.path.join(TEX, "sign_" + sign + ".png"), emit=0.15), (x, DOOR_Y - 0.01, DOOR_H + 0.35), (0.82, 0.38), rot=(R(90), 0, 0))
    return hinge


def xmark3d(x, t_on):
    """試して開かなかったドアの上の、灰色の×（白い丸の板に灰色の×）。t_on で小さく出て、ふくらむ"""
    e = empty((x + 0.0, DOOR_Y - 0.06, DOOR_H - 0.28)); e.rotation_euler = (R(90), 0, 0)
    cyl(mat("g_xbase", "#EEF0F3", rough=0.6), (0, 0, 0), 0.17, 0.02, parent=e, verts=32)
    for a_ in (45, -45): cube(mat("g_xbar", "#7C838E", rough=0.6), (0, 0, 0.014), (0.26, 0.055, 0.01), rot=(0, 0, R(a_)), parent=e)
    key(e, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(e, "scale", t_on, (0.001,) * 3); key(e, "scale", t_on + 0.18, (1.15,) * 3); key(e, "scale", t_on + 0.3, (1, 1, 1))
    return e


class Mach:
    """鍵束を持った機械：灰色の小さな箱（車輪 4 つ）・前に赤い小さな目の光・上に細い腕（+y の向き＝ドアのほうへのびる）・腕の先に鍵束"""
    def __init__(self, loc):
        self.root = empty(loc)
        gm = mat("g_mach", "#8E949C", rough=0.4, metal=0.5)
        cube(gm, (0, 0, 0.27), (0.5, 0.38, 0.3), bevel=0.03, parent=self.root)
        cube(mat("g_machtop", "#6E747C", rough=0.4, metal=0.5), (0, 0, 0.44), (0.3, 0.26, 0.06), parent=self.root)
        for dx in (-0.17, 0.17):
            for dy in (-0.17, 0.17): cyl(mat("g_wheel", "#2A2C30", rough=0.7), (dx, dy, 0.08), 0.08, 0.05, rot=(R(90), 0, 0), parent=self.root, verts=20)
        sphere(glow_mat("g_macheye", "#FF4A3A", 6.0), (0.26, -0.08, 0.32), 0.03, parent=self.root, seg=12)
        self.arm = empty((0.0, 0.12, 0.47)); self.arm.parent = self.root          # 腕の付け根
        self.arm_l = empty((0, 0, 0)); self.arm_l.parent = self.arm                 # のびる所（scale の y）
        cyl(mat("g_arm", "#5E646C", rough=0.4, metal=0.6), (0, 0.5, 0), 0.022, 1.0, rot=(R(90), 0, 0), parent=self.arm_l, verts=12)
        self.tip = empty((0, 1.0, 0)); self.tip.parent = self.arm_l
        ring = empty((0, 0, 0)); ring.parent = self.tip; ring.scale = (1.0, 1.0 / 0.35, 1.0)     # 腕ののびで鍵束がのびないように（下で打ち消す）
        self.ring = ring
        for k, a_ in enumerate((-25, 0, 25)):
            key_obj((0, 0, 0), rot=(0, R(a_), R(90)), s=0.7, parent=ring)
        aim = math.atan2(KH_Z - 0.47, DOOR_Y - MACH_Y - 0.12)                      # 鍵穴へ向く角度（上へ）
        self.arm.rotation_euler = (aim, 0, 0)
        self.reach = math.hypot(KH_Z - 0.47, DOOR_Y - MACH_Y - 0.12) - 0.02       # のばしきった長さ（鍵の先が鍵穴）
        self.set_len(-100.0, 0.35, "CONSTANT")
        self.xs = []

    def set_len(self, t, L, interp="BEZIER"):
        key(self.arm_l, "scale", t, (1.0, L, 1.0), interp); key(self.ring, "scale", t, (1.0, 1.0 / L, 1.0), interp)

    def go(self, t0, t1, x, y=MACH_Y):
        x = x + KH_DX                                                              # 腕が鍵穴の前に来るように（v17 の点検：ドアのまん中を突いていた）
        key(self.root, "location", t0, tuple(self.root.location) if t0 < -50 else self._at(t0)); key(self.root, "location", t1, (x, y, 0.0))
        self._last = (t1, (x, y, 0.0))

    def _at(self, t):
        return getattr(self, "_last", (None, tuple(self.root.location)))[1]

    def put(self, t, x, y=MACH_Y):
        """場面の替わり目で置き直す。直前まで前の位置で止めておく（v17 の点検：前の位置から次の位置へ、するすると流れて画面から出た）"""
        if hasattr(self, "_last"): key(self.root, "location", t - 0.09, self._last[1], "CONSTANT")      # 2 コマ以上あける（SKILL：近いキーはつぶれる）
        x = x + KH_DX
        key(self.root, "location", t, (x, y, 0.0), "CONSTANT"); self._last = (t, (x, y, 0.0))

    def try_door(self, t, hinge=None, opens=False, x_on=True, dx=0.0, sound=True, gacha_t=None):
        """腕をのばして鍵を差す（0.35 秒）→ 開くなら、ドアが内側へ開く／開かないならドアがガタッとゆれて腕を戻す・×"""
        self.set_len(t - 0.01, 0.35); self.set_len(t + 0.35, self.reach)
        if sound: ev(t + 0.35, "tick", 0.3, "")
        if opens:
            tg = gacha_t if gacha_t is not None else t + 0.6
            key(hinge, "rotation_euler", tg - 0.01, (0, 0, 0)); key(hinge, "rotation_euler", tg + 0.9, (0, 0, R(-78)))
            self.set_len(tg + 0.05, self.reach); self.set_len(tg + 0.5, 0.35)
        else:
            if hinge is not None:
                key(hinge, "rotation_euler", t + 0.40, (0, 0, 0)); key(hinge, "rotation_euler", t + 0.48, (0, 0, R(-2.5))); key(hinge, "rotation_euler", t + 0.56, (0, 0, R(1.5))); key(hinge, "rotation_euler", t + 0.66, (0, 0, 0))
            if sound: ev(t + 0.45, "rattle", 0.25, "")
            self.set_len(t + 0.7, self.reach); self.set_len(t + 0.95, 0.35)
            if x_on: self.xs.append(xmark3d(self._at(t)[0] - KH_DX + dx, t + 0.8))


def b_g(cl):
    g_world()
    hs = [door_unit(x, sign=SIGNS6[k], wall=["#EDE4D4", "#DCE6EE", "#F0E0D8"][k % 3], roof=["#9B4A3A", "#5E6E86", "#7A8A5A"][k % 3], name="sd%d" % k)
          for k, x in enumerate(STREET_X)]
    for k, h_ in enumerate(hs): track("sdoor%d" % k, h_, KEY_Z)
    # まるロボの家（通りのつきあたり）：白いかべ、青緑の縁のドア（左）とだいだい色の縁のドア（右）
    hh = [door_unit(HOME_X[0], frame="#2FD9C8", wall="#F6F2EA", roof="#3E8C84", name="home0"), door_unit(HOME_X[1], frame="#F0943A", wall="#F6F2EA", roof="#3E8C84", name="home1")]
    track("hdoor0", hh[0], KEY_Z); track("hdoor1", hh[1], KEY_Z)
    # 29 の別の通り（上から見る）
    h2 = [door_unit(x, sign=SIGNS6[(k + 3) % len(SIGNS6)], frame=("#2FD9C8" if k in TEAL2 else None), wall=["#EDE4D4", "#DCE6EE", "#F0E0D8"][k % 3],
                    roof=["#9B4A3A", "#5E6E86", "#7A8A5A"][k % 3], name="s2d%d" % k) for k, x in enumerate(STREET2_X)]
    # ---- 機械
    mc = Mach((-6.0, MACH_Y, 0.0)); track("mach", mc.root, 0.4); track("keys", mc.tip, 0.0)
    mc.put(-100.0, -6.0)
    mc.go(s("27-04") - 0.2, wv("27-04", "やって来") + 0.6, 0.6)                    # 27-04：西から通りに入ってくる
    ev(s("27-04") + 0.2, "squeak", 0.2, "mach")
    mc.go(s("27-07") + 0.6, e("27-07") - 0.2, STREET_X[0])                         # 27-07：1 枚目のドアの前へ
    t1 = s("28-01") + 0.4
    mc.try_door(t1, hs[0])
    mc.go(t1 + 1.0, t1 + 1.8, STREET_X[1])
    # 28-02「ガチャ、ガチャ」：2 枚目で 2 回（言葉の時刻に、ガチャと鳴る物はつけない＝必ず鳴らす）
    g0, g1 = wv("28-02", "ガチャ"), wv("28-02", "ガチャ", 1)
    for g_ in (g0, g1):
        mc.set_len(g_ - 0.36, 0.35); mc.set_len(g_ - 0.01, mc.reach); mc.set_len(g_ + 0.2, 0.35)
        key(hs[1], "rotation_euler", g_ - 0.02, (0, 0, 0)); key(hs[1], "rotation_euler", g_ + 0.06, (0, 0, R(-2.5))); key(hs[1], "rotation_euler", g_ + 0.16, (0, 0, 0))
        ev(g_, "clunk", 0.4, "")
    mc.xs.append(xmark3d(STREET_X[1], g1 + 0.35))
    mc.go(g1 + 0.6, g1 + 1.2, STREET_X[2]); mc.try_door(g1 + 1.25, hs[2])
    # 28-03：休まずに 4〜10 枚目（1 枚 0.62 秒）
    tq = s("28-03") + 0.1
    for k in range(3, 10):
        mc.go(tq, tq + 0.25, STREET_X[k]); mc.try_door(tq + 0.25, hs[k], sound=(k % 2 == 0)); tq += 0.62
    # 28-04〜28-11：まるロボの家の前（場面の替わり目で置き直す）
    mc.put(s("28-04") - 0.07, HOME_X[0] - 2.5)
    mc.go(s("28-04") + 0.6, s("28-04") + 2.6, HOME_X[0])
    mc.try_door(wv("28-06", "差しこむ") - 0.2, hh[0], opens=True, gacha_t=wv("28-07", "ガチャッ"))
    ev(wv("28-07", "ガチャッ"), "clunk", 0.45, "")                                  # 声がまねする音（鳴らす物を付けない）
    ev(wv("28-07", "ガチャッ") + 0.2, "creak", 0.25, "hdoor0")
    mc.go(s("28-09") + 2.0, s("28-10") - 0.1, HOME_X[1])
    mc.try_door(s("28-10") + 0.4, hh[1], x_on=False)
    # 29：別の通りを上から。機械が西から東へ次々に（29-01）→ 同じ鍵のドアだけ開く（29-02）
    mc.put(s("29-01") - 0.07, STREET2_X[0] - 1.0)
    tq = s("29-01") + 0.4
    for k in range(8):
        mc.go(tq, tq + 0.22, STREET2_X[k]); mc.try_door(tq + 0.22, h2[k], sound=(k % 3 == 0)); tq += (e("29-01") - s("29-01") - 0.6) / 8
    tops = [wv("29-02", "使い回し") - 0.2, wv("29-02", "そこでも") - 0.1, wv("29-02", "開いて") - 0.1]
    for k, t_o in zip(TEAL2, tops):
        mc.go(t_o - 0.75, t_o - 0.45, STREET2_X[k]); mc.try_door(t_o - 0.45, h2[k], opens=True, gacha_t=t_o)
        ev(t_o + 0.1, "creak", 0.2, "")
    # ---- まるロボ
    M = MaruR((40.0, -40.0, 0.0), face=270.0, s=MS6); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75); track("maru_c", M.body, 0.35)
    M.at(s("27-04") - 0.3, loc=(-0.4, -0.35, 0.0), face=0.0, interp="CONSTANT")       # 通りのはし。道のほう（−y）を向いて立つ（西を向かせると、東への向き直りが 3.6 秒遅れた）
    M.surprise(wv("27-04", "機械") + 0.3)
    M.at(s("27-05") + 1.5, face=90.0)                                                  # 機械のほう（東）へ向き直る（face：0＝−y・90＝+x・180＝+y）
    M.walk(s("27-07") + 1.0, e("27-07") + 0.3, (STREET_X[0] - 1.3, -0.3))             # あとをつける
    M.at(s("28-03") - 0.07, loc=(STREET_X[3] - 1.2, -0.35, 0.0), face=90.0, interp="CONSTANT")
    M.walk(s("28-03") + 0.3, e("28-03") - 0.3, (STREET_X[3] + 1.6, -0.35))      # 計画の点検：6 m は 3 秒遅れた → 2.8 m
    M.at(s("28-04") - 0.07, loc=(HOME_X[0] - 1.4, -0.2, 0.0), face=90.0, interp="CONSTANT")   # 家の前（機械の左うしろ）
    M.at(s("28-05") + 0.2, face=140.0)                                                  # ドアと機械のほうを見る
    M.act(s("28-05") + 0.6, "rest", dur=2.0)                                             # 体をちぢめる（ドキドキ）
    M.act(s("28-06") + 0.2, "wake")
    M.surprise(s("28-08") + 0.1)                                                         # ぎょっ
    M.act(wv("28-12", "へなへな") - 0.2, "rest", dur=1.8)                               # へなへなと座りこむ（ため息は付けない：ため息のあとに座ると 2 秒遅れた）
    M.at(s("29-01") - 0.07, loc=(STREET2_X[6] + 0.8, -0.45, 0.0), face=180.0, interp="CONSTANT")   # 別の通りのまん中（ドアのほうを向く）
    M.act(s("29-01") + 0.1, "wake")
    M.shake(wv("29-03", "だれが") - 0.2)
    return None, M


# ======================================================================== カット（6章）
CUTS6 = [
    ("G27a", b_g, s("27-01"), C((-3.5, -4.0, 3.2), (9.0, 1.4, 1.0), 28), "G"),                                                         # 通りの西のはしから、高めの引き
    ("G27b", b_g, s("27-02"), C((1.0, -3.6, 1.4), (1.0, DOOR_Y, 1.2), 30, (7.0, -3.6, 1.4), (7.0, DOOR_Y, 1.2), 30, d=5.0), "G"),    # ドアの並びに沿って横へ（v17 の点検：10 m だと速くて目で追えない → 6 m）
    ("G27c", b_g, s("27-03"), C((4.4, -1.4, 2.1), (4.4, DOOR_Y, 2.25), 34, (8.4, -1.4, 2.1), (8.4, DOOR_Y, 2.25), 34, d=5.0), "G"),  # 看板の高さで横へ
    ("G27d", b_g, s("27-04"), C((2.2, -3.4, 1.5), (-1.6, 0.3, 0.4), 30), "G"),                                                         # 機械が西から来る・はしのまるロボ
    ("G27e", b_g, s("27-05"), C((1.85 + KH_DX, -0.75, 0.85), (0.6 + KH_DX, MACH_Y, 0.4), 32), "G"),                                                   # 機械の斜め前
    ("G27f", b_g, s("27-06"), C((1.0 + KH_DX, 0.55, 0.98), (0.64 + KH_DX, MACH_Y + 0.28, 0.84), 42), "G"),                                         # 鍵束の寄り（試しの絵：空ばかりだった → 機械の上の鍵束へ）
    ("G27g", b_g, s("27-07"), C((-2.4, -2.6, 1.6), (2.0, 0.6, 0.6), 28), "G"),                                                         # 機械とまるロボのうしろから
    ("G28a", b_g, s("28-01"), C((STREET_X[0] + 2.0, -1.2, 1.3), (STREET_X[0], DOOR_Y, 0.95), 30), "G"),                               # ドアの前（機械の横）
    ("G28b", b_g, s("28-02"), C((STREET_X[1] + 2.4, -2.2, 1.6), (STREET_X[1] + 0.4, 0.8, 0.8), 28), "G"),                            # 2 枚目で「ガチャ、ガチャ」
    ("G28c", b_g, s("28-03"), C((STREET_X[3] - 2.0, -4.6, 5.0), (STREET_X[7], DOOR_Y, 0.8), 26), "G"),                                # 高い所から：×が並んでいく
    ("G28d", b_g, s("28-04"), C((20.6, -4.2, 1.7), (20.6, DOOR_Y, 1.0), 30), "G"),                        # まるロボまで入れる（試しの絵：左のはしで切れた）                                                    # まるロボの家の正面
    ("G28e", b_g, s("28-05"), C((HOME_X[0] - 0.55, 0.95, 0.75), (HOME_X[0] - 1.4, -0.2, 0.42), 28), "G"),                            # まるロボの前（ドアの側）から寄る（試しの絵：背中しか見えなかった）
    ("G28f", b_g, s("28-06"), C((HOME_X[0] + 1.3, -0.4, 1.3), (HOME_X[0] + 0.1, DOOR_Y, 1.0), 30), "G"),                             # 青緑のドアの寄り（開く）
    ("G28g", b_g, s("28-08"), C((HOME_X[0] + 0.3, 0.6, 0.7), (HOME_X[0] - 1.4, -0.2, 0.45), 26), "G"),                               # まるロボの前：ぎょっ（開いたドアの側から）
    ("G28h", b_g, s("28-09"), C((21.1, -3.0, 1.5), (21.1, DOOR_Y, 1.0), 30), "G"),                                                    # 2D の下：家の正面
    ("G28i", b_g, s("28-10"), C((HOME_X[1] + 1.2, -1.7, 1.25), (HOME_X[1] - 0.1, DOOR_Y - 0.25, 0.75), 32), "G"),                    # だいだい色のドアと機械（v17 の点検：近すぎて腕の先しか見えず、試して開かないのが分からない）
    ("G28j", b_g, s("28-12"), C((HOME_X[0] - 1.1, 1.0, 0.6), (HOME_X[0] - 1.4, -0.2, 0.35), 28), "G"),                               # まるロボの前：座りこむ
    ("G29a", b_g, s("29-01"), C((STREET2_X[5] + 0.4, -5.0, 9.0), (STREET2_X[5] + 0.4, 0.8, 0.0), 26), "G"),                         # 別の通りを上から
    ("G29b", b_g, s("29-03"), C((STREET2_X[6] + 0.8, -3.4, 1.2), (STREET2_X[6] + 0.8, 0.9, 0.7), 30), "G"),                         # まるロボのうしろから両側のドア
]
