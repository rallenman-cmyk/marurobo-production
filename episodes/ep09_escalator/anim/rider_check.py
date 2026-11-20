# 9本目 v1 のコメント（「まるロボに人が貫通してる」3 件）から：昼の場面で、乗る人（お客さん）とまるロボが重なる所を数える
#   blender -b --factory-startup --python rider_check.py -- <クリップ> <出力フォルダ>
#   映っている間（その場面の頭〜次の場面の頭）を 1/8 秒ごとに見て、まるロボの体の真ん中と人の足もとの横の距離が
#   0.55m 未満で、高さも重なる所を「重なり」として出す（RIDER_HIT 時刻 人の番号 距離 画面に映っているか）
import os, sys, json
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenes.py")
src = open(P, encoding="utf-8").read().replace("        render_clip(CLIPNAME,", "        CHECK(t0, t1)\n        0 and render_clip(CLIPNAME,")


def CHECK(t0, t1):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view as w2c
    sc = bpy.context.scene; cam = sc.camera; G_ = _G
    CL = json.load(open(os.path.join(os.path.dirname(P), "clips.json")))
    nm = G_["CLIPNAME"]; a = CL[nm][2]
    nxt = sorted(v[2] for v in CL.values() if v[2] > a + 0.01)
    b = nxt[0] if nxt else CL[nm][1]
    E = G_["ESC"][0]; mc = G_["TRACK"]["maru_c"][0]
    hits = []
    t = a
    while t < b:
        sc.frame_set(G_["f"](t))
        m = mc.matrix_world.translation
        mv = w2c(sc, cam, m); m_on = 0 <= mv.x <= 1 and 0 <= mv.y <= 1 and mv.z > 0
        for i, (wk, k, y) in enumerate(E.riders):
            if not getattr(wk, "_vis", True): continue
            r = wk.root.matrix_world.translation
            d = ((r.x - m.x) ** 2 + (r.y - m.y) ** 2) ** 0.5
            if d < 0.55 and r.z - 0.3 < m.z < r.z + 1.8:
                rv = w2c(sc, cam, r + type(r)((0, 0, 0.9)))
                r_on = 0 <= rv.x <= 1 and 0 <= rv.y <= 1 and rv.z > 0
                hits.append((round(t, 2), i, round(d, 2), bool(m_on or r_on)))
        t += 0.125
    for h in hits: print("RIDER_HIT %s %.2f 人%d 距離%.2f 映る%s" % (nm, h[0], h[1], h[2], h[3]))
    print("RIDER_DONE %s %d" % (nm, len(hits)))


_G = {"__file__": P, "__name__": "__main__", "CHECK": CHECK}
exec(compile(src, P, "exec"), _G)
