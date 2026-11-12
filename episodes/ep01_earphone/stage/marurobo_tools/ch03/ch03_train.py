# 第3章の電車の場面（C1・C2・C12）：冒頭の電車を、時間が止まった最後のコマのまま組み、カメラだけを置き直す
#   C1（1:21〜1:32）スマホの画面を手前、耳のイヤホンを奥に。ピントを送る
#   C2（1:32〜1:40）止まった電波の波面：スマホのアンテナから 12.3cm おき（2.44GHz の波長）の球面。光らず、向こうを少しゆがめるだけ
#                   振幅は距離に反比例（球面波）なので、遠い波面ほど弱い。「目に見えません」で消える
#   C12（2:30〜2:34）耳元とスマホの画面に戻る
# 使い方: blender -b --factory-startup --python ch03_train.py -- --out DIR [--still T,T,..（章の中の秒。0＝本編81.0）] [--res W H] [--samples N] [--blend maru_opening.blend]
import bpy, sys, os, math, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); HUMAN = os.path.abspath(os.path.join(HERE, "..", "human"))
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="/tmp/ch03_train"); ap.add_argument("--still", default="1.0,6.0,10.0,13.0,17.5,70.0")
ap.add_argument("--res", nargs=2, type=int, default=[640, 360]); ap.add_argument("--samples", type=int, default=16); ap.add_argument("--blend", default="")
ap.add_argument("--probe", type=int, default=0, help="1＝主人公・スマホ・イヤホンの位置だけ出して終わる")
ap.add_argument("--anim", default="", help="カメラが動く連番：章の中の秒の範囲 A:B（コマ番号＝秒×24）。例 0:19.2 や 68.8:73.0。frames_train/ に描く")
ap.add_argument("--share", type=int, default=0, help="1＝何本かで同じ範囲を描く：描き始めに空のファイルを置き、ほかの描き手に飛ばしてもらう（止まったら空のファイルを消してから描き直す）")
ap.add_argument("--rev", type=int, default=0, help="1＝連番を後ろから描く（手伝いの2本目が、同じ範囲を反対側から描く）")
ap.add_argument("--tag", default="", help="カメラの記録の名前に付ける印（同じ範囲を2本で描くとき、記録が上書きされないように）")
ap.add_argument("--survey", type=int, default=0, help="1＝主人公の止まった姿を、前・横・上から確かめる絵だけ描く")
ap.add_argument("--acts", type=int, default=1, help="1＝第1・2章と同じく、時間が止まる瞬間の乗客の小さな動き（--acts 1）を入れて組む。第2章の最後の止まった姿と同じになる")
ap.add_argument("--from_ch02", type=int, default=1, help="1＝第1・2章の電車（乗客を増やした車内・81秒で止まった姿）から組む。0＝冒頭22秒の試作から")
A3 = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
os.makedirs(A3.out, exist_ok=True)

# ---------------------------------------------------------------- 冒頭の電車を組む（描かない）。止まった最後のコマへ
sys.argv = [sys.argv[0], "--", "--out", os.path.join(A3.out, "opening_build"), "--dry", "2", "--frames", "2:2", "--res", str(A3.res[0]), str(A3.res[1]),
            "--samples", str(A3.samples), "--blur", "0"] + (["--blend", A3.blend] if A3.blend else []) + \
           (["--seq", "ch0102_seq.py", "--crowd", "1", "--world_len", "1450", "--acts", str(A3.acts)] if A3.from_ch02 else [])   # 第2章で時間が止まった姿（81秒の最後のコマ）から
G = {"__file__": os.path.join(HUMAN, "opening_phys.py"), "__name__": "__main__"}
exec(compile(open(G["__file__"], encoding="utf-8").read(), G["__file__"], "exec"), G)
import numpy as np
from mathutils import Vector, Matrix
scene = bpy.context.scene; O = bpy.data.objects
N_OPEN = int(round(G["T_END"] * 24)); scene.frame_set(N_OPEN)            # 止まった最後のコマ（第1・2章なら 1944 コマ目）
hero = G["P"]["H"]; rig = hero["rig"]
bpy.context.view_layer.update()
ph = hero["phone"]; M_ph = ph.matrix_world.copy()
scr = next((c for c in ph.children if "screen" in c.name), None)
C_ph = M_ph.translation.copy(); n_scr = (M_ph.to_3x3() @ Vector((0, 0, 1))).normalized(); up_ph = (M_ph.to_3x3() @ Vector((0, 1, 0))).normalized()
ANT = C_ph + up_ph * 0.075 * 1.15                                 # アンテナ：スマホの上の端（スマホの長さ0.150×1.15倍の半分）
head_c, bud = G["hero_points"]()
print("TRAIN phone", tuple(round(v, 3) for v in C_ph), "screen normal", tuple(round(v, 2) for v in n_scr), "up", tuple(round(v, 2) for v in up_ph),
      "bud", tuple(round(v, 3) for v in bud), "head", tuple(round(v, 3) for v in head_c), "ant-bud %.3f m" % (bud - ANT).length, flush=True)
if A3.probe: sys.exit(0)

# ---------------------------------------------------------------- 電波の波面（C2）：止まった球面波。光らない屈折だけ（IOR がわずかに1からずれる）
LAM = 299792458.0 / 2.44e9                                        # 0.1229 m
WF = []; wm_list = []
for k in range(6):
    r = 0.045 + k * LAM
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r, location=ANT)
    sp = bpy.context.active_object; sp.name = "Wavefront %d" % k
    for f_ in sp.data.polygons: f_.use_smooth = True
    m = bpy.data.materials.new("Wavefront %d" % k); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (1, 1, 1, 1); bs.inputs["Roughness"].default_value = 0.0
    bs.inputs["Transmission Weight"].default_value = 1.0; bs.inputs["IOR"].default_value = 1.0
    try: m.surface_render_method = "DITHERED"
    except Exception: pass
    try: m.use_raytrace_refraction = True; m.thickness_mode = "SLAB"
    except Exception: pass
    sp.data.materials.append(m); sp.visible_shadow = False; WF.append((sp, bs, r)); wm_list.append(m)


def wave_amount(a):
    """a：0＝見えない、1＝見える。振幅は 1/r（いちばん内側を基準）。IOR のずれは最大 0.035"""
    for sp, bs, r in WF:
        d = 0.06 * a * (0.045 + LAM * 0.5) / (r + LAM * 0.5)
        bs.inputs["IOR"].default_value = 1.0 + d; sp.hide_render = a < 1e-3


wave_amount(0.0)
ee = scene.eevee
try: ee.use_raytracing = True; ee.ray_tracing_options.resolution_scale = "1"; ee.ray_tracing_method = "SCREEN"
except Exception: pass

# ---------------------------------------------------------------- カメラ（C1・C2・C12）。時間は止まっている：場面は N_OPEN のまま、カメラだけ動かす
cam_d = bpy.data.cameras.new("Ch03 train camera"); cam = O.new("Ch03 train camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
scene.timeline_markers.clear()                                     # 冒頭のカメラの切り替えの印を消す
cam_d.sensor_width = 36; cam_d.clip_start = 0.02; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.2
hz = Vector((0, 0, 1)); side = (bud - C_ph); side.z = 0; side.normalize()
right = side.cross(hz).normalized()                                   # スマホ→耳の横向き


def smooth(u): u = max(0.0, min(1.0, u)); return u * u * u * (10 - 15 * u + 6 * u * u)


def shot(t):
    """章の中の秒 → (位置, 見る点, レンズ, ピントの点, 名前)。止まった主人公：右手は耳のイヤホン、左手にスマホ（画面は顔へ向く）
    C1：スマホの画面のアップ（左上から望遠）→ 耳のイヤホンのアップ（正面右から）→ 画面（音楽のデータ）。C12 は画面のアップ"""
    H = head_c; mid = C_ph.lerp(bud, 0.45)
    side_l = Vector((0, -1, 0)); d_scr = (n_scr * math.cos(math.radians(45)) + side_l * math.sin(math.radians(45))).normalized()
    if 8.3 <= t < 11.0:                                               # 「つまり、音楽のデータです」：画面の上のまとまりの帯に寄る（望遠）
        bar = C_ph + up_ph * 0.063 + n_scr * 0.002; u = smooth((t - 8.3) / 2.7)
        return C_ph + d_scr * (0.95 - 0.05 * u), bar, 150.0, bar, "C1"
    if t < 2.85 or t >= 68.75:                                        # 画面のアップ（C12 の最初のコマは 1651/24＝68.79 秒なので、68.8 より少し前から）
        t0 = 0.0 if t < 2.85 else 68.8
        u = smooth((t - t0) / 3.0); base = C_ph + d_scr * (0.95 - 0.08 * u)
        return base, C_ph + up_ph * 0.01, 85.0, C_ph, ("C1" if t < 11.0 else "C12")
    if t < 8.3:                                                       # 耳のイヤホンのアップ（右手が触れたまま止まっている）
        u = smooth((t - 2.85) / 5.4); base = bud + Vector((-0.72 + 0.06 * u, 0.30, 0.04))
        return base, bud + Vector((-0.04, -0.05, -0.03)), 50.0, bud, "C1"
    u = smooth((t - 11.0) / 8.2)                                      # C2：引いて、スマホのアンテナから広がる止まった波面
    base = H + Vector((-1.35, -0.40 + 0.25 * u, 0.25 - 0.05 * u))
    return base, mid, 24.0, mid, "C2"


def place(t):
    p, tg, lens, fp, nm = shot(t)
    cam.location = p; cam.rotation_euler = (tg - p).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens; cam_d.dof.focus_distance = (fp - p).length
    a = 0.0
    if 11.0 <= t < 19.2:                                              # 「そのデータを、電波で送っています」で現れ、「目に見えません」で消える
        a = smooth((t - 11.6) / 1.0) * (1 - smooth((t - 16.8) / 1.6))
    wave_amount(a); return nm


scene.render.resolution_x, scene.render.resolution_y = A3.res; scene.render.image_settings.file_format = "PNG"
if A3.survey:
    wave_amount(0.0); cam_d.dof.use_dof = False
    for nm, off, lens in (("front", Vector((-1.7, 0.0, -0.1)), 30), ("right", Vector((-0.5, 1.4, 0.0)), 30), ("top", Vector((-0.25, 0.05, 1.3)), 24),
                          ("left", Vector((-0.6, -1.3, 0.05)), 30)):
        scene.frame_set(N_OPEN); p_ = head_c + off; cam.location = p_; tg = head_c.lerp(C_ph, 0.5)
        cam.rotation_euler = (tg - p_).to_track_quat("-Z", "Y").to_euler(); cam_d.lens = lens; scene.camera = cam
        scene.render.filepath = os.path.join(A3.out, "survey_%s.png" % nm); bpy.ops.render.render(write_still=True); print("SURVEY", nm, flush=True)
    sys.exit(0)
scene.render.use_placeholder = False; scene.render.use_overwrite = True
log3 = {"lambda": LAM, "antenna": list(ANT), "bud": list(bud), "phone": list(C_ph), "res": list(A3.res), "stills": {}}
# 主人公のスマホの画面：曲の進み具合の帯を「データのまとまり」に区切った画面（ch03_screen.py）に替えられる（"1.0:k3" のように指定）
scr_tex = None
if scr is not None and scr.active_material:
    scr_tex = next((n for n in scr.active_material.node_tree.nodes if n.bl_idname == "ShaderNodeTexImage"), None)
SCREENS = os.path.join(HERE, "screens")
STILLS = [x for x in A3.still.split(",") if x]
if A3.anim and A3.still == ap.get_default("still"): STILLS = []       # 連番を描くときは、静止画（初めの候補）は描かない
for spec in STILLS:
    tt = float(spec.split(":")[0]); kk = spec.split(":")[1] if ":" in spec else ""
    if scr_tex is not None and kk and os.path.exists(os.path.join(SCREENS, "music_%s.png" % kk)):
        scr_tex.image = bpy.data.images.load(os.path.join(SCREENS, "music_%s.png" % kk), check_existing=True)
    scene.frame_set(N_OPEN); nm = place(tt); scene.camera = cam; print("CAMERA", scene.camera.name, tuple(round(v, 2) for v in cam.location), flush=True)
    if nm == "C2": wave_amount(0.0)                                   # 波面は描いたあとの絵の上でゆがめる（ch03_assemble.py）。ここでは描かない
    fn = "train_%05.1f_%s%s.png" % (tt, nm, ("_" + kk) if kk else ""); scene.render.filepath = os.path.join(A3.out, fn); bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.update()
    log3["stills"][fn] = dict(t=tt, shot=nm, cam=[list(r) for r in cam.matrix_world], lens=cam_d.lens, sensor=cam_d.sensor_width)
    print("TRAIN STILL", tt, nm, flush=True)



def screen_state(t):
    """章の中の秒 → 主人公のスマホの画面（ch03_screen.py）。「音楽のデータ」で帯を区切る→01・02→03が光る。C2（電波）は03を送っている画面"""
    if 8.3 <= t < 9.1: return "k1"
    if 9.1 <= t < 9.9: return "k2"
    if 9.9 <= t < 19.2: return "k3"
    return "k0"


if A3.anim:                                                           # カメラが動く連番（止まった世界なので、動くのはカメラと画面の絵だけ）
    fd = os.path.join(A3.out, "frames_train"); os.makedirs(fd, exist_ok=True)
    a_, b_ = [float(x) for x in A3.anim.split(":")]
    idx = list(range(int(round(a_ * 24)), int(round(b_ * 24))))
    lp = os.path.join(A3.out, "train_frames_log_%04d%s.json" % (idx[0], ("_" + A3.tag) if A3.tag else ""))
    scene.frame_set(N_OPEN)                                            # 時間は止まっている：場面は一度だけ合わせ、コマごとにはカメラだけ動かす
    for i_ in (idx[::-1] if A3.rev else idx):
        tt = i_ / 24.0; fn = "t_%04d.png" % i_; fp = os.path.join(fd, fn)
        nm = place(tt); scene.camera = cam; bpy.context.view_layer.update()
        if nm == "C2": wave_amount(0.0)
        # カメラの記録は、ほかの描き手が描いたコマのぶんも残す（電波の波面を重ねるのに全コマ要る。途中で止まっても欠けない）
        log3["stills"][fn] = dict(t=tt, shot=nm, cam=[list(r) for r in cam.matrix_world], lens=cam_d.lens, sensor=cam_d.sensor_width)
        if os.path.exists(fp) and (A3.share or os.path.getsize(fp) > 0): continue
        if A3.share: open(fp, "wb").close()                            # 描いている印（空のファイル）。ほかの描き手はこのコマを飛ばす
        kk = screen_state(tt)
        if scr_tex is not None and os.path.exists(os.path.join(SCREENS, "music_%s.png" % kk)):
            scr_tex.image = bpy.data.images.load(os.path.join(SCREENS, "music_%s.png" % kk), check_existing=True)
        scene.render.filepath = fp; bpy.ops.render.render(write_still=True); bpy.context.view_layer.update()
        json.dump(log3, open(lp, "w", encoding="utf-8"), indent=0)     # 1コマごとに書く（止まっても、描けたコマの記録は残る）
        print("TRAIN FRAME", i_, nm, flush=True)
    json.dump(log3, open(lp, "w", encoding="utf-8"), indent=0)
else:
    json.dump(log3, open(os.path.join(A3.out, "train_log.json"), "w", encoding="utf-8"), indent=0)
