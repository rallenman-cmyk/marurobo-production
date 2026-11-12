# 参考画像と描画の色を、同じ場所（材質ごとの代表点）で比べる。sRGB の値と、線形での比（描画→参考にするには何倍か）
# 使い方: python3 color_match.py render.png
import sys, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
PTS = {
    "M1 skin": [(1340, 470), (1300, 440), (1380, 520)], "M1 hair": [(1300, 90), (1450, 150), (1200, 200)],
    "M1 jacket": [(1560, 820), (1600, 700)], "M1 turtleneck": [(1450, 640), (1500, 600)],
    "W1 skin": [(600, 590), (620, 560)], "W1 hair": [(560, 400), (640, 380), (720, 450)], "W1 blazer": [(700, 740), (660, 800)],
    "G1 skin": [(235, 615), (250, 590)], "G1 hair": [(220, 460), (280, 470)], "G1 suit": [(170, 790), (300, 760)],
}


def lin(c): c = np.asarray(c) / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


if __name__ == "__main__":
    ref = np.asarray(Image.open(os.path.join(HERE, "..", "..", "refimg", "ref_2827_2.jpeg")).convert("RGB")).astype(float)
    mine = np.asarray(Image.open(sys.argv[1]).convert("RGB").resize((ref.shape[1], ref.shape[0]), Image.LANCZOS)).astype(float)
    for k, pts in PTS.items():
        a = np.mean([ref[y - 4:y + 5, x - 4:x + 5].reshape(-1, 3).mean(0) for x, y in pts], 0)
        b = np.mean([mine[y - 4:y + 5, x - 4:x + 5].reshape(-1, 3).mean(0) for x, y in pts], 0)
        ratio = lin(a) / np.maximum(lin(b), 1e-4)
        print(f"{k:14s} ref #{int(a[0]):02X}{int(a[1]):02X}{int(a[2]):02X}  mine #{int(b[0]):02X}{int(b[1]):02X}{int(b[2]):02X}  linear ratio {np.round(ratio, 2)}")
