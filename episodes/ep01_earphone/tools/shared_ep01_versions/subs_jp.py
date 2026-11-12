# メインの字幕（ナレーションの字幕）の共通の決まり（2026-11-09 ユーザー：小さくて読みにくい・改行の位置が日本語として不自然）
#   ・大きさ：1280×720 の座標で 56（1080p では 84。2026-11-09 ユーザー「もう少しだけ大きく」で 50 → 56。25 字の行で画面の幅の 78%）。太字・白・濃い紺の太い縁（5）＋やわらかい影
#     明るい図の上でも、暗い 3D の上でも読める
#   ・1 行は全角 25 文字まで（2026-11-09 ユーザー指定。前は 20）、2 行まで。1 枚に入らない文は、文の終わり（。？）や読点の所で次の字幕に送る
#   ・改行と分け方は文の切れ目（文節）で：句点 ＞ 読点 ＞ 助詞の後（次が漢字・カタカナ）。
#     「の」の後（自分の｜曲）、言い切りでない動詞の後（届いた｜荷物）、カタカナ語や数字の途中、行頭の「、」「ー」「っ」などは避ける。
#     そのうえで行の長さがそろう所。二つの文を 1 枚に入れるときは、文の終わりで改行する
#   ・何枚かに分けた文は、声の「間」（息つぎ）で次の字幕に替える（声のファイルの無音を探す。見つからなければ文字数の割合）
#   ・全 189 文（と第4章 6:24 の②）を一覧で読み、変な所は OVERRIDES で手で決める
#   使い方（組み立てのスクリプトから）：
#     import subs_jp as SJ
#     ass に SJ.STYLE_MAIN（または SJ.STYLE_SUB）を入れ、for a, c, txt in SJ.expand(srt_lines(SRT)): … txt はもう改行入り
#   一覧：python3 subs_jp.py placement.json [--times]
import re, os, json

MAXC = 25.0                                                        # 2026-11-09 ユーザー：1行は最大25文字・最大2行（前は 20）
STYLE_MAIN = "Style: Main,Noto Sans CJK JP,56,&H00FFFFFF,&H00FFFFFF,&H00301A10,&H96000000,-1,0,0,0,100,100,1,0,1,5,2.2,2,50,50,40,1"
STYLE_SUB = STYLE_MAIN.replace("Style: Main,", "Style: Sub,")
VOICE = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/voice/achernar"

SENT = "。？！"
P1 = set("はがをにでともへや")                                        # 一文字の助詞
PM = ("から", "まで", "ので", "のに", "けど", "ても", "でも", "たら", "れば", "ながら", "より", "など", "だけ", "しか", "ほど", "ように")
NO_HEAD = set("、。，．・？！ー）」』〕】ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ…")
NO_TAIL = set("（「『〔【")
SMALL = set("ぁぃぅぇぉっゃゅょゎ")
KATA = re.compile(r"[ァ-ヴー]")
KANJI = re.compile(r"[一-龯々〆ヶ]")
HIRA = re.compile(r"[ぁ-ゖ]")
ALNUM = re.compile(r"[0-9A-Za-z０-９Ａ-Ｚａ-ｚ]")
ATTR = set("るたいなだ")                                             # 言い切りでない形（後ろの言葉にかかる）の終わり

# 手で決めた分け方（キー＝元の文、値＝字幕の枚数ぶんの「1行目\\N2行目」）
OVERRIDES = {
    "ここでは、スマホとイヤホンが持っている「ひみつ」を、絵の具の色にたとえてみます。": ["ここでは、スマホとイヤホンが\\N持っている「ひみつ」を、", "絵の具の色にたとえてみます。"],   # 55
    "すると……どちらも同じ紫色に。どちらにも、白と青と赤が同じだけ入っているからです。": ["すると……どちらも同じ紫色に。", "どちらにも、白と青と赤が\\N同じだけ入っているからです。"],   # 65
    "もし、隣のイヤホンが見えた二つを混ぜても……青と赤は入りますが、白が二回分入るので、薄い紫にしかなりません。": ["もし、隣のイヤホンが見えた二つを混ぜても……", "青と赤は入りますが、", "白が二回分入るので、薄い紫にしかなりません。"],   # 第4章 6:24 の②
    "その音を長く待たせれば、操作した瞬間と、聞こえる瞬間が離れてしまいます。": ["その音を長く待たせれば、\\N操作した瞬間と、聞こえる瞬間が離れてしまいます。"],   # 172
    "それは、ほかの電波に邪魔されたりして、次に鳴らすデータが間に合わなくなることがあるからです。": ["それは、ほかの電波に邪魔されたりして、", "次に鳴らすデータが\\N間に合わなくなることがあるからです。"],   # 183
}

for _k, _v in OVERRIDES.items():                                  # 手で決めた分け方が、元の文と同じ字か確かめる
    assert "".join(_v).replace("\\N", "") == _k, _k


def width(s):
    """見た目の幅（全角 1、半角の英数字 0.55）"""
    s = s.replace("\\N", "")
    return sum(0.55 if ord(ch) < 0x2000 else 1.0 for ch in s)


def _q(t, k):
    """t[:k] | t[k:] で改行・分けるときの悪さ（小さいほどよい）。だめな所は None"""
    a, b = t[k - 1], t[k]
    if b in NO_HEAD or a in NO_TAIL: return None
    if a in SENT: return 0.0
    if a == "、": return 1.0
    if a == "…": return 1.5
    if KATA.match(a) and KATA.match(b): return None
    if ALNUM.match(a) and ALNUM.match(b): return None
    newword = bool(KANJI.match(b) or KATA.match(b) or ALNUM.match(b) or b in "「『（")
    if a in "」』）": return 2.0 if newword else None
    if not HIRA.match(a) or a in SMALL: return None
    if newword:
        if any(t[:k].endswith(m) for m in PM): return 2.5           # から｜鳴らす
        if a in P1: return 3.0                                      # 曲を｜鳴らす
        if a == "の": return 9.0                                    # 自分の｜曲（なるべく使わない）
        r = k - 1
        while r > 0 and HIRA.match(t[r - 1]): r -= 1
        if k - r == 1 and r > 0 and (KANJI.match(t[r - 1]) or KATA.match(t[r - 1])): return None   # 受け｜取る（送りがなの途中）
        if a in "おご": return 8.0                                  # お｜待たせ
        if a in ATTR: return 7.0                                    # 届いた｜荷物
        return 5.0                                                  # もう｜一度
    if a in P1 and b not in P1 and b not in "のいっ": return 4.5    # イヤホンが｜すぐ
    return None


def _cands(t):
    return {k: q for k in range(2, len(t) - 1) for q in [_q(t, k)] if q is not None}


def _two(t, j, i, Q):
    """t[j:i] を 2 行にする一番よい改行（悪さ, 位置）。だめなら None"""
    best = None
    for k, q in Q.items():
        if not (j + 1 < k < i - 1): continue
        l1, l2 = width(t[j:k]), width(t[k:i])
        if l1 > MAXC or l2 > MAXC: continue
        m = min(l1, l2)
        c = 1.0 + q + 0.15 * max(0.0, abs(l1 - l2) - 4) + (3.0 if m < 4 else 1.0 if m < 6 else 0.0)
        if any(ch in SENT for ch in t[j:k - 1]) or any(ch in SENT for ch in t[k:i - 1]): c += 6.0   # 行のまん中で文が終わる
        elif t[k - 1] in SENT: c += 1.2                             # 二つの文を 1 枚に（なるべく 1 文ずつ）
        if best is None or c < best[0]: best = (c, k)
    return best


def _card(t, j, i, Q):
    """1 枚の字幕 t[j:i] の悪さと改行の位置（1 行なら None）"""
    if width(t[j:i]) <= MAXC:
        return (0.5 if any(ch in SENT for ch in t[j:i - 1]) else 0.0), None
    return _two(t, j, i, Q)


def _cut(t, j, q):
    """j の所で次の字幕に替える悪さ"""
    a = t[j - 1]
    if a in SENT: return 0.8                                        # 文の終わり
    if a == "、": return 5.5 if t[j - 2] in "はも" else 4.0          # 文の途中（「…は、」の後はなるべく替えない）
    if a == "…": return 3.0
    return 6.0 + q


def plan(t):
    """字幕の枚数ぶんの文字列（改行入り）。文字の並びを動的計画法で区切る"""
    if t in OVERRIDES: return list(OVERRIDES[t])
    Q = _cands(t); n = len(t); INF = float("inf")
    dp = [INF] * (n + 1); back = [None] * (n + 1); dp[0] = 0.0
    starts = [0] + sorted(Q)
    for i in sorted(Q) + [n]:
        for j in starts:
            if j >= i or dp[j] == INF: continue
            r = _card(t, j, i, Q)
            if r is None: continue
            c = dp[j] + r[0] + (1.0 + _cut(t, j, Q[j]) if j > 0 else 0.0) + (3.0 if width(t[j:i]) < 6 else 0.0)
            if c < dp[i]: dp[i] = c; back[i] = (j, r[1])
    if dp[n] == INF: return [t]
    out = []; i = n
    while i > 0:
        j, k = back[i]
        out.append(t[j:i] if k is None else t[j:k] + "\\N" + t[k:i]); i = j
    return out[::-1]


parts = plan


# ---------------------------------------------------------------- 声の間（何枚かに分けた文を、息つぎの所で替える）
_PL = None


def _placement():
    global _PL
    if _PL is None:
        try: _PL = {p["text"]: p for p in json.load(open(os.path.join(VOICE, "placement.json"), encoding="utf-8"))}
        except Exception: _PL = {}
    return _PL


def gaps(wav, speed=1.0):
    """声のファイルの無音の所 → ([(始まり, 終わり), …], 声の長さ)（声の頭からの秒。速さで割った後の時間）"""
    import wave
    import numpy as np
    with wave.open(wav) as w:
        sr, ch = w.getframerate(), w.getnchannels(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    hop = int(0.01 * sr); n = len(x) // hop
    r = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    r = np.convolve(r, np.ones(3) / 3, mode="same"); db = 20 * np.log10(r + 1e-9)
    on = np.where(db > db.max() - 30)[0]
    if len(on) == 0: return [], len(x) / sr / speed
    sil = db < db.max() - 38
    runs = []; i = on[0]
    while i <= on[-1]:
        if sil[i]:
            j = i
            while j <= on[-1] and sil[j]: j += 1
            if j - i >= 7: runs.append((i * 0.01 / speed, j * 0.01 / speed))
            i = j
        else: i += 1
    return runs, len(x) / sr / speed


def _weights(p):
    s = p.replace("\\N", "")
    return width(s) + 1.5 * s.count("、") + 3.0 * sum(s.count(ch) for ch in SENT) + 1.0 * s.count("…")


def events(a, c, t, wav=None, speed=None):
    """（始まり, 終わり, 文）→ [(始まり, 終わり, 改行入りの文), …]。何枚かに分けるときは、声の間で替える
    wav：声のファイル（省くと placement.json から文で探す）。a は声の頭の時刻（字幕ファイルの始まりと同じ）"""
    ps = plan(t)
    if len(ps) == 1: return [(a, c, ps[0])]
    p = _placement().get(t)
    if wav is None and p is not None: wav = p.get("wav") or os.path.join(VOICE, "line_%03d.wav" % p["no"])
    sp = speed or (p["speed"] if p is not None else 1.0)
    runs, dur = [], max(c - a - 0.35, 0.5)
    if wav and os.path.exists(wav):
        try: runs, dur = gaps(wav, sp)
        except Exception: runs = []
    w = [_weights(x) for x in ps]; tot = sum(w); out = []; t0 = a
    for i in range(len(ps) - 1):
        est = a + dur * sum(w[:i + 1]) / tot
        lo, hi = t0 + 0.6, c - 0.6 * (len(ps) - 1 - i) - 0.4
        cand = [(abs((a + (g0 + g1) / 2) - est) - 0.6 * min(g1 - g0, 0.5), a + g0, a + g1) for g0, g1 in runs
                if lo <= a + g1 and a + g0 <= hi and abs((a + (g0 + g1) / 2) - est) < 1.2]
        if cand:
            _, g0, g1 = min(cand); t1 = max(g0 + 0.05, g1 - 0.15)            # 次の言葉の 0.15 秒前に替える
        else:
            t1 = est
        t1 = min(max(t1, lo), hi) if lo <= hi else est
        out.append((t0, t1, ps[i])); t0 = t1
    out.append((t0, c, ps[-1]))
    return out


def expand(lines, alt=None):
    """[(始まり, 終わり, 文), …] → 字幕 1 枚ずつの [(始まり, 終わり, 改行入りの文), …]。alt：{文: 声のファイル}（差し替えた声）"""
    out = []
    for a, c, t in lines:
        out += events(a, c, t, wav=(alt or {}).get(t))
    return out


if __name__ == "__main__":
    import sys
    PL = json.load(open(sys.argv[1], encoding="utf-8"))
    extra = [dict(no=67.5, text="もし、隣のイヤホンが見えた二つを混ぜても……青と赤は入りますが、白が二回分入るので、薄い紫にしかなりません。",
                  start=0.0, end=10.77, wav=os.path.join(VOICE, "line_067_b.wav"))]   # 第4章 6:24 の②
    for p in sorted(PL + extra, key=lambda p: p["no"]):
        ps = plan(p["text"])
        line = "%5s %2d| %s" % (p["no"], len(p["text"]), "  ／  ".join(x.replace("\\N", " ⏎ ") for x in ps))
        if "--times" in sys.argv and len(ps) > 1:
            ev = events(p["start"], p["end"] + 0.35, p["text"], wav=p.get("wav"))
            line += "\n        " + "  ".join("[%.2f→%.2f]" % (e[0] - p["start"], e[1] - p["start"]) for e in ev)
            wv = p.get("wav") or os.path.join(VOICE, "line_%03d.wav" % p["no"])
            g, d = gaps(wv, p.get("speed", 1.0))
            line += "  間: " + " ".join("%.2f-%.2f" % x for x in g) + "  声 %.2f" % d
        print(line)
