# 5本目：確認用の通しを組む（3D のクリップ＋2D の札＋字幕＋声・BGM・効果音）
# MARU_WORK=<作業フォルダ> python3 assemble.py <描いたクリップの親フォルダ> <フォントの親フォルダ> <出力.mp4> [--from 秒 --to 秒]
#   クリップ：<親>/<名前>/<名前>_NNNNN.png（--step で間引いたコマ）と <名前>_log.json（効果音・画面の場所）。clips.json（scenes.py --list）の範囲
#   つなぎ：切り替わる時刻（＝その文の字幕が出る時刻）から 0.35 秒で溶かす。章の変わり目は 0.6 秒（SKILL §3-5）
#   S06（昔の先輩）はセピア。字幕：subs_jp.events_v（声の出ている時間で分けた字幕を替える）。BGM：bgm/bgm_bus.py（声の間は 6 dB 下げる）
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
RD, FONTDIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FROM = float(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0.0
TO = float(sys.argv[sys.argv.index("--to") + 1]) if "--to" in sys.argv else T.END
FPS, SR, WV, HV = 24, 48000, 1280, 720
FINAL = os.environ.get("MARU_FINAL") == "1"          # 本番：PC の絵（pc_frames.py の jpg・1 フォルダにまとめて）を 1920×1080 で組む。札は 1280×720 で描いて広げる
if FINAL: WV, HV = 1920, 1080
CL = json.load(open(os.path.join(HERE, "clips.json")))
ORDER = sorted(CL, key=lambda k: CL[k][2])
CHAPTER = {"S04a", "S06a", "S09a", "S13a", "S18a", "S22a", "S26a", "S27a"}
SEPIA = {"S06a", "S06b", "S06c"}
# v3（5本目 v2「左上の小窓を出しつつ、メインの映像もそこのシーンを」）：26-05「ぶつかって曲がるだけだった先輩たち」で、
#   メインの絵も昔の先輩がぶつかって曲がる場面（S06b・セピア）にする：(差しかえるカット, 始め, 使うクリップ, そのクリップの秒)
REPLAY = [("S26a", T.s("26-05"), "S06b", T.s("06-07") + 0.5)]

# ---------------------------------------------------------------- 字幕（声の終わり +0.35 秒・次の字幕の 0.05 秒前まで。1.2 秒未満なら次の前までのばす）
P = T.P
lines = []
for k, p in enumerate(P):
    nxt = P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.5
    end = max(p["end"] + 0.35, p["start"] + 1.2)
    lines.append((p["start"], min(end, nxt - 0.05), p["text"]))
# 波形で確かめた切り替わり（文の頭からの秒）。自動で選ぶと外れた所（5本目 v2 のコメント：「これを」が早い・「あれ」が遅い・「ぱっ」がだいぶ早い・改行の位置がおかしい）
#   ID: (分け方（None＝自動の分け方のまま）, [切り替わりの秒, …])。最後の 1 枚が 1.0 秒未満なら、次の文の前までのばす
FIX_AT = {"15-10": (None, [5.2]), "16-03": (None, [2.25]), "21-01": (None, [3.2]),
          "26-05": (["ぶつかって曲がるだけだった先輩たちは、", "いつの間にか自分で地図を\\N描けるようになっていました。"], [3.05])}
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
    ev_ = SJ.events_v(a, c, t)
    for i in range(len(ev_) - 1):        # 分けた字幕の 1 枚が 1.0 秒より短いときは、次の札を少し後ろへ（次も 1.0 秒は残す）
        a0, c0, t0 = ev_[i]; a1, c1, t1 = ev_[i + 1]
        if c0 - a0 < 1.0 and c1 - (a0 + 1.0) >= 1.0: ev_[i] = (a0, a0 + 1.0, t0); ev_[i + 1] = (a0 + 1.0, c1, t1)
    SUBS += ev_


def _lay2(txt):
    """字幕 1 枚を、1 行 25 字までの 1〜2 行に置き直す（だめなら None）"""
    s = txt.replace("\\N", "")
    if len(s.replace(" ", "")) <= 25: return s
    Q = SJ._cands(s); b_ = SJ._two(s, 0, len(s), Q)
    if not b_: return None
    r1, r2 = s[:b_[1]], s[b_[1]:]
    return r1 + "\\N" + r2 if max(len(r1), len(r2)) <= 25 else None


def _fix_subs(S, lines, end_all):
    """v8（2026-11-20 の字幕の決まり）：1 枚 2 秒以上・1 行 25 字まで。①短い札は、次の札の前まで（2 秒まで）のばす
    ②まだ短ければ、同じ文の隣の札とまとめる（2 行に置き直す）③1 行が長い札は 2 行に置き直す"""
    S = sorted(S)
    sid = lambda a: next((k for k, (la, lc, lt) in enumerate(lines) if la - 0.01 <= a <= lc + 0.01), -1)
    for _ in range(200):
        ch = False
        for i, (a, c, txt) in enumerate(S):
            nx = S[i + 1][0] if i + 1 < len(S) else end_all
            if c - a < 2.0:
                c2 = min(a + 2.0, nx - 0.05)
                if c2 > c + 1e-3: S[i] = (a, c2, txt); ch = True; break
                if i + 1 < len(S) and sid(S[i + 1][0]) == sid(a):
                    m = _lay2(txt + S[i + 1][2])
                    if m: S[i:i + 2] = [(a, S[i + 1][1], m)]; ch = True; break
                if i > 0 and sid(S[i - 1][0]) == sid(a):
                    m = _lay2(S[i - 1][2] + txt)
                    if m: S[i - 1:i + 1] = [(S[i - 1][0], c, m)]; ch = True; break
                if i > 0 and c - a < 2.0 and a - S[i - 1][0] > 2.3:       # ④前の札を少し縮めて、出すのを最大 0.2 秒早める（前の札も 2 秒は残す）
                    a2 = max(c - 2.0, a - 0.2, S[i - 1][0] + 2.05)
                    if a2 < a - 1e-3: S[i - 1] = (S[i - 1][0], min(S[i - 1][1], a2 - 0.05), S[i - 1][2]); S[i] = (a2, c, txt); ch = True; break
            if any(len(r) > 25 for r in txt.split("\\N")):
                m = _lay2(txt)
                if m and m != txt: S[i] = (a, c, m); ch = True; break
        if not ch: break
    return S


SUBS = _fix_subs(SUBS, lines, T.END)
SUB_STARTS = sorted(x[0] for x in SUBS)

# ---------------------------------------------------------------- クリップのコマ・ログ
LOG, FR = {}, {}
for nm in ORDER:
    d = os.path.join(RD, nm)
    if FINAL: d = RD
    lg = os.path.join(d, nm + "_log.json")
    if os.path.exists(lg): LOG[nm] = json.load(open(lg))
    fs = sorted(glob.glob(os.path.join(d, nm + "_[0-9]*.png")) + glob.glob(os.path.join(d, nm + "_[0-9]*.jpg")))
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


def where_box(name, t, clip=None):
    """物の形を画面に写した箱 (x0, y0, x1, y1)（track(..., box=True) で記録したもの）"""
    cands = [clip] if clip else [n for n, _ in active(t)][::-1]
    for nm in cands:
        if nm not in LOG or name + "#box" not in LOG[nm]["track"]: continue
        tr = LOG[nm]["track"][name + "#box"]; k = (t - CL[nm][0]) * FPS
        if not tr: continue
        best = min(tr, key=lambda r: abs(r[0] - k))
        if best[5] <= 0: return None
        return tuple(best[1:5])
    return None


OV.BOX[0] = where_box


# ---------------------------------------------------------------- 音
N = int((T.END + 1) * SR)
voice = np.zeros(N, np.float32)
VD = os.environ["MARU_VOICE"]
on = np.zeros(N, np.float32)
for p in P:
    with wave.open(os.path.join(VD, "line_%03d.wav" % p["no"])) as wv:
        sr0 = wv.getframerate(); x = np.frombuffer(wv.readframes(wv.getnframes()), np.int16).astype(np.float32) / 32768
    if sr0 != SR: x = np.interp(np.arange(int(len(x) * SR / sr0)) * sr0 / SR, np.arange(len(x)), x).astype(np.float32)
    v = x[np.abs(x) > 0.01]; r = np.sqrt((v ** 2).mean() + 1e-12); x *= 10 ** (-20 / 20) / r
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
for nm in ORDER:
    if nm not in LOG: continue
    a_, b_ = CL[nm][0], CL[nm][1]
    for t, kind, gain in LOG[nm]["events"]:
        if any(k_ == kind and abs(t_ - t) < 0.05 for (t_, k_) in EV if abs(t_ - t) < 0.05): continue     # v7：カットごとの記録で 0.01 秒ずれた同じ音は 1 つに
        EV[(round(t, 2), kind)] = gain
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
mix = voice + music * g + fx * 0.8
mix /= max(1.0, np.abs(mix).max() / 0.89)
a0, a1 = int(FROM * SR), int(TO * SR)
tmp = os.path.splitext(OUT)[0] + "_tmp"; os.makedirs(tmp, exist_ok=True)
with wave.open(os.path.join(tmp, "mix.wav"), "wb") as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix[a0:a1] * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 字幕の ASS
def ts(x): x = max(0.0, x - FROM); return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
style = SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP")
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       style, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, t in SUBS:
    if c < FROM or a > TO: continue
    ass.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(a), ts(c), t.replace("\n", "\\N")))
open(os.path.join(tmp, "subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")
open(OUT[:-4] + ".ass", "w", encoding="utf-8").write("\n".join(ass) + "\n")       # 関所（pre_upload_gate.py）が読む字幕
json.dump(SUBS, open(os.path.join(HERE, "subs_events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

# ---------------------------------------------------------------- 絵（1 コマずつ組んで、ffmpeg へ流す）
ffdir = os.path.join(FONTDIR, "700Bold")
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (WV, HV), "-r", str(FPS), "-i", "-",
       "-i", os.path.join(tmp, "mix.wav"), "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(tmp, "subs.ass"), ffdir),
       "-c:v", "libx264"] + (["-preset", "medium", "-crf", "18"] if FINAL else ["-preset", "veryfast", "-crf", "30"]) + ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k" if FINAL else "96k", "-shortest", OUT]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
missing = set(); last = None; OVL = {}
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
    if FINAL:
        lay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); OV.draw(t, lay, where, frame_of=frame, fontdir=FONTDIR)
        if lay.getbbox(): base.alpha_composite(lay.resize((WV, HV), Image.LANCZOS))
    else:
        OV.draw(t, base, where, frame_of=frame, fontdir=FONTDIR)
    for pr_ in OV.overlaps(): OVL.setdefault(pr_, []).append(t)
    pr.stdin.write(base.convert("RGB").tobytes())
    if fi % 1200 == 0: print("%.0f 秒" % t, flush=True)
pr.stdin.close(); pr.wait()

# ---------------------------------------------------------------- 点検
chk = []
ovl_txt = []
for (na, nb), ts in sorted(OVL.items(), key=lambda x: x[1][0]):
    ovl_txt.append("%d:%04.1f〜%d:%04.1f %s × %s" % (ts[0] // 60, ts[0] % 60, ts[-1] // 60, ts[-1] % 60, na, nb))
chk.append("重なっている札・吹き出し・枠（2D どうし）：" + ("、".join(ovl_txt) or "なし"))
gaps = [(P[k]["end"], P[k + 1]["start"] - P[k]["end"], T.L[P[k + 1]["no"]]["id"]) for k in range(len(P) - 1) if P[k + 1]["start"] - P[k]["end"] >= 2.2]
chk.append("2.2 秒以上の間：" + ("、".join("%.1f 秒（%s の前）" % (g_, i_) for _, g_, i_ in gaps) or "なし"))
short = [(a, c - a, t) for a, c, t in SUBS if c - a < 1.0]
chk.append("1.0 秒未満の字幕：" + ("、".join("%.1f秒 %.2f 秒「%s」" % (a, d_, t[:12]) for a, d_, t in short) or "なし"))
over = [t for a, c, t in SUBS if any(SJ.width(r) > 25 for r in t.split("\\N")) or t.count("\\N") > 1]
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
