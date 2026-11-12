# 第4章「届くことと、再生することは違う」（本編 2:41.1〜4:37.1）の確認用動画
#   D1：止まった車内の主人公と隣の人（静止画にゆっくり寄る）→ D2〜D7：図（ch04_diagram.py）→ D8：止まった車内の全景に、組ごとの別の印
#   字幕＝Codex版のナレーション（声は未収録）、カットの名前、効果音（図の出来事の時刻から合成）
# 使い方: python3 ch04_assemble.py OUT_DIR（OUT_DIR に D1.png・D8.png・ch04_heads.json・diagram/・ch04_diagram.json がある）
import sys, os, json, math, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRT = os.path.join(ROOT, "handoff", "bluetooth_handoff_restored", "bt_production_v1", "output", "bluetooth_full_native.srt")
SRT_REV = os.path.join(HERE, "..", "script", "bluetooth_full_native_rev1.srt")         # 台本を直した版（stage/script/script_fixes.json → make_srt_rev.py）
if os.path.exists(SRT_REV): SRT = SRT_REV
FONTS = os.path.join(HERE, "..", "av", "fonts")
FPS, SR, W, H = 24, 48000, 1280, 720
CH0, CH1 = 161.10, 277.10
N = int(round((CH1 - CH0) * FPS)); T = N / FPS
DG = json.load(open(os.path.join(OUT, "ch04_diagram.json"))); TD0, TD1 = DG["t0"], DG["t1"]
HEADS = json.load(open(os.path.join(OUT, "ch04_heads.json")))
# ペアリングの3D（ch04_pairing.py の連番と記録）。あれば、図の 4:04.6〜4:24.4 をこれに差し替える
PAIR_DIR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--pair=")), os.path.join(OUT, "pair"))
PL = json.load(open(os.path.join(PAIR_DIR, "pairing_log.json"))) if os.path.exists(os.path.join(PAIR_DIR, "pairing_log.json")) else None
TP0 = PL["t0"] if PL else 1e9; TP1 = (PL["t0"] + (PL["frames"] - 1) / PL["fps"]) if PL else -1e9
TEAL = (31, 94, 102); AMBER = (214, 128, 44)
JFONT = os.path.join(HERE, "..", "av", "fonts", "japanese.ttc")


def spotlight(im, c, r, k):
    """c（出力の座標）のまわり半径 r だけ明るく残し、ほかを暗くする（k＝0〜1 の強さ）"""
    if k <= 0: return im
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.45))
    dark = Image.eval(im, lambda v: int(v * (1.0 - 0.55 * k)))
    return Image.composite(im, dark, m)


def tag(d, xy, txt, col, px=34):
    """白い札に太めの文字"""
    f = ImageFont.truetype(JFONT, px); w = d.textlength(txt, font=f); x, y = xy
    d.rounded_rectangle([x - w / 2 - 16, y - px * 0.75, x + w / 2 + 16, y + px * 0.75], radius=12, fill=(250, 250, 248), outline=col, width=3)
    d.text((x, y), txt, font=f, fill=col, anchor="mm", stroke_width=1, stroke_fill=col)
PALETTE = [(92, 120, 190), (176, 84, 140), (70, 150, 90), (150, 110, 60), (120, 90, 170), (200, 90, 80), (60, 140, 160), (160, 140, 40)]
SHAPES = ["s", "d", "x", "h", "star", "o2", "t2"]


def sm(u):
    u = max(0.0, min(1.0, u)); return u * u * u * (10 - 15 * u + 6 * u * u)


def crop_push(im, t, t0, t1, cx, cy, z1=0.94):
    """静止画にゆっくり寄る（t0〜t1 で 1.0 → z1 倍の範囲。中心は (cx, cy)＝0〜1）"""
    Wi, Hi = im.size; z = 1.0 + (z1 - 1.0) * sm((t - t0) / (t1 - t0))
    w, h = Wi * z, Hi * z; x0 = min(max(cx * Wi - w / 2, 0), Wi - w); y0 = min(max(cy * Hi - h / 2, 0), Hi - h)
    return im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h)), (x0, y0, w, h)


def draw_mark(d, c, kind, r, col, width):
    x, y = c
    if kind in ("o", "o2"):
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=width)
        if kind == "o2": d.ellipse([x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45], fill=col)
    elif kind in ("t", "t2"):
        sgn = 1 if kind == "t" else -1
        pts = [(x, y - sgn * r * 1.15), (x - r * 1.05, y + sgn * r * 0.75), (x + r * 1.05, y + sgn * r * 0.75)]
        d.polygon(pts, outline=col, width=width)
    elif kind == "s": d.rectangle([x - r * 0.9, y - r * 0.9, x + r * 0.9, y + r * 0.9], outline=col, width=width)
    elif kind == "d": d.polygon([(x, y - r * 1.2), (x + r, y), (x, y + r * 1.2), (x - r, y)], outline=col, width=width)
    elif kind == "x":
        d.line([x - r, y, x + r, y], fill=col, width=width + 1); d.line([x, y - r, x, y + r], fill=col, width=width + 1)
    elif kind == "h": d.polygon([(x + r * math.cos(a), y + r * math.sin(a)) for a in [math.pi / 6 + k * math.pi / 3 for k in range(6)]], outline=col, width=width)
    else:
        pts = [(x + (r if k % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + k * math.pi / 5), y + (r if k % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
        d.polygon(pts, outline=col, width=width)


# ---------------------------------------------------------------- ペアリングの3Dに重ねる言葉（3Dの点の画面の位置に合わせる）
LAB_COL = dict(teal=(31, 94, 102), ink=(40, 46, 52), amber=(214, 128, 44), key=(118, 92, 170))


def pair_overlay(im, t, anc):
    if not PL: return
    T_ = PL["times"]; d = ImageDraw.Draw(im)
    def at(nm_, dx=0, dy=0):
        a = anc.get(nm_)
        if not a or a[2] <= 0 or not (0.02 < a[0] < 0.98 and 0.02 < a[1] < 0.98): return None
        return (a[0] * W + dx, a[1] * H + dy)
    def lab(txt, xy, col, t0, t1, px=30):
        if xy is None: return
        a = sm((t - t0) / 0.3) * (1 - sm((t - t1) / 0.3))
        if a <= 0.02: return
        f = ImageFont.truetype(JFONT, px); w_ = d.textlength(txt, font=f); x, y = xy
        x = min(max(x, w_ / 2 + 20), W - w_ / 2 - 20); y = min(max(y, 78), H - 170)          # 上の端の注記と重ならない
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); al = int(255 * a)
        od.rounded_rectangle([x - w_ / 2 - 14, y - px * 0.72, x + w_ / 2 + 14, y + px * 0.72], radius=12, fill=(250, 250, 248, int(235 * a)), outline=col + (al,), width=3)
        od.text((x, y), txt, font=f, fill=col + (al,), anchor="mm", stroke_width=1, stroke_fill=col + (al,))
        im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))
    G = PL.get("g0") or dict(white=245.40, secret1=246.55, load_p=247.60); LK = T_.get("lock") or {k_: T_["key"][k_] + 0.8 for k_ in ("P", "E")}
    SHOT = {n_: a_ for a_, n_ in PL.get("shots", [])}
    # 名札：最初の全景は巨大な物の上、イヤホンの台・スマホの台に寄ったときは台の上（どちらの台か、いつでも分かる）
    for k_, nm_ in (("P", "スマホ"), ("E", "イヤホン")):
        lab(nm_, at("dev" + k_, 0, -16), LAB_COL["teal"], TP0 - 0.3, G["load_p"] - 0.15, 30)
    if "S3" in SHOT: lab("イヤホン", at("tagE"), LAB_COL["teal"], SHOT["S3"] + 0.05, SHOT["S3"] + 1.6, 30)
    if "S5" in SHOT: lab("スマホ", at("tagP"), LAB_COL["teal"], SHOT["S5"] + 0.05, SHOT["S5"] + 1.6, 30)
    lab("みんなが知っている色", at("tank", 0, 62), LAB_COL["ink"], G["white"] + 0.05, G["white"] + 1.45)   # 名札（巨大な二台の上）より下に
    for k in ("P", "E"):
        lab("ひみつの色", at("jar" + k, 0, -24), LAB_COL["ink"], G["secret1"] - 0.1, G["secret1"] + 1.15)
        t2 = T_["pour"]["secret" + k]; lab("ひみつの色", at("jar" + k, 0, -24), LAB_COL["ink"], t2 - 0.25, t2 + 0.95)
    t_go = PL.get("t_go", 249.0); t_a, t_b = t_go + 1.25, SHOT.get("S3", t_go + 2.8) - 0.05        # 「電波で運ぶのは、混ぜた色だけ」に合わせる
    nbh = at("nb")                                                         # 隣のイヤホンの頭の上 → 頭の真ん中を橙の輪で囲み、札は左下に離して線でつなぐ
    a_nb = sm((t - t_a) / 0.3) * (1 - sm((t - t_b) / 0.3))
    if nbh and a_nb > 0.02:
        cx_, cy_ = nbh[0], nbh[1] + 32; r_ = 44 + 3 * math.sin(2 * math.pi * 1.4 * (t - t_a))
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); al = int(255 * a_nb)
        od.ellipse([cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_], outline=LAB_COL["amber"] + (al,), width=4)
        lx_, ly_ = cx_ - 250, cy_ + 120
        od.line([cx_ - r_ * 0.72, cy_ + r_ * 0.72, lx_ + 150, ly_ - 18], fill=LAB_COL["amber"] + (al,), width=3)
        im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))
        lab("見えても、同じ色は作れない", (lx_, ly_), LAB_COL["amber"], t_a, t_b)
    lab("次からは自動でつながる", at("holeE", 0, -26), LAB_COL["key"], LK["E"] + 0.10, LK["E"] + 1.10)
    kp_, ke_ = at("keyP"), at("keyE")                                     # 二つの鍵の下の真ん中（どちらも指せる所）
    mid = ((kp_[0] + ke_[0]) / 2, max(kp_[1], ke_[1]) + 92) if kp_ and ke_ else (W / 2, H - 205)
    lab("同じ色の鍵ができた", mid, LAB_COL["key"], LK["P"] + 0.10, 264.6, 34)
    a = sm((t - 262.40) / 0.35) * (1 - sm((t - 264.2) / 0.2))
    if a > 0.02:                                                           # まとめ：運んだのは混ぜた色だけ・鍵は二台がそれぞれ作る
        f = ImageFont.truetype(JFONT, 28); ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); al = int(255 * a)
        x0_, y0_ = W - 470, 24
        od.rounded_rectangle([x0_, y0_, W - 24, y0_ + 116], radius=16, fill=(250, 250, 248, int(235 * a)), outline=(205, 210, 215, al), width=2)
        od.text((x0_ + 24, y0_ + 36), "運んだのは、混ぜた色だけ", font=f, fill=LAB_COL["ink"] + (al,), anchor="lm", stroke_width=1, stroke_fill=LAB_COL["ink"] + (al,))
        od.text((x0_ + 24, y0_ + 82), "鍵は、二台がそれぞれ作る", font=f, fill=LAB_COL["key"] + (al,), anchor="lm", stroke_width=1, stroke_fill=LAB_COL["key"] + (al,))
        im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))


def caption(im, t, txt, t0, t1, px=34):
    """画面の上の真ん中の一言（2D と 3D にまたがる）"""
    a = sm((t - t0) / 0.3) * (1 - sm((t - t1) / 0.3))
    if a <= 0.02: return
    f = ImageFont.truetype(JFONT, px); d0 = ImageDraw.Draw(im); w_ = d0.textlength(txt, font=f); x, y = W / 2, 62
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); al = int(255 * a)
    od.rounded_rectangle([x - w_ / 2 - 22, y - px * 0.85, x + w_ / 2 + 22, y + px * 0.85], radius=16, fill=(40, 46, 52, int(225 * a)))
    od.text((x, y), txt, font=f, fill=(255, 255, 255, al), anchor="mm", stroke_width=1, stroke_fill=(255, 255, 255, al))
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))


# ---------------------------------------------------------------- 絵
SEQ = os.path.join(OUT, "full"); os.makedirs(SEQ, exist_ok=True)
D1 = Image.open(os.path.join(OUT, "D1.png")).convert("RGB"); D8 = Image.open(os.path.join(OUT, "D8.png")).convert("RGB")
h1 = HEADS["D1"]; c1 = ((h1["H"][0] + h1["P1"][0]) / 2, (h1["H"][1] + h1["P1"][1]) / 2 + 0.06) if "H" in h1 and "P1" in h1 else (0.5, 0.5)
B1 = HEADS.get("D1_buds", {}).get("P1_L")                                  # 隣の人のイヤホン（主人公の側の耳）
if B1: c1 = (c1[0] * 0.5 + B1[0] * 0.5, c1[1] * 0.5 + B1[1] * 0.5)        # そちらへ寄る
h8 = HEADS["D8"]
order = ["H", "P1"] + sorted([k for k in h8 if k not in ("H", "P1")], key=lambda k: -h8[k][2])     # 主人公・隣の人 → 遠い組から
POP = {}
for i, k in enumerate(order):
    if k not in h8: continue
    if k == "H": POP[k] = (265.20, "o", TEAL)
    elif k == "P1": POP[k] = (266.00, "t", AMBER)
    else:
        j = i - 2; POP[k] = (269.10 + 3.6 * j / max(1, len(order) - 3), SHAPES[j % len(SHAPES)], PALETTE[j % len(PALETTE)])
SFX_POP = sorted(v[0] for v in POP.values())
for i in range(N):
    t = CH0 + i / FPS
    if os.path.exists(os.path.join(SEQ, "f_%04d.png" % (i + 1))) and "--redo" not in sys.argv: continue
    if t < TD0:
        im, (x0, y0, w, h) = crop_push(D1, t, CH0, TD0, c1[0], c1[1], 0.86)
        if B1:                                                             # 隣の人のイヤホンを目立たせる：まわりを暗く・隣の組の色の輪・札
            bx = (B1[0] * D1.size[0] - x0) / w * W; by = (B1[1] * D1.size[1] - y0) / h * H
            k = sm((t - 161.45) / 0.45)
            im = spotlight(im, (bx, by), 120, k)
            d = ImageDraw.Draw(im)
            if k > 0:
                r = 30 + 3 * math.sin(2 * math.pi * 1.4 * (t - 161.45))
                d.ellipse([bx - r, by - r, bx + r, by + r], outline=AMBER, width=5)
                u = ((t - 161.45) % 0.9) / 0.9; rr_ = 32 + 40 * u; a = int(255 * (1 - u) * k)
                ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).ellipse([bx - rr_, by - rr_, bx + rr_, by + rr_], outline=AMBER + (a,), width=3)
                im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(im)
                ta = sm((t - 161.75) / 0.35)
                if ta > 0:
                    lx, ly = bx + 150, by - 150
                    d.line([bx + 22, by - 22, lx - 60, ly + 22], fill=AMBER, width=3)
                    tag(d, (lx, ly), "隣の人のイヤホン", AMBER)
    elif TP0 - 1e-6 <= t < TD1 and PL:
        k = min(int(round((t - TP0) * FPS)) + 1, PL["frames"]); im = Image.open(os.path.join(PAIR_DIR, "frames", "p_%04d.png" % k)).convert("RGB").resize((W, H), Image.LANCZOS)
        xf = sm((t - TP0) / 0.40)
        if xf < 1:                                                         # 図（よく見るペアリングの画面から寄ってきた二台）→ 3D
            kd = min(int(round((t - TD0) * FPS)) + 1, DG["frames"]); imd = Image.open(os.path.join(OUT, "diagram", "d_%04d.png" % kd)).convert("RGB")
            im = Image.blend(imd, im, xf)
        pair_overlay(im, t, PL["anchors"][k - 1])
    elif t < TD1:
        k = min(int(round((t - TD0) * FPS)) + 1, DG["frames"]); im = Image.open(os.path.join(OUT, "diagram", "d_%04d.png" % k)).convert("RGB")
    else:
        im, (x0, y0, w, h) = crop_push(D8, t, TD1, CH1, 0.5, 0.48, 0.95)
        d = ImageDraw.Draw(im)
        for k, (tp, kind, col) in POP.items():
            u = t - tp
            if u < 0: continue
            sc = 1.0 + 0.35 * math.sin(math.pi * min(u / 0.28, 1.0)) * (1 - sm(u / 0.28))                # はねて出る
            px = (h8[k][0] * D8.size[0] - x0) / w * W; py = (h8[k][1] * D8.size[1] - y0) / h * H
            r = max(7.0, 13.0 * (2.0 / max(h8[k][2], 1.2)) ** 0.6) * sc
            bg = (250, 250, 248)
            d.ellipse([px - r * 1.7, py - r * 1.7, px + r * 1.7, py + r * 1.7], fill=bg, outline=(205, 210, 215), width=2)
            draw_mark(d, (px, py), kind, r, col, max(2, int(r / 4.5)))
    if 246.85 <= t < 249.1: caption(im, t, "中で起きていることを、絵の具でたとえると…", 246.95, 248.85)   # 2D と 3D にまたがる一言
    im.save(os.path.join(SEQ, "f_%04d.png" % (i + 1)), compress_level=1)


# ---------------------------------------------------------------- 字幕
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
    """長い1行を、真ん中に近い読点（、）で2行に分ける（ASS の改行 \\N）"""
    if len(txt) <= maxc or "\\N" in txt: return txt
    cands = [i + 1 for i, ch in enumerate(txt) if ch in "、，," and 6 <= i + 1 <= len(txt) - 6]
    if not cands: cut = len(txt) // 2
    else: cut = min(cands, key=lambda i: abs(i - len(txt) / 2))
    return txt[:cut] + "\\N" + txt[cut:]


NAMES = [(161.10, "D1 では、隣の人のイヤホンが近くにあったら？"), (165.10, "D2 上が自分の組、下が隣の組"), (168.90, "D3 電波はまわり一面に届く"),
         (187.73, "D4 自分のイヤホンに、両方の荷物"), (199.13, "D5 印を確かめる（○は鳴らす、△は鳴らさない）"), (217.95, "D6 こちらはこちら、あちらはあちら"),
         (233.59, "D7 見分ける情報・ペアリング・鍵"), (264.40, "D8 届くことと、再生することは別")]
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,Noto Sans CJK JP,40,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2.6,0,2,60,60,46,1",
       "Style: Shot,Noto Sans CJK JP,20,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,3,1,0,7,14,14,12,1",
       "Style: Note,Noto Sans CJK JP,18,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,3,1,0,9,14,14,12,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
EXTRA = []                                                                   # v4：足していた一文は、直した台本（電波で運ぶのは、混ぜた色だけ）に入れた
for a, c, txt in sorted(srt_lines(SRT) + EXTRA):
    if c > CH0 and a < CH1: ass.append("Dialogue: 0,%s,%s,Sub,,0,0,0,,%s" % (ts(a - CH0), ts(min(c, CH1) - CH0), wrap_jp(txt)))
for (a, nm), (b, _) in zip(NAMES, NAMES[1:] + [(CH1, "")]):
    ass.append("Dialogue: 1,%s,%s,Shot,,0,0,0,,%s　%d:%04.1f" % (ts(a - CH0), ts(b - CH0), nm, int(a // 60), a % 60))
ass.append("Dialogue: 1,%s,%s,Note,,0,0,0,,第4章（2:41〜4:37）確認用・図はA案・声は未収録" % (ts(0), ts(T)))
open(os.path.join(OUT, "ch04_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 音（効果音だけ。止まった車内はほぼ無音）
Nn = int(T * SR); rng = np.random.default_rng(4); mix = np.zeros((Nn, 2), np.float32)


def add(at, s, g=1.0, pan=0.0):
    i0 = int((at - CH0) * SR)
    if i0 < 0 or i0 >= Nn: return
    m = min(len(s), Nn - i0); l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    mix[i0:i0 + m, 0] += s[:m] * g * l; mix[i0:i0 + m, 1] += s[:m] * g * r


def tone(fs, dur, tau, amp=1.0):
    tt = np.arange(int(dur * SR)) / SR
    return sum(np.sin(2 * math.pi * f * tt) * a for f, a in fs) * np.exp(-tt / tau) * (1 - np.exp(-tt / 0.004)) * amp


def noise(dur, tau, lp=0.0):
    x = rng.normal(0, 1, int(dur * SR)); tt = np.arange(len(x)) / SR
    if lp: k = int(SR / lp); x = np.convolve(x, np.ones(k) / k, mode="same")
    return x * np.exp(-tt / tau)


SND = dict(arrive=lambda: tone([(1400, 0.5), (2100, 0.2)], 0.12, 0.025) * 0.5,
           accept=lambda: np.concatenate([tone([(880, 0.6), (1760, 0.15)], 0.12, 0.08), tone([(1320, 0.6), (2640, 0.15)], 0.5, 0.18)]) * 0.55,
           reject=lambda: (tone([(180, 0.8), (120, 0.4)], 0.35, 0.09) + noise(0.35, 0.03, 900) * 0.15) * 0.8,
           key=lambda: (tone([(3200, 0.4), (4700, 0.3), (6100, 0.2)], 0.5, 0.12)) * 0.35,
           pair=lambda: np.concatenate([tone([(660, 0.5)], 0.15, 0.1), tone([(990, 0.5)], 0.6, 0.25)]) * 0.45,
           lock=lambda: (noise(0.08, 0.006) * 0.5 + tone([(2400, 0.4)], 0.08, 0.01)) * 0.6,
           unlock=lambda: (noise(0.08, 0.006) * 0.5 + tone([(2000, 0.4)], 0.08, 0.01)) * 0.6,
           pop=lambda: tone([(520, 0.7), (1040, 0.2)], 0.18, 0.05) * 0.45,
           whoosh=lambda: noise(0.6, 0.25, 400) * np.minimum(np.arange(int(0.6 * SR)) / (0.15 * SR), 1.0) * 0.35,
           drip=lambda: tone([(1150, 0.6), (1700, 0.2)], 0.12, 0.03) * 0.4,
           clunk=lambda: (tone([(210, 0.8), (330, 0.3)], 0.16, 0.035) + noise(0.16, 0.008, 1500) * 0.2) * 0.55,
           step=lambda: (tone([(400, 0.6), (800, 0.2)], 0.06, 0.012) + noise(0.06, 0.004, 2500) * 0.15) * 0.3,
           tap=lambda: (tone([(1900, 0.5), (3100, 0.2)], 0.05, 0.008) + noise(0.05, 0.003, 4000) * 0.2) * 0.5, stamp=lambda: (tone([(240, 0.8)], 0.15, 0.04) + noise(0.15, 0.01, 1200) * 0.2) * 0.6)
for e in DG["events"]:
    if e["kind"] in SND and not (PL and TP0 - 0.2 <= e["t"] < TD1): add(e["t"], SND[e["kind"]]())     # 3D の間は、図の効果音は使わない
if PL:
    for e in PL["events"]:
        if e["kind"] in SND: add(e["t"], SND[e["kind"]]())
for t_w in (168.90, 178.65):                                                 # 電波：やわらかい風の音（広がり始め）
    x = noise(2.2, 0.8, 300) * np.minimum(np.arange(int(2.2 * SR)) / (0.4 * SR), 1.0) * 0.25; add(t_w, x)
for tp in SFX_POP: add(tp, tone([(700 + 40 * (tp % 3), 0.6), (1400, 0.15)], 0.16, 0.04) * 0.35)
room = noise(T, 1e9, 200) * 0.004; mix[:, 0] += room[:Nn]; mix[:, 1] += room[:Nn]
mix /= max(np.abs(mix).max(), 1e-6) / 0.85
wav = os.path.join(OUT, "ch04_audio.wav")
with wave.open(wav, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
mp4 = os.path.join(OUT, "ch04_animatic.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(SEQ, "f_%04d.png"), "-i", wav,
                "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch04_subs.ass"), FONTS),
                "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], check=True)
print("WROTE", mp4)
