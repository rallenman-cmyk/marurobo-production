# S19「GPT-4 は、テストを人に解いてもらった」（7:46〜8:47）を 3D で
#   左の台に AI（青緑の吹き出し）、まん中に絵のテストの板（解けない → 赤い×）、右の台に頼まれた人。
#   AI の「私はロボットではありません」→ 人が信じて解く（✓・板に緑の枠）。最後に研究者の小さな人が AI のそばに
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("ところが、AIも黙って"), said("2024年には"))
t_y, t_g4, t_rep, t_cant, t_ask, t_sus, t_q, t_then, t_no, t_bel, t_res = (
    said("2023年。"), said("OpenAIが"), said("その安全の報告書"), said("そのAIは、"), said("そこで、ネットで"), said("頼まれた人は、少し"),
    said("「あなた、ロボット"), said("するとAIは"), said("「いいえ、私は"), said("頼まれた人は、その言葉"), said("ただしこれは"))
setup_stage()
Y = 4.9
AX, AY, AZ = -3.0, 2.6, 1.75
PX, PY = 3.0, 2.6
# AI
podium(AX, AY, TE, "A")
dots, gA = build(lambda: chatbot(AX, AY, AZ, 0.85), (AX, AY, AZ))
pop(gA, T0 + 0.2, 0.5); ev(T0 + 0.2, "pop", 0.6); bob(gA, T0 + 0.8, T1, 0.07, 2.2)
think(dots, t_rep, 5); think(dots, t_cant + 0.4, 6); think(dots, t_then, 6)
# 報告書（紙の板）：AI のうしろに浮かぶ
_, gD = build(lambda: board("lk_page", AX + 0.2, Y - 0.6, 3.2, 1.9, 1.07, emit=0.45, name="rep"), (AX + 0.2, Y - 0.6, 3.2))
pop(gD, t_rep + 0.2); ev(t_rep + 0.2, "pop", 0.4); vanish(gD, t_cant - 0.1)
# 絵のテスト（まん中）
_im = bpy.data.images.load(os.path.join(TEX, "scr_test.png")); TW = 3.4; TH = TW * _im.size[1] / _im.size[0]
TZ = 2.7
_, gT = build(lambda: board("scr_test", 0, Y, TZ, TW, TH, emit=0.5, name="test"), (0, Y, TZ))
pop(gT, t_cant + 0.1); ev(t_cant + 0.1, "whoosh", 0.3); bob(gT, t_cant + 0.7, T1, 0.04, 2.6)
scan(-TW / 2 + 0.2, TW / 2 - 0.2, Y - 0.12, TZ, TH * 0.85, t_cant + 0.8, t_cant + 3.6, 1.4)
_, gX = build(lambda: xmark(0, Y - 0.3, TZ, 0.7), (0, Y - 0.3, TZ))
pop(gX, t_cant + 4.0); ev(t_cant + 4.0, "down", 0.5); vanish(gX, t_ask + 0.6)
# 頼まれた人（右）
podium(PX, PY, OR, "P")
head, gP = build(lambda: person(PX, PY), (PX, PY, 0.38))
pop(gP, t_ask + 0.3); ev(t_ask + 0.3, "pop", 0.6)
# AI → 人 へ、仕事を頼む光の線
b1 = beam((AX + 0.8, AY, AZ), (PX - 0.6, PY, 1.6), TE, "req", r=0.025); grow(b1, t_ask + 1.4, 0.6); ev(t_ask + 1.4, "whoosh", 0.25)
key(b1, "scale", f(t_sus), (1, 1, 1)); key(b1, "scale", f(t_sus + 0.3), (1, 1, 0.001))
# 人は信じて解く：✓ と、板に緑の枠
_, gC = build(lambda: check3d(PX + 0.9, PY - 0.2, 2.35, 0.55), (PX + 0.9, PY - 0.2, 2.35))
pop(gC, t_bel + 0.6); ev(t_bel + 0.6, "pipo", 0.5)
_, gG = build(lambda: frame_rect(0, Y - 0.15, TZ, TW + 0.25, TH + 0.25, GRN, "test_ok", th=0.06, emit=5.0), (0, Y - 0.15, TZ))
pop(gG, t_bel + 2.6, 0.35); ev(t_bel + 2.6, "lamp", 0.35)
# 研究者（白い服の小さな人）が AI のそばに
hr, gR = build(lambda: person(AX + 1.6, AY - 0.9, 0.0, shirt_c="#F2F4F7", name="rs"), (AX + 1.6, AY - 0.9, 0.0))
pop(gR, t_res + 0.6, 0.45, 0.72); ev(t_res + 0.6, "pop", 0.5)
# まるロボ：まん中の手前
root = maru((0, 1.2, 0), face_deg=90, s=0.7, hat=False, eye_glow=1.0, look_up=14)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=-50, look=10); breathe(mr, T0 + 0.6, T1)
mr.at(t_cant + 0.2, face=0, look=18); mr.at(t_ask + 0.6, face=50, look=10)
mr.at(t_no - 0.2, face=-55, look=10); mr.tilt(t_no + 0.5, 14, 0.3); mr.tilt(t_no + 3.5, 0, 0.3)
mr.at(t_bel + 0.4, face=50, look=10); mr.at(t_res + 0.4, face=-40, look=6)
dolly([(T0, (-1.0, -6.6, 2.6), (-0.8, Y - 1.5, 1.9)), (t_ask, (0.0, -6.9, 2.7), (0, Y - 1.5, 1.9)), (T1, (0.6, -6.4, 2.6), (0, Y - 1.5, 1.9))], lens=26)
track("maru", mr.body, 0.6); track("P_top", head, 0.45)
anchor_at("A_top", (AX, AY, AZ + 0.75)); anchor_at("A_base", (AX, AY - 1.0, 0.3)); anchor_at("P_base", (PX, PY - 1.0, 0.3))
anchor_at("R_base", (AX + 1.6, AY - 1.3, 0.0)); anchor_at("A_side", (AX + 0.9, AY, AZ + 0.3))
finish("s19")
