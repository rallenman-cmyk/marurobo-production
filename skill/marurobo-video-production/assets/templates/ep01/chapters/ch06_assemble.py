# 第6章「送り直し（再送）」（本編 10:54.7〜12:10.4、台本 v2 の 114〜127）の組み立て
#   3D の連番（ch06_stage.py）に札・印（2D）を重ね、字幕・効果音・曲・声を付けて mp4 にする
#   札や印の位置は、記録（ch06_log.json）のカメラから計算する（3D の物に付いて動く）
#   曲：第3章と同じ曲の 40.04 秒からの 3.08 秒（8拍）を、継ぎ目なくくり返す（くり返しの一致度 1.000）。まるロボの揺れは、この拍に合わせてある
# 使い方: python3 ch06_assemble.py OUT_DIR [--frames DIR] [--proxy DIR] [--range A:B] [--no_video]
#   OUT_DIR/ch06_log.json と DIR/f_NNNN.png（既定 OUT_DIR/frames。番号は 1 から）
#   --proxy：連番の代わりに、確かめ用の静止画（still_本編秒.png）を、同じ場面のいちばん近いコマに使う（札の位置と時刻を見るため）
#   MARU_FINAL=1：確認用の札（場面名・注記）を出さない。MARU_CRF：画質（既定 20）
import sys, os, json, math, subprocess, wave, glob
import numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import subs_jp as SJ                       # 字幕の共通の決まり（大きさ・改行・何枚かに分ける。2026-11-09）
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import ch06_plan as p6, ch03_plan as cp


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


OUT = sys.argv[1]
FR = opt("--frames", os.path.join(OUT, "frames")); PROXY = opt("--proxy")
LOG = json.load(open(os.path.join(OUT, "ch06_log.json"), encoding="utf-8"))
FPS = LOG["fps"]; N = LOG["frames"]; T0 = LOG["t0"]
# 2026-11-09 ユーザー（11:06）：データが受け取る側へ動いたことが分かるように、最初の配達にも「六番を載せて細い橋を渡る」絵を差し込む。
#   3D は描き直さず、送り直しの S8（もう一度イヤホンへ）のコマを使う：S8 の 34.50 秒から 74 コマ（3.083 秒）を、S2b（06 を積む）と S3a（巨大イヤホン）の間へ。
#   長さは曲のくり返し 1 回分（3.08 秒）とほぼ同じなので、曲の拍は前後でそのままつながる（差し込みの終わりで 3 ms だけ合わせ直す）
import timeedit
INS_AT = next(a_ for a_, n_ in LOG["shots"] if n_ == "S3a")             # 差し込む所（章の頭からの秒）＝ S3a の始まり
INS_I0, INS_N = int(round(34.50 * FPS)), 74                              # 使うコマ（0 から数える）と数
INS_J = int(round(INS_AT * FPS)); INS_LEN = INS_N / FPS
TE = timeedit.TimeEdit([(T0 + INS_AT, T0 + INS_AT, INS_LEN)])
def te_rel(t): return TE.out(T0 + t) - T0                               # 元の秒（章の頭から）→ 出す秒
def src_i(j): return j if j < INS_J else (INS_I0 + (j - INS_J) if j < INS_J + INS_N else j - INS_N)   # 出すコマ → 元のコマ
N_OUT = N + INS_N; T = N_OUT / FPS
RNG = opt("--range"); I0, I1 = (0, N_OUT) if not RNG else tuple(int(v) for v in RNG.split(":"))
SRT = os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")
SONG = os.path.join(HERE, "..", "human", "audio", "song_mono.wav")
FONTS = os.path.join(HERE, "..", "av", "fonts"); FONT_J = os.path.join(FONTS, "japanese.ttc")
SEQ = os.path.join(OUT, "full"); os.makedirs(SEQ, exist_ok=True)
SR = 48000
TM = LOG["times"]; PTS = LOG["points"]
F_ = np.array(cp.F, float); R_ = np.array(cp.R, float)


def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)
def fade(t, a, b, fi=0.2, fo=0.2): return clamp((t - a) / fi) * clamp((b - t) / fo) if fi > 0 and fo > 0 else float(a <= t < b)
def L(n): return p6.L(n)


# ---------------------------------------------------------------- 場面（ch06_stage.py の記録）
SH = LOG["shots"]
def shot_at(t):
    nm = SH[0][1]
    for a, n_ in SH:
        if t >= a - 1e-6: nm = n_
    return nm


# ---------------------------------------------------------------- 3D の点 → 画面（640×360 の目盛り）
def qmat(w, x, y, z):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def proj(i, P):
    if P is None: return None
    c = LOG["cam"][min(max(i, 0), N - 1)]; R = qmat(*c[3:7]); d = R.T @ (np.array(P, float) - np.array(c[:3], float))
    if d[2] > -1e-4: return None
    f = c[7] / LOG.get("sensor", 36.0) * 640.0
    return (320.0 + f * d[0] / -d[2], 180.0 - f * d[1] / -d[2])


def label_pt(i):
    """運ぶ荷物の、前の面の札の番号（06）の位置と、まわりの丸の半径（画面の目盛り）。札の番号は札の中心から右へ 10cm・上へ 11cm"""
    c = LOG["cargo"][i]
    if c is None: return None, 0
    P = np.array(c) + np.array([*(F_ * 0.32 - R_ * 0.10), 0.13]); a = proj(i, P); b = proj(i, P + np.array([0, 0, 0.15]))
    return (a, clamp(math.hypot(b[0] - a[0], b[1] - a[1]) if (a and b) else 40.0, 18.0, 90.0)) if a else (None, 0)


def add2(p, dx, dy): return None if p is None else (p[0] + dx, p[1] + dy)


# ---------------------------------------------------------------- 絵（連番 or 確かめ用の静止画）
STILLS = []
if PROXY:
    for p in glob.glob(os.path.join(PROXY, "still_*.png")):
        try: ta = float(os.path.basename(p)[6:-4])
        except ValueError: continue
        STILLS.append((int(round((ta - T0) * FPS)), p))
    STILLS.sort()


def src_frame(i):
    if PROXY:
        nm = shot_at(i / FPS); cand = [(abs(fi - i), p) for fi, p in STILLS if shot_at(fi / FPS) == nm]
        if cand: return Image.open(min(cand)[1]).convert("RGB")
        im = Image.new("RGB", (640, 360), (70, 76, 84)); ImageDraw.Draw(im).text((320, 180), nm, fill="white", anchor="mm"); return im
    return Image.open(os.path.join(FR, "f_%04d.png" % (i + 1))).convert("RGB")


_first = src_frame(I0); RW, RH = _first.size
import cutfix
REMAP6 = {}                                                            # 差し込みの両どなり（S2b の最後・S3a の最初）がカメラの飛びでブレていたら、となりのコマに替える
if not PROXY:
    try: REMAP6 = {a_ - 1: b_ - 1 for a_, b_ in cutfix.remap(lambda k_: os.path.join(FR, "f_%04d.png" % k_), [INS_J], log=print).items()}
    except Exception as ex: print("cutfix skipped", ex)
# 確認ページ用：MARU_OUTW=1280 なら、640×360 の絵を 1280×720 に広げてから札・印を描く（字や線がくっきり）
if os.environ.get("MARU_OUTW"): RW = int(os.environ["MARU_OUTW"]); RH = RW * 9 // 16
K = RW / 640.0
TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY = (31, 94, 102), (40, 160, 88), (214, 64, 60), (206, 120, 36), (40, 46, 52), (250, 250, 248), (150, 158, 166)
_fc = {}
def F(px):
    k = max(8, int(round(px * K)))
    if k not in _fc: _fc[k] = ImageFont.truetype(FONT_J, k)
    return _fc[k]
def P_(*xy): return [v * K for v in xy]
def W_(w): return max(1, int(round(w * K)))


def draw(base, a, fn):
    """透明な層に fn で描き、層全体の濃さを a にして重ねる（フェード）"""
    if a <= 0.003: return base
    Ly = Image.new("RGBA", base.size, (0, 0, 0, 0)); fn(ImageDraw.Draw(Ly))
    if a < 0.999: Ly.putalpha(Ly.getchannel("A").point(lambda v: int(v * a)))
    return Image.alpha_composite(base, Ly)


def tag(d, xy, txt, col, px=17):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * K, xy[1] * K
    d.rounded_rectangle([x - w / 2 - 12 * K, y - px * 0.8 * K, x + w / 2 + 12 * K, y + px * 0.8 * K], radius=9 * K, fill=WHITE, outline=col, width=W_(2))
    d.text((x, y), txt, font=f, fill=col, anchor="mm")


def ring(d, c, r, col, w=3):
    d.ellipse(P_(c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col, width=W_(w))


def mark(d, c, r, ok):
    col = GREEN if ok else RED; x, y = c
    d.ellipse(P_(x - r - 2, y - r - 2, x + r + 2, y + r + 2), fill=WHITE); d.ellipse(P_(x - r, y - r, x + r, y + r), fill=col)
    if ok: d.line(P_(x - r * .45, y, x - r * .1, y + r * .35, x + r * .48, y - r * .35), fill=WHITE, width=W_(r * .2), joint="curve")
    else:
        for sg in (1, -1): d.line(P_(x - r * .42, y - sg * r * .42, x + r * .42, y + sg * r * .42), fill=WHITE, width=W_(r * .2))


def bubble(d, c, txt, col, dashed=False, px=16):
    f = F(px); w = d.textlength(txt, font=f) / K; x, y = c
    box = P_(x - w / 2 - 12, y - 16, x + w / 2 + 12, y + 16)
    d.rounded_rectangle(box, radius=10 * K, fill=WHITE, outline=None if dashed else col, width=W_(2))
    if dashed:                                                         # 点線のふち（「もし受け取れたら」の説明）
        x0, y0, x1, y1 = box; n = 14
        for k in range(n):
            if k % 2: continue
            u0, u1 = k / n, (k + 1) / n
            d.line([(x0 + (x1 - x0) * u0, y0), (x0 + (x1 - x0) * u1, y0)], fill=col, width=W_(2)); d.line([(x0 + (x1 - x0) * u0, y1), (x0 + (x1 - x0) * u1, y1)], fill=col, width=W_(2))
        d.line([(x0, y0 + 4 * K), (x0, y1 - 4 * K)], fill=col, width=W_(2)); d.line([(x1, y0 + 4 * K), (x1, y1 - 4 * K)], fill=col, width=W_(2))
    d.text((x * K, y * K), txt, font=f, fill=col, anchor="mm")


def arc(d, a, b, col, u=1.0, dashed=True, h=70, w=3):
    """a → b の山なりの矢印（u：先までの割合）。真ん中の点を返す"""
    pts = []
    for k in range(41):
        s = k / 40 * u; x = a[0] + (b[0] - a[0]) * s; y = a[1] + (b[1] - a[1]) * s - h * 4 * s * (1 - s); pts.append((x * K, y * K))
    for k in range(40):
        if dashed and k % 2: continue
        d.line([pts[k], pts[k + 1]], fill=col, width=W_(w))
    if u > 0.98:
        x1, y1 = pts[-1]; x0, y0 = pts[-3]; ang = math.atan2(y1 - y0, x1 - x0)
        d.polygon([(x1, y1), (x1 - 14 * K * math.cos(ang - .45), y1 - 14 * K * math.sin(ang - .45)), (x1 - 14 * K * math.cos(ang + .45), y1 - 14 * K * math.sin(ang + .45))], fill=col)
    m = 0.5; return (a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m - h)


def note(d, c, col, sc=1.0):
    x, y = c[0] * K, c[1] * K; s = sc * K
    d.ellipse([x - 7 * s, y + 5 * s, x + 4 * s, y + 14 * s], fill=col); d.line([(x + 3 * s, y + 9 * s), (x + 3 * s, y - 13 * s)], fill=col, width=max(1, int(2.5 * s)))
    d.line([(x + 3 * s, y - 13 * s), (x + 12 * s, y - 8 * s)], fill=col, width=max(1, int(2.5 * s)))


def qmark(d, c, col, px=40):
    d.text((c[0] * K, c[1] * K), "？", font=F(px), fill=col, anchor="mm", stroke_width=W_(3), stroke_fill=WHITE)


def title(d, xy, txt, col, px=30):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * K, xy[1] * K
    d.rounded_rectangle([x - w / 2 - 22 * K, y - px * 0.85 * K, x + w / 2 + 22 * K, y + px * 0.85 * K], radius=14 * K, fill=WHITE, outline=col, width=W_(3))
    d.text((x, y), txt, font=f, fill=col, anchor="mm")


T_GROOVE0 = TM["groove"]; BEAT = p6.BEAT
def beat_n(t): return math.floor((t - T_GROOVE0) / BEAT)        # 曲の拍の番号（揺れ始めが 0）


SHOT_SPAN = {nm_: (a_, (SH[k_ + 1][0] if k_ + 1 < len(SH) else N / FPS)) for k_, (a_, nm_) in enumerate(SH)}
def overlays(base, i):
    t = i / FPS; ta = T0 + t; nm = shot_at(t)
    if nm == "S2":                                                     # 「今度は、この六番の荷物を…」
        c, r = label_pt(i); a = fade(ta, 658.25, 659.55, 0.25, 0.2)
        if c: base = draw(base, a, lambda d: ring(d, c, r, TEAL, 4))
    elif nm == "S3a":                                                  # 「受け取る側は、」：巨大イヤホンを丸ごと見上げる
        a_, b_ = SHOT_SPAN["S3a"]; base = draw(base, fade(t, a_ + 0.12, b_ - 0.02, 0.2, 0.15), lambda d: tag(d, (478, 72), "受け取る側：イヤホン", TEAL))   # 右の空（イヤホンの頭にかからない所）
    elif nm == "S3":                                                   # 「誤りがないかを確かめます」：光がなぞる
        pass
    elif nm == "S4":                                                   # 「受け取れたら、スマホに『届いたよ』と返事を送ります」（もしもの説明なので点線）
        A_ = add2(proj(i, PTS["booth_lamp"]), 0, -10); B_ = add2(proj(i, PTS["phone_lamp"]), 0, -10)
        if A_ and B_:
            u = clamp((ta - 667.9) / 0.9); a = fade(ta, 667.9, 671.35, 0.15, 0.25)
            def f4(d):
                m = arc(d, A_, B_, GREEN, u, True, 64)
                if ta >= 668.55: bubble(d, (m[0], m[1] - 26), "届いたよ", GREEN, True)
            base = draw(base, a, f4)
    elif nm == "S5":                                                   # 「今回は、正しく受け取れませんでした」：灯が赤
        c = proj(i, PTS["booth_lamp"]); a = fade(ta, TM["red"] + T0 + 0.05, 674.85, 0.12, 0.2)
        def f5(d):
            if c: mark(d, (c[0] + 30, c[1] + 22), 15, False)
        base = draw(base, a, f5)
    elif nm == "S6":                                                   # 返事を待つ輪 → 一周しても来ない →「？」
        c = proj(i, PTS["phone_lamp"]); a6 = SHOT_SPAN["S6"][0]
        base = draw(base, fade(t, a6 + 0.15, a6 + 2.2, 0.2, 0.2), lambda d: tag(d, (478, 72), "送る側：スマホ", TEAL))   # 巨大スマホが丸ごと見える引き（右の空に）
        def f6(d):
            if c: qmark(d, (c[0] - 74, c[1] - 58), AMBER, 44)
        base = draw(base, fade(ta, TM["lost"] + T0 + 0.02, 681.25, 0.12, 0.2), f6)
    elif nm == "S7":                                                   # 「そこで、同じ六番を、もう一度」：スマホに残しておいた 06
        c, r = label_pt(i); a = fade(ta, 684.45, 686.15, 0.25, 0.2)
        if c: base = draw(base, a, lambda d: ring(d, c, r, AMBER, 4))
    elif nm == "S9":                                                   # もう一度なぞる → 今度は緑
        c = proj(i, PTS["booth_lamp"])
        def f9(d):
            if c: mark(d, (c[0] + 30, c[1] + 22), 15, True)
        base = draw(base, fade(ta, TM["green"] + T0 + 0.05, 1e9, 0.12, 0.2), f9)
    elif nm == "S10":                                                  # 返事の光：「届いたよ」の吹き出しが光に付いていく
        o = LOG["orb"][i]; c = proj(i, o) if o else None
        if c: base = draw(base, fade(ta, TM["reply0"] + T0 + 0.15, 700.2, 0.2, 0.05), lambda d: bubble(d, (c[0], c[1] - 30), "届いたよ", GREEN))
    elif nm == "S10b":                                                 # スマホの返事ランプが緑：届いたと分かる
        c = proj(i, PTS["phone_lamp"])
        def f10(d):
            if c: mark(d, (c[0] - 46, c[1] - 44), 15, True); bubble(d, (c[0] - 120, c[1] - 84), "届いたよ", GREEN)
        base = draw(base, fade(ta, TM["lamp_ok"] + T0 + 0.05, 702.4, 0.12, 0.2), f10)
    elif nm == "S11":                                                  # 「この送り直しを、再送といいます」
        base = draw(base, fade(ta, 702.85, 705.5, 0.25, 0.2), lambda d: title(d, (320, 74), "再送（さいそう）", TEAL))
    elif nm == "S12":                                                  # 06× → 06✓ → 07 → 08（新しい曲ではなく、受け取れなかった分をもう一度）
        items = [("06 ×", RED, 706.1), ("06 ✓", GREEN, 707.5), ("07", INK, 709.2), ("08", INK, 709.8)]
        for j, (txt, col, t_on) in enumerate(items):
            x = 170 + j * 100
            def fi(d, j=j, txt=txt, col=col, x=x):
                d.rounded_rectangle(P_(x - 36, 20, x + 36, 52), radius=8 * K, fill=WHITE, outline=col, width=W_(2)); d.text((x * K, 36 * K), txt, font=F(18), fill=col, anchor="mm")
                if j > 0: d.text(((x - 50) * K, 36 * K), "→", font=F(18), fill=INK, anchor="mm", stroke_width=W_(2), stroke_fill=WHITE)
            base = draw(base, fade(ta, t_on, 712.05, 0.2, 0.2), fi)
    elif nm == "S13":                                                  # 「ところで、今の音楽、聞いていましたか？」：拍ごとに音符が出る
        c0 = proj(i, [*cp.RP(cp.S_U), 2.05])
        if c0:
            for n_ in range(beat_n(t) - 4, beat_n(t) + 1):
                if n_ < 0 or n_ % 2: continue
                tb = T_GROOVE0 + n_ * BEAT; age = t - tb
                if not (0 <= age < 1.7) or ta < 712.6: continue
                side = 1 if (n_ // 2) % 2 else -1
                c = (c0[0] + side * (34 + 10 * age), c0[1] - 12 - 30 * age)
                base = draw(base, fade(age, 0.0, 1.7, 0.12, 0.6) * fade(ta, 712.6, 720.4, 0.3, 0.3), lambda d, c=c: note(d, c, TEAL, 1.3))
    if nm in ("S14", "S15", "S16"):                                    # 「曲は続いていました」→「何を鳴らしていたのでしょう」→ 耳の先へ
        c0 = proj(i, PTS["eb_head"])
        if c0:
            for n_ in range(beat_n(t) - 4, beat_n(t) + 1):
                if n_ % 2: continue
                tb = T_GROOVE0 + n_ * BEAT; age = t - tb
                if not (0 <= age < 1.7): continue
                side = 1 if (n_ // 2) % 2 else -1
                c = (c0[0] + side * (60 + 12 * age), c0[1] - 20 - 26 * age)
                base = draw(base, fade(age, 0.0, 1.7, 0.12, 0.6) * fade(ta, 720.75, 726.2, 0.3, 0.6), lambda d, c=c: note(d, c, TEAL, 1.3))
            base = draw(base, fade(ta, 726.6, 731.0, 0.3, 0.5), lambda d: qmark(d, (c0[0] + 92, c0[1] - 70), TEAL, 52))
    return base


# ---------------------------------------------------------------- 字幕：ナレーション（本編の時刻から）、場面の名前、最初だけの注記
def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def mmss(t): return "%d:%04.1f" % (int(t // 60), t % 60)


def wrap_jp(txt, n=28):
    if len(txt) <= n: return txt
    cands = [i + 1 for i, ch in enumerate(txt[:-1]) if ch in "。、" and 6 <= i + 1 <= len(txt) - 4]
    cut = min(cands, key=lambda i: abs(i - len(txt) / 2)) if cands else len(txt) // 2
    return txt[:cut] + "\\N" + txt[cut:]


def srt_lines(path):
    out = []
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        Ls = b.split("\n")
        if len(Ls) < 3 or " --> " not in Ls[1]: continue
        def sec(x):
            h, m, r = x.strip().split(":"); s_, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(s_) + int(ms) / 1000
        a, c = Ls[1].split(" --> "); out.append((sec(a), sec(c), " ".join(Ls[2:])))
    return out


NAMES = {"S1": "S1 巨大スマホの画面（06 が光る）→ 窓の前のまるロボ", "S2": "S2 窓の中の 06・07・08", "S2b": "S2 06 を積む", "S3a": "S3a 引き：巨大イヤホン（受け取る側）", "S3": "S3 受付ボックス：光がなぞる",
         "S4": "S4 受け取れたら返事（説明）", "S5": "S5 今回は誤り（灯が赤）", "S6": "S6 スマホの返事ランプ：待つ輪 →「？」", "S6b": "S6 スマホへ戻る（細い橋）",
         "S7": "S7 残しておいた 06", "S7b": "S7 もう一度積む", "S8": "S8 もう一度イヤホンへ（細い橋）", "S9": "S9 受付ボックス：光 → 灯が緑",
         "S10": "S10 返事の光がスマホへ", "S10b": "S10 返事ランプが緑", "S11": "S11 再送", "S12": "S12 06×→06✓→07→08", "S13": "S13 曲はずっと鳴っていた",
         "S14": "S14 巨大イヤホン", "S15": "S15 イヤホンの頭へ →「？」", "S16": "S16 耳の先（音の出口）へ → イヤホンの中へ"}
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       SJ.STYLE_MAIN,
       "Style: Note,Noto Sans CJK JP,19,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,3,6,0,9,0,24,18,1",
       "Style: Shot,Noto Sans CJK JP,19,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,3,6,0,7,24,0,18,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
ass.append("Dialogue: 0,%s,%s,Note,,0,0,0,,第6章（%s〜%s）確認用・低画質・声は Gemini（Achernar）" % (ts(0), ts(T), mmss(T0), mmss(T0 + T)))
for a, b, txt in SJ.expand(TE.subs(srt_lines(SRT))):                  # 1 枚ずつ（改行入り。長い文は声の間で何枚かに）。始まりは出す時刻へ
    if b < T0 or a > T0 + T: continue
    ass.append("Dialogue: 1,%s,%s,Main,,0,0,0,,{\\fad(120,120)}%s" % (ts(a - T0), ts(min(b, T0 + T) - T0), txt))
for (a, nm), (b, _) in zip(SH, SH[1:] + [[T, None]]):
    ass.append("Dialogue: 0,%s,%s,Shot,,0,0,0,,%s　%s" % (ts(a), ts(b), NAMES.get(nm, nm), mmss(T0 + a)))
if os.environ.get("MARU_FINAL") == "1": ass = [l_ for l_ in ass if ",Note,," not in l_ and ",Shot,," not in l_]
open(os.path.join(OUT, "ch06_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 効果音（出来事の時刻に置く。まるロボの声は使わない）
audio = np.zeros(int((T + 1.0) * SR)); rng = np.random.default_rng(6)


def env_ad(n, a=0.004, d=0.08):
    t = np.arange(n) / SR; return np.minimum(t / a, 1.0) * np.exp(-np.maximum(t - a, 0) / d)


def tone(f0, f1, dur, amp, d=None, shape="sine"):
    n = int(dur * SR); t = np.arange(n) / SR; f = f0 + (f1 - f0) * t / dur
    ph = 2 * math.pi * np.cumsum(f) / SR
    x = np.sin(ph) if shape == "sine" else (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph))
    return amp * x * env_ad(n, 0.004, d or dur * 0.6)


def lowpass(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x): s = a * s + (1 - a) * v; y[i] = s
    return y


def thump(amp, dur=0.09, f=85.0, click=0.3):
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * math.pi * f * t * (1 - 0.3 * t / dur)) * np.exp(-t / (dur * 0.35))
    nz = lowpass(rng.normal(0, 1, n), 1800) * np.exp(-t / 0.012) * click
    return amp * (body + nz)


def clank(amp, dur=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * sum(w * np.sin(2 * math.pi * f * t) * np.exp(-t / dd) for f, w, dd in ((820, 1.0, 0.09), (1310, 0.6, 0.06), (2170, 0.35, 0.04)))


def motor(dur, amp, f=150.0):
    n = int(dur * SR); t = np.arange(n) / SR; e = np.minimum(t / 0.15, 1.0) * np.minimum((dur - t) / 0.2, 1.0)
    ph = 2 * math.pi * (f * t + 6 * np.sin(2 * math.pi * 0.7 * t) / (2 * math.pi * 0.7))
    x = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph) + 0.15 * lowpass(rng.normal(0, 1, n), 900)
    return amp * x * e


def chime(amp, notes=((1568, 1.0, 0.35), (2093, 0.6, 0.25)), dur=0.9):
    n = int(dur * SR); tt = np.arange(n) / SR
    return amp * sum(w * np.sin(2 * math.pi * f * tt) * np.exp(-tt / d) for f, w, d in notes)


def whoosh(dur, amp, f0, f1, rise=False):
    """光が通る音：帯域を動かした雑音（遠ざかる・近づく）"""
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.normal(0, 1, n); y = np.zeros(n); s1 = s2 = 0.0
    fc = f0 + (f1 - f0) * t / dur
    for i in range(n):
        a = math.exp(-2 * math.pi * fc[i] / SR); s1 = a * s1 + (1 - a) * x[i]; s2 = a * s2 + (1 - a) * s1; y[i] = s1 - s2
    e = (t / dur) ** 2 if rise else np.minimum(t / 0.05, 1.0) * np.exp(-t / (dur * 0.4))
    return amp * y / max(np.abs(y).max(), 1e-9) * e


def add(t, x, raw=False):
    if not raw: t = te_rel(t)                                         # 出す時刻へ（差し込みのあとは 3.08 秒おそく）
    i = int(t * SR)
    if i < 0 or i >= len(audio): return
    j = min(len(audio), i + len(x)); audio[i:j] += x[:j - i]


MONT = [(a, b) for a, b, nm in LOG["montage"]]
for e in LOG["events"]:
    t, k, s = e["t"], e["kind"], e.get("strength", 1.0)
    if t < 0 or t > T: continue
    if k == "step": add(t, thump(0.22 * (0.4 + 0.6 * s), f=95.0))
    elif k == "step_turn": add(t, thump(0.10, f=110.0, click=0.2))
    elif k == "beep_yes": add(t, tone(880, 880, 0.08, 0.16)); add(t + 0.11, tone(1175, 1175, 0.10, 0.16))
    elif k == "cradle_out": add(t, tone(180, 260, 0.5, 0.05, d=0.4, shape="buzz"))
    elif k == "cradle_in": add(t, tone(260, 170, 0.6, 0.05, d=0.5, shape="buzz"))
    elif k == "push": add(t - 0.55, motor(0.4, 0.035, 210.0)); add(t, motor(2.2, 0.045, 140.0))
    elif k == "pull":
        T_ = e.get("T", 2.2); add(t - 0.9, motor(0.85, 0.03, 230.0)); add(t, thump(0.08, dur=0.05, f=900.0, click=0.6)); add(t, clank(0.03, 0.12))
        add(t + 0.3, motor(T_, 0.045, 140.0)); add(t + 0.3 + T_ + 0.02, clank(0.02, 0.08)); add(t + 0.3 + T_ + 0.2, motor(0.9, 0.022, 230.0))
    elif k == "load_done": add(t, thump(0.12, dur=0.12, f=80.0, click=0.15))
    elif k in ("lock", "unlock"): add(t, thump(0.06, dur=0.04, f=1400.0, click=0.8)); add(t + 0.03, clank(0.012, 0.06))
    elif k == "takeoff": add(t - 0.02, thump(0.10, dur=0.10, f=72.0, click=0.25))
    elif k == "land": v_ = e.get("strength", 2.0); add(t, thump(min(0.30, 0.11 * v_), dur=0.14, f=64.0, click=0.35)); add(t + 0.01, clank(0.010, 0.08))
for k_, t in enumerate(TM["scan"]):                                   # なぞる光：やわらかく上がる音（1.4秒）
    add(t - 0.1, tone(620, 980, p6.SCAN_T + 0.2, 0.035, d=p6.SCAN_T)); add(t - 0.1, tone(310, 490, p6.SCAN_T + 0.2, 0.02, d=p6.SCAN_T))
for t in TM["shut"]:                                                  # シャッター（細かい音の連なり → 閉まる音）
    for k in range(11): add(t + k * 0.05, clank(0.012 + 0.002 * k, 0.05))
    add(t + 0.56, thump(0.12, dur=0.1, f=120.0, click=0.5)); add(t + 0.56, clank(0.04))
add(TM["red"], tone(330, 330, 0.16, 0.09, d=0.12, shape="buzz")); add(TM["red"] + 0.22, tone(262, 262, 0.26, 0.09, d=0.2, shape="buzz"))   # 誤り：低い2つの音
add(TM["green"], chime(0.10))                                         # 受け取れた：第3章と同じ、やわらかいチャイム
for k in range(24): add(TM["ring0"] + (TM["ring1"] - TM["ring0"]) * k / 24.0, tone(1760, 1760, 0.03, 0.02, d=0.015))   # 待つ輪：小さな刻み
add(TM["lost"], tone(660, 660, 0.14, 0.06, d=0.1)); add(TM["lost"] + 0.17, tone(494, 494, 0.24, 0.06, d=0.18))           # 時間切れ（下がる2つの音）
add(TM["reply0"], whoosh(0.9, 0.05, 2400, 900))                       # 返事の光が出る（遠ざかる）
add(TM["reply1"] - 0.35, whoosh(0.35, 0.05, 900, 2600, rise=True))    # 着く（近づく）
add(TM["lamp_ok"], chime(0.10, ((1319, 1.0, 0.25), (1760, 0.8, 0.4)), 1.0))   # スマホの返事ランプ：明るい2つの音
add(TM["adv"], motor(2.6, 0.018, 95.0))                               # 07・08 が前へ（ローラー）
for e in LOG["events"]:                                               # 差し込んだ S8 のコマの足音（同じ一歩を、差し込んだ所でも）
    if e["kind"] == "step" and INS_I0 / FPS <= e["t"] < (INS_I0 + INS_N) / FPS:
        add(INS_AT + e["t"] - INS_I0 / FPS, thump(0.22 * (0.4 + 0.6 * e.get("strength", 1.0)), f=95.0), raw=True)
sfx_peak = np.abs(audio).max(); audio = audio / max(sfx_peak, 1e-9) * 0.55

# ---------------------------------------------------------------- 曲：ずっと小さく鳴っている（「今の音楽、聞いていましたか？」から少し大きく）
#   拍の頭は、まるロボの揺れ始めから 0.385 秒ごと（揺れは2拍に1回沈む）
try:
    w = wave.open(SONG); sr0 = w.getframerate(); w.setpos(int(round(40.04 * sr0))); x = np.frombuffer(w.readframes(int(round(3.08 * sr0))), np.int16).astype(float) / 32768
    nL = int(round(3.08 * SR)); loop = np.interp(np.arange(nL) * (len(x) / nL), np.arange(len(x)), x)
    loop = loop / max(np.abs(loop).max(), 1e-9)
    nA = len(audio); g0 = int(round(T_GROOVE0 * SR)); n_ins = int(round(INS_LEN * SR)); k_end = int(round((INS_AT + INS_LEN) * SR))
    ar = np.arange(nA); bed1 = loop[(ar - g0) % nL]                                    # 出す時刻のまま（差し込みの間も曲は続く）
    bed2 = loop[(ar - n_ins - g0) % nL]                                                 # 差し込みのあと：元の拍（第7章へそのままつながる）
    wx = np.clip((ar - k_end) / (0.03 * SR), 0, 1); bed = bed1 * (1 - wx) + bed2 * wx   # 差し込みの終わりで 30ms かけて合わせ直す（3ms の差）
    tt_o = ar / SR; tt = np.where(tt_o < INS_AT, tt_o, np.where(tt_o < INS_AT + INS_LEN, INS_AT, tt_o - INS_LEN)); t_up0, t_up1 = L(125) - T0 - 0.6, L(125) - T0 + 1.4; t_dn0, t_dn1 = p6.LE(126) - T0 + 0.3, p6.LE(126) - T0 + 2.3
    lev = 0.16 + 0.16 * np.clip((tt - t_up0) / (t_up1 - t_up0), 0, 1) - 0.08 * np.clip((tt - t_dn0) / (t_dn1 - t_dn0), 0, 1)
    lev *= np.clip(tt_o / 1.2, 0, 1)                                  # 章の頭は 1.2 秒で上がる（前の章から続いて聞こえる大きさへ）
    audio = audio + bed * lev
except Exception as ex:
    print("SONG skipped:", ex)
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import narration as NAR
PLACE6 = TE.place([p_ for p_ in json.load(open(os.path.join(HERE, "..", "voice", "achernar", "placement.json"), encoding="utf-8")) if p_["no"] <= 128])   # 声も出す時刻へ（第7章の声は入れない）
audio = NAR.mix_voice(audio, T0, SR, bus_peak=0.5, duck_db=6.0, P=PLACE6)
with wave.open(os.path.join(OUT, "ch06_audio.wav"), "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 本番（MARU_STREAM=1）：コマを PNG に書かず、ffmpeg へ直接流す（1080p の PNG はディスクに入らない）
if os.environ.get("MARU_STREAM") == "1" and not RNG and "--no_video" not in sys.argv:
    mp4 = os.path.join(OUT, "ch06_animatic.mp4")
    pr_ = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (RW, RH), "-framerate", str(FPS), "-i", "-",
                            "-i", os.path.join(OUT, "ch06_audio.wav"), "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch06_subs.ass"), FONTS),
                            "-frames:v", str(I1 - I0), "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], stdin=subprocess.PIPE)
    for j in range(I0, I1):
        i = src_i(j); i = REMAP6.get(i, i); im = src_frame(i).convert("RGBA")
        if im.size != (RW, RH): im = im.resize((RW, RH), Image.LANCZOS)
        pr_.stdin.write(overlays(im, i).convert("RGB").tobytes())
        if j % 240 == 0: print("STREAM", j, "/", I1, flush=True)
    pr_.stdin.close(); rc_ = pr_.wait()
    if rc_ != 0: sys.exit("ffmpeg failed %d" % rc_)
    print("WROTE", mp4); sys.exit(0)

# ---------------------------------------------------------------- 絵：札・印を重ねて full/ へ
for j in range(I0, I1):
    i = src_i(j); i = REMAP6.get(i, i); im = src_frame(i).convert("RGBA")
    if im.size != (RW, RH): im = im.resize((RW, RH), Image.LANCZOS)
    overlays(im, i).convert("RGB").save(os.path.join(SEQ, "f_%04d.png" % (j + 1)))
print("FRAMES", I0, I1, "→", SEQ, flush=True)
if "--no_video" in sys.argv: sys.exit(0)

# ---------------------------------------------------------------- 動画
mp4 = os.path.join(OUT, "ch06_animatic.mp4" if not RNG else "ch06_part.mp4")
cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-start_number", str(I0 + 1), "-i", os.path.join(SEQ, "f_%04d.png"),
       "-ss", "%.3f" % (I0 / FPS), "-i", os.path.join(OUT, "ch06_audio.wav"),
       "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch06_subs.ass"), FONTS) if not RNG else "null",
       "-frames:v", str(I1 - I0), "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p",
       "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4]
subprocess.run(cmd, check=True)
print("WROTE", mp4)
