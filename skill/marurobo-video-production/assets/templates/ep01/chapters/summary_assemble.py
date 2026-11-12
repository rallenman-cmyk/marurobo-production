# まとめ（本編 17:04.9〜18:15、台本の 179〜189）の組み立て
#   前半（2D・〜17:58.7）：これまでの章の本番の絵を並べ、二つの疑問の答えと三つの工夫をふり返る（札の文字は絵コンテより大きく）
#   後半（3D・17:58.7〜）：止まった電車に戻り、まるロボが時間を元に戻す（summary_seq.py の連番）
#   音：前半は第3章からの曲（8拍のくり返し）を小さく敷く。後半は、止まった世界の静けさ → 動き出す（電車の音と曲が、テープが回り出すように戻る）
#       → M10 は主人公の耳の中（サビ）→ M11 は隣の人から聞こえる小さな音漏れ（第1章 K8 と同じ）
# 使い方: python3 summary_assemble.py OUT_DIR --frames3d DIR [--log summary_log.json] [--assets DIR] [--still 秒,秒,…]
#   DIR/f_NNNN.png：summary_seq.py の連番（番号はその台本のコマ番号 1945〜2340。大きさは何でもよい）
#   MARU_OUTW：出す幅（既定 1280。本番は 1920）、MARU_FINAL=1：確認用の札（場面名・注記）を出さない、MARU_CRF：画質（既定 20）
import sys, os, json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import overlay2d as O2, ch07_plan as p7
SC = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(SC, "tools")); import narration as NAR


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
FR3 = opt("--frames3d"); ASSETS = opt("--assets", os.path.join(SC, "work_sum", "assets"))
LOG = json.load(open(opt("--log", os.path.join(FR3 or OUT, "..", "summary_log.json")), encoding="utf-8"))
FPS, SR = 24, 48000
RW = int(os.environ.get("MARU_OUTW", "1280")); RH = RW * 9 // 16; k = RW / 1920.0          # 図は 1920×1080 の目盛りで描く
FINAL = os.environ.get("MARU_FINAL") == "1"
FONTS = os.path.join(HERE, "..", "av", "fonts"); FONT_J = os.path.join(FONTS, "japanese.ttc")
SRT = os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")
SONG = os.path.join(HERE, "..", "human", "audio", "song_mono.wav")
def L(n): return p7.L(n)
def LE(n): return p7.LE(n)
def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)
def sm(u): u = clamp(u); return u * u * (3 - 2 * u)
def mj(t, t0, d): u = clamp((t - t0) / d); return u * u * u * (10 - 15 * u + 6 * u * u)

# ---------------------------------------------------------------- 時刻（本編の秒）
T_S0 = L(179) - 0.3                                   # 第8章の終わり（ch08_assemble.py の T_END と同じ）
EP0 = LOG["ep0"]; T2 = LOG["t2"]                      # 3D の頭（「お待たせしました。」）＝ summary_seq.py の 81.0 秒
D3 = 16.25                                            # 3D の長さ（声の終わり 14.86 秒のあと、決めポーズのまま 1.4 秒）
T_END = EP0 + D3
N = int(round((T_END - T_S0) * FPS)); T = N / FPS
def ep_of_scene(ts): return EP0 + (ts - T2)           # summary_seq.py の秒 → 本編の秒
T_UNF = ep_of_scene(LOG["t_unfreeze"]); T_LAND2 = ep_of_scene(LOG["t_land2"]); T_M10 = ep_of_scene(LOG["t_m10"]); T_M11 = ep_of_scene(LOG["t_m11"])
B1, B2, B3, B4, B5, B6 = L(180), L(181), L(182), L(183), L(184), L(185)    # 前半の札の切り替え（声の頭）


def at(n, word):
    """声 n の中で、word が言われるおよその時刻（文字の位置で割る）"""
    txt = NAR_TEXT[n]; a, b = L(n), LE(n)
    return a + (b - a) * txt.index(word) / len(txt)


NAR_TEXT = {p["no"]: p["text"] for p in json.load(open(os.path.join(HERE, "..", "voice", "achernar", "placement.json"), encoding="utf-8"))}

# ---------------------------------------------------------------- 色・文字
TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY, PUR, BG = (31, 94, 102), (52, 168, 96), (214, 64, 60), (214, 128, 44), (40, 46, 52), (250, 250, 248), (130, 138, 146), (118, 92, 170), (238, 242, 245)
_fc = {}
def F(px):
    s = max(8, int(round(px * k)))
    if s not in _fc: _fc[s] = ImageFont.truetype(FONT_J, s)
    return _fc[s]
def P(*xy): return [v * k for v in xy]


def tag(d, xy, txt, col, px, lw=4, fill=WHITE):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * k, xy[1] * k; pad = 0.55 * px * k
    d.rounded_rectangle([x - w / 2 - pad, y - px * 0.82 * k, x + w / 2 + pad, y + px * 0.82 * k], radius=0.42 * px * k, fill=fill, outline=col, width=max(1, int(lw * k)))
    d.text((x, y), txt, font=f, fill=col, anchor="mm")


def check(d, xy, col, r=40):
    x, y = xy
    d.ellipse(P(x - r, y - r, x + r, y + r), fill=col)
    d.line(P(x - r * .45, y + r * .02, x - r * .1, y + r * .36, x + r * .5, y - r * .34), fill=WHITE, width=max(2, int(r * .22 * k)), joint="curve")


def note(d, xy, col, s=3.2):
    x, y = xy
    d.ellipse(P(x - 7 * s, y + 5 * s, x + 4 * s, y + 14 * s), fill=col)
    d.line(P(x + 3 * s, y + 9 * s, x + 3 * s, y - 13 * s), fill=col, width=max(1, int(2.6 * s * k)))
    d.line(P(x + 3 * s, y - 13 * s, x + 12 * s, y - 8 * s), fill=col, width=max(1, int(2.6 * s * k)))


def layer(base, a, fn):
    """透明な層に fn で描き、濃さ a で重ねる"""
    if a <= 0.003: return base
    Ly = Image.new("RGBA", base.size, (0, 0, 0, 0)); fn(ImageDraw.Draw(Ly))
    if a < 0.999: Ly.putalpha(Ly.getchannel("A").point(lambda v: int(v * a)))
    return Image.alpha_composite(base, Ly)


# ---------------------------------------------------------------- 絵（これまでの章の本番の絵。字幕なし）
_img = {}
CROP = {"c4_pair.png": (300, 220, 1660, 985), "c5_drop.png": (120, 100, 1800, 1045), "c5_hop.png": (150, 120, 1770, 1031)}   # 図がまばらなものは中身へ寄せる（16:9）
def src(name, size=None):
    key = (name, size)
    if key not in _img:
        im = Image.open(os.path.join(ASSETS, name)).convert("RGB")
        if name in CROP and size is not None: im = im.resize((1920, 1080), Image.LANCZOS).crop(CROP[name])
        _img[key] = im.resize(size or (RW, RH), Image.LANCZOS)
    return _img[key]


SHOW_CH = False                                                                  # 2026-11-09 ユーザー：札の上の「第4章」「第5章」などの章の表示は出さない


def card(base, name, box, title, col, a, px=56):
    """name の絵を box（1920 目盛りの x0,y0,x1,y1）に入れ、色の枠と上の見出し。a：出方（0→1。下から少し上がりながら）"""
    if a <= 0.003: return base
    x0, y0, x1, y1 = box; dy = 26 * (1 - sm(a))
    w, h = int(round((x1 - x0) * k)), int(round((y1 - y0) * k))
    Ly = Image.new("RGBA", base.size, (0, 0, 0, 0)); Ly.paste(src(name, (w, h)), (int(round(x0 * k)), int(round((y0 + dy) * k))))
    d = ImageDraw.Draw(Ly); d.rectangle(P(x0, y0 + dy, x1, y1 + dy), outline=col, width=max(2, int(6 * k)))
    if title and SHOW_CH: tag(d, ((x0 + x1) / 2, y0 + dy - 0.86 * px - 4), title, col, px)
    if a < 0.999: Ly.putalpha(Ly.getchannel("A").point(lambda v: int(v * sm(a))))
    return Image.alpha_composite(base, Ly)


Q1, Q2 = (92, 170, 928, 838), (992, 170, 1828, 838)      # 「二つの疑問」の画の ① と ② の札（1920 目盛り）


QDY = 30                                                                         # 2026-11-09：字幕が大きくなったので、二つの疑問の画を 30px 上へ（1080p の目盛り）


def _up(im, dy):
    if dy <= 0: return im
    out = Image.new("RGBA", im.size, BG + (255,)); out.paste(im.crop((0, dy, im.size[0], im.size[1])), (0, 0)); return out


def questions(t, focus):
    """二つの疑問の画。focus：0＝そのまま、1＝① を強く（② を薄く）、2＝② を強く（① を薄く）"""
    base = _up(src("q.png").convert("RGBA"), int(round(QDY * k)))
    if focus == 0: return base
    t0 = B1 if focus == 1 else B3; u = mj(t, t0 + 0.05, 0.45)
    keep, dim = (Q1, Q2) if focus == 1 else (Q2, Q1); col = TEAL if focus == 1 else AMBER
    keep, dim = (keep[0], keep[1] - QDY, keep[2], keep[3] - QDY), (dim[0], dim[1] - QDY, dim[2], dim[3] - QDY)
    def f(d):
        d.rounded_rectangle(P(*dim), radius=26 * k, fill=BG + (int(205 * u),))
        d.rounded_rectangle(P(keep[0] - 8, keep[1] - 8, keep[2] + 8, keep[3] + 8), radius=32 * k, outline=col + (int(255 * u),), width=max(2, int(8 * k)))
    base = layer(base, 1.0, f)
    cx, cy = (dim[0] + dim[2]) / 2, (dim[1] + dim[3]) / 2
    return base                                                                  # 強めるのは枠と薄さだけ（「まずは ①」などの文字は字幕と同じなので出さない）


def panel(t):
    """前半（2D）の一コマ（RGBA）"""
    if t < B1: return questions(t, 0)
    if t < B2: return questions(t, 1)
    if t < B3:                                                                   # ① の答え（2026-11-09：字幕が大きくなったので、絵と札を 60px 上へ）
        im = Image.new("RGBA", (RW, RH), BG + (255,))
        im = card(im, "c4_pair.png", (90, 176, 930, 648), "第4章", TEAL, mj(t, at(181, "イヤホンが") - 0.1, 0.45))
        im = card(im, "c4_keys.png", (990, 176, 1830, 648), "第4章", PUR, mj(t, at(181, "さらに"), 0.45))
        ta = at(181, "音楽に") + 0.2
        im = layer(im, mj(t, ta, 0.35), lambda d: tag(d, (1010, 752), "① の答え", TEAL, 66, lw=5))
        return layer(im, mj(t, ta + 0.25, 0.25), lambda d: check(d, (1240, 752), GREEN, 44))
    if t < B4: return questions(t, 2)
    if t < B5:                                                                   # ② の答え
        im = Image.new("RGBA", (RW, RH), BG + (255,))
        im = card(im, "c5_drop.png", (90, 176, 930, 648), "第5章", RED, mj(t, at(183, "ほかの") - 0.1, 0.45))
        im = card(im, "c7_3290.png", (990, 176, 1830, 648), "第7章", RED, mj(t, at(183, "次に"), 0.45))
        ta = at(183, "間に合わなく") + 0.3
        im = layer(im, mj(t, ta, 0.35), lambda d: tag(d, (1010, 752), "② の答え", AMBER, 66, lw=5))
        return layer(im, mj(t, ta + 0.25, 0.25), lambda d: check(d, (1240, 752), AMBER, 44))
    if t < B6:                                                                   # 三つの工夫
        im = Image.new("RGBA", (RW, RH), BG + (255,))
        im = layer(im, mj(t, B5 + 0.1, 0.4), lambda d: tag(d, (960, 138), "途切れないための三つの工夫", INK, 72, lw=5))
        for name, box, ttl, col, word in (("c5_hop.png", (45, 330, 635, 662), "第5章", TEAL, "使う周波数"),
                                          ("c6_930.png", (665, 330, 1255, 662), "第6章", AMBER, "届かなかった"),
                                          ("c7_2040.png", (1285, 330, 1875, 662), "第7章", GREEN, "先に届いた")):
            im = card(im, name, box, ttl, col, mj(t, at(184, word) - 0.1, 0.45), px=56)
        return im
    # その工夫が積み重なって、いつもの一曲が続いている（第3章の舞台：受付ボックスから曲が流れている。ゆっくり寄る）
    u = clamp((t - B6) / (EP0 - B6)); z = 1.0 + 0.05 * sm(u)
    s = src("c3_1244.png"); w, h = s.size; cw, ch_ = w / z, h / z; cx, cy = min(max(w * 0.56, cw / 2), w - cw / 2), min(max(h * 0.47, ch_ / 2), h - ch_ / 2)
    im = s.crop((int(cx - cw / 2), int(cy - ch_ / 2), int(cx + cw / 2), int(cy + ch_ / 2))).resize((RW, RH), Image.LANCZOS).convert("RGBA")
    for j, (x0_, ph) in enumerate(((1330, 0.0), (1430, 0.55), (1385, 1.1))):        # 音符：ボックスの上から、ゆっくり上へ
        for rep in range(4):
            tn = t - (B6 + 0.4 + ph + 1.65 * rep)
            if 0 <= tn <= 1.8:
                a_ = clamp(tn / 0.3) * clamp((1.8 - tn) / 0.5)
                im = layer(im, a_, lambda d, x0_=x0_, tn=tn, j=j: note(d, (x0_ + 18 * math.sin(tn * 2.2 + j), 230 - 120 * tn), TEAL, 3.0))
    return im


sys.path.insert(0, os.path.join(SC, "tools")); import cutfix                   # 2026-11-09：カットのつなぎ目 2 コマのブレ（カメラが飛ぶ分のモーションブラー）を、となりのコマに差し替える
REMAP3 = {}                                                                      # ユーザー（11/9）：同じ場面でカメラを振っているのは分かるので、まとめのカットはそのまま（直すときは下の行を使う）
# REMAP3 = cutfix.remap(lambda i: os.path.join(FR3, "f_%04d.png" % i), [int(round((T2 + s_) * FPS)) for s_, _ in LOG["shots"][1:]]) if FR3 else {}


def frame3d(t):
    f = int(round((T2 + (t - EP0)) * FPS)) + 1
    f = REMAP3.get(f, f)
    for df in (0, -1, 1, -2, 2):
        p_ = os.path.join(FR3, "f_%04d.png" % (f + df))
        if os.path.exists(p_) and os.path.getsize(p_) > 1000: break
    im = Image.open(p_).convert("RGB")
    if im.size != (RW, RH): im = im.resize((RW, RH), Image.LANCZOS)
    g = clamp((T_END - t) / 0.6)                                                 # 終わり：0.6 秒で暗くする
    if g < 1.0: im = Image.blend(Image.new("RGB", (RW, RH), (0, 0, 0)), im, sm(g))
    return im


XF = 0.30                                                                        # 札の切り替え：0.3 秒で重ねる（同じ「二つの疑問」の画どうしは重ねなくても続く）
def frame(t):
    if t >= EP0: return frame3d(t)
    for b in (B2, B4, B5, B6):
        if b - XF / 2 <= t < b + XF / 2:
            u = sm((t - (b - XF / 2)) / XF)
            return Image.blend(panel(b - XF / 2 - 1e-3).convert("RGB"), panel(max(t, b)).convert("RGB"), u)
    im = panel(t).convert("RGB")
    if t < T_S0 + 0.25: im = Image.blend(src("q.png"), im, 1.0)                  # 頭は第8章の塔の画からの切り替え（そのまま）
    return im


# ---------------------------------------------------------------- 字幕と場面名（ASS）
SH = [(T_S0, "P1 二つの疑問"), (B1, "P2 一つ目の疑問"), (B2, "P3 ① の答え（第4章）"), (B3, "P4 二つ目の疑問"), (B4, "P5 ② の答え（第5・7章）"),
      (B5, "P6 三つの工夫（第5・6・7章）"), (B6, "P7 いつもの一曲（第3章）")]
NM3 = {"M8": "M8 止まった電車", "M9": "M9 ボタンをもう一度：時間が動き出す", "M10": "M10 まだこの曲（サビ）", "M11": "M11 まわりがちらっと見る"}
SH += [(ep_of_scene(T2 + s_), NM3.get(n_, n_)) for s_, n_ in LOG["shots"]]
ass = list(O2.ASS_HEAD)
for a, c, txt in O2.narr(SRT):                                         # 1 枚ずつ（改行入り。長い文は声の間で何枚かに）
    if c > T_S0 and a < T_END: ass.append("Dialogue: 1,%s,%s,Main,,0,0,0,,{\\fad(120,120)}%s" % (O2.ts(a - T_S0), O2.ts(min(c, T_END) - T_S0), txt))
if not FINAL:
    for (a, n_), (b, _) in zip(SH, SH[1:] + [(T_END, None)]):
        ass.append("Dialogue: 1,%s,%s,Shot,,0,0,0,,%s　%s" % (O2.ts(a - T_S0), O2.ts(b - T_S0), n_, O2.mmss(a)))
    ass.append("Dialogue: 1,%s,%s,Note,,0,0,0,,まとめ（%s〜%s）確認用・声は Gemini（Achernar）" % (O2.ts(0), O2.ts(T), O2.mmss(T_S0), O2.mmss(T_END)))
open(os.path.join(OUT, "summary_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 音
nA = int(round(T * SR)); tt = np.arange(nA) / SR + T_S0; audio = np.zeros(nA)
rng = np.random.default_rng(21)
def add(at_, x, g=1.0):
    i = int(round((at_ - T_S0) * SR))
    if i >= nA or i + len(x) <= 0: return
    j0 = max(0, -i); m = min(len(x), nA - i); audio[i + j0:i + m] += x[j0:m] * g
# 前半：第3章の曲の 8拍のくり返しを小さく敷く（第8章と同じ拍の位置）。P7 で少し上げ、電車に戻る前に消す
loop = O2.song_loop(SONG); nL = len(loop)
bed = loop[(np.round((tt - p7.T_START_C) * SR).astype(np.int64)) % nL]
lev = 0.12 * np.clip((tt - T_S0) / 1.0, 0, 1) + 0.10 * np.clip((tt - (B6 - 0.4)) / 1.2, 0, 1)
lev *= np.clip((EP0 - 0.15 - tt) / 1.4, 0, 1)
audio += bed * lev
for t_pop in (at(181, "イヤホンが") - 0.1, at(181, "さらに"), at(183, "ほかの") - 0.1, at(183, "次に"), at(184, "使う周波数") - 0.1, at(184, "届かなかった") - 0.1, at(184, "先に届いた") - 0.1):
    add(t_pop, O2.tone(660, 990, 0.09, 0.10))                                   # 札が出る：小さな「ぽん」
for t_ok in (at(181, "音楽に") + 0.45, at(183, "間に合わなく") + 0.55):
    add(t_ok, O2.chime(0.10))                                                   # 答えの ✓


# 後半：止まった世界 → 動き出す（第1・2章の電車の音と同じ作り方）
def thump(f1, f2, tau, n_amp=0.15, dur=0.2):
    t_ = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * math.pi * f1 * t_) * 0.8 + np.sin(2 * math.pi * f2 * t_) * 0.3) * np.exp(-t_ / tau) + rng.normal(0, 1, len(t_)) * np.exp(-t_ / 0.01) * n_amp


for e in LOG["events"]:                                                         # まるロボ（電車の中では小さいので、音も軽く高め）
    te = ep_of_scene(e["t"]); kd = e["kind"]; s_ = e.get("strength", 1.0)
    if te < EP0 - 0.05 or te > T_END: continue
    gq = 2.0 if te < T_UNF else 1.0                                             # 止まった世界で鳴るのは、まるロボの音だけ（よく聞こえる）
    if kd == "step": add(te, thump(170, 340, 0.02, 0.08, 0.08), (0.10 + 0.10 * s_) * gq)
    elif kd == "step_turn": add(te, thump(190, 380, 0.018, 0.06, 0.07), 0.08 * gq)
    elif kd == "takeoff": add(te, thump(150, 300, 0.03, 0.2, 0.15), 0.35)
    elif kd == "land": add(te, thump(160, 430, 0.05, 0.35, 0.3) * min(1.0, s_ / 3.0), 0.7)
t_ = np.arange(int(0.08 * SR)) / SR                                             # ボタンの「カチッ」
add(T_LAND2 + 0.025, rng.normal(0, 1, len(t_)) * np.exp(-t_ / 0.003) * 0.6 + np.sin(2 * math.pi * 1800 * t_) * np.exp(-t_ / 0.012) * 0.5, 0.9)
t_ = np.arange(int(1.6 * SR)) / SR                                              # 時間が動き出す合図：第2章の「止まる音」を逆に（だんだん大きくなって、動き出す瞬間に切れる）
sh = sum(np.sin(2 * math.pi * f * t_ + p) for f, p in ((1568, 0), (2093, 1.1), (2637, 2.3))) / 3 * np.exp(-t_ / 0.6) * (1 - np.exp(-t_ / 0.02)) * 0.16
add(T_UNF - len(sh) / SR, sh[::-1])
# 世界の時計：止まった時刻から、0.5 秒で速さ 0→1（summary_seq.py の consumed と同じ式）
T_FZ, RAMP, P_RES = LOG["t_fz"], LOG["ramp"], LOG["p_resume"]
def consumed(u):
    u = np.maximum(u, 0.0); x = np.clip((RAMP - u) / RAMP, 0, 1)
    return np.where(u >= RAMP, RAMP - RAMP / 2.6 + (u - RAMP), u - RAMP / 2.6 * (1.0 - x ** 2.6))
on3 = tt >= T_UNF; tw = T_FZ + consumed(tt - T_UNF)                              # 各サンプルの世界の時刻（動き出す前は使わない）
# 電車の走行音（うなり＋レールの継ぎ目 25m ごと＝1.5 秒ごと）を世界の時刻で作り、動き出したら世界の時計で読む（テープが回り出す音になる）
w0, w1 = T_FZ - 2.0, T_FZ + D3 + 2.0; nW = int((w1 - w0) * SR)
bW = np.cumsum(rng.normal(0, 1, nW)); bW -= np.convolve(bW, np.ones(4800) / 4800, mode="same"); bW = np.convolve(bW, np.ones(60) / 60, mode="same"); bW /= np.abs(bW).max() + 1e-9
trainW = bW * 0.55 * 0.28
for k0 in np.arange(0.35, w1, 1.5):
    for dd, aa in ((0.0, 1.0), (0.126, 0.85), (0.83, 0.8), (0.956, 0.7)):
        tk = k0 + dd
        if w0 <= tk < w1 - 0.3:
            x_ = thump(58, 120, 0.045); i0 = int((tk - w0) * SR); trainW[i0:i0 + len(x_)] += x_ * aa * 0.35
train = np.where(on3, np.interp(tw, w0 + np.arange(nW) / SR, trainW), 0.0)
# 曲（主人公の耳の中）：止まった所から 8拍のくり返しの中で戻り、サビの頭が M10 の頭に来る（summary_seq.py の P_RESUME）
with wave.open(SONG) as w_:
    sr0 = w_.getframerate(); song = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).astype(float) / 32768.0
pos = P_RES + (tw - T_FZ)
mus = np.where(on3, np.interp(pos * sr0, np.arange(len(song)), song), 0.0)
g_m10 = ((tt >= T_M10) & (tt < T_M11)).astype(float); g_m11 = (tt >= T_M11).astype(float)
nf = 1 << (nA - 1).bit_length(); fq = np.fft.rfftfreq(nf, 1 / SR)
Hf = (1 / (1 + (500 / np.maximum(fq, 1)) ** 4)) * (1 / (1 + (fq / 4200) ** 4))  # 小さなスピーカーの音：低い音と高い音が抜ける（第1章 K8 と同じ）
leak = np.fft.irfft(np.fft.rfft(mus, nf) * Hf, nf)[:nA] * 0.17
sm8 = lambda g: np.convolve(g, np.ones(int(0.008 * SR)) / int(0.008 * SR), mode="same")   # 切り替えは 8ms でなめらかに
g_m10, g_m11 = sm8(g_m10), sm8(g_m11)
music3 = mus * (0.75 * (1 - g_m10 - g_m11) + 0.92 * g_m10) + leak * g_m11
audio += (music3 + train * (1.0 - 0.35 * g_m10)) * np.clip((T_END - tt) / 1.2, 0, 1)
audio = NAR.mix_voice(audio, T_S0, SR, bus_peak=0.5, duck_db=7.0)
with wave.open(os.path.join(OUT, "summary_audio.wav"), "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
json.dump(dict(t_s0=T_S0, ep0=EP0, t_end=T_END, frames=N, b=[B1, B2, B3, B4, B5, B6], unfreeze=T_UNF, m10=T_M10, m11=T_M11),
          open(os.path.join(OUT, "summary_timeline.json"), "w"), indent=0)
print("AUDIO ok  %d frames  %.2f s  (%.3f → %.3f)" % (N, T, T_S0, T_END), flush=True)

# ---------------------------------------------------------------- 絵 → mp4（コマは書かずに ffmpeg へ直接流す）
if "--still" in sys.argv:
    for s_ in opt("--still").split(","):
        frame(float(s_)).save(os.path.join(OUT, "still_%07.2f.png" % float(s_)))
    sys.exit(0)
if "--no_video" in sys.argv: sys.exit(0)
mp4 = os.path.join(OUT, "summary.mp4")
pr_ = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (RW, RH), "-framerate", str(FPS), "-i", "-",
                        "-i", os.path.join(OUT, "summary_audio.wav"), "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "summary_subs.ass"), FONTS),
                        "-frames:v", str(N), "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], stdin=subprocess.PIPE)
for i in range(N):
    pr_.stdin.write(frame(T_S0 + i / FPS).convert("RGB").tobytes())
    if i % 240 == 0: print("STREAM", i, "/", N, flush=True)
pr_.stdin.close(); rc_ = pr_.wait()
if rc_ != 0: sys.exit("ffmpeg failed %d" % rc_)
print("WROTE", mp4)
