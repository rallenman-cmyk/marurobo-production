# 会話と広告の回：2D の場面（S03 あるある・S09 1万7千本の研究・S20 広告の設定）を、声の時刻に合わせて動く絵にする
# python3 scenes_2d.py <出力フォルダ> [--fps 8] [--res 1280 720]
#   出力：<場面>_####.png（コマの番号は 24 コマ/秒で数える。--fps 8 なら 3 コマおき）と <場面>_log.json（3D の場面と同じ形）
# 字は札だけ（字幕と同じことは書かない）。字は 44 以上（1280×720）
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.join(HERE, "..", "storyboard")
OUT = sys.argv[1]
def opt(n, d): return [type(x)(sys.argv[sys.argv.index(n) + 1 + k]) for k, x in enumerate(d)] if n in sys.argv else d
FPS2, = opt("--fps", [8])
W, H = opt("--res", [1280, 720])
FONT = os.environ.get("MARU_FONT_BOLD", os.path.join(os.environ.get("MARU_WORK", "."), "..", "font", "NotoSansJP_700Bold.ttf"))
TAGF = ImageFont.truetype(FONT, 46)
NAVY = (20, 36, 72)
VO = os.path.join(HERE, "..", "voice")
P = json.load(open(os.path.join(VO, "placement.json"), encoding="utf-8"))
SID = {e["no"]: e for e in json.load(open(os.path.join(VO, "script_v1_0.json"), encoding="utf-8"))}
T = {SID[p["no"]]["id"]: (p["start"], p["end"]) for p in P}
SCN = {}
for p in P:
    k = SID[p["no"]]["scene"]
    SCN.setdefault(k, [p["start"] - 0.4, None])
ks = list(SCN)
for i, k in enumerate(ks): SCN[k][1] = SCN[ks[i + 1]][0] if i + 1 < len(ks) else P[-1]["end"] + 2
def s(i, k=0): return T[i][k]
sys.path.insert(0, HERE); import wordtime as _wt
def WT(i, frag, o=0.0): return _wt.W(i, frag, o)    # 札は、その言葉を言う瞬間に（W は絵の幅なので別の名前）
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def prog(t, a, b): return ease((t - a) / max(1e-6, b - a))


def tag(d, text, cx, cy, font=TAGF, bg=(255, 255, 255)):
    bb = d.textbbox((0, 0), text, font=font); w, th = bb[2] - bb[0], bb[3] - bb[1]; h = th + 30
    assert cy + h / 2 < H - 196, ('札が字幕の帯にかかる', text)
    d.rounded_rectangle([cx - w / 2 - 22, cy - h / 2, cx + w / 2 + 22, cy + h / 2], 18, fill=bg, outline=NAVY, width=4)
    d.text((cx - w / 2 - bb[0], cy - th / 2 - bb[1]), text, font=font, fill=NAVY)


def phone(im, x, y, w, h, inner):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], 28, fill=(34, 38, 43), outline=NAVY, width=4)
    im.paste(inner.resize((w - 28, h - 28)), (x + 14, y + 14))


# ---------------- S03 あるある：吹き出しの物の絵が、一つずつスマホの広告へ飛んでいく
AD = Image.open(os.path.join(SB, "phone_ad.png")).convert("RGB")
NEWS = Image.open(os.path.join(SB, "phone_news.png")).convert("RGB")


def icon(d, k, x, y, s=1.0):
    if k == 0:   # ラーメン
        d.pieslice([x - 40 * s, y - 20 * s, x + 40 * s, y + 60 * s], 0, 180, fill=(242, 169, 59)); d.line([(x - 30 * s, y - 15 * s), (x + 35 * s, y - 45 * s)], fill=(120, 80, 40), width=int(6 * s))
    elif k == 1:  # かばん
        d.rounded_rectangle([x - 33 * s, y - 25 * s, x + 33 * s, y + 35 * s], 8, fill=(62, 124, 177)); d.arc([x - 18 * s, y - 45 * s, x + 18 * s, y - 10 * s], 180, 360, fill=(40, 60, 90), width=int(6 * s))
    else:         # 犬のえさ（骨）
        d.rounded_rectangle([x - 33 * s, y - 8 * s, x + 33 * s, y + 8 * s], 6, fill=(200, 160, 110))
        for xx in (x - 35 * s, x + 35 * s):
            for yy in (y - 10 * s, y + 10 * s): d.ellipse([xx - 10 * s, yy - 10 * s, xx + 10 * s, yy + 10 * s], fill=(200, 160, 110))


def f03(t):
    im = Image.new("RGB", (W, H), (238, 244, 247)); d = ImageDraw.Draw(im)
    d.ellipse([60, 100, 440, 400], fill="white", outline=NAVY, width=6)
    d.polygon([(150, 380), (210, 380), (120, 470)], fill="white", outline=NAVY)
    d.ellipse([110, 470, 210, 570], fill=(244, 210, 181)); d.pieslice([90, 540, 230, 700], 180, 360, fill=(62, 124, 177))
    phone(im, 860, 50, 300, 560, NEWS)
    starts = [s("03-02") + 0.2, s("03-02") + 1.4, s("03-02") + 2.6]
    for k, (x0, y0) in enumerate(((150, 260), (250, 200), (340, 270))):
        p = prog(t, starts[k], starts[k] + 1.0)
        if p >= 1:
            continue
        x, y = x0 + (1010 - x0) * p, y0 + (300 - y0) * p - 120 * math.sin(math.pi * p)
        icon(d, k, x, y, 1.0 - 0.3 * p)
    shown = sum(t >= a + 1.0 for a in starts)
    if shown:                                            # 届いた物の広告が画面に出る（最後はテント）
        im.paste(AD.resize((272, 532)), (874, 64)) if shown >= 3 else None
        if shown < 3:
            d.rounded_rectangle([890, 360, 1130, 560], 18, fill=("#FFE3A3", "#BFE3F2")[shown - 1]); icon(d, shown - 1, 1010, 460, 1.4)
    return im


# ---------------- S09 研究：アプリの四角を虫めがねが調べる → 音の印は光らない → 画面を撮る印の四角が赤く光る
APPC = [(110, 140, 180), (90, 160, 150), (160, 130, 190), (190, 150, 110), (120, 170, 120)]
RED = {(1, 3), (3, 9), (2, 12)}


def f09(t):
    im = Image.new("RGB", (W, H), (30, 42, 60)); d = ImageDraw.Draw(im)
    if t >= WT("09-02", "1万7千本"): tag(d, "1万7千本以上のアプリ", 470, 60)
    if t >= WT("09-02", "2018年"): tag(d, "2018年", 1000, 60)
    for r in range(5):
        for c in range(14):
            x, y = 80 + c * 80, 130 + r * 80
            col = APPC[(r + c) % 5]
            red = (r, c) in RED and t >= WT("09-04", "スマホの画面を")
            if red:
                col = (229, 72, 77)
            d.rounded_rectangle([x, y, x + 60, y + 60], 12, fill=col)
            if red:
                d.rectangle([x + 16, y + 12, x + 44, y + 48], outline="white", width=4); d.ellipse([x + 26, y + 24, x + 34, y + 32], fill="white")
    # 虫めがね：09-03 で端から端へ（行ごとに）
    p = prog(t, s("09-03"), s("09-03b") + 0.6)
    if 0 < p < 1 or (s("09-04") <= t < s("09-05")):
        if s("09-04") <= t:
            p = prog(t, s("09-04"), s("09-04") + 1.5)
        row = min(4, int(p * 5)); fx = (p * 5) % 1
        mx, my = 110 + fx * 1040, 160 + row * 80
        d.ellipse([mx - 70, my - 70, mx + 70, my + 70], outline=(242, 193, 78), width=14)
        d.line([(mx + 50, my + 50), (mx + 120, my + 120)], fill=(242, 193, 78), width=22)
    # 09-03b：音の印（〜）がついた四角は一つもない → 大きな × ではなく「0」の札
    if WT("09-03b", "一つも") <= t < s("09-04"):
        tag(d, "0本", 640, 330, font=ImageFont.truetype(FONT, 72))  # 数だけ（字幕と同じ文は書かない）
    # 09-06b〜e：まとめ（これまでの絵を 3 つ並べて、一つずつ光らせる）
    if t >= s("09-06") - 0.2:
        d.rectangle([0, 0, W, H], fill=(22, 30, 46))
        for k, (idn, label) in enumerate((("09-06b", "見張り番"), ("09-06c", "ランプと画面の点"), ("09-06d", "1万7千本"))):
            on = t >= s(idn)
            x0 = 90 + k * 380
            d.rounded_rectangle([x0, 130, x0 + 330, 400], 24, fill=(48, 62, 86) if on else (36, 46, 64), outline=(242, 193, 78) if on else (70, 84, 110), width=6)
            if k == 0:   # 番犬の顔（白い丸に茶色の垂れ耳・閉じた目）
                cx = x0 + 165; d.ellipse([cx - 70, 195, cx + 70, 335], fill=(242, 235, 221)); d.ellipse([cx - 105, 215, cx - 55, 325], fill=(138, 90, 52)); d.ellipse([cx + 55, 215, cx + 105, 325], fill=(138, 90, 52))
                d.arc([cx - 45, 245, cx - 15, 265], 0, 180, fill=NAVY, width=5); d.arc([cx + 15, 245, cx + 45, 265], 0, 180, fill=NAVY, width=5)
            elif k == 1:  # オレンジのランプと点
                cx = x0 + 165; d.ellipse([cx - 60, 205, cx + 60, 325], fill=(255, 122, 0))
            else:         # 四角の列
                for rr in range(3):
                    for cc in range(4):
                        d.rounded_rectangle([x0 + 45 + cc * 62, 180 + rr * 62, x0 + 95 + cc * 62, 230 + rr * 62], 8, fill=APPC[(rr + cc) % 5])
            tag(d, label, x0 + 165, 455)
        if t >= WT("09-06e", "容疑は"):                              # 1 人目の容疑者：マイク → 容疑はひとまず晴れた
            tag(d, "①マイク", 560, 80, bg=(255, 244, 214))
            d.line([(690, 80), (715, 105), (765, 50)], fill=(93, 187, 99), width=14)  # 容疑が晴れた印（字の代わりにチェック）
    return im


# ---------------- S20 広告の設定：スマホの設定の画面。広告のスイッチを切る
def f20(t):
    im = Image.new("RGB", (W, H), (12, 20, 38)); d = ImageDraw.Draw(im)
    scr = Image.new("RGB", (300, 600), (244, 246, 248)); sd = ImageDraw.Draw(scr)
    off = prog(t, s("20-01") + 2.0, s("20-01") + 2.5)
    for k in range(5):
        y = 60 + k * 100
        sd.rounded_rectangle([20, y, 280, y + 70], 14, fill="white"); sd.rounded_rectangle([30, y + 22, 170, y + 46], 8, fill=(203, 211, 220))
        on = 1.0 - off if k == 2 else 1.0
        col = tuple(int(a * on + b * (1 - on)) for a, b in zip((43, 179, 166), (190, 196, 204)))
        sd.rounded_rectangle([200, y + 18, 266, y + 52], 17, fill=col); xx = 202 + 32 * on; sd.ellipse([xx, y + 20, xx + 30, y + 50], fill="white")
    phone(im, 490, 40, 300, 600, scr)
    if t >= s("20-01"):
        tag(d, "広告の設定", 1010, 330)
        d.ellipse([643, 254 + 14, 803, 344 + 14], outline=(255, 138, 42), width=8)
    return im


SC = dict(s03=("S03", f03), s09=("S09", f09), s20=("S20", f20))
os.makedirs(OUT, exist_ok=True)
for key, (scn, fn) in SC.items():
    t0, t1 = SCN[scn]
    step = 24 // FPS2
    n = int((t1 - t0) * 24)
    for fr in range(0, n, step):
        fn(t0 + fr / 24).save(os.path.join(OUT, "%s_%04d.png" % (key, fr)))
    json.dump(dict(mode=key, t0=t0, t1=t1, fps=24, frames=n, steps=[], events=[]), open(os.path.join(OUT, key + "_log.json"), "w"))
    print(key, scn, "%.1f-%.1f" % (t0, t1), n, "コマ")
