# 4本目：簡単なまるロボ（絵コンテ用）を隠し、本物のまるロボ（maru_real）を同じ所・向き・大きさに置いて、marumotion の予定で動かす
#   2026-11-17 ユーザー「本物に替えて描き直す」。決まり：references/maru_walk.md。表：episodes/ep04_robot/絵コンテ表_本物.md
#   使い方（clip_anim.py・scenes.py・look の台本が exec のあとで呼ぶ）：
#     h, C, p = swap(root, T0)        # root＝簡単なまるロボの親。T0＝このカットの 0 コマ目の時刻
#     PLANS[名前](p, C, ...)            # 予定を書く（時刻は場面の時刻。C.go(p, t) でその時刻まで待つ）
#     finish(h, p, T0, T1)              # 毎コマを当て、足音を EVENTS へ
#   予定の座標＝置き場所から見た座標（大きさ 1 の m）。C.xy(場面の点)・C.hd(簡単なまるロボの face 度) で直す
import os, sys, math
import bpy
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts"),
           os.path.join(_HERE, "..", "..", "ep01_earphone", "stage", "maru"), _HERE):
    _p = os.path.abspath(_p)
    if os.path.isdir(_p) and _p not in sys.path: sys.path.insert(0, _p)
import marumotion as mm
import maru_real as MR

MOTION_EV = ("step", "jump", "land")
BEEPS = ("beep_yes", "beep_no", "beep_surprise", "beep_happy", "beep_think", "beep_question", "beep_hello", "beep_present", "ding", "sigh", "zoom")
BEEP_SAME = {"beep_surprise": "pi", "sigh": "down"}   # 動きの電子音と、前から付けている同じ役の音            # 簡単なまるロボのために書いた足音・跳ぶ音（予定から出し直すので消す）


def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out


class Conv:
    def __init__(self, loc, face, scale, T0):
        self.loc, self.face, self.s, self.T0 = Vector(loc), face, scale, T0
        self.heading = face + 180.0                  # 簡単なまるロボは −Y が正面、本物は +Y が正面

    def xy(self, w):
        """場面の点 → 予定の座標"""
        d = (Vector((w[0], w[1], 0)) - Vector((self.loc.x, self.loc.y, 0))) / self.s
        a = -math.radians(self.heading)
        return (d.x * math.cos(a) - d.y * math.sin(a), d.x * math.sin(a) + d.y * math.cos(a))

    def z(self, wz): return (wz - self.loc.z) / self.s

    def hd(self, face_deg):
        """簡単なまるロボの face（場面の度）→ 予定の向き（度）"""
        return face_deg - self.face

    def go(self, p, t):
        """場面の時刻 t まで待つ（もう過ぎていれば何もしない）"""
        dt = (t - self.T0) - p.t
        if dt < -0.15 and os.environ.get("MARU_DEBUG"): print("PLAN_LATE %.2f 予定より %.2f 秒おそい" % (t, -dt))
        if dt > 1e-3: p.wait(dt)
        return p

    def idle_to(self, p, t):
        dt = (t - self.T0) - p.t
        if dt < -0.15 and os.environ.get("MARU_DEBUG"): print("PLAN_LATE %.2f 予定より %.2f 秒おそい" % (t, -dt))
        if dt > 0.3: p.idle(dt)
        elif dt > 1e-3: p.wait(dt)
        return p


PLACE_LAST = {"c_s12a": 20.0}   # 置き場所を、最初のコマでなく着地したあと（この秒）の簡単なまるロボから取るカット（上から降りてくる所）
GROUND = {}      # カット名 → 0 コマ目の足の高さ（場面の m）。上から降りてくる所など


def swap(root, T0, frame=0, name=""):
    """簡単なまるロボを隠し、同じ所に本物を置く。返す：(handle, Conv, Plan)"""
    sc = bpy.context.scene
    if name in PLACE_LAST: frame = sc.frame_end if sc.frame_end > 1 else int(round(PLACE_LAST[name] * mm.FPS))
    sc.frame_set(frame)
    M = root.matrix_world.copy(); loc = M.translation.copy()
    face = math.degrees(M.to_euler().z); scale = M.to_scale().x
    for o in hier(root):
        o.hide_render = True; o.hide_viewport = True
        if o.animation_data and o.animation_data.action:       # 隠したまま（キーで出てこないように）
            for fc in list(o.animation_data.action.fcurves):
                if fc.data_path == "hide_render": o.animation_data.action.fcurves.remove(fc)
    C = Conv(loc, face, scale, T0)
    if os.environ.get("MARU_DEBUG"): print("PLAN_PLACE %s loc=(%.2f, %.2f, %.2f) face=%.0f s=%.2f" % (name, loc.x, loc.y, loc.z, face, scale))
    h = MR.place(loc=tuple(loc), heading=C.heading, scale=scale, name="maru_real")
    p = mm.Plan(pos=(0.0, 0.0), heading=0.0, ground=GROUND.get(name, 0.0) / scale)
    return h, C, p


def C_heading(h): return math.degrees(h.parent.matrix_world.to_euler().z)


def finish(h, p, T0, T1, EVENTS, STEPS):
    """毎コマを当てる。簡単なまるロボ用の足音・跳ぶ音を消し、予定の足音を入れる"""
    off = T0 - getattr(p, "T0_world", T0)        # ひと続きの予定（前のカットから続く）なら、このカットの頭までの時間
    n = int(round((T1 - T0) * mm.FPS)) + 2
    if p.t < (T1 - T0) + off: p.idle((T1 - T0) + off - p.t + 0.1)
    if os.environ.get("MARU_DEBUG"):
        print("PLAN_END %.2f / %.2f" % (T0 - off + p.t, T1))
        for e in p.events: print("PLAN_EV %.2f %s %.2f" % (T0 - off + e["t"], e["kind"], e.get("strength", 1.0)))
    k0 = int(round(off * mm.FPS))
    frames = mm.simulate(p, fps=mm.FPS, t_end=off + n / mm.FPS)
    h.bake(frames[k0:k0 + n], f0=0)
    if getattr(p, "hide_until", None) is not None:
        fh = int(round((p.hide_until - off) * mm.FPS))
        for o in MR.hier(h.root):
            if o.hide_render: continue
            o.hide_render = True; o.keyframe_insert("hide_render", frame=0)
            o.hide_render = False; o.keyframe_insert("hide_render", frame=max(1, fh))
            for fc in o.animation_data.action.fcurves:
                if fc.data_path == "hide_render":
                    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
    if os.environ.get("MARU_DEBUG"):
        for nm, fr in (("START", frames[k0]), ("END", frames[min(k0 + n - 3, len(frames) - 1)])):
            M = h.parent.matrix_world; r = M @ Vector(fr["root"]); hd_w = math.degrees(fr["psi"]) + C_heading(h)
            print("PLAN_%s world=(%.2f, %.2f, %.2f) heading=%.0f" % (nm, r.x, r.y, r.z, hd_w))
    EVENTS[:] = [e for e in EVENTS if e[1] not in MOTION_EV]; STEPS[:] = []
    for e in p.events:
        t, kind, st = e["t"], e["kind"], e.get("strength", 1.0)
        tt = round(T0 - off + t, 3)
        if not (T0 - 0.05 <= tt <= T1): continue
        if kind == "step": STEPS.append(tt) if st >= 0.6 else EVENTS.append((tt, "step", 0.5))
        elif kind == "step_turn": EVENTS.append((tt, "step", 0.45))
        elif kind == "takeoff": EVENTS.append((tt, "jump", 0.6))
        elif kind == "land": EVENTS.append((tt, "land", 0.7))
        elif kind in BEEPS:
            same = BEEP_SAME.get(kind)                 # v14 で決まった音（pi・down）がすぐ近くにあれば、そちらを残す
            if same and any(e[1] == same and abs(e[0] - tt) < 0.8 for e in EVENTS): continue
            EVENTS.append((tt, kind, 0.8))
    return frames


# ================================================================ 予定（絵コンテ表_本物.md の順）
#   引数：p（予定）・C（座標と時刻）・g（台本の globals：said・s・cell_c・T0・T1・ms など）
def tilt(p, t0, deg, dur=0.4, hold=0.8):
    """首をかしげる（体ごと横へ傾ける）"""
    p.layer(t0, t0 + dur + hold + dur, lambda t, a=t0: {"roll": deg * mm.env(t, a, dur, hold, dur)})


def glow(p, t0, k, up=0.2, hold=0.8, down=0.5):
    p.layer(t0, t0 + up + hold + down, lambda t, a=t0: {"light": k * mm.env(t, a, up, hold, down)})


def P_s01(p, C, g):
    s, said = g["s"], g["said"]
    C.idle_to(p, s("01-02") + 1.0); p.hops(n=2, height=0.06)
    C.idle_to(p, s("01-03") + 0.1)
    ms = g["ms"]; m = C.xy(ms.location)
    p.turn_to(toward=m); p.walk_to(tuple(mm.np.array(m) * 0.55))   # マウスのそばまで 2 歩 → 体で押す（マウスは台本が動かす）


def P_s02a(p, C, g):
    s = g["s"]
    C.idle_to(p, s("02-01") + 1.0); p.look(0, 14, hold=0.4)
    for k in range(4): p.blinks.append(s("02-01") + 1.6 + k * 0.3 - C.T0)
    C.idle_to(p, s("02-04") + 0.4); p.confused()


def P_s03(p, C, g):
    """欄の前で、右へ少し歩いて（足踏みで向きを変えてから）→ 正面へ振り向く → 「なぜ？」で首をかしげる"""
    s = g["s"]
    C.idle_to(p, s("03-02") + 0.1)
    p.walk_to((-0.35, 0.0)); p.wait(0.2)         # 画面の右へ（予定の −x：正面がカメラ向き）
    C.idle_to(p, s("03-03")); p.turn_to(0.0)     # 正面へ
    C.idle_to(p, s("03-04") + 0.2); p.confused()



def P_s05x(p, C, g):
    said = g["said"]; m0 = said("今度は") + 0.4
    C.idle_to(p, m0 - 0.3); p.look(0, -10, hold=0.3)
    p.layer(m0 + 0.1, m0 + 6.0, lambda t, a=m0 + 0.1 - C.T0: {"pitch": 10.0 * mm.mj(t, a, 0.5)})   # 首を前に伸ばしてのぞく


def P_s05b(p, C, g):
    T0 = g["T0"]; p.surprise(at=0.2); p.wait(0.6); p.hops(n=1, height=0.08)


def P_s06b(p, C, g):
    T0 = g["T0"]
    C.idle_to(p, T0 + 1.0); p.turn_to(-30); p.wait(0.4); p.turn_to(30); p.wait(0.4); p.turn_to(0); tilt(p, p.t + 0.2, 12)


def P_s08(p, C, g):
    T0, T1 = g["T0"], g["T1"]
    C.idle_to(p, T0 + 0.8); p.look(0, 10, hold=1.0)
    p.turn_to(35); p.look(0, 12, hold=0.8)


def P_s11(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 0.6); p.look(0, 8, hold=0.3); glow(p, T0 + 0.8 - C.T0, 1.0, hold=2.0)
    p.tracks["iris"].set(T0 + 0.8 - C.T0, 0.3, 0.12)


def P_idle_look(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 1.0); p.look(0, 8, hold=0.5)


def P_s11d(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 0.8); p.look(30, 6, hold=0.8); p.look(-30, 6, hold=0.8); p.look(0, 8, hold=0.3); tilt(p, p.t, 12)


def P_s12a(p, C, g):
    s, said = g["s"], g["said"]
    tS = said("では、画面の中に")
    # 上から降りてくる：高い所（GROUND）に立っていて、字幕の頭で、いまの場所へ跳び降りて脚で受け止める
    p.jump_to((0.0, 0.0), z1=0.0)                # カットの頭から、画面の外で跳ぶ（見る・しゃがむ・落ちる）
    t_land = C.T0 + p.t - 0.9                    # だいたいの着地（跳ぶ動きの終わりの手前）
    for e in p.events:
        if e["kind"] == "land": t_land = C.T0 + e["t"]
    g["EVENTS"][:] = [e for e in g["EVENTS"] if e[1] != "dive"]; g["ev"](t_land - 0.55, "dive")
    for e in p.events:                           # 跳ぶまでは描かない（高い所で立っている・しゃがむのが画面の上に見えるため）
        if e["kind"] == "takeoff": p.hide_until = e["t"] + 0.1; break   # 落ちてくる音は、画面に入るころから
    C.idle_to(p, s("12-01b"))
    p.turn_to(50); p.wait(0.3); p.turn_to(-50); p.wait(0.3); p.turn_to(0)
    C.idle_to(p, said("門番です") - 0.6); p.turn_to(25); p.look(0, 16, hold=0.4)


def P_s13(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 0.8); p.look(25, -12, hold=1.2); p.look(-20, -14, hold=1.0)


def P_s13d(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 1.8); p.look(0, -16, hold=3.5); glow(p, T0 + 2.3 - C.T0, -0.6, hold=3.2)


def P_s14(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 1.5); p.sigh()


def P_s15(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 1.1); p.look(0, 18, hold=0.2); p.hops(n=2, height=0.05)


def P_s16(p, C, g):
    s, T0 = g["s"], g["T0"]
    t2 = s("16-02") if "16-02" in g["T"] else T0 + 6
    C.idle_to(p, T0 + 1.0); p.look(0, -4, hold=0.5)
    C.idle_to(p, t2 + 0.3); p.look(0, 14, hold=0.5)
    C.idle_to(p, s("16-03") + 0.3); p.look(0, 2, hold=0.5)


S17_T0 = 414.04                              # c_s17a の頭。c_s17a・c_s17b・c_s18a は、ひと続きの予定（カットの切れ目で置き直さない）


def _s17_18(p, C, g, name):
    """床の左下から歩いてマス（2, 1）に乗る（青く光る）→（2, 0）→ 慎重に（3, 0）→ 端っこのマスの手前で止まる →
    見下ろす → 一歩乗る → 後ずさりで降りる → また半歩乗りかけて止まり、首をかしげる。座標は場面（世界）の点で書く"""
    import numpy as np
    s, said, cell_c = g["s"], g["said"], g["cell_c"]
    C.T0 = S17_T0; p.T0_world = S17_T0
    start = np.array(C.xy((-2.3, 1.3, 0.03))); tgt = np.array(C.xy(cell_c(2, 1))); d = tgt - start   # 左下の角（字幕にかからない所）から
    p.teleport(tuple(start), math.degrees(math.atan2(-d[0], d[1])))     # 0 コマ目から、マスの方を向いて立っている
    C.go(p, S17_T0 + 0.3)
    p.walk_to(tuple(tgt), speed=1.35)
    t_on = C.T0 + p.t - 0.3                                       # マスに乗った時刻 → マスが青く光る・ぽん（c_s17a）
    if name == "c_s17a":
        sel = [o for o in bpy.data.objects if o.active_material and o.active_material.name.startswith("cell_sel_a")]
        if sel:
            g["vis"](sel, g["T0"] - 1, False); g["vis"](sel, t_on, True)
            g["EVENTS"][:] = [e for e in g["EVENTS"] if not (e[1] == "pop_ui" and abs(e[0] - t_on) < 4)]; g["ev"](t_on + 0.05, "pop_ui", 0.25)   # 声と重なるので小さく（ずらすとマスが光る絵とずれる）
    p.wait(0.2); p.walk_to(C.xy(cell_c(2, 0)), speed=1.0)
    C.go(p, said("まるロボ、慎重に") - 0.1)
    p.walk_to(C.xy(cell_c(3, 0)), speed=0.9); p.look(0, -12, hold=0.3)
    p.walk_to(C.xy(EDGE_STOP), speed=0.9)        # 端っこのマスの手前へ。両足をそろえて止まる
    cx = EDGE_STOP[0]
    C.idle_to(p, said("このマス") - 0.3); p.look(0, -16, hold=0.6)
    C.idle_to(p, s("18-03") - 3.5); p.walk_to(C.xy((cx, EDGE_STOP[1] - 0.4, 0.03)), speed=0.6); p.wait(0.2)   # 乗る（「信号機の端っこが」のあいだ）
    p.back_to(C.xy(EDGE_STOP))                   # 降りる（後ずさり）
    C.idle_to(p, s("18-04") - 0.1); p.walk_to(C.xy((cx, EDGE_STOP[1] - 0.18, 0.03)), speed=0.5); p.confused()   # また乗りかけて止まる


def P_s17a(p, C, g): _s17_18(p, C, g, "c_s17a")
def P_s17b(p, C, g): _s17_18(p, C, g, "c_s17b")
def P_s18a(p, C, g): _s17_18(p, C, g, "c_s18a")


EDGE_STOP = (2.25, 5.65, 0.03)               # 端っこのマス（3, 1：y 4.0〜5.5）の手前。c_s17b の終わり＝c_s18a の始め


def P_s20e(p, C, g):
    T0 = g["T0"]; C.idle_to(p, T0 + 1.0); p.turn_to(20); p.look(0, 6, hold=0.5)


def P_s23(p, C, g):
    """10:28〜：眠そう（光とろん・ゆっくりまばたき）にカメラの方を向いて立っている → まばたき 2 回 → 足踏みでマウスの方へ向き →
    ふらふらしながらゆっくり歩いて押す → カチッ → はっと起きる → カメラへ向き直って 2 回はねる"""
    import numpy as np
    said, s = g["said"], g["s"]
    m_0, m_1 = said("次の夜") + 1.5, said("……あ、通りました") - 0.6; click = said("……あ、通りました") - 0.3
    start, end = np.array(C.xy((0.98 + 0.17, 0.2 - 0.08, 0.75))), np.array(C.xy((0.98 - 0.24 + 0.17, 0.2 + 0.11 - 0.08, 0.75)))
    d = end - start; hd_m = math.degrees(math.atan2(-d[0], d[1]))
    p.teleport(tuple(start), C.hd(0))                             # カメラの方を向いている（眠そうな目が見える）
    p.layer(0.0, click - C.T0 + 0.2, lambda t: {"light": -0.7, "iris": -0.14})
    for tt in (C.T0 + 0.4, C.T0 + 1.1): p.blinks.append(tt - C.T0)   # ゆっくり、重いまばたき 2 回
    p.layer(C.T0 + 0.5 - C.T0, C.T0 + 1.3 - C.T0, lambda t, a=0.5: {"pitch": 9.0 * mm.hump(t, a, 0.8)})   # こっくり
    C.go(p, m_0 - 1.2); p.turn_to(hd_m, step=0.24, gap=0.03)
    v = 1.25 * float(np.linalg.norm(d)) / max(1.0, (m_1 - 0.4) - (C.T0 + p.t))   # 歩き出し・止まりの遅れの分、少し速く
    p.walk_to(tuple(end), speed=v)               # 眠そうに、ゆっくり押して歩く（マウスは台本が同じ時刻に動かす）
    for k, tt in enumerate((said("……だいぶ") - 1.2, said("……だいぶ") - 0.5, said("……だいぶ") + 0.2)):
        tilt(p, tt - C.T0, 10 if k % 2 else -10, 0.35, 0.2)   # ふらふら
    C.go(p, click + 0.1); p.surprise()
    p.turn_to(C.hd(0), step=0.22, gap=0.03)
    C.go(p, s("23-04") + 0.8); p.hops(n=2, height=0.07)


GROUND["c_s12a"] = 7.0                # 7m 上から降りてくる。跳ぶまでは描かない（5m だと跳ぶ前の姿が画面の上に見えた）

PLANS = dict(c_s01=P_s01, c_s02a=P_s02a, c_s03=P_s03, c_s05x=P_s05x, c_s05b=P_s05b, c_s06b=P_s06b, c_s08e=P_s08, c_s08f=P_s08,
             c_s11=P_s11, c_s11b=P_idle_look, c_s11c=P_idle_look, c_s11d=P_s11d, c_s12a=P_s12a, c_s13a=P_s13, c_s13b=P_s13, c_s13d=P_s13d,
             c_s14=P_s14, c_s15a=P_s15, c_s15e=P_idle_look, c_s16=P_s16, c_s17a=P_s17a, c_s17b=P_s17b, c_s18a=P_s18a, c_s20e=P_s20e,
             c_s21b=P_idle_look, c_s21=P_idle_look, c_s22=P_idle_look, c_s22b=P_idle_look, c_s22c=P_idle_look, c_s23a=P_s23)


def P_s04(p, C, g):
    """0:44〜1:11：最初からマウスの真うしろで、マウスの方を向いている → やる気（2 回はねる）→ 同じ速さで歩いて押す →
    跳び乗ってカチッ → 見上げて首をかしげる → 絵のテストでびくっ → 跳び降りて後ずさる → のぞきこむ → しょんぼり"""
    import numpy as np
    s, said = g["s"], g["said"]
    M0 = (0.98, 0.2, 0.75); M1 = (M0[0] - 0.24, M0[1] + 0.11, M0[2])
    click = said("カチッ"); a0, a1 = said("マウスで") + 0.3, click - 1.75; test_t = said("代わりに") - 0.35   # scenes.py・screens.py と同じ
    m0, m1 = np.array(C.xy(M0)), np.array(C.xy(M1)); d = (m1 - m0) / np.linalg.norm(m1 - m0)
    BK = 0.2 / C.s                                                # マウスの真うしろ 0.2m（場面）
    hd = math.degrees(math.atan2(-d[0], d[1]))
    p.teleport(tuple(m0 - d * BK), hd)                            # 0 コマ目から、マウスのうしろでマウスの方を向いている
    C.idle_to(p, s("04-01") + 0.5); p.hops(n=2, height=0.06)
    C.go(p, a0 - 0.35)                                            # 体重を移す 0.25 秒の分、少し前から
    L = float(np.linalg.norm(m1 - m0)); v = 1.5 * L / max(0.5, a1 - a0)
    p.walk_to(tuple(m1 - d * BK), speed=v, a_up=6.0, a_dn=6.0)   # 押す：いきなり同じ速さに近く（マウスと一緒）
    C.go(p, click - 1.61)                                         # 跳び乗りは、見る→しゃがむ→跳ぶで約 1.6 秒。着地＝カチッ
    p.jump_to(tuple(m1), z1=0.42)                                # マウスのボタンへ跳び乗る（体の大きさ 1 でマウスの上は 0.42）
    C.idle_to(p, s("04-03")); p.look(0, 12, hold=0.4); tilt(p, s("04-03") + 0.8 - C.T0, 10)
    C.go(p, test_t + 0.05); p.surprise()
    off = np.array(C.xy((M1[0] + 0.12, M1[1] - 0.26, 0.75)))
    p.jump_to(tuple(off), z1=0.0)                                # 跳び降りる
    p.back_to(tuple(off + (np.array(C.xy((M1[0] + 0.3, M1[1] - 0.4, 0.75))) - off) * 0.6))
    C.idle_to(p, s("04-05") + 0.5); p.peer(dur=1.6); tilt(p, s("04-05") + 3.5 - C.T0, 10, 0.5)
    C.idle_to(p, s("04-06") + 0.8); p.sigh()


PLANS_SCENE = dict(s04=P_s04)


# ================================================================ 図の場面（look/<名前>_3d.py）
#   ちらっと見る所は look（目→胴のひねり 40° まで。足は動かさない）。向きを大きく変える所だけ turn_to（足踏み）
def _lk(p, C, t, yaw, pitch, hold=0.4):
    C.go(p, t); p.look(max(-40, min(40, yaw)), pitch, hold=hold)


def L_s06(p, C, g):
    t_diff, t_q, t_next = g["t_diff"], g["t_q"], g["t_next"]
    p.teleport((0.0, 0.0), C.hd(0)); p.look(0, 10, hold=0.2, at=0.2)
    _lk(p, C, t_diff, 40, 12); _lk(p, C, t_diff + 1.3, -40, 12); _lk(p, C, t_q - 0.2, 0, 8, 0.1)
    C.go(p, t_q); p.confused(); C.go(p, t_next + 0.1); p.hops(n=1, height=0.06)


def L_s07(p, C, g):
    G = lambda k: g[k]
    p.teleport((0.0, 0.0), C.hd(0)); p.look(0, 22, hold=0.2, at=0.2)
    _lk(p, C, G("t_who") + 0.2, 40, 10); _lk(p, C, G("t_who") + 2.6, -40, 10); _lk(p, C, G("t_two") - 0.2, 0, 22)
    _lk(p, C, G("t_known") + 0.2, 15, 24); _lk(p, C, G("t_other") + 0.2, -15, 24)
    C.go(p, G("t_unk") + 0.3); p.confused(); C.go(p, G("t_why")); tilt(p, p.t, 10)


def L_s08x(p, C, g):
    p.teleport((0.0, 0.0), C.hd(0)); p.look(0, 20, hold=0.2, at=0.2)
    _lk(p, C, g["t_many"] + 1.0, 35, 8); _lk(p, C, g["t_many"] + 2.6, -35, 8); _lk(p, C, g["t_same"] + 0.5, 0, 22)
    C.go(p, g["t_ok"]); p.hops(n=1, height=0.07)


def L_s09(p, C, g):
    T0 = g["T0"]
    p.teleport((0.0, 0.0), C.hd(0)); p.look(0, 20, hold=0.2, at=0.2)
    C.go(p, T0 + 1.3); p.turn_to(C.hd(35)); _lk(p, C, g["t_g"], -35, 18)          # 機械の方へ向く（足踏み）→ 板を見上げる
    C.go(p, g["t_998"] + 0.3); p.turn_to(C.hd(-35)); _lk(p, C, g["t_998"] + 3.0, 0, 22)
    C.go(p, g["t_so"]); p.turn_to(C.hd(0)); p.sigh()


def L_s10(p, C, g):
    T0 = g["T0"]
    p.teleport((0.0, 0.0), C.hd(20)); p.look(0, 12, hold=0.2, at=0.1)
    C.go(p, g["t_who"] - 0.6); p.turn_to(C.hd(0))
    _lk(p, C, g["t_who"] + 0.4, -40, 10); _lk(p, C, g["t_who"] + 1.6, 40, 10)     # 人・プログラムを見比べる
    C.go(p, g["t_res"] - 0.2); p.turn_to(C.hd(70)); p.look(0, 16, hold=0.3)        # プログラムの方へ
    C.go(p, g["t_hum"] - 0.2); p.turn_to(C.hd(-70)); p.look(0, 16, hold=0.3)       # 人の方へ
    C.go(p, g["t_wow"] - 1.6); p.turn_to(C.hd(10))
    C.go(p, g["t_wow"]); p.hops(n=2, height=0.08); glow(p, g["t_wow"] + 0.1 - C.T0, 1.6, hold=1.0)
    C.go(p, g["t_how"] - 0.3); p.turn_to(C.hd(0)); p.confused()


def L_s15(p, C, g):
    T0 = g["T0"]
    p.teleport((0.0, 0.0), C.hd(0)); p.look(0, 18, hold=0.2, at=0.2)
    _lk(p, C, T0 + 1.0, 25, 18); _lk(p, C, T0 + 2.4, 0, 18); _lk(p, C, T0 + 3.8, -25, 18)
    C.go(p, g["t_ok"] + 0.2); p.hops(n=1, height=0.05)
    _lk(p, C, g["t_rep"] + 0.5, 0, 20); C.go(p, g["t_sus"] + 0.1); p.confused()


def L_s19(p, C, g):
    G = lambda k: g[k]
    p.teleport((0.0, 0.0), C.hd(-50)); p.look(0, 10, hold=0.2, at=0.2)
    C.go(p, G("t_cant") + 0.1); p.turn_to(C.hd(0)); p.look(0, 18, hold=0.3)
    C.go(p, G("t_ask") + 0.4); p.turn_to(C.hd(50))
    C.go(p, G("t_no") - 0.9); p.turn_to(C.hd(-55)); C.go(p, G("t_no") + 0.5); p.confused()
    C.go(p, G("t_bel") + 0.3); p.turn_to(C.hd(50))
    C.go(p, G("t_res") + 0.3); p.turn_to(C.hd(-40))


def L_s20(p, C, g):
    G = lambda k: g[k]
    p.teleport((0.0, 0.0), C.hd(10)); p.look(0, 16, hold=0.2, at=0.2)
    C.go(p, G("t_25") + 0.2); p.turn_to(C.hd(-40)); p.look(0, 10, hold=0.2)
    C.go(p, G("t_chk") - 0.6); p.turn_to(C.hd(10)); p.look(0, 18, hold=0.2)
    C.go(p, G("t_click") + 1.8); p.hops(n=1, height=0.08); glow(p, G("t_click") + 1.8 - C.T0, 1.6, hold=1.0)
    C.go(p, G("t_go") - 0.4); p.turn_to(C.hd(-30))


def L_s22(p, C, g):
    p.teleport((0.0, 0.0), C.hd(0)); p.look(0, 14, hold=0.2, at=0.2)
    _lk(p, C, g["T0"] + 0.2, 30, 14); _lk(p, C, g["t_now"], -30, 14); _lk(p, C, g["t_ai"] + 0.3, 0, 26)
    _lk(p, C, g["t_few"] + 2.0, 35, 12); _lk(p, C, g["t_few"] + 3.6, -35, 12); C.go(p, g["t_few"] + 4.0); p.confused()


PLANS_LOOK = dict(s06=L_s06, s07=L_s07, s08x=L_s08x, s09=L_s09, s10=L_s10, s15=L_s15, s19=L_s19, s20=L_s20, s22=L_s22)
