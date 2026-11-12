# 会話と広告の回：全部の場面（3D の試し描き・2D の場面）をつなぎ、札・効果音・声・字幕を重ねた通しを作る
# MARU_WORK=<作業フォルダ> python3 assemble.py <フォントのフォルダ> <出力.mp4> <コマのフォルダ>...（場面の log.json とコマがある所）
#   場面の順：PARTS。足りない場面は、絵コンテの絵（storyboard/board/bXX_nosub.png）で埋める
#   札：OVERLAYS（台詞の番号で出す時刻を決める）。字は 44 以上、字幕の帯（下から 196px）にかけない
#   効果音：各場面の log.json の events・steps から合成（sfx.py）。声のある所は 6 dB 下げる
#   BGM：bgm/bgm_bus.py（曲B を基本に、場面に合わせて曲C・D）。声のある所は 6 dB 下げる
#   REMUX=<前に作った通し.mp4> を付けると、絵は作り直さずに、その絵に新しい音（声・効果音・BGM）だけを付け直す
#   出力と一緒に <出力>_check.txt（点検の結果）を書く
import os, sys, json, glob, subprocess, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.join(HERE, "..")
W_ = os.environ["MARU_WORK"]
FONTS, OUT, DIRS = sys.argv[1], sys.argv[2], sys.argv[3:]
FONT = os.path.join(FONTS, "NotoSansJP_700Bold.ttf")
TAGF, BIGF = ImageFont.truetype(FONT, 46), ImageFont.truetype(FONT, 72)
NAVY = (20, 36, 72)
P = json.load(open(os.path.join(EP, "voice", "placement.json"), encoding="utf-8"))
SID = {e["no"]: e for e in json.load(open(os.path.join(EP, "voice", "script_v1_0.json"), encoding="utf-8"))}
T = {SID[p["no"]]["id"]: (p["start"], p["end"]) for p in P}
def s(i, k=0): return T[i][k]
END = P[-1]["end"] + 2.0
PARTS = ["s00", "s01", "s02", "s03", "s04", "s05", "s06a", "s06b", "gate", "phone", "s09", "s10", "s11", "s12",
         "s13", "s14", "s15", "s16", "s17", "s18", "s19", "s20", "s21", "s22"]
BOARD = dict(s00=0, s01=1, s02=2, s03=3, s04=4, s05=5, s06a=6, s06b=6, gate=7, phone=8, s09=9, s10=10, s11=11, s12=12,
             s13=13, s14=14, s15=15, s16=16, s17=17, s18=18, s19=19, s20=20, s21=21, s22=22)
tmp = W_ + "/assemble_tmp"; os.makedirs(tmp, exist_ok=True)
SUB_TOP = 720 - 40 - 72 * 2 - 12   # 字幕の帯の上の端（2 行のとき）


# ---------------- 札（透明の 1280×720 の絵を作り、出す時刻のあいだだけ重ねる）
def tag_png(name, items):
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); d = ImageDraw.Draw(im); boxes = []
    for it in items:
        kind = it[0]
        if kind == "tag":
            _, text, cx, cy, tail, big = (list(it) + [None, False])[:6]
            font = BIGF if big else TAGF
            bb = d.textbbox((0, 0), text, font=font); w, th = bb[2] - bb[0], bb[3] - bb[1]; h = th + 30
            cx = min(max(cx, w / 2 + 30), 1250 - w / 2)
            x0, y0, x1, y1 = cx - w / 2 - 22, cy - h / 2, cx + w / 2 + 22, cy + h / 2
            if tail:
                by = y1 - 2 if tail[1] > cy else y0 + 2
                d.polygon([(cx - 16, by), (cx + 16, by), tail], fill="white", outline=NAVY)
            d.rounded_rectangle([x0, y0, x1, y1], 18, fill="white", outline=NAVY, width=4)
            d.text((x0 + 22 - bb[0], cy - th / 2 - bb[1]), text, font=font, fill=NAVY)
            boxes.append((text, x0, y0, x1, y1, font.size))
        elif kind == "ring":
            _, cx, cy, rx, ry = it
            d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(255, 138, 42), width=8)
        elif kind == "img":
            _, path, x, y, w = it
            sub = Image.open(path).convert("RGBA"); sub = sub.resize((w, int(sub.height * w / sub.width))); im.alpha_composite(sub, (x, y))
        elif kind == "wifi":
            _, cx, cy, ends = it
            for r in (90, 62, 34): d.arc([cx - r, cy - r, cx + r, cy + r], 225, 315, fill="white", width=12)
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill="white")
            for x, y in ends:
                for k in range(0, 100, 10):
                    a = (cx + (x - cx) * k / 100, cy + (y - cy) * k / 100); b = (cx + (x - cx) * (k + 5) / 100, cy + (y - cy) * (k + 5) / 100)
                    d.line([a, b], fill="white", width=6)
        elif kind == "dark":   # 「6時間前」の前に画面を暗く
            d.rectangle([0, 0, 1280, 720], fill=(0, 0, 0, 150))
    p = os.path.join(tmp, "ov_%s.png" % name); im.save(p)
    return p, boxes


def picbubble(name, cx, cy, r, drawer):
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white", outline=NAVY, width=4)
    d.ellipse([cx - r * 0.9 - 30, cy + r * 0.7, cx - r * 0.9, cy + r * 0.7 + 30], fill="white", outline=NAVY, width=3)
    drawer(d, cx, cy, r)
    p = os.path.join(tmp, "ov_%s.png" % name); im.save(p); return p, []


def leaf(d, cx, cy, r):
    pts = [(cx + r * (0.75 if i % 2 == 0 else 0.35) * math.cos(math.radians(90 + i * 36)), cy - r * (0.75 if i % 2 == 0 else 0.35) * math.sin(math.radians(90 + i * 36))) for i in range(10)]
    d.polygon(pts, fill=(217, 71, 43)); d.line([(cx, cy), (cx, cy + r * 0.7)], fill=(120, 40, 20), width=6)


def tent(d, cx, cy, r):
    d.polygon([(cx - r * 0.6, cy + r * 0.45), (cx, cy - r * 0.55), (cx + r * 0.6, cy + r * 0.45)], fill=(233, 105, 44))
    d.polygon([(cx - r * 0.15, cy + r * 0.45), (cx, cy + r * 0.05), (cx + r * 0.15, cy + r * 0.45)], fill=(122, 46, 18))


SB = os.path.join(EP, "storyboard")
def night_inset():
    """22-03：夜中、まるロボがスマホでキャンプの動画を見ている（小さな絵）"""
    im = Image.new("RGBA", (420, 260), (12, 20, 38, 255)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 419, 259], 18, outline=(255, 255, 255), width=5)
    d.rounded_rectangle([230, 60, 330, 230], 14, fill=(34, 38, 43)); im.paste(Image.open(os.path.join(SB, "tent.png")).convert("RGBA").resize((84, 112)), (238, 80))
    d.ellipse([70, 90, 200, 220], fill=(244, 246, 247)); d.ellipse([150, 125, 205, 180], fill=(33, 193, 179)); d.ellipse([168, 142, 188, 162], fill=(11, 39, 48))
    d.polygon([(205, 150), (238, 110), (238, 190)], fill=(207, 239, 255, 120))
    p = os.path.join(tmp, "inset22.png"); im.save(p); return p


OVERLAYS = []   # (始まり, 終わり, png, 札の箱)
def ov(a, b, name, items): p, bx = tag_png(name, items); OVERLAYS.append((a, b, p, bx))
def ovp(a, b, pb): OVERLAYS.append((a, b, pb[0], pb[1]))

ov(6.2, 7.19, "s00_6h", [("dark",), ("tag", "6時間前", 640, 300, None, True)])
ov(s("01-01") + 0.8, s("01-02") + 1.0, "s01_a", [("tag", "今度、キャンプ行きたいね", 400, 110, (420, 250))])
ov(s("01-02") + 0.6, s("01-03") + 0.2, "s01_b", [("tag", "いいね！", 900, 150, (880, 260))])
ovp(s("01-03"), s("01-03", 1) + 0.3, picbubble("s01_tent", 760, 300, 70, tent))
ov(s("04-04"), s("04-04", 1) + 0.3, "s04_title", [("tag", "さっき話した物が、なぜ広告に出る？", 640, 110, None, False)])
ov(s("05-02"), s("05-06", 1), "s05_1", [("tag", "①マイク", 230, 70)])
ov(s("05-03"), s("05-06", 1), "s05_2", [("tag", "②出ていく手がかり", 627, 165)])
ov(s("05-04b"), s("05-06", 1), "s05_3", [("tag", "③わたしたちの記憶", 1040, 70)])
ov(s("06-02") + 0.5, s("06-02", 1), "s06_ring", [("ring", 830, 392, 200, 62)])
ov(s("07-02") + 0.3, s("07-02b", 1), "s07_guard", [("tag", "見張り番", 1100, 120)])
ov(s("07-04") + 0.5, s("07-04", 1) + 0.3, "s07_word", [("tag", "Hey Siri", 640, 110, None, True), ("tag", "OK Google", 640, 230)])
ov(s("08-08") - 1.3, s("08-08") + 2.5, "s08_similar", [("tag", "Hey, Siri-al（ヘイ、シリアル）", 640, 110)])
ov(s("08-11") - 1.3, s("08-11") + 2.5, "s08_real", [("tag", "Hey Siri", 640, 110, None, True)])
_dot = None
for _d in DIRS:
    _p = os.path.join(_d, "phone_log.json")
    if os.path.exists(_p): _dot = json.load(open(_p)).get("dot2d") or None; break
if _dot: ov(s("08-14") + 0.4, s("08-15", 1), "s08_dot", [("ring", _dot[0], _dot[1], 70, 70)])   # 3D で計算した点の位置
ov(s("10-05"), s("10-05", 1), "s10_drop", [("tag", "いた場所", 640, 110)])
ov(s("10-06"), s("10-06", 1), "s10_square", [("tag", "見たページ", 640, 110)])
ov(s("10-07"), s("10-07", 1), "s10_two", [("tag", "一緒にいた人", 640, 110)])
ov(s("12-04") + 1.5, s("12-05b", 1), "s12_cards", [("tag", "いた場所", 330, 110), ("tag", "見たページ", 640, 110), ("tag", "一緒にいた人", 960, 110)])
ov(s("13-03"), s("13-04", 1), "s13_phone", [("img", os.path.join(SB, "phone_ad.png"), 1010, 170, 160), ("tag", "ソラさんのスマホ", 1060, 90)])
ov(s("13-05") + 0.3, s("13-06", 1), "s13_wifi", [("wifi", 640, 150, ((300, 380), (900, 380)))])
ovp(s("14-01"), s("14-01b") + 1.0, picbubble("s14_leaf", 760, 300, 70, leaf))
ov(s("15-03") + 2.0, s("15-04", 1), "s15_q", [("tag", "？枚", 640, 300, None, True)])
for k, x in enumerate((70, 640, 1210)):
    ov(s("15-05") + 1.4 * k, s("15-06", 1), "s15_%d" % k, [("ring", x, 300, 80, 90), ("tag", str(k + 1), x, 170, None, True)])
ov(s("16-06"), s("16-06", 1), "s16", [("tag", "当たり", 470, 150), ("tag", "外れ", 1050, 330)])
ov(s("18-03"), s("18-03", 1) + 0.5, "s18", [("tag", "メールアドレスの名簿", 900, 110)])
ov(s("21-02"), s("21-02", 1), "s21", [("tag", "ピポ、ピポ", 980, 170)])
ov(s("22-03"), s("22-03", 1), "s22_inset", [("img", night_inset(), 820, 60, 420)])

# ---------------- 絵の並び（場面ごとのコマ。間引いたコマは長さで埋める）
logs, rows = {}, []
for k in PARTS:
    lg = None
    for d in DIRS:
        p = os.path.join(d, k + "_log.json")
        if os.path.exists(p) and glob.glob(os.path.join(d, k + "_[0-9]*.png")):
            lg = json.load(open(p)); lg["dir"] = d; break
    logs[k] = lg
SCST = {}
for p in P:
    SCST.setdefault(SID[p["no"]]["scene"], max(0.0, p["start"] - 0.4))
SCST["S00"] = 0.0
_sk = list(SCST)
SCEND = {k: (SCST[_sk[i + 1]] if i + 1 < len(_sk) else END) for i, k in enumerate(_sk)}
t_prev = 0.0
missing = []
for k in PARTS:
    lg = logs[k]
    if lg is None:
        missing.append(k); continue
    fs = sorted(glob.glob(os.path.join(lg["dir"], k + "_[0-9]*.png")))
    nums = [int(os.path.basename(x)[len(k) + 1:-4]) for x in fs]
    lim = min(lg["t1"], SCEND["S%02d" % BOARD[k]] if k != "gate" else SCEND["S08"])   # 場面の終わり（次の場面の始まり）で切る
    for i, (pth, n) in enumerate(zip(fs, nums)):
        a = lg["t0"] + n / 24
        b = min(lim, lg["t0"] + (nums[i + 1] / 24 if i + 1 < len(nums) else lg["frames"] / 24))
        if a < lim - 1e-6: rows.append((a, b, pth))
rows.sort()
# 足りない場面・すき間は絵コンテの絵で埋める
fill, cur = [], 0.0
SC = {}
for p in P:
    sc_ = SID[p["no"]]["scene"]
    SC.setdefault(sc_, p["start"] - 0.4)
for a, b, pth in rows + [(END, END, None)]:
    while a - cur > 0.05:                                    # すき間を場面の境目ごとに分けて、その場面の絵コンテで埋める
        sc_ = max([k for k, v in SCST.items() if v <= cur + 0.01] or ["S00"], key=lambda k: SCST[k])
        e = min(a, SCEND[sc_])
        fill.append((cur, e, os.path.join(SB, "board", "b%02d_nosub.png" % int(sc_[1:]))))
        cur = e
    cur = max(cur, b)
allrows = sorted(rows + fill)
# 大きさの違う絵（3D の試し描き・2D・絵コンテ）を一度に並べると時刻がずれるので、続いている同じ場面ごとに
# 1280×720・24 コマ/秒の短い動画にしてから、つなぐ
runs = []
for a, b, pth in allrows:
    grp = os.path.dirname(pth) + "|" + os.path.basename(pth).split("_")[0]
    if runs and runs[-1][0] == grp and abs(runs[-1][2] - a) < 1e-3:
        runs[-1][2] = b; runs[-1][3].append((a, b, pth))
    else:
        runs.append([grp, a, b, [(a, b, pth)]])
REMUX = os.environ.get("REMUX")
if REMUX: runs = []
seg_list = os.path.join(tmp, "segs.txt")
with open(seg_list, "w") as fs_:
    for i, (grp, a, b, items) in enumerate(runs):
        l = os.path.join(tmp, "seg_%03d.txt" % i); sp = os.path.join(tmp, "seg_%03d.mp4" % i)
        with open(l, "w") as fo:
            for a2, b2, pth in items: fo.write("file '%s'\nduration %.4f\n" % (pth, b2 - a2))
            fo.write("file '%s'\n" % items[-1][2])
        n = round((b - a) * 24)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", l,
                        "-vf", "scale=1280:720,setsar=1,fps=24,format=yuv420p", "-frames:v", str(n),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", sp], check=True)
        fs_.write("file '%s'\n" % sp)
lst = os.path.join(tmp, "video.mp4")
if not REMUX: subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", seg_list, "-c", "copy", lst], check=True)

# ---------------- 効果音
sys.path.insert(0, HERE)
import sfx
sr = 48000
sfx_bus = np.zeros(int(END * sr), np.float32)
ev_all = []
for k, lg in logs.items():
    if not lg: continue
    ev_all += [(t, kd) for t, kd in lg.get("events", [])]
    ev_all += [(t, "step") for t in lg.get("steps", [])]
for t, kd in ev_all:
    x = sfx.make(kd, sr)
    if x is None: continue
    i = int(t * sr); sfx_bus[i:i + len(x)] += x[:max(0, len(sfx_bus) - i)]
# 声（アニマティックの声：ピー入り、24 kHz）を 48 kHz に
with wave.open(W_ + "/animatic_tmp/voice.wav") as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; vsr = w.getframerate()
v = np.interp(np.arange(int(len(v) * sr / vsr)) / sr, np.arange(len(v)) / vsr, v).astype(np.float32)
voice = np.zeros_like(sfx_bus); voice[:min(len(v), len(voice))] = v[:len(voice)]
# 声のある所は効果音を 6 dB 下げる（上がり 0.12 秒・下がり 0.35 秒）
env = np.ones_like(sfx_bus)
for p in P:
    a, b = int((p["start"] - 0.12) * sr), int((p["end"] + 0.35) * sr); env[max(0, a):b] = 10 ** (-6 / 20)
k = int(0.05 * sr); env = np.convolve(env, np.ones(k) / k, mode="same")
# BGM（声のある所は 6 dB 下げる。効果音と同じ下げ方）
sys.path.insert(0, os.path.join(EP, "bgm"))
import bgm_bus
music = bgm_bus.make(END, SCST, sr)[:len(voice)]
mix = voice + sfx_bus * env * 0.5 + music * env
mix /= max(1.0, np.abs(mix).max() / 0.89)
with wave.open(tmp + "/mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ---------------- 字幕（アニマティックと同じ）
ev = json.load(open(os.path.join(EP, "animatic", "subs_events.json"), encoding="utf-8"))
def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Main,Noto Sans JP,56,&H00FFFFFF,&H00FFFFFF,&H00301A10,&H96000000,-1,0,0,0,100,100,1,0,1,5,2.2,2,50,50,40,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, t in ev: ass.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(a), ts(c), t.replace("\n", "\\N")))
open(tmp + "/subs.ass", "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------- 組み立て（絵 → 札 → 字幕、声と効果音）
inputs = ["-i", lst]
fl = ["[0:v]scale=1280:720,fps=24,setsar=1[v0]"]
for i, (a, b, pth, _) in enumerate(OVERLAYS):
    inputs += ["-i", pth]
    fl.append("[v%d][%d:v]overlay=0:0:enable='between(t,%.3f,%.3f)'[v%d]" % (i, i + 1, a, b, i + 1))
fl.append("[v%d]subtitles=%s:fontsdir=%s[vout]" % (len(OVERLAYS), tmp + "/subs.ass", FONTS))
inputs += ["-i", tmp + "/mix.wav"]
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fl), "-map", "[vout]", "-map", "%d:a" % (len(OVERLAYS) + 1),
       "-c:v", "libx264", "-preset", "medium", "-crf", os.environ.get("CRF", "27"), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", os.environ.get("ABR", "128k"), "-t", "%.2f" % END, OUT]
if REMUX:
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", REMUX, "-i", tmp + "/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
           "-c:a", "aac", "-b:a", os.environ.get("ABR", "128k"), "-t", "%.2f" % END, OUT]
subprocess.run(cmd, check=True)

# ---------------- 点検
chk = []
chk.append("足りない場面（絵コンテの絵で埋めた）：%s" % (", ".join(missing) or "なし"))
for a, b, pth, bx in OVERLAYS:
    for text, x0, y0, x1, y1, fs in bx:
        if fs < 44: chk.append("札の字が小さい：%s（%d）" % (text, fs))
        subs_on = any(c > a and e < b for e, c, _ in ev)
        if subs_on and y1 > SUB_TOP: chk.append("札が字幕の帯にかかる：%s（%.1f〜%.1f 秒）" % (text, a, b))
for i, (a, b, *_r) in enumerate(OVERLAYS):
    for a2, b2, *_r2 in OVERLAYS[i + 1:]:
        if a < b2 and a2 < b:
            for t1_ in _r[1]:
                for t2_ in _r2[1]:
                    if not (t1_[3] < t2_[1] or t2_[3] < t1_[1] or t1_[4] < t2_[2] or t2_[4] < t1_[2]):
                        chk.append("札どうしが重なる：%s と %s" % (t1_[0], t2_[0]))
ov_sfx = []
for t, kd in ev_all:
    for p in P:
        if p["start"] - 0.05 < t < p["end"] and kd in ("jump", "land", "pi", "pipo", "win", "rise", "clatter", "lamp", "gate_up"):
            ov_sfx.append("%.1f %s（%s）" % (t, kd, SID[p["no"]]["id"])); break
chk.append("声と重なる大きめの効果音：%d か所 %s" % (len(ov_sfx), "／".join(ov_sfx[:20])))
gaps = [(P[i + 1]["start"] - P[i]["end"], SID[P[i + 1]["no"]]["id"]) for i in range(len(P) - 1)]
chk.append("2.2 秒以上の間：%s" % ([g for g in gaps if g[0] >= 2.2] or "なし"))
chk.append("1.0 秒未満の字幕：%s" % ([e for e in ev if e[1] - e[0] < 1.0] or "なし"))
open(OUT + "_check.txt", "w", encoding="utf-8").write("\n".join(chk) + "\n")
print("\n".join(chk))
print(OUT, "%.1f MB" % (os.path.getsize(OUT) / 1e6))
