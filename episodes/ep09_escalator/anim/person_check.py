# 9本目 v2（29 章で、点検のおじさんがまるロボの 0.47m 後ろに立ち、足が体に重なって見えた）：おじさんとまるロボの近さを場面ごとに数える
#   blender -b --factory-startup --python person_check.py -- <クリップ> <出力フォルダ>
#   その場面の間を 1/4 秒ごとに、まるロボの体の真ん中とおじさんの足もとの横の距離を測り、いちばん近い所を出す（OJ_MIN クリップ 距離 時刻）。
#   画面の上でまるロボの丸に重なれば OJ_SCREEN を出す（9本目 v2 の点検で追加）
#   0.75m 未満なら OJ_NEAR を出す（40 章の受け止めのように、わざとさわる所は表で確かめる）
import os, sys, math
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenes.py")
src = open(P, encoding="utf-8").read().replace("        render_clip(CLIPNAME,", "        CHECK(t0, t1)\n        0 and render_clip(CLIPNAME,")


def CHECK(t0, t1):
    import bpy
    G_ = _G; sc = bpy.context.scene; TR = G_["TRACK"]
    if "ojisan" not in TR or "maru_c" not in TR: print("OJ_MIN %s なし" % G_["CLIPNAME"]); return
    mc, oj = TR["maru_c"][0], TR["ojisan"][0]
    from bpy_extras.object_utils import world_to_camera_view as w2c
    mt = TR.get("maru_top", (None,))[0]; cam_ = sc.camera
    best = (9.0, t0); t = t0; scr = []
    while t <= t1:
        sc.frame_set(G_["f"](t)); m = mc.matrix_world.translation; r = oj.matrix_world.translation
        if abs(m.z - r.z) < 1.6:
            d = math.hypot(m.x - r.x, m.y - r.y)
            if d < best[0]: best = (d, t)
        # 画面の上で、おじさんの形がまるロボの丸にかかるか（13-04：0.79m 離れていても、カメラから見て真後ろに重なった）
        if mt is not None and cam_ is not None:
            a_ = w2c(sc, cam_, m); b_ = w2c(sc, cam_, mt.matrix_world.translation)
            if a_.z > 0 and -0.05 < a_.x < 1.05 and -0.05 < a_.y < 1.05:
                sm = (a_.x * 1280, a_.y * 720, max(8.0, math.hypot((a_.x - b_.x) * 1280, (a_.y - b_.y) * 720)))
                if G_["_screen_touch"](sc, cam_, sm, r): scr.append(round(t, 2))
        t += 0.25
    print("OJ_MIN %s %.2f %.2f" % (G_["CLIPNAME"], best[0], best[1]))
    if best[0] < 0.75: print("OJ_NEAR %s %.2f %.2f" % (G_["CLIPNAME"], best[0], best[1]))
    if scr: print("OJ_SCREEN %s 画面で重なる %d 回 %s〜%s" % (G_["CLIPNAME"], len(scr), scr[0], scr[-1]))


_G = {"__file__": P, "__name__": "__main__", "CHECK": CHECK}
exec(compile(src, P, "exec"), _G)
