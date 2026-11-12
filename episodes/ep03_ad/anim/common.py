# 会話と広告の回：3D を声の時刻に合わせて動かす共通の部品（scenes_all.py が exec で読む）
# 前提：exec する側で ARGS・_ANIM_HERE を決めてから、このファイルを読む
import os, sys, json, math, bpy
SB = os.path.join(_ANIM_HERE, "..", "storyboard")
_BOARD_SRC = open(os.path.join(SB, "board.py"), encoding="utf-8").read()  # 部品の中で src が上書きされるので別の名前
__file__ = os.path.abspath(os.path.join(SB, "board.py"))   # 部品の中の HERE（素材の場所）を絵コンテのフォルダにする
sys.argv = [sys.argv[0], "--", "x", "x.png"]               # board.py の頭が読む引数（使わない）
exec(_BOARD_SRC.split("\n# ---------------- 場面（台本 v1.0")[0])  # まるロボ・人・番犬・泡・部屋・電車・台などの部品
exec(_BOARD_SRC[_BOARD_SRC.index("def salesman"):_BOARD_SRC.index("def b17")])        # 会社の人（ヘッドホン・名簿）
FPS = 24

# 声の時刻（通しの秒）
VO = os.path.join(_ANIM_HERE, "..", "voice")
_P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
_L = {e["no"]: e for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
T = {_L[p["no"]]["id"]: (p["start"], p["end"]) for p in _P}
SCENE_T = {}                                                 # 場面 → (始まり, 終わり)：最初の声の 0.4 秒前で切り替える
for p in _P:
    sc_ = _L[p["no"]]["scene"]
    if sc_ not in SCENE_T: SCENE_T[sc_] = [p["start"] - 0.4, None]
_ks = list(SCENE_T)
for i, k in enumerate(_ks):
    SCENE_T[k][1] = SCENE_T[_ks[i + 1]][0] if i + 1 < len(_ks) else _P[-1]["end"] + 2.0
SCENE_T[_ks[0]][0] = 0.0
CLOCK = dict(T0=0.0)                                         # この舞台の 0 コマ目（通しの秒）


def f(t): return round((t - CLOCK["T0"]) * FPS)
def s(i, k=0): return T[i][k]


def _interp(ob, frame, interp):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5: kp.interpolation = interp


def key(ob, path, frame, value, interp="BEZIER"):
    if isinstance(path, tuple):
        p, idx = path
        getattr(ob, p)[idx] = value
        ob.keyframe_insert(p, index=idx, frame=frame)
    else:
        setattr(ob, path, value)
        ob.keyframe_insert(path, frame=frame)
    _interp(ob, frame, interp)


def show(obs, frame, on):
    for o in obs:
        o.hide_render = not on
        o.keyframe_insert("hide_render", frame=frame)
        _interp(o, frame, "CONSTANT")


def matkey(m, frame, strength=None, color=None):
    b = m.node_tree.nodes["Principled BSDF"]
    if strength is not None:
        b.inputs["Emission Strength"].default_value = strength
        b.inputs["Emission Strength"].keyframe_insert("default_value", frame=frame)
    if color is not None:
        b.inputs["Emission Color"].default_value = srgb(color)
        b.inputs["Emission Color"].keyframe_insert("default_value", frame=frame)


def lightkey(L, frame, energy):
    L.data.energy = energy
    L.data.keyframe_insert("energy", frame=frame)


def made(fn, *a, **k):
    """部品を作り、新しくできた物を全部ひとつの空の下にまとめて返す（まとめて動かす・消すため）"""
    before = set(bpy.data.objects)
    r = fn(*a, **k)
    new = [o for o in set(bpy.data.objects) - before if o.parent is None and o.type != 'CAMERA']
    e = empty((0, 0, 0))
    for o in new:
        if o is e: continue
        o.parent = e
    return e, r, list(set(bpy.data.objects) - before)


class Maru:
    """まるロボ：root（場所・向き）、body（跳ぶ・見上げる・傾く）、アンテナの光"""
    def __init__(self, loc, face, **kw):
        self.root = maru(loc, face_deg=face, **kw)
        self.body = self.root.children[0]
        self.z0 = self.body.location.z
        self.ant = bpy.data.materials["maru_orange"]
        self.lens = bpy.data.materials["maru_lens"]

    def at(self, t, loc=None, face=None, look=None, interp="BEZIER"):
        if loc is not None: key(self.root, "location", f(t), loc, interp)
        if face is not None: key(self.root, ("rotation_euler", 2), f(t), R(face), interp)
        if look is not None: key(self.body, ("rotation_euler", 0), f(t), R(-look), interp)

    def hop(self, t, h=0.3, d=0.45):
        key(self.body, ("location", 2), f(t), self.z0)
        key(self.body, ("location", 2), f(t + d / 2), self.z0 + h)
        key(self.body, ("location", 2), f(t + d), self.z0)

    def walk(self, t0, t1, a, b, face=None, h=0.06, step=0.32):
        """a から b へ歩く（小さく弾む。足音は組み立てで、この弾みの着地に付ける）"""
        self.at(t0, a, face); self.at(t1, b, face)
        n = max(1, int((t1 - t0) / step))
        for k in range(n):
            self.hop(t0 + k * step, h, step)
        STEPS.extend(t0 + (k + 1) * step for k in range(n))

    def tilt(self, t, deg, d=0.3):
        key(self.body, ("rotation_euler", 1), f(t), self.body.rotation_euler[1])
        key(self.body, ("rotation_euler", 1), f(t + d), R(deg))

    def glow(self, t, s0, s1, d=0.25):
        matkey(self.ant, f(t), strength=s0); matkey(self.ant, f(t + d), strength=s1)

    def blink(self, t, d=0.25):
        matkey(self.lens, f(t), strength=1.2); matkey(self.lens, f(t + d / 2), strength=0.0); matkey(self.lens, f(t + d), strength=1.2)


STEPS = []          # まるロボの足の着地の時刻（効果音用。描いたあとで log に書く）
EVENTS = []         # 効果音を付ける出来事（通しの秒, 種類）


def ev(t, kind):
    EVENTS.append((round(t, 3), kind))


def cam_rig(lens=35):
    cam = camera((0, -6, 2), (0, 0, 1), lens=lens)
    tgt = empty((0, 0, 1))
    tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    return cam, tgt


def shots(cam, tgt, S):
    """[(t0, t1, カメラの場所0, 見る所0, カメラの場所1, 見る所1, レンズ)]：ショットの中はなめらかに動き、境目で切り替わる"""
    for t0, t1, l0, g0, l1, g1, lens in S:
        a, b = f(t0), f(t1) - 1
        key(cam, "location", a, l0, "BEZIER"); key(tgt, "location", a, g0, "BEZIER")
        key(cam.data, "lens", a, lens, "CONSTANT")
        key(cam, "location", b, l1, "CONSTANT"); key(tgt, "location", b, g1, "CONSTANT")
