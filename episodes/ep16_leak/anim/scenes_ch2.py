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
SH_SHELF = (D_["tags"] + 0.2, Y_ROOM + 2.1)     # 15-02 で名札を取る影の立つ所（棚の前）
ARM_UP = -65.0      # 腕の角度は −で上がる（測った：+55 で手は 0.59 m、−25 で 0.91 m）
SH_LOCK = (D_["tags"] + ID_W / 2 + 0.1, 1.05)     # 16-04：錠をかける影の立つ所（取っ手の右）
LX0 = 0.15       # 17：1 通目の手紙の x（持ち主の x からのずれ）。2 通目は +0.5
TBOX_AT = (D_["tags"] - 0.42, Y_ROOM + 2.25, 0.0)      # 手を下ろした所（x 10.37・y 4.4）の左下。影の体（x 10.3〜）と棚（y 4.25〜 の下の板）の手前


def sh_key(sh, t, loc, face=None, interp="BEZIER"):
    key(sh.root, "location", t, (loc[0], loc[1], 0.0), interp)
    if face is not None: key(sh.root, "rotation_euler", t, (0, 0, R(face)), interp)


def door_key(name, t, deg, interp="BEZIER"):
    key(IN["door_" + name], "rotation_euler", t, (0, 0, R(deg)), interp)


def pop_lock(name, t, s=1.0, heard=True):
    """赤い錠が扉に「ガチャン」とかかる（t＝扉に当たる時刻）：少し上から下りて、大きさ 0 → s"""
    lk = IN["lock_" + name]; z0 = lk.location[2]
    # 上に出て、少し止まり、「ガチャン」へ 0.3 秒かけて下りてかかる（確認役：最初から付いていた。2 回目：場面が替わる重なりのうちに、もうかかって見えた
    #   → カットを 0.5 秒早く始め（CUTS2）、錠は t−0.75 に出て t−0.3 まで上で止まる）
    key(lk, "scale", -100.0, (0.001, 0.001, 0.001), "CONSTANT"); key(lk, "scale", t - 0.75, (0.001, 0.001, 0.001)); key(lk, "scale", t - 0.6, (s, s, s))
    key(lk, "location", t - 0.75, (lk.location[0], lk.location[1], z0 + 0.3)); key(lk, "location", t - 0.3, (lk.location[0], lk.location[1], z0 + 0.3)); key(lk, "location", t, (lk.location[0], lk.location[1], z0), "CONSTANT")
    if heard: ev(t, "clunk", 0.45, "")
    if heard:      # 錠がかかる扉を照らす（確認役：扉が真っ黒で、錠がかかるのが見えなかった）
        dx_ = dict(IDOORS)[name]
        bpy.ops.object.light_add(type='POINT', location=(dx_ + 0.2, YB - 0.7, 1.4)); L_ = bpy.context.object; L_.data.color = srgb("#FFD6B0")[:3]; L_.data.shadow_soft_size = 0.5
        for tt_, en_ in ((-100.0, 0.0), (t - 0.95, 0.0), (t - 0.75, 25.0)): light_key(L_, tt_, en_)      # 声の「ガチャン」と同じ時刻に必ず鳴らす（v1 の組み立て：場面の替わり目で前のカットの絵で判定され、2 つ鳴らなかった）


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
    # 「次の夜も」「また次の夜も」と言う間は夜の窓（確認役 2 回目：「夜」と言う時に昼の窓だった）。そのあと、カレンダーがめくれるたびに昼・夜
    m_ = wv("13-04", "また次の夜"); c_ = wv("13-04", "カレンダー")
    #   夜・昼はどれも 1 秒以上（2 回目の点検：0.3〜0.7 秒ごとに替わり、窓がちかちかした）。「次の夜も、また次の夜も」の間は夜のまま
    day_night([(-100.0, "night"), (c_ - 0.2, "day"), (wv("13-04", "1枚") + 0.2, "night"), (wv("13-04", "また1枚") + 0.55, "day"), (s("13-05") - 0.2, "day"),
               (s("13-06") + 0.3, "night"), (s("16-10") - 0.3, "day")])
    for nm, e_ in (("work", 60.0), ("admin", 30.0), ("tags", 0.0), ("backup", 0.0)):
        light_key(IN["room_" + nm], -100.0, 0.0)
    # 明かりは、つける・消す時刻の 0.4 秒前に「前の強さ」の印を打つ（v1：印が 2 つだけで、13-05・14-01 の間ずっと少しずつ暗くなっていた）
    for nm_, keys_ in (("work", [(s("13-05") - 0.3, 70.0), (s("13-06") + 0.3, 0.0), (s("16-10"), 70.0)]), ("admin", [(s("14-01") - 0.6, 70.0), (s("14-02") + 1.0, 0.0)])):
        prev_ = 0.0
        for tt_, en_ in keys_:
            light_key(IN["room_" + nm_], tt_ - 0.4, prev_); light_key(IN["room_" + nm_], tt_, en_); prev_ = en_
    light_key(IN["room_tags"], s("14-05"), 0.0); light_key(IN["room_tags"], s("14-05") + 0.6, 45.0); light_key(IN["room_tags"], e("15-04") + 0.5, 45.0); light_key(IN["room_tags"], e("15-04") + 1.0, 0.0)
    light_key(IN["room_backup"], s("14-07"), 0.0); light_key(IN["room_backup"], s("14-07") + 0.6, 80.0); light_key(IN["room_backup"], e("14-13") + 0.3, 80.0); light_key(IN["room_backup"], e("14-13") + 0.8, 0.0)      # 試しの絵：14-08・14-12 の部屋の中が真っ黒だった。予備は名札の倉庫より明るく（確認役 2 回目：2 つの倉庫が暗くて見分けにくい）
    # ---- 影（別の所へ置き直すのは、場面が替わる重なり（切り替わりの 0.1 秒前〜0.25 秒後）の中で。v1：0.3 秒前で、前の場面の最後に影が消えた）
    sh = shadow((-1.4, 0.25, 0.0), face=90.0, s=SHS2); track("shadow", sh.root, 1.5 * SHS2)
    IN["_hand"] = sh.hand
    key(sh.root, "scale", -100.0, (SHS2, SHS2, SHS2), "CONSTANT")
    # 13-01：裏口からの暗い通路から出てきて、立ち止まる（「でしょうか」）
    sh_key(sh, -100.0, (-1.4, 0.25), 90.0, "CONSTANT"); sh_key(sh, s("13-01") + 0.3, (-1.4, 0.25), 90.0); sh_key(sh, s("13-01") + 2.6, (0.9, 0.25), 90.0)
    # 13-02：「いいえ」のあと、足音を立てずに奥へ（すべるように。音なし）
    t_ = wv("13-02", "いいえ") + 0.6
    sh_key(sh, t_, (0.9, 0.25)); sh_key(sh, e("13-02") + 0.2, (6.6, 0.55))
    # 13-03：hall2 の扉を少し開けてのぞく → 閉める → tags の扉でも
    t_ = s("13-03") + 0.2
    sh_key(sh, t_, (6.6, 0.55)); sh_key(sh, t_ + 0.8, (D_["hall2"] - 0.2, 0.8), 150.0)
    door_key("hall2", t_ + 0.9, 0, "LINEAR"); door_key("hall2", t_ + 1.3, 50); door_key("hall2", t_ + 2.2, 50); door_key("hall2", t_ + 2.6, 0)      # 確認役：28 度では閉じたままに見えた
    ev(t_ + 0.9, "squeak", 0.25, "door_hall2")
    sh_key(sh, t_ + 2.4, (D_["hall2"] - 0.2, 0.8), 150.0); sh_key(sh, t_ + 3.4, (D_["tags"] - 0.2, 0.8), 150.0)
    door_key("tags", t_ + 3.5, 0, "LINEAR"); door_key("tags", t_ + 3.9, 50); door_key("tags", t_ + 4.6, 50); door_key("tags", t_ + 5.0, 0)
    ev(t_ + 3.5, "squeak", 0.25, "door_tags")
    for nm_, ta_ in (("hall2", t_ + 0.9), ("tags", t_ + 3.5)):       # のぞく間、部屋の中をうすく照らす（確認役：扉が開くのが見えなかった）
        for tt_, en_ in ((ta_ - 0.4, 0.0), (ta_ + 0.3, 18.0), (ta_ + 1.3, 18.0), (ta_ + 1.7, 0.0)): light_key(IN["room_" + nm_], tt_, en_)
    # 13-05〜13-07 の間、影は奥（13 の手前）へ。13-08 で廊下を見渡す
    sh_key(sh, e("13-04"), (D_["tags"] - 0.2, 0.8), 90.0); sh_key(sh, s("13-08"), (11.8, 0.3), 90.0)
    for k, a in enumerate((90, 40, 140, 90)):
        key(sh.root, "rotation_euler", wv("13-08", "すみずみ") - 1.0 + k * 0.9, (0, 0, R(a)))
    # 14-01：管理する人の部屋の机。引き出しを開けて、赤い鍵束を持ち上げる
    ta = s("14-01")
    sh_key(sh, ta - 0.1, (11.8, 0.3), 90.0, "CONSTANT"); sh_key(sh, ta - 0.05, (D_["admin"] - 0.15, Y_ROOM + 1.0), 0.0 + 180.0, "CONSTANT")   # 部屋の中（場面が替わる所で置き直す）
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
    sh_key(sh, tb - 0.1, (D_["admin"] - 0.15, Y_ROOM + 1.0), 180.0, "CONSTANT"); sh_key(sh, tb - 0.05, (D_["admin"] + 0.3, 0.2), 90.0, "CONSTANT")
    key(sh.arm, "rotation_euler", tb + 0.1, (R(5), 0, 0)); key(sh.arm, "rotation_euler", tb + 0.6, (R(40), 0, 0))
    bm = bpy.data.materials.get("in_bundle")
    if bm is None:
        for m_ in bpy.data.materials:
            if m_.name.startswith("in_bundle"): bm = m_; break
    if bm is not None:
        emit_key(bm, -100.0, 0.0, "CONSTANT"); emit_key(bm, tb + 0.6, 0.0); emit_key(bm, tb + 0.9, 1.2); emit_key(bm, e("14-03") + 0.3, 1.2); emit_key(bm, e("14-03") + 0.8, 0.3)
    ev(tb + 0.8, "ding", 0.25, "bundle2")
    for k, (nm, x) in enumerate(IDOORS):
        bpy.ops.object.light_add(type='POINT', location=(x, YB - 0.5, 1.3)); fl = bpy.context.object; fl.data.color = srgb("#FF5A4A")[:3]; fl.data.shadow_soft_size = 0.4
        t0_ = tb + 1.1 + 0.25 * k
        for tt, en in ((-100.0, 0.0), (t0_, 0.0), (t0_ + 0.15, 60.0), (t0_ + 0.6, 0.0)): light_key(fl, tt, en)
    # 14-03：鍵束の寄り（影の手の中で光る）
    # 14-04：2 つの扉に赤い印（「こっそり」で 1 つ目、そのあと 2 つ目）。まるロボがびくっ
    tc = s("14-04")
    # 確認役 2 回目：「こっそり」と「印」が 0.65 秒しか離れておらず、1 つ目の扉から 2 つ目の扉（2.6 m）へ 0.15 秒で移ってワープに見えた
    #   → 1 つ目の印は「2つの部屋の扉に」の間に付け、2.2 秒かけて歩いて 2 つ目の扉へ。2 つ目は「印を付けました」
    t_m1 = tc + 0.9; t_m2 = wv("14-04", "印") + 0.5
    sh_key(sh, tc - 0.1, (D_["admin"] + 0.3, 0.2), 90.0, "CONSTANT"); sh_key(sh, tc - 0.05, (D_["tags"] - 0.3, 0.85), 180.0, "CONSTANT")
    key(sh.arm, "rotation_euler", t_m1 - 0.3, (R(5), 0, 0)); key(sh.arm, "rotation_euler", t_m1, (R(70), 0, 0))
    key(sh.arm, "rotation_euler", t_m1 + 0.4, (R(5), 0, 0))
    for nm, tm in (("tags", t_m1), ("backup", t_m2)):
        mk = IN["mark_" + nm]; key(mk, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(mk, "scale", tm, (0.001,) * 3); key(mk, "scale", tm + 0.25, (1, 1, 1))
        ev(tm, "squeak2", 0.3, "door_" + nm); track("mark_" + nm, mk, 0.0)
    sh_key(sh, t_m1 + 0.5, (D_["tags"] - 0.3, 0.85), 180.0); key(sh.root, "rotation_euler", t_m1 + 0.75, (0, 0, R(90)))       # 進む向き（+x）を向いて歩く
    sh_key(sh, t_m2 - 0.6, (D_["backup"] - 0.3, 0.85), 90.0); key(sh.root, "rotation_euler", t_m2 - 0.4, (0, 0, R(180)))
    key(sh.arm, "rotation_euler", t_m2 - 0.3, (R(5), 0, 0)); key(sh.arm, "rotation_euler", t_m2, (R(70), 0, 0)); key(sh.arm, "rotation_euler", t_m2 + 0.4, (R(5), 0, 0))
    # 14-05〜14-07：扉が開いて中を見せる（影は扉の前に立ったまま）→ 閉める
    door_key("tags", s("14-05") + 0.4, 0, "LINEAR"); door_key("tags", s("14-05") + 1.1, 85); door_key("tags", e("14-06") + 0.3, 85); door_key("tags", e("14-06") + 1.0, 0)
    ev(s("14-05") + 0.4, "squeak", 0.25, "door_tags")      # 場面が替わり終わってから開く（2 回目の点検：替わる重なりの中で鳴った）
    sh_key(sh, s("14-05"), (D_["backup"], 0.85), 180.0); sh_key(sh, s("14-05") + 0.05, (D_["tags"] + 1.3, 0.3), 160.0, "CONSTANT")       # 扉の回る所の外
    sh_key(sh, s("14-07") - 0.1, (D_["tags"] + 1.3, 0.3), 160.0); sh_key(sh, s("14-07") - 0.05, (D_["backup"] + 1.3, 0.3), 160.0, "CONSTANT")
    door_key("backup", s("14-07") + 0.45, 0, "LINEAR"); door_key("backup", s("14-07") + 1.15, 85); door_key("backup", s("14-08") + 0.2, 85); door_key("backup", s("14-08") + 0.9, 0)
    ev(s("14-07") + 0.45, "squeak", 0.25, "door_backup")      # 場面が替わり終わってから（v1：替わる途中で鳴らず）
    # 14-09：予備の倉庫の扉の前に立つ影（後ろ姿）
    sh_key(sh, s("14-09") - 0.1, (D_["backup"] + 1.3, 0.3), 160.0, "CONSTANT"); sh_key(sh, s("14-09") - 0.05, (D_["backup"], 0.75), 180.0, "CONSTANT")
    # 15-01：名札の倉庫の扉を鍵束で開ける
    tf = s("15-01")
    sh_key(sh, tf - 0.1, (D_["backup"], 0.75), 180.0, "CONSTANT"); sh_key(sh, tf - 0.05, (D_["tags"] + 0.1, 1.05), 180.0, "CONSTANT")      # 取っ手に手が届く所（2 回目の点検：0.85 m 離れて手が届かなかった）
    t_k2 = wv("15-01", "鍵束") + 0.2       # 「あの鍵束で」：鍵束を扉の取っ手に当てる → カチャ → すぐに開く（確認役：鍵で開けるのが見えず、音が 2〜3 秒前で小さかった）
    key(sh.arm, "rotation_euler", t_k2 - 0.6, (R(5), 0, 0)); key(sh.arm, "rotation_euler", t_k2, (R(-50), 0, 0)); ev(t_k2 + 0.05, "click", 0.9, "door_tags")
    key(sh.arm, "rotation_euler", t_k2 + 0.5, (R(-50), 0, 0)); key(sh.arm, "rotation_euler", t_k2 + 0.9, (R(10), 0, 0))      # 開けたら腕を下ろす（入りこみの点検：鍵束が扉の枠に当たった）
    door_key("tags", t_k2 + 0.2, 0, "LINEAR"); door_key("tags", t_k2 + 0.5, 30); door_key("tags", t_k2 + 1.1, 88); ev(t_k2 + 0.2, "squeak", 0.25, "door_tags")      # ギィと同時に動きだす（2 回目の点検：ゆっくり動きだし、音から 0.6 秒遅れて見えた）
    sh_key(sh, t_k2 + 1.0, (D_["tags"] + 0.1, 1.05), 180.0); sh_key(sh, t_k2 + 1.6, (D_["tags"] + 0.1, 1.1), 180.0); sh_key(sh, s("15-02") - 0.06, (D_["tags"] + 0.1, 1.1), 180.0, "CONSTANT")      # 扉が開いて一歩入りかけた所で、次の場面（部屋の中）へ。部屋へ歩いて入るのは映さない（入りこみの点検：0.03 秒で 2 m 動いていた・扉の枠をかすめた）
    # 15-02：名札を箱につめる（3 枚が棚から箱へ）。箱は部屋の床
    # 確認役 2 回目：手が棚に届かず（手から棚まで 1.2 m）、名札が棚から手へ、手から遠くの箱へ宙を飛んでいた
    #   → 場面が替わる重なりで、影を棚の前（手が届く所）へ。手のすぐ近くの 3 枚を取り、箱は手を下ろした所の真下に
    bx = tag_box(TBOX_AT); track("tbox", bx, 0.15)
    sh_key(sh, s("15-02") - 0.05, SH_SHELF, 180.0, "CONSTANT")
    tags = IN["tags_tags"]
    pick = [tags[7 + 3], tags[7 + 2], tags[7 + 4]]      # 2 段目のまん中の 3 枚（1 枚目がまるロボの青緑）。手の前の 3 枚
    for k, tg in enumerate(pick):
        t0_ = s("15-02") + 0.2 + k * 0.8
        p0 = tuple(tg.location); r0 = tuple(tg.rotation_euler)
        p1 = (bx.location[0] - 0.1 + 0.1 * k, bx.location[1] - 0.02 + 0.03 * k, 0.05 + 0.012 * (2 - k))      # まるロボの青緑の名札をいちばん上に（v1：ほかの札の下に隠れた）
        key(tg, "location", -100.0, p0, "CONSTANT"); key(tg, "location", t0_, p0)
        key(tg, "location", t0_ + 0.75, p1)
        IN.setdefault("_tag_hand", []).append((tg, t0_))       # 棚 → 手 → 箱（手の場所はあとで計る。確認役：名札が手を通らず勝手に飛んだ）
        key(tg, "rotation_euler", t0_, r0); key(tg, "rotation_euler", t0_ + 0.75, (0, 0, R(8 * k - 8)))
        key(sh.arm, "rotation_euler", t0_ - 0.25, (R(-10), 0, 0)); key(sh.arm, "rotation_euler", t0_, (R(ARM_UP), 0, 0)); key(sh.arm, "rotation_euler", t0_ + 0.3, (R(ARM_UP + 10), 0, 0)); key(sh.arm, "rotation_euler", t0_ + 0.65, (R(40), 0, 0))
        ev(t0_ + 0.75, "paper", 0.3, "tbox")
        if k == 0: track("mytag", tg, 0.0)
    sc_ = 1.1 / SHS2 * 1.4
    key(kb2, "scale", s("15-02") - 0.15, (sc_,) * 3, "CONSTANT"); key(kb2, "scale", s("15-02") - 0.1, (0.001,) * 3, "CONSTANT"); key(kb2, "scale", s("15-05") - 0.3, (0.001,) * 3, "CONSTANT"); key(kb2, "scale", s("15-05") - 0.25, (sc_,) * 3, "CONSTANT")      # 名札を持つ間は鍵束をしまう（場面の替わり目で）
    # 15-05：箱をかかえて廊下を裏口のほうへ（箱は影の胸の前。持ち替えは箱の場面の外で）
    bx2 = tag_box((0, 0, 0)); bx2.parent = sh.root; bx2.location = (0, -0.55, 0.9); bx2.scale = (0.001,) * 3
    key(bx2, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(bx2, "scale", s("15-05") - 0.3, (0.001,) * 3, "CONSTANT"); key(bx2, "scale", s("15-05") - 0.25, (1.0 / SHS2,) * 3, "CONSTANT")
    key(bx, "scale", -100.0, (1, 1, 1), "CONSTANT"); key(bx, "scale", s("15-05") - 0.3, (1, 1, 1), "CONSTANT"); key(bx, "scale", s("15-05") - 0.25, (0.001,) * 3, "CONSTANT")
    for tg in pick:
        key(tg, "scale", -100.0, (1, 1, 1), "CONSTANT"); key(tg, "scale", s("15-05") - 0.3, (1, 1, 1), "CONSTANT"); key(tg, "scale", s("15-05") - 0.25, (0.001,) * 3, "CONSTANT")
    track("box2", bx2, 0.2)
    # 箱を持ちかえる所は、カメラの後ろ（部屋の奥）。影は部屋から歩いて出てくる（置き直さない。入りこみの点検：入口のまるロボとぶつかった）
    key(sh.arm, "rotation_euler", s("15-05") - 0.25, (R(-20), 0, 0), "CONSTANT")
    sh_key(sh, s("15-05") - 0.26, SH_SHELF, 180.0, "CONSTANT"); sh_key(sh, s("15-05") - 0.25, (D_["tags"] + 0.2, Y_ROOM + 1.5), 0.0, "CONSTANT")      # 箱を持つのは、棚から離れて出口を向いてから（場面の替わり目で。入りこみの点検：棚を向いたまま箱が出て、箱が棚に入った）
    sh_key(sh, s("15-05") + 0.6, (D_["tags"] + 0.2, Y_ROOM + 1.2), 0.0); sh_key(sh, s("15-05") + 1.0, (D_["tags"] - 0.05, Y_ROOM + 0.7), 0.0); sh_key(sh, s("15-05") + 2.0, (D_["tags"] - 0.05, 0.45), 0.0)     # 出入口のまん中を通る
    sh_key(sh, s("15-05") + 2.4, (D_["tags"] - 0.1, 0.4), -90.0); sh_key(sh, e("15-05") + 0.4, (2.0, 0.3), -90.0)
    door_key("tags", e("15-05") + 0.5, 88); door_key("tags", e("15-05") + 1.3, 0)      # 影が出ていったあと、場面の外で閉める（v1：16 の錠が開いた扉に付いて見えた）
    # 15-06〜16-02 はお城の外（b_out2）。16-03：もう一度、廊下を奥へ（背中に「？」）
    sh_key(sh, s("16-03") - 0.1, (2.0, 0.3), 90.0, "CONSTANT"); sh_key(sh, s("16-03") - 0.05, (0.6, 0.25), 90.0, "CONSTANT")
    key(bx2, "scale", s("16-03") - 0.4, (0.001,) * 3, "CONSTANT")
    sh_key(sh, s("16-03"), (0.6, 0.25), 90.0); sh_key(sh, e("16-03") - 0.05, (4.2, 0.4), 90.0)
    key(sh.arm, "rotation_euler", s("16-03"), (R(-20), 0, 0))
    # 16-04〜16-06：赤い錠（声の「ガチャン」の時刻）。影は見せない所で動く
    t_l1 = wv("16-04", "ガチャン") + 0.08
    pop_lock("tags", t_l1)
    # 1 つ目の錠は、影が手でかける所を見せる（確認役 2 回目：錠の場面に影がいなくて、だれがかけたか分からない）。扉の取っ手の右に立ち、扉のほうを向いて腕を上げる
    sh_key(sh, e("16-03") - 0.04, (4.2, 0.4), 90.0, "CONSTANT"); sh_key(sh, e("16-03") - 0.03, SH_LOCK, 210.0, "CONSTANT")
    key(sh.arm, "rotation_euler", t_l1 - 0.9, (R(-20), 0, 0)); key(sh.arm, "rotation_euler", t_l1 - 0.5, (R(-85), 0, 0)); key(sh.arm, "rotation_euler", t_l1 + 0.15, (R(-85), 0, 0)); key(sh.arm, "rotation_euler", t_l1 + 0.7, (R(-10), 0, 0))
    sh_key(sh, t_l1 + 0.8, SH_LOCK, 210.0); sh_key(sh, t_l1 + 1.8, (SH_LOCK[0] + 0.6, SH_LOCK[1] - 0.25), 120.0)      # かけたら、廊下の奥へ下がる
    g1 = wv("16-05", "ガチャン") + 0.08; g2 = wv("16-05", "ガチャン", 1) + 0.08
    pop_lock("admin", g1); pop_lock("work", g2)       # 2 つが 1 枚の絵に入るとなりの扉（v1 の決まり：動きを目で追える。5 m 先へ 0.6 秒で振ると追えない）
    pop_lock("hall2", e("16-05") + 0.3, heard=False); pop_lock("hall5", e("16-05") + 0.5, heard=False)      # 映らない扉（音なし）
    pop_lock("backup", wv("16-06", "ガチャン") + 0.08, 1.6)
    sh_key(sh, e("16-04") + 0.05, (SH_LOCK[0] + 0.6, SH_LOCK[1] - 0.25), 120.0, "CONSTANT"); sh_key(sh, e("16-04") + 0.1, (40.0, 30.0), 90.0, "CONSTANT")      # 2 つ目からの錠は、影を見せない（錠だけ）
    # 16-07：まるロボが走り回る → 予備の倉庫の扉の前でへたりこむ（まるロボは下で）
    # 16-11〜16-12：朝。働く人が扉を引く → 開かない（ガタッ）。この扉も、あの扉も
    wk = walker((1.0, -0.2, 0.0), 90.0, shirt="#5A7BA8", pants="#2D3640"); track("worker", wk.head, 0.0)
    key(wk.root, "location", -100.0, (40.0, 40.0, 0.0), "CONSTANT"); key(wk.root, "location", s("16-11") - 0.5, (40.0, 40.0, 0.0), "CONSTANT")
    tw = s("16-11") - 0.45
    key(wk.root, "location", tw, (D_["hall2"] - 1.2, 0.55, 0.02), "CONSTANT"); key(wk.root, "rotation_euler", tw, (0, 0, R(90)), "CONSTANT")
    pulls = [(D_["hall2"], wv("16-12", "扉が開きません") - 0.2), (D_["tags"], wv("16-12", "この扉") + 0.1), (D_["backup"], wv("16-12", "どの扉") + 0.1)]
    xprev = D_["hall2"] - 1.2
    for k, (dx_, tp) in enumerate(pulls):
        xr = dx_ + ID_W / 2 - 0.15 - 0.25      # 取っ手の少し左に立つ
        wk_walk(wk, tp - 1.3, tp - 0.3, (xprev, 0.55), (xr, 0.55), 90.0)     # 1 回目も取っ手まで歩いてから引く（確認役：だれもさわっていないのにガタッ）
        key(wk.root, "rotation_euler", tp - 0.25, (0, 0, R(90))); key(wk.root, "rotation_euler", tp - 0.05, (0, 0, R(180)))
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
        for tt, col, st in ((-100.0, "#CFE6FF", 1.6), (wv("16-13", "パソコン") - 0.1 + 0.3 * k, "#CFE6FF", 1.6), (wv("16-13", "パソコン") + 0.2 + 0.3 * k, "#E0322C", 2.2)):
            bb.inputs["Emission Color"].default_value = srgb(col); bb.inputs["Emission Color"].keyframe_insert("default_value", frame=f(tt))
            bb.inputs["Emission Strength"].default_value = st; bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f(tt))
    for k in range(2): track("screen%d" % k, bpy.data.objects[[o.name for o in bpy.data.objects if o.active_material is scr[k]][0]], 0.0)
    xw = D_["work"]
    for k in range(5):
        pp = cube(mat("paper", "#FFFFFF", rough=0.6), (xw - 0.3, Y_ROOM + 2.25, 0.775 + 0.01 * k), (0.21, 0.3, 0.008), rot=(0, 0, R(6 * k - 12)))
        hide_key(pp, -100.0, True); hide_key(pp, wv("16-14", "注文") - 0.2 + 0.25 * k, False)
    track("orders", pp, 0.05)
    for k in range(3):
        b_ = cube(mat("parcel", "#C9A06A", rough=0.8), (xw + 0.3, Y_ROOM + 2.25, 0.83 + 0.16 * k), (0.28, 0.2, 0.15), rot=(0, 0, R(8 * k - 8)))
        hide_key(b_, -100.0, True); hide_key(b_, wv("16-14", "荷物") - 0.2 + 0.3 * k, False)
    track("parcels", b_, 0.1)
    # 17：持ち主の部屋。手紙が 2 通、ひらひら落ちる。2 通とも持ち主の頭の右に（確認役 2 回目：1 通目が持ち主の頭の陰で、1 通しか見えなかった）
    ox, oy = OWN
    lts = []
    for k in range(2):
        lt = letter((ox + LX0 + 0.5 * k, oy + 1.45, 2.6)); lts.append(lt); track("letter%d" % k, lt, 0.0)
        t0_ = s("17-01") + 1.0 + 0.6 * k
        key(lt, "location", -100.0, (ox + LX0 + 0.5 * k, oy + 1.45, 2.6), "CONSTANT"); key(lt, "location", t0_, (ox + LX0 + 0.5 * k, oy + 1.45, 2.6))
        for j in range(1, 5):
            key(lt, "location", t0_ + 0.45 * j, (ox + LX0 + 0.5 * k + (0.12 if j % 2 else -0.12), oy + 1.45, 2.6 - (2.6 - 0.82) * j / 4))
            key(lt, "rotation_euler", t0_ + 0.45 * j, (R(18 if j % 2 else -18), 0, R(10 * k)))
        key(lt, "rotation_euler", t0_ + 2.0, (0, 0, R(10 * k - 5)))
        ev(t0_ + 1.85, "paper", 0.3, "letter%d" % k)
    # ---- まるロボ（柱のかげで見張る → 名札に気づく → 走り回ってへたりこむ → 持ち主のうしろからのぞく）
    M = MaruR((30.0, 30.0, 0.0), face=90.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    PX = IN["pillars"]
    M.at(s("13-06") - 0.5, loc=(PX[3] - 0.76, -1.0, 0.0), face=110.0, interp="CONSTANT")     # 柱（x=9.1）の左のかげ。奥の影のほうを向く
    M.peer(s("13-06") + 0.3, 1.2)
    M.blink(wv("13-06", "ずっと") + 0.1); M.blink(wv("13-06", "ずっと") + 0.5)
    M.confused(wv("13-07", "なぜ") + 0.1)
    M.at(tc - 0.3, loc=(PX[3] - 0.76, -1.0, 0.0), face=110.0, interp="CONSTANT")      # 柱の影の側（確認役：廊下のまん中で丸見えだった）
    M.surprise(t_m1 + 0.25)
    M.at(s("15-04") - 1.2, loc=(D_["tags"] + 0.95, 0.55, 0.0), face=205.0, interp="CONSTANT")      # 名札の倉庫の入口の右から、ななめに中をのぞく（出てくる影の通り道の外。まるロボは歩くのが遅いので、下がらせない）
    M.surprise(wv("15-04", "まるロボ") + 0.25)      # 場面が替わり終わってから（v1：替わる途中で、驚く音が鳴らなかった）
    M.at(e("15-05") + 0.6, loc=(40.0, -30.0, 0.0), interp="CONSTANT")
    tr = s("16-07")
    # 確認役 2 回目：「走り回る」のに 1 m 歩いて来るだけだった → 横から撮り、錠のかかった 2 つの扉の間を、ぴょんぴょん行って戻って、
    #   最後の錠（予備の倉庫）の前でへたりこむ。1 回のぴょんは 0.7 m・0.65 秒（1 つの動きは 1.4 m まで）
    xa, xb, yy = D_["tags"] + 0.2, D_["backup"] - 0.25, 0.45
    M.at(tr - 0.3, loc=(xa, yy, 0.0), face=90.0, interp="CONSTANT")
    #   計画の点検で、跳ぶ動きも 1 秒に 0.5 m ほどで、行って戻ると 3 秒遅れた → 1 つ目の錠の扉から、予備の倉庫の扉まで、1 回で急いで跳んでいく
    M.path([(xa + 0.68, yy, 0.0), (xa + 1.36, yy, 0.0), (xb, yy, 0.0)], [tr + 0.8, tr + 2.0, tr + 3.2], silent=False)
    M.sigh(tr + 3.8)       # 最後の錠（予備の倉庫）の前で。映っている間に（確認役：ため息が次の場面にかかった）
    M.at(e("16-07") + 0.9, loc=(40.0, -30.0, 0.0), interp="CONSTANT")
    M.at(s("17-01") - 0.5, loc=(ox + 0.8, oy + 0.5, 0.0), face=170.0, interp="CONSTANT")       # 持ち主の右うしろで見ている（確認役：持ち主の部屋の 36 秒、まるロボがいなかった）
    M.peer(wv("17-02", "元に") - 0.2, 1.2)
    M.confused(wv("17-04", "かも") + 0.1)
    M.at(s("17-07") - 0.6, loc=(ox + 0.8, oy + 0.5, 0.0), face=170.0)       # 持ち主の右うしろから、手紙をのぞきこむ
    M.peer(s("17-07") + 0.3, 1.2)
    M.at(s("17-18") - 0.5, loc=(ox + 1.0, oy + 0.45, 0.0), face=150.0, interp="CONSTANT")
    M.nod(wv("17-18", "払わない") + 0.3)
    # 13-04：かべのカレンダーが 1 枚ずつめくれる（数字なし）。窓の夜と昼も替わる（day_night）
    pages = calendar(17.0, n=4); track("calendar", pages[0], 0.0)
    for k, tt in enumerate((wv("13-04", "1枚") - 0.1, wv("13-04", "また1枚") - 0.1, e("13-04") - 0.9)):
        key(pages[k], "rotation_euler", -100.0, (0, 0, 0), "CONSTANT"); key(pages[k], "rotation_euler", tt, (0, 0, 0)); key(pages[k], "rotation_euler", tt + 0.5, (R(-175), 0, 0))
        key(pages[k], "scale", -100.0, (1, 1, 1), "CONSTANT"); key(pages[k], "scale", tt + 0.45, (1, 1, 1), "CONSTANT"); key(pages[k], "scale", tt + 0.5, (0.001,) * 3, "CONSTANT")      # めくった紙は消す（確認役：上に浮いたままだった）
        ev(tt + 0.1, "paper", 0.3, "calendar")
    _bundle_handoff_fix()
    return sh, M


def _bundle_handoff_fix():
    """鍵束 1（引き出しの中から持ち上げる）を、手の鍵束 2 の場所まで動かしてから替える（一瞬で移さない）"""
    if "_bundle_handoff" not in IN: return
    kb, kb2, t_a, t_b = IN["_bundle_handoff"]
    sc = bpy.context.scene
    for tg, t0_ in IN.get("_tag_hand", []):      # 名札は、手の所を通って箱へ
        for dt in (0.3, 0.5):
            sc.frame_set(f(t0_ + dt)); q = IN["_hand"].matrix_world.translation.copy()
            key(tg, "location", t0_ + dt, (q.x, q.y - 0.05, q.z - 0.05))
    sc.frame_set(f(t_b)); p = kb2.matrix_world.translation.copy()
    key(kb, "location", t_b - 0.05, (p.x, p.y, p.z))
    key(kb, "scale", -100.0, (1.1,) * 3, "CONSTANT"); key(kb, "scale", t_b + 0.04, (1.1,) * 3, "CONSTANT"); key(kb, "scale", t_b + 0.05, (0.001,) * 3, "CONSTANT")
    sc.frame_set(0)


# ======================================================================== O：夜のお城の外（15-06〜16-02・16-08・16-09）
def b_out2(cl):
    C_, gk = _castle_common(True)
    SH = SHS2
    sh = shadow((40.0, 40.0, 0.0), face=180.0, s=SH); track("shadow", sh.root, 1.5 * SH)
    bx = tag_box((0, 0, 0)); bx.parent = sh.root; bx.location = (0, -0.55, 0.9); bx.scale = (1 / SH,) * 3; track("box", bx, 0.2)      # 荷車の横の板より上で持つ（入りこみの点検）
    key(sh.arm, "rotation_euler", -100.0, (R(-20), 0, 0), "CONSTANT")
    hg = C_["door"]
    key(hg, "rotation_euler", -100.0, (0, 0, R(-94)), "CONSTANT")      # 裏口は開いたまま（影が出入りする）
    # 15-06：上から。横の裏口から、箱を持った影が出ていく
    t6 = s("15-06")
    sh_key(sh, t6 - 0.4, (X_SIDE - 0.6, DOOR_Y), -90.0, "CONSTANT"); sh_key(sh, t6 + 0.4, (X_SIDE - 0.6, DOOR_Y), -90.0)
    sh_key(sh, t6 + 2.2, (X_SIDE + 1.6, DOOR_Y - 0.3), -45.0); sh_key(sh, e("15-06") + 0.4, (X_SIDE + 1.9, DOOR_Y - 2.0), 0.0)     # 角の塔（半径 1.4）の外を通る。−y へ歩くので前を −y（face 0）に（確認役：後ろ向きに歩き、箱が背中で見えなかった）
    # 15-07：暗い道を遠ざかる（−y へ）
    sh_key(sh, s("15-07"), (X_SIDE + 1.9, DOOR_Y - 2.0), 0.0); sh_key(sh, e("15-07") - 0.2, (X_SIDE + 1.9, DOOR_Y - 6.5), 0.0)
    # 16-01：さらに道の先へ歩き、遠くの道ばたに箱を置く（「運び出された」の続き。確認役：箱が地面をすべり、手前に置きっぱなし）
    t1_ = s("16-01")
    sh_key(sh, t1_ + 0.2, (X_SIDE + 1.9, DOOR_Y - 6.5), 0.0); sh_key(sh, t1_ + 2.6, (X_SIDE + 1.9, DOOR_Y - 9.85), 0.0)      # 荷車の手前 0.75 m で止まる（入りこみの点検：荷車の板と車輪に体が入った）
    key(sh.arm, "rotation_euler", t1_ + 2.6, (R(-20), 0, 0)); key(sh.arm, "rotation_euler", t1_ + 3.2, (R(-50), 0, 0))
    # 道ばたの荷車に積む（確認役 2 回目：箱を道に置きっぱなしで戻るのはおかしい → 運び出すための荷車に積んだ形にする）
    CART = (X_SIDE + 1.9, DOOR_Y - 10.6); BED = 0.46
    cw_ = mat("cart", "#6E5038", rough=0.8)
    cube(cw_, (CART[0], CART[1], BED - 0.03), (0.8, 0.62, 0.05))
    for sx in (-1, 1): cube(cw_, (CART[0] + sx * 0.4, CART[1], BED + 0.08), (0.04, 0.62, 0.2))
    for sy in (-1, 1): cube(cw_, (CART[0], CART[1] + sy * 0.31, BED + 0.08), (0.8, 0.04, 0.2))
    for sx in (-1, 1): cyl(mat("wheel", "#3A2A1E", rough=0.8), (CART[0] + sx * 0.46, CART[1], 0.25), 0.25, 0.06, rot=(0, R(90), 0))
    for sx in (-1, 1): cube(cw_, (CART[0] + sx * 0.18, CART[1] - 0.75, 0.4), (0.04, 0.9, 0.04), rot=(R(-12), 0, 0))     # 引く棒（道の先の向き）
    key(bx, "location", t1_ + 2.6, (0, -0.55, 0.9)); key(bx, "location", t1_ + 3.2, (0, -0.99, (BED + 0.02) / SH))
    bx_g = tag_box((CART[0], CART[1] + 0.0, BED)); key(bx_g, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(bx_g, "scale", t1_ + 3.25, (0.001,) * 3, "CONSTANT"); key(bx_g, "scale", t1_ + 3.3, (1, 1, 1), "CONSTANT")
    key(bx, "scale", t1_ + 3.25, (1 / SH,) * 3, "CONSTANT"); key(bx, "scale", t1_ + 3.3, (0.001,) * 3, "CONSTANT")
    ev(t1_ + 3.25, "thud", 0.2, "box")
    # 16-02：くるりと向きを変えて、裏口から中へ戻る
    t2_ = s("16-02") + 0.2
    key(sh.root, "rotation_euler", t2_, (0, 0, R(0))); key(sh.root, "rotation_euler", t2_ + 0.6, (0, 0, R(-180)))      # 荷車と反対の側へ回る。次の −90 へは 90 度だけ（前は 180 → −90 で 270 度回っていた）       # くるりと向きを変える（前を +y＝お城へ）
    sh_key(sh, t2_ + 0.6, (X_SIDE + 1.9, DOOR_Y - 9.85)); sh_key(sh, t2_ + 4.2, (X_SIDE + 2.2, DOOR_Y - 1.6), -180.0); sh_key(sh, t2_ + 4.8, (X_SIDE + 1.1, DOOR_Y + 0.05), -135.0)      # 歩く間は前（+y）を向いたまま（前は歩きながら少しずつ回っていた）
    sh_key(sh, t2_ + 5.6, (X_SIDE - 0.9, DOOR_Y + 0.05), -90.0); ev(t2_ + 0.3, "swish", 0.25, "shadow")      # 出入口のまん中を通る。鍵束を持つ腕は下ろして体に寄せる（入りこみの点検：鍵束が扉の枠に当たった）
    # 「鍵束を持って」：向きを変えながら、鍵束を持った手を上げる（確認役 2 回目：影が遠くて小さく、鍵束が見えなかった → 寄りのカット O16k）
    kbo = key_bundle((0, 0, 0), parent=sh.hand, s=1.1 / SH * 1.4); kbo.location = (0, -0.1, -0.08); track("bundle_o", kbo, 0.0)
    key(kbo, "scale", -100.0, (0.001,) * 3, "CONSTANT"); key(kbo, "scale", t1_ + 3.6, (0.001,) * 3, "CONSTANT"); key(kbo, "scale", t1_ + 3.65, (1.1 / SH * 1.4,) * 3, "CONSTANT")      # 箱を置いたあと、手に持つ
    key(sh.arm, "rotation_euler", t2_ + 0.05, (R(-50), 0, 0)); key(sh.arm, "rotation_euler", t2_ + 0.45, (R(-80), 0, 0)); key(sh.arm, "rotation_euler", t2_ + 1.3, (R(-80), 0, 0)); key(sh.arm, "rotation_euler", t2_ + 1.8, (R(-20), 0, 0)); key(sh.arm, "rotation_euler", t2_ + 3.8, (R(-20), 0, 0)); key(sh.arm, "rotation_euler", t2_ + 4.3, (R(15), 0, 0))
    ev(t2_ + 0.45, "ding", 0.2, "bundle_o")
    key(sh.root, "scale", -100.0, (SH,) * 3, "CONSTANT"); key(sh.root, "scale", t2_ + 5.6, (SH,) * 3, "CONSTANT"); key(sh.root, "scale", t2_ + 5.7, (0.001,) * 3, "CONSTANT")
    # まるロボ：15-07 で裏口から走って出てきて、道の手前で止まる → 16-02 で台のかげへよける
    LG = (X_SIDE + 1.0, DOOR_Y + 2.2)
    cube(_stone(), (LG[0] + 0.25, LG[1], 0.4), (0.5, 1.0, 0.8))
    M = MaruR((30.0, 30.0, 0.0), face=180.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    M.at(s("15-07") - 0.3, loc=(X_SIDE - 0.9, DOOR_Y, 0.0), face=-90.0 + 180.0 - 180.0 + 90.0, interp="CONSTANT")
    M.walk(s("15-07") + 0.3, e("15-07") - 0.3, (X_SIDE + 0.9, DOOR_Y + 0.1, 0.0))      # 扉からまっすぐ出る（開いた扉の板に当たらない）
    M.at(s("16-01") + 0.05, loc=(LG[0] - 0.25, LG[1] - 1.05, 0.0), interp="CONSTANT")     # 影が戻ってくる前に、台のかげへ。場面が替わる重なりの中で置き直す（確認役 2 回目：映らない所を歩く足音が、影の場面で鳴った）
    # 16-02 の驚く動きは外した（まるロボは台のかげで、16-02 の絵に映らない。音だけ鳴らないように）
    # 16-08：窓の明かりが 1 つずつ消える（正面のかべに窓を 6 つ足す。1 つずつ別の材質）
    for k in range(6):
        wm_ = bpy.data.materials.new("out_win%d" % k); wm_.use_nodes = True
        b_ = wm_.node_tree.nodes["Principled BSDF"]; b_.inputs["Base Color"].default_value = (0.03, 0.03, 0.04, 1)
        b_.inputs["Emission Color"].default_value = srgb("#FFC870")
        x_ = (-5.6, -4.2, -2.8, 2.8, 4.2, 5.6)[k]
        cube(wm_, (x_, -0.03, 3.8), (0.55, 0.06, 0.8))
        tk = wv("16-08", "閉ざされて") - 2.6 + 0.55 * k
        for tt, st in ((-100.0, 2.4), (tk, 2.4), (tk + 0.2, 0.0)):
            b_.inputs["Emission Strength"].default_value = st; b_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f(tt))
    track("castle_c", C_["gate"][0], 3.0)
    gf = empty((GK[0], GK[1] - 5.0, 1.0)); track("gk_front", gf, 0.0)     # 門番さんの見ている先（15-06 の扇）
    bpy.ops.object.light_add(type='POINT', location=(X_SIDE + 2.6, DOOR_Y - 8.0, 2.6)); rl = bpy.context.object; rl.data.energy = 60; rl.data.color = srgb("#9FB6FF")[:3]; rl.data.shadow_soft_size = 1.0     # 道の先を照らす（v1：遠くの影が見えなかった）
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
    # 町の家（確認役 2 回目：名札がお城の門の前に降るだけで、「町じゅう」に見えなかった）。道の両側に、屋根のある小さな家
    for k, (hx, hy) in enumerate(((-3.6, -5.2), (-4.4, -7.4), (-5.6, -4.0), (3.4, -5.6), (4.6, -7.8), (5.4, -4.2))):
        wall_ = mat("hs%d" % (k % 3), ["#E9DCC4", "#D9C9B0", "#EFE4D0"][k % 3], rough=0.8)
        cube(wall_, (hx, hy, 0.75), (1.4, 1.2, 1.5))
        cube(mat("roof%d" % (k % 2), ["#A8443A", "#5E6E86"][k % 2], rough=0.7), (hx, hy, 1.75), (1.12, 1.3, 1.12), rot=(0, R(45), 0))
        cube(mat("hwin", "#FFE7A8", rough=0.5), (hx + (0.71 if hx < 0 else -0.71), hy, 0.9), (0.02, 0.4, 0.35))
    for k in range(40):
        x = random.uniform(-6, 6); y = random.uniform(-9, -3); z0 = random.uniform(3.5, 6.5)
        tg = nameplate((x, y, z0), rot=(R(random.uniform(-40, 40)), 0, R(random.uniform(0, 180))), tex=random.choice(["tag_cust", "tag_cust", "tag_maru"]), w=0.75)      # v1：小さくて見えなかった
        td = t0 + random.uniform(0.0, 1.5)
        key(tg, "location", -100.0, (x, y, z0), "CONSTANT"); key(tg, "location", td, (x, y, z0))
        key(tg, "location", td + 4.5, (x + random.uniform(-1, 1), y, max(0.05, z0 - 5.5)))
        key(tg, "rotation_euler", td + 4.5, (R(random.uniform(-80, 80)), 0, R(random.uniform(0, 360))))
    M = MaruR((0.2, -3.6, 0.0), face=180.0 - 180.0); track("maru", M.body, 0.6); track("maru_top", M.body, 0.75)
    M.surprise(t0 + 1.2)


# ======================================================================== カット（2章）
I0 = 0.0
CUTS2 = [
    ("D13", b_in, s("13-01"), C((5.2, -0.4, 1.5), (0.4, 0.25, 0.9), 30, (3.4, -0.1, 1.35)), "D"),     # ゆっくり寄る（確認役：止めた絵が 8 秒）
    ("D13b", b_in, s("13-02"), C((0.15, -1.05, 2.4), (6.5, 0.6, 0.8), 26), "D"),     # 試しの絵：横からだと影が画面いっぱいだった
    ("D13c", b_in, s("13-03"), C((5.9, -0.95, 1.6), (9.0, 1.5, 1.0), 22), "D"),     # 扉の手前の斜めから（確認役：扉が開くのが見えなかった）
    ("D13d", b_in, s("13-04"), C((15.3, -0.95, 1.7), (17.3, 0.9, 1.7), 30), "D"),
    ("D13e", b_in, s("13-05"), C((D_["work"] - 1.1, Y_ROOM + 0.3, 2.3), (D_["work"] + 0.2, Y_ROOM + 2.3, 0.75), 22), "D"),
    ("D13f", b_in, s("13-06"), C((7.2, -0.85, 1.0), (11.0, 0.7, 0.8), 24), "D"),     # まるロボの肩ごしに、廊下の奥の影（確認役 2 回目：「見張っています」なのに影が映らず、まるロボがカメラを向いていた）
    ("D13g", b_in, s("13-07"), C((10.1, 0.4, 0.95), (8.55, -0.95, 0.62), 28), "D"),
    ("D13h", b_in, s("13-08"), C((1.0, -1.0, 2.2), (10.0, 0.8, 0.8), 24), "D"),
    ("D14", b_in, s("14-01"), C((D_["admin"] - 1.15, Y_ROOM + 0.45, 1.3), (D_["admin"] - 0.45, Y_ROOM + 1.5, 0.7), 30), "D"),     # 引き出しと手元が見える左前から（v1：影の背中で暗かった）     # 机の横から（試しの絵：影の背中で机が隠れた）
    ("D14b", b_in, s("14-02"), C((0.6, -1.0, 1.8), (12.0, 0.9, 1.0), 24), "D"),
    ("D14c", b_in, s("14-03"), C((D_["admin"] + 1.4, -0.35, 0.95), (D_["admin"] + 0.68, 0.43, 0.66), 40), "D"),     # 鍵束の高さ（調べた場所 5.88, 0.43, 0.64）     # 影の手の鍵束に寄る（試しの絵：手が画面の外だった）
    ("D14d", b_in, s("14-04"), C((5.9, -0.7, 1.75), (11.0, 0.45, 0.5), 22), "D"),     # 高めのうしろから：柱のかげのまるロボの全身と、2 つの扉に印を付ける影（確認役 2 回目：まるロボの後ろ頭が下で切れて大きかった）     # まるロボ（柱のかげ）も入れる。柱（x 6.5）の外（v1：びくっが映らなかった）
    ("D14e", b_in, s("14-05"), C((D_["tags"], -0.6, 1.45), (D_["tags"], Y_ROOM + 2.6, 0.95), 30, (D_["tags"], YB - 0.2, 1.3)), "D"),
    ("D14f", b_in, s("14-06"), C((D_["tags"], Y_ROOM + 1.1, 1.25), (D_["tags"], Y_ROOM + 2.9, 0.95), 30), "D"),
    ("D14g", b_in, s("14-07"), C((D_["backup"], -0.6, 1.45), (D_["backup"], Y_ROOM + 2.6, 0.95), 30, (D_["backup"], YB - 0.2, 1.3)), "D"),
    ("D14h", b_in, s("14-08"), C((D_["backup"], Y_ROOM + 1.1, 1.25), (D_["backup"], Y_ROOM + 2.9, 0.95), 30), "D"),
    ("D14i", b_in, s("14-09"), C((D_["backup"] - 0.2, -1.0, 1.55), (D_["backup"], YB, 1.35), 30), "D"),
    ("A14", b_house, s("14-10"), C((1.97, 0.4, 0.42), (1.95, 0.65, 0.0), 30), "A"),
    ("D14j", b_in, s("14-12"), C((D_["backup"], Y_ROOM + 1.1, 1.25), (D_["backup"], Y_ROOM + 2.9, 0.95), 30), "D"),
    ("D14k", b_in, s("14-14"), C((D_["backup"] + 0.1, -0.3, 1.6), (D_["backup"], YB, 1.45), 30, (D_["backup"] + 0.1, 0.45, 1.6)), "D"),     # ゆっくり寄る（確認役：止めた絵が 7.6 秒）
    ("D14k2", b_in, wv("14-14", "あとで") - 0.25, C((D_["backup"] - 2.0, -0.45, 1.45), (D_["backup"] + 0.1, YB, 1.15), 28), "D"),     # 横から、予備の倉庫の扉と、その前に立つ影（確認役 2 回目：扉の寄りが 8.2 秒続いた）
    ("D15", b_in, s("15-01"), C((D_["tags"] + 1.7, 0.1, 1.45), (D_["tags"] + 0.3, YB, 1.0), 28), "D"),     # 取っ手の右から、鍵束を当てる手と扉（2 回目の確認役：鍵束が体の陰）
    ("D15b", b_in, s("15-02"), C((D_["tags"] - 1.05, Y_ROOM + 0.35, 1.7), (D_["tags"] - 0.2, Y_ROOM + 2.0, 0.5), 26), "D"),
    ("D15c", b_in, s("15-03"), C((TBOX_AT[0], TBOX_AT[1] - 0.08, 0.95), (TBOX_AT[0], TBOX_AT[1], 0.0), 32), "D"),     # 箱の真上（箱の位置は TBOX_AT から取る。2 回目の確認役の直しで箱を動かしたとき、ここが前の位置のままで茶色一色になった）
    ("D15d", b_in, s("15-04"), C((D_["tags"] - 0.25, Y_ROOM + 0.85, 0.95), (D_["tags"] + 0.95, 0.55, 0.55), 30), "D"),     # 部屋の中から入口のまるロボ（顔）
    ("D15e", b_in, s("15-05"), C((0.6, -0.9, 1.5), (7.5, 0.4, 0.8), 26), "D"),
    ("O15", b_out2, s("15-06"), C((DX + 8.0, -10.0, 8.5), (4.2, 1.0, 0.4), 30), "O"),     # 正面の門番さんと横の裏口が 1 枚に（v1：高すぎて影が小さかった）
    ("O15b", b_out2, s("15-07"), C((DX + 5.0, DOOR_Y - 1.4, 1.05), (DX + 1.6, DOOR_Y - 4.6, 0.6), 24), "O"),     # 道の横から、箱をかかえて遠ざかる影（確認役 2 回目：うしろからで、箱が影の体の陰だった）
    ("O16", b_out2, s("16-01"), C((DX + 5.2, DOOR_Y - 7.0, 1.6), (DX + 1.9, DOOR_Y - 9.5, 0.6), 30), "O"),     # 道の横から、遠くの道ばたに箱を置く影
    ("O16k", b_out2, s("16-02"), C((X_SIDE + 3.3, DOOR_Y - 9.0, 1.3), (X_SIDE + 1.9, DOOR_Y - 9.9, 1.15), 30), "O"),     # 鍵束を持った手を上げる影の寄り（確認役 2 回目）
    ("O16b", b_out2, s("16-02") + 1.7, C((DX + 2.7, DOOR_Y + 1.0, 1.6), (DX + 1.9, DOOR_Y - 8.0, 0.6), 26), "O"),     # 裏口の横から道の先：影がくるりと向きを変えて戻ってくる（v1：向きを変える所がカメラの後ろ。扉の板で半分ふさがれた）
    ("D16", b_in, s("16-03"), C((-0.4, 0.3, 1.5), (6.0, 0.4, 1.0), 30), "D"),
    ("D16b", b_in, e("16-03") + 0.05, C((D_["tags"] - 1.7, -0.75, 1.55), (D_["tags"] + 0.35, YB, 1.15), 26), "D"),     # 廊下の手前から、扉の印・錠・錠をかける影（確認役 2 回目：かかる瞬間が見えず、影もいなかった。カットを 0.5 秒早く始める）
    ("D16c", b_in, e("16-04") + 0.05, C((3.9, -0.7, 1.45), (3.9, YB, 1.05), 22), "D"),
    ("D16d", b_in, e("16-05") + 0.05, C((D_["backup"] + 0.55, 0.15, 0.55), (D_["backup"] + 0.2, YB, 1.05), 28), "D"),
    ("D16e", b_in, s("16-07"), C((D_["tags"] + 0.55, -1.3, 1.2), (D_["backup"] - 0.9, YB, 0.55), 15), "D"),     # 横から、錠のかかった 2 つの扉と、その間を行き来するまるロボ（確認役 2 回目：走り回っていない・字幕が目に重なる）
    ("O16c", b_out2, s("16-08"), C((-4.5, -15.0, 3.2), (0.4, 0.0, 3.0), 30), "O"),
    ("M16", b_morning, s("16-10"), C((3.5, -14.0, 2.4), (0.0, -2.0, 1.4), 30), "M"),
    ("D16f", b_in, s("16-11"), C((D_["hall2"] - 1.3, -0.9, 1.6), (D_["tags"] - 0.3, 1.3, 1.1), 24), "D"),
    ("D16g", b_in, s("16-13"), C((D_["work"], Y_ROOM + 0.4, 2.4), (D_["work"], Y_ROOM + 2.15, 0.85), 24), "D"),     # 上から（確認役：頭が画面いっぱい）
    ("D16g2", b_in, wv("16-13", "パソコン") - 0.45, C((D_["work"], Y_ROOM + 0.75, 1.45), (D_["work"], Y_ROOM + 2.37, 1.0), 26), "D"),     # 2 人の肩ごしに、2 つの画面が赤く固まる（確認役 2 回目：上からの同じ絵が 12.5 秒・画面が頭でかくれる）
    ("D16h", b_in, s("16-14"), C((D_["work"] - 1.1, Y_ROOM + 0.6, 2.5), (D_["work"] + 0.1, Y_ROOM + 2.25, 0.8), 24), "D"),     # 窓の側から、2 つの机の上（注文の紙・荷物）と赤い画面。13-05 の昼の絵ともちがう向き
    ("M16b", b_morning, s("16-15"), C((-4.5, -15.0, 3.2), (0.4, 0.0, 3.2), 30), "M"),
    ("D17", b_in, s("17-01"), C((OWN[0] + 2.4, OWN[1] - 1.0, 2.5), (OWN[0] + 0.3, OWN[1] + 1.3, 0.8), 28), "D"),     # 右うしろの高めから、持ち主・2 通の手紙・まるロボ（確認役 2 回目：まるロボのアンテナだけが画面のまん中に映った）
    ("D17b", b_in, s("17-02"), C((OWN[0] + LX0, OWN[1] + 1.1, 1.35), (OWN[0] + LX0, OWN[1] + 1.45, 0.82), 36), "D"),
    ("D17c", b_in, s("17-03"), C((OWN[0] + 0.4, OWN[1] - 1.4, 1.6), (OWN[0], OWN[1] + 1.5, 1.0), 30), "D"),
    ("D17c2", b_in, s("17-04"), C((OWN[0] + 2.3, OWN[1] + 1.7, 1.35), (OWN[0] + 0.6, OWN[1] + 0.6, 0.6), 30), "D"),     # 前から、首をかしげるまるロボ（v1：17-03〜04 が 1 つの絵で 12 秒、まるロボが映らなかった）
    ("D17d", b_in, s("17-05"), C((D_["backup"] + 0.55, 0.15, 0.55), (D_["backup"] + 0.2, YB, 1.05), 28, (D_["backup"] + 0.45, 0.7, 0.75)), "D"),
    ("D17d2", b_in, s("17-06"), C((D_["backup"] - 2.2, -0.75, 1.5), (D_["backup"], YB, 1.0), 26), "D"),     # 17-06 は廊下から予備の倉庫の扉（確認役：錠の寄りが 11 秒）
    ("D17e", b_in, s("17-07"), C((OWN[0] - 1.3, OWN[1] - 0.2, 1.9), (OWN[0] + 0.2, OWN[1] + 1.35, 0.8), 28), "D"),     # 左うしろから（確認役：まるロボの背中が画面をふさぎ、アンテナが手紙に重なった）
    ("I17", b_imag2, s("17-08"), C((1.2, -11.5, 2.0), (0.2, -3.8, 1.3), 24), "I2"),     # 町の家も入る引き。まるロボを字幕より上に（確認役 2 回目）
    ("D17f", b_in, s("17-09"), C((OWN[0] + LX0 - 0.35, OWN[1] + 0.85, 1.5), (OWN[0] + LX0, OWN[1] + 1.45, 0.82), 32, (OWN[0] + LX0 + 0.1, OWN[1] + 1.12, 1.3), (OWN[0] + LX0 + 0.1, OWN[1] + 1.45, 0.82), 36, d=58.0), "D"),     # 17-09〜17-17 の 60 秒、2D の図の後ろで手紙へゆっくり寄る（v6 で 6 文を足し、止めた絵が長くなった）
    ("D17g", b_in, s("17-18"), C((OWN[0] + 2.2, OWN[1] - 1.8, 2.0), (OWN[0], OWN[1] + 1.0, 0.8), 28), "D"),
    ("P17", b_in, s("14-04") - 0.2, C((7.0, -1.0, 1.6), (12.2, 1.4, 1.05), 24), "D"),       # 17-06 の小窓（14-04 の印を付ける場面をもう一度）
]
PIP2 = {"P17": (s("14-04") - 0.2, e("14-04") + 0.4)}
