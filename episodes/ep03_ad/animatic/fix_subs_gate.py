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
    if abs(x[0] - 891.12) < 0.02: x[0] = 891.65
setcards(884.2, 891.1, [(884.25, 887.8, "ピポ、ピポ……。"), (887.8, 891.6, "テントの絵を浮かべて\\N「テント」と言っているつもりみたいです。")])
# 19-08b：「手が／かり」と言葉の途中で行が切れていた（v11 842.5）。声の間（844.73-844.99）で 2 枚に分ける
setcards(840.0, 847.0, [(840.09, 844.94, "スマホから出ていく、\\Nいた場所や一緒にいた人の手がかりから、"), (844.99, 847.0, "好きそうな物を予想している。")])
L = [list(x) for x in SB.balance([tuple(x) for x in L], MIN=2.02, CPS=7.9)]
# ためた答えの短い 1 枚（2 秒にするために、声より 0.5 秒ほど先に出ていた）は、声の 0.35 秒前まで遅らせ、次の 1 枚を押す（答えを先に見せない）
#   時刻は、その言葉の頭（声の間の終わり）を波形で確かめた物。sub_sync_check.py で確かめる
#   （先に出す長さ）は、次の 1 枚が決まりに入り、次の 1 枚の遅れが 0.35 秒ほどで済む長さ。「テント。」「その先には……」「結果は……」は次の文まで間がなく、動かすと次が 0.8 秒遅れるので、そのまま
TAME = {"うふふ。": (68.89, 0.35), "……一瞬！": (529.21, 0.5), "正解は……。": (662.65, 0.35), "と、思ったそのとき。": (745.4, 0.3)}
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
json.dump(L, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("字幕 %d 枚・決まりの外 %d 枚・重なり %d" % (len(L), len(bad), len(ov)))
for b in bad: print("  ", b)
