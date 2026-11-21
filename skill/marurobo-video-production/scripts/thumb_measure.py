# サムネを数で比べる道具（2026-11-21。ユーザー「文字数と黒帯のサイズをリサーチ元からしっかり調べて」「背景とのコントラスト」）
#   python3 thumb_measure.py band 画像…   → 黒い帯の高さ・字の高さ・余白・字の幅
#   python3 thumb_measure.py ink 画像…    → 帯の字の濃さ・線の太さ・白黄赤の色
#   python3 thumb_measure.py pic 画像…    → 帯の下の絵の色の強さ・明暗の差・鮮やかさ・線のはっきりさ・明るさ
#   参考（建物の深層 16 枚の値）は references/thumbnail_rules.md の「数で決めた値」
import sys
MODE = sys.argv.pop(1) if len(sys.argv) > 1 and sys.argv[1] in ("band", "ink", "pic") else "band"
if MODE == "band":
    import sys, numpy as np
    from PIL import Image
    def lumof(c): 
        c = np.asarray(c, float) / 255; c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]
    def measure(f):
        im = Image.open(f).convert("RGB")
        if im.size != (1280, 720): im = im.resize((1280, 720), Image.LANCZOS)
        a = np.asarray(im).astype(int); H, W, _ = a.shape; l = a.mean(2)
        dark = l < 45; rows = dark.mean(1)
        full = [y for y in range(int(H * 0.4)) if rows[y] > 0.97]
        band = max(full) + 1 if full else 0
        # 帯の中の字
        txt = l[:band] > 100; ys = np.where(txt.mean(1) > 0.002)[0]; xs = np.where(txt.any(0))[0]
        t = a[:band][txt]
        yel = ((t[:, 0] > 180) & (t[:, 1] > 150) & (t[:, 2] < 120)).mean(); red = ((t[:, 0] > 160) & (t[:, 1] < 110) & (t[:, 2] < 110)).mean()
        # 帯のすぐ下の絵（下 80px）の明るさと、帯との境の差
        below = a[band:band + 80]
        return dict(f=f.split("/")[-1][:14], 帯=band, 帯pct=round(band / H * 100, 1), 字高=int(ys[-1] - ys[0] + 1), 字高pct=round((ys[-1] - ys[0] + 1) / H * 100, 1),
                    上余白=int(ys[0]), 下余白=int(band - 1 - ys[-1]), 左=int(xs[0]), 右=int(W - 1 - xs[-1]), 字幅pct=round((xs[-1] - xs[0] + 1) / W * 100),
                    黄=round(float(yel), 2), 赤=round(float(red), 2), 下の絵の明るさ=int(below.mean()), 下の絵の暗い所pct=round(float((below.mean(2) < 60).mean() * 100), 1))
    for f in sys.argv[1:]: print(measure(f))
if MODE == "ink":
    import sys, numpy as np
    from PIL import Image
    for f in sys.argv[1:]:
        im = Image.open(f).convert("RGB").resize((1280, 720), Image.LANCZOS); a = np.asarray(im).astype(int)
        b = a[:120]; mx = b.max(2); txt = mx > 120
        ys = np.where(txt.mean(1) > 0.002)[0]; xs = np.where(txt.any(0))[0]
        box = txt[ys[0]:ys[-1]+1, xs[0]:xs[-1]+1]
        t = b[txt]
        W_ = (t.min(1) > 200); Y_ = (t[:,0]>200)&(t[:,1]>170)&(t[:,2]<120); R_ = (t[:,0]>170)&(t[:,1]<100)&(t[:,2]<100)
        med = lambda m: tuple(int(v) for v in np.median(t[m], 0)) if m.sum() else None
        # 線の太さ：字の行の真ん中で、横に続く字の画素の長さの中央値
        runs = []
        for y in range(ys[0] + (ys[-1]-ys[0])//3, ys[-1] - (ys[-1]-ys[0])//3, 3):
            r = txt[y]; n = 0
            for v in r:
                if v: n += 1
                elif n: runs.append(n); n = 0
        print(f.split("/")[-1][:14], "字の濃さ", round(box.mean(), 2), "線の太さ中央", int(np.median(runs)), "白", med(W_), "黄", med(Y_), "赤", med(R_), "割合 白/黄/赤", round(W_.mean(),2), round(Y_.mean(),2), round(R_.mean(),2))
if MODE == "pic":
    import sys, numpy as np
    from PIL import Image
    def m(f):
        a = np.asarray(Image.open(f).convert("RGB").resize((640, 360), Image.LANCZOS)).astype(float)[67:]   # 帯の下だけ
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        rg = R - G; yb = 0.5 * (R + G) - B
        colorful = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)   # Hasler の色の強さ
        L = 0.299 * R + 0.587 * G + 0.114 * B
        hsv = np.asarray(Image.fromarray(a.astype(np.uint8)).convert("HSV")).astype(float)
        sat = hsv[..., 1].mean() / 255
        # 線のはっきりさ：明るさの差（となりの画素）の平均
        edge = (np.abs(np.diff(L, axis=0)).mean() + np.abs(np.diff(L, axis=1)).mean()) / 2
        return colorful, L.std(), sat, edge, L.mean()
    rows = []
    for f in sys.argv[1:]:
        c, s, sa, e, l = m(f); rows.append((c, s, sa, e, l)); print("%-14s 色の強さ %5.1f  明暗の差 %5.1f  鮮やかさ %.2f  線のはっきりさ %4.1f  明るさ %5.1f" % (f.split('/')[-1][:14], c, s, sa, e, l))
    r = np.array(rows); print("平均", " ".join("%.2f" % v for v in r.mean(0)))
