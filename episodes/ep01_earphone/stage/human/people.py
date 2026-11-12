# 電車の乗客10人：見た目（主人公の要素を組み替えた変化）と座り方
import math
import numpy as np
import hchar, hrig, pose_lib, motion, dance
from hrig import norm

SCREENS = "screens"

PEOPLE = {
    "PASSENGER 00": dict(hchar.HERO, pose="phone_left", screen="music.png", name="Hero"),
    "PASSENGER 01": dict(quality="mid", earbuds=True, pose="phone_both", screen="chat.png",
                         head=dict(hs=1.10, width=1.03, jaw=1.08, nose=0.95, eye=0.95), hair=dict(style="crop", seed=4, crown=(0.0, 0.45, 0.88)),
                         body=dict(shoulder=0.188, chest=1.04, belly=1.05),
                         colors=dict(skin="#E2AE8C", hair="#1C1714", top="#3A4A8C", pants="#2C2E33", shoe="#2F2F33", sole="#E8E4DC")),
    "PASSENGER 02": dict(quality="mid", earbuds=False, pose="phone_left", screen="news.png",
                         head=dict(hs=1.10, width=0.96, jaw=0.92, nose=0.80, eye=1.05, chin=0.9), hair=dict(style="bob", seed=7, front=0.40, sweep=0.5, crown=(-0.15, 0.45, 0.88)),
                         body=dict(shoulder=0.168, hip=1.04, chest=0.95, arm=0.93),
                         colors=dict(skin="#F0C4A8", hair="#4A2E1E", top="#C8B48A", pants="#3B3A44", shoe="#B9805A", sole="#3A2C24")),
    "PASSENGER 03": dict(quality="mid", earbuds=True, pose="phone_both", screen="game.png",
                         head=dict(hs=1.11, width=0.97, jaw=0.95, nose=0.82, eye=1.04), hair=dict(style="bob", seed=11, front=0.36, sweep=-0.6, crown=(0.2, 0.42, 0.88)),
                         body=dict(shoulder=0.170, hip=1.03, chest=0.96, arm=0.94),
                         colors=dict(skin="#E9B898", hair="#2A1A14", top="#8C2F4F", pants="#24262C", shoe="#F2F0EA", sole="#D8D2C6")),
    "PASSENGER 04": dict(quality="mid", earbuds=False, pose="phone_left", screen="news.png",
                         head=dict(hs=1.08, width=1.05, jaw=1.10, nose=1.05, eye=0.92, cheek=1.1), hair=dict(style="crop", seed=2, front=0.62, thick=0.8),
                         body=dict(shoulder=0.185, belly=1.18, waist=1.08),
                         colors=dict(skin="#D9A07E", hair="#8A8580", top="#CBD8E6", pants="#4A4A50", shoe="#3A2A20", sole="#2A2422")),
    "PASSENGER 05": dict(quality="mid", earbuds=True, pose="video", screen="video.png",
                         head=dict(hs=1.10, width=0.96, jaw=0.93, nose=0.82, eye=1.05), hair=dict(style="bob", seed=5, front=0.38, sweep=0.4),
                         body=dict(shoulder=0.168, hip=1.03, chest=0.95, arm=0.93),
                         colors=dict(skin="#EDC0A0", hair="#3A2418", top="#C8B48A", pants="#2E3440", shoe="#E8E4DA", sole="#C9C2B4")),
    "PASSENGER 06": dict(quality="mid", earbuds=True, pose="phone_left", screen="chat.png",
                         head=dict(hs=1.11, width=1.02, jaw=1.04, nose=0.92), hair=dict(style="short", seed=8, sweep=0.5, crown=(-0.2, 0.45, 0.87)),
                         body=dict(shoulder=0.184),
                         colors=dict(skin="#C98E6A", hair="#151110", top="#8C2F4F", pants="#2B3240", shoe="#ECEAE4", sole="#D9D3C8")),
    "PASSENGER 07": dict(quality="mid", earbuds=False, pose="phone_both", screen="game.png",
                         head=dict(hs=1.10, width=1.0, jaw=1.02, nose=0.9), hair=dict(style="crop", seed=9),
                         body=dict(shoulder=0.182, belly=1.06),
                         colors=dict(skin="#E6B08E", hair="#241A15", top="#E9E6DF", pants="#38404E", shoe="#30302F", sole="#E5E0D6")),
    "PASSENGER 08": dict(quality="mid", earbuds=True, pose="phone_left", screen="music.png",
                         head=dict(hs=1.11, width=0.97, jaw=0.94, nose=0.8, eye=1.04), hair=dict(style="bob", seed=12, front=0.42, sweep=-0.4),
                         body=dict(shoulder=0.169, hip=1.03, arm=0.94),
                         colors=dict(skin="#F2C9AE", hair="#5A3A26", top="#2F8A86", pants="#27292F", shoe="#C9A27A", sole="#3C2E26")),
    "PASSENGER 09": dict(quality="mid", earbuds=False, pose="phone_both", screen="news.png",
                         head=dict(hs=1.09, width=1.04, jaw=1.06, nose=0.98, eye=0.95), hair=dict(style="short", seed=13, sweep=-0.3),
                         body=dict(shoulder=0.186, chest=1.03),
                         colors=dict(skin="#E0A986", hair="#1E1915", top="#3A4A8C", pants="#2F3036", shoe="#2B2B2D", sole="#D8D2C6")),
}


# ---------------------------------------------------------------- 時間が止まる前の、小さな自然な動き（第1・2章）
#   顔を上げる（目が先、頭は0.35秒で上がる）・スクロール（手首を少し返し、画面の中身が流れる）・座り直す・
#   空いた手でイヤホンを押し込む・スマホを持ち直す。一人ずつ別の乱数で時刻を決める（全員が同時に動かない）
def make_acts(kind, seed, t_end=81.0, t_freeze=None, force=None):
    import random
    rng = random.Random(seed); acts = []
    t = rng.uniform(1.0, 14.0)                                      # 顔を上げる：14〜30秒おき、1.2〜3.5秒
    while t < t_end:
        hold = rng.uniform(1.2, 3.5); yaw = rng.choice((rng.uniform(-32, -12), rng.uniform(12, 32), rng.uniform(-6, 6)))
        acts.append(("look", t, hold, yaw)); t += hold + rng.uniform(14.0, 30.0)
    if kind == "phone_left":                                        # スクロール：4〜11秒おきに、2〜4回はじく
        t = rng.uniform(0.5, 6.0)
        while t < t_end:
            n = rng.randint(2, 4)
            for k in range(n): acts.append(("flick", t + k * rng.uniform(0.55, 1.1), 0.0, 0.0))
            t += n * 1.0 + rng.uniform(4.0, 11.0)
    else:                                                           # 両手：打つ・遊ぶ（小さく速い手の動き）を、ときどき
        t = rng.uniform(0.5, 6.0)
        while t < t_end:
            d = rng.uniform(1.5, 4.0); acts.append(("type", t, d, 0.0)); t += d + rng.uniform(3.0, 9.0)
    t = rng.uniform(8.0, 40.0)                                      # 座り直す：30〜55秒おき
    while t < t_end:
        acts.append(("shift", t, 0.0, rng.choice((-1.0, 1.0)))); t += rng.uniform(30.0, 55.0)
    t = rng.uniform(6.0, 30.0)                                      # スマホを持ち直す：20〜40秒おき
    while t < t_end:
        acts.append(("hold", t, 0.0, 0.0)); t += rng.uniform(20.0, 40.0)
    if kind == "phone_left" and rng.random() < 0.35:                # 空いた右手でイヤホンを押し込む（3人に1人ほど、1回）
        acts.append(("press", rng.uniform(10.0, 55.0), 0.0, 0.0))
    for a in (force or []): acts.append(a)                          # 時間が止まる瞬間に、動きの途中になる人
    return sorted(acts, key=lambda a: a[1])


def acts_at(person, t):
    """時刻 t の、動きの強さ（0〜1）"""
    out = dict(look=0.0, yaw=0.0, flick=0.0, type=0.0, shift=0.0, shift_s=1.0, hold=0.0, press=0.0)
    for kind, t0, d, v in person.get("acts", ()):
        if t < t0 - 0.1 or t > t0 + max(d, 1.0) + 2.0: continue
        if kind == "look":
            e = motion.env(t, t0 + 0.08, 0.38, d, 0.48)
            if e > out["look"]: out["look"], out["yaw"] = e, v
        elif kind == "flick": out["flick"] = max(out["flick"], motion.env(t, t0, 0.10, 0.04, 0.22))
        elif kind == "type": out["type"] = max(out["type"], motion.env(t, t0, 0.25, d, 0.3))
        elif kind == "shift":
            e = motion.env(t, t0, 0.55, 0.35, 0.9)
            if e > out["shift"]: out["shift"], out["shift_s"] = e, v
        elif kind == "hold": out["hold"] = max(out["hold"], motion.env(t, t0, 0.5, 0.0, 0.7))
        elif kind == "press": out["press"] = max(out["press"], motion.env(t, t0, 0.75, 0.55, 0.8))
    return out


def _slerp_R(R0, R1, s):
    from mathutils import Matrix
    q0 = Matrix([list(r) for r in R0]).to_quaternion(); q1 = Matrix([list(r) for r in R1]).to_quaternion()
    M = q0.slerp(q1, s).to_matrix(); return np.array([[M[i][j] for j in range(3)] for i in range(3)])


DANCE = None          # 踊り：関数 (person, t) → dance.crowd などの値（None なら踊らない）。ch0102_seq.py が入れる
UP = np.array([0, 0, 1.0]); FWD = np.array([0, -1.0, 0]); LAT = np.array([1.0, 0, 0])   # 人物の座標：上・前・左


def up_frame(n_dir, up_dir, roll_deg=0.0):
    """画面の向き n と上の向き（画面の中でのロール付き）→ phone_frame と同じ並び [x, a_long, n]"""
    n = norm(np.asarray(n_dir, float)); a = np.asarray(up_dir, float); a = norm(a - (a @ n) * n)
    if abs(roll_deg) > 1e-6:
        c_, s_ = math.cos(math.radians(roll_deg)), math.sin(math.radians(roll_deg)); a = norm(a * c_ + np.cross(n, a) * s_)
    return np.stack([np.cross(a, n), a, n], 1)


def raise_phone(rig, kind, C, R, dn, J):
    """踊り：スマホを顔の高さ（lift）・頭の上（phones_up）へ。体の揺れにもついていく"""
    if dn is None: return C, R
    C = C + (rig.head_pos("neck") - J["neck"]) * 0.8 * max(dn["on"], dn["phones_up"], dn["lift"])
    s = dn["phones_up"]
    if s > 1e-4:
        shL = rig.head_pos("upper_arm.L"); shR = rig.head_pos("upper_arm.R")
        base = shL if kind == "phone_left" else (shL + shR) / 2
        w = dn["wave"]; fin = dn["final"]
        C_up = base + UP * (0.46 + 0.04 * fin) + FWD * 0.08 + LAT * ((0.03 if kind == "phone_left" else 0.0) + 0.11 * w)
        R_up = up_frame(FWD * 0.75 + UP * 0.45, UP, 14.0 * w)
        C = C + (C_up - C) * s; R = _slerp_R(R, R_up, s)
    lift = dn["lift"]
    if lift > 1e-4: C = C + UP * (0.10 + 0.025 * dn["pump"]) * lift + FWD * 0.04 * lift
    return C, R


def raise_right(rig, wr, Rr, pole, dn, t=None):
    """踊り：空いた右手で太ももを拍ごとに叩く（拍で当たる）／突き上げる（拍ごとに押し上げ、スマホを上げたら一緒に左右へ）"""
    if dn is not None and t is not None and dn.get("tap", 0.0) > 1e-4:
        wr = wr + UP * 0.03 * math.sin(math.pi * (dance.beat_count(t) % 1.0)) ** 2 * dn["tap"]
    if dn is None or dn["arm_up"] < 1e-4: return wr, Rr, pole
    s = dn["arm_up"]; OUT = np.array([-1.0, 0, 0])
    shR = rig.head_pos("upper_arm.R")
    w_up = shR + UP * (0.40 + 0.05 * dn["final"] + 0.05 * dn["pump"]) + FWD * 0.10 + OUT * 0.05 + LAT * (0.10 * dn["wave"] * dn["phones_up"])
    Yh = norm(UP + FWD * 0.25); Zh = np.array([0, 1.0, 0]); Zh = norm(Zh - (Zh @ Yh) * Yh); R_up = np.stack([np.cross(Yh, Zh), Yh, Zh], 1)
    wr = wr + (w_up - wr) * s + OUT * 0.10 * 4 * s * (1 - s)
    return wr, _slerp_R(Rr, R_up, s), norm(np.asarray(pole, float) * (1 - s) + np.array([-1.0, 0.0, -0.2]) * s)


def phone_center(kind):
    if kind == "video": return (0.0, -0.33, 0.95), 0.0
    if kind == "phone_both": return (0.0, -0.31, 0.905), 0.30
    return (0.035, -0.300, 0.930), 0.30


def both_grip(C, R, sd):
    """両手で持つ：両手で下の角を支え、親指を画面へ"""
    x, a_long, n = R[:, 0], R[:, 1], R[:, 2]
    sx = 1.0 if sd == "L" else -1.0           # 人物の左＝画面の左（−x）
    Y = norm(a_long * 0.85 + x * 0.52 * sx)
    Z = -n; Z = norm(Z - (Z @ Y) * Y); X = np.cross(Y, Z)
    palm = C - x * 0.030 * sx - a_long * 0.045 - n * pose_lib.PALM_N
    return palm - Y * 0.050, np.stack([X, Y, Z], 1)


def video_grip(C, R, sd):
    """横向きの動画：両手で左右の端を持つ（R の列：上・人物の左・画面の向き）"""
    up, side, n = R[:, 0], R[:, 1], R[:, 2]
    sx = 1.0 if sd == "L" else -1.0
    Y = norm(up * 0.90 - side * sx * 0.35)
    Z = -n; Z = norm(Z - (Z @ Y) * Y); X = np.cross(Y, Z)
    palm = C + side * 0.058 * sx - up * 0.012 - n * pose_lib.PALM_N
    return palm - Y * 0.050, np.stack([X, Y, Z], 1)


def base_pose(person, t=0.0, sway=None):
    """座ってスマホを見る基本姿勢（時刻 t の呼吸・揺れつき）。rig の q を設定し、スマホの位置を返す"""
    rig = person["rig"]; J = person["J"]; kind = person["kind"]; ph = person.get("phase", 0.0)
    rig.reset()
    b = motion.breath(t, period=person.get("breath", 4.0), phase=ph)
    sw = 0.0 if sway is None else sway
    ac = acts_at(person, t)
    dn = DANCE(person, t) if DANCE else None
    if dn:                                                          # 踊っている間は、ふだんの小さな動きはしない
        for k_ in ac:
            if k_ not in ("yaw", "shift_s"): ac[k_] *= (1.0 - dn["on"])
    dz = dn or dict(spine_x=0.0, spine_z=0.0, chest_x=0.0, chest_z=0.0, neck_x=0.0, head_x=0.0, head_z=0.0)
    sh = ac["shift"] * ac["shift_s"]
    gl = person.get("glance")                                       # 決めた時間だけ、ある点（隣の人など）へ顔を向ける：(t0, t1, 点, 向きの角度[, 身を引く角度])
    g_on = ac["look"] if (gl and gl[0] <= t <= gl[1]) else 0.0
    g_turn = gl[3] * g_on if g_on else 0.0
    g_lean = (gl[4] if gl and len(gl) > 4 else 0.0) * g_on                 # まとめ：踊る主人公から少し身を引く（顔のない頭でも、見ていると分かるように）
    rig.rot("spine", x=4 + 0.3 * b + 0.5 * sw + 2.6 * sh + dz["spine_x"], z=0.8 * sh + dz["spine_z"] + 0.6 * g_lean, y=0.12 * g_turn)
    rig.rot("chest", x=5 - 1.0 * b + 0.4 * sw - 1.4 * sh + dz["chest_x"], z=dz["chest_z"] + 0.4 * g_lean, y=0.13 * g_turn)
    rig.rot("neck", x=9 + person.get("neck", 0.0) - 8.0 * ac["look"] + dz["neck_x"], z=0.25 * ac["yaw"] * ac["look"], y=0.3 * g_turn)
    rig.rot("head", x=13 + 0.6 * b + person.get("headx", 0.0) - 20.0 * ac["look"] + 0.8 * ac["type"] * math.sin(2 * math.pi * 1.7 * t) + dz["head_x"],
            z=person.get("headz", 0.0) + 0.75 * ac["yaw"] * ac["look"] + dz["head_z"], y=0.7 * g_turn)
    for sd in ("L", "R"): rig.rot("clav." + sd, x=0.0, z=0.0, y=0.0)
    rig.fk()
    eye_mid = (rig.head_pos("eye.L") + rig.head_pos("eye.R")) / 2
    c, tilt = phone_center(kind)
    c = person.get("phone_c", c)
    jig = ac["type"] * 0.004 * math.sin(2 * math.pi * 3.3 * t + ph) + ac["type"] * 0.003 * math.sin(2 * math.pi * 5.1 * t)   # 打つ・遊ぶ：小さく速い手の動き
    c = (c[0], c[1] - 0.012 * ac["hold"], c[2] + 0.028 * ac["hold"] - 0.012 * ac["look"] + jig)                              # 持ち直す・顔を上げると少し下がる
    C, R = pose_lib.phone_frame(J, eye_mid, center=c, tilt_up=tilt + 0.06 * ac["flick"])                                       # はじくと手首が少し返る
    C, R = raise_phone(rig, kind, C, R, dn, J)
    if kind == "video":  # 横向き：画面の上辺を人物の左へ
        R = np.stack([R[:, 1], -R[:, 0], R[:, 2]], 1)
    up_s = dn["phones_up"] if dn else 0.0
    if kind == "phone_left":
        wl, Rl = pose_lib.left_grip(C, R)
        rig.ik2("upper_arm.L", "forearm.L", wl, pole=norm(np.array([0.7, 0.4, -1.0]) * (1 - up_s) + np.array([1.0, 0.0, -0.2]) * up_s), end="hand.L", end_R=Rl)
        pose_lib.curl(rig, "L", 38, 70, 38, thumb=(6, 8, 6))
        wr, Rr = pose_lib.thigh_rest(J, "R", -1)
        if ac["press"] > 1e-3 and person.get("bud_R") is not None:      # 空いた右手でイヤホンを押し込む（太もも → 耳 → 太もも）
            bud = rig.posed_point("head", person["bud_R"]); w1, R1 = pose_lib.ear_touch_pict(bud, sx=-1); s_ = ac["press"]
            arc = np.array([-0.05, -0.06, 0.0]) * 4 * s_ * (1 - s_)
            wr = wr + (w1 - wr) * s_ + arc; Rr = _slerp_R(Rr, R1, s_)
            pole = norm(np.array([-0.6, 0.5, -1.0]) * (1 - s_) + np.array([-0.9, -0.5, -0.6]) * s_)
        else:
            pole = (-0.6, 0.5, -1.0)
        wr, Rr, pole = raise_right(rig, wr, Rr, pole, dn, t)
        rig.ik2("upper_arm.R", "forearm.R", wr, pole=pole, end="hand.R", end_R=Rr)
        pose_lib.curl(rig, "R", 14, 22, 12, thumb=(6, 6, 4), spread=2)
    else:
        for sd, sx in (("L", 1.0), ("R", -1.0)):
            w, Rh = (both_grip if kind == "phone_both" else video_grip)(C, R, sd)
            rig.ik2("upper_arm." + sd, "forearm." + sd, w, pole=norm(np.array([0.7 * sx, 0.4, -1.0]) * (1 - up_s) + np.array([1.0 * sx, 0.0, -0.2]) * up_s),
                    end="hand." + sd, end_R=Rh)
            pose_lib.curl(rig, sd, 30, 55, 30, thumb=(4, 14, 18))
    rig.fk()
    scr = C + R[:, 2] * 0.006
    if g_on > 1e-3: scr = scr + (np.asarray(gl[2], float) - scr) * min(1.0, g_on * 1.3)      # 目は顔より先に向く
    yaw = pitch = 0.0
    for sd in ("L", "R"): yaw, pitch = rig.look("eye." + sd, scr)
    # まばたき：人ごとにずらして 3〜5秒に1回（画面を見ているときは少なめ）
    period = person.get("blink_T", 4.2); bl = motion.blink((t + ph * 0.7) % period, period - 0.4); person["_blink"] = bl
    up = 0.55 * pitch
    for sd in ("L", "R"):
        rig.rot("lid_up." + sd, x=up - (person.get("lid_up", 30.0) + up + 12.0) * bl)
        rig.rot("lid_lo." + sd, x=0.25 * pitch + (person.get("lid_lo", 33.0) - 14.0) * bl)
    rig.fk()
    return C, R
