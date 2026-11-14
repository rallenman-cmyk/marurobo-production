# S20「2024年：絵のテストも AI がほぼ解けた／2025年：ChatGPT が自分で『人間です』にチェック」（8:47〜9:30）を 3D で
#   まん中の板：絵のテスト（光の線で読まれ、緑の枠）→ ふつうのページ → チェック欄。AI（左）が矢印を動かして、チェックを入れる
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_head.py"), encoding="utf-8").read())
span(said("2024年には"), next_sub("先へ進んでしまった"))
t_25, t_op, t_one, t_chk, t_wrote, t_quote, t_click, t_go = (said("そして2025年"), said("ChatGPTに、自分で"), said("ある人が、この機能"),
    said("途中で、人間かどうか"), said("するとAIは、作業"), said("「ロボットではないことを"), said("そして、ロボットであるAIが"), said("先へ進んでしまった"))
setup_stage()
Y, BZ = 4.9, 2.75
AX, AY, AZ = -3.4, 2.6, 1.75
podium(AX, AY, TE, "A")
dots, gA = build(lambda: chatbot(AX, AY, AZ, 0.85), (AX, AY, AZ))
bob(gA, T0, T1, 0.07, 2.2)
think(dots, T0 + 0.5, 5); think(dots, t_op + 0.5, 5); think(dots, t_wrote, 8)
# 2024年：絵のテスト → 読まれて緑の枠
_im = bpy.data.images.load(os.path.join(TEX, "scr_test.png")); TW = 3.6; TH = TW * _im.size[1] / _im.size[0]
_, gT = build(lambda: board("scr_test", 0, Y, BZ, TW, TH, emit=0.5, name="t24"), (0, Y, BZ))
pop(gT, T0 + 0.1); ev(T0 + 0.1, "whoosh", 0.3)
scan(-TW / 2 + 0.2, TW / 2 - 0.2, Y - 0.12, BZ, TH * 0.85, T0 + 0.9, T0 + 3.3, 1.2)
_, gG = build(lambda: frame_rect(0, Y - 0.15, BZ, TW + 0.25, TH + 0.25, GRN, "t24ok", th=0.06, emit=5.0), (0, Y - 0.15, BZ))
pop(gG, T0 + 3.6, 0.35); ev(T0 + 3.6, "lamp", 0.35)
for g in (gT, gG): vanish(g, t_25, 0.3)
# 2025年：ページの板（チェック欄へ替わる → チェックが入る）
PW = 5.4; PH = PW * 1000 / 1600
pm, gPg = build(lambda: board("lk_page", 0.4, Y, BZ, PW, PH, emit=0.45, name="pg"), (0.4, Y, BZ))
pop(gPg, t_op + 0.1); ev(t_op + 0.1, "whoosh", 0.3); bob(gPg, t_op + 0.6, T1, 0.035, 2.8)
swap_tex(pm, "lk_check", t_chk + 0.2); ev(t_chk + 0.2, "pop_ui", 0.5)
# チェック欄の場所（絵の左から 0.296・上から 0.51）
BX, BZ2 = 0.4 + (0.296 - 0.5) * PW, BZ + (0.5 - 0.51) * PH
def swap2(m, tex, t):
    nt = m.node_tree; mx = [n for n in nt.nodes if n.type == 'MIX_RGB'][0]
    t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = bpy.data.images.load(os.path.join(TEX, tex + ".png"))
    m2 = nt.nodes.new("ShaderNodeMixRGB"); m2.inputs[0].default_value = 0.0
    b = nt.nodes["Principled BSDF"]
    nt.links.new(mx.outputs[0], m2.inputs[1]); nt.links.new(t2.outputs["Color"], m2.inputs[2])
    nt.links.new(m2.outputs[0], b.inputs["Base Color"]); nt.links.new(m2.outputs[0], b.inputs["Emission Color"])
    m2.inputs[0].keyframe_insert("default_value", frame=f(t) - 1); m2.inputs[0].default_value = 1.0; m2.inputs[0].keyframe_insert("default_value", frame=f(t) + 1)
swap2(pm, "scr_pass", t_click + 1.6)
# 矢印：ページの上を動き回り（作業中）、最後に欄を押す
cur = cursor()
y_c = Y - 0.25
pts = [(t_op + 0.4, (1.8, y_c, BZ + 0.6)), (t_op + 2.0, (-0.6, y_c, BZ + 0.3)), (t_op + 3.6, (1.2, y_c, BZ - 0.4)),
       (t_one + 0.5, (0.2, y_c, BZ + 0.7)), (t_one + 2.5, (2.0, y_c, BZ - 0.2)), (t_chk + 0.6, (1.6, y_c, BZ - 0.6)),
       (t_click + 0.2, (1.4, y_c, BZ - 0.5)), (t_click + 1.4, (BX + 0.05, y_c, BZ2 - 0.05))]
key(cur, "scale", f(T0), (0.001,) * 3); key(cur, "scale", f(t_op + 0.3), (0.001,) * 3); key(cur, "scale", f(t_op + 0.6), (1, 1, 1))
for t, p in pts: key(cur, "location", f(t), p)
key(cur, "scale", f(t_click + 1.5), (1, 1, 1)); key(cur, "scale", f(t_click + 1.6), (0.85,) * 3); key(cur, "scale", f(t_click + 1.75), (1, 1, 1))
ev(t_click + 1.6, "click", 0.6)
# 先へ進む：ページが横へ流れて消える
key(gPg, ("location", 0), f(t_go), 0.4); key(gPg, ("location", 0), f(t_go + 0.8), 9.0); ev(t_go, "whoosh", 0.35)
key(cur, "scale", f(t_go), (1, 1, 1)); key(cur, "scale", f(t_go + 0.2), (0.001,) * 3)
# まるロボ：右の手前。チェックが入ると、びっくりして跳ねる
root = maru((2.6, 1.4, 0), face_deg=90, s=0.7, hat=False, eye_glow=1.0, look_up=16)
mr = Maru(root); mr.g0 = 1.0
mr.at(T0 + 0.2, face=10, look=16); breathe(mr, T0 + 0.6, T1, [(t_click + 1.6, t_click + 3.0)])
mr.at(t_25 + 0.3, face=-40, look=10); mr.at(t_chk, face=10, look=18)
mr.hop(t_click + 1.8, 0.35, 0.45); ev(t_click + 1.8, "jump", 0.6); ev(t_click + 2.25, "land", 0.6)
mr.glow(t_click + 1.8, 1.0, 2.6, 0.2); mr.glow(t_click + 3.0, 2.6, 1.0, 0.6)
mr.at(t_go, face=-30, look=10)
dolly([(T0, (-0.6, -6.6, 2.5), (-0.2, Y - 1.4, 2.0)), (t_chk, (0.2, -6.2, 2.5), (0, Y - 1.4, 2.0)), (T1, (0.0, -5.5, 2.4), (0, Y - 1.4, 2.0))], lens=26)
track("maru", mr.body, 0.6)
anchor_at("A_top", (AX, AY, AZ + 0.75)); anchor_at("A_base", (AX, AY - 1.0, 0.3))
anchor_at("board_top", (0.4, Y, BZ + PH / 2 + 0.2)); anchor_at("box", (BX, Y - 0.1, BZ2))
finish("s20")
