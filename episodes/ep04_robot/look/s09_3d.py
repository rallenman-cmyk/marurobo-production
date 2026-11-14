# S09「機械の目が良くなった。2014年、Google：いちばん難しいゆがんだ文字でも 99.8% 読める」（3:09〜3:33）を 3D で
#   ゆがんだ文字の板を、機械（プログラム）が光の線で読む。ガラスの柱に 99.8% の光がたまる。まるロボはしょんぼり
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("ところが、機械の目は"), next_sub("つまり、ゆがんだ文字だけでは"))
t_g, t_998, t_so = said("2014年、このテスト"), said("今のAIは"), said("つまり、ゆがんだ文字だけでは")
setup_stage()
Y, BZ, BW = 4.8, 3.05, 6.0; BH = BW * 270 / 1000
bm, gB = build(lambda: board("lk_captcha", 0, Y, BZ, BW, BH, emit=0.5), (0, Y, BZ))
bob(gB, T0, T1, 0.04, 2.8)
# 機械（右の手前）
PX, PY = 3.1, 2.2
dots, gM = build(lambda: (podium(PX, PY, TE, "R"), machine(PX, PY))[1], (PX, PY, 0))
pop(gM, T0 + 0.3); ev(T0 + 0.3, "pop", 0.5)
think(dots, T0 + 1.0, 8, 0.35)
scan(-BW / 2 + 0.3, BW / 2 - 0.3, Y - 0.15, BZ, BH * 0.8, T0 + 1.2, t_so - 0.3, 1.6)
ev(T0 + 1.2, "whoosh", 0.25)
# 99.8% の柱（左の手前）
liq, H = tube(-3.4, 2.5, TE, "acc")
fill(liq, H, t_998 + 0.6, 0.998, 2.0); ev(t_998 + 0.6, "rise", 0.45)
# 「つまり」：板の明かりが落ちる
b = bm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
b.default_value = 0.5; b.keyframe_insert("default_value", frame=f(t_so)); b.default_value = 0.18; b.keyframe_insert("default_value", frame=f(t_so + 1.0))
root = maru((0, 1.3, 0), face_deg=90, s=0.72, hat=False, eye_glow=1.0, look_up=20)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=0, look=20); breathe(mr, T0 + 0.6, t_so)
mr.at(T0 + 1.5, face=35, look=8); mr.at(t_g, face=0, look=18)
mr.at(t_998 + 0.5, face=-35, look=14); mr.at(t_998 + 3.0, face=-35, look=22)
mr.at(t_so, face=0, look=-14); mr.glow(t_so, 1.0, 0.35, 0.8); ev(t_so + 0.1, "down", 0.5)
dolly([(T0, (-0.5, -6.6, 2.5), (0, Y, 2.1)), (T1, (0.5, -5.8, 2.3), (0, Y, 2.1))], lens=27)
track("maru", mr.body, 0.6)
anchor_at("tube_top", (-3.4, 2.5, H + 0.5)); anchor_at("board_top", (0, Y, BZ + BH / 2 + 0.2))
anchor_at("R_top", (PX, PY, 1.9))
finish("s09")
