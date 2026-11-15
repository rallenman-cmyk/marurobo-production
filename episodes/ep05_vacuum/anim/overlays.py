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
TEAL = (33, 193, 179); YEL = (255, 210, 74); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48)
SUB_TOP = 560


def ev_list():
    E = []
    add = lambda *a: E.append(a)
    # 02：スマホに地図（大きく）。言うたびに家具が光る・いまいる場所の点に輪
    # （2026-11-14 v2：大きな 2D のスマホの絵はやめ、3D のスマホに寄る。家具が光る・輪も 3D の画面の中で。scenes.py の phone_seq）
    add(e("02-01") - 0.2, s("02-02") - 0.15, "bubble", dict(obj="maru", icon="!", side=-1))     # スマホがついて、びくっ（大きなスマホの絵より前に）
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
    add(w("10-03", "光の物差し"), e("10-04") + 0.3, "tag", dict(text="光の物差し", pos=(1040, 90)))
    # 11：「ここは壁。ここは、ソファの足」（点の上に黄色い輪。暗い中でも見えるように 2D で）
    add(w("11-05", "壁"), e("11-05") + 0.8, "ring2d", dict(obj="wallpt", r=34))
    add(w("11-05", "ソファ"), e("11-05") + 0.8, "ring2d", dict(obj="sofaleg", r=26))
    # 12：さきほどのスマホの地図（小窓）
    add(w("12-03", "さきほど"), e("12-05") + 0.2, "pip_clip", dict(clip='S02a', src_t=s("02-04") + 0.3, hold=True, crop=(0.06, 0.04, 0.9, 0.88)))   # 3D のスマホの寄りの絵（v2）
    # 13：1 メートル・「？」
    add(w("13-03", "1メートル"), e("13-03") + 0.4, "tag", dict(text="1メートル", obj="onemeter", dy=-70, size=56))
    #   （v3：「ここ」が分からない、が伝わらない → 「ここから」で先輩に「ここ」の札。「ここ」で先輩が消え、点と線が当てずっぽうに動き回る（3D）。
    #    「先輩がどこにいたか」で、先輩を赤い枠で囲む）
    add(w("13-03", "ここから"), w("13-04", "「ここ」") + 0.1, "tag", dict(text="ここ", obj="senpai", dy=-110, bg=YEL))
    add(w("13-04", "「ここ」") + 0.2, s("13-05") + 0.3, "bubble", dict(obj="ghost", icon="?", side=1))
    add(w("13-05", "先輩がどこに"), e("13-05") + 0.4, "frame2d", dict(obj="senpai", r=62, col=RED))
    add(w("13-06", "どうやって") - 0.3, e("13-06") + 0.3, "bubble", dict(obj="senpai", icon="?", side=1))
    # 14：にわとりと卵
    add(w("14-01", "地図"), e("14-02") + 0.4, "loop", dict(a=w("14-01", "自分の場所"), b=w("14-02", "地図")))
    add(w("14-03", "にわとり"), e("14-04") + 0.3, "bubble", dict(obj="maru", icon="chicken_egg", side=1, big=True))
    # 15：車輪の数（数えながら 10 まで）・だいたいここ・ぴったりここ
    add(w("15-02", "数えて"), e("15-03") + 0.4, "counter", dict(t10=w("15-03", "10回")))
    add(w("15-04", "だいたいここ"), e("15-05") + 0.3, "tag", dict(text="だいたいここ", obj="disc", dy=-120, track_clip="S15c"))
    add(w("15-08", "ぴったりここ"), e("15-08") + 0.4, "tag", dict(text="ぴったりここ", obj="disc", dy=-120, track_clip="S15c", bg=YEL))
    # v3：いま見えている形（白）を地図（青緑）に合わせる、が分かるように名前の札
    add(w("15-06", "いま見えている") + 0.3, w("15-08", "ぴったり") - 0.1, "tag", dict(text="いま見えている壁", obj="curshape", dy=-70, track_clip="S15c", size=44))
    # 16：車輪が空回り（v3：車輪のまわりで回る矢印。車輪は 3D で速く回る）
    add(w("16-03", "空回り") - 0.4, e("16-04") + 0.3, "spin", dict(obj="wheel_r", r=58, track_clip="S16b"))
    # 16：首をかしげる
    add(s("16-06") + 0.1, e("16-06") + 0.4, "bubble", dict(obj="maru", icon="?", side=1, track_clip="S16c"))
    # 17-07（v3）：上から見た 2 本の壁の間に、両向きの矢印と「同じ壁」の札（引き戻す前に消す）
    add(w("17-07", "一つの壁") + 0.3, w("17-08", "ぐっと") - 0.1, "darrow", dict(a="wall1", b="wall2", text="同じ壁", track_clip="S17c"))
    # 18：名前（言う瞬間）
    add(w("18-03", "カメラの先輩"), s("18-04") - 0.1, "tag", dict(text="カメラの先輩", obj="cam", dy=-130))
    # v3：「前にカメラ」で、前のカメラを黄色い輪で囲み「カメラ」の札（5本目 v2「前のカメラがどれかわかんない」）
    add(w("18-04", "カメラ"), e("18-04") + 0.5, "ring2d", dict(obj="camlens", r=40, track_clip="S18a"))
    add(w("18-04", "カメラ"), e("18-04") + 0.5, "tag", dict(text="カメラ", obj="camlens", dy=-120, track_clip="S18a"))
    # 19：照明が後ろへ（矢印）
    add(w("19-03", "後ろ") - 0.3, e("19-04") + 0.2, "arrow", dict(p0=(640, 140), p1=(640, 470)))
    # 19（v3）：カメラの先輩から見た絵だと分かるように、四すみにカメラの枠（5本目 v2「前のカメラがどれかわかんない」）
    add(s("19-01"), s("20-01"), "viewfinder", {})
    # 20：迷子
    add(w("20-04", "くるくる"), e("20-05") + 0.3, "bubble", dict(obj="cam", icon="?", side=1, track_clip="S20a", gap=95))   # v3：先輩に重ならないよう高く
    # 25：約束（2021 年・絵だけのカード。文は下の字幕にあるので、カードは絵で）
    #   （v2：カードはやめ、3D の赤い×と新しい箱で見せる。年だけ札で）
    add(w("25-05", "2021年"), s("25-07") - 0.1, "tag", dict(text="2021年", pos=(640, 110), size=56))
    # v3：25-06 はテレビの広告（3D の S25c）。まわりにテレビのふち
    add(s("25-06"), s("25-07"), "tv", {})
    add(s("25-07") + 0.25, s("25-07") + 1.6, "bubble", dict(obj="maru", icon="!", side=-1, track_clip="S25d"))
    # 26：前の場面の小窓（「ぶつかって曲がるだけだった」→ 昔の先輩）
    add(w("26-05", "ぶつかって"), e("26-05") + 0.2, "pip_clip", dict(clip="S06c", src_t=s("06-09") + 2.5, sepia=True))
    add(s("26-02"), e("26-04") + 0.2, "pip_clip", dict(clip='S02a', src_t=s("02-04") + 0.3, hold=True, crop=(0.06, 0.04, 0.9, 0.88)))
    # 27：オチの地図
    add(s("27-05"), e("27-05") + 2.0, "pip_clip", dict(clip='S27b', src_t=e("27-04") - 0.3, hold=True, crop=(0.06, 0.04, 0.9, 0.88)))
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


def arrow_sprite(p0, p1, col=YEL, hs=1.0):
    """矢印（v3：先が潰れて見えた → 2 倍で描いて縮める・線は頭の付け根で止める・頭を大きく 1 つの三角に。5本目 v2）"""
    key = ("arrow", p0, p1, col, hs)
    if key in _cache: return _cache[key]
    S2 = 2; im = Image.new("RGBA", (1280 * S2, 720 * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); ca, sa = math.cos(a), math.sin(a)
    L_, Hw, lw = 52 * hs, 30 * hs, round(14 * min(1.0, hs + 0.2))
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
            spr, off = bubble_sprite(p["icon"], p.get("big", False), p.get("side", 1))
            cx = q[0] + p.get("dx", 0); cy = q[1] - p.get("gap", 40) - spr.height / 2
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
            hs = max(0.45, min(1.0, (L / 2 - 14) / 70))      # 短い矢印は頭も小さく（2 つの頭が重ならない）
            im = arrow_sprite((round(mid[0]), round(mid[1])), (round(pb[0]), round(pb[1])), WHITE, hs).copy(); im.alpha_composite(arrow_sprite((round(mid[0]), round(mid[1])), (round(pa[0]), round(pa[1])), WHITE, hs))
            sh = Image.new("RGBA", im.size, (20, 24, 30, 0)); sh.putalpha(im.getchannel("A").filter(ImageFilter.MaxFilter(7)))   # 暗いふち（明るい点の上でも見える）
            sh.alpha_composite(im); im = sh
            if a < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            base.alpha_composite(im)
            spr, off = tag_sprite(p["text"], 48)
            _paste(base, spr, mid[0] + spr.width / 2 - 30, max(pa[1], pb[1]) + 26 + spr.height / 2, k, a)    # 矢印の下に（矢印・点の線に重ねない）
        elif kind == "tv":        # テレビのふち（黒い枠・下に小さな電源の光）。枠は 0.25 秒で出る
            kk = min(1.0, (t - t0) / 0.25) * a
            bw = int(34 * kk) + 1; im = Image.new("RGBA", base.size, (0, 0, 0, 0)); d_ = ImageDraw.Draw(im)
            m_ = Image.new("L", base.size, 255); ImageDraw.Draw(m_).rounded_rectangle([bw, bw, 1279 - bw, 719 - bw], 26, fill=0)
            im.paste((22, 25, 30, 255), (0, 0), m_)
            if kk > 0.9: d_.ellipse([1280 - 70, 720 - 24, 1280 - 60, 720 - 14], fill=(90, 230, 140, 255))
            base.alpha_composite(im)
        elif kind == "viewfinder":   # カメラの枠（四すみのかぎ）
            im = Image.new("RGBA", base.size, (0, 0, 0, 0)); d_ = ImageDraw.Draw(im); col = WHITE + (int(230 * a),); L_ = 60; m0 = 40
            for (x, y, sx, sy) in ((m0, m0, 1, 1), (1280 - m0, m0, -1, 1), (m0, 720 - m0 - 170, 1, -1), (1280 - m0, 720 - m0 - 170, -1, -1)):
                d_.line([(x, y), (x + sx * L_, y)], fill=col, width=6); d_.line([(x, y), (x, y + sy * L_)], fill=col, width=6)
            d_.ellipse([m0 + 24, m0 + 24, m0 + 42, m0 + 42], fill=(235, 70, 60, int(230 * a)))
            base.alpha_composite(im)
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
            im = im.resize((400, 225), Image.LANCZOS)
            if p.get("sepia"): im = sepia(im)
            fr = Image.new("RGBA", (412, 237), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            _paste(base, fr, 230, 150, k, a)
    return base


def sepia(im):
    g = im.convert("L")
    return Image.merge("RGB", (g.point(lambda v: min(255, int(v * 1.07 + 18))), g.point(lambda v: int(v * 0.92 + 8)), g.point(lambda v: int(v * 0.74))))
