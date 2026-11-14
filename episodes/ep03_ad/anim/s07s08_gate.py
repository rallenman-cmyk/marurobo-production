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


# ---------------- まるロボ（root：場所と向き、body：跳ぶ・見上げる）
class Maru:
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

    def lean(self, t, deg, d=0.3):
        key(self.body, ("rotation_euler", 1), f(t), 0.0)
        key(self.body, ("rotation_euler", 1), f(t + d), R(deg))

    def glow(self, t, s):
        matkey(self.ant, f(t), strength=s)


# ---------------- カメラ（ショットごとに切り替え。ショットの中はゆっくり動く）
def shots(cam, tgt, S):
    for k, (t0, t1, l0, g0, l1, g1, lens) in enumerate(S):
        a, b = f(t0), f(t1) - 1
        key(cam, "location", a, l0, "LINEAR"); key(tgt, "location", a, g0, "LINEAR")
        key(cam.data, "lens", a, lens, "CONSTANT")
        key(cam, "location", b, l1, "CONSTANT"); key(tgt, "location", b, g1, "CONSTANT")


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

    mr = Maru((-1.7, -0.5, 0), 20, eye_glow=1.2, look_up=0)
    # ---- S07
    mr.at(T0, (-0.6, -1.2, 0), 25, 5)
    for k, tt in enumerate((T0 + 0.3, T0 + 1.3, T0 + 2.3)):   # 07-00 きょろきょろ（どこから？）
        mr.at(tt, face=25 + (35 if k % 2 == 0 else -35))
    mr.at(s("07-01") - 0.3, face=10, look=16)                   # 門を見上げる
    mr.at(s("07-01", 1) - 2.5, face=-10, look=22)                # 柱の穴と外の穴を見比べる（首を振る）
    mr.at(s("07-01", 1) - 1.5, face=20, look=22)
    mr.at(s("07-02") + 0.4, (-0.8, -1.0, 0), 55, 18)             # 番犬の方を向く
    ear_twitch(s("07-02b") + 0.8)                                 # 音を聞く係
    # 07-04b：合言葉の泡が来たときだけ格子が上がる（予告。すぐ下りる）
    #   v4「門を通ってから門が開いてる」：泡は門の外で待つ → 格子が上がりきってから → 中へ通る
    t4 = Wt("07-04b", "この合言葉")
    pb = sound_bubble(t4 + 0.1, t4 + 1.1, None, r=0.32, glow=1.5, path=(GATE_IN, (0.2, 2.25, 1.4)), pop=False)
    key(pb, "location", f(t4 + 2.2), (0.2, 2.25, 1.4)); key(pb, "location", f(t4 + 2.9), (0.2, -1.5, 1.4))
    key(pb, "scale", f(t4 + 2.7), (1.0,) * 3); key(pb, "scale", f(t4 + 3.0), (0.001,) * 3)
    bars_lift(bars, t4 + 1.2, t4 + 2.1, s("07-04b", 1) + 0.2, s("07-04b", 1) + 1.0)
    lamps_on(lamps, lights, t4 + 1.7)
    lamps_on(lamps, lights, s("07-04b", 1) + 0.6, on=False)
    # 07-05：外の音の泡（時計・車）が流れてきて、番犬の耳の前で消える
    icons = ["icon_clock.png", "icon_car.png", "icon_sleep.png", "icon_car.png", "icon_clock.png", "icon_sleep.png"]
    tt = Wt("07-05", "この泡")
    for k in range(6):
        sound_bubble(tt, tt + 2.0, icons[k], path=(GATE_IN, (-0.6 + 0.24 * k, 2.25, 1.25 + 0.12 * (k % 3))))   # 門の外で止まってはじける
        ear_twitch(tt + 1.9)
        tt += 2.1
    # 07-05b：まるロボが泡に跳びつく → 頭の上で消える
    tj = s("07-05b") - 0.9
    mr.at(tj - 0.8, (0.3, 1.2, 0), 15, 25)                      # 門の格子の前まで行って
    sound_bubble(tj - 1.8, tj + 0.25, "icon_clock.png", path=(GATE_IN, (0.32, 2.2, 1.6)), burst_at=(0.32, 2.2, 1.6))   # 格子の向こうで消える
    mr.hop(tj - 0.1, 0.4, 0.55)
    mr.at(s("07-05b") + 1.0, look=30)                            # 消えた所を見上げる
    mr.at(s("07-06") + 0.5, (0.4, -0.6, 0), 60, 14)              # 番犬を見る
    # ---- S08 実験
    mr.at(s("08-02") + 1.0, look=10)
    mr.at(s("08-02") + 2.0, face=40)                             # 外を見て、うなずく
    mr.hop(s("08-02", 1) - 1.2, 0.12, 0.3)
    # 08-03 テント：泡は消える。まるロボは番犬の顔をのぞき込む
    tt = Wt("08-03", "テント")                                   # 「テント」と言った瞬間に泡
    sound_bubble(tt, tt + 1.6, "icon_tent.png", path=(GATE_IN, OUTSIDE)); ear_twitch(tt + 1.5)
    mr.at(s("08-04") - 0.2, (1.35, -0.45, 0), 60, 14)           # 番犬の顔をのぞく（見上げすぎない。v4「ひっくり返ってる」）
    mr.at(s("08-04", 1), (1.35, -0.45, 0), 60, 14)
    # 08-05 ヘイ、テント（大きな泡）：耳がぴくっ。まるロボが目の前で左右に跳ねる
    tt = Wt("08-05", "ヘイ、テント")                             # v4「音声に合わせて泡出して」(4:10)
    sound_bubble(tt, tt + 1.8, "icon_tent.png", r=0.42, path=(GATE_IN, (0.3, 2.25, 1.6))); ear_twitch(tt + 1.6); ear_twitch(tt + 2.1)
    for k in range(4):
        x = 1.05 if k % 2 == 0 else 1.6
        mr.at(s("08-06") + 0.6 * k, (x, -0.45, 0), 60, 30); mr.hop(s("08-06") + 0.6 * k, 0.18, 0.4)
    mr.at(s("08-07"), (0.5, -0.5, 0), 55, 16)
    # 08-08 似た言葉（ピー）：片目だけ開けて、すぐ閉じる。まるロボはのけぞる
    tb = s("08-08") - 1.6 + 0.3                                  # 「ピー」の始まり
    sound_bubble(tb, tb + 1.0, None, r=0.32, glow=0.4, path=(GATE_IN, OUTSIDE))   # 「ピー」と同時に泡。門の外で消える
    show(D["closed"][1], f(tb + 1.0), False); show(D["open"][1], f(tb + 1.0), True)
    show(D["closed"][1], f(s("08-08") + 2.6), True); show(D["open"][1], f(s("08-08") + 2.6), False)
    mr.lean(tb + 1.1, -18, 0.25); mr.at(tb + 1.1, look=26)
    mr.lean(s("08-08") + 3.0, 0, 0.4)
    # 08-11 本物の合言葉（ピー）：両目をぱっと開け、耳が動き、格子が上がり、ランプがオレンジ
    tb = s("08-11") - 1.6 + 0.3
    #   v4「門を通ってから門が開いてる」(4:56)：泡は門の外で待つ → 「門が開きました」で格子が上がる → 上がりきってから中へ
    tg = Wt("08-11", "門が開きました")
    rb = sound_bubble(tb, tb + 1.0, None, r=0.34, glow=1.5, pop=False, path=(GATE_IN, OUTSIDE))
    key(rb, "location", f(tg + 0.5), OUTSIDE); key(rb, "location", f(tg + 1.3), (1.2, 0.9, 1.6))
    key(rb, "scale", f(tg + 1.2), (1.0,) * 3); key(rb, "scale", f(tg + 1.5), (0.001,) * 3)
    show(eyes_closed, f(tb + 1.0), False); show(D["open"][0] + D["open"][1], f(tb + 1.0), True)
    ear_twitch(tb + 1.0)
    bars_lift(bars, tg - 0.5, tg + 0.4)
    lamps_on(lamps, lights, tg + 0.5)
    mr.hop(tg + 0.7, 0.45, 0.55); mr.hop(tg + 1.4, 0.3, 0.45)
    mr.glow(tg + 0.6, 0.3); mr.glow(tg + 0.9, 8.0)
    # ---- 光
    area((-2, -4, 3.5), (0, 0, 1), 350, 4, "#BFD9FF")
    area((4, -3, 3), (2.3, 1, 1.5), 250, 3, "#FFE9C7")
    spot((0, -1.5, 6), (0, 1.5, 1), 1200, 45, "#E8F7FF")
    # ---- カメラ（ショット）
    cam = camera((0, -6, 2), (0, 0, 1), lens=32)
    tgt = empty((0, 0, 1))
    for c in list(cam.constraints): cam.constraints.remove(c)
    tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    W = ((-0.9, -7.6, 2.0), (0.6, 1.0, 1.55))           # 門と番犬とまるロボの引き
    S = [
        (T0, s("07-01") - 0.2, (-1.9, -4.6, 1.2), (-0.5, -1.0, 0.9), (-1.8, -4.3, 1.2), (-0.5, -1.0, 0.95), 36),        # まるロボ（どこから？）
        (s("07-01") - 0.2, s("07-02") - 0.2, (-0.6, -5.0, 0.9), (0.0, 1.8, 1.6), (-0.3, -3.6, 1.6), (0.0, 1.8, 2.6), 30),  # 門を見せる → 柱の穴へ寄る
        (s("07-02") - 0.2, s("07-04") - 0.2, (0.8, -3.0, 1.6), (2.3, 1.0, 1.7), (1.0, -2.6, 1.7), (2.3, 1.0, 1.8), 34),    # 番犬
        (s("07-04") - 0.2, s("07-06") - 0.2, W[0], W[1], (-0.7, -7.0, 2.0), (0.6, 1.0, 1.5), 32),                           # 引き：予告・泡
        (s("07-06") - 0.2, s("08-01") - 0.4, (1.2, -2.2, 1.6), (2.3, 1.0, 1.75), (1.35, -1.9, 1.65), (2.3, 1.0, 1.8), 36),  # 番犬に寄る（聞き分けているのはこの見張り番）
        (s("08-01") - 0.4, s("08-12") - 0.2, W[0], W[1], (-0.6, -7.2, 2.0), (0.7, 1.0, 1.5), 32),                           # 実験の引き
        (s("08-12") - 0.2, T1, (-1.0, -2.0, 2.3), (-1.3, 1.57, 2.42), (-1.15, -1.6, 2.35), (-1.3, 1.57, 2.42), 38),             # ランプに寄る
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
