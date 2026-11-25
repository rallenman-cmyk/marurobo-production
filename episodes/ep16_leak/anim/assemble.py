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
PIP_ONLY = {"P02", "P09"}      # 小窓だけに使うクリップ（本編の切り替わりに入れない）
ORDER = sorted([k for k in CL if k not in PIP_ONLY], key=lambda k: CL[k][2])
CHAPTER = {"T05", "B06", "I07", "N12", "D13", "A14", "D14j", "O15", "D16", "O16c", "M16", "D16f", "M16b", "D17", "D17d", "I17", "D17f", "E18a", "E19a", "E22c", "A22c", "E23b"}   # 舞台が変わる所（重ねるつなぎ 0.6 秒）。2章を足した
SEPIA = set()
# v3（5本目 v2「左上の小窓を出しつつ、メインの映像もそこのシーンを」）：26-05「ぶつかって曲がるだけだった先輩たち」で、
#   メインの絵も昔の先輩がぶつかって曲がる場面（S06b・セピア）にする：(差しかえるカット, 始め, 使うクリップ, そのクリップの秒)
REPLAY = []   # 冒頭・1章は差し替えなし

# ---------------------------------------------------------------- 字幕（声の終わり +0.35 秒・次の字幕の 0.05 秒前まで。1.2 秒未満なら次の前までのばす）
P = T.P
lines = []
for k, p in enumerate(P):
    nxt = P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.5
    end = max(p["end"] + 0.35, p["start"] + 1.2)
    lines.append((p["start"], min(end, nxt - 0.05), p["text"]))
# 波形で確かめた切り替わり（文の頭からの秒）。自動で選ぶと外れた所（5本目 v2 のコメント：「これを」が早い・「あれ」が遅い・「ぱっ」がだいぶ早い・改行の位置がおかしい）
#   ID: (分け方（None＝自動の分け方のまま）, [切り替わりの秒, …])。最後の 1 枚が 1.0 秒未満なら、次の文の前までのばす
FIX_AT = {
    # 16本目 v1：自動の切り替わり（文の頭から 3.86 秒）は「流出の」のあとの小さな谷で、「発表が」が次の字幕に入った（聞き取りで分かった）。
    #   本当の切れ目は 4.74 秒（「発表が、」のあと）だが、そこで切ると「次々に続きました。」が 1.8 秒になるので、2 行の 1 枚にする
    "04-01": (["2026年の秋、こうした流出の発表が、\\N次々に続きました。"], []),
}
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
SUBS = [(a_, c_, t_.strip("　 ")) for a_, c_, t_ in SUBS]   # 分けた頭に残る空白を取る（9本目 v2「　すぐに止まった…」）
SUBS = SO.balance(sorted(SUBS), MIN=2.02, CPS=7.9)      # 2 秒に足りない字幕は、となりから時間を借りる（7本目 v8 の作り）   # 時刻を 1/100 秒に切り捨てても 2 秒・8 字を割らないよう、少しゆとりを持たせる（9本目 v2：2.00 秒が 1.99 秒・8.0 字が 8.01 字になった）
json.dump(SUBS, open(os.path.join(HERE, "subs_events_pre.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)   # 声の切れ目へ合わせる前（subs_sync.py を試すため）
import subs_sync as SY     # 9本目 v2：切り替わりを声の切れ目へ（関所 subs_sync_check.py で 10 枚がずれていた。時刻で長さを合わせず、足りない 1 枚はとなりとまとめる）
SUBS = SY.fix(SUBS, json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8")),
              os.path.join(os.environ.get("MARU_WORK", ""), "stage", "voice", "achernar"))
# 16本目：1 行が 25 字をこえる字幕は、まん中に近い「、」で 2 行にする（関所の「1 行 25 字まで」。1 か所だけでなく全部に効く）
def _wrap(t_):
    out = []
    for ln in t_.split("\\N"):
        if len(ln) > 25:
            cut = [i + 1 for i, ch in enumerate(ln[:-1]) if ch in "、。？！"]
            if cut:
                c_ = min(cut, key=lambda i: abs(i - len(ln) / 2)); out += [ln[:c_], ln[c_:]]; continue
        out.append(ln)
    return "\\N".join(out)
SUBS = [(a_, c_, _wrap(t_)) for a_, c_, t_ in SUBS]
# 16本目 v1：「……」でためたあとの答えは別の字幕にする（台本 v0.2 のコメント「やっぱり以降はテロップ別にして」・SKILL）。
#   声の切れ目へ合わせる道具（subs_sync）が、短い答えの文（「やっぱり、だめ。」1.0 秒）を前の「……」の字幕にまとめていた。
#   「……\N」で 2 つの文がつながった字幕は、答えの文の声の頭で分け、答えが 2 秒に足りなければ、次の字幕の上の行にする
def _split_tame(S):
    S = sorted(S); out = []; i = 0
    while i < len(S):
        a_, c_, t_ = S[i]
        if "……\\N" in t_:
            x_, y_ = t_.split("……\\N", 1); x_ += "……"
            tb = next((p["start"] for p in P if p["text"].startswith(y_[:6]) and a_ < p["start"] < c_), None)
            if tb is not None:
                out.append((a_, tb - 0.05, x_))
                if c_ - tb >= 2.0 or i + 1 >= len(S) or "\\N" in S[i + 1][2] or len(S[i + 1][2]) > 25:
                    out.append((tb, c_, y_))
                else:
                    S[i + 1] = (tb, S[i + 1][1], y_ + "\\N" + S[i + 1][2])
                i += 1; continue
        out.append(S[i]); i += 1
    return out
SUBS = _split_tame(SUBS)
# 16本目 v2（v1 のコメント「テロップの切り替わりが早い」2 件・「……え？」の 1 枚が遅い）：
#   ① 1 枚の中で文が変わる字幕（「……え？\Nそれは、」）は、文の切れ目で分ける（字幕をまとめるのは同じ文の中だけ。SKILL）
#   ② 字幕 1 枚ずつ、最初の言葉を声が言い始める 0.05 秒前に替える。続けて読んでいる所では分けない（subs_mora.py）
#   ③ 2 秒に足りない 1 枚は、短い声（「……え？」など 8 字まで、1 秒以上）なら残して 字幕_ため.json に書き、ほかは同じ文のとなりとまとめる
import re as _re
import subs_mora as SM
def _split_sent(S):
    out = []
    for a, c, t in S:
        parts = [x for x in _re.split(r"(?<=[。？！])(?:\\N)?", t) if x.strip()]
        if len(parts) == 1: out.append((a, c, t)); continue
        L = sum(len(x) for x in parts); x0 = a
        for x in parts:
            x1 = x0 + (c - a) * len(x) / L; out.append((x0, x1, x.replace("\\N", ""))); x0 = x1
    return out
SUBS = _split_sent(SUBS)
_SC = {e["no"]: e for e in json.load(open(os.path.join(HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
SUBS, SM_MOVED, SM_MERGED = SM.fix(SUBS, P, _SC, os.environ["MARU_VOICE"])
TAME = []
def _min2(S):
    """2 秒に足りない 1 枚：短い 1 文（8 字まで・1 秒以上）は残す。ほかは同じ声（文の番号）の中のとなりとまとめる。声をまたいではまとめない"""
    S = [list(x) for x in sorted(S)]
    while True:
        loc = SM._locate([tuple(x) for x in S], P); ch = False
        for i, (a, c, t) in enumerate(S):
            if c - a >= 2.0: continue
            keep = len(t.replace("\\N", "")) <= 8 and c - a >= 1.0
            if keep and _re.search(r"(？|！|……)$", t):          # ため・問いの短い 1 枚（「……え？」）は、答えと別の字幕のまま
                TAME.append(t); continue
            if keep and t.endswith("。") and (i + 1 >= len(S) or loc[i + 1] is None or loc[i] is None or loc[i + 1][0] != loc[i][0]):
                TAME.append(t); continue                         # 1 つの声が短い 1 文だけ（「やっぱり、だめ。」）
            for j in (i + 1, i - 1):
                if not (0 <= j < len(S)) or loc[j] is None or loc[i] is None: continue
                li = loc[i][0]; lj = loc[j][0]
                if li != lj: continue                            # 声（文の番号）をまたいではまとめない
                x, y = (S[j], S[i]) if j < i else (S[i], S[j])
                tt = x[2] + ("\\N" if len(x[2].replace("\\N", "")) + len(y[2].replace("\\N", "")) > 25 else "") + y[2]
                if tt.count("\\N") > 1 or any(len(z) > 25 for z in tt.split("\\N")): continue
                S[min(i, j)] = [x[0], y[1], tt]; del S[max(i, j)]; ch = True; break
            if ch: break
        if not ch: return [tuple(x) for x in S]
SUBS = _min2(SUBS)
def _head_lead(S):
    """（16本目 2章）2 秒にわずかに足りない、文の頭の 1 枚（ためでない）は、頭を声より少し前（0.12 秒まで）に出して 2 秒にする。
    文の声の頭からのずれは 0.25 秒以内（関所の測りの決まり）。前の字幕とは 0.05 秒あける。「まるロボの名札です！」が 1.93 秒で、次の文までのばせなかった"""
    S = sorted(S); heads = {round(p["start"], 3) for p in P}
    for i, (a, c, t) in enumerate(S):
        need = 2.02 - (c - a)
        if need < 0.01 or t in TAME or need > 0.12 or not any(abs(a - h) < 0.06 for h in heads): continue      # 字幕の頭は声の頭の 0.05 秒前に合わせてあるので、少しの差は同じ文の頭とみる
        prev_end = S[i - 1][1] if i else -1.0
        if a - need < prev_end + 0.05 and i:              # 前の字幕（声のあとの余韻の所）を同じだけ早く消す。前も 2 秒以上・前の声の終わりより後のまま
            pa, pc, pt = S[i - 1]; npc = a - need - 0.05
            pv = max([q["end"] for q in P if q["start"] <= pa + 0.01] or [0.0])
            if npc - pa >= 2.02 and npc >= pv: S[i - 1] = (pa, npc, pt); prev_end = npc
        if a - need >= prev_end + 0.05: S[i] = (a - need, c, t); print("字幕の頭を前へ：%.2f 秒 %s（%.2f 秒）" % (a, t, need))
    return S
SUBS = _head_lead(SUBS)
SUBS = [(a_, c_, _wrap(t_)) for a_, c_, t_ in SUBS]
json.dump(sorted(set(TAME)), open(os.path.join(HERE, "..", "字幕_ため.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
SUB_STARTS = sorted(x[0] for x in SUBS)
if os.environ.get("SUBS_ONLY"): json.dump(SUBS, open(os.path.join(HERE, "subs_events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0); sys.exit(0)

# ---------------------------------------------------------------- クリップのコマ・ログ
LOG, FR = {}, {}
for nm in list(ORDER) + sorted(PIP_ONLY):
    d = os.path.join(RD, nm)
    lg = os.path.join(d, nm + "_log.json")
    if os.path.exists(lg): LOG[nm] = json.load(open(lg))
    fs = sorted(glob.glob(os.path.join(d, nm + "_[0-9]*.png")))
    FR[nm] = {int(os.path.basename(f)[len(nm) + 1:-4]): f for f in fs}
_img = {}
# 場面の終わりと、溶けて切りかわる間は、その場面を止めた絵にする（9本目 v3：次の場面のために人物を置き直すのが、
# 溶ける間や切りかわりの直前に見えて、消えたり、追うカメラが壁に入って暗くなった）。
# 止める時刻：次の場面の 0.1 秒前。それより前 0.6 秒の間に、映っている人物が 1 コマで 150px 以上飛ぶ所があれば、その手前
def _hold(nm, tn):
    h = tn - 0.1; lg = LOG.get(nm)
    if not lg: return h
    for ob in ("maru_c", "ojisan", "ball"):
        tr = lg["track"].get(ob) or []
        for p_, q_ in zip(tr, tr[1:]):
            t_ = lg["t0"] + q_[0] / lg["fps"]
            if not (tn - 0.6 <= t_ <= tn + 0.4): continue
            on_ = lambda r: 0 <= r[1] <= 1280 and 0 <= r[2] <= 720 and r[3] > 0
            if not (on_(p_) or on_(q_)): continue
            if ((p_[1] - q_[1]) ** 2 + (p_[2] - q_[2]) ** 2) ** 0.5 / max(1, q_[0] - p_[0]) > 150:
                h = min(h, lg["t0"] + p_[0] / lg["fps"])
    return h
HOLD = {ORDER[i]: _hold(ORDER[i], CL[ORDER[i + 1]][2]) for i in range(len(ORDER) - 1)}


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
VOICE_DB = -24.0; FX_GAIN = 1.1; TYPE_GAIN = 0.35   # 16本目 v10：曲を +7 dB したら効果音が曲の下に埋もれた（箱の「シュッ」が曲より 16 dB 下）→ 効果音も +7 dB（0.5→1.1）


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
for p in P: SCST.setdefault(T.L[p["no"]]["id"], p["start"])   # 曲を文の頭で替えられるように（16本目：「22-05」などの文の番号でも PLAN に書ける）
music = bgm_bus.make(T.END + 1, SCST, SR, W)[:N]
g = np.where(on > 0, 10 ** (-3 / 20), 1.0).astype(np.float32)   # 16本目 3章 v9「bgm全然聞こえない・途切れ途切れ」：-6 dB を 0.4 秒で上げ下げしていて、文の間ごとに曲が出たり消えたり（141 秒で 168 回）→ -3 dB を 1.2 秒でゆっくり
kk = int(1.2 * SR)   # 0.4 秒の移動平均（累積和で。np.convolve だと何十分もかかる）
gp = np.pad(g.astype(np.float64), (kk // 2, kk - kk // 2), mode="edge"); cs_ = np.concatenate([[0.0], np.cumsum(gp)])
g = ((cs_[kk:] - cs_[:-kk]) / kk)[:N].astype(np.float32)
# 効果音（クリップのログを合わせ、同じ物は 1 つに）
EV = {}
EVSRC = {}      # 映っている物が鳴らす音（扉・箱・紙など）。声と重なっても時刻をずらさない（16本目 2章の確認役：鍵の「カチャ」を声のすき間へ 0.6 秒ずらし、扉の動きとずれた）
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
        _act = active(t)       # その時刻に映っているカットの記録からだけ取る（17本目の決まり。16本目 2章：先に描いた別のカットの古い記録で、声の「ガチャン」の音が消えた）
        if not _act or max(_act, key=lambda q: q[1])[0] != nm: continue
        if src and not _seen(src, t): DROP.append((round(t, 2), kind)); EV[(round(t, 2), kind)] = 0.0; continue
        EV[(round(t, 2), kind)] = gain * (TYPE_GAIN if kind == "key" and src.startswith("typist") else 1.0)
        if src: EVSRC[(round(t, 2), kind)] = src
for (t_, k_, g_) in OV.sfx_list():      # 16本目：札・図に合わせて鳴らす音（絵の物の記録にない音）
    EV[(round(t_, 2), k_)] = g_
# 16本目 v10：曲を大きくしたら、足音と小さな物の音が曲に埋もれた（測った差：走る足音 -1 dB・歩く足音 -14 dB・箱の「シュッ」-7 dB・影の「チャリン」+2 dB）
#   → 走る足音（0.15 以上）は 2 倍、歩く足音は 1.6 倍。紙・シュッ・チャリンは 0.45 より小さくしない（描き直さずに、組み立てで上げる）
for k__ in list(EV):
    g__ = EV[k__]
    if g__ <= 0: continue
    if k__[1] == "step": EV[k__] = g__ * (2.0 if g__ >= 0.15 else 1.6)
    elif k__[1] in ("paper", "swish", "jingle"): EV[k__] = max(g__, 0.45)
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
FINAL = []      # 本当に鳴らした音（時刻・種類・大きさ・鳴らした物）。点検で、絵の動きと比べる
for (t, kind), gain in sorted(EV.items()):
    t0_ev = t
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
    if kind in SHIFT and (round(t, 2), kind) not in EVSRC and voiced(t, t + dur):
        best = None
        win = 0.9 if kind in ("pipi", "click") else 0.5     # 返事の「ピッ、ピッ」・バンパーのカチッは、言葉の「……」の間まで探す
        for d_ in np.arange(-win, win + 0.01, 0.02):
            if not voiced(t + d_, t + d_ + dur) and (best is None or abs(d_) < abs(best)): best = d_
        if best is not None: moves.append((round(t, 2), kind, round(best, 2))); t += best
        else: overl.append((round(t, 2), kind)); x = x * 0.5      # 言葉の瞬間に出る札の音：ずらせないときは半分の大きさに（声をじゃましない）
    i = int(t * SR)
    if i < 0: continue
    fx[i:i + len(x)] += x[:N - i]
    if gain > 0: FINAL.append((round(t, 2), kind, round(float(gain), 3), EVSRC.get((round(t0_ev, 2), kind), "")))
# 16本目：駅の環境音（9本目の床の音）は使わない。夜の虫の声などは効果音（crickets）で鳴らす
bed = 0.0
mix = voice + music * g + fx * FX_GAIN + bed
if os.environ.get("MARU_DUMP_STEMS"):   # 調べる用：曲（下げたあと）と声を別に保存
    np.save(os.environ["MARU_DUMP_STEMS"] + "_music.npy", (music * g)[int(FROM * SR):int(TO * SR)]); np.save(os.environ["MARU_DUMP_STEMS"] + "_voice.npy", voice[int(FROM * SR):int(TO * SR)]); np.save(os.environ["MARU_DUMP_STEMS"] + "_fx.npy", (fx * FX_GAIN)[int(FROM * SR):int(TO * SR)])
mix /= max(1.0, np.abs(mix).max() / 0.89)
a0, a1 = int(FROM * SR), int(TO * SR)
tmp = os.path.splitext(OUT)[0] + "_tmp"; os.makedirs(tmp, exist_ok=True)
json.dump([x for x in FINAL if FROM - 1 <= x[0] <= TO + 1], open(os.path.join(tmp, "sfx_final.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
with wave.open(os.path.join(tmp, "mix.wav"), "wb") as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix[a0:a1] * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- 字幕の ASS
def ts(x): x = math.floor(max(0.0, x - FROM) * 100 + 1e-6) / 100; return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)   # 頭も終わりも 1/100 秒に切り捨て（四捨五入で 2.00 秒の字幕が 1.99 秒になった。9本目 v2）
style = SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP")      # 16本目 v1 のユーザー「テロップのフォント違う」：この作業場所の 700Bold にあるのは Noto Sans JP（CJK と同じ字の形）。
#   名前が合わないと、ffmpeg は別の字（丸い字）に置きかえていた。名前は fc-scan で調べた物を使う
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
# 字幕のフォントが本当に置いてあるかを確かめる（無いと ffmpeg は黙って別の字にする。16本目 v1 のユーザー「テロップのフォント違う」）
_fam = style.split(",")[1]
_have = subprocess.run(["fc-scan", "--format", "%{family}\n"] + glob.glob(os.path.join(ffdir, "*.tt[fc]")) + glob.glob(os.path.join(ffdir, "*.otf")), capture_output=True, text=True).stdout
if _fam not in [x.strip() for l in _have.splitlines() for x in l.split(",")]:
    raise SystemExit("字幕のフォント「%s」が %s にない（あるのは %s）" % (_fam, ffdir, _have.split()))
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (WV, HV), "-r", str(FPS), "-i", "-",
       "-i", os.path.join(tmp, "mix.wav"), "-vf", "subtitles=%s:fontsdir=%s" % (os.path.join(tmp, "subs.ass"), ffdir),
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest", OUT]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
missing = set(); last = None
nf = int((TO - FROM) * FPS)
for fi in range(nf):
    t = FROM + fi / FPS
    act = active(t); im = None
    for i_, (nm, wgt) in enumerate(act):
        # 溶けて切りかわる間、前の場面はその直前の絵で止める（9本目 v3：場面の先で人物を次の場所へ置き直すので、溶ける間に消えたり、追うカメラが壁に入って暗くなった）
        f_ = frame(nm, min(t, HOLD.get(nm, 1e9)))
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
chk.append("終わりを早めに止めた場面（置き直しの手前）：" + ("、".join("%s %.2f 秒前" % (k_, CL[ORDER[ORDER.index(k_) + 1]][2] - v_) for k_, v_ in HOLD.items() if CL[ORDER[ORDER.index(k_) + 1]][2] - v_ > 0.11) or "なし"))
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
