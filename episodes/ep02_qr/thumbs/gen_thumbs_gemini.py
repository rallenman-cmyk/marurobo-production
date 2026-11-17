# QR回のサムネ案を Gemini の画像の AI で作る（2026-11-15）。前に作ってもらった案と同じ作り：
#   大きな QR が主役・太い 2 行の字（白／黄色、または黒／赤）・左上に「QRコード」の札・まるロボは小さく手前
#   まるロボの見た目は本編の 3D のコマを見本として渡して、似せる
#   使い方: GEMINI_API_KEY は環境の設定から読む（ファイルに書かない）
#   THUMB_WORK=<作業フォルダ（src/ に見本の png、gen/ に出す）> python3 gen_thumbs_gemini.py <案の名前>…
import os, sys, json, base64, urllib.request
KEY = os.environ["GEMINI_API_KEY"]; S = os.environ["THUMB_WORK"]; OUT = os.path.join(S, "gen"); os.makedirs(OUT, exist_ok=True)
MODEL = os.environ.get("THUMB_MODEL", "gemini-3-pro-image")
ROBOT = ("The mascot robot must match the reference images exactly: a glossy white sphere body, ONE large round teal-and-navy camera-lens eye "
         "on the front, teal round discs on both sides, a thin dark antenna with a small orange ball on top, two short stubby legs with "
         "navy feet that glow teal at the soles. No mouth, no arms, no second eye.")
STYLE = ("YouTube thumbnail, 16:9, Japanese tech explainer channel. Clean glossy 3D render, high contrast, sharp focus, vivid but not neon-cluttered. "
         "Huge bold Japanese headline text in a heavy rounded gothic font with a thick dark outline and drop shadow, exactly as written, no other words. "
         "Keep the bottom-right corner free of important elements (video length overlay). " + ROBOT)
PLANS = {
 "D": ("Headline on the left in two lines: line 1 「たった3%で」 in white, line 2 「読めない!?」 in big yellow. Small rounded tag above the headline: 「QRコード」 "
       "(white text on teal). Right half: a large clean QR code printed on white paper on a desk, with about twelve small black ink drops scattered on its "
       "white squares, and a toppled small ink bottle with a little spill. A big red circle-with-slash or red × stamp over the QR, slightly transparent. "
       "The robot stands small at the lower middle, leaning back in surprise. Dark navy studio background with a soft teal rim light."),
 "BD": ("Split comparison. Left side: a QR code with the robot sitting on its lower-right corner, covering a big part, with a big green ○ badge. "
        "Right side: the same QR code with only about twelve tiny black ink drops, with a big red × badge. Headline across the top in one line: "
        "「隠してもOK」 in white and 「汚れでアウト!?」 in yellow, separated by a small gap. Small tag 「QRコード」 at the top-left corner. "
        "Bright light-grey studio background."),
 "B": ("Headline on the left in two lines: line 1 「体で隠しても」 in black, line 2 「読めた!?」 in big red. Small tag 「QRコード」 (white on teal). "
       "Right half: a large QR code lying slightly tilted on a wooden desk; the robot is sitting on its lower-right corner, covering about a quarter of it. "
       "A smartphone held above it shows a green check mark and the word HELLO on its screen. Warm bright background."),
 "C": ("Headline on the left in two lines: line 1 「中身の3分の2は」 in white, line 2 「予備だった!」 with 予備 in big orange and the rest in white. "
       "Small tag 「QRコード」 (white on teal). Right half: a large 3D QR code made of small cubes; about two-thirds of the data cubes glow orange, "
       "one-third glow blue, the three corner finder squares are plain black and white. The robot stands small in front looking up at it. "
       "Dark navy background."),
}
def gen(name):
    parts = [{"text": STYLE + "\n\n" + PLANS[name]}]
    for ref in ("op_49.png", "op_13.png", "op_28.png"):
        p = os.path.join(S, "src", ref)
        if os.path.exists(p): parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(open(p, "rb").read()).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    r = json.load(urllib.request.urlopen(req, timeout=300)); n = 0
    for c in r.get("candidates", []):
        for pt in c.get("content", {}).get("parts", []):
            d = pt.get("inlineData") or pt.get("inline_data")
            if d:
                n += 1; fn = os.path.join(OUT, "%s_%d.png" % (name, n)); open(fn, "wb").write(base64.b64decode(d["data"])); print(fn)
    if not n: print(name, "no image", json.dumps(r)[:400])
for a in sys.argv[1:] or list(PLANS): gen(a)
