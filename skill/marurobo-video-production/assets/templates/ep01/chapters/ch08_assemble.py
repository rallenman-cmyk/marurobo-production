# 第8章「ためる余裕と、すぐに音が出ること」（本編 15:06.2〜17:04.9、台本 v2 の 158〜178）の組み立て
#   15:06.2〜15:27.4：イヤホンの中の塔（3D：ch07_stage.py --part ch8）。空になった塔 → 01〜03 が待ち 04 が届く（灯は琥珀：ためている）→ いっぱいで鳴らし始める
#   15:27.4〜17:00.3：図（2D：ch08_game.py）。時間の帯・てんびん → 音楽なら少し待っても → ゲームのパンチ（ぴったり／遅れる。10分の1のゆっくり）→ 流れ・札・まとめのてんびん・棒
#   17:00.3〜17:04.9：塔（3D の一コマに、ゆっくり寄る）「今回は、音を待たせる時間に注目した」
# 使い方: python3 ch08_assemble.py OUT_DIR --tower DIR [--proxy DIR] [--range A:B] [--no_video]
#   OUT_DIR/game/g_NNNN.png と ch08_game.json（ch08_game.py OUT_DIR）、DIR/ch08_tower_log.json と DIR/frames/f_NNNN.png（塔の 3D）
import sys, os, json, math, subprocess, wave, glob
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import ch07_plan as p7, overlay2d as O2
from overlay2d import TEAL, GREEN, RED, AMBER, INK, WHITE, GRAY, fade, clamp, draw, tag, ring, mark, note, qmark, add2


def opt(name, default=None): return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


OUT = sys.argv[1]; TW_DIR = opt("--tower"); PROXY = opt("--proxy")
GL = json.load(open(os.path.join(OUT, "ch08_game.json"), encoding="utf-8"))
TLOG = json.load(open(os.path.join(TW_DIR, "ch08_tower_log.json"), encoding="utf-8"))
FPS = 24; L, LE = p7.L, p7.LE
T0 = p7.T0_8; T_2D = GL["t0"]; T_TOWER2 = GL["t1"]; T_END = L(179) - 0.3
T = T_END - T0; N = int(round(T * FPS)); N3 = TLOG["frames"]
RNG = opt("--range"); I0, I1 = (0, N) if not RNG else tuple(int(v) for v in RNG.split(":"))
SRT = os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")
SONG = os.path.join(HERE, "..", "human", "audio", "song_mono.wav")
SEQ = os.path.join(OUT, "full"); os.makedirs(SEQ, exist_ok=True)
SR = O2.SR; PTS = TLOG["points"]; SH = TLOG["shots"]
def shot_at(t):
    nm = SH[0][1]
    for a, n_ in SH:
        if t >= a - 1e-6: nm = n_
    return nm


STILLS = []
if PROXY:
    for p in glob.glob(os.path.join(PROXY, "still_*.png")):
        try: STILLS.append((int(round((float(os.path.basename(p)[6:-4]) - T0) * FPS)), p))
        except ValueError: pass
    STILLS.sort()


def tower(i):
    i = min(max(i, 0), N3 - 1)
    if PROXY:
        nm = shot_at(i / FPS); cand = [(abs(fi - i), p) for fi, p in STILLS if shot_at(fi / FPS) == nm]
        if cand: return Image.open(min(cand)[1]).convert("RGB")
        return Image.new("RGB", (640, 360), (60, 64, 70))
    return Image.open(os.path.join(TW_DIR, "frames", "f_%04d.png" % (i + 1))).convert("RGB")


_f0 = tower(0); RW, RH = _f0.size
# 確認ページ用：MARU_OUTW=1280 なら、640×360 の絵を 1280×720 に広げてから札・印を描く（字や線がくっきり）
if os.environ.get("MARU_OUTW"): RW = int(os.environ["MARU_OUTW"]); RH = RW * 9 // 16
O2.init(RW); K = O2.K
def pj(i, P): return O2.proj(TLOG["cam"][min(max(i, 0), N3 - 1)], P)


def tower_overlays(base, i, t):
    ta = T0 + t; nm = shot_at(t)
    # 2026-11-09 ユーザー：字幕と同じ文を上の札でくり返さない。残すのは、灯と目盛りに付いた短い名前だけ（大きく）
    if nm == "C1": pass
    elif nm == "C2":
        c = pj(i, PTS["lamp"])
        def f2(d):
            if c: tag(d, (c[0] - 26, min(c[1] + 40, 262)), "まだ鳴らさない", GRAY, 18)
        base = draw(base, fade(ta, p7.T_C + 0.1, 1e9, 0.25, 0.2), f2)
    elif nm == "C3":
        g = pj(i, PTS["gauge_top"])
        # 「鳴らし始める」の札はなくした（2026-11-09）：字幕「…音を鳴らし始める。」と同じ言葉で、灯の右に立つまるロボにも重なっていた。灯が緑になり曲が鳴り、まるロボが跳ねるので伝わる
        def f3(d):
            if g: tag(d, (g[0] - 70, max(g[1] + 10, 80)), "余裕 ✓", GREEN, 20)
        base = draw(base, fade(ta, L(160) - 0.05, LE(160) + 1.6, 0.25, 0.3), f3)
    return base


def last_tower(t):
    """178：塔の一コマ（いっぱいで鳴っている）に、ゆっくり寄る"""
    ta = T0 + t; u = clamp((ta - T_TOWER2) / (T_END - T_TOWER2)); src = tower(int(round((918.0 - T0) * FPS))); w, h = src.size
    z = 1.0 + 0.07 * u; cw, ch = w / z, h / z; cx, cy = w * 0.5, min(max(h * 0.46, ch / 2), h - ch / 2)   # 枠の外を切り取らない
    im = src.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((RW, RH), Image.LANCZOS).convert("RGBA")
    return im


def game(t):
    ta = T0 + t; j = int(round((ta - T_2D) * FPS)); j = min(max(j, 0), GL["frames"] - 1)
    return Image.open(os.path.join(OUT, "game", "g_%04d.png" % (j + 1))).convert("RGB").resize((RW, RH), Image.LANCZOS).convert("RGBA")


# ---------------------------------------------------------------- 字幕
NAMES = {"C1": "C1 空になった塔：もっとためれば？", "C2": "C2 たくさん届くまで待つ（灯は琥珀）", "C3": "C3 いっぱいで鳴らし始める：余裕", "G": "G 図：時間の帯・てんびん・ゲーム", "E": "E 塔：待たせる時間に注目した"}
ass = list(O2.ASS_HEAD)
ass.append("Dialogue: 0,%s,%s,Note,,0,0,0,,第8章（%s〜%s）%s" % (O2.ts(0), O2.ts(T), O2.mmss(T0), O2.mmss(T0 + T), os.environ.get("MARU_NOTE", "確認用・低画質・声は Gemini（Achernar）")))
for a, b, txt in O2.narr(SRT):                                         # 1 枚ずつ（改行入り。長い文は声の間で何枚かに）
    if b < T0 or a > T0 + T: continue
    ass.append("Dialogue: 1,%s,%s,Main,,0,0,0,,{\\fad(120,120)}%s" % (O2.ts(a - T0), O2.ts(min(b, T0 + T) - T0), txt))
SHX = [[a, n_] for a, n_ in SH if a < T_2D - T0] + [[T_2D - T0, "G"], [T_TOWER2 - T0, "E"], [T, None]]
for (a, nm), (b, _) in zip(SHX[:-1], SHX[1:]):
    ass.append("Dialogue: 0,%s,%s,Shot,,0,0,0,,%s　%s" % (O2.ts(a), O2.ts(b), NAMES.get(nm, nm), O2.mmss(T0 + a)))
if os.environ.get("MARU_FINAL") == "1": ass = [l_ for l_ in ass if ",Note,," not in l_ and ",Shot,," not in l_]
open(os.path.join(OUT, "ch08_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 効果音：昇降機・扉・着く音（塔）、ゲームの「押す」「ドン！」
audio = np.zeros(int((T + 1.0) * SR))
def add(t, x):
    i = int(t * SR)
    if i < 0 or i >= len(audio): return
    j = min(len(audio), i + len(x)); audio[i:j] += x[:j - i]
for key, a in p7.ARR.items():
    if not key.endswith("C"): continue
    r = lambda t_abs: t_abs - T0
    if a["t_push0"] > T0: add(r(a["t_push0"]), O2.motor(a["t_push1"] - a["t_push0"], 0.03, 200.0))
    add(r(a["t_open"]), O2.clank(0.035, 0.18)); add(r(a["t_open"]) + 0.02, O2.thump(0.06, 0.06, 300.0, 0.5))
    add(r(a["t_open"]) + 0.1, O2.motor(max(a["T_fall"] - 0.1, 0.3), 0.012, 60.0)); add(r(a["t_land"]), O2.thump(0.16, 0.12, 78.0, 0.3))
    add(r(a["t_close"]) + 0.35, O2.clank(0.02, 0.12)); add(r(a["t_lower0"]), O2.motor(a["t_lower1"] - a["t_lower0"], 0.025, 110.0))
add(p7.T_START_C - T0, O2.thump(0.05, 0.08, 140.0, 0.2))                                       # 再生装置が動き出す
for e in GL["events"]:
    t = e["t"] - T0
    if e["kind"] == "tap": add(t, O2.thump(0.10, 0.03, 1400.0, 0.9)); add(t + 0.01, O2.clank(0.01, 0.05))      # ボタンを押す「カチッ」
DON = np.zeros_like(audio)                                                                     # 「ドン！」だけ（あとで少し大きくする）
for e in GL["events"]:
    if e["kind"] == "don":
        i_ = int((e["t"] - T0) * SR); x_ = O2.thump(0.55, 0.30, 58.0, 0.6) + np.pad(O2.thump(0.25, 0.12, 140.0, 0.4), (0, int(0.30 * SR) - int(0.12 * SR)))
        if 0 <= i_ < len(DON): j_ = min(len(DON), i_ + len(x_)); DON[i_:j_] += x_[:j_ - i_]
audio = audio + DON
sfx_peak = np.abs(audio).max(); audio = audio / max(sfx_peak, 1e-9) * 0.5; K_SFX = 0.5 / max(sfx_peak, 1e-9)
# まるロボの足音（2026-11-09 ユーザー）：塔（ch07_robot.plan_ch8）と天びん A・B（ch08_seesaw.plan_A/B）の一歩ずつ。3D を描いたときと同じ予定
import ch07_robot as RB, ch08_seesaw as SSW
steps = np.zeros_like(audio); n_st = 0
def _step_snd(k_, s_, small=False):
    if k_ == "step": return O2.thump(0.22 * (0.4 + 0.6 * s_), f=110.0 if small else 95.0, click=0.35 if small else 0.3)
    if k_ == "step_turn": return O2.thump(0.10, f=125.0 if small else 110.0, click=0.2)
    if k_ == "takeoff": return O2.thump(0.10, dur=0.10, f=72.0, click=0.25)
    if k_ == "land": return O2.thump(min(0.30, 0.11 * s_), dur=0.14, f=64.0, click=0.35)
    return None
for pl_, base_, small_, t_lo, t_hi in ((RB.plan_ch8(T0), T0, False, T0, T_2D), (SSW.plan_A(), SSW.SCN["A"]["t0"], True, SSW.SCN["A"]["t_in"], SSW.SCN["A"]["t_out"]),
                                       (SSW.plan_B(), SSW.SCN["B"]["t0"], True, SSW.SCN["B"]["t_in"], SSW.SCN["B"]["t_out"])):
    for e in pl_.events:
        x_ = _step_snd(e["kind"], float(e.get("strength", 1.0)), small_); ta_ = base_ + float(e["t"]) - (0.02 if e["kind"] == "takeoff" else 0.0)
        if x_ is None or not (t_lo <= ta_ < t_hi): continue                    # 見えている間だけ
        i_ = int((ta_ - T0) * SR)
        if 0 <= i_ < len(steps): j_ = min(len(steps), i_ + len(x_)); steps[i_:j_] += x_[:j_ - i_]; n_st += 1
audio = audio + steps * (0.18 / max(float(np.abs(steps).max()), 1e-9))       # 一番強い一歩が 0.18
print("ROBOT steps", n_st, flush=True)

# ---------------------------------------------------------------- 曲：塔が鳴らし始めてから。図に変わる所で消え、最後の塔の画で少しだけ
try:
    loop = O2.song_loop(SONG); nL = len(loop); nA = len(audio); tt = np.arange(nA) / SR + T0
    bed = loop[(np.round((tt - p7.T_START_C) * SR).astype(np.int64)) % nL]                      # 鳴らし始めが、曲の拍の頭
    lev = 0.26 * np.clip((tt - p7.T_START_C) / 0.25, 0, 1) * np.clip((T_2D + 1.2 - tt) / 1.2, 0, 1)
    lev += 0.12 * np.clip((tt - T_TOWER2) / 0.6, 0, 1) * np.clip((T_END - tt) / 0.8, 0, 1)
    audio = audio + bed * lev
except Exception as ex:
    print("SONG skipped:", ex)
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import narration as NAR
_bp = float(np.abs(audio).max())                                                               # mix_voice が全体の山を 0.5 にそろえる分
audio = NAR.mix_voice(audio, T0, SR, bus_peak=0.5, duck_db=6.0)
audio = audio + DON * K_SFX * (0.5 / max(_bp, 1e-9)) * 0.45                                     # 「ドン！」を少しだけ大きく（2026-11-09 ユーザー：＋3 dB ほど。そろえたあとに足す）
_pk = float(np.abs(audio).max()); audio = audio * (0.97 / _pk) if _pk > 0.97 else audio
with wave.open(os.path.join(OUT, "ch08_audio.wav"), "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 絵
def make_frame(i):
    t = i / FPS; ta = T0 + t
    if ta < T_2D: return tower_overlays(tower(i).resize((RW, RH)).convert("RGBA"), i, t)
    if ta < T_TOWER2: return game(t)
    return last_tower(t)

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
    stream_mp4(os.path.join(OUT, "ch08_animatic.mp4"), lambda k: make_frame(I0 + k), os.path.join(OUT, "ch08_audio.wav"), os.path.join(OUT, "ch08_subs.ass"), I1 - I0)
    sys.exit(0)
for i in range(I0, I1):
    make_frame(i).convert("RGB").save(os.path.join(SEQ, "f_%04d.png" % (i + 1)))
print("FRAMES", I0, I1, "→", SEQ, flush=True)
if "--no_video" in sys.argv: sys.exit(0)
mp4 = os.path.join(OUT, "ch08_animatic.mp4" if not RNG else "ch08_part.mp4")
cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-start_number", str(I0 + 1), "-i", os.path.join(SEQ, "f_%04d.png"),
       "-ss", "%.3f" % (I0 / FPS), "-i", os.path.join(OUT, "ch08_audio.wav"),
       "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch08_subs.ass"), O2.FONTS) if not RNG else "null",
       "-frames:v", str(I1 - I0), "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p",
       "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4]
subprocess.run(cmd, check=True)
print("WROTE", mp4)
