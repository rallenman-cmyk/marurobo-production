# 16本目 v1 のコメント（「ドアが開く時扉が貫通してる」「泥棒が壁に貫通してる」）から作った、動く物が止まった物に入りこんでいないかを数える道具
#   blender -b --factory-startup --python hitcheck.py -- <カット> [見る物=shadow,maru,door,door2]
#   動く物（track の名前。その子の形を全部）の頂点が、止まった物（動かない形）の中に 2 cm より深く入るコマを、0.1 秒ごとに数える。
#   出力の最後に「HITCHECK <カット> <入りこんだコマ数>」。0 になるまで直す
import bpy, sys, os
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index("--") + 1:]
name = _a[0]; WATCH = (_a[1] if len(_a) > 1 else "shadow,maru,door,door2").split(",")
# 17本目 v1 のコメント「ドア開ける時にまるロボの体を貫通してる」：動く物（金庫のとびら・カード・帽子）どうしは数えていなかった。
#   3 つ目に相手の名前（track の名前。その子の形）を渡すと、動いていても相手として数える
AGAINST = (_a[2].split(",") if len(_a) > 2 else [])
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [name, "/tmp/hitcheck_" + name, "--track"]
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "scenes.py")}
exec(open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read(), g)
sc = bpy.context.scene; FPS = sc.render.fps; TR = g["TRACK"]


def root_of(ob):
    while ob.parent is not None and ob.parent.type == "EMPTY" and ob.parent.parent is not None: ob = ob.parent
    return ob


movers = {}
for nm in WATCH:
    if nm not in TR: continue
    ob = TR[nm][0]
    top = ob
    while top.parent is not None: top = top.parent
    meshes = [o for o in [top] + list(top.children_recursive) if o.type == "MESH" and not o.hide_render]
    movers[nm] = meshes
moving = set(o for v in movers.values() for o in v)
def animated(o):
    while o is not None:
        if o.animation_data and o.animation_data.action: return True
        o = o.parent
    return False
statics = [o for o in sc.objects if o.type == "MESH" and o not in moving and not o.hide_render and not animated(o)
           and max(o.dimensions) < 40 and min(o.dimensions) > 0.015]
if AGAINST:
    statics = []
    for nm in AGAINST:
        if nm in TR: statics += [o for o in [TR[nm][0]] + list(TR[nm][0].children_recursive) if o.type == "MESH" and max(o.dimensions) > 0.015]
bad = 0; seen = set()
for k in range(sc.frame_start, sc.frame_end + 1, max(1, FPS // 10)):
    sc.frame_set(k)
    for nm, ms in movers.items():
        pts = []
        for m in ms:
            mw = m.matrix_world; pts += [mw @ m.data.vertices[i].co for i in range(0, len(m.data.vertices), 3)]
        if not pts: continue
        if max((p - pts[0]).length for p in pts[::7]) < 0.05: continue       # 出る前・消えたあと（大きさ 0）は数えない
        lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
        for s in statics:
            bb = [s.matrix_world @ Vector(c) for c in s.bound_box]
            slo = Vector([min(c[i] for c in bb) for i in range(3)]); shi = Vector([max(c[i] for c in bb) for i in range(3)])
            if any(hi[i] < slo[i] or lo[i] > shi[i] for i in range(3)): continue
            inv = s.matrix_world.inverted(); hit = 0
            for p in pts:
                lp = inv @ p
                ok_, loc_, nor_, _ = s.closest_point_on_mesh(lp)
                if not ok_: continue
                d = (loc_ - lp)
                if d.dot(nor_) > 0 and (s.matrix_world.to_3x3() @ d).length > 0.02: hit += 1
            if hit:
                bad += 1
                if (nm, s.name) not in seen: print("HIT", nm, s.name, "%d コマ目" % k, hit, "場所", tuple(round(v, 2) for v in s.matrix_world.translation), "大きさ", tuple(round(v, 2) for v in s.dimensions)); seen.add((nm, s.name))
print("HITCHECK", name, bad)
