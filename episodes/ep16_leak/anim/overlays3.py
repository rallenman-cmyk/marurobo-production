# 16本目 3章（S18〜S21）の 2D：地図・検索の窓・売り買い・まとめ売りの図・印の輪・「？」
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは overlays2.py と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上）
#   2章の直しを最初から入れる：図は 1 文で 1 段ずつ出し、出ている段だけの高さ・矢じりは線の向き（overlays2._arrow）・×の横に理由・語り手の「？」は画面のすみ
#   絵コンテ表：../絵コンテ_v1.md の「3章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import overlays2 as O2
from overlays2 import wv, _canvas, _done, _tag, _arrow, _xbadge, S2, NAVY, RED, GREY, TEALC, WHITE
s, e = T.s, T.e
GOLD = (240, 190, 60); GOLD_D = (190, 140, 30)


def _coin(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (255,), outline=GOLD_D + (255,), width=max(2, int(r * 0.14)))
    d.ellipse((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=(255, 226, 140, 255), width=max(2, int(r * 0.1)))


def _envelope(d, cx, cy, w):
    h = w * 0.66
    d.rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), fill=(250, 250, 252, 255), outline=NAVY + (255,), width=max(2, int(w * 0.06)))
    d.line((cx - w / 2, cy - h / 2, cx, cy + h * 0.1, cx + w / 2, cy - h / 2), fill=NAVY + (255,), width=max(2, int(w * 0.06)))


def map_sprite(t, p):
    """18-04〜18-07：地図（字なし）。町＝明るい四角、道＝白い線、いま走っている道＝赤い線。
    18-05 で赤い線をたどって寄ると、地図のはしで線がとぎれる（道が地図にない）。18-07 で引くと、明るい町の外へ暗い道が細くのびていく"""
    W_, H_ = 900, 520
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    out = 0.0 if t < p["t_out"] else min(1.0, (t - p["t_out"]) / 1.6)      # 18-07：引く
    zin = 0.0 if t < p["t_zoom"] else min(1.0, (t - p["t_zoom"]) / 1.2)    # 18-05：線の終わりに寄る
    sc = (1.0 + 0.5 * zin) * (1.0 - 0.55 * out)
    fx, fy = 640 - 520 * zin * (1 - out), 0                                   # 寄るときは、地図の右はし（線の終わり）を見せる
    cx, cy = W_ / 2 + (-fx + 640) * 0.0, H_ / 2
    mw, mh = 600 * sc, 400 * sc
    ox = W_ / 2 - mw / 2 - 170 * zin * (1 - out) + 120 * out; oy = H_ / 2 - mh / 2
    if out > 0:     # 地図の外（ふつうの地図にない所）は暗い。暗い道が細くのびていく
        d.rounded_rectangle((0, 0, W_ * S2, H_ * S2), radius=30 * S2, fill=(14, 18, 34, int(235 * out)))
    P = lambda x, y: ((ox + x * mw) * S2, (oy + y * mh) * S2)
    d.rounded_rectangle(P(0, 0) + P(1, 1), radius=int(14 * sc * S2), fill=(246, 238, 216, 255), outline=(190, 170, 130, 255), width=max(2, int(4 * sc * S2)))
    for i in range(4):          # 町の四角（家のかたまり）
        for j in range(3):
            x0 = 0.06 + i * 0.16; y0 = 0.1 + j * 0.28
            d.rounded_rectangle(P(x0, y0) + P(x0 + 0.12, y0 + 0.2), radius=int(4 * sc * S2), fill=(214, 206, 188, 255))
    for j in range(4): d.line(P(0.02, 0.05 + j * 0.28) + P(0.7, 0.05 + j * 0.28), fill=(255, 255, 255, 255), width=max(2, int(9 * sc * S2)))
    for i in range(5): d.line(P(0.03 + i * 0.16, 0.03) + P(0.03 + i * 0.16, 0.97), fill=(255, 255, 255, 255), width=max(2, int(9 * sc * S2)))
    # お城の印（左）と、いま走っている道（赤）：町の道を通って、地図の右へ。右の 3 割には道がない（白い紙のまま）
    d.polygon([P(0.04, 0.70), P(0.04, 0.54), P(0.075, 0.54), P(0.075, 0.60), P(0.105, 0.60), P(0.105, 0.54), P(0.14, 0.54), P(0.14, 0.70)], fill=(120, 96, 170, 255))      # 出発のお城（v1 の確認役：小さくて何か分からなかった → 大きく）
    rt = 0.0 if t < p["t_open"] else min(1.0, (t - p["t_open"]) / 1.4)
    pts = [(0.1, 0.61), (0.35, 0.61), (0.35, 0.33), (0.7, 0.33), (0.98, 0.33)]
    L = [math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(len(pts) - 1)]; tot = sum(L)
    done = rt * tot; acc = 0.0
    for k in range(len(pts) - 1):
        if done <= acc: break
        u = min(1.0, (done - acc) / L[k]); a_, b_ = pts[k], pts[k + 1]
        q = (a_[0] + (b_[0] - a_[0]) * u, a_[1] + (b_[1] - a_[1]) * u)
        if a_[0] >= 0.7:     # 道のない所（白い紙）：線はここでぷつっと切れる（v1 の確認役：点線が続いて「消えた」に見えなかった）
            pass
        else:
            d.line(P(*a_) + P(*q), fill=(226, 58, 48, 255), width=max(2, int(10 * sc * S2)))
        acc += L[k]
    if t >= p["t_gone"]:      # 線が消える所に赤い丸
        r_ = 0.09 * mh / max(mh, 1) * 400 * sc
        c_ = P(0.72, 0.33)      # 線がとぎれる所
        d.ellipse((c_[0] - r_ * S2 * 0.9, c_[1] - r_ * S2 * 0.9, c_[0] + r_ * S2 * 0.9, c_[1] + r_ * S2 * 0.9), outline=(226, 58, 48, 255), width=6 * S2)
    if out > 0:               # 地図の外へ、暗い道が細くのびる（点線）→ 先は暗がり
        x0, y0 = P(0.72, 0.33); n = int(14 * out)
        for m in range(n):
            xa = x0 + (m * 26 + 6) * S2
            if xa > (W_ - 20) * S2: break
            d.line((xa, y0, xa + 16 * S2, y0), fill=(235, 205, 120, int(240 * out)), width=9 * S2)      # v1 の確認役：細い灰色でほぼ見えなかった → 太く明るく
    return _done(im, W_, H_)


def search_sprite(t, p):
    """19-04：ふつうの検索の窓（虫めがね＋線）。結果の欄に、市場は出てこない（灰色の欄に×）。字なし"""
    W_, H_ = 560, 250
    im, d = _canvas(W_, H_)
    d.rounded_rectangle((30 * S2, 30 * S2, 530 * S2, 100 * S2), radius=35 * S2, fill=(240, 244, 250, 255), outline=NAVY + (255,), width=4 * S2)
    d.ellipse((55 * S2, 45 * S2, 95 * S2, 85 * S2), outline=NAVY + (255,), width=6 * S2); d.line((90 * S2, 80 * S2, 108 * S2, 98 * S2), fill=NAVY + (255,), width=7 * S2)
    d.rounded_rectangle((130 * S2, 58 * S2, 380 * S2, 72 * S2), radius=6 * S2, fill=GREY + (255,))
    if t >= p["t_x"]:
        d.rounded_rectangle((30 * S2, 130 * S2, 530 * S2, 220 * S2), radius=16 * S2, fill=(236, 238, 242, 255))
        _xbadge(d, 280 * S2, 175 * S2, 32 * S2, RED)
    return _done(im, W_, H_)


def trade_sprite(t, p):
    """19-05：名札の箱 ⇄ 硬貨（売り買い）。字なし"""
    W_, H_ = 560, 230
    im, d = _canvas(W_, H_)
    d.rounded_rectangle((50 * S2, 60 * S2, 190 * S2, 170 * S2), radius=10 * S2, fill=(180, 138, 90, 255))
    _tag(d, 120 * S2, 112 * S2, 90 * S2, col=(47, 217, 200))
    _arrow(d, 220, 90, 340, 90, NAVY); _arrow(d, 340, 145, 220, 145, NAVY)
    for k, (dx, dy) in enumerate(((-26, 20), (26, 20), (0, -22))): _coin(d, (440 + dx) * S2, (118 + dy) * S2, 38 * S2)
    return _done(im, W_, H_)


def bulk_sprite(t, p):
    """21-01〜21-07：1 文で 1 段ずつ。名札 1 枚 → たくさんの名札の箱に入り、ふたが閉まる（21-02）→ 1 枚の横に小さな硬貨 1 つ（21-04）→
    箱から手紙がたくさん飛ぶ（21-05）→ いくつかだけが硬貨になって戻る（21-06）→ 硬貨の山（21-07）。字は札の短い言葉だけ"""
    # v9 のユーザー「箱が急に出てきてわかんないので横から出てくるとか」「箱にいろんな名札が入っていくのを動き入れて分かるようにして、今は外側に名札貼ってるだけに見える」
    #   → 板が横へ広がりながら、空の箱が右から入ってくる（t_box〜t_in-0.3）。名札（まるロボの青緑）が箱の口へ入り、ほかのお城の色の名札が上から 1 枚ずつ落ちて入る。
    #     箱は口の開いた形（奥の板 → 名札 → 手前の板）にして、名札の下半分が手前の板にかくれる。そのあと、ふたが閉まる
    t_b0, t_b1 = p["t_in"] - 0.9, p["t_in"] - 0.3
    if t < t_b0:          # 21-01：名札 1 枚だけ（名札の大きさの板）
        im, d = _canvas(360, 300); _tag(d, 180 * S2, 150 * S2, 220 * S2, col=(47, 217, 200)); return _done(im, 360, 300)
    wv_ = min(1.0, (t - t_b0) / (t_b1 - t_b0)); wv_ = wv_ * wv_ * (3 - 2 * wv_)
    W_ = int(round(360 + (1120 - 360) * wv_)) if t < t_b1 else 1120
    H_ = (300 + int(30 * wv_)) if t < t_b1 else (330 if t < p["t_lbl"] else 410)      # 3章 v1 の点検：中の絵が小さく、幅 390px で見分けにくかった → 全部ひとまわり大きく
    im, d = _canvas(W_, H_)
    ox = (W_ - 1120) / 2.0                     # 広がっている間は、図のまん中を板のまん中に合わせる
    X = lambda x: (x + ox) * S2
    one_x, one_y = 250, 165       # 板が広がる間に、名札 1 枚は左へよける（箱が右から入ってくる所を空ける）
    bx_, by_ = 560, 175          # 箱（まん中）
    bxx = bx_ + (1120 + 200 - bx_) * (1 - wv_) if t < t_b1 else bx_      # 右から入ってくる
    BROWN, BROWN_D, BROWN_L = (180, 138, 90, 255), (120, 86, 52, 255), (200, 158, 108, 255)
    TAGS = [((47, 217, 200), -140, -64), ((220, 70, 70), -70, -68), ((60, 110, 200), 0, -64), ((70, 170, 80), 70, -68), ((235, 130, 40), 140, -64),
            ((140, 90, 190), -105, -40), ((230, 190, 40), -35, -37), ((40, 160, 170), 35, -40), ((200, 90, 150), 105, -37)]
    def box_back():
        d.rounded_rectangle((X(bxx - 185), (by_ - 95) * S2, X(bxx + 185), (by_ + 110) * S2), radius=12 * S2, fill=BROWN_D)
    def box_front():
        d.rounded_rectangle((X(bxx - 185), (by_ - 22) * S2, X(bxx + 185), (by_ + 110) * S2), radius=12 * S2, fill=BROWN)
        d.rectangle((X(bxx - 185), (by_ - 22) * S2, X(bxx + 185), (by_ - 12) * S2), fill=BROWN_L)      # 口のふち
    box_back()
    mv = 0.0 if t < p["t_in"] else min(1.0, (t - p["t_in"]) / 0.7)
    if t >= p["t_in"]:
        for k_, (col_, dx_, dy_) in enumerate(TAGS):
            if k_ == 0:          # まるロボの名札：左の大きな 1 枚が、小さくなって箱の口へ
                if mv < 1.0: continue
                _tag(d, X(bxx + dx_), (by_ + dy_) * S2, 68 * S2, col=col_); continue
            t_k = p["t_in"] + 0.2 + 0.14 * (k_ - 1); u = 0.0 if t < t_k else min(1.0, (t - t_k) / 0.4)
            if u <= 0: continue
            y_ = -40 + (by_ + dy_ + 40) * (u * u)       # 上から落ちてくる（だんだん速く）
            _tag(d, X(bxx + dx_), y_ * S2, 68 * S2, col=col_)
    box_front()
    if t >= p["t_in"] - 0.3:
        lid = 0.0 if t < p["t_lid"] else min(1.0, (t - p["t_lid"]) / 0.4)
        if lid > 0:
            yl = (by_ - 170) + 70 * lid       # ふたが上から下りて、口を全部ふさぐ（前は口の上に浮いて見えた）
            d.rounded_rectangle((X(bx_ - 193), yl * S2, X(bx_ + 193), (yl + 88) * S2), radius=10 * S2, fill=(150, 110, 66, 255))
            d.rectangle((X(bx_ - 193), (yl + 78) * S2, X(bx_ + 193), (yl + 88) * S2), fill=(130, 94, 56, 255))
    if t < t_b1:          # 広がっている間：名札 1 枚は板のまん中のまま
        _tag(d, X(560 - 310 * wv_), (150 + 15 * wv_) * S2, 220 * S2, col=(47, 217, 200)); return _done(im, W_, H_)
    tx = one_x + (bx_ - 140 - one_x) * mv; ty = one_y + (by_ - 64 - one_y) * mv
    if mv < 1.0: _tag(d, tx * S2, ty * S2, (220 - 152 * mv) * S2, col=(47, 217, 200))
    if t >= p.get("t_one", p["t_cheap"]):          # 21-04「1人分の名札」：1 枚（左。v1 の点検：「1人分の…わずかです」の間、図が変わらなかった）
        _tag(d, 140 * S2, 165 * S2, 170 * S2, col=(47, 217, 200))      # v1 の確認役：小さかった → 大きく
    if t >= p["t_cheap"]:          # 「1枚は安い」：1 枚の横に、小さな硬貨 1 つ
        _coin(d, 140 * S2, 280 * S2, 34 * S2)
    # 21-05：箱から手紙が右へ一斉に飛ぶ
    if t >= p["t_mail"] and t < p["t_pile"]:      # 硬貨の山が出たら手紙は消す（v1 の確認役：山が手紙に重なった）
        u = min(1.0, (t - p["t_mail"]) / 1.2)
        for k in range(10):
            ang = -0.9 + 0.2 * k
            x = bx_ + 190 + (230 * u) * math.cos(ang) + 40 * u; y = by_ + (240 * u) * math.sin(ang) * 0.6
            back = t >= p["t_back"] and k in (2, 5, 8)
            if back:          # 21-06：3 つだけが硬貨になって、箱の右へ戻る
                v = min(1.0, (t - p["t_back"]) / 1.0)
                x2 = bx_ + 225 + 32 * (k // 3); y2 = by_ + 85
                _coin(d, (x + (x2 - x) * v) * S2, (y + (y2 - y) * v) * S2, 28 * S2)
            else:
                _envelope(d, x * S2, y * S2, 58 * S2)
    if t >= p["t_pile"]:           # 21-07：硬貨の山（箱の右下）
        n = min(15, int((t - p["t_pile"]) / 0.12) + 3)
        for k in range(n):
            r = k // 5; c = k % 5
            _coin(d, (905 + c * 40 - r * 20) * S2, (275 - r * 36) * S2, 30 * S2)      # 右はしが図の外にはみ出していた → 30 左へ
    if t >= p["t_lbl"]:
        D.ctext(d, (140 * S2, 365 * S2), "1枚は安い", D.font(46 * S2), NAVY)
        D.ctext(d, (920 * S2, 365 * S2), "たくさん＝お金", D.font(46 * S2), (140, 80, 0))      # 濃い色に
    return _done(im, W_, H_)


def ev_list3():
    E = []
    add = lambda *a: E.append(a)
    add(wv("18-01", "どこへ") - 0.2, e("18-01") + 0.3, "qmark", dict(pos=(1120, 140), size=150))      # 語り手の問い（画面のすみ）
    add(wv("18-04", "あれ") - 0.1, e("18-04") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(wv("18-04", "地図") - 0.1, e("18-07") + 0.3, "c3_map", dict(t_open=wv("18-04", "地図") + 0.2, t_zoom=s("18-05") + 0.05, t_gone=wv("18-05", "消え") - 0.1, t_out=s("18-07") + 0.1))
    add(wv("18-06", "ふつうの地図") - 0.1, e("18-06") + 0.3, "tag", dict(text="ふつうの地図にのっていない道", pos=(640, 45), size=48))
    add(wv("19-04", "ふつうの検索") - 0.1, e("19-04") + 0.3, "c3_search", dict(t_x=wv("19-04", "出てこない") - 0.1))
    add(wv("19-04", "かくれた市場") - 0.1, e("19-04") + 0.3, "tag", dict(text="かくれた市場", pos=(640, 330), size=56))
    add(wv("19-05", "売り買い") - 0.3, e("19-05") + 0.3, "c3_trade", {})
    add(wv("20-01", "自分のお城") - 0.1, e("20-01") + 0.3, "ring", dict(obj="mybox", r=55, col=RED))
    add(s("21-01") - 0.05, e("21-07") + 0.3, "c3_bulk", dict(t_in=wv("21-02", "たくさん") - 0.2, t_lid=wv("21-02", "まとめて") + 0.3, t_one=s("21-04") + 0.1, t_cheap=wv("21-04", "1枚") - 0.2,
                                                         t_mail=wv("21-05", "まとめてメール") - 0.3, t_back=wv("21-06", "だまされる") - 0.2, t_pile=s("21-07") + 0.1, t_lbl=wv("21-07", "1枚") - 0.1))
    add(wv("21-02", "まとめて") + 0.2, e("21-02") + 0.3, "tag", dict(text="まとめて売られる", pos=(640, 470), size=48))
    add(wv("21-03", "なぜ") - 0.1, e("21-03") + 0.3, "qmark", dict(pos=(1150, 450), size=120))      # 語り手の問い。図の右下（v1 の確認役：まるロボの頭が図の裏で、「？」が箱の上に付いた）
    add(wv("21-10", "だれの手") - 0.2, e("21-10") + 0.3, "qmark", dict(pos=(1120, 140), size=150))
    return E


def sfx_list3():
    L = [(wv("18-04", "地図") + 0.1, "paper", 0.35)]           # 地図を広げる「ぱさ」
    L.append((wv("21-02", "たくさん") - 1.1, "swish", 0.2))      # 箱が右からすべりこむ（v9 のユーザー「箱が急に出てきて」）
    L.append((wv("21-02", "まとめて") + 0.65, "thud", 0.15))    # ふたが閉まる「ぱたん」
    L.append((wv("21-05", "まとめてメール") - 0.25, "swish", 0.3))
    L.append((wv("21-06", "だまされる") + 0.7, "jingle", 0.3))
    return L


def draw3(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    if kind == "c3_map":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(110 * a))))
        zin = 0.0 if t < p["t_zoom"] else min(1.0, (t - p["t_zoom"]) / 1.2)
        _paste(base, map_sprite(t, p), 820 - 180 * zin, 300, k, a)        # 18-04 は右（左にまるロボと「？」）、18-05 からまん中へ
    elif kind == "c3_search": _paste(base, search_sprite(t, p), 640, 170, k, a)
    elif kind == "c3_trade": _paste(base, trade_sprite(t, p), 640, 170, k, a)
    elif kind == "c3_bulk":
        spr = bulk_sprite(t, p); _paste(base, spr, 640, 30 + spr.height / 2, k, a)
