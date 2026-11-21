# 3本目 v12：2 行の字幕（make_subs_v.py の結果）を、関所の決まり（1 枚 2 秒以上・1 秒 8 字まで・1 行 25 字まで・2 行まで）に合わせる
#   2026-11-20：v11 で 1 行ずつにしたら「テロップの切り替わりが早い／遅い」が約 30 件。ほかの回の決まり（6本目 v10 ユーザー「2 行のまま・道具を決まりに合わせる」）に合わせ、
#   2 行の字幕（v10 まで直してきた切り替えの時刻）に戻し、決まりの外の 1 枚だけを直す
#   ①1 行が 25 字をこえる 1 枚は、読点で 2 行に分け直す（RELINE） ②短い・速い 1 枚は、共通の subs_balance でとなりと声のない間から時間を借りる
#   ③時刻は 1/100 秒に切り捨て（2.02 秒・7.9 字/秒のゆとり。四捨五入だと 2.00 が 1.99 になる）
#   MARU_WORK=… MARU_VOICE=… python3 make_subs_v.py && python3 fix_subs_gate.py
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "skill", "marurobo-video-production", "scripts"))
import subs_balance as SB
P = os.path.join(HERE, "subs_events.json")
L = [list(x) for x in json.load(open(P, encoding="utf-8"))]
RELINE = {"このように、同じWi-Fiにいた人が調べた物の広告が、\\N出てくることもあるのです。": "このように、同じWi-Fiにいた人が\\N調べた物の広告が、出てくることもあるのです。"}
rows = lambda t: t.replace("\\N", "\n").split("\n")
n_ = lambda t: len("".join(rows(t)).replace(" ", ""))
for x in L:
    x[2] = RELINE.get(x[2], x[2]).replace("\n", "\\N")
    if x[2] == "うふふ。": x[2] = "ふふっ。"                                 # v12：字幕ごとの聞き取りで、声の笑いは 3 回とも「ふふっ」と聞こえた。字幕を聞こえるとおりに（台本の文はそのまま）
    if max(len(r) for r in rows(x[2])) > 25: print("1 行 25 字こえ（RELINE に足す）：", x[2])
# （言葉の時刻の表にそろえる手は使わない：表は文の中の言葉を字数で当てはめた見積もりで、ためる所で 1 秒以上外れた。05-05・06-04・17-00 を波形で確かめた）
# 声が速くて、決まりに入らない 2 か所は、波形で確かめた時刻で手で分ける（ためた答えを先に見せない・ずれは 0.6 秒以内）
def setcards(t0, t1, cards):
    global L
    L = [x for x in L if not (t0 - 0.01 <= x[0] < t1 - 0.01)] + [list(c) for c in cards]
    L.sort()
for x in L:                                                               # 12-05b のあとの 1 枚の頭（514.71）を 0.28 秒遅らせて、ためた答えに 2 秒をつくる
    if abs(x[0] - 514.71) < 0.02: x[0] = 514.99
setcards(508.1, 514.7, [(508.18, 510.95, "「ニュースを読んでいる、この人。"), (510.95, 512.97, "手がかりを見ると……"), (512.97, 514.99, "うちのテントが合いそうだ！」")])
for x in L:                                                               # 21-03 の頭を 0.39 秒遅らせ、21-02 の 2 枚目を 0.57 秒早く出す（31 字を 3.9 秒で）
    if abs(x[0] - 891.12) < 0.02: x[0] = 891.12
setcards(884.2, 891.1, [(884.25, 886.02, "ピポ、ピポ……。"), (886.07, 891.07, "テントの絵を浮かべて、\\N「テント」と言っているつもりみたいです。")])   # v12：字幕ごとの聞き取りで、「テントの絵」の頭は 886.07（885.04〜886.07 の間のあと）と分かった。887.65〜888.3 は「浮かべて」のあとの間だった
# 19-08b：「手が／かり」と言葉の途中で行が切れていた（v11 842.5）。声の間（844.73-844.99）で 2 枚に分ける
setcards(840.0, 847.0, [(840.09, 844.94, "スマホから出ていく、\\Nいた場所や一緒にいた人の手がかりから、"), (844.99, 847.0, "好きそうな物を予想している。")])
L = [list(x) for x in SB.balance([tuple(x) for x in L], MIN=2.02, CPS=7.9)]
# ためた答えの短い 1 枚（2 秒にするために、声より 0.5 秒ほど先に出ていた）は、声の 0.35 秒前まで遅らせ、次の 1 枚を押す（答えを先に見せない）
#   時刻は、その言葉の頭（声の間の終わり）を波形で確かめた物。sub_sync_check.py で確かめる
#   （先に出す長さ）は、次の 1 枚が決まりに入り、次の 1 枚の遅れが 0.35 秒ほどで済む長さ。「テント。」「その先には……」「結果は……」は次の文まで間がなく、動かすと次が 0.8 秒遅れるので、そのまま
TAME = {"ふふっ。": (68.89, 0.35), "……一瞬！": (529.21, 0.5), "正解は……。": (662.65, 0.35), "と、思ったそのとき。": (745.4, 0.3)}
for i, x in enumerate(L):
    if x[2] not in TAME: continue
    v, lead = TAME[x[2]]
    if x[0] >= v - lead: continue
    d = (v - lead) - x[0]; x[0] += d; x[1] += d
    nx = L[i + 1]
    if nx[0] < x[1] + 0.05:
        nx[0] = x[1] + 0.05
        lim = (L[i + 2][0] - 0.05) if i + 2 < len(L) else nx[1] + 1
        nx[1] = max(nx[1], min(lim, nx[0] + max(2.02, n_(nx[2]) / 7.9)))
for i, x in enumerate(L):                                                  # 前の 1 枚が、遅らせた頭と重ならないように
    if i and L[i - 1][1] > x[0] - 0.05 and x[2] in TAME: L[i - 1][1] = x[0] - 0.05
fl = lambda v: math.floor(v * 100 + 1e-6) / 100
for x in L: x[0], x[1] = fl(x[0]), fl(x[1])
bad = [(x[0], round(x[1] - x[0], 2), x[2]) for x in L if x[1] - x[0] < 2.0 or n_(x[2]) / (x[1] - x[0]) > 8.0 or max(len(r) for r in rows(x[2])) > 25 or len(rows(x[2])) > 2]
ov = [(a[0], a[2]) for a, b in zip(L, L[1:]) if b[0] < a[1] - 1e-6]
sys.path.insert(0, os.path.join(HERE, "..", "voice"))
from gaps import G                                                       # v12：声と声のあいだに足した間（ここまでは v11 の時刻で作る）
L = [[fl(G(x[0]) + 1e-6), fl(G(x[1]) + 1e-6), x[2]] for x in L]
# 間を足した所では、前の 1 枚に押されて遅れていた文の頭を、声の頭へ戻せる（前の 1 枚が 2 秒・7.9 字/秒のまま残るときだけ）
_P12 = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
for i, x in enumerate(L[1:], 1):
    st = min((p["start"] for p in _P12), key=lambda v: abs(v - x[0]))
    pv = L[i - 1]
    if 0.1 < x[0] - st < 0.8 and (st - 0.05) - pv[0] >= max(2.02, n_(pv[2]) / 7.9):
        x[0] = fl(st); pv[1] = fl(st - 0.05)
# 足した間の前の 1 枚は、声の終わりの 0.6 秒あとで消す（「入ってみましょう」が中の町に着いたあとまで残っていた。v12 の自分の点検）
#   ただし、泡が飛ぶ間（「テント。」「ヘイ、テント！」）は、何の泡かを示すので残す
for x in L:
    if x[2].endswith(("入ってみましょう。", "目をはなさないで。")):
        ve = min((p["end"] for p in _P12), key=lambda v: abs(v - x[1]))
        x[1] = max(fl(x[0] + 2.02), min(x[1], fl(ve + 0.6)))
# ための短い 1 枚（2026-11-21 ユーザーの選択「ためだけ 2 秒未満を許す」）：声の頭と同時に出し、次の言葉の頭で替える（1 秒以上）。
#   時刻は声の波形で求める（1 文ずつの声の無音 0.15 秒以上の終わり＝言葉の頭）。関所は ../字幕_ため.json の字幕だけ 1 秒以上でよい
TAMES = ["ふふっ。", "鏡？", "ピポ、ピポ……。", "テント。", "結果は……", "その先には……", "……一瞬！", "正解は……。", "すると……", "次の朝。"]
json.dump(TAMES, open(os.path.join(HERE, "..", "字幕_ため.json"), "w", encoding="utf-8"), ensure_ascii=False)
import wave
import numpy as np
VD = os.environ.get("MARU_VOICE")
def _heads(p):                                                           # その文の言葉の頭（文の頭と、無音のあとの頭）
    with wave.open(os.path.join(VD, "line_%03d.wav" % p["no"])) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
    h = sr // 100; n = len(x) // h; db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9); on = db > db.max() - 38
    out, i = [p["start"]], 0
    while i < n:
        if not on[i]:
            j = i
            while j < n and not on[j]: j += 1
            if j - i >= 15 and i > 0 and j < n: out.append(p["start"] + j / 100)
            i = j
        else: i += 1
    return out
if VD:
    HD = sorted(v for p in _P12 for v in _heads(p))
    for i, x in enumerate(L):
        if x[2] not in TAMES: continue
        v = min(HD, key=lambda h: abs(h - x[0]))                          # ための言葉の頭
        nx = min([h for h in HD if h > v + 0.9] or [x[1]])                # 次の言葉の頭（ための言葉の中の短い息は数えない）
        a_, b_ = fl(v - 0.05), fl(nx - 0.05)
        if b_ - a_ < 1.0: print("ための 1 枚が 1 秒に足りない：", x); continue
        x[0], x[1] = a_, b_
        if i > 0: L[i - 1][1] = min(L[i - 1][1], fl(a_ - 0.05))
        if i + 1 < len(L):
            nn = L[i + 2][0] if i + 2 < len(L) else 1e9; need = max(2.02, n_(L[i + 1][2]) / 7.9)
            st = min(fl(nx), fl(nn - 0.05 - need))                         # 次の 1 枚が決まりの長さを取れるように（取れなければ、その分だけ早く替える）
            st = max(st, fl(a_ + 1.05)); x[1] = fl(st - 0.05)
            L[i + 1][0] = st; L[i + 1][1] = max(L[i + 1][1], min(fl(nn - 0.05), fl(st + need)))
    for i, x in enumerate(L[:-1]):                                          # 押した次の 1 枚が、その次と重ならないように（重なるなら次の頭までにする）
        if x[1] > L[i + 1][0]: x[1] = L[i + 1][0]
else: print("MARU_VOICE がないので、ための 1 枚は直していない")
bad = [(x[0], round(x[1] - x[0], 2), x[2]) for x in L if x[1] - x[0] < (1.0 if x[2] in TAMES else 2.0) or n_(x[2]) / (x[1] - x[0]) > 8.0 or max(len(r) for r in rows(x[2])) > 25 or len(rows(x[2])) > 2]
ov = [(a[0], a[2]) for a, b in zip(L, L[1:]) if b[0] < a[1] - 1e-6]
json.dump(L, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("字幕 %d 枚・決まりの外 %d 枚・重なり %d" % (len(L), len(bad), len(ov)))
for b in bad: print("  ", b)
