# 共通の部品：運ばれる物の物理（Blender なしで動く）
#   ・吊った物の振れ（振り子）：支点が加速すると、物は遅れて振れ、減衰しながら戻る
#       θ'' = −(g/L)·sinθ − (a/L)·cosθ − 2ζω·θ'      （a＝支点の水平の加速度、L＝支点→重心）
#   ・器の中の液体の揺れ（第1モードのスロッシング）：器が加速すると液面が傾き、揺れ戻りながら静まる
#       φ'' + 2ζω·φ' + ω²·φ = −ω²·(a/g)            （φ＝液面の傾き。静かに加速し続けると tanφ＝a/g に落ち着く）
#       円柱の器（半径 R、深さ h）の固有角振動数：ω² = (g·ξ/R)·tanh(ξ·h/R)、ξ＝1.8412
#   どちらも数値積分（1コマを10に分けた半陰的オイラー法）。入力は1コマごとの加速度の列
import math
import numpy as np

G = 9.81
XI = 1.8412


def accel(pos, fps):
    """位置の列（N×k）→ 加速度の列（中心差分）"""
    p = np.asarray(pos, float); dt = 1.0 / fps
    a = np.zeros_like(p)
    if len(p) >= 3: a[1:-1] = (p[2:] - 2 * p[1:-1] + p[:-2]) / (dt * dt)
    return a


def pendulum(acc, fps, L, zeta=0.08, theta0=0.0, sub=10):
    """吊った物の振れ角（rad）。acc：支点の水平の加速度の列（1方向）。L は一定でも列でもよい"""
    acc = np.asarray(acc, float); n = len(acc); Ls = np.broadcast_to(np.asarray(L, float), (n,))
    th, om = theta0, 0.0; out = np.zeros(n); h = 1.0 / fps / sub
    for i in range(n):
        Li = max(Ls[i], 0.05); w = math.sqrt(G / Li)
        for _ in range(sub):
            om += (-(G / Li) * math.sin(th) - (acc[i] / Li) * math.cos(th) - 2 * zeta * w * om) * h
            th += om * h
        out[i] = th
    return out


def slosh_omega(R, h): return math.sqrt(G * XI / R * math.tanh(XI * h / R))


def slosh(acc, fps, R=0.2, h=0.3, zeta=0.15, sub=10):
    """液面の傾き（rad）。acc：器の水平の加速度の列（1方向）。絵の具は水より粘るので減衰は大きめ"""
    acc = np.asarray(acc, float); w = slosh_omega(R, h); ph, om = 0.0, 0.0; out = np.zeros(len(acc)); dt = 1.0 / fps / sub
    for i in range(len(acc)):
        for _ in range(sub):
            om += (-2 * zeta * w * om - w * w * ph - w * w * acc[i] / G) * dt
            ph += om * dt
        out[i] = ph
    return out


if __name__ == "__main__":
    fps = 24; t = np.arange(0, 4, 1 / fps)
    x = np.clip((t - 0.5) / 1.0, 0, 1); x = x * x * x * (10 - 15 * x + 6 * x * x) * 1.2       # 1.2m を1秒で動く（躍度最小）
    a = accel(x[:, None], fps)[:, 0]
    th = pendulum(a, fps, 0.6); ph = slosh(a, fps)
    print("max swing %.1f deg, max slosh %.1f deg, omega %.2f rad/s" % (math.degrees(abs(th).max()), math.degrees(abs(ph).max()), slosh_omega(0.2, 0.3)))
