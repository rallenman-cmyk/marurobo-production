# 6本目：3D の上に重ねる 2D（札・吹き出し・題名・小窓・矢印・こぼれる絵・速さの絵）
#   一覧 EVENTS：(始め, 終わり, 種類, 中身)。時刻は声の時刻（timing.py）。札の答えは、その言葉を言う瞬間に出す（SKILL §3）
#   見た目は 4本目の design.py（2 倍で描いて縮める・やわらかい影・ぽんと弾んで出る 0.3 秒・しっぽと 1 つの形）
#   字の大きさ：数字は 56〜60、ほかは 48（1280×720 の座標。スマホで読める大きさ）。字幕の帯（y 560 より下）に置かない
#   下の字幕と同じ文を札にしない。札は単語・数・ラベルだけ。5本目の overlays.py を写して、この回の札にした
import os, sys, math
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep04_robot", "look"))
import design as D
import timing as T
s, e, w = T.s, T.e, T.w
TEAL = (33, 193, 179); YEL = (255, 210, 74); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48); ORANGE = (255, 154, 60)
SUB_TOP = 560


def ev_list():
    E = []
    add = lambda *a: E.append(a)
    # 03：にらめっこ（どいていいのか分からない）
    add(w("03-02", "どいて") - 0.2, e("03-02") + 0.3, "bubble", dict(obj="maru", icon="?", side=-1))
    # 04：問い → 題名（2 秒）
    add(w("04-03", "どうして") - 0.2, e("04-04") + 0.2, "bubble", dict(obj="maru", icon="?", side=-1))
    add(e("04-05") + 0.3, s("05-01") - 0.3, "title", {})
    # 06：体の名前（言う瞬間に）
    add(w("06-01", "顔の画面"), e("06-01") + 0.2, "tag", dict(text="顔の画面", obj="head", dy=-110))
    add(w("06-01", "トレー"), e("06-01") + 0.2, "tag", dict(text="トレー", obj="tray", dy=-60))
    add(w("06-02", "カメラ"), w("06-02", "足もと") - 0.1, "tag", dict(text="カメラ", obj="lens", dy=-90))
    add(w("06-02", "小さな窓"), e("06-02") + 0.4, "tag", dict(text="小さな窓", obj="window", dy=60))
    # 07：台数
    add(w("07-02", "2022年"), e("07-02") + 0.4, "tag", dict(text="2022年の1年間", pos=(640, 100), size=48))
    add(w("07-02", "約3,000台"), e("07-02") + 0.6, "tag", dict(text="約3,000台", pos=(640, 190), size=64, bg=YEL))
    # 08：席の番号
    add(w("08-03", "12番"), e("08-04") + 0.2, "tag", dict(text="12番", obj="head", dy=-120, size=60, bg=YEL))
    # 09〜10：席の点・道・自分はどこ？
    add(w("09-03", "白い丸") + 0.3, e("09-04") + 0.3, "tag", dict(text="席の点", pos=(1080, 90)))
    add(w("09-04", "ここで"), e("10-03") + 0.3, "tag", dict(text="12番", obj="seat12", dy=-70, size=56, bg=YEL))
    add(w("10-05", "自分が"), e("10-05") + 0.3, "bubble", dict(obj="senpai", icon="?", side=1, gap=30))
    # 11：天井の目印
    add(w("11-02", "目印"), e("11-04") + 0.3, "tag", dict(text="目印のシール", pos=(640, 90)))
    # 12：地図と、いま見えている形
    add(w("12-02", "地図"), e("12-03"), "legend", dict(items=[(TEAL, "地図"), (WHITE, "いま見えている形")], t1=w("12-02", "地図") + 0.5))
    # 13：光の物差し
    add(w("13-02", "光の物差し"), e("13-03") + 0.3, "tag", dict(text="光の物差し", pos=(1060, 90)))
    # 14〜16：点の色の名前（14 から最後まで同じ）
    add(w("14-03", "青緑"), e("16-04") + 0.5, "legend", dict(items=[(TEAL, "止まった物"), (ORANGE, "動く人の足")], t1=w("14-04", "橙")))
    add(w("16-01", "遅く"), s("16-02") - 0.05, "tag", dict(text="遅くなる", pos=(1060, 90)))
    add(w("16-02", "ぴたっ"), s("16-03") - 0.05, "tag", dict(text="止まる", pos=(1060, 90), bg=YEL))
    add(w("16-03", "よけて"), e("16-03") + 0.5, "tag", dict(text="よける", pos=(1060, 90)))
    add(w("16-04", "冒頭で"), e("16-04") + 0.2, "pip_clip", dict(clip="S03a", src_t=w("03-01", "ぴたっ") + 0.3, hold=True))
    # 17：光の板
    add(w("17-02", "この高さ"), e("17-03") + 0.3, "tag", dict(text="回る光の高さ", pos=(1060, 90)))
    add(w("17-03", "低い物") - 0.2, e("17-03") + 0.2, "bubble", dict(obj="senpai", icon="?", side=1, gap=10))
    # 18：先輩の目の絵（小窓）。まるロボの所に点がない
    add(w("18-03", "先輩の目"), e("18-03") + 0.6, "pip_clip", dict(clip="S18p", src_t=s("18-03"), big=True))
    # 19：出っぱったテーブルのはし
    add(w("19-01", "テーブルのはし"), e("19-02") + 0.3, "ring2d", dict(obj="edgept", r=40))
    add(w("19-04", "どこで") - 0.2, e("19-04") + 0.2, "bubble", dict(obj="maru", icon="?", side=1))
    # 20：前のカメラ 3 つ
    add(w("20-02", "3つ"), e("20-03") + 0.3, "tag", dict(text="前のカメラ 3つ", pos=(1040, 90), size=52))
    add(w("20-04", "回る光"), e("20-05") + 0.2, "legend", dict(items=[(TEAL, "回る光：遠くまで"), ((255, 226, 122), "前のカメラ：目の前")], t1=w("20-04", "前のカメラ")))
    # 21：子ども
    add(s("21-01") + 0.3, s("21-01") + 1.6, "bubble", dict(obj="maru", icon="!", side=-1))
    # 22：人が運ぶと……（小窓の絵）・速さの変え方（絵）
    add(w("22-01b", "人が"), e("22-01b") + 0.3, "spill", {})
    add(w("22-02", "なめらかに"), e("22-03") + 0.3, "speed", dict(t1=e("22-02")))
    # 24：通路のはば
    add(s("24-01"), e("24-03") + 0.3, "darrow", dict(a="gapL", b="gapR", text="70cm", track_clip="S24a", t_text=w("24-01", "70cm")))
    # 23・25：困り顔・ほっと
    add(s("23-03") + 0.3, e("23-03") + 0.6, "bubble", dict(obj="maru", icon="?", side=-1, track_clip="S23b"))
    # 28：怒った
    add(w("28-03", "怒った") + 0.1, e("28-03") + 0.6, "bubble", dict(obj="maru", icon="!", side=1, track_clip="S28a"))
    # 29：まとめ（言い始めてから、1 つずつ）
    for txt, at, row in (("席の点", w("29-02", "席ごとの"), 0), ("天井の目印", w("29-03", "天井の目印"), 0), ("まわりの形", w("29-03", "まわりの形"), 0),
                         ("回る光", w("29-05", "回る光"), 1), ("前のカメラ", w("29-05", "前のカメラ"), 1), ("顔", w("29-07", "顔が"), 2)):
        add(at, e("29-07") + 0.5, "sumtag", dict(text=txt, row=row, t_all=at))
    # 30：オチ
    add(w("30-04", "デザート") - 0.2, e("30-04") + 1.2, "bubble", dict(obj="maru", icon="!", side=-1, gap=30))
    return sorted(E, key=lambda x: x[0])


EVENTS = ev_list()
_cache = {}


def _pop(t, t0, t1):
    """出るときぽんと弾む（0.3 秒）、消えるとき 0.2 秒で薄く"""
    k = D.ease_out_back((t - t0) / 0.3) if t - t0 < 0.3 else 1.0
    a = 1.0 if t1 - t > 0.2 else max(0.0, (t1 - t) / 0.2)
    return max(0.05, k), a


def _paste(base, spr, cx, cy, k=1.0, a=1.0):
    if k != 1.0:
        spr = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.LANCZOS)
    if a < 1.0:
        al = spr.getchannel("A").point(lambda v: int(v * a)); spr = spr.copy(); spr.putalpha(al)
    base.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))


def tag_sprite(text, size=48, bg=WHITE, fg=None, tail=None):
    key = ("tag", text, size, bg, tail)
    if key not in _cache:
        spr, off = D.pill(text, size, fg=fg or NAVY, bg=bg, tail=tail)
        _cache[key] = (spr, off)
    return _cache[key]


def icon_draw(kind):
    def dr(d, cx, cy, ss, img):
        f = D.font(80 * ss)
        if kind in ("?", "!"):
            D.ctext(d, (cx, cy), kind, f, NAVY if kind == "?" else D.ORANGE)
        elif kind == "dizzy":     # ぐるぐる
            for k in range(3):
                r = (12 + k * 12) * ss; d.arc([cx - r, cy - r, cx + r, cy + r], 30 + k * 40, 330 + k * 40, fill=NAVY, width=5 * ss)
        elif kind == "chicken_egg":   # にわとり ⇄ 卵（字なし）
            x1, x2 = cx - 62 * ss, cx + 62 * ss
            # にわとり
            d.ellipse([x1 - 34 * ss, cy - 22 * ss, x1 + 30 * ss, cy + 34 * ss], fill=(255, 255, 255), outline=NAVY, width=4 * ss)
            d.ellipse([x1 + 4 * ss, cy - 46 * ss, x1 + 34 * ss, cy - 14 * ss], fill=(255, 255, 255), outline=NAVY, width=4 * ss)
            d.polygon([(x1 + 34 * ss, cy - 32 * ss), (x1 + 50 * ss, cy - 26 * ss), (x1 + 34 * ss, cy - 22 * ss)], fill=D.ORANGE)
            d.ellipse([x1 + 10 * ss, cy - 56 * ss, x1 + 26 * ss, cy - 42 * ss], fill=D.RED)
            d.ellipse([x1 + 20 * ss, cy - 34 * ss, x1 + 26 * ss, cy - 28 * ss], fill=NAVY)
            # 卵
            d.ellipse([x2 - 26 * ss, cy - 36 * ss, x2 + 26 * ss, cy + 34 * ss], fill=(255, 243, 214), outline=NAVY, width=4 * ss)
            # ⇄ の矢印
            for sg in (-1, 1):
                y = cy + sg * 12 * ss
                d.line([cx - 18 * ss, y, cx + 18 * ss, y], fill=D.TEAL, width=5 * ss)
                tip = cx + sg * 18 * ss
                d.polygon([(tip, y), (tip - sg * 10 * ss, y - 8 * ss), (tip - sg * 10 * ss, y + 8 * ss)], fill=D.TEAL)
    return dr


def bubble_sprite(kind, big=False, side=1):
    """吹き出し（v3：しっぽなし。5本目 v2「はてなの吹き出しのしっぽいらない」。頭の上に浮かべる）"""
    key = ("bub", kind, big)
    if key not in _cache:
        wdt, hgt = (240, 140) if big else (120, 110)
        spr, off = D.bubble(wdt, hgt, (0, 0), draw=icon_draw(kind))
        _cache[key] = (spr, off)
    return _cache[key]


def arrow_sprite(p0, p1, col=YEL):
    """矢印（v3：先が潰れて見えた → 2 倍で描いて縮める・線は頭の付け根で止める・頭を大きく 1 つの三角に。5本目 v2）"""
    key = ("arrow", p0, p1, col)
    if key in _cache: return _cache[key]
    S2 = 2; im = Image.new("RGBA", (1280 * S2, 720 * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); ca, sa = math.cos(a), math.sin(a)
    L_, Hw, lw = 52, 30, 14
    tip = (p1[0] * S2, p1[1] * S2); base = ((p1[0] - L_ * ca) * S2, (p1[1] - L_ * sa) * S2)
    d.line([(p0[0] * S2, p0[1] * S2), (base[0] + 4 * ca, base[1] + 4 * sa)], fill=col + (255,), width=lw * S2)
    r = lw * S2 / 2; d.ellipse([p0[0] * S2 - r, p0[1] * S2 - r, p0[0] * S2 + r, p0[1] * S2 + r], fill=col + (255,))
    d.polygon([tip, (base[0] - Hw * sa * S2, base[1] + Hw * ca * S2), (base[0] + Hw * sa * S2, base[1] - Hw * ca * S2)], fill=col + (255,))
    im = im.resize((1280, 720), Image.LANCZOS)
    _cache[key] = im
    return im


def draw(t, base, where, frame_of=None, fontdir=None):
    """base（1280×720 RGBA）に、時刻 t の 2D を描く。where(名前, t, clip=None) → 画面の (x, y) か None。frame_of(clip, t) → 小窓の絵"""
    if fontdir and not D.FDIR[0]: D.FDIR[0] = fontdir
    for t0, t1, kind, p in EVENTS:
        if not (t0 <= t < t1): continue
        k, a = _pop(t, t0, t1)
        if kind == "tag":
            if "pos" in p: cx, cy = p["pos"]; tail = None
            else:
                q = where(p["obj"], t, p.get("track_clip"))
                if q is None: continue
                cx, cy = q[0], max(70, q[1] + p.get("dy", -120)); cy = min(cy, SUB_TOP - 60)
                tail = (0, 46) if q[1] - cy > 60 else None      # v3：しっぽは決まった三角（物との距離で大きさが変わらない。5本目 v2「バンパー」）
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), tail=tail)
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            _paste(base, spr, cx + (off[0] + spr.width / 2), cy + (off[1] + spr.height / 2), k, a)
        elif kind == "bubble":
            q = where(p["obj"], t, p.get("track_clip"))
            if q is None: continue
            if not (-20 <= q[0] <= 1300 and -20 <= q[1] <= 700): continue      # 物が画面の外なら出さない（どこの吹き出しか分からなくなる）
            spr, off = bubble_sprite(p["icon"], p.get("big", False), p.get("side", 1))
            cx = q[0] + p.get("dx", 0); cy = q[1] - p.get("gap", 40) - spr.height / 2
            cx = min(max(cx, spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(cy, spr.height / 2 + 10), SUB_TOP - spr.height / 2)
            _paste(base, spr, cx, cy, k, a)
        elif kind == "title":
            dim = Image.new("RGBA", base.size, (8, 14, 26, int(120 * a))); base.alpha_composite(dim)
            _paste(base, title_sprite(), 640, 290, k, a)
        elif kind == "legend":     # 点の色の名前（色の丸＋名前）。左上に、1 つずつ
            y_ = 70
            for i, (col, txt) in enumerate(p["items"]):
                ti = t0 if i == 0 else p.get("t1", t0)
                if t < ti: continue
                spr = legend_sprite(col, txt)
                k2, a2 = _pop(t, ti, t1)
                _paste(base, spr, 40 + spr.width / 2, y_ + spr.height / 2, k2, a2)
                y_ += spr.height + 12
        elif kind == "sumtag":     # まとめの札（3 段に並べる）
            row = p["row"]; same = [x for x in EVENTS if x[2] == "sumtag" and x[3]["row"] == row]
            i = [x[3]["text"] for x in same].index(p["text"])
            spr, off = tag_sprite(p["text"], 46, YEL if row == 2 else WHITE)
            widths = [tag_sprite(x[3]["text"], 46)[0].width for x in same]; tot = sum(widths) + 24 * (len(same) - 1)
            x_ = 640 - tot / 2 + sum(widths[:i]) + 24 * i + spr.width / 2
            _paste(base, spr, x_, 80 + row * 92, k, a)
        elif kind == "spill":      # 人がおぼんで運んで、急に止まると……スープがはねる（字なしの絵）
            _paste(base, spill_sprite(min(1.0, (t - t0) / 1.6)), 250, 170, k, a)
        elif kind == "speed":      # 速さの変え方：ぐっと（点線）と、なめらか（青緑）
            _paste(base, speed_sprite(min(1.0, (t - t0) / 1.4)), 1010, 180, k, a)
        elif kind == "ring2d":
            q = where(p["obj"], t, p.get("track_clip"))
            if q is None: continue
            r = p.get("r", 30) * k; im = Image.new("RGBA", base.size, (0, 0, 0, 0)); d_ = ImageDraw.Draw(im)
            d_.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], outline=YEL + (int(255 * a),), width=7)
            base.alpha_composite(im)
        elif kind == "frame2d":    # 物を囲む角の丸い枠（v3：先輩がどこにいたか）
            q = where(p["obj"], t, p.get("track_clip"))
            if q is None: continue
            r = p.get("r", 60) * k; S2 = 2; im = Image.new("RGBA", (1280 * S2, 720 * S2), (0, 0, 0, 0)); d_ = ImageDraw.Draw(im)
            d_.rounded_rectangle([(q[0] - r) * S2, (q[1] - r * 0.8) * S2, (q[0] + r) * S2, (q[1] + r * 0.8) * S2], int(18 * S2), outline=p.get("col", RED) + (int(255 * a),), width=8 * S2)
            base.alpha_composite(im.resize((1280, 720), Image.LANCZOS))
        elif kind == "darrow":    # 2 つの物の間の両向きの矢印と札
            qa = where(p["a"], t, p.get("track_clip")); qb = where(p["b"], t, p.get("track_clip"))
            if qa is None or qb is None: continue
            L = math.dist(qa, qb); ux, uy = (qb[0] - qa[0]) / max(L, 1), (qb[1] - qa[1]) / max(L, 1)
            pa = (qa[0] + ux * 14, qa[1] + uy * 14); pb = (qb[0] - ux * 14, qb[1] - uy * 14); mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            im = arrow_sprite((round(mid[0]), round(mid[1])), (round(pb[0]), round(pb[1])), WHITE).copy(); im.alpha_composite(arrow_sprite((round(mid[0]), round(mid[1])), (round(pa[0]), round(pa[1])), WHITE))
            if a < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            base.alpha_composite(im)
            if t >= p.get("t_text", t0):
                spr, off = tag_sprite(p["text"], 60, YEL)
                _paste(base, spr, mid[0], mid[1] - 70, *_pop(t, p.get("t_text", t0), t1))
        elif kind == "spin":      # 回る矢印（円の 3/4 と矢じり）が、物のまわりでくるくる回る
            q = where(p["obj"], t, p.get("track_clip"))
            if q is None: continue
            S2 = 2; r = p.get("r", 50) * k * S2; im = Image.new("RGBA", (1280 * S2, 720 * S2), (0, 0, 0, 0)); d_ = ImageDraw.Draw(im)
            cx, cy = q[0] * S2, q[1] * S2; rot = -((t - t0) * 540) % 360; col = YEL + (int(255 * a),)
            for half in (0, 180):
                a0 = rot + half; a1 = a0 + 120
                d_.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=col, width=9 * S2)
                th = math.radians(a0); tx, ty = cx + r * math.cos(th), cy + r * math.sin(th)
                tg = (math.sin(th), -math.cos(th))          # 回る向き（角度が減る向き）の接線
                L_, Hw = 26 * S2, 16 * S2
                d_.polygon([(tx + tg[0] * L_, ty + tg[1] * L_), (tx - Hw * math.cos(th), ty - Hw * math.sin(th)), (tx + Hw * math.cos(th), ty + Hw * math.sin(th))], fill=col)
            base.alpha_composite(im.resize((1280, 720), Image.LANCZOS))
        elif kind == "arrow":
            base.alpha_composite(arrow_sprite(p["p0"], p["p1"]))
        elif kind == "pip_clip" and frame_of:
            im = frame_of(p["clip"], p["src_t"] + (0 if p.get("hold") else (t - t0)))
            if im is None: continue
            im = im.convert("RGB")
            if p.get("crop"):     # 3D のスマホの寄りの絵から、スマホのまわりだけ切り出す（16:9 のまま）
                cx0, cy0, cx1, cy1 = p["crop"]; W_, H_ = im.size
                im = im.crop((int(cx0 * W_), int(cy0 * H_), int(cx1 * W_), int(cy1 * H_)))
            W2, H2 = (560, 315) if p.get("big") else (400, 225)
            im = im.resize((W2, H2), Image.LANCZOS)
            if p.get("sepia"): im = sepia(im)
            fr = Image.new("RGBA", (W2 + 12, H2 + 12), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            _paste(base, fr, 30 + (W2 + 12) / 2, 25 + (H2 + 12) / 2, k, a)
    return base


def title_sprite():
    key = ("title",)
    if key not in _cache:
        spr, off = D.card(1000, 330, draw=lambda d, W_, H_, ss, img: [D.ctext(d, (W_ / 2, H_ / 2 - 92 * ss), "ファミレスの配膳ロボットは、", D.font(54 * ss), NAVY),
                                                                      D.ctext(d, (W_ / 2, H_ / 2 + 0 * ss), "なぜぶつからない？", D.font(62 * ss), D.TEAL_D),
                                                                      D.ctext(d, (W_ / 2, H_ / 2 + 92 * ss), "どの席か分かる？", D.font(62 * ss), D.TEAL_D)])
        _cache[key] = spr
    return _cache[key]


def legend_sprite(col, txt):
    key = ("leg", col, txt)
    if key not in _cache:
        spr, off = D.pill(txt, 44, fg=NAVY, bg=WHITE, accent=col)
        _cache[key] = spr
    return _cache[key]


def spill_sprite(k):
    """人がおぼんで運ぶ → 急に止まると、スープがはねる（k：0〜1 で、止まる → はねる）"""
    st = round(min(1.0, k) * 4) / 4
    key = ("spill", st)
    if key in _cache: return _cache[key]
    def dr(d, W_, H_, ss, img):
        gx = W_ * 0.42; gy = H_ * 0.84
        d.line([40 * ss, gy, W_ - 40 * ss, gy], fill=(200, 205, 210), width=4 * ss)
        lean = 10 * ss * st
        # 人（顔は描かない）
        d.ellipse([gx - 26 * ss + lean, gy - 210 * ss, gx + 26 * ss + lean, gy - 158 * ss], fill=(241, 199, 165), outline=NAVY, width=3 * ss)
        d.rounded_rectangle([gx - 34 * ss + lean * 0.6, gy - 158 * ss, gx + 34 * ss + lean * 0.6, gy - 70 * ss], 16 * ss, fill=(62, 124, 177))
        d.rectangle([gx - 26 * ss, gy - 72 * ss, gx - 6 * ss, gy], fill=(45, 54, 64)); d.rectangle([gx + 6 * ss, gy - 72 * ss, gx + 26 * ss, gy], fill=(45, 54, 64))
        # 腕とおぼん・どんぶり
        tx = gx + 70 * ss + lean; ty = gy - 120 * ss
        d.line([gx + 20 * ss + lean * 0.6, gy - 140 * ss, tx - 20 * ss, ty], fill=(62, 124, 177), width=12 * ss)
        d.rectangle([tx - 50 * ss, ty, tx + 50 * ss, ty + 8 * ss], fill=(120, 90, 60))
        d.pieslice([tx - 30 * ss, ty - 40 * ss, tx + 30 * ss, ty + 4 * ss], 0, 180, fill=(184, 55, 43))
        # はねるスープ
        for i in range(int(st * 6)):
            a_ = math.radians(-60 + i * 22); r_ = (24 + 18 * st) * ss
            cx, cy = tx + 26 * ss + r_ * math.cos(a_), ty - 34 * ss + r_ * math.sin(a_) * 0.8
            d.ellipse([cx - 7 * ss, cy - 7 * ss, cx + 7 * ss, cy + 7 * ss], fill=(217, 163, 90))
        if st >= 0.5:   # 急に止まった線
            for j in range(3):
                x_ = gx - 70 * ss - j * 16 * ss
                d.line([x_, gy - 150 * ss + j * 30 * ss, x_ - 30 * ss, gy - 150 * ss + j * 30 * ss], fill=NAVY, width=4 * ss)
    spr, off = D.card(400, 300, draw=dr)
    _cache[key] = spr
    return spr


def speed_sprite(k):
    """速さの変え方：横＝時間・縦＝速さ。点線＝ぐっと止まる、青緑＝なめらかに止まる（字は使わない）"""
    st = round(min(1.0, k) * 10) / 10
    key = ("speed", st)
    if key in _cache: return _cache[key]
    def dr(d, W_, H_, ss, img):
        x0, y0, x1, y1 = 50 * ss, H_ - 50 * ss, W_ - 40 * ss, 50 * ss
        d.line([x0, y0, x1, y0], fill=NAVY, width=4 * ss); d.line([x0, y0, x0, y1], fill=NAVY, width=4 * ss)
        top = y1 + 30 * ss; mid = x0 + (x1 - x0) * 0.45
        # ぐっと（点線）：高いまま → いきなり 0
        for i in range(0, 20):
            if i % 2: continue
            xa = x0 + (mid - x0) * i / 20; xb = x0 + (mid - x0) * (i + 1) / 20
            d.line([xa, top, xb, top], fill=(150, 160, 170), width=5 * ss)
        for i in range(0, 10, 2):
            ya = top + (y0 - top) * i / 10; yb = top + (y0 - top) * (i + 1) / 10
            d.line([mid, ya, mid, yb], fill=(150, 160, 170), width=5 * ss)
        # なめらか（青緑）：少しずつ 0 へ
        pts = []
        n = int(40 * st) + 1
        for i in range(n):
            u = i / 40; x = x0 + (x1 - x0) * u
            if u < 0.3: v = 1.0
            else:
                q = min(1.0, (u - 0.3) / 0.6); v = 1 - q * q * (3 - 2 * q)
            pts.append((x, top + (y0 - top) * (1 - v)))
        if len(pts) > 1: d.line(pts, fill=TEAL, width=8 * ss, joint="curve")
    spr, off = D.card(440, 280, draw=dr)
    _cache[key] = spr
    return spr


def sepia(im):
    g = im.convert("L")
    return Image.merge("RGB", (g.point(lambda v: min(255, int(v * 1.07 + 18))), g.point(lambda v: int(v * 0.92 + 8)), g.point(lambda v: int(v * 0.74))))
