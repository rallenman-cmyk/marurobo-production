# 4本目「私はロボットではありません」のサムネ（2026-11-19、サムネのリサーチ.md の設計書 A・B・C）
#   絵は Gemini の画像の AI（gemini-3-pro-image）に「字なし」で描かせ（gen）、字・チェック欄の字・印はこちらで重ねる（comp）。
#   字の重ね方の部品は 2本目の thumbs_v3.py（極太字・ふち・札・矢印・印）をそのまま使う
#   使い方: THUMB_WORK=<作業> THUMB_FONT=<NotoSansJP[wght].ttf> python3 thumbs04.py gen A B C ／ comp '{"A":"A_1.png",...}'
#   見本のコマ（本物のまるロボ）：<作業>/src/r1.png〜r4.png（PC の ep04_v15 の mp4 から）
import os, sys, json, importlib.util
H_ = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("tv3", os.path.join(H_, "..", "..", "ep02_qr", "thumbs", "thumbs_v3.py"))
T = importlib.util.module_from_spec(_sp); sys.argv_ = sys.argv; sys.argv = [sys.argv[0], "x"]; _sp.loader.exec_module(T); sys.argv = sys.argv_
from PIL import Image, ImageDraw, ImageFilter
W, H = T.W, T.H
ROBOT = ("The mascot robot must match the reference images exactly: a glossy white sphere body, ONE large round camera-lens eye on the front "
         "(dark navy outer ring, teal iris ring, glossy dark pupil), small teal discs on the sides, a thin grey antenna on the upper-left with a small "
         "beige-orange ball on top, two short stubby grey legs with dark navy boots whose soles glow teal. No mouth, no arms, no hands.")
BASE = ("Background art for a YouTube thumbnail, 16:9, polished cinematic 3D render like a high-end tech explainer channel (Pixar-like lighting). "
        "ABSOLUTELY NO TEXT: no letters, no words, no numbers, no logos anywhere. " + ROBOT)
BOX = ("A giant floating web 'I am not a robot' verification card: a clean white rounded rectangle panel with a soft shadow, an EMPTY square "
       "checkbox outline on its left part, a plain blank area where the label would be (leave it completely blank, no letters), and a small blue-grey "
       "circular-arrows icon on its right part. ")
PLANS = {
 "A": ("Dark navy-blue room at night, soft rim lights. " + BOX + "The card is huge and fills the RIGHT 58% of the frame (x 40-98%, y 30-78%), slightly "
       "tilted toward the camera. The robot (about 40% of the frame height) is standing ON TOP of the card, both boots planted on the EMPTY checkbox, "
       "pressing it down with its weight (the checkbox pushed in a little), body facing the camera so its big eye is clearly visible. The robot has NO arms "
       "and NO hands at all: it presses only by standing on the box with its two legs. A soft red glow ring around the checkbox. "
       "STRICT LAYOUT: the whole TOP-LEFT area (x 0-45%, y 0-60%) is plain dark background with nothing in it. Bottom-right corner free."),
 "B": ("Dark navy-blue room at night, soft rim lights. " + BOX.replace("an EMPTY square checkbox outline", "a square checkbox with a bright GREEN CHECK MARK in it")
       + "The card fills the RIGHT 55% (x 42-98%, y 18-60%). The robot (about 38% of the frame height) stands below the card at x 50-70%, y 55-98%, "
       "looking up at the check mark, surprised: its single eye opened wide and glowing brighter, leaning back a little. The robot has NO mouth (the body is a smooth white sphere except the one eye) and NO arms. On the floor behind the robot, two "
       "footprint trails made of small glowing dots: one perfectly STRAIGHT trail of teal dots, one wavy curvy trail of orange dots. "
       "STRICT LAYOUT: the whole LEFT 40% of the frame (x 0-40%) is plain dark background with nothing in it."),
 "C": ("Dark navy-blue digital space with a faint glowing grid floor. A big floating image-selection test panel: a 4x4 grid of photo tiles of a street "
       "with a traffic light (realistic street photos, the traffic light pole crossing several tiles; one tile at the edge shows only a tiny sliver of the "
       "traffic light). Some tiles are highlighted blue as selected. The panel fills the RIGHT 55% of the frame (x 42-98%, y 8-80%). The robot (about 35% "
       "of the frame height) stands at x 46-62%, y 62-98% in front of the panel, head tilted, confused, looking up at the panel. "
       "STRICT LAYOUT: the whole LEFT 40% of the frame (x 0-40%) is plain dark background with nothing in it."),
}
T.PLANS.update({k: v for k, v in PLANS.items()}); T.BASE = BASE


def label(im, box, txt="私はロボットではありません", col=(40, 44, 52)):
    """絵の AI が描いた空のチェック欄に、こちらで字を書く。box＝欄の白い札の (左, 上, 右, 下)"""
    x0, y0, x1, y1 = box; h = y1 - y0; px = int(h * 0.26)
    f = T.F(px, 500)
    while f.getlength(txt) > (x1 - x0) * 0.55 and px > 20: px -= 2; f = T.F(px, 500)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    b = f.getbbox(txt); d.text((x0 + (x1 - x0) * 0.22, y0 + (h - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill=col + (255,))
    return Image.alpha_composite(im, lay)


def card_tag(im, xy, txt="私はロボットではありません", px=70):
    """左上の札：本編のチェック欄と同じ形（白い札・□・紺の字）。何の話かが一目で分かるように"""
    x, y = xy; f = T.F(px, 700); tw = f.getlength(txt); h = int(px * 1.7); bs = int(px * 0.95); pad = int(px * 0.45)
    w = pad + bs + pad + tw + pad
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle((x + 6, y + 10, x + w + 6, y + h + 10), 18, fill=(0, 0, 0, 130))
    d.rounded_rectangle((x, y, x + w, y + h), 18, fill=(250, 251, 252, 255))
    by = y + (h - bs) // 2; d.rounded_rectangle((x + pad, by, x + pad + bs, by + bs), 8, outline=(60, 68, 80, 255), width=6, fill=(255, 255, 255, 255))
    b = f.getbbox(txt); d.text((x + pad * 2 + bs, y + (h - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill=(24, 34, 56, 255))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)


LAYOUT = {   # 案 → [行]（[(字, 色)]）・字の右の端
 "A": ([[("ロボットが", T.WHITE)], [("押したら？", T.YEL)]], 1080),
 "B": ([[("ロボットでも", T.WHITE)], [("通った!?", T.YEL)]], 880),   # 右の欄（x 928〜）に字をかけない
 "C": ([[("この", T.WHITE), ("マス", T.YEL)], [("選ぶ？", T.YEL)]], 980),
}


def comp(choice, boxes):
    out = []
    for name, src in choice.items():
        k = name.split("_")[0]; im = T.bg(os.path.join(T.G, src))
        if boxes.get(name): im = label(im, boxes[name])
        im = card_tag(im, (70, 56))
        rows, maxw = LAYOUT[k]; px = min(T.fit(r, maxw - 80, 330) for r in rows); y = 290
        for r in rows:
            im, _ = T.line(im, (80, y), r, px, T.BLACK, ew=int(px * 0.14)); y += int(px * 1.06)
        out.append(T.save(im, "ep04_" + name))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]: T.gen(a, refs=("r1.png", "r2.png", "r3.png", "r4.png"))
    else:
        print("\n".join(comp(json.loads(sys.argv[2]), json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})))
