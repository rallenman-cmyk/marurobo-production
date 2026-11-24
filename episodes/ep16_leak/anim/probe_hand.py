# 手で物を取る・置く動きを決める前に、手と物の位置を測る（16本目 2章の 2 回目の確認役：名札が棚から手へ飛んだ。手が棚に 1.2 m 届いていなかった）
#   blender -b --factory-startup --python probe_hand.py -- <カット> <時刻,時刻,...> [物の名前（TRACK の名前）,...]
#   各時刻の、影の手（IN["_hand"]）と、TRACK の物の世界の位置を出す。腕の角度は −で上がる（+55 で手 0.59 m、−25 で 0.91 m）
import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index("--") + 1:]
name, ts = _a[0], [float(x) for x in _a[1].split(",")]
objs = _a[2].split(",") if len(_a) > 2 else []
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [name, "/tmp/probe_hand", "--track"]
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "scenes.py")}
exec(open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read(), g)
sc = bpy.context.scene; IN = g["IN"]; TR = g["TRACK"]
for t in ts:
    sc.frame_set(g["f"](t))
    row = ["HAND %.2f" % t, tuple(round(v, 2) for v in IN["_hand"].matrix_world.translation)] if "_hand" in IN else ["%.2f" % t]
    for o in objs:
        if o in TR: row.append((o, tuple(round(v, 2) for v in TR[o][0].matrix_world.translation)))
    print(*row)
