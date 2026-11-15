# S08g〜h「機械に読めない文字を、たくさんの人に読んでもらう」（2:43〜2:55）を 3D で
#   まん中に、かすれた単語（upon）の板。まわりに小さな人がたくさん出て、光の線で板に答えを送る → 板のふちが緑に（決まった）
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("機械に読めない文字を"), next_sub("何人もの人が"))
t_many, t_same = said("機械に読めない文字を"), said("何人もの人が")
t_ok = t_same + 3.4
setup_stage()
Y, BZ = 5.0, 2.6
_im = bpy.data.images.load(os.path.join(TEX, "lk_upon.png")); bw = 3.4; bh = bw * _im.size[1] / _im.size[0]
_, gB = build(lambda: board("lk_upon", 0, Y, BZ, bw, bh, emit=0.55), (0, Y, BZ))
rise(gB, T0 - 0.2, 2.0, 0.8); bob(gB, T0 + 0.7, T1, 0.04, 2.6)
ev(T0, "whoosh", 0.3)
fg, gG = build(lambda: frame_rect(0, Y - 0.1, BZ, bw + 0.3, bh + 0.3, GRN, "fr_ok", th=0.07, emit=5.0), (0, Y - 0.1, BZ))
pop(gG, t_ok, 0.4); ev(t_ok, "win", 0.5)
# まわりの小さな人（半円に 12 人）
import math as _m
heads = []
cols = ["#3E7CB1", "#E07A5F", "#81B29A", "#F2CC8F", "#6D597A", "#3D9BE9"]
for i in range(12):
    a = _m.radians(200 + i * (140 / 11))
    x, y = 4.3 * _m.cos(a), Y - 1.2 + 2.2 * _m.sin(a)
    sp = 0.55
    h, g = build(lambda: person(x / sp, y / sp, 0.0, shirt_c=cols[i % 6], name="q%d" % i), (x / sp, y / sp, 0))
    g.scale = (sp,) * 3; g.location = (x, y, 0)
    ti = t_many + 0.6 + i * 0.13
    key(g, "scale", f(T0), (0.001,) * 3); key(g, "scale", f(ti), (0.001,) * 3); key(g, "scale", f(ti + 0.3), (sp * 1.08,) * 3); key(g, "scale", f(ti + 0.45), (sp,) * 3)
    if i % 3 == 0: ev(ti, "pop", 0.35)
    heads.append(h)
    # 光の線：頭から板へ
    bpy.context.view_layer.update()
    hp = (x, y, 1.75 * sp + 0.2)
    b = beam(hp, (0.0 + (i - 5.5) * 0.12, Y - 0.15, BZ - bh / 2 + 0.1), TE if i % 2 else OR, "bm%d" % i, r=0.018)
    tb = t_same + 0.4 + i * 0.12; grow(b, tb, 0.45)
    if i % 2 == 0: ev(tb, "pi", 0.12)
root = maru((0, 1.0, 0), face_deg=90, s=0.7, hat=False, eye_glow=1.0, look_up=20)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=0, look=20); breathe(mr, T0 + 0.6, T1, [(t_ok, t_ok + 1.2)])
mr.at(t_many + 1.0, face=-40, look=8); mr.at(t_many + 2.6, face=40, look=8); mr.at(t_same + 0.5, face=0, look=22)
mr.hop(t_ok + 0.15, 0.25, 0.42); ev(t_ok + 0.15, "jump", 0.5); ev(t_ok + 0.57, "land", 0.5)
dolly([(T0, (0.5, -5.6, 3.4), (0, Y - 1.0, 1.9)), (T1, (-0.5, -4.9, 3.1), (0, Y - 1.0, 1.9))], lens=27)
track("maru", mr.body, 0.6)
anchor_at("board", (0, Y - 0.1, BZ))
finish("s08x")
