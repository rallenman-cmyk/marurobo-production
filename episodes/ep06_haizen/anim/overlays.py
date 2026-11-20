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
s, e = T.s, T.e
# 札の時刻は、声の本当の切れ目に寄せる（6本目 v8 7:33「矢印が表示されるの早い」・5:52「テーブルのはしが早い」）。
#   T.w は字の数で言葉の位置を見積もるので、文の中に長い間があると 1 秒ほどずれる。言葉が「、。」のすぐ後なら、
#   その文の声の切れ目（0.25 秒以上の無音のあと、言葉が始まる時刻）のいちばん近い所（2.5 秒以内）を使う。3D（scenes.py）は T.w のまま
_GAPS = {}
W_SNAPS = []


def _gaps(i):
    """文の声の切れ目：[(言葉が始まる時刻, 無音の長さ)]"""
    if i in _GAPS: return _GAPS[i]
    g = []
    try:
        import wave, numpy as np
        L = [l for _, l in T.L.items() if l["id"] == i][0]
        vd = os.environ.get("MARU_VOICE") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "voice", "achernar")
        with wave.open(os.path.join(vd, "line_%03d.wav" % L["no"])) as wv_:
            sr = wv_.getframerate(); x = np.frombuffer(wv_.readframes(wv_.getnframes()), np.int16).astype(np.float32) / 32768
        h = int(sr * 0.02); on = np.abs(x[:len(x) // h * h]).reshape(-1, h).max(1) > 0.02; k = 0
        while k < len(on):
            if not on[k]:
                j = k
                while j < len(on) and not on[j]: j += 1
                if (j - k) * 0.02 >= 0.25 and k > 0 and j < len(on): g.append((L["start"] + j * 0.02 - 0.04, (j - k) * 0.02))
                k = j
            else: k += 1
    except Exception: pass
    _GAPS[i] = g; return g


def w(i, word, end=False):
    t0 = T.w(i, word, end)
    txt = T.TEXT[i]; k = txt.index(word) + (len(word) if end else 0)
    if k == 0 or txt[k - 1] not in "、。？！…": return t0
    g = _gaps(i)
    if not g: return t0
    body = txt.rstrip("、。？！…")
    ends = [n for n, ch in enumerate(body) if ch in "。？！" and (n + 1 >= len(body) or body[n + 1] not in "、。？！…")]
    commas = [n for n, ch in enumerate(body) if ch in "、…" and (n + 1 >= len(body) or body[n + 1] not in "、。？！…")]
    t1 = None
    long_ = [a for a, d in g if d >= 0.4]
    if txt[k - 1] in "。？！" and len(ends) == len(long_):                 # 文の終わりの後：長い間を何番目かで
        nth = sum(1 for n in ends if n < k); t1 = long_[nth - 1] if nth else None
    elif len(ends) + len(commas) == len(g):                                 # 区切り全部と切れ目の数が同じ：何番目かで
        nth = sum(1 for n in ends + commas if n < k); t1 = g[nth - 1][0] if nth else None
        if t1 is not None and abs(t1 - t0) > 0.8: t1 = None                 # 読点の間は短くて数えそこねることがある（29-03）→ 大きくは動かさない
    if t1 is None:                                                          # 合わないとき：見積もりから 0.6 秒以内の切れ目へ少しだけ
        c = min((a for a, d in g), key=lambda a: abs(a - t0))
        if abs(c - t0) <= 0.6: t1 = c
    if t1 is None or abs(t1 - t0) > 2.5: return t0
    if abs(t1 - t0) > 0.15: W_SNAPS.append((i, word, round(t0, 2), round(t1, 2)))
    return t1

TEAL = (33, 193, 179); YEL = (255, 210, 74); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48); ORANGE = (255, 154, 60); PINK = (255, 79, 160)
SUB_TOP = 560


def ev_list():
    E = []
    add = lambda *a: E.append(a)
    # 03：にらめっこ（どいていいのか分からない）
    add(w("03-02", "どうして") - 0.2, e("03-02") + 0.3, "bubble", dict(obj="maru", icon="?", side=-1))
    # 04：問い → 題名（2 秒）
    add(w("04-03", "どうして") - 0.2, e("04-04") + 0.2, "bubble", dict(obj="maru", icon="?", side=-1))
    add(e("04-05") + 0.3, s("05-01") - 0.3, "title", {})
    # 06：体の名前（言う瞬間に）
    add(w("06-01", "顔の画面"), w("06-01", "トレー"), "tag", dict(text="顔の画面", obj="head", dy=-110))
    add(w("06-01", "トレー"), e("06-01") + 0.2, "tag", dict(text="トレー", obj="tray", dy=-60))
    add(w("06-02", "カメラ"), w("06-02", "足もと") - 0.1, "tag", dict(text="カメラ", obj="lens", dy=-90))
    add(w("06-02", "小さな窓"), e("06-02") + 0.4, "tag", dict(text="小さな窓", obj="window", dy=60))
    # 07：台数
    add(w("07-02", "2022年"), e("07-02") + 0.4, "tag", dict(text="2022年の1年間", pos=(640, 100), size=48))
    add(w("07-02", "約3,000台"), e("07-02") + 0.6, "tag", dict(text="約3,000台", pos=(640, 190), size=64, bg=YEL))
    # 08：席の番号
    add(w("08-03", "12番"), s("08-04") + 0.4, "tag", dict(text="12番", obj="head", dy=-120, size=60, bg=YEL))   # v2：走り出したら消す（v1 2:16）
    # 09〜10：席の点・道・自分はどこ？
    add(w("09-03", "白い丸") + 0.3, e("09-04") + 0.3, "tag", dict(text="席の点", pos=(1080, 90)))
    add(w("09-04", "ここで"), s("10-03"), "tag", dict(text="12番", obj="seat12", dy=-70, size=56, bg=YEL))
    add(w("10-05", "自分が"), e("10-05") + 0.3, "bubble", dict(obj="senpai", icon="?", side=1, gap=30))
    # 11：天井の目印
    add(w("11-02", "目印"), e("11-04") + 0.3, "tag", dict(text="目印のシール", pos=(640, 90), leaders=["mark0", "mark1", "mark2"]))   # v4：札から目印へ線を引き、丸で囲む（3:14「どれかわかんない」）
    for k in range(3): add(w("11-02", "目印") + 0.1 * k, e("11-04") + 0.3, "ring2d", dict(obj="mark%d" % k, r=26))
    # 12：地図と、いま見えている形
    # v3：12-02〜12-02c は 2D の図（左＝先輩に見える点の形、右＝お店の地図。ゆっくり動かして × × ✓。v2 3:31「分かりにくい・動きも早い」）
    add(s("12-02") - 0.2, e("12-02c") + 0.6, "shapematch", {})
    # 13：光の物差し
    add(w("13-02", "光の物差し"), e("13-03") + 0.3, "tag", dict(text="光の物差し", pos=(1060, 90)))
    # 14〜16：点の色の名前（14 から最後まで同じ）
    add(w("14-03", "青緑"), w("16-04", "冒頭で"), "legend", dict(items=[(TEAL, "止まった物"), (ORANGE, "動く人の足")], t1=w("14-04", "橙")))
    add(w("16-01", "遅く"), s("16-02") - 0.05, "tag", dict(text="遅くなる", pos=(1060, 90)))
    add(w("16-02", "ぴたっ"), s("16-03") - 0.05, "tag", dict(text="止まる", pos=(1060, 90), bg=YEL))
    add(w("16-03", "よけて"), e("16-03") + 0.5, "tag", dict(text="よける", pos=(1060, 90)))
    add(w("16-04", "冒頭で"), e("16-04") + 0.2, "pip_clip", dict(clip="S03a", src_t=w("03-01", "ぴたっ") + 0.3, hold=True))
    # 17：光の板
    add(w("17-02", "この高さ"), e("17-03") + 0.3, "tag", dict(text="回る光の高さ", pos=(1060, 90)))
    add(w("17-03", "低い物") - 0.2, e("17-03") + 0.2, "bubble", dict(obj="senpai", icon="?", side=1, gap=10))
    # 18：先輩の目の絵（小窓）。まるロボの所に点がない
    add(w("18-03", "先輩の目"), e("18-03") + 0.6, "pip_clip", dict(clip="S18p", src_t=w("18-03", "先輩の目"), big=True))   # v5 点検：文の頭から流すと 4 秒おくれて、黄色い輪が出る前に小窓が終わった
    # 19：出っぱったテーブルのはし
    add(w("19-01", "テーブルのはし"), e("19-02") + 0.3, "ring2d", dict(obj="edgept", r=40))
    add(w("19-04", "どこで") - 0.2, e("19-04") + 0.2, "bubble", dict(obj="maru", icon="?", side=1))
    # 20：前のカメラ 3 つ。v2：「このカメラ」で、おなかの前の 2 つに丸と札（どれのことか分かるように。v1 5:51）。「3つ」で頭の下にも丸
    add(w("20-01", "このカメラ"), e("20-02") + 0.3, "ring2d", dict(obj="lens", r=30))
    add(w("20-01", "このカメラ"), e("20-02") + 0.3, "ring2d", dict(obj="lens1", r=30))
    add(w("20-01", "このカメラ"), w("20-02", "3つ"), "tag", dict(text="前のカメラ", obj="lens", dx=40, dy=-90, leaders=["lens2"]))   # v4：上のカメラにも線（6:10「上についているのも対象」）
    add(w("20-01", "このカメラ"), w("20-02", "3つ"), "ring2d", dict(obj="lens2", r=30))
    add(w("20-02", "3つ"), e("20-02") + 0.3, "ring2d", dict(obj="lens2", r=30))
    add(w("20-02", "3つ"), e("20-03") + 0.3, "tag", dict(text="前のカメラ 3つ", pos=(1040, 90), size=52))
    add(w("20-04", "回る光"), e("20-05") + 0.2, "legend", dict(items=[(TEAL, "回る光：遠くまで"), (PINK, "前のカメラ：目の前")], t1=w("20-04", "前のカメラ")))
    # 21：子ども
    add(s("21-01") + 0.3, s("21-01") + 1.6, "bubble", dict(obj="maru", icon="!", side=-1))
    # 22：人が運ぶと……（小窓の絵）・速さの変え方（絵）
    add(w("22-01b", "人が"), e("22-01b") + 0.3, "pip_clip", dict(clip="S22p", src_t=w("22-01b", "人が"), big=True))   # v2：3D の小窓に
    add(w("22-02", "なめらかに"), e("22-03") + 0.3, "speed", dict(t1=e("22-02")))
    # 24：通路のはば
    # v8 7:33「矢印が表示されるの早い」：場面の頭ではなく「通路のはば」と言う瞬間に。「70cm」はそこからの字の数で
    add(w("24-01", "通路のはば"), e("24-03") + 0.3, "darrow", dict(a="gapL", b="gapR", text="70cm", track_clip="S24a",
                                                           t_text=w("24-01", "通路のはば") + T.w("24-01", "70cm") - T.w("24-01", "通路のはば")))
    # 23・25：困り顔・ほっと
    add(s("23-03") + 0.3, e("23-03") + 0.6, "bubble", dict(obj="maru", icon="?", side=-1, track_clip="S23b"))
    # 28：怒った
    add(w("28-03", "怒った") + 0.1, e("28-03") + 0.6, "bubble", dict(obj="maru", icon="!", side=1, track_clip="S28a"))
    # 29：まとめ。v2：問いと答えが分かるように、問いの札（黄色）の下に答えの札を並べる（v1 8:43・9:00「何が問いで何が答えか」「まとめ方分かりにくい」）
    # v3：1 枚の白いカードに、問い（黄色）と答え（青緑のふち）を 2 段で。うしろの絵は暗く（v2 8:52「画面がぐちゃぐちゃしている」）
    add(w("29-01", "一つ目") - 0.2, e("29-07") + 0.8, "sumcard", dict(rows=[
        ("問い①　どの席か分かる？", w("29-01", "一つ目"), [("席の点", w("29-02", "席ごとの")), ("天井の目印", w("29-03", "天井の目印")), ("まわりの形", w("29-03", "まわりの形"))]),
        ("問い②　なぜぶつからない？", w("29-04", "二つ目"), [("回る光", w("29-05", "回る光")), ("前のカメラ", w("29-05", "前のカメラ")), ("近づくと止まる", w("29-06", "止まって")), ("顔", w("29-07", "顔が"))])]))
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
    for t0, t1, kind, p in sorted(EVENTS, key=lambda x: x[2] == "tag"):   # 札はいちばん前に（v5 3:14「テロップを最前面に」）
        if not (t0 <= t < t1): continue
        k, a = _pop(t, t0, t1)
        if kind == "tag":
            if "pos" in p: cx, cy = p["pos"]; tail = None
            else:
                q = where(p["obj"], t, p.get("track_clip"))
                if q is None: continue
                cx, cy = q[0] + p.get("dx", 0), max(70, q[1] + p.get("dy", -120)); cy = min(cy, SUB_TOP - 60)
                tail = (0, 46) if q[1] - cy > 60 else None      # v3：しっぽは決まった三角（物との距離で大きさが変わらない。5本目 v2「バンパー」）
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), tail=tail)
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            for ob in p.get("leaders", []):   # 札から物へ細い線（しっぽを 2 つ目・3 つ目の物にも。v4）
                q2 = where(ob, t, p.get("track_clip"))
                if q2 is None: continue
                y0 = cy + off[1] + spr.height / 2 + (spr.height / 2 - 6 if q2[1] > cy else -(spr.height / 2 - 6))
                L_ = math.dist((cx, y0), q2)
                if L_ < 40: continue
                ux, uy = (q2[0] - cx) / L_, (q2[1] - y0) / L_
                ln = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(ln).line([cx, y0, q2[0] - ux * 30, q2[1] - uy * 30], fill=WHITE + (int(235 * a),), width=5)
                base.alpha_composite(ln)
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
            spr, off = tag_sprite(p["text"], 46, WHITE)
            widths = [tag_sprite(x[3]["text"], 46)[0].width for x in same]; tot = sum(widths) + 24 * (len(same) - 1)
            x_ = 640 - tot / 2 + sum(widths[:i]) + 24 * i + spr.width / 2
            _paste(base, spr, x_, (150, 330, 420)[row], k, a)
        elif kind == "shapematch":
            shapematch_draw(base, t, t0, t1)
        elif kind == "sumcard":
            sumcard_draw(base, t, t0, t1, p)
        elif kind == "spill":      # 人がおぼんで運んで、急に止まると……スープがはねる（字なしの絵）
            _paste(base, spill_sprite(min(1.0, (t - t0) / 1.6)), 250, 170, k, a)
        elif kind == "speed":      # 速さの変え方：ぐっと（点線）と、なめらか（青緑）
            _paste(base, speed_sprite(min(1.0, (t - t0) / 1.4)), 960, 280, k, a)
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
    """止まるときの速さ（v2：何のグラフか分かるように、題・軸・線の名前を入れた。v1 6:51「何のグラフかわかるように、大事なところ」）
       横＝時間・縦＝速さ。灰色の点線＝ぐっと止まる、青緑＝先輩（なめらかに止まる）"""
    st = round(min(1.0, k) * 10) / 10
    key = ("speed", st)
    if key in _cache: return _cache[key]
    def dr(d, W_, H_, ss, img):
        f_t = D.font(44 * ss); f_a = D.font(36 * ss); f_l = D.font(36 * ss)
        D.ctext(d, (W_ / 2, 40 * ss), "止まるときの速さ", f_t, NAVY)
        # 線の名前（題の下に 1 列で）
        ly = 100 * ss; gx = 60 * ss
        for i in range(0, 4): d.line([gx + i * 16 * ss, ly, gx + i * 16 * ss + 9 * ss, ly], fill=(150, 160, 170), width=6 * ss)
        d.text((gx + 70 * ss, ly), "ぐっと止まる", font=f_l, fill=(110, 120, 130), anchor="lm")
        ly2 = ly + 48 * ss
        d.line([gx, ly2, gx + 56 * ss, ly2], fill=TEAL, width=9 * ss)
        d.text((gx + 70 * ss, ly2), "先輩（なめらか）", font=f_l, fill=(20, 150, 138), anchor="lm")
        x0, y0, x1, y1 = 120 * ss, H_ - 80 * ss, W_ - 40 * ss, 190 * ss
        d.line([x0, y0, x1, y0], fill=NAVY, width=4 * ss); d.line([x0, y0, x0, y1], fill=NAVY, width=4 * ss)
        d.polygon([(x1 + 4 * ss, y0), (x1 - 14 * ss, y0 - 9 * ss), (x1 - 14 * ss, y0 + 9 * ss)], fill=NAVY)
        d.polygon([(x0, y1 - 4 * ss), (x0 - 9 * ss, y1 + 14 * ss), (x0 + 9 * ss, y1 + 14 * ss)], fill=NAVY)
        D.ctext(d, (x0 - 55 * ss, (y0 + y1) / 2), "速さ", f_a, NAVY)
        D.ctext(d, (x1 - 50 * ss, y0 + 38 * ss), "時間", f_a, NAVY)
        top = y1 + 30 * ss; mid = x0 + (x1 - x0) * 0.32
        # ぐっと（灰色の点線）：高いまま → いきなり 0（なめらかな線より少し上に描いて、重ならないように）
        topg = top - 12 * ss
        for i in range(0, 20, 2):
            xa = x0 + (mid - x0) * i / 20; xb = x0 + (mid - x0) * (i + 1) / 20
            d.line([xa, topg, xb, topg], fill=(150, 160, 170), width=6 * ss)
        for i in range(0, 10, 2):
            ya = topg + (y0 - topg) * i / 10; yb = topg + (y0 - topg) * (i + 1) / 10
            d.line([mid, ya, mid, yb], fill=(150, 160, 170), width=6 * ss)
        # なめらか（青緑）：少しずつ 0 へ
        pts = []
        n = int(40 * st) + 1
        for i in range(n):
            u = i / 40; x = x0 + (x1 - x0) * u
            if u < 0.3: v = 1.0
            else:
                q = min(1.0, (u - 0.3) / 0.6); v = 1 - q * q * (3 - 2 * q)
            pts.append((x, top + (y0 - top) * (1 - v)))
        if len(pts) > 1: d.line(pts, fill=TEAL, width=9 * ss, joint="curve")
    spr, off = D.card(480, 420, draw=dr)
    _cache[key] = spr
    return spr


def sepia(im):
    g = im.convert("L")
    return Image.merge("RGB", (g.point(lambda v: min(255, int(v * 1.07 + 18))), g.point(lambda v: int(v * 0.92 + 8)), g.point(lambda v: int(v * 0.74))))


# ======================================================================== 12：点の形を地図に重ねる（v3。2D の図）
import plan as _plan
_SM = {}


def _sm_data():
    if _SM: return _SM
    S = _plan.segments(); pos = (0.0, 0.35)
    pts = []
    for k in range(0, 360, 2):
        h = _plan.ray(pos[0], pos[1], math.radians(k), S, 2.2)
        if h: pts.append((h[1][0] - pos[0], h[1][1] - pos[1]))
    _SM.update(S=S, pos=pos, pts=pts)
    return _SM


SM_SC = 64.0                      # 1 m ＝ 64 px
SM_MAP_C = (842, 318)             # 地図のまん中（お店の x 0・y 0.1）
SM_LEFT_C = (300, 318)            # 左の枠のまん中


def _m2p(x, y):
    return (SM_MAP_C[0] + x * SM_SC, SM_MAP_C[1] - (y - 0.1) * SM_SC)


def _sm_base():
    """変わらない所：白いカード・2 つの枠・題・地図"""
    if "base" in _SM: return _SM["base"]
    _sm_data()
    ss = 2; im = Image.new("RGBA", (1280 * ss, 720 * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([104 * ss, 40 * ss, 1176 * ss, 552 * ss], 30 * ss, fill=(0, 0, 0, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14 * ss)))
    d.rounded_rectangle([100 * ss, 34 * ss, 1180 * ss, 548 * ss], 30 * ss, fill=(255, 255, 255, 255))
    f = D.font(40 * ss)
    D.ctext(d, (SM_LEFT_C[0] * ss, 78 * ss), "先輩に見える点の形", f, NAVY)
    D.ctext(d, (SM_MAP_C[0] * ss, 78 * ss), "お店の地図", f, NAVY)
    d.rounded_rectangle([130 * ss, 112 * ss, 470 * ss, 528 * ss], 20 * ss, fill=(236, 243, 247, 255))
    d.rounded_rectangle([590 * ss, 104 * ss, 1094 * ss, 536 * ss], 16 * ss, fill=(246, 241, 232, 255))
    P = lambda x, y: tuple(v * ss for v in _m2p(x, y))
    # いす・テーブル（上から見た形）
    for n, (tx, ty) in _plan.TABLE.items():
        for side in ("in", "out"):
            cx, cy = _plan.chair_pos(n, side)
            a, b = P(cx - 0.2, cy + 0.2), P(cx + 0.2, cy - 0.2)
            d.rounded_rectangle([a[0], a[1], b[0], b[1]], 4 * ss, fill=(228, 214, 196, 255), outline=(190, 170, 150, 255), width=2 * ss)
        h = _plan.TSIZE / 2; a, b = P(tx - h, ty + h), P(tx + h, ty - h)
        d.rounded_rectangle([a[0], a[1], b[0], b[1]], 5 * ss, fill=(214, 186, 150, 255), outline=(170, 135, 100, 255), width=2 * ss)
    # 壁
    x0, y0, x1, y1 = _plan.ROOM
    for (ax, ay), (bx, by) in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x0, y0), (x0, y1)), ((x0, y1), (_plan.KITCHEN[0], y1)), ((_plan.KITCHEN[1], y1), (x1, y1))]:
        d.line([P(ax, ay), P(bx, by)], fill=NAVY + (255,), width=6 * ss)
    _SM["base"] = im.resize((1280, 720), Image.LANCZOS)
    return _SM["base"]


def _ease(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def shapematch_draw(base, t, t0, t1):
    sm = _sm_data(); pts = sm["pts"]
    a = min(1.0, (t - t0) / 0.35, max(0.0, (t1 - t) / 0.4))
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    lay.alpha_composite(_sm_base())
    # 形の置き場所（スクリーン座標）：左の枠 → ちがう所 1 → ちがう所 2 → ぴったり
    tgt = sm["pos"]
    T1, T2 = (-1.45, 0.55), (1.45, -1.05)   # ちがう所：テーブルの上（点が机や壁とずれて、合わないのがすぐ分かる）
    m1a, m1b = w("12-02a", "動かして"), w("12-02b", "ここは") + 0.05
    x1 = w("12-02b", "合わない")
    m2a, m2b = w("12-02b", "ここも") - 0.15, w("12-02b", "も……合") - 0.05
    x2 = w("12-02b", "も……合") + 0.15
    m3a, m3b = s("12-02c") - 0.7, w("12-02c", "ぴったり") + 0.35
    ok = w("12-02c", "ここが")
    L = SM_LEFT_C; Q1, Q2, Q3 = _m2p(*T1), _m2p(*T2), _m2p(*tgt)
    def lerp(p, q, u): u = _ease(u); return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)
    if t < m1a: c = L
    elif t < m1b: c = lerp(L, Q1, (t - m1a) / (m1b - m1a))
    elif t < m2a: c = Q1
    elif t < m2b: c = lerp(Q1, Q2, (t - m2a) / (m2b - m2a))
    elif t < m3a: c = Q2
    elif t < m3b: c = lerp(Q2, Q3, (t - m3a) / (m3b - m3a))
    else: c = Q3
    bad = (x1 <= t < m2a) or (x2 <= t < m3a); good = t >= m3b
    col = (226, 58, 48) if bad else ((240, 170, 0) if good else TEAL)
    # 点：はじめはぐるりと順に出る（光が回って測る感じ）
    n_show = len(pts) if t > s("12-02") + 2.2 else int(len(pts) * max(0.0, (t - s("12-02") - 0.3) / 1.9))
    ss = 2; L2 = Image.new("RGBA", (1280 * ss, 720 * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(L2)
    for (dx, dy) in pts[:n_show]:
        px, py = (c[0] + dx * SM_SC) * ss, (c[1] - dy * SM_SC) * ss
        d.ellipse([px - 5.5 * ss, py - 5.5 * ss, px + 5.5 * ss, py + 5.5 * ss], fill=col + (255,))
    if t >= m1a:   # 左の枠には、もとの形をうすく残す（見比べられるように）
        for (dx, dy) in pts:
            px, py = (L[0] + dx * SM_SC) * ss, (L[1] - dy * SM_SC) * ss
            d.ellipse([px - 5.5 * ss, py - 5.5 * ss, px + 5.5 * ss, py + 5.5 * ss], fill=(160, 222, 215, 255))
    # 先輩の印（白い丸に目 2 つ）
    cx, cy = c[0] * ss, c[1] * ss; r = 15 * ss
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255), outline=NAVY + (255,), width=4 * ss)
    for ex in (-5, 5): d.ellipse([cx + (ex - 2.5) * ss, cy - 4.5 * ss, cx + (ex + 2.5) * ss, cy + 0.5 * ss], fill=NAVY + (255,))
    if good:
        rr = 28 * ss; d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(240, 170, 0, 255), width=6 * ss)
    lay.alpha_composite(L2.resize((1280, 720), Image.LANCZOS))
    # × と ✓（字ではなく線で描く）
    def mark(kind, at, p0):
        if t < at: return
        k, _ = _pop(t, at, at + 99)
        m = Image.new("RGBA", (200, 200), (0, 0, 0, 0)); md = ImageDraw.Draw(m)
        md.ellipse([20, 20, 180, 180], fill=(255, 255, 255, 235))
        if kind == "x":
            md.line([60, 60, 140, 140], fill=(226, 58, 48, 255), width=22); md.line([140, 60, 60, 140], fill=(226, 58, 48, 255), width=22)
        else:
            md.line([52, 104, 88, 140, 150, 64], fill=(30, 170, 90, 255), width=24, joint="curve")
        m = m.resize((84, 84), Image.LANCZOS)
        _paste(lay, m, p0[0] + 46, p0[1] - 46, k)
    if x1 <= t < m2a: mark("x", x1, Q1)
    if x2 <= t < m3a: mark("x", x2, Q2)
    if t >= m3b: mark("ok", m3b, (Q3[0] + 40, Q3[1] + 46))   # ✓ は右下（上の「ここ！」と重ねない）
    if t >= ok:
        k, _ = _pop(t, ok, ok + 99)
        spr, off = tag_sprite("ここ！", 48, YEL, tail=(0, 46))
        _paste(lay, spr, Q3[0] + off[0] + spr.width / 2, Q3[1] - 90 + off[1] + spr.height / 2, k)
    if a < 1.0:
        al = lay.getchannel("A").point(lambda v: int(v * a)); lay.putalpha(al)
    base.alpha_composite(lay)


# ======================================================================== 29：まとめのカード（v3）
def chip_sprite(text, size=40):
    key = ("chip", text, size)
    if key not in _cache:
        f = D.font(size * 2); tw = int(D.font(size * 2).getlength(text)); ss = 2
        W_, H_ = tw + 56 * ss, int(size * 1.7) * ss
        im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([3 * ss, 3 * ss, W_ - 3 * ss, H_ - 3 * ss], H_ // 2, fill=(232, 248, 246, 255), outline=TEAL + (255,), width=4 * ss)
        D.ctext(d, (W_ / 2, H_ / 2), text, f, NAVY)
        _cache[key] = im.resize((W_ // ss, H_ // ss), Image.LANCZOS)
    return _cache[key]


def sumcard_draw(base, t, t0, t1, p):
    a = min(1.0, (t - t0) / 0.35, max(0.0, (t1 - t) / 0.4))
    dim = Image.new("RGBA", base.size, (10, 18, 28, int(140 * a))); base.alpha_composite(dim)
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    if "sumbase" not in _cache:
        ss = 2; im = Image.new("RGBA", (1280 * ss, 720 * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([110 * ss, 46 * ss, 1170 * ss, 530 * ss], 30 * ss, fill=(255, 255, 255, 250))
        d.line([150 * ss, 290 * ss, 1130 * ss, 290 * ss], fill=(220, 226, 232, 255), width=3 * ss)
        _cache["sumbase"] = im.resize((1280, 720), Image.LANCZOS)
    lay.alpha_composite(_cache["sumbase"])
    for r, (head, th, chips) in enumerate(p["rows"]):
        y_h, y_c = (110, 205) if r == 0 else (350, 445)
        if t >= th:
            k, _ = _pop(t, th, th + 99)
            spr, off = tag_sprite(head, 48, YEL)
            _paste(lay, spr, 150 + spr.width / 2, y_h, k)
        x = 160
        for txt, at in chips:
            spr = chip_sprite(txt)
            if t >= at:
                k, _ = _pop(t, at, at + 99)
                _paste(lay, spr, x + spr.width / 2, y_c, k)
            x += spr.width + 18
    if a < 1.0:
        al = lay.getchannel("A").point(lambda v: int(v * a)); lay.putalpha(al)
    base.alpha_composite(lay)
