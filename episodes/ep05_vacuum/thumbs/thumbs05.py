# 5本目「ロボット掃除機は、どうやって部屋の形を覚える？」のサムネ（2026-11-21。6本目 thumbs06.py と同じ作り。references/thumbnail_rules.md の決まり）
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

SENPAI = ("The robot vacuum must match the reference images exactly: a round flat white robot vacuum cleaner (about 34 cm wide, 9 cm tall), "
          "glossy white top, dark grey bumper band around the front half, and on top a small round DARK lidar turret (a short black cylinder with a "
          "thin glass ring) slightly toward the front. No face, no eyes on the vacuum.")
MARU = ("The small mascot robot must match the reference images exactly: a glossy white sphere body about 25 cm, ONE large round camera-lens eye "
        "(navy outer ring, teal iris ring, glossy dark pupil), a thin grey antenna with a small orange ball on top, two short stubby dark grey legs "
        "with teal-soled boxy shoes. No mouth, no arms, no hands.")
BRIGHT = ("Background art for a YouTube thumbnail, 16:9, bright clean soft 3D illustration like a polished explainer channel (soft daylight, warm "
          "living-room colors: light wooden floor, pale green wainscot walls, a teal sofa, a colorful bookshelf). ABSOLUTELY NO TEXT: no letters, "
          "no numbers, no logos, no speech bubbles, no signs, no screens with text. Do NOT draw any black bar or band anywhere: the scene fills the "
          "whole frame edge to edge. The TOP 20% of the frame shows only plain wall (a title will be added there later), nothing important in it. "
          "Keep the bottom-right corner free of important things. ")
PLANS = {
 "A": (BRIGHT + SENPAI + " " + MARU + "\n\nCamera low near the floor in a living room. The robot vacuum sits in the middle of the floor, LARGE and close "
       "to the camera, facing the camera (x 30-75%, y 50-95%). From its lidar turret, six thin bright TEAL laser beams shoot out horizontally in a fan "
       "across the room and hit the wall, the sofa legs and the bookshelf, each hit point glowing as a small teal dot; a row of small glowing teal "
       "dots runs along the bottom of the walls like a dotted outline of the room. The small mascot robot stands on the floor to the left of the vacuum "
       "(x 6-30%, y 40-90%), its whole body visible, its big eye looking at the laser beams in wonder (head tilted up)."),
 "B": (BRIGHT + SENPAI + "\n\nTwo panels side by side separated by a thin white gap. LEFT panel: an empty unfamiliar bright living room seen from "
       "above at an angle, the robot vacuum alone in the middle of the floor, small. RIGHT panel: a black smartphone lying flat on a wooden table, seen from "
       "above, its screen showing a simple clean floor-plan map of the same room drawn in light blue and white blocks (walls, sofa, bed shapes) with a "
       "small glowing dot for the vacuum; the phone screen has NO text and NO icons. Big, simple, readable at small size."),
 "C": (BRIGHT + SENPAI + "\n\nTwo panels side by side separated by a thin white gap, the SAME living room seen from straight above (top-down floor "
       "plan view, walls, sofa, bookshelf, bed) in both panels. LEFT panel: an OLD simple robot vacuum (plain white disc, no turret) and behind it a "
       "messy tangled bright YELLOW path line bouncing randomly all over the room, crossing itself many times, and one corner of the room the path never "
       "reaches. RIGHT panel: the modern robot vacuum with the dark lidar turret, and behind it a neat orderly back-and-forth (zigzag lawn-mower) bright "
       "TEAL path line that covers the whole room evenly. Big, simple, readable at small size."),
}
REFS = {"A": ("r_senpai_lid.png", "r_maru_greet.png", "r_lidar_beam.png"), "B": ("r_senpai_lid.png", "r_room.png", "r_lidar_beam.png"),
        "C": ("r_senpai_lid.png", "r_map_dots.png", "r_room.png")}
T.PLANS.update(PLANS); T.BASE = ""
BAND = {   # 案 → [(字, 色)]。物の名前は黄、おかしな所・結果は赤。14 字までが目安
 "A": [("掃除機", "Y"), ("はなぜ", "W"), ("部屋の形", "R"), ("が分かる？", "W")],
 "B": [("初めての部屋", "W"), ("の", "W"), ("地図", "Y"), ("、", "W"), ("どう描く", "R"), ("？", "W")],
 "C": [("今の", "W"), ("掃除機", "Y"), ("はなぜ", "W"), ("迷わない", "R"), ("？", "W")],
}
MARKS = {"C_2": [("ng", 330, 470, 120), ("ok", 1610, 470, 120)]}     # 絵の名前 → [("ok"|"ng"|"q", 中心x, 中心y, 大きさ)]（2560×1440。絵を見て決める）
CIRCLES = {}   # 絵の名前 → [(中心x, 中心y, 半径)]（注目の赤い丸）
ARROWS = {"B_2": [((1020, 1000), (1580, 1000), 0.0)]}    # 絵の名前 → [((x0, y0), (x1, y1), 曲げ)]
RED2 = (240, 40, 40)


def q_mark(im, c, r=200):
    """大きな「？」の札（白い丸に赤い ？）。答えを隠す"""
    x, y = c; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.ellipse((x - r + 10, y - r + 14, x + r + 10, y + r + 14), fill=(0, 0, 0, 110))
    d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), fill=(255, 255, 255, 255)); d.ellipse((x - r, y - r, x + r, y + r), fill=RED2 + (255,))
    f = T.F(int(r * 1.5)); b = f.getbbox("？"); d.text((x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2), "？", font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)


FIT = {}   # 絵の名前 → 中身の上の端（高さの割合）。帯（17%）の下に入るよう縮め、左右は元の絵の端をのばす


def fit_below(im, top, band_h=0.195):
    k = (1 - band_h) / (1 - top); w2, h2 = int(W * k), int(H * k)
    sm = im.resize((w2, h2), Image.LANCZOS); out = Image.new("RGBA", (W, H))
    side = (W - w2) // 2
    out.paste(sm.crop((0, 0, 1, h2)).resize((side + 1, h2)), (0, H - h2)); out.paste(sm.crop((w2 - 1, 0, w2, h2)).resize((W - side - w2 + 1, h2)), (side + w2, H - h2))
    out.paste(sm, (side, H - h2)); return out


# 帯の字と絵の色（2026-11-21 ユーザー「サムネのルール追加したから 3 つのやつ作り直して」。references/thumbnail_rules.md の「数で決めた値」：
#   建物の深層 16 枚を数えた値。帯の高さ 18.5%・字の高さ 14.4%・字の幅は画面の 92〜97%・字を詰める・色は白黄赤の決まった値・絵の色と明暗を合わせる）
#   4本目の thumbs04.py の band_text・grade と同じ作り（字の形は太さごとのファイルを使う）
BAND_H = 0.185; BAND_GLYPH = 0.144; BAND_MAXW = 0.97; BAND_TRACK = -0.07; BAND_BOLD = 0.010; SQUEEZE_MIN = 0.80   # 太さ：決まりの 0.018 では「膳・転・続」の字がつぶれ、字の濃さが 0.59 で幅（0.45〜0.54）の外。0.010 で 0.47〜0.54
BAND_COL = {"W": (255, 255, 255), "Y": (251, 254, 5), "R": (248, 3, 3)}
GRADE = dict(sat=0.28, std=63.0, mean=172.0)   # 決まりの幅（鮮やかさ 0.27〜0.31・明るさ 165〜180）のまん中に入るよう、少しずらした


BOLD_OF = {"A": 0.004}      # 5本目 A：「掃除機・部屋」の画数の多い字で、0.010 だと字の濃さ 0.57（幅 0.45〜0.54 の外）


def band_text(im, runs, bold=None):
    bh = round(H * BAND_H); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, bh), fill=(0, 0, 0, 255))
    want = BAND_GLYPH * H
    for _ in range(40):
        f0 = T.F(100); b = f0.getbbox("なぜロボット見抜ける？"); px = int(100 * want / (b[3] - b[1]))
        f = T.F(px); sw = max(1, round(px * (bold if bold is not None else BAND_BOLD)))
        chars = [(ch, BAND_COL[c]) for t, c in runs for ch in t]
        widths = [f.getlength(ch) + px * BAND_TRACK for ch, _ in chars]; tw = int(sum(widths) - px * BAND_TRACK + 2 * sw + 4)
        lay = Image.new("RGBA", (tw, bh)); dl = ImageDraw.Draw(lay)
        bb = f.getbbox("な"); y = (bh - (bb[3] - bb[1])) / 2 - bb[1]; x = sw + 2
        for (ch, col), w_ in zip(chars, widths):
            dl.text((x, y), ch, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=col + (255,)); x += w_
        sq = min(1.0, BAND_MAXW * W / tw)
        if sq >= SQUEEZE_MIN: break
        want *= 0.97
    bx = lay.getbbox(); lay = lay.crop((bx[0], 0, bx[2], bh))
    lay = lay.resize((max(1, int(lay.width * sq)), bh), Image.LANCZOS)
    im.alpha_composite(lay, ((W - lay.width) // 2, 0))
    print("帯の字", "".join(ch for ch, _ in chars), "字数", len(chars), "字の高さ %.1f%%" % (want / H * 100), "横の詰め %.2f" % sq)
    return im


def grade(im):
    from PIL import ImageEnhance
    import numpy as np
    rgb = im.convert("RGB")
    def stats(x):
        a = np.asarray(x.resize((640, 360)), float)[round(360 * BAND_H):]
        L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
        sat = np.asarray(Image.fromarray(a.astype("uint8")).convert("HSV"), float)[..., 1].mean() / 255
        return sat, L.std(), L.mean()
    sat, sd, mn = stats(rgb)
    if mn > GRADE["mean"] + 3:
        g = np.log(GRADE["mean"] / 255) / np.log(mn / 255)
        rgb = rgb.point([int(255 * (i / 255) ** g) for i in range(256)] * 3)
    sat, sd, mn = stats(rgb)
    rgb = ImageEnhance.Contrast(rgb).enhance(min(1.9, max(1.0, GRADE["std"] / max(sd, 1))))      # 5本目：真上からの絵（C）は明暗の差 40 で、1.5 倍まででは足りなかった
    sat, sd, mn = stats(rgb)
    if abs(mn - GRADE["mean"]) > 3:   # 6本目：明暗の差を上げると暗くなる絵があった（151）→ 明るさを 170 へ戻す（明るくもする）
        g = np.log(GRADE["mean"] / 255) / np.log(mn / 255)
        rgb = rgb.point([int(255 * (i / 255) ** g) for i in range(256)] * 3)
    sat, sd, mn = stats(rgb)
    rgb = ImageEnhance.Color(rgb).enhance(min(2.0, max(0.5, GRADE["sat"] / max(sat, 0.01))))      # 5本目：B は鮮やかさ 0.40 で、0.7 倍まででは下がりきらなかった
    sat, sd, mn = stats(rgb); print("絵の色 鮮やかさ %.2f 明暗の差 %.1f 明るさ %.1f" % (sat, sd, mn))
    return rgb.convert("RGBA")


def band(choice):
    out = []
    for name, src in choice.items():
        k = name.split("_")[0]; key = src.rsplit(".", 1)[0]; im = T.bg(os.path.join(T.G, src))
        if key in FIT: im = fit_below(im, FIT[key])
        im = grade(im)
        for _ in range(4):        # 5本目：1 回では明暗の差・鮮やかさが幅（58〜72・0.27〜0.31）に入らない絵があった → 入るまでくり返す
            import numpy as _np
            a_ = _np.asarray(im.convert("RGB").resize((640, 360)), float)[round(360 * BAND_H):]
            L_ = 0.299 * a_[..., 0] + 0.587 * a_[..., 1] + 0.114 * a_[..., 2]
            s_ = _np.asarray(Image.fromarray(a_.astype("uint8")).convert("HSV"), float)[..., 1].mean() / 255
            if 59 <= L_.std() <= 71 and 0.27 <= s_ <= 0.30 and 166 <= L_.mean() <= 179: break
            im = grade(im)
        for p0, p1, bend in ARROWS.get(key, []): im = T.arrow(im, p0, p1, bend=bend, w=70, col=RED2)
        for kind, mx, my, r in MARKS.get(key, []):
            im = q_mark(im, (mx, my), r) if kind == "q" else T.badge(im, (mx, my), kind == "ok", r)
        for cx, cy, r in CIRCLES.get(key, []):
            lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
            dl.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(255, 255, 255, 255), width=40)
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED2 + (255,), width=26)
            im = Image.alpha_composite(im, lay)
        im = band_text(im, BAND[k], BOLD_OF.get(k))
        out.append(T.save(im, "ep05_" + name))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]:
            T.gen(a, refs=REFS[a])
    elif sys.argv[1] == "band":
        print("\n".join(band(json.loads(sys.argv[2]))))
