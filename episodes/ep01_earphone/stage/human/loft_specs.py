# 3人の頭の設計値（6面図から）。spec_*.json（自動で取り出した横顔の線など）＋手で測った値
import os, json, math
import numpy as np
SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sheets")

MANUAL = {
    "M1": dict(
        width_tab=[(0.080, 0.080), (0.050, 0.080), (0.038, 0.079), (0.011, 0.0756), (-0.0087, 0.079), (-0.020, 0.080), (-0.032, 0.0767),
                   (-0.0436, 0.0733), (-0.055, 0.0709), (-0.067, 0.064), (-0.078, 0.057), (-0.084, 0.051), (-0.090, 0.044), (-0.096, 0.035),
                   (-0.102, 0.021), (-0.106, 0.004)],
        y_back=0.035,
        jaw_line=[(-0.30, -0.1066), (-0.083, -0.1066), (-0.040, -0.099), (0.010, -0.067), (0.060, -0.030), (0.30, 0.0)],
        cranium=dict(c=(0.0, 0.008, 0.035), r=(0.083, 0.112, 0.095)),
        ear_yaw=28.0, ear_tilt=-10.0,
        neck=dict(c=(0.0, 0.017, 0.0), r=(0.0535, 0.057), top=-0.055, bottom=-0.26),
        # 各ビューの横位置（切り抜きの中のピクセル）：首の中心などで合わせる
        u=dict(front=180.0, left=151.4, right=None, back=None, left45=None), vT=None,
        # 顔の部品（人物の左側の値。右は左右反転）：正面図から
        feat=dict(iris=(0.0384, 0.011), iris_r=0.0145,
                  eye_box=dict(x_in=0.0233, z_in=0.0169, x_out=0.0721, z_out=0.0215, hu=0.0107, hl=0.0230),
                  brow=dict(inner=(0.019, 0.0395), outer=(0.0745, 0.0564), t_in=0.0105, t_out=0.0080, arch=0.002),
                  mouth=dict(hw=0.032, z_mid=-0.060, sag=0.007)),
    ),
    "W1": dict(
        width_tab=[(0.090, 0.078), (0.060, 0.080), (0.032, 0.0817), (0.011, 0.0817), (-0.0162, 0.0807), (-0.0283, 0.0787), (-0.0564, 0.0666),
                   (-0.0806, 0.046), (-0.0927, 0.0278), (-0.0964, 0.004)],
        y_back=0.030,
        jaw_line=[(-0.30, -0.0985), (-0.0853, -0.0985), (-0.0203, -0.0864), (0.008, -0.0586), (0.060, -0.030), (0.30, 0.0)],
        cranium=dict(c=(0.0, 0.008, 0.035), r=(0.080, 0.110, 0.092)),
        ear_yaw=24.0, ear_tilt=-10.0,
        neck=dict(c=(0.0, 0.017, 0.0), r=(0.036, 0.037), top=-0.050, bottom=-0.26),
        u=dict(front=165.0, left=153.5, right=None, back=None, left45=None), vT=None,
        feat=dict(iris=(0.0412, 0.011), iris_r=0.0150,
                  eye_box=dict(x_in=0.0278, z_in=0.0116, x_out=0.0811, z_out=0.0237, hu=0.0145, hl=0.0242),
                  brow=dict(inner=(0.0224, 0.0528), outer=(0.0835, 0.0607), t_in=0.0085, t_out=0.0060, arch=0.003),
                  mouth=dict(hw=0.0285, z_mid=-0.0598, sag=0.0048)),
    ),
    "G1": dict(
        width_tab=[(0.090, 0.080), (0.040, 0.080), (0.011, 0.0784), (-0.0087, 0.0784), (-0.029, 0.0767), (-0.0597, 0.0682), (-0.0804, 0.0519),
                   (-0.0906, 0.0435), (-0.0998, 0.0256), (-0.1057, 0.004)],
        y_back=0.035,
        jaw_line=[(-0.30, -0.1057), (-0.086, -0.1057), (-0.0349, -0.1006), (0.0078, -0.075), (0.060, -0.035), (0.30, 0.0)],
        cranium=dict(c=(0.0, 0.008, 0.035), r=(0.083, 0.110, 0.095)),
        ear_yaw=24.0, ear_tilt=-10.0,
        neck=dict(c=(0.0, 0.017, 0.0), r=(0.052, 0.052), top=-0.055, bottom=-0.26),
        u=dict(front=182.5, left=142.4, right=None, back=None, left45=None), vT=None,
        feat=dict(iris=(0.0332, 0.011), iris_r=0.0108,
                  eye_box=dict(x_in=0.0196, z_in=0.0119, x_out=0.0656, z_out=0.016, hu=0.0082, hl=0.0143),
                  brow=dict(inner=(0.0143, 0.0395), outer=(0.0682, 0.0492), t_in=0.0112, t_out=0.0082, arch=0.002),
                  mouth=dict(hw=0.0281, z_mid=-0.0597, sag=0.0051),
                  glasses=dict(c=(0.0495, 0.0042), half=(0.0367, 0.0248), thick=0.0069, y_front=-0.115, temple_z=0.026)),
    ),
}


def get(k):
    sp = json.load(open(os.path.join(SH, f"spec_{k}.json")))
    M = MANUAL[k]
    L = dict(base=sp["base"], width_tab=M["width_tab"], y_back=M["y_back"], jaw_line=M["jaw_line"], cranium=M["cranium"],
             nose=sp["nose"], ear=dict(sp["ear"], yaw=M["ear_yaw"], tilt=M["ear_tilt"]), neck=M["neck"])
    P = dict(loft=L)
    reg = dict(S=sp["reg"]["S"], v0=sp["reg"]["v0"], u=dict(M["u"]), vT=M["vT"])
    lay = json.load(open(os.path.join(SH, "layout.json")))[k]["panels"]
    # 後ろ・右・斜めの位置合わせ：頭の上の方（髪）の幅の中心をそろえる（首や服の影響を受けない高さ）
    from PIL import Image
    S, v0 = reg["S"], reg["v0"]
    def ext(view, z):
        fg = np.asarray(Image.open(os.path.join(SH, f"{k}_{view}_fg.png")).convert("L")) > 128
        v = int(round(v0 - z * S)); xs = np.nonzero(fg[v])[0]
        return (xs.min(), xs.max()) if len(xs) else None
    acc = {"back": [], "right": [], "left45": []}
    for z in (0.03, 0.05, 0.07, 0.09, 0.11):
        f, sl = ext("front", z), ext("left", z)
        if f is None or sl is None: continue
        xc = ((f[0] + f[1]) / 2 - reg["u"]["front"]) / S; yc = ((sl[0] + sl[1]) / 2 - reg["u"]["left"]) / S
        for view in acc:
            e = ext(view, z)
            if e is None: continue
            uc = (e[0] + e[1]) / 2
            if view == "back": acc[view].append(uc + S * xc)
            elif view == "right": acc[view].append(uc + S * yc)
            else: a = math.radians(45.0); acc[view].append(uc - S * (xc * math.cos(a) + yc * math.sin(a)))
    for view, vals in acc.items():
        if reg["u"].get(view) is None and vals: reg["u"][view] = float(np.median(vals))
    if reg["vT"] is None:
        fg = np.asarray(Image.open(os.path.join(SH, f"{k}_top_fg.png")).convert("L")) > 128
        ys, xs = np.nonzero(fg[:520]); reg["u"]["top"] = (xs.min() + xs.max()) / 2
        # 真上：髪の前後の中心を、髪の前後の中心（横ビューで測る）に合わせる
        fgL = np.asarray(Image.open(os.path.join(SH, f"{k}_left_fg.png")).convert("L")) > 128
        rows = fgL[:int(reg["v0"] - 0.10 * reg["S"])]; cols = np.nonzero(rows.any(0))[0]
        y_front = (cols.min() - reg["u"]["left"]) / reg["S"]; y_back = (cols.max() - reg["u"]["left"]) / reg["S"]
        top_rows = np.nonzero(fg[:520].any(1))[0]
        # 真上の図は胴も写る：髪の部分だけ（上から見た頭の前後の幅は横ビューと同じ）→ 上の端を髪の後ろに合わせる
        reg["vT"] = top_rows.min() + reg["S"] * y_back
    return P, reg


def feat(k, head_m):
    """顔の部品の位置（頭の中心からの座標）。目の骨は顔の面の2cm奥"""
    import hgen
    F = MANUAL[k]["feat"]; L = None
    sp = json.load(open(os.path.join(SH, f"spec_{k}.json")))
    ix, iz = F["iris"]
    hit = hgen.surface_hit(head_m, np.array([[ix, -0.30, iz]]), np.array([[0, 1.0, 0]]), tmax=0.40)[0]
    eye_y = float(hit[1]) + 0.020
    E = sp["ear"]; ear_x = E["in_x"] + 0.006
    return dict(eye=[[ix, eye_y, iz], [-ix, eye_y, iz]], ear=[[ear_x, E["center"][1] - 0.004, E["center"][2] - 0.006], [-ear_x, E["center"][1] - 0.004, E["center"][2] - 0.006]],
                brow=[[F["brow"]["inner"][0] + 0.02, eye_y - 0.005, F["brow"]["inner"][1] + 0.004], [-(F["brow"]["inner"][0] + 0.02), eye_y - 0.005, F["brow"]["inner"][1] + 0.004]],
                mouth=[0.0, -0.09, F["mouth"]["z_mid"]], iris_r=F["iris_r"], eye_box=F["eye_box"], brow_line=F["brow"], mouth_line=F["mouth"],
                glasses=F.get("glasses"))
