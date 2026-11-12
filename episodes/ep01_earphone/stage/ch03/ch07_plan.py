# 第7章「イヤホンの中：バッファ」（本編 12:15.2〜14:39.2、台本 v2 の 129〜152）の予定と時刻（Blender の外でも中でも同じ予定を使う）
#   イヤホンの中の貯蔵タワー：下の再生装置の口に、いま鳴っている荷物がゆっくり沈んでいく（鳴らした分だけ減る）。待っている荷物はその上に積み重なり、
#   いっしょに下がっていく（すき間なく次へ：曲は途切れない）。新しい荷物は、受付ボックスから昇降機で上がってきて、塔の上の扉から入り、
#   塔の内側のブレーキ（速さに比例する抵抗：うず電流）で、ゆっくり落ちて積み重なる
#   前半（A）：04 が鳴り、05 が待つ → 05 へ → 06 が届く（間に合う）→ バッファ → 07 は少し遅れて届く
#   後半（B）：09 が届かない。07・08 が減っていき、最後の一つが終わると、再生装置が空になって音が止まる
#   時刻はナレーションの声の置き場所（stage/voice/achernar/placement.json）から決める。予定の 0 秒 ＝ 本編 T0
import math, os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ch06_plan as p6

PLC = {p["no"]: p for p in json.load(open(os.path.join(HERE, "..", "voice", "achernar", "placement.json"), encoding="utf-8"))}
def L(n): return PLC[n]["start"]
def LE(n): return PLC[n]["end"]
T0 = p6.T1                                   # 第6章の終わり（耳の先の口の中）＝第7章の始まり（本編 735.18）
T1 = L(153) - 0.3                            # 3D はここまで（このあとは二つを並べた図と、電車の画）
def A(t_abs): return t_abs - T0

G = 9.81
# ---------------------------------------------------------------- 寸法（m。原点は再生装置の真下の床）
UNIT_H = 0.74                                # 荷物一つ（トレーこみ）の高さ
Z_SEAT = 1.10                                # 再生装置の上面（口）。荷物の底がここに来ると鳴り始め、UNIT_H 沈むと鳴り終わる
N_SLOT = 4                                   # 塔に積める数（鳴っている一つ＋待つ三つ）
Z_DOOR = Z_SEAT + N_SLOT * UNIT_H + 0.30     # 塔の上の扉（受け渡し台の上面）
X_LIFT = 1.80                                # 昇降機の中心（塔の右）
Z_LIFT_LOW = -0.90                           # 昇降機の下の位置（床の下：受付ボックスからの通路）
V_TERM = 1.3                                 # 塔の中のブレーキで落ちる速さ（m/s）

# ---------------------------------------------------------------- 再生の速さ：荷物一つ（曲の一部分）を鳴らすのに T_P 秒
T_P = 31.0
V_PLAY = UNIT_H / T_P                        # 沈む速さ 2.4 cm/s
#   前半 A：03→04 の切り替わりが 738.8、04→05 が「四番が終わったら、次は五番」（769.8）、05→06 が 800.8、06→07 が 831.8
SEAM_A = 769.8
#   後半 B：08 が鳴り終わる（音が止まる）のは「間に合わなくなると……」のあと、「ここで、音が途切れる」の前
T_STOP = 871.8
T_B = L(146) - 0.25                          # 後半に切り替えるカット「今度は、九番がなかなか届きません」
#   第8章の前半（C）：「たとえば、たくさん届くまで待ってから、音を鳴らし始める」。塔がいっぱい（4つ）になるまで鳴らさずに待ち（灯は琥珀）、それから鳴らす
T0_8 = L(158) - 0.3                          # 第8章の始まり（「それなら、もっと先の分まで…」）。ここまでは後半 B の終わり（空・音なし）のまま
T_C = L(159) - 0.4                           # 切り替えるカット：01・02・03 が待っていて、04 が届くところ（その間は時間を飛ばす）
T_START_C = LE(159) + 0.15                   # 「…音を鳴らし始める」のすぐあと
T2_8 = L(161) - 0.3                          # 第8章の 3D はここまで（このあとは時間の帯・てんびんの図）

# ---------------------------------------------------------------- 荷物：(番号, 場面, 鳴り始め（本編）, 届く時刻（積み重なる時刻。None＝最初からある）)
_SA = {3: SEAM_A - 2 * T_P, 4: SEAM_A - T_P, 5: SEAM_A, 6: SEAM_A + T_P, 7: SEAM_A + 2 * T_P}
_SB = {7: T_STOP - 2 * T_P, 8: T_STOP - T_P}
T_06_LAND = L(137) + 1.45                    # 「その間に、六番が到着しました」
T_07_LAND = L(141) + 1.30                    # 「次の配達が少し遅れても…」のあと、少し遅れて 07 が届く（「余裕を作っています」）
PARCELS = [  # 番号, 場面, 鳴り始め, 届く（積み重なる）時刻
    ("03", "A", _SA[3], None), ("04", "A", _SA[4], None), ("05", "A", _SA[5], None),
    ("06", "A", _SA[6], T_06_LAND), ("07", "A", _SA[7], T_07_LAND),
    ("07", "B", _SB[7], None), ("08", "B", _SB[8], None),
    ("01", "C", T_START_C, None), ("02", "C", T_START_C + T_P, None), ("03", "C", T_START_C + 2 * T_P, None), ("04", "C", T_START_C + 3 * T_P, T_C + 2.6),
]


def scene_of(t_abs): return "A" if t_abs < T_B else ("B" if t_abs < T_C else "C")


def stack_bottom(start, t_abs):
    """積み重なっている荷物の底の高さ（鳴り始め start の荷物）。再生装置が回っている間は、積み重なり全体が V_PLAY で下がる
    （C では、鳴らし始める T_START_C までは止まっている）"""
    if scene_of(t_abs) == "C": t_abs = max(t_abs, T_START_C)
    return Z_SEAT - V_PLAY * (t_abs - start)


def braked_fall(z0, t):
    """速さに比例するブレーキ（終わりの速さ V_TERM）で落ちる：z(t), v(t)（下向きが正の v）"""
    k = G / V_TERM
    return z0 - V_TERM * t + (V_TERM / k) * (1.0 - math.exp(-k * t)), V_TERM * (1.0 - math.exp(-k * t))


def arrival(start, t_land):
    """届く荷物の動き：昇降機で上がる → 押されて塔の上の扉へ → 扉が開いて落ちる → 積み重なりの上に着く（t_land）
    → dict(times..., z_top(t)) 扉が開く時刻は、落ちて着く時刻が t_land になるように逆算する"""
    z_land = stack_bottom(start, t_land)                            # 着く高さ（下の荷物の上面）＝この荷物が積み重なったときの底
    lo, hi = 0.05, 8.0                                               # 扉が開いてから着くまでの時間（二分法）
    for _ in range(60):
        mid = 0.5 * (lo + hi); z, _ = braked_fall(Z_DOOR, mid)
        if z > z_land: lo = mid
        else: hi = mid
    T_fall = 0.5 * (lo + hi); t_open = t_land - T_fall
    t_push1 = t_open - 0.15; t_push0 = t_push1 - 1.40; t_rise1 = t_push0 - 0.10; t_rise0 = t_rise1 - 3.40
    _, v_land = braked_fall(Z_DOOR, T_fall)
    return dict(t_rise0=t_rise0, t_rise1=t_rise1, t_push0=t_push0, t_push1=t_push1, t_open=t_open, t_land=t_land, T_fall=T_fall, v_land=v_land,
                t_close=t_open + 0.85, t_lower0=t_push1 + 0.4, t_lower1=t_push1 + 3.6)


def mj(t, t0, T):
    u = min(max((t - t0) / T, 0.0), 1.0) if T > 1e-9 else float(t >= t0); return u * u * u * (10 - 15 * u + 6 * u * u)


def parcel_state(p, t_abs):
    """荷物の位置と状態 → (見える?, x, z_bottom, 状態)。状態：lift / push / fall / stack / gone"""
    no, sc, start, t_land = p
    if scene_of(t_abs) != sc: return (False, 0.0, 0.0, "other")
    if t_abs >= start + T_P: return (False, 0.0, Z_SEAT - UNIT_H, "gone")      # 鳴り終わった（再生装置の中へ消えた）
    if t_land is None or t_abs >= t_land: return (True, 0.0, stack_bottom(start, t_abs), "stack")
    a = arrival(start, t_land)
    if t_abs < a["t_rise0"]: return (False, X_LIFT, Z_LIFT_LOW, "below")
    if t_abs < a["t_push0"]: return (True, X_LIFT, Z_LIFT_LOW + (Z_DOOR - Z_LIFT_LOW) * mj(t_abs, a["t_rise0"], a["t_rise1"] - a["t_rise0"]), "lift")
    if t_abs < a["t_open"]: return (True, X_LIFT * (1.0 - mj(t_abs, a["t_push0"], a["t_push1"] - a["t_push0"])), Z_DOOR, "push")
    z, v = braked_fall(Z_DOOR, t_abs - a["t_open"])
    return (True, 0.0, max(z, stack_bottom(start, t_abs)), "fall")


def stack_top(t_abs):
    """塔の中の量（バッファの目盛り）：積み重なっている荷物のいちばん上（再生装置の口からの高さ）。落ちている荷物は数えない"""
    tops = [st[2] + UNIT_H for p in PARCELS for st in [parcel_state(p, t_abs)] if st[0] and st[3] == "stack"]
    return max(tops) - Z_SEAT if tops else 0.0


def playing(t_abs):
    """再生装置が鳴っているか：前半はずっと、後半は最後の荷物が終わるまで、C は鳴らし始めてから"""
    sc = scene_of(t_abs)
    return sc == "A" or (sc == "B" and t_abs < T_STOP) or (sc == "C" and t_abs >= T_START_C)


def player_state(t_abs):
    """再生装置の灯：play（緑）／wait（琥珀：ためている）／stop（消える）"""
    if playing(t_abs): return "play"
    return "wait" if scene_of(t_abs) == "C" else "stop"


ARR = {p[0] + p[1]: arrival(p[2], p[3]) for p in PARCELS if p[3] is not None}
# ---------------------------------------------------------------- カメラの場面（本編の秒, 名前）
SHOTS = [(T0, "K1 イヤホンの中（引き）：塔と再生装置と昇降機"), (L(130) + 2.6, "K2 再生装置：04 が鳴っている"), (L(132) - 0.25, "K3 上へ：05 が待っている"),
         (L(133) - 0.4, "K4 塔と再生装置（説明）"), (L(135) - 0.4, "K5 04 が終わって 05（曲は続く）"), (L(137) - 5.6, "K6 昇降機で 06 が届く"),
         (L(139) - 5.6, "K7 塔：バッファ（まるロボが下がって見上げる）"), (L(139) + (LE(139) - L(139)) * 24 / 30 - 0.55, "K7s 見上げた先：札「バッファ」が光る"), (L(140) - 0.4, "K8 目盛り：07 は少し遅れて届く"), (L(142) - 0.4, "K9 塔と再生装置（説明）"),
         (L(144) - 0.3, "K9b 引き"), (T_B, "K10 後半：09 が届かない"), (L(149) - 0.4, "K11 残りは一つ"), (L(151) - 0.4, "K12 再生装置：空になり音が止まる")]
SHOTS8 = [(T0_8, "C1 空になった塔：もっとためれば？"), (T_C, "C2 たくさん届くまで鳴らさずに待つ（04 が届く）"), (T_C + 3.3, "C3 いっぱいになってから鳴らす：余裕")]

if __name__ == "__main__":
    print("T0 %.2f T1 %.2f (%.1f s)  T_P %.1f  V %.4f m/s  Z_DOOR %.2f" % (T0, T1, T1 - T0, T_P, V_PLAY, Z_DOOR))
    for p in PARCELS: print("  %s %s start %.2f end %.2f land %s" % (p[0], p[1], p[2], p[2] + T_P, "%.2f" % p[3] if p[3] else "-"))
    for k, a in ARR.items(): print("  arrival", k, {kk: round(v, 2) for kk, v in a.items()})
    print("ch8: T0_8 %.2f T_C %.2f start %.2f T2_8 %.2f" % (T0_8, T_C, T_START_C, T2_8))
    for t in (T0, 748.35, 750.9, 769.2, 770.5, 783.6, 795.7, 800.8, 811.7, 834.0, T_B, 841.0, 847.1, 856.5, 866.3, 871.7, 871.9, 908.0, 912.0, 914.6, 916.0, 917.0, 925.0):
        print("  %.2f %s level %.2f %s  %s" % (t, scene_of(t), stack_top(t), player_state(t), " ".join("%s%s:%s%.2f" % (p[0], p[1], st[3][0], st[2]) for p in PARCELS for st in [parcel_state(p, t)] if st[0])))
    for t_, nm in SHOTS: print("  %7.2f %s" % (t_, nm))
