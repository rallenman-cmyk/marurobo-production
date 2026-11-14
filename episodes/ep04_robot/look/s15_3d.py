# S15c〜d「これまでの記録：ニュース・買い物・動画 → 同じことを何百回も」（5:59〜6:15）を 3D で
#   宙に浮く記録の板。アイコンの札が 1 つずつ出る（人らしい）→ 消えて、同じカートが何十個も一気に並ぶ（怪しい）→ ふちが赤く
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("たとえば、ふだんから"), next_sub("怪しいですよね"))
t_ok, t_rep, t_sus = said("これは、人が使って"), said("反対に、短い間に"), said("怪しいですよね")
setup_stage()
Y, BZ, PW, PH = 4.8, 2.7, 7.4, 3.2
def panel():
    cube(mat("rec_frame", NV, rough=0.3, coat=0.5), (0, Y + 0.08, BZ), (PW + 0.3, 0.12, PH + 0.3), bevel=0.08)
    cube(mat("rec_in", "#2A4268", rough=0.5, emit=0.15), (0, Y, BZ), (PW, 0.04, PH), bevel=0.03)
_, gP = build(panel, (0, Y, BZ))
rise(gP, T0 - 0.3, 2.5, 0.9); bob(gP, T0 + 0.6, T1, 0.035, 2.8); ev(T0 - 0.2, "whoosh", 0.3)
# アイコンの札（人らしい記録）
tiles = []
for k, (tx, x) in enumerate((("lk_news", -2.3), ("lk_cart", 0.0), ("lk_play", 2.3))):
    def tile(tx=tx, x=x):
        cube(mat("tile_b", "#FFFFFF", rough=0.4), (x, Y - 0.12, BZ + 0.25), (1.5, 0.12, 1.5), bevel=0.15)
        plane(img(tx, emit=0.3), (x, Y - 0.19, BZ + 0.25), (1.3, 1.3), rot=(R(90), 0, 0))
    _, g = build(tile, (x, Y - 0.12, BZ + 0.25)); tiles.append(g)
    tt = T0 + 1.0 + k * 1.4; pop(g, tt); ev(tt, "pop", 0.5)
    vanish(g, t_rep - 0.1 + k * 0.05, 0.25)
ev(t_rep - 0.1, "whoosh", 0.25)
_, gC = build(lambda: check3d(PW / 2 - 0.2, Y - 0.3, BZ + PH / 2 - 0.1, 0.8), (PW / 2 - 0.2, Y - 0.3, BZ + PH / 2 - 0.1))
pop(gC, t_ok + 0.2); ev(t_ok + 0.2, "pipo", 0.45); vanish(gC, t_rep - 0.1, 0.25)
# 同じカートがずらりと（3 段 × 12）
for r in range(3):
    for c in range(12):
        x = -PW / 2 + 0.45 + c * (PW - 0.9) / 11; z = BZ + 0.75 - r * 0.62
        def mini(x=x, z=z):
            cube(mat("mini_b", "#FFFFFF", rough=0.4), (x, Y - 0.1, z), (0.5, 0.08, 0.5), bevel=0.06)
            plane(img("lk_cart", emit=0.3), (x, Y - 0.15, z), (0.44, 0.44), rot=(R(90), 0, 0))
        _, g = build(mini, (x, Y - 0.1, z))
        tt = t_rep + 0.4 + (r * 12 + c) * 0.07; pop(g, tt, 0.25)
        if c % 3 == 0: ev(tt, "pi", 0.1)
fr, gR = build(lambda: frame_rect(0, Y - 0.15, BZ, PW + 0.35, PH + 0.35, RED, "rec_red", th=0.07, emit=5.0), (0, Y - 0.15, BZ))
pop(gR, t_sus, 0.35); ev(t_sus, "down", 0.5)
root = maru((0, 1.4, 0), face_deg=90, s=0.72, hat=False, eye_glow=1.0, look_up=18)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=0, look=18); breathe(mr, T0 + 0.6, T1, [(t_ok, t_ok + 1.0)])
mr.at(T0 + 1.0, face=-25, look=18); mr.at(T0 + 2.4, face=0, look=18); mr.at(T0 + 3.8, face=25, look=18)
mr.hop(t_ok + 0.3, 0.15, 0.35); ev(t_ok + 0.3, "jump", 0.4); ev(t_ok + 0.65, "land", 0.4)
mr.at(t_rep + 0.5, face=0, look=20); mr.tilt(t_sus + 0.1, 14, 0.35)
dolly([(T0, (0.6, -6.4, 2.6), (0, Y, 2.2)), (T1, (-0.4, -5.6, 2.4), (0, Y, 2.2))], lens=27)
track("maru", mr.body, 0.6)
anchor_at("top", (0, Y, BZ + PH / 2 + 0.15)); anchor_at("bottom", (0, Y - 0.2, BZ - PH / 2 + 0.1))
for k, x in enumerate((-2.3, 0.0, 2.3)): anchor_at("t%d" % k, (x, Y - 0.2, BZ - 0.62))
finish("s15")
