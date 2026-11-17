# 本物のまるロボ（1本目の story.blend の「Maru」）を、1本目・2本目と同じ道具で動かす（3本目 v10 から）
#   2026-11-17 ユーザー「歩き方全然違うって」「1本目の動画の時はできてたよ」→ 決まり references/maru_walk.md のとおりにする
#     ・動き：skill/.../scripts/marumotion.py の予定（Plan）。歩く・向く・見る・跳ぶ・驚く…を、声の時刻に合わせて並べる
#     ・3D に当てる：episodes/ep01_earphone/stage/maru/marurig.py（MaruRig・Baker）。体を床の上で滑らせない・足を手で打たない
#     ・体：PC では story.blend の本物（環境変数 MARU_STORY か、C:\marurobo の決まった場所）。
#           クラウドの試しでは、部品一覧 maru_parts.txt と同じ名前・場所・大きさの代わりの体（形は簡単）
#   場面の書き方は前と同じ：mr = Maru(場所, 向き, s=大きさ, hat=…)、mr.at(t, loc=, face=, look=)、mr.walk(t0, t1, a, b)、mr.hop(t) …
#     → 命令をためておき、場面を作り終えたら bake_all() が時刻の順に予定へ並べて、毎コマの姿勢を打つ
#   向き（face）は前と同じ 3本目の向き（前が −Y のときの角度）。本物の前は +Y なので、予定の向き＝face＋180
import copy, glob, json, math, os, sys
import bpy
from mathutils import Vector, Matrix, Euler

_SK = os.path.join(_ANIM_HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts")
_RG = os.path.join(_ANIM_HERE, "..", "..", "ep01_earphone", "stage", "maru")
for _d in (_ANIM_HERE, _RG, _SK):                      # 一式（PC）では anim に marumotion.py・marurig.py を入れる
    if os.path.isdir(_d) and _d not in sys.path: sys.path.insert(0, _d)
import marumotion as mm
import marurig

STORY_CANDIDATES = [os.environ.get("MARU_STORY", ""), r"C:\marurobo\bluetooth_handoff_restored\output\story.blend",
                    r"C:\marurobo\bluetooth_handoff_restored\story.blend", r"C:\marurobo\story.blend"]
LATE = []          # 間に合わなかった動き（名前, 遅れた秒）


# ---------------------------------------------------------------- 体を用意する
def _hier(o):
    out = [o]
    for c in o.children: out += _hier(c)
    return out


def _load_story(path):
    with bpy.data.libraries.load(path, link=False) as (src, dst): dst.objects = [n for n in src.objects]
    loaded = [o for o in dst.objects if o is not None]
    root = next(o for o in loaded if o.name.startswith("Maru") and o.parent is None and o.type == "EMPTY" and "•" not in o.name and "cargo" not in o.name)
    keep = set(_hier(root))
    for o in loaded:
        if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
    for o in keep:
        bpy.context.scene.collection.objects.link(o)
        if o.animation_data: o.animation_data_clear()
    return root


def _mat(name, col, rough=0.4, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(col); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = srgb(col); b.inputs["Emission Strength"].default_value = emit
    return m


def _standin():
    """部品一覧（maru_parts.txt）と同じ名前・親・場所・回転・大きさの、簡単な形の代わりの体"""
    M = dict(Porcelain=_mat("Porcelain", "#F2F1EC", 0.25, coat=0.5), Graphite=_mat("Graphite", "#2A3134", 0.35, 0.4),
             Rubber=_mat("Rubber", "#2F8C86", 0.6), Titanium=_mat("Titanium", "#B9C0C4", 0.3, 0.8),
             **{"Petrol aluminium": _mat("Petrol aluminium", "#1F5F66", 0.35, 0.6), "Optical blue": _mat("Optical blue", "#2FC4C0", 0.08, emit=1.2, coat=1.0),
                "Cyan": _mat("Cyan", "#7FF3F0", 0.2, emit=2.0), "Amber status": _mat("Amber status", "#FA7A1F", 0.3, emit=1.6),
                "Brass": _mat("Brass", "#B88A3A", 0.3, 0.9), "Ceramic seam": _mat("Ceramic seam", "#C9C6BE", 0.4), "White markings": _mat("White markings", "#FFFFFF", 0.4)})
    objs = {}
    lines = [json.loads(l[4:]) for l in open(os.path.join(_ANIM_HERE, "maru_parts.txt"), encoding="utf-8") if l.startswith("OBJ ")]
    for d in lines:
        n = d["name"]; base = n.split(".")[0]; m = M.get(d["mats"][0]) if d["mats"] else None
        if d["type"] == "EMPTY":
            o = bpy.data.objects.new(n, None); o.empty_display_size = 0.05
        else:
            if base in ("Ivory ceramic body", "Eye lens", "Lens black housing", "Ankle", "Antenna light"):
                bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24)
            elif base == "Inner lens ring":
                bpy.ops.mesh.primitive_torus_add(major_radius=0.145, minor_radius=0.014)
            elif base == "Shin":
                bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.27, vertices=32)
            elif base == "Antenna stem":
                bpy.ops.mesh.primitive_cylinder_add(radius=0.017, depth=0.585, vertices=16)
            elif base in ("Soft boot", "Boot sole"):
                bpy.ops.mesh.primitive_cube_add(size=1.0)
                o = bpy.context.object; h = 0.16 if base == "Soft boot" else 0.04
                o.data.transform(Matrix.Diagonal((0.27, 0.40, h, 1.0)))
                bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.05 if base == "Soft boot" else 0.015; bv.segments = 4
            else:                                         # 荷台・荷物・飾り：使わない（あとで消す）
                bpy.ops.mesh.primitive_cube_add(size=0.05)
            o = bpy.context.object; o.name = n
            if m: o.data.materials.append(m)
            for p in getattr(o.data, "polygons", []): p.use_smooth = True
            for c in o.users_collection: c.objects.unlink(o)
        bpy.context.scene.collection.objects.link(o)
        objs[n] = o
    for d in lines:
        o = objs[d["name"]]
        if d["parent"]: o.parent = objs[d["parent"]]
        o.location = d["loc"]; o.rotation_euler = d["rot"]; o.scale = d["scl"]
        if d["name"].startswith("Antenna stem"):            # 根元→先の玉の向きにそろえる（一覧の回転は元の形の向き）
            o.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((-0.13, 0, 0.57)).normalized()).to_euler()
    root = objs["Maru"]; root.location = (0, 0, 0); root.rotation_euler = (0, 0, 0)
    return root


def new_maru():
    for p in STORY_CANDIDATES:
        if p and os.path.exists(p):
            print("【まるロボ】本物：", p); return _load_story(p), True
    print("【まるロボ】代わりの体（クラウドの試し）"); return _standin(), False


def _drop_cradle(root):
    """荷台と荷物は 3本目では使わない：消す（MaruRig は荷台がなければ使わない）"""
    names = set()
    for o in _hier(root):
        if "cradle" in o.name.lower() or o.name.startswith(("Maru cargo", "Cradle", "Static / Brass", "Static / Cyan", "Static / Graphite.003", "Static / White markings.005")):
            names |= {c.name for c in _hier(o)}
    for n in names:
        o = bpy.data.objects.get(n)
        if o is not None: bpy.data.objects.remove(o, do_unlink=True)


def _hat(torso):
    """探偵の帽子（3本目の帽子と同じ形・柄）。本物の頭のてっぺん（胴の中心から 0.49）に合わせる。前は +Y"""
    plaid = checker_mat("hat_plaid", "#B88A55", "#8A6239", 9); band = mat("hat_band", "#5B3B22", rough=0.6)
    he = empty((0, 0, 0)); he.parent = torso; he.location = (0, -0.03, 0.40); he.rotation_euler = (R(8), 0, 0)
    he.scale = (1.02, 0.93, 1.0)                           # 体（0.51×0.46）に合わせて少し横長
    parts = [sphere(plaid, (0, 0, 0.02), 0.35, scale=(1, 1.02, 0.7), parent=he), cyl(band, (0, 0, -0.03), 0.352, 0.07, parent=he)]
    for sy, ang in ((1, 18), (-1, -18)):
        parts.append(cyl(plaid, (0, sy * 0.40, -0.03), 0.2, 0.03, rot=(R(ang), 0, 0), scale=(1.05, 0.62, 1), parent=he))
    for sx in (-1, 1): parts.append(sphere(plaid, (sx * 0.3, 0, -0.02), 0.1, scale=(0.35, 1, 1.1), parent=he))
    parts.append(sphere(band, (0, 0, 0.26), 0.05, scale=(1.6, 0.8, 0.8), parent=he))
    return he, parts


# ---------------------------------------------------------------- まるロボ（命令をためて、最後に予定にする）
class Maru:
    ALL = []

    def __init__(self, loc, face, s=1.0, hat=True, eye_glow=1.2, look_up=0.0, **_):
        self.s = s
        self.holder = empty((0.0, 0.0, loc[2] if len(loc) > 2 else 0.0)); self.holder.scale = (s, s, s); self.holder.name = "Maru holder"
        self.root, self.real = new_maru(); _drop_cradle(self.root)
        self.root.parent = self.holder
        H = _hier(self.root); fnd = lambda pred: next((o for o in H if pred(o)), None)
        self.torso = fnd(lambda o: o.name.endswith("• torso")); self.body = self.torso
        self.antenna = fnd(lambda o: "• antenna" in o.name)
        self.antenna_objs = [o for o in _hier(self.antenna) if o.type == "MESH"] if self.antenna else []
        lens_o = fnd(lambda o: o.name.startswith("Eye lens"))
        self.lens = None
        if lens_o and lens_o.data.materials:
            m = lens_o.data.materials[0].copy(); m.name = "maru_lens"; lens_o.data.materials[0] = m; self.lens = m
            b = m.node_tree.nodes.get("Principled BSDF")
            if b and not self.real: b.inputs["Emission Strength"].default_value = eye_glow
        self.ant = None                                      # 光は予定の light で動かす（glow）
        self.hat_e, self.hat_parts = _hat(self.torso) if hat else (None, [])
        self.z0 = 0.0
        self.cmds = []; self.p0 = (loc[0] / s, loc[1] / s); self.h0 = face + 180.0; self.look0 = look_up
        self._last = {}
        Maru.ALL.append(self)

    # ---- 命令（時刻は場面の時刻＝声の時刻）
    def at(self, t, loc=None, face=None, look=None, **_):
        if loc is not None: self.cmds.append((t, "go", dict(p=(loc[0], loc[1]))))
        if face is not None and loc is None: self.cmds.append((t, "face", dict(face=face)))
        if look is not None: self.cmds.append((t, "look", dict(pitch=look)))

    def walk(self, t0, t1, a, b, face=None, end_face=None, **_):
        self.cmds.append((t1, "go", dict(p=(b[0], b[1]), end_face=end_face)))

    def hop(self, t, h=0.3, d=0.45): self.cmds.append((t, "hop", dict(h=h)))
    def tilt(self, t, deg, d=0.3): self.cmds.append((t, "roll", dict(deg=deg, d=d)))
    def lean(self, t, deg, d=0.3): self.cmds.append((t, "pitch", dict(deg=deg, d=d)))
    def glow(self, t, s0, s1=None, d=0.25): self.cmds.append((t, "light", dict(v=(s1 if s1 is not None else s0), d=d)))
    def blink(self, t, d=0.25): self.cmds.append((t, "blink", {}))
    def surprise(self, t): self.cmds.append((t, "surprise", {}))
    def nod(self, t, n=2): self.cmds.append((t, "nod", dict(n=n)))
    def shake(self, t): self.cmds.append((t, "shake", {}))
    def think(self, t, dur=2.2): self.cmds.append((t, "think", dict(dur=dur)))
    def peer(self, t, dur=1.6): self.cmds.append((t, "peer", dict(dur=dur)))
    def sigh(self, t): self.cmds.append((t, "sigh", {}))
    def look_around(self, t): self.cmds.append((t, "look_around", {}))

    # ---- 予定にする
    def _pp(self, p): return (p[0] / self.s, p[1] / self.s)

    def _wait_to(self, p, tau, name):
        if tau < p.t - 1e-6: LATE.append((name, round(p.t - tau, 2)))
        gap = tau - p.t
        if gap > 3.2: p.idle(gap - 0.4, shifts=True, glance=True)
        p.wait(max(0.0, tau - p.t))

    def plan(self, t_end):
        T0_ = CLOCK_T0()
        p = mm.Plan(pos=self.p0, heading=self.h0)
        if self.look0: p.look(0, self.look0, hold=0.0, at=0.0)
        for t, kind, a in sorted(self.cmds, key=lambda c: c[0]):
            tau = t - T0_
            if kind == "go":
                tgt = self._pp(a["p"])
                if float(math.hypot(tgt[0] - p._p[0], tgt[1] - p._p[1])) < 0.03: continue
                for v in (1.0, 1.3):                           # ふつう → 急ぎ。間に合う方（着く時刻＝t）
                    d = (lambda q: (q.walk_to(tgt, speed=v), q.t)[1])(copy.deepcopy(p)) - p.t
                    if tau - d >= p.t - 1e-6: break
                self._wait_to(p, tau - d, "歩く%.1f" % t); p.walk_to(tgt, speed=v)
                if a.get("end_face") is not None: p.turn_to(a["end_face"] + 180.0)
            elif kind == "face":
                h = a["face"] + 180.0
                d = (lambda q: (q.turn_to(h), q.t)[1])(copy.deepcopy(p)) - p.t
                if d < 0.05: continue
                self._wait_to(p, tau - d, "向く%.1f" % t); p.turn_to(h)
            elif kind == "look":
                p.look(0, a["pitch"], hold=0.0, at=max(tau, 0.0))
            elif kind == "hop":
                self._wait_to(p, tau, "跳ぶ%.1f" % t); p.hops(n=1, height=max(0.05, min(0.16, a["h"] * 0.35)))
            elif kind == "roll":
                p.tracks["roll"].set(max(tau, 0.0), a["d"], -a["deg"])
            elif kind == "pitch":
                p.tracks["pitch"].set(max(tau, 0.0), a["d"], a["deg"])
            elif kind == "light":
                p.tracks["light"].set(max(tau, 0.0), a["d"], a["v"] / 1.6 - 1.0)
            elif kind == "blink":
                p.blinks.append(max(tau, 0.0))
            else:                                              # 気持ちの動き（予定を進める）
                self._wait_to(p, tau, kind + "%.1f" % t)
                getattr(p, kind)(**a)
        if p.t < t_end - T0_ + 0.5: p.idle(t_end - T0_ + 0.5 - p.t)
        return p

    def bake(self, t_end):
        p = self.plan(t_end)
        frames = mm.simulate(p, fps=FPS, t_end=p.t)
        rig = marurig.MaruRig(self.root); bk = marurig.Baker()
        for i, fr in enumerate(frames): rig.apply(fr, i, bk)
        bk.write()
        T0_ = CLOCK_T0()
        for e in p.events:                                     # 足音：予定の一歩ずつ
            if e["kind"] in ("step", "step_turn"): STEPS.append(round(T0_ + e["t"], 3))
            elif e["kind"] in ("takeoff", "land"): EVENTS.append((round(T0_ + e["t"], 3), "jump" if e["kind"] == "takeoff" else "land"))
        self.frames = frames; self.p = p
        return frames


def bake_all(t_end):
    for m in Maru.ALL: m.bake(t_end)
    if LATE: print("【まるロボ】間に合わなかった動き（秒）：", LATE)


def CLOCK_T0():
    return CLOCK["T0"] if "CLOCK" in globals() else T0
