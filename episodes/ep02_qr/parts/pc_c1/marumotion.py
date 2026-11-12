# まるロボの動きの部品集（物理と生体力学に合わせた動き）
#   予定（Plan）に動きを順に積み、simulate() で毎コマの姿勢（世界座標）にする。Blender の部品に当てるのは marurig.py
#   単位：長さ m・時間 s・引数の角度は「度」。重力 9.81 m/s²。数値の根拠は制作バイブル「まるロボの動き」
#
#   p = Plan(pos=(0, 0), heading=0)        # heading 0 で +Y を向く。左回り（上から見て反時計回り）が＋
#   p.idle(3); p.look(30); p.walk_to((0, 3)); p.turn_to(90); p.nod(); p.shake(); p.surprise(); p.hops()
#   p.think(); p.peer(); p.sigh(); p.jump_to((1, 0), z1=0.3); p.unload()
#   frames = simulate(p, fps=24)            # 毎コマの姿勢の辞書のリスト（バネ・足の置き場所・荷物まで計算済み）
#
# 体の向きの約束：前＝ローカル +Y、右＝ローカル +X。左脚＝足0（x−）、右脚＝足1（x＋）
import math, random, bisect
import numpy as np

G = 9.81

# ---------------------------------------------------------------- 体の寸法（story.blend の「Maru」を測った値）
L_LEG = 0.43                 # 倒立振子の脚の長さ（腰→地面）
HIP_X = 0.255                # 脚の付け根の左右の位置
HIP_Z = 0.43                 # 脚の付け根の高さ（ルートから）
ROOT_DZ = -0.01              # ルートは床より 1cm 下（靴底がちょうど床に着く）
HIP_REST = HIP_Z + ROOT_DZ   # 立っているときの脚の付け根の高さ（床から）0.42
ANKLE = 0.25                 # 脚の付け根→足首
SOLE = 0.17                  # 足首→靴底
HEEL = np.array([0.0, -0.08, 0.01])   # 足の基準点（足首の真下の靴底）から見た、かかとの角
TOE = np.array([0.0, 0.28, 0.01])     # つま先の角
TORSO_Z = 0.73               # 胴の中心（ルートから）
ANT_BASE = np.array([-0.27, -0.04, 0.38])    # アンテナの根元（胴の中心から）
ANT_REST_Y = -0.026                          # アンテナの根元の傾き（rad）
ANT_TIP = np.array([-0.13, 0.0, 0.57])       # 根元→先の玉
ANT_LEN = float(np.linalg.norm(ANT_TIP))     # 0.585 m
# 荷物はトレー（板）ごと受け渡す。まるロボの頭には小さな受け皿だけ（板は体より幅が広く、体の中にはしまえないため）
CRADLE_LIFT = 0.0                            # （前の版の名残。使わない）
SADDLE_R = 0.12                              # 頭の受け皿の半径
CRADLE = np.array([0.0, -0.02, 0.50])        # 受け皿の回転軸（胴の中心から）。頭のてっぺん（0.49）のすぐ上
CRADLE_TOP = 0.015                           # 回転軸→受け皿の上面（頭のてっぺんより 2.5cm 上）
SADDLE_DROP = 0.025                          # 使わないとき、受け皿は 2.5cm 下がって頭のてっぺんにそろう
TRAY_H = 0.06                                # トレーの厚さ
CARGO_HALF = (0.33, 0.37)                    # 荷物（トレー6cm＋箱68cm）の半分の奥行き・半分の高さ
CARGO_Z = CRADLE_TOP + CARGO_HALF[1]         # 回転軸→荷物（トレーごと）の中心
CRADLE_FRONT = SADDLE_R                      # 回転軸→受け皿の前・後ろの端
CARGO_LOCK = True                            # 受け皿の真ん中の錠（ピン）がトレーの下の穴にかかる：運ぶ間・跳ぶ間も、荷物は滑らず倒れない
ANT_RETRACT = 0.70                           # 荷台を出す間、アンテナを軸の向きに 0.70m 体の中へしまう（先の玉も体の中に隠れる）
LOAD_RATIO = 0.25                            # 荷物の重さ÷ロボの重さ
MU_CRADLE = 0.28                             # 受け皿とトレーの摩擦
LOAD_LEAN = math.degrees(math.atan(LOAD_RATIO / (1 + LOAD_RATIO) * (-CRADLE[1]) / 1.0))   # 荷物が体の中心より後ろにある分、前へ傾けて釣り合う（いまは約0.2°）
LENS = dict(y=0.508, depth=0.075, r=0.223, ring_y=0.578, ring_r=0.145, z=0.025)   # 目のレンズ（胴の中心から）

# ---------------------------------------------------------------- 歩き（バイブルの値）
BETA = 0.60          # 足が地面に着いている割合
LIFT = 0.07          # 足の上げ幅
ROLL_WALK = 5.0      # 支えている脚の側への横揺れ ±5°（ペンギン歩き）
LEAN_WALK = 2.0      # 歩いている間の前傾
V_WALK, V_BRISK, V_RUN = 1.0, 1.3, 2.0
A_RUN = 2.0          # 走り出し・走って止まるときの最大の加速度（前傾 約11°）
A_STOP = 1.39        # 止まるときの最大の減速度（1.3 m/s → 1.4 秒・0.91 m、後ろへ約8°）
A_START = 1.5        # 歩き出しの最大の加速度（少しせっかち）
C_MIN = 1.0          # 歩き始め・終わりの最低の歩調（左右の2歩で1組、1秒あたり）
DS_DIP = 0.012       # 両足で支える間の追加の沈み（上下の揺れを約4.5cmにする）
REACT = 0.20         # 反応の遅れ
IRIS_SHIFT = 0.016   # 目（内側の輪）が動ける幅
FPS = 24


def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)


def smooth(u):
    """躍度最小（5次）：0→1 を、速さが釣り鐘形になるように"""
    u = clamp(u); return u * u * u * (10 - 15 * u + 6 * u * u)


def mj(t, t0, T): return smooth((t - t0) / T) if T > 1e-9 else (1.0 if t >= t0 else 0.0)


def env(t, t0, up, hold, down): return mj(t, t0, up) - mj(t, t0 + up + hold, down)


def hump(t, t0, T):
    """0→1→0 の山（sin²、両端で速さ0）"""
    u = (t - t0) / T
    return math.sin(math.pi * u) ** 2 if 0.0 < u < 1.0 else 0.0


def quintic(t, T, x0, v0, a0, x1, v1, a1):
    """境界条件（位置・速さ・加速度）つきの5次の軌道 → (x, v, a)"""
    T2, T3, T4, T5 = T * T, T ** 3, T ** 4, T ** 5
    c3 = (20 * (x1 - x0) - (8 * v1 + 12 * v0) * T - (3 * a0 - a1) * T2) / (2 * T3)
    c4 = (30 * (x0 - x1) + (14 * v1 + 16 * v0) * T + (3 * a0 - 2 * a1) * T2) / (2 * T4)
    c5 = (12 * (x1 - x0) - 6 * (v1 + v0) * T - (a0 - a1) * T2) / (2 * T5)
    x = x0 + v0 * t + a0 / 2 * t * t + c3 * t ** 3 + c4 * t ** 4 + c5 * t ** 5
    v = v0 + a0 * t + 3 * c3 * t * t + 4 * c4 * t ** 3 + 5 * c5 * t ** 4
    a = a0 + 6 * c3 * t + 12 * c4 * t * t + 20 * c5 * t ** 3
    return x, v, a


def wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi
def fwd(psi): return np.array([-math.sin(psi), math.cos(psi)])
def rgt(psi): return np.array([math.cos(psi), math.sin(psi)])


def rotz(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rotx(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def roty(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def stride(v):
    """Alexander の関係：歩幅/脚長 = 2.3 × (v²/gL)^0.3（2歩ぶん＝同じ足が次に着くまで）"""
    return 2.3 * L_LEG * max(v * v / (G * L_LEG), 1e-9) ** 0.3


def cadence(v): return max(C_MIN, v / stride(v)) if v > 1e-4 else C_MIN


def duty(v):
    """足が地面に着いている割合：歩き 0.60 → 走り 0.35。1.40〜1.60 m/s で切り替える（バイブル：フルード数0.5＝約1.45m/s で走りへ。
    それより速く歩くと、倒立振子の体の上下が大きくなりすぎる）。0.5 より小さくなると、両足が地面から離れる間ができる"""
    return BETA - 0.25 * smooth((v - 1.40) / 0.20)


def run_weight(beta): return smooth((0.55 - beta) / 0.10)


def saccade_time(amp_deg):
    """目の跳躍運動の時間（主系列）：約 2.2ms×振幅(度)＋21ms"""
    return (2.2 * abs(amp_deg) + 21.0) / 1000.0


def blink_shape(t, t0, close=2 / 24, hold=1 / 24, opn=4 / 24):
    """まばたき（バイブル：閉じる2コマ・止める1コマ・開く4コマ）。0＝開、1＝閉"""
    if t < t0 or t > t0 + close + hold + opn: return 0.0
    if t < t0 + close: u = (t - t0) / close; return u * u * (3 - 2 * u)
    if t < t0 + close + hold: return 1.0
    u = (t - t0 - close - hold) / opn; return 1.0 - u * u * (3 - 2 * u)


# ================================================================ 予定の部品
class Contact:
    """足の置き場所：足の基準点（足首の真下の靴底）p・向き psi・着いている時間"""
    __slots__ = ("t_on", "t_off", "p", "psi", "lift", "hs", "to", "kind", "tau", "ext", "ext_to")

    def __init__(self, t_on, p, psi, lift=0.0, hs=0.0, kind="stand", tau=0.07):
        self.t_on = t_on; self.t_off = None; self.p = np.array(p, float); self.psi = psi
        self.lift = lift      # この足場へ来るときの足の上げ幅
        self.hs = hs          # かかとから着く角度（度）
        self.to = 0.0         # つま先で離れる角度（度）：次の一歩が決まったら入れる
        self.kind = kind      # stand / walk / close / turn / jump
        self.tau = tau        # 体重が乗り移る時間
        self.ext = 0.0        # 跳んで着くときの脚の伸び
        self.ext_to = 0.0     # ここから跳ぶときの脚の伸び


class Track:
    """値を、ある時刻から決めた時間で次の値へ移す（躍度最小）。値はそのまま残る。命令は時刻の順に"""
    def __init__(self, v0=0.0):
        self.t0s = [-1e9]; self.keys = [(-1e9, 0.0, v0, v0)]

    def at(self, t):
        t0, T, a, b = self.keys[bisect.bisect_right(self.t0s, t) - 1]
        return a + (b - a) * mj(t, t0, T)

    def set(self, t0, T, to):
        frm = self.at(t0); i = bisect.bisect_right(self.t0s, t0)
        self.t0s.insert(i, t0); self.keys.insert(i, (t0, T, frm, to))


class Seg:
    """体の位置と向き（ルート）の区間。ここでは止まっている"""
    kind = "hold"

    def __init__(self, t0, t1, p, psi):
        self.t0, self.t1 = t0, t1; self.p0 = np.array(p, float); self.psi0 = psi

    def xy(self, t): return self.p0, self.psi0
    def vel(self, t): return 0.0, 0.0           # 進む向きの速さ・加速度
    def phase(self, t): return None
    def hip(self, t): return None               # 跳ぶ間の脚の付け根の高さ（世界）


class TurnSeg(Seg):
    kind = "turn"

    def __init__(self, t0, t1, p, psi0, d):
        super().__init__(t0, t1, p, psi0); self.d = d

    def xy(self, t): return self.p0, self.psi0 + self.d * mj(t, self.t0, self.t1 - self.t0)


class ShiftSeg(Seg):
    """向きを変えずに、足踏みで少しだけ動く（後ずさり）。体は躍度最小で動き、進む向きの加速度の分だけ傾く（倒立振子）"""
    kind = "shift"

    def __init__(self, t0, t1, p, psi, dv):
        super().__init__(t0, t1, p, psi); self.dv = np.array(dv, float)

    def xy(self, t): return self.p0 + self.dv * mj(t, self.t0, self.t1 - self.t0), self.psi0

    def vel(self, t):
        T = self.t1 - self.t0
        if t < self.t0 or t > self.t1 or T <= 0: return 0.0, 0.0
        u = (t - self.t0) / T; f = float(self.dv @ fwd(self.psi0))
        return f * 30 * u * u * (1 - u) ** 2 / T, f * 60 * u * (1 - u) * (1 - 2 * u) / (T * T)


class WalkSeg(Seg):
    """まっすぐ歩く：加速（5次）→一定の速さ→減速（5次）。歩調は Alexander の歩幅から"""
    kind = "walk"

    def __init__(self, t0, p0, psi, D, v, a_up, a_dn, lead):
        v = min(v, math.sqrt(D / (0.75 * (1 / a_up + 1 / a_dn))))     # 短い距離では最高速を下げる
        Ta, Td = 1.5 * v / a_up, 1.5 * v / a_dn; Da, Dd = v * Ta / 2, v * Td / 2; Tc = max(0.0, (D - Da - Dd) / v)
        super().__init__(t0, t0 + Ta + Tc + Td, p0, psi)
        self.D, self.v = D, v
        dt = 1.0 / 480; tt = np.arange(t0, self.t1 + 2.5, dt); S = np.zeros_like(tt); V = np.zeros_like(tt); A = np.zeros_like(tt)
        for i, t in enumerate(tt):
            u = t - t0
            if u < Ta:
                s = u / Ta; S[i] = v * Ta * (s ** 3 - s ** 4 / 2); V[i] = v * (3 * s * s - 2 * s ** 3); A[i] = v / Ta * (6 * s - 6 * s * s)
            elif u < Ta + Tc:
                S[i] = Da + v * (u - Ta); V[i] = v
            elif u < Ta + Tc + Td:
                s = (u - Ta - Tc) / Td; S[i] = Da + v * Tc + v * Td * (s - s ** 3 + s ** 4 / 2); V[i] = v * (1 - 3 * s * s + 2 * s ** 3); A[i] = -v / Td * (6 * s - 6 * s * s)
            else:
                S[i] = D
        c = np.array([cadence(x) for x in V])
        PH = np.concatenate([[0.0], np.cumsum(0.5 * (c[1:] + c[:-1]) * dt)]) + BETA - 0.5 * lead
        self.tt, self.S, self.V, self.A, self.PH = tt, S, V, A, PH
        self.B = np.array([duty(x) for x in V])

    def xy(self, t): return self.p0 + fwd(self.psi0) * float(np.interp(t, self.tt, self.S)), self.psi0

    def vel(self, t):
        if t < self.t0 or t > self.t1: return 0.0, 0.0
        return float(np.interp(t, self.tt, self.V)), float(np.interp(t, self.tt, self.A))

    def phase(self, t):
        if t < self.t0 or t > self.t1: return None
        return float(np.interp(t, self.tt, self.PH))

    def beta(self, t): return float(np.interp(t, self.tt, self.B))


def push_time(crouch, ext, v):
    """蹴る時間：しゃがんだ所（−crouch・止まっている）から脚を伸ばした所（+ext・速さ v・加速度 −g）まで。
    途中で戻らない（速さが負にならない）いちばん長い時間＝いちばん穏やかな蹴り"""
    d = crouch + ext; best = None
    for k in np.linspace(1.0, 3.5, 51):
        T = k * d / v; ok = True
        for u in np.linspace(0, T, 41)[1:]:
            if quintic(u, T, -crouch, 0, 0, ext, v, -G)[1] < -1e-3: ok = False; break
        if ok: best = T
    return best if best else 2 * d / v


def _qmin(T, x0, v0, a0, x1, v1, a1):
    return min(quintic(u, T, x0, v0, a0, x1, v1, a1)[0] for u in np.linspace(0, T, 61))


def bounce_time(ext, v_in, v_out, depth):
    """続けて跳ぶときの、着いてから離れるまでの時間：いちばん沈む所が −depth になる長さ"""
    lo, hi = 0.02, 0.8
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if _qmin(m, ext, -v_in, -G, ext, v_out, -G) < -depth: hi = m
        else: lo = m
    return 0.5 * (lo + hi)


def land_curve(ext, v, depth, zeta):
    """最後の着地：脚を ext 伸ばして着き（下へ速さ v）、減衰振動で受け止める。いちばん沈む所が −depth"""
    def make(w):
        wd = w * math.sqrt(1 - zeta * zeta); B = (zeta * w * ext - v) / wd
        return lambda u: math.exp(-zeta * w * u) * (ext * math.cos(wd * u) + B * math.sin(wd * u))
    lo, hi = 2.0, 200.0
    for _ in range(50):
        w = math.sqrt(lo * hi); f = make(w)
        if min(f(u) for u in np.linspace(0, 4.0 / w, 80)) < -depth: lo = w
        else: hi = w
    return make(math.sqrt(lo * hi)), math.sqrt(lo * hi)


class JumpSeg(Seg):
    """跳ぶ（1回または続けて何回も）：しゃがむ→脚を伸ばしながら蹴る→放物線→（弾んで次へ）→脚を伸ばして着き、受け止める
    横へ跳ぶときは、蹴る間に横の速さをつけ、着いてから減らす（速さが急に変わらない）。
    しゃがみ・沈みは 4.5cm まで（それより深いと胴が足首の玉に当たる）。脚の伸びは 10cm まで（脚の上の端が胴の中に残る）"""
    kind = "jump"

    def __init__(self, t0, p0, psi0, z0, apexes, dxy=(0.0, 0.0), dz=0.0, crouch=0.04, T_c=0.2, ext=0.04, ext_ld=None, depth=0.04, zeta=0.65,
                 settle=0.8, T_l=0.3):
        super().__init__(t0, t0, p0, psi0)
        self.pieces = []; self.flights = []
        ext_ld = ext if ext_ld is None else ext_ld
        dxy = np.array(dxy, float); D = float(np.linalg.norm(dxy)); self.dir = dxy / D if D > 1e-6 else np.zeros(2); self.D = D
        t = t0; z = z0; h = z + HIP_REST
        v_up = math.sqrt(2 * G * apexes[0])
        self.pieces.append((t, t + T_c, lambda u, h=h: h - crouch * smooth(u / T_c))); t += T_c
        T_p = push_time(crouch, ext, v_up); self.T_push = T_p; self.t_push = t
        self.pieces.append((t, t + T_p, lambda u, h=h, T=T_p, v=v_up: h + quintic(u, T, -crouch, 0, 0, ext, v, -G)[0])); t += T_p
        t_air = 0.0
        for k, apex in enumerate(apexes):
            last = k + 1 == len(apexes)
            e0 = ext; e1 = ext_ld if last else ext          # 蹴るときの脚の伸び・着くときの脚の伸び
            v_up = math.sqrt(2 * G * apex); z1 = z + (dz if k == 0 else 0.0)
            h0 = z + HIP_REST + e0; h1 = z1 + HIP_REST
            T_up = v_up / G; T_dn = math.sqrt(2 * max(h0 + apex - (h1 + e1), 1e-4) / G); T_fl = T_up + T_dn; v_imp = G * T_dn
            self.pieces.append((t, t + T_fl, lambda u, h=h0, v=v_up: h + v * u - 0.5 * G * u * u))
            fl = dict(t0=t, t1=t + T_fl, z0=z, z1=z1, v_up=v_up, v_imp=v_imp, ext_to=e0, ext_ld=e1)
            self.flights.append(fl); t_air += T_fl
            t += T_fl; z = z1
            if not last:
                v_nx = math.sqrt(2 * G * apexes[k + 1]); T_b = bounce_time(ext, v_imp, v_nx, depth)
                self.pieces.append((t, t + T_b, lambda u, h=h1, T=T_b, a=v_imp, b=v_nx, e=ext: h + quintic(u, T, e, -a, -G, e, b, -G)[0]))
                fl["t_next"] = t + T_b; t_air += T_b; t += T_b
            else:
                f, w = land_curve(e1, v_imp, depth, zeta); fl["omega"] = w
                self.pieces.append((t, t + settle, lambda u, h=h1, f=f: h + f(u))); self.t_land = t; t += settle
        # 横の速さ：蹴る間に 0→vh、宙と弾む間は一定、着いてから T_l で 0 へ
        self.T_l = T_l; self.vh = D / (T_p / 2 + t_air + T_l / 2) if D > 1e-6 else 0.0
        self.t1 = max(t, self.t_land + T_l); self.p_end = self.p0 + dxy; self.psi_end = psi0; self.z_end = z
        for fl in self.flights:
            fl["p0"] = self._pos(fl["t0"]); fl["p1"] = self._pos(fl["t1"])

    def _s(self, t):
        vh, T_p, tp = self.vh, self.T_push, self.t_push
        if vh == 0.0 or t <= tp: return 0.0
        if t <= tp + T_p: return quintic(t - tp, T_p, 0, 0, 0, vh * T_p / 2, vh, 0)[0]
        if t <= self.t_land: return vh * T_p / 2 + vh * (t - tp - T_p)
        s0 = vh * T_p / 2 + vh * (self.t_land - tp - T_p)
        if t <= self.t_land + self.T_l: return s0 + quintic(t - self.t_land, self.T_l, 0, vh, 0, vh * self.T_l / 2, 0, 0)[0]
        return self.D

    def _pos(self, t): return self.p0 + self.dir * self._s(t)

    def xy(self, t): return self._pos(t), self.psi0

    def hip(self, t):
        if t < self.t0 or t > self.t1: return None
        for a_, b_, fn in self.pieces:
            if a_ <= t <= b_: return fn(t - a_)
        return None


# ================================================================ 予定
class Plan:
    CHANNELS = ("gaze_yaw", "gaze_pitch", "twist", "pitch", "roll", "lift", "dx", "iris", "light", "zoom", "cradle", "ant")

    def __init__(self, pos=(0.0, 0.0), heading=0.0, ground=0.0, carry=False, seed=7):
        self.t = 0.0
        p = np.array(pos, float); psi = math.radians(heading)
        self.segs = [Seg(-1e9, 0.0, p, psi)]; self.seg_t0 = [-1e9]
        self.feet = [[Contact(-1e9, (*(p + rgt(psi) * s * HIP_X), ground), psi)] for s in (-1, 1)]
        self.tracks = {k: Track() for k in self.CHANNELS}
        self.layers = []; self.events = []; self.labels = []; self.blinks = []; self.no_blink = []
        self.rng = random.Random(seed)
        self.carry = [(-1e9, bool(carry))]; self.unloads = []; self.cuts = []; self.loads = []
        self.cradle = [(-1e9, 1.0 if carry else 0.0, 0.0)]           # 荷台の出し入れ（時刻, 0＝しまう 1＝出す, かける時間）
        self._p, self._psi, self._z = p, psi, ground

    # ---------------------------------------------------------- 内部の道具
    def _at(self, at): return self.t if at is None else at

    def _seg_add(self, seg):
        self.segs.append(seg); self.seg_t0.append(seg.t0)

    def _seg(self, t): return self.segs[bisect.bisect_right(self.seg_t0, t) - 1]

    def layer(self, t0, t1, fn):
        """足し合わせる動き：fn(t) → {チャンネル: 値}"""
        self.layers.append((t0, t1, fn)); return self

    def event(self, t, kind, strength=1.0, **kw):
        self.events.append(dict(t=round(t, 4), kind=kind, strength=round(float(strength), 3), **kw)); return self

    def label(self, text, t0=None, t1=None):
        self.labels.append([self.t if t0 is None else t0, t1, text]); return self

    def _lb(self, text, t0=None):
        if not text: return None
        self.labels.append([self.t if t0 is None else t0, None, text]); return len(self.labels) - 1

    def _lb_end(self, i):
        if i is not None and self.labels[i][1] is None: self.labels[i][1] = self.t

    def _neutral(self, t0, T=0.25, keep_gaze=False):
        for ch in ("twist", "pitch", "roll", "dx", "lift"):
            self.tracks[ch].set(t0, T, 0.0)
        if not keep_gaze:
            self.tracks["gaze_yaw"].set(t0, saccade_time(30), 0.0); self.tracks["gaze_pitch"].set(t0, saccade_time(20), 0.0)

    def _lift_foot(self, j, t):
        c = self.feet[j][-1]
        if c.t_off is None or c.t_off > t: c.t_off = t
        return c

    def _place(self, j, t_on, p, psi, **kw):
        c = Contact(t_on, p, psi, **kw); self.feet[j].append(c); return c

    def _ground(self):
        return max(self.feet[0][-1].p[2], self.feet[1][-1].p[2])

    # ---------------------------------------------------------- 待つ・見る
    def wait(self, dur):
        self.t += dur; return self

    def idle(self, dur=3.0, shifts=True, glance=True, label=None):
        """待機：呼吸（いつも）、4〜7秒ごとの体重移動（左右1.2cm・1.2°）、目の小さな動き"""
        lid = self._lb(label)
        t0, t1 = self.t, self.t + dur
        if shifts:
            t = t0 + self.rng.uniform(0.6, 1.6); side = self.rng.choice((-1, 1))
            while t + 0.9 < t1:
                self.tracks["dx"].set(t, 0.9, 0.012 * side); self.tracks["roll"].set(t, 0.9, -1.2 * side)
                side = -side; t += self.rng.uniform(4.0, 7.0)
        if glance:
            t = t0 + self.rng.uniform(0.5, 1.2); gy = self.tracks["gaze_yaw"].at(t0); gp = self.tracks["gaze_pitch"].at(t0)
            while t + 0.3 < t1:
                y = gy + self.rng.uniform(-5, 5); p_ = gp + self.rng.uniform(-3, 3)
                self.tracks["gaze_yaw"].set(t, saccade_time(5), y); self.tracks["gaze_pitch"].set(t, saccade_time(3), p_)
                t += self.rng.uniform(0.8, 2.2)
        self.t = t1; self._lb_end(lid); return self

    def look(self, yaw=0.0, pitch=0.0, hold=0.6, at=None, body=True, label=None):
        """見る：目が先に跳び（0.1秒）、0.12秒遅れて胴が追う。胴が追いつくと目は真ん中へ戻る
        yaw：体の正面から左が＋（度）、pitch：上が＋"""
        t0 = self._at(at)
        lid = self._lb(label, t0)
        gy0, gp0 = self.tracks["gaze_yaw"].at(t0), self.tracks["gaze_pitch"].at(t0)
        amp = math.hypot(yaw - gy0, pitch - gp0); Ts = saccade_time(amp)
        self.tracks["gaze_yaw"].set(t0, Ts, yaw); self.tracks["gaze_pitch"].set(t0, Ts, pitch)
        Th = 0.0
        if body:
            Th = 0.30 + amp / 150.0
            self.tracks["twist"].set(t0 + 0.12, Th, clamp(yaw, -40, 40))
            tp = -0.45 * pitch if pitch > 0 else -0.65 * pitch            # 上を見る＝少し反る、下を見る＝おじぎ
            self.tracks["pitch"].set(t0 + 0.14, Th, clamp(tp, -12, 18))
        if at is None: self.t = t0 + 0.14 + Th + hold
        self._lb_end(lid); return self

    def look_around(self, label=None):
        lid = self._lb(label)
        self.look(35, 0, hold=0.7); self.look(-35, 5, hold=0.8); self.look(0, 14, hold=0.6); self.look(0, 0, hold=0.5)
        self._lb_end(lid); return self

    # ---------------------------------------------------------- 向きを変える（足踏み）
    def turn_to(self, heading=None, toward=None, label=None, step=0.30, gap=0.05):
        """その場で向きを変える：目→胴（ねじって先に向く）→足踏み（片足ずつ最大35°）の順。
        step・gap：1歩の時間と歩の間（急ぐときは 0.22・0.03 くらいまで）"""
        if toward is not None:
            d_ = np.array(toward, float) - self._p; heading = math.degrees(math.atan2(-d_[0], d_[1]))
        psi1 = math.radians(heading); d = wrap(psi1 - self._psi)
        if abs(d) < math.radians(2): return self
        lid = self._lb(label)
        t0 = self.t; psi0 = self._psi; ground = self._ground()
        self._neutral(t0, 0.2, keep_gaze=True)
        n = max(2, 2 * math.ceil(abs(d) / math.radians(70)))
        SW, GAP = step, gap
        tr0 = t0 + 0.22; Tr = n * (SW + GAP) + 0.05
        seg = TurnSeg(tr0, tr0 + Tr, self._p, psi0, d); self._seg_add(seg)
        Ts = saccade_time(min(abs(math.degrees(d)), 45)); Tl = 0.35 + abs(math.degrees(d)) / 400.0
        D = math.degrees(d)

        def lead(t, D=D, s=seg, t0=t0, Ts=Ts, Tl=Tl):
            root = math.degrees(s.xy(t)[1] - s.psi0)
            gaze = D * mj(t, t0, Ts) - root
            tw = D * mj(t, t0 + 0.10, Tl) - root
            return {"gaze_yaw": 40 * math.tanh(gaze / 40), "twist": 35 * math.tanh(tw / 35)}
        self.layer(t0, tr0 + Tr + 0.05, lead)
        first = 0 if d > 0 else 1                     # 左へ回るときは左足から
        for k in range(n):
            j = first if k % 2 == 0 else 1 - first
            t_lo = tr0 + 0.03 + k * (SW + GAP); t_ld = t_lo + SW
            psi_k = psi1 if k == n - 1 else seg.xy(min(t_ld + 0.08, seg.t1))[1]
            self._lift_foot(j, t_lo)
            side = -1 if j == 0 else 1
            p = self._p + rgt(psi_k) * side * HIP_X
            self._place(j, t_ld, (*p, ground), psi_k, lift=0.03, kind="turn")
            self.event(t_ld, "step_turn", 0.3, foot=j)
        self._psi = psi1; self.t = tr0 + Tr + 0.12; self._lb_end(lid); return self

    def back_to(self, target, step=0.20, label=None, sw=0.34, gap=0.08, look=True):
        """後ずさりで、向きを変えずに後ろの target へ寄せる。まず左の肩ごしに後ろをちらっと見て、小さな足踏み（片足 step m まで）で下がる。
        下がり始めは後ろへ、止まるときは前へ、加速度の分だけ傾く（最大 約2°）"""
        target = np.array(target, float); dv = target - self._p; D = float(np.linalg.norm(dv))
        if D < 0.02: return self
        lid = self._lb(label); t0 = self.t; psi = self._psi; ground = self._ground()
        self._neutral(t0, 0.2)
        if look: self.layer(t0, t0 + 1.2, lambda t, t0=t0: {"twist": 24.0 * env(t, t0, 0.30, 0.20, 0.45), "gaze_yaw": 50.0 * env(t, t0, 0.18, 0.35, 0.40)})
        n = 2 * max(1, math.ceil(D / step))                           # 両足とも D だけ動く：片足 step m までの歩数
        SW, GAP = sw, gap                                            # ふだんはゆっくり（後ろは見えないので、慎重に）。横歩きは速めにできる
        tr0 = t0 + (0.50 if look else 0.15); Tr = n * (SW + GAP) + 0.05
        seg = ShiftSeg(tr0, tr0 + Tr, self._p, psi, dv); self._seg_add(seg)
        rel = [float((self.feet[j][-1].p[:2] - self._p) @ fwd(psi)) for j in (0, 1)]
        first = 0 if rel[0] >= rel[1] - 0.02 else 1                 # 前にある足から下げる（そろっていれば左）
        for k in range(n):
            j = first if k % 2 == 0 else 1 - first
            t_lo = tr0 + 0.03 + k * (SW + GAP); t_ld = t_lo + SW
            pk = target if k >= n - 2 else seg.xy(min(t_ld + 0.10, seg.t1))[0]
            self._lift_foot(j, t_lo)
            p = pk + rgt(psi) * (-1 if j == 0 else 1) * HIP_X
            self._place(j, t_ld, (*p, ground), psi, lift=0.03, kind="turn")
            self.event(t_ld, "step_turn", 0.35, foot=j)
        self._p = target.copy(); self.t = tr0 + Tr + 0.12; self._lb_end(lid); return self

    # ---------------------------------------------------------- 歩く
    def walk_to(self, target, speed=V_WALK, a_up=A_START, a_dn=A_STOP, label=None):
        """まっすぐ歩いて止まる。向きが違えば先に足踏みで向きを変える。最初に支える足へ体重を移す（予備動作0.25秒）"""
        target = np.array(target, float); dv = target - self._p; D = float(np.linalg.norm(dv))
        if D < 0.05: return self
        lid = self._lb(label)
        psi = math.atan2(-dv[0], dv[1])
        if abs(wrap(psi - self._psi)) > math.radians(8): self.turn_to(math.degrees(psi))
        psi = self._psi
        t0 = self.t; self._neutral(t0, 0.25)
        # 先に出す足：後ろにある足（そろっていれば右足）
        rel = [float((self.feet[j][-1].p[:2] - self._p) @ fwd(psi)) for j in (0, 1)]
        lead = 1 if rel[1] <= rel[0] + 0.02 else 0
        sgn = 1.0 if lead == 1 else -1.0                        # 支える足（反対側）へ傾く：左が＋
        self.layer(t0, t0 + 0.7, lambda t, s=sgn, t0=t0: {"roll": 2.5 * s * env(t, t0, 0.25, 0.0, 0.4), "dx": -0.010 * s * env(t, t0, 0.25, 0.0, 0.4)})
        seg = WalkSeg(t0 + 0.25, self._p, psi, D, speed, a_up, a_dn, lead); self._seg_add(seg)
        t_end = self._walk_steps(seg, lead)
        self._p = self._p + fwd(psi) * D; self.t = max(seg.t1, t_end) + 0.1
        self._lb_end(lid); return self

    def run_to(self, target, speed=V_RUN, label=None):
        """走る：歩き出し→1.45m/s を超えると走り（宙に浮く間ができる）→減速して歩き→両足をそろえて止まる。
        2.0m/s（フルード数0.95）・歩幅0.97m・毎秒4.1歩・地面に着いている割合0.35。最大の加速度 2.0m/s²"""
        return self.walk_to(target, speed=speed, a_up=A_RUN, a_dn=A_RUN, label=label)

    def _walk_steps(self, seg, lead):
        """足の置き場所：足が地面に着いている真ん中の時刻の体の真下（左右は腰の幅）。最後は両足をそろえる"""
        psi = seg.psi0; P1 = seg.p0 + fwd(psi) * seg.D; ground = self._ground()
        final = [np.array([*(P1 + rgt(psi) * s * HIP_X), ground]) for s in (-1, 1)]
        ev = []
        def at_level(q, lev):                           # 位相 q がその値になる時刻
            return float(np.interp(lev, q, seg.tt)) if q[0] <= lev <= q[-1] else None
        for j in (0, 1):
            q = seg.PH + 0.5 * j
            n0 = int(math.floor(q[0] + 1e-9))
            t_lo0 = at_level(q, n0 + seg.B[0])          # 最初に立っている足が離れる時刻
            if t_lo0 is not None: ev.append((t_lo0, "off", j, None))
            for n in range(n0 + 1, int(math.ceil(q[-1])) + 1):
                t_on = at_level(q, float(n))
                if t_on is None: break
                b = seg.beta(t_on)                      # 地面に着いている割合は、着いた瞬間の速さで1歩ごとに決める（途中で変えない）
                t_mid = at_level(q, n + b / 2); t_off = at_level(q, n + b)
                ev.append((t_on, "on", j, (1e9 if t_mid is None else t_mid, b)))
                if t_off is not None: ev.append((t_off, "off", j, None))
        ev.sort(key=lambda e: e[0])
        done = [False, False]; t_last = seg.t1
        for t, kind, j, lev in ev:
            if all(done): break
            if done[j]: continue
            last = self.feet[j][-1]
            if kind == "off":
                if last.t_off is None: last.t_off = t
                continue
            if last.t_off is None: continue
            t_mid, b_step = lev
            if t_mid >= seg.t1 - 1e-6:
                p = final[j]; done[j] = True
            else:
                p = np.array([*(seg.xy(t_mid)[0] + rgt(psi) * (-1 if j == 0 else 1) * HIP_X), ground])
            dist = float(np.linalg.norm(p[:2] - last.p[:2]))
            last.to = 5.0 * clamp(dist / 0.64)
            wr_ = run_weight(b_step); lift_ = LIFT * clamp(dist / 0.30, 0.45, 1.0) * (1 - wr_) + 0.05 * wr_     # 走りは5cm（足首の玉が胴に入らない）
            self._place(j, t, p, psi, lift=lift_, hs=6.0 * clamp(dist / 0.64), kind="walk",
                        tau=clamp((b_step - 0.5) / cadence(seg.vel(t)[0]), 0.02, 0.10))
            self.event(t, "step", clamp(dist / 0.64, 0.2, 1.0), foot=j)
            t_last = t
            if done[j]:
                k = 1 - j; lk = self.feet[k][-1]
                if lk.t_off is None:                     # もう片方が地面にあれば、そろえる一歩
                    dk = float(np.linalg.norm(lk.p[:2] - final[k][:2]))
                    if dk > 0.015:
                        tl = t + 0.10; lk.t_off = tl; lk.to = 10.0 * clamp(dk / 0.3)
                        self._place(k, tl + 0.30, final[k], psi, lift=0.035 * clamp(dk / 0.15, 0.5, 1.0), hs=3.0, kind="close")
                        self.event(tl + 0.30, "step", 0.25, foot=k); t_last = tl + 0.30
                    done[k] = True
        return t_last

    # ---------------------------------------------------------- 跳ぶ
    def _jumps(self, t0, apexes, dxy=(0.0, 0.0), dz=0.0, **kw):
        """跳ぶ区間を足す。足は蹴った瞬間に離れ、着く所（最後に止まる位置の左右）に置く"""
        ground = self._ground()
        seg = JumpSeg(t0, self._p, self._psi, ground, apexes, dxy=dxy, dz=dz, **kw); self._seg_add(seg)
        psi = self._psi
        for k, f in enumerate(seg.flights):
            last = k == len(seg.flights) - 1
            pc = seg.p_end if last else f["p1"]
            for j in (0, 1):
                self._lift_foot(j, f["t0"]).ext_to = f["ext_to"]
                p = pc + rgt(psi) * (-1 if j == 0 else 1) * HIP_X
                c = self._place(j, f["t1"], (*p, f["z1"]), psi, kind="jump", tau=0.02); c.ext = f["ext_ld"]
                if "t_next" in f: c.t_off = f["t_next"]
            self.event(f["t0"], "takeoff", f["v_up"]); self.event(f["t1"], "land", f["v_imp"])
        self._p = seg.p_end
        return seg

    def hops(self, n=3, height=0.06, spin=20.0, label=None):
        """うれしくて跳ねる：小さく n 回（高さ6cm・宙に0.22秒）。宙で左右に少し回る（蹴るときにひねる）"""
        lid = self._lb(label)
        t0 = self.t; self._neutral(t0, 0.15)
        seg = self._jumps(t0 + 0.15, [height] * n, crouch=0.035, T_c=0.18, ext=0.03, depth=0.035, zeta=0.6, settle=0.6)
        for k, f in enumerate(seg.flights):            # 宙で胴を左右交互にひねる（脚に対して）
            self.layer(f["t0"] - 0.08, f["t1"] + 0.12, lambda t, a=f["t0"] - 0.08, d=f["t1"] - f["t0"] + 0.2, s=(1 if k % 2 == 0 else -1): {"twist": s * spin * hump(t, a, d)})
        self.tracks["iris"].set(t0, 0.15, 0.12); self.tracks["iris"].set(seg.t1 - 0.3, 0.5, 0.0)
        for f in seg.flights:
            self.layer(f["t0"] - 0.05, f["t1"] + 0.3, lambda t, a=f["t0"], b=f["t1"]: {"light": 2.5 * env(t, a, 0.04, b - a - 0.04, 0.2), "pitch": -5.0 * hump(t, a - 0.05, b - a + 0.15)})
        self.event(t0 + 0.1, "beep_happy", 1.0)
        self.t = seg.t1; self._lb_end(lid); return self

    def jump_to(self, target, z1=0.0, apex=None, label=None):
        """離れた所・高い所へ跳び乗る：見る→向く→深くしゃがむ（0.36秒）→蹴る→放物線→着地を脚で受け止める"""
        lid = self._lb(label)
        target = np.array(target, float); dv = target - self._p; D = float(np.linalg.norm(dv))
        z0 = self._ground(); dz = z1 - z0
        if D > 0.05:
            self.turn_to(math.degrees(math.atan2(-dv[0], dv[1])))
        apex = apex if apex is not None else max(0.25, dz + 0.20)
        t0 = self.t
        self.look(0, math.degrees(math.atan2(dz - 0.4, max(D, 0.3))), hold=0.35, body=False)
        t1 = self.t
        seg = self._jumps(t1, [apex], dxy=tuple(dv), dz=dz, crouch=0.045, T_c=0.36, ext=0.09, ext_ld=0.06, depth=0.045, zeta=0.6, settle=0.9, T_l=0.16)
        f = seg.flights[0]
        self.layer(t1, seg.t1, lambda t, f=f, t1=t1: {
            "pitch": 8.0 * mj(t, t1, 0.36) * (1 - mj(t, f["t0"] - 0.02, 0.12)) - 4.0 * hump(t, f["t0"], f["t1"] - f["t0"])
                     + 7.0 * (math.exp(-(t - f["t1"]) / 0.12) * math.sin(math.pi * min(1.0, (t - f["t1"]) / 0.24)) if t > f["t1"] else 0.0)})
        self.tracks["gaze_pitch"].set(f["t0"], 0.2, 0.0)
        self.t = seg.t1; self._lb_end(lid); return self

    # ---------------------------------------------------------- 気持ちの動き
    def nod(self, n=2, amp=8.0, label=None):
        """うなずく：下げて（0.2秒）ゆっくり戻す（0.28秒）。2回目は小さく。首がないので胴ぜんぶ（重い）で"""
        lid = self._lb(label)
        t0 = self.t; amps = [amp * (0.65 ** k) for k in range(n)]

        def f(t, t0=t0, amps=amps):
            return {"pitch": sum(a * env(t, t0 + 0.52 * k, 0.20, 0.04, 0.28) for k, a in enumerate(amps))}
        self.layer(t0, t0 + 0.52 * n + 0.5, f)
        self.blinks.append(t0 + 0.06); self.event(t0, "beep_yes", 1.0)
        self.t = t0 + 0.52 * n + 0.5; self._lb_end(lid); return self

    def shake(self, amp=12.0, label=None):
        """首を振る（胴をひねる）：左右へ 12° → 減っていく。ひねりに少し横の傾きがつく"""
        lid = self._lb(label)
        t0 = self.t
        keys = [(0.0, 0.0), (0.20, amp), (0.50, -amp), (0.78, 0.7 * amp), (1.04, -0.4 * amp), (1.30, 0.0)]

        def f(t, t0=t0, keys=keys):
            u = t - t0
            for (ta, a), (tb, b) in zip(keys, keys[1:]):
                if ta <= u <= tb:
                    v = a + (b - a) * smooth((u - ta) / (tb - ta)); return {"twist": v, "roll": 0.15 * v}
            return {}
        self.layer(t0, t0 + 1.3, f); self.event(t0, "beep_no", 1.0)
        self.t = t0 + 1.55; self._lb_end(lid); return self

    def surprise(self, at=None, label=None):
        """驚く：0.2秒の反応の遅れ→反射のまばたき→目を見開く→少し沈んで後ろへ跳ぶ（5cm・12cm）→のけぞったまま固まる→戻る"""
        ts = self._at(at)
        lid = self._lb(label, ts)
        tr = ts + REACT
        self.blinks.append((tr, "fast")); self.no_blink.append((tr - 0.5, tr + 2.0))
        self.tracks["iris"].set(tr + 0.05, 0.06, 0.30); self.tracks["iris"].set(tr + 1.6, 0.8, 0.0)
        self.t = tr
        back = -fwd(self._psi) * 0.12
        seg = self._jumps(tr, [0.05], dxy=tuple(back), crouch=0.02, T_c=0.06, ext=0.03, depth=0.03, zeta=0.55, settle=0.6, T_l=0.2)
        self.layer(tr, tr + 2.4, lambda t, tr=tr: {
            "pitch": -12.0 * env(t, tr, 0.10, 0.75, 0.6),
            "light": 3.0 * env(t, tr, 0.03, 0.10, 0.12) + 1.5 * sum(hump(t, tr + 0.35 + 0.16 * k, 0.1) for k in range(3))})
        self.event(tr, "beep_surprise", 1.0)
        self.t = max(seg.t1, tr + 1.9); self._lb_end(lid); return self

    def think(self, dur=2.2, label=None):
        """考える：目が斜め上へ→胴が少し上を見て首をかしげる（8°）→アンテナの光がゆっくり点滅→右足のつま先で床をたたく→ひらめく"""
        lid = self._lb(label)
        t0 = self.t
        self.look(18, 12, hold=0.0)
        self.tracks["roll"].set(t0 + 0.2, 0.5, -8.0)
        t1 = t0 + dur
        self.layer(t0 + 0.4, t1, lambda t, a=t0 + 0.4, b=t1: {"light": 0.8 * (0.5 - 0.5 * math.cos(2 * math.pi * 1.4 * (t - a))) * env(t, a, 0.2, b - a - 0.4, 0.2)})
        self.layer(t0 + 0.9, t0 + 2.0, lambda t, a=t0 + 0.9: {"tap1": 14.0 * (hump(t, a, 0.28) + hump(t, a + 0.42, 0.28))})
        for k in range(3): self.event(t0 + 0.45 + 0.71 * k, "beep_think", 0.5)
        # ひらめき：光がぱっと強く、目が開き、体が2cm伸びる
        ta = t1
        self.layer(ta, ta + 0.9, lambda t, ta=ta: {"light": 3.0 * env(t, ta, 0.04, 0.15, 0.3), "lift": 0.02 * env(t, ta, 0.10, 0.05, 0.35), "iris": 0.15 * env(t, ta, 0.06, 0.25, 0.4)})
        self.event(ta, "ding", 1.0)
        self.t = ta + 0.05; self.look(0, 0, hold=0.0); self.tracks["roll"].set(ta + 0.05, 0.4, 0.0)
        self.t = ta + 0.9; self._lb_end(lid); return self

    def peer(self, dur=1.6, label=None):
        """のぞき込む：腰から前へ 24° 曲げて 2cm 沈み、目のレンズを前へ出して絞る（ピント合わせ）。少し左右を見て戻る"""
        lid = self._lb(label)
        t0 = self.t
        self.tracks["pitch"].set(t0, 0.7, 24.0); self.tracks["lift"].set(t0, 0.7, -0.02)
        self.tracks["gaze_pitch"].set(t0, 0.1, -18.0)
        self.tracks["zoom"].set(t0 + 0.45, 0.25, 0.016); self.tracks["iris"].set(t0 + 0.45, 0.25, -0.15)
        tm = t0 + 0.7
        self.layer(tm, tm + dur, lambda t, a=tm, d=dur: {"twist": 5.0 * math.sin(2 * math.pi * 0.55 * (t - a)) * env(t, a, 0.3, d - 0.6, 0.3),
                                                          "zoom": 0.004 * hump(t, a + 0.5, 0.3)})
        self.event(t0 + 0.5, "zoom", 0.6)
        t2 = tm + dur
        self.tracks["zoom"].set(t2, 0.25, 0.0); self.tracks["iris"].set(t2, 0.25, 0.0)
        self.tracks["pitch"].set(t2 + 0.1, 0.8, 0.0); self.tracks["lift"].set(t2 + 0.1, 0.8, 0.0); self.tracks["gaze_pitch"].set(t2, 0.1, 0.0)
        self.t = t2 + 1.0; self._lb_end(lid); return self

    def sigh(self, label=None):
        """ほっとする：吸う（1.2cm伸びて少し反る 0.55秒）→吐く（3cm沈み 6°前へ、アンテナが垂れ、目と光がゆるむ 0.9秒）→戻る"""
        lid = self._lb(label)
        t0 = self.t; t1 = t0 + 0.55; t2 = t1 + 0.9; t3 = t2 + 0.5
        self.tracks["lift"].set(t0, 0.55, 0.012); self.tracks["pitch"].set(t0, 0.55, -3.0)
        self.tracks["lift"].set(t1, 0.9, -0.03); self.tracks["pitch"].set(t1, 0.9, 6.0)
        self.tracks["iris"].set(t1, 0.9, -0.15); self.tracks["light"].set(t1, 0.9, -0.4); self.tracks["ant"].set(t1, 0.9, 8.0)
        self.tracks["gaze_pitch"].set(t1, 0.1, -6.0)
        for ch in ("lift", "pitch", "iris", "light", "ant", "gaze_pitch"):
            self.tracks[ch].set(t3, 1.0, 0.0)
        self.blinks.append(t1 + 0.3); self.event(t1, "sigh", 1.0)
        self.t = t3 + 1.0; self._lb_end(lid); return self

    def confused(self, label=None):
        """首をかしげる（？）：目を少し細めて上を見る→右へ10°かしげる（0.5秒）→反対へ少し→戻る。問いかけの電子音"""
        lid = self._lb(label); t0 = self.t
        self.tracks["roll"].set(t0, 0.5, -10.0); self.tracks["twist"].set(t0, 0.5, 6.0)
        self.tracks["iris"].set(t0, 0.3, -0.08); self.tracks["gaze_pitch"].set(t0, saccade_time(8), 8.0)
        self.event(t0 + 0.3, "beep_question", 1.0)
        self.tracks["roll"].set(t0 + 1.1, 0.5, 5.0); self.tracks["twist"].set(t0 + 1.1, 0.5, -4.0)
        for ch in ("roll", "twist", "iris", "gaze_pitch"): self.tracks[ch].set(t0 + 2.0, 0.5, 0.0)
        self.blinks.append(t0 + 0.9)
        self.t = t0 + 2.6; self._lb_end(lid); return self

    def present(self, yaw=45.0, label=None):
        """紹介する（これです）：横の物を見る（目→胴）→アンテナの光を2回点滅→カメラへ向き直って小さくうなずく"""
        lid = self._lb(label)
        self.look(yaw, -8.0, hold=0.15)
        t1 = self.t
        self.layer(t1, t1 + 0.7, lambda t, a=t1: {"light": 2.2 * (hump(t, a, 0.22) + hump(t, a + 0.34, 0.22))})
        self.event(t1, "beep_present", 1.0)
        self.t = t1 + 0.75
        self.look(0.0, 0.0, hold=0.05)
        self.nod(n=1, amp=6.0)
        self._lb_end(lid); return self

    def greet(self, label=None):
        """あいさつ（おじぎ）：ゆっくりまばたき→腰から前へ15°（0.5秒）→止める（0.3秒）→起きる（0.6秒）。光があたたかく1回ふくらむ"""
        lid = self._lb(label); t0 = self.t
        self.blinks.append(t0 + 0.05)
        self.layer(t0, t0 + 1.8, lambda t, t0=t0: {"pitch": 15.0 * env(t, t0 + 0.2, 0.5, 0.3, 0.6), "light": 1.2 * hump(t, t0 + 0.2, 1.2),
                                                   "gaze_pitch": 10.0 * env(t, t0 + 0.2, 0.5, 0.3, 0.6)})
        self.event(t0 + 0.15, "beep_hello", 1.0)
        self.t = t0 + 1.9; self._lb_end(lid); return self

    def awe(self, dur=3.2, pitch=20.0, label=None):
        """見上げる（大きな物に感心する）：目が上へ跳ぶ→体が反る（上を見る分の0.45倍、最大12°）→目の輪が少し開き、光がゆっくりふくらむ→戻る"""
        lid = self._lb(label); t0 = self.t
        self.look(0.0, pitch, hold=max(dur - 1.0, 0.5))
        self.layer(t0, t0 + dur, lambda t, t0=t0, dur=dur: {"iris": 0.10 * env(t, t0 + 0.3, 0.5, dur - 1.4, 0.6),
                                                           "light": 0.6 * hump(t, t0 + 0.4, 1.6), "lift": 0.006 * env(t, t0 + 0.3, 0.6, dur - 1.5, 0.6)})
        self.event(t0 + 0.35, "beep_wow", 1.0)
        self.look(0.0, 0.0, hold=0.3); self._lb_end(lid); return self

    def groove(self, dur=4.0, bpm=96.0, amp=0.006, label=None):
        """曲に合わせて揺れる：拍ごとに少し沈み（amp）、2拍で左右に1.5°。始めと終わりはなめらかに"""
        lid = self._lb(label); t0 = self.t; fb = bpm / 60.0
        def f(t, t0=t0, dur=dur, fb=fb, amp=amp):
            e = env(t, t0, 0.6, max(dur - 1.2, 0.0), 0.6); ph = (t - t0) * fb
            return {"lift": -amp * e * 0.5 * (1 - math.cos(2 * math.pi * ph)), "roll": 1.5 * e * math.sin(math.pi * ph),
                    "gaze_pitch": 6.0 * e}
        self.layer(t0, t0 + dur, f)
        self.t = t0 + dur; self._lb_end(lid); return self

    def load_back(self, T=2.2, gap=0.21, label=None):
        """荷物を積む（後ろの積み込み口から）：アンテナをしまう→荷台がせり上がる（0.5秒）→押し出し板が荷物を荷台へ水平に押す（T秒・躍度最小）
        荷台の上を滑る間、摩擦（0.28）の力でロボは前へ押されるので、後ろへ最大約4.8°踏ん張る。荷物が止まると踏ん張りが戻る（少し行き過ぎる）
        積んだあとは、荷物（ロボの1/4の重さ）が体の後ろにある分、前へ2.3°傾けて釣り合い、重さで0.55cm沈む"""
        lid = self._lb(label); t0 = self.t; self._neutral(t0, 0.2)
        self.set_carry(True, at=t0 + 0.75, ramp=0.5)
        tp = t0 + 0.95; a = CARGO_HALF[0]
        self.layer(t0, tp + T + 1.2, lambda t, t0=t0, t1=tp + T + 0.3: {"breath": -env(t, t0, 0.6, t1 - t0 - 0.6, 0.8)})
        x0 = -(CRADLE_FRONT + gap + a); x1 = 0.0
        ld = dict(t0=t0, tp=tp, T=T, t_end=tp + T, x0=x0, x1=x1, gap=gap, x_deck=-(CRADLE_FRONT + gap), pos=self._p.copy(), psi=self._psi, t_retract=tp + T + 0.3)
        # 踏ん張り：摩擦の力 μ·f·m_p·g（荷物が荷台に載っている割合 f）。2次の遅れ（1.6Hz・減衰0.5）で体が応える
        dt = 1.0 / 240.0; n = int((T + 2.5) / dt); w = 2 * math.pi * 1.6; z = 0.5; y = yv = 0.0; ts = []; ys = []
        for i in range(n):
            t = tp + i * dt; x, v = self.load_x(ld, t)
            g = self.load_frac(x, ld) * math.tanh(max(v, 0.0) / 0.06)
            ya = w * w * (g - y) - 2 * z * w * yv; yv += ya * dt; y += yv * dt
            ts.append(t); ys.append(y)
        brace = math.degrees(math.atan(MU_CRADLE * LOAD_RATIO * 1.2 / 1.0))
        self.layer(tp, ts[-1], lambda t, ts=ts, ys=ys, b=brace: {"pitch": -b * float(np.interp(t, ts, ys))})
        self.loads.append(ld)
        self.event(tp, "push", 1.0); self.event(tp + T, "load_done", 1.0); self.event(tp + T + 0.25, "lock", 0.8)   # 受け皿の錠がトレーの下の穴にかかる
        self.t = tp + T + 0.6; self._lb_end(lid); return self

    def unload_pull(self, T=2.2, gap=0.21, conv=0.5, run=1.5, wait=0.6, x_end=None, label=None):
        """荷物を降ろす（後ろの受け取り台へ）：台の引き込み板がトレーの後ろの縁をつかみ、トレーごと水平に台へ引き取る（T秒・躍度最小）。
        受け皿の上を滑る間、摩擦の力でロボは後ろへ引かれるので、前へ踏ん張る。荷物が台に移ると、重さの分（0.55cm）体が戻る。
        台の上では動力つきローラー（conv m/s）が、さらに run m 奥へ運ぶ。そのあと受け皿を下げ、アンテナが出る"""
        lid = self._lb(label); t0 = self.t; self._neutral(t0, 0.2)
        tp = t0 + wait; a = CARGO_HALF[0]                        # wait：台の腕が伸びてトレーをつかむまで
        self.layer(t0 - 0.6, tp + T + 1.2, lambda t, t0=t0 - 0.6, t1=tp + T + 0.3: {"breath": -env(t, t0, 0.6, t1 - t0 - 0.6, 0.8)})
        x_deck = -(CRADLE_FRONT + gap)                          # 台の手前の端（受け皿の中心から）
        x1 = x_deck - a - 0.05 if x_end is None else x_end       # 引き取り終わり：トレー全体が台の上（x_end：もっと奥まで引き込む）
        ud = dict(t0=t0, tp=tp, T=T, t_end=tp + T, x0=0.0, x1=x1, gap=gap, x_deck=x_deck, conv=conv, run=run,
                  pos=self._p.copy(), psi=self._psi, kind="pull")
        dt = 1.0 / 240.0; n = int((T + 2.5) / dt); w = 2 * math.pi * 1.6; z = 0.5; y = yv = 0.0; ts = []; ys = []
        for i in range(n):
            t = tp + i * dt; x, v = self.load_x(ud, t)
            g = self.load_frac(x, ud) * math.tanh(max(-v, 0.0) / 0.06)
            ya = w * w * (g - y) - 2 * z * w * yv; yv += ya * dt; y += yv * dt
            ts.append(t); ys.append(y)
        brace = math.degrees(math.atan(MU_CRADLE * LOAD_RATIO * 1.2 / 1.0))
        self.layer(tp, ts[-1], lambda t, ts=ts, ys=ys, b=brace: {"pitch": b * float(np.interp(t, ts, ys))})
        self.unloads.append(ud)
        self.event(t0 + 0.05, "unlock", 0.8); self.event(tp - 0.3, "pull", 1.0, T=T); self.event(tp + T, "load_done", 0.8)
        t_conv = tp + T + 0.1; ud["t_conv"] = t_conv
        self.t = tp + T + 0.4
        self.set_carry(False, at=self.t, ramp=0.6)
        self._lb_end(lid); return self

    def load_x(self, ld, t):
        """積む荷物の位置（荷台の中心から前へ）と速さ"""
        u = clamp((t - ld["tp"]) / ld["T"]); x = ld["x0"] + (ld["x1"] - ld["x0"]) * smooth(u)
        v = (ld["x1"] - ld["x0"]) * 30 * u * u * (1 - u) ** 2 / ld["T"] if 0 < u < 1 else 0.0
        return x, v

    @staticmethod
    def load_frac(x, ld=None):
        """荷物の重さのうち、頭の受け皿にかかる割合（てこの比）。重心が積み込み口の端より後ろなら0、受け皿の後ろの端を越えたら1"""
        xd = ld["x_deck"] if ld else -(CRADLE_FRONT + 0.21)
        return clamp((x - xd) / (-CRADLE_FRONT - xd))

    def loaded_at(self, t):
        """荷台の荷物の重さが体にかかっている割合（積む間に増え、後ろへ降ろす間に減る）"""
        L = 0.0
        for ld in self.loads:
            if t >= ld["tp"]: L = self.load_frac(self.load_x(ld, t)[0], ld)
        for un in self.unloads:
            if un.get("kind") == "pull":
                if t >= un["tp"]: L = min(L, self.load_frac(self.load_x(un, t)[0], un))
            elif t >= un["t0"]: L *= 1.0 - mj(t, un["t0"] + 0.4, 1.2)
        if not self.loads and self.carry_at(t): L = 1.0
        return L

    def ant_ext_at(self, t):
        """アンテナが出ている割合：荷台がせり上がる少し前（0.2秒）からしまい、荷台をしまい終えたら0.18秒でぱっと出る"""
        ev = sorted(self.cradle, key=lambda e: e[0]); v = 1.0 - ev[0][1]
        for t0, target, ramp in ev[1:]:
            if target > 0.5:
                ts, T = (t0 - 0.2, 0.35) if ramp > 0 else (t0, 0.0)
                if t < ts: break
                u = clamp((t - ts) / T) if T > 0 else 1.0; v = v * (1.0 - smooth(u))
            else:
                ts, T = (t0 + ramp, 0.18) if ramp > 0 else (t0, 0.0)
                if t < ts: break
                u = clamp((t - ts) / T) if T > 0 else 1.0; v = v + (1.0 - v) * (1.0 - (1.0 - u) ** 3)
        return v

    def ant_pops(self):
        return [t0 + ramp + 0.18 for t0, target, ramp in self.cradle[1:] if target < 0.5 and ramp > 0]

    def rest(self, dur=2.5, label=None):
        """休む：目の輪をゆっくり細め（0.35倍）、体を4cm沈めて前へ6°、アンテナの光を落とす。起きるまでそのまま"""
        lid = self._lb(label); t0 = self.t
        self.tracks["iris"].set(t0, 1.2, -0.65); self.tracks["light"].set(t0, 1.5, -0.85); self.tracks["lift"].set(t0 + 0.3, 1.4, -0.04)
        self.tracks["pitch"].set(t0 + 0.3, 1.4, 6.0); self.tracks["gaze_pitch"].set(t0, 0.8, -10.0); self.tracks["ant"].set(t0 + 0.3, 1.4, 6.0)
        self.no_blink.append((t0, t0 + dur + 0.2)); self.event(t0, "power_down", 1.0)
        self.t = t0 + dur; self._lb_end(lid); return self

    def wake(self, label=None):
        """起きる：2回まばたき→目が開く→体が少し行き過ぎて伸び（2cm）戻る。光が戻る。起動音"""
        lid = self._lb(label); t0 = self.t
        self.blinks += [t0 + 0.05, t0 + 0.42]
        self.tracks["iris"].set(t0 + 0.25, 0.25, 0.0); self.tracks["light"].set(t0, 0.3, 0.0)
        self.tracks["pitch"].set(t0 + 0.1, 0.45, 0.0); self.tracks["gaze_pitch"].set(t0 + 0.1, 0.2, 0.0); self.tracks["ant"].set(t0 + 0.1, 0.45, 0.0)
        self.tracks["lift"].set(t0 + 0.1, 0.35, 0.02); self.tracks["lift"].set(t0 + 0.45, 0.45, 0.0)
        self.layer(t0, t0 + 1.0, lambda t, t0=t0: {"light": 2.0 * hump(t, t0 + 0.05, 0.35)})
        self.event(t0, "boot", 1.0)
        self.t = t0 + 1.2; self._lb_end(lid); return self

    def unload(self, bow=0.9, table=None, label=None):
        """荷物を降ろす：少し反る（4°・0.25秒）→前へ36°のおじぎ（bow 秒）→荷台を10°傾ける→荷物が滑る（摩擦0.28）→戻る
        おじぎが速いと（バイブルの元の0.38秒）、荷台の後ろの端が 3m/s で上がり、荷物を前へ投げてしまう（物理で確認）→ 0.9秒
        table：受け取る台 dict(near=体の中心から台の手前の端まで, depth=奥行き, height=高さ)。なければ床へ落ちる"""
        lid = self._lb(label)
        t0 = self.t; self._neutral(t0, 0.2)
        ta = t0 + 0.2; tb0 = ta + 0.25; tb1 = tb0 + bow; tr = tb1 + 1.3
        self.layer(t0, tr + 0.9, lambda t, ta=ta, tb0=tb0, tb1=tb1, tr=tr, bow=bow: {
            "pitch": -4.0 * mj(t, ta, 0.25) + 40.0 * mj(t, tb0, bow) - 36.0 * mj(t, tr, 0.8),
            "cradle": 10.0 * mj(t, tb0 + 0.4 * bow, 0.6 * bow + 0.2) - 10.0 * mj(t, tr, 0.6),
            "gaze_pitch": -25.0 * env(t, tb0, 0.3, tr - tb0, 0.3)})
        self.unloads.append(dict(t0=tb0, t_back=tr, table=table, pos=self._p.copy(), psi=self._psi))
        self.event(tb0, "unload", 1.0)
        self.t = tr + 0.9; self._lb_end(lid); return self

    def unload_back(self, dock=None, tilt=22.0, lean=6.0, label=None):
        """荷物を後ろの台へ降ろす（ダンプ式）：体を前へ6°傾けて釣り合いをとり、荷台を後ろへ26°傾ける→荷物が後ろへゆっくり滑り（傾き20°・摩擦0.28）、台へ移る
        荷台は体の後ろにはみ出しているので、荷物は胴に触れない。荷物の形（奥行き0.62・高さ0.68）は42°を超えると倒れるので、傾きは控えめ
        dock：受け取る台 dict(near=体の中心から台の手前の端まで（後ろへ）, depth=奥行き, height=高さ)"""
        lid = self._lb(label)
        t0 = self.t; self._neutral(t0, 0.2)
        ta = t0 + 0.2; tc0 = ta + 0.25; tc1 = tc0 + 1.0; tr = tc1 + 2.0
        self.layer(t0, tr + 1.0, lambda t, ta=ta, tc0=tc0, tr=tr: {
            "pitch": lean * mj(t, ta, 0.7) - lean * mj(t, tr + 0.2, 0.8),
            "cradle": -tilt * mj(t, tc0, 1.0) + tilt * mj(t, tr, 0.9),
            "gaze_yaw": 0.0})
        self.unloads.append(dict(t0=tc0, t_back=tr, table=None, dock=dock, pos=self._p.copy(), psi=self._psi))
        self.event(tc0, "unload", 1.0)
        self.t = tr + 1.0; self.set_carry(False, at=tr + 1.1, ramp=0.6)       # 荷台をしまう（荷物は台の上に残る）
        self._lb_end(lid); return self

    def set_carry(self, on, at=None, ramp=0.5):
        """荷物を持つ／持たない。荷台は運ぶ間だけ出る：持つ前に ramp 秒でせり上がり、持たなくなったら ramp 秒でしまう（カットの瞬間なら一瞬で）"""
        t = self._at(at); self.carry.append((t, bool(on)))
        cut = any(abs(t - tc) < 1e-6 for tc in self.cuts)
        if on: self.cradle.append((t if cut else t - ramp, 1.0, 0.0 if cut else ramp))
        else: self.cradle.append((t, 0.0, ramp))
        if not cut: self.event(t - ramp if on else t, "cradle_out" if on else "cradle_in", 0.6)
        return self

    def cradle_at(self, t):
        v = 0.0
        for t0, target, ramp in sorted(self.cradle, key=lambda e: e[0]):
            if t < t0: break
            frm = v; v = frm + (target - frm) * (mj(t, t0, ramp) if ramp > 0 else 1.0)
        return v

    def teleport(self, pos, heading):
        """場面の切り替え（カット）：体と足をその場で置き直す"""
        t = self.t; p = np.array(pos, float); psi = math.radians(heading); z = self._ground()
        self._seg_add(Seg(t, t, p, psi))
        for j in (0, 1):
            self._lift_foot(j, t)
            self._place(j, t, (*(p + rgt(psi) * (-1 if j == 0 else 1) * HIP_X), z), psi)
        for ch, tr in self.tracks.items(): tr.set(t, 0.0, 0.0)
        self.cuts.append(t); self._p, self._psi = p, psi
        return self

    # ---------------------------------------------------------- まばたき（自動：3〜5秒ごと）
    def blink_times(self, T, seed=11):
        rng = random.Random(seed); out = []
        explicit = [b if isinstance(b, tuple) else (b, "normal") for b in self.blinks]
        t = rng.uniform(1.0, 2.5)
        while t < T:
            near = any(abs(t - b[0]) < 0.8 for b in explicit) or any(a <= t <= b for a, b in self.no_blink)
            if not near: out.append((t, "normal"))
            t += rng.uniform(3.0, 5.0)
        return sorted(out + explicit)

    # ---------------------------------------------------------- ある時刻の姿勢（バネより前の、決まった動き）
    def prep(self):
        self._ton = [[c.t_on for c in L] for L in self.feet]

    def foot_state(self, j, t):
        L = self.feet[j]; ton = self._ton[j] if getattr(self, "_ton", None) else [c.t_on for c in L]
        i = max(bisect.bisect_right(ton, t) - 1, 0)
        c = L[i]
        if c.t_off is None or t < c.t_off or i + 1 >= len(L):
            return ("stance", c, None, 0.0)
        nx = L[i + 1]
        T = nx.t_on - c.t_off
        if T <= 1e-6: return ("stance", nx, None, 0.0)
        return ("air" if nx.kind == "jump" else "swing", c, nx, clamp((t - c.t_off) / T))

    def kin(self, t, blinks=()):
        seg = self._seg(t)
        p, psi = seg.xy(t)
        v, a = seg.vel(t); ph = seg.phase(t)
        walk = clamp(v / 0.4) if ph is not None else 0.0
        ch = {k: tr.at(t) for k, tr in self.tracks.items()}
        ch["blink"] = 0.0; ch["tap0"] = ch["tap1"] = 0.0
        for t0, t1, fn in self.layers:
            if t0 <= t <= t1:
                for k, val in fn(t).items():
                    if k == "blink": ch[k] = max(ch[k], val)
                    else: ch[k] = ch.get(k, 0.0) + val
        beta = seg.beta(t) if ph is not None else BETA; wr = run_weight(beta) if ph is not None else 0.0
        if ph is not None and walk > 0:
            cph = math.cos(2 * math.pi * (ph - beta / 2))
            ch["roll"] += ROLL_WALK * walk * (1 - 0.6 * wr) * cph; ch["dx"] += -0.012 * walk * (1 - 0.6 * wr) * cph
        lean = math.degrees(math.atan2(a, G)) + LEAN_WALK * walk + 5.0 * wr
        body = p + rgt(psi) * ch["dx"]
        fs = [self.foot_state(j, t) for j in (0, 1)]
        # ---- 脚の付け根の高さ
        hz = seg.hip(t); airborne = any(f[0] == "air" for f in fs)
        if hz is None:
            num = den = 0.0; ws = []
            for j, (mode, c, nx, q) in enumerate(fs):
                if mode != "stance": ws.append(0.0); continue
                w = smooth((t - c.t_on) / c.tau) if c.t_on > -1e8 else 1.0
                if c.t_off is not None: w *= 1.0 - smooth((t - (c.t_off - c.tau)) / c.tau)
                w = max(w, 1e-4); ws.append(w)
                hip_j = body + rgt(psi) * (-1 if j == 0 else 1) * HIP_X
                d = float((hip_j - c.p[:2]) @ fwd(psi)) if seg.kind != "turn" else 0.0       # その場で回るときは沈まない
                d = min(abs(d), 0.9 * L_LEG)
                num += w * (c.p[2] + HIP_REST - min(L_LEG - math.sqrt(L_LEG ** 2 - d * d), 0.07)); den += w      # 沈みは7cmまで
            hz = num / den if den > 0 else self._ground() + HIP_REST
            if len(ws) == 2 and walk > 0: hz -= DS_DIP * walk * 4 * ws[0] * ws[1] / max((ws[0] + ws[1]) ** 2, 1e-9)
            if wr > 0:                                     # 走り：ばねと質点の上下（宙の時間 t_f と着いている時間 t_c から）
                st = [k for k, f in enumerate(fs) if f[0] == "stance"]; dz = 0.0
                if len(st) == 1:
                    j = st[0]; c = fs[j][1]; o = fs[1 - j]
                    if c.t_off is not None and o[0] == "swing" and c.t_on > -1e8:
                        tc = c.t_off - c.t_on; tf = max(0.0, o[2].t_on - c.t_off)
                        dz = -G * tf * tc / (2 * math.pi) * math.sin(math.pi * clamp((t - c.t_on) / tc))
                elif len(st) == 0 and fs[0][0] == "swing" and fs[1][0] == "swing":
                    t_lo = max(fs[0][1].t_off, fs[1][1].t_off); t_td = min(fs[0][2].t_on, fs[1][2].t_on); tf = max(t_td - t_lo, 1e-3)
                    tau = clamp(t - t_lo, 0.0, tf); dz = 0.5 * G * tf * tau - 0.5 * G * tau * tau
                    airborne = True
                h_run = (min(f[1].p[2] for f in fs) if fs else 0.0) + HIP_REST + 0.02 + dz      # 走る間は脚を2cm伸ばしておく（ばねの縮みしろ）
                hz = (1 - wr) * hz + wr * h_run
            for j, (mode, c, nx, q) in enumerate(fs):        # 足踏み・そろえる一歩：足を上げている間、少し沈み、支える足へ傾く
                if mode == "swing" and nx.kind in ("turn", "close"):
                    hz -= 0.006 * math.sin(math.pi * q); ch["roll"] += (2.5 if j == 1 else -2.5) * math.sin(math.pi * q)
        calm = (1.0 - walk) * (0.0 if isinstance(seg, JumpSeg) and seg.t0 <= t <= seg.t1 else 1.0)
        loaded = self.loaded_at(t) if self.loads else 0.0                      # 積んだ荷物の重さ：0.55cm沈み、前へ2.3°（釣り合い）
        br = clamp(1.0 + ch.get("breath", 0.0))                               # 荷物を受け渡す間は、息（上下 ±8mm）を止めて台と高さをそろえる
        hz += ch["lift"] + 0.008 * math.sin(2 * math.pi * 0.25 * t) * calm * br - 0.0055 * loaded
        ch["pitch"] += LOAD_LEAN * loaded
        root = np.array([body[0], body[1], hz - HIP_Z])
        Rr = rotz(psi)
        # ---- 足
        feet = []
        for j, (mode, c, nx, q) in enumerate(fs):
            side = -1 if j == 0 else 1
            hip_w = root + Rr @ np.array([side * HIP_X, 0.0, HIP_Z])
            if mode == "stance":
                ank, fpsi, fp = self._stance_foot(c, t, ch.get("tap%d" % j, 0.0))
            elif mode == "swing":
                a0, ps0, p0 = self._stance_foot(c, c.t_off, 0.0); a1, ps1, p1 = self._stance_foot(nx, nx.t_on, 0.0)
                sq = smooth(q)
                ank = a0 + (a1 - a0) * sq
                bump = max(0.0, max(c.p[2], nx.p[2]) + SOLE + nx.lift - 0.5 * (a0[2] + a1[2]))
                ank[2] += bump * math.sin(math.pi * q)
                fpsi = ps0 + wrap(ps1 - ps0) * sq; fp = p0 + (p1 - p0) * sq
            else:                                             # 宙：足は体と一緒に動き、少し縮める
                sq = smooth(q)
                Ba = seg.xy(c.t_off)[0] + rgt(psi) * side * HIP_X; Bb = seg.xy(nx.t_on)[0] + rgt(psi) * side * HIP_X
                off = (c.p[:2] - Ba) * (1 - sq) + (nx.p[:2] - Bb) * sq
                ank = np.array([hip_w[0] + off[0], hip_w[1] + off[1], 0.0])
                e0, e1 = c.ext_to, nx.ext
                leg = ANKLE + e0 * (1.0 - smooth(q / 0.3)) + e1 * smooth((q - 0.7) / 0.3)
                ank[2] = hip_w[2] - leg
                fpsi = c.psi + wrap(nx.psi - c.psi) * sq; fp = -6.0 * math.sin(math.pi * q)
            dl = ank - hip_w; ext = float(np.linalg.norm(dl)) - ANKLE
            feet.append(dict(ankle=ank, psi=fpsi, pitch=fp, mode=mode, ext=ext, top=hip_w + dl / max(np.linalg.norm(dl), 1e-9) * ext))
        # ---- 胴（脚の付け根の高さを中心に前後・左右に傾き、上でひねる）
        pitch = ch["pitch"] + lean; roll = ch["roll"]; twist = ch["twist"]
        Rl = rotz(math.radians(twist)) @ rotx(-math.radians(pitch)) @ roty(-math.radians(roll))
        Pv = np.array([0.0, 0.0, HIP_Z]); tor_l = Pv + Rl @ (np.array([0.0, 0.0, TORSO_Z]) - Pv)
        Rw = Rr @ Rl; tor_w = root + Rr @ tor_l
        ant_tip = tor_w + Rw @ (ANT_BASE + roty(ANT_REST_Y) @ ANT_TIP)
        gap = 1.0; shin = 0.0
        for f in feet:
            q_ = Rw.T @ (f["top"] - tor_w); shin = max(shin, (q_[0] / 0.51) ** 2 + (q_[1] / 0.46) ** 2 + (q_[2] / 0.49) ** 2)
            q_ = Rw.T @ (f["ankle"] - tor_w); r2 = (q_[0] / 0.51) ** 2 + (q_[1] / 0.46) ** 2
            if r2 < 1.0: gap = min(gap, -0.49 * math.sqrt(1.0 - r2) - (q_[2] + 0.08))
        cr_w = tor_w + Rw @ (CRADLE - np.array([0.0, 0.0, SADDLE_DROP * (1.0 - self.cradle_at(t))])); Rcr = Rw @ rotx(-math.radians(ch["cradle"]))
        cargo_pt = cr_w + Rcr @ np.array([0.0, 0.0, CARGO_Z])
        # ---- 目
        b = ch["blink"]
        for tb, kind in blinks:
            if tb - 0.01 <= t <= tb + 0.4:
                b = max(b, blink_shape(t, tb, 1 / 24, 0.5 / 24, 2 / 24) if kind == "fast" else blink_shape(t, tb))
        eye_yaw = ch["gaze_yaw"] - twist; eye_pitch = ch["gaze_pitch"] + 0.6 * ch["pitch"]
        iris = dict(scale=max(0.05, (1.0 + ch["iris"]) * (1.0 - 0.85 * b)), dx=-IRIS_SHIFT * math.tanh(eye_yaw / 35.0),
                    dz=IRIS_SHIFT * math.tanh(eye_pitch / 35.0), zoom=ch["zoom"])
        return dict(t=t, root=root, psi=psi, pitch=pitch, roll=roll, twist=twist, feet=feet, Rw=Rw, tor_w=tor_w, ant_tip=ant_tip,
                    cr_w=cr_w, Rcr=Rcr, cargo_pt=cargo_pt, iris=iris, light=max(0.0, 1.0 + ch["light"]), cradle=ch["cradle"],
                    ant_bias=ch["ant"], v=v, a=a, walk=walk, airborne=airborne, carry=self.carry_at(t), gap=gap, shin=shin, cradle_out=self.cradle_at(t),
                    ant_ext=self.ant_ext_at(t), loaded=loaded)

    def carry_at(self, t):
        on = False
        for tc, val in self.carry:
            if tc <= t: on = val
        return on

    def _stance_foot(self, c, t, tap=0.0):
        """地面にある足：かかとから着き（つま先を上げて）→べた足→かかとを上げてつま先で離れる。足が滑らない"""
        hs = to = 0.0
        if c.hs > 0 and c.t_on > -1e8:
            T = 0.06 if c.t_off is None else 0.18 * (c.t_off - c.t_on)
            hs = c.hs * (1.0 - smooth((t - c.t_on) / max(T, 1e-3)))
        if c.t_off is not None and c.to > 0:
            T = 0.35 * (c.t_off - max(c.t_on, c.t_off - 1.0))
            to = c.to * smooth((t - (c.t_off - T)) / max(T, 1e-3))
        pitch = hs + tap - to
        Rz_ = rotz(c.psi)
        if pitch >= 0:
            piv = c.p + Rz_ @ HEEL; ank = piv + Rz_ @ rotx(math.radians(pitch)) @ (np.array([0.0, 0.0, SOLE]) - HEEL)
        else:
            piv = c.p + Rz_ @ TOE; ank = piv + Rz_ @ rotx(math.radians(pitch)) @ (np.array([0.0, 0.0, SOLE]) - TOE)
        return ank, c.psi, pitch


# ================================================================ 荷物（降ろすときの物理：荷台の上を滑る→前の端で傾く→落ちる→床で跳ねて止まる）
class Cargo2D:
    """進む向きと上下の面の中の箱（奥行き 2a・高さ 2b）。荷台・床との当たり：箱の角と線、動く点（荷台の端）と箱の面。
    衝突は撃力（反発 e・クーロン摩擦 mu）を何回か繰り返して解く"""
    def __init__(self, a=CARGO_HALF[0], b=CARGO_HALF[1], mu=0.28, e=0.25):
        self.a, self.b, self.mu, self.e = a, b, mu, e
        self.m = 1.0; self.I = (4 * a * a + 4 * b * b) / 12.0
        self.x = np.zeros(2); self.v = np.zeros(2); self.th = 0.0; self.w = 0.0

    def R(self):
        c, s = math.cos(self.th), math.sin(self.th); return np.array([[c, -s], [s, c]])

    def _impulse(self, p, n, depth, vel, h, mu=None):
        mu = self.mu if mu is None else mu
        r = p - self.x
        vp = self.v + self.w * np.array([-r[1], r[0]]) - vel
        vn = float(vp @ n)
        rn = r[0] * n[1] - r[1] * n[0]; kn = 1.0 / self.m + rn * rn / self.I
        bias = min(0.2 * max(depth - 0.002, 0.0) / h, 0.3)        # めり込みを戻す速さ（上限 0.3m/s）
        jn = max(0.0, (-(1 + (self.e if vn < -0.5 else 0.0)) * vn + bias) / kn)
        self.v = self.v + jn * n / self.m; self.w += rn * jn / self.I
        u = np.array([n[1], -n[0]])
        vp = self.v + self.w * np.array([-r[1], r[0]]) - vel
        vt = float(vp @ u); rt = r[0] * u[1] - r[1] * u[0]; kt = 1.0 / self.m + rt * rt / self.I
        jt = clamp(-vt / kt, -mu * jn, mu * jn)
        self.v = self.v + jt * u / self.m; self.w += rt * jt / self.I

    def step(self, h, planes, points, ellipses=()):
        """planes：[(点 o, 外向きの法線 n, 線の向き u, 範囲 (s0, s1), 速さ関数 vel(点))]、points：[(点 q, 速さ)]
        ellipses：[(中心 c, 前の軸 ex, 上の軸 ez, 半径 rx, rz, 速さ関数 vel(点))]（胴とレンズ）"""
        self.v = self.v + np.array([0.0, -G]) * h
        for _ in range(5):
            R = self.R()
            for c, ex, ez, rx, rz, vel in ellipses:
                for sx in (-1, 1):                      # 箱の角が楕円の中
                    for sy in (-1, 1):
                        p = self.x + R @ np.array([sx * self.a, sy * self.b]); d = p - c
                        lx, lz = float(d @ ex) / rx, float(d @ ez) / rz; r2 = lx * lx + lz * lz
                        if r2 < 1.0:
                            n = ex * (lx / rx) + ez * (lz / rz); n /= np.linalg.norm(n)
                            self._impulse(p, n, (1.0 - math.sqrt(r2)) * min(rx, rz), vel(p), h)
                for k in range(28):                     # 楕円の上の点が箱の中
                    ph = -0.6 * math.pi + 1.6 * math.pi * k / 27
                    q = c + ex * rx * math.cos(ph) + ez * rz * math.sin(ph)
                    ql = R.T @ (q - self.x); dx_, dy_ = self.a - abs(ql[0]), self.b - abs(ql[1])
                    if dx_ <= 0 or dy_ <= 0: continue
                    nl = np.array([0.0, math.copysign(1.0, ql[1])]) if dy_ < dx_ else np.array([math.copysign(1.0, ql[0]), 0.0])
                    self._impulse(q, -(R @ nl), min(dx_, dy_), vel(q), h)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    p = self.x + R @ np.array([sx * self.a, sy * self.b])
                    for pl in planes:
                        o, n, u, (s0, s1), vel = pl[:5]; mu = pl[5] if len(pl) > 5 else None
                        s = float((p - o) @ u)
                        if not (s0 <= s <= s1): continue
                        depth = float((o - p) @ n)
                        if depth >= -1e-4: self._impulse(p, n, depth, vel(p), h, mu)
            for pt in points:
                q, vq = pt[:2]; mu = pt[2] if len(pt) > 2 else None; ns = pt[3] if len(pt) > 3 else None
                ql = R.T @ (q - self.x)
                dx_, dy_ = self.a - abs(ql[0]), self.b - abs(ql[1])
                if dx_ <= 0 or dy_ <= 0: continue
                if ns is not None:                       # 支える点（荷台・台の端）：その面の法線の向きにだけ押す
                    nl_ = R.T @ ns; d = 1e9
                    for i, ext_ in ((0, self.a), (1, self.b)):
                        if abs(nl_[i]) > 1e-6:
                            d = min(d, (ql[i] + ext_) / nl_[i] if nl_[i] > 0 else (ext_ - ql[i]) / -nl_[i])
                    self._impulse(q, ns, d, vq, h, mu); continue
                nl = np.array([0.0, math.copysign(1.0, ql[1])]) if dy_ < dx_ else np.array([math.copysign(1.0, ql[0]), 0.0])
                self._impulse(q, -(R @ nl), min(dx_, dy_), vq, h, mu)
        self.x = self.x + self.v * h; self.th += self.w * h


def simulate(plan, fps=FPS, sub=10, t_end=None, seed=11, ant_f=2.5, ant_z=0.20, cargo_f=2.2, cargo_z=0.35):
    """毎コマの姿勢。アンテナ（2.5Hz・減衰0.2）と荷物（2.2Hz・減衰0.35）は、根元の加速度で揺れるバネとして積分する"""
    T = plan.t + 0.5 if t_end is None else t_end
    h = 1.0 / (fps * sub); N = int(math.ceil(T / h)) + 1
    blinks = plan.blink_times(T, seed); plan.prep()
    ks = [plan.kin(i * h, blinks) for i in range(N + 2)]
    up = np.array([0.0, 0.0, G])
    # ---- アンテナ：先の玉に重さが集まった棒。根元の座標で見た見かけの力（加速度＋重力）で振れる
    P = np.array([k["ant_tip"] for k in ks]); acc = np.zeros_like(P); acc[1:-1] = (P[2:] - 2 * P[1:-1] + P[:-2]) / (h * h)
    cut_i = set()
    for tc in plan.cuts:
        i0 = int(round(tc / h)); cut_i |= set(range(i0 - 2, i0 + 3))
    for i in cut_i:
        if 0 <= i < len(acc): acc[i] = 0.0
    w = 2 * math.pi * ant_f; ay = ax = vy = vx = 0.0; ant = []
    pops = {int(round(tp_ / h)) for tp_ in plan.ant_pops()}
    for i, k in enumerate(ks):
        if i in cut_i or k["ant_ext"] < 0.02: ay = ax = vy = vx = 0.0
        if i in pops: vy += 1.6                                   # ぱっと出て止まった瞬間：先の玉が前後に少し揺れる
        f = k["Rw"].T @ (acc[i] + up) - up                      # 立っているときの重力は、ばねの休みの形に含まれる
        bias = math.radians(k["ant_bias"])
        fy = -f[1] / ANT_LEN; fx = -f[0] / ANT_LEN
        vy += (-w * w * (ay - bias) - 2 * ant_z * w * vy + fy) * h; ay += vy * h
        vx += (-w * w * ax - 2 * ant_z * w * vx + fx) * h; ax += vx * h
        ay = clamp(ay, -0.6, 0.6); ax = clamp(ax, -0.6, 0.6)
        e_ = k["ant_ext"]; ant.append((ay * e_, ax * e_))
    # ---- 荷物：運ぶ間は荷台の上を前後にわずかに滑る（ベルトのばね ±7cm）。降ろすときは Cargo2D
    Pc = np.array([k["cargo_pt"] for k in ks]); accc = np.zeros_like(Pc); accc[1:-1] = (Pc[2:] - 2 * Pc[1:-1] + Pc[:-2]) / (h * h)
    for i in cut_i:
        if 0 <= i < len(accc): accc[i] = 0.0
    wc = 2 * math.pi * cargo_f; s = sv = 0.0; cargo = []
    un = plan.unloads[0] if plan.unloads else None; box = None; free_from = None; rest_at = None
    ld = plan.loads[0] if plan.loads else None
    if ld is not None:                                         # 積み込み口の高さ＝押し始めの荷台の上面
        kr = ks[min(int(round(ld["tp"] / h)), len(ks) - 1)]
        top = kr["cr_w"] + kr["Rcr"] @ np.array([0.0, 0.0, CRADLE_TOP])
        ld["deck"] = dict(top_z=float(top[2]), center=kr["cr_w"][:2].tolist(), psi=ld["psi"], edge=ld["x_deck"])
    upl = plan.unloads[0] if plan.unloads and plan.unloads[0].get("kind") == "pull" else None
    if upl is not None:                                         # 受け取り台の高さ＝引き取り始めの受け皿の上面
        kr = ks[min(int(round(upl["tp"] / h)), len(ks) - 1)]
        top = kr["cr_w"] + kr["Rcr"] @ np.array([0.0, 0.0, CRADLE_TOP])
        upl["deck"] = dict(top_z=float(top[2]), center=kr["cr_w"][:2].tolist(), psi=upl["psi"], edge=upl["x_deck"])
        un = None
    for i, k in enumerate(ks):
        t = k["t"]
        if ld is not None and t < ld["t_end"]:
            cargo.append(("free", _load_world(plan, ld, k))); s = sv = 0.0
            continue
        if upl is not None and t >= upl["tp"]:
            cargo.append(("free", _pull_world(plan, upl, k))); continue
        if un is not None and t >= un["t0"] and box is None and k["carry"]:
            box = _cargo_start(k, s); free_from = t; s_hand, sv_hand = s, sv
        if box is not None:
            if rest_at is None:
                _cargo_step(box, ks, i, h, plan, un, s_hand if i == int(round(free_from / h)) else 0.0, sv_hand if i == int(round(free_from / h)) else 0.0)
                if t > un["t_back"] + 1.5 and abs(box.v).max() < 0.005 and abs(box.w) < 0.01: rest_at = t      # ロボが戻り終えてから止める
            cargo.append(("free", _cargo_world(box, plan, k)))
            continue
        if i in cut_i: s = sv = 0.0
        if CARGO_LOCK: cargo.append(("on", 0.0)); continue                 # 錠がかかっているので、受け皿とトレーは一体
        f = k["Rcr"].T @ (accc[i] + up) - up
        sv += (-wc * wc * s - 2 * cargo_z * wc * sv - f[1]) * h; s = clamp(s + sv * h, -0.07, 0.07)
        cargo.append(("on", s))
    frames = []
    for i in range(0, N, sub):
        k = ks[i]
        frames.append(dict(t=k["t"], root=k["root"].tolist(), psi=k["psi"], pitch=k["pitch"], roll=k["roll"], twist=k["twist"],
                           feet=[dict(ankle=f["ankle"].tolist(), psi=f["psi"], pitch=f["pitch"], mode=f["mode"], ext=f["ext"]) for f in k["feet"]],
                           ant=ant[i], iris=k["iris"], light=k["light"], cradle=k["cradle"], cargo=cargo[i], carry=k["carry"],
                           cradle_out=k["cradle_out"], cargo_vis=bool(k["carry"] or cargo[i][0] == "free"), ant_ext=k["ant_ext"], loaded=k["loaded"],
                           v=k["v"], a=k["a"], walk=k["walk"], airborne=k["airborne"], gap=k["gap"], shin=k["shin"]))
    return frames


# ---- 荷物の2次元の計算（体の進む向きの縦の面。原点はおじぎを始めたときの体の真下）
def _plane(plan, k):
    psi = plan._seg(k["t"]).xy(k["t"])[1]
    return fwd(psi), np.array(k["root"][:2])


def _cargo_start(k, s):
    box = Cargo2D()
    box._fw = None; box._o = None
    return box


def _to2(box, p3):
    return np.array([float((p3[:2] - box._o) @ box._fw), float(p3[2])])


def _cargo_step(box, ks, i, h, plan, un, s0=0.0, sv0=0.0):
    k = ks[i]; k0 = ks[max(i - 1, 0)]
    if box._fw is None:
        box._fw, box._o = fwd(un["psi"]), np.array(un["pos"], float)
        off = k["Rcr"] @ np.array([0.0, s0, 0.0])
        box.x = _to2(box, k["cargo_pt"] + off)
        fwd3 = k["Rcr"] @ np.array([0.0, 1.0, 0.0]); box.th = math.atan2(fwd3[2], float(fwd3[:2] @ box._fw))
        box.v = (_to2(box, k["cargo_pt"]) - _to2(box, k0["cargo_pt"])) / h + np.array([float((k["Rcr"] @ np.array([0, sv0, 0]))[:2] @ box._fw), 0.0])
        box.w = 0.0
        box._floor = min(f["ankle"][2] for f in k["feet"]) - SOLE
    def frame2(kk):
        Rc = kk["Rcr"]; o = _to2(box, kk["cr_w"] + Rc @ np.array([0.0, 0.0, CRADLE_TOP]))
        u3 = Rc @ np.array([0.0, 1.0, 0.0]); u = np.array([float(u3[:2] @ box._fw), u3[2]]); u /= np.linalg.norm(u)
        return o, u
    def body2(kk):
        Rw = kk["Rw"]; c = _to2(box, kk["tor_w"])
        e1 = Rw @ np.array([0.0, 1.0, 0.0]); e2 = Rw @ np.array([0.0, 0.0, 1.0])
        ex = np.array([float(e1[:2] @ box._fw), e1[2]]); ez = np.array([float(e2[:2] @ box._fw), e2[2]])
        return c, ex / np.linalg.norm(ex), ez / np.linalg.norm(ez)
    o1, u1 = frame2(k); o0, u0 = frame2(k0)
    n1 = np.array([-u1[1], u1[0]])
    wv = (math.atan2(u1[1], u1[0]) - math.atan2(u0[1], u0[0])) / h; vo = (o1 - o0) / h

    def vel_rigid(p, o=o1, vo=vo, wv=wv):
        r = p - o; return vo + wv * np.array([-r[1], r[0]])
    edge = o1 + u1 * CRADLE_FRONT; back = o1 - u1 * CRADLE_FRONT
    planes = [(o1, n1, u1, (-CRADLE_FRONT, CRADLE_FRONT), vel_rigid),
              (np.array([0.0, box._floor]), np.array([0.0, 1.0]), np.array([1.0, 0.0]), (-50.0, 50.0), lambda p: np.zeros(2))]
    points = [(edge, vel_rigid(edge), None, n1), (back, vel_rigid(back), None, n1)]
    dk = un.get("dock")
    if dk:                                       # 受け取る台：ローラー（摩擦 dk["mu"]）、奥に高さ10cmの止め
        top = box._floor + dk["height"]; x0 = -dk["near"] - dk["depth"]; mu_d = dk.get("mu", 0.05)
        v_c = np.array([-dk.get("v", 0.0), 0.0])                 # 動力つきローラー：台の面が奥へ v で動く（なければ止まったローラー）
        planes.append((np.array([x0, top]), np.array([0.0, 1.0]), np.array([1.0, 0.0]), (0.0, dk["depth"]), lambda p, v_c=v_c: v_c, mu_d))
        planes.append((np.array([x0, top]), np.array([1.0, 0.0]), np.array([0.0, 1.0]), (0.0, dk.get("lip", 0.10)), lambda p: np.zeros(2), 0.3))
        points += [(np.array([-dk["near"], top]), np.zeros(2), mu_d, np.array([0.0, 1.0])), (np.array([x0, top + dk.get("lip", 0.10)]), np.zeros(2), 0.3)]
    tb = un.get("table")
    if tb:
        top = box._floor + tb["height"]
        planes.append((np.array([tb["near"], top]), np.array([0.0, 1.0]), np.array([1.0, 0.0]), (0.0, tb["depth"]), lambda p: np.zeros(2)))
        points += [(np.array([tb["near"], top]), np.zeros(2), None, np.array([0.0, 1.0])), (np.array([tb["near"] + tb["depth"], top]), np.zeros(2), None, np.array([0.0, 1.0]))]
    c1, ex1, ez1 = body2(k); c0, ex0, ez0 = body2(k0)
    wb = (math.atan2(ex1[1], ex1[0]) - math.atan2(ex0[1], ex0[0])) / h; vb = (c1 - c0) / h

    def vel_body(p, c=c1, vb=vb, wb=wb):
        r = p - c; return vb + wb * np.array([-r[1], r[0]])
    lens_c = c1 + ex1 * LENS["y"] + ez1 * LENS["z"]
    # 胴：本当の形（前後0.46・上下0.49）は荷物の底より3cm高い所がある（荷台が胴の上にくぼんで付いている）。荷物の下に収まる大きさで当てる
    ellipses = [(c1, ex1, ez1, 0.44, 0.445, vel_body), (lens_c, ex1, ez1, LENS["depth"], LENS["r"], vel_body)]
    for _ in range(5): box.step(h / 5, planes, points, ellipses)


def _load_world(plan, ld, k):
    """積む荷物：積み込み口（止まっている）の上 → 荷台の上。荷台に載った割合 f で、2つの置き場所を混ぜる"""
    t = k["t"]; x, _ = plan.load_x(ld, t); f = plan.load_frac(x, ld); dk = ld["deck"]
    fw = fwd(ld["psi"]); c = np.array(dk["center"])
    p_deck = np.array([c[0] + fw[0] * x, c[1] + fw[1] * x, dk["top_z"] + CARGO_HALF[1]])
    p_cr = k["cr_w"] + k["Rcr"] @ np.array([0.0, x, CARGO_Z])
    pos = (1 - f) * p_deck + f * p_cr
    f3 = k["Rcr"] @ np.array([0.0, 1.0, 0.0]); th = math.atan2(f3[2], float(np.hypot(f3[0], f3[1])))
    R = rotz(ld["psi"]) @ rotx(f * th)
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = pos
    return M.tolist()


def _pull_world(plan, up, k):
    """引き取る荷物：受け皿の上 → 受け取り台（止まっている）。台に載った割合で2つの置き場所を混ぜる。台に移ったあとはローラーで奥へ"""
    t = k["t"]; x, _ = plan.load_x(up, t); f = plan.load_frac(x, up); dk = up["deck"]
    fw = fwd(up["psi"]); c = np.array(dk["center"])
    if t > up["t_conv"]:                                       # ローラー：なめらかに動き出し、run m 進んで止まる
        T_r = up["run"] / up["conv"] + 0.6; x = x - up["run"] * mj(t, up["t_conv"], T_r)
    p_deck = np.array([c[0] + fw[0] * x, c[1] + fw[1] * x, dk["top_z"] + CARGO_HALF[1]])
    p_cr = k["cr_w"] + k["Rcr"] @ np.array([0.0, x, CARGO_Z])
    pos = f * p_cr + (1 - f) * p_deck
    if x + 0.295 > -CRADLE_FRONT: pos[2] = max(pos[2], p_cr[2])   # トレーの前がまだ受け皿に載っている間は、受け皿より下へは行かない（荷が軽くなってロボが少し上がる分）
    f3 = k["Rcr"] @ np.array([0.0, 1.0, 0.0]); th = math.atan2(f3[2], float(np.hypot(f3[0], f3[1])))
    R = rotz(up["psi"]) @ rotx(f * th)
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = pos
    return M.tolist()


def _cargo_world(box, plan, k):
    """2次元の箱 → 世界の 4×4（向きは体の向き、前後の面で回る）"""
    fw = box._fw; o = box._o
    pos = np.array([o[0] + fw[0] * box.x[0], o[1] + fw[1] * box.x[0], box.x[1]])
    psi = math.atan2(-fw[0], fw[1])
    R = rotz(psi) @ rotx(box.th)
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = pos
    return M.tolist()
