# 第5章の図（ch05_diagram.py）のコマを、何本かに分けて並べて描く（本番 1080p 用。MARU_RES=1080 で起動する）
# 使い方: MARU_RES=1080 python3 ch05_frames_par.py OUT_DIR [本数]  → OUT_DIR/ch05/c_%04d.png（できているコマは飛ばす）
import sys, os
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ch05_diagram as c5
OUT = os.path.join(sys.argv[1], "ch05"); os.makedirs(OUT, exist_ok=True)
NP = int(sys.argv[2]) if len(sys.argv) > 2 else 4; FPS = 24
N = c5.N_OUT                                                   # 2026-11-09：時間の直し（c5.TE）のあとのコマの数
def one(i):
    fp = os.path.join(OUT, "c_%04d.png" % (i + 1))
    if os.path.exists(fp) and os.path.getsize(fp) > 0: return 0
    c5.frame(c5.TE.src(c5.T_A + i / FPS)).save(fp + ".tmp.png", compress_level=1); os.replace(fp + ".tmp.png", fp); return 1
if __name__ == "__main__":
    with Pool(NP) as p: done = sum(p.imap_unordered(one, range(N), chunksize=24))
    print("FRAMES", N, "drawn", done, flush=True)
