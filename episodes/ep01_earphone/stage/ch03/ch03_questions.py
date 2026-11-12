# 第3章の終わり（台本 v2 の 33・34：本編 166.2〜175.786 秒）：「二つの疑問」の画
#   ①「どうして隣の人の曲が混ざらないのか」：自分の組（○・青緑）と隣の組（△・橙）。電波は両方のイヤホンに届いている（点線）
#   ②「どうしてときどき音が途切れるのか」：スマホ → イヤホンへ流れる音の波が、途中で切れる
#   ナレーションに合わせて ① → ② の順に出し、最後は ① を強く（第4章の「まずは、一つ目の疑問から」へ）
#   絵の部品は第4章の図（ch04_diagram.py）と同じもの（スマホ・イヤホン・○△の印・色）
# 使い方: python3 ch03_questions.py OUT_DIR → OUT_DIR/questions/q_0001.png …（1280×720・24fps）
import sys, os, json, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ch04_diagram as dg

W, H, FPS = 1280, 720, 24
T_A, T_B = 166.2, 175.786                       # この画の始まりと終わり（本編）。終わり＝第4章の始まり
TXT = None
for e in json.load(open(os.path.join(HERE, "..", "script", "script_v2_timed.json"), encoding="utf-8")):
    if e["text"].startswith("一つ目は、どうして隣の人の曲"): TXT = e
assert TXT, "台本 v2 の 34 が見つからない"


def at_char(n): return TXT["start"] + (TXT["end"] - TXT["start"]) * n / len(TXT["text"])


T_Q1 = at_char(0) + 0.15                        # 「一つ目は、」
T_Q2 = at_char(TXT["text"].index("そして")) + 0.05   # 「そして二つ目は、」
T_FOCUS = T_B - 0.55                            # 最後に ① を強く
S = dg.S


def panel(p, box, a, hi):
    x0, y0, x1, y1 = box
    p.rr((x0, y0, x1, y1), 22, fill=dg.mix((244, 247, 249), a), outline=dg.mix((200, 206, 212) if hi < 0.5 else dg.TEAL, a), width=2 + 2 * hi)   # 白いイヤホンが見えるように、板は少しだけ色をつける


def badge(p, c, n, col, a):
    p.ell((c[0] - 24, c[1] - 24, c[0] + 24, c[1] + 24), fill=dg.mix(col, a)); p.text(c, n, 30, dg.mix(dg.WHITE, a))


def note(p, c, col, a, sc=1.0):
    """音符（♪）"""
    x, y = c
    p.ell((x - 9 * sc, y + 6 * sc, x + 5 * sc, y + 17 * sc), fill=dg.mix(col, a))
    p.line([(x + 4 * sc, y + 11 * sc), (x + 4 * sc, y - 16 * sc)], dg.mix(col, a), 3 * sc)
    p.line([(x + 4 * sc, y - 16 * sc), (x + 15 * sc, y - 10 * sc)], dg.mix(col, a), 3 * sc)


def dashed(p, a_, b_, col, a, dash=12, gap=9, width=3):
    L = math.dist(a_, b_); n = int(L // (dash + gap)) + 1
    for k in range(n):
        u0 = k * (dash + gap) / L; u1 = min(1.0, (k * (dash + gap) + dash) / L)
        if u0 >= 1: break
        p.line([(a_[0] + (b_[0] - a_[0]) * u0, a_[1] + (b_[1] - a_[1]) * u0), (a_[0] + (b_[0] - a_[0]) * u1, a_[1] + (b_[1] - a_[1]) * u1)], dg.mix(col, a), width)


def draw_card(p, ph_t, a0, a1, a2, hi1=0.0, hi2=0.0, dim1=1.0, dim2=1.0, check1=0.0):
    """二つの疑問の画（第3章の終わりと、第5章の始まりで使う）。a0 題・a1/a2 ①②の出方、hi 強く（枠を青緑）、dim 薄く、check1 ①に「解けた ✓」"""
    p.text((W / 2, 64), "二つの疑問", 34, dg.mix(dg.INK, a0))
    # ---------------------------------------------------------------- ① 隣の人の曲が混ざらない？
    if a1 > 0:
        aa = a1 * dim1; bx = (60, 112, 620, 560); panel(p, bx, aa, hi1)
        badge(p, (112, 166), "1", dg.TEAL, aa)
        p.text((150, 152), "隣の人の曲が", 32, dg.mix(dg.INK, aa), anchor="lm"); p.text((150, 194), "混ざらないのはなぜ？", 32, dg.mix(dg.INK, aa), anchor="lm")
        dg.DS = 0.62
        rows = ((300, dg.TEAL, "o", "自分の組"), (450, dg.AMBER, "x", "隣の組"))
        for y, col, mk, nm in rows:
            dg.phone(p, 190, y, ((92, 196, 210), (160, 120, 200)) if col == dg.TEAL else ((240, 180, 90), (220, 110, 120)), a=aa, ds=0.62)
            dg.earbud(p, 500, y - 10, col, (150, 158, 166), a=aa, ds=0.62)
            dg.mark(p, (120, y), "o" if mk == "o" else "t", 13, dg.mix(col, aa), 4)
            p.text((120, y + 34), nm, 18, dg.mix(col, aa))
            note(p, (560, y - 52), col, aa, 1.0)
        for (ya, ca), (yb, _) in (((300, dg.TEAL), (440, None)), ((450, dg.AMBER), (290, None))):     # 電波は、どちらのイヤホンにも届いている
            dashed(p, (232, ya), (452, yb), ca, aa * 0.75, 10, 9, 3)
        for y, col in ((300, dg.TEAL), (450, dg.AMBER)):
            dashed(p, (232, y), (452, y - 10), col, aa * 0.9, 14, 8, 4)
        p.text((342, 372), "？" if check1 < 0.5 else "", 44, dg.mix(dg.TEAL, aa * (1 - check1)))
        if check1 > 0:                                                # 第5章：「解けました」→ 解けた ✓
            c_ = (520, 500); r_ = 46 * (0.6 + 0.4 * check1)
            p.ell((c_[0] - r_, c_[1] - r_, c_[0] + r_, c_[1] + r_), fill=dg.mix(dg.GREEN, check1))
            p.line([(c_[0] - r_ * 0.45, c_[1] + r_ * 0.02), (c_[0] - r_ * 0.1, c_[1] + r_ * 0.36), (c_[0] + r_ * 0.48, c_[1] - r_ * 0.34)], dg.mix(dg.WHITE, check1), 7)
            p.text((400, 500), "解けた", 30, dg.mix(dg.GREEN, check1))
    # ---------------------------------------------------------------- ② ときどき音が途切れる？
    if a2 > 0:
        bx = (660, 112, 1220, 560); aa = a2 * dim2; panel(p, bx, aa, hi2)
        badge(p, (712, 166), "2", dg.TEAL, aa)
        p.text((750, 152), "ときどき音が", 32, dg.mix(dg.INK, aa), anchor="lm"); p.text((750, 194), "途切れるのはなぜ？", 32, dg.mix(dg.INK, aa), anchor="lm")
        dg.phone(p, 760, 375, ((92, 196, 210), (160, 120, 200)), a=aa, ds=0.62)
        dg.earbud(p, 1110, 365, dg.TEAL, (150, 158, 166), a=aa, ds=0.62)
        # 音の波（左から右へ流れる）。真ん中で切れる
        x0, x1, yc = 810, 1052, 375; gap0, gap1 = 905, 965
        ph = 2 * math.pi * 1.1 * ph_t
        for seg0, seg1 in ((x0, gap0), (gap1, x1)):
            pts = [(x, yc + 22 * math.sin((x - x0) / 15.0 - ph) * math.sin(math.pi * (x - x0) / (x1 - x0)) ** 0.35) for x in range(seg0, seg1 + 1, 3)]
            p.line(pts, dg.mix(dg.TEAL, aa), 4)
        p.line([(gap0 + 6, yc), (gap1 - 6, yc)], dg.mix((190, 196, 202), aa), 3)
        p.text(((gap0 + gap1) / 2, yc - 48), "？", 44, dg.mix(dg.TEAL, aa))


def frame(t):
    im = Image.new("RGB", (W * S, H * S), dg.BG); p = dg.Pen(ImageDraw.Draw(im))
    a0 = dg.sm((t - T_A) / 0.4)
    a1 = dg.sm((t - T_Q1) / 0.45); a2 = dg.sm((t - T_Q2) / 0.45); fo = dg.sm((t - T_FOCUS) / 0.45)
    draw_card(p, t - T_Q2, a0, a1, a2, hi1=fo, dim2=1.0 - 0.55 * fo)   # 最後は ② を薄く、① を強く
    return im.resize(dg.OUT_WH, Image.LANCZOS)


if __name__ == "__main__":
    out = os.path.join(sys.argv[1], "questions"); os.makedirs(out, exist_ok=True)
    n = int(round((T_B - T_A) * FPS))
    if "--still" in sys.argv:
        for s_ in sys.argv[sys.argv.index("--still") + 1].split(","): frame(float(s_)).save(os.path.join(sys.argv[1], "q_%06.2f.png" % float(s_)))
    else:
        for i in range(n): frame(T_A + i / FPS).save(os.path.join(out, "q_%04d.png" % (i + 1)), compress_level=1)
        json.dump(dict(t0=T_A, t1=T_B, fps=FPS, frames=n, q1=T_Q1, q2=T_Q2, focus=T_FOCUS), open(os.path.join(sys.argv[1], "ch03_questions.json"), "w"), indent=0)
    print("questions", n, "Q1 %.2f Q2 %.2f focus %.2f" % (T_Q1, T_Q2, T_FOCUS))
