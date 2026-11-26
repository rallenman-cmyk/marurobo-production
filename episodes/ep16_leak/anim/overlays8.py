# 16本目 8章（S33〜S35）の 2D：想像の色・お店そっくりの入力の画面（＊が入り、鍵に変わって飛ぶ）・1章の場面の小窓・
#   2 つの裏口の見比べ・所の名の札・名札の数が増える図
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜7章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   図は場面のつなぎのあと・札と札のすき間をあけない）。絵コンテ表：../絵コンテ_v1.md の「8章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import icons16 as IC
from overlays2 import wv, _canvas, _done, _tag, S2, NAVY, RED
s, e = T.s, T.e
TEAL = (47, 217, 200); GOLD = (201, 162, 74); GOLD_D = (150, 116, 40); GREYB = (200, 206, 216)


def _ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def _key(d, cx, cy, r, col=GOLD, dk=GOLD_D):
    d.ellipse((cx - r * 1.4, cy - r * 0.5, cx - r * 0.4, cy + r * 0.5), outline=col + (255,), width=int(r * 0.28))
    d.rectangle((cx - r * 0.45, cy - r * 0.13, cx + r * 1.4, cy + r * 0.13), fill=col + (255,))
    for dx in (0.85, 1.25): d.rectangle((cx + r * dx - r * 0.1, cy + r * 0.1, cx + r * dx + r * 0.1, cy + r * 0.5), fill=dk + (255,))


def login_sprite(t, p):
    """33-01〜33-02：お店そっくりの入力の画面（印・灰色の帯・「パスワード」の欄・ボタン）。＊が 1 つずつ入る → 33-02 で＊が金色の鍵に変わり、右へ飛んで消える"""
    W_, H_ = 760, 400
    im, d = _canvas(W_, H_)
    IC.castle_logo(d, 70 * S2, 60 * S2, 34 * S2)
    d.rounded_rectangle((120 * S2, 46 * S2, 340 * S2, 74 * S2), radius=14 * S2, fill=GREYB + (255,))
    D.ctext(d, (W_ / 2 * S2, 140 * S2), "パスワード", D.font(48 * S2), NAVY)
    d.rounded_rectangle((150 * S2, 180 * S2, (W_ - 150) * S2, 260 * S2), radius=14 * S2, outline=(150, 160, 176, 255), width=4 * S2, fill=(255, 255, 255, 255))
    u_k = _ease((t - p["t_key"]) / 0.4)
    n = sum(1 for tt in p["stars"] if t >= tt)
    if u_k < 1.0 and n:
        D.ctext(d, (W_ / 2 * S2, 222 * S2), "＊" * n, D.font(56 * S2), (NAVY[0], NAVY[1], NAVY[2], int(255 * (1 - u_k))))
    d.rounded_rectangle((250 * S2, 295 * S2, (W_ - 250) * S2, 360 * S2), radius=30 * S2, fill=(68, 132, 222, 255))
    D.ctext(d, (W_ / 2 * S2, 328 * S2), "入る", D.font(44 * S2), (255, 255, 255))
    if t >= p["t_key"]:
        v = _ease((t - p["t_fly"]) / 0.7) if t >= p["t_fly"] else 0.0
        x = W_ / 2 + v * (W_ / 2 + 200); y = 222 - 120 * math.sin(math.pi * v)
        if x < W_ + 150: _key(d, x * S2, y * S2, 40 * S2 * max(0.2, u_k))
    return _done(im, W_, H_)


def pair_sprite(t, p, frame_of):
    """34-05：左に 1章の最初のお城の裏口の鍵、右にいまの別のお城の裏口の鍵（描いた下書きから）。あいだに「＝」、下に「だまし取られた鍵？」"""
    W_, H_ = 1200, 460
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, (clip, st, lab) in enumerate(((p["l_clip"], p["l_t"], "最初のお城"), (p["r_clip"], p["r_t"], "別のお城"))):
        x0 = 20 + k * 640
        d.rounded_rectangle((x0, 50, x0 + 540, 50 + 316), radius=16, fill=(255, 255, 255, 255))
        fr = frame_of(clip, st) if frame_of else None
        if fr is not None: im.paste(fr.convert("RGB").resize((528, 297), Image.LANCZOS), (x0 + 6, 56))
        D.ctext(d, (x0 + 270, 24), lab, D.font(44), (255, 255, 255))
    D.ctext(d, (W_ / 2, 210), "＝", D.font(80), (255, 255, 255))
    if t >= p["t_q"]:
        d.rounded_rectangle((W_ / 2 - 230, 385, W_ / 2 + 230, 450), radius=30, fill=(255, 255, 255, 245))
        D.ctext(d, (W_ / 2, 417), "だまし取られた鍵？", D.font(48), RED)
    return im


def count_sprite(t, p):
    """35-05：輪が 1 周するたびに、名札の数が増える（1 → 3 → 9）。行ごとに左から「1周」「2周」「3周」"""
    W_, H_ = 980, 360
    im, d = _canvas(W_, H_)
    for r, (n, lab) in enumerate(((1, "1周"), (3, "2周"), (9, "3周"))):
        if t < p["t"][r]: continue
        y = 70 + r * 105
        D.ctext(d, (90 * S2, y * S2), lab, D.font(44 * S2), NAVY)
        for k in range(n):
            u = _ease((t - p["t"][r] - 0.06 * k) / 0.25)
            if u <= 0: continue
            _tag(d, (210 + k * 84) * S2, y * S2, 70 * S2 * u, col=TEAL)
    return _done(im, W_, H_)


def ev_list8():
    E = []
    add = lambda *a: E.append(a)
    # 想像の色（33-01〜33-06）：章の頭のつなぎのあとから、34-01 のつなぎが終わるまで
    add(s("33-01") + 0.8, s("34-01") + 0.85, "tint", {})
    t_st = [wv("33-01", "パスワード") + 0.05 + 0.22 * k for k in range(6)]
    add(s("33-01") + 0.8, s("33-02") + 1.4, "c8_login", dict(stars=t_st, t_key=s("33-02") + 0.1, t_fly=s("33-02") + 0.5))
    add(wv("33-04", "会社で働く人") - 0.1, e("33-04") + 0.3, "tag", dict(text="会社で働く人の鍵", pos=(640, 110), size=52))
    add(wv("33-06", "別のお城") - 0.1, e("33-06") + 0.3, "tag", dict(text="別のお城", pos=(640, 110), size=52))
    # 34：1章の場面の小窓（鍵を取り出す → 鍵を差す）。小窓は左上。名の札はその下
    add(s("34-01") + 0.85, s("34-02") + 0.85, "pip_clip", dict(clip="N12b", src_t=s("12-03") + 0.2))      # 小窓の中身は、場面のつなぎが終わってから替える
    add(s("34-02") + 0.85, s("34-05") + 0.05, "pip_clip", dict(clip="N12c", src_t=s("12-05") + 0.2))
    add(s("34-01") + 0.85, s("34-05") + 0.05, "tag", dict(text="1章：最初のお城", pos=(308, 380), size=44))
    add(s("34-02") + 0.85, s("34-02") + 2.2, "bubble", dict(obj="maru_top", icon="!"))      # 場面のつなぎのあと（「思い出してください」の間）
    add(wv("34-03", "ID") - 0.1, e("34-03") + 0.3, "tag", dict(text="働く人のIDとパスワード", pos=(930, 120), size=48))
    add(wv("34-04", "どこから") - 0.2, e("34-04") + 0.3, "qmark", dict(pos=(480, 150), size=130))
    add(s("34-05") + 0.05, s("35-01") + 0.8, "c8_pair", dict(l_clip="N12c", l_t=s("12-05") + 0.9, r_clip="N34c", r_t=s("34-04") + 1.0, t_q=wv("34-05", "だまし取られた") - 0.1))
    # 35：所の名の札（上から見た輪の台の上に）
    for nm, obj, t_ in (("お城", "st_castle", wv("35-02", "お城")), ("市場", "st_market", wv("35-02", "市場")), ("影の机", "st_desk", wv("35-02", "影の机")),
                        ("町のドア・メール", "st_town", wv("35-03", "町のドア")), ("次のお城", "st_next", wv("35-03", "次のお城"))):
        add(t_ - 0.1, wv("35-04", "輪になって") - 0.1, "tag", dict(text=nm, obj=obj, dy=-70, size=44))      # 輪の札が出たら下げる（v20 の点検：上の「お城」の札と重なった）
    add(wv("35-04", "輪になって") - 0.1, e("35-04") + 0.3, "tag", dict(text="輪になって回っている", pos=(640, 110), size=52))
    add(s("35-05") + 0.05, e("35-05") + 0.3, "c8_count", dict(t=[s("35-05") + 0.2, wv("35-05", "回るたびに") + 0.6, wv("35-05", "増えて") - 0.1]))
    return E


def sfx_list8():
    L = [(t_, "typing", 0.2) for t_ in [wv("33-01", "パスワード") + 0.05]]
    L += [(s("33-02") + 0.5, "swish", 0.35)]
    L += [(wv("35-05", "回るたびに") + 0.6, "pop", 0.3), (wv("35-05", "増えて") - 0.1, "pop", 0.3)]
    return L


def draw8(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a, frame_of=None):
    k, a = _pop_k, _pop_a
    if kind == "c8_login":
        spr = login_sprite(t, p); _paste(base, spr, 640, 40 + spr.height / 2, k, a)
    elif kind == "c8_pair":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(120 * a))))
        spr = pair_sprite(t, p, frame_of); _paste(base, spr, 640, 20 + spr.height / 2, k, a)
    elif kind == "c8_count":
        spr = count_sprite(t, p); _paste(base, spr, 640, 40 + spr.height / 2, k, a)
