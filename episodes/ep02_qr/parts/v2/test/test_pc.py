import os, sys, numpy as np   # 使い方: python3 test_pc.py 試しの動画のフォルダ op,c1,c2  （make_fakepc.py で作る）
os.environ['PC_RENDER'] = sys.argv[1]
sys.path.insert(0, '/home/user/qr_plan/parts/v2'); os.chdir('/home/user/qr_plan/parts/v2')
import final_build as FB, pc_render as PCR
pc = PCR.PC((320, 180)); FB.PCX = pc
for tag in sys.argv[2].split(','):
    ch = FB.build(tag); segs = FB.fig_segments(ch)
    n3d = ok = bad = 0; miss = {}; NF = int(round(ch.T_END * 24))
    for i in range(NF):
        t = i / 24
        if any(a <= t < b for a, b, *_ in segs): continue
        sh = next((x for x in ch.SHOTS if x[0] <= t < x[1]), ch.SHOTS[-1]); k = sh[2]
        if k in ('poster', 'title', 'end_card') or k in FB.SINGLE or k in FB.FAMILY: continue
        n3d += 1; pc.last = None
        im, reuse = pc.frame(tag, k, t, sh[0], sh[1], FB.INFO)
        if im is None:
            miss.setdefault(k, []).append(t); continue
        a = np.asarray(im)[5:25, 5:25].reshape(-1, 3).mean(0); fd = int(round(a[0] / 16)) + 16 * int(round(a[1] / 16)) + 256 * int(round(a[2] / 6))
        if fd == pc.last[1]: ok += 1
        else:
            bad += 1
            if bad < 5: print('  BAD', tag, k, round(t, 2), pc.last, fd)
    print(tag, '3D frames', n3d, 'ok', ok, 'bad', bad, 'missing', {k: (len(v), round(min(v), 2), round(max(v), 2)) for k, v in miss.items()}, flush=True)
