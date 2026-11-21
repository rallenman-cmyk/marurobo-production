# QR回のサムネ：「サムネの構図の決まり」（2026-11-20 ユーザー決定。SKILL.md §9）で作る
#   上に黒い帯（高さの 17%）＋白い極太字 1 行の問い（物の名前＝黄、おかしな所・結果＝赤）。帯の下は明るく清潔な 3D の絵
#   形：A 左右の比べ／B 前→後／C アップ。印（✓・✕・？・赤い丸・赤い矢印）と画面の札はこちらで描く（絵の AI に字・印を描かせない）
#   部品は thumbs_v3.py（字・矢印・✓✕）と 4本目の thumbs04.py の q_mark・band の形をまねた
#   使い方: THUMB_WORK=<作業> THUMB_FONT=<NotoSansJP[wght].ttf> python3 thumbs_band.py gen A B C ／ comp '{"A":"QA_1.png",...}'
import os, sys, json, importlib.util
H_ = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("tv3", os.path.join(H_, "thumbs_v3.py"))
T = importlib.util.module_from_spec(_sp); sys.argv_ = sys.argv; sys.argv = [sys.argv[0], "x"]; _sp.loader.exec_module(T); sys.argv = sys.argv_
from PIL import Image, ImageDraw, ImageFilter
W, H = T.W, T.H
ROBOT = ("The small mascot robot must match the reference images exactly: a glossy white sphere body, ONE large round camera-lens eye on the front "
         "(dark navy outer ring, teal iris ring, glossy dark pupil), small teal discs on the sides, a thin grey antenna with a small beige-orange ball on "
         "top, two short stubby grey legs with dark navy boots whose soles glow teal. NO mouth, NO arms, NO hands, no eyebrows.")
BRIGHT = ("Background art for a YouTube thumbnail, 16:9, bright clean soft 3D illustration (polished explainer style: soft daylight, white and light "
          "pastel colors, smooth shading, crisp). ABSOLUTELY NO TEXT, no letters, no numbers, no logos, no icons, no check marks, no X marks, no speech "
          "bubbles. The TOP 18% of the frame will be covered by a black title band, so put nothing important there. QR codes must look like real QR codes "
          "with EXACTLY three big square corner markers (top-left, top-right, bottom-left). " + ROBOT)
PLANS = {
 "QA": ("Two panels side by side separated by a thin white gap, the SAME bright clean white desk in both. In EACH panel the SAME large crisp QR code "
        "printed on a white card stands facing the camera straight on, big (about 70% of the panel height, below the top 18%). LEFT panel: the robot "
        "SITS on the lower-right corner of the card, covering about a quarter of the code, relaxed. RIGHT panel: no robot; the code has only a few small "
        "black ink drops scattered on its white squares (small but clearly visible). Nothing else."),
 "QB": ("Two panels side by side separated by a thin white gap (before / after), same bright clean desk. LEFT panel (before): a large crisp QR code on a "
        "white card facing the camera, the robot SITS on its lower-right corner covering about a quarter of it, and a smartphone held above points its "
        "camera at the code. RIGHT panel (after): a large smartphone seen from the front, its whole screen plain blank glowing white (nothing on it), "
        "standing upright on the desk. Leave the middle gap between the panels calm (an arrow will be added)."),
 "QC": ("Close-up shot, bright soft daylight. A large crisp QR code printed on a white card faces the camera straight on and fills the center-right (x "
        "35-95%, y 22-95%); its lower-right corner is clearly torn off (a ragged paper edge, a missing piece). A smartphone enters from the upper right, "
        "its back camera pointing at the code, the instant before scanning (we see the back of the phone, no screen). The robot is small at the lower "
        "left (x 4-24%, y 60-98%), looking up at the code, curious."),
}
PLANS.update({   # 2026-11-20 ユーザー「C はおけ、なぜこっちは読めるみたいな切り口も欲しい、あとは他の切り口も」
 "QD": ("Same bright clean white desk across the whole frame. Two identical large crisp QR codes on white cards stand facing the camera straight on: "
        "the LEFT card at x 4-40%, the RIGHT card at x 60-96%, both at y 25-92%. The middle (x 40-60%) is EMPTY plain background (an arrow will be added). "
        "LEFT card: the robot SITS on its lower-right corner, covering a big part (about a third) of the code. RIGHT card: no robot; only a few small black "
        "ink drops scattered on its white squares (small but clearly visible). Nothing else."),
 "QE": ("Two panels side by side separated by a thin white gap (before / after), same bright clean desk. LEFT panel (before): a large crisp QR code "
        "printed on white paper lies on the desk facing the camera; next to it a small glass ink bottle is tipping over, a first drop of black ink flying "
        "toward the paper; the robot stands behind the bottle, surprised (it bumped the bottle with its body). RIGHT panel (after): a large smartphone seen "
        "from the front standing upright, its whole screen plain blank glowing white (nothing on it). Leave the middle gap calm (an arrow will be added)."),
 "QF": ("Close-up, bright soft daylight. One very large crisp QR code printed on a white card faces the camera straight on, filling x 30-92%, y 22-96%; its "
        "three big square corner markers (top-left, top-right, bottom-left) are clearly visible and crisp. The robot is small at the lower left (x 4-24%, "
        "y 58-98%), looking up at the top-left corner marker, curious."),
 "QG": ("Close-up, bright soft daylight. One very large crisp QR code printed on a white card faces the camera straight on, filling x 30-92%, y 22-96%; "
        "in its exact center a plain round teal badge with a simple white leaf shape covers the middle of the code (a logo, no letters). A smartphone "
        "enters from the upper right, its back camera pointing at the code, the instant before scanning (no screen visible). The robot is small at the "
        "lower left (x 4-24%, y 58-98%), looking up at the logo, curious."),
})
T.PLANS.update(PLANS)
BAND = {   # 案 → [(字, 色)]。物の名前＝黄、おかしな所・結果＝赤
 "QA": [("なぜ", "W"), ("QRコード", "Y"), ("は", "W"), ("小さな汚れ", "R"), ("で読めない？", "W")],
 "QB": [("QRコード", "Y"), ("を体で隠すと", "W"), ("どうなる", "R"), ("？", "W")],
 "QC": [("なぜ", "W"), ("欠けていても", "Y"), ("読める", "R"), ("？", "W")],   # 2026-11-21「黄色も割り振って」：欠けていても＝黄、読める＝赤   # 2026-11-21 ユーザー「サムネの文字をなぜ欠けていても読める？にして」（前は「なぜQRコードは欠けても読めるのか？」）
 "QD": [("なぜ", "W"), ("こっち", "R"), ("の", "W"), ("QRコード", "Y"), ("だけ読める？", "W")],
 "QE": [("QRコード", "Y"), ("にインクをこぼすと", "W"), ("どうなる", "R"), ("？", "W")],
 "QF": [("なぜ", "W"), ("QRコード", "Y"), ("の角には", "W"), ("四角", "R"), ("があるのか？", "W")],
 "QG": [("なぜ", "W"), ("QRコード", "Y"), ("は", "W"), ("ロゴ", "R"), ("があっても読める？", "W")],
}
# 印の位置は、10% の目盛りを重ねた一覧で絵を見て決めた（2560×1440）。QR・まるロボ・帯にかけない
MARKS = {"QA_2": [("ok", 175, 470, 105), ("ng", 2390, 470, 105)],   # 左右の比べ：左＝隠しても ✓、右＝小さな汚れで ✕（QR の外の余白に）
         "QB_1": [("q", 1958, 880, 200)],
         "P2C_2": [("ok", 880, 470, 100), ("ng", 2465, 365, 92)]}  # D は前に描いた比べの絵（P2C_2：左を空けて QR を右に寄せた絵）。Gemini が 402 で描けなかったため                           # 前→後：右のスマホの画面に赤い ？（結果を隠す）
CIRCLES = {"QA_2": [(1840, 840, 150)],                              # 右の QR の汚れ
           "QC_1": [(1720, 1170, 210)],
           "P2C_2": [(2110, 560, 165)]}                              # D：右の QR の汚れ（小さい幅でも比べる物が分かるように）                             # 欠けた角
ARROWS = {"QB_1": [((1290, 880), (1610, 880))],
          "P2C_2": [((240, 820), (990, 820))]}                      # D：左の空いた所から、読める方（まるロボが座った左の QR）を指す                     # 前→後の赤い太い矢印（2 つの絵の間）
RED2 = (248, 3, 3)   # 2026-11-21：赤は決まりの値（印・丸・矢印も同じ赤）


def q_mark(im, c, r=260):
    """大きな「？」の札（赤い丸に白い ？、白いふち）。結果を隠す（4本目の thumbs04.py と同じ形）"""
    x, y = c; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.ellipse((x - r + 10, y - r + 14, x + r + 10, y + r + 14), fill=(0, 0, 0, 110))
    d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), fill=(255, 255, 255, 255)); d.ellipse((x - r, y - r, x + r, y + r), fill=(235, 40, 40, 255))
    f = T.F(int(r * 1.5)); b = f.getbbox("？"); d.text((x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2), "？", font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)


# ---- 2026-11-21 追加のサムネのルール（references/thumbnail_rules.md「数で決めた値」。建物の深層 16 枚を数えた値）----
#   4本目の thumbs04.py の band_text・grade と同じ作り。帯 18.5%（真っ黒）・字の高さ 14.4%・字の幅 92〜97%（詰め -0.07、同じ色のふちで太く）
#   色 白 (255,255,255)・黄 (251,254,5)・赤 (248,3,3)。絵は 鮮やかさ 0.29・明暗の差 62・明るさ 170 に合わせる
BAND_H = 0.185; BAND_GLYPH = 0.144; BAND_MAXW = 0.97; BAND_TRACK = -0.07; BAND_BOLD = 0.0; SQUEEZE_MIN = 0.80   # 太らせ 0.018 は「読」がつぶれた（2026-11-21「読めるの文字潰れてて読めない」）。900 の書体だけで描く
BAND_COL = {"W": (255, 255, 255), "Y": (251, 254, 5), "R": (248, 3, 3)}
GRADE = dict(sat=0.29, std=62.0, mean=170.0)


def band_text(im, runs):
    bh = round(H * BAND_H); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, bh), fill=(0, 0, 0, 255))
    want = BAND_GLYPH * H
    for _ in range(40):
        f0 = T.F(100); b = f0.getbbox("なぜロボット見抜ける？"); px = int(100 * want / (b[3] - b[1]))
        f = T.F(px); sw = round(px * BAND_BOLD)
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
    # 短い問いは字の幅が 92% に届かないので、届くまで横に広げる（字の高さは 14.4% のまま。広げすぎない：1.15 倍まで）
    if lay.width * sq < 0.92 * W: sq = min(0.92 * W / lay.width, 1.15)
    lay = lay.resize((max(1, int(lay.width * sq)), bh), Image.LANCZOS)
    im.alpha_composite(lay, ((W - lay.width) // 2, 0))
    print("帯の字", "".join(ch for ch, _ in chars), "字数", len(chars), "字の高さ %.1f%%" % (want / H * 100), "横 %.2f" % sq)
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
    for _ in range(4):   # 鮮やかさは 1 回では届かないことがある（QR回の C は白っぽい水色で、2 倍でも 0.22）。0.27 以上になるまでくり返す（合わせて 3.5 倍まで）
        if sat >= 0.27: break
        rgb = ImageEnhance.Color(rgb).enhance(min(1.6, max(1.0, GRADE["sat"] / max(sat, 0.01)))); sat, sd, mn = stats(rgb)
    if sat > 0.31: rgb = ImageEnhance.Color(rgb).enhance(GRADE["sat"] / sat)
    sat, sd, mn = stats(rgb); print("絵の色 鮮やかさ %.2f 明暗の差 %.1f 明るさ %.1f" % (sat, sd, mn))
    return rgb.convert("RGBA")


def band_comp(choice):
    out = []
    for name, src in choice.items():
        k = name.split("_")[0]; key = src.rsplit(".", 1)[0]; im = grade(T.bg(os.path.join(T.G, src)))   # 2026-11-21：絵の色と明暗を決まりの値に
        for kind, mx, my, r in MARKS.get(key, []):
            im = q_mark(im, (mx, my), r) if kind == "q" else T.badge(im, (mx, my), kind == "ok", r)
        for cx, cy, r in CIRCLES.get(key, []):
            lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
            dl.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(255, 255, 255, 255), width=40)
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED2 + (255,), width=26)
            im = Image.alpha_composite(im, lay)
        for p0, p1 in ARROWS.get(key, []): im = T.arrow(im, p0, p1, bend=0.06, w=46, col=RED2)   # 曲げ 0 だと線に切れ目が出たので少しだけ曲げる
        im = band_text(im, BAND[k])   # 2026-11-21：帯と字を決まりの値で
        out.append(T.save(im, "band_" + name))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        T.BASE = BRIGHT
        for a in sys.argv[2:]: T.gen(a)
    else:
        print("\n".join(band_comp(json.loads(sys.argv[2]))))
