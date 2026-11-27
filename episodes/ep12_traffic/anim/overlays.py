# 12本目（渋滞）：3D の上に重ねる 2D（17本目の overlays.py から、使う物だけを写した）（札・吹き出し・題名・輪・小窓・左右の比べ）
#   一覧 EVENTS：(始め, 終わり, 種類, 中身)。時刻は声の時刻（timing.py）。絵コンテ表：../絵コンテ_v1.md
#   決まり：札の答えは、その言葉を言う瞬間に出す（SKILL §3）。字幕の帯（y 560 より下）に置かない。下の字幕と同じことを上に書かない（単語・数字・ラベルだけ）
#   字の大きさ：数字は 56 以上、ほかは 44〜52（1280×720。スマホで読める大きさ）。3D の中に字を書かないので、字は全部ここ
#   色：すいている＝緑・少しこむ＝黄・こんでいる＝赤。感知器＝水色。注目の輪＝黄
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ep04_robot", "look"))
import design as D
import timing as T
s, e, w, wp = T.s, T.e, T.w, T.wp
YEL = (255, 201, 40); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48)
ORANGE = (255, 138, 31); TEAL = D.TEAL; WAVE = (111, 208, 240); GREEN = (52, 178, 102)
SUB_TOP = 560
_cache = {}
EVENTS = None


def ev_list():
    """絵コンテ_v1.md と見比べて作る（冒頭・1章・2章）"""
    E = []
    add = lambda *a: E.append(a)
    # 冒頭
    add(s("02-01") + 0.1, e("02-01") + 0.3, "ring", dict(obj="ph_red", r=50, col=YEL))
    add(s("03-01") + 0.1, s("03-01") + 2.2, "ring", dict(obj="owncar", r=42, col=YEL))   # 12本目 v1 の確認役（2 回目）：上からの引きで、自分たちの車がほかの車にまぎれた → 曲がる前に、短い間だけ輪
    add(wp("02-02", "渋滞") - 0.1, e("02-02") + 0.3, "tag", dict(text="この先 渋滞", obj="phone", dy=-150, size=52, bg=RED, fg=WHITE))
    add(wp("02-04", "首を") - 0.2, e("02-04") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("03-04") + 0.05, s("04-01") - 0.05, "pair", dict(left=("TEX:ph_map_alert", 0), right=("A03b", e("03-02") - 0.3),
        cap=("地図の赤い線", "本当の車の列")))   # 消すのは次のカットに替わる所（e+0.4 で消すと、後ろの似た列の絵が 0.5 秒だけ見えてから替わった。v1 点検）
    add(wp("04-03", "測って") - 0.2, e("04-03") + 0.3, "bubble", dict(obj="maru_top", icon="?"))   # v1 の確認役：「？」が首をかしげる音より 2.6 秒早かった → かしげる時刻に
    add(wp("04-06", "細い道") - 0.1, e("04-06") + 0.3, "ring", dict(obj="ph_far", r=50, col=YEL))
    add(wp("04-07", "120万") - 0.1, e("04-07") + 0.4, "tag", dict(text="120万km以上", pos=(640, 92), size=64, bg=WHITE))
    add(wp("04-07", "地球") - 0.1, e("04-07") + 0.4, "tag", dict(text="地球 約30周", pos=(640, 196), size=64, bg=YEL))
    add(wp("04-08", "着く時刻") - 0.1, e("04-08") + 0.4, "tag", dict(text="着く時刻 17:40", obj="ph_eta", dy=0, size=48, bg=WHITE))
    add(wp("04-10", "誰が") - 0.1, e("04-10") + 0.5, "tag", dict(text="誰が測っている？", pos=(340, 110), size=56, bg=WHITE))
    add(wp("04-10", "どうして") - 0.1, e("04-10") + 0.5, "tag", dict(text="なぜ先まで分かる？", pos=(940, 110), size=56, bg=YEL))
    add(wp("04-10", "先のこと") - 0.1, s("04-11") - 0.1, "title", {})   # v1 のコメント：題の間（2.5 秒）に声がない → 間をやめ、題は「先のことまで分かるのか」の言葉の上から出す（約 2.6 秒）   # 次の文（04-11）の字幕に残っていた（v1 点検）。次の声の前に消す
    # 1章
    add(wp("06-04", "何が") - 0.2, e("06-04") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    # 2章
    add(s("07-02") + 0.1, e("07-02") + 0.3, "ring", dict(obj="sensor", r=60, col=YEL))
    add(wp("07-03", "感知器") - 0.1, e("07-03") + 0.4, "tag", dict(text="感知器", obj="sensor", dy=-120, size=56, bg=WAVE))
    add(wp("07-04", "何を") - 0.2, e("07-04") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("08-01") + 0.1, e("08-02") + 0.3, "tag", dict(text="感知器", obj="sensor", dx=230, dy=-40, size=52, bg=WAVE))   # 横から見た図：どれが感知器か（試しの絵の点検）
    add(wp("08-04", "車の数") - 0.1, e("08-04") + 0.4, "tag", dict(text="台数", obj="sensor", dx=-150, dy=-130, size=56, bg=WHITE))
    add(wp("08-04", "こみ具合") - 0.1, e("08-04") + 0.4, "tag", dict(text="こみ具合", obj="sensor", dx=170, dy=-130, size=56, bg=WHITE))
    add(wp("09-02", "警察") - 0.1, e("09-02") + 0.3, "tag", dict(text="警察", obj="police", dy=-90, size=52, bg=WHITE))
    add(wp("09-02", "道路") - 0.1, e("09-02") + 0.3, "tag", dict(text="道路を管理する会社", obj="roadco", dy=-90, size=48, bg=WHITE))
    add(wp("09-03", "まとめる") - 0.1, e("09-03") + 0.3, "tag", dict(text="まとめる所", obj="hub", dy=-90, size=52, bg=WHITE))
    add(wp("09-03", "電波") - 0.1, e("09-03") + 0.3, "tag", dict(text="電波", obj="tower", dy=-110, size=52, bg=YEL))
    add(wp("10-05", "橋") - 0.1, e("10-05") + 0.3, "ring", dict(obj="bridge", r=70, col=YEL))
    add(wp("10-05", "トンネル") - 0.1, e("10-05") + 0.3, "ring", dict(obj="tunnel", r=70, col=YEL))
    # 遠くから見た町で、輪の中の物が小さく、何を指しているか分からなかった（v1 点検、390px）→ 輪の上に名前の札
    add(wp("10-05", "橋") - 0.1, e("10-05") + 0.3, "tag", dict(text="橋", obj="bridge", dy=-105, size=48, bg=WHITE))
    add(wp("10-05", "トンネル") - 0.1, e("10-05") + 0.3, "tag", dict(text="トンネル", obj="tunnel", dy=-105, size=48, bg=WHITE))
    add(s("10-06") + 0.1, e("10-06") + 0.3, "ring", dict(obj="phone", r=80, col=YEL))
    add(s("10-07") + 0.05, e("10-07") + 0.4, "pip_clip", dict(clip="TEX:ph_map_z2", src_t=0, hold=True))
    add(wp("10-08", "なぜ") - 0.2, e("10-08") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    # 物について動く札（吹き出し・札・輪）は、カメラの替わり目（重なるつなぎ 0.35 秒）が終わってから出す（17本目 v1 のコメント）
    import json as _js
    _CL = _js.load(open(os.path.join(HERE, "clips.json"), encoding="utf-8"))
    _cuts = sorted(v[2] for k_, v in _CL.items())
    out = []
    for a_, b_, kd, p_ in E:
        a0_ = a_
        if "obj" in p_ or kd == "tag":   # 12本目 v1 の点検：位置を決めた札も、替わる途中の前の場面（霧）の上に出ていた
            for c_ in _cuts:
                if a_ - 0.42 <= c_ < b_ - 0.5 and c_ < a_ + 0.42: a_ = c_ + 0.42
        if a_ != a0_: MOVED[round(a0_, 2)] = a_
        out.append((a_, b_, kd, p_))
    return out


MOVED = {}   # 場面の替わり終わりまで遅らせた札：元の時刻 → 出す時刻（札の音も一緒に遅らせる）


def sfx_list():
    """札・図に合わせて鳴らす音：(時刻, 種類, 大きさ)"""
    L = []
    L.append((s("02-01") + 0.1, "pi", 0.3))
    L.append((s("03-04") + 0.05, "swish", 0.25))
    L.append((wp("04-07", "120万") - 0.1, "pop", 0.3)); L.append((wp("04-07", "地球") - 0.1, "pop", 0.3))
    L.append((wp("04-08", "着く時刻") - 0.1, "pop", 0.3))
    L.append((wp("04-10", "誰が") - 0.1, "pop", 0.3)); L.append((wp("04-10", "どうして") - 0.1, "pop", 0.3))
    L.append((wp("04-10", "先のこと") - 0.1, "title", 0.35))
    L.append((wp("07-03", "感知器") - 0.1, "pop", 0.3))
    L.append((wp("08-04", "車の数") - 0.1, "pop", 0.3)); L.append((wp("08-04", "こみ具合") - 0.1, "pop", 0.3))
    L.append((wp("10-05", "橋") - 0.1, "pi", 0.3)); L.append((wp("10-05", "トンネル") - 0.1, "pi", 0.3))
    L.append((s("10-07") + 0.05, "swish", 0.25))
    ev_list()
    return [(MOVED.get(round(t_, 2), t_), k_, g_) for t_, k_, g_ in L]   # 12本目 v1 の点検：札を遅らせたのに音だけ先に鳴っていた


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
        D.ctext(d, (cx, cy), kind, f, NAVY if kind != "!" else D.ORANGE)
    return dr


def bubble_sprite(kind):
    key = ("bub", kind)
    if key not in _cache:
        _cache[key] = D.bubble(120, 110, (0, 0), draw=icon_draw(kind))
    return _cache[key]


def title_sprite():
    """題：「地図アプリは、なぜ渋滞が分かる？」（「渋滞」を赤）"""
    key = ("title",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            f = D.font(60 * ss); a_, b_, c_ = "地図アプリは、なぜ", "渋滞", "が分かる？"
            wa, wb, wc = (d.textlength(x, font=f) for x in (a_, b_, c_)); x0 = W_ / 2 - (wa + wb + wc) / 2
            D.ctext(d, (x0 + wa / 2, H_ / 2), a_, f, NAVY); D.ctext(d, (x0 + wa + wb / 2, H_ / 2), b_, f, RED); D.ctext(d, (x0 + wa + wb + wc / 2, H_ / 2), c_, f, NAVY)
        spr, off = D.card(1080, 230, draw=dr)
        _cache[key] = spr
    return _cache[key]


def tex_frame(name):
    """v1 の点検：小窓・左右の絵に 3D の画面を写すと、小さく斜めで地図の色が見えなかった。画面の絵そのもの（横向きに戻す）を使う"""
    pth = os.path.join(os.environ.get("TEX12") or os.path.join(os.environ.get("MARU_WORK", ""), "stage", "tex12"), name + ".png")
    return Image.open(pth).convert("RGB").rotate(-90, expand=True) if os.path.exists(pth) else None


def imag_pip(im, w_, h_):
    """小窓（前の場面の切り抜き）：色はそのまま"""
    return im.convert("RGB").resize((w_, h_), Image.LANCZOS)


def _layer():
    return Image.new("RGBA", (1280 * 2, 720 * 2), (0, 0, 0, 0))


def _down(im):
    return im.resize((1280, 720), Image.LANCZOS)


def ring_img(q, r, col, a):
    im = _layer(); d = ImageDraw.Draw(im); S2 = 2
    d.ellipse([(q[0] - r) * S2, (q[1] - r) * S2, (q[0] + r) * S2, (q[1] + r) * S2], outline=(24, 38, 74, int(200 * a)), width=11 * S2)
    d.ellipse([(q[0] - r) * S2, (q[1] - r) * S2, (q[0] + r) * S2, (q[1] + r) * S2], outline=col + (int(255 * a),), width=7 * S2)
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
                if q is None or not (-20 <= q[0] <= 1300 and -20 <= q[1] <= 740): continue   # 物が画面の外なら出さない
                cx, cy = q[0] + p.get("dx", 0), min(max(70, q[1] + p.get("dy", -120)), SUB_TOP - 60)
            spr, off = tag_sprite(p["text"], p.get("size", 48), p.get("bg", WHITE), p.get("fg"))
            cx = min(max(cx, spr.width / 2 + 20), 1260 - spr.width / 2)
            _paste(base, spr, cx + (off[0] + spr.width / 2), cy + (off[1] + spr.height / 2), k, a)
        elif kind == "bubble":
            q = p["pos"] if "pos" in p else where(p["obj"], t)
            if q is None or not (-60 <= q[0] <= 1340): continue
            spr, off = bubble_sprite(p["icon"])
            cx = min(max(q[0], spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(q[1] - 40 - spr.height / 2, spr.height / 2 + 10), SUB_TOP - spr.height / 2)
            _paste(base, spr, cx, cy, k, a)
        elif kind == "title":
            base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(120 * a))))
            _paste(base, title_sprite(), 640, 290, k, a)
        elif kind == "ring":
            q = where(p["obj"], t)
            if q is None or not (0 <= q[0] <= 1280 and 0 <= q[1] <= 720): continue
            base.alpha_composite(ring_img((q[0] + p.get("dx", 0), q[1] + p.get("dy", 0)), p.get("r", 40) * k, p.get("col", WHITE), a))
        elif kind == "pair" and frame_of:
            for i_, ((cl_, st_), cap) in enumerate(zip((p["left"], p["right"]), p["cap"])):
                im = tex_frame(cl_[4:]) if cl_.startswith("TEX:") else frame_of(cl_, st_)
                if im is None: continue
                im = im.convert("RGB").resize((560, 315), Image.LANCZOS)
                fr = Image.new("RGBA", (572, 387), (255, 255, 255, 255)); fr.paste(im, (6, 6))
                dd = ImageDraw.Draw(fr); D.ctext(dd, (286, 352), cap, D.font(44), NAVY)
                _paste(base, fr, 340 + i_ * 600, 260, k, a)
        elif kind == "pip_clip" and frame_of:
            im = tex_frame(p["clip"][4:]) if p["clip"].startswith("TEX:") else frame_of(p["clip"], p["src_t"] + (0 if p.get("hold") else (t - t0)))
            if im is None: continue
            im = imag_pip(im, 544, 306)
            fr = Image.new("RGBA", (556, 318), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            _paste(base, fr, 30 + 278, 25 + 159, k, a)
    return base
