# 6本目「ファミレスの配膳ロボットは、なぜお客さんにぶつからない？」のサムネ（2026-11-20、サムネのリサーチ.md の案 A・B・C）
#   型は SKILL.md §9「サムネの構図の決まり」：上に黒い帯（高さの 17%）と 1 行の問い、物の名前は黄色・大事な所は赤。答えは見せない
#   絵は Gemini の画像の AI（gemini-3-pro-image）に「字なし」で描かせ（gen）、帯・字・印はこちらで重ねる（band）
#   2026-11-20 ユーザー「全部作って、b で撫でるのは人の手にして無理やりまるロボ出さなくていい」
#   使い方: THUMB_WORK=<作業> THUMB_FONTDIR=<fonts/package> python3 thumbs06.py gen A B C ／ band '{"A":"A_1.png",...}'
#   見本のコマ：<作業>/src/r_S05b.png（先輩の全身）・r_S28a.png（先輩の顔とまるロボ）・r_S18a.png（床に寝ころぶまるロボ）・r_S01a.png（お店の通路）・r_S27a.png（耳をなでる子ども）
import os, sys, json, importlib.util
H_ = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("tv3", os.path.join(H_, "..", "..", "ep02_qr", "thumbs", "thumbs_v3.py"))
T = importlib.util.module_from_spec(_sp); _a = sys.argv; sys.argv = [sys.argv[0], "x"]; _sp.loader.exec_module(T); sys.argv = _a
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = T.W, T.H
FD = os.environ.get("THUMB_FONTDIR", "")
_WN = {900: "900Black", 800: "800ExtraBold", 700: "700Bold", 600: "600SemiBold", 500: "500Medium"}


def F(px, wght=900):   # 太さごとの字の形のファイル（変えられる太さの 1 ファイルが無いとき）
    n = _WN.get(wght, "900Black"); return ImageFont.truetype(os.path.join(FD, n, "NotoSansJP_%s.ttf" % n), px)


if FD: T.F = F

SENPAI = ("The serving robot must match the reference images exactly: a tall slim white robot (about 1.2 m), on top a white boxy head with a BLACK "
          "rectangular face screen showing a simple cute face drawn with thin glowing white lines (two eyes and a small smile), two small round "
          "bear-like ears with pale pink insides on top of the head, under the head several round white tray shelves stacked on a slim column, and a "
          "round white base near the floor with two small dark round cameras on its front and a thin dark window band near the floor. Not a cat robot.")
MARU = ("The small mascot robot must match the reference images exactly: a glossy white sphere body about 30 cm, ONE large round camera-lens eye "
        "(navy outer ring, teal iris ring, glossy dark pupil), a thin grey antenna with a small orange ball on top, two short stubby grey legs. "
        "No mouth, no arms, no hands.")
BRIGHT = ("Background art for a YouTube thumbnail, 16:9, bright clean soft 3D illustration like a polished explainer channel (soft daylight, warm "
          "family-restaurant colors: wooden tables, orange-red chairs, cream walls, light floor), simple rounded cartoon people with smooth faces "
          "and no facial features. ABSOLUTELY NO TEXT: no letters, no numbers, no logos, no speech bubbles, no signs. Do NOT draw any black bar or "
          "band anywhere: the scene fills the whole frame edge to edge. The TOP 20% of the frame shows only plain wall and ceiling (a title will be "
          "added there later), nothing important in it. Keep the bottom-right corner free of important things. ")
PLANS = {
 "A": (BRIGHT + SENPAI + " " + MARU + "\n\nCamera at knee height in a family-restaurant aisle between tables. The serving robot comes straight toward "
       "the camera down the middle of the aisle, LARGE, facing the camera, its whole body visible from its ears down to the floor, occupying x 50-78% and "
       "y 22-98% of the frame (its head and ears must be BELOW the top 22% of the frame), a bowl of ramen on its middle tray. In its path on the floor "
       "close to the camera, the small mascot robot is LYING ON ITS SIDE on the floor: the sphere body tipped over 90 degrees, its two stubby legs "
       "sticking out sideways, its antenna lying flat along the floor, its big eye (navy ring, TEAL iris ring, dark pupil) facing the camera; at "
       "x 6-50%, y 48-100% (BIG: about half of the frame height, very close to the camera). Clear empty floor between them. A few seated customers at the side tables, out of focus."),
 "B": (BRIGHT + SENPAI + "\n\nClose-up. The serving robot's head fills the right 62% of the frame (x 35-97%, y 18-100%), facing the camera straight "
       "on: the black face screen with the simple happy face of thin glowing white lines (two closed happy arc eyes and a small smile), and the two "
       "round bear ears on top. From the left edge, a child's hand and forearm (simple smooth rounded cartoon arm, skin color, short sleeve) reaches in "
       "and gently strokes the robot's RIGHT-side ear (the ear on the left of the image) with its palm. Only the hand and arm, no other person "
       "visible. The robot is NOT a cat and has NO arms. No small round mascot robot in this image."),
 "C": (BRIGHT + SENPAI + "\n\nTwo panels side by side separated by a thin white gap, the same narrow family-restaurant aisle in both, seen from the "
       "side at table height. LEFT panel: a human waiter (simple rounded cartoon person in a dark uniform) carrying a tray with a bowl of soup, "
       "bumping into a customer (simple rounded cartoon person) who suddenly stepped into the aisle; the soup splashes out of the bowl. RIGHT panel: "
       "the serving robot, carrying the same bowl of soup on its tray, has stopped smoothly just in front of the same customer stepping into the aisle, "
       "a small gap between them, the soup calm. Big, simple, readable at small size."),
}
REFS = {"A": ("r_S05b.png", "r_S18a.png", "r_S01a.png"), "B": ("r_S28a.png", "r_S27a.png", "r_S05b.png"), "C": ("r_S05b.png", "r_S01a.png", "r_S21a.png")}
T.PLANS.update(PLANS); T.BASE = ""
BAND = {   # 案 → [(字, 色)]
 # 2026-11-20 ユーザー「上の帯の文字って参考のチャンネルのやつもこんな多いかな？」→ 建物の深層の最近 16 本は 11〜13 字（いちばん長くて 16 字）。
 #   前の 19・17・16 字から、12〜14 字へ短くした（絵で分かることは字にしない：B の「配膳ロボの耳」は絵で見える）
 "A": [("配膳ロボ", "Y"), ("の目の前で", "W"), ("転がると", "R"), ("？", "W")],   # 2026-11-20 ユーザー「a は配膳ロボの目の前で転がるとの文字にして」
 "B": [("耳を", "W"), ("なで続ける", "R"), ("と", "W"), ("どうなる？", "W")],
 "C": [("なぜ", "W"), ("配膳ロボ", "Y"), ("は", "W"), ("ぶつからない", "R"), ("？", "W")],
}
MARKS = {"A_6": [("q", 1960, 430, 150)], "A_9": [("q", 1660, 400, 150)], "C_4": [("ng", 1100, 440, 115), ("ok", 1650, 470, 105)]}     # 絵の名前 → [("ok"|"ng"|"q", 中心x, 中心y, 大きさ)]（2560×1440。絵を見て決める）
CIRCLES = {"A_6": [(905, 1170, 250)], "A_9": [(945, 1135, 320)]}   # 絵の名前 → [(中心x, 中心y, 半径)]（注目の赤い丸）
ARROWS = {}    # 絵の名前 → [((x0, y0), (x1, y1), 曲げ)]
RED2 = (240, 40, 40)


def q_mark(im, c, r=200):
    """大きな「？」の札（白い丸に赤い ？）。答えを隠す"""
    x, y = c; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.ellipse((x - r + 10, y - r + 14, x + r + 10, y + r + 14), fill=(0, 0, 0, 110))
    d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), fill=(255, 255, 255, 255)); d.ellipse((x - r, y - r, x + r, y + r), fill=RED2 + (255,))
    f = T.F(int(r * 1.5)); b = f.getbbox("？"); d.text((x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2), "？", font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)


FIT = {"A_6": 0.07, "A_9": 0.075}   # 絵の名前 → 中身の上の端（高さの割合）。帯（17%）の下に入るよう縮め、左右は元の絵の端をのばす


def fit_below(im, top, band_h=0.18):
    k = (1 - band_h) / (1 - top); w2, h2 = int(W * k), int(H * k)
    sm = im.resize((w2, h2), Image.LANCZOS); out = Image.new("RGBA", (W, H))
    side = (W - w2) // 2
    out.paste(sm.crop((0, 0, 1, h2)).resize((side + 1, h2)), (0, H - h2)); out.paste(sm.crop((w2 - 1, 0, w2, h2)).resize((W - side - w2 + 1, h2)), (side + w2, H - h2))
    out.paste(sm, (side, H - h2)); return out


def band(choice):
    out = []
    for name, src in choice.items():
        k = name.split("_")[0]; key = src.rsplit(".", 1)[0]; im = T.bg(os.path.join(T.G, src))
        if key in FIT: im = fit_below(im, FIT[key])
        for p0, p1, bend in ARROWS.get(key, []): im = T.arrow(im, p0, p1, bend=bend, w=46, col=RED2)
        for kind, mx, my, r in MARKS.get(key, []):
            im = q_mark(im, (mx, my), r) if kind == "q" else T.badge(im, (mx, my), kind == "ok", r)
        for cx, cy, r in CIRCLES.get(key, []):
            lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
            dl.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(255, 255, 255, 255), width=40)
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED2 + (255,), width=26)
            im = Image.alpha_composite(im, lay)
        bh = int(H * 0.17); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, bh), fill=(8, 8, 10, 255))
        runs = [(t, {"W": T.WHITE, "Y": T.YEL, "R": RED2}[c]) for t, c in BAND[k]]
        px = T.fit(runs, W - 120, 220, track=-0.03)
        f = T.F(px); tw = sum(f.getlength(ch) + px * -0.03 for t, _ in runs for ch in t)
        b = f.getbbox("な"); y = (bh - (b[3] - b[1])) // 2 - b[1]
        im, _ = T.line(im, ((W - tw) / 2, y), runs, px, (8, 8, 10), ew=0, track=-0.03, shadow=False)
        out.append(T.save(im, "ep06_" + name))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]:
            T.gen(a, refs=REFS[a])
    elif sys.argv[1] == "band":
        print("\n".join(band(json.loads(sys.argv[2]))))
