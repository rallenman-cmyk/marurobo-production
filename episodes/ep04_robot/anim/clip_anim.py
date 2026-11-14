# ロボットではありません回：3D のクリップ（clips.py の一覧）を、声の時刻に合わせて動かして描く
# blender -b --factory-startup --python clip_anim.py -- <クリップ名> <clips.json> <出力フォルダ> [samples] [--res W H] [--step N] --tex <絵> [--scr <画面のコマ>] [--track-only]
#   どのクリップも：絵コンテの場面（board.py の b..）をそのまま組み、まるロボに「生きている小さな動き」（息・まばたき・見回し）を付ける
#   クリップごとの動き（ACT）：台本の「ロボ」の欄の動き（跳ねる・うろうろ・足あとが浮かぶ・マスに跳び乗る など）
#   S04 は scenes.py（まるロボが押す）で描く
# 決まり：カメラは絵コンテと同じ所に止める（2D の札の場所がずれない）。3D の中に字を書かない
import os, sys, json, math, random
ARGS = sys.argv[sys.argv.index("--") + 1:]
_ANIM_HERE = os.path.dirname(os.path.abspath(__file__))
def opt(name, default):
    return [type(d)(ARGS[ARGS.index(name) + 1 + k]) for k, d in enumerate(default)] if name in ARGS else default
TEX, = opt("--tex", [os.path.join(_ANIM_HERE, "..", "storyboard", "tex")])
SCR, = opt("--scr", [""])
NAME, CLIPS, OUTDIR = ARGS[0], ARGS[1], ARGS[2]
N_SAMPLES = int(ARGS[3]) if len(ARGS) > 3 and ARGS[3].isdigit() else 32
RESX, RESY = opt("--res", [1920, 1080])
STEP, = opt("--step", [1])
TRACK_ONLY = "--track-only" in ARGS
exec(open(os.path.join(_ANIM_HERE, "common.py"), encoding="utf-8").read())
CLIP = [c for c in json.load(open(CLIPS, encoding="utf-8")) if c["name"] == NAME][0]
MERGE = {"c_s23a": "c_s23b"}            # s23a〜s23b（ふらふらの 4 枚）は、b23 の 1 つの場面で続けて動かす
if NAME in MERGE:
    last = [c for c in json.load(open(CLIPS, encoding="utf-8")) if c["name"] == MERGE[NAME]][0]
    CLIP["t1"] = last["t1"]
T0, T1 = CLIP["t0"], CLIP["t1"]
CLOCK["T0"] = T0


def objs(prefix):
    return [o for o in bpy.data.objects if o.type == 'MESH' and o.active_material and o.active_material.name.startswith(prefix)]


def find_maru():
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and o.children and any(c.type == 'EMPTY' and any(g.type == 'MESH' and g.active_material and g.active_material.name.startswith("maru_white") for g in c.children) for c in o.children):
            return o


def find_mouse():
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and any(c.type == 'MESH' and c.active_material and c.active_material.name.startswith("mouse") for c in o.children):
            return o


def find_screen():
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.active_material and o.active_material.name.startswith("scr_"): return o


def vis(obs, t, on):
    for o in obs:
        o.hide_render = not on; o.keyframe_insert("hide_render", frame=f(t)); _interp(o, f(t), "CONSTANT")


def appear(obs, t0, t1):
    """物を、t0 から t1 のあいだに 1 つずつ出す（並び順に）"""
    for o in obs: vis([o], T0 - 1, False)
    for i, o in enumerate(obs): vis([o], t0 + (t1 - t0) * i / max(1, len(obs) - 1), True)


def screen_tex(times):
    """画面の絵を時刻で替える：[(時刻, 絵の名前)]。同じ板を重ねて、見える板を切り替える"""
    scr = find_screen(); planes = [(None, scr)]
    scr.data.materials.clear(); scr.data.materials.append(img(times[0][1], 1.8))     # 最初の絵（絵コンテの場面の絵とちがうことがある）
    for t, name in times[1:]:
        o = scr.copy(); o.data = scr.data.copy(); bpy.context.collection.objects.link(o)
        o.data.materials.clear(); o.data.materials.append(img(name, 1.8)); planes.append((t, o))
    for i, (t, o) in enumerate(planes):
        nxt = planes[i + 1][0] if i + 1 < len(planes) else None
        vis([o], T0 - 1, i == 0)
        if t is not None: vis([o], t, True)
        if nxt is not None: vis([o], nxt, False)


def idle(mr, a=None, b=None, still=()):
    """生きている小さな動き：息（ゆっくり上下）・まばたき・少し見回す。still＝止めておく時間 [(t0, t1)]"""
    a = T0 if a is None else a; b = T1 if b is None else b
    rnd = random.Random(int(T0 * 10))
    def free(t): return all(not (s0 - 0.3 <= t <= s1 + 0.3) for s0, s1 in still) and t < b - 0.2
    t = a + 0.6
    while t < b - 0.6:
        if free(t) and free(t + 0.9):
            key(mr.body, ("location", 2), f(t), mr.z0); key(mr.body, ("location", 2), f(t + 0.45), mr.z0 + 0.025); key(mr.body, ("location", 2), f(t + 0.9), mr.z0)
        t += 1.8
    t = a + rnd.uniform(1.0, 2.0)
    while t < b - 0.5:
        if free(t): mr.blink(t, mr.g0, 0.22)
        t += rnd.uniform(2.6, 4.2)


class M(Maru):
    def __init__(self, root):
        super().__init__(root)
        b = self.lens.node_tree.nodes["Principled BSDF"]
        self.g0 = b.inputs["Emission Strength"].default_value
        self.loc0 = tuple(root.location); self.face0 = math.degrees(root.rotation_euler[2]); self.look0 = -math.degrees(self.body.rotation_euler[0])
        self.at(T0, self.loc0, self.face0, self.look0)

    def walk(self, t0, t1, b, face=None, h=0.05, step=0.3):
        if face is not None: self.at(t0, face=face)
        a = self._last.get("loc", (t0, self.loc0))[1]
        self.at(t0, a); self.at(t1, b, interp="LINEAR", hold=False)
        n = max(1, int((t1 - t0) / step))
        for k in range(n):
            self.hop(t0 + k * (t1 - t0) / n, h, (t1 - t0) / n); STEPS.append(round(t0 + (k + 1) * (t1 - t0) / n, 3))

    def jump_to(self, t, b, d=0.5, h=0.6):
        a = self._last.get("loc", (t, self.loc0))[1]
        self.at(t, a); self.at(t + d, b, interp="LINEAR", hold=False)
        self.hop(t, h, d); ev(t, "jump"); ev(t + d, "land")


# ---------------- クリップごとの動き
def a_s01(mr, ms):                    # 夜の買い物：マウスを少し押して、テントを見てうれしそうに跳ねる
    idle(mr, still=[(s("01-02") + 1.0, s("01-02") + 2.2), (s("01-03"), T1)])
    mr.hop(s("01-02") + 1.2, 0.25, 0.35); mr.hop(s("01-02") + 1.65, 0.25, 0.35); ev(s("01-02") + 1.55, "step"); ev(s("01-02") + 2.0, "step")
    m0 = tuple(ms.location); m1 = (m0[0] + 0.06, m0[1] - 0.08, m0[2])
    r0 = mr.loc0; r1 = (r0[0] + 0.06, r0[1] - 0.08, r0[2])
    key(ms, "location", f(s("01-03") + 0.3), m0); key(ms, "location", f(s("01-03") + 1.5), m1)
    mr.at(s("01-03") + 0.3, r0); mr.at(s("01-03") + 1.5, r1)


def a_s02a(mr, ms):                   # チェック欄がぽん → ぴたりと止まって、目がちかちか
    screen_tex([(T0, "scr_shop"), (s("02-01") + 1.2, "scr_check")]); ev(s("02-01") + 1.2, "pop_ui")
    idle(mr, still=[(s("02-01") + 1.0, s("02-02") + 1.5)])
    for k in range(4): mr.blink(s("02-01") + 1.6 + k * 0.3, mr.g0 * 1.6, 0.2)
    mr.at(s("02-03") + 0.4, look=12); mr.tilt(s("02-04") + 0.6, 12, 0.4)


def a_s03(mr, ms):                    # 欄の前で、右へ左へうろうろ
    x0 = mr.loc0
    idle(mr, still=[(s("03-02"), s("03-04") + 2)])
    mr.walk(s("03-02") + 0.2, s("03-02") + 1.6, (x0[0] + 0.25, x0[1], x0[2]), face=-40)
    mr.walk(s("03-02") + 2.0, s("03-02") + 3.6, (x0[0] - 0.2, x0[1], x0[2]), face=30)
    mr.walk(s("03-04") + 0.3, s("03-04") + 1.6, x0, face=-5)


def a_s05x(mr, ms):                   # 私が押す：まるロボは机の端で見守る。マウスがひとりでに、ふらつきながら
    from mathutils import Vector
    m0 = (0.95, 0.15, 0.75); ms.location = m0
    mr.at(T0, (1.22, 0.5, 0.75), -60, 6)
    seq_screen(find_screen(), SCR, "s05")
    m_0, m_1 = said("今度は") + 0.4, said("……カチッ") - 0.35
    pa = (m_0 + (m_1 - m_0) * 0.55, m_0 + (m_1 - m_0) * 0.55 + 0.5); mv = (m_1 - m_0) - 0.5
    for k in range(0, 31):
        u = k / 30; tt = m_0 + u * mv; tt += 0.5 if tt > pa[0] else 0
        x = 0.95 - 0.24 * u + 0.022 * math.sin(u * 9.0) * (1 - u); y = 0.15 + 0.11 * u + 0.016 * math.sin(u * 6.0) * (1 - u)
        key(ms, "location", f(tt), (x, y, 0.75), "LINEAR")
    key(ms, "location", f(pa[0]), ms.location.copy(), "CONSTANT")
    idle(mr, still=[(m_0 - 0.5, T1)])
    mr.at(m_0 - 0.3, look=6); mr.at(m_0 + 0.6, look=16)                 # 首を前に伸ばして、のぞきこむ
    key(mr.body, ("location", 1), f(m_0 + 0.1), mr.body.location.y); key(mr.body, ("location", 1), f(m_0 + 0.6), mr.body.location.y - 0.15)


def a_s05b(mr, ms):                   # 緑の印で、目を大きく開く → 跳ねる
    idle(mr, still=[(T0, T0 + 1.6)])
    mr.glow(T0 + 0.2, mr.g0, mr.g0 * 2.2, 0.15); mr.glow(T0 + 1.5, mr.g0 * 2.2, mr.g0, 0.5)
    mr.hop(T0 + 0.3, 0.35, 0.4); ev(T0 + 0.7, "land")


def a_s06b(mr, ms):                   # 左右を見て、首をかしげる
    idle(mr, still=[(T0 + 1, T0 + 5)])
    mr.at(T0 + 1.0, face=mr.face0 - 30); mr.at(T0 + 2.2, face=mr.face0 + 30); mr.at(T0 + 3.4, face=mr.face0); mr.tilt(T0 + 3.8, 14, 0.4)


def a_s08(mr, ms):                    # 新聞の山を見上げて、ゆっくり見回す
    idle(mr, still=[(T0 + 0.5, T1)])
    mr.at(T0 + 0.5, face=mr.face0); mr.at(T1 - 0.5, face=mr.face0 + 70, hold=False)
    mr.at(T0 + 1.0, look=mr.look0); mr.at(T0 + 3.0, look=mr.look0 + 8)


def a_s11(mr, ms):                    # ぽかんと目を丸くする
    idle(mr); mr.glow(T0 + 0.8, mr.g0, mr.g0 * 1.8, 0.3); mr.at(T0 + 0.8, look=mr.look0 + 6)


def a_s12a(mr, ms):                   # 画面の中へ：上から降りてきて着地 → ぐるりと見渡す → 門番を見上げる
    l0 = mr.loc0
    key(mr.root, "location", f(T0), (l0[0], l0[1], l0[2] + 3.0)); key(mr.root, "location", f(T0 + 0.7), l0, "BEZIER")
    mr._last["loc"] = (T0 + 0.7, l0); ev(T0 + 0.7, "land"); ev(T0 + 0.05, "dive")
    idle(mr, a=T0 + 1.0, still=[(s("12-01b"), s("12-01b") + 3.2)])
    mr.at(s("12-01b"), face=mr.face0 + 50); mr.at(s("12-01b") + 1.5, face=mr.face0 - 50); mr.at(s("12-01b") + 3.0, face=mr.face0)
    mr.at(said("門番です") - 0.4, face=mr.face0 + 25, look=18)


def a_s13a(mr, ms):
    idle(mr); mr.at(T0 + 1.0, look=mr.look0 + 5)


def a_s13b(mr, ms):                   # 私の足あと（オレンジ）が、くねくね浮かび上がる。まるロボはたどって見る
    appear(objs("fp_h"), T0 + 0.3, T0 + 4.5); idle(mr)
    mr.at(T0 + 0.5, face=mr.face0 + 30); mr.at(T0 + 4.0, face=mr.face0 - 10)


def a_s13d(mr, ms):                   # まるロボの足あと（青緑）が、まっすぐ浮かぶ → 見下ろして固まる
    appear(objs("fp_r"), T0 + 0.4, T0 + 2.2); ev(T0 + 0.4, "pop_ui")
    idle(mr, still=[(T0 + 2.0, T0 + 6.0)])
    mr.at(T0 + 2.0, look=mr.look0 - 10); mr.glow(T0 + 2.3, mr.g0, mr.g0 * 0.4, 0.4); mr.glow(T0 + 6.0, mr.g0 * 0.4, mr.g0, 0.5)


def a_s14(mr, ms):                    # 足あとの横で、しょんぼり沈む
    idle(mr, still=[(T0 + 1.5, T0 + 4)])
    key(mr.body, ("location", 2), f(T0 + 1.5), mr.z0); key(mr.body, ("location", 2), f(T0 + 2.5), mr.z0 - 0.1)
    mr.z0 -= 0.1; mr.glow(T0 + 1.6, mr.g0, mr.g0 * 0.5, 0.6); ev(T0 + 1.6, "down")


def a_s15(mr, ms):                    # 記録帳を下からのぞきこむ（つま先立ちで小さく跳ねる）
    idle(mr, still=[(T0 + 1, T0 + 2.5)]); mr.hop(T0 + 1.2, 0.15, 0.35); mr.hop(T0 + 1.7, 0.15, 0.35)


def a_s16(mr, ms):                    # 目盛りが上がり下がり → 首を上下させて見る
    fill = objs("meter_fill")
    idle(mr, still=[(T0, T1)])
    for o in fill:
        h0 = o.scale.z; z0 = o.location.z; base = z0 - o.dimensions.z / 2
        for t, k in ((T0, 0.2), (s("16-02") if "16-02" in T else T0 + 6, 1.6), (s("16-03"), 0.9), (s("16-03") + 3, 0.9), (T1, 1.0)):
            key(o, ("scale", 2), f(t), h0 * k); key(o, ("location", 2), f(t), base + (z0 - base) * k)
    for t, lk in ((T0 + 1, mr.look0 - 5), ((s("16-02") if "16-02" in T else T0 + 6) + 0.3, mr.look0 + 12), (s("16-03") + 0.3, mr.look0), (s("16-03") + 1.5, mr.look0 + 4)):
        mr.at(t, look=lk)


CELL = 1.5
def cell_c(c, r): return (-2.25 + c * CELL, 6.25 - r * CELL, 0.03)


def a_s17a(mr, ms):                   # 信号機の写ったマスへ、一つずつ跳び乗る（乗るとマスが青く光る）
    blue = mat("cell_sel_a", "#3B82F6", rough=0.3, alpha=0.45, emit=0.6)
    seq = [(-2.6, 0.2), cell_c(0, 3)[:2], cell_c(1, 2)[:2], cell_c(2, 1)[:2]]
    idle(mr, a=T0, b=s("17-02") + 1)
    t = s("17-03") + 0.6
    pos = [(-2.6, 0.2, 0.03), (-1.2, 1.4, 0.03), cell_c(2, 1)]
    for p in pos[1:]:
        mr.jump_to(t, p, 0.55, 0.9); t += 1.3
    sel = cube(blue, (cell_c(2, 1)[0], cell_c(2, 1)[1], 0.03), (1.42, 1.42, 0.02)); vis([sel], T0 - 1, False); vis([sel], t - 1.3 + 0.55, True); ev(t - 1.3 + 0.6, "pop_ui")
    idle(mr, a=t, still=[])


def a_s17b(mr, ms):
    idle(mr); mr.at(T0 + 0.8, face=mr.face0 - 20); mr.at(T0 + 2.5, face=mr.face0)


def a_s18a(mr, ms):                   # 端っこのマスのふちで止まる → 乗る → 降りる → また乗りかける。18-02 からマスをふちどる（3D：まるロボより奥）
    org = mat("cell_edge", "#FF8A2A", rough=0.4, emit=3.0)
    cx, cy = 2.25, 4.75
    edges = [cube(org, (cx, cy + dy * 0.75, 0.04), (1.5, 0.07, 0.03)) for dy in (-1, 1)] + [cube(org, (cx + dx * 0.75, cy, 0.04), (0.07, 1.5, 0.03)) for dx in (-1, 1)]
    vis(edges, T0 - 1, False); vis(edges, said("このマス") - 0.1, True)
    l0 = mr.loc0; on = (cx, cy - 0.1, 0.03); off = (l0[0], l0[1] + 0.9, 0.03)
    idle(mr, still=[(s("18-03") - 0.5, s("18-04") + 1)])
    mr.at(T0 + 0.6, look=mr.look0 - 5)
    mr.jump_to(s("18-03") - 0.4, off, 0.45, 0.5); mr.jump_to(s("18-03") + 1.0, on, 0.45, 0.5); mr.jump_to(s("18-03") + 2.3, off, 0.45, 0.5)
    mr.at(s("18-04") - 0.2, on); mr.at(s("18-04") + 0.4, (cx, cy + 0.25, 0.03))                # また乗りかける
    mr.at(s("18-04") + 1.0, (cx, cy + 0.4, 0.03)); mr.tilt(s("18-04") + 0.6, -14, 0.4)


def a_idle(mr, ms):
    idle(mr)


def a_s20e(mr, ms):
    idle(mr); mr.at(T0 + 1.0, face=mr.face0 + 20, look=mr.look0 + 5)


def a_s21b(mr, ms):
    idle(mr); mr.at(T0 + 0.8, look=mr.look0 + 10)


def a_s23(mr, ms):                    # 次の夜：眠そうに（光とろん）ふらふら押す → こっくり → カチッ → はっと起きて、跳ねる
    seq_screen(find_screen(), SCR, "s23")
    m_0, m_1 = said("次の夜") + 1.5, said("……あ、通りました") - 0.6; click = said("……あ、通りました") - 0.3
    pa0 = m_0 + (m_1 - m_0) * 0.55; pa = (pa0, pa0 + 1.0)
    m0 = (0.98, 0.2, 0.75); ms.location = m0; mr.at(T0, (0.98, 0.0, 0.75), -10, -8)
    mr.glow(T0, 0.3, 0.3, 0.1)
    mv = (m_1 - m_0) - 1.0
    for k in range(0, 31):
        u = k / 30; uu = u * u * (3 - 2 * u); tt = m_0 + u * mv; tt += 1.0 if tt > pa[0] else 0
        x = 0.98 - 0.24 * uu + 0.022 * math.sin(uu * 9.0) * (1 - uu); y = 0.2 + 0.11 * uu + 0.016 * math.sin(uu * 6.0) * (1 - uu)
        key(ms, "location", f(tt), (x, y, 0.75), "LINEAR"); mr.at(tt, (x + 0.0, y - 0.2, 0.75), interp="LINEAR", hold=False)
    for k, tt in enumerate((said("……だいぶ") - 1.2, said("……だいぶ") - 0.5, said("……だいぶ") + 0.2, said("……だいぶ") + 0.9)):
        mr.tilt(tt, 16 if k % 2 else -16, 0.45)                                                   # ふらふら
    key(mr.body, ("rotation_euler", 0), f(pa[0]), R(8)); key(mr.body, ("rotation_euler", 0), f(pa[0] + 0.5), R(26)); key(mr.body, ("rotation_euler", 0), f(pa[1]), R(8))   # こっくり
    ev(click, "click")
    mr.tilt(click + 0.2, 0, 0.2); mr.glow(click + 0.25, 0.3, 1.8, 0.15); ev(click + 0.25, "pi")      # はっと起きる
    mr.hop(s("23-04") + 0.8, 0.3, 0.4); mr.hop(s("23-04") + 1.3, 0.3, 0.4); ev(s("23-04") + 1.2, "step"); ev(s("23-04") + 1.7, "step")


ACT = dict(c_s01=a_s01, c_s02a=a_s02a, c_s03=a_s03, c_s05x=a_s05x, c_s05b=a_s05b, c_s06b=a_s06b, c_s08e=a_s08, c_s08f=a_s08,
           c_s11=a_s11, c_s11b=a_idle, c_s11c=a_idle, c_s11d=a_s06b, c_s12a=a_s12a, c_s13a=a_s13a, c_s13b=a_s13b, c_s13d=a_s13d,
           c_s14=a_s14, c_s15a=a_s15, c_s15e=a_idle, c_s16=a_s16, c_s17a=a_s17a, c_s17b=a_s17b, c_s18a=a_s18a, c_s20e=a_s20e,
           c_s21b=a_s21b, c_s21=a_idle, c_s22=a_idle, c_s22b=a_idle, c_s22c=a_idle, c_s23a=a_s23)

base = "b23" if NAME == "c_s23a" else CLIP["base"]
globals()[base]()
if not bpy.context.scene.camera.data.dof.use_dof:
    for k in ("maru", "book", "edge", "gate", "dog"):
        if k in ANCH: focus_on(tuple(ANCH[k]), 4.0); break
mr = M(find_maru()); ms = find_mouse()
TRACK["maru"] = (mr.body, 0.12 if base.startswith(("b0", "b1", "b2")) and base in ("b01", "b02", "b03", "b04a", "b04b", "b05a", "b05b", "b11", "b22", "b23") else 0.6)
ACT.get(NAME, a_idle)(mr, ms)
bpy.context.view_layer.update()
render(NAME, T0, T1, OUTDIR, N_SAMPLES, (RESX, RESY), STEP)
print("DONE", NAME, T0, T1)
