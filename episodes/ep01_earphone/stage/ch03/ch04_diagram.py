# 第4章「届くことと、再生することは違う」の図の場面（本編 2:45.1〜4:24.4、D2〜D7）
#   C13（第3章の最後の図）と同じ描き方：上に自分の組（スマホ → イヤホン）、下に隣の組。ナレーションの1文ずつに合わせて動く
#   D2 組の紹介 → D3 電波はまわり一面に広がる（両方のイヤホンに届く。隣の電波もこちらへ）→ D4 自分のイヤホンに両方の荷物が届く
#   → D5 印（○・△）を付ける：受付口が確かめ、○は取り込んで鳴らし、△は鳴らさない → D6 隣も同じ。こちらはこちら、あちらはあちら
#   → D7 本当は「どの通信かを見分ける情報」→ ペアリングで同じ鍵 → 荷物に鍵：つないだ相手だけが開けられる
# 使い方: python3 ch04_diagram.py OUT_DIR [--still 秒,秒,...]  → OUT_DIR/diagram/d_0001.png …（1280×720・24fps）と events.json（効果音の時刻）
import sys, os, math, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.join(HERE, "..", "av", "fonts", "japanese.ttc")
W, H, FPS, S = 1280, 720, 24, 2
if os.environ.get("MARU_RES") == "1080": S = 3        # 本番：1.5 倍の大きさ（3 倍で描いて 1920×1080 に縮める）。座標は 1280×720 のまま
OUT_WH = (1920, 1080) if S == 3 else (W, H)
T0, T1 = 165.10, 264.40                      # 図の場面の始まりと終わり（本編の秒）
BG = (238, 242, 245); INK = (40, 46, 52); TEAL = (31, 94, 102); CYAN = (63, 198, 201); AMBER = (214, 128, 44)
GRAY = (150, 158, 166); GREEN = (52, 168, 96); RED = (196, 72, 62); WHITE = (250, 250, 248); DARK = (42, 45, 49)
TOP, BOT = 205, 462; PX, EX = 330, 1030      # 組の高さ、スマホとイヤホンの横の位置（v2：物を1.25倍、文字を大きく）
DS = 1.25                                    # スマホ・イヤホンの大きさ
A_COL = ((45, 172, 205), (232, 110, 160)); B_COL = ((242, 168, 64), (112, 72, 168))
PAIR = {"A": dict(y=TOP, col=TEAL, scr=A_COL, mark="o", name="自分の組"), "B": dict(y=BOT, col=AMBER, scr=B_COL, mark="t", name="隣の組")}
_fonts = {}


def font(px):
    k = int(px * S)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FONT, k)
    return _fonts[k]


def sm(u):
    u = max(0.0, min(1.0, u)); return u * u * u * (10 - 15 * u + 6 * u * u)


def win(t, a, b, fi=0.35, fo=0.35):
    """a〜b 秒で 1（入り fi 秒・出 fo 秒でなめらかに）"""
    return sm((t - a) / fi) * (1 - sm((t - b) / fo)) if fo > 0 else sm((t - a) / fi)


def mix(c, a, bg=BG): return tuple(int(bg[i] + (c[i] - bg[i]) * max(0.0, min(1.0, a))) for i in range(3))


class Pen:
    def __init__(self, d): self.d = d
    def rr(self, box, r, fill=None, outline=None, width=1):
        self.d.rounded_rectangle([v * S for v in box], radius=r * S, fill=fill, outline=outline, width=int(width * S) if outline else 0)
    def ell(self, box, fill=None, outline=None, width=1):
        self.d.ellipse([v * S for v in box], fill=fill, outline=outline, width=int(width * S) if outline else 0)
    def line(self, pts, fill, width): self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")
    def poly(self, pts, fill=None, outline=None, width=1): self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=outline, width=int(width * S) if outline else 0)
    def arc(self, c, r, a0, a1, fill, width): self.d.arc([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], a0, a1, fill=fill, width=int(width * S))
    def text(self, xy, s, px, fill, anchor="mm", bold=True):
        self.d.text((xy[0] * S, xy[1] * S), s, font=font(px), fill=fill, anchor=anchor, stroke_width=int(px * S * 0.035) if bold else 0, stroke_fill=fill)


def mark(p, c, kind, r, col, width=4):
    """○（自分の組）・△（隣の組）"""
    if kind == "o": p.ell((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col, width=width)
    else:
        pts = [(c[0], c[1] - r * 1.15), (c[0] - r * 1.05, c[1] + r * 0.75), (c[0] + r * 1.05, c[1] + r * 0.75)]
        p.poly(pts, outline=col, width=width)


# ---------------------------------------------------------------- 物の形
def phone(p, x, y, cols, a=1.0, ds=None, screen=True):
    DS = ds or globals()["DS"]
    q = lambda dx0, dy0, dx1, dy1: (x + dx0 * DS, y + dy0 * DS, x + dx1 * DS, y + dy1 * DS)
    p.rr(q(-40, -76, 40, 76), 12 * DS, fill=mix(INK, a)); p.rr(q(-33, -68, 33, 68), 7 * DS, fill=mix((23, 27, 32), a))
    if not screen: return
    for k in range(20):
        c = tuple(int(u + (v - u) * k / 19) for u, v in zip(cols[0], cols[1]))
        b = q(-25, -58 + k * 2.4, 25, -58 + (k + 1) * 2.4); p.d.rectangle([v * S for v in b], fill=mix(c, a))
    p.ell(q(-9, -47, 9, -29), fill=mix((250, 240, 222), a))
    p.rr(q(-25, 6, 15, 11), 2, fill=mix((225, 230, 235), a)); p.rr(q(-25, 18, 2, 22), 2, fill=mix((120, 128, 138), a))


def SLOT(y): return (EX + 7 * DS, y + 44 * DS)        # 受付口の中心（軸の上）
def TIP(y): return (EX - 47 * DS, y - 23 * DS)        # 耳の先（音が出る所）


def earbud(p, x, y, slot_col, lamp, a=1.0, glow=0.0, ds=None):
    DS = ds or globals()["DS"]
    q = lambda dx0, dy0, dx1, dy1: (x + dx0 * DS, y + dy0 * DS, x + dx1 * DS, y + dy1 * DS)
    if glow > 0:
        for k in range(3): p.ell(q(-64 - 8 * k, -62 - 8 * k, 50 + 8 * k, 22 + 8 * k), outline=mix(slot_col, glow * (0.35 - 0.1 * k)), width=4)
    p.ell(q(-46, -54, 34, 14), fill=mix(WHITE, a), outline=mix((205, 210, 215), a), width=3)
    p.rr(q(-5, -2, 19, 86), 12 * DS, fill=mix(WHITE, a), outline=mix((205, 210, 215), a), width=3)
    p.ell(q(-58, -36, -36, -10), fill=mix((205, 212, 218), a))
    p.rr(q(-1, 34, 15, 54), 4 * DS, fill=mix(slot_col, a))
    p.ell(q(2, 18, 12, 28), fill=mix(lamp, a))                                   # 受付の灯（灰 → 緑／赤）


def parcel(p, c, col, sc=1.0, a=1.0, mk=None, mk_a=0.0, band=0.0, band_col=None, lock=0.0, lock_open=0.0, xmark=0.0, mk_sc=1.0):
    x, y = c; w, h = 30 * sc, 21 * sc
    p.rr((x - w, y - h, x + w, y + h), 7 * sc, fill=mix(col, a))
    p.rr((x - w + 5 * sc, y - h + 5 * sc, x + w - 5 * sc, y + h - 5 * sc), 4 * sc, fill=mix(DARK, a))
    for b in range(5):                                                            # 中身（曲のデータ）
        hh = (5, 10, 7, 12, 8)[b] * sc
        p.d.rectangle([(x - 4 * sc + b * 6 * sc) * S, (y + 11 * sc - hh) * S, (x - 1 * sc + b * 6 * sc) * S, (y + 11 * sc) * S], fill=mix((233, 236, 238), a))
    if mk and mk_a > 0 and mk_sc > 0.02:                                       # v7：印を大きく（半径 7 → 10）
        mark(p, (x - 14.5 * sc, y + (1.5 if mk == "t" else -1.0) * sc), mk, 10 * sc * mk_sc, mix((233, 236, 238), a * mk_a), max(2, int(4 * sc)))
    if band > 0:                                                                  # どの通信かを見分ける情報（荷物の頭の帯）
        bc = band_col or col; bw = 2 * w * band
        p.rr((x - w, y - h - 9 * sc, x - w + bw, y - h + 1 * sc), 3 * sc, fill=mix(bc, a))
        pat = (1, 0, 1, 1, 0, 1, 0, 0) if bc == TEAL else (0, 1, 1, 0, 1, 0, 1, 1)
        for k, on in enumerate(pat):
            if on and (k + 1) * 7 * sc <= bw: p.d.rectangle([(x - w + 3 * sc + k * 7 * sc) * S, (y - h - 6 * sc) * S, (x - w + 7 * sc + k * 7 * sc) * S, (y - h - 2 * sc) * S], fill=mix(WHITE, a))
    if lock > 0:                                                                  # 鍵（南京錠）：開くと掛け金が上がる
        lx, ly = x + 22 * sc, y + 16 * sc; la = a * lock; lc = mix((70, 76, 84), la)
        p.arc((lx, ly - 6 * sc - 7 * sc * lock_open), 6 * sc, 180, 360, fill=lc, width=max(2, int(3 * sc)))
        p.rr((lx - 9 * sc, ly - 6 * sc, lx + 9 * sc, ly + 8 * sc), 2 * sc, fill=mix((236, 196, 92), la), outline=lc, width=max(1, int(1.5 * sc)))
    if xmark > 0:
        r = 14 * sc; xc = (x + w * 0.9, y - h * 0.9)
        p.ell((xc[0] - r, xc[1] - r, xc[0] + r, xc[1] + r), fill=mix(RED, xmark))
        p.line([(xc[0] - r * 0.45, xc[1] - r * 0.45), (xc[0] + r * 0.45, xc[1] + r * 0.45)], mix(WHITE, xmark), 3 * sc)
        p.line([(xc[0] - r * 0.45, xc[1] + r * 0.45), (xc[0] + r * 0.45, xc[1] - r * 0.45)], mix(WHITE, xmark), 3 * sc)


def key(p, c, col, a=1.0, sc=1.0, teeth=(1, 0, 1)):
    x, y = c
    p.ell((x - 14 * sc, y - 14 * sc, x + 14 * sc, y + 14 * sc), outline=mix(col, a), width=max(2, int(5 * sc)))
    p.line([(x + 14 * sc, y), (x + 54 * sc, y)], mix(col, a), 5 * sc)
    for k, tl in enumerate(teeth):
        if tl: p.line([(x + (34 + 9 * k) * sc, y), (x + (34 + 9 * k) * sc, y + 11 * sc)], mix(col, a), 5 * sc)


# ---------------------------------------------------------------- 時刻（本編の秒。ナレーションの文の始まり）
K = dict(intro_a=165.15, intro_b=166.49, wave_a=168.90, reach_b=175.40, wave_b=178.65, worry=187.73, butnot=192.32,
         marks=199.13, mine=204.48, notmine=209.45, nb_same=217.95, here=220.44, there=221.97, each=223.50,
         idinfo=233.59, pairing=244.80, prep=247.67, lock=252.83, end=260.20)
# v7：印は文に合わせて一つずつ。台本 v2 の 43「ここでは、自分の組に丸印、隣の組に三角印を付けてみます。」の字の位置（元の時刻。この文は変えていないので v1 と同じ）
#   「自分の組に」で自分の組を光らせ →「丸印」で○ →「隣の組に」で隣の組を光らせ →「三角印」で△
K.update(hl_a=200.07, mark_o=200.96, hl_b=201.58, mark_t=202.31)
MARK_AT = {"A": K["mark_o"], "B": K["mark_t"]}
V_WAVE = 260.0; LAM = 150.0                     # 波面の進む速さ（画面の点/秒）と間隔


# 荷物の予定：(組, 出す組のスマホ, 届けるイヤホンの組, 出発, 着く, 確かめる, 結果, 鍵)
def flights():
    F = []
    F.append(("A", "A", 187.95, 190.10, 205.10, "ok", 0))          # 自分の荷物と隣の荷物が、自分のイヤホンに届く（D4）→ D5 で確かめる
    F.append(("B", "A", 188.35, 190.55, 210.05, "ng", 0))
    for k, t0 in enumerate((212.6, 215.2)):                         # 鳴らし続ける（自分の組）
        F.append(("A", "A", t0, t0 + 1.6, t0 + 1.9, "ok", 0))
    F.append(("B", "B", 217.95, 219.55, 219.85, "ok", 0))          # 隣のイヤホンも同じ（D6）
    F.append(("A", "B", 218.35, 220.15, 220.50, "ng", 0))
    for k, t0 in enumerate((224.0, 226.6, 229.2)):                  # それぞれ、つないだ相手と（流れ続ける。ときどき向こうの荷物も届くが、取らない）
        F.append(("A", "A", t0, t0 + 1.6, t0 + 1.9, "ok", 0)); F.append(("B", "B", t0 + 0.7, t0 + 2.3, t0 + 2.6, "ok", 0))
    F.append(("B", "A", 227.4, 229.2, 229.5, "ng", 0)); F.append(("A", "B", 230.0, 231.8, 232.1, "ng", 0))
    for t0 in (236.0, 239.4):                                        # 見分ける情報の帯（D7 の前半）
        F.append(("A", "A", t0, t0 + 1.6, t0 + 1.9, "ok", 0)); F.append(("B", "B", t0 + 0.8, t0 + 2.4, t0 + 2.7, "ok", 0))
    F.append(("A", "A", 257.55, 259.05, 259.35, "unlock", 1))       # 鍵をかけた荷物：自分のイヤホンは開けられる
    F.append(("A", "B", 257.55, 259.30, 259.70, "locked", 1))       # 同じ電波は隣のイヤホンにも届くが、鍵が合わない
    return F


FL = flights()


def route(src, dst, u):
    """スマホ（src の組）から受付口（dst の組）へ：ゆるい弧"""
    x0, y0 = PX + 80, PAIR[src]["y"]; x1, y1 = SLOT(PAIR[dst]["y"]); x1 -= 62
    s = sm(u); x = x0 + (x1 - x0) * s; y = y0 + (y1 - y0) * s - math.sin(math.pi * s) * (40 if src == dst else 0)
    return x, y


def parcel_state(f, t):
    """荷物の位置・大きさ・濃さ（見えない時は None）と確かめた結果の表示"""
    src, dst, ta, tb, tc, res, lk = f
    if t < ta - 0.05: return None
    col = PAIR[src]["col"]
    if t < tb: x, y = route(src, dst, (t - ta) / (tb - ta)); return dict(c=(x, y), sc=1.2, a=sm((t - ta) / 0.25), col=col, x=0.0, lo=0.0)
    sx, sy = SLOT(PAIR[dst]["y"]); wait = (sx - 62, sy)
    q = sum(1 for g in FL if g[1] == dst and g[3] < tb and g[4] > t and g is not f and g[3] <= f[3]) if res in ("ok", "ng") else 0
    wait = (wait[0] - 78 * min(q, 2) * (1 if t < tc else 0), wait[1])
    if t < tc: return dict(c=wait, sc=1.2, a=1.0, col=col, x=0.0, lo=0.0)
    u = (t - tc)
    if res in ("ok", "unlock"):
        d0 = 0.0 if res == "ok" else 0.7                             # 鍵を開けてから入る
        lo = sm(u / 0.45) if res == "unlock" else 0.0
        v = sm((u - d0) / 0.5)
        if v >= 1.0: return None
        return dict(c=(wait[0] + 62 * v, wait[1]), sc=1.2 - 0.8 * v, a=1.0 - 0.8 * sm((u - d0 - 0.3) / 0.2), col=col, x=0.0, lo=lo)
    # 取らない：少し震えて、✕、下へ落ちて消える
    sh = math.sin(u * 2 * math.pi * 7) * 5 * (1 - sm(u / 0.5)) if u < 0.5 else 0.0
    dr = sm((u - 0.9) / 0.7)
    if dr >= 1.0: return None
    return dict(c=(wait[0] + sh, wait[1] + 50 * dr), sc=1.2, a=1.0 - dr, col=col, x=sm((u - 0.15) / 0.2) * (1 - dr), lo=0.0)


def lamp_state(dst, t):
    """受付の灯：取り込むと緑（0.8秒）、取らないと赤（0.6秒）。ふだんは灰"""
    lamp = (176, 182, 188)
    for f in FL:
        if f[1] != dst: continue
        u = t - f[4]
        if f[5] in ("ok", "unlock") and 0 <= u - (0.7 if f[5] == "unlock" else 0.0) < 0.9: lamp = GREEN
        if f[5] in ("ng", "locked") and 0.1 <= u < 0.8: lamp = RED
    return lamp


def playing(dst, t):
    """そのイヤホンが鳴っている強さ（取り込んだ荷物のあと 2.6秒）"""
    v = 0.0
    for f in FL:
        if f[1] == dst and f[5] in ("ok", "unlock"):
            u = t - f[4] - (0.7 if f[5] == "unlock" else 0.0)
            if u >= 0.2: v = max(v, 1.0 - sm((u - 2.3) / 0.6))
    return v


def events():
    """効果音の時刻：荷物が着く（tick）・取り込む（ding）・取らない（bonk）・鍵（clink）・開く（click）"""
    ev = []
    for f in FL:
        ev.append(dict(kind="arrive", t=f[3])); r = f[5]
        if r == "ok": ev.append(dict(kind="accept", t=f[4]))
        elif r == "unlock": ev += [dict(kind="unlock", t=f[4]), dict(kind="accept", t=f[4] + 0.7)]
        else: ev.append(dict(kind="reject", t=f[4] + 0.1))
    ev += [dict(kind="pop", t=PI["card"] + 0.05), dict(kind="tap", t=PI["tap"]), dict(kind="pair", t=PI["done"]), dict(kind="whoosh", t=PI["go"])]
    for (ta, xa), (tb, xb) in ([] if True else zip(ROBOT_PATH, ROBOT_PATH[1:])):   # v4：2D の絵の具の場面はやめた（足音もなし）
        if abs(xb - xa) < 1: continue
        n = int(abs(xb - xa) / 44)
        for k in range(1, n + 1):
            u = k * 44 / abs(xb - xa)                                           # 進んだ割合 → 時刻（躍度最小の逆）
            lo, hi = 0.0, 1.0
            for _ in range(30):
                m = (lo + hi) / 2
                if sm(m) < u: lo = m
                else: hi = m
            ev.append(dict(kind="step", t=ta + (tb - ta) * lo))
    for k in ("intro_a", "intro_b"): ev.append(dict(kind="pop", t=K[k]))
    ev += [dict(kind="stamp", t=MARK_AT["A"]), dict(kind="stamp", t=MARK_AT["B"])]   # v7：印ひとつに一回（前は 0.25 秒おきに 4 回で、速すぎた）
    return sorted(ev, key=lambda e: e["t"])


# ---------------------------------------------------------------- D7 ペアリング：絵の具を混ぜて、同じ色の鍵を作る（鍵そのものは送らない）
#   スマホとイヤホンは、それぞれ「ひみつの色」を持つ。みんなが知っている色（黄）にひみつの色を混ぜたバケツだけを、まるロボが運んで交換する。
#   受け取った側が自分のひみつの色を足すと、両方とも同じ色（茶）になり、それが鍵になる。運ばれるバケツが見えても、隣では同じ色を作れない
#   （本物の仕組み：楕円曲線の Diffie–Hellman 鍵共有。公開の値だけを交換し、鍵は両方で計算する）
YEL = (240, 198, 56); BLU = (52, 102, 210); RED_S = (204, 58, 118); GRN = (86, 160, 108); CORAL = (236, 112, 110); BRN = (128, 90, 66)
PK = dict(robot=245.30, secrets=247.90, common=248.50, split=249.50, mix1=250.60, go=252.00, pick1=252.55, carry1=252.75, swap=253.95,
          carry2=254.30, drop2=255.50, back=255.75, mix2=255.85, keys=256.75, recap=260.45)
XS_P, XS_E = PX + 150, EX - 150                  # まるロボが止まる所（スマホの側・イヤホンの側）
B_P, B_E = (XS_P - 60, TOP + 98), (XS_E + 60, TOP + 98)   # バケツを置く所
Y_FLOOR = TOP + 118; X_MID = (PX + EX) / 2
POT_P, POT_E, COMMON = (PX + 120, TOP - 95), (EX - 120, TOP - 95), (X_MID, TOP - 95)


def lerp(a, b, u): return a + (b - a) * u
def mixc(c1, c2, u): return tuple(int(c1[i] + (c2[i] - c1[i]) * max(0.0, min(1.0, u))) for i in range(3))


def bucket(p, c, col, a=1.0, sc=1.0):
    x, y = c; g = (120, 128, 138)
    p.poly([(x - 22 * sc, y - 18 * sc), (x + 22 * sc, y - 18 * sc), (x + 17 * sc, y + 20 * sc), (x - 17 * sc, y + 20 * sc)], fill=mix((235, 238, 240), a), outline=mix(g, a), width=2)
    p.ell((x - 22 * sc, y - 24 * sc, x + 22 * sc, y - 12 * sc), fill=mix(col, a), outline=mix(g, a), width=2)     # 中の絵の具
    p.arc((x, y - 20 * sc), 24 * sc, 200, 340, mix(g, a), 2)                                                   # 取っ手


def pot(p, c, col, a=1.0):
    x, y = c
    p.rr((x - 16, y - 18, x + 16, y + 20), 6, fill=mix(col, a), outline=mix((90, 96, 104), a), width=2)
    p.rr((x - 10, y - 26, x + 10, y - 18), 3, fill=mix((90, 96, 104), a))


def robot(p, x, y, a=1.0, squash=0.0, look=0.0):
    """平たいまるロボ（第3章と同じ姿）：白い丸い体・大きな青緑のレンズの目・アンテナ（だいだいの玉）・黒い足。y＝足もと"""
    sy = 1.0 - 0.12 * squash; sx_ = 1.0 + 0.08 * squash; cy = y - 34 * sy
    p.rr((x - 22, y - 8, x - 6, y + 2), 4, fill=mix((40, 44, 50), a)); p.rr((x + 6, y - 8, x + 22, y + 2), 4, fill=mix((40, 44, 50), a))
    p.ell((x - 32 * sx_, cy - 32 * sy, x + 32 * sx_, cy + 32 * sy), fill=mix(WHITE, a), outline=mix((190, 196, 202), a), width=2)
    ex = x + 8 * look
    p.ell((ex - 13, cy - 13, ex + 13, cy + 13), fill=mix((28, 70, 80), a), outline=mix(CYAN, a), width=4)
    p.ell((ex - 4 + 3 * look, cy - 7, ex + 4 + 3 * look, cy + 1), fill=mix((220, 245, 245), a))
    p.line([(x + 10, cy - 30 * sy), (x + 18, cy - 50 * sy)], mix((120, 128, 138), a), 3)
    p.ell((x + 13, cy - 57 * sy, x + 23, cy - 47 * sy), fill=mix((240, 150, 60), a))


ROBOT_PATH = [(PK["robot"], X_MID), (PK["go"], X_MID), (PK["pick1"], XS_P), (PK["carry1"], XS_P), (PK["swap"], XS_E), (PK["carry2"], XS_E),
              (PK["drop2"], XS_P), (PK["back"], XS_P), (PK["back"] + 0.7, X_MID)]


def robot_state(t):
    """まるロボの位置（x）・跳ねる高さ・つぶれ。歩く区間は躍度最小、歩幅 44点ごとに小さく跳ねる"""
    if t < PK["robot"]: return None
    for (ta, xa), (tb, xb) in zip(ROBOT_PATH, ROBOT_PATH[1:]):
        if ta <= t < tb:
            if abs(xb - xa) < 1: return X_MID if False else xa, 0.0, 0.0, 0.0
            u = sm((t - ta) / (tb - ta)); x = lerp(xa, xb, u); dist = abs(x - xa)
            ph = math.sin(math.pi * dist / 44.0); hop = 12 * abs(ph); sq = max(0.0, 1 - abs(ph) * 5) * (1 if 0.02 < u < 0.98 else 0)
            return x, hop, sq, (1.0 if xb > xa else -1.0)
    return ROBOT_PATH[-1][1], 0.0, 0.0, 0.0


def drop(p, a_, b_, u, col):
    """ひみつの色をひとしずく（放物線で落ちる）"""
    if not (0 <= u < 1): return
    x = lerp(a_[0], b_[0], u); y = lerp(a_[1], b_[1], u) - 60 * math.sin(math.pi * u); p.ell((x - 7, y - 9, x + 7, y + 7), fill=col)


def pairing_scene(p, t):
    if t < PK["robot"] - 0.1: return
    end = 1.0 - sm((t - 264.2) / 0.2)
    # ひみつの色・みんなが知っている色
    sa = sm((t - PK["secrets"]) / 0.4) * (1 - sm((t - PK["keys"] - 0.2) / 0.5))
    if sa > 0:
        pot(p, POT_P, BLU, sa); pot(p, POT_E, RED_S, sa)
        p.text((POT_P[0], POT_P[1] - 48), "ひみつの色", 28, mix(INK, sa)); p.text((POT_E[0], POT_E[1] - 48), "ひみつの色", 28, mix(INK, sa))
    ca = sm((t - PK["common"]) / 0.4) * (1 - sm((t - PK["split"] - 0.9) / 0.4))
    if ca > 0:
        bucket(p, COMMON, YEL, ca); p.text((COMMON[0], COMMON[1] - 48), "みんなが知っている色", 28, mix(INK, ca))
    # バケツ：黄を両側へ → ひみつの色を混ぜる → まるロボが交換 → もう一度ひみつの色 → 同じ色（茶）→ 鍵
    us = sm((t - PK["split"]) / 0.8)
    if t >= PK["split"] and t < PK["keys"] + 0.45:
        m1p = sm((t - PK["mix1"] - 0.5) / 0.4); m1e = sm((t - PK["mix1"] - 0.6) / 0.4)
        col_p = mixc(YEL, GRN, m1p); col_e = mixc(YEL, CORAL, m1e)               # スマホの側（緑）・イヤホンの側（さんご色）
        m2p = sm((t - PK["mix2"] - 0.5) / 0.4); m2e = sm((t - PK["mix2"] - 0.6) / 0.4)
        ks = 1.0 - sm((t - PK["keys"]) / 0.4)
        rs = robot_state(t); rx = rs[0] if rs else X_MID; ry = Y_FLOOR - (rs[1] if rs else 0.0)
        head = (rx, ry - 34 - 32 - 22)
        # 緑のバケツ：スマホの側 → まるロボの頭の上 → イヤホンの側
        if t < PK["pick1"] + 0.0: gp = (lerp(COMMON[0], B_P[0], us), lerp(COMMON[1], B_P[1], us))
        elif t < PK["swap"]: gp = (lerp(B_P[0], head[0], sm((t - PK["pick1"]) / 0.2)), lerp(B_P[1], head[1], sm((t - PK["pick1"]) / 0.2)))
        else: gp = (lerp(head[0], B_E[0], sm((t - PK["swap"]) / 0.2)) if t < PK["swap"] + 0.2 else B_E[0], lerp(head[1], B_E[1], sm((t - PK["swap"]) / 0.2)))
        # さんご色のバケツ：イヤホンの側 → まるロボの頭の上 → スマホの側
        if t < PK["swap"] + 0.15: cp = (lerp(COMMON[0], B_E[0], us), lerp(COMMON[1], B_E[1], us))
        elif t < PK["drop2"]: cp = (lerp(B_E[0], head[0], sm((t - PK["swap"] - 0.15) / 0.2)), lerp(B_E[1], head[1], sm((t - PK["swap"] - 0.15) / 0.2)))
        else: cp = (lerp(head[0], B_P[0], sm((t - PK["drop2"]) / 0.2)), lerp(head[1], B_P[1], sm((t - PK["drop2"]) / 0.2)))
        c_green = mixc(col_p, BRN, m2e) if t >= PK["swap"] else col_p                 # 緑はイヤホンの側で赤を足されて茶に
        c_coral = mixc(col_e, BRN, m2p) if t >= PK["drop2"] else col_e                # さんご色はスマホの側で青を足されて茶に
        if ks > 0.02:
            bucket(p, gp, c_green, 1.0, ks); bucket(p, cp, c_coral, 1.0, ks)
        drop(p, POT_P, B_P, (t - PK["mix1"]) / 0.55, BLU); drop(p, POT_E, B_E, (t - PK["mix1"] - 0.1) / 0.55, RED_S)
        drop(p, POT_P, B_P, (t - PK["mix2"]) / 0.55, BLU); drop(p, POT_E, B_E, (t - PK["mix2"] - 0.1) / 0.55, RED_S)
    # 同じ色の鍵 → 二台のそばへ
    kk = sm((t - PK["keys"]) / 0.4)
    if kk > 0:
        mv = sm((t - PK["keys"] - 0.45) / 0.55)
        for b0, tgt in ((B_P, (PX + 58, TOP - 122)), (B_E, (EX + 46, TOP - 122))):
            c = (lerp(b0[0] - 30, tgt[0], mv), lerp(b0[1], tgt[1], mv)); key(p, c, BRN, kk * end, 1.25)
        ck = win(t, PK["keys"] + 0.3, 258.55, 0.3, 0.3); ck2 = win(t, 258.7, PK["recap"] - 0.1, 0.3, 0.3)
        if ck2 > 0: p.text((X_MID, TOP - 118), "次からは自動でつながる", 32, mix(BRN, ck2))
    # 隣：運ばれるバケツは見えても、同じ色は作れない
    nb = win(t, 254.3, 257.3, 0.35, 0.35)
    if nb > 0:
        p.text((EX + 96, BOT - 84), "？", 60, mix(AMBER, nb))
    key(p, (EX + 46, BOT - 122), AMBER, sm((t - 257.4) / 0.6) * end, 1.1, teeth=(0, 1, 1))          # 隣のイヤホンの鍵（形が違う）
    # まるロボ
    rs = robot_state(t)
    if rs:
        x, hop, sq, dirn = rs; ra = sm((t - PK["robot"]) / 0.35) * end
        robot(p, x, Y_FLOOR - hop, ra, sq, dirn if abs(dirn) > 0 else 0.0)
    # 「鍵そのものは、電波で送っていません」：運んだのは混ぜた色だけ
    rc = 0.0                                                          # 2026-11-09：まとめのカード（運んだのは混ぜた色だけ／鍵は二台がそれぞれ作る）は字幕と同じ意味なのでやめた
    if rc > 0:
        cx, cy = 670, 372
        p.rr((cx - 280, cy - 82, cx + 280, cy + 82), 20, fill=mix(WHITE, rc), outline=mix((205, 210, 215), rc), width=2)
        bucket(p, (cx - 222, cy - 30), GRN, rc, 0.8); bucket(p, (cx - 178, cy - 30), CORAL, rc, 0.8)
        p.text((cx + 52, cy - 34), "運んだのは、混ぜた色だけ", 32, mix(INK, rc))
        key(p, (cx - 238, cy + 34), BRN, rc, 0.9)
        p.text((cx + 52, cy + 34), "鍵は、二台がそれぞれ作る", 32, mix(BRN, rc))


# ---------------------------------------------------------------- D7 ペアリング（v4）：よく見るペアリングの画面 → 中では？ → 3D（ch04_pairing.py）
#   図の並び（左にスマホ、右にイヤホン）のまま、二台が 3D の最初のコマの巨大スマホ・巨大イヤホンの所・大きさへ寄って、3D に変わる
PI = dict(t0=244.62, settle=245.15, card=244.95, tap=245.75, busy=245.85, done=246.55, out=246.95, go=247.00, t3d=247.60)
MATCH = None                                                               # 3D の最初のコマの、巨大スマホ・巨大イヤホンの画面の上の箱（0〜1）


def intro_pose(t):
    """（スマホの中心・大きさ、イヤホンの中心・大きさ）。大きさは DS に掛ける"""
    if V6: return intro_pose_v6(t)
    u1 = sm((t - PI["t0"]) / (PI["settle"] - PI["t0"]))
    ph = (PX + (330 - PX) * u1, TOP + (372 - TOP) * u1, 1.0 + 0.30 * u1)
    eb = (EX + (950 - EX) * u1, TOP + (372 - TOP) * u1, 1.0 + 0.30 * u1)
    if MATCH:
        u2 = sm((t - PI["go"]) / (PI["t3d"] - PI["go"]))
        if u2 > 0:
            bp, be = MATCH["P"], MATCH["E"]
            scp = (bp[3] - bp[1]) * H / (152 * DS); scp_xy = ((bp[0] + bp[2]) / 2 * W, (bp[1] + bp[3]) / 2 * H)
            sce = (be[3] - be[1]) * H / (140 * DS); sce_xy = ((be[0] + be[2]) / 2 * W + 12 * DS * sce, (be[1] + be[3]) / 2 * H - 16 * DS * sce)
            ph = (ph[0] + (scp_xy[0] - ph[0]) * u2, ph[1] + (scp_xy[1] - ph[1]) * u2, ph[2] + (scp - ph[2]) * u2)
            eb = (eb[0] + (sce_xy[0] - eb[0]) * u2, eb[1] + (sce_xy[1] - eb[1]) * u2, eb[2] + (sce - eb[2]) * u2)
    return ph, eb


def tagbox(p, xy, txt, col, a, px=30):
    if a <= 0.02: return
    w_ = len(txt) * px * 0.98 + 30
    p.rr((xy[0] - w_ / 2, xy[1] - px * 0.75, xy[0] + w_ / 2, xy[1] + px * 0.75), 12, fill=mix(WHITE, a), outline=mix(col, a), width=3)
    p.text(xy, txt, px, mix(col, a))


def pairing_intro(p, t):
    """よく見るペアリングの画面（真ん中のカード）・二台の名札・電波の小さな輪"""
    if t < PI["t0"]: return
    (px_, py_, sp), (ex_, ey_, se) = intro_pose(t)
    tg = sm((t - PI["card"]) / 0.35)
    # 名札（物の上）：スマホ・イヤホン
    tagbox(p, (px_, py_ - 76 * DS * sp - 34), "スマホ", TEAL, tg)
    tagbox(p, (ex_ - 12 * DS * se, ey_ - 54 * DS * se - 34), "イヤホン", TEAL, tg)
    # 電波の小さな輪（接続中）：スマホからイヤホンへ
    busy = win(t, PI["busy"], PI["done"] + 0.2, 0.15, 0.3)
    if busy > 0:
        for k in range(3):
            ph_ = ((t - PI["busy"]) * 1.6 - k * 0.33) % 1.0
            r = 40 + 60 * ph_; p.arc((px_ + 46 * DS * sp, py_ - 10), r, -35, 35, mix(TEAL, busy * (1 - ph_)), 5)
    # カード
    ca = win(t, PI["card"], PI["out"], 0.35, 0.3)
    if ca <= 0.01: return
    cx, cy = 640, 360 + 26 * (1 - sm((t - PI["card"]) / 0.35)); w2, h2 = 190, 160
    p.rr((cx - w2 + 4, cy - h2 + 8, cx + w2 + 4, cy + h2 + 8), 26, fill=mix((215, 220, 226), ca))         # 影
    p.rr((cx - w2, cy - h2, cx + w2, cy + h2), 26, fill=mix(WHITE, ca), outline=mix((205, 210, 215), ca), width=2)
    p.text((cx, cy - h2 + 36), "Bluetooth", 24, mix(GRAY, ca), bold=False)
    for dx in (-34, 34):                                                   # 左右のイヤホン（小さく）
        earbud(p, cx + dx + 8, cy - 62, (205, 212, 218), (205, 212, 218), ca, ds=0.62)
    p.text((cx, cy + 22), "ワイヤレスイヤホン", 28, mix(INK, ca))
    bx0, bx1, by0, by1 = cx - 130, cx + 130, cy + 66, cy + 124
    done = sm((t - PI["done"]) / 0.2)
    bcol = tuple(int(TEAL[i] + (GREEN[i] - TEAL[i]) * done) for i in range(3))
    press = win(t, PI["tap"], PI["tap"] + 0.12, 0.05, 0.1)
    p.rr((bx0 + 4 * press, by0 + 3 * press, bx1 - 4 * press, by1 - 3 * press), 18, fill=mix(bcol, ca))
    if t < PI["busy"]: p.text((cx, (by0 + by1) / 2), "ペアリング", 30, mix(WHITE, ca))
    elif t < PI["done"]:
        dots = "・" * (1 + int((t - PI["busy"]) * 4) % 3)
        p.text((cx - 10, (by0 + by1) / 2), "接続中" + dots, 28, mix(WHITE, ca))
        a0 = (t - PI["busy"]) * 540; p.arc((bx0 + 36, (by0 + by1) / 2), 12, a0, a0 + 270, mix(WHITE, ca), 4)
    else: p.text((cx, (by0 + by1) / 2), "接続しました ✓", 28, mix(WHITE, ca))
    # 指（押す）：丸い影と広がる輪
    u = t - PI["tap"]
    if -0.35 < u < 0.6:
        fa = ca * win(t, PI["tap"] - 0.35, PI["tap"] + 0.3, 0.2, 0.25)
        fx, fy = cx + 40, (by0 + by1) / 2 + 6
        p.ell((fx - 20, fy - 20, fx + 20, fy + 20), fill=mix((150, 160, 170), 0.55 * fa))
        if u > 0:
            r = 22 + 70 * min(u / 0.45, 1.0); p.ell((fx - r, fy - r, fx + r, fy + r), outline=mix(TEAL, ca * (1 - min(u / 0.45, 1.0))), width=4)


def pop_scale(u):
    """弾んで出る大きさ：0 → 1.13（0.2秒）→ 1 に落ち着く（減衰する振動）"""
    if u <= 0: return 0.0
    return 1.0 - math.exp(-u / 0.10) * math.cos(2 * math.pi * u / 0.40)


def sticker(p, c, kind, r, col, a, sc=1.0, burst=1.0):
    """印のシール：白い丸に色の○／△。burst（0〜1）の間、まわりに輪が広がって消える"""
    if sc <= 0.02 or a <= 0.01: return
    R = (r + 13) * sc
    if 0 <= burst < 1:
        rb = (r + 13) * (1.0 + 0.9 * burst); p.ell((c[0] - rb, c[1] - rb, c[0] + rb, c[1] + rb), outline=mix(col, a * 0.6 * (1 - burst)), width=4)
    p.ell((c[0] - R, c[1] - R, c[0] + R, c[1] + R), fill=mix(WHITE, a), outline=mix((196, 203, 210), a), width=2)
    mark(p, (c[0], c[1] + (0.2 * r * sc if kind == "t" else 0.0)), kind, r * sc, mix(col, a), max(2, 7 * sc))


# ---------------------------------------------------------------- 1コマ
def frame(t):
    im = Image.new("RGB", (W * S, H * S), BG); p = Pen(ImageDraw.Draw(im))
    intro = {"A": sm((t - K["intro_a"]) / 0.45), "B": sm((t - K["intro_b"]) / 0.45)}
    mark_fade = 1 - sm((t - K["idinfo"] - 1.2) / 1.2)
    mark_a = {k_: sm((t - MARK_AT[k_]) / 0.10) * mark_fade for k_ in ("A", "B")}             # v7：組ごとに、文に合わせて出る
    mark_sc = {k_: pop_scale(t - MARK_AT[k_]) for k_ in ("A", "B")}
    band_on = sm((t - K["idinfo"] - 2.0) / 1.0)
    pair_glow = {"A": win(t, K["here"], K["there"] - 0.1, 0.25, 0.4) + 0.6 * win(t, K["each"], K["idinfo"] - 0.5, 0.4, 0.5),
                 "B": win(t, K["there"], K["each"] - 0.1, 0.25, 0.4) + 0.6 * win(t, K["each"], K["idinfo"] - 0.5, 0.4, 0.5)}
    pair_glow["A"] += win(t, K["hl_a"], K["mark_o"] + 1.0, 0.25, 0.45)                      # v7：印を付ける組を、先に光らせる
    pair_glow["B"] += win(t, K["hl_b"], K["mark_t"] + 1.0, 0.25, 0.45)
    # 組の背景の光（こちらはこちら・あちらはあちら）
    for k_, pr in PAIR.items():
        g = min(pair_glow[k_], 1.0)
        if g > 0.01: p.rr((36, pr["y"] - 118, EX + 96, pr["y"] + 132), 26, fill=mix(pr["col"], 0.10 * g))
    # 電波（同心円）：スマホからまわり一面に。光らない輪
    for k_, t_on in (("A", K["wave_a"]), ("B", K["wave_b"])):
        if t < t_on: continue
        dim = 1.0 - 0.7 * sm((t - K["worry"]) / 1.0) - 0.3 * sm((t - K["marks"]) / 1.0)
        cx, cy = PX, PAIR[k_]["y"]; age = t - t_on
        rmax = min(V_WAVE * age, 1500)
        n0 = int((V_WAVE * age) // LAM)
        for n in range(n0, max(-1, n0 - 10), -1):
            r = V_WAVE * age - n * LAM
            if r <= 30 or r > rmax: continue
            a = dim * 0.45 * math.exp(-r / 750.0) * sm(age / 0.4)
            if a < 0.004: continue                                   # v7：消えた輪は描かない（背景色の輪が、組の光の上に白い線で見えていた）
            p.arc((cx, cy), r, 0, 360, mix(PAIR[k_]["col"], a), 3)
    # 届いたことの印（D3：隣のイヤホンにも届く・反対に隣の電波もこちらへ）
    for (dst, t_hit, col) in (("B", K["reach_b"], TEAL), ("A", K["wave_b"] + 3.3, AMBER)):
        u = t - t_hit
        if 0 <= u < 2.6:
            ex, ey = EX - 8, PAIR[dst]["y"] - 25
            for k in range(3):
                ph = (u * 1.1 - k * 0.3)
                if 0 <= ph < 1: p.ell((ex - 64 - 46 * ph, ey - 64 - 46 * ph, ex + 64 + 46 * ph, ey + 64 + 46 * ph), outline=mix(col, (1 - ph) * 0.8), width=5)
    # 組：スマホ・イヤホン・名前・印
    fade_b = 1 - sm((t - PI["t0"] + 0.22) / 0.30); name_a = 1 - sm((t - PI["t0"] + 0.22) / 0.30)   # 隣の組は、自分の組が動き出す前に消える
    for k_, pr in PAIR.items():
        a = intro[k_] * (fade_b if k_ == "B" else 1.0)
        if a <= 0.005: continue
        y = pr["y"] + 18 * (1 - a)
        if k_ == "A" and t >= PI["t0"]:                                   # よく見るペアリングの画面の間（スマホとイヤホンが寄って、大きくなる）
            (px_, py_, sp), (ex_, ey_, se) = intro_pose(t)
            busy = win(t, PI["busy"], PI["done"], 0.05, 0.05); blink = 0.5 + 0.5 * math.cos((t - PI["busy"]) * 2 * math.pi * 3.0)
            lamp = mix(TEAL, busy * blink, bg=(205, 212, 218)) if t < PI["done"] else mix(GREEN, sm((t - PI["done"]) / 0.15), bg=(205, 212, 218))
            phone(p, px_, py_, pr["scr"], a, ds=DS * sp)
            earbud(p, ex_, ey_, pr["col"], lamp, a, ds=DS * se)
            continue
        phone(p, PX, y, pr["scr"], a)
        earbud(p, EX, y, pr["col"], mix(lamp_state(k_, t), a), a, glow=min(pair_glow[k_], 1.0))
        p.text((52, y), pr["name"], 38, mix(pr["col"], a * name_a), anchor="lm")
        if mark_a[k_] > 0:                                                                       # v7：大きな印のシール（受付口の右・スマホの右下）
            u_m = t - MARK_AT[k_]
            for cxy in ((EX + 84, y + 52), (PX + 102, y + 60)):
                sticker(p, cxy, pr["mark"], 24, pr["col"], mark_a[k_] * a, mark_sc[k_], burst=u_m / 0.6)
        # 鳴っている：音の輪（耳の先から）
        pl = playing(k_, t)
        if pl > 0:
            tx, ty = TIP(y)
            for k in range(3):
                ph = ((t * 1.3) - k * 0.33) % 1.0
                r = 22 + 56 * ph; p.arc((tx, ty), r, 140, 230, mix(pr["col"], (1 - ph) * pl), 5)
    # 「？」（隣の曲まで聞こえる？）→ 受付口で確かめる
    wq = win(t, K["worry"] + 2.6, K["butnot"] + 0.4, 0.3, 0.3)
    if wq > 0: p.text((EX + 96, TOP - 84), "？", 66, mix(INK, wq))
    ck = win(t, K["butnot"] + 0.6, K["marks"] + 0.5, 0.3, 0.4)
    if ck > 0:
        sx, sy = SLOT(TOP); p.rr((sx + 30, sy - 28, sx + 196, sy + 28), 12, fill=mix(WHITE, ck), outline=mix(TEAL, ck), width=3)
        p.text((sx + 113, sy), "確かめる", 32, mix(TEAL, ck))
    # 荷物
    for f in FL:
        st = parcel_state(f, t)
        if st is None: continue
        src = f[0]; lk = f[6]
        ma = mark_a.get(src, 0.0)
        lock_on = 1.0 if lk else 0.0
        parcel(p, st["c"], st["col"], st["sc"], st["a"], mk=PAIR[src]["mark"], mk_a=ma * (1 - band_on), band=band_on, band_col=PAIR[src]["col"],
               lock=lock_on, lock_open=st["lo"], xmark=st["x"], mk_sc=mark_sc.get(src, 1.0))
    # D7：見分ける情報（大きく見せる）
    zi = win(t, K["idinfo"] + 2.3, K["pairing"] - 0.4, 0.5, 0.5)
    if zi > 0:
        cx, cy = 690, 335
        p.rr((cx - 270, cy - 105, cx + 270, cy + 105), 20, fill=mix(WHITE, zi), outline=mix((205, 210, 215), zi), width=2)
        parcel(p, (cx - 150, cy + 10), TEAL, 2.0, zi, band=1.0, band_col=TEAL)
        p.text((cx + 105, cy - 28), "どの通信かを", 36, mix(INK, zi)); p.text((cx + 105, cy + 22), "見分ける情報", 36, mix(INK, zi))
        p.line([(cx - 150 - 60, cy + 10 - 53), (cx - 20, cy - 52)], mix(TEAL, zi * 0.8), 3)
    # D7：ペアリング（自分の組を点線でつなぐ）→ 同じ鍵を二台が持つ
    pg = 0.0                                                               # v4：点線の「ペアリング」はやめ、よく見るペアリングの画面にした
    if pg > 0:
        x0, x1 = PX + 64, EX - 86; y = TOP
        n = int((x1 - x0) / 22)
        for k in range(n):
            if k / n > sm((t - K["pairing"]) / 0.6): break
            if k % 2 == 0: p.line([(x0 + k * 22, y), (x0 + k * 22 + 12, y)], mix(TEAL, pg), 4)
        p.text(((x0 + x1) / 2, y - 34), "ペアリング", 36, mix(TEAL, pg))
    pairing_intro(p, t)
    im = im.resize(OUT_WH, Image.LANCZOS)
    return im


# ---------------------------------------------------------------- v6（台本 v2、2026-11-06）：新しい時刻で描く
#   図（D2〜D7）は元の時刻の絵を、新しい台本の時刻へずらして流す（足した文の間は止めて待つ：stage/script/timewarp.py）
#   ペアリングの前：よく見るペアリング画面（P1）→ 二台が 3D の台の所へ寄る（P2）。3D のあと：「接続しました ✓」と鍵（P17）→ 鍵のない隣は読めない（足した一文）
sys.path.insert(0, os.path.join(HERE, "..", "script"))
V6 = None


def setup_v6(pair_dir):
    """新しい時刻を読む。PI（ペアリングの画面の時刻）も新しい時刻にする"""
    global V6, MATCH
    import timewarp as tw
    L = json.load(open(pair_dir + "/pairing_log.json"))
    P = {int(k): v for k, v in L["times"]["P"].items()}
    _, t_ch0, _ = tw.find("まずは、一つ目の疑問から"); _, t_d2, _ = tw.find("上が自分の組")
    _, t_br0, t_br1 = tw.find("では、この「つないだ相手」"); _, t_add0, t_add1 = tw.find("隣のイヤホンに届いても")
    _, t_d8, _ = tw.find("電波が届くことと"); _, t_ch1, _ = tw.find("これで、一つ目の疑問")
    V6 = dict(W=tw.Warp(161.0, 244.7), P=P, ch0=t_ch0, d2=t_d2, br=(t_br0, t_br1), add=(t_add0, t_add1), d8=t_d8, ch1=t_ch1, t3d0=L["t0"], t3d1=L["t1"])
    MATCH = L["match"]
    p1a, p1b = P[1]; p2a, p2b = P[2]
    PI.update(t0=p1a - 0.05, settle=p1a + 0.55, card=p1a + 0.35, tap=p1a + 3.55, busy=p1a + 3.65, done=p1a + 4.45, out=p2a + 0.70, go=V6["t3d0"] - 1.6, t3d=V6["t3d0"])
    return V6


def intro_pose_v6(t):
    """v6：最後は 3D の台（寝かせたスマホ・ケース）の真ん中へ小さくなって寄る（形が違うので、大きさは合わせず、重ねて消える）"""
    u1 = sm((t - PI["t0"]) / (PI["settle"] - PI["t0"]))
    ph = [PX + (330 - PX) * u1, TOP + (372 - TOP) * u1, 1.0 + 0.30 * u1]
    eb = [EX + (950 - EX) * u1, TOP + (372 - TOP) * u1, 1.0 + 0.30 * u1]
    u2 = sm((t - PI["go"]) / (PI["t3d"] - PI["go"]))
    if MATCH and u2 > 0:
        for d_, b_ in ((ph, MATCH["P"]), (eb, MATCH["E"])):
            cx_, cy_ = (b_[0] + b_[2]) / 2 * W, (b_[1] + b_[3]) / 2 * H - 40
            d_[0] += (cx_ - d_[0]) * u2; d_[1] += (cy_ - d_[1]) * u2; d_[2] += (0.75 - d_[2]) * u2
    return tuple(ph), tuple(eb)


def padlock(p, c, sc, col, a, opened=0.0):
    """南京錠（色つき）。opened＝0〜1 で掛け金が上がる"""
    x, y = c; lc = mix((70, 76, 84), a)
    p.arc((x, y - 8 * sc - 9 * sc * opened), 8 * sc, 180, 360, fill=lc, width=max(2, int(4 * sc)))
    p.rr((x - 12 * sc, y - 8 * sc, x + 12 * sc, y + 10 * sc), 3 * sc, fill=mix(col, a), outline=lc, width=max(1, int(2 * sc)))
    p.ell((x - 2.5 * sc, y - 1 * sc, x + 2.5 * sc, y + 4 * sc), fill=lc)


LAV = (147, 122, 186); AMB_KEY = (226, 160, 72)


def frame_after(t):
    """3D のあと：「接続しました ✓」と、二台に同じ鍵（P17）→ 鍵をかけた荷物が自分のイヤホンで開く → 隣のイヤホンでは開かない（足した一文）"""
    im = Image.new("RGB", (W * S, H * S), BG); p = Pen(ImageDraw.Draw(im))
    P = V6["P"]; p17a, p17b = P[17]; a0, a1 = V6["add"]
    t_back = a0 - 0.15                                                   # 二段の図へ戻り始める
    ub = sm((t - t_back) / 0.7)                                          # 0：ペアリングの画面の並び、1：二段の図
    # 自分の組：真ん中の高さ（大きい）→ 上の段へ
    px_, py_, sp = 330 + (PX - 330) * ub, 372 + (TOP - 372) * ub, 1.30 + (1.0 - 1.30) * ub
    ex_, ey_, se = 950 + (EX - 950) * ub, 372 + (TOP - 372) * ub, 1.30 + (1.0 - 1.30) * ub
    nb_a = sm((t - t_back - 0.2) / 0.5)                                  # 隣の組が戻る
    if nb_a > 0:
        phone(p, PX, BOT, PAIR["B"]["scr"], nb_a); earbud(p, EX, BOT, PAIR["B"]["col"], mix((205, 212, 218), nb_a), nb_a)
        p.text((52, BOT), PAIR["B"]["name"], 38, mix(PAIR["B"]["col"], nb_a), anchor="lm")
        p.text((52, TOP), PAIR["A"]["name"], 38, mix(PAIR["A"]["col"], nb_a), anchor="lm")
    phone(p, px_, py_, PAIR["A"]["scr"], 1.0, ds=DS * sp)
    open_t = at_char17(11) + 1.25                                         # 荷物が自分のイヤホンに着いて開く
    lamp = mix(GREEN, 1.0, bg=(205, 212, 218))
    earbud(p, ex_, ey_, PAIR["A"]["col"], lamp, 1.0, ds=DS * se)
    # 鍵の印：二台とも同じ紫（P17 の始め）。隣の組は自分たちの鍵（橙）
    ka = sm((t - p17a - 0.25) / 0.35)
    if ka > 0:
        key(p, (px_ - 40 * DS * sp, py_ + 88 * DS * sp), LAV, ka, 0.85 * sp)
        key(p, (ex_ + 30 * DS * se, ey_ + 98 * DS * se), LAV, ka, 0.85 * se)
    if nb_a > 0:
        key(p, (PX - 40 * DS, BOT + 88 * DS), AMB_KEY, nb_a, 0.85); key(p, (EX + 30 * DS, BOT + 98 * DS), AMB_KEY, nb_a, 0.85)
    # 「接続しました ✓」の画面（はじめの 2.6 秒）
    ca = win(t, V6["t3d1"] - 0.2, p17a + 2.4, 0.3, 0.35)
    if ca > 0.01:
        cx, cy = 640, 360; w2, h2 = 190, 110
        p.rr((cx - w2, cy - h2, cx + w2, cy + h2), 26, fill=mix(WHITE, ca), outline=mix((205, 210, 215), ca), width=2)
        p.text((cx, cy - h2 + 34), "Bluetooth", 24, mix(GRAY, ca), bold=False)
        p.text((cx, cy - 6), "ワイヤレスイヤホン", 28, mix(INK, ca))
        p.rr((cx - 130, cy + 30, cx + 130, cy + 86), 18, fill=mix(GREEN, ca)); p.text((cx, cy + 58), "接続しました ✓", 28, mix(WHITE, ca))
    # 鍵をかけた荷物：スマホ → 自分のイヤホン（開く・鳴る）
    t_go1 = at_char17(11); u = (t - t_go1) / 1.2
    if 0 <= u and t < t_back + 0.2:
        s0 = (px_ + 60 * DS * sp, py_ - 20); s1 = (ex_ - 70 * DS * se, ey_ - 10)
        uu = sm(min(u, 1.0)); c = (s0[0] + (s1[0] - s0[0]) * uu, s0[1] + (s1[1] - s0[1]) * uu - 60 * math.sin(math.pi * uu))
        op = sm((t - t_go1 - 1.25) / 0.35); fade = 1 - sm((t - t_go1 - 2.6) / 0.4)
        if fade > 0:
            parcel(p, c, TEAL, 1.6, fade); padlock(p, (c[0] + 34, c[1] + 26), 1.4, LAV, fade, op)
        if op > 0.5:
            tx_, ty_ = TIP(ey_) if se == 1.0 else (ex_ - 47 * DS * se, ey_ - 23 * DS * se)
            for k_ in range(3):
                ph_ = ((t * 1.3) - k_ * 0.33) % 1.0; r = 22 + 56 * ph_; p.arc((tx_, ty_), r, 140, 230, mix(TEAL, (1 - ph_) * fade), 5)
    # 足した一文：鍵をかけた荷物が、隣のイヤホンにも届く → 開かない（×）
    t_go2 = a0 + 0.9; u2 = (t - t_go2) / 1.3
    if u2 >= 0:
        s0 = (PX + 60 * DS, TOP + 10); s1 = (EX - 70 * DS, BOT - 10)
        uu = sm(min(u2, 1.0)); c = (s0[0] + (s1[0] - s0[0]) * uu, s0[1] + (s1[1] - s0[1]) * uu)
        shake = 6 * math.sin(2 * math.pi * 7 * (t - t_go2 - 1.35)) * win(t, t_go2 + 1.35, t_go2 + 1.9, 0.05, 0.15)
        parcel(p, (c[0] + shake, c[1]), TEAL, 1.6, 1.0, xmark=sm((t - t_go2 - 1.55) / 0.3)); padlock(p, (c[0] + 34 + shake, c[1] + 26), 1.4, LAV, 1.0, 0.0)
    im = im.resize(OUT_WH, Image.LANCZOS)
    return im


def at_char17(n):
    a, b = V6["P"][17]; txt = "これでペアリング完成。音楽は、この鍵をかけて送られます。"; return a + (b - a) * n / len(txt)


def frame6(t):
    """v6 の 1コマ（新しい時刻）"""
    if t >= V6["t3d1"] - 0.3: return frame_after(t)
    if t < PI["t0"]:
        to = min(V6["W"].old_of(t), 244.45)                                # 図（元の時刻へ）。ペアリングの画面の前で止めて待つ
        im = frame(to)
        b0, b1 = V6["br"]; qa = win(t, b0 + 0.6, PI["t0"] + 0.3, 0.3, 0.3)
        if qa > 0:                                                         # 「では、この『つないだ相手』は、いつ決まるのでしょう」：自分の組の二台を点線と「？」でつなぐ
            ov = Image.new("RGB", (W * S, H * S), BG); po = Pen(ImageDraw.Draw(ov))
            x0, x1, y = PX + 64, EX - 86, TOP
            for k_ in range(int((x1 - x0) / 22)):
                if k_ % 2 == 0: po.line([(x0 + k_ * 22, y), (x0 + k_ * 22 + 12, y)], TEAL, 4)
            po.text(((x0 + x1) / 2, y - 40), "？", 56, TEAL)
            ov = ov.resize(OUT_WH, Image.LANCZOS)
            mask = Image.eval(ImageChops_diff(ov), lambda v: 255 if v > 6 else 0)
            im = Image.composite(Image.blend(im, ov, qa), im, mask)
        return im
    return frame(t)


def ImageChops_diff(ov):
    from PIL import ImageChops
    return ImageChops.difference(ov, Image.new("RGB", ov.size, BG)).convert("L")


if __name__ == "__main__":
    out = os.path.join(sys.argv[1], "diagram"); os.makedirs(out, exist_ok=True)
    for a_ in sys.argv:
        if a_.startswith("--pair="):
            MATCH = json.load(open(os.path.join(a_.split("=", 1)[1], "pairing_log.json")))["match"]
    T_FROM = float([a_ for a_ in sys.argv if a_.startswith("--from=")][0].split("=")[1]) if any(a_.startswith("--from=") for a_ in sys.argv) else T0
    if "--still" in sys.argv:
        v6 = [a_ for a_ in sys.argv if a_.startswith("--v6=")]
        if v6: setup_v6(v6[0].split("=", 1)[1])
        for s_ in sys.argv[sys.argv.index("--still") + 1].split(","):
            (frame6 if v6 else frame)(float(s_)).save(os.path.join(sys.argv[1], ("d6_%06.2f.png" if v6 else "d4_%06.2f.png") % float(s_)))
        print("STILLS done")
    elif any(a_.startswith("--v6=") for a_ in sys.argv):
        pair_dir = [a_ for a_ in sys.argv if a_.startswith("--v6=")][0].split("=", 1)[1]
        setup_v6(pair_dir); out6 = os.path.join(sys.argv[1], "diagram6"); os.makedirs(out6, exist_ok=True)
        ch0, ch1 = V6["ch0"], V6["ch1"]; n = int(round((ch1 - ch0) * FPS)); done_ = 0
        for i in range(n):
            t = ch0 + i / FPS
            need = (V6["d2"] - 0.05 <= t < V6["t3d0"] + 0.5) or (V6["t3d1"] - 0.5 <= t < V6["d8"] + 0.1)
            if not need: continue
            fp = os.path.join(out6, "d_%04d.png" % (i + 1))
            if os.path.exists(fp) and "--redo" not in sys.argv: continue
            frame6(t).save(fp, compress_level=1); done_ += 1
        W_ = V6["W"]
        ev = [dict(kind=e["kind"], t=round(W_.new_of(e["t"]), 3)) for e in events() if e["t"] < 244.5]
        P = V6["P"]
        ev += [dict(kind="pop", t=PI["card"] + 0.05), dict(kind="tap", t=PI["tap"]), dict(kind="pair", t=PI["done"]), dict(kind="whoosh", t=PI["go"]),
               dict(kind="pop", t=P[17][0] + 0.3), dict(kind="whoosh", t=at_char17(11)), dict(kind="unlock", t=at_char17(11) + 1.3), dict(kind="accept", t=at_char17(11) + 1.5),
               dict(kind="whoosh", t=V6["add"][0] + 0.9), dict(kind="reject", t=V6["add"][0] + 2.3)]
        json.dump(dict(t0=ch0, t1=ch1, fps=FPS, frames=n, d2=V6["d2"], d8=V6["d8"], t3d0=V6["t3d0"], t3d1=V6["t3d1"], events=sorted(ev, key=lambda e: e["t"])),
                  open(os.path.join(sys.argv[1], "ch04_diagram6.json"), "w"), indent=0)
        print("DIAGRAM6", done_, "frames ->", out6)
    else:
        n = int(round((T1 - T0) * FPS))
        for i in range(n):
            if T0 + i / FPS < T_FROM - 1e-6: continue
            frame(T0 + i / FPS).save(os.path.join(out, "d_%04d.png" % (i + 1)), compress_level=1)
        json.dump(dict(t0=T0, t1=T1, fps=FPS, frames=n, events=events()), open(os.path.join(sys.argv[1], "ch04_diagram.json"), "w"), indent=0)
        print("DIAGRAM", n, "frames ->", out)
