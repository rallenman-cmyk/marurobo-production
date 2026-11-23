# 16本目 2章（S13〜S17）：お城の中（D）・夜と朝のお城の外（O・M）・家のたとえ（A）・持ち主の部屋（D の中の OWN）・想像（I2）
#   scenes.py が CUTS を作る前に exec で読む（kit16b.py の部品を使う）。絵コンテ表：../絵コンテ_v1.md の「2章」
#   1章の直しを最初から入れる：ずっと流す音なし・長い音は小さく・扉の音は短く・効果音は鳴らす物のまん中の印で・動く物どうしも当てない
exec(open(os.path.join(KIT_HERE, "kit16b.py"), encoding="utf-8").read())
SHS2 = 0.76          # 影の大きさ（1章の夜と同じ）
_WT = json.load(open(os.path.join(KIT_HERE, "word_times_ch2.json"), encoding="utf-8"))


def wv(i, word, occ=0):
    """声の波形から取った言い始めの時刻（word_times_ch2.json）。ない言葉は w()（字数の見積もり）"""
    return _WT.get("%s|%s|%d" % (i, word, occ)) or w(i, word)
D_ = dict(IDOORS)
Y_ROOM = YB + WALL_T          # 部屋の入口側のかべの奥の面


def sh_key(sh, t, loc, face=None, interp="BEZIER"):
    key(sh.root, "location", t, (loc[0], loc[1], 0.0), interp)
    if face is not None: key(sh.root, "rotation_euler", t, (0, 0, R(face)), interp)


def door_key(name, t, deg, interp="BEZIER"):
    key(IN["door_" + name], "rotation_euler", t, (0, 0, R(deg)), interp)


def pop_lock(name, t, s=1.0):
    """赤い錠が扉に「ガチャン」とかかる（t＝扉に当たる時刻）：少し上から下りて、大きさ 0 → s"""
    lk = IN["lock_" + name]; z0 = lk.location[2]
    key(lk, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(lk, "scale", t - 0.12, (0.001, 0.001, 0.001)); key(lk, "scale", t, (s, s, s))
    key(lk, "location", t - 0.12, (lk.location[0], lk.location[1], z0 + 0.12)); key(lk, "location", t, (lk.location[0], lk.location[1], z0))
    ev(t, "clunk", 0.45, "lk_" + name)


def wk_walk(wk, t0, t1, p0, p1, face):
    """働く人（walker）を歩かせる：根もとを動かし、足を 0.3 秒ごとに交互にふる"""
    key(wk.root, "location", t0, (p0[0], p0[1], 0.02)); key(wk.root, "location", t1, (p1[0], p1[1], 0.02))     # 靴の底が床に 2 cm 入るので少し上げる
    key(wk.root, "rotation_euler", t0, (0, 0, R(face))); key(wk.root, "rotation_euler", t1, (0, 0, R(face)))
    n = max(2, int((t1 - t0) / 0.3))
    for k in range(n + 1):
        tt = t0 + (t1 - t0) * k / n; a = 0 if k in (0, n) else (18 if k % 2 else -18)
        key(wk.hips[0], "rotation_euler", tt, (R(a), 0, 0)); key(wk.hips[1], "rotation_euler", tt, (R(-a), 0, 0))
        key(wk.arms[0], "rotation_euler", tt, (R(-a * 0.7), 0, 0)); key(wk.arms[1], "rotation_euler", tt, (R(a * 0.7), 0, 0))


# ======================================================================== D：お城の中（13〜17）
def b_in(cl):
    inside()
    scr = work_room(people=True)
    dr = admin_room()
    store_room("tags", "tag_cust", special=(1, 3))
    store_room("backup", "tag_copy")
    for nm, x in IDOORS: red_lock(nm, 1.0 if nm != "backup" else 1.6); red_mark(nm)
    pad = owner_room()
    for nm, x in IDOORS: track("door_" + nm, IN["dc_" + nm], 0.0); track("lk_" + nm, IN["lock_" + nm], 0.0)
    # ---- 夜と昼（13-04 で夜昼が何度も替わる・13-05 は昼・16-10 からは朝）
    t4 = s("13-04")
    day_night([(-100.0, "night"), (t4 + 0.9, "day"), (t4 + 2.1, "night"), (t4 + 3.3, "day"), (t4 + 4.5, "night"), (s("13-05") - 0.2, "day"),
               (e("13-05") + 0.3, "night"), (s("16-10") - 0.3, "day")])
    for nm, e_ in (("work", 60.0), ("admin", 30.0), ("tags", 0.0), ("backup", 0.0)):
        light_key(IN["room_" + nm], -100.0, 0.0)
    light_key(IN["room_work"], s("13-05") - 0.3, 70.0); light_key(IN["room_work"], e("13-05") + 0.3, 0.0)
    light_key(IN["room_work"], s("16-10"), 70.0)
    light_key(IN["room_admin"], s("14-01") - 0.6, 35.0); light_key(IN["room_admin"], e("14-01") + 0.4, 0.0)
    light_key(IN["room_tags"], s("14-05"), 0.0); light_key(IN["room_tags"], s("14-05") + 0.6, 45.0); light_key(IN["room_tags"], e("15-04") + 0.5, 45.0); light_key(IN["room_tags"], e("15-04") + 1.0, 0.0)
    light_key(IN["room_backup"], s("14-07"), 0.0); light_key(IN["room_backup"], s("14-07") + 0.6, 45.0); light_key(IN["room_backup"], e("14-13") + 0.3, 45.0); light_key(IN["room_backup"], e("14-13") + 0.8, 0.0)      # 試しの絵：14-08・14-12 の部屋の中が真っ黒だった
    # ---- 影
    sh = shadow((-1.4, 0.25, 0.0), face=90.0, s=SHS2); track("shadow", sh.root, 1.5 * SHS2)
    key(sh.root, "scale", -100.0, (SHS2, SHS2, SHS2), "CONSTANT")
    # 13-01：裏口からの暗い通路から出てきて、立ち止まる（「でしょうか」）
    sh_key(sh, -100.0, (-1.4, 0.25), 90.0, "CONSTANT"); sh_key(sh, s("13-01") + 0.3, (-1.4, 0.25), 90.0); sh_key(sh, s("13-01") + 2.6, (0.9, 0.25), 90.0)
    # 13-02：「いいえ」のあと、足音を立てずに奥へ（すべるように。音なし）
    t_ = wv("13-02", "いいえ") + 0.6
    sh_key(sh, t_, (0.9, 0.25)); sh_key(sh, e("13-02") + 0.2, (6.6, 0.55))
    # 13-03：hall2 の扉を少し開けてのぞく → 閉める → tags の扉でも
    t_ = s("13-03") + 0.2
    sh_key(sh, t_, (6.6, 0.55)); sh_key(sh, t_ + 0.8, (D_["hall2"] - 0.2, 0.8), 150.0)
    door_key("hall2", t_ + 0.9, 0); door_key("hall2", t_ + 1.3, 28); door_key("hall2", t_ + 2.2, 28); door_key("hall2", t_ + 2.6, 0)
    ev(t_ + 0.9, "squeak", 0.25, "door_hall2")
    sh_key(sh, t_ + 2.4, (D_["hall2"] - 0.2, 0.8), 150.0); sh_key(sh, t_ + 3.4, (D_["tags"] - 0.2, 0.8), 150.0)
    door_key("tags", t_ + 3.5, 0); door_key("tags", t_ + 3.9, 28); door_key("tags", t_ + 4.6, 28); door_key("tags", t_ + 5.0, 0)
    ev(t_ + 3.5, "squeak", 0.25, "door_tags")
    # 13-05〜13-07 の間、影は奥（13 の手前）へ。13-08 で廊下を見渡す
    sh_key(sh, e("13-04"), (D_["tags"] - 0.2, 0.8), 90.0); sh_key(sh, s("13-08"), (11.8, 0.3), 90.0)
    for k, a in enumerate((90, 40, 140, 90)):
        key(sh.root, "rotation_euler", w("13-08", "すみずみ") - 1.0 + k * 0.9, (0, 0, R(a)))
    # 14-01：管理する人の部屋の机。引き出しを開けて、赤い鍵束を持ち上げる
    ta = s("14-01")
    sh_key(sh, ta - 0.4, (11.8, 0.3), 90.0, "CONSTANT"); sh_key(sh, ta - 0.3, (D_["admin"] - 0.15, Y_ROOM + 1.0), 0.0 + 180.0, "CONSTANT")   # 部屋の中（場面が替わる所で置き直す）
    key(dr, "location", -100.0, tuple(dr.location), "CONSTANT"); key(dr, "location", ta + 0.4, tuple(dr.location))
    key(dr, "location", ta + 1.1, (dr.location[0], dr.location[1] - 0.32, dr.location[2]))
    kb = key_bundle((dr.location[0], dr.location[1] + 0.2, dr.location[2] - 0.01), s=1.1); track("bundle", kb, 0.0)
    key(sh.arm, "rotation_euler", -100.0, (R(-60), 0, 0), "CONSTANT")
    key(kb, "location", ta + 1.1, (dr.location[0], dr.location[1] - 0.12, dr.location[2] - 0.01))
    key(sh.arm, "rotation_euler", ta + 0.6, (R(-60), 0, 0)); key(sh.arm, "rotation_euler", ta + 1.3, (R(-20), 0, 0))
    key(kb, "location", ta + 1.5, (dr.location[0], dr.location[1] - 0.12, dr.location[2] + 0.02))
    ev(ta + 1.6, "jingle", 0.35, "bundle")
    # 持ち上げた鍵束は、影の手に付ける（手の所まで動かしてから、手の子に替える＝16本目 17本目の「一瞬で移さない」）
    kb2 = key_bundle((0, 0, 0), parent=sh.hand, s=1.1 / SHS2 * 1.4); kb2.location = (0, -0.1, -0.08); track("bundle2", kb2, 0.0)
    key(kb2, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(kb2, "scale", ta + 2.35, (0.001, 0.001, 0.001), "CONSTANT"); key(kb2, "scale", ta + 2.4, (1.1 / SHS2 * 1.4,) * 3, "CONSTANT")
    IN["_bundle_handoff"] = (kb, kb2, ta + 1.5, ta + 2.35)
    key(sh.arm, "rotation_euler", ta + 2.4, (R(5), 0, 0))
    # 14-02：廊下で鍵束を上げる → 光る → 6 つの扉が手前から順に光る
    tb = s("14-02")
    sh_key(sh, tb - 0.4, (D_["admin"] - 0.15, Y_ROOM + 1.0), 180.0, "CONSTANT"); sh_key(sh, tb - 0.3, (D_["admin"] + 0.3, 0.2), 90.0, "CONSTANT")
    key(sh.arm, "rotation_euler", tb + 0.1, (R(5), 0, 0)); key(sh.arm, "rotation_euler", tb + 0.6, (R(40), 0, 0))
    bm = bpy.data.materials.get("in_bundle")
    if bm is None:
        for m_ in bpy.data.materials:
            if m_.name.startswith("in_bundle"): bm = m_; break
    if bm is not None:
        emit_key(bm, -100.0, 0.0, "CONSTANT"); emit_key(bm, tb + 0.6, 0.0); emit_key(bm, tb + 0.9, 4.0); emit_key(bm, e("14-03") + 0.3, 4.0); emit_key(bm, e("14-03") + 0.8, 0.6)
    ev(tb + 0.8, "ding", 0.25, "bundle2")
    for k, (nm, x) in enumerate(IDOORS):
        bpy.ops.object.light_add(type='POINT', location=(x, YB - 0.5, 1.3)); fl = bpy.context.object; fl.data.color = srgb("#FF5A4A")[:3]; fl.data.shadow_soft_size = 0.4
        t0_ = tb + 1.1 + 0.25 * k
        for tt, en in ((-100.0, 0.0), (t0_, 0.0), (t0_ + 0.15, 60.0), (t0_ + 0.6, 0.0)): light_key(fl, tt, en)
    # 14-03：鍵束の寄り（影の手の中で光る）
    # 14-04：2 つの扉に赤い印（「こっそり」で 1 つ目、そのあと 2 つ目）。まるロボがびくっ
    tc = s("14-04")
    sh_key(sh, tc, (D_["admin"] + 0.3, 0.2), 90.0); sh_key(sh, tc + 0.9, (D_["tags"], 0.85), 90.0)
    t_m1 = w("14-04", "こっそり") + 0.1; t_m2 = w("14-04", "印") + 0.5
    key(sh.root, "rotation_euler", tc + 1.0, (0, 0, R(0 + 180))); key(sh.arm, "rotation_euler", t_m1 - 0.3, (R(5), 0, 0)); key(sh.arm, "rotation_euler", t_m1, (R(70), 0, 0))
    key(sh.arm, "rotation_euler", t_m1 + 0.4, (R(5), 0, 0))
    for nm, tm in (("tags", t_m1), ("backup", t_m2)):
        mk = IN["mark_" + nm]; key(mk, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(mk, "scale", tm, (0.001,) * 3); key(mk, "scale", tm + 0.25, (1, 1, 1))
        ev(tm, "squeak2", 0.3, "door_" + nm); track("mark_" + nm, mk, 0.0)
    sh_key(sh, t_m1 + 0.5, (D_["tags"], 0.85), 180.0); sh_key(sh, t_m2 - 0.4, (D_["backup"], 0.85), 180.0)
    key(sh.arm, "rotation_euler", t_m2 - 0.3, (R(5), 0, 0)); key(sh.arm, "rotation_euler", t_m2, (R(70), 0, 0)); key(sh.arm, "rotation_euler", t_m2 + 0.4, (R(5), 0, 0))
    # 14-05〜14-07：扉が開いて中を見せる（影は扉の前に立ったまま）→ 閉める
    door_key("tags", s("14-05") + 0.1, 0); door_key("tags", s("14-05") + 0.9, 85); door_key("tags", e("14-06") + 0.3, 85); door_key("tags", e("14-06") + 1.0, 0)
    ev(s("14-05") + 0.1, "squeak", 0.25, "door_tags")
    sh_key(sh, s("14-05"), (D_["backup"], 0.85), 180.0); sh_key(sh, s("14-05") + 0.05, (D_["tags"] + 1.3, 0.3), 160.0, "CONSTANT")       # 扉の回る所の外
    sh_key(sh, s("14-07") - 0.3, (D_["tags"] + 1.3, 0.3), 160.0); sh_key(sh, s("14-07") - 0.25, (D_["backup"] + 1.3, 0.3), 160.0, "CONSTANT")
    door_key("backup", s("14-07") + 0.1, 0); door_key("backup", s("14-07") + 0.9, 85); door_key("backup", s("14-08") + 0.2, 85); door_key("backup", s("14-08") + 0.9, 0)
    ev(s("14-07") + 0.1, "squeak", 0.25, "door_backup")
    # 14-09：予備の倉庫の扉の前に立つ影（後ろ姿）
    sh_key(sh, s("14-09") - 0.3, (D_["backup"] + 1.3, 0.3), 160.0, "CONSTANT"); sh_key(sh, s("14-09") - 0.25, (D_["backup"], 0.75), 180.0, "CONSTANT")
    # 15-01：名札の倉庫の扉を鍵束で開ける
    tf = s("15-01")
    sh_key(sh, tf - 0.4, (D_["backup"], 0.75), 180.0, "CONSTANT"); sh_key(sh, tf - 0.35, (D_["tags"] + 0.25, 0.75), 180.0, "CONSTANT")
    key(sh.arm, "rotation_euler", tf + 0.3, (R(5), 0, 0)); key(sh.arm, "rotation_euler", tf + 1.0, (R(60), 0, 0)); ev(tf + 1.1, "click", 0.4, "door_tags")
    key(sh.arm, "rotation_euler", tf + 1.6, (R(60), 0, 0)); key(sh.arm, "rotation_euler", tf + 2.0, (R(-10), 0, 0))
    sh_key(sh, tf + 1.6, (D_["tags"] + 0.25, 0.75), 180.0); sh_key(sh, tf + 2.1, (D_["tags"] + 1.35, 0.35), 180.0)
    door_key("tags", tf + 2.2, 0); door_key("tags", tf + 3.2, 88); ev(tf + 2.2, "squeak", 0.25, "door_tags")
    sh_key(sh, tf + 3.4, (D_["tags"] + 1.35, 0.35), 180.0); sh_key(sh, tf + 4.0, (D_["tags"] + 0.15, 0.6), 180.0); sh_key(sh, e("15-01") + 0.6, (D_["tags"] + 0.2, Y_ROOM + 1.2), 180.0)     # 出入口を通って中へ（入りこみの点検：かべを斜めに通っていた）
    # 15-02：名札を箱につめる（3 枚が棚から箱へ）。箱は部屋の床
    bx = tag_box((D_["tags"] - 0.5, Y_ROOM + 1.7, 0.0)); track("tbox", bx, 0.15)
    sh_key(sh, s("15-02") - 0.2, (D_["tags"] + 0.2, Y_ROOM + 1.2), 0.0 + 180.0)
    tags = IN["tags_tags"]
    pick = [tags[7 + 3], tags[7 + 1], tags[7 + 5]]      # 2 段目の 3 枚（1 枚目がまるロボの青緑）
    for k, tg in enumerate(pick):
        t0_ = s("15-02") + 0.2 + k * 0.8
        p0 = tuple(tg.location); r0 = tuple(tg.rotation_euler)
        p1 = (bx.location[0] - 0.1 + 0.1 * k, bx.location[1] - 0.02 + 0.03 * k, 0.05 + 0.012 * k)
        key(tg, "location", -100.0, p0, "CONSTANT"); key(tg, "location", t0_, p0)
        key(tg, "location", t0_ + 0.35, (p0[0], p0[1] - 0.35, p0[2] + 0.1)); key(tg, "location", t0_ + 0.75, p1)
        key(tg, "rotation_euler", t0_, r0); key(tg, "rotation_euler", t0_ + 0.75, (0, 0, R(8 * k - 8)))
        key(sh.arm, "rotation_euler", t0_, (R(30), 0, 0)); key(sh.arm, "rotation_euler", t0_ + 0.4, (R(-10), 0, 0))
        ev(t0_ + 0.75, "paper", 0.3, "tbox")
        if k == 0: track("mytag", tg, 0.0)
    # 15-05：箱をかかえて廊下を裏口のほうへ（箱は影の胸の前。持ち替えは箱の場面の外で）
    bx2 = tag_box((0, 0, 0)); bx2.parent = sh.root; bx2.location = (0, -0.55, 0.78); bx2.scale = (0.001,) * 3
    key(bx2, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(bx2, "scale", s("15-05") - 0.3, (0.001,) * 3, "CONSTANT"); key(bx2, "scale", s("15-05") - 0.25, (1.0 / SHS2,) * 3, "CONSTANT")
    key(bx, "scale", -100.0, (1, 1, 1), "CONSTANT"); key(bx, "scale", s("15-05") - 0.3, (1, 1, 1), "CONSTANT"); key(bx, "scale", s("15-05") - 0.25, (0.001,) * 3, "CONSTANT")
    for tg in pick:
        key(tg, "scale", -100.0, (1, 1, 1), "CONSTANT"); key(tg, "scale", s("15-05") - 0.3, (1, 1, 1), "CONSTANT"); key(tg, "scale", s("15-05") - 0.25, (0.001,) * 3, "CONSTANT")
    track("box2", bx2, 0.2)
    # 箱を持ちかえる所は、カメラの後ろ（部屋の奥）。影は部屋から歩いて出てくる（置き直さない。入りこみの点検：入口のまるロボとぶつかった）
    key(sh.arm, "rotation_euler", s("15-05") - 0.25, (R(-20), 0, 0), "CONSTANT")
    sh_key(sh, s("15-05") + 0.6, (D_["tags"] + 0.2, Y_ROOM + 1.2), 0.0); sh_key(sh, s("15-05") + 1.0, (D_["tags"] - 0.05, Y_ROOM + 0.7), 0.0); sh_key(sh, s("15-05") + 2.0, (D_["tags"] - 0.05, 0.45), 0.0)     # 出入口のまん中を通る
    sh_key(sh, s("15-05") + 2.4, (D_["tags"] - 0.1, 0.4), -90.0); sh_key(sh, e("15-05") + 0.4, (2.0, 0.3), -90.0)
    # 15-06〜16-02 はお城の外（b_out2）。16-03：もう一度、廊下を奥へ（背中に「？」）
    sh_key(sh, s("16-03") - 0.4, (2.0, 0.3), 90.0, "CONSTANT"); sh_key(sh, s("16-03") - 0.35, (0.6, 0.25), 90.0, "CONSTANT")
    key(bx2, "scale", s("16-03") - 0.4, (0.001,) * 3, "CONSTANT")
    sh_key(sh, s("16-03"), (0.6, 0.25), 90.0); sh_key(sh, e("16-03") + 0.5, (4.5, 0.4), 90.0)
    key(sh.arm, "rotation_euler", s("16-03"), (R(-20), 0, 0))
    # 16-04〜16-06：赤い錠（声の「ガチャン」の時刻）。影は見せない所で動く
    pop_lock("tags", wv("16-04", "ガチャン") + 0.08)
    g1 = wv("16-05", "ガチャン") + 0.08; g2 = wv("16-05", "ガチャン", 1) + 0.08
    pop_lock("admin", g1); pop_lock("work", g2)       # 2 つが 1 枚の絵に入るとなりの扉（v1 の決まり：動きを目で追える。5 m 先へ 0.6 秒で振ると追えない）
    pop_lock("hall2", e("16-05") + 0.3); pop_lock("hall5", e("16-05") + 0.5)
    pop_lock("backup", wv("16-06", "ガチャン") + 0.08, 1.6)
    sh_key(sh, e("16-03") + 0.6, (4.5, 0.4), 90.0, "CONSTANT"); sh_key(sh, e("16-03") + 0.65, (40.0, 30.0), 90.0, "CONSTANT")      # 錠をかける影は見せない（錠だけ）
    # 16-07：まるロボが走り回る → 予備の倉庫の扉の前でへたりこむ（まるロボは下で）
    # 16-11〜16-12：朝。働く人が扉を引く → 開かない（ガタッ）。この扉も、あの扉も
    wk = walker((1.0, -0.2, 0.0), 90.0, shirt="#5A7BA8", pants="#2D3640"); track("worker", wk.head, 0.0)
    key(wk.root, "location", -100.0, (40.0, 40.0, 0.0), "CONSTANT"); key(wk.root, "location", s("16-11") - 0.5, (40.0, 40.0, 0.0), "CONSTANT")
    tw = s("16-11") - 0.45
    key(wk.root, "location", tw, (D_["hall2"] - 0.9, 0.55, 0.02), "CONSTANT"); key(wk.root, "rotation_euler", tw, (0, 0, R(180)), "CONSTANT")
    pulls = [(D_["hall2"], w("16-12", "扉が開きません") - 0.2), (D_["tags"], w("16-12", "この扉") + 0.1), (D_["backup"], w("16-12", "どの扉") + 0.1)]
    xprev = D_["hall2"] - 0.9
    for k, (dx_, tp) in enumerate(pulls):
        xr = dx_ + ID_W / 2 - 0.15 - 0.25      # 取っ手の少し左に立つ
        if k > 0: wk_walk(wk, tp - 1.3, tp - 0.3, (xprev, 0.55), (xr, 0.55), 90.0)
        key(wk.root, "rotation_euler", tp - 0.25, (0, 0, R(90 if k else 180))); key(wk.root, "rotation_euler", tp - 0.05, (0, 0, R(180)))
        key(wk.arms[1], "rotation_euler", tp - 0.2, (R(0), 0, 0)); key(wk.arms[1], "rotation_euler", tp, (R(-70), 0, 0))
        key(wk.arms[1], "rotation_euler", tp + 0.15, (R(-60), 0, 0)); key(wk.arms[1], "rotation_euler", tp + 0.35, (R(-70), 0, 0)); key(wk.arms[1], "rotation_euler", tp + 0.7, (R(0), 0, 0))
        nm = [n for n, x in IDOORS if x == dx_][0]
        for tt, dg in ((tp - 0.01, 0), (tp + 0.08, -2.5), (tp + 0.18, 0), (tp + 0.28, -2.0), (tp + 0.4, 0)): door_key(nm, tt, dg)
        ev(tp + 0.08, "rattle", 0.4, "door_" + nm)
        xprev = xr
    key(wk.root, "location", e("16-12") + 0.55, tuple(wk.root.location), "CONSTANT"); key(wk.root, "location", e("16-12") + 0.6, (40.0, 40.0, 0.0), "CONSTANT")       # 17 の予備の倉庫の錠の寄りに、働く人が残っていた（試しの絵）
    # 16-13：働く人の部屋。画面が赤く固まる（16-14 の机の上に、注文の紙と荷物の箱が積まれていく）
    for k, sm in enumerate(scr):
        bb = sm.node_tree.nodes["Principled BSDF"]
        for tt, col, st in ((-100.0, "#CFE6FF", 1.6), (w("16-13", "パソコン") - 0.1 + 0.3 * k, "#CFE6FF", 1.6), (w("16-13", "パソコン") + 0.2 + 0.3 * k, "#E0322C", 2.2)):
            bb.inputs["Emission Color"].default_value = srgb(col); bb.inputs["Emission Color"].keyframe_insert("default_value", frame=f(tt))
            bb.inputs["Emission Strength"].default_value = st; bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f(tt))
    track("screen0", bpy.data.objects[[o.name for o in bpy.data.objects if o.active_material is scr[0]][0]], 0.0)
    xw = D_["work"]
    for k in range(5):
        pp = cube(mat("paper", "#FFFFFF", rough=0.6), (xw - 0.85, Y_ROOM + 2.1, 0.775 + 0.01 * k), (0.21, 0.3, 0.008), rot=(0, 0, R(6 * k - 12)))
        hide_key(pp, -100.0, True); hide_key(pp, w("16-14", "注文") - 0.2 + 0.25 * k, False)
    track("orders", pp, 0.05)
    for k in range(3):
        b_ = cube(mat("parcel", "#C9A06A", rough=0.8), (xw + 0.75, Y_ROOM + 2.05, 0.83 + 0.16 * k), (0.28, 0.2, 0.15), rot=(0, 0, R(8 * k - 8)))
        hide_key(b_, -100.0, True); hide_key(b_, w("16-14", "荷物") - 0.2 + 0.3 * k, False)
    track("parcels", b_, 0.1)
    # 17：持ち主の部屋。手紙が 2 通、ひらひら落ちる
    ox, oy = OWN
    lts = []
    for k in range(2):
        lt = letter((ox - 0.25 + 0.5 * k, oy + 1.45, 2.6)); lts.append(lt); track("letter%d" % k, lt, 0.0)
        t0_ = s("17-01") + 1.0 + 0.6 * k
        key(lt, "location", -100.0, (ox - 0.25 + 0.5 * k, oy + 1.45, 2.6), "CONSTANT"); key(lt, "location", t0_, (ox - 0.25 + 0.5 * k, oy + 1.45, 2.6))
        for j in range(1, 5):
            key(lt, "location", t0_ + 0.45 * j, (ox - 0.25 + 0.5 * k + (0.12 if j % 2 else -0.12), oy + 1.45, 2.6 - (2.6 - 0.82) * j / 4))
            key(lt, "rotation_euler", t0_ + 0.45 * j, (R(18 if j % 2 else -18), 0, R(10 * k)))
        key(lt, "rotation_euler", t0_ + 2.0, (0, 0, R(10 * k - 5)))
        ev(t0_ + 1.85, "paper", 0.3, "letter%d" % k)
    # ---- まるロボ（柱のかげで見張る → 名札に気づく → 走り回ってへたりこむ → 持ち主のうしろからのぞく）
    M = MaruR((30.0, 30.0, 0.0), face=90.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    PX = IN["pillars"]
    M.at(s("13-06") - 0.5, loc=(PX[3] - 0.75, -0.8, 0.0), face=125.0, interp="CONSTANT")     # 柱（x=9.1）の左のかげ。奥の影のほうを向く
    M.peer(s("13-06") + 0.3, 1.2)
    M.blink(w("13-06", "ずっと") + 0.1); M.blink(w("13-06", "ずっと") + 0.5)
    M.confused(w("13-07", "なぜ") + 0.1)
    M.at(tc - 0.3, loc=(PX[3] - 0.75, -0.8, 0.0), face=125.0, interp="CONSTANT")
    M.surprise(t_m1 + 0.25)
    M.at(s("15-04") - 1.2, loc=(D_["tags"] + 0.95, 0.55, 0.0), face=205.0, interp="CONSTANT")      # 名札の倉庫の入口の右から、ななめに中をのぞく（出てくる影の通り道の外。まるロボは歩くのが遅いので、下がらせない）
    M.surprise(wv("15-04", "まるロボ") - 0.1)
    M.at(e("15-05") + 0.6, loc=(40.0, -30.0, 0.0), interp="CONSTANT")
    tr = s("16-07")
    M.at(tr - 0.3, loc=(D_["tags"] - 0.5, 0.05, 0.0), face=90.0, interp="CONSTANT")      # 錠のかかった扉の前を急ぐが、まるロボは遅い（1.4 m を 3.8 秒。向きを変えずに）。v2 の計画で 7 秒遅れた
    M.walk(tr + 0.1, e("16-07") - 0.3, (D_["tags"] + 0.9, 0.1, 0.0))
    M.sigh(e("16-07") + 0.1)
    M.at(e("16-07") + 0.9, loc=(40.0, -30.0, 0.0), interp="CONSTANT")
    M.at(s("17-07") - 0.6, loc=(ox + 0.8, oy + 0.5, 0.0), face=170.0, interp="CONSTANT")       # 持ち主の右うしろから、手紙をのぞきこむ
    M.peer(s("17-07") + 0.3, 1.2)
    M.at(s("17-13") - 0.5, loc=(ox + 1.0, oy + 0.45, 0.0), face=150.0, interp="CONSTANT")
    M.nod(w("17-13", "払わない") + 0.3)
    # 13-04：かべのカレンダーが 1 枚ずつめくれる（数字なし）。窓の夜と昼も替わる（day_night）
    pages = calendar(17.0, n=4); track("calendar", pages[0], 0.0)
    for k, tt in enumerate((w("13-04", "1枚") - 0.1, w("13-04", "また1枚") - 0.1, e("13-04") - 0.9)):
        key(pages[k], "rotation_euler", -100.0, (0, 0, 0), "CONSTANT"); key(pages[k], "rotation_euler", tt, (0, 0, 0)); key(pages[k], "rotation_euler", tt + 0.5, (R(-175), 0, 0))
        ev(tt + 0.1, "paper", 0.3, "calendar")
    _bundle_handoff_fix()
    return sh, M


def _bundle_handoff_fix():
    """鍵束 1（引き出しの中から持ち上げる）を、手の鍵束 2 の場所まで動かしてから替える（一瞬で移さない）"""
    if "_bundle_handoff" not in IN: return
    kb, kb2, t_a, t_b = IN["_bundle_handoff"]
    sc = bpy.context.scene; sc.frame_set(f(t_b)); p = kb2.matrix_world.translation.copy()
    key(kb, "location", t_b - 0.05, (p.x, p.y, p.z))
    key(kb, "scale", -100.0, (1.1,) * 3, "CONSTANT"); key(kb, "scale", t_b + 0.04, (1.1,) * 3, "CONSTANT"); key(kb, "scale", t_b + 0.05, (0.001,) * 3, "CONSTANT")
    sc.frame_set(0)


# ======================================================================== O：夜のお城の外（15-06〜16-02・16-08・16-09）
def b_out2(cl):
    C_, gk = _castle_common(True)
    SH = SHS2
    sh = shadow((40.0, 40.0, 0.0), face=180.0, s=SH); track("shadow", sh.root, 1.5 * SH)
    bx = tag_box((0, 0, 0)); bx.parent = sh.root; bx.location = (0, -0.55, 0.78); bx.scale = (1 / SH,) * 3; track("box", bx, 0.2)
    key(sh.arm, "rotation_euler", -100.0, (R(-20), 0, 0), "CONSTANT")
    hg = C_["door"]
    key(hg, "rotation_euler", -100.0, (0, 0, R(-94)), "CONSTANT")      # 裏口は開いたまま（影が出入りする）
    # 15-06：上から。横の裏口から、箱を持った影が出ていく
    t6 = s("15-06")
    sh_key(sh, t6 - 0.4, (X_SIDE - 0.6, DOOR_Y), -90.0, "CONSTANT"); sh_key(sh, t6 + 0.4, (X_SIDE - 0.6, DOOR_Y), -90.0)
    sh_key(sh, t6 + 2.2, (X_SIDE + 1.6, DOOR_Y - 0.3), -90.0 - 60.0); sh_key(sh, e("15-06") + 0.4, (X_SIDE + 1.9, DOOR_Y - 2.0), 180.0)     # 角の塔（半径 1.4）の外を通る
    # 15-07：暗い道を遠ざかる（−y へ）
    sh_key(sh, s("15-07"), (X_SIDE + 1.9, DOOR_Y - 2.0), 180.0); sh_key(sh, e("15-07") - 0.2, (X_SIDE + 1.9, DOOR_Y - 6.5), 180.0)
    # 16-01：立ち止まって、箱を道ばたに置く
    t1_ = s("16-01")
    key(sh.arm, "rotation_euler", t1_ + 0.6, (R(-20), 0, 0)); key(sh.arm, "rotation_euler", t1_ + 1.4, (R(-50), 0, 0))
    key(bx, "location", t1_ + 0.6, (0, -0.55, 0.78)); key(bx, "location", t1_ + 1.4, (0, -0.65, 0.05 / SH))
    bx_g = tag_box((X_SIDE + 1.9, DOOR_Y - 7.15, 0.0)); key(bx_g, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(bx_g, "scale", t1_ + 1.45, (0.001,) * 3, "CONSTANT"); key(bx_g, "scale", t1_ + 1.5, (1, 1, 1), "CONSTANT")
    key(bx, "scale", t1_ + 1.45, (1 / SH,) * 3, "CONSTANT"); key(bx, "scale", t1_ + 1.5, (0.001,) * 3, "CONSTANT")
    ev(t1_ + 1.45, "thud", 0.25, "box")
    # 16-02：くるりと向きを変えて、裏口から中へ戻る
    t2_ = w("16-02", "逆戻り") - 1.6
    key(sh.root, "rotation_euler", t2_, (0, 0, R(180))); key(sh.root, "rotation_euler", t2_ + 0.6, (0, 0, R(0)))
    sh_key(sh, t2_ + 0.6, (X_SIDE + 1.9, DOOR_Y - 6.5)); sh_key(sh, t2_ + 2.8, (X_SIDE + 1.9, DOOR_Y - 1.6)); sh_key(sh, t2_ + 3.4, (X_SIDE + 1.1, DOOR_Y - 0.1))
    sh_key(sh, t2_ + 4.2, (X_SIDE - 0.9, DOOR_Y), -90.0); ev(t2_ + 0.3, "swish", 0.25, "shadow")
    key(sh.root, "scale", -100.0, (SH,) * 3, "CONSTANT"); key(sh.root, "scale", t2_ + 4.2, (SH,) * 3, "CONSTANT"); key(sh.root, "scale", t2_ + 4.3, (0.001,) * 3, "CONSTANT")
    # まるロボ：15-07 で裏口から走って出てきて、道の手前で止まる → 16-02 で台のかげへよける
    LG = (X_SIDE + 1.0, DOOR_Y + 2.2)
    cube(_stone(), (LG[0] + 0.25, LG[1], 0.4), (0.5, 1.0, 0.8))
    M = MaruR((30.0, 30.0, 0.0), face=180.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    M.at(s("15-07") - 0.3, loc=(X_SIDE - 0.9, DOOR_Y, 0.0), face=-90.0 + 180.0 - 180.0 + 90.0, interp="CONSTANT")
    M.walk(s("15-07") + 0.3, e("15-07") - 0.3, (X_SIDE + 0.9, DOOR_Y + 0.1, 0.0))      # 扉からまっすぐ出る（開いた扉の板に当たらない）
    M.walk(s("16-01") + 0.0, e("16-01") + 0.4, (LG[0] - 0.25, LG[1] - 1.05, 0.0))     # 影が戻ってくる前に、台のかげへ（入りこみの点検：戻る影とぶつかった）
    M.surprise(w("16-02", "逆戻り") - 1.4)
    # 16-08：窓の明かりが 1 つずつ消える（正面のかべに窓を 6 つ足す。1 つずつ別の材質）
    for k in range(6):
        wm_ = bpy.data.materials.new("out_win%d" % k); wm_.use_nodes = True
        b_ = wm_.node_tree.nodes["Principled BSDF"]; b_.inputs["Base Color"].default_value = (0.03, 0.03, 0.04, 1)
        b_.inputs["Emission Color"].default_value = srgb("#FFC870")
        x_ = (-5.6, -4.2, -2.8, 2.8, 4.2, 5.6)[k]
        cube(wm_, (x_, -0.03, 3.8), (0.55, 0.06, 0.8))
        tk = w("16-08", "閉ざされて") - 2.6 + 0.55 * k
        for tt, st in ((-100.0, 2.4), (tk, 2.4), (tk + 0.2, 0.0)):
            b_.inputs["Emission Strength"].default_value = st; b_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f(tt))
    track("castle_c", C_["gate"][0], 3.0)
    return sh, M


# ======================================================================== M：朝のお城の外（16-10・16-15）と、想像（17-08）
def b_morning(cl):
    C_, gk = _castle_common(False)
    for i, hg in enumerate(C_["gate"]):
        sx = -1 if i == 0 else 1
        key(hg, "rotation_euler", -100.0, (0, 0, 0), "CONSTANT"); key(hg, "rotation_euler", s("16-10") + 0.2, (0, 0, 0))
        key(hg, "rotation_euler", s("16-10") + 1.4, (0, 0, R(-70 * sx)))
    cols = ["#5A7BA8", "#A86A5A", "#6A9A6A"]
    for k in range(3):
        wk = walker((-1.2 + 1.0 * k, -9.0 - 1.4 * k, 0.0), 0.0 + 180.0, shirt=cols[k])
        t0_ = s("16-10") + 0.6 + 0.5 * k
        key(wk.root, "location", -100.0, (-1.2 + 1.0 * k, -9.0 - 1.4 * k, 0.0), "CONSTANT")
        wk_walk(wk, t0_, t0_ + 4.0, (-1.2 + 1.0 * k, -9.0 - 1.4 * k), (-0.6 + 0.6 * k, -2.2 - 0.8 * k), 180.0)
    # 16-15：旗が下がる（会社ごと止まる）
    for o in bpy.data.objects:
        if o.active_material is not None and o.active_material.name.startswith("flag"):
            key(o, "rotation_euler", -100.0, (0, 0, 0), "CONSTANT"); key(o, "rotation_euler", s("16-15") + 0.4, (0, 0, 0)); key(o, "rotation_euler", s("16-15") + 1.6, (0, R(70), 0))


def b_imag2(cl):
    """17-08 の想像：お城の前の町に、名札がひらひら降る（組み立てで青っぽくする）。まるロボが体を小さくする"""
    C_, gk = _castle_common(False)
    random.seed(1708)
    t0 = s("17-08")
    for k in range(26):
        x = random.uniform(-6, 6); y = random.uniform(-9, -2); z0 = random.uniform(4.0, 8.0)
        tg = nameplate((x, y, z0), rot=(R(random.uniform(-40, 40)), 0, R(random.uniform(0, 180))), tex=random.choice(["tag_cust", "tag_cust", "tag_maru"]), w=0.45)
        td = t0 + random.uniform(0.0, 1.5)
        key(tg, "location", -100.0, (x, y, z0), "CONSTANT"); key(tg, "location", td, (x, y, z0))
        key(tg, "location", td + 4.5, (x + random.uniform(-1, 1), y, max(0.05, z0 - 5.5)))
        key(tg, "rotation_euler", td + 4.5, (R(random.uniform(-80, 80)), 0, R(random.uniform(0, 360))))
    M = MaruR((0.2, -3.6, 0.0), face=180.0 - 180.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    M.surprise(t0 + 1.2)


# ======================================================================== カット（2章）
I0 = 0.0
CUTS2 = [
    ("D13", b_in, s("13-01"), C((5.2, -0.4, 1.5), (0.4, 0.25, 0.9), 30), "D"),
    ("D13b", b_in, s("13-02"), C((0.2, -1.0, 1.8), (6.5, 0.6, 0.9), 26), "D"),     # 試しの絵：横からだと影が画面いっぱいだった
    ("D13c", b_in, s("13-03"), C((5.6, -1.05, 1.6), (9.2, 1.2, 1.0), 26), "D"),
    ("D13d", b_in, s("13-04"), C((15.3, -0.95, 1.7), (17.3, 0.9, 1.7), 30), "D"),
    ("D13e", b_in, s("13-05"), C((D_["work"] - 1.1, Y_ROOM + 0.3, 2.3), (D_["work"] + 0.2, Y_ROOM + 2.3, 0.75), 22), "D"),
    ("D13f", b_in, s("13-06"), C((10.7, 1.0, 1.3), (8.55, -0.95, 0.6), 24), "D"),
    ("D13g", b_in, s("13-07"), C((10.1, 0.4, 0.95), (8.55, -0.95, 0.62), 28), "D"),
    ("D13h", b_in, s("13-08"), C((1.0, -1.0, 2.2), (10.0, 0.8, 0.8), 24), "D"),
    ("D14", b_in, s("14-01"), C((D_["admin"] + 1.0, Y_ROOM + 2.6, 1.6), (D_["admin"] - 0.35, Y_ROOM + 1.4, 0.75), 26), "D"),     # 机の横から（試しの絵：影の背中で机が隠れた）
    ("D14b", b_in, s("14-02"), C((0.6, -1.0, 1.8), (12.0, 0.9, 1.0), 24), "D"),
    ("D14c", b_in, s("14-03"), C((D_["admin"] + 1.3, -0.3, 1.25), (D_["admin"] + 0.58, 0.43, 1.05), 45), "D"),     # 影の手の鍵束に寄る（試しの絵：手が画面の外だった）
    ("D14d", b_in, s("14-04"), C((7.0, -1.0, 1.6), (12.2, 1.4, 1.05), 24), "D"),
    ("D14e", b_in, s("14-05"), C((D_["tags"], -0.6, 1.45), (D_["tags"], Y_ROOM + 2.6, 0.95), 30, (D_["tags"], YB - 0.2, 1.3)), "D"),
    ("D14f", b_in, s("14-06"), C((D_["tags"], Y_ROOM + 1.1, 1.25), (D_["tags"], Y_ROOM + 2.9, 0.95), 30), "D"),
    ("D14g", b_in, s("14-07"), C((D_["backup"], -0.6, 1.45), (D_["backup"], Y_ROOM + 2.6, 0.95), 30, (D_["backup"], YB - 0.2, 1.3)), "D"),
    ("D14h", b_in, s("14-08"), C((D_["backup"], Y_ROOM + 1.1, 1.25), (D_["backup"], Y_ROOM + 2.9, 0.95), 30), "D"),
    ("D14i", b_in, s("14-09"), C((D_["backup"] - 0.2, -1.0, 1.55), (D_["backup"], YB, 1.35), 30), "D"),
    ("A14", b_house, s("14-10"), C((1.97, 0.4, 0.42), (1.95, 0.65, 0.0), 30), "A"),
    ("D14j", b_in, s("14-12"), C((D_["backup"], Y_ROOM + 1.1, 1.25), (D_["backup"], Y_ROOM + 2.9, 0.95), 30), "D"),
    ("D14k", b_in, s("14-14"), C((D_["backup"] + 0.1, 0.35, 1.6), (D_["backup"], YB, 1.55), 34), "D"),
    ("D15", b_in, s("15-01"), C((D_["tags"] + 2.3, -0.9, 1.55), (D_["tags"] + 0.3, 1.2, 1.0), 28), "D"),
    ("D15b", b_in, s("15-02"), C((D_["tags"] - 1.05, Y_ROOM + 0.35, 1.7), (D_["tags"] - 0.2, Y_ROOM + 2.0, 0.5), 26), "D"),
    ("D15c", b_in, s("15-03"), C((D_["tags"] - 0.5, Y_ROOM + 1.62, 0.95), (D_["tags"] - 0.5, Y_ROOM + 1.7, 0.0), 32), "D"),
    ("D15d", b_in, s("15-04"), C((D_["tags"] - 0.25, Y_ROOM + 0.85, 0.95), (D_["tags"] - 0.2, 0.35, 0.6), 30), "D"),     # 部屋の中から入口のまるロボ（顔）
    ("D15e", b_in, s("15-05"), C((0.6, -0.9, 1.5), (7.5, 0.4, 0.8), 26), "D"),
    ("O15", b_out2, s("15-06"), C((DX + 13.0, -15.0, 21.0), (2.0, 1.5, 0.0), 30), "O"),     # 正面の門番さんと横の裏口が 1 枚に
    ("O15b", b_out2, s("15-07"), C((DX + 3.2, DOOR_Y + 1.6, 0.75), (DX + 0.6, DOOR_Y - 3.5, 0.7), 24), "O"),
    ("O16", b_out2, s("16-01"), C((DX + 4.0, DOOR_Y - 12.0, 1.6), (DX + 1.2, DOOR_Y - 6.8, 0.7), 30), "O"),
    ("O16b", b_out2, s("16-02"), C((DX + 4.2, DOOR_Y - 3.6, 1.7), (DX + 0.6, DOOR_Y - 0.6, 0.8), 26), "O"),
    ("D16", b_in, s("16-03"), C((-0.4, 0.3, 1.5), (6.0, 0.4, 1.0), 30), "D"),
    ("D16b", b_in, s("16-04"), C((D_["tags"] + 0.45, 0.25, 1.25), (D_["tags"] + ID_W / 2 - 0.28, YB, 0.97), 32), "D"),
    ("D16c", b_in, s("16-05"), C((3.9, -0.7, 1.45), (3.9, YB, 1.05), 22), "D"),
    ("D16d", b_in, s("16-06"), C((D_["backup"] + 0.55, 0.15, 0.55), (D_["backup"] + 0.2, YB, 1.05), 28), "D"),
    ("D16e", b_in, s("16-07"), C((9.4, -1.05, 1.7), (11.2, 1.0, 0.7), 24), "D"),
    ("O16c", b_out2, s("16-08"), C((-4.5, -15.0, 3.2), (0.4, 0.0, 3.0), 30), "O"),
    ("M16", b_morning, s("16-10"), C((3.5, -14.0, 2.4), (0.0, -2.0, 1.4), 30), "M"),
    ("D16f", b_in, s("16-11"), C((D_["hall2"] - 1.3, -0.9, 1.6), (D_["tags"] - 0.3, 1.3, 1.1), 24), "D"),
    ("D16g", b_in, s("16-13"), C((D_["work"] - 0.2, Y_ROOM + 0.4, 1.7), (D_["work"], Y_ROOM + 2.4, 0.95), 28), "D"),
    ("D16h", b_in, s("16-14"), C((D_["work"] - 0.1, Y_ROOM + 1.25, 1.35), (D_["work"], Y_ROOM + 2.2, 0.85), 32), "D"),
    ("M16b", b_morning, s("16-15"), C((-4.5, -15.0, 3.2), (0.4, 0.0, 3.2), 30), "M"),
    ("D17", b_in, s("17-01"), C((OWN[0] + 1.3, OWN[1] - 0.5, 1.8), (OWN[0] - 0.1, OWN[1] + 1.5, 0.85), 30), "D"),
    ("D17b", b_in, s("17-02"), C((OWN[0] - 0.25, OWN[1] + 1.1, 1.35), (OWN[0] - 0.25, OWN[1] + 1.45, 0.82), 36), "D"),
    ("D17c", b_in, s("17-03"), C((OWN[0] + 0.4, OWN[1] - 1.4, 1.6), (OWN[0], OWN[1] + 1.5, 1.0), 30), "D"),
    ("D17d", b_in, s("17-05"), C((D_["backup"] + 0.55, 0.15, 0.55), (D_["backup"] + 0.2, YB, 1.05), 28), "D"),
    ("D17e", b_in, s("17-07"), C((OWN[0] + 1.4, OWN[1] - 0.3, 1.5), (OWN[0] + 0.3, OWN[1] + 1.3, 0.8), 30), "D"),
    ("I17", b_imag2, s("17-08"), C((2.0, -11.0, 2.0), (0.0, -3.0, 2.0), 28), "I2"),
    ("D17f", b_in, s("17-09"), C((OWN[0] - 0.25, OWN[1] + 1.1, 1.35), (OWN[0] - 0.25, OWN[1] + 1.45, 0.82), 36), "D"),
    ("D17g", b_in, s("17-13"), C((OWN[0] + 2.2, OWN[1] - 1.8, 2.0), (OWN[0], OWN[1] + 1.0, 0.8), 28), "D"),
    ("P17", b_in, s("14-04") - 0.2, C((7.0, -1.0, 1.6), (12.2, 1.4, 1.05), 24), "D"),       # 17-06 の小窓（14-04 の印を付ける場面をもう一度）
]
PIP2 = {"P17": (s("14-04") - 0.2, e("14-04") + 0.4)}
