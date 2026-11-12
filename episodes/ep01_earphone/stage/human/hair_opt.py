# 髪の形を参考画像の輪郭に合わせる：髪のかたまりの位置と大きさを少しずつ変え、頭全体（髪＋顔）の輪郭の重なり（IoU）が最大になるものを探す
# 使い方: python3 hair_opt.py fit.json M1 iters out_prefix
import sys, os, json, math, time, copy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import hgen, chunkhair, ref_people
from trace_tool import project, silhouette, place, IMG_W, IMG_H

TR = os.path.join(HERE, "..", "..", "trace")
SEED = {"M1": (1340, 470), "W1": (600, 590), "G1": (235, 615)}
CHIN = {"M1": 612, "W1": 662, "G1": 662}
EXCL = {"M1": [(1560, 0, 1672, 120), (1555, 330, 1672, 640), (1100, 0, 1672, 18)], "W1": [(300, 300, 418, 700)]}
BOX = {"M1": (1000, 0, 1672, 640), "W1": (360, 300, 840, 700), "G1": (80, 400, 420, 700)}


# 主人公は題字の暗い背景が髪とつながってしまうため、参考画像から手で拾った輪郭（髪＋顔、あごの高さで切る）を使う
POLY = {"M1": [(1097, 207), (1140, 120), (1197, 80), (1290, 57), (1377, 45), (1403, 43), (1457, 63), (1523, 100), (1563, 127), (1603, 167),
               (1633, 213), (1650, 247), (1637, 280), (1610, 313), (1597, 347), (1583, 400), (1570, 453), (1557, 473), (1555, 612), (1303, 612),
               (1303, 603), (1283, 597), (1250, 560), (1223, 527), (1200, 513), (1185, 497), (1180, 467), (1170, 430), (1143, 417), (1100, 387),
               (1060, 313), (1065, 260)]}


def ref_union(k):
    if k in POLY:
        im = Image.new("L", (IMG_W, IMG_H), 0); ImageDraw.Draw(im).polygon(POLY[k], fill=255)
        a = np.asarray(im) > 128; a = a.copy(); a[CHIN[k]:, :] = False; return a
    return ref_union_mask(k)


def ref_union_mask(k):
    hair = np.asarray(Image.open(os.path.join(TR, f"hairmask_{k}.png")).convert("L")) > 128
    skin = np.asarray(Image.open(os.path.join(TR, f"skinmask_{k}.png")).convert("L")) > 128
    m = Image.fromarray(((hair | skin) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    ImageDraw.floodfill(m, SEED[k], 128)                     # 目のあたりから続いている部分だけ（窓枠などを除く）
    a = np.asarray(m) == 128
    inv = Image.fromarray(((~a) * 255).astype(np.uint8)).copy(); inv.load(); inv = inv.point(lambda v: v); ImageDraw.floodfill(inv, (0, 0), 0)   # 穴（イヤホンなど）を埋める
    a = a | (np.asarray(inv) == 255)
    a[CHIN[k]:, :] = False
    for (x0, y0, x1, y1) in EXCL.get(k, []): a[y0:y1, x0:x1] = False      # 窓枠など（肌に似た色）を除く
    return a


def mine_union(sil_head, sil_hair, k):
    a = (np.asarray(sil_head) > 128) | (np.asarray(sil_hair) > 128)
    a = a.copy(); a[CHIN[k]:, :] = False
    return a


def iou(a, b, k):
    x0, y0, x1, y1 = BOX[k]; a = a[y0:y1, x0:x1]; b = b[y0:y1, x0:x1]
    return (a & b).sum() / max((a | b).sum(), 1)


def apply(style, prm):
    """prm[i] = (dy, dz, ksx, ksy, ksz) for each blob then lock"""
    st = copy.deepcopy(style); j = 0
    for grp in ("blobs", "locks"):
        new = []
        for b in st.get(grp, []):
            dy, dz, kx, ky, kz = prm[j]; j += 1
            b = list(b)
            if b[0] == "ell":
                c = np.array(b[1]) + np.array([0, dy, dz]); r = np.array(b[2]) * np.exp([kx, ky, kz])
                b[1] = tuple(c); b[2] = tuple(r)
            else:
                b[1] = tuple(np.array(b[1]) + np.array([0, dy, dz])); b[2] = tuple(np.array(b[2]) + np.array([0, dy, dz]))
                b[3] = b[3] * math.exp(kx); b[4] = b[4] * math.exp(kx)
            new.append(tuple(b))
        st[grp] = new
    return st


if __name__ == "__main__":
    fit = json.load(open(sys.argv[1])); k = sys.argv[2]; iters = int(sys.argv[3]); outp = sys.argv[4]
    cf = fit["camera"]; cam = (np.array(cf["C"]), cf["yaw"], cf["pitch"], cf["roll"], cf["lens"])
    cfg = ref_people.PEOPLE[k]
    P = dict(hgen.HEAD); P.update(cfg["head"]); B = dict(hgen.BODY); B.update(cfg.get("body", {})); HP = dict(hgen.HAIR); HP.update(cfg["hair"])
    J = hgen.skeleton(B); hc = np.asarray(J["head_center"]); s = P["hs"]
    m, Vh, Qh = hgen.head_mesh(P, hc, 0.0040)
    sil_head = silhouette(place(Vh, hc, fit["heads"][k]), Qh, cam)
    R = ref_union(k)
    base = chunkhair.STYLES[HP["style"]]
    sf = os.environ.get("START_FROM", "")
    if sf and os.path.exists(sf):        # 前回の結果から続ける
        ov = json.load(open(sf)); base = dict(base, blobs=[tuple(b) for b in ov["blobs"]], locks=[tuple(b) for b in ov.get("locks", [])]); print("start from", sf, flush=True)
    nprm = len(base["blobs"]) + len(base.get("locks", []))
    prm = np.zeros((nprm, 5))

    def evaluate(prm):
        st = apply(base, prm)
        hp = dict(HP, over=dict(blobs=st["blobs"], locks=st.get("locks", [])))
        _, Va, Qa = chunkhair.chunk_hair_mesh(m, P, hp, hc, s, 0.006)
        sh = silhouette(place(Va, hc, fit["heads"][k]), Qa, cam)
        return iou(mine_union(sil_head, sh, k), R, k), sh

    best, sh = evaluate(prm); print("start IoU", round(best, 4), flush=True)
    rng = np.random.default_rng(1); step = np.array([0.008, 0.008, 0.10, 0.10, 0.10]); fails = 0
    for it in range(iters):
        cand = prm.copy()
        for _ in range(rng.integers(1, 3)):
            i = rng.integers(nprm); j = rng.integers(5)
            cand[i, j] += rng.normal(0, step[j])
        cand[:, 2:] = np.clip(cand[:, 2:], -0.5, 0.5); cand[:, :2] = np.clip(cand[:, :2], -0.05, 0.05)
        v, shc = evaluate(cand)
        if v > best:
            best, prm, sh = v, cand, shc; fails = 0
            print("it", it, "IoU", round(best, 4), flush=True)
        else:
            fails += 1
            if fails > 12: step *= 0.7; fails = 0
    st = apply(base, prm)
    json.dump(dict(blobs=st["blobs"], locks=st.get("locks", [])), open(outp + ".json", "w"), indent=1)
    # 確認用の重ね合わせ
    ref = Image.open(os.path.join(HERE, "..", "..", "refimg", "ref_2827_2.jpeg")).convert("RGB")
    vis = Image.blend(ref, Image.new("RGB", ref.size, (255, 255, 255)), 0.35)
    mine = Image.fromarray((mine_union(sil_head, sh, k) * 255).astype(np.uint8)); refm = Image.fromarray((R * 255).astype(np.uint8))
    for img, col in ((mine, (230, 20, 30)), (refm, (0, 170, 60)), (sh, (255, 140, 0))):
        e = img.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 60 else 0).filter(ImageFilter.MaxFilter(3))
        vis.paste(Image.new("RGB", ref.size, col), (0, 0), e)
    vis.crop(BOX[k]).save(outp + ".png")
    print("BEST IoU", round(best, 4))
