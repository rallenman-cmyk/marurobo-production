# 表情シートの1コマを、6面図の同じ向きの絵の位置・大きさに合わせて重ねた画像を作る（頭に貼る絵の差し替え用）
# 使い方: python3 expr_register.py M1 lookdown     → sheets/M1_front__lookdown.png と sheets/M1_left45__lookdown.png
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); SH = os.path.join(HERE, "..", "..", "sheets")
EXPR = {"neutral": 0, "lookdown": 1, "blink": 2, "surprise": 3, "puzzled": 4}


def fgmask(rgb, bg):
    d = np.abs(rgb - bg).max(2) > 0.12
    m = Image.fromarray((d * 255).astype(np.uint8))
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))          # 細い目安線を消す
    return np.asarray(m) > 128


def skinmask(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]; lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return (g - b > 0.10) & (r - b > 0.25) & (lum > 0.38)


def register(k, expr):
    sp = json.load(open(os.path.join(SH, f"spec_{k}.json"))); S, v0 = sp["reg"]["S"], sp["reg"]["v0"]
    E = np.asarray(Image.open(os.path.join(SH, f"expr_{k}.png")).convert("RGB")).astype(float) / 255
    Hh, Ww, _ = E.shape; col = EXPR[expr]; pw = Ww / 5.0; ph = Hh / 2.0
    out = {}
    for row, view in ((0, "front"), (1, "left45")):
        P = E[int(row * ph):int((row + 1) * ph), int(col * pw):int((col + 1) * pw)]
        P = P[: int(ph * 0.90)]                                   # 下の文字を除く
        T = np.asarray(Image.open(os.path.join(SH, f"{k}_{view}.png")).convert("RGB")).astype(float) / 255
        bg = np.median(T[5:30].reshape(-1, 3), 0)
        mT = fgmask(T, bg); mP = fgmask(P, np.median(P[3:12].reshape(-1, 3), 0))
        v_cut = int(v0 + 0.095 * S)                              # あごの高さで切る（服は比べない）
        mT[v_cut:] = False
        # 粗く→細かく：大きさ s と位置 (tx, ty)。半分の解像度で探す
        def score(s, tx, ty, half=2):
            Ps = Image.fromarray((mP * 255).astype(np.uint8)).resize((max(1, int(P.shape[1] * s / half)), max(1, int(P.shape[0] * s / half))), Image.NEAREST)
            Ps = np.asarray(Ps) > 128
            Tm = mT[::half, ::half]; H2, W2 = Tm.shape
            canvas = np.zeros_like(Tm); x0, y0 = int(round(tx / half)), int(round(ty / half))
            xs0, ys0 = max(0, x0), max(0, y0); xs1, ys1 = min(W2, x0 + Ps.shape[1]), min(H2, y0 + Ps.shape[0])
            if xs1 <= xs0 or ys1 <= ys0: return 0.0
            canvas[ys0:ys1, xs0:xs1] = Ps[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
            canvas[v_cut // half:] = False
            inter = (canvas & Tm).sum(); uni = (canvas | Tm).sum()
            return inter / max(uni, 1)
        best = (0, None)
        for s in np.arange(1.0, 1.9, 0.04):
            for tx in range(-200, 120, 8):
                for ty in range(-60, 200, 8):
                    v = score(s, tx, ty, 4)
                    if v > best[0]: best = (v, (s, tx, ty))
        s0, tx0, ty0 = best[1]
        for it, (ds, dt) in enumerate(((0.01, 3), (0.003, 1))):
            b2 = best
            for s in np.arange(s0 - 4 * ds, s0 + 4.01 * ds, ds):
                for tx in range(int(tx0 - 4 * dt), int(tx0 + 4 * dt) + 1, dt):
                    for ty in range(int(ty0 - 4 * dt), int(ty0 + 4 * dt) + 1, dt):
                        v = score(s, tx, ty, 2 if it == 0 else 1)
                        if v > b2[0]: b2 = (v, (s, tx, ty))
            best = b2; s0, tx0, ty0 = best[1]
        print(k, expr, view, "IoU", round(best[0], 3), "scale", round(s0, 3), "offset", tx0, ty0, flush=True)
        # 重ねた画像：表情の絵を大きさ s で (tx, ty) に置く。外は元の絵のまま
        Pi = Image.fromarray((P * 255).astype(np.uint8)).resize((int(P.shape[1] * s0), int(P.shape[0] * s0)), Image.LANCZOS)
        Pa = np.asarray(Pi).astype(float) / 255
        Ti = T.copy(); H2, W2, _ = Ti.shape
        xs0, ys0 = max(0, tx0), max(0, ty0); xs1, ys1 = min(W2, tx0 + Pa.shape[1]), min(H2, ty0 + Pa.shape[0])
        patch = Pa[ys0 - ty0:ys1 - ty0, xs0 - tx0:xs1 - tx0]
        # 色合わせ：肌の色の中央値を元の絵にそろえる（ほかの向きの絵とのつなぎ目を目立たせない）
        sk_t = skinmask(T[ys0:ys1, xs0:xs1]); sk_p = skinmask(patch)
        if sk_t.sum() > 200 and sk_p.sum() > 200:
            gain = np.median(T[ys0:ys1, xs0:xs1][sk_t], 0) / np.maximum(np.median(patch[sk_p], 0), 1e-3)
            patch = np.clip(patch * gain, 0, 1)
        Ti[ys0:ys1, xs0:xs1] = patch
        Image.fromarray((Ti * 255).astype(np.uint8)).save(os.path.join(SH, f"{k}_{view}__{expr}.png"))
        out[view] = dict(iou=best[0], s=s0, tx=tx0, ty=ty0)
    return out


if __name__ == "__main__":
    k, expr = sys.argv[1], sys.argv[2]
    register(k, expr)
