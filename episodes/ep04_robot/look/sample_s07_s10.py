# 見た目の作り直しの見本：S07（1:51〜2:12 ゆがんだ文字・人と機械）と S10（3:33〜4:05 人とプログラムの比べっこ）
# MARU_WORK=<作業> python3 sample_s07_s10.py <フォント（package）> <切り抜き cutout.py の出力> <出力.mp4>
#   切り替えは字幕の切り替わり（subs_events.json）と同じコマ。声と BGM は animatic_tmp/voice.wav を切り出す
import os, sys, json, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import design as D
FD, CUT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
D.FDIR[0] = FD
W = os.environ["MARU_WORK"]
EV = json.load(open(os.path.join(HERE, "..", "animatic", "subs_events.json"), encoding="utf-8"))
def said(text, after=0.0):
    for a, c, t in EV:
        if a >= after and t.replace("\\N", "").startswith(text): return a
    raise KeyError(text)
FPS = 24


def maru(pose, h):
    im = Image.open(os.path.join(CUT, "maru_%s.png" % pose)).convert("RGBA")
    bb = im.getbbox(); im = im.crop(bb); s = h / im.height
    im = im.resize((int(im.width * s), int(h)), Image.LANCZOS)
    # 足もとの影
    sh = Image.new("RGBA", (im.width + 60, im.height + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.ellipse([30 + im.width * 0.12, im.height - 4, 30 + im.width * 0.88, im.height + 22], fill=(22, 38, 74, 70))
    from PIL import ImageFilter
    sh = sh.filter(ImageFilter.GaussianBlur(8)); sh.alpha_composite(im, (30, 0))
    return sh, (-sh.width / 2, -sh.height + 20)


def warp_word(word, size=110, seed=1):
    random.seed(seed); f = D.font(size)
    tmp = Image.new('L', (int(size * len(word) * 0.75) + 80, int(size * 1.6)), 0); d = ImageDraw.Draw(tmp); x = 30
    for ch in word:
        layer = Image.new('L', tmp.size, 0); dl = ImageDraw.Draw(layer)
        dl.text((x, size * 0.2 + random.randint(-12, 12)), ch, font=f, fill=255)
        layer = layer.rotate(random.uniform(-18, 18), center=(x + size * 0.3, size * 0.8), resample=Image.BICUBIC)
        tmp = Image.fromarray(np.maximum(np.array(tmp), np.array(layer))); x += int(d.textlength(ch, font=f) * 0.82)
    a = np.array(tmp); out = np.zeros_like(a)
    for yy in range(a.shape[0]): out[yy] = np.roll(a[yy], int(10 * math.sin(yy / 14.0)))
    a2 = out.copy()
    for xx in range(a.shape[1]): a2[:, xx] = np.roll(out[:, xx], int(9 * math.sin(xx / 22.0)))
    img = Image.fromarray(a2); ImageDraw.Draw(img).line([(10, img.height * 0.55), (img.width - 10, img.height * 0.42)], fill=255, width=7)
    return img.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(0.8))


def test_card(typed=""):
    def dr(d, W_, H_, S, img):
        for k, (w, sd) in enumerate((("morning", 3), ("upon", 7))):
            wi = warp_word(w, 100, sd)
            wi = wi.resize((wi.width * S, wi.height * S), Image.LANCZOS)
            tint = Image.new("RGBA", wi.size, (52, 58, 72, 255))
            img.paste(tint, (int((60 if k == 0 else 470) * S), int(70 * S)), wi)
        d.rounded_rectangle([150 * S, 260 * S, 760 * S, 318 * S], 14 * S, fill=(241, 245, 249))
        if typed:
            f = D.font(34 * S); d.text((176 * S, 268 * S), typed, font=f, fill=D.INK)
    return D.card(910, 360, draw=dr, header=None)


def write(frames_fn, t0, t1, path):
    os.makedirs(path, exist_ok=True)
    n = round((t1 - t0) * FPS)
    for k in range(n):
        frames_fn(t0 + k / FPS).save(os.path.join(path, "f_%05d.png" % k))
    return n


# ---------------- S07
T0a, T1a = said("少し前まで") - 0.4, said("実は、このゆがんだ") - 0.05
st = D.Stage(D.background(), dur=T1a - T0a, t0=T0a)
t_ex, t_type, t_seen, t_hm, t_diff = said("少し前まで"), said("ぐにゃぐにゃ"), said("見たことがある"), said("人には読める"), said("その差で")
card_main = st.add(test_card(), (560, 300), t_ex, t_hm - 0.0)
# 打ち込み：1 字ずつ（ぐにゃぐにゃ〜の間）
word = "morning upon"
for i in range(1, len(word) + 1):
    ta = t_type + 0.8 + i * 0.16
    st.add(test_card(word[:i]), (560, 300), ta, ta + 0.16 if i < len(word) else t_hm, pop=False, fade_out=0.0, z=1)
mr = st.add(maru("front", 230), (1110, 520), t_ex + 0.3, t_hm, bob=3, hop=(t_seen + 0.2,))
# 人には読める／機械には読めない
st.add(D.person(210), (300, 300), t_hm, slide=(-60, 0))
st.add(maru("q", 230), (980, 400), t_hm, bob=3, z=2)
def ok_word(d, cx, cy, S, img):
    D.ctext(d, (cx - 32 * S, cy), "morning", D.font(50 * S), D.NAVY); D.check_icon(d, cx + 130 * S, cy, 24 * S)
st.add(D.bubble(360, 110, (-110, 95), ok_word), (420, 140), t_hm + 0.15)
def q_word(d, cx, cy, S, img):
    D.ctext(d, (cx, cy), "？？？", D.font(54 * S), D.ORANGE)
st.add(D.bubble(250, 110, (60, 110), q_word), (890, 150), t_hm + 0.55)
st.add(D.pill("人", 44, accent=D.ORANGE), (300, 470), t_hm + 0.2)
st.add(D.pill("機械", 44, accent=D.TEAL), (980, 470), t_hm + 0.6)
# その差で：まん中に ≠
def neq(d, W_, H_, S, img):
    D.ctext(d, (W_ / 2, H_ / 2 - 4 * S), "≠", D.font(90 * S), D.NAVY2)
st.add(D.card(130, 130, r=65, draw=neq), (640, 300), t_diff + 0.1)

# ---------------- S10
T0b, T1b = said("2023年には") - 0.4, said("では、どうやって") - 0.05
st2 = D.Stage(D.background(top=(238, 243, 250), bottom=(214, 224, 240)), dur=T1b - T0b, t0=T0b)
t_y, t_who, t_res, t_fast, t_hum, t_hsec, t_wow = (said("2023年には"), said("ゆがんだ文字のテストを"), said("結果は"),
                                                  said("しかも、1問"), said("人は、正解"), said("1問に、9秒"), said("なんと"))
st2.add(D.pill("2023年", 50, accent=D.ORANGE), (640, 64), t_y)
COLS = ((330, "人", D.ORANGE), (950, "プログラム", D.TEAL))
for k, (x, who, col) in enumerate(COLS):
    st2.add(D.card(460, 370, header=(col, None)), (x, 320), t_y + 0.2 + k * 0.15, slide=(0, 40))
    st2.add(D.pill(who, 44, fg=D.WHITE, bg=col), (x, 160), t_who + k * 0.25)
# 中身：正解（棒）と時間（数字）
def rowcard(label, val, frac, col, lo=None):
    def dr(d, W_, H_, S, img):
        D.ctext(d, (64 * S, H_ / 2), label, D.font(34 * S), D.MUTED)
        x0, x1, y0, y1 = 130 * S, W_ - 24 * S, H_ / 2 + 12 * S, H_ / 2 + 30 * S
        if frac is not None:
            d.rounded_rectangle([x0, y0, x1, y1], 9 * S, fill=(230, 236, 244))
            a = x0 + (x1 - x0) * (lo if lo is not None else 0); b = x0 + (x1 - x0) * frac
            d.rounded_rectangle([a, y0, b, y1], 9 * S, fill=col)
            D.ctext(d, ((x0 + x1) / 2, H_ / 2 - 22 * S), val, D.font(46 * S), D.NAVY)
        else:
            D.ctext(d, ((x0 + x1) / 2, H_ / 2), val, D.font(52 * S), D.NAVY)
    return D.card(410, 118, r=22, bg=(250, 252, 255), draw=dr)
# プログラム：棒が伸びる（数コマで）
for i in range(1, 9):
    ta = t_res + 1.2 + i * 0.07
    st2.add(rowcard("正解", "ほぼ全部" if i == 8 else "", 0.97 * i / 8, D.TEAL), (950, 280), ta, ta + 0.07 if i < 8 else 1e9, pop=False, fade_out=0, z=1 + i)
st2.add(rowcard("時間", "1秒未満", None, D.TEAL), (950, 425), t_fast, z=1)
for i in range(1, 9):
    ta = t_hum + 0.3 + i * 0.07
    st2.add(rowcard("正解", "5〜8割" if i == 8 else "", 0.5 + 0.3 * i / 8, D.ORANGE, lo=0.0), (330, 280), ta, ta + 0.07 if i < 8 else 1e9, pop=False, fade_out=0, z=1 + i)
st2.add(rowcard("時間", "9〜15秒", None, D.ORANGE), (330, 425), t_hsec, z=1)
# まるロボ：まん中の下で見ている → なんと：跳ねて目が光る
st2.add(maru("up", 150), (640, 505), t_y + 0.5, t_wow, bob=2, z=20)
st2.add(maru("joy", 150), (640, 505), t_wow, hop=(t_wow + 0.1, t_wow + 0.6), z=20, pop=False)
def ring(d, W_, H_, S, img):
    pass
st2.add(D.pill("得意", 46, fg=D.WHITE, bg=D.TEAL, tail=(-70, 45)), (1150, 120), t_wow + 0.3, z=30)

# ---------------- 書き出し
if os.environ.get("STILLS"):
    for k, tt in enumerate(map(float, os.environ["STILLS"].split())):
        (st if tt < 200 else st2).frame(tt).save(OUT.replace(".mp4", "_%d.png" % k))
    sys.exit()
tmp = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_look_tmp"); os.makedirs(tmp, exist_ok=True)
na = write(st.frame, T0a, T1a, tmp + "/a"); nb = write(lambda t: st2.frame(t), T0b, T1b, tmp + "/b")
def seg(src, t0, t1, n, name):
    ass = os.path.join(tmp, name + ".ass")
    sys.path.insert(0, W + "/tools"); import subs_jp as SJ
    def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
    rs = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
          "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
          SJ.STYLE_MAIN.replace("Noto Sans CJK JP", "Noto Sans JP"), "", "[Events]",
          "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for a, c, tx in EV:
        if c > t0 and a < t1: rs.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(max(0, a - t0)), ts(min(c, t1) - t0), tx))
    open(ass, "w", encoding="utf-8").write("\n".join(rs) + "\n")
    o = os.path.join(tmp, name + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", src + "/f_%05d.png", "-ss", "%.3f" % t0, "-t", "%.3f" % (n / FPS),
                    "-i", W + "/animatic_tmp/voice.wav", "-vf", "subtitles=%s:fontsdir=%s" % (ass, FD + "/700Bold"),
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", o], check=True)
    return o
oa = seg(tmp + "/a", T0a, T1a, na, "a"); ob = seg(tmp + "/b", T0b, T1b, nb, "b")
open(tmp + "/list.txt", "w").write("file '%s'\nfile '%s'\n" % (oa, ob))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp + "/list.txt", "-c", "copy", OUT], check=True)
print("SAMPLE", OUT, na, nb)
