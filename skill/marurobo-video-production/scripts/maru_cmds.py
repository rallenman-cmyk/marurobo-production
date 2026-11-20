# まるロボを「前と同じ書き方」で動かす共通の部品（2026-11-17、3本目で作成。4〜6本目も使える）
#   決まり：references/maru_walk.md（手で動かさない。marumotion の予定 → simulate → marurig）
#   体を置いて毎コマを当てる所は、共通の maru_real.py（place / Handle.bake）を使う。
#
#   前の回の場面は、mr = Maru(場所, 向き, s=大きさ)、mr.at(t, loc=, face=, look=)、mr.walk(t0, t1, a, b)、mr.hop(t) …
#   のように「声の時刻」で書いてある。この部品は、その命令をそのまま受け取ってためておき、最後に bake() で
#   時刻の順に marumotion の予定（Plan）へ並べる：
#     ・場所を変える（at の loc・walk）→ walk_to。着く時刻に間に合うように歩き出しを早める（ふつう 1.0m/s、だめなら急ぎ 1.3m/s）
#     ・向き（at の face）→ turn_to（足踏みで回る）。見上げ（at の look）→ look（目と胴。体ごと傾けない）
#     ・hop → hops（小さく跳ねる）。tilt → 首をかしげる（roll）。lean → 前後（pitch）。glow → アンテナの光
#     ・surprise / nod / shake / think / peer / sigh / look_around / confused / present / greet / awe / groove / rest / wake / hops
#       → 予定の気持ちの動き。run・back・jump も（動きの一覧と見え方は references/maru_motions.md）
#     間に合わなかった動きは LATE に入る（名前, 遅れた秒）。必ず見て、場面の時刻か動きを直す
#   足音：予定の step・step_turn の時刻を steps に。跳ぶ・着く音と気持ちの動きの電子音（beep_…）は events に「maru:種類:強さ」で入れる（組み立てで maru_sfx.make(種類, 強さ)）
#
#   使い方（Blender の中）：
#     import maru_cmds as MC
#     mr = MC.Maru(loc=(x, y, z), face=度, s=0.7, face_offset=180)   # face_offset：その回の「向き 0」が本物の前（+Y）から何度か。
#                                                                    # 3〜6本目の簡単な maru() は前が −Y なので 180
#     mr.walk(...); mr.at(...); ...
#     MC.bake_all(t_end, T0=場面の 0 コマ目の時刻, fps=24, steps=STEPS, events=EVENTS)
#   mr.torso：体の中心（帽子・札を付ける親）。mr.handle：maru_real の Handle（real＝本物かどうか）
import copy, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import marumotion as mm
import maru_real as MR

LATE = []
ALL = []


def _plan_util():
    """QR回で足した動き（よろける・長くかしげる）：episodes/ep02_qr/pc_kit/qr/plan_util.py（PC の一式では同じフォルダに入れる）"""
    import importlib.util
    for d in (HERE, os.path.join(HERE, "..", "..", "..", "episodes", "ep02_qr", "pc_kit", "qr")):
        f = os.path.join(d, "plan_util.py")
        if os.path.exists(f):
            sp = importlib.util.spec_from_file_location("plan_util", f); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
    raise ImportError("plan_util.py がない")


class Maru:
    def __init__(self, loc, face, s=1.0, face_offset=180.0, look_up=0.0, name="maru", **_):
        z = loc[2] if len(loc) > 2 else 0.0
        self.s = s; self.off = face_offset
        self.handle = MR.place(loc=(0.0, 0.0, z), heading=0.0, scale=s, name=name)   # 親は世界の原点・回転なし・大きさ s
        self.root = self.handle.root; self.torso = self.handle.torso; self.body = self.torso
        self.holder = self.handle.parent                        # 置き場所の親（落ちる・小さくして消す・ひっくり返る は、これを動かす）
        self.cmds = []; self.p0 = (loc[0] / s, loc[1] / s); self.h0 = face + face_offset; self.look0 = look_up
        self._last = {}
        ALL.append(self)

    # ---- 命令（時刻は場面の時刻）
    def at(self, t, loc=None, face=None, look=None, **_):
        if loc is not None: self.cmds.append((t, "go", dict(p=(loc[0], loc[1]))))
        if face is not None and loc is None: self.cmds.append((t, "face", dict(face=face)))
        if look is not None: self.cmds.append((t, "look", dict(pitch=look)))

    def walk(self, t0, t1, a, b=None, face=None, end_face=None, speed=None, **_):
        if b is None: b = a                                   # walk(t0, t1, b) の書き方にも
        self.cmds.append((t1, "go", dict(p=(b[0], b[1]), end_face=end_face, speed=speed)))   # speed：そろりそろり（0.5）など

    def hop(self, t, h=0.3, d=0.45): self.cmds.append((t, "hop", dict(h=h)))
    def tilt(self, t, deg, d=0.3): self.cmds.append((t, "roll", dict(deg=deg, d=d)))
    def lean(self, t, deg, d=0.3): self.cmds.append((t, "pitch", dict(deg=deg, d=d)))
    def glow(self, t, s0, s1=None, d=0.25): self.cmds.append((t, "light", dict(v=(s1 if s1 is not None else s0), d=d)))
    def blink(self, t, d=0.25): self.cmds.append((t, "blink", {}))
    def surprise(self, t): self.cmds.append((t, "surprise", {}))
    def nod(self, t, n=2): self.cmds.append((t, "nod", dict(n=n)))
    def shake(self, t): self.cmds.append((t, "shake", {}))
    def think(self, t, dur=2.2): self.cmds.append((t, "think", dict(dur=dur)))
    def peer(self, t, dur=1.6, bend=24.0): self.cmds.append((t, "peer", dict(dur=dur, bend=bend)))
    def sigh(self, t): self.cmds.append((t, "sigh", {}))
    def look_around(self, t): self.cmds.append((t, "look_around", {}))
    def confused(self, t): self.cmds.append((t, "confused", {}))
    def present(self, t, yaw=45.0): self.cmds.append((t, "present", dict(yaw=yaw)))
    def greet(self, t): self.cmds.append((t, "greet", {}))
    def awe(self, t, dur=3.2, pitch=20.0): self.cmds.append((t, "awe", dict(dur=dur, pitch=pitch)))
    def groove(self, t, dur=4.0, bpm=96.0): self.cmds.append((t, "groove", dict(dur=dur, bpm=bpm)))
    def rest(self, t, dur=2.5): self.cmds.append((t, "rest", dict(dur=dur)))
    def wake(self, t): self.cmds.append((t, "wake", {}))
    def stagger(self, t, n=3): self.cmds.append((t, "stagger", dict(n=n)))     # よろける（QR回の plan_util.stagger）
    def bonk(self, t, hold=0.8): self.cmds.append((t, "bonk", dict(hold=hold)))       # ぶつかる（ゴツン）。5本目で足した動き
    def hops(self, t, n=3, height=0.06): self.cmds.append((t, "hops", dict(n=n, height=height)))
    def run(self, t, loc): self.cmds.append((t, "move", dict(p=(loc[0], loc[1]), how="run_to")))      # t＝着く時刻
    def back(self, t, loc): self.cmds.append((t, "move", dict(p=(loc[0], loc[1]), how="back_to")))
    def jump(self, t, loc, z1=0.0): self.cmds.append((t, "jump", dict(p=(loc[0], loc[1]), z1=z1)))  # t＝跳び始める時刻

    # ---- 予定にする
    def _pp(self, p): return (p[0] / self.s, p[1] / self.s)

    def _wait_to(self, p, tau, name):
        if tau < p.t - 1e-6: LATE.append((name, round(p.t - tau, 2)))
        gap = tau - p.t
        if gap > 3.2: p.idle(gap - 0.4, shifts=True, glance=True)
        p.wait(max(0.0, tau - p.t))

    def plan(self, t_end, T0):
        p = mm.Plan(pos=self.p0, heading=self.h0)
        if self.look0: p.look(0, self.look0, hold=0.0, at=0.0)
        for t, kind, a in sorted(self.cmds, key=lambda c: c[0]):
            tau = t - T0
            if kind == "go":
                tgt = self._pp(a["p"])
                if math.hypot(tgt[0] - p._p[0], tgt[1] - p._p[1]) < 0.03: continue
                for v in ([a["speed"]] if a.get("speed") else []) + [1.0, 1.3]:   # 決めた速さ → ふつう → 急ぎ
                    q = copy.deepcopy(p); q.walk_to(tgt, speed=v); d = q.t - p.t
                    if tau - d >= p.t - 1e-6: break
                self._wait_to(p, tau - d, "歩く %.1f秒" % t); p.walk_to(tgt, speed=v)
                if a.get("end_face") is not None: p.turn_to(a["end_face"] + self.off)
            elif kind == "move":                                       # 走る・後ろへ下がる（着く時刻＝t）
                tgt = self._pp(a["p"]); fn = a["how"]
                q = copy.deepcopy(p); getattr(q, fn)(tgt); d = q.t - p.t
                self._wait_to(p, tau - d, "%s %.1f秒" % (fn, t)); getattr(p, fn)(tgt)
            elif kind == "jump":
                self._wait_to(p, tau, "跳び乗る %.1f秒" % t); p.jump_to(self._pp(a["p"]), z1=a["z1"] / self.s, apex=(a["apex"] / self.s if a.get("apex") is not None else None))     # apex：出発より上へ何 m（世界）上がるか。台のふちを越えて跳び降りるとき（5本目で足した）
            elif kind == "face":
                h = a["face"] + self.off
                q = copy.deepcopy(p); q.turn_to(h); d = q.t - p.t
                if d < 0.05: continue
                self._wait_to(p, tau - d, "向く %.1f秒" % t); p.turn_to(h)
            elif kind == "look":
                p.look(0, a["pitch"], hold=0.0, at=max(tau, 0.0))
            elif kind == "hop":
                self._wait_to(p, tau, "跳ぶ %.1f秒" % t); p.hops(n=1, height=max(0.05, min(0.16, a["h"] * 0.35)))
            elif kind == "roll":
                p.tracks["roll"].set(max(tau, 0.0), a["d"], -a["deg"])
            elif kind == "pitch":
                p.tracks["pitch"].set(max(tau, 0.0), a["d"], a["deg"])
            elif kind == "light":
                p.tracks["light"].set(max(tau, 0.0), a["d"], a["v"] / 1.6 - 1.0)
            elif kind == "blink":
                p.blinks.append(max(tau, 0.0))
            elif kind == "stagger":                                    # QR回で足した動き（plan_util）
                self._wait_to(p, tau, "よろける %.1f秒" % t); _plan_util().stagger(p, **a)
            else:
                self._wait_to(p, tau, "%s %.1f秒" % (kind, t)); getattr(p, kind)(**a)
        if p.t < t_end - T0 + 0.5: p.idle(t_end - T0 + 0.5 - p.t)
        return p

    def bake(self, t_end, T0=0.0, fps=24, steps=None, events=None):
        p = self.plan(t_end, T0)
        frames = mm.simulate(p, fps=fps, t_end=p.t)
        self.handle.bake(frames, f0=0)
        for e in p.events:
            if steps is not None and e["kind"] in ("step", "step_turn"): steps.append(round(T0 + e["t"], 3))
            elif events is not None and not e["kind"].startswith("_"):   # 跳ぶ・着く・気持ちの動きの電子音（beep_surprise・beep_yes・sigh・ding…。maru_motions.md の音）
                events.append((round(T0 + e["t"], 3), "maru:%s:%.2f" % (e["kind"], e.get("strength", 1.0))))
                #   「maru:種類:強さ」。組み立ては maru_sfx.make(種類, 強さ) で鳴らす（小さく跳ねる音は小さく。3本目 v10：
                #   前は takeoff・land をその回の大きな「ピョン・ドン」で鳴らし、声と重なる大きな音が 57 か所出た／気持ちの音は渡していなかった）
        self.p, self.frames = p, frames
        return frames


def bake_all(t_end, T0=0.0, fps=24, steps=None, events=None):
    for m in ALL: m.bake(t_end, T0, fps, steps, events)
    if LATE: print("【まるロボ】間に合わなかった動き（秒）：", LATE)
