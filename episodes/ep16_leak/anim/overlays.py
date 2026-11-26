# 16本目（情報流出）：3D の上に重ねる 2D（札・吹き出し・題名・小窓・輪・メールの文・名札の絵・ニュースの見出し・数の図・遠くから操作する図・巻きもどし・想像の色）
#   9本目の overlays.py を写して、この回の札にした。一覧 EVENTS：(始め, 終わり, 種類, 中身)。時刻は声の時刻（timing.py）
#   決まり：札の答えは、その言葉を言う瞬間に出す（SKILL §3）。字幕の帯（y 560 より下）に置かない。下の字幕と同じことを上に書かない（単語・数字・ラベルだけ）
#   字の大きさ：数字は 56 以上、ほかは 44〜48（1280×720。スマホで読める大きさ）。3D の中に字を書かないので、字は全部ここ。絵コンテ表：../絵コンテ_v1.md
#   色：まるロボの名札＝青緑。出入口の機械＝青緑、遠くから操作するしくみ＝橙。注目＝赤
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep04_robot", "look"))
import design as D
import timing as T
s, e, w = T.s, T.e, T.w
YEL = (255, 201, 40); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48)
ORANGE = (255, 138, 31); PURPLE = (138, 77, 255); TEAL = D.TEAL
import icons16 as IC
GREY = (190, 198, 210)
SUB_TOP = 560
_cache = {}
EVENTS = None


def ev_list():
    """絵コンテ_v1.md と見比べて作る（冒頭・1章）"""
    E = []
    add = lambda *a: E.append(a)
    # 冒頭
    add(w("01-03", "セール") - 0.2, w("02-02", "え") - 0.15, "bubble", dict(obj="maru_top", icon="sale"))      # 表どおり 02-02 の「え？」で消す（v1：開く所で消えていた）
    add(s("02-01") - 0.05, e("02-01") + 0.3, "mailcard", {})
    add(w("02-02", "え") - 0.05, w("02-02", "え") + 1.1, "bubble", dict(obj="maru_top", icon="!"))
    add(s("02-03") + 0.05, e("02-03") + 0.3, "pip_clip", dict(clip="P02", src_t=s("02-03") + 0.05))
    add(s("02-04"), e("02-08") + 0.4, "form", dict(lit=[w("02-05", "名前"), w("02-05", "住所"), w("02-05", "電話"), w("02-05", "メール")],
                                                   fly=w("02-06", "知らない"), back=s("02-07"), extra=w("02-08", "誕生日")))
    add(w("02-08", "安心") + 0.1, e("02-08") + 0.4, "bubble", dict(obj="maru_top", icon="?", pos=(1000, 650)))   # 上の札と重ねない（まるロボの右）
    add(w("04-01", "流出の発表") - 0.3, e("04-01") + 0.3, "headlines", {})
    add(w("04-03", "どこから") - 0.2, e("04-03") + 0.3, "qmark", dict(pos=(860, 250), size=190))      # v1 の点検：町の上の？が小さかった
    add(s("04-05") - 0.05, e("04-05") + 0.5, "title", {})
    add(w("05-02", "お城") - 0.1, e("05-02") + 0.3, "tag", dict(text="会社 → お城", pos=(640, 120), size=52))
    add(w("05-03", "名札") - 0.1, e("05-03") + 0.3, "tag", dict(text="1人分の情報 → 名札", pos=(640, 120), size=52))
    add(w("05-04", "鍵") - 0.1, e("05-04") + 0.3, "tag", dict(text="IDとパスワード → 鍵", pos=(640, 120), size=52))
    # 1章
    add(w("06-04", "どうやって") - 0.3, e("06-04") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("07-01"), e("07-01") + 0.2, "tint", {})
    add(w("07-03", "どこから") - 0.3, e("07-03") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(w("08-02", "小さな扉"), e("08-02") + 0.4, "ring", dict(obj="door", r=150, col=RED))     # 扉の全体を囲む（v1 の確認役：何もない所に小さな丸）
    add(w("08-04", "うしろ") + 0.3, w("08-04", "うしろ") + 1.6, "bubble", dict(obj="maru_top", icon="!"))
    add(w("09-01", "裏口"), e("09-01") + 0.3, "tag", dict(text="裏口", obj="door", dy=-150, size=52))
    add(w("09-02", "なぜ") - 0.3, e("09-02") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("09-03") + 0.05, e("09-03") + 0.3, "pip_clip", dict(clip="P09", src_t=s("09-03") + 0.05))
    add(s("09-04") + 0.2, e("09-04") + 0.3, "pathfig", dict(t_line=w("09-04", "外から") - 0.1))      # 家 → 点線 → お城の裏口（v1 の確認役：「外から入れるように」が絵に出ていなかった）
    add(w("09-05", "出入口の機械"), e("09-05") + 0.3, "tag", dict(text="外から会社につなぐ出入口の機械", pos=(640, 100), size=44))
    add(w("09-06", "ねらわれ"), e("09-06") + 0.3, "ring", dict(obj="door", r=170, col=RED))
    add(w("10-04", "プログラム") - 0.2, e("10-04") + 0.3, "tag", dict(text="新しいプログラム", obj="box", dy=-110, size=44))
    add(w("10-06", "弱い所") - 0.2, e("10-06") + 0.3, "ring", dict(obj="lockhole", r=46, col=RED))      # 穴のまわり（v2：錠のまん中に出て、穴から左にずれた）
    add(w("10-08", "誕生日"), e("10-08") + 0.3, "tag", dict(text="誕生日", pos=(470, 110), size=52))
    add(w("10-08", "1234"), e("10-08") + 0.3, "tag", dict(text="1234", pos=(800, 110), size=56))
    add(s("11-02") - 0.05, e("11-09") + 0.4, "fig92", dict(t_co=s("11-03") + 0.2, t_fill=w("11-03", "どこから") - 0.1, t92=w("11-03", "92件") - 0.2, t61=w("11-04", "61件") - 0.2, t61b=w("11-04", "出入口") - 0.1, t19=w("11-08", "19件") - 0.2,
                                                        t80=w("11-09", "80件") - 0.2, small=(s("11-05"), s("11-08") - 0.05)))     # 11-08 の頭から図に戻す（v1：「ここから入られたのが」の間、図がなかった）
    add(w("11-06", "家に") - 0.2, e("11-07") + 0.3, "remote", dict(ghost=w("11-07", "座って") - 0.2))
    add(s("12-01") - 0.05, s("12-01") + 1.6, "rewind", {})
    add(w("12-05", "ID") - 0.1, e("12-05") + 0.3, "tag", dict(text="働く人のIDとパスワード", obj="key", dy=-120, size=44))
    add(w("12-07", "どこから") - 0.2, e("12-07") + 0.3, "qmark", dict(obj="door", dy=-170))      # 鍵は影と一緒に動くので、扉の上に止めて出す（v1：？が飛び回った）
    add(max(w("12-08", "古い") - 0.1, s("12-08") + 0.45), e("12-08") + 0.4, "tag", dict(text="古いままの錠", obj="i_lock", dy=-110, size=48))
    add(w("12-08", "かんたん") - 0.1, e("12-08") + 0.4, "tag", dict(text="かんたんな鍵", obj="i_skey", dy=-200, size=48))
    add(w("12-08", "漏れた") - 0.1, e("12-08") + 0.4, "tag", dict(text="漏れた鍵", obj="i_key", dy=-110, size=48))
    import overlays2 as OV2      # 2章（S13〜S17）
    E += OV2.ev_list2()
    import overlays3 as OV3      # 3章（S18〜S21）
    E += OV3.ev_list3()
    import overlays4 as OV4      # 4章（S22〜S24）
    E += OV4.ev_list4()
    import overlays5 as OV5      # 5章（S25〜S26）
    E += OV5.ev_list5()
    import overlays6 as OV6      # 6章（S27〜S29）
    E += OV6.ev_list6()
    import overlays7 as OV7      # 7章（S30〜S32）
    E += OV7.ev_list7()
    import overlays8 as OV8      # 8章（S33〜S35）
    E += OV8.ev_list8()
    return E


def sfx_list():
    """札・図に合わせて鳴らす音（絵コンテ表の音。v1 の確認役：表の音が入っていなかった）：(時刻, 種類, 大きさ)"""
    L = []
    for i in range(4): L.append((w("04-01", "流出の発表") - 0.3 + i * 0.45, "paper", 0.35))     # 見出しが重なる「ぱさ」
    for k in ("名前", "住所", "電話", "メール"): L.append((w("02-05", k), "tick", 0.3))     # 光るたび「ピッ」
    L.append((w("02-06", "知らない"), "swish", 0.35))      # 4 つが飛んでいく「ひゅっ」
    L.append((s("12-01") - 0.05, "rewind", 0.4))           # 時間を巻きもどす
    L.append((s("07-02") + 0.05, "swish", 0.3))            # 想像の場面から戻る「しゅっ」
    import overlays2 as OV2
    L += OV2.sfx_list2()
    import overlays3 as OV3
    L += OV3.sfx_list3()
    import overlays4 as OV4
    L += OV4.sfx_list4()
    import overlays5 as OV5
    L += OV5.sfx_list5()
    import overlays6 as OV6
    L += OV6.sfx_list6()
    import overlays7 as OV7
    L += OV7.sfx_list7()
    import overlays8 as OV8
    L += OV8.sfx_list8()
    return L


def _pop(t, t0, t1):
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
    key = ("tag", text, size, bg, fg, tail)
    if key not in _cache:
        _cache[key] = D.pill(text, size, fg=fg or NAVY, bg=bg, tail=tail)
    return _cache[key]


def icon_draw(kind):
    def dr(d, cx, cy, ss, img):
        f = D.font(80 * ss)
        if kind in ("?", "!"):
            D.ctext(d, (cx, cy), kind, f, NAVY if kind != "!" else D.ORANGE)
        elif kind == "coin":   # 7章 30-06：硬貨 2 枚（字なし。金色の丸）
            for dx, dy in ((-14, 8), (14, -8)):
                r_ = 26 * ss
                d.ellipse((cx + dx * ss - r_, cy + dy * ss - r_, cx + dx * ss + r_, cy + dy * ss + r_), fill=(236, 190, 70), outline=(176, 132, 30), width=int(4 * ss))
                d.ellipse((cx + dx * ss - r_ * 0.55, cy + dy * ss - r_ * 0.55, cx + dx * ss + r_ * 0.55, cy + dy * ss + r_ * 0.55), outline=(250, 222, 130), width=int(3 * ss))
        elif kind == "sale":   # セールの値札の絵（字なし。赤い札に白い丸）
            r_ = 30 * ss
            d.polygon([(cx - r_, cy - r_ * 0.7), (cx + r_ * 0.6, cy - r_ * 0.7), (cx + r_, cy), (cx + r_ * 0.6, cy + r_ * 0.7), (cx - r_, cy + r_ * 0.7)], fill=RED)
            d.ellipse((cx + r_ * 0.35, cy - r_ * 0.15, cx + r_ * 0.65, cy + r_ * 0.15), fill=WHITE)
    return dr


def bubble_sprite(kind):
    key = ("bub", kind)
    if key not in _cache:
        _cache[key] = D.bubble(120, 110, (0, 0), draw=icon_draw(kind))
    return _cache[key]


def title_sprite():
    key = ("title",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            f = D.font(64 * ss); a_, b_ = "盗まれた情報は、", "どこへ行く？"
            wa, wb = d.textlength(a_, font=f), d.textlength(b_, font=f); x0 = W_ / 2 - (wa + wb) / 2     # 2 つの幅を測って、続けて並べる（v1 の点検：「は」と「ど」が重なっていた）
            D.ctext(d, (x0 + wa / 2, H_ / 2), a_, f, NAVY); D.ctext(d, (x0 + wa + wb / 2, H_ / 2), b_, f, (214, 150, 0))
        spr, off = D.card(1000, 230, draw=dr)
        _cache[key] = spr
    return _cache[key]


def mailcard_sprite():
    """02-01：メールの大事な文（お店の印つき）"""
    key = ("mailcard",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            IC.castle_logo(d, 90 * ss, H_ / 2, 46 * ss)
            D.ctext(d, (W_ / 2 + 55 * ss, H_ / 2 - 40 * ss), "お客さまの情報が、", D.font(50 * ss), NAVY)
            D.ctext(d, (W_ / 2 + 55 * ss, H_ / 2 + 40 * ss), "流出したおそれがあります", D.font(50 * ss), RED)
        _cache[key] = D.card(820, 210, draw=dr)[0]
    return _cache[key]


def form_sprite(t, p):
    """02-04〜02-08：会員になるときに預けた 4 つ（顔＝名前・家＝住所・電話・手紙＝メール）。言う順に光る → 外へ飛ぶ → 戻る → 誕生日と勤め先に灰色の×"""
    W_, H_ = 1000, 300; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, 240))
    names = ["名前", "住所", "電話", "メール"]; kinds = ["face", "house", "phone", "mail"]
    gone = p["fly"] <= t < p["back"]
    for i, (kd, nm) in enumerate(zip(kinds, names)):
        cx = (130 + i * 190) * S2; cy = 120 * S2
        if gone:
            u = min(1.0, (t - p["fly"]) / 0.8); cx += int((i - 1.5) * 260 * u * S2); cy -= int(260 * u * S2)
            if u >= 1.0: continue
        lit = t >= p["lit"][i]
        if lit and not gone: d.ellipse((cx - 72 * S2, cy - 72 * S2, cx + 72 * S2, cy + 72 * S2), fill=(210, 248, 243, 255))
        IC.icon(d, kd, cx, cy, 46 * S2, NAVY)
        if lit and not gone: D.ctext(d, (cx, 240 * S2), nm, D.font(40 * S2), NAVY)
    if t >= p["extra"]:
        for j, kd in enumerate(("cake", "bldg")):
            cx = 885 * S2; cy = (82 + j * 136) * S2
            d.rounded_rectangle((cx - 62 * S2, cy - 62 * S2, cx + 62 * S2, cy + 62 * S2), radius=16 * S2, fill=(236, 238, 242, 255))     # 4 つとは別の灰色の地（預けていない物）
            IC.icon(d, kd, cx, cy, 54 * S2, (110, 118, 132))
            r_ = 48 * S2; d.line((cx - r_, cy - r_, cx + r_, cy + r_), fill=RED + (230,), width=10 * S2); d.line((cx - r_, cy + r_, cx + r_, cy - r_), fill=RED + (230,), width=10 * S2)     # 太い赤の×
    if t >= p["back"] and t < p["extra"] + 0.01:
        f = D.font(44 * S2); D.ctext(d, (850 * S2, 150 * S2), "4つ", f, D.TEAL_D)
    if gone and t >= p["fly"] + 0.8:     # 4 つが飛んでいったあとの札：大きな「？」（v1 の確認役：空の札だけが 3 秒残った）
        D.ctext(d, (W_ * S2 / 2 - 80 * S2, 140 * S2), "？", D.font(150 * S2), RED)
    return im.resize((760, 228), Image.LANCZOS)      # 小さくして左上へ（v1 の確認役：まるロボの顔と体を 26 秒かくしていた）


def pathfig_sprite(t, p):
    """09-04：外の家から、お城の裏口まで点線がのびる（外からでも入れる入口）"""
    W_, H_ = 900, 260; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, 245))
    IC.icon(d, "house", 130 * S2, 120 * S2, 70 * S2, NAVY); D.ctext(d, (130 * S2, 220 * S2), "家", D.font(40 * S2), NAVY)
    IC.castle_logo(d, 770 * S2, 120 * S2, 70 * S2); D.ctext(d, (770 * S2, 220 * S2), "会社", D.font(40 * S2), NAVY)
    d.rounded_rectangle((744 * S2, 128 * S2, 796 * S2, 190 * S2), radius=6 * S2, fill=(124, 100, 72, 255))     # 裏口
    n = 0 if t < p["t_line"] else min(10, int((t - p["t_line"]) / 0.12) + 1)
    for k in range(n):
        x = (230 + k * 46) * S2; d.ellipse((x, 152 * S2, x + 16 * S2, 168 * S2), fill=(255, 138, 31, 255))
    return im.resize((W_, H_), Image.LANCZOS)


def headlines_sprite(t, t0):
    """04-01：ニュースの見出しの絵（会社の名前は書かない。「流出」の字と、架空の印だけ）。少しずつずらして重ねる"""
    W_, H_ = 900, 420; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cols = [(120, 96, 170), (70, 130, 200), (220, 120, 60), (80, 160, 110)]
    for k in range(4):
        if t < t0 + k * 0.45: break
        x0 = (60 + k * 70) * S2; y0 = (30 + k * 75) * S2
        d.rounded_rectangle((x0, y0, x0 + 560 * S2, y0 + 150 * S2), radius=18 * S2, fill=(255, 255, 255, 255), outline=(200, 206, 214, 255), width=3 * S2)
        IC.castle_logo(d, x0 + 70 * S2, y0 + 75 * S2, 42 * S2, cols[k])
        D.ctext(d, (x0 + 210 * S2, y0 + 72 * S2), "流出", D.font(64 * S2), RED)
        for j, ww in enumerate((200, 170)):
            d.rounded_rectangle((x0 + 300 * S2, y0 + (50 + j * 34) * S2, x0 + (300 + ww) * S2, y0 + (64 + j * 34) * S2), radius=6 * S2, fill=GREY + (255,))
    return im.resize((W_, H_), Image.LANCZOS)


def qmark_sprite(sz=120):
    key = ("qmark", sz)
    if key not in _cache:
        im = Image.new("RGBA", (240, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.ellipse((20, 20, 220, 220), fill=(255, 255, 255, 235)); D.ctext(d, (120, 118), "？", D.font(150), RED)
        _cache[key] = im.resize((sz, sz), Image.LANCZOS)
    return _cache[key]


def fig92_sprite(t, p):
    """11：2025年の警察のまとめ。どこから入られたかが分かった 92 件（小さな扉の形を 92 個）。61 件＝青緑、19 件＝橙、合わせて 80 件に赤い丸"""
    W_, H_ = 1000, 480; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, 245))
    D.ctext(d, (W_ * S2 / 2, 42 * S2), "2025年 警察のまとめ", D.font(40 * S2), NAVY)
    tf = p.get("t_fill", p["t92"] - 0.9)      # マスは「どこから入られたか」から並び始め、「92件」の言葉でそろう（v1：書類の絵だけが 12 秒続いた）
    n_show = 0 if t < tf else min(92, int((t - tf) / max(0.9, p["t92"] - tf) * 92) + 1)
    if n_show == 0:      # 11-02「警察のまとめを見てみます」：書類の束の絵（v1 の点検：何もない白い札が 5 秒出ていた）
        for k_ in range(3):
            x0_, y0_ = (400 + k_ * 26) * S2, (110 + k_ * 22) * S2
            d.rounded_rectangle((x0_, y0_, x0_ + 200 * S2, y0_ + 260 * S2), radius=14 * S2, fill=(250, 251, 253, 255), outline=(150, 160, 176, 255), width=4 * S2)
        for j_ in range(6):
            yy_ = (200 + j_ * 30) * S2; d.rounded_rectangle((480 * S2, yy_, (480 + [150, 120, 150, 100, 140, 90][j_]) * S2, yy_ + 12 * S2), radius=5 * S2, fill=GREY + (255,))
        if "t_co" in p and t >= p["t_co"]:      # 「泥棒に入られた会社に聞いて」：入られた会社（お城の印）が左右に並んでいく
            step_ = min(0.25, max(0.08, (p["t_fill"] - p["t_co"] - 0.6) / 8))     # 8 つを、マスが並び始める 0.6 秒前までに出し終える（v1：5 つ目が出た直後に図が替わり「右に何か一瞬」）
            m_ = min(8, int((t - p["t_co"]) / step_) + 1)
            for i_ in range(m_):
                cx_ = (150 + (i_ % 2) * 100) * S2 if i_ < 4 else (750 + (i_ % 2) * 100) * S2; cy_ = (150 + (i_ % 4 // 2) * 120) * S2
                IC.castle_logo(d, cx_, cy_, 36 * S2)
    for i in range(n_show):
        r_, c_ = divmod(i, 23)
        x = (70 + c_ * 25) * S2; y = (100 + r_ * 52) * S2
        col = GREY
        if t >= p["t61"] and i < 61: col = (33, 193, 179)
        if t >= p["t19"] and 61 <= i < 80: col = (255, 138, 31)
        d.rounded_rectangle((x, y, x + 18 * S2, y + 36 * S2), radius=6 * S2, fill=col + (255,))
        d.ellipse((x + 12 * S2, y + 17 * S2, x + 16 * S2, y + 21 * S2), fill=(255, 255, 255, 255))
    if t >= p["t92"]: D.ctext(d, (870 * S2, 160 * S2), "92件", D.font(60 * S2), NAVY)
    if t >= p["t61"]: D.ctext(d, (240 * S2, 345 * S2), "出入口の機械 61件" if t >= p.get("t61b", 0) else "61件", D.font(40 * S2), (18, 140, 130))     # 「出入口の機械」は言ってから足す（v2 の確認役：先に出ていた）
    if t >= p["t19"]: D.ctext(d, (640 * S2, 345 * S2), "遠くから操作 19件", D.font(40 * S2), (214, 104, 0))
    if t >= p["t80"]:
        pts = [(60, 90), (648, 90), (648, 247), (348, 247), (348, 300), (60, 300), (60, 90)]      # 3 段と 4 段目の 11 個（80 個）だけ（v1 の確認役：灰色まで囲っていた）
        d.line([(x * S2, y * S2) for x, y in pts], fill=RED + (255,), width=8 * S2, joint="curve")
        D.ctext(d, (500 * S2, 420 * S2), "合わせて 80件", D.font(60 * S2), RED)
    return im.resize((W_, H_), Image.LANCZOS)


def _pc(d, x, y, S2, scr, cursor=None):
    d.rounded_rectangle((x, y, x + 260 * S2, y + 170 * S2), radius=10 * S2, fill=(43, 47, 54, 255))
    d.rectangle((x + 12 * S2, y + 12 * S2, x + 248 * S2, y + 158 * S2), fill=scr)
    d.rectangle((x + 110 * S2, y + 170 * S2, x + 150 * S2, y + 200 * S2), fill=(43, 47, 54, 255))
    d.rounded_rectangle((x + 60 * S2, y + 200 * S2, x + 200 * S2, y + 212 * S2), radius=5 * S2, fill=(43, 47, 54, 255))
    # 画面の中身（会社の書類の絵。字の代わりの線）
    for j, ww in enumerate((150, 190, 120)):
        d.rounded_rectangle((x + 40 * S2, y + (40 + j * 30) * S2, x + (40 + ww) * S2, y + (52 + j * 30) * S2), radius=4 * S2, fill=(170, 182, 200, 255))
    if cursor:
        cx, cy = x + cursor[0] * S2, y + cursor[1] * S2
        d.polygon([(cx, cy), (cx, cy + 26 * S2), (cx + 8 * S2, cy + 19 * S2), (cx + 18 * S2, cy + 19 * S2)], fill=(20, 20, 20, 255))


def remote_sprite(t, t0, p):
    """11-06〜11-07：遠くから操作するしくみ。左に家のパソコン、右に会社のパソコン。家の画面に会社の画面がそのまま映り、家でマウスを動かすと会社の画面の矢印も動く"""
    W_, H_ = 900, 330; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, 245))
    u = (t - t0) % 2.4 / 2.4; cur = (120 + 80 * math.sin(2 * math.pi * u), 90 + 30 * math.cos(2 * math.pi * u))
    _pc(d, 60 * S2, 70 * S2, S2, (232, 240, 250, 255), cur)
    _pc(d, 580 * S2, 70 * S2, S2, (232, 240, 250, 255), cur)
    D.ctext(d, (190 * S2, 38 * S2), "家", D.font(40 * S2), NAVY); D.ctext(d, (710 * S2, 38 * S2), "会社", D.font(40 * S2), NAVY)
    for k in range(5):   # 遠くへつながる点線
        x = (360 + k * 40) * S2; d.ellipse((x, 150 * S2, x + 14 * S2, 164 * S2), fill=(255, 138, 31, 255))
    if t >= p["ghost"]:   # 家の人の姿が、会社の机にうっすら重なる
        a_ = int(150 * min(1.0, (t - p["ghost"]) / 0.6))
        for cx_, al_ in ((190, 255), (710, a_)):      # 画面の前に座る人の後ろ姿（頭と肩を大きく。v1 の確認役：台に見えた）。会社のほうはうすく重なる
            d.ellipse(((cx_ - 34) * S2, 196 * S2, (cx_ + 34) * S2, 264 * S2), fill=(244, 160, 70, al_))
            d.rounded_rectangle(((cx_ - 80) * S2, 252 * S2, (cx_ + 80) * S2, 330 * S2), radius=40 * S2, fill=(244, 160, 70, al_))
    return im.resize((W_, H_), Image.LANCZOS)


def rewind_layer(t, t0):
    """12-01：時間を巻きもどす（白い渦が回って、まわりが暗くなる）"""
    u = (t - t0) / 1.6; a = math.sin(math.pi * min(1.0, max(0.0, u)))
    im = _layer(); d = ImageDraw.Draw(im); S2 = 2
    for k in range(9):
        r = (80 + k * 70) * S2; ang = -720 * u + k * 40
        d.arc((640 * S2 - r, 360 * S2 - r, 640 * S2 + r, 360 * S2 + r), ang, ang + 200, fill=(255, 255, 255, int(170 * a)), width=10 * S2)
    out = _down(im)
    base = Image.new("RGBA", (1280, 720), (10, 16, 40, int(110 * a))); base.alpha_composite(out)
    return base


def _layer():
    return Image.new("RGBA", (1280 * 2, 720 * 2), (0, 0, 0, 0))


def _down(im):
    return im.resize((1280, 720), Image.LANCZOS)


def ring_img(q, r, col, a):
    im = _layer(); d = ImageDraw.Draw(im); S2 = 2
    d.ellipse([(q[0] - r) * S2, (q[1] - r) * S2, (q[0] + r) * S2, (q[1] + r) * S2], outline=col + (int(255 * a),), width=7 * S2)
    return _down(im)


def arrow_img(p0, p1, col, both=False, a=1.0):
    S2 = 2; im = _layer(); d = ImageDraw.Draw(im)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); ca, sa = math.cos(ang), math.sin(ang)
    L_, Hw, lw = 30, 18, 9
    fill = col + (int(255 * a),)

    def head(tip, ca_, sa_):
        bs = ((tip[0] - L_ * ca_) * S2, (tip[1] - L_ * sa_) * S2)
        d.polygon([(tip[0] * S2, tip[1] * S2), (bs[0] - Hw * sa_ * S2, bs[1] + Hw * ca_ * S2), (bs[0] + Hw * sa_ * S2, bs[1] - Hw * ca_ * S2)], fill=fill)
    a0 = (p0[0] + (L_ * ca if both else 0), p0[1] + (L_ * sa if both else 0)); a1 = (p1[0] - L_ * ca, p1[1] - L_ * sa)
    d.line([(a0[0] * S2, a0[1] * S2), (a1[0] * S2, a1[1] * S2)], fill=fill, width=lw * S2)
    head(p1, ca, sa)
    if both: head(p0, -ca, -sa)
    return _down(im)


def sticker_sprite():
    key = ("sticker",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            cx, cy, r = W_ / 2, H_ / 2, 70 * ss
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 250, 246), outline=(200, 205, 210), width=3 * ss)
            d.ellipse([cx - 30 * ss, cy - 30 * ss, cx + 30 * ss, cy + 30 * ss], fill=(31, 184, 172))
            d.ellipse([cx - 12 * ss, cy - 12 * ss, cx + 12 * ss, cy + 12 * ss], fill=(16, 60, 70))
        _cache[key] = D.card(200, 200, draw=dr)[0]
    return _cache[key]


def coins_sprite():
    key = ("coins",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            for i in range(3):
                y = H_ / 2 + (30 - 22 * i) * ss
                d.ellipse([W_ / 2 - 80 * ss, y - 22 * ss, W_ / 2 + 80 * ss, y + 22 * ss], fill=(214, 218, 222), outline=(150, 156, 162), width=3 * ss)
            D.ctext(d, (W_ / 2, H_ / 2 + 84 * ss), "1円玉 3枚", D.font(40 * ss), NAVY)
        _cache[key] = D.card(260, 230, draw=dr)[0]
    return _cache[key]


def pile_sprite(t=None, t0=None):
    """06-03 の想像：横から見たエスカレーター。上の降り口で消えた段が、床の下に 1 枚ずつ落ちてたまっていく（v1 のコメント「この絵がわかりにくい」で描き替え）"""
    k = 1.0 if t is None else max(0.0, min(1.0, (t - t0) / 3.2))

    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: (x * ss, y * ss)
        GR, ST, NV = (150, 156, 166), (96, 104, 118), NAVY
        # 床（下の階・上の階）と坂
        d.line([S_(30, 330), S_(250, 330)], fill=GR, width=8 * ss)
        d.line([S_(250, 330), S_(560, 140)], fill=GR, width=8 * ss)
        d.line([S_(560, 140), S_(870, 140)], fill=GR, width=8 * ss)
        # 坂の段（のこぎりの形）
        for q in range(9):
            x0, y0 = 262 + q * 33, 323 - q * 20.2
            d.line([S_(x0, y0), S_(x0, y0 - 20), S_(x0 + 33, y0 - 20)], fill=ST, width=5 * ss)
        # 床の下（上の階の下）：点線の箱
        bx0, by0, bx1, by1 = 590, 160, 850, 400
        for xx in range(bx0, bx1, 22):
            d.line([S_(xx, by1), S_(xx + 12, by1)], fill=GR, width=4 * ss)
        for yy in range(by0, by1, 22):
            d.line([S_(bx0, yy), S_(bx0, yy + 12)], fill=GR, width=4 * ss)
            d.line([S_(bx1, yy), S_(bx1, yy + 12)], fill=GR, width=4 * ss)
        D.ctext(d, S_(520, 380), "床の下", D.font(32 * ss), GR)
        # たまっていく段（1 枚ずつ落ちる）
        u = k * 7.0; n = min(7, 1 + int(u))
        for i_ in range(n):
            fall = 1.0 if (i_ < n - 1 or k >= 1.0) else min(1.0, (u - (n - 1)) * 1.6 + 0.2)
            yb = by1 - 8 - i_ * 26; ytop = 150 + (yb - 150) * fall
            x0 = 640 + (i_ % 2) * 18
            d.rounded_rectangle([S_(x0, ytop - 22), S_(x0 + 150, ytop)], radius=5 * ss, fill=ST)
            for g in range(6):
                d.line([S_(x0 + 14 + g * 23, ytop - 18), S_(x0 + 14 + g * 23, ytop - 4)], fill=(150, 158, 172), width=3 * ss)
        # 消える所から下へ落ちる矢印
        d.line([S_(575, 128), S_(612, 128), S_(612, 210)], fill=(214, 72, 64), width=7 * ss)
        d.polygon([S_(598, 206), S_(626, 206), S_(612, 232)], fill=(214, 72, 64))
        D.ctext(d, S_(450, 40), "消えた段が、床の下にたまる？", D.font(46 * ss), NV)
    return D.card(900, 430, draw=dr)[0]


def hrloop_sprite(t, tA, tB, tC):
    """23-01〜23-04：手すりのしくみの図（9本目 v2 の点検：3D は段の断面のままで、「手すりはゴムの輪」「車ではさんで」の物が画面になかった）。
    手すりの輪（上を進み、端で回って床の下を戻る）。tA「ゴム」で輪が青緑に光る。tB「車」で、戻る所をはさむ 2 つの車がオレンジに光る。
    tC「すべって」で、車の所に「少しすべる」の印。手すりの白い印が輪にそって動き、車が回る"""
    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: (x * ss, y * ss)
        GR, NV = (70, 76, 86), NAVY
        D.ctext(d, S_(500, 40), "手すりのしくみ", D.font(40 * ss), NV)
        top = [(110, 270), (330, 270), (690, 115), (890, 115)]
        ret = [(x, y + 96) for x, y in reversed(top)]
        rr = 48
        arcR = [(890 + rr * math.sin(a), 115 + rr - rr * math.cos(a)) for a in [i * math.pi / 18 for i in range(19)]]
        arcL = [(110 - rr * math.sin(a), 366 - rr + rr * math.cos(a)) for a in [i * math.pi / 18 for i in range(19)]]
        loop = top + arcR + ret + arcL
        # 段（うすい灰色の坂。手すりがその上を進むのが分かるように）
        d.line([S_(x, y + 36) for x, y in top], fill=(205, 209, 215), width=26 * ss)
        D.ctext(d, S_(800, 175), "段", D.font(32 * ss), (150, 156, 166))
        on = t >= tA
        col = D.TEAL if on else GR
        if on: d.line([S_(x, y) for x, y in loop], fill=(170, 225, 215), width=30 * ss, joint="curve")
        d.line([S_(x, y) for x, y in loop], fill=col, width=16 * ss, joint="curve")
        # 白い印：輪にそって進む（上は右へ、床の下は左へ）
        acc = [0.0]
        for (a, b), (c, e_) in zip(loop, loop[1:]): acc.append(acc[-1] + math.hypot(c - a, e_ - b))
        L = acc[-1]
        for j in range(int(L // 70)):
            u = (j * 70 + 60.0 * t) % L
            i = max(0, min(len(acc) - 2, next(k for k in range(len(acc) - 1) if acc[k + 1] >= u)))
            (a, b), (c, e_) = loop[i], loop[i + 1]
            f = (u - acc[i]) / max(1e-6, acc[i + 1] - acc[i]); x, y = a + (c - a) * f, b + (e_ - b) * f
            d.ellipse([S_(x - 4, y - 4), S_(x + 4, y + 4)], fill=(235, 240, 244))
        # はさむ車（戻る坂のまん中）
        (xa, ya), (xb, yb) = ret[1], ret[2]
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        ln = math.hypot(xb - xa, yb - ya); nx, ny = -(yb - ya) / ln, (xb - xa) / ln
        onB = t >= tB
        for sg in (1, -1):
            cx, cy = mx + sg * nx * 36, my + sg * ny * 36
            fc = ORANGE if onB else (150, 156, 166)
            if onB: d.ellipse([S_(cx - 34, cy - 34), S_(cx + 34, cy + 34)], fill=(255, 214, 170))
            d.ellipse([S_(cx - 27, cy - 27), S_(cx + 27, cy + 27)], fill=fc, outline=NV, width=3 * ss)
            ang = sg * t * 3.0
            for q in range(3):
                a_ = ang + q * 2 * math.pi / 3
                d.line([S_(cx, cy), S_(cx + 22 * math.cos(a_), cy + 22 * math.sin(a_))], fill=NV, width=4 * ss)
        if on: D.ctext(d, S_(255, 215), "手すり（ゴムの輪）", D.font(34 * ss), D.TEAL_D)
        cl = (mx - nx * 36, my - ny * 36)          # 下の車
        if onB:
            d.line([S_(cl[0] + 30, cl[1] + 8), S_(700, 318)], fill=(214, 104, 0), width=3 * ss)
            D.ctext(d, S_(800, 318), "車ではさむ", D.font(34 * ss), (214, 104, 0))
        if t >= tC:
            ux, uy = (xb - xa) / ln, (yb - ya) / ln    # 戻る坂の向き
            bx, by = cl[0] + nx * -40, cl[1] + ny * -40
            d.line([S_(bx - ux * 40, by - uy * 40), S_(bx + ux * 30, by + uy * 30)], fill=RED, width=6 * ss)
            d.polygon([S_(bx + ux * 46, by + uy * 46), S_(bx + ux * 24 + nx * 12, by + uy * 24 + ny * 12), S_(bx + ux * 24 - nx * 12, by + uy * 24 - ny * 12)], fill=RED)
            d.line([S_(bx + 10, by + 10), S_(700, 372)], fill=RED, width=3 * ss)
            D.ctext(d, S_(800, 372), "少しすべる", D.font(34 * ss), RED)
    return D.card(1000, 420, draw=dr)[0]


LOC_PATH = [(292, 12), (318, 14), (330, 28), (316, 42), (282, 42), (104, 140), (72, 140), (60, 126), (70, 112), (96, 112)]   # 床の下の道（上の床の下 → 歯車 → 坂の下を戻る → 下の端 → 下の床の下）


def _loc_pt(u):
    acc = [0.0]
    for (a, b), (c, d) in zip(LOC_PATH, LOC_PATH[1:]): acc.append(acc[-1] + math.hypot(c - a, d - b))
    L = acc[-1] * max(0.0, min(1.0, u))
    for i in range(len(LOC_PATH) - 1):
        if acc[i + 1] >= L:
            f = (L - acc[i]) / max(1e-6, acc[i + 1] - acc[i]); (a, b), (c, d) = LOC_PATH[i], LOC_PATH[i + 1]
            return a + (c - a) * f, b + (d - b) * f
    return LOC_PATH[-1]


def locator_sprite(u, blink=1.0):
    """10〜13 章（床の下）：いま、エスカレーターのどこを見ているかの小さな地図（v2 のコメント 3:55「どの部分を見ているか分かりにくい」）。
    横から見たエスカレーター（下の床・坂・上の床）と、床の下の道（点線）に、赤い点と「いまここ」"""
    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: ((x + 10) * ss, (y + 50) * ss)
        GR, ST = (150, 156, 166), (96, 104, 118)
        d.line([S_(0, 100), S_(90, 100)], fill=GR, width=6 * ss)            # 下の床
        d.line([S_(90, 100), S_(270, 0)], fill=ST, width=10 * ss)           # 坂（段）
        d.line([S_(270, 0), S_(340, 0)], fill=GR, width=6 * ss)             # 上の床
        for (a, b), (c, e_) in zip(LOC_PATH, LOC_PATH[1:]):                  # 床の下の道（点線）
            L = math.hypot(c - a, e_ - b); n = max(1, int(L // 12))
            for q in range(n):
                f0, f1 = q / n, (q + 0.55) / n
                d.line([S_(a + (c - a) * f0, b + (e_ - b) * f0), S_(a + (c - a) * f1, b + (e_ - b) * f1)], fill=GR, width=4 * ss)
        x, y = _loc_pt(u)
        d.ellipse([S_(x - 15, y - 15), S_(x + 15, y + 15)], fill=(255, 205, 200))
        d.ellipse([S_(x - 9, y - 9), S_(x + 9, y + 9)], fill=RED)
        D.ctext(d, S_(110, -22), "いまここ", D.font(44 * ss), RED)
    return D.card(380, 230, draw=dr)[0]


def ruler_sprite(t=None, t_meas=None):
    """36-04〜36-06：止まるまでの長さを、まっすぐなものさしの図で（9本目 v2 ユーザー「テロップ重なるし、どこが何センチかわかんない」。
    3D の段の横に線を引くと、見る角度でずれて読めなかった）。10〜60 センチの間をぬり、36-05「測って」で矢印が 0 から約 50 センチまでのびる"""
    k = 0.0 if (t is None or t_meas is None) else max(0.0, min(1.0, (t - t_meas) / 1.6))

    def dr(d, W_, H_, ss, img):
        S_ = lambda x, y: (x * ss, y * ss)
        x0, cm = 175, 10.0                      # 0 センチの位置と、1 センチの長さ（65 センチまで）
        X = lambda c: x0 + c * cm
        GR, NV, YL, TL = (150, 156, 166), NAVY, YEL, D.TEAL_D
        D.ctext(d, S_(450, 36), "ボタンを押してから、止まるまで", D.font(40 * ss), NV)
        ya, yb = 132, 205                       # 矢印の高さ・ものさしの線の高さ
        d.rectangle([S_(X(10), yb - 36), S_(X(60), yb)], fill=YL)   # 決まりの間（10〜60 センチ）
        D.ctext(d, S_((X(10) + X(60)) / 2, yb - 18), "この間で止まる", D.font(28 * ss), NV)
        d.line([S_(X(0), yb), S_(X(65), yb)], fill=GR, width=6 * ss)
        for c in range(0, 66, 10):
            d.line([S_(X(c), yb), S_(X(c), yb + (18 if c in (0, 10, 60) else 10))], fill=GR, width=4 * ss)
        D.ctext(d, S_(X(0), yb + 42), "0", D.font(30 * ss), NV)
        D.ctext(d, S_(X(10), yb + 42), "10センチ", D.font(30 * ss), NV)
        D.ctext(d, S_(X(60), yb + 42), "60センチ", D.font(30 * ss), NV)
        D.ctext(d, S_(X(0) - 88, ya), "押した所", D.font(28 * ss), NV)
        d.line([S_(X(0), ya - 22), S_(X(0), yb)], fill=NV, width=4 * ss)
        if k > 0:
            xe = X(49 * k)
            d.line([S_(X(0), ya), S_(xe - 14, ya)], fill=TL, width=10 * ss)
            d.polygon([S_(xe, ya), S_(xe - 24, ya - 15), S_(xe - 24, ya + 15)], fill=TL)
            if k >= 1.0:
                d.line([S_(xe, ya), S_(xe, yb)], fill=TL, width=5 * ss)
                D.ctext(d, S_(xe, ya - 34), "止まった所（約50センチ）", D.font(28 * ss), TL)
    return D.card(900, 290, draw=dr)[0]


def hrarrows_sprite(t, t0):
    def dr(d, W_, H_, ss, img):
        k = min(1.0, (t - t0) / 0.8)
        for i, (lab, L, col) in enumerate((("手すり", 1.08, (40, 46, 54)), ("段", 1.0, D.TEAL_D))):
            y = (70 + 90 * i) * ss; x0 = 190 * ss; x1 = x0 + int(560 * ss * L * k)
            d.line([x0, y, x1 - 20 * ss, y], fill=col, width=12 * ss)
            d.polygon([(x1, y), (x1 - 34 * ss, y - 20 * ss), (x1 - 34 * ss, y + 20 * ss)], fill=col)
            D.ctext(d, (100 * ss, y), lab, D.font(42 * ss), col)
    return D.card(900, 230, draw=dr)[0]


def flow_sprite(t, items):
    shown = [nm for nm, ti in items if t >= ti]
    key = ("flow", tuple(shown))
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            # 字の幅を測って並べ、矢印はどれも同じ長さで字と字の間に（v2 のコメント 4:38「矢印が文字に重なってる」）。全部の字の場所を先に決めるので、出てきても字は動かない
            f_ = D.font(46 * ss); ws = [d.textlength(nm, font=f_) for nm, _ in items]
            gap, arr = 22 * ss, 100 * ss
            tot = sum(ws) + (len(items) - 1) * (arr + 2 * gap); x = (W_ - tot) / 2
            for i, (nm, _) in enumerate(items):
                cx = x + ws[i] / 2
                if nm in shown: D.ctext(d, (cx, H_ / 2), nm, f_, NAVY)
                if i + 1 < len(items) and items[i + 1][0] in shown:
                    xa = x + ws[i] + gap; xb = xa + arr
                    d.line([xa, H_ / 2, xb - 16 * ss, H_ / 2], fill=D.TEAL_D, width=8 * ss)
                    d.polygon([(xb, H_ / 2), (xb - 22 * ss, H_ / 2 - 14 * ss), (xb - 22 * ss, H_ / 2 + 14 * ss)], fill=D.TEAL_D)
                x += ws[i] + arr + 2 * gap
        _cache[key] = D.card(980, 120, draw=dr)[0]
    return _cache[key]


def dotloop_img(qa, qb, a):
    """2 つの歯車の中心を結ぶ、輪（かまぼこ形）の点線"""
    im = _layer(); d = ImageDraw.Draw(im); S2 = 2
    dx, dy = qb[0] - qa[0], qb[1] - qa[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy, ux
    r = max(40, 0.12 * L)
    pts = []
    for i in range(41): pts.append((qa[0] + dx * i / 40 + nx * r, qa[1] + dy * i / 40 + ny * r))
    for i in range(21):
        th = math.pi / 2 - math.pi * i / 20; pts.append((qb[0] + (ux * math.cos(th) + nx * math.sin(th)) * r * 1, qb[1] + (uy * math.cos(th) + ny * math.sin(th)) * r))
    for i in range(41): pts.append((qb[0] - dx * i / 40 - nx * r, qb[1] - dy * i / 40 - ny * r))
    for i in range(21):
        th = -math.pi / 2 - math.pi * i / 20; pts.append((qa[0] + (ux * math.cos(th) + nx * math.sin(th)) * r, qa[1] + (uy * math.cos(th) + ny * math.sin(th)) * r))
    for i in range(0, len(pts) - 1, 2):
        d.line([(pts[i][0] * S2, pts[i][1] * S2), (pts[i + 1][0] * S2, pts[i + 1][1] * S2)], fill=(255, 255, 255, int(235 * a)), width=8 * S2)
    return _down(im)


def draw(t, base, where, frame_of=None, fontdir=None):
    global EVENTS
    if fontdir and not D.FDIR[0]: D.FDIR[0] = fontdir
    if EVENTS is None: EVENTS = ev_list()
    for t0, t1, kind, p in EVENTS:
        if not (t0 <= t < t1): continue
        k, a = _pop(t, t0, t1)
        if kind == "tag":
            if "pos" in p: cx, cy = p["pos"]
            else:
                q = where(p["obj"], t)
                if q is None or not (-20 <= q[0] <= 1300 and -20 <= q[1] <= 740): continue   # 物が画面の外なら出さない（9本目 26-03：端に寄せた札が何もない所を指した）
                cx, cy = q[0] + p.get("dx", 0), min(max(70, q[1] + p.get("dy", -120)), SUB_TOP - 60)
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), p.get("fg"))
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            _paste(base, spr, cx + (off[0] + spr.width / 2), cy + (off[1] + spr.height / 2), k, a)
        elif kind == "bubble":
            q = p["pos"] if "pos" in p else where(p["obj"], t)
            # 16本目 v1：寄りの絵で頭が画面の上にはみ出すと、吹き出しを出していなかった（01-03 のセールの吹き出しが一度も出なかった）。
            #   頭が横にはみ出すときだけ出さず、上下は画面のふちに寄せて出す
            if q is None or not (-60 <= q[0] <= 1340): continue
            spr, off = bubble_sprite(p["icon"])
            cx = min(max(q[0], spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(q[1] - 40 - p.get("lift", 0) - spr.height / 2, spr.height / 2 + 10), SUB_TOP - spr.height / 2)      # lift：頭に重なる寄りの絵で上げる（16本目 4章の確認役）
            _paste(base, spr, cx, cy, k, a)
        elif kind == "title":
            base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(120 * a))))
            _paste(base, title_sprite(), 640, 290, k, a)
        elif kind == "ring":
            q = where(p["obj"], t)
            if q is None or not (0 <= q[0] <= 1280 and 0 <= q[1] <= 720): continue
            base.alpha_composite(ring_img((q[0] + p.get("dx", 0), q[1] + p.get("dy", 0)), p.get("r", 40) * k, p.get("col", WHITE), a))
        elif kind == "arrow2":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            base.alpha_composite(arrow_img((qa[0], qa[1] + p["dy"]), (qb[0], qb[1] + p["dy"]), p.get("col", NAVY), a=a))
        elif kind == "dbl":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            if math.hypot(qb[0] - qa[0], qb[1] - qa[1]) < 30: continue
            base.alpha_composite(arrow_img(qa, qb, YEL, both=True, a=a))
        elif kind == "seg":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            im = _layer(); d = ImageDraw.Draw(im)
            d.line([(qa[0] * 2, qa[1] * 2), (qb[0] * 2, qb[1] * 2)], fill=YEL + (int(255 * a),), width=12)
            for q in (qa, qb): d.ellipse([(q[0] - 9) * 2, (q[1] - 9) * 2, (q[0] + 9) * 2, (q[1] + 9) * 2], fill=YEL + (int(255 * a),))
            base.alpha_composite(_down(im))
        elif kind == "vline":
            q = where(p["obj"], t)
            if q is None or not (0 <= q[0] <= 1280): continue
            im = _layer(); d = ImageDraw.Draw(im)
            d.line([(q[0] * 2, (q[1] - 90) * 2), (q[0] * 2, (q[1] + 10) * 2)], fill=p.get("col", WHITE) + (int(255 * a),), width=10)
            base.alpha_composite(_down(im))
            if p.get("text"):
                spr, off = tag_sprite(p["text"], 40, p.get("bg", YEL), fg=p.get("fg"))
                if p.get("right"):   # right：線の右に札（上は 10・60 センチの札、下は字幕と重なる。9本目 v2）
                    _paste(base, spr, q[0] + spr.size[0] // 2 + 24, q[1] - 45, k, a)
                else:
                    _paste(base, spr, q[0], max(60, q[1] - 130), k, a)
        elif kind == "tint":      # 想像の場面：少し青く暗く（本当の試しではないと分かるように）
            base.alpha_composite(Image.new("RGBA", base.size, (40, 60, 130, int(115 * a))))      # v1 の確認役：想像か本当か分かりにくい → 濃く
            spr, off = tag_sprite("もしも…", 44, WHITE)
            _paste(base, spr, 150, 70, 1.0, a)
        elif kind == "locator":
            ks = p["keys"]; u = ks[0][1]
            for (ta, ua), (tb, ub) in zip(ks, ks[1:]):
                if ta <= t <= tb: u = ua + (ub - ua) * (t - ta) / max(1e-6, tb - ta); break
                if t > tb: u = ub
            _paste(base, locator_sprite(round(u, 3)), 1080, 122, k, a)
        elif kind == "hrloop":
            _paste(base, hrloop_sprite(t, p["tA"], p["tB"], p["tC"]), 640, 300, k, a)
        elif kind == "ruler":
            _paste(base, ruler_sprite(t, p["t_meas"]), p["pos"][0], p["pos"][1], k, a)
        elif kind == "pile":
            _paste(base, pile_sprite(t, t0), p["pos"][0], p["pos"][1], k, a)
        elif kind == "sticker":
            _paste(base, sticker_sprite(), p["pos"][0], p["pos"][1], k, a)
        elif kind == "coins":
            _paste(base, coins_sprite(), p["pos"][0], p["pos"][1], k, a)
        elif kind == "hrarrows":
            _paste(base, hrarrows_sprite(t, t0), 640, 150, k, a)
        elif kind == "flow":
            _paste(base, flow_sprite(t, p["items"]), 640, 95, k, a)
        elif kind == "dotloop":
            qa, qb = where(p["a"], t), where(p["b"], t)
            if qa is None or qb is None: continue
            base.alpha_composite(dotloop_img(qa, qb, a))
        elif kind == "mailcard":
            _paste(base, mailcard_sprite(), 640, 200, k, a)
        elif kind == "form":
            _paste(base, form_sprite(t, p), 420, 140, k, a)
        elif kind == "pathfig":
            _paste(base, pathfig_sprite(t, p), 640, 160, k, a)
        elif kind == "headlines":
            _paste(base, headlines_sprite(t, t0), 640, 270, 1.0, a)
        elif kind == "qmark":
            if "pos" in p: cx, cy = p["pos"]
            else:
                q = where(p["obj"], t)
                if q is None: continue
                cx, cy = q[0] + p.get("dx", 0), max(80, q[1] + p.get("dy", -100))
            _paste(base, qmark_sprite(p.get("size", 120)), cx, cy, k, a)
        elif kind == "fig92":
            base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(90 * a))))
            sm = p.get("small")
            if sm and sm[0] <= t < sm[1]: _paste(base, fig92_sprite(t, p), 640, 285, 0.0001 + 0.0, 0.0)
            else: _paste(base, fig92_sprite(t, p), 640, 285, k, a)
        elif kind == "remote":
            _paste(base, remote_sprite(t, t0, p), 640, 290, k, a)
        elif kind == "rewind":
            base.alpha_composite(rewind_layer(t, t0))
        elif kind.startswith("c2_"):
            import overlays2 as OV2
            OV2.draw2(kind, t, t0, p, base, where, _paste, k, a)
        elif kind.startswith("c3_"):
            import overlays3 as OV3
            OV3.draw3(kind, t, t0, p, base, where, _paste, k, a)
        elif kind.startswith("c4_"):
            import overlays4 as OV4
            OV4.draw4(kind, t, t0, p, base, where, _paste, k, a)
        elif kind.startswith("c5_"):
            import overlays5 as OV5
            OV5.draw5(kind, t, t0, p, base, where, _paste, k, a)
        elif kind.startswith("c6_"):
            import overlays6 as OV6
            OV6.draw6(kind, t, t0, p, base, where, _paste, k, a)
        elif kind.startswith("c7_"):
            import overlays7 as OV7
            OV7.draw7(kind, t, t0, p, base, where, _paste, k, a)
        elif kind.startswith("c8_"):
            import overlays8 as OV8
            OV8.draw8(kind, t, t0, p, base, where, _paste, k, a, frame_of=frame_of)
        elif kind == "pip_clip" and frame_of:
            im = frame_of(p["clip"], p["src_t"] + (0 if p.get("hold") else (t - t0)))
            if im is None: continue
            im = im.convert("RGB").resize((544, 306), Image.LANCZOS)      # v1 の確認役：小さくて中身が分からない（400×225 → 544×306）
            fr = Image.new("RGBA", (556, 318), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            _paste(base, fr, 30 + 278, 25 + 159, k, a)
    return base
