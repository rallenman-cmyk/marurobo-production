# 図の場面（3D）の札と効果音。compose3d.py が読む
#   札：text・at（TRACK の名前か 1280×720 の場所）・d（ずれ）・t（出る時刻）・out（消える時刻）・col（te/or/nv/rd/gr）
#       solid＝色を塗った札（白い字）・plain＝印の点なし・tail＝しっぽ・size・quiet＝pop_ui を鳴らさない
#   効果音：(時刻, 種類, 大きさ)。絵の動き 1 つに 1 つ、動きに合う種類（SKILL.md）
#   出る時刻は字幕の切り替わり（said）にそろえる
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
EV = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))


def said(text, after=0.0):
    for a, c, t in EV:
        if a >= after - 1e-6 and t.replace("\\N", "").startswith(text): return a
    raise KeyError(text)


def P(text, at, t, **kw):
    d = dict(text=text, at=at, t=t); d.update(kw); return d


# ---------------- S10 人とプログラムの比べっこ（3:33〜4:10）
def s10_labels():
    t_y, t_who, t_res, t_fast, t_hum, t_hsec = (said("2023年には"), said("ゆがんだ文字のテストを"), said("結果は"),
                                               said("しかも、1問"), said("人は、正解"), said("1問に、9秒"))
    return [P("2023年", (640, 62), t_y, size=50, col="or"),
            P("人", "L_top", t_who, d=(0, -70), solid=True, col="or", size=46, tail=(0, 55)),
            P("プログラム", "R_top", t_who + 0.4, d=(0, -70), solid=True, col="te", size=46, tail=(0, 55)),
            P("ほぼ全部", "R_tube", t_res + 2.2, size=40, d=(40, 0)),
            P("1秒未満", "R_clock", t_fast, d=(0, -78), size=40),
            P("5〜8割", "L_tube", t_hum + 2.0, size=40, col="or"),
            P("9〜15秒", "L_clock", t_hsec, d=(0, -78), size=40, col="or")]


def s10_sfx():
    t_who, t_res, t_fast, t_hum, t_hsec, t_wow = (said("ゆがんだ文字のテストを"), said("結果は"), said("しかも、1問"),
                                                 said("人は、正解"), said("1問に、9秒"), said("なんと"))
    e = [(t_who - 0.1, "pop", 0.6), (t_who + 0.3, "pop", 0.6)]
    e += [(t_res + 0.2 + j * 0.3, "pi", 0.18) for j in range(5)]
    e += [(t_res + 1.3, "rise", 0.5), (t_fast + 0.2, "whoosh", 0.35)]
    e += [(t_hum + 0.3, "rise", 0.4), (t_hum + 1.5, "rise", 0.35)]
    e += [(t_hsec + 0.2 + j * 0.33, "click", 0.25) for j in range(8)]
    e += [(t_wow + 0.1, "jump", 0.8), (t_wow + 0.55, "land", 0.8)]
    return e


def nxt(text):
    a = said(text); return min(e[0] for e in EV if e[0] > a + 0.01)


# ---------------- S06 押したボタンは同じ（1:28〜1:40）
def s06_labels():
    T0, t_q, t_next = said("押したボタンは"), said("いったい、どこで"), said("その答えに")
    return [P("まるロボ", "L_top", T0 + 0.6, d=(0, -40), solid=True, col="te", tail=(0, 50), quiet=True),
            P("私", "R_top", T0 + 0.9, d=(0, -40), solid=True, col="or", tail=(0, 50), quiet=True),
            P("？", "maru", t_q + 0.2, d=(70, -80), solid=True, col="or", size=52, out=t_next)]


def s06_sfx(): return []   # 3D の log の音を使う（use_log）


# ---------------- S07〜S08 昔のテスト（1:52〜2:36）
def s07_labels():
    t_who, t_two, t_known, t_unk, t_other = said("人には読める"), said("実は、このゆがんだ"), said("1つは、出題"), said("実は、出題する側も"), said("では、もう1つは")
    return [P("人", "L_base", t_who - 0.1, d=(0, 30), solid=True, col="or", quiet=True, out=t_two - 0.1),
            P("機械", "R_base", t_who + 0.3, d=(0, 30), solid=True, col="te", quiet=True, out=t_two - 0.1),
            P("morning", "L_top", t_who + 0.9, d=(0, -85), plain=True, size=46, tail=(0, 55), quiet=True, out=t_two - 0.1),
            P("？？？", "R_top", t_who + 2.7, d=(0, -75), plain=True, size=44, tail=(0, 50), quiet=True, out=t_two - 0.1),
            P("出題する側", "asker", t_known - 0.1, d=(-170, 0), solid=True, col="nv", size=40, quiet=True),
            P("morning", "wL", t_known + 1.6, d=(0, -70), plain=True, size=46, tail=(0, 50)),
            P("？？？", "wR", t_unk + 0.4, d=(0, -70), solid=True, col="or", size=44, tail=(0, 50))]


# ---------------- S08g〜h たくさんの人に読んでもらう（2:43〜2:55）
def s08x_labels():
    t_ok = said("何人もの人が") + 3.4
    return [P("upon", "board", t_ok + 0.1, d=(0, 0), solid=True, col="gr", size=70, quiet=True)]


# ---------------- S09 2014年 Google 99.8%（3:09〜3:33）
def s09_labels():
    t_g, t_998 = said("2014年、このテスト"), said("今のAIは")
    return [P("2014年", (500, 62), t_g, size=50, col="or"),
            P("Google", (720, 62), t_g + 2.0, size=50, col="nv"),
            P("99.8%", "tube_top", t_998 + 2.6, d=(0, -40), solid=True, col="te", size=60, quiet=True)]


# ---------------- S15 これまでの記録（5:59〜6:15）
def s15_labels():
    T0, t_rep = said("たとえば、ふだんから"), said("反対に、短い間に")
    L = [P("これまでの記録", "top", T0, d=(0, -10), size=46, col="nv", quiet=True)]
    for k, w in enumerate(("ニュース", "買い物", "動画")):
        L.append(P(w, "t%d" % k, T0 + 1.2 + k * 1.4, d=(0, 10), plain=True, size=38, quiet=True, out=t_rep - 0.1))
    L.append(P("同じことを何百回も", "bottom", t_rep + 2.0, d=(0, 10), solid=True, col="rd", size=44))
    return L


# ---------------- S19 GPT-4 は人に頼んだ（7:46〜8:47）
def s19_labels():
    t_y, t_ask, t_q, t_no, t_res = said("2023年。"), said("そこで、ネットで"), said("「あなた、ロボット"), said("「いいえ、私は"), said("ただしこれは")
    return [P("2023年  OpenAI「GPT-4」", (640, 62), t_y, size=46, col="or"),
            P("GPT-4", "A_base", said("OpenAIが") + 0.6, d=(0, 30), solid=True, col="te"),
            P("頼まれた人", "P_base", t_ask + 0.5, d=(0, 30), solid=True, col="or", quiet=True),
            P("？", "P_top", t_q, d=(60, -80), solid=True, col="or", size=52, tail=(-30, 50)),
            P("「私はロボットではありません」", "A_side", t_no + 0.1, d=(250, -150), plain=True, size=40, tail=(-180, 110)),
            P("研究者が手伝った試験", "R_base", t_res + 1.0, d=(60, 40), solid=True, col="nv", size=38, quiet=True)]


# ---------------- S20 2024年・2025年（8:47〜9:30）
def s20_labels():
    T0, t_25, t_op, t_chk = said("2024年には"), said("そして2025年"), said("ChatGPTに、自分で"), said("途中で、人間かどうか")
    return [P("2024年", (640, 62), T0, size=50, col="or", out=t_25 - 0.1),
            P("2025年", (640, 62), t_25 + 0.3, size=50, col="or"),
            P("ChatGPT", "A_base", t_op + 0.4, d=(0, 30), solid=True, col="te"),
            P("人間かどうかを確かめます", "box", t_chk + 0.4, d=(140, 110), plain=True, size=36, tail=(-120, -70))]


# ---------------- S22 昔と今・AI は賢く・残り少ない（10:10〜10:28）
def s22_labels():
    T0, t_ai, t_few = said("昔は、文字を"), said("そして今、AIは"), said("人と機械の違いを")
    t_now = T0 + 2.4
    L = [P("昔：文字を読めるか", "O_top", T0 + 0.1, d=(0, -50), size=40, col="nv", quiet=True, out=t_ai - 0.1),
         P("今：ふるまい", "N_top", t_now, d=(0, -40), size=40, col="te", quiet=True, out=t_ai - 0.1),
         P("AI は ますます賢く", "A_top", t_ai + 0.4, d=(0, -40), size=44, col="or", out=t_few - 0.1)]
    for k, w in enumerate(("ゆがんだ文字", "絵のテスト", "ふるまい")):
        L.append(P(w, "T%d" % k, t_few + 0.3 + k * 0.45, d=(0, 20), size=36, plain=True, quiet=True))
    L.append(P("？", "Q2", t_few + 3.6, d=(0, -20), solid=True, col="or", size=54, quiet=True))
    L.append(P("見分ける方法", (640, 62), t_few + 0.1, size=44, col="nv", quiet=True))
    return L


def none(): return []


SCENES = {"s10": dict(labels=s10_labels, sfx=s10_sfx),
          "s06": dict(labels=s06_labels, sfx=none, use_log=True),
          "s07": dict(labels=s07_labels, sfx=none, use_log=True),
          "s08x": dict(labels=s08x_labels, sfx=none, use_log=True),
          "s09": dict(labels=s09_labels, sfx=none, use_log=True),
          "s15": dict(labels=s15_labels, sfx=none, use_log=True),
          "s19": dict(labels=s19_labels, sfx=none, use_log=True),
          "s20": dict(labels=s20_labels, sfx=none, use_log=True),
          "s22": dict(labels=s22_labels, sfx=none, use_log=True)}
