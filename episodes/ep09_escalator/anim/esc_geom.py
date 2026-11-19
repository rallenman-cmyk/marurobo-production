# 9本目（エスカレーター）：段の輪の形と動き（Blender の外でも同じ計算。kit9.py・scenes.py・点検の図が読む）
#   座標：x＝上る向き（右）、y＝幅の向き（奥が +）、z＝上。下の床の面 z=0、上の床の面 z=H。長さは m。
#   段の基準点＝前の車輪の中心（鎖の通り道の上）。段は輪の通り道に沿って同じ間隔で並び、同じ速さで動く。
#   上の通り道（人が乗る側）では段は水平のまま（だから坂では階段に、端では平らになる）。
#   上の歯車のまわりで回って、戻る側ではさかさま（180°）。下の歯車のまわりでもう一度回って表に戻る。
#   後ろの車輪は、段に固定した場所にある。2 本のレールは、前の車輪と後ろの車輪が本当に通る道（ここで計算）から作る。
import math

H = 3.0                     # 上の床までの高さ
ANG = math.radians(30.0)    # 坂の角度
D = 0.40                    # 段の踏む所の奥行き（平らな所での段の間隔）
WID = 1.0                   # 段の幅（2 人乗り）
TREAD_DZ = 0.20             # 前の車輪の中心から、踏む面までの高さ
FLAT_LO = 1.6               # 下の乗り口の平らな所（踏む面が床の高さ）の長さ
FLAT_HI = 1.6               # 上の降り口の平らな所
R_CONVEX = 1.2              # 上の曲がり（坂 → 平ら）の半径
R_CONCAVE = 2.0             # 下の曲がり（平ら → 坂）の半径
DIP = 0.35                  # くしをくぐったあと、段が床の下へもぐる深さ（歯車で回るとき、段の角が床の板に当たらない深さ。2026-11-19 ユーザー「くしのところではみ出てる」）
DIP_LEN = 0.90              # もぐる長さ
RG = 0.60                   # 上と下の歯車の半径（前の車輪の通り道）。上の段と戻る段の間に、まるロボ（高さ約 0.9m）が乗れるすき間ができる大きさ
REAR = (-0.33, 0.04)        # 後ろの車輪の場所（段の中で。前の車輪から後ろへ。高さはほぼ同じ＝平らな所で 2 つの車輪がほぼ一直線に並ぶ。坂では 2 本のレールが離れる）
COMB_LO_X = None            # 下のくしの x（下で決める）
COMB_HI_X = None


def _top_path():
    """人が乗る側の、前の車輪の通り道（下の端 → 上の端）。区間のリスト：('L', p0, p1) か ('A', 中心, 半径, a0, a1)"""
    z0 = -TREAD_DZ                    # 平らな所：踏む面が z=0 になる車輪の高さ
    z1 = H - TREAD_DZ
    segs = []
    x = 0.0
    # 下の端：もぐった所から上がってくる（下のくしの先）
    segs.append(("L", (x, z0 - DIP), (x + DIP_LEN, z0)))
    x += DIP_LEN
    segs.append(("L", (x, z0), (x + FLAT_LO, z0))); x += FLAT_LO
    # 下の曲がり（へこむ向き）：中心は上
    c = (x, z0 + R_CONCAVE)
    segs.append(("A", c, R_CONCAVE, -math.pi / 2, -math.pi / 2 + ANG))
    px = c[0] + R_CONCAVE * math.sin(ANG); pz = c[1] - R_CONCAVE * math.cos(ANG)
    # 上の曲がり（ふくらむ向き）：中心は下。坂の長さは高さが合うように決める
    dz_conv = R_CONVEX * (1 - math.cos(ANG))
    L_inc = (z1 - dz_conv - pz) / math.sin(ANG)
    qx = px + L_inc * math.cos(ANG); qz = pz + L_inc * math.sin(ANG)
    segs.append(("L", (px, pz), (qx, qz)))
    c2 = (qx + R_CONVEX * math.sin(ANG), qz - R_CONVEX * math.cos(ANG))   # 中心は通り道の右下
    segs.append(("A", c2, R_CONVEX, math.pi / 2 + ANG, math.pi / 2))
    x = c2[0]
    segs.append(("L", (x, z1), (x + FLAT_HI, z1))); x += FLAT_HI
    segs.append(("L", (x, z1), (x + DIP_LEN, z1 - DIP))); x += DIP_LEN
    return segs


def _seglen(sg):
    if sg[0] == "L":
        return math.hypot(sg[2][0] - sg[1][0], sg[2][1] - sg[1][1])
    return abs(sg[4] - sg[3]) * sg[2]


def _segpt(sg, u):
    """区間の中の点（u：0〜1）と、進む向きの角度"""
    if sg[0] == "L":
        (a, b), (c, d) = sg[1], sg[2]
        return (a + (c - a) * u, b + (d - b) * u), math.atan2(d - b, c - a)
    c, r, a0, a1 = sg[1], sg[2], sg[3], sg[4]
    a = a0 + (a1 - a0) * u
    tang = a + (math.pi / 2 if a1 > a0 else -math.pi / 2)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a)), tang


TOP = _top_path()
LTOP = sum(_seglen(s) for s in TOP)
X_HI_END = TOP[-1][2][0]                       # 上の端（もぐり終わり）
X_LO_END = TOP[0][1][0]
COMB_LO_X = DIP_LEN + 0.18                     # 下のくし（の線 + 0.18）：段が上がりきって、平らに出てくる所
COMB_HI_X = X_HI_END - DIP_LEN + 0.18          # 上のくし（の線 + 0.18）：段がもぐり始める所
LOOP = 2 * LTOP + 2 * math.pi * RG
N_STEPS = round(LOOP / D)
PITCH = LOOP / N_STEPS                         # 段の間隔（輪の上で。平らな所の奥行きにほぼ等しい）


def top_point(s):
    """人が乗る側の通り道で、下の端から s 進んだ所：(x, z), 進む向き"""
    s = max(0.0, min(LTOP, s))
    for sg in TOP:
        L = _seglen(sg)
        if s <= L + 1e-9:
            return _segpt(sg, s / L if L else 0.0)
        s -= L
    return _segpt(TOP[-1], 1.0)


def loop_pose(s):
    """輪の上で s 進んだ所の前の車輪：(x, z, 段の回り角[度]、0＝表・180＝さかさま)。s は 0〜LOOP をくり返す"""
    s = s % LOOP
    if s < LTOP:
        (x, z), _ = top_point(s); return x, z, 0.0
    s -= LTOP
    arc = math.pi * RG
    if s < arc:                                   # 上の歯車のまわり（右へ回って下へ）
        (ex, ez), _ = top_point(LTOP)
        cx, cz = ex, ez - RG
        a = math.pi / 2 - s / RG                  # 90° → -90°
        return cx + RG * math.cos(a), cz + RG * math.sin(a), math.degrees(s / RG)
    s -= arc
    if s < LTOP:                                  # 戻る側：上の通り道を 2RG 下げて、逆にたどる（さかさま）
        (x, z), _ = top_point(LTOP - s); return x, z - 2 * RG, 180.0
    s -= LTOP
    (bx, bz), _ = top_point(0.0)                  # 下の歯車のまわり（左へ回って上へ）
    cx, cz = bx, bz - RG
    a = -math.pi / 2 - s / RG                     # -90° → -270°
    return cx + RG * math.cos(a), cz + RG * math.sin(a), 180.0 + math.degrees(s / RG)


def local_to_world(x, z, rot_deg, lx, lz):
    """段の中の点（lx, lz：前の車輪から）を、世界へ。段は y 軸のまわりに rot_deg 回る（上の歯車で、前が下へ回る向き）"""
    a = math.radians(rot_deg)
    # 右へ進みながら下へ回る：前（+x）が下（-z）を向く向き＝ y 軸まわり（Blender で正）
    ca, sa = math.cos(a), math.sin(a)
    return x + lx * ca + lz * sa, z - lx * sa + lz * ca


def step_pose(k, pos):
    """k 番目の段（0〜N_STEPS-1）。pos：輪が進んだ長さ（時刻ごと）。前の車輪 (x, z)・回り角・後ろの車輪 (x, z)"""
    x, z, r = loop_pose(pos + k * PITCH)
    rx, rz = local_to_world(x, z, r, REAR[0], REAR[1])
    return (x, z), r, (rx, rz)


def rail_points(which="front", n=600):
    """レールの点（輪をひと回り）。front＝前の車輪の通り道、rear＝後ろの車輪の通り道"""
    pts = []
    for i in range(n + 1):
        s = LOOP * i / n
        x, z, r = loop_pose(s)
        if which == "rear": x, z = local_to_world(x, z, r, REAR[0], REAR[1])
        pts.append((x, z))
    return pts


class Speed:
    """エスカレーターの動き：(時刻, 速さ m/秒) を並べた予定。速さはなめらかに変わる。pos(t) は進んだ長さ"""

    def __init__(self, keys, v0=0.5, dt=1 / 48):
        self.keys = sorted(keys); self.v0 = v0; self.dt = dt; self._tab = None

    def v(self, t):
        if not self.keys: return self.v0
        if t <= self.keys[0][0]: return self.keys[0][1]
        for (t0, v0), (t1, v1) in zip(self.keys, self.keys[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / max(1e-6, t1 - t0); u = u * u * (3 - 2 * u)
                return v0 + (v1 - v0) * u
        return self.keys[-1][1]

    def pos(self, t, t_from=-30.0):
        """t_from から t までに進んだ長さ（台形でたす。表にしておく）"""
        if self._tab is None:
            self._tab = {}; acc = 0.0; tt = t_from; k = 0
            self._t0 = t_from; self._vals = [0.0]
            while tt < 4000:
                acc += 0.5 * (self.v(tt) + self.v(tt + self.dt)) * self.dt; tt += self.dt; self._vals.append(acc)
                if tt > self.keys[-1][0] + 60 if self.keys else tt > t_from + 2000: break
            self._tab = True
        i = (t - self._t0) / self.dt
        if i <= 0: return 0.0
        j = int(i)
        if j + 1 >= len(self._vals):
            return self._vals[-1] + self.v(t) * (t - (self._t0 + (len(self._vals) - 1) * self.dt))
        return self._vals[j] + (self._vals[j + 1] - self._vals[j]) * (i - j)


if __name__ == "__main__":
    print("坂の長さ・輪の長さ・段の数・間隔", round(LTOP, 3), round(LOOP, 3), N_STEPS, round(PITCH, 4))
    (x, z), _ = top_point(LTOP)
    print("上の端", round(x, 3), round(z, 3), "下の端", top_point(0)[0])
