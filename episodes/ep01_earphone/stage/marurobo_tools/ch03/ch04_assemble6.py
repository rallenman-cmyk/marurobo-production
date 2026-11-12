# 第4章 v6（台本 v2、2026-11-06）の確認用動画：新しい時刻（stage/script/script_v2_timed.json）
#   D1：止まった車内（隣の人のイヤホン）→ 図 D2〜D7（元の絵を新しい時刻へずらす）→ よく見るペアリング画面 → ペアリングの3D（ch04_pairing6.py）
#   （途中の「十人十色」は車内の全景に色の丸）→ 2D：「接続しました ✓」と同じ鍵、鍵のない隣は開けない → D8：車内の全景に、組ごとの別の印
# 使い方: python3 ch04_assemble6.py OUT_DIR --pair=PAIR6_DIR（先に ch04_diagram.py OUT_DIR --v6=PAIR6_DIR で diagram6/ を作る）
import sys, os, json, math, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "script")); import timewarp as tw
SRT = os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")                         # 声（Gemini・Achernar）に合わせた字幕（2026-11-07）
FONTS = os.path.join(HERE, "..", "av", "fonts"); JFONT = os.path.join(FONTS, "japanese.ttc")
FPS, SR, W, H = 24, 48000, 1280, 720                                     # 札・図の位置は 1280×720 の目盛りのまま
DW, DH = (1920, 1080) if os.environ.get("MARU_RES") == "1080" else (W, H)  # 本番（MARU_RES=1080）：実際の絵は 1920×1080
SCL = DW / W
_RAW_DRAW = ImageDraw.Draw
class SD:
    """1280×720 の目盛りで書いた描く命令を、実際の大きさ（DW×DH）に広げて描く（字や線がにじまない）"""
    def __init__(self, im): self.d = _RAW_DRAW(im)
    @staticmethod
    def _s(v):
        if isinstance(v, bool) or v is None: return v
        if isinstance(v, (int, float)): return v * SCL
        if isinstance(v, (list, tuple)): return type(v)(SD._s(x) for x in v)
        return v
    @staticmethod
    def _kw(kw):
        for k in ("width", "stroke_width"):
            if kw.get(k): kw[k] = max(1, int(round(kw[k] * SCL)))
        if kw.get("radius"): kw["radius"] = kw["radius"] * SCL
        return kw
    def text(self, xy, txt, **kw): return self.d.text(SD._s(xy), txt, **SD._kw(kw))
    def textlength(self, txt, **kw): return self.d.textlength(txt, **kw) / SCL
    def textbbox(self, xy, txt, **kw): return tuple(v / SCL for v in self.d.textbbox(SD._s(xy), txt, **SD._kw(kw)))
    def __getattr__(self, name):
        f = getattr(self.d, name)
        def g(xy, *a, **kw): return f(SD._s(xy), *a, **SD._kw(kw))
        return g
def FT(px): return ImageFont.truetype(JFONT, max(6, int(round(px * SCL))))
DG = json.load(open(os.path.join(OUT, "ch04_diagram6.json")))
CH0, CH1 = DG["t0"], DG["t1"]; T_D2, T_D8 = DG["d2"], DG["d8"]
N = int(round((CH1 - CH0) * FPS)); T = N / FPS
PAIR_DIR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--pair=")), os.path.join(OUT, "pair6"))
PL = json.load(open(os.path.join(PAIR_DIR, "pairing_log.json")))
TP0, TP1 = PL["t0"], PL["t1"]; SKIP = PL["skip"]; PT = PL["times"]; P = {int(k): v for k, v in PT["P"].items()}
HEADS = json.load(open(os.path.join(OUT, "ch04_heads.json")))
# ---------------------------------------------------------------- v8（2026-11-08 ユーザー：6:24 は②）：声を「…青と赤は入りますが、白が二回分入るので、薄い紫にしかなりません」に替え、
#   その場面（NB：隣のイヤホン。カメラの寄りが止まったあと）を DELTA 秒のばす。後ろの絵・声・字幕・効果音は DELTA ずらす（--alt624）
ALT624 = "--alt624" in sys.argv
ALT_TXT = "もし、隣のイヤホンが見えた二つを混ぜても……青と赤は入りますが、白が二回分入るので、薄い紫にしかなりません。"
ALT_WAV = os.path.join(HERE, "..", "voice", "achernar", "line_067_b.wav")
DELTA = 2.25 if ALT624 else 0.0                                          # 54 コマ：次の文（P16）の前の間を 2.25 → 1.5 秒に
INS_T = 392.55                                                           # NB の画でカメラの寄りが止まる（384.482＋8.0）すぐあと。ここで 3D を止めてのばす
ALT_A, ALT_LEN = P[15][0], 0.0
if ALT624:
    with wave.open(ALT_WAV) as w_: ALT_LEN = w_.getnframes() / w_.getframerate()
CH1_OUT = CH1 + DELTA
N = int(round((CH1_OUT - CH0) * FPS)); T = N / FPS
T_OUT = [CH0]                                                            # いま組んでいるコマの、出す時刻（札を新しい声に合わせる）
def warp(t):
    """出す時刻 → 元の時刻（3D・図・札は元の時刻で描く）。INS_T から DELTA 秒は INS_T のまま止める"""
    if t < INS_T: return t
    return INS_T if t < INS_T + DELTA else t - DELTA
def unwarp(t):
    """元の時刻 → 出す時刻（効果音・字幕・声）"""
    return t if t < INS_T else t + DELTA
def alt_char(n): return ALT_A + ALT_LEN * n / len(ALT_TXT)
TEAL = (31, 94, 102); AMBER = (214, 128, 44)
LAB_COL = dict(teal=(31, 94, 102), ink=(40, 46, 52), amber=(214, 128, 44), key=(118, 92, 170), blue=(52, 102, 210), red=(204, 58, 118))
D8_SHIFT = T_D8 - 264.578                                                 # D8 の印の時刻（元の版）を、新しい時刻へ


def sm(u):
    u = max(0.0, min(1.0, u)); return u * u * u * (10 - 15 * u + 6 * u * u)


def at_char(k, n):
    txt = [e["text"] for e in json.load(open(os.path.join(HERE, "..", "script", "script_v2_timed.json"), encoding="utf-8")) if e["tag"] == "P%d" % k][0]
    a, b = P[k]; return a + (b - a) * n / len(txt)


def spotlight(im, c, r, k):
    if k <= 0: return im
    m = Image.new("L", im.size, 0); SD(m).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.45 * SCL))
    dark = Image.eval(im, lambda v: int(v * (1.0 - 0.55 * k)))
    return Image.composite(im, dark, m)


def tag(d, xy, txt, col, px=34):
    f = FT(px); w = d.textlength(txt, font=f); x, y = xy
    d.rounded_rectangle([x - w / 2 - 16, y - px * 0.75, x + w / 2 + 16, y + px * 0.75], radius=12, fill=(250, 250, 248), outline=col, width=3)
    d.text((x, y), txt, font=f, fill=col, anchor="mm", stroke_width=1, stroke_fill=col)


def crop_push(im, t, t0, t1, cx, cy, z1=0.94):
    Wi, Hi = im.size; z = 1.0 + (z1 - 1.0) * sm((t - t0) / (t1 - t0))
    w, h = Wi * z, Hi * z; x0 = min(max(cx * Wi - w / 2, 0), Wi - w); y0 = min(max(cy * Hi - h / 2, 0), Hi - h)
    return im.resize((DW, DH), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h)), (x0, y0, w, h)


PALETTE = [(92, 120, 190), (176, 84, 140), (70, 150, 90), (150, 110, 60), (120, 90, 170), (200, 90, 80), (60, 140, 160), (160, 140, 40)]
AMB_KEY = (226, 160, 72)                                                                      # 隣の組の鍵（ch04_diagram の AMB_KEY と同じ）
KEY_PALETTE = [(70, 150, 90), (60, 128, 196), (200, 84, 78), (40, 156, 160), (214, 108, 156), (130, 150, 50), (72, 92, 168)]   # ほかの組の鍵：紫・橙（と、橙に近い茶・朱）は使わない


def key_badge(d, c, R, col, tail=False):
    """組の鍵の札：その組の色の丸に、白い鍵。近い人は下に小さな三角（その人の頭を指す）"""
    x, y = c
    if tail: d.polygon([(x - 0.42 * R, y + 0.78 * R), (x + 0.42 * R, y + 0.78 * R), (x, y + 1.42 * R)], fill=(250, 250, 248))
    d.ellipse([x - R - 2.5, y - R - 2.5, x + R + 2.5, y + R + 2.5], fill=(250, 250, 248))
    d.ellipse([x - R, y - R, x + R, y + R], fill=col)
    wk = max(2, int(round(0.15 * R))); rr = 0.25 * R; bx = x - 0.36 * R
    d.ellipse([bx - rr, y - rr, bx + rr, y + rr], outline=(255, 255, 255), width=wk)                     # 鍵の輪
    d.line([bx + rr, y, x + 0.58 * R, y], fill=(255, 255, 255), width=wk)                                 # 軸
    for tx in (0.28, 0.48): d.line([x + tx * R, y, x + tx * R, y + 0.27 * R], fill=(255, 255, 255), width=wk)   # 歯
SHAPES = ["s", "d", "x", "h", "star", "o2", "t2"]


def draw_mark(d, c, kind, r, col, width):
    x, y = c
    if kind in ("o", "o2"):
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=width)
        if kind == "o2": d.ellipse([x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45], fill=col)
    elif kind in ("t", "t2"):
        sgn = 1 if kind == "t" else -1
        d.polygon([(x, y - sgn * r * 1.15), (x - r * 1.05, y + sgn * r * 0.75), (x + r * 1.05, y + sgn * r * 0.75)], outline=col, width=width)
    elif kind == "s": d.rectangle([x - r * 0.9, y - r * 0.9, x + r * 0.9, y + r * 0.9], outline=col, width=width)
    elif kind == "d": d.polygon([(x, y - r * 1.2), (x + r, y), (x, y + r * 1.2), (x - r, y)], outline=col, width=width)
    elif kind == "x":
        d.line([x - r, y, x + r, y], fill=col, width=width + 1); d.line([x, y - r, x, y + r], fill=col, width=width + 1)
    elif kind == "h": d.polygon([(x + r * math.cos(a), y + r * math.sin(a)) for a in [math.pi / 6 + k * math.pi / 3 for k in range(6)]], outline=col, width=width)
    else:
        pts = [(x + (r if k % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + k * math.pi / 5), y + (r if k % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
        d.polygon(pts, outline=col, width=width)


def lab(im, txt, xy, col, t, t0, t1, px=30):
    """3D に重ねる札（白地・色の枠）。xy が None なら出さない"""
    if xy is None: return
    a = sm((t - t0) / 0.3) * (1 - sm((t - t1) / 0.3))
    if a <= 0.02: return
    d0 = SD(im); f = FT(px); w_ = d0.textlength(txt, font=f); x, y = xy
    x = min(max(x, w_ / 2 + 20), W - w_ / 2 - 20); y = min(max(y, 70), H - 170)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = SD(ov); al = int(255 * a)
    od.rounded_rectangle([x - w_ / 2 - 14, y - px * 0.72, x + w_ / 2 + 14, y + px * 0.72], radius=12, fill=(250, 250, 248, int(235 * a)), outline=col + (al,), width=3)
    od.text((x, y), txt, font=f, fill=col + (al,), anchor="mm", stroke_width=1, stroke_fill=col + (al,))
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))


def ring(im, xy, r, col, t, t0, t1, width=4):
    if xy is None: return
    a = sm((t - t0) / 0.3) * (1 - sm((t - t1) / 0.3))
    if a <= 0.02: return
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = SD(ov); al = int(255 * a)
    rr = r * (1.0 + 0.06 * math.sin(2 * math.pi * 1.3 * (t - t0)))
    od.ellipse([xy[0] - rr, xy[1] - rr, xy[0] + rr, xy[1] + rr], outline=col + (al,), width=width)
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))


def panel(im, t, t0, t1, rows, x0=None, y0=28):
    """上の札（色の丸と言葉の並び）。rows：[(要素...)]、要素は ('c', rgb) 色の丸 / ('s', 文字)"""
    a = sm((t - t0) / 0.35) * (1 - sm((t - t1) / 0.3))
    if a <= 0.02: return
    f = FT(34); d0 = SD(im)
    def wid(row): return sum((48 if e[0] == "c" else d0.textlength(e[1], font=f) + 10) for e in row)
    bw = max(wid(r) for r in rows) + 48; bh = 62 * len(rows) + 26
    x0 = (W - bw) / 2 if x0 is None else x0
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = SD(ov); al = int(255 * a)
    od.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=18, fill=(250, 250, 248, int(238 * a)), outline=(205, 210, 215, al), width=2)
    for j, row in enumerate(rows):
        x = x0 + 24 + (bw - 48 - wid(row)) / 2; y = y0 + 44 + 62 * j
        for e in row:
            if e[0] == "c":
                od.ellipse([x + 4, y - 20, x + 44, y + 20], fill=e[1] + (al,), outline=(120, 126, 132, al), width=2); x += 48
            else:
                od.text((x + 5, y), e[1], font=f, fill=LAB_COL["ink"] + (al,), anchor="lm", stroke_width=1, stroke_fill=LAB_COL["ink"] + (al,)); x += d0.textlength(e[1], font=f) + 10
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))


LOCK_ICON = "🔒"
C_LB, C_PK, C_LAV, C_PALE = (127, 167, 227), (226, 133, 177), (147, 122, 186), (170, 149, 201)
C_WH, C_BL, C_RD = (245, 245, 242), (52, 102, 210), (204, 58, 118)


def pop(u):
    """弾んで出る大きさ（0 → 1.13 → 1）"""
    return 0.0 if u <= 0 else 1.0 - math.exp(-u / 0.10) * math.cos(2 * math.pi * u / 0.40)


def recipe_p15(im, t):
    """P15（v7）：隣が、見えた二つ（水色・桃色）を混ぜると、中身は 白・白・青・赤 → 白が二回分なので、うすい紫。二台の鍵（白・青・赤）の紫と並べる。
    「白になるのでは？」への答え：青と赤が入っているので紫になる。白は色をうすくするだけ（下の一行）"""
    t_in = at_char(15, 10) - 0.15; t_eq = at_char(15, 16); t_w2 = at_char(15, 22) - 0.05; t_pale = at_char(15, 31) - 0.25
    t_cap = t_pale + 0.6; t_out = P[16][0] - 0.40                                   # カメラが二つの紫へ切り替わる前に消す
    t_br = None
    if ALT624:                                                                       # v8：②の言葉の位置で（出す時刻で数える）。「青と赤は入りますが」で青と赤を囲む
        t = T_OUT[0]
        t_in = alt_char(10) - 0.15; t_eq = alt_char(16); t_br = alt_char(22) - 0.05; t_w2 = alt_char(32) - 0.05; t_pale = alt_char(42) - 0.25
        t_cap = t_pale + 0.6; t_out = P[16][0] + DELTA - 0.40
    A = sm((t - t_in) / 0.35) * (1 - sm((t - t_out) / 0.3))
    if A <= 0.02: return
    f = FT(32); f2 = FT(26); f3 = FT(24); d0 = SD(im)
    CW, R, RB = 48, 19, 25
    tl = lambda s_, ff=f: d0.textlength(s_, font=ff)
    lab1, lab2, plus, eq, arr = "隣が混ぜると", "二台の鍵", "＋", "＝", "→"
    # 横の位置（一段目）。二段目の 白・青・赤・→・できた色 は、一段目の 二つ目の白 からの列にそろえる
    xs = {}; x = 0.0
    xs["L1"] = x; x += tl(lab1) + 16
    xs["LB"] = x + CW / 2; x += CW
    xs["P1"] = x; x += tl(plus) + 8
    xs["PK"] = x + CW / 2; x += CW
    xs["EQ"] = x; x += tl(eq) + 8
    for k in ("W1", "W2", "B", "R"): xs[k] = x + CW / 2; x += CW
    xs["AR"] = x + 2; x += tl(arr) + 12
    xs["OUT"] = x + RB; x += 2 * RB + 12
    xs["T"] = x; x += max(tl("うすい紫", f2), tl("鍵の紫", f2))
    cap = "青と赤が入っているので紫。白が多いぶん、うすくなる"
    bw = max(x, tl(cap, f3)) + 48; x0 = (W - bw) / 2 + 24; y0 = 22
    y1, y2 = y0 + 44, y0 + 44 + 92; yc = y2 + 48; bh = yc + 24 - y0                   # 二段目は「白が2回」の下へ
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = SD(ov)
    def al(a_): return int(255 * max(0.0, min(1.0, a_)) * A)
    INK = LAB_COL["ink"]; AMB = LAB_COL["amber"]; PUR = LAB_COL["key"]
    od.rounded_rectangle([x0 - 24, y0, x0 - 24 + bw, y0 + bh], radius=18, fill=(250, 250, 248, al(0.94)), outline=(205, 210, 215, al(1)), width=2)
    def txt(s_, xy, col, a_, ff=f, anchor="lm"):
        if a_ > 0.01: od.text(xy, s_, font=ff, fill=col + (al(a_),), anchor=anchor, stroke_width=1, stroke_fill=col + (al(a_),))
    def dot(cx, cy, rgb, a_, sc=1.0, r=R):
        if a_ <= 0.01 or sc <= 0.02: return
        rr = r * sc; od.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=rgb + (al(a_),), outline=(120, 126, 132, al(a_)), width=2)
    # 一段目：隣が混ぜると［水色］＋［桃色］
    a1 = sm((t - t_in) / 0.3)
    txt(lab1, (x0 + xs["L1"], y1), AMB, a1)
    dot(x0 + xs["LB"], y1, C_LB, a1); txt(plus, (x0 + xs["P1"], y1), INK, a1); dot(x0 + xs["PK"], y1, C_PK, a1)
    # ＝ 白・白・青・赤（中身。順に弾んで出る）
    txt(eq, (x0 + xs["EQ"], y1), INK, sm((t - t_eq) / 0.25))
    for j, (k, rgb) in enumerate((("W1", C_WH), ("W2", C_WH), ("B", C_BL), ("R", C_RD))):
        u = t - t_eq - 0.10 - 0.09 * j
        hb = 1.0 + 0.12 * math.sin(math.pi * min(max((t - t_w2) / 0.35, 0), 1)) if k in ("W1", "W2") else 1.0   # 「白が二回分」で白が二つとも跳ねる
        if t_br is not None and k in ("B", "R"): hb = 1.0 + 0.12 * math.sin(math.pi * min(max((t - t_br) / 0.35, 0), 1))   # v8：「青と赤は」で二つとも跳ねる
        dot(x0 + xs[k], y1, rgb, sm(u / 0.12), pop(u) * hb)
    # v8：青と赤：二つを紫の枠で囲み、下に「青と赤」（「青と赤は入りますが」）
    if t_br is not None:
        hq = sm((t - t_br) / 0.3)
        if hq > 0.01:
            od.rounded_rectangle([x0 + xs["B"] - 27, y1 - 27, x0 + xs["R"] + 27, y1 + 27], radius=14, outline=PUR + (al(hq),), width=4)
            txt("青と赤", (x0 + (xs["B"] + xs["R"]) / 2, y1 + 44), PUR, hq, f3, "mm")
    # 白が二回分：二つの白を橙の枠で囲み、下に「白が2回」
    hw = sm((t - t_w2) / 0.3)
    if hw > 0.01:
        od.rounded_rectangle([x0 + xs["W1"] - 27, y1 - 27, x0 + xs["W2"] + 27, y1 + 27], radius=14, outline=AMB + (al(hw),), width=4)
        txt("白が2回", (x0 + (xs["W1"] + xs["W2"]) / 2, y1 + 44), AMB, hw, f3, "mm")
    # → うすい紫（できた色）
    up = t - t_pale
    txt(arr, (x0 + xs["AR"], y1), INK, sm(up / 0.25)); dot(x0 + xs["OUT"], y1, C_PALE, sm(up / 0.12), pop(up), RB)
    txt("うすい紫", (x0 + xs["T"], y1), AMB, sm((up - 0.15) / 0.3), f2)
    # 二段目：二台の鍵［白・青・赤］→ 紫（同じ列にそろえて比べる）
    a2 = sm((up - 0.25) / 0.35)
    txt(lab2, (x0 + xs["W2"] - CW / 2 - 14, y2), PUR, a2, f, "rm")
    for k, rgb in (("W2", C_WH), ("B", C_BL), ("R", C_RD)): dot(x0 + xs[k], y2, rgb, a2)
    txt(arr, (x0 + xs["AR"], y2), INK, a2); dot(x0 + xs["OUT"], y2, C_LAV, a2, 1.0, RB); txt("鍵の紫", (x0 + xs["T"], y2), PUR, a2, f2)
    # 下の一行：白にならない理由
    txt(cap, (x0 - 24 + bw / 2, yc), INK, sm((t - t_cap) / 0.4), f3, "mm")
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))


def pair_overlay(im, t, anc):
    def at(nm_, dx=0, dy=0):
        a = anc.get(nm_)
        if not a or a[2] <= 0 or not (0.02 < a[0] < 0.98 and 0.02 < a[1] < 0.98): return None
        return (a[0] * W + dx, a[1] * H + dy)
    def at_top(nm_, dx=0, dy=0):
        """寄りの画で、点が画面の上の外に出ているとき（びんの上が切れている）は、上の端に寄せて出す（lab が y を 70 に止める）"""
        a = anc.get(nm_)
        if not a or a[2] <= 0 or not (0.02 < a[0] < 0.98) or a[1] > 0.98: return None
        return (a[0] * W + dx, max(a[1], 0.0) * H + dy)
    def mid(n1, n2, dy=0):
        p1, p2 = at(n1), at(n2)
        if p1 is None or p2 is None: return p1 or p2
        return ((p1[0] + p2[0]) / 2, min(p1[1], p2[1]) + dy)
    # 台の名前（最初の引き）・隣のイヤホン（電波が見えている）
    lab(im, "スマホ", at("tagP"), LAB_COL["teal"], t, TP0 + 0.4, P[3][1] + 0.4)
    lab(im, "イヤホン", at("tagE"), LAB_COL["teal"], t, TP0 + 0.4, P[3][1] + 0.4)
    lab(im, "隣のイヤホン", at("tagN"), LAB_COL["amber"], t, P[11][0] - 0.1, P[11][1] + 0.6)
    # ひみつの色（寄りの画）
    c4 = at_char(4, 10)
    lab(im, "スマホのひみつ（青）", at_top("secP", 0, -6), LAB_COL["blue"], t, P[4][0] + 0.15, c4 - 0.05)
    lab(im, "イヤホンのひみつ（赤）", at_top("secE", 0, -6), LAB_COL["red"], t, c4 + 0.05, P[4][1] + 0.3)
    # 相手にも見せない
    pass                                                              # 2026-11-09：「相手にも見せない」は字幕と同じなのでやめた
    # みんなが知っている白
    for k_ in ("P", "E"): lab(im, "みんなが知っている白", at("white" + k_, 0, -8), LAB_COL["ink"], t, PT["white"] - 0.2, P[8][1] + 0.3, 28)   # 注ぐ間（約2.3秒）と「白は、みんなが知っている色です」の終わりまで
    # 混ぜた色
    lab(im, "水色", at("cupA", 0, -6), LAB_COL["blue"], t, PT["sec1"]["P"] + 0.75, PT["sec1"]["E"] - 0.6)   # 「スマホは水色」と言い終わる、イヤホンへ切り替わる前まで
    lab(im, "桃色", at("cupB", 0, -6), LAB_COL["red"], t, PT["sec1"]["E"] + 0.75, PT["sec1"]["E"] + 2.6)
    # 隣に見えている写し
    # 2026-11-09：「見えている」は字幕と同じなのでやめた（写しそのものは出る）
    # 同じ紫：二つのコップを囲み、上に「白＋青＋赤 ＝ 白＋赤＋青」
    for nm_ in ("A", "B"): ring(im, at("cupb" + nm_), 46, LAB_COL["key"], t, P[13][0] + 1.4, P[13][1] + 0.6)
    panel(im, t, at_char(13, 15), P[13][1] + 0.6, [[("c", C_WH), ("s", "＋"), ("c", C_BL), ("s", "＋"), ("c", C_RD), ("s", "＝"), ("c", C_WH), ("s", "＋"), ("c", C_RD), ("s", "＋"), ("c", C_BL)]])
    # 両方のひみつが入ったときにしかできない
    lab(im, "スマホのひみつ（青）", at("secP", 0, -6), LAB_COL["blue"], t, at_char(14, 6), P[14][1] + 0.3)
    lab(im, "イヤホンのひみつ（赤）", at("secE", 0, -6), LAB_COL["red"], t, at_char(14, 14), P[14][1] + 0.3)
    panel(im, t, at_char(14, 26), P[14][1] + 0.3, [[("c", C_BL), ("s", "＋"), ("c", C_RD), ("s", "＋"), ("c", C_WH), ("s", "→"), ("c", C_LAV)]])
    # 隣が混ぜても：薄い紫（本物と並べる）。v7：中身（白・白・青・赤）を見せ、白が二回分なので薄い、を式の札で
    tm = PT["merge"]
    recipe_p15(im, t)                                                                    # v7：3D の「薄い紫」の札はやめた（上の札に「うすい紫」。同じ色の丸で、下のコップとつながる）
    # 鍵
    lab(im, "鍵", at("keyP", 0, -40), LAB_COL["key"], t, PT["key_in"] + 0.9, P[16][1] + 1.2, 32)
    lab(im, "鍵", at("keyE", 0, -40), LAB_COL["key"], t, PT["key_in"] + 0.9, P[16][1] + 1.2, 32)


# ---------------------------------------------------------------- 絵
VER = next((a_.split("=", 1)[1] for a_ in sys.argv if a_.startswith("--ver=")), "v7")         # 版（v7＝2026-11-07、v8＝スマホの台を大きくした 2026-11-08）
VN = VER.lstrip("v")
SEQ = os.path.join(OUT, "full" + VN); os.makedirs(SEQ, exist_ok=True)
D1 = Image.open(os.path.join(OUT, "D1.png")).convert("RGB"); D8 = Image.open(os.path.join(OUT, "D8.png")).convert("RGB")
h1 = HEADS["D1"]; c1 = ((h1["H"][0] + h1["P1"][0]) / 2, (h1["H"][1] + h1["P1"][1]) / 2 + 0.06) if "H" in h1 and "P1" in h1 else (0.5, 0.5)
B1 = HEADS.get("D1_buds", {}).get("P1_L")
if B1: c1 = (c1[0] * 0.5 + B1[0] * 0.5, c1[1] * 0.5 + B1[1] * 0.5)
h8 = HEADS["D8"]
order = ["H", "P1"] + sorted([k for k in h8 if k not in ("H", "P1")], key=lambda k: -h8[k][2])
POP = {}
for i, k in enumerate(order):
    if k not in h8: continue
    if k == "H": POP[k] = (265.20 + D8_SHIFT, "key", C_LAV)                                 # v7：記号（○△□…）をやめ、組ごとの色の鍵。主人公＝二台の鍵の紫
    elif k == "P1": POP[k] = (266.00 + D8_SHIFT, "key", AMB_KEY)                             # 隣の人＝隣の組の鍵の橙（P17 の 2D と同じ色）
    else:
        j = i - 2; POP[k] = (269.10 + D8_SHIFT + 3.6 * j / max(1, len(order) - 3), "key", KEY_PALETTE[j % len(KEY_PALETTE)])
SFX_POP = sorted(v[0] for v in POP.values())
# 十人十色：主人公（青）→ 隣の人（黄）→ その隣（緑）→ ほかの人（ばらばらの色）
CROWD_COL = [(240, 198, 56), (70, 160, 90), (226, 120, 60), (120, 90, 170), (60, 150, 160), (200, 90, 80), (150, 110, 60), (230, 140, 180), (90, 120, 60)]
DOTS = {"H": (P[5][0] - 0.25 + 0.0, (52, 102, 210)), "P1": (at_char(5, 4), (240, 198, 56))}
others = [k for k in order if k not in ("H", "P1")]
for j, k in enumerate(others):
    DOTS[k] = ((at_char(5, 12) if j == 0 else at_char(5, 18) + 2.2 * (j - 1) / max(1, len(others) - 2)), CROWD_COL[(j + 1) % len(CROWD_COL)] if j else (70, 160, 90))
SFX_DOTS = sorted(v[0] for v in DOTS.values())


def diagram6(t):
    i = int(round((t - CH0) * FPS)) + 1; fp = os.path.join(OUT, "diagram6", "d_%04d.png" % i)
    if not os.path.exists(fp):
        for di in (-1, 1, -2, 2):
            q = os.path.join(OUT, "diagram6", "d_%04d.png" % (i + di))
            if os.path.exists(q): fp = q; break
    im = Image.open(fp).convert("RGB")
    return im if im.size == (DW, DH) else im.resize((DW, DH), Image.LANCZOS)


def pair3d(t):
    k = min(max(int(round((t - TP0) * FPS)) + 1, 1), PL["frames"])
    im = Image.open(os.path.join(PAIR_DIR, "frames", "p_%04d.png" % k)).convert("RGB")
    if im.size != (DW, DH): im = im.resize((DW, DH), Image.LANCZOS)
    pair_overlay(im, t, PL["anchors"][k - 1]); return im


def crowd(t):
    """十人十色：止まった車内の全景に、人ごとに違う色の丸"""
    im, (x0, y0, w, h) = crop_push(D8, t, SKIP[0], SKIP[1], 0.5, 0.48, 0.96); d = SD(im)
    for k, (tp, col) in DOTS.items():
        if k not in h8: continue
        u = t - tp
        if u < 0: continue
        sc = 1.0 + 0.35 * math.sin(math.pi * min(u / 0.28, 1.0)) * (1 - sm(u / 0.28))
        px = (h8[k][0] * D8.size[0] - x0) / w * W; py = (h8[k][1] * D8.size[1] - y0) / h * H
        r = max(8.0, 14.0 * (2.0 / max(h8[k][2], 1.2)) ** 0.6) * sc
        d.ellipse([px - r * 1.6, py - r * 1.6, px + r * 1.6, py + r * 1.6], fill=(250, 250, 248), outline=(205, 210, 215), width=2)
        d.ellipse([px - r, py - r, px + r, py + r], fill=col)
    return im


def make_frame(t):
    if t < T_D2:                                                          # D1：隣の人のイヤホン（「まずは、一つ目の疑問から」）
        im, (x0, y0, w, h) = crop_push(D1, t, CH0, T_D2, c1[0], c1[1], 0.86)
        if B1:
            bx = (B1[0] * D1.size[0] - x0) / w * W; by = (B1[1] * D1.size[1] - y0) / h * H; k = sm((t - CH0 - 0.35) / 0.45)
            im = spotlight(im, (bx, by), 120, k); d = SD(im)
            if k > 0:
                r = 30 + 3 * math.sin(2 * math.pi * 1.4 * (t - CH0)); d.ellipse([bx - r, by - r, bx + r, by + r], outline=AMBER, width=5)
                if sm((t - CH0 - 0.65) / 0.35) > 0:
                    lx, ly = bx + 150, by - 150; d.line([bx + 22, by - 22, lx - 60, ly + 22], fill=AMBER, width=3); tag(d, (lx, ly), "隣の人のイヤホン", AMBER)
    elif t < TP0: im = diagram6(t)
    elif t < TP1:
        if SKIP[0] <= t < SKIP[1]:
            im = crowd(t)
            for e0, e1 in ((SKIP[0], SKIP[0] + 0.3), (SKIP[1] - 0.3, SKIP[1])):
                if e0 <= t < e1:
                    u = sm((t - e0) / 0.3); im = Image.blend(pair3d(t), im, u if e0 == SKIP[0] else 1 - u)
        else:
            im = pair3d(t)
            xf = sm((t - TP0) / 0.40)
            if xf < 1: im = Image.blend(diagram6(t), im, xf)
    elif t < T_D8:
        im = diagram6(t)
        xf = sm((t - TP1) / 0.35)
        if xf < 1: im = Image.blend(pair3d(TP1 - 1.0 / FPS), im, xf)
    else:
        im, (x0, y0, w, h) = crop_push(D8, t, T_D8, CH1, 0.5, 0.48, 0.95); d = SD(im)
        for k, (tp, kind, col) in POP.items():
            u = t - tp
            if u < 0: continue
            sc = 1.0 + 0.35 * math.sin(math.pi * min(u / 0.28, 1.0)) * (1 - sm(u / 0.28))
            px = (h8[k][0] * D8.size[0] - x0) / w * W; py = (h8[k][1] * D8.size[1] - y0) / h * H
            R = max(11.0, 21.0 * (2.0 / max(h8[k][2], 1.2)) ** 0.6) * sc
            key_badge(d, (px, py), R, col, tail=R > 13.5)
    return im


MISSING = []
RNG = next(([float(x) for x in a_.split("=", 1)[1].split(":")] for a_ in sys.argv if a_.startswith("--range=")), None)   # 試し：この時刻（本編の秒）のコマだけ組む
STREAM = os.environ.get("MARU_STREAM") == "1" and not RNG     # 本番（1080p）：コマを PNG に書かず、最後に ffmpeg へ直接流す（1080p の PNG 6000枚はディスクに入らない）
for i in (range(0) if STREAM else range(N)):
    t = CH0 + i / FPS
    fp = os.path.join(SEQ, "f_%04d.png" % (i + 1))
    if os.path.exists(fp) and "--redo" not in sys.argv: continue
    if RNG and not (RNG[0] <= t < RNG[1]): continue
    T_OUT[0] = t
    try: im = make_frame(warp(t))
    except OSError: MISSING.append(i + 1); continue                     # 3D がまだ描けていないコマ（あとで同じコマンドを流すと埋まる）
    im.save(fp, compress_level=1)
print("missing 3D frames:", len(MISSING), (MISSING[0], MISSING[-1]) if MISSING else "")
if RNG: print("RANGE ONLY", RNG); sys.exit(0)



# ---------------------------------------------------------------- 字幕（台本 v2 の仮の時刻）
def ts(x):
    x = max(0.0, x); return "%d:%02d:%05.2f" % (int(x // 3600), int(x % 3600 // 60), x % 60)


def srt_lines(path):
    out = []
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        L = b.split("\n")
        if len(L) < 3 or " --> " not in L[1]: continue
        def sec(x):
            hh, mm, rr = x.strip().split(":"); s_, ms = rr.split(","); return int(hh) * 3600 + int(mm) * 60 + int(s_) + int(ms) / 1000
        a, c = L[1].split(" --> "); out.append((sec(a), sec(c), " ".join(L[2:])))
    return out


def wrap_jp(txt, maxc=27):
    if len(txt) <= maxc or "\\N" in txt: return txt
    cands = [i + 1 for i, ch in enumerate(txt) if ch in "、，,。" and 6 <= i + 1 <= len(txt) - 6]
    cut = min(cands, key=lambda i: abs(i - len(txt) / 2)) if cands else len(txt) // 2
    return txt[:cut] + "\\N" + txt[cut:]


W_ = tw.Warp(161.0, 244.7)
NAMES = [(CH0, "D1 一つ目の疑問：隣の人のイヤホン"), (T_D2, "D2 上が自分の組、下が隣の組"), (W_.new_of(168.90), "D3 電波はまわり一面に届く"),
         (W_.new_of(187.73), "D4 自分のイヤホンに、両方の荷物"), (W_.new_of(199.13), "D5 印を確かめる（○は鳴らす、△は鳴らさない）"), (W_.new_of(217.95), "D6 こちらはこちら、あちらはあちら"),
         (W_.new_of(233.59), "D7 見分ける情報"), (P[1][0] - 0.1, "P1 よく見るペアリング画面"), (TP0, "P2〜 絵の具のたとえ（3D）"), (SKIP[0], "P5 十人十色（車内）"), (SKIP[1], "P6〜 絵の具のたとえ（3D）"),
         (TP1, "P17 接続しました・鍵のない隣は開けない"), (T_D8, "D8 届くことと、再生することは別")]
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,Noto Sans CJK JP,40,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2.6,0,2,60,60,46,1",
       "Style: Shot,Noto Sans CJK JP,20,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,3,1,0,7,14,14,12,1",
       "Style: Note,Noto Sans CJK JP,18,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,3,1,0,9,14,14,12,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, txt in sorted(srt_lines(SRT)):
    if ALT624 and abs(a - P[15][0]) < 0.05: c, txt = a + ALT_LEN, ALT_TXT          # v8：6:24 は②
    elif a >= INS_T: a, c = a + DELTA, c + DELTA
    if c > CH0 and a < CH1_OUT: ass.append("Dialogue: 0,%s,%s,Sub,,0,0,0,,%s" % (ts(a - CH0), ts(min(c, CH1_OUT) - CH0), wrap_jp(txt)))
for (a, nm), (b, _) in zip(NAMES, NAMES[1:] + [(CH1, "")]):
    a, b = unwarp(a), unwarp(b)
    ass.append("Dialogue: 1,%s,%s,Shot,,0,0,0,,%s　%d:%04.1f" % (ts(a - CH0), ts(b - CH0), nm, int(a // 60), a % 60))
ass.append("Dialogue: 1,%s,%s,Note,,0,0,0,,第4章 %s（台本 v2：%d:%02d〜%d:%02d）確認用・声は Gemini（Achernar）" % (ts(0), ts(T), VER, int(CH0 // 60), int(CH0 % 60), int(CH1 // 60), int(CH1 % 60)))
if os.environ.get("MARU_FINAL") == "1": ass = [l_ for l_ in ass if ",Note,," not in l_ and ",Shot,," not in l_]   # 本番（MARU_FINAL=1）：確認用の札（場面名・注記）を出さない
open(os.path.join(OUT, "ch04_subs%s.ass" % VN), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 音（効果音だけ）
Nn = int(T * SR); rng = np.random.default_rng(4); mix = np.zeros((Nn, 2), np.float32)


def add(at, s, g=1.0, raw=False):
    if not raw: at = unwarp(at)                                           # v8：元の時刻で置いた音を、のばした分ずらす（raw は出す時刻のまま）
    i0 = int((at - CH0) * SR)
    if i0 < 0 or i0 >= Nn: return
    m = min(len(s), Nn - i0); mix[i0:i0 + m, 0] += s[:m] * g * 0.707; mix[i0:i0 + m, 1] += s[:m] * g * 0.707


def tone(fs, dur, tau, amp=1.0):
    tt = np.arange(int(dur * SR)) / SR
    return sum(np.sin(2 * math.pi * f * tt) * a for f, a in fs) * np.exp(-tt / tau) * (1 - np.exp(-tt / 0.004)) * amp


def noise(dur, tau, lp=0.0):
    x = rng.normal(0, 1, int(dur * SR)); tt = np.arange(len(x)) / SR
    if lp: k = int(SR / lp); x = np.convolve(x, np.ones(k) / k, mode="same")
    return x * np.exp(-tt / tau)


def pour_snd(dur=2.30, ramp=0.15):
    """注ぐ音（白：約2.3秒）：水のしぶきのざわめき（低めに丸めた雑音）＋小さな泡の音（高さが上がる短い音）。流れの強さと同じ台形で出入り"""
    n = int(dur * SR); tt = np.arange(n) / SR
    env = np.clip(np.minimum(tt / ramp, (dur - tt) / ramp), 0.0, 1.0)
    x = noise(dur, 1e9, 1300) * (0.75 + 0.25 * np.sin(2 * math.pi * 6.5 * tt) ** 2)
    for tb in rng.uniform(0.1, dur - 0.2, 14):
        i0 = int(tb * SR); m = int(0.05 * SR); t2 = np.arange(m) / SR; f0 = rng.uniform(380, 720)
        b = np.sin(2 * math.pi * (f0 * t2 + 0.5 * 2600 * t2 * t2)) * np.exp(-t2 / 0.015) * 0.35
        m2 = max(0, min(m, n - i0)); x[i0:i0 + m2] += b[:m2]
    return x * env * 0.11                                                # 二本同時に注ぐので、ほかの効果音と同じくらいの大きさに


SND = dict(pour=lambda: pour_snd(),
           arrive=lambda: tone([(1400, 0.5), (2100, 0.2)], 0.12, 0.025) * 0.5,
           accept=lambda: np.concatenate([tone([(880, 0.6), (1760, 0.15)], 0.12, 0.08), tone([(1320, 0.6), (2640, 0.15)], 0.5, 0.18)]) * 0.55,
           reject=lambda: (tone([(180, 0.8), (120, 0.4)], 0.35, 0.09) + noise(0.35, 0.03, 900) * 0.15) * 0.8,
           key=lambda: (tone([(3200, 0.4), (4700, 0.3), (6100, 0.2)], 0.5, 0.12)) * 0.35,
           pair=lambda: np.concatenate([tone([(660, 0.5)], 0.15, 0.1), tone([(990, 0.5)], 0.6, 0.25)]) * 0.45,
           lock=lambda: (noise(0.08, 0.006) * 0.5 + tone([(2400, 0.4)], 0.08, 0.01)) * 0.6,
           unlock=lambda: (noise(0.08, 0.006) * 0.5 + tone([(2000, 0.4)], 0.08, 0.01)) * 0.6,
           pop=lambda: tone([(520, 0.7), (1040, 0.2)], 0.18, 0.05) * 0.45,
           whoosh=lambda: noise(0.6, 0.25, 400) * np.minimum(np.arange(int(0.6 * SR)) / (0.15 * SR), 1.0) * 0.35,
           drip=lambda: tone([(1150, 0.6), (1700, 0.2)], 0.12, 0.03) * 0.4,
           clunk=lambda: (tone([(210, 0.8), (330, 0.3)], 0.16, 0.035) + noise(0.16, 0.008, 1500) * 0.2) * 0.45,
           step=lambda: (tone([(400, 0.6), (800, 0.2)], 0.06, 0.012) + noise(0.06, 0.004, 2500) * 0.15) * 0.3,
           tap=lambda: (tone([(1900, 0.5), (3100, 0.2)], 0.05, 0.008) + noise(0.05, 0.003, 4000) * 0.2) * 0.5,
           tilt=lambda: (tone([(700, 0.4), (1050, 0.2)], 0.08, 0.02) + noise(0.08, 0.01, 2500) * 0.1) * 0.35,
           slide=lambda: noise(1.2, 0.6, 1800) * np.minimum(np.arange(int(1.2 * SR)) / (0.2 * SR), 1.0) * 0.12,
           stamp=lambda: (tone([(240, 0.8)], 0.15, 0.04) + noise(0.15, 0.01, 1200) * 0.2) * 0.6)
for e in DG["events"]:
    if e["kind"] in SND and not (TP0 - 0.2 <= e["t"] < TP1): add(e["t"], SND[e["kind"]]())
for e in PL["events"]:
    if e["kind"] in SND and not (SKIP[0] <= e["t"] < SKIP[1]): add(e["t"], SND[e["kind"]]())
for t_w in (W_.new_of(168.90), W_.new_of(178.65)):
    x = noise(2.2, 0.8, 300) * np.minimum(np.arange(int(2.2 * SR)) / (0.4 * SR), 1.0) * 0.25; add(t_w, x)
for tp in SFX_POP + SFX_DOTS: add(tp, tone([(700 + 40 * (int(tp * 10) % 3), 0.6), (1400, 0.15)], 0.16, 0.04) * 0.35)
# v7：P15 の式の札（中身の丸が出る・白が二つ跳ねる・うすい紫ができる）
t15_eq, t15_w2, t15_pale = at_char(15, 16), at_char(15, 22) - 0.05, at_char(15, 31) - 0.25
if ALT624: t15_eq, t15_w2, t15_pale = alt_char(16), alt_char(32) - 0.05, alt_char(42) - 0.25    # v8：②の言葉の位置（出す時刻）
for j in range(4): add(t15_eq + 0.10 + 0.09 * j, tone([(900 + 120 * j, 0.6), (1800 + 240 * j, 0.12)], 0.09, 0.025) * 0.22, raw=ALT624)
if ALT624:
    for j in range(2): add(alt_char(22) - 0.05 + 0.12 * j, tone([(1050, 0.6), (2100, 0.12)], 0.10, 0.03) * 0.22, raw=True)   # 「青と赤は」で二つ跳ねる
for j in range(2): add(t15_w2 + 0.12 * j, tone([(1250, 0.6), (2500, 0.12)], 0.10, 0.03) * 0.25, raw=ALT624)
add(t15_pale, SND["pop"](), 0.8, raw=ALT624)
room = noise(T, 1e9, 200) * 0.004; mix[:, 0] += room[:Nn]; mix[:, 1] += room[:Nn]
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import narration as NAR                       # 声を足す（効果音は声の下。声の間は 4dB 下げる）
PLACE = None
if ALT624:                                                                # v8：67 は②（line_067_b.wav）、後ろの文は DELTA ずらす
    PLACE = json.load(open(os.path.join(NAR.D, "placement.json"), encoding="utf-8"))
    for p_ in PLACE:
        if p_["no"] == 67: p_.update(start=ALT_A, end=ALT_A + ALT_LEN, speed=1.0, wav=ALT_WAV)
        elif p_["start"] >= INS_T: p_["start"] += DELTA; p_["end"] += DELTA
mix = NAR.mix_voice(mix, CH0, SR, bus_peak=0.45, duck_db=4.0, P=PLACE)
wav = os.path.join(OUT, "ch04_audio%s.wav" % VN)
with wave.open(wav, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
mp4 = os.path.join(OUT, "ch04_%s.mp4" % VER)
if MISSING: print("3D の絵がそろっていないので、動画は書き出さない（字幕と音はできた）"); sys.exit(0)
if STREAM:
    pr_ = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (DW, DH), "-framerate", str(FPS), "-i", "-", "-i", wav,
                            "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch04_subs%s.ass" % VN), FONTS),
                            "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000",
                            "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], stdin=subprocess.PIPE)
    t_s = time.time() if "time" in globals() else None
    for i in range(N):
        t = CH0 + i / FPS; T_OUT[0] = t
        im = make_frame(warp(t)).convert("RGB")
        if im.size != (DW, DH): im = im.resize((DW, DH), Image.LANCZOS)
        pr_.stdin.write(im.tobytes())
        if i % 240 == 0: print("STREAM", i, "/", N, flush=True)
    pr_.stdin.close(); rc_ = pr_.wait()
    if rc_ != 0: sys.exit("ffmpeg failed %d" % rc_)
    print("WROTE", mp4); sys.exit(0)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(SEQ, "f_%04d.png"), "-i", wav,
                "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch04_subs%s.ass" % VN), FONTS),
                "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], check=True)
print("WROTE", mp4)
