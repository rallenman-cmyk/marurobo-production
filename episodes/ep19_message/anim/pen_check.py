# 9本目 v2 のコメント「まるロボが貫通してる」5 件（11:19・12:20・12:51 ボール・14:21・5:23）：物の突き抜けを、場面ごとに数える
#   blender -b --factory-startup --python pen_check.py -- <クリップ> <出力フォルダ>
#   その場面の間を 1/4 秒ごとに、動く物（まるロボの体・ボール・小さなまるロボ）を球とみなし、ほかの全部の物（形のある物）との
#   いちばん近い距離を測る。球の半径より 3cm 以上めりこんでいて、その物が画面に映っている間を「突き抜け」と数える。
#   PEN クリップ 動く物 ぶつかる物 時刻の始め〜終わり 回数 いちばん深いめりこみ(cm)
import os, sys, math
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenes19.py")
src = open(P, encoding="utf-8").read().replace("        render_clip(CLIPNAME,", "        CHECK(t0, t1)\n        0 and render_clip(CLIPNAME,")
TOL = 0.03


def CHECK(t0, t1):
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from bpy_extras.object_utils import world_to_camera_view as w2c
    G_ = _G; sc = bpy.context.scene; TR = G_["TRACK"]; cam_ = sc.camera
    movers = []
    if "maru_c" in TR: movers.append(("まるロボ", TR["maru_c"][0], 0.36))
    if "ball" in TR: movers.append(("ボール", TR["ball"][0], 0.078))
    if "doll" in TR: movers.append(("小さなまるロボ", TR["doll"][0], 0.36 * 0.4))
    if not movers: print("PEN_DONE %s 動く物なし" % G_["CLIPNAME"]); return
    # 動く物の体（子も）はぶつかる物から外す。まるロボの体の物（目・足など）も外す
    skip = set()
    for _, ob, _r in movers:
        # 自分と子だけを外す（親をたどると、段に乗った物は段の親＝エスカレーター全体まで外してしまい、26-07 の突き抜けを見落とした）
        for o in [ob] + list(ob.children_recursive): skip.add(o.name)
    for o in bpy.data.objects:
        if "maru" in o.name.lower() or o.name.startswith(("Inner lens", "Lens", "Antenna", "Maru")): skip.add(o.name)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in skip and len(o.data.polygons) > 0]
    BV = {}; CL = {}
    def closed(o):
        """形が閉じている（どの辺も 2 つの面にはさまれる）か。閉じた形なら、中に入っているかを光線で数える"""
        if o.name not in CL:
            from collections import Counter
            cnt = Counter(k for p in o.data.polygons for k in p.edge_keys)
            CL[o.name] = len(cnt) > 0 and all(v == 2 for v in cnt.values())
        return CL[o.name]
    def inside(o, lc):
        b = bvh(o); n = 0; org = lc.copy(); dr = Vector((0.577, 0.577, 0.577))
        for _ in range(64):
            hit, nrm, idx, dist = b.ray_cast(org, dr)
            if hit is None: break
            n += 1; org = hit + dr * 1e-4
        return n % 2 == 1
    def bvh(o):
        if o.name not in BV:
            BV[o.name] = BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])
        return BV[o.name]
    hits = {}
    t = t0
    while t <= t1:
        sc.frame_set(G_["f"](t))
        for nm, ob, r in movers:
            if ob.hide_render: continue
            c = ob.matrix_world.translation.copy()
            if nm == "まるロボ": c = c + Vector((0, 0, 0.0))
            q = w2c(sc, cam_, c)
            if not (q.z > 0 and -0.05 < q.x < 1.05 and -0.05 < q.y < 1.05): continue
            for o in meshes:
                if o.hide_render or o.hide_get() is None: continue
                mw = o.matrix_world
                # 箱で先にふるい落とす
                bb = [mw @ Vector(v) for v in o.bound_box]
                lo = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb))); hi = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
                if any(c[i] < lo[i] - r or c[i] > hi[i] + r for i in range(3)): continue
                inv = mw.inverted(); lc = inv @ c
                loc, nrm, idx, dist = bvh(o).find_nearest(lc)
                if loc is None: continue
                d = (mw @ loc - c).length          # 世界の長さで（物は縦横で倍率がちがうので、倍率をかけるだけでは合わない）
                # 面までの距離が半径より近い。閉じた形（箱・筒）は、中に入っていれば面までの距離を足す（板は厚みがないので、中か外かは見ない）
                depth = (r + d) if (closed(o) and inside(o, lc)) else (r - d)
                if depth > TOL:
                    k = (nm, o.name)
                    h = hits.setdefault(k, [t, t, 0, 0.0]); h[1] = t; h[2] += 1; h[3] = max(h[3], depth)
        t += 0.25
    for (nm, on), (a, b, n, dp) in sorted(hits.items(), key=lambda x: x[1][0]):
        print("PEN %s %s %s %.2f〜%.2f %d回 %.0fcm" % (G_["CLIPNAME"], nm, on, a, b, n, dp * 100))
    print("PEN_DONE %s %d" % (G_["CLIPNAME"], len(hits)))


_G = {"__file__": P, "__name__": "__main__", "CHECK": CHECK}
exec(compile(src, P, "exec"), _G)
