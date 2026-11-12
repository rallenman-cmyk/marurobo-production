# 第5章（台本 v2：本編 7:07〜10:55＝426.98〜654.96 秒）の図
#   たとえ：電波の「チャンネル」＝ 窓。画面の真ん中に、縦に並んだ窓の列（みんなが使う同じ空気）。
#   スマホとイヤホンは、自分が使う窓へ光を向ける。スマホとイヤホンが同じ窓を照らしていると、荷物がその窓を通って届く。
#   ① 頭（73〜76）：二つの疑問の画（第3章の終わりと同じ）。① に「解けた ✓」、② を強く → 図へ
#   ② 前半（77〜84）：二組とも同じ窓。同じタイミングで重なると、受け取る側で中身が読めない（帯＝相手は分かる。中身は読めない）
#   ③ 中盤（85〜102）：自分の組だけ、窓を三つに。スマホだけ変える → 受け取れない／二台でそろえて変える → 受け取れる。
#      順番とタイミング（つないだときにそろえる）→ 窓の正体は周波数（窓の中の波）→ 実際は数十の窓 → 次々に切り替える
#   ④ 後半（103〜113）：隣の組も戻す。たまに同じ窓で重なっても、次へ切り替わる。うまく通信できない窓は、二台で使う候補から外す。
#      それでも荷物が届かないことはある →「なかったことになるのでしょうか？」（第6章のまるロボの配達へ）
#   部品は第4章の図（ch04_diagram.py）と同じ：スマホ・イヤホン・帯つきの荷物・○△の印・色
# 使い方: python3 ch05_diagram.py OUT_DIR [--still 秒,秒,…]   → OUT_DIR/ch05/c_0001.png …（1280×720・24fps）
import sys, os, json, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ch04_diagram as dg
import ch03_questions as q3

W, H, FPS, S = 1280, 720, 24, dg.S
TL = {e["no"]: e for e in json.load(open(os.path.join(HERE, "..", "script", "script_v2_timed.json"), encoding="utf-8"))}
T_A, T_B = TL[73]["start"], TL[114]["start"]                  # 第5章の始まりと終わり（第6章の始まり）


def ln(n): return TL[n]["start"], TL[n]["end"], TL[n]["text"]
def at(n, word=None):
    a, b, t = ln(n)
    return a if word is None else a + (b - a) * t.index(word) / len(t)


sm = dg.sm; mix = dg.mix
TEAL, AMBER, INK, GRAY, GREEN, RED, WHITE = dg.TEAL, dg.AMBER, dg.INK, dg.GRAY, dg.GREEN, dg.RED, dg.WHITE
SCR = {TEAL: ((92, 196, 210), (160, 120, 200)), AMBER: ((240, 180, 90), (220, 110, 120))}
def lerp(a, b, u): return a + (b - a) * u
def lerp2(p0, p1, u): return (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u))
def win(t, a, b, fi=0.3, fo=0.3): return sm((t - a) / fi) * (1 - sm((t - b) / fo))


# ================================================================ 時刻（ナレーションが先、動きはあと）
T_CARD_OUT = at(76) + 0.45                                     # 二つの疑問の画 → 図
T_COL_IN = at(77, "小さな窓") + 0.1                             # 窓の列が現れる
T_SAME = at(78, "同じ窓") + 0.1                                 # 二組とも同じ窓を照らす
OK_A = [at(79) + 0.5, at(79) + 2.7]                             # こちらだけ：届いて読める
T_CLASH = at(80, "重なると") - 0.2                              # 二組が同じタイミングで送る（窓で重なる）
T_BAD = at(81, "読めなく")                                      # × と「読めない」
T_OTHER = at(82) + 0.3                                          # 「ほかの電波」
T_ADDR, T_BODY = at(83) + 0.2, at(83, "そのデータ")             # 「相手は分かる」「中身は読めない」
T_NOT_SWAP, T_GAP = at(84) + 0.2, at(84, "自分の曲")            # 隣の曲ではない → 自分の曲が途切れる
T_SOLO = at(87) + 0.35                                          # 自分の組だけに（隣は消え、二台が真ん中へ）
T_THREE = at(88, "三つの窓") + 0.1                              # 窓を三つに
T_HERE = at(90, "ここ")                                         # 「いまは、両方ともここ」
T_PH_MOVE = at(91, "変えたら") + 0.1                            # スマホだけ次の窓へ
T_TRY = TL[91]["end"] + 0.5                                     # 問いのあと、荷物を送ってみる（届かない）
T_WAIT = at(92) + 0.2                                           # イヤホンは元の窓のまま（光を強く）
T_BOTH = at(94, "そろえて") + 0.3                               # イヤホンもそろえて変える
T_NEXT1, T_NEXT2 = at(95, "ここ") - 0.1, at(96, "こちら") - 0.1
T_SEQ = at(97) + 0.2                                            # 順番とタイミング：切り替え続ける
T_LINK = at(98, "つないだ")                                     # つないだときにそろえた順番
T_FREQ = at(99, "正体") + 0.1                                   # 窓の中に波（周波数）
T_FREQ_LBL = at(99, "周波数")
T_VIB = at(100) + 0.2                                           # 1 秒間に振動する回数
T_MANY = at(101, "数十") + 0.05                                 # 窓を数十に
T_FAST = at(102) + 0.2                                          # 次々に切り替える（速く）
T_NB_BACK = at(103, "戻して") + 0.2                             # 隣の組が戻る
T_CLASH2 = at(105) - 0.35                                       # 「あ、ここでは重なりました」の少し前に重なる
T_AFH_NOISE = at(108, "うまく通信") - 0.1                       # うまく通信できない窓（ざらざら）
T_AFH_CLOSE = at(108, "外す") + 0.1                             # 候補から外す（窓が閉じる）
T_SHARE = at(109) + 0.15                                        # 二台で共有
T_LOST = at(112, "届かない") + 0.2                              # それでも届かない荷物
T_Q = at(113) + 0.3                                             # 「なかったことになる？」

# ================================================================ 置き場所
TWO = dict(P=((190, 210), (1090, 200)), N=((190, 500), (1090, 490)), ds=0.78)      # 二組：上が自分の組、下が隣の組
ONE = dict(P=((235, 360), (1050, 350)), ds=1.05)                                     # 自分の組だけ（真ん中・大きく）
CX = 640


def column_geom(t):
    """窓の列：（上, 下, 幅, 窓の数の組み合わせ）。窓の数は 5 → 3 → 40 と変わる（変わる間は重ねて溶かす）"""
    u1 = sm((t - T_SOLO) / 0.9); u2 = sm((t - T_NB_BACK) / 0.9)
    y0 = lerp(lerp(120, 140, u1), 100, u2); y1 = lerp(lerp(590, 580, u1), 610, u2)
    w = lerp(lerp(118, 150, u1), 118, u2)
    if t < T_THREE: ns = [(5, 1.0)]
    elif t < T_THREE + 0.6: v = sm((t - T_THREE) / 0.6); ns = [(5, 1 - v), (3, v)]
    elif t < T_MANY: ns = [(3, 1.0)]
    elif t < T_MANY + 0.7: v = sm((t - T_MANY) / 0.7); ns = [(3, 1 - v), (40, v)]
    else: ns = [(40, 1.0)]
    return y0, y1, w, ns


def slot_box(k, n, y0, y1, w):
    gap = 14 if n <= 5 else (12 if n <= 3 else 3)
    h = (y1 - y0 - gap * (n - 1)) / n; a = y0 + k * (h + gap)
    return (CX - w / 2, a, CX + w / 2, a + h)


# ================================================================ どの窓を使うか（スマホ・イヤホン、自分の組・隣の組）
def hop_seq(seed, n, length, avoid=()):
    x = seed; out = []
    while len(out) < length:
        x = (x * 1103515245 + 12345) % 2147483648; k = (x >> 8) % n
        if k in avoid or (out and k == out[-1]): continue
        out.append(k)
    return out


BAD = set(range(15, 23))                                         # うまく通信できない窓（後半で外す）
HOP_FAST, HOP_C = 0.42, 0.62                                     # 数十の窓での切り替えの間（ゆっくり見せる）
SEQ_ME_B = [1, 2, 0, 2, 1, 0, 1, 2, 0, 1, 0, 2, 1, 2]            # 窓三つ：「切り替える順番」（2→3→1→3→2→1…）
SEQ_ME = hop_seq(7, 40, 200); SEQ_NB = hop_seq(91, 40, 200)
SEQ_ME_AFH = hop_seq(17, 40, 200, BAD); SEQ_NB_AFH = hop_seq(23, 40, 200, BAD)
# 「あ、ここでは重なりました」：その一回だけ、隣を自分と同じ窓に。ほかは重ならないように
def c_hops(t0, seq, t):
    return seq[max(0, int((t - t0) // HOP_C))]
K_CLASH = int((T_CLASH2 - T_NB_BACK - 0.9) // HOP_C)
for k_ in range(len(SEQ_NB)):
    if k_ == K_CLASH: SEQ_NB[k_] = SEQ_ME[k_]
    elif SEQ_NB[k_] == SEQ_ME[k_]: SEQ_NB[k_] = (SEQ_ME[k_] + 9) % 40
K_AFH_FAIL = int((T_AFH_NOISE + 0.9 - T_NB_BACK - 0.9) // HOP_C)   # 外す前に、うまく通信できない窓に当たる一回
SEQ_ME[K_AFH_FAIL] = 18; SEQ_NB[K_AFH_FAIL] = 30 if SEQ_NB[K_AFH_FAIL] in BAD else SEQ_NB[K_AFH_FAIL]
T_C0 = T_NB_BACK + 0.9                                           # 後半の切り替えの始まり
for k_ in range(len(SEQ_NB_AFH)):                                # 外したあとは、重ならないように（重なる場面は一度だけ見せる）
    while SEQ_NB_AFH[k_] == SEQ_ME_AFH[k_] or SEQ_NB_AFH[k_] in BAD: SEQ_NB_AFH[k_] = (SEQ_NB_AFH[k_] + 9) % 40


def choice(t):
    """→ dict（窓の数 n, 自分のスマホ・イヤホン、隣のスマホ・イヤホンが使う窓。None は使っていない）"""
    if t < T_THREE:                                              # 窓五つ：二組とも 3 番目
        return dict(n=5, mp=2, me=2, np=2, ne=2)
    if t < T_MANY:                                               # 窓三つ：自分の組だけ
        ph = 0 if t < T_PH_MOVE else 1
        ea = 0 if t < T_BOTH else 1
        if t >= T_NEXT1: ph = ea = 2
        if t >= T_NEXT2: ph = ea = 0
        if t >= T_SEQ:
            k = int((t - T_SEQ) // 0.9) + 1; ph = ea = SEQ_ME_B[k % len(SEQ_ME_B)]
        if t >= T_FREQ - 0.4: ph = ea = 1                       # 周波数を見せる間は止める（真ん中）
        return dict(n=3, mp=ph, me=ea, np=None, ne=None)
    if t < T_C0:                                                 # 数十の窓：自分の組だけ、次々に
        k = SEQ_ME[max(0, int((t - T_FAST) // HOP_FAST))] if t >= T_FAST else 20
        return dict(n=40, mp=k, me=k, np=None, ne=None)
    seq_me = SEQ_ME_AFH if t >= T_AFH_CLOSE else SEQ_ME; seq_nb = SEQ_NB_AFH if t >= T_AFH_CLOSE else SEQ_NB
    k_me = c_hops(T_C0, seq_me, t); k_nb = c_hops(T_C0, seq_nb, t)
    if t >= T_Q: k_me = c_hops(T_C0, seq_me, T_Q); k_nb = c_hops(T_C0, seq_nb, T_Q)   # 問いの間は止める
    return dict(n=40, mp=k_me, me=k_me, np=k_nb, ne=k_nb)


# ================================================================ 荷物の流れ：(送る時刻, 組, 窓, 結果)。結果 ok／miss（窓が合わない）／clash（重なって読めない）／lost（届かない）／bad（うまく通信できない窓）
def flights():
    F = []
    for t0 in OK_A: F.append((t0, "me", 2, "ok", 1.1))
    F.append((T_CLASH, "me", 2, "clash", 1.1)); F.append((T_CLASH, "nb", 2, "clash", 1.1))
    F.append((at(89) + 0.6, "me", 0, "ok", 1.1)); F.append((at(89) + 3.0, "me", 0, "ok", 1.1))
    F.append((T_TRY, "me", 1, "miss", 1.4))
    F.append((T_BOTH + 0.5, "me", 1, "ok", 1.1)); F.append((T_NEXT1 + 0.15, "me", 2, "ok", 0.8)); F.append((T_NEXT2 + 0.15, "me", 0, "ok", 0.8))
    t = T_SEQ + 0.9
    while t < T_FREQ - 0.9: k = int((t - T_SEQ) // 0.9) + 1; F.append((t + 0.1, "me", SEQ_ME_B[k % len(SEQ_ME_B)], "ok", 0.7)); t += 0.9
    t = T_FAST
    while t < T_C0 - 0.3: k = SEQ_ME[int((t - T_FAST) // HOP_FAST)]; F.append((t + 0.03, "me", k, "ok", 0.36)); t += HOP_FAST
    t = T_C0; i = 0
    while t < T_Q - 0.2:
        aft = t >= T_AFH_CLOSE; sm_ = SEQ_ME_AFH if aft else SEQ_ME; sn_ = SEQ_NB_AFH if aft else SEQ_NB
        km, kn = sm_[i], sn_[i]
        res = "clash" if km == kn else ("bad" if (km in BAD and t >= T_AFH_NOISE and not aft) else "ok")
        if abs(t + 0.05 - T_LOST) < HOP_C / 2: res = "lost"
        F.append((t + 0.05, "me", km, res, 0.52))
        F.append((t + 0.05, "nb", kn, "clash" if res == "clash" else "ok", 0.52))
        t += HOP_C; i += 1
    return F


FL = flights()


# ================================================================ 絵
def pair_pos(t, who):
    u1 = sm((t - T_SOLO) / 0.9); u2 = sm((t - T_NB_BACK) / 0.9)
    if who == "me":
        ph = lerp2(lerp2(TWO["P"][0], ONE["P"][0], u1), TWO["P"][0], u2); eb = lerp2(lerp2(TWO["P"][1], ONE["P"][1], u1), TWO["P"][1], u2)
        ds = lerp(lerp(TWO["ds"], ONE["ds"], u1), TWO["ds"], u2); a = 1.0
    else:
        ph, eb, ds = TWO["N"][0], TWO["N"][1], TWO["ds"]
        a = (1 - sm((t - T_SOLO) / 0.6)) + sm((t - T_NB_BACK) / 0.8)
    return ph, eb, ds, min(1.0, a)


def ph_anchor(ph, ds): return (ph[0] + 44 * ds, ph[1])
def eb_anchor(eb, ds): return (eb[0] - 52 * ds, eb[1] - 22 * ds)


def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def scramble(p, c, sc, a, seed):
    """荷物の中身が読めない（重なった）：中の棒がばらばらの高さ・色"""
    x, y = c
    for b in range(5):
        hh = ((seed * 7 + b * 13) % 11 + 2) * sc; col = (AMBER, TEAL, (230, 236, 238))[(seed + b) % 3]
        p.d.rectangle([(x - 4 * sc + b * 6 * sc) * S, (y + 11 * sc - hh) * S, (x - 1 * sc + b * 6 * sc) * S, (y + 11 * sc) * S], fill=mix(col, a))
    for k in range(3): p.line([(x - 22 * sc, y - 8 * sc + k * 7 * sc), (x + 22 * sc, y - 12 * sc + k * 9 * sc)], mix((220, 90, 80), a * 0.8), 2)


def check(p, c, r, a, col=GREEN):
    p.ell((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=mix(col, a))
    p.line([(c[0] - r * 0.45, c[1] + r * 0.02), (c[0] - r * 0.1, c[1] + r * 0.36), (c[0] + r * 0.48, c[1] - r * 0.34)], mix(WHITE, a), max(2, r * 0.16))


def xmark(p, c, r, a):
    p.ell((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=mix(RED, a))
    p.line([(c[0] - r * 0.42, c[1] - r * 0.42), (c[0] + r * 0.42, c[1] + r * 0.42)], mix(WHITE, a), max(2, r * 0.16))
    p.line([(c[0] - r * 0.42, c[1] + r * 0.42), (c[0] + r * 0.42, c[1] - r * 0.42)], mix(WHITE, a), max(2, r * 0.16))


def tag(p, xy, txt, col, a, px=26):
    if a <= 0.02: return
    w_ = sum(0.55 if ord(ch_) < 128 else 1.0 for ch_ in txt) * px + 26
    p.rr((xy[0] - w_ / 2, xy[1] - px * 0.78, xy[0] + w_ / 2, xy[1] + px * 0.78), 12, fill=mix(WHITE, a), outline=mix(col, a), width=3)
    p.text(xy, txt, px, mix(col, a))


def wave_in(p, box, cycles, ph, col, a):
    x0, y0, x1, y1 = box; yc = (y0 + y1) / 2; amp = (y1 - y0) * 0.30
    pts = [(x, yc + amp * math.sin(2 * math.pi * cycles * (x - x0) / (x1 - x0) - ph)) for x in range(int(x0 + 8), int(x1 - 7), 2)]
    p.line(pts, mix(col, a), 3)


def frame(t):
    im = Image.new("RGB", (W * S, H * S), dg.BG); p = dg.Pen(ImageDraw.Draw(im))
    # ---------------------------------------------------------------- 頭：二つの疑問（① 解けた ✓ → ② を強く）
    if t < T_CARD_OUT + 0.5:
        ca = 1 - sm((t - T_CARD_OUT) / 0.5)
        chk = sm((t - at(73, "解けました")) / 0.5); hi2 = sm((t - at(74)) / 0.5)
        q3.draw_card(p, t - T_A, ca, ca, ca, hi1=0.0, hi2=hi2, dim1=1.0 - 0.45 * hi2, dim2=1.0, check1=chk)
        if t < T_CARD_OUT: return im.resize((W, H), Image.LANCZOS)
    da = sm((t - T_CARD_OUT) / 0.5)                              # 図の出方
    ch = choice(t); y0, y1, cw, ns = column_geom(t)
    me = pair_pos(t, "me"); nb = pair_pos(t, "nb")
    # ---------------------------------------------------------------- 窓の列（チャンネル）
    ca_ = da * sm((t - T_COL_IN) / 0.5)
    closed = sm((t - T_AFH_CLOSE) / 0.6); noisy = sm((t - T_AFH_NOISE) / 0.4) * (1 - closed)
    for n, na in ns:
        for k in range(n):
            bx = slot_box(k, n, y0, y1, cw); aa = ca_ * na
            lit_me = ch["n"] == n and ch["mp"] == k and ch["me"] == k
            lit_nb = ch["n"] == n and ch["np"] == k and ch["ne"] == k and nb[3] > 0.05
            r_ = 10 if n <= 5 else 3
            fill = (250, 251, 252)
            p.rr(bx, r_, fill=mix(fill, aa), outline=mix((150, 158, 166), aa), width=2 if n <= 5 else 1)
            if lit_me and lit_nb:
                hb = (bx[1] + bx[3]) / 2
                p.rr((bx[0], bx[1], bx[2], hb), r_, fill=mix(TEAL, aa * 0.9)); p.rr((bx[0], hb, bx[2], bx[3]), r_, fill=mix(AMBER, aa * 0.9 * nb[3]))
            elif lit_me: p.rr(bx, r_, fill=mix(TEAL, aa * 0.85))
            elif lit_nb: p.rr(bx, r_, fill=mix(AMBER, aa * 0.85 * nb[3]))
            if n == 40 and k in BAD and (noisy > 0 or closed > 0):     # うまく通信できない窓：ざらざら → 閉じる
                for j in range(6):
                    xx = bx[0] + 6 + ((int(t * 24) * 7 + j * 19 + k * 5) % int(cw - 12))
                    p.line([(xx, bx[1] + 1), (xx + 5, bx[3] - 1)], mix((160, 90, 84), aa * noisy * 0.9), 2)
                if closed > 0: p.rr((bx[0], bx[1], bx[0] + (bx[2] - bx[0]) * closed, bx[3]), r_, fill=mix((120, 126, 134), aa * closed))
            if ch["n"] == 3 and n == 3 and t >= T_FREQ:                # 窓の正体は周波数：窓の中に波（下の窓ほど振動が多い）
                wave_in(p, bx, (1.5, 2.5, 3.5)[k], 2 * math.pi * 1.2 * (t - T_FREQ), TEAL if not lit_me else WHITE, aa * sm((t - T_FREQ) / 0.6))
        if n == 3 and na > 0.5:                                       # 窓の番号（順番を見せる）
            for k in range(3):
                bx = slot_box(k, 3, y0, y1, cw); p.text((bx[0] - 26, (bx[1] + bx[3]) / 2), str(k + 1), 26, mix(GRAY, ca_ * na * (1 - sm((t - T_FREQ) / 0.5))))
    if ca_ > 0 and t < T_SOLO + 2: tag(p, (CX, y0 - 32), "チャンネル（窓）", TEAL, ca_ * win(t, T_COL_IN + 0.2, T_SAME + 2.5))
    if t >= T_FREQ_LBL - 0.2 and t < T_MANY + 1.5:
        tag(p, (CX, y0 - 34), "周波数" if t < T_VIB else "周波数：1秒間に振動する回数", TEAL, win(t, T_FREQ_LBL - 0.2, T_MANY + 1.2))
    if t >= T_MANY: tag(p, (CX + cw / 2 + 92, (y0 + y1) / 2), "数十の窓", TEAL, win(t, T_MANY + 0.4, T_FAST + 2.5), 24)
    if T_FAST + 0.6 < t < T_C0 + 4: p.text((CX, y1 + 34), "※ 実際は、もっとずっと速く切り替えています", 20, mix(GRAY, win(t, T_FAST + 0.6, T_C0 + 3)))
    # ---------------------------------------------------------------- 光（どの窓を使っているか）
    def beams(pos, kp, ke, col, a):
        ph, eb, ds, pa = pos; a = a * pa
        if a <= 0.01: return
        n = ch["n"]
        for kk, anchor, side in ((kp, ph_anchor(ph, ds), 0), (ke, eb_anchor(eb, ds), 2)):
            if kk is None: continue
            bx = slot_box(kk, n, y0, y1, cw); ex = bx[side]
            emph = 1.0 + (0.8 * math.sin(math.pi * min(1.0, max(0.0, (t - T_WAIT) / 1.2))) if (side == 2 and col == TEAL and T_WAIT < t < T_WAIT + 1.2) else 0.0)
            p.poly([anchor, (ex, bx[1] + 1), (ex, bx[3] - 1)], fill=mix(col, a * 0.16 * emph))
            p.line([(ex, bx[1] + 1), (ex, bx[3] - 1)], mix(col, a), 5 if n <= 5 else 3)
    if t >= T_SAME - 0.3 or ch["n"] != 5:
        ba = da * sm((t - (T_SAME - 0.3)) / 0.5)
        beams(me, ch["mp"], ch["me"], TEAL, ba); beams(nb, ch["np"], ch["ne"], AMBER, ba)
    # ---------------------------------------------------------------- スマホ・イヤホン・印
    for who, (pos, col, mk, nm) in (("nb", (nb, AMBER, "t", "隣の組")), ("me", (me, TEAL, "o", "自分の組"))):
        ph, eb, ds, a = pos; a *= da
        if a <= 0.01: continue
        dg.phone(p, ph[0], ph[1], SCR[col], a=a, ds=ds)
        dg.earbud(p, eb[0], eb[1], col, (150, 158, 166), a=a, ds=ds)
        dg.mark(p, (ph[0] - 82 * ds, ph[1] - 30 * ds), "o" if mk == "o" else "t", 13 * ds / 0.78, mix(col, a), 4)
        p.text((ph[0] - 82 * ds, ph[1] + 12 * ds), nm, int(18 * ds / 0.78), mix(col, a))
    # ---------------------------------------------------------------- 荷物
    for t0, who, k, res, dur in FL:
        u = (t - t0) / dur
        if u < 0 or u > 1.0 + (1.6 if res in ("clash", "miss", "bad", "lost") else 0.5): continue
        pos = me if who == "me" else nb; ph, eb, ds, pa = pos
        if pa < 0.05: continue
        n = 40 if (t0 >= T_MANY) else (3 if t0 >= T_THREE else 5)
        bx = slot_box(k, n, y0, y1, cw); wc = ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)
        a0_, a1_ = ph_anchor(ph, ds), eb_anchor(eb, ds)
        col = TEAL if who == "me" else AMBER; sc = 0.85 * ds / 0.78 if n <= 5 else 0.55
        uu = min(u, 1.0)
        if uu < 0.5: c = bez(a0_, ((a0_[0] + wc[0]) / 2, min(a0_[1], wc[1]) - 30), wc, uu / 0.5)
        else:
            stop = 0.78 if res == "miss" else 1.0
            v = min((uu - 0.5) / 0.5, stop) if res != "lost" else min((uu - 0.5) / 0.5, 0.45)
            c = bez(wc, ((wc[0] + a1_[0]) / 2, min(wc[1], a1_[1]) - 30), a1_, v)
        fade = 1.0
        if res in ("miss", "lost", "bad") and u > 0.85: fade = 1 - sm((u - 0.85) / 0.5)
        if res == "ok" and u > 1.0: fade = 1 - sm((u - 1.0) / 0.25)
        if res == "clash" and u > 1.0: fade = 1 - sm((u - 1.6) / 0.5) if t < T_SOLO else 1 - sm((u - 1.0) / 0.4)
        aa = pa * da * fade
        if aa <= 0.02: continue
        if res == "lost" and uu > 0.5:                                # 届かない：途中で薄くなり、輪郭だけ残る
            ghost = sm((uu - 0.62) / 0.3); aa *= (1 - 0.85 * ghost)
        dg.parcel(p, c, col, sc, aa, band=1.0, band_col=col)
        if res == "clash" and u > 0.5: scramble(p, c, sc, aa * sm((u - 0.5) / 0.15), int(t0 * 10))
        if res == "bad" and u > 0.5: scramble(p, c, sc, aa * sm((u - 0.5) / 0.15), int(t0 * 10) + 3)
        # 結果の印
        if who == "me":
            mpos = (a1_[0] + 34 * sc, a1_[1] - 46 * sc)
            if res == "ok" and u > 0.98: check(p, mpos, 15 * sc / 0.85, aa * sm((u - 0.98) / 0.12))
            if res == "miss" and u > 0.85: xmark(p, ((wc[0] + a1_[0]) / 2 + 60, wc[1] - 40), 18, pa * da * sm((u - 0.85) / 0.15) * (1 - sm((t - T_BOTH) / 0.4)))
            if res in ("clash", "bad") and n == 40 and u > 0.95: xmark(p, mpos, 13, aa * sm((u - 0.95) / 0.12))
    # 前半の「読めない」：× と、帯（相手は分かる）・中身（読めない）の札
    if T_CLASH < t < T_SOLO:
        ph, eb, ds, pa = me; c_ = eb_anchor(eb, ds)
        if t >= T_BAD - 0.3: xmark(p, (c_[0] + 30, c_[1] - 60), 20, da * sm((t - T_BAD + 0.3) / 0.3) * (1 - sm((t - T_SOLO + 0.6) / 0.4)))
        tag(p, (CX + 120, 380), "ほかの電波", AMBER, da * win(t, T_OTHER, T_ADDR - 0.2))
        if t >= T_ADDR - 0.2:                                         # 受け取った荷物を大きく：帯は読める（相手は分かる）、中身は読めない
            za = da * win(t, T_ADDR - 0.2, T_SOLO - 0.6)
            zc = (900, 380); dg.parcel(p, zc, TEAL, 2.4, za, band=1.0, band_col=TEAL); scramble(p, zc, 2.4, za, 5)
            tag(p, (zc[0] - 10, zc[1] - 118), "相手は分かる ✓", TEAL, za, 24)
            tag(p, (zc[0] + 10, zc[1] + 96), "中身は読めない ×", RED, za * sm((t - T_BODY) / 0.3), 24)
        if t >= T_NOT_SWAP:                                           # 隣の曲に入れ替わるのではない → 自分の曲が途切れる
            na_ = da * win(t, T_NOT_SWAP, T_SOLO - 0.5)
            q3.note(p, (eb[0] + 70, eb[1] - 70), AMBER, na_ * (1 - 0.6 * sm((t - T_GAP) / 0.4)), 1.2)
            p.line([(eb[0] + 52, eb[1] - 92), (eb[0] + 96, eb[1] - 40)], mix(RED, na_), 4)
            ga = da * win(t, T_GAP, T_SOLO - 0.5)
            if ga > 0:
                xg0, xg1, yg = eb[0] - 250, eb[0] - 70, eb[1] + 80; g0, g1 = xg0 + 70, xg0 + 110
                for s0, s1 in ((xg0, g0), (g1, xg1)):
                    p.line([(x, yg + 12 * math.sin((x - xg0) / 9.0 - 6 * (t - T_GAP))) for x in range(int(s0), int(s1), 3)], mix(TEAL, ga), 4)
                p.line([(g0 + 4, yg), (g1 - 4, yg)], mix((190, 196, 202), ga), 3)
    # 「いまは、両方ともここ」：指さし
    if T_HERE - 0.2 < t < T_PH_MOVE:
        bx = slot_box(0, 3, y0, y1, cw); ha = win(t, T_HERE - 0.2, T_PH_MOVE - 0.2)
        p.poly([(bx[2] + 70, (bx[1] + bx[3]) / 2), (bx[2] + 100, (bx[1] + bx[3]) / 2 - 16), (bx[2] + 100, (bx[1] + bx[3]) / 2 + 16)], fill=mix(TEAL, ha))
    # 「スマホだけ」：スマホの光を動かしたあと、問い
    if T_PH_MOVE < t < T_BOTH:
        tag(p, (me[0][0], me[0][1] - 128), "スマホだけ次へ", TEAL, win(t, T_PH_MOVE, T_TRY + 0.2), 24)
        tag(p, (me[1][0], me[1][1] - 138), "元の窓のまま", TEAL, win(t, T_WAIT, T_BOTH - 0.3), 24)
    # 順番とタイミング（窓三つ）：二台の下に同じ順番の帯。つないだときにそろえた
    if T_SEQ - 0.2 < t < T_FREQ + 0.4:
        sa = win(t, T_SEQ - 0.2, T_FREQ)
        cur = int((t - T_SEQ) // 0.9) + 1 if t >= T_SEQ else 0
        for x_ in (me[0][0], me[1][0] - 10):
            for j in range(6):
                kk = SEQ_ME_B[(cur + j) % len(SEQ_ME_B)]; xx = x_ - 100 + j * 40; yy = me[0][1] + 150
                on = j == 0
                p.rr((xx - 15, yy - 17, xx + 15, yy + 17), 6, fill=mix(TEAL if on else (225, 230, 235), sa))
                p.text((xx, yy), str(kk + 1), 20, mix(WHITE if on else INK, sa))
            p.text((x_ - 140, me[0][1] + 150), "順番", 18, mix(GRAY, sa))
        if t >= T_LINK - 0.2:
            la = win(t, T_LINK - 0.2, T_FREQ - 0.2)
            p.rr((CX - 112, me[0][1] + 132, CX + 112, me[0][1] + 170), 10, fill=mix(GREEN, la))
            p.text((CX, me[0][1] + 151), "つないだときに、そろえた", 18, mix(WHITE, la))
        beat = (t - T_SEQ) % 0.9 if t >= T_SEQ else 1.0                # タイミング：切り替える瞬間に、二台の上の点が一緒に光る
        for x_ in (me[0][0], me[1][0] - 10):
            r_ = 7 + 6 * max(0.0, 1 - beat / 0.25)
            p.ell((x_ - r_, me[0][1] - 112 - r_, x_ + r_, me[0][1] - 112 + r_), fill=mix(TEAL, sa * (0.35 + 0.65 * max(0.0, 1 - beat / 0.3))))
    # 後半：二台で共有する「使う窓」の地図（外した窓に印）
    if t >= T_SHARE - 0.2:
        ma = win(t, T_SHARE - 0.2, T_Q)
        for x_, y_ in ((me[0][0] + 0, me[0][1] - 112), (me[1][0] - 10, me[1][1] - 122)):
            p.rr((x_ - 13, y_ - 52, x_ + 13, y_ + 52), 5, fill=mix(WHITE, ma), outline=mix(GRAY, ma), width=2)
            for k in range(40):
                yy = y_ - 48 + k * 2.4
                p.d.rectangle([(x_ - 9) * S, yy * S, (x_ + 9) * S, (yy + 1.5) * S], fill=mix((120, 126, 134) if k in BAD else (190, 220, 224), ma))
        dashed_ = lambda a_, b_: [p.line([lerp2(a_, b_, j / 12), lerp2(a_, b_, min(1, (j + 0.55) / 12))], mix(GRAY, ma), 2) for j in range(12)]
        dashed_((me[0][0] + 20, me[0][1] - 112), (me[1][0] - 30, me[1][1] - 122))
        tag(p, (CX, me[0][1] - 150), "二台で共有", TEAL, win(t, T_SHARE, T_SHARE + 3.5), 22)
    # 「あ、ここでは重なりました」の窓に輪
    if T_CLASH2 < t < T_CLASH2 + 2.6:
        k = SEQ_ME[K_CLASH]; bx = slot_box(k, 40, y0, y1, cw); ra = win(t, T_CLASH2 + 0.25, T_CLASH2 + 2.3)
        p.rr((bx[0] - 14, bx[1] - 12, bx[2] + 14, bx[3] + 12), 10, outline=mix(RED, ra), width=4)
    # 届かなかった荷物：「なかったことになる？」
    if t >= T_Q - 0.2:
        qa = sm((t - T_Q + 0.2) / 0.5)
        fl = [f for f in FL if f[3] == "lost"]
        if fl:
            t0, who, k, res, dur = fl[0]; ph, eb, ds, pa = me; bx = slot_box(k, 40, y0, y1, cw); wc = ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)
            c = bez(wc, ((wc[0] + eb_anchor(eb, ds)[0]) / 2, min(wc[1], eb_anchor(eb, ds)[1]) - 30), eb_anchor(eb, ds), 0.45)
            p.rr((c[0] - 30, c[1] - 22, c[0] + 30, c[1] + 22), 8, outline=mix(TEAL, qa), width=3)
            p.text((c[0], c[1] - 56), "？", 48, mix(TEAL, qa))
    return im.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    out = os.path.join(sys.argv[1], "ch05"); os.makedirs(out, exist_ok=True)
    if "--still" in sys.argv:
        for s_ in sys.argv[sys.argv.index("--still") + 1].split(","): frame(float(s_)).save(os.path.join(sys.argv[1], "c5_%06.2f.png" % float(s_)))
    else:
        n = int(round((T_B - T_A) * FPS))
        for i in range(n):
            fp = os.path.join(out, "c_%04d.png" % (i + 1))
            if os.path.exists(fp) and "--redo" not in sys.argv: continue
            frame(T_A + i / FPS).save(fp, compress_level=1)
        json.dump(dict(t0=T_A, t1=T_B, fps=FPS, frames=n), open(os.path.join(sys.argv[1], "ch05_diagram.json"), "w"), indent=0)
    print("ch05", T_A, T_B)
