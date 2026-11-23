# 7本目（キーボード・クワーティ）のサムネ：A・D2・I（2026-11-23。サムネ案.md の §4。ユーザー「そのみっつつくって」）
#   字ごと Lovart の GPT Image 2 に描かせる（SKILL.md §9 の 4）。型は references/thumbnail_rules.md（上に黒い帯・1 行の問い・帯の下は明るい 3D）
#   使い方: python3 thumbs_ep07.py <出力フォルダ> A D2 I   （何も付けないと 3 つとも。並べて頼む）
import os, sys, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
import thumb_lovart as T

ROBOT = ("THE ROBOT (must match the attached reference images exactly): a small glossy white sphere robot with ONE large round "
         "teal-and-black camera-lens eye on the front, a small teal round disc on each side, a thin dark antenna with a small glowing orange "
         "ball on top, two short dark legs with chunky dark navy feet with teal soles. NO arms, NO hands, NO mouth. ")
STYLE = ("BELOW THE BAND: a bright, clean, polished 3D render (soft daylight, light wooden desk, white and light pastel colors, crisp edges, "
         "vivid but not dark). Keep the bottom-right corner (x 86-100%, y 84-100%) free of important things. Red circles are bright red "
         "rings with a thin white outline, drawn on top of the scene. ")
KEYS_NOTE = "Letters printed on the keys must be crisp, correct single Latin capital letters exactly as listed. "

PLANS = {
 # A（採用）左右の比べ：今のキーボード（QWERTY）と、同じ形の ABC 順のキーボード。比べる所を赤い丸で囲む（？は使わない）
 "A": ([("なぜ", "white"), ("キーボード", "bright yellow"), ("は", "white"), ("ABC順じゃない", "bright red"), ("?", "white")],
       "Two identical modern white keyboards side by side on the desk, seen from slightly above and in front, each large (each about 44% "
       "of the width). LEFT keyboard: the normal layout, top letter row Q W E R T Y U I O P, middle row A S D F G H J K L, bottom row "
       "Z X C V B N M. RIGHT keyboard: exactly the same shape and size, but the letters are in alphabetical order: top row A B C D E F G H I J, "
       "middle row K L M N O P Q R S, bottom row T U V W X Y Z. One red circle (ellipse) around Q W E R T Y on the left keyboard, one red circle "
       "around A B C D E F on the right keyboard. The small robot stands on the desk between the two keyboards at the bottom center (about 22% "
       "of the image height), looking from one keyboard to the other, curious. " + KEYS_NOTE),
 # D2 昔→今（建物の深層の当たりの形）：1868 年のピアノ形のタイプライター（ABC 順）→ 赤い矢印 → 今のキーボード
 "D2": ([("なぜ", "white"), ("キーボード", "bright yellow"), ("は", "white"), ("ABC順をやめた", "bright red"), ("?", "white")],
       "LEFT half: an antique 1868-style typewriter whose keyboard looks like a PIANO keyboard: two rows of flat piano-like black and white keys "
       "in wood and brass, with letters on the keys in alphabetical order: front row A B C D E F G, back row O P Q R S T U (only these letters, "
       "large and readable). A red circle around A B C. In the MIDDLE: one big bold bright-red arrow pointing from left to right (with a thin "
       "white outline). RIGHT half: a modern white computer keyboard, top letter row Q W E R T Y U I O P clearly visible, with a red circle "
       "around Q W E. Both objects large and clean on the light desk. The small robot stands at the lower left in front of the old typewriter "
       "(about 20% of the image height), looking up at the arrow. " + KEYS_NOTE),
 # I 150 年変わらない：古いタイプライターとスマホの画面のキーボード、どちらも QWERTY。間に大きな「＝」
 "I": ([("なぜ", "white"), ("150年も", "bright yellow"), ("同じ並び", "bright red"), ("?", "white")],
       "LEFT: an antique black 1870s-style typewriter with round keys, its top letter row Q W E R T Y clearly readable on the round keys, red "
       "circle around Q W E R T Y. MIDDLE: a big bold bright-red equals sign (=) with a thin white outline. RIGHT: a modern smartphone standing "
       "upright, screen showing a clean on-screen keyboard whose top row is Q W E R T Y U I O P, red circle around Q W E R T Y. Both objects "
       "large. The small robot stands at the lower left near the typewriter (about 20% of the image height), looking at the smartphone in "
       "surprise. " + KEYS_NOTE),
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
