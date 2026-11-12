# 組み立て（chNN_assemble.py）で共通に使う道具：札・印（2D）、カメラの記録から画面の位置、字幕（ASS）、効果音
#   札の大きさは 640×360 の目盛りで書き、init(画面の幅) で実際の大きさにそろえる
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import subs_jp as SJ                       # 字幕の共通の決まり（大きさ・改行・何枚かに分ける。2026-11-09）
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.environ.get("MARU_FONTS") or os.path.join(os.environ.get("MARU_WORK", "."), "stage", "av", "fonts"); FONT_J = os.path.join(FONTS, "japanese.ttc")   # 字のフォント（Noto Sans CJK JP）の置き場所
TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY = (31, 94, 102), (40, 160, 88), (214, 64, 60), (206, 120, 36), (40, 46, 52), (250, 250, 248), (150, 158, 166)
K = 1.0; _fc = {}


def init(rw):
    global K
    K = rw / 640.0


def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)
def fade(t, a, b, fi=0.2, fo=0.2): return clamp((t - a) / fi) * clamp((b - t) / fo)
def F(px):
    k = max(8, int(round(px * K)))
    if k not in _fc: _fc[k] = ImageFont.truetype(FONT_J, k)
    return _fc[k]
def P_(*xy): return [v * K for v in xy]
def W_(w): return max(1, int(round(w * K)))


# ---------------------------------------------------------------- 3D の点 → 画面（640×360 の目盛り）
def qmat(w, x, y, z):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def proj(cam, P, sensor=36.0):
    """cam：[x, y, z, qw, qx, qy, qz, lens]（記録の1コマ分）"""
    if P is None: return None
    R = qmat(*cam[3:7]); d = R.T @ (np.array(P, float) - np.array(cam[:3], float))
    if d[2] > -1e-4: return None
    f = cam[7] / sensor * 640.0
    return (320.0 + f * d[0] / -d[2], 180.0 - f * d[1] / -d[2])


def add2(p, dx, dy): return None if p is None else (p[0] + dx, p[1] + dy)


# ---------------------------------------------------------------- 描く道具
def draw(base, a, fn):
    """透明な層に fn で描き、層全体の濃さを a にして重ねる（フェード）。base は RGBA"""
    if a <= 0.003: return base
    Ly = Image.new("RGBA", base.size, (0, 0, 0, 0)); fn(ImageDraw.Draw(Ly))
    if a < 0.999: Ly.putalpha(Ly.getchannel("A").point(lambda v: int(v * a)))
    return Image.alpha_composite(base, Ly)


def tag(d, xy, txt, col, px=17):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * K, xy[1] * K
    d.rounded_rectangle([x - w / 2 - 12 * K, y - px * 0.8 * K, x + w / 2 + 12 * K, y + px * 0.8 * K], radius=9 * K, fill=WHITE, outline=col, width=W_(2))
    d.text((x, y), txt, font=f, fill=col, anchor="mm")


def ring(d, c, r, col, w=3): d.ellipse(P_(c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col, width=W_(w))


def mark(d, c, r, ok):
    col = GREEN if ok else RED; x, y = c
    d.ellipse(P_(x - r - 2, y - r - 2, x + r + 2, y + r + 2), fill=WHITE); d.ellipse(P_(x - r, y - r, x + r, y + r), fill=col)
    if ok: d.line(P_(x - r * .45, y, x - r * .1, y + r * .35, x + r * .48, y - r * .35), fill=WHITE, width=W_(r * .2), joint="curve")
    else:
        for sg in (1, -1): d.line(P_(x - r * .42, y - sg * r * .42, x + r * .42, y + sg * r * .42), fill=WHITE, width=W_(r * .2))


def note(d, c, col, sc=1.0):
    x, y = c[0] * K, c[1] * K; s = sc * K
    d.ellipse([x - 7 * s, y + 5 * s, x + 4 * s, y + 14 * s], fill=col); d.line([(x + 3 * s, y + 9 * s), (x + 3 * s, y - 13 * s)], fill=col, width=max(1, int(2.5 * s)))
    d.line([(x + 3 * s, y - 13 * s), (x + 12 * s, y - 8 * s)], fill=col, width=max(1, int(2.5 * s)))


def qmark(d, c, col, px=40, txt="？"):
    d.text((c[0] * K, c[1] * K), txt, font=F(px), fill=col, anchor="mm", stroke_width=W_(3), stroke_fill=WHITE)


def title(d, xy, txt, col, px=30):
    f = F(px); w = d.textlength(txt, font=f); x, y = xy[0] * K, xy[1] * K
    d.rounded_rectangle([x - w / 2 - 22 * K, y - px * 0.85 * K, x + w / 2 + 22 * K, y + px * 0.85 * K], radius=14 * K, fill=WHITE, outline=col, width=W_(3))
    d.text((x, y), txt, font=f, fill=col, anchor="mm")


# ---------------------------------------------------------------- 字幕（ASS）
def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def mmss(t): return "%d:%04.1f" % (int(t // 60), t % 60)


def wrap_jp(txt, n=28):
    if len(txt) <= n: return txt
    cands = [i + 1 for i, ch in enumerate(txt[:-1]) if ch in "。、" and 6 <= i + 1 <= len(txt) - 4]
    cut = min(cands, key=lambda i: abs(i - len(txt) / 2)) if cands else len(txt) // 2
    return txt[:cut] + "\\N" + txt[cut:]


def narr(path):
    """ナレーションの字幕を 1 枚ずつ（改行入り。長い文は声の間で何枚かに）：[(始まり, 終わり, 文), …]"""
    return SJ.expand(srt_lines(path))


def srt_lines(path):
    out = []
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        Ls = b.split("\n")
        if len(Ls) < 3 or " --> " not in Ls[1]: continue
        def sec(x):
            h, m, r = x.strip().split(":"); s_, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(s_) + int(ms) / 1000
        a, c = Ls[1].split(" --> "); out.append((sec(a), sec(c), " ".join(Ls[2:])))
    return out


ASS_HEAD = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            SJ.STYLE_MAIN,
            "Style: Note,Noto Sans CJK JP,19,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,3,6,0,9,0,24,18,1",
            "Style: Shot,Noto Sans CJK JP,19,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,3,6,0,7,24,0,18,1",
            "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]


# ---------------------------------------------------------------- 効果音
SR = 48000
_rng = np.random.default_rng(7)


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
    nz = lowpass(_rng.normal(0, 1, n), 1800) * np.exp(-t / 0.012) * click
    return amp * (body + nz)


def clank(amp, dur=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * sum(w * np.sin(2 * math.pi * f * t) * np.exp(-t / dd) for f, w, dd in ((820, 1.0, 0.09), (1310, 0.6, 0.06), (2170, 0.35, 0.04)))


def motor(dur, amp, f=150.0):
    n = int(dur * SR); t = np.arange(n) / SR; e = np.minimum(t / 0.15, 1.0) * np.minimum((dur - t) / 0.2, 1.0)
    ph = 2 * math.pi * (f * t + 6 * np.sin(2 * math.pi * 0.7 * t) / (2 * math.pi * 0.7))
    x = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph) + 0.15 * lowpass(_rng.normal(0, 1, n), 900)
    return amp * x * e


def chime(amp, notes=((1568, 1.0, 0.35), (2093, 0.6, 0.25)), dur=0.9):
    n = int(dur * SR); tt = np.arange(n) / SR
    return amp * sum(w * np.sin(2 * math.pi * f * tt) * np.exp(-tt / d) for f, w, d in notes)


def song_loop(path, at=40.04, dur=3.08):
    """第3章からの曲の、継ぎ目なくくり返せる 3.08 秒（8拍）を 48kHz で"""
    import wave
    w = wave.open(path); sr0 = w.getframerate(); w.setpos(int(round(at * sr0))); x = np.frombuffer(w.readframes(int(round(dur * sr0))), np.int16).astype(float) / 32768
    nL = int(round(dur * SR)); loop = np.interp(np.arange(nL) * (len(x) / nL), np.arange(len(x)), x)
    return loop / max(np.abs(loop).max(), 1e-9)
