# まるロボのペンギン歩き（3本目用）。common.py と s07s08_gate.py が exec で読む
#   2026-11-17 ユーザー「まるロボはペンギン歩きみたいなの前に作ってたよ」。1本目・2本目の marumotion.py と同じ数値で歩く
#     ・脚を胴から分け、脚の付け根（hip）で前後に振る。地面に着いている足は、その場で止める（すべらない）
#     ・支えている脚の側へ体が ±5° ゆれる（ペンギン歩き）。足の上げ幅 7cm。両足で支える所で体が少し沈む
#     ・進む向きは自動で前を向く（歩き出しの前に向きを変える）。最後は両足をそろえて止まる
#   前の版の walk() は、体ごと滑らせて上下にはずませるだけで、向きも手で決めていた（v9「後ろ向きにはずむ」「滑った動き」）
#   3本目のまるロボの前は −Y（目の向き）。体の大きさは root の scale（s）。長さは s=1 のときの値
import math
import bpy

ROLL_WALK = 8.0          # 支えている脚の側への横揺れ（度）。2026-11-17 ユーザー「横ゆれを大きく」で 5 → 8
LIFT = 0.07              # 足の上げ幅（s=1 のとき）
DIP = 0.018              # 両足で支える所での体の沈み
HIP_Z = 0.25             # 脚の付け根の高さ（root から。胴の中に隠れる所）
HIP_X = 0.17
L_LEG = 0.22             # 付け根 → 足の裏
STEP = 0.17              # 1 歩の長さのめやす（s=1）。これより長いと歩数をふやす
CAD_MAX = 4.5            # 1 秒の歩数の上限（ちょこちょこ歩きの上限）
TURN_T = 0.35            # 歩き出しの前に向きを変える時間


def _fc(ob, path, idx):
    ad = ob.animation_data or ob.animation_data_create()
    if ad.action is None: ad.action = bpy.data.actions.new(ob.name + " action")
    return ad.action.fcurves.find(path, index=idx) or ad.action.fcurves.new(path, index=idx)


def kf(ob, path, idx, frame, value, interp="LINEAR"):
    """速い鍵打ち（毎コマ打つため。key() は毎回すべての鍵を調べるので遅い）"""
    p = _fc(ob, path, idx).keyframe_points.insert(frame, value, options={'FAST'})
    p.interpolation = interp


def _clear(ob, path, idx, fa, fb):
    """fa〜fb の間の鍵を消す（歩きの毎コマの鍵で上書きするため）"""
    ad = ob.animation_data
    if not ad or not ad.action: return
    fc = ad.action.fcurves.find(path, index=idx)
    if not fc: return
    for kp in [k for k in fc.keyframe_points if fa <= k.co[0] <= fb][::-1]:
        fc.keyframe_points.remove(kp)


def _eval(ob, path, idx, frame, default):
    ad = ob.animation_data
    if ad and ad.action:
        fc = ad.action.fcurves.find(path, index=idx)
        if fc and len(fc.keyframe_points): return fc.evaluate(frame)
    return default


def rig_legs(m):
    """脚と靴を胴の子から外し、左右の付け根（空の物）の子にする。付け根は root の子"""
    bpy.context.view_layer.update()
    parts = [c for c in m.body.children if c.active_material and c.active_material.name.startswith(("maru_leg", "maru_foot"))]
    m.hips = []
    for sx in (-1, 1):
        h = bpy.data.objects.new("maru_hip", None); h.empty_display_size = 0.05
        for c in m.root.users_collection: c.objects.link(h)
        h.parent = m.root; h.location = (sx * HIP_X, 0.0, HIP_Z)
        bpy.context.view_layer.update()
        for c in parts:
            if (c.location.x > 0) == (sx > 0):
                mw = c.matrix_world.copy(); c.parent = h; c.matrix_parent_inverse.identity()
                bpy.context.view_layer.update(); c.matrix_basis = h.matrix_world.inverted() @ mw
        m.hips.append(h)
    bpy.context.view_layer.update()


def hop_legs(m, t, h, d):
    """跳ぶ間は脚も体と一緒に上がる（足が地面から離れる）"""
    for hp in m.hips:
        key(hp, ("location", 2), f(t), HIP_Z); key(hp, ("location", 2), f(t + d / 2), HIP_Z + h); key(hp, ("location", 2), f(t + d), HIP_Z)


def face_of(dx, dy):
    """進む向き (dx, dy) を向く root の回転（度）。前は −Y"""
    return math.degrees(math.atan2(dx, -dy))


def walk_penguin(m, t0, t1, a, b, face=None, end_face=None):
    """t0 に a を出て、t1 に b で止まる。向きは進む向き（face は使わない：前の呼び方との互換のため受け取るだけ）。
    end_face：止まったあとに向く向き（度）。返り値：歩数"""
    sc = m.root.scale.x
    ax, ay = a[0], a[1]; bx, by = b[0], b[1]
    dx, dy = bx - ax, by - ay; D = math.hypot(dx, dy)
    if D < 1e-3: return 0
    T = t1 - t0
    yaw_w = face_of(dx, dy)
    cur = m._last["face"][1] if "face" in m.__dict__.get("_last", {}) else math.degrees(m.root.rotation_euler[2])
    yaw_w = cur + ((yaw_w - cur + 180) % 360 - 180)
    if abs(yaw_w - cur) > 8:                              # 歩き出しの前に、その場で足踏みしながら向きを変える（足をすべらせない）
        m.at(t0 - TURN_T, face=cur); m.at(t0, face=yaw_w)
        for j, hp in enumerate(m.hips):
            ts = t0 - TURN_T + j * TURN_T / 2
            key(hp, ("location", 2), f(ts), HIP_Z); key(hp, ("location", 2), f(ts + TURN_T / 4), HIP_Z + LIFT * 0.7); key(hp, ("location", 2), f(ts + TURN_T / 2), HIP_Z)
            key(m.body, ("rotation_euler", 1), f(ts + TURN_T / 4), math.radians(ROLL_WALK * 0.6) * (1 if j == 0 else -1))
        key(m.body, ("rotation_euler", 1), f(t0), 0.0)
    else:
        m.at(t0, face=yaw_w)
    m.at(t0, loc=(ax, ay, 0.0))
    yaw = math.radians(yaw_w)
    fwd = (math.sin(yaw), -math.cos(yaw))                 # 前（−Y）の世界の向き
    rgt = (math.cos(yaw), math.sin(yaw))                  # 右（+X）の世界の向き
    # 歩数：1 歩の長さが STEP くらい。速すぎるときは歩数の上限で、歩幅を広げる
    v_l = D / sc / T
    cad = min(CAD_MAX, max(2.0, v_l / STEP))
    n = max(2, int(round(T * cad)))
    if n % 2: n += 1                                      # 両足をそろえて止まるため偶数
    dt = T / n

    def pos(t):                                           # 体の位置（ゆっくり出て、ゆっくり止まる）
        u = min(1.0, max(0.0, (t - t0) / T))
        w = u * u * u * (10 - 15 * u + 6 * u * u) * 0.35 + u * 0.65
        return (ax + dx * w, ay + dy * w)

    # 足の置き場所：i 歩目は i%2 の足（0＝左 x−、1＝右 x+）。着く時刻の体の位置より半歩前。最後の 2 歩は横にそろえる
    feet = []
    for j, sx in enumerate((-1, 1)):
        p = pos(t0)
        feet.append([(t0 - 1.0, (p[0] + rgt[0] * sx * HIP_X * sc, p[1] + rgt[1] * sx * HIP_X * sc))])
    for i in range(n):
        j = i % 2; sx = (-1, 1)[j]
        tl = t0 + (i + 1) * dt
        p = pos(tl)
        ahead = 0.0 if i >= n - 2 else 0.5 * (D / n) * 1.0
        feet[j].append((tl, (p[0] + fwd[0] * ahead + rgt[0] * sx * HIP_X * sc, p[1] + fwd[1] * ahead + rgt[1] * sx * HIP_X * sc), t0 + i * dt))

    def foot_at(j, t):
        """足 j の世界の位置と上げ幅（s=1 の単位）"""
        tr = feet[j]
        cur_p = tr[0][1]
        for e in tr[1:]:
            tl, pl, ts = e
            if t < ts: return cur_p, 0.0
            if t < tl:
                u = (t - ts) / (tl - ts); w = u * u * (3 - 2 * u)
                return (cur_p[0] + (pl[0] - cur_p[0]) * w, cur_p[1] + (pl[1] - cur_p[1]) * w), LIFT * math.sin(math.pi * u)
            cur_p = pl
        return cur_p, 0.0

    fa, fb = f(t0), f(t1)
    for h in m.hips:
        for idx in (1, 2): _clear(h, "location", idx, fa, fb)
        _clear(h, "rotation_euler", 0, fa, fb)
    for idx in (0, 1): _clear(m.root, "location", idx, fa + 1, fb - 1)
    _clear(m.body, "rotation_euler", 1, fa, fb); _clear(m.body, "location", 2, fa, fb)
    z0 = m.z0
    for fr in range(fa, fb + 1):
        t = t0 + (fr - fa) / FPS * (T / max(1e-6, (fb - fa) / FPS))
        p = pos(t)
        kf(m.root, "location", 0, fr, p[0]); kf(m.root, "location", 1, fr, p[1]); kf(m.root, "location", 2, fr, 0.0)
        # 足：root から見た前後（前は −Y）と上げ幅 → 付け根を前後に振る角度
        i = min(n - 1, int((t - t0) / dt)); u = (t - t0 - i * dt) / dt
        for j, h in enumerate(m.hips):
            fp, lift = foot_at(j, t)
            rx, ry = fp[0] - p[0], fp[1] - p[1]
            ahead = (rx * fwd[0] + ry * fwd[1]) / sc            # 前へ＋（s=1 の単位）
            th = math.asin(max(-0.8, min(0.8, ahead / L_LEG)))
            kf(h, "rotation_euler", 0, fr, -th)                  # x 軸の回転：負で足が前（−Y）へ
            kf(h, "location", 2, fr, HIP_Z + lift)
            kf(h, "location", 1, fr, 0.0)
        # 体：支えている脚の側へ ±5°（i 歩目に振っているのは i%2 の足 → 支えは反対）。両足で支える所で少し沈む
        sup = 1 if i % 2 == 0 else -1
        k = math.sin(math.pi * min(1.0, max(0.0, u)))
        kf(m.body, "rotation_euler", 1, fr, math.radians(ROLL_WALK) * sup * k)
        kf(m.body, "location", 2, fr, z0 - DIP * (1 - k))
    # 止まったら、足をそろえ、体をまっすぐに
    for h in m.hips:
        key(h, "rotation_euler", f(t1) + 1, (0.0, 0.0, 0.0)); key(h, ("location", 2), f(t1) + 1, HIP_Z)
    key(m.body, ("rotation_euler", 1), f(t1) + 2, 0.0); key(m.body, ("location", 2), f(t1) + 2, z0)
    key(m.root, ("rotation_euler", 2), f(t1), math.radians(yaw_w))     # 歩き終わりまで向きを止める（打たないと次の向きへ回り続けた）
    m._last["loc"] = (t1, (bx, by, 0.0)); m._last["face"] = (t1, yaw_w)
    if end_face is not None: m.at(t1 + 0.4, face=end_face)
    STEPS.extend(feet[j][k][0] for j in (0, 1) for k in range(1, len(feet[j])))   # 足音：足が着く時刻
    return n
