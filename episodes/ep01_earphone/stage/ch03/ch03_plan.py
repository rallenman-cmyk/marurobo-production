# 第3章「音楽を届ける、小さな旅」舞台の部分（C3〜C11）の配置と、まるロボの予定
#   v2（長い道）：巨大イヤホンは 2 倍の大きさで、スマホから約 75m 先。道のりは短いカットでつなぐ（時間を飛ばす）
#     M1 段差の台に跳び乗る → M2 溝を跳び越える → M3 運河の細い橋を渡る → C10 受付ボックスに着く
#   障害物は「ふつうの地形」だけ（電波のじゃまや遅れを思わせない）。どれも一度で、すっと越える
# 時刻 0 ＝ 本編 100.2 秒（C3 の始まり）。Blender の外でも中でも同じ予定を使う
import math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import marumotion as mm

T0 = 100.2                                   # 本編での時刻のずれ
# 台本 v2（2026-11-06 確定）の時刻：23「…番号は、曲の順番です」で 2.2 秒、24「電波の代わりに、配達をお願いするのは、まるロボです」で 1.6 秒延びた。
#   C4（窓の中の荷物）は 105.4〜111.7 秒、あいさつは「まるロボです」（115.3 秒）の 1 秒前から、25「目指すのは」（121.0 秒）から後は v1 より +3.8 秒
DV2 = 3.8


def heading_of(v):
    """向きベクトル → marumotion の向き（度）。fwd(psi) = (−sin psi, cos psi)"""
    return math.degrees(math.atan2(-v[0], v[1]))


def A(t_abs): return t_abs - T0               # 本編の時刻 → 予定の時刻


# ---------------------------------------------------------------- 出発点（スマホの積み込み口の前）。前の版と同じ場所
_E0 = np.array([0.0, 11.12]); _NG0 = np.array([math.cos(math.radians(235.0)), math.sin(math.radians(235.0))])
psi1 = math.radians(heading_of(np.array([math.cos(math.radians(85.0)), math.sin(math.radians(85.0))])))   # −5°
F = mm.fwd(psi1); R = mm.rgt(psi1)          # 道の前・右
L = (_E0 + _NG0 * 6.6) - F * 3.4             # 出発点
PHONE_BACK = 1.15


def RP(s, r=0.0):
    """道の座標（出発点から前へ s・右へ r）→ 世界の (x, y)"""
    return L + F * s + R * r


# ---------------------------------------------------------------- 巨大イヤホン（2倍）と受付ボックス
EB_SCALE = 2.0                               # Codex版の 2 倍（高さ約 36m）
EB_SRC = np.array([0.0, 11.12])              # Codex版の軸の位置（足もと）
EB_SRC_Z = 0.36                              # Codex版の軸の先（いちばん下）の高さ
EB_TIP_SRC = math.pi                         # Codex版で耳の先が向く向き（−X）
R_STEM = 1.40 * EB_SCALE                     # 軸の半径（足もと）
BOOTH = dict(width=1.9, height=2.3, depth=1.0, open_w=1.30, open_h=0.95)   # 受付ボックス（軸に付く）
DOCK = dict(near=0.35, depth=1.5, height=1.12, width=1.2, mu=0.35, v=0.50, lip=0.10, outside=0.6)   # 受け取り台：外に0.6m、ボックスの中に0.9m
S_U = 70.0                                   # 降ろす所（ロボの中心）の道の上の距離
U = RP(S_U)
NG = -F                                      # 受付ボックスの向き（来た道のほうを向く）
G_ANG = math.atan2(NG[1], NG[0])
E = U - NG * (R_STEM + BOOTH["depth"] + DOCK["outside"] + DOCK["near"])   # 軸の中心
EB_ROT = math.atan2(NG[1], NG[0]) - EB_TIP_SRC   # 耳の先を、来た道（スマホ）のほうへ向ける。図（C13）と同じ形
U_TURN = U + NG * 0.38                       # 向きを変える所。荷物の角（中心から0.62m）が回る円が、台の手前の端から9cm離れる
P1 = RP(3.4)                                 # （前の版の名残）

# ---------------------------------------------------------------- 道の地形（道の座標）
TERRACE = dict(s0=18.0, s1=40.0, half=6.0, h=0.30)          # 段差の台（石）：高さ 30cm
GROOVE = dict(s0=29.0, s1=29.5)                              # 台を横切る溝：幅 50cm（底は地面）
CANAL = dict(s0=56.0, s1=60.0, depth=1.6, half=400.0)        # 運河（水なし）：幅 4m・深さ 1.6m
BRIDGE = dict(s0=55.6, s1=60.4, w=0.9, thick=0.15)           # 細い橋：幅 0.9m（両足の外側どうしは約 0.66m）

# ---------------------------------------------------------------- カットの時刻（本編）
T_C9A, T_M1, T_M2, T_M3, T_C10 = 127.9 + DV2, 130.4 + DV2, 132.7 + DV2, 135.0 + DV2, 137.0 + DV2
T_STOP = 138.40 + DV2                        # 受付ボックスの前で止まる（「到着しました」142.7 の少し前）


def _jump_shot(t_stop, s_stop, z0, s_land, z1, seed):
    """t_stop（予定の時刻）に s_stop で止まり、跳ぶ。止まる 2.0m 手前から歩いてくる（カットの前から動いている）"""
    def build(t_idle):
        p = mm.Plan(pos=tuple(RP(s_stop - 2.0)), heading=math.degrees(psi1), ground=z0, carry=True, seed=seed)
        p.idle(t_idle, shifts=False, glance=False)
        p.walk_to(tuple(RP(s_stop)), speed=mm.V_WALK); ts = p.t
        p.jump_to(tuple(RP(s_land)), z1=z1)
        p.idle(1.5, shifts=False, glance=False)
        return p, ts
    _, ts0 = build(1.0)
    return build(1.0 + (t_stop - ts0))[0]


def _walk_shot(t_at, s_at, s0, s1, speed, seed, z0=0.0):
    """t_at（予定の時刻）に s_at を通るように、s0 から s1 へ歩く"""
    def build(t_idle):
        p = mm.Plan(pos=tuple(RP(s0)), heading=math.degrees(psi1), ground=z0, carry=True, seed=seed)
        p.idle(t_idle, shifts=False, glance=False)
        p.walk_to(tuple(RP(s1)), speed=speed)
        p.idle(1.0, shifts=False, glance=False)
        return p
    p = build(1.0); fr = mm.simulate(p)
    ss = np.array([float((np.array(f["root"][:2]) - L) @ F) for f in fr]); tt = np.array([f["t"] for f in fr])
    t_hit = float(np.interp(s_at, ss, tt))
    return build(1.0 + (t_at - t_hit))


def montage_plans():
    """道のりのカット：(本編の始まり, 終わり, 予定, 名前)。それぞれ別の予定で動かし、その時間だけ使う"""
    m1 = _jump_shot(A(T_M1) + 0.35, TERRACE["s0"] - 0.30, 0.0, TERRACE["s0"] + 0.32, TERRACE["h"], 31)
    m2 = _jump_shot(A(T_M2) + 0.35, GROOVE["s0"] - 0.30, TERRACE["h"], GROOVE["s1"] + 0.18 + 0.10, TERRACE["h"], 32)
    m3 = _walk_shot(A(T_M3) + 0.2, BRIDGE["s0"] + 0.55, BRIDGE["s0"] - 2.6, BRIDGE["s1"] + 3.0, 0.8, 33)
    return [(T_M1, T_M2, m1, "M1"), (T_M2, T_M3, m2, "M2"), (T_M3, T_C10, m3, "M3")]


def ch03_plan():
    p = mm.Plan(pos=tuple(L), heading=math.degrees(psi1), seed=21)
    p.idle(A(114.3), label=None)                                     # C3・C4：窓の前で待つ（荷物は後ろの台の上）。v2：あいさつは「まるロボです」の 1 秒前
    p.greet(label="あいさつ")                                         # C5「配達をお願いするのは、まるロボです」
    p.idle(A(119.1 + DV2) - p.t, shifts=True)
    t_awe = p.t
    p.awe(dur=2.9, pitch=22.0, label="見上げる")                       # C6〜C7「目指すのは、あのイヤホン。……ずいぶん大きく見えますね」（遠くの巨大イヤホンを見上げる）
    for e in p.events:
        if e["kind"] == "beep_wow" and e["t"] >= t_awe: e["t"] = round(A(119.55 + DV2), 4)   # 「……」の間に感心の音
    p.idle(A(122.4 + DV2) - p.t, shifts=False)
    p.load_back(T=2.2, label="積む")                                  # C8（間）積み込み
    p.event(p.t + 0.25, "beep_yes", 1.0)
    p.idle(A(127.9 + DV2) - p.t, shifts=False)
    p.walk_to(tuple(RP(5.0)), speed=mm.V_WALK, label="出発")          # C9a「音楽の荷物を載せて、出発です」（カットの外で止まる）
    p.idle(A(T_M3) - p.t, shifts=False, glance=False)
    # ---- 道のりは別の予定（montage_plans）。この予定は、見えない間に受付ボックスの手前へ移る
    d_in = 1.8
    p.teleport(tuple(U_TURN - F * d_in), math.degrees(psi1))
    def arrive(t_idle):                                              # 止まるまでの時間（同じ歩き方を、別の予定で試す）
        q = mm.Plan(pos=tuple(U_TURN - F * d_in), heading=math.degrees(psi1), carry=True)
        q.idle(t_idle, shifts=False, glance=False); q.walk_to(tuple(U_TURN), speed=mm.V_WALK); return q.t
    t_idle = max(0.05, 0.5 + (A(T_STOP) - A(T_M3) - arrive(0.5)))
    p.idle(t_idle, shifts=False, glance=False)
    p.walk_to(tuple(U_TURN), speed=mm.V_WALK, label="受付口へ")        # 台の手前 0.38m で止まる（ここなら回っても荷物の角が台に当たらない）
    t_arrive = p.t                                                   # C10「到着しました」
    p.turn_to(heading_of(NG), label="向きを変える")                     # 台に背を向ける
    p.back_to(tuple(U), label="後ずさり")                              # 肩ごしに後ろを見て、足踏みで台へ寄せる
    gap = DOCK["near"] + float(mm.CRADLE[1]) - mm.CRADLE_FRONT        # 受け皿の後ろの端 → 台の手前の端
    y_cr = BOOTH["depth"] + DOCK["outside"] + DOCK["near"] + float(mm.CRADLE[1])   # 受け皿の中心（ボックスの軸の面から外へ）
    x_end = (0.12 + 0.04 + mm.CARGO_HALF[0]) - y_cr                  # 引き込み終わり：ボックスの奥の壁（0.12）の 4cm 手前
    p.unload_pull(T=2.2, gap=gap, conv=DOCK["v"], run=0.0, wait=0.8, x_end=x_end, label="降ろす")   # 台の左右の腕がトレーの横をつかみ、ボックスの中まで引き込む
    p.look(0.0, 12.0, hold=0.3)
    p.groove(dur=max(A(150.2 + DV2) - p.t, 2.0), bpm=96.0, label="曲を聴く")   # C11（曲が流れる）
    return p, t_arrive


if __name__ == "__main__":
    p, ta = ch03_plan()
    fr = mm.simulate(p)
    print("L", L.round(2), "U", U.round(2), "E", E.round(2), "psi1 %.1f" % math.degrees(psi1), "EB_ROT %.1f" % math.degrees(EB_ROT))
    print("plan end %.2f s (本編 %.2f)  arrive %.2f (本編 %.2f)" % (p.t, p.t + T0, ta, ta + T0))
    for a, b, txt in p.labels: print("  %6.2f-%6.2f (本編 %6.2f-%6.2f) %s" % (a, b or -1, a + T0, (b or -1) + T0, txt))
    un = p.unloads[0]; print("unload t0 %.2f tp %.2f t_end %.2f (本編 tp %.2f t_end %.2f) x1 %.2f" % (un["t0"], un["tp"], un["t_end"], un["tp"] + T0, un["t_end"] + T0, un["x1"]))
    for a, b, q, nm in montage_plans():
        fq = mm.simulate(q); ev = [(round(e["t"] + T0, 2), e["kind"]) for e in q.events if e["kind"] in ("takeoff", "land")]
        ss = [round(float((np.array(f["root"][:2]) - L) @ F), 2) for f in fq if A(a) <= f["t"] <= A(b)]
        print("%s %.1f-%.1f s along route %s → %s" % (nm, a, b, ss[0] if ss else None, ss[-1] if ss else None), ev)
