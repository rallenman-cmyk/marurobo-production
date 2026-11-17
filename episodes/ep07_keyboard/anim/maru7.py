# 7本目のまるロボ（2026-11-17 から）：本物の体（maru_real）を、動きの予定（marumotion）で動かす。scenes.py が exec で読む
#   決まり：skill/marurobo-video-production/references/maru_walk.md・maru_motions.md（手で動かさない。体を滑らせない）
#   前と同じ書き方（M.at / walk / hop / tilt / glow / wobble / blink）を受け取ってためておき、最後に bake_maru() で
#   声の時刻の順に予定へ並べる。予定の時刻＝場面の時刻（秒）。予定の座標＝場面の座標 ÷ 大きさ s
#     ・at(loc)・walk → 歩く（walk_to。着く時刻に間に合うように早く歩き出す）。高さが変わるときは跳ぶ（hop_path の 1 回）
#     ・at(-100 など、0 より前) → 始めの場所・向き
#     ・at(…, interp="CONSTANT") → その時刻に置き直す（カットの中だけで使う）
#     ・path（kit の hop_path から）→ キーからキーへ続けて跳ぶ（marumotion の hop_path）
#     ・jump → 1 回跳んで移る（台に跳び乗る・跳び降りる）。drop → 上から落ちてくる（置き場所の親を落とす）
#     ・hop → その場で 1 回跳ねる（hops）。face → 足踏みで向く。look → 見上げる・見下ろす（目と胴）
#     ・tilt → 首をかしげる（胴ぜんぶ）。wobble → 体を左右にゆらす。glow → アンテナの光。blink → まばたき
#   間に合わなかった動きは MARU_LATE に入れて、描くときに表に出す（場面の時刻か動きを直す）
#   足音・跳ぶ音・着く音は、予定の step・takeoff・land の時刻に置く（キーを打つ所の跳ぶ音は、キーの音があるので鳴らさない）
import copy
_SK7 = os.path.join(_K7, "..", "..", "..", "skill", "marurobo-video-production", "scripts")
_RG7 = os.path.join(_K7, "..", "..", "ep01_earphone", "stage", "maru")
for _d in (_RG7, _SK7, _K7):                     # PC の一式では anim に marumotion・marurig・maru_real を入れる
    if os.path.isdir(_d) and _d not in sys.path: sys.path.insert(0, _d)
import marumotion as mm
import maru_real as MRL

MARU_ALL = []
MARU_LATE = []
FACE_OFF = 180.0          # 前の体は前が −Y（face=0 でカメラの方）。本物は前が +Y


class MaruR:
    S = 0.26

    def __init__(self, loc, face=0.0, s=None, glow=0.9, **_):
        self.s = s or MaruR.S
        z = loc[2] if len(loc) > 2 else 0.0
        self.init = dict(p=(loc[0], loc[1]), z=z, face=face)
        self.h = MRL.place(loc=(0.0, 0.0, 0.0), heading=0.0, scale=self.s, name="maru%d" % len(MARU_ALL))
        self.body = self.h.torso; self.torso = self.h.torso
        self.root = empty((0, 0, 0)); self.root.name = "maru%d follow" % len(MARU_ALL)   # 追うカメラ用：足もとの真ん中（上下にはずまない）。bake で打つ
        self.cmds = []; self.silent = []; self.drops = []
        self._last = {"loc": (-100.0, tuple(loc))}
        track("maru_c", self.torso, 0.0)                     # 効果音の「映っているか」は体の真ん中で見る（"maru" は頭の上の吹き出し用）
        MARU_ALL.append(self); _M_[0] = self

    # ---------------------------------------------------------------- 命令（時刻は場面の時刻）
    def at(self, t, loc=None, face=None, look=None, interp="BEZIER", **_):
        if loc is not None:
            loc = tuple(loc) + ((0.0,) if len(loc) < 3 else ())
            if t < 0: self.init.update(p=(loc[0], loc[1]), z=loc[2])
            else: self.cmds.append((t, "go", dict(p=loc, cut=(interp == "CONSTANT"))))
            self._last["loc"] = (t, loc)
        if face is not None:
            if t < 0: self.init["face"] = face
            elif loc is None: self.cmds.append((t, "face", dict(face=face)))
            else: self.cmds.append((t + 0.001, "face", dict(face=face, cut=(interp == "CONSTANT"), after=True)))   # 着いてから向く
        if look is not None and t >= 0: self.cmds.append((t, "look", dict(pitch=look)))

    def walk(self, t0, t1, p1, **_):
        p1 = tuple(p1) + ((0.0,) if len(p1) < 3 else ())
        self.cmds.append((t1, "go", dict(p=p1, cut=False, t0=t0))); self._last["loc"] = (t1, p1)

    def jump(self, t_land, loc, apex=None):
        """1 回跳んで移る（t_land に着く）。高さがちがう所へも。見る → 向く → しゃがむ → 跳ぶ（marumotion の jump_to）"""
        loc = tuple(loc) + ((0.0,) if len(loc) < 3 else ())
        self.cmds.append((t_land, "jump", dict(p=loc, apex=apex))); self._last["loc"] = (t_land, loc)

    def hopto(self, t_land, loc, silent=False):
        """向きを変えずに、すばやく 1 回跳んで移る（横・後ろへも。marumotion の hop_path の 1 回）"""
        loc = tuple(loc) + ((0.0,) if len(loc) < 3 else ())
        self.cmds.append((t_land, "path", dict(pts=[loc], ts=[t_land], silent=silent))); self._last["loc"] = (t_land, loc)

    def hops(self, t, n=2, height=0.12, sound=True): self.cmds.append((t, "hops", dict(n=n, height=height, sound=sound)))
    def push(self, t, d=0.3): self.cmds.append((t, "push", dict(d=d)))

    def path(self, pts, ts, silent=True):
        """続けて跳んで移る（kit の hop_path から）。pts：[(x, y, z)]、ts：着く時刻"""
        pts = [tuple(p) for p in pts]
        self.cmds.append((ts[0], "path", dict(pts=pts, ts=list(ts), silent=silent))); self._last["loc"] = (ts[-1], pts[-1])

    def drop(self, t0, t1, z_from):
        """上から落ちてくる（t0〜t1。置き場所の親を z_from の高さから今の床へ落とす。着いたら脚で受け止める）"""
        self.drops.append((t0, t1, z_from)); self.cmds.append((t1, "land", {}))

    def hop(self, t, h=0.25, d=0.45, sound=True):
        self.cmds.append((t, "hop", dict(sound=sound)))

    def tilt(self, t, deg, d=0.3): self.cmds.append((t, "roll", dict(deg=deg, d=d)))
    def glow(self, t, g, d=0.3, g0=None): self.cmds.append((t, "light", dict(v=g, d=d)))
    def blink(self, t, g=0.9, d=0.22): self.cmds.append((t, "blink", {}))
    def wobble(self, t0, t1, deg=10, period=0.5): self.cmds.append((t0, "wobble", dict(t1=t1, deg=deg, period=period)))
    def nod(self, t, n=2): self.cmds.append((t, "nod", dict(n=n)))
    def shake(self, t): self.cmds.append((t, "shake", {}))
    def surprise(self, t): self.cmds.append((t, "surprise", {}))
    def confused(self, t): self.cmds.append((t, "confused", {}))
    def sigh(self, t): self.cmds.append((t, "sigh", {}))
    def peer(self, t, dur=1.6): self.cmds.append((t, "peer", dict(dur=dur)))
    def look_around(self, t): self.cmds.append((t, "look_around", {}))

    # ---------------------------------------------------------------- 予定にする
    def _pp(self, p): return (p[0] / self.s, p[1] / self.s)

    def _late(self, name, d):
        if d > 0.08: MARU_LATE.append((name, round(d, 2)))

    def _wait_to(self, p, tau, name):
        self._late(name, p.t - tau)
        gap = tau - p.t
        if gap > 3.2: p.idle(gap - 0.4, shifts=True, glance=True)
        p.wait(max(0.0, tau - p.t))

    def plan(self, t_end):
        I = self.init
        p = mm.Plan(pos=self._pp(I["p"]), heading=I["face"] + FACE_OFF, ground=I["z"] / self.s)
        self.log = []
        for t, kind, a in sorted(self.cmds, key=lambda c: c[0]):
            nm = "%s %.1f秒" % (kind, t)
            self.log.append([round(t, 2), kind, round(p.t, 2)])
            if kind == "go":
                tgt = self._pp(a["p"]); z1 = a["p"][2] / self.s
                if a["cut"]:                                # 置き直す（高さも）
                    self._wait_to(p, t, nm); p.teleport(tgt, math.degrees(p._psi))
                    for j in (0, 1): p.feet[j][-1].p[2] = z1
                    continue
                if abs(z1 - p._ground()) > 0.1:            # 高さが変わる → 跳ぶ（見る → 向く → しゃがむ → 跳ぶ）
                    self._jump(p, tgt, z1, t, nm); continue
                if math.hypot(tgt[0] - p._p[0], tgt[1] - p._p[1]) < 0.06: continue
                for v in (1.0, 1.3, 1.6):                  # ふつう → 急ぎ → もっと急ぎ
                    q = copy.deepcopy(p); q.walk_to(tgt, speed=v); d = q.t - p.t
                    if t - d >= p.t - 1e-6: break
                self._wait_to(p, t - d, nm); p.walk_to(tgt, speed=v)
            elif kind == "path":
                pts = [(*self._pp(q), q[2] / self.s) for q in a["pts"]]
                self._path(p, pts, a["ts"], nm, a["silent"])
            elif kind == "jump":
                q = a["p"]; self._jump(p, self._pp(q), q[2] / self.s, t, nm, a.get("apex"))
            elif kind == "hops":
                self._wait_to(p, t - 0.3, nm); t_ = p.t; p.hops(n=a["n"], height=a["height"])
                if not a["sound"]: self.silent.append((t_, p.t))
            elif kind == "push":                           # 前へ体重をかけて押す（ぐっ）
                p.layer(t, t + a["d"] + 0.2, lambda u, t0=t, d=a["d"]: {"pitch": 22.0 * mm.hump(u, t0, d)})
            elif kind == "face":
                h = a["face"] + FACE_OFF
                if a.get("cut"):
                    p.teleport(p._p, h); continue
                q = copy.deepcopy(p); q.turn_to(h); d = q.t - p.t
                if d < 0.05: continue
                if a.get("after"): p.turn_to(h); continue
                self._wait_to(p, t - d, nm); p.turn_to(h)
            elif kind == "look":
                p.look(0, a["pitch"], hold=0.0, at=t)
            elif kind == "hop":
                self._wait_to(p, t - 0.3, nm); t_ = p.t; p.hops(n=1, height=0.18)      # 声の「ぴょん」で見える高さ（v7 の点検）
                if not a["sound"]: self.silent.append((t_, p.t))
            elif kind == "land":                           # 落ちてきて着く：脚で受け止める（沈んで戻る）
                p.tracks["lift"].set(t, 0.08, -0.06); p.tracks["lift"].set(t + 0.1, 0.45, 0.0)
                p.tracks["pitch"].set(t, 0.08, 6.0); p.tracks["pitch"].set(t + 0.1, 0.5, 0.0)
                p.event(t, "land", 2.5)
            elif kind == "roll":
                p.tracks["roll"].set(t, a["d"], -a["deg"])
            elif kind == "light":
                p.tracks["light"].set(t, a["d"], a["v"] / 0.9 - 1.0)
            elif kind == "blink":
                p.blinks.append(t)
            elif kind == "wobble":
                t0, t1, deg, per = t, a["t1"], a["deg"], a["period"]
                p.layer(t0, t1 + 0.3, lambda u, t0=t0, t1=t1, deg=deg, per=per: {
                    "roll": deg * 0.8 * math.sin(2 * math.pi * (u - t0) / per) * mm.env(u, t0, 0.25, max(0.01, t1 - t0 - 0.5), 0.25)})
            else:
                self._wait_to(p, t, nm); getattr(p, kind)(**a)
        if p.t < t_end + 0.5: p.idle(t_end + 0.5 - p.t)
        return p

    def _jump(self, p, tgt, z1, t_land, nm, apex=None):
        """1 回跳んで移る（marumotion の jump_to）：着く時刻が t_land になるように始める。apex：予定の m（遠くへ跳ぶときは高く）"""
        ap = None if apex is None else apex / self.s
        q = copy.deepcopy(p); q.jump_to(tgt, z1=z1, apex=ap); seg = q.segs[-1]; d = seg.t_land - p.t
        self._wait_to(p, t_land - d, nm); p.jump_to(tgt, z1=z1, apex=ap)

    def _path(self, p, pts, ts, nm, silent):
        while pts and math.hypot(pts[0][0] - p._p[0], pts[0][1] - p._p[1]) < 0.06 and abs(pts[0][2] - p._ground()) < 0.05:
            pts, ts = pts[1:], ts[1:]                       # 今いる所は跳ばない
        if not pts: return
        q = copy.deepcopy(p); q.hop_path(pts, ts); seg = q.segs[-1]
        need = seg.t0 - 0.05
        self._late(nm, p.t - need)
        if need < p.t:                                      # 間に合わない：着く時刻をずらす（前の動きと重ねない）
            ts = [x + (p.t - need) for x in ts]
        if need > p.t:
            gap = need - p.t
            if gap > 3.2: p.idle(gap - 0.4, shifts=True, glance=True)
            p.wait(max(0.0, need - p.t))
        t_ = p.t; p.hop_path(pts, ts)
        if silent: self.silent.append((t_, p.t))

    def bake(self, T0, T1):
        p = self.plan(T1 + 1.0)
        frames = mm.simulate(p, fps=FPS, t_end=T1 + 1.0, t_start=max(0.0, T0 - 2.0))
        self.h.bake(frames, f0=f(frames[0]["t"]))
        par = self.h.parent
        for t0, t1, zf in self.drops:                        # 上から落ちる（重さで速くなる）
            key(par, ("location", 2), t0 - 0.001, zf, "CONSTANT")
            n = 6
            for k in range(n + 1):
                u = k / n; key(par, ("location", 2), t0 + (t1 - t0) * u, zf * (1 - u * u), "LINEAR")
        for fr in frames[::6] + frames[-1:]:                 # 追うカメラ用（0.25 秒ごと）
            x, y, z = fr["root"]; zp = par.location.z if not self.drops else 0.0
            key(self.root, "location", fr["t"], (x * self.s, y * self.s, z * self.s + zp))
        snd = {"step": ("step", 0.06), "step_turn": ("step", 0.03), "takeoff": ("jump", 0.3), "land": ("land", 0.4)}
        for e_ in p.events:
            if e_["kind"] not in snd: continue
            if e_["t"] < T0 - 1.0 or e_["t"] > T1 + 1.0: continue
            if e_["kind"] in ("takeoff", "land") and any(a - 0.01 <= e_["t"] <= b + 0.01 for a, b in self.silent): continue
            k_, g_ = snd[e_["kind"]]
            st = e_.get("strength", 1.0)
            g = g_ * (max(0.3, min(1.0, st / 3.0)) if e_["kind"] in ("takeoff", "land") else max(0.3, st))
            ev(e_["t"], k_, round(g, 3), "maru_c")
        self.p = p
        return frames


def bake_maru(T0, T1):
    for m in MARU_ALL: m.bake(T0, T1)
    if MARU_LATE: print("【まるロボ】間に合わなかった動き（遅れた秒）：", MARU_LATE)
