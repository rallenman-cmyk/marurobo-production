# 第8章の図（本編 15:27.4〜17:00.3、台本 v2 の 161〜177）：ためる時間の帯・てんびん（161〜162）、ゲームの例と「押す → 当たる → 音」の時間の帯（163〜177）（2D）
#   ゲームの中のピクトグラムの人は、主人公と同じ姿（白い体・紺白しまの上着・黄色いキャップ・点の目）。サンドバッグにパンチ
#   パンチの腕は躍度最小で 0.10 秒で伸び（当たる）、0.06 秒止めて 0.18 秒で戻す。サンドバッグは減衰する振り子（ひも 1.2m）
#   音のずれは実際の 0.3 秒前後。そのままだと短すぎて見えないので、パンチの所は「ゆっくり再生（10分の1）」で見せ、画面にもそう書く
#   時刻：ナレーションの声の置き場所（stage/voice/achernar/placement.json）。「パンチは、もう当たっているのに」で当たり、
#         「音だけ、今ごろ届きました」で「ドン！」が鳴る
# 使い方: python3 ch08_game.py OUT_DIR [--still 秒,秒,...]  → OUT_DIR/game/g_0001.png …（1280×720・24fps）と ch08_game.json（効果音の時刻）
import sys, os, math, json
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ch04_diagram as dg
from ch04_diagram import Pen, sm, win, mix, W, H, FPS, S, BG, INK, TEAL, AMBER, GRAY, GREEN, RED, WHITE, DARK

PL = {p["no"]: p for p in json.load(open(os.path.join(HERE, "..", "voice", "achernar", "placement.json"), encoding="utf-8"))}
def L(n): return PL[n]["start"]
def LE(n): return PL[n]["end"]
def at_char(n, k, txt=None):
    """n 番の文の k 文字目の時刻（声の長さを文字数で割る）"""
    t = PL[n]["text"]; return L(n) + (LE(n) - L(n)) * k / len(t)

# 天びんに乗るまるロボ（2026-11-09。ch08_seesaw.py の動き → ch08_seesaw_render.py で描いた透明な絵）。MARU_SEESAW＝その置き場所（無ければ ch03/seesaw）
SS_DIR = os.environ.get("MARU_SEESAW") or os.path.join(HERE, "seesaw")
SS = {sc: json.load(open(os.path.join(SS_DIR, "seesaw_%s.json" % sc), encoding="utf-8")) for sc in ("A", "B") if os.path.exists(os.path.join(SS_DIR, "seesaw_%s.json" % sc))}
T_A, T_B = L(161) - 0.3, L(178)                 # この図の場面の始まりと終わり（本編の秒）。161 の前までは、塔の 3D（ch07_stage.py --part ch8）
NAVY, YELLOW, SKY, GRASS, BAG, PUR = (36, 52, 92), (240, 198, 56), (198, 228, 238), (122, 170, 110), (200, 72, 60), (118, 92, 170)
SLOW = 10.0                                      # ゆっくり再生：10分の1の速さ
BAG_X = 709                                      # バッグの支点の x：腕を伸ばしきったグローブの先（662＋15）に、止まっているバッグの左の面（709−32）が触れる

# ---------------------------------------------------------------- パンチの二回（ぴったり／遅れる）
T_TAP1 = LE(165) + 0.6                            # 「まずは、パンチと音が、ぴったり合う場合。」と言い終えてから押す（2026-11-09 ユーザー。指がボタンへ向かう 0.6 秒も言い終えてから）
T_TAP2 = L(167) - 1.10                            # 当たるのが「パンチは、もう当たっているのに」の頭
T_SND2 = L(168) - 0.65                            # 「ドン！」が鳴って 0.65 秒たってから「音だけ、今ごろ届きました」（2026-11-09 ユーザー）
EXT, HOLD, RET = 0.10, 0.06, 0.18                 # 腕：伸ばす・止める・戻す（実際の秒）
D_LATE = (T_SND2 - (T_TAP2 + EXT * SLOW)) / SLOW  # 実際の遅れ（秒）
PEND_L = 1.2; OMEGA = math.sqrt(9.81 / PEND_L); BETA = 0.9; TH0 = 0.35   # 振り子：支点から重心まで 1.2m・角振動数・減衰・最初の振れ（rad、約20°。強めのパンチ）


def mj(u):
    u = max(0.0, min(1.0, u)); return u * u * u * (10 - 15 * u + 6 * u * u)


def punch_state(t, t_tap):
    """t（本編の秒）→ (ゲームの中の実際の秒 τ, 腕の伸び 0〜1, 当たってからの τ)。ゆっくり再生は t_tap から"""
    tau = (t - t_tap) / SLOW
    if tau < 0: return tau, 0.0, None
    if tau < EXT: e = mj(tau / EXT)
    elif tau < EXT + HOLD: e = 1.0
    else: e = 1.0 - mj((tau - EXT - HOLD) / RET)
    return tau, e, (tau - EXT if tau >= EXT else None)


def bag_angle(th):
    """当たってから th 秒（実際）の振れの角度（rad、+ が奥＝右へ）"""
    if th is None or th < 0: return 0.0
    return TH0 * math.exp(-BETA * th) * math.sin(OMEGA * th)


# ---------------------------------------------------------------- 絵の部品
def fighter(p, x, y, e=0.0, sc=1.0, tilt=0.0, puzzled=0.0):
    """ゲームの中のピクトグラムの人（右向き）。e＝右の腕の伸び（0〜1）"""
    s = sc
    def P(dx, dy): return (x + dx * s, y + dy * s)
    hx, hy = P(0, -150); hr = 34 * s
    p.ell((hx - hr, hy - hr, hx + hr, hy + hr), fill=WHITE, outline=(200, 205, 210), width=2)                       # 頭
    p.d.chord([(hx - hr - 2 * s) * S, (hy - hr - 6 * s) * S, (hx + hr + 2 * s) * S, (hy + hr * 0.45) * S], 180, 360, fill=YELLOW)   # キャップ
    p.rr((hx + 4 * s, hy - 12 * s, hx + hr + 22 * s, hy - 4 * s), 3 * s, fill=YELLOW)                                     # つば（前＝右）
    ey = hy + 2 * s
    for ex in (hx + 8 * s, hx + 22 * s): p.ell((ex - 4 * s, ey - 5 * s, ex + 4 * s, ey + 5 * s), fill=INK)               # 点の目
    bx0, by0, bx1, by1 = x - 30 * s, y - 112 * s, x + 30 * s, y - 20 * s                                                   # 上着（紺白しま）
    p.rr((bx0, by0, bx1, by1), 16 * s, fill=WHITE)
    for k in range(5): p.rr((bx0, by0 + 8 * s + k * 17 * s, bx1, by0 + 16 * s + k * 17 * s), 2 * s, fill=NAVY)
    p.line([P(-14, -20), P(-24, 40)], WHITE, 18 * s); p.line([P(14, -20), P(26, 40)], WHITE, 18 * s)                    # 脚
    p.line([P(-20, -96), P(-44, -64), P(-30, -84)], NAVY, 15 * s); p.ell((x - 40 * s, y - 96 * s, x - 22 * s, y - 78 * s), fill=BAG)   # 左（構え）
    sx, sy = P(20, -96); gx, gy = sx + (26 + 96 * e) * s, sy + (14 - 14 * e) * s                                           # 右の腕：伸びる
    p.line([(sx, sy), (gx, gy)], NAVY, 15 * s); p.ell((gx - 15 * s, gy - 15 * s, gx + 15 * s, gy + 15 * s), fill=BAG)
    if puzzled > 0.01:
        p.text((hx + 60 * s, hy - 46 * s), "？", int(44 * s), mix(RED, puzzled, SKY))
    return (gx + 15 * s, gy)                                                                                              # グローブの先


def bag(p, cx, top, ang, hit=0.0):
    """吊ったサンドバッグ（ひもとバッグを一つの振り子として、支点のまわりに回す）。ang＝振れ（rad、+ が右）。hit＞0 で当たった光"""
    Lr, w, h = 92, 64, 170
    ux, uy = math.sin(ang), math.cos(ang); vx, vy = math.cos(ang), -math.sin(ang)                    # 下向き（ひもの向き）と右向き
    tx, ty = cx + Lr * ux, top + Lr * uy                                                            # バッグの上の真ん中
    p.line([(cx, top), (tx, ty)], (90, 96, 104), 3)
    def Q(dx, dy): return (tx + dx * vx + dy * ux, ty + dx * vy + dy * uy)
    pts = [Q(-w / 2, 0), Q(w / 2, 0), Q(w / 2, h), Q(-w / 2, h)]
    p.poly(pts, fill=BAG); p.line([pts[0], pts[1]], (150, 50, 42), 6)
    if hit > 0.01:
        hx, hy = Q(-w / 2, 70)
        pts = []
        for k in range(16):
            r = (44 if k % 2 == 0 else 18) * (0.6 + 0.4 * hit); a = k * math.pi / 8; pts.append((hx + r * math.cos(a), hy + r * math.sin(a)))
        p.poly(pts, fill=(255, 230, 90))
    return tx


def phone_land(p, a=1.0, slow=False, caption="", cap_col=TEAL):
    """横向きのスマホのゲーム画面。中の座標（画面の左上）を返す"""
    p.rr((290, 70, 990, 430), 52, fill=mix((29, 34, 40), a))
    p.rr((314, 92, 966, 408), 22, fill=mix(SKY, a)); p.rr((314, 350, 966, 408), 0, fill=mix(GRASS, a))
    p.rr((314, 350, 966, 372), 0, fill=mix(GRASS, a)); p.rr((314, 92, 966, 408), 22, outline=mix((29, 34, 40), a), width=2)
    if slow and a > 0.5:
        p.rr((330, 104, 612, 148), 14, fill=(60, 66, 74)); p.text((471, 126), "ゆっくり再生（10分の1）", 21, WHITE)


def button(p, tap=0.0, a=1.0):
    """「パンチ」のボタンと、押す指（親指の先）"""
    bx, by = 896, 376
    p.ell((bx - 34, by - 34, bx + 34, by + 34), fill=mix(WHITE, a), outline=mix(GRAY, a), width=2); p.text((bx, by), "パンチ", 18, mix(INK, a))
    if tap > 0:
        r = 34 + 40 * tap; p.ell((bx - r, by - r, bx + r, by + r), outline=mix(TEAL, 1 - tap), width=4)


def thumb(p, press):
    """押す指（画面の外の右下から）。press＝0〜1"""
    tx, ty = 940 - 30 * press, 470 - 70 * press
    p.ell((tx - 30, ty - 40, tx + 30, ty + 40), fill=(236, 214, 196), outline=(200, 170, 150), width=2)


def tag(p, xy, txt, col, px=22, a=1.0):
    w = p.d.textlength(txt, font=dg.font(px)) / S; x, y = xy
    p.rr((x - w / 2 - 18, y - px * 0.85, x + w / 2 + 18, y + px * 0.85), 14, fill=mix(WHITE, a), outline=mix(col, a), width=3)
    p.text((x, y), txt, px, mix(col, a))


# ---------------------------------------------------------------- 時間の帯（ゲームの中の実際の秒 → 横の位置）
SX0, SPX = 330, 1500.0                            # 押した所の x、1 秒あたりの px（実際の秒）
SY = 520


def strip(p, a, marks, gap=None, gap_a=0.0, title="", SY=SY, x0=230):
    """marks＝[(実際の秒, ラベル, 色, 形, 出る割合)]。SY：帯の高さ"""
    if a <= 0.01: return
    x1 = 1090
    p.line([(x0, SY), (x1, SY)], mix(GRAY, a), 4); p.poly([(x1 + 16, SY), (x1 - 2, SY - 10), (x1 - 2, SY + 10)], fill=mix(GRAY, a))
    p.text((x1 + 14, SY + 32), "時間", 22, mix(GRAY, a), "rm")
    if title: p.text((x0 - 22, SY), title, 24, mix(INK, a), "rm")              # 帯の名前は帯の左に（上に置くと、ずれの札と並んで読めてしまう）
    for tau, lab, col, kind, u in marks:
        if u <= 0.01: continue
        x = SX0 + tau * SPX; k = a * u
        if kind == "tap":
            p.ell((x - 14, SY - 14, x + 14, SY + 14), fill=mix(col, k)); p.ell((x - 6, SY - 6, x + 6, SY + 6), fill=mix(WHITE, k))
        elif kind == "hit":
            pts = []
            for j in range(10):
                r = 18 if j % 2 == 0 else 8; ang = math.pi / 2 + j * math.pi / 5; pts.append((x + r * math.cos(ang), SY - r * math.sin(ang)))
            p.poly(pts, fill=mix(col, k))
        else:
            p.ell((x - 8, SY - 8, x + 8, SY + 8), fill=mix(col, k))
            for r in (16, 26): p.arc((x, SY), r, -50, 50, mix(col, k), 3)
        p.text((x, SY + 40), lab, 24, mix(col, k))
    if gap and gap_a > 0.01:
        xa, xb = SX0 + gap[0] * SPX, SX0 + gap[1] * SPX; yb = SY - 30; k = a * gap_a
        p.line([(xa, yb), (xb, yb)], mix(RED, k), 3); p.line([(xa, yb - 8), (xa, yb + 8)], mix(RED, k), 3); p.line([(xb, yb - 8), (xb, yb + 8)], mix(RED, k), 3)
        p.text(((xa + xb) / 2, yb - 22), gap[2], 24, mix(RED, k))


# ---------------------------------------------------------------- 場面
def scene_wait(p, t):
    """161：たくさんためてから鳴らすと、押してから音が出るまで長い（時間の帯を二本）"""
    a = win(t, L(161) - 0.3, L(162) - 0.4)
    if a <= 0.01: return
    t0 = L(161) + 0.6; u1 = sm((t - t0) / 0.25); u2 = sm((t - t0 - 0.6) / 0.25); u3 = sm((t - at_char(161, 18)) / 0.3)
    strip(p, a, [(0.0, "▶ 鳴らす", TEAL, "tap", u1), (0.10, "音が出る", GREEN, "snd", u2)], gap=(0.0, 0.10, "少し"), gap_a=u2, title="少しためる", SY=230, x0=250)
    strip(p, a, [(0.0, "▶ 鳴らす", TEAL, "tap", u1), (0.42, "音が出る", GREEN, "snd", u3)], gap=(0.0, 0.42, "待つ時間"), gap_a=u3, title="たくさんためる", SY=440, x0=250)


def scene_tradeoff(p, t):
    """162：待つ余裕を増やすことと、すぐに音が出ることは、いつも両立するとは限らない（てんびん）"""
    a = win(t, L(162) - 0.3, L(163) - 0.4)
    if a <= 0.01: return
    if "A" in SS:                                                   # まるロボの重みで傾く（左の「ためる」→ 右へ渡る → ふり返って首をかしげる）
        balance(p, a, 0, ("ためる", TEAL), ("すぐ音が出る", AMBER), "途切れにくい", "待たない", ang=seesaw_ang("A", t), thick=SS["A"]["thick_px"])
        paste_robot(p, "A", t, a); return
    tilt = 1.0 * sm((t - at_char(162, 4)) / 0.6) - 0.6 * sm((t - at_char(162, 20)) / 0.8)
    balance(p, a, tilt, ("ためる", TEAL), ("すぐ音が出る", AMBER), "途切れにくい", "待たない")


def scene_music(p, t):
    """163：音楽なら、始まりを少し待っても気にならない"""
    a = win(t, L(163) - 0.3, L(164) - 0.4)
    if a <= 0.01: return
    p.rr((560, 130, 720, 400), 26, fill=mix((29, 34, 40), a)); p.rr((574, 146, 706, 384), 14, fill=mix((52, 60, 70), a))
    p.ell((600, 176, 680, 256), fill=mix((170, 200, 230), a)); p.poly([(626, 290), (626, 330), (660, 310)], fill=mix(WHITE, a))
    t_tap = L(163) + 0.8; t_play = t_tap + 1.4
    u_tap = sm((t - t_tap) / 0.2); u_play = sm((t - t_play) / 0.2)
    strip(p, a, [(0.0, "▶ 押す", TEAL, "tap", u_tap), (0.25, "曲が始まる", GREEN, "snd", u_play)], gap=(0.0, 0.25, "少し待つ"), gap_a=u_play, SY=490)


def scene_game(p, t):
    """164〜169：ゲーム画面。ぴったり → 遅れる → 調子が狂う"""
    a = win(t, L(164) - 0.3, L(170) - 0.5)
    if a <= 0.01: return
    case2 = t >= L(166) - 0.4
    t_tap = T_TAP2 if case2 else T_TAP1
    tau, e, th = punch_state(t, t_tap)
    slow = -0.5 < (t - t_tap) < (T_SND2 - T_TAP2 + 1.2 if case2 else 2.4)
    phone_land(p, a, slow=slow and t >= t_tap - 0.5 and a > 0.5)
    ang = bag_angle(th)
    hit = 0.0 if th is None else max(0.0, 1.0 - th / 0.08)
    puzzled = sm((t - L(169)) / 0.4) if case2 else 0.0
    fighter(p, 520, 360, e, 1.0, puzzled=puzzled)
    bag(p, BAG_X, 92, ang, hit * a)
    press = 0.0
    if -0.6 <= t - t_tap <= 0.0: press = sm((t - t_tap + 0.6) / 0.6)
    elif 0.0 < t - t_tap <= 0.8: press = 1.0 - sm((t - t_tap) / 0.8)
    button(p, sm((t - t_tap) / 0.6) if 0 <= t - t_tap <= 0.6 else 0.0, a)
    if a > 0.5 and press > 0.01: thumb(p, press)
    t_snd = (t_tap + EXT * SLOW) if not case2 else T_SND2
    if t >= t_snd and t - t_snd < 1.6:                                                         # 「ドン！」（ゆっくり再生なので 1.6 秒見せる）
        k = 1.0 - sm((t - t_snd - 1.0) / 0.6)
        for r in (52, 74, 96): p.arc((BAG_X + 60, 230), r * (0.8 + 0.2 * sm((t - t_snd) / 0.4)), -40, 40, mix(AMBER, k * a, SKY), 5)
        p.text((875, 150), "ドン！", 40, mix(AMBER, k * a, SKY))
    if case2 and t_tap + EXT * SLOW <= t < T_SND2:                                               # 当たったのに、まだ音がない
        p.text((875, 150), "……", 40, mix(GRAY, a * sm((t - t_tap - EXT * SLOW - 0.3) / 0.4), SKY))
    # 時間の帯
    hit_tau = EXT; snd_tau = EXT if not case2 else EXT + D_LATE
    u_tap = sm((t - t_tap) / 0.25); u_hit = sm((t - t_tap - EXT * SLOW) / 0.25); u_snd = sm((t - t_snd) / 0.25)
    if not case2:
        marks = [(0.0, "押す", TEAL, "tap", u_tap), (hit_tau, "当たる・音（同時）", (220, 170, 30), "hit", u_hit)]
        if u_hit > 0.01: marks.append((hit_tau, "", GREEN, "snd", u_hit))
        strip(p, a * sm((t - t_tap + 0.4) / 0.4), marks, SY=505)                  # 帯の名前は出さない（画面の「ゆっくり再生」と同じこと）
    else:
        marks = [(0.0, "押す", TEAL, "tap", u_tap), (hit_tau, "当たる", (220, 170, 30), "hit", u_hit), (snd_tau, "音", GREEN, "snd", u_snd)]
        strip(p, a * sm((t - t_tap + 0.4) / 0.4), marks, gap=(hit_tau, snd_tau, "ずれ（実際は %.1f 秒ほど）" % D_LATE), gap_a=u_snd, SY=505)


def box(p, c, w, h, title, sub, col, a, icon=None):
    x, y = c
    p.rr((x - w / 2, y - h / 2, x + w / 2, y + h / 2), 18, fill=mix(WHITE, a), outline=mix(col, a), width=4)
    p.text((x, y - 22), title, 32, mix(col, a)); p.text((x, y + 30), sub, 24, mix(INK, a))


def arrow(p, x0, x1, y, a, col=GRAY):
    if a <= 0.01: return
    xe = x0 + (x1 - x0) * a
    p.line([(x0, y), (xe, y)], mix(col, a), 5); p.poly([(xe + 12, y), (xe - 4, y - 11), (xe - 4, y + 11)], fill=mix(col, a))


def scene_flow(p, t):
    """170：ゲームでは、操作してから鳴らす音が決まる"""
    a = win(t, L(170) - 0.3, L(171) - 0.3)
    if a <= 0.01: return
    items = [("押す", "操作", TEAL), ("パンチ！", "音が決まる", AMBER), ("送る", "電波", TEAL), ("鳴る", "イヤホン", GREEN)]
    for k, (ti, su, col) in enumerate(items):
        tk = L(170) + 0.25 + 0.75 * k; u = sm((t - tk) / 0.3)
        x = 220 + k * 280; box(p, (x, 300), 220, 150, ti, su, col, a * u)
        if k < 3: arrow(p, x + 116, x + 164, 300, a * sm((t - tk - 0.3) / 0.35))


def scene_cards(p, t):
    """171：音そのものは用意できる。いつ鳴らすかは、押すまで分からない"""
    a = win(t, L(171) - 0.3, L(172) - 0.4)
    if a <= 0.01: return
    t1 = at_char(171, 0); t2 = at_char(171, 18)
    u1 = sm((t - t1) / 0.35); u2 = sm((t - t2) / 0.35)
    box(p, (400, 300), 400, 230, "パンチの音", "用意できる ✓", GREEN, a * u1)
    box(p, (880, 300), 400, 230, "いつ鳴らす？", "押すまで分からない", RED, a * u2)


def scene_queue(p, t):
    """172：その音を長く待たせれば、操作した瞬間と、聞こえる瞬間が離れる（イヤホンの中の待ち行列）"""
    a = win(t, L(172) - 0.3, L(173) - 0.4)
    if a <= 0.01: return
    n = 1 + int(min(4, max(0, (t - L(172) - 0.6) / 1.1)))                                     # 待っている荷物が増える（1 → 5）
    for k in range(5):
        x = 330 + k * 92; on = k < n
        p.rr((x - 40, 210, x + 40, 274), 10, fill=mix(TEAL if on else WHITE, a), outline=mix(TEAL, a), width=3)
        if on: p.text((x, 242), "%02d" % (k + 1), 24, mix(WHITE, a))
    x = 330 + n * 92                                                                            # 一番後ろにパンチの音
    p.rr((x - 40, 210, x + 40, 274), 10, fill=mix(BAG, a)); p.text((x, 242), "ドン", 24, mix(WHITE, a))
    p.text((290, 168), "イヤホンの中で、順番を待っている分", 24, mix(INK, a), "lm"); p.text((282, 242), "←", 30, mix(GRAY, a))
    p.text((330, 306), "先に鳴る", 22, mix(GRAY, a))
    d = 0.06 * (n + 1)
    strip(p, a, [(0.0, "押す", TEAL, "tap", 1.0), (d, "聞こえる", GREEN, "snd", 1.0)], gap=(0.0, d, "ずれ"), gap_a=1.0, SY=470)


def scene_future(p, t):
    """173：まだしていない操作の音を、先に全部ためておくわけにはいかない"""
    a = win(t, L(173) - 0.3, L(174) - 0.4)
    if a <= 0.01: return
    for k in range(5):
        x = 330 + k * 150; u = sm((t - L(173) - 0.3 - 0.25 * k) / 0.3)
        p.rr((x - 52, 260, x + 52, 340), 14, fill=mix(WHITE, a * u), outline=mix(RED, a * u), width=3); p.text((x, 300), "？", 34, mix(RED, a * u))
    p.text((640, 398), "これからの操作（いつ・何を押すか、まだ分からない）", 26, mix(INK, a))


def balance(p, a, tilt, left, right, lab_l, lab_r, ang=None, thick=7):
    cx, cy = 640, 300; Lb = 300; ang = math.radians(9 * tilt) if ang is None else ang
    p.poly([(cx, cy), (cx - 40, cy + 130), (cx + 40, cy + 130)], fill=mix((120, 128, 136), a))
    xl, yl = cx - Lb * math.cos(ang), cy + Lb * math.sin(ang); xr, yr = cx + Lb * math.cos(ang), cy - Lb * math.sin(ang)
    p.line([(xl, yl), (xr, yr)], mix(INK, a), thick); p.ell((cx - 11, cy - 11, cx + 11, cy + 11), fill=mix(INK, a))
    for (x_, y_), (txt, col), lab in (((xl, yl), left, lab_l), ((xr, yr), right, lab_r)):
        p.line([(x_, y_), (x_, y_ + 60)], mix(GRAY, a), 3)
        p.rr((x_ - 165, y_ + 60, x_ + 165, y_ + 136), 18, fill=mix(WHITE, a), outline=mix(col, a), width=4); p.text((x_, y_ + 98), txt, 30, mix(col, a))
        p.text((x_, y_ + 168), lab, 26, mix(col, a))


def seesaw_i(sc, t):
    J = SS[sc]; return max(0, min(J["n"] - 1, int(round((t - J["t0"]) * J["fps"]))))


def seesaw_ang(sc, t):
    """まるロボの重みで傾いた角度（図の向き：＋＝左の端が下がる）"""
    return -SS[sc]["beta"][seesaw_i(sc, t)]


def paste_robot(p, sc, t, a):
    """まるロボの透明な絵を、支点の中心（世界の原点）に合わせて重ねる"""
    J = SS[sc]; fp = os.path.join(SS_DIR, sc, "f_%04d.png" % (seesaw_i(sc, t) + 1))
    if a <= 0.01 or not os.path.exists(fp) or os.path.getsize(fp) == 0 or not hasattr(p, "im"): return
    spr = Image.open(fp).convert("RGBA"); r_ = spr.size[0] / J["res"][0]
    k = (J["pxm"] * S) / (J["rpxm"] * r_)                           # 下地の 1 px あたりの、絵の px
    spr = spr.resize((max(1, int(round(spr.size[0] * k))), max(1, int(round(spr.size[1] * k)))), Image.LANCZOS)
    ox, oy = J["origin"][0] * r_ * k, J["origin"][1] * r_ * k
    al = spr.getchannel("A")
    if a < 0.999: al = al.point(lambda v, a=a: int(v * a))
    p.im.paste(spr.convert("RGB"), (int(round(640 * S - ox)), int(round(300 * S - oy))), al)


def scene_both(p, t):
    """174〜176：音が途切れにくいこと・すぐ返ってくること・両方を考える"""
    a = win(t, L(174) - 0.3, L(177) - 0.4)
    if a <= 0.01: return
    if "B" in SS:                                                   # まるロボの重みで傾く（左 → 右へ走って、おっとっと → 真ん中で釣り合う）
        balance(p, a, 0, ("途切れにくい", TEAL), ("すぐ返ってくる", AMBER), "音楽を聴く", "ゲーム", ang=seesaw_ang("B", t), thick=SS["B"]["thick_px"])
        paste_robot(p, "B", t, a); return
    tilt = 1.0 * sm((t - L(174)) / 0.4) - 2.0 * sm((t - L(175)) / 0.4) + 1.0 * sm((t - L(176)) / 0.6)
    balance(p, a, tilt, ("途切れにくい", TEAL), ("すぐ返ってくる", AMBER), "音楽を聴く", "ゲーム")


def scene_bars(p, t):
    """177：実際の遅れは、機器や通信の方式によっても変わる（棒はたとえ）"""
    a = win(t, L(177) - 0.3, T_B + 0.2)
    if a <= 0.01: return
    for k, (lab, w_) in enumerate((("機器 A", 640), ("機器 B", 430), ("機器 C", 270))):
        y = 250 + k * 92; u = sm((t - L(177) - 0.3 - 0.3 * k) / 0.5)
        p.text((300, y), lab, 28, mix(INK, a), "rm"); p.rr((330, y - 24, 330 + w_ * u, y + 24), 10, fill=mix((200, 210, 216), a))
    p.text((640, 520), "（棒の長さは、たとえ）", 22, mix(GRAY, a))


def frame(t):
    im = Image.new("RGB", (W * S, H * S), BG); p = Pen(ImageDraw.Draw(im)); p.im = im      # p.im：まるロボの絵を重ねる下地
    scene_wait(p, t); scene_tradeoff(p, t); scene_music(p, t); scene_game(p, t); scene_flow(p, t); scene_cards(p, t); scene_queue(p, t); scene_future(p, t); scene_both(p, t); scene_bars(p, t)
    return im.resize(dg.OUT_WH, Image.LANCZOS)


def events():
    """効果音の時刻（本編の秒）：押す・当たる・ドン（ぴったり／遅れて）"""
    ev = [dict(kind="tap", t=T_TAP1), dict(kind="hit", t=T_TAP1 + EXT * SLOW), dict(kind="don", t=T_TAP1 + EXT * SLOW),
          dict(kind="tap", t=T_TAP2), dict(kind="hit", t=T_TAP2 + EXT * SLOW), dict(kind="don", t=T_SND2)]
    return ev


if __name__ == "__main__":
    out = sys.argv[1]
    if "--still" in sys.argv:
        for s_ in sys.argv[sys.argv.index("--still") + 1].split(","): frame(float(s_)).save(os.path.join(out, "g8_%07.2f.png" % float(s_)))
        print("D_LATE %.3f s  T_TAP1 %.2f  T_TAP2 %.2f  T_SND2 %.2f" % (D_LATE, T_TAP1, T_TAP2, T_SND2))
    else:
        gd = os.path.join(out, "game"); os.makedirs(gd, exist_ok=True); n = int(round((T_B - T_A) * FPS))
        for i in range(n):
            fp = os.path.join(gd, "g_%04d.png" % (i + 1))
            if os.path.exists(fp) and "--redo" not in sys.argv: continue
            im_ = frame(T_A + i / FPS)
            if "--small" in sys.argv: im_ = im_.resize((640, 360), Image.LANCZOS)     # 確認用（低画質の組み立てと同じ大きさ）
            im_.save(fp, compress_level=1)
        json.dump(dict(t0=T_A, t1=T_B, fps=FPS, frames=n, events=events(), d_late=D_LATE), open(os.path.join(out, "ch08_game.json"), "w"), indent=0)
        print("GAME", n, "frames")
