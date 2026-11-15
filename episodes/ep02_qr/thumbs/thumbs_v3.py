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
 "D2": ("dark", ("QRコード", CYAN, NAVY), [[("たった", WHITE), ("3%", YEL), ("で", WHITE)], [("読めない!?", YEL)]], 1300),
 "B2": ("light", ("QRコード", TEAL, WHITE), [[("隠しても", BLACK)], [("読めた!?", RED)]], 1300),
}
def comp(choice):
    made = []
    for name, src in choice.items():
        im = bg(os.path.join(G, src)); kind, (tt, tb, tf), lines, maxw = LAYOUTS[name.split("_")[0]]
        edge = NAVY if kind == "dark" else WHITE
        im = tag(im, (90, 50), tt, px=104, bg=tb, fg=tf)   # 参考：札は高さの 1 割ほど
        y = 230 if kind == "dark" else 205
        for i, runs in enumerate(lines):
            px = fit(runs, maxw - 90, 360 if kind == "dark" else 320)   # 明るい地の案は、まるロボの頭に字がかからない大きさまで                  # 参考：1 行が高さの 2 割以上
            im, _ = line(im, (90, y), runs, px, edge)
            y += int(px * 1.06)
        made.append(save(im, "v3_" + name.replace("_", "") ))
    return made
if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for a in sys.argv[2:]: gen(a)
    else:
        print("\n".join(comp(json.loads(sys.argv[2]))))
