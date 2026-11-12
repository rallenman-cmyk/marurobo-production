# まるロボの動きの見本リール：story.blend のまるロボを、何もないスタジオで動かす（動きの部品集の見本）
# 使い方: blender -b story.blend --python maru_reel.py -- --out DIR [--frames A:B] [--res W H] [--samples N] [--engine eevee|workbench] [--still T,T,..]
import bpy, bmesh, sys, os, math, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from mathutils import Vector, Matrix, Euler
import marumotion as mm, marurig as mr
from maru_reel_plan import reel_plan, extra_plan, PLATFORM, DOCK, PEDESTAL

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/maru_reel"); ap.add_argument("--frames", default="")
ap.add_argument("--res", nargs=2, type=int, default=[640, 360]); ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--engine", default="eevee"); ap.add_argument("--still", default=""); ap.add_argument("--save", action="store_true")
ap.add_argument("--plan", default="main", help="main＝全部の動き、extra＝追加の動き（走る・首をかしげる・紹介する）")
ap.add_argument("--video", type=int, default=0, help="1＝連番ではなく mp4（H.264）で書き出す（PC用。字幕と電子音はあとで付ける）")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A.out, exist_ok=True)
FPS = 24
scene = bpy.context.scene; O = bpy.data.objects; M = bpy.data.materials


def kelvin(k):
    t = k / 100.0
    if t <= 66: r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else: r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def link(ob): scene.collection.objects.link(ob); return ob


def mat(name, rgb, rough=0.5, metal=0.0):
    m = M.new(name); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    return m


def box(name, size, loc, m, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free(); ob = link(O.new(name, me)); ob.location = loc; me.materials.append(m)
    if bevel > 0:
        b = ob.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    return ob


def cyl(name, r, depth, loc, rot, m, seg=24):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    bm.to_mesh(me); bm.free(); ob = link(O.new(name, me)); ob.location = loc; ob.rotation_euler = rot; me.materials.append(m)
    for f in me.polygons: f.use_smooth = True
    return ob


# ---------------------------------------------------------------- まるロボだけ残す
maru = O["Maru"]; keep = set(mr.hier(maru))
for ob in list(O):
    if ob not in keep: O.remove(ob, do_unlink=True)
for coll in (bpy.data.materials, bpy.data.worlds):
    for idb in coll:
        if getattr(idb, "animation_data", None): idb.animation_data_clear()
        nt = getattr(idb, "node_tree", None)
        if nt and nt.animation_data: nt.animation_data_clear()
scene.frame_set(1)

# ---------------------------------------------------------------- スタジオ：床（0.5m の目盛り）、背景、光
floor_m = M.new("Studio floor"); floor_m.use_nodes = True; nt = floor_m.node_tree; bs = nt.nodes["Principled BSDF"]
bs.inputs["Roughness"].default_value = 0.65
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
def grid_axis(sock):
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 2.0; nt.links.new(sock, mul.inputs[0])
    fr_ = nt.nodes.new("ShaderNodeMath"); fr_.operation = "PINGPONG"; fr_.inputs[1].default_value = 0.5; nt.links.new(mul.outputs[0], fr_.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.012; nt.links.new(fr_.outputs[0], lt.inputs[0])
    return lt.outputs[0]
mx_ = nt.nodes.new("ShaderNodeMath"); mx_.operation = "MAXIMUM"; nt.links.new(grid_axis(sep.outputs[0]), mx_.inputs[0]); nt.links.new(grid_axis(sep.outputs[1]), mx_.inputs[1])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; nt.links.new(mx_.outputs[0], mix.inputs[0])
mix.inputs[6].default_value = (0.62, 0.61, 0.58, 1); mix.inputs[7].default_value = (0.50, 0.49, 0.47, 1); nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
me = bpy.data.meshes.new("Floor"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60.0); bm.to_mesh(me); bm.free()
floor = link(O.new("Floor", me)); me.materials.append(floor_m)
w = bpy.data.worlds.new("Studio"); w.use_nodes = True; scene.world = w
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.80, 0.80, 0.81, 1); bg.inputs[1].default_value = 0.85


def light(name, kind, energy, color, rot=None, loc=(0, 0, 0), size=None):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ob = link(O.new(name, ld)); ob.location = loc
    if rot is not None: ob.rotation_euler = Vector(rot).normalized().to_track_quat("Z", "Y").to_euler()
    if size is not None:
        if kind == "SUN": ld.angle = math.radians(size)
        elif kind == "AREA": ld.size = size
        else: ld.shadow_soft_size = size
    return ob
light("Key", "SUN", 3.2, kelvin(5400), rot=(-0.50, -0.62, 0.78), size=4.0)
light("Fill", "SUN", 0.9, kelvin(7000), rot=(0.75, -0.35, 0.45), size=12.0).data.use_shadow = False
light("Rim", "SUN", 1.6, kelvin(6200), rot=(0.25, 0.85, 0.50), size=3.0)

# ---------------------------------------------------------------- 小道具：跳び乗る台、受け取るローラーの台（main）／紹介する物（extra）
plan = reel_plan() if A.plan == "main" else extra_plan()
dock = []
if A.plan == "main":
    wood = mat("Platform", (0.50, 0.38, 0.27), 0.55); steel = mat("Dock steel", (0.36, 0.38, 0.40), 0.4, 0.6); roller_m = mat("Roller", (0.75, 0.76, 0.78), 0.25, 1.0)
    cx, cy = PLATFORM["center"]; sx, sy = PLATFORM["size"]; ph = PLATFORM["height"]
    box("Platform", (sx, sy, ph), (cx, cy, ph / 2), wood, bevel=0.015)
    un = plan.unloads[0]; dk = DOCK
    bw = -mm.fwd(un["psi"]); side = mm.rgt(un["psi"]); c0 = np.array(un["pos"]) + bw * (dk["near"] + dk["depth"] / 2)
    yaw = math.atan2(bw[1], bw[0])
    top_z = dk["height"]
    def dk_obj(ob):
        ob.rotation_euler = (0, 0, yaw); dock.append(ob); return ob
    # 台の枠（上の面は 4cm）、ローラー 9本、奥の止め、脚 4本（ロボから離れた側に寄せる）
    frame = dk_obj(box("Dock top frame", (dk["depth"], dk["width"], 0.04), (c0[0], c0[1], top_z - 0.02 - 0.02), steel, bevel=0.005))
    for k in range(9):
        u = -dk["depth"] / 2 + 0.06 + k * (dk["depth"] - 0.12) / 8
        p_ = c0 + bw * u
        r = dk_obj(cyl("Dock roller %d" % k, 0.022, dk["width"] - 0.06, (p_[0], p_[1], top_z - 0.022), (math.pi / 2, 0, 0), roller_m))
        r.rotation_euler = (math.pi / 2, 0, yaw)                  # ローラーの軸は台の横向き
    pl = c0 + bw * (dk["depth"] / 2 - 0.02)
    dk_obj(box("Dock lip", (0.04, dk["width"], 0.12), (pl[0], pl[1], top_z + 0.04), steel))
    for su in (-1, 1):
        for sw in (-0.42, 0.45):
            pq = c0 + bw * sw * dk["depth"] + side * su * (dk["width"] / 2 - 0.05)
            dk_obj(box("Dock leg", (0.05, 0.05, top_z - 0.04), (pq[0], pq[1], (top_z - 0.04) / 2), steel))


else:
    ped_m = mat("Pedestal", (0.10, 0.11, 0.12), 0.35); bud_m = mat("Presented earbud", (0.92, 0.93, 0.95), 0.22)
    px, py = PEDESTAL["pos"]; phh = PEDESTAL["height"]
    cyl("Pedestal", 0.16, phh, (px, py, phh / 2), (0, 0, 0), ped_m, seg=40)
    me_ = bpy.data.meshes.new("Earbud"); bm_ = bmesh.new(); bmesh.ops.create_uvsphere(bm_, u_segments=32, v_segments=16, radius=0.07); bm_.to_mesh(me_); bm_.free()
    bud = link(O.new("Earbud", me_)); bud.location = (px, py, phh + 0.07); bud.scale = (1.0, 0.8, 0.85); me_.materials.append(bud_m)
    for f_ in me_.polygons: f_.use_smooth = True
    cyl("Earbud stem", 0.022, 0.12, (px + 0.03, py, phh + 0.04), (0.0, math.radians(-35), 0.0), bud_m, seg=20)

# ---------------------------------------------------------------- まるロボを動かす
frames = mm.simulate(plan, fps=FPS)
N = len(frames)
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
rig = mr.MaruRig(maru); bk = mr.Baker()
for i, fr in enumerate(frames): rig.apply(fr, i + 1, bk)
# 受け取る台は荷物の場面から
t_cut = plan.cuts[0] if plan.cuts else 0.0
f_cut = int(round(t_cut * FPS)) + 1
for ob in dock:
    for f, v in ((1, 1.0), (max(f_cut - 1, 1), 1.0), (f_cut, 0.0)):
        bk.put(ob, "hide_render", 0, f, v); bk.put(ob, "hide_viewport", 0, f, v)

# ---------------------------------------------------------------- カメラ：まるロボを追う（場面ごとの向き・距離、なめらかに移る）
cam_d = bpy.data.cameras.new("Reel camera"); cam = link(O.new("Reel camera", cam_d)); scene.camera = cam
cam_d.sensor_width = 36; cam_d.clip_end = 100
PRESET = {"present": (-4.0, 4.3, 1.05, 40.0, 0.80), "close": (-24.0, 3.9, 1.10, 40.0, 0.92), "side": (0.0, 4.8, 0.90, 35.0, 0.85), "turn": (-20.0, 4.0, 1.05, 38.0, 0.90),
          "jump": (-12.0, 5.4, 1.15, 35.0, 0.95), "unload": (62.0, 4.6, 1.50, 35.0, 1.05)}       # 向き・距離・カメラの高さ・レンズ・見る高さ
def preset_at(t):
    key = "close"
    for a0, a1, txt in plan.labels:
        if a0 - 0.6 <= t <= a1:
            if txt.startswith(("歩く", "急ぎ足", "荷物を運ぶ", "走る")): key = "side"
            elif txt.startswith(("その場で", "受け取る")): key = "turn"
            elif txt.startswith(("台に跳び", "跳び降り")): key = "jump"
            elif txt.startswith("荷物を後ろ"): key = "unload"
            elif txt.startswith("紹介する"): key = "present"
            else: key = "close"
    return np.array(PRESET[key])
tgt = None; par = None; cams = []
for i, fr in enumerate(frames):
    t = fr["t"]; r = np.array(fr["root"]); z_g = min(f["ankle"][2] for f in fr["feet"]) - mm.SOLE
    want_p = preset_at(t); want_t = np.array([r[0], r[1], max(z_g, 0.0)])
    want_t[:2] += mm.fwd(fr["psi"]) * fr["v"] * 0.45            # 速く動くときは、遅れの分だけ先を見る
    if A.plan == "extra" and any(a0 - 0.6 <= t <= a1 and tx.startswith("紹介する") for a0, a1, tx in plan.labels):
        want_t[:2] += 0.45 * (np.array(PEDESTAL["pos"]) - r[:2])     # 紹介する間は、ロボと物の間を見る
    cut = any(abs(t - tc) < 0.5 / FPS for tc in plan.cuts)
    if tgt is None or cut: tgt = want_t.copy(); par = want_p.copy()
    else:
        tgt += (want_t - tgt) * (1 - math.exp(-(1 / FPS) / 0.45)); par += (want_p - par) * (1 - math.exp(-(1 / FPS) / 0.8))
    az, dist, hgt, lens, th = par
    a = math.radians(az); look = tgt + np.array([0, 0, th]); pos = tgt + np.array([math.sin(a) * dist, -math.cos(a) * dist, hgt])
    q = (Vector(look) - Vector(pos)).to_track_quat("-Z", "Y")
    for k in range(3): bk.put(cam, "location", k, i + 1, pos[k])
    cam.rotation_mode = "QUATERNION"
    for k in range(4): bk.put(cam, "rotation_quaternion", k, i + 1, q[k])
    bk.put(cam_d, "lens", 0, i + 1, lens)
    if i == 0: cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
    bk.put(cam_d, "dof.focus_distance", 0, i + 1, float(np.linalg.norm(pos - (r + np.array([0, 0, 0.7])))))
bk.write()

# ---------------------------------------------------------------- 描画の設定と、字幕・効果音のための記録
scene.render.resolution_x, scene.render.resolution_y = A.res; scene.render.resolution_percentage = 100
if A.engine == "workbench":
    scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
else:
    scene.render.engine = "BLENDER_EEVEE_NEXT"; scene.eevee.taa_render_samples = A.samples
    scene.eevee.use_shadows = True; scene.eevee.shadow_resolution_scale = 0.75
    try: scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
    except Exception: pass
scene.render.image_settings.file_format = "PNG"
json.dump(dict(fps=FPS, frames=N, labels=[[round(a, 3), round(b, 3), t] for a, b, t in plan.labels], events=plan.events, cuts=plan.cuts),
          open(os.path.join(A.out, "reel_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, default=float)
print("REEL frames", N, "seconds", round(N / FPS, 2), flush=True)
if A.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, "maru_reel.blend"))
if A.still:
    for tt in A.still.split(","):
        f = int(round(float(tt) * FPS)) + 1; scene.frame_set(f)
        scene.render.filepath = os.path.join(A.out, "still_%05.2f.png" % float(tt)); bpy.ops.render.render(write_still=True)
        print("STILL", tt, flush=True)
elif A.frames:
    f0, f1 = [int(x) for x in A.frames.split(":")]
    scene.frame_start, scene.frame_end = f0, min(f1, N)
    scene.render.filepath = os.path.join(A.out, "frames", "f_")
    if A.video:
        scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
        ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "HIGH"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
        scene.render.filepath = os.path.join(A.out, "maru_reel_")
    bpy.ops.render.render(animation=True)
    print("SEQ DONE", flush=True)
