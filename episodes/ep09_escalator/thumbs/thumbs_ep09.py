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
