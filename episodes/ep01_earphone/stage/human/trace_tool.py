# 髪と顔の輪郭を、合わせたカメラで参考画像に重ねる（Blenderを使わず速く確かめる）
# 使い方: python3 trace_tool.py fit.json out.png [M1,W1,G1]
import sys, os, json, math, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import hgen, chunkhair, ref_people
IMG_W, IMG_H = 1672, 941


def cam_basis(yaw, pit, roll):
    d = np.array([math.cos(pit) * math.cos(yaw), math.cos(pit) * math.sin(yaw), math.sin(pit)])
    r0 = np.array([math.sin(yaw), -math.cos(yaw), 0.0]); u0 = np.cross(r0, d)
    r = r0 * math.cos(roll) + u0 * math.sin(roll); u = -r0 * math.sin(roll) + u0 * math.cos(roll)
    return d, r, u


def project(Pw, cam):
    C, yaw, pit, roll, f = cam
    d, r, u = cam_basis(yaw, pit, roll)
    v = Pw - C; zc = v @ d; fx = f / 36.0 * IMG_W
    return np.stack([IMG_W / 2 + fx * (v @ r) / zc, IMG_H / 2 - fx * (v @ u) / zc], -1), zc

REF = os.path.join(HERE, "..", "..", "refimg", "ref_2827_2.jpeg")
MASK = os.path.join(HERE, "..", "..", "trace", "hairmask_{}.png")


def silhouette(V, Q, cam, size=(IMG_W, IMG_H)):
    uv, zc = project(V, cam)
    im = Image.new("L", size, 0); d = ImageDraw.Draw(im)
    for q in Q:
        if (zc[q] < 0.05).any(): continue
        d.polygon([tuple(uv[i]) for i in q], fill=255)
    return im


def person_meshes(k, h=0.0034):
    cfg = ref_people.PEOPLE[k]
    P = dict(hgen.HEAD); P.update(cfg["head"]); B = dict(hgen.BODY); B.update(cfg.get("body", {}))
    HP = dict(hgen.HAIR); HP.update(cfg.get("hair", {}))
    J = hgen.skeleton(B); hc = np.asarray(J["head_center"]); s = P["hs"]
    m, Vh, Qh = hgen.head_mesh(P, hc, h)
    _, Va, Qa = chunkhair.chunk_hair_mesh(m, P, HP, hc, s, h)
    return dict(head=(Vh, Qh), hair=(Va, Qa)), hc


def place(V, hc, head):
    R = np.array(head["R"]); H = np.array(head["H"])
    return H + (V - hc) @ R.T


if __name__ == "__main__":
    fit = json.load(open(sys.argv[1])); out = sys.argv[2]
    who = sys.argv[3].split(",") if len(sys.argv) > 3 else ["M1", "W1", "G1"]
    cf = fit["camera"]; cam = (np.array(cf["C"]), cf["yaw"], cf["pitch"], cf["roll"], cf["lens"])
    ref = Image.open(REF).convert("RGB")
    vis = Image.blend(ref, Image.new("RGB", ref.size, (255, 255, 255)), 0.35)
    d = ImageDraw.Draw(vis)
    for k in who:
        t0 = time.time()
        M, hc = person_meshes(k)
        sil = {nm: silhouette(place(V, hc, fit["heads"][k]), Q, cam) for nm, (V, Q) in M.items()}
        # 髪は顔の前に出ている所だけ（顔に隠れる部分は除く）…ここでは単純に重ねる
        mine = np.asarray(sil["hair"]) > 128
        refm = np.asarray(Image.open(MASK.format(k)).convert("L")) > 128
        inter = (mine & refm).sum(); uni = (mine | refm).sum()
        print(k, "hair IoU", round(inter / max(uni, 1), 3), "mine", int(mine.sum()), "ref", int(refm.sum()), round(time.time() - t0, 1), "s", flush=True)
        for img, col in ((sil["hair"], (230, 20, 30)), (sil["head"], (240, 170, 0)), (Image.fromarray((refm * 255).astype(np.uint8)), (0, 170, 60))):
            e = img.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 60 else 0).filter(ImageFilter.MaxFilter(3))
            vis.paste(Image.new("RGB", ref.size, col), (0, 0), e)
    vis.save(out)
