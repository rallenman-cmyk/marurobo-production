# 5本目：場面づくりの共通（scenes.py が exec で読む）。時刻・キー・まるロボと先輩の動き・描く手順
#   前提：exec する側で KIT_HERE・CLIP（t0, t1）を決めてから読む
#   4本目の anim/common.py と同じ考え方：声の置き場所（voice/placement.json）から文ごとの時刻を出し、動きを声に合わせる
import os, sys, json, math, bpy
from mathutils import Vector
VO = os.path.join(KIT_HERE, "..", "voice")
_P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
_L = {e["no"]: e for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
T, TEXT = {}, {}
for p in _P:
    i = _L[p["no"]]["id"]; T[i] = (p["start"], p["end"]); TEXT[i] = _L[p["no"]]["text"]
CLOCK = dict(T0=0.0)
STEPS, EVENTS, TRACK = [], [], {}
TRACK_ONLY = False


def s(i): return T[i][0]
def e(i): return T[i][1]
def w(i, word, end=False):
    """台詞 i の中で word を言う時刻（字数の割合で見積もる。……は短く数える）"""
    t = TEXT[i]; k = t.index(word) + (len(word) if end else 0)
    wt = lambda u: sum(0.35 if ch in "…" else (0.6 if ch in "、。？！「」　" else 1.0) for ch in u)
    return s(i) + (e(i) - s(i)) * wt(t[:k]) / max(1e-6, wt(t))


def f(t): return round((t - CLOCK["T0"]) * FPS)
def ev(t, kind, gain=1.0): EVENTS.append((round(t, 3), kind, gain))
def track(name, ob, dz=0.0): TRACK[name] = (ob, dz)


def _interp(ob, frame, interp):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5: kp.interpolation = interp


def key(ob, path, t, value, interp="BEZIER"):
    fr = f(t)
    if isinstance(path, tuple):
        p, idx = path
        getattr(ob, p)[idx] = value
        ob.keyframe_insert(p, index=idx, frame=fr)
    else:
        setattr(ob, path, value)
        ob.keyframe_insert(path, frame=fr)
    _interp(ob, fr, interp)


def emit_key(m, t, strength, interp="BEZIER"):
    nt = m.node_tree
    n = nt.nodes.get("Principled BSDF") or next(x for x in nt.nodes if x.type == 'EMISSION')
    inp = n.inputs["Emission Strength"] if n.type == 'BSDF_PRINCIPLED' else n.inputs["Strength"]
    inp.default_value = strength; inp.keyframe_insert("default_value", frame=f(t))


def alpha_key(m, t, a):
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Alpha"].default_value = a; b.inputs["Alpha"].keyframe_insert("default_value", frame=f(t))


def hide_key(ob, t, hidden):
    """t から見える／見えない（描く物ごと。子も一緒）"""
    for o in [ob] + list(ob.children_recursive):
        o.hide_render = hidden; o.keyframe_insert("hide_render", frame=f(t))
        ad = o.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                if fc.data_path == "hide_render":
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'


def show_between(ob, t0, t1=None):
    hide_key(ob, min(CLOCK["T0"], t0) - 1.0, True); hide_key(ob, t0, False)
    if t1 is not None: hide_key(ob, t1, True)


def scale_pop(ob, t, s1=1.0, d=0.3, s0=0.001):
    """ぽんと出る（0.3 秒で弾む。4本目の見た目の決まり）"""
    key(ob, "scale", t - 0.01, (s0, s0, s0)); key(ob, "scale", t + d * 0.6, (s1 * 1.12,) * 3); key(ob, "scale", t + d, (s1,) * 3)


def face_to(p, q):
    return plan.face_deg(q[0] - p[0], q[1] - p[1])


class Maru:
    """まるロボ：root（場所・向き）、body（跳ぶ・見上げる・傾く）、レンズの光"""
    S = 0.26

    def __init__(self, loc, face=0.0, glow=0.9, s=None):
        self.s = s or Maru.S
        self.root = maru(loc, face_deg=face, s=self.s, hat=False, eye_glow=glow)
        self.body = self.root.children[0]
        self.z0 = self.body.location.z
        self.lens = bpy.data.materials["maru_lens"]
        self._last = {}
        self.loc = Vector(loc); self.face = face

    def at(self, t, loc=None, face=None, look=None, interp="BEZIER", hold=True):
        for ch, v in (("loc", loc), ("face", face), ("look", look)):
            if v is None: continue
            if hold and ch in self._last and t - self._last[ch][0] > 1.0:
                th = max(self._last[ch][0], t - 0.8); self._set(ch, th, self._last[ch][1], interp)
            self._last[ch] = (t, v); self._set(ch, t, v, interp)

    def _set(self, ch, t, v, interp):
        if ch == "loc": key(self.root, "location", t, tuple(v), interp)
        elif ch == "face": key(self.root, ("rotation_euler", 2), t, R(v), interp)
        else: key(self.body, ("rotation_euler", 0), t, R(-v), interp)

    def hop(self, t, h=0.25, d=0.45, sound=True):
        z = self.z0
        key(self.body, ("location", 2), t, z); key(self.body, ("location", 2), t + d / 2, z + h); key(self.body, ("location", 2), t + d, z)
        if sound: ev(t, "jump", 0.5); ev(t + d, "land", 0.5)

    def tilt(self, t, deg, d=0.3):
        key(self.body, ("rotation_euler", 1), t, self.body.rotation_euler[1]); key(self.body, ("rotation_euler", 1), t + d, R(deg))

    def glow(self, t, g, d=0.3, g0=None):
        if g0 is not None: emit_key(self.lens, t, g0)
        else: emit_key(self.lens, t, self.lens.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value)
        emit_key(self.lens, t + d, g)

    def eyelid(self, t, closed=1.0, d=0.35):
        """まぶた（体と同じ白）を上から下ろす。closed＝0（開く）〜1（閉じる）。v3：5本目 v2「目の光を消しました → 目を閉じさせて」"""
        if not hasattr(self, "_lid"):
            piv = empty((0, -0.485, 0.04 + 0.235)); piv.parent = self.body
            lid = sphere(bpy.data.materials["maru_white"], (0, 0, -0.235), 0.238, scale=(1, 0.55, 1), parent=piv)
            piv.scale = (1, 1, 0.001); self._lid = piv
            key(piv, ("scale", 2), CLOCK["T0"] - 5, 0.001)
            # 閉じた目の線（「︶」）：閉じ終わってから出る
            seam = empty((0, -0.62, 0.04)); seam.parent = self.body
            dk = mat("lidline", "#2B3440", rough=0.5)
            for k in range(17):
                a0 = math.radians(-60 + 7.5 * k)
                o_ = cyl(dk, (0.13 * math.sin(a0), 0, -0.13 * math.cos(a0) + 0.1), 0.012, 0.022, rot=(0, R(90) + a0, 0), parent=seam)
            self._seam = seam; hide_key(seam, CLOCK["T0"] - 5, True)
        cur = self._lid.scale[2]
        key(self._lid, ("scale", 2), t, max(0.001, self._lid.get("_v", 0.001)))
        key(self._lid, ("scale", 2), t + d, max(0.001, closed)); self._lid["_v"] = max(0.001, closed)
        hide_key(self._seam, t + d if closed >= 0.99 else t, closed < 0.99)

    def blink(self, t, g=0.9, d=0.22):
        emit_key(self.lens, t, g); emit_key(self.lens, t + d / 2, 0.0); emit_key(self.lens, t + d, g)

    def walk(self, t0, t1, p1, step=0.24, turn=True, gain=0.05):
        """t0〜t1 で p1 まで歩く（向きは歩く前の 0.3 秒で変える。一歩ずつ小さく上下・足音）"""
        v3 = lambda p: Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0))
        p0 = v3(self._last["loc"][1]) if "loc" in self._last else v3(self.loc)
        p1 = v3(p1)
        if turn and (p1 - p0).length > 0.01:
            fd = face_to(p0, p1)
            cur = self._last["face"][1] if "face" in self._last else self.face
            fd = cur + ((fd - cur + 180) % 360 - 180)
            self.at(t0 - 0.35, face=cur); self.at(t0, face=fd)
        self.at(t0, loc=p0, interp="LINEAR"); self.at(t1, loc=p1, interp="LINEAR")
        n = max(1, int((t1 - t0) / step)); z = self.z0
        for k in range(n):
            ta = t0 + k * (t1 - t0) / n
            key(self.body, ("location", 2), ta, z); key(self.body, ("location", 2), ta + (t1 - t0) / n / 2, z + 0.06)
            ev(ta, "step", gain)
        key(self.body, ("location", 2), t1, z)

    def wobble(self, t0, t1, deg=10, period=0.5):
        k = 0; t = t0
        while t < t1:
            key(self.body, ("rotation_euler", 1), t, R(deg if k % 2 else -deg)); t += period / 2; k += 1
        key(self.body, ("rotation_euler", 1), t1, 0.0)


class Sp:
    """先輩：kit の senpai_* の辞書を包む。走る・回る・光の物差しを回す・ピッと光る"""
    def __init__(self, d):
        self.d = d; self.root = d["root"]; self.wh = 0.0

    def place(self, t, x, y, ang, interp="LINEAR"):
        key(self.root, ("location", 0), t, x, interp); key(self.root, ("location", 1), t, y, interp); key(self.root, ("rotation_euler", 2), t, R(ang), interp)

    def drive(self, dr, t0=None, t1=None, dt=0.125, motor=True, brush=True, wheel_scale=1.0):
        a = dr.t0 if t0 is None else t0; b = dr.t1 if t1 is None else t1
        t = a; prev = None
        while t < b + 1e-6:
            x, y, ang = dr.pose(t)
            self.place(t, x, y, ang)
            if prev is not None:
                dist = math.dist(prev[:2], (x, y)); dang = abs(ang - prev[2])
                self.wh += (dist / 0.032 + math.radians(dang) * 0.15 / 0.032) * wheel_scale
            for wl in self.d["wheels"]: key(wl, ("rotation_euler", 2), t, -self.wh * (1 if wl.parent.location.x > 0 else -1), "LINEAR")
            if brush: key(self.d["brush"], ("rotation_euler", 2), t, -t * 12.0, "LINEAR")
            prev = (x, y, ang); t += dt
        if motor: ev(a, "motor_on", 0.5); ev(b, "motor_off", 0.5)

    def spin(self, t0, t1, rps=0.5):
        if "spin" not in self.d: return
        sp = self.d["spin"]
        key(sp, ("rotation_euler", 2), t0, t0 * rps * 2 * math.pi, "LINEAR"); key(sp, ("rotation_euler", 2), t1, t1 * rps * 2 * math.pi, "LINEAR")

    def pi(self, t, n=2, gap=0.18, sound=True):
        m = self.d["led"].data.materials[0]
        for k in range(n):
            emit_key(m, t + k * gap, 2.0); emit_key(m, t + k * gap + 0.06, 9.0); emit_key(m, t + k * gap + 0.14, 2.0)
        if sound: ev(t, "pipi" if n >= 2 else "pi", 0.6)


def cam_rig(loc, target, lens=35):
    """カメラと、見る点（empty）。両方にキーを打てる"""
    c = camera(loc, target, lens)
    tg = empty(target)
    con = c.constraints.new('TRACK_TO'); con.target = tg; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    return c, tg


def cam_top(loc, lens=30):
    """真上から見下ろすカメラ（上＝奥。回らないように、向きは固定して場所だけ動かす）"""
    bpy.ops.object.camera_add(location=loc, rotation=(0, 0, 0)); c = bpy.context.object; c.data.lens = lens
    bpy.context.scene.camera = c
    return c


def cam_top_move(c, t0, t1, loc0, loc1, interp="BEZIER"):
    key(c, "location", t0, loc0, interp); key(c, "location", t1, loc1, interp)


def cam_follow(target, offset, look_dz=0.03, lens=40):
    """動く物に、横からついていくカメラ（世界の向きで offset だけ離れる）"""
    hold = empty((0, 0, 0)); con = hold.constraints.new('COPY_LOCATION'); con.target = target
    bpy.ops.object.camera_add(location=(0, 0, 0)); c = bpy.context.object; c.data.lens = lens; c.parent = hold; c.location = offset
    tg = empty((0, 0, 0)); con2 = tg.constraints.new('COPY_LOCATION'); con2.target = target
    tg2 = empty((0, 0, look_dz)); tg2.parent = tg
    tt = c.constraints.new('TRACK_TO'); tt.target = tg2; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
    bpy.context.scene.camera = c
    return c


def cam_move(c, tg, t0, t1, loc0, loc1, tgt0=None, tgt1=None, lens0=None, lens1=None, interp="BEZIER"):
    key(c, "location", t0, loc0, interp); key(c, "location", t1, loc1, interp)
    if tgt0 is not None: key(tg, "location", t0, tgt0, interp); key(tg, "location", t1, tgt1 if tgt1 is not None else tgt0, interp)
    if lens0 is not None:
        c.data.lens = lens0; c.data.keyframe_insert("lens", frame=f(t0)); c.data.lens = lens1; c.data.keyframe_insert("lens", frame=f(t1))


def dof(c, target_ob, fstop=4.0):
    c.data.dof.use_dof = True; c.data.dof.focus_object = target_ob; c.data.dof.aperture_fstop = fstop


def render_clip(name, t0, t1, outdir, samples, res, step, fr=None, stills=None):
    sc = bpy.context.scene
    render_settings(samples, res)
    if "--fast" in sys.argv:   # PC の本番：光の跳ね返りを減らす（見た目はほぼ同じで速い。SKILL「PC の本番描画は速い設定で描く」2026-11-15）
        c = bpy.context.scene.cycles
        c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = 3, 1, 1, 2, 4
    n = round((t1 - t0) * FPS)
    sc.frame_start, sc.frame_end = 0, max(0, n - 1)
    os.makedirs(outdir, exist_ok=True)
    from bpy_extras.object_utils import world_to_camera_view
    track = {k: [] for k in TRACK}
    for k in range(0, n, 2):
        sc.frame_set(k)
        for nm, (ob, dz) in TRACK.items():
            p = world_to_camera_view(sc, sc.camera, ob.matrix_world.translation + Vector((0, 0, dz)))
            track[nm].append([k, round(p.x * 1280, 1), round((1 - p.y) * 720, 1), round(p.z, 2)])
    json.dump(dict(t0=t0, t1=t1, fps=FPS, frames=n, step=step, events=sorted(EVENTS), track=track), open(os.path.join(outdir, name + "_log.json"), "w"))
    if TRACK_ONLY: return
    if "--video" in _argv or "--gpu" in _argv:      # PC の本番（pc_out.py：グラフィックボード・mp4）
        exec(open(os.path.join(KIT_HERE, "pc_out.py"), encoding="utf-8").read(), {"_argv": _argv, "sc": sc})
    if "--video" in _argv:
        a, b = (fr if fr else (0, n - 1))
        sc.frame_start, sc.frame_end = a, min(b, n - 1)
        sc.render.filepath = os.path.join(outdir, name + "_")
        bpy.ops.render.render(animation=True)
        return
    if stills:
        frames = [round((t - t0) * FPS) for t in stills]
    else:
        a, b = (fr if fr else (0, n - 1))
        frames = list(range(a, b + 1, step))
    for k in frames:
        sc.frame_set(k)
        sc.render.filepath = os.path.join(outdir, "%s_%05d.png" % (name, k))
        bpy.ops.render.render(write_still=True)
