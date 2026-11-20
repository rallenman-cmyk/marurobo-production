# 1本目（電車でイヤホン）のサムネ作り直し（2026-11-20）。SKILL.md §9 の手順どおり：調べる → 参考を並べる → 設計書 → 作る → 点検
#   絵は Gemini の画像の AI に「字なし」で描かせ（gen）、字・札・矢印・赤い丸はこちらで重ねる（comp）。絵の AI に字を描かせない
#   型（branding.md・SKILL.md §9）：Noto Sans JP 900・白と黄色の極太字に黒の太いふち（字の大きさの 14%）・1 行 5 字ほどで 2 行・左上の半分、
#   左上に札、主役の物は右半分、まるロボは高さの 3 分の 1 ほどで左下、右下は空ける、矢印と印は字・まるロボ・ほかの印に重ねない
#   1本目の参考（前に作ってもらった 7 枚）から残すもの：電車とイヤホンの世界、自分の曲＝水色・隣の曲＝黄色、アンテナつきのまるロボ
#   使い方: THUMB_WORK=<作業フォルダ（src/ に本編のコマ）> THUMB_FONT=<NotoSansJP[wght].ttf> GEMINI_API_KEY=… python3 thumbs_ep01.py gen A B C
#           python3 thumbs_ep01.py comp '{"A": "A_1.png"}'
import os, sys, json, base64, math, urllib.request, glob
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = os.environ["THUMB_WORK"]; G = os.path.join(S, "gen"); OUT = os.path.join(S, "out")
os.makedirs(G, exist_ok=True); os.makedirs(OUT, exist_ok=True)
FONT = os.environ.get("THUMB_FONT", "")

ROBOT = ("The small mascot robot must match the reference images exactly: a glossy white sphere body, ONE large round teal-and-navy camera-lens eye "
         "on the front, teal round discs on both sides, a thin dark antenna with a small glowing orange ball on top, two short stubby legs with navy "
         "feet glowing teal at the soles. No mouth, no arms, no hands.")
BASE = ("Background art for a YouTube thumbnail, 16:9, polished cinematic 3D render like a high-end tech explainer channel. ABSOLUTELY NO TEXT: "
        "no letters, no numbers, no words, no logos, no signs or screens with writing anywhere. The TOP-LEFT area (x 0-50%, y 0-55%) must be calm, "
        "fairly dark and plain background (a big headline will be added there later). Keep the bottom-right corner (x 86-100%, y 84-100%) free of "
        "important elements. " + ROBOT)
LAYOUT = ("STRICT LAYOUT (like a pro YouTube thumbnail): the robot is SMALL - its whole body INCLUDING the antenna fits inside x 4-26%, "
          "y 62-97% of the frame (the antenna tip must be lower than 62% of the frame height). The whole top-left region x 0-52%, y 0-60% is "
          "empty plain background with nothing in it (no robot, no phone, no streams). ")
PLANS = {
 # A（おすすめ）：本編の「電波は隣のイヤホンにも届いている」を、見て分かるおかしな一点（隣の曲の光が自分のイヤホンに当たっている）にする
 "A": ("Setting: the inside of a commuter train at dusk, softly out of focus (blue seats, hanging hand straps, warm city lights through the windows). "
       "MAIN OBJECT on the RIGHT half (x 50-95%, y 6-88%): ONE GIANT glossy white wireless earbud (modern stem-style true-wireless earbud), standing "
       "upright and slightly tilted, its rounded speaker tip facing left. Two glowing streams of light flow INTO that speaker tip: (1) a cool CYAN "
       "stream carrying tiny glowing cyan music-note shaped particles, rising from a smartphone held low near the middle bottom of the frame "
       "(x 38-50%, y 74-94%); (2) a warm YELLOW-ORANGE stream carrying tiny glowing yellow music-note shaped particles, arriving from the far right edge "
       "of the frame from another passenger's smartphone (blurred, partly out of frame). Both streams clearly touch the same earbud tip. "
       "The small robot stands at the lower left (see layout), leaning back in surprise and looking up at the earbud."),
 # B：本編の「荷物（音のデータ）が届かない・落ちる」を、落ちていく一個にする（音切れのしくみを見せる回は空いていた）
 "B": ("Setting: a dark navy digital void with a faint teal grid glow on the floor. A narrow glowing CYAN light bridge runs from a smartphone floating "
       "at the middle left (x 34-46%, y 60-82%) across to ONE GIANT glossy white wireless earbud on the right (x 62-96%, y 8-86%). Small white "
       "cube parcels with teal edges travel along the bridge in a neat line toward the earbud. In the MIDDLE of the bridge (around x 52-62%, "
       "y 50-64%) the bridge has a small break, and one parcel is tipping off the edge and falling down into the dark gap below, slightly "
       "motion-blurred. The small robot stands at the lower left (see layout), leaning forward in panic toward the falling parcel."),
 # C：本編の「イヤホンの中で先に受け取って待たせる（バッファ）」を、中が見える断面にする（中を見せるサムネは伸びていた）
 "C": ("Setting: a dark navy studio with soft teal rim lights and subtle bokeh. MAIN OBJECT on the RIGHT half (x 48-96%, y 5-90%): ONE GIANT glossy "
       "white STEM-STYLE wireless earbud (same shape as the earbud in the last reference image, with its long stem clearly visible), its round head "
       "shown as a clean cutaway (the front half of the head's shell removed like a dollhouse), revealing inside a tiny warm-lit "
       "warehouse: a tall narrow dark-teal metal shelf tower holding several small white boxes stacked neatly on its shelves; the TOP shelf slot is "
       "clearly EMPTY. Tiny warm lights inside the earbud. The small robot stands OUTSIDE the earbud at the lower left (see layout), looking up at the cutaway in awe."),
}
REFS = {"A": ("robot_front.png", "robot_34.png", "robot_side.png", "giant_earbud.png"),
        "B": ("robot_front.png", "robot_34.png", "robot_side.png", "giant_earbud.png"),
        "C": ("robot_front.png", "robot_34.png", "robot_side.png", "buffer_tower.png", "giant_earbud.png")}


def gen(name):
    parts = [{"text": BASE + "\n\n" + LAYOUT + PLANS[name] + "\n\nThe attached images are references: the first ones show the robot (match it exactly); "
              "the last one shows the style of the scene in the video (match the clean 3D look, not the composition)."}]
    for ref in REFS[name]:
        p = os.path.join(S, "src", ref)
        if os.path.exists(p): parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(open(p, "rb").read()).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    r = json.load(urllib.request.urlopen(req, timeout=300)); k = len(glob.glob(os.path.join(G, name + "_*.png")))
    for c in r.get("candidates", []):
        for pt in c.get("content", {}).get("parts", []):
            d = pt.get("inlineData") or pt.get("inline_data")
            if d:
                k += 1; fn = os.path.join(G, "%s_%d.png" % (name, k)); open(fn, "wb").write(base64.b64decode(d["data"])); print(fn)


# ---- 字・札・矢印・赤い丸を重ねる（2560×1440 で組んで 1280×720 に縮める）----
W, H = 2560, 1440
NAVY, WHITE, YEL, RED, BLACK, CYAN = (12, 22, 44), (255, 255, 255), (255, 226, 0), (226, 24, 24), (14, 14, 18), (0, 230, 230)


def F(px, wght=900):
    f = ImageFont.truetype(FONT, px); f.set_variation_by_axes([wght]); return f


def line(im, xy, runs, px, edge, ew=None, track=-0.02, shadow=True):
    f = F(px); ew = ew if ew is not None else int(px * 0.14); x, y = xy
    lay_s = Image.new("RGBA", (W, H)); lay_e = Image.new("RGBA", (W, H)); lay_f = Image.new("RGBA", (W, H))
    ds, de, df = ImageDraw.Draw(lay_s), ImageDraw.Draw(lay_e), ImageDraw.Draw(lay_f)
    for t, col in runs:
        for ch in t:
            adv = f.getlength(ch)
            if shadow: ds.text((x + px * 0.03, y + px * 0.05), ch, font=f, fill=(0, 0, 0, 120), stroke_width=ew, stroke_fill=(0, 0, 0, 120))
            de.text((x, y), ch, font=f, fill=edge + (255,), stroke_width=ew, stroke_fill=edge + (255,))
            df.text((x, y), ch, font=f, fill=col + (255,))
            x += adv + px * track
    if shadow: im = Image.alpha_composite(im, lay_s.filter(ImageFilter.GaussianBlur(px * 0.04)))
    return Image.alpha_composite(Image.alpha_composite(im, lay_e), lay_f), x


def tag(im, xy, txt, px=92, bg=CYAN, fg=NAVY):
    f = F(px); tw = f.getlength(txt); x, y = xy; h = int(px * 1.45); pad = int(px * 0.55)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); w = tw + pad * 2; k = h // 2
    poly = [(x + k * 0.6, y), (x + w - k * 0.6, y), (x + w, y + k), (x + w - k * 0.6, y + h), (x + k * 0.6, y + h), (x, y + k)]
    d.polygon(poly, fill=bg + (255,))
    b = f.getbbox(txt); d.text((x + pad, y + (h - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill=fg + (255,))
    return Image.alpha_composite(im, lay)


def arrow(im, p0, p1, bend=0.35, w=40, col=RED, edge=WHITE):
    (x0, y0), (x1, y1) = p0, p1; mx, my = (x0 + x1) / 2, (y0 + y1) / 2; dx, dy = x1 - x0, y1 - y0
    cx, cy = mx - dy * bend, my + dx * bend
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1) for t in [i / 60 for i in range(61)]]
    ang = math.atan2(y1 - pts[-6][1], x1 - pts[-6][0]); L = w * 2.6
    tip = (x1 + math.cos(ang) * w * 0.6, y1 + math.sin(ang) * w * 0.6)
    head = [tip, (x1 - math.cos(ang - 0.55) * L, y1 - math.sin(ang - 0.55) * L), (x1 - math.cos(ang + 0.55) * L, y1 - math.sin(ang + 0.55) * L)]
    body = pts[:-4]
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.line([(x + 10, y + 14) for x, y in body], fill=(0, 0, 0, 110), width=w + 16, joint="curve"); ds.polygon([(x + 10, y + 14) for x, y in head], fill=(0, 0, 0, 110))
    d.line(body, fill=edge + (255,), width=w + 16, joint="curve"); d.polygon(head, fill=edge + (255,), outline=edge + (255,), width=16)
    d.line(body, fill=col + (255,), width=w, joint="curve"); d.polygon(head, fill=col + (255,))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8))), lay)


def ring(im, c, r, w=30, col=RED):
    """赤く光る丸（何が起きているかの印）。絵の AI に描かせず、こちらで位置を決める"""
    x, y = c; glow = Image.new("RGBA", (W, H)); dg = ImageDraw.Draw(glow)
    dg.ellipse((x - r, y - r, x + r, y + r), outline=col + (200,), width=w + 30)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    d.ellipse((x - r, y - r, x + r, y + r), outline=WHITE + (255,), width=w + 12)
    d.ellipse((x - r + 6, y - r + 6, x + r - 6, y + r - 6), outline=col + (255,), width=w)
    return Image.alpha_composite(Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(18))), lay)


def fit(runs, maxw, px0, track=-0.02):
    px = px0
    while px > 80:
        f = F(px); w = sum(f.getlength(c) + px * track for t, _ in runs for c in t)
        if w <= maxw: return px
        px -= 4
    return px


def bg(path):
    return Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")


def save(im, name):
    p = os.path.join(OUT, name + ".jpg"); im.convert("RGB").resize((1280, 720), Image.LANCZOS).save(p, quality=93); return p


# 案ごとの字と印（印の位置は、描いた絵に 10% の目盛りを重ねて決める。元の絵の 2560×1440 で）
TEXT = {"A": [[("隣の曲も", WHITE)], [("届いてる", YEL), ("!?", YEL)]],
        "B": [[("音切れの", WHITE)], [("正体", YEL), ("!?", YEL)]],
        "C": [[("イヤホンの", WHITE)], [("中に", WHITE), ("倉庫", YEL), ("!?", YEL)]]}
# 絵ごとの置き方と印。位置は元の絵の割合（0〜1）で、10% の目盛りを重ねて決めた。
#   k：絵を k 倍に縮めて右下に寄せる（絵の AI はまるロボを大きく・高く描きがちで、字にかかるため）。あいた左と上は暗い地にして、絵の端をぼかしてつなぐ
#   ring：赤く光る丸（x, y, 半径 px）。arrow：(出す行, 行の右端からのずれ px, 先の x, 先の y, 曲がり)。矢印は字・まるロボに重ねない
CONF = {"A_1.png": dict(k=0.75, px=262, ring=(0.765, 0.255, 120), arrow=(0, 40, 0.80, 0.215, -0.45)),
        "B_3.png": dict(k=0.76, px=268, ring=(0.553, 0.585, 115), arrow=(1, 40, 0.505, 0.555, -0.35)),
        "C_3.png": dict(k=0.88, ring=(0.585, 0.215, 230))}


def zoom_out(src, k):
    """絵を k 倍に縮めて右下に置き、左と上を暗い地にする（絵の端は地へなめらかにぼかす）"""
    im = bg(src); sw, sh = int(W * k), int(H * k); ox, oy = W - sw, H - sh
    sm = im.resize((sw, sh), Image.LANCZOS); fx, fy = int(sw * 0.12), int(sh * 0.12)
    ax_ = Image.new("L", (sw, sh), 255); dx_ = ImageDraw.Draw(ax_)        # 左の端をぼかす
    for i in range(fx): dx_.line([(i, 0), (i, sh)], fill=int(255 * (i / fx) ** 1.5))
    ay_ = Image.new("L", (sw, sh), 255); dy_ = ImageDraw.Draw(ay_)        # 上の端をぼかす
    for j in range(fy): dy_.line([(0, j), (sw, j)], fill=int(255 * (j / fy) ** 1.5))
    from PIL import ImageChops
    sm.putalpha(ImageChops.multiply(ax_, ay_))
    # 地の色：絵の左と上の端の平均を暗くした色
    e = im.convert("RGB").resize((64, 36)); px_ = [e.getpixel((0, y)) for y in range(36)] + [e.getpixel((x, 0)) for x in range(64)]
    c = tuple(int(sum(p[i] for p in px_) / len(px_) * 0.55) for i in range(3))
    cv = Image.new("RGBA", (W, H), c + (255,)); cv.alpha_composite(sm, (ox, oy))
    return cv, (ox, oy, k)


def to_cv(p, t):
    ox, oy, k = t; return (ox + p[0] * W * k, oy + p[1] * H * k)


def comp(choice):
    made = []
    for key, src in choice.items():
        cf = CONF.get(src, dict(k=1.0))
        im, t = zoom_out(os.path.join(G, src), cf["k"])
        im = tag(im, (90, 56), "Bluetooth", px=100, bg=CYAN, fg=NAVY)          # 左上の札（高さの 1 割ほど）
        y = 236; ends = []
        rows = TEXT[key]; px = min(fit(r, 1240, cf.get("px", 290)) for r in rows)            # 左上の半分に収める。1 行は高さの 2 割前後
        for runs in rows:
            im, xe = line(im, (84, y), runs, px, BLACK, ew=int(px * 0.14)); ends.append((xe, y + px * 0.55)); y += int(px * 1.06)
        if "ring" in cf:
            c = to_cv(cf["ring"][:2], t); im = ring(im, c, cf["ring"][2])
        if "arrow" in cf:
            row, dx, ax, ay, bend = cf["arrow"]; x0, y0 = ends[row]
            im = arrow(im, (x0 + dx, y0), to_cv((ax, ay), t), bend=bend)
        made.append(save(im, "ep01_%s" % key))
    return made


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]: gen(a)
    else:
        print("\n".join(comp(json.loads(sys.argv[2]))))
