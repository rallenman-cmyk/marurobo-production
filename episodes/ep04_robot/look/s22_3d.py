# S22d〜f「昔は文字、今はふるまい → AI はますます賢く → 見分ける方法は残り少ない」（10:10〜10:28）を 3D で
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("昔は、文字を"), next_sub("人と機械の違いを"))
t_now, t_ai, t_few = said("昔は、文字を") + 2.4, said("そして今、AIは"), said("人と機械の違いを")
setup_stage()
Y, BZ = 4.8, 2.6
# 昔と今の板
_, gO = build(lambda: board("lk_captcha", -2.3, Y, BZ, 3.6, 3.6 * 0.27, emit=0.5, name="old"), (-2.3, Y, BZ))
_, gN = build(lambda: board("scr_human_pass", 2.3, Y, BZ, 3.4, 3.4 * 1000 / 1600, emit=0.5, name="now"), (2.3, Y, BZ))
pop(gO, T0 + 0.1); ev(T0 + 0.1, "pop", 0.5); pop(gN, t_now); ev(t_now, "pop", 0.5)
for g in (gO, gN): vanish(g, t_ai - 0.1, 0.3)
ev(t_ai - 0.1, "whoosh", 0.3)
# AI が上へ（ますます賢く）
dots, gA = build(lambda: chatbot(0, Y - 0.6, 2.6, 1.15), (0, Y - 0.6, 2.6))
pop(gA, t_ai + 0.2, 0.5); ev(t_ai + 0.2, "pop", 0.5); think(dots, t_ai + 0.8, 6)
key(gA, ("location", 2), f(t_ai + 0.7), 2.6); key(gA, ("location", 2), f(t_few - 0.3), 3.0)
arws = []
for x in (-1.9, 1.9):
    _, g = build(lambda x=x: arrow_up(x, Y - 0.6, 2.0, 1.0), (x, Y - 0.6, 2.0)); arws.append(g)
    pop(g, t_ai + 0.6, 0.4)
    for k in range(3):
        tt = t_ai + 0.9 + k * 1.3; key(g, ("location", 2), f(tt), 2.0); key(g, ("location", 2), f(tt + 1.0), 2.5)
ev(t_ai + 0.6, "rise", 0.4)
for g in arws + [gA]: vanish(g, t_few - 0.1, 0.3)
# 見分ける方法：3 つの札（2 つは赤い×、最後は ？）
tiles = (("lk_captcha", -2.6, 3.0, 0.27), ("scr_test", 0.0, 2.2, 720 / 1280), ("scr_human_pass", 2.6, 2.4, 1000 / 1600))
for k, (tx, x, w, r) in enumerate(tiles):
    def tl(tx=tx, x=x, w=w, r=r):
        cube(mat("tl_b", NV, rough=0.3, coat=0.5), (x, Y + 0.06, BZ), (2.3, 0.1, 1.9), bevel=0.08)
        plane(img(tx, emit=0.45), (x, Y, BZ + 0.05), (min(w, 2.0), min(w, 2.0) * r), rot=(R(90), 0, 0))
    _, g = build(tl, (x, Y, BZ)); tt = t_few + 0.3 + k * 0.45; pop(g, tt); ev(tt, "pop", 0.45)
for k, x in enumerate((-2.6, 0.0)):
    _, g = build(lambda x=x: xmark(x, Y - 0.3, BZ, 0.75), (x, Y - 0.3, BZ)); tt = t_few + 2.0 + k * 0.7; pop(g, tt); ev(tt, "down", 0.35)
_, gQ = build(lambda: ring3d(2.6, Y - 0.2, BZ, 1.15, OR, "q_ring", minor=0.04, emit=5.0), (2.6, Y - 0.2, BZ))
pop(gQ, t_few + 3.6, 0.4); ev(t_few + 3.6, "lamp", 0.35)
for k in range(3):
    tt = t_few + 4.2 + k * 0.9; key(gQ, "scale", f(tt), (1, 1, 1)); key(gQ, "scale", f(tt + 0.45), (1.08,) * 3); key(gQ, "scale", f(tt + 0.9), (1, 1, 1))
root = maru((0, 1.4, 0), face_deg=90, s=0.7, hat=False, eye_glow=1.0, look_up=16)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=-30, look=14); breathe(mr, T0 + 0.6, T1)
mr.at(t_now, face=30, look=14); mr.at(t_ai + 0.3, face=0, look=26)
mr.at(t_few + 2.0, face=-35, look=12); mr.at(t_few + 3.6, face=35, look=12); mr.tilt(t_few + 4.0, 14, 0.35)
dolly([(T0, (0.5, -6.4, 2.5), (0, Y, 2.15)), (T1, (-0.5, -5.6, 2.4), (0, Y, 2.15))], lens=27)
track("maru", mr.body, 0.6)
anchor_at("O_top", (-2.3, Y, BZ + 0.75)); anchor_at("N_top", (2.3, Y, BZ + 1.3)); anchor_at("A_top", (0, Y - 0.6, 3.9))
for k, x in enumerate((-2.6, 0.0, 2.6)): anchor_at("T%d" % k, (x, Y, BZ - 0.95)); anchor_at("Q%d" % k, (x, Y, BZ + 0.95))
finish("s22")
