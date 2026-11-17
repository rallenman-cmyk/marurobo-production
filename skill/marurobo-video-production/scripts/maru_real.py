# 本物のまるロボを場面に置き、marumotion の毎コマを当てる（全部の回で共通。2026-11-17 ユーザー「本物に替えて描き直す」）
#   決まり：references/maru_walk.md（手で動かさない・予定で動かす）
#
#   使い方（Blender の中で）：
#     import maru_real as MR
#     h = MR.place(loc=(x, y, z), heading=度, scale=1.0)        # 置き場所（場面の座標）・向き・大きさ（机の上なら 0.22 など）
#     p = mm.Plan(pos=(0, 0), heading=0)                           # 予定の座標は「置き場所の親の中の座標」＝本物の寸法の m（大きさ 1）。
#                                                                  #   世界の点 w は ((w − loc) を −heading 回して) ÷ scale で直す（4本目 anim/real_maru.py の Conv.xy）
#     p.wait(1.0); p.walk_to((0.3, 0)); ...
#     h.bake(mm.simulate(p, fps=24), f0=0)                         # 毎コマを当てる（コマ番号 f0 から）
#     h.torso → 札や記録に使う体の中心（Object）。h.real → 本物なら True
#     予定にない動き（ころぶ・寝ころぶ・人に運ばれる など）は、h.parent（置き場所の親）にキーを足して重ねる。
#       marurig は親の中の座標で当てるので、親を回す・動かすと、歩きや姿勢ごとまとめて動く
#   本物には荷台がある：荷台（cradle・cargo）と、marurig が頭に作る受け皿（saddle）は描かない（帽子のない回で頭の上に見えるため）
#
#   本物の体（PC）：story.blend の「Maru」を読みこみ、ep01 の marurig で当てる。story.blend の場所は
#     ① place(blend=...)  ② 環境変数 MARU_BLEND  ③ コマンドの --blend <path>  ④ C:\marurobo の下を探す（bt_production_v1\output\story.blend）
#   代わりの体（クラウドの確認）：本物がないときは、marumotion と同じ寸法の白い体に、同じ毎コマを当てる（ep02 の op_stage_standin と同じ考え）
#     代わりの体で描いたものは本番に使わない。MARU_REQUIRE_REAL=1 なら、本物がないとき止める（PC の本番で使う）
#
#   import の前に、sys.path にこのフォルダと ep01 の stage/maru（marurig）を入れる：MR.add_paths(<リポジトリの根>) でもよい
import os, sys, glob, math
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import marumotion as mm


def add_paths(repo_root):
    for p in (os.path.join(repo_root, "skill", "marurobo-video-production", "scripts"), os.path.join(repo_root, "episodes", "ep01_earphone", "stage", "maru")):
        if os.path.isdir(p) and p not in sys.path: sys.path.insert(0, p)


def _rig_path():
    """marurig.py のあるフォルダ（このフォルダの写し → リポジトリの ep01）"""
    for p in (HERE, os.path.join(HERE, "..", "..", "..", "episodes", "ep01_earphone", "stage", "maru")):
        if os.path.exists(os.path.join(p, "marurig.py")): return os.path.abspath(p)
    return None


def find_blend(blend=None):
    c = [blend, os.environ.get("MARU_BLEND")]
    if "--blend" in sys.argv: c.append(sys.argv[sys.argv.index("--blend") + 1])
    for p in c:
        if p and os.path.exists(p): return p
    for root in ("C:\\marurobo", os.path.join(os.path.expanduser("~"), "marurobo")):
        if not os.path.isdir(root): continue
        hits = glob.glob(os.path.join(root, "**", "bt_production_v1", "output", "story.blend"), recursive=True) or \
            glob.glob(os.path.join(root, "**", "story.blend"), recursive=True)
        if hits: return sorted(hits, key=len)[0]
    return None


def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out


def _link(o, coll):
    if o.name not in coll.objects: coll.objects.link(o)


# ---------------------------------------------------------------- 代わりの体（寸法は marumotion と同じ）
def _mat(name, rgb, rough=0.4, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    return m


def _srgb(h):
    h = h.lstrip("#"); v = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in v)


def _prim(kind, name, parent, coll, mat, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(**kw); o = bpy.context.object; o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o); o.parent = parent; o.data.materials.append(mat)
    for p_ in o.data.polygons: p_.use_smooth = True
    return o


class _Standin:
    """本物と同じ親子の名前（• torso・• leg・Inner lens ring・Antenna light）で作り、marurig をそのまま当てる"""
    def __init__(self, coll, tag):
        white = _mat("Maru white " + tag, _srgb("#F2F4F5"), 0.35); gray = _mat("Maru gray " + tag, _srgb("#C9CED3"), 0.4)
        dark = _mat("Maru ring " + tag, _srgb("#203236"), 0.25); teal = _mat("Maru lens " + tag, _srgb("#3FC6C9"), 0.2, 2.2)
        orange = _mat("Maru light " + tag, _srgb("#FF9A3C"), 0.3, 1.6); boot = _mat("Maru boot " + tag, _srgb("#E9ECEF"), 0.5)
        self.root = bpy.data.objects.new("Maru " + tag, None); coll.objects.link(self.root)
        torso = bpy.data.objects.new("Maru " + tag + " • torso", None); coll.objects.link(torso); torso.parent = self.root; torso.location = (0, 0, mm.TORSO_Z)
        _prim("uv_sphere", "Maru body " + tag, torso, coll, white, radius=1, segments=48, ring_count=24).scale = (0.51, 0.46, 0.49)
        r = _prim("cylinder", "Lens ring " + tag, torso, coll, dark, radius=0.27, depth=0.06, vertices=48); r.rotation_euler = (math.radians(90), 0, 0); r.location = (0, 0.445, mm.LENS["z"])
        l = _prim("cylinder", "Lens " + tag, torso, coll, teal, radius=mm.LENS["r"], depth=0.05, vertices=48); l.rotation_euler = (math.radians(90), 0, 0); l.location = (0, 0.47, mm.LENS["z"])
        ir = _prim("cylinder", "Inner lens ring " + tag, torso, coll, dark, radius=mm.LENS["ring_r"], depth=0.012, vertices=48)
        ir.rotation_euler = (math.radians(90), 0, 0); ir.location = (0, mm.LENS["ring_y"], mm.LENS["z"]); ir.scale = (1, 1, 1)
        ant = bpy.data.objects.new("Maru " + tag + " • antenna", None); coll.objects.link(ant); ant.parent = torso; ant.location = tuple(mm.ANT_BASE)
        tip = Vector(mm.ANT_TIP)
        rod = _prim("cylinder", "Antenna rod " + tag, ant, coll, gray, radius=0.018, depth=tip.length, vertices=16)
        rod.location = tip / 2; rod.rotation_euler = tip.to_track_quat("Z", "Y").to_euler()
        _prim("uv_sphere", "Antenna light " + tag, ant, coll, orange, radius=0.07, segments=24, ring_count=12).location = tip
        for s, nm in ((-1, "leg"), (1, "leg.001")):
            leg = bpy.data.objects.new("Maru " + tag + " • " + nm, None); coll.objects.link(leg); leg.parent = self.root
            leg.location = (s * mm.HIP_X, 0, mm.HIP_Z)
            _prim("cylinder", "Leg " + tag + nm, leg, coll, gray, radius=0.05, depth=mm.ANKLE, vertices=16).location = (0, 0, -mm.ANKLE / 2)
            bt = _prim("cube", "Soft boot " + tag + nm, leg, coll, boot, size=1); bt.scale = (0.2, 0.36, 0.12); bt.location = (0, 0.1, -mm.ANKLE - mm.SOLE + 0.07)
        bpy.context.view_layer.update()


# ---------------------------------------------------------------- 置く
class Handle:
    def __init__(self, parent, root, rig, real):
        self.parent, self.root, self.rig, self.real = parent, root, rig, real
        self.torso = rig.torso

    def bake(self, frames, f0=0):
        import marurig as mr
        bk = mr.Baker()
        for i, fr in enumerate(frames): self.rig.apply(fr, f0 + i, bk)
        bk.write()
        return self


def place(loc=(0, 0, 0), heading=0.0, scale=1.0, blend=None, name="maru", coll=None):
    """置き場所の親（Empty）を作り、本物（なければ代わり）のまるロボをその子にする。
    heading：場面の座標で、親の向き（度。0＝予定の +y が場面の +y）。予定の中の向きは Plan(heading=) で決める"""
    rp = _rig_path()
    if rp and rp not in sys.path: sys.path.insert(0, rp)
    import marurig as mr
    coll = coll or bpy.context.scene.collection
    par = bpy.data.objects.new(name + " place", None); coll.objects.link(par)
    par.location = loc; par.rotation_euler = (0, 0, math.radians(heading)); par.scale = (scale,) * 3
    path = find_blend(blend); real = bool(path)
    if real:
        with bpy.data.libraries.load(path, link=False) as (src, dst): dst.objects = [n for n in src.objects]
        loaded = [o for o in dst.objects if o is not None]
        m0 = next(o for o in loaded if o.name.startswith("Maru") and o.parent is None and any("• torso" in c.name for c in hier(o)))
        keep = {o.name for o in hier(m0)}
        for o in loaded:
            if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
        for n in keep: _link(bpy.data.objects[n], coll)
        for o in hier(m0):
            if o.name.startswith(("Cradle", "Maru cargo")) or "cradle" in o.name.lower(): o.hide_render = True; o.hide_viewport = True
        root = m0
    else:
        if os.environ.get("MARU_REQUIRE_REAL"): raise SystemExit("本物のまるロボ（story.blend）が見つからない。--blend か MARU_BLEND で指定する")
        root = _Standin(coll, name).root
    root.parent = par; root.matrix_parent_inverse = Matrix.Identity(4); root.location = (0, 0, 0); root.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    rig = mr.MaruRig(root)
    if getattr(rig, "saddle", None):                     # 頭の受け皿（荷物用）は使わないので隠す
        rig.saddle.hide_render = True; rig.saddle.hide_viewport = True
    for o in hier(root):
        if "cradle" in o.name.lower() or o.name.startswith(("Cradle", "Maru cargo")): o.hide_render = True; o.hide_viewport = True
    print("MARU", "REAL" if real else "STANDIN", path or "")
    return Handle(par, root, rig, real)
