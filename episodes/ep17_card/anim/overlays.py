# 17本目（カード）：3D の上に重ねる 2D（16本目から写した）（札・吹き出し・題名・小窓・輪・メールの文・名札の絵・ニュースの見出し・数の図・遠くから操作する図・巻きもどし・想像の色）
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
s, e, w, wp = T.s, T.e, T.w, T.wp
YEL = (255, 201, 40); NAVY = D.NAVY; WHITE = (255, 255, 255); RED = (226, 58, 48)
ORANGE = (255, 138, 31); PURPLE = (138, 77, 255); TEAL = D.TEAL
BLUE = (52, 120, 230)
WRONG = "35280481"      # 打ちまちがえた番号（kit17.py・make_tex17.py と同じ）
import icons17 as IC
GREY = (190, 198, 210)
SUB_TOP = 560
_cache = {}
EVENTS = None


def ev_list():
    """絵コンテ_v1.md と見比べて作る（冒頭・1章・2章）"""
    E = []
    add = lambda *a: E.append(a)
    # 冒頭
    add(w("01-02", "はじめて") - 0.1, e("01-02") + 0.3, "bubble", dict(obj="maru_top", icon="heart"))
    add(s("02-03") - 0.05, e("02-03") + 0.3, "notice", {})
    add(w("02-04", "え") - 0.05, w("02-04", "え") + 0.95, "bubble", dict(obj="maru_top", icon="!"))   # v1 の点検：次の字幕に 0.2 秒残っていた → 次の字幕（声の波形で 33.54 秒）の直前で消す（言葉の時刻の見積もりは 0.6 秒早い）
    add(w("02-07", "お店") - 0.2, e("02-07") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("02-08") + 0.1, e("02-08") + 0.3, "notice", {})   # v1 の点検：スマホの画面が色の点だけで、買い物をしたと分からなかった → 知らせ（買い物ぶくろの絵）をもう一度
    add(s("03-01") + 0.2, e("03-02") + 0.3, "headlines", dict(t_more=s("03-02") + 0.2))
    add(s("03-04") - 0.05, e("03-04") + 0.5, "title", {})
    # 1章：3 か所に番号 → 1 つずつ小窓（想像）と × → 3 つ並べて ×
    for k_, nm in enumerate(("spot1", "spot2", "spot3")):
        add(w("04-04", "1つずつ") + 0.1 + 0.55 * k_, e("04-04") + 0.3, "num", dict(obj=nm, n=k_ + 1))
    add(s("05-01") + 0.05, e("05-03") + 0.6, "pip_clip", dict(clip="P05", src_t=s("05-01") + 0.05, x_at=w("05-03", "ありません")))
    add(s("06-01") + 0.05, e("06-03") + 0.6, "pip_clip", dict(clip="P06", src_t=s("06-01") + 0.05, x_at=w("06-03", "どこにも")))
    add(s("07-01") + 0.05, e("07-03") + 0.4, "pip_clip", dict(clip="P07", src_t=s("07-01") + 0.05, x_at=s("07-03")))
    add(s("08-01") + 0.05, e("08-01") + 0.4, "pip3", dict(clips=(("P05", s("05-01") + 2.0), ("P06", s("06-01") + 2.0), ("P07", s("07-01") + 2.0))))
    add(w("08-05", "いったい") - 0.2, e("08-05") + 0.4, "bubble", dict(obj="maru_top", icon="?"))
    # 2章：番号の札
    add(w("10-03", "14けた") - 0.1, e("10-04") + 0.3, "tag", dict(text="本物は 14〜16 けた", pos=(640, 92), size=52))
    add(w("10-04", "短く") - 0.1, e("10-04") + 0.3, "tag", dict(text="ここでは 8 けた", pos=(640, 178), size=48, bg=YEL))
    add(w("11-02", "6けた") - 0.1, e("11-02") + 0.3, "tag", dict(text="はじめの 6 けた ＝ どの会社か", pos=(640, 92), size=48))
    add(w("11-03", "会社の印") - 0.1, e("11-03") + 0.3, "tag", dict(text="会社の印", obj="tile0", dx=70, dy=-110, size=52, bg=BLUE, fg=WHITE))
    add(w("12-02", "役目") - 0.2, e("12-02") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    # v1 のコメント「計算で決まる数字が分からない。決まりの計算あるなら載せたい」（ユーザーの選択：かんたんな決まりで見せる）
    add(w("12-03", "前に") - 0.1, e("12-04") + 0.4, "sum", dict(y=125, lines=[   # v2 の点検：y=455 ではタイルの列にかかった → 上へ。v2 のコメント「式が消えるのが早い」：4.8 秒（46 字）→ 12-04 の終わりまで（10 秒）
        (w("12-03", "前に") - 0.1, "3＋5＋2＋8＋0＋4＋7 ＝ 29", NAVY),
        (w("12-03", "計算") - 0.1, "あと 1 で 30 → 最後の数字は 1", ORANGE),
        (w("12-03", "計算") - 0.1, "※かんたんな決まりで表しています", (110, 118, 132))]))
    add(s("12-04") + 0.05, e("12-04") + 0.4, "notebook", dict(check=w("12-04", "見直す") - 0.1))
    add(w("12-05", "検算の数字") - 0.1, e("12-05") + 0.3, "tag", dict(text="検算の数字", obj="tile7", dy=-110, size=52, bg=ORANGE, fg=WHITE))
    add(w("13-04", "となり") - 0.2, e("13-04") + 0.3, "ring", dict(obj="key" + WRONG[6], r=46, col=RED))   # v1 の点検：どのキーを押しまちがえたか分からなかった
    add(s("13-06") - 0.05, e("13-06") + 0.6, "tag", dict(text="番号がちがいます", pos=(640, 92), size=56, bg=RED, fg=WHITE))
    add(w("13-07", "その場") + 0.1, e("13-07") + 0.3, "xobj", dict(obj="dotq", sz=70))   # 光の点が止まった所（門の中）に ×（v1 のコメント：門の上のランプの赤い輪は、監視カメラに見えた）
    add(s("13-09") + 0.05, e("13-10") + 0.3, "sum", dict(y=130, t2=s("13-10") - 0.12, x2=965, y2=112, w2=600, lines2=[(0, "3＋5＋2＋8＋0＋4＋8 ＝ 30", NAVY), (0, "→ 0 になるはず", NAVY), (0, "でも、1 → 合わない ×", RED)], lines=[   # v2 のコメント（式が消えるのが早い）と同じ種類：5.6 秒（39 字）→ 13-10 の終わりまで（7.6 秒）。13-10 では短い 3 行にして右上へ（左のレジの画面と、下の字幕の帯を隠さない）
        (s("13-09") + 0.05, "3＋5＋2＋8＋0＋4＋8 ＝ 30", NAVY),
        (s("13-09") + 0.05, "→ 検算の数字は 0 になるはず", NAVY),
        (w("13-09", "検算") - 0.1, "でも、1 → 合わない ×", RED)]))
    add(w("13-08", "むっと") - 0.1, e("13-08") + 0.2, "bubble", dict(obj="maru_top", icon="hmph"))
    add(s("14-02") - 0.05, s("14-04") + 0.35, "tint", {})   # v1 の点検：e("14-03") で消え、想像の場面の終わり 1 秒が色なしに戻っていた → お店に戻る重ねの終わりまで
    add(w("14-06", "1人1人") - 0.1, e("14-06") + 0.3, "tag", dict(text="1人1人の数字", obj="stile4", dy=-100, size=48, bg=WHITE))
    add(max(w("14-07", "会社") - 0.1, s("14-07")), e("14-07") + 0.4, "tag", dict(text="会社の印", obj="stile0", dx=40, dy=-95, size=44, bg=BLUE, fg=WHITE))
    add(w("14-07", "1人1人") - 0.1, e("14-07") + 0.4, "tag", dict(text="1人1人の数字", obj="stile4", dy=95, size=44, bg=WHITE))
    add(w("14-07", "検算") - 0.1, e("14-07") + 0.4, "tag", dict(text="検算の数字", obj="stile7", dx=-30, dy=-95, size=44, bg=ORANGE, fg=WHITE))
    # 3章（2026-11-24）：絵コンテ表の 3章。言葉に合わせる時刻は wp()（声の本当の間から）
    add(wp("15-11", "本当に") - 0.1, e("15-11") + 0.4, "qmark", dict(obj="pile", dy=-110, size=150))
    add(wp("16-04", "光の") - 0.05, e("16-05") + 0.4, "tag", dict(text="光の問い合わせ", obj="qball", dy=-90, size=48))   # 390px の点検：下の字幕と同じ文を上にも書いていた（決まり：上は単語・ラベルだけ）→ 光の玉の名前に
    add(wp("16-08", "ブッブー") + 1.25, e("16-08") + 0.3, "xobj", dict(obj="drops", sz=100, dx=110))   # 通しの点検：門の前に落ちた札が細くて、はじかれたと分かりにくかった
    add(wp("16-12", "限らない") - 0.2, e("16-12") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(wp("17-08", "通って") - 0.1, e("17-08") + 0.3, "bubble", dict(obj="maru_top", icon="!"))   # 17-08 の前半は緑の札の寄り（まるロボは映らない）
    add(s("18-06") + 0.05, e("18-07") + 0.2, "pip3", dict(x_at=wp("18-07", "盗まれて") - 0.1, clips=(("P05", s("05-01") + 2.0), ("P06", s("06-01") + 2.0), ("P07", s("07-01") + 2.0))))   # 別の目の点検：18-06 で初めから × が付き、言っていることと逆だった → 「盗まれていなかった」の言葉で ×、文の終わりで消える
    add(s("18-09") + 0.05, e("18-11") + 0.3, "pip_clip", dict(clip="P18", src_t=s("18-09") + 0.05))
    add(wp("18-11", "クレジットマスター") - 0.1, e("18-11") + 0.4, "tag", dict(text="クレジットマスター", pos=(930, 110), size=56, bg=YEL))
    add(s("19-02") + 0.05, e("19-02") + 0.3, "pip_clip", dict(clip="P19", src_t=s("19-02") + 0.05))
    add(wp("19-03", "作る") - 0.1, s("19-05") + 0.35, "cycle", dict(t_a=wp("19-03", "作る"), t_b=wp("19-03", "試す"), t_arr=s("19-04")))   # 点検（flash_check）：e("19-04")+0.5 で消え、次のカットまで 0.3 秒だけ図のない絵が挟まった → 替わり目のつなぎが終わるまで
    # 4章（2026-11-26）：絵コンテ表の 4章
    add(s("20-01") - 0.1, wp("20-02", "金庫") - 0.2, "pip_clip", dict(clip="A01c", src_t=e("01-03") - 1.0))          # 冒頭の夜：カードが頭の上から金庫の棚へ飛んで入る（文ごとの点検：- 1.9 では歩く背中だけだった）
    add(wp("20-02", "金庫") - 0.2, s("20-03") + 0.35, "pip_clip", dict(clip="A01d", src_t=w("01-04", "閉めて") + 0.3, nopop=True))   # 別の目の点検：とびらが 2 回閉まって見えた → 閉まったあとから（ダイヤルを回す）  # とびらが閉まる（続きの小窓は出直さない）
    add(wp("20-03", "なぜ") - 0.1, e("20-03") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(s("21-04") + 0.05, e("21-04") + 0.4, "pip_clip", dict(clip="P21", src_t=s("21-04") + 0.05))
    add(wp("21-05", "ぽっと") + 0.3, e("21-07") + 0.3, "tag", dict(text="まるロボのカード", obj="mylamp", dy=-95, size=44, bg=IC.TEAL, fg=IC.NAVY))
    add(s("21-07") + 0.05, s("21-07") + 2.3, "pip_clip", dict(clip="A01b", src_t=w("01-01", "1枚") - 0.1))             # 封筒からカード
    add(s("21-07") + 2.3, e("21-07") + 0.3, "pip_clip", dict(clip="A01c", src_t=e("01-03") - 1.0, nopop=True))
    add(s("21-08") + 0.5, wp("21-08", "台帳") + 0.3, "qmark", dict(obj="lball", dy=-70, size=90))   # 別の目の点検：何を調べているか絵で分からなかった → 光の玉に「？」（字幕と同じ文の札は書かない）       # 金庫へしまう（続きの小窓は出直さない。文ごとの点検：途中で一度小さくなって出直した）
    add(wp("22-03", "2025年") - 0.1, s("22-07") + 0.05, "fig22", dict(t_num=wp("22-03", "およそ") - 0.1, t_c=wp("22-04", "9割") - 0.1,
        t_i=s("22-05") + 0.2, t_hl=wp("22-06", "当てられる") - 0.1))
    add(s("22-07") + 0.05, s("22-08") + 0.35, "pair",   # flash_check：札が消えてから次のカットまで 0.4 秒、図のない絵が挟まった → つなぎが終わるまで
        dict(left=("A01c", e("01-03") + 0.25), right=("D21e", wp("21-05", "ぽっと") + 1.5),
        cap=("金庫の中のカード", "塔の台帳の番号")))
    # 5章（2026-11-27）：絵コンテ表の 5章。字幕と同じ文は書かない（26-08 の問いはスマホの絵だけ）
    add(wp("23-05", "門番さんの") + 1.2, e("23-05") + 0.3, "bubble", dict(obj="maru_top", icon="!"))   # 胸を張る（得意）
    add(wp("26-13", "スマホに") - 0.05, e("26-14") + 0.3, "idv", dict(t_a=wp("26-13", "スマホに") + 0.1, t_b=wp("26-13", "持ち主") - 0.1))
    add(wp("26-14", "本人確認") - 0.1, e("26-14") + 0.3, "tag", dict(text="本人確認", pos=(640, 60), size=56, bg=YEL))
    add(s("27-01") + 0.05, wp("27-02", "金庫では") + 1.3, "pip_clip", dict(clip="A01c", src_t=e("01-03") - 1.0, fade=(wp("27-02", "金庫では") - 0.2, 1.4)))   # 冒頭の、カードを金庫にしまう所 → 27-02 でうすくなる
    add(wp("27-03", "本人確認") - 0.1, e("27-03") + 0.4, "glowtag", dict(text="本人確認", pos=(640, 150), size=80, t0=wp("27-03", "本人確認") - 0.1))
    add(s("28-04") + 0.05, e("28-04") + 0.3, "pip_clip", dict(clip="A02", src_t=w("02-01", "ブルッ") - 0.6))   # 2章の頭：スマホに知らせが届いた所
    add(wp("28-03", "カードを使った") - 0.1, e("28-09") + 0.4, "steps", dict(rows=[
        (wp("28-03", "カードを使った") - 0.1, ["① 使った知らせ"]),
        (wp("28-05", "明細を") - 0.1, ["② 明細を見る"]),
        (wp("28-06", "ネットの") - 0.1, ["③ 本人確認に登録"]),
        (wp("28-07", "おかしいと") - 0.1, ["④ おかしいと思ったら", "すぐカードの会社へ"])]))
    # v1 のコメント「シーン変わる前にはてな出してるからすぐ位置が移動してるの気になる」：物について動く札（吹き出し・札・輪）は、
    #   カメラの替わり目（重なるつなぎ 0.35〜0.6 秒）が終わってから出す。替わり目をまたぐ札は、替わり目のあとにずらす
    import json as _js
    _CL = _js.load(open(os.path.join(HERE, "clips.json"), encoding="utf-8"))
    _cuts = sorted(v[2] for k_, v in _CL.items() if not k_.startswith("P"))
    out = []
    for a_, b_, kd, p_ in E:
        if "obj" in p_:
            for c_ in _cuts:
                if a_ - 0.42 <= c_ < b_ - 0.5 and c_ < a_ + 0.42: a_ = c_ + 0.42   # 重なるつなぎ（0.35 秒）の中・直前に出る札は、つなぎが終わってから
        out.append((a_, b_, kd, p_))
    return out


def sfx_list():
    """札・図に合わせて鳴らす音：(時刻, 種類, 大きさ)"""
    L = []
    for i in range(3): L.append((s("03-01") + 0.2 + i * 0.45, "paper", 0.35))
    L.append((s("03-02") + 0.2, "paper", 0.35))
    for k_ in range(3): L.append((w("04-04", "1つずつ") + 0.1 + 0.55 * k_, "tick", 0.3))
    for t_ in (w("05-03", "ありません"), w("06-03", "どこにも"), s("07-03")): L.append((t_, "x_mark", 0.3))
    L.append((s("13-05") + 0.25, "key", 0.3))      # v1 の点検：13-05 の 8 つ目のキーは画面の寄りでキーが映らず、音が消えていた（表では「ポン」）
    L.append((s("14-02") - 0.05, "swish", 0.3)); L.append((s("14-04") - 0.05, "swish", 0.3))
    L.append((s("18-06") + 0.05, "swish", 0.25)); L.append((wp("18-07", "いなかった") + 0.1, "swish", 0.25))
    L.append((wp("18-11", "クレジットマスター") - 0.1, "pop", 0.3))
    L.append((wp("19-03", "作る"), "pop", 0.35)); L.append((wp("19-03", "試す"), "pop", 0.35)); L.append((s("19-04"), "swish", 0.3))
    L.append((s("20-01") - 0.1, "swish", 0.25)); L.append((s("21-04") + 0.05, "swish", 0.25)); L.append((s("21-07") + 0.05, "swish", 0.25))
    L.append((wp("22-03", "2025年") - 0.1, "pop", 0.3)); L.append((wp("22-03", "およそ") - 0.1, "thump", 0.35)); L.append((wp("22-04", "9割") - 0.1, "pi", 0.3))
    for k_ in range(3): L.append((s("22-05") + 0.2 + 0.35 * k_, "pop", 0.3))
    L.append((wp("22-06", "当てられる") - 0.1, "pi", 0.3)); L.append((s("22-07") + 0.05, "swish", 0.25))
    L.append((wp("26-13", "スマホに") + 0.1, "pop", 0.3)); L.append((wp("26-13", "持ち主") - 0.1, "pop", 0.3)); L.append((wp("26-14", "本人確認") - 0.1, "pi", 0.3))
    L.append((s("27-01") + 0.05, "swish", 0.25)); L.append((wp("27-03", "本人確認") - 0.1, "shimmer", 0.3)); L.append((s("28-04") + 0.05, "swish", 0.25))
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
        elif kind == "heart":
            r_ = 26 * ss
            d.ellipse((cx - r_ * 1.0, cy - r_ * 0.8, cx, cy + r_ * 0.2), fill=RED); d.ellipse((cx, cy - r_ * 0.8, cx + r_ * 1.0, cy + r_ * 0.2), fill=RED)
            d.polygon([(cx - r_ * 0.97, cy - r_ * 0.15), (cx + r_ * 0.97, cy - r_ * 0.15), (cx, cy + r_ * 1.0)], fill=RED)
        elif kind == "hmph":      # むっ：もくもくした小さな雲（字なし）
            r_ = 14 * ss
            for (ox, oy) in ((-1.2, 0.2), (0, -0.4), (1.2, 0.2), (0.4, 0.6), (-0.5, 0.6)):
                d.ellipse((cx + ox * r_ - r_, cy + oy * r_ - r_, cx + ox * r_ + r_, cy + oy * r_ + r_), fill=(120, 130, 150))
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
            # v1 のコメント「タイトルは使っていないカードが使われた？にして」（「使っていない」を黄色。ユーザーの選択）
            f = D.font(60 * ss); y_, n_ = "使っていない", "カードが使われた？"
            wy, wn = d.textlength(y_, font=f), d.textlength(n_, font=f); x0 = W_ / 2 - (wy + wn) / 2
            D.ctext(d, (x0 + wy / 2, H_ / 2), y_, f, (214, 150, 0)); D.ctext(d, (x0 + wy + wn / 2, H_ / 2), n_, f, NAVY)
        spr, off = D.card(1080, 230, draw=dr)
        _cache[key] = spr
    return _cache[key]


def notice_sprite():
    """02-03：カードの会社からの知らせ（カードの絵と買い物ぶくろの絵）"""
    key = ("notice",)
    if key not in _cache:
        def dr(d, W_, H_, ss, img):
            d.rounded_rectangle((40 * ss, 50 * ss, 150 * ss, 120 * ss), radius=10 * ss, fill=(52, 120, 230))
            IC.icon(d, "bag", 95 * ss, 160 * ss, 26 * ss, D.ORANGE)
            D.ctext(d, (W_ / 2 + 70 * ss, H_ / 2), "カードのご利用がありました", D.font(50 * ss), NAVY)
        spr, off = D.card(900, 210, draw=dr)
        _cache[key] = spr
    return _cache[key]


def headlines_sprite(t, t0, t_more=None):
    """03-01・03-02：新聞の切り抜き（v1 の点検：色の四角と線だけで、02-03 の知らせと同じ形に見えた → 新聞と分かる形に）。
    会社の名前・本当の見出しは書かない：太い黒い帯（見出し）・写真の枠（カードの絵）・段の線・赤い「？」だけ"""
    W_, H_ = 760, 470; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cols = [(52, 120, 230), (126, 84, 196), (220, 120, 60), (80, 160, 110)]
    n = 3 + (1 if t_more is not None and t >= t_more else 0)
    for k in range(n):
        if k < 3 and t < t0 + k * 0.45: break
        x0 = (20 + k * 58) * S2; y0 = (14 + k * 62) * S2; w_, h_ = 440, 230
        d.rectangle((x0 + 8 * S2, y0 + 8 * S2, x0 + (w_ + 8) * S2, y0 + (h_ + 8) * S2), fill=(0, 0, 0, 60))            # 影
        d.rectangle((x0, y0, x0 + w_ * S2, y0 + h_ * S2), fill=(246, 242, 230, 255), outline=(180, 174, 160, 255), width=2 * S2)
        d.rectangle((x0 + 18 * S2, y0 + 16 * S2, x0 + (w_ - 18) * S2, y0 + 26 * S2), fill=(40, 40, 46, 255))            # 新聞の名前の帯
        d.rectangle((x0 + 18 * S2, y0 + 40 * S2, x0 + 300 * S2, y0 + 72 * S2), fill=(30, 30, 36, 255))                  # 太い見出し
        D.ctext(d, (x0 + 350 * S2, y0 + 58 * S2), "？", D.font(64 * S2), RED)
        d.rectangle((x0 + 18 * S2, y0 + 88 * S2, x0 + 170 * S2, y0 + 200 * S2), fill=(214, 220, 228, 255))              # 写真の枠
        d.rounded_rectangle((x0 + 40 * S2, y0 + 118 * S2, x0 + 148 * S2, y0 + 172 * S2), radius=8 * S2, fill=cols[k])  # 写真：カード
        for c_ in range(2):
            for j in range(7):
                xx = x0 + (190 + c_ * 120) * S2
                d.rectangle((xx, y0 + (92 + j * 16) * S2, xx + (104 if j < 6 else 60) * S2, y0 + (98 + j * 16) * S2), fill=(150, 150, 158, 255))   # 段の線（本文）
    return im.resize((W_, H_), Image.LANCZOS)


def num_sprite(n):
    key = ("num", n)
    if key not in _cache:
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.ellipse((8, 8, 152, 152), fill=(255, 201, 40, 255)); D.ctext(d, (80, 76), str(n), D.font(100), NAVY)
        _cache[key] = im.resize((80, 80), Image.LANCZOS)
    return _cache[key]


def xmark(sz):
    im = Image.new("RGBA", (sz * 2, sz * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for (a_, b_) in (((0.15, 0.15), (0.85, 0.85)), ((0.85, 0.15), (0.15, 0.85))):
        d.line([(a_[0] * sz * 2, a_[1] * sz * 2), (b_[0] * sz * 2, b_[1] * sz * 2)], fill=(255, 255, 255, 255), width=int(sz * 0.34))
        d.line([(a_[0] * sz * 2, a_[1] * sz * 2), (b_[0] * sz * 2, b_[1] * sz * 2)], fill=RED + (255,), width=int(sz * 0.22))
    return im.resize((sz, sz), Image.LANCZOS)


def imag_pip(im, w_, h_):
    """小窓の想像の絵：青っぽく暗く（本当の出来事ではないと分かるように）"""
    im = im.convert("RGB").resize((w_, h_), Image.LANCZOS)
    ov = Image.new("RGB", im.size, (40, 60, 130)); im = Image.blend(im, ov, 0.35)
    return im


def sum_sprite(t, lines, W0=820):
    """かんたんな検算の決まりの足し算（v1 のコメント「計算で決まる数字が分からない」）。lines：[(出す時刻, 字, 色), ...]。字は 2D なので書いてよい"""
    W_, H_ = W0, 34 + 60 * len(lines); S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, W_ * S2 - 6, H_ * S2 - 6), radius=22 * S2, fill=(255, 253, 244, 240), outline=(200, 206, 214, 255), width=4 * S2)
    for i, (t0, txt, col) in enumerate(lines):
        if t < t0: continue
        D.ctext(d, (W_ / 2 * S2, (46 + 60 * i) * S2), txt, D.font(44 * S2), col)
    return im.resize((W_, H_), Image.LANCZOS)


def notebook_sprite(t, t_check):
    """12-04：ノートの足し算と、答えを見直す検算（v1 の点検：点の並びにしか見えなかった → 2D なので数字で書く。カードの計算のやり方ではない、ふつうの検算）"""
    W_, H_ = 520, 300; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, W_ * S2 - 6, H_ * S2 - 6), radius=24 * S2, fill=(255, 253, 244, 255), outline=(200, 206, 214, 255), width=4 * S2)
    for j in range(4): d.line([(30 * S2, (78 + j * 62) * S2), ((W_ - 30) * S2, (78 + j * 62) * S2)], fill=(190, 214, 236, 255), width=2 * S2)
    D.ctext(d, (220 * S2, 112 * S2), "12 ＋ 35 ＝ 47", D.font(56 * S2), NAVY)
    if t >= t_check - 0.6:
        D.ctext(d, (220 * S2, 200 * S2), "47 − 35 ＝ 12", D.font(56 * S2), ORANGE)
    if t >= t_check:
        d.line([(410 * S2, 190 * S2), (440 * S2, 222 * S2), (490 * S2, 160 * S2)], fill=(52, 178, 102, 255), width=16 * S2, joint="curve")
    return im.resize((W_, H_), Image.LANCZOS)


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


def headlines_sprite_ep16(t, t0):   # 16本目の物（使わない。同じ名前で 17本目の物を上書きしていた）
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
    if t >= p["t61"]: D.ctext(d, (240 * S2, 345 * S2), "出入口の機械 61件", D.font(40 * S2), (18, 140, 130))
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


def cycle_sprite(t, p):
    """19-03・19-04「作る。試す。当たるまで、くり返す」：左に機械の絵（作る）、右に門の絵（試す）。あいだを回る矢印"""
    W_, H_ = 760, 330; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, 240))
    LX, RX, CY = 170 * S2, 590 * S2, 140 * S2
    if t >= p["t_a"]:        # 機械（灰色の箱・札の口・ランプ）
        d.rounded_rectangle((LX - 70 * S2, CY - 70 * S2, LX + 70 * S2, CY + 70 * S2), radius=12 * S2, fill=(110, 116, 128))
        d.rectangle((LX - 45 * S2, CY + 18 * S2, LX + 45 * S2, CY + 30 * S2), fill=(21, 23, 27))
        d.ellipse((LX - 50 * S2, CY - 60 * S2, LX - 26 * S2, CY - 36 * S2), fill=(255, 179, 71))
        d.rounded_rectangle((LX - 40 * S2, CY + 30 * S2, LX + 40 * S2, CY + 46 * S2), radius=3 * S2, fill=(250, 250, 247), outline=NAVY, width=2 * S2)
        D.ctext(d, (LX, CY + 128 * S2), "作る", D.font(52 * S2), NAVY)
    if t >= p["t_b"]:        # 門（木のアーチ）
        c = (138, 106, 72)
        d.rectangle((RX - 70 * S2, CY - 60 * S2, RX - 50 * S2, CY + 70 * S2), fill=c); d.rectangle((RX + 50 * S2, CY - 60 * S2, RX + 70 * S2, CY + 70 * S2), fill=c)
        d.rectangle((RX - 80 * S2, CY - 78 * S2, RX + 80 * S2, CY - 56 * S2), fill=c)
        for j in range(8):          # しまの日よけ（お店の門と分かるように。別の目の点検：机に見えた）
            d.rectangle((RX - 96 * S2 + j * 24 * S2, CY - 104 * S2, RX - 72 * S2 + j * 24 * S2, CY - 80 * S2), fill=(224, 106, 90) if j % 2 == 0 else (255, 255, 255))
        d.rectangle((RX - 96 * S2, CY - 104 * S2, RX + 96 * S2, CY - 80 * S2), outline=(200, 90, 76), width=2 * S2)
        d.rectangle((RX - 46 * S2, CY - 52 * S2, RX + 46 * S2, CY + 70 * S2), fill=(246, 232, 214))   # 門の中（お店の中の明るい床）
        D.ctext(d, (RX, CY + 128 * S2), "試す", D.font(52 * S2), NAVY)
    if t >= p["t_arr"]:      # 回る矢印（上：機械 → 門、下：門 → 機械）。0.6 秒でのびて、そのあと光の点が回る
        g = min(1.0, (t - p["t_arr"]) / 0.6); col = (52, 120, 230)
        for top in (True, False):
            box = (LX + 10 * S2, CY - 130 * S2, RX - 10 * S2, CY + 130 * S2)
            a0, a1 = (200, 340) if top else (20, 160)
            d.arc(box, a0, a0 + (a1 - a0) * g, fill=col, width=9 * S2)
            if g >= 1.0:
                ang = math.radians(a1); cx_ = (box[0] + box[2]) / 2 + (box[2] - box[0]) / 2 * math.cos(ang); cy_ = (box[1] + box[3]) / 2 + (box[3] - box[1]) / 2 * math.sin(ang)
                dx_, dy_ = -math.sin(ang), math.cos(ang); L_ = 22 * S2; nx_, ny_ = -dy_, dx_
                d.polygon([(cx_ + dx_ * L_, cy_ + dy_ * L_), (cx_ + nx_ * L_ * 0.7, cy_ + ny_ * L_ * 0.7), (cx_ - nx_ * L_ * 0.7, cy_ - ny_ * L_ * 0.7)], fill=col)
        if g >= 1.0:
            ph = ((t - p["t_arr"] - 0.6) / 1.6) % 1.0; ang = math.radians(200 + 360 * ph)
            box = (LX + 10 * S2, CY - 130 * S2, RX - 10 * S2, CY + 130 * S2)
            cx_ = (box[0] + box[2]) / 2 + (box[2] - box[0]) / 2 * math.cos(ang); cy_ = (box[1] + box[3]) / 2 + (box[3] - box[1]) / 2 * math.sin(ang)
            d.ellipse((cx_ - 12 * S2, cy_ - 12 * S2, cx_ + 12 * S2, cy_ + 12 * S2), fill=(255, 201, 40))
    return im.resize((W_, H_), Image.LANCZOS)


def idv_sprite(t, p):
    """26-13：本人確認の 2 つの例（字の名前は短く。字幕の文は書かない）：スマホに届いた数字を打ちこむ・指で画面にふれる"""
    W_, H_ = 700, 300; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, 240))
    for j, (kd, lab, ta) in enumerate((("keypad", "数字を打ちこむ", p["t_a"]), ("finger", "指でふれる", p["t_b"]))):
        if t < ta: continue
        cx = (185 + j * 330) * S2
        IC.icon5(d, kd, cx, 115 * S2, 78 * S2, NAVY)
        D.ctext(d, (cx, 245 * S2), lab, D.font(44 * S2), NAVY)
    return im.resize((W_, H_), Image.LANCZOS)


def glowtag_sprite(t, p):
    """27-03：「本人確認」の札が大きく光る（黄色い光の輪が広がる）"""
    spr, off = tag_sprite(p["text"], p.get("size", 72), p.get("bg", YEL), p.get("fg"))
    W_, H_ = spr.width + 120, spr.height + 120
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    u = ((t - p["t0"]) / 1.2) % 1.0
    for r_ in range(3):
        g = max(0.0, 1.0 - u - r_ * 0.25)
        if g <= 0: continue
        pad = int(20 + 40 * (u + r_ * 0.25))
        d.rounded_rectangle((60 - pad, 60 - pad, W_ - 60 + pad, H_ - 60 + pad), radius=40 + pad, outline=(255, 214, 60, int(200 * g)), width=8)
    im.alpha_composite(spr, (60, 60))
    return im


def steps_sprite(t, p):
    """28-03〜28-09：自分でできること（出したまま下に足していく。いま言っている段は黄色）"""
    rows = [(tt, lines) for tt, lines in p["rows"] if t >= tt]
    S2 = 2; W_ = 540; LH = 62
    nlines = sum(len(l) for _, l in rows)
    H_ = 30 + nlines * LH + 10 * max(0, len(rows) - 1) + 20
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=26 * S2, fill=(255, 255, 255, 236))
    y = 30
    for i, (tt, lines) in enumerate(rows):
        now = (i == len(rows) - 1) and (t - tt < p.get("hl", 4.0))
        h = len(lines) * LH
        if now: d.rounded_rectangle((12 * S2, (y - 8) * S2, (W_ - 12) * S2, (y + h - 4) * S2), radius=14 * S2, fill=(255, 236, 150, 255))
        for j, ln in enumerate(lines):
            d.text(((30 if j == 0 else 74) * S2, (y + j * LH) * S2), ln, font=D.font(44 * S2), fill=NAVY + (255,))
        y += h + 10
    return im.resize((W_, H_), Image.LANCZOS)


def fig22_sprite(t, p):
    """22-03〜22-06：被害の数字（約 510 億円・2025年・1年間）、10 に分けた丸（9 つが青＝番号だけ）、きっかけの 3 つの絵（「当てられた」だけ光る）。
    数字の出どころ：日本クレジット協会の発表（2025 年 510.5 億円、番号盗用 93.1％）"""
    W_, H_ = 1040, 490; S2 = 2
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ * S2 - 1, H_ * S2 - 1), radius=30 * S2, fill=(255, 255, 255, 242))
    D.ctext(d, (290 * S2, 62 * S2), "2025年・1年間", D.font(44 * S2), (110, 118, 132))
    if t >= p["t_num"]:
        D.ctext(d, (290 * S2, 160 * S2), "約 510 億円", D.font(92 * S2), RED)
    if t >= p["t_c"]:
        cx, cy, r = 790 * S2, 150 * S2, 110 * S2
        g = min(1.0, (t - p["t_c"]) / 0.9)
        for k in range(10):
            a0, a1 = -90 + k * 36, -90 + (k + 1) * 36 - 3
            on = k < 9 and k < int(round(g * 9 + 0.49))
            d.pieslice((cx - r, cy - r, cx + r, cy + r), a0, a1, fill=BLUE if on else (205, 210, 218))
        d.ellipse((cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45), fill=(255, 255, 255))
        D.ctext(d, (790 * S2, 296 * S2), "番号だけ：9割以上", D.font(44 * S2), NAVY)
    if t >= p["t_i"]:
        labels = ("のぞき見", "漏れた", "当てられた")
        for k, lab in enumerate(labels):
            if t < p["t_i"] + 0.35 * k: continue
            dim = t >= p["t_hl"] and k != 2
            col = (190, 196, 206) if dim else NAVY
            x = (200 + k * 320) * S2; y = 372 * S2      # 390px の点検：名前が絵に重なり、右の名前が枠からはみ出した → 名前は絵の下に
            if k == 0:     # 目
                d.ellipse((x - 46 * S2, y - 24 * S2, x + 46 * S2, y + 24 * S2), outline=col, width=6 * S2)
                d.ellipse((x - 14 * S2, y - 14 * S2, x + 14 * S2, y + 14 * S2), fill=col)
            elif k == 1:   # 書類としずく
                d.rectangle((x - 30 * S2, y - 38 * S2, x + 24 * S2, y + 34 * S2), outline=col, width=5 * S2)
                for j in range(3): d.line((x - 18 * S2, y - 20 * S2 + j * 16 * S2, x + 12 * S2, y - 20 * S2 + j * 16 * S2), fill=col, width=4 * S2)
                dcol = (190, 196, 206) if dim else BLUE         # しずく（別の目の点検：黒い点に見えた）
                d.polygon([(x + 38 * S2, y + 4 * S2), (x + 28 * S2, y + 24 * S2), (x + 48 * S2, y + 24 * S2)], fill=dcol)
                d.ellipse((x + 28 * S2, y + 16 * S2, x + 48 * S2, y + 36 * S2), fill=dcol)
            else:          # 当てられた札（緑のふち）
                gcol = (190, 196, 206) if dim else (52, 178, 102)
                for j in range(4):
                    d.rounded_rectangle((x - 62 * S2 + j * 32 * S2, y - 22 * S2, x - 36 * S2 + j * 32 * S2, y + 22 * S2), radius=5 * S2, outline=gcol, width=5 * S2)
                    D.ctext(d, (x - 49 * S2 + j * 32 * S2, y), "35??"[j], D.font(26 * S2), col)   # 札の数字（別の目の点検：空の四角が字化けに見えた）
                if t >= p["t_hl"]:
                    d.rounded_rectangle((x - 74 * S2, y - 40 * S2, x + 74 * S2, y + 40 * S2), radius=14 * S2, outline=YEL, width=6 * S2)
            D.ctext(d, (x, y + 76 * S2), lab, D.font(44 * S2), col)
    return im.resize((W_, H_), Image.LANCZOS)


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
            cx = min(max(q[0], spr.width / 2 + 10), 1270 - spr.width / 2); cy = min(max(q[1] - 40 - spr.height / 2, spr.height / 2 + 10), SUB_TOP - spr.height / 2)
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
            _paste(base, headlines_sprite(t, t0, p.get("t_more")), 860, 280, 1.0, a)   # v1 の点検：まるロボの目の上に重なった → 右へ
        elif kind == "notice":
            _paste(base, notice_sprite(), 640, 130, k, a)
        elif kind == "num":
            q = where(p["obj"], t)
            if q is None or not (0 <= q[0] <= 1280 and 0 <= q[1] <= 720): continue
            _paste(base, num_sprite(p["n"]), q[0], max(50, q[1] - 70), k, a)
        elif kind == "xobj":
            q = where(p["obj"], t)
            if q is None or not (0 <= q[0] <= 1280 and 0 <= q[1] <= 720): continue
            sz = p.get("sz", 60); _paste(base, xmark(sz), q[0] + p.get("dx", 0), q[1] + p.get("dy", 0), k, a)
        elif kind == "sum":
            if "t2" in p and t >= p["t2"]:      # 次の場面では、小さくして空いている所へ（13-10：レジの画面を隠さない）
                _paste(base, sum_sprite(t, p.get("lines2", p["lines"]), p.get("w2", 820)), p["x2"], p["y2"], k, a)   # 字は小さくしない（44 より小さいとスマホで読めない）
            else:
                _paste(base, sum_sprite(t, p["lines"]), 640, p.get("y", 470), k, a)
        elif kind == "notebook":
            _paste(base, notebook_sprite(t, p["check"]), 290, 395, k, a)   # v2：式の札（上）と重ならないよう、少し下へ   # v1 の点検：タイルの列の左を隠していた → 下へ
        elif kind == "pip3" and frame_of:
            for i_, (cl_, st_) in enumerate(p["clips"]):
                im = frame_of(cl_, st_)
                if im is None: continue
                im = imag_pip(im, 360, 203)
                fr = Image.new("RGBA", (372, 215), (255, 255, 255, 255)); fr.paste(im, (6, 6))
                if p.get("x_at") is None or t >= p["x_at"]: fr.alpha_composite(xmark(150), (111, 32))   # 3章 18-06：「盗まれたと思っていた」では × を付けない（別の目の点検）
                _paste(base, fr, 230 + i_ * 410, 190, k, a)
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
        elif kind == "fig22":
            _paste(base, fig22_sprite(t, p), 640, 290, k, a)
        elif kind == "pair" and frame_of:
            for i_, ((cl_, st_), cap) in enumerate(zip((p["left"], p["right"]), p["cap"])):
                im = frame_of(cl_, st_)
                if im is None: continue
                im = im.convert("RGB").resize((560, 315), Image.LANCZOS)
                fr = Image.new("RGBA", (572, 387), (255, 255, 255, 255)); fr.paste(im, (6, 6))
                dd = ImageDraw.Draw(fr); D.ctext(dd, (286, 352), cap, D.font(40), NAVY)
                _paste(base, fr, 340 + i_ * 600, 260, k, a)
        elif kind == "cycle":
            _paste(base, cycle_sprite(t, p), 640, 250, k, a)
        elif kind == "idv":
            _paste(base, idv_sprite(t, p), 640, 235, k, a)
        elif kind == "glowtag":
            spr = glowtag_sprite(t, p); _paste(base, spr, p["pos"][0], p["pos"][1], k, a)
        elif kind == "steps":
            spr = steps_sprite(t, p); _paste(base, spr, 1260 - spr.width / 2, 30 + spr.height / 2, 1.0, a)
        elif kind == "remote":
            _paste(base, remote_sprite(t, t0, p), 640, 290, k, a)
        elif kind == "rewind":
            base.alpha_composite(rewind_layer(t, t0))
        elif kind == "pip_clip" and frame_of:
            if p.get("nopop"): k = 1.0          # 前の小窓の続き：小さくなって出直さない
            if p.get("fade") and t >= p["fade"][0]: a *= max(0.0, 1.0 - (t - p["fade"][0]) / p["fade"][1])   # 5章 27-02「小窓の金庫がうすくなる」：ゆっくり消える
            im = frame_of(p["clip"], p["src_t"] + (0 if p.get("hold") else (t - t0)))
            if im is None: continue
            im = imag_pip(im, 544, 306)      # 小窓は想像の絵（青っぽく）。大きさは 16本目 v1 の確認役の直し（544×306）
            fr = Image.new("RGBA", (556, 318), (255, 255, 255, 255)); fr.paste(im, (6, 6))
            if p.get("x_at") is not None and t >= p["x_at"]: fr.alpha_composite(xmark(220), (168, 49))
            _paste(base, fr, 30 + 278, 25 + 159, k, a)
    return base
