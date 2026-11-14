# ロボットではありません回：3D の場面を声の時刻に合わせて動かして描く
# blender -b --factory-startup --python scenes.py -- <場面> <出力フォルダ> [samples] [--res W H] [--step N] [--frames A B] --tex <絵のフォルダ> --scr <画面のコマのフォルダ>
#   場面：s04（まるロボが押す）
#   出力：<場面>_####.png と <場面>_log.json（t0・t1・fps・frames・効果音 events）
# 決まり：3D の中に字を書かない（札・吹き出しは 2D）。まるロボは喋らない・腕はない（マウスは体で押す）
import os, sys
ARGS = sys.argv[sys.argv.index("--") + 1:]
_ANIM_HERE = os.path.dirname(os.path.abspath(__file__))
def opt(name, default):
    return [type(d)(ARGS[ARGS.index(name) + 1 + k]) for k, d in enumerate(default)] if name in ARGS else default
TEX, = opt("--tex", [os.path.join(_ANIM_HERE, "..", "storyboard", "tex")])
SCR, = opt("--scr", [""])
KEY, OUTDIR = ARGS[0], ARGS[1]
N_SAMPLES = int(ARGS[2]) if len(ARGS) > 2 and ARGS[2].isdigit() else 32
RESX, RESY = opt("--res", [1920, 1080])
STEP, = opt("--step", [1])
FR = opt("--frames", [0, 0])
TRACK_ONLY = "--track-only" in ARGS                 # 描かずに、log（場所の記録・効果音）だけ書き直す
exec(open(os.path.join(_ANIM_HERE, "common.py"), encoding="utf-8").read())


def span(sc_):
    t0, t1 = SCENE_T[sc_]
    CLOCK["T0"] = t0
    return t0, t1


def find_screen():
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.active_material and o.active_material.name.startswith("img_scr"): return o
        if o.type == 'MESH' and o.active_material and "scr_" in o.active_material.name: return o


def find_maru():
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and o.children and any(c.type == 'EMPTY' and any(g.type == 'MESH' and g.active_material and g.active_material.name.startswith("maru_white") for g in c.children) for c in o.children):
            return o


def find_mouse():
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and any(c.type == 'MESH' and c.active_material and c.active_material.name.startswith("mouse") for c in o.children):
            return o


# ---------------- S04 まるロボが押す：体でマウスを押して矢印をまっすぐ → 跳び乗ってカチッ → くるくる → 絵のテスト → びくっと後ずさる
def s04():
    t0, t1 = span("S04")
    M0 = (0.98, 0.2, 0.75); R0 = (0.98, 0.0, 0.75)                   # パソコンの右の空いた所（マウスがパソコンに乗り上げない）
    room_shot("scr_check", maru_loc=R0, face=-10, mouse_loc=M0)
    seq_screen(find_screen(), SCR, "s04")
    mr = Maru(find_maru()); ms = find_mouse()
    TRACK["maru"] = (mr.body, 0.12)                                  # 体の少し上（札のしっぽの先）
    click = said("カチッ"); a0, a1 = said("マウスで") + 0.3, click - 0.75   # screens.py と同じ時刻
    test_t = said("代わりに") - 0.35   # 前の文の声が終わってすぐ（ピッが声と重ならない）
    M1 = (M0[0] - 0.24, M0[1] + 0.11, M0[2])                       # 矢印の動き（左上へ）と同じ向きにマウスが動く
    off = (0.0, -0.2, 0.0)
    # 04-01：やる気。小さく 2 回跳ねる
    mr.at(t0, R0, -10, 0)
    mr.hop(s("04-01") + 0.6, 0.25, 0.35); mr.hop(s("04-01") + 1.1, 0.25, 0.35)
    ev(s("04-01") + 0.6 + 0.35, "step"); ev(s("04-01") + 1.1 + 0.35, "step")
    # 04-02：体で押して、まっすぐ（等しい速さで）
    dirz = math.degrees(math.atan2(M1[1] - M0[1], M1[0] - M0[0])) - 90
    mr.at(a0 - 0.4, face=dirz)
    key(ms, "location", f(a0), M0, "LINEAR"); key(ms, "location", f(a1), M1, "LINEAR")
    mr.at(a0, tuple(M0[i] + off[i] for i in range(3)), interp="LINEAR", hold=False)
    R1 = tuple(M1[i] + off[i] for i in range(3))
    # 押している向きに体を回した分、後ろへ回り込む（マウスの真後ろ）
    import mathutils
    back = mathutils.Vector((M0[0] - M1[0], M0[1] - M1[1], 0)).normalized() * 0.2
    R1 = (M1[0] + back.x, M1[1] + back.y, M1[2])
    mr.at(a0 + 0.01, (M0[0] + back.x, M0[1] + back.y, M0[2]), interp="LINEAR", hold=False)
    mr.at(a1, R1, interp="LINEAR", hold=False)
    for k in range(int((a1 - a0) / 0.3)):                           # 押すときの小さな足どり
        tt = a0 + k * 0.3; mr.hop(tt, 0.05, 0.3); STEPS.append(round(tt + 0.3, 3))
    key(ms, "location", f(a1 + 0.5), M1, "CONSTANT")
    # 止まって、マウスのボタンへ跳び乗る（カチッ）
    up = 0.42                                                        # マウスの上（体の大きさ 0.22 に対して）
    mr.at(click - 0.55, R1); mr.at(click - 0.05, (M1[0], M1[1] - 0.02, M1[2]))
    key(mr.body, ("location", 2), f(click - 0.55), mr.z0)
    key(mr.body, ("location", 2), f(click - 0.3), mr.z0 + 0.9)
    key(mr.body, ("location", 2), f(click), mr.z0 + up)
    key(mr.body, ("location", 2), f(click + 0.08), mr.z0 + up - 0.08)   # 押しこむ
    key(mr.body, ("location", 2), f(click + 0.2), mr.z0 + up)
    ev(click - 0.55, "jump"); ev(click, "click")
    # 04-03：見上げて待つ（くるくる）
    mr.at(s("04-03"), look=12); mr.tilt(s("04-03") + 0.8, 10, 0.4)
    # 04-04：絵のテストがぱっ → びくっと跳ねて、マウスから降りて後ずさる
    ev(test_t, "pop_ui")
    key(mr.body, ("location", 2), f(test_t + 0.05), mr.z0 + up)
    key(mr.body, ("location", 2), f(test_t + 0.25), mr.z0 + up + 0.7)
    key(mr.body, ("location", 2), f(test_t + 0.5), mr.z0)
    mr.at(test_t + 0.05, (M1[0], M1[1] - 0.02, M1[2])); mr.at(test_t + 0.5, (M1[0] + 0.12, M1[1] - 0.26, 0.75), face=-25, look=14)
    mr.tilt(test_t + 0.05, 0, 0.2)
    mr.glow(test_t + 0.1, 0.9, 1.8, 0.15)
    ev(test_t + 0.12, "pi"); ev(test_t + 0.5, "land")
    mr.at(test_t + 1.6, (M1[0] + 0.3, M1[1] - 0.4, 0.75)); mr.at(test_t + 1.6, face=-30)   # 少し後ずさる
    for k in range(3): mr.hop(test_t + 0.75 + k * 0.28, 0.05, 0.28); STEPS.append(round(test_t + 1.03 + k * 0.28, 3))
    # 04-05：テストをのぞきこむ・首をかしげる
    mr.at(s("04-05") + 0.5, look=10); mr.tilt(s("04-05") + 1.0, -12, 0.4); mr.tilt(s("04-05") + 3.5, 12, 0.5)
    mr.glow(s("04-05") + 0.3, 1.8, 1.2, 0.5)
    # 04-06：怪しまれて、しょんぼり（下を向いて、光を弱く）
    mr.at(s("04-06") + 0.8, look=-6); mr.tilt(s("04-06") + 0.8, 6, 0.6)
    mr.glow(s("04-06") + 0.8, 1.2, 0.4, 0.8); mr.blink(s("04-06") + 2.5, 0.4)
    ev(s("04-06") + 0.9, "down")
    return t0, t1


t0, t1 = globals()[KEY]()
if "--dbg" in ARGS: exec(open(ARGS[ARGS.index("--dbg") + 1]).read()); raise SystemExit
bpy.context.view_layer.update()
render(KEY, t0, t1, OUTDIR, N_SAMPLES, (RESX, RESY), STEP, FR if FR != [0, 0] else None)
print("DONE", KEY, t0, t1)
