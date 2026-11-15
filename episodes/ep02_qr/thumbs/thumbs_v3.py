# QR回のサムネ v3（2026-11-15）。ユーザー「字が死ぬほどチープ」「参考のやつ一回見てよ」から作り直し
#   参考（前に作ってもらった 6 枚）の形：とても太いゴシック体（Noto Sans JP Black）のべた塗り 2 行、ふちは 1 本
#   （明るい字＝紺のふち、暗い字＝白のふち）、やわらかい影。左上に「QRコード」の札。大きな QR が右に主役、まるロボは小さく手前
#   絵は Gemini の画像の AI に「字なし」で描かせ（gen）、字はこちらで重ねる（comp）。絵の AI に字を描かせない
#   使い方: THUMB_WORK=<作業フォルダ> THUMB_FONT=<NotoSansJP[wght].ttf> python3 thumbs_v3.py gen D B BD ／ comp
import os, sys, json, base64, urllib.request, glob
from PIL import Image, ImageDraw, ImageFilter, ImageFont
S = os.environ["THUMB_WORK"]; G = os.path.join(S, "gen3"); OUT = os.path.join(S, "out3"); os.makedirs(G, exist_ok=True); os.makedirs(OUT, exist_ok=True)
FONT = os.environ.get("THUMB_FONT", "")
ROBOT = ("The small mascot robot must match the reference images: a glossy white sphere body, ONE large round teal-and-navy camera-lens eye on the front, "
         "teal round discs on both sides, a thin dark antenna with a small orange ball on top, two short stubby legs with navy feet glowing teal at the soles. "
         "No mouth, no arms.")
BASE = ("Background art for a YouTube thumbnail, 16:9, polished cinematic 3D render like a high-end tech explainer channel. ABSOLUTELY NO TEXT: no letters, "
        "no numbers, no words, no symbols, no logos anywhere (the QR code pattern itself is fine). The LEFT 45% of the frame, upper two-thirds, must be calm "
        "and fairly empty background (a headline will be added there later). Keep the bottom-right corner free of important elements. " + ROBOT)
LAYOUT = ("STRICT LAYOUT (like a pro YouTube thumbnail): the QR card occupies the RIGHT half (x 52-97%, y 5-88%). The robot is SMALL, about one third "
          "of the frame height, standing at x 22-40%, y 58-95%. The whole TOP-LEFT area (x 0-50%, y 0-56%) is empty, plain, softly lit background for a big headline. ")
PLANS = {
 "P2C": ("Background art for a YouTube thumbnail, 16:9, polished 3D render. ABSOLUTELY NO TEXT and NO badges, icons, check marks or X marks anywhere (QR patterns "
        "are fine). Clean bright light-grey studio with a soft teal accent light on the right. STRICT LAYOUT: everything left of the frame's horizontal middle "
        "(x 0-52%) is completely empty plain background. Two identical crisp QR codes on thick white cards stand side by side ONLY in x 55-98%, vertically "
        "y 25-90%, each card about 20% of the frame width, small gap between them. LEFT card (at x 55-76%): the small robot sits on its lower-right corner, "
        "covering about a quarter of the code. RIGHT card (at x 78-98%): a few small dark smudges / tiny ink stains on its white squares (subtle but visible). "
        "Nothing else. " + ROBOT),
 "P2B": ("Background art for a YouTube thumbnail, 16:9, polished 3D render. ABSOLUTELY NO TEXT anywhere (QR patterns are fine). Clean bright light-grey studio "
        "with a soft teal accent light. STRICT LAYOUT: the LEFT 44% of the frame is completely empty plain background (a big headline goes there). In the RIGHT "
        "56% (x 46-98%), two identical crisp QR codes on thick white cards stand side by side in the lower 70% (y 28-95%), each card about 24% of the frame width. "
        "LEFT card: the small robot sits on its lower-right corner, covering about a quarter of the code; a green circular badge with a white check mark floats "
        "just above the card's top-left corner. RIGHT card: a few small dark smudges / tiny ink stains on its white squares (subtle but visible); a red circular "
        "badge with a white X floats just above the card's top-right corner. " + ROBOT),
 "P1": (LAYOUT + "Dark navy studio with soft teal rim lights and subtle bokeh. The large crisp QR code is printed on a thick white card lying slightly tilted "
       "toward camera. The small robot is SITTING on the lower-right corner of the QR code, covering roughly a quarter of the code, looking pleased. A smartphone "
       "hovers above the card at the upper right, its screen facing us showing only a big glowing green check mark (no text). The robot is ON the card here, "
       "so ignore the robot position in the layout; keep the top-left empty."),
 "P2": ("Background art for a YouTube thumbnail, 16:9, polished 3D render. ABSOLUTELY NO TEXT anywhere (QR patterns are fine). Clean bright light-grey studio. "
        "The TOP 35% of the frame is plain empty background. Two identical large crisp QR codes on thick white cards stand side by side in the lower 65%, "
        "the left one centered at x 28%, the right one at x 72%. LEFT card: the small robot sits on its lower-right corner, covering about a quarter of the "
        "code, and a big green circular badge with a white check mark floats at its upper-left corner. RIGHT card: a few small dark smudges / tiny ink stains "
        "on its white squares (subtle but visible), and a big red circular badge with a white X floats at its upper-right corner. " + ROBOT),
 "P3": ("Photorealistic stock-photo style image, 16:9, like a real camera photo (NOT a 3D render, no cartoon). ABSOLUTELY NO TEXT anywhere (QR pattern is fine). "
        "A large QR code sticker on a slightly worn poster on a city wall or a shop window, shot close-up with shallow depth of field and natural daylight. "
        "The QR code fills the RIGHT 55% of the frame. Its lower-right corner is clearly torn off and scratched, with the paper peeling, yet the rest is intact. "
        "The LEFT 45% of the frame is out-of-focus wall/background, calm and fairly empty, for a big headline. No people, no robot."),
 "D2": (LAYOUT + "Dark navy studio with soft teal rim lights and subtle bokeh. The large crisp QR code is printed on a thick white card standing upright, "
       "slightly angled. About twelve small flat black ink splatter dots are scattered on its white modules, and a glowing bright RED ring (neon-like, slightly "
       "glowing) circles a cluster of three ink dots on the lower part of the code, like a highlight mark. A toppled small glass ink bottle lies at the base of the "
       "card. The small robot leans back in shock, looking at the card, with a few small yellow surprise lines near its head."),
 "B2": (LAYOUT + "Bright clean light-grey studio, soft daylight, subtle teal light from the right. The large crisp QR code is printed on a thick white card standing "
       "upright, slightly angled. The small robot is NOT on the card; instead a big soft-edged dark grey sticky note / card covers the lower-right quarter of "
       "the QR code, and a smartphone in front of the QR shows only a big glowing green check mark (no text). The small robot stands at lower left looking up, surprised."),
 "D": ("Dark navy studio with soft teal rim lights and subtle bokeh, like a premium product shot. On the right, a large crisp QR code printed on a thick white "
       "card standing upright and slightly angled toward camera, filling the right half. About twelve small flat black ink splatter dots are scattered on its "
       "WHITE modules (small, clearly visible, flat ink stains, not 3D drops). A toppled small glass ink bottle lies at the base of the card with a small ink "
       "puddle. The small robot stands at lower-left-center, leaning back in shock, looking at the card."),
 "B": ("Bright clean light-grey studio, soft daylight, subtle teal accent light from the right. On the right, a large crisp QR code printed on a thick white card "
       "lying slightly tilted on a smooth table, filling the right half. The small robot is SITTING on the lower-right corner of the QR code, covering roughly a "
       "quarter of it, happily. Above the card, a smartphone hovers, its screen facing the QR code (screen not visible to us), with a soft scan light beam."),
 "BD": ("Clean bright light-grey studio. Two identical large crisp QR codes on white cards side by side in the lower 65% of the frame, centered. "
        "LEFT card: the small robot sits on its lower-right corner, covering about a quarter of the code; a big green circular badge with a white check mark "
        "floats at its upper-left. RIGHT card: about twelve small flat black ink splatter dots on its white modules; a big red circular badge with a white "
        "X floats at its upper-right. The top 30% of the frame is plain empty background for a headline."),
}
def gen(name, refs=("op_49.png", "op_13.png", "op_28.png")):
    parts = [{"text": BASE + "\n\n" + PLANS[name]}]
    for ref in refs:
        p = os.path.join(S, "src", ref)
        if os.path.exists(p): parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(open(p, "rb").read()).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    r = json.load(urllib.request.urlopen(req, timeout=300)); k = len(glob.glob(os.path.join(G, name + "_*.png")))
    for c in r.get("candidates", []):
        for pt in c.get("content", {}).get("parts", []):
            d = pt.get("inlineData") or pt.get("inline_data")
            if d: k += 1; fn = os.path.join(G, "%s_%d.png" % (name, k)); open(fn, "wb").write(base64.b64decode(d["data"])); print(fn)

# ---- 字を重ねる（2560×1440 で組んで 1280×720 に縮める）----
W, H = 2560, 1440
NAVY, WHITE, YEL, RED, BLACK, TEAL, CYAN = (12, 22, 44), (255, 255, 255), (255, 226, 0), (226, 24, 24), (14, 14, 18), (0, 112, 112), (0, 230, 230)
def F(px, wght=900):
    f = ImageFont.truetype(FONT, px); f.set_variation_by_axes([wght]); return f
def line(im, xy, runs, px, edge, ew=None, track=-0.02, shadow=True):
    """runs：[(文字, 色)]。edge：ふちの色（1 本）。字の間を少し詰める（参考の詰まった組み方）"""
    f = F(px); ew = ew if ew is not None else int(px * 0.11); x, y = xy
    lay_s = Image.new("RGBA", (W, H)); lay_e = Image.new("RGBA", (W, H)); lay_f = Image.new("RGBA", (W, H))
    ds, de, df = ImageDraw.Draw(lay_s), ImageDraw.Draw(lay_e), ImageDraw.Draw(lay_f)
    for t, col in runs:
        for ch in t:
            b = f.getbbox(ch); adv = f.getlength(ch)
            if shadow: ds.text((x + px * 0.03, y + px * 0.05), ch, font=f, fill=(0, 0, 0, 120), stroke_width=ew, stroke_fill=(0, 0, 0, 120))
            de.text((x, y), ch, font=f, fill=edge + (255,), stroke_width=ew, stroke_fill=edge + (255,))
            df.text((x, y), ch, font=f, fill=col + (255,))
            x += adv + px * track
    if shadow: im = Image.alpha_composite(im, lay_s.filter(ImageFilter.GaussianBlur(px * 0.04)))
    return Image.alpha_composite(Image.alpha_composite(im, lay_e), lay_f), x
def tag(im, xy, txt, px=92, bg=CYAN, fg=NAVY, edge=None):
    """左上の札（参考：水色の六角の札に紺の字）"""
    f = F(px); tw = f.getlength(txt); x, y = xy; h = int(px * 1.45); pad = int(px * 0.55)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); w = tw + pad * 2; k = h // 2
    poly = [(x + k * 0.6, y), (x + w - k * 0.6, y), (x + w, y + k), (x + w - k * 0.6, y + h), (x + k * 0.6, y + h), (x, y + k)]
    if edge: d.polygon([(px_ + (3 if px_ > x + w / 2 else -3), py_ + (3 if py_ > y + k else -3)) for px_, py_ in poly], fill=edge + (255,))
    d.polygon(poly, fill=bg + (255,))
    b = f.getbbox(txt); d.text((x + pad, y + (h - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill=fg + (255,))
    return Image.alpha_composite(im, lay)
def arrow(im, p0, p1, bend=0.35, w=34, col=RED, edge=WHITE):
    """しくみの正体のような、白いふちの太い赤い矢印（p0 から p1 へ、少し曲げる）"""
    import math
    (x0, y0), (x1, y1) = p0, p1; mx, my = (x0 + x1) / 2, (y0 + y1) / 2; dx, dy = x1 - x0, y1 - y0
    cx, cy = mx - dy * bend, my + dx * bend
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1) for t in [i / 60 for i in range(61)]]
    ang = math.atan2(y1 - pts[-6][1], x1 - pts[-6][0]); L = w * 2.6
    tip = (x1 + math.cos(ang) * w * 0.6, y1 + math.sin(ang) * w * 0.6)
    head = [tip, (x1 - math.cos(ang - 0.55) * L, y1 - math.sin(ang - 0.55) * L), (x1 - math.cos(ang + 0.55) * L, y1 - math.sin(ang + 0.55) * L)]
    body = pts[:-4]
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.line([(x + 10, y + 14) for x, y in body], fill=(0, 0, 0, 110), width=w + 16, joint="curve"); ds.polygon([(x + 10, y + 14) for x, y in head], fill=(0, 0, 0, 110))
    d.line(body, fill=edge + (255,), width=w + 16, joint="curve"); d.polygon(head, fill=edge + (255,), outline=edge + (255,), width=16)
    d.line(body, fill=col + (255,), width=w, joint="curve"); d.polygon(head, fill=col + (255,))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8))), lay)
def bg(path):
    return Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
def save(im, name):
    p = os.path.join(OUT, name + ".jpg"); im.convert("RGB").resize((1280, 720), Image.LANCZOS).save(p, quality=93); return p
def fit(runs, maxw, px0, track=-0.02):
    """字の幅が maxw に収まる一番大きな字の大きさ"""
    px = px0
    while px > 80:
        f = F(px); w = sum(f.getlength(c) + px * track for t, _ in runs for c in t)
        if w <= maxw: return px
        px -= 4
    return px
LAYOUTS = {   # 名前 → (地の種類, 札, [1 行目, 2 行目], 字の右の端)
 "P1": ("dark", ("QRコード", CYAN, NAVY), [[("隠しても", WHITE)], [("なぜ", WHITE), ("読める？", YEL)]], 1400, [250, 300]),
 "P3": ("photo", None, [[("こんなに", WHITE)], [("欠けても", WHITE)], [("なぜ読める？", YEL)]], 1250, [280, 280, 280]),
 "D2": ("dark", ("QRコード", CYAN, NAVY), [[("たった", WHITE), ("3%", YEL), ("で", WHITE)], [("読めない!?", YEL)]], 1300),
 "B2": ("light", ("QRコード", TEAL, WHITE), [[("隠しても", BLACK)], [("読めた!?", RED)]], 1300),
}
CARDS_P2 = {"P2C_2.png": [(1050, 317, 1766, 1152), (1818, 317, 2509, 1152)]}   # 絵ごとの左と右の QR の札の位置（元の絵の 2560×1440 で。10% の目盛りを重ねて決めた）
def badge(im, c, ok, r=110):
    """緑の ✓／赤の × の丸い印（白いふち・影）"""
    x, y = c; lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); sh = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(sh)
    ds.ellipse((x - r + 8, y - r + 12, x + r + 8, y + r + 12), fill=(0, 0, 0, 120))
    d.ellipse((x - r - 12, y - r - 12, x + r + 12, y + r + 12), fill=WHITE + (255,)); d.ellipse((x - r, y - r, x + r, y + r), fill=((40, 170, 70) if ok else (220, 40, 40)) + (255,))
    if ok: d.line([(x - r * 0.48, y + r * 0.02), (x - r * 0.12, y + r * 0.38), (x + r * 0.5, y - r * 0.36)], fill=WHITE + (255,), width=int(r * 0.24), joint="curve")
    else:
        k = r * 0.4; d.line([(x - k, y - k), (x + k, y + k)], fill=WHITE + (255,), width=int(r * 0.24)); d.line([(x - k, y + k), (x + k, y - k)], fill=WHITE + (255,), width=int(r * 0.24))
    return Image.alpha_composite(Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10))), lay)
def comp(choice):
    made = []
    for name, src in choice.items():
        im = bg(os.path.join(G, src)); key = name.split("_")[0]
        if key == "P2":   # 比べる案。しくみの正体の「なぜ／右に2回／左に1回？」と同じ 3 行・白と黄色の極太字・黒の太いふち。✓ と × はこちらで描く
            k = 0.88; sw, sh_ = int(W * k), int(H * k); ox, oy = W - sw, (H - sh_) // 2   # 絵を少し小さくして右へ寄せ、左を同じ地でのばす
            sm = bg(os.path.join(G, src)).resize((sw, sh_), Image.LANCZOS); cv = Image.new("RGBA", (W, H))
            cv.paste(sm, (ox, oy)); cv.paste(sm.crop((0, 0, 6, sh_)).resize((ox, sh_)).filter(ImageFilter.GaussianBlur(20)), (0, oy))
            cv.paste(cv.crop((0, oy, W, oy + 6)).resize((W, oy)), (0, 0)); cv.paste(cv.crop((0, oy + sh_ - 6, W, oy + sh_)).resize((W, H - oy - sh_)), (0, oy + sh_))
            im = cv; c = [tuple(int(o + k * v) for o, v in zip((ox, oy, ox, oy), b)) for b in CARDS_P2[src]]   # 札の (左, 上, 右, 下)
            im = tag(im, (70, 60), "QRコード", px=96, bg=TEAL, fg=WHITE)
            rows = [[("なぜ", WHITE)], [("こっち", YEL), ("は", WHITE)], [("読めない？", YEL)]]
            px = min(fit(r, c[0][0] - 100, 300) for r in rows); y = 220; xe = []
            for r in rows:
                im, x_ = line(im, (60, y), r, px, BLACK, ew=int(px * 0.14)); xe.append((x_, y)); y += int(px * 1.04)
            im = badge(im, (c[0][0] + 40, c[0][1] + 70), True); im = badge(im, (c[1][2] - 110, c[1][1] - 10), False)
            x2, y2 = xe[1]                                          # 「こっちは」の右から、右の札（読めない方）の真ん中へ
            # 左の札の上を高く越えて、右の札の上から指す（左の札・✓ の印・字に重ねない）
            im = arrow(im, (x2 + 30, y2 + px * 0.15), ((c[1][0] + c[1][2]) / 2 - 60, c[1][1] + 230), bend=-0.55, w=40)
            made.append(save(im, "v3_" + name.replace("_", ""))); continue
        kind, tg, lines, maxw, *mx = LAYOUTS[key]; mx = mx[0] if mx else None
        edge = NAVY if kind == "dark" else (BLACK if kind == "photo" else WHITE)
        ewk = 0.14 if kind == "photo" else 0.11   # しくみの正体の形は黒いふちを太く
        if tg: im = tag(im, (90, 50), tg[0], px=104, bg=tg[1], fg=tg[2])   # 参考：札は高さの 1 割ほど
        y = 230 if kind == "dark" else (110 if kind == "photo" else 205)
        for i, runs in enumerate(lines):
            px = fit(runs, maxw - 90, mx[i] if mx else (360 if kind == "dark" else 320))   # 明るい地の案は、まるロボの頭に字がかからない大きさまで                  # 参考：1 行が高さの 2 割以上
            im, _ = line(im, (90, y), runs, px, edge, ew=int(px * ewk))
            y += int(px * 1.06)
        if key == "P3": im = arrow(im, (420, y + 110), (1760, 1180), bend=-0.15, w=42)   # 字の下から出して、字に重ねない   # 破れた角を指す（絵を見て位置を合わせる）
        made.append(save(im, "v3_" + name.replace("_", "") ))
    return made
if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]: gen(a)
    else:
        print("\n".join(comp(json.loads(sys.argv[2]))))
