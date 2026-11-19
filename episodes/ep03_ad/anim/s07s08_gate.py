# 会話と広告の回：S07（マイクの門と見張り番）〜 S08（実験）の 3D。声の置き場所（voice/placement.json）の時刻に合わせて動く
# blender -b --factory-startup --python s07s08_gate.py -- <gate|phone> <出力フォルダ> [samples] [--res W H] [--step N] [--frames A B]
#   gate ：07-00〜08-12（門の町の 1 つの舞台。カメラはショットごとに切り替える）
#   phone：08-13〜08-15（外のスマホの画面。右上にオレンジの点）
# 字は 3D に書かない（「Hey Siri」などの札は 2D で重ねる）。合言葉の「ピー」は音で入れる（声には出さない）
# 人と犬の見た目は決定版（番犬＝ぶちの垂れ耳＋紺の帽子：board.py の DOG）
import os, sys, json, math, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.join(HERE, "..", "storyboard")
ARGS = sys.argv[sys.argv.index("--") + 1:]  # 部品を読むと argv が上書きされるので別の名前
MODE, OUTDIR = ARGS[0], ARGS[1]
N_SAMPLES = int(ARGS[2]) if len(ARGS) > 2 and ARGS[2].isdigit() else 32
def opt(name, n, default):
    return [type(d)(ARGS[ARGS.index(name) + 1 + k]) for k, d in enumerate(default)] if name in ARGS else default
RESX, RESY = opt("--res", 2, [1920, 1080])
STEP, = opt("--step", 1, [1])
FR = opt("--frames", 2, [0, 0])
FPS = 24

# 部品（board.py の場面より前：まるロボ・番犬・泡・門の町など）
_ANIM_HERE = HERE
src = open(os.path.join(SB, "board.py"), encoding="utf-8").read()
__file__ = os.path.abspath(os.path.join(SB, "board.py"))  # 部品の中の HERE（絵の素材の場所）を絵コンテのフォルダにする
sys.argv = [sys.argv[0], "--", "x", "x.png"]  # board.py の頭が読む引数（使わない）
exec(src.split("\n# ---------------- 場面（台本 v1.0")[0])  # これ以降 HERE は絵コンテのフォルダ（素材の場所）

# 声の時刻
VO = os.path.join(_ANIM_HERE, "..", "voice")
P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
SID = {e["no"]: e["id"] for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
T = {SID[p["no"]]: (p["start"], p["end"]) for p in P}
T0 = T["07-00"][0] - 0.43 if MODE == "gate" else T["08-13"][0] - 0.4   # この舞台の 0 コマ目（場面の切り替え＝最初の声の 0.4 秒前）
T1 = T["08-13"][0] - 0.4 if MODE == "gate" else T["09-01"][0] - 0.4   # 次の場面（S09）の始まりまで
def f(t): return round((t - T0) * FPS)        # 通しの秒 → この舞台のコマ
def s(i, k=0): return T[i][k]                 # 台詞の始まり（k=1 で終わり）


def key(ob, path, frame, value, interp="BEZIER"):
    setattr(ob, path, value) if not isinstance(path, tuple) else None
    if isinstance(path, tuple):  # (データの道, 番号)
        p, idx = path
        getattr(ob, p)[idx] = value
        ob.keyframe_insert(p, index=idx, frame=frame)
    else:
        ob.keyframe_insert(path, frame=frame)
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp


def show(obs, frame, on):
    for o in obs:
        o.hide_render = not on; o.keyframe_insert("hide_render", frame=frame)
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"


def matkey(m, frame, strength=None, color=None):
    b = m.node_tree.nodes["Principled BSDF"]
    if strength is not None:
        b.inputs["Emission Strength"].default_value = strength
        b.inputs["Emission Strength"].keyframe_insert("default_value", frame=frame)
    if color is not None:
        b.inputs["Emission Color"].default_value = srgb(color)
        b.inputs["Emission Color"].keyframe_insert("default_value", frame=frame)


# ---------------- 門（格子とランプを動かす）
def gate_anim():
    pil = mat("gatep", "#C7D0D6", rough=0.3, metal=0.7)
    lamps, lights = [], []
    for x in (-1.3, 1.3):
        cube(pil, (x, 1.8, 1.3), (0.42, 0.42, 2.6), bevel=0.05)
        lm = mat("lamp%.1f" % x, "#5A3A2A", rough=0.3, emit=0.0)
        lm.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = srgb("#FF7A00")
        sphere(lm, (x, 1.57, 2.42), 0.09)
        bpy.ops.object.light_add(type='POINT', location=(x, 1.3, 2.42))
        L = bpy.context.object; L.data.energy = 0.0; L.data.color = srgb("#FF7A00")[:3]
        lamps.append(lm); lights.append(L)
    cube(pil, (0, 1.8, 2.78), (3.2, 0.5, 0.48), bevel=0.06)
    hole = mat("hole", "#0B1220", rough=0.8)
    for cx in (-0.75, 0.75):
        for i in range(6):
            cyl(hole, (cx + (i - 2.5) * 0.16, 1.54, 2.78), 0.05, 0.02, rot=(R(90), 0, 0), verts=16)
    bar = mat("bar", "#8A97A1", rough=0.25, metal=0.9)
    bars = empty((0, 0, 0))
    for i in range(-4, 5):
        cyl(bar, (i * 0.26, 1.8, 1.25), 0.04, 2.5, verts=16, parent=bars)
    cube(bar, (0, 1.8, 0.05), (2.3, 0.08, 0.08), parent=bars)
    return bars, lamps, lights


def bars_lift(bars, t_up, t_top, t_down=None, t_bottom=None):
    EVENTS.append((round(t_up, 3), "gate_up"))
    if t_down: EVENTS.append((round(t_down, 3), "gate_down"))
    key(bars, ("location", 2), f(t_up), 0.0)
    key(bars, ("location", 2), f(t_top), 2.2)
    if t_down:
        key(bars, ("location", 2), f(t_down), 2.2)
        key(bars, ("location", 2), f(t_bottom), 0.0)


def lamps_on(lamps, lights, t, on=True):
    if on: EVENTS.append((round(t, 3), "lamp"))
    for m, L in zip(lamps, lights):
        matkey(m, f(t) - 1, strength=0.0 if on else 2.5)
        matkey(m, f(t) + 3, strength=2.5 if on else 0.0)
        L.data.energy = 0.0 if on else 60; L.data.keyframe_insert("energy", frame=f(t) - 1)
        L.data.energy = 60 if on else 0.0; L.data.keyframe_insert("energy", frame=f(t) + 3)


# ---------------- 音の泡（門から入って、番犬の耳の前で消える）
EAR = (1.75, 0.45, 2.35)        # 番犬の耳の前（泡が消える所）
GATE_IN = (0.0, 2.6, 1.5)       # 門の向こう（泡が入ってくる所）
_nb = [0]
EVENTS = []   # 効果音を付ける出来事（通しの秒, 種類）
DOT2D = []    # 外のスマホの画面のオレンジの点の位置（2D の丸用）
STEPS = []
SHOTLOG = []   # カメラのカット（絵コンテ表用。PLAN_DUMP で書き出す）


def sound_bubble(t_in, t_pop, icon=None, r=0.3, glow=0.0, path=None, burst_at=None, pop=True):
    _nb[0] += 1
    b = bubble((0, 0, 0), r, icon, glow=glow)
    a = path[0] if path else GATE_IN
    z = path[1] if path else EAR
    mid = ((a[0] + z[0]) / 2, (a[1] + z[1]) / 2 - 0.3, (a[2] + z[2]) / 2 + 0.25)
    key(b, "scale", f(t_in) - 1, (0.001,) * 3)
    key(b, "location", f(t_in) - 1, a)
    key(b, "scale", f(t_in) + 6, (1.0,) * 3)
    key(b, "location", f((t_in + t_pop) / 2), mid)
    key(b, "location", f(t_pop), z)
    EVENTS.append((round(t_in, 3), "bubble_in"))
    if pop:
        EVENTS.append((round(t_pop, 3), "pop"))
        key(b, "scale", f(t_pop), (1.0,) * 3)
        key(b, "scale", f(t_pop) + 3, (0.001,) * 3)
        bs = empty(burst_at or z)  # はじけるしずく（burst の物を、ここを中心に大きさを動かす）
        before = set(bpy.data.objects)
        burst(burst_at or z, r * 1.1, seed=_nb[0])
        bpy.context.view_layer.update()
        for o in set(bpy.data.objects) - before:
            o.parent = bs; o.matrix_parent_inverse = bs.matrix_world.inverted()
        key(bs, "scale", f(t_pop), (0.001,) * 3)
        key(bs, "scale", f(t_pop) + 4, (1.0,) * 3)
        key(bs, "scale", f(t_pop) + 9, (1.25,) * 3)
        key(bs, "scale", f(t_pop) + 11, (0.001,) * 3)
    return b


# ---------------- まるロボ（v9 までの作り。v10 から使わない）
class MaruOld:
    def __init__(self, loc, face, **kw):
        self.root = maru(loc, face_deg=face, **kw)
        self.body = self.root.children[0]
        self.z0 = self.body.location.z
        self.ant = bpy.data.materials["maru_orange"]

    def at(self, t, loc=None, face=None, look=None, interp="BEZIER", hold=True):
        # v4「まるロボ徐々に動いてひっくり返ってる」(3:57)：前の置き場所から何秒も離れた時刻に次を置くと、その間ずっとゆっくり動き続けていた。
        #   1 秒より離れているときは、動き出す 0.8 秒前まで前の場所・向きのまま止めておく（hold=False で、ゆっくり動かすことも）
        last = self.__dict__.setdefault("_last", {})
        for ch, v in (("loc", loc), ("face", face), ("look", look)):
            if v is None: continue
            if hold and ch in last and t - last[ch][0] > 1.0:
                th = max(last[ch][0], t - 0.8); pv = last[ch][1]
                if ch == "loc": key(self.root, "location", f(th), pv, interp)
                elif ch == "face": key(self.root, ("rotation_euler", 2), f(th), R(pv), interp)
                else: key(self.body, ("rotation_euler", 0), f(th), R(-pv), interp)
            last[ch] = (t, v)
        if loc is not None: key(self.root, "location", f(t), loc, interp)
        if face is not None: key(self.root, ("rotation_euler", 2), f(t), R(face), interp)
        if look is not None: key(self.body, ("rotation_euler", 0), f(t), R(-look), interp)

    def hop(self, t, h=0.3, d=0.45):
        if h >= 0.25: EVENTS.append((round(t, 3), "jump")); EVENTS.append((round(t + d, 3), "land"))
        key(self.body, ("location", 2), f(t), self.z0)
        key(self.body, ("location", 2), f(t + d / 2), self.z0 + h)
        key(self.body, ("location", 2), f(t + d), self.z0)

    def walk(self, t0, t1, a, b, face=None, h=0.05, step=0.3):
        """a から b へ歩く（小さく弾みながら）。v8 見直し：場所を変えるときに、すべって動かない（他の回の決まり）"""
        self.at(t0, a, face); self.at(t1, b, face, hold=False)
        n = max(1, int(round((t1 - t0) / step))); d = (t1 - t0) / n
        for k in range(n): self.hop(t0 + k * d, h, d)
        STEPS.extend(t0 + (k + 1) * d for k in range(n))   # 足音

    def lean(self, t, deg, d=0.3):
        key(self.body, ("rotation_euler", 1), f(t), 0.0)
        key(self.body, ("rotation_euler", 1), f(t + d), R(deg))

    def glow(self, t, s):
        matkey(self.ant, f(t), strength=s)


_MM_ = exec(open(os.path.join(_ANIM_HERE, "maru_ep03.py"), encoding="utf-8").read())   # v10：本物のまるロボを決まりの部品で動かす（Maru）

# ---------------- カメラ（ショットごとに切り替え。ショットの中はゆっくり動く）
def shots(cam, tgt, S):
    for k, (t0, t1, l0, g0, l1, g1, lens) in enumerate(S):
        a, b = f(t0), f(t1) - 1
        key(cam, "location", a, l0, "LINEAR"); key(tgt, "location", a, g0, "LINEAR")
        key(cam.data, "lens", a, lens, "CONSTANT")
        key(cam, "location", b, l1, "CONSTANT"); key(tgt, "location", b, g1, "CONSTANT")
        SHOTLOG.append((round(t0, 2), round(t1, 2), tuple(round(v, 2) for v in l0), tuple(round(v, 2) for v in g0), lens))   # 絵コンテ表用


def _load_wt(path):
    # 言葉を言う瞬間の表（voice/word_times.json。wordtime.py の load_table と同じ。PC のキットでも動くよう、ここに置く）
    tb = json.load(open(path, encoding="utf-8"))
    yl = lambda t: max(0, sum(1 for ch in t if ch not in "、。？！…「」（）・ 　"))
    def Wt(i, frag, o=0.0):
        v = tb[i]; t = v["text"]; k = t.find(frag)
        if k < 0: raise KeyError("%s に「%s」がない" % (i, frag))
        if v["wt"] is None: return v["start"] + (v["end"] - v["start"]) * yl(t[:k]) / max(1, yl(t)) + o
        ch, asg = v["wt"]
        for (a, b), (g0, g1) in zip(ch, asg):
            if a <= k < b: return v["start"] + (g0 + (g1 - g0) * yl(t[a:k]) / max(1, yl(t[a:b]))) / v["speed"] + o
        return v["start"] + asg[-1][0] / v["speed"] + o
    return Wt


Wt = _load_wt(os.path.join(_ANIM_HERE, "..", "voice", "word_times.json"))   # v4：泡は声に合わせて出す
OUTSIDE = (0.0, 2.25, 1.5)      # 門の外のすぐ前（閉じた門では、泡はここで止まってはじける。v4「泡が門を通り過ぎてから消える」）


def scene_gate():
    city_floor()
    bars, lamps, lights = gate_anim()
    dog((2.35, 1.0, 0), -40, eyes="anim", **DOG)
    D = DOG_PARTS
    head, ears = D["head"], D["ears"]
    # 番犬：ふだんは目を閉じて、ゆっくり息をする（頭が少し上下）
    t = T0
    while t < T1:
        key(head, ("location", 2), f(t), 1.75); key(head, ("location", 2), f(t + 1.8), 1.78); t += 3.6
    eyes_closed = D["closed"][0] + D["closed"][1]
    show(D["open"][0] + D["open"][1], 0, False); show(eyes_closed, 0, True)

    def ear_twitch(t):
        for e in ears:
            r0 = e.rotation_euler[1]
            key(e, ("rotation_euler", 1), f(t), r0); key(e, ("rotation_euler", 1), f(t + 0.12), r0 + R(18) * (1 if e.location.x > 0 else -1))
            key(e, ("rotation_euler", 1), f(t + 0.35), r0)

    # v10（v9 のコメント 3:08・3:27・4:00・4:13・4:56「泡がわからない」「門の外側からの映像に」「内側のまるロボが外の泡に触れるのはおかしい」）
    #   泡は門の外の遠く（FAR）で生まれ、門へ流れてくる。合言葉でない泡は門の手前（OUTSIDE）ではじける。合言葉の泡は、格子が上がりきってから中へ入り、奥へ進んで消える。
    #   泡が出る文は門の外から映し、見張り番とまるロボの様子は内側から映す（文ごとに切り替える）。まるロボは門の内側にいて、外の泡には触れない。
    #   まるロボの動きは決まりの部品（maru_walk.md・maru_motions.md）。
    FAR = lambda x=0.0, z=1.5: (x, 6.2, z)
    def through(b, t_wait, t_go, x=0.2, z=1.4):                        # 合言葉の泡：門の前で待つ → 格子が上がったら中へ進み、奥で消える
        key(b, "location", f(t_wait), (x, 2.3, z)); key(b, "location", f(t_go), (x, 2.3, z))
        key(b, "location", f(t_go + 0.7), (x, 1.0, z)); key(b, "location", f(t_go + 1.6), (x * 0.5, -1.6, z + 0.1))
        key(b, "scale", f(t_go + 1.3), (1.0,) * 3); key(b, "scale", f(t_go + 1.7), (0.001,) * 3)
    P0, PB, PM, PD = (-0.6, -1.2), (0.25, 1.15), (0.4, -0.6), (1.1, -0.35)
    mr = Maru((P0[0], P0[1], 0), 95, eye_glow=1.2)
    mr.look_around(T0 + 0.1)                                           # 07-00 どこから？
    mr.at(Wt("07-01", "この門") + 0.1, face=face_to(P0, (0.0, 2.0))); mr.at(Wt("07-01", "この門") + 0.3, look=16)    # 門を見上げる
    mr.at(s("07-02") + 0.2, face=face_to(P0, (2.35, 1.0)), look=10)   # 番犬のほうを向く
    ear_twitch(s("07-02b") + 0.8)                                     # 音を聞く係
    # 07-04b：合言葉の泡が外から来て、格子が上がり、中へ入っていく（予告）
    t4 = Wt("07-04b", "この合言葉")
    pb = sound_bubble(t4 - 0.6, t4 + 0.8, None, r=0.32, glow=1.5, path=(FAR(0.2, 1.4), (0.2, 2.3, 1.4)), pop=False)
    bars_lift(bars, t4 + 0.9, t4 + 1.7, s("07-04b", 1) + 0.4, s("07-04b", 1) + 1.2)
    through(pb, t4 + 0.8, t4 + 1.8)
    lamps_on(lamps, lights, t4 + 1.3); lamps_on(lamps, lights, s("07-04b", 1) + 0.8, on=False)
    # 07-05・07-05a：外の音（時計・車・寝息）が泡になって門へ流れてきて、門の手前ではじける
    icons = ["icon_clock.png", "icon_car.png", "icon_sleep.png", "icon_car.png", "icon_clock.png"]
    tt = Wt("07-05", "この泡") - 0.3
    for k in range(5):
        x = -0.55 + 0.27 * k; z = 1.25 + 0.12 * (k % 3)
        sound_bubble(tt, tt + 1.9, icons[k], path=(FAR(x * 2.2, z + 0.3), (x, 2.3, z)))
        ear_twitch(tt + 1.8); tt += 2.0
    # 07-05b：まるロボは格子の内側まで歩いて行き、外から来る泡をのぞく → 泡は目の前（格子の外）ではじけて、驚く
    mr.walk(0, s("07-05a") + 2.6, None, PB); mr.at(s("07-05a") + 3.4, face=face_to(PB, (0.25, 3.0)))
    mr.peer(s("07-05b") - 2.6, dur=1.0)
    tj = s("07-05b") + 0.2
    sound_bubble(tj - 1.9, tj, "icon_clock.png", path=(FAR(0.3, 1.0), (0.3, 2.3, 0.9)))
    mr.surprise(tj - 0.05)
    mr.walk(0, s("07-06") + 3.6, None, PM); mr.at(s("07-06") + 4.6, face=face_to(PM, (2.35, 1.0)))   # 戻って番犬を見る
    # ---- S08 実験
    mr.walk(0, s("08-02") + 3.4, None, PD); mr.at(s("08-02") + 4.2, face=face_to(PD, (2.35, 1.0)))   # 「目をはなさないで」：番犬の近くへ
    tt = Wt("08-03", "テント")                                   # 「テント」と言った瞬間に、外で泡が生まれる
    sound_bubble(tt, tt + 1.8, "icon_tent.png", path=(FAR(0.0, 1.5), OUTSIDE)); ear_twitch(tt + 1.7)
    mr.peer(s("08-04") + 0.1, dur=1.6)                               # 番犬の顔をのぞく（知らん顔）
    tt = Wt("08-05", "ヘイ、テント")
    sound_bubble(tt, tt + 1.9, "icon_tent.png", r=0.42, path=(FAR(0.3, 1.6), (0.3, 2.3, 1.6))); ear_twitch(tt + 1.8); ear_twitch(tt + 2.2)
    mr.confused(s("08-06") + 0.5)                                    # 完全に無視：首をかしげる
    mr.think(s("08-07") + 0.4, dur=s("08-07", 1) - s("08-07") - 0.3)   # 「よく似た言葉では？」：考える → 文の終わりの切れ目でひらめく（ピン）
    tb = s("08-08") - 1.6 + 0.3                                  # 「ピー」の始まり
    sound_bubble(tb - 0.3, tb + 1.2, None, r=0.32, glow=0.4, path=(FAR(0.0, 1.5), OUTSIDE))
    show(D["closed"][1], f(tb + 1.2), False); show(D["open"][1], f(tb + 1.2), True)
    show(D["closed"][1], f(s("08-08") + 2.6), True); show(D["open"][1], f(s("08-08") + 2.6), False)
    mr.surprise(tb + 1.25)                                           # 片目が開いた！
    mr.nod(s("08-09") + 0.6)                                         # うっかり反応することもある
    # 08-11 本物の合言葉：外で泡 → 門の前で待つ → 両目がぱっと開き、格子が上がり、ランプがオレンジ → 泡が中へ入って進む
    tb = s("08-11") - 1.6 + 0.3
    tg = Wt("08-11", "門が開きました")
    rb = sound_bubble(tb - 0.3, tb + 1.2, None, r=0.34, glow=1.5, pop=False, path=(FAR(0.0, 1.5), OUTSIDE))
    show(eyes_closed, f(tb + 1.2), False); show(D["open"][0] + D["open"][1], f(tb + 1.2), True)
    ear_twitch(tb + 1.2)
    bars_lift(bars, tg - 0.5, tg + 0.4)
    lamps_on(lamps, lights, tg + 0.5)
    through(rb, tb + 1.2, tg + 0.45, x=0.0, z=1.5)
    mr.hops(tg + 0.6, n=2); mr.glow(tg + 0.6, 8.0)
    # ---- 光
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF")
    area((4, -3, 3), (2.3, 1, 1.5), 250, 3, "#FFE9C7")
    spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    area((0.3, 5.0, 3.0), (0.2, 1.6, 1.1), 260, 3, "#BFD9FF")          # 外から見たとき、格子・まるロボ・番犬が暗い影にならないように
    pm = bpy.data.materials.get("bubble1.5")                            # 合言葉の泡は、ランプと同じだいだい色に光る（v10：ただの白い玉に見えた）
    if pm:
        bn = pm.node_tree.nodes["Principled BSDF"]
        bn.inputs["Emission Color"].default_value = (1.0, 0.55, 0.15, 1.0); bn.inputs["Emission Strength"].default_value = 0.9
        bn.inputs["Base Color"].default_value = (1.0, 0.78, 0.5, 1.0)
    # ---- カメラ（ショット）
    cam = camera((0, -6, 2), (0, 0, 1), lens=32)
    tgt = empty((0, 0, 1))
    for c in list(cam.constraints): cam.constraints.remove(c)
    tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    W = ((-0.9, -7.6, 2.0), (0.6, 1.0, 1.55))           # 内側の引き：門と番犬とまるロボ
    O = ((-1.3, 8.6, 2.1), (0.1, 1.6, 1.25))            # 外側の引き：泡が生まれて門へ流れてくる所と、格子の向こうのまるロボ。v10：番犬が手前で黒い影になったので、反対側から
    MD = ((-1.9, -2.9, 1.35), (1.6, 0.9, 1.2))          # まるロボの肩ごしに番犬（カメラはまるロボの 1.5m うしろ。近すぎると帽子の中に入った）
    DG = ((3.15, -1.85, 1.6), (2.4, 1.0, 1.75))           # 番犬の寄り。v10：右手前から（まるロボが番犬の近くに立つと、左下に帽子が大きく切れて映った）
    def sh(a, b, v, lens=32, d=(0.15, -0.3, 0.0)):
        return (a, b, v[0], v[1], tuple(v[0][k] + d[k] for k in range(3)), v[1], lens)
    tt3 = Wt("08-03", "テント"); tt5 = Wt("08-05", "ヘイ、テント"); tb8 = s("08-08") - 1.6; tb11 = s("08-11") - 1.6
    S = [
        (T0, s("07-01") - 0.2, (-1.9, -4.6, 1.2), (-0.5, -1.0, 0.9), (-1.8, -4.3, 1.2), (-0.5, -1.0, 0.95), 36),        # まるロボ（どこから？）
        (s("07-01") - 0.2, s("07-02") - 0.2, (0.7, -2.2, 1.5), (0.1, 1.8, 1.9), (0.25, -1.1, 1.6), (0.0, 1.8, 2.5), 28),    # 門を見せる → 柱の穴へ寄る
        sh(s("07-02") - 0.2, s("07-02b") - 0.2, DG, 34),                                                                   # 番犬（見張り番がいます）
        sh(s("07-02b") - 0.2, s("07-03") - 0.2, W, 32),                                                                    # 内側の引き：門・番犬・まるロボ（門を開けるかを決める係）
        sh(s("07-03") - 0.2, s("07-04") - 0.2, DG, 38, (0.1, 0.25, 0.0)),                                                   # 番犬に寄る（待っているのは一つの言葉）
        sh(s("07-04") - 0.2, s("07-04b") - 0.2, MD, 30),                                                                   # まるロボの肩ごしに番犬（あの合言葉）。v10：番犬の寄りが 19 秒続いていた
        sh(s("07-04b") - 0.2, s("07-05b") + 1.4, O, 30, (-0.2, -0.5, 0.0)),                                                 # 外から：合言葉の泡が入る・外の音の泡がはじける・まるロボの目の前ではじける
        sh(s("07-05b") + 1.4, s("08-01") - 0.4, DG, 36),                                                                    # 番犬に寄る（聞き分けているのはこの見張り番）
        sh(s("08-01") - 0.4, tt3 - 0.6, W, 32),                                                                             # 内側の引き：これから試す
        sh(tt3 - 0.6, s("08-04"), O, 30),                                                                                   # 外から：「テント」の泡
        sh(s("08-04"), tt5 - 0.6, DG, 36),                                                                                  # 番犬：知らん顔
        sh(tt5 - 0.6, s("08-06"), O, 30),                                                                                   # 外から：「ヘイ、テント」の泡
        sh(s("08-06"), tb8 - 0.6, W, 32),                                                                                   # 内側：無視・首をかしげる
        sh(tb8 - 0.6, s("08-08"), O, 30),                                                                                   # 外から：似た言葉の泡
        sh(s("08-08"), tb11 - 0.6, DG, 36),                                                                                 # 番犬：片目だけ開ける
        sh(tb11 - 0.6, s("08-12") - 0.2, O, 30, (-0.3, -0.6, 0.0)),                                                          # 外から：本物の合言葉 → 門が開いて、泡が中へ
        (s("08-12") - 0.2, T1, (-1.0, -2.0, 2.3), (-1.3, 1.57, 2.42), (-1.15, -1.6, 2.35), (-1.3, 1.57, 2.42), 38),         # ランプに寄る
    ]
    shots(cam, tgt, S)


def scene_phone():
    # 08-13〜08-15：外から見たスマホの画面。右上にオレンジの点（2D の丸で囲む）
    world("#0C1426", 0.15)
    ground("#E9E2D4", size=20)
    ph = phone((0, 0, 0), 0, screen="phone_ad.png", glow=1.6, s=2.2)
    dot = sphere(mat("dot", "#FF7A00", rough=0.3, emit=0.0), (0.27, 0.62, 0.11), 0.03)
    matkey(dot.data.materials[0], f(s("08-14")) - 6, strength=0.0, color="#FF7A00")
    matkey(dot.data.materials[0], f(s("08-14")) - 3, strength=2.5, color="#FF7A00")
    area((-2, -3, 3), (0, 0, 0), 250, 3, "#BFD9FF")
    cam = camera((0.0, -1.2, 2.6), (0.0, 0.1, 0.0), lens=40)
    key(cam, "location", 0, (0.0, -1.2, 2.6), "LINEAR")
    key(cam, "location", f(s("08-14")) - 8, (0.25, -0.2, 1.4), "BEZIER")   # 点を見せる所で止める（2D の丸を重ねるため）
    key(cam, "location", f(T1), (0.25, -0.2, 1.4), "CONSTANT")
    from bpy_extras.object_utils import world_to_camera_view
    sc_ = bpy.context.scene; sc_.frame_set(f(s("08-14")) + 6)
    v = world_to_camera_view(sc_, cam, dot.matrix_world.translation)
    DOT2D.extend([round(v.x * 1280), round((1 - v.y) * 720)])   # 1280×720 の画面での点の位置


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
(scene_gate if MODE == "gate" else scene_phone)()
bake_all(T1)                                       # v10：まるロボの予定 → 毎コマの姿勢

if os.environ.get("PLAN_DUMP"):                # 絵コンテ表用：カット・まるロボの命令・効果音を書き出す（make_board_table.py が読む）
    import maru_cmds as _MC
    json.dump(dict(key="gate", t0=T0, t1=T1, shots=SHOTLOG, events=sorted(EVENTS), steps=len(STEPS),
                   maru=[[(round(t, 2), k, {a: (round(v, 2) if isinstance(v, float) else v) for a, v in d.items() if a in ("deg", "pitch", "face", "n", "dur", "speed")}) for t, k, d in sorted(m.cmds, key=lambda c: c[0])] for m in _MC.ALL]),
              open(os.path.join(os.environ["PLAN_DUMP"], "gate" + "_plan.json"), "w"), ensure_ascii=False)
sc.frame_start = FR[0] if FR[1] else 0
sc.frame_end = FR[1] if FR[1] else f(T1) - 1
sc.frame_step = STEP
sc.render.fps = FPS
sc.render.engine = 'CYCLES'
sc.cycles.samples = N_SAMPLES
sc.cycles.use_denoising = True
sc.render.use_persistent_data = True  # コマごとに舞台を組み直さない（速くなる）
if "--fast" in ARGS:  # 光の跳ね返りを減らす。見た目はほぼ同じで 1.5〜2 倍速い（2026-11-14 ユーザー「速くするやり方ないの」→ 本番の PC でも使う）
    c = sc.cycles
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = 3, 1, 1, 2, 4
    c.caustics_reflective = c.caustics_refractive = False
    c.use_adaptive_sampling = True
sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = RESX, RESY
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Punchy'
sc.render.filepath = os.path.join(OUTDIR, MODE + "_")
exec(open(os.path.join(_ANIM_HERE, "pc_out.py"), encoding="utf-8").read())  # PC：--gpu・--video
json.dump(dict(mode=MODE, t0=T0, t1=T1, fps=FPS, frames=sc.frame_end + 1, steps=sorted(STEPS), events=sorted(EVENTS), dot2d=DOT2D), open(os.path.join(OUTDIR, MODE + "_log.json"), "w"))
print("FRAMES", sc.frame_start, sc.frame_end, "T0", T0)
if "--blend" in ARGS:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, MODE + ".blend"))
else:
    bpy.ops.render.render(animation=True)
