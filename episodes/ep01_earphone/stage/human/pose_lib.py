# 姿勢の部品：スマホを持つ・太ももに手を置く・耳のイヤホンに触れる・指の曲げ
import math
import numpy as np
from hrig import norm

FINGER_NAMES = ("index", "middle", "ring", "pinky")
# 手のひらの中心を、スマホの中心の面からどれだけ後ろに置くか（画面の向きの逆へ）。
# ピクトグラムの丸い手（厚さの半分 0.029m）は、スマホ（厚さの半分 0.0049m：0.0085m×1.15倍）の裏に触れる位置まで下げる（すき間 1.5mm）。
# 指のある手（昔の人の形）は 0.0172
PALM_N = 0.0049 + 0.029 + 0.0015


def phone_frame(J, hf_eye_mid, center=(0.035, -0.300, 0.930), tilt_up=0.30):
    """スマホの位置と向き（骨格空間）。画面は目の方を向く"""
    C = np.asarray(center, float)
    n = norm(np.asarray(hf_eye_mid) - C)
    up = np.array([0, -1.0, tilt_up]); a_long = norm(up - (up @ n) * n)
    x = np.cross(a_long, n)
    return C, np.stack([x, a_long, n], 1)


def left_grip(C, R, wrap=1.0):
    """左手でスマホを持つ：手のひらを背面に、指は右の縁へ回す、親指は左の縁"""
    x, a_long, n = R[:, 0], R[:, 1], R[:, 2]
    Y = norm(x * 0.93 + a_long * 0.36)
    Z = -n; Z = norm(Z - (Z @ Y) * Y); X = np.cross(Y, Z)
    palm = C - x * 0.016 - a_long * 0.030 - n * PALM_N
    wrist = palm - Y * 0.050
    return wrist, np.stack([X, Y, Z], 1)


def thigh_rest(J, sd="R", sx=-1, fwd=0.0):
    """手のひらを下にして太ももに置く"""
    kn, hp = J["knee." + sd], J["hip." + sd]
    p = hp + (kn - hp) * (0.55 + fwd)
    wrist = p + np.array([sx * 0.010, 0.050, 0.083])
    Y = norm((kn - hp) * np.array([1, 1, 0]) + np.array([-sx * 0.25, 0, -0.10]))
    Z = np.array([0, 0.10, 1.0]); Z = norm(Z - (Z @ Y) * Y); X = np.cross(Y, Z)
    return wrist, np.stack([X, Y, Z], 1)


def ear_touch(bud_pos, sx=-1):
    """人さし指・中指の腹でイヤホンに触れる：手首は耳の前下、指先は上・後ろへ"""
    tip_dir = norm(np.array([sx * -0.18, 0.30, 0.94]))
    wrist = np.asarray(bud_pos) - tip_dir * 0.150 + np.array([sx * 0.030, -0.030, 0.0])
    Y = norm(np.asarray(bud_pos) - wrist)
    Z = np.array([sx * 1.0, -0.35, 0.0]); Z = norm(Z - (Z @ Y) * Y); X = np.cross(Y, Z)
    return wrist, np.stack([X, Y, Z], 1)


def ear_touch_pict(bud_pos, sx=-1, pad=(0.100, 0.026)):
    """ピクトグラムの手（指の分かれていない手）でイヤホンに触れる：手の先の腹（手首から 0.100m・手のひらの側 0.026m）をイヤホンに当てる。
    手は耳の前から近づけ、指の向きは上・後ろ・少し内側、手の甲は前と外へ向ける（イヤホンを前から押すときの自然な形）"""
    Y = norm(np.array([sx * -0.10, 0.45, 0.88]))                       # 手首→指先（人物の座標：+Y＝後ろ、+Z＝上、右手は sx=−1）
    Z0 = np.array([sx * 0.45, -0.85, 0.15]); Z = norm(Z0 - (Z0 @ Y) * Y)   # 手の甲の向き：前（−Y）と外
    X = np.cross(Y, Z)
    wrist = np.asarray(bud_pos) - Y * pad[0] + Z * pad[1]
    return wrist, np.stack([X, Y, Z], 1)


def curl(rig, sd, mcp, pip, dip, fingers=FINGER_NAMES, spread=0.0, thumb=None):
    """指の曲げ（度）。曲げ＝局所X軸まわりのマイナス回転"""
    for i, f in enumerate(fingers):
        sp = spread * (i - 1.5)
        rig.rot(f"{f}_01.{sd}", x=-mcp, z=sp * (1 if sd == "R" else -1))
        rig.rot(f"{f}_02.{sd}", x=-pip); rig.rot(f"{f}_03.{sd}", x=-dip)
    if thumb is not None:
        a, b, c = thumb
        rig.rot(f"thumb_01.{sd}", x=-a); rig.rot(f"thumb_02.{sd}", x=-b); rig.rot(f"thumb_03.{sd}", x=-c)
