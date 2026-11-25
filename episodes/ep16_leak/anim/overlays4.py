# 16本目 4章（S22〜S24）の 2D：値札の小さな絵・透ける箱の小窓・紙とデジタルの写しの図・外へ広がる図・「？」
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜3章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   図は 1 文で 1 段ずつ・語り手の「？」は画面のすみ・場面のつなぎの中で大事な動きを始めない）
#   絵コンテ表：../絵コンテ_v1.md の「4章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
from overlays2 import wv, _canvas, _done, _tag, _arrow, S2, NAVY, RED, WHITE
s, e = T.s, T.e
TEAL = (47, 217, 200); PAPER = (205, 186, 150)
GOLD = (240, 190, 60); GOLD_D = (190, 140, 30)


def _coin(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (255,), outline=GOLD_D + (255,), width=max(2, int(r * 0.14)))
    d.ellipse((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=(255, 226, 140, 255), width=max(2, int(r * 0.1)))


def _glow_tag(d, cx, cy, w, a=1.0):
    """光るデジタルの名札（青緑のふち＋まわりの光）"""
    for k, col in ((3, (226, 250, 247)), (2, (200, 245, 240)), (1, (170, 238, 230))):      # 光は白い板の上の不透明な色で（半透明だと板が抜けて黒く見えた）
        r = w * (0.5 + 0.05 * k)
        d.rounded_rectangle((cx - r, cy - w * 0.315 - w * 0.05 * k, cx + r, cy + w * 0.315 + w * 0.05 * k), radius=int(w * 0.12), fill=col + (255,))
    _tag(d, cx, cy, w, col=TEAL)


def _maru_icon(d, cx, cy, r):
    """まるロボの小さな絵（白い丸に青緑の目）"""
    d.ellipse(((cx - r) * S2, (cy - r) * S2, (cx + r) * S2, (cy + r) * S2), fill=(244, 244, 240, 255), outline=(150, 156, 166, 255), width=3 * S2)
    d.ellipse(((cx - r * 0.45) * S2, (cy - r * 0.45) * S2, (cx + r * 0.45) * S2, (cy + r * 0.45) * S2), fill=(30, 40, 46, 255))
    d.ellipse(((cx - r * 0.3) * S2, (cy - r * 0.3) * S2, (cx + r * 0.3) * S2, (cy + r * 0.3) * S2), fill=(90, 220, 215, 255))


def _paper_tag(d, cx, cy, w):
    """紙の名札：白っぽい紙・右上の角が折れている（確認役：デジタルとふちの色しかちがわなかった）"""
    h = w * 0.63; f = w * 0.16
    pts = [(cx - w / 2, cy - h / 2), (cx + w / 2 - f, cy - h / 2), (cx + w / 2, cy - h / 2 + f), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    d.polygon([(x * S2, y * S2) for x, y in pts], fill=(246, 240, 226, 255), outline=(170, 150, 110, 255), width=3 * S2)
    d.polygon([((cx + w / 2 - f) * S2, (cy - h / 2) * S2), ((cx + w / 2 - f) * S2, (cy - h / 2 + f) * S2), ((cx + w / 2) * S2, (cy - h / 2 + f) * S2)], fill=(214, 200, 170, 255))
    _tag(d, cx * S2, (cy + h * 0.06) * S2, w * 0.7 * S2, col=(206, 192, 160), icons=True)


def _star(d, cx, cy, r, col=(240, 190, 60)):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45; ang = math.pi / 2 + k * math.pi / 5
        pts.append(((cx + rr * math.cos(ang)) * S2, (cy - rr * math.sin(ang)) * S2))
    d.polygon(pts, fill=col + (255,), outline=(170, 120, 20, 255))


def ptag_sprite(t, p):
    """22-07「安いから」：3章の値札（白い札に硬貨 1 つ）の小さな絵"""
    W_, H_ = 170, 230
    im, d = _canvas(W_, H_)
    d.rounded_rectangle((25 * S2, 22 * S2, 145 * S2, 208 * S2), radius=10 * S2, fill=(255, 246, 214, 255), outline=(150, 120, 70, 255), width=4 * S2)
    d.ellipse((77 * S2, 34 * S2, 93 * S2, 50 * S2), fill=(120, 110, 96, 255))
    _coin(d, 85 * S2, 135 * S2, 38 * S2)
    return _done(im, W_, H_)


def xray_sprite(t, p):
    """23-05：3章で影が持っていった箱が透けて、中に同じ青緑の名札（小窓）。左に、箱を持つ影の形"""
    W_, H_ = 470, 330
    im, d = _canvas(W_, H_)
    # 影（黒い形。輪郭は紫）
    d.ellipse((40 * S2, 60 * S2, 120 * S2, 140 * S2), fill=(24, 22, 40, 255), outline=(110, 90, 220, 255), width=3 * S2)
    d.rounded_rectangle((30 * S2, 130 * S2, 130 * S2, 300 * S2), radius=40 * S2, fill=(24, 22, 40, 255), outline=(110, 90, 220, 255), width=3 * S2)
    # 透けた箱（段ボールの色をうすく、ふちは濃く）
    bx0, by0, bx1, by1 = 150, 95, 440, 290
    d.rectangle((bx0 * S2, by0 * S2, bx1 * S2, by1 * S2), fill=(236, 220, 192, 255), outline=(140, 100, 60, 255), width=5 * S2)      # 透けた箱＝うすい段ボールの色（半透明は黒く抜けた）
    d.line((bx0 * S2, by0 * S2, (bx0 + 40) * S2, (by0 - 40) * S2, (bx1 + 0) * S2, (by0 - 40) * S2, bx1 * S2, by0 * S2), fill=(140, 100, 60, 255), width=5 * S2)
    for k in range(3):        # 中の名札（青緑）
        _tag(d, (205 + 85 * k) * S2, (195 + (k % 2) * 18) * S2, 80 * S2, col=TEAL)
    return _done(im, W_, H_)


def copy_sprite(t, p):
    """24-01〜24-06：左＝紙の名札、右＝デジタルの名札。1 文で 1 段ずつ（取られて 0 枚 → 写しが出る → 2 枚・4 枚 → 入れかわって「？」 → 1 枚取られて 3 枚）"""
    W_, H_ = 1120, 420
    im, d = _canvas(W_, H_)
    d.line((560 * S2, 30 * S2, 560 * S2, 390 * S2), fill=(200, 205, 214, 255), width=4 * S2)
    D.ctext(d, (280 * S2, 50 * S2), "紙", D.font(56 * S2), NAVY)
    D.ctext(d, (840 * S2, 50 * S2), "デジタル", D.font(56 * S2), NAVY)
    _maru_icon(d, 75, 330, 34)                               # 取り返したまるロボ（左下）
    # 左：紙の名札 1 枚 → 取られると、点線のわくと「0枚」
    u = 0.0 if t < p["t_lt"] else min(1.0, (t - p["t_lt"]) / 0.7)
    cx, cy = 280, 205
    if u > 0:
        for k in range(12):        # 点線のわく（いまいた所）
            a0 = k / 12.0; x0 = cx - 95 + 190 * a0
            d.line((x0 * S2, (cy - 60) * S2, (x0 + 9) * S2, (cy - 60) * S2), fill=(150, 160, 176, 255), width=3 * S2)
            d.line((x0 * S2, (cy + 60) * S2, (x0 + 9) * S2, (cy + 60) * S2), fill=(150, 160, 176, 255), width=3 * S2)
        for k in range(7):
            y0 = cy - 60 + 120 * k / 7.0
            d.line(((cx - 95) * S2, y0 * S2, (cx - 95) * S2, (y0 + 9) * S2), fill=(150, 160, 176, 255), width=3 * S2)
            d.line(((cx + 95) * S2, y0 * S2, (cx + 95) * S2, (y0 + 9) * S2), fill=(150, 160, 176, 255), width=3 * S2)
    if u < 1.0:
        _paper_tag(d, cx - 160 * u, cy + 110 * u, 190 * (1 - 0.6 * u))      # まるロボの手もとへ（確認役：消えると「なくなった」に見えた）
    D.ctext(d, (cx * S2, 340 * S2), "0枚" if u >= 0.5 else "1枚", D.font(52 * S2), NAVY)      # 赤をやめる（取り返せた＝良いこと）
    # 右：デジタルの名札
    P2 = [(-90, 0), (90, 0)]; P4 = [(-85, -50), (85, -50), (-85, 50), (85, 50)]      # 見出しと数の字に重ならない（v0 の点検）
    rx, ry = 840, 200
    if t < p["t_c1"]:
        pos = [(0, 0)]; wd = 190
    elif t < p["t_4"]:
        v = min(1.0, (t - p["t_c1"]) / 0.6)            # 元の 1 枚は残ったまま、写しが右へ出る
        pos = [(-90 * v, 0), (90 * v, 0)]; wd = 190 - 55 * v
        ghost = t < p["t_2"]                             # 24-03 は写しを点線のわくだけ（確認役：「2枚に」の時刻に絵が変わらなかった）→「2枚に」ではっきり
    else:
        v = min(1.0, (t - p["t_4"]) / 0.6)
        pos = [(P2[i % 2][0] + (P4[i][0] - P2[i % 2][0]) * v, P4[i][1] * v) for i in range(4)]; wd = 135 - 15 * v
        if t >= p["t_sh"]:                               # 入れかわって並び直す（どれが元か分からない）
            w_ = min(1.0, (t - p["t_sh"]) / 2.0); order = [3, 0, 1, 2]      # ゆっくり入れかえる
            pos = [(P4[i][0] + (P4[order[i]][0] - P4[i][0]) * math.sin(math.pi * w_ / 2), P4[i][1] + (P4[order[i]][1] - P4[i][1]) * math.sin(math.pi * w_ / 2)) for i in range(4)]
    gone = 0.0 if t < p["t_take"] else min(1.0, (t - p["t_take"]) / 0.7)
    ghost = p["t_c1"] <= t < p["t_2"]
    for i, (dx, dy) in enumerate(pos):
        if ghost and i == 1:
            x0_, y0_ = rx + dx - wd * 0.5, ry + dy - wd * 0.315
            for q_ in range(10):
                fx = q_ / 10.0
                d.line(((x0_ + wd * fx) * S2, y0_ * S2, (x0_ + wd * fx + wd * 0.05) * S2, y0_ * S2), fill=(47, 217, 200, 255), width=3 * S2)
                d.line(((x0_ + wd * fx) * S2, (y0_ + wd * 0.63) * S2, (x0_ + wd * fx + wd * 0.05) * S2, (y0_ + wd * 0.63) * S2), fill=(47, 217, 200, 255), width=3 * S2)
            for q_ in range(6):
                fy = q_ / 6.0
                for xx in (x0_, x0_ + wd):
                    d.line((xx * S2, (y0_ + wd * 0.63 * fy) * S2, xx * S2, (y0_ + wd * 0.63 * fy + wd * 0.05) * S2), fill=(47, 217, 200, 255), width=3 * S2)
            continue
        if i == 0 and gone > 0:
            if gone >= 1.0: continue
            dx += (1035 - rx - dx) * gone; dy += (330 - ry - dy) * gone; wd = wd * (1 - 0.5 * gone)
        pulse = 1.0 + (0.08 * math.sin(min(1.0, (t - p["t_2"]) / 0.5) * math.pi) if p["t_2"] <= t < p["t_2"] + 0.5 else 0.0)
        _glow_tag(d, (rx + dx) * S2, (ry + dy) * S2, wd * pulse * S2)
        if i == 0 and t < p["t_sh"] - 0.2: _star(d, rx + dx + wd * 0.42, ry + dy - wd * 0.3, 16)      # 元の 1 枚の印（入れかわる前に消す）
    if p["t_q"] <= t < p["t_take"]:
        D.ctext(d, ((rx + 232) * S2, (ry + 5) * S2), "？", D.font(96 * S2), RED)
    if t >= p["t_take"] - 0.3: _maru_icon(d, 1075, 330, 34)
    n = 1 if t < p["t_2"] else (2 if t < p["t_4"] else (4 if gone < 0.5 else 3))
    D.ctext(d, (rx * S2, 340 * S2), "%d枚" % n, D.font(52 * S2), NAVY)
    return _done(im, W_, H_)


def out_sprite(t, p):
    """24-09：1 枚の名札から、矢印で外へたくさんの写し。下に「一度出ると、取り戻せない」"""
    W_, H_ = 1120, 430
    im, d = _canvas(W_, H_)
    cx, cy = 560, 210
    u = 0.0 if t < p["t_go"] else min(1.0, (t - p["t_go"]) / 1.0)
    for k in range(6):
        ang = math.radians([-160, -120, -60, -20, 20, 160][k])      # 下は字のために空ける。わくの中に収める（v0 の点検：はしの名札が切れた）
        r1 = 105; r2 = 105 + 175 * u
        x1, y1 = cx + r1 * math.cos(ang) * 1.5, cy + r1 * math.sin(ang) * 0.6
        x2, y2 = cx + r2 * math.cos(ang) * 1.5, cy + r2 * math.sin(ang) * 0.6
        if u > 0.05:
            L_ = math.hypot(x2 - x1, y2 - y1)
            if L_ > 90:          # 矢の先は名札の手前で止める（確認役：名札の絵が矢じりに重なり「T」の形に見えた）
                ex, ey = x1 + (x2 - x1) * (L_ - 70) / L_, y1 + (y2 - y1) * (L_ - 70) / L_
                _arrow(d, x1, y1, ex, ey, RED)
            _glow_tag(d, x2 * S2, y2 * S2, 100 * S2)
    for q_ in range(28):        # 元の場所（まるロボの手もと）を点線のわくで。写しは、このわくの外へ出ていく（確認役：「外」がなかった）
        ang_ = 2 * math.pi * q_ / 28; ang2 = ang_ + math.pi / 40
        d.line(((cx + 125 * math.cos(ang_)) * S2, (cy + 78 * math.sin(ang_)) * S2, (cx + 125 * math.cos(ang2)) * S2, (cy + 78 * math.sin(ang2)) * S2), fill=(120, 130, 150, 255), width=4 * S2)
    _glow_tag(d, cx * S2, cy * S2, 150 * S2)
    if t >= p["t_lbl"]:
        D.ctext(d, (560 * S2, 385 * S2), "一度出ると、取り戻せない", D.font(50 * S2), RED)
    return _done(im, W_, H_)


def ev_list4():
    E = []
    add = lambda *a: E.append(a)
    add(s("22-02") - 0.05, wv("22-02", "とびこむ") + 0.3, "ring", dict(obj="leftbox", r=80, col=RED))      # 残っていた自分の箱（確認役：どの箱か分からなかった）
    add(wv("22-07", "安いから") - 0.6, e("22-07") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(wv("22-07", "安いから") - 0.1, e("22-07") + 0.3, "c4_ptag", dict(obj="maru_top"))      # 「？」のすぐ右（確認役：画面の右のふちで遠かった）
    add(s("23-01") + 0.3, e("23-01") + 0.3, "qmark", dict(pos=(1120, 140), size=150))      # 語り手の問い（画面のすみ）
    add(wv("23-04", "まだ何枚") - 0.1, e("23-04") + 0.3, "ring", dict(obj="copies", r=170, col=RED))
    add(s("23-05") + 0.2, e("23-05") + 0.4, "c4_xray", {})
    add(wv("23-06", "どういう") - 0.3, e("23-06") + 0.3, "bubble", dict(obj="maru_top", icon="?", lift=90))      # 確認役：頭の球に重なった
    add(s("24-01") - 0.05, e("24-06") + 0.3, "c4_copy", dict(t_lt=wv("24-02", "取り返せば") - 0.1, t_c1=wv("24-03", "写しても") - 0.1,
                                                            t_2=wv("24-04", "2枚に") - 0.1, t_4=wv("24-04", "4枚に") - 0.1, t_sh=s("24-05") + 0.3,
                                                            t_q=wv("24-05", "見分け") - 0.1, t_take=wv("24-06", "1枚取り返し") - 0.1))
    add(s("24-09") - 0.05, e("24-09") + 0.3, "c4_out", dict(t_go=wv("24-09", "外に出た") - 0.2, t_lbl=wv("24-09", "取り戻せない") - 0.2))
    add(wv("24-10", "どうなる") - 0.2, e("24-10") + 0.3, "qmark", dict(pos=(1120, 140), size=150))
    return E


def sfx_list4():
    L = [(wv("24-02", "取り返せば"), "swish", 0.2)]
    L.append((wv("24-03", "写しても") + 0.1, "swish", 0.25))
    L.append((wv("24-04", "2枚に") - 0.1, "tick", 0.3)); L.append((wv("24-04", "4枚に") - 0.1, "tick", 0.3))      # 図が分かれる時刻（pop は声のすき間へずらされ、図より 0.3 秒早かった）
    L.append((wv("24-06", "1枚取り返し"), "swish", 0.2))
    return L


def draw4(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    if kind in ("c4_copy", "c4_out"):
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(110 * a))))
        spr = copy_sprite(t, p) if kind == "c4_copy" else out_sprite(t, p)
        _paste(base, spr, 640, 30 + spr.height / 2, k, a)
    elif kind == "c4_ptag":
        q = where(p["obj"], t) if p.get("obj") else None
        x_, y_ = (q[0] + 150, max(130, q[1] - 95)) if q else (1050, 230)
        _paste(base, ptag_sprite(t, p), x_, y_, k, a)
    elif kind == "c4_xray": _paste(base, xray_sprite(t, p), 1000, 200, k, a)
