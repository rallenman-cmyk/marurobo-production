# 16本目 9章（S36〜S38）の 2D：使えない鍵の図（36-03・36-04）・やることの一覧（37：自分でできること／38：お城の側）・
#   スマホに届く番号の吹き出し（37-06）・いつものアプリから入るスマホの図（37-09）・所の札（つながっていない場所・1人1人の鍵）
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜8章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   図は場面のつなぎのあと・札と札のすき間をあけない・章の番号など作る側の言葉を書かない・一覧は出したまま足す）。絵コンテ表：../絵コンテ_v1.md の「9章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import icons16 as IC
from overlays2 import wv, _canvas, _done, _tag, S2, NAVY, RED
from overlays8 import _key, _ease, GOLD, GOLD_D
s, e = T.s, T.e
TEAL = (47, 217, 200); TEAL_D = (20, 150, 140); GREYX = (124, 131, 142); GREYT = (150, 158, 170); BLUE = (74, 123, 224); BLUE_D = (44, 86, 170)

LIST_ME = ["使い回さない", "確かめをもう1つ", "リンクを押さない", "すぐ信じない"]
LIST_CASTLE = ["錠を新しく", "2つ目の確かめ", "予備をはなれた所に", "働く人も使い回さない"]


def _xmark(d, cx, cy, r, a=255):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(238, 240, 243, a))
    w_ = int(r * 0.32)
    for sx in (-1, 1):
        d.line((cx - r * 0.55, cy - sx * r * 0.55, cx + r * 0.55, cy + sx * r * 0.55), fill=GREYX + (a,), width=w_)


def _lock(d, cx, cy, r, body=BLUE, dark=BLUE_D):
    """錠の絵（四角い体と、上の輪。鍵穴）"""
    d.arc((cx - r * 0.55, cy - r * 1.35, cx + r * 0.55, cy - r * 0.15), 180, 360, fill=dark, width=int(r * 0.22))
    d.line((cx - r * 0.55, cy - r * 0.75, cx - r * 0.55, cy - r * 0.3), fill=dark, width=int(r * 0.22))
    d.line((cx + r * 0.55, cy - r * 0.75, cx + r * 0.55, cy - r * 0.3), fill=dark, width=int(r * 0.22))
    d.rounded_rectangle((cx - r, cy - r * 0.4, cx + r, cy + r), radius=int(r * 0.2), fill=body)
    d.ellipse((cx - r * 0.18, cy + r * 0.05, cx + r * 0.18, cy + r * 0.41), fill=(20, 26, 40))
    d.rectangle((cx - r * 0.07, cy + r * 0.3, cx + r * 0.07, cy + r * 0.65), fill=(20, 26, 40))


def unuse_sprite(t, p):
    """36-03〜36-04：左に市場の棚の名札（青緑）と、その上の金色の鍵 →「使えなく」で鍵に灰色の×（「使えない鍵」）。
    36-04：右に新しい錠（青）。「古い鍵」で金色の鍵が錠へすべって差さり、がたがたゆれる →「開かない」で×と「開かない」"""
    W_, H_ = 1000, 330
    im, d = _canvas(W_, H_)
    # 左：名札と鍵
    _tag(d, 230 * S2, 170 * S2, 210 * S2, col=TEAL)
    _key(d, 230 * S2, 62 * S2, 40 * S2)
    if t >= p["t_x"]:
        u = _ease((t - p["t_x"]) / 0.25)
        _xmark(d, 238 * S2, 62 * S2, (30 + 14 * u) * S2)
    if t >= p["t_x"] + 0.1:
        D.ctext(d, (230 * S2, 290 * S2), "使えない鍵", D.font(44 * S2), NAVY)
    # 右：新しい錠と古い鍵
    if t >= p["t_r"]:
        a_ = int(255 * _ease((t - p["t_r"]) / 0.3))
        d.line((500 * S2, 40 * S2, 500 * S2, 290 * S2), fill=(210, 216, 226, a_), width=4 * S2)
        _lock(d, 760 * S2, 150 * S2, 70 * S2)
        if t >= p["t_key"]:
            v = _ease((t - p["t_key"]) / 0.6)
            kx = 560 + v * 95                                  # 鍵の先が鍵穴（760）に届く
            wig = 6 * math.sin((t - p["t_key"] - 0.6) * 30) if t > p["t_key"] + 0.6 and t < p["t_no"] else 0.0
            _key(d, (kx - 30) * S2, (195 + wig) * S2, 40 * S2)
            D.ctext(d, (600 * S2, 290 * S2), "古い鍵", D.font(44 * S2), NAVY)
        if t >= p["t_no"]:
            u = _ease((t - p["t_no"]) / 0.25)
            _xmark(d, 850 * S2, 80 * S2, (30 + 14 * u) * S2)
            D.ctext(d, (850 * S2, 290 * S2), "開かない", D.font(44 * S2), RED)
    return _done(im, W_, H_)


def list_sprite(t, p):
    """やることの一覧：題と、言う時刻に 1 行ずつ足す（出したまま）。いま言っている行は濃い字、前の行は少しうすく"""
    items, ts, title = p["items"], p["ts"], p["title"]
    n = sum(1 for tt in ts if t >= tt)
    W_ = p.get("w", 520); RH = 60
    H_ = 78 + max(1, n) * RH + 12
    im, d = _canvas(W_, H_)
    D.ctext(d, (W_ / 2 * S2, 42 * S2), title, D.font(44 * S2), TEAL_D)
    for i in range(n):
        y = 78 + i * RH + RH / 2
        cur = (i == n - 1)
        col = NAVY if cur else GREYT
        r_ = 22
        d.ellipse(((34 - r_) * S2, (y - r_) * S2, (34 + r_) * S2, (y + r_) * S2), fill=(TEAL if cur else (200, 230, 226)))
        D.ctext(d, (34 * S2, y * S2), str(i + 1), D.font(34 * S2), (255, 255, 255))
        f = D.font(44 * S2); tw = d.textlength(items[i], font=f)
        D.ctext(d, ((70 * S2) + tw / 2, y * S2), items[i], f, col)
    return _done(im, W_, H_)


def code_sprite(t, p):
    """37-06：スマホに届く番号の吹き出し（スマホの絵と 4 けたの数）"""
    W_, H_ = 380, 150
    im, d = _canvas(W_, H_)
    IC.icon(d, "phone", 70 * S2, 75 * S2, 50 * S2, NAVY)
    n = min(4, int(max(0.0, t - p["t0"]) / 0.12) + 1)
    D.ctext(d, (235 * S2, 76 * S2), " ".join("4719"[:n]), D.font(64 * S2), TEAL_D)
    return _done(im, W_, H_)


def phone_sprite(t, p):
    """37-09：スマホの図。アプリの並び →「いつものアプリ」でお店のアプリ（紫のお城の印）に輪 → 押すとお店のページ（上に印・灰色の行・青い帯）"""
    W_, H_ = 300, 520
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=40 * S2, fill=(30, 34, 42, 255))
    x0, y0, x1, y1 = 16, 40, W_ - 16, H_ - 40
    if t < p["t_page"]:
        d.rounded_rectangle((x0 * S2, y0 * S2, x1 * S2, y1 * S2), radius=20 * S2, fill=(150, 196, 230, 255))
        cols = [(255, 255, 255), (255, 214, 120), (130, 210, 170), (240, 140, 120)]
        for i in range(4):
            for j in range(3):
                cx, cy = 66 + j * 84, 110 + i * 96
                if (i, j) == (1, 1):
                    d.rounded_rectangle(((cx - 30) * S2, (cy - 30) * S2, (cx + 30) * S2, (cy + 30) * S2), radius=14 * S2, fill=(250, 251, 253, 255))
                    IC.castle_logo(d, cx * S2, cy * S2, 24 * S2)
                else:
                    d.rounded_rectangle(((cx - 30) * S2, (cy - 30) * S2, (cx + 30) * S2, (cy + 30) * S2), radius=14 * S2, fill=cols[(i + j) % 4] + (255,))
        if t >= p["t_ring"]:
            u = _ease((t - p["t_ring"]) / 0.3); r_ = 44 + 10 * (1 - u)
            d.ellipse(((150 - r_) * S2, (206 - r_) * S2, (150 + r_) * S2, (206 + r_) * S2), outline=(255, 200, 30, 255), width=7 * S2)
    else:
        d.rounded_rectangle((x0 * S2, y0 * S2, x1 * S2, y1 * S2), radius=20 * S2, fill=(250, 251, 253, 255))
        IC.castle_logo(d, 150 * S2, 110 * S2, 44 * S2)
        for k, ww in enumerate((200, 170, 210, 150)):
            d.rounded_rectangle(((150 - ww / 2) * S2, (190 + k * 40) * S2, (150 + ww / 2) * S2, (206 + k * 40) * S2), radius=6 * S2, fill=(200, 206, 214, 255))
        d.rounded_rectangle((60 * S2, 380 * S2, 240 * S2, 430 * S2), radius=24 * S2, fill=(68, 132, 222, 255))
    return im.resize((W_, H_), Image.LANCZOS)


def ev_list9():
    E = []
    add = lambda *a: E.append(a)
    # 36-01：語り手の「？」（右上のすみ）
    add(wv("36-01", "何も") - 0.1, e("36-01") + 0.3, "qmark", dict(pos=(1120, 140), size=150))
    # 36-03〜36-04：使えない鍵の図
    add(wv("36-03", "使えなく") - 0.6, e("36-04") + 0.3, "c9_unuse", dict(t_x=wv("36-03", "使えなく") - 0.1, t_r=s("36-04") + 0.05,
                                                                       t_key=wv("36-04", "古い鍵") - 0.1, t_no=wv("36-04", "開かない") - 0.1))
    # 37：自分でできること（言う時刻に 1 行ずつ。37-11 の終わりまで出したまま）
    add(wv("37-02", "1つ目") - 0.1, e("37-11") + 0.3, "c9_list", dict(title="自分でできること", items=LIST_ME, w=500,
        ts=[wv("37-02", "1つ目") - 0.1, wv("37-05", "2つ目") - 0.1, wv("37-08", "3つ目") - 0.1, wv("37-10", "4つ目") - 0.1]))
    add(wv("37-06", "スマホに届く番号") - 0.1, e("37-06") + 0.3, "c9_code", dict(obj="maru_top", t0=wv("37-06", "スマホに届く番号")))
    add(wv("37-09", "いつものアプリ") - 0.5, e("37-09") + 0.3, "c9_phone", dict(t_ring=wv("37-09", "いつものアプリ") - 0.1, t_page=wv("37-09", "お店のページ") - 0.1))
    # 38：お城の側（38-06 の終わりまで）
    add(wv("38-02", "裏口の錠") - 0.1, e("38-06") + 0.3, "c9_list", dict(title="お城の側", items=LIST_CASTLE, w=560,
        ts=[wv("38-02", "裏口の錠") - 0.1, wv("38-03", "2つ目の確かめ") - 0.1, wv("38-04", "予備の倉庫") - 0.1, wv("38-06", "働く人") - 0.1]))
    add(wv("38-04", "つながっていない") - 0.1, e("38-04") + 0.3, "tag", dict(text="つながっていない場所", obj="i_isle", dy=-110, size=48))
    add(wv("38-07", "1人1人") - 0.1, e("38-07") + 0.3, "tag", dict(text="1人1人の鍵", pos=(640, 110), size=52))
    return E


def sfx_list9():
    L = [(wv("36-03", "使えなく") - 0.1, "thud", 0.3), (wv("36-04", "開かない") - 0.1, "thud", 0.3), (wv("36-04", "古い鍵") + 0.55, "rattle", 0.25)]
    L += [(wv("37-09", "いつものアプリ") - 0.1, "tick", 0.3)]
    return L


def draw9(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    if kind == "c9_unuse":
        spr = unuse_sprite(t, p); _paste(base, spr, 640, 30 + spr.height / 2, k, a)
    elif kind == "c9_list":
        spr = list_sprite(t, p); _paste(base, spr, 24 + spr.width / 2, 24 + spr.height / 2, 1.0 if t - t0 > 0.3 else k, a)     # 左上。行が増えても左上はそのまま
    elif kind == "c9_code":
        q = where(p["obj"], t)
        if q is None: return
        spr = code_sprite(t, p)
        cx = min(max(q[0] + 150, spr.width / 2 + 20), 1260 - spr.width / 2); cy = min(max(q[1] - 120, spr.height / 2 + 20), 520 - spr.height / 2)
        _paste(base, spr, cx, cy, k, a)
    elif kind == "c9_phone":
        spr = phone_sprite(t, p); _paste(base, spr, 1000, 30 + spr.height / 2, k, a)
