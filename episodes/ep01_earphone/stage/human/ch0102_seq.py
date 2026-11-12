# 第1・2章（本編 0:00〜1:21）の動き：opening_phys.py から exec される
#   使い方: blender -b --factory-startup --python opening_phys.py -- --seq ch0102_seq.py --crowd 1 --world_len 1450 --out DIR [--dry 1 --dry_frames ...] [--frames A:B]
#   冒頭22秒の試作（承認済み）を、ナレーションの1文ずつに合わせた15カット（K1〜K15）に広げる
#   ・曲は 37.9秒で途切れ、0.85秒で戻る。主人公は目→頭→体→右手でイヤホンに触れ、そのまま時間が止まる（第3章の止まった姿へつながる）
#   ・まるロボは第3章と同じ動きの部品集（marumotion）で動かす。電車の中では高さ約0.4m（1/3）。同じ重力で小さいので、
#     動きは √3 ≈ 1.73倍の速さになる（フルード数をそろえる：大きい世界で計算し、時間を 1/√3 に縮めて当てる）
#   ・59.6秒、まるロボが一時停止ボタンに着地した 0.1秒後に時間が止まる：外の景色・つり革・ほこり・乗客が止まり、色が少し落ちる。
#     止まった世界で動くのは、まるロボとカメラだけ
import json
sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import marumotion as mm, marurig as mr
import dance
f0, f1 = [int(x) for x in A.frames.split(":")]
T_END = 81.0
N = int(round(T_END * FPS))
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, N
mj = motion.mj

# ---------------------------------------------------------------- 時刻（本編の秒）
T_DROP = 38.20                   # 曲が途切れる（Codex版の音源でも 38.2〜38.8秒が無音。「ときどき……」と「こんなふうに」の間）
T_BACK = 38.80                   # 曲が戻る（主人公がイヤホンに触れる前。押したから直ったとは見せない）
T_SAME0, T_SAME1 = 21.75, dance.T_FANT1   # 「たまたま、みんな同じ曲を？」：画面がすべて主人公の曲になる → 「……そんなわけないですよね」で戻る
T_K7B = dance.G0 + 8 * dance.T_B          # K7 の後半（3小節目の頭 24.876秒）：車内全体。手が上がる
# K7（想像）：曲の盛り上がりに合わせて全員が踊る → K8（現実、29.878秒）：踊っているのは主人公だけ。隣の人がちらっと見る
CUTS = [(0.0, "K1"), (3.7, "K2"), (5.9, "K3"), (7.6, "K4"), (12.7, "K5"), (17.1, "K6"), (21.6, "K7"), (T_K7B, "K7b"), (dance.T_FANT1, "K8"), (32.8, "K9"),
        (42.7, "K10"), (50.8, "K11"), (56.1, "K12"), (64.0, "K13"), (68.7, "K14"), (74.7, "K15")]


def cut_of(t):
    nm = CUTS[0][1]
    for a_, n_ in CUTS:
        if t >= a_: nm = n_
    return nm


# ---------------------------------------------------------------- 一時停止ボタン：主人公の足もとの通路（足先から 0.27m）へ置き直す
B_NEW2 = Vector((-1.00, -0.25, 0.0))
oldw.matrix_world = Matrix.Translation(B_NEW2) @ Matrix.Rotation(PHI, 4, "Z") @ Matrix.Scale(1.0 / S, 4) @ Matrix.Translation(-B_OLD)
bpy.context.view_layer.update()
E = oldw.matrix_world.copy(); Einv = E.inverted()
BTN = Vector((B_NEW2.x, B_NEW2.y, 0.0)); TOP_W = 0.178 / S          # ボタンの上面の高さ（電車の座標で 0.108m）
glow.location = to_w((0.14, -3.65, 0.35))

# ---------------------------------------------------------------- まるロボ：大きい世界（第3章と同じ大きさ）で計算し、1/3 に縮めて電車に置く
KS = 1.0 / 3.0; SQK = math.sqrt(KS)
RW = link(O.new("ROBOT WORLD", None)); RW.matrix_world = Matrix.Scale(KS, 4)
robot.parent = RW; robot.matrix_parent_inverse = Matrix.Identity(4); robot.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
def Bt(t_real): return t_real / SQK                                  # 本編の秒 → 大きい世界の秒
def Bp(x, y): return (x / KS, y / KS)                               # 電車の座標 → 大きい世界の座標
def heading_to(src, dst): return math.degrees(math.atan2(-(dst[0] - src[0]), dst[1] - src[1]))
R_START = (BTN.x, -2.35); R_STOP = (BTN.x, BTN.y - 0.40); R_HERO = (-0.80, -0.47)
hp0, bud0 = hero_points()
PHONE_W = tuple(float(v) for v in hero["phone"].matrix_world.translation)   # 主人公のスマホ（左手）の位置
# v5（2026-11-09 ユーザー：冒頭からまるロボを出す。最初の 50 秒で離脱させないため）：まるロボは最初から車内にいる脇役。音は出さない（足音は 50 秒から）
#   既定は通路の床（OP_SPOT＝aisle）：K1 で通路の真ん中から見回し、K3 で動画を見ている人の横から一緒に見上げ、K4 で両側のスマホを見上げ、
#   K7b（みんな同じ曲で踊る想像）でカメラの近くでノリノリ。K7・K8 の画面には入らない（カットの切り替わりで置き直す）
#   網棚の版（OP_SPOT＝rack）も残す：静止画で、つり革の陰で暗く小さかったので使わない（網棚の上ではアンテナを 45% に縮める：天井 2.30m）
#   どちらも 50.15 秒から今までどおり通路を歩いてくる。乱数は使わない（50 秒からの動きは前と同じ）
RACK_X, RACK_Z = 0.17, 1.80; RACK_P1 = (RACK_X, 1.6); RACK_P2 = (RACK_X, 3.4); T_OFF = 33.6; ANT_RACK = 0.45
CAM_K1 = (-1.31, -2.40)
OP_SPOT = os.environ.get("MARU_OP_SPOT", "aisle")                                    # aisle＝通路の床（明るい真ん中。2026-11-09 の静止画で、網棚は つり革の陰で暗く小さかった）／rack＝網棚
AISLE_A = (-1.15, 2.4); AISLE_B = (-1.35, 3.6)                                         # 通路（両側の膝のあいだ x −1.65〜−0.65）。B は K7・K8 の画面の外で、K7b には映る所
def until_r(t_real): plan.idle(max(Bt(t_real) - plan.t, 0.05), shifts=False, glance=False)
def look_r(src, dst, z_eye, hold):
    hd = heading_to(src, dst); yaw = (hd - math.degrees(plan._psi) + 180) % 360 - 180
    pitch = math.degrees(math.atan2(dst[2] - z_eye, math.hypot(dst[0] - src[0], dst[1] - src[1])))
    plan.look(yaw=max(-60, min(60, yaw)), pitch=max(-35, min(40, pitch)), hold=hold)
def rack_dance(t):
    """想像の中のノリノリ：拍（0.385秒）ごとに弾み、2拍で左右に揺れる。体を少しひねって、目は少し上。現実に変わる所でぴたりと止まる"""
    tr = t * SQK
    if tr < dance.G0 - 0.15 or tr >= dance.T_FANT1: return {}
    e = min(1.0, (tr - (dance.G0 - 0.15)) / 0.3)
    ph = (tr - dance.G0) / dance.T_B; b = 0.5 * (1 - math.cos(2 * math.pi * ph))
    return {"lift": -0.045 * e * b, "pitch": 5.0 * e * b, "roll": 6.0 * e * math.sin(math.pi * ph),
            "twist": 12.0 * e * math.sin(math.pi * ph + 0.6), "gaze_pitch": 8.0 * e, "light": 1.2 * e * b * b}
def jump_cut(xy, heading, z=0.0):
    """カットの切り替わり（どちらのカメラにも映っていない間）に、まるロボを別の場所へ置き直す（体と足をその場に。ばねの揺れも止める）"""
    t_ = plan.t; p_ = np.array(Bp(*xy), float); psi_ = math.radians(heading)
    plan._seg_add(mm.Seg(t_, t_, p_, psi_))
    for j_ in (0, 1):
        plan._lift_foot(j_, t_); plan._place(j_, t_, (*(p_ + mm.rgt(psi_) * (-1 if j_ == 0 else 1) * mm.HIP_X), z / KS), psi_)
    for ch_, tr_ in plan.tracks.items(): tr_.set(t_, 0.0, 0.0)
    plan.cuts.append(t_); plan._p, plan._psi = p_, psi_
if OP_SPOT == "rack":
    plan = mm.Plan(pos=Bp(*RACK_P1), heading=heading_to(RACK_P1, CAM_K1), ground=RACK_Z / KS, seed=5)
    until_r(0.35); plan.look_around(label="車内を見回す")                                      # K1
    until_r(3.75); plan.turn_to(0.0); plan.walk_to(Bp(*RACK_P2), speed=mm.V_WALK, label="網棚の上を奥へ")   # K2・K3 の間（K4 の頭まで）
    plan.turn_to(90.0)                                                                       # 通路の側を向く
    plan.peer(dur=Bt(1.4), label="下の乗客のスマホをのぞく")                                    # K4
    until_r(dance.G0 - 0.15); plan.layer(plan.t, Bt(dance.T_FANT1) + 0.01, rack_dance)        # K7・K7b
    until_r(dance.T_FANT1 + 0.30)
    look_r(RACK_P2, tuple(hp0), RACK_Z + 0.27, Bt(0.5))                                      # K8：踊り続ける主人公を見る
    plan.confused(label="主人公だけ踊っている？")
else:
    # 通路（v5b）：K1 は明るい通路の真ん中（字幕のすぐ上）で、カメラの方を向いて見回す（アンテナの灯が 3 回光る）
    #   → K3 の背景で、動画を見ている人（L2）のスマホを見上げる → K4（遠い端から）両側の乗客のスマホを見上げ、こちらを見る
    #   → K5・K6 の間に画面の外（奥）へ → K7 の間も奥で踊り始める（K7 の画面の外）→ K7b に切り替わる瞬間、K7b のカメラの近くへ（みんなとノリノリ）
    #   → K8（現実）に切り替わる瞬間、画面の外（通路の手前の端）へ → 50.15 秒から今までどおり歩いてくる
    AISLE_A = (-1.15, 1.7); AISLE_H = (-1.35, 3.6); AISLE_D = (-1.15, 1.2)
    plan = mm.Plan(pos=Bp(*AISLE_A), heading=heading_to(AISLE_A, CAM_K1), seed=5)
    until_r(0.35); t_l = plan.t
    plan.layer(t_l, t_l + Bt(3.2), lambda t, a=t_l: {"light": 2.2 * sum(mm.hump(t, a + Bt(0.25 + 0.95 * k), Bt(0.30)) for k in range(3))})
    plan.look_around(label="車内を見回す")                                                     # K1
    until_r(5.5)
    look_r(AISLE_A, (-1.95, 1.48, 0.95), 0.27, Bt(1.2))                                      # K3：動画を見ている人（L2）のスマホを見上げる
    until_r(7.9)
    look_r(AISLE_A, (-0.35, 2.12, 0.95), 0.27, Bt(0.9))                                      # K4：右の人（P3）のスマホ
    look_r(AISLE_A, (-1.95, 2.50, 0.95), 0.27, Bt(0.9))                                      #     左の人（L3）のスマホ
    look_r(AISLE_A, (-1.15, 6.4, 2.0), 0.27, Bt(0.5))                                        #     こちら（奥の高いカメラ）
    until_r(14.0); jump_cut(AISLE_H, 180.0)                                                  # K5・K6 の間（画面の外）
    until_r(dance.G0 - 0.15); plan.layer(plan.t, Bt(dance.T_FANT1) + 0.01, rack_dance)        # 踊り始め（K7 の間は画面の外）
    until_r(T_K7B); jump_cut(AISLE_D, 180.0)                                                 # K7b：カメラの近くで、みんなとノリノリ
    until_r(dance.T_FANT1); jump_cut(R_START, 0.0)                                           # K8（現実）：画面の外（通路の手前の端）へ
if OP_SPOT == "rack":
    until_r(T_OFF); jump_cut(R_START, 0.0)                                                # 画面の外で、網棚から通路の端へ（足を床に置き直す）
plan.idle(max(Bt(50.15) - plan.t, 0.05), shifts=False, glance=False)
plan.walk_to(Bp(*R_STOP), speed=mm.V_WALK, label="通路を歩いてくる")                     # K11：通路を歩いてきて、ボタンの手前で止まる
t_stop = plan.t
def look_at(pl, src, dst, z_eye=0.27, hold=0.6, at=None):
    hd = heading_to(src, dst); yaw = (hd - math.degrees(pl._psi) + 180) % 360 - 180
    pitch = math.degrees(math.atan2(dst[2] - z_eye, math.hypot(dst[0] - src[0], dst[1] - src[1])))
    pl.look(yaw=yaw, pitch=pitch, hold=hold, at=at)
plan.idle(max(Bt(53.85) - plan.t, 0.05), shifts=False, glance=False)
look_at(plan, R_STOP, PHONE_W, hold=Bt(0.9) - 0.3, )                                    # 主人公のスマホを見上げる（右上）
plan.idle(max(Bt(55.25) - plan.t, 0.05), shifts=False, glance=False)
plan.look(yaw=0.0, pitch=8.0, hold=0.4)                                                 # こちら（カメラ）を見る：「追いかけてみましょう」
plan.idle(max(Bt(56.35) - plan.t, 0.05), shifts=False, glance=False)
plan.look(yaw=0.0, pitch=-14.0, hold=0.2)                                               # 「その前に」：足もとのボタンを見る


def jump_plan(t_idle):
    q = mm.Plan(pos=Bp(*R_STOP), heading=0.0, seed=5); q.idle(t_idle, shifts=False, glance=False)
    q.jump_to(Bp(BTN.x, BTN.y), z1=TOP_W / KS); seg = [s_ for s_ in q.segs if isinstance(s_, mm.JumpSeg)][0]
    return seg.flights[0]["t1"] - t_idle
d_land = jump_plan(1.0)                                                                  # 跳び始めから着地までの時間（大きい世界）
T_LAND_B = Bt(59.45)                                                                     # 「時間を止めます」の終わり（59.59）の少し前に着地
plan.idle(max(T_LAND_B - d_land - plan.t, 0.05), shifts=False, glance=False)
plan.jump_to(Bp(BTN.x, BTN.y), z1=TOP_W / KS, label="ボタンに跳び乗る")
seg_j = [s_ for s_ in plan.segs if isinstance(s_, mm.JumpSeg)][-1]
T_LAND = seg_j.flights[0]["t1"] * SQK; T_FREEZE = T_LAND + 0.10
CAM12 = (BTN.x - 0.62, BTN.y + 0.55)                                                     # K12 のカメラ（ボタンの左前の低い所）
plan.idle(max(Bt(T_FREEZE + 0.55) - plan.t, 0.05), shifts=False, glance=False)
plan.turn_to(heading_to((BTN.x, BTN.y), CAM12))                                          # 時間を止めたら、こちらを向く
plan.idle(max(Bt(68.95) - plan.t, 0.05), shifts=True, glance=True)
plan.jump_to(Bp(*R_HERO), z1=0.0, label="ボタンから降りる")                                   # K14：ボタンから降り、主人公の前へ
plan.turn_to(heading_to(R_HERO, PHONE_W))                                                # 主人公のスマホのほうへ向く
# v3（2026-11-08 ユーザー：第2章の終わりが無音で長い）：K15 の途中で、スマホが見やすい所へ横に二歩ほど動いて、もう一度見上げる。
#   止まった世界で動いて音を出すのは、まるロボだけ（足音が聞こえる）。前へ歩くと主人公の足に近づくので、横（y）へ
T_SIDE = 77.9; R_SIDE = (R_HERO[0], R_HERO[1] + 0.10)
look_at(plan, R_HERO, PHONE_W, hold=max(Bt(T_SIDE) - plan.t - Bt(0.35), Bt(0.5)))     # スマホを見上げる（K15 の途中まで）
plan.back_to(Bp(*R_SIDE), step=0.20, sw=0.26, gap=0.06, look=False, label="スマホが見やすい所へ横に（4歩）")
look_at(plan, R_SIDE, PHONE_W, hold=Bt(3.0))                                             # もう一度見上げる（このまま第3章へ）
plan.idle(max(Bt(T_END + 0.5) - plan.t, 0.1), shifts=False, glance=False)
frames_r = mm.simulate(plan, fps=FPS * SQK)                                              # 本編の 1コマ（1/24秒）＝ 大きい世界の 1/(24·√k) 秒
for i_, fr_ in enumerate(frames_r):                                                     # 網棚の上（T_OFF まで）はアンテナを 45% だけ出す（天井 2.30m に当たらない）
    if OP_SPOT == "rack" and i_ / FPS < T_OFF: fr_["ant_ext"] = ANT_RACK; fr_["ant"] = (fr_["ant"][0] * ANT_RACK, fr_["ant"][1] * ANT_RACK)
print("ROBOT stop %.2f land %.2f freeze %.2f" % (t_stop * SQK, T_LAND, T_FREEZE), flush=True)
rig_r = mr.MaruRig(robot); bk_r = mr.Baker()
for i in range(N): rig_r.apply(frames_r[min(i, len(frames_r) - 1)], i + 1, bk_r)
bk_r.write()
T_SHOW = 50.80                                                                           # ボタンが見え始める（K11）。まるロボは最初から（v5：網棚の上）
for k_ in range(3): RW.scale[k_] = KS
for n_ in ("Pause button", "Pause button base", "Pause icon", "Pause icon.001", "Pause pulse"):
    if n_ in O:
        ob_ = O[n_]
        for fr_, hide_ in ((1, True), (int(T_SHOW * FPS) + 1, False)):
            ob_.hide_render = hide_; ob_.keyframe_insert("hide_render", frame=fr_)

# ---------------------------------------------------------------- 時間が止まる前の乗客の、小さな自然な動き（--acts 1）
#   一人ずつ別の乱数で：顔を上げる・スクロール（画面の中身も流れる）・打つ／遊ぶ・座り直す・持ち直す・空いた手でイヤホンを押す
#   時間が止まる瞬間に、何人かは動きの途中になるようにする（止まった車内で、止まったことが分かる）
if getattr(A, "acts", 0):
    FORCE = {"P3": [("look", T_FREEZE - 0.30, 3.0, 24.0)], "L3": [("press", T_FREEZE - 0.55, 0.0, 0.0)], "P4": [("shift", T_FREEZE - 0.45, 0.0, 1.0)],
             "P5": [("look", T_FREEZE - 0.15, 3.0, -20.0)], "L1": [("hold", T_FREEZE - 0.30, 0.0, 0.0)]}
    for n_, person in P.items():
        if n_ == "H": continue
        person["acts"] = people.make_acts(person["kind"], seed=sum(ord(c) * (i + 3) for i, c in enumerate(n_)), t_end=T_END, force=FORCE.get(n_))
    n_fl = 0
    for n_, person in P.items():                                     # スクロール：画面の中身（画像）をはじくたびに上へ流す（躍度最小で0.35秒）
        if n_ == "H" or person["kind"] != "phone_left": continue
        so = next((c for c in person["phone"].children if c.name.endswith("screen")), None)
        if so is None or not so.active_material: continue
        nt_ = so.active_material.node_tree; tx0 = next((n for n in nt_.nodes if n.bl_idname == "ShaderNodeTexImage"), None)
        if tx0 is None or (tx0.image and tx0.image.name.startswith("music")): continue     # 曲の画面は流れない（ニュース・チャットなどだけ）
        tcn = nt_.nodes.new("ShaderNodeTexCoord"); mp = nt_.nodes.new("ShaderNodeMapping"); mp.name = "Scroll"
        nt_.links.new(tcn.outputs["UV"], mp.inputs["Vector"]); nt_.links.new(mp.outputs["Vector"], tx0.inputs["Vector"])
        loc = mp.inputs["Location"]; off = 0.0; rsc = random.Random(len(n_) * 7 + n_fl)
        loc.default_value[1] = 0.0; loc.keyframe_insert("default_value", index=1, frame=1)
        for kind_, t0_, d_, v_ in person["acts"]:
            if kind_ != "flick" or t0_ >= T_FREEZE: continue
            loc.keyframe_insert("default_value", index=1, frame=t0_ * FPS + 1)
            off -= rsc.uniform(0.05, 0.11); loc.default_value[1] = off; loc.keyframe_insert("default_value", index=1, frame=(t0_ + 0.35) * FPS + 1)
        n_fl += 1
    print("ACTS", sum(len(pr.get("acts", ())) for pr in P.values()), "scroll screens", n_fl, flush=True)

# ---------------------------------------------------------------- 踊り（dance.py）：K7 は全員（想像）、K8〜K9 は主人公だけ（現実）
people.DANCE = lambda person, t_: dance.crowd(t_)
hero_anim.DANCE = dance.hero
K8_ROW = ("X2", "P1", "P2", "P3", "P4")                               # K8 に映る人：この間は大きな動きをしない（隣の人のちらっと見る、だけ）
for n_ in K8_ROW:
    pr_ = P.get(n_)
    if pr_ is None or "acts" not in pr_: continue
    pr_["acts"] = [a_ for a_ in pr_["acts"] if not (a_[0] in ("look", "shift", "hold", "press") and dance.T_FANT1 - 1.5 <= a_[1] <= 33.0)]
if "P1" in P:                                                        # 隣の人：主人公のほうへ顔を向けて、ちらっと見る（目が先、顔はあと）
    _hh = hero["arm"].matrix_world @ Vector(tuple(float(v) for v in hero["rig"].posed_point("head", hero["hc"])))
    _gp = P["P1"]["arm"].matrix_world.inverted() @ _hh
    P["P1"]["glance"] = (dance.T_FANT1 + 0.2, 32.6, np.array(_gp[:]), 55.0)
    P["P1"].setdefault("acts", []).append(("look", dance.T_FANT1 + 0.42, 1.25, 0.0)); P["P1"]["acts"].sort(key=lambda a_: a_[1])

if os.environ.get("DEBUG_GLANCE"):                                   # 確かめ用：隣の人の顔の向き（主人公のほうを向くか）
    _pr = P["P1"]; _rg = _pr["rig"]
    for _tt in (29.95, 31.3):
        people.base_pose(_pr, _tt); _rg.fk()
        _Rn = hrig.m3(_rg.M["head"]) @ hrig.m3(_rg.rest["head"]).T; _fw = _Rn @ np.array([0, -1.0, 0]); _to = np.asarray(_pr["glance"][2]) - _rg.head_pos("head")
        _ang = math.degrees(math.atan2(_fw[0], -_fw[1])); _ang_to = math.degrees(math.atan2(_to[0], -_to[1]))
        print("GLANCE t=%.2f face yaw %.1f deg (to hero %.1f deg)" % (_tt, _ang, _ang_to), flush=True)
# ---------------------------------------------------------------- 「みんな同じ曲？」：画面の絵を主人公の曲に入れ替える（物が出す光のまま）
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

# ---------------------------------------------------------------- 光の輪（時間を止めたとき）
pulse.data.materials.clear(); pulse.data.materials.append(mat_emit("Pulse glow", (0.3, 1.0, 0.9), 6.0))

# ---------------------------------------------------------------- 主人公のまばたき（長い時間ぶん、3〜5秒おきに。驚いた直後は入れない）
rbl = random.Random(9); BL = []; tb = -34.0
while tb < 24.0:
    if not (-0.3 < tb < 2.0): BL.append(tb)
    tb += rbl.uniform(3.2, 4.8)
hero_anim.BLINKS = sorted(BL + [hero_anim.T_DROP + 2.05, hero_anim.T_DROP + 4.30])
T_REL = T_DROP - hero_anim.T_DROP                                                         # 本編の秒 − T_REL ＝ 主人公の時計
hero_anim.T_REL = T_REL

# ---------------------------------------------------------------- カメラ（カットごと。1台のカメラを動かす）
cd_ = bpy.data.cameras.new("Ch0102 camera"); cam = link(O.new("Ch0102 camera", cd_)); cd_.sensor_width = 36; cd_.clip_start = 0.02
cd_.dof.use_dof = True; cd_.dof.aperture_fstop = 2.8; scene.camera = cam
scene.timeline_markers.clear()
V3 = lambda *a: Vector(a)
def lerpv(a, b, u): return Vector(a).lerp(Vector(b), u)
def person_head(key):
    pr = P[key]; rig = pr["rig"]; rig.fk(); return W(pr, rig.posed_point("head", pr["hc"]))
HEADS = {k: person_head(k) for k in ("L4", "L2", "P1", "L1", "P3", "L3")}
PHONES = {k: P[k]["phone"].matrix_world.translation.copy() for k in ("L4", "L2", "L1", "P3", "L3")}


def ots(key, t0_, d_, t, push=0.06):
    """肩ごし（その人の右の肩の上）から、スマホの画面と耳のイヤホン。画面は持つ人のほうを向いているので、ここからだけよく見える"""
    h = HEADS[key]; ph_ = PHONES[key]; f = Vector((ph_.x - h.x, ph_.y - h.y, 0.0)).normalized(); r = Vector((f.y, -f.x, 0.0))
    u = mj(t, t0_, d_); p = h + r * (0.44 - push * u) - f * (0.07 - push * u) + V3(0, 0, 0.21 - 0.03 * u)
    return p, ph_.lerp(h, 0.22), 30.0, ph_
ROW_R = sorted([(float(pr["phone"].matrix_world.translation.y), pr["phone"].matrix_world.translation.copy()) for k_, pr in P.items()
                if pr["arm"].location.x > -1.0], key=lambda e: e[0])          # 右の列のスマホ（y の順）
def row_phone(y):
    """右の列のスマホの並びを y でなめらかにたどる（x・z は近い2台の間を補う）"""
    ys = [e[0] for e in ROW_R]; ps = [e[1] for e in ROW_R]
    if y <= ys[0]: return ps[0].copy()
    if y >= ys[-1]: return ps[-1].copy()
    for i in range(len(ys) - 1):
        if ys[i] <= y <= ys[i + 1]:
            u = (y - ys[i]) / max(ys[i + 1] - ys[i], 1e-6); u = u * u * (3 - 2 * u); v = ps[i].lerp(ps[i + 1], u); v.y = y; return v
_rh = hero["rig"]; _rh.fk(); BUD_L = W(hero, _rh.posed_point("head", hero["hc"] + np.array([hero["Rh"] * 0.99 + 0.004, 0.010, -0.010])))
C1_CAM = None                                                       # 第3章 C1 の最初の絵（止まったスマホの画面のアップ）：止まった姿が決まってから計算する
def robot_pos(t):
    fr = frames_r[min(int(round(t * FPS)), len(frames_r) - 1)]; x, y, z = fr["root"]
    return Vector((x * KS, y * KS, z * KS))


def shot(t):
    """本編の秒 → (位置, 見る点, レンズ, ピントの点)"""
    nm = cut_of(t)
    if nm == "K1":                                  # 車内の全景：通路の奥から、立った人の目の高さで、ゆっくり前へ
        u = mj(t, 0.0, 3.7); p = lerpv((-1.30, -2.75, 1.48), (-1.32, -2.05, 1.44), u); tg = lerpv((-0.70, 3.0, 1.05), (-0.60, 2.4, 1.02), u)
        return p, tg, 22.0, hp0
    if nm in ("K2", "K3"):                          # 音楽を聴いている人（L4）・動画を見ている人（L2）：右の肩ごしに、画面と耳のイヤホン
        return ots("L4", 3.7, 2.2, t) if nm == "K2" else ots("L2", 5.9, 1.7, t)
    if nm == "K4":                                  # 車両の端の高い所から全体（「何十組」）
        u = mj(t, 7.6, 5.1); p = lerpv((-0.62, 6.75, 2.12), (-0.66, 6.35, 2.05), u); tg = lerpv((-1.12, -0.6, 0.62), (-1.10, -0.9, 0.70), u)
        return p, tg, 17.0, V3(-1.15, 2.5, 0.9)
    if nm == "K5":                                  # 主人公（右前から）。曲に合わせて小さくうなずく
        u = mj(t, 12.7, 4.4); p = hp0 + lerpv((-1.50, 0.46, 0.05), (-1.38, 0.42, 0.04), u); tg = hp0 + V3(0.0, 0.04, -0.25)
        return p, tg, 34.0, hp0
    if nm == "K6":                                  # 主人公と隣の人（P1）。二人の間へ寄る
        u = mj(t, 17.1, 4.5); mid = (hp0 + HEADS["P1"]) * 0.5
        p = mid + lerpv((-1.85, 0.02, -0.02), (-1.55, 0.02, -0.04), u); tg = mid + V3(0.0, 0.0, -0.16)
        return p, tg, 30.0, mid
    if nm in ("K7", "K8"):                          # 右の列を斜めに（主人公が手前）。K7：拍に合わせて一斉に踊り出す → K8：同じ向きで、現実（踊るのは主人公だけ）
        u = mj(t, 21.6, T_K7B - 21.6) if nm == "K7" else 1.0 + 0.4 * mj(t, dance.T_FANT1, 32.8 - dance.T_FANT1)
        p = lerpv((-1.58, -0.72, 1.15), (-1.48, -0.60, 1.14), u); tg = V3(0.0, 0.85, 1.00)
        return p, tg, 22.0, hp0 + V3(0, 0.3, -0.1)
    if nm == "K7b":                                 # 通路の端の低い所から見上げる：両側の全員が手とスマホを頭の上で振り、決めポーズ
        u = mj(t, T_K7B, dance.T_FANT1 - T_K7B); p = lerpv((-1.13, -2.88, 1.30), (-1.13, -2.42, 1.30), u); tg = lerpv((-1.10, 3.5, 1.42), (-1.10, 3.5, 1.40), u)
        return p, tg, 17.0, V3(-1.1, 1.0, 1.3)
    if nm == "K9":                                  # 主人公（冒頭のBと同じ向き）。途切れたら、ゆっくり寄る
        s = mj(t, T_DROP + 0.35, 1.8); base = hp0 + V3(-1.48, 0.44, 0.04); tgt = hp0 + V3(0.0, 0.04, -0.25)
        p = base.lerp(tgt, 0.12 * s); return p, tgt, 34.0, hp0
    if nm == "K10":                                 # 左前から：手前に左手のスマホ（画面の光が顔に返る）、上に左耳のイヤホン。ピントをスマホ→イヤホンへ（つないだ二台）
        u = mj(t, 42.7, 8.1); ph_ = V3(*PHONE_W)
        p = hp0 + lerpv((-0.82, -0.62, -0.20), (-0.74, -0.56, -0.20), u); tg = ph_.lerp(BUD_L, 0.45)
        fp = ph_.lerp(BUD_L, mj(t, 44.6, 1.6))
        return p, tg, 40.0, fp
    if nm == "K11":                                 # 床の高さ：通路を歩いてくるまるロボ（主人公の足もと）
        r = robot_pos(t); p = V3(-1.20, 0.55, 0.16); tg = V3(r.x * 0.6 - 1.10 * 0.4, r.y, 0.20)
        return p, tg, 26.0, r + V3(0, 0, 0.18)
    if nm == "K12":                                 # ボタンの左前の低い所から。止まったあと、ゆっくり寄る
        s = mj(t, T_FREEZE + 1.0, 4.0); c0 = V3(CAM12[0], CAM12[1], 0.20); tgt0 = BTN + V3(0.0, -0.05, 0.16)
        p = c0.lerp(tgt0, 0.30 * s); return p, tgt0, 24.0, BTN + V3(0, 0, 0.2)
    if nm == "K13":                                 # 止まった車内：カメラだけが動く（揺れたままのつり革、日差しの中に浮いたままのほこり）
        u = mj(t, 64.0, 4.7); p = lerpv((-1.18, 4.9, 1.30), (-1.16, 3.4, 1.26), u); tg = lerpv((-0.30, 2.6, 1.35), (-0.40, 1.4, 1.05), u)
        return p, tg, 24.0, V3(-0.6, 2.4, 1.2)
    c1p, c1t, c1l = C1_CAM if C1_CAM else (V3(-0.95, -0.62, 1.2), V3(*PHONE_W), 85.0)
    if nm == "K14":                                 # ボタンから降りて主人公の前へ → カメラはまるロボから、スマホの高さへ上がる
        r = robot_pos(t); u = mj(t, 70.4, 4.3)
        mid_p = V3(-1.10, -0.85, 1.05)
        p = lerpv(r + V3(-0.80, -0.95, 0.20), mid_p, u); tg = lerpv(r + V3(0.10, 0.10, 0.17), c1t, u)
        return p, tg, lerp_f(26.0, 34.0, u), lerpv(r + V3(0, 0, 0.17), c1t, u)
    u = mj(t, 74.7, 6.0)                            # K15：スマホの画面へ寄り、第3章 C1 の最初の絵（左上から望遠）にぴたりと重ねる
    p = lerpv(V3(-1.10, -0.85, 1.05), c1p, u); tg = c1t
    return p, tg, lerp_f(34.0, c1l, u ** 1.5), c1t


def lerp_f(a, b, u): return a + (b - a) * u


# ---------------------------------------------------------------- 毎コマの計算（冒頭と同じ物理：電車の揺れ・乗客・つり革・ほこり・流れる景色）
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
bk = hrig.Baker()
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
ex = {}; hero_anim.pose_at(hero, hero_anim.T_DROP + 2.0, 0.0, hero_bud_rest, ex)
rig_h = hero["rig"]; rig_h.fk()
tip = (rig_h.tail_pos("index_03.R") + rig_h.tail_pos("middle_03.R")) / 2
hero["touch_fix"] = (rig_h.posed_point("head", hero_bud_rest) + np.array([-0.006, -0.004, -0.010])) - tip
hero["sp_neck"] = motion.Spring(2.2, 0.5); hero["sp_head"] = motion.Spring(3.0, 0.45); hero.pop("hair_st", None)
cam.rotation_mode = "QUATERNION"; shots = []
# 描くコマだけ記録する（23人×1944コマを全部記録すると、メモリが足りない）。主人公のばね（うなずき・髪）は毎コマ計算して、状態をつなぐ
if A.dry == 2: KEYS = {N}                                                     # 組むだけ（第3章の電車の場面が、止まった最後のコマにカメラを置く）
elif A.dry: KEYS = set(int(x) for x in A.dry_frames.split(","))
else: KEYS = set(range(max(1, f0 - 1), min(N, f1 + 1) + 1))
F_LAST = max(f for f in range(1, N + 1) if (f - 1) / FPS < T_FREEZE)          # 時間が止まる直前のコマ（ここの姿のまま止まる）
eyes_last = (0.0, 0.0)
for f in range(1, N + 1):
    t = (f - 1) / FPS
    frozen = t >= T_FREEZE
    need = f in KEYS
    if not frozen:
        ex = {}
        hero_anim.pose_at(hero, t - T_REL, float(sway[f - 1]), hero_bud_rest, ex)
        eyes_last = (ex["blink"], ex["wide"] * (1 - ex["blink"]))
        if need or f == F_LAST:
            for n, person in P.items():
                if n == "H": continue
                people.base_pose(person, t, sway=float(SWAY[n][f - 1]))
    if need:
        fz = F_LAST if frozen else f                                              # 止まったあとは、止まった瞬間の値
        bk.pose(hero["rig"], f)
        for sd in ("L", "R"):
            sk = hero["objs"]["eye." + sd].data.shape_keys
            bk.put(sk, 'key_blocks["blink"].value', 0, f, eyes_last[0]); bk.put(sk, 'key_blocks["wide"].value', 0, f, eyes_last[1])
        for n, person in P.items():
            if n != "H": bk.pose(person["rig"], f)
        for st_ in STRAPS:
            ax_, ay_ = st_["ang"][min(fz - 1, len(st_["ang"]) - 1)]
            bk.put(st_["ob"], "rotation_euler", 1, f, ax_); bk.put(st_["ob"], "rotation_euler", 0, f, ay_)
        for d_ in DUST:
            pp, rr = d_["traj"][fz - 1]
            for i in range(3): bk.put(d_["ob"], "location", i, f, d_["c0"][i] + pp[i])
            bk.put(d_["ob"], "rotation_euler", 2, f, rr)
        bk.put(FLOW, "location", 1, f, -V_TRAIN * (fz - 1) / FPS)
        s_p = 2.6 * (1 - (1 - min(max((t - T_FREEZE) / 0.6, 0.0), 1.0)) ** 3) if t >= T_FREEZE else 0.0
        for i in range(3): bk.put(pulse, "scale", i, f, max(s_p, 1e-4))
        bk.put(glow.data, "energy", 0, f, 45.0 * mj(t, T_FREEZE, 0.3))
        g_ = mj(t, T_FREEZE, 0.35)
        bk.put(scene.node_tree, 'nodes["%s"].inputs["Saturation"].default_value' % hsv.name, 0, f, 1.0 - 0.45 * g_)
        bk.put(scene.node_tree, 'nodes["%s"].inputs["Fac"].default_value' % cb_.name, 0, f, 0.6 * g_)
    nm = cut_of(t)
    if not shots or shots[-1][1] != nm: shots.append([round(t, 3), nm])
bk.write(interp="LINEAR")
# 画面の入れ替え：材質ごとの中の節点の木は、どれも同じ名前（Shader Nodetree）なので、まとめ書き（Baker）を使わず直接キーを打つ
for m_ in same_mix:
    sock = m_.node_tree.nodes["Same song"].inputs[0]
    for t_, v_ in ((T_SAME0, 0.0), (T_SAME0 + 0.15, 1.0), (T_SAME1, 1.0), (T_SAME1 + 0.15, 0.0)):
        sock.default_value = v_; sock.keyframe_insert("default_value", frame=t_ * FPS + 1)
# ---- 止まった姿のスマホから、第3章 C1 の最初の絵を決める（ch03_train.py と同じ式：画面の向き45°を左へ傾けた所、0.95m、85mm）
scene.frame_set(N); bpy.context.view_layer.update()
M_ph = hero["phone"].matrix_world.copy(); C_ph = M_ph.translation.copy()
n_scr = (M_ph.to_3x3() @ Vector((0, 0, 1))).normalized(); up_ph = (M_ph.to_3x3() @ Vector((0, 1, 0))).normalized()
d_scr = (n_scr * math.cos(math.radians(45)) + Vector((0, -1, 0)) * math.sin(math.radians(45))).normalized()
C1_CAM = (C_ph + d_scr * 0.95, C_ph + up_ph * 0.01, 85.0)
print("C1 CAM", tuple(round(v, 3) for v in C1_CAM[0]), flush=True)
bkc = hrig.Baker()                                                            # カメラは全コマ（軽い）
for f in range(1, N + 1):
    t = (f - 1) / FPS; p, tg, lens, fp = shot(t); q = (Vector(tg) - Vector(p)).to_track_quat("-Z", "Y")
    for k in range(3): bkc.put(cam, "location", k, f, p[k])
    for k in range(4): bkc.put(cam, "rotation_quaternion", k, f, q[k])
    bkc.put(cd_, "lens", 0, f, lens); bkc.put(cd_, "dof.focus_distance", 0, f, max((Vector(fp) - Vector(p)).length, 0.05))
bkc.write(interp="LINEAR")
for o_ in [cam]:
    if o_.animation_data and o_.animation_data.action:                         # カットの切り替えは1コマで
        for fc in o_.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
log = dict(fps=FPS, frames=N, t_drop=T_DROP, t_back=T_BACK, t_freeze=T_FREEZE, t_land=T_LAND, same=[T_SAME0, T_SAME1], shots=shots,
           events=[dict(e, t=round(e["t"] * SQK, 4)) for e in plan.events])
json.dump(log, open(os.path.join(A.out, "ch0102_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, default=float)
print("BAKED", round(time.time() - t0, 1), "freeze %.2f" % T_FREEZE, flush=True)
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
        scene.render.filepath = os.path.join(A.out, getattr(A, "vprefix", "") or "ch0102_")
    bpy.ops.render.render(animation=True)
print("SEQ DONE", round(time.time() - t0, 1), flush=True)
