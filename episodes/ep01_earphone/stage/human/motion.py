# 人の動きの部品（物理・生体の数値つき）
# すべて「時刻 t（秒）→ 値」の関数。毎コマ計算してキーフレームにする
import math
import numpy as np


def clip01(x): return max(0.0, min(1.0, x))


def mj(t, t0, T):
    """躍度最小（minimum jerk）：人の到達運動の速さは釣り鐘形。10τ³−15τ⁴+6τ⁵"""
    u = clip01((t - t0) / T); return u * u * u * (10 - 15 * u + 6 * u * u)


def env(t, t0, up, hold, down):
    """立ち上がり→保持→戻り（それぞれ躍度最小）"""
    return mj(t, t0, up) - mj(t, t0 + up + hold, down)


def breath(t, period=4.0, inhale=0.4, phase=0.0):
    """呼吸：安静時 毎分12〜20回（ここでは15回＝4秒周期）。吸う4割・吐く6割"""
    p = ((t + phase) / period) % 1.0
    if p < inhale: return mj(p, 0, inhale)
    return 1.0 - mj(p, inhale, 1.0 - inhale)


def blink(t, t0, close=0.09, hold=0.04, open_=0.17):
    """まばたき：閉じる90ms（速い）→40ms→開く170ms（遅い）。0＝開、1＝閉"""
    if t < t0 or t > t0 + close + hold + open_: return 0.0
    if t < t0 + close: u = (t - t0) / close; return u * u
    if t < t0 + close + hold: return 1.0
    u = (t - t0 - close - hold) / open_; return 1.0 - u * (2 - u)


def saccade_time(amp_deg):
    """サッカード（目の跳躍運動）の所要時間：約 2.2ms×振幅(度)＋21ms（主系列）"""
    return (2.2 * amp_deg + 21.0) / 1000.0


class Spring:
    """ばね＋ダンパー（2次系）。固有振動数 f（Hz）、減衰比 z。遅れて追いかける動き（重なり合う動き）"""
    def __init__(self, f=3.0, z=0.6, x0=0.0):
        self.w = 2 * math.pi * f; self.z = z; self.x = x0; self.v = 0.0

    def step(self, target, dt, n=8):
        h = dt / n
        for _ in range(n):
            a = self.w * self.w * (target - self.x) - 2 * self.z * self.w * self.v
            self.v += a * h; self.x += self.v * h
        return self.x


def train_sway(T, fps, seed=3, rms=0.22):
    """電車の横揺れ（床の加速度 m/s²）：0.6〜1.8Hz の揺れを重ねた不規則な揺れ"""
    rng = np.random.default_rng(seed); t = np.arange(int(T * fps) + 2) / fps
    a = np.zeros_like(t)
    for f in (0.62, 0.95, 1.31, 1.77):
        a += rng.uniform(0.6, 1.0) * np.sin(2 * math.pi * f * t + rng.uniform(0, 2 * math.pi))
    a *= rms / max(a.std(), 1e-9)
    return t, a


def pendulum_response(acc, fps, f0=1.1, z=0.55, L=0.45, g=9.81):
    """座った上半身＝筋肉で支えた倒立振子。床が揺れると少し遅れて傾く（角度・度）"""
    w = 2 * math.pi * f0; th = 0.0; v = 0.0; out = []
    dt = 1.0 / fps
    for a in acc:
        for _ in range(8):
            h = dt / 8
            acc_th = -w * w * th - 2 * z * w * v - a / L
            v += acc_th * h; th += v * h
        out.append(math.degrees(th))
    return np.array(out)
