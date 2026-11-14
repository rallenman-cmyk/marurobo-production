# 5本目：3D の上に重ねる 2D（札・吹き出し・スマホの地図・題名・約束のカード・数・小窓）
#   一覧 EVENTS：(始め, 終わり, 種類, 中身)。時刻は声の時刻（timing.py）。札の答えは、その言葉を言う瞬間に出す（SKILL §3）
#   見た目は 4本目の design.py（2 倍で描いて縮める・やわらかい影・ぽんと弾んで出る 0.3 秒・しっぽと 1 つの形）
#   字の大きさ：数字は 60、ほかは 48（1280×720 の座標。スマホで読める大きさ。SKILL §3）。字幕の帯（y 560 より下）に置かない
#   下の字幕と同じ文を札にしない。札は単語・数・ラベルだけ
import os, sys, math
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep04_robot", "look"))
import design as D
import timing as T
import map_tex
s, e, w = T.s, T.e, T.w
TEAL = (33, 193, 179); YEL = (255, 210, 74); NAVY = D.NAVY; WHITE = (255, 255, 255)
SUB_TOP = 560


def ev_list():
    E = []
    add = lambda *a: E.append(a)
    # 02：スマホに地図（大きく）。言うたびに家具が光る・いまいる場所の点に輪
    add(s("02-02") - 0.15, s("02-05") - 0.4, "phone", dict(hl=[(w("02-03", "ソファ"), "sofa"), (w("02-03", "机"), "desk"), (w("02-03", "ベッド"), "bed"), (e("02-03") + 0.2, None)], ring=w("02-04", "この点")))
    add(s("02-02") + 0.6, s("02-02") + 2.4, "bubble", dict(obj="maru", icon="!", side=-1))
    # 03：題名の前の「？」
    add(w("03-04", "いったい"), e("03-04") + 0.2, "bubble", dict(obj="maru", icon="?", side=-1))
    # オープニング（題名 2 秒）
    add(e("03-05") + 0.3, s("04-01") - 0.3, "title", {})
    # 05：ラベル（言うときに）
    add(w("05-02", "丸いふた"), e("05-02") + 0.5, "tag", dict(text="ふた", obj="senpai", dy=-150))
    add(w("05-03", "バンパー"), e("05-03") + 0.4, "tag", dict(text="バンパー", obj="senpai", dy=-150))
    add(w("05-04", "小さな窓"), e("05-04") + 0.4, "tag", dict(text="おなかの窓", obj="senpai", dy=-170))
    # 06：昔（セピアは組み立てで）・年
    add(w("06-02", "2002年"), e("06-03") + 0.3, "tag", dict(text="2002年ごろ", pos=(640, 110), size=56))
    # 07：まるロボ、目の光を消す
    add(e("07-05") - 2.6, e("07-05") + 0.3, "bubble", dict(obj="maru", icon="dizzy", side=1))
    # 08：「？」は 3D の輪で。
    # 10：光の物差し（言う瞬間）
    add(w("10-03", "光の物差し"), e("10-04") + 0.3, "tag", dict(text="光の物差し", obj="senpai", dy=-160, track_clip="S10a"))
    # 12：さきほどのスマホの地図（小窓）
    add(w("12-03", "さきほど"), e("12-05") + 0.2, "phone_pip", {})
    # 13：1 メートル・「？」
    add(w("13-03", "1メートル"), e("13-03") + 0.4, "tag", dict(text="1メートル", obj="onemeter", dy=-70, size=56))
    add(w("13-04", "「ここ」"), s("13-05") + 1.0, "bubble", dict(obj="ghost", icon="?", side=1))
    add(w("13-06", "どうやって") - 0.3, e("13-06") + 0.3, "bubble", dict(obj="senpai", icon="?", side=1))
    # 14：にわとりと卵
    add(w("14-01", "地図"), e("14-02") + 0.4, "loop", dict(a=w("14-01", "自分の場所"), b=w("14-02", "地図")))
    add(w("14-03", "にわとり"), e("14-04") + 0.3, "bubble", dict(obj="maru", icon="chicken_egg", side=1, big=True))
    # 15：車輪の数（数えながら 10 まで）・だいたいここ・ぴったりここ
    add(w("15-02", "数えて"), e("15-03") + 0.4, "counter", dict(t10=w("15-03", "10回")))
    add(w("15-04", "だいたいここ"), e("15-05") + 0.3, "tag", dict(text="だいたいここ", obj="disc", dy=-120, track_clip="S15c"))
    add(w("15-08", "ぴったりここ"), e("15-08") + 0.4, "tag", dict(text="ぴったりここ", obj="disc", dy=-120, track_clip="S15c", bg=YEL))
    # 16：首をかしげる
    add(s("16-06") + 0.1, e("16-06") + 0.4, "bubble", dict(obj="maru", icon="?", side=1, track_clip="S16c"))
    # 18：名前（言う瞬間）
    add(w("18-03", "カメラの先輩"), e("18-04") + 0.3, "tag", dict(text="カメラの先輩", obj="cam", dy=-130))
    # 19：照明が後ろへ（矢印）
    add(w("19-03", "後ろ") - 0.3, e("19-04") + 0.2, "arrow", dict(p0=(640, 140), p1=(640, 470)))
    # 20：迷子
    add(w("20-04", "くるくる"), e("20-05") + 0.3, "bubble", dict(obj="cam", icon="?", side=1, track_clip="S20a"))
    # 25：約束（2021 年・絵だけのカード。文は下の字幕にあるので、カードは絵で）
    add(w("25-05", "2021年"), e("25-06") + 0.3, "promise", dict(t2=w("25-06", "よけられなかったら"), t3=w("25-06", "新品")))
    add(s("25-07") + 0.25, s("25-07") + 1.6, "bubble", dict(obj="maru", icon="!", side=-1, track_clip="S25a"))
    # 26：前の場面の小窓（「ぶつかって曲がるだけだった」→ 昔の先輩）
    add(w("26-05", "ぶつかって"), e("26-05") + 0.2, "pip_clip", dict(clip="S06c", src_t=s("06-09") + 2.5, sepia=True))
    add(s("26-02"), e("26-04") + 0.2, "phone_pip", {})
    # 27：オチの地図
    add(e("27-02") - 0.5, s("27-05") - 0.2, "phone", dict(maru=True, ring_maru=w("27-03", "丸い形")))
    add(s("27-05") - 0.2, e("27-05") + 2.0, "phone_pip", dict(maru=True))
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
    key = ("bub", kind, big, side)
    if key not in _cache:
        wdt, hgt = (240, 140) if big else (120, 110)
        spr, off = D.bubble(wdt, hgt, (side * 40, 90), draw=icon_draw(kind))
        _cache[key] = (spr, off)
    return _cache[key]


def phone_sprite(maru=False, hl=None, ring=0.0, ring_maru=0.0, wdt=900):
    key = ("ph", maru, hl, round(ring, 2), round(ring_maru, 2), wdt)
    if key not in _cache:
        im = map_tex.phone_screen_land(maru=maru, hl=hl)
        BOX = map_tex.LAND_BOX
        dr = ImageDraw.Draw(im)
        if ring > 0:      # いまいる場所の点に、広がる輪
            P = map_tex.draw_map(Image.new("RGBA", im.size), BOX, dot=False)
            cx, cy = P(*map_tex.DOCK); r = 30 + 60 * ring
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=YEL + (255,), width=10)
        if ring_maru > 0:
            P = map_tex.draw_map(Image.new("RGBA", im.size), BOX, dot=False)
            cx, cy = P(0.0, 0.2); r = 50 + 30 * ring_maru
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=YEL + (255,), width=12)
        # 本体（ふち・角の丸い黒）
        W_, H_ = im.size; pad = 26
        body = Image.new("RGBA", (W_ + pad * 2, H_ + pad * 2), (0, 0, 0, 0))
        m = Image.new("L", body.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, body.width - 1, body.height - 1], 90, fill=255)
        body.paste((24, 28, 34, 255), (0, 0), m)
        m2 = Image.new("L", im.size, 0); ImageDraw.Draw(m2).rounded_rectangle([0, 0, W_ - 1, H_ - 1], 70, fill=255)
        body.paste(im, (pad, pad), m2)
        sc = wdt / body.width
        body = body.resize((wdt, int(body.height * sc)), Image.LANCZOS)
        sh = Image.new("RGBA", (body.width + 80, body.height + 80), (0, 0, 0, 0))
        sm = Image.new("L", sh.size, 0); ImageDraw.Draw(sm).rounded_rectangle([40, 52, 40 + body.width, 52 + body.height], 40, fill=110)
        sh.putalpha(sm.filter(ImageFilter.GaussianBlur(18)))
        sh.alpha_composite(body, (40, 40))
        _cache[key] = sh
    return _cache[key]


def title_sprite(fontdir):
    key = ("title",)
    if key not in _cache:
        spr, off = D.card(940, 300, draw=lambda d, W_, H_, ss, img: [D.ctext(d, (W_ / 2, H_ / 2 - 52 * ss), "ロボット掃除機は、", D.font(60 * ss), NAVY),
                                                                     D.ctext(d, (W_ / 2, H_ / 2 + 48 * ss), "どうやって部屋の形を覚える？", D.font(60 * ss), D.TEAL_D)])
        _cache[key] = spr
    return _cache[key]


def promise_sprite(stage):
    key = ("pr", stage)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            cy = H_ / 2 + 30 * ss
            # うんち
            x = W_ * 0.2
            for r_, dy in ((40, 30), (30, 0), (19, -26)):
                d.ellipse([x - r_ * ss, cy + (dy - r_ * 0.6) * ss, x + r_ * ss, cy + (dy + r_ * 0.6) * ss], fill=(122, 75, 42))
            if stage >= 1:   # よけられなかったら（× の印）→ 矢印
                D.cross_icon(d, x + 50 * ss, cy - 40 * ss, 22 * ss)
                d.line([W_ * 0.38, cy, W_ * 0.58, cy], fill=NAVY, width=10 * ss)
                d.polygon([(W_ * 0.62, cy), (W_ * 0.56, cy - 22 * ss), (W_ * 0.56, cy + 22 * ss)], fill=NAVY)
            if stage >= 2:   # 新品（箱と、ぴかぴかの先輩）
                bx = W_ * 0.8
                d.rounded_rectangle([bx - 70 * ss, cy - 40 * ss, bx + 70 * ss, cy + 50 * ss], 10 * ss, fill=(214, 170, 110))
                d.rectangle([bx - 70 * ss, cy - 10 * ss, bx + 70 * ss, cy + 2 * ss], fill=(190, 140, 80))
                d.ellipse([bx - 50 * ss, cy - 78 * ss, bx + 50 * ss, cy - 40 * ss], fill=(243, 245, 247), outline=(58, 63, 69), width=5 * ss)
                for k in range(3):
                    a = k * 2.1; d.line([bx + 60 * ss * math.cos(a) * 1.3, cy - 90 * ss + 20 * ss * math.sin(a), bx + 75 * ss * math.cos(a) * 1.3, cy - 100 * ss + 20 * ss * math.sin(a)], fill=YEL, width=5 * ss)
        spr, off = D.card(760, 330, draw=dr, header=(D.TEAL_D, "2021年"))
        _cache[key] = spr
    return _cache[key]


def arrow_sprite(p0, p1, col=YEL):
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line([p0, p1], fill=col + (255,), width=14)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    tip = p1; L_ = 38
    d.polygon([tip, (tip[0] - L_ * math.cos(a - 0.5), tip[1] - L_ * math.sin(a - 0.5)), (tip[0] - L_ * math.cos(a + 0.5), tip[1] - L_ * math.sin(a + 0.5))], fill=col + (255,))
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
                tail = (round((q[0] - cx) / 10) * 10, round((q[1] - 30 - cy) / 10) * 10) if q[1] - cy > 60 else None
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), tail=tail)
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            _paste(base, spr, cx + (off[0] + spr.width / 2), cy + (off[1] + spr.height / 2), k, a)
        elif kind == "bubble":
            q = where(p["obj"], t, p.get("track_clip"))
            if q is None: continue
            spr, off = bubble_sprite(p["icon"], p.get("big", False), p.get("side", 1))
            cx = q[0] - p.get("side", 1) * 40 - off[0] - spr.width / 2; cy = q[1] - 90 - (spr.height / 2 + off[1])
            cx = min(max(cx, spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(cy, spr.height / 2 + 10), SUB_TOP - spr.height / 2)
            _paste(base, spr, cx, cy, k, a)
        elif kind in ("phone", "phone_pip"):
            hl = None
            for th, nm in p.get("hl", []):
                if t >= th: hl = nm
            ring = (((t - p["ring"]) % 1.2) / 1.2) if "ring" in p and t >= p["ring"] else 0.0
            rm = min(1.0, (t - p["ring_maru"]) / 0.4) if "ring_maru" in p and t >= p["ring_maru"] else 0.0
            if kind == "phone":
                dim = Image.new("RGBA", base.size, (8, 14, 26, int(150 * a))); base.alpha_composite(dim)
                spr = phone_sprite(p.get("maru", False), hl, ring, rm, 900)
                _paste(base, spr, 640, 285, k, a)
            else:
                spr = phone_sprite(p.get("maru", False), None, 0.0, 0.0, 400)
                _paste(base, spr, 230, 140, k, a)
        elif kind == "title":
            dim = Image.new("RGBA", base.size, (8, 14, 26, int(120 * a))); base.alpha_composite(dim)
            _paste(base, title_sprite(fontdir), 640, 300, k, a)
        elif kind == "promise":
            st = 0 + (1 if t >= p["t2"] else 0) + (1 if t >= p["t3"] else 0)
            _paste(base, promise_sprite(st), 640, 270, k, a)
        elif kind == "counter":
            n = int(min(10, max(1, 1 + 9 * (t - t0) / max(0.1, p["t10"] - t0))))
            txt = "車輪 %d回" % n
            spr, off = tag_sprite(txt, 60, YEL if n == 10 else WHITE)
            _paste(base, spr, 640 + off[0] + spr.width / 2, 110 + off[1] + spr.height / 2, k, a)
        elif kind == "loop":   # 地図 ⇄ 自分の場所
            for txt, x_, tt in (("地図", 360, t0), ("自分の場所", 920, p["a"])):
                if t >= tt:
                    spr, off = tag_sprite(txt, 52)
                    _paste(base, spr, x_ + off[0] + spr.width / 2, 110 + off[1] + spr.height / 2, *_pop(t, tt, t1))
            if t >= p["a"]: base.alpha_composite(arrow_sprite((790, 180), (440, 180), TEAL))      # 自分の場所 → 地図（地図を描くには、自分の場所が要る）
            if t >= p["b"]: base.alpha_composite(arrow_sprite((440, 225), (790, 225), D.ORANGE))  # 地図 → 自分の場所
        elif kind == "arrow":
            base.alpha_composite(arrow_sprite(p["p0"], p["p1"]))
        elif kind == "pip_clip" and frame_of:
            im = frame_of(p["clip"], p["src_t"] + (t - t0))
            if im is None: continue
            im = im.convert("RGB").resize((400, 225), Image.LANCZOS)
            if p.get("sepia"): im = sepia(im)
            fr = Image.new("RGBA", (412, 237), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            _paste(base, fr, 230, 150, k, a)
    return base


def sepia(im):
    g = im.convert("L")
    return Image.merge("RGB", (g.point(lambda v: min(255, int(v * 1.07 + 18))), g.point(lambda v: int(v * 0.92 + 8)), g.point(lambda v: int(v * 0.74))))
