# opening_pict.py から exec される：冒頭の動き 約22秒・3ショット（晴れた電車＋ピクトグラムの人）
#   A（0〜5秒）  車内の全景。曲が流れ、カメラが主人公へゆっくり寄る
#   B（5〜13秒） 主人公（右前から）。8秒で音が途切れ、目→頭→体→手の順に反応し、右手で右耳のイヤホンに触れる。光が暗くなりスポット
#   C（13〜22秒）まるロボ：見上げる→ボタンへ向く→しゃがむ→跳ぶ→放物線→着地を脚で受け止める→時間が止まる→こちらを向く
# まるロボ・ボタン・ほこり・カメラCの座標は「1.65倍の電車」の古い座標（OldWorld の中）。to_w() で今の電車の座標にする
import json
f0, f1 = [int(x) for x in A.frames.split(":")]
T_B, T_C, T_END = 5.0, 13.0, 22.0
N = int(round(T_END * FPS))
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
T_DROP_G = T_B + hero_anim.T_DROP
mj = motion.mj

# ---------------------------------------------------------------- まるロボの動き（物理：前と同じ）
G_W = 9.81 * S
RS = 0.55
b0 = button.location.copy(); TOP = 0.178
cam_c_pos = Vector((b0.x - 1.00, b0.y - 1.60, 0.40))
_away = Vector((b0.x - cam_c_pos.x, b0.y - cam_c_pos.y, 0.0)).normalized()
P0 = Vector((b0.x, b0.y, 0.0)) + _away * 0.55
P1 = Vector((b0.x, b0.y, TOP))
H_AP = 0.40
VZ = math.sqrt(2 * G_W * H_AP); T_UP = VZ / G_W; T_DN = math.sqrt(2 * (H_AP - TOP) / G_W); T_FL = T_UP + T_DN
U_TURN, U_CROUCH, U_PUSH, U_TAKE = 0.8, 1.60, 1.96, 2.08
U_LAND = U_TAKE + T_FL; U_FREEZE = U_LAND + 0.10
V_IMPACT = G_W * T_DN
T_FREEZE = T_C + U_FREEZE
print(f"JUMP vz={VZ:.2f} flight={T_FL:.3f}s impact={V_IMPACT:.2f} freeze_at={T_FREEZE:.2f}s", flush=True)
hero["rig"].fk(); hp0, bud0 = hero_points()
hero_w = to_old(hp0)                                  # 主人公の頭（古い座標）：まるロボが最初に見上げる先
def yaw_to(src, dst):
    d = dst - src; return math.atan2(-d.x, d.y)
PSI_HERO = yaw_to(P0, hero_w); PSI_BTN = yaw_to(P0, P1); PSI_CAM = yaw_to(P1, cam_c_pos)
legs = [o for o in hier(robot) if o.name.endswith("• leg") or o.name.endswith("• leg.001")]
LEG_REST = {o.name: o.location.copy() for o in legs}; TORSO_REST = r_torso.location.copy()


def crouch_delta(u):
    if u < U_CROUCH: return 0.004 * math.sin(2 * math.pi * 0.5 * u)
    if u < U_PUSH: return 0.10 * mj(u, U_CROUCH, 0.30)
    if u < U_TAKE: return 0.10 + (-0.03 - 0.10) * mj(u, U_PUSH, U_TAKE - U_PUSH)
    if u < U_LAND:
        s = (u - U_TAKE) / T_FL; return -0.03 + 0.06 * math.sin(math.pi * s) - 0.01 * s
    t = u - U_LAND; w_ = 2 * math.pi * 6.0; z = 0.5; wd = w_ * math.sqrt(1 - z * z)
    return 0.11 * math.exp(-z * w_ * t) * math.sin(wd * t) / 0.87 * (1 if t < 2.0 else 0)


def torso_pitch(u):
    p = 14.0 * (1 - mj(u, U_TURN, 0.6)) - 8.0 * mj(u, U_TURN, 0.6)
    p += -6.0 * mj(u, U_CROUCH, 0.30) * (1 - mj(u, U_TAKE, 0.15))
    if U_TAKE <= u < U_LAND: p += -4.0 + 10.0 * (u - U_TAKE) / T_FL
    if u >= U_LAND: p += -10.0 * math.exp(-(u - U_LAND) / 0.12) + 8.0 * mj(u, U_FREEZE + 0.6, 0.6) * 0.5
    return p


def robot_root(u):
    if u < U_TAKE: return P0.copy()
    if u < U_LAND:
        tau = u - U_TAKE; s = tau / T_FL
        p = P0.lerp(P1, s); p.z = VZ * tau - 0.5 * G_W * tau * tau; return p
    t = u - U_LAND
    dz = -0.03 * (1 - math.exp(-t / 0.025)) + 0.004 * math.exp(-t / 0.08) * math.sin(2 * math.pi * 9 * t)
    return P1 + Vector((0, 0, dz))


def robot_yaw(u):
    y = PSI_HERO + (PSI_BTN - PSI_HERO) * mj(u, U_TURN, 0.6)
    return y + (PSI_CAM - PSI_BTN) * mj(u, U_FREEZE + 0.6, 0.6)


# ---------------------------------------------------------------- ほこりの動き（シェイプキー）と光の輪
dme = dust.data
if dme.shape_keys is None:
    dust.shape_key_add(name="Basis"); rng_d = np.random.default_rng(5)
    base = np.array([v.co[:] for v in dme.vertices]); nm = 160; nper = len(base) // nm
    for kn in ("dA", "dB"):
        off = rng_d.normal(0, 1, (nm, 3)) * np.array([0.05, 0.05, 0.035])
        kb = dust.shape_key_add(name=kn, from_mix=False)
        kb.data.foreach_set("co", (base + np.repeat(off, nper, axis=0)).ravel().astype(np.float32))
pulse.data.materials.clear(); pulse.data.materials.append(mat_emit("Pulse glow", (0.3, 1.0, 0.9), 6.0))

# ---------------------------------------------------------------- カメラ3台
def new_cam(name):
    cd_ = bpy.data.cameras.new(name); ob_ = link(O.new(name, cd_)); cd_.sensor_width = 36; return ob_
camA, camB, camC = new_cam("Cam A wide"), new_cam("Cam B hero"), new_cam("Cam C robot")
for nm_, fr_, cm_ in (("A", 1, camA), ("B", int(T_B * FPS) + 1, camB), ("C", int(T_C * FPS) + 1, camC)):
    mk = scene.timeline_markers.new(nm_, frame=fr_); mk.camera = cm_
scene.camera = camA
def aim_cam(cm, pos, tgt, lens):
    cm.location = Vector(pos); cm.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler(); cm.data.lens = lens
# B：主人公の右前（右手で右耳のイヤホンに触れるのが見える向き）
aim_cam(camB, hp0 + Vector((-1.48, 0.44, 0.04)), hp0 + Vector((0.0, 0.04, -0.25)), 34)
camB.data.dof.use_dof = True; camB.data.dof.focus_distance = (hp0 - camB.location).length; camB.data.dof.aperture_fstop = 2.8
camC.data.dof.use_dof = True; camC.data.dof.focus_object = robot; camC.data.dof.aperture_fstop = 3.2
camA.data.dof.use_dof = True; camA.data.dof.aperture_fstop = 5.6

# ---------------------------------------------------------------- 毎コマの計算と記録
tt, acc = motion.train_sway(T_END + 1, FPS, seed=3, rms=0.22)
sway = motion.pendulum_response(acc, FPS)
bk = hrig.Baker()
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
ex = {}; hero_anim.pose_at(hero, hero_anim.T_DROP + 2.0, 0.0, hero_bud_rest, ex)
rig_h = hero["rig"]; rig_h.fk()
tip = (rig_h.tail_pos("index_03.R") + rig_h.tail_pos("middle_03.R")) / 2
hero["touch_fix"] = (rig_h.posed_point("head", hero_bud_rest) + np.array([-0.006, -0.004, -0.010])) - tip
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
ant = motion.Spring(3.5, 0.18); prev_z = []; log = dict(t=[], root_z=[], crouch=[], antenna=[], pitch=[])
WN = w.node_tree; HN = hm.node_tree
for f in range(1, N + 1):
    t = (f - 1) / FPS
    frozen = t >= T_FREEZE
    if not frozen:
        ex = {}
        hero_anim.pose_at(hero, t - T_B, float(sway[f - 1]), hero_bud_rest, ex)
        bk.pose(hero["rig"], f)
        for sd in ("L", "R"):
            sk = hero["objs"]["eye." + sd].data.shape_keys
            bk.put(sk, 'key_blocks["blink"].value', 0, f, ex["blink"]); bk.put(sk, 'key_blocks["wide"].value', 0, f, ex["wide"] * (1 - ex["blink"]))
        for n, person in P.items():
            if n == "H": continue
            people.base_pose(person, t, sway=float(sway[(f - 1 + 7 * (person["idx"] * 3) % 11) % len(sway)]) * 0.8)
            bk.pose(person["rig"], f)
        bk.put(dme.shape_keys, 'key_blocks["dA"].value', 0, f, math.sin(2 * math.pi * 0.21 * t + 0.3))
        bk.put(dme.shape_keys, 'key_blocks["dB"].value', 0, f, math.sin(2 * math.pi * 0.13 * t + 1.7))
    # まるロボ（ショットCだけ見える）
    u = t - T_C
    if u >= 0.0:
        root = robot_root(u); dl = crouch_delta(u); pt = torso_pitch(u); yw = robot_yaw(u)
        tz = root.z + RS * (TORSO_REST.z - dl); prev_z.append(tz)
        acc_z = 0.0
        if len(prev_z) >= 3: acc_z = (prev_z[-1] - 2 * prev_z[-2] + prev_z[-3]) * FPS * FPS
        th = ant.step(-0.006 * acc_z, 1.0 / FPS); th = max(-0.52, min(0.52, th))
        for ob_, path, idx, val in ((robot, "location", 0, root.x), (robot, "location", 1, root.y), (robot, "location", 2, root.z),
                                   (robot, "rotation_euler", 2, yw), (robot, "scale", 0, RS), (robot, "scale", 1, RS), (robot, "scale", 2, RS),
                                   (r_torso, "location", 2, TORSO_REST.z - dl), (r_torso, "rotation_euler", 0, math.radians(pt)),
                                   (r_torso, "scale", 2, 1.0 - 0.25 * max(dl, 0.0)), (r_torso, "scale", 0, 1.0 + 0.12 * max(dl, 0.0)),
                                   (r_torso, "scale", 1, 1.0 + 0.12 * max(dl, 0.0))):
            bk.put(ob_, path, idx, f, val)
        if r_ant: bk.put(r_ant, "rotation_euler", 0, f, th)
        for lg in legs:
            k = (0.43 - dl) / 0.43
            bk.put(lg, "location", 2, f, LEG_REST[lg.name].z - dl); bk.put(lg, "scale", 2, f, k)
        bdz = (root.z - TOP) if u >= U_LAND else 0.0
        bk.put(button, "location", 2, f, b0.z + bdz)
        s_p = 2.6 * (1 - (1 - min(max((u - U_FREEZE) / 0.6, 0.0), 1.0)) ** 3) if u >= U_FREEZE else 0.0
        for i in range(3): bk.put(pulse, "scale", i, f, max(s_p, 1e-4))
        log["t"].append(t); log["root_z"].append(root.z); log["crouch"].append(dl); log["antenna"].append(math.degrees(th)); log["pitch"].append(pt)
    else:
        for i in range(3): bk.put(robot, "scale", i, f, 0.0)
        for i in range(3): bk.put(pulse, "scale", i, f, 1e-4)
    # カメラ：A＝通路の奥から主人公へゆっくり寄る、C＝時間が止まった後にゆっくり寄る（古い座標で計算 → 今の座標へ）
    if t < T_B:
        s = mj(t, 0.0, T_B)
        pos = Vector((-1.30, -2.70, 1.42)).lerp(Vector((-1.36, -1.05, 1.24)), s); tgt = Vector((-0.55, 2.40, 1.00)).lerp(Vector((-0.30, 1.00, 1.02)), s)
        aim_cam(camA, pos, tgt, 24 + 2 * s); camA.data.dof.focus_distance = (hp0 - camA.location).length
        for i in range(3): bk.put(camA, "location", i, f, camA.location[i]); bk.put(camA, "rotation_euler", i, f, camA.rotation_euler[i])
        bk.put(camA.data, "lens", 0, f, camA.data.lens); bk.put(camA.data, "dof.focus_distance", 0, f, camA.data.dof.focus_distance)
    if t >= T_C - 1.0 / FPS:
        s = mj(t, T_FREEZE + 1.0, 4.0)
        tgt0 = Vector((b0.x + 0.25, b0.y + 0.25, 0.44)); pos = cam_c_pos.lerp(tgt0 + (cam_c_pos - tgt0) * 0.72, s)
        aim_cam(camC, to_w(pos), to_w(tgt0.lerp(Vector((b0.x + 0.05, b0.y + 0.05, 0.50)), s)), 24)
        for i in range(3): bk.put(camC, "location", i, f, camC.location[i]); bk.put(camC, "rotation_euler", i, f, camC.rotation_euler[i])
    # 光
    if t < T_B:
        st = dict(sun=8.5, key=260.0, fill=80.0, win=90.0, world=0.15, exp=0.0, spot=0.0, haze=0.0, glow=0.0)
    elif t < T_C:
        c = mj(t, T_DROP_G + 0.15, 0.5)
        st = dict(sun=8.5 + (2.0 - 8.5) * c, key=260 + (55 - 260) * c, fill=80 + (20 - 80) * c, win=90 + (22 - 90) * c, world=0.15 + (0.05 - 0.15) * c,
                  exp=-0.45 * c, spot=180.0 * c, haze=0.02 * c, glow=0.0)
    else:
        st = dict(sun=2.4, key=60.0, fill=22.0, win=25.0, world=0.05, exp=-0.45, spot=200.0, haze=0.025, glow=45.0 * mj(t, T_FREEZE, 0.3))
    for ob_, v_ in ((sun, "sun"), (key, "key"), (fill, "fill"), (win, "win"), (spot, "spot"), (glow, "glow")):
        bk.put(ob_.data, "energy", 0, f, st[v_])
    bk.put(scene, "view_settings.exposure", 0, f, st["exp"])
    bk.put(WN, 'nodes["Background"].inputs[1].default_value', 0, f, st["world"])
    bk.put(HN, 'nodes["Volume Scatter"].inputs["Density"].default_value', 0, f, st["haze"])
    if t < T_C:   # スポットは主人公へ（天井の下から）
        sp_loc = Vector((hp0.x - 0.75, hp0.y + 0.30, 2.18)); sp_tgt = Vector((hp0.x, hp0.y, hp0.z - 0.30)); col = kelvin(7000)
    else:         # まるロボとボタンへ
        sp_loc = to_w((b0.x - 0.3, b0.y - 0.5, 2.9)); sp_tgt = to_w((b0.x, b0.y, 0.3)); col = kelvin(3500)
    spot.location = sp_loc; aim(spot, sp_tgt); spot.data.color = col
    for i in range(3):
        bk.put(spot, "location", i, f, spot.location[i]); bk.put(spot, "rotation_euler", i, f, spot.rotation_euler[i]); bk.put(spot.data, "color", i, f, col[i])
bk.write(interp="LINEAR")
# 見せる／隠す：ボタンとほこりはショットCだけ
for n_ in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
    if n_ in O:
        ob_ = O[n_]
        for fr_, hide_ in ((1, True), (int(T_C * FPS) + 1, False)):
            ob_.hide_render = hide_; ob_.keyframe_insert("hide_render", frame=fr_)
for fr_, hide_ in ((1, True), (int(T_C * FPS) + 1, False)):
    dust.hide_render = hide_; dust.keyframe_insert("hide_render", frame=fr_)
for fr_, hide_ in ((1, True), (int(T_DROP_G * FPS), False), (int(T_C * FPS) + 1, True)):   # かすみは主人公にスポットが当たる間だけ（ほかは計算しない＝速い）
    haze.hide_render = hide_; haze.keyframe_insert("hide_render", frame=fr_)
if robot.animation_data and robot.animation_data.action:
    for fc in robot.animation_data.action.fcurves:
        if fc.data_path == "scale":
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT" if kp.co[0] <= int(T_C * FPS) + 1 else "LINEAR"
json.dump(dict(log, T_B=T_B, T_C=T_C, T_DROP=T_DROP_G, T_FREEZE=T_FREEZE, T_LAND=T_C + U_LAND, T_TAKE=T_C + U_TAKE, V_IMPACT=V_IMPACT,
               T_PRESS=T_B + 4.42, T_TURN_CAM=T_C + U_FREEZE + 0.6), open(os.path.join(A.out, "opening_log.json"), "w", encoding="utf-8"))
print("BAKED", round(time.time() - t0, 1), flush=True)
scene.render.use_motion_blur = bool(A.blur); scene.render.motion_blur_shutter = 0.5
scene.render.image_settings.file_format = "PNG"; scene.render.use_overwrite = False; scene.render.use_placeholder = True
scene.render.filepath = os.path.join(A.out, "frames", "f_")
scene.frame_start, scene.frame_end = f0, min(f1, N)
if f0 == 1: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "opening_pict.blend"))
if A.dry:
    for fr in [int(x) for x in A.dry_frames.split(",")]:
        scene.frame_set(fr); scene.render.filepath = os.path.join(A.out, f"check_{fr:03d}.png"); bpy.ops.render.render(write_still=True)
        print("CHECK", fr, round(time.time() - t0, 1), flush=True)
else:
    if A.video:      # PC用：Blenderから直接 mp4（H.264）で書き出す（音と字幕はあとで付ける）
        scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
        ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "HIGH"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
        scene.render.use_overwrite = True; scene.render.use_placeholder = False
        scene.render.filepath = os.path.join(A.out, "opening_pict_")
    bpy.ops.render.render(animation=True)
print("SEQ DONE", round(time.time() - t0, 1), flush=True)
