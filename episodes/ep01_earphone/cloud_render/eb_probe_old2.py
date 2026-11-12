import bpy, numpy as np
O = bpy.data.objects; bpy.context.scene.frame_set(1)
for nm in ("Static / Porcelain.003", "Static / Graphite.002", "Giant earbud / silicone tip"):
    o = O[nm]; M = np.array(o.matrix_world)
    V = np.array([v.co[:] for v in o.data.vertices]); V = V @ M[:3, :3].T + M[:3, 3]
    print("OBJ", nm, len(o.data.polygons), "polys")
    zs = np.linspace(V[:, 2].min(), V[:, 2].max(), 14)
    for a, b in zip(zs[:-1], zs[1:]):
        s = V[(V[:, 2] >= a) & (V[:, 2] < b)]
        if len(s): print("  z %5.2f-%5.2f n=%4d x %6.2f..%6.2f y %6.2f..%6.2f" % (a, b, len(s), s[:, 0].min(), s[:, 0].max(), s[:, 1].min(), s[:, 1].max()))
    # 面ごとの平らさ（シェーディング）
    print("  smooth:", sum(p.use_smooth for p in o.data.polygons), "/", len(o.data.polygons), "mods:", [m.type for m in o.modifiers])
