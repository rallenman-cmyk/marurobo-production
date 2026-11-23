# 7本目「キーボードは、なぜ ABC 順に並んでいない？」のサムネ（2026-11-23、サムネのリサーチ.md の案 A・B・C）
#   6本目の thumbs06.py と同じ作り（references/thumbnail_rules.md の数で、帯・字・絵の色を合わせる）
#   絵は Gemini の画像の AI に「字なし」で描かせ（gen）、帯・字・印・キーの字はこちらで重ねる（band）
#   使い方: THUMB_WORK=<作業> THUMB_FONTDIR=<fonts/package> python3 thumbs07.py gen A B C ／ band '{"A":"A_1.png",...}'
#   見本のコマ：<作業>/src/r_S01b.png（キーボードとまるロボ）・r_S03a2.png（浮いた QWERTY）・r_S04b.png（2 台のキーボード）・r_S12a.png（タイプライターの中）・r_S13a.png（からまる 2 本）
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

MARU = ("The small mascot robot must match the reference images exactly: a glossy white sphere body, ONE large round camera-lens eye "
        "(navy outer ring, teal iris ring, glossy dark pupil), a thin grey antenna with a small orange ball on top, two short stubby grey legs with "
        "small white shoes. No mouth, no arms, no hands, no eyebrows.")
BRIGHT = ("Background art for a YouTube thumbnail, 16:9, bright clean soft 3D illustration like a polished explainer channel (soft warm daylight, "
          "a wooden desk, light cream wall). ABSOLUTELY NO TEXT anywhere: no letters, no numbers, no symbols on the keys (every key cap is plain blank "
          "white), no logos, no speech bubbles. Do NOT draw any black bar or band anywhere: the scene fills the whole frame edge to edge. The TOP 20% "
          "of the frame shows only plain wall (a title will be added there later), nothing important in it. Keep the bottom-right corner free of "
          "important things. ")
PLANS = {
 "A": (BRIGHT + MARU + "\n\nCamera low and close in front of a big modern white computer keyboard lying on a wooden desk, the keyboard fills the lower "
       "half of the frame (y 62-100%), keys are plain blank white rounded caps. Above the left part of the keyboard, a ROW OF SIX BIG blank white key "
       "caps floats in the air in a straight horizontal line, lifted out of the keyboard, each cap large (about 9% of frame width), occupying x 8-66% "
       "and y 30-50%, facing the camera, with soft shadows below them on the keyboard. On the right side, the small mascot robot stands on the "
       "keyboard at x 72-90%, y 30-75%, looking up at the floating keys with its head slightly tilted (curious). Nothing else."),
 "B": (BRIGHT + MARU + "\n\nWide shot of a wooden desk seen from the front, slightly above. TWO identical modern white keyboards lie side by side on "
       "dark grey mats, the left one at x 3-46%, the right one at x 54-97%, both at y 50-90%, same size, same shape, plain blank white keys. Between "
       "them, standing on the desk in the middle (x 44-56%, y 38-78%), the small mascot robot faces the camera, its body turned slightly, looking "
       "from one keyboard to the other. Bright, clean, symmetric composition. Nothing else on the desk."),
 "C": (BRIGHT.replace("a wooden desk, light cream wall", "inside an old 1870s typewriter") + "\n\nClose-up inside an old mechanical typewriter: "
       "a half-circle fan of thin silver type-bars (long slender metal arms) lying in a semicircle on a pale beige base, like the reference images. "
       "In the center, TWO NEIGHBORING type-bars have both swung UP at the same time and are JAMMED, crossed and stuck together in an X shape just "
       "below a cream paper roll at the top center; those two bars glow warm gold. The jam is LARGE and in the middle of the frame (x 35-65%, y "
       "24-80%). The rest of the bars rest in the fan. Soft warm light. No robot. No text, no letters on the bars."),
}
REFS = {"A": ("r_S03a2.png", "r_S01b.png", "r_S05a.png"), "B": ("r_S04b.png", "r_S05a.png", "r_S01b.png"), "C": ("r_S13a.png", "r_S12a.png")}
T.PLANS.update(PLANS); T.BASE = ""
BAND = {   # 案 → [(字, 色)]。物の名前は黄、おかしな所は赤（thumbnail_rules.md）。11〜14 字
 "A": [("なぜ", "W"), ("ABC順", "Y"), ("に", "W"), ("並んでない", "R"), ("？", "W")],
 "B": [("ABC順", "Y"), ("のほうが", "W"), ("打ちやすい", "R"), ("？", "W")],
 "C": [("わざと", "R"), ("打ちにくく", "Y"), ("した？", "W")],
}
MARKS = {}     # 絵の名前 → [("ok"|"ng"|"q", 中心x, 中心y, 大きさ)]（2560×1440。絵を見て決める）
CIRCLES = {"C_1": [(1220, 700, 360)]}   # 絵の名前 → [(中心x, 中心y, 半径)]（注目の赤い丸）
ARROWS = {}    # 絵の名前 → [((x0, y0), (x1, y1), 曲げ)]
RED2 = (240, 40, 40)


def q_mark(im, c, r=200):
    """大きな「？」の札（白い丸に赤い ？）。答えを隠す"""
    x, y = c; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.ellipse((x - r + 10, y - r + 14, x + r + 10, y + r + 14), fill=(0, 0, 0, 110))
    d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), fill=(255, 255, 255, 255)); d.ellipse((x - r, y - r, x + r, y + r), fill=RED2 + (255,))
    f = T.F(int(r * 1.5)); b = f.getbbox("？"); d.text((x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2), "？", font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)


FIT = {}
SHIFT = {"C_1": 0.16}   # C：2 本が交わる所（絵の上の端）が帯に隠れるので、絵を下へずらす（縮めると左右の端をのばした所が筋に見えた）   # 絵の名前 → 中身の上の端（高さの割合）。帯（17%）の下に入るよう縮め、左右は元の絵の端をのばす


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
GRADE = dict(sat=0.32, std=66.0, mean=173.0)   # 7本目：3D の絵は 0.28・62 で入れると 0.26・56 にとどまった（強めに当てる）   # 決まりの幅（鮮やかさ 0.27〜0.31・明るさ 165〜180）のまん中に入るよう、少しずらした


def band_text(im, runs):
    bh = round(H * BAND_H); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, bh), fill=(0, 0, 0, 255))
    want = BAND_GLYPH * H
    for _ in range(40):
        f0 = T.F(100); b = f0.getbbox("なぜロボット見抜ける？"); px = int(100 * want / (b[3] - b[1]))
        f = T.F(px); sw = max(1, round(px * BAND_BOLD))
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
    rgb = ImageEnhance.Contrast(rgb).enhance(min(1.5, max(1.0, GRADE["std"] / max(sd, 1))))
    sat, sd, mn = stats(rgb)
    if abs(mn - GRADE["mean"]) > 3:   # 6本目：明暗の差を上げると暗くなる絵があった（151）→ 明るさを 170 へ戻す（明るくもする）
        g = np.log(GRADE["mean"] / 255) / np.log(mn / 255)
        rgb = rgb.point([int(255 * (i / 255) ** g) for i in range(256)] * 3)
    sat, sd, mn = stats(rgb)
    rgb = ImageEnhance.Color(rgb).enhance(min(2.4, max(0.7, GRADE["sat"] / max(sat, 0.01))))
    sat, sd, mn = stats(rgb); print("絵の色 鮮やかさ %.2f 明暗の差 %.1f 明るさ %.1f" % (sat, sd, mn))
    return rgb.convert("RGBA")


# 2026-11-23：絵の AI が使えない（前払いの残りなし・402）ので、絵は本編の 3D を Blender で描いた静止画（2560×1440 か 3840×2160）を使う。
#   CROPS：絵の名前 → 切り抜く箱（元の絵の画素）。RECTS：赤い角丸の枠。LABELS：白い札（黒いふち）に色の字
CROPS = {"B_1": (90, 84, 3780, 2160)}   # B は 3840×2160 で描き、2 台のキーボードが大きく入るよう少し寄る
RECTS = {"A_1": [(190, 300, 1700, 590)]}      # 絵の名前 → [(x0, y0, x1, y1)]（2560×1440）
LABELS = {"B_1": [("クワーティ", 600, 930, 150, (30, 110, 240)), ("ABC順", 1940, 930, 150, (240, 120, 20))]}     # 絵の名前 → [(字, 中心x, 中心y, 字の高さ, 字の色)]


def label(im, text, c, px, col):
    f = T.F(px); b = f.getbbox(text); tw, th = b[2] - b[0], b[3] - b[1]; padx, pady = int(px * 0.45), int(px * 0.32)
    x0, y0 = c[0] - tw / 2 - padx, c[1] - th / 2 - pady; x1, y1 = c[0] + tw / 2 + padx, c[1] + th / 2 + pady
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle((x0 + 8, y0 + 14, x1 + 8, y1 + 14), int((y1 - y0) / 2), fill=(0, 0, 0, 110))
    d.rounded_rectangle((x0, y0, x1, y1), int((y1 - y0) / 2), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=8)
    d.text((c[0] - tw / 2 - b[0], c[1] - th / 2 - b[1]), text, font=f, fill=col + (255,))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)


def red_rect(im, box):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0 - 8, y0 - 8, x1 + 8, y1 + 8), 40, outline=(255, 255, 255, 255), width=40)
    d.rounded_rectangle((x0, y0, x1, y1), 32, outline=RED2 + (255,), width=26)
    return Image.alpha_composite(im, lay)


def band(choice):
    out = []
    for name, src in choice.items():
        k = name.split("_")[0]; key = src.rsplit(".", 1)[0]
        im0 = Image.open(os.path.join(T.G, src)).convert("RGB")
        if key in CROPS: im0 = im0.crop(CROPS[key])
        im = im0.resize((W, H), Image.LANCZOS).convert("RGBA")
        if key in FIT: im = fit_below(im, FIT[key])
        if key in SHIFT:
            dy = round(H * SHIFT[key]); sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 255)); sh_.paste(im.crop((0, 0, W, H - dy)), (0, dy)); im = sh_
        im = grade(im)
        for p0, p1, bend in ARROWS.get(key, []): im = T.arrow(im, p0, p1, bend=bend, w=46, col=RED2)
        for kind, mx, my, r in MARKS.get(key, []):
            im = q_mark(im, (mx, my), r) if kind == "q" else T.badge(im, (mx, my), kind == "ok", r)
        for cx, cy, r in CIRCLES.get(key, []):
            lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
            dl.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(255, 255, 255, 255), width=40)
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED2 + (255,), width=26)
            im = Image.alpha_composite(im, lay)
        for box in RECTS.get(key, []): im = red_rect(im, box)
        for t_, x_, y_, px_, c_ in LABELS.get(key, []): im = label(im, t_, (x_, y_), px_, c_)
        im = band_text(im, BAND[k])
        out.append(T.save(im, "ep07_" + name))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]:
            T.gen(a, refs=REFS[a])
    elif sys.argv[1] == "band":
        print("\n".join(band(json.loads(sys.argv[2]))))
