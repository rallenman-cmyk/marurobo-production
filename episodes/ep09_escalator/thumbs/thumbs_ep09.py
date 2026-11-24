# 9本目（エスカレーター）のサムネ：A・B・D（2026-11-23。サムネ案.md。ユーザー「abdで」）
#   字ごと Lovart の GPT Image 2 に描かせる（SKILL.md §9 の 4）。型は references/thumbnail_rules.md（上に黒い帯・1 行の問い・帯の下は明るい 3D）
#   答え（段は鎖で輪になって床の下を戻る・2 本のレール・くしがすくい上げる）は描かない
#   仕上げ（帯の下の明るさ・鮮やかさ）は 7 本目の thumbs_ep07.py の finish を使う
#   使い方: python3 thumbs_ep09.py <出力フォルダ> A B D   （何も付けないと 3 つとも）
import os, sys, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
import thumb_lovart as T

ROBOT = ("THE ROBOT (must match the attached reference images exactly): a small glossy white sphere robot with ONE large round "
         "teal-and-black camera-lens eye on the front, a small teal round disc on each side, a thin dark antenna with a small glowing orange "
         "ball on top, two short dark legs with chunky dark navy feet with teal soles. NO arms, NO hands, NO mouth, NO eyebrows, no hat. ")
ESC = ("The escalator is a clean modern station escalator: dark grey aluminium steps with fine parallel grooves and yellow edge lines, a "
       "black rubber handrail, a metal landing plate with a comb plate (a row of fine teeth) where the steps slide in. No brand names, no "
       "logos, no signs with writing. ")
STYLE = ("BELOW THE BAND: a bright, clean, polished 3D render (soft daylight, light colors, crisp edges, vivid but not dark). Keep the "
         "bottom-right corner (x 86-100%, y 84-100%) free of important things. Red circles are bright red rings with a thin white outline. ")

PLANS = {
 # A 段が消える所：降り口のくしに吸いこまれる段、段に乗ったまま近づくまるロボ。くしのすき間に赤い丸
 "A": ([("エスカレーター", "bright yellow"), ("の", "white"), ("段はどこへ", "bright red"), ("?", "white")],
       "Low close-up at the TOP landing of an escalator, seen from the side and slightly above: the last steps are flattening out and "
       "sliding one by one into the narrow gap under the comb plate teeth, disappearing into the floor. The small robot stands on the "
       "second-to-last flat step, riding toward the gap, its lens eye wide open in surprise, looking down at the gap (robot about 25% of the "
       "image height, in the left-center). A red circle around the gap where the steps disappear (right-center). " + ESC),
 # B 床の下をのぞく：夜の点検、降り口の床のふたが開いて暗い穴。まるロボが目のライトでのぞく（中は見せない）
 "B": ([("エスカレーター", "bright yellow"), ("の", "white"), ("床の下", "bright red"), ("は?", "white")],
       "Night inspection time at a quiet, softly lit station (still bright and clean, not dark overall): at the top landing of a stopped "
       "escalator, the metal floor plate (the access lid) is lifted open and leaning aside, revealing a deep DARK rectangular hole in the "
       "floor; inside the hole only darkness is visible (do NOT show any machinery). The small robot stands at the edge of the hole, leaning "
       "forward and peering down into it, a soft beam of light shining from its lens eye into the dark hole (robot about 25% of the image "
       "height). A red circle around the dark hole. " + ESC),
 # D はさまらないのは？：くしの歯と段の溝の寄り、くつのつま先、赤い丸。まるロボは横で見る
 "D": ([("なぜ", "white"), ("足", "bright yellow"), ("が", "white"), ("はさまらない", "bright red"), ("?", "white")],
       "Big macro close-up of where a moving escalator step meets the comb plate: the fine teeth of the comb plate mesh exactly into the "
       "grooves of the step surface. The toe of a clean white sneaker rests on the step just before the comb teeth (the foot is safe, calm "
       "everyday situation, nothing dangerous happening). A red circle around the comb teeth where they meet the step grooves. The small "
       "robot stands on the landing plate at the left, looking at the comb teeth with a curious wide-open eye (robot about 22% of the image "
       "height). " + ESC),

 # 2026-11-24 ユーザー「階段はどこへ見たいな切り口でアングル変えてほしい、確かにって思えるような見せ方で」
 # A3 横から：坂の階段 → 上で平らに → 床のすき間へ。段の流れを赤い矢印でなぞり、床の中は赤い ？ で隠す
 "A3": ([("エスカレーター", "bright yellow"), ("の", "white"), ("階段はどこへ", "bright red"), ("?", "white")],
       "Clean SIDE VIEW of the upper part of a station escalator, like a clear diagram but as a polished 3D render: on the left the steps "
       "climb diagonally as a clear STAIRCASE shape; toward the right, at the top landing, the steps gradually flatten into a flat floor and "
       "slide one by one into the narrow gap under the comb plate, where the solid floor begins. A big bold bright-red curved arrow follows "
       "the steps along the staircase, over the top and dives down into the gap in the floor. Just below the floor surface after the arrow, "
       "a big bright-red question mark on a white round badge (the inside of the floor is hidden, solid, NOT shown). The small robot rides on "
       "one of the stair steps near the top, looking ahead at the gap with a wide-open eye (robot about 20% of the image height). " + ESC),
 # A4 乗っている人の目線：上に着く直前に足もとを見下ろす。目の前の階段がたたまれて平らになり、くしの下へ。まるロボは手前の段
 "A4": ([("エスカレーター", "bright yellow"), ("の", "white"), ("階段はどこへ", "bright red"), ("?", "white")],
       "FIRST-PERSON VIEW of a rider just before reaching the top of a station escalator, looking down and forward: in the foreground the "
       "steps are still a clear STAIRCASE (each step a riser and a tread), and ahead the steps fold down and become a flat floor, then slide "
       "under the comb plate teeth and vanish into the floor at the landing. The black handrails run along both sides toward the landing. "
       "The small robot stands on a step in the lower-center foreground, seen from behind and slightly from the side, its eye glowing, "
       "looking at where the steps vanish (robot about 22% of the image height). A red circle around the line where the steps vanish under "
       "the comb plate. " + ESC),

 # A5（2026-11-24 ユーザー「上りのエスカレーターに乗りながら見上げるアングルで」）：上りに乗って降り口を見上げる。上で階段が平らになって消える所に赤い丸
 "A5": ([("エスカレーター", "bright yellow"), ("の", "white"), ("階段はどこへ", "bright red"), ("?", "white")],
       "FIRST-PERSON VIEW of a rider standing on an ASCENDING (going UP) station escalator, LOOKING UP toward the top: the camera is low on a "
       "step, the stairs rise steeply ahead and above (clear staircase shape: risers and treads, yellow edge lines), the black handrails run "
       "up on both sides converging toward the top. At the TOP, against a bright ceiling and daylight, the last steps flatten out and slide "
       "into the floor at the landing comb plate, so the staircase visibly ends and disappears over the top edge. The small robot rides a "
       "few steps ahead (about 22% of the image height, center-left), seen from behind and slightly from the side, its head tilted up toward "
       "the top. A red circle around the spot at the top where the steps flatten and vanish into the floor. " + ESC),
}
REFS = ["robot_front", "robot_34", "robot_side", "robot_antenna"]


def prompt(name):
    runs, scene = PLANS[name]
    return T.band_block(runs) + "\n" + STYLE + "\n" + scene + "\n\n" + ROBOT


if __name__ == "__main__":
    out = sys.argv[1]; names = sys.argv[2:] or list(PLANS)
    os.makedirs(out, exist_ok=True)
    th = [threading.Thread(target=T.gen, args=(out, n, prompt(n), REFS)) for n in names]
    for t in th: t.start()
    for t in th: t.join()
