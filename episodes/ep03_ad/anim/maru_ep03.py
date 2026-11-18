# 3本目のまるロボ（v10 から。ファイル名は共通の maru_real.py とぶつからないように maru_ep03.py）：共通の部品で、本物のまるロボを決まりどおりに動かす。common.py と s07s08_gate.py が exec で読む
#   2026-11-17 ユーザー「歩き方全然違うって」「1本目の動画の時はできてた」→ references/maru_walk.md のとおり
#   ・体を置いて毎コマを当てる：skill/.../scripts/maru_real.py（4本目が作った共通の部品。PC は story.blend の本物、クラウドは代わりの体）
#   ・前と同じ書き方（mr.at / walk / hop / tilt / glow …）を予定に並べる：skill/.../scripts/maru_cmds.py（3本目が作った共通の部品）
#   ここでは 3本目だけのもの（探偵の帽子・目の光の材質）を足す。向きは前と同じ（前が −Y のときの角度 → face_offset=180）
import os, sys
import bpy
from mathutils import Vector

_SK = os.path.join(_ANIM_HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts")
_RG = os.path.join(_ANIM_HERE, "..", "..", "ep01_earphone", "stage", "maru")
for _d in (_RG, _SK, _ANIM_HERE):                     # PC の一式では anim に marumotion・marurig・maru_real・maru_cmds を入れる
    if os.path.isdir(_d) and _d not in sys.path: sys.path.insert(0, _d)
import maru_cmds as MC


def _hat(torso):
    """探偵の帽子（3本目の帽子と同じ形・柄）。本物の頭のてっぺん（胴の中心から 0.49）に合わせる。本物の前は +Y"""
    plaid = checker_mat("hat_plaid", "#B88A55", "#8A6239", 9); band = mat("hat_band", "#5B3B22", rough=0.6)
    he = empty((0, 0, 0)); he.parent = torso; he.location = (0, -0.03, 0.40); he.rotation_euler = (R(8), 0, 0)
    he.scale = (1.02, 0.93, 1.0)
    parts = [sphere(plaid, (0, 0, 0.02), 0.35, scale=(1, 1.02, 0.7), parent=he), cyl(band, (0, 0, -0.03), 0.352, 0.07, parent=he)]
    for sy, ang in ((1, 18), (-1, -18)):
        parts.append(cyl(plaid, (0, sy * 0.40, -0.03), 0.2, 0.03, rot=(R(ang), 0, 0), scale=(1.05, 0.62, 1), parent=he))
    for sx in (-1, 1): parts.append(sphere(plaid, (sx * 0.3, 0, -0.02), 0.1, scale=(0.35, 1, 1.1), parent=he))
    parts.append(sphere(band, (0, 0, 0.26), 0.05, scale=(1.6, 0.8, 0.8), parent=he))
    return he, parts


class Maru(MC.Maru):
    def __init__(self, loc, face, s=1.0, hat=True, eye_glow=1.2, look_up=0.0, **_):
        super().__init__(loc, face, s=s, face_offset=180.0, look_up=look_up, name="maru%d" % len(MC.ALL))
        H = MC.MR.hier(self.root)
        self.antenna_objs = [o for o in H if o.type == "MESH" and any("• antenna" in a.name for a in _parents(o))]
        lens_o = next((o for o in H if o.type == "MESH" and o.data.materials and ("lens" in o.name.lower() and "ring" not in o.name.lower() and "housing" not in o.name.lower())), None)
        self.lens = None
        if lens_o:
            m = lens_o.data.materials[0].copy(); m.name = "maru_lens"; lens_o.data.materials[0] = m; self.lens = m
        self.hat_e, self.hat_parts = _hat(self.torso) if hat else (None, [])
        self.z0 = 0.0
        self.post = []                                       # 予定を当てたあとにする仕事（体の場所に合わせて物を動かす など）


def _parents(o):
    out = []
    while o.parent: o = o.parent; out.append(o)
    return out


def bake_all(t_end):
    MC.bake_all(t_end, T0=CLOCK_T0(), fps=FPS, steps=STEPS, events=EVENTS)
    for m in MC.ALL:
        for fn in getattr(m, "post", []): fn(m)


def head_top(m, t, up=0.49):
    """時刻 t の、まるロボの頭のてっぺん（世界の座標）。予定を当てたあとに使う"""
    sc_ = bpy.context.scene; sc_.frame_set(f(t)); bpy.context.view_layer.update()
    return m.torso.matrix_world @ Vector((0, 0, up))


def CLOCK_T0():
    return CLOCK["T0"] if "CLOCK" in globals() else T0
