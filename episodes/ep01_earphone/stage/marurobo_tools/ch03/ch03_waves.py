# 止まった電波の波面（C2）を、描いた絵の上で見せる：スマホのアンテナを中心にした球面の波面（12.3cmおき）を、
# 光らない「ゆがみ」として重ねる。視線がアンテナから距離 b を通るとき、半径 R の球面にほぼ接するところで光がいちばん曲がる
# → 画面ではアンテナのまわりに、半径 R_k（奥行きに合わせた大きさ）の同心円のゆがみの輪ができる。振幅は 1/R（球面波）
import json, math, numpy as np

def project(cam_mat, lens, sensor, res, P):
    """世界の点 → 画面の画素（x→右, y→下）と奥行き"""
    M = np.array(cam_mat); R = M[:3, :3]; t = M[:3, 3]
    d = R.T @ (np.array(P) - t)                                   # カメラの座標（−Z が前）
    z = -d[2]; W, H = res; f = lens / sensor * W
    return np.array([W / 2 + f * d[0] / z, H / 2 - f * d[1] / z]), z, f

def wave_field(log, still, res_out=(1280, 720), sigma=0.016, n=6, r0=0.045, amp_px=5.0):
    """画面の各点のずらし（dx, dy）。amp_px＝いちばん内側の輪の、出力の画素でのずれの大きさ"""
    st = log["stills"][still]; res = log["res"]
    c, z, f = project(st["cam"], st["lens"], st["sensor"], res, log["antenna"])
    sx = res_out[0] / res[0]; c = c * sx; f = f * sx               # 出力の大きさに合わせる
    H, W = res_out[1], res_out[0]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = xx - c[0]; dy = yy - c[1]; rp = np.sqrt(dx * dx + dy * dy) + 1e-6
    b = rp * z / f                                                 # 画素の距離 → アンテナの奥行きでの距離（m）
    lam = log["lambda"]; D = np.zeros_like(b)
    for k in range(n):
        R = r0 + k * lam; x = (b - R) / sigma
        D += (r0 + lam * 0.5) / (R + lam * 0.5) * x * np.exp(-0.5 * x * x)
    D *= amp_px / 0.607                                            # x·e^(−x²/2) の最大は 0.607
    return D * dx / rp, D * dy / rp, c

def apply(img, fx, fy, a):
    """img：H×W×3（0〜255）。a：0〜1（見える割合）。ずらした所から色を取る（両線形）"""
    if a <= 1e-3: return img
    H, W = img.shape[:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sx = np.clip(xx + a * fx, 0, W - 1.001); sy = np.clip(yy + a * fy, 0, H - 1.001)
    x0 = sx.astype(np.int32); y0 = sy.astype(np.int32); wx = (sx - x0)[..., None]; wy = (sy - y0)[..., None]
    im = img.astype(np.float32)
    out = (im[y0, x0] * (1 - wx) * (1 - wy) + im[y0, x0 + 1] * wx * (1 - wy) + im[y0 + 1, x0] * (1 - wx) * wy + im[y0 + 1, x0 + 1] * wx * wy)
    return np.clip(out, 0, 255).astype(np.uint8)
