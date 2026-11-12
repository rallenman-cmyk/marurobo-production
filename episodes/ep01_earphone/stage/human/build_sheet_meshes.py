# 6面図から作った頭と髪の網目を保存する（Blender の外で。画像の読み込みに PIL を使うため）
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import sdf, loft_head, loft_specs, hair_sheet
k = sys.argv[1]; t0 = time.time()
P, reg = loft_specs.get(k)
m = loft_head.loft_model(P, np.zeros(3))
V, Q = sdf.mesh(m, np.array([-0.16, -0.20, -0.28]), np.array([0.16, 0.22, 0.18]), 0.0028, relax_iters=2)
Vh, Qh = hair_sheet.hair_mesh(k, m, 0.0035)
np.savez(os.path.join(HERE, "..", "..", "sheets", f"mesh_{k}.npz"), V=V, Q=Q, Vh=Vh, Qh=Qh)
import json
L = dict(P["loft"]); L["feat"] = loft_specs.feat(k, m)
json.dump(L, open(os.path.join(HERE, "..", "..", "sheets", f"loftP_{k}.json"), "w"), default=lambda o: o.tolist() if hasattr(o, "tolist") else o)
json.dump({kk: float(v) for kk, v in reg["u"].items() if v is not None}, open(os.path.join(HERE, "..", "..", "sheets", f"reg_{k}.json"), "w"))
print("saved", k, len(Q), len(Qh), round(time.time() - t0, 1), "s")
