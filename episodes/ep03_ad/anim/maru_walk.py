# 【使わない】v10 で maru_real.py（1本目と同じ marumotion＋marurig）に置きかえた。自分で似せて作った歩きの残り（2026-11-17 ユーザー「歩き方全然違う」）
# まるロボの歩き（3本目用）。common.py と s07s08_gate.py が exec で読む
#   2026-11-17 ユーザー「まるロボはペンギン歩きみたいなの前に作ってたよ」「歩き方全然違うって」
#   → 自分で似せて作るのをやめ、1本目・2本目と同じ道具 skill/.../scripts/marumotion.py の予定（Plan.walk_to）をそのまま使う。
#     毎コマの姿勢（体の位置・向き・前後と左右の傾き・ひねり、両足の足首の場所・向き・かかとからつま先への転がり）を、
#     3本目のまるロボ（storyboard/scenes.py の maru()）の部品に当てる。速さも前と同じ（1 m/s くらい。歩き出し・止まりの加減速つき）
#   3本目のまるロボの前は −Y、marumotion の前は +Y（体の中では 180° 回した向き）。大きさは root の scale（s）
import math, os, sys
import bpy
from mathutils import Vector, Quaternion, Euler

_MM_DIR = os.path.join(_ANIM_HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts")
if not os.path.exists(os.path.join(_MM_DIR, "marumotion.py")): _MM_DIR = _ANIM_HERE      # PC の一式では anim に入れる
sys.path.insert(0, _MM_DIR)
import marumotion as mm

HIP_Z = 0.25              # 3本目の脚の付け根（root から。胴の中）
HIP_X = 0.17              # 3本目の足の左右の位置（marumotion は 0.255）
FOOT_Z = 0.03             # 立っているときの靴の中心の高さ
PIVOT_Z = 0.40            # 胴を傾ける中心の高さ（marumotion の脚の付け根 0.42 にあたる）
BODY_Z = 0.69             # 胴の中心
SX = HIP_X / mm.HIP_X     # 左右の幅の比


def _fc(ob, path, idx):
    ad = ob.animation_data or ob.animation_data_create()
    if ad.action is None: ad.action = bpy.data.actions.new(ob.name + " action")
    return ad.action.fcurves.find(path, index=idx) or ad.action.fcurves.new(path, index=idx)


def kf(ob, path, idx, frame, value, interp="LINEAR"):
    """速い鍵打ち（毎コマ打つため）"""
    p = _fc(ob, path, idx).keyframe_points.insert(frame, value, options={'FAST'})
    p.interpolation = interp


def _clear(ob, path, idx, fa, fb):
    ad = ob.animation_data
    if not ad or not ad.action: return
    fc = ad.action.fcurves.find(path, index=idx)
    if not fc: return
    for kp in [k for k in fc.keyframe_points if fa <= k.co[0] <= fb][::-1]:
        fc.keyframe_points.remove(kp)


def rig_legs(m):
    """脚（すね）は付け根の空（hip）の子、靴は足首の空（ankle）の子にする。どちらも root の子。
    すねは付け根から足首へ向けて伸び縮みし、靴は地面に平らに置ける（marurig.py と同じ考え）"""
    bpy.context.view_layer.update()
    legs = [c for c in m.body.children if c.active_material and c.active_material.name.startswith("maru_leg")]
    shoes = [c for c in m.body.children if c.active_material and c.active_material.name.startswith("maru_foot")]
    m.hips, m.ankles = [], []
    for sx in (-1, 1):
        h = bpy.data.objects.new("maru_hip", None); a = bpy.data.objects.new("maru_ankle", None)
        for o in (h, a):
            o.empty_display_size = 0.05
            for c in m.root.users_collection: c.objects.link(o)
            o.parent = m.root; o.rotation_mode = "QUATERNION"
        h.location = (sx * HIP_X, 0.0, HIP_Z); a.location = (sx * HIP_X, 0.0, FOOT_Z)
        bpy.context.view_layer.update()
        for c, tgt in [(c, h) for c in legs if (c.location.x > 0) == (sx > 0)] + [(c, a) for c in shoes if (c.location.x > 0) == (sx > 0)]:
            mw = c.matrix_world.copy(); c.parent = tgt; c.matrix_parent_inverse.identity()
            bpy.context.view_layer.update(); c.matrix_basis = tgt.matrix_world.inverted() @ mw
        m.hips.append(h); m.ankles.append(a)
    m.leg_len = HIP_Z - FOOT_Z
    bpy.context.view_layer.update()


def hop_legs(m, t, h, d):
    """跳ぶ間は、脚と靴も体と一緒に上がる（足が地面から離れる）"""
    for o, z in [(o, HIP_Z) for o in m.hips] + [(o, FOOT_Z) for o in m.ankles]:
        key(o, ("location", 2), f(t), z); key(o, ("location", 2), f(t + d / 2), z + h); key(o, ("location", 2), f(t + d), z)


def face_of(dx, dy):
    """進む向き (dx, dy) を向く root の回転（度）。前は −Y"""
    return math.degrees(math.atan2(dx, -dy))


def plan_walk(D, rel_heading, speed):
    p = mm.Plan(pos=(0.0, 0.0), heading=rel_heading)
    p.walk_to((0.0, D), speed=speed)
    t_end = p.t
    p.idle(0.6, shifts=False, glance=False)
    return p, t_end


def walk_penguin(m, t0, t1, a, b, end_face=None, speed=None):
    """b に t1 で着いて止まる。歩き出しは、前と同じ速さ（1 m/s 前後）で間に合う時刻（t0 より前になることもある）。
    向きを変えるときは、その場で足踏みして向く（marumotion の turn_to）。返り値：歩き出した時刻"""
    sc = m.root.scale.x
    ax, ay = a[0], a[1]; dx, dy = b[0] - ax, b[1] - ay; Dw = math.hypot(dx, dy)
    if Dw < 1e-3: return t0
    D = Dw / sc                                                   # marumotion の大きさ（s=1）での距離
    yaw = face_of(dx, dy)
    cur = m._last["face"][1] if "face" in m.__dict__.get("_last", {}) else math.degrees(m.root.rotation_euler[2])
    rel = ((cur - yaw + 180) % 360) - 180                          # 歩く向きから見た、いまの向き（左回りが＋）
    T = t1 - t0
    if speed is None:                                             # t0〜t1 に収まる速さ（0.7〜1.3 m/s）。収まらなければ早く歩き出す
        speed = 1.0
        for v in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
            speed = v
            if plan_walk(D, rel, v)[1] <= T: break
    p, t_end = plan_walk(D, rel, speed)
    frames = mm.simulate(p)
    # 歩き出しは、前の動き（最後に置いた場所・向き）が終わってから。間に合わないときだけ、予定を少し速めて流す（w 倍）
    lastT = max([v[0] for v in m.__dict__.get("_last", {}).values()] + [-1e9])
    early = max(t0 - 1.5, lastT + 0.1)
    ts = t1 - t_end; w = 1.0
    if ts < early:
        w = t_end / max(0.3, t1 - early); ts = early
        if w > 1.35: print("【歩き】速めすぎ %.2f 倍：%.2f〜%.2f 秒、%.2f m。場面の時刻を見直す" % (w, ts, t1, Dw))
    u = (dx / Dw, dy / Dw); r = (u[1], -u[0])                      # 歩く向きと、その右（予定の +Y と +X）
    yaw_r = math.radians(yaw)
    fa = f(ts); fb = f(ts + (t_end + 0.5) / w)
    for o in [m.root]:
        for idx in (0, 1, 2): _clear(o, "location", idx, fa, fb)
        _clear(o, "rotation_euler", 2, fa, fb)
    for idx in (0, 1, 2): _clear(m.body, "rotation_euler", idx, fa, fb); _clear(m.body, "location", idx, fa, fb)
    for o in m.hips + m.ankles:
        for idx in range(4): _clear(o, "rotation_quaternion", idx, fa, fb)
        for idx in range(3): _clear(o, "location", idx, fa, fb); _clear(o, "scale", idx, fa, fb)
    last = None
    for fr in range(fa, fb + 1):
        tau = (CLOCK_T0() + fr / FPS - ts) * w                  # 予定の時刻
        k = frames[max(0, min(len(frames) - 1, int(round(tau * mm.FPS))))]
        last = k
        px, py, pz = k["root"]; psi = k["psi"]
        wx = ax + sc * (px * r[0] + py * u[0]); wy = ay + sc * (px * r[1] + py * u[1])
        kf(m.root, "location", 0, fr, wx); kf(m.root, "location", 1, fr, wy); kf(m.root, "location", 2, fr, sc * (pz - mm.ROOT_DZ))
        rz = yaw_r + psi                                          # 予定の向き psi（左回り＋）を足す
        kf(m.root, "rotation_euler", 2, fr, rz)
        # 胴：脚の付け根の高さを中心に、前後（pitch）・左右（roll）に傾き、ひねる（3本目は体の中で 180° 回った向きなので、符号はそのまま）
        P, R_, Tw = math.radians(k["pitch"]), math.radians(k["roll"]), math.radians(k["twist"])
        kf(m.body, "rotation_euler", 0, fr, P); kf(m.body, "rotation_euler", 1, fr, R_); kf(m.body, "rotation_euler", 2, fr, Tw)
        off = Euler((P, R_, Tw), "YXZ").to_matrix() @ Vector((0, 0, BODY_Z - PIVOT_Z))
        kf(m.body, "location", 0, fr, off.x); kf(m.body, "location", 1, fr, off.y); kf(m.body, "location", 2, fr, PIVOT_Z + off.z)
        # 足：足首の世界の場所 → 体（予定の向き psi）から見た右・前・高さ → 3本目の root から見た場所（右＝−X、前＝−Y、幅は SX 倍）
        c, s_ = math.cos(psi), math.sin(psi)
        for j in (0, 1):
            ft = k["feet"][j]
            qx, qy = ft["ankle"][0] - px, ft["ankle"][1] - py
            right = qx * c + qy * s_; fwd = -qx * s_ + qy * c
            lift = ft["ankle"][2] - mm.SOLE                     # 地面からの上げ幅
            side = 0 if j == 0 else 1                             # marumotion 足0＝左（x−）。3本目は左＝+X（前が −Y のため）
            o_ank = m.ankles[1 - side]
            lx, ly = -right * SX, -fwd
            kf(o_ank, "location", 0, fr, lx); kf(o_ank, "location", 1, fr, ly); kf(o_ank, "location", 2, fr, FOOT_Z + lift)
            yaw_f = ft["psi"] - psi                               # 足の向き（体から見た）
            q = Quaternion((0, 0, 1), yaw_f) @ Quaternion((1, 0, 0), math.radians(ft["pitch"]))
            for i_, v in enumerate(q): kf(o_ank, "rotation_quaternion", i_, fr, v)
            # すね：付け根から足首へ向け、長さを合わせる
            h = m.hips[1 - side]; hp = Vector((h.location.x, 0.0, HIP_Z))
            d = Vector((lx, ly, FOOT_Z + lift)) - hp; n = max(d.length, 1e-6)
            qh = Vector((0, 0, -1)).rotation_difference(d / n)
            for i_, v in enumerate(qh): kf(h, "rotation_quaternion", i_, fr, v)
            kf(h, "scale", 2, fr, n / m.leg_len)
    m.__dict__.setdefault("_last", {}); m._last["loc"] = (t1 + 0.5, (ax + dx, ay + dy, 0.0)); m._last["face"] = (t1 + 0.5, yaw)
    if end_face is not None: m.at(t1 + 0.9, face=end_face)
    # 足音：足が地面に着いた時刻
    for j in (0, 1):
        for c_ in p.feet[j][1:]:
            if c_.t_on < t_end + 0.1: STEPS.append(round(ts + c_.t_on / w, 3))
    return ts


def CLOCK_T0():
    return CLOCK["T0"] if "CLOCK" in globals() else T0
