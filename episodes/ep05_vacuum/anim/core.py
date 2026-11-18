# 5本目：場面づくりの共通（scenes.py が exec で読む）。時刻・キー・まるロボと先輩の動き・描く手順
#   前提：exec する側で KIT_HERE・CLIP（t0, t1）を決めてから読む
#   4本目の anim/common.py と同じ考え方：声の置き場所（voice/placement.json）から文ごとの時刻を出し、動きを声に合わせる
import os, sys, json, math, bpy
from mathutils import Vector, Matrix
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
def track(name, ob, dz=0.0, box=False):
    """2D の札をつける物。box=True なら、物（と子）の形の角を画面に写した外接の箱も記録する（name#box）。
    赤い枠・輪は、中心と決まった大きさで描くとずれる（5本目 v4「赤い枠はちゃんと先輩の形で囲って」「カメラのまるの位置ズレてる」）"""
    TRACK[name] = (ob, dz)
    if box: TRACK_BOX[name] = ob


TRACK_BOX = {}
START_SE_FROM = [1e9]    # scenes.py が入れる（カメラの先輩が出る 18 章の頭）


def _screen_box(sc, ob):
    from bpy_extras.object_utils import world_to_camera_view
    xs, ys, zs = [], [], []
    for o in [ob] + list(ob.children_recursive):
        if o.type != 'MESH' or o.hide_render: continue
        for c in o.bound_box:
            p = world_to_camera_view(sc, sc.camera, o.matrix_world @ Vector(c))
            xs.append(p.x * 1280); ys.append((1 - p.y) * 720); zs.append(p.z)
    if not xs: return None
    return [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1), round(min(zs), 2)]


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


# ---------------------------------------------------------------- まるロボ（本物の体・決まりどおりの動き）
# 2026-11-17 ユーザー「描画を止めて直す」：3本目の絵コンテ用の簡単な体（maru()）と、体を滑らせる歩きをやめた。
#   体：共通の maru_real.py（PC は story.blend の本物、クラウドは同じ寸法の代わりの体）
#   動き：共通の maru_cmds.py（前の書き方の命令をためて、marumotion の予定に並べ、marurig で毎コマ当てる）。references/maru_walk.md
#   5本目だけの足し：置き場所の親を動かす跳び（机から降りる・先輩に乗る・段差で落ちる・うんちから跳ぶ）とぶつかり、
#   早回し（予定をゆっくり作って速く流す）、レンズの光、まぶた、足音の大きさ
def _maru_paths():
    here = os.path.dirname(os.path.abspath(KIT_HERE + "/core.py"))
    # 共通の道具（skill/scripts）をいちばん先に読む。ep01 の stage/maru にも marumotion.py の古い写しがあり、
    #   先に読むと 6本目以降で足した動き（lie_side・get_up など）がない（marurig.py だけ ep01 から読む）
    for d in (here, os.path.join(here, "..", "..", "ep01_earphone", "stage", "maru"),
              os.path.join(here, "..", "..", "..", "skill", "marurobo-video-production", "scripts")):
        d = os.path.abspath(d)
        if os.path.isdir(d):
            if d in sys.path: sys.path.remove(d)
            sys.path.insert(0, d)


_maru_paths()
import maru_cmds as MC
import marumotion as MM

STEP_GAIN = [0.5]          # 足音（共通の maru_sfx の step。予定の一歩ずつ）
MARU_GAIN = 0.6            # 動きの電子音・跳ぶ音（共通の maru_sfx）
MARUS = []


class Maru(MC.Maru):
    S = 0.26

    def __init__(self, loc, face=0.0, glow=0.9, s=None):
        s = s or Maru.S
        z = loc[2] if len(loc) > 2 else 0.0
        MC.Maru.__init__(self, (loc[0], loc[1], z), face, s=s, face_offset=180, name="maru%d" % len(MARUS))
        self.loc = Vector((loc[0], loc[1], z)); self.face = face; self._last = {}
        self.g_ref = glow; self.offs = [(-1e9, Vector((0.0, 0.0, z)))]      # 置き場所の親のずれ（時刻, 世界の位置）
        self.warps = []; self.nosound = []; self.layers05 = []; self.mutes = []
        self.lens = self._find_mat(("Optical blue", "Maru lens"))
        self.white = self._find_mat(("Porcelain", "Maru white"))
        MARUS.append(self)

    # ---- 部品さがし
    def _find_mat(self, keys):
        for o in [self.root] + list(self.root.children_recursive):
            if o.type != 'MESH': continue
            for m in o.data.materials:
                if m and any(m.name.startswith(k) for k in keys): return m
        return None

    # ---- 置き場所の親のずれ
    def poff(self, t):
        return [v for (tt, v) in self.offs if tt <= t + 1e-6][-1]

    def _rel(self, t, p):
        o = self.poff(t); return (p[0] - o.x, p[1] - o.y)

    def move_parent(self, t0, t1, dp, h=0.0, dz=0.0, rot=None):
        """置き場所の親を、t0〜t1 で dp（世界の xy）・dz だけ動かす（h：途中の山の高さ）。rot：親の回転 (x, y, z) 度"""
        par = self.handle.parent; a = self.poff(t0); b = a + Vector((dp[0], dp[1], dz))
        key(par, "location", t0, tuple(a), "LINEAR")
        if h: key(par, "location", (t0 + t1) / 2, tuple((a + b) / 2 + Vector((0, 0, h))))
        key(par, "location", t1, tuple(b), "LINEAR" if not h else "BEZIER")
        if rot is not None:
            key(par, "rotation_euler", t0, tuple(par.rotation_euler)); key(par, "rotation_euler", t1, tuple(R(v) for v in rot))
        self.offs.append((t1, b)); self.offs.sort(key=lambda x: x[0])

    def jump(self, t, p_from, p_to, z_to=None, apex=None, **_):
        """p_from（世界）まで歩いておき、t に一覧の jump_to（見る→向く→しゃがむ→蹴る→放物線→脚で受け止める）で p_to へ。
        z_to：着く所の高さ（世界）。台に跳び乗る・机から跳び降りる"""
        self.at(t - 0.05, loc=p_from)
        z1 = (z_to if z_to is not None else self.poff(t).z) - self.poff(t).z
        self.cmds.append((t, "jump", dict(p=self._rel(t, p_to), z1=z1, apex=apex)))     # apex：出発より何 m 上がるか（世界。None なら一覧の決まり）

    def act(self, t, kind, **kw):
        """一覧（references/maru_motions.md）の部品を、そのまま呼ぶ（lie_side・get_up など）"""
        self.cmds.append((t, kind, kw))

    def teleport(self, t, loc, face):
        """カットで置き直す（画面に映っていない所でだけ。一覧の teleport）"""
        self.cmds.append((t, "teleport", dict(pos=self._pp(self._rel(t, loc)), heading=face + self.off)))

    def eyes_closed(self, t0, t1):
        """目を閉じたまま（目の内側の輪を、まばたきで閉じた形に保つ。一覧の blink のチャンネル）"""
        self.layers05.append((t0, t1, lambda t: {"blink": 1.0}))

    def mute(self, t0, t1):
        """この間の動きの電子音を鳴らさない（同じ所に、場面で決めた音があるとき）"""
        self.mutes.append((t0, t1))

    # ---- 前の書き方
    def at(self, t, loc=None, face=None, look=None, interp=None, hold=None, **_):
        if loc is not None:      # 場所と向きを一緒に言われたら、着いてからその向きへ（前の書き方）
            self.cmds.append((t, "go", dict(p=self._rel(t, loc), end_face=face)))
            if look is not None: MC.Maru.at(self, t, look=look)
        else:
            MC.Maru.at(self, t, face=face, look=look)

    def walk(self, t0, t1, p1, step=None, turn=True, gain=None, speeds=None, **_):
        if speeds == "run": self.cmds.append((t1, "move", dict(p=self._rel(t1, p1), how="run_to")))     # 走って着く（共通の部品の run）
        else: MC.Maru.walk(self, t0, t1, self._rel(t1, p1))

    def hop(self, t, h=0.25, d=0.45, sound=True):
        MC.Maru.hop(self, t, h=h, d=d)
        if not sound: self.nosound.append(t)

    def fast(self, t0, t1, slow):
        """t0〜t1 を早回しにする：予定はこの間を slow 倍の長さで作り、絵では速く流す（歩く速さの決まりは守ったまま）"""
        self.warps.append((t0, t1, slow))

    def route_fast(self, ts, te, pts):
        """早回しで pts を順に歩く：本当の速さの歩きで何秒かかるかを先に測り、ts〜te に入るように速く流す"""
        q = MM.Plan(pos=self._pp(self._rel(ts, pts[0])), heading=0.0); q.turn_to(math.degrees(math.atan2(-(pts[1][0] - pts[0][0]), pts[1][1] - pts[0][1])) % 360)
        tk = []
        for pt in pts[1:]: q.walk_to(self._pp(self._rel(ts, pt))); tk.append(q.t)
        k = max(1.0, q.t / (te - ts) * 1.03)
        self.fast(ts, te, k)
        for pt, ti in zip(pts[1:], tk): self.cmds.append((ts + ti / k, "go", dict(p=self._rel(ts, pt))))
        return [ts + ti / k for ti in tk]          # 各点に着く時刻（場面の時刻）

    def glow(self, t, g, d=0.3, g0=None):
        """レンズ（目）の光。g は前の書き方の強さ（作ったときの glow が 1 倍）"""
        m = self.lens
        if m is None: return
        nd = m.node_tree.nodes.get("Principled BSDF")
        inp = nd.inputs["Emission Strength"] if nd else [n for n in m.node_tree.nodes if n.type == 'EMISSION'][0].inputs["Strength"]
        if not hasattr(self, "_lens0"): self._lens0 = inp.default_value; self._lens_cur = 1.0
        if g0 is not None: self._lens_cur = g0 / self.g_ref
        inp.default_value = self._lens0 * self._lens_cur; inp.keyframe_insert("default_value", frame=f(t))
        self._lens_cur = g / self.g_ref
        inp.default_value = self._lens0 * self._lens_cur; inp.keyframe_insert("default_value", frame=f(t + d))

    # ---- 毎コマにする
    def _W(self, t):
        """場面の時刻 → 予定の時刻（早回しの間は slow 倍にのばす）"""
        x = t
        for a, b, k in sorted(self.warps):
            if t > a: x += (min(t, b) - a) * (k - 1)
        return x

    def bake05(self, t_end):
        T0b = min([CLOCK["T0"]] + [c[0] for c in self.cmds]) - 1.0
        keep = self.cmds
        self.cmds = [(self._W(t), k, a) for (t, k, a) in keep]
        p = self.plan(self._W(t_end), self._W(T0b)); self.cmds = keep
        W0_ = self._W(T0b)
        for a_, b_, fn_ in self.layers05: p.layer(self._W(a_) - W0_, self._W(b_) - W0_, fn_)
        if os.environ.get("DBG_MARU"):
            for c in sorted(keep, key=lambda c: c[0]): print("DBGCMD %.2f %s %s" % (c[0], c[1], {k: (tuple(round(x, 2) for x in v) if isinstance(v, tuple) else v) for k, v in c[2].items()}))
        pf = MM.simulate(p, fps=FPS, t_end=p.t)
        n = round((t_end - T0b) * FPS) + 1; W0 = self._W(T0b)
        frames = [pf[min(len(pf) - 1, max(0, round((self._W(T0b + i / FPS) - W0) * FPS)))] for i in range(n)]
        self.handle.bake(frames, f0=f(T0b))
        self.evs = []
        inv = lambda x: next((T0b + i / FPS for i in range(n) if self._W(T0b + i / FPS) - W0 >= x - 1e-6), None)
        for e_ in p.events:
            ts = inv(e_["t"])
            self.evs.append((ts, e_["kind"]))       # 焼いたあとに使う（跳んで着いた時刻など。カットより後は None）
            if ts is None: continue          # v6：このカットの終わりより後の音は、ここでは付けない（前は終わりの時刻にまとめて付いていた）
            if any(a <= ts <= b for a, b, _ in self.warps): continue           # 早回しの間は音なし
            k_ = e_["kind"]; g_ = e_.get("strength", 1.0)
            if k_ in ("step", "step_turn"):
                ev(ts, "maru:" + k_, STEP_GAIN[0] * min(1.5, g_)); continue
            if any(abs(ts - t_) < 0.6 for t_ in self.nosound) and k_ in ("takeoff", "land"): continue
            if any(a <= ts <= b for a, b in self.mutes): continue
            ev(ts, "maru:" + k_, MARU_GAIN * min(1.5, g_))                    # 一覧の動きの音（共通の maru_sfx）
        self.p = p


AFTER_BAKE = []          # 焼いたあとに呼ぶ（まるロボの入れかえを、跳んで着いた本当の時刻に合わせる など）


def maru_bake_all(t_end):
    MC.LATE.clear()
    for m in MARUS: m.bake05(t_end)
    for fn in AFTER_BAKE: fn()
    if MC.LATE: print("【まるロボ】間に合わなかった動き（秒）：", MC.LATE)


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
        # v4「先輩 2 人の動き始めるときの SE を分けたら、どっちか分かりやすい」（候補 C）：カメラの先輩が出てから（START_SE_FROM）、
        #   止まっていた先輩が動き出す所で、光の物差し＝上がる 3 音／カメラ＝下がる 3 音。続けて走る区間（すき間 0.5 秒未満）では鳴らさない
        kind = self.d.get("kind")
        if kind in ("lidar", "camera") and a >= START_SE_FROM[0] and a - getattr(self, "_drive_end", -99) > 0.5:
            ev(a, "start_" + kind, 0.45)
        self._drive_end = b

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
        if os.environ.get("DBG_LOC"):
            for nm in os.environ["DBG_LOC"].split(","):
                if nm in TRACK: print("DBG", k, nm, tuple(round(v, 3) for v in TRACK[nm][0].matrix_world.translation))
        for nm, ob in TRACK_BOX.items():
            bx = _screen_box(sc, ob)
            if bx: track.setdefault(nm + "#box", []).append([k] + bx)
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
