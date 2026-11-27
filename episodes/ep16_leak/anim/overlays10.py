# 16本目 まとめ・オチ（S39〜S40）の 2D：まとめの札（問いは黄色の札、答えは小さな絵と短い言葉。言う時刻に 1 つずつ足し、出したまま）・
#   当選メールの札（7章と同じ形。プレゼントの箱の絵）・「ぽいっ」でメールがごみ箱の絵へ飛ぶ
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜9章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   図は場面のつなぎのあと・字幕と同じ文は出さない・章の番号など作る側の言葉を書かない）。絵コンテ表：../絵コンテ_v1.md の「まとめ・オチ」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import icons16 as IC
from overlays2 import wv, _canvas, _done, _tag, S2, NAVY, RED
from overlays8 import _key, _ease, GOLD, GOLD_D
from overlays9 import _lock
s, e = T.s, T.e
TEAL = (47, 217, 200); TEAL_D = (20, 150, 140); YEL = (255, 206, 60); BROWN = (122, 85, 54); GREYB = (200, 206, 216)


def _qtag(d, x, y, text):
    """黄色の問いの札（左はし x、まん中の高さ y）"""
    f = D.font(44 * S2); w_ = d.textlength(text, font=f) / S2 + 40
    d.rounded_rectangle((x * S2, (y - 32) * S2, (x + w_) * S2, (y + 32) * S2), radius=32 * S2, fill=YEL + (255,))
    D.ctext(d, ((x + w_ / 2) * S2, y * S2), text, f, NAVY)
    return x + w_


def _door(d, cx, cy, r):
    """古い裏口の絵：茶色の扉と、錆びた錠"""
    d.rounded_rectangle(((cx - r * 0.6) * S2, (cy - r) * S2, (cx + r * 0.6) * S2, (cy + r) * S2), radius=int(r * 0.1 * S2), fill=BROWN + (255,))
    d.rectangle(((cx - r * 0.6) * S2, (cy - r * 0.45) * S2, (cx + r * 0.6) * S2, (cy - r * 0.32) * S2), fill=(96, 66, 40, 255))
    _lock(d, (cx + r * 0.28) * S2, (cy + r * 0.15) * S2, r * 0.25 * S2, body=(150, 96, 56), dark=(110, 90, 70))


def _stall(d, cx, cy, r):
    """市場の屋根（しまの日よけ）と台"""
    for k in range(5):
        x0 = cx - r + k * r * 0.4
        d.rectangle((x0 * S2, (cy - r * 0.6) * S2, (x0 + r * 0.4) * S2, (cy - r * 0.15) * S2), fill=((224, 106, 90) if k % 2 == 0 else (255, 255, 255)) + (255,))
    d.rectangle(((cx - r) * S2, (cy - r * 0.6) * S2, (cx + r) * S2, (cy - r * 0.15) * S2), outline=(160, 80, 70, 255), width=2 * S2)
    d.rectangle(((cx - r * 0.85) * S2, (cy + r * 0.2) * S2, (cx + r * 0.85) * S2, (cy + r * 0.7) * S2), fill=(138, 106, 74, 255))


def _ring(d, cx, cy, r, lit=1.0, phase=0.0):
    """輪の絵：点が輪になって並び、光が 1 周する"""
    n = 12
    for k in range(n):
        a = -math.pi / 2 + 2 * math.pi * k / n
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        on = ((k / n - phase) % 1.0) < 0.25
        c = TEAL if on else (170, 220, 214)
        rr = r * (0.16 if on else 0.11)
        d.ellipse(((x - rr) * S2, (y - rr) * S2, (x + rr) * S2, (y + rr) * S2), fill=c + (255,))


def _letter(d, cx, cy, r):
    IC.icon(d, "mail", cx * S2, cy * S2, r * S2, NAVY)


def summary_sprite(t, p):
    """まとめの札：4 行。絵の下に短い言葉。行と絵は言う時刻に出し、出したまま（行がふえると札が下へのびる）"""
    W_ = 950
    rows = [p["t_q1"], p["t_q2"], p["t_r3"], p["t_r4"]]
    n = sum(1 for tt in rows if t >= tt)
    H_ = [40, 160, 310, 410, 520][n]
    im, d = _canvas(W_, H_)
    def show(tt): return t >= tt
    def pop(tt): return min(1.0, _ease((t - tt) / 0.25))
    LB = D.font(44 * S2)
    # 1 行目：どこから？ → 古い裏口・漏れた鍵（絵の下に言葉）
    if show(p["t_q1"]):
        x = _qtag(d, 28, 80, "どこから？")
        for k, (tt, lab, kind) in enumerate(((p["t_a1"][0], "古い裏口", "door"), (p["t_a1"][1], "漏れた鍵", "key"))):
            if not show(tt): continue
            cx = x + 130 + k * 230; u = pop(tt)
            if kind == "door": _door(d, cx, 58, 34 * u)
            else: _key(d, cx * S2, 58 * S2, 34 * u * S2)
            D.ctext(d, (cx * S2, 120 * S2), lab, LB, NAVY)
    # 2 行目：どこへ？ → 売られる・増える・合わさる・戻る
    if show(p["t_q2"]):
        x = _qtag(d, 28, 230, "どこへ？")
        items = (("売られる", "stall"), ("増える", "copies"), ("合わさる", "merge"), ("戻る", "mail"))
        for k, ((lab, kind), tt) in enumerate(zip(items, p["t_a2"])):
            if not show(tt): continue
            cx = x + 110 + k * 185; u = pop(tt); cy = 205
            if kind == "stall": _stall(d, cx, cy + 6, 44 * u)
            elif kind == "copies":
                for j in range(3): _tag(d, (cx - 22 + j * 16) * S2, (cy - 8 + j * 7) * S2, 56 * u * S2, col=TEAL)
            elif kind == "merge":
                _tag(d, (cx - 14) * S2, (cy - 6) * S2, 58 * u * S2, col=TEAL); _tag(d, (cx + 14) * S2, (cy + 8) * S2, 58 * u * S2, col=(240, 148, 58))
            else: _letter(d, cx, cy, 30 * u)
            D.ctext(d, (cx * S2, 268 * S2), lab, LB, NAVY)
    # 3 行目：輪と「増えて、回る」
    if show(p["t_r3"]):
        ph = ((t - p["t_r3"]) / 1.6) % 1.0
        _ring(d, 80, 358, 42, phase=ph)
        D.ctext(d, (330 * S2, 358 * S2), "増えて、回る", D.font(52 * S2), NAVY)
    # 4 行目：使えなくする
    if show(p["t_r4"]):
        u = pop(p["t_r4"])
        d.rounded_rectangle((28 * S2, 420 * S2, (W_ - 28) * S2, 500 * S2), radius=40 * S2, fill=(210, 248, 243, int(255 * u)), outline=TEAL + (int(255 * u),), width=5 * S2)
        D.ctext(d, (W_ / 2 * S2, 460 * S2), "使えなくする", D.font(64 * S2), TEAL_D + (int(255 * u),))
    return _done(im, W_, H_)


def win_sprite(t, p):
    """40-03：当選メールの札（プレゼントの箱の絵・灰色の帯・「まるロボ様」・「おめでとうございます！」・「当選しました！」）"""
    W_, H_ = 760, 330
    im, d = _canvas(W_, H_)
    cx, cy, r = 62, 58, 30                                       # プレゼントの箱
    d.rectangle(((cx - r) * S2, (cy - r * 0.6) * S2, (cx + r) * S2, (cy + r) * S2), fill=(226, 76, 66, 255))
    d.rectangle(((cx - 6) * S2, (cy - r * 0.6) * S2, (cx + 6) * S2, (cy + r) * S2), fill=(255, 206, 60, 255))
    d.ellipse(((cx - 18) * S2, (cy - r - 6) * S2, (cx - 2) * S2, (cy - r * 0.6 + 2) * S2), outline=(255, 206, 60, 255), width=4 * S2)
    d.ellipse(((cx + 2) * S2, (cy - r - 6) * S2, (cx + 18) * S2, (cy - r * 0.6 + 2) * S2), outline=(255, 206, 60, 255), width=4 * S2)
    d.rounded_rectangle((110 * S2, 44 * S2, 330 * S2, 72 * S2), radius=14 * S2, fill=GREYB + (255,))
    D.ctext(d, (W_ / 2 * S2, 135 * S2), "まるロボ様", D.font(52 * S2), NAVY)
    D.ctext(d, (W_ / 2 * S2, 205 * S2), "おめでとうございます！", D.font(48 * S2), NAVY)
    D.ctext(d, (W_ / 2 * S2, 270 * S2), "当選しました！", D.font(56 * S2), RED)
    return _done(im, W_, H_)


def trash_sprite(lid=0.0):
    """ごみ箱の絵（灰色の箱としま、ふた）。lid：ふたが少し開く"""
    W_, H_ = 170, 190
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    g = (120, 128, 140, 255)
    d.polygon([(30 * S2, 60 * S2), (140 * S2, 60 * S2), (128 * S2, 180 * S2), (42 * S2, 180 * S2)], fill=g)
    for x in (62, 85, 108): d.line((x * S2, 75 * S2, x * S2, 165 * S2), fill=(170, 178, 190, 255), width=5 * S2)
    a = -25 * lid
    lidim = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); ld = ImageDraw.Draw(lidim)
    ld.rounded_rectangle((22 * S2, 40 * S2, 148 * S2, 56 * S2), radius=6 * S2, fill=g); ld.rectangle((70 * S2, 28 * S2, 100 * S2, 40 * S2), fill=g)
    lidim = lidim.rotate(a, center=(22 * S2, 56 * S2))
    im.alpha_composite(lidim)
    return im.resize((W_, H_), Image.LANCZOS)


def ev_list10():
    E = []
    add = lambda *a: E.append(a)
    t_q1 = wv("39-01", "どこから") - 0.1
    add(wv("39-01", "まとめ") - 0.1, e("39-07") + 0.5, "c10_sum", dict(
        t_q1=t_q1, t_a1=[wv("39-02", "裏口") - 0.1, wv("39-02", "漏れた鍵") - 0.1],
        t_q2=wv("39-03", "どこへ") - 0.1,
        t_a2=[wv("39-04", "売られ") - 0.1, wv("39-04", "写されて") - 0.1, wv("39-04", "合わさって") - 0.1, wv("39-05", "戻ってくる") - 0.1],
        t_r3=wv("39-06", "増えて") - 0.1, t_r4=wv("39-07", "使えなくする") - 0.1))
    t_p = wv("40-05", "ぽいっ")
    add(wv("40-03", "おめでとう") - 0.1, t_p + 0.75, "c10_win", dict(t_p=t_p))
    add(t_p - 0.4, e("40-05") + 0.3, "c10_trash", dict(t_p=t_p))
    return E


def sfx_list10():
    L = [(x, "pop", 0.25) for x in (wv("39-02", "裏口") - 0.1, wv("39-02", "漏れた鍵") - 0.1, wv("39-04", "売られ") - 0.1, wv("39-04", "写されて") - 0.1,
                                     wv("39-04", "合わさって") - 0.1, wv("39-05", "戻ってくる") - 0.1)]
    return L


def draw10(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    if kind == "c10_sum":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(110 * a))))
        spr = summary_sprite(t, p); _paste(base, spr, 30 + spr.width / 2, 30 + spr.height / 2, 1.0 if t - t0 > 0.3 else k, a)
    elif kind == "c10_win":
        spr = win_sprite(t, p)
        tp = p["t_p"]
        if t < tp: _paste(base, spr, 640, 30 + spr.height / 2, k, a)
        else:                                                        # ぽいっ：右下のごみ箱へ、小さくなりながら飛ぶ
            u = _ease((t - tp) / 0.6)
            x = 640 + (1110 - 640) * u; y = 30 + spr.height / 2 + (420 - (30 + spr.height / 2)) * u - 120 * math.sin(math.pi * u)
            if u < 0.98: _paste(base, spr, x, y, max(0.06, 1.0 - 0.94 * u), 1.0)
    elif kind == "c10_trash":
        tp = p["t_p"]; lid = 1.0 if tp - 0.1 <= t <= tp + 0.7 else 0.0
        _paste(base, trash_sprite(lid), 1110, 430, k, a)
