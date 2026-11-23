# 3本目（会話と広告）のサムネ：A・B・A2（2026-11-23。サムネ案_字ごと.md。ユーザー「AとBつくって、あとはAを違う見せ方でつくって」）
#   字ごと Lovart の GPT Image 2 に描かせる（SKILL.md §9 の 4）。型は references/thumbnail_rules.md（上に黒い帯・1 行の問い・帯の下は明るい 3D）
#   見本：探偵の帽子のまるロボ（robot_cap_*）と、本編のテントの広告の画面（tent_ad_screen）。references/lovart_refs.json
#   仕上げ（帯の下の明るさ・鮮やかさ）は 7 本目の thumbs_ep07.py の finish を使う
#   使い方: python3 thumbs_ep03_lovart.py <出力フォルダ> A B A2   （何も付けないと 3 つとも）
import os, sys, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
import thumb_lovart as T

ROBOT = ("THE ROBOT (must match the attached robot reference images exactly): a small glossy white sphere robot with ONE large round "
         "teal-and-black camera-lens eye on the front, a small teal round disc on each side, a thin dark antenna with a small glowing orange "
         "ball on top, two short dark legs with chunky dark navy feet with teal soles, wearing a small brown checkered detective cap (deerstalker "
         "style) tilted on its head. NO arms, NO hands, NO mouth, NO eyebrows. ")
PEOPLE = ("People are simple rounded soft 3D cartoon adults with smooth friendly faces (like a polished explainer animation): one in a blue "
          "hoodie, one in a peach hoodie with a teal scarf. ")
AD = ("The tent ad on the phone screen must look like the attached ad reference: a simple flat picture of an orange tent on green grass under "
      "a pale blue sky with a small yellow sun, and a pale teal rounded button below; NO letters on the screen. ")
STYLE = ("BELOW THE BAND: a bright, clean, polished soft 3D illustration (soft daylight, light pastel colors, crisp edges, vivid but not "
         "dark). Keep the bottom-right corner (x 86-100%, y 84-100%) free of important things. Red arrows and red circles are bright red with "
         "a thin white outline. Do not show any brand logos. ")

PLANS = {
 # A 前→後：電車で話す二人（吹き出しにテントの絵）→ 赤い矢印 → 手に持ったスマホにテントの広告
 "A": ([("話しただけで", "bright red"), ("なぜ", "white"), ("広告", "bright yellow"), ("に?", "white")],
       "LEFT half: two cartoon adults sit side by side on a bright commuter-train seat chatting happily; above them one large white rounded "
       "speech bubble with a thick black outline containing ONLY a simple orange tent drawing (no letters). MIDDLE: one big bold bright-red "
       "arrow pointing from the speech bubble to the right. RIGHT half: a hand holds a modern smartphone upright facing the camera, LARGE, its "
       "screen showing the tent ad. The small robot stands at the lower left on the floor in front of the seat (about 20% of the image "
       "height), looking at the phone in surprise. " + PEOPLE + AD),
 # B スマホに大きな耳：話す二人の声の線が耳へ、驚くまるロボ
 "B": ([("スマホ", "bright yellow"), ("は", "white"), ("会話を聞いてる", "bright red"), ("?", "white")],
       "A modern smartphone stands upright on a light wooden table in the center-right, LARGE, facing the camera, its screen plain dark; a big "
       "friendly cartoon HUMAN EAR is attached to the side of the phone, clearly listening. On the left, two cartoon adults sit at the table "
       "talking to each other; soft curved light-blue sound-wave lines flow from their mouths toward the ear. The small robot stands on the "
       "table in the lower-left foreground (about 22% of the image height), looking at the phone with a surprised wide-open lens eye. Only "
       "these things. " + PEOPLE),
 # A2（A の別の見せ方）1 つの場面：夜、ベッドでスマホを見る人の画面にテントの広告。頭の上の思い出の雲に、昼の電車で話す二人
 "A2": ([("話しただけで", "bright red"), ("なぜ", "white"), ("広告", "bright yellow"), ("に?", "white")],
       "ONE scene, night in a cozy bedroom with warm soft lamp light (still bright and clear, not dark): the person in the blue hoodie lies in "
       "bed holding a smartphone, the phone LARGE in the right-center facing the camera showing the tent ad, the person's face shocked "
       "(eyes wide). Above the person's head, a big soft white thought cloud (memory bubble) shows a small daytime scene: the same two people "
       "chatting on a commuter train with a tiny orange tent drawing between them. A red circle around the tent ad on the phone screen. The "
       "small robot peeks over the edge of the bed at the lower left (about 20% of the image height), surprised. " + PEOPLE + AD),
}
REFS = ["robot_cap_front", "robot_cap_34", "robot_cap_side", "robot_antenna", "tent_ad_screen"]


def prompt(name):
    runs, scene = PLANS[name]
    return T.band_block(runs) + "\n" + STYLE + "\n" + scene + "\n\n" + ROBOT


if __name__ == "__main__":
    out = sys.argv[1]; names = sys.argv[2:] or list(PLANS)
    os.makedirs(out, exist_ok=True)
    th = [threading.Thread(target=T.gen, args=(out, n, prompt(n), REFS)) for n in names]
    for t in th: t.start()
    for t in th: t.join()
