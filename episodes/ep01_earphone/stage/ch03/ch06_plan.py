# 第6章「送り直し（再送）」（本編 10:54.7〜12:10.4、台本 v2 の 114〜127）のまるロボの予定と時刻
#   第3章の舞台（ch03_plan の配置）をそのまま使う。06 を二回運ぶ：1回目は誤り（受付の灯が赤）、2回目は受け取れた（灯が緑）
#   道のりはカットでつなぐ（時間を飛ばす。第3章と同じ）。受付ボックスでは、台に背を向けて寄せ終わった所から見せる
#   時刻はナレーションの声の置き場所（stage/voice/achernar/placement.json）から決める。予定の 0 秒 ＝ 本編 T0
import math, os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import marumotion as mm
import ch03_plan as c3

PLC = {p["no"]: p for p in json.load(open(os.path.join(HERE, "..", "voice", "achernar", "placement.json"), encoding="utf-8"))}
def L(n): return PLC[n]["start"]
def LE(n): return PLC[n]["end"]
T0 = L(114) - 0.3                            # 予定の 0 秒（本編）
T_IN = L(128) - 0.3                          # 「それではここからは、イヤホンの中を見てみましょう」：耳の先（音の出口）へ飛び込む
T1 = L(129) - 0.6                            # 第6章の終わり＝耳の先の中（暗い網）で、第7章のイヤホンの中へ切り替える
def A(t_abs): return t_abs - T0              # 本編 → 予定

# ---------------------------------------------------------------- 出来事の時刻（本編の秒）
T_LOAD1 = L(115) - 0.30                      # 「今度は、この六番の荷物を追いかけます」の頭で 06 を積み始める（積み終わり 3.75 秒後が、受付ボックスへ切り替える前）
T_BOX1 = L(116) - 0.20                       # 受付ボックスへ（時間を飛ばす）：台に背を向けて寄せ終わった所
UNLOAD_WAIT, UNLOAD_T = 0.8, 2.2             # 腕がトレーをつかむまで・引き込む時間（第3章と同じ）
T_SCAN1 = T_BOX1 + UNLOAD_WAIT + UNLOAD_T + 0.15   # 荷物がボックスの中に入ったら、光がなぞる（「誤りがないかを確かめます」）
SCAN_T = 1.4                                 # なぞる光が荷物の端から端まで（1.4秒）
T_RED = L(118) + 0.15                        # 「今回は、正しく受け取れませんでした」：灯が赤
T_RING0, T_RING1 = L(119) + 0.45, L(119) + 3.95   # 「返事が来ないので…」：スマホの返事ランプのまわりの輪が一周（待ち時間）
T_LOST = T_RING1 + 0.15                      # 輪が一周しても返事がない →「？」
T_WB0 = L(119) + 6.1                         # まるロボがスマホへ戻る（細い橋を、来た道と逆の向きに渡る）のカット
T_WB_HIT = T_WB0 + 1.2                       # その時刻に、橋のイヤホン側の入り口から 0.55m を通る
T_BACK = L(120) - 0.3                        # 次のカット（窓の前）から後半の予定に切り替える（スマホへ戻り終えている）
T_LOAD2 = T_BACK + 0.10                      # 「そこで、同じ六番を、もう一度」：残しておいた 06 を積む（押し終わり 3.15 秒後）
T_S7B = T_LOAD2 + 1.75                       # 横からの絵へ（押し出しの途中）
T_WALK2 = L(121) + 1.75                      # 「送り直します」：道のりのカット（細い橋を渡る）。この時刻に入り口から 0.55m
T_S8 = T_WALK2 - 1.0
T_BOX2 = L(121) + 4.6                        # 受付ボックスへ
T_SCAN2 = T_BOX2 + UNLOAD_WAIT + UNLOAD_T + 0.15
T_GREEN = L(122) + 0.10                      # 「今度は、受け取れました」：灯が緑
T_REPLY0, T_REPLY1 = T_GREEN + 0.70, T_GREEN + 3.40   # 返事の光：受付の灯 → スマホの返事ランプ（約 71m を 2.7秒）
T_LAMP_OK = T_REPLY1 + 0.05                  # スマホの返事ランプが緑（届いたよ）
T_S10 = T_GREEN + 0.55                       # 返事の光を追うカット
T_S11 = L(123) - 0.3                         # 「再送」（引き）：この間に、残しておいた 06 は窓から片付く（見えない所で）
T_DROP = T_S11 + 0.3
T_S12 = L(124) - 0.3                         # 窓：07・08 が前へ進む
T_ADV = T_S12 + 1.2
T_GROOVE = L(125) - 0.4                      # 「ところで、今の音楽、聞いていましたか？」：曲に合わせて揺れる（曲はずっと鳴っていた）
BEAT = 0.385                                 # 曲の1拍（156BPM）。曲の 40.04 秒からの 3.08 秒（8拍）は、そのままくり返せる（継ぎ目なし。一致度 1.000）
GROOVE_BPM = 60.0 / (2 * BEAT)               # 2拍に1回沈む。曲の拍の頭は、揺れ始め（T_GROOVE）から BEAT ごと（ch06_assemble.py が合わせる）


def gap_x_end():
    """受付の台の寸法から、降ろすときの gap と引き込み終わり（第3章と同じ式）"""
    gap = c3.DOCK["near"] + float(mm.CRADLE[1]) - mm.CRADLE_FRONT
    y_cr = c3.BOOTH["depth"] + c3.DOCK["outside"] + c3.DOCK["near"] + float(mm.CRADLE[1])
    x_end = (0.12 + 0.04 + mm.CARGO_HALF[0]) - y_cr
    return gap, x_end


def ch06_plan():
    """→ (前半, 後半)。荷物の動き（積む・降ろす）は一つの予定で一回ずつしか計算できないので、二回目は別の予定にして T_BACK でつなぐ
    前半：06 を積む → 受付ボックスで降ろす → 光がなぞる → 灯が赤（荷物はボックスの中のまま。後半では見えない）
    後半：スマホの前で、残しておいた 06 をもう一度積む → 受付ボックスで降ろす → 灯が緑 → 曲に合わせて揺れる（同じ時刻の目盛り）"""
    gap, x_end = gap_x_end()
    p = mm.Plan(pos=tuple(c3.L), heading=math.degrees(c3.psi1), seed=61)
    p.idle(A(T_LOAD1), shifts=True)                                          # 窓の前で待つ（窓の中に 06・07・08）
    p.load_back(T=2.2, label="06 を積む")
    p.event(p.t + 0.25, "beep_yes", 1.0)
    p.idle(max(A(T_BOX1) - p.t, 0.05), shifts=False, glance=False)
    p.teleport(tuple(c3.U), c3.heading_of(c3.NG))                              # 受付ボックス：台に背を向けて寄せ終わった所（時間を飛ばす）
    p.unload_pull(T=UNLOAD_T, gap=gap, conv=c3.DOCK["v"], run=0.0, wait=UNLOAD_WAIT, x_end=x_end, label="降ろす（1回目）")
    p.look(0.0, 12.0, hold=0.3)
    p.idle(max(A(T_RED) - 0.2 - p.t, 0.05), shifts=False, glance=False)
    p.look(0.0, 18.0, hold=1.2)                                              # 灯を見上げる（赤）
    p.idle(max(A(T_BACK) - p.t + 1.0, 0.05), shifts=False, glance=False)
    q = mm.Plan(pos=tuple(c3.L), heading=math.degrees(c3.psi1), seed=62)        # 後半：スマホの前へ戻っている（時間を飛ばす）
    q.idle(A(T_LOAD2), shifts=True)
    q.load_back(T=2.2, label="残しておいた 06 をもう一度積む")
    q.event(q.t + 0.25, "beep_yes", 1.0)
    q.idle(max(A(T_BOX2) - q.t, 0.05), shifts=False, glance=False)
    q.teleport(tuple(c3.U), c3.heading_of(c3.NG))
    q.unload_pull(T=UNLOAD_T, gap=gap, conv=c3.DOCK["v"], run=0.0, wait=UNLOAD_WAIT, x_end=x_end, label="降ろす（2回目）")
    q.look(0.0, 12.0, hold=0.3)
    q.idle(max(A(T_GREEN) - 0.2 - q.t, 0.05), shifts=False, glance=False)
    q.look(0.0, 18.0, hold=1.0)                                              # 灯を見上げる（緑）
    q.idle(max(A(T_GROOVE) - q.t, 0.05), shifts=False, glance=False)
    q.groove(dur=max(A(T1) - q.t + 0.5, 2.0), bpm=GROOVE_BPM, label="曲に合わせて揺れる")
    return p, q


def _bridge_walk(t_at, s_at, s0, s1, back, carry, seed):
    """細い橋を歩くカット：t_at（予定の時刻）に s_at を通るよう、s0 から s1 へ。back＝スマホへ戻る向き"""
    hd = math.degrees(c3.psi1) + (180.0 if back else 0.0)
    def build(t_idle):
        q = mm.Plan(pos=tuple(c3.RP(s0)), heading=hd, carry=carry, seed=seed)
        q.idle(t_idle, shifts=False, glance=False); q.walk_to(tuple(c3.RP(s1)), speed=0.8); q.idle(1.0, shifts=False, glance=False)
        return q
    q = build(1.0); fr = mm.simulate(q)
    ss = np.array([float((np.array(f["root"][:2]) - c3.L) @ c3.F) for f in fr]); tt = np.array([f["t"] for f in fr])
    if back: ss = -ss
    t_hit = float(np.interp(-s_at if back else s_at, ss, tt))
    return build(1.0 + (t_at - t_hit))


def walk_plan():
    """「送り直します」：道のりのカット（細い橋をイヤホンへ）。T_WALK2 に橋のスマホ側の入り口から 0.55m を通る"""
    return _bridge_walk(A(T_WALK2), c3.BRIDGE["s0"] + 0.55, c3.BRIDGE["s0"] - 2.6, c3.BRIDGE["s1"] + 3.0, False, True, 63)


def walk_back_plan():
    """返事が来ない → まるロボはスマホへ戻る：細い橋をスマホへ（荷物なし）。T_WB_HIT に橋のイヤホン側の入り口から 0.55m を通る"""
    return _bridge_walk(A(T_WB_HIT), c3.BRIDGE["s1"] - 0.55, c3.BRIDGE["s1"] + 2.6, c3.BRIDGE["s0"] - 3.0, True, False, 64)


def montages():
    """道のりのカット：(本編の始まり, 終わり, 予定, 名前)。その時間だけ、この予定の姿勢に差し替える（荷物は本筋の予定のまま）"""
    return [(T_WB0, T_BACK, walk_back_plan(), "WB"), (T_S8, T_BOX2, walk_plan(), "S8")]


SHOTS = [(T0, "S1 引き：スマホと巨大イヤホン"), (L(115) - 0.25, "S2 窓の中の 06・07・08（06 を積む）"), (L(115) + 1.75, "S2b 横から：06 を積む"),
         (T_BOX1, "S3a 引き：巨大イヤホン（受け取る側）"), (L(116) + 1.30, "S3 受付ボックス：光がなぞる"), (L(117) - 0.2, "S4 受け取れたら返事（説明）"), (L(118) - 0.3, "S5 今回は誤り（灯が赤）"),
         (L(119) - 0.3, "S6 スマホの返事ランプ：待ち時間の輪 →「？」"), (T_WB0, "S6b スマホへ戻る（細い橋）"), (T_BACK, "S7 残しておいた 06 をもう一度積む"),
         (T_S7B, "S7b 横から：積む"), (T_S8, "S8 道のり（細い橋）"), (T_BOX2, "S9 受付ボックス：降ろす → 光 → 灯が緑"), (T_S10, "S10 返事の光がスマホへ"), (T_REPLY1 - 0.41, "S10b スマホの返事ランプ：緑（S6 と同じ向き）"),
         (T_S11, "S11 再送"), (T_S12, "S12 06×→06✓→07→08"), (T_GROOVE - 0.1, "S13 曲はずっと鳴っていた（まるロボが揺れる）"),
         (L(126) - 0.2, "S14 引き：巨大イヤホン"), (L(127) - 0.2, "S15 巨大イヤホンへ寄る →「？」"), (T_IN, "S16 耳の先（音の出口）へ飛び込む")]


if __name__ == "__main__":
    p, q = ch06_plan()
    print("T0 %.2f  T1 %.2f  前半の終わり %.2f  後半の終わり %.2f  つなぐ T_BACK %.2f" % (T0, T1, p.t + T0, q.t + T0, T_BACK))
    fp = mm.simulate(p); fq = mm.simulate(q)
    for pl_ in (p, q):
        for a, b, txt in pl_.labels: print("  %6.2f-%6.2f (本編 %7.2f-%7.2f) %s" % (a, b or -1, a + T0, (b or -1) + T0, txt))
        ld = pl_.loads[0]; un = pl_.unloads[0]
        print("  load t0 %.2f tp %.2f t_end %.2f (本編 %.2f-%.2f) | unload t0 %.2f tp %.2f t_end %.2f (本編 %.2f-%.2f)" % (ld["t0"], ld["tp"], ld["t_end"], ld["tp"] + T0, ld["t_end"] + T0, un["t0"], un["tp"], un["t_end"], un["tp"] + T0, un["t_end"] + T0))
        print("  beeps", [round(e["t"] + T0, 2) for e in pl_.events if e["kind"] == "beep_yes"])
    print("scan1 %.2f red %.2f ring %.2f-%.2f wb %.2f back %.2f load2 %.2f s7b %.2f s8 %.2f walk %.2f box2 %.2f scan2 %.2f green %.2f reply %.2f-%.2f s10 %.2f s11 %.2f s12 %.2f groove %.2f"
          % (T_SCAN1, T_RED, T_RING0, T_RING1, T_WB0, T_BACK, T_LOAD2, T_S7B, T_S8, T_WALK2, T_BOX2, T_SCAN2, T_GREEN, T_REPLY0, T_REPLY1, T_S10, T_S11, T_S12, T_GROOVE))
    iB = int(round(A(T_BACK) * 60))
    print("前半の荷物（つなぐ前）", fp[min(iB - 1, len(fp) - 1)]["cargo"][0], "後半の荷物（つないだ後）", fq[iB]["cargo"][0])
    for a_, b_, w, nm in montages():
        fw = mm.simulate(w)
        ss = [round(float((np.array(f["root"][:2]) - c3.L) @ c3.F), 2) for f in fw if A(a_) <= f["t"] <= A(b_)]
        print("montage %s %.2f-%.2f along route %s → %s" % (nm, a_, b_, ss[0] if ss else None, ss[-1] if ss else None))
    for t_, nm in SHOTS: print("  %7.2f %s" % (t_, nm))
