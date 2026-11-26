# 16本目 5章（S25〜S26）の 2D：開いた名簿のページ（6 つの絵が言葉の時刻に 1 つずつ光る）・冒頭 02-08 の小窓・語り手の「？」
#   overlays.py の ev_list / sfx_list / draw から呼ぶ。決まりは 1〜4章と同じ（字幕の帯に置かない・言葉の瞬間に出す・字は 44 以上・
#   図は 1 文で 1 段ずつ・語り手の「？」は画面のすみ・物は急に出さない）。絵コンテ表：../絵コンテ_v1.md の「5章」
import os, sys, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import timing as T
import icons16 as IC
from overlays2 import wv, _canvas, _done, S2, NAVY, RED
s, e = T.s, T.e
TEAL = (47, 217, 200); TEAL_L = (210, 248, 243)
BOOK_ITEMS = [("face", "名前"), ("house", "住所"), ("phone", "電話"), ("cake", "誕生日"), ("bldg", "勤め先"), ("bag", "買った物")]


def book_sprite(t, p):
    """26-05：開いた名簿（左右 2 ページ、青緑の表紙のふち）。6 つの絵が、言う言葉の時刻に 1 つずつ光り、下に言葉が出る。
    開くとき：はじめ閉じた表紙（右半分だけ）→ 0.5 秒で左へ開く（急に出さない）"""
    W_, H_ = 1000, 520
    im = Image.new("RGBA", (W_ * S2, H_ * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    u = min(1.0, max(0.0, (t - p["t_open"]) / 0.5)); u = u * u * (3 - 2 * u)
    cx = W_ / 2
    x0 = cx - (cx - 40) * u                                                  # 左のページは開くにつれて左へのびる
    d.rounded_rectangle((x0 * S2, 20 * S2, (W_ - 40) * S2, (H_ - 20) * S2), radius=22 * S2, fill=(31, 168, 154, 255))      # 表紙（ふち）
    d.rounded_rectangle(((x0 + 14) * S2, 34 * S2, (W_ - 54) * S2, (H_ - 34) * S2), radius=14 * S2, fill=(250, 248, 240, 255))
    if u < 1.0:
        return im.resize((W_, H_), Image.LANCZOS)
    for i, (kd, nm) in enumerate(BOOK_ITEMS):      # 2 段 × 3 つ（試しの絵：1 列に 6 つだと「電話誕生日」のように字が重なった）
        col, row = i % 3, i // 3
        x = 200 + col * 300; y = 110 + row * 200
        lit = t >= p["lit"][i]
        if lit:
            v = min(1.0, (t - p["lit"][i]) / 0.25)
            r = 56 + 10 * math.sin(v * math.pi)
            d.ellipse(((x - r) * S2, (y - r) * S2, (x + r) * S2, (y + r) * S2), fill=TEAL_L + (255,))
        IC.icon(d, kd, x * S2, y * S2, 38 * S2, NAVY if lit else (176, 182, 194))
        if lit: D.ctext(d, (x * S2, (y + 86) * S2), nm, D.font(44 * S2), NAVY)
    return im.resize((W_, H_), Image.LANCZOS)


def W26():
    """26-05 の 6 つの言葉の時刻（make_word_times.py が拾えるように、1 つずつ書く）"""
    return [wv("26-05", "名前"), wv("26-05", "住所"), wv("26-05", "電話"), wv("26-05", "誕生日"), wv("26-05", "勤め先"), wv("26-05", "買った物")]


def ev_list5():
    E = []
    add = lambda *a: E.append(a)
    add(wv("25-06", "なぜ") - 0.3, e("25-06") + 0.3, "bubble", dict(obj="maru_top", icon="?"))
    add(wv("25-06", "並べて") - 0.1, e("25-06") + 0.3, "qmark", dict(pos=(1120, 140), size=150))      # 語り手の問い（画面のすみ）
    lit = [t_ - 0.1 for t_ in W26()]
    add(s("26-05") - 0.25, e("26-05") + 0.3, "c5_book", dict(t_open=s("26-05") - 0.2, lit=lit))
    # 26-06：冒頭 02-08 と同じ入力の絵（ケーキとビルに灰色の×）。言い終わった形をそのまま
    add(s("26-06") + 0.1, e("26-06") + 0.3, "form", dict(lit=[-100.0] * 4, fly=-100.0, back=-100.0, extra=-100.0))
    add(wv("26-11", "何に") - 0.2, e("26-11") + 0.3, "qmark", dict(pos=(1120, 140), size=150))
    return E


def sfx_list5():
    L = []
    for t_ in W26():
        L.append((t_ - 0.1, "tick", 0.25))       # 絵が光る時刻（pop は声のすき間へずらされるので tick）
    L.append((s("26-05") - 0.2, "paper", 0.45))              # 名簿が開く「ぱさ」
    return L


def draw5(kind, t, t0, p, base, where, _paste, _pop_k, _pop_a):
    k, a = _pop_k, _pop_a
    if kind == "c5_book":
        base.alpha_composite(Image.new("RGBA", base.size, (8, 14, 26, int(110 * a))))
        spr = book_sprite(t, p); _paste(base, spr, 640, 30 + spr.height / 2, k, a)
