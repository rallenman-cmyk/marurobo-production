import sys, time, os
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/ch03")
import numpy as np, earbud_v2 as E, sdf
t0 = time.time()
jobs = [("body", E.body_sdf(), (-6.2, 7.9, E.Z_CAP - 0.1), (1.9, 14.4, 18.5), 0.07),
        ("tip", E.eartip_sdf(), (-7.4, 8.8, 12.9), (-3.5, 11.9, 17.3), 0.049),
        ("cap", E.cap_sdf(), (-1.6, 9.5, E.Z0 - 0.1), (1.6, 12.8, E.Z_CAP + 0.2), 0.042)]
for nm, F, lo, hi, h in jobs:
    t1 = time.time(); V, Q = E.mesh_cached(nm, F, lo, hi, h)
    print(nm, len(V), len(Q), "bbox", V.min(0).round(2), V.max(0).round(2), "%.1fs" % (time.time() - t1), flush=True)
print("total %.1fs" % (time.time() - t0))
