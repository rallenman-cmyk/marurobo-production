# まるロボが画面に映っているかを、時刻ごとに数える（2026-11-20、3本目 v11「まるロボが映ってないのに足音」6 件）
#   場面を組んだあと（予定を毎コマに当てたあと）に呼ぶ。カメラの切り替え（マーカー）も frame_set で反映される
#   返り値：[[時刻, 0/1], ...]（step 秒ごと）
import bpy
from bpy_extras.object_utils import world_to_camera_view


def visible_times(t0, t1, frame_of, bodies, step=0.125, margin=0.0):
    """frame_of：時刻 → その場面のコマ（場面の f()。場面の t0 と時計の 0 がずれる場面があるので、必ず場面の f を渡す）
    体の中心・頭のてっぺん・左右のどれか 1 点が枠の中なら映っている（頭だけ見える絵もある）"""
    from mathutils import Vector
    sc = bpy.context.scene; out = []; t = t0
    while t < t1:
        sc.frame_set(frame_of(t)); bpy.context.view_layer.update()
        cam = sc.camera; v = 0
        if cam is not None:
            for b in bodies:
                for o in ((0, 0, 0), (0, 0, 0.45), (0.3, 0, 0.2), (-0.3, 0, 0.2)):
                    p = world_to_camera_view(sc, cam, b.matrix_world @ Vector(o))
                    if p.z > 0 and margin < p.x < 1 - margin and margin < p.y < 1 - margin: v = 1; break
                if v: break
        out.append([round(t, 3), v]); t += step
    return out
