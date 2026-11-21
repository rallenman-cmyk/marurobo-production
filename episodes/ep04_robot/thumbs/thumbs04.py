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
        k = name.split("_")[0]; im = grade(T.bg(os.path.join(T.G, src)))
        if boxes.get(name): im = label(im, boxes[name])
        im = card_tag(im, (70, 56))
        rows, maxw = LAYOUT[k]; px = min(T.fit(r, maxw - 80, 330) for r in rows); y = 290
        for r in rows:
            im, _ = T.line(im, (80, y), r, px, T.BLACK, ew=int(px * 0.14)); y += int(px * 1.06)
        out.append(T.save(im, "ep04_" + name))
    return out


# ---------------- 建物の深層（@tatemono-shinsou）の型（2026-11-19 ユーザー「このチャンネルのサムネとかすごいうまい」）
#   上に黒い帯（高さの 17%）・白い極太字 1 行の問い、大事な言葉を黄色と赤。下は明るく清潔な 3D の絵。
#   前→後の比べ（赤い矢印）と、おかしな一点を赤い丸で囲む。字は帯の中だけ。絵の中には字を入れない
BRIGHT = ("Background art for a YouTube thumbnail, 16:9, bright clean soft 3D illustration (like a polished explainer: soft daylight, white and light "
          "pastel colors, slightly low-poly smooth shading, crisp). ABSOLUTELY NO TEXT, no letters, no numbers, no logos, no speech bubbles. "
          "The TOP 18% of the frame will be covered by a black title band, so put nothing important there. " + ROBOT)
PLANS2 = {
 "D": ("Split comparison in two halves side by side, both bright rooms with a white desk and a laptop. LEFT half: a cheerful young person (simple "
       "rounded 3D character) clicking the mouse; on the laptop screen a white web card with a big GREEN CHECK MARK. RIGHT half: the robot standing on "
       "the desk next to the laptop, pushing the mouse with its body; on its laptop screen a 3x3 grid of small street photos with traffic lights (an image "
       "test) popped up, and a big soft red glow around that screen. The robot looks puzzled. Both laptops large and clearly visible."),
 "E": ("A large bright white web verification card fills the middle (x 10-90%, y 22-80%): an EMPTY square checkbox on its left part, a blank area, a "
       "small grey circular-arrows icon on its right. On the card surface, two mouse-cursor paths lead to the checkbox: one PERFECTLY STRAIGHT path of "
       "teal dots coming from the lower right, and one WAVY wandering path of orange dots coming from the lower left. Two small black arrow cursors at the "
       "start of each path. The robot (about 35% of the frame height) stands at the lower right (x 70-90%, y 55-98%) looking at the straight teal path."),
 "F": ("Bright tidy room, white desk, a large open laptop in the center-left (x 15-65%, y 22-90%). On its screen: a 3x3 grid of small street photos with "
       "traffic lights (an image test). The robot (about 40% of the frame height) stands ON the desk at the right (x 66-88%, y 45-98%), facing the "
       "laptop, its single eye wide open in surprise, leaning back a little. A white computer mouse in front of the robot."),
}
T.PLANS.update(PLANS2)
BAND = {   # 案 → [(字, 色)]
 "D": [("なぜ", "W"), ("ロボット", "Y"), ("だけ", "W"), ("バレる", "R"), ("のか？", "W")],
 "E": [("なぜ", "W"), ("チェック1つ", "Y"), ("で", "W"), ("見抜ける", "R"), ("のか？", "W")],
 "F": [("ロボット", "Y"), ("が押すと", "W"), ("どうなる", "R"), ("？", "W")],
 # 2026-11-19 ユーザー「ばれる・見抜ける・どうなるは言い方が分かりにくい」→ 言い換えの案
 "V1": [("同じボタン", "Y"), ("なのに、なぜ", "W"), ("結果が違う", "R"), ("？", "W")],
 "V2": [("押しただけ", "Y"), ("で、なぜ", "W"), ("ロボットと分かる", "R"), ("？", "W")],
 "V3": [("なぜ", "W"), ("ロボット", "Y"), ("が押すと", "W"), ("止められる", "R"), ("のか？", "W")],
 "V4": [("このチェック欄", "Y"), ("、", "W"), ("何を見ている", "R"), ("？", "W")],
 "V5": [("なぜ", "W"), ("押し方", "R"), ("で", "W"), ("ロボット", "Y"), ("と分かる？", "W")],
 "V6": [("ロボット", "Y"), ("が押したら", "W"), ("通れる", "R"), ("？", "W")],
}
CIRCLES = {"D": [(2104, 744, 300)], "E": [(1330, 815, 230)]}   # 名前 → [(中心x, 中心y, 半径)]（2560×1440 で。絵を見て決めた：D は右の画面の絵のテスト、E はまっすぐの点線）
BAND_LABEL = {"E": (416, 352, 2144, 714)}   # 絵のチェック欄に字を書く所（E_2.png の白い札）
ARROWS = {}    # 名前 → [((x0, y0), (x1, y1))]

# 2026-11-19 ユーザー「文字はいいけど絵がわかりにくい」→ 左右の比べ・大きな正面向きのチェック欄・物を少なく（G＝D の字、H＝E の字、I＝F の字）
CARD = ("a big flat white web checkbox card facing the camera straight on (a clean white rounded rectangle, a square checkbox on its left, a blank "
        "light-grey bar where a label would be, NO letters at all)")
PLANS3 = {
 "G": ("Two panels side by side separated by a thin white gap, same bright clean room in both. In EACH panel a laptop seen from the front, its screen "
       "filling most of the panel, showing " + CARD + ". LEFT panel: a friendly young person (simple rounded 3D character) sits in front clicking the "
       "mouse, and the checkbox on the screen has a big bright GREEN CHECK MARK. RIGHT panel: the robot stands on the desk in front of its laptop, "
       "pushing the mouse with its body, and on its screen the checkbox stays EMPTY while a pop-up image test (a 3x3 grid of street photos with traffic "
       "lights) covers the right part of the screen. Big, simple, readable at small size."),
 "H": ("Two panels side by side separated by a thin white gap, bright clean background. In EACH panel " + CARD + " fills the upper half of the panel, "
       "and a black mouse-cursor path leads up to its checkbox from below. LEFT panel: the path is a WAVY, wandering line of ORANGE dots; a friendly "
       "young person (simple rounded 3D character) stands at the bottom holding a computer mouse, and the checkbox has a big GREEN CHECK MARK. RIGHT "
       "panel: the path is a PERFECTLY STRAIGHT ruler-like line of TEAL dots; the robot stands at the bottom, and the checkbox stays EMPTY. "
       "Big, simple, readable at small size."),
 "I": ("Two panels side by side separated by a thin white gap (before / after), bright clean room, a laptop seen from the front in both, its screen "
       "filling most of the panel. LEFT panel (before): the screen shows " + CARD + " and the robot stands on the desk pushing the mouse with its body, "
       "determined. RIGHT panel (after): on the same screen a large pop-up image test (a 3x3 grid of street photos with traffic lights) has appeared over "
       "the checkbox card, and the robot leans back in surprise, eye wide open. Big, simple, readable at small size."),
}
T.PLANS.update(PLANS3); PLANS2.update(PLANS3)
BAND.update({"G": BAND["D"], "H": BAND["E"], "I": BAND["F"]})
CIRCLES.update({"G": [(2350, 680, 270)], "H": [(1600, 980, 200)], "I": [(1888, 700, 300)]})   # G＝右の絵のテスト、H＝まっすぐの線、I＝出てきた絵のテスト
ARROWS.update({"I": [((1140, 760), (1430, 760))], "L": [((1140, 900), (1430, 900))]})                                               # I：前→後（2 つの絵の間）
BARS = {"H": [(432, 346, 1072, 480), (1728, 346, 2362, 480)], "K": [(1584, 618, 2208, 858)], "K2": [(1114, 493, 1600, 563)], "L": [(512, 637, 832, 701)]}                                      # 絵の灰色の帯（チェック欄の字の所）に字を書く


def label_bar(im, box, txt="私はロボットではありません"):
    x0, y0, x1, y1 = box; px = int((y1 - y0) * 0.62); f = T.F(px, 600)
    while f.getlength(txt) > (x1 - x0) * 0.96 and px > 16: px -= 2; f = T.F(px, 600)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); d.rectangle(box, fill=(255, 255, 255, 255))
    b = f.getbbox(txt); d.text((x0 + 6, y0 + (y1 - y0 - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill=(40, 44, 52, 255))
    return Image.alpha_composite(im, lay)

# 2026-11-19 ユーザー「1 は バレる＝信号機の絵 が一般的じゃない」「2 はマウスの軌跡が答えでわかっちゃう。チェック欄と押してる人のアップに」「3 も 1 と同じ」
#   J＝1 の字（✓ と ✕ はこちらで描く）、K・K2＝2 の字（人のアップ／まるロボのアップ）、L＝3 の字（押したあとは「？」で隠す。こちらで描く）
EMPTY = ("a big flat white web checkbox card facing the camera (a clean white rounded rectangle with an EMPTY square checkbox on its left and a blank "
         "light-grey bar where a label would be, NO letters, NO check mark)")
PLANS4 = {
 "J": ("Two panels side by side separated by a thin white gap, same bright clean room. In EACH panel a laptop seen from the front, its screen filling "
       "most of the panel, showing " + EMPTY + " large in the middle of the screen. LEFT panel: a friendly young person (simple rounded 3D character) sits "
       "in front, relaxed, clicking the mouse. RIGHT panel: the robot stands on the desk in front of its laptop, pushing the mouse with its body, and "
       "leans back in shock, eye wide open; a soft red glow from the screen. Nothing else on the screens."),
 "K": ("Close-up shot. A large laptop screen fills the right 65% of the frame showing " + EMPTY + " very large; a black mouse arrow cursor hovers right "
       "on the empty checkbox. In the left foreground, a close-up of a friendly young person (simple rounded 3D character, seen from the side-front, "
       "head and shoulder) focused on the screen, their hand on a white computer mouse about to click. The robot is NOT in this image. Bright soft daylight."),
 "K2": ("Close-up shot. A large laptop screen fills the upper right 65% of the frame showing " + EMPTY + " very large; a black mouse arrow cursor hovers "
        "right on the empty checkbox. In the lower left foreground, close-up of the robot on the desk pushing a white computer mouse with its round body "
        "(no arms), its big eye looking up at the checkbox, determined. Bright soft daylight."),
 "L": ("Two panels side by side separated by a thin white gap (before / after), bright clean room, a laptop seen from the front in both, its screen "
       "filling most of the panel. LEFT panel (before): the screen shows " + EMPTY + " and the robot stands on the desk pushing the mouse with its body, "
       "determined. RIGHT panel (after): the same laptop, but its whole screen is a plain blank glowing white (nothing on it), and the robot leans back "
       "a little, looking up at the screen, eye wide open."),
}
PLANS4["J3"] = PLANS4["J"].replace("showing " + EMPTY + " large in the middle of the screen", "with a plain blank screen (nothing on it)").replace(
    "Nothing else on the screens.", "The LEFT screen is plain white, the RIGHT screen is plain soft red. Leave the upper middle of each panel calm (cards will be added).")
T.PLANS.update(PLANS4); PLANS2.update(PLANS4)
BAND.update({"J3": BAND["D"], "J": BAND["D"], "K": BAND["E"], "K2": BAND["E"], "L": BAND["F"]})
MARKS = {"J_2": [("ok", 803, 773, 120), ("ng", 1360, 650, 120)], "L_1": [("q", 1920, 624, 230)]}   # 絵の名前 → [("ok"|"ng"|"q", 中心x, 中心y, 大きさ)]（2560×1440。絵を見て決める）


def q_mark(im, c, r=260):
    """大きな「？」の札（白い丸に赤い ？）。押したあとの画面を隠す"""
    x, y = c; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.ellipse((x - r + 10, y - r + 14, x + r + 10, y + r + 14), fill=(0, 0, 0, 110))
    d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), fill=(255, 255, 255, 255)); d.ellipse((x - r, y - r, x + r, y + r), fill=(235, 40, 40, 255))
    f = T.F(int(r * 1.5)); b = f.getbbox("？"); d.text((x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2), "？", font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)

# 2026-11-19 ユーザー「124 でいきたい、ただチェックのところの文字が小さすぎて見えない」
#   チェック欄は絵の AI の小さな欄の上に、こちらで大きく描く（2 行「私はロボット／ではありません」）。✓・✕・矢印の形の指もこちらで
BIGCARDS = {   # 絵 → [(左, 上, 右, 下, 印 "ok"|"ng"|None, 矢印を描くか)]
 "J_2": [(520, 600, 1275, 880, "ok", False), (1295, 470, 1955, 800, "ng", False)],   # もとの小さな欄を覆う・人の顔とまるロボにかけない
 "J3_2": [(470, 330, 1270, 690, "ok", False), (1640, 330, 2540, 690, "ng", False)],   # 座標は 2560×1440。人の顔とまるロボ（アンテナ）にかけない
 "K_1": [(1100, 470, 2440, 1010, None, True)],
 "L_1": [(120, 420, 1200, 830, None, False)],
}


PATCH = {}   # まわりの色で消すと四角い跡が残ったので使わない。大きな欄で、もとの小さな欄を覆う   # 絵の AI の小さな欄を、近くの画面の色で消す：(左, 上, 右, 下, 色を取る点)


def patch(im, box, at):
    c = im.getpixel(at); lay = Image.new("RGBA", (W, H)); ImageDraw.Draw(lay).rounded_rectangle(box, 20, fill=c[:3] + (255,))
    return Image.alpha_composite(im, lay.filter(ImageFilter.GaussianBlur(6)))


def big_card(im, box, mark=None, cursor=False):
    x0, y0, x1, y1 = box; h = y1 - y0; w = x1 - x0
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle((x0 + 8, y0 + 14, x1 + 8, y1 + 14), int(h * 0.12), fill=(0, 0, 0, 110))
    d.rounded_rectangle((x0, y0, x1, y1), int(h * 0.12), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=CARD_EDGE)   # 黒いふち（建物の深層の吹き出しと同じ。1280 幅で 4px）
    bs = int(min(h * 0.48, w * 0.17)); pad = int(min(h * 0.2, w * 0.06)); bx, by = x0 + pad, y0 + (h - bs) // 2
    col = {"ok": (40, 170, 70), "ng": (225, 40, 40)}.get(mark)
    if col: d.rounded_rectangle((bx, by, bx + bs, by + bs), int(bs * 0.14), fill=col + (255,))
    else: d.rounded_rectangle((bx, by, bx + bs, by + bs), int(bs * 0.14), fill=(255, 255, 255, 255), outline=(90, 98, 110, 255), width=max(6, bs // 16))
    if mark == "ok": d.line([(bx + bs * 0.22, by + bs * 0.52), (bx + bs * 0.43, by + bs * 0.74), (bx + bs * 0.8, by + bs * 0.28)], fill=(255, 255, 255, 255), width=int(bs * 0.14), joint="curve")
    if mark == "ng":
        k = bs * 0.27; c = (bx + bs / 2, by + bs / 2)
        d.line([(c[0] - k, c[1] - k), (c[0] + k, c[1] + k)], fill=(255, 255, 255, 255), width=int(bs * 0.14)); d.line([(c[0] - k, c[1] + k), (c[0] + k, c[1] - k)], fill=(255, 255, 255, 255), width=int(bs * 0.14))
    tx = bx + bs + pad; best = None
    for lines in (["私はロボット", "ではありません"], ["私は", "ロボットでは", "ありません"]):   # 狭い欄は 3 行の方が字が大きくなる
        px = int(h * 0.8 / (len(lines) * 1.15)); f = T.F(px, 900)
        while max(f.getlength(l) for l in lines) > x1 - tx - pad * 0.6 and px > 20: px -= 2; f = T.F(px, 900)
        if not best or px > best[1] * 1.15: best = (lines, px, f)   # 3 行は、はっきり大きくなるときだけ
    lines, px, f = best
    lh = px * 1.15; ty = y0 + (h - lh * len(lines)) / 2
    for i, l in enumerate(lines):
        b = f.getbbox(l); d.text((tx, ty + i * lh - b[1] + (lh - (b[3] - b[1])) / 2), l, font=f, fill=(0, 0, 0, 255))
    im = Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)
    if cursor:   # 矢印の形のカーソル（黒に白いふち）を □ の右下に
        cx, cy = bx + bs * 0.62, by + bs * 0.6; u = bs * 0.62
        pts = [(0, 0), (0, 1.0), (0.26, 0.77), (0.43, 1.12), (0.58, 1.05), (0.42, 0.7), (0.75, 0.7)]
        P = [(cx + a * u, cy + b_ * u) for a, b_ in pts]; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
        d.polygon(P, fill=(255, 255, 255, 255), outline=(255, 255, 255, 255), width=int(u * 0.12)); d.polygon(P, fill=(15, 15, 18, 255))
        im = Image.alpha_composite(im, lay)
    return im



# 帯の字（2026-11-21 ユーザー「文字数と黒帯のサイズをリサーチ元からしっかり調べて」。建物の深層 16 枚を 1280 幅で数えた値）
#   帯の高さ 133px＝18.5%・字の高さ 102〜104px＝14.4%（帯の 78%。上下の余白 13〜16px）・字の幅は画面の 91〜99%・1 行 10〜17 字（多くは 12〜14 字）
#   色：白 (255,255,255)・黄 (251,254,5)・赤 (248,3,3)。ふちなし。字の濃さ（字の箱の中の字の割合）0.45〜0.54、線の太さは字の高さの 18%
#   こちらの前の版は、帯 16.9%・字の高さ 10.6〜12.9%・濃さ 0.37 で、字が小さく、字の間が空いていた
BAND_H = 0.185; BAND_GLYPH = 0.144; BAND_MAXW = 0.97; BAND_TRACK = -0.07; BAND_BOLD = 0.018; SQUEEZE_MIN = 0.80
BAND_COL = {"W": (255, 255, 255), "Y": (251, 254, 5), "R": (248, 3, 3)}


def band_text(im, runs):
    bh = round(H * BAND_H); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, bh), fill=(0, 0, 0, 255))
    want = BAND_GLYPH * H
    for _ in range(40):
        f0 = T.F(100); b = f0.getbbox("なぜロボット見抜ける？"); px = int(100 * want / (b[3] - b[1]))
        f = T.F(px); sw = max(1, round(px * BAND_BOLD))
        # 1 字ずつ詰めて、帯と同じ高さの横長の層に描く
        chars = [(ch, BAND_COL[c]) for t, c in runs for ch in t]
        widths = [f.getlength(ch) + px * BAND_TRACK for ch, _ in chars]; tw = int(sum(widths) - px * BAND_TRACK + 2 * sw + 4)
        lay = Image.new("RGBA", (tw, bh)); dl = ImageDraw.Draw(lay)
        bb = f.getbbox("な"); y = (bh - (bb[3] - bb[1])) / 2 - bb[1]; x = sw + 2
        for (ch, col), w_ in zip(chars, widths):
            dl.text((x, y), ch, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=col + (255,)); x += w_
        sq = min(1.0, BAND_MAXW * W / tw)
        if sq >= SQUEEZE_MIN: break
        want *= 0.97                                     # 横に詰めても入らないときだけ、字を小さくする
    bx = lay.getbbox(); lay = lay.crop((bx[0], 0, bx[2], bh))          # 字のある所だけで左右の真ん中にそろえる
    lay = lay.resize((max(1, int(lay.width * sq)), bh), Image.LANCZOS)
    im.alpha_composite(lay, ((W - lay.width) // 2, 0))
    print("帯の字", "".join(ch for ch, _ in chars), "字数", len(chars), "字の高さ %.1f%%" % (want / H * 100), "横の詰め %.2f" % sq)
    return im


# 絵の色と明暗（2026-11-21。建物の深層 16 枚の帯の下の平均：色の強さ 68・明暗の差 62・鮮やかさ 0.29・明るさ 169。
#   前のこちらの 3 枚は 47・50・0.16・201 で、白っぽく色が薄く、物の形が背景にとけていた）
GRADE = dict(sat=0.29, std=62.0, mean=170.0)
CARD_EDGE = 8


def grade(im):
    from PIL import ImageEnhance
    import numpy as np
    rgb = im.convert("RGB"); top = round(H * BAND_H)
    def stats(x):
        a = np.asarray(x.resize((640, 360)), float)[round(360 * BAND_H):]
        L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
        sat = np.asarray(Image.fromarray(a.astype("uint8")).convert("HSV"), float)[..., 1].mean() / 255
        return sat, L.std(), L.mean()
    sat, sd, mn = stats(rgb)
    if mn > GRADE["mean"] + 3:                           # 白っぽすぎるときだけ、明るい所を落とす（ガンマ）
        g = np.log(GRADE["mean"] / 255) / np.log(mn / 255)
        rgb = rgb.point([int(255 * (i / 255) ** g) for i in range(256)] * 3)
    sat, sd, mn = stats(rgb)
    rgb = ImageEnhance.Contrast(rgb).enhance(min(1.5, max(1.0, GRADE["std"] / max(sd, 1))))
    sat, sd, mn = stats(rgb)
    rgb = ImageEnhance.Color(rgb).enhance(min(2.0, max(0.7, GRADE["sat"] / max(sat, 0.01))))   # 最後に鮮やかさを合わせる（強すぎても下げる）
    sat, sd, mn = stats(rgb); print("絵の色 鮮やかさ %.2f 明暗の差 %.1f 明るさ %.1f" % (sat, sd, mn))
    return rgb.convert("RGBA")

def band_comp(choice):
    out = []
    RED2 = (240, 40, 40)
    for name, src in choice.items():
        k = name.split("_")[0]; im = grade(T.bg(os.path.join(T.G, src)))
        lb = BAND_LABEL.get(name, BAND_LABEL.get(src.split("_")[0]))
        if lb: im = label(im, lb)
        for bx in ([] if src.rsplit(".", 1)[0] in BIGCARDS else BARS.get(src.split("_")[0], [])): im = label_bar(im, bx)
        for pb in PATCH.get(src.rsplit(".", 1)[0], []): im = patch(im, pb[:4], pb[4])
        for bc in BIGCARDS.get(src.rsplit(".", 1)[0], []): im = big_card(im, bc[:4], bc[4], bc[5])
        for kind, mx, my, r in ([] if src.rsplit(".", 1)[0] in BIGCARDS and src.startswith("J") else MARKS.get(src.rsplit(".", 1)[0], [])):
            im = q_mark(im, (mx, my), r) if kind == "q" else T.badge(im, (mx, my), kind == "ok", r)
        im = band_text(im, BAND[k])
        for cx, cy, r in CIRCLES.get(name, CIRCLES.get(src.split("_")[0], [])):
            lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
            dl.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(255, 255, 255, 255), width=40)
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED2 + (255,), width=26)
            im = Image.alpha_composite(im, lay)
        for p0, p1 in ARROWS.get(name, []): im = T.arrow(im, p0, p1, bend=0.0, w=46, col=RED2)
        out.append(T.save(im, "ep04_" + name))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]:
            T.BASE = BRIGHT if a in PLANS2 else BASE
            T.gen(a, refs=("r1.png", "r2.png", "r3.png", "r4.png"))
    elif sys.argv[1] == "band":
        print("\n".join(band_comp(json.loads(sys.argv[2]))))
    else:
        print("\n".join(comp(json.loads(sys.argv[2]), json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})))
