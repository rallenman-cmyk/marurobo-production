# opening_v2.py から exec される：主人公の動きテスト（8秒）。音が途切れる→反応→イヤホンに触れる
f0, f1 = [int(x) for x in A.frames.split(":")]
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, 192
T_END = 192 / FPS
tt, acc = motion.train_sway(T_END + 1, FPS, seed=3, rms=0.22)
sway = motion.pendulum_response(acc, FPS)          # 上半身の前後の揺れ（度）
log = dict(t=[], sway=[], reach=[], head=[], gaze=[], blink=[], wrist=[])
bk = hrig.Baker()
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45)
# 指先がイヤホンに届くよう、手首の目標を一度だけ補正（指の腹＝人さし指と中指の先の中点）
ex = {}; hero_anim.pose_at(hero, hero_anim.T_DROP + 2.0, 0.0, hero_bud_rest, ex)
rig = hero["rig"]; rig.fk()
tip = (rig.tail_pos("index_03.R") + rig.tail_pos("middle_03.R")) / 2
bud_now = rig.posed_point("head", hero_bud_rest)
hero["touch_fix"] = (bud_now + np.array([-0.006, -0.004, -0.010])) - tip
print("TOUCH_FIX", np.round(hero["touch_fix"], 3), flush=True)
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
for f in range(1, 193):
    t = (f - 1) / FPS
    ex = {}
    tl = hero_anim.pose_at(hero, t, float(sway[f - 1]), hero_bud_rest, ex)
    bk.pose(hero["rig"], f)
    if hero.get("mouth") is not None:
        bk.put(hero["mouth"].data.shape_keys, 'key_blocks["o"].value', 0, f, ex["mouth_o"])
        if "flat" in hero["mouth"].data.shape_keys.key_blocks: bk.put(hero["mouth"].data.shape_keys, 'key_blocks["flat"].value', 0, f, ex["mouth_flat"])
    if hero.get("dots"):
        for sd in ("L", "R"):
            sk = hero["objs"]["eye." + sd].data.shape_keys
            bk.put(sk, 'key_blocks["blink"].value', 0, f, ex["blink"]); bk.put(sk, 'key_blocks["wide"].value', 0, f, ex["wide"] * (1 - ex["blink"]))
    rg = hero["rig"]
    log.setdefault("hair", []).append([float(x) for x in np.degrees(hero.get("hair_st", {}).get("th", np.zeros(3)))])
    log["t"].append(t); log["sway"].append(float(sway[f - 1])); log["reach"].append(tl["reach"]); log["head"].append(tl["head"]); log["gaze"].append(tl["gaze"])
    log["wrist"].append([float(x) for x in rg.head_pos("hand.R")])
    log["blink"].append(max(motion.blink(t, tb) for tb in hero_anim.BLINKS))
    log.setdefault("torso", []).append(tl["torso"]); log.setdefault("breath", []).append(float(ex["breath"])); log.setdefault("nod", []).append(float(ex["nod"]))
    log.setdefault("mouth", []).append(float(ex["mouth_o"])); log.setdefault("brow", []).append(tl["brow"])
    for n, person in P.items():
        if n == "PASSENGER 00": continue
        people.base_pose(person, t, sway=float(sway[(f - 1 + 7 * hash(n) % 11) % len(sway)]) * 0.8)
        bk.pose(person["rig"], f)
        if person.get("dots"):
            for sd in ("L", "R"): bk.put(person["objs"]["eye." + sd].data.shape_keys, 'key_blocks["blink"].value', 0, f, person.get("_blink", 0.0))
bk.write()
print("BAKED", round(time.time() - t0, 1), flush=True)
# 光：A案（昼）→ 音が途切れた0.15秒後から0.5秒で C案（主人公だけに光）
hp, bud = hero_points()
spot.location = (hp.x - 0.6, hp.y - 0.4, 2.9); aim(spot, (hp.x, hp.y, hp.z - 0.3)); spot.data.color = kelvin(7000)
haze.hide_render = False
for f in range(1, 193):
    t = (f - 1) / FPS; c = motion.mj(t, hero_anim.T_DROP + 0.15, 0.5)
    sun.data.energy = 4.0 + (0.6 - 4.0) * c; ceil.data.energy = 900 + (120 - 900) * c; spot.data.energy = 260 * c
    scene.view_settings.exposure = -1.0 * c; vs.inputs["Density"].default_value = 0.035 * c
    for idb, path in ((sun.data, "energy"), (ceil.data, "energy"), (spot.data, "energy"), (scene.view_settings, "exposure")):
        idb.keyframe_insert(path, frame=f)
    vs.inputs["Density"].keyframe_insert("default_value", frame=f)
for fc_owner in (sun.data, ceil.data, spot.data):
    for fc in fc_owner.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
pause_parts(False); dust.hide_render = True
# カメラ：主人公の右前から（耳・右手・スマホが入る）
# 主人公の正面（−X）から右へ35°・目より少し上から。頭〜手元（腰の上）が入る
_az = math.radians(35.0); _d = float(os.environ.get("OP2_CAMD", "2.55")); _tz = float(os.environ.get("OP2_CAMTZ", "-0.26"))
set_cam((hp.x - _d * math.cos(_az), hp.y + _d * math.sin(_az), hp.z + 0.10), (hp.x - 0.10, hp.y + 0.02, hp.z + _tz), 40, dof=(hp, 2.8))
scene.render.use_motion_blur = bool(A.blur); scene.render.motion_blur_shutter = 0.5
import json
json.dump(log, open(os.path.join(A.out, "hero_motion_log.json"), "w"))
scene.render.image_settings.file_format = "PNG"; scene.render.use_overwrite = False; scene.render.use_placeholder = True
scene.render.filepath = os.path.join(A.out, "frames", "f_")
if getattr(A, "video", 0):   # PC用：動画ファイル（H.264）を直接書き出す
    scene.render.image_settings.file_format = "FFMPEG"; scene.render.ffmpeg.format = "MPEG4"; scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"; scene.render.use_overwrite = True; scene.render.use_placeholder = False
    scene.render.filepath = os.path.join(A.out, "hero_motion_")
scene.frame_start, scene.frame_end = f0, f1
if os.environ.get("OP2_DRY") == "1":
    for f in (1, 80, 110, 130):
        scene.frame_set(f); scene.render.filepath = os.path.join(A.out, f"check_{f:03d}.png"); bpy.ops.render.render(write_still=True)
        print("CHECK", f, flush=True)
else:
    bpy.ops.render.render(animation=True)
print("ANIM DONE", round(time.time() - t0, 1), flush=True)
