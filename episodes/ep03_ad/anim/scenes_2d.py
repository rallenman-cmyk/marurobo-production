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
    """v4「ここ表現わかりにくい」(0:52)：「話した物 → あとで → スマホの広告に同じ物」を 3 行の表で。1 行ずつ、話す → 時計 → 広告の順に出る"""
    im = Image.new("RGB", (W, H), (238, 244, 247)); d = ImageDraw.Draw(im)
    tag(d, "話した物", 250, 50); tag(d, "あとで出た広告", 960, 50)
    starts = [s("03-01") + 0.6, WT("03-02", "話しただけ"), WT("03-02", "あとで")]
    for k, t0 in enumerate(starts):
        if t < t0: continue
        y = 165 + k * 120; pa = prog(t, t0, t0 + 0.4)
        # 話す人と吹き出し（中に物）
        d.ellipse([60, y - 40, 120, y + 20], fill=(244, 210, 181)); d.pieslice([40, y + 15, 140, y + 95], 180, 360, fill=((62, 124, 177), (229, 140, 90), (90, 160, 150))[k])
        d.rounded_rectangle([160, y - 50, 400, y + 40], 26, fill="white", outline=NAVY, width=4); d.polygon([(170, y + 10), (150, y + 25), (182, y + 30)], fill="white")
        icon(d, k, 280, y - 5, 0.85 * pa + 0.15)
        # あとで（矢印と時計）
        pb = prog(t, t0 + 0.5, t0 + 1.1)
        if pb > 0:
            x1 = 450 + 260 * pb; d.line([(450, y), (x1, y)], fill=(242, 153, 58), width=12)
            if pb >= 1:
                d.polygon([(730, y), (700, y - 22), (700, y + 22)], fill=(242, 153, 58))
                d.ellipse([560, y - 34, 628, y + 34], fill="white", outline=NAVY, width=4); d.line([(594, y), (594, y - 22)], fill=NAVY, width=5); d.line([(594, y), (612, y + 8)], fill=NAVY, width=5)
        # スマホの広告に同じ物
        pc = prog(t, t0 + 1.1, t0 + 1.5)
        d.rounded_rectangle([760, y - 55, 1160, y + 55], 18, fill=(34, 38, 43)); d.rounded_rectangle([772, y - 45, 1148, y + 45], 12, fill="white")
        for q in range(2): d.rectangle([790, y - 30 + q * 22, 900, y - 22 + q * 22], fill=(203, 211, 220))
        if pc > 0:
            d.rounded_rectangle([930, y - 40, 1140, y + 40], 12, fill=("#FFE3A3", "#BFE3F2", "#D7EFD0")[k]); icon(d, k, 1035, y - 2, 0.7 * pc + 0.1)
    if t >= s("03-03"):
        d.text((1180, 420), "!?", font=ImageFont.truetype(FONT, 72), fill=(229, 72, 77))
    return im


# ---------------- S09 研究：アプリの四角を虫めがねが調べる → 音の印は光らない → 画面を撮る印の四角が赤く光る
APPC = [(110, 140, 180), (90, 160, 150), (160, 130, 190), (190, 150, 110), (120, 170, 120)]
RED = {(1, 3), (3, 9), (2, 12)}


def gate2d(d, cx, cy, sc=1.0, open_=0.0):
    """門（2 本の柱と、上下する格子）。open_：0 閉じ・1 開き"""
    d.rectangle([cx - 150 * sc, cy - 170 * sc, cx - 110 * sc, cy + 110 * sc], fill=(225, 228, 233), outline=NAVY, width=4)
    d.rectangle([cx + 110 * sc, cy - 170 * sc, cx + 150 * sc, cy + 110 * sc], fill=(225, 228, 233), outline=NAVY, width=4)
    d.rectangle([cx - 160 * sc, cy - 200 * sc, cx + 160 * sc, cy - 165 * sc], fill=(225, 228, 233), outline=NAVY, width=4)
    lift = 250 * sc * open_
    for k in range(6):
        x = cx - 95 * sc + k * 38 * sc
        d.line([(x, cy - 160 * sc - lift * 0.0), (x, cy + 105 * sc - lift)], fill=(120, 130, 150), width=int(8 * sc))


def dogface(d, cx, cy, sc=1.0):
    d.ellipse([cx - 70 * sc, cy - 70 * sc, cx + 70 * sc, cy + 70 * sc], fill=(242, 235, 221))
    d.ellipse([cx - 105 * sc, cy - 50 * sc, cx - 55 * sc, cy + 60 * sc], fill=(138, 90, 52)); d.ellipse([cx + 55 * sc, cy - 50 * sc, cx + 105 * sc, cy + 60 * sc], fill=(138, 90, 52))
    d.arc([cx - 45 * sc, cy - 20 * sc, cx - 15 * sc, cy], 0, 180, fill=NAVY, width=5); d.arc([cx + 15 * sc, cy - 20 * sc, cx + 45 * sc, cy], 0, 180, fill=NAVY, width=5)
    d.ellipse([cx - 14 * sc, cy + 12 * sc, cx + 14 * sc, cy + 32 * sc], fill=NAVY)
    d.chord([cx - 60 * sc, cy - 95 * sc, cx + 60 * sc, cy - 35 * sc], 180, 360, fill=(52, 72, 110))


def sneaky_app(d, cx, cy, sc=1.0):
    """こっそり音を拾うアプリ（黒っぽい四角に、目かくしの帯とマイク）"""
    d.rounded_rectangle([cx - 60 * sc, cy - 60 * sc, cx + 60 * sc, cy + 60 * sc], int(22 * sc), fill=(60, 50, 80), outline=NAVY, width=4)
    d.rounded_rectangle([cx - 52 * sc, cy - 28 * sc, cx + 52 * sc, cy - 4 * sc], 8, fill=(20, 20, 30))
    for k in (-1, 1): d.ellipse([cx + k * 24 * sc - 7 * sc, cy - 23 * sc, cx + k * 24 * sc + 7 * sc, cy - 9 * sc], fill="white")
    d.rounded_rectangle([cx - 9 * sc, cy + 8 * sc, cx + 9 * sc, cy + 38 * sc], int(9 * sc), fill=(229, 72, 77))


def f09(t):
    im = Image.new("RGB", (W, H), (30, 42, 60)); d = ImageDraw.Draw(im)
    # 09-01（v4「表現わかりにくい」5:19）：合言葉を言っていないのに、こっそりアプリが門を開けて、外の音（話し声の泡）が入ってくる
    if t < s("09-02"):
        op = prog(t, WT("09-01", "こっそり"), WT("09-01", "こっそり") + 1.2)
        gate2d(d, 640, 330, 1.0, op)
        sneaky_app(d, 920, 380, 1.0)
        if op > 0.3:
            for k in range(4):
                ph = ((t - WT("09-01", "こっそり")) * 0.6 + k * 0.25) % 1.0
                x = 180 + ph * 460; y = 300 + 30 * math.sin(k * 1.7)
                d.ellipse([x - 26, y - 26, x + 26, y + 26], outline=(180, 220, 255), width=5)
                d.arc([x - 12, y - 10, x + 12, y + 10], 200, 340, fill=(180, 220, 255), width=4)
        return im
    if t >= WT("09-02", "1万7千本"): tag(d, "1万7千本以上のアプリ", 470, 60)
    if t >= WT("09-02", "2018年"): tag(d, "2018年", 1000, 60)
    t_red = WT("09-04", "スマホの画面を"); REDL = [(1, 3), (2, 12), (3, 9)]
    for r in range(5):
        for c in range(14):
            x, y = 80 + c * 80, 130 + r * 80
            col = APPC[(r + c) % 5]
            red = (r, c) in REDL and t >= t_red + 0.8 * REDL.index((r, c))
            if red: col = (229, 72, 77)
            d.rounded_rectangle([x, y, x + 60, y + 60], 12, fill=col)
            if red: d.rectangle([x + 16, y + 12, x + 44, y + 48], outline="white", width=4); d.ellipse([x + 26, y + 24, x + 34, y + 32], fill="white")
    # 虫めがね：09-03 で行ごとに調べる。09-04（v4「虫めがねと見つけたアプリの位置が合ってない」5:52）：赤くなるアプリへ順に動いて止まる
    mpos = None
    p = prog(t, s("09-03"), s("09-03b") + 0.6)
    if 0 < p < 1:
        row = min(4, int(p * 5)); fx = (p * 5) % 1; mpos = (110 + fx * 1040, 160 + row * 80)
    if s("09-04") <= t < s("09-06"):
        k = 0
        for q in range(3):
            if t >= t_red + 0.8 * q - 0.4: k = q
        r, c = REDL[k]; tx, ty = 80 + c * 80 + 30, 130 + r * 80 + 30
        if t < t_red - 0.4: tx, ty = 640, 330
        mpos = (tx, ty)
    if mpos:
        mx, my = mpos
        d.ellipse([mx - 70, my - 70, mx + 70, my + 70], outline=(242, 193, 78), width=14)
        d.line([(mx + 50, my + 50), (mx + 120, my + 120)], fill=(242, 193, 78), width=22)
    if WT("09-03b", "一つも") <= t < s("09-04"):
        tag(d, "0本", 640, 330, font=ImageFont.truetype(FONT, 72))
    # まとめ（09-06b〜）。v4「まだまとめてないのにネタバレ」(6:04)：前置き（09-06）の間はマイクのアップを差し込み（組み立て）、
    #   ここでは、言った物から 1 枚ずつ出す（先に枠を並べない）。v4「アイコン分かりやすく」(6:18)：門・スマホの点・虫めがねの絵で
    if t >= s("09-06b"):
        d.rectangle([0, 0, W, H], fill=(22, 30, 46))
        for k, (idn, label) in enumerate((("09-06b", "見張り番"), ("09-06c", "ランプと画面の点"), ("09-06d", "1万7千本"))):
            if t < s(idn): continue
            x0 = 90 + k * 380; cx = x0 + 165
            d.rounded_rectangle([x0, 130, x0 + 330, 400], 24, fill=(48, 62, 86), outline=(242, 193, 78), width=6)
            if k == 0:
                gate2d(d, cx + 60, 300, 0.45, 0.0); dogface(d, cx - 70, 300, 0.6)
            elif k == 1:
                d.rounded_rectangle([cx - 70, 170, cx + 70, 380], 20, fill=(34, 38, 43)); d.rounded_rectangle([cx - 58, 184, cx + 58, 366], 12, fill=(235, 240, 245))
                d.ellipse([cx + 30, 192, cx + 50, 212], fill=(255, 122, 0)); d.ellipse([cx + 18, 180, cx + 62, 224], outline=(255, 122, 0), width=4)
                d.ellipse([cx - 135, 180, cx - 95, 220], fill=(255, 122, 0))
            else:
                for rr in range(3):
                    for cc in range(4):
                        d.rounded_rectangle([x0 + 45 + cc * 62, 180 + rr * 62, x0 + 95 + cc * 62, 230 + rr * 62], 8, fill=APPC[(rr + cc) % 5])
                d.ellipse([cx - 10, 210, cx + 110, 330], outline=(242, 193, 78), width=12); d.line([(cx + 92, 312), (cx + 140, 360)], fill=(242, 193, 78), width=16)
            tag(d, label, x0 + 165, 455)
        if t >= WT("09-06e", "容疑は"):
            tag(d, "①マイク", 560, 80, bg=(255, 244, 214))
            d.line([(690, 80), (715, 105), (765, 50)], fill=(93, 187, 99), width=14)
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
        d.ellipse([715 - 52, 335 - 30, 715 + 52, 335 + 30], outline=(255, 138, 42), width=7)   # v4「丸の位置ずれてる」：3 つ目のスイッチ（画面の y=278〜312 → 319〜351）に合わせた
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
