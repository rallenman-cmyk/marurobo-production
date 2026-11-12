# 第3章の確認用動画の仕上げ：章ぜんぶ（台本 v2：本編 81.0〜175.786）をつなぐ
#   C1・C2（81.0〜100.2）と C12（153.6〜157.8）は、電車の場面を作るまで冒頭のコマの静止画で代用（時間が止まった色）
#   C3〜C11（100.2〜153.6）は舞台の描画、C13（157.8〜166.2）は図（ch03_diagram.py）、C14（166.2〜175.786）は二つの疑問（ch03_questions.py）
#   C4 の「番号は、曲の順番です」で、上に曲の順番の帯（01〜05。03・04・05 が順に光る）を重ねる
#   ナレーションの字幕（声は未収録）・場面の名前・出来事から作る電子音・曲 → mp4
# 使い方: python3 ch03_assemble.py OUT_DIR [SRT] [SONG] [OPENING_FRAMES]（OUT_DIR に ch03_log.json・frames/・diagram/ がある）
import sys, os, json, math, subprocess, wave
import numpy as np

OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
SRT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")       # 台本 v2・声（Gemini・Achernar）に合わせた字幕
SONG = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "human", "audio", "song_mono.wav")
OPEN = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "..", "human", "op_phys", "frames")
FONTS = os.path.join(HERE, "..", "av", "fonts")
log = json.load(open(os.path.join(OUT, "ch03_log.json"), encoding="utf-8"))
FPS, N_STAGE, T_ST = log["fps"], log["frames"], log["t0"]
CH0, CH1 = 81.0, 175.786                     # 章の始まりと終わり（本編。台本 v2：終わり＝第4章の始まり）
C12_A, C13_A, C14_A = 153.6, 157.8, 166.2    # C12（あの曲）・C13（図）・C14（二つの疑問）の始まり
OFF = T_ST - CH0                             # 舞台の部分の始まり（章の中の時刻）19.2 秒
T0 = CH0; T = CH1 - CH0; N = int(round(T * FPS))
SR = 48000
RW, RH = (1920, 1080) if os.environ.get("MARU_RES") == "1080" else (1280, 720)   # 本番（MARU_RES=1080）は 1920×1080。札は 1.5 倍
KS = RW / 1280.0

# ---------------------------------------------------------------- 絵をつなぐ（代用の静止画は、彩度0.55・ゆっくり寄る）
from PIL import Image, ImageEnhance
SEQ = os.path.join(OUT, "full"); os.makedirs(SEQ, exist_ok=True)
TRAIN = sys.argv[5] if len(sys.argv) > 5 else os.path.join(HERE, "train_test")      # 電車の場面の静止画（ch03_train.py）。なければ冒頭のコマで代用
def still_clip(src, n, k0, zoom=(1.0, 1.08), center=(0.5, 0.45), gray=True, waves=None):
    im0 = Image.open(src).convert("RGB").resize((RW, RH), Image.LANCZOS)
    if gray: im0 = ImageEnhance.Color(im0).enhance(0.55)
    arr0 = np.array(im0) if waves else None
    for i in range(n):
        u = i / max(n - 1, 1); z = zoom[0] + (zoom[1] - zoom[0]) * (u * u * (3 - 2 * u))
        im = im0
        if waves:                                                     # 止まった電波の波面（光らないゆがみ）。waves = (fx, fy, 見える割合の関数, 始めの時刻)
            fx, fy, amt, t_a = waves; im = Image.fromarray(cw.apply(arr0, fx, fy, amt(t_a + i / FPS)))
        w, h = RW / z, RH / z; cx, cy = center[0] * RW, center[1] * RH
        x0 = min(max(cx - w / 2, 0), RW - w); y0 = min(max(cy - h / 2, 0), RH - h)
        im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((RW, RH), Image.LANCZOS).save(os.path.join(SEQ, "f_%04d.png" % (k0 + i)), compress_level=1)
k = 1
TRAIN_SEQ = os.path.join(TRAIN, "frames_train")                       # カメラが動く連番（ch03_train.py --anim）があれば、静止画の代わりに使う
N_TS = int(round(OFF * FPS)); I12 = int(round(68.8 * FPS)); N12 = int(round((C13_A - C12_A) * FPS))
HAVE_SEQ = os.path.isdir(TRAIN_SEQ) and all(os.path.exists(os.path.join(TRAIN_SEQ, "t_%04d.png" % i)) for i in list(range(N_TS)) + list(range(I12, I12 + N12)))
T_SCR, T_EAR, T_C2 = os.path.join(TRAIN, "train_001.0_C1_k0.png"), os.path.join(TRAIN, "train_005.0_C1.png"), os.path.join(TRAIN, "train_015.0_C2.png")
T_D1, T_D2, T_D3 = [os.path.join(TRAIN, "train_009.0_C1_k%d.png" % k) for k in (1, 2, 3)]          # 画面の上の帯：区切る→01・02→03が光る
if HAVE_SEQ:                                                         # 止まった電車をカメラが動く絵（C1・C2）。C2 の電波の波面は、コマごとのカメラで計算して重ねる
    sys.path.insert(0, HERE); import ch03_waves as cw
    tlog = {"stills": {}}
    for fn_ in sorted(os.listdir(TRAIN)):
        if fn_.startswith("train_frames_log_") and fn_.endswith(".json"):
            lg_ = json.load(open(os.path.join(TRAIN, fn_), encoding="utf-8")); st_ = lg_.pop("stills"); tlog.update(lg_); tlog["stills"].update(st_)
    def sm_(u): u = min(max(u, 0.0), 1.0); return u * u * u * (10 - 15 * u + 6 * u * u)
    amt = lambda t: sm_((t - 11.6) / 1.0) * (1 - sm_((t - 16.8) / 1.6))
    for i in range(N_TS):
        t = i / FPS; fn_ = "t_%04d.png" % i
        im = Image.open(os.path.join(TRAIN_SEQ, fn_)).convert("RGB").resize((RW, RH), Image.LANCZOS)
        if t >= 11.0 and amt(t) > 1e-3 and fn_ in tlog["stills"]:
            fx_, fy_, _ = cw.wave_field(tlog, fn_, res_out=(RW, RH), amp_px=10.0 * KS, sigma=0.014); im = Image.fromarray(cw.apply(np.array(im), fx_, fy_, amt(t)))
        im.save(os.path.join(SEQ, "f_%04d.png" % k), compress_level=1); k += 1
    C12_SRC, C12_GRAY = None, False
elif all(os.path.exists(x) for x in (T_SCR, T_EAR, T_C2)):
    sys.path.insert(0, HERE); import ch03_waves as cw
    tlog = json.load(open(os.path.join(TRAIN, "train_log.json"), encoding="utf-8"))
    wfx, wfy, _ = cw.wave_field(tlog, os.path.basename(T_C2), res_out=(RW, RH), amp_px=10.0 * KS, sigma=0.014)
    def sm_(u): u = min(max(u, 0.0), 1.0); return u * u * u * (10 - 15 * u + 6 * u * u)
    amt = lambda t: sm_((t - 11.6) / 1.0) * (1 - sm_((t - 16.8) / 1.6))   # 「電波で送っています」で現れ、「目に見えません」で消える
    segs = [(0.0, 2.85, T_SCR, (1.0, 1.06)), (2.85, 8.3, T_EAR, (1.0, 1.05))]
    if all(os.path.exists(x) for x in (T_D1, T_D2, T_D3)): segs += [(8.3, 9.1, T_D1, (1.0, 1.02)), (9.1, 9.9, T_D2, (1.02, 1.04)), (9.9, 11.0, T_D3, (1.04, 1.07))]
    else: segs += [(8.3, 11.0, T_SCR, (1.04, 1.10))]
    for a_, b_, src_, z_ in segs + [(11.0, OFF, T_C2, (1.0, 1.06))]:
        n_ = int(round(b_ * FPS)) - int(round(a_ * FPS))
        still_clip(src_, n_, k, zoom=z_, center=(0.5, 0.5), gray=False, waves=(wfx, wfy, amt, a_) if src_ == T_C2 else None); k += n_
    C12_SRC, C12_GRAY = T_SCR, False
else:
    n1 = int(round(OFF * FPS)); still_clip(os.path.join(OPEN, "f_0170.png"), n1, k, zoom=(1.0, 1.10), center=(0.62, 0.45)); k += n1
    C12_SRC, C12_GRAY = os.path.join(OPEN, "f_0300.png"), True
# C4「番号は、曲の順番です」：上に曲の順番の帯（01・02 は送ったあと、03・04・05 が窓の中の荷物。言葉に合わせて 03 → 04 → 05 と光る）
from PIL import ImageDraw, ImageFont
_L23 = [e for e in json.load(open(os.path.join(HERE, "..", "script", "script_v2_timed.json"), encoding="utf-8")) if e["text"].startswith("一つひとつに、この曲の一部分")][0]
T_NUM = _L23["start"] + (_L23["end"] - _L23["start"]) * _L23["text"].index("番号") / len(_L23["text"])
T_NUM_END = _L23["end"] + 0.05
FONT_J = os.path.join(FONTS, "japanese.ttc")
def order_strip(im, t):
    a = min(max((t - T_NUM + 0.15) / 0.3, 0.0), 1.0) * min(max((T_NUM_END - t) / 0.25, 0.0), 1.0)
    if a <= 0: return im
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); al = lambda x: int(255 * a * x)
    f1 = ImageFont.truetype(FONT_J, int(26 * KS)); f2 = ImageFont.truetype(FONT_J, int(30 * KS))
    cw, gap = 78 * KS, 12 * KS; x0 = RW / 2 - (5 * cw + 4 * gap) / 2; y0 = 58 * KS
    d.rounded_rectangle([x0 - 150 * KS, y0 - 18 * KS, x0 + 5 * cw + 4 * gap + 26 * KS, y0 + 70 * KS], radius=int(16 * KS), fill=(250, 250, 248, al(0.94)), outline=(31, 94, 102, al(1)), width=int(3 * KS))
    d.text((x0 - 78 * KS, y0 + 26 * KS), "曲の順番", font=f1, fill=(40, 46, 52, al(1)), anchor="mm")
    for j in range(5):
        x = x0 + j * (cw + gap); on = j >= 2 and t >= T_NUM + 0.25 + 0.42 * (j - 2)
        fill = (31, 94, 102, al(1)) if on else ((150, 158, 166, al(0.55)) if j < 2 else (210, 216, 222, al(1)))
        d.rounded_rectangle([x, y0, x + cw, y0 + 52 * KS], radius=int(10 * KS), fill=fill)
        d.text((x + cw / 2, y0 + 26 * KS), "%02d" % (j + 1), font=f2, fill=(255, 255, 255, al(1)) if (on or j < 2) else (90, 98, 106, al(1)), anchor="mm")
        if j < 4: d.text((x + cw + gap / 2, y0 + 26 * KS), "›", font=f1, fill=(120, 128, 136, al(1)), anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
for i in range(1, N_STAGE + 1):
    dst = os.path.join(SEQ, "f_%04d.png" % k); src = os.path.join(OUT, "frames", "f_%04d.png" % i)
    im = Image.open(src).convert("RGB").resize((RW, RH), Image.LANCZOS)
    im = order_strip(im, T_ST + (i - 1) / FPS)
    im.save(dst, compress_level=1); k += 1
n12 = int(round((C13_A - C12_A) * FPS))
if HAVE_SEQ:                                                         # C12：止まった電車に戻り、スマホの画面のアップ（カメラが動く絵）
    for i in range(I12, I12 + n12):
        Image.open(os.path.join(TRAIN_SEQ, "t_%04d.png" % i)).convert("RGB").resize((RW, RH), Image.LANCZOS).save(os.path.join(SEQ, "f_%04d.png" % k), compress_level=1); k += 1
else:
    still_clip(C12_SRC, n12, k, zoom=(1.0, 1.06), center=(0.5, 0.5), gray=C12_GRAY); k += n12
nd = int(round((C14_A - CH0) * FPS)) + 1 - k                         # C13 図（ch03_diagram.py）
n_dg = len([f_ for f_ in os.listdir(os.path.join(OUT, "diagram")) if f_.startswith("d_")])
for i in range(nd):
    src = os.path.join(OUT, "diagram", "d_%04d.png" % min(i + 1, n_dg)); Image.open(src).convert("RGB").save(os.path.join(SEQ, "f_%04d.png" % (k + i)), compress_level=1)
k += nd
nq = N + 1 - k                                                       # C14 二つの疑問（ch03_questions.py）
n_q = len([f_ for f_ in os.listdir(os.path.join(OUT, "questions")) if f_.startswith("q_")])
for i in range(nq):
    src = os.path.join(OUT, "questions", "q_%04d.png" % min(i + 1, n_q)); Image.open(src).convert("RGB").save(os.path.join(SEQ, "f_%04d.png" % (k + i)), compress_level=1)
print("FRAMES", N, "stage", N_STAGE, "diagram", nd, "questions", nq)


def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def mmss(t): return "%d:%04.1f" % (int(t // 60), t % 60)


def wrap_jp(txt, n=28):
    """長い字幕は 2 行に（句点・読点で、真ん中に近い所で折る）"""
    if len(txt) <= n: return txt
    cands = [i + 1 for i, ch in enumerate(txt[:-1]) if ch in "。、" and 6 <= i + 1 <= len(txt) - 4]
    cut = min(cands, key=lambda i: abs(i - len(txt) / 2)) if cands else len(txt) // 2
    return txt[:cut] + "\\N" + txt[cut:]


# ---------------------------------------------------------------- 字幕：ナレーション（本編の時刻から）、場面の名前、最初だけの注記
def srt_lines(path):
    out = []
    if not os.path.exists(path): return out
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        L = b.split("\n")
        if len(L) < 3 or " --> " not in L[1]: continue
        def sec(x):
            h, m, r = x.strip().split(":"); s_, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(s_) + int(ms) / 1000
        a, c = L[1].split(" --> "); out.append((sec(a), sec(c), " ".join(L[2:])))
    return out


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Main,Noto Sans CJK JP,40,&H00FFFFFF,&H00FFFFFF,&H00302418,&H64000000,-1,0,0,0,100,100,0,0,1,3.2,0,2,60,60,46,1",
       "Style: Note,Noto Sans CJK JP,19,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,3,6,0,9,0,24,18,1",
       "Style: Shot,Noto Sans CJK JP,19,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,3,6,0,7,24,0,18,1",
       "Style: Caption,Noto Sans CJK JP,26,&H00FFFFFF,&H00FFFFFF,&H00402A1A,&H8C000000,0,0,0,0,100,100,0,0,3,9,0,7,40,0,64,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
ass.append("Dialogue: 0,%s,%s,Note,,0,0,0,,第3章（%s〜%s）確認用・低画質・声は Gemini（Achernar）" % (ts(0), ts(T), mmss(T0), mmss(T0 + T)))
for a, b, txt in srt_lines(SRT):
    if b < T0 or a > T0 + T: continue
    ass.append("Dialogue: 1,%s,%s,Main,,0,0,0,,{\\fad(120,120)}%s" % (ts(a - T0), ts(min(b, T0 + T) - T0), wrap_jp(txt)))
shots = [[0.0, "C1"], [92.0 - CH0, "C2"]] + [[a + OFF, nm] for a, nm in log["shots"]] + [[C12_A - CH0, "C12"], [C13_A - CH0, "C13"], [C14_A - CH0, "C14"], [T, None]]
_KIND = "止まった車内・カメラが動く" if HAVE_SEQ else "静止画"                 # 連番（ch03_train.py --anim）があれば、カメラが動く絵
NAMES = {"C1": "C1（%s）電車：曲の画面→耳のイヤホン→画面" % _KIND, "C2": "C2（%s）止まった電波の波面（12.3cmおき）" % _KIND, "C12": "C12（%s）あの曲" % _KIND, "C13": "C13 図：送る→受け取る→音にする", "C14": "C14 二つの疑問",
         "C3": "C3 データ→荷物", "C4": "C4 曲の一部分", "C5": "C5 まるロボ", "C6": "C6 あのイヤホン（横へ引く）", "C7": "C7 見上げる", "C8": "C8 積み込み",
         "C9a": "C9 出発", "C9b": "C9 受付口を見つける", "C9c": "C9 近づく", "C10": "C10 到着", "C11": "C11 曲が鳴る",
         "M1": "道のり① 段差の台に跳び乗る", "M2": "道のり② 溝を跳び越える", "M3": "道のり③ 運河の細い橋", "C10b": "C10 受付ボックスが受け取る", "C11b": "C11 引きの絵（左にスマホ・右にイヤホン）"}
for (a, nm), (b, _) in zip(shots[:-1], shots[1:]):
    ass.append("Dialogue: 0,%s,%s,Shot,,0,0,0,,%s　%s" % (ts(a), ts(b), NAMES.get(nm, nm), mmss(T0 + a)))
ass.append("Dialogue: 2,%s,%s,Caption,,0,0,0,,{\\fad(250,250)}データを荷物に置き換えたイメージ" % (ts(OFF + 0.4), ts(OFF + 5.2)))
if os.environ.get("MARU_FINAL") == "1": ass = [l_ for l_ in ass if ",Note,," not in l_ and ",Shot,," not in l_]   # 本番（MARU_FINAL=1）：確認用の札（場面名・注記）を出さない
open(os.path.join(OUT, "ch03_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 電子音（出来事の時刻に置く。まるロボの声は使わない）
audio = np.zeros(int((T + 1.0) * SR)); rng = np.random.default_rng(3)


def env_ad(n, a=0.004, d=0.08):
    t = np.arange(n) / SR; return np.minimum(t / a, 1.0) * np.exp(-np.maximum(t - a, 0) / d)


def tone(f0, f1, dur, amp, d=None, shape="sine"):
    n = int(dur * SR); t = np.arange(n) / SR; f = f0 + (f1 - f0) * t / dur
    ph = 2 * math.pi * np.cumsum(f) / SR
    x = np.sin(ph) if shape == "sine" else (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph))
    return amp * x * env_ad(n, 0.004, d or dur * 0.6)


def lowpass(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x): s = a * s + (1 - a) * v; y[i] = s
    return y


def thump(amp, dur=0.09, f=85.0, click=0.3):
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * math.pi * f * t * (1 - 0.3 * t / dur)) * np.exp(-t / (dur * 0.35))
    nz = lowpass(rng.normal(0, 1, n), 1800) * np.exp(-t / 0.012) * click
    return amp * (body + nz)


def clank(amp, dur=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * sum(w * np.sin(2 * math.pi * f * t) * np.exp(-t / dd) for f, w, dd in ((820, 1.0, 0.09), (1310, 0.6, 0.06), (2170, 0.35, 0.04)))


def motor(dur, amp, f=150.0):
    n = int(dur * SR); t = np.arange(n) / SR; e = np.minimum(t / 0.15, 1.0) * np.minimum((dur - t) / 0.2, 1.0)
    ph = 2 * math.pi * (f * t + 6 * np.sin(2 * math.pi * 0.7 * t) / (2 * math.pi * 0.7))
    x = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph) + 0.15 * lowpass(rng.normal(0, 1, n), 900)
    return amp * x * e


def add(t, x):
    i = int(t * SR)
    if i < 0 or i >= len(audio): return
    j = min(len(audio), i + len(x)); audio[i:j] += x[:j - i]


for e in log["events"]:
    t, k, s = e["t"] + OFF, e["kind"], e["strength"]
    if t > OFF + N_STAGE / FPS: continue
    if k == "step": add(t, thump(0.22 * (0.4 + 0.6 * s), f=95.0))
    elif k == "step_turn": add(t, thump(0.10, f=110.0, click=0.2))
    elif k == "beep_yes": add(t, tone(880, 880, 0.08, 0.16)); add(t + 0.11, tone(1175, 1175, 0.10, 0.16))
    elif k == "beep_hello": add(t, tone(784, 784, 0.10, 0.13)); add(t + 0.13, tone(1047, 1047, 0.18, 0.13))
    elif k == "beep_wow": add(t, tone(480, 900, 0.45, 0.12, d=0.5)); add(t + 0.47, tone(900, 860, 0.35, 0.09, d=0.3))
    elif k == "beep_found": add(t, tone(880, 1320, 0.08, 0.13)); add(t + 0.10, tone(1320, 1760, 0.10, 0.13))
    elif k == "cradle_out": add(t, tone(180, 260, 0.5, 0.05, d=0.4, shape="buzz"))
    elif k == "cradle_in": add(t, tone(260, 170, 0.6, 0.05, d=0.5, shape="buzz"))
    elif k == "push": add(t - 0.55, motor(0.4, 0.035, 210.0)); add(t, motor(2.2, 0.045, 140.0))
    elif k == "pull":                                                  # 引き込み腕：伸びる音 → 爪が閉じる「カチッ」→ 引く音 → 戻る音
        T_ = e.get("T", 2.2); add(t - 0.9, motor(0.85, 0.03, 230.0)); add(t, thump(0.08, dur=0.05, f=900.0, click=0.6)); add(t, clank(0.03, 0.12))
        add(t + 0.3, motor(T_, 0.045, 140.0)); add(t + 0.3 + T_ + 0.02, clank(0.02, 0.08)); add(t + 0.3 + T_ + 0.2, motor(0.9, 0.022, 230.0))
    elif k == "load_done": add(t, thump(0.12, dur=0.12, f=80.0, click=0.15))
    elif k in ("lock", "unlock"): add(t, thump(0.06, dur=0.04, f=1400.0, click=0.8)); add(t + 0.03, clank(0.012, 0.06))   # 受け皿の錠「カチッ」
    elif k == "takeoff": add(t - 0.02, thump(0.10, dur=0.10, f=72.0, click=0.25))                                   # 蹴る
    elif k == "land": v_ = e.get("strength", 2.0); add(t, thump(min(0.30, 0.11 * v_), dur=0.14, f=64.0, click=0.35)); add(t + 0.01, clank(0.010, 0.08))
    elif k == "unload": add(t, tone(110, 150, 1.0, 0.06, d=0.8, shape="buzz"))
tm = {k_: v_ + OFF for k_, v_ in log["times"].items()}
# 荷物が台に乗る音と、ローラーの音（台の上を運ばれる間）
if "conv" in tm: add(tm["conv"], motor(tm.get("conv_T", 2.0), 0.02, 95.0))   # トレーごと台に移ったあと、ローラーが奥へ運ぶ
else: add(tm["t_in"] - 1.6, thump(0.14, dur=0.12, f=70.0, click=0.4)); add(tm["t_in"] - 1.6, motor(2.0, 0.02, 95.0))
# シャッター（細かい音の連なり → 閉まる音）、受付の灯（やわらかいチャイム）
for k in range(11): add(tm["shutter"] + k * 0.05, clank(0.012 + 0.002 * k, 0.05))
add(tm["shutter"] + 0.56, thump(0.12, dur=0.1, f=120.0, click=0.5)); add(tm["shutter"] + 0.56, clank(0.04))
n = int(0.9 * SR); tt = np.arange(n) / SR
add(tm["lamp"], 0.10 * sum(w * np.sin(2 * math.pi * f * tt) * np.exp(-tt / d) for f, w, d in ((1568, 1.0, 0.35), (2093, 0.6, 0.25))))
sfx_peak = np.abs(audio).max(); audio = audio / max(sfx_peak, 1e-9) * 0.55
# 曲：Codex版の同じメロディーを、曲が鳴る時刻から 7.2 秒。
#   元の曲の 145.0〜152.2 秒は、148.43 秒に 0.57 秒の無音があり、そのあと頭から鳴り直す（元の版の継ぎ目。「ぶつん」と切れて聞こえる）。
#   同じフレーズは 40.04 秒から切れ目なく続いている（145.05〜148.0 秒は 40.09〜43.04 秒と、音量が 4.5 倍違うだけで同じ音：一致度 0.996〜0.9996。
#   40.04〜47.24 秒は 8 拍＝3.08 秒ごとにまったく同じ音のくり返しで、無音なし）。大きさはあとで山をそろえるので、ここから 7.2 秒を使う
SONG_AT = 40.04
try:
    w = wave.open(SONG); sr = w.getframerate(); w.setpos(int(SONG_AT * sr)); x = np.frombuffer(w.readframes(int(7.2 * sr)), np.int16).astype(float) / 32768
    x = np.interp(np.arange(int(len(x) * SR / sr)) / SR, np.arange(len(x)) / sr, x)
    x = x / max(np.abs(x).max(), 1e-9) * 0.5; fade = np.minimum(np.arange(len(x)) / (0.03 * SR), 1.0) * np.minimum((len(x) - np.arange(len(x))) / (0.8 * SR), 1.0)   # 終わりは 0.8 秒で消えていく（図に変わる所でぷつっと止めない）
    add(tm["music"], x * fade)
    w.setpos(int(81.0 * sr)); y = np.frombuffer(w.readframes(int(3.6 * sr)), np.int16).astype(float) / 32768
    y = np.interp(np.arange(int(len(y) * SR / sr)) / SR, np.arange(len(y)) / sr, y); y = y / max(np.abs(y).max(), 1e-9) * 0.5
    y *= np.minimum(1.0, (len(y) - np.arange(len(y))) / (0.4 * SR)); add(0.0, y)
except Exception as ex:
    print("SONG skipped:", ex)
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import narration as NAR                       # 声を足す（曲・効果音は声の下。声の間は 6dB 下げる）
audio = NAR.mix_voice(audio, CH0, SR, bus_peak=0.5, duck_db=6.0)
with wave.open(os.path.join(OUT, "ch03_sfx.wav"), "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((audio * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 動画
mp4 = os.path.join(OUT, "ch03_animatic.mp4")
cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(SEQ, "f_%04d.png"), "-i", os.path.join(OUT, "ch03_sfx.wav"),
       "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch03_subs.ass"), FONTS),
       "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4]
subprocess.run(cmd, check=True)
print("WROTE", mp4)
