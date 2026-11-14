# S07〜S08「昔のテスト：ゆがんだ文字」（1:52〜2:36）を 3D で
#   宙に浮く大きな板にゆがんだ 2 つの単語。人（読める）と機械（読めない）→ 2 つの種類（枠が光る）
#   → 出題する側（紺の箱）が答えを知っている単語／知らない単語（右がオレンジに）。まるロボは下から見上げる
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("少し前まで"), next_sub("いったい、何のために"))
t_type, t_who, t_two, t_known, t_other, t_unk, t_why = (said("ぐにゃぐにゃ"), said("人には読める"), said("実は、このゆがんだ"),
                                                      said("1つは、出題"), said("では、もう1つは"), said("実は、出題する側も"), said("いったい、何のために"))
setup_stage()
Y, BZ, BW, BH = 4.8, 3.05, 6.6, 6.6 * 270 / 1000
bm, gB = build(lambda: board("lk_captcha", 0, Y, BZ, BW, BH, emit=0.5), (0, Y, BZ))
rise(gB, T0, 3.0, 1.0); bob(gB, T0 + 1.1, T1, 0.04, 2.8)
ev(T0 + 0.1, "whoosh", 0.35)
swap_tex(bm, "lk_captcha_r", t_other + 0.3)
# 単語の場所（板の絵の中の場所から）
def wpos(u0, u1):
    return ((u0 + u1) / 2 - 0.5) * BW, BZ + (0.5 - 115 / 270) * BH, (u1 - u0) * BW
xL, zW, wL = wpos(0.035, 0.49); xR, _, wR = wpos(0.545, 0.93)
fL, gFL = build(lambda: frame_rect(xL, Y - 0.12, zW, wL, 0.62 * BH, TE, "frL"), (xL, Y - 0.12, zW))
fR, gFR = build(lambda: frame_rect(xR, Y - 0.12, zW, wR, 0.62 * BH, OR, "frR"), (xR, Y - 0.12, zW))
pop(gFL, t_two + 0.5, 0.35); pop(gFR, t_two + 0.9, 0.35); ev(t_two + 0.5, "lamp", 0.35); ev(t_two + 0.9, "lamp", 0.35)
for g in (gFL, gFR): bob(g, t_two + 1.3, T1, 0.04, 2.8)   # 板と一緒に浮く（だいたい）
# 右の枠：「もう1つは」で強く光る
matkey(fR, f(t_other), 4.0); matkey(fR, f(t_other + 0.25), 9.0); matkey(fR, f(t_other + 0.8), 4.0)
# 人と機械（「人には読めるけれど、機械には読めない」）
PX, PY = 2.9, 2.3
(head, gP) = build(lambda: (podium(-PX, PY, OR, "L"), person(-PX, PY))[1], (-PX, PY, 0))
(dots, gM) = build(lambda: (podium(PX, PY, TE, "R"), machine(PX, PY))[1], (PX, PY, 0))
pop(gP, t_who - 0.1); pop(gM, t_who + 0.3); ev(t_who - 0.1, "pop", 0.6); ev(t_who + 0.3, "pop", 0.6)
think(dots, t_who + 1.3, 4)
_, gO = build(lambda: ring3d(-PX + 1.0, PY, 1.7, 0.28, GRN, "okring", minor=0.07, emit=2.0), (-PX + 1.0, PY, 1.7))
_, gX = build(lambda: xmark(PX + 1.15, PY, 1.7, 0.42), (PX + 1.15, PY, 1.7))
pop(gO, t_who + 1.0); ev(t_who + 1.0, "pipo", 0.5)
pop(gX, t_who + 2.8); ev(t_who + 2.8, "down", 0.6)
for g in (gP, gM, gO, gX): vanish(g, t_two - 0.1, 0.35)
ev(t_two - 0.1, "whoosh", 0.3)
# 出題する側（紺の箱に白い目）
def asker():
    cube(mat("ask_body", "#2F4A73", rough=0.3, coat=0.6), (0, 0, 0), (0.7, 0.5, 0.7), bevel=0.15)
    sphere(mat("ask_eye", "#FFFFFF", emit=2.0), (0, -0.25, 0.02), 0.17, scale=(1, 0.4, 1))
_, gA = build(asker, (0, 0, 0)); gA.location = (BW / 2 + 0.75, Y - 0.2, BZ + 0.9)
pop(gA, t_known - 0.1); bob(gA, t_known + 0.5, T1, 0.06, 2.0)
# まるロボ：下から見上げる
root = maru((0, 1.2, 0), face_deg=90, s=0.75, hat=False, eye_glow=1.0, look_up=24)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=0, look=24); breathe(mr, T0 + 0.6, T1)
mr.at(t_who + 0.2, face=-50, look=10); mr.at(t_who + 2.6, face=50, look=10)
mr.at(t_two - 0.2, face=0, look=24)
mr.at(t_known + 0.2, face=-15, look=26); mr.at(t_other + 0.2, face=15, look=26)
mr.tilt(t_unk + 0.3, 14, 0.35); mr.tilt(t_why, -12, 0.4)
dolly([(T0, (0.6, -6.6, 2.4), (0, Y, 2.1)), (t_two, (-0.3, -6.2, 2.3), (0, Y, 2.1)), (T1, (0.4, -5.8, 2.3), (0, Y, 2.15))], lens=27)
track("maru", mr.body, 0.6); track("L_top", head, 0.45)
anchor_at("R_top", (PX, PY, 1.9)); anchor_at("L_base", (-PX, PY - 1.0, 0.3)); anchor_at("R_base", (PX, PY - 1.0, 0.3))
anchor_at("wL", (xL, Y - 0.12, zW + 0.31 * BH)); anchor_at("wR", (xR, Y - 0.12, zW + 0.31 * BH))
anchor_at("asker", (BW / 2 + 0.75, Y - 0.2, BZ + 0.9))
finish("s07")
