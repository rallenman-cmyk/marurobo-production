# まとめの電車の場面（本編 17:58.7〜18:15）の動き：opening_phys.py から exec される
#   使い方: blender -b --factory-startup --python opening_phys.py -- --seq summary_seq.py --crowd 1 --world_len 1450 --acts 1 --out DIR
#           [--frames 1945:2340]（省略時もこの範囲）[--dry 1 --dry_frames ...] [--video 1]
#   第1・2章（ch0102_seq.py）と同じ電車・同じ乗客・同じ動きを、時間が止まる所までまったく同じ計算でたどり（止まった姿がぴたりと同じ）、
#   その先に 16.5秒を足す（この台本の秒 81.0 ＝ 本編 1078.747秒）：
#   M8  止まった車内（引き）。まるロボがこちらを向いて、おじぎ　　　　　　　　　　　「お待たせしました。」
#   M9  ボタンの左前の低い所から。まるロボがボタンにもう一度跳び乗る → 0.1秒後に時間が動き出す（第2章の逆）　「時間を、元に戻しましょう。」
#       ・世界の時刻は、止まった瞬間の時刻から、テープが回り出すように 0.5秒で速さ 0→1 に戻る（景色・つり革・ほこり・乗客・曲が同じ時計で）
#       ・光の輪はボタンへ縮んで消え、色が戻る
#   M10 右の列を斜めに（主人公が手前）。曲が同じ曲のサビに入り、主人公は一人で第1章の振り付けを踊る　「……この人は、まだこの曲でした。」
#   M11 主人公の正面（両隣が見える）。隣の人がちらっと見る → 決めポーズで、もう一度見る　「ちなみに、電車の中では、こんなに踊ってはいけませんよ。」
#   ・主人公の踊りは、曲の位置（第1章の秒）で dance.py の振り付けを引く。曲の静かな部分は 8拍のくり返しなので、
#     止まった位置から曲を進めても、サビの頭（21.798秒）が M10 の頭（まとめの 7.551秒）に来るよう、戻る位置を選べる（音の継ぎ目は出ない）
import json
sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import marumotion as mm, marurig as mr
import dance
T2 = 81.0                                    # 第2章の終わり＝まとめの電車の場面の頭
EP0 = 1078.747                               # そのときの本編の秒
D_SUM = 16.5
T_END = T2 + D_SUM
N = int(round(T_END * FPS))
F_SUM0 = int(round(T2 * FPS)) + 1            # 描く最初のコマ（1945）
if A.frames == "1:528": A.frames = "%d:%d" % (F_SUM0, N)
f0, f1 = [int(x) for x in A.frames.split(":")]
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
mj = motion.mj
def S_(s): return T2 + s                     # まとめの秒 → この台本の秒

# ---------------------------------------------------------------- 時刻（第1・2章と同じ）
T_DROP = 38.20
T_BACK = 38.80
T_SAME0, T_SAME1 = 21.75, dance.T_FANT1
T_M9, T_M10, T_M11 = S_(1.739), S_(7.551), S_(10.828)      # 声の頭（「時間を、」「……この人は、」「ちなみに、」）
CUTS = [(0.0, "K"), (T2, "M8"), (T_M9, "M9"), (T_M10, "M10"), (T_M11, "M11")]


def cut_of(t):
    nm = CUTS[0][1]
    for a_, n_ in CUTS:
        if t >= a_: nm = n_
    return nm


# ---------------------------------------------------------------- 一時停止ボタン（第1・2章と同じ所）
B_NEW2 = Vector((-1.00, -0.25, 0.0))
oldw.matrix_world = Matrix.Translation(B_NEW2) @ Matrix.Rotation(PHI, 4, "Z") @ Matrix.Scale(1.0 / S, 4) @ Matrix.Translation(-B_OLD)
bpy.context.view_layer.update()
E = oldw.matrix_world.copy(); Einv = E.inverted()
BTN = Vector((B_NEW2.x, B_NEW2.y, 0.0)); TOP_W = 0.178 / S
glow.location = to_w((0.14, -3.65, 0.35))

# ---------------------------------------------------------------- カメラの位置（まるロボがこちらを向くのに使うので先に決める）
M8_P0, M8_P1 = Vector((-1.22, -2.62, 1.40)), Vector((-1.18, -2.28, 1.34))     # 通路の奥・立った人の目の高さから、ゆっくり前へ（止まった世界でカメラだけが動く）
M8_T0, M8_T1 = Vector((-0.86, -0.20, 0.58)), Vector((-0.86, -0.26, 0.52))
# M9：まるロボ（R_SIDE）とボタンを結ぶ線の横（通路の後ろ側）の低い所から。跳ぶ前の所とボタンが画面の左右に分かれて見える
_mid9 = Vector(((-0.80 + BTN.x) / 2, (-0.37 + BTN.y) / 2, 0.0)); _n9 = Vector((0.12, 0.20, 0.0)).normalized()
CAM9 = _mid9 - _n9 * 1.35 + Vector((0, 0, 0.30))
TG9_0 = _mid9 + Vector((0, 0, 0.24)); TG9_1 = BTN + Vector((0.0, 0.0, 0.34))
TG9_2 = Vector((-0.78, -0.16, 0.50))                                              # 動き出したあと：まるロボが見上げる先（主人公のひざと手）へ少し上げる

# ---------------------------------------------------------------- まるロボ：第1・2章と同じ計画をたどり、その先を足す
KS = 1.0 / 3.0; SQK = math.sqrt(KS)
RW = link(O.new("ROBOT WORLD", None)); RW.matrix_world = Matrix.Scale(KS, 4)
robot.parent = RW; robot.matrix_parent_inverse = Matrix.Identity(4); robot.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
def Bt(t_real): return t_real / SQK
def Bp(x, y): return (x / KS, y / KS)
def heading_to(src, dst): return math.degrees(math.atan2(-(dst[0] - src[0]), dst[1] - src[1]))
R_START = (BTN.x, -2.35); R_STOP = (BTN.x, BTN.y - 0.40); R_HERO = (-0.80, -0.47)
hp0, bud0 = hero_points()
PHONE_W = tuple(float(v) for v in hero["phone"].matrix_world.translation)
plan = mm.Plan(pos=Bp(*R_START), heading=0.0, seed=5)
plan.idle(Bt(50.15), shifts=False, glance=False)
plan.walk_to(Bp(*R_STOP), speed=mm.V_WALK, label="通路を歩いてくる")
t_stop = plan.t
def look_at(pl, src, dst, z_eye=0.27, hold=0.6, at=None):
    hd = heading_to(src, dst); yaw = (hd - math.degrees(pl._psi) + 180) % 360 - 180
    pitch = math.degrees(math.atan2(dst[2] - z_eye, math.hypot(dst[0] - src[0], dst[1] - src[1])))
    pl.look(yaw=yaw, pitch=pitch, hold=hold, at=at)
plan.idle(max(Bt(53.85) - plan.t, 0.05), shifts=False, glance=False)
look_at(plan, R_STOP, PHONE_W, hold=Bt(0.9) - 0.3, )
plan.idle(max(Bt(55.25) - plan.t, 0.05), shifts=False, glance=False)
plan.look(yaw=0.0, pitch=8.0, hold=0.4)
plan.idle(max(Bt(56.35) - plan.t, 0.05), shifts=False, glance=False)
plan.look(yaw=0.0, pitch=-14.0, hold=0.2)


def jump_plan(t_idle):
    q = mm.Plan(pos=Bp(*R_STOP), heading=0.0, seed=5); q.idle(t_idle, shifts=False, glance=False)
    q.jump_to(Bp(BTN.x, BTN.y), z1=TOP_W / KS); seg = [s_ for s_ in q.segs if isinstance(s_, mm.JumpSeg)][0]
    return seg.flights[0]["t1"] - t_idle
d_land = jump_plan(1.0)
T_LAND_B = Bt(59.45)
plan.idle(max(T_LAND_B - d_land - plan.t, 0.05), shifts=False, glance=False)
plan.jump_to(Bp(BTN.x, BTN.y), z1=TOP_W / KS, label="ボタンに跳び乗る")
seg_j = [s_ for s_ in plan.segs if isinstance(s_, mm.JumpSeg)][-1]
T_LAND = seg_j.flights[0]["t1"] * SQK; T_FREEZE = T_LAND + 0.10
CAM12 = (BTN.x - 0.62, BTN.y + 0.55)
plan.idle(max(Bt(T_FREEZE + 0.55) - plan.t, 0.05), shifts=False, glance=False)
plan.turn_to(heading_to((BTN.x, BTN.y), CAM12))
plan.idle(max(Bt(68.95) - plan.t, 0.05), shifts=True, glance=True)
plan.jump_to(Bp(*R_HERO), z1=0.0, label="ボタンから降りる")
plan.turn_to(heading_to(R_HERO, PHONE_W))
T_SIDE = 77.9; R_SIDE = (R_HERO[0], R_HERO[1] + 0.10)
look_at(plan, R_HERO, PHONE_W, hold=max(Bt(T_SIDE) - plan.t - Bt(0.35), Bt(0.5)))
plan.back_to(Bp(*R_SIDE), step=0.20, sw=0.26, gap=0.06, look=False, label="スマホが見やすい所へ横に（4歩）")
look_at(plan, R_SIDE, PHONE_W, hold=Bt(0.26))                                          # 第2章では Bt(3.0)。まとめでは 81.0秒（描く頭）までに、こちらを向き終える
print("ROBOT end of ch2 plan at %.2f s" % (plan.t * SQK), flush=True)
# ---- ここから、まとめ（第1・2章の計画は上まで同じ）
plan.turn_to(heading_to(R_SIDE, (M8_P0.x, M8_P0.y)), label="こちら（カメラ）を向く")          # まとめの頭（M8）では、もうこちらを向いている
cam8_mid = (M8_P0 + M8_P1) * 0.5
plan.idle(max(Bt(S_(0.10)) - plan.t, 0.05), shifts=False, glance=False)
look_at(plan, R_SIDE, cam8_mid, hold=0.05)                                                # 見上げて
plan.idle(max(Bt(S_(0.42)) - plan.t, 0.05), shifts=False, glance=False)
plan.nod(n=1, amp=15.0, label="おじぎ")                                                    # 「お待たせしました。」でおじぎ
plan.idle(max(Bt(S_(1.95)) - plan.t, 0.05), shifts=False, glance=False)
plan.jump_to(Bp(BTN.x, BTN.y), z1=TOP_W / KS, label="ボタンにもう一度跳び乗る")                   # M9「時間を、元に戻しましょう。」
seg_j2 = [s_ for s_ in plan.segs if isinstance(s_, mm.JumpSeg)][-1]
T_LAND2 = seg_j2.flights[0]["t1"] * SQK; T_UNFREEZE = T_LAND2 + 0.10
plan.idle(max(Bt(T_UNFREEZE + 0.70) - plan.t, 0.05), shifts=False, glance=False)
plan.turn_to(heading_to((BTN.x, BTN.y), PHONE_W), label="主人公のほうを向く")
look_at(plan, (BTN.x, BTN.y), tuple(hp0), z_eye=0.27 + TOP_W, hold=Bt(T_END + 0.5) - plan.t)       # 主人公を見上げる（そのまま M10 へ）
plan.idle(max(Bt(T_END + 0.5) - plan.t, 0.1), shifts=False, glance=False)
frames_r = mm.simulate(plan, fps=FPS * SQK)
print("ROBOT land %.2f freeze %.2f | land2 %.3f unfreeze %.3f (summary s %.3f)" % (T_LAND, T_FREEZE, T_LAND2, T_UNFREEZE, T_UNFREEZE - T2), flush=True)
rig_r = mr.MaruRig(robot); bk_r = mr.Baker()
for i in range(N): rig_r.apply(frames_r[min(i, len(frames_r) - 1)], i + 1, bk_r)
bk_r.write()
for k_ in range(3): RW.scale[k_] = KS
for n_ in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
    if n_ in O: O[n_].hide_render = False

# ---------------------------------------------------------------- 世界の時刻（止まる → 動き出す）
F_LAST = max(f for f in range(1, N + 1) if (f - 1) / FPS < T_FREEZE)          # 時間が止まる直前のコマ（ここの姿のまま止まる）
T_FZ = (F_LAST - 1) / FPS                                                      # 止まった姿の時刻
RAMP = 0.5                                                                     # 動き出し：0.5秒で速さ 0→1（テープが回り出すように）


def consumed(u):
    """動き出してから u 秒で、世界の時計が進んだ秒（速さ 1−(1−u/RAMP)^1.6 の積分）"""
    if u <= 0: return 0.0
    if u >= RAMP: return RAMP - RAMP / 2.6 + (u - RAMP)
    x = (RAMP - u) / RAMP; return u - RAMP / 2.6 * (1.0 - x ** 2.6)


def world_t(t):
    if t < T_FREEZE: return t
    if t < T_UNFREEZE: return T_FZ
    return T_FZ + consumed(t - T_UNFREEZE)


def t_of_world(tw):
    """世界の時刻 → この台本の秒（動き出したあと）"""
    lo, hi = T_UNFREEZE, T_END + 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if world_t(mid) < tw: lo = mid
        else: hi = mid
    return hi


# 曲：止まった位置からそのまま進めても、8拍のくり返しの中なら同じ音。サビの頭（dance.G0）が M10 の頭に来るように、戻る位置 P_RESUME を決める
P_RESUME = dance.G0 - (world_t(T_M10) - T_FZ)
def song_pos(tw): return P_RESUME + (tw - T_FZ)                                # 世界の時刻（動き出したあと）→ 曲の位置（第1章の秒）
assert 2.0 < P_RESUME < 21.5, "曲の戻る位置が、静かな部分のくり返しの外 %.3f" % P_RESUME
print("SONG resume %.3f (chorus at summary s %.3f)" % (P_RESUME, T_M10 - T2), flush=True)

# ---------------------------------------------------------------- 乗客の小さな動き（第1・2章と同じ乱数で作る → 止まった姿が同じ）
if getattr(A, "acts", 0):
    FORCE = {"P3": [("look", T_FREEZE - 0.30, 3.0, 24.0)], "L3": [("press", T_FREEZE - 0.55, 0.0, 0.0)], "P4": [("shift", T_FREEZE - 0.45, 0.0, 1.0)],
             "P5": [("look", T_FREEZE - 0.15, 3.0, -20.0)], "L1": [("hold", T_FREEZE - 0.30, 0.0, 0.0)]}
    for n_, person in P.items():
        if n_ == "H": continue
        person["acts"] = people.make_acts(person["kind"], seed=sum(ord(c) * (i + 3) for i, c in enumerate(n_)), t_end=81.0, force=FORCE.get(n_))
    n_fl = 0
    for n_, person in P.items():
        if n_ == "H" or person["kind"] != "phone_left": continue
        so = next((c for c in person["phone"].children if c.name.endswith("screen")), None)
        if so is None or not so.active_material: continue
        nt_ = so.active_material.node_tree; tx0 = next((n for n in nt_.nodes if n.bl_idname == "ShaderNodeTexImage"), None)
        if tx0 is None or (tx0.image and tx0.image.name.startswith("music")): continue
        tcn = nt_.nodes.new("ShaderNodeTexCoord"); mp = nt_.nodes.new("ShaderNodeMapping"); mp.name = "Scroll"
        nt_.links.new(tcn.outputs["UV"], mp.inputs["Vector"]); nt_.links.new(mp.outputs["Vector"], tx0.inputs["Vector"])
        loc = mp.inputs["Location"]; off = 0.0; rsc = random.Random(len(n_) * 7 + n_fl)
        loc.default_value[1] = 0.0; loc.keyframe_insert("default_value", index=1, frame=1)
        for kind_, t0_, d_, v_ in person["acts"]:
            if kind_ != "flick": continue
            if t0_ < T_FREEZE: fa, fb = t0_ * FPS + 1, (t0_ + 0.35) * FPS + 1
            elif T_FZ < t0_ < world_t(T_END): fa, fb = t_of_world(t0_) * FPS + 1, t_of_world(t0_ + 0.35) * FPS + 1     # 動き出したあとも、はじくたびに流れる
            else: continue
            loc.keyframe_insert("default_value", index=1, frame=fa)
            off -= rsc.uniform(0.05, 0.11); loc.default_value[1] = off; loc.keyframe_insert("default_value", index=1, frame=fb)
        n_fl += 1
    print("ACTS", sum(len(pr.get("acts", ())) for pr in P.values()), "scroll screens", n_fl, flush=True)

# ---------------------------------------------------------------- 踊り：乗客は第1章 K7 の想像の中だけ。主人公は曲の位置で振り付けを引く
people.DANCE = lambda person, t_: dance.crowd(t_)
K8_ROW = ("X2", "P1", "P2", "P3", "P4")
for n_ in K8_ROW:
    pr_ = P.get(n_)
    if pr_ is None or "acts" not in pr_: continue
    pr_["acts"] = [a_ for a_ in pr_["acts"] if not (a_[0] in ("look", "shift", "hold", "press") and dance.T_FANT1 - 1.5 <= a_[1] <= 33.0)]
# まとめ：M10・M11 に映る人は、動き出したあと大きな動きをしない（はじく・打つは続ける）。止まる前に始まっていた動きは、そのまま続く
CALM = ("X1", "X2", "P1", "P2", "P3", "P4", "P5")
for n_ in CALM:
    pr_ = P.get(n_)
    if pr_ is None or "acts" not in pr_: continue
    pr_["acts"] = [a_ for a_ in pr_["acts"] if not (a_[0] in ("look", "shift", "hold", "press") and a_[1] > T_FZ)]
_rh0 = hero["rig"]; _rh0.fk()
HERO_HEAD_W = hero["arm"].matrix_world @ Vector(tuple(float(v) for v in _rh0.posed_point("head", hero["hc"])))
HERO_LOOKAT = HERO_HEAD_W + Vector((0.0, 0.0, 0.18))                          # 踊っている主人公の頭〜振り上げた手のあたり
GLANCE = {}                                                                    # 隣の人：主人公のほうへ顔を向ける（目が先、顔はあと）。一度ちらっと見て戻し、決めポーズでもう一度
LEAN_P1, LEAN_X2 = float(os.environ.get("LEAN_P1", "11")), float(os.environ.get("LEAN_X2", "-11"))   # 主人公から少し身を引く（度。向きは確かめて決める）
for n_, deg_, lean_, looks_ in (("P1", 55.0, LEAN_P1, [(11.25, 1.10), (14.70, 3.20)]), ("X2", -55.0, LEAN_X2, [(12.35, 0.95), (14.95, 3.00)])):
    if n_ not in P: continue
    gp_ = P[n_]["arm"].matrix_world.inverted() @ HERO_LOOKAT
    P[n_]["glance"] = (world_t(S_(10.9)), world_t(S_(D_SUM)) + 1.0, np.array(gp_[:]), deg_, lean_)
    for s_a, d_a in looks_:
        P[n_].setdefault("acts", []).append(("look", world_t(S_(s_a)), d_a, 0.0))
    P[n_]["acts"].sort(key=lambda a_: a_[1]); GLANCE[n_] = looks_


def dance_sum(tw):
    """主人公の踊り（引数は世界の時刻）。止まるまでは第1・2章と同じ。動き出したあとは曲の位置で引き、決めポーズのまま終わる"""
    if tw <= T_FZ + 1e-6: return dance.hero(tw)
    ts = min(song_pos(tw), dance.T_FANT1 - 1e-3)
    d = dance.hero(ts)
    if ts < dance.G0 - 0.05:                                                   # サビの前（静かな部分）：手を下ろしてから、小さくうなずき始める
        k = mj(tw, T_FZ + 1.0, 0.8)
        for key in ("head_x", "neck_x", "spine_x"): d[key] *= k
    return d


hero_anim.DANCE = dance_sum
_TL0 = hero_anim.timeline


def timeline_sum(t):
    """主人公の驚き（第2章）を、動き出したあとで解く：目→頭→胴の順に画面へ戻り、手をイヤホンから下ろし、口もとが戻る"""
    d = _TL0(t); tw = t + hero_anim.T_REL
    if tw <= T_FZ + 1e-6: return d
    r_g = mj(tw, T_FZ + 0.30, 0.20); r_h = mj(tw, T_FZ + 0.36, 0.55); r_t = mj(tw, T_FZ + 0.46, 0.70)
    r_r = mj(tw, T_FZ + 0.42, 0.85); r_m = mj(tw, T_FZ + 0.80, 0.50); r_p = mj(tw, T_FZ + 0.50, 0.80)
    d["gaze"] *= 1 - r_g; d["head"] *= 1 - r_h; d["torso"] *= 1 - r_t; d["reach"] *= 1 - r_r
    d["flat"] *= 1 - r_m; d["phone_down"] *= 1 - r_p
    return d


hero_anim.timeline = timeline_sum

# ---------------------------------------------------------------- 「みんな同じ曲？」（第1章。止まる前の計算をそろえるため、同じ節点を作る）
SAME_IMG = bpy.data.images.load(os.path.join(HERE, "screens", "music.png"), check_existing=True)
same_mix = []
for n_, person in P.items():
    if n_ == "H": continue
    so = next((c for c in person["phone"].children if c.name.endswith("screen")), None)
    if so is None or not so.active_material: continue
    m_ = so.active_material; nt_ = m_.node_tree
    tx0 = next((n for n in nt_.nodes if n.bl_idname == "ShaderNodeTexImage"), None); em_ = next((n for n in nt_.nodes if n.bl_idname == "ShaderNodeEmission"), None)
    if tx0 is None or em_ is None: continue
    tx1 = nt_.nodes.new("ShaderNodeTexImage"); tx1.image = SAME_IMG
    mx = nt_.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.name = "Same song"
    nt_.links.new(tx0.outputs["Color"], mx.inputs[6]); nt_.links.new(tx1.outputs["Color"], mx.inputs[7]); nt_.links.new(mx.outputs[2], em_.inputs["Color"])
    same_mix.append(m_)

pulse.data.materials.clear(); pulse.data.materials.append(mat_emit("Pulse glow", (0.3, 1.0, 0.9), 6.0))

# ---------------------------------------------------------------- 主人公のまばたき（第1・2章と同じ ＋ 動き出したあと）
rbl = random.Random(9); BL = []; tb = -34.0
while tb < 24.0:
    if not (-0.3 < tb < 2.0): BL.append(tb)
    tb += rbl.uniform(3.2, 4.8)
T_REL = T_DROP - hero_anim.T_DROP
hero_anim.T_REL = T_REL
BL_SUM = [T_FZ + d_ - T_REL for d_ in (0.95, 3.6, 6.4, 9.6)]                    # 動き出したあと（世界の秒）：手を下ろしたあと・サビの前・踊りの合間
hero_anim.BLINKS = sorted(BL + [hero_anim.T_DROP + 2.05, hero_anim.T_DROP + 4.30] + BL_SUM)

# ---------------------------------------------------------------- カメラ
cd_ = bpy.data.cameras.new("Summary camera"); cam = link(O.new("Summary camera", cd_)); cd_.sensor_width = 36; cd_.clip_start = 0.02
cd_.dof.use_dof = True; cd_.dof.aperture_fstop = 2.8; scene.camera = cam
V3 = lambda *a: Vector(a)
def lerpv(a, b, u): return Vector(a).lerp(Vector(b), u)
def lerp_f(a, b, u): return a + (b - a) * u
def robot_pos(t):
    fr = frames_r[min(int(round(t * FPS)), len(frames_r) - 1)]; x, y, z = fr["root"]
    return Vector((x * KS, y * KS, z * KS))


def shot(t):
    """この台本の秒 → (位置, 見る点, レンズ, ピントの点)"""
    nm = cut_of(t)
    if nm in ("K", "M8"):                          # 止まった車内：通路の奥から、まるロボと主人公の足もと（光の輪）へゆっくり寄る
        u = mj(t, T2, T_M9 - T2); p = lerpv(M8_P0, M8_P1, u); tg = lerpv(M8_T0, M8_T1, u)
        return p, tg, 26.0, robot_pos(t) + V3(0, 0, 0.2)
    if nm == "M9":                                 # 横の低い所：まるロボが跳び乗る → 動き出したあと、ボタンの上のまるロボへゆっくり寄る
        w = mj(t, T_LAND2 - 0.35, 0.9); s = mj(t, T_UNFREEZE + 0.2, T_M10 - T_UNFREEZE - 0.2); w2 = mj(t, T_UNFREEZE + 1.6, 1.8)
        tg = TG9_0.lerp(TG9_1, w).lerp(TG9_2, 0.55 * w2); p = CAM9.lerp(TG9_1, 0.16 * s)
        return p, tg, 26.0, robot_pos(t) + V3(0, 0, 0.2)
    if nm == "M10":                                # 右の列を斜めに（主人公が手前。第1章 K8 と同じ向き）
        u = mj(t, T_M10, T_M11 - T_M10); p = lerpv((-1.50, -0.64, 1.14), (-1.44, -0.58, 1.13), u); tg = V3(0.0, 0.85, 1.02)
        return p, tg, 22.0, hp0 + V3(0, 0.3, -0.1)
    u = mj(t, T_M11, T_END - T_M11)                # M11：主人公の正面（通路から、座った人の目の高さ）。両隣と、頭の上に振り上げたスマホまで入る
    p = lerpv((-1.52, 0.03, 1.12), (-1.42, 0.02, 1.11), u); tg = V3(0.0, 0.0, 1.28)
    return p, tg, 22.0, hp0


# ---------------------------------------------------------------- 毎コマの計算（第1・2章と同じ物理）
tt, acc = motion.train_sway(T_END + 1, FPS, seed=3, rms=0.22)
_, acc_y = motion.train_sway(T_END + 1, FPS, seed=8, rms=0.07)
sway = motion.pendulum_response(acc, FPS)
rq = random.Random(4); SWAY = {}
for n, person in P.items():
    if n == "H": continue
    r_ = motion.pendulum_response(acc, FPS, f0=rq.uniform(0.95, 1.35), z=rq.uniform(0.45, 0.65))
    s_ = 1.0 if person["arm"].location.x > -1.0 else -1.0
    r_ = s_ * r_; r_ = np.where(r_ < 0, r_ * 0.35, r_)
    SWAY[n] = r_
h_ = 1.0 / (FPS * 10); pre = 10.0
acc_f = lambda arr, t_: float(np.interp(t_, tt, arr))
for st_ in STRAPS:
    w_ = math.sqrt(9.81 / st_["L"]); z_ = st_["zeta"]; px = py = vx = vy = 0.0; out = []
    for i in range(int((pre + T_END + 1) * FPS * 10)):
        t_ = i * h_ - pre; tm = (t_ % 20.0) if t_ < 0 else t_
        ax_ = acc_f(acc, tm); ay_ = acc_f(acc_y, tm)
        vx += (-w_ * w_ * math.sin(px) - 2 * z_ * w_ * vx + ax_ / st_["L"] * math.cos(px)) * h_; px += vx * h_
        vy += (-w_ * w_ * math.sin(py) - 2 * z_ * w_ * vy - ay_ / st_["L"] * math.cos(py)) * h_; py += vy * h_
        if t_ >= 0 and i % 10 == 0: out.append((px, py))
    st_["ang"] = out
rdu = np.random.default_rng(13)
for d_ in DUST:
    v_ = np.zeros(3); p_ = np.zeros(3); traj = []; rot = 0.0; wr_ = rdu.uniform(-0.15, 0.15)
    for i in range(N + 2):
        v_ += (-v_ / 2.0) / FPS + rdu.normal(0, 1, 3) * 0.015 * math.sqrt(2 / 2.0 / FPS)
        p_ = p_ + v_ / FPS; rot += wr_ / FPS; traj.append((p_.copy(), rot))
    d_["traj"] = traj


def at_frame(arr, fw):
    """コマの番号（1から、小数も）で配列を引く（間は直線でつなぐ）"""
    x = min(max(fw - 1.0, 0.0), len(arr) - 1.0); i = int(math.floor(x)); j = min(i + 1, len(arr) - 1); u = x - i
    return arr[i], arr[j], u


bk = hrig.Baker()
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
ex = {}; hero_anim.pose_at(hero, hero_anim.T_DROP + 2.0, 0.0, hero_bud_rest, ex)
rig_h = hero["rig"]; rig_h.fk()
tip = (rig_h.tail_pos("index_03.R") + rig_h.tail_pos("middle_03.R")) / 2
hero["touch_fix"] = (rig_h.posed_point("head", hero_bud_rest) + np.array([-0.006, -0.004, -0.010])) - tip
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
cam.rotation_mode = "QUATERNION"; shots = []
if A.dry == 2: KEYS = {N}
elif A.dry: KEYS = set(int(x) for x in A.dry_frames.split(","))
else: KEYS = set(range(max(1, f0 - 1), min(N, f1 + 1) + 1))
eyes_last = (0.0, 0.0)
SW_N = {n: np.asarray(v, float) for n, v in SWAY.items()}; SW_H = np.asarray(sway, float)
for f in range(1, N + 1):
    t = (f - 1) / FPS
    frozen = T_FREEZE <= t < T_UNFREEZE
    tw = world_t(t); fw = tw * FPS + 1.0                                      # 世界の時刻とコマ（動き出したあとは小数）
    need = f in KEYS
    if not frozen:
        ex = {}
        a_, b_, u_ = at_frame(SW_H, fw); hero_anim.pose_at(hero, tw - T_REL, float(a_ + (b_ - a_) * u_), hero_bud_rest, ex)
        eyes_last = (ex["blink"], ex["wide"] * (1 - ex["blink"]))
        if need or f == F_LAST:
            for n, person in P.items():
                if n == "H": continue
                a_, b_, u_ = at_frame(SW_N[n], fw); people.base_pose(person, tw, sway=float(a_ + (b_ - a_) * u_))
    if need:
        fz = F_LAST if frozen else fw                                         # 止まっている間は、止まった瞬間の値
        bk.pose(hero["rig"], f)
        for sd in ("L", "R"):
            sk = hero["objs"]["eye." + sd].data.shape_keys
            bk.put(sk, 'key_blocks["blink"].value', 0, f, eyes_last[0]); bk.put(sk, 'key_blocks["wide"].value', 0, f, eyes_last[1])
        for n, person in P.items():
            if n != "H": bk.pose(person["rig"], f)
        for st_ in STRAPS:
            a_, b_, u_ = at_frame(st_["ang"], fz)
            bk.put(st_["ob"], "rotation_euler", 1, f, a_[0] + (b_[0] - a_[0]) * u_); bk.put(st_["ob"], "rotation_euler", 0, f, a_[1] + (b_[1] - a_[1]) * u_)
        for d_ in DUST:
            a_, b_, u_ = at_frame(d_["traj"], fz); pp = a_[0] + (b_[0] - a_[0]) * u_; rr = a_[1] + (b_[1] - a_[1]) * u_
            for i in range(3): bk.put(d_["ob"], "location", i, f, d_["c0"][i] + pp[i])
            bk.put(d_["ob"], "rotation_euler", 2, f, rr)
        bk.put(FLOW, "location", 1, f, -V_TRAIN * (fz - 1) / FPS)
        # 光の輪：止まると広がって残る（第2章）→ 動き出すと、ボタンへ縮んで消える（第2章の逆）
        if t < T_FREEZE: s_p = 0.0
        elif t < T_UNFREEZE: s_p = 2.6 * (1 - (1 - min(max((t - T_FREEZE) / 0.6, 0.0), 1.0)) ** 3)
        else: s_p = 2.6 * (1 - min(max((t - T_UNFREEZE) / 0.6, 0.0), 1.0) ** 3)
        for i in range(3): bk.put(pulse, "scale", i, f, max(s_p, 1e-4))
        on_ = mj(t, T_FREEZE, 0.3) * (1 - mj(t, T_UNFREEZE + 0.05, 0.45))
        flash = motion.env(t, T_LAND2, 0.04, 0.0, 0.30) if t >= T_FREEZE else 0.0              # 押した瞬間、ボタンが一度明るくなる
        bk.put(glow.data, "energy", 0, f, 45.0 * on_ + 40.0 * flash)
        g_ = mj(t, T_FREEZE, 0.35) * (1 - mj(t, T_UNFREEZE, 0.35))
        bk.put(scene.node_tree, 'nodes["%s"].inputs["Saturation"].default_value' % hsv.name, 0, f, 1.0 - 0.45 * g_)
        bk.put(scene.node_tree, 'nodes["%s"].inputs["Fac"].default_value' % cb_.name, 0, f, 0.6 * g_)
    nm = cut_of(t)
    if t >= T2 and (not shots or shots[-1][1] != nm): shots.append([round(t - T2, 3), nm])
bk.write(interp="LINEAR")
for m_ in same_mix:
    sock = m_.node_tree.nodes["Same song"].inputs[0]
    for t_, v_ in ((T_SAME0, 0.0), (T_SAME0 + 0.15, 1.0), (T_SAME1, 1.0), (T_SAME1 + 0.15, 0.0)):
        sock.default_value = v_; sock.keyframe_insert("default_value", frame=t_ * FPS + 1)
if os.environ.get("DEBUG_GLANCE"):                                   # 確かめ用：隣の人の顔の向き（主人公のほうを向くか）
    for _n in GLANCE:
        _pr = P[_n]; _rg = _pr["rig"]
        for _s in (11.9, 15.6):
            _tw = world_t(S_(_s)); people.base_pose(_pr, _tw); _rg.fk()
            _Rn = hrig.m3(_rg.M["head"]) @ hrig.m3(_rg.rest["head"]).T; _fw = _Rn @ np.array([0, -1.0, 0]); _to = np.asarray(_pr["glance"][2]) - _rg.head_pos("head")
            _hw = _pr["arm"].matrix_world @ Vector(tuple(float(v) for v in _rg.head_pos("head")))
            print("GLANCE %s s=%.2f face yaw %.1f deg (to hero %.1f deg) head world y %.3f (person y %.2f)" % (_n, _s, math.degrees(math.atan2(_fw[0], -_fw[1])), math.degrees(math.atan2(_to[0], -_to[1])), _hw.y, _pr["arm"].location.y), flush=True)
bkc = hrig.Baker()
for f in range(1, N + 1):
    t = (f - 1) / FPS; p, tg, lens, fp = shot(t); q = (Vector(tg) - Vector(p)).to_track_quat("-Z", "Y")
    for k in range(3): bkc.put(cam, "location", k, f, p[k])
    for k in range(4): bkc.put(cam, "rotation_quaternion", k, f, q[k])
    bkc.put(cd_, "lens", 0, f, lens); bkc.put(cd_, "dof.focus_distance", 0, f, max((Vector(fp) - Vector(p)).length, 0.05))
bkc.write(interp="LINEAR")
for o_ in [cam]:
    if o_.animation_data and o_.animation_data.action:
        for fc in o_.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
log = dict(fps=FPS, frames=N, t2=T2, ep0=EP0, f_sum0=F_SUM0, t_freeze=T_FREEZE, t_fz=T_FZ, t_land2=T_LAND2, t_unfreeze=T_UNFREEZE, ramp=RAMP,
           p_resume=P_RESUME, g0=dance.G0, t_m9=T_M9, t_m10=T_M10, t_m11=T_M11, shots=shots, glance=GLANCE,
           events=[dict(e, t=round(e["t"] * SQK, 4)) for e in plan.events if e["t"] * SQK >= T2 - 0.5])
json.dump(log, open(os.path.join(A.out, "summary_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, default=float)
print("BAKED", round(time.time() - t0, 1), "unfreeze %.3f (s %.3f)" % (T_UNFREEZE, T_UNFREEZE - T2), flush=True)
scene.render.use_motion_blur = bool(A.blur); scene.render.motion_blur_shutter = 0.5
scene.render.image_settings.file_format = "PNG"; scene.render.use_overwrite = False; scene.render.use_placeholder = True
scene.render.filepath = os.path.join(A.out, "frames", "f_")
scene.frame_start, scene.frame_end = f0, min(f1, N)
if A.dry == 2:
    pass
elif A.dry:
    for fr in [int(x) for x in A.dry_frames.split(",")]:
        scene.frame_set(fr); scene.render.filepath = os.path.join(A.out, f"check_{fr:04d}.png"); bpy.ops.render.render(write_still=True)
        print("CHECK", fr, round(time.time() - t0, 1), flush=True)
else:
    if A.video:
        scene.render.image_settings.file_format = "FFMPEG"; ff = scene.render.ffmpeg
        ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "HIGH"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
        scene.render.use_overwrite = True; scene.render.use_placeholder = False
        scene.render.filepath = os.path.join(A.out, "summary_")
    bpy.ops.render.render(animation=True)
print("SEQ DONE", round(time.time() - t0, 1), flush=True)
