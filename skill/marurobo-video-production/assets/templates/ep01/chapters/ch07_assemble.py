# 第7章「イヤホンの中：バッファ」（本編 12:15.2〜15:06.2、台本 v2 の 129〜157）の組み立て
#   3D（ch07_stage.py：〜14:39.2）に札・印を重ね、そのあとに二つを並べた図（間に合った ✓／間に合わなかった ×）と、電車の画（第4章の D8）を続ける
#   曲：第6章からずっと同じ 3.08 秒のくり返し（拍の頭も同じ）。後半、最後の荷物が鳴り終わる所（871.8）で止まる
# 使い方: python3 ch07_assemble.py OUT_DIR [--frames DIR] [--proxy DIR] [--range A:B] [--no_video]
import sys, os, json, math, subprocess, wave, glob
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import ch07_plan as p7, overlay2d as O2
from overlay2d import TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY, fade, clamp, draw, tag, ring, mark, note, qmark, title, add2


def opt(name, default=None): return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


OUT = sys.argv[1]
FR = opt("--frames", os.path.join(OUT, "frames")); PROXY = opt("--proxy")
LOG = json.load(open(os.path.join(OUT, "ch07_log.json"), encoding="utf-8"))
FPS = LOG["fps"]; N3 = LOG["frames"]; T0 = LOG["t0"]
# 2026-11-09 ユーザー：12:55「ほら、曲は」・13:33「バッファが」・14:47「あるいは」の前に間を足す。この章の中だけで声と字幕をずらす
#   （3D は台本の時刻 p7.L で描いてあるので placement は変えない）。14:47 からあとの文は続けてずらし、章の終わり（電車の画）を同じだけのばす
VSHIFT = {136: 0.65, 141: 0.5, 154: 0.5, 155: 0.5, 156: 0.5, 157: 0.5}
def L2(n): return p7.L(n) + VSHIFT.get(n, 0.0)
def LE2(n): return p7.LE(n) + VSHIFT.get(n, 0.0)
T_END = p7.L(158) - 0.3 + VSHIFT[157]                     # 第8章「それなら、もっと先の分まで…」の前（ずらした分だけのばす）
T = T_END - T0; N = int(round(T * FPS))
T_CMP, T_TRAIN = p7.T1, L2(156) - 0.3                      # 二つを並べた図、電車の画
RNG = opt("--range"); I0, I1 = (0, N) if not RNG else tuple(int(v) for v in RNG.split(":"))
SRT = os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")
SONG = os.path.join(HERE, "..", "human", "audio", "song_mono.wav")
SEQ = os.path.join(OUT, "full"); os.makedirs(SEQ, exist_ok=True)
SR = O2.SR; PTS = LOG["points"]; IDX = {k: j for j, k in enumerate(LOG["parcels"])}
SH = LOG["shots"]
def shot_at(t):
    nm = SH[0][1]
    for a, n_ in SH:
        if t >= a - 1e-6: nm = n_
    return nm


# ---------------------------------------------------------------- 絵
STILLS = []
if PROXY:
    for p in glob.glob(os.path.join(PROXY, "still_*.png")):
        try: STILLS.append((int(round((float(os.path.basename(p)[6:-4]) - T0) * FPS)), p))
        except ValueError: pass
    STILLS.sort()


def frame3d(i):
    i = min(max(i, 0), N3 - 1)
    if PROXY:
        nm = shot_at(i / FPS); cand = [(abs(fi - i), p) for fi, p in STILLS if shot_at(fi / FPS) == nm]
        if cand: return Image.open(min(cand)[1]).convert("RGB")
        im = Image.new("RGB", (640, 360), (60, 64, 70)); ImageDraw.Draw(im).text((320, 180), nm, fill="white", anchor="mm"); return im
    return Image.open(os.path.join(FR, "f_%04d.png" % (i + 1))).convert("RGB")


_f0 = frame3d(0); RW, RH = _f0.size
# 確認ページ用：MARU_OUTW=1280 なら、640×360 の絵を 1280×720 に広げてから札・印を描く（字や線がくっきり）
if os.environ.get("MARU_OUTW"): RW = int(os.environ["MARU_OUTW"]); RH = RW * 9 // 16
O2.init(RW); K = O2.K
def cam(i): return LOG["cam"][min(max(i, 0), N3 - 1)]
def pj(i, P): return O2.proj(cam(i), P)
def num_pt(i, key):
    """荷物の前の札の番号の位置（画面）と、まわりの丸の半径"""
    w = LOG["parcel_w"][min(i, N3 - 1)][IDX[key]]
    if w is None: return None, 0
    P = np.array([w[0] + 0.10, -0.32, w[1] + 0.16]); a = pj(i, P); b = pj(i, P + np.array([0, 0, 0.15]))
    return (a, clamp(math.hypot(b[0] - a[0], b[1] - a[1]), 16.0, 90.0)) if (a and b) else (None, 0)


def ringonly(base, i, key, col, a):
    c, r = num_pt(i, key)
    if c: base = draw(base, a, lambda d: ring(d, c, r, col, 4))
    return base


def at_word(n, word):
    """声 n の中で word が言われるおよその時刻（文字の位置で割る）"""
    a, b = p7.L(n), p7.LE(n); txt = p7.PLC[n]["text"]
    return a + (b - a) * txt.index(word) / len(txt)


def ringtag(base, i, key, txt, col, a):
    c, r = num_pt(i, key)
    if c: base = draw(base, a, lambda d: (ring(d, c, r, col, 4), tag(d, (c[0], c[1] - r - 22), txt, col)))
    return base


BEAT0 = 712.29; BEAT = 0.385
def notes(base, i, t_abs, c0, a_all, spread=34):
    """拍ごと（2拍に1回）に音符が出て、上へ消えていく"""
    if c0 is None or a_all <= 0: return base
    nb = math.floor((t_abs - BEAT0) / BEAT)
    for n_ in range(nb - 4, nb + 1):
        if n_ % 2: continue
        age = t_abs - (BEAT0 + n_ * BEAT)
        if not (0 <= age < 1.7): continue
        side = 1 if (n_ // 2) % 2 else -1; c = (c0[0] + side * (spread + 10 * age), c0[1] - 12 - 30 * age)
        base = draw(base, fade(age, 0.0, 1.7, 0.12, 0.6) * a_all, lambda d, c=c: note(d, c, TEAL, 1.3))
    return base


def wave_strip(base, t_abs, a):
    """音の帯：いままでの 4 秒の音（止まった所から先は平らな灰色の線）"""
    def fn(d):
        x0, x1, y = 170, 470, 92
        d.rounded_rectangle(O2.P_(x0 - 16, y - 26, x1 + 16, y + 26), radius=10 * K, fill=(250, 250, 248, 225))
        pts_on, pts_off = [], []
        for x in range(x0, x1 + 1, 2):
            tt = t_abs - (x1 - x) / (x1 - x0) * 4.0
            yy = y + (12 * math.sin((tt - BEAT0) * 2 * math.pi / BEAT) * (0.55 + 0.45 * abs(math.sin((tt - BEAT0) * 3.1))) if tt < p7.T_STOP else 0.0)
            (pts_on if tt < p7.T_STOP else pts_off).append((x * K, yy * K))
        if len(pts_on) > 1: d.line(pts_on, fill=TEAL, width=O2.W_(3))
        if len(pts_off) > 1: d.line(pts_off, fill=GRAY, width=O2.W_(3))
    return draw(base, a, fn)


def overlays(base, i, t):
    ta = T0 + t; nm = shot_at(t); L = p7.L
    if nm == "K1": base = draw(base, fade(ta, 735.6, 741.8, 0.3, 0.3), lambda d: tag(d, (320, 36), "イヤホンの中", TEAL))
    elif nm == "K2": base = ringonly(base, i, "04A", GREEN, fade(ta, L(131) - 0.1, 750.55, 0.25, 0.2))
    elif nm == "K3": base = ringonly(base, i, "05A", TEAL, fade(ta, L(132) + 0.3, 755.4, 0.25, 0.2))
    elif nm == "K5":
        base = ringonly(base, i, "05A", GREEN, fade(ta, 769.85, 775.0, 0.2, 0.3))
        base = notes(base, i, ta, pj(i, PTS["speaker"]), fade(ta, L2(136), 776.4, 0.3, 0.3), 70)
    elif nm == "K6":
        base = ringonly(base, i, "06A", AMBER, fade(ta, L(137) - 0.2, L(138) - 0.1, 0.25, 0.2))
    elif nm == "K7": pass                                            # 「バッファ」は 3D の札（K7s の寄りで光る）が見せる。平面の名前札は重ねない
    elif nm == "K8":
        c = pj(i, PTS["gauge_top"]); c0 = pj(i, PTS["gauge_bottom"])
        if c and c0:                                                 # 目盛り（左の柱の灯）の横に「たまっている分」
            ym = 0.5 * (c[1] + c0[1])
            base = draw(base, fade(ta, L(140) + 1.5, LE2(141), 0.3, 0.3), lambda d: (d.line(O2.P_(c0[0] - 16, c0[1], c[0] - 16, c[1]), fill=TEAL, width=O2.W_(3)), tag(d, (c[0] - 70, ym), "たまっている分", TEAL, 13)))
    elif nm == "K10":
        c = pj(i, PTS["pit"])
        def f10(d):
            if c: qmark(d, (c[0], c[1] - 110), RED, 30, "09 …？")          # まるロボ（高さ 1.2m）が口の前を通っても重ならない高さ
        base = draw(base, fade(ta, L(146) + 0.2, 846.6, 0.25, 0.3), f10)
    elif nm == "K12":
        base = wave_strip(base, ta, fade(ta, L(151) - 0.2, 1e9, 0.3, 0.2))
    return base


# ---------------------------------------------------------------- 二つを並べた図（間に合った ✓／間に合わなかった ×）と、電車の画
CMP_A, CMP_B = 788.0, 876.0                               # 3D のコマ（前半：06 が待っている、後半：空になった）
def compare_frame(t):
    ta = T0 + t; L = p7.L
    im = Image.new("RGB", (RW, RH), (238, 242, 245)).convert("RGBA")
    a = frame3d(int(round((CMP_A - T0) * FPS))).resize((int(300 * K), int(169 * K))); b = frame3d(int(round((CMP_B - T0) * FPS))).resize((int(300 * K), int(169 * K)))
    im.paste(a, (int(14 * K), int(92 * K))); im.paste(b, (int(326 * K), int(92 * K)))
    im = draw(im, 1.0, lambda d: (d.rectangle(O2.P_(14, 92, 314, 261), outline=GREEN, width=O2.W_(3)), d.rectangle(O2.P_(326, 92, 626, 261), outline=RED, width=O2.W_(3))))
    im = draw(im, fade(ta, L(153) - 0.1, 1e9, 0.25, 0.2), lambda d: mark(d, (300, 100), 15, True))
    im = draw(im, fade(ta, L2(154) - 0.1, 1e9, 0.25, 0.2), lambda d: mark(d, (612, 100), 15, False))
    return im


D8 = os.path.join(HERE, "ch04_out", "D8.png")
def train_frame(t):
    ta = T0 + t; u = clamp((ta - T_TRAIN) / (T_END - T_TRAIN))
    src = Image.open(D8).convert("RGB"); w, h = src.size; z = 1.0 + 0.08 * u
    cw, ch = w / z, h / z; cx, cy = w * 0.5, h * 0.52
    im = src.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((RW, RH), Image.LANCZOS).convert("RGBA")
    return im


# ---------------------------------------------------------------- 字幕
NAMES = {"K1": "K1 イヤホンの中（引き）", "K2": "K2 再生装置：04 が鳴っている", "K3": "K3 05 が待っている", "K4": "K4 塔と再生装置", "K5": "K5 04 → 05（曲は続く）",
         "K6": "K6 昇降機で 06 が届く", "K7": "K7 まるロボが下がって見上げる", "K7s": "K7s 札「バッファ」が光る", "K8": "K8 目盛り：07 は少し遅れて届く", "K9": "K9 塔と再生装置", "K9b": "K9 引き",
         "K10": "K10 後半：09 が届かない", "K11": "K11 残りは一つ", "K12": "K12 空になり、音が止まる", "CMP": "C 二つを並べる", "TRAIN": "D 電車：人の体や物"}
ass = list(O2.ASS_HEAD)
ass.append("Dialogue: 0,%s,%s,Note,,0,0,0,,第7章（%s〜%s）%s" % (O2.ts(0), O2.ts(T), O2.mmss(T0), O2.mmss(T0 + T), os.environ.get("MARU_NOTE", "確認用・低画質・声は Gemini（Achernar）")))
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import subs_jp as SJ
def _vs(a):                                                           # その字幕（文の始まり a）をずらす秒
    return next((d for n, d in VSHIFT.items() if abs(a - p7.L(n)) < 0.02), 0.0)
for a, b, txt in SJ.expand([(a + _vs(a), c + _vs(a), t_) for a, c, t_ in O2.srt_lines(SRT) if a < p7.L(158) - 0.05]):   # 第8章の文（158〜）は第8章で出す   # 1 枚ずつ（改行入り。長い文は声の間で何枚かに）
    if b < T0 or a > T0 + T: continue
    ass.append("Dialogue: 1,%s,%s,Main,,0,0,0,,{\\fad(120,120)}%s" % (O2.ts(a - T0), O2.ts(min(b, T0 + T) - T0), txt))
SHX = [[a, n_] for a, n_ in SH if a < T_CMP - T0] + [[T_CMP - T0, "CMP"], [T_TRAIN - T0, "TRAIN"], [T, None]]
for (a, nm), (b, _) in zip(SHX[:-1], SHX[1:]):
    ass.append("Dialogue: 0,%s,%s,Shot,,0,0,0,,%s　%s" % (O2.ts(a), O2.ts(b), NAMES.get(nm, nm), O2.mmss(T0 + a)))
if os.environ.get("MARU_FINAL") == "1": ass = [l_ for l_ in ass if ",Note,," not in l_ and ",Shot,," not in l_]
open(os.path.join(OUT, "ch07_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 効果音：昇降機・押し出し板・扉・ブレーキで落ちる音・着く音
audio = np.zeros(int((T + 1.0) * SR))
def add(t, x):
    i = int(t * SR)
    if i < 0 or i >= len(audio): return
    j = min(len(audio), i + len(x)); audio[i:j] += x[:j - i]
for key, a in p7.ARR.items():
    r = lambda t_abs: t_abs - T0
    add(r(a["t_rise0"]), O2.motor(a["t_rise1"] - a["t_rise0"], 0.035, 120.0))                  # 昇降機が上がる
    add(r(a["t_push0"]), O2.motor(a["t_push1"] - a["t_push0"], 0.03, 200.0))                   # 押し出し板
    add(r(a["t_open"]), O2.clank(0.035, 0.18)); add(r(a["t_open"]) + 0.02, O2.thump(0.06, 0.06, 300.0, 0.5))   # 扉が開く
    add(r(a["t_open"]) + 0.1, O2.motor(a["T_fall"] - 0.1, 0.012, 60.0))                        # ブレーキで落ちる（低いうなり）
    add(r(a["t_land"]), O2.thump(0.16, 0.12, 78.0, 0.3))                                       # 積み重なりの上に着く
    add(r(a["t_close"]) + 0.35, O2.clank(0.02, 0.12))                                          # 扉が閉まる
    add(r(a["t_lower0"]), O2.motor(a["t_lower1"] - a["t_lower0"], 0.025, 110.0))              # 昇降機が下りる
add(p7.T_STOP - T0, O2.thump(0.05, 0.08, 120.0, 0.2))                                          # 再生装置が止まる
sfx_peak = np.abs(audio).max(); audio = audio / max(sfx_peak, 1e-9) * 0.45
# まるロボの足音（2026-11-09 ユーザー）：3D を描いたときと同じ予定（ch07_robot.plan_ch7）の一歩ずつ。音は第3・6章と同じ（低い「トッ」）
import ch07_robot as RB
steps = np.zeros_like(audio); _ev = [e for e in RB.plan_ch7(p7.T0).events if e["kind"] in ("step", "step_turn", "takeoff", "land")]
for e in _ev:
    t_, k_, s_ = float(e["t"]), e["kind"], float(e.get("strength", 1.0)); i_ = int(t_ * SR)
    if t_ + T0 < RB.T_SHOW or i_ >= len(steps): continue                      # まるロボが見えるのは 06 の到着から（t_ は章の頭からの秒）
    if k_ == "step": x_ = O2.thump(0.22 * (0.4 + 0.6 * s_), f=95.0)
    elif k_ == "step_turn": x_ = O2.thump(0.10, f=110.0, click=0.2)
    elif k_ == "takeoff": x_ = O2.thump(0.10, dur=0.10, f=72.0, click=0.25); i_ = max(0, i_ - int(0.02 * SR))
    else: x_ = O2.thump(min(0.30, 0.11 * s_), dur=0.14, f=64.0, click=0.35)
    j_ = min(len(steps), i_ + len(x_)); steps[i_:j_] += x_[:j_ - i_]
audio = audio + steps * (0.18 / max(float(np.abs(steps).max()), 1e-9))       # 一番強い一歩が 0.18（荷物が着く音の 4 割ほど）
print("ROBOT steps", len(_ev), flush=True)

# ---------------------------------------------------------------- 曲：第6章から続く 3.08 秒のくり返し（拍の頭も同じ）。後半の最後の荷物が終わると止まる
try:
    loop = O2.song_loop(SONG); nL = len(loop); nA = len(audio); tt = np.arange(nA) / SR + T0
    bed = loop[(np.round((tt - BEAT0) * SR).astype(np.int64)) % nL]
    lev = np.full(nA, 0.24)
    stop = (tt >= p7.T_STOP) & (tt < T_CMP + 30)
    lev[stop] = 0.0
    k0 = int((p7.T_STOP - T0) * SR); lev[max(0, k0 - int(0.03 * SR)):k0] *= np.linspace(1, 0, min(k0, int(0.03 * SR)))   # 30ms で止まる（ぷつっ）
    audio = audio + bed * lev
except Exception as ex:
    print("SONG skipped:", ex)
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import narration as NAR
PLACE7 = [dict(p, start=p["start"] + VSHIFT.get(p["no"], 0.0), end=p["end"] + VSHIFT.get(p["no"], 0.0)) for p in json.load(open(os.path.join(HERE, "..", "voice", "achernar", "placement.json"), encoding="utf-8")) if p["no"] <= 157]   # 第8章の声（158〜）は入れない
audio = NAR.mix_voice(audio, T0, SR, bus_peak=0.5, duck_db=6.0, P=PLACE7)
with wave.open(os.path.join(OUT, "ch07_audio.wav"), "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 絵：札・印を重ねて full/ へ
def make_frame(i):
    t = i / FPS; ta = T0 + t
    if ta < T_CMP:
        im = overlays(frame3d(i).resize((RW, RH)).convert("RGBA"), i, t)
        if t < 0.35: im = Image.blend(Image.new("RGBA", im.size, (8, 9, 10, 255)), im, clamp(t / 0.35))   # 耳の先の口の奥（暗い網）から、イヤホンの中へ
    elif ta < T_TRAIN: im = compare_frame(t)
    else: im = train_frame(t)
    return im

def stream_mp4(mp4, frame_fn, audio, subs, n, extra_vf=""):
    """本番（MARU_STREAM=1）：コマを PNG に書かず、ffmpeg へ直接流す（1080p の PNG はディスクに入らない）"""
    vf = (extra_vf + "," if extra_vf else "") + "subtitles=%s:fontsdir=%s" % (subs, O2.FONTS)
    pr_ = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (RW, RH), "-framerate", str(FPS), "-i", "-",
                            "-i", audio, "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], stdin=subprocess.PIPE)
    for k in range(n):
        im = frame_fn(k).convert("RGB")
        if im.size != (RW, RH): im = im.resize((RW, RH), Image.LANCZOS)
        pr_.stdin.write(im.tobytes())
        if k % 240 == 0: print("STREAM", k, "/", n, flush=True)
    pr_.stdin.close(); rc_ = pr_.wait()
    if rc_ != 0: sys.exit("ffmpeg failed %d" % rc_)
    print("WROTE", mp4)

if os.environ.get("MARU_STREAM") == "1" and not RNG and "--no_video" not in sys.argv:
    stream_mp4(os.path.join(OUT, "ch07_animatic.mp4"), lambda k: make_frame(I0 + k), os.path.join(OUT, "ch07_audio.wav"), os.path.join(OUT, "ch07_subs.ass"), I1 - I0)
    sys.exit(0)
for i in range(I0, I1):
    make_frame(i).convert("RGB").save(os.path.join(SEQ, "f_%04d.png" % (i + 1)))
print("FRAMES", I0, I1, "→", SEQ, flush=True)
if "--no_video" in sys.argv: sys.exit(0)
mp4 = os.path.join(OUT, "ch07_animatic.mp4" if not RNG else "ch07_part.mp4")
cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-start_number", str(I0 + 1), "-i", os.path.join(SEQ, "f_%04d.png"),
       "-ss", "%.3f" % (I0 / FPS), "-i", os.path.join(OUT, "ch07_audio.wav"),
       "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch07_subs.ass"), O2.FONTS) if not RNG else "null",
       "-frames:v", str(I1 - I0), "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p",
       "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4]
subprocess.run(cmd, check=True)
print("WROTE", mp4)
