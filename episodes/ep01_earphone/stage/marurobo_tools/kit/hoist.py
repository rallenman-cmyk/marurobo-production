# 共通の部品：天井クレーン（1方向のレールを走る台車＋上下に巻き上げるフック）の動き（Blender なしで動く）
#   予定（moves）：区間ごとに台車の位置 y とフックの高さ z を躍度最小で動かす
#   つかむ・はなす（hold）：その間、吊った物はフックといっしょに動き、台車の加速で振り子のように振れる（kit.carry.pendulum）
#   使い方:
#     h = Hoist(y0=1.2, z0=1.8, z_top=2.6)
#     h.move(t0, T, y=..., z=...); h.grab(t, "bucket A"); h.release(t)
#     S = h.sample(fps, t_start, t_end)   → S["y"], S["z"], S["hold"][i]（つかんでいる物の名前か None）, S["theta"]（振れ角）
import math
import numpy as np
from . import carry


def mj(u):
    u = min(max(u, 0.0), 1.0); return u * u * u * (10 - 15 * u + 6 * u * u)


class Hoist:
    def __init__(self, y0, z0, z_top, d_load=0.62, rigid=False):
        """y0・z0：はじめの台車の位置とフックの高さ、z_top：レール（台車の滑車）の高さ、d_load：フック→吊った物の基準点（底）。
        rigid＝True：綱でなく伸び縮みする硬い棒で吊る（振れない。速く動かせる）"""
        self.y0, self.z0, self.z_top, self.d_load, self.rigid = y0, z0, z_top, d_load, rigid
        self.moves = []; self.holds = []

    def move(self, t0, T, y=None, z=None):
        self.moves.append((t0, T, y, z)); return t0 + T

    def grab(self, t, name): self.holds.append((t, name)); return t

    def release(self, t): self.holds.append((t, None)); return t

    def state(self, t):
        y, z = self.y0, self.z0
        for t0, T, y1, z1 in sorted(self.moves, key=lambda m: m[0]):
            if t < t0: break
            u = mj((t - t0) / T) if T > 1e-9 else 1.0
            if y1 is not None: y = y + (y1 - y) * u
            if z1 is not None: z = z + (z1 - z) * u
        return y, z

    def holding(self, t):
        h = None
        for tt, nm in sorted(self.holds, key=lambda e: e[0]):
            if t >= tt: h = nm
        return h

    def sample(self, fps, t_start, t_end, zeta=0.10):
        n = int(round((t_end - t_start) * fps)) + 1; ts = t_start + np.arange(n) / fps
        Y = np.zeros(n); Z = np.zeros(n); H = []
        for i, t in enumerate(ts): Y[i], Z[i] = self.state(t); H.append(self.holding(t))
        L = (self.z_top - Z) + self.d_load * 0.6                      # 滑車 → 吊った物の重心（底から上へ 0.4 の所）
        a = carry.accel(Y[:, None], fps)[:, 0]
        th = carry.pendulum(a, fps, L, zeta=zeta)
        hold_on = np.array([1.0 if h else 0.0 for h in H])
        th = th * hold_on * (0.0 if self.rigid else 1.0)              # 何も吊っていないとき・硬い棒のときは振れない
        return dict(t=ts, y=Y, z=Z, hold=H, theta=th, L=L)

    def load_pose(self, S, i, x_rail):
        """吊った物の基準点（底の中心）の位置と、振れ角（y-z 面の回転）"""
        th = S["theta"][i]; Lb = (self.z_top - S["z"][i]) + self.d_load
        y = S["y"][i] + math.sin(th) * Lb; z = self.z_top - math.cos(th) * Lb
        return (x_rail, y, z), th
