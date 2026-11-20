# 9本目（7本目から写した）：確認用の通しを組む（3D のクリップ＋2D の札＋字幕＋声・BGM・効果音）
# MARU_WORK=<作業フォルダ> python3 assemble.py <描いたクリップの親フォルダ> <フォントの親フォルダ> <出力.mp4> [--from 秒 --to 秒]
#   クリップ：<親>/<名前>/<名前>_NNNNN.png（--step で間引いたコマ）と <名前>_log.json（効果音・画面の場所）。clips.json（scenes.py --list）の範囲
#   つなぎ：切り替わる時刻（＝その文の字幕が出る時刻）から 0.35 秒で溶かす。章の変わり目は 0.6 秒（SKILL §3-5）
#   字幕：subs_jp.events_v（声の出ている時間で分けた字幕を替える）。BGM：bgm/bgm_bus.py（声の間は 6 dB 下げる）
#   効果音：ログの events。大事な短い音（pop・pi・snap・click）が声と重なったら、前後 0.5 秒以内の声のすき間へずらす（4本目 v10）
#   点検：<出力>_check.txt（2.2 秒以上の間・1.0 秒未満の字幕・25 字 2 行こえ・クリップの足りない所・効果音と声の重なり）
import os, sys, json, glob, wave, subprocess, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
W = os.environ["MARU_WORK"]
sys.path.insert(0, os.path.join(W, "tools"))
os.environ.setdefault("MARU_VOICE", os.path.join(W, "stage", "voice", "achernar"))
import timing as T
import overlays as OV
import sfx
import subs_jp as SJ
import subs_one as SO
RD, FONTDIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FROM = float(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0.0
TO = float(sys.argv[sys.argv.index("--to") + 1]) if "--to" in sys.argv else T.END
FPS, SR, WV, HV = 24, 48000, 1280, 720
CL = json.load(open(os.path.join(HERE, "clips.json")))
PIP_ONLY = set()      # 小窓だけに使うクリップ（本編の切り替わりに入れない）
ORDER = sorted([k for k in CL if k not in PIP_ONLY], key=lambda k: CL[k][2])
CHAPTER = {"A06", "B09", "C15", "A21", "A25", "B28", "D39", "A40"}
SEPIA = set()
# v3（5本目 v2「左上の小窓を出しつつ、メインの映像もそこのシーンを」）：26-05「ぶつかって曲がるだけだった先輩たち」で、
#   メインの絵も昔の先輩がぶつかって曲がる場面（S06b・セピア）にする：(差しかえるカット, 始め, 使うクリップ, そのクリップの秒)
REPLAY = [("A24", T.s("24-06"), "A22b", T.s("22-02") + 0.2),        # 24-06：頭が前へずれた場面をもう一度
          ("A25", T.s("25-01"), "A04c", T.w("04-03", "ころん") - 1.2)]   # 25-01：冒頭ではじかれた場面をもう一度

# ---------------------------------------------------------------- 字幕（声の終わり +0.35 秒・次の字幕の 0.05 秒前まで。1.2 秒未満なら次の前までのばす）
P = T.P
lines = []
for k, p in enumerate(P):
    nxt = P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.5
    end = max(p["end"] + 0.35, p["start"] + 1.2)
    lines.append((p["start"], min(end, nxt - 0.05), p["text"]))
# 波形で確かめた切り替わり（文の頭からの秒）。自動で選ぶと外れた所（5本目 v2 のコメント：「これを」が早い・「あれ」が遅い・「ぱっ」がだいぶ早い・改行の位置がおかしい）
#   ID: (分け方（None＝自動の分け方のまま）, [切り替わりの秒, …])。最後の 1 枚が 1.0 秒未満なら、次の文の前までのばす
FIX_AT = {}
ID_OF = {v: k for k, v in T.TEXT.items()}
NEXT_START = {p["start"]: (P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.5) for k, p in enumerate(P)}
SUBS = []
for a, c, t in lines:
    fx_ = FIX_AT.get(ID_OF.get(t))
    if fx_:
        ps_ = fx_[0] or SJ.plan_tame(t); ts_ = [a] + [a + x for x in fx_[1]]
        assert len(ps_) == len(ts_), (t, ps_)
        if c - ts_[-1] < 1.0: c = min(ts_[-1] + 1.0, NEXT_START[a] - 0.05)
        SUBS += [(ts_[i], ts_[i + 1] if i + 1 < len(ts_) else c, ps_[i]) for i in range(len(ps_))]
        continue
    # 7本目 v6：1 行ずつの字幕（subs_one.py。文の区切りで必ず分け、2 行の字幕は出さない）
    _p = SJ._placement().get(t)
    ev_ = SO.events(a, c, t, os.path.join(SJ.VOICE, "line_%03d.wav" % _p["no"]), SJ, speed=_p.get("speed", 1.0), c_max=NEXT_START[a] - 0.05)
    SUBS += [(float(x), float(y), z) for x, y, z in ev_]
SUB_STARTS = sorted(x[0] for x in SUBS)

# ---------------------------------------------------------------- クリップのコマ・ログ
LOG, FR = {}, {}
for nm in list(ORDER) + sorted(PIP_ONLY):
    d = os.path.join(RD, nm)
    lg = os.path.join(d, nm + "_log.json")
    if os.path.exists(lg): LOG[nm] = json.load(open(lg))
    fs = sorted(glob.glob(os.path.join(d, nm + "_[0-9]*.png")))
    FR[nm] = {int(os.path.basename(f)[len(nm) + 1:-4]): f for f in fs}
_img = {}


def frame(nm, t):
    """クリップ nm の時刻 t の絵（間引いたコマのうち、t より前でいちばん近いもの）"""
    if nm not in FR or not FR[nm]: return None
    t0 = CL[nm][0]; k = int(round((t - t0) * FPS))
    ks = [x for x in FR[nm] if x <= k]
    kk = max(ks) if ks else min(FR[nm])
    key = (nm, kk)
    if key not in _img:
        if len(_img) > 40: _img.clear()
        im = Image.open(FR[nm][kk]).convert("RGB").resize((WV, HV), Image.BICUBIC)
        if nm in SEPIA: im = OV.sepia(im)
        _img[key] = im
    return _img[key]


# 音の大きさ（7本目 v5「声大きい」「SEの音でかい」「叩く音うるさい」）：声 -24（v5 は -20）、効果音 0.5（v5 は 0.8）、人の打つ音はさらに 0.35 倍
VOICE_DB = -24.0; FX_GAIN = 0.5; TYPE_GAIN = 0.35


def active(t):
    """時刻 t に映すクリップと、溶かす割合：[(名前, 重み)]"""
    cur = None
    for i, nm in enumerate(ORDER):
        if CL[nm][2] <= t: cur = i
    if cur is None: return [(ORDER[0], 1.0)]
    nm = ORDER[cur]; tc = CL[nm][2]; dur = 0.6 if nm in CHAPTER else 0.35
    if cur > 0 and t < tc + dur:
        k = (t - tc) / dur; k = k * k * (3 - 2 * k)
        return [(ORDER[cur - 1], 1 - k), (nm, k)]
    return [(nm, 1.0)]


def where(name, t, clip=None):
    """2D の札をつける物の、画面の場所（1280×720）"""
    cands = [clip] if clip else [n for n, _ in active(t)][::-1]
    for nm in cands:
        if nm not in LOG or name not in LOG[nm]["track"]: continue
        tr = LOG[nm]["track"][name]; k = (t - CL[nm][0]) * FPS
        if not tr: continue
        best = min(tr, key=lambda r: abs(r[0] - k))
        if best[3] <= 0: return None
        return (best[1], best[2])
    return None


# ---------------------------------------------------------------- 音
N = int((T.END + 1) * SR)
voice = np.zeros(N, np.float32)
VD = os.environ["MARU_VOICE"]
on = np.zeros(N, np.float32)
for p in P:
    with wave.open(os.path.join(VD, "line_%03d.wav" % p["no"])) as wv:
        sr0 = wv.getframerate(); x = np.frombuffer(wv.readframes(wv.getnframes()), np.int16).astype(np.float32) / 32768
    if sr0 != SR: x = np.interp(np.arange(int(len(x) * SR / sr0)) * sr0 / SR, np.arange(len(x)), x).astype(np.float32)
    v = x[np.abs(x) > 0.01]; r = np.sqrt((v ** 2).mean() + 1e-12); x *= 10 ** (VOICE_DB / 20) / r
    # 文の頭と終わりをなめらかに（切り出しの端がいきなり大きいと「プツッ」「ザッ」と鳴る。ep02 v13「ノイズ入ってる」）
    fi, fo = int(0.012 * SR), int(0.025 * SR)
    x[:fi] *= np.linspace(0, 1, fi, dtype=np.float32) ** 2; x[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32) ** 2
    i = int(p["start"] * SR); voice[i:i + len(x)] += x[:N - i]; on[i:i + len(x)] = 1
sys.path.insert(0, os.path.join(HERE, "..", "bgm"))
import bgm_bus
SCST = {}
for p in P: SCST.setdefault(T.L[p["no"]]["scene"], p["start"])
music = bgm_bus.make(T.END + 1, SCST, SR, W)[:N]
g = np.where(on > 0, 10 ** (-6 / 20), 1.0).astype(np.float32)
kk = int(0.4 * SR)   # 0.4 秒の移動平均（累積和で。np.convolve だと何十分もかかる）
gp = np.pad(g.astype(np.float64), (kk // 2, kk - kk // 2), mode="edge"); cs_ = np.concatenate([[0.0], np.cumsum(gp)])
g = ((cs_[kk:] - cs_[:-kk]) / kk)[:N].astype(np.float32)
# 効果音（クリップのログを合わせ、同じ物は 1 つに）
EV = {}
def _seen(src, t):
    """鳴らした物（track の名前）が、時刻 t に映っているクリップの画面の中にあるか。src + "_f"（足もと）があれば、どちらかが入っていればよい"""
    if _seen1(src + "_f", t): return True
    return _seen1(src, t)


def _seen1(src, t):
    nm = max(active(t), key=lambda q: q[1])[0]
    lg = LOG.get(nm)
    if not lg or src not in lg["track"]: return False
    k = (t - CL[nm][0]) * lg["fps"]; pts = lg["track"][src]
    q = min(pts, key=lambda p: abs(p[0] - k))
    return 0 <= q[1] <= 1280 and 0 <= q[2] <= 720 and q[3] > 0
DROP = []
for nm in ORDER:
    if nm not in LOG: continue
    for e_ in LOG[nm]["events"]:
        t, kind, gain = e_[:3]; src = e_[3] if len(e_) > 3 else ""
        if (round(t, 2), kind) in EV: continue
        if src and not _seen(src, t): DROP.append((round(t, 2), kind)); EV[(round(t, 2), kind)] = 0.0; continue
        EV[(round(t, 2), kind)] = gain * (TYPE_GAIN if kind == "key" and src.startswith("typist") else 1.0)
# 打つ音（人がタイプライターを打つ音）は、続けて鳴らすのを 3 秒まで（7本目 v5「叩く音うるさい」）
_run = None
for (t, kind) in sorted(EV):
    if kind != "key" or EV[(t, kind)] == 0: continue
    if _run is None or t - _last > 0.6: _run = t
    _last = t
    if t - _run > 3.0: EV[(t, kind)] = 0.0
SHIFT = {"pop", "pi", "snap", "click", "pipi", "notify"}
fx = np.zeros(N, np.float32); moves = []; overl = []
# 効果音と声の重なりは、声が本当に出ている所（文の中の「……」の間は除く）で見る
_hop = int(0.02 * SR); _m = N // _hop
_env = np.abs(voice[:_m * _hop]).reshape(_m, _hop).max(1) > 0.02
_env = np.convolve(_env.astype(float), np.ones(5), mode="same") > 0      # 前後 0.04 秒の余白
voiced = lambda t0, t1: _env[max(0, int(t0 * SR) // _hop):max(0, int(t1 * SR) // _hop + 1)].any()
motor_on = []
for (t, kind), gain in sorted(EV.items()):
    if kind == "motor_on": motor_on.append(t); continue
    if kind == "motor_off":
        if motor_on:
            t0m = motor_on.pop(0); m1 = sfx.make("motor"); n_ = int((t - t0m) * SR)
            if n_ > 0:
                seg = np.tile(m1, n_ // len(m1) + 1)[:n_].astype(np.float32); fade = min(len(seg) // 2, int(0.25 * SR))
                seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
                i = int(t0m * SR); fx[i:i + n_] += seg[:N - i] * 0.8
        continue
    x = sfx.make(kind, SR)
    if x is None: continue
    x = x.astype(np.float32) * gain
    dur = len(x) / SR
    if kind in SHIFT and voiced(t, t + dur):
        best = None
        win = 0.9 if kind in ("pipi", "click") else 0.5     # 返事の「ピッ、ピッ」・バンパーのカチッは、言葉の「……」の間まで探す
        for d_ in np.arange(-win, win + 0.01, 0.02):
            if not voiced(t + d_, t + d_ + dur) and (best is None or abs(d_) < abs(best)): best = d_
        if best is not None: moves.append((round(t, 2), kind, round(best, 2))); t += best
        else: overl.append((round(t, 2), kind)); x = x * 0.5      # 言葉の瞬間に出る札の音：ずらせないときは半分の大きさに（声をじゃましない）
    i = int(t * SR)
    if i < 0: continue
    fx[i:i + len(x)] += x[:N - i]
# 床の音（9本目）：エスカレーターの低いうなり（昼の駅はずっと、夜は動いている間だけ）と、昼の駅のざわめき。どちらもごく小さく
def _night_run():
    """scenes._night_speed と同じ時刻で、夜のエスカレーターが動いている間（速さ 0.1 m/秒より上）"""
    t_hr = T.w("32-02", "押さえると") + 0.5; t_all = T.w("32-03", "全体が") - 0.6; t_btn = T.w("34-03", "えいっ") + 0.25
    ivs = [(T.w("09-05", "動かして") + 0.5, T.w("29-03", "止まりました") - 0.6), (T.s("30-01") + 0.8, T.w("30-03", "止まりました") - 0.6),
           (T.s("31-01") + 0.8, T.w("31-03", "止まりました") - 0.6), (T.s("32-01") + 0.8, t_all + 0.3), (T.s("34-01") + 1.0, t_btn + 0.7)]
    return ivs
NIGHT_RUN = _night_run()
def _bed_env(kind_ok):
    e = np.zeros(N, np.float32); step = int(0.05 * SR)
    for i0 in range(0, N, step):
        t = i0 / SR; act = active(t)
        if not act: continue
        nm = max(act, key=lambda q: q[1])[0]; grp = CL[nm][3]
        e[i0:i0 + step] = 1.0 if kind_ok(grp, t) else 0.0
    k = int(0.4 * SR)                                       # 0.4 秒でなめらかに出入りする
    return np.convolve(e, np.ones(k, np.float32) / k, mode="same").astype(np.float32)
def _loop(kind):
    x = sfx.make(kind, SR); return np.tile(x, N // len(x) + 1)[:N].astype(np.float32)
hum_env = _bed_env(lambda grp, t: grp == "A" or (grp == "B" and any(a <= t <= b for a, b in NIGHT_RUN)))
mur_env = _bed_env(lambda grp, t: grp == "A")
bed = 0.022 * _loop("hum") * hum_env + 0.03 * _loop("murmur") * mur_env
mix = voice + music * g + fx * FX_GAIN + bed
mix /= max(1.0, np.abs(mix).max() / 0.89)
a0, a1 = int(FROM * SR), int(TO * SR)
tmp = os.path.splitext(OUT)[0] + "_tmp"; os.makedirs(tmp, exist_ok=True)
with wave.open(os.path.join(tmp, "mix.wav"), "wb") as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix[a0:a1] * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 字幕の ASS
def ts(x): x = max(0.0, x - FROM); return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
style = SJ.STYLE_MAIN      # 9本目：フォントは Noto Sans CJK JP（fontsdir の 700Bold に置いた物）
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       style, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, t in SUBS:
    if c < FROM or a > TO: continue
    ass.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(a), ts(c), t.replace("\n", "\\N")))
open(os.path.join(tmp, "subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")
json.dump(SUBS, open(os.path.join(HERE, "subs_events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

# ---------------------------------------------------------------- 絵（1 コマずつ組んで、ffmpeg へ流す）
ffdir = os.path.join(FONTDIR, "700Bold")
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (WV, HV), "-r", str(FPS), "-i", "-",
       "-i", os.path.join(tmp, "mix.wav"), "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(tmp, "subs.ass"), ffdir),
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest", OUT]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
missing = set(); last = None
nf = int((TO - FROM) * FPS)
for fi in range(nf):
    t = FROM + fi / FPS
    act = active(t); im = None
    for nm, wgt in act:
        f_ = frame(nm, t)
        for r_nm, r0, r_clip, r_src in REPLAY:     # 前の場面をもう一度（メインの絵を差しかえる。頭は 0.35 秒で溶かす）
            if nm == r_nm and t >= r0:
                g_ = frame(r_clip, r_src + (t - r0))
                if g_ is not None:
                    kq = min(1.0, (t - r0) / 0.35); kq = kq * kq * (3 - 2 * kq)
                    f_ = g_ if (f_ is None or kq >= 1) else Image.blend(f_, g_, kq)
        if f_ is None: missing.add(nm); continue
        im = f_.copy() if im is None else Image.blend(im, f_, wgt)
    if im is None: im = last if last is not None else Image.new("RGB", (WV, HV), (20, 24, 32))
    last = im
    base = im.convert("RGBA")
    OV.draw(t, base, where, frame_of=frame, fontdir=FONTDIR)
    pr.stdin.write(base.convert("RGB").tobytes())
    if fi % 1200 == 0: print("%.0f 秒" % t, flush=True)
pr.stdin.close(); pr.wait()

# ---------------------------------------------------------------- 点検
chk = []
gaps = [(P[k]["end"], P[k + 1]["start"] - P[k]["end"], T.L[P[k + 1]["no"]]["id"]) for k in range(len(P) - 1) if P[k + 1]["start"] - P[k]["end"] >= 2.2]
chk.append("2.2 秒以上の間：" + ("、".join("%.1f 秒（%s の前）" % (g_, i_) for _, g_, i_ in gaps) or "なし"))
short = [(a, c - a, t) for a, c, t in SUBS if c - a < 1.0]
chk.append("1.0 秒未満の字幕：" + ("、".join("%.1f秒 %.2f 秒「%s」" % (a, d_, t[:12]) for a, d_, t in short) or "なし"))
over = [t for a, c, t in SUBS if any(SJ.width(r) > 25 for r in t.split("\\N")) or t.count("\\N") > 1]
chk.append("鳴らした効果音（時刻・種類・大きさ）：" + "、".join("%.1f %s %.2f" % (t, k, g) for (t, k), g in sorted(EV.items()) if g > 0))
chk.append("映っていないので鳴らさなかった効果音：" + ("、".join("%.1f %s" % x for x in sorted(DROP)) or "なし"))
chk.append("25 字・2 行をこえる字幕：" + ("、".join(over) or "なし"))
chk.append("絵の足りないクリップ：" + ("、".join(sorted(missing)) or "なし"))
chk.append("声のすき間へずらした効果音：" + ("、".join("%.2f %s → %+.2f 秒" % m for m in moves) or "なし"))
chk.append("声と重なるので半分の大きさにした効果音（札が言葉の瞬間に出る音）：" + ("、".join("%.2f %s" % m for m in overl) or "なし"))
small = [p.get("text") for t0_, t1_, kind, p in OV.EVENTS if kind == "tag" and p.get("size", 48) < 44]
chk.append("44 より小さい札の字：" + ("、".join(small) or "なし（札 48・年や数 56〜60）"))
cps = []
for p in P:
    d_ = p["end"] - p["start"]; c_ = len(p["text"].replace("…", "").replace("、", "").replace("。", ""))
    if d_ > 0 and not (4.0 <= c_ / d_ <= 9.5): cps.append("%s %.1f字/秒" % (T.L[p["no"]]["id"], c_ / d_))
chk.append("極端に遅い・速い声（4〜9.5 字/秒の外）：" + ("、".join(cps) or "なし"))
open(os.path.splitext(OUT)[0] + "_check.txt", "w", encoding="utf-8").write("\n".join(chk) + "\n")
print("\n".join(chk))
print("→ %s（%.1f MB）" % (OUT, os.path.getsize(OUT) / 1e6))
