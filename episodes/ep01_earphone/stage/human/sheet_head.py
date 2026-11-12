# 6面図（正面・横）から頭の形の設計値（輪郭の曲線と顔の部品の位置）を取り出す
# 座標：頭の中心 hc からの位置（メートル）。x＝人物の左、y＝後ろ、z＝上
# 使い方: python3 sheet_head.py M1  → sheets/spec_M1.json と確認画像
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SH = os.path.join(HERE, "..", "..", "sheets")

# 手で測った目印（各ビューの切り抜きの中のピクセル）
ANCH = {
    "M1": dict(
        S=860.0, v_eye=323.0, z_eye=0.011,              # 目の高さを z=0.011 に合わせる
        front=dict(u0=180.0),                             # 顔の中心線
        left=dict(u_neck=166.0, v_neck=420.0, y_neck=0.017),   # 首の中心を骨格の首の線に合わせる
        nose=dict(root=(47.5, 340.0), tip=(42.5, 365.0), sub=(57.5, 370.0), width=25.0),
        chin=(80.0, 424.0), neck_front=(117.0, 418.0), neck_back=(215.0, 420.0),
        jaw_angle_v=402.0,                                # 正面で、あごの線が首とつながる高さ
        ear=dict(center=(184.0, 318.0), size=(56.0, 68.0), out_u=75.0, in_u=111.0),   # 横（中心・幅・高さ）、正面（外側・付け根）
        eye=dict(iris=(147.0, 323.0), outer=(118.0, 309.0), inner=(160.0, 314.0), low_v=336.0, iris_d=25.0,
                 side_lash=((67.5, 307.5), (101.0, 305.5))),
        brow=dict(outer=(115.0, 285.0), inner=(162.0, 300.0), thick=9.0),
        mouth=dict(left=(152.5, 378.0), right=(207.5, 378.0), low=(180.0, 384.0)),
        face_rows=dict(top_v=300.0, sideburn_v=342.0, below_ear_v=372.0),
    ),
    "W1": dict(
        S=826.0, v_eye=317.5, z_eye=0.011, front=dict(u0=165.0), left=dict(u_neck=167.5, v_neck=420.0, y_neck=0.017),
        nose=dict(root=(62.0, 333.0), tip=(52.7, 349.3), sub=(68.3, 355.0), width=14.0),
        chin=(83.0, 408.0), neck_front=(136.7, 398.0), neck_back=(198.0, 400.0), jaw_angle_v=405.0,
        ear=dict(center=(186.0, 318.0), size=(53.0, 77.0), out_u=260.0, in_u=233.0),
        eye=dict(iris=(199.0, 317.5), outer=(232.0, 307.0), inner=(188.0, 317.0), low_v=332.0, iris_d=25.0, side_lash=((75.0, 300.0), (110.0, 298.0))),
        brow=dict(outer=(235.0, 276.5), inner=(185.0, 283.0), thick=7.0), mouth=dict(left=(143.0, 372.0), right=(190.0, 372.0), low=(165.0, 376.0)),
        face_rows=dict(top_v=300.0, sideburn_v=330.0, below_ear_v=370.0)),
    "G1": dict(
        S=978.0, v_eye=310.8, z_eye=0.011, front=dict(u0=182.5), left=dict(u_neck=159.0, v_neck=425.0, y_neck=0.017),
        nose=dict(root=(36.0, 330.0), tip=(25.0, 356.7), sub=(41.7, 365.0), width=30.0),
        chin=(58.3, 425.0), neck_front=(108.3, 420.0), neck_back=(210.0, 425.0), jaw_angle_v=405.0,
        ear=dict(center=(175.0, 329.0), size=(50.0, 72.0), out_u=70.0, in_u=103.3),
        eye=dict(iris=(215.0, 310.8), outer=(246.7, 306.0), inner=(201.7, 310.0), low_v=322.0, iris_d=21.0, side_lash=((51.7, 306.7), (71.7, 308.3))),
        brow=dict(outer=(248.0, 273.5), inner=(195.0, 283.0), thick=11.0), mouth=dict(left=(155.0, 375.0), right=(210.0, 375.0), low=(181.7, 380.0)),
        face_rows=dict(top_v=300.0, sideburn_v=330.0, below_ear_v=370.0)),
}


def load(k, view, kind):
    return np.asarray(Image.open(os.path.join(SH, f"{k}_{view}_{kind}.png")).convert("L")) > 128


def spec(k):
    A = ANCH[k]; S = A["S"]; v0 = A["v_eye"] + A["z_eye"] * S
    z_of = lambda v: (v0 - v) / S
    uF = A["front"]["u0"]
    uL = A["left"]["u_neck"] - A["left"]["y_neck"] * S
    y_of = lambda u: (u - uL) / S                       # 横（左）ビューの u → y
    x_of = lambda u: (u - uF) / S                       # 正面の u → x
    fgL, skL = load(k, "left", "fg"), load(k, "left", "skin")
    skF = load(k, "front", "skin")
    # ---- 横顔の前の線（鼻を除いた素の線も）
    rows = np.arange(int(A["face_rows"]["top_v"]) - 40, int(A["chin"][1]) + 1)
    prof = []
    u_ear = A["ear"]["center"][0] - 22
    for v in rows:
        xs = np.nonzero(skL[v, :int(u_ear)])[0]          # 顔の肌のいちばん前（髪が前にかかる人もいるので肌で見る）
        if len(xs) < 3: continue
        u = xs.min()
        if not skL[v, u:u + 3].all(): continue
        prof.append((z_of(v), y_of(u)))
    prof = np.array(prof); prof = prof[np.argsort(prof[:, 0])]
    # 飛び値（髪の明るい所など）を除く：前後9点の中央値から6mm以上ずれた点
    med = np.array([np.median(prof[max(0, i - 4):i + 5, 1]) for i in range(len(prof))])
    prof = prof[np.abs(prof[:, 1] - med) < 0.006]
    z_brow = (v0 - A["brow"]["inner"][1]) / S
    prof = prof[prof[:, 0] < z_brow + 0.02]
    nr, nt, ns = A["nose"]["root"], A["nose"]["tip"], A["nose"]["sub"]
    z_nr, z_ns = z_of(nr[1]), z_of(ns[1])
    base = prof.copy()
    m = (base[:, 0] < z_nr) & (base[:, 0] > z_ns)      # 鼻のふくらみを、付け根と鼻の下を結ぶ線に置きかえる
    y_nr, y_ns = y_of(nr[0]), y_of(ns[0])
    base[m, 1] = y_nr + (base[m, 0] - z_nr) / (z_ns - z_nr) * (y_ns - y_nr)
    # ---- 正面の顔の幅（中心から外へ、肌が途切れるまで）。耳と接する高さは上下からつなぐ
    wrows = []
    for v in range(int(A["face_rows"]["top_v"]), int(A["jaw_angle_v"]) + 26):
        row = skF[v]; c = int(round(uF))
        if not row[c]: continue
        l = c
        while l > 0 and row[l - 1]: l -= 1
        r = c
        while r < len(row) - 1 and row[r + 1]: r += 1
        wrows.append((v, z_of(v), (r - l) / 2.0 / S))
    wrows = np.array(wrows)
    sb, be = A["face_rows"]["sideburn_v"], A["face_rows"]["below_ear_v"]
    ok = (wrows[:, 0] < sb) | (wrows[:, 0] > be)
    w_z = wrows[ok][:, 1]; w_w = wrows[ok][:, 2]
    # あごの下（首とつながる所から下）は首の太さ
    E = A["ear"]; ear_c = (0.0, y_of(E["center"][0]), z_of(E["center"][1]))
    out = dict(
        S=S, prof=prof.tolist(), base=base.tolist(), width=np.stack([w_z, w_w], 1).tolist(),
        nose=dict(root=(y_nr, z_nr), tip=(y_of(nt[0]), z_of(nt[1])), sub=(y_ns, z_ns), width=A["nose"]["width"] / S),
        chin=(y_of(A["chin"][0]), z_of(A["chin"][1])), neck_front=(y_of(A["neck_front"][0]), z_of(A["neck_front"][1])),
        neck_back=(y_of(A["neck_back"][0]), z_of(A["neck_back"][1])), neck_half_w=None,
        jaw_angle_z=z_of(A["jaw_angle_v"]),
        ear=dict(center=ear_c, size=(E["size"][0] / S, E["size"][1] / S), out_x=abs(x_of(E["out_u"])), in_x=abs(x_of(E["in_u"]))),
        eye=dict(iris=(x_of(A["eye"]["iris"][0]), z_of(A["eye"]["iris"][1])), outer=(x_of(A["eye"]["outer"][0]), z_of(A["eye"]["outer"][1])),
                 inner=(x_of(A["eye"]["inner"][0]), z_of(A["eye"]["inner"][1])), low_z=z_of(A["eye"]["low_v"]), iris_d=A["eye"]["iris_d"] / S,
                 side_lash=[(y_of(a), z_of(b)) for a, b in A["eye"]["side_lash"]]),
        brow=dict(outer=(x_of(A["brow"]["outer"][0]), z_of(A["brow"]["outer"][1])), inner=(x_of(A["brow"]["inner"][0]), z_of(A["brow"]["inner"][1])),
                  thick=A["brow"]["thick"] / S),
        mouth=dict(left=(x_of(A["mouth"]["left"][0]), z_of(A["mouth"]["left"][1])), right=(x_of(A["mouth"]["right"][0]), z_of(A["mouth"]["right"][1])),
                   low=(x_of(A["mouth"]["low"][0]), z_of(A["mouth"]["low"][1]))),
        reg=dict(S=S, v0=v0, uF=uF, uL=uL),
    )
    # 首の太さ（正面）
    nf = []
    for v in range(int(A["neck_front"][1]) + 2, int(A["neck_front"][1]) + 14):
        xs = np.nonzero(skF[v])[0]
        if len(xs): nf.append((xs.max() - xs.min()) / 2.0 / S)
    out["neck_half_w"] = float(np.median(nf)) if nf else 0.055
    return out


if __name__ == "__main__":
    k = sys.argv[1]; sp = spec(k)
    json.dump(sp, open(os.path.join(SH, f"spec_{k}.json"), "w"), indent=1)
    print(k, "profile pts", len(sp["prof"]), "width pts", len(sp["width"]), "nose tip", np.round(sp["nose"]["tip"], 4), "chin", np.round(sp["chin"], 4),
          "ear", np.round(sp["ear"]["center"], 4), "neck half w", round(sp["neck_half_w"], 4))
