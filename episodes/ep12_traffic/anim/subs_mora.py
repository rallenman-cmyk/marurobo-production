# 16本目 v1 のコメント「テロップの切り替わりが早い」2 件（06-04・10-08）から作った、字幕の切り替わりを「言葉」で合わせる道具
#   それまでの道具（subs_sync）は「切り替わる時刻が声の切れ目にあるか」だけを見ていて、「どの言葉の前の切れ目か」は見ていなかった。
#   06-04 は「お城に、」のあとの切れ目で、字幕は「泥棒は、」のあとで切っていた（「どうやって」の字が声より 0.6 秒早く出た）。
#   ここでは、字幕 1 枚ずつ、その最初の文字が文のどの区切り（、。？！……）のあとかを調べ、voice/pauses.cut_all でその区切りの
#   声の切れ目を探し、「声が言い始める 0.05 秒前」に字幕を替える。区切りに切れ目がない（続けて読んでいる）所では、字幕は分けない（前とまとめる）。
#   fix(SUBS, P, S, VD) → 直した SUBS と、動かした一覧。check(...) → 声の言い始めから 0.25 秒より離れた字幕の一覧（関所の点検に使う）
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "voice"))
import pauses as PZ

LEAD = 0.05
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
import subs_pause_align as PA
P_TEXT = {}


def _raw_from(raw, off):
    """空白・改行を除いた off 文字目から始まる、元の文の残り"""
    k = 0
    for i, ch in enumerate(raw):
        if re.match(r"[\s　]", ch): continue
        if k == off: return raw[i:]
        k += 1
    return ""


def _clean(s): return re.sub(r"[\s　]|\\N", "", s)


def _locate(SUBS, P):
    """字幕ごとに、その最初の文字が、どの文（P の何番目）の何文字目か"""
    stream = []
    for i, p in enumerate(P):
        t = _clean(p["text"])
        for j, ch in enumerate(t): stream.append((i, j, ch))
    k = 0; out = []
    for a, c, txt in SUBS:
        t = _clean(txt)
        # 字幕の文字を、流れの中で順に探す（字幕の頭の「……」など、文の頭と合わない記号は飛ばしてよい）
        st = None
        while k < len(stream) and stream[k][2] != t[0]: k += 1
        if k < len(stream): st = stream[k][:2]
        out.append(st); k += len(t)
    return out


def _tts_off(text, tts, off):
    """text の off 文字目を、tts の何文字目かに直す（区切りのあとの数文字で探す）"""
    if off == 0: return 0
    snip = text[off:off + 3]
    for L in (3, 2, 1):
        i = tts.find(snip[:L], max(0, int(off * len(tts) / max(1, len(text))) - 12))
        if i >= 0: return i
    return None


def boundary(P, S, VD, i, off):
    """文 i の off 文字目で始まる字幕の、声が言い始める時刻（秒）。区切りに切れ目がなければ None"""
    p = P[i]; text = _clean(p["text"]); tts = _clean(S[p["no"]]["tts"])
    wav = os.path.join(VD, "line_%03d.wav" % p["no"])
    if off == 0:
        v, hop = PZ.env(wav); import numpy as np
        idx = np.where(v)[0]; return p["start"] + (idx[0] * hop if len(idx) else 0.0)
    # 17本目 v1：関所の道具（subs_sync_check）と同じ「声の本当の間に句読点を 1 対 1 で当てる」やり方（subs_pause_align）を先に使う。
    #   pauses.cut_all は 14-02「たまたま、｜ほかの人の」で「たま｜たま」の間を選び、字幕が 0.39 秒早かった（聞き取りで確かめた）
    tg = PA.target(p, _raw_from(p["text"], off).lstrip("…"), wav)   # 字幕の頭の「……」は、前の句読点（「。……」）の一部
    if tg is not None: return tg + LEAD
    to = _tts_off(text, tts, off)
    if to is None: return None
    for pos, ch, r in PZ.cut_all(wav, tts):
        if pos == to or (pos < to and tts[pos:to].strip("　 「」") == ""):
            return None if r is None else p["start"] + r[1] * p.get("speed", 1.0)
    return None


def fix(SUBS, P, S, VD):
    SUBS = sorted(SUBS); loc = _locate(SUBS, P); out = []; moved = []; merged = []
    for (a, c, txt), L in zip(SUBS, loc):
        if L is None: out.append([a, c, txt]); continue
        i, off = L
        t = boundary(P, S, VD, i, off)
        if t is None and off > 0 and out:                 # 続けて読んでいる所：前の字幕にまとめる
            pa, pc, pt = out[-1]
            nt = pt + "\\N" + txt if len(_clean(pt)) + len(_clean(txt)) > 25 else pt + txt
            if nt.count("\\N") <= 1 and all(len(x) <= 25 for x in nt.split("\\N")):
                out[-1] = [pa, c, nt]; merged.append((round(a, 2), txt)); continue
        if t is not None:
            na = round(t - LEAD, 2)
            # 17本目 v1：「……」で始まる字幕を声の前のためから（0.8 秒まで早く）出していたが、関所（声の頭から 0.2 秒以内）で「声のない所で切り替わる」になった。
            #   ためは前の字幕を残して見せる → 声の頭で替える（ほかの字幕と同じ）
            if abs(na - a) > 0.05: moved.append((round(a, 2), na, txt))
            if out and out[-1][1] > na - 0.05: out[-1][1] = round(na - 0.05, 2)
            if out and out[-1][1] < na - 0.05 and out[-1][1] > a - 0.06: out[-1][1] = round(na - 0.05, 2)   # 前の字幕は次の字幕まで出す
            if out is not None and c < na + 0.3: c = na + 0.3
            a = na
        out.append([a, c, txt])
    return [tuple(x) for x in out], moved, merged


def check(SUBS, P, S, VD, tol=0.25):
    SUBS = sorted(SUBS); loc = _locate(SUBS, P); bad = []
    for (a, c, txt), L in zip(SUBS, loc):
        if L is None: continue
        t = boundary(P, S, VD, *L)
        if t is None:
            if L[1] > 0: bad.append((round(a, 2), None, txt, "区切りに声の切れ目がない（続けて読んでいる所で分けている）"))
            continue
        if abs(a + LEAD - t) > tol: bad.append((round(a, 2), round(t, 2), txt, "%+.2f 秒" % (a + LEAD - t)))
    return bad
