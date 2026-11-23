# 3本目「スマホは会話を聞いている？（テント広告事件）」のサムネ（2026-11-23。6本目の thumbs06.py を写した。references/thumbnail_rules.md で作る）
#   型は SKILL.md §9「サムネの構図の決まり」：上に黒い帯（高さの 17%）と 1 行の問い、物の名前は黄色・大事な所は赤。答えは見せない
#   絵は Gemini の画像の AI（gemini-3-pro-image）に「字なし」で描かせ（gen）、帯・字・印はこちらで重ねる（band）
#   2026-11-23 ユーザー「サムネも進めて」。調べ：サムネのリサーチ.md の「2026-11-23 の調べ直し」
#   使い方: THUMB_WORK=<作業> THUMB_FONTDIR=<fonts/package> python3 thumbs03b.py gen A B C ／ band '{"A":"A_1.png",...}'
#   見本のコマ：<作業>/src/r_maru.png（部屋の探偵まるロボ）・r_train.png（電車の二人とまるロボ）・r_train2.png（座席のまるロボの寄り）・r_phone_ad.png／r_phone_night.png（テントの広告のスマホ）
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

MARU = ("The small mascot robot must match the reference images exactly: a glossy white sphere body about 30 cm, ONE large round camera-lens eye "
        "(navy outer ring, teal iris ring, glossy dark pupil), a thin grey antenna with a small orange ball on top, two short stubby grey legs with grey shoes, "
        "and a small brown checkered detective cap (deerstalker style) on top of its head. No mouth, no arms, no hands, no eyebrows.")
PEOPLE = ("Two simple rounded cartoon adults like the reference images, smooth faces with no facial features: HARU with short blond hair, a blue hoodie "
          "and grey-blue trousers; SORA with short light-brown hair, a peach hoodie and a teal scarf.")
PHONE = ("A modern black smartphone whose screen shows a simple flat advertisement picture: a large orange triangle tent on green grass under a pale blue "
         "sky with a small yellow sun, and a pale teal rounded button below it. No letters on the screen.")
BRIGHT = ("Background art for a YouTube thumbnail, 16:9, bright clean soft 3D illustration like a polished explainer channel (soft daylight, light "
          "pastel colors), simple rounded cartoon people with smooth faces and no facial features. ABSOLUTELY NO TEXT: no letters, no numbers, no logos, "
          "no signs. Do NOT draw any black bar or band anywhere: the scene fills the whole frame edge to edge. The TOP 20% of the frame shows only plain "
          "background (a title will be added there later), nothing important in it. Keep the bottom-right corner free of important things. ")
PLANS = {
 "A": (BRIGHT + PEOPLE + " " + PHONE + "\n\nLeft-to-right 'before -> after' picture. LEFT half (x 2-46%, y 22-100%): inside a bright commuter train "
       "with autumn trees seen through the windows, HARU and SORA sit side by side on a blue bench seat, turned toward each other, chatting happily. Above "
       "them a LARGE plain white rounded speech bubble (x 8-40%, y 24-52%) with a thick black outline, containing ONLY a simple orange tent drawing "
       "(no text). The MIDDLE (x 46-56%) is empty background (a big red arrow will be added later). RIGHT (x 56-96%, y 22-100%): a hand holds the "
       "smartphone upright facing the camera, LARGE (about 70% of the frame height), its screen showing the tent advertisement. Clean and simple."),
 "B": (BRIGHT + MARU + " " + PHONE.replace("whose screen shows a simple flat advertisement picture: a large orange triangle tent on green grass under a pale blue sky with a small yellow sun, and a pale teal rounded button below it", "standing upright with its screen dark") + "\n\nClose-up on a light "
       "wooden table. The smartphone stands upright, very LARGE, on the right (x 48-88%, y 20-100%), seen slightly from below so its BOTTOM EDGE with "
       "the small row of microphone holes is clearly visible and facing the camera. From the left, soft pale-blue curved sound-wave lines float "
       "toward the microphone holes. The mascot robot peeks at the microphone holes from the left foreground, LARGE (x 6-46%, y 34-100%), its big "
       "lens eye wide open and leaning forward curiously, close to the bottom edge of the phone. Only these two things."),
 "C": (BRIGHT + MARU + " " + PHONE + "\n\nThe mascot robot detective, VERY LARGE in the center-left (x 10-58%, y 22-100%), facing the camera "
       "straight on, its big lens eye looking at the viewer with a serious, curious look (the lens iris glowing slightly), the detective cap on its "
       "head. Behind it on the right (x 60-92%, y 26-90%), the smartphone floats slightly tilted, showing the tent advertisement, a little out of focus "
       "but clearly recognizable. Soft warm room background (Japanese room, cream walls) very blurred."),
}
REFS = {"A": ("r_train.png", "r_phone_ad.png", "r_train2.png"), "B": ("r_maru.png", "r_train2.png", "r_phone_night.png"), "C": ("r_maru.png", "r_train2.png", "r_phone_ad.png")}
T.PLANS.update(PLANS); T.BASE = ""
BAND = {   # 案 → [(字, 色)]。11〜14 字（thumbnail_rules.md）。物の名前は黄、おかしな所は赤
 "A": [("話しただけで", "R"), ("なぜ", "W"), ("広告", "Y"), ("に？", "W")],          # 12 字
 "B": [("スマホ", "Y"), ("は", "W"), ("会話", "W"), ("を", "W"), ("聞いてる", "R"), ("？", "W")],   # 12 字
 "C": [("テント広告", "Y"), ("事件", "W"), ("の", "W"), ("犯人", "R"), ("は", "W"), ("誰", "R"), ("？", "W")],     # 13 字（11 字では帯の字の幅が 83% で、決まりの 92〜97% に足りなかった）
}
MARKS = {}     # 絵の名前 → [("ok"|"ng"|"q", 中心x, 中心y, 大きさ)]（2560×1440。絵を見て決める）
CIRCLES = {}   # 絵の名前 → [(中心x, 中心y, 半径)]（注目の赤い丸）
ARROWS = {}    # 絵の名前 → [((x0, y0), (x1, y1), 曲げ)]
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
GRADE = dict(sat=0.31, std=62.0, mean=173.0)   # 3本目：0.28 では数えると 0.25 になった（白・灰の物が多い）   # 決まりの幅（鮮やかさ 0.27〜0.31・明るさ 165〜180）のまん中に入るよう、少しずらした


def band_text(im, runs):
    bh = round(H * BAND_H); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, bh), fill=(0, 0, 0, 255))
    want = BAND_GLYPH * H
    trk = BAND_TRACK
    for _ in range(40):
        f0 = T.F(100); b = f0.getbbox("なぜロボット見抜ける？"); px = int(100 * want / (b[3] - b[1]))
        f = T.F(px); sw = max(1, round(px * BAND_BOLD))
        chars = [(ch, BAND_COL[c]) for t, c in runs for ch in t]
        widths = [f.getlength(ch) + px * trk for ch, _ in chars]; tw = int(sum(widths) - px * trk + 2 * sw + 4)
        lay = Image.new("RGBA", (tw, bh)); dl = ImageDraw.Draw(lay)
        bb = f.getbbox("な"); y = (bh - (bb[3] - bb[1])) / 2 - bb[1]; x = sw + 2
        for (ch, col), w_ in zip(chars, widths):
            dl.text((x, y), ch, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=col + (255,)); x += w_
        sq = min(1.0, BAND_MAXW * W / tw)
        if tw < 0.955 * W and trk < 0:   # 3本目：12 字だと字の幅が 91%（決まり 92〜97%）。字の間の詰めをゆるめて幅を足す
            trk = min(0.0, trk + 0.01); continue
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
    rgb = ImageEnhance.Color(rgb).enhance(min(2.0, max(0.7, GRADE["sat"] / max(sat, 0.01))))
    sat, sd, mn = stats(rgb); print("絵の色 鮮やかさ %.2f 明暗の差 %.1f 明るさ %.1f" % (sat, sd, mn))
    return rgb.convert("RGBA")


def band(choice):
    out = []
    for name, src in choice.items():
        k = name.split("_")[0]; key = src.rsplit(".", 1)[0]; im = T.bg(os.path.join(T.G, src))
        if key in FIT: im = fit_below(im, FIT[key])
        im = grade(im)
        for p0, p1, bend in ARROWS.get(key, []): im = T.arrow(im, p0, p1, bend=bend, w=46, col=RED2)
        for kind, mx, my, r in MARKS.get(key, []):
            im = q_mark(im, (mx, my), r) if kind == "q" else T.badge(im, (mx, my), kind == "ok", r)
        for cx, cy, r in CIRCLES.get(key, []):
            lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
            dl.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(255, 255, 255, 255), width=40)
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED2 + (255,), width=26)
            im = Image.alpha_composite(im, lay)
        im = band_text(im, BAND[k])
        out.append(T.save(im, "ep03_" + name))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]:
            T.gen(a, refs=REFS[a])
    elif sys.argv[1] == "band":
        print("\n".join(band(json.loads(sys.argv[2]))))


# ---- 絵の AI が使えないとき（2026-11-23：Gemini の前払いの残高切れで 402）：PC で描いた本番の 1080p のコマから組む ----
#   python3 thumbs03b.py hd <1080p のコマのフォルダ>   （s01_12.png・s22_ad.png・s06a_123.png・s13_549.png。dl_pc の mp4 から取り出す）
def _load(p, box=None, size=(W, H)):
    im = Image.open(p).convert("RGBA")
    if box: im = im.crop(box)
    return im.resize(size, Image.LANCZOS)


def _cover(im, w, h):
    """w×h をすき間なくおおうように縮めて、まん中で切る"""
    k = max(w / im.width, h / im.height); im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))


def tent_bubble(im, box, tail):
    """白い吹き出し（黒いふち）に、テントの絵（字なし）"""
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    d.polygon([(x0 + (x1 - x0) * 0.40, y1 - 10), (x0 + (x1 - x0) * 0.58, y1 - 10), tail], fill=(0, 0, 0, 255))
    d.rounded_rectangle(box, radius=60, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=10)
    d.polygon([(x0 + (x1 - x0) * 0.42, y1 - 14), (x0 + (x1 - x0) * 0.56, y1 - 14), (tail[0], tail[1] - 22)], fill=(255, 255, 255, 255))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; s = (y1 - y0) * 0.36
    d.rectangle((cx - s * 1.6, cy + s * 0.55, cx + s * 1.6, cy + s * 0.8), fill=(140, 200, 120, 255))
    d.polygon([(cx - s * 1.25, cy + s * 0.6), (cx, cy - s * 0.9), (cx + s * 1.25, cy + s * 0.6)], fill=(233, 105, 44, 255))
    d.polygon([(cx - s * 0.32, cy + s * 0.6), (cx, cy - s * 0.15), (cx + s * 0.32, cy + s * 0.6)], fill=(150, 55, 25, 255))
    return Image.alpha_composite(im, lay)


def red_circle(im, c, r, wd=26):
    lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay); cx, cy = c
    dl.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(255, 255, 255, 255), width=wd + 14)
    dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED2 + (255,), width=wd)
    return Image.alpha_composite(im, lay)


def waves(im, c, n=3, r0=120, step=90, ang=(150, 210), col=(80, 170, 255)):
    """音の線（左から穴へ向かう弧）"""
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); cx, cy = c
    for k in range(n):
        r = r0 + k * step
        d.arc((cx - r, cy - r, cx + r, cy + r), ang[0], ang[1], fill=(255, 255, 255, 255), width=34)
        d.arc((cx - r, cy - r, cx + r, cy + r), ang[0], ang[1], fill=col + (255,), width=20)
    return Image.alpha_composite(im, lay)


def _contain(im, w, h, fill=None):
    """w×h の中に全体が入るように縮め、余りは絵の端の色で埋める"""
    k = min(w / im.width, h / im.height); sm = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    fill = fill or im.convert("RGB").getpixel((2, im.height // 2)) + (255,)
    out = Image.new("RGBA", (w, h), fill); out.paste(sm, ((w - sm.width) // 2, (h - sm.height) // 2)); return out


def card(im, xy, text, px=96):
    """白い地・黒いふち（4px＝2560 幅で 8px）の札。字は真っ黒の極太"""
    f = T.F(px); b = f.getbbox(text); pad = int(px * 0.35); x, y = xy
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x, y, x + b[2] - b[0] + 2 * pad, y + b[3] - b[1] + 2 * pad), radius=24, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=8)
    d.text((x + pad - b[0], y + pad - b[1]), text, font=f, fill=(0, 0, 0, 255)); return Image.alpha_composite(im, lay)


def hd(D):
    out = []; bh = int(H * BAND_H)
    # A 前→後：左に電車で話す二人（吹き出しにテント）、まん中に赤い矢印、右にテントの広告が出たスマホ（スマホ全体が見えるように）
    im = Image.new("RGBA", (W, H), (240, 240, 240, 255))
    im.paste(_cover(Image.open(os.path.join(D, "s01_12.png")).convert("RGBA").crop((560, 330, 1360, 1000)), 1330, H - bh), (0, bh))
    ph = Image.open(os.path.join(D, "s22_ad.png")).convert("RGBA").crop((600, 0, 1400, 1080))
    im.paste(_contain(ph, W - 1450, H - bh), (1450, bh))
    d = ImageDraw.Draw(im); d.rectangle((1330, bh, 1450, H), fill=(255, 255, 255, 255))
    im = tent_bubble(im, (330, bh + 50, 1000, bh + 400), (700, bh + 560))
    im = T.arrow(im, (1180, 900), (1700, 900), bend=0.0, w=70, col=RED2)
    im = grade(im); im = band_text(im, BAND["A"]); out.append(T.save(im, "ep03_hdA"))
    # B アップ：スマホの下のマイクの穴をのぞく探偵まるロボ。穴に赤い丸と「マイク」の札、手前から音の線
    from PIL import ImageEnhance
    src = Image.open(os.path.join(D, "s06a_123.png")).convert("RGB"); src = ImageEnhance.Contrast(src).enhance(0.72); src = ImageEnhance.Brightness(src).enhance(1.45); src = ImageEnhance.Color(src).enhance(2.3)   # 鮮やかさを決まり（0.27〜）へ。奥が黒く明暗の差が大きすぎる（93）
    im = fit_below(src.convert("RGBA").resize((W, H), Image.LANCZOS), 0.0, band_h=BAND_H)      # 帯の下に全体を入れる（まるロボの帽子を切らない）。元の絵が暗い（明るさ 145）ので先に明るくする
    k = (1 - BAND_H) * W / 1920; X = lambda x: (W - 1920 * k) / 2 + x * k; Y = lambda y: H - 1080 * k + y * k
    im = grade(im)
    hole = (X(1180), Y(585))
    im = waves(im, hole, n=3, r0=260, step=95, ang=(100, 160))
    im = red_circle(im, hole, 170)
    im = card(im, (int(hole[0]) + 230, int(hole[1]) - 330), "マイク")
    im = band_text(im, BAND["B"]); out.append(T.save(im, "ep03_hdB"))
    # C アップ：まるロボの目の寄り（電車の座席）、右にテントの広告のスマホと赤い ？
    im = fit_below(_load(os.path.join(D, "s13_546.png")), 0.0, band_h=BAND_H); im = grade(im)
    if True:
        from PIL import ImageEnhance
        im = ImageEnhance.Brightness(im.convert("RGB")).enhance(1.04).convert("RGBA")   # 明るさ 164 → 決まりの 165〜180 へ
    ph = Image.open(os.path.join(D, "s22_ad.png")).convert("RGBA").crop((760, 20, 1250, 1070))
    ph = ph.resize((int(ph.width * 0.9), int(ph.height * 0.9)), Image.LANCZOS)
    fr = Image.new("RGBA", (ph.width + 28, ph.height + 28), (255, 255, 255, 255)); fr.paste(ph, (14, 14))
    fr = fr.rotate(-7, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(fr, (W - fr.width - 60, bh + 40))
    im = q_mark(im, (W - fr.width - 40, H - 330), 150)
    im = band_text(im, BAND["C"]); out.append(T.save(im, "ep03_hdC"))
    return out


if __name__ == "__main__" and sys.argv[1] == "hd":
    print("\n".join(hd(sys.argv[2])))
