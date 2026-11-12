# 主人公の動き：音楽を聴く → 音が途切れる → 反応（目→頭→体の順）→ 右手でイヤホンに触れる
# 数値の根拠：反応時間0.2秒、サッカード 2.2ms/度+21ms、まばたき（閉90ms・開170ms）、呼吸 毎分15回、
#            手の到達は躍度最小（釣り鐘形の速さ）、所要時間はフィッツの法則（約0.75秒）
import math
import numpy as np
import motion, pose_lib, people, dance
from motion import mj, env, blink
from hrig import norm, m3

T_DROP = 3.0          # 音が途切れる時刻（秒）
RT = 0.20             # 反応時間（聴覚→動き出し）
BPM = 78.3            # 曲は約156.6BPM。うなずきは半分の速さ（2拍に1回）
BEAT0 = 0.08          # 曲の20.0秒から使う：最初の拍は0.08秒
SONG_START = 20.0
DANCE = None          # 踊り：関数（本編の秒）→ dance.hero の値。ch0102_seq.py が入れる（None なら昔どおりの小さなうなずき）
T_REL = 0.0           # 本編の秒 − 主人公の時計


def timeline(t):
    """各要素の強さ（0〜1）を返す"""
    d = t - T_DROP
    music = 1.0 if d < 0 else 0.0
    return dict(
        music=music,
        nod_on=1.0 - mj(t, T_DROP + 0.12, 0.25),                    # 曲が止まると0.12〜0.37秒でうなずきが止まる
        brow=env(t, T_DROP + RT, 0.12, 1.6, 0.6),                    # 眉が上がる（驚き・注意）
        wide=env(t, T_DROP + RT, 0.10, 1.4, 0.5),                    # まぶたが少し大きく開く
        gaze=mj(t, T_DROP + RT + 0.02, motion.saccade_time(28)),     # 目が先に跳ぶ（約80ms）
        head=mj(t, T_DROP + RT + 0.06, 0.45),                        # 頭は少し遅れて0.45秒
        torso=mj(t, T_DROP + RT + 0.15, 0.60),                       # 胴はさらに遅れる
        mouth=env(t, T_DROP + 0.45, 0.16, 1.3, 0.5),                 # 口が「o」
        flat=mj(t, T_DROP + 1.75, 0.5),                              # 「o」のあとは笑顔に戻らず、まっすぐな口（まだ不思議）
        reach=mj(t, T_DROP + 0.55, 0.75),                            # 右手がイヤホンへ（0.75秒）
        press=env(t, T_DROP + 1.32, 0.10, 0.06, 0.14),               # 指でイヤホンを軽く押す
        phone_down=mj(t, T_DROP + 0.60, 0.80),                       # スマホを持つ手が少し下がる
        breath_hold=env(t, T_DROP + 0.25, 0.3, 1.0, 0.6),            # 息を一瞬止める
    )


BLINKS = [0.75, 2.45, T_DROP + 2.05, T_DROP + 4.30]


def reading_target(C, R, t):
    """画面を読む視線：250msの注視と短いサッカードで行を左→右、次の行へ"""
    x, a_long, n = R[:, 0], R[:, 1], R[:, 2]
    k = int(t / 0.28); u = (t - k * 0.28) / 0.28
    col = k % 3; line = (k // 3) % 4
    def pt(c, l): return C + x * (-0.018 + 0.018 * c) + a_long * (0.030 - 0.012 * l) + n * 0.006
    prev = pt((k - 1) % 3, ((k - 1) // 3) % 4); cur = pt(col, line)
    s = mj(u, 0, 0.12)
    return prev + (cur - prev) * s


def pose_at(person, t, sway_deg, bud_R, extras):
    """時刻 t の主人公の姿勢を rig に設定する。extras に表情などの値を返す"""
    rig = person["rig"]; J = person["J"]; tl = timeline(t)
    rig.reset()
    # --- 体幹：呼吸（止める時もある）・電車の揺れ・うなずき
    th = breath_clock(t)                      # 息を止めている間だけ止まる時計（止める前後で途切れない）
    b = motion.breath(th, period=4.0, phase=0.6)
    beat = ((t - BEAT0) * BPM / 60.0) % 1.0
    nod = (0.5 + 0.5 * math.cos(2 * math.pi * beat)) * tl["nod_on"]
    dn = DANCE(t + T_REL) if DANCE else None
    if dn is not None: nod = 0.0                                     # うなずきは踊りの値で（曲の拍に合わせる）
    dz = dn or dict(spine_x=0.0, spine_z=0.0, chest_x=0.0, chest_z=0.0, neck_x=0.0, head_x=0.0, head_z=0.0)
    person["sp_neck"].step(1.6 * nod, 1 / 24); person["sp_head"].step(person["sp_neck"].x * 0.9, 1 / 24)
    rig.rot("spine", x=4 + 0.3 * b + 0.5 * sway_deg - 1.5 * tl["torso"] + dz["spine_x"], z=dz["spine_z"])
    rig.rot("chest", x=5 - 1.0 * b + 0.4 * sway_deg - 2.0 * tl["torso"] + dz["chest_x"], z=-4.0 * tl["torso"] + dz["chest_z"])
    for sd in ("L", "R"): rig.rot("clav." + sd, x=0.6 * b)
    # 頭：下を見る → 音が消えると顔を上げ、右へ向き、右へ傾ける（聞き耳）
    hx = 13 + 0.6 * b + person["sp_head"].x - 14.0 * tl["head"] + dz["head_x"]
    rig.rot("neck", x=9 + person["sp_neck"].x - 6.0 * tl["head"] + dz["neck_x"], z=-6.0 * tl["head"])
    rig.rot("head", x=hx, z=-12.0 * tl["head"] + dz["head_z"], y=9.0 * tl["head"])
    rig.fk()
    hair_follow(person, rig)
    eye_mid = (rig.head_pos("eye.L") + rig.head_pos("eye.R")) / 2
    C, R = pose_lib.phone_frame(J, eye_mid, center=(0.035, -0.300 + 0.02 * tl["phone_down"], 0.930 - 0.05 * tl["phone_down"]))
    C, R = people.raise_phone(rig, "phone_left", C, R, dn, J)           # 踊り：スマホを頭の上へ
    up_s = dn["phones_up"] if dn else 0.0
    # 左手：スマホ
    wl, Rl = pose_lib.left_grip(C, R)
    rig.ik2("upper_arm.L", "forearm.L", wl, pole=norm(np.array([0.7, 0.4, -1.0]) * (1 - up_s) + np.array([1.0, 0.0, -0.2]) * up_s), end="hand.L", end_R=Rl)
    th_s = env(t, 1.30, 0.12, 0.05, 0.18)          # 親指で画面をなぞる（スクロール）
    pose_lib.curl(rig, "L", 38, 70, 38, thumb=(6 + 10 * th_s, 8 + 22 * th_s, 6 + 18 * th_s))
    # 右手：太もも → イヤホン（躍度最小の軌道＋少し外へふくらむ弧）
    w0, R0 = pose_lib.thigh_rest(J, "R", -1)
    pole0 = np.array([-0.6, 0.5, -1.0])
    if dn is not None:                                               # 踊り：右手を突き上げる／太ももを拍ごとに叩く（拍で手が太ももに当たる）
        w0, R0, pole0 = people.raise_right(rig, w0, R0, pole0, dn, t + T_REL)
    bud = rig.posed_point("head", bud_R)
    if person.get("pict"):
        w1, R1 = pose_lib.ear_touch_pict(bud, sx=-1)                 # 見えている手の先の腹でイヤホンに触れる
    else:
        w1, R1 = pose_lib.ear_touch(bud, sx=-1)
        w1 = w1 + person.get("touch_fix", np.zeros(3))
    s = tl["reach"]
    arc = np.array([-0.06, -0.07, 0.0]) * 4 * s * (1 - s)
    press = norm(rig.head_pos("head") - bud) * 0.004 * tl["press"]
    wr = w0 + (w1 - w0) * s + arc + press
    Rr = slerp_R(R0, R1, s)
    pole = norm(np.asarray(pole0, float) * (1 - s) + np.array([-0.9, -0.5, -0.6]) * s)
    rig.ik2("upper_arm.R", "forearm.R", wr, pole=pole, end="hand.R", end_R=Rr)
    if person.get("pict"): extras["wrist_twist"] = relax_wrist(rig, "R")
    # 指：休み → 人さし指と中指を伸ばし、薬指と小指は軽く握る
    rig.rot("index_01.R", x=-(14 * (1 - s) + 8 * s)); rig.rot("index_02.R", x=-(22 * (1 - s) + 10 * s)); rig.rot("index_03.R", x=-(12 * (1 - s) + 6 * s))
    rig.rot("middle_01.R", x=-(14 * (1 - s) + 12 * s)); rig.rot("middle_02.R", x=-(22 * (1 - s) + 14 * s)); rig.rot("middle_03.R", x=-(12 * (1 - s) + 8 * s))
    for f in ("ring", "pinky"):
        rig.rot(f + "_01.R", x=-(14 + 36 * s)); rig.rot(f + "_02.R", x=-(22 + 50 * s)); rig.rot(f + "_03.R", x=-(12 + 30 * s))
    rig.rot("thumb_01.R", x=-6); rig.rot("thumb_02.R", x=-(6 + 14 * s)); rig.rot("thumb_03.R", x=-(4 + 10 * s))
    rig.fk()
    # 目：画面を読む → 音が消えると右上へ跳ぶ（頭が回る間も目標を見続ける＝前庭動眼反射）
    read = reading_target(C, R, t)
    side = rig.head_pos("head") + np.array([-0.55, -0.45, 0.10])
    g = tl["gaze"]
    tgt = read * (1 - g) + side * g
    for sd in ("L", "R"):
        yaw, pitch = rig.look("eye." + sd, tgt)
    # まぶた：目の上下に合わせて動く＋まばたき＋見開き
    bl = max(blink(t, tb) for tb in BLINKS)
    up_rest = 0.55 * pitch + 6.0 * tl["wide"]
    for sd in ("L", "R"):
        rig.rot("lid_up." + sd, x=up_rest - (person.get("lid_up", 30.0) + up_rest + 12.0) * bl)
        rig.rot("lid_lo." + sd, x=0.25 * pitch + (person.get("lid_lo", 33.0) - 14.0) * bl - 2.0 * tl["wide"])
        rig.rot("brow." + sd, x=0.0)
        rig.loc["brow." + sd] = __import__("mathutils").Vector((0, 0.0022 * tl["brow"], 0))
    rig.fk()
    extras.update(mouth_o=0.85 * tl["mouth"], mouth_flat=tl["flat"] * (1 - tl["mouth"]), music=tl["music"], C=C, R=R, breath=b,
                  nod=person["sp_head"].x + person["sp_neck"].x,
                  blink=bl, wide=tl["wide"])
    return tl


def relax_wrist(rig, sd="R", share=1.0):
    """手首はほとんどねじれない（ねじれは前腕の回内・回外＝2本の骨が交差して起こる）。
    手の向きの、前腕の軸まわりのねじれ（休みの姿勢から）を前腕の回転に移す。手の向きと手首の位置は変わらない"""
    from mathutils import Matrix
    fa, hd = "forearm." + sd, "hand." + sd
    Rf = m3(rig.M[fa]); Rh = m3(rig.M[hd])
    Q_rest = m3(rig.rest[fa]).T @ m3(rig.rest[hd]); D = (Rf.T @ Rh) @ Q_rest.T
    q = Matrix([list(r) for r in D]).to_quaternion()
    tw = 2 * math.atan2(q.y, q.w); tw = (tw + math.pi) % (2 * math.pi) - math.pi
    phi = share * tw; c, s_ = math.cos(phi), math.sin(phi)
    Ry = np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
    rig.set_world_rot(fa, Rf @ Ry); rig.set_world_rot(hd, Rh)
    return math.degrees(tw)


def slerp_R(R0, R1, s):
    from mathutils import Matrix
    q0 = Matrix([list(r) for r in R0]).to_quaternion(); q1 = Matrix([list(r) for r in R1]).to_quaternion()
    q = q0.slerp(q1, s); M = q.to_matrix()
    return np.array([[M[i][j] for j in range(3)] for i in range(3)])


def hair_follow(person, rig, fps=24.0, f=2.6, z=0.32, gain=1.8):
    """髪の慣性：頭の角加速度と逆向きに、ばね＋ダンパーで遅れて揺れる（重なり合う動き）"""
    from mathutils import Matrix
    Rh = np.array([[rig.M["head"][i][j] for j in range(3)] for i in range(3)])
    st = person.setdefault("hair_st", dict(R=None, w=np.zeros(3), th=np.zeros(3), v=np.zeros(3)))
    if st["R"] is None:
        st["R"] = Rh; return
    dR = st["R"].T @ Rh
    ang = math.acos(max(-1.0, min(1.0, (np.trace(dR) - 1) / 2)))
    axis = np.array([dR[2, 1] - dR[1, 2], dR[0, 2] - dR[2, 0], dR[1, 0] - dR[0, 1]])
    w_now = (axis / (2 * math.sin(ang)) * ang * fps) if ang > 1e-6 else np.zeros(3)   # 頭の座標での角速度
    alpha = (w_now - st["w"]) * fps
    wn = 2 * math.pi * f; h = 1.0 / fps / 8
    for _ in range(8):
        a = -wn * wn * st["th"] - 2 * z * wn * st["v"] - gain * alpha
        st["v"] = st["v"] + a * h; st["th"] = st["th"] + st["v"] * h
    st["R"] = Rh; st["w"] = w_now
    # 頭の局所軸（X＝人物の左、Y＝上、Z＝前）→ 髪の骨の局所軸（X＝左、Y＝後ろ、Z＝上）
    th = np.degrees(st["th"])
    rig.rot("hair", x=th[0], y=-th[2], z=th[1])


def breath_clock(t, n=400):
    """呼吸の時計：息を止めている度合い（0〜1）の分だけ進みを遅らせる。th = t − ∫hold dτ（なめらかにつながる）"""
    if t <= T_DROP: return t
    ts = np.linspace(T_DROP, t, n); h = np.array([env(x, T_DROP + 0.25, 0.3, 1.0, 0.6) for x in ts])
    return t - float(np.trapz(h, ts))
