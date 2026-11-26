# 16本目 2章：絵・札・音を言葉に合わせる時刻を、声の波形から取って word_times_ch2.json に書く
#   確認役（§2.6）の指摘「管理する人の ID の札が声より 0.6 秒早い」から作った。w()（文の字数の割合で見積もる）は、
#   句読点の間の長さを知らないので、文の後ろのほうの言葉ほど早くなる。
#   ここでは、文の句読点ごとの声の間（voice/pauses.cut_all）で文を区切り、言葉の入っている区切りの中だけで字数の割合を取る。
#   区切りの頭の言葉は、その区切りの声の頭（0.00 秒のずれ）。
#   MARU_WORK=<作業> python3 make_word_times.py   （scenes_ch2.py・overlays2.py の w("..", "..") と wv(..) を全部拾う）
import os, re, sys, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "voice"))
import numpy as np
import pauses as PZ
import subs_mora as SM
VD = os.path.join(os.environ["MARU_WORK"], "stage", "voice", "achernar")
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
SC = {x["no"]: x for x in json.load(open(os.path.join(HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
IDX = {SC[p["no"]]["id"]: k for k, p in enumerate(P)}
OUT = os.path.join(HERE, "word_times_ch2.json")
old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
KEEP = {k: v for k, v in old.items() if k == "_" or k.split("|")[1] in ("ガチャン",)}     # 「ガチャン」は声の区間を目で確かめて手で書いた
# 声の区切りの道具（pauses.cut_all）が、長い間（0.66 秒）ではなく短い息（0.11 秒）を「、」に当てた文は、波形を見て手で書く（文の頭からの秒）。
#   16本目 5章 v15 のユーザー「音声と光るところのタイミングがあってない」：26-05 の「電話・誕生日・勤め先」が 0.5〜1.1 秒早かった
MANUAL = {"28-02": {"ガチャ|1": 0.96},      # 2 つ目の「ガチャ」：同じ言葉の 2 つ目を、道具が 1 つ目と同じ時刻にしていた（6章を作るとき）
          "26-05": {"名前": 0.02, "住所": 1.05, "電話": 1.90, "誕生日": 3.00, "勤め先": 3.84, "買った物": 5.06}}


def seg_times(k):
    """文 k の声の区切り：[(tts の始め, tts の終わり, 声の始め秒, 声の終わり秒)]（文の頭からの秒ではなく、本編の秒）"""
    p = P[k]; tts = SM._clean(SC[p["no"]]["tts"]); wav = os.path.join(VD, "line_%03d.wav" % p["no"])
    v, hop = PZ.env(wav); idx = np.where(v)[0]
    on, off = (idx[0] * hop, (idx[-1] + 1) * hop) if len(idx) else (0.0, len(v) * hop)
    sp = p.get("speed", 1.0)
    cuts = [(pos, r) for pos, ch, r in PZ.cut_all(wav, tts) if r is not None]
    segs = []; a_pos, a_t = 0, on
    for pos, r in cuts:
        segs.append((a_pos, pos, p["start"] + a_t * sp, p["start"] + r[0] * sp)); a_pos, a_t = pos, r[1]
    segs.append((a_pos, len(tts), p["start"] + a_t * sp, p["start"] + off * sp))
    return segs, tts


def word_time(i, word, occ=0):
    k = IDX[i]; p = P[k]; text = SM._clean(p["text"])
    pos = -1
    for _ in range(occ + 1): pos = text.index(word, pos + 1)
    segs, tts = seg_times(k)
    to = SM._tts_off(text, tts, pos) if pos > 0 else 0
    if to is None: to = int(pos * len(tts) / max(1, len(text)))
    for a, b, ta, tb in segs:
        if a <= to < b or (to >= b and (a, b, ta, tb) == segs[-1]):
            body = re.sub(r"[、。？！…「」　 ]", "", tts[a:b]); pre = re.sub(r"[、。？！…「」　 ]", "", tts[a:to])
            return round(ta + (tb - ta) * len(pre) / max(1, len(body)), 3)
    return None


if __name__ == "__main__":
    src = "".join(open(os.path.join(HERE, f), encoding="utf-8").read() for f in sorted(os.listdir(HERE)) if re.match(r"(scenes_ch|overlays)[0-9]+\.py$", f))      # 章のファイルを全部（16本目 7章：名前を並べて書いていて、新しい章が抜けた）
    calls = set(re.findall(r'\bwv?\("(\d\d-\d\d)", "([^"]+)"(?:, (\d))?\)', src))
    out = dict(KEEP)
    for i, word, occ in sorted(calls):
        key = "%s|%s|%d" % (i, word, int(occ or 0))
        if key in out: continue
        mk = word if int(occ or 0) == 0 else "%s|%d" % (word, int(occ))
        t = round(P[IDX[i]]["start"] + MANUAL[i][mk], 3) if mk in MANUAL.get(i, {}) else word_time(i, word, int(occ or 0))
        if t is not None: out[key] = t
    out["_"] = "2章の絵・札・音を合わせる言葉の時刻（声の区切りごとの字数の割合。make_word_times.py が作る。ガチャンは声の区間を見て手で書いた）"
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import timing as T
    big = [(k, v, round(v - T.w(k.split("|")[0], k.split("|")[1]), 2)) for k, v in out.items() if k != "_" and abs(v - T.w(k.split("|")[0], k.split("|")[1])) > 0.3]
    print(len(out) - 1, "語。見積もり（w）と 0.3 秒より違う：", big)
