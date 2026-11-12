# ch03_stage.py のあとに走らせる：まるロボの体・荷物（トレー＋箱）・台（積み込み口・受け取り台・腕）が、めり込んでいないかを、コマごとに調べる
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sc = bpy.context.scene; O = bpy.data.objects
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
maru = O["Maru"]; cargo = next(o for o in O if o.name.startswith("Maru cargo") and o.type == "EMPTY")
cargo_set = set(hier(cargo))
robot = [o for o in hier(maru) if o.type == "MESH" and o not in cargo_set and not o.hide_render]
cargo_m = [o for o in cargo_set if o.type == "MESH"]
dock_names = ("Deck frame", "Deck roller", "Pusher", "Dock frame", "Dock roller", "Pull rail", "Pull arm", "Pull claw", "Dock leg", "Booth", "Dock base", "Dock window", "Dock top", "Dock side")
docks = [o for o in O if o.type == "MESH" and o.name.startswith(dock_names) and not o.hide_render]
print("PROBE robot meshes:", [o.name for o in robot][:60], flush=True)
print("PROBE cargo meshes:", [o.name for o in cargo_m], flush=True)
dg = bpy.context.evaluated_depsgraph_get()
def bvh(objs):
    V = []; P = []
    for o in objs:
        if o.hide_render: continue
        ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
        base = len(V); V += [mw @ v.co for v in me.vertices]; P += [[base + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(V, P) if P else None
def names_overlap(A, B):
    """どの組がめり込んでいるか（重いので、重なったときだけ）"""
    out = []
    for a in A:
        ta = bvh([a])
        if ta is None: continue
        for b in B:
            tb = bvh([b])
            if tb is not None and ta.overlap(tb): out.append((a.name, b.name))
    return out
ts = [float(x) for x in sys.argv[sys.argv.index("--") + 1:][-1].split(",")] if "--probe_t" in sys.argv else [i * 0.25 for i in range(int(22.0 / 0.25), int(49.5 / 0.25))]
for t in ts:
    sc.frame_set(int(round(t * 24)) + 1); dg = bpy.context.evaluated_depsgraph_get()
    vis = not cargo_m[0].hide_render if cargo_m else False
    R = bvh(robot); C = bvh([o for o in cargo_m if not o.hide_render]); D = bvh(docks)
    rc = bool(R and C and R.overlap(C)); rd = bool(R and D and R.overlap(D)); cd = bool(C and D and C.overlap(D))
    msg = "PROBE t=%.2f cargo_vis=%s robot×cargo=%s robot×dock=%s cargo×dock=%s" % (t, vis, rc, rd, cd)
    if rc: msg += " RC:" + str(names_overlap([o for o in robot], [o for o in cargo_m if not o.hide_render])[:6])
    if rd: msg += " RD:" + str(names_overlap(robot, docks)[:6])
    print(msg, flush=True)
