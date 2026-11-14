# ロボットではありません回：3D を声の時刻に合わせて動かす共通の部品（scenes.py が exec で読む）
#   絵コンテの board.py（部品・場面のカメラ）と rich.py（作り込んだ舞台）をそのまま読み、まるロボ・マウス・画面に動きを付ける
#   前提：exec する側で ARGS・_ANIM_HERE・TEX を決めてから読む
import os, sys, json, math, bpy
SB = os.path.join(_ANIM_HERE, "..", "storyboard")
_BOARD = open(os.path.join(SB, "board.py"), encoding="utf-8").read()
__file__ = os.path.abspath(os.path.join(SB, "board.py"))
sys.argv = [sys.argv[0], "--", "b01", "x.png", "8", "--tex", TEX]
exec(_BOARD.split("\nif RICH:\n")[0])                      # 部品と場面（room_shot・b04a など）
exec(open(os.path.join(SB, "rich.py"), encoding="utf-8").read())   # 作り込んだ舞台に差し替える
bpy.ops.wm.read_factory_settings(use_empty=True)      # 最初からある立方体などを消す（消さないと机の前に白い箱が出る）
FPS = 24

VO = os.path.join(_ANIM_HERE, "..", "voice")
_P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
_L = {e["no"]: e for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
T = {}
for p in _P: T.setdefault(_L[p["no"]]["id"], (p["start"], p["end"]))
SCENE_T = {}
for p in _P:
    sc_ = _L[p["no"]]["scene"]
    if sc_ not in SCENE_T: SCENE_T[sc_] = [p["start"] - 0.4, None]
_ks = list(SCENE_T)
for i, k in enumerate(_ks):
    SCENE_T[k][1] = SCENE_T[_ks[i + 1]][0] if i + 1 < len(_ks) else _P[-1]["end"] + 2.0
SUBS = json.load(open(os.path.join(_ANIM_HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
CLOCK = dict(T0=0.0)


def f(t): return round((t - CLOCK["T0"]) * FPS)
def s(i, k=0): return T[i][k]
def said(text, after=0.0):
    """字幕の札の頭の時刻（分けた字幕の 2 枚目など、言葉を言う瞬間に使う）"""
    for a, c, t in SUBS:
        if a >= after and t.replace("\\N", "").startswith(text): return a
    raise KeyError(text)


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


def matkey(m, frame, strength=None):
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Emission Strength"].keyframe_insert("default_value", frame=frame)


STEPS, EVENTS = [], []
TRACK = {}          # 名前 → (物, 上へのずれ)：コマごとの画面の場所を log に書く（2D の札のしっぽを向けるため。1280×720 の座標）
def ev(t, kind, gain=1.0): EVENTS.append((round(t, 3), kind, gain))


class Maru:
    """まるロボ：root（場所・向き）、body（跳ぶ・見上げる・傾く）、アンテナとレンズの光"""
    def __init__(self, root):
        self.root = root
        self.body = root.children[0]
        self.z0 = self.body.location.z
        self.lens = bpy.data.materials["maru_lens"]
        self._last = {}

    def at(self, t, loc=None, face=None, look=None, interp="BEZIER", hold=True):
        # 前のキーから 1 秒以上離れているときは、動き出す 0.8 秒前まで前の場所・向きで止めておく（ゆっくり回り続けない）
        for ch, v in (("loc", loc), ("face", face), ("look", look)):
            if v is None: continue
            if hold and ch in self._last and t - self._last[ch][0] > 1.0:
                th = max(self._last[ch][0], t - 0.8); pv = self._last[ch][1]
                self._set(ch, th, pv, interp)
            self._last[ch] = (t, v)
            self._set(ch, t, v, interp)

    def _set(self, ch, t, v, interp):
        if ch == "loc": key(self.root, "location", f(t), v, interp)
        elif ch == "face": key(self.root, ("rotation_euler", 2), f(t), R(v), interp)
        else: key(self.body, ("rotation_euler", 0), f(t), R(-v), interp)

    def hop(self, t, h=0.3, d=0.45, base=None):
        z = self.z0 if base is None else base
        key(self.body, ("location", 2), f(t), z)
        key(self.body, ("location", 2), f(t + d / 2), z + h)
        key(self.body, ("location", 2), f(t + d), z)

    def z(self, t, v):
        key(self.body, ("location", 2), f(t), self.z0 + v)

    def tilt(self, t, deg, d=0.3):
        key(self.body, ("rotation_euler", 1), f(t), self.body.rotation_euler[1])
        key(self.body, ("rotation_euler", 1), f(t + d), R(deg))

    def glow(self, t, s0, s1, d=0.3):
        matkey(self.lens, f(t), s0); matkey(self.lens, f(t + d), s1)

    def blink(self, t, g=0.9, d=0.25):
        matkey(self.lens, f(t), g); matkey(self.lens, f(t + d / 2), 0.0); matkey(self.lens, f(t + d), g)


def seq_screen(scr_obj, folder, prefix):
    """画面の板に、コマごとの絵（<folder>/<prefix>_0001.png〜）を貼る。0 コマ目＝1 枚目"""
    import glob
    fs = sorted(glob.glob(os.path.join(folder, prefix + "_*.png")))
    im = bpy.data.images.load(fs[0]); im.source = 'SEQUENCE'
    m = bpy.data.materials.new("seq_" + prefix); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = im; tx.image_user.frame_duration = len(fs); tx.image_user.frame_start = 0; tx.image_user.use_auto_refresh = True
    nt.links.new(tx.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.8
    nt.links.new(em.outputs[0], out.inputs[0])
    scr_obj.data.materials.clear(); scr_obj.data.materials.append(m)


def render(name, t0, t1, outdir, samples, res, step, fr=None):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.cycles.device = os.environ.get("CYCLES_DEVICE", "CPU")
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
    sc.render.fps = FPS
    sc.render.use_persistent_data = True          # コマごとに舞台を作り直さない（速くなる）
    n = round((t1 - t0) * FPS)
    if not fr and os.environ.get("FR"): fr = tuple(int(x) for x in os.environ["FR"].split())   # 試し：FR="48 48" でそのコマだけ
    a, b = (fr if fr else (0, n - 1))
    os.makedirs(outdir, exist_ok=True)
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    track = {k: [] for k in TRACK}
    for k in range(0, n):
        sc.frame_set(k)
        for nm, (ob, dz) in TRACK.items():
            p = world_to_camera_view(sc, sc.camera, ob.matrix_world.translation + Vector((0, 0, dz)))
            track[nm].append([round(p.x * 1280), round((1 - p.y) * 720)])
    json.dump(dict(t0=t0, t1=t1, fps=FPS, frames=n, steps=STEPS, events=EVENTS, track=track), open(os.path.join(outdir, name + "_log.json"), "w"))
    if TRACK_ONLY: return
    for k in range(a, b + 1, step):
        sc.frame_set(k)
        sc.render.filepath = os.path.join(outdir, "%s_%04d.png" % (name, k))
        bpy.ops.render.render(write_still=True)
