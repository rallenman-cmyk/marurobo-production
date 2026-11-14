# 会話と広告の回：S07・S08 以外の 3D の場面（声の時刻に合わせて動く）
# blender -b --factory-startup --python scenes_all.py -- <場面> <出力フォルダ> [samples] [--res W H] [--step N] [--frames A B] [--fast] [--blend]
#   場面：s00 s01 s02 s04 s05 s06a s06b s10 s11 s12 s13 s14 s15 s16 s17 s18 s19 s21 s22
#   出力：<場面>_####.png と <場面>_log.json（t0・t1・fps・frames・足音 steps・効果音 events）
# 決まり：3D の中に字を書かない（札・吹き出し・数字は 2D）。人＝服と肌の色を分けた形、番犬＝ぶちの垂れ耳。まるロボは喋らない
import os, sys, json, math, random
ARGS = sys.argv[sys.argv.index("--") + 1:]
_ANIM_HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_ANIM_HERE, "common.py"), encoding="utf-8").read())
KEY, OUTDIR = ARGS[0], ARGS[1]
N_SAMPLES = int(ARGS[2]) if len(ARGS) > 2 and ARGS[2].isdigit() else 32
def opt(name, default):
    return [type(d)(ARGS[ARGS.index(name) + 1 + k]) for k, d in enumerate(default)] if name in ARGS else default
RESX, RESY = opt("--res", [1920, 1080])
STEP, = opt("--step", [1])
FR = opt("--frames", [0, 0])


def span(*scenes, a=None, b=None):
    t0 = SCENE_T[scenes[0]][0] if a is None else a
    t1 = SCENE_T[scenes[-1]][1] if b is None else b
    CLOCK["T0"] = t0
    return t0, t1


def night_lamp(loc, e=60, col="#CFEFFF"):
    bpy.ops.object.light_add(type='POINT', location=loc)
    L = bpy.context.object; L.data.energy = e; L.data.color = srgb(col)[:3]
    return L


def phone_screen(ph, img, glow):
    """スマホの画面を足す（切り替え用に、画面の板を返す）"""
    p = plane(img_mat("scr_" + img, os.path.join(HERE, img), emit=glow), (0, 0, 0.042), (0.32, 0.66), parent=ph)  # 絵の上がスマホの上
    return p


# ---------------- S00 いきなり夜：テントの広告に、まるロボがびくっ
def s00():
    t0, t1 = span("S00")
    room(night=True); person_lie((0.15, -0.15, 0.42))
    ph = phone((0.35, -0.9, 0.0), 10, screen=None)
    ad = phone_screen(ph, "phone_ad.png", 2.5)
    L = night_lamp((0.35, -0.9, 0.6), 0)
    lightkey(L, 0, 60)
    show([ad], 0, True)                                                   # 声（0.5 秒〜）の前に、びくっと跳ねる
    mr = Maru((-0.25, -1.0, 0), 40, s=0.42, hat=False, eye_glow=1.6)
    mr.hop(0.05, 0.25, 0.4); ev(0.05, "pi"); mr.at(0.05, look=-5); mr.at(0.45, look=-14)
    area((-3, 2, 3), (0, 0, 0), 120, 2, "#7F9CFF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [(t0, t1, (0.5, -3.3, 1.4), (0.1, -0.8, 0.3), (0.35, -2.7, 1.2), (0.1, -0.85, 0.32), 40)])
    return t0, t1


# ---------------- S01 電車：ハルさんとソラさん、まるロボはわくわく
def s01():
    t0, t1 = span("S01")
    _m = globals()["maru"]; globals()["maru"] = lambda *a, **k: empty()
    s5_train(); globals()["maru"] = _m
    train_windows()
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    mr = Maru((0.0, 1.05, 0.5), 0, s=0.55, hat=False, eye_glow=0.9)
    for k, tt in enumerate((s("01-01") + 1.0, s("01-01") + 2.5, s("01-01") + 4.0, s("01-02") + 1.5)):
        mr.at(tt, face=35 if k % 2 == 0 else -35)                 # 二人の顔を交互に見る
    mr.at(s("01-03") - 0.2, face=0, look=8)
    mr.hop(s("01-03") + 0.3, 0.15, 0.35); mr.hop(s("01-03") + 0.8, 0.15, 0.35)   # 行く気まんまん
    cam, tgt = cam_rig()
    # v4「冒頭のテントも、この時点のと配置とか合わせて」(11:07)：つり広告（テント 3 枚）が全部入るように引いて、上も見せる
    shots(cam, tgt, [(t0, t1, (0.15, -1.45, 1.15), (0.0, 1.0, 1.55), (0.0, -1.45, 1.12), (0.0, 1.0, 1.5), 12)])
    return t0, t1


# ---------------- S02 その夜：ニュース → テントの広告 → タオルでマイクをふさぐ
def s02():
    t0, t1 = span("S02")
    room(night=True)
    # v4「ハルさんがスマホを見ていると言っているのに寝ている」(0:45)：ふとんに座って、前のスマホをのぞきこむ
    hr = person((0.8, -0.32, 0.0), 160, shirt="#3E7CB1", s=0.6)   # ふとんのはしに腰かける
    for bn, deg in (("chest", 12), ("neck", 22), ("head", 28)):
        pb = hr.pose.bones[bn]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(deg), 0, 0)
    ph = phone((0.35, -0.9, 0.0), 10, screen=None)
    news = phone_screen(ph, "phone_news.png", 2.2)
    ad = phone_screen(ph, "phone_ad.png", 2.5)
    show([ad], 0, False); show([news], 0, True)
    ta = s("02-02") - 0.2
    show([ad], f(ta), True); show([news], f(ta), False); ev(ta, "pop_ui")
    night_lamp((0.35, -0.9, 0.6), 50)
    mr = Maru((-0.35, -1.05, 0), 40, s=0.42, hat=False, eye_glow=1.2)
    mr.hop(ta + 0.25, 0.25, 0.4); ev(ta + 0.25, "pi")                       # 広告を見てびくっ
    for k, tt in enumerate((s("02-04") + 0.2, s("02-04") + 0.9, s("02-04") + 1.6)):  # きょろきょろ
        mr.at(tt, face=40 + (45 if k % 2 == 0 else -45))
    # タオルを取りに走る → 頭に載せて戻る → スマホにぱさり
    tw = towel((-1.6, -1.6, 0.02), 30)
    tr = s("02-05") - 2.2
    mr.walk(tr - 1.0, tr, (-0.35, -1.05, 0), (-1.5, -1.5, 0), face=120)
    key(tw, "location", f(tr), (-1.6, -1.6, 0.02)); key(tw, "location", f(tr + 0.3), (-1.5, -1.5, 0.62))
    mr.walk(tr + 0.4, tr + 1.4, (-1.5, -1.5, 0), (0.05, -1.0, 0), face=-60)
    key(tw, "location", f(tr + 1.4), (0.05, -1.0, 0.62))
    key(tw, "location", f(tr + 1.75), (0.36, -1.0, 0.06)); ev(tr + 1.75, "towel")
    key(tw, ("rotation_euler", 2), f(tr + 1.4), R(30)); key(tw, ("rotation_euler", 2), f(tr + 1.75), R(12))
    mr.at(tr + 2.0, look=-6); key(mr.body, ("location", 2), f(tr + 2.1), mr.z0); key(mr.body, ("location", 2), f(tr + 2.5), mr.z0 - 0.04)  # ふうっと沈む
    area((-3, 2, 3), (0, 0, 0), 120, 2, "#7F9CFF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("02-04") - 0.3, (0.9, -1.6, 1.0), (0.3, -0.9, 0.05), (0.8, -1.5, 0.9), (0.33, -0.9, 0.05), 36),     # 肩越しにスマホ
        (s("02-04") - 0.3, t1, (0.3, -3.7, 1.6), (-0.2, -0.9, 0.45), (0.2, -3.4, 1.5), (-0.15, -0.9, 0.45), 34)])     # 引き：タオル（ハルさんの顔も入れる）
    return t0, t1


# ---------------- S04 フックの帽子をかぶって探偵に
def s04():
    t0, t1 = span("S04")
    room(night=False, hook_hat=True)
    # v4「帽子ちゃんとかぶってない、ベッドの上じゃなくてすり抜けてる」(1:11)：
    #   ふとんの外（x≥1.6）を歩く。落ちてきた帽子は、頭に乗った瞬間に、まるロボの本物の帽子（いつもの形・大きさ）に入れかえる
    HX, HY = 1.6, 1.4
    hat_e = empty((1.4, 1.73, 1.6))
    _hp = checker_mat("hat_plaid_a", "#B88A55", "#8A6239", 9)
    sphere(_hp, (0, 0, 0), 0.35 * 0.55, scale=(1, 1.02, 0.7), parent=hat_e)
    cyl(mat("hat_band_a", "#5B3B22", rough=0.6), (0, 0, -0.03), 0.352 * 0.55, 0.04, parent=hat_e)
    cyl(_hp, (0, -0.22, -0.03), 0.11, 0.02, rot=(R(-18), 0, 0), scale=(1.05, 0.62, 1), parent=hat_e)
    before = set(bpy.data.objects)
    mr = Maru((1.75, -0.7, 0), 200, s=0.55, hat=True, eye_glow=1.2)
    real_hat = [o for o in set(bpy.data.objects) - before if o.active_material and o.active_material.name.startswith(("hat_plaid", "hat_band"))]
    tj = s("04-02") + 0.8
    show(real_hat, 0, False)
    mr.walk(t0 + 0.5, tj - 1.2, (1.75, -0.7, 0), (HX, HY, 0), face=175)
    mr.at(tj - 0.6, look=-30)                                        # 見上げる
    mr.hop(tj, 0.75, 0.8); ev(tj, "jump"); ev(tj + 0.8, "land")
    key(hat_e, "location", f(tj + 0.3), (1.4, 1.73, 1.6))
    key(hat_e, "location", f(tj + 0.4), (HX, HY + 0.02, 1.36))        # 頭の上（跳んだいちばん上）
    ev(tj + 0.45, "hat")
    _hm = [o for o in real_hat if o.type == "MESH" and o.active_material.name.startswith("hat_plaid")]
    if _hm:                                                           # 届く所は、そのときの本物の帽子の場所ぴったりに
        _hm = max(_hm, key=lambda o: o.dimensions.x * o.dimensions.y)
        bpy.context.scene.frame_set(f(tj + 0.4)); bpy.context.view_layer.update()
        key(hat_e, "location", f(tj + 0.4), tuple(_hm.matrix_world.translation))
        key(hat_e, "rotation_euler", f(tj + 0.4), tuple(_hm.matrix_world.to_euler()))
        bpy.context.scene.frame_set(0)
    # v5「帽子が最初引っかかってない」(1:06)：落ちた帽子は、頭に届いた瞬間（跳んだいちばん上）に本物の帽子へ入れかえる。
    #   前は届いてから 0.4 秒、まっすぐ下がる帽子と、弧を描いて下りるまるロボがずれて、ななめに引っかかって見えた
    _fh = [o for o in bpy.data.objects if o.parent == hat_e] + [hat_e]
    show(_fh, 0, True)                                                # 掛かっている・落ちてくる帽子は見せる（v4 は最初から隠れていて、急に頭に出た）
    show(_fh, f(tj + 0.4), False)
    show(real_hat, f(tj + 0.4), True)                                 # ここから本物の帽子（いっしょに動く）
    mr.at(tj + 1.0, face=180, look=0); mr.at(tj + 1.8, face=10)       # かぶったら、こちらを向く
    mr.at(s("04-03") + 0.3, look=12); mr.glow(s("04-03") + 0.3, 0.3, 6.0); ev(s("04-03") + 0.3, "pipo")   # 胸を張る
    sun((50, 0, 200), 2.0)
    area((0, -3, 2.5), (1.2, 1.2, 1.2), 350, 3, "#FFF1DD")
    cam, tgt = cam_rig()
    shots(cam, tgt, [(t0, t1, (0.2, -2.8, 1.25), (1.3, 1.1, 0.9), (0.5, -2.4, 1.2), (1.45, 1.2, 0.9), 36)])
    return t0, t1


# ---------------- S05 容疑者は3人：一つずつ光が当たる。③は紫のふちの鏡
def ped_set(lit0=(0, 0, 0)):
    world("#1B2733", 0.25); ground("#2C3A47", rough=0.5)
    xs = (-2.3, 0.0, 2.3); ped = mat("ped", "#E8EEF1", rough=0.35, coat=0.3)
    cols = ("#E5484D", "#F2A93B", "#8E6CEF"); lights, bands = [], []
    for x, c, l in zip(xs, cols, lit0):
        cyl(ped, (x, 1.2, 0.45), 0.55, 0.9)
        bm = mat("pedband" + c, c, rough=0.4, emit=0.6 if l else 0.05); bands.append(bm)
        cyl(bm, (x, 1.2, 0.86), 0.57, 0.08)
        L = spot((x, 0.2, 5.2), (x, 1.2, 1.1), 1400 if l else 0, 32, "#FFF6E8"); lights.append(L)
    grille = mat("grille", "#B9C2C8", rough=0.3, metal=0.9)
    sphere(grille, (xs[0], 1.2, 1.55), 0.26)
    cyl(mat("micband", "#E5484D", rough=0.3, metal=0.3), (xs[0], 1.2, 1.32), 0.17, 0.08)
    cyl(mat("michandle", "#30363C", rough=0.35, metal=0.4), (xs[0], 1.2, 1.1), 0.1, 0.42)
    box((xs[1] - 0.22, 1.2, 0.9), "drop"); box((xs[1] + 0.22, 1.15, 0.9), "square"); box((xs[1], 1.2, 1.28), "two")
    mirror((xs[2], 1.2, 0.9))
    return xs, lights, bands


def light_on(L, bm, t, e=1400):
    lightkey(L, f(t) - 1, L.data.energy); lightkey(L, f(t) + 4, e)
    matkey(bm, f(t) - 1); matkey(bm, f(t) + 4, strength=0.6 if e else 0.05)
    ev(t, "spot" if e else "spot_off")


def s05():
    t0, t1 = span("S05")
    xs, Ls, Bs = ped_set()
    for i, idn in enumerate(("05-02", "05-03", "05-04")):
        light_on(Ls[i], Bs[i], s(idn) + 0.2)
    mr = Maru((-3.6, -0.6, 0), 120, s=0.7, eye_glow=1.2)
    # 台の右横に立って見上げる（台の前に立つと、寄りのショットで台の物が隠れる）
    mr.walk(s("05-01"), s("05-02") + 0.3, (-3.6, -0.6, 0), (-1.6, -0.3, 0), face=-90)
    mr.at(s("05-02") + 0.6, face=-135, look=24)
    mr.walk(s("05-03") - 0.3, s("05-03") + 1.2, (-1.6, -0.3, 0), (0.7, -0.3, 0), face=-90)
    mr.at(s("05-03") + 1.4, face=-135, look=22)
    mr.walk(s("05-04") - 0.3, s("05-04") + 1.2, (0.7, -0.3, 0), (2.95, -0.25, 0), face=-90)
    mr.at(s("05-04") + 1.5, face=-140, look=16)
    tb = s("05-04b") + 0.4                                             # 鏡に映った自分にびっくり → 後ずさる
    mr.hop(tb, 0.25, 0.35); ev(tb, "pi"); mr.at(tb + 0.1, (2.95, -0.25, 0)); mr.at(tb + 0.7, (3.3, -0.9, 0))
    mr.at(s("05-05") + 1.5, (3.0, -0.45, 0), face=-140, look=10); mr.tilt(s("05-05") + 1.5, -10)   # そっとのぞく
    area((0, -4, 3), (0, 0.5, 1), 120, 4, "#A9C8FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("05-02"), (0.0, -6.4, 2.4), (0.0, 0.9, 1.0), (0.0, -6.0, 2.3), (0.0, 0.9, 1.0), 34),
        (s("05-02"), s("05-03"), (-2.0, -3.6, 1.6), (-2.3, 1.0, 1.2), (-2.1, -3.3, 1.6), (-2.3, 1.0, 1.25), 36),
        (s("05-03"), s("05-04"), (0.3, -3.6, 1.6), (0.0, 1.0, 1.2), (0.1, -3.3, 1.6), (0.0, 1.0, 1.25), 36),
        (s("05-04"), s("05-06"), (2.6, -3.8, 1.5), (2.3, 1.0, 1.25), (2.5, -3.4, 1.45), (2.3, 1.0, 1.25), 36),
        (s("05-06"), t1, (0.0, -6.4, 2.4), (0.0, 0.9, 1.0), (0.0, -6.8, 2.5), (0.0, 0.9, 1.0), 34)])
    return t0, t1


# ---------------- S06a スマホの下の小さな穴 → 画面に飛び込む
def s06a():
    t0, t1 = span("S06", b=s("06-04") + 0.5)   # 飛び込み（言い終えてから）が入るように、次の台詞の頭まで
    world("#0C1426", 0.15); ground("#E9E2D4", size=20)
    ph = phone((0, 0, 0.0), 0, screen=None, s=3.0)
    mr = Maru((-1.2, -2.0, 0), 30, eye_glow=1.4, s=0.5)
    mr.walk(s("06-01"), s("06-02") + 0.5, (-1.2, -2.0, 0), (-0.45, -1.45, 0), face=40)
    mr.at(s("06-02") + 1.0, look=-14); mr.at(s("06-02") + 2.5, face=70); mr.at(s("06-02") + 4.0, face=20)   # 穴をのぞき込む
    tj = s("06-03", 1) + 0.05                                          # 言い終えてから跳ぶ
    mr.at(tj - 0.3, face=0, look=0)
    mr.at(tj, (-0.3, -1.4, 0)); mr.at(tj + 0.5, (0.0, -0.2, 0.25)); mr.hop(tj, 0.9, 0.7); ev(tj, "jump")
    key(mr.root, "scale", f(tj + 0.45), (0.5,) * 3); key(mr.root, "scale", f(tj + 0.65), (0.01,) * 3)
    rip = add(bpy.ops.mesh.primitive_torus_add, mat("ripple", "#7FE6F2", emit=3.0), (0.0, -0.1, 0.13), (0, 0, 0), major_radius=0.3, minor_radius=0.01)
    key(rip, "scale", f(tj + 0.55), (0.01,) * 3); key(rip, "scale", f(tj + 1.1), (3.0,) * 3); show([rip], f(tj + 1.15), False); ev(tj + 0.55, "dive")
    area((-2, -3, 3), (-0.5, 0, 0), 300, 3, "#BFD9FF"); area((2, 2, 2), (0, 0, 0), 80, 2, "#7F9CFF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("06-02"), (1.6, -4.0, 2.2), (0.0, -0.6, 0.1), (1.2, -3.7, 1.9), (0.0, -0.8, 0.1), 34),
        (s("06-02"), tj - 0.3, (0.4, -3.1, 0.75), (-0.25, -1.15, 0.12), (0.3, -2.9, 0.7), (-0.25, -1.15, 0.12), 38),
        (tj - 0.3, t1, (0.3, -2.8, 2.6), (0.0, -0.4, 0.2), (0.2, -2.0, 2.3), (0.0, -0.2, 0.1), 34)])
    return t0, t1


# ---------------- S06b スマホの中の町に着地して、ぐるりと見渡す
def s06b():
    t0, t1 = span("S06", a=s("06-04") + 0.5)
    city_floor()
    mr = Maru((0, 0, 0), 0, eye_glow=1.3)
    key(mr.root, "location", f(t0), (0, 0, 2.5)); key(mr.root, "location", f(t0 + 0.5), (0, 0, 0)); ev(t0 + 0.5, "land")
    for k in range(4):
        mr.at(s("06-04") + 1.5 + 1.6 * k, face=-60 + 40 * k, look=10)
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF"); spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [(t0, t1, (0.5, -3.0, 1.0), (0.0, 0.0, 1.0), (-2.0, -5.0, 2.6), (0.0, 3.0, 1.6), 28)])
    return t0, t1


# ---------------- S10 出ていく荷物：光る道を箱が次々に。印の箱に寄る
def s10():
    t0, t1 = span("S10")
    city_floor()
    cube(mat("road", "#2CD3C2", rough=0.3, emit=1.2), (0, 3, 0.02), (1.0, 16, 0.03))
    cube(mat("exit", "#FFFFFF", emit=6.0), (0, 11.5, 1.2), (1.6, 0.05, 2.4))
    kinds = ["drop", "square", "two"]
    n, period, travel = 30, 2.0, 14.0
    for i in range(n):
        tb = t0 - travel + i * (t1 - t0 + travel) / n
        b = box((0, 0.4, 0.04), kinds[i % 3], s=1.2)          # v4「箱が箱を貫通」(6:56)：流れる箱は、説明の箱の後ろ（y≥0.4）から出る
        key(b, "location", f(tb), (0, 0.4, 0.04), "LINEAR"); key(b, "location", f(tb + travel * 0.75), (0, 11.0, 0.04), "LINEAR")
        key(b, "scale", f(tb), (0.001,) * 3); key(b, "scale", f(tb) + 6, (1.2,) * 3)
    # 説明する箱（3 つ）：道の手前で止まって見せる
    hero = {}
    for k, idn, x in (("drop", "10-05", -1.1), ("square", "10-06", 0.0), ("two", "10-07", 1.1)):
        b = box((x, -1.4, 0.04), k, s=1.5); hero[k] = b
        key(b, "scale", f(s(idn)) - 2, (1.5,) * 3); key(b, "scale", f(s(idn)) + 5, (1.9,) * 3); key(b, "scale", f(s(idn, 1)), (1.9,) * 3); key(b, "scale", f(s(idn, 1)) + 6, (1.5,) * 3)
    mr = Maru((-2.5, -1.9, 0), -40, eye_glow=1.2)                # v4「まるロボが箱に貫通」(7:10)：箱から離して立つ
    for k in range(6):
        mr.at(s("10-02") + 1.2 * k, face=-40 + (20 if k % 2 else -10), look=4)
    mr.at(s("10-05") - 0.3, face=-20, look=10)
    area((-2, -4, 3.5), (0, 1, 0.5), 300, 4, "#BFD9FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("10-04"), (-2.6, -4.6, 1.6), (0.2, 2.0, 0.5), (-2.3, -4.4, 1.5), (0.2, 2.5, 0.5), 30),
        (s("10-04"), s("10-05"), (0.0, -4.4, 1.2), (0.0, -1.4, 0.4), (0.0, -4.0, 1.1), (0.0, -1.4, 0.4), 34),
        (s("10-05"), s("10-06"), (-1.1, -3.8, 1.0), (-1.1, -1.4, 0.4), (-1.1, -3.6, 0.95), (-1.1, -1.4, 0.4), 36),
        (s("10-06"), s("10-07"), (0.0, -3.8, 1.0), (0.0, -1.4, 0.4), (0.0, -3.6, 0.95), (0.0, -1.4, 0.4), 36),
        (s("10-07"), s("10-08"), (1.1, -3.8, 1.0), (1.1, -1.4, 0.4), (1.1, -3.6, 0.95), (1.1, -1.4, 0.4), 36),
        (s("10-08"), t1, (-2.6, -4.6, 1.6), (0.2, 2.0, 0.5), (-2.9, -5.0, 1.8), (0.2, 3.0, 0.6), 30)])
    return t0, t1


# ---------------- S11 箱を追う：まるロボが走り、箱は電波に乗って町と山をこえる
def s11():
    t0, t1 = span("S11")
    world("#25325E", 0.7); ground("#22314F", size=200)
    # v4「背景もチープ」(7:51)：家の窓に明かり・家を増やす・木・星と月
    import random as _r; _r.seed(11)
    win = mat("townwin", "#FFD98A", emit=3.0); roofm = mat("townroof", "#5A4A7A", rough=0.6)
    for x, y, h in ((-6, 10, 1.2), (-3, 12, 2.0), (1, 9, 1.4), (5, 11, 2.4), (8, 13, 1.6), (-8.5, 14, 2.8), (-4.5, 16, 1.6), (3.5, 15, 3.2), (10.5, 9, 1.4), (-1.5, 15.5, 2.2), (6.5, 17, 1.8)):
        cube(mat("town", "#33456B", rough=0.6), (x, y, h / 2), (1.2, 1.2, h), bevel=0.05)
        cube(roofm, (x, y, h + 0.08), (1.3, 1.3, 0.16), bevel=0.04)
        for zz in [0.45 + 0.55 * k for k in range(int(h / 0.55))]:
            for xx in (-0.3, 0.3):
                if _r.random() < 0.7: cube(win, (x + xx, y - 0.61, zz), (0.22, 0.02, 0.22))
    for x, y in ((-7.5, 6), (-5, 7.5), (3, 6.5), (6.5, 7), (-1.8, 7.8), (9, 8.5)):
        cyl(mat("trunk", "#5B4636", rough=0.8), (x, y, 0.3), 0.08, 0.6)
        sphere(mat("leaf", "#2F6B5A", rough=0.7), (x, y, 0.85), 0.45, scale=(1, 1, 1.15))
    star = mat("star", "#FFFFFF", emit=6.0)
    for k in range(70):
        sphere(star, (_r.uniform(-40, 40), _r.uniform(55, 70), _r.uniform(8, 32)), _r.uniform(0.05, 0.12))
    sphere(mat("moon", "#FFF3C4", emit=4.0), (-14, 60, 24), 2.2)
    for x, y, r in ((-8, 30, 6), (0, 34, 9), (10, 30, 7)):
        add(bpy.ops.mesh.primitive_cone_add, mat("mtn", "#2E3F66", rough=0.8), (x, y, r * 0.5), radius1=r, radius2=0.0, depth=r, vertices=6)
    pts = [(-3, -1, 0.5), (-1, 4, 2.5), (1, 10, 4.2), (2, 18, 6.0), (3, 30, 9.5), (3.5, 45, 8.0)]
    road = mat("radio", "#2CD3C2", rough=0.3, emit=3.0)
    for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
        Ln = math.dist((x0, y0, z0), (x1, y1, z1))
        o = cyl(road, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), 0.05, Ln, verts=12)
        o.rotation_euler = Vector((x1 - x0, y1 - y0, z1 - z0)).to_track_quat('Z', 'Y').to_euler()
    for i, k in enumerate(("drop", "square", "two", "drop", "square")):
        b = box(pts[0], k, s=2.0)
        ta = t0 + i * 1.6
        for j, p in enumerate(pts):
            key(b, "location", f(ta + j * 2.2), (p[0], p[1], p[2] + 0.05), "LINEAR")
    mr = Maru((-4.0, -2.5, 0), -20, eye_glow=1.3)
    mr.walk(t0 + 0.3, s("11-02") + 1.0, (-4.0, -2.5, 0), (-3.9, 0.3, 0), face=-10, h=0.12, step=0.25)   # v4「箱を貫通」(7:51)：箱の通り道から離れて追う
    mr.at(s("11-02") + 1.5, look=28)
    sun((40, 0, 160), 3.0, "#C8D8FF"); area((-3, -5, 4), (0, 3, 2), 400, 5, "#BFD9FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [(t0, t1, (-5.5, -6.0, 1.6), (-1.0, 2.0, 1.5), (-4.0, -4.0, 2.4), (2.0, 20.0, 6.0), 26)])
    return t0, t1


# ---------------- S12 競り：ゆっくり → 本当の速さ（一瞬）
def s12():
    t0, t1 = span("S12")
    world("#2A1E3B", 0.3); ground("#3A2C50", rough=0.45)
    fr = mat("frame", "#FFD166", rough=0.3, metal=0.6, emit=0.4)
    cube(fr, (0, 3.2, 2.3), (2.6, 0.12, 1.7), bevel=0.04)
    blank = cube(mat("slot", "#FFFFFF", emit=1.2), (0, 3.12, 2.3), (2.3, 0.02, 1.4))
    ad = plane(img_mat("tent_slot", os.path.join(HERE, "tent.png"), emit=1.2), (0, 3.1, 2.3), (1.0, 1.4), rot=(R(90), 0, 0)); ad.scale = (2.3, 1.0, 1.0)
    cyl(mat("stand", "#5A4A73", rough=0.4), (0, 3.25, 0.7), 0.12, 1.4)
    random.seed(4)
    cols = ["#E5484D", "#3E7CB1", "#2BB3A6", "#F2A93B", "#8E6CEF", "#E86FA3", "#5DBB63", "#4C6EF5"]
    paddles = []
    for i in range(11):
        a = R(-70 + 140 * i / 10); x, y = 3.2 * math.sin(a), 3.2 - 3.2 * math.cos(a) * 0.95
        c = cols[i % 8]; e = empty((x, y, 0), math.atan2(x, -(y - 3.2)) + math.pi)
        cube(mat("rep" + c, c, rough=0.45, coat=0.3), (0, 0, 0.5), (0.42, 0.32, 1.0), bevel=0.12, parent=e)
        sphere(mat("rephead", "#F3E3D3", rough=0.5), (0, 0, 1.22), 0.2, parent=e)
        pe = empty((0.26, 0, 0.9)); pe.parent = e
        cyl(mat("stick", "#DDDDDD", rough=0.5), (0, 0, 0.3), 0.025, 0.6, parent=pe)
        cyl(mat("paddle" + c, "#FFFFFF", rough=0.4, emit=0.3), (0, -0.01, 0.67), 0.17, 0.03, rot=(R(90), 0, 0), parent=pe)
        cyl(mat("pdot" + c, c, rough=0.4, emit=1.0), (0, -0.03, 0.67), 0.08, 0.02, rot=(R(90), 0, 0), parent=pe)
        paddles.append((pe, i == 6))                                        # 6 番＝緑の服（テントの会社）
    hb = [box((x, 1.2, 0.0), k, s=1.0) for k, x in (("drop", -0.5), ("square", 0.0), ("two", 0.5))]

    def auction(ta, tb, tc, slow=True):
        """ta：ページが開く（箱が浮かぶ）、tb：札が上がる、tc：一番高い会社が決まり、枠に広告"""
        for b in hb:
            key(b, ("location", 2), f(ta), 0.0); key(b, ("location", 2), f(ta) + (12 if slow else 2), 0.5)
        for k, (pe, win) in enumerate(paddles):
            up = 0.9 + (0.75 if win else random.uniform(0.0, 0.45))
            d = random.uniform(0, 0.8) if slow else random.uniform(0, 0.05)
            key(pe, ("location", 2), f(tb + d), 0.9); key(pe, ("location", 2), f(tb + d) + (10 if slow else 1), up)
        show([ad], f(tc), True); show([blank], f(tc), False); ev(tc, "win")

    show([ad], 0, False); show([blank], 0, True)
    auction(s("12-04") + 0.8, s("12-05") + 0.5, s("12-06") + 1.0)
    # 本当の速さでもう一度（元に戻してから、0.1 秒ほどで終わる）
    tr = s("12-07", 1) + 0.15
    for b in hb: key(b, ("location", 2), f(tr - 0.3), 0.0)
    for pe, _ in paddles: key(pe, ("location", 2), f(tr - 0.3), 0.9, "CONSTANT")
    show([ad], f(tr - 0.3), False); show([blank], f(tr - 0.3), True)
    auction(tr, tr + 0.04, tr + 0.1, slow=False); ev(tr, "whoosh")
    mr = Maru((-2.9, -1.6, 0), -140, eye_glow=1.2, look_up=14)
    mr.at(s("12-03"), face=-150, look=18)
    for k in range(3): mr.at(s("12-05") + 1.5 * k, face=-170 + 15 * k, look=20)
    mr.blink(s("12-10") - 0.2); mr.blink(s("12-10") + 0.4)
    spot((0, 0.5, 6), (0, 2.6, 1.2), 1600, 60, "#FFE9C7"); area((-3, -4, 3), (0, 2, 1), 300, 4, "#C8B8FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("12-04"), (-0.6, -5.6, 2.4), (0.0, 2.0, 1.25), (-0.4, -5.2, 2.3), (0.0, 2.2, 1.4), 30),
        (s("12-04"), s("12-06"), (0.0, -3.0, 1.4), (0.0, 1.6, 1.0), (0.4, -2.6, 1.5), (0.0, 1.8, 1.2), 30),
        (s("12-06"), s("12-07", 1) - 0.2, (0.0, -1.6, 2.2), (0.0, 3.1, 2.3), (0.0, -1.2, 2.25), (0.0, 3.1, 2.3), 32),
        (s("12-07", 1) - 0.2, t1, (-0.6, -5.6, 2.4), (0.0, 2.0, 1.25), (-0.8, -5.8, 2.4), (-0.4, 1.6, 1.1), 30)])
    return t0, t1


# ---------------- S13〜S15 電車（ふり返り）
def train_set(maru_kw=None):
    _m = globals()["maru"]; globals()["maru"] = lambda *a, **k: empty()
    s5_train(); globals()["maru"] = _m
    train_windows()
    cube(mat("wifi_box", "#F4F4F4", rough=0.4), (0, 0.6, 2.45), (0.5, 0.3, 0.1), bevel=0.03)
    led = mat("wifi_led", "#2BB3A6", emit=3.0); sphere(led, (0, 0.44, 2.43), 0.025)
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    return Maru(**(maru_kw or dict(loc=(0.0, 1.05, 0.5), face=0, s=0.55, hat=False, eye_glow=0.9))), led


def s13():
    t0, t1 = span("S13")
    mr, led = train_set()
    mr.at(s("13-03"), face=-40)
    mr.glow(s("13-04") + 0.2, 0.3, 6.0); ev(s("13-04") + 0.2, "pipo")
    for k in range(8):
        matkey(led, f(s("13-05")) + 12 * k, strength=3.0 if k % 2 else 0.5)
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        # v4「『ここで』のときに今の絵にして、それまではアップめで」(9:13)
        (t0, s("13-02"), (0.15, -0.35, 1.0), (0.0, 1.05, 0.95), (0.1, -0.2, 0.98), (0.0, 1.05, 0.95), 30),        # まるロボのアップ
        (s("13-02"), s("13-03"), (0.15, -1.45, 1.15), (0.0, 1.0, 1.55), (0.0, -1.45, 1.12), (0.0, 1.0, 1.5), 12),  # 冒頭と同じ絵

        (s("13-03"), s("13-05"), (0.7, -0.4, 1.5), (0.9, 0.85, 0.95), (0.75, -0.2, 1.4), (0.9, 0.85, 0.95), 30),      # ソラさんのスマホ
        (s("13-05"), t1, (0.3, -1.4, 1.5), (0.3, 1.0, 1.55), (0.2, -1.45, 1.55), (0.2, 1.0, 1.7), 22)])               # 天井の Wi-Fi と二人
    return t0, t1


def s14():
    t0, t1 = span("S14")
    mr, led = train_set(dict(loc=(-3.0, 1.05, 0.5), face=0, s=0.55, hat=False, eye_glow=1.2))
    for k in range(3): mr.hop(s("14-01") + 0.2 + 0.45 * k, 0.15, 0.35)
    mr.at(s("14-01b") - 0.2, face=170, look=12)                        # 窓の外を見つめる
    mr.glow(s("14-04") + 0.5, 0.3, 6.0); ev(s("14-04") + 0.5, "pipo")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("14-01b"), (-2.6, -0.9, 1.1), (-3.0, 1.0, 0.9), (-2.7, -0.7, 1.1), (-3.0, 1.0, 0.9), 30),
        (s("14-01b"), s("14-02"), (-2.4, -0.2, 1.5), (-3.6, 1.5, 1.55), (-2.8, 0.2, 1.5), (-3.6, 1.5, 1.6), 28),    # 窓の紅葉
        (s("14-02"), t1, (-1.6, -0.9, 1.25), (-3.3, 1.4, 1.4), (-1.4, -0.9, 1.25), (-3.3, 1.4, 1.4), 26)])
    return t0, t1


def s15():
    t0, t1 = span("S15")
    mr, led = train_set()
    mr.at(s("15-03"), look=4); mr.tilt(s("15-03") + 0.3, 14)          # 首をかしげて思い出そうとする
    mr.tilt(s("15-05") - 0.2, 0)
    posters = [m for m in bpy.data.materials if m.name.startswith("tentposter")]
    for k, x in enumerate((-2.8, 0.0, 2.8)):
        mr.at(s("15-05") + 1.4 * k, face=-30 + 30 * k)
    for m in posters:
        matkey(m, f(s("15-05")) - 2, strength=0.6); matkey(m, f(s("15-05")) + 6, strength=2.0)
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("15-05") - 0.3, (0.0, -1.45, 1.2), (0.0, 1.0, 1.15), (0.0, -1.45, 1.2), (0.0, 1.0, 1.25), 24),        # 広告が見えない角度
        (s("15-05") - 0.3, t1, (0.0, -1.45, 1.1), (0.0, 0.8, 1.9), (0.0, -1.45, 1.1), (0.0, 0.8, 1.85), 11)])
    return t0, t1


# ---------------- S16 紫の舞台：鏡に残るのはテントの 1 枚、外れは灰色の山
def s16():
    t0, t1 = span("S16")
    world("#1E1433", 0.3); ground("#2B1F45", rough=0.5)
    mirror((0, 1.0, 0), s=2.6)
    spot((0, -1, 5), (0, 1, 1.4), 1500, 35, "#E8DDFF")
    random.seed(5)
    cols = ["#F6B8C8", "#9BC4E2", "#C9E4B4", "#FFE3A3", "#E86FA3", "#8E6CEF"]
    heap = 0
    tA = s("16-03")                                                     # テントのカードだけ鏡に残る
    for i in range(40):
        tc = t0 + 0.5 + i * (t1 - t0 - 3) / 40
        tent = abs(tc - tA) < 0.6 and heap >= 0 and "tent" not in [o.name for o in bpy.data.objects]
        m = mat("card_c%d" % i, "#FFE07A" if tent else cols[i % 6], rough=0.5, emit=2.0 if tent else 0.6)
        c = cube(m, (-4.0, 0.6, 1.4), (0.5, 0.02, 0.32))
        key(c, "location", f(tc), (-4.0, 0.6, 1.4 + random.uniform(-0.3, 0.3)), "LINEAR")
        key(c, "location", f(tc + 1.4), (0.0, 0.9, 1.43), "LINEAR")      # 鏡の前
        if tent:
            c.name = "tent"; key(c, "location", f(tc + 1.6), (0.0, 0.95, 1.43)); continue
        matkey(m, f(tc + 1.4), strength=0.6, color=cols[i % 6]); matkey(m, f(tc + 1.8), strength=0.0, color="#6D6880")
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb(cols[i % 6])
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].keyframe_insert("default_value", frame=f(tc + 1.4))
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb("#6D6880")
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].keyframe_insert("default_value", frame=f(tc + 1.8))
        x, y = 2.4 + random.uniform(-0.6, 0.6), 1.2 + random.uniform(-0.5, 0.5)
        key(c, "location", f(tc + 2.6), (x, y, 0.03 + heap * 0.02))      # 外れの山へ
        key(c, ("rotation_euler", 0), f(tc + 1.8), 0.0); key(c, ("rotation_euler", 0), f(tc + 2.6), R(90))
        heap += 1
    mr = Maru((-1.0, -0.6, 0), 20, eye_glow=1.2, look_up=22)
    for k in range(10): mr.at(t0 + 1 + k * 4.5, face=10 + (20 if k % 2 else -20))
    area((-3, -4, 3), (0, 1, 1), 250, 4, "#C8B8FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [(t0, t1, (0.0, -6.2, 2.0), (0.4, 1.0, 1.3), (0.6, -5.6, 2.2), (0.8, 1.0, 1.2), 32)])
    return t0, t1


# ---------------- S17・S18 新たな容疑者：ヘッドホンの会社の人 → ヘッドホンはぽろり
def s17():
    t0, t1 = span("S17")
    world("#120D1C", 0.2); ground("#2A2238", rough=0.5)
    pd = cyl(mat("ped2", "#E8EEF1", rough=0.35, coat=0.3), (0, 1.2, 0.3), 0.8, 0.6)
    e, _, _ = made(salesman, (0, 1.2, 0.6))
    tr = s("17-01")
    key(e, ("location", 2), f(tr), -2.0); key(e, ("location", 2), f(tr + 1.5), 0.0); ev(tr, "rise")
    key(pd, ("location", 2), f(tr), -1.7); key(pd, ("location", 2), f(tr + 1.5), 0.3)
    L = spot((0, -0.5, 5.5), (0, 1.2, 1.4), 0, 28, "#FFE9C7"); lightkey(L, f(tr + 1.2), 0); lightkey(L, f(tr + 1.6), 2200)
    mr = Maru((-1.5, -0.6, 0), 25, eye_glow=1.6, look_up=10)
    mr.hop(tr + 1.6, 0.25, 0.35); ev(tr + 1.6, "pi"); mr.tilt(tr + 1.9, -10)
    area((-3, -4, 3), (0, 1, 1), 150, 4, "#C8B8FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [(t0, t1, (-0.6, -5.8, 1.8), (-0.2, 1.0, 1.2), (-0.5, -5.2, 1.7), (-0.2, 1.0, 1.4), 34)])
    return t0, t1


def s18():
    t0, t1 = span("S18")
    world("#120D1C", 0.2); ground("#2A2238", rough=0.5)
    cyl(mat("ped2", "#E8EEF1", rough=0.35, coat=0.3), (0, 1.2, 0.3), 0.8, 0.6)
    e1, _, objs1 = made(salesman, (0, 1.2, 0.6), headphones=True, list_behind=True)
    hp = [o for o in objs1 if o.data and o.active_material and o.active_material.name == "sm_hp"]
    tf = s("18-02") + 0.6                                                # ヘッドホンがぽろり（中は何もつながっていない）
    for o in hp:
        z0 = o.location.z
        key(o, ("location", 2), f(tf), z0); key(o, ("location", 2), f(tf + 0.5), z0 - 1.35); key(o, ("location", 1), f(tf + 0.5), o.location.y - 0.4)
    ev(tf + 0.5, "clatter")
    spot((0, -0.5, 5.5), (0, 1.2, 1.4), 2200, 28, "#FFE9C7")
    mr = Maru((-1.3, -0.6, 0), 25, eye_glow=1.1, look_up=10)
    mr.tilt(tf + 0.6, 18, 0.25); mr.at(tf + 0.6, (-1.1, -0.4, 0)); mr.tilt(tf + 1.6, 0, 0.4)   # ずっこける
    area((-3, -4, 3), (0, 1, 1), 150, 4, "#C8B8FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("18-03"), (-0.6, -5.4, 1.7), (-0.2, 1.0, 1.3), (-0.5, -5.0, 1.7), (-0.2, 1.0, 1.2), 34),
        (s("18-03"), t1, (1.4, -5.0, 1.8), (0.1, 1.0, 1.0), (1.6, -4.4, 1.7), (0.2, 1.0, 1.0), 34)])      # 背中の名簿が見える
    return t0, t1


# ---------------- S19 3人の容疑者に戻る：①は消え、②③が強く光る
def s19():
    t0, t1 = span("S19")
    xs, Ls, Bs = ped_set(lit0=(1, 1, 1))
    for L in Ls: lightkey(L, 0, 1400)
    light_on(Ls[0], Bs[0], s("19-03") + 1.0, 0)
    light_on(Ls[1], Bs[1], s("19-04") + 0.8, 2400)
    light_on(Ls[2], Bs[2], s("19-06") + 0.8, 2400)
    mr = Maru((-1.15, -1.0, 0), 200, s=0.75, eye_glow=1.4)
    mr.walk(s("19-06") - 0.5, s("19-06") + 1.5, (-1.15, -1.0, 0), (2.0, -0.4, 0), face=180)   # 鏡に映る
    mr.walk(s("19-07") - 0.6, s("19-07") + 0.6, (2.0, -0.4, 0), (0.0, -1.2, 0), face=0)
    mr.at(s("19-07") + 1.0, look=-12); mr.glow(s("19-07") + 1.0, 0.3, 6.0)   # つばを上げるように上を向く
    area((0, -4, 3), (0, 0.5, 1), 120, 4, "#A9C8FF")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("19-06"), (0.4, -5.8, 2.3), (0.1, 0.8, 1.0), (0.3, -5.4, 2.2), (0.1, 0.8, 1.0), 33),
        (s("19-06"), s("19-07"), (2.8, -3.0, 1.4), (2.3, 1.2, 1.4), (2.6, -2.8, 1.4), (2.3, 1.2, 1.4), 38),       # 鏡にまるロボ
        (s("19-07"), t1, (0.0, -6.6, 2.5), (0.0, 0.8, 1.0), (0.0, -7.2, 2.7), (0.0, 0.8, 1.0), 33)])
    return t0, t1


# ---------------- S21 その夜：こそこそ近づいて「ピポ、ピポ」→ 何も起きない → 丸くなる
def s21():
    t0, t1 = span("S21")
    room(night=True); person_lie((0.15, -0.15, 0.42))
    phone((0.35, -0.9, 0.0), 10, screen=None)
    mr = Maru((-1.2, -1.9, 0), 40, s=0.42, hat=True, eye_glow=1.1)
    for k in range(3): mr.at(s("21-01") + 3.0 + 0.5 * k, face=40 + (40 if k % 2 == 0 else -40))   # 辺りを見回す
    mr.walk(s("21-01b") - 0.2, s("21-01b") + 3.0, (-1.2, -1.9, 0), (0.3, -1.55, 0), face=160, h=0.03, step=0.45)  # そろりそろり
    mr.at(s("21-02") - 0.3, look=-18)
    bb = bubble((0.3, -1.6, 0.66), 0.11, "icon_tent.png")   # まるロボの頭の上（字のない絵の吹き出し）
    key(bb, "scale", f(s("21-02")) - 1, (0.001,) * 3)
    for k in range(2):
        tp = s("21-02") + 0.1 + 0.7 * k; ev(tp, "pipo"); mr.hop(tp, 0.06, 0.25); mr.glow(tp, 0.3, 5.0, 0.15); mr.glow(tp + 0.3, 5.0, 0.3, 0.15)
    key(bb, "scale", f(s("21-02")) + 4, (1.0,) * 3); key(bb, "scale", f(s("21-03", 1)), (1.0,) * 3); key(bb, "scale", f(s("21-03", 1)) + 5, (0.001,) * 3)
    tc = s("21-04") + 2.5                                                # 安心して、スマホの横で丸くなる
    key(mr.body, ("location", 2), f(tc), mr.z0); key(mr.body, ("location", 2), f(tc + 1.0), mr.z0 - 0.08)
    matkey(mr.lens, f(tc), strength=1.1); matkey(mr.lens, f(tc + 1.5), strength=0.15)
    area((-3, 2, 3), (0, 0, 0), 120, 2, "#7F9CFF"); area((2, -3, 2.5), (0, -1, 0.3), 40, 2, "#FFE2B8")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("21-02") - 0.5, (0.6, -4.0, 1.6), (-0.4, -1.4, 0.3), (0.8, -3.6, 1.4), (-0.1, -1.4, 0.3), 34),
        (s("21-02") - 0.5, t1, (1.7, -3.6, 1.2), (0.3, -1.3, 0.35), (1.6, -3.4, 1.15), (0.3, -1.3, 0.35), 38)])
    return t0, t1


# ---------------- S22 次の朝：ひっくり返ったまるロボ → テントの広告 → 帽子を下げて目をかくす
def s22():
    t0, t1 = span("S22")
    room(night=False)
    ph = phone((0.35, -0.9, 0.0), 10, screen=None)
    phone_screen(ph, "phone_ad.png", 1.6)
    mr = Maru((-0.2, -1.2, 0.56), -200, s=0.45, hat=True, eye_glow=1.6)
    mr.root.rotation_euler = (R(165), 0, R(-160)); mr.root.keyframe_insert("rotation_euler", frame=0)
    tu = s("22-04") - 0.4                                                # 起き上がる
    key(mr.root, "rotation_euler", f(tu), (R(165), 0, R(-160))); key(mr.root, "rotation_euler", f(tu + 0.6), (0, 0, R(30)))
    key(mr.root, "location", f(tu), (-0.2, -1.2, 0.56)); key(mr.root, "location", f(tu + 0.6), (-0.2, -1.2, 0.0)); ev(tu + 0.6, "land")
    mr.at(s("22-05") - 0.2, look=-25)                                    # 帽子を下げて目をかくす
    matkey(mr.lens, f(s("22-05")), strength=1.6); matkey(mr.lens, f(s("22-05") + 0.6), strength=0.3)
    sun((50, 0, 200), 2.0); area((0, -3, 2.5), (0, -1, 0.3), 300, 3, "#FFF1DD")
    cam, tgt = cam_rig()
    shots(cam, tgt, [
        (t0, s("22-02c") - 0.2, (0.3, -3.0, 1.2), (0.05, -1.0, 0.3), (0.3, -2.7, 1.1), (0.0, -1.05, 0.3), 38),
        (s("22-02c") - 0.2, s("22-03"), (0.45, -1.5, 1.2), (0.36, -0.9, 0.02), (0.45, -1.4, 1.15), (0.36, -0.9, 0.02), 36),   # 画面のテントの広告
        (s("22-03"), t1, (0.3, -3.0, 1.2), (0.05, -1.0, 0.3), (0.2, -2.6, 1.0), (-0.1, -1.1, 0.3), 38)])
    return t0, t1


SC = dict(s00=s00, s01=s01, s02=s02, s04=s04, s05=s05, s06a=s06a, s06b=s06b, s10=s10, s11=s11, s12=s12,
          s13=s13, s14=s14, s15=s15, s16=s16, s17=s17, s18=s18, s19=s19, s21=s21, s22=s22)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
t0, t1 = SC[KEY]()
sc.frame_start = FR[0] if FR[1] else 0
sc.frame_end = FR[1] if FR[1] else f(t1) - 1
sc.frame_step = STEP
sc.render.fps = FPS
sc.render.engine = 'CYCLES'
sc.cycles.samples = N_SAMPLES
sc.cycles.use_denoising = True
sc.cycles.device = 'CPU'
sc.render.use_persistent_data = True
if "--fast" in ARGS:  # 光の跳ね返りを減らす。見た目はほぼ同じで 1.5〜2 倍速い（2026-11-14 ユーザー「速くするやり方ないの」→ 本番の PC でも使う）
    c = sc.cycles
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = 3, 1, 1, 2, 4
    c.caustics_reflective = c.caustics_refractive = False
    c.use_adaptive_sampling = True
sc.render.resolution_x, sc.render.resolution_y = RESX, RESY
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Punchy'
sc.render.filepath = os.path.join(OUTDIR, KEY + "_")
exec(open(os.path.join(_ANIM_HERE, "pc_out.py"), encoding="utf-8").read())  # PC：--gpu・--video
os.makedirs(OUTDIR, exist_ok=True)
json.dump(dict(mode=KEY, t0=t0, t1=t1, fps=FPS, frames=sc.frame_end + 1, steps=sorted(STEPS), events=sorted(EVENTS)),
          open(os.path.join(OUTDIR, KEY + "_log.json"), "w"), ensure_ascii=False)
print("FRAMES", KEY, sc.frame_start, sc.frame_end, "T0 %.2f T1 %.2f" % (t0, t1))
if "--blend" in ARGS:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, KEY + ".blend"))
else:
    bpy.ops.render.render(animation=True)
