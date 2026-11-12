# 6面図から起こす頭：横顔の線（前の輪郭）と正面の顔幅で「輪切りを重ねる」（ロフト）。頭蓋・鼻・耳・首は別の部品
# 座標：hc（頭の中心）からの位置。x＝人物の左、y＝後ろ（前は−）、z＝上
import math
import numpy as np
from sdf import Model, ellipsoid, sphere, cone, rot, smin, smax


def _interp(z, table):
    t = np.asarray(table, float); o = np.argsort(t[:, 0]); t = t[o]
    return np.interp(z, t[:, 0], t[:, 1])


def loft_model(P, hc):
    L = P["loft"]; hc = np.asarray(hc, float)
    H = {"head": 1.0}
    base = np.asarray(L["base"], float)
    o = np.argsort(base[:, 0]); base = base[o]
    ker = np.ones(9) / 9.0                                  # 段がつかないよう、横顔の線をならす
    yy = np.convolve(np.pad(base[:, 1], 4, mode="edge"), ker, mode="valid"); base = np.stack([base[:, 0], yy], 1)
    # 前の輪郭：顔が見えている範囲＋上（額）と下（あご）へ少しのばす
    zt = base[:, 0].max(); zb = base[:, 0].min()
    yb_top = base[np.argmax(base[:, 0]), 1]
    prof = np.concatenate([base, [[zt + 0.03, yb_top + 0.004], [zt + 0.06, yb_top + 0.016]]])
    width = np.asarray(L["width_tab"], float)
    y_back = L.get("y_back", 0.035)
    zj = np.asarray(L["jaw_line"], float)          # (y, z)：あごの下の線（前→後ろ）
    p_front, p_back = L.get("p_front", 2.6), L.get("p_back", 2.1)
    z_lo, z_hi = zb - 0.002, zt + 0.06

    def face(p):
        q = p - hc; z = q[:, 2]
        yf = _interp(z, prof); w = np.maximum(_interp(z, width), 1e-3)
        yc = (yf + y_back) / 2; d = (y_back - yf) / 2
        X = np.abs(q[:, 0]) / w; Y = (q[:, 1] - yc) / d
        pp = np.where(Y < 0, p_front, p_back)
        r = (X ** pp + np.abs(Y) ** pp) ** (1 / pp)
        f = (r - 1) * np.minimum(w, d)
        zjaw = np.interp(q[:, 1], zj[:, 0], zj[:, 1])
        f = smax(f, zjaw - z, 0.006)                # あごの下より下は顔ではない
        f = smax(f, z - z_hi, 0.01)
        return f
    m = Model()
    cr = L["cranium"]
    m.add(ellipsoid(hc + np.array(cr["c"]), np.array(cr["r"])), "cranium", bones=H)
    m.add(face, "face", k=0.022, bones=H)
    # 鼻：付け根→鼻先の円すい＋鼻の下の小さなふくらみ（正面の幅）
    nz = L["nose"]; root = np.array([0, nz["root"][0], nz["root"][1]]); tip = np.array([0, nz["tip"][0], nz["tip"][1]])
    sub = np.array([0, nz["sub"][0], nz["sub"][1]])
    m.add(cone(hc + root + np.array([0, 0.006, 0]), hc + tip + np.array([0, 0.0045, 0.002]), 0.0045, 0.0050), "nose", k=0.008, bones=H)
    m.add(ellipsoid(hc + (tip + sub) / 2 + np.array([0, 0.008, 0.001]), np.array([nz["width"] / 2, 0.0085, 0.0055])), "nose", k=0.006, bones=H)
    # 耳
    E = L["ear"]; ec = np.array(E["center"]); ew, eh = E["size"]
    x_mid = (E["in_x"] + E["out_x"]) / 2
    for sx in (1, -1):
        R = rot(0, 0, sx * E.get("yaw", 28.0)) @ rot(E.get("tilt", -10.0), 0, 0)
        c = hc + np.array([sx * x_mid, ec[1], ec[2]])
        er = np.array([0.0105, ew / 2, eh / 2])
        m.add(ellipsoid(c, er, R), "ear", k=0.006, bones=H)
        m.sub(ellipsoid(c + R @ np.array([sx * 0.008, -0.002, -0.004]), er * np.array([0.65, 0.62, 0.66]), R), k=0.003)
    # 首（楕円の柱）
    N = L["neck"]; nc = np.array(N["c"]); nr = np.array(N["r"])
    def neck(p):
        q = p - hc - nc
        rr = np.sqrt((q[:, 0] / nr[0]) ** 2 + (q[:, 1] / nr[1]) ** 2)
        f = (rr - 1) * min(nr)
        return smax(f, smax(q[:, 2] - N["top"], N["bottom"] - q[:, 2], 0.0), 0.004)
    if not L.get("no_neck"): m.add(neck, "neck", k=0.016, bones={"neck": 1.0})
    return m
