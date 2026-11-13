# 前の版（kit18）と今（kit24）のまるロボの動きを、コマごとに比べる。違うコマの範囲を出す（描き直す範囲を決めるため）
import sys, os, importlib, json
import numpy as np
SP = os.path.dirname(os.path.abspath(__file__))
def load(kit, mod, fn):
    d = os.path.join(SP, kit, 'marurobo_tools', 'qr'); sys.path.insert(0, d)
    for m in list(sys.modules):
        if m in ('marumotion', 'plan_util', 'c1_plan', 'c1_timeline', 'c2_plan', 'c3_plan', 'c4_plan', 'c5_plan', 'robot_events'): del sys.modules[m]
    M = importlib.import_module(mod); r = getattr(M, fn)(); sys.path.remove(d)
    fr = r[1] if isinstance(r, tuple) else r
    return fr
def vec(f):
    v = list(f['root'][:3]) + [f['psi'], f['pitch'], f['roll'], f['twist']]
    for ft in f['feet']: v += list(ft['ankle']) + [ft['psi'], ft['pitch']]
    v += list(f['ant']) + [f['iris']['scale'], f['iris']['dx'], f['iris']['dz'], f['light']]
    return np.array(v, float)
mod, fn = sys.argv[1], sys.argv[2]
a = load('kit18', mod, fn); b = load('kit24', mod, fn)
n = min(len(a), len(b)); d = np.array([np.abs(vec(a[i]) - vec(b[i])).max() for i in range(n)])
bad = np.where(d > 1e-4)[0]
spans = []
for i in bad:
    if spans and i - spans[-1][1] <= 24: spans[-1][1] = i
    else: spans.append([i, i])
print(mod, fn, 'frames', len(a), len(b), 'diff spans (frame no. 1-based, sec):', [(s + 1, e + 1, round(s / 24, 2), round(e / 24, 2)) for s, e in spans])
