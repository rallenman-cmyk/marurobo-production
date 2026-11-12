# 第1・2章（本編 0:00〜1:21）の確認用動画の仕上げ：連番 → 1280×720、ナレーションの字幕（声は未収録）・カットの名前・音 → mp4
# 使い方: python3 ch0102_assemble.py OUT_DIR（OUT_DIR に ch0102_log.json と frames/ がある）
#   音：Codex版の曲（full_song.flac。38.2秒の途切れもそのまま）＋電車の走行音＋まるロボ（足音・跳ぶ・着地・ボタン）＋時間が止まる音
import sys, os, json, math, wave, subprocess
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import subs_jp as SJ                       # 字幕の共通の決まり（大きさ・改行・何枚かに分ける。2026-11-09）
import numpy as np
from PIL import Image

OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRT = os.path.join(ROOT, "handoff", "bluetooth_handoff_restored", "bt_production_v1", "output", "bluetooth_full_native.srt")
SRT_V2 = os.path.join(HERE, "..", "script", "bluetooth_full_native_rev2.srt")             # 台本 v2（2026-11-06 確定）。第1・2章の時刻は元と同じ
if os.path.exists(SRT_V2): SRT = SRT_V2
SRT_VOICE = os.path.join(HERE, "..", "script", "bluetooth_voice_rev3.srt")                # 声（Gemini・Achernar）に合わせた字幕（2026-11-07）
if os.path.exists(SRT_VOICE): SRT = SRT_VOICE
SONG = os.path.join(ROOT, "handoff", "bluetooth_handoff_restored", "restore", "v3", "bt_full_native", "audio", "full_song.flac")
FONTS = os.path.join(HERE, "..", "av", "fonts")
log = json.load(open(os.path.join(OUT, "ch0102_log.json"), encoding="utf-8"))
FPS, N = log["fps"], log["frames"]; T = N / FPS; SR = 48000
T_DROP, T_BACK, T_FREEZE, T_LAND = log["t_drop"], log["t_back"], log["t_freeze"], log["t_land"]

# ---------------------------------------------------------------- 絵（640×360 などの連番 → 1280×720。本番 MARU_RES=1080 は 1920×1080）
OUT_WH = (1920, 1080) if os.environ.get("MARU_RES") == "1080" else (1280, 720)
SEQ = os.path.join(OUT, "full"); os.makedirs(SEQ, exist_ok=True)
STREAM_ON = os.environ.get("MARU_STREAM") == "1"                   # 本番：コマを PNG に書かず、最後に ffmpeg へ直接流す（1080p の PNG はディスクに入らない）
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import cutfix                                                       # 2026-11-09：カットのつなぎ目 2 コマのブレ（カメラが飛ぶ分のモーションブラー）を、となりのコマに差し替える
REMAP = cutfix.remap(lambda i: os.path.join(OUT, "frames", "f_%04d.png" % i), [int(round(t_ * FPS)) for t_, _ in log["shots"][1:3]])   # ユーザー：ぶつ切りに見えたのは最初の 2 か所（K1→K2・K2→K3）だけ。ほかは「同じ場面でカメラを振っている」と分かるので、そのまま
def fsrc(i): return os.path.join(OUT, "frames", "f_%04d.png" % REMAP.get(i, i))
for i in range(1, N + 1):
    if STREAM_ON: break
    src = fsrc(i); dst = os.path.join(SEQ, "f_%04d.png" % i)
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src) and "--redo" not in sys.argv: continue
    Image.open(src).convert("RGB").resize(OUT_WH, Image.LANCZOS).save(dst, compress_level=1)


# ---------------------------------------------------------------- 字幕
def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def srt_lines(path):
    out = []
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        L = b.split("\n")
        if len(L) < 3 or " --> " not in L[1]: continue
        def sec(x):
            h, m, r = x.strip().split(":"); s_, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(s_) + int(ms) / 1000
        a, c = L[1].split(" --> "); out.append((sec(a), sec(c), " ".join(L[2:])))
    return out


def wrap_jp(txt, maxc=27):
    """長い1行を、真ん中に近い読点（、）で2行に分ける（ASS の改行 \\N）"""
    if len(txt) <= maxc or "\\N" in txt: return txt
    cands = [i + 1 for i, ch in enumerate(txt) if ch in "、，,。" and 6 <= i + 1 <= len(txt) - 6]
    if not cands: cut = len(txt) // 2
    else: cut = min(cands, key=lambda i: abs(i - len(txt) / 2))
    return txt[:cut] + "\\N" + txt[cut:]


NAMES = {"K1": "K1 車内の全景", "K2": "K2 音楽を聴いている人", "K3": "K3 動画を見ている人", "K4": "K4 何十組ものスマホとイヤホン",
         "K5": "K5 自分が選んだ音だけ", "K6": "K6 隣の人", "K7": "K7 （もしも）みんな同じ曲？", "K7b": "K7b みんなで踊る（想像）", "K8": "K8 そんなわけない（踊るのは主人公だけ）", "K9": "K9 音が途切れる",
         "K10": "K10 つないだ相手", "K11": "K11 まるロボ", "K12": "K12 時間を止める", "K13": "K13 止まった車内", "K14": "K14 こちらのスマホへ",
         "K15": "K15 中をのぞく → 第3章へ"}
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       SJ.STYLE_SUB,
       "Style: Shot,Noto Sans CJK JP,20,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,3,1,0,7,14,14,12,1",
       "Style: Note,Noto Sans CJK JP,18,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,3,1,0,9,14,14,12,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, txt in SJ.expand(srt_lines(SRT)):                            # 1 枚ずつ（改行入り。長い文は声の間で何枚かに）
    if a < T: ass.append("Dialogue: 0,%s,%s,Sub,,0,0,0,,{\\fad(120,120)}%s" % (ts(a), ts(min(c, T)), txt))
shots = log["shots"]
for (a, nm), (b, _) in zip(shots, shots[1:] + [[T, ""]]):
    ass.append("Dialogue: 1,%s,%s,Shot,,0,0,0,,%s　%d:%04.1f" % (ts(a), ts(b), NAMES.get(nm, nm), int(a // 60), a % 60))
ass.append("Dialogue: 1,%s,%s,Note,,0,0,0,,第1・2章（0:00〜1:21）確認用・低画質・声は Gemini（Achernar）" % (ts(0), ts(T)))
if os.environ.get("MARU_FINAL") == "1": ass = [l_ for l_ in ass if ",Note,," not in l_ and ",Shot,," not in l_]   # 本番（MARU_FINAL=1）：確認用の札（場面名・注記）を出さない
open(os.path.join(OUT, "ch0102_subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- 音
Nn = int(T * SR); t = np.arange(Nn) / SR; rng = np.random.default_rng(11)
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0", "-t", str(T), "-i", SONG, "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
song = np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, 2) / 32768.0
song_full = np.zeros((Nn, 2), np.float32); song_full[:min(len(song), Nn)] = song[:Nn]
# Codex版の曲は 55.80 秒から小さくなって 55.99 秒で無音になり、56.0 秒から次の曲に入れ替わる（元の版の場面の切り替わり）。
# この版は時間が止まるのが T_FREEZE（59.55秒）なので、その手前で曲が「ぶつん」と切れて聞こえる（2026-11-06 ユーザーの指摘）。
# 曲は 8 拍（3.08 秒＝147840 サンプル）ごとにまったく同じ音のくり返し（ずらして重ねると一致度 1.000、55.80 秒まで差 0）。
# だから 55.75 秒から先は 8 拍前の音をつないで、時間が止まるまで同じ曲を切れ目なく続ける（つなぎ目も元と同じ音なので、継ぎ目の音は出ない）
LOOP = int(round(3.08 * SR)); i_s = int(55.75 * SR)
idx = np.arange(i_s, Nn); song_full[i_s:] = song_full[i_s - LOOP + (idx - i_s) % LOOP]


def gate(a, b, fade=0.02):
    """a〜b 秒で 1（両端は fade 秒でなめらかに）"""
    g = np.clip((t - a) / fade, 0, 1) * np.clip((b - t) / fade, 0, 1); return (g * g * (3 - 2 * g)).astype(np.float32)[:, None]


# K7（想像）：曲が車内いっぱいに鳴る（少し大きく、車内の響き 0.35秒） → K8（現実）：主人公のイヤホンから漏れる小さな音 → K9：主人公の耳の中（ふつう）
T_K7, T_K8, T_K9 = 21.75, 29.878, 32.8
i0, i1 = int((T_K7 - 0.5) * SR), int((T_K8 + 0.6) * SR)
seg = song_full[i0:i1]; ir_n = int(0.35 * SR); tir = np.arange(ir_n) / SR
ir = np.stack([rng.normal(0, 1, ir_n), rng.normal(0, 1, ir_n)], 1) * np.exp(-tir / 0.09)[:, None]; ir /= np.sqrt((ir ** 2).sum(0))
L_ = len(seg) + ir_n; nf = 1 << (L_ - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(seg[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:len(seg)] for c in range(2)], 1).astype(np.float32)
big = np.zeros_like(song_full); big[i0:i1] = seg * 1.30 + wet * 0.30
j0, j1 = int((T_K8 - 0.3) * SR), int((T_K9 + 0.3) * SR)
mono = song_full[j0:j1].mean(1); nf = 1 << (len(mono) - 1).bit_length(); fq = np.fft.rfftfreq(nf, 1 / SR)
H = (1 / (1 + (500 / np.maximum(fq, 1)) ** 4)) * (1 / (1 + (fq / 4200) ** 4))      # 小さなスピーカーの音：低い音と高い音が抜ける
leak1 = np.fft.irfft(np.fft.rfft(mono, nf) * H, nf)[:len(mono)].astype(np.float32) * 0.17
leak = np.zeros_like(song_full); leak[j0:j1] = np.stack([leak1 * 0.9, leak1 * 1.1], 1)
g_big, g_leak = gate(T_K7, T_K8), gate(T_K8, T_K9, 0.008)
mix = (song_full * (1 - g_big - g_leak) + big * g_big + leak * g_leak) * 0.9


def add(buf, at, s, pan=0.0, g=1.0):
    i = int(at * SR)
    if i >= Nn or i < 0: return
    m = min(len(s), Nn - i); l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:i + m, 0] += s[:m] * g * l; buf[i:i + m, 1] += s[:m] * g * r


def thump(f1, f2, tau, n_amp=0.15, dur=0.2):
    tt = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * math.pi * f1 * tt) * 0.8 + np.sin(2 * math.pi * f2 * tt) * 0.3) * np.exp(-tt / tau) + rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.01) * n_amp


def tape_stop(buf, at, dur=0.35):
    i0 = int(at * SR); L_ = int(dur * SR)
    rate = 1 - (np.arange(L_) / L_) ** 1.6; pos = i0 + np.cumsum(rate).astype(int)
    seg = buf[np.clip(pos, 0, Nn - 1)] * (1 - np.arange(L_) / L_)[:, None]
    buf[i0:i0 + L_] = seg[:max(0, min(L_, Nn - i0))]; buf[i0 + L_:] = 0


# 電車の走行音（うなり＋レールの継ぎ目 25m ごと＝1.5秒ごと）。主人公のアップ（曲が聞こえる）では小さく
b = np.cumsum(rng.normal(0, 1, Nn)).astype(np.float32); b -= np.convolve(b, np.ones(4800) / 4800, mode="same")
b = np.convolve(b, np.ones(60) / 60, mode="same"); b /= np.abs(b).max() + 1e-9
train = np.stack([b, np.roll(b, 300)], 1) * 0.55 * 0.28
rails = np.zeros((Nn, 2), np.float32)
for k0 in np.arange(0.35, T, 1.5):
    for d, a in ((0.0, 1.0), (0.126, 0.85), (0.83, 0.8), (0.956, 0.7)): add(rails, k0 + d, thump(58, 120, 0.045), 0.0, a)
train += rails * 0.35
train *= (1 - 0.45 * g_big)                                       # 想像の場面では、電車の音を少し下げる
tape_stop(train, T_FREEZE)
song_part = mix.copy(); tape_stop(song_part, T_FREEZE, 0.5); mix = song_part + train
fx = np.zeros((Nn, 2), np.float32)
for e in log["events"]:                                            # まるロボ（電車の中では小さいので、音も軽く高め）
    k, te, s = e["kind"], e["t"], e.get("strength", 1.0)
    if te < 50.0: continue
    gq = 2.0 if te > T_FREEZE + 1.0 else 1.0                       # 止まった世界で鳴るのは、まるロボの足音だけ（2026-11-08：第2章の終わりで聞こえるように）
    if k == "step": add(fx, te, thump(170, 340, 0.02, 0.08, 0.08), -0.1, (0.10 + 0.10 * s) * gq)
    elif k == "step_turn": add(fx, te, thump(190, 380, 0.018, 0.06, 0.07), 0.0, 0.08 * gq)
    elif k == "takeoff": add(fx, te, thump(150, 300, 0.03, 0.2, 0.15), 0.0, 0.35)
    elif k == "land": add(fx, te, thump(160, 430, 0.05, 0.35, 0.3) * min(1.0, s / 3.0), 0.0, 0.7)
tt = np.arange(int(0.08 * SR)) / SR                                # ボタンの「カチッ」
btn = rng.normal(0, 1, len(tt)) * np.exp(-tt / 0.003) * 0.6 + np.sin(2 * math.pi * 1800 * tt) * np.exp(-tt / 0.012) * 0.5
add(fx, T_LAND + 0.025, btn, 0.0, 0.9)
tt = np.arange(int(5.0 * SR)) / SR                                 # 時間が止まった合図：澄んだ高い音（ゆっくり消える）
shimmer = sum(np.sin(2 * math.pi * f * tt + p) for f, p in ((1568, 0), (2093, 1.1), (2637, 2.3))) / 3 * np.exp(-tt / 1.6) * (1 - np.exp(-tt / 0.02)) * 0.16
add(fx, T_FREEZE, shimmer, 0.0, 1.0)
mix += fx
sys.path.insert(0, "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/tools"); import narration as NAR                       # 声を足す（曲は声の下。声の間は 8dB 下げる）
mix = NAR.mix_voice(mix, 0.0, SR, bus_peak=0.55, duck_db=8.0).astype(np.float32)
wav = os.path.join(OUT, "ch0102_audio.wav")
with wave.open(wav, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

mp4 = os.path.join(OUT, "ch0102_animatic.mp4")
if STREAM_ON:
    pr_ = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % OUT_WH, "-framerate", str(FPS), "-i", "-", "-i", wav,
                            "-vf", "hqdn3d=2.0:1.5:3:3,subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch0102_subs.ass"), FONTS),
                            "-frames:v", str(N), "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], stdin=subprocess.PIPE)
    for i in range(1, N + 1):
        im = Image.open(fsrc(i)).convert("RGB")
        if im.size != OUT_WH: im = im.resize(OUT_WH, Image.LANCZOS)
        pr_.stdin.write(im.tobytes())
    pr_.stdin.close()
    if pr_.wait() != 0: sys.exit("ffmpeg failed")
    print("WROTE", mp4); sys.exit(0)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(SEQ, "f_%04d.png"), "-i", wav,
                "-vf", "hqdn3d=2.0:1.5:3:3,subtitles=%s:fontsdir=%s" % (os.path.join(OUT, "ch0102_subs.ass"), FONTS),
                "-c:v", "libx264", "-crf", os.environ.get("MARU_CRF", "20"), "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], check=True)
print("WROTE", mp4)
