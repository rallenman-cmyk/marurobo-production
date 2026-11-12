# 作った頭（と髪）を6面図と同じ向き・縮尺で正投影し、シートに輪郭を重ねて確かめる
# 使い方: python3 sheet_check.py M1 out.png [hair]
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import sdf, loft_head, loft_specs
SH = os.path.join(HERE, "..", "..", "sheets")
VIEWS = ["front", "left45", "left", "back", "right", "top"]
ANG = {"front": 0.0, "left45": 45.0, "left": 90.0, "back": 180.0, "right": 270.0}


def project(V, view, reg):
    S, v0 = reg["S"], reg["v0"]; u0 = reg["u"][view]
    if view == "top":
        return np.stack([u0 + S * V[:, 0], reg["vT"] - S * V[:, 1]], 1)
    a = math.radians(ANG[view])
    return np.stack([u0 + S * (V[:, 0] * math.cos(a) + V[:, 1] * math.sin(a)), v0 - S * V[:, 2]], 1)


def silhouette(V, Q, view, reg, size):
    uv = project(V, view, reg); im = Image.new("L", size, 0); d = ImageDraw.Draw(im)
    for q in Q: d.polygon([tuple(uv[i]) for i in q], fill=255)
    return im


def outline(img):
    return img.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 60 else 0).filter(ImageFilter.MaxFilter(3))


if __name__ == "__main__":
    k = sys.argv[1]; out = sys.argv[2]
    P, reg = loft_specs.get(k)
    m = loft_head.loft_model(P, np.zeros(3))
    V, Q = sdf.mesh(m, np.array([-0.16, -0.20, -0.28]), np.array([0.16, 0.22, 0.18]), 0.003, relax_iters=1)
    meshes = [(V, Q, (240, 150, 0))]
    if len(sys.argv) > 3 and sys.argv[3] == "hair":
        import hair_sheet
        Vh, Qh = hair_sheet.hair_mesh(k, m, 0.004)
        meshes.append((Vh, Qh, (230, 20, 30)))
    tiles = []
    for view in VIEWS:
        im = Image.open(os.path.join(SH, f"{k}_{view}.png")).convert("RGB"); im = Image.blend(im, Image.new("RGB", im.size, (255, 255, 255)), 0.25)
        for (VV, QQ, col) in meshes:
            e = outline(silhouette(VV, QQ, view, reg, im.size)); im.paste(Image.new("RGB", im.size, col), (0, 0), e)
        tiles.append(im.crop((0, 60, im.width, 560)))
    W = sum(t.width for t in tiles); H = tiles[0].height
    sheet = Image.new("RGB", (W, H), "white"); x = 0
    for t in tiles: sheet.paste(t, (x, 0)); x += t.width
    sheet.save(out); print("saved", out, sheet.size)
