# S06「押したボタンは同じ。違ったのは押した人だけ」（1:28〜1:40）を 3D で
#   左の板＝まるロボが出されたテスト（信号機の絵）、右の板＝私はチェックだけで通った。まるロボはまん中で見比べ、首をかしげる
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("押したボタンは"), said("実はこの欄"))
t_diff, t_q, t_next = said("違ったのは"), said("いったい、どこで"), said("その答えに")
setup_stage()
Y = 4.6
_, gL = build(lambda: board("scr_test", -2.2, Y, 2.1, 3.2, 1.8), (-2.2, Y, 2.1))
_, gR = build(lambda: board("scr_pass", 2.2, Y, 2.1, 3.2, 1.8), (2.2, Y, 2.1))
for g, dt in ((gL, 0.0), (gR, 0.25)):
    rise(g, T0 + dt, 2.6, 0.9); bob(g, T0 + 1.0 + dt, T1, 0.05, 2.6)
ev(T0, "whoosh", 0.35)
# 板の下の光る台（色で 2 つを分ける）
for x, c, n in ((-2.2, TE, "L"), (2.2, OR, "R")):
    cyl(mat("base_" + n, NV, rough=0.25, coat=0.6), (x, Y - 0.2, 0.08), 0.9, 0.16)
    ring3d(x, Y - 0.2, 0.17, 0.92, c, "base_rim_" + n, minor=0.022, rot=(0, 0, 0))
root = maru((0, 2.0, 0), face_deg=90, s=0.75, hat=False, eye_glow=1.0, look_up=10)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=0, look=10); breathe(mr, T0 + 0.6, T1, [(t_next, t_next + 1.0)])
mr.at(t_diff, face=-55, look=14); mr.at(t_diff + 1.3, face=55, look=14)
mr.at(t_q - 0.2, face=0, look=8); mr.tilt(t_q, 16, 0.35)
mr.tilt(t_next, 0, 0.35); mr.hop(t_next + 0.1, 0.18, 0.4); ev(t_next + 0.1, "jump", 0.6); ev(t_next + 0.5, "land", 0.6)
dolly([(T0, (0.8, -6.3, 3.1), (0, Y, 1.9)), (T1, (-0.5, -5.4, 2.8), (0, Y, 1.8))])
track("maru", mr.body, 0.6)
anchor_at("L_top", (-2.2, Y, 3.25)); anchor_at("R_top", (2.2, Y, 3.25))
finish("s06")
