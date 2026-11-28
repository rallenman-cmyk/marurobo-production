# 16本目：カメラが物の中に入っていないかを数える（下書きで、ベッドの中・塔の中にカメラが入り、真っ黒なカットが出た）
#   blender -b --factory-startup --python camcheck.py -- <カット名>
#   scenes.py を --track（描かない）で組み立ててから、カットの間 0.5 秒ごとにカメラの位置を調べる。
#   映る物（カメラに見える・描く物）の箱（物の向きに合わせた箱）の中にカメラがあれば「IN <物> <秒>」を出す。
#   出力の最後に「CAMCHECK <カット> <中に入ったコマ数>」。0 でなければ、描く前に直す。
import bpy, sys, os
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index("--") + 1:]
name = _a[0]
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [name, "/tmp/camcheck_" + name, "--track"]
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "scenes19.py")}
exec(open(os.environ.get("CAMCHECK_SCENES", os.path.join(HERE, "scenes19.py")), encoding="utf-8").read(), g)
sc = bpy.context.scene
FPS = sc.render.fps
bad = 0
seen = set()
for k in range(sc.frame_start, sc.frame_end + 1, max(1, FPS // 2)):
    sc.frame_set(k)
    cp = sc.camera.matrix_world.translation
    for ob in sc.objects:
        if ob.type != "MESH" or ob.hide_render or not ob.visible_camera: continue
        d = ob.dimensions
        if max(d) > 30 or min(d) < 0.03: continue        # 床・空・薄い板は除く
        lp = ob.matrix_world.inverted() @ cp
        bb = [Vector(c) for c in ob.bound_box]
        lo = Vector([min(c[i] for c in bb) for i in range(3)]); hi = Vector([max(c[i] for c in bb) for i in range(3)])
        if all(lo[i] < lp[i] < hi[i] for i in range(3)):
            ok_, loc_, nor_, _ = ob.closest_point_on_mesh(lp)      # 箱の中でも、形（丸い塔など）の外ならよい：いちばん近い面の向きで内外を決める
            if not ok_ or (loc_ - lp).dot(nor_) <= 0: continue
            bad += 1
            if ob.name not in seen:
                print("IN", ob.name, "%.1f秒" % (k / FPS)); seen.add(ob.name)
print("CAMCHECK", name, bad)
